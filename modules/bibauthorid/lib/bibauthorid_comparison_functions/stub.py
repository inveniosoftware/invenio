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
bibauthorid_module_stub
    Meant for calculating probabilities of a virtual author and a real author
    being the same based on their data on a particular paper.
'''
from bibauthorid_utils import get_field_values_on_condition
from bibauthorid_realauthor_utils import set_realauthor_data
from bibauthorid_realauthor_utils import get_realauthor_data
from bibauthorid_virtualauthor_utils import get_virtualauthor_records
from bibauthorid_authorname_utils import get_name_and_db_name_strings
from math import exp
import bibauthorid_config as bconfig

# NAME: Defines the name of the module for display purposes. [A-Za-z0-9 \-_]
MODULE_NAME = "Data Comparison"
# OPERATOR: Defines the operator to use for the final computation [+|*]
MODULE_OPERATOR = "+"
# WEIGHT: Defines the weight of this module for the final computation [0..1]
MODULE_WEIGHT = 1.0


def get_information_from_dataset(va_id, ra_id= -1):
    '''
    Retrieves information about the data
    of a virtual author from the data set.

    In dependency of the real author ID, the information will be written to the
    real author holding this ID. If the real author ID should be the default
    '-1', a list with all the data will be returned.

    @param va_id: Virtual author ID to get the information from
    @type va_id: int
    @param ra_id: Real author ID to set information for.
    @type ra_id: int

    @return: True, if ra_id is set OR A list of the data
    @rtype: True if ra_id > -1 or list of strings
    '''
    va_data = get_virtualauthor_records(va_id)
    bibrec_id = ""

    for va_data_item in va_data:
        if va_data_item['tag'] == "bibrec_id":
            bibrec_id = va_data_item['value']
        elif va_data_item['tag'] == "orig_authorname_id":
            authorname_id = va_data_item['value']

    authorname_strings = get_name_and_db_name_strings(authorname_id)

    bconfig.LOGGER.info("| Reading info for va %s: %s recid %s"
                  % (va_id, authorname_strings["name"], bibrec_id))

    data = get_field_values_on_condition(
        bibrec_id, ['100', '700'], 'a', 'a',
        authorname_strings["db_name"], "!=")

    if ra_id > -1:
        formatted = "something"
        set_realauthor_data(ra_id, "module_tag", "module_value %s"
                            % (formatted))

        return True
    else:
        return data


def compare_va_to_ra(va_id, ra_id):
    '''
    Compares the data of a virtual author with all the data of
    a real author.

    @param va_id: Virtual author ID
    @type va_id: int
    @param ra_id: Real author ID
    @type ra_id: int

    @return: the probability of the virtual author belonging to the real author
    @rtype: float
    '''
    bconfig.LOGGER.info("|-> Start of data comparison (va %s : ra %s)"
                  % (va_id, ra_id))

    ra_data = get_realauthor_data(ra_id, "module_tag")
    va_data_set = get_information_from_dataset(va_id)

    if (len(ra_data) == 0) and (len(va_data_set) == 0):
        bconfig.LOGGER.info("|-> End of data comparison (Sets empty)")
        return 0

    parity = len(ra_data)

    # Your probability assessment function here:
    certainty = 1 - exp(-.8 * pow(len(parity), .7))

    bconfig.LOGGER.info("|--> Found %s matching information out of %s "
                        "on the paper. Result: %s%% similarity"
                        % (len(parity), len(va_data_set), certainty))

    return certainty
