#!/bin/bash

# Load configuration path from config.py
TEMP_DIR=$(python3 -c "import os; from config import BASE_DIR; print(os.path.join(BASE_DIR, 'temp'))")
CONFIG_PATH=$(python3 -c "import os; from config import TACPLUS_CONFIG; print(TACPLUS_CONFIG)")
TACPLUS_SVC=$(python3 -c "import os; from config import TACPLUS_SYSTEMD_SERVICE; print(TACPLUS_SYSTEMD_SERVICE)")

# Ensure the temporary directory exists
mkdir -p "$TEMP_DIR"

# Calculate SHA sums for the deployed and to-be-deployed configuration files
deployed_sha_sum=$(shasum -a 256 "$CONFIG_PATH" | awk -F" " '{print $1}')
to_be_deployed_sha_sum=$(shasum -a 256 "$TEMP_DIR/tac_plus.cfg" | awk -F" " '{print $1}')

if [ "$deployed_sha_sum" != "$to_be_deployed_sha_sum" ]
then
    echo "Deploying the configuration file..."
    cp -rv "$TEMP_DIR/tac_plus.cfg" "$CONFIG_PATH"

    if systemctl list-units --type=service | grep -q "$TACPLUS_SVC"; then
		echo "Systemd service $TACPLUS_SVC found. Restarting..."
        echo "Using systemd to manage tac_plus..."
        systemctl restart "$TACPLUS_SVC"
    else
        echo "Using init.d to manage tac_plus..."
        /etc/init.d/tac_plus stop
        killall tac_plus
        /etc/init.d/tac_plus start
    fi
else
    echo "Configurations are the same. Skipping..."
fi
