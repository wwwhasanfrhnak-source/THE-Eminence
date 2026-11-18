"""HTTPS/LAN API client and local session store for the Android app."""

from __future__ import annotations

import ipaddress
import json
import os
import ssl
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

TIMEOUT_SECONDS = 8
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
SESSION_FILE = "mobile_session.json"
DEVICE_FILE = "mobile_device.json"
PLATFORM = "android"


class ApiError(Exception):
    def __init__(self, message, status=0):
        super().__init__(message)
        self.status = status


def _app_dir():
    try:
        from kivy.app import App

        app = App.get_running_app()
        if app is not None and app.user_data_dir:
            return Path(app.user_data_dir)
    except Exception:
        pass
    path = Path.home() / ".the_eminence"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cleartext_host_allowed(host):
    host = (host or "").strip().strip(".").lower()
    if not host:
        return False
    if host in ("localhost", "127.0.0.1", "::1") or host.endswith(".local"):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # Single-label hostnames are only resolvable inside the LAN.
        return "." not in host
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
    )


def normalize_server(server):
    value = str(server or "").strip()
    if not value:
        raise ApiError("آدرس سرور را وارد کنید.")
    if "://" not in value:
        value = "http://" + value
    parts = urlsplit(value)
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        raise ApiError("آدرس سرور باید http یا https باشد.")
    if not parts.hostname:
        raise ApiError("آدرس سرور معتبر نیست.")
    if scheme == "http" and not _cleartext_host_allowed(parts.hostname):
        raise ApiError(
            "ارتباط بدون رمزنگاری فقط برای شبکه محلی مجاز است؛ "
            "برای این سرور از https استفاده کنید."
        )
    return value.rstrip("/")


def _tls_context():
    try:
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        context = ssl.create_default_context()
    try:
        context.minimum_version = ssl.TLSVersion.TLSv1_2
    except (AttributeError, ValueError):
        pass
    return context


def device_identity():
    path = _app_dir() / DEVICE_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("device_id"):
            return data["device_id"], data.get("device_name") or PLATFORM
    except (OSError, ValueError, TypeError):
        pass
    device_id = str(uuid.uuid4())
    device_name = "Android"
    try:
        from kivy.utils import platform as kivy_platform

        device_name = f"Android ({kivy_platform})"
    except Exception:
        pass
    _write_json(path, {"device_id": device_id, "device_name": device_name})
    return device_id, device_name


def _write_json(path, payload):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        temporary.replace(path)
    except OSError:
        pass


def _request(server, method, path, payload=None, token=None):
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = normalize_server(server) + path
    request = Request(url, data=body, headers=headers, method=method)
    context = _tls_context() if url.lower().startswith("https://") else None
    try:
        with urlopen(
            request, timeout=TIMEOUT_SECONDS, context=context
        ) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
    except HTTPError as exc:
        try:
            message = json.loads(exc.read().decode("utf-8")).get("error")
        except Exception:
            message = ""
        raise ApiError(message or f"خطای سرور ({exc.code})", exc.code) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ApiError(f"ارتباط با سرور برقرار نشد: {exc}") from exc
    if len(data) > MAX_RESPONSE_BYTES:
        raise ApiError("پاسخ سرور بیش از اندازه مجاز است.")
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ApiError("پاسخ سرور معتبر نیست.") from exc


def login(server, username, password):
    device_id, device_name = device_identity()
    data = _request(
        server,
        "POST",
        "/v1/login",
        {
            "username": username,
            "password": password,
            "device_id": device_id,
            "device_name": device_name,
        },
    )
    save_session(
        {
            "server": normalize_server(server),
            "token": data.get("token", ""),
            "username": username,
            "expires_at": data.get("expires_at", ""),
            "permissions": list(data.get("permissions") or []),
        }
    )
    return data


def me(server, token):
    return _request(server, "GET", "/v1/me", token=token)


def logout(server, token):
    try:
        _request(server, "POST", "/v1/logout", {}, token=token)
    except ApiError:
        pass
    clear_session()


def summary(server, token):
    return _request(server, "GET", "/v1/summary", token=token)


def delta(server, token, since=""):
    query = urlencode({"since": since})
    return _request(server, "GET", f"/v1/delta?{query}", token=token)


def save_session(session):
    path = _app_dir() / SESSION_FILE
    payload = json.dumps(session, ensure_ascii=False).encode("utf-8")
    try:
        import secure_store

        if secure_store.write_encrypted(path, payload):
            return
    except Exception:
        pass
    _write_json(path, session)


def load_session():
    path = _app_dir() / SESSION_FILE
    try:
        import secure_store

        payload = secure_store.read_encrypted(path)
        if payload:
            data = json.loads(payload.decode("utf-8"))
            if data.get("server") and data.get("token"):
                return data
    except Exception:
        pass
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("server") and data.get("token"):
            return data
    except (OSError, ValueError, TypeError):
        pass
    return None


def clear_session():
    try:
        (_app_dir() / SESSION_FILE).unlink()
    except OSError:
        pass
