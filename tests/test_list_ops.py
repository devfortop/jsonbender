from operator import add
import unittest

from jsonbender import Context, K, S, bend
from jsonbender.list_ops import Forall, FlatForall, Filter, ListOp, Reduce
from jsonbender.test import BenderTestMixin


class ListOpTestCase(unittest.TestCase, BenderTestMixin):
    cls = ListOp

    def assert_list_op(self, the_list, func, expected_value):
        self.assert_bender(self.cls(func), the_list, expected_value)


class TestForall(ListOpTestCase):
    cls = Forall

    def test_empty_list(self):
        self.assert_list_op([], lambda i: i*2, [])

    def test_none_list(self):
        self.assert_list_op(None, lambda i: i*2, None)

    def test_nonempty_list(self):
        self.assert_list_op(range(1, 5), lambda i: i*2, [2, 4, 6, 8])

    def test_compatibility(self):
        # TODO: remove this when compatibility is broken
        bender = self.cls(K([1]), lambda i: i)
        self.assert_bender(bender, {}, [1])

    def test_bend(self):
        self.assert_bender(self.cls.bend({'b': S('a')}),
                           [{'a': 23}, {'a': 27}],
                           [{'b': 23}, {'b': 27}])

    def test_bend_none(self):
        self.assert_bender(self.cls.bend({'b': S('a')}),
                           None,
                           None)

    def test_bend_with_context(self):
        mapping = {'b': Context() >> S('c')}
        context = {'c': 42}
        self.assert_bender(self.cls.bend(mapping, context),
                           [{}, {}],
                           [{'b': 42}, {'b': 42}])

    def test_bend_inherits_outer_context_by_default(self):
        inner_mapping = {'val': Context()}
        outer_mapping = {'a': S('items') >> Forall.bend(inner_mapping)}
        source = {'items': range(3)}
        got = bend(outer_mapping, source, context=27)
        expected = {'a': [{'val': 27}, {'val': 27}, {'val': 27}]}
        self.assertEqual(got, expected)


class TestReduce(ListOpTestCase):
    cls = Reduce

    def test_empty_list(self):
        bender = Reduce(add)
        self.assertRaises(ValueError, bender, [])

    def test_nonempty_list(self):
        self.assert_list_op(range(1, 5), add, 10)

    def test_compatibility(self):
        # TODO: remove this when compatibility is broken
        bender = self.cls(K([1, 2]), add)
        self.assert_bender(bender, {}, 3)


class TestFilter(ListOpTestCase):
    cls = Filter

    def test_empty_list(self):
        self.assert_list_op([], lambda d: not d['ignore'], [])

    def test_nonempty_list(self):
        the_list = [{'id': 1, 'ignore': True},
                    {'id': 2, 'ignore': False},
                    {'id': 3, 'ignore': False},
                    {'id': 4, 'ignore': True}]

        expected = [{'id': 2, 'ignore': False}, {'id': 3, 'ignore': False}]
        self.assert_list_op(the_list, lambda d: not d['ignore'], expected)

    def test_compatibility(self):
        # TODO: remove this on next release
        bender = self.cls(K([1]), lambda i: True)
        self.assert_bender(bender, {}, [1])


class TestFlatForall(ListOpTestCase):
    cls = FlatForall

    def test_empty_list(self):
        self.assert_list_op([], lambda d: d['b'], [])

    def test_nonempty_list(self):
        self.assert_list_op([{'b': [1, 2]}, {'b': [-2, -1]}],
                            lambda d: d['b'],
                            [1, 2, -2, -1])

    def test_compatibility(self):
        # TODO: remove this on next release
        bender = self.cls(K([1]), lambda i: [i])
        self.assert_bender(bender, {}, [1])


if __name__ == '__main__':
    unittest.main()

