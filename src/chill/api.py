from __future__ import absolute_import
from sqlalchemy.exc import DatabaseError, StatementError
from sqlalchemy.sql import text
from flask import current_app, render_template

from chill.app import db
from .database import fetch_query_string, rowify

def _short_circuit(value=None):
    """
    Add the `value` to the `collection` by modifying the collection to be
    either a dict or list depending on what is already in the collection and
    value.
    Returns the collection with the value added to it.

    Clean up by removing single item array and single key dict.
    ['abc'] -> 'abc'
    [['abc']] -> 'abc'
    [{'abc':123},{'def':456}] -> {'abc':123,'def':456}
    [{'abc':123},{'abc':456}] -> [{'abc':123},{'abc':456}] # skip for same set keys
    [[{'abc':123},{'abc':456}]] -> [{'abc':123},{'abc':456}]
    """
    if not isinstance(value, list):
        return value
    if len(value) == 0:
        return value
    if len(value) == 1:
        if not isinstance(value[0], list):
            return value[0]
        else:
            if len(value[0]) == 1:
                return value[0][0]
            else:
                return value[0]
    else:
        value = [_f for _f in value if _f]
        # Only checking first item and assumin all others are same type
        if isinstance(value[0], dict):
            if set(value[0].keys()) == set(value[1].keys()):
                return value
            elif max([len(list(x.keys())) for x in value]) == 1:
                newvalue = {}
                for v in value:
                    key = list(v.keys())[0]
                    newvalue[key] = v[key]
                return newvalue
            else:
                return value
        else:
            return value



def _query(_node_id, value=None, **kw):
    "Look up value by using Query table"
    query_result = []
    try:
        query_result = db.execute(text(fetch_query_string('select_query_from_node.sql')), **kw).fetchall()
    except DatabaseError as err:
        current_app.logger.error("DatabaseError: %s, %s", err, kw)
        return value
    #current_app.logger.debug("queries kw: %s", kw)
    #current_app.logger.debug("queries value: %s", value)
    #current_app.logger.debug("queries: %s", query_result)
    if query_result:
        values = []
        for query_name in [x['name'] for x in query_result]:
            if query_name:
                result = []
                try:
                    #current_app.logger.debug("query_name: %s", query_name)
                    #current_app.logger.debug("kw: %s", kw)
                    # Query string can be insert or select here
                    #statement = text(fetch_query_string(query_name))
                    #params = [x.key for x in statement.params().get_children()]
                    #skw = {key: kw[key] for key in params}
                    #result = db.execute(statement, **skw)
                    result = db.execute(text(fetch_query_string(query_name)), **kw)
                    #current_app.logger.debug("result query: %s", list(result.keys()))
                except (DatabaseError, StatementError) as err:
                    current_app.logger.error("DatabaseError (%s) %s: %s", query_name, kw, err)
                if result and result.returns_rows:
                    result = result.fetchall()
                    #values.append(([[dict(zip(result.keys(), x)) for x in result]], result.keys()))
                    #values.append((result.fetchall(), result.keys()))
                    #current_app.logger.debug("fetchall: %s", values)
                    if len(result) == 0:
                        values.append(([], []))
                    else:
                        #current_app.logger.debug("result: %s", result)
                        # There may be more results, but only interested in the
                        # first one. Use the older rowify method for now.
                        # TODO: use case for rowify?
                        values.append(rowify(result, [(x, None) for x in list(result[0].keys())]))
                        #current_app.logger.debug("fetchone: %s", values)
        value = values
    #current_app.logger.debug("value: %s", value)
    return value

def _template(node_id, value=None):
    "Check if a template is assigned to it and render that with the value"
    result = []
    select_template_from_node = fetch_query_string('select_template_from_node.sql')
    try:
        result = db.execute(text(select_template_from_node), node_id=node_id)
        template_result = result.fetchone()
        result.close()
        if template_result and template_result['name']:
            template = template_result['name']

            if isinstance(value, dict):
                return render_template(template, **value)
            else:
                return render_template(template, value=value)
    except DatabaseError as err:
        current_app.logger.error("DatabaseError: %s", err)

    # No template assigned to this node so just return the value
    return value

def render_node(_node_id, value=None, noderequest={}, **kw):
    "Recursively render a node's value"
    if value == None:
        kw.update( noderequest )
        results = _query(_node_id, **kw)
        #current_app.logger.debug("results: %s", results)
        if results:
            values = []
            for (result, cols) in results:
                if set(cols) == set(['node_id', 'name', 'value']):
                    for subresult in result:
                        #if subresult.get('name') == kw.get('name'):
                            # This is a link node
                        #current_app.logger.debug("sub: %s", subresult)
                        name = subresult['name']
                        if noderequest.get('_no_template'):
                            # For debugging or just simply viewing with the
                            # operate script we append the node_id to the name
                            # of each. This doesn't work with templates.
                            name = "{0} ({1})".format(name, subresult['node_id'])
                        values.append( {name: render_node( subresult['node_id'], noderequest=noderequest, **subresult )} )
                #elif 'node_id' and 'name' in cols:
                #    for subresult in result:
                #        current_app.logger.debug("sub2: %s", subresult)
                #        values.append( {subresult.get('name'): render_node( subresult.get('node_id'), **subresult )} )
                else:
                    values.append( result )

            value = values

    value = _short_circuit(value)
    if not noderequest.get('_no_template'):
        value = _template(_node_id, value)

    return value
