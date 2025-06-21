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

# Update package lists
print_color "Updating package lists..." "$YELLOW"
pkg update -y

# Install required packages
print_color "Installing required packages..." "$YELLOW"
pkg install -y python bluez pulseaudio termux-api openssh

# Install Python dependencies
print_color "Installing Python dependencies..." "$YELLOW"
pip install argparse requests pybluez

# Create necessary directories
print_color "Creating necessary directories..." "$BLUE"
mkdir -p ~/.config/pulse
mkdir -p ~/extracted_data/contacts
mkdir -p ~/extracted_data/call_logs
mkdir -p ~/extracted_data/files
mkdir -p ~/extracted_data/media
mkdir -p ~/extracted_data/screenshots

# Configure PulseAudio
print_color "Configuring PulseAudio..." "$YELLOW"
echo "load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1" > ~/.config/pulse/default.pa
echo "load-module module-bluetooth-discover" >> ~/.config/pulse/default.pa
echo "load-module module-zeroconf-publish" >> ~/.config/pulse/default.pa

# Start PulseAudio
print_color "Starting PulseAudio..." "$YELLOW"
pulseaudio --start

# Set up Bluetooth
print_color "Setting up Bluetooth..." "$YELLOW"
termux-bluetooth-enable
sleep 2

# Create data extraction scripts
print_color "Creating data extraction scripts..." "$BLUE"
cat > ~/extract_contacts.sh << 'EOL'
#!/data/data/com.termux/files/usr/bin/bash
termux-contact-list > ~/extracted_data/contacts/contacts_$(date +%Y%m%d_%H%M%S).json
EOL

cat > ~/extract_call_logs.sh << 'EOL'
#!/data/data/com.termux/files/usr/bin/bash
termux-telephony-call-log > ~/extracted_data/call_logs/calls_$(date +%Y%m%d_%H%M%S).json
EOL

cat > ~/capture_screenshot.sh << 'EOL'
#!/data/data/com.termux/files/usr/bin/bash
termux-screen-capture -p ~/extracted_data/screenshots/screen_$(date +%Y%m%d_%H%M%S).png
EOL

chmod +x ~/extract_contacts.sh ~/extract_call_logs.sh ~/capture_screenshot.sh

print_color "Setup complete! You can now connect to Bluetooth devices and extract data" "$GREEN"
print_color "Available commands:" "$BLUE"
print_color "- bluetoothctl scan on                  # Find nearby devices" "$YELLOW"
print_color "- bluetoothctl pair [MAC]               # Pair with device" "$YELLOW"
print_color "- bluetoothctl connect [MAC]            # Connect to device" "$YELLOW"
print_color "- ./extract_contacts.sh                 # Extract contacts" "$YELLOW"
print_color "- ./extract_call_logs.sh                # Extract call logs" "$YELLOW"
print_color "- ./capture_screenshot.sh               # Capture screenshot" "$YELLOW"
print_color "- termux-microphone-record              # Record audio" "$YELLOW"
print_color "- termux-storage-get                    # Browse and extract files" "$YELLOW"
print_color "\nNote: Make sure to grant necessary permissions when prompted" "$RED"