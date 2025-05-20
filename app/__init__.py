# Import flask and template operators
from flask import Flask, render_template, redirect, url_for

# System libraries
import os
import re
import secrets
from datetime import datetime
from app.utils.tacacs.utils import encrypt_password
from app.utils.render import render_configuration

# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from config import TACPLUS_APP, TACPLUS_CONFIG, TACPLUS_SYSTEMD_SERVICE

# make sure the tmp directory exists
if not os.path.exists(os.path.join(os.path.curdir, 'tmp')):
    os.makedirs(os.path.join(os.path.curdir, 'tmp'))

# Define the WSGI application object
app = Flask(__name__, static_folder = 'templates/static')

# Configurations
app.config.from_object('config')

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)

# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
	return render_template('404.html'), 404

@app.route("/")
def index():
	return redirect(url_for("auth.signin"))

# Import a module / component using its blueprint handler variable
from app.auth.controllers import mod_auth
from app.tacacs.controllers import mod_tac_plus
from app.statistics.controllers import mod_tac_plus_statistiscs

# Register blueprint(s)
app.register_blueprint(mod_auth)
app.register_blueprint(mod_tac_plus)
app.register_blueprint(mod_tac_plus_statistiscs)

# Create all tables if they do not exist
with app.app_context():
    db.create_all()

# Database models
from app.tacacs.models import System
from app.tacacs.models import Configuration
from app.tacacs.models import ConfigurationGroups
from app.tacacs.models import ConfigurationUsers
from app.tacacs.models import Group
from app.tacacs.models import GroupCommands
from app.tacacs.models import TacacsUserGroups
from app.tacacs.models import Command
from app.tacacs.models import TacacsUser
from app.tacacs.models import UserACL
from app.tacacs.models import GroupACL

# Utils
from app.utils.tacacs.utils import encrypt_password
from app.utils.tacacs.utils import verify_the_configuration
import hashlib

# Add watchdog imports for file watching
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import logging
logging.getLogger("watchdog").setLevel(logging.WARNING)

def file_hash(filepath):
    """Return SHA256 hash of the file, or None if file doesn't exist."""
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        return None

# File watcher for external config changes
class ConfigFileChangeHandler(FileSystemEventHandler):
    def __init__(self, config_path):
        super().__init__()
        self.config_path = os.path.abspath(config_path)

    def on_modified(self, event):
        if os.path.abspath(event.src_path) == self.config_path:
            auto_deploy()

    def on_created(self, event):
        if os.path.abspath(event.src_path) == self.config_path:
            auto_deploy()

def start_config_file_watcher():
    config_path = TACPLUS_CONFIG
    event_handler = ConfigFileChangeHandler(config_path)
    observer = Observer()
    # Only watch the config file, not the whole directory
    observer.schedule(event_handler, os.path.dirname(os.path.abspath(config_path)), recursive=False)
    observer_thread = threading.Thread(target=observer.start, daemon=True)
    observer_thread.start()

# Start the file watcher on app startup
start_config_file_watcher()

def auto_deploy():
    with app.app_context():
        first_configuration_id = None
        configuration_id = None
        configurations = Configuration.query.all()
        config_changed = False
        for configuration in configurations:
            if not first_configuration_id:
                first_configuration_id = configuration.id
            if configuration.deployed:
                configuration_id = configuration.id
                config_changed = True
            configuration.deployed = False
            db.session.commit()
        if not configuration_id:
            configuration_id = first_configuration_id
        if not config_changed:
            # No configuration marked as deployed, skip
            return
        system = System.query.first()
        if not system:
            print("Exiting no system configuration found...")
            return
        configuration = None
        try:
            configuration = Configuration.query.filter_by(id = configuration_id).one()
            configuration.deployed = True
            db.session.commit()
        except Exception as e:
            return
        configuration_groups = ConfigurationGroups.query.filter_by(configuration_id = configuration_id).all()
        groups = []
        for configuration_group in configuration_groups:
            group = {
                "group": configuration_group.group,
                "commands": [],
                "acls": []
            }
            commands = GroupCommands.query.filter_by(group_id = configuration_group.group.id).all()
            for command in commands:
                group["commands"].append(command.command)
            acls = GroupACL.query.filter_by(group_id = configuration_group.group.id).all()
            for acl in acls:
                group["acls"].append(acl)
            groups.append(group)

        configuration_users = ConfigurationUsers.query.filter_by(configuration_id = configuration_id).all()
        users = []
        for configuration_user in configuration_users:
            user = {
                "user": configuration_user.user,
                "groups": [],
                "acls": []
            }
            user_groups = TacacsUserGroups.query.filter_by(user_id = configuration_user.user.id)
            for user_group in user_groups:
                user["groups"].append(user_group.group)
            acls = UserACL.query.filter_by(user_id = configuration_user.user.id).all()
            for acl in acls:
                user["acls"].append(acl)
            users.append(user)

        rendered_config = render_configuration(system, groups, users)
        rendered_hash = hashlib.sha256(rendered_config.encode("utf-8")).hexdigest()
        current_hash = file_hash(TACPLUS_CONFIG)
        if rendered_hash == current_hash:
            # No change in configuration file content, skip deployment
            return

        temporary_configuration_file = os.path.join(os.path.curdir, 'tmp', secrets.token_hex(nbytes=16) + '.cfg')
        with open(temporary_configuration_file, "w") as fd:
            fd.write(rendered_config)
        if not verify_the_configuration(temporary_configuration_file):
            return
        os.rename(temporary_configuration_file, TACPLUS_CONFIG)
