import unittest
import tempfile
import flask
import os

from chill.app import make_app, db
from chill.database import ( init_db,
        add_node_to_node,
        path_for_node,
        add_node_for_route,
        add_template_for_node )

class ChillTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp_template_dir = tempfile.mkdtemp()
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)
        self.app = make_app(CHILL_DATABASE_URI=self.tmp_db.name,
                TEMPLATE_FOLDER=self.tmp_template_dir,
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

class SelectSQL(ChillTestCase):
    def test_some_data(self):
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

