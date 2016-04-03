create table Node (
    id integer primary key,
    name varchar(255),
    value text,
    template integer,
    query integer,
    foreign key ( template ) references Template ( id ) on delete set null,
    foreign key ( query ) references Query ( id ) on delete set null
    );
