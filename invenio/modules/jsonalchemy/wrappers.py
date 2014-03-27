# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
    invenio.modules.jsonalchemy.wrapper
    -----------------------------------
"""
import copy
import six

from invenio.utils.datastructures import DotableDict, SmartDict

from .parser import FieldParser, ModelParser
from .reader import Reader
from .registry import contexts, producers


class SmartJson(SmartDict):
    """Base class for Json structures"""

    def __init__(self, json=None, set_default_values=False,
                 process_model_info=False, **kwargs):
        """
        #TODO: explain what can go in **kwargs and for what
        """
        super(SmartJson, self).__init__(json)
        self._dict_bson = SmartDict()

        if not json or '__meta_metadata__' not in json:
            model_names = kwargs.get('model', ['__default__', ])
            if 'model' in kwargs:
                del kwargs['model']
            if isinstance(model_names, six.string_types):
                model_names = [model_names, ]
            self._dict['__meta_metadata__'] = dict()
            self._dict['__meta_metadata__']['__additional_info__'] = kwargs
            self._dict['__meta_metadata__']['__model_info__'] = \
                dict(names=model_names)
            self._dict['__meta_metadata__']['__aliases__'] = dict()
            self._dict['__meta_metadata__']['__errors__'] = list()
            self._dict['__meta_metadata__']['__continuable_errors__'] = list()

        if process_model_info:
            Reader.process_model_info(self)

        if set_default_values:
            self.set_default_values()

    @property
    def additional_info(self):
        return DotableDict(self['__meta_metadata__']['__additional_info__'])

    @property
    def errors(self):
        return self._dict['__meta_metadata__']['__errors__']

    @property
    def continuable_errors(self):
        return self._dict['__meta_metadata__']['__continuable_errors__']

    @property
    def meta_metadata(self):
        return DotableDict(self._dict['__meta_metadata__'])

    @property
    def model_info(self):
        return DotableDict(self._dict['__meta_metadata__']['__model_info__'])

    def __getitem__(self, key, reset=False, **kwargs):
        try:
            value = self._dict_bson[key]
            if value and not reset:
                return value
        except KeyError:
            #We will try to find the key inside the json dict and load it
            pass
        main_key = SmartDict.main_key_pattern.sub('', key)
        if main_key == '__meta_metadata__':
            return self._dict[key]
        elif main_key in self._dict:
            if main_key not in self.meta_metadata:
                Reader.set(self, main_key)
            action = kwargs.get('action', 'get')
            exclude = kwargs.get('exclude', [])
            if 'extensions' not in exclude:
                for ext, args in \
                        six.iteritems(self.meta_metadata[main_key]['ext']):
                    if ext in exclude:
                        continue
                    FieldParser.field_extensions()[ext]\
                        .evaluate(self, main_key, action, args)
            if 'decorators' not in exclude:
                for ext, args in \
                        six.iteritems(self.meta_metadata[main_key]['after']):
                    if ext in exclude:
                        continue
                    FieldParser.decorator_after_extensions()[ext]\
                        .evaluate(self, main_key, action, args)

            return self._dict_bson[key]
        else:
            try:
                rest_of_key = SmartDict.main_key_pattern.findall(key)[0]
            except IndexError:
                rest_of_key = ''
            return self[
                self._dict['__meta_metadata__']['__aliases__'][main_key]
                + rest_of_key]

    def __setitem__(self, key, value, extend=False, **kwargs):
        main_key = SmartDict.main_key_pattern.sub('', key)
        # If we have meta_metadata for the main key go ahead
        if main_key in self.meta_metadata:
            self._dict_bson.__setitem__(key, value, extend)
        # Othewise we need the meta_metadata
        else:
            Reader.set(self, main_key)
            self._dict_bson.__setitem__(key, value, extend, **kwargs)
        action = kwargs.get('action', 'set')
        exclude = kwargs.get('exclude', [])
        if 'decorators' not in exclude:
            for ext, args in \
                    six.iteritems(self.meta_metadata[main_key]['after']):
                if ext in exclude:
                    continue
                FieldParser.decorator_after_extensions()[ext]\
                    .evaluate(self, main_key, action, args)
        if 'extensions' not in exclude:
            for ext, args in \
                    six.iteritems(self.meta_metadata[main_key]['ext']):
                if ext in exclude:
                    continue
                FieldParser.field_extensions()[ext]\
                    .evaluate(self, main_key, action, args)

    def __str__(self):
        return self.dumps(without_meta_metadata=True).__str__()

    def __repr__(self):
        return self._dict.__repr__()

    def __delitem__(self, key):
        self._dict.__delitem__(key)
        del self._dict['__meta_metadata__'][key]
        try:
            del self._dict_bson[key]
        except KeyError:
            pass

    def get(self, key, default=None, reset=False, **kwargs):
        try:
            return self.__getitem__(key, reset, **kwargs)
        except (KeyError, IndexError):
            return default

    def items(self, without_meta_metadata=False):
        for key in self.keys():
            if key == '__meta_metadata__' and without_meta_metadata:
                continue
            yield (key, self[key])
    iteritems = items

    def keys(self, without_meta_metadata=False):
        for key in super(SmartJson, self).keys():
            if key == '__meta_metadata__' and without_meta_metadata:
                continue
            yield key

    def get_blob(self, *args, **kwargs):
        """
        Should look for the original version of the file where the json came
        from.
        """
        raise NotImplementedError()

    def dumps(self, without_meta_metadata=False, with_calculated_fields=False,
              clean=False):
        """
        Creates the JSON friendly representation of the current object.

        :param without_meta_metadata: by default ``False``, if set to ``True``
            all the ``__meta_metadata__`` will be removed from the output.
        :param wit_calculated_fields: by default the calculated fields are not
            dump, if they are needed in the output set it to ``True``
        :param clean: if set to ``True`` all the keys stating with ``_`` will be
            removed from the ouput

        :return: JSON friendly object
        """
        dict_ = copy.copy(self._dict)
        if with_calculated_fields:
            for key, value in six.iteritems(self._dict):
                if value is None and \
                        self.meta_metadata[key]['type'] == 'calculated':
                    dict_[key] = self[key]
        if without_meta_metadata:
            del dict_['__meta_metadata__']
        if clean:
            for key in list(dict_.keys()):
                if key.startswith('_'):
                    del dict_[key]
        return dict_

    def loads(self, without_meta_metadata=False, with_calculated_fields=True,
              clean=False):
        """
        Creates the BSON representation of the current object.

        :param without_meta_metadata: if set to ``True`` all the
            ``__meta_metadata__`` will be removed from the output.
        :param wit_calculated_fields: by default the calculated fields are in
            the output, if they are not needed set it to ``False``
        :param clean: if set to ``True`` all the keys stating with ``_`` will be
            removed from the ouput

        :return: JSON friendly object

        """
        dict_ = dict()
        for key in self.keys():
            dict_[key] = self[key]

        if without_meta_metadata:
            del dict_['__meta_metadata__']
        if not with_calculated_fields:
            for key in self.keys():
                if self.meta_metadata[key]['type'] == 'calculated':
                    del dict_[key]
        if clean:
            for key in list(dict_.keys()):
                if key.startswith('_'):
                    del dict_[key]

        return dict_

    def produce(self, producer_code, fields=None):
        """
        Depending on the ``producer_code`` it creates a different flavor of JSON

        :param producer_code: One of the possible producers listed in the
            ``producer`` section inside de field definitions
        :param fields: List of fields that should be present in the output, if
            ``None`` all fields from ``self`` will be used.

        :return: It depends on each producer, see producer folder inside
            jsonext, typically ``dict``.
        """
        return producers[producer_code](self, fields=fields)

    def set_default_values(self, fields=None):
        # TODO
        raise NotImplementedError('Missing implementation in this version')

    def validate(self, validator=None):
        """

        """
        if validator is None:
            from .validator import Validator as validator
        schema = dict()
        model_fields = ModelParser.resolve_models(
            self.model_info.names,
            self.additional_info.namespace).get('fields', {})
        for field in self.keys():
            if not field == '__meta_metadata__' and field not in model_fields \
                    and self.meta_metadata[field]['json_id'] not in model_fields:
                model_fields[field] = self.meta_metadata[field]['json_id']
        for json_id in model_fields.keys():
            try:
                schema.update(FieldParser.field_definitions(
                    self.additional_info.namespace)[json_id].get('schema', {}))
            except TypeError:
                pass
        _validator = validator(schema=schema)
        _validator.validate(self)
        return _validator.errors

    # Legacy methods, try not to use them as they are already deprecated

    def legacy_export_as_marc(self):
        """
        It creates a valid marcxml using the legacy rules defined in the config
        file
        """
        from collections import Iterable

        def encode_for_marcxml(value):
            from invenio.utils.text import encode_for_xml
            if isinstance(value, unicode):
                value = value.encode('utf8')
            return encode_for_xml(str(value))

        export = '<record>'
        marc_dicts = self.produce('json_for_marc')
        for marc_dict in marc_dicts:
            content = ''
            tag = ''
            ind1 = ''
            ind2 = ''
            for key, value in six.iteritems(marc_dict):
                if isinstance(value, six.string_types) or \
                        not isinstance(value, Iterable):
                    value = [value]
                for v in value:
                    if v is None:
                        continue
                    if key.startswith('00') and len(key) == 3:
                        # Control Field (No indicators no subfields)
                        export += '<controlfield tag="%s">%s</controlfield>\n'\
                            % (key, encode_for_marcxml(v))
                    elif len(key) == 6:
                        if not (tag == key[:3]
                                and ind1 == key[3].replace('_', '')
                                and ind2 == key[4].replace('_', '')):
                            tag = key[:3]
                            ind1 = key[3].replace('_', '')
                            ind2 = key[4].replace('_', '')
                            if content:
                                export += '<datafield tag="%s" ind1="%s"'\
                                    'ind2="%s">%s</datafield>\n' \
                                    % (tag, ind1, ind2, content)
                                content = ''
                        content += '<subfield code="%s">%s</subfield>'\
                            % (key[5], encode_for_marcxml(v))
                    else:
                        pass

            if content:
                export += \
                    '<datafield tag="%s" ind1="%s" ind2="%s">%s</datafield>\n'\
                    % (tag, ind1, ind2, content)

        export += '</record>'
        return export

    def legacy_create_recstruct(self):
        """
        It creates the recstruct representation using the legacy rules defined
        in the configuration file
        """
        # FIXME: it might be a bit overkilling
        from invenio.legacy.bibrecord import create_record
        return create_record(self.legacy_export_as_marc())[0]


class SmartJsonLD(SmartJson):
    """Utility class for JSON-LD serialization"""

    def translate(self, context_name, context):
        """
        Translates object to fit given JSON-LD context. Should not inject
        context as this will be done at publication time.

        """
        raise NotImplementedError('Translation not required')

    def get_context(self, context):
        """
        Returns the context definition identified by the parameter. If the
        context is not found in the current namespace, the received parameter is
        returned as is, the assumption being that a IRI was passed.

        :param: context identifier
        """
        try:
            return contexts(self.additional_info.namespace)[context]
        except KeyError:
            return context

    def get_jsonld(self, context, new_context={}, format="full"):
        """
        Returns the JSON-LD serialization.

        :param: context the context to use for raw publishing; each SmartJsonLD
                        instance is expected to have a default context
                        associated.
        :param: new_context the context to use for formatted publishing,
                            usually supplied by the client; used by the
                            'compacted', 'framed', and 'normalized' formats.
        :param: format the publishing format; can be 'full', 'inline',
                       'compacted', 'expanded', 'flattened', 'framed' or
                       'normalized'. Note that 'full' and 'inline' are synonims,
                       referring to the document form which includes the
                       context; for more information see:
                       http://www.w3.org/TR/json-ld/
        """
        from pyld import jsonld

        if isinstance(context, six.string_types):
            ctx = self.get_context(context)
        elif isinstance(context, dict):
            ctx = context
        else:
            raise TypeError('JSON-LD context must be a string or dictionary')

        try:
            doc = self.translate(context, ctx)
        except NotImplementedError:
            # model does not require translation
            doc = self.dumps(clean=True)

        doc["@context"] = ctx

        if format in ["full", "inline"]:
            return doc
        if format == "compacted":
            return jsonld.compact(doc, new_context)
        elif format == "expanded":
            return jsonld.expand(doc)
        elif format == "flattened":
            return jsonld.flatten(doc)
        elif format == "framed":
            return jsonld.frame(doc, new_context)
        elif format == "normalized":
            return jsonld.normalize(doc, new_context)
        raise ValueError('Invalid JSON-LD serialization format')
