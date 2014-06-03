# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

"""

__revision__ = "$Id$"


from invenio.bibfield_jsonreader import JsonReader
from invenio.bibfield_utils import CoolDict, CoolList


class MarcReader(JsonReader):
    """
    Reader class that understands MARC21 as base format
    """

    @staticmethod
    def split_blob(blob, schema):
        """
        Splits the blob using <record.*?>.*?</record> as pattern.

        Note 1: Taken from invenio.bibrecord:create_records
        Note 2: Use the DOTALL flag to include newlines.
        """
        import re
        regex = re.compile('<record.*?>.*?</record>', re.DOTALL)
        return regex.findall(blob)

    def _prepare_blob(self):
        """
        Transforms the blob into rec_tree structure to use it in the standar
        translation phase inside C{JsonReader}
        """
        self.rec_tree = CoolDict()
        try:
            if self.blob_wrapper.schema.lower().startswith('file:'):
                self.blob_wrapper.blob = open(self.blob_wrapper.blob_file_name, 'r').read()
            if self.blob_wrapper.schema.lower() in ['recstruct']:
                self.__create_rectree_from_recstruct()
            elif self.blob_wrapper.schema.lower() in ['xml', 'file:xml']:
                #TODO: Implement translation directrly from xml
                from invenio.bibrecord import create_record
                self.blob_wrapper.blob = create_record(self.blob_wrapper.blob)[0]
                self.__create_rectree_from_recstruct()
        except AttributeError:
            #Assume marcxml
            from invenio.bibrecord import create_record
            self.blob_wrapper.blob = create_record(self.blob_wrapper.blob)[0]
            self.__create_rectree_from_recstruct()

    def __create_rectree_from_recstruct(self):
        """
        Using rectruct as base format it creates the intermediate structure that
        _translate will use.
        """
        for key, values in self.blob_wrapper.blob.iteritems():
            if key < '010' and key.isdigit():
                #Control field, it assumes controlfields are numeric only
                self.rec_tree[key] = CoolList([value[3] for value in values])
            else:
                for value in values:
                    field = CoolDict()
                    for subfield in value[0]:
                        field.extend(subfield[0], subfield[1])
                    self.rec_tree.extend((key + value[1] + value[2]).replace(' ', '_'), field)

## Compulsory plugin interface
readers = MarcReader
