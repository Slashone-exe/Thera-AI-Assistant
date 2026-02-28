import subprocess
from typing import Any

from .cmd_controller import execute_command_silent, execute_command_visual
from .ps_controller import (
    get_installed_apps,
    get_running_apps,
    is_process_running,
    is_window_open,
    open_app,
    close_app,
    search_file,
    system_sleep,
    system_hibernate,
    system_lock,
    cancel_shutdown,
)


def system_shutdown(delay: int = 0, force: bool = False, admin_override: bool = False) -> str:
    if not admin_override:
        return "Blocked: shutdown requires explicit confirmation and admin override."
    cmd = f"shutdown /s /t {max(0, int(delay))}" + (" /f" if force else "")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return f"System will shutdown in {max(0, int(delay))} seconds."
    return f"Shutdown failed: {(result.stderr or result.stdout).strip()}"


def system_restart(delay: int = 0, force: bool = False, admin_override: bool = False) -> str:
    if not admin_override:
        return "Blocked: restart requires explicit confirmation and admin override."
    cmd = f"shutdown /r /t {max(0, int(delay))}" + (" /f" if force else "")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return f"System will restart in {max(0, int(delay))} seconds."
    return f"Restart failed: {(result.stderr or result.stdout).strip()}"


def system_signout(force: bool = False, admin_override: bool = False) -> str:
    if not admin_override:
        return "Blocked: signout requires explicit confirmation and admin override."
    cmd = "shutdown /l /f" if force else "shutdown /l"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        return "Signing out current user."
    return f"Signout failed: {(result.stderr or result.stdout).strip()}"


def system_control(action: str, _mode: str = "silent", **kwargs: Any) -> str:
    delay = kwargs.get("delay", 0)
    force = kwargs.get("force", False)
    admin_override = kwargs.get("admin_override", False)

    action_lower = (action or "").lower().strip()
    if action_lower == "shutdown":
        return system_shutdown(delay=delay, force=force, admin_override=admin_override)
    if action_lower == "restart":
        return system_restart(delay=delay, force=force, admin_override=admin_override)
    if action_lower == "sleep":
        return system_sleep()
    if action_lower == "hibernate":
        return system_hibernate()
    if action_lower == "signout":
        return system_signout(force=force, admin_override=admin_override)
    if action_lower == "lock":
        return system_lock()
    if action_lower == "cancel":
        return cancel_shutdown()
    return f"Unknown system action: {action}"
