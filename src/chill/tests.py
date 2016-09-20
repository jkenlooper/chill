import unittest
import tempfile
import os
import json
import logging

from PIL import Image

from chill.app import make_app, db
from chill.database import ( init_db,
        init_picture_tables,
        add_picture_for_node,
        link_picturename_for_node,
        rowify,
        insert_node,
        insert_node_node,
        delete_node,
        insert_route,
        insert_query,
        fetch_query_string,
        add_template_for_node )


class ChillTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp_template_dir = tempfile.mkdtemp()
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)
        self.app = make_app(CHILL_DATABASE_URI=self.tmp_db.name,
                THEME_TEMPLATE_FOLDER=self.tmp_template_dir,
                THEME_SQL_FOLDER=self.tmp_template_dir,
                MEDIA_FOLDER=self.tmp_template_dir,
                DOCUMENT_FOLDER=self.tmp_template_dir,
                CACHE_NO_NULL_WARNING=True,
                DEBUG=True)
        self.app.logger.setLevel(logging.CRITICAL)

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
            c.execute(fetch_query_string('insert_node.sql'), {'name': 'a', 'value':'apple'})
            a = c.lastrowid
            db.commit()

            result = c.execute('select * from Node where id = :id;', {'id':a}).fetchall()
            (result, col_names) = rowify(result, c.description)
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
            result = c.execute(fetch_query_string('select_link_node_from_node.sql'), {'node_id': a_id}).fetchall()
            (result, col_names) = rowify(result, c.description)
            result = [x.get('node_id', None) for x in result]
            assert c_id in result
            assert d_id in result
            assert a_id not in result

            result = c.execute(fetch_query_string('select_link_node_from_node.sql'), {'node_id': b_id}).fetchall()
            (result, col_names) = rowify(result, c.description)
            result = [x.get('node_id', None) for x in result]
            assert c_id in result
            assert d_id not in result
            assert a_id not in result

    def test_value(self):
        """
        """
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                a_id = insert_node(name='a', value=None)
                insert_route(path='/', node_id=a_id)

                content = insert_node(name='content', value='apple')
                insert_node_node(node_id=a_id, target_node_id=content)

                rv = c.get('/', follow_redirects=True)
                assert 200 == rv.status_code
                #self.app.logger.debug('test: %s', rv.data)
                assert 'apple' in rv.data

    def test_noderequest(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, 'select_pagenames.sql'), 'w')
        f.write("""
          select 'yup' as test where :pagename in ('apple', 'pear', 'grapes');
          """)
        f.close()
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name='page', value=None)
                insert_route(path='/page/<pagename>/', node_id=page)

                pagenames = insert_node(name='pagenames', value=None)
                insert_node_node(node_id=page, target_node_id=pagenames)
                insert_query(name='select_pagenames.sql', node_id=pagenames)

                rv = c.get('/page/cucumber/', follow_redirects=True)
                assert 200 == rv.status_code
                self.app.logger.debug('test: %s', rv.data)
                assert 'yup' not in rv.data

                rv = c.get('/page/pear/', follow_redirects=True)
                assert 200 == rv.status_code
                self.app.logger.debug('test: %s', rv.data)
                assert 'yup' in rv.data

    def test_noderequest_args(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, 'select_llama.sql'), 'w')
        f.write("""
          select :llama as llama;
          """)
        f.close()
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name='page', value=None)
                insert_route(path='/page/', node_id=page)

                llama = insert_node(name='llama', value=None)
                insert_node_node(node_id=page, target_node_id=llama)
                insert_query(name='select_llama.sql', node_id=llama)

                rv = c.get('/page/?llama=chuck', follow_redirects=True)
                assert 200 == rv.status_code
                self.app.logger.debug('test: %s', rv.data)
                assert 'chuck' in rv.data

                rv = c.get('/page/?nollama=chuck', follow_redirects=True)
                assert 200 == rv.status_code
                self.app.logger.debug('test: %s', rv.data)
                assert 'chuck' not in rv.data

    def test_noderequest_cookies(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, 'select_llama.sql'), 'w')
        f.write("""
          select :llama as llama;
          """)
        f.close()
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name='page', value=None)
                insert_route(path='/page/', node_id=page)

                llama = insert_node(name='llama', value=None)
                insert_node_node(node_id=page, target_node_id=llama)
                insert_query(name='select_llama.sql', node_id=llama)

                c.set_cookie('localhost', 'llama', 'chuck')

                rv = c.get('/page/', follow_redirects=True)
                assert 200 == rv.status_code
                self.app.logger.debug('test: %s', rv.data)
                assert 'chuck' in rv.data


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
            result = c.execute(fetch_query_string('select_template_from_node.sql'), {'node_id': a}).fetchall()
            (result, col_names) = rowify(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert result[0] == 'template_a.html'

            # another node that uses the same template
            c = db.cursor()
            result = c.execute(fetch_query_string('select_template_from_node.sql'), {'node_id': aa}).fetchall()
            (result, col_names) = rowify(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert result[0] == 'template_a.html'

            # can overwrite what node is tied to what template
            add_template_for_node('template_over_a.html', a)

            c = db.cursor()
            result = c.execute(fetch_query_string('select_template_from_node.sql'), {'node_id': a}).fetchall()
            (result, col_names) = rowify(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert result[0] == 'template_over_a.html'

            # this one still uses the other template
            c = db.cursor()
            result = c.execute(fetch_query_string('select_template_from_node.sql'), {'node_id': aa}).fetchall()
            (result, col_names) = rowify(result, c.description)
            result = [x.get('name', None) for x in result]
            assert len(result) == 1
            assert result[0] == 'template_a.html'


    def test_delete_one_node(self):
        """
        Delete a node
        """
        with self.app.app_context():
            init_db()
            c = db.cursor()
            c.execute(fetch_query_string('insert_node.sql'), {'name': 'a', 'value':'apple'})
            a = c.lastrowid
            db.commit()

            result = c.execute(fetch_query_string('select_node_from_id.sql'), {'node_id': a}).fetchall()
            (result, col_names) = rowify(result, c.description)
            assert len(result) == 1
            r = result.pop()
            assert a == r.get('node_id')
            assert 'a' == r.get('name')
            assert 'apple' == r.get('value')

            # now delete
            c = db.cursor()
            delete_node(node_id=a)

            result = c.execute(fetch_query_string('select_node_from_id.sql'), {'node_id': a}).fetchall()
            (result, col_names) = rowify(result, c.description)
            assert len(result) == 0

    def test_delete_node_with_link(self):
        """
        Delete a node also will delete from link
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
            result = c.execute(fetch_query_string('select_link_node_from_node.sql'), {'node_id': a_id}).fetchall()
            (result, col_names) = rowify(result, c.description)
            result = [x.get('node_id', None) for x in result]
            assert c_id in result
            assert d_id in result
            assert a_id not in result

            result = c.execute(fetch_query_string('select_link_node_from_node.sql'), {'node_id': b_id}).fetchall()
            (result, col_names) = rowify(result, c.description)
            result = [x.get('node_id', None) for x in result]
            assert c_id in result
            assert d_id not in result
            assert a_id not in result

            # now delete (should use the 'on delete cascade' sql bit)
            c = db.cursor()
            c.execute(fetch_query_string('delete_node_for_id.sql'), {'node_id': a_id})
            db.commit()

            result = c.execute(fetch_query_string('select_node_from_id.sql'), {'node_id': a_id}).fetchall()
            (result, col_names) = rowify(result, c.description)
            assert len(result) == 0

            c = db.cursor()
            result = c.execute(fetch_query_string('select_link_node_from_node.sql'), {'node_id': a_id}).fetchall()
            (result, col_names) = rowify(result, c.description)
            assert len(result) == 0

            result = c.execute(fetch_query_string('select_node_node_from_node_id.sql'), {'node_id': a_id}).fetchall()
            (result, col_names) = rowify(result, c.description)
            assert len(result) == 0

class Query(ChillTestCase):
    def test_empty(self):
        """
        """
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                # Not setting a value for a node
                four_id = insert_node(name='empty', value=None)
                insert_route(path='/empty/', node_id=four_id)

                # When no value is set and no Query or Template is set
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
                insert_query(name='simple.sql', node_id=simple_id)

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

                pageattr_id = insert_node(name='pageattr', value=None)
                insert_node_node(node_id=page_id, target_node_id=pageattr_id)
                insert_query(name='select_pageattr.sql', node_id=pageattr_id)

                mainmenu_id = insert_node(name='mainmenu', value=None)
                insert_node_node(node_id=page_id, target_node_id=mainmenu_id)
                insert_query(name='select_mainmenu.sql', node_id=mainmenu_id)
                # Add some other pages that will be shown in menu as just links
                insert_node(name='page2', value=None)
                insert_node(name='page3', value=None)

                promos_id = insert_node(name='promos', value=None)
                insert_node_node(node_id=page_id, target_node_id=promos_id)
                insert_query(name='select_promos.sql', node_id=promos_id)


                for a in range(0,100):
                    a_id = insert_node(name='promo', value=None)
                    cursor.execute(fetch_query_string('insert_promoattr.sql'), {'node_id':a_id, 'title':'promo %i' % a, 'description': 'a'*a})
                    db.commit()
                    # wire the promo to it's attr
                    insert_query(name='select_promoattr.sql', node_id=a_id)

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

    def test_dict(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, 'llama.html'), 'w')
        f.write("""
          <!doctype html>
          <html><head><title>llama</title></head>
          <body>
          <h1>template for llama_name</h1>
          {{ llama_name }}
          </body>
          </html>
          """)
        f.close()
        f = open(os.path.join(self.tmp_template_dir, 'select_llama.sql'), 'w')
        f.write("""
          select :llama_name as llama_name;
          """)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                a = insert_node(name='a', value=None)
                insert_route(path='/a/<llama_name>/', node_id=a)
                insert_query(name='select_llama.sql', node_id=a)
                add_template_for_node('llama.html', a)

                rv = c.get('/a/chuck/', follow_redirects=True)
                assert 'chuck' in rv.data
                rv = c.get('/a/chase/', follow_redirects=True)
                assert 'chase' in rv.data

class Documents(ChillTestCase):
    def test_reading_in_a_document(self):
        """
        The custom 'readfile' jinja2 filter reads the file from the DOCUMENT_FOLDER.
        """
        f = open(os.path.join(self.tmp_template_dir, 'imasimplefile.txt'), 'w')
        f.write("""
          Hello, this is just a file.
          """)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'template.html'), 'w')
        f.write("""
          <h1>template</h1>
          {{ simplefilename }}
          <br>
          {{ simplefilename|readfile }}
          """)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                a = insert_node(name='simplefilename', value='imasimplefile.txt')
                apage = insert_node(name='apage', value=None)
                insert_node_node(node_id=apage, target_node_id=a)
                insert_route(path='/a/', node_id=apage)
                add_template_for_node('template.html', apage)

                rv = c.get('/a/', follow_redirects=True)
                assert 'Hello' in rv.data

    def test_markdown_document(self):
        """
        Use 'readfile' and 'markdown' filter together.
        """
        md = """
Heading
=======

Sub-heading
-----------

### Another deeper heading

Paragraphs are separated
by a blank line.

Leave 2 spaces at the end of a line to do a
line break

Text attributes *italic*, **bold**,
onospace
A [link](http://example.com).

Shopping list:

  * apples
  * oranges
  * pears

Numbered list:

  1. apples
  2. oranges
  3. pears

The rain---not the reign---in
Spain.
        """
        html = """<h1>Heading</h1>
<h2>Sub-heading</h2>
<h3>Another deeper heading</h3>
<p>Paragraphs are separated
by a blank line.</p>
<p>Leave 2 spaces at the end of a line to do a
line break</p>
<p>Text attributes <em>italic</em>, <strong>bold</strong>,
onospace
A <a href="http://example.com">link</a>.</p>
<p>Shopping list:</p>
<ul>
<li>apples</li>
<li>oranges</li>
<li>pears</li>
</ul>
<p>Numbered list:</p>
<ol>
<li>apples</li>
<li>oranges</li>
<li>pears</li>
</ol>
<p>The rain---not the reign---in
Spain.</p>"""
        f = open(os.path.join(self.tmp_template_dir, 'imasimplefile.md'), 'w')
        f.write(md)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'template.html'), 'w')
        f.write("""
          {{ simplefilename|readfile|markdown }}
          """)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                a = insert_node(name='simplefilename', value='imasimplefile.md')
                apage = insert_node(name='apage', value=None)
                insert_node_node(node_id=apage, target_node_id=a)
                insert_route(path='/a/', node_id=apage)
                add_template_for_node('template.html', apage)

                rv = c.get('/a/', follow_redirects=True)
                assert html in rv.data

class Picture(ChillTestCase):
    def test_add(self):
        "Add a picture to the database"

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                init_picture_tables()

                a = insert_node(name="apicture", value=None)

                # Create a.jpg in tmp dir media_folder
                ajpg = open(os.path.join(self.tmp_template_dir, 'a.jpg'), 'wb')
                img = Image.new("RGB", (100,100))
                img.save(fp=ajpg)

                add_picture_for_node(node_id=a, filepath='a.jpg')

                apage = insert_node(name="apage", value=None)
                insert_node_node(node_id=apage, target_node_id=a)
                insert_route(path='/', node_id=apage)

                rv = c.get('/', follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert 100 == rv_json['apicture']['width']

    def test_simple_use_case(self):
        "Add a picture and apply a template."

        f = open(os.path.join(self.tmp_template_dir, 'simple.html'), 'w')
        f.write("""
          <!doctype html>
          <html><head><title>test</title></head>
          <body>
          <div>
          {{ cat|safe }}
          </div>
          </body>
          </html>
          """)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, 'img.html'), 'w')
        f.write("""
          <img src="{{ url_for('send_media_file', filename=path) }}"/>
          """)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                init_picture_tables()

                # Create a blank jpg
                catjpg = open(os.path.join(self.tmp_template_dir, 'cat.jpg'), 'wb')
                img = Image.new("RGB", (300,200))
                img.save(fp=catjpg)

                # The 'cat' node is what will link the cat.jpg to.
                cat = insert_node(name="cat", value=None)
                add_picture_for_node(node_id=cat, filepath='cat.jpg')

                # Set a img template around the 'cat'
                add_template_for_node('img.html', cat)

                # Setup a page to show the cat.jpg with the img template
                page = insert_node(name='page', value=None)
                insert_route(path='/cat/', node_id=page)
                add_template_for_node('simple.html', page)

                # Link the page with cat node
                insert_node_node(node_id=page, target_node_id=cat)

                rv = c.get('/cat/', follow_redirects=True)
                assert '<title>test</title>' in rv.data
                assert '<img src="/media/cat.jpg"/>' in rv.data

    def test_add_and_link(self):
        "Add a picture to the database and link it to two nodes"

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                init_picture_tables()

                apage = insert_node(name="apage", value=None)
                insert_route(path='/', node_id=apage)

                for f in ('apple 200 300', 'banana 500 100', 'carrot 100 30'):
                    (name, width, height) = f.split(' ')
                    width = int(width)
                    height = int(height)
                    node = insert_node(name=name, value=None)
                    # Create a.jpg in tmp dir media_folder
                    jpg = open(os.path.join(self.tmp_template_dir, '{0}.jpg'.format(name)), 'wb')
                    img = Image.new("RGB", (width,height))
                    img.save(fp=jpg)

                    add_picture_for_node(node_id=node, filepath='{0}.jpg'.format(name))
                    insert_node_node(node_id=apage, target_node_id=node)

                # Make a 'pictures' node and add all the pictures to it.
                pictures = insert_node(name='pictures', value=None)
                for name in ('apple.jpg', 'banana.jpg', 'carrot.jpg'):
                    link_picturename_for_node(node_id=pictures, picturename=name)
                insert_node_node(node_id=apage, target_node_id=pictures)

                rv = c.get('/', follow_redirects=True)
                #self.app.logger.debug('test: %s', rv.data)
                rv_json = json.loads(rv.data)

                assert 200 == rv_json['apple']['width']
                assert 500 == rv_json['banana']['width']
                assert 100 == rv_json['banana']['height']
                assert 30 == rv_json['carrot']['height']

                assert 'apple.jpg' in [x['path'] for x in rv_json['pictures']]

class ShortcodeRoute(ChillTestCase):
    def test_route(self):
        "Expand the route shortcode"

        f = open(os.path.join(self.tmp_template_dir, 'simple.html'), 'w')
        f.write("""
          <!doctype html>
          <html><head><title>test</title></head>
          <body>
          <div>
          {{ cat|shortcodes }}
          </div>
          </body>
          </html>
          """)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name='page', value=None)
                insert_route(path='/', node_id=page)
                add_template_for_node('simple.html', page)

                catimg = insert_node(name='acat', value="<img alt='a picture of a cat'/>")
                insert_route(path='/cat/picture/', node_id=catimg)

                text = "something [chill route /cat/picture/ ] [blah blah[chill route /dog/pic] the end"
                textnode = insert_node(name='cat', value=text)

                insert_node_node(node_id=page, target_node_id=textnode)

                rv = c.get('/', follow_redirects=True)
                assert "something <img alt='a picture of a cat'/> [blah blah<!-- 404 '/dog/pic' --> the end" in rv.data
                assert "[chill route /cat/picture/ ]" not in rv.data

                rv = c.get('/cat/picture/', follow_redirects=True)
                assert "<img alt='a picture of a cat'/>" in rv.data

class ShortcodePageURI(ChillTestCase):
    def test_page_uri(self):
        "Expand the page_uri shortcode"

        f = open(os.path.join(self.tmp_template_dir, 'simple.html'), 'w')
        f.write("""
          <!doctype html>
          <html><head><title>test</title></head>
          <body>
          <div>
          {{ cat|shortcodes }}
          </div>
          </body>
          </html>
          """)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name='page', value=None)
                insert_route(path='/', node_id=page)
                add_template_for_node('simple.html', page)

                catpage = insert_node(name='acat', value="a page for cat")
                insert_route(path='/cat/', node_id=catpage)

                text = "something link for cat page that does exist = '[chill page_uri cat ]' link for dog that does not exist = '[chill page_uri dog]'"
                textnode = insert_node(name='cat', value=text)

                insert_node_node(node_id=page, target_node_id=textnode)

                rv = c.get('/', follow_redirects=True)
                assert "something link for cat page that does exist = '/cat/' link for dog that does not exist = '/dog/'" in rv.data
                assert "[chill page_uri cat ]" not in rv.data

                rv = c.get('/cat/', follow_redirects=True)
                assert "a page for cat" in rv.data

                rv = c.get('/dog/', follow_redirects=True)
                assert 404 == rv.status_code

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
                insert_route(path='/api/llamas/', node_id=llamas_id, weight=1, method="POST")
                insert_query(name='insert_llama.sql', node_id=llamas_id)

                llama_1 = {
                        'llama_name': 'Rocky',
                        'location': 'unknown',
                        'description': 'first llama'
                        }
                rv = c.post('/api/llamas/', data=llama_1)
                assert 201 == rv.status_code

                llama_2 = {
                        'llama_name': 'Nocky',
                        'location': 'unknown',
                        'description': 'second llama'
                        }
                rv = c.post('/api/llamas/', data=llama_2)
                assert 201 == rv.status_code

                select_llama = insert_node(name='llamas', value=None)
                insert_route(path='/api/llamas/name/<llama_name>/', node_id=select_llama, weight=1)
                insert_query(name='select_llama.sql', node_id=select_llama)

                rv = c.get('/api/llamas/name/Rocky/', follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert set(llama_1.keys()) == set(rv_json.keys())
                assert set(llama_1.values()) == set(rv_json.values())

                rv = c.get('/api/llamas/name/Nocky/', follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert set(llama_2.keys()) == set(rv_json.keys())
                assert set(llama_2.values()) == set(rv_json.values())

class PutMethod(ChillTestCase):
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
                insert_route(path='/api/llamas/name/<llama_name>/', node_id=llamas_id, weight=1, method="PUT")
                insert_query(name='insert_llama.sql', node_id=llamas_id)

                llama_1 = {
                        'llama_name': 'Socky',
                        'location': 'unknown',
                        'description': 'first llama'
                        }
                rv = c.put('/api/llamas/name/Socky/', data=llama_1)
                assert 201 == rv.status_code

                select_llama = insert_node(name='llamas', value=None)
                insert_route(path='/api/llamas/name/<llama_name>/', node_id=select_llama, weight=1)
                insert_query(name='select_llama.sql', node_id=select_llama)

                rv = c.get('/api/llamas/name/Socky/', follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert set(llama_1.keys()) == set(rv_json.keys())
                assert set(llama_1.values()) == set(rv_json.values())

class PatchMethod(ChillTestCase):
    def test_a(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, 'update_llama.sql'), 'w')
        f.write("""
          update Llama set location = :location, description = :description where llama_name = :llama_name;
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

                cursor.execute("""
                  insert into Llama (llama_name) values ('Pocky');
                """)
                db.commit()

                llamas_id = insert_node(name='llamas', value=None)
                insert_route(path='/api/llamas/name/<llama_name>/', node_id=llamas_id, weight=1, method="PATCH")
                insert_query(name='update_llama.sql', node_id=llamas_id)

                llama_1 = {
                        'llama_name': 'Pocky',
                        'location': 'unknown',
                        'description': 'first llama'
                        }
                rv = c.patch('/api/llamas/name/Pocky/', data=llama_1)
                assert 201 == rv.status_code

                select_llama = insert_node(name='llamas', value=None)
                insert_route(path='/api/llamas/name/<llama_name>/', node_id=select_llama, weight=1)
                insert_query(name='select_llama.sql', node_id=select_llama)

                rv = c.get('/api/llamas/name/Pocky/', follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert set(llama_1.keys()) == set(rv_json.keys())
                assert set(llama_1.values()) == set(rv_json.values())

class DeleteMethod(ChillTestCase):
    def test_a(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, 'delete_llama.sql'), 'w')
        f.write("""
          Delete from Llama where llama_name = :llama_name;
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

                cursor.execute("""
                  insert into Llama (llama_name, location, description) values ('Docky', 'somewhere', 'damaged');
                """)
                db.commit()

                select_llama = insert_node(name='llamas', value=None)
                insert_route(path='/api/llamas/name/<llama_name>/', node_id=select_llama, weight=1)
                insert_query(name='select_llama.sql', node_id=select_llama)

                llamas_id = insert_node(name='llamas', value=None)
                insert_route(path='/api/llamas/name/<llama_name>/', node_id=llamas_id, weight=1, method="DELETE")
                insert_query(name='delete_llama.sql', node_id=llamas_id)

                rv = c.get('/api/llamas/name/Docky/', follow_redirects=True)
                assert 200 == rv.status_code

                rv = c.delete('/api/llamas/name/Docky/')
                assert 204 == rv.status_code

                rv = c.get('/api/llamas/name/Docky/', follow_redirects=True)
                assert 404 == rv.status_code

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NothingConfigured))
    suite.addTest(unittest.makeSuite(SimpleCheck))
    return suite


if __name__ == '__main__':
    unittest.main()

