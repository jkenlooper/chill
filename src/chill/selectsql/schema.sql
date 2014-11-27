create table Node (
    id integer primary key autoincrement,
    name varchar(255),
    value text
    );

/* The Route table specifies the URL for which a page can be rendered. Supports
 * dynamic Werkzeug style routes with angle brackets like
 * '/<int:year>/<int:month>/<int:day>/<slug>'. The weight value is used to
 * order these desc.
 */
create table Route (
    id integer primary key autoincrement,
    path text not null,
    node_id integer,
    weight integer default 0,
    method varchar(10) default 'GET',
    foreign key ( node_id ) references Node ( id ) on delete set null
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
    selectsql_id integer,
    node_id integer,
    foreign key ( selectsql_id ) references SelectSQL ( id ) on delete set null,
    foreign key ( node_id ) references Node ( id ) on delete set null
);

/* Link a node to a some other node's value */
create table Node_Node (
    node_id integer,
    target_node_id integer,
    foreign key ( node_id ) references Node ( id ) on delete set null,
    foreign key ( target_node_id ) references Node ( id ) on delete set null
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
