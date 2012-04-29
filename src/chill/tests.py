import unittest
import chill


class IndexTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.app = chill.app.test_client()
        chill.init_db()

    def tearDown(self):
        """Get rid of the database again after each test."""
        pass

    def test_index_page(self):
        """Test index page."""

        # all get the same page
        rv = self.app.get('/index.html')
        assert 'stuff goes here' in rv.data
        rv = self.app.get('/')
        assert 'stuff goes here' in rv.data

    def test_simple_page(self):
        """Test simple page."""
        rv = self.app.get('/simple/')
        assert 'a simple page' in rv.data
        rv = self.app.get('/simple/index.html')
        assert 'a simple page' in rv.data

    def test_simple_index_page(self):
        """Test simple sub index page."""
        rv = self.app.get('/simple/')
        assert 'a index within the simple directory' not in rv.data
        rv = self.app.get('/simple/index/')
        assert 'a index within the simple directory' in rv.data
        rv = self.app.get('/simple/index/index.html')
        assert 'a index within the simple directory' in rv.data

    def test_sub_page(self):
        """Test sub page."""
        rv = self.app.get('/simple/subpage/')
        assert 'a simple subpage' in rv.data
        rv = self.app.get('/simple/subpage/index.html')
        assert 'a simple subpage' in rv.data

class CascadeTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.app = chill.app.test_client()
        chill.init_db()

    def test_one_page(self):
        """Test one page."""
        rv = self.app.get('/cascade_test/five/four/three/two/one/')
        assert 'one content page' in rv.data

    def test_empty_page(self):
        """Test empty page."""
        rv = self.app.get('/cascade_test/five/four/three/')
        assert 'cascade test parent page' in rv.data

class YAMLDataCascadeTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.app = chill.app.test_client()
        chill.init_db()

    def test_top_level_yaml(self):
        rv = self.app.get('/')
        assert 'Chill Examples and Tests' in rv.data

    def test_yaml_and_txt_conflict(self):
        rv = self.app.get('/simple/')
        assert 'just a simple page' in rv.data
        assert 'this pagetitle gets replaced by the pagetitle.txt' not in rv.data

    def test_replace_top_yaml(self):
        rv = self.app.get('/simple/')
        assert 'Simple sitetitle' in rv.data

class YAMLDataTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.app = chill.app.test_client()
        chill.init_db()

    def test_menu_yaml(self):
        rv = self.app.get('/')
        assert 'imatitleinamenu' in rv.data

class ResourceFileTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.app = chill.app.test_client()
        chill.init_db()

    def test_if_file_exists(self):
        rv = self.app.get('/_data/test.js')
        assert 'test.js file in data path' in rv.data

    def test_for_file_outside_of_data_path(self):
        " test for file outside of data path "
        rv = self.app.get('/_data/../cantgetthisfile.js')
        assert 'Should NOT be able to retreive this file!' not in rv.data

        rv = self.app.get('/_data/../../cantgetthisfile.js')
        assert 'Should NOT be able to retreive this file!' not in rv.data

    def test_for_file_way_outside_of_data_path(self):
        " test for file way outside of data path "
        rv = self.app.get('/_data/../../../../README.txt')
        assert 404 == rv.status_code

    def test_for_file_outside_of_data_path_but_get_other(self):
        " test for file outside of data path but get other "
        rv = self.app.get('/_data/../../cantgetthisfile.js')
        assert 200 == rv.status_code
        assert 'This file will be returned instead of the one above this directory' in rv.data

class ThemeFileTestCase(unittest.TestCase):
    def setUp(self):
        """Before each test, set up a blank database"""
        self.app = chill.app.test_client()
        chill.init_db()

    def test_if_css_file_exists(self):
        " check if site.css file in default theme css directory exists "
        rv = self.app.get('/_themes/default/css/site.css')
        assert 200 == rv.status_code

    def test_if_mustache_file_exists(self):
        " check if base.mustache file can be accessed"
        rv = self.app.get('/_themes/default/base.mustache')
        assert 200 == rv.status_code


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IndexTestCase))
    suite.addTest(unittest.makeSuite(YAMLDataTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()

