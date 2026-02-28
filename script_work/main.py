# main.py

import threading
import time
import sys
import os

# Add tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from tools.app_control import (
    open_app, close_app, search_file,
    get_installed_apps, get_running_apps, is_process_running,
    is_window_open, system_shutdown, system_restart,
    system_sleep, system_hibernate, system_signout, system_lock,
    cancel_shutdown, execute_command_silent, execute_command_visual,
    system_control
)


def print_help():
    """Print help information"""
    help_text = """
╔════════════════════════════════════════════════════════════════════════════╗
║                         Lara AI Assistant v2.0                             ║
╠════════════════════════════════════════════════════════════════════════════╣
║  APPLICATION COMMANDS:                                                     ║
║    open <app>     - Open an application (e.g., open chrome)               ║
║    close <app>    - Close an application (e.g., close notepad)            ║
║    list           - List running applications                             ║
║    apps           - List all installed applications                       ║
║    status <app>   - Check if an application is running                    ║
║                                                                            ║
║  SYSTEM CONTROL COMMANDS:                                                  ║
║    shutdown       - Shutdown computer                                      ║
║    shutdown /f    - Force shutdown (close apps without saving)            ║
║    shutdown /t 60 - Shutdown with 60 second delay                         ║
║    restart        - Restart computer                                       ║
║    restart /t 30  - Restart with 30 second delay                          ║
║    sleep          - Put computer to sleep                                 ║
║    hibernate      - Hibernate computer                                     ║
║    signout        - Sign out current user                                 ║
║    lock           - Lock computer                                          ║
║    cancel         - Cancel scheduled shutdown                             ║
║                                                                            ║
║  FILE & COMMAND COMMANDS:                                                  ║
║    run <command>     - Run terminal command (silent mode)                 ║
║    runv <command>    - Run command in visible window                      ║
║    search <file>     - Search for files                                   ║
║                                                                            ║
║  GENERAL:                                                                  ║
║    help           - Show this help                                         ║
║    clear          - Clear the screen                                      ║
║    exit           - Exit Lara                                              ║
╚════════════════════════════════════════════════════════════════════════════╝
    """
    print(help_text)


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def execute_task(task_type, value, mode='silent', **kwargs):
    """Execute tasks with better error handling"""
    try:
        if task_type == "open":
            result = open_app(value)
            print(f"\n📱 Lara: {result}")

        elif task_type == "close":
            result = close_app(value)
            print(f"\n🔚 Lara: {result}")

        elif task_type == "run":
            print("\n💻 Lara: Executing command...")
            if mode == 'visual':
                result = execute_command_visual(value)
            else:
                result = execute_command_silent(value)
            print(f"\n📟 Lara: {result}")

        elif task_type == "search":
            print("\n🔍 Lara: Searching...")
            result = search_file(value)
            print(f"\n📁 Lara: {result}")
            
        elif task_type == "shutdown":
            print("\n🔌 Lara: Initiating shutdown...")
            result = system_control('shutdown', mode, **kwargs)
            print(f"\n🔌 Lara: {result}")
            
        elif task_type == "restart":
            print("\n🔄 Lara: Initiating restart...")
            result = system_control('restart', mode, **kwargs)
            print(f"\n🔄 Lara: {result}")
            
        elif task_type == "sleep":
            print("\n😴 Lara: Putting system to sleep...")
            result = system_sleep()
            print(f"\n😴 Lara: {result}")
            
        elif task_type == "hibernate":
            print("\n💤 Lara: Hibernating system...")
            result = system_hibernate()
            print(f"\n💤 Lara: {result}")
            
        elif task_type == "signout":
            print("\n👋 Lara: Signing out...")
            result = system_signout(force=kwargs.get('force', False), admin_override=kwargs.get('admin_override', False))
            print(f"\n👋 Lara: {result}")
            
        elif task_type == "lock":
            print("\n🔒 Lara: Locking computer...")
            result = system_lock()
            print(f"\n🔒 Lara: {result}")
            
        elif task_type == "cancel":
            print("\n⏹️  Lara: Cancelling scheduled shutdown...")
            result = cancel_shutdown()
            print(f"\n⏹️  Lara: {result}")
            
    except Exception as e:
        print(f"\n❌ Lara: Error - {str(e)}")


def parse_system_command(command):
    """Parse system command with parameters"""
    parts = command.lower().split()
    cmd = parts[0]
    
    # Default parameters
    params = {
        'delay': 0,
        'force': False
    }
    
    # Parse additional parameters
    i = 1
    while i < len(parts):
        part = parts[i]
        if part in ['/f', '-f', '--force']:
            params['force'] = True
            i += 1
        elif part in ['/t', '-t', '--time']:
            if i + 1 < len(parts):
                try:
                    params['delay'] = int(parts[i + 1])
                    i += 2
                except ValueError:
                    i += 1
            else:
                i += 1
        else:
            i += 1
    
    return cmd, params


def preload_apps():
    """Preload apps in background"""
    print("⏳ Lara: Loading applications in background...")
    start_time = time.time()
    count = len(get_installed_apps(force_refresh=True))
    elapsed = time.time() - start_time
    print(f"✅ Lara: Loaded {count} apps in {elapsed:.1f} seconds")
    print("✨ Lara: Ready! Type 'help' for commands.")


def lara():
    """Main Lara loop with improvements"""
    clear_screen()
    print("╔════════════════════════════════════════════╗")
    print("║        Lara AI Assistant v2.0             ║")
    print("║     Your Personal Windows Assistant       ║")
    print("╚════════════════════════════════════════════╝")
    
    # Pre-load apps in background
    threading.Thread(target=preload_apps, daemon=True).start()
    
    # Give a moment for the welcome message
    time.sleep(0.5)

    while True:
        try:
            command = input("\n🎤 You: ").strip()

            if not command:
                continue

            if command.lower() == "exit":
                print("👋 Lara: Goodbye! Shutting down...")
                break

            elif command.lower() == "clear":
                clear_screen()
                print("╔════════════════════════════════════════════╗")
                print("║        Lara AI Assistant v2.0             ║")
                print("╚════════════════════════════════════════════╝")

            elif command.lower() == "help":
                print_help()

            elif command.lower() == "list":
                running = get_running_apps()
                if running:
                    print(f"\n📋 Lara: Running applications ({len(running)}):")
                    for i, app in enumerate(sorted(running)[:20], 1):
                        print(f"   {i}. {app}")
                    if len(running) > 20:
                        print(f"   ... and {len(running) - 20} more")
                else:
                    print("\n📋 Lara: No applications running.")

            elif command.lower() == "apps":
                print("\n📚 Lara: Loading installed applications...")
                apps = get_installed_apps()
                if apps:
                    print(f"\n📚 Lara: Found {len(apps)} applications (showing first 30):")
                    for i, app in enumerate(sorted(apps, key=lambda x: x['name'])[:30], 1):
                        print(f"   {i}. {app['name']}")
                    if len(apps) > 30:
                        print(f"   ... and {len(apps) - 30} more")
                else:
                    print("\n📚 Lara: No applications found.")

            elif command.lower().startswith("status "):
                app = command[7:].strip()
                if app:
                    is_running = is_process_running(app) or is_window_open(app)
                    if is_running:
                        print(f"\n✅ Lara: '{app}' is running.")
                    else:
                        print(f"\n❌ Lara: '{app}' is not running.")
                else:
                    print("\n⚠️  Lara: Please specify an application to check.")

            elif command.lower().startswith("open "):
                app = command[5:].strip()
                if app:
                    print(f"\n🚀 Lara: Opening '{app}' in background...")
                    threading.Thread(
                        target=execute_task, 
                        args=("open", app), 
                        daemon=True
                    ).start()
                else:
                    print("\n⚠️  Lara: Please specify an application to open.")

            elif command.lower().startswith("close "):
                app = command[6:].strip()
                if app:
                    print(f"\n🔄 Lara: Closing '{app}' in background...")
                    threading.Thread(
                        target=execute_task, 
                        args=("close", app), 
                        daemon=True
                    ).start()
                else:
                    print("\n⚠️  Lara: Please specify an application to close.")

            elif command.lower().startswith("run "):
                cmd = command[4:].strip()
                if cmd:
                    threading.Thread(
                        target=execute_task, 
                        args=("run", cmd, "silent"), 
                        daemon=True
                    ).start()
                else:
                    print("\n⚠️  Lara: Please specify a command to run.")
                    
            elif command.lower().startswith("runv "):
                cmd = command[5:].strip()
                if cmd:
                    threading.Thread(
                        target=execute_task, 
                        args=("run", cmd, "visual"), 
                        daemon=True
                    ).start()
                else:
                    print("\n⚠️  Lara: Please specify a command to run.")

            elif command.lower().startswith("search "):
                filename = command[7:].strip()
                if filename:
                    threading.Thread(
                        target=execute_task, 
                        args=("search", filename), 
                        daemon=True
                    ).start()
                else:
                    print("\n⚠️  Lara: Please specify a filename to search.")

            # System control commands
            elif command.lower() in ["shutdown", "restart", "sleep", "hibernate", "signout", "lock", "cancel"]:
                cmd, params = parse_system_command(command)
                
                # Confirm with user for shutdown/restart
                if cmd in ["shutdown", "restart"]:
                    if params['delay'] > 0:
                        print(f"\n⚠️  Lara: System will {cmd} in {params['delay']} seconds.")
                    else:
                        print(f"\n⚠️  Lara: Are you sure you want to {cmd}?")
                        confirm = input("Type 'yes' to confirm: ").strip().lower()
                        if confirm != 'yes':
                            print("❌ Lara: Operation cancelled.")
                            continue
                
                print(f"\n⚙️  Lara: Executing {cmd} command...")
                if cmd in ["shutdown", "restart", "signout"]:
                    params["admin_override"] = True
                threading.Thread(
                    target=execute_task, 
                    args=(cmd, ""),
                    kwargs=params,
                    daemon=True
                ).start()

            elif command.lower().startswith("shutdown "):
                cmd, params = parse_system_command(command)
                
                if params['delay'] > 0:
                    print(f"\n⚠️  Lara: System will shutdown in {params['delay']} seconds.")
                else:
                    print(f"\n⚠️  Lara: Are you sure you want to shutdown?")
                    confirm = input("Type 'yes' to confirm: ").strip().lower()
                    if confirm != 'yes':
                        print("❌ Lara: Operation cancelled.")
                        continue
                
                print(f"\n⚙️  Lara: Executing shutdown command...")
                params["admin_override"] = True
                threading.Thread(
                    target=execute_task, 
                    args=("shutdown", ""),
                    kwargs=params,
                    daemon=True
                ).start()

            elif command.lower().startswith("restart "):
                cmd, params = parse_system_command(command)
                
                if params['delay'] > 0:
                    print(f"\n⚠️  Lara: System will restart in {params['delay']} seconds.")
                else:
                    print(f"\n⚠️  Lara: Are you sure you want to restart?")
                    confirm = input("Type 'yes' to confirm: ").strip().lower()
                    if confirm != 'yes':
                        print("❌ Lara: Operation cancelled.")
                        continue
                
                print(f"\n⚙️  Lara: Executing restart command...")
                params["admin_override"] = True
                threading.Thread(
                    target=execute_task, 
                    args=("restart", ""),
                    kwargs=params,
                    daemon=True
                ).start()

            else:
                # Try natural language interpretation
                cmd_lower = command.lower()
                
                # Check for system control commands
                if any(word in cmd_lower for word in ["shutdown", "turn off", "power off"]):
                    if "force" in cmd_lower or "forcefully" in cmd_lower:
                        print("\n⚠️  Lara: Force shutdown will close applications without saving!")
                    
                    print(f"\n⚙️  Lara: Executing shutdown command...")
                    threading.Thread(
                        target=execute_task, 
                        args=("shutdown", ""),
                        kwargs={'force': 'force' in cmd_lower},
                        daemon=True
                    ).start()
                    
                elif any(word in cmd_lower for word in ["restart", "reboot"]):
                    print("\n⚠️  Lara: Are you sure you want to restart?")
                    print(f"\n⚙️  Lara: Executing restart command...")
                    threading.Thread(
                        target=execute_task, 
                        args=("restart", ""),
                        daemon=True
                    ).start()
                    
                elif any(word in cmd_lower for word in ["sleep", "suspend"]):
                    print("\n😴 Lara: Putting computer to sleep...")
                    threading.Thread(
                        target=execute_task, 
                        args=("sleep", ""), 
                        daemon=True
                    ).start()
                    
                elif "hibernate" in cmd_lower:
                    print("\n💤 Lara: Hibernating computer...")
                    threading.Thread(
                        target=execute_task, 
                        args=("hibernate", ""), 
                        daemon=True
                    ).start()
                    
                elif any(word in cmd_lower for word in ["sign out", "logout", "log out"]):
                    print("\n👋 Lara: Signing out...")
                    threading.Thread(
                        target=execute_task, 
                        args=("signout", ""), 
                        daemon=True
                    ).start()
                    
                elif "lock" in cmd_lower:
                    print("\n🔒 Lara: Locking computer...")
                    threading.Thread(
                        target=execute_task, 
                        args=("lock", ""), 
                        daemon=True
                    ).start()
                    
                elif "cancel shutdown" in cmd_lower or "abort shutdown" in cmd_lower:
                    print("\n⏹️  Lara: Cancelling shutdown...")
                    threading.Thread(
                        target=execute_task, 
                        args=("cancel", ""), 
                        daemon=True
                    ).start()
                    
                # Check for app commands
                elif any(word in cmd_lower for word in ["open", "launch", "start"]):
                    app = cmd_lower.replace("open", "").replace("launch", "").replace("start", "").strip()
                    if app:
                        print(f"\n🚀 Lara: Opening {app}...")
                        threading.Thread(
                            target=execute_task, 
                            args=("open", app), 
                            daemon=True
                        ).start()
                    else:
                        print("\n❓ Lara: What would you like me to open?")
                    
                elif any(word in cmd_lower for word in ["close", "kill", "stop", "exit"]):
                    app = cmd_lower.replace("close", "").replace("kill", "").replace("stop", "").replace("exit", "").strip()
                    if app:
                        print(f"\n🔄 Lara: Closing {app}...")
                        threading.Thread(
                            target=execute_task, 
                            args=("close", app), 
                            daemon=True
                        ).start()
                    else:
                        print("\n❓ Lara: What would you like me to close?")
                    
                elif "search" in cmd_lower or "find" in cmd_lower:
                    file = cmd_lower.replace("search", "").replace("find", "").strip()
                    if file:
                        print(f"\n🔍 Lara: Searching for {file}...")
                        threading.Thread(
                            target=execute_task, 
                            args=("search", file), 
                            daemon=True
                        ).start()
                    else:
                        print("\n❓ Lara: What would you like me to search for?")
                        
                else:
                    print("\n🤔 Lara: I don't understand. Type 'help' for available commands.")

        except KeyboardInterrupt:
            print("\n\n👋 Lara: Interrupted. Shutting down...")
            break
        except Exception as e:
            print(f"\n❌ Lara: Unexpected error - {str(e)}")
            print("   Please try again or type 'help' for commands.")


if __name__ == "__main__":
    lara()
