import os
import os.path

import sqlite3
from flask import abort, redirect, Blueprint, current_app, render_template
from flask.views import MethodView

from chill.app import db


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
       
        c = db.cursor()
        try:
            c.execute("""
              select Node.name, Node.value, Node.id, route.node_id, route.path from Node
              join route on route.node_id = Node.id where route.path = :uri
              group by Node.name;""", {'uri':uri})
        except sqlite3.DatabaseError as err:
            current_app.logger.error("DatabaseError: %s", err)
            if uri == '/chill':
                # Show something for fun
                return "Cascading, Highly Irrelevant, Lost Llamas"

        result = c.fetchone()
        if result:
            if result[1]:
                # Has a value set.
                value = result[1]
            else:
                # Look up value by using SelectSQL table
                value = None # TODO:

            # TODO: check if a template is assigned to it and render that instead
            try:
                c.execute("""
                    select t.id, t.name from Template as t
                    join Template_Node as tn on ( tn.template_id = t.id )
                    join Node as n on ( n.id = tn.node_id )
                    where n.id is :node_id 
                    group by t.id;
                """, {'node_id':result[2]})
                template_result = c.fetchone()
                if template_result and template_result[1]:
                    template = template_result[1]

                    # TODO: render the template with value
                    #return 'TODO: render template: "%s" with value: "%s"' % (template, value)
                    return render_template(template, value=value)
                else:
                    # No template for this node so just return the value
                    return value
            except sqlite3.DatabaseError as err:
                current_app.logger.error("DatabaseError: %s", err)

        abort(404)


page.add_url_rule('/', view_func=PageView.as_view('page'))
page.add_url_rule('/index.html', view_func=PageView.as_view('index'))
page.add_url_rule('/<path:uri>/', view_func=PageView.as_view('page_uri'))
page.add_url_rule('/<path:uri>/index.html', view_func=PageView.as_view('uri_index'))
