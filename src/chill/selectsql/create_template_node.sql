create table Template_Node (
    template_id integer,
    node_id integer unique,
    foreign key ( template_id ) references Template ( id ) on delete set null,
    foreign key ( node_id ) references Node ( id ) on delete set null
);

