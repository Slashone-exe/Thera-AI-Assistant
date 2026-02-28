import os
import re
import shlex
import subprocess
import time
from typing import Dict, Optional


BLOCKED_PATTERNS = [
    r"\bformat\b",
    r"\bdel\s+/s\s+/q\b",
    r"\brd\s+/s\b",
    r"\bshutdown\b",
    r"\brestart\b",
    r"\breg\s+delete\b",
    r"\bdiskpart\b",
    r"\bnet\s+user\s+add\b",
    r"\bnet\s+user\b",
]

SYSTEM_PATH_BLOCKLIST = [
    r"c:\windows",
    r"c:\program files",
    r"c:\program files (x86)",
    r"c:\users\default",
]

ALLOWED_PREFIXES = {
    "file": {"dir", "cd", "mkdir", "copy", "move", "type", "get-content", "new-item", "remove-item"},
    "network": {"ipconfig", "ping", "tracert", "netstat", "nslookup", "get-netipaddress", "test-connection"},
    "process": {"tasklist", "taskkill", "get-process", "start-process"},
    "system": {"systeminfo", "hostname", "whoami", "get-computerinfo"},
}
ALL_ALLOWED_PREFIXES = set().union(*ALLOWED_PREFIXES.values())

CRITICAL_PROCESSES = {"svchost", "system", "csrss", "winlogon", "services", "lsass", "smss", "wininit"}


def _first_token(command: str) -> str:
    text = command.strip()
    if not text:
        return ""
    parts = shlex.split(text, posix=False)
    return (parts[0] if parts else "").lower()


def _extract_paths(command: str) -> list[str]:
    # Extract quoted and unquoted Windows style paths.
    quoted = re.findall(r'"([A-Za-z]:\\[^"]+)"', command)
    unquoted = re.findall(r"\b([A-Za-z]:\\[^\s]+)", command)
    return quoted + unquoted


def _is_system_path(path: str) -> bool:
    normalized = os.path.normpath(path).lower()
    return any(normalized.startswith(blocked) for blocked in SYSTEM_PATH_BLOCKLIST)


def _contains_blocked_pattern(command: str) -> Optional[str]:
    lower = command.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, lower):
            return pattern
    return None


def _taskkill_targets_critical(command: str) -> bool:
    lower = command.lower()
    if not lower.startswith("taskkill"):
        return False
    return any(proc in lower for proc in CRITICAL_PROCESSES)


def validate_command(command: str, admin_override: bool = False) -> Dict[str, str]:
    cmd = command.strip()
    if not cmd:
        return {"ok": "false", "reason": "Empty command."}

    blocked = _contains_blocked_pattern(cmd)
    if blocked and not admin_override:
        return {
            "ok": "false",
            "reason": "Restricted action. Explicit confirmation + ADMIN override required.",
        }

    token = _first_token(cmd)
    if token not in ALL_ALLOWED_PREFIXES:
        return {"ok": "false", "reason": f"Command '{token}' is not in the whitelist."}

    if token == "taskkill" and _taskkill_targets_critical(cmd):
        return {"ok": "false", "reason": "Blocking taskkill for critical process target."}

    if token == "remove-item":
        for p in _extract_paths(cmd):
            if _is_system_path(p):
                return {"ok": "false", "reason": f"Blocked system path: {p}"}

    for p in _extract_paths(cmd):
        if _is_system_path(p):
            return {"ok": "false", "reason": f"Blocked system path: {p}"}

    return {"ok": "true", "reason": "validated"}


def _format_agent_response(intent: str, command: str, mode: str, result: str) -> str:
    return (
        f"Intent detected: {intent}\n"
        f"Command generated: {command}\n"
        f"Execution mode: {mode}\n"
        f"Result:\n{result}"
    )


def _run_subprocess(command: str, timeout: int = 30) -> str:
    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
    output = result.stdout if result.stdout else result.stderr
    output = output.strip() if output else "Command executed successfully (no output)."
    if len(output) > 4000:
        output = output[:4000] + "\n... (truncated)"
    return output


def execute_command_silent(command: str, intent: str = "Run terminal command", admin_override: bool = False) -> str:
    print(f"[ACTION LOG] About to run in SILENT mode: {command}")
    validation = validate_command(command, admin_override=admin_override)
    if validation["ok"] != "true":
        return _format_agent_response(intent, command, "SILENT", f"BLOCKED: {validation['reason']}")

    try:
        output = _run_subprocess(command)
        return _format_agent_response(intent, command, "SILENT", output)
    except subprocess.TimeoutExpired:
        return _format_agent_response(intent, command, "SILENT", "Command timed out after 30 seconds.")
    except Exception as exc:
        return _format_agent_response(intent, command, "SILENT", f"Execution error: {exc}")


def execute_command_visual(command: str, intent: str = "Run terminal command", admin_override: bool = False) -> str:
    print(f"[ACTION LOG] About to run in VISUAL mode: {command}")
    validation = validate_command(command, admin_override=admin_override)
    if validation["ok"] != "true":
        return _format_agent_response(intent, command, "VISUAL", f"BLOCKED: {validation['reason']}")

    try:
        subprocess.Popen("start cmd", shell=True)
        time.sleep(2)
        subprocess.Popen(f'start cmd /k "{command}"', shell=True)
        return _format_agent_response(intent, command, "VISUAL", "Visible terminal opened and command executed.")
    except Exception as exc:
        return _format_agent_response(intent, command, "VISUAL", f"Execution error: {exc}")
