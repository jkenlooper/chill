from __future__ import absolute_import
from builtins import str, bytes
import os
import time
import sqlite3

from werkzeug.local import LocalProxy
from flask import Flask, g, current_app, Blueprint, Markup
from flask.helpers import send_from_directory
from flaskext.markdown import Markdown
from jinja2 import FileSystemLoader
from .cache import cache
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy import event
from babel import dates

from . import shortcodes

# from chill.resource import resource
# from chill.page import page


class ChillFlask(Flask):
    def send_root_file(self, filename):
        """
        Function used to send static files from the root of the domain.
        """
        cache_timeout = self.get_send_file_max_age(filename)
        return send_from_directory(
            self.config["ROOT_FOLDER"], filename, cache_timeout=cache_timeout
        )

    def send_media_file(self, filename):
        """
        Function used to send media files from the media folder to the browser.
        """
        cache_timeout = self.get_send_file_max_age(filename)
        return send_from_directory(
            self.config["MEDIA_FOLDER"], filename, cache_timeout=cache_timeout
        )

    def send_theme_file(self, filename):
        """
        Function used to send static theme files from the theme folder to the browser.
        """
        cache_timeout = self.get_send_file_max_age(filename)
        return send_from_directory(
            self.config["THEME_STATIC_FOLDER"], filename, cache_timeout=cache_timeout
        )


def connect_to_database():
    """
    Return the engine. Echo all sql statements if in DEBUG mode.
    """
    def sqlite_readonly_connect():

        db_file = current_app.config.get("CHILL_DATABASE_URI")[len('sqlite:///'):]
        if db_file and not db_file.startswith(':'):
            # Open the database connection in read only mode
            return sqlite3.connect(
                "file:{}?mode=ro".format(db_file), uri=True
            )
        else:
            return sqlite3.connect(current_app.config.get("CHILL_DATABASE_URI"))

    if current_app.config.get("database_readonly") and current_app.config.get("is_sqlite_database"):
        return create_engine(current_app.config["CHILL_DATABASE_URI"], creator=sqlite_readonly_connect)
    else:
        return create_engine(current_app.config["CHILL_DATABASE_URI"])


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = connect_to_database()
        if str(db.url).startswith("sqlite://"):
            # Enable foreign key support so 'on update' and 'on delete' actions
            # will apply. This needs to be set for each db connection.
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

    return db


db = LocalProxy(get_db)


def multiple_directory_files_loader(*args):
    """
    Loads all the files in each directory as values in a dict with the key
    being the relative file path of the directory.  Updates the value if
    subsequent file paths are the same.
    """
    d = dict()

    def load_files(folder):
        for (dirpath, dirnames, filenames) in os.walk(folder):
            for f in filenames:
                filepath = os.path.join(dirpath, f)
                with open(filepath, "r") as f:
                    key = filepath[len(os.path.commonprefix([root, filepath])) + 1 :]
                    d[key] = f.read()
            for foldername in dirnames:
                load_files(os.path.join(dirpath, foldername))

    for root in args:
        load_files(root)
    return d


def make_app(config=None, database_readonly=False, **kw):
    "factory to create the app"

    app = ChillFlask("chill")

    if config:
        config_file = (
            config if config[0] == os.sep else os.path.join(os.getcwd(), config)
        )
        app.config.from_pyfile(config_file)
    app.config.update(kw, database_readonly=database_readonly)
    is_sqlite_database = str(app.config.get("CHILL_DATABASE_URI")).startswith("sqlite://")
    app.config["is_sqlite_database"] = is_sqlite_database

    cache.init_app(app)

    # Set the freezer destination path to be absolute if needed.
    freeze_folder = app.config.get("FREEZER_DESTINATION", None)
    if freeze_folder:
        if freeze_folder[0] != os.sep:
            freeze_folder = os.path.join(os.getcwd(), freeze_folder)

        app.config["FREEZER_DESTINATION"] = freeze_folder

    # TODO: fix conflict with page_uri
    root_folder = app.config.get("ROOT_FOLDER", None)
    if root_folder:
        if root_folder[0] != os.sep:
            root_folder = os.path.join(os.getcwd(), root_folder)

        app.config["ROOT_FOLDER"] = root_folder
        # root_path = '/' # See no need to have this be different
        if os.path.isdir(root_folder):
            app.add_url_rule("/<path:filename>", view_func=app.send_root_file)

    media_folder = app.config.get("MEDIA_FOLDER", None)
    if media_folder:
        if media_folder[0] != os.sep:
            media_folder = os.path.join(os.getcwd(), media_folder)

        app.config["MEDIA_FOLDER"] = media_folder
        media_path = app.config.get("MEDIA_PATH", "/media/")
        if os.path.isdir(media_folder) and media_path[0] == "/":
            app.add_url_rule(
                "%s<path:filename>" % media_path, view_func=app.send_media_file
            )

    document_folder = app.config.get("DOCUMENT_FOLDER", None)
    if document_folder:
        if document_folder[0] != os.sep:
            document_folder = os.path.join(os.getcwd(), document_folder)
        app.config["DOCUMENT_FOLDER"] = document_folder

    template_folder = app.config.get("THEME_TEMPLATE_FOLDER", app.template_folder)
    app.config["THEME_TEMPLATE_FOLDER"] = (
        template_folder
        if template_folder[0] == os.sep
        else os.path.join(os.getcwd(), template_folder)
    )

    queries_folder = app.config.get("THEME_SQL_FOLDER", "queries")
    app.config["THEME_SQL_FOLDER"] = (
        queries_folder
        if queries_folder[0] == os.sep
        else os.path.join(os.getcwd(), queries_folder)
    )

    chill_queries_folder = os.path.join(os.path.dirname(__file__), "queries")
    user_queries_folder = app.config.get("THEME_SQL_FOLDER")
    app.queries = multiple_directory_files_loader(
        chill_queries_folder, user_queries_folder
    )

    # Set the jinja2 template folder eith fallback for app.template_folder
    app.jinja_env.loader = FileSystemLoader(app.config.get("THEME_TEMPLATE_FOLDER"))

    @app.teardown_appcontext
    def teardown_db(exception):
        db = getattr(g, "_database", None)
        if db is not None:
            db.dispose()

    # STATIC_URL='http://cdn.example.com/whatever/works/'
    @app.context_processor
    def inject_paths():
        """
        Inject the variables 'theme_static_path' and 'media_path' into the templates.

        Template variable will always have a trailing slash.

        """
        theme_static_path = app.config.get("THEME_STATIC_PATH", "/theme/")
        media_path = app.config.get("MEDIA_PATH", "/media/")
        # static_url = app.config.get('STATIC_URL', app.static_url_path)
        if not theme_static_path.endswith("/"):
            theme_static_path += "/"
        if not media_path.endswith("/"):
            media_path += "/"
        return dict(theme_static_path=theme_static_path, media_path=media_path)

    @app.context_processor
    def inject_config():
        """
        Inject the config into the templates.
        """
        return dict(config=dict(app.config))

    @app.context_processor
    def inject_chill_vars():
        """
        Inject some useful variables for templates to use.
        """
        return {"chill_now": int(time.time())}

    @app.template_filter("datetime")
    def datetime(value, format="y-MM-dd HH:mm:ss"):
        "Date time filter that uses babel to format."
        return dates.format_datetime(value, format)

    @app.template_filter("timedelta")
    def timedelta(value):
        "time delta"
        return dates.format_timedelta(value)

    # Add the markdown filter for the templates
    md = Markdown(app)

    @app.template_filter("readfile")
    def readfile(filename):
        "A template filter to read files from the DOCUMENT_FOLDER"
        document_folder = app.config.get("DOCUMENT_FOLDER")
        if document_folder:
            # Restrict access to just the DOCUMENT_FOLDER.
            filepath = os.path.normpath(os.path.join(document_folder, filename))
            if os.path.commonprefix([document_folder, filepath]) != document_folder:
                app.logger.warn(
                    "The filepath: '{0}' is outside of the DOCUMENT_FOLDER".format(
                        filepath
                    )
                )
                return filename

            with open(os.path.join(document_folder, filename), "r") as f:
                # py2 return unicode str (not py3 compat)
                # content = f.read().decode('utf-8')

                # py3 (not py2 compat)
                # content = f.read()

                # py2 and py3 compat
                content = bytes(f.read(), "utf-8").decode("utf-8")
            return content

        app.logger.warn(
            "jinja2 filter 'readfile' can't find file: '{0}'".format(filename)
        )
        return filename

    # register any blueprints here
    # app.logger.warning("Not registering resource blueprint")
    # app.register_blueprint(resource)

    from chill.public import PageView

    # app.logger.warning("Not registering page blueprint")
    page = Blueprint("public", __name__, static_folder=None, template_folder=None)

    # TODO: The shortcode start and end is rather custom.  Make this
    # configurable or no?
    # The defualt from the shortcodes.py is '[%' and '%]'.
    app.parser = shortcodes.Parser(start="[chill", end="]", esc="\\")

    @app.template_filter("shortcodes")
    def shortcodes_filter(content):
        "Parse the rendered string for chill shortcodes"
        return Markup(app.parser.parse(content))

    theme_static_folder = app.config.get("THEME_STATIC_FOLDER", None)
    if theme_static_folder:
        if theme_static_folder[0] != os.sep:
            theme_static_folder = os.path.join(os.getcwd(), theme_static_folder)

        app.config["THEME_STATIC_FOLDER"] = theme_static_folder
        theme_static_path = app.config.get("THEME_STATIC_PATH", "/theme/")
        if os.path.isdir(theme_static_folder) and theme_static_path[0] == "/":
            app.add_url_rule(
                "%s<path:filename>" % theme_static_path, view_func=app.send_theme_file
            )

    page.add_url_rule("/", view_func=PageView.as_view("page"))
    page.add_url_rule("/index.html", view_func=PageView.as_view("index"))
    page.add_url_rule("/<path:uri>/", view_func=PageView.as_view("page_uri"))
    page.add_url_rule("/<path:uri>/index.html", view_func=PageView.as_view("uri_index"))
    app.register_blueprint(page, url_prefix=app.config.get("PUBLIC_URL_PREFIX", ""))

    return app
