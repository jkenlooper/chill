create table Node (
    id integer primary key autoincrement,
    name varchar(255),
    value text,
    template integer,
    foreign key ( template ) references Template ( id ) on delete set null
    );
