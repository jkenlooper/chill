#chill - Simple Frozen website management
#Copyright (C) 2012  Jake Hickenlooper
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
