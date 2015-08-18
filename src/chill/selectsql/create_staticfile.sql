create table StaticFile (
  id integer primary key autoincrement,
  path varchar(255) not null,
  contenttype varchar(64)
);
