"""Authenticated table-level synchronization over a local network.

PIN pairing authenticates peers but the HTTP transport does not encrypt data.
Use only on a trusted LAN; HTTPS is needed for confidentiality against network
observers.
"""

import hashlib
import hmac
import json
import secrets
import socket
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from electrocalc.data.database import get_connection

DISCOVERY_PORT = 50000
HTTP_PORT = 8080
DISCOVERY_REQUEST = "THE_EMINENCE_LAN_SYNC_DISCOVER_V1"
TABLES = ("projects", "reports", "timesheets")
MAX_BODY_SIZE = 8 * 1024 * 1024
PAIR_WINDOW_SECONDS = 60
SESSION_SECONDS = 8 * 60 * 60


def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _local_ip():
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("192.0.2.1", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


def _device_id():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            ("lan_sync_device_id",),
        )
        row = cursor.fetchone()
        if row:
            return row["value"]
        value = str(uuid.uuid4())
        cursor.execute(
            "INSERT OR IGNORE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            ("lan_sync_device_id", value, _utc_now()),
        )
        connection.commit()
        cursor.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            ("lan_sync_device_id",),
        )
        return cursor.fetchone()["value"]
    finally:
        connection.close()


def _make_handler(service):
    class SyncRequestHandler(BaseHTTPRequestHandler):
        server_version = "EminenceSync/1"

        def log_message(self, _format, *_args):
            return

        def _send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise ValueError("طول درخواست نامعتبر است.") from None
            if length <= 0 or length > MAX_BODY_SIZE:
                raise ValueError("اندازه درخواست نامعتبر است.")
            try:
                return json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("JSON درخواست معتبر نیست.") from exc

        def _authorized(self):
            scheme, _, token = self.headers.get("Authorization", "").partition(" ")
            return scheme.lower() == "bearer" and service.validate_session(token)

        def do_GET(self):
            route = urlparse(self.path)
            if route.path == "/v1/info":
                self._send_json(200, service.local_info(include_pin=False))
                return
            if route.path == "/v1/challenge":
                self._send_json(200, {
                    "challenge": service.create_challenge(),
                    "device_id": service.device_id,
                })
                return
            if route.path == "/v1/delta":
                if not self._authorized():
                    self._send_json(401, {"error": "احراز هویت لازم است."})
                    return
                query = parse_qs(route.query)
                since = query.get("since", [""])[0]
                role = query.get("role", ["engineer"])[0]
                self._send_json(200, service.export_delta(since, role))
                return
            self._send_json(404, {"error": "مسیر درخواست پیدا نشد."})

        def do_POST(self):
            route = urlparse(self.path)
            try:
                payload = self._read_json()
                if route.path == "/v1/pair":
                    token = service.verify_pairing(payload)
                    self._send_json(200, {"token": token})
                    return
                if route.path == "/v1/merge":
                    if not self._authorized():
                        self._send_json(401, {"error": "احراز هویت لازم است."})
                        return
                    self._send_json(200, {"merged": service.merge_delta(payload)})
                    return
                self._send_json(404, {"error": "مسیر درخواست پیدا نشد."})
            except PermissionError as exc:
                self._send_json(403, {"error": str(exc)})
            except ValueError as exc:
                self._send_json(400, {"error": str(exc)})
            except Exception as exc:
                self._send_json(500, {"error": str(exc)})

    return SyncRequestHandler


class LanSyncService:
    """LAN discovery, PIN pairing, and allowlisted table delta exchange."""

    def __init__(self):
        self.device_id = _device_id()
        self.hostname = socket.gethostname()
        self.ip = _local_ip()
        self.port = HTTP_PORT
        self.pin = self._new_pin()
        self._server = None
        self._server_thread = None
        self._discovery_socket = None
        self._discovery_thread = None
        self._stopping = threading.Event()
        self._lock = threading.RLock()
        self._challenges = {}
        self._sessions = {}

    @staticmethod
    def _new_pin():
        return f"{secrets.randbelow(1_000_000):06d}"

    def local_info(self, include_pin=True):
        info = {
            "device_id": self.device_id,
            "hostname": self.hostname,
            "ip": self.ip,
            "port": self.port,
        }
        if include_pin:
            info["pin"] = self.pin
        return info

    def start(self):
        self._ensure_sync_timestamps()
        if self._server is None:
            try:
                self._server = ThreadingHTTPServer(
                    ("0.0.0.0", self.port), _make_handler(self),
                )
            except OSError as exc:
                if exc.errno not in (98, 10048):
                    raise
                self._server = ThreadingHTTPServer(
                    ("0.0.0.0", 0), _make_handler(self),
                )
                self.port = self._server.server_address[1]
            self._server.daemon_threads = True
            self._server_thread = threading.Thread(
                target=self._server.serve_forever,
                name="EminenceSyncHTTP",
                daemon=True,
            )
            self._server_thread.start()
        if self._discovery_socket is None:
            try:
                discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                discovery_socket.bind(("", DISCOVERY_PORT))
                discovery_socket.settimeout(1.0)
                self._discovery_socket = discovery_socket
                self._discovery_thread = threading.Thread(
                    target=self._serve_discovery,
                    name="EminenceSyncDiscovery",
                    daemon=True,
                )
                self._discovery_thread.start()
            except OSError:
                self._discovery_socket = None
        self.ip = _local_ip()
        return self.local_info()

    @staticmethod
    def _ensure_sync_timestamps():
        connection = get_connection()
        try:
            cursor = connection.cursor()
            for table in TABLES:
                columns = {
                    row[1] for row in cursor.execute(f"PRAGMA table_info({table})")
                }
                if not columns:
                    continue
                if "updated_at" not in columns:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN updated_at TEXT")
                cursor.execute(
                    f"UPDATE {table} SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)"
                )
                cursor.execute(
                    f"""
                    CREATE TRIGGER IF NOT EXISTS trg_{table}_sync_insert
                    AFTER INSERT ON {table}
                    WHEN NEW.updated_at IS NULL
                    BEGIN
                        UPDATE {table}
                        SET updated_at = COALESCE(NEW.created_at, CURRENT_TIMESTAMP)
                        WHERE id = NEW.id;
                    END
                    """
                )
                cursor.execute(
                    f"""
                    CREATE TRIGGER IF NOT EXISTS trg_{table}_sync_update
                    AFTER UPDATE ON {table}
                    WHEN NEW.updated_at IS OLD.updated_at
                    BEGIN
                        UPDATE {table}
                        SET updated_at = strftime('%Y-%m-%dT%H:%M:%f+00:00', 'now')
                        WHERE id = NEW.id;
                    END
                    """
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def stop(self):
        self._stopping.set()
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._discovery_socket is not None:
            self._discovery_socket.close()
            self._discovery_socket = None
        with self._lock:
            self._sessions.clear()
            self._challenges.clear()

    def rotate_pin(self):
        with self._lock:
            self.pin = self._new_pin()
            self._sessions.clear()
            self._challenges.clear()
        return self.local_info()

    def _serve_discovery(self):
        while not self._stopping.is_set():
            try:
                packet, address = self._discovery_socket.recvfrom(1024)
                if packet.decode("utf-8", errors="ignore") != DISCOVERY_REQUEST:
                    continue
                response = json.dumps({
                    "device_id": self.device_id,
                    "hostname": self.hostname,
                    "port": self.port,
                }).encode("utf-8")
                self._discovery_socket.sendto(response, address)
            except (OSError, AttributeError):
                break

    def discover_peers(self, timeout=2.5):
        peers = {}
        discovery = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            discovery.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            discovery.settimeout(0.25)
            discovery.bind(("", 0))
            discovery.sendto(
                DISCOVERY_REQUEST.encode("utf-8"),
                ("255.255.255.255", DISCOVERY_PORT),
            )
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    payload, address = discovery.recvfrom(4096)
                except socket.timeout:
                    continue
                try:
                    peer = json.loads(payload.decode("utf-8"))
                    if peer.get("device_id") == self.device_id:
                        continue
                    if not peer.get("device_id") or not peer.get("hostname"):
                        continue
                    peer["ip"] = address[0]
                    peer["port"] = int(peer.get("port", HTTP_PORT))
                    peers[peer["device_id"]] = peer
                except (ValueError, TypeError, json.JSONDecodeError):
                    continue
        finally:
            discovery.close()
        return list(peers.values())

    def create_challenge(self):
        challenge = secrets.token_hex(24)
        with self._lock:
            now = time.monotonic()
            self._challenges = {
                key: created for key, created in self._challenges.items()
                if now - created < PAIR_WINDOW_SECONDS
            }
            self._challenges[challenge] = now
        return challenge

    def verify_pairing(self, payload):
        challenge = payload.get("challenge", "")
        client_nonce = payload.get("client_nonce", "")
        client_device_id = payload.get("device_id", "")
        proof = payload.get("proof", "")
        with self._lock:
            created = self._challenges.pop(challenge, None)
            expected = hmac.new(
                self.pin.encode("ascii"),
                f"{challenge}:{client_nonce}:{client_device_id}".encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if (
                created is None
                or time.monotonic() - created > PAIR_WINDOW_SECONDS
                or not client_device_id
                or not hmac.compare_digest(expected, str(proof))
            ):
                raise PermissionError("PIN اشتباه است یا مهلت اتصال پایان یافته است.")
            token = secrets.token_urlsafe(32)
            self._sessions[token] = time.monotonic() + SESSION_SECONDS
            return token

    def validate_session(self, token):
        with self._lock:
            expiry = self._sessions.get(token)
            if expiry is None:
                return False
            if expiry <= time.monotonic():
                self._sessions.pop(token, None)
                return False
            return True

    def pair_with_peer(self, peer, pin):
        base_url = f"http://{peer['ip']}:{int(peer.get('port', HTTP_PORT))}"
        challenge_response = self._request_json("GET", f"{base_url}/v1/challenge")
        if challenge_response.get("device_id") != peer["device_id"]:
            raise ConnectionError("شناسه دستگاه پاسخ‌دهنده با دستگاه انتخاب‌شده مطابقت ندارد.")
        challenge = challenge_response["challenge"]
        client_nonce = secrets.token_hex(24)
        proof = hmac.new(
            pin.encode("ascii"),
            f"{challenge}:{client_nonce}:{self.device_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        response = self._request_json(
            "POST",
            f"{base_url}/v1/pair",
            {
                "challenge": challenge,
                "client_nonce": client_nonce,
                "device_id": self.device_id,
                "proof": proof,
            },
        )
        return {"token": response["token"]}

    def _last_sync(self, peer_id):
        connection = get_connection()
        try:
            key = f"lan_sync_last_{peer_id}"
            row = connection.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,),
            ).fetchone()
            return row["value"] if row else "1970-01-01T00:00:00+00:00"
        finally:
            connection.close()

    def _save_last_sync(self, peer_id, timestamp):
        connection = get_connection()
        try:
            connection.execute(
                "INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
                (f"lan_sync_last_{peer_id}", timestamp, _utc_now()),
            )
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _table_columns(cursor, table):
        return {row[1] for row in cursor.execute(f"PRAGMA table_info({table})")}

    def export_delta(self, since, role="engineer"):
        connection = get_connection()
        try:
            cursor = connection.cursor()
            result = {"tables": {}, "generated_at": _utc_now()}
            table_order = list(TABLES)
            if role == "admin":
                table_order = ["reports", "timesheets", "projects"]
            for table in table_order:
                columns = self._table_columns(cursor, table)
                if not columns:
                    result["tables"][table] = []
                    continue
                timestamp_column = "updated_at" if "updated_at" in columns else "created_at"
                if timestamp_column not in columns:
                    result["tables"][table] = []
                    continue
                rows = cursor.execute(
                    f"SELECT * FROM {table} WHERE COALESCE({timestamp_column}, '') > ?",
                    (since,),
                ).fetchall()
                result["tables"][table] = [dict(row) for row in rows]
            return result
        finally:
            connection.close()

    def merge_delta(self, payload):
        tables = payload.get("tables")
        if not isinstance(tables, dict):
            raise ValueError("ساختار داده دریافتی معتبر نیست.")
        connection = get_connection()
        merged_count = 0
        try:
            cursor = connection.cursor()
            ordered_tables = [table for table in tables if table in TABLES]
            for table in ordered_tables:
                rows = tables.get(table, [])
                if not isinstance(rows, list):
                    raise ValueError(f"داده جدول {table} معتبر نیست.")
                columns = self._table_columns(cursor, table)
                if not columns:
                    continue
                table_info = cursor.execute(f"PRAGMA table_info({table})").fetchall()
                primary_key = next((row[1] for row in table_info if row[5]), None)
                timestamp_column = "updated_at" if "updated_at" in columns else "created_at"
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    safe_row = {key: value for key, value in row.items() if key in columns}
                    if not primary_key or primary_key not in safe_row:
                        continue
                    existing = cursor.execute(
                        f"SELECT * FROM {table} WHERE {primary_key} = ?",
                        (safe_row[primary_key],),
                    ).fetchone()
                    incoming_time = str(safe_row.get(timestamp_column) or "")
                    existing_time = str(existing[timestamp_column] or "") if existing else ""
                    if existing and incoming_time <= existing_time:
                        continue
                    names = list(safe_row)
                    placeholders = ", ".join("?" for _ in names)
                    assignments = ", ".join(
                        f"{name} = excluded.{name}"
                        for name in names if name != primary_key
                    )
                    if not assignments:
                        continue
                    cursor.execute(
                        f"INSERT INTO {table} ({', '.join(names)}) VALUES ({placeholders}) "
                        f"ON CONFLICT({primary_key}) DO UPDATE SET {assignments}",
                        [safe_row[name] for name in names],
                    )
                    merged_count += 1
            connection.commit()
            return merged_count
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def sync_with_peer(self, peer, token, role="engineer"):
        base_url = f"http://{peer['ip']}:{int(peer.get('port', HTTP_PORT))}"
        since = self._last_sync(peer["device_id"])
        headers = {"Authorization": f"Bearer {token}"}
        query = urlencode({"since": since, "role": role})
        remote_delta = self._request_json(
            "GET", f"{base_url}/v1/delta?{query}", headers=headers,
        )
        local_delta = self.export_delta(since, role)
        posted = self._request_json(
            "POST", f"{base_url}/v1/merge", local_delta, headers=headers,
        )
        received_count = self.merge_delta(remote_delta)
        timestamp = max(
            _utc_now(),
            local_delta.get("generated_at", ""),
            remote_delta.get("generated_at", ""),
        )
        self._save_last_sync(peer["device_id"], timestamp)
        return {"received": received_count, "sent": int(posted.get("merged", 0))}

    @staticmethod
    def _request_json(method, url, payload=None, headers=None):
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request_headers = {"Accept": "application/json"}
        if body is not None:
            request_headers["Content-Type"] = "application/json; charset=utf-8"
        if headers:
            request_headers.update(headers)
        request = Request(url, data=body, headers=request_headers, method=method)
        try:
            with urlopen(request, timeout=8) as response:
                data = response.read(MAX_BODY_SIZE + 1)
            if len(data) > MAX_BODY_SIZE:
                raise ValueError("پاسخ دستگاه بیش از اندازه مجاز است.")
            return json.loads(data.decode("utf-8"))
        except HTTPError as exc:
            try:
                error = json.loads(exc.read().decode("utf-8")).get("error", str(exc))
            except Exception:
                error = str(exc)
            raise ConnectionError(error) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ConnectionError(f"ارتباط با دستگاه ناموفق بود: {exc}") from exc
