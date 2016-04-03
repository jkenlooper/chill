## Goal of this software

Chill can be used to create a simple website that has some of its data in
a relational database.  It can also be used for creating pages with more
complex data requirements. That requires the developer to write their own SQL
queries and such.  It is scriptable, so you can write your own script that
loads all the data from a hierarchy of folders and inserts them into
a database.  The idea here is to keep things rather simple and flexible.

You can create a website using Chill and not even write any python code or SQL.  It
comes with a built-in `chill operate` command which allows managing nodes,
routes, templates, etc. in a database.  You can also manually edit your
database using whatever other tool works for you.  All Chill does is read from
the database to determine what URL routes load the templates with the data.  It
doesn't have a built-in admin web interface to do anything like a more complete
CMS would.  Chill is not a CMS.  You can create a CMS with Chill, though.  It's
more of a web application framework which is built on Flask which is also a web
application framework.

## Conventions that Chill uses

A URL route loads the data from a node in the database.  A template can be
assigned to that node when it is rendered.  A SQL query is used to get more
complex data for a node.  Simple, right?

### Relational databases

Chill is configured to work with SQLite databases.  It uses a few specific
tables in the database. It utilizes some saved SQL queries which are used to
generate the output for a website.

### Key to value mapping with nodes

A Node is used to hold a value.  The value can be any bit of text that is
displayed on the web page. The name attribute of a Node entry is how the
template refers to that value.  If the value is null then the value is
determined by the query attrbute.  In this way you can have one Node get the
value or result from running another query.

### URL Route registrations with Flask

The Route table holds the various URL routes for a website.  The path attribute
is set to the text of the route like '/path/to/somepage/'.  More information
about [URL Route
registrations](http://flask.pocoo.org/docs/0.10/api/#url-route-registrations).
The node_id attribute refers to the node that should display it's value at that
route.

### Queries

If the value for a Node is null, then a Query can be used to return a value.
For instance, nothing exciting happens when a node has a value set to the
string: 'Hello, World!'.  Chill will simply return that value if the node is
referred to by a route like '/'.  A Query has a name attribute that refers to
the file in the queries folder. This file is a SQL query which will be run when
whatever node has been linked to it.  The query can return other nodes which
can in turn run their own queries.  The return value can then be a nested list
of dictionaries or whatever.  

The complexity of all the different queries that can run for the generation of
a page's content can get rather slow.  Chill was designed to be more of static
page generator and not necessarily be ran on production servers under heavy
load.  There are some caching configurations that can be done to make things
more optimal.

### Templates for rendering the nodes

A Node can be assigned a jinja2 template to use when it's value is being
rendered.  If the route to a node doesn't have a template assigned to it, then
a JSON string will be returned.

### Documents on the file system

Not all the data for a site needs to be in a database.  A document folder can
be configured to store text files that a node can refer to.  The jinja2
template can use the `readfile` filter to read the file and optionally pass it
along to other filters like a markdown filter.  The `chill operate` command can
be used to easily assign a node's value to the name of a document in the
folder.

## routes
more detail and examples

## nodes
more detail and examples

## queries
more detail and examples

## templates
more detail and examples

## Static Resources

The files that a website design relies on are configured to be in the theme
static folder.  Note that these files are used by the *design* of the site and
not the *content* of the site.  The files that are used by the content of the
site are stored in the media folder.

A root folder can also be configured to serve static resources from the root of
the site.  By default this is not configured since the PUBLIC_URL_PREFIX would
also need to be set in order to avoid conflicting URL routes.

See the site.cfg file for setting these configurations.

## Create a manage script




##creating a static version

##running a server

##Extending as a flask blueprint

##optimize response time with caches

