import os

from werkzeug.local import LocalProxy
from flask import Flask, g, current_app, Blueprint
from flask.helpers import send_from_directory
from jinja2 import FileSystemLoader
import sqlite3


#from chill.resource import resource
#from chill.page import page

class ChillFlask(Flask):

    def send_root_file(self, filename):
        """
        Function used to send static files from the root of the domain.
        """
        cache_timeout = self.get_send_file_max_age(filename)
        return send_from_directory(self.config['ROOT_FOLDER'], filename,
                                   cache_timeout=cache_timeout)

    def send_media_file(self, filename):
        """
        Function used to send media files from the media folder to the browser.
        """
        cache_timeout = self.get_send_file_max_age(filename)
        return send_from_directory(self.config['MEDIA_FOLDER'], filename,
                                   cache_timeout=cache_timeout)

    def send_theme_file(self, filename):
        """
        Function used to send static theme files from the theme folder to the browser.
        """
        cache_timeout = self.get_send_file_max_age(filename)
        return send_from_directory(self.config['THEME_STATIC_FOLDER'], filename,
                                   cache_timeout=cache_timeout)

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

    app = ChillFlask('chill')

    if config:
        config_file = config if config[0] == os.sep else os.path.join(os.getcwd(), config)
        app.config.from_pyfile(config_file)
    app.config.update(kw)

    # TODO: fix conflict with page_uri
    root_folder = app.config.get('ROOT_FOLDER', None)
    if root_folder:
        if root_folder[0] != os.sep:
            root_folder = os.path.join(os.getcwd(), root_folder)

        app.config['ROOT_FOLDER'] = root_folder
        #root_path = '/' # See no need to have this be different
        if os.path.isdir( root_folder ):
            app.add_url_rule('/<path:filename>', view_func=app.send_root_file)

    media_folder = app.config.get('MEDIA_FOLDER', None)
    if media_folder:
        if media_folder[0] != os.sep:
            media_folder = os.path.join(os.getcwd(), media_folder)

        app.config['MEDIA_FOLDER'] = media_folder
        media_path = app.config.get('MEDIA_PATH', '/media/')
        if os.path.isdir( media_folder ) and media_path[0] == '/':
            app.add_url_rule('%s<path:filename>' % media_path, view_func=app.send_media_file)


    template_folder = app.config.get('THEME_TEMPLATE_FOLDER', app.template_folder)
    app.config['THEME_TEMPLATE_FOLDER'] = template_folder if template_folder[0] == os.sep else os.path.join(os.getcwd(), template_folder)

    selectsql_folder = app.config.get('THEME_SQL_FOLDER', 'selectsql')
    app.config['THEME_SQL_FOLDER'] = selectsql_folder if selectsql_folder[0] == os.sep else os.path.join(os.getcwd(), selectsql_folder)

    # Set the jinja2 template folder eith fallback for app.template_folder
    app.jinja_env.loader = FileSystemLoader( app.config.get('THEME_TEMPLATE_FOLDER') )

    @app.teardown_appcontext
    def teardown_db(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()


    # STATIC_URL='http://cdn.example.com/whatever/works/'
    @app.context_processor
    def inject_paths():
        """
        Inject the variables 'theme_static_path' and 'media_path' into the templates.

        Template variable will always have a trailing slash.

        """
        theme_static_path = app.config.get('THEME_STATIC_PATH', '/theme/')
        media_path = app.config.get('MEDIA_PATH', '/media/')
        #static_url = app.config.get('STATIC_URL', app.static_url_path)
        if not theme_static_path.endswith('/'):
            theme_static_path += '/'
        if not media_path.endswith('/'):
            media_path += '/'
        return dict(
            theme_static_path=theme_static_path,
            media_path=media_path
        )


    # register any blueprints here
    #app.logger.warning("Not registering resource blueprint")
    #app.register_blueprint(resource)

    from chill.public import PageView
    #app.logger.warning("Not registering page blueprint")
    page = Blueprint('public', __name__, static_folder=None, template_folder=None)

    theme_static_folder = app.config.get('THEME_STATIC_FOLDER', None)
    if theme_static_folder:
        if theme_static_folder[0] != os.sep:
            theme_static_folder = os.path.join(os.getcwd(), theme_static_folder)

        app.config['THEME_STATIC_FOLDER'] = theme_static_folder
        theme_static_path = app.config.get('THEME_STATIC_PATH', '/theme/')
        if os.path.isdir( theme_static_folder ) and theme_static_path[0] == '/':
            page.add_url_rule('%s<path:filename>' % theme_static_path, view_func=app.send_theme_file)

    page.add_url_rule('/', view_func=PageView.as_view('page'))
    page.add_url_rule('/index.html', view_func=PageView.as_view('index'))
    page.add_url_rule('/<path:uri>/', view_func=PageView.as_view('page_uri'))
    page.add_url_rule('/<path:uri>/index.html', view_func=PageView.as_view('uri_index'))
    app.register_blueprint(page, url_prefix=app.config.get('PUBLIC_URL_PREFIX', ''))

    return app
