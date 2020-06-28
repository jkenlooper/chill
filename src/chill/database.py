from __future__ import absolute_import
from builtins import zip
import os
from sqlalchemy.sql import text
from flask import current_app, g
from chill.app import db
from .cache import cache

CHILL_DROP_TABLE_FILES = (
    "drop_chill.sql",
    "drop_query.sql",
    "drop_template.sql",
    "drop_node.sql",
    "drop_node_node.sql",
    "drop_route.sql",
)
CHILL_CREATE_TABLE_FILES = (
    "create_chill.sql",
    "set_current_chill_version.sql",
    "create_query.sql",
    "create_template.sql",
    "create_node.sql",
    "create_node_node.sql",
    "create_route.sql",
)


def init_db():
    """Initialize a new database with the default tables for chill.
    Creates the following tables:
    Chill
    Node
    Node_Node
    Route
    Query
    Template

    The current Chill migration version is added to the Chill table.
    """
    hold_database_readonly_setting = current_app.config.get("database_readonly")
    current_app.config["database_readonly"] = False
    with current_app.app_context():
        for filename in CHILL_CREATE_TABLE_FILES:
            db.execute(text(fetch_query_string(filename)))
    current_app.config["database_readonly"] = hold_database_readonly_setting


def rowify(l, description):
    d = []
    col_names = []
    if l != None and description != None:
        col_names = [x[0] for x in description]
        for row in l:
            d.append(dict(list(zip(col_names, row))))
    return (d, col_names)


def _fetch_sql_string(file_name):
    with current_app.open_resource(os.path.join("queries", file_name), mode="r") as f:
        return f.read()


def fetch_query_string(file_name):
    content = current_app.queries.get(file_name, None)
    if content != None:
        return content
    current_app.logger.info(
        "queries file: '%s' not available. Checking file system..." % file_name
    )

    # folder = current_app.config.get('THEME_SQL_FOLDER', '')
    # file_path = os.path.join(os.path.abspath('.'), folder, file_name)
    folder = current_app.config.get("THEME_SQL_FOLDER")
    file_path = os.path.join(folder, file_name)
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            return f.read()
    else:
        # fallback on one that's in app resources
        return _fetch_sql_string(file_name)


def insert_node(**kw):
    "Insert a node with a name and optional value. Return the node id."
    with current_app.app_context():
        result = db.execute(text(fetch_query_string("insert_node.sql")), **kw)
        # TODO: support for postgres may require using a RETURNING id; sql
        # statement and using the inserted_primary_key?
        # node_id = result.inserted_primary_key
        node_id = result.lastrowid
        if not node_id:
            result = result.fetchall()
            node_id = result[0]["id"]
        return node_id


def insert_node_node(**kw):
    """
    Link a node to another node. node_id -> target_node_id.  Where `node_id` is
    the parent and `target_node_id` is the child.
    """
    with current_app.app_context():
        insert_query(name="select_link_node_from_node.sql", node_id=kw.get("node_id"))
        db.execute(text(fetch_query_string("insert_node_node.sql")), **kw)


def delete_node(**kw):
    """
    Delete a node by id.
    """
    with current_app.app_context():
        db.execute(text(fetch_query_string("delete_node_for_id.sql")), **kw)


def select_node(**kw):
    """
    Select node by id.
    """
    with current_app.app_context():
        result = db.execute(
            text(fetch_query_string("select_node_from_id.sql")), **kw
        ).fetchall()
        return result


def insert_route(**kw):
    """
    `path` - '/', '/some/other/path/', '/test/<int:index>/'
    `node_id`
    `weight` - How this path is selected before other similar paths
    `method` - 'GET' is default.
    """
    binding = {"path": None, "node_id": None, "weight": None, "method": "GET"}
    binding.update(kw)
    with current_app.app_context():
        db.execute(text(fetch_query_string("insert_route.sql")), **binding)


def add_template_for_node(name, node_id):
    "Set the template to use to display the node"
    with current_app.app_context():
        db.execute(
            text(fetch_query_string("insert_template.sql")), name=name, node_id=node_id
        )
        result = db.execute(
            text(fetch_query_string("select_template.sql")), name=name, node_id=node_id
        ).fetchall()
        if result:
            template_id = result[0]["id"]
            db.execute(
                text(fetch_query_string("update_template_node.sql")),
                template=template_id,
                node_id=node_id,
            )


def insert_query(**kw):
    """
    Insert a query name for a node_id.
    `name`
    `node_id`

    Adds the name to the Query table if not already there. Sets the query field
    in Node table.
    """
    with current_app.app_context():
        result = db.execute(
            text(fetch_query_string("select_query_where_name.sql")), **kw
        ).fetchall()
        if result:
            kw["query_id"] = result[0]["id"]
        else:
            result = db.execute(text(fetch_query_string("insert_query.sql")), **kw)
            kw["query_id"] = result.lastrowid
            if not kw["query_id"]:
                result = result.fetchall()
                kw["query_id"] = result[0]["id"]
        db.execute(text(fetch_query_string("insert_query_node.sql")), **kw)
