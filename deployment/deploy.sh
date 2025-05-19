#!/bin/bash

# Prompt user for installation directory
read -p "Enter the directory where you want to install TACACSGUI (default: /opt/tacacsgui): " TARGET_DIR
TARGET_DIR=${TARGET_DIR:-/opt/tacacsgui}

# Update and install Python3
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip

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
sudo chown www-data:www-data -R $TARGET_DIR

# Move systemd service file and enable the service
sudo rsync -rv ../systemd/tacacsgui.service /etc/systemd/system/
sudo systemctl enable tacacsgui
sudo systemctl start tacacsgui
echo "* * * * *	root	/bin/bash /opt/tacacsgui/synchronizer.sh" >> /etc/crontab
sudo service cron reload

echo "Deployment completed successfully."
