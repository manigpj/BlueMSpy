#!/bin/bash

# Detect if running in Termux
if [ -d "/data/data/com.termux" ]; then
    echo "Detected Termux environment"
    PREFIX="/data/data/com.termux/files/usr"
    PKG_MANAGER="pkg"
    IS_TERMUX=true
else
    echo "Detected regular terminal environment"
    PREFIX="/usr"
    if [ -f "/etc/debian_version" ]; then
        PKG_MANAGER="apt-get"
    elif [ -f "/etc/arch-release" ]; then
        PKG_MANAGER="pacman"
    elif [ -f "/etc/fedora-release" ]; then
        PKG_MANAGER="dnf"
    else
        echo "Unsupported Linux distribution"
        exit 1
    fi
    IS_TERMUX=false
fi

# Function to install packages
install_packages() {
    if [ "$IS_TERMUX" = true ]; then
        pkg update -y
        pkg install -y python bluez pulseaudio termux-api
    else
        if [ "$PKG_MANAGER" = "apt-get" ]; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip bluez pulseaudio
        elif [ "$PKG_MANAGER" = "pacman" ]; then
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm python python-pip bluez pulseaudio
        elif [ "$PKG_MANAGER" = "dnf" ]; then
            sudo dnf update -y
            sudo dnf install -y python3 python3-pip bluez pulseaudio
        fi
    fi
}

# Function to setup PulseAudio
setup_pulseaudio() {
    mkdir -p ~/.config/pulse
    echo "load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1" > ~/.config/pulse/default.pa
    echo "load-module module-zeroconf-publish" >> ~/.config/pulse/default.pa
    
    if [ "$IS_TERMUX" = true ]; then
        pulseaudio --start
    else
        systemctl --user start pulseaudio
    fi
}

# Function to setup Bluetooth
setup_bluetooth() {
    if [ "$IS_TERMUX" = true ]; then
        termux-bluetooth-enable
    else
        sudo systemctl start bluetooth
        sudo systemctl enable bluetooth
    fi
}

# Function to setup web interface
setup_web_interface() {
    # Create necessary directories
    mkdir -p templates
    mkdir -p recordings

    # Install Python web dependencies
    pip3 install flask

    # Create devices.json if it doesn't exist
    if [ ! -f "devices.json" ]; then
        echo "[]" > devices.json
    fi
}

# Main setup process
echo "Starting setup..."

# Install required packages
echo "Installing required packages..."
install_packages

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install argparse flask

# Setup PulseAudio
echo "Setting up PulseAudio..."
setup_pulseaudio

# Setup Bluetooth
echo "Setting up Bluetooth..."
setup_bluetooth

# Setup web interface
echo "Setting up web interface..."
setup_web_interface

echo "Setup complete!"
echo "To run BlueSpy:"
echo "1. Make sure Bluetooth is enabled"
echo "2. Start the web interface: python3 web_interface.py"
echo "3. In another terminal, run: python3 BlueSpy.py -a <bluetooth-address>"
echo "4. Open your browser and go to: http://localhost:5000"
echo ""
echo "To find Bluetooth devices, run:"
if [ "$IS_TERMUX" = true ]; then
    echo "bluetoothctl scan on"
else
    echo "sudo bluetoothctl scan on"
fi 