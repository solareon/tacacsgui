from flask import Blueprint, request, render_template, \
                  session, redirect, url_for, jsonify
from app import db

# System libraries
import os
import re
import secrets
from datetime import datetime
import ipaddress

# Database models
from app.tacacs.models import System
from app.tacacs.models import Configuration
from app.tacacs.models import ConfigurationGroups
from app.tacacs.models import ConfigurationUsers
from app.tacacs.models import TacacsGroup
from app.tacacs.models import GroupCommands
from app.tacacs.models import TacacsUserGroups
from app.tacacs.models import Command
from app.tacacs.models import TacacsUser
from app.tacacs.models import UserACL
from app.tacacs.models import GroupACL

# Utils
from app.utils.tacacs.utils import verify_the_configuration
from app.utils.render import render_configuration

# System
import sys
# Logging
import logging

# Configure logging to console and file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("tacacs.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Blueprint
mod_tac_plus = Blueprint('tac_plus', __name__, url_prefix='/tac_plus')

@mod_tac_plus.route('/configurations/', methods=['GET'])
def configurations():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	configurations = Configuration.query.all()
	return render_template("tacacs/configurations.html", configurations=configurations, status = request.args.get("status", None))

@mod_tac_plus.route('/add_configuration/', methods=['POST'])
def add_configuration():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	configuration = Configuration()
	configuration.name = request.form.get("configuration_name", "")
	db.session.add(configuration)
	db.session.commit()
	return redirect(url_for("tac_plus.configurations"))

@mod_tac_plus.route('/edit_configuration/', methods=['GET', 'POST'])
def edit_configuration():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		try:
			configuration = Configuration.query.filter_by(id=request.args.get("config_id", None)).one()
			configuration_groups = ConfigurationGroups.query.filter_by(configuration_id=configuration.id).join(TacacsGroup).all()
			groups = [cg.group for cg in configuration_groups]
			configuration_users = ConfigurationUsers.query.filter_by(configuration_id=configuration.id).join(TacacsUser).all()
			users = [cu.user for cu in configuration_users]
			# Fetch all groups and users for selection
			all_groups = TacacsGroup.query.all()
			all_users = TacacsUser.query.all()
			return render_template(
				"tacacs/edit_configuration.html",
				configuration=configuration,
				groups=groups,
				users=users,
				all_groups=all_groups,
				all_users=all_users
			)
		except Exception as e:
			logging.debug(e)
			return redirect(url_for("tac_plus.configurations"))
	else:
		configuration = Configuration.query.filter_by(id=request.form.get("configuration_id", None)).one()
		configuration.name = request.form.get("name", "")
		db.session.commit()
		return redirect(url_for("tac_plus.configurations"))

@mod_tac_plus.route('/delete_configuration/', methods=['GET'])
def delete_configuration():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))

	try:
		configuration = Configuration.query.filter_by(id=request.args.get("config_id", None)).one()
		db.session.delete(configuration)
		db.session.commit()
	except:
		pass
	return redirect(url_for("tac_plus.configurations"))

@mod_tac_plus.route("/groups/", methods=["GET"])
def groups():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	groups = TacacsGroup.query.all()
	return render_template("tacacs/groups.html", groups = groups)

@mod_tac_plus.route("/users/", methods=["GET"])
def users():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	users = TacacsUser.query.all()
	return render_template("tacacs/users.html", users = users)

@mod_tac_plus.route("/commands/", methods=["GET"])
def commands():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	commands = Command.query.all()
	return render_template("tacacs/commands.html", commands = commands)

@mod_tac_plus.route("/delete_command/", methods=["POST"])
def delete_command():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	try:
		command = Command.query.filter_by(id=request.args.get("command_id", "")).one()
		if command:
			db.session.delete(command)
			db.session.commit()
	except:
		pass
	return redirect(url_for('tac_plus.commands'))

@mod_tac_plus.route("/edit_command/", methods=["GET", "POST"])
def edit_command():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		try:
			command = Command.query.filter_by(id=request.args.get("command_id", "")).one()
			return render_template("tacacs/edit_command.html", command=command)
		except:
			return redirect(url_for('tac_plus.commands'))
	else:
		try:
			command = Command.query.filter_by(id=request.form.get("command_id", "")).one()
			command.name = request.form.get("command_name", "")
			command.permit_regex = request.form.get("permit_regex", "")
			command.deny_regex = request.form.get("deny_regex", "")
			command.permit_message = request.form.get("permit_message", "")
			command.deny_message = request.form.get("deny_message", "")		
			db.session.commit()
			return redirect(url_for('tac_plus.commands'))
		except Exception as e: 
			logging.debug(e)
			return redirect(url_for('tac_plus.commands'))	


@mod_tac_plus.route("/add_command/", methods=["POST"])
def add_command():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	command = Command()
	command.name = request.form.get("command_name", "")
	command.regex = request.form.get("regex", "")
	command.message = request.form.get("message", "")
	command.action = request.form.get("action", "")
	db.session.add(command)
	db.session.commit()
	return redirect(url_for('tac_plus.commands'))


@mod_tac_plus.route("/add_group/", methods=["POST"])
def add_group():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	group = TacacsGroup()
	group.name = request.form.get("group_name", "")
	valid_until = request.form.get("valid_until", "")
	if valid_until:
		try:
			group.valid_until = datetime.strptime(valid_until, "%Y-%m-%d")
		except Exception:
			group.valid_until = None
	else:
		group.valid_until = None
	group.cmd_default_policy = request.form.get("cmd_default_policy", "")
	group.default_privilege = request.form.get("default_privilege", "")
	group.is_enable_pass = True if request.form.get("is_enable_pass", "") == "on" else False
	group.deny_default_service = True if request.form.get("deny_default_service", "") == "on" else False
	group.enable_pass = request.form.get("enable_pass", "")
	db.session.add(group)
	db.session.commit()
	return redirect(url_for('tac_plus.groups'))

@mod_tac_plus.route("/delete_group/", methods=["POST"])
def delete_group():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	try:
		group = TacacsGroup.query.filter_by(id=request.form.get("group_id", "")).one()
		if group:
			db.session.delete(group)
			db.session.commit()
	except:
		pass
	return redirect(url_for('tac_plus.groups'))

@mod_tac_plus.route("/add_command_to_group/", methods=["POST"])
def add_command_to_group():
    if not session.get("user_id", None):
        return jsonify([]), 403
    group_id = request.form.get("group_id", None)
    command_id = request.form.get("command_id", None)
    found = False
    try:
        group_command = GroupCommands.query.filter_by(group_id=group_id, command_id=command_id).all()
        if len(group_command) > 0:
            found = True
    except Exception as e:
        pass
    if found:
        return jsonify([])
    group_command = GroupCommands()
    group_command.group_id = group_id
    group_command.command_id = command_id
    db.session.add(group_command)
    db.session.commit()
    return redirect(url_for('tac_plus.edit_group', group_id=group_id))

@mod_tac_plus.route("/add_group_to_configuration/", methods=["POST"])
def add_group_to_configuration():
    if not session.get("user_id", None):
        return redirect(url_for('auth.signin'))
    config_id = request.form.get("config_id", None)
    group_id = request.form.get("group_id", None)
    found = False
    try:
        group_configuration = ConfigurationGroups.query.filter_by(configuration_id=config_id, group_id=group_id).all()
        if len(group_configuration) > 0:
            found = True
    except Exception as e:
        pass
    if not found:
        group_configuration = ConfigurationGroups()
        group_configuration.group_id = group_id
        group_configuration.configuration_id = config_id
        db.session.add(group_configuration)
        db.session.commit()
    return redirect(url_for('tac_plus.edit_configuration', config_id=config_id))

@mod_tac_plus.route("/add_user_to_configuration/", methods=["POST"])
def add_user_to_configuration():
    if not session.get("user_id", None):
        return redirect(url_for('auth.signin'))
    config_id = request.form.get("config_id", None)
    user_id = request.form.get("user_id", None)
    found = False
    try:
        user_configuration = ConfigurationUsers.query.filter_by(configuration_id=config_id, user_id=user_id).all()
        if len(user_configuration) > 0:
            found = True
    except Exception as e:
        logging.debug(e)
        pass
    if not found:
        user_configuration = ConfigurationUsers()
        user_configuration.user_id = user_id
        user_configuration.configuration_id = config_id
        db.session.add(user_configuration)
        db.session.commit()
    return redirect(url_for('tac_plus.edit_configuration', config_id=config_id))

@mod_tac_plus.route("/delete_command_from_group/", methods=["POST"])
def delete_command_from_group():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if not session.get("csrf_token", None):
		return jsonify([]), 403
	#if request.args.get("csrf_token", None) != session["csrf_token"]:
	#	return jsonify([]), 403
	group_command = GroupCommands.query.filter_by(group_id=request.args.get("group_id", ""), \
		command_id=request.args.get("command_id", "")).one()
	if group_command:
		db.session.delete(group_command)
		db.session.commit()
	return redirect(url_for('tac_plus.edit_group', group_id = request.args.get("group_id", "")))

@mod_tac_plus.route("/delete_group_from_configuration/", methods=["POST"])
def delete_group_from_configuration():
    if not session.get("user_id", None):
        return redirect(url_for('auth.signin'))
    if not session.get("csrf_token", None):
        return jsonify([]), 403
    group_id = request.form.get("group_id", "")
    config_id = request.form.get("config_id", "")
    group_configuration = ConfigurationGroups.query.filter_by(group_id=group_id, configuration_id=config_id).one()
    if group_configuration:
        db.session.delete(group_configuration)
        db.session.commit()
    return redirect(url_for('tac_plus.edit_configuration', config_id=config_id))

@mod_tac_plus.route("/delete_user_from_configuration/", methods=["POST"])
def delete_user_from_configuration():
    if not session.get("user_id", None):
        return redirect(url_for('auth.signin'))
    if not session.get("csrf_token", None):
        return jsonify([]), 403
    user_id = request.form.get("user_id", "")
    config_id = request.form.get("config_id", "")
    user_configuration = ConfigurationUsers.query.filter_by(user_id=user_id, configuration_id=config_id).one()
    if user_configuration:
        db.session.delete(user_configuration)
        db.session.commit()
    return redirect(url_for('tac_plus.edit_configuration', config_id=config_id))

@mod_tac_plus.route("/add_group_to_user/", methods=["POST"])
def add_group_to_user():
    if not session.get("user_id", None):
        return jsonify([]), 403
    user_id = request.form.get("user_id", None)
    group_id = request.form.get("group_id", None)
    user_groups = TacacsUserGroups()
    user_groups.user_id = user_id
    user_groups.group_id = group_id
    db.session.add(user_groups)
    db.session.commit()
    return redirect(url_for('tac_plus.edit_user', user_id=user_id))

@mod_tac_plus.route("/delete_group_from_user/", methods=["POST"])
def delete_group_from_user():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	user_group = TacacsUserGroups.query.filter_by(user_id=request.args.get("user_id", ""), \
		group_id=request.args.get("group_id", "")).one()
	if user_group:
		db.session.delete(user_group)
		db.session.commit()
	return redirect(url_for('tac_plus.edit_user', user_id = request.args.get("user_id", "")))

@mod_tac_plus.route("/add_user/", methods=["POST"])
def add_user():
    if not session.get("user_id", None):
        return redirect(url_for('auth.signin'))
    user = TacacsUser()
    user.name = request.form.get("user_name", "")
    user.password = request.form.get("password", "")
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('tac_plus.users'))

@mod_tac_plus.route("/delete_user/", methods=["POST"])
def delete_user():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	try:
		user_id = request.form.get("user_id", "")
		user_configurations = ConfigurationUsers.query.filter_by(user_id=user_id).all()
		for user_configuration in user_configurations:
			db.session.delete(user_configuration)
			db.session.commit()
		user_groups = TacacsUserGroups.query.filter_by(user_id=user_id).all()
		for user_group in user_groups:
			db.session.delete(user_group)
			db.session.commit()
		user = TacacsUser.query.filter_by(id=user_id).one()
		if user:
			db.session.delete(user)
			db.session.commit()
	except Exception as e:
		pass
	return redirect(url_for('tac_plus.users'))

@mod_tac_plus.route("/edit_user/", methods=["GET", "POST"])
def edit_user():
    if not session.get("user_id", None):
        return redirect(url_for('auth.signin'))
    if request.method == "GET":
        try:
            user = TacacsUser.query.filter_by(id=request.args.get("user_id", "")).one()
            user_groups = TacacsUserGroups.query.filter_by(user_id = user.id) \
                .join(TacacsGroup) \
                .all()
            
            user_acls = UserACL.query.filter_by(user_id = request.args.get("user_id", "")).all()    
            
            acls = []
            for acl in user_acls:
                acls.append(acl)

            groups = []
            user_group_ids = []
            for user_group in user_groups:
                groups.append(user_group.group)
                user_group_ids.append(user_group.group.id)

            user_acl_ids = [acl.id for acl in user_acls]
            available_groups = TacacsGroup.query.all()
            all_acls = UserACL.query.all()
            return render_template(
                "tacacs/edit_user.html",
                user=user,
                groups=groups,
                acls=acls,
                all_acls=all_acls,
                available_groups=available_groups,
                user_group_ids=user_group_ids,
                user_acl_ids=user_acl_ids
            )
        except Exception as e:
            logging.debug(e)
            return redirect(url_for('tac_plus.users'))
    else:
        try:
            user = TacacsUser.query.filter_by(id=request.form.get("user_id", "")).one()
            user.name = request.form.get("user_name", "")
            user.password = request.form.get("password", "")
            db.session.commit()
            return redirect(url_for('tac_plus.users'))
        except Exception as e:
            logging.debug(e)
            return redirect(url_for('tac_plus.users'))

@mod_tac_plus.route("/add_acl_to_group/", methods=["POST"])
def add_acl_to_group():
    if not session.get("user_id", None):
        return jsonify({}), 403
    group_id = request.form.get("group_id", "")
    ip = request.form.get("ip", "")
    mask = request.form.get("mask", "")
    access = request.form.get("access", "")
    if not (group_id and ip and mask and access):
        return jsonify({"error": "Missing data"}), 400
    if access not in ("permit", "deny"):
        return jsonify({"error": "Access must be 'permit' or 'deny'"}), 400
    try:
        ipaddress.ip_network(f"{ip}/{mask}", strict=False)
    except Exception:
        return jsonify({"error": "Invalid IP address or mask"}), 400
    acl = GroupACL()
    acl.group_id = group_id
    acl.ip = ip
    acl.mask = mask
    acl.access = access
    db.session.add(acl)
    db.session.commit()
    return redirect(url_for('tac_plus.edit_group', group_id=group_id))

@mod_tac_plus.route("/delete_acl_from_group/", methods=["POST"])
def delete_acl_from_group():
    if not session.get("user_id", None):
        return jsonify({}), 403
    group_id = request.form.get("group_id", "")
    acl_id = request.form.get("acl_id", "")
    try:
        acl = GroupACL.query.filter_by(group_id=group_id, id=acl_id).first()
        db.session.delete(acl)
        db.session.commit()
        return redirect(url_for('tac_plus.edit_group', group_id=group_id))
    except Exception as e:
        return jsonify({})
    
@mod_tac_plus.route("/add_acl_to_user/", methods=["POST"])
def add_acl_to_user():
	if not session.get("user_id", None):
		return jsonify({}), 403
	user_id = request.form.get("user_id", "")
	ip = request.form.get("ip", "")
	mask = request.form.get("mask", "")
	access = request.form.get("access", "")
	if not (user_id and ip and mask and access):
		return jsonify({"error": "Missing data"}), 400
	if access not in ("permit", "deny"):
		return jsonify({"error": "Access must be 'permit' or 'deny'"}), 400
	try:
		ipaddress.ip_network(f"{ip}/{mask}", strict=False)
	except Exception:
		return jsonify({"error": "Invalid IP address or mask"}), 400
	acl = UserACL()
	acl.user_id = user_id
	acl.ip = ip
	acl.mask = mask
	acl.access = access
	db.session.add(acl)
	db.session.commit()
	return redirect(url_for('tac_plus.edit_user', user_id=user_id))

@mod_tac_plus.route("/delete_acl_from_user/", methods=["POST"])
def delete_acl_from_user():
    if not session.get("user_id", None):
        return jsonify({}), 403
    user_id = request.form.get("user_id", "")
    acl_id = request.form.get("acl_id", "")
    try:
        acl = UserACL.query.filter_by(user_id=user_id, id=acl_id).first()
        db.session.delete(acl)
        db.session.commit()
        return redirect(url_for('tac_plus.edit_user', user_id=user_id))
    except Exception as e:
        return jsonify({})

@mod_tac_plus.route("/edit_group/", methods=["GET", "POST"])
def edit_group():
    if not session.get("user_id", None):
        return redirect(url_for('auth.signin'))
    if request.method == "GET":
        try:
            group = TacacsGroup.query.filter_by(id=request.args.get("group_id", "")).one()
            group_commands = GroupCommands.query.filter_by(group_id=group.id).join(Command).all()
            commands = [gc.command for gc in group_commands]
            group_acls = GroupACL.query.filter_by(group_id=group.id).all()
            acls = group_acls
            # For dropdowns: all commands and all acls
            all_commands = Command.query.all()
            all_acls = GroupACL.query.all()
            # For filtering: ids already assigned
            group_command_ids = [cmd.id for cmd in commands]
            group_acl_ids = [acl.id for acl in acls]
            return render_template(
                "tacacs/edit_group.html",
                group=group,
                commands=commands,
                acls=acls,
                all_commands=all_commands,
                all_acls=all_acls,
                group_command_ids=group_command_ids,
                group_acl_ids=group_acl_ids
            )
        except Exception as e:
            logging.debug(e)
            return redirect(url_for('tac_plus.groups'))
    else:
        try:
            group = TacacsGroup.query.filter_by(id=request.form.get("group_id", "")).one()
            group.name = request.form.get("group_name", "")
            group.valid_until = request.form.get("valid_until", "")
            group.cmd_default_policy = request.form.get("cmd_default_policy", "")
            group.default_privilege = request.form.get("default_privilege", "")
            group.is_enable_pass = True if request.form.get("is_enable_pass", "") == "on" else False
            group.enable_pass = request.form.get("enable_pass", "")
            group.deny_default_service = True if request.form.get("deny_default_service", "") == "on" else False
            db.session.commit()
            return redirect(url_for('tac_plus.groups'))
        except Exception as e:
            logging.debug(e)
            return redirect(url_for('tac_plus.groups'))

@mod_tac_plus.route('/system/', methods=['GET', 'POST'])
def system():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		system = System.query.filter().first()
		if not system:
			system = System()
			db.session.add(system)
			db.session.commit()
		return render_template("tacacs/system.html", system=system)
	else:
		system = System.query.filter_by(id=request.form.get("system_id", "")).one()
		system.log_files_path = request.form.get("log_files_path", "/var/log/tac_plus/")
		system.welcome_banner = request.form.get("welcome_banner", "/usr/local/etc/tac_plus.cfg")
		system.port_number = int(request.form.get("port_number", 49))
		system.mavis_exec = request.form.get("mavis_exec", "/usr/local/lib/mavis/mavis_tacplus_passwd.pl")
		system.host_ip = request.form.get("host_ip", "0.0.0.0/0")
		system.auth_key = request.form.get("auth_key", "my key")
		system.login_backend = "mavis"
		system.tacplus_app = request.form.get("tacplus_app", "/usr/local/sbin/tac_plus")
		system.tacplus_config = request.form.get("tacplus_config", "/usr/local/etc/tac_plus.cfg")
		system.tacplus_systemd_service = request.form.get("tacplus_systemd_service", "tac_plus.service")
		db.session.commit()
		return render_template("tacacs/system.html", system=system)

def build_rendered_config(configuration_id):
    system = System.query.first()
    if not system:
        return None, None, None, None
    configuration_groups = ConfigurationGroups.query.filter_by(configuration_id=configuration_id).all()
    groups = []
    for configuration_group in configuration_groups:
        group = {
            "group": configuration_group.group,
            "commands": [gc.command for gc in GroupCommands.query.filter_by(group_id=configuration_group.group.id).all()],
            "acls": GroupACL.query.filter_by(group_id=configuration_group.group.id).all()
        }
        groups.append(group)
    configuration_users = ConfigurationUsers.query.filter_by(configuration_id=configuration_id).all()
    users = []
    for configuration_user in configuration_users:
        user = {
            "user": configuration_user.user,
            "groups": [ug.group for ug in TacacsUserGroups.query.filter_by(user_id=configuration_user.user.id)],
            "acls": UserACL.query.filter_by(user_id=configuration_user.user.id).all()
        }
        users.append(user)
    rendered_config = render_configuration(system, groups, users)
    return system, rendered_config, groups, users

@mod_tac_plus.route("/verify_configuration/", methods=["POST"])
def verify_configuration():
    if not session.get("user_id", None):
        return redirect(url_for('auth.signin'))
    configuration_id = request.form.get("config_id", "")
    if not re.match("[1-9]{1}[0-9]*", configuration_id):
        return redirect(url_for("tac_plus.configurations"))
    system, rendered_config, groups, users = build_rendered_config(configuration_id)
    if not system:
        logging.debug("Exiting no system configuration found...")
        return redirect(url_for("tac_plus.configurations"))
    temporary_configuration_file = os.path.join(os.path.curdir, 'tmp', secrets.token_hex(nbytes=16) + '.cfg')
    if rendered_config is None:
        return redirect(url_for("tac_plus.configurations", status="Error: Could not render configuration."))
    with open(os.path.abspath(temporary_configuration_file), "w") as temp_cfg_file:
        temp_cfg_file.write(rendered_config)
    status = "Build status: Configuration file is OK!"
    if not verify_the_configuration(temporary_configuration_file):
        status = "Build status: Configuration file is NOT OK!"
    os.remove(temporary_configuration_file)
    return redirect(url_for("tac_plus.configurations", status=status))

@mod_tac_plus.route("/deploy_configuration/", methods=["POST"])
def deploy_configuration_route():
    if not session.get("user_id", None):
        return redirect(url_for('auth.signin'))
    configuration_id = request.form.get("config_id", "")
    if not re.match("[1-9]{1}[0-9]*", configuration_id):
        return redirect(url_for("tac_plus.configurations"))
    configurations = Configuration.query.all()
    for configuration in configurations:
        configuration.deployed = False
        db.session.commit()
    try:
        configuration = Configuration.query.filter_by(id=configuration_id).one()
        configuration.deployed = True
        db.session.commit()
    except Exception as e:
        return redirect(url_for("tac_plus.configurations"))
    system, rendered_config, groups, users = build_rendered_config(configuration_id)
    if not system:
        logging.debug("Exiting no system configuration found...")
        return redirect(url_for("tac_plus.configurations"))
    temporary_configuration_file = os.path.join(os.path.curdir, 'tmp', secrets.token_hex(nbytes=16) + '.cfg')
    if rendered_config is None:
        status = "Error: Could not render configuration."
        return redirect(url_for("tac_plus.configurations", status=status))
    with open(temporary_configuration_file, "w") as fd:
        fd.write(rendered_config)
    if not verify_the_configuration(temporary_configuration_file):
        status = "Build status: Configuration file is NOT OK!"
    # Move to /tacacsgui/tac_plus-ng.conf and touch /tacacsgui/reload_tacacs_cfg
    import shutil
    shutil.move(temporary_configuration_file, "/opt/tacacsgui/tac_plus-ng.conf")
    with open("/opt/tacacsgui/reload_tacacs_cfg", "a"):
        os.utime("/opt/tacacsgui/reload_tacacs_cfg", None)
    status = "Build status: Configuration file is OK! Deploy in progress..."
    return redirect(url_for("tac_plus.configurations", status=status))
