# Import flask dependencies
from flask import Blueprint, request, render_template, \
                  flash, session, redirect, url_for


# Import the database object from the main app module
from app import db

# Import tacacs users
from app.auth.models import SystemUser

# Secrets
import secrets

# Import regex stuff
import re

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_auth = Blueprint('auth', __name__, url_prefix='/auth')

# Set the route and accepted methods
@mod_auth.route("/signin/", methods=["GET", "POST"])
def signin():
    error = None
    # Check if any system users exist in the database
    user_count = SystemUser.query.count()
    bootstrap_mode = user_count == 0
    if request.method == "POST":
        username = request.form.get("username", None)
        password = request.form.get("password", "")
        if not username:
            error = 'Username is required'
            return render_template("auth/signin.html", error=error)
        if bootstrap_mode:
            # Allow default admin login if no users exist
            if username == "admin" and password == "password":
                session["user_id"] = "admin"
                session["csrf_token"] = secrets.token_hex(nbytes=16)
                session["bootstrap_mode"] = True
                flash('Bootstrap mode: Please create the first user.')
                return redirect(url_for('auth.system_users'))
            else:
                error = 'Default admin login is only available until the first user is created.'
                return render_template("auth/signin.html", error=error)
        # Normal login flow
        try:
            user = SystemUser.query.filter_by(username=username).first()
            if not user or not user.check_password(password):
                error = 'Wrong username or password'
                return render_template("auth/signin.html", error=error)
            session["user_id"] = user.username
            session["csrf_token"] = secrets.token_hex(nbytes=16)
            session.pop("bootstrap_mode", None)
            flash('Welcome %s' % user.username)
            return redirect(url_for('tac_plus.configurations'))
        except Exception as e:
            error = str(e)
    return render_template("auth/signin.html", error=error)

@mod_auth.route("/logout/", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('auth.signin'))

@mod_auth.route("/reset_tacacs_password/", methods=["GET", "POST"])
def reset_tacacs_password():
    if request.method == "POST":
        username = request.form.get("username", "")
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        new_password_confirm = request.form.get("new_password_confirm", "")
        try:
            tacacs_user = SystemUser.query.filter_by(username = username).one()
        except:
            return render_template("auth/reset_tacacs_password.html", error="User was not found in the database", status=None)
        if not tacacs_user.check_password(old_password):
            return render_template("auth/reset_tacacs_password.html", error="Old password is incorrect", status=None)
        if not re.match(r"[a-zA-Z_$@0-9]{5,16}", new_password):
            return render_template("auth/reset_tacacs_password.html", error="Password is too easy. It should match the regex: [a-zA-Z_$@0-9]{5,16}", status=None)
        if new_password != new_password_confirm:
            return render_template("auth/reset_tacacs_password.html", error="Passwords do not match!", status=None)
        tacacs_user.password = new_password
        db.session.commit()
        return render_template("auth/reset_tacacs_password.html", error=None, status="Password was changed! Contact your administrator and ask to update the configuration file")
    else:
        return render_template("auth/reset_tacacs_password.html", error=None, status=None)

@mod_auth.route("/system_users/", methods=["GET", "POST"])
def system_users():
    # Only allow access if logged in (or in bootstrap mode)
    if not session.get("user_id"):
        return redirect(url_for('auth.signin'))
    user_count = SystemUser.query.count()
    bootstrap_mode = session.get("bootstrap_mode", False)
    users = SystemUser.query.all()
    error = None
    status = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add":
            username = request.form.get("name", "").strip()
            password = request.form.get("password", "")
            if not username or not password:
                error = "Username and password are required."
            elif SystemUser.query.filter_by(username=username).first():
                error = "User already exists."
            else:
                new_user = SystemUser()
                new_user.username = username
                new_user.password = password
                db.session.add(new_user)
                db.session.commit()
                status = f"User {username} created."
                # If in bootstrap mode, remove bootstrap session
                if bootstrap_mode and SystemUser.query.count() > 0:
                    session.pop("bootstrap_mode", None)
        elif action == "delete":
            user_id = request.form.get("user_id")
            user = SystemUser.query.filter_by(id=user_id).first()
            if user:
                db.session.delete(user)
                db.session.commit()
                status = f"User {user.username} deleted."
            else:
                error = "User not found."
        elif action == "edit":
            user_id = request.form.get("user_id")
            password = request.form.get("password", "")
            user = SystemUser.query.filter_by(id=user_id).first()
            if user:
                if password:
                    user.password = password
                    db.session.commit()
                    status = f"Password for {user.username} updated."
                else:
                    error = "Password required to update."
            else:
                error = "User not found."
        users = SystemUser.query.all()
    return render_template("auth/system_users.html", users=users, error=error, status=status, bootstrap_mode=bootstrap_mode)
