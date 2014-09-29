import sqlite3
from flask import current_app, render_template

from chill.app import db
from database import fetch_sql_string, fetch_selectsql_string, normalize

def render_node(node_id, value, name):
    c = db.cursor()
    if value == None:
        # Look up value by using SelectSQL table
        #value = None # 'TODO: get value from SelectSQL' # TODO:
        # TODO: recursive  set value to dict with each node found as a key?
        # Or just render?
        select_selectsql_from_node = fetch_sql_string('select_selectsql_from_node.sql')
        try:
            current_app.logger.debug(node_id)
            c.execute(select_selectsql_from_node, {'node_id':node_id})
            selectsql_result = c.fetchone()
            current_app.logger.debug('ss %s', selectsql_result)
            if selectsql_result and selectsql_result[1]:
                selectsql_name = selectsql_result[1]
                selectsql = fetch_selectsql_string(selectsql_name)
                value = c.execute(selectsql, {'node_id':node_id}).fetchall()
                if value and (len(value) >= 1):
                    (value, col_names) = normalize(value, c.description)
                    #TODO: only encode json if no template is set for it? Or just if route ends with .json?
                    #TODO: determine if selecting from Node table
                    #current_app.logger.debug([x[0] for x in c.description])
                    #TODO: check if 'node_id' in description and render_node for any
                    if 'node_id' in col_names:
                        list = []
                        for v in value:
                            current_app.logger.debug(v)
                            list.append({v['name']: render_node(v['node_id'], v.get('value',None), v.get('name', None))})
                        value = list

                    value = {name:value}
                current_app.logger.debug('value %s', value)
        except sqlite3.DatabaseError as err:
            current_app.logger.error("DatabaseError: %s", err)

        # TODO: add the value for a linked node
        linked_value = c.execute(fetch_sql_string('select_link_node_from_node.sql'), {'node_id': node_id}).fetchall()
        if linked_value:
            current_app.logger.debug("linked: %s", linked_value)
            if len(linked_value) > 1:
                list = []
                for v in linked_value:
                    current_app.logger.debug(v)
                    list.append({v[1]: render_node(v[2], None, v[1])})
                linked_value = list
            else:
                linked_value = render_node(linked_value[0][0]) #TODO

            if value == None:
                # subsitute the value from the linked node for this one
                value = linked_value
            elif isinstance(value, (tuple, list)):
                # Multiple values have been set via other means already so append or extend it.
                if isinstance(linked_value, (tuple, list)):
                    value.extend(linked_value)
                else:
                    value.append(linked_value)
            else:
                current_app.logger.warning('Replacing value with linked value.')
                value = linked_value
                # TODO: currently, this won't happen?
                # One value has been set, but now need to convert to list with the linked value
              

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
