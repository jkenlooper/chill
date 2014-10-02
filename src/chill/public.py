import os
import os.path

import sqlite3
from flask import abort, redirect, Blueprint, current_app, render_template, json
from flask.views import MethodView

from chill.app import db
from database import fetch_sql_string, fetch_selectsql_string, normalize
from api import render_node

encoder = json.JSONEncoder()

# The page blueprint has no static files or templates read from disk.
page = Blueprint('public', __name__, static_folder=None, template_folder=None)

class PageView(MethodView):
    """
    Handles access to a page.
    """

    def get(self, uri=''):
        """
        view a page
        """
        # check if page exists in data_path

        # a//b == a/b/ == a/./b == a/foo/../b
        # '' == '.'
        # Prepend the uri with '/' and normalize
        uri = os.path.normpath(os.path.join('/', uri))

        uri, ext = os.path.splitext(uri)
        #current_app.logger.debug('uri: "%s"' % uri)

        select_node_from_route = fetch_sql_string('select_node_from_route.sql')
       
        c = db.cursor()
        try:
            c.execute(select_node_from_route, {'uri':uri})
        except sqlite3.DatabaseError as err:
            current_app.logger.error("DatabaseError: %s", err)
            if uri == '/chill':
                # Show something for fun
                return "Cascading, Highly Irrelevant, Lost Llamas"

        result = c.fetchone()
        if result:

            rendered = render_node(result[2], result[1], result[0])
            if rendered:
                if not isinstance(rendered, (str, unicode, int, float)):
                    # return a json string
                    return encoder.encode(rendered)
                return rendered

        abort(404)



page.add_url_rule('/', view_func=PageView.as_view('page'))
page.add_url_rule('/index.html', view_func=PageView.as_view('index'))
page.add_url_rule('/<path:uri>/', view_func=PageView.as_view('page_uri'))
page.add_url_rule('/<path:uri>/index.html', view_func=PageView.as_view('uri_index'))
