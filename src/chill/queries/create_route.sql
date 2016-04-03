/* The Route table specifies the URL for which a page can be rendered. Supports
 * dynamic Werkzeug style routes with angle brackets like
 * '/<int:year>/<int:month>/<int:day>/<slug>'. The weight value is used to
 * order these desc.
 */
create table Route (
    id integer primary key,
    path text not null,
    node_id integer,
    weight integer default 0,
    method varchar(10) default 'GET',
    foreign key ( node_id ) references Node ( id ) on delete set null
);
