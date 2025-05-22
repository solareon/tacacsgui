-- Remove database creation as SQLite does not support it
-- DROP DATABASE IF EXISTS tacacsgui;

-- Remove AUTO_INCREMENT and use INTEGER PRIMARY KEY for SQLite
CREATE TABLE auth_user(
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	username VARCHAR(128) NOT NULL,
	password VARCHAR(192) NOT NULL,
	salt VARCHAR(128) NOT NULL
);

CREATE TABLE tac_plus_system (
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	log_files_path VARCHAR(128) NOT NULL DEFAULT "/var/log/tac_plus/",
	cfg_file_path VARCHAR(128) NOT NULL DEFAULT "/usr/local/etc/tac_plus.cfg",
	port_number INT NOT NULL DEFAULT 49,
	mavis_exec VARCHAR(128) NOT NULL DEFAULT "/usr/local/lib/mavis/mavis_tacplus_passwd.pl",
	host_ip VARCHAR(128) NOT NULL DEFAULT "0.0.0.0/0",
	auth_key VARCHAR(128) NOT NULL DEFAULT "my key",
	login_backend VARCHAR(128) NOT NULL DEFAULT "mavis"
);

CREATE TABLE tac_plus_cfg (
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	name VARCHAR(128) NOT NULL,
	deployed BOOLEAN NOT NULL DEFAULT False
);

CREATE TABLE tac_plus_groups (
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	name VARCHAR(128) NOT NULL,
	valid_until DATETIME NOT NULL,
	cmd_default_policy VARCHAR(128) NOT NULL,
	default_privilege INT NOT NULL,
	is_enable_pass BOOL DEFAULT FALSE,
	enable_pass VARCHAR(100),
	deny_default_service BOOL NOT NULL DEFAULT FALSE
);

CREATE TABLE tac_plus_config_groups (
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	group_id INT NOT NULL,
	configuration_id INT NOT NULL,
	FOREIGN KEY (group_id)
    	REFERENCES tac_plus_groups(id)
    	ON DELETE CASCADE,
    FOREIGN KEY (configuration_id)
    	REFERENCES tac_plus_cfg(id)
    	ON DELETE CASCADE
);

CREATE TABLE tac_plus_users (
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	name VARCHAR(128) NOT NULL,
	password VARCHAR(128) NOT NULL
);

CREATE TABLE tac_plus_config_users (
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	user_id INT NOT NULL,
	configuration_id INT NOT NULL,
	FOREIGN KEY (user_id)
    	REFERENCES tac_plus_users(id),
    FOREIGN KEY (configuration_id)
    	REFERENCES tac_plus_cfg(id)
    	ON DELETE CASCADE
);

CREATE TABLE tac_plus_commands (
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	name VARCHAR(128) NOT NULL,
	permit_regex VARCHAR(512) NOT NULL,
	deny_regex VARCHAR(512) NOT NULL,
	permit_message VARCHAR(512) NOT NULL,
	deny_message VARCHAR(512) NOT NULL
);

CREATE TABLE tac_plus_group_commands (
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	group_id INT NOT NULL,
	command_id INT NOT NULL,
	FOREIGN KEY (group_id)
    	REFERENCES tac_plus_groups(id),
    FOREIGN KEY (command_id)
    	REFERENCES tac_plus_commands(id)
    	ON DELETE CASCADE
);

CREATE TABLE tac_plus_user_groups (
	id INTEGER PRIMARY KEY NOT NULL,
	date_created DATETIME NOT NULL,
	date_modified DATETIME NOT NULL,
	group_id INT NOT NULL,
	user_id INT NOT NULL,
	FOREIGN KEY (group_id)
    	REFERENCES tac_plus_groups(id),
    FOREIGN KEY (user_id)
    	REFERENCES tac_plus_users(id)
    	ON DELETE CASCADE
);

INSERT INTO auth_user(date_created, date_modified, username, password, salt) VALUES(NOW(), NOW(), "admin", SHA2(CONCAT("Jaiddaks", "CiWiWoat"), 256), "CiWiWoat");

INSERT INTO tac_plus_system(date_created, date_modified) VALUES(NOW(), NOW());

INSERT INTO tac_plus_commands(date_created, \
	date_modified, \
	name, \
	permit_regex,\
	deny_regex, \
	permit_message, \
	deny_message) VALUES(NOW(), NOW(), "display", "\".*\"", "", "", "");

INSERT INTO tac_plus_commands(date_created, \
	date_modified, \
	name, \
	permit_regex,\
	deny_regex, \
	permit_message, \
	deny_message) VALUES(NOW(), NOW(), "show", "\".*\"", "", "", "");

INSERT INTO tac_plus_commands(date_created, \
	date_modified, \
	name, \
	permit_regex,\
	deny_regex, \
	permit_message, \
	deny_message) VALUES(NOW(), NOW(), "interface", "\".*\"", "", "", "");

INSERT INTO tac_plus_commands(date_created, \
	date_modified, \
	name, \
	permit_regex,\
	deny_regex, \
	permit_message, \
	deny_message) VALUES(NOW(), NOW(), "undo", "shutdown", "", "", "");