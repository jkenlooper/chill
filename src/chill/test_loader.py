import unittest
import tempfile
import os

from chill.app import multiple_directory_files_loader

class LoadSelectSql(unittest.TestCase):
    def setUp(self):
        self.dir_a = tempfile.mkdtemp()
        self.dir_b = tempfile.mkdtemp()

    def tearDown(self):
        for tmp_dir in (self.dir_a, self.dir_b):
            for root, dirs, files in os.walk( tmp_dir, topdown=False ):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(tmp_dir)


    def write_dict_to_files(self, d, dirname):
        for (k, v) in list(d.items()):
            # mkdir that are in the path (if any)
            dirs = k.split('/')[:-1]
            if len(dirs) > 0:
                try:
                    os.makedirs( os.path.join( dirname, os.path.dirname(k) ) )
                except OSError:
                    pass
                    #print 'exists ' + os.path.join( dirname, os.path.dirname(k) )
            with open( os.path.join(dirname, k), 'w') as f:
                f.write( v )

    def test_one_dir_with_one_file(self):
        self.write_dict_to_files({
            'abc': 'a value',
            }, self.dir_a)

        a = multiple_directory_files_loader(self.dir_a)
        assert a.get('abc') == 'a value'

    def test_two_dir_with_one_file(self):
        self.write_dict_to_files({
            'abc': 'a value',
            }, self.dir_a)
        self.write_dict_to_files({
            'abc': 'b value',
            }, self.dir_b)

        a = multiple_directory_files_loader(self.dir_a, self.dir_b)
        assert a.get('abc') == 'b value'

    def test_two_dir_with_more_files(self):
        self.write_dict_to_files({
            'abc': 'a value',
            'a': '1',
            }, self.dir_a)
        self.write_dict_to_files({
            'abc': 'b value',
            'b': '2',
            }, self.dir_b)

        a = multiple_directory_files_loader(self.dir_a, self.dir_b)
        assert a.get('abc') == 'b value'
        assert a.get('a') == '1'
        assert a.get('b') == '2'

    def test_two_dir_with_subfiles(self):
        self.write_dict_to_files({
            'abc/dog': 'a value',
            'a/b/c/dog': '1',
            'a/blue': '1',
            'cat': '1',
            }, self.dir_a)
        self.write_dict_to_files({
            'abc/dog': 'b value',
            'cat': '2',
            'a/b/c/dog': '2',
            'a/dog': '2',
            'a/b/cat': '2',
            }, self.dir_b)

        a = multiple_directory_files_loader(self.dir_a, self.dir_b)
        assert a.get('abc/dog') == 'b value'
        assert a.get('a') == None
        assert a.get('cat') == '2'
        assert a.get('a/b/c/dog') == '2'
        assert a.get('a/b') == None
        assert a.get('a/b/cat') == '2'

if __name__ == '__main__':
    unittest.main()
