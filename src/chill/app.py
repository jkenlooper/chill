from flask import Flask

from chill.resource import resource
from chill.page import page
from chill.tools import build_context_data

def make_app(config, debug=False):
    "factory to create the app"

    app = Flask(__name__)

    app.config.from_pyfile(config)
    app.debug = debug

    # register any blueprints here
    app.register_blueprint(resource)
    app.register_blueprint(page)

    build_context_data(app)

    return app
