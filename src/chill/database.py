from flask import current_app
from chill.app import db

def init_db():
    with current_app.app_context():
        #db = get_db()
        with current_app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def add_node_to_node(target_node_id, name, **kw):
    values = {'target_node_id':target_node_id,
            'name': name}
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
              insert or ignore into Template_Node (template_id, node_id) values (:template_id, :node_id);
              """, {'template_id':template_id, 'node_id':node_id})
        db.commit()


