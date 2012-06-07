"""Chill scripts"""
import os

from flask_frozen import Freezer

from chill.app import make_app

# bin/run
def run(config, debug=False):
    "Run app in foreground. don't use for production"
    app = make_app(config=config, debug=debug)

    app.run(
            host=app.config.get("HOST", '127.0.0.1'),
            port=app.config.get("PORT", 5000),
            use_reloader=True,
            )

# bin/freeze
def freeze(config, debug=False):
    """Freeze the application by creating a static version of it."""
    app = make_app(config=config, debug=debug)
    app.logger.debug('freezing app to directory: %s' % app.config['FREEZER_DESTINATION'])
    freezer = Freezer(app)

    @freezer.register_generator
    def index_page():
        for (dirpath, dirnames, filenames) in os.walk(app.config['DATA_PATH'], topdown=True):
            start = len(os.path.commonprefix((app.config['DATA_PATH'], dirpath)))
            relative_path = dirpath[start+1:]
            for dirname in dirnames:
                yield ('page.index_page', {'uri': os.path.join(relative_path, dirname)})

    @freezer.register_generator
    def data_resource():
        for (dirpath, dirnames, filenames) in os.walk(app.config['DATA_PATH'], topdown=True):
            start = len(os.path.commonprefix((app.config['DATA_PATH'], dirpath)))
            relative_path = dirpath[start+1:]
            for filename in filenames:
                (name, ext) = os.path.splitext(filename)
                if ext[1:]:
                    yield ('resource.data_resource', {
                            'uri': os.path.join(relative_path, name),
                            'ext': ext[1:]
                            })

    @freezer.register_generator
    def themes_resource():
        for (dirpath, dirnames, filenames) in os.walk(app.config['THEME_PATH'], topdown=True):
            start = len(os.path.commonprefix((app.config['THEME_PATH'], dirpath)))
            relative_path = dirpath[start+1:]
            for filename in filenames:
                (name, ext) = os.path.splitext(filename)
                if ext[1:]:
                    yield ('resource.themes_resource', {
                            'uri': os.path.join(relative_path, name),
                            'ext': ext[1:]
                            })


    freezer.freeze()
