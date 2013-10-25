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


from operator import itemgetter
try:
    from xml.etree import ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

from invenio.search_engine import get_record as get_record_original
from invenio.bibrecord import create_record as create_record_original, \
                              create_records as create_records_original


def parse_tag(tag):
    tag_code = tag[0:3]

    try:
        ind1 = tag[3]
    except IndexError:
        ind1 = "%"

    if ind1 == '_':
        ind1 = ' '

    try:
        ind2 = tag[4]
    except IndexError:
        ind2 = "%"

    if ind2 == '_':
        ind2 = ' '

    try:
        subfield_code = tag[5]
    except IndexError:
        subfield_code = None

    return tag_code, ind1, ind2, subfield_code


def convert_record(bibrecord):
    def create_control_field(inst):
        return BibRecordControlField(inst[3].decode('utf-8'))

    def create_field(inst):
        subfields = [BibRecordSubField(code, value.decode('utf-8'))
                                                for code, value in inst[0]]
        return BibRecordField(ind1=inst[1], ind2=inst[2], subfields=subfields)

    record = BibRecord()
    for tag, instances in bibrecord.iteritems():
        if tag.startswith('00'):
            record[tag] = [create_control_field(inst) for inst in instances]
        else:
            record[tag] = [create_field(inst) for inst in instances]

    return record


def get_record(recid):
    """Fetch record from the database and loads it into a bibrecord"""
    record = get_record_original(recid)
    return convert_record(record)


def create_record(xml):
    record = create_record_original(xml)[0]
    return convert_record(record)


def create_records(xml):
    return [convert_record(rec[0]) for rec in create_records_original(xml)]


def print_records(records, encoding='utf-8'):
    root = ET.Element('collection',
                      {'xmlns': 'http://www.loc.gov/MARC21/slim'})

    for record in records:
        root.append(record._to_element_tree())

    return ET.tostring(root, encoding=encoding)


class BibRecord(object):
    def __init__(self, recid=None):
        """Create an empty BibRecord object

        If you specify the recid, the record will have a 001 field set
        to the value of recid.
        """
        self.record = {}
        if recid:
            self.record['001'] = [BibRecordControlField(str(recid))]

    def __setitem__(self, tag, fields):
        self.record[tag] = fields

    def __getitem__(self, tag):
        return self.find_fields(tag)

    def __delitem__(self, tag):
        assert len(tag) >= 3
        if len(tag) == 3:
            # Case '100', it's easy to delete all fields
            del self.record[tag]
        else:
            tag_code, ind1, ind2, subfield_code = parse_tag(tag)

            if subfield_code is None:
                # Case '100__', we filter out all fields that match
                # the indicators
                self.record[tag_code] = [f for f in self.record[tag_code]
                                         if ind1 != '%' and f.ind1 != ind1
                                         or ind2 != '%' and f.ind2 != ind2]
            else:
                # Case '100__a', we filter out matching subfields
                for field in self.find_fields(tag):
                    field.subfields = [s for s in field.subfields
                                       if s.code != subfield_code]

                # Cleanup empty fields
                self.record[tag_code] = [f for f in self.record[tag_code]
                                         if f.subfields]

            # Cleanup empty list
            if not self.record[tag_code]:
                del self.record[tag_code]


    def __len__(self):
        return sum(len(fields) for fields in self.record.itervalues())

    def get(self, tag, default):
        try:
            r = self[tag]
        except KeyError:
            r = default
        return r

    def get(self, tag, default):
        try:
            r = self[tag]
        except KeyError:
            r = default
        return r

    def __eq__(self, b):
        if set(self.record.keys()) != set(b.record.keys()):
            return False

        for tag, fields in self.record.iteritems():
            if set(fields) != set(b[tag]):
                return False

        return True

    def __hash__(self):
        return hash(tuple(self.record.iteritems()))

    def __repr__(self):
        if '001' in self.record:
            s = u'BibRecord(%s)' % list(self['001'])[0].value
        else:
            s = u'BibRecord(fields=%s)' % repr(self.record)
        return s

    def find_subfields(self, tag):
        tag_code, ind1, ind2, subfield_code = parse_tag(tag)
        results = []
        for field in self.record.get(tag_code, []):
            if ind1 != '%' and field.ind1 != ind1:
                continue

            if ind2 != '%' and field.ind2 != ind2:
                continue

            for subfield in field.subfields:
                if subfield_code is None or subfield.code == subfield_code:
                    results.append(subfield)

        return results

    def find_fields(self, tag):
        tag_code, ind1, ind2, dummy = parse_tag(tag)
        results = []
        for field in self.record.get(tag_code, []):
            if ind1 != '%' and field.ind1 != ind1:
                continue

            if ind2 != '%' and field.ind2 != ind2:
                continue

            results.append(field)

        return results

    def add_field(self, tag):
        tag_code, ind1, ind2, dummy = parse_tag(tag)
        field = BibRecordField(ind1=ind1, ind2=ind2)
        self.record.setdefault(tag_code, []).append(field)
        return field

    def add_subfield(self, tag, value):
        tag_code, ind1, ind2, subfield_code = parse_tag(tag)

        subfield = BibRecordSubField(code=subfield_code, value=value)
        field = BibRecordField(ind1=ind1, ind2=ind2, subfields=[subfield])
        self.record.setdefault(tag_code, []).append(field)
        return subfield

    def _to_element_tree(self):
        root = ET.Element('record')
        for tag, fields in sorted(self.record.iteritems(), key=itemgetter(0)):
            for field in fields:
                if tag.startswith('00'):
                    controlfield = ET.SubElement(root,
                                                 'controlfield',
                                                 {'tag': tag})
                    controlfield.text = field.value
                else:
                    attribs = {'tag': tag,
                               'ind1': field.ind1,
                               'ind2': field.ind2}
                    datafield = ET.SubElement(root, 'datafield', attribs)
                    for subfield in field.subfields:
                        attrs = {'code': subfield.code}
                        s = ET.SubElement(datafield, 'subfield', attrs)
                        s.text = subfield.value
        return root

    def to_xml(self, encoding='utf-8'):
        return ET.tostring(self._to_element_tree(), encoding=encoding)


class BibRecordControlField(object):
    def __init__(self, value):
        self.value = value

    def __eq__(self, b):
        return self.value == b.value

    def __hash__(self):
        return hash(self.value)


class BibRecordField(object):
    def __init__(self, ind1=" ", ind2=" ", subfields=None):
        self.ind1 = ind1
        self.ind2 = ind2
        if subfields is None:
            subfields = []
        self.subfields = subfields

    def __repr__(self):
        return 'BibRecordField(ind1=%s, ind2=%s, subfields=%s)' \
                     % (repr(self.ind1), repr(self.ind2), repr(self.subfields))

    def __eq__(self, b):
        return self.ind1 == b.ind1 and self.ind2 == b.ind2 \
                    and set(self.subfields) == set(b.subfields)

    def __hash__(self):
        return hash((self.ind1, self.ind2, tuple(self.subfields)))

    def __len__(self):
        return len(self.subfields)

    def __getitem__(self, code):
        """Returns all the values of the subfields with given code

        @see get_subfield_values()
        """
        return self.get_subfield_values(code)

    def __setitem__(self, code, value):
        """Replaces the value of a single subfield element

        e.g. MARC:
        999C5 $ahello1$ahello2$bhello3
        record['999'][0].find_subfields('a')
        Returns ['hello1', 'hello2']
        """
        subfields = self.find_subfields(code)
        assert len(subfields) == 1
        subfields[0].value = value

    def __delitem__(self, code):
        self.subfields = [s for s in self.subfields if s.code != code]

    def find_subfields(self, code):
        """Returns all the values of the subfields with given code

        e.g. MARC:
        999C5 $ahello1$ahello2$bhello3
        record['999'][0].find_subfields('a')
        Returns ['hello1', 'hello2']
        """
        return [s for s in self.subfields if s.code == code]

    def get_subfield_values(self, code):
        return [s.value for s in self.subfields if s.code == code]

    def add_subfield(self, code, value):
        subfield = BibRecordSubField(code=code, value=value)
        self.subfields.append(subfield)
        return subfield


class BibRecordSubField(object):
    def __init__(self, code, value):
        self.code = code
        self.value = value

    def __repr__(self):
        return 'BibRecordSubField(code=%s, value=%s)' \
                                          % (repr(self.code), repr(self.value))

    def __eq__(self, b):
        return self.code == b.code and self.value == b.value

    def __hash__(self):
        return hash((self.code, self.value))
