create table Image (
  id integer primary key,
  width integer not null,
  height integer not null,
  srcset integer references Srcset (id),
  staticfile integer references StaticFile (id) not null
);

/*
 * Image(id) many-to-one Srcset(id) many-to-one Picture(id)
 * and/or
 * Image(id) -> Picture(image)
 * and/or
 * Image(id) -> Picture(original)
 */



