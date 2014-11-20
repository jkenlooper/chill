import sqlite3
from flask import current_app, render_template

from chill.app import db
from database import fetch_sql_string, fetch_selectsql_string, normalize

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
        # Only checking first item and assumin all others are same type
        current_app.logger.debug( value )
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



def _selectsql(_node_id, value=None, **kw):
    "Look up value by using SelectSQL table"
    c = db.cursor()
    try:
        result = c.execute(fetch_sql_string('select_selectsql_from_node.sql'), kw).fetchall()
    except sqlite3.DatabaseError as err:
        current_app.logger.error("DatabaseError: %s, %s", err, kw)
        return value
    (selectsql_result, selectsql_col_names) = normalize(result, c.description)
    current_app.logger.debug("selectsql: %s", selectsql_result)
    if selectsql_result:
        values = []
        for selectsql_name in [x.get('name', None) for x in selectsql_result]:
            if selectsql_name:
                try:
                    result = c.execute(fetch_selectsql_string(selectsql_name), kw).fetchall()
                    values.append( normalize(result, c.description) )
                except sqlite3.DatabaseError as err:
                    current_app.logger.error("DatabaseError (%s) %s: %s", selectsql_name, kw, err)
        value = values
    current_app.logger.debug("value: %s", value)
    return value

def _link(node_id):
    "Add the value for a linked node"
    c = db.cursor()
    linked_value = c.execute(fetch_sql_string('select_link_node_from_node.sql'), {'node_id': node_id}).fetchall()
    if linked_value:
        if len(linked_value) > 1:
            list = []
            for v in linked_value:
                list.append({v[1]: render_node(v[2], None, v[1])})
            linked_value = list
        else:
            linked_value = render_node(linked_value[0][0]) #TODO
    return linked_value

def _add_value(value, new_value):
    if value == None:
        # subsitute the value from the linked node for this one
        value = new_value
    elif isinstance(value, (tuple, list)):
        # Multiple values have been set via other means already so append or extend it.
        if isinstance(new_value, (tuple, list)):
            value.extend(new_value)
        else:
            value.append(new_value)
    else:
        current_app.logger.warning('Replacing value with new value.')
        value = new_value
        # TODO: currently, this won't happen?
        # One value has been set, but now need to convert to list with the linked value
    return value

def _template(node_id, value=None):
    "Check if a template is assigned to it and render that with the value"
    c = db.cursor()
    select_template_from_node = fetch_sql_string('select_template_from_node.sql')
    try:
        c.execute(select_template_from_node, {'node_id':node_id})
        template_result = c.fetchone()
        if template_result and template_result[1]:
            template = template_result[1]

            # TODO: render the template with value
            return render_template(template, value=value)
    except sqlite3.DatabaseError as err:
        current_app.logger.error("DatabaseError: %s", err)

    # No template assigned to this node so just return the value
    return value

def render_node(_node_id, value=None, **kw):
    if value == None:
        results = _selectsql(_node_id, **kw)
        if results and results[0]:
            values = []
            for (result, cols) in results:
                if set(cols) == set(['node_id', 'name']):
                    for subresult in result:
                        #if subresult.get('name') == kw.get('name'):
                            # This is a link node
                        current_app.logger.debug("sub: %s", subresult)
                        values.append( {subresult.get('name'): render_node( subresult.get('node_id'), **subresult )} )
                #elif 'node_id' and 'name' in cols:
                #    for subresult in result:
                #        current_app.logger.debug("sub2: %s", subresult)
                #        values.append( {subresult.get('name'): render_node( subresult.get('node_id'), **subresult )} )
                else:
                    values.append( result )

            value = values
        #value = _add_value(value, _link(_node_id))

    value = _short_circuit(value)
    value = _template(_node_id, value)

    return value
