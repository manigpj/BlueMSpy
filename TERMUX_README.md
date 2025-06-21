# BlueSpy for Termux

A Bluetooth device scanner and data extractor optimized for Termux environment.

## Features

- 🔍 Scan for nearby Bluetooth devices
- 📱 Auto-connect to nearest device
- 📞 Extract call history
- 👥 Access contacts
- 🎵 Download media files
- 🎤 Record audio
- 🌐 Web interface for easy access

## Installation

1. Open Termux and run:
```bash
pkg update && pkg upgrade
pkg install git
git clone https://github.com/yourusername/BlueSpy.git
cd BlueSpy
chmod +x termux_setup.sh
./termux_setup.sh
```

2. Grant required permissions:
   - Bluetooth
   - Storage
   - Microphone
   - Contacts
   - Call logs

## Usage

1. Start the application:
```bash
./run_termux.sh
```

2. Open your browser and go to:
   - Local: http://localhost:5000
   - Network: http://[your-ip]:5000

3. Using the interface:
   - Click the blue scan button to discover devices
   - Enable "Auto-Connect Nearest" for automatic connection
   - Use the "View Data" button to access device information
   - Start/stop recordings using the recording controls

## Troubleshooting

1. Bluetooth not working:
   ```bash
   pkg install bluetooth pulseaudio
   pulseaudio --start
   pactl load-module module-bluetooth-discover
   ```

2. Permission issues:
   - Go to Termux settings
   - Enable all required permissions
   - Restart Termux

3. Web interface not accessible:
   - Check if port 5000 is available
   - Try using a different port in web_interface_termux.py
   - Make sure no firewall is blocking the connection

## Security Notes

- This tool is for educational purposes only
- Always get permission before scanning devices
- Be aware of local laws regarding Bluetooth scanning
- Keep your Termux installation updated

## Requirements

- Termux (latest version)
- Python 3.x
- Bluetooth adapter
- Required Termux packages:
  - python
  - bluetooth
  - pulseaudio
  - termux-api

## Support

For issues and feature requests, please open an issue on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 