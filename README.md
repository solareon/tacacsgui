Configure your TACACS+ instance with GUI. 

#Simple #TACACSGUI

## Migration from MySQL to SQLite

To migrate your data from MySQL to SQLite, follow these steps:

1. Ensure you have Python installed on your system.
2. Navigate to the project directory where the `migrate_mysql_to_sqlite.py` script is located.
3. Run the script using the following command:

   ```bash
   python migrate_mysql_to_sqlite.py
   ```

4. Enter your MySQL credentials and database name when prompted.
5. The script will transfer the data to the SQLite database file `tacacsgui.db`.

6. Verify the migration by checking the SQLite database.

## Installation Guide

To install and deploy the TACACSGUI application, follow these steps:

1. Ensure you have Python3 installed on your system.
2. Clone the repository to your local machine.
3. Navigate to the root directory of the repository.
4. Create a `requirements.txt` file in the root directory with the necessary Python dependencies.
5. Run the deployment script:

   ```bash
   bash deploy.sh
   ```

6. The script will:
   - Install Python3 and required packages.
   - Create a virtual environment in `/opt/tacacsgui`.
   - Install dependencies from `requirements.txt`.
   - Deploy the application files.
   - Set up and start the systemd service for TACACSGUI.

7. Verify the deployment by checking the service status:

   ```bash
   sudo systemctl status tacacsgui
   ```
