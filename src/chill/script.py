"""Chill - Database driven web application framework in Flask

Usage: chill run [--config <file>] [--readonly]
       chill serve [--config <file>] [--readonly]
       chill freeze [--config <file>] [--urls <file>]
       chill operate [--config <file>]
       chill init
       chill initdb [--config <file>]
       chill load [--config <file>] [--yaml <file>]
       chill dump [--config <file>] [--yaml <file>]
       chill migrate [--config <file>]
       chill --help
       chill --version

Options:
  --version         Display version
  -h --help         Show this screen.
  --config <file>   Set config file. [default: ./site.cfg]
  --readonly        Set sqlite database connection to be read only
  --urls <file>     A txt file with a url to freeze on each line
  --yaml <file>     A yaml file with ChillNode objects [default: ./chill-data.yaml]

Subcommands:
    run     - Start the web server in the foreground. Don't use for production.
    serve   - Starts a daemon web server with Gevent.
    freeze  - Freeze the application by creating a static version of it.
    operate - Interface to do simple operations on the database.
    init    - Initialize the current directory with base starting files and database.
    initdb  - Initialize Chill database tables only.
    load    - Load a yaml file that has ChillNode objects into the database.
    dump    - Create a yaml file of ChillNode objects from the database.
    migrate - Perform a database migration from one version to the next.

"""
from __future__ import print_function

from builtins import map
import os
import subprocess
import sqlite3

from sqlalchemy.exc import DatabaseError, StatementError
from sqlalchemy.sql import text
from docopt import docopt
from flask_frozen import Freezer

from chill.app import make_app, db
from chill.database import (
    init_db,
    insert_node,
    insert_node_node,
    insert_route,
    insert_query,
    add_template_for_node,
    fetch_query_string,
)
from chill.operate import operate_menu
from chill.migrations import migrate1
from chill.yaml_chill_node import load_yaml, dump_yaml
from chill._version import __version__

SITECFG = """
# The site.cfg file is used to configure a flask app.  Refer to the flask
# documentation for other configurations.  The below are used specifically by
# Chill.

# Set the HOST to 0.0.0.0 for being an externally visible server.
#HOST = '127.0.0.1'
#PORT = 5000

# Valid SQLite URL forms are:
#   sqlite:///:memory: (or, sqlite://)
#   sqlite:///relative/path/to/file.db
#   sqlite:////absolute/path/to/file.db
# http://docs.sqlalchemy.org/en/latest/core/engines.html
CHILL_DATABASE_URI = "sqlite:///db"

# Set the sqlite journal_mode
# https://sqlite.org/pragma.html#pragma_journal_mode
# Leave blank to not change
SQLITE_JOURNAL_MODE = ""

# If using the ROOT_FOLDER then you will need to set the PUBLIC_URL_PREFIX to
# something other than '/'.
#PUBLIC_URL_PREFIX = "/"

# If setting the ROOT_FOLDER:
#PUBLIC_URL_PREFIX = "/site"

# The ROOT_FOLDER is used to send static files from the '/' route.  This will
# conflict with the default value for PUBLIC_URL_PREFIX. Any file or directory
# within the ROOT_FOLDER will be accessible from '/'.  The default is not
# having anything set.
#ROOT_FOLDER = "root"

# The document folder is an optional way of storing content outside of the
# database.  It is used with the custom filter 'readfile' which can read the
# file from the document folder into the template.  If it is a Markdown file
# you can also use another filter to parse the markdown into HTML with the
# 'markdown' filter. For example:
# {{ 'llamas-are-cool.md'|readfile|markdown }}
# DOCUMENT_FOLDER = "documents"

# The media folder is used to send static files that are not related to the
# 'theme' of a site.  This usually includes images and videos that are better
# served from the file system instead of the database. The default is not
# having this set to anything.
#MEDIA_FOLDER = "media"

# The media path is where the files in the media folder will be accessible.  In
# templates you can use the custom variable: 'media_path' which will have this
# value.
# {{ media_path }}llama.jpg
# or:
# {{ url_for('send_media_file', filename='llama.jpg') }}
#MEDIA_PATH = "/media/"

# When creating a stand-alone static website the files in the MEDIA_FOLDER are
# only included if they are linked to from a page.  Set this to True if all the
# files in the media folder should be included in the FREEZER_DESTINATION.
#MEDIA_FREEZE_ALL = False

# The theme is where all the front end resources like css, js, graphics and
# such that make up the theme of a website. The THEME_STATIC_FOLDER is where
# these files are located and by default nothing is set here.
#THEME_STATIC_FOLDER = "static"

# Set a THEME_STATIC_PATH for routing the theme static files with.  It's useful
# to set a version number within this path to easily do cache-busting.  In your
# templates you can use the custom variable:
# {{ theme_static_path }}llama.css
# or:
# {{ url_for('send_theme_file', filename='llama.css') }}
# to get the url to a file in the theme static folder.
#THEME_STATIC_PATH = "/theme/v0.0.1/"

# Where the jinja2 templates for the site are located.  Will default to the app
# template_folder if not set.
THEME_TEMPLATE_FOLDER = "templates"

# Where all the custom SQL queries and such are located.  Chill uses a few
# built-in ones and they can be overridden by adding a file with the same name
# in here. To do much of anything with Chill you will need to add some custom
# SQL queries and such to load data into your templates.
#THEME_SQL_FOLDER = "queries"

# Helpful to have this set to True if you want to fix stuff.
#DEBUG=True

# Caching with Flask-Cache
CACHE_NO_NULL_WARNING = True
CACHE_TYPE = "null"
#CACHE_TYPE = "simple"
#CACHE_TYPE = "filesystem"

# For creating a stand-alone static website that you can upload without
# requiring an app to run it. This will use Frozen-Flask.
# The path to the static/frozen website will be put.
#FREEZER_DESTINATION = "/home/something/path/to/frozen"
"""


def main():
    ""
    args = docopt(__doc__, version=__version__)
    # parse args and pass to run, server, etc.
    if args["init"]:
        init()

    if args["initdb"]:
        initdb(args["--config"])

    if args["run"]:
        run(args["--config"], database_readonly=args.get("--readonly", False))

    if args["operate"]:
        operate(args["--config"])

    if args["load"]:
        load(args["--config"], yaml_file=args.get("--yaml", "chill-data.yaml"))

    if args["dump"]:
        dump(args["--config"], yaml_file=args.get("--yaml", "chill-data.yaml"))

    if args["migrate"]:
        migrate(args["--config"])

    if args["serve"]:
        serve(args["--config"], database_readonly=args.get("--readonly", False))

    if args["freeze"]:
        freeze(args["--config"], urls_file=args.get("--urls", None))


if __name__ == "__main__":
    main()


def initdb(config):
    "Initialize Chill database tables only."

    app = make_app(config=config)

    with app.app_context():
        app.logger.info("initializing database")
        init_db()


def init():
    "Initialize the current directory with base starting files and database."

    if not os.path.exists("site.cfg"):
        f = open("site.cfg", "w")
        f.write(SITECFG)
        f.close()

    try:
        os.mkdir("queries")
    except OSError:
        pass

    try:
        os.mkdir("templates")
    except OSError:
        pass

    htmlfile = os.path.join("templates", "homepage.html")
    if not os.path.exists(htmlfile):
        f = open(htmlfile, "w")
        f.write(
            """
<!doctype html>
<html>
    <head>
        <title>Chill</title>
    </head>
    <body>
        <p>{{ homepage_content }}</p>
    </body>
</html>
        """
        )
        f.close()

    app = make_app(config="site.cfg", DEBUG=True)

    with app.app_context():
        app.logger.info("initializing database")
        init_db()

        homepage = insert_node(name="homepage", value=None)
        insert_route(path="/", node_id=homepage)
        insert_query(name="select_link_node_from_node.sql", node_id=homepage)

        add_template_for_node("homepage.html", homepage)

        homepage_content = insert_node(
            name="homepage_content", value="Cascading, Highly Irrelevant, Lost Llamas"
        )
        insert_node_node(node_id=homepage, target_node_id=homepage_content)


def operate(config):
    "Interface to do simple operations on the database."

    app = make_app(config=config)

    print("Operate Mode")
    with app.app_context():
        operate_menu()


def load(config, yaml_file):
    "Load a yaml file that has ChillNode objects into the database."

    app = make_app(config=config)

    with app.app_context():
        load_yaml(yaml_file)


def dump(config, yaml_file):
    "Create a yaml file of ChillNode objects from the database."

    app = make_app(config=config)

    with app.app_context():
        dump_yaml(yaml_file)


def migrate(config):
    "Migrate the database from a previous version to a new one."

    app = make_app(config=config)

    with app.app_context():
        migrate1()

def set_sqlite_journal_mode(app):

    db_file = app.config.get("CHILL_DATABASE_URI")[len("sqlite:///"):]
    journal_mode = app.config.get("SQLITE_JOURNAL_MODE")
    if not journal_mode or not isinstance(journal_mode, str):
        return

    if not journal_mode.lower() in ("delete", "truncate" , "persist" , "memory" , "wal" , "off"):
        return

    if db_file and not db_file.startswith(":"):
        # Need to set Write-Ahead Logging so multiple apps can work with the db
        # concurrently.  https://sqlite.org/wal.html
        app.logger.info("set journal mode to '{}' on db file: {}".format(journal_mode, db_file))
        subprocess.run(["sqlite3", db_file, "pragma journal_mode={journal_mode}".format(journal_mode=journal_mode)])

# bin/run
def run(config, database_readonly=False):
    "Start the web server in the foreground. Don't use for production."
    app = make_app(config=config, database_readonly=database_readonly)

    set_sqlite_journal_mode(app)

    app.run(
        host=app.config.get("HOST", "127.0.0.1"),
        port=app.config.get("PORT", 5000),
        use_reloader=True,
    )


# bin/serve
def serve(config, database_readonly=False):
    "Serve the app with Gevent"
    from gevent import pywsgi, signal

    app = make_app(config=config, database_readonly=database_readonly)

    set_sqlite_journal_mode(app)

    host = app.config.get("HOST", "127.0.0.1")
    port = app.config.get("PORT", 5000)
    app.logger.info("serving on {host}:{port}".format(**locals()))
    http_server = pywsgi.WSGIServer((host, port), app)
    def shutdown():
        app.logger.info("Stopping Chill app")
        http_server.stop(timeout=10)
        exit(signal.SIGTERM)

    signal(signal.SIGTERM, shutdown)
    signal(signal.SIGINT, shutdown)
    http_server.serve_forever(stop_timeout=10)


# bin/freeze
def freeze(config, urls_file=None):
    """Freeze the application by creating a static version of it."""
    if urls_file:
        app = make_app(config=config, URLS_FILE=urls_file)
    else:
        app = make_app(config=config)
    app.logger.info("freezing app to directory: %s" % app.config["FREEZER_DESTINATION"])
    freezer = Freezer(app)

    # @freezer.register_generator
    # def index_page():
    #    for (dirpath, dirnames, filenames) in os.walk(app.config['DATA_PATH'], topdown=True):
    #        start = len(os.path.commonprefix((app.config['DATA_PATH'], dirpath)))
    #        relative_path = dirpath[start+1:]
    #        for dirname in dirnames:
    #            yield ('page.index_page', {'uri': os.path.join(relative_path, dirname)})

    # @freezer.register_generator
    # def page_uri():
    #    # uri_index will be used so just avoid showing a warning
    #    return [
    #            ('public.page_uri', {'uri': ''}),
    #            ]
    @freezer.register_generator
    def uri_index():
        def cleanup_url(url):
            url = url.strip()
            if url.startswith("/"):
                if url.endswith("/index.html"):
                    return url
                elif url.endswith("/"):
                    url = url.strip("/")
                    if len(url) == 0:
                        return ("public.index", {})
                    return ("public.uri_index", {"uri": url})

        try:
            result = db.execute(
                text(fetch_query_string("select_paths_to_freeze.sql"))
            ).fetchall()
        except (DatabaseError, StatementError) as err:
            app.logger.error("DatabaseError: %s", err)
            return []
        urls = [_f for _f in [cleanup_url(x[0]) for x in result] if _f]

        urls_file = app.config.get("URLS_FILE", None)
        if urls_file:
            urls_file = (
                urls_file
                if urls_file[0] == os.sep
                else os.path.join(os.getcwd(), urls_file)
            )
            f = open(urls_file, "r")
            urls.extend([_f for _f in map(cleanup_url, f.readlines()) if _f])
            f.close()

        return urls

    @freezer.register_generator
    def send_root_file():
        root_folder = app.config.get("ROOT_FOLDER", None)
        if root_folder and os.path.isdir(root_folder):
            for (dirpath, dirnames, filenames) in os.walk(root_folder, topdown=True):
                start = len(os.path.commonprefix((root_folder, dirpath)))
                relative_path = dirpath[start + 1 :]
                for filename in filenames:
                    yield (
                        "send_root_file",
                        {"filename": os.path.join(relative_path, filename)},
                    )

    @freezer.register_generator
    def send_media_file():
        media_folder = app.config.get("MEDIA_FOLDER", None)
        media_path = app.config.get("MEDIA_PATH", "/media/")
        freeze_all_files = app.config.get("MEDIA_FREEZE_ALL", False)
        if (
            media_folder
            and freeze_all_files
            and os.path.isdir(media_folder)
            and media_path[0] == "/"
        ):
            for (dirpath, dirnames, filenames) in os.walk(media_folder, topdown=True):
                start = len(os.path.commonprefix((media_folder, dirpath)))
                relative_path = dirpath[start + 1 :]
                for filename in filenames:
                    yield (
                        "send_media_file",
                        {"filename": os.path.join(relative_path, filename)},
                    )

    @freezer.register_generator
    def send_theme_file():
        theme_static_folder = app.config.get("THEME_STATIC_FOLDER", None)
        theme_static_path = app.config.get("THEME_STATIC_PATH", "/theme/")
        if (
            theme_static_folder
            and os.path.isdir(theme_static_folder)
            and theme_static_path[0] == "/"
        ):
            for (dirpath, dirnames, filenames) in os.walk(
                theme_static_folder, topdown=True
            ):
                start = len(os.path.commonprefix((theme_static_folder, dirpath)))
                relative_path = dirpath[start + 1 :]
                for filename in filenames:
                    yield (
                        "send_theme_file",
                        {"filename": os.path.join(relative_path, filename)},
                    )

    freezer.freeze()
