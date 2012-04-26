import os.path

from flask import Flask
from pystache.context import Context

class _DefaultSettings(object):
    """
    Default settings for the Flask app.  These are overridden by what's in the
    buildout.cfg.
    These settings will be used when running the tests.
    """
    SECRET_KEY = 'development key' # set in buildout.cfg
    DEBUG = True # set in buildout.cfg
    THEME_PATH = os.path.join(os.path.dirname(__file__), 'themes')
    DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')


# create the application
app = Flask(__name__)
app.config.from_object(_DefaultSettings)
del _DefaultSettings

# init the views...
import page

def init_db(db_name=None):
    """Create the database tables."""

def build_context_data():
    app.data = {}
    for (dirpath, dirnames, filenames) in os.walk(app.config['DATA_PATH'], topdown=True):
        start = len(os.path.commonprefix((app.config['DATA_PATH'], dirpath)))
        relative_path = dirpath[start+1:]
        app.logger.debug(relative_path)
        d = {}
        for f in filenames: #filenames here are considered page fragments
            file_path = os.path.join(dirpath, f)
            (filename, ext) = os.path.splitext(f)
            if ext in ('.html', '.htm', '.txt'):
                h = open(file_path, 'r')
                d[filename] = h.read()


        ctx = Context(d)
        ctx_list = []
        #parent_pages = os.path.dirname(relative_path).split('/')
        parent_page = os.path.dirname(relative_path)
        if parent_page != '':
            ctx_list.insert(0, app.data[parent_page])
            #parent_page = os.path.dirname(parent_page)
        ctx_list.append(ctx)
        ctx_with_parent = Context.create(*ctx_list)
        app.data[relative_path] = ctx_with_parent

build_context_data()


