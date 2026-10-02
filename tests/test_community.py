import concurrent.futures
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from climate.services import community as c
from climate.web.app import app


TOKEN = "ab" * 32
OTHER = "cd" * 32
PAYLOAD = dict(nickname="Reader", comment="<script>plain text</script>", latitude=1, longitude=2)


class CommunityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "community.db"
        self.config = dict(COMMUNITY_ENABLED=True, COMMUNITY_SECRET="fake-test-only-secret-" * 3,
                           COMMUNITY_DATABASE_PATH=str(self.path),
                           USER_DATABASE_PATH=str(Path(self.temp.name) / "users.db"))
        self.now = patch("climate.services.community.time.time", return_value=100000).start()
        self.settings = patch.dict(app.config, {**self.config, "TESTING": True})
        self.settings.start()
        self.client = app.test_client()

    def tearDown(self):
        self.settings.stop()
        patch.stopall()
        self.temp.cleanup()

    def publish(self, token=TOKEN, ip="192.0.2.1", **payload):
        return c.publish(self.config, token, ip, {**PAYLOAD, **payload})

    def error(self, status, operation):
        with self.assertRaises(c.CommunityError) as caught:
            operation()
        self.assertEqual(caught.exception.status, status)

    def headers(self, token=TOKEN):
        return {"Origin": "http://localhost", "X-Community-Token": token}

    def test_disabled_invalid_configuration_never_creates_database(self):
        for change in ({"COMMUNITY_ENABLED": False}, {"COMMUNITY_SECRET": "short"},
                       {"COMMUNITY_MAX_ACTIVE": True}, {"COMMUNITY_COOLDOWN_SECONDS": 0},
                       {"COMMUNITY_DATABASE_PATH": self.config["USER_DATABASE_PATH"]},
                       {"COMMUNITY_DATABASE_PATH": str(c.STATIC_DIRECTORY / "pins.db")}):
            with self.subTest(change=change):
                self.error(503, lambda: c.publish({**self.config, **change}, TOKEN, "ip", PAYLOAD))
                self.assertFalse(self.path.exists())
        # Both symlink and hardlink aliases of private account storage are rejected.
        account = Path(self.config["USER_DATABASE_PATH"])
        account.touch()
        for mode in ("symlink", "hardlink"):
            alias = Path(self.temp.name) / (mode + ".db")
            if mode == "symlink":
                alias.symlink_to(account)
            else:
                os.link(account, alias)
            self.error(503, lambda: c.settings({**self.config, "COMMUNITY_DATABASE_PATH": str(alias)}))

    def test_public_fields_private_list_and_bounded_pagination(self):
        for i in range(3):
            self.now.return_value += 11
            self.publish(longitude=i)
        page = c.list_pins(self.config, -85, -180, 85, 180, limit=2)
        self.assertTrue(page["more"])
        self.assertEqual(len(page["pins"]), 2)
        self.assertEqual(set(page["pins"][0]), {"id", "nickname", "comment", "latitude", "longitude", "created"})
        self.assertEqual(len(c.list_pins(self.config, -85, -180, 85, 180, cursor=page["next_cursor"], limit=2)["pins"]), 1)
        self.assertEqual(len(c.list_pins(self.config, 0, -1, 2, .5)["pins"]), 1)
        self.assertEqual(len(c.own_pins(self.config, TOKEN)), 3)
        self.error(403, lambda: c.own_pins(self.config, None))
        self.assertEqual(c.own_pins(self.config, OTHER), [])
        with sqlite3.connect(self.path) as con:
            self.assertNotEqual(con.execute("SELECT owner FROM community_pins").fetchone()[0], TOKEN)
            self.assertNotEqual(con.execute("SELECT ip FROM community_events").fetchone()[0], "192.0.2.1")

    def test_path_safety_is_bounded_and_rejects_public_aliases_and_nonregular_files(self):
        public = Path(self.temp.name) / "public"
        public.mkdir()
        private = Path(self.temp.name) / "private"
        private.mkdir()
        alias = Path(self.temp.name) / "public-alias"
        alias.symlink_to(public, target_is_directory=True)
        exposed = public / "exposed.db"
        exposed.touch()
        linked = private / "linked.db"
        os.link(exposed, linked)
        directory = private / "directory.db"
        directory.mkdir()
        fifo = private / "fifo.db"
        os.mkfifo(fifo)
        with (patch.object(c, "STATIC_DIRECTORY", public),
              patch.object(Path, "rglob", side_effect=AssertionError("Unbounded traversal"))):
            self.assertEqual(c.settings(self.config)["path"], self.path.resolve())
            for candidate in (public / "new.db", alias / "new.db", linked, directory, fifo):
                with self.subTest(candidate=candidate.name):
                    self.error(503, lambda: c.settings({**self.config, "COMMUNITY_DATABASE_PATH": str(candidate)}))
            account = Path(self.config["USER_DATABASE_PATH"])
            account.touch()
            differently_cased = account.with_name("USERS.DB")
            # Case aliases are filesystem-dependent; verify when this volume
            # resolves both spellings to the same inode, without creating one.
            if differently_cased.exists() and os.path.samefile(account, differently_cased):
                self.error(503, lambda: c.settings({**self.config, "COMMUNITY_DATABASE_PATH": str(differently_cased)}))

    def test_default_quota_lowering_preserves_pins_and_atomic_race(self):
        for _ in range(10):
            self.now.return_value += 11
            self.publish()
        self.now.return_value += 11
        self.error(409, self.publish)
        self.config["COMMUNITY_MAX_ACTIVE"] = 2
        self.error(409, self.publish)
        self.assertEqual(len(c.own_pins(self.config, TOKEN)), 10)
        self.config["COMMUNITY_MAX_ACTIVE"] = 1
        def attempt(_):
            try:
                self.publish(OTHER, "192.0.2.2")
                return 201
            except c.CommunityError as error:
                return error.status
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            self.assertEqual(sorted(pool.map(attempt, range(2))), [201, 409])
        self.assertEqual(len(c.own_pins(self.config, OTHER)), 1)

    def test_deletion_retains_cooldown_and_ip_rate_limits(self):
        pin = self.publish()
        self.error(403, lambda: c.delete_pin(self.config, pin["id"], OTHER, "192.0.2.1"))
        c.delete_pin(self.config, pin["id"], TOKEN, "192.0.2.1")
        self.error(429, self.publish)
        self.config["COMMUNITY_HOURLY_LIMIT"] = 2
        self.error(429, lambda: self.publish(OTHER))
        self.assertEqual(c.own_pins(self.config, TOKEN), [])

    def test_invalid_payloads_coordinates_tokens_and_read_bounds(self):
        for payload in (None, [], {**PAYLOAD, "nickname": False}, {**PAYLOAD, "comment": "x" * 501},
                        {**PAYLOAD, "latitude": True}, {**PAYLOAD, "latitude": float("nan")},
                        {**PAYLOAD, "longitude": 10**1000}, {**PAYLOAD, "latitude": "1"}):
            self.error(400, lambda: c.publish(self.config, TOKEN, "ip", payload))
        for token in (None, "a" * 63, "z" * 64, True):
            self.error(403, lambda: c.own_pins(self.config, token))
        for kwargs in ({"cursor": -1}, {"cursor": True}, {"cursor": 10**1000}, {"limit": 101}, {"limit": False}):
            self.error(400, lambda: c.list_pins(self.config, -85, -180, 85, 180, **kwargs))
        for pin_id in (True, 0, -1, 10**1000):
            self.error(400, lambda: c.delete_pin(self.config, pin_id, TOKEN, "ip"))
        self.assertFalse(self.path.exists())

    def test_http_origin_header_body_validation_and_private_reads(self):
        for headers in ({}, {"Origin": "http://elsewhere", "X-Community-Token": TOKEN},
                        {"Origin": "http://localhost"}):
            self.assertEqual(self.client.post("/api/community/pins", json=PAYLOAD, headers=headers).status_code, 403)
        for body, status in (("[]", 400), ("{", 400), ("x" * 4097, 413)):
            self.assertEqual(self.client.post("/api/community/pins", data=body, content_type="application/json", headers=self.headers()).status_code, status)
        self.assertEqual(self.client.post("/api/community/pins", data="x", headers=self.headers()).status_code, 415)
        self.assertFalse(self.path.exists())
        response = self.client.post("/api/community/pins", json=PAYLOAD, headers=self.headers())
        self.assertEqual(response.status_code, 201)
        pin = response.json["pin"]
        self.assertEqual(self.client.get("/api/community/my-pins").status_code, 403)
        self.assertEqual(len(self.client.get("/api/community/my-pins", headers=self.headers()).json["pins"]), 1)
        self.assertEqual(self.client.delete(f'/api/community/pins/{pin["id"]}', json={}, headers=self.headers(OTHER)).status_code, 403)
        for query in ("south=NaN&west=-180&north=85&east=180", "south=-85&west=-180&north=85&east=180&limit=101", "south=-85&west=-180&north=85&east=180&cursor=-1"):
            self.assertEqual(self.client.get("/api/community/pins?" + query).status_code, 400)

    def test_admin_delete_requires_current_account_and_csrf_without_profile_token(self):
        with sqlite3.connect(self.config["USER_DATABASE_PATH"]) as con:
            con.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, is_admin BOOLEAN)")
            con.execute("INSERT INTO users VALUES (1, 1)")
        pin = self.publish()
        url = f'/api/community/admin/pins/{pin["id"]}'
        headers = {"Origin": "http://localhost", "X-Community-CSRF": OTHER}
        self.assertEqual(self.client.delete(url, json={}, headers=headers).status_code, 403)
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["community_csrf"] = OTHER
        self.assertEqual(self.client.delete(url, json={}, headers={"Origin": "http://localhost"}).status_code, 403)
        with sqlite3.connect(self.config["USER_DATABASE_PATH"]) as con:
            con.execute("UPDATE users SET is_admin=0")
        self.assertEqual(self.client.delete(url, json={}, headers=headers).status_code, 403)
        with sqlite3.connect(self.config["USER_DATABASE_PATH"]) as con:
            con.execute("UPDATE users SET is_admin=1")
        self.assertEqual(self.client.delete(url, json={}, headers=headers).status_code, 200)
        self.assertEqual(c.own_pins(self.config, TOKEN), [])

    def test_administrator_can_moderate_a_saturated_posting_network(self):
        pin = self.publish()
        self.config["COMMUNITY_HOURLY_LIMIT"] = 1
        c.delete_pin(self.config, pin["id"], None, "192.0.2.1", admin=True)
        self.assertEqual(c.own_pins(self.config, TOKEN), [])

    def test_invalid_unicode_is_rejected_before_database_creation(self):
        for field in ("nickname", "comment"):
            self.error(400, lambda: self.publish(**{field: "\ud800"}))
        self.assertFalse(self.path.exists())
