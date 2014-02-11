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
import datetime
import six

from werkzeug.utils import import_string

from invenio.base.utils import try_to_eval
from invenio.utils.datastructures import SmartDict

from .parser import FieldParser, ModelParser
from .registry import functions, readers, producers, contexts
from .validator import Validator


class SmartJson(SmartDict):
    """Base class for Json structures"""

    def __init__(self, json=None, **kwargs):
        super(SmartJson, self).__init__(json)
        self._dict_bson = SmartDict()
        self._validator = None

        if json is None or not json:
            self._dict['__meta_metadata__'] = dict()
            self._dict['__meta_metadata__']['__additional_info__'] = kwargs
            self._dict['__meta_metadata__']['__aliases__'] = {}
            self._dict['__meta_metadata__']['__errors__'] = []
            self._dict['__meta_metadata__']['__continuable_errors__'] = []

        if '__meta_metadata__.__additional_info__.model_meta_classes' in self:
            meta_classes = [import_string(str_cls)
                    for str_cls in self['__meta_metadata__.__additional_info__.model_meta_classes']]
            self.__class__ = type(self.__class__.__name__,
                    [self.__class__] + meta_classes, {})


    def __getitem__(self, key):
        """
        Uses the load capabilities to output the information stored in the DB.
        """
        try:
            return self._dict_bson[key]
        except KeyError:
            #We will try to find the key inside the json dict and load it
            pass

        main_key = SmartDict.main_key_pattern.sub('', key)
        if main_key in self._dict['__meta_metadata__']['__aliases__']:
            try:
                rest_of_key = SmartDict.main_key_pattern.findall(key)[0]
            except IndexError:
                rest_of_key = ''
            return self[self._dict['__meta_metadata__']['__aliases__'][main_key] + rest_of_key]
        try:
            if self._dict['__meta_metadata__'][main_key]['type'] == 'calculated':
                self._load_precalculated_value(main_key)
            else:
                self._loads(main_key)
        except KeyError:
            self._loads(main_key)

        return self._dict_bson[key]

    def __setitem__(self, key, value, extend=False):
        """
        Uses the dumps capabilities to set the items to store them in the DB
        """
        main_key = SmartDict.main_key_pattern.sub('', key)
        if main_key in self:
            self._dict_bson.__setitem__(key, value, extend)
        else:
            reader = readers[self['__meta_metadata__']['__additional_info__']['master_format']]\
                (namespace=self['__meta_metadata__']['__additional_info__']['namespace'])
            reader.set(self, main_key)
            self._dict_bson.__setitem__(key, value, extend)

        self._dumps(main_key)

    def items(self):
        for key in self.keys():
            yield (key, self[key])

    @property
    def validation_errors(self):
        if self._validator is None:
            self.validate()
        return self._validator.errors

    def dumps(self):
        """ """
        for key in self._dict_bson.keys():
            if key == '__meta_metadata__':
                continue
            self._dumps(key)
        return self._dict

    def loads(self):
        """ """
        for key in self._dict.keys():
            if key == '__meta_metadata__':
                continue
            self._loads(key)
        return self._dict_bson._dict

    def produce(self, output, fields=None):
        return producers[output](self, fields=fields)

    def validate(self):

        def find_schema(json_id):
            schema = FieldParser.field_definitions(self['__meta_metadata__']['__additional_info__']['namespace']).get(json_id, {})
            if isinstance(schema, list):
                for jjson_id in schema:
                    yield FieldParser.field_definitions(self['__meta_metadata__']['__additional_info__']['namespace']).get(jjson_id, {}).get('schema', {})
                raise StopIteration()
            yield schema.get('schema', {})

        if self._validator is None:
            schema = {}
            model_fields = ModelParser.model_definitions(self['__meta_metadata__']['__additional_info__']['namespace']).get(fields, {})
            if model_fields:
                for field in self.document.keys():
                    if field not in model_fields:
                        model_fields[field] = field
                model_field = [json_id for json_id in model_fields.values()]
            else:
                model_fields = self.document.keys()

            for json_id in model_fields:
                for schema in find_schema(json_id):
                    self.schema.update(schema)
            self._validator = Validator(schema=shema)

        return self._validator.validate(self)

    def _dumps(self, field):
        """ """
        try:
            self._dict[field] = reduce(lambda obj, key: obj[key], \
                    self._dict['__meta_metadata__'][field]['dumps'], \
                    FieldParser.field_definitions(self['__meta_metadata__']['__additional_info__']['namespace']))(self._dict_bson[field])
        except (KeyError, IndexError):
            if self['__meta_metadata__'][field]['memoize'] or \
                    self['__meta_metadata__'][field]['type'] in ('derived', 'creator', 'UNKNOWN'):
                self._dict[field] = self._dict_bson[field]

    def _loads(self, field):
        """ """
        try:
            self._dict_bson[field] = reduce(lambda obj, key: obj[key], \
                    self._dict['__meta_metadata__'][field]['loads'], \
                    FieldParser.field_definition(self['__meta_metadata__']['__additional_info__']['namespace']))(self._dict[field])
        except (KeyError, IndexError):
            self._dict_bson[field] = self._dict[field]

    def _load_precalculated_value(self, field):
        """

        """
        if self._dict['__meta_metadata__'][field]['memoize'] is None:
            func = reduce(lambda obj, key: obj[key], \
                    self._dict['__meta_metadata__'][field]['function'], \
                    FieldParser.field_definitions(self['__meta_metadata__']['__additional_info__']['namespace']))
            self._dict_bson[field] = try_to_eval(func,
                    functions(self['__meta_metadata__']['__additional_info__']['namespace']),
                    self=self)
        else:
            live_time = datetime.timedelta(0, self._dict['__meta_metadata__'][field]['memoize'])
            timestamp = datetime.datetime.strptime(self._dict['__meta_metadata__'][field]['timestamp'], "%Y-%m-%dT%H:%M:%S")
            if datetime.datetime.now() > timestamp + live_time:
                old_value = self._dict_bson[field]
                func = reduce(lambda obj, key: obj[key], \
                    self._dict['__meta_metadata__'][field]['function'], \
                    FieldParser.field_definitions(self['__meta_metadata__']['__additional_info__']['namespace']))
                self._dict_bson[field] = try_to_eval(func,
                        functions(self['__meta_metadata__']['__additional_info__']['namespace']),
                        self=self)
                if not old_value == self._dict_bson[field]:
                    #FIXME: trigger update in DB and fire signal to update others
                    pass

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
            for key, value in marc_dict.iteritems():
                if isinstance(value, six.string_types) or not isinstance(value, Iterable):
                    value = [value]
                for v in value:
                    if v is None:
                        continue
                    if key.startswith('00') and len(key) == 3:
                        # Control Field (No indicators no subfields)
                        export += '<controlfield tag="%s">%s</controlfield>\n' % (key, encode_for_marcxml(v))
                    elif len(key) == 6:
                        if not (tag == key[:3] and ind1 == key[3].replace('_', '') and ind2 == key[4].replace('_', '')):
                            tag = key[:3]
                            ind1 = key[3].replace('_', '')
                            ind2 = key[4].replace('_', '')
                            if content:
                                export += '<datafield tag="%s" ind1="%s" ind2="%s">%s</datafield>\n' % (tag, ind1, ind2, content)
                                content = ''
                        content += '<subfield code="%s">%s</subfield>' % (key[5], encode_for_marcxml(v))
                    else:
                        pass

            if content:
                export += '<datafield tag="%s" ind1="%s" ind2="%s">%s</datafield>\n' % (tag, ind1, ind2, content)

        export += '</record>'
        return export

    def legacy_create_recstruct(self):
        """
        It creates the recstruct representation using the legacy rules defined in
        the configuration file

        #CHECK: it might be a bit overkilling
        """
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
            return contexts(self['__meta_metadata__']['__additional_info__']['namespace'])[context]
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
        :param: format the publishing format; can be 'full', 'compacted',
                       'expanded', 'flattened', 'framed' or 'normalized'
        """
        from pyld import jsonld
        import six

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
            doc = self.dumps()
            del doc["__meta_metadata__"]
        doc["@context"] = ctx

        if format == "full":
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
