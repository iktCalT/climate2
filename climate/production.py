"""Explicit production configuration and peer-gated forwarded headers."""

import ipaddress
import os
import re
import stat
from pathlib import Path
from urllib.parse import urlsplit

from werkzeug.middleware.proxy_fix import ProxyFix

from climate.paths import production_state_root


def _hops(name):
    value = os.environ.get(name, "0")
    if not re.fullmatch(r"[0-9]+", value) or int(value) > 8:
        raise ValueError(f"Invalid {name}")
    return int(value)


def configure_production(app):
    """Require a durable private mount and explicit browser/proxy settings."""
    root = production_state_root()
    try:
        database = urlsplit(os.environ.get("DATABASE_URL", ""))
        valid_database = (database.scheme in ("postgresql", "postgres") and
                          bool(database.path.strip("/")) and database.port != 0)
    except ValueError:
        valid_database = False
    if not valid_database:
        raise ValueError("Production requires a PostgreSQL DATABASE_URL")
    secret = os.environ.get("CLIMATE_SECRET_KEY", "")
    if len(secret) < 32:
        raise ValueError("Production requires a CLIMATE_SECRET_KEY of at least 32 characters")
    hosts = [part.strip().lower() for part in os.environ.get("CLIMATE_ALLOWED_HOSTS", "").split(",")]
    if not hosts or any(len(host) > 253 or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in host.split(".")) for host in hosts):
        raise ValueError("Production requires explicit DNS CLIMATE_ALLOWED_HOSTS")
    if len(set(hosts)) != len(hosts):
        raise ValueError("Duplicate allowed host")
    for name, expected in (("COMMUNITY_DATABASE_PATH", root / "community.db"),
                           ("USER_DATABASE_PATH", root / "users.db")):
        selected = os.environ.get(name)
        if selected and Path(selected).resolve() != expected:
            raise ValueError(f"Production {name} must use CLIMATE_STATE_ROOT")
        if expected.is_symlink() or (expected.exists() and
                                     (not expected.is_file() or expected.stat().st_nlink != 1)):
            raise ValueError(f"Unsafe production {name}")
    peers = os.environ.get("CLIMATE_TRUSTED_PROXY_CIDRS", "")
    try:
        networks = tuple(ipaddress.ip_network(part.strip(), strict=False)
                         for part in peers.split(",") if part.strip())
    except ValueError:
        raise ValueError("Invalid trusted proxy CIDR") from None
    if any(network.prefixlen == 0 for network in networks):
        raise ValueError("Trusted proxy CIDR cannot include every peer")
    hops = {key: _hops("CLIMATE_PROXY_" + key.upper() + "_HOPS")
            for key in ("for", "proto", "host")}
    if any(hops.values()) and not networks:
        raise ValueError("Forwarded headers require trusted proxy CIDRs")
    if networks and not any(hops.values()):
        raise ValueError("Trusted proxy CIDRs require explicit hop counts")
    app.config.update(
        SECRET_KEY=secret,
        TRUSTED_HOSTS=hosts,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_USE_SIGNER=True,
        USER_DATABASE_PATH=str(root / "users.db"),
        COMMUNITY_DATABASE_PATH=str(root / "community.db"),
        SESSION_FILE_DIR=str(root / "sessions"),
        CLIMATE_CHART_DIRECTORY=str(root / "charts"),
        CLIMATE_IMAGE_DIRECTORY=str(root / "images"),
    )
    for name in ("SESSION_FILE_DIR", "CLIMATE_CHART_DIRECTORY", "CLIMATE_IMAGE_DIRECTORY"):
        directory = Path(app.config[name])
        if directory.is_symlink():
            raise ValueError(f"Unsafe production {name}")
        directory.mkdir(mode=0o700, exist_ok=True)
        metadata = directory.lstat()
        if (not stat.S_ISDIR(metadata.st_mode) or directory.resolve().parent != root
                or metadata.st_uid != os.geteuid() or metadata.st_mode & 0o077):
            raise ValueError(f"Unsafe production {name}")
    if networks:
        app.wsgi_app = TrustedProxy(app.wsgi_app, networks, hops)


class TrustedProxy:
    """Apply ProxyFix only when the socket peer belongs to an operator CIDR."""

    def __init__(self, application, networks, hops):
        self.application = application
        self.networks = networks
        self.fixed = ProxyFix(application, x_for=hops["for"],
                              x_proto=hops["proto"], x_host=hops["host"])

    def __call__(self, environ, start_response):
        try:
            peer = ipaddress.ip_address(environ.get("REMOTE_ADDR", ""))
        except ValueError:
            return self.application(environ, start_response)
        if any(peer in network for network in self.networks):
            return self.fixed(environ, start_response)
        return self.application(environ, start_response)
