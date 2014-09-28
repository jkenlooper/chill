import os
from flask import current_app
from chill.app import db

def init_db():
    with current_app.app_context():
        #db = get_db()
        with current_app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

#TODO: change the 'normalize' name...
def normalize(l, description):
    d = []
    if l != None and description != None:
        col_names = [x[0] for x in description]
        for row in l:
            d.append(dict(zip(col_names, row)))
    return (d, col_names)

def fetch_sql_string(file_name):
    # TODO: optimize reading this into memory or get it elsewhere.
    with current_app.open_resource(file_name, mode='r') as f:
        return f.read()

def fetch_selectsql_string(file_name):
    # TODO: optimize reading this into memory or get it elsewhere.
    folder = current_app.config.get('SELECTSQL_FOLDER', '')
    file_path = os.path.join(os.path.abspath('.'), folder, file_name) 
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    else:
        # fallback on one that's in app resources
        return fetch_sql_string(file_name)

def add_node_to_node(target_node_id, name, value=None, **kw):
    values = {'target_node_id':target_node_id,
            'name': name,
            'value': value}
    values.update(kw)

    with current_app.app_context():

        is_leaf_node = db.execute("""
        SELECT id
        FROM Node
        WHERE right = left + 1 and id = :target_node_id;
        """, values).fetchone();

        added_id = None
        if True or is_leaf_node:
            sql = 'add_node_to_leaf_node.sql'
        else:
            sql = 'add_node_to_node.sql'
        with current_app.open_resource(sql, mode='r') as f:
            # TODO: strip out comments

            for statement in f.read().split(';'):
                result = db.execute(statement, values).fetchone()
                if result:
                    added_id = result[0]
        db.commit()
        return added_id

def path_for_node(id):
    with current_app.app_context():
        return '/'.join([x[0] for x in db.execute("""
        SELECT parent.name
        FROM Node as n,
                Node AS parent
                WHERE n.left BETWEEN parent.left AND parent.right
                        AND n.id = :id
                        ORDER BY n.left;
        """, {'id':id}).fetchall()])

def add_node_for_route(path, node_id):
    with current_app.app_context():
        c = db.cursor()
        c.execute("""
          insert into route (path, node_id) values (:path, :node_id)
          """, {'path':path, 'node_id':node_id})
        db.commit()

def add_template_for_node(name, node_id):
    with current_app.app_context():
        c = db.cursor()
        c.execute("""
          insert or ignore into Template (name) values (:name)
          """, {'name':name, 'node_id':node_id})
        c.execute("""
          select t.id, t.name from Template as t where t.name is :name;
          """, {'name':name, 'node_id':node_id})
        result = c.fetchone()
        if result:
            template_id = result[0]
            c.execute("""
              insert or replace into Template_Node (template_id, node_id) values (:template_id, :node_id);
              """, {'template_id':template_id, 'node_id':node_id})
        db.commit()


def add_selectsql_for_node(name, node_id):
    with current_app.app_context():
        c = db.cursor()
        c.execute("""
          insert or ignore into SelectSQL (name) values (:name)
          """, {'name':name, 'node_id':node_id})
        c.execute("""
          select s.id, s.name from SelectSQL as s where s.name is :name;
          """, {'name':name, 'node_id':node_id})
        result = c.fetchone()
        if result:
            selectsql_id = result[0]
            c.execute("""
              insert or replace into SelectSQL_Node (selectsql_id, node_id) values (:selectsql_id, :node_id);
              """, {'selectsql_id':selectsql_id, 'node_id':node_id})
        db.commit()


def link_node_to_node(node_id, target_node_id):
    with current_app.app_context():
        c = db.cursor()
        c.execute("""
          insert or replace into Node_Node (node_id, target_node_id) values (:node_id, :target_node_id);
          """, {'node_id':node_id, 'target_node_id':target_node_id})
        db.commit()
