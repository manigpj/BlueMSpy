# BlueSpy - Bluetooth Audio Recording Tool

This tool allows you to record audio from Bluetooth devices. It works on both regular Linux terminals and Termux (Android).

## Prerequisites

### For Regular Linux Terminal:
- Python 3.x
- BlueZ Bluetooth stack
- PulseAudio
- sudo privileges

### For Termux:
- Termux installed from F-Droid (recommended) or Google Play Store
- Required permissions:
  - Bluetooth
  - Storage
  - Microphone

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/BlueSpy.git
cd BlueSpy
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

The script will automatically detect your environment (Termux or regular terminal) and install the necessary dependencies.

## Usage

1. Make sure Bluetooth is enabled on your device

2. Find your target device's MAC address:
```bash
# In regular terminal:
sudo bluetoothctl scan on

# In Termux:
bluetoothctl scan on
```

3. Run BlueSpy with the device's MAC address:
```bash
python3 BlueSpy.py -a <MAC-ADDRESS>
```

Example:
```bash
python3 BlueSpy.py -a 00:11:22:33:44:55
```

## Troubleshooting

### Common Issues:

1. Permission Errors:
   - Regular terminal: Make sure you have sudo privileges
   - Termux: Grant all required permissions in Android settings

2. Bluetooth Issues:
   - Regular terminal: Check if Bluetooth service is running (`sudo systemctl status bluetooth`)
   - Termux: Run `termux-bluetooth-enable`

3. Audio Recording Issues:
   - Make sure PulseAudio is running
   - Check if the target device is properly connected
   - Verify that the device supports audio recording

### Environment-Specific Issues:

#### Regular Terminal:
- If you get "No such file or directory" errors, make sure all required packages are installed
- If Bluetooth commands fail, try running them with sudo manually

#### Termux:
- If Bluetooth doesn't work, try restarting Termux
- If audio recording fails, check if Termux has microphone permission
- Some Android devices might have restrictions on Bluetooth functionality

## Security Note

This tool is for educational purposes only. Only use it on devices you own or have explicit permission to test. Unauthorized use may be illegal.

## References

For more information about Bluetooth security, refer to:
- [BSAM: Bluetooth Security Assessment Methodology](https://www.tarlogic.com/bsam/) 