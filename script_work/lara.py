import re
import threading
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))
from tools.app_control import (
    execute_command_visual,
    system_control,
)


def execute_task(task_type: str, value: str = "", **kwargs):
    try:
        if task_type == "run_visual":
            print("\nLara: Executing terminal command in visual mode...")
            print(execute_command_visual(value, intent="User spoken terminal command"))
            return

        if task_type in {"shutdown", "restart", "signout", "sleep", "hibernate", "lock", "cancel"}:
            print(f"\nLara: Executing system action '{task_type}'...")
            result = system_control(task_type, "visual", admin_override=True, **kwargs)
            print(f"Lara: {result}")
            return

        print("Lara: I don't understand that command.")
    except Exception as exc:
        print(f"Lara: Error - {exc}")


def parse_spoken_command(text: str):
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)

    if t in {"cancel", "cancel shutdown", "abort shutdown", "cancle"}:
        return ("cancel", "", {})

    if t in {"lock", "lock pc", "lock computer", "lock system"}:
        return ("lock", "", {})

    if t in {"sleep", "sleep pc", "sleep computer", "suspend"}:
        return ("sleep", "", {})

    if t in {"hibernate", "hibernate pc", "hibernate computer"}:
        return ("hibernate", "", {})

    if t in {"signout", "sign out", "logout", "log out"}:
        return ("signout", "", {})

    if "shutdown" in t:
        if any(x in t for x in {"30", "thirty"}):
            return ("shutdown", "", {"delay": 30})
        return ("shutdown", "", {"delay": 0})

    if any(x in t for x in {"restart", "reboot"}):
        if any(x in t for x in {"30", "thirty"}):
            return ("restart", "", {"delay": 30})
        return ("restart", "", {"delay": 0})

    # Terminal command via speech:
    # "run dir", "execute ipconfig", "command ping google.com"
    for prefix in ("run ", "execute ", "command "):
        if t.startswith(prefix):
            cmd = text[len(prefix):].strip()
            if cmd:
                return ("run_visual", cmd, {})
    return (None, "", {})


def lara():
    print("Lara Voice Command Agent")
    print("Speak/type commands. System actions supported:")
    print("- shutdown now")
    print("- shutdown after 30 sec")
    print("- restart now")
    print("- restart after 30 sec")
    print("- signout, sleep, hibernate, lock, cancel")
    print("- run <terminal command> (always visual)")
    print("- exit")

    while True:
        command = input("\nYou: ").strip()
        if not command:
            continue
        if command.lower() in {"exit", "quit"}:
            print("Lara: Goodbye.")
            break

        task_type, value, kwargs = parse_spoken_command(command)
        if not task_type:
            print("Lara: I don't understand that command.")
            continue

        threading.Thread(
            target=execute_task,
            args=(task_type, value),
            kwargs=kwargs,
            daemon=True,
        ).start()


if __name__ == "__main__":
    lara()
