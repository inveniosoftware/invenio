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
bibauthorid_module_coauthorship
    Meant for calculating probabilities of a virtual author and a real author
    being the same based on their coauthors.
'''

from bibauthorid_utils import create_unified_name
from bibauthorid_utils import get_field_values_on_condition
from bibauthorid_realauthor_utils import set_realauthor_data
from bibauthorid_realauthor_utils import get_realauthor_data
from bibauthorid_virtualauthor_utils import get_virtualauthor_records
from bibauthorid_authorname_utils import get_name_and_db_name_strings
from math import exp
import bibauthorid_config as bconfig

# NAME: Defines the name of the module for display purposes. [A-Za-z0-9 \-_]
MODULE_NAME = "Coauthor Comparison"
# OPERATOR: Defines the operator to use for the final computation [+|*]
MODULE_OPERATOR = "+"
# WEIGHT: Defines the weight of this module for the final computation [0..1]
MODULE_WEIGHT = 1.0
## max number of co-authors to be considered.
MAX_COAUTHORS = 60


def hash_coauthor_set(coauthors):
    '''
    In case a collaboration are not tagged as such in the appropriate MARC21
    field, this function will create a hash value for the list of authors
    after creating a sorted list of unified representations of the names.

    A collaboration is defined as a group of authors larger than the value
    MAX_COAUTHORS defined in the configuration file. MAX_COAUTHORS defaults to
    60 people.

    @param coauthors: a list of names
    @type coauthors: list of strings

    @return: A hash representation of the sorted, unified list
    @rtype: string
    '''
    hashlist = []

    for i in coauthors:
        hashlist.append(create_unified_name(i).strip())

    hashlist.sort()
    hashvalue = hash(str(hashlist))

    return hashvalue


def get_information_from_dataset(va_id, ra_id= -1):
    '''
    Retrieves information about the coauthors/collaboration attachment
    of a virtual author from the data set.

    In dependency of the real author ID, the information will be written to the
    real author holding this ID. If the real author ID should be the default
    '-1', a list with all the coauthors will be returned.

    @param va_id: Virtual author ID to get the information from
    @type va_id: int
    @param ra_id: Real author ID to set information for.
    @type ra_id: int

    @return: True, if ra_id is set OR A list of coauthors OR the name of a
        collaboration
    @rtype: True if ra_id > -1 or list of strings or string
    '''
    va_data = get_virtualauthor_records(va_id)
    bibrec_id = ""
    authorname_id = -1

    for va_data_item in va_data:
        if va_data_item['tag'] == "bibrec_id":
            bibrec_id = va_data_item['value']
        elif va_data_item['tag'] == "orig_authorname_id":
            authorname_id = va_data_item['value']

    authorname_strings = get_name_and_db_name_strings(authorname_id)

    bconfig.LOGGER.info("| Reading coauthors for va %s: %s recid %s"
                  % (va_id, authorname_strings["name"], bibrec_id))

    coauthors = get_field_values_on_condition(
                                        bibrec_id, ['100', '700'], 'a', 'a',
                                        authorname_strings["db_name"], "!=")

    collaboration = get_field_values_on_condition(bibrec_id, "710", "g")

    if (not coauthors) and (not collaboration):
        bconfig.LOGGER.info("|-> No coauthors and no collaboration found "
                            "for this author on this record")
    elif not ra_id:
        if collaboration:
            bconfig.LOGGER.info("|-> Collaboration found: %s"
                          % (list(collaboration)[0]))
        else:
            bconfig.LOGGER.info("|-> Coauthors found: %s" % (len(coauthors)))

    max_coauthors = MAX_COAUTHORS

    if ra_id > -1:
        if collaboration:
            cname = list(collaboration)[0]
            coauthor_formatted = create_unified_name(cname.lower())
            set_realauthor_data(ra_id, "coauthor", "%s;;%s"
                                % (authorname_strings["name"],
                                   coauthor_formatted))
        else:
            if len(coauthors) <= max_coauthors:
                for coauthor in coauthors:
                    coauthor_formatted = create_unified_name(coauthor.lower())
                    set_realauthor_data(ra_id, "coauthor", "%s;;%s"
                                    % (authorname_strings["name"],
                                       coauthor_formatted))
            else:
                hashvalue = hash_coauthor_set(coauthors)
                bconfig.LOGGER.info("|--> Coauthor # > %s. To preserve"
                                    " information, a hash will be stored: %s"
                                    % (max_coauthors, hashvalue))
                set_realauthor_data(ra_id, "coauthor", "%s;;%s"
                                    % (authorname_strings["name"],
                                       hashvalue))

        return True
    else:
        if collaboration:
            return collaboration
        else:
            return coauthors


def compare_va_to_ra(va_id, ra_id):
    '''
    Compares the coauthors of a virtual author with all the coauthors of
    a real author. If a collaboration is detected on both sides, these
    collaboration detachments will be compared as well.

    @param va_id: Virtual author ID
    @type va_id: int
    @param ra_id: Real author ID
    @type ra_id: int

    @return: the probability of the virtual author belonging to the real author
    @rtype: float
    '''
    bconfig.LOGGER.info("|-> Start of coauthorship comparison (va %s : ra %s)"
                  % (va_id, ra_id))

    ra_coauth_set = set()

    ra_coauthors_data = get_realauthor_data(ra_id, "coauthor")
    va_coauth_set = get_information_from_dataset(va_id)
    va_coauth_set_format = set()

#    max_coauthors = int(get_config_parameter('MAX_COAUTHORS')[0])
    max_coauthors = MAX_COAUTHORS

    if (len(ra_coauthors_data) == 0) and (len(va_coauth_set) == 0):
        bconfig.LOGGER.info("|-> End of coauthorship comparison (Sets empty)")
        return 0

    if (len(va_coauth_set) > max_coauthors):
        bconfig.LOGGER.info("|--> Many coauthors found. Will try hash"
                      + " values for collaboration testing.")
        hashed = str(hash_coauthor_set(va_coauth_set))

        for coauthor_data in ra_coauthors_data:
            if coauthor_data['value'].split(";;")[1] == hashed:
                bconfig.LOGGER.info("|---> Hash found! Assuming "
                              "collaboration attachment.")
                return 1.0

        bconfig.LOGGER.info("|---> Hash NOT found. Skipping metric.")
        return 0

    for rcoauthor_data in ra_coauthors_data:
        ra_coauth_set.add(rcoauthor_data['value'].split(";;")[1])

    for vcoauthor_data in va_coauth_set:
        va_coauth_set_format.add(create_unified_name(vcoauthor_data.lower()))

    parity = ra_coauth_set.intersection(va_coauth_set_format)

    certainty = 0

    for collaborationsearch in parity:
        if collaborationsearch.count("ollaboration"):
            bconfig.LOGGER.info("|--> Found matching collaboration: %s"
                          % (collaborationsearch))
            return 1.0

    if len(va_coauth_set) > 0:
        certainty = 1 - exp(-.8 * pow(len(parity), .7))

    bconfig.LOGGER.info("|--> Found %s matching coauthors out of %s "
                        "on the paper. Result: %s%% similarity"
                        % (len(parity), len(va_coauth_set), certainty))

    return certainty
