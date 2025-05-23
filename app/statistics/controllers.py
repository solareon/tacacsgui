from flask import Blueprint, request, render_template, \
                  session, redirect, url_for
from app import db

from app.tacacs.models import System

# Utils

mod_tac_plus_statistiscs = Blueprint('tac_plus_statistics', __name__)

@mod_tac_plus_statistiscs.route('/statistics/', methods=['GET'])
def statistics():
	if not session.get("user_id", None):
		return redirect(url_for('auth.signin'))
	if request.method == "GET":
		system = System.query.filter().first()
		if not system:
			system = System()
			db.session.commit()
		auth_data = {
			"success": 0,
			"failure": 0
		}
		try:
			fd_authentication = open("/".join([system.log_files_path, "authentication.log"]))
			line = fd_authentication.readline()
			while line:
				try:
					auth_log_entity = line.split("\t")[5]
					if auth_log_entity.count("succeeded") > 0:
						auth_data["success"] += 1
					if auth_log_entity.count("failed") > 0:
						auth_data["failure"] += 1
				except Exception as e:
					#print(e)
					pass
				line = fd_authentication.readline()
			fd_authentication.close()
		except:
			pass
		authorization_data = {
			"success": 0,
			"failure": 0
		}
		try:
			fd_authorization = open("/".join([system.log_files_path, "authorization.log"]))
			line = fd_authorization.readline()
			while line:
				try:
					auth_log_entity = line.split("\t")[5]
					if auth_log_entity.count("permit") > 0:
						authorization_data["success"] += 1
					if auth_log_entity.count("deny") > 0:
						authorization_data["failure"] += 1
				except Exception as e:
					pass
				line = fd_authorization.readline()
			fd_authorization.close()
		except:
			pass
		return render_template("statistics/statistics.html", \
			authentication_data = auth_data, \
			authorization_data = authorization_data)
	# Fallback return if method is not GET (should not happen, but for type safety)
	return redirect(url_for('auth.signin'))
