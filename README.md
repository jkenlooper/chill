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

This latest version is not published so I recommend installing with pip in
editable mode.  I install it by 
`pip install -e . -r requirements.txt`
after cloning the
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

## Docker

*TODO: publish the chill image*

Chill can also be run as a docker container.  Download the chill image or build
it using the Dockerfile.  The chill image sets the entrypoint to be the chill
command and copies the context to the container so you can use `docker run`
commands to work with chill like it was installed on the host machine.

These are just some example commands to give an idea on how to do development
with a container.  In all of them the `--rm` is being used since there is no
need to keep the container around after the command finishes.  The `-v` option
is to allow the working directory to be bind-mounted to the host.  It should
contain all the normal files for chill including the sqlite3 database.

Also note that when developing it like this the chill app won't be directly
accessible under the PORT set in site.cfg.  In the example commands I set the
port mapping (`-p 8080:5000`).  It will need to have it's site.cfg HOST updated
to be '0.0.0.0' or have some other kind of networking setup.

### Start in the foreground.

This is equivalent to using `chill run` within `$HOME/example-website/`, but
maps the port from 8080 on the host to port 5000 for the chill app.  Then you
can visit the website via http://localhost:8080 which will be running in
a docker container.  You will need to make sure that the site.cfg has been
updated to set the HOST to be external (0.0.0.0), or you won't be able to hit
it with your web browser.

```
docker run --rm -p 8080:5000 -v $HOME/example-website/:/usr/run/ chill run
```

### Serve the app in daemon mode

Same as using `chill serve`.  Uses the `-d` option for running the container in
the background.

```
docker run -d --rm -p 8080:5000 -v $HOME/example-website/:/usr/run/ chill serve
```

### Run operate sub command

Same as using `chill operate`.  Here the `-it` option is used so the operate
functions correctly since it needs user input.

```
docker run -it --rm -v $HOME/example-website/:/usr/run/ chill operate
```
