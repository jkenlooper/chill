/* Name of a template file that will be used to render the node's value. */
create table Template (
    id integer primary key autoincrement,
    name varchar(255) unique not null
);
