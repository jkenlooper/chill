"""Chill - Database driven web application framework in Flask

Usage: chill run --config <file>
       chill serve --config <file>
       chill freeze --config <file> [--urls <file>]

Options:
  -h --help         Show this screen.
  --config <file>   Set config file.
  --urls <file>     A txt file with a url to freeze on each line

"""
import os

import sqlite3
from docopt import docopt
from flask_frozen import Freezer

from chill.app import make_app, db
from database import fetch_selectsql_string

def main():
    ""
    args = docopt(__doc__)
    # parse args and pass to run, server, etc.
    if args['run']:
        run(args['--config'])

    if args['serve']:
        serve(args['--config'])

    if args['freeze']:
        freeze(args['--config'], urls_file=args.get('--urls', None))

if __name__ == '__main__':
    main()

# bin/run
def run(config, debug=False):
    "Run app in foreground. don't use for production"
    app = make_app(config=config, debug=debug)

    app.run(
            host=app.config.get("HOST", '127.0.0.1'),
            port=app.config.get("PORT", 5000),
            use_reloader=True,
            )

# bin/serve
def serve(config, debug=False):
    "Serve the app with Gevent"
    from gevent.wsgi import WSGIServer

    app = make_app(config=config, debug=debug)

    host = app.config.get("HOST", '127.0.0.1')
    port = app.config.get("PORT", 5000)
    http_server = WSGIServer((host, port), app)
    http_server.serve_forever()


# bin/freeze
def freeze(config, debug=False, urls_file=None):
    """Freeze the application by creating a static version of it."""
    if urls_file:
        app = make_app(config=config, debug=debug, URLS_FILE=urls_file)
    else:
        app = make_app(config=config, debug=debug)
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
            result = c.execute(fetch_selectsql_string('select_paths_to_freeze.sql')).fetchall()
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
        media_folder = app.config['MEDIA_FOLDER']
        media_path = app.config.get('MEDIA_PATH', '/media/')
        freeze_all_files = app.config.get('MEDIA_FREEZE_ALL', False)
        if freeze_all_files and os.path.isdir( media_folder ) and media_path[0] == '/':
            for (dirpath, dirnames, filenames) in os.walk(media_folder, topdown=True):
                start = len(os.path.commonprefix((media_folder, dirpath)))
                relative_path = dirpath[start+1:]
                for filename in filenames:
                    yield ('send_media_file', {
                            'filename': os.path.join(relative_path, filename)
                            })

    @freezer.register_generator
    def send_theme_file():
        theme_static_folder = app.config['THEME_STATIC_FOLDER']
        theme_static_path = app.config.get('THEME_STATIC_PATH', '/theme/')
        if os.path.isdir( theme_static_folder ) and theme_static_path[0] == '/':
            for (dirpath, dirnames, filenames) in os.walk(theme_static_folder, topdown=True):
                start = len(os.path.commonprefix((theme_static_folder, dirpath)))
                relative_path = dirpath[start+1:]
                for filename in filenames:
                    yield ('send_theme_file', {
                            'filename': os.path.join(relative_path, filename)
                            })


    freezer.freeze()
