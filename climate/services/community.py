"""Bounded public comments in a separate private SQLite store."""

import hashlib
import hmac
import math
import os
import re
import sqlite3
import stat
import time
from contextlib import contextmanager
from pathlib import Path

from climate.paths import PROJECT_ROOT, STATIC_DIRECTORY


class CommunityError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def settings(config):
    """Validate deployment settings before any filesystem/database operation."""
    if config.get("COMMUNITY_ENABLED") not in (True, 1, "1"):
        raise CommunityError("Community pins are currently disabled.", 503)
    secret = config.get("COMMUNITY_SECRET", "")
    if not isinstance(secret, str) or len(secret) < 32:
        raise CommunityError("Community pins are currently disabled.", 503)
    result = {"secret": secret}
    for name, default, minimum, maximum in (
        ("MAX_ACTIVE", 10, 1, 100), ("HOURLY_LIMIT", 20, 1, 1000),
        ("DAILY_LIMIT", 100, 1, 10000), ("COOLDOWN_SECONDS", 10, 1, 3600),
    ):
        value = config.get("COMMUNITY_" + name, default)
        try:
            if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
                raise ValueError
            value = int(value)
            if not minimum <= value <= maximum:
                raise ValueError
        except (TypeError, ValueError):
            raise CommunityError("Community configuration is unavailable.", 503) from None
        result[name.lower()] = value
    try:
        path = Path(config.get("COMMUNITY_DATABASE_PATH", PROJECT_ROOT / "instance/community.db")).resolve()
        static = STATIC_DIRECTORY.resolve()
        if path.suffix.lower() not in (".db", ".sqlite", ".sqlite3") or path.is_relative_to(static):
            raise ValueError
        static_identity = static.stat()
        # Parent metadata catches aliases on case-insensitive filesystems even
        # when their spelling differs. Work is bounded by path depth, not files.
        for ancestor in path.parents:
            try:
                identity = ancestor.stat()
            except FileNotFoundError:
                continue
            if (identity.st_dev, identity.st_ino) == (static_identity.st_dev, static_identity.st_ino):
                raise ValueError
        protected = [Path(config["USER_DATABASE_PATH"]), PROJECT_ROOT / "instance/users.db",
                     STATIC_DIRECTORY / "users.db", STATIC_DIRECTORY / "weather.db",
                     STATIC_DIRECTORY / "weather_update.db", PROJECT_ROOT / ".cache.sqlite"]
        if path in {p.resolve() for p in protected}:
            raise ValueError
        try:
            identity = path.stat()
        except FileNotFoundError:
            identity = None
        if identity is not None:
            # Reject every hard-linked store; detecting aliases no longer needs
            # a traversal of public static content (or any other directory).
            if not stat.S_ISREG(identity.st_mode) or identity.st_nlink != 1:
                raise ValueError
            for other in protected:
                if other.is_file() and os.path.samefile(path, other):
                    raise ValueError
    except (OSError, RuntimeError, TypeError, ValueError, KeyError):
        raise CommunityError("Community storage configuration is unavailable.", 503) from None
    result["path"] = path
    return result


def token_hash(token):
    if not isinstance(token, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", token):
        raise CommunityError("A valid local ownership credential is required.", 403)
    return hashlib.sha256(bytes.fromhex(token)).hexdigest()


def coordinate(value, bound):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CommunityError("Enter numeric coordinates within the supported world bounds.")
    if not -bound <= value <= bound or not math.isfinite(value):
        raise CommunityError("Enter coordinates within the supported world bounds.")
    return float(value)


def text(value, maximum, label):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
        raise CommunityError(f"{label} must contain 1–{maximum} characters.")
    value = value.strip()
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        raise CommunityError(f"{label} contains invalid Unicode characters.") from None
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise CommunityError(f"{label} contains unsupported control characters.")
    return value


@contextmanager
def connection(options, create=False):
    path = options["path"]
    if create:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Exclusive creation protects private file permissions without chmod-ing
        # unrelated existing files. SQLite creates sidecars alongside this file.
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(fd)
    con = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=5, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        con.execute("BEGIN IMMEDIATE" if create else "BEGIN")
        if create:
            con.execute("CREATE TABLE IF NOT EXISTS community_pins (id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT NOT NULL, nickname TEXT NOT NULL, comment TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, created REAL NOT NULL)")
            con.execute("CREATE INDEX IF NOT EXISTS community_owner ON community_pins(owner)")
            con.execute("CREATE TABLE IF NOT EXISTS community_events (owner TEXT NOT NULL, ip TEXT NOT NULL, created REAL NOT NULL, kind TEXT NOT NULL)")
            con.execute("CREATE INDEX IF NOT EXISTS community_event_ip ON community_events(ip, created)")
            con.execute("CREATE INDEX IF NOT EXISTS community_event_owner ON community_events(owner, created)")
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def throttle(con, options, owner, ip, now, kind):
    digest = hmac.new(options["secret"].encode(), (ip or "unknown").encode(), hashlib.sha256).hexdigest()
    con.execute("DELETE FROM community_events WHERE created < ?", (now - 86400,))
    hour, day = con.execute("SELECT COALESCE(SUM(created >= ?), 0), COUNT(*) FROM community_events WHERE ip = ?", (now - 3600, digest)).fetchone()
    if hour >= options["hourly_limit"] or day >= options["daily_limit"]:
        raise CommunityError("Too many community changes from this network. Try again later.", 429)
    if kind == "publish":
        last = con.execute("SELECT MAX(created) FROM community_events WHERE owner = ? AND kind = 'publish'", (owner,)).fetchone()[0]
        if last is not None and now - last < options["cooldown_seconds"]:
            raise CommunityError("Please wait before publishing another pin.", 429)
    con.execute("INSERT INTO community_events (owner, ip, created, kind) VALUES (?, ?, ?, ?)", (owner, digest, now, kind))


def public_pin(row):
    return {key: row[key] for key in ("id", "nickname", "comment", "latitude", "longitude", "created")}


def publish(config, token, ip, payload):
    options = settings(config)
    owner = token_hash(token)
    if not isinstance(payload, dict):
        raise CommunityError("Expected a JSON pin.")
    nickname = text(payload.get("nickname"), 40, "Nickname")
    comment = text(payload.get("comment"), 500, "Comment")
    latitude = coordinate(payload.get("latitude"), 85)
    longitude = coordinate(payload.get("longitude"), 180)
    now = time.time()
    with connection(options, create=True) as con:
        count = con.execute("SELECT COUNT(*) FROM community_pins WHERE owner = ?", (owner,)).fetchone()[0]
        if count >= options["max_active"]:
            raise CommunityError("Your device has reached the active pin limit. Delete one of your pins before adding another.", 409)
        throttle(con, options, owner, ip, now, "publish")
        cursor = con.execute("INSERT INTO community_pins (owner, nickname, comment, latitude, longitude, created) VALUES (?, ?, ?, ?, ?, ?)", (owner, nickname, comment, latitude, longitude, now))
        return public_pin(con.execute("SELECT * FROM community_pins WHERE id = ?", (cursor.lastrowid,)).fetchone())


def list_pins(config, south, west, north, east, cursor=0, limit=100):
    options = settings(config)
    south, north = coordinate(south, 85), coordinate(north, 85)
    west, east = coordinate(west, 180), coordinate(east, 180)
    if south >= north or west >= east or isinstance(cursor, bool) or not isinstance(cursor, int) or not 0 <= cursor <= 2**63 - 1 or isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise CommunityError("Invalid viewport, cursor or page size.")
    if not options["path"].exists():
        return {"pins": [], "more": False, "next_cursor": None}
    with connection(options) as con:
        rows = con.execute("SELECT id, nickname, comment, latitude, longitude, created FROM community_pins WHERE latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ? AND id > ? ORDER BY id LIMIT ?", (south, north, west, east, cursor, limit + 1)).fetchall()
    pins = [public_pin(row) for row in rows[:limit]]
    more = len(rows) > limit
    return {"pins": pins, "more": more, "next_cursor": pins[-1]["id"] if more else None}


def delete_pin(config, pin_id, token, ip, admin=False):
    options = settings(config)
    owner = hashlib.sha256(b"community-administrator").hexdigest() if admin else token_hash(token)
    if isinstance(pin_id, bool) or not isinstance(pin_id, int) or not 1 <= pin_id <= 2**63 - 1:
        raise CommunityError("Invalid pin identifier.")
    if not options["path"].exists():
        raise CommunityError("Pin not found.", 404)
    with connection(options, create=True) as con:
        row = con.execute("SELECT owner FROM community_pins WHERE id = ?", (pin_id,)).fetchone()
        if row is None:
            raise CommunityError("Pin not found.", 404)
        if not admin and not hmac.compare_digest(row["owner"], owner):
            raise CommunityError("This device cannot delete that pin.", 403)
        # Authenticated moderation must remain available after public posting
        # exhausts a shared network bucket. Owner deletion still uses its limits.
        if not admin:
            throttle(con, options, owner, ip, time.time(), "delete")
        con.execute("DELETE FROM community_pins WHERE id = ?", (pin_id,))


def own_pins(config, token):
    options = settings(config)
    owner = token_hash(token)
    if not options["path"].exists():
        return []
    with connection(options) as con:
        # Config never allows more than 100 active pins. Lowering preserves them.
        rows = con.execute("SELECT * FROM community_pins WHERE owner = ? ORDER BY id LIMIT 100", (owner,)).fetchall()
    return [public_pin(row) for row in rows]
