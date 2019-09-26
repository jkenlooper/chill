[![Build Status](https://travis-ci.org/jkenlooper/chill.svg?branch=mustached-rival)](https://travis-ci.org/jkenlooper/chill)

# Cascading, Highly Irrelevant, Lost Llamas

*Or, just chill.*  This is a **database driven web application framework in
[Flask](https://palletsprojects.com/p/flask/)** and it can be used to create
static or dynamic web sites.

This involves creating custom SQL queries to pull data from a database and uses
[Jinja2](https://palletsprojects.com/p/jinja/) HTML templates to populate pages
for a website.  Chill can create static files for the website or can run as
a Flask app and build pages on request.

Chill is database driven when it comes to handling http requests.  Each http
request uses data from the database when determining what content to show on the
page as well as what HTML templates to use.  Content for a page can come from
other database queries and can recursively call other queries when populating
the page.

## Installing

Chill can be installed via pip.
```bash
pip install chill
```

Or from within this cloned project; install with pip in editable mode.  It is
recommended to setup a virtual environment first with `virtualenv . -p python3`
command.
```bash
pip install -e .
```

This will create a script called `chill`.  Type `chill --help` for help on using
it.  It will need a config file and such.  I recommend creating an empty
directory and running `chill init` within it.  That will create a `site.cfg`
config file and the bare minimum to show a homepage.  Run the 
`chill run --config site.cfg` 
and visit http://localhost:5000 with your browser.

## Quick start

Run the `chill init` script in an empty directory and it will create a minimal
starting point for using Chill. The `site.cfg` created will have comments on each
configuration value.  The `chill run --config site.cfg` will run the app in the
foreground at the http://localhost:5000/ URL. Notice that the script also
creates a sqlite database in that directory.  This database is what the script
uses to display the pages in a site.

**Review the docs for more.** Some helpful guides and such are in the
[docs/](docs/) folder.  The [tests.py](src/chill/tests.py) file within the chill
package is also a good resource.

## Static site generator

The command `chill freeze --config site.cfg` will go through all the URLs and
create a static version of each page.  It places all the necessary files in
a folder which can then be uploaded to a static web server.  This is a wrapper
around the Frozen-Flask python package.  Which is partly the inspiration behind
the name 'chill'.  Also, llamas are cool and have two 'l's like chill.

## Websites using chill

* [Puzzle Massive](http://puzzle.massive.xyz/) - 
    Massively Multiplayer Online Jigsaw Puzzles
* [Web of Tomorrow](http://www.weboftomorrow.com/) -
    A web developer's website about web development
* [Awesome Mud Works](http://awesomemudworks.com/) -
    Pottery studio in Salt Lake City, Utah

A cookiecutter for making a _chill_ website also exists.  Checkout the
[cookiecutter-website](https://github.com/jkenlooper/cookiecutter-website/)
project to get started.

## Docker

I've included a `Dockerfile` which can be used when creating a container for
chill.  See the 
[guide on using chill with docker](docs/docker-container-usage.md).

