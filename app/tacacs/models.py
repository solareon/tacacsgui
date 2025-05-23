from app import db
from app.utils.tacacs.crypt import generate_hash, verify_hash

class Base(db.Model):

	__abstract__  = True

	id            = db.Column(db.Integer, primary_key=True)
	date_created  = db.Column(db.DateTime,  default=db.func.current_timestamp())
	date_modified = db.Column(db.DateTime,  default=db.func.current_timestamp(), 
		onupdate=db.func.current_timestamp())

class System(Base):

	__tablename__ = "tac_plus_system"

	id                 = db.Column(db.Integer,      primary_key=True)

	# Log files path
	log_files_path     = db.Column(db.String(128),  nullable=False, default="/var/log/tac_plus/")

	# Welcome Banner (was Configuration file location)
	welcome_banner      = db.Column(db.String(128),  nullable=False, default="TACACS:")  # Now used for Welcome Banner

	# Listen port
	port_number        = db.Column(db.Integer,      nullable=False, default=49)

	# Mavis module password verification script
	mavis_exec         = db.Column(db.String(128),  nullable=False, default="/usr/local/lib/mavis/mavis_tacplus_passwd.pl")

	# Host IP
	host_ip            = db.Column(db.String(128),  nullable=False, default="0.0.0.0/0")

	# Authentication key
	auth_key           = db.Column(db.String(128),  nullable=False, default="my key")

	# Login backend
	login_backend      = db.Column(db.String(128),  nullable=False, default="mavis")
 
	min_instances     = db.Column(db.Integer,      nullable=False, default=1)
	max_instances     = db.Column(db.Integer,      nullable=False, default=32)

	# TACACS+ application path
	tacplus_app        = db.Column(db.String(256),  nullable=False, default="/usr/local/sbin/tac_plus")

	# TACACS+ configuration file path
	tacplus_config     = db.Column(db.String(256),  nullable=False, default="/usr/local/etc/tac_plus.cfg")

	# Systemd service name for TACACS+
	tacplus_systemd_service = db.Column(db.String(128), nullable=False, default="tac_plus.service")

class Configuration(Base):

	__tablename__ = "tac_plus_cfg"

	id                 = db.Column(db.Integer,      primary_key=True)

	# Name
	name               = db.Column(db.String(128),  nullable=False)

	# Deployed/Not deployed
	deployed           = db.Column(db.Boolean,      nullable=False, default=False)

class ConfigurationGroups(Base):

	__tablename__ = "tac_plus_config_groups"

	id                 = db.Column(db.Integer,      primary_key=True)
	group_id           = db.Column(db.Integer, db.ForeignKey('tac_plus_groups.id'), nullable=False)
	configuration_id   = db.Column(db.Integer, db.ForeignKey('tac_plus_cfg.id'), nullable=False)

	configuration      = db.relationship("Configuration", backref="configuration_group")
	group              = db.relationship("TacacsGroup", backref="configuration_group_1")

class ConfigurationUsers(Base):

	__tablename__ = "tac_plus_config_users"

	id                 = db.Column(db.Integer,      primary_key=True)
	user_id            = db.Column(db.Integer, db.ForeignKey('tac_plus_users.id'), nullable=False)
	configuration_id   = db.Column(db.Integer, db.ForeignKey('tac_plus_cfg.id'), nullable=False)

	configuration      = db.relationship("Configuration", backref="configuration_user")
	user               = db.relationship("TacacsUser", backref="configuration_user_1")


class TacacsGroup(Base):

	__tablename__ = "tac_plus_groups"

	id                   = db.Column(db.Integer,      primary_key=True)
	name                 = db.Column(db.String(128),  nullable=False)
	valid_until          = db.Column(db.DateTime,     nullable=False)
	cmd_default_policy   = db.Column(db.String(128),  nullable=False)
	default_privilege    = db.Column(db.Integer,      nullable=False)
	is_enable_pass       = db.Column(db.Boolean,      nullable=False, default = False)
	enable_pass          = db.Column(db.String(100),  nullable=True)
	deny_default_service = db.Column(db.Boolean,     nullable=False, default=False)

class GroupCommands(Base):
	__tablename__ = "tac_plus_group_commands"

	id                 = db.Column(db.Integer,      primary_key=True)
	group_id           = db.Column(db.Integer, db.ForeignKey('tac_plus_groups.id'), nullable=False)
	command_id         = db.Column(db.Integer, db.ForeignKey('tac_plus_commands.id'), nullable=False)
	group              = db.relationship("TacacsGroup", backref="group")
	command            = db.relationship("Command", backref="command")

class Command(Base):

	__tablename__ = "tac_plus_commands"

	id                 = db.Column(db.Integer,      primary_key=True)
	name               = db.Column(db.String(128),  nullable=False)
	regex       = db.Column(db.String(512),  nullable=False)
	message     = db.Column(db.String(512),  nullable=False)
	action       = db.Column(db.String(128),  nullable=False)

class UserACL(Base):
	__tablename__ = "tac_plus_user_acls"

	id                 = db.Column(db.Integer,      primary_key=True)
	user_id            = db.Column(db.Integer,      db.ForeignKey('tac_plus_users.id'), nullable=False)
	ip                 = db.Column(db.String(15),   nullable=False)
	mask               = db.Column(db.String(2),    nullable=False)
	access             = db.Column(db.String(5),    nullable=False)

class GroupACL(Base):
	__tablename__ = "tac_plus_group_acls"

	id                 = db.Column(db.Integer,      primary_key=True)
	group_id            = db.Column(db.Integer,     db.ForeignKey('tac_plus_groups.id'), nullable=False)
	ip                 = db.Column(db.String(15),   nullable=False)
	mask               = db.Column(db.String(2),    nullable=False)
	access             = db.Column(db.String(5),    nullable=False)

class TacacsUser(Base):

	__tablename__ = "tac_plus_users"

	id                 = db.Column(db.Integer,      primary_key=True)
	name               = db.Column(db.String(128),  nullable=False)
	password_hash      = db.Column(db.String(256),  nullable=False)

	@property
	def password(self):
		raise AttributeError("Password is write-only.")

	@password.setter
	def password(self, plaintext):
		self.password_hash = generate_hash(plaintext)

	def check_password(self, plaintext):
		try:
			return verify_hash(plaintext, self.password_hash)
		except Exception:
			return False


class TacacsUserGroups(Base):

	__tablename__ = "tac_plus_user_groups"

	id                 = db.Column(db.Integer,      primary_key=True)
	group_id           = db.Column(db.Integer, db.ForeignKey('tac_plus_groups.id'), nullable=False)
	user_id            = db.Column(db.Integer, db.ForeignKey('tac_plus_users.id'), nullable=False)
	group              = db.relationship("TacacsGroup", backref="user_group")
	user               = db.relationship("TacacsUser", backref="user")

