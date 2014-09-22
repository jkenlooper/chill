import os
import os.path

import sqlite3
from flask import abort, redirect, Blueprint, current_app, render_template
from flask.views import MethodView

from chill.app import db
from database import fetch_sql_string


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

            rendered = self.render_node(result[2], result[1])
            if rendered:
                return rendered

        abort(404)

    def render_node(self, node_id, value):
        c = db.cursor()
        if value == None:
            # Look up value by using SelectSQL table
            value = None # 'TODO: get value from SelectSQL' # TODO:
            # TODO: recursive  set value to dict with each node found as a key?
            # Or just render?

        # TODO: check if a template is assigned to it and render that instead
        select_template_from_node = fetch_sql_string('select_template_from_node.sql')
        try:
            c.execute(select_template_from_node, {'node_id':node_id})
            template_result = c.fetchone()
            if template_result and template_result[1]:
                template = template_result[1]

                # TODO: render the template with value
                #return 'TODO: render template: "%s" with value: "%s"' % (template, value)
                return render_template(template, value=value)
            #else:
            #    # No template for this node so just return the value if not None
            #    if value:
            #        return value
        except sqlite3.DatabaseError as err:
            current_app.logger.error("DatabaseError: %s", err)
        
        return value


page.add_url_rule('/', view_func=PageView.as_view('page'))
page.add_url_rule('/index.html', view_func=PageView.as_view('index'))
page.add_url_rule('/<path:uri>/', view_func=PageView.as_view('page_uri'))
page.add_url_rule('/<path:uri>/index.html', view_func=PageView.as_view('uri_index'))
