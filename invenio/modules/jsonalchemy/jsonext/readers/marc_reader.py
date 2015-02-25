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
Marc reader.

This reader (or any) shouldn't be used directly, at least in the normal use
cases. Instead :class:`~invenio.modules.jsonalchemy.readers.Reader` should be
used with the explicit format.
"""

import copy
import re
from six import iteritems
from werkzeug.utils import import_string

from invenio.base.globals import cfg
from invenio.base.utils import try_to_eval

from invenio.modules.jsonalchemy.reader import Reader
from invenio.modules.jsonalchemy.errors import ReaderException
from invenio.modules.jsonalchemy.registry import functions


class MarcReader(Reader):

    """Marc reader."""

    __master_format__ = 'marc'

    split_marc = re.compile('<record.*?>.*?</record>', re.DOTALL)

    @staticmethod
    def split_blob(blob, schema=None, **kwargs):
        """Split the blob using <record.*?>.*?</record> as pattern.

        Note 1: Taken from invenio.legacy.bibrecord:create_records
        Note 2: Use the DOTALL flag to include newlines.
        """
        if schema in (None, 'xml'):
            for match in MarcReader.split_marc.finditer(blob):
                yield match.group()
        else:
            raise StopIteration()

    def guess_model_from_input(self):
        """Guess from the input Marc the model to be used in this record.

        This is the simplest implementation possible, it just take all `980__a`
        tags and sets it as list of models.
        The guess function could be easily change by setting
        `CFG_MARC_MODEL_GUESSER` with an importable string
        """
        guess_function = cfg.get('CFG_MARC_MODEL_GUESSER', None)

        if guess_function:
            return import_string(guess_function)(self)

        try:
            return [coll['a'].lower()
                    for coll in self.rec_tree.get('980__') if 'a' in coll]
        except TypeError:
            try:
                return self.rec_tree.get('980__', {})['a']
            except:
                return '__default__'

    def _get_elements_from_blob(self, regex_key):
        """Retrieve elements from the blob or the intermediate structure.

        :return: A tuple containing the first match for the list of regex_keys
        """
        if regex_key in ('entire_record', '*'):
            return self.rec_tree
        for k in regex_key:
            regex = re.compile(k)
            keys = filter(regex.match, self.rec_tree.keys())
            for key in keys:
                if key in self.rec_tree:
                    return (key, self.rec_tree.get(key, []))
        return ('', [])

    def _prepare_blob(self, *args, **kwargs):
        """Transform the incoming blob into recstruct.

        FIXME: stop using recstruct!
        """
        from invenio.legacy.bibrecord import create_record

        class SaveDict(dict):
            __getitem__ = dict.get

        def dict_extend_helper(d, key, value):
            """Helper function.

            If the key is present inside the dictionary it creates a list (if
            not present) and extends it with the new value.
            Almost as in `list.extend`
            """
            if key in d:
                current_value = d.get(key)
                if not isinstance(current_value, list):
                    current_value = [current_value]
                current_value.append(value)
                value = current_value
            d[key] = value
        self.rec_tree = SaveDict()
        record, status_code, errors = create_record(self._blob)
        if status_code == 0:
            if isinstance(errors, list):
                errors = "\n".join(errors)
            # There was an error
            raise ReaderException(
                "There was an error while parsing MARCXML: %s" % (errors,))
        for key, values in iteritems(record):
            if key < '010' and key.isdigit():
                self.rec_tree[key] = [value[3] for value in values]
            else:
                for value in values:
                    field = SaveDict()
                    for subfield in value[0]:
                        dict_extend_helper(field, subfield[0], subfield[1])
                    dict_extend_helper(
                        self.rec_tree,
                        (key + value[1] + value[2]).replace(' ', '_'), field)

    def _apply_rules(self, json_id, field_name, rule):
        """Override default behavior.

        See :meth:`~invenio.modules.jsonalchemy.readers.Reader._apply_rules`.

        Tries to apply all the rules defined for marc and as soon as it can
        apply one it stops the process.
        It also keeps the marc_tag that comes from
        :meth:`._get_elements_from_blob`

        :param json_id: as in
            :meth:`~invenio.modules.jsonalchemy.readers.Reader._apply_rules`
        :param field_name: as in
            :meth:`~invenio.modules.jsonalchemy.readers.Reader._apply_rules`
        :param rule: as in
            :meth:`~invenio.modules.jsonalchemy.readers.Reader._apply_rules`
        """
        for field_def in rule['rules'].get(
                self._json.additional_info.master_format, []):
            if not self._evaluate_before_decorators(field_def):
                continue
            marc_tag, elements = self._get_elements_from_blob(
                field_def['source_tags'])
            if not isinstance(elements, (list, tuple)):
                elements = (elements, )
            for element in elements:
                tmp_field_def = copy.deepcopy(field_def)
                tmp_field_def['source_tags'] = [marc_tag, ]
                if not self._evaluate_on_decorators(tmp_field_def, element):
                    continue
                try:
                    value = try_to_eval(
                        tmp_field_def['function'],
                        functions(self._json.additional_info.namespace),
                        value=element, self=self._json)
                    self._remove_none_values(value)
                    info = self._find_field_metadata(json_id, field_name,
                                                     'creator', tmp_field_def)
                    self._json['__meta_metadata__'][field_name] = info
                    self._json.__setitem__(field_name, value, extend=True,
                                           exclude=['decorators',
                                                    'extensions'])
                except Exception as e:
                    self._json.errors.append(
                        "Rule Error - Unable to apply rule for field "
                        "'%s' with value '%s'. \n%s"
                        % (field_name, element, str(e)),)
            if field_name in self._json._dict_bson:
                break

reader = MarcReader
