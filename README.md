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

**Review the docs for more.** Some helpful guides and such are in the docs/
folder.  They might even make some sense, but that is not a guarantee.  You can
also read through the tests.py file within the chill package.


## Installing

This latest version is not published so I recomend installing with pip in
editable mode.  I install it by `pip install -e .` after cloning the
repository.  This will create a script called `chill`.  Type `chill --help` for
help on using it.  It will need a config file and such.  I recommend creating
an empty directory and running `chill init` within it.  That will create
a site.cfg config file and the bare minimum to show a homepage.  Run the `chill
run --config site.cfg` and visit http://localhost:5000 with your browser.


## Static site generator

The command `chill freeze --config site.cfg` will go through all the urls and
creates a static version of each page.  It places all the necessary files in
a folder which can then simply be uploaded to a static web server or whatever.
This is basically a wrapper around the Frozen-Flask python package.  Which is
probably the reasoning behind the name 'chill'.
