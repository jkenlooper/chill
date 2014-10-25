import os

from werkzeug.local import LocalProxy
from flask import Flask, g, current_app
from jinja2 import FileSystemLoader
import sqlite3


#from chill.resource import resource
#from chill.page import page

def connect_to_database():
    return sqlite3.connect(current_app.config['CHILL_DATABASE_URI'])

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

db = LocalProxy(get_db)

def make_app(config=None, **kw):
    "factory to create the app"

    app = Flask('chill', static_url_path=os.path.abspath('.'), static_folder='static', template_folder='templates')

    if config:
        app.config.from_pyfile(config)
    app.config.update(kw)

    # Set the jinja2 template folder eith fallback for app.template_folder
    app.jinja_env.loader = FileSystemLoader( app.config.get('TEMPLATE_FOLDER', app.template_folder) )

    @app.teardown_appcontext
    def teardown_db(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()


    # STATIC_URL='http://cdn.example.com/whatever/works/'
    @app.context_processor
    def inject_static_url():
        """
        Inject the variable 'static_url' into the templates. Grab it from
        the environment variable STATIC_URL, or use the default.

        Template variable will always have a trailing slash.

        """
        static_url = app.config.get('STATIC_URL', app.static_url_path)
        if not static_url.endswith('/'):
            static_url += '/'
        return dict(
            static_url=static_url
        )

    # register any blueprints here
    #app.logger.warning("Not registering resource blueprint")
    #app.register_blueprint(resource)

    from chill.public import page
    #app.logger.warning("Not registering page blueprint")
    app.register_blueprint(page)

    # not here...
    #build_context_data(app)

    return app
