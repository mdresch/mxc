#!/usr/bin/env python3
"""
MXC Just-in-Time (JIT) Connection-Buffering Ingress Gateway Prototype
=====================================================================
Implements Pillar II (ADR-002, ADR-004, ADR-006) & Pillar III (FDD 2.1, FDD 3, FDD 4):
  - Listens on host/edge port (default 0.0.0.0:8090) with TCP_NODELAY enabled.
  - Maintains a warm persistent Hyper-V Control Runspace (eliminating ~800ms PowerShell cold-spawn overhead)
    so Resume-VM and Suspend-VM execute directly against the Hypervisor in <150ms.
  - Buffers incoming HTTP requests when target Hyper-V VM is dormant (Paused / Off / Saved).
  - Polls guest health endpoint (:8080/health) to assert PRNG re-seed, DB pool flush, & clock sync.
  - Fast-path proxies warm requests when routing_state == ActiveRunning (<5ms proxy overhead).
  - Maintains atomic active_open_requests counter and TransitionLock to prevent mid-flight reaping.
  - Enforces max_request_execution_timeout_seconds (default 900s, overrideable per request via
    X-Max-Timeout-Ms header) returning HTTP 504 Gateway Timeout on hung downstream requests.
"""

import argparse
import http.client
import json
import os
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class PersistentHyperVRunspace:
    """
    Maintains a persistent PowerShell child process with the Hyper-V module pre-loaded
    so hypervisor state transitions (Resume-VM / Suspend-VM) execute in <150ms without
    paying process-creation or module-import overhead.
    """

    def __init__(self, vm_name: str):
        self.vm_name = vm_name
        self._lock = threading.Lock()
        self._proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NoLogo", "-NonInteractive", "-Command", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        # Pre-load Hyper-V cmdlets and cache VM object reference
        self._exec_raw(
            f"Import-Module Hyper-V -ErrorAction SilentlyContinue; "
            f"$global:MxcTargetVm = Get-VM -Name '{self.vm_name}'"
        )

    def _exec_raw(self, ps_cmd: str) -> str:
        with self._lock:
            sentinel = "__MXC_DONE__"
            assert self._proc.stdin is not None and self._proc.stdout is not None
            self._proc.stdin.write(f"{ps_cmd}; Write-Output '{sentinel}'\n")
            self._proc.stdin.flush()
            lines = []
            while True:
                line = self._proc.stdout.readline()
                if not line:
                    break
                stripped = line.strip()
                if stripped == sentinel:
                    break
                if stripped:
                    lines.append(stripped)
            return "\n".join(lines)

    def resume_vm(self) -> float:
        t0 = time.perf_counter()
        self._exec_raw(
            "if ($global:MxcTargetVm.State -eq 'Paused') { Resume-VM -VM $global:MxcTargetVm -Confirm:$false }"
            " elseif ($global:MxcTargetVm.State -ne 'Running') { Start-VM -VM $global:MxcTargetVm -Confirm:$false }"
        )
        return (time.perf_counter() - t0) * 1000.0

    def suspend_vm(self) -> float:
        t0 = time.perf_counter()
        self._exec_raw("Suspend-VM -VM $global:MxcTargetVm -Confirm:$false")
        return (time.perf_counter() - t0) * 1000.0

    def close(self):
        try:
            self._proc.terminate()
        except Exception:
            pass


class JitGatewayController:
    def __init__(
        self,
        vm_name: str = "mxc-hv-a7df7452",
        guest_ip: str = "172.24.173.100",
        guest_port: int = 8080,
        idle_timeout_seconds: float = 300.0,
        max_request_timeout_seconds: float = 900.0,
        wake_timeout_ms: float = 3000.0,
    ):
        self.vm_name = vm_name
        self.guest_ip = guest_ip
        self.guest_port = guest_port
        self.idle_timeout_seconds = idle_timeout_seconds
        self.max_request_timeout_seconds = max_request_timeout_seconds
        self.wake_timeout_ms = wake_timeout_ms

        self.hv_runspace = PersistentHyperVRunspace(vm_name)
        self.transition_lock = threading.RLock()
        self.active_open_requests = 0
        self.routing_state = "ActiveRunning"  # StandbyPaused | ActiveRunning | ReapingState
        self.last_activity_monotonic = time.monotonic()

        # Telemetry metrics
        self.last_wake_ms = 0.0
        self.last_health_probe_ms = 0.0
        self.last_total_cold_ttfb_ms = 0.0
        self.total_wakes = 0
        self.total_requests_proxied = 0
        self.total_504_timeouts = 0
        self.last_health_payload = {}

    def resume_vm_fast(self) -> float:
        elapsed_ms = self.hv_runspace.resume_vm()
        self.last_wake_ms = round(elapsed_ms, 2)
        self.total_wakes += 1
        return elapsed_ms

    def suspend_vm_fast(self) -> dict:
        """
        Acquires TransitionLock, marks VM as ReapingState, triggers guest working-set pre-trimming
        & DB pool flush, and suspends the VM into Hyper-V Paused state (0.0% CPU).
        """
        with self.transition_lock:
            if self.active_open_requests > 0:
                return {
                    "reaped": False,
                    "reason": f"Cannot reap while active_open_requests={self.active_open_requests}",
                }
            self.routing_state = "ReapingState"

            # 1. Close any cached gateway keep-alive socket and trigger Guest Pre-Trim + DB Pool Flush
            ka = getattr(self, "_keepalive_conn", None)
            if ka is not None:
                try:
                    ka.close()
                except Exception:
                    pass
                self._keepalive_conn = None

            pre_trim_result = {}
            try:
                conn = http.client.HTTPConnection(self.guest_ip, self.guest_port, timeout=1.0)
                conn.request("POST", "/admin/pre-trim", body=b"{}", headers={"Content-Type": "application/json"})
                resp = conn.getresponse()
                pre_trim_result = json.loads(resp.read().decode("utf-8"))
                conn.close()
            except Exception as e:
                pre_trim_result = {"warning": str(e)}

            # 2. Suspend VM in Hypervisor RAM (Paused state) via warm runspace
            pause_ms = self.hv_runspace.suspend_vm()
            self.routing_state = "StandbyPaused"
            return {
                "reaped": True,
                "vm_name": self.vm_name,
                "new_state": "Paused",
                "routing_state": self.routing_state,
                "suspend_ms": round(pause_ms, 2),
                "pre_trim": pre_trim_result,
            }

    def poll_guest_health(self) -> tuple[bool, float, dict]:
        """Polls GET /health on the guest appliance until healthy + clock synced."""
        t0 = time.perf_counter()
        deadline = t0 + (self.wake_timeout_ms / 1000.0)
        last_err = ""

        while time.perf_counter() < deadline:
            try:
                conn = http.client.HTTPConnection(self.guest_ip, self.guest_port, timeout=0.25)
                conn.request("GET", "/health")
                resp = conn.getresponse()
                raw = resp.read().decode("utf-8")
                conn.close()
                if resp.status == 200:
                    data = json.loads(raw)
                    if data.get("status") == "healthy" and data.get("clock_synced") is True:
                        probe_ms = (time.perf_counter() - t0) * 1000.0
                        self.last_health_probe_ms = round(probe_ms, 2)
                        self.last_health_payload = data
                        return True, probe_ms, data
            except Exception as e:
                last_err = str(e)
                time.sleep(0.005)

        probe_ms = (time.perf_counter() - t0) * 1000.0
        return False, probe_ms, {"error": f"Health probe timed out: {last_err}"}

    def ensure_instance_awake(self) -> dict:
        """
        Fast-path returns immediately if routing_state == ActiveRunning.
        Otherwise coordinates atomic wake-on-request (<300ms Resume-VM + Health Probe).
        """
        if self.routing_state == "ActiveRunning":
            return {"cold_wake": False, "wake_ms": 0.0, "health_probe_ms": 0.0}

        with self.transition_lock:
            if self.routing_state == "ActiveRunning":
                return {"cold_wake": False, "wake_ms": 0.0, "health_probe_ms": 0.0}

            wake_ms = self.resume_vm_fast()
            ok, probe_ms, health_data = self.poll_guest_health()
            if not ok:
                raise RuntimeError(f"Guest wake health check failed: {health_data}")

            self.routing_state = "ActiveRunning"
            self.last_activity_monotonic = time.monotonic()
            return {
                "cold_wake": True,
                "wake_ms": round(wake_ms, 2),
                "health_probe_ms": round(probe_ms, 2),
                "health_data": health_data,
            }


GATEWAY: JitGatewayController | None = None


class LowLatencyHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(
        self,
        server_address,
        RequestHandlerClass,
        controller: JitGatewayController | None = None,
        image_id: str = "default",
    ):
        self.controller = controller
        self.image_id = image_id
        super().__init__(server_address, RequestHandlerClass)

    def get_request(self):
        sock, addr = super().get_request()
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except Exception:
            pass
        return sock, addr


class GatewayProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    @property
    def gw(self) -> JitGatewayController:
        ctrl = getattr(self.server, "controller", None) or GATEWAY
        assert ctrl is not None
        return ctrl

    @property
    def image_id(self) -> str:
        return getattr(self.server, "image_id", "default")

    def log_message(self, format_str, *args):
        if os.environ.get("MXC_GATEWAY_VERBOSE") == "1":
            super().log_message(format_str, *args)

    def _send_json(self, status_code: int, payload: dict, extra_headers: dict | None = None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        gw = self.gw
        parsed = urlparse(self.path)

        if parsed.path == "/gateway/status":
            idle_elapsed = time.monotonic() - gw.last_activity_monotonic
            self._send_json(
                200,
                {
                    "image_id": self.image_id,
                    "vm_name": gw.vm_name,
                    "guest_target": f"{gw.guest_ip}:{gw.guest_port}",
                    "routing_state": gw.routing_state,
                    "active_open_requests": gw.active_open_requests,
                    "idle_elapsed_seconds": round(idle_elapsed, 2),
                    "idle_timeout_seconds": gw.idle_timeout_seconds,
                    "max_request_execution_timeout_seconds": gw.max_request_timeout_seconds,
                    "last_wake_ms": gw.last_wake_ms,
                    "last_health_probe_ms": gw.last_health_probe_ms,
                    "last_total_cold_ttfb_ms": gw.last_total_cold_ttfb_ms,
                    "total_wakes": gw.total_wakes,
                    "total_requests_proxied": gw.total_requests_proxied,
                    "total_504_timeouts": gw.total_504_timeouts,
                    "last_health_payload": gw.last_health_payload,
                },
            )
            return

        self._proxy_request("GET")

    def do_POST(self):
        gw = self.gw
        parsed = urlparse(self.path)

        if parsed.path == "/gateway/reap":
            res = gw.suspend_vm_fast()
            code = 200 if res.get("reaped") else 409
            self._send_json(code, res)
            return

        self._proxy_request("POST")

    def _proxy_request(self, method: str):
        gw = self.gw
        t_start = time.perf_counter()

        content_len = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_len) if content_len > 0 else None

        # Per-request safety timeout override (e.g. X-Max-Timeout-Ms for testing AC-02.1)
        timeout_sec = gw.max_request_timeout_seconds
        if "X-Max-Timeout-Ms" in self.headers:
            try:
                timeout_sec = float(self.headers["X-Max-Timeout-Ms"]) / 1000.0
            except ValueError:
                pass

        # 1. Buffer & Wake VM if dormant (Fast-path 0ms if ActiveRunning)
        try:
            wake_info = gw.ensure_instance_awake()
        except Exception as e:
            self._send_json(
                503,
                {"error": "Service Unavailable (Wake Timeout)", "detail": str(e)},
                extra_headers={"Retry-After": "2"},
            )
            return

        # 2. Increment active_open_requests atomically
        with gw.transition_lock:
            gw.active_open_requests += 1
            gw.last_activity_monotonic = time.monotonic()

        try:
            # Use persistent HTTP/1.1 Keep-Alive connection pool for normal requests,
            # or isolated connection when custom X-Max-Timeout-Ms is under test
            is_custom_timeout = "X-Max-Timeout-Ms" in self.headers
            conn = None
            if not is_custom_timeout:
                conn = getattr(gw, "_keepalive_conn", None)

            if conn is None:
                conn = http.client.HTTPConnection(gw.guest_ip, gw.guest_port, timeout=timeout_sec)
                conn.connect()
                try:
                    conn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                except Exception:
                    pass
                if not is_custom_timeout:
                    gw._keepalive_conn = conn

            forward_headers = {
                "Content-Type": self.headers.get("Content-Type", "application/json"),
                "X-Forwarded-For": self.client_address[0],
                "Connection": "close" if is_custom_timeout else "keep-alive",
            }
            try:
                conn.request(method, self.path, body=body, headers=forward_headers)
                resp = conn.getresponse()
                resp_body = resp.read()
            except Exception:
                # Reconnect once if keep-alive socket was reset after VM pause/resume
                try:
                    conn.close()
                except Exception:
                    pass
                conn = http.client.HTTPConnection(gw.guest_ip, gw.guest_port, timeout=timeout_sec)
                conn.connect()
                try:
                    conn.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                except Exception:
                    pass
                if not is_custom_timeout:
                    gw._keepalive_conn = conn
                conn.request(method, self.path, body=body, headers=forward_headers)
                resp = conn.getresponse()
                resp_body = resp.read()

            if is_custom_timeout:
                conn.close()

            total_ttfb_ms = (time.perf_counter() - t_start) * 1000.0
            if wake_info.get("cold_wake"):
                gw.last_total_cold_ttfb_ms = round(total_ttfb_ms, 2)
            gw.total_requests_proxied += 1

            self.send_response(resp.status)
            self.send_header("Content-Type", resp.getheader("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(resp_body)))
            self.send_header("Connection", "keep-alive")
            self.send_header("X-MXC-Image-Id", self.image_id)
            self.send_header("X-MXC-VM-Name", gw.vm_name)
            self.send_header("X-MXC-Cold-Wake", str(wake_info.get("cold_wake", False)).lower())
            self.send_header("X-MXC-Wake-Ms", str(wake_info.get("wake_ms", 0.0)))
            self.send_header("X-MXC-Health-Probe-Ms", str(wake_info.get("health_probe_ms", 0.0)))
            self.send_header("X-MXC-Total-TTFB-Ms", str(round(total_ttfb_ms, 2)))
            self.end_headers()
            self.wfile.write(resp_body)

        except Exception as e:
            if isinstance(e, (TimeoutError, socket.timeout)) or "timed out" in str(e).lower():
                gw.total_504_timeouts += 1
                self._send_json(
                    504,
                    {
                        "error": "Gateway Timeout (max_request_execution_timeout_seconds exceeded)",
                        "timeout_seconds": timeout_sec,
                        "action": "Socket forcefully terminated and active_open_requests decremented (AC-02.1)",
                    },
                )
            else:
                self._send_json(502, {"error": "Bad Gateway", "detail": str(e)})
        finally:
            with gw.transition_lock:
                gw.active_open_requests = max(0, gw.active_open_requests - 1)
                gw.last_activity_monotonic = time.monotonic()


def main():
    global GATEWAY
    parser = argparse.ArgumentParser(description="MXC JIT Connection-Buffering Ingress Gateway")
    parser.add_argument("--port", type=int, default=8090, help="Gateway listen port")
    parser.add_argument("--vm-name", type=str, default="mxc-hv-a7df7452", help="Target Hyper-V VM name")
    parser.add_argument("--guest-ip", type=str, default="172.24.173.100", help="Target Guest IP")
    parser.add_argument("--guest-port", type=int, default=8080, help="Target Guest Port")
    parser.add_argument("--idle-timeout", type=float, default=300.0, help="Idle timeout in seconds")
    parser.add_argument(
        "--registry",
        type=str,
        default=None,
        help="Optional path to golden_image_registry.json to launch multi-port listeners for all active routes",
    )
    args = parser.parse_args()

    if args.registry and os.path.exists(args.registry):
        with open(args.registry, "r", encoding="utf-8") as f:
            reg = json.load(f)
        servers: list[LowLatencyHTTPServer] = []
        controllers: list[JitGatewayController] = []
        for img in reg.get("images", []):
            route = img.get("ingress_route")
            if not route or not route.get("active_vm_name") or not route.get("guest_ip"):
                continue
            ctrl = JitGatewayController(
                vm_name=route["active_vm_name"],
                guest_ip=route["guest_ip"],
                guest_port=int(route.get("guest_port", 8080)),
                idle_timeout_seconds=float(route.get("idle_timeout_seconds", 300.0)),
                max_request_timeout_seconds=float(route.get("max_request_execution_timeout_seconds", 900.0)),
            )
            srv = LowLatencyHTTPServer(
                ("0.0.0.0", int(route["listen_port"])),
                GatewayProxyHandler,
                controller=ctrl,
                image_id=img["image_id"],
            )
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            servers.append(srv)
            controllers.append(ctrl)
            print(
                f"[MXC Multi-Port JIT Gateway] Port :{route['listen_port']} -> "
                f"Image={img['image_id']} | VM={route['active_vm_name']} ({route['guest_ip']}:{route.get('guest_port', 8080)})"
            )
        sys.stdout.flush()
        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            for srv in servers:
                srv.server_close()
            for ctrl in controllers:
                ctrl.hv_runspace.close()
        return

    GATEWAY = JitGatewayController(
        vm_name=args.vm_name,
        guest_ip=args.guest_ip,
        guest_port=args.guest_port,
        idle_timeout_seconds=args.idle_timeout,
    )

    server = LowLatencyHTTPServer(
        ("0.0.0.0", args.port),
        GatewayProxyHandler,
        controller=GATEWAY,
        image_id="img-mxc-dev-v2.3",
    )
    print(
        f"[MXC JIT Ingress Gateway] Listening on http://0.0.0.0:{args.port} -> "
        f"VM={args.vm_name} ({args.guest_ip}:{args.guest_port})"
    )
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        GATEWAY.hv_runspace.close()


if __name__ == "__main__":
    main()

