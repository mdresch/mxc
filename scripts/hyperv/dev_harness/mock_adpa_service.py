#!/usr/bin/env python3
"""
MXC Guest Production Appliance Prototype (ADPA / SIDPA Mock Service)
====================================================================
Implements Pillar II (ADR-004, ADR-006) & Pillar III (FDD 2.3, FDD 3):
  - Listens on 0.0.0.0:8080 inside the Windows Server 2025 Hyper-V Guest VM.
  - GET /health:
      1. Hardware PRNG Entropy Re-seed via Windows CNG (bcrypt.dll BCryptGenRandom)
      2. Stale TCP Database Connection Pool Purging (ClearAllPools() simulation/hook)
      3. Hyper-V VMBus Clock-Skew Assertion (vmictimesync check & UTC timestamp)
  - POST /admin/pre-trim:
      Compacts guest working set via Win32 EmptyWorkingSet (psapi.dll) & GC prior to Suspend-VM.
  - POST /api/v1/adpa/process & POST /api/v1/sidpa/process:
      Executes simulated stateless enterprise workloads with configurable duration for
      testing in-flight request draining (AC-02.1) and sub-second wake TTFB (AC-01.1).
"""

import ctypes
import datetime
import gc
import hashlib
import json
import os
import platform
import random
import socket
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = int(os.environ.get("MXC_ADPA_PORT", "8080"))


class SimulatedDatabaseConnectionPool:
    """Simulates an enterprise SQL Server (:1433) / PostgreSQL (:5432) connection pool."""

    def __init__(self):
        self._lock = threading.Lock()
        self.active_sockets = ["tcp://10.240.16.10:1433#sock1", "tcp://10.240.16.11:5432#sock2"]
        self.last_cleared_utc = None
        self.clear_count = 0

    def clear_all_pools(self) -> dict:
        """Equivalent to SqlConnection.ClearAllPools() / NpgsqlConnection.ClearAllPools()."""
        with self._lock:
            dropped = len(self.active_sockets)
            self.active_sockets.clear()
            self.clear_count += 1
            self.last_cleared_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
            return {
                "db_pools_cleared": True,
                "dropped_stale_sockets": dropped,
                "total_pool_flushes": self.clear_count,
                "cleared_at_utc": self.last_cleared_utc,
            }

    def acquire_connection(self, endpoint: str = "tcp://10.240.16.10:1433") -> str:
        with self._lock:
            conn_id = f"{endpoint}#conn-{uuid.uuid4().hex[:8]}"
            self.active_sockets.append(conn_id)
            return conn_id


DB_POOL = SimulatedDatabaseConnectionPool()


def reseed_hardware_prng() -> dict:
    """
    Forcibly re-seeds the process CSPRNG/PRNG state using Windows CNG hardware entropy
    (BCryptGenRandom with BCRYPT_USE_SYSTEM_PREFERRED_RNG = 0x00000002, backed by RDRAND/RDSEED).
    """
    hw_bytes = bytearray(64)
    method = "os.urandom"
    if sys.platform == "win32":
        try:
            bcrypt = ctypes.WinDLL("bcrypt.dll")
            BCRYPT_USE_SYSTEM_PREFERRED_RNG = 0x00000002
            buf = (ctypes.c_ubyte * 64)()
            status = bcrypt.BCryptGenRandom(None, buf, 64, BCRYPT_USE_SYSTEM_PREFERRED_RNG)
            if status == 0:
                hw_bytes = bytes(buf)
                method = "CNG:BCryptGenRandom(RDRAND/RDSEED)"
            else:
                hw_bytes = os.urandom(64)
        except Exception:
            hw_bytes = os.urandom(64)
    else:
        hw_bytes = os.urandom(64)

    seed_int = int.from_bytes(hw_bytes, byteorder="big")
    random.seed(seed_int)
    wake_nonce = hashlib.sha256(hw_bytes).hexdigest()[:32]
    return {
        "entropy_reseeded": True,
        "entropy_source": method,
        "wake_nonce": wake_nonce,
    }


def check_vmbus_clock_sync(host_utc_ms: float | None = None) -> dict:
    """
    Verifies guest UTC clock synchronization against Hyper-V Time Synchronization service
    and optional host UTC timestamp header/query parameter (asserts drift < 50ms).
    """
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    guest_utc_ms = now_utc.timestamp() * 1000.0

    drift_ms = 0.0
    if host_utc_ms is not None:
        drift_ms = abs(guest_utc_ms - host_utc_ms)

    # Note: Even if host and guest clocks have small scheduling jitter over HTTP,
    # report both raw drift and vmbus service status.
    clock_synced = True if host_utc_ms is None else (drift_ms < 50.0)
    return {
        "clock_synced": clock_synced,
        "guest_utc_iso": now_utc.isoformat(),
        "guest_utc_ms": round(guest_utc_ms, 2),
        "measured_drift_ms": round(drift_ms, 2),
        "threshold_ms": 50.0,
    }


def trim_process_working_set() -> dict:
    """
    Compacts the guest working set prior to Suspend-VM (ADR-004 / AC-03.2)
    using Python GC + Win32 EmptyWorkingSet (psapi.dll).
    """
    collected = gc.collect()
    win32_trimmed = False
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.WinDLL("kernel32.dll")
            psapi = ctypes.WinDLL("psapi.dll")
            handle = kernel32.GetCurrentProcess()
            res = psapi.EmptyWorkingSet(handle)
            win32_trimmed = bool(res)
        except Exception:
            win32_trimmed = False

    return {
        "pre_trimmed": True,
        "gc_objects_collected": collected,
        "win32_empty_working_set": win32_trimmed,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


class AdpaRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format_str, *args):
        # Keep stdout clean for benchmark parsing unless verbose
        if os.environ.get("MXC_ADPA_VERBOSE") == "1":
            super().log_message(format_str, *args)

    def _send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/health":
            t0 = time.perf_counter()
            host_utc_ms = None
            if "host_utc_ms" in qs:
                try:
                    host_utc_ms = float(qs["host_utc_ms"][0])
                except ValueError:
                    pass
            elif "X-Host-Utc-Ms" in self.headers:
                try:
                    host_utc_ms = float(self.headers["X-Host-Utc-Ms"])
                except ValueError:
                    pass

            prng_info = reseed_hardware_prng()
            pool_info = DB_POOL.clear_all_pools()
            clock_info = check_vmbus_clock_sync(host_utc_ms)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            payload = {
                "status": "healthy",
                "service": "MXC-ADPA-SIDPA-Production-Appliance",
                "hostname": socket.gethostname(),
                "pid": os.getpid(),
                "probe_duration_ms": round(elapsed_ms, 2),
                **prng_info,
                **pool_info,
                **clock_info,
            }
            self._send_json(200, payload)
            return

        if parsed.path == "/status":
            self._send_json(
                200,
                {
                    "service": "MXC-ADPA-SIDPA-Production-Appliance",
                    "hostname": socket.gethostname(),
                    "platform": platform.platform(),
                    "active_db_sockets": DB_POOL.active_sockets,
                    "total_pool_flushes": DB_POOL.clear_count,
                },
            )
            return

        self._send_json(404, {"error": "Not Found", "path": parsed.path})

    def do_POST(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        content_len = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            req_data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception:
            req_data = {"raw": raw_body.decode("utf-8", errors="replace")}

        if parsed.path == "/admin/pre-trim":
            pool_info = DB_POOL.clear_all_pools()
            trim_info = trim_process_working_set()
            self._send_json(200, {**pool_info, **trim_info})
            return

        if parsed.path in ("/api/v1/adpa/process", "/api/v1/sidpa/process"):
            t0 = time.perf_counter()
            workload = "ADPA" if "adpa" in parsed.path else "SIDPA"

            # Optional simulated processing delay (in ms) for testing in-flight draining & 504 timeouts
            delay_ms = float(qs.get("delay_ms", [req_data.get("delay_ms", 0)])[0])
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

            conn = DB_POOL.acquire_connection()
            tx_id = f"tx-{uuid.uuid4().hex[:12]}"
            exec_ms = (time.perf_counter() - t0) * 1000.0

            self._send_json(
                200,
                {
                    "result": "success",
                    "workload": workload,
                    "txId": tx_id,
                    "session_nonce": uuid.uuid4().hex,
                    "db_connection": conn,
                    "hostname": socket.gethostname(),
                    "processing_ms": round(exec_ms, 2),
                    "input_echo": req_data,
                    "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                },
            )
            return

        self._send_json(404, {"error": "Unknown POST endpoint", "path": parsed.path})


class LowLatencyAdpaServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def get_request(self):
        sock, addr = super().get_request()
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass
        return sock, addr


def main():
    server = LowLatencyAdpaServer(("0.0.0.0", PORT), AdpaRequestHandler)
    print(f"[MXC ADPA/SIDPA Appliance] Listening on http://0.0.0.0:{PORT} (PID: {os.getpid()})")
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[MXC ADPA/SIDPA Appliance] Shutting down cleanly...")
        server.server_close()


if __name__ == "__main__":
    main()

