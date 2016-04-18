import os
from flask import current_app, g
from chill.app import db
from cache import cache
from PIL import Image

CHILL_CREATE_TABLE_FILES = (
        'create_chill.sql',
        'create_node_node.sql',
        'create_node.sql',
        'create_route.sql',
        'create_query.sql',
        'create_template.sql'
        )

CHILL_CREATE_PICTURE_TABLE_FILES = (
    'create_picture.sql',
    'create_image.sql',
    'create_srcset.sql',
    'create_staticfile.sql',
    'create_node_picture.sql'
    )


def init_db():
    """Initialize a new database with the default tables for chill.
    Creates the following tables:
    Chill
    Node
    Node_Node
    Route
    Query
    Template
    """
    with current_app.app_context():
        #db = get_db()
        c = db.cursor()

        for filename in CHILL_CREATE_TABLE_FILES:
            c.execute(fetch_query_string(filename))

        db.commit()

def rowify(l, description):
    d = []
    col_names = []
    if l != None and description != None:
        col_names = [x[0] for x in description]
        for row in l:
            d.append(dict(zip(col_names, row)))
    return (d, col_names)

def _fetch_sql_string(file_name):
    with current_app.open_resource(os.path.join('queries', file_name), mode='r') as f:
        return f.read()

def fetch_query_string(file_name):
    content = current_app.queries.get(file_name, None)
    if content != None:
        return content
    current_app.logger.info( "queries file: '%s' not available. Checking file system..." % file_name )

    #folder = current_app.config.get('THEME_SQL_FOLDER', '')
    #file_path = os.path.join(os.path.abspath('.'), folder, file_name)
    folder = current_app.config.get('THEME_SQL_FOLDER')
    file_path = os.path.join(folder, file_name)
    if os.path.isfile(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    else:
        # fallback on one that's in app resources
        return _fetch_sql_string(file_name)

def insert_node(**kw):
    "Insert a node with a name and optional value. Return the node id."
    with current_app.app_context():
        c = db.cursor()
        c.execute(fetch_query_string('insert_node.sql'), kw)
        node_id = c.lastrowid
        db.commit()
        return node_id

def insert_node_node(**kw):
    """
    Link a node to another node. node_id -> target_node_id.  Where `node_id` is
    the parent and `target_node_id` is the child.
    """
    with current_app.app_context():
        insert_query(name='select_link_node_from_node.sql', node_id=kw.get('node_id'))
        c = db.cursor()
        c.execute(fetch_query_string('insert_node_node.sql'), kw)
        db.commit()

def delete_node(**kw):
    """
    Delete a node by id.
    """
    with current_app.app_context():
        c = db.cursor()
        c.execute(fetch_query_string('delete_node_for_id.sql'), kw)
        db.commit()

def select_node(**kw):
    """
    Select node by id.
    """
    with current_app.app_context():
        c = db.cursor()
        result = c.execute(fetch_query_string('select_node_from_id.sql'), kw).fetchall()
        (result, col_names) = rowify(result, c.description)
        return result

def insert_route(**kw):
    """
    `path` - '/', '/some/other/path/', '/test/<int:index>/'
    `node_id`
    `weight` - How this path is selected before other similar paths
    `method` - 'GET' is default.
    """
    binding = {
            'path': None,
            'node_id': None,
            'weight': None,
            'method': "GET"
            }
    binding.update(kw)
    with current_app.app_context():
        c = db.cursor()
        c.execute(fetch_query_string('insert_route.sql'), binding)
        db.commit()

def add_template_for_node(name, node_id):
    "Set the template to use to display the node"
    with current_app.app_context():
        c = db.cursor()
        c.execute(fetch_query_string('insert_template.sql'),
                {'name':name, 'node_id':node_id})
        c.execute(fetch_query_string('select_template.sql'),
                {'name':name, 'node_id':node_id})
        result = c.fetchone()
        if result:
            template_id = result[0]
            c.execute(fetch_query_string('update_template_node.sql'),
                    {'template':template_id, 'node_id':node_id})
        db.commit()


def insert_query(**kw):
    """
    Insert a query name for a node_id.
    `name`
    `node_id`

    Adds the name to the Query table if not already there. Sets the query field
    in Node table.
    """
    with current_app.app_context():
        c = db.cursor()
        result = c.execute(fetch_query_string('select_query_where_name.sql'), kw).fetchall()
        (result, col_names) = rowify(result, c.description)
        if result:
            kw['query_id'] = result[0].get('id')
        else:
            c.execute(fetch_query_string('insert_query.sql'), kw)
            kw['query_id'] = c.lastrowid
        c.execute(fetch_query_string('insert_query_node.sql'), kw)
        db.commit()

def init_picture_tables():
    """Create optional picture and staticfile database tables:
    Picture
    Image
    Srcset
    StaticFile
    Node_Picture
    """
    with current_app.app_context():
        c = db.cursor()

        for filename in CHILL_CREATE_PICTURE_TABLE_FILES:
            c.execute(fetch_query_string(filename))

        db.commit()


def add_picture_for_node(node_id, filepath, **kw):
    """
    Add a picture for a node id. This adds to the Image, StaticFile, Picture, ... tables.
    The `filepath` must be an image file within the media folder.
    width and height are deduced from the image.
    Other attributes that should be associated with the picture can be passed in:
    title
    description
    author
    (and others, some have not been implemented)
    """

    with current_app.app_context():
        c = db.cursor()


        # media folder needs to be set
        media_folder = current_app.config.get('MEDIA_FOLDER')
        if not media_folder:
            current_app.logger.warn('No MEDIA_FOLDER set in config.')
            return False

        # filepath needs to exist
        media_filepath = os.path.join(media_folder, filepath)
        if not os.path.exists(media_filepath):
            current_app.logger.warn('filepath not exists: {0}'.format(media_filepath))
            return False

        # file needs to be an image
        try:
            img = Image.open(media_filepath)
        except IOError as err:
            current_app.logger.warn(err)
            return False


        (width, height) = img.size


        c.execute(fetch_query_string("insert_staticfile.sql"), {
            'path':filepath
            })
        staticfile = c.lastrowid

        c.execute(fetch_query_string("insert_image.sql"),{
            'width': width,
            'height': height,
            'staticfile': staticfile
            })
        image = c.lastrowid

        c.execute(fetch_query_string("insert_picture.sql"),{
            'picturename': filepath,
            'title': kw.get('title', None),
            'description': '',
            'author': None,
            'created': '',
            'image': image
            })
        picture = c.lastrowid

        c.execute(fetch_query_string("insert_node_picture.sql"),{
            'node_id': node_id,
            'picture': picture
            })

        db.commit()

        insert_query(name='select_picture_for_node.sql', node_id=node_id)

        db.commit()

def link_picturename_for_node(node_id, picturename, **kw):
    """
    Link a picture for a node id.  Use this if the picture has already been added to the database.
    """
    with current_app.app_context():
        c = db.cursor()

        result = c.execute(fetch_query_string("select_picture_by_name.sql"), {
            'picturename':picturename
            })
        (result, col_names) = rowify(result, c.description)
        if result:
            picture = result[0].get('id')
        else:
            current_app.logger.warn('picture by name:"{0}" is not in database.'.format(filepath))
            return False

        c.execute(fetch_query_string("insert_node_picture.sql"),{
            'node_id': node_id,
            'picture': picture
            })

        db.commit()

        insert_query(name='select_picture_for_node.sql', node_id=node_id)

        db.commit()
