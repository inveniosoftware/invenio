# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Test unit for the miscutil/datastructures module.
"""

from operator import delitem, setitem
from werkzeug.datastructures import MultiDict

from invenio.utils.datastructures import LazyDict, LaziestDict, SmartDict, DotableDict, flatten_multidict
from invenio.testsuite import make_test_suite, run_test_suite, InvenioTestCase


class CallCounter(object):

    """Counts number of calls."""

    def __init__(self, populate):
        self.counter = 0
        self.populate = populate

    def __call__(self, *args, **kwargs):
        self.counter = self.counter + 1
        return self.populate(*args, **kwargs)


class TestLazyDictionaries(InvenioTestCase):

    """
    Lazy dictionaries TestSuite.
    """

    def test___setitem(self):
        lazy_dict = LazyDict()

        lazy_dict.__setitem__('foo', 'bar')
        lazy_dict.__setitem__('foo2', 'bar2')
        lazy_dict.__setitem__('foo3', 'bar3')

        self.assertEqual(lazy_dict['foo'], 'bar')
        self.assertEqual(lazy_dict['foo3'], 'bar3')
        self.assertEqual(lazy_dict['foo2'], 'bar2')

    def testa___delitem(self):
        populate = CallCounter(lambda: {'foo': 'bar', 1: 11, 'empty': None})

        lazy_dict = LazyDict(populate)
        self.assertEqual(lazy_dict['foo'], 'bar')

        del lazy_dict['foo']
        self.assertRaises(KeyError, lambda: lazy_dict['foo'])

    def test___delitem_on_empty_dict(self):
        lazy_dict = LazyDict()

        self.assertRaises(KeyError, delitem, lazy_dict, "foo")

    def test___getattr_on_empty_dict(self):
        lazy_dict = LazyDict()

        self.assertRaises(AttributeError, lambda: lazy_dict.fooattr)

    def test___iter(self):
        populate = CallCounter(lambda: {'foo': 'bar', 1: 11, 'empty': None})
        lazy_dict = LazyDict(populate)

        iterator = iter(lazy_dict)

        self.assertEqual(iterator.next(), 1)
        self.assertEqual(iterator.next(), 'foo')
        self.assertEqual(iterator.next(), 'empty')

        self.assertRaises(StopIteration, iterator.next)

    def test_iteritems(self):
        populate = CallCounter(lambda: {'foo': 'bar', 1: 11, 'empty': None})
        lazy_dict = LazyDict(populate)

        iterator = lazy_dict.iteritems()

        k, v = iterator.next()
        self.assertEqual(k, 1)
        self.assertEqual(v, 11)

        k, v = iterator.next()
        self.assertEqual(k, 'foo')
        self.assertEqual(v, 'bar')

        k, v = iterator.next()
        self.assertEqual(k, 'empty')
        self.assertEqual(v, None)

        self.assertRaises(StopIteration, iterator.next)

    def test_iterkeys(self):
        populate = CallCounter(lambda: {'foo': 'bar', 1: 11, 'empty': None})
        lazy_dict = LazyDict(populate)

        iterator = lazy_dict.iterkeys()

        self.assertEqual(iterator.next(), 1)
        self.assertEqual(iterator.next(), 'foo')
        self.assertEqual(iterator.next(), 'empty')

        self.assertRaises(StopIteration, iterator.next)

    def test_itervalues(self):
        populate = CallCounter(lambda: {'foo': 'bar', 1: 11, 'empty': None})
        lazy_dict = LazyDict(populate)

        iterator = lazy_dict.itervalues()

        self.assertEqual(iterator.next(), 11)
        self.assertEqual(iterator.next(), 'bar')
        self.assertEqual(iterator.next(), None)

        self.assertRaises(StopIteration, iterator.next)

    def test_lazy_dictionary(self):
        """Checks content of lazy dictionary and number of evaluations."""
        populate = CallCounter(lambda: {'foo': 'bar', 1: 11, 'empty': None})

        lazy_dict = LazyDict(populate)
        self.assertEqual(populate.counter, 0)

        self.assertEqual(lazy_dict['foo'], 'bar')
        self.assertEqual(populate.counter, 1)

        self.assertEqual(lazy_dict[1], 11)
        self.assertEqual(populate.counter, 1)

        self.assertEqual(lazy_dict['empty'], None)
        self.assertEqual(populate.counter, 1)

        # clear the cache
        lazy_dict.expunge()
        self.assertEqual(lazy_dict['foo'], 'bar')
        self.assertEqual(populate.counter, 2)

        del lazy_dict['foo']
        self.assertEqual(populate.counter, 2)
        assert 'foo' not in lazy_dict

    def test_laziest_dictionary(self):
        populate = CallCounter(
            lambda k: {'foo': 'bar', 1: 11, 'empty': None}[k]
        )

        laziest_dict = LaziestDict(populate)
        self.assertEqual(populate.counter, 0)

        self.assertEqual(laziest_dict['foo'], 'bar')
        self.assertEqual(laziest_dict.keys(), ['foo'])
        self.assertEqual(populate.counter, 1)

        self.assertEqual(laziest_dict[1], 11)
        self.assertEqual(laziest_dict.keys(), [1, 'foo'])
        self.assertEqual(populate.counter, 2)

        self.assertEqual(laziest_dict['empty'], None)
        self.assertEqual(laziest_dict.keys(), [1, 'foo', 'empty'])
        self.assertEqual(populate.counter, 3)

        # cached result will not cause new call
        self.assertEqual(laziest_dict['foo'], 'bar')
        self.assertEqual(populate.counter, 3)

        # not existing key cause new call (even multiple times)
        self.assertEqual(laziest_dict.get('does not exists', -1), -1)
        self.assertEqual(populate.counter, 4)
        self.assertEqual(laziest_dict.get('does not exists'), None)
        self.assertEqual(populate.counter, 5)

    def test_laziest__contains(self):
        populate = CallCounter(
            lambda k: {'foo': 'bar', 1: 11, 'empty': None}[k]
        )

        laziest_dict = LaziestDict(populate)
        self.assertTrue('foo' in laziest_dict)
        self.assertFalse('foo2' in laziest_dict)

        laziest_dict2 = LaziestDict()
        self.assertFalse('foo2' in laziest_dict2)


class TestSmartDict(InvenioTestCase):

    """
    Smart Dictionary TestSuite
    """

    def test_smart_dict(self):
        d = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]
        self.assertEqual(d.keys(), ['a', 'foo'])
        self.assertTrue('foo.a' in d)
        del d['foo']
        self.assertEqual(d.keys(), ['a'])
        self.assertEqual(d['a'], [{'b': 1}, {'b': 2}, {'b': 3}])
        self.assertEqual(d['a[0]'], {'b': 1})
        self.assertEqual(d['a.b'], [1, 2, 3])
        self.assertEqual(d['a[1:]'], [{'b': 2}, {'b': 3}])

        d.set('a', {'b': 4}, extend=True)
        self.assertEqual(d['a'], [{'b': 1}, {'b': 2}, {'b': 3}, {'b': 4}])
        d.set('a', [{'b': 1}, {'b': 2}, {'b': 3}], extend=False)
        self.assertEqual(d['a'], [{'b': 1}, {'b': 2}, {'b': 3}])

        self.assertEqual(d.get('does not exists'), None)

        d = SmartDict()
        d.set('a.b.c[n]', 'foo', True)
        self.assertEqual(d['a.b.c'], ['foo'])
        d.set('a.b.c[n]', 'bar', True)
        self.assertEqual(d['a.b.c'], ['foo', 'bar'])
        d.set('a.b.c', ['foo'], False)
        self.assertEqual(d['a.b.c'], ['foo'])

    def test_smart__contains(self):
        d = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]

        self.assertFalse('.' in d)
        self.assertFalse('[' in d)

    def test_smart_insert_special_chars(self):
        d = SmartDict({'a': 'world', 'b': 'hello'})

        self.assertRaises(KeyError, setitem, d, ".", "dot")
        self.assertRaises(KeyError, setitem, d, "[", "open bracket")
        self.assertRaises(KeyError, setitem, d, "]", "close bracket")

    def test_smart_iter(self):
        d = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]

        iterator = iter(d)

        self.assertEqual(iterator.next(), 'a')
        self.assertEqual(iterator.next(), 'foo')

        self.assertRaises(StopIteration, iterator.next)

    def test_smart_items(self):
        d = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]
        d['c.d'] = [{'e': 4}, {'f': 5}]

        self.assertTrue(d.items(), [('a', [{'b': 1}, {'b': 2}, {'b': 3}]),
                                    ('c', {'d': [{'e': 4}, {'f': 5}]}),
                                    ('foo', {'a': 'world', 'b': 'hello'})])

    def test_smart_iteritems(self):
        d = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['c.d'] = [{'e': 4}, {'f': 5}]
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]

        iterator = d.iteritems()

        k, v = iterator.next()
        self.assertEqual(k, 'a')
        self.assertEqual(v, [{'b': 1}, {'b': 2}, {'b': 3}])

        k, v = iterator.next()
        self.assertEqual(k, 'c')
        self.assertEqual(v, {'d': [{'e': 4}, {'f': 5}]})

        k, v = iterator.next()
        self.assertEqual(k, 'foo')
        self.assertEqual(v, {'a': 'world', 'b': 'hello'})

        self.assertRaises(StopIteration, iterator.next)

    def test_smart_iterkeys(self):
        d = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['c.d'] = [{'e': 4}, {'f': 5}]
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]

        iterator = d.iterkeys()

        self.assertEqual(iterator.next(), 'a')
        self.assertEqual(iterator.next(), 'c')
        self.assertEqual(iterator.next(), 'foo')

        self.assertRaises(StopIteration, iterator.next)

    def test_smart_itervalues(self):
        d = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['c.d'] = [{'e': 4}, {'f': 5}]
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]

        iterator = d.itervalues()

        self.assertEqual(iterator.next(), [{'b': 1}, {'b': 2}, {'b': 3}])
        self.assertEqual(iterator.next(), {'d': [{'e': 4}, {'f': 5}]})
        self.assertEqual(iterator.next(), {'a': 'world', 'b': 'hello'})

        self.assertRaises(StopIteration, iterator.next)

    def test_smart_has_key(self):
        d = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['c.d'] = [{'e': 4}, {'f': 5}]
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]

        self.assertTrue('c' in d)
        self.assertFalse('v' in d)
        self.assertTrue('c.d' in d)
        self.assertTrue('foo.b' in d)

    def test_smart_repr(self):
        d = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['c.d'] = [{'e': 4}, {'f': 5}]
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]

        self.assertEqual(repr(d), "{'a': [{'b': 1}, {'b': 2}, {'b': 3}], " +
                                  "'c': {'d': [{'e': 4}, {'f': 5}]}, " +
                                  "'foo': {'a': 'world', 'b': 'hello'}}")

        del d['c']
        self.assertEqual(repr(d), "{'a': [{'b': 1}, {'b': 2}, {'b': 3}], " +
                                  "'foo': {'a': 'world', 'b': 'hello'}}")

    def test_smart_update(self):
        d = SmartDict()
        d2 = SmartDict()

        d['foo'] = {'a': 'world', 'b': 'hello'}
        d['c.d'] = [{'e': 4}, {'f': 5}]
        d['a'] = [{'b': 1}, {'b': 2}, {'b': 3}]

        d2['qwerty'] = {'t': 'u', 'i': 'o'}
        d2['qwe.rty'] = [{'n': 34}, {'x': 3}]

        d.update(d2)

        d3 = SmartDict({'a': [{'b': 1}, {'b': 2}, {'b': 3}],
                        'c': {'d': [{'e': 4}, {'f': 5}]},
                        'foo': {'a': 'world', 'b': 'hello'},
                        'qwe': {'rty': [{'n': 34}, {'x': 3}]},
                        'qwerty': {'i': 'o', 't': 'u'}})

        self.assertTrue(d == d3)


class TestDotableDict(InvenioTestCase):

    def test_get_attr(self):
        dotable = DotableDict({'a': [{'b': 3, 'c': 5}]})
        self.assertEqual(dotable.a, [{'b': 3, 'c': 5}])

    def test_set_attr(self):
        dotable = DotableDict({'a': [{'b': 3, 'c': 5}]})
        dotable.d = 42
        self.assertEqual(dotable.d, 42)


class TestFlattenMultict(InvenioTestCase):

    def test_flatten_multidict(self):
        d = MultiDict({'a': 3, 'b': {'c': 5}})
        d2 = flatten_multidict(d)

        self.assertEqual(d2, {'a': 3, 'b': {'c': 5}})

TEST_SUITE = make_test_suite(TestLazyDictionaries, TestSmartDict,
                             TestDotableDict)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
