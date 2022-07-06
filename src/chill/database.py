import os
import json
import sqlite3

from flask import current_app, g
from werkzeug.security import safe_join


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


class ChillDBNotWritableError(Exception):
    "Error when trying to write to the sqlite database when it is read only."


def get_db():
    if 'db' not in g:

        # TODO Include arg to sqlite3.connect detect_types=sqlite3.PARSE_DECLTYPES ?
        db_file = current_app.config.get("CHILL_DATABASE_URI")
        if db_file and not db_file.startswith(":"):
            if not current_app.config.get("database_readonly"):
                g.db = sqlite3.connect(db_file)
            else:
                g.db = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
        else:
            g.db = sqlite3.connect(current_app.config.get("CHILL_DATABASE_URI"))

        g.db.row_factory = sqlite3.Row

        # Enable foreign key support so 'on update' and 'on delete' actions
        # will apply. This needs to be set for each db connection.
        cur = g.db.cursor()
        cur.execute("pragma foreign_keys = ON;")

        # Check that journal_mode is set to wal
        result = cur.execute("pragma journal_mode;").fetchone()
        cur.close()
        if result["journal_mode"] != "wal":
            if not current_app.config.get("TESTING"):
                raise sqlite3.IntegrityError("The pragma journal_mode is not set to wal.")
            else:
                pass
                # logger.info("In TESTING mode. Ignoring requirement for wal journal_mode.")

        g.db.commit()
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)


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
    db = get_db()
    cur = db.cursor()
    for filename in CHILL_CREATE_TABLE_FILES:
        cur.execute(fetch_query_string(filename))
    cur.close()


def drop_db():
    """Drop all tables that Chill uses.
    Deletes the following tables from the database:
    Chill
    Node
    Node_Node
    Route
    Query
    Template
    """
    db = get_db()
    cur = db.cursor()
    for filename in CHILL_DROP_TABLE_FILES:
        cur.execute(fetch_query_string(filename))
    cur.close()


class RowEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, sqlite3.Row):
            return dict(map(lambda x: (x, obj[x]), obj.keys()))


def serialize_sqlite3_results(results):
    return json.loads(json.dumps(results, cls=RowEncoder))


def _fetch_sql_string(file_name):
    with current_app.open_resource(safe_join("queries", file_name), mode="r") as f:
        return f.read()


def fetch_query_string(file_name):
    content = current_app.queries.get(file_name, None)
    if content is not None:
        return content
    current_app.logger.info(
        "queries file: '%s' not available. Checking file system..." % file_name
    )

    # folder = current_app.config.get('THEME_SQL_FOLDER', '')
    # file_path = os.path.join(os.path.abspath('.'), folder, file_name)
    folder = current_app.config.get("THEME_SQL_FOLDER")
    file_path = safe_join(folder, file_name)
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            return f.read()
    else:
        # fallback on one that's in app resources
        return _fetch_sql_string(file_name)


def insert_node(**kw):
    "Insert a node with a name and optional value. Return the node id."
    db = get_db()
    cur = db.cursor()
    result = cur.execute(fetch_query_string("insert_node.sql"), kw)
    node_id = result.lastrowid
    if not node_id:
        result = result.fetchall()
        node_id = result[0]["id"]
    cur.close()
    return node_id


def insert_node_node(**kw):
    """
    Link a node to another node. node_id -> target_node_id.  Where `node_id` is
    the parent and `target_node_id` is the child.
    """
    db = get_db()
    cur = db.cursor()
    insert_query(name="select_link_node_from_node.sql", node_id=kw.get("node_id"))
    cur.execute(fetch_query_string("insert_node_node.sql"), kw)
    cur.close()


def delete_node(**kw):
    """
    Delete a node by id.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute(fetch_query_string("delete_node_for_id.sql"), kw)
    cur.close()


def select_node(**kw):
    """
    Select node by id.
    """
    db = get_db()
    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select_node_from_id.sql"), kw
    ).fetchall()
    cur.close()
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
    db = get_db()
    cur = db.cursor()
    cur.execute(fetch_query_string("insert_route.sql"), binding)
    cur.close()


def add_template_for_node(name, node_id):
    "Set the template to use to display the node"
    db = get_db()
    cur = db.cursor()
    cur.execute(
        fetch_query_string("insert_template.sql"),
        {"name": name, "node_id": node_id},
    )
    result = cur.execute(
        fetch_query_string("select_template.sql"),
        {"name": name, "node_id": node_id},
    ).fetchall()
    if result:
        template_id = result[0]["id"]
        cur.execute(
            fetch_query_string("update_template_node.sql"),
            {
                "template": template_id,
                "node_id": node_id,
            },
        )
    cur.close()


def insert_query(**kw):
    """
    Insert a query name for a node_id.
    `name`
    `node_id`

    Adds the name to the Query table if not already there. Sets the query field
    in Node table.
    """
    db = get_db()
    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select_query_where_name.sql"), kw
    ).fetchall()
    if result:
        kw["query_id"] = result[0]["id"]
    else:
        result = cur.execute(fetch_query_string("insert_query.sql"), kw)
        kw["query_id"] = result.lastrowid
        if not kw["query_id"]:
            result = result.fetchall()
            kw["query_id"] = result[0]["id"]
    cur.execute(fetch_query_string("insert_query_node.sql"), kw)
    cur.close()
