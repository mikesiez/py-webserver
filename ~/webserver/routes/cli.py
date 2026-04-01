import os
import subprocess
import flask

def cli_page():
	if flask.session.get('authenticated') != True:
		return flask.redirect('/login')
	return flask.render_template('cli.html')

def cli_run():
	if flask.session.get('authenticated') != True or flask.session.get('username') != "michael":
		return flask.redirect('/cli')

	if 'cwd' not in flask.session:
		flask.session['cwd'] = os.path.expanduser('~')

	data = flask.request.get_json()
	cmd = data.get('cmd','').strip()
	parts = cmd.split()

	allowed = ['ls','cd','uptime','whoami']
	if not parts or parts[0] not in allowed:
		return flask.jsonify({'output':f"Command '{cmd}' not allowed"})

	try:
		if parts[0] == 'cd':
			arg = parts[1] if len(parts) > 1 else "~"
			arg_expanded = os.path.expanduser(arg)

			rel_target = os.path.join(flask.session.get('cwd'), arg_expanded)
			abs_target = os.path.abspath(rel_target)
			note = ""

			if not os.path.exists(abs_target):
				abs_target = os.path.abspath(arg_expanded)
				if os.path.exists(abs_target):
					note = f"(could not find relative, considering absolute)"
				else:
					return flask.jsonify({"output":f"No dir : {arg}"})

			os.chdir(abs_target)
			flask.session['cwd'] = os.getcwd()

			msg = f"Changed dir to {flask.session.get('cwd')}"
			if note:
				msg += f" {note}"

			return flask.jsonify({'output':msg})

		proc = subprocess.run(cmd,cwd=flask.session.get('cwd'),
				capture_output=True,text=True,shell=True,
				timeout=10)
		output = proc.stdout or proc.stderr

	except Exception as e:
		output = f"Error: {e}"

	return flask.jsonify({"output": output})

def register_cli_routes(app):
	"""Called from app.py to register CLI routes"""
	app.add_url_rule('/cli', "cli_page", cli_page, methods=['GET'])
	app.add_url_rule('/cli/run', "cli_run", cli_run, methods=['POST'])
