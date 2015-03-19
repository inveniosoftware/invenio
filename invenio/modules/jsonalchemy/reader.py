# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Default JSONAlchemy reader.

It provides the common functionality to use by the readers.
Typically this class should be used as a factory to create the concrete
reader depending of the master format of the input.

    >>> from invenio.modules.jsonalchemy.reader import Reader
    >>> from invenio.modules.readers.api import Record
    >>> record = Reader.translate(blob, 'marc', Record, model=['picture'])
"""
import itertools
import datetime
import six

from invenio.base.utils import try_to_eval

from .errors import ReaderException
from .parser import FieldParser, ModelParser
from .registry import functions, readers


def split_blob(blob, master_format, slice_size=0, **kwargs):
    """TODO: Docstring for split_blob.

    :params blob: todo
    :params master_format: todo
    :params slice_size: todo
    :params kwargs: todo
    :returns: todo

    """
    def grouper(n, iterable):
        iter_ = iter(iterable)
        while True:
            chunk = tuple(itertools.islice(iter_, n))
            if not chunk:
                return
            yield chunk
    if slice_size == 0:
        return readers[master_format].split_blob(blob, **kwargs)
    else:
        return grouper(slice_size,
                       readers[master_format].split_blob(blob, **kwargs))


class Reader(object):  # pylint: disable=R0921

    """Base reader."""

    def __new__(cls, json, blob=None, **kwargs):  # pylint: disable=W0613
        """Implement object's instantiation."""
        try:
            master_format = json.additional_info.master_format
            return super(Reader, cls).__new__(readers[master_format])
        except KeyError as e:
            raise KeyError("Not reader found for '%s'" % (e.message, ))

    def __init__(self, json, blob=None, **kwargs):
        """Implement initializer for the class."""
        self._blob = blob if blob is not None or kwargs.get('no_blob', False) \
            else json.get_blob()
        self._json = json
        self._parsed = []

    @staticmethod
    def split_blob(blob, schema=None, **kwargs):
        """Specify how to split the blob by single record.

        In case of several records inside the blob this method specify how to
        split then and work one by one afterwards.
        """
        raise NotImplementedError()

    @classmethod
    def translate(cls, blob, json_class, master_format='json', **kwargs):
        """Transform the incoming blob into a json structure (``json_class``).

        It uses the rules described in the field and model definitions.

        :param blob: incoming blob (like MARC)
        :param json_class: Any subclass of
            :class:`~invenio.modules.jsonalchemy.wrappers.SmartJson`
        :param master_format: Master format of the input blob.
        :param kwargs: parameter to pass to json_class

        :return: New object of ``json_class`` type containing the result of the
            translation
        """
        from .wrappers import SmartJson
        if blob is None:
            raise ReaderException(
                "To perform a 'translate' operation a blob is needed")
        if not issubclass(json_class, SmartJson):
            raise ReaderException("The json class must be of type 'SmartJson'")

        json = json_class(master_format=master_format, **kwargs)
        # fill up with all possible fields
        fields = ModelParser.resolve_models(json.model_info.names,
                                            json.additional_info.namespace
                                            ).get('fields')
        cls.add(json, fields, blob, fetch_model_info=True)
        return json

    @classmethod
    def add(cls, json, fields, blob=None, fetch_model_info=False):
        """Add the list of fields to the json structure.

        If fields is ``None`` it adds all the possible fields from the current
        model.

        :param json: Any ``SmartJson`` object
        :param fields: Dict of fields to be added to the json structure
            containing field_name:json_id
        """
        reader = cls(json, blob)
        reader._prepare_blob()

        if fetch_model_info:
            reader._process_model_info()

        if isinstance(fields, six.string_types):
            fields = (fields, )
        if isinstance(fields, (list, tuple)):
            model_fields = ModelParser.resolve_models(
                json.model_info.names,
                json.additional_info.namespace).get('fields')
            fields = dict(
                (field_name, model_fields.get(field_name, field_name))
                for field_name in fields)

        for json_id, field_name in six.iteritems(fields):
            reader._unpack_rule(json_id, field_name)
        reader._post_process_json()

    @classmethod
    def set(cls, json, field, value=None, set_default_value=False):
        """Set new field value to json object.

        When adding a new field to the json object finds as much information
        about it as possible and attaches it to the json object inside
        ``json['__meta_metadata__'][field]``.

        :param json: Any ``SmartJson`` object
        :param field: Name of the new field to be added
        :param value: New value for the field (if not ``None``)
        :param set_default_value: If set to ``True`` looks for the default
            value if any and sets it.
        """
        reader = None
        json_id = None
        if field not in json.meta_metadata:
            # We don't have any meta_metadata, look for it.
            reader = cls(json=json, no_blob=True)
            json_id = \
                ModelParser.resolve_models(json.model_info,
                                           json.additional_info.namespace
                                           )['fields'].get(field, field)
            json['__meta_metadata__'][field] = \
                reader._find_field_metadata(json_id, field)

        if value:
            json[field] = value
        elif set_default_value:
            if reader is None:
                reader = cls(json=json, no_blob=True)
                json_id = \
                    ModelParser.resolve_models(json.model_info,
                                               json.additional_info.namespace
                                               )['fields'].get(field, field)

            reader._set_default_value(json_id, field)
            reader._evaluate_after_decorators(field)

    @classmethod
    def update(cls, json, fields, blob=None, update_db=False):
        """
        Update the fields given from the json structure.

        :param json: Any ``SmartJson`` object
        :param blob: incoming blob (like MARC), if ``None``, ``json.get_blob``
            will be used to retrieve it if needed.
        :param fields: List of fields to be updated, if ``None`` all fields
            will be updated.
        :param save: If set to ``True`` a 'soft save' will be performed with
            the changes.
        """
        reader = cls(json=json, blob=blob if blob else json.get_blob())
        reader._update(fields)

        if update_db:
            json.update()

    @classmethod
    def process_model_info(cls, json):
        """Process model information.

        Fetches all the possible information about the current models and
        applies all the model extensions `evaluate` methods if any extension is
        used.
        """
        reader = cls(json, no_blob=True)
        reader._process_model_info()

    @classmethod
    def update_meta_metadata(cls, json, blob=None, fields=None, section=None,
                             keep_core_values=True, store_backup=True):
        """Update the meta-metadata for a guiven set of fields.

        If it is ``None`` all fields will be used.
        """
        reader = cls(json, blob)
        reader._update_meta_metadata(fields, section, keep_core_values,
                                     store_backup)

    def _process_model_info(self):
        """Dummy method to guess the model of a given input.

        Should be redefined in the dedicated readers.

        :return: List of models found in the blob
        """
        if self._json.model_info.names == ['__default__']:
            self._json['__meta_metadata__']['__model_info__']['names'] = \
                self._guess_model_from_input()

        model = ModelParser.resolve_models(
            self._json.model_info.names, self._json.additional_info.namespace)

        for key, value in six.iteritems(model):
            if key in ('fields', 'bases'):
                continue
            ModelParser.parser_extensions()[key].evaluate(self._json, value)

    def _guess_model_from_input(self):
        """Dummy method to guess the model of a given input.

        Should be redefined in the dedicated readers.

        :return: List of models found in the blob
        """
        return ['__default__']

    def _prepare_blob(self, *args, **kwargs):
        """Dummy method to prepare blob.

        Responsible of doing any kind of transformation over the blob before
        the translation begins. It should create a common structure that all
        the methods, specially ``_get_elements_from_blob`` understand.
        """
        raise NotImplementedError()

    def _post_process_json(self):
        """Dummy method to process json data.

        Responsible of doing any kind of transformation over the json structure
        after it is created, e.g. pruning the json to delete singletons.
        """
        pass

    def _get_elements_from_blob(self, regex_key):
        """Dummy method to get elements from blob.

        Like ``get`` for a normal python dictionary but in this case it should
        handle 'entire_record' and '*' as key.

        :param regex_key: key to access the intermediate structure, could be a
            plain string or a python regular expression.

        :return: List containing the values matching the regex_key
        """
        raise NotImplementedError()

    def _unpack_rule(self, json_id, field_name=None):
        """Extract the rules from the field definitions and try to apply them.

        It applies the rules to the current json.

        :param json_id: key to access the field description in
            ``FieldParser.field_definitions``
        :param field_name: future name of the field in the json structure, if
            ``None`` json_id will be used.

        :return: ``True`` if the rule for ``json_id`` was applied successfully,
            ``False`` otherwise.
        """
        try:
            rule = FieldParser.field_definitions(
                self._json.additional_info.namespace)[json_id]
        except KeyError:
            self._json.continuable_errors.append(
                "Error - Unable to find '%s' field definition" % (json_id, ))
            return False

        if not field_name:
            field_name = json_id

        if (json_id, field_name) in self._parsed:
            return field_name in self._json

        self._parsed.append((json_id, field_name))

        # In these two method calls the decorators are never applied because of
        # the default types, i.e. when keywords are evaluated the first keyword
        # which is parsed creates a string not a list, therefore all the
        # extensions and decorators that are expecting a list will fail.
        self._apply_rules(json_id, field_name, rule)
        self._apply_virtual_rules(json_id, field_name, rule)

        self._set_default_value(json_id, field_name)
        self._set_default_type(json_id, field_name)
        self._evaluate_after_decorators(field_name)
        return field_name in self._json

    def _apply_rules(self, json_id, field_name, rule):
        """Try to apply a 'creator' rule.

        :param json_id: Name os the json field in the configuration file.
        :param field_name: Final name of the field, taken from the model
            definiti, if any, otherwise is equal to the `json_id`
        :param rule: Current rule for the `json_id`
        """
        for field_def in rule['rules'].get(
                self._json.additional_info.master_format, []):
            if not self._evaluate_before_decorators(field_def):
                continue
            for elements in \
                    self._get_elements_from_blob(field_def['source_tags']):
                if not isinstance(elements, (list, tuple)):
                    elements = (elements, )
                for element in elements:
                    if not self._evaluate_on_decorators(field_def, element):
                        continue
                    try:
                        value = try_to_eval(
                            field_def['function'],
                            functions(self._json.additional_info.namespace),
                            value=element, self=self._json)
                        self._remove_none_values(value)
                        info = self._find_field_metadata(json_id, field_name,
                                                         'creator', field_def)
                        self._json['__meta_metadata__'][field_name] = info
                        self._json.__setitem__(field_name, value, extend=True,
                                               exclude=['decorators',
                                                        'extensions'])
                    except Exception as e:
                        self._json.errors.append(
                            "Rule Error - Unable to apply rule for field "
                            "'%s' with value '%s'. \n%s"
                            % (field_name, element, str(e)),)

    def _apply_virtual_rules(self, json_id, field_name, rule):
        """Try to apply either a 'derived' or 'calculated' rule.

        :param json_id: Name os the json field in the configuration file.
        :param field_name: Final name of the field, taken from the model
            definiti, if any, otherwise is equal to the `json_id`
        :param rule: Current rule for the `json_id`
        """
        field_defs = []
        field_defs.append(('calculated', rule['rules'].get('calculated', [])))
        field_defs.append(('derived', rule['rules'].get('derived', [])))
        for (field_type, _field_def) in field_defs:
            for field_def in _field_def:
                if not self._evaluate_before_decorators(field_def):
                    continue
                try:
                    value = try_to_eval(
                        field_def['function'],
                        functions(self._json.additional_info.namespace),
                        self=self._json)
                    self._remove_none_values(value)
                    info = self._find_field_metadata(json_id, field_name,
                                                     field_type, field_def)
                    self._json['__meta_metadata__'][field_name] = info
                    self._json.__setitem__(
                        field_name, value, extend=False,
                        exclude=['decorators', 'extensions'])
                except Exception as e:
                    self._json.errors.append(
                        "Rule Error - Unable to apply rule for virtual "
                        "field '%s'. \n%s" % (field_name, str(e)),)

    def _set_default_value(self, json_id, field_name):
        """Find the default value inside the schema, if any."""
        # FIXME check how to update default values for items in a list!
        def set_default_value(field, schema):
            """Helper function to allow subfield default values."""
            if 'default' in schema:
                return schema['default']()
            elif 'schema' in schema:
                default = dict()
                for key, value in six.iteritems(schema['schema']):
                    default[key] = set_default_value(key, value)
                return default
            return None

        value = set_default_value(
            field_name, FieldParser.field_definitions(
                self._json.additional_info.namespace)[json_id]
            .get('schema', {}).get(json_id, {}))
        if value is not None:
            if field_name not in self._json._dict_bson:
                info = self._find_field_metadata(json_id, field_name,
                                                 self._json.get(field_name))
                self._json['__meta_metadata__'][field_name] = info
                self._json.__setitem__(field_name, value, extend=False,
                                       exclude=['decorators', 'extensions'])
            else:
                try:
                    old_value = self._json.__getitem__(
                        field_name, exclude=['decorators', 'extensions'])
                except KeyError:
                    old_value = value
                self._json.__setitem__(field_name, value, extend=False,
                                       exclude=['decorators', 'extensions'])
                # FIXME: Find a better way to set the default values
                try:
                    self._json._dict_bson[field_name].update(old_value)
                except (AttributeError, ValueError):
                    self._json.__setitem__(
                        field_name, old_value, extend=False,
                        exclude=['decorators', 'extensions'])

    def _set_default_type(self, json_id, field_name):
        """Find the default type inside the schema, if `force` is used."""
        from .validator import Validator

        def set_default_type(field, schema):
            """Helper function to allow subfield default values."""
            if 'type' in schema and schema.get('force', False):
                Validator.force_type(self._json._dict_bson, field_name,
                                     schema['type'])
            elif 'schema' in schema:
                for key, value in six.iteritems(schema['schema']):
                    set_default_type('%s.%s' % (field, key), value)

        if field_name not in self._json._dict_bson:
            return

        schema = FieldParser.field_definitions(
            self._json.additional_info.namespace)[json_id]\
            .get('schema', {}).get(json_id, {})
        set_default_type(field_name, schema)

    def _remove_none_values(self, obj):
        """Handy method to remove recursively ``None`` values from ``obj``."""
        if isinstance(obj, dict):
            for key in list(obj.keys()):
                if obj[key] is None:
                    del obj[key]
                else:
                    self._remove_none_values(obj[key])
        if isinstance(obj, list):
            for element in obj:
                if element is None:
                    obj.remove(element)
                else:
                    self._remove_none_values(element)

    def _update(self, fields):
        """From the list of field names try to update their content."""
        # TODO
        raise NotImplementedError('Missing implementation in current version')

    def _find_field_metadata(self, json_id, field_name,
                             field_type=None, field_def=None):
        """Find field metadata and fill up needed meta-metadata.

        Given one field definition fills up the parallel dictionary with the
        needed meta-metadata, inlcuding field extensions and after decorators.

        If the information regarding the field definition is no present, the
        first one available will be used: first ``creator`` rules for the
        master format of the json, then ``derived`` and finally ``calculated``.
        For each of them if more than one definition is present the first one
        will be used.

        If no rule is found the field info will be tag as ``UNKNOWN``

        :return: dictionary
        """
        try:
            rule = FieldParser.field_definitions(
                self._json.additional_info.namespace)[json_id]
        except KeyError:
            self._json.continuable_errors.append(
                "Adding a new field '%s' ('%s') without definition"
                % (field_name, json_id))
            rule = {}
            field_def = {}
            field_type = 'UNKNOWN'

        if field_def is None:
            if self._json.additional_info.master_format in \
                    rule.get('rules', {}):
                field_def = rule['rules'][
                    self._json.additional_info.master_format][0]
                field_type = 'creator'
            elif 'derived' in rule.get('rules', {}):
                field_def = rule['rules']['derived'][0]
                field_type = 'derived'
            elif 'calculated' in rule.get('rules', {}):
                field_def = rule['rules']['calculated'][0]
                field_type = 'calculated'
            else:
                field_def = {}
                field_type = 'UNKNOWN'

        for alias in rule.get('aliases', []):
            self._json['__meta_metadata__']['__aliases__'][alias] = field_name

        info = {}
        info['json_id'] = json_id
        info['timestamp'] = datetime.datetime.now().isoformat()
        info['pid'] = rule.get('pid', None)
        info['type'] = field_type
        info['hidden'] = rule.get('hidden', False)
        if field_type in ('calculated', 'derived'):
            info['function'] = (json_id, 'rules', field_type, 0, 'function')
        elif field_type == 'UNKNOWN':
            info['function'] = 'UNKNOWN'
        else:
            info['function'] = field_def['source_tags']

        # Decorator extensions
        info['after'] = dict()
        for name, parser in \
                six.iteritems(FieldParser.decorator_after_extensions()):
            try:
                ext = parser.add_info_to_field(
                    json_id, info,
                    field_def['decorators']['after'].get(name))
                if ext is not None:
                    info['after'][name] = ext
            except KeyError as e:
                # Only raise if the error is different the KeyError
                # 'decorators'
                if not e.args[0] == 'decorators':
                    raise e

        # Field extensions
        info['ext'] = dict()
        for name, parser in six.iteritems(FieldParser.field_extensions()):
            try:
                ext = parser.add_info_to_field(json_id, rule)
                if ext is not None:
                    info['ext'][name] = ext
            except NotImplementedError:
                # Maybe your extension doesn't have anything to add to the
                # field
                pass

        return info

    def _update_meta_metadata(self, fields=None, section=None,
                              keep_core_values=True, store_backup=True):
        """Fill up the parallel dictionary with the needed meta-metadata.

        Meta-metadata will include also field extensions and after decorators.
        If there is some information about this field in the json structure it
        will keep some core information like the source format.
        """
        # TODO
        raise NotImplementedError('Missing implementation on this version')

    def _evaluate_before_decorators(self, field_def):
        """Evaluate all the before decorators (they must return a boolean)."""
        for name, content in six.iteritems(field_def['decorators']['before']):
            if not FieldParser.decorator_before_extensions()[name]\
                    .evaluate(self, content):
                return False
        return True

    def _evaluate_on_decorators(self, field_def, master_value):
        """Evaluate all the on decorators (they must return a boolean."""
        for name, content in six.iteritems(field_def['decorators']['on']):
            if not FieldParser.decorator_on_extensions()[name]\
                    .evaluate(master_value,
                              self._json.additional_info.namespace, content):
                return False
        return True

    def _evaluate_after_decorators(self, field_name):
        """Evaluate all the after decorators."""
        if field_name not in self._json._dict_bson:
            return
        for ext, args in \
                six.iteritems(self._json.meta_metadata[field_name]['after']):
            FieldParser.decorator_after_extensions()[ext]\
                .evaluate(self._json, field_name, 'set', args)
        for ext, args in \
                six.iteritems(self._json.meta_metadata[field_name]['ext']):
            FieldParser.field_extensions()[ext]\
                .evaluate(self._json, field_name, 'set', args)
