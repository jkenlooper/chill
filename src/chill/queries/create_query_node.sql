create table Query_Node (
    query_id integer,
    node_id integer,
    foreign key ( query_id ) references Query ( id ) on delete set null,
    foreign key ( node_id ) references Node ( id ) on delete set null
);

