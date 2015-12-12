/* Name of a sql file that has a select statement which will be used to select
 * the node's value. */
create table Query (
    id integer primary key autoincrement,
    name varchar(255) not null
);
