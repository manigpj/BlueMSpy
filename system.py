#!/usr/bin/env python3

"""
This module contains functions to interact with system programs.
"""

from typing import Callable, List
import subprocess
from flask_socketio import SocketIO, emit
import os
import shutil
from flask import send_file


class CommandValidationException(Exception):
    def __init__(self, command, output) -> None:
        self.output = output
        super().__init__(f'Error while executing command "{command}"', output)


def run_and_check(
    command: List[str],
    is_valid: Callable[[str], bool] = lambda _: True,
    verbose: bool = False,
) -> None:
    """
    Run a system program and capture the output.
    You may validate that the command has executed correctly with a validation function.
    On exception, the output of the failed command is shown.
    """
    if verbose:
        print("[C] " + " ".join(command))
    output = subprocess.run(command, capture_output=True)
    out = output.stdout.decode("utf-8")
    if verbose:
        print(out)
    if not is_valid(out) or output.stderr != b"":
        cmdline = " ".join(command)
        raise CommandValidationException(cmdline, out)


def check_command_available(command: str) -> bool:
    """
    Check wether a command or tool is available in the system.
    """
    output = subprocess.run(command, capture_output=True)
    return output.returncode == 0


# Flask-SocketIO setup (add to your imports and app init)
socketio = SocketIO(app)

@socketio.on('start_live_audio')
def handle_live_audio(data):
    # Start arecord/parecord and stream chunks to client
    pass

@socketio.on('stop_live_audio')
def handle_stop_audio(data):
    # Stop the recording process
    pass

@app.route('/api/device/<address>/export')
def export_device_data(address):
    device_dir = os.path.join(EXTRACTED_DATA_DIR, address)
    zip_path = f'/tmp/{address}_data.zip'
    shutil.make_archive(zip_path.replace('.zip',''), 'zip', device_dir)
    return send_file(zip_path, as_attachment=True)
