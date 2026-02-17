import os
import flask
import logging
from dotenv import load_dotenv
import json
import subprocess
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix

from routes.cli import register_cli_routes
from routes.login import register_login_routes
from routes.performance import register_performance_routes
from routes.public import register_public_routes
from routes.fileManager import register_fileManager_routes
from routes.chatbot import register_chatbot_routes

from pathlib import Path

load_dotenv()

# --- Logging ---
auth_log = logging.getLogger('auth')
auth_handler = logging.FileHandler('./logs/auth.log')
auth_log.addHandler(auth_handler)
auth_log.setLevel(logging.INFO)

# --- Flask App ---
app = flask.Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1) # makes it so it interprets nginx forwarded IPs instead of using local ip cuz running locally

allowed_users = json.load(open('users.json'))

# --- Session Configuration (server-side) ---
app.config['SESSION_TYPE'] = os.getenv("FLASK_SESSION_TYPE")
app.config['SESSION_FILE_DIR'] = os.getenv("FLASK_SESSION_DIR")
app.config['SESSION_PERMANENT'] = False  # session ends on browser close
app.config['SESSION_USE_SIGNER'] = True  # add signature to session IDs
app.config['PROPAGATE_EXCEPTIONS'] = False  # prevent debug info leaking
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# --- Initialize server-side session ---
Session(app)

global_html = {}
directory_path = Path('/home/mike/webserver/templates/global')
for item in directory_path.iterdir():
    file = open(item,'r')
    global_html[item.name] = (file.read()).strip()
    file.close()

app.config['global_html'] = global_html

# --- Routes ---

def homepage():
    user = flask.session.get('username')
    try:
        user = str(user).upper()
    except Exception:
        user = user

    last_updated = ""
    if os.path.exists('lastupdated.txt'):
        with open('lastupdated.txt', "r") as file:
            last_updated = file.read().strip()

    return flask.render_template('homepage.html', user=user, last_updated=last_updated,global_html=global_html)

def require_login():
    public_endpoints = ('login','public')
    if flask.request.endpoint not in public_endpoints and not flask.session.get('authenticated'):
        return flask.redirect(flask.url_for("login", next=flask.request.path))

app.before_request(require_login)

def update():

    if flask.session.get('username') != 'michael':
        return flask.redirect('/')

    result = subprocess.run(
        ["/bin/bash", "/home/mike/update.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return flask.redirect('/cpanel')

def reboot():
    if flask.session.get('username') not in ['michael','ats10']:
        return flask.redirect('/')

    subprocess.run(["sudo", "/usr/sbin/reboot"])

    return flask.redirect('/cpanel')

def control_panel():
    if flask.session.get('username') != 'michael':
        return flask.redirect('/')

    user = flask.session.get('username')
    try:
        user = str(user).upper()
    except Exception:
        user = user

    last_updated = ""
    if os.path.exists('lastupdated.txt'):
        with open('lastupdated.txt', "r") as file:
            last_updated = file.read().strip()

    return flask.render_template('controlpanel.html',last_updated=last_updated,user=user,global_html=global_html)

# --- Add URL rules ---
app.add_url_rule('/', "homepage", homepage)
app.add_url_rule('/update', 'update', update)
app.add_url_rule('/reboot','reboot', reboot)
app.add_url_rule('/cpanel','cpanel',control_panel)

# --- Register route modules ---
register_cli_routes(app)
register_public_routes(app)
register_login_routes(app, auth_log, allowed_users)
register_performance_routes(app)
register_fileManager_routes(app)
register_chatbot_routes(app)

# --- Suppress Flask default logging ---
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- Run ---
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
