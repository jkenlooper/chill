create table Node (
    id integer primary key autoincrement,
    name varchar(255) not null,
    left integer not null,
    right integer not null,
    value text,
    modified datetime,
    created datetime,
    something);

insert into Node (name, left, right) values ('root', 1, 2);


create table route (
    id integer primary key autoincrement,
    path text unique not null,
    node_id integer
);

/* Name of a template file that will be used to render the node's value. */
create table Template (
    id integer primary key autoincrement,
    name varchar(255) unique not null
);
create table Template_Node (
    template_id integer,
    node_id integer unique,
    foreign key ( template_id ) references Template ( id ) on delete set null,
    foreign key ( node_id ) references Node ( id ) on delete set null
);

/* Name of a sql file that has a select statement which will be used to select
 * the node's value. */
create table SelectSQL (
    id integer primary key autoincrement,
    name varchar(255) not null
);
create table SelectSQL_Node (
    select_sql_id integer,
    node_id integer
);
  
/*
create table owner (
    id integer primary key,
    name unique not null,
    )

--http://stackoverflow.com/questions/3290183/managing-picture-tags-in-sql?rq=1
create table owner_node (
    id integer primary key,
    name unique not null,
    )

create table permission (
    id integer primary key,
    name unique not null,
    )

create table tag (
    id integer primary key,
    name unique not null,
    )
*/
