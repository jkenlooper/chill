=========================================
Cascading, Highly Irrelevant, Lost Llamas
=========================================

*Or, just chill.*

This is yet another static website generator.  What's different is that it uses
a simple way of managing the content for the website. All page content is in a
data directory with each page represented as the directory name.  All the page
content is either a separate file or is in a yaml file.  A page accesses it's
data by first looking for it in it's own directory and then all of it's parent
directories in order.  So, setting a file called `sitetitle.txt` in the top
level will be used by all pages in the site unless those pages also have a file
with that name in their directory.

Templates are also used for a page in a similiar cascading manner.  Each page
can override any part of a template by just including it in it's own directory.
Any sub pages of that page directory will also use that template.

Mustache Templates
------------------

Chill uses mustache templates as they are language agnostic, logicless, and
pretty simple to use.  This is important as chill was designed to be simple and
as future-proof as possible when it comes to the actual website *guts*.  All
chill does is load up the mustache template or templates for a page and render
it with the data it finds.  This functionality could easily be improved on or
replaced with any other software without need to modify any of the *guts*.

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

A buildout config file will be needed to 'buildout' the site. At the least this
will need to specify where the data and themes directories are located.  A
sample (and minimal) buildout.cfg can be seen below::

    [buildout]
    parts = 
            site_cfg
            scripts

    [scripts]
    # installs the run and freeze scripts in the bin directory
    recipe = zc.recipe.egg:scripts
    eggs = chill
    # The run and freeze scripts need this site.cfg file path sent to them.
    arguments = '${buildout:parts-directory}/site.cfg' 

    [site_cfg]
    # Creates the site.cfg in the parts directory
    recipe = collective.recipe.template
    input = inline:
        HOST = '127.0.0.1' # default
        PORT = 5000 # default
        FREEZER_DESTINATION = "${buildout:directory}/frozen"
        THEME_PATH = "${buildout:directory}/themes"
        DATA_PATH = "${buildout:directory}/data"
    output = ${buildout:parts-directory}/site.cfg

If you have buildout installed on your system then just run the command:
``buildout -c buildout.cfg`` or just ``buildout`` as it defaults to using the
config file buildout.cfg.  Buildout will create a few extra directories
including a bin directory that will have the run and freeze scripts in it.  

Buildout can also be installed on your system with ``pip install zc.buildout``

bin/run
*******

This script is used when you are developing your site's content and structure.
It stays in the foreground and logs access to the default host and port which
is http://localhost:5000 . This really is just designed to run on your
development machine and not under a production environment.

bin/freeze
**********

This is basically a wrapper around the Frozen-Flask python package that freezes
your site into static files ready to be uploaded to a server or something.
