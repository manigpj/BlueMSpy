# Running BlueSpy on Termux

This guide will help you set up and run BlueSpy on Termux.

## Prerequisites

1. Install Termux from F-Droid (recommended) or Google Play Store
2. Make sure you have granted Termux the following permissions:
   - Bluetooth
   - Storage
   - Microphone

## Installation

1. Open Termux and run the setup script:
```bash
curl -O https://raw.githubusercontent.com/yourusername/BlueSpy/main/setup_termux.sh
chmod +x setup_termux.sh
./setup_termux.sh
```

2. Grant necessary permissions when prompted

## Usage

1. Start PulseAudio (if not already running):
```bash
pulseaudio --start
```

2. Enable Bluetooth:
```bash
termux-bluetooth-enable
```

3. Run BlueSpy:
```bash
python BlueSpy.py -a <bluetooth-address>
```

## Troubleshooting

1. If you get permission errors:
   - Make sure you've granted all necessary permissions to Termux
   - Try running `termux-setup-storage` to ensure storage permissions are set correctly

2. If Bluetooth doesn't work:
   - Make sure Bluetooth is enabled on your device
   - Try running `termux-bluetooth-enable` again
   - Check if your device supports the required Bluetooth profiles

3. If audio recording doesn't work:
   - Make sure PulseAudio is running (`pulseaudio --start`)
   - Check if the target device is properly connected
   - Verify that the device supports audio recording

## Notes

- The script has been modified to work with Termux's specific paths and permissions
- Some features might be limited due to Android's security restrictions
- Make sure to use the device responsibly and only on devices you own or have permission to test 