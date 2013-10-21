# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibField Utils

Helper classes and functions to work with BibField
"""

import re

__revision__ = "$Id$"

import os
import datetime

from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer

CFG_BIBFIELD_FUNCTIONS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'bibfield_functions', '*.py'))


class BibFieldException(Exception):
    """
    General exception to use within BibField
    """
    pass


class InvenioBibFieldContinuableError(Exception):
    """BibField continuable error"""
    pass


class InvenioBibFieldError(Exception):
    """BibField fatal error, @see CFG_BIBUPLOAD_BIBFIELD_STOP_ERROR_POLICY"""


class BibFieldDict(object):
    """
    This class implements a I{dict} mostly and uses special key naming for
    accessing as describe in __getitem__

    >>> #Creating a dictionary
    >>> d = BibFieldDict()

    >>> #Filling up the dictionary
    >>> d['foo'] = {'a': 'world', 'b':'hello'}
    >>> d['a'] = [ {'b':1}, {'b':2}, {'b':3} ]
    >>> d['_c'] = random.randint(1,100)
    >>> d['__calculated_functions']['_c'] = "random.randint(1,100)"

    >>> #Accessing data inside the dictionary
    >>> d['a']
    >>> d['a[0]']
    >>> d['a.b']
    >>> d['a[1:]']
    >>> d['_c'] #this value will be calculated on the fly
    """

    def __init__(self):
        self.rec_json = {}
        self.rec_json['__aliases'] = {}
        self.rec_json['__do_not_cache'] = []
        self.is_init_phase = True
        self.rec_json['__calculated_functions'] = {}

    def __getitem__(self, key):
        """
        As in C{dict.__getitem__} but using BibField name convention.

        @param key: String containing the name of the field and subfield.
        For e.g. lest work with:
         {'a': [ {'b':1}, {'b':2}, {'b':3} ], '_c': 42 }
         - 'a' -> All the 'a' field info
           [{'b': 1}, {'b': 2}, {'b': 3}]
         - 'a[0]' -> All the info of the first element inside 'a'
           {'b': 1}
         - 'a[0].b' -> Field 'b' for the first element in 'a'
           1
         - 'a[1:]' -> All the 'a' field info but the first
           [{'b': 2}, {'b': 3}]
         - 'a.b' -> All the 'b' inside 'b'
           [1, 2, 3]
         - '_c- -> will give us the random number that is cached
           42
         - ... any other combination ...
         - ... as deep as the dictionary is ...

        NOTE: accessing one value in a normal way, meaning d['a'], is almost as
              fast as accessing a regular dictionary. But using the special name
              convention is a bit slower than using the regular access.
              d['a[0].b'] -> 10000 loops, best of 3: 18.4 us per loop
              d['a'][0]['b'] -> 1000000 loops, best of 3: 591 ns per loop

        @return: The value of the field, this might be, a dictionary, a list,
        a string, or any combination of the three depending on the value of
        field
        """
        if not self.is_cacheable(key):
            dict_part = self._recalculate_field_value(key)
        else:
            dict_part = self.rec_json

        try:
            if '.' not in key and '[' not in key:
                dict_part = dict_part[key]
            else:
                for group in prepare_field_keys(key):
                    dict_part = self._get_intermediate_value(dict_part, group)
        except KeyError, err:
            return self[key.replace(err.args[0], self.rec_json['__aliases'][err.args[0]].replace('[n]', '[1:]'), 1)]

        return dict_part

    def __setitem__(self, key, value):
        """
        As in C{dict.__setitem__} but using BibField name convention.

        @note: at creation time dict['a[-1]'] = 'something' will mean
        dict['a'].append('something') and if the field already exists and is
        not a list, then this method will create a list with the existing value
        and append the new one,
        dict['a'] = 'first value' -> {'a':'first value'}
        dict['a'] = 'second value' -> {'a':['first value', 'second value']}
        There is one class variable self.is_init_phase for that matter.

        @param key: String containing the name of the field and subfield.
        @param value: The new value
        """
        if self.is_init_phase:
            if '.' not in key and '[' not in key:
                if not key in self.rec_json:
                    self.rec_json[key] = value
                    return
                tmp = self.rec_json[key]
                if tmp is None:
                    self.rec_json[key] = value
                else:
                    if not isinstance(tmp, list):
                        self.rec_json[key] = [tmp]
                    self.rec_json[key].append(value)
            else:
                try:
                    dict_part = eval("self.rec_json%s" % (''.join(prepare_field_keys(key)),))  # kwalitee: disable=eval
                except:
                    build_data_structure(self.rec_json, key)
                    dict_part = eval("self.rec_json%s" % (''.join(prepare_field_keys(key)),))
                if dict_part:
                    exec("self.rec_json%s.append(value)" % (''.join(prepare_field_keys(key, write=True)[:-1]),))
                else:
                    exec("self.rec_json%s = value" % (''.join(prepare_field_keys(key)),))
        else:
            if '.' not in key and '[' not in key:
                self.rec_json[key] = value
            else:
                try:
                    exec("self.rec_json%s = value" % (''.join(prepare_field_keys(key)),))
                except:
                    build_data_structure(self.rec_json, key)
                    exec("self.rec_json%s = value" % (''.join(prepare_field_keys(key)),))

    def __delitem__(self, key):
        """
        As in C{dict.__delitem__}.

        @note: It only works with first keys
        """
        del self.rec_json[key]

    def __contains__(self, key):
        """
        As in C{dict.__contains__} but using BibField name convention.

        @param key: Name of the key
        @return: True if the dictionary contains the special key
        """
        if '.' not in key and '[' not in key:
            return key in self.rec_json
        try:
            self[key]
        except:
            return False
        return True

    def __eq__(self, other):
        """@see C{dict.__eq__}"""
        if not self.keys() == other.keys():
            return False
        try:
            for key in [k for k in self.keys() if not k in self['__do_not_cache']]:
                if not self.get(k) == other.get(k):
                    return False
        except:
            return False
        return True

    def __repr__(self):
        """@see C{dict.__repr__}"""
        return  repr(self.rec_json)

    def __iter__(self):
        """@see C{dict.__iter__}"""
        return iter(self.rec_json)

    def __len__(self):
        """@see C{dict.__len__}"""
        return len(self.rec_json)

    def keys(self):
        """@see C{dict.keys}"""
        return self.rec_json.keys()

    def iteritems(self):
        """@see C{dict.iteritems}"""
        return self.rec_json.iteritems()

    def iterkeys(self):
        """@see C{dict.iterkeys}"""
        return self.rec_json.iterkeys()

    def itervalues(self):
        """@see C{dict.itervalues}"""
        return self.rec_json.itervalues()

    def has_key(self, key):
        """
        As in C{dict.has_key} but using BibField name convention.
        @see __contains__(self, key)
        """
        return self.__contains__(key)

    def get(self, field=None, default=None, reset_cache=False, formatstring=None, formatfunction=None):
        """
        As in C{dict.get} it Retrieves the value of field from the json structure
        but using BibField name convention and also applies some formating if
        present.

        @see __getitem__(self, key)

        @param field: Name of the field/s to retrieve.  If it is None then it
        will return the entire dictionary.
        @param default: in case of error this value will be returned
        @param formatstring: Optional parameter to format the output value.
        This could be a format string, like this example:
        >>> d['foo'] = {'a': 'world', 'b':'hello'}
        >>> get('foo', formatstring="{0[b]} {0[a]}!")
        >>> 'hello world!'
        Note: Use this parameter only if you are running python 2.5 or higher.
        @param formatfunction: Optional parameter to format the output value.
        This parameter must be function and must handle all the possible
        parameter types (str, dict or list)

        @return: The value of the field, this might be, a dictionary, a list,
        a string, or any combination of the three depending on the value of
        field. If any formating parameter is present, then the return value
        will be the formated value.
        """
        if reset_cache:
            self.update_field_cache(field)

        value = self.rec_json
        if field:
            try:
                value = self.__getitem__(field)
            except:
                return default

        if not value:
            return default

        if formatstring:
            value = self._apply_formatstring(value, formatstring)

        if formatfunction:
            value = formatfunction(value)

        return value

    def is_cacheable(self, field):
        """
        Check if a field is inside the __do_not_cache or not

        @return True if it is not in __do_not_cache
        """
        return not get_main_field(field) in self.rec_json['__do_not_cache']


    def update_field_cache(self, field):
        """
        Updates the value of the cache for the given calculated field
        """
        field = get_main_field(field)
        if re.search('^_[a-zA-Z0-9]', field) and not field in self.rec_json['__do_not_cache']:
            self.rec_json[field] = self._recalculate_field_value(field)[field]

    def update_all_fields_cache(self):
        """
        Update the cache of all the calculated fields
        @see: update_field_cache()
        """
        for field in [key for key in self.keys() if re.search('^_[a-zA-Z0-9]', key)]:
            self.update_field_cache(field)

    def _recalculate_field_value(self, field):
        """
        Obtains the new vaule of field using
        """
        field = get_main_field(field)
        return {field: self._try_to_eval(self['__calculated_functions'][field])}

    def _try_to_eval(self, string, bibfield_functions_only=False, **context):
        """
        This method takes care of evaluating the python expression, and, if an
        exception happens, it tries to import the needed module from bibfield_functions
        or from the python path using plugin utils

        @param string: String to evaluate
        @param context: Context needed, in some cases, to evaluate the string

        @return: The value of the expression inside string
        """
        if not string:
            return None

        res = None
        imports = []

        while (True):
            try:
                res = eval(string, globals().update(context), locals())  # kwalitee: disable=eval
            except NameError, err:
                import_name = str(err).split("'")[1]
                if not import_name in imports:
                    if import_name in CFG_BIBFIELD_FUNCTIONS:
                        globals()[import_name] = CFG_BIBFIELD_FUNCTIONS[import_name]
                    elif not bibfield_functions_only:
                        globals()[import_name] = __import__(import_name)
                    imports.append(import_name)
                    continue
                assert False, 'Error not expected when trying to import bibfield function module'
            return res

    def _apply_formatstring(self, value, formatstring):
        """
        Helper function that simply formats the result of get() using a
        format string

        If the value is of type datetime it tries to apply the format using
        strftime(formatstring).

        @see: get(self, field=None, formatstring=None, formatfunction=None)

        @param value: String, dict or list to apply the format string
        @param formatstring: formatstring

        @return: Formated value of "value"
        """
        if not value:
            return ''
        if isinstance(value, datetime.datetime):
            if formatstring == value.strftime(formatstring):
                value = value.isoformat()
            else:
                return value.strftime(formatstring)
        if isinstance(value, list):
            tmp = ''
            for element in value:
                tmp += self._apply_formatstring(element, formatstring)
            return tmp
        elif isinstance(value, dict) or isinstance(value, basestring):
            return formatstring.format(value)
        else:
            assert False, 'String, Dictionay or List expected'

    def _get_intermediate_value(self, dict_part, field):
        """
        Helper function that fetch the value of some field from dict_part

        @see: get(self, field=None, formatstring=None, formatfunction=None)

        @param dict_part: Dictionary or list containing all the information from
        this method will fetch field.
        @param field: Name or index of the field to fetch from dict_part

        @return: The value of the field, this might be, a dictionary, a list,
        a string, or any combination of the three depending on the value of
        field
        """
        if isinstance(dict_part, dict):
            return eval('dict_part%s' % field)  # kwalitee: disable=eval
        elif isinstance(dict_part, list):
            tmp = []
            for element in dict_part:
                tmp.append(self._get_intermediate_value(element, field))
            return tmp
        else:
            assert False, 'Dictionay or List expected get %s' % (type(dict_part),)


class BlobWrapper(object):
    """
    Wrapper class to work easily with the blob and the information related to it
    inside the *Reader
    """
    def __init__(self, blob, **kw):
        self.__info = kw
        self.blob = blob

    def __getattr__(self, name):
        """Trick to access the information inside self.__info using dot syntax"""
        try:
            return self.__info[name]
        except KeyError:
            raise AttributeError("%r object has no attribute %r" % (type(self).__name__, name))


class CoolDict(dict):
    """
    C{dict} but it keeps track of which elements has been consumed/accessed
    and which not
    """

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._consumed = {}
        if self:
            for key, value in dict.iteritems(self):
                self[key] = value

    def __getitem__(self, key):
        """
        As in C{dict} but in this case the key could be a compiled regular expression.

        Also update the consumed list in case the item is not a list or other
        dictionary.

        @return: Like in C{dict.__getitem__} or, if a regular expression is used,
        a list containing all the items inside the dictionary which key matches
        the regular expression ([] if none)
        """
        try:
            keys = filter(key.match, self.keys())
            values = []
            for key in keys:
                value = dict.get(self, key)
                values.append(dict.get(self, key))
                if not isinstance(value, dict) and not isinstance(value, list):
                    self._consumed[key] = True
            return values
        except AttributeError:
            try:
                value = dict.get(self, key)
                if not isinstance(value, dict) and not isinstance(value, list):
                    self._consumed[key] = True
                return value
            except:
                return None

    def __setitem__(self, key, value):
        """
        As in C{dict} but in this case it takes care of updating the consumed
        value for each element inside value depending on its type.
        """
        if isinstance(value, dict):
            dict.__setitem__(self, key, CoolDict(value))
            self._consumed[key] = self[key]._consumed
        elif isinstance(value, list):
            dict.__setitem__(self, key, CoolList(value))
            self._consumed[key] = self[key]._consumed
        else:
            dict.__setitem__(self, key, value)
            self._consumed[key] = False

    def extend(self, key, value):
        """
        If the key is present inside the dictionary it creates a list (it not
        present) and extends it with the new value. Almost as in C{list.extend}
        """
        if key in self:
            current_value = dict.get(self, key)
            if not isinstance(current_value, list):
                current_value = CoolList([current_value])
            current_value.append(value)
            value = current_value

        self[key] = value

    def iteritems(self):
        """ As in C{dict} but it updates the consumed value if needed"""
        for key, value in dict.iteritems(self):
            if not isinstance(value, dict) and not isinstance(value, list):
                self._consumed[key] = True
            yield key, value

        raise StopIteration

    @property
    def consumed(self):
        for key, value in self._consumed.iteritems():
            if not isinstance(value, dict) and not isinstance(value, list):
                if not value:
                    return False
            elif not dict.get(self, key).consumed:
                return False
        return True


class CoolList(list):
    """
    C{list} but it keeps track of which elements has been consumed/accessed and
    which not
    """

    def __init__(self, *args, **kwargs):
        list.__init__(self, *args, **kwargs)
        self._consumed = []
        if self:
            for i, value in enumerate(list.__iter__(self)):
                self._consumed.append(None)
                self[i] = value

    def __getitem__(self, index):
        """As in C{list}, also update the consumed list in case the item is not
        a dictionary or other list.

        @return: Like in C{list.__getitem__}
        """
        value = list.__getitem__(self, index)
        if not isinstance(value, dict) and not isinstance(value, list):
            self._consumed[index] = True
        return value

    def __setitem__(self, index, value):
        """
        As in C{list} but in this case it takes care of updating the consumed
        value for each element inside value depending on its type
        """

        if isinstance(value, dict):
            list.__setitem__(self, index, CoolDict(value))
            self._consumed[index] = self[index]._consumed
        elif isinstance(value, list):
            list.__setitem__(self, index, CoolList(value))
            self._consumed[index] = self[index]._consumed
        else:
            list.__setitem__(self, index, value)
            self._consumed[index] = False

    def __iter__(self, *args, **kwargs):
        """ As in C{dict} but it updates the consumed value if needed"""
        for index, value in enumerate(list.__iter__(self)):
            if not isinstance(value, dict) and not isinstance(value, list):
                self._consumed[index] = True
            yield value

        raise StopIteration

    def append(self, element):
        """@see __setitem__() """
        self += [None]
        self._consumed += [None]
        self[len(self) - 1] = element

    @property
    def consumed(self):
        for index, value in enumerate(self._consumed):
            if not isinstance(value, dict) and not isinstance(value, list):
                if not value:
                    return False
            elif not list.__getitem__(self, index).consumed:
                return False
        return True


def prepare_field_keys(field, write=False):
    """
    Helper function to split the name of the fields and the indexes in a
    proper way to be used by eval function

    @see: bibfield.get()

    @param field: String containing all the names and indexes
    @param write: If the fields are use to write inside the record then the
    granularity is lower for convenience

    @return: List of string that can be evaluated by eval function
    """
    parts = field.split('.')
    keys = []
    for part in parts:
        if '[' in part:
            if write:
                keys.append('["%s"]' % (part[:part.find('[')]))
                keys.append(part[part.find('['):].replace('n', '-1'))
            else:
                keys.append('["%s"]%s' % (part[:part.find('[')], part[part.find('['):].replace('n', '-1')))
        else:
            keys.append('["%s"]' % part)
    return keys


def build_data_structure(record, field):
    """
    Helper functions that builds the record structure

    @param record: Existing data structure
    @param field: New field to add to the structure
    """
    eval_string = ''
    for key in prepare_field_keys(field, write=True):
        if key == '[-1]':
            try:
                eval("record%s.append(None)" % (eval_string,))  # kwalitee: disable=eval
            except AttributeError:
                exec("record%s=[None]" % (eval_string,))
        elif key == '[0]':
            try:
                eval("record%s" % (eval_string + key,))  # kwalitee: disable=eval
                rec_part = eval("record%s" % (eval_string,))  # kwalitee: disable=eval
                if not isinstance(rec_part, list):
                    pass
                rec_part.insert(0, None)
            except TypeError:
                exec("record%s=list([None])" % (eval_string,))
        else:
            try:
                eval("record%s" % (eval_string + key,))  # kwalitee: disable=eval
            except KeyError:
                exec("record%s=None" % (eval_string + key,))
            except TypeError:
                exec("record%s={}" % (eval_string,))
                exec("record%s=None" % (eval_string + key,))
        eval_string += key


def get_main_field(field):
    """
    From a given field it gets the outer field of the tree.

    i.e.: 'a[0].b.c' returns 'a'
    """
    if '.' in field:
        field = field.split('.')[0]
    if '[' in field:
        field = field.split('[')[0]
    return field


def get_producer_rules(field, code):
    """docstring for get_producer_rules"""
    from invenio.bibfield_config import config_rules

    rule = config_rules[field]
    if isinstance(rule, list):
        if len(rule) == 1:
            # case field[n]
            return [(rule[0].replace('[n]', ''), config_rules[rule[0]]['producer'].get(code, {}))]
        else:
            # case field[1], field[n]
            rules = []
            for new_field in rule:
                rules.append((new_field.replace('[n]', '[1:]'), config_rules[new_field]['producer'].get(code, {})))
            return rules
    else:
        return [(field, rule['producer'].get(code, {}))]
