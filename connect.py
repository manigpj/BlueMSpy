#!/usr/bin/env python3

import argparse
import sys
import time
import os
from core import connect, BluezTarget, BluezAddressType
from interface import color_print, bcolors, log_info, log_warn, input_yn

def scan_for_devices(timeout=5, verbose=True):
    """Scan for nearby Bluetooth devices and return a list of addresses"""
    from core import run_and_check, get_command, BLUETOOTHCTL
    import re
    
    if verbose:
        log_info(f"Scanning for devices ({timeout}s)...")
    
    cmd = get_command(f"{BLUETOOTHCTL} --timeout {timeout} scan on")
    output = run_and_check(cmd, verbose=verbose)
    
    # Extract device addresses using regex
    pattern = re.compile(r"(?i:Device\s+([\da-f]{2}:[\da-f]{2}:[\da-f]{2}:[\da-f]{2}:[\da-f]{2}:[\da-f]{2}))")
    matches = pattern.findall(output)
    
    return list(set(matches))  # Remove duplicates

def auto_connect(verbose=True):
    """Automatically scan and connect to the first available device"""
    devices = scan_for_devices(verbose=verbose)
    
    if not devices:
        log_warn("No devices found during scan.")
        return False
    
    for address in devices:
        log_info(f"Attempting to connect to {address}...")
        try:
            connect(BluezTarget(address), verbose=verbose)
            log_info(f"Successfully connected to {address}")
            return True
        except Exception as e:
            log_warn(f"Failed to connect to {address}: {str(e)}")
    
    return False

def main():
    parser = argparse.ArgumentParser(
        prog="Connect",
        description="Connect to Bluetooth devices using system tools",
    )
    parser.add_argument(
        "-a",
        "--target-address",
        help="Target device MAC address",
        dest="address",
    )
    parser.add_argument(
        "-t",
        "--target-address-type",
        help="Target device MAC address type",
        dest="address_type",
        type=lambda t: BluezAddressType[t],
        choices=list(BluezAddressType),
        default=BluezAddressType.BR_EDR,
    )
    parser.add_argument(
        "-s",
        "--scan",
        help="Scan for available devices",
        action="store_true"
    )
    parser.add_argument(
        "-a",
        "--auto",
        help="Automatically connect to first available device",
        action="store_true"
    )
    parser.add_argument(
        "-r",
        "--retry",
        help="Number of connection retries",
        type=int,
        default=3
    )
    args = parser.parse_args()

    if args.scan:
        devices = scan_for_devices()
        if devices:
            color_print("Available devices:", bcolors.OKBLUE)
            for i, addr in enumerate(devices):
                print(f"{i+1}. {addr}")
            
            if input_yn("Would you like to connect to any of these devices?"):
                try:
                    choice = int(input("Enter device number: ")) - 1
                    if 0 <= choice < len(devices):
                        args.address = devices[choice]
                    else:
                        log_warn("Invalid selection.")
                        return
                except ValueError:
                    log_warn("Invalid input.")
                    return
            else:
                return
    
    if args.auto:
        if auto_connect():
            return
        else:
            log_warn("Automatic connection failed.")
            return
    
    if not args.address:
        log_warn("No target address specified. Use -a ADDRESS or --auto for automatic connection.")
        parser.print_help()
        return

    # Attempt connection with retries
    for attempt in range(args.retry):
        try:
            if attempt > 0:
                log_info(f"Retry attempt {attempt+1}/{args.retry}...")
            connect(BluezTarget(args.address, args.address_type), verbose=True)
            log_info(f"Successfully connected to {args.address}")
            break
        except Exception as e:
            log_warn(f"Connection attempt {attempt+1} failed: {str(e)}")
            if attempt < args.retry - 1:
                time.sleep(2)  # Wait before retrying
            else:
                log_warn("All connection attempts failed.")


if __name__ == "__main__":
    main()
