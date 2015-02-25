# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

import datetime
import six
from dateutil import parser as dateparser
from pyparsing import Keyword, Literal, SkipTo
from werkzeug.utils import import_string

from invenio.base.globals import cfg
from invenio.base.utils import try_to_eval

from invenio.modules.jsonalchemy.parser import FieldParser, \
    DecoratorAfterEvalBaseExtensionParser
from invenio.modules.jsonalchemy.registry import functions


class MemoizeParser(DecoratorAfterEvalBaseExtensionParser):

    """
    Handle the ``@memoze`` decorator.

    .. code-block:: ini

        number_of_comments:
            calculated:
                @memoize(300)
                get_number_of_comments(self['recid'])

    This decorator works only with calculated fields and it has three different
    ways of doing it:

    1. No decorator is specified, the value of the field will be calculated
       every time that somebody asks for it and its value will not be stored
       in the DB. This way is useful to create fields that return objects
       that can't be stored in the DB in a JSON friendly manner or a field
       that changes a lot its value and the calculated function is really
       light.

    2. The decorator is used without any time, ``@memoize()``. This means
       that the value of the field is calculated when the record is created,
       it is stored in the DB and it is the job of the client that modifies
       the data, which is used to calculated the field, to update the field
       value in the DB.
       This way should be used for fields that are typically updated just by
       a few clients, like ``bibupload``, ``bibrank``, etc.

    3. A lifetime is set with the decorator ``@memoize(300)``. In this case
       the field value is only calculated when somebody asks for it and its
       value is stored in a general cache (``invenio.ext.cache``) using the
       timeout from the decorator.
       This form of the memoize decorator should be used with a field that
       changes a lot its value and the function to calculate it is not
       light.
       Keep in mind that the value that someone might get could be
       outdated. To avoid this situation the client that modifies the data
       where the value is calculated from could also invalidate the cache or
       modify the cached value.
       One good example of the use of it is the field ``number_of_comments``

    The cache engine used by this decorator could be set using
    ``CFG_JSONALCHEMY_CACHE`` in your instance configuration, by default
    ``invenio.ext.cache:cache`` will use.
    ``CFG_JSONALCHEMY_CACHE`` must be and importable string pointing to the
    cache object.
    """

    __parsername__ = 'memoize'

    DEFAULT_TIMEOUT = -1
    """Default timeout, -1 means the cache will not be invalidated unless is
    explicitly requested"""

    __cache = None

    def __new__(cls):
        if cls.__cache is None:
            cls.__cache = import_string(cfg.get('CFG_JSONALCHEMY_CACHE',
                                                'invenio.ext.cache:cache'))
        return cls

    @classmethod
    def parse_element(cls, indent_stack):
        """Set ``memoize`` attribute to the rule."""
        return (Keyword("@memoize").suppress() +
                Literal('(').suppress() +
                SkipTo(')') +
                Literal(')').suppress()
                ).setResultsName("memoize")

    @classmethod
    def create_element(cls, rule, field_def, content, namespace):
        """Try to evaluate the memoize value to int.

        If it fails it sets the default value from ``DEFAULT_TIMEOUT``.
        """
        try:
            return int(content[0])
        except (TypeError, IndexError, ValueError):
            return cls.DEFAULT_TIMEOUT

    @classmethod
    def add_info_to_field(cls, json_id, info, args):
        """Set the time out for the field"""
        if info['type'] == 'calculated' and args is None:
            return 0
        return args

    @classmethod
    def evaluate(cls, json, field_name, action, args):
        """Evaluate the parser.

        When getting a json field compare the timestamp and the lifetime of it
        and, if it the lifetime is over calculate its value again.

        If the value of the field has changed since the last time it gets
        updated in the DB.
        """
        if cls.__cache is None:
            cls.__cache = import_string(cfg.get('CFG_JSONALCHEMY_CACHE',
                                                'invenio.ext.cache:cache'))

        @cls.__cache.memoize(timeout=args)
        def memoize(_id, field_name):
            func = reduce(lambda obj, key: obj[key],
                          json.meta_metadata[field_name]['function'],
                          FieldParser.field_definitions(
                              json.additional_info.namespace))
            return try_to_eval(func, functions(json.additional_info.namespace),
                               self=json)

        if args == cls.DEFAULT_TIMEOUT:
            return
        if action == 'get':
            if args == 0:  # No cached version is stored, retrieve it
                func = reduce(lambda obj, key: obj[key],
                              json.meta_metadata[field_name]['function'],
                              FieldParser.field_definitions(
                                  json.additional_info.namespace))
                json._dict_bson[field_name] = try_to_eval(
                    func,
                    functions(json.additional_info.namespace),
                    self=json)
            else:
                json._dict_bson[field_name] = memoize(json.get('_id'),
                                                      field_name)
        elif action == 'set':
            if args >= 0:  # Don't store anything
                json._dict_bson[field_name] = None

parser = MemoizeParser
