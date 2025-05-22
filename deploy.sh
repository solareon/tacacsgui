#!/bin/bash

# Prompt user for installation directory
read -p "Enter the directory where you want to install TACACSGUI (default: /opt/tacacsgui): " TARGET_DIR
TARGET_DIR=${TARGET_DIR:-/opt/tacacsgui}

# Detect package manager and install Python3
if command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt"
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip
elif command -v yum >/dev/null 2>&1; then
    PKG_MANAGER="yum"
    sudo yum install -y python3 python3-venv python3-pip
elif command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
    sudo pacman -Sy --noconfirm python python-pip python-virtualenv
else
    echo "No supported package manager found (apt, yum, pacman)."
    exit 1
fi

# Load configuration from config.py
if [ -f "../config.py" ]; then
    echo "Loading configuration from config.py"
    while IFS=' = ' read -r key value; do
        if [[ $key =~ ^[A-Z_][A-Z0-9_]*$ ]] && [[ $value =~ ^[\"\'].*[\"\']$ ]]; then
            # Remove quotes from value
            value=${value:1:-1}
        fi
    done < <(grep -E '^[A-Z_][A-Z0-9_]*\s*=\s*["'\''].*["'\'']' ../config.py)
else
    echo "config.py not found. Skipping config import."
fi

# Create a virtual environment in the target directory
echo "Creating virtual environment in $TARGET_DIR"
sudo mkdir -p $TARGET_DIR
sudo python3 -m venv $TARGET_DIR/venv

# Activate the virtual environment and install requirements
source $TARGET_DIR/venv/bin/activate
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt"
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Please ensure it exists in the root directory."
    exit 1
fi

deactivate

# Copy application files to the target directory
sudo rsync -rv ../app ../run.py ../config.py $TARGET_DIR/
sudo chown $TACACSGUI_USER:$TACACSGUI_GROUP -R $TARGET_DIR

# Update systemd service file with correct username and path and enable the service
sudo sed -i "s|^User=.*|User=$TACACSGUI_USER|" ./systemd/tacacsgui.service
sudo sed -i "s|^Group=.*|Group=$TACACSGUI_GROUP|" ./systemd/tacacsgui.service
sudo sed -i "s|^ExecStart=.*|ExecStart=$TARGET_DIR/venv/bin/python3 $TARGET_DIR/run.py|" ./systemd/tacacsgui.service
sudo sed -i "s|^WorkingDirectory=.*|WorkingDirectory=$TARGET_DIR|" ./systemd/tacacsgui.service
sudo sed -i "s|^Environment=.*|Environment=PATH=$TARGET_DIR|" ./systemd/tacacsgui.service

# Copy the systemd service file to the systemd directory
sudo cp ./systemd/tacacsgui.service /etc/systemd/system/tacacsgui.service
# Reload systemd to recognize the new service
sudo systemctl daemon-reload
# Enable and start the service  
sudo systemctl enable --now tacacsgui

echo "Deployment completed successfully."
