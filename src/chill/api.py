from sqlalchemy.exc import DatabaseError, StatementError
from flask import current_app, render_template

from chill.app import db
from database import fetch_query_string, rowify

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
    [{'abc':123},{'abc':456}] -> [{'abc':123,'abc':456}] # skip for same set keys
    [[{'abc':123},{'abc':456}]] -> [{'abc':123,'abc':456}]
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
        value = filter(None, value)
        # Only checking first item and assumin all others are same type
        if isinstance(value[0], dict):
            if set(value[0].keys()) == set(value[1].keys()):
                return value
            elif max([len(x.keys()) for x in value]) == 1:
                newvalue = {}
                for v in value:
                    key = v.keys()[0]
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
        query_result = db.query(fetch_query_string('select_query_from_node.sql'), fetchall=True, **kw)
    except DatabaseError as err:
        current_app.logger.error("DatabaseError: %s, %s", err, kw)
        return value
    #current_app.logger.debug("queries kw: %s", kw)
    #current_app.logger.debug("queries value: %s", value)
    #current_app.logger.debug("queries: %s", query_result)
    if query_result:
        values = []
        for query_name in [x.get('name', None) for x in query_result]:
            if query_name:
                result = []
                try:
                    result = db.query(fetch_query_string(query_name), **kw)
                    if len(result) == 0:
                        values.append(([], []))
                    else:
                        # There may be more results, but only interested in the
                        # first one
                        values.append((result.as_dict(), result[0].keys()))
                except (DatabaseError, StatementError) as err:
                    current_app.logger.error("DatabaseError (%s) %s: %s", query_name, kw, err)
        value = values
    #current_app.logger.debug("value: %s", value)
    return value

def _link(node_id):
    "Add the value for a linked node"
    c = db.cursor()
    linked_value = c.execute(fetch_query_string('select_link_node_from_node.sql'), {'node_id': node_id}).fetchall()
    if linked_value:
        if len(linked_value) > 1:
            list = []
            for v in linked_value:
                list.append({v[1]: render_node(v[2], None, v[1])})
            linked_value = list
        else:
            linked_value = render_node(linked_value[0][0]) #TODO
    return linked_value

def _template(node_id, value=None):
    "Check if a template is assigned to it and render that with the value"
    result = []
    select_template_from_node = fetch_query_string('select_template_from_node.sql')
    try:
        result = db.query(select_template_from_node, **{'node_id':node_id})
        template_result = result.first()
        if template_result and template_result.get('name'):
            template = template_result.get('name')

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
        if results and results[0]:
            values = []
            for (result, cols) in results:
                if set(cols) == set(['node_id', 'name', 'value']):
                    for subresult in result:
                        #if subresult.get('name') == kw.get('name'):
                            # This is a link node
                        #current_app.logger.debug("sub: %s", subresult)
                        name = subresult.get('name')
                        if noderequest.get('_no_template'):
                            # For debugging or just simply viewing with the
                            # operate script we append the node_id to the name
                            # of each. This doesn't work with templates.
                            name = "{0} ({1})".format(name, subresult.get('node_id'))
                        values.append( {name: render_node( subresult.get('node_id'), noderequest=noderequest, **subresult )} )
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
