# Operate Mode Tutorial

Making changes to the database that Chill uses can be done through the `chill
operate` command.  It is not required to use the operate command in order to
use Chill, but it makes doing some common things easier.

## Initialize a blank database

To start from scratch, create an empty directory and within initialize a new
Chill database.

    mkdir llama;
    cd llama;
    chill init;

That creates the necessary *site.cfg* as well as a sqlite database file named
*db*. By default the `init` creates an initial page with some exciting content.
To run the `operate` sub command there only needs to be a *site.cfg*.  For now
delete the generated *db* file and homepage template. And create an empty
database to start.

    rm db;
    rm templates/homepage.html;
    chill operate;

The operate command shows a numbered menu.  To create the database and empty
tables used by chill; pick option **chill.database functions** which lists some
of the python function in the chill/database.py file.  Then pick the
**init_db** option and confirm. To exit the menu just hit return with no option
picked. That brings you back to the previous menu which happens to be the main
menu.  Hit return again and it exits the interactive script.

Now the database file is created again, but this time it is completely empty
and running `chill run` will only show 'not found' pages.

## Add a route to a node with a value

And now for something really basic.  Lets set it up to show a 'Hello, World!'
message if visiting the URL '/' in a browser. First, we'll add a node with the
name 'greeting' and set the value to 'Hello, World!'.

    chill operate;
    # Pick option 1) chill.database functions
    # Pick option 3) insert_node
    # Enter the name: greeting
    # Enter the value: Hello, World!

After hitting enter it pops back to the previous menu.  Note that it also
displays some information of the node it just added to the database.  Depending
on if the Node table was empty it likely has the node id of 1.

Now create a route to this node in order to display it's value.  Within the
**chill.database functions** menu which should still be active.

    # Pick option 5) insert_route
    # Enter the path: /
    # Enter nothing for weight and method to use the default
    # Enter 'greeting' when asked for the node to use
    
Done.  Hit enter a couple of times to exit out of each menu.  Now `chill run`
and visit the http://localhost:5000/ to see the greeting.

You can also review what is in the database if you're curious and familiar with
SQL.

## Summary

This is a rather simple demo of the `chill operate` command and initializing an
empty database for Chill.  Check the other tutorials for more advanced stuff
that involve training llamas and avoidance of spit.
