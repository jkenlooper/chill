create table Picture (
  id integer primary key autoincrement,
  picturename varchar(64) unique not null,
  /* picturename:
    For user use only like in shortcode:
    [picture:crazy-cat] or for listing in
    a management interface, could also be used for
    the shown filename.
    */
  artdirected boolean default false,
    -- Hint for the template to use <picture> or <img[srcset]>.
  title text,
  description text,
  author text,
  created text,
  image integer references Image (id) not null,
  /*
   * image is not null as its used as the src attribute in img tag. <picture>
   * requires having an img.
   */
  original integer references Image (id)
);
/*
 * The Srcset table references the id for Picture and
 * can have a many to one relationship. (Many Srcset to
 * one Picture)
 */


