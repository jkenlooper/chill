"""Chill - Database driven web application framework in Flask

Usage: chill run [--config <file>]
       chill serve [--config <file>]
       chill freeze [--config <file>] [--urls <file>]
       chill operate [--config <file>]
       chill init
       chill migrate [--config <file>]
       chill --help
       chill --version

Options:
  --version         Display version
  -h --help         Show this screen.
  --config <file>   Set config file. [default: ./site.cfg]
  --urls <file>     A txt file with a url to freeze on each line

Subcommands:
    run     - Start the web server in the foreground. Don't use for production.
    serve   - Starts a daemon web server with Gevent.
    freeze  - Freeze the application by creating a static version of it.
    operate - Interface to do simple operations on the database.
    init    - Initialize the current directory with base starting files and database.
    migrate - Perform a database migration from one version to the next.

"""

import os

import sqlite3
from docopt import docopt
from flask_frozen import Freezer
from setuptools_scm import get_version

from chill.app import make_app, db
from database import fetch_query_string
from chill.database import (
        init_db,
        insert_node,
        insert_node_node,
        insert_route,
        insert_query,
        add_template_for_node,
        )
from chill.operate import operate_menu
from chill.migrations import migrate1

chill_version = get_version()

SITECFG = """
# The site.cfg file is used to configure a flask app.  Refer to the flask
# documentation for other configurations.  The below are used specifically by
# Chill.

# Set the HOST to 0.0.0.0 for being an externally visible server.
#HOST = '127.0.0.1'
#PORT = 5000

# The sqlite database file
CHILL_DATABASE_URI = "db"

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
    args = docopt(__doc__, version=chill_version)
    # parse args and pass to run, server, etc.
    if args['init']:
        init()

    if args['run']:
        run(args['--config'])

    if args['operate']:
        operate(args['--config'])

    if args['migrate']:
        migrate(args['--config'])

    if args['serve']:
        serve(args['--config'])

    if args['freeze']:
        freeze(args['--config'], urls_file=args.get('--urls', None))

if __name__ == '__main__':
    main()

def init():
    "Initialize the current directory with base starting files and database."

    if not os.path.exists('site.cfg'):
        print "Creating a default site.cfg"
        f = open('site.cfg', 'w')
        f.write(SITECFG)
        f.close()

    try:
        os.mkdir('queries')
    except OSError:
        pass

    try:
        os.mkdir('templates')
    except OSError:
        pass

    htmlfile = os.path.join('templates', 'homepage.html')
    if not os.path.exists(htmlfile):
        f = open(htmlfile, 'w')
        f.write("""
<!doctype html>
<html>
    <head>
        <title>Chill</title>
    </head>
    <body>
        <p>{{ homepage_content }}</p>
    </body>
</html>
        """)
        f.close()

    app = make_app(config='site.cfg', DEBUG=True)

    with app.app_context():
        print "initializing database"
        init_db()

        homepage = insert_node(name='homepage', value=None)
        insert_route(path='/', node_id=homepage)
        insert_query(name='select_link_node_from_node.sql', node_id=homepage)

        add_template_for_node('homepage.html', homepage)

        homepage_content = insert_node(name='homepage_content', value="Cascading, Highly Irrelevant, Lost Llamas")
        insert_node_node(node_id=homepage, target_node_id=homepage_content)

        db.commit()

def operate(config):
    "Interface to do simple operations on the database."

    app = make_app(config=config)

    print "Operate Mode"
    with app.app_context():
        operate_menu()

def migrate(config):
    "Migrate the database from a previous version to a new one."

    app = make_app(config=config)

    with app.app_context():
        migrate1()

# bin/run
def run(config):
    "Start the web server in the foreground. Don't use for production."
    app = make_app(config=config)

    app.run(
            host=app.config.get("HOST", '127.0.0.1'),
            port=app.config.get("PORT", 5000),
            use_reloader=True,
            )

# bin/serve
def serve(config):
    "Serve the app with Gevent"
    from gevent.wsgi import WSGIServer

    app = make_app(config=config)

    host = app.config.get("HOST", '127.0.0.1')
    port = app.config.get("PORT", 5000)
    http_server = WSGIServer((host, port), app)
    http_server.serve_forever()


# bin/freeze
def freeze(config, urls_file=None):
    """Freeze the application by creating a static version of it."""
    if urls_file:
        app = make_app(config=config, URLS_FILE=urls_file)
    else:
        app = make_app(config=config)
    app.logger.debug('freezing app to directory: %s' % app.config['FREEZER_DESTINATION'])
    freezer = Freezer(app)


    #@freezer.register_generator
    #def index_page():
    #    for (dirpath, dirnames, filenames) in os.walk(app.config['DATA_PATH'], topdown=True):
    #        start = len(os.path.commonprefix((app.config['DATA_PATH'], dirpath)))
    #        relative_path = dirpath[start+1:]
    #        for dirname in dirnames:
    #            yield ('page.index_page', {'uri': os.path.join(relative_path, dirname)})

    #@freezer.register_generator
    #def page_uri():
    #    # uri_index will be used so just avoid showing a warning
    #    return [
    #            ('public.page_uri', {'uri': ''}),
    #            ]
    @freezer.register_generator
    def uri_index():
        def cleanup_url(url):
            url = url.strip()
            if url.startswith('/'):
                if url.endswith('/index.html'):
                    return url
                elif url.endswith('/'):
                    url = url.strip('/')
                    if len(url) == 0:
                        return ('public.index', {})
                    return ('public.uri_index', {'uri': url})

        c = db.cursor()
        try:
            result = c.execute(fetch_query_string('select_paths_to_freeze.sql')).fetchall()
        except sqlite3.DatabaseError as err:
            app.logger.error("DatabaseError: %s", err)
            return []
        urls = filter(None, map(lambda x:cleanup_url(x[0]), result))

        urls_file = app.config.get('URLS_FILE', None)
        if urls_file:
            urls_file = urls_file if urls_file[0] == os.sep else os.path.join(os.getcwd(), urls_file)
            f = open(urls_file, 'r')
            urls.extend(filter(None, map(cleanup_url, f.readlines())))
            f.close()

        return urls


    @freezer.register_generator
    def send_root_file():
        root_folder = app.config.get('ROOT_FOLDER', None)
        if root_folder and os.path.isdir( root_folder ):
            for (dirpath, dirnames, filenames) in os.walk(root_folder, topdown=True):
                start = len(os.path.commonprefix((root_folder, dirpath)))
                relative_path = dirpath[start+1:]
                for filename in filenames:
                    yield ('send_root_file', {
                            'filename': os.path.join(relative_path, filename)
                            })

    @freezer.register_generator
    def send_media_file():
        media_folder = app.config.get('MEDIA_FOLDER', None)
        media_path = app.config.get('MEDIA_PATH', '/media/')
        freeze_all_files = app.config.get('MEDIA_FREEZE_ALL', False)
        if media_folder and freeze_all_files and os.path.isdir( media_folder ) and media_path[0] == '/':
            for (dirpath, dirnames, filenames) in os.walk(media_folder, topdown=True):
                start = len(os.path.commonprefix((media_folder, dirpath)))
                relative_path = dirpath[start+1:]
                for filename in filenames:
                    yield ('send_media_file', {
                            'filename': os.path.join(relative_path, filename)
                            })

    @freezer.register_generator
    def send_theme_file():
        theme_static_folder = app.config.get('THEME_STATIC_FOLDER', None)
        theme_static_path = app.config.get('THEME_STATIC_PATH', '/theme/')
        if theme_static_folder and os.path.isdir( theme_static_folder ) and theme_static_path[0] == '/':
            for (dirpath, dirnames, filenames) in os.walk(theme_static_folder, topdown=True):
                start = len(os.path.commonprefix((theme_static_folder, dirpath)))
                relative_path = dirpath[start+1:]
                for filename in filenames:
                    yield ('send_theme_file', {
                            'filename': os.path.join(relative_path, filename)
                            })


    freezer.freeze()
