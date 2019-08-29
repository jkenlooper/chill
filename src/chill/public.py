from __future__ import absolute_import
from builtins import str
import os
import os.path

from sqlalchemy.sql import text
from sqlalchemy.exc import (
        DatabaseError,
        OperationalError
        )
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException

from flask import (
        abort, redirect, Blueprint, current_app, render_template, json, request, make_response, app,
        url_for
        )
from flask.views import MethodView

from chill.app import db
from .database import fetch_query_string, rowify
from .api import render_node, _query
from .cache import cache
from . import shortcodes

#def get_map_adapter():
#    map_adapter = getattr(
#
def check_map(uri, url_root):
    """
    return a tuple of the rule and kw.
    """
    # TODO: Building the Map each time this is called seems like it could be more effiecent.
    result = []
    try:
        result = db.execute(text(fetch_query_string('select_route_where_dynamic.sql'))).fetchall()
    except OperationalError as err:
        current_app.logger.error("OperationalError: %s", err)
        return (None, None)
    if result:
        #routes = result.as_dict()
        #(routes, col_names) = rowify(result, c.description)
        #current_app.logger.debug( [x['rule'] for x in routes] )
        rules = [Rule(r['rule'], endpoint='dynamic') for r in result]
        d_map = Map( rules )
        map_adapter = d_map.bind(url_root)
        #current_app.logger.debug(uri)
        try:
            (rule, rule_kw) = map_adapter.match(path_info=uri, return_rule=True)
            #current_app.logger.debug(rule)
            return (str(rule), rule_kw)
        except HTTPException:
            pass
    return (None, {})

def node_from_uri(uri, method="GET"):
    # check if page exists in data_path

    # a//b == a/b/ == a/./b == a/foo/../b
    # '' == '.'
    # Prepend the uri with '/' and normalize
    uri = os.path.normpath(os.path.join('/', uri))

    uri, ext = os.path.splitext(uri)
    if not uri.endswith('/'):
        uri = ''.join((uri, '/'))

    #current_app.logger.debug('uri: "%s"' % uri)

    rule_kw = {}
    select_node_from_route = fetch_query_string('select_node_from_route.sql')

    result = []
    try:
        result = db.execute(text(select_node_from_route), uri=uri, method=method).fetchall()
    except DatabaseError as err:
        current_app.logger.error("DatabaseError: %s", err)

    #current_app.logger.debug('result: "{}", {}'.format(result, len(result)))
    if not result or len(result) == 0:
        # See if the uri matches any dynamic rules
        (rule, rule_kw) = check_map(uri, request.url_root)
        #current_app.logger.debug(rule)
        #current_app.logger.debug('rule: "%s"' % rule or '')
        if rule:
            try:
                result = db.execute(text(select_node_from_route), uri=rule, method=method).fetchall()
            except DatabaseError as err:
                current_app.logger.error("DatabaseError: %s", err)

    if result:
        #result = result.as_dict()
        #(result, col_names) = rowify(result, c.description)

        # Only one result for a getting a node from a unique path.
        return (result[0], rule_kw)
    return (None, rule_kw)

def skip_cache():
    """Skip the cache if request has Chill-Skip-Cache set"""
    if u'Chill-Skip-Cache' in request.headers:
        return True

    return False

# The page blueprint has no static files or templates read from disk.
#page = Blueprint('public', __name__, static_folder=os.path.join( os.getcwd(), current_app.config.get('CHILL_STATIC_DIR', 'static') ), template_folder=None)

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

    @cache.cached(unless=skip_cache)
    def get(self, uri=''):
        "For sql queries that start with 'SELECT ...'"
        (node, rule_kw) = node_from_uri(uri)

        if node == None:
            abort(404)
        rule_kw.update( node )
        values = rule_kw
        xhr_data = request.get_json(silent=True)
        if xhr_data:
            values.update( xhr_data )
        values.update( request.form.to_dict(flat=True) )
        values.update( request.args.to_dict(flat=True) )
        values.update( request.cookies )
        values['method'] = request.method
        noderequest = values.copy()
        noderequest.pop('node_id')
        noderequest.pop('name')
        noderequest.pop('value')

        #current_app.logger.debug("get kw: %s", values)
        rendered = render_node(node['id'], noderequest=noderequest, **values)
        #current_app.logger.debug("rendered: %s", rendered)
        if rendered:
            if not isinstance(rendered, (str, str, int, float)):
                # return a json string
                return json.jsonify(rendered)
            return rendered

        # Nothing to show, so nothing found
        abort(404)


    def post(self, uri=''):
        "For sql queries that start with 'INSERT ...'"

        # get node...
        (node, rule_kw) = node_from_uri(uri, method=request.method)
        if node == None:
            abort(404)

        rule_kw.update( node )
        values = rule_kw
        xhr_data = request.get_json(silent=True)
        if xhr_data:
            values.update( xhr_data )
        values.update( request.form.to_dict(flat=True) )
        values.update( request.args.to_dict(flat=True) )
        values['method'] = request.method

        # Execute the sql query with the data
        _query(node['id'], **values)

        response = make_response('ok', 201)
        return response

    def put(self, uri=''):
        "For sql queries that start with 'INSERT ...' or 'UPDATE ...'"

        # get node...
        (node, rule_kw) = node_from_uri(uri, method=request.method)
        if node == None:
            abort(404)

        rule_kw.update( node )
        values = rule_kw
        xhr_data = request.get_json(silent=True)
        if xhr_data:
            values.update( xhr_data )
        values.update( request.form.to_dict(flat=True) )
        values.update( request.args.to_dict(flat=True) )
        values['method'] = request.method

        # Execute the sql query with the data
        _query(node['id'], **values)

        response = make_response('ok', 201)
        return response

    def patch(self, uri=''):
        "For sql queries that start with 'UPDATE ...'"

        # get node...
        (node, rule_kw) = node_from_uri(uri, method=request.method)
        if node == None:
            abort(404)

        rule_kw.update( node )
        values = rule_kw
        xhr_data = request.get_json(silent=True)
        if xhr_data:
            values.update( xhr_data )
        values.update( request.form.to_dict(flat=True) )
        values.update( request.args.to_dict(flat=True) )
        values['method'] = request.method

        # Execute the sql query with the data
        _query(node['id'], **values)

        response = make_response('ok', 201)
        return response

    def delete(self, uri=''):
        "For sql queries that start with 'DELETE from ...'"

        # get node...
        (node, rule_kw) = node_from_uri(uri, method=request.method)
        if node == None:
            abort(404)

        rule_kw.update( node )
        values = rule_kw
        xhr_data = request.get_json(silent=True)
        if xhr_data:
            values.update( xhr_data )
        values.update( request.form.to_dict(flat=True) )
        values.update( request.args.to_dict(flat=True) )
        values['method'] = request.method

        # Execute the sql query with the data
        _query(node['id'], **values)

        response = make_response('ok', 204)
        return response

@shortcodes.register('route')
def route_handler(context, content, pargs, kwargs):
    """
    Route shortcode works a lot like rendering a page based on the url or
    route.  This allows inserting in rendered HTML within another page.

    Activate it with the 'shortcodes' template filter. Within the content use
    the chill route shortcode: "[chill route /path/to/something/]" where the
    '[chill' and ']' are the shortcode starting and ending tags. And 'route' is
    this route handler that takes one argument which is the url.
    """
    (node, rule_kw) = node_from_uri(pargs[0])

    if node == None:
        return u"<!-- 404 '{0}' -->".format(pargs[0])

    rule_kw.update( node )
    values = rule_kw
    values.update( request.form.to_dict(flat=True) )
    values.update( request.args.to_dict(flat=True) )
    values['method'] = request.method
    noderequest = values.copy()
    noderequest.pop('node_id')
    noderequest.pop('name')
    noderequest.pop('value')

    rendered = render_node(node['id'], noderequest=noderequest, **values)

    if rendered:
        if not isinstance(rendered, (str, str, int, float)):
            # return a json string
            return json.jsonify(rendered)

        return rendered

    # Nothing to show, so nothing found
    return "<!-- 404 '{0}' -->".format(pargs[0])

@shortcodes.register('page_uri')
def page_uri_handler(context, content, pargs, kwargs):
    """
    Shortcode for getting the link to internal pages using the flask `url_for`
    method.

    Activate with 'shortcodes' template filter. Within the content use the
    chill page_uri shortcode: "[chill page_uri idofapage]". The argument is the
    'uri' for a page that chill uses.

    Does not verify the link to see if it's valid.
    """
    uri = pargs[0]
    return url_for('.page_uri', uri=uri)
