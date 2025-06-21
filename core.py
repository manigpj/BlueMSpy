#!/usr/bin/env python3

import os
import json
import time
import re
import shlex
from enum import Enum
from datetime import datetime
from system import run_and_check, CommandValidationException

# Detect environment
IS_TERMUX = os.path.exists("/data/data/com.termux")
PREFIX = "/data/data/com.termux/files/usr" if IS_TERMUX else "/usr"

# Set up command paths
BLUETOOTHCTL = os.path.join(PREFIX, "bin/bluetoothctl")
BTMGMT = os.path.join(PREFIX, "bin/btmgmt")
PACTL = os.path.join(PREFIX, "bin/pactl")
PARECORD = os.path.join(PREFIX, "bin/parecord")
PAPLAY = os.path.join(PREFIX, "bin/paplay")

# Directory structure
RECORDINGS_DIR = "recordings"
EXTRACTED_DATA_DIR = "extracted_data"
for directory in [RECORDINGS_DIR, EXTRACTED_DATA_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Add sudo prefix for non-Termux environments
def get_command(cmd):
    if not IS_TERMUX and cmd.startswith(("bluetoothctl", "btmgmt")):
        return ["sudo"] + cmd.split()
    return cmd.split()


class BluezAddressType(Enum):
    BR_EDR = 0
    LE_PUBLIC = 1
    LE_RANDOM = 2

    def __str__(self):
        return self.name


def is_valid_bluezaddress(address: str) -> bool:
    ok = True
    try:
        Address(address)
    except ValueError:
        ok = False
    return ok


class Address:
    regexp = re.compile(r"(?i:^([\da-f]{2}:){5}[\da-f]{2}$)")

    def __init__(self, value: str):
        if self.regexp.match(value) is None:
            raise ValueError(f"{value} is not a valid bluetooth address")
        self._address = value.lower()

    def __str__(self):
        return self._address

    def __eq__(self, other):
        return self._address == str(other).lower()


class BluezTarget:
    regexp = re.compile(r"(?i:^([\da-f]{2}:){5}[\da-f]{2}$)")

    def __init__(
        self, address: str, type: int | BluezAddressType = BluezAddressType.BR_EDR
    ):
        self.address = Address(address)
        if isinstance(type, int):
            type = BluezAddressType(type)
        elif isinstance(type, str):
            type = BluezAddressType(int(type))
        self.type = type
        self.name = None
        self.rssi = None
        self.services = []

    def __eq__(self, other):
        return self.address == other.address and self.type == other.type
    
    def to_dict(self):
        return {
            'address': str(self.address),
            'type': str(self.type),
            'name': self.name,
            'rssi': self.rssi,
            'services': self.services,
            'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


class BluezIoCaps(Enum):
    DisplayOnly = 0
    DisplayYesNo = 1
    KeyboardOnly = 2
    NoInputNoOutput = 3
    KeyboardDisplay = 4


def pair(target: BluezTarget, verbose: bool = False) -> bool:
    # Configure ourselves to be bondable and pairable
    run_and_check(get_command(f"{BTMGMT} bondable true"), verbose=verbose)
    run_and_check(get_command(f"{BTMGMT} pairable true"), verbose=verbose)

    # No need for link security ;)
    run_and_check(get_command(f"{BTMGMT} linksec false"), verbose=verbose)

    # Try to pair to a device with NoInputNoOutput capabilities
    try:
        run_and_check(
            get_command(
                f"{BTMGMT} pair -c {str(BluezIoCaps.NoInputNoOutput.value)} -t {str(target.type.value)} {str(target.address)}"
            ),
            is_valid=lambda out: not ("failed" in out and not "Already Paired" in out),
            verbose=verbose,
        )
        return True
    except CommandValidationException as e:
        if "status 0x05 (Authentication Failed)" in e.output:
            return False
        raise e


def connect(target: BluezTarget, timeout: int = 2, verbose: bool = False):
    # First get device info by scanning
    scan_result = run_and_check(
        get_command(f"{BLUETOOTHCTL} --timeout {str(timeout)} scan on"), verbose=verbose
    )
    
    # Extract device name and RSSI if available
    for line in scan_result.split('\n'):
        if str(target.address) in line:
            if 'Device' in line and 'RSSI' in line:
                parts = line.split()
                target.name = ' '.join(parts[3:-2]) if len(parts) > 4 else None
                target.rssi = parts[-1] if 'RSSI' in line else None
    
    # Connect to the device
    run_and_check(
        get_command(f"{BLUETOOTHCTL} connect {str(target.address)}"),
        is_valid=lambda out: not "Failed to connect" in out,
        verbose=verbose
    )
    
    # Get services
    info_result = run_and_check(
        get_command(f"{BLUETOOTHCTL} info {str(target.address)}"),
        verbose=verbose
    )
    
    # Extract services
    services = []
    for line in info_result.split('\n'):
        if 'UUID' in line:
            uuid = line.split('UUID:')[1].strip()
            service_name = line.split('(')[1].split(')')[0] if '(' in line else "Unknown"
            services.append({'uuid': uuid, 'name': service_name})
    
    target.services = services
    
    # Save device info
    save_device_info(target.to_dict())
    
    return True


def normalize_address(target: BluezTarget) -> str:
    return str(target.address).upper().replace(":", "_")


def to_card_name(target: BluezTarget) -> str:
    return "bluez_card." + normalize_address(target=target)


def to_source_name(target: BluezTarget) -> str:
    return "bluez_input." + normalize_address(target=target) + ".0"


def record(target: BluezTarget, outfile: str, verbose: bool = True):
    source_name = to_source_name(target)
    card_name = to_card_name(target)
    
    # Try to set higher quality profile if available
    run_and_check(
        get_command(f"{PACTL} set-card-profile {card_name} headset-head-unit-msbc"),
        verbose=verbose,
    )
    
    # Generate timestamp for the recording
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if not outfile:
        outfile = f"{normalize_address(target)}_{timestamp}.wav"
    
    # Save recording to recordings directory with device address and timestamp
    recording_path = os.path.join(RECORDINGS_DIR, outfile)
    
    # Create device-specific directory
    device_dir = os.path.join(EXTRACTED_DATA_DIR, str(target.address), 'recordings')
    if not os.path.exists(device_dir):
        os.makedirs(device_dir)
    
    # Create symbolic link or copy to device-specific directory
    device_recording_path = os.path.join(device_dir, os.path.basename(recording_path))
    
    try:
        print(f"Recording from {source_name} to {recording_path}")
        print("Press Ctrl+C to stop recording...")
        run_and_check([PARECORD, "-d", source_name, recording_path], verbose=verbose)
    except KeyboardInterrupt:
        print("Recording stopped by user")
    except Exception as e:
        print(f"Recording error: {str(e)}")
        raise
    
    # Create a link or copy to device-specific directory
    try:
        if os.path.exists(recording_path):
            if IS_TERMUX:
                import shutil
                shutil.copy2(recording_path, device_recording_path)
            else:
                os.symlink(os.path.abspath(recording_path), device_recording_path)
            
            # Update recording metadata
            update_recording_metadata(target, recording_path)
            return recording_path
    except Exception as e:
        print(f"Error saving recording: {str(e)}")
    
    return None


def playback(sink: str, file: str, verbose: bool = True):
    if not os.path.exists(file):
        print(f"File not found: {file}")
        return False
    
    try:
        run_and_check([PAPLAY, "-d", sink, file], verbose=verbose)
        return True
    except Exception as e:
        print(f"Playback error: {str(e)}")
        return False


def save_device_info(device_info):
    devices_file = 'devices.json'
    devices = []
    
    try:
        if os.path.exists(devices_file):
            with open(devices_file, 'r') as f:
                devices = json.load(f)
    except Exception as e:
        print(f"Error reading devices file: {str(e)}")
    
    # Update or add device
    found = False
    for i, d in enumerate(devices):
        if d['address'] == device_info['address']:
            # Update existing device but preserve history
            if 'connection_history' in d and not 'connection_history' in device_info:
                device_info['connection_history'] = d['connection_history']
            devices[i] = device_info
            found = True
            break
    
    if not found:
        # Initialize connection history for new devices
        device_info['connection_history'] = []
        devices.append(device_info)
    
    # Add connection timestamp to history
    if 'connection_history' not in device_info:
        device_info['connection_history'] = []
    
    device_info['connection_history'].append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Keep only last 10 connections
    if len(device_info['connection_history']) > 10:
        device_info['connection_history'] = device_info['connection_history'][-10:]
    
    # Create device directory in extracted data
    device_dir = os.path.join(EXTRACTED_DATA_DIR, device_info['address'])
    if not os.path.exists(device_dir):
        os.makedirs(device_dir)
        os.makedirs(os.path.join(device_dir, 'recordings'))
    
    # Save updated devices list
    try:
        with open(devices_file, 'w') as f:
            json.dump(devices, f, indent=2)
    except Exception as e:
        print(f"Error saving devices file: {str(e)}")


def update_recording_metadata(target, recording_path):
    metadata_file = os.path.join(EXTRACTED_DATA_DIR, str(target.address), 'recordings.json')
    recordings = []
    
    try:
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                recordings = json.load(f)
    except:
        pass
    
    file_stat = os.stat(recording_path)
    
    recording_info = {
        'filename': os.path.basename(recording_path),
        'path': recording_path,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'size_bytes': file_stat.st_size,
        'duration_seconds': estimate_audio_duration(file_stat.st_size)
    }
    
    recordings.append(recording_info)
    
    with open(metadata_file, 'w') as f:
        json.dump(recordings, f, indent=2)


def estimate_audio_duration(size_bytes):
    # Rough estimation based on WAV format (16-bit, 44.1kHz, stereo)
    bytes_per_second = 44100 * 2 * 2  # Sample rate * bytes per sample * channels
    return round(size_bytes / bytes_per_second, 1)


def scan_for_devices(timeout=5, verbose=False):
    """Scan for nearby Bluetooth devices and return them as BluezTargets"""
    scan_result = run_and_check(
        get_command(f"{BLUETOOTHCTL} --timeout {timeout} scan on"), 
        verbose=verbose
    )
    
    devices = []
    current_device = None


