#!/usr/bin/env python3

"""
Logging and text interface related code.
"""


class bcolors:
    HEADER = "\033[34m"
    OK_BLUE = "\033[94m"
    OK_CYAN = "\033[96m"
    OK_GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class loglevel:
    INFO = ("I", bcolors.OK_GREEN)
    WARN = ("!", bcolors.WARNING)
    INPUT = ("?", bcolors.OK_BLUE)
    DEBUG = ("D", bcolors.OK_BLUE)


def color_print(color: bcolors, msg: str):
    """
    Print a string with the selected color.
    """
    print(f"{color}{msg}{bcolors.ENDC}")


def log(level: loglevel, msg: str):
    """
    Print a string with the selected log level.
    """
    print(f"[{level[1]}{level[0]}{bcolors.ENDC}] {msg}")
    # Store data when connecting to Bluetooth devices
    if "Connected to" in msg:
        device_address = msg.split("Connected to ")[-1].strip()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        data_dir = f"extracted_data/{device_address}"
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(f"{data_dir}/calls", exist_ok=True)
        os.makedirs(f"{data_dir}/screenshots", exist_ok=True)
        os.makedirs(f"{data_dir}/files", exist_ok=True)
        with open(f"{data_dir}/connection_log.txt", "a") as f:
            f.write(f"{timestamp}: {msg}\n")


def log_info(msg: str):
    """
    Print an info string.
    """
    log(loglevel.INFO, msg)


def log_warn(msg: str):
    """
    Print a warning string.
    """
    log(loglevel.WARN, msg)


def input_yn(msg: str) -> bool:
    """
    Get a yes/no answer to a prompt.
    """
    log(loglevel.INPUT, msg)
    option = input("[Y/n] ") or "y"
    return option.lower() in ("y", "yes")
