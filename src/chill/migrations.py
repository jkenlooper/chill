import sqlite3
from flask import current_app
from chill.app import make_app, db
from chill.database import (
        fetch_query_string,
        rowify,
        )


def migrate1():
    "Migrate from version 0 to 1"

    initial = [
    "create table Chill (version integer);",
    "insert into Chill (version) values (1);",
    "alter table SelectSQL rename to Query;",
    "alter table Node add column template integer references Template (id) on delete set null;",
    "alter table Node add column query integer references Query (id) on delete set null;"
    ]


    cleanup = [
    "drop table SelectSQL_Node;",
    "drop table Template_Node;"
    ]

    c = db.cursor()
    try:
        c.execute("select version from Chill limit 1;")
    except sqlite3.DatabaseError as err:
        pass
    result = c.fetchone()
    if result:
        version = result[0]
        if version == 1:
            current_app.logger.warn("Migration from version 0 to 1 is not needed.")
        else:
            current_app.logger.warn("Migration from version 0 to {0} is not supported.".format(version))
        return

    try:
        for query in initial:
            c.execute(query)
    except sqlite3.DatabaseError as err:
        current_app.logger.error("DatabaseError: %s", err)

    try:
        c.execute(fetch_query_string('select_all_nodes.sql'))
    except sqlite3.DatabaseError as err:
        current_app.logger.error("DatabaseError: %s", err)
    result = c.fetchall()
    if result:
        (result, col_names) = rowify(result, c.description)
        for kw in result:

            try:
                c.execute("""
                update Node set template = (
                select t.id from Template as t
                join Template_Node as tn on ( tn.template_id = t.id )
                join Node as n on ( n.id = tn.node_id )
                where n.id is :node_id
                group by t.id)
                where id is :node_id;
                """, {'node_id':kw['id']})
            except sqlite3.DatabaseError as err:
                current_app.logger.error("DatabaseError: %s", err)

            try:
                c.execute("""
                update Node set query = (
                select s.id from Query as s
                join SelectSQL_Node as sn on ( sn.selectsql_id = s.id )
                join Node as n on ( n.id = sn.node_id )
                where n.id is :node_id
                group by s.id)
                where id is :node_id;
                """, {'node_id':kw['id']})
            except sqlite3.DatabaseError as err:
                current_app.logger.error("DatabaseError: %s", err)
    try:
        for query in cleanup:
            c.execute(query)
    except sqlite3.DatabaseError as err:
        current_app.logger.error("DatabaseError: %s", err)

    db.commit()
