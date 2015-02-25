# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2010, 2011 CERN.
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

__revision__ = "$Id$"

import invenio.legacy.elmsubmit.config as elmsubmit_config

def generate_marc(submission_dict):
    """ method generates a marc xml file from the submission dict
    """
    marc_dict = {}


    for field in submission_dict.keys():
        # print "field", field, submission_dict[field]

        # marc_dict should cotain a dictionary {'marc_code', value, ...}

        generate_data_field(field, submission_dict[field], marc_dict)

    # generate an xml file from marc_dict

    # print 'MARC DICT', marc_dict

    full_marc = print_marc(marc_dict)

    return full_marc


def print_marc(marc_dict):
    """ method prints the xml file from the transformed dictionary
    """
    marc_text = '<record>\n'

    # extract the ind1 and ind2 tags
    for key in marc_dict.keys():
        tag = key[0:3]
        if key[3] != '_':
            ind1 = key[3]
        else:
            ind1 =''
        if key[4] != '_':
            ind2 = key[4]
        else:
            ind2 = ''

        # subfields joined into one field
        if key in elmsubmit_config.CFG_ELMSUBMIT_MARC_FIELDS_JOINED.keys():

            tuple_list = marc_dict[key]

            prefix_list = []
            prefix_dict = {}

            # make a list and a dictionary with occurance numbers
            for subfield_tuple in marc_dict[key]:
                prefix_list.append(subfield_tuple[0])
                if (subfield_tuple[0] in prefix_dict) == 1:
                    prefix_dict[subfield_tuple[0]] = prefix_dict[subfield_tuple[0]] + 1
                else:
                    prefix_dict[subfield_tuple[0]] = 1


            for linked_prefix_list in elmsubmit_config.CFG_ELMSUBMIT_MARC_FIELDS_JOINED[key]:

                #we found a list of prefixes to join, build a field out of them

                while contains_elements(linked_prefix_list, prefix_dict.keys()):

                    marc_text = marc_text + '<datafield tag ="' + tag + '" ind1="' + ind1 + '" ind2="' + ind2 + '">\n'

                    for prefix in linked_prefix_list:

                        tuple_index = prefix_list.index(prefix)


                        sub_tuple = tuple_list[tuple_index]
                        marc_text = marc_text + '<subfield code="' + sub_tuple[0] + '">' + sub_tuple[1] + '</subfield>\n'

                        del tuple_list[tuple_index]
                        del prefix_list[tuple_index]
                        prefix_dict[prefix] = prefix_dict[prefix] - 1
                        if prefix_dict[prefix] == 0:
                            del prefix_dict[prefix]


                    marc_text = marc_text + '</datafield>\n'

            # append the actual datafields
            for sub_tuple in tuple_list:

                marc_text = marc_text + '<datafield tag ="' + tag + '" ind1="' + ind1 +'" ind2="' + ind2 + '">\n'

                marc_text = marc_text + '<subfield code="' + sub_tuple[0] + '">' + sub_tuple[1] + '</subfield>\n'

                prefix_dict[sub_tuple[0]] = prefix_dict[sub_tuple[0]] - 1
                if prefix_dict[sub_tuple[0]] == 0:
                    del prefix_dict[sub_tuple[0]]

                marc_text = marc_text + '</datafield>\n'

            del tuple_list
            del prefix_list


        else:

            # simply create the datafield
            for subfield_tuple in marc_dict[key]:
                marc_text = marc_text + '<datafield tag ="' + tag + '" ind1="' + ind1 + '" ind2="' + ind2 + '">\n'
                marc_text = marc_text + '<subfield code="' + subfield_tuple[0] + '">' + subfield_tuple[1] + '</subfield>\n'
                marc_text = marc_text + '</datafield>\n'

    marc_text = marc_text + '</record>'
    return marc_text

def contains_elements(small_list, big_list):
    """function checking if all elements of list a are in list b
    """
    for element in small_list:
        try:
            a = big_list.index(element)
        except ValueError:
            return False

    return True




def generate_data_field(field, value, marc_dict):
    """ for a given data field, determine if it is in the marc dictionary dictionary and update marc_dict accordingly
    """

    if (field in elmsubmit_config.CFG_ELMSUBMIT_MARC_MAPPING):
        # print "field:", field

        # field is a normal field

        if not isinstance(elmsubmit_config.CFG_ELMSUBMIT_MARC_MAPPING[field], list):

            for value_part in value:
                (datafield, subfield) = process_marc(elmsubmit_config.CFG_ELMSUBMIT_MARC_MAPPING[field])
                if (datafield in marc_dict) == 1:
                    marc_dict[datafield].append((subfield, value_part))
                else:
                    marc_dict[datafield] = [(subfield, value_part)]

        else:

            # field is a list

            #determine the length

            for value_part in value:
                if value.index(value_part) == 0:
                    (datafield, subfield) = process_marc(elmsubmit_config.CFG_ELMSUBMIT_MARC_MAPPING[field][0])
                    if (datafield in marc_dict) == 1:
                        marc_dict[datafield].append((subfield, value_part))
                    else:
                        marc_dict[datafield] = [(subfield, value_part)]
                else:
                    (datafield, subfield) = process_marc(elmsubmit_config.CFG_ELMSUBMIT_MARC_MAPPING[field][1])
                    if (datafield in marc_dict) == 1:
                        marc_dict[datafield].append((subfield, value_part))
                    else:
                        marc_dict[datafield] = [(subfield, value_part)]
    else:
        pass
        #print "field_not_in Marc:", field


def process_marc(marc_code):
    """ extract the datafield and subfield from a Marc field
    """
    # print "marc_code", marc_code
    datafield = marc_code[0:5]
    subfield = marc_code[5]
    # print "datafield", datafield, "subfield", subfield
    return (datafield, subfield)

