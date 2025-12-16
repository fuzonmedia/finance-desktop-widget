#!/usr/bin/env bash
set -e

echo "=============================="
echo " Finance Widget Installer"
echo "=============================="

# -------- CONFIG --------
APP_NAME="Finance Widget"
PY_FILE="finance_widget.py"
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/finance-widget.desktop"

# -------- CHECK PY FILE --------
if [ ! -f "$PY_FILE" ]; then
    echo "ERROR: $PY_FILE not found in current directory"
    echo "Run this script from the directory containing $PY_FILE"
    exit 1
fi

APP_PATH="$(cd "$(dirname "$PY_FILE")" && pwd)/$PY_FILE"

echo "Using widget path:"
echo "  $APP_PATH"

# -------- SYSTEM DEPENDENCIES --------
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-pyqt5 \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    libgl1 \
    libglib2.0-0

# -------- PYTHON DEPENDENCIES --------
echo "Installing Python dependencies..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user \
    requests \
    yfinance

# -------- VERIFY PYQT --------
echo "Verifying PyQt5 installation..."
python3 - <<EOF
from PyQt5.QtWidgets import QApplication
print("PyQt5 OK")
EOF

# -------- AUTOSTART --------
echo "Configuring autostart..."
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Exec=python3 $APP_PATH
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$APP_PATH"

echo "Autostart entry created:"
echo "  $AUTOSTART_FILE"

# -------- START IMMEDIATELY --------
echo "Starting Finance Widget now..."

# Run in background, detached from terminal
nohup python3 "$APP_PATH" >/dev/null 2>&1 &

sleep 1

if pgrep -f "$PY_FILE" >/dev/null; then
    echo "Finance Widget started successfully."
else
    echo "WARNING: Widget did not start automatically."
    echo "You can start it manually using:"
    echo "  python3 $APP_PATH"
fi

# -------- DONE --------
echo "=============================="
echo " Installation Complete"
echo "=============================="
echo "• Finance Widget is running now"
echo "• It will start automatically on next login"
echo "• Startup can be disabled from the tray menu"

