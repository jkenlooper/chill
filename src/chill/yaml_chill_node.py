import os
import sqlite3

from sqlalchemy.sql import text
from flask import current_app
import yaml

from chill.app import make_app, db
from chill.database import (
        init_db,
        insert_node,
        insert_node_node,
        delete_node,
        select_node,
        insert_route,
        insert_query,
        add_template_for_node,
        fetch_query_string,
        rowify,
        )

def _is_sql_file(file_name):
    folder = current_app.config.get('THEME_SQL_FOLDER')
    file_path = os.path.join(folder, file_name)
    return os.path.isfile(file_path)

def _is_template_file(file_name):
    folder = current_app.config.get('THEME_TEMPLATE_FOLDER')
    file_path = os.path.join(folder, file_name)
    return os.path.isfile(file_path)

def _value_is_simple_string(value):
    if isinstance(value, str):
        _value = value.strip()
        if _value.endswith('.sql') and _is_sql_file(_value):
            return False
        else:
            return True

def _add_node_to_parent(parent_node_id, name, value):
    if isinstance(value, bool):
        raise TypeError('Boolean values are not supported. Surround the value with quotes to set as string.')
    _value = value
    if isinstance(value, int) or isinstance(value, float):
        _value = str(value)
    if _value_is_simple_string(_value):
        item_node_id = insert_node(name=name, value=_value)
        insert_query(name='select_link_node_from_node.sql', node_id=item_node_id)
        insert_node_node(node_id=parent_node_id, target_node_id=item_node_id)

    elif isinstance(_value, str) and _is_sql_file(_value):
        item_node_id = insert_node(name=name, value=None)
        insert_query(name=_value, node_id=item_node_id)
        insert_node_node(node_id=parent_node_id, target_node_id=item_node_id)

    else:
        item_node_id = insert_node(name=name, value=None)
        insert_query(name='select_link_node_from_node.sql', node_id=item_node_id)
        insert_node_node(node_id=parent_node_id, target_node_id=item_node_id)

        if isinstance(_value, dict):
            for item_name in _value.keys():
                item_value = _value.get(item_name)
                _add_node_to_parent(item_node_id, item_name, item_value)

        elif isinstance(_value, list):
            for item_value in _value:
                _add_node_to_parent(item_node_id, name, item_value)
        else:
            raise TypeError('unsupported value type. Use only dict, or list.')

class ChillNode(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!ChillNode'

    # Default props
    name = None
    value = None
    template = None
    route = None

    def __init__(self, name, value=None, template=None, route=None):
        self.name = name
        self.value = value
        self.template = template
        self.route = route

    def load(self):
        if not self.name:
            raise TypeError('the `name` property is required for ChillNode')

        if isinstance(self.value, bool):
            raise TypeError('Boolean values are not supported. Surround the value with quotes to set as string.')

        value = None
        if _value_is_simple_string(self.value):
            value = self.value
        elif isinstance(self.value, int) or isinstance(self.value, float):
            value = str(self.value)

        # Insert the chill_node
        chill_node = insert_node(name=self.name, value=value)

        # Set the route
        if self.route:
            if isinstance(self.route, str):
                insert_route(path=self.route, node_id=chill_node, weight=None, method='GET')
            elif isinstance(self.route, dict):
                route_path = self.route.get('path', None)
                if route_path == None:
                    raise TypeError('A path must be set for a route')
                elif not isinstance(route_path, str):
                    raise TypeError('A path must be a string value')
                route_weight = self.route.get('weight', None)
                route_method = self.route.get('method', 'GET')
                if route_weight != None and not isinstance(route_weight, int):
                    raise TypeError("route weight value needs to be integer if defined")
                if (isinstance(route_method, str) and route_method.upper() not in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH')):
                    raise TypeError("route method value needs to be 'GET', 'POST', 'PUT', 'DELETE', or 'PATCH' if defined")
                elif not isinstance(route_method, str):
                    raise TypeError("route method value needs to be 'GET', 'POST', 'PUT', 'DELETE', or 'PATCH' if defined")
                insert_route(path=self.route['path'], node_id=chill_node, weight=route_weight, method=route_method.upper())

            else:
                raise TypeError('route value other then str or dict not supported')

        # Set the template
        if self.template:
            if isinstance(self.template, str):
                if _is_template_file(self.template):
                    add_template_for_node(name=self.template, node_id=chill_node)
                else:
                    raise TypeError('template value must be a path to a file in template folder')
            else:
                raise TypeError('template value must be a string')

        # Set the query if value is not simple string
        if not value:
            if isinstance(self.value, str) and _is_sql_file(self.value):
                insert_query(name=self.value, node_id=chill_node)

            elif isinstance(self.value, dict):
                for item_name in self.value.keys():
                    item_value = self.value.get(item_name)
                    _add_node_to_parent(chill_node, item_name, item_value)

            elif isinstance(self.value, list):
                for item_value in self.value:
                    _add_node_to_parent(chill_node, 'value', item_value)
            else:
                raise TypeError('unsupported value type. Use only dict, or list.')


        current_app.logger.debug(self.route)

    def __repr__(self):
        return "%s(name=%r, value=%r, template=%r, route=%r)" % (self.__class__.__name__, self.name, self.value, self.template, self.route)


def dump_yaml(yaml_file):
    "Dump chill database structure to ChillNode yaml objects."
    current_app.logger.debug(globals()['dump_yaml'].__doc__)

    result = db.execute(text(fetch_query_string('select_all_chill_nodes.sql'))).fetchall()

    current_app.logger.debug(result)
    node_list = result
    chill_nodes = []

    for node in node_list:
        current_app.logger.debug(node)
        node_path = node.path
        if isinstance(node_path, str):
            chill_node = ChillNode(name=node.name, value=node.value)

            chill_nodes.append(chill_node)

    with open(yaml_file, 'w') as f:
        current_app.logger.debug(yaml.dump_all(chill_nodes, default_flow_style=False))
        f.write(yaml.dump_all(chill_nodes, default_flow_style=False))

    # select all from Node and store in a list
    # for each that has a route
        # get template string if defined
        # if value is string
            # set value
        # else
            # if query is defined and not path to Node_Node query
                # set value to sql query file
            # else
                # recursivly render node value and set path to sql query files for
                # nodes with null value.

        # pop node from list for each node that has been added
    #

def load_yaml(yaml_file):
    "Load ChillNode yaml objects into chill database."
    current_app.logger.debug(globals()['load_yaml'].__doc__)

    with open(yaml_file, 'r') as f:
        documents = yaml.safe_load_all(f.read())
        for item in documents:
            current_app.logger.debug(item)
            if isinstance(item, ChillNode):
                try:
                    item.load()
                except NotImplementedError as err:
                    current_app.logger.warning(err)
