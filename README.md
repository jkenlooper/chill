[![Build Status](https://travis-ci.org/jkenlooper/chill.svg?branch=mustached-rival)](https://travis-ci.org/jkenlooper/chill)

# Cascading, Highly Irrelevant, Lost Llamas

*Or, just chill.*

(Oh, that makes little sense. Let me try to be more descriptive.)


## Database driven web application framework in Flask

This involves creating custom SQL queries to pull your data from your database
into your jinja2 HTML templates for your website.  Chill creates a static
version of the website or can run as a Flask app. Their are a few tables that
are specific to Chill in order to handle page routes and what SQL query should
be used and such.  

## Quickstart

Run the `chill init` script in an empty directory and it will create a minimal
starting point for using Chill. The *site.cfg* created will have comments on each
configuration value.  The `chill run --config site.cfg` will run the app in the
foreground at the 'http://localhost:5000/' url. Notice that the script also
creates a sqlite database in that directory.  This database is what the script
uses to display the pages in a site.

## Create a single page example

One way to manage the content for the website is to create a python script that
uses some of the helper functions from chill.database.  One of them is the
`insert_node` function which simply inserts a name and value to the `Node`
database table. 

    from chill.app import make_app, db
    from chill.database import insert_node

    app = make_app(config='site.cfg', DEBUG=True)

    with app.app_context():
        testnode = insert_node(name='testnode', value='just testing')
        db.commit()
    
The following code creates a simple homepage that uses a template and is
available at the '/' url and displays the content of another node.  It's
basically what the `chill init` command does.

When a node has no value assigned to it it can be used to find other nodes via
the `insert_selectsql` function. This function takes the filename of the sql
query you want to use which will then have its results put in for the value.

    homepage = insert_node(name='homepage', value=None)

Set the homepage node to be viewable at the url '/'.  If there was a value set
it would simply show that value at the url. 

    insert_route(path='/', node_id=homepage)

Set the homepage node's value be whatever else is linked to it.  The
`insert_selectsql` takes the filename of the sql query you want to use which
will then have its results put in for the value. By using the
'select_link_node_from_node.sql' file (located in the chill package) it will
find all the other node's that have been linked to it.

    insert_selectsql(name='select_link_node_from_node.sql', node_id=homepage)

To make the homepage node use a template to display its value then use
`add_template_for_node` and pass in the filename of the jinja2 template. By not
setting a template the value will just be displayed as JSON.

    add_template_for_node('homepage.html', homepage)

Finally, add some content to be displayed by adding another node but setting
its value to something irrelevant.

    homepage_content = insert_node(name='homepage_content',
        value="Cascading, Highly Irrelevant, Lost Llamas")

Then just add that node to the homepage node. Its value will be available under
the name 'homepage_content'.

    insert_node_node(node_id=homepage, target_node_id=homepage_content)


**Review the docs for more. (TODO: write the docs...)**  Until I have some
better documentation I would recommend reading through the tests.py file within
the chill package.  


## Installing

Install with `pip install chill`.  This will create a script called `chill`.
Type `chill --help` for help on using it.  It will need a config file and such.
I recommend creating an empty directory and running `chill init` within it.
That will create a site.cfg config file and the bare minimum to show
a homepage.  Run the `chill run --config site.cfg` and visit
http://localhost:5000 with your browser.


## Static site generator

The command `chill freeze --config site.cfg` will go through all the urls and
creates a static version of each page.  It places all the necessary files in
a folder which can then simply be uploaded to a static web server or whatever.
This is basically a wrapper around the Frozen-Flask python package.  Which is
probably the reasoning behind the name 'chill'.
