#!/bin/bash
# ============================================================
# Raspberry Pi Companion Computer — Setup Script
# Cube Orange + ELRS + Walksnail
# ============================================================
#
# Run: chmod +x setup.sh && sudo ./setup.sh
#

set -e

echo "=== Raspberry Pi Companion Computer Setup ==="
echo ""

# Update system
echo "[1/6] Updating system packages..."
apt-get update -qq

# Install Python and dependencies
echo "[2/6] Installing Python and pip..."
apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
echo "[3/6] Creating Python virtual environment..."
VENV_DIR="/home/pi/companion_venv"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# Install Python packages
echo "[4/6] Installing pymavlink..."
pip install --upgrade pip
pip install -r requirements.txt

# Enable UART on Raspberry Pi
echo "[5/6] Configuring UART..."
if ! grep -q "enable_uart=1" /boot/config.txt 2>/dev/null && \
   ! grep -q "enable_uart=1" /boot/firmware/config.txt 2>/dev/null; then
    CONFIG_FILE="/boot/config.txt"
    [ -f "/boot/firmware/config.txt" ] && CONFIG_FILE="/boot/firmware/config.txt"
    
    echo "" >> "$CONFIG_FILE"
    echo "# Companion Computer UART for MAVLink" >> "$CONFIG_FILE"
    echo "enable_uart=1" >> "$CONFIG_FILE"
    echo "dtoverlay=disable-bt" >> "$CONFIG_FILE"
    
    # Disable serial console to free up UART
    systemctl disable serial-getty@ttyAMA0.service 2>/dev/null || true
    sed -i 's/console=serial0,115200 //g' /boot/cmdline.txt 2>/dev/null || true
    sed -i 's/console=serial0,115200 //g' /boot/firmware/cmdline.txt 2>/dev/null || true
    
    echo "  UART configured. Reboot required!"
    NEEDS_REBOOT=true
fi

# Create log directories
echo "[6/6] Creating directories..."
mkdir -p /var/log/companion
mkdir -p /home/pi/telemetry_logs
chown -R pi:pi /var/log/companion /home/pi/telemetry_logs

# Create systemd service for auto-start
echo "Creating systemd service..."
cat > /etc/systemd/system/companion.service << 'EOF'
[Unit]
Description=Drone Companion Computer
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/companion
ExecStart=/home/pi/companion_venv/bin/python3 main.py --log-only --port /dev/ttyAMA0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "  Service created. Enable with: sudo systemctl enable companion"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Quick start:"
echo "  source $VENV_DIR/bin/activate"
echo "  python3 main.py                    # Dashboard mode"
echo "  python3 main.py --check-params     # Verify parameters"
echo "  python3 main.py --fix-params       # Fix RSSI settings"
echo "  python3 main.py --log-only         # Headless logging"
echo ""
echo "Connection options:"
echo "  --port /dev/ttyAMA0         # GPIO UART (default)"
echo "  --port /dev/ttyUSB0         # USB-to-serial adapter"
echo "  --port udpin:0.0.0.0:14550  # UDP (WiFi telemetry)"
echo "  --port tcp:127.0.0.1:5760   # TCP (SITL simulator)"
echo ""

if [ "${NEEDS_REBOOT:-false}" = "true" ]; then
    echo "*** REBOOT REQUIRED for UART changes! ***"
    echo "Run: sudo reboot"
fi
