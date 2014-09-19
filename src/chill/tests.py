import unittest
import tempfile
import flask

from chill.app import make_app, db
from chill.database import init_db, add_node_to_node, path_for_node, add_node_for_route

class ChillTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)
        self.app = make_app(CHILL_DATABASE_URI=self.tmp_db.name, DEBUG=True)

    def tearDown(self):
        """Get rid of the database again after each test."""
        self.tmp_db.unlink(self.tmp_db.name)

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
            flask.current_app.logger.debug(db.execute("select * from route").fetchall())

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

class ContextData(ChillTestCase):
    def test_some_data(self):
        """
        Build some example context data that works with a cascade...
        """

class Template(ChillTestCase):
    def test_some_template(self):
        """
        """

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NothingConfigured))
    suite.addTest(unittest.makeSuite(SimpleCheck))
    return suite


if __name__ == '__main__':
    unittest.main()

