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
        rv = self.app.get('/index')
        assert 'stuff goes here' in rv.data
        rv = self.app.get('/index.html')
        assert 'stuff goes here' in rv.data
        rv = self.app.get('/')
        assert 'stuff goes here' in rv.data

    def test_simple_page(self):
        """Test simple page."""
        rv = self.app.get('/simple')
        assert 'a simple page' in rv.data
        rv = self.app.get('/simple.html')
        assert 'a simple page' in rv.data

    def test_simple_index_page(self):
        """Test simple sub index page."""
        #TODO: should get the index page in simple/index/
        #rv = self.app.get('/simple/')
        #assert 'a index within the simple directory' in rv.data
        rv = self.app.get('/simple/index')
        assert 'a index within the simple directory' in rv.data
        rv = self.app.get('/simple/index.html')
        assert 'a index within the simple directory' in rv.data

    def test_sub_page(self):
        """Test sub page."""
        rv = self.app.get('/simple/subpage')
        assert 'a simple subpage' in rv.data
        rv = self.app.get('/simple/subpage.html')
        assert 'a simple subpage' in rv.data

class CascadeTestCase(unittest.TestCase):

    def setUp(self):
        """Before each test, set up a blank database"""
        self.app = chill.app.test_client()
        chill.init_db()

    def tearDown(self):
        """Get rid of the database again after each test."""
        pass

    def test_one_page(self):
        """Test one page."""
        rv = self.app.get('/cascade_test/five/four/three/two/one')
        assert 'one content page' in rv.data

    def test_empty_page(self):
        """Test empty page."""
        rv = self.app.get('/cascade_test/five/four/three')
        assert 'cascade test parent page' in rv.data

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IndexTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()

