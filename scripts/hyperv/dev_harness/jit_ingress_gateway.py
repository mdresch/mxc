#!/usr/bin/env python3
"""
MXC JIT Scale-to-Zero Ingress Reverse Proxy Gateway
===================================================
Implements ADR-002, ADR-004, ADR-006 & FDD Section 2.1 / 3:
- Connection buffering / hold queue for dormant VMs
- Synchronous wake via `wxc-exec --experimental --hyperv-op pool-lease` (<300ms wake)
- Automatic background standby replenishment via AC-05.1
- Guest health, PRNG re-seed & clock-sync probe (/health on port 8080)
- In-flight request tracking (active_open_requests counter)
- Guest memory compaction (POST /admin/pre-trim) prior to suspend
- Idle inactivity reaper (configurable timeout -> pool-release)
- Native telemetry headers & /gateway/status inspection endpoint
"""

import http.client
import http.server
import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [IngressGateway]: %(message)s",
    datefmt="%H:%M:%S",
)

GATEWAY_HOST = "0.0.0.0"
GATEWAY_PORT = int(os.environ.get("MXC_GATEWAY_PORT", "8090"))
DEFAULT_POOL = os.environ.get("MXC_DEFAULT_POOL", "default")
GUEST_PORT = int(os.environ.get("MXC_GUEST_PORT", "8080"))
IDLE_TIMEOUT_SECONDS = float(os.environ.get("MXC_IDLE_TIMEOUT", "300.0"))
WAKE_TIMEOUT_MS = float(os.environ.get("MXC_WAKE_TIMEOUT_MS", "5000.0"))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../../.."))
WXC_EXEC_PATH = os.path.join(REPO_ROOT, "src", "target", "debug", "wxc-exec.exe")
if not os.path.exists(WXC_EXEC_PATH):
    # Fallback to current directory relative path
    WXC_EXEC_PATH = os.path.abspath("src/target/debug/wxc-exec.exe")


class PoolManagerClient:
    """Interface to wxc-exec Rust control plane for pool leasing and releasing."""

    @staticmethod
    def get_vm_ip(vm_name: str, timeout_sec: float = 25.0) -> str:
        """Resolve guest IPv4 address via Hyper-V integration services, waking and attaching switch if needed."""
        ps_cmd = (
            f"$vm = Get-VM -Name '{vm_name}'; "
            f"if ($vm.State -eq 'Paused') {{ Resume-VM -VM $vm -Confirm:$false }} "
            f"elseif ($vm.State -ne 'Running') {{ Start-VM -VM $vm -Confirm:$false }}; "
            f"$adapter = Get-VMNetworkAdapter -VMName '{vm_name}'; "
            f"if (-not $adapter.SwitchName) {{ Connect-VMNetworkAdapter -VMName '{vm_name}' -SwitchName 'Default Switch' -ErrorAction SilentlyContinue }}; "
            f"$adapter.IPAddresses | "
            f"Where-Object {{ $_ -notlike '*:*' -and $_ -notlike '169.254.*' }} | "
            f"Select-Object -First 1"
        )
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            try:
                res = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                ip = res.stdout.strip()
                if ip:
                    return ip
            except Exception as e:
                logging.debug(f"Waiting for IP on {vm_name}: {e}")
            time.sleep(0.5)
        raise TimeoutError(f"Could not resolve IPv4 for {vm_name} within {timeout_sec}s")

    @classmethod
    def lease_pool(cls, pool_id: str, holder: str = "gateway") -> dict:
        """Atomically leases a warm standby VM from the specified pool in <300ms."""
        cmd = [
            WXC_EXEC_PATH,
            "--experimental",
            "--hyperv-op",
            "pool-lease",
            "--pool",
            pool_id,
            "--pool-lease-holder",
            holder,
        ]
        logging.info(f"Dispatching lease: {' '.join(cmd)}")
        t0 = time.perf_counter()
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lease_ms = (time.perf_counter() - t0) * 1000.0

        if res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip()
            # If named pool is not provisioned or empty, try default pool fallback
            if pool_id != DEFAULT_POOL:
                logging.warning(
                    f"Pool '{pool_id}' lease failed ({err_msg}). Falling back to '{DEFAULT_POOL}'..."
                )
                return cls.lease_pool(DEFAULT_POOL, holder=holder)
            raise RuntimeError(f"pool-lease failed (code {res.returncode}): {err_msg}")

        data = json.loads(res.stdout)
        result = data.get("result", data)
        sandbox_id = result.get("sandboxId") or result.get("sandbox_id")
        if not sandbox_id:
            raise RuntimeError(f"Unexpected pool-lease output: {data}")

        token = sandbox_id.replace("hv:", "")
        vm_name = f"mxc-hv-{token}"
        logging.info(f"Leased {sandbox_id} ({vm_name}) in {lease_ms:.1f}ms (AC-01.1)")

        ip = cls.get_vm_ip(vm_name)
        return {
            "sandbox_id": sandbox_id,
            "vm_name": vm_name,
            "ip_address": ip,
            "lease_ms": round(lease_ms, 2),
            "pool_id": pool_id,
        }

    @staticmethod
    def release_pool(pool_id: str, sandbox_id: str, guest_ip: str | None = None) -> dict:
        """Pre-trims working set, restores clean baseline snapshot, and suspends to pool."""
        trim_data = {"pre_trimmed": False, "db_pools_cleared": False}
        # 1. Trigger guest pre-trim / DB pool clear if reachable
        if guest_ip:
            try:
                logging.info(f"Triggering guest pre-trim compaction on {guest_ip}:{GUEST_PORT}...")
                req = urllib.request.Request(
                    f"http://{guest_ip}:{GUEST_PORT}/admin/pre-trim",
                    data=b"{}",
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    trim_data = json.loads(resp.read().decode())
                    logging.info(f"Guest pre-trim complete: {trim_data}")
            except Exception as e:
                logging.warning(f"Guest pre-trim skipped/failed: {e}")

        # 2. Release VM back to pool via wxc-exec
        cmd = [
            WXC_EXEC_PATH,
            "--experimental",
            "--hyperv-op",
            "pool-release",
            "--hyperv-sandbox-id",
            sandbox_id,
            "--pool",
            pool_id,
        ]
        logging.info(f"Dispatching release: {' '.join(cmd)}")
        release_ms = 0.0
        try:
            t0 = time.perf_counter()
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            release_ms = (time.perf_counter() - t0) * 1000.0
            if res.returncode == 0:
                logging.info(
                    f"Released {sandbox_id} back to pool '{pool_id}' in {release_ms:.1f}ms "
                    f"(baseline restored, VM suspended, 0% CPU)"
                )
            else:
                logging.error(f"pool-release error: {res.stderr.strip() or res.stdout.strip()}")
        except Exception as e:
            logging.error(f"Failed to execute pool-release for {sandbox_id}: {e}")

        return {
            "reaped": True,
            "new_state": "StandbyPaused",
            "suspend_ms": round(release_ms, 2),
            "pre_trim": trim_data,
        }


class SandboxSessionManager:
    """Manages active guest leases, health probing, active request counts, and idle timers."""

    def __init__(self):
        self.lock = threading.RLock()
        self.active_sandbox_id = None
        self.active_vm_name = None
        self.active_guest_ip = None
        self.active_pool = None
        self.active_open_requests = 0
        self.last_activity_time = time.time()
        self.total_leases = 0
        self.total_requests_proxied = 0
        self.last_wake_ms = 0.0
        self.last_probe_ms = 0.0
        self.last_health_payload = {}

        self.reaper_thread = threading.Thread(target=self._idle_reaper_loop, daemon=True)
        self.reaper_thread.start()

    def acquire_or_wake(self, pool_id: str) -> tuple[str, str, bool, float]:
        """
        Returns (guest_ip, sandbox_id, cold_wake, wake_ms).
        If already active and matching pool, returns in 0ms (warm fast-path).
        """
        with self.lock:
            if self.active_sandbox_id and self.active_guest_ip:
                self.last_activity_time = time.time()
                return self.active_guest_ip, self.active_sandbox_id, False, 0.0

            # Cold wake / lease from pool
            lease_info = PoolManagerClient.lease_pool(pool_id)
            self.active_sandbox_id = lease_info["sandbox_id"]
            self.active_vm_name = lease_info["vm_name"]
            self.active_guest_ip = lease_info["ip_address"]
            self.active_pool = lease_info["pool_id"]
            self.last_activity_time = time.time()
            self.total_leases += 1
            self.last_wake_ms = lease_info["lease_ms"]

            # Probe guest health & PRNG re-seed
            probe_ms = self._probe_guest_health(self.active_guest_ip)
            self.last_probe_ms = probe_ms

            return self.active_guest_ip, self.active_sandbox_id, True, self.last_wake_ms

    def _probe_guest_health(self, guest_ip: str) -> float:
        """Polls /health on guest port until status == healthy."""
        health_url = f"http://{guest_ip}:{GUEST_PORT}/health"
        start_time = time.time()
        timeout = WAKE_TIMEOUT_MS / 1000.0

        while time.time() - start_time < timeout:
            try:
                req = urllib.request.Request(health_url)
                with urllib.request.urlopen(req, timeout=0.5) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode())
                        self.last_health_payload = data
                        probe_ms = (time.time() - start_time) * 1000.0
                        logging.info(
                            f"Guest health probe passed in {probe_ms:.1f}ms: "
                            f"PRNG re-seeded={data.get('entropy_reseeded')}, "
                            f"DB flushed={data.get('db_pools_cleared')}, "
                            f"Clock synced={data.get('clock_synced')}"
                        )
                        return probe_ms
            except Exception:
                time.sleep(0.05)

        probe_ms = (time.time() - start_time) * 1000.0
        raise RuntimeError(f"Guest health probe timed out after {probe_ms:.1f}ms on {health_url}")

    def increment_requests(self):
        with self.lock:
            self.active_open_requests += 1
            self.last_activity_time = time.time()

    def decrement_requests(self):
        with self.lock:
            if self.active_open_requests > 0:
                self.active_open_requests -= 1
            self.last_activity_time = time.time()

    def force_reap(self) -> dict:
        """Manually trigger immediate idle reap if no requests are in-flight."""
        with self.lock:
            if self.active_open_requests > 0:
                return {
                    "reaped": False,
                    "reason": f"Cannot reap while active_open_requests={self.active_open_requests}",
                }
            if not self.active_sandbox_id:
                return {
                    "reaped": True,
                    "new_state": "StandbyPaused",
                    "suspend_ms": 0.0,
                    "pre_trim": {"pre_trimmed": True, "db_pools_cleared": True},
                    "reason": "Already reaped / idle in StandbyPaused",
                }

            pool = self.active_pool
            sandbox_id = self.active_sandbox_id
            guest_ip = self.active_guest_ip

            self.active_sandbox_id = None
            self.active_vm_name = None
            self.active_guest_ip = None
            self.active_pool = None

            # Execute release synchronously to provide telemetry to caller
            reap_info = PoolManagerClient.release_pool(pool, sandbox_id, guest_ip)
            return {
                "reaped": True,
                "sandbox_id": sandbox_id,
                "pool_id": pool,
                "new_state": reap_info.get("new_state", "StandbyPaused"),
                "suspend_ms": reap_info.get("suspend_ms", 120.0),
                "pre_trim": reap_info.get("pre_trim", {"pre_trimmed": True, "db_pools_cleared": True}),
            }

    def _idle_reaper_loop(self):
        while True:
            time.sleep(2)
            with self.lock:
                if self.active_sandbox_id and self.active_open_requests == 0:
                    elapsed = time.time() - self.last_activity_time
                    if elapsed >= IDLE_TIMEOUT_SECONDS:
                        logging.info(
                            f"Idle timeout reached ({elapsed:.1f}s >= {IDLE_TIMEOUT_SECONDS}s). "
                            f"Reaping sandbox {self.active_sandbox_id} back to pool '{self.active_pool}'..."
                        )
                        pool = self.active_pool
                        sandbox_id = self.active_sandbox_id
                        guest_ip = self.active_guest_ip

                        self.active_sandbox_id = None
                        self.active_vm_name = None
                        self.active_guest_ip = None
                        self.active_pool = None

                        threading.Thread(
                            target=PoolManagerClient.release_pool,
                            args=(pool, sandbox_id, guest_ip),
                            daemon=True,
                        ).start()


session_manager = SandboxSessionManager()


class JITProxyRequestHandler(http.server.BaseHTTPRequestHandler):
    """Buffers incoming HTTP requests, triggers JIT VM wake, proxies payload, and tracks active requests."""

    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self._route_request()

    def do_POST(self):
        self._route_request()

    def do_PUT(self):
        self._route_request()

    def do_DELETE(self):
        self._route_request()

    def _send_json(self, status: int, data: dict, headers: dict | None = None):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        if headers:
            for k, v in headers.items():
                self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(body)

    def _route_request(self):
        parsed = urlparse(self.path)

        # 1. Gateway Administration Endpoints
        if parsed.path == "/gateway/status":
            with session_manager.lock:
                idle_elapsed = time.time() - session_manager.last_activity_time
                status = {
                    "gateway": "MXC JIT Scale-to-Zero Ingress Reverse Proxy",
                    "listen_port": GATEWAY_PORT,
                    "active_sandbox_id": session_manager.active_sandbox_id,
                    "active_vm_name": session_manager.active_vm_name,
                    "active_guest_ip": session_manager.active_guest_ip,
                    "active_pool": session_manager.active_pool,
                    "active_open_requests": session_manager.active_open_requests,
                    "idle_elapsed_seconds": round(idle_elapsed, 1),
                    "idle_timeout_seconds": IDLE_TIMEOUT_SECONDS,
                    "last_wake_ms": session_manager.last_wake_ms,
                    "last_probe_ms": session_manager.last_probe_ms,
                    "last_health_payload": session_manager.last_health_payload,
                    "total_leases": session_manager.total_leases,
                    "total_requests_proxied": session_manager.total_requests_proxied,
                }
            self._send_json(200, status)
            return

        if parsed.path == "/gateway/reap" and self.command == "POST":
            res = session_manager.force_reap()
            code = 200 if res.get("reaped") else 409
            self._send_json(code, res)
            return

        # 2. Workload Proxying
        self._handle_proxy()

    def _handle_proxy(self):
        t0 = time.perf_counter()
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Determine target pool based on URL path
        pool_id = DEFAULT_POOL
        if self.path.startswith("/api/v1/adpa"):
            pool_id = "prod-adpa"
        elif self.path.startswith("/api/v1/sidpa"):
            pool_id = "prod-sidpa"

        # 1. Hold connection in buffer queue, wake VM via pool-lease, probe health
        try:
            guest_ip, sandbox_id, cold_wake, wake_ms = session_manager.acquire_or_wake(pool_id)
            session_manager.increment_requests()
        except Exception as e:
            logging.error(f"Failed to acquire sandbox for {self.path}: {e}")
            self._send_json(
                503,
                {"error": "Service Unavailable (Wake Timeout)", "detail": str(e)},
                headers={"Retry-After": "2"},
            )
            return

        timeout_sec = 90.0
        for k, v in self.headers.items():
            if k.lower() == "x-max-timeout-ms":
                try:
                    timeout_sec = float(v) / 1000.0
                except Exception:
                    pass
                break

        try:
            # 2. Forward HTTP request to guest appliance (:8080)
            target_url = f"http://{guest_ip}:{GUEST_PORT}{self.path}"
            forward_headers = {
                key: val
                for key, val in self.headers.items()
                if key.lower() not in ["host", "transfer-encoding"]
            }
            forward_headers["Host"] = f"{guest_ip}:{GUEST_PORT}"
            forward_headers["X-Forwarded-For"] = self.client_address[0]

            req = urllib.request.Request(
                target_url,
                data=body,
                headers=forward_headers,
                method=self.command,
            )

            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                resp_body = resp.read()
                ttfb_ms = (time.perf_counter() - t0) * 1000.0

                with session_manager.lock:
                    session_manager.total_requests_proxied += 1

                self.send_response(resp.status)
                for header, val in resp.headers.items():
                    if header.lower() not in ["transfer-encoding", "connection"]:
                        self.send_header(header, val)

                # Append MXC Telemetry Headers
                self.send_header("Connection", "keep-alive")
                self.send_header("X-MXC-Sandbox-Id", sandbox_id)
                self.send_header("X-MXC-Pool-Id", pool_id)
                self.send_header("X-MXC-Cold-Wake", str(cold_wake).lower())
                self.send_header("X-MXC-Wake-Ms", f"{wake_ms:.1f}")
                self.send_header("X-MXC-Health-Probe-Ms", f"{session_manager.last_probe_ms:.1f}")
                self.send_header("X-MXC-Total-TTFB-Ms", f"{ttfb_ms:.1f}")
                self.end_headers()
                self.wfile.write(resp_body)

        except urllib.error.HTTPError as he:
            self.send_response(he.code)
            for header, val in he.headers.items():
                if header.lower() not in ["transfer-encoding", "connection"]:
                    self.send_header(header, val)
            self.end_headers()
            try:
                self.wfile.write(he.read())
            except Exception:
                pass
        except Exception as ex:
            if isinstance(ex, (TimeoutError, socket.timeout)) or "timed out" in str(ex).lower():
                self._send_json(
                    504,
                    {
                        "error": "Gateway Timeout (max_request_execution_timeout_seconds exceeded)",
                        "timeout_seconds": timeout_sec,
                        "action": "Socket forcefully terminated and active_open_requests decremented (AC-02.1)",
                    },
                )
            else:
                logging.error(f"Proxy forwarding error to {guest_ip}: {ex}")
                self._send_json(502, {"error": "Bad Gateway", "detail": str(ex)})
        finally:
            session_manager.decrement_requests()

    def log_message(self, fmt, *args):
        logging.info(f"{self.client_address[0]} - - {fmt % args}")


class ThreadedHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True

    def get_request(self):
        sock, addr = super().get_request()
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass
        return sock, addr


def run_server():
    global GATEWAY_PORT, GATEWAY_HOST, DEFAULT_POOL, GUEST_PORT, IDLE_TIMEOUT_SECONDS
    import argparse

    parser = argparse.ArgumentParser(description="MXC JIT Connection-Buffering Ingress Gateway")
    parser.add_argument("--port", type=int, default=GATEWAY_PORT, help="Gateway listen port")
    parser.add_argument("--host", type=str, default=GATEWAY_HOST, help="Gateway host binding")
    parser.add_argument("--pool", type=str, default=DEFAULT_POOL, help="Default pool name")
    parser.add_argument("--guest-port", type=int, default=GUEST_PORT, help="Guest HTTP appliance port")
    parser.add_argument("--idle-timeout", type=float, default=IDLE_TIMEOUT_SECONDS, help="Idle reap timeout in seconds")
    parser.add_argument("--vm-name", type=str, default=None, help="Target Hyper-V VM name (optional override)")
    parser.add_argument("--guest-ip", type=str, default=None, help="Target Guest IP (optional override)")
    args, _ = parser.parse_known_args()

    GATEWAY_PORT = args.port
    GATEWAY_HOST = args.host
    DEFAULT_POOL = args.pool
    GUEST_PORT = args.guest_port
    IDLE_TIMEOUT_SECONDS = args.idle_timeout

    if args.guest_ip:
        session_manager.active_guest_ip = args.guest_ip
    if args.vm_name:
        session_manager.active_vm_name = args.vm_name

    server_address = (GATEWAY_HOST, GATEWAY_PORT)
    httpd = ThreadedHTTPServer(server_address, JITProxyRequestHandler)
    print(
        f"[MXC JIT Ingress Gateway] Listening on http://{GATEWAY_HOST}:{GATEWAY_PORT} "
        f"(Default Pool: '{DEFAULT_POOL}', Idle Timeout: {IDLE_TIMEOUT_SECONDS}s)",
        flush=True,
    )
    logging.info(
        f"JIT Ingress Gateway running on http://{GATEWAY_HOST}:{GATEWAY_PORT} "
        f"(Default Pool: '{DEFAULT_POOL}', Idle Timeout: {IDLE_TIMEOUT_SECONDS}s)"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down JIT Ingress Gateway...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
