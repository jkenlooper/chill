import sqlite3
from flask import current_app, render_template

from chill.app import db
from database import fetch_sql_string, fetch_selectsql_string, normalize

def _selectsql(node_id, value=None):
    "Look up value by using SelectSQL table"
    c = db.cursor()
    select_selectsql_from_node = fetch_sql_string('select_selectsql_from_node.sql')
    try:
        c.execute(select_selectsql_from_node, {'node_id':node_id})
        # TODO: change to fetchall 
        selectsql_result = c.fetchone()
        if selectsql_result and selectsql_result[1]:
            selectsql_name = selectsql_result[1]
            selectsql = fetch_selectsql_string(selectsql_name)
            value = c.execute(selectsql, {'node_id':node_id}).fetchall()
            if value and (len(value) >= 1):
                (value, col_names) = normalize(value, c.description)
                #TODO: only encode json if no template is set for it? Or just if route ends with .json?
                #TODO: determine if selecting from Node table
                #TODO: check if 'node_id' in description and render_node for any
                if 'node_id' in col_names:
                    list = []
                    for v in value:
                        list.append({v['name']: render_node(v['node_id'], v.get('value',None), v.get('name', None))})
                    value = list

                value = {'name':value} #TODO: restructure this
    except sqlite3.DatabaseError as err:
        current_app.logger.error("DatabaseError: %s", err)
    return value

def _link(node_id):
    "Add the value for a linked node"
    c = db.cursor()
    linked_value = c.execute(fetch_sql_string('select_link_node_from_node.sql'), {'node_id': node_id}).fetchall()
    if linked_value:
        if len(linked_value) > 1:
            list = []
            for v in linked_value:
                current_app.logger.debug(v)
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

def render_node(node_id, value, name):
    #c = db.cursor()
    if value == None:
        value = _selectsql(node_id)

        value = _add_value(value, _link(node_id))

    value = _template(node_id, value)
    
    return value
