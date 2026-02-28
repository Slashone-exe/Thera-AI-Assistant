generate_cad_prototype_tool = {
    "name": "generate_cad_prototype",
    "description": "Generates a 3D wireframe prototype based on a user's description. Use this when the user asks to 'visualize', 'prototype', 'create a wireframe', or 'design' something in 3D.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {
                "type": "STRING",
                "description": "The user's description of the object to prototype."
            }
        },
        "required": ["prompt"]
    }
}




write_file_tool = {
    "name": "write_file",
    "description": "Writes content to a file at the specified path. Overwrites if exists.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {
                "type": "STRING",
                "description": "The path of the file to write to."
            },
            "content": {
                "type": "STRING",
                "description": "The content to write to the file."
            }
        },
        "required": ["path", "content"]
    }
}

read_directory_tool = {
    "name": "read_directory",
    "description": "Lists the contents of a directory.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {
                "type": "STRING",
                "description": "The path of the directory to list."
            }
        },
        "required": ["path"]
    }
}

read_file_tool = {
    "name": "read_file",
    "description": "Reads the content of a file.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {
                "type": "STRING",
                "description": "The path of the file to read."
            }
        },
        "required": ["path"]
    }
}

open_app_tool = {
    "name": "open_app",
    "description": "Open/launch a desktop application by name.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "app_name": {"type": "STRING", "description": "Application name to open."}
        },
        "required": ["app_name"]
    }
}

close_app_tool = {
    "name": "close_app",
    "description": "Close/terminate a running desktop application by name.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "app_name": {"type": "STRING", "description": "Application/process name to close."}
        },
        "required": ["app_name"]
    }
}

run_command_tool = {
    "name": "run_command",
    "description": "Run a terminal command on the local machine.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "command": {"type": "STRING", "description": "Command string to execute."}
        },
        "required": ["command"]
    }
}

search_file_tool = {
    "name": "search_file",
    "description": "Search for files by partial name.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "filename": {"type": "STRING", "description": "File name or partial name to search."},
            "search_path": {"type": "STRING", "description": "Optional root path to search from."}
        },
        "required": ["filename"]
    }
}

get_installed_apps_tool = {
    "name": "get_installed_apps",
    "description": "List installed/start-menu applications.",
    "parameters": {
        "type": "OBJECT",
        "properties": {}
    }
}

get_running_apps_tool = {
    "name": "get_running_apps",
    "description": "List currently running applications/processes.",
    "parameters": {
        "type": "OBJECT",
        "properties": {}
    }
}

check_app_status_tool = {
    "name": "check_app_status",
    "description": "Check whether an application is currently running or has an open window.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "app_name": {"type": "STRING", "description": "Application name to check."}
        },
        "required": ["app_name"]
    }
}

system_shutdown_tool = {
    "name": "system_shutdown",
    "description": "Shut down the computer. Optionally provide delay (seconds) and force mode.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "delay": {"type": "INTEGER", "description": "Optional delay in seconds before shutdown."},
            "force": {"type": "BOOLEAN", "description": "Force close running apps without prompting to save."}
        }
    }
}

tools_list = [{"function_declarations": [
    generate_cad_prototype_tool,
    write_file_tool,
    read_directory_tool,
    read_file_tool,
    open_app_tool,
    close_app_tool,
    run_command_tool,
    search_file_tool,
    get_installed_apps_tool,
    get_running_apps_tool,
    check_app_status_tool,
    system_shutdown_tool
]}]


