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
    node_has_template = False
    if isinstance(value, bool):
        raise TypeError('Boolean values are not supported. Surround the value with quotes to set as string.')
    _value = value
    if isinstance(value, int) or isinstance(value, float):
        _value = str(value)
    elif isinstance(value, dict) and (value.get('chill_template') != None or value.get('chill_value')  != None):
        if value.get('chill_template') == None:
            _add_node_to_parent(parent_node_id, name, value.get('chill_value'))
            return
        else:
            _value = value.get('chill_value')
            node_has_template = True

    item_node_id = None
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
            # TODO: check if 'chill_template' or 'chill_value' is a key name
            for item_name in _value.keys():
                item_value = _value.get(item_name)
                _add_node_to_parent(item_node_id, item_name, item_value)

        elif isinstance(_value, list):
            for item_value in _value:
                _add_node_to_parent(item_node_id, name, item_value)
        else:
            raise TypeError('unsupported value type. Use only dict, or list.')

    if node_has_template:
        add_template_for_node(value.get('chill_template'), item_node_id)

def _render_chill_node_value(node_id):
    # get the node
    query_result = db.execute(text(fetch_query_string('select_query_from_node.sql')), {"node_id": node_id}).fetchall()
    value = None
    if query_result:
        current_app.logger.debug('render {node_id}'.format(node_id=node_id))
        current_app.logger.debug(query_result)
        values = []
        if len(query_result) > 1:
            raise NotImplementedError('TODO: Support for multiple queries found for a node.')
        for query_name in [x['name'] for x in query_result]:
            if query_name == 'select_link_node_from_node.sql':
                link_nodes_result = db.execute(text(fetch_query_string('select_link_node_from_node.sql')), {"node_id": node_id}).fetchall()
                if link_nodes_result:
                    value = {}
                    for link_node in link_nodes_result:
                        current_app.logger.debug('link_nodes_result item {}'.format(link_node))
                        value[link_node.name] = _render_chill_node_value(link_node.node_id)
                        current_app.logger.debug('link_node name and value {} : {}'.format(link_node.name, value[link_node.name]))

                else:
                    node = select_node(node_id=node_id)[0]
                    value = node.value
                    current_app.logger.debug('set node {} value {}'.format(node_id, node.value))
            else:
                value = query_name
                current_app.logger.debug('set node {} to query value {}'.format(node_id, value))
    else:
        node = select_node(node_id=node_id)[0]
        value = node.value
        current_app.logger.debug('no query; set node {} value {}'.format(node_id, value))

    return value


class ChillNode(yaml.YAMLObject):
    yaml_loader = yaml.SafeLoader
    yaml_tag = u'!ChillNode'

    # Default props
    name = None
    value = None
    template = None
    route = None

    def __init__(self, name, node_id=None, value=None, template=None, query=None, path=None, method=None, weight=None):
        self.name = name
        if value != None:
            self.value = value
        if template != None:
            self.template = template
        if query != None:
            if query == 'select_link_node_from_node.sql':
                #self.value = {
                #    'content': "hello"
                #}
                self.value = _render_chill_node_value(node_id)

                #raise NotImplementedError('TODO: render_node for ChillNode value')
            else:
                self.value = query

        if path != None:
            if isinstance(path, str) and method == None and weight == None:
                self.route = path
            else:
                route = {
                    "path": path
                }
                if method != None:
                    route["method"] = method
                if weight != None:
                    route["weight"] = weight
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
        if isinstance(node.path, str):
            # TODO: route or path, method, weight
            chill_node = ChillNode(name=node.name, node_id=node.node_id, value=node.value, query=node.query, path=node.path, method=node.method, weight=node.weight)

            chill_nodes.append(chill_node)

    with open(yaml_file, 'w') as f:
        yaml.dump_all(chill_nodes, stream=f, default_flow_style=False)
        current_app.logger.debug(yaml.dump_all(chill_nodes, default_flow_style=False))

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
