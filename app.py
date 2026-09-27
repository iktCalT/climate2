import os
import numpy as np
import sqlite3
import secrets
import hashlib

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from db import ACTIVE_CLIMATE_PROVIDER
from helpers import apology, draw_chart, is_valid_month, is_valid_username, login_required, swap
from helpers_data import get_data_locations, get_location_history
from map_data import viewport_geojson
from admin_import import ImportBusy, import_status, start_import
from admin_cleanup import cleanup_preview, cleanup_batch

DATA_TYPES = ["temp_mean", "temp_max", "temp_min", "precip"]
DEFAULT_MAP_DATA_TYPE = "temp_mean"
FIRST_DAY_MAP_FALLBACK_HOURS = 6
START = "1950-01"
LOCATION_HISTORY_START = "1951-01-01"
LOCATION_CHART_VERSION = "v5"
MAX_ADMIN_PREFETCH_POINTS = 100
ALLOWED_PROFILE_IMAGE_EXTENSIONS = {".gif", ".jpeg", ".jpg", ".png", ".webp"}


def latest_map_month(now=None):
    """Return the newest month the Maps interface is allowed to request."""
    now = now or datetime.now(timezone.utc)
    return now.strftime("%Y-%m")


def default_map_month(now=None):
    """Choose the newest stable month for the initial Maps page."""
    now = now or datetime.now(timezone.utc)
    if now.day == 1 and now.hour < FIRST_DAY_MAP_FALLBACK_HOURS:
        previous_month = now.replace(day=1) - timedelta(days=1)
        return previous_month.strftime("%Y-%m")
    return latest_map_month(now)

# Configure application
app = Flask(__name__)
app.config["CLIMATE_PROVIDER"] = ACTIVE_CLIMATE_PROVIDER
app.config["USER_DATABASE_PATH"] = os.environ.get("USER_DATABASE_PATH", "static/users.db")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@contextmanager
def user_db():
    """Yield a local user connection and always close it cleanly."""
    connection = sqlite3.connect(app.config["USER_DATABASE_PATH"])
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def current_image_name():
    """Return the optional profile image stored in the current session."""
    return session.get("imgname")


def current_user_is_admin():
    user_id = session.get("user_id")
    if user_id is None:
        return False
    try:
        with user_db() as con:
            row = con.execute(
                "SELECT is_admin FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        return bool(row and row[0])
    except sqlite3.Error:
        return False


def admin_required(view):
    """Allow climate prefetching only for an account currently marked admin."""

    @wraps(view)
    def decorated_view(*args, **kwargs):
        if not current_user_is_admin():
            return apology("Administrator access is required", 403)
        return view(*args, **kwargs)
    return decorated_view


@app.context_processor
def inject_user_permissions():
    return {
        "is_admin": current_user_is_admin(),
        "climate_provider": app.config["CLIMATE_PROVIDER"],
    }


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    message = request.args.get("message")
    return render_template("index.html", message=message, imgname=current_image_name())


@app.route("/locations")
def locations():
    strlat = request.args.get("latitude")
    strlon = request.args.get("longitude")
    imgname = current_image_name()
    if not (strlat and strlon):
        return render_template("locations.html", imgname=imgname)
    try:
        lat = float(strlat)
        lon = float(strlon)
    except (TypeError, ValueError):
        return apology("Invalid latitude/longitude", 400)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return apology("Latitude/longitude out of range", 400)
    
    strlat = f"{lat:.2f}"
    strlon = f"{lon:.2f}"
    try:
        data, _ = get_location_history(
            location=(lat, lon),
            date_start=LOCATION_HISTORY_START,
            date_end=datetime.today().strftime("%Y-%m-%d"),
            fields=tuple(DATA_TYPES),
            fetch_missing=False,
        )
    except Exception:
        app.logger.exception("Cached location history unavailable")
        return apology("Climate data is temporarily unavailable", 503)
    available_months = int(data.notna().any(axis=1).sum())
    complete_months = int(data.notna().all(axis=1).sum())
    filename = None
    if available_months:
        # Data and coordinates identify the chart, so cleanup/imports invalidate
        # an old render without deleting files or trusting a stale file's mtime.
        content = f"{lat!r},{lon!r},{ACTIVE_CLIMATE_PROVIDER}:" + data.to_json(
            orient="split", date_format="iso", double_precision=15
        )
        digest = hashlib.sha256(content.encode()).hexdigest()
        filename = f"location_data/{LOCATION_CHART_VERSION}_{strlat}_{strlon}_{digest}.html"
        if not os.path.isfile("static/" + filename):
            draw_chart(lat, lon, data, filename=filename.split("/")[1])
    return render_template(
        "locations.html", imgname=imgname, lat=lat, lon=lon, filename=filename,
        available_months=available_months, complete_months=complete_months,
        total_months=len(data),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        with user_db() as con:
            rows = con.execute(
                "SELECT * FROM users WHERE username = ?",
                (request.form.get("username"),),
            ).fetchall()

            # Ensure username exists and password is correct
            if len(rows) != 1 or not check_password_hash(
                rows[0][2], request.form.get("password")
            ):
                return apology("invalid username and/or password", 400)

            # Remember which user has logged in
            session["user_id"] = rows[0][0]
            image_row = con.execute(
                "SELECT img FROM profiles WHERE user_id = ?",
                (session["user_id"],),
            ).fetchone()
            session["imgname"] = image_row[0] if image_row else None

        # Redirect user to home page
        path = "/?message=Hi!+" + request.form.get("username")
        return redirect(path)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")


@app.route("/maps")
def maps():
    months = [month for month in request.args.getlist("month-picker") if month]
    data_type = request.args.get("data-type")
    latest_month = latest_map_month()
    imgname = current_image_name()
    show_selector = request.args.get("select") == "1"

    if show_selector and not months and not data_type:
        return render_template(
            "maps.html",
            imgname=imgname,
            data_types=DATA_TYPES,
            start=START,
            end=latest_month,
        )

    if not months and not data_type:
        months = [default_map_month()]
        data_type = DEFAULT_MAP_DATA_TYPE
    elif not months or not data_type:
        return apology("Month and climate data type are both required", 400)

    if len(months) > 4:
        return apology("Compare at most four months at a time", 400)
    if len(set(months)) != len(months):
        return apology("Comparison months must be distinct", 400)
    if any(
        not is_valid_month(month, start=START, end=latest_month)
        for month in months
    ):
        return apology("Invalid month", 400)
    if data_type not in DATA_TYPES:
        return apology(f"This data type ({data_type}) is not supported", 400)
    return render_template(
        "maps.html",
        imgname=imgname,
        data_types=DATA_TYPES,
        data_type=data_type,
        month=months[0],
        months=months,
        comparison=len(months) > 1,
        start=START,
        end=latest_month,
    )


@app.route("/api/map-data")
def map_data():
    try:
        month, climate_type = request.args["month"], request.args["climate_type"]
        south, west, north, east = (
            float(request.args[key]) for key in ("south", "west", "north", "east")
        )
        zoom = float(request.args["zoom"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Invalid map request"), 400
    if (
        not is_valid_month(month, start=START, end=latest_map_month())
        or climate_type not in DATA_TYPES
    ):
        return jsonify(error="Unsupported month or climate type"), 400
    try:
        return jsonify(
            viewport_geojson(month, climate_type, south, west, north, east, zoom, fetch_missing=False)
        )
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except Exception:
        app.logger.exception("Map data request failed")
        return (
            jsonify(
                error="Climate database is unavailable. Start PostgreSQL or set DATABASE_URL."
            ),
            503,
        )


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    imgname = current_image_name()
    if request.method == "POST":
        img = request.files.get("img")
        bio = request.form.get("bio")

        if img:
            extension = Path(img.filename or "").suffix.lower()
            if extension not in ALLOWED_PROFILE_IMAGE_EXTENSIONS:
                img.close()
                return apology(
                    "Profile image must be GIF, JPEG, PNG, or WebP", 400
                )
            try:
                imgname = f'{session["user_id"]}{extension}'
                img.save("static/user_img/" + imgname)
            except (OSError, ValueError):
                return apology("Cannot save the image", 400)
            finally:
                img.close()

            with user_db() as con:
                con.execute(
                    """
                    INSERT INTO profiles (user_id, img) VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET img = excluded.img
                    """,
                    (session["user_id"], imgname),
                )
            session["imgname"] = imgname
        elif bio:
            with user_db() as con:
                con.execute(
                    """
                    INSERT INTO profiles (user_id, bio) VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET bio = excluded.bio
                    """,
                    (session["user_id"], bio),
                )
        else:
            return redirect("/profile?message=Nothing changed")
        return redirect("/profile?message=Succeeded!")

    # If request.method = "GET"
    else:
        with user_db() as con:
            profile_row = con.execute(
                "SELECT bio FROM profiles WHERE user_id = ?", (session["user_id"],)
            ).fetchone()
            if profile_row is None:
                con.execute(
                    "INSERT INTO profiles (user_id) VALUES (?)", (session["user_id"],)
                )
                profile_row = con.execute(
                    "SELECT bio FROM profiles WHERE user_id = ?",
                    (session["user_id"],),
                ).fetchone()
            username_row = con.execute(
                "SELECT username FROM users WHERE id = ?", (session["user_id"],)
            ).fetchone()
        if username_row is None:
            session.clear()
            return redirect("/login")
        message = request.args.get("message")
        return render_template(
            "profile.html",
            message=message,
            username=username_row[0],
            bio=profile_row[0],
            imgname=imgname,
        )


@app.route("/references")
def references():
    return render_template("references.html", imgname=current_image_name())


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        pwd = request.form.get("password")
        re_pwd = request.form.get("confirmation")
        if not username:
            return apology("Username is required", 400)
        if not pwd:
            return apology("Password is required", 400)
        if not re_pwd:
            return apology("Please re-enter the password", 400)
        if not re_pwd == pwd:
            return apology("Re-entered password is inconsistent with password", 400)
        if not is_valid_username(username):
            return apology(
                "Username must be 3-16 characters long and contain only alphanumeric, underscores, or hyphens",
                400,
            )
        hash_pwd = generate_password_hash(pwd)

        try:
            with user_db() as con:
                cursor = con.execute(
                    "INSERT INTO users (username, hash_pwd, is_admin) VALUES (?, ?, ?)",
                    (username, hash_pwd, False),
                )
                con.execute(
                    "INSERT INTO profiles (user_id) VALUES (?)", (cursor.lastrowid,)
                )
        except sqlite3.IntegrityError:
            return apology("Username already exists!", 400)
        return render_template("/login.html", username=username)
    else:
        return render_template("/register.html")


@app.route("/admin/data")
@login_required
@admin_required
def admin_data():
    if "import_csrf" not in session:
        session["import_csrf"] = secrets.token_urlsafe(32)
    return render_template("admin_data.html", csrf_token=session["import_csrf"])


@app.route("/api/admin/import", methods=["GET", "POST"])
@login_required
@admin_required
def admin_import_api():
    if request.method == "POST":
        token = request.headers.get("X-CSRF-Token", "")
        expected = session.get("import_csrf")
        if not expected or not secrets.compare_digest(token.encode(), expected.encode()):
            return jsonify(error="Refresh the administrator page before starting a batch."), 403
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(error="Expected a window and month limit."), 400
        try:
            result = start_import(payload.get("window"), payload.get("limit", 1))
            return jsonify(result), 202 if result["started"] else 200
        except (ValueError, TypeError):
            return jsonify(error="Choose a listed window and 1–12 whole months."), 400
        except ImportBusy as error:
            return jsonify(error=str(error)), 409
        except Exception:
            app.logger.exception("Administrator import could not start")
            return jsonify(error="Import unavailable. Check PostgreSQL and run database setup."), 503
    try:
        return jsonify(import_status())
    except Exception:
        app.logger.exception("Administrator import status unavailable")
        return jsonify(error="Status unavailable. Check PostgreSQL and run database setup."), 503


@app.route("/api/admin/cleanup", methods=["GET", "POST"])
@login_required
@admin_required
def admin_cleanup_api():
    if request.method == "GET":
        session.pop("cleanup_preview", None)
        try:
            result = cleanup_preview()
            token = secrets.token_urlsafe(32)
            session["cleanup_preview"] = [token, datetime.now(timezone.utc).timestamp()]
            return jsonify({**result, "preview_token": token})
        except Exception:
            app.logger.exception("Administrator cleanup preview failed")
            return jsonify(error="Cleanup preview unavailable. No data was deleted."), 503
    token = request.headers.get("X-CSRF-Token", "")
    expected = session.get("import_csrf")
    if not expected or not secrets.compare_digest(token.encode(), expected.encode()):
        return jsonify(error="Reload the administrator page before cleanup."), 403
    payload = request.get_json(silent=True)
    preview = session.get("cleanup_preview")
    if (not isinstance(payload, dict) or payload.get("confirm") is not True
            or not preview or not isinstance(payload.get("preview_token"), str)
            or not secrets.compare_digest(payload["preview_token"].encode(), preview[0].encode())
            or not 0 <= datetime.now(timezone.utc).timestamp() - preview[1] <= 600):
        return jsonify(error="Preview cleanup again and confirm the permanent deletion."), 400
    session.pop("cleanup_preview", None)
    try:
        return jsonify(cleanup_batch())
    except ImportBusy as error:
        return jsonify(error=str(error)), 409
    except Exception:
        app.logger.exception("Administrator cleanup failed")
        return jsonify(error="Cleanup could not be confirmed. Preview current counts before retrying."), 503


@app.route("/update", methods=["GET", "POST"])
@login_required
@admin_required
def update():
    imgname = current_image_name()
    if request.method == "POST":
        lat_start = request.form.get("lat_start")
        lat_end = request.form.get("lat_end")
        n_lat = request.form.get("n_lat")
        lon_start = request.form.get("lon_start")
        lon_end = request.form.get("lon_end")
        n_lon = request.form.get("n_lon")
        date_start = request.form.get("date_start")
        date_end = request.form.get("date_end")
        force_update = request.form.get("force_update")
        if not all(
            (
                lat_start,
                lat_end,
                n_lat,
                lon_start,
                lon_end,
                n_lon,
                date_start,
                date_end,
            )
        ):
            return apology("Missing parameter(s)", 400)
        try:
            lat_start = float(lat_start)
            lat_end = float(lat_end)
            n_lat = int(n_lat)
            lon_start = float(lon_start)
            lon_end = float(lon_end)
            n_lon = int(n_lon)
            dt_date_start = datetime.strptime(date_start, "%Y-%m-%d")
            dt_date_end = datetime.strptime(date_end, "%Y-%m-%d")
        except (TypeError, ValueError):
            return apology("Invalid parameter(s)", 400)

        if not (-90 <= lat_start <= 90 and -90 <= lat_end <= 90):
            return apology("Latitude out of range", 400)
        if not (-180 <= lon_start <= 180 and -180 <= lon_end <= 180):
            return apology("Longitude out of range", 400)
        if n_lat < 1 or n_lon < 1 or n_lat * n_lon > MAX_ADMIN_PREFETCH_POINTS:
            return apology(
                f"Select between 1 and {MAX_ADMIN_PREFETCH_POINTS} total points per prefetch", 400
            )
        if (
            dt_date_start < datetime.strptime(START + "-01", "%Y-%m-%d")
            or dt_date_end > datetime.today()
        ):
            return apology("Dates must be between January 1950 and today", 400)

        force_update = bool(force_update)
        if lat_start > lat_end:
            lat_start, lat_end = swap(lat_start, lat_end)
        if lon_start > lon_end:
            lon_start, lon_end = swap(lon_start, lon_end)
        if dt_date_start > dt_date_end:
            date_start, date_end = swap(date_start, date_end)
        lats = np.linspace(lat_start, lat_end, n_lat)
        lons = np.linspace(lon_start, lon_end, n_lon)
        is_successful = get_data_locations(
            lats=lats,
            lons=lons,
            date_start=date_start,
            date_end=date_end,
            force_update_database=force_update,
        )
        if not is_successful:
            return apology("Failed to update data", 400)
        return redirect("/update?message=Succeeded!")
    else:
        message = request.args.get("message")
        start = START + "-01"  # "1950-01-01"
        end = datetime.today().strftime("%Y-%m-%d")  # eg: "2024-12-25"
        return render_template(
            "update.html",
            message=message,
            imgname=imgname,
            start=start,
            end=end,
            max_points=MAX_ADMIN_PREFETCH_POINTS,
        )
