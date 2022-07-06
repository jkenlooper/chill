import sqlite3

from flask import current_app, render_template

from chill.database import get_db, fetch_query_string, serialize_sqlite3_results, ChillDBNotWritableError


def _short_circuit(value=None):
    """
    Add the `value` to the `collection` by modifying the collection to be
    either a dict or list depending on what is already in the collection and
    value.
    Returns the collection with the value added to it.

    Clean up by removing single item array and single key dict.
    ['abc'] -> 'abc'
    [['abc']] -> 'abc'
    [{'abc':123}] -> {'abc':123}
    [[{'abc':123}]] -> {'abc':123}
    [{'abc':123},{'def':456}] -> {'abc':123,'def':456}
    [{'abc':123},{'abc':456}] -> [{'abc':123},{'abc':456}] # skip for same set keys
    [[{'abc':123},{'abc':456}]] -> [{'abc':123},{'abc':456}]
    """
    if not isinstance(value, list):
        return value
    if len(value) == 0:
        return value
    if len(value) == 1:
        if not isinstance(value[0], list):
            return value[0]
        else:
            if len(value[0]) == 1:
                return value[0][0]
            else:
                return value[0]
    else:
        value = [_f for _f in value if _f]
        # Only checking first item and assumin all others are same type
        if isinstance(value[0], dict):
            if set(value[0].keys()) == set(value[1].keys()):
                return value
            elif max([len(list(x.keys())) for x in value]) == 1:
                newvalue = {}
                for v in value:
                    key = list(v.keys())[0]
                    newvalue[key] = v[key]
                return newvalue
            else:
                return value
        else:
            return value


def _query(_node_id, value=None, **kw):
    "Look up value by using Query table"
    # GET query method can only be read
    # POST query method can be read or write
    if current_app.config.get("database_readonly") and kw["method"] in ("PUT", "PATCH", "DELETE"):
        raise Exception("Database is currently readonly, but started processing a query method that was not readonly")
    query_result = []
    db = get_db()
    cur = db.cursor()
    try:
        query_result = cur.execute(
            fetch_query_string("select_query_from_node.sql"), kw
        ).fetchall()
    except sqlite3.DatabaseError as err:
        current_app.logger.error("DatabaseError: %s, %s", err, kw)
        cur.close()
        return value
    # current_app.logger.debug("queries kw: %s", kw)
    # current_app.logger.debug("queries value: %s", value)
    # current_app.logger.debug("queries: %s", serialize_sqlite3_results(query_result))
    ignored_db_error = False
    if query_result:
        values = []
        for query_name in [x["name"] for x in query_result]:
            if query_name:
                result = []
                try:
                    current_app.logger.debug("query_name: %s", query_name)
                    current_app.logger.debug("kw: %s", kw)
                    # Query string can be insert or select here
                    # statement = fetch_query_string(query_name)
                    # params = [x.key for x in statement.params().get_children()]
                    # skw = {key: kw[key] for key in params}
                    # result = cur.execute(statement, **skw)
                    result = cur.execute(fetch_query_string(query_name), kw)
                except (sqlite3.DatabaseError, sqlite3.ProgrammingError) as err:
                    ignored_db_error = True
                    current_app.logger.error(
                        "DatabaseError (%s) %s: %s", query_name, kw, err
                    )
                if result:
                    result = result.fetchall()
                    # values.append(([[dict(zip(result.keys(), x)) for x in result]], result.keys()))
                    # values.append((result.fetchall(), result.keys()))
                    # current_app.logger.debug("fetchall: %s", values)
                    if len(result) == 0:
                        current_app.logger.debug("result is empty")
                        # values.append([{}])
                        values.append([{}])
                    else:
                        current_app.logger.debug(
                            "result: %s", serialize_sqlite3_results(result)
                        )
                        values.append(result)
        value = values
    # current_app.logger.debug("value: %s", value)
    cur.close()

    if kw["method"] == "GET" and db.in_transaction:
        raise Exception("There are uncommitted changes to db when query was GET")
    if kw["method"] == "POST" and (db.in_transaction or ignored_db_error) and current_app.config.get("database_readonly"):
        if db.in_transaction:
            current_app.logger.error("There are uncommitted changes to read only db connection when query was POST")
            raise ChillDBNotWritableError("There are uncommitted changes to read only db connection when query was POST")
        elif ignored_db_error:
            current_app.logger.error("There were database query errors to read only db connection when query was POST")
            raise ChillDBNotWritableError("There were database query errors to read only db connection when query was POST")
        else:
            raise Exception("Not handled error.")
    if current_app.config.get("database_readonly") and db.in_transaction:
        current_app.logger.error("There are uncommitted changes to db when query should have been readonly")
        raise Exception("There are uncommitted changes to db when query should have been readonly")
    if not current_app.config.get("database_readonly"):
        # Only need to commit a transaction if the database is not in read only
        # mode.
        db.commit()

    return value


def _template(node_id, value=None):
    "Check if a template is assigned to it and render that with the value"
    db = get_db()
    if value:
        value = serialize_sqlite3_results(value)
    result = []
    select_template_from_node = fetch_query_string("select_template_from_node.sql")
    cur = db.cursor()
    try:
        result = cur.execute(select_template_from_node, {"node_id": node_id})
        template_result = result.fetchone()
        cur.close()
        if template_result and template_result["name"]:
            template = template_result["name"]

            if isinstance(value, dict):
                return render_template(template, **value)
            else:
                return render_template(template, value=value)
    except sqlite3.DatabaseError as err:
        current_app.logger.error("DatabaseError: %s", err)

    # No template assigned to this node so just return the value
    return value


def render_node(_node_id, value=None, noderequest={}, **kw):
    "Recursively render a node's value"
    if value is None:
        kw.update(noderequest)
        kw["method"] = "GET"
        results = _query(_node_id, **kw)
        current_app.logger.debug("render_node results: %s", results)
        if results:
            values = []
            for result in results:
                if set(result[0].keys()) == set(["node_id", "name", "value"]):
                    for subresult in result:
                        # if subresult.get('name') == kw.get('name'):
                        # This is a link node
                        current_app.logger.debug("sub: %s", subresult)
                        name = subresult["name"]
                        if noderequest.get("_no_template"):
                            # For debugging; append the node_id to the name
                            # of each. This doesn't work with templates.
                            name = "{0} ({1})".format(name, subresult["node_id"])
                        values.append(
                            {
                                name: render_node(
                                    subresult["node_id"],
                                    noderequest=noderequest,
                                    **subresult
                                )
                            }
                        )
                # elif 'node_id' and 'name' in cols:
                #    for subresult in result:
                #        current_app.logger.debug("sub2: %s", subresult)
                #        values.append( {subresult.get('name'): render_node( subresult.get('node_id'), **subresult )} )
                else:
                    values.append(result)

            value = values

    value = _short_circuit(value)
    # current_app.logger.debug(f"after sc: {value}")
    if not noderequest.get("_no_template"):
        value = _template(_node_id, value)
        # current_app.logger.debug(f"after template: {value}")

    return value
