# -*- coding: utf-8 -*-

from builtins import range, bytes
import unittest
import tempfile
import os
import json
import logging

from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text
import yaml

from chill.app import make_app, db
from chill.database import (
    init_db,
    rowify,
    insert_node,
    insert_node_node,
    select_node,
    delete_node,
    insert_route,
    insert_query,
    fetch_query_string,
    add_template_for_node,
)
from chill.yaml_chill_node import load_yaml, dump_yaml, ChillNode


class ChillTestCase(unittest.TestCase):
    database_readonly=False
    def setUp(self):
        self.debug = False
        self.tmp_template_dir = tempfile.mkdtemp()
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)
        self.app = make_app(
            CHILL_DATABASE_URI="sqlite:///" + self.tmp_db.name,
            THEME_TEMPLATE_FOLDER=self.tmp_template_dir,
            THEME_SQL_FOLDER=self.tmp_template_dir,
            MEDIA_FOLDER=self.tmp_template_dir,
            DOCUMENT_FOLDER=self.tmp_template_dir,
            CACHE_NO_NULL_WARNING=True,
            DEBUG=self.debug,
            database_readonly=self.database_readonly,
        )
        self.app.logger.setLevel(logging.DEBUG if self.debug else logging.CRITICAL)

    def tearDown(self):
        """Get rid of the database and templates after each test."""
        # self.tmp_db.unlink(self.tmp_db.name)
        os.unlink(self.tmp_db.name)

        # Walk and remove all files and directories in the created temp directory
        for root, dirs, files in os.walk(self.tmp_template_dir, topdown=False):
            for name in files:
                # self.app.logger.debug('removing: %s', os.path.join(root, name))
                os.remove(os.path.join(root, name))
            for name in dirs:
                # self.app.logger.debug('removing: %s', os.path.join(root, name))
                os.rmdir(os.path.join(root, name))

        os.rmdir(self.tmp_template_dir)


class SimpleCheck(ChillTestCase):
    def test_db(self):
        """Check usage of db"""
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                db.execute(
                    text("""insert into Node (name, value) values (:name, :value)"""),
                    **{"name": "bill", "value": "?"}
                )

                # rv = c.get('/bill', follow_redirects=True)
                # assert '?' in rv.data


class SimpleCheckReadonly(ChillTestCase):
    database_readonly=True
    def test_db_is_readonly(self):
        """Check usage of db"""
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                with self.assertRaises(OperationalError) as err:
                    db.execute(
                        text("""insert into Node (name, value) values (:name, :value)"""),
                        **{"name": "bill", "value": "?"}
                    )
                self.assertRegex(str(err.exception), 'attempt to write a readonly database')


class Route(ChillTestCase):
    def test_paths(self):
        with self.app.app_context():
            init_db()

            top_id = insert_node(name="top", value="hello")
            insert_route(path="/", node_id=top_id)

            one_id = insert_node(name="one", value="1")
            insert_route(path="/one/", node_id=one_id)
            two_id = insert_node(name="two", value="2")
            insert_route(path="/one/two/", node_id=two_id)
            three_id = insert_node(name="three", value="3")
            insert_route(path="/one/two/three/", node_id=three_id)
            insert_route(path="/one/two/other_three/", node_id=three_id)

            with self.app.test_client() as c:

                rv = c.get("/", follow_redirects=True)
                assert b"hello" == rv.data
                rv = c.get("/.", follow_redirects=True)
                assert b"hello" == rv.data
                rv = c.get("/index.html", follow_redirects=True)
                assert b"hello" == rv.data
                rv = c.get("", follow_redirects=True)
                assert b"hello" == rv.data

                rv = c.get("/one", follow_redirects=True)
                assert b"1" == rv.data
                rv = c.get("/one/", follow_redirects=True)
                assert b"1" == rv.data
                rv = c.get("/one/.", follow_redirects=True)
                assert b"1" == rv.data
                rv = c.get("/one/index.html", follow_redirects=True)
                assert b"1" == rv.data
                rv = c.get("/one/two", follow_redirects=True)
                assert b"2" == rv.data
                rv = c.get("/one/foo/../two", follow_redirects=True)
                assert b"2" == rv.data
                rv = c.get("/./one//two", follow_redirects=True)
                assert b"2" == rv.data
                rv = c.get("/one/two/", follow_redirects=True)
                assert b"2" == rv.data
                rv = c.get("/one/two/index.html", follow_redirects=True)
                assert b"2" == rv.data
                rv = c.get("/one/two/three", follow_redirects=True)
                assert b"3" == rv.data
                rv = c.get("/one/two/other_three", follow_redirects=True)
                assert b"3" == rv.data
                rv = c.get("/one/two/other_three/index.html", follow_redirects=True)
                assert b"3" == rv.data
                rv = c.get(
                    "/one///////two/other_three/index.html", follow_redirects=True
                )
                assert b"3" == rv.data
                rv = c.get("/one/two/other_three/nothing", follow_redirects=True)
                assert 404 == rv.status_code

    def test_single_rule(self):
        with self.app.app_context():
            init_db()

            id = insert_node(name="top", value="hello")
            insert_route(path="/<int:count>/", node_id=id)

            with self.app.test_client() as c:

                rv = c.get("/", follow_redirects=True)
                assert 404 == rv.status_code
                rv = c.get("/1", follow_redirects=True)
                assert b"hello" == rv.data
                rv = c.get("/1/", follow_redirects=True)
                assert b"hello" == rv.data
                rv = c.get("////1/", follow_redirects=True)
                assert b"hello" == rv.data
                rv = c.get("/1/index.html", follow_redirects=True)
                assert b"hello" == rv.data
                rv = c.get("/1/index.html/not", follow_redirects=True)
                assert 404 == rv.status_code

    def test_multiple_rules(self):
        with self.app.app_context():
            init_db()

            id = insert_node(name="fruit", value="fruit")
            insert_route(path="/fruit/<anything>/", node_id=id)
            id = insert_node(name="vegetables", value="vegetables")
            insert_route(path="/vegetables/<anything>/", node_id=id)

            with self.app.test_client() as c:

                rv = c.get("/fruit", follow_redirects=True)
                assert 404 == rv.status_code
                rv = c.get("/fruit/pear/", follow_redirects=True)
                assert b"fruit" == rv.data
                rv = c.get("/vegetables", follow_redirects=True)
                assert 404 == rv.status_code
                rv = c.get("/vegetables/pear/", follow_redirects=True)
                assert b"vegetables" == rv.data

    def test_weight(self):
        with self.app.app_context():
            init_db()

            id = insert_node(name="a", value="a")
            insert_route(path="/<path:anything>/", node_id=id, weight=1)
            id = insert_node(name="aardvark", value="aardvark")
            insert_route(path="/animals/<anything>/", node_id=id, weight=1)
            id = insert_node(name="b", value="b")
            insert_route(path="/<path:something>/", node_id=id, weight=2)

            with self.app.test_client() as c:

                rv = c.get("/apple", follow_redirects=True)
                assert b"b" == rv.data
                rv = c.get("/animals/ape", follow_redirects=True)
                assert b"aardvark" == rv.data
                rv = c.get("/animals/ape/1", follow_redirects=True)
                assert b"b" == rv.data
                rv = c.get("/vegetables", follow_redirects=True)
                assert b"b" == rv.data
                rv = c.get("/vegetables/pear/", follow_redirects=True)
                assert b"b" == rv.data

    def test_404_on_mismatch_method(self):
        """
        route that matches, but has no method match
        """
        with self.app.app_context():
            init_db()

            llama_id = insert_node(name="llama", value="1234")
            insert_route(path="/llama/", node_id=llama_id)

            with self.app.test_client() as c:

                rv = c.get("/llama/", follow_redirects=True)
                assert b"1234" == rv.data
                assert 200 == rv.status_code

                rv = c.post("/llama/", follow_redirects=True)
                assert b"1234" != rv.data
                assert 404 == rv.status_code

                rv = c.put("/llama/", follow_redirects=True)
                assert b"1234" != rv.data
                assert 404 == rv.status_code

                rv = c.patch("/llama/", follow_redirects=True)
                assert b"1234" != rv.data
                assert 404 == rv.status_code

                rv = c.delete("/llama/", follow_redirects=True)
                assert b"1234" != rv.data
                assert 404 == rv.status_code


class NothingConfigured(ChillTestCase):
    def test_empty(self):
        """Show something for nothing"""
        with self.app.test_client() as c:
            rv = c.get("/")
            assert 404 == rv.status_code
            rv = c.get("/index.html")
            assert 404 == rv.status_code
            rv = c.get("/something/")
            assert 404 == rv.status_code
            rv = c.get("/something/test.txt", follow_redirects=True)
            assert 404 == rv.status_code
            rv = c.get("/static/afile.txt", follow_redirects=True)
            assert 404 == rv.status_code
            rv = c.get("/something/nothing/")
            assert 404 == rv.status_code


class SQL(ChillTestCase):
    def test_insert_one_node(self):
        """
        Add a node
        """
        with self.app.app_context():
            init_db()
            result = db.execute(
                text(fetch_query_string("insert_node.sql")), name="a", value="apple"
            )
            a = result.lastrowid

            result = db.execute(
                text("select * from Node where id = :id;"), id=a
            ).fetchall()
            assert len(result) == 1
            r = result[0]
            assert a == r["id"]
            assert "a" == r["name"]
            assert "apple" == r["value"]

    def test_insert_one_node_with_unicode(self):
        """
        Add a node with a unicode value
        """
        with self.app.app_context():
            init_db()
            result = db.execute(
                text(fetch_query_string("insert_node.sql")), name="a", value=u"Àрpĺè"
            )
            a = result.lastrowid

            result = db.execute(
                text("select * from Node where id = :id;"), id=a
            ).fetchall()
            assert len(result) == 1
            r = result[0]
            assert a == r["id"]
            assert "a" == r["name"]
            assert u"Àрpĺè" == r["value"]

    def test_link(self):
        """
        Link to any node
        """
        with self.app.app_context():
            init_db()
            a_id = insert_node(name="a", value=None)
            b_id = insert_node(name="b", value=None)
            c_id = insert_node(name="c", value="c")
            d_id = insert_node(name="d", value="d")

            # a -> c, b -> c
            # a -> d
            insert_node_node(node_id=a_id, target_node_id=c_id)
            insert_node_node(node_id=a_id, target_node_id=d_id)
            insert_node_node(node_id=b_id, target_node_id=c_id)

            result = db.execute(
                text(fetch_query_string("select_link_node_from_node.sql")), node_id=a_id
            )
            result = [x["node_id"] for x in result]
            assert c_id in result
            assert d_id in result
            assert a_id not in result

            result = db.execute(
                text(fetch_query_string("select_link_node_from_node.sql")), node_id=b_id
            )
            result = [x["node_id"] for x in result]
            assert c_id in result
            assert d_id not in result
            assert a_id not in result

    def test_value(self):
        """
        """
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                a_id = insert_node(name="a", value=None)
                insert_route(path="/", node_id=a_id)

                content = insert_node(name="content", value="apple")
                insert_node_node(node_id=a_id, target_node_id=content)

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code
                # self.app.logger.debug('test: %s', rv.data)
                assert b"apple" in rv.data

    def test_unicode_value(self):
        """
        """
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                a_id = insert_node(name="a", value=None)
                insert_route(path="/", node_id=a_id)

                content = insert_node(name="content", value=u"Àрpĺè")
                insert_node_node(node_id=a_id, target_node_id=content)

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code
                # assert '\u00c0\u0440p\u013a\u00e8' in bytes(rv.data, 'utf-8').decode('utf-8')
                assert bytes(b"\u00c0\u0440p\u013a\u00e8") in rv.data

    def test_noderequest(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "select_pagenames.sql"), "w")
        f.write(
            """
          select 'yup' as test where :pagename in ('apple', 'pear', 'grapes');
          """
        )
        f.close()
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name="page", value=None)
                insert_route(path="/page/<pagename>/", node_id=page)

                pagenames = insert_node(name="pagenames", value=None)
                insert_node_node(node_id=page, target_node_id=pagenames)
                insert_query(name="select_pagenames.sql", node_id=pagenames)

                rv = c.get("/page/cucumber/", follow_redirects=True)
                assert 200 == rv.status_code
                # self.app.logger.debug('test: %s', rv.data)
                assert b"yup" not in rv.data

                rv = c.get("/page/pear/", follow_redirects=True)
                assert 200 == rv.status_code
                # self.app.logger.debug('test: %s', rv.data)
                assert b"yup" in rv.data

    def test_noderequest_args(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "select_llama.sql"), "w")
        f.write(
            """
          select :llama as llama;
          """
        )
        f.close()
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name="page", value=None)
                insert_route(path="/page/", node_id=page)

                llama = insert_node(name="llama", value=None)
                insert_node_node(node_id=page, target_node_id=llama)
                insert_query(name="select_llama.sql", node_id=llama)

                rv = c.get("/page/?llama=chuck", follow_redirects=True)
                assert 200 == rv.status_code
                # self.app.logger.debug('test: %s', rv.data)
                assert b"chuck" in rv.data

                rv = c.get("/page/?nollama=chuck", follow_redirects=True)
                assert 200 == rv.status_code
                # self.app.logger.debug('test: %s', rv.data)
                assert b"chuck" not in rv.data

    def test_noderequest_cookies(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "select_llama.sql"), "w")
        f.write(
            """
          select :llama as llama;
          """
        )
        f.close()
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name="page", value=None)
                insert_route(path="/page/", node_id=page)

                llama = insert_node(name="llama", value=None)
                insert_node_node(node_id=page, target_node_id=llama)
                insert_query(name="select_llama.sql", node_id=llama)

                c.set_cookie("localhost", "llama", "chuck")

                rv = c.get("/page/", follow_redirects=True)
                assert 200 == rv.status_code
                # self.app.logger.debug('test: %s', rv.data)
                assert b"chuck" in rv.data

    def test_template(self):
        with self.app.app_context():
            init_db()

            a = insert_node(name="a", value=None)
            add_template_for_node("template_a.html", a)
            aa = insert_node(name="aa", value=None)
            add_template_for_node("template_a.html", aa)
            b = insert_node(name="b", value=None)
            add_template_for_node("template_b.html", b)
            c = insert_node(name="c", value=None)
            add_template_for_node("template_c.html", c)

            result = db.execute(
                text(fetch_query_string("select_template_from_node.sql")), node_id=a
            )
            result = [x["name"] for x in result]
            assert len(result) == 1
            assert result[0] == "template_a.html"

            # another node that uses the same template
            result = db.execute(
                text(fetch_query_string("select_template_from_node.sql")), node_id=aa
            )
            result = [x["name"] for x in result]
            assert len(result) == 1
            assert result[0] == "template_a.html"

            # can overwrite what node is tied to what template
            add_template_for_node("template_over_a.html", a)

            result = db.execute(
                text(fetch_query_string("select_template_from_node.sql")), node_id=a
            )
            result = [x["name"] for x in result]
            assert len(result) == 1
            assert result[0] == "template_over_a.html"

            # this one still uses the other template
            result = db.execute(
                text(fetch_query_string("select_template_from_node.sql")), node_id=aa
            )
            result = [x["name"] for x in result]
            assert len(result) == 1
            assert result[0] == "template_a.html"

    def test_delete_one_node(self):
        """
        Delete a node
        """
        with self.app.app_context():
            init_db()
            result = db.execute(
                text(fetch_query_string("insert_node.sql")), name="a", value="apple"
            )
            a = result.lastrowid

            result = db.execute(
                text(fetch_query_string("select_node_from_id.sql")), node_id=a
            ).fetchall()
            assert len(result) == 1
            r = result[0]
            assert a == r["node_id"]
            assert "a" == r["name"]
            assert "apple" == r["value"]

            # now delete
            delete_node(node_id=a)

            result = db.execute(
                text(fetch_query_string("select_node_from_id.sql")), node_id=a
            ).fetchall()
            assert len(result) == 0

    def test_delete_node_with_link(self):
        """
        Delete a node also will delete from link
        """
        with self.app.app_context():
            init_db()
            a_id = insert_node(name="a", value=None)
            b_id = insert_node(name="b", value=None)
            c_id = insert_node(name="c", value="c")
            d_id = insert_node(name="d", value="d")

            # a -> c, b -> c
            # a -> d
            insert_node_node(node_id=a_id, target_node_id=c_id)
            insert_node_node(node_id=a_id, target_node_id=d_id)
            insert_node_node(node_id=b_id, target_node_id=c_id)

            result = db.execute(
                text(fetch_query_string("select_link_node_from_node.sql")), node_id=a_id
            )
            result = [x["node_id"] for x in result]
            assert c_id in result
            assert d_id in result
            assert a_id not in result

            result = db.execute(
                text(fetch_query_string("select_link_node_from_node.sql")), node_id=b_id
            )
            result = [x["node_id"] for x in result]
            assert c_id in result
            assert d_id not in result
            assert a_id not in result

            # now delete (should use the 'on delete cascade' sql bit)
            db.execute(text(fetch_query_string("delete_node_for_id.sql")), node_id=a_id)

            result = db.execute(
                text(fetch_query_string("select_node_from_id.sql")), node_id=a_id
            ).fetchall()
            assert len(result) == 0

            result = db.execute(
                text(fetch_query_string("select_link_node_from_node.sql")), node_id=a_id
            ).fetchall()
            assert len(result) == 0

            result = db.execute(
                text(fetch_query_string("select_node_node_from_node_id.sql")),
                node_id=a_id,
            ).fetchall()

            assert len(result) == 0

    def test_select_node(self):
        with self.app.app_context():
            init_db()
            simple_id = insert_node(name="simple", value="test")
            result = select_node(node_id=simple_id)[0]
            assert set(result.keys()) == set(["name", "value", "node_id"])
            assert result["value"] == "test"
            assert result["name"] == "simple"
            assert result["node_id"] == simple_id


class Query(ChillTestCase):
    def test_empty(self):
        """
        """
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                # Not setting a value for a node
                four_id = insert_node(name="empty", value=None)
                insert_route(path="/empty/", node_id=four_id)

                # When no value is set and no Query or Template is set
                rv = c.get("/empty", follow_redirects=True)
                assert 404 == rv.status_code

    def test_simple(self):
        """
        """

        f = open(os.path.join(self.tmp_template_dir, "simple.sql"), "w")
        f.write(
            """
          select 'yup' as a, 'pretty' as b, 'darn' as c, 'simple' as d;
          """
        )
        f.close()
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                simple_id = insert_node(name="simple", value=None)
                insert_query(name="simple.sql", node_id=simple_id)

                insert_route(path="/simple/", node_id=simple_id)

                rv = c.get("/simple", follow_redirects=True)
                assert 200 == rv.status_code
                simple_json = json.loads(rv.data)
                assert "yup" == simple_json["a"]

    def test_rules(self):
        f = open(os.path.join(self.tmp_template_dir, "insert_promoattr.sql"), "w")
        f.write(
            """
          insert into PromoAttr (node_id, title, description) values (:node_id, :title, :description);
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_promoattr.sql"), "w")
        f.write(
            """
          select * from PromoAttr where node_id = :node_id;
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_promos.sql"), "w")
        f.write(
            """
          select id as node_id, * from Node where name = 'promo' order by id limit 2 offset 13;
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_mainmenu.sql"), "w")
        f.write(
            """
          select name as link from Node where name like 'page_' order by link;
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_pageattr.sql"), "w")
        f.write(
            """
          select 'example title' as title, 'a description of the page' as description;
          """
        )
        f.close()

        expected = {
            "mainmenu": [{"link": "page1"}, {"link": "page2"}, {"link": "page3"}],
            "pageattr": {
                "description": "a description of the page",
                "title": "example title",
            },
            "promos": [
                {
                    "promo": {
                        "description": "aaaaaaaaaaaaa",
                        "node_id": 20,
                        "title": "promo 13",
                    }
                },
                {
                    "promo": {
                        "description": "aaaaaaaaaaaaaa",
                        "node_id": 21,
                        "title": "promo 14",
                    }
                },
            ],
        }
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                db.execute(
                    text(
                        """
                create table PromoAttr (
                  node_id integer,
                  abc integer,
                  title varchar(255),
                  description text
                  );
                """
                    )
                )

                page_id = insert_node(name="page1", value=None)
                insert_route(path="/page1/", node_id=page_id)

                pageattr_id = insert_node(name="pageattr", value=None)
                insert_node_node(node_id=page_id, target_node_id=pageattr_id)
                insert_query(name="select_pageattr.sql", node_id=pageattr_id)

                mainmenu_id = insert_node(name="mainmenu", value=None)
                insert_node_node(node_id=page_id, target_node_id=mainmenu_id)
                insert_query(name="select_mainmenu.sql", node_id=mainmenu_id)
                # Add some other pages that will be shown in menu as just links
                insert_node(name="page2", value=None)
                insert_node(name="page3", value=None)

                promos_id = insert_node(name="promos", value=None)
                insert_node_node(node_id=page_id, target_node_id=promos_id)
                insert_query(name="select_promos.sql", node_id=promos_id)

                for a in range(0, 100):
                    a_id = insert_node(name="promo", value=None)
                    db.execute(
                        text(fetch_query_string("insert_promoattr.sql")),
                        **{
                            "node_id": a_id,
                            "title": "promo %i" % a,
                            "description": "a" * a,
                        }
                    )
                    # wire the promo to it's attr
                    insert_query(name="select_promoattr.sql", node_id=a_id)

                rv = c.get("/page1", follow_redirects=True)
                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert 200 == rv.status_code
                rv_json = json.loads(rv.data)
                assert set(expected.keys()) == set(rv_json.keys())
                assert set(expected["pageattr"].keys()) == set(
                    rv_json["pageattr"].keys()
                )


class Template(ChillTestCase):
    def test_some_template(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "base.html"), "w")
        f.write(
            """
          <!doctype html>
          <html><head><title>test</title></head>
          <body>
          <div>{% block content %}{% endblock %}</div>
          </body>
          </html>
          """
        )
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "template_a.html"), "w")
        f.write(
            """
          {% extends "base.html" %}
          {% block content %}
          <h1>template_a</h1>
          {{ value }}
          {% endblock %}
          """
        )
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "template_b.html"), "w")
        f.write(
            """
          {% extends "base.html" %}
          {% block content %}
          <h1>template_b</h1>
          {{ value }}
          {% endblock %}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                test_id = insert_node(name="test one", value="testing one")
                insert_route(path="/test/1/", node_id=test_id)
                add_template_for_node("template_a.html", test_id)

                rv = c.get("/test/1", follow_redirects=True)
                assert b"testing one" in rv.data

                a_id = insert_node(name="a", value="apple")
                insert_route(path="/fruit/a/", node_id=a_id)
                add_template_for_node("template_a.html", a_id)

                rv = c.get("/fruit/a", follow_redirects=True)
                assert b"apple" in rv.data
                assert b"template_a" in rv.data

                b_id = insert_node(name="b", value="banana")
                add_template_for_node("template_b.html", b_id)
                o_id = insert_node(name="orange", value="orange")
                add_template_for_node("template_b.html", o_id)

                eggplant_id = insert_node(name="eggplant", value="eggplant")
                add_template_for_node("template_b.html", eggplant_id)

                # overwrite ( fruit/a use to be set to template_a.html )
                add_template_for_node("template_b.html", a_id)

                rv = c.get("/fruit/a", follow_redirects=True)
                assert b"apple" in rv.data
                assert b"template_b" in rv.data

    def test_some_unicode_as_value_in_template(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "template_unicode.html"), "w")
        f.write(
            """
          <h1>template_unicode</h1>
          {{ isit|safe }}
          """
        )
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "isit.html"), "w")
        f.write(
            """
            <div>template with a unicode {{ value }}</div>
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                test_id = insert_node(name="page", value=None)
                insert_route(path="/test/1/", node_id=test_id)
                add_template_for_node("template_unicode.html", test_id)

                isit = insert_node(name="isit", value=u"Àрpĺè")
                add_template_for_node("isit.html", isit)

                insert_node_node(node_id=test_id, target_node_id=isit)

                rv = c.get("/test/1/", follow_redirects=True)
                assert u"Àрpĺè" in rv.data.decode("utf-8")

    def test_dict(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "llama.html"), "w")
        f.write(
            """
          <!doctype html>
          <html><head><title>llama</title></head>
          <body>
          <h1>template for llama_name</h1>
          {{ llama_name }}
          </body>
          </html>
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_llama.sql"), "w")
        f.write(
            """
          select :llama_name as llama_name;
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                a = insert_node(name="a", value=None)
                insert_route(path="/a/<llama_name>/", node_id=a)
                insert_query(name="select_llama.sql", node_id=a)
                add_template_for_node("llama.html", a)

                rv = c.get("/a/chuck/", follow_redirects=True)
                assert b"chuck" in rv.data
                rv = c.get("/a/chase/", follow_redirects=True)
                assert b"chase" in rv.data

    def test_chill_now(self):
        """
        Check that the chill_now timestamp is available for templates to use
        """
        f = open(os.path.join(self.tmp_template_dir, "chill_now.html"), "w")
        f.write(
            """
          {% if chill_now %}timestamp: {{ chill_now }}{% endif %}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                a = insert_node(name="a", value=None)
                insert_route(path="/a/", node_id=a)
                add_template_for_node("chill_now.html", a)

                rv = c.get("/a/", follow_redirects=True)
                # self.app.logger.debug(rv.data)
                assert b"timestamp" in rv.data


class Filters(ChillTestCase):
    def test_datetime_filter(self):
        """
        The custom 'datetime' jinja2 filter converts a timestamp to a formatted
        date string.
        """
        f = open(os.path.join(self.tmp_template_dir, "datetime.html"), "w")
        f.write(
            """
          {% set timestamp=1576122368 %}date and time:  {{ timestamp|datetime('y-MM-dd') }}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                a = insert_node(name="a", value=None)
                insert_route(path="/a/", node_id=a)
                add_template_for_node("datetime.html", a)

                rv = c.get("/a/", follow_redirects=True)
                # self.app.logger.debug(rv.data)
                assert b"2019-12-12" in rv.data

    def test_timedelta_filter(self):
        """
        The custom 'timedelta' jinja2 filter wraps around the babel format_timedelta.
        """
        f = open(os.path.join(self.tmp_template_dir, "timedelta.html"), "w")
        f.write(
            """
          {% set timesince=847 %}time since:  {{ timesince|timedelta }}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                a = insert_node(name="a", value=None)
                insert_route(path="/a/", node_id=a)
                add_template_for_node("timedelta.html", a)

                rv = c.get("/a/", follow_redirects=True)
                # self.app.logger.debug(rv.data)
                assert b"14 minutes" in rv.data


class Documents(ChillTestCase):
    def test_reading_in_a_document(self):
        """
        The custom 'readfile' jinja2 filter reads the file from the DOCUMENT_FOLDER.
        """
        f = open(os.path.join(self.tmp_template_dir, "imasimplefile.txt"), "w")
        f.write(
            """
          Hello, this is just a file.
          """
        )
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "template.html"), "w")
        f.write(
            """
          <h1>template</h1>
          {{ simplefilename }}
          <br>
          {{ simplefilename|readfile }}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                a = insert_node(name="simplefilename", value="imasimplefile.txt")
                apage = insert_node(name="apage", value=None)
                insert_node_node(node_id=apage, target_node_id=a)
                insert_route(path="/a/", node_id=apage)
                add_template_for_node("template.html", apage)

                rv = c.get("/a/", follow_redirects=True)
                assert b"Hello" in rv.data

    def test_reading_in_a_document_with_unicode(self):
        """
        The custom 'readfile' jinja2 filter reads the file with unicode characters from the DOCUMENT_FOLDER.
        """
        f = open(
            os.path.join(self.tmp_template_dir, "imasimplefilewithunicode.txt"), "w"
        )
        f.write(
            """
          Hello, this is an Àрpĺè.
          [chill route /cat/picture/ ]
          """
        )
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "template.html"), "w")
        f.write(
            """
          <h1>template</h1>
          {{ simplefilename }}
          <br>
          {{ simplefilename|readfile|safe|shortcodes }}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                catimg = insert_node(
                    name="acat", value="<img alt='a picture of a cat'/>"
                )
                insert_route(path="/cat/picture/", node_id=catimg)

                a = insert_node(
                    name="simplefilename", value="imasimplefilewithunicode.txt"
                )
                apage = insert_node(name="apage", value=None)
                insert_node_node(node_id=apage, target_node_id=a)
                insert_route(path="/a/", node_id=apage)
                add_template_for_node("template.html", apage)

                rv = c.get("/a/", follow_redirects=True)
                assert bytes("Àрpĺè", "utf-8") in rv.data

                assert b"<img alt='a picture of a cat'/>" in rv.data
                assert b"[chill route /cat/picture/ ]" not in rv.data

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
        f = open(os.path.join(self.tmp_template_dir, "imasimplefile.md"), "w")
        f.write(md)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "template.html"), "w")
        f.write(
            """
          {{ simplefilename|readfile|markdown }}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                a = insert_node(name="simplefilename", value="imasimplefile.md")
                apage = insert_node(name="apage", value=None)
                insert_node_node(node_id=apage, target_node_id=a)
                insert_route(path="/a/", node_id=apage)
                add_template_for_node("template.html", apage)

                rv = c.get("/a/", follow_redirects=True)
                # self.app.logger.debug('data: %s', rv.data.decode('utf-8'))
                # self.app.logger.debug('html: %s', html)
                assert bytes(html, "utf-8") in rv.data


class ShortcodeRoute(ChillTestCase):
    def test_route(self):
        "Expand the route shortcode"

        f = open(os.path.join(self.tmp_template_dir, "simple.html"), "w")
        f.write(
            """
          <!doctype html>
          <html><head><title>test</title></head>
          <body>
          <div>
          {{ cat|shortcodes }}
          </div>
          </body>
          </html>
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name="page", value=None)
                insert_route(path="/", node_id=page)
                add_template_for_node("simple.html", page)

                catimg = insert_node(
                    name="acat", value="<img alt='a picture of a cat'/>"
                )
                insert_route(path="/cat/picture/", node_id=catimg)

                text = "something [chill route /cat/picture/ ] [blah blah[chill route /dog/pic] the end"
                textnode = insert_node(name="cat", value=text)

                insert_node_node(node_id=page, target_node_id=textnode)

                rv = c.get("/", follow_redirects=True)
                assert (
                    b"something <img alt='a picture of a cat'/> [blah blah<!-- 404 '/dog/pic' --> the end"
                    in rv.data
                )
                assert b"[chill route /cat/picture/ ]" not in rv.data

                rv = c.get("/cat/picture/", follow_redirects=True)
                assert b"<img alt='a picture of a cat'/>" in rv.data

    def test_route_with_unicode(self):
        "Expand the route shortcode with unicode contents"

        f = open(os.path.join(self.tmp_template_dir, "simple.html"), "w")
        f.write(
            """
          <!doctype html>
          <html><head><title>test</title></head>
          <body>
          <div>
          {{ cat|shortcodes }}
          </div>
          </body>
          </html>
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name="page", value=None)
                insert_route(path="/", node_id=page)
                add_template_for_node("simple.html", page)

                catimg = insert_node(name="acat", value=u"Àрpĺè")
                insert_route(path="/cat/picture/", node_id=catimg)

                text = "something [chill route /cat/picture/ ] [blah blah[chill route /dog/pic] the end"
                textnode = insert_node(name="cat", value=text)

                insert_node_node(node_id=page, target_node_id=textnode)

                rv = c.get("/", follow_redirects=True)
                assert (
                    bytes(
                        "something Àрpĺè [blah blah<!-- 404 '/dog/pic' --> the end",
                        "utf-8",
                    )
                    in rv.data
                )
                assert b"[chill route /cat/picture/ ]" not in rv.data

                rv = c.get("/cat/picture/", follow_redirects=True)
                assert bytes("Àрpĺè", "utf-8") in rv.data


class ShortcodePageURI(ChillTestCase):
    def test_page_uri(self):
        "Expand the page_uri shortcode"

        f = open(os.path.join(self.tmp_template_dir, "simple.html"), "w")
        f.write(
            """
          <!doctype html>
          <html><head><title>test</title></head>
          <body>
          <div>
          {{ cat|shortcodes }}
          </div>
          </body>
          </html>
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                page = insert_node(name="page", value=None)
                insert_route(path="/", node_id=page)
                add_template_for_node("simple.html", page)

                catpage = insert_node(name="acat", value="a page for cat")
                insert_route(path="/cat/", node_id=catpage)

                text = "something link for cat page that does exist = '[chill page_uri cat ]' link for dog that does not exist = '[chill page_uri dog]'"
                textnode = insert_node(name="cat", value=text)

                insert_node_node(node_id=page, target_node_id=textnode)

                rv = c.get("/", follow_redirects=True)
                assert (
                    b"something link for cat page that does exist = '/cat/' link for dog that does not exist = '/dog/'"
                    in rv.data
                )
                assert b"[chill page_uri cat ]" not in rv.data

                rv = c.get("/cat/", follow_redirects=True)
                assert b"a page for cat" in rv.data

                rv = c.get("/dog/", follow_redirects=True)
                assert 404 == rv.status_code


class PostMethod(ChillTestCase):
    def test_a(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "insert_llama.sql"), "w")
        f.write(
            """
          insert into Llama (llama_name, location, description) values (:llama_name, :location, :description);
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_llama.sql"), "w")
        f.write(
            """
          select * from Llama
          where llama_name = :llama_name;
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                db.execute(
                    text(
                        """
                create table Llama (
                  llama_name varchar(255),
                  location varchar(255),
                  description text
                  );
                """
                    )
                )

                llamas_id = insert_node(name="llamas", value=None)
                insert_route(
                    path="/api/llamas/", node_id=llamas_id, weight=1, method="POST"
                )
                insert_query(name="insert_llama.sql", node_id=llamas_id)

                llama_1 = {
                    "llama_name": "Rocky",
                    "location": "unknown",
                    "description": "first llama",
                }
                rv = c.post("/api/llamas/", data=llama_1)
                assert 201 == rv.status_code

                llama_2 = {
                    "llama_name": "Nocky",
                    "location": "unknown",
                    "description": "second llama",
                }
                rv = c.post("/api/llamas/", data=llama_2)
                assert 201 == rv.status_code

                select_llama = insert_node(name="llamas", value=None)
                insert_route(
                    path="/api/llamas/name/<llama_name>/",
                    node_id=select_llama,
                    weight=1,
                )
                insert_query(name="select_llama.sql", node_id=select_llama)

                rv = c.get("/api/llamas/name/Rocky/", follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert set(llama_1.keys()) == set(rv_json.keys())
                assert set(llama_1.values()) == set(rv_json.values())

                rv = c.get("/api/llamas/name/Nocky/", follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert set(llama_2.keys()) == set(rv_json.keys())
                assert set(llama_2.values()) == set(rv_json.values())


class PutMethod(ChillTestCase):
    def test_a(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "insert_llama.sql"), "w")
        f.write(
            """
          insert into Llama (llama_name, location, description) values (:llama_name, :location, :description);
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_llama.sql"), "w")
        f.write(
            """
          select * from Llama
          where llama_name = :llama_name;
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                db.execute(
                    text(
                        """
                create table Llama (
                  llama_name varchar(255),
                  location varchar(255),
                  description text
                  );
                """
                    )
                )

                llamas_id = insert_node(name="llamas", value=None)
                insert_route(
                    path="/api/llamas/name/<llama_name>/",
                    node_id=llamas_id,
                    weight=1,
                    method="PUT",
                )
                insert_query(name="insert_llama.sql", node_id=llamas_id)

                llama_1 = {
                    "llama_name": "Socky",
                    "location": "unknown",
                    "description": "first llama",
                }
                rv = c.put("/api/llamas/name/Socky/", data=llama_1)
                assert 201 == rv.status_code

                select_llama = insert_node(name="llamas", value=None)
                insert_route(
                    path="/api/llamas/name/<llama_name>/",
                    node_id=select_llama,
                    weight=1,
                )
                insert_query(name="select_llama.sql", node_id=select_llama)

                rv = c.get("/api/llamas/name/Socky/", follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert set(llama_1.keys()) == set(rv_json.keys())
                assert set(llama_1.values()) == set(rv_json.values())


class PatchMethod(ChillTestCase):
    def test_a(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "update_llama.sql"), "w")
        f.write(
            """
          update Llama set location = :location, description = :description where llama_name = :llama_name;
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_llama.sql"), "w")
        f.write(
            """
          select * from Llama
          where llama_name = :llama_name;
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                db.execute(
                    text(
                        """
                create table Llama (
                  llama_name varchar(255),
                  location varchar(255),
                  description text
                  );
                """
                    )
                )

                db.execute(
                    text(
                        """
                  insert into Llama (llama_name) values ('Pocky');
                """
                    )
                )

                llamas_id = insert_node(name="llamas", value=None)
                insert_route(
                    path="/api/llamas/name/<llama_name>/",
                    node_id=llamas_id,
                    weight=1,
                    method="PATCH",
                )
                insert_query(name="update_llama.sql", node_id=llamas_id)

                llama_1 = {
                    "llama_name": "Pocky",
                    "location": "unknown",
                    "description": "first llama",
                }
                rv = c.patch("/api/llamas/name/Pocky/", data=llama_1)
                assert 201 == rv.status_code

                select_llama = insert_node(name="llamas", value=None)
                insert_route(
                    path="/api/llamas/name/<llama_name>/",
                    node_id=select_llama,
                    weight=1,
                )
                insert_query(name="select_llama.sql", node_id=select_llama)

                rv = c.get("/api/llamas/name/Pocky/", follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert set(llama_1.keys()) == set(rv_json.keys())
                assert set(llama_1.values()) == set(rv_json.values())


class DeleteMethod(ChillTestCase):
    def test_a(self):
        """
        """
        f = open(os.path.join(self.tmp_template_dir, "delete_llama.sql"), "w")
        f.write(
            """
          Delete from Llama where llama_name = :llama_name;
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_llama.sql"), "w")
        f.write(
            """
          select * from Llama
          where llama_name = :llama_name;
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                db.execute(
                    text(
                        """
                create table Llama (
                  llama_name varchar(255),
                  location varchar(255),
                  description text
                  );
                """
                    )
                )

                db.execute(
                    text(
                        """
                  insert into Llama (llama_name, location, description) values ('Docky', 'somewhere', 'damaged');
                """
                    )
                )

                select_llama = insert_node(name="llamas", value=None)
                insert_route(
                    path="/api/llamas/name/<llama_name>/",
                    node_id=select_llama,
                    weight=1,
                )
                insert_query(name="select_llama.sql", node_id=select_llama)

                llamas_id = insert_node(name="llamas", value=None)
                insert_route(
                    path="/api/llamas/name/<llama_name>/",
                    node_id=llamas_id,
                    weight=1,
                    method="DELETE",
                )
                insert_query(name="delete_llama.sql", node_id=llamas_id)

                rv = c.get("/api/llamas/name/Docky/", follow_redirects=True)
                assert 200 == rv.status_code

                rv = c.delete("/api/llamas/name/Docky/")
                assert 204 == rv.status_code

                rv = c.get("/api/llamas/name/Docky/", follow_redirects=True)
                assert 404 == rv.status_code


class YAMLChillNode(ChillTestCase):
    def check_dump(self, expected_chill_nodes=None):
        test_dump_file = os.path.join(self.tmp_template_dir, "test-data-dump.yaml")
        dump_yaml(test_dump_file)

        with open(test_dump_file, "r") as f:
            contents = f.read()
            self.app.logger.debug("contents {}".format(contents))
            self.app.logger.debug("expected {}".format(expected_chill_nodes))
            documents = yaml.safe_load_all(contents)
            for item in documents:
                self.app.logger.debug("check_dump {}".format(item))
                assert isinstance(item, ChillNode) == True

                if isinstance(expected_chill_nodes, list):
                    match = expected_chill_nodes.pop(
                        expected_chill_nodes.index(str(item))
                    )
                    assert match == str(item)

    def test_route_simple_value(self):
        """
        Create a node with a string value and route
        """
        yaml_content = """
--- !ChillNode
name: simple_value_at_route
route: /simple/
value: "simple string value"
        """
        expected_chill_nodes = [
            "ChillNode(name='simple_value_at_route', value='simple string value', template=None, route='/simple/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/simple/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("simple string value", "utf-8") in rv.data

                self.check_dump(expected_chill_nodes)

    def test_multiple_route_simple_value(self):
        """
        Create two nodes with a string value and route
        """
        yaml_content = """
--- !ChillNode
name: simple_value_at_route
route: /simple/
value: "simple string value"

--- !ChillNode
name: another_value_at_route
route: /another/
value: "another string value"
        """
        expected_chill_nodes = [
            "ChillNode(name='simple_value_at_route', value='simple string value', template=None, route='/simple/')",
            "ChillNode(name='another_value_at_route', value='another string value', template=None, route='/another/')",
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/simple/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("simple string value", "utf-8") in rv.data

                rv = c.get("/another/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("another string value", "utf-8") in rv.data

                self.check_dump(expected_chill_nodes)

    def test_route_query_value(self):
        """
        Create a node with a query value and route
        """
        yaml_content = """
--- !ChillNode
name: query_value_at_route
route: /total-count/
value: get-total-count.sql
        """
        expected_chill_nodes = [
            "ChillNode(name='query_value_at_route', value='get-total-count.sql', template=None, route='/total-count/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "get-total-count.sql"), "w")
        f.write("""select 26 as count;""")
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/total-count/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                data = json.loads(rv.data)
                assert 26 == data["count"]

                self.check_dump(expected_chill_nodes)

    def test_method_and_weight_route_value(self):
        """
        Create a node with a route using specific method and weight values.
        """
        yaml_content = """
--- !ChillNode
name: llamas
route:
    path: /api/llamas/
    method: POST
value: insert_llama.sql

--- !ChillNode
name: llamas
route:
    path: /api/llamas/name/<llama_name>/
value: select_llama.sql
        """
        expected_chill_nodes = [
            "ChillNode(name='llamas', value='insert_llama.sql', template=None, route={'method': 'POST', 'path': '/api/llamas/'})",
            "ChillNode(name='llamas', value='select_llama.sql', template=None, route='/api/llamas/name/<llama_name>/')",
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "insert_llama.sql"), "w")
        f.write(
            """
          insert into Llama (llama_name, location, description) values (:llama_name, :location, :description);
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "select_llama.sql"), "w")
        f.write(
            """
          select * from Llama
          where llama_name = :llama_name;
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()
                db.execute(
                    text(
                        """
                create table Llama (
                  llama_name varchar(255),
                  location varchar(255),
                  description text
                  );
                """
                    )
                )

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                llama_1 = {
                    "llama_name": "Rocky",
                    "location": "unknown",
                    "description": "first llama",
                }
                rv = c.post("/api/llamas/", data=llama_1)
                assert 201 == rv.status_code

                llama_2 = {
                    "llama_name": "Nocky",
                    "location": "unknown",
                    "description": "second llama",
                }
                rv = c.post("/api/llamas/", data=llama_2)
                assert 201 == rv.status_code

                rv = c.get("/api/llamas/name/Rocky/", follow_redirects=True)
                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                rv_json = json.loads(rv.data)
                assert set(llama_1.keys()) == set(rv_json.keys())
                assert set(llama_1.values()) == set(rv_json.values())

                rv = c.get("/api/llamas/name/Nocky/", follow_redirects=True)
                rv_json = json.loads(rv.data)
                assert set(llama_2.keys()) == set(rv_json.keys())
                assert set(llama_2.values()) == set(rv_json.values())

                self.check_dump(expected_chill_nodes)

    def test_template_simple_value(self):
        """
        Create a node with a string value and template
        """
        yaml_content = """
--- !ChillNode
name: simple_value_at_route
route: /simple-template/
template: test.html
value: "simple"
        """
        expected_chill_nodes = [
            "ChillNode(name='simple_value_at_route', value='simple', template='test.html', route='/simple-template/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "test.html"), "w")
        f.write(
            """
          <h1>test template</h1>
          {{ value }}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/simple-template/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("test template", "utf-8") in rv.data
                assert bytes("simple", "utf-8") in rv.data

                self.check_dump(expected_chill_nodes)

    def test_rendered_value(self):
        """
        Create a node with a query value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value:
    content: "hello"
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value={'content': 'hello'}, template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("hello", "utf-8") in rv.data

                self.check_dump(expected_chill_nodes)

    def test_rendered_chill_value(self):
        """
        Create a node with a query chill_value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value:
    content:
        chill_value: "hello"
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value={'content': 'hello'}, template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("hello", "utf-8") in rv.data

                self.check_dump(expected_chill_nodes)

    def test_bool_value(self):
        """
        Raise TypeError for a node with a boolean value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
# Boolean values like Yes, No, true, False are not supported. Use a string value
# like 'Yes' or 'false'.
value: Yes
        """

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                try:
                    load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))
                except TypeError as err:
                    self.app.logger.debug(err)

                rv = c.get("/", follow_redirects=True)
                assert 404 == rv.status_code

    def test_sub_bool_value(self):
        """
        Raise TypeError for a node with a sub boolean value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
# Boolean values like Yes, No, true, False are not supported. Use a string value
# like 'Yes' or 'false'.
value:
    content: yes
        """

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                try:
                    load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))
                except TypeError as err:
                    self.app.logger.debug(err)

                rv = c.get("/", follow_redirects=True)
                assert 404 == rv.status_code

    def test_sub_list_bool_value(self):
        """
        Raise TypeError for a node with a sub boolean value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
# Boolean values like Yes, No, true, False are not supported. Use a string value
# like 'Yes' or 'false'.
value:
    - yes
    - no
        """

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                try:
                    load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))
                except TypeError as err:
                    self.app.logger.debug(err)

                rv = c.get("/", follow_redirects=True)
                assert 404 == rv.status_code

    def test_bool_chill_value(self):
        """
        Raise TypeError for a node with a boolean chill_value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value:
    content:
        chill_value: Yes
        """

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                try:
                    load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))
                except TypeError as err:
                    self.app.logger.debug(err)

                rv = c.get("/", follow_redirects=True)
                assert 404 == rv.status_code

    def test_none_value(self):
        """
        Handle None value
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value: None
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value='None', template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                try:
                    load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))
                except TypeError as err:
                    self.app.logger.debug(err)

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.check_dump(expected_chill_nodes)

    def test_multiple_rendered_value(self):
        """
        Create a node with multiple string value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value:
    content: "hello"
    title: "a title here"
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value={'content': 'hello', 'title': 'a title here'}, template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("hello", "utf-8") in rv.data
                assert bytes("a title here", "utf-8") in rv.data

                self.check_dump(expected_chill_nodes)

    def test_rendered_list_value(self):
        """
        Create a node with a list value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /list/
value:
    - "a is for aardvark"
    - "b is for bat"
    - "c is for cat"
    - 1234
    - 'Yes'
    - 'No'
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value=[{'value': 'a is for aardvark'}, {'value': 'b is for bat'}, {'value': 'c is for cat'}, {'value': '1234'}, {'value': 'Yes'}, {'value': 'No'}], template=None, route='/list/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/list/", follow_redirects=True)
                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert 200 == rv.status_code

                json_response = json.loads(rv.data)
                assert "a is for aardvark" == json_response[0]["value"]
                assert "1234" == json_response[3]["value"]
                assert "Yes" == json_response[4]["value"]
                assert "No" == json_response[5]["value"]

                self.check_dump(expected_chill_nodes)

    def test_rendered_sub_list_value(self):
        """
        Create a node with a sub list value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /list/
value:
    - "a is for aardvark"
    -
        page:
            top: 'Yes'
            menu:
                - "one"
                - "two"
            bottom: 'No'
    - "c is for cat"
    - 1234
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value=[{'value': 'a is for aardvark'}, {'value': {'page': {'bottom': 'No', 'menu': [{'menu': 'one'}, {'menu': 'two'}], 'top': 'Yes'}}}, {'value': 'c is for cat'}, {'value': '1234'}], template=None, route='/list/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/list/", follow_redirects=True)
                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert 200 == rv.status_code

                json_response = json.loads(rv.data)
                assert "a is for aardvark" == json_response[0]["value"]
                assert "one" == json_response[1]["value"]["page"]["menu"][0]["menu"]
                assert "two" == json_response[1]["value"]["page"]["menu"][1]["menu"]
                assert "1234" == json_response[3]["value"]

                self.check_dump(expected_chill_nodes)

    def test_recursive_rendered_string_value(self):
        """
        Create a node with recursive query string value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value:
    page:
        content: an-example-doc.html
        description: >
            Description would go here and can be
            multiple lines.
        title: "a title here"
        menu2:
            one: 'cat'
            two: 'dog'
            footer:
                one: 'kitten'
                two: 'puppy'
                three: 'tadpole'
        menu:
            one: 'cat'
            two: 'dog'
            footer:
                one: 'kitten'
                two: 'puppy'
                three: 'tadpole'
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value={'page': {'content': 'an-example-doc.html', 'description': 'Description would go here and can be multiple lines.\\n', 'menu': {'footer': {'one': 'kitten', 'three': 'tadpole', 'two': 'puppy'}, 'one': 'cat', 'two': 'dog'}, 'menu2': {'footer': {'one': 'kitten', 'three': 'tadpole', 'two': 'puppy'}, 'one': 'cat', 'two': 'dog'}, 'title': 'a title here'}}, template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                json_response = json.loads(rv.data)
                assert "an-example-doc.html" == json_response["page"]["content"]
                assert (
                    "Description would go here and can be multiple lines.\n"
                    == json_response["page"]["description"]
                )
                assert "a title here" == json_response["page"]["title"]
                assert "tadpole" == json_response["page"]["menu"]["footer"]["three"]

                self.check_dump(expected_chill_nodes)

    def test_recursive_rendered_query_value(self):
        """
        Create a node with recursive query value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value:
    total_count: get-total-count.sql
    best: get-best-animal.sql
    simple: simple.sql
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value={'best': 'get-best-animal.sql', 'simple': 'simple.sql', 'total_count': 'get-total-count.sql'}, template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "get-total-count.sql"), "w")
        f.write("""select 26 as value;""")
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "get-best-animal.sql"), "w")
        f.write("""select 'kangaroo' as value;""")
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "simple.sql"), "w")
        f.write(
            """
          select 'yup' as a, 'pretty' as b, 'darn' as c, 'simple' as d;
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                json_response = json.loads(rv.data)
                assert 26 == json_response["total_count"]["value"]
                assert "kangaroo" == json_response["best"]["value"]
                assert "yup" == json_response["simple"]["a"]

                self.check_dump(expected_chill_nodes)

    def test_recursive_rendered_query_and_string_value(self):
        """
        Create a node with recursive query value and string value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value:
    page:
        total_count: get-total-count.sql
        description: >
            Description would go here and can be
            multiple lines.
        title: "a title here"
        menu:
            one: 'cat'
            two: 'dog'
            footer:
                one: 'kitten'
                two: 'puppy'
                three: 'tadpole'
                best: get-best-animal.sql
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value={'page': {'description': 'Description would go here and can be multiple lines.\\n', 'menu': {'footer': {'best': 'get-best-animal.sql', 'one': 'kitten', 'three': 'tadpole', 'two': 'puppy'}, 'one': 'cat', 'two': 'dog'}, 'title': 'a title here', 'total_count': 'get-total-count.sql'}}, template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "get-total-count.sql"), "w")
        f.write("""select 26 as value;""")
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "get-best-animal.sql"), "w")
        f.write("""select 'kangaroo' as value;""")
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                json_response = json.loads(rv.data)
                assert 26 == json_response["page"]["total_count"]["value"]
                assert (
                    "Description would go here and can be multiple lines.\n"
                    == json_response["page"]["description"]
                )
                assert "a title here" == json_response["page"]["title"]
                assert "tadpole" == json_response["page"]["menu"]["footer"]["three"]
                assert (
                    "kangaroo"
                    == json_response["page"]["menu"]["footer"]["best"]["value"]
                )

                self.check_dump(expected_chill_nodes)

    def test_query_with_list_value(self):
        """
        Create a node with query list value and route
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value: get-list-of-animals.sql
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value='get-list-of-animals.sql', template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "get-list-of-animals.sql"), "w")
        f.write("""select name, description from Animal;""")
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                db.execute(
                    text(
                        """
                create table Animal (
                  id integer,
                  name varchar(30),
                  description text
                  );
                """
                    )
                )
                db.execute(
                    text(
                        "insert into Animal (name, description) values ('horse', '4 legged furry thing');"
                    )
                )
                db.execute(
                    text(
                        "insert into Animal (name, description) values ('llama', 'furry thing with four legs');"
                    )
                )
                db.execute(
                    text(
                        "insert into Animal (name, description) values ('cow', 'a furry thing that also has 4 legs');"
                    )
                )

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                json_response = json.loads(rv.data)
                assert "horse" == json_response[0]["name"]
                assert "cow" == json_response[2]["name"]

                self.check_dump(expected_chill_nodes)

    def test_rendered_chill_value_with_template(self):
        """
        Create a node with a query chill_value and chill_template
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value:
    content:
        chill_value: "hello"
        chill_template: "hello.html"
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value={'content': {'chill_template': 'hello.html', 'chill_value': 'hello'}}, template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "hello.html"), "w")
        f.write(
            """
          <h1>greeting template</h1>
          {{ value }}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("hello", "utf-8") in rv.data

                self.check_dump(expected_chill_nodes)

    def test_rendered_value_with_template_and_no_chill_value(self):
        """
        Create a node with a query value and only chill_template
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
value:
    content:
        chill_template: "hello.html"
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value={'content': {'chill_template': 'hello.html'}}, template=None, route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "hello.html"), "w")
        f.write(
            """
          <h1>greeting template</h1>
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("greeting", "utf-8") in rv.data

                self.check_dump(expected_chill_nodes)

    def test_sub_chill_template_chill_value(self):
        """
        Create a node with nested chill_template and chill_value
        """
        yaml_content = """
--- !ChillNode
name: page
route: /
template: page.html
value:
    content:
        chill_template: "hello.html"
        chill_value:
            - item:
                chill_value: "one"
                chill_template: one.html
            - item:
                chill_value: "two"
                chill_template: two.html
            - item:
                chill_value:
                    - subitem: "thr"
                    - subitem: "ee"
                chill_template: three.html
        """
        expected_chill_nodes = [
            "ChillNode(name='page', value={'content': {'chill_template': 'hello.html', 'chill_value': [{'content': {'item': {'chill_template': 'one.html', 'chill_value': 'one'}}}, {'content': {'item': {'chill_template': 'two.html', 'chill_value': 'two'}}}, {'content': {'item': {'chill_template': 'three.html', 'chill_value': [{'item': {'subitem': 'thr'}}, {'item': {'subitem': 'ee'}}]}}}]}}, template='page.html', route='/')"
        ]

        f = open(os.path.join(self.tmp_template_dir, "test-data.yaml"), "w")
        f.write(yaml_content)
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "page.html"), "w")
        f.write(
            """
          page
          {{ content|safe }}
          """
        )
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "hello.html"), "w")
        f.write(
            """
          <h1>greeting template</h1>
          {% for item in value %}
          {{ item.content.item|safe }}
          {% endfor %}
          """
        )
        f.close()

        f = open(os.path.join(self.tmp_template_dir, "one.html"), "w")
        f.write(
            """
            <span>First</span> {{ value }}
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "two.html"), "w")
        f.write(
            """
            <span>Second</span> {{ value }}
          """
        )
        f.close()
        f = open(os.path.join(self.tmp_template_dir, "three.html"), "w")
        f.write(
            """
            <span>Third</span> {% for item in value -%} {{ item.item.subitem }}{%- endfor %}
          """
        )
        f.close()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                load_yaml(os.path.join(self.tmp_template_dir, "test-data.yaml"))

                rv = c.get("/", follow_redirects=True)
                assert 200 == rv.status_code

                self.app.logger.debug("data: %s", rv.data.decode("utf-8"))
                assert bytes("greeting", "utf-8") in rv.data

                self.check_dump(expected_chill_nodes)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(NothingConfigured))
    suite.addTest(unittest.makeSuite(SimpleCheck))
    return suite


if __name__ == "__main__":
    unittest.main()
