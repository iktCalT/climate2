"""Small single-instance WSGI defaults for disk-backed deployment."""

import os

if os.environ.get("CLIMATE_ENV") != "production":
    raise ValueError("Gunicorn launch requires CLIMATE_ENV=production")


def _port():
    value = os.environ.get("PORT", "8000")
    if not value.isascii() or not value.isdecimal() or not 1 <= int(value) <= 65535:
        raise ValueError("PORT must be an integer from 1 to 65535")
    return int(value)


bind = f"0.0.0.0:{_port()}"
workers = 1
threads = 4
worker_class = "gthread"
forwarded_allow_ips = ""
proxy_protocol = False
