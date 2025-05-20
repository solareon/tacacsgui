from jinja2 import Environment, FileSystemLoader

def build_jinja2_context(system, groups, users):
    log_path = system.log_files_path.rstrip("/")
    context = {
        "listen_port": system.port_number,
        "min_instances": system.min_instances,
        "max_instances": system.max_instances,
        "authentication_log": f"{log_path}/authentication.log",
        "accounting_log": f"{log_path}/accounting.log",
        "authorization_log": f"{log_path}/authorization.log",
        "mavis_module": system.mavis_exec,
        "login_backend": "mavis",
        "default_host": system.host_ip,
        "authentication_key": system.auth_key,
        "groups": [],
        "users": [],
    }

    for group in groups:
        group_obj = group["group"]
        group_dict = {
            "name": group_obj.name,
            "enable_password": (
                f'enable = clear {group_obj.enable_pass}' if group_obj.is_enable_pass else None
            ),
            "default_service": (
                "default service = deny" if group_obj.deny_default_service else None
            ),
            "privilege_level": group_obj.default_privilege,
            "access": "\n".join(
                f'client = {"permit" if acl.access == "allow" else "deny"} {acl.ip}/{acl.mask}'
                for acl in group["acls"]
            ),
            "cmds": [],
        }
        # Group commands by name
        commands_groupped = {}
        for command in group["commands"]:
            commands_groupped.setdefault(command.name, []).append(command)
        for command_name, command_list in commands_groupped.items():
            permit = "".join(f"permit {cmd.permit_regex}\n" for cmd in command_list)
            deny = "".join(
                f"deny {cmd.deny_regex}\n" if cmd.deny_regex else "deny .\n"
                for cmd in command_list
            )
            group_dict["cmds"].append({
                "name": command_name,
                "permit": permit,
                "deny": deny,
            })
        context["groups"].append(group_dict)

    for user in users:
        user_obj = user["user"]
        user_dict = {
            "username": user_obj.name,
            "encrypted_password": user_obj.password_hash,
            "groups": "".join(f"member = {g.name}\n" for g in user["groups"]),
            "access": "\n".join(
                f'client = {"permit" if acl.access == "allow" else "deny"} {acl.ip}/{acl.mask}'
                for acl in user["acls"]
            ),
        }
        context["users"].append(user_dict)

    return context

def render_configuration(system, groups, users, template_dir="app/templates/tacacs", template_name="configuration.j2"):
    env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(template_name)
    context = build_jinja2_context(system, groups, users)
    return template.render(**context)