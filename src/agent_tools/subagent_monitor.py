#!/usr/bin/env python3
"""Sub-agent health monitor for OpenClaw

Checks for hung, stalled, or crashed sub-agents.
Usage:
    python3 subagent_monitor.py           # Check all active sub-agents
    python3 subagent_monitor.py --watch   # Watch mode (check every 30s)
    python3 subagent_monitor.py --kill-stuck  # Kill agents stuck >5 min
"""

import subprocess
import json
import sys
import time
from datetime import datetime, timedelta


def get_subagents(active_minutes=60):
    """Get list of isolated (sub-agent) sessions."""
    result = subprocess.run(
        ["openclaw", "sessions", "list", "--kinds", "isolated", "other",
         "--active-minutes", str(active_minutes), "--json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return []
    try:
        data = json.loads(result.stdout)
        return data.get("sessions", [])
    except json.JSONDecodeError:
        # Try parsing line-delimited JSON
        sessions = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    sessions.append(json.loads(line))
                except:
                    pass
        return sessions


def get_session_history(session_key, limit=3):
    """Get last N messages from a session."""
    result = subprocess.run(
        ["openclaw", "sessions", "history", session_key, "--limit", str(limit), "--json"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return data.get("messages", [])
    except:
        return None


def format_timestamp(ts_ms):
    """Convert epoch ms to readable time."""
    dt = datetime.fromtimestamp(ts_ms / 1000)
    return dt.strftime("%H:%M:%S")


def check_health(session):
    """Check health status of a sub-agent session."""
    key = session.get("sessionKey", "unknown")
    kind = session.get("kind", "unknown")
    updated_at = session.get("updatedAt", 0)
    total_tokens = session.get("totalTokens", 0)
    system_sent = session.get("systemSent", False)
    aborted = session.get("abortedLastRun", False)
    display = session.get("displayName", key)

    now = datetime.now().timestamp() * 1000
    idle_ms = now - updated_at
    idle_min = idle_ms / 60000

    issues = []
    status = "healthy"

    if aborted:
        issues.append("last run was aborted/crashed")
        status = "crashed"

    if not system_sent and total_tokens == 0:
        issues.append("never started (no system prompt)")
        status = "stalled"

    if idle_min > 5 and total_tokens > 0:
        issues.append(f"idle {idle_min:.1f} min")
        # Could be done, could be stuck

    if idle_min > 10:
        issues.append(f"very idle ({idle_min:.1f} min)")
        status = "suspect"

    return {
        "key": key,
        "display": display,
        "status": status,
        "idle_min": idle_min,
        "total_tokens": total_tokens,
        "issues": issues,
        "last_update": format_timestamp(updated_at)
    }


def print_report(sessions):
    """Print formatted health report."""
    if not sessions:
        print("✅ No active sub-agents found")
        return

    print(f"\n🤖 Sub-Agent Health Report ({len(sessions)} total)\n")
    print(f"{'Session':<45} {'Status':<10} {'Idle':<8} {'Tokens':<8} Issues")
    print("-" * 90)

    for s in sorted(sessions, key=lambda x: x.get("updatedAt", 0), reverse=True):
        health = check_health(s)
        status_emoji = {
            "healthy": "🟢",
            "crashed": "🔴",
            "stalled": "🟡",
            "suspect": "🟠"
        }.get(health["status"], "⚪")

        short_name = health["display"][:40] + "..." if len(health["display"]) > 40 else health["display"]
        issues_str = ", ".join(health["issues"]) if health["issues"] else "-"

        print(f"{status_emoji} {short_name:<43} {health['status']:<8} "
              f"{health['idle_min']:.1f}m  {health['total_tokens']:<8} {issues_str}")


def watch_mode():
    """Continuous monitoring mode."""
    print("👀 Watching sub-agents (Ctrl+C to exit)...")
    while True:
        subprocess.run(["clear"])
        sessions = get_subagents(active_minutes=120)
        print_report(sessions)
        print(f"\n⏱️  Last check: {datetime.now().strftime('%H:%M:%S')}")
        time.sleep(30)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        watch_mode()
    elif len(sys.argv) > 1 and sys.argv[1] == "--kill-stuck":
        sessions = get_subagents(active_minutes=120)
        stuck = [s for s in sessions if check_health(s)["status"] in ("crashed", "stalled", "suspect")]
        if not stuck:
            print("✅ No stuck sub-agents to kill")
            return
        print(f"🔪 Killing {len(stuck)} stuck sub-agents...")
        for s in stuck:
            key = s.get("sessionKey")
            print(f"  → {key}")
            subprocess.run(["openclaw", "sessions", "cancel", key], capture_output=True)
        print("Done.")
    else:
        sessions = get_subagents(active_minutes=60)
        print_report(sessions)


if __name__ == "__main__":
    main()
