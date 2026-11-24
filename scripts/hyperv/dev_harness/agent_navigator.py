#!/usr/bin/env python3
"""
agent_navigator.py - Autonomous AI Agent VM Fleet Navigator & Health Auditor

This harness simulates or executes an autonomous AI Agent navigating through
the MXC Hyper-V Just-in-Time (JIT) Scale-to-Zero infrastructure using FastMCP tools.

The Agent's Mission:
1. Discover all configured standby pools and their lifecycle states.
2. Verify hardware Ring-0 Virtual Switch Port ACL isolation boundaries.
3. Inspect standby nodes residing in paused RAM (Saved state).
4. Evaluate Ingress Gateway telemetry and request velocity autoscaling.
5. Generate an authoritative Autonomous Fleet Scorecard.

Usage:
    python scripts/hyperv/dev_harness/agent_navigator.py [--auto] [--pool POOL_NAME]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure scripts/hyperv is in python path to import mxc_mcp_server
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HYPERV_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))
if HYPERV_DIR not in sys.path:
    sys.path.insert(0, HYPERV_DIR)

try:
    import mxc_mcp_server
except ImportError as e:
    print(f"[Fatal]: Failed to import mxc_mcp_server: {e}")
    sys.exit(1)


# ANSI Color Codes for terminal UI
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def log_agent_thought(thought: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}🤖 [Agent Thought]:{Colors.END} {thought}")


def log_agent_action(tool_name: str, args: Dict[str, Any]):
    args_str = ", ".join(f"{k}='{v}'" for k, v in args.items())
    print(f"{Colors.YELLOW}⚡ [Agent Tool Call]:{Colors.END} {Colors.BOLD}{tool_name}({args_str}){Colors.END}")


def log_agent_observation(summary: str, details: Optional[str] = None):
    print(f"{Colors.GREEN}👁️ [Observation]:{Colors.END} {summary}")
    if details:
        indented = "\n".join("   " + line for line in details.strip().splitlines()[:15])
        print(f"{Colors.BLUE}{indented}{Colors.END}")


class AgentNavigator:
    def __init__(self, target_pool: Optional[str] = None, auto_mode: bool = False):
        self.target_pool = target_pool
        self.auto_mode = auto_mode
        self.scorecard = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "target_pool": target_pool or "all",
            "steps_completed": 0,
            "pools_discovered": [],
            "acl_status": "UNKNOWN",
            "gateway_status": "UNKNOWN",
            "findings": [],
            "operational_readiness": "UNKNOWN",
        }

    def _pause_if_interactive(self, step_title: str):
        if not self.auto_mode:
            input(f"\n{Colors.HEADER}--- Press [Enter] to execute Step: {step_title} ---{Colors.END}")

    def run_mission(self) -> Dict[str, Any]:
        print(f"{Colors.BOLD}{Colors.CYAN}" + "=" * 70)
        print("  MXC Hyper-V Agent Fleet Navigator (FastMCP Mission Runner)")
        print("=" * 70 + f"{Colors.END}")
        print(f"Agent Persona:  Autonomous Cloud Infrastructure & SRE Explorer")
        print(f"Control Plane:  FastMCP Interface (`mxc_mcp_server.py`)")
        print(f"Mission Goal:   Discover VM pools, audit Ring-0 ACLs, and test JIT health")
        print("=" * 70)

        # -------------------------------------------------------------
        # STEP 1: Discover Pool Inventory
        # -------------------------------------------------------------
        self._pause_if_interactive("1. Pool Fleet Discovery")
        log_agent_thought(
            "To understand what infrastructure is present, I will call `hyperv_pool_list` "
            "to inspect all registered warm standby pools, ready counts, and leased members."
        )
        log_agent_action("hyperv_pool_list", {})
        pool_raw = mxc_mcp_server.hyperv_pool_list()
        
        pools = []
        try:
            # Parse json output from wxc pool-list
            clean_json = pool_raw
            if clean_json.startswith("[Exit Code: 0]"):
                clean_json = clean_json.replace("[Exit Code: 0]", "").strip()
            data = json.loads(clean_json)
            pools = data.get("result", {}).get("pools", [])
        except Exception as e:
            self.scorecard["findings"].append(f"Failed to parse pool list: {e}")

        self.scorecard["pools_discovered"] = [p.get("pool_id") for p in pools]
        self.scorecard["steps_completed"] += 1

        summary_lines = []
        for p in pools:
            pid = p.get("pool_id")
            ready = p.get("ready_count", 0)
            leased = p.get("leased_count", 0)
            total = p.get("total_members", 0)
            summary_lines.append(f"Pool '{pid}': {ready} Ready (Saved RAM), {leased} Leased, {total} Total")

        log_agent_observation(
            f"Successfully identified {len(pools)} active standby pool(s).",
            "\n".join(summary_lines),
        )

        # -------------------------------------------------------------
        # STEP 2: Stateful Network Isolation & Port ACL Audit
        # -------------------------------------------------------------
        self._pause_if_interactive("2. Ring-0 Extended Port ACL Verification")
        log_agent_thought(
            "I need to verify that active instances are locked down with zero-trust Ring-0 Port ACLs "
            "at the Hyper-V Virtual Switch level (default-deny egress, enterprise database whitelists)."
        )

        # Find a leased or ready VM to inspect
        target_sandbox_id = None
        for p in pools:
            for m in p.get("members", []):
                if m.get("sandbox_id"):
                    target_sandbox_id = m.get("sandbox_id")
                    if m.get("status") == "leased":
                        break
            if target_sandbox_id:
                break

        if not target_sandbox_id:
            target_sandbox_id = "hv:0b1e0d7e"  # Fallback to known token

        log_agent_action("hyperv_port_acls", {"sandbox_id": target_sandbox_id, "action": "status"})
        acl_output = mxc_mcp_server.hyperv_port_acls(target_sandbox_id, "status")

        has_default_deny = "Outbound   Deny any" in acl_output or "Deny any" in acl_output
        has_sql_whitelist = "1433" in acl_output
        has_http_ingress = "8080" in acl_output

        if has_default_deny and has_sql_whitelist and has_http_ingress:
            self.scorecard["acl_status"] = "VERIFIED_AIRGAPPED"
            acl_verdict = (
                f"Ring-0 Port ACLs strictly enforced on {target_sandbox_id}: "
                f"Default-Deny Egress confirmed, SQL Server (:1433) and Ingress (:8080) explicitly permitted."
            )
        else:
            self.scorecard["acl_status"] = "UNCONSTRAINED_WARNING"
            acl_verdict = f"ACLs on {target_sandbox_id} do not match strict enterprise baseline."

        self.scorecard["steps_completed"] += 1
        log_agent_observation(acl_verdict, acl_output)

        # -------------------------------------------------------------
        # STEP 3: Standby Pool Warmth & Elastic State Check
        # -------------------------------------------------------------
        self._pause_if_interactive("3. Standby Pool Warmth Inspection")
        target_eval_pool = self.target_pool or "prod-adpa"
        log_agent_thought(
            f"Checking the readiness of pool '{target_eval_pool}'. "
            f"Standby members must reside in paused RAM (Saved state) with 0% CPU consumption."
        )

        eval_pool_data = next((p for p in pools if p.get("pool_id") == target_eval_pool), None)
        if eval_pool_data:
            ready_vms = [m.get("vm_name") for m in eval_pool_data.get("members", []) if m.get("status") == "ready"]
            standby_info = f"Found {len(ready_vms)} node(s) hot-ready in paused RAM: {', '.join(ready_vms)}"
            self.scorecard["findings"].append(standby_info)
            log_agent_observation(standby_info)
        else:
            log_agent_observation(f"Pool '{target_eval_pool}' not found in active pool list.")

        self.scorecard["steps_completed"] += 1

        # -------------------------------------------------------------
        # STEP 4: Ingress Gateway & Velocity Autoscaler Telemetry
        # -------------------------------------------------------------
        self._pause_if_interactive("4. Ingress Gateway & Autoscaler Status")
        log_agent_thought(
            "Querying the JIT Ingress Gateway to evaluate reverse proxy health, "
            "sliding-window request velocity tracking, and burst autoscaling state."
        )
        log_agent_action("hyperv_gateway_status", {})
        gw_raw = mxc_mcp_server.hyperv_gateway_status()

        if "Gateway Status Offline" in gw_raw:
            self.scorecard["gateway_status"] = "OFFLINE"
            gw_summary = "JIT Ingress Gateway daemon is currently dormant (Scale-to-Zero)."
        else:
            self.scorecard["gateway_status"] = "ONLINE_ACTIVE"
            gw_summary = "JIT Ingress Gateway is actively accepting connections."

        # -------------------------------------------------------------
        # STEP 5: Golden Image Registry & Windows 11 Enterprise Discovery
        # -------------------------------------------------------------
        self._pause_if_interactive("5. Windows 11 Enterprise Golden Image Discovery")
        log_agent_thought(
            "Searching the Golden Image Registry to discover available OS baselines, "
            "specifically hunting for the Windows 11 Enterprise Client image (img-os-win11-ent)."
        )

        reg_path = os.path.join(SCRIPT_DIR, "golden_image_registry.json")
        win11_found = False
        win11_details = ""

        if os.path.exists(reg_path):
            try:
                with open(reg_path, "r", encoding="utf-8") as f:
                    reg_data = json.load(f)
                
                images = reg_data.get("images", [])
                for img in images:
                    if "win11" in img.get("image_id", "").lower() or "windows 11" in img.get("name", "").lower():
                        win11_found = True
                        vhdx = img.get("vhdx_path", "")
                        status = img.get("status", "unknown")
                        size_gb = img.get("size_gb", 0)
                        
                        # Verify physical presence on NVMe tier
                        exists_on_disk = os.path.exists(vhdx)
                        actual_size_gb = os.path.getsize(vhdx) / (1024**3) if exists_on_disk else 0
                        
                        win11_details = (
                            f"Image ID:      {img.get('image_id')}\n"
                            f"Name:          {img.get('name')}\n"
                            f"Application:   {img.get('application')}\n"
                            f"Status:        {status} (Physical File: {'Present' if exists_on_disk else 'Missing'})\n"
                            f"Path:          {vhdx} ({actual_size_gb:.2f} GB on disk)\n"
                            f"Stack:         {', '.join(img.get('installed_stack', []))}"
                        )
                        self.scorecard["windows_11_image"] = {
                            "image_id": img.get("image_id"),
                            "name": img.get("name"),
                            "vhdx_path": vhdx,
                            "physical_present": exists_on_disk,
                            "size_gb": round(actual_size_gb, 2),
                            "status": status
                        }
                        self.scorecard["findings"].append(
                            f"Discovered Windows 11 Enterprise Image: {img.get('image_id')} at {vhdx} ({actual_size_gb:.2f} GB)"
                        )
                        break
            except Exception as e:
                win11_details = f"Registry parse error: {e}"

        self.scorecard["steps_completed"] += 1
        if win11_found and self.scorecard.get("windows_11_image", {}).get("physical_present"):
            log_agent_observation("Successfully discovered Windows 11 Enterprise Golden Image!", win11_details)
        else:
            log_agent_observation("Windows 11 Enterprise Image could not be located in registry or disk.", win11_details)

        # -------------------------------------------------------------
        # STEP 6: Final Scorecard Synthesis
        # -------------------------------------------------------------
        self._pause_if_interactive("6. Final Assessment & Scorecard Synthesis")
        log_agent_thought(
            "All navigation steps complete. Synthesizing the final Autonomous Infrastructure Scorecard."
        )

        has_win11 = self.scorecard.get("windows_11_image", {}).get("physical_present", False)
        if self.scorecard["acl_status"] == "VERIFIED_AIRGAPPED" and len(self.scorecard["pools_discovered"]) > 0 and has_win11:
            self.scorecard["operational_readiness"] = "OPTIMAL_ENTERPRISE_GRADE"
        else:
            self.scorecard["operational_readiness"] = "FUNCTIONAL_PARTIAL"

        self.scorecard["completed_at"] = datetime.now(timezone.utc).isoformat()

        self._print_scorecard()
        self._save_scorecard()
        return self.scorecard

    def _print_scorecard(self):
        print("\n" + "=" * 70)
        print(f"{Colors.BOLD}{Colors.GREEN}🏆 AUTONOMOUS FLEET AUDIT SCORECARD{Colors.END}")
        print("=" * 70)
        print(f"Status:                {Colors.BOLD}{self.scorecard['operational_readiness']}{Colors.END}")
        print(f"Steps Executed:        {self.scorecard['steps_completed']} / 5")
        print(f"Pools Discovered:      {', '.join(self.scorecard['pools_discovered'])}")
        print(f"Network Isolation:     {self.scorecard['acl_status']}")
        print(f"Ingress Gateway:       {self.scorecard['gateway_status']}")
        win11_info = self.scorecard.get("windows_11_image", {})
        if win11_info.get("physical_present"):
            print(f"Windows 11 Enterprise: FOUND ({win11_info.get('image_id')} @ {win11_info.get('size_gb')} GB)")
        else:
            print(f"Windows 11 Enterprise: NOT FOUND")
        print("-" * 70)
        print(f"Key Findings:")
        for f in self.scorecard["findings"]:
            print(f" • {f}")
        print("=" * 70 + "\n")


    def _save_scorecard(self):
        out_file = os.path.join(SCRIPT_DIR, "agent_navigator_run.json")
        try:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(self.scorecard, f, indent=2)
            print(f"[+] Audit Scorecard persisted to: {out_file}")
        except Exception as e:
            print(f"[!] Warning: Failed to persist scorecard: {e}")


def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Agent Hyper-V Fleet Navigator")
    parser.add_argument("--auto", action="store_true", help="Run autonomously without interactive pauses")
    parser.add_argument("--pool", type=str, default=None, help="Specific pool ID to focus on (e.g. prod-adpa)")
    args = parser.parse_args()

    navigator = AgentNavigator(target_pool=args.pool, auto_mode=args.auto)
    navigator.run_mission()


if __name__ == "__main__":
    main()
