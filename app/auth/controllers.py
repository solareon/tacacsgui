# Import flask dependencies
from flask import Blueprint, request, render_template, \
                  flash, g, session, redirect, url_for


# Import the database object from the main app module
from app import db

# Import tacacs users
from app.tacacs.models import TacacsUser

# Secrets
import secrets


# Password encryption routines
from app.utils.tacacs.utils import encrypt_password

# Import pwd and grp for user and group management
import pwd
import grp

TACACS_GROUP = "tacacs"

# Import regex stuff
import re

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_auth = Blueprint('auth', __name__, url_prefix='/auth')

# Set the route and accepted methods
@mod_auth.route("/signin/", methods=["GET", "POST"])
def signin():
    error = None
    if request.method == "POST":
        username = request.form.get("username", None)
        password = request.form.get("password", "")
        if not username:
            error = 'Username is required'
            return render_template("auth/signin.html", error=error)
        try:
            # Check if user exists in the system
            user_info = pwd.getpwnam(username)
            # Check if user is in tacacs group
            groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
            # Also check primary group
            primary_group = grp.getgrgid(user_info.pw_gid).gr_name
            if TACACS_GROUP not in groups and TACACS_GROUP != primary_group:
                error = 'User is not a member of the tacacs group'
                return render_template("auth/signin.html", error=error)
            # Authenticate user using PAM
            import subprocess
            result = subprocess.run(['su', '-', username, '-c', 'true'], input=password + '\n', text=True, capture_output=True)
            if result.returncode != 0:
                error = 'Wrong username or password'
                return render_template("auth/signin.html", error=error)
            session["user_id"] = username
            session["csrf_token"] = secrets.token_hex(nbytes=16)
            flash('Welcome %s' % username)
            return redirect(url_for('tac_plus.configurations'))
        except KeyError:
            error = 'Wrong username or password'
        except Exception as e:
            error = str(e)
    return render_template("auth/signin.html", error=error)

@mod_auth.route("/logout/", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('auth.signin'))

@mod_auth.route("/reset_tacacs_password/", methods=["GET", "POST"])
def reset_tacacs_password():
    error = None
    status = None
    if request.method == "POST":
        username = request.form.get("username", "")
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        new_password_confirm = request.form.get("new_password_confirm", "")
        try:
            tacacs_user = TacacsUser.query.filter_by(name = username).one()
        except:
            return render_template("auth/reset_tacacs_password.html", error="User was not found in the database", status=None)
        if encrypt_password(old_password) != tacacs_user.password:
            return render_template("auth/reset_tacacs_password.html", error="Old password is incorrect", status=None)
        if not re.match(r"[a-zA-Z_$@0-9]{5,16}", new_password):
            return render_template("auth/reset_tacacs_password.html", error="Password is too easy. It should match the regex: [a-zA-Z_$@0-9]{5,16}", status=None)
        if new_password != new_password_confirm:
            return render_template("auth/reset_tacacs_password.html", error="Passwords do not match!", status=None)
        tacacs_user.password = encrypt_password(new_password)
        db.session.commit()
        return render_template("auth/reset_tacacs_password.html", error=None, status="Password was changed! Contact your administrator and ask to update the configuration file")
    else:
        return render_template("auth/reset_tacacs_password.html", error=None, status=None)
