import os
import os.path

import sqlite3
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException

from flask import abort, redirect, Blueprint, current_app, render_template, json, request, make_response
from flask.views import MethodView

from chill.app import db
from database import fetch_sql_string, fetch_selectsql_string, normalize
from api import render_node, _selectsql

encoder = json.JSONEncoder(indent=2, sort_keys=True)

#def get_map_adapter():
#    map_adapter = getattr(
#
def check_map(uri, url_root):
    """
    return a tuple of the rule and kw.
    """
    # TODO: Building the Map each time this is called seems like it could be more effiecent.
    c = db.cursor()
    try:
        c.execute("""
        select path as rule, weight, node_id from Route where rule like '%<%>%'
        order by weight desc;
        """)
    except sqlite3.OperationalError as err:
        current_app.logger.error("OperationalError: %s", err)
        return (None, None)
    result = c.fetchall()
    if result:
        (routes, col_names) = normalize(result, c.description)
        current_app.logger.debug( [x['rule'] for x in routes] )
        rules = map( lambda r: Rule(r['rule'], endpoint='dynamic'), routes )
        d_map = Map( rules )
        map_adapter = d_map.bind(url_root)
        current_app.logger.debug(uri)
        try:
            (rule, rule_kw) = map_adapter.match(path_info=uri, return_rule=True)
            current_app.logger.debug(rule)
            return (str(rule), rule_kw)
        except HTTPException:
            pass
    return (None, {})

# The page blueprint has no static files or templates read from disk.
page = Blueprint('public', __name__, static_folder=None, template_folder=None)

#page.record(set_map)
#map_adapter = map.bind('example.com')

class PageView(MethodView):
    """
    Handles access to a uri.
    The uri is first matched directly with a route to get a node. If that
    fails, it will load up the custom map and check the uri with any matching
    routes.  
    
    When a node is retrieved (get) it renders that nodes value. (See `render_node`.)
    """
    def _node_from_uri(self, uri):
        # check if page exists in data_path

        # a//b == a/b/ == a/./b == a/foo/../b
        # '' == '.'
        # Prepend the uri with '/' and normalize
        uri = os.path.normpath(os.path.join('/', uri))

        uri, ext = os.path.splitext(uri)
        if not uri.endswith('/'):
            uri = ''.join((uri, '/'))

        current_app.logger.debug('uri: "%s"' % uri)

        rule_kw = {}
        select_node_from_route = fetch_sql_string('select_node_from_route.sql')

        c = db.cursor()
        try:
            c.execute(select_node_from_route, {'uri':uri})
        except sqlite3.DatabaseError as err:
            current_app.logger.error("DatabaseError: %s", err)

        result = c.fetchall()
        current_app.logger.debug('result: "%s"' % result)
        if not result or len(result) == 0:
            # See if the uri matches any dynamic rules
            (rule, rule_kw) = check_map(uri, request.url_root)
            current_app.logger.debug(rule)
            current_app.logger.debug('rule: "%s"' % rule or '')
            if rule:
                try:
                    c.execute(select_node_from_route, {'uri':rule})
                    result = c.fetchall()
                except sqlite3.DatabaseError as err:
                    current_app.logger.error("DatabaseError: %s", err)

        if result:
            (result, col_names) = normalize(result, c.description)

            # Only one result for a getting a node from a unique path.
            return (result[0], rule_kw)
        return (None, rule_kw)

    def get(self, uri=''):
        """
        view a page
        """
        (node, rule_kw) = self._node_from_uri(uri)

        if node == None:
            abort(404)
        rule_kw.update( node )
        values = rule_kw
        values.update( request.form.to_dict(flat=True) )
        values.update( request.args.to_dict(flat=True) )

        current_app.logger.debug("get kw: %s", values)
        rendered = render_node(node['id'], **values)
        current_app.logger.debug("rendered: %s", rendered)
        if rendered:
            if not isinstance(rendered, (str, unicode, int, float)):
                # return a json string
                return encoder.encode(rendered)
            return rendered

        # Nothing to show, so nothing found
        abort(404)


    def post(self, uri=''):
        "Modify"
        
        (node, rule_kw) = self._node_from_uri(uri)
        current_app.logger.debug(node)
        current_app.logger.debug(rule_kw)
        current_app.logger.debug(request.form)
        current_app.logger.debug(request.args)
        # render node...
        rule_kw.update( node )
        values = rule_kw
        values.update( request.form.to_dict(flat=True) )
        values.update( request.args.to_dict(flat=True) )
        current_app.logger.debug(values)
        sql = _selectsql(node.get('id'), **values)
        db.commit()
        response = make_response('ok', 201)
        return response

    def put(self, uri=''):
        "Modify"
        
        (node, rule_kw) = self._node_from_uri(uri)

    def patch(self, uri=''):
        "Modify"
        
        (node, rule_kw) = self._node_from_uri(uri)

    def delete(self, uri=''):
        "Modify"
        
        (node, rule_kw) = self._node_from_uri(uri)



page.add_url_rule('/', view_func=PageView.as_view('page'))
page.add_url_rule('/index.html', view_func=PageView.as_view('index'))
page.add_url_rule('/<path:uri>/', view_func=PageView.as_view('page_uri'))
page.add_url_rule('/<path:uri>/index.html', view_func=PageView.as_view('uri_index'))
