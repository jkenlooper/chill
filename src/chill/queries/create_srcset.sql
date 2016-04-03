create table Srcset (
  id integer primary key,
  picture integer references Picture (id)
);
/* The Image table references the Srcset. */
