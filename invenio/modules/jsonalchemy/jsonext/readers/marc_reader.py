# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
    invenio.modules.jsonalchemy.jsonext.readers.marc_reader
    --------------------------------------------------------

"""
import re
from six import iteritems
from werkzeug.utils import import_string

from invenio.base.globals import cfg

from invenio.modules.jsonalchemy.reader import Reader
from invenio.modules.jsonalchemy.errors import ReaderException


class MarcReader(Reader):
    """Marc reader"""

    __master_format__ = 'marc'

    split_marc = re.compile('<record.*?>.*?</record>', re.DOTALL)

    @staticmethod
    def split_blob(blob, schema=None, **kwargs):
        """
        Splits the blob using <record.*?>.*?</record> as pattern.

        Note 1: Taken from invenio.legacy.bibrecord:create_records
        Note 2: Use the DOTALL flag to include newlines.
        """
        if schema in (None, 'xml'):
            for match in MarcReader.split_marc.finditer(blob):
                yield match.group()
        else:
            raise StopIteration()

    def guess_model_from_input(self):
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
        if regex_key in ('entire_record', '*'):
            return self.rec_tree
        elements = []
        for k in regex_key:
            regex = re.compile(k)
            keys = filter(regex.match, self.rec_tree.keys())
            values = []
            for key in keys:
                values.append(self.rec_tree.get(key))
            elements.extend(values)
        return elements

    def _prepare_blob(self, *args, **kwargs):
        #FIXME stop using recstruct!
        from invenio.legacy.bibrecord import create_record

        class SaveDict(dict):
            __getitem__ = dict.get

        def dict_extend_helper(d, key, value):
            """
            If the key is present inside the dictionary it creates a list (it not
            present) and extends it with the new value. Almost as in C{list.extend}
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
            raise ReaderException("There was an error while parsing MARCXML: %s"
                                  % (errors,))
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

reader = MarcReader
