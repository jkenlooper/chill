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

from flask import current_app
from pyselect import select
from chill.app import db
from chill.database import (
        init_db,
        insert_node,
        insert_node_node,
        insert_route,
        insert_selectsql,
        add_template_for_node,
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

def mode_insert():
    "Select a function to perform"

    print globals()['mode_insert'].__doc__
    selection = True
    database_functions = [
            'insert_node',
            'insert_selectsql',
            'insert_node_node',
            'insert_route',
            'add_template_for_node',
            ]
    while selection:
        choices = database_functions + [
            'help',
            ]
        selection = select(choices)

        if selection:
            print globals().get(selection).__doc__
        if selection == 'insert_node':
            name = raw_input("Node name: ")
            value = raw_input("Node value: ")
            node = insert_node(name=name, value=value or None)
            print "name: %s \nid: %s" % (name, node)

        elif selection == 'insert_selectsql':
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
            sqlfile = select(choices)
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
            'insert',
            'update',
            'select',
            'delete',
            'help',
            ])
        if selection == 'insert':
            mode_insert()
        elif selection == 'update':
            print 'not implemented yet'
        elif selection == 'select':
            print 'not implemented yet'
        elif selection == 'delete':
            print 'not implemented yet'
        elif selection == 'help':
            print "------"
            print __doc__
            print "------"
        else:
            print 'Done'

        db.commit()


