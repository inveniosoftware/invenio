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
bibauthorid_utils
    Bibauthorid utilities used by many parts of the framework
'''

import sys
import re

import bibauthorid_config as bconfig
import bibauthorid_structs as dat

try:
    from invenio.search_engine import get_record
except ImportError:
    pass


def string_partition(s, sep, dir='l'):
    '''
    Partition a string by the first occurrence of the separator.
    Mimics the string.partition function, which is not available in Python2.4

    @param s: string to be partitioned
    @type s: string
    @param sep: separator to partition by
    @type sep: string
    @param dir: direction (left 'l' or right 'r') to search the separator from
    @type dir: string

    @return: tuple of (left or sep, sep, right of sep)
    @rtype: tuple
    '''
    if dir == 'r':
        i = s.rfind(sep)
    else:
        i = s.find(sep)
    if i < 0:
        return (s, '', '')
    else:
        return (s[0:i], s[i:i + 1], s[i + 1:])


def split_name_parts(name_string, delete_name_additions=True,
                     override_surname_sep=''):
    '''
    Splits name_string in three arrays of strings :
        surname, initials (without trailing dot), names
    RETURNS an array containing a string and two arrays of strings.
    delete_name_additions defines if extensions
        e.g. Jr., (Ed.) or (spokesperson)
        will be ignored

    @param name_string: the name to be spli
    @type name: string
    @param delete_name_additions: determines whether to delete name additions
    @type delete_name_additions: boolean
    @param override_surname_sep: Define alternative surname separator
    @type override_surname_sep: string
    @param reverse_name_surname: if true names come first

    @return: list of [surname string, initials list, names list]
        e.g. split_name_parts("Ellis, John R.")
        --> ['Ellis', ['J', 'R'], ['John'], [0]]
        --> ['Ellis', ['K', 'J', 'R'], ['John', 'Rob'], [1,2]]
    @rtype: list of lists
    '''
    if not override_surname_sep:
        surname_separators = bconfig.SURNAMES_SEPARATOR_CHARACTER_LIST
    else:
        surname_separators = ','

    name_separators = bconfig.NAMES_SEPARATOR_CHARACTER_LIST

    if name_separators == "-1":
        name_separators = ',;.=\-\(\)'

    if delete_name_additions:
        name_additions = re.findall('\([.]*[^\)]*\)', name_string)
        for name_addition in name_additions:
            name_string = name_string.replace(name_addition, '')

    surname = ""
    rest_of_name = ""
    found_sep = ''
    name_string = name_string.strip()

    for sep in surname_separators:
        if name_string.count(sep) >= 1:
            found_sep = sep
            surname, rest_of_name = string_partition(name_string, sep)[0::2]
            break

    if not found_sep:
        if name_string.count(" ") > 0:
            rest_of_name, surname = string_partition(name_string, ' ', dir='r')[0::2]
        else:
            return [name_string, [], []]

    if rest_of_name.count(","):
        rest_of_name = string_partition(rest_of_name, ",")[0]

    substitution_regexp = re.compile('[%s]' % (name_separators))
    initials_names_list = substitution_regexp.sub(' ', rest_of_name).split()
    names = []
    initials = []
    positions = []
    pos_counter = 0
    for i in initials_names_list:
        if len(i) == 1:
            initials.append(i.capitalize())
            pos_counter += 1
        else:
            names.append(i.capitalize())
            initials.append(i[0].capitalize())
            positions.append(pos_counter)
            pos_counter += 1

    return [surname, initials, names, positions]


def split_name_parts_old(name_string, delete_name_additions=True):
    '''
    Splits name_string in three arrays of strings :
        surname, initials (without trailing dot), names
    RETURNS an array containing a string and two arrays of strings.
    delete_name_additions defines if extensions
        e.g. Jr., (Ed.) or (spokesperson)
        will be ignored

    @param name_string: the name to be spli
    @type name: string
    @param delete_name_additions: determines whether to delete name additions
    @type delete_name_additions: boolean

    @return: list of [surname string, initials list, names list]
        e.g. split_name_parts("Ellis, John R.")
        --> ['Ellis', ['J', 'R'], ['John']]
    @rtype: list of lists

    '''
    name_separators = bconfig.NAMES_SEPARATOR_CHARACTER_LIST

    if name_separators == "-1":
        name_separators = '.,;=\-\(\)'

    if delete_name_additions:
        name_additions = re.findall('\([.]*[^\)]*\)', name_string)
        for name_addition in name_additions:
            name_string = name_string.replace(name_addition, '')

    surname, rest_of_name = string_partition(name_string, ',')[0::2]

    if rest_of_name.count(","):
        rest_of_name = string_partition(rest_of_name, ",")[0]

    substitution_regexp = re.compile('[%s]' % (name_separators))
    initials_names_list = substitution_regexp.sub(' ', rest_of_name).split()
    names = []
    initials = []

    for i in initials_names_list:
        if len(i) == 1:
            initials.append(i.capitalize())
        else:
            names.append(i.capitalize())
            initials.append(i[0].capitalize())

    return [surname, initials, names]


def create_canonical_name(name):
    canonical_name = create_unified_name(name, reverse=True)
    artifact_removal = re.compile("[^a-zA-Z0-9]")
    whitespace_removal = re.compile("[ ]{1,10}")
    canonical_name = artifact_removal.sub(" ", canonical_name)
    canonical_name = whitespace_removal.sub(" ", canonical_name)
    canonical_name = canonical_name.strip().replace(" ", ".")
    return canonical_name

def create_normalized_name(splitted_name):
    '''
    Creates a normalized name from a given name array. A normalized name
    looks like "Lastname, Firstnames and Initials"

    @param splitted_name: name array from split_name_parts
    @type splitted_name: list in form [string, list, list]

    @return: normalized name
    @rtype: string
    '''
    name = splitted_name[0] + ','

    if not splitted_name[1] and not splitted_name[2]:
        return name

    for i in splitted_name[1]:
        try:
            fname = splitted_name[2][splitted_name[3].index(splitted_name[1].index(i))]
            name = name + ' ' + fname
        except:
            name = name + ' ' + i + '.'
    return name


def create_unified_name(name, reverse=False):
    '''
    Creates unified name. E.g. Ellis, John Richard T. (Jr.)
    will become Ellis, J. R. T.

    @param name: The name to be unified
    @type name: string

    @param reverse: if true, names come first

    @return: The unified name
    @rtype: string

    '''
    split_name = split_name_parts(name)

    if reverse:
        unified_name = ''
        for i in split_name[1]:
            unified_name += "%s. " % (i)
        unified_name += "%s" % (split_name[0])
    else:
        unified_name = "%s, " % (split_name[0])
        for i in split_name[1]:
            unified_name += "%s. " % (i)

    if unified_name.count("ollabo"):
        unified_name = unified_name.replace("ollaborations", "ollaboration")
        unified_name = unified_name.replace("The ", "")
        unified_name = unified_name.replace("the ", "")
        unified_name = unified_name.replace("For ", "")
        unified_name = unified_name.replace("for ", "")


    return unified_name

# pylint: disable=R0912
# pylint: disable=R0913


def get_field_values_on_condition(bibrecid, get_table="", get_tag="",
                                         condition_tag="", condition_value="",
                                         condition="==", source="MEM"):
    '''
    Method to fetch data from a record in the database.
    It is possible to specify a condition in order to get
    only certain fields if condition holds.

    Examples:

    In [2]: bibauthorid_utils.get_field_values_on_condition
        (742535, [100, 700], 'u', 'a', 'Mathieu, Vincent')
    Out[2]: set(['UMH, Mons'])

    In [3]: bibauthorid_utils.get_field_values_on_condition
        (742535, [100, 700], 'u', 'a')
    Out[3]: set(['LPSC, Grenoble', 'UMH, Mons'])

    In [9]: bibauthorid_utils.get_field_values_on_condition
        (742535, [100,700], 'a', 'u', 'UMH, Mons')
    Out[9]: set(['Semay, Claude', 'Mathieu, Vincent'])

    In [4]: bibauthorid_utils.get_field_values_on_condition
        (742535, [100, 700], 'u')
    Out[4]: set(['LPSC, Grenoble', 'UMH, Mons'])

    In [5]: bibauthorid_utils.get_field_values_on_condition
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
    In [6]: bibauthorid_utils.get_field_values_on_condition(1)
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
    @param get_table: List of one or more tables to look at
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
    rec = None
    if source == "MEM":
        rec = dat.RELEVANT_RECORDS.get(bibrecid)
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


def str_to_unicode(obj, encoding="utf-8"):
    '''
    Transforms any string object into a unicode object.

    @param obj: the object to be transformed
    @type obj: string or unicode
    @param encoding: the preferred encoding. Defaults to UTF-8
    @type encoding: string

    @return: returns the unicode representation of the object.
    @rtype: basetype::unicode

    '''
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


def str_to_int(string_value):
    '''
    Transforms a string into an int value

    @param string_value: The string representation of an integer
    @type string_value: string

    @return: The int value of the string
    @rtype: int

    '''
    return int(''.join([c for c in string_value if c.isdigit()]))


def clean_name_string(namestring, replacement=" ", keep_whitespace=True,
                      trim_whitespaces=False):
    '''
    remove specific artifacts from the names in order to be able to
    compare them. E.g. 't Hooft, G. and t'Hooft, G.

    @param namestring: the string to be cleaned
    @type namestring: string
    '''
#    artifact_removal = re.compile("['`\-\[\]\_\"]")
    artifact_removal = None

    if trim_whitespaces:
        namestring.strip()

    if keep_whitespace:
        artifact_removal = re.compile("[^a-zA-Z0-9,.\s]")
    else:
        artifact_removal = re.compile("[^a-zA-Z0-9,.]")

    whitespace_removal = re.compile("[\s]{2,100}")
    tmp = artifact_removal.sub(replacement, namestring)

#    print namestring, "->", whitespace_removal.sub(" ", tmp).strip()

    return whitespace_removal.sub(" ", tmp).strip()
