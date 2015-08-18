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
        insert_route,
        insert_selectsql,
        add_template_for_node,
        fetch_selectsql_string,
        add_picture_for_node,
        rowify,
        )

def node_input():
    """
    Get a valid node id from the user.

    Return -1 if invalid
    """
    try:
        node = int(raw_input("Node id: "))
    except ValueError:
        node = -1
        print 'invalid node id: %s' % node
    return node

def choose_selectsql_file():
    print "Choose from the available selectsql files:"
    choices = set(
            map(os.path.basename,
                glob(os.path.join(os.path.dirname(__file__), 'selectsql', '*'))
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

def mode_collection():
    "Create a collection of items with common attributes"

    print globals()['mode_collection'].__doc__
    collection_name = raw_input("Collection name: ")
    item_attr_list = []
    if collection_name:
        collection_node_id = insert_node(name=collection_name, value=None)
        insert_selectsql(name='select_link_node_from_node.sql', node_id=collection_node_id)
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
            item_node_id = insert_node(name='{0}-item'.format(collection_name), value=None)
            insert_selectsql(name='select_link_node_from_node.sql', node_id=item_node_id)
            insert_node_node(node_id=collection_node_id, target_node_id=item_node_id)
            for item_attr_name in item_attr_list:
                value = raw_input("Enter item attribute value for '{0}': ".format(item_attr_name))
                item_attr_node_id = insert_node(name=item_attr_name, value=value)
                insert_node_node(node_id=item_node_id, target_node_id=item_attr_node_id)

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
            'insert_route',
            'insert_selectsql',
            'add_template_for_node',
            'add_picture_for_node',
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

        elif selection == 'insert_selectsql':
            sqlfile = choose_selectsql_file()
            if sqlfile:
                node = node_input()
                if node >= 0:
                    insert_selectsql(name=sqlfile, node_id=node)
                    print "adding %s to node id: %s" % (sqlfile, node)

        elif selection == 'insert_node_node':
            node = node_input()
            print "Add target node id"
            target_node = node_input()
            if node >= 0 and target_node >= 0:
                insert_node_node(node_id=node, target_node_id=target_node)

        elif selection == 'insert_route':
            path = raw_input('path: ')
            weight = raw_input('weight: ')
            method = raw_input('method: ') or 'GET'
            node = node_input()
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
                node = node_input()
                if node >= 0:
                    add_template_for_node(name=templatefile, node_id=node)
                    print "adding %s to node id: %s" % (templatefile, node)
        elif selection == 'add_picture_for_node':
            if current_app.config.get('MEDIA_FOLDER'):
                node = node_input()

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
            'Create collection',
            'Add document for node',
            'help',
            ])
        if selection == 'chill.database functions':
            mode_database_functions()
        elif selection == 'execute sql file':
            print "View the sql file and show a fill in the blanks interface with raw_input"
            sqlfile = choose_selectsql_file()
            sql_named_placeholders_re = re.compile(r":(\w+)")
            sql = fetch_selectsql_string(sqlfile)
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
            node_id = node_input()

            c = db.cursor()
            try:
                c.execute(fetch_selectsql_string('select_node_from_id.sql'), {'node_id':node_id})
            except sqlite3.DatabaseError as err:
                current_app.logger.error("DatabaseError: %s", err)

            result = c.fetchall()
            if result:
                (result, col_names) = rowify(result, c.description)
                kw = result[0]

                value = render_node(node_id, noderequest={'_no_template':True}, **kw)
                print safe_dump(value, default_flow_style=False)

        elif selection == 'Create collection':
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


