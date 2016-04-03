import unittest

from chill.api import (
        _short_circuit
        )


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

class ShortCircuit(ApiTestCase):

    def test_short_circuit_skip(self):
        a = 'Johnny'
        b = _short_circuit(a)
        assert a == b

        a = ['Johnny', 'Johnny Five']
        b = _short_circuit(a)
        assert a == b

        a = {'id':5}
        b = _short_circuit(a)
        assert a == b

        a = {'id':5,'name':'Johnny'}
        b = _short_circuit(a)
        assert a == b

        a = [{'id':5},{'id':4}]
        b = _short_circuit(a)
        assert a == b

    def test_short_circuit_list(self):
        a = ['Johnny']
        b = _short_circuit(a)
        assert b == 'Johnny'

        a = [['Johnny']]
        b = _short_circuit(a)
        assert b == 'Johnny'

        a = [[{'id':5},{'id':4}]]
        b = _short_circuit(a)
        assert b == [{'id':5},{'id':4}]

    def test_short_circuit_dict(self):
        a = [{'id':5,'name':'Johnny Five'}]
        b = _short_circuit(a)
        assert b == {'id':5,'name':'Johnny Five'}

        a = [{'id':5},{'name':'Johnny Five'}]
        b = _short_circuit(a)
        assert b == {'id':5,'name':'Johnny Five'}

        a = [{'id':5, 'status':'unknown'},{'name':'Johnny Five'}]
        b = _short_circuit(a)
        assert a == b

        a = [{'id':5,'name':'Johnny Five'}, {'id':4,'name':'unknown'}]
        b = _short_circuit(a)
        assert a == b

        a = {'name':'Number Five', 'manufacturer':'NOVA Laboratories'}
        b = _short_circuit(a)
        assert a == b


if __name__ == '__main__':
    unittest.main()

