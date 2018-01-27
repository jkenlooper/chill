create table Node_Node (
    node_id integer,
    target_node_id integer,
    foreign key ( node_id ) references Node ( id ) on delete cascade,
    foreign key ( target_node_id ) references Node ( id ) on delete cascade
);
