import flask

def public():
    user = flask.session.get('username')
    if user != None:
        user = str(user).upper()
    else:
        user = "PUBLIC_USER"

    return flask.render_template("public.html", user=user)


def register_public_routes(app):
	app.add_url_rule("/public", "public", public)
