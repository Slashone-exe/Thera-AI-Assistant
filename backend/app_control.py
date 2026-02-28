import json
import os
import subprocess
import time
from difflib import get_close_matches

import psutil

try:
    import pygetwindow as gw
except Exception:
    gw = None


SYSTEM_PROCESSES = {
    "svchost.exe",
    "system",
    "idle",
    "dwm.exe",
    "csrss.exe",
    "winlogon.exe",
    "services.exe",
    "lsass.exe",
    "smss.exe",
    "wininit.exe",
}


def get_installed_apps(force_refresh=False):
    del force_refresh
    command = (
        'powershell "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json"'
    )
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        if not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        if isinstance(data, dict):
            data = [data]
        apps = []
        for item in data:
            name = (item.get("Name") or "").strip()
            appid = (item.get("AppID") or "").strip()
            if name:
                apps.append({"name": name, "appid": appid})
        return apps
    except Exception:
        return []


def get_running_apps():
    names = set()
    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info.get("name") or "").strip()
            if name and name.lower() not in SYSTEM_PROCESSES:
                names.add(name)
        except Exception:
            continue
    return sorted(names)


def is_process_running(process_name):
    needle = process_name.lower().strip()
    for proc in psutil.process_iter(["name", "exe"]):
        try:
            name = (proc.info.get("name") or "").lower()
            exe = (proc.info.get("exe") or "").lower()
            if needle in name or needle in exe:
                return True
        except Exception:
            continue
    return False


def is_window_open(app_name):
    if gw is None:
        return False
    needle = app_name.lower().strip()
    try:
        for title in gw.getAllTitles():
            if title and needle in title.lower():
                return True
    except Exception:
        return False
    return False


def _find_best_app(app_name):
    apps = get_installed_apps()
    if not apps:
        return None
    needle = app_name.lower().strip()

    for app in apps:
        if needle == app["name"].lower():
            return app
    for app in apps:
        if needle in app["name"].lower():
            return app

    names = [a["name"] for a in apps]
    matches = get_close_matches(app_name, names, n=1, cutoff=0.5)
    if matches:
        for app in apps:
            if app["name"] == matches[0]:
                return app
    return None

def _activate_window_for_app(app_name, retries=8, delay=0.35):
    if gw is None:
        return False

    needle = app_name.lower().strip()
    for _ in range(retries):
        try:
            for title in gw.getAllTitles():
                if title and needle in title.lower():
                    windows = gw.getWindowsWithTitle(title)
                    if windows:
                        win = windows[0]
                        if win.isMinimized:
                            win.restore()
                        win.activate()
                        return True
        except Exception:
            pass
        time.sleep(delay)
    return False


def open_app(app_name):
    app = _find_best_app(app_name)
    if app:
        appid = app.get("appid")
        try:
            if appid:
                subprocess.Popen(f'explorer shell:appsFolder\\{appid}')
                _activate_window_for_app(app["name"])
                return f"{app['name']} launched."
        except Exception:
            pass

    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", f'Start-Process -FilePath "{app_name}"'],
            shell=False,
        )
        _activate_window_for_app(app_name)
        return f"{app_name} launch requested."
    except Exception as e:
        return f"Failed to open {app_name}: {e}"


def close_app(process_name):
    needle = process_name.lower().strip()
    killed = []
    for proc in psutil.process_iter(["name", "exe", "pid"]):
        try:
            name = (proc.info.get("name") or "")
            exe = (proc.info.get("exe") or "")
            if name.lower() in SYSTEM_PROCESSES:
                continue
            if needle in name.lower() or needle in exe.lower():
                proc.terminate()
                killed.append(name or str(proc.info.get("pid")))
        except Exception:
            continue

    if killed:
        return f"Closed: {', '.join(sorted(set(killed)))}"
    return f"No running process matched '{process_name}'."


def search_file(filename, search_path=None):
    base = search_path or os.path.expanduser("~")
    if not os.path.exists(base):
        return f"Search path does not exist: {base}"

    found = []
    needle = filename.lower()
    try:
        for root, _, files in os.walk(base):
            for f in files:
                if needle in f.lower():
                    found.append(os.path.join(root, f))
                    if len(found) >= 20:
                        break
            if len(found) >= 20:
                break
    except Exception as e:
        return f"Search failed: {e}"

    if not found:
        return f"No files found matching '{filename}'."
    return "Found files:\n" + "\n".join(found)


def run_command(command):
    dangerous = ["format", "del /f", "rm -rf", "rd /s", "shutdown", "taskkill"]
    lowered = command.lower()
    if any(x in lowered for x in dangerous):
        return "Command blocked for safety reasons."
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout if result.stdout else result.stderr
        if not output:
            return "Command executed successfully (no output)."
        if len(output) > 1500:
            return output[:1500] + "\n... (output truncated)"
        return output
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Command error: {e}"


def system_shutdown(delay=0, force=False):
    try:
        delay_seconds = max(0, int(delay))
    except Exception:
        delay_seconds = 0

    cmd = f"shutdown /s /t {delay_seconds}" + (" /f" if force else "")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return f"System will shut down in {delay_seconds} seconds."
        error_text = (result.stderr or result.stdout or "Unknown error").strip()
        return f"Shutdown failed: {error_text}"
    except Exception as e:
        return f"Shutdown failed: {e}"
