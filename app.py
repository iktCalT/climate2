import os
import numpy as np
import sqlite3

from datetime import datetime
from functools import wraps
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, draw_chart, is_valid_month, is_valid_username, login_required, swap
from helpers_data import get_data_locations, get_location_history
from map_data import viewport_geojson

SHAPE = (91, 91)
DATA_TYPES = ["temp_mean", "temp_max", "temp_min", "precip"]
START = "1950-01"
LOCATION_HISTORY_START = "1951-01-01"
LOCATION_CHART_VERSION = "v2"
MAX_ADMIN_PREFETCH_POINTS = 100


def latest_map_month():
    """Return the newest month the Maps interface is allowed to request."""
    return datetime.today().strftime("%Y-%m")

# Configure application
app = Flask(__name__)
app.config["USER_DATABASE_PATH"] = os.environ.get("USER_DATABASE_PATH", "static/users.db")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def user_db():
    """Open the local user database without mixing it with climate PostgreSQL."""
    return sqlite3.connect(app.config["USER_DATABASE_PATH"])


def current_user_is_admin():
    user_id = session.get("user_id")
    if user_id is None:
        return False
    con = None
    try:
        con = user_db()
        row = con.execute(
            "SELECT is_admin FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return bool(row and row[0])
    except sqlite3.Error:
        return False
    finally:
        if con is not None:
            con.close()


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
    return {"is_admin": current_user_is_admin()}


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
    try:
        imgname = session["imgname"]
    except:
        imgname = None
    return render_template("index.html", message=message, imgname=imgname)


@app.route("/locations")
def locations():
    strlat = request.args.get("latitude")
    strlon = request.args.get("longitude")
    try:
        imgname = session["imgname"]
    except:
        imgname = None
    if not (strlat and strlon):
        return render_template("locations.html", imgname=imgname)
    try:
        lat = float(strlat)
        lon = float(strlon)
    except:
        return apology("Invalid latitude/longitude", 400)
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        print(f"Latitude: {lat} \nLongitude: {lon}")
        return apology(f"Latitude/logitude out of range", 400)
    
    strlat = "{:.2f}".format(lat)
    strlon = "{:.2f}".format(lon)
    filename = f"location_data/{LOCATION_CHART_VERSION}_{strlat}_{strlon}.html"
    try:
        data, fetched = get_location_history(
            location=(lat, lon),
            date_start=LOCATION_HISTORY_START,
            date_end=datetime.today().strftime("%Y-%m-%d"),
            fields=tuple(DATA_TYPES),
        )
    except RuntimeError:
        return apology("Climate data is temporarily unavailable", 503)
    if fetched or not os.path.isfile("static/"+filename):
        draw_chart(lat, lon, data, filename=filename.split("/")[1])
    return render_template("locations.html", imgname=imgname, lat=lat, lon=lon, filename=filename)


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
        con = user_db()
        rows = con.execute(
            "SELECT * FROM users WHERE username = ?", (request.form.get("username"),)
        ).fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0][2], request.form.get("password")
        ):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        try:
            imgname = con.execute("SELECT img FROM profiles WHERE user_id = ?",
                                 (session["user_id"],)).fetchone()
            print (imgname)
            session["imgname"] = imgname[0]
        except:
            session["imgname"] = None

        # Redirect user to home page
        path = "/?message=Hi!+"+request.form.get("username")
        con.close()
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
    month = request.args.get("month-picker")
    data_type = request.args.get("data-type")
    latest_month = latest_map_month()
    try:
        imgname = session["imgname"]
    except:
        imgname = None
    if not (month and data_type):
        return render_template("maps.html", imgname=imgname, data_types=DATA_TYPES,
                               start=START, end=latest_month)
    elif not is_valid_month(month, start=START, end=latest_month):
        return apology("Invalid month", 400)
    elif data_type not in DATA_TYPES:
        return apology(f"This data type ({data_type}) is not supported", 400)
    else:
        return render_template("maps.html", imgname=imgname, data_types=DATA_TYPES, 
                               data_type=data_type, month=month, start=START, end=latest_month)

@app.route("/api/map-data")
def map_data():
    try:
        month, climate_type = request.args["month"], request.args["climate_type"]
        south, west, north, east = (float(request.args[key]) for key in ("south", "west", "north", "east"))
        zoom = float(request.args["zoom"])
    except (KeyError, TypeError, ValueError):
        return jsonify(error="Invalid map request"), 400
    if not is_valid_month(month, start=START, end=latest_map_month()) or climate_type not in DATA_TYPES:
        return jsonify(error="Unsupported month or climate type"), 400
    try: return jsonify(viewport_geojson(month, climate_type, south, west, north, east, zoom))
    except ValueError as error: return jsonify(error=str(error)), 400
    except Exception:
        app.logger.exception("Map data request failed")
        return jsonify(error="Climate database is unavailable. Start PostgreSQL or set DATABASE_URL."), 503


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    try:
        imgname = session["imgname"]
    except:
        imgname = None
    if request.method == "POST":
        img = request.files.get("img")
        bio = request.form.get("bio")
        
        con = user_db()
        if img:
            # Save image only
            try:
                extenstion = os.path.splitext(img.filename)[-1]
                imgname = str(session["user_id"]) + extenstion
                img.save("static/user_img/" + imgname)
                img.close()
            except:
                img.close()
                return apology("Cannot save the image", 400)
            
            # Save its path in database
            try:
                con.execute("UPDATE profiles SET img = ? WHERE user_id = ?",
                           (imgname, session["user_id"]))
                con.commit()
                session["imgname"] = imgname
            except:
                try:
                    con.execute("INSERT INTO profiles (user_id, img) VALUES (?, ?)",
                               (session["user_id"], imgname))
                    con.commit()
                    session["imgname"] = imgname
                except:
                    con.close()
                    return apology("Oh no! Something went wrong",400)
        elif bio:
            # Change bio only
            try:
                con.execute("UPDATE profiles SET bio = ? WHERE user_id = ?", (bio, session["user_id"]))
                con.commit()
            except:
                try:
                    con.execute("INSERT INTO profiles (user_id, bio) VALUES (?, ?)",
                               (session["user_id"], bio))
                    con.commit()
                except:
                    con.close()
                    return apology("Oh no! Something went wrong",400)
        else:
            # Change nothing
            con.close()
            return redirect("/profile?message=Nothing changed")
        con.close()
        return redirect("/profile?message=Succeeded!")

    # If request.method = "GET"
    else:
        con = user_db()
        try:
            profile = con.execute("SELECT * FROM profiles WHERE user_id = ?", (session["user_id"],)).fetchone()
        except:
            con.execute("INSERT INTO profiles (user_id) VALUES (?)", (session["user_id"],))
            con.commit()
            profile = con.execute("SELECT * FROM profiles WHERE user_id = ?", (session["user_id"],)).fetchone()
        username = con.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        message = request.args.get("message")
        con.close()
        return render_template("profile.html", message=message, username=username[0], bio=profile[1], 
                               imgname=imgname)


@app.route("/references")
def references():
    try:
        imgname = session["imgname"]
    except:
        imgname = None
    return render_template("references.html", imgname=imgname)


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
            return apology("Username must be 3-12 characters long and contain only alphanumeric, underscores, or hyphens", 400)
        hash_pwd = generate_password_hash(pwd)
        
        con = user_db()
        try:
            con.execute(
                "INSERT INTO users (username, hash_pwd, is_admin) VALUES (?, ?, ?)",
                (username, hash_pwd, False),
            )
            con.commit()
            # Create a profile for the user
            user_id = con.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            con.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id[0],))
            con.commit()
        except:
            con.close()
            return apology("Username already exists!", 400)
        con.close()
        return render_template("/login.html", username=username)
    else:
        return render_template("/register.html")
    
    
@app.route("/update", methods=["GET", "POST"])
@login_required
@admin_required
def update():
    try:
        imgname = session["imgname"]
    except:
        imgname = None
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
        if not (lat_start and lat_end and n_lat and lon_start and lon_end and n_lon and date_start and date_end):
            return apology("Missing parameter(s)", 400)
        try: 
            lat_start = float(lat_start)
            lat_end = float(lat_end)
            n_lat = int(n_lat)
            lon_start = float(lon_start)
            lon_end = float(lon_end)
            n_lon = int(n_lon)
            dt_date_start = datetime.strptime(date_start,"%Y-%m-%d")
            dt_date_end = datetime.strptime(date_end,"%Y-%m-%d")
        except:
            return apology("Invalid parameter(s)", 400)

        if not (-90 <= lat_start <= 90 and -90 <= lat_end <= 90):
            return apology("Latitude out of range", 400)
        if not (-180 <= lon_start <= 180 and -180 <= lon_end <= 180):
            return apology("Longitude out of range", 400)
        if n_lat < 1 or n_lon < 1 or n_lat * n_lon > MAX_ADMIN_PREFETCH_POINTS:
            return apology(
                f"Select between 1 and {MAX_ADMIN_PREFETCH_POINTS} total points per prefetch", 400
            )
        if dt_date_start < datetime.strptime(START + "-01", "%Y-%m-%d") or dt_date_end > datetime.today():
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
        is_successful = get_data_locations(lats=lats, lons=lons, date_start=date_start, date_end=date_end, 
                           force_update_database=force_update)
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
