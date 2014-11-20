import unittest
import tempfile
import os
import json

from chill.app import make_app, db
from chill.database import ( init_db,
        normalize,
        insert_node,
        insert_node_node,
        insert_route,
        insert_selectsql,
        fetch_sql_string,
        fetch_selectsql_string,
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
                cursor.execute("""insert into Node (name, value) values (:name, :value)""", {"name": "bill", "value": "?"})
                db.commit()

                #rv = c.get('/bill', follow_redirects=True)
                #assert '?' in rv.data

class Route(ChillTestCase):
    def test_paths(self):
        with self.app.app_context():
            init_db()

            top_id = insert_node(name='top', value='hello')
            insert_route(path='/', node_id=top_id)

            one_id = insert_node(name='one', value='1')
            insert_route(path='/one/', node_id=one_id)
            two_id = insert_node(name='two', value='2')
            insert_route(path='/one/two/', node_id=two_id)
            three_id = insert_node(name='three', value='3')
            insert_route(path='/one/two/three/', node_id=three_id)
            insert_route(path='/one/two/other_three/', node_id=three_id)

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

    def test_single_rule(self):
        with self.app.app_context():
            init_db()

            id = insert_node(name='top', value='hello')
            insert_route(path='/<int:count>/', node_id=id)

            with self.app.test_client() as c:

                rv = c.get('/', follow_redirects=True)
                assert 404 == rv.status_code
                rv = c.get('/1', follow_redirects=True)
                assert 'hello' == rv.data
                rv = c.get('/1/', follow_redirects=True)
                assert 'hello' == rv.data
                rv = c.get('////1/', follow_redirects=True)
                assert 'hello' == rv.data
                rv = c.get('/1/index.html', follow_redirects=True)
                assert 'hello' == rv.data
                rv = c.get('/1/index.html/not', follow_redirects=True)
                assert 404 == rv.status_code

    def test_multiple_rules(self):
        with self.app.app_context():
            init_db()

            id = insert_node(name='fruit', value='fruit')
            insert_route(path='/fruit/<anything>/', node_id=id)
            id = insert_node(name='vegetables', value='vegetables')
            insert_route(path='/vegetables/<anything>/', node_id=id)

            with self.app.test_client() as c:

                rv = c.get('/fruit', follow_redirects=True)
                assert 404 == rv.status_code
                rv = c.get('/fruit/pear/', follow_redirects=True)
                assert 'fruit' == rv.data
                rv = c.get('/vegetables', follow_redirects=True)
                assert 404 == rv.status_code
                rv = c.get('/vegetables/pear/', follow_redirects=True)
                assert 'vegetables' == rv.data

    def test_weight(self):
        with self.app.app_context():
            init_db()

            id = insert_node(name='a', value='a')
            insert_route(path='/<path:anything>/', node_id=id, weight=1)
            id = insert_node(name='aardvark', value='aardvark')
            insert_route(path='/animals/<anything>/', node_id=id, weight=1)
            id = insert_node(name='b', value='b')
            insert_route(path='/<path:something>/', node_id=id, weight=2)

            with self.app.test_client() as c:

                rv = c.get('/apple', follow_redirects=True)
                assert 'b' == rv.data
                rv = c.get('/animals/ape', follow_redirects=True)
                assert 'aardvark' == rv.data
                rv = c.get('/animals/ape/1', follow_redirects=True)
                assert 'b' == rv.data
                rv = c.get('/vegetables', follow_redirects=True)
                assert 'b' == rv.data
                rv = c.get('/vegetables/pear/', follow_redirects=True)
                assert 'b' == rv.data


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

class SQL(ChillTestCase):
    def test_insert_one_node(self):
        """
        Add a node
        """
        with self.app.app_context():
            init_db()
            c = db.cursor()
            c.execute(fetch_sql_string('insert_node.sql'), {'name': 'a', 'value':'apple'})
            a = c.execute(fetch_sql_string('select_max_id_node.sql')).fetchone()[0]
            db.commit()

            result = c.execute('select * from Node where id = :id;', {'id':a}).fetchall()
            (result, col_names) = normalize(result, c.description)
            assert len(result) == 1
            r = result.pop()
            assert a == r.get('id')
            assert 'a' == r.get('name')
            assert 'apple' == r.get('value')

    def test_link(self):
        """
        Link to any node 
        """
        with self.app.app_context():
            init_db()
            a_id = insert_node(name='a', value=None)
            b_id = insert_node(name='b', value=None)
            c_id = insert_node(name='c', value="c")
            d_id = insert_node(name='d', value="d")

            # a -> c, b -> c
            # a -> d
            insert_node_node(node_id=a_id, target_node_id=c_id)
            insert_node_node(node_id=a_id, target_node_id=d_id)
            insert_node_node(node_id=b_id, target_node_id=c_id)

            c = db.cursor()
            result = c.execute(fetch_sql_string('select_link_node_from_node.sql'), {'node_id': a_id}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('node_id', None) for x in result]
            assert c_id in result
            assert d_id in result
            assert a_id not in result

            result = c.execute(fetch_sql_string('select_link_node_from_node.sql'), {'node_id': b_id}).fetchall()
            (result, col_names) = normalize(result, c.description)
            result = [x.get('node_id', None) for x in result]
            assert c_id in result
            assert d_id not in result
            assert a_id not in result

    def test_template(self):
        with self.app.app_context():
            init_db()

            a = insert_node(name='a', value=None)
            add_template_for_node('template_a.html', a)
            aa = insert_node(name='aa', value=None)
            add_template_for_node('template_a.html', aa)
            b = insert_node(name='b', value=None)
            add_template_for_node('template_b.html', b)
            c = insert_node(name='c', value=None)
            add_template_for_node('template_c.html', c)

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



class SelectSQL(ChillTestCase):
    def test_empty(self):
        """
        """
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                # Not setting a value for a node
                four_id = insert_node(name='empty', value=None)
                insert_route(path='/empty/', node_id=four_id)

                # When no value is set and no SelectSQL or Template is set
                rv = c.get('/empty', follow_redirects=True)
                assert 404 == rv.status_code

    def test_simple(self):
        """
        """

        f = open(os.path.join(self.tmp_template_dir, 'simple.sql'), 'w')
        f.write("""
          select 'yup' as a, 'pretty' as b, 'darn' as c, 'simple' as d;
          """)
        f.close()
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                simple_id = insert_node(name='simple', value=None)
                insert_selectsql(name='simple.sql', node_id=simple_id)

                insert_route(path="/simple/", node_id=simple_id)

                rv = c.get('/simple', follow_redirects=True)
                assert 200 == rv.status_code
                simple_json = json.loads(rv.data)
                assert 'yup' == simple_json['a']

    def test_rules(self):
        f = open(os.path.join(self.tmp_template_dir, 'insert_promoattr.sql'), 'w')
        f.write("""
          insert into PromoAttr (node_id, title, description) values (:node_id, :title, :description);
          """)
        f.close()
        f = open(os.path.join(self.tmp_template_dir, 'select_promoattr.sql'), 'w')
        f.write("""
          select * from PromoAttr where node_id = :node_id;
          """)
        f.close()
        f = open(os.path.join(self.tmp_template_dir, 'select_promos.sql'), 'w')
        f.write("""
          select id as node_id, * from Node where name = 'promo' order by id limit 2 offset 13;
          """)
        f.close()
        f = open(os.path.join(self.tmp_template_dir, 'select_mainmenu.sql'), 'w')
        f.write("""
          select name as link from Node where name like 'page_' order by link;
          """)
        f.close()
        f = open(os.path.join(self.tmp_template_dir, 'select_pageattr.sql'), 'w')
        f.write("""
          select 'example title' as title, 'a description of the page' as description;
          """)
        f.close()

        expected = {
                "mainmenu": [
                    { "link": "page1" },
                    { "link": "page2" },
                    { "link": "page3" }
                    ],
                "pageattr": {
                    "description": "a description of the page",
                    "title": "example title"
                    },
                "promos": [
                    { "promo": {
                            "description": "aaaaaaaaaaaaa",
                            "node_id": 20,
                            "title": "promo 13"
                            }
                        },
                    { "promo": {
                            "description": "aaaaaaaaaaaaaa",
                            "node_id": 21,
                            "title": "promo 14"
                            }
                        }
                    ]
                }
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                cursor = db.cursor()
                cursor.execute("""
                create table PromoAttr (
                  node_id integer, 
                  abc integer, 
                  title varchar(255),
                  description text
                  );
                """)
                db.commit()


                page_id = insert_node(name='page1', value=None)
                insert_route(path='/page1/', node_id=page_id)
                insert_selectsql(name='select_link_node_from_node.sql', node_id=page_id)

                pageattr_id = insert_node(name='pageattr', value=None)
                insert_node_node(node_id=page_id, target_node_id=pageattr_id)
                insert_selectsql(name='select_pageattr.sql', node_id=pageattr_id)

                mainmenu_id = insert_node(name='mainmenu', value=None)
                insert_node_node(node_id=page_id, target_node_id=mainmenu_id)
                insert_selectsql(name='select_mainmenu.sql', node_id=mainmenu_id)
                # Add some other pages that will be shown in menu as just links
                insert_node(name='page2', value=None)
                insert_node(name='page3', value=None)

                promos_id = insert_node(name='promos', value=None)
                insert_node_node(node_id=page_id, target_node_id=promos_id)
                insert_selectsql(name='select_promos.sql', node_id=promos_id)


                for a in range(0,100):
                    a_id = insert_node(name='promo', value=None)
                    cursor.execute(fetch_selectsql_string('insert_promoattr.sql'), {'node_id':a_id, 'title':'promo %i' % a, 'description': 'a'*a})
                    db.commit()
                    # wire the promo to it's attr
                    insert_selectsql(name='select_promoattr.sql', node_id=a_id)

                rv = c.get('/page1', follow_redirects=True)
                assert 200 == rv.status_code
                rv_json = json.loads(rv.data)
                assert set(expected.keys()) == set(rv_json.keys())
                assert set(expected['pageattr'].keys()) == set(rv_json['pageattr'].keys())



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

                test_id = insert_node(name='test one', value='testing one')
                insert_route(path='/test/1/', node_id=test_id)
                add_template_for_node('template_a.html', test_id)

                rv = c.get('/test/1', follow_redirects=True)
                assert 'testing one' in rv.data

                a_id = insert_node(name='a', value='apple')
                insert_route(path='/fruit/a/', node_id=a_id)
                add_template_for_node('template_a.html', a_id)

                rv = c.get('/fruit/a', follow_redirects=True)
                assert 'apple' in rv.data
                assert 'template_a' in rv.data

                b_id = insert_node(name='b', value='banana')
                add_template_for_node('template_b.html', b_id)
                o_id = insert_node(name='orange', value='orange')
                add_template_for_node('template_b.html', o_id)

                eggplant_id = insert_node(name='eggplant', value='eggplant')
                add_template_for_node('template_b.html', eggplant_id)

                # overwrite ( fruit/a use to be set to template_a.html )
                add_template_for_node('template_b.html', a_id)

                rv = c.get('/fruit/a', follow_redirects=True)
                assert 'apple' in rv.data
                assert 'template_b' in rv.data


class PostMethod(ChillTestCase):
    def test_a(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, 'insert_llama.sql'), 'w')
        f.write("""
          insert into Llama (llama_name, location, description) values (:llama_name, :location, :description);
          """)
        f.close()
        f = open(os.path.join(self.tmp_template_dir, 'select_llama.sql'), 'w')
        f.write("""
          select * from Llama
          where llama_name = :llama_name;
          """)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                cursor = db.cursor()
                cursor.execute("""
                create table Llama (
                  llama_name varchar(255),
                  location varchar(255),
                  description text
                  );
                """)
                db.commit()

                llamas_id = insert_node(name='llamas', value=None)
                insert_route(path='/api/llamas/', node_id=llamas_id, weight=1)
                insert_selectsql(name='insert_llama.sql', node_id=llamas_id)

                llama_1 = {
                        'llama_name': 'Rocky',
                        'location': 'unknown',
                        'description': 'first llama'
                        }
                rv = c.post('/api/llamas/', data=llama_1)
                assert 201 == rv.status_code
                self.app.logger.debug(rv.data)

                llama_2 = {
                        'llama_name': 'Nocky',
                        'location': 'unknown',
                        'description': 'second llama'
                        }
                rv = c.post('/api/llamas/', data=llama_2)

                select_llama = insert_node(name='llamas', value=None)
                insert_route(path='/api/llamas/name/<llama_name>/', node_id=select_llama, weight=1)
                insert_selectsql(name='select_llama.sql', node_id=select_llama)
                rv = c.get('/api/llamas/name/Rocky/', follow_redirects=True)
                self.app.logger.debug(rv.data)

                cursor = db.cursor()
                cursor.execute("""select * from Llama;""")
                self.app.logger.debug(normalize(cursor, cursor.description))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NothingConfigured))
    suite.addTest(unittest.makeSuite(SimpleCheck))
    return suite


if __name__ == '__main__':
    unittest.main()

