create table Node_Picture (
    node_id integer references Node (id) not null,
    picture integer references Picture (id) not null
)
