#chill - Simple Frozen website management
#Copyright (C) 2012  Jake Hickenlooper
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import unittest

import chill.app

TEST_CFG = os.path.join(os.path.dirname(__file__), 'test.cfg')

class Mixin(object):
    def setUp(self):
        """Before each test, set up a blank database"""
        self.app = chill.app.make_app(config=TEST_CFG, debug=True)
        self.test_client = self.app.test_client()

    def tearDown(self):
        """Get rid of the database again after each test."""
        pass

class IndexTestCase(Mixin, unittest.TestCase):

    def test_index_page(self):
        """Test index page."""

        # all get the same page
        rv = self.test_client.get('/index.html', follow_redirects=True)
        assert 'stuff goes here' in rv.data
        rv = self.test_client.get('/')
        assert 'stuff goes here' in rv.data

    def test_simple_page(self):
        """Test simple page."""
        rv = self.test_client.get('/simple/')
        assert 'a simple page' in rv.data
        rv = self.test_client.get('/simple/index.html', follow_redirects=True)
        assert 'a simple page' in rv.data

    def test_simple_index_page(self):
        """Test simple sub index page."""
        rv = self.test_client.get('/simple/')
        assert 'a index within the simple directory' not in rv.data
        rv = self.test_client.get('/simple/index/')
        assert 'a index within the simple directory' in rv.data
        rv = self.test_client.get('/simple/index/index.html', follow_redirects=True)
        assert 'a index within the simple directory' in rv.data

    def test_sub_page(self):
        """Test sub page."""
        rv = self.test_client.get('/simple/subpage/')
        assert 'a simple subpage' in rv.data
        rv = self.test_client.get('/simple/subpage/index.html', follow_redirects=True)
        assert 'a simple subpage' in rv.data

class CascadeTestCase(Mixin, unittest.TestCase):

    def test_one_page(self):
        """Test one page."""
        rv = self.test_client.get('/cascade_test/five/four/three/two/one/')
        assert 'one content page' in rv.data

    def test_empty_page(self):
        """Test empty page."""
        rv = self.test_client.get('/cascade_test/five/four/three/')
        assert 'cascade test parent page' in rv.data

class YAMLDataCascadeTestCase(Mixin, unittest.TestCase):

    def test_top_level_yaml(self):
        rv = self.test_client.get('/')
        assert 'Chill Examples and Tests' in rv.data

    def test_yaml_and_txt_conflict(self):
        rv = self.test_client.get('/simple/')
        assert 'just a simple page' in rv.data
        assert 'this pagetitle gets replaced by the pagetitle.txt' not in rv.data

    def test_replace_top_yaml(self):
        rv = self.test_client.get('/simple/')
        assert 'Simple sitetitle' in rv.data

class YAMLDataTestCase(Mixin, unittest.TestCase):

    def test_menu_yaml(self):
        rv = self.test_client.get('/')
        assert 'imatitleinamenu' in rv.data

class ResourceFileTestCase(Mixin, unittest.TestCase):

    def test_if_file_exists(self):
        rv = self.test_client.get('/test.js')
        assert 'test.js file in data path' in rv.data

    def test_for_file_outside_of_data_path(self):
        " test for file outside of data path "
        rv = self.test_client.get('/../cantgetthisfile.js')
        assert 'Should NOT be able to retreive this file!' not in rv.data

        rv = self.test_client.get('/../../cantgetthisfile.js')
        assert 'Should NOT be able to retreive this file!' not in rv.data

    def test_for_file_way_outside_of_data_path(self):
        " test for file way outside of data path "
        rv = self.test_client.get('/../../../../README.txt')
        assert 404 == rv.status_code

    def test_for_file_outside_of_data_path_but_get_other(self):
        " test for file outside of data path but get other "
        rv = self.test_client.get('/../../cantgetthisfile.js', follow_redirects=True)
        assert 200 == rv.status_code
        assert 'This file will be returned instead of the one above this directory' in rv.data

    def test_for_humans(self):
        " humans? "
        rv = self.test_client.get('/humans.txt', follow_redirects=True)
        assert 200 == rv.status_code

    def test_for_page_fragment(self):
        " page fragments viewable "
        rv = self.test_client.get('/content.html', follow_redirects=True)
        assert 200 == rv.status_code
        rv = self.test_client.get('/_data.yaml', follow_redirects=True)
        assert 200 == rv.status_code

    def test_no_dot_files(self):
        " no dot files accessible "
        rv = self.test_client.get('/.nope.txt', follow_redirects=True)
        assert 404 == rv.status_code
        rv = self.test_client.get('/simple/.nope.html', follow_redirects=True)
        assert 404 == rv.status_code

    def test_no_dot_directories(self):
        " no dot directories accessible "
        rv = self.test_client.get('/.imadot/nope.txt', follow_redirects=True)
        assert 404 == rv.status_code
        rv = self.test_client.get('/simple/.imadot/nope.html', follow_redirects=True)
        assert 404 == rv.status_code

class ThemeFileTestCase(Mixin, unittest.TestCase):

    def test_if_css_file_exists(self):
        " check if site.css file in default theme css directory exists "
        rv = self.test_client.get('/_themes/default/css/site.css')
        assert 200 == rv.status_code

    def test_if_mustache_file_exists(self):
        " check if base.mustache file can be accessed"
        rv = self.test_client.get('/_themes/default/base.mustache')
        assert 200 == rv.status_code

class MustacheDataTestCase(Mixin, unittest.TestCase):

    def test_mustache_wrap(self):
        " content.html and content.mustache no conflict "
        rv = self.test_client.get('/simple/mustache/')
        assert "Some content that should be inside the content.mustache template." in rv.data
        assert "mustache file with same name as a page fragment" in rv.data


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IndexTestCase))
    suite.addTest(unittest.makeSuite(YAMLDataTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()

