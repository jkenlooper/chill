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

from flask import Flask

from chill.resource import resource
from chill.page import page
from chill.tools import build_context_data

def make_app(config, debug=False):
    "factory to create the app"

    app = Flask(__name__)

    app.config.from_pyfile(config)
    app.debug = debug

    # register any blueprints here
    app.register_blueprint(resource)
    app.register_blueprint(page)

    build_context_data(app)

    return app
