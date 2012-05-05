import unittest
import chill

class Mixin(object):
    def setUp(self):
        """Before each test, set up a blank database"""
        self.app = chill.app.test_client()
        chill.app.build_context_data(chill.app)
        chill.init_db()

    def tearDown(self):
        """Get rid of the database again after each test."""
        pass

class IndexTestCase(Mixin, unittest.TestCase):

    def test_index_page(self):
        """Test index page."""

        # all get the same page
        rv = self.app.get('/index.html', follow_redirects=True)
        assert 'stuff goes here' in rv.data
        rv = self.app.get('/')
        assert 'stuff goes here' in rv.data

    def test_simple_page(self):
        """Test simple page."""
        rv = self.app.get('/simple/')
        assert 'a simple page' in rv.data
        rv = self.app.get('/simple/index.html', follow_redirects=True)
        assert 'a simple page' in rv.data

    def test_simple_index_page(self):
        """Test simple sub index page."""
        rv = self.app.get('/simple/')
        assert 'a index within the simple directory' not in rv.data
        rv = self.app.get('/simple/index/')
        assert 'a index within the simple directory' in rv.data
        rv = self.app.get('/simple/index/index.html', follow_redirects=True)
        assert 'a index within the simple directory' in rv.data

    def test_sub_page(self):
        """Test sub page."""
        rv = self.app.get('/simple/subpage/')
        assert 'a simple subpage' in rv.data
        rv = self.app.get('/simple/subpage/index.html', follow_redirects=True)
        assert 'a simple subpage' in rv.data

class CascadeTestCase(Mixin, unittest.TestCase):

    def test_one_page(self):
        """Test one page."""
        rv = self.app.get('/cascade_test/five/four/three/two/one/')
        assert 'one content page' in rv.data

    def test_empty_page(self):
        """Test empty page."""
        rv = self.app.get('/cascade_test/five/four/three/')
        assert 'cascade test parent page' in rv.data

class YAMLDataCascadeTestCase(Mixin, unittest.TestCase):

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

class YAMLDataTestCase(Mixin, unittest.TestCase):

    def test_menu_yaml(self):
        rv = self.app.get('/')
        assert 'imatitleinamenu' in rv.data

class ResourceFileTestCase(Mixin, unittest.TestCase):

    def test_if_file_exists(self):
        rv = self.app.get('/test.js')
        assert 'test.js file in data path' in rv.data

    def test_for_file_outside_of_data_path(self):
        " test for file outside of data path "
        rv = self.app.get('/../cantgetthisfile.js')
        assert 'Should NOT be able to retreive this file!' not in rv.data

        rv = self.app.get('/../../cantgetthisfile.js')
        assert 'Should NOT be able to retreive this file!' not in rv.data

    def test_for_file_way_outside_of_data_path(self):
        " test for file way outside of data path "
        rv = self.app.get('/../../../../README.txt')
        assert 404 == rv.status_code

    def test_for_file_outside_of_data_path_but_get_other(self):
        " test for file outside of data path but get other "
        rv = self.app.get('/../../cantgetthisfile.js', follow_redirects=True)
        assert 200 == rv.status_code
        assert 'This file will be returned instead of the one above this directory' in rv.data

    def test_for_humans(self):
        " humans? "
        rv = self.app.get('/humans.txt', follow_redirects=True)
        assert 200 == rv.status_code

    def test_for_page_fragment(self):
        " page fragments viewable "
        rv = self.app.get('/content.html', follow_redirects=True)
        assert 200 == rv.status_code
        rv = self.app.get('/_data.yaml', follow_redirects=True)
        assert 200 == rv.status_code

    def test_no_dot_files(self):
        " no dot files accessible "
        rv = self.app.get('/.nope.txt', follow_redirects=True)
        assert 404 == rv.status_code
        rv = self.app.get('/simple/.nope.html', follow_redirects=True)
        assert 404 == rv.status_code

    def test_no_dot_directories(self):
        " no dot directories accessible "
        rv = self.app.get('/.imadot/nope.txt', follow_redirects=True)
        assert 404 == rv.status_code
        rv = self.app.get('/simple/.imadot/nope.html', follow_redirects=True)
        assert 404 == rv.status_code

class ThemeFileTestCase(Mixin, unittest.TestCase):

    def test_if_css_file_exists(self):
        " check if site.css file in default theme css directory exists "
        rv = self.app.get('/_themes/default/css/site.css')
        assert 200 == rv.status_code

    def test_if_mustache_file_exists(self):
        " check if base.mustache file can be accessed"
        rv = self.app.get('/_themes/default/base.mustache')
        assert 200 == rv.status_code

class MustacheDataTestCase(Mixin, unittest.TestCase):

    def test_mustache_wrap(self):
        " content.html and content.mustache no conflict "
        rv = self.app.get('/simple/mustache/')
        assert "Some content that should be inside the content.mustache template." in rv.data
        assert "mustache file with same name as a page fragment" in rv.data


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IndexTestCase))
    suite.addTest(unittest.makeSuite(YAMLDataTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()

