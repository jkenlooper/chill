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
    col_names = []
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

def insert_node(**kw):
    with current_app.app_context():
        c = db.cursor()
        c.execute(fetch_sql_string('insert_node.sql'), kw)
        node_id = c.execute(fetch_sql_string('select_max_id_node.sql')).fetchone()[0]
        db.commit()
        return node_id

def insert_node_node(**kw):
    """ Link a node to another node. """
    with current_app.app_context():
        c = db.cursor()
        c.execute(fetch_sql_string('insert_node_node.sql'), kw)
        db.commit()

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

def insert_route(**kw):
    """
    `path`
    `node_id`
    `weight`
    `method`
    """
    binding = {
            'path': None,
            'node_id': None,
            'weight': None,
            'method': "GET"
            }
    binding.update(kw)
    with current_app.app_context():
        c = db.cursor()
        c.execute(fetch_sql_string('insert_route.sql'), binding)
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


def insert_selectsql(**kw):
    """
    Insert a selectsql name for a node_id.
    `name`
    `node_id`
    """
    with current_app.app_context():
        c = db.cursor()
        c.execute(fetch_sql_string('insert_selectsql.sql'), kw)
        result = c.execute(fetch_sql_string('select_selectsql_where_name.sql'), kw).fetchall()
        (result, col_names) = normalize(result, c.description)
        if result:
            kw['selectsql_id'] = result[0].get('id')
            c.execute(fetch_sql_string('insert_selectsql_node.sql'), kw)
        db.commit()


