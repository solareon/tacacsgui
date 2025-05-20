import subprocess
import hashlib
import os
import secrets
from config import (
    BASE_DIR, TACPLUS_APP, TACPLUS_CONFIG, TACPLUS_SYSTEMD_SERVICE
)

DEBUG = os.environ.get("TACACSGUI_DEBUG", "0") == "1"

def csrf_token():
	return secrets.token_hex(nbytes=16)

def is_valid_session(session, token):
	if not session.get("scrf_token", None):
		return False
	if session.get("scrf_token", None) != token:
		return False
	return True

def verify_the_configuration(configuration_file):
	if subprocess.call([TACPLUS_APP, "-P", configuration_file]) == 0:
		return True
	return False

def deploy_configuration(configuration_file):
	copy_status = (subprocess.call(["cp", "-v", configuration_file, "/usr/local/etc/tac_plus.cfg"]) == 0)
	restart_status = (subprocess.call(["/etc/init.d/tac_plus", "restart"]) == 0)
	return (copy_status and restart_status)

def update_tac_plus_configuration():
    """
    Updates the tac_plus configuration if there are changes.
    """
    temp_dir = os.path.join(BASE_DIR, 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    config_path = TACPLUS_CONFIG
    temp_config_path = os.path.join(temp_dir, 'tac_plus.cfg')

    # Calculate SHA sums for the deployed and to-be-deployed configuration files
    deployed_sha_sum = hashlib.sha256(open(config_path, 'rb').read()).hexdigest()
    to_be_deployed_sha_sum = hashlib.sha256(open(temp_config_path, 'rb').read()).hexdigest()

    if deployed_sha_sum != to_be_deployed_sha_sum:
        print("Deploying the configuration file...")
        os.replace(temp_config_path, config_path)
        # Restart the tac_plus service
        try:
            result = subprocess.run(["systemctl", "list-units", "--type=service"], capture_output=True, text=True)
            if TACPLUS_SYSTEMD_SERVICE in result.stdout:
                if DEBUG:
                    print(f"Systemd service {TACPLUS_SYSTEMD_SERVICE} found. Restarting...")
                subprocess.run(["systemctl", "restart", TACPLUS_SYSTEMD_SERVICE], check=True)
            else:
                print("Using init.d to manage tac_plus...")
                subprocess.run(["/etc/init.d/tac_plus", "stop"], check=True)
                subprocess.run(["killall", "tac_plus"], check=True)
                subprocess.run(["/etc/init.d/tac_plus", "start"], check=True)
        except Exception as e:
            print(f"Error restarting tac_plus service: {e}")
    else:
        print("Configurations are the same. Skipping...")
