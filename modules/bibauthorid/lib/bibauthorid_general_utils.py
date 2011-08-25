# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
'''
bibauthorid_general_utils
    Bibauthorid utilities used by many parts of the framework
'''

import sys
import re

get_record_available = True

try:
    from invenio.search_engine import get_record
except ImportError:
    get_record_available = False


# pylint: disable=R0912
# pylint: disable=R0913


def get_field_values_on_condition(bibrecid, get_table="", get_tag="",
                                         condition_tag="", condition_value="",
                                         condition="==", source="API"):
    '''
    Method to fetch data from a record in the database.
    It is possible to specify a condition in order to get
    only certain fields if condition holds.

    Examples:

    In [2]: bibauthorid_general_utils.get_field_values_on_condition
        (742535, [100, 700], 'u', 'a', 'Mathieu, Vincent')
    Out[2]: set(['UMH, Mons'])

    In [3]: bibauthorid_general_utils.get_field_values_on_condition
        (742535, [100, 700], 'u', 'a')
    Out[3]: set(['LPSC, Grenoble', 'UMH, Mons'])

    In [9]: bibauthorid_general_utils.get_field_values_on_condition
        (742535, [100,700], 'a', 'u', 'UMH, Mons')
    Out[9]: set(['Semay, Claude', 'Mathieu, Vincent'])

    In [4]: bibauthorid_general_utils.get_field_values_on_condition
        (742535, [100, 700], 'u')
    Out[4]: set(['LPSC, Grenoble', 'UMH, Mons'])

    In [5]: bibauthorid_general_utils.get_field_values_on_condition
        (742535, [100, 700])
    Out[5]:
    {'100': [([('a', 'Mathieu, Vincent'), ('u', 'UMH, Mons'), ('i', '4286')],
          ' ',
          ' ',
          '',
          3)],
     '700': [([('a', 'Semay, Claude'), ('u', 'UMH, Mons'), ('i', '4286')],
          ' ',
          ' ',
          '',
          4),
         ([('a', 'Silvestre-Brac, Bernard'),
           ('u', 'LPSC, Grenoble'),
           ('i', '2240')],
          ' ',
          ' ',
          '',
          5)]}
    In [6]: bibauthorid_general_utils.get_field_values_on_condition(1)
    Out[6]:
    {'001': [([], ' ', ' ', '1', 1)],
    '035': [([('a', 'Groom:0965xu'), ('9', 'SPIRESTeX')], ' ', ' ', '', 13)],
    '037': [([('a', 'CALT-68-62')], ' ', ' ', '', 3)],
    '100': [([('a', 'Groom, Donald E.'), ('u', 'Caltech'), ('i', '981')],
             ' ',
             ' ',
             '',
             4)],
    '245': [([('a',
                'A GENERAL RANGE ENERGY LIGHT OUTPUT PROGRAM FOR HEP')],
              ' ',
              ' ',
              '',
              5)],
    '260': [([('c', '0965')], ' ', ' ', '', 7)],
    '269': [([('c', '0965-12-01')], ' ', ' ', '', 6)],
    '300': [([('a', '10')], ' ', ' ', '', 8)],
    '690': [([('a', 'Preprint')], 'C', ' ', '', 2)],
    '961': [([('x', '2007-03-02')], ' ', ' ', '', 10),
            ([('c', '2007-03-02')], ' ', ' ', '', 11)],
    '970': [([('9', 'DESY'), ('a', 'DESY-404799')], ' ', ' ', '', 9),
            ([('a', 'SPIRES-7090030')], ' ', ' ', '', 12)],
    '980': [([('a', 'Citeable')], ' ', ' ', '', 14),
            ([('a', 'CORE')], ' ', ' ', '', 15)]}

    @param bibrecid: The id of the record (bibrec) to get
    @type bibrecid: int
    @param get_table: List of one or more tables to look attry:
    from invenio.search_engine import get_record
except ImportError:
    pass
    @type get_table: list or string or int or long
    @param get_tag: The value of this tag shall be returned
    @type get_tag: string
    @param condition_tag: First part of the condition. Provide a tag to look up
    @type condition_tag: string
    @param condition_value: Second pard of the condition. Provide a value
        that has to be matched
    @type condition_value: string
    @param condition: Optional value to describe the condition.
        Defaults to "==" and may be any comparison

    @return: set of found values, empty set if no value found.
    @rtype: set or dictionary
        (if get_tag, condition_tag and condition_value are empty)

    '''
    if not get_record_available:
        return set()

    rec = None
    if source == "MEM":
        raise AssertionError
    elif source == "API":
        rec = get_record(bibrecid)

    if condition_value and isinstance(condition_value, str):
        condition_value = condition_value.decode('utf-8')

    returnset = set()

    if not rec:
        return set()

    if get_table:
        if not isinstance(get_table, list):
            if isinstance(get_table, str):
                get_table = [get_table]
            elif isinstance(get_table, int) or isinstance(get_table, long):
                get_table = [str(get_table)]
            else:
                sys.stderr.write('Error: Wrong table for table selection. ' +
                    'Allowed are list of strings, string or int/long values\n')


        for table in get_table:
            if str(table) in rec:
                if table in ["cites", "cited-by"]:
                    return rec[str(table)]

                for recordentries in rec[str(table)]:
                    is_condition = True
                    is_skip_entry = False

                    for field in recordentries[0]:
                        if condition_tag and condition_value:
                            if field[0] == condition_tag:
                                condition_holds = False
                                try:
                                    condition_holds = not eval(("field[1].decode('utf-8') %s"
                                        + " condition_value") % (condition))
                                except (TypeError, NameError, IndexError):
                                    condition_holds = False

                                if condition_holds:
                                    is_skip_entry = True
                                    is_condition = False
                                    break
                        elif get_tag:
                            if get_tag == field[0]:
                                returnset.add(field[1].decode('utf-8'))
                        else:
                            retlist = {}

                            for table in get_table:
                                try:
                                    retlist[str(table)] = rec[str(table)]
                                except KeyError:
                                    pass

                            return retlist

                    if is_condition and not is_skip_entry:
                        for field in recordentries[0]:
                            if field[0] == get_tag:
                                returnset.add(field[1].decode('utf-8'))

        if len(returnset) == 0:
            returnset = set()

        return returnset
    else:
        return rec


# pylint: enable=R0912
# pylint: enable=R0913

