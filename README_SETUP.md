# BlueSpy Project Setup & Usage

## Requirements
- Python 3.8+
- pip
- Bluetooth hardware (and drivers)
- On Linux: bluez, pulseaudio, pactl, parecord, paplay
- On Windows: Bluetooth drivers, PowerShell

## Setup

1. Clone or copy this repository.
2. Install Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. On Linux/Termux, ensure you have bluez, pulseaudio, and related tools installed.
4. On Windows, ensure Bluetooth is enabled and drivers are installed.

## Usage

### Command Line
- Run the main tool:
  ```sh
  python BlueSpy.py --help
  ```
- To record from a device:
  ```sh
  python BlueSpy.py --scan
  # or
  python BlueSpy.py -a XX:XX:XX:XX:XX:XX
  ```

### Web Interface
- Start the web interface:
  ```sh
  python web_interface.py
  ```
- Open your browser at [http://localhost:5000](http://localhost:5000)

### Termux
- Run the setup script:
  ```sh
  bash termux_setup.sh
  ./run_termux.sh
  ```

## Troubleshooting
- Ensure all required system tools are installed (see above).
- If you see missing tool errors, install the required packages for your OS.
- For Bluetooth issues, ensure your device is discoverable and not paired elsewhere.

## Directory Structure
- `recordings/` - Saved audio recordings
- `extracted_data/` - Extracted device data
- `devices.json` - Known devices
- `templates/` - Web UI HTML

## Credits
- Manish Kumar
