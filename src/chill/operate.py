"""Operate script to edit a SQL Database that is used by chill.

Some various operations are selected via a select menu.  Entering the number
and pressing return will select that item and will show other prompts to
interactively edit the content in the database. Entering nothing and simply
hitting return will exit that menu.

All of these operations can be manually done via SQL, but this is more of
a simple approach using functions found within chill.  If needing to add lots
of content it would be wise to write a script to handle these things.

"""
import os
from glob import glob
import re

from yaml import safe_dump
import sqlite3
from flask import current_app
from pyselect import select
from chill.app import db
from api import render_node
from chill.database import (
        init_db,
        init_picture_tables,
        insert_node,
        insert_node_node,
        delete_node,
        select_node,
        insert_route,
        insert_query,
        add_template_for_node,
        fetch_query_string,
        add_picture_for_node,
        link_picturename_for_node,
        rowify,
        )

INVALID_NODE = -1

def node_input():
    """
    Get a valid node id from the user.

    Return -1 if invalid
    """
    try:
        node = int(raw_input("Node id: "))
    except ValueError:
        node = INVALID_NODE
        print 'invalid node id: %s' % node
    return node

def existing_node_input():
    """
    Get an existing node id by name or id.

    Return -1 if invalid
    """
    input_from_user = raw_input("Existing node name or id: ")
    node_id = INVALID_NODE
    c = db.cursor()

    if not input_from_user:
        return node_id

    # int or str?
    try:
        parsed_input = int(input_from_user)
    except ValueError:
        parsed_input = input_from_user

    if isinstance(parsed_input, int):
        c.execute(fetch_query_string('select_node_from_id.sql'),
                {'node_id':parsed_input})
        result = c.fetchall()
        (result, col_names) = rowify(result, c.description)
        if result:
            node_id = int(result[0].get('node_id'))
    else:
        c.execute(fetch_query_string('select_node_from_name.sql'),
                {'node_name':parsed_input})
        result = c.fetchall()
        (result, col_names) = rowify(result, c.description)
        if result:
            if len(result) == 1:
                print 'Node id: {node_id}\nNode name: {name}'.format(**result[0])
                print '-------------'
                node_id = result[0].get('node_id')
            else:
                print 'Multiple nodes found with the name: {0}'.format(parsed_input)
                for item in result:
                    print '{node_id}: {name} = {value}'.format(**item)
                node_selection = raw_input('Enter a node id from this list or enter "?" to render all or "?<node>" for a specific one.')
                if node_selection:
                    node_selection_match = re.match(r"\?(\d)*", node_selection)
                    if node_selection_match:
                        if node_selection_match.groups()[0]:
                            value = render_node(int(node_selection_match.groups()[0]), noderequest={'_no_template':True}, **result[0])
                            print safe_dump(value, default_flow_style=False)
                        else:
                            for item in result:
                                value = render_node(item.get('node_id'), noderequest={'_no_template':True}, **item)
                                print 'Node id: {0}'.format(item.get('node_id'))
                                print safe_dump(value, default_flow_style=False)
                                print '---'
                        node_id = node_input()
                    else:
                        try:
                            node_id = int(node_selection)
                        except ValueError:
                            node_id = INVALID_NODE
                            print 'invalid node id: %s' % node

    return node_id

def render_value_for_node(node_id):
    """
    Wrap render_node for usage in operate scripts.  Returns without template
    rendered.
    """
    value = None
    c = db.cursor()
    try:
        c.execute(fetch_query_string('select_node_from_id.sql'), {'node_id':node_id})
    except sqlite3.DatabaseError as err:
        current_app.logger.error("DatabaseError: %s", err)

    result = c.fetchall()
    if result:
        (result, col_names) = rowify(result, c.description)
        kw = result[0]
        value = render_node(node_id, noderequest={'_no_template':True}, **kw)

    return value

def choose_query_file():
    print "Choose from the available query files:"
    choices = set(
            map(os.path.basename,
                glob(os.path.join(os.path.dirname(__file__), 'queries', '*'))
                )
            )
    folder = current_app.config.get('THEME_SQL_FOLDER')
    choices.update(
            set(map(os.path.basename,
                glob(os.path.join(folder, '*'))
                )
            ))
    choices = list(choices)
    choices.sort()
    return select(choices)

def purge_collection(keys):
    "Recursive purge of nodes with name and id"
    for key in keys:
        m = re.match(r'(.*) \((\d+)\)', key)
        name = m.group(1)
        node_id = m.group(2)
        value = render_value_for_node(node_id)
        print 'remove node with name:{0} and id:{1}'.format(name, node_id)

        delete_node(node_id=node_id)
        if isinstance(value, dict):
            purge_collection(value.keys())

def list_items_in_collection(keys):
    "List just the items in the collection."


def mode_collection():
    """
    Manage an existing collection node.
    """
    print globals()['mode_collection'].__doc__
    collection_node_id = existing_node_input()
    value = render_value_for_node(collection_node_id)
    if not value:
        return None
    print "Collection length: {0}".format(len(value))
    print safe_dump(value, default_flow_style=False)

    item_attr_list = []
    if len(value):
        for key in value.items()[0][1].keys():
            m = re.match(r'(.*) \((\d+)\)', key)
            item_attr_list.append(m.group(1))

    selection = True
    while selection:
        selection = select([
            'View collection',
            'Add item',
            'Add attribute',
            'Remove item',
            'Remove attribute',
            'Purge collection'
            ])
        if selection == 'View collection':
            print safe_dump(value, default_flow_style=False)
        elif selection == 'Purge collection':
            confirm = raw_input("Delete all {0} items and their {1} attributes from the collection? y/n\n".format(len(value.keys()), len(item_attr_list)))
            if confirm == 'y':
                delete_node(node_id=collection_node_id)
                purge_collection(value.keys())
        elif selection == 'Remove item':
            item_node_id = existing_node_input()
            if item_node_id < 0:
                return
            value = render_value_for_node(item_node_id)
            print safe_dump(value, default_flow_style=False)
            confirm = raw_input("Delete this node and it's attributes? y/n\n").format(len(value.keys()), len(item_attr_list))
            if confirm == 'y':
                delete_node(node_id=item_node_id)
                purge_collection(value.keys())

        elif selection == 'Add item':
            result = select_node(node_id=collection_node_id)
            collection_name = result[0].get('name')

            add_item_with_attributes_to_collection(
                    collection_name=collection_name,
                    collection_node_id=collection_node_id,
                    item_attr_list=item_attr_list)
        elif selection == 'Remove attribute':
            print "Select the attribute that will be removed:"
            attribute_selection = select(item_attr_list)
            if attribute_selection:
                confirm = raw_input("Delete attribute '{0}' from all {1} items in the collection? y/n\n".format(attribute_selection, len(value.keys())))
                if confirm == 'y':
                    for item_key, item in value.items():
                        for key in item.keys():
                            m = re.match(r'(.*) \((\d+)\)', key)
                            if m.group(1) == attribute_selection:
                                delete_node(node_id=m.group(2))
                                break
        elif selection == 'Add attribute':
            item_attr = raw_input("Add a collection item attribute name: ")
            if item_attr:
                item_index = 0
                for item_key, item in value.items():
                    item_index += 1
                    m = re.match(r'(.*) \((\d+)\)', item_key)
                    item_value = render_value_for_node(m.group(2))
                    print "item {0} of {1} items".format(item_index, len(value))
                    print safe_dump(item_value, default_flow_style=False)

                    new_attr_value = raw_input("Enter item attribute value for '{0}': ".format(item_attr))
                    # set value to none if it's an empty string
                    new_attr_value = new_attr_value if len(new_attr_value) else None
                    item_attr_node_id = insert_node(name=item_attr, value=new_attr_value)

                    insert_node_node(node_id=m.group(2), target_node_id=item_attr_node_id)
        # Update the value after each operation
        value = render_value_for_node(collection_node_id)


def add_item_with_attributes_to_collection(collection_name, collection_node_id, item_attr_list):
    item_node_id = insert_node(name='{0}_item'.format(collection_name), value=None)
    insert_query(name='select_link_node_from_node.sql', node_id=item_node_id)
    insert_node_node(node_id=collection_node_id, target_node_id=item_node_id)
    for item_attr_name in item_attr_list:
        value = raw_input("Enter item attribute value for '{0}': ".format(item_attr_name))
        # set value to none if it's an empty string
        value = value if len(value) else None
        item_attr_node_id = insert_node(name=item_attr_name, value=value)
        insert_node_node(node_id=item_node_id, target_node_id=item_attr_node_id)

def mode_new_collection():
    """
    Create a new collection of items with common attributes.
    """

    print globals()['mode_new_collection'].__doc__
    collection_name = raw_input("Collection name: ")
    item_attr_list = []
    collection_node_id = None
    if collection_name:
        collection_node_id = insert_node(name=collection_name, value=None)
        insert_query(name='select_link_node_from_node.sql', node_id=collection_node_id)
        item_attr = True
        while item_attr:
            item_attr = raw_input("Add a collection item attribute name: ")
            if item_attr:
                item_attr_list.append(item_attr)

    # if no collection name then exit
    selection = collection_name

    while selection:
        selection = select([
            'Add item',
            ])
        if selection == 'Add item':
            # create item
            add_item_with_attributes_to_collection(
                    collection_name=collection_name,
                    collection_node_id=collection_node_id,
                    item_attr_list=item_attr_list)

    if collection_node_id:
        print "Added collection name '{0}' with node id: {1}".format(collection_name, collection_node_id)

    db.commit()


def mode_database_functions():
    "Select a function to perform from chill.database"

    print globals()['mode_database_functions'].__doc__
    selection = True
    database_functions = [
            'init_db',
            'init_picture_tables',
            'insert_node',
            'insert_node_node',
            'delete_node',
            'insert_route',
            'insert_query',
            'add_template_for_node',
            'add_picture_for_node',
            'link_picturename_for_node',
            ]
    while selection:
        choices = database_functions + [
            'help',
            ]
        selection = select(choices)

        if selection:
            print globals().get(selection).__doc__
        if selection == 'init_db':
            confirm = raw_input("Initialize new database y/n? [n] ")
            if confirm == 'y':
                init_db()
        if selection == 'init_picture_tables':
            confirm = raw_input("Initialize new tables for pictures y/n? [n] ")
            if confirm == 'y':
                init_picture_tables()
        elif selection == 'insert_node':
            name = raw_input("Node name: ")
            value = raw_input("Node value: ")
            node = insert_node(name=name, value=value or None)
            print "name: %s \nid: %s" % (name, node)

        elif selection == 'insert_query':
            sqlfile = choose_query_file()
            if sqlfile:
                node = existing_node_input()
                if node >= 0:
                    insert_query(name=sqlfile, node_id=node)
                    print "adding %s to node id: %s" % (sqlfile, node)

        elif selection == 'insert_node_node':
            print "Add parent node id"
            node = existing_node_input()
            print "Add target node id"
            target_node = existing_node_input()
            if node >= 0 and target_node >= 0:
                insert_node_node(node_id=node, target_node_id=target_node)

        elif selection == 'delete_node':
            node = existing_node_input()
            if node >= 0:
                delete_node(node_id=node)

        elif selection == 'insert_route':
            path = raw_input('path: ')
            weight = raw_input('weight: ')
            method = raw_input('method: ') or 'GET'
            node = existing_node_input()
            if node >= 0:
                insert_route(path=path, node_id=node, weight=weight, method=method)
        elif selection == 'add_template_for_node':
            folder = current_app.config.get('THEME_TEMPLATE_FOLDER')
            choices = map(os.path.basename,
                        glob(os.path.join(folder, '*'))
                        )
            choices.sort()
            templatefile = select(choices)
            if templatefile:
                node = existing_node_input()
                if node >= 0:
                    add_template_for_node(name=templatefile, node_id=node)
                    print "adding %s to node id: %s" % (templatefile, node)
        elif selection == 'add_picture_for_node':
            if current_app.config.get('MEDIA_FOLDER'):
                node = existing_node_input()

                if node >= 0:
                    filepath = raw_input("Enter the filepath in the media folder. Enter nothing to bring up a list.")
                    if not filepath:
                        filelist = glob(os.path.join(current_app.config.get('MEDIA_FOLDER'), '*'))
                        if len(filelist) > 0:
                            toplevel_files = map(os.path.basename, filelist)
                            toplevel_files.sort()
                            filepath = select(toplevel_files)
                        else:
                            print "no files found in media folder."
                    if filepath:
                        add_picture_for_node(node_id=node, filepath=filepath)
            else:
                print "MEDIA_FOLDER not set in config."

        elif selection == 'link_picturename_for_node':
            if current_app.config.get('MEDIA_FOLDER'):
                node = existing_node_input()

                if node >= 0:
                    filepath = raw_input("Enter the filepath/picturename in the media folder. Enter nothing to bring up a list.")
                    if not filepath:
                        filelist = glob(os.path.join(current_app.config.get('MEDIA_FOLDER'), '*'))
                        if len(filelist) > 0:
                            toplevel_files = map(os.path.basename, filelist)
                            toplevel_files.sort()
                            filepath = select(toplevel_files)
                        else:
                            print "no files found in media folder."
                    if filepath:
                        link_picturename_for_node(node_id=node, picturename=filepath)
            else:
                print "MEDIA_FOLDER not set in config."

        elif selection == 'help':
            print "------"
            for f in database_functions:
                print "\n** %s **" % f
                print globals().get(f).__doc__
            print "------"
        else:
            pass

        db.commit()

def operate_menu():
    "Select between these operations on the database"

    selection = True
    while selection:

        print globals()['operate_menu'].__doc__
        selection = select([
            'chill.database functions',
            'execute sql file',
            'render_node',
            'New collection',
            'Manage collection',
            'Add document for node',
            'help',
            ])
        if selection == 'chill.database functions':
            mode_database_functions()
        elif selection == 'execute sql file':
            print "View the sql file and show a fill in the blanks interface with raw_input"
            sqlfile = choose_query_file()
            if not sqlfile:
                # return to the menu choices if not file picked
                selection = True
            else:
                sql_named_placeholders_re = re.compile(r":(\w+)")
                sql = fetch_query_string(sqlfile)
                placeholders = set(sql_named_placeholders_re.findall(sql))
                print sql
                data = {}
                for placeholder in placeholders:
                    value = raw_input(placeholder + ': ')
                    data[placeholder] = value

                c = db.cursor()
                try:
                    c.execute(sql, data)
                except sqlite3.DatabaseError as err:
                    current_app.logger.error("DatabaseError: %s", err)

                result = c.fetchall()
                if result:
                    (result, col_names) = rowify(result, c.description)
                    kw = result[0]

                    if 'node_id' in kw:
                        value = render_node(kw['node_id'], **kw)
                        print safe_dump(value, default_flow_style=False)
                    else:
                        print safe_dump(result, default_flow_style=False)

        elif selection == 'render_node':
            print globals()['render_node'].__doc__
            node_id = existing_node_input()

            value = render_value_for_node(node_id)
            print safe_dump(value, default_flow_style=False)

        elif selection == 'New collection':
            mode_new_collection()
        elif selection == 'Manage collection':
            mode_collection()
        elif selection == 'Add document for node':
            folder = current_app.config.get('DOCUMENT_FOLDER')
            if not folder:
                print "No DOCUMENT_FOLDER configured for the application."
            else:
                choices = map(os.path.basename,
                            glob(os.path.join(folder, '*'))
                            )
                choices.sort()
                if len(choices) == 0:
                    print "No files found in DOCUMENT_FOLDER."
                else:
                    filename = select(choices)
                    if filename:
                        defaultname = os.path.splitext(filename)[0]
                        nodename = raw_input("Enter name for node [{0}]: ".format(defaultname)) or defaultname
                        node = insert_node(name=nodename, value=filename)
                        print "Added document '%s' to node '%s' with id: %s" % (filename, nodename, node)
        elif selection == 'help':
            print "------"
            print __doc__
            print "------"
        else:
            print 'Done'

        db.commit()


