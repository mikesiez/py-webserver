import flask
import html
from werkzeug.security import check_password_hash

def homepage():
	user = flask.session.get('username')
	return flask.render_template('homepage.html', user=user)

def login(auth_log, allowed_users):
	if flask.session.get('authenticated') == True:
		return flask.redirect('/')
	
	if flask.request.method == "POST":
		uname = html.escape(flask.request.form.get("username",""))
		pwd = flask.request.form.get('password')
		stored_hash = allowed_users.get(uname)
		if stored_hash and check_password_hash(stored_hash,pwd):
			flask.session['authenticated'] = True
			flask.session['username'] = uname # tracking user
			auth_log.info(f'LOGIN SUCCESS {uname} from {flask.request.remote_addr}')
			return flask.redirect(flask.request.args.get("next") or "/")
		else:
			auth_log.warning(f'LOGIN FAIL {uname} from {flask.request.remote_addr}')
			return flask.render_template("login.html",error = "Wrong username or password")

	return flask.render_template("login.html")


def logout():
	flask.session.clear()
	return flask.redirect('/login')

def register_login_routes(app, auth_log, allowed_users):
	"""Registers login/logout routes in flask app"""
	app.add_url_rule("/login", "login", lambda: login(auth_log, allowed_users), methods=["GET", "POST"])
	app.add_url_rule("/logout", "logout", logout)
