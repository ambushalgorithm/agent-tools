#!/usr/bin/env python3
"""Sub-agent health monitor for OpenClaw

Checks for hung, stalled, or crashed sub-agents.
Usage:
    python3 subagent_monitor.py              # Check all active sessions
    python3 subagent_monitor.py --subagents-only   # Show only isolated (spawned) agents
    python3 subagent_monitor.py --watch      # Watch mode (check every 30s)
    python3 subagent_monitor.py --details    # Show task prompt and full details
"""

import subprocess
import json
import sys
import time
from datetime import datetime, timedelta


def get_sessions(active_minutes=60, subagents_only=False, channels_only=False):
    """Get list of sessions, optionally filtering for isolated (sub-agent) or channels only."""
    # Build command - CLI accepts multiple --kinds flags or comma-separated
    cmd = ["openclaw", "sessions", "list", "--active-minutes", str(active_minutes), "--json"]
    
    if subagents_only:
        # Try filtering for isolated only - use the kinds filter
        # CLI format: --kinds isolated (may need adjustment based on actual CLI behavior)
        cmd.extend(["--kinds", "isolated"])
    elif channels_only:
        # Filter for group (channel) sessions
        cmd.extend(["--kinds", "group"])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return []
    try:
        data = json.loads(result.stdout)
        sessions = data.get("sessions", [])
        # Post-filter: apply kind filters
        if subagents_only:
            sessions = [s for s in sessions if s.get("kind") == "isolated"]
        elif channels_only:
            sessions = [s for s in sessions if s.get("kind") == "group"]
        return sessions
    except json.JSONDecodeError:
        sessions = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    s = json.loads(line)
                    if subagents_only and s.get("kind") == "isolated":
                        sessions.append(s)
                    elif channels_only and s.get("kind") == "group":
                        sessions.append(s)
                    elif not subagents_only and not channels_only:
                        sessions.append(s)
                except:
                    pass
        return sessions


def get_session_history(session_key, limit=5):
    """Get messages from a session to extract task/prompt."""
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


def extract_task_prompt(messages):
    """Extract the initial task prompt from session history.
    
    For sub-agents spawned via sessions_spawn, the first user message
    is the task instruction. We return a preview of that.
    """
    if not messages:
        return "-"
    
    # Find first user message (skip system prompts)
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                # Handle complex content structure
                text_parts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        text_parts.append(c.get("text", ""))
                content = " ".join(text_parts)
            
            # Truncate and clean up
            preview = content[:80].replace("\n", " ")
            if len(content) > 80:
                preview += "..."
            return preview
    
    return "-"


def extract_model(messages):
    """Extract the model being used from the last assistant message."""
    if not messages:
        return "-"
    
    # Look for the last assistant message with model info
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            model = msg.get("model", "-")
            if model and model != "-":
                # Shorten model name for display
                if "/" in model:
                    model = model.split("/")[-1]
                if len(model) > 20:
                    model = model[:17] + "..."
                return model
    
    return "-"


def format_timestamp(ts_ms):
    """Convert epoch ms to readable time."""
    dt = datetime.fromtimestamp(ts_ms / 1000)
    return dt.strftime("%H:%M:%S")


def format_total_tokens(tokens):
    """Format total tokens for display, handling None."""
    if tokens is None:
        return "-"
    return str(tokens)


def format_duration(minutes):
    """Format duration in a readable way."""
    if minutes < 1:
        return f"{minutes*60:.0f}s"
    elif minutes < 60:
        return f"{minutes:.1f}m"
    else:
        hours = minutes / 60
        return f"{hours:.1f}h"


def check_health(session, stuck_threshold=10):
    """Check health status of a sub-agent session.
    
    Args:
        stuck_threshold: Minutes of idle time before marking as 'suspect'
    """
    key = session.get("key", session.get("sessionKey", "unknown"))
    kind = session.get("kind", "unknown")
    updated_at = session.get("updatedAt", 0)
    total_tokens = session.get("totalTokens")  # Can be None
    system_sent = session.get("systemSent", False)
    aborted = session.get("abortedLastRun", False)
    session_id = session.get("sessionId", "-")[:8]
    model = session.get("model", "-")
    
    # Shorten model name
    if model and model != "-":
        if "/" in model:
            model = model.split("/")[-1]
        if len(model) > 18:
            model = model[:15] + "..."
    
    # Build display name
    display = key
    if "discord:channel:" in key:
        display = key.split("discord:channel:")[-1][:35]
    elif "cron:" in key:
        display = "cron:" + key.split("cron:")[-1][:30]
    elif "main" in key:
        display = "main"
    else:
        display = key[:40]

    now = datetime.now().timestamp() * 1000
    idle_ms = now - updated_at
    idle_min = idle_ms / 60000

    issues = []
    status = "healthy"

    if aborted:
        issues.append("crashed/aborted")
        status = "crashed"

    if not system_sent and (total_tokens is None or total_tokens == 0):
        issues.append("never started (no system)")
        status = "stalled"

    if idle_min > 5 and (total_tokens is not None and total_tokens > 0):
        issues.append(f"idle {format_duration(idle_min)}")

    if idle_min > stuck_threshold:
        issues.append(f"STUCK >{stuck_threshold}min")
        status = "suspect"

    return {
        "key": key,
        "id": session_id,
        "kind": kind,
        "display": display,
        "status": status,
        "idle_min": idle_min,
        "total_tokens": total_tokens,
        "model": model,
        "issues": issues,
        "last_update": format_timestamp(updated_at),
        "system_sent": system_sent
    }


def print_report(sessions, show_details=False, stuck_threshold=10, channels_only=False):
    """Print formatted health report."""
    if not sessions:
        if channels_only:
            kind_filter = "channels"
        elif show_details:
            kind_filter = "sub-agents"
        else:
            kind_filter = "sessions"
        print(f"✅ No active {kind_filter} found")
        return

    if channels_only:
        kind_label = "Channel"
    elif show_details:
        kind_label = "Sub-Agent"
    else:
        kind_label = "Session"
    print(f"\n🤖 {kind_label} Health Report ({len(sessions)} total)\n")
    
    # Base header columns
    base_header = f"{'ID':<10} {'Kind':<6} {'Status':<8} {'Idle':>7} {'Tokens':>8} {'Model':<18}"
    
    if show_details:
        header = base_header + f" {'Task Preview':<42}"
    else:
        header = base_header + f" {'Channel/Key':<28} Issues"
    
    # Calculate max width
    max_width = len(header)
    health_data = []
    
    for s in sorted(sessions, key=lambda x: x.get("updatedAt", 0), reverse=True):
        health = check_health(s, stuck_threshold)
        
        # Get additional details if requested
        task_preview = "-"
        if show_details:
            history = get_session_history(health["key"], limit=3)
            task_preview = extract_task_prompt(history)
            # Update model from history if not in session data
            if health["model"] == "-" and history:
                health["model"] = extract_model(history)
        
        health_data.append((health, task_preview))
        
        # Calculate line length for separator
        if show_details:
            tok_str = format_total_tokens(health['total_tokens'])
            line = (f"🟢 {health['id']:<8} {health['kind']:<6} {health['status']:<8} "
                    f"{format_duration(health['idle_min']):>7} {tok_str:<8} "
                    f"{health['model']:<18} {task_preview:<42}")
        else:
            issues_str = ", ".join(health["issues"]) if health["issues"] else "-"
            short_name = health["display"][:26] + ".." if len(health["display"]) > 28 else health["display"]
            tok_str = format_total_tokens(health['total_tokens'])
            line = (f"🟢 {health['id']:<8} {health['kind']:<6} {health['status']:<8} "
                    f"{format_duration(health['idle_min']):>7} {tok_str:<8} "
                    f"{health['model']:<18} {short_name:<28} {issues_str}")
        max_width = max(max_width, len(line))
    
    print(header)
    print("-" * max_width)

    for health, task_preview in health_data:
        status_emoji = {
            "healthy": "🟢",
            "crashed": "🔴",
            "stalled": "🟡",
            "suspect": "🟠"
        }.get(health["status"], "⚪")

        idle_str = format_duration(health["idle_min"])
        tok_str = format_total_tokens(health["total_tokens"])

        if show_details:
            # Detailed view: Task preview instead of channel key
            line = (f"{status_emoji} {health['id']:<8} "
                    f"{health['kind']:<6} "
                    f"{health['status']:<8} "
                    f"{idle_str:>7} "
                    f"{tok_str:>8} "
                    f"{health['model']:<18} "
                    f"{task_preview:<42}")
        else:
            # Standard view: Channel key + issues
            short_name = health["display"][:26] + ".." if len(health["display"]) > 28 else health["display"]
            issues_str = ", ".join(health["issues"]) if health["issues"] else "-"
            
            line = (f"{status_emoji} {health['id']:<8} "
                    f"{health['kind']:<6} "
                    f"{health['status']:<8} "
                    f"{idle_str:>7} "
                    f"{tok_str:>8} "
                    f"{health['model']:<18} "
                    f"{short_name:<28} "
                    f"{issues_str}")
        print(line)


def watch_mode(subagents_only=False, channels_only=False, show_details=False, stuck_threshold=10):
    """Continuous monitoring mode."""
    if channels_only:
        kind_label = "channels"
    elif subagents_only:
        kind_label = "sub-agents"
    else:
        kind_label = "sessions"
    print(f"👀 Watching {kind_label} (Ctrl+C to exit)...")
    try:
        while True:
            subprocess.run(["clear"])
            sessions = get_sessions(active_minutes=120, subagents_only=subagents_only, channels_only=channels_only)
            print_report(sessions, show_details=show_details, stuck_threshold=stuck_threshold, channels_only=channels_only)
            print(f"\n⏱️  Last check: {datetime.now().strftime('%H:%M:%S')} | Stuck threshold: {stuck_threshold}min")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n👋 Exiting watch mode.")
        sys.exit(0)


def main():
    args = sys.argv[1:]
    
    # Parse flags
    subagents_only = "--subagents-only" in args
    channels_only = "--channels-only" in args
    show_details = "--details" in args
    watch = "--watch" in args
    
    # Stuck threshold config (default 10 min, override with --stuck-threshold N)
    stuck_threshold = 10
    if "--stuck-threshold" in args:
        try:
            idx = args.index("--stuck-threshold")
            stuck_threshold = int(args[idx + 1])
        except (IndexError, ValueError):
            print("Warning: --stuck-threshold requires a number, using default 10min")
    
    if "--help" in args or "-h" in args:
        print(__doc__)
        print("""
Options:
    --subagents-only        Show only isolated (spawned) sub-agents
    --channels-only         Show only Discord channel threads (kind: group)
    --details               Show task prompt preview and model for each agent
    --watch                 Continuous monitoring mode (refreshes every 30s)
    --stuck-threshold N     Set idle minutes before marking as stuck (default: 10)

Examples:
    openclaw-subagent --subagents-only                    # See only spawned agents
    openclaw-subagent --subagents-only --details          # See what each agent is doing
    openclaw-subagent --channels-only                     # See only Discord channels
    openclaw-subagent --watch --stuck-threshold 30        # Alert if idle >30min
""")
        return
    
    if watch:
        watch_mode(subagents_only=subagents_only, channels_only=channels_only, show_details=show_details, stuck_threshold=stuck_threshold)
    else:
        sessions = get_sessions(active_minutes=60, subagents_only=subagents_only, channels_only=channels_only)
        print_report(sessions, show_details=show_details, stuck_threshold=stuck_threshold, channels_only=channels_only)


if __name__ == "__main__":
    main()
