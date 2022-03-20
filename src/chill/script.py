"""Chill - Database driven web application framework in Flask

Usage: chill run [--config <file>] [--readonly]
       chill serve [--config <file>] [--readonly]
       chill freeze [--config <file>] [--urls <file>]
       chill init
       chill initdb [--config <file>]
       chill dropdb [--config <file>]
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
    init    - Initialize the current directory with base starting files and database.
    initdb  - Initialize Chill database tables only.
    dropdb  - Deletes Chill database tables only.
    load    - Load a yaml file that has ChillNode objects into the database.
    dump    - Create a yaml file of ChillNode objects from the database.
    migrate - Perform a database migration from one version to the next.

"""
from gevent import monkey

monkey.patch_all()

import os
import subprocess
import sqlite3

from docopt import docopt
from flask_frozen import Freezer

from chill.app import make_app
from chill.database import (
    get_db,
    init_db,
    drop_db,
    insert_node,
    insert_node_node,
    insert_route,
    insert_query,
    add_template_for_node,
    fetch_query_string,
)
from chill.migrations import migrate1
from chill.yaml_chill_node import load_yaml, dump_yaml
from chill._version import __version__

SITECFG = """
from os import getenv
from os.path import isfile
import json

# The site.cfg file is used to configure a flask app.  Refer to the flask
# documentation for other configurations.  The below are used specifically by
# Chill.

# Set the HOST to 0.0.0.0 for being an externally visible server.
# Set the HOST to 127.0.0.1 for internal
HOST = getenv("CHILL_HOST", default="0.0.0.0")
PORT = int(getenv("CHILL_PORT", default="5000"))

# Optional if needing to freeze the site and absolute URLs are needed. See the
# FREEZER_BASE_URL setting below.
HOSTNAME = getenv("CHILL_HOSTNAME", default="localhost")

# Path to sqlite3 database file
CHILL_DATABASE_URI = getenv("CHILL_DATABASE_URI", default="db")

# Set the sqlite journal_mode
# https://sqlite.org/pragma.html#pragma_journal_mode
SQLITE_JOURNAL_MODE = getenv("CHILL_SQLITE_JOURNAL_MODE", default="wal")

# If using the ROOT_FOLDER then you will need to set the PUBLIC_URL_PREFIX to
# something other than '/'.
#PUBLIC_URL_PREFIX = getenv("CHILL_PUBLIC_URL_PREFIX", default="/")

# If setting the ROOT_FOLDER:
#PUBLIC_URL_PREFIX = getenv("CHILL_PUBLIC_URL_PREFIX", default="/site")

# The ROOT_FOLDER is used to send static files from the '/' route.  This will
# conflict with the default value for PUBLIC_URL_PREFIX. Any file or directory
# within the ROOT_FOLDER will be accessible from '/'.  The default is not
# having anything set.
#ROOT_FOLDER = getenv("CHILL_ROOT_FOLDER", default="root")

# The document folder is an optional way of storing content outside of the
# database.  It is used with the custom filter 'readfile' which can read the
# file from the document folder into the template.  If it is a Markdown file
# you can also use another filter to parse the markdown into HTML with the
# 'markdown' filter. For example:
# {{ 'llamas-are-cool.md'|readfile|markdown }}
#DOCUMENT_FOLDER = getenv("CHILL_DOCUMENT_FOLDER", default="documents")

# The media folder is used to send static files that are not related to the
# 'theme' of a site.  This usually includes images and videos that are better
# served from the file system instead of the database. The default is not
# having this set to anything.
#MEDIA_FOLDER = getenv("CHILL_MEDIA_FOLDER", default="media")

# The media path is where the files in the media folder will be accessible.  In
# templates you can use the custom variable: 'media_path' which will have this
# value.
# {{ media_path }}llama.jpg
# or:
# {{ url_for('send_media_file', filename='llama.jpg') }}
#MEDIA_PATH = getenv("CHILL_MEDIA_PATH", default="/media/")

# When creating a stand-alone static website the files in the MEDIA_FOLDER are
# only included if they are linked to from a page.  Set this to True if all the
# files in the media folder should be included in the FREEZER_DESTINATION.
#MEDIA_FREEZE_ALL = getenv("CHILL_MEDIA_FREEZE_ALL", default="False").lower() == "true"

# The theme is where all the front end resources like css, js, graphics and
# such that make up the theme of a website. The THEME_STATIC_FOLDER is where
# these files are located and by default nothing is set here.
#THEME_STATIC_FOLDER = getenv("CHILL_THEME_STATIC_FOLDER", default="static")

# Set a THEME_STATIC_PATH for routing the theme static files with.  It's useful
# to set a version number within this path to easily do cache-busting.  In your
# templates you can use the custom variable:
# {{ theme_static_path }}llama.css
# or:
# {{ url_for('send_theme_file', filename='llama.css') }}
# to get the url to a file in the theme static folder.

VERSION = "0"
PACKAGEJSON = {}
if isfile('package.json'):
    with open('package.json') as f:
        PACKAGEJSON = json.load(f)
        VERSION = PACKAGEJSON['version']
elif isfile('VERSION'):
    with open('VERSION') as f:
        VERSION = f.read().strip()

THEME_STATIC_PATH = getenv("CHILL_THEME_STATIC_PATH", default="/theme/{VERSION}/").format(**locals())

# Where the jinja2 templates for the site are located.  Will default to the app
# template_folder if not set.
THEME_TEMPLATE_FOLDER = getenv("CHILL_THEME_TEMPLATE_FOLDER", default="templates")

# Where all the custom SQL queries and such are located.  Chill uses a few
# built-in ones and they can be overridden by adding a file with the same name
# in here. To do much of anything with Chill you will need to add some custom
# SQL queries and such to load data into your templates.
#THEME_SQL_FOLDER = getenv("CHILL_THEME_SQL_FOLDER", default="queries")

# Helpful to have this set to True if you want to fix stuff.
#DEBUG = getenv("CHILL_DEBUG", default="False").lower() == "true"

# https://pythonhosted.org/Frozen-Flask/#configuration
# For creating a stand-alone static website that you can upload without
# requiring an app to run it. This will use Frozen-Flask.
# The path to the static/frozen website will be put.
FREEZER_DESTINATION = getenv("CHILL_FREEZER_DESTINATION", default="frozen")
#FREEZER_BASE_URL = getenv("CHILL_FREEZER_BASE_URL", default="//{HOSTNAME}/").format(**locals())
"""


def main():
    """"""
    args = docopt(__doc__, version=__version__)
    # parse args and pass to run, server, etc.
    if args["init"]:
        init()

    if args["initdb"]:
        initdb(args["--config"])

    if args["dropdb"]:
        dropdb(args["--config"])

    if args["run"]:
        run(args["--config"], database_readonly=args.get("--readonly", False))

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
    set_sqlite_journal_mode(app)

    with app.app_context():
        app.logger.info("initializing database")
        db = get_db()
        with db:
            init_db()


def dropdb(config):
    "Deletes Chill database tables only."

    app = make_app(config=config)
    set_sqlite_journal_mode(app)

    with app.app_context():
        app.logger.info("Removing Chill database tables: Chill, Node, Node_Node, Route, Query, Template.")
        db = get_db()
        with db:
            drop_db()


def init():
    "Initialize the current directory with base starting files and database."

    if not os.path.exists("site.cfg"):
        with open("site.cfg", "w") as f:
            f.write(SITECFG)

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
        with open(htmlfile, "w") as f:
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

    app = make_app(config="site.cfg", DEBUG=True)
    set_sqlite_journal_mode(app)

    with app.app_context():
        app.logger.info("initializing database")
        db = get_db()
        with db:
            init_db()

            homepage = insert_node(name="homepage", value=None)
            insert_route(path="/", node_id=homepage)
            insert_query(name="select_link_node_from_node.sql", node_id=homepage)

            add_template_for_node("homepage.html", homepage)

            homepage_content = insert_node(
                name="homepage_content", value="Cascading, Highly Irrelevant, Lost Llamas"
            )
            insert_node_node(node_id=homepage, target_node_id=homepage_content)


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

    db_file = app.config.get("CHILL_DATABASE_URI")
    journal_mode = app.config.get("SQLITE_JOURNAL_MODE")
    if not journal_mode or not isinstance(journal_mode, str):
        return

    if not journal_mode.lower() in (
        "delete",
        "truncate",
        "persist",
        "memory",
        "wal",
        "off",
    ):
        return

    if db_file and not db_file.startswith(":"):
        # Need to set Write-Ahead Logging so multiple apps can work with the db
        # concurrently.  https://sqlite.org/wal.html
        app.logger.info(
            "set journal mode to '{}' on db file: {}".format(journal_mode, db_file)
        )
        set_journal_mode_output = subprocess.run(
            [
                "sqlite3",
                db_file,
                "pragma journal_mode={journal_mode}".format(journal_mode=journal_mode),
            ],
            capture_output=True,
            check=True,
        )
        app.logger.info(" ".join(set_journal_mode_output.args))
        app.logger.info(set_journal_mode_output.stdout.decode())


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
    from gevent import pywsgi, signal_handler
    import signal

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

    signal_handler(signal.SIGTERM, shutdown)
    signal_handler(signal.SIGINT, shutdown)
    http_server.serve_forever(stop_timeout=10)


# bin/freeze
def freeze(config, urls_file=None):
    """Freeze the application by creating a static version of it."""
    if urls_file:
        app = make_app(config=config, URLS_FILE=urls_file, database_readonly=True)
    else:
        app = make_app(config=config, database_readonly=True)
    app.logger.info("freezing app to directory: %s" % app.config["FREEZER_DESTINATION"])
    freezer = Freezer(app)

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

        db = get_db()
        cur = db.cursor()
        try:
            result = cur.execute(
                fetch_query_string("select_paths_to_freeze.sql")
            ).fetchall()
        except (sqlite3.Error) as err:
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
            with open(urls_file, "r") as f:
                urls.extend([_f for _f in map(cleanup_url, f.readlines()) if _f])

        cur.close()

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
