import unittest
import tempfile
import flask
import os

from chill.app import make_app, db
from chill.database import ( init_db,
        normalize,
        add_node_to_node,
        link_node_to_node,
        path_for_node,
        add_node_for_route,
        fetch_sql_string,
        add_selectsql_for_node,
        add_template_for_node )

class ChillTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp_template_dir = tempfile.mkdtemp()
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)
        self.app = make_app(CHILL_DATABASE_URI=self.tmp_db.name,
                TEMPLATE_FOLDER=self.tmp_template_dir,
                SELECTSQL_FOLDER=self.tmp_template_dir,
                DEBUG=True)

    def tearDown(self):
        """Get rid of the database and templates after each test."""
        self.tmp_db.unlink(self.tmp_db.name)
       
        # Walk and remove all files and directories in the created temp directory
        for root, dirs, files in os.walk(self.tmp_template_dir, topdown=False):
            for name in files:
                #self.app.logger.debug('removing: %s', os.path.join(root, name))
                os.remove(os.path.join(root, name))
            for name in dirs:
                #self.app.logger.debug('removing: %s', os.path.join(root, name))
                os.rmdir(os.path.join(root, name))

        os.rmdir(self.tmp_template_dir)

class SimpleCheck(ChillTestCase):
    def test_db(self):
        """Check usage of db"""
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                cursor = db.cursor()
                cursor.execute("""insert into Node (name, left, right, value) values (:name, 0, 0, :value)""", {"name": "bill", "value": "?"})
                db.commit()

                #rv = c.get('/bill', follow_redirects=True)
                #assert '?' in rv.data

class Route(ChillTestCase):
    def test_paths(self):
        with self.app.app_context():
            init_db()

            top_id = add_node_to_node(1, 'top', value='hello')
            add_node_for_route('/', top_id)

            one_id = add_node_to_node(1, 'one', value='1')
            add_node_for_route('/one', one_id)
            two_id = add_node_to_node(one_id, 'two', value='2')
            add_node_for_route('/one/two', two_id)
            three_id = add_node_to_node(two_id, 'three', value='3')
            add_node_for_route('/one/two/three', three_id)
            add_node_for_route('/one/two/other_three', three_id)

            with self.app.test_client() as c:

                rv = c.get('/', follow_redirects=True)
                assert 'hello' == rv.data
                rv = c.get('/.', follow_redirects=True)
                assert 'hello' == rv.data
                rv = c.get('/index.html', follow_redirects=True)
                assert 'hello' == rv.data
                rv = c.get('', follow_redirects=True)
                assert 'hello' == rv.data

                rv = c.get('/one', follow_redirects=True)
                assert '1' == rv.data
                rv = c.get('/one/', follow_redirects=True)
                assert '1' == rv.data
                rv = c.get('/one/.', follow_redirects=True)
                assert '1' == rv.data
                rv = c.get('/one/index.html', follow_redirects=True)
                assert '1' == rv.data
                rv = c.get('/one/two', follow_redirects=True)
                assert '2' == rv.data
                rv = c.get('/one/foo/../two', follow_redirects=True)
                assert '2' == rv.data
                rv = c.get('/./one//two', follow_redirects=True)
                assert '2' == rv.data
                rv = c.get('/one/two/', follow_redirects=True)
                assert '2' == rv.data
                rv = c.get('/one/two/index.html', follow_redirects=True)
                assert '2' == rv.data
                rv = c.get('/one/two/three', follow_redirects=True)
                assert '3' == rv.data
                rv = c.get('/one/two/other_three', follow_redirects=True)
                assert '3' == rv.data
                rv = c.get('/one/two/other_three/index.html', follow_redirects=True)
                assert '3' == rv.data
                rv = c.get('/one///////two/other_three/index.html', follow_redirects=True)
                assert '3' == rv.data
                rv = c.get('/one/two/other_three/nothing', follow_redirects=True)
                assert 404 == rv.status_code

class Populate(ChillTestCase):
    def test_add_single_nodes(self):
        """Check usage of nested set sql adding"""
        with self.app.app_context():
            init_db()

            ice_cream_id = add_node_to_node(1, 'ice_cream', value='yummy')
            blueberry_id = add_node_to_node(ice_cream_id, 'ice_cream blueberry', value='blueberry')
            raspberry_id = add_node_to_node(ice_cream_id, 'ice_cream raspberry', value='raspberry')
            candy_id = add_node_to_node(1, 'candy', value='yummy candy')
            strawberry_id = add_node_to_node(ice_cream_id, 'ice_cream strawberry', value='strawberry')
            for i in range(0, 33):
                sub_id = add_node_to_node(strawberry_id, 'sub%i' % i, value='strawberry sub %i' % i)
                if sub_id % 5:
                    other_id = add_node_to_node(sub_id, 'other%i' % i, value='other')
                    another_id = add_node_to_node(blueberry_id, 'blueberry_other%i' % i, value='other')
                    extra_id = add_node_to_node(1, 'extra%i' % i, value='other')
                if sub_id % 7:
                    sev_id = add_node_to_node(candy_id, 'seven other%i' % i, value='other')
            banana_id = add_node_to_node(1, 'banana', value='')
            orange_id = add_node_to_node(1, 'orange', value='')
            eggplant_id = add_node_to_node(1, 'eggplant', value='')

            orange2_id = add_node_to_node(orange_id, 'color-is-orange', value='')

            assert path_for_node(orange2_id) == u'root/orange/color-is-orange'
            assert path_for_node(eggplant_id) == u'root/eggplant'
            assert path_for_node(strawberry_id) == u'root/ice_cream/ice_cream strawberry'



class NothingConfigured(ChillTestCase):
    def test_empty(self):
        """Show something for nothing"""
        with self.app.test_client() as c:
            rv = c.get('/')
            assert 404 == rv.status_code
            rv = c.get('/index.html')
            assert 404 == rv.status_code
            rv = c.get('/something/')
            assert 404 == rv.status_code
            rv = c.get('/something/test.txt', follow_redirects=True)
            assert 404 == rv.status_code
            rv = c.get('/static/afile.txt', follow_redirects=True)
            assert 404 == rv.status_code
            rv = c.get('/something/nothing/')
            assert 404 == rv.status_code


            rv = c.get('/chill/')
            assert 'Llamas' in rv.data
            rv = c.get('/chill/index.html')
            assert 'Llamas' in rv.data

class SQL(ChillTestCase):
    def test_link(self):
        """
        Link to any node 
        """
        with self.app.app_context():
            init_db()
            a = add_node_to_node(1, 'a')
            b = add_node_to_node(1, 'b')
            c = add_node_to_node(1, 'c')
            aa = add_node_to_node(a, 'aa')
            bb = add_node_to_node(b, 'bb')
            cc = add_node_to_node(c, 'cc')

            # test for these
            link_node_to_node(a, b)
            link_node_to_node(a, cc)

            link_node_to_node(b, cc)
            link_node_to_node(b, a)
            link_node_to_node(b, aa)

            c = db.cursor()
            result = c.execute(fetch_sql_string('select_link_node_from_node.sql'), {'node_id': a}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('node_id', None) for x in result]
            assert cc in result
            assert b in result
            assert a not in result
            #self.app.logger.debug(result)

    def test_template(self):
        with self.app.app_context():
            init_db()

            a = add_node_to_node(1, 'a')
            add_template_for_node('template_a.html', a)
            aa = add_node_to_node(1, 'aa')
            add_template_for_node('template_a.html', aa)
            b = add_node_to_node(1, 'b')
            add_template_for_node('template_b.html', b)
            c = add_node_to_node(1, 'c')
            add_template_for_node('template_c.html', c)
            d = add_node_to_node(1, 'd')
            e = add_node_to_node(1, 'e')

            c = db.cursor()
            result = c.execute(fetch_sql_string('select_template_from_node.sql'), {'node_id': a}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert result[0] == 'template_a.html'

            # another node that uses the same template
            c = db.cursor()
            result = c.execute(fetch_sql_string('select_template_from_node.sql'), {'node_id': aa}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert result[0] == 'template_a.html'

            # can overwrite what node is tied to what template
            add_template_for_node('template_over_a.html', a)

            c = db.cursor()
            result = c.execute(fetch_sql_string('select_template_from_node.sql'), {'node_id': a}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert result[0] == 'template_over_a.html'

            # this one still uses the other template
            c = db.cursor()
            result = c.execute(fetch_sql_string('select_template_from_node.sql'), {'node_id': aa}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert result[0] == 'template_a.html'

    def test_selectsql(self):

        with self.app.app_context():
            init_db()

            # a node can have multiple selectsql's
            a = add_node_to_node(1, 'a')
            add_selectsql_for_node('simple_a.sql', a)
            add_selectsql_for_node('simple_aa.sql', a)

            # or just one
            b = add_node_to_node(1, 'b')
            add_selectsql_for_node('simple_b.sql', b)

            # other nodes can use the same
            d = add_node_to_node(1, 'd')
            add_selectsql_for_node('simple_a.sql', d)
            e = add_node_to_node(1, 'e')
            add_selectsql_for_node('simple_a.sql', e)

            c = db.cursor()

            result = c.execute(fetch_sql_string('select_selectsql_from_node.sql'), {'node_id': a}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 2
            assert 'simple_a.sql' in result
            assert 'simple_aa.sql' in result

            result = c.execute(fetch_sql_string('select_selectsql_from_node.sql'), {'node_id': b}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert 'simple_b.sql' in result

            result = c.execute(fetch_sql_string('select_selectsql_from_node.sql'), {'node_id': d}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert 'simple_a.sql' in result

class SelectSQL(ChillTestCase):
    def test_empty(self):
        """
        """
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                # Not setting a value for a node
                four_id = add_node_to_node(1, 'empty')
                add_node_for_route('/empty', four_id)

                # When no value is set and no SelectSQL or Template is set
                rv = c.get('/empty', follow_redirects=True)
                assert 404 == rv.status_code

    def test_flat_data_without_templates(self):
        """
        """

        f = open(os.path.join(self.tmp_template_dir, 'simple.sql'), 'w')
        f.write("""
          select 'yup', 'pretty', 'darn', 'simple';
          """)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'by_name.sql'), 'w')
        f.write("""
          select n.id as node_id, n.name as name, n.value as value from Node as n where name = :name;
          """)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'by_node_id.sql'), 'w')
        f.write("""
          select n.id as node_id, n.name as name, n.value as value from Node as n where id = :node_id;
          """)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'by_value.sql'), 'w')
        f.write("""
          select n.id as node_id, n.name as name, n.value as value from Node as n where value = :value;
          """)
        f.close()


        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                colors = add_node_to_node(1, 'colors')
                i=0
                color_nodes = []
                for col in ('red', 'blue', 'yellow'):
                    color_nodes.append(add_node_to_node(colors, 'color-%i' % i, value=col))
                    i += 1

                llamas = add_node_to_node(1, 'llamas', value=None)
                add_node_for_route('/llamas', llamas)
                add_selectsql_for_node('select_immediate_children.sql', llamas)
                i=0
                for x in ('a','b','c'):
                    llama = add_node_to_node(llamas, 'llama-%s' % x, value=x)
                    add_node_to_node(llama, 'title', value="Llama %s" % x)
                    color = add_node_to_node(llama, 'color')
                    # Link the llama to it's color
                    link_node_to_node(color, color_nodes[i])
                    i += 1

                rv = c.get('/llamas', follow_redirects=True)
                self.app.logger.debug(rv.data)
                assert 200 == rv.status_code

    def test_nested_data_without_templates(self):
        """
        TODO: messy...
        """

        f = open(os.path.join(self.tmp_template_dir, 'simple.sql'), 'w')
        f.write("""
          select 'yup', 'I reckon';
          """)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'by_name.sql'), 'w')
        f.write("""
          select n.id as node_id, n.name as name, n.value as value from Node as n where name = :name;
          """)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'by_node_id.sql'), 'w')
        f.write("""
          select n.id as node_id, n.name as name, n.value as value from Node as n where id = :node_id;
          """)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                # Not setting a value for a node
                four_id = add_node_to_node(1, 'empty')
                add_node_for_route('/empty', four_id)

                # When no value is set and no SelectSQL or Template is set
                rv = c.get('/empty', follow_redirects=True)
                assert 404 == rv.status_code


                page_id = add_node_to_node(1, 'page')
                add_node_for_route('/page', page_id)
                add_node_to_node(page_id, 'title', value="test page title")
                add_node_to_node(page_id, 'description', value="This is a short description for the test page")
                add_node_to_node(page_id, 'body', value='<p>yup. "this is just a test"</p>')
                add_node_to_node(page_id, 'body', value='<p>Same name.</p>')

                menu_id = add_node_to_node(1, 'menu')
                menu_item1 = add_node_to_node(menu_id, 'menuitem1')
                add_node_to_node(menu_item1, 'title', value='menu title for test page')
                add_node_to_node(menu_item1, 'link', value='/page')
                add_node_to_node(menu_item1, 'target', value='_blank')

                #add_selectsql_for_node('simple.sql', page_id)
                add_selectsql_for_node('select_immediate_children.sql', page_id)

                #add_template_for_node('a_page_template.html', page_id)

                rv = c.get('/page', follow_redirects=True)
                self.app.logger.debug(rv.data)
                assert 200 == rv.status_code


#        f = open(os.path.join(self.tmp_template_dir, 'base.html'), 'w')
#        f.write("""
#          <!doctype html>
#          <html><head><title>test</title></head>
#          <body>
#          <div>{% block menu %}
#              <ul>
#                  {% for menuitem in menu %}
#                    <li>
#                      <a href="{{ menuitem.link }}" target="{{ menuitem.target }}">
#                        {{menuitem.title}}
#                      </a>
#                    </li>
#                  {% endfor %}
#                  </ul>
#          {% endblock %}</div>
#          <div>{% block content %}{% endblock %}</div>
#          </body>
#          </html>
#          """)
#        f.close()
#
#        f = open(os.path.join(self.tmp_template_dir, 'a_page_template.html'), 'w')
#        f.write("""
#          {% extends "base.html" %}
#          {% block content %}
#          <code>a page template</code>
#          <h1>{{ value.title }}</h1>
#          {{ value.body }}
#          {% endblock %}
#          """)
#        f.close()

class Template(ChillTestCase):
    def test_some_template(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, 'base.html'), 'w')
        f.write("""
          <!doctype html>
          <html><head><title>test</title></head>
          <body>
          <div>{% block content %}{% endblock %}</div>
          </body>
          </html>
          """)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'template_a.html'), 'w')
        f.write("""
          {% extends "base.html" %}
          {% block content %}
          <h1>template_a</h1>
          {{ value }}
          {% endblock %}
          """)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'template_b.html'), 'w')
        f.write("""
          {% extends "base.html" %}
          {% block content %}
          <h1>template_b</h1>
          {{ value }}
          {% endblock %}
          """)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                test_id = add_node_to_node(1, 'test one', value='testing one')
                add_node_for_route('/test/1', test_id)
                add_template_for_node('template_a.html', test_id)

                rv = c.get('/test/1', follow_redirects=True)
                assert 'testing one' in rv.data

                a_id = add_node_to_node(1, 'a', value='apple')
                add_node_for_route('/fruit/a', a_id)
                add_template_for_node('template_a.html', a_id)

                rv = c.get('/fruit/a', follow_redirects=True)
                assert 'apple' in rv.data
                assert 'template_a' in rv.data

                b_id = add_node_to_node(1, 'b', value='banana')
                add_template_for_node('template_b.html', b_id)
                o_id = add_node_to_node(1, 'orange', value='orange')
                add_template_for_node('template_b.html', o_id)
                
                eggplant_id = add_node_to_node(1, 'eggplant', value='eggplant')
                add_template_for_node('template_b.html', eggplant_id)

                # overwrite ( fruit/a use to be set to template_a.html )
                add_template_for_node('template_b.html', a_id)

                rv = c.get('/fruit/a', follow_redirects=True)
                assert 'apple' in rv.data
                assert 'template_b' in rv.data

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NothingConfigured))
    suite.addTest(unittest.makeSuite(SimpleCheck))
    return suite


if __name__ == '__main__':
    unittest.main()

