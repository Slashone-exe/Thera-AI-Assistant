# ps_controller.py

import subprocess
import psutil
import time
import os
import pygetwindow as gw
import json
import re
from difflib import get_close_matches

# ---------------------------------
# CONFIGURATION
# ---------------------------------

EXCLUDED_KEYWORDS = [
    "uninstall", "documentation", "release", "help", "tutorial", "reset", "website", 
    "update", "manual", "faq", "settings", "configuration", "service", "installer", 
    "install", "notes", "readme", "license", "setup", "config", "debug", "diagnostic", 
    "uninst", "cleanup", "repair", "remove", "delete"
]

SYSTEM_PROCESSES = [
    "svchost", "system", "idle", "dwm", "csrss", "winlogon",
    "services", "lsass", "smss", "wininit", "taskhost", "conhost"
]

APP_EXECUTABLES = {
    "chrome": "chrome.exe", "firefox": "firefox.exe", "edge": "msedge.exe",
    "notepad": "notepad.exe", "calculator": "calculator.exe", "paint": "mspaint.exe",
    "word": "winword.exe", "excel": "excel.exe", "powerpoint": "powerpnt.exe",
    "vs code": "code.exe", "discord": "discord.exe", "spotify": "spotify.exe",
    "vlc": "vlc.exe", "android studio": "studio64.exe", "pycharm": "pycharm64.exe",
    "steam": "steam.exe", "obs studio": "obs64.exe", "winrar": "winrar.exe"
    # (Add other executables here as in your original file)
}

APP_ALIASES = {
    "calculator": "calculator", "calc": "calculator", "notepad": "notepad",
    "editor": "notepad", "paint": "paint", "mspaint": "paint",
    "chrome": "google chrome", "browser": "google chrome",
    "vs code": "visual studio code", "vscode": "visual studio code",
    "cmd": "command prompt", "powershell": "powershell", "explorer": "file explorer"
}

_apps_cache = None
_cache_timestamp = 0
_CACHE_DURATION = 300

# ---------------------------------
# APP & FILE UTILITIES
# ---------------------------------

def clean_app_name(name):
    name = re.sub(r'\{[^}]+\}\\?', '', name)
    name = re.sub(r'\\[^\\]+$', '', name)
    name = re.sub(r'\s*\([^)]*\)', '', name)
    name = re.sub(r'\s+-\s+.*$', '', name)
    name = re.sub(r'\s+\d+(?:\.\d+)?$', '', name)
    name = re.sub(r'[®™©]', '', name)
    return name.strip()

def normalize_app_name(name):
    name_lower = name.lower().strip()
    if name_lower in APP_ALIASES: return APP_ALIASES[name_lower]
    for alias, target in APP_ALIASES.items():
        if alias in name_lower or name_lower in alias: return target
    name = re.sub(r'[^\w\s-]', ' ', name)
    return re.sub(r'\s+', ' ', name).strip()

def is_valid_app(name):
    lower = name.lower()
    if len(lower) < 2: return False
    return not any(word in lower for word in EXCLUDED_KEYWORDS)

def get_installed_apps(force_refresh=False):
    global _apps_cache, _cache_timestamp
    if not force_refresh and _apps_cache and (time.time() - _cache_timestamp) < _CACHE_DURATION:
        return _apps_cache
        
    apps, seen_paths = [], set()
    
    try:
        cmd = 'powershell "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.stdout.strip():
            try:
                apps_json = json.loads(result.stdout)
                if isinstance(apps_json, dict): apps_json = [apps_json]
                for item in apps_json:
                    name, appid = item.get("Name", ""), item.get("AppID", "")
                    if is_valid_app(name) and name.strip():
                        apps.append({'name': name, 'clean_name': clean_app_name(name), 'appid': appid, 'executable': None, 'source': 'startapps'})
            except json.JSONDecodeError: pass
    except Exception as e:
        print(f"Error fetching apps: {e}")
        
    unique_apps = []
    seen_names = set()
    for app in apps:
        key = app['clean_name']
        if key not in seen_names:
            seen_names.add(key)
            unique_apps.append(app)

    _apps_cache = unique_apps
    _cache_timestamp = time.time()
    return unique_apps

def find_app(app_name):
    apps = get_installed_apps()
    if not apps: return None, None, None
    search_lower = normalize_app_name(app_name).lower()
    
    if search_lower in APP_EXECUTABLES:
        exe_name = APP_EXECUTABLES[search_lower]
        for app in apps:
            if app.get('executable') and exe_name.lower() in app['executable'].lower():
                return app['name'], app['appid'], app.get('executable')
                
    for app in apps:
        if search_lower in app['name'].lower() or search_lower in app['clean_name'].lower():
            return app['name'], app['appid'], app.get('executable')
            
    return None, None, None

def is_process_running(process_name):
    search_name = process_name.lower()
    for process in psutil.process_iter(['name', 'exe']):
        try:
            proc_name, proc_exe = process.info['name'] or "", process.info['exe'] or ""
            if search_name in proc_name.lower() or search_name in proc_exe.lower():
                return True
        except: continue
    return False

def get_running_apps():
    running = []
    for process in psutil.process_iter(['name']):
        try:
            name = process.info['name']
            if name and name.lower() not in SYSTEM_PROCESSES and name.lower().endswith('.exe'):
                running.append(name)
        except: continue
    return list(set(running))

def is_window_open(app_name):
    try:
        windows = gw.getAllTitles()
        app_lower = app_name.lower()
        for title in windows:
            if title and app_lower in title.lower(): return True
    except: pass
    return False

def open_app(app_name):
    try:
        name, app_id, executable = find_app(app_name)
        if not name:
            subprocess.Popen(f'start {app_name}', shell=True)
            return f"Attempted to launch {app_name} via start command."
            
        if is_process_running(name) or is_window_open(name):
            return f"{name} already running."
            
        if app_id and ("!" in app_id or "App" in app_id):
            subprocess.Popen(f'explorer shell:appsFolder\\{app_id}')
            return f"{name} launched (UWP)."
            
        subprocess.Popen(f'start {name}', shell=True)
        return f"{name} launched."
    except Exception as e:
        return f"Error opening {app_name}: {str(e)}"

def close_app(process_name):
    search_name = normalize_app_name(process_name)
    closed = False
    for process in psutil.process_iter(['name', 'pid', 'exe']):
        try:
            proc_name = process.info['name'] or ""
            if search_name.lower() in proc_name.lower() and proc_name.lower() not in SYSTEM_PROCESSES:
                process.terminate()
                time.sleep(1)
                if process.is_running(): process.kill()
                closed = True
        except: continue
    
    if not closed:
        try:
            subprocess.run(f'taskkill /f /im "*{search_name}*"', shell=True, capture_output=True)
            closed = True
        except: pass
        
    return f"{process_name} closed successfully." if closed else f"{process_name} not found or could not be closed."

def search_file(filename, search_path=None):
    paths = [search_path] if search_path else [
        os.path.expanduser("~\\Desktop"), os.path.expanduser("~\\Documents"),
        os.path.expanduser("~\\Downloads"), "C:\\"
    ]
    results = []
    for path in paths:
        if not os.path.exists(path): continue
        try:
            cmd = f'powershell "Get-ChildItem -Path \'{path}\' -Recurse -File -Filter \'*{filename}*\' -ErrorAction SilentlyContinue | Select-Object -First 20 FullName | Format-List"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    if ':' in line and 'FullName' in line:
                        file_path = line.split(':', 1)[1].strip()
                        if file_path and os.path.exists(file_path): results.append(file_path)
        except: continue
        
    if results:
        return f"Found {len(results)} files:\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(results[:10]))
    return f"No files found with name '{filename}'."

# ---------------------------------
# SYSTEM CONTROLS
# ---------------------------------

def system_shutdown(delay=0, force=False):
    cmd = f"shutdown /s /t {delay}" + (" /f" if force else "")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return f"System will shutdown in {delay} seconds." if res.returncode == 0 else "Shutdown failed."

def system_restart(delay=0, force=False):
    cmd = f"shutdown /r /t {delay}" + (" /f" if force else "")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return f"System will restart in {delay} seconds." if res.returncode == 0 else "Restart failed."

def system_sleep():
    cmd = "rundll32.exe powrprof.dll,SetSuspendState Sleep"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        return "System is going to sleep."
    return f"Sleep failed: {(res.stderr or res.stdout).strip()}"

def system_hibernate():
    cmd = "shutdown /h"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode == 0:
        return "System is hibernating."
    return f"Hibernate failed: {(res.stderr or res.stdout).strip()}"

def system_signout(force=False):
    cmd = "shutdown /l /f" if force else "shutdown /l"
    subprocess.run(cmd, shell=True)
    return "Signing out current user."

def system_lock():
    subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
    return "Workstation locked."

def cancel_shutdown():
    res = subprocess.run("shutdown /a", shell=True, capture_output=True, text=True)
    return "Scheduled shutdown cancelled." if res.returncode == 0 else "No scheduled shutdown to cancel."
