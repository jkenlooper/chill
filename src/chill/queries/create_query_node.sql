create table SelectSQL_Node (
    selectsql_id integer,
    node_id integer,
    foreign key ( selectsql_id ) references SelectSQL ( id ) on delete set null,
    foreign key ( node_id ) references Node ( id ) on delete set null
);

