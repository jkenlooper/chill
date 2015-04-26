=========================================
Cascading, Highly Irrelevant, Lost Llamas
=========================================

*Or, just chill.*

(Oh, that makes little sense. Let me try to be more descriptive.)


Database driven web application framework in Flask
--------------------------------------------------

This involves creating custom SQL queries to pull your data from your database
into your jinja2 HTML templates for your website.  Chill creates a static
version of the website or can run as a Flask app. Their are a few tables that
are specific to Chill in order to handle page routes and what SQL query should
be used and such.

Quickstart
----------

Run the `chill init` script in an empty directory and it will create a minimal
starting point for using Chill. The site.cfg created will have comments on each
configuration value.  The `chill run --config site.cfg` will run the app in the
foreground at the 'http://localhost:5000/' url.

To add a page involves a few steps.  This is done by editing the tables in the
relational database.  Chill provides some helpers to make this easier. For
example::

    >>> from chill.database import insert_node
    >>> from chill.app import make_app, db
    >>> app = make_app(config='site.cfg', DEBUG=True)
    >>> with app.app_context():
    ...     testnode = insert_node(name='testnode', value='just testing')
    ...     db.commit()
    ...
    >>>

Will do the same as the following SQL::

    sqlite> insert into Node (name, value) values ('testnode', 'just testing');


The builtin SQL tables that Chill uses are the following::

    sqlite> .table
    Node            Route           SelectSQL_Node  Template_Node
    Node_Node       SelectSQL       Template


The minimum to show a templated page requires doing the following::

    echo "<html><head><title>Example</title></head><body><p> {{ message }} </p>" > templates/hello.html

    sqlite3 -header -column db

    sqlite> insert into Node (name, value) values ('message', 'Hello, World!');
    sqlite> select last_insert_rowid();
    last_insert_rowid()
    -------------------
    6
    sqlite> insert into Node (name, value) values ('hellopage', null);
    sqlite> select last_insert_rowid();
    last_insert_rowid()
    -------------------
    7
    sqlite> insert or replace into Node_Node (node_id, target_node_id) values (7, 6);
    sqlite> insert or ignore into SelectSQL (name) values ('select_link_node_from_node.sql');
    sqlite> select * from SelectSQL where name is 'select_link_node_from_node.sql' limit 1;
    id          name
    ----------  ------------------------------
    1           select_link_node_from_node.sql
    sqlite> insert or replace into SelectSQL_Node (selectsql_id, node_id) values (1, 7);
    sqlite> insert or ignore into Template (name) values ('hello.html');
    sqlite> select t.id, t.name from Template as t where t.name is 'hello.html';
    id          name
    ----------  ----------
    2           hello.html
    sqlite> insert or replace into Template_Node (template_id, node_id) values (2, 7);
    sqlite> insert into Route (path, node_id, weight, method) values ('/hello/', 7, null, 'GET');
    sqlite> .quit

    chill run --config site.cfg &

    curl localhost:5000/hello/
    <html><head><title>Example</title></head><body><p> Hello, World! </p>


Which simply creates a node with the "Hello, World!" message and makes it
available to the /hello/ route using the 'hello.html' template.


Overview of Resource Directories
--------------------------------

There are two directories that are used when creating a website:  `themes`, and
`data`.  Ideally, these are specified in your own buildout.cfg and are under
some kind of version control.  An example of these are included in the source
of this package and are used for unit tests.

Themes
******

This directory can contain multiple theme directories each with their set of
mustache templates and other resource files like css, js, images, and such.
These get applied to a page when the page has set it's special `_theme`
variable to the name of the theme directory. Normally the `_theme` would be set
at the top level of the data directory. All files within the themes directory
can be accessed with a url like: '/_themes/default/css/site.css' where
'default' is the name of the theme.  Note, the mustache templates can also be
accessed like this: '/_themes/default/base.mustache'.

Data
****

Each directory and it's sub directories are made into HTML pages with the url
being something like: /cheese/index.html . This would be for a directory at the
top level with the name of 'cheese'. Notice that the 'index.html' is created
instead of a file called 'cheese.html'.  This is to help with future additions
to the content where you may want sub pages under this directory, like:
'/cheese/provolone/index.html'. Also, the 'index.html' part of the url for
these can be omitted as webservers are usually configured to redirect to the
'index.html' if accessing a directory.


Building a website
------------------

Install with ``pip install chill``.  This will create a script called
``chill``.  Type ``chill --help`` for help on using it.  It will need a config
file::

    HOST = '127.0.0.1'
    PORT = 5000
    FREEZER_DESTINATION = "frozen"
    THEME_PATH = "themes"
    DATA_PATH = "data"

chill run
*********

The ``run`` command is used when you are developing your site's content and
structure.  It stays in the foreground and logs access to the default host and
port which is http://localhost:5000 . This really is just designed to run on
your development machine and not under a production environment.

chill freeze
************

This is basically a wrapper around the Frozen-Flask python package that freezes
your site into static files ready to be uploaded to a server or something.
