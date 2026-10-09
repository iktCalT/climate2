import os
import numpy as np
import sqlite3
import secrets
import hashlib
import re
import json
import stat

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, session, send_from_directory
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from climate.paths import (
    STATIC_DIRECTORY, TEMPLATE_DIRECTORY,
    climate_mode, resolve_user_database_path,
)
from climate.production import configure_production
from climate.data.db import ACTIVE_CLIMATE_PROVIDER
from climate.data.location_sampling import sample_noaa_location
from climate.data.months import last_complete_month
from climate.web.helpers import apology, draw_chart, is_valid_month, is_valid_username, login_required, swap
from climate.providers.open_meteo import get_data_locations, get_location_history
from climate.services.map_data import viewport_geojson
from climate.services.admin_import import ImportBusy, import_status, start_import
from climate.services.admin_cleanup import cleanup_preview, cleanup_batch
from climate.data.cache_availability import saved_map_months
from climate.services import community
from climate.services import location_fetch

DATA_TYPES = ["temp_mean", "temp_max", "temp_min", "precip"]
DEFAULT_MAP_DATA_TYPE = "temp_mean"
FIRST_DAY_MAP_FALLBACK_HOURS = 6
START = "1950-01"
LOCATION_HISTORY_START = "1951-01-01"
LOCATION_CHART_VERSION = "v7"
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
mode = climate_mode()
app = Flask(
    __name__, template_folder=str(TEMPLATE_DIRECTORY),
    static_folder=str(STATIC_DIRECTORY), static_url_path="/static",
)
app.config["CLIMATE_PRODUCTION"] = mode == "production"
app.config["CLIMATE_PROVIDER"] = ACTIVE_CLIMATE_PROVIDER
app.config["USER_DATABASE_PATH"] = str(resolve_user_database_path())
for name, default in (
    ("ENABLED", "0"), ("SECRET", ""),
    ("DATABASE_PATH", str(Path(app.root_path).parents[1] / "instance/community.db")),
    ("MAX_ACTIVE", "10"), ("HOURLY_LIMIT", "20"),
    ("DAILY_LIMIT", "100"), ("COOLDOWN_SECONDS", "10"),
):
    app.config["COMMUNITY_" + name] = os.environ.get("COMMUNITY_" + name, default)
for name, default in (
    ("ENABLED", "0" if app.config["CLIMATE_PRODUCTION"] else "1"),
    ("HOURLY_LIMIT", "12"), ("MAX_REQUESTS", "192"),
    ("MAX_MIB", "512"), ("MAX_SECONDS", "900"),
):
    app.config["LOCATION_FETCH_" + name] = os.environ.get("LOCATION_FETCH_" + name, default)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
if app.config["CLIMATE_PRODUCTION"]:
    configure_production(app)
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


@app.context_processor
def inject_community_controls():
    if request.endpoint not in ("maps", "register"):
        return {}
    try:
        options = community.settings(app.config)
        enabled, maximum = True, options["max_active"]
    except community.CommunityError:
        enabled, maximum = False, 10
    csrf = None
    if enabled and request.endpoint == "maps" and current_user_is_admin():
        if "community_csrf" not in session:
            session["community_csrf"] = secrets.token_hex(32)
        csrf = session["community_csrf"]
    return {"community_enabled": enabled, "community_max_active": maximum,
            "community_admin_csrf": csrf}


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.before_request
def protect_static_files():
    """Keep private, hidden, and out-of-root files off Flask's static route."""
    if request.endpoint != "static":
        return None

    filename = request.view_args.get("filename", "")
    if app.config["CLIMATE_PRODUCTION"]:
        generated = _production_generated_asset(filename)
        if generated is not None:
            return generated
    requested = Path(filename)
    if any(part.startswith(".") for part in requested.parts):
        abort(404)

    try:
        static_root = Path(app.static_folder).resolve()
    except (OSError, RuntimeError, ValueError):
        abort(404)
    candidate = static_root / requested
    try:
        resolved = candidate.resolve()
        resolved_relative = resolved.relative_to(static_root)
    except (OSError, RuntimeError, ValueError):
        abort(404)
    if any(part.startswith(".") for part in resolved_relative.parts):
        abort(404)
    if app.config["CLIMATE_PRODUCTION"]:
        try:
            metadata = candidate.lstat()
        except (OSError, ValueError):
            abort(404)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            abort(404)

    names = (requested.name.lower(), candidate.name.lower(), resolved.name.lower())
    if any(_is_database_or_sidecar(name) for name in names):
        abort(404)

    try:
        configured_paths = set()
        for configured in (app.config["USER_DATABASE_PATH"], app.config["COMMUNITY_DATABASE_PATH"]):
            configured = Path(configured)
            configured_paths.update((configured.absolute(), configured.resolve()))
    except (OSError, RuntimeError, ValueError):
        abort(404)
    protected = set()
    for database in configured_paths:
        protected.add(database)
        protected.update(Path(str(database) + suffix) for suffix in ("-journal", "-wal", "-shm"))
    candidates = {candidate.absolute(), resolved}
    if candidates & protected:
        abort(404)
    # Path comparison alone misses hard links and alternate-case aliases on
    # case-insensitive filesystems. Identity checks read metadata only.
    for candidate_path in candidates:
        for protected_path in protected:
            try:
                if os.path.samefile(candidate_path, protected_path):
                    abort(404)
            except OSError:
                pass
    return None


def _production_generated_asset(filename):
    """Serve only generated public files, never arbitrary private state."""
    if filename.startswith("location_data/"):
        directory = Path(app.config["CLIMATE_CHART_DIRECTORY"])
        basename = filename.removeprefix("location_data/")
        allowed = re.fullmatch(r"v[0-9]+_-?[0-9]+\.[0-9]{2}_-?[0-9]+\.[0-9]{2}_[0-9a-f]{64}\.html", basename)
    elif filename.startswith("user_img/"):
        if filename == "user_img/default_icon.png":
            return None
        directory = Path(app.config["CLIMATE_IMAGE_DIRECTORY"])
        basename = filename.removeprefix("user_img/")
        allowed = re.fullmatch(r"[0-9]+\.(?:gif|jpeg|jpg|png|webp)", basename)
    else:
        return None
    if not allowed:
        abort(404)
    candidate = directory / basename
    try:
        metadata = candidate.lstat()
        if not candidate.is_file() or candidate.is_symlink() or metadata.st_nlink != 1:
            abort(404)
        candidate.resolve().relative_to(directory.resolve())
    except (OSError, RuntimeError, ValueError):
        abort(404)
    return send_from_directory(directory, basename)


def _is_database_or_sidecar(name):
    """Match database extensions at end or before any non-alphanumeric delimiter."""
    return re.search(
        r"\.(?:db|sqlite|sqlite3)(?=$|[^a-z0-9])",
        name,
        re.IGNORECASE | re.ASCII,
    ) is not None


@app.route("/")
def index():
    message = request.args.get("message")
    return render_template("index.html", message=message, imgname=current_image_name())


@app.route("/healthz")
def healthz():
    return ("ok\n", 200, {"Content-Type": "text/plain; charset=utf-8"})


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
    if not np.isfinite(lat) or not np.isfinite(lon) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return apology("Latitude/longitude out of range", 400)

    provider = ACTIVE_CLIMATE_PROVIDER
    noaa_sample = sample_noaa_location(lat, lon) if provider == "noaa_core" else None
    sampled_lat = noaa_sample.latitude if noaa_sample else lat
    sampled_lon = noaa_sample.longitude if noaa_sample else lon
    strlat = f"{lat:.2f}"
    strlon = f"{lon:.2f}"
    try:
        data, _ = get_location_history(
            location=(sampled_lat, sampled_lon),
            date_start=LOCATION_HISTORY_START,
            date_end=last_complete_month().strftime("%Y-%m-%d"),
            fields=tuple(DATA_TYPES),
            fetch_missing=False,
        )
    except Exception:
        app.logger.exception("Cached location history unavailable")
        return apology("Climate data is temporarily unavailable", 503)
    available_months = int(data.notna().any(axis=1).sum())
    complete_months = int(np.isfinite(data.to_numpy(dtype=float)).all(axis=1).sum())
    filename = None
    if available_months:
        # Data and coordinates identify the chart, so cleanup/imports invalidate
        # an old render without deleting files or trusting a stale file's mtime.
        content = f"{provider}:{lat!r},{lon!r}:{sampled_lat!r},{sampled_lon!r}:" + data.to_json(
            orient="split", date_format="iso", double_precision=15
        )
        digest = hashlib.sha256(content.encode()).hexdigest()
        filename = f"location_data/{LOCATION_CHART_VERSION}_{strlat}_{strlon}_{digest}.html"
        chart_directory = Path(app.config.get("CLIMATE_CHART_DIRECTORY", "static/location_data"))
        chart_exists = ((chart_directory / filename.split("/", 1)[1]).is_file()
                        if app.config["CLIMATE_PRODUCTION"]
                        else os.path.isfile("static/" + filename))
        if not chart_exists:
            draw_chart(
                lat, lon, data, filename=filename.split("/")[1],
                source_label="NOAA CORe reanalysis" if noaa_sample else "Open-Meteo CMIP6 model output",
                sampled_location=(sampled_lat, sampled_lon),
            )
    try:
        fetch_enabled = provider == "noaa_core" and location_fetch.settings(app.config)["enabled"]
    except location_fetch.FetchUnavailable:
        app.logger.warning("Location fetching disabled by invalid operator setting")
        fetch_enabled = False
    return render_template(
        "locations.html", imgname=imgname, lat=lat, lon=lon, filename=filename,
        noaa_sample=noaa_sample,
        location_fetch_enabled=fetch_enabled,
        available_months=available_months, complete_months=complete_months,
        total_months=len(data),
    )


@app.route("/api/location-fetch/status")
def location_fetch_status():
    try:
        latitude = request.args["latitude"]
        longitude = request.args["longitude"]
        if app.config["CLIMATE_PROVIDER"] != "noaa_core":
            return jsonify({"state": "disabled", "sample": None, "complete": 0,
                            "total": 0, "remaining": 0, "month": None,
                            "retry_seconds": 0})
        return jsonify(location_fetch.status(latitude, longitude, app.config))
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid location request"}), 400
    except location_fetch.FetchUnavailable:
        return jsonify({"error": "Location fetching unavailable"}), 503
    except Exception:
        app.logger.warning("Location fetch status unavailable")
        return jsonify({"error": "Location status temporarily unavailable"}), 503


@app.route("/api/location-fetch/start", methods=["POST"])
def location_fetch_start():
    if request.headers.get("Origin") != request.host_url.rstrip("/"):
        return jsonify({"error": "Same-origin request required"}), 403
    request.max_content_length = 1024
    if request.mimetype != "application/json":
        return jsonify({"error": "JSON request required"}), 415
    payload = request.get_json(silent=True)
    if (not isinstance(payload, dict) or set(payload) != {"latitude", "longitude"}
            or any(type(payload[key]) not in (int, float) for key in payload)):
        return jsonify({"error": "Invalid location request"}), 400
    try:
        if app.config["CLIMATE_PROVIDER"] != "noaa_core":
            return jsonify({"state": "disabled", "sample": None, "complete": 0,
                            "total": 0, "remaining": 0, "month": None,
                            "retry_seconds": 0})
        return jsonify(location_fetch.start(payload["latitude"], payload["longitude"], app.config))
    except ValueError:
        return jsonify({"error": "Invalid location request"}), 400
    except location_fetch.FetchUnavailable:
        return jsonify({"error": "Location fetching unavailable"}), 503
    except Exception:
        app.logger.warning("Location fetch start unavailable")
        return jsonify({"error": "Location fetch temporarily unavailable"}), 503


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
    supplied_months = request.args.getlist("month-picker")
    months = [month for month in supplied_months if month]
    data_type = request.args.get("data-type")
    latest_month = latest_map_month()
    imgname = current_image_name()
    show_selector = request.args.get("select") == "1"
    has_explicit_selection = "month-picker" in request.args or "data-type" in request.args

    if has_explicit_selection:
        if not supplied_months or any(not month for month in supplied_months) or not data_type:
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

    initial_saved_month = False
    if show_selector or not has_explicit_selection:
        availability_error = None
        try:
            saved_months = saved_map_months(START, latest_month)
        except Exception:
            app.logger.exception("Saved map month discovery failed")
            saved_months = []
            availability_error = "Saved dates could not be checked. You can still enter a month manually."
        if show_selector and has_explicit_selection:
            return render_template(
                "maps.html", imgname=imgname, data_types=DATA_TYPES,
                start=START, end=latest_month, saved_months=saved_months,
                availability_error=availability_error, months=months,
                data_type=data_type, selector_mode=True,
            )
        if not has_explicit_selection:
            stable_month = min(latest_month, default_map_month())
            eligible = [row["month"] for row in saved_months
                        if row["counts"][DEFAULT_MAP_DATA_TYPE] > 0 and row["month"] <= stable_month]
            if show_selector or not eligible:
                return render_template(
                    "maps.html", imgname=imgname, data_types=DATA_TYPES,
                    start=START, end=latest_month, saved_months=saved_months,
                    availability_error=availability_error,
                    no_default=not eligible and not show_selector and not availability_error,
                )
            months = [max(eligible)]
            data_type = DEFAULT_MAP_DATA_TYPE
            initial_saved_month = True

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
        initial_saved_month=initial_saved_month,
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


def community_response(operation):
    try:
        return operation()
    except community.CommunityError as error:
        return jsonify(error=str(error)), error.status
    except (sqlite3.Error, OSError, RuntimeError):
        # Do not log credentials, addresses, public bodies or private paths.
        return jsonify(error="Community storage is unavailable. Please retry later."), 503


def community_json_write(admin=False):
    community.settings(app.config)
    if request.headers.get("Origin") != request.host_url.rstrip("/"):
        raise community.CommunityError("Community changes require the same site origin.", 403)
    if request.mimetype != "application/json":
        raise community.CommunityError("Expected a JSON request.", 415)
    if request.content_length is not None and request.content_length > 4096:
        raise community.CommunityError("Community request is too large.", 413)
    body = request.stream.read(4097)
    if len(body) > 4096:
        raise community.CommunityError("Community request is too large.", 413)
    token = request.headers.get("X-Community-CSRF" if admin else "X-Community-Token")
    community.token_hash(token)
    try:
        payload = json.loads(body)
    except (ValueError, UnicodeError, RecursionError):
        raise community.CommunityError("Expected a JSON object.") from None
    if not isinstance(payload, dict):
        raise community.CommunityError("Expected a JSON object.")
    return token, payload


@app.route("/api/community/pins", methods=["GET", "POST"])
def community_pins_api():
    def perform():
        if request.method == "POST":
            token, payload = community_json_write()
            pin = community.publish(app.config, token, request.remote_addr, payload)
            return jsonify(pin=pin), 201
        try:
            bounds = [float(request.args[name]) for name in ("south", "west", "north", "east")]
            cursor = int(request.args.get("cursor", "0"))
            limit = int(request.args.get("limit", "100"))
        except (KeyError, ValueError, TypeError, OverflowError):
            raise community.CommunityError("Invalid community viewport or page.") from None
        return jsonify(community.list_pins(app.config, *bounds, cursor=cursor, limit=limit))
    return community_response(perform)


@app.route("/api/community/my-pins")
def community_own_pins_api():
    return community_response(lambda: jsonify(pins=community.own_pins(
        app.config, request.headers.get("X-Community-Token"))))


@app.route("/api/community/pins/<int:pin_id>", methods=["DELETE"])
def community_delete_api(pin_id):
    def perform():
        token, _ = community_json_write()
        community.delete_pin(app.config, pin_id, token, request.remote_addr)
        return jsonify(deleted=pin_id)
    return community_response(perform)


@app.route("/api/community/admin/pins/<int:pin_id>", methods=["DELETE"])
def community_admin_delete_api(pin_id):
    def perform():
        token, _ = community_json_write(admin=True)
        expected = session.get("community_csrf")
        csrf = request.headers.get("X-Community-CSRF", "")
        if not current_user_is_admin() or not expected or not secrets.compare_digest(csrf.encode(), expected.encode()):
            raise community.CommunityError("Administrator access and a current page token are required.", 403)
        community.delete_pin(app.config, pin_id, token, request.remote_addr, admin=True)
        return jsonify(deleted=pin_id)
    return community_response(perform)


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
                img.save(str(Path(app.config.get("CLIMATE_IMAGE_DIRECTORY", "static/user_img")) / imgname))
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
    """Explain the temporary closure without accepting account creation."""
    return render_template("register.html"), 403 if request.method == "POST" else 200


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
