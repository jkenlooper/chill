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
the `insert_query` function. This function takes the filename of the sql
query you want to use which will then have its results put in for the value.

    homepage = insert_node(name='homepage', value=None)

Set the homepage node to be viewable at the url '/'.  If there was a value set
it would simply show that value at the url. 

    insert_route(path='/', node_id=homepage)

Set the homepage node's value be whatever else is linked to it.  The
`insert_query` takes the filename of the sql query you want to use which
will then have its results put in for the value. By using the
'select_link_node_from_node.sql' file (located in the chill package) it will
find all the other node's that have been linked to it.

    insert_query(name='select_link_node_from_node.sql', node_id=homepage)

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
