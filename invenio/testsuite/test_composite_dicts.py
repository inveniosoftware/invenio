# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Unit tests for add_orcid."""

from nose_parameterized import parameterized, param
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableComposite
from sqlalchemy.orm import composite
from unittest import TestCase


from invenio.testsuite import make_test_suite, run_test_suite
from invenio.ext.sqlalchemy.utils import get_model_type


Base = declarative_base()
Base = get_model_type(Base)  # Patch with our methods


class MyComposite(MutableComposite):
    """Example usage of MutableComposite for testing purposes."""

    def __init__(self, mycomposite_one, mycomposite_two, mycomposite_thr):
        self.val_one = mycomposite_one
        self.val_two = mycomposite_two
        self.val_thr = mycomposite_thr

    def __setattr__(self, key, value):
        """Intercept set events."""
        object.__setattr__(self, key, value)
        self.changed()

    def __composite_values__(self):
        """Return ordered values of the composite."""
        return (self.val_one, self.val_two, self.val_thr)

    def __composite_keys__(self):
        """Return ordered keys of the composite."""
        return ('one', 'two', 'thr')

    def __composite_items__(self):
        """Return keys and values in the composite."""
        return (('one', self.val_one),
                ('two', self.val_two),
                ('thr', self.val_thr))

    def __composite_orig_keys__(self):
        """Return ordered keys as present in the model."""
        return ('mycomposite_one', 'mycomposite_two', 'mycomposite_thr')


class TestModel(Base):
    """Sample test model with composite."""

    __tablename__ = 'test_model'

    simple = Column(String(50), primary_key=True)
    mycomposite_one = Column(String(255), nullable=True)
    mycomposite_two = Column(String(255), nullable=True)
    mycomposite_thr = Column(Integer, nullable=True)
    mycomposite = composite(MyComposite,
                            mycomposite_one,
                            mycomposite_two,
                            mycomposite_thr)


cases = {
    'simple':
    {
        'todict_args': {'composites': False,
                        'without_none': False,
                        'composite_drop_consumed': False},
        'expected_dict': {'simple': u'abc',
                          'mycomposite_one': u'1',
                          'mycomposite_thr': 3,
                          'mycomposite_two': None},
    },

    'simple_with_none':
    {
        'todict_args': {'composites': False,
                        'without_none': True,
                        'composite_drop_consumed': False},
        'expected_dict': {'simple': u'abc',
                          'mycomposite_one': u'1',
                          'mycomposite_thr': 3},
    },

    'composite':
    {
        'todict_args': {'composites': True,
                        'without_none': False,
                        'composite_drop_consumed': False},
        'expected_dict': {'simple': u'abc',
                          'mycomposite_one': u'1',
                          'mycomposite_thr': 3,
                          'mycomposite': {'thr': 3,
                                          'two': None,
                                          'one': u'1'},
                          'mycomposite_two': None},
    },

    'composite_and_consume':
    {
        'todict_args': {'composites': True,
                        'without_none': False,
                        'composite_drop_consumed': True},
        'expected_dict': {'mycomposite': {'one': u'1',
                                          'thr': 3,
                                          'two': None},
                          'simple': 'abc'},
    },

    'composite_without_none':
    {
        'todict_args': {'composites': True,
                        'without_none': True,
                        'composite_drop_consumed': False},
        'expected_dict': {'simple': u'abc',
                          'mycomposite_one': u'1',
                          'mycomposite_thr': 3,
                          'mycomposite': {'thr': 3, 'one': u'1'}},
    },
}


def case_builder(name, extra_args=None):
    """Wrap case name and given arguments into a `param` for `parameterized`."""
    if not extra_args:
        extra_args = {}
    return param(name, **dict(cases[name].items() + extra_args.items()))


class TestChanges(TestCase):
    """Test if desired changes occured."""

    def setUp(self):
        self.row = TestModel(simple='abc', mycomposite_one='1',
                             mycomposite_two=None, mycomposite_thr=3)

    def test_returned_value_is_iterator(self):
        resulting_dict = self.row.todict()
        next(resulting_dict)

    def test_returned_value_can_be_converted_to_dict(self):
        resulting_dict = self.row.todict()
        dict(resulting_dict)

    @parameterized.expand((
        case_builder('simple',                 {'condition': lambda res, exp: res == exp}),
        case_builder('simple_with_none',       {'condition': lambda res, exp: "mycomposite_two" not in res}),
        case_builder('composite',              {'condition': lambda res, exp: exp["mycomposite"] == res["mycomposite"]}),
        case_builder('composite_and_consume',  {'condition': lambda res, exp: not {"mycomposite_one", "mycomposite_two", "mycomposite_thr"} & set(res)}),
        case_builder('composite_without_none', {'condition': lambda res, exp: "mycomposite_two" not in res and "two" not in res["mycomposite"]}),
    ))
    def test_todict(self, _, todict_args, expected_dict, condition,
                    expected_exception=None):
        resulting_dict = dict(self.row.todict(**todict_args))
        self.assertTrue(condition(resulting_dict, expected_dict))

    @parameterized.expand((
        case_builder('simple'                ),
        case_builder('simple_with_none'      ),
        case_builder('composite'             ),
        case_builder('composite_and_consume' ),
        case_builder('composite_without_none'),
    ))
    def test_fromdict(self, _, todict_args, expected_dict,
                      expected_exception=None):
        # `todict_args` is not used here because we already know the result from
        # `expected_dict`
        row_from_todict = TestModel()
        row_from_todict.fromdict(expected_dict)
        dict_of_fromdict = dict(row_from_todict.todict(composites=False,
                                                       without_none=False))

        resulting_dict = dict(self.row.todict(composites=False,
                                              without_none=False))

        self.assertEquals(dict_of_fromdict, resulting_dict)

    @parameterized.expand((
        case_builder('composite'             ),
        case_builder('composite_and_consume' ),
        case_builder('composite_without_none'),
    ))
    def test_assignment_to_composite_is_picked_up(self, _, todict_args,
                                                  expected_dict,
                                                  expected_exception=None):
        changes = {'mycomposite': {'one': 'hello'}}

        row_from_todict = TestModel()
        import copy
        expected_dict = copy.deepcopy(expected_dict)
        expected_dict.update(changes.items())
        row_from_todict.fromdict(expected_dict)
        dict_of_todict = dict(row_from_todict.todict(composites=False,
                                                     without_none=False))

        self.assertEquals(dict_of_todict['mycomposite_one'], 'hello')


TEST_SUITE = make_test_suite(TestChanges)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE)
