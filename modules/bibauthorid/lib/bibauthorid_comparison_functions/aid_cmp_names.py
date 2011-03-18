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
"""
bibauthorid_module_names
    Module for the bibauthorid framwork to compare name strings of
    virtual and real author entities.
"""
from bibauthorid_authorname_utils import compare_names
from bibauthorid_realauthor_utils import get_realauthor_names_from_set
from bibauthorid_virtualauthor_utils import get_virtualauthor_records
from bibauthorid_authorname_utils import get_name_and_db_name_strings

import bibauthorid_config as bconfig

# NAME: Defines the name of the module for display purposes. [A-Za-z0-9 \-_]
MODULE_NAME = "Name Comparison"
# OPERATOR: Defines the operator to use for the final computation [+|*]
MODULE_OPERATOR = "+"
# WEIGHT: Defines the weight of this module for the final computation [0..1]
MODULE_WEIGHT = 1.0


def compare_va_to_ra(va_id, ra_id):
    '''
    Compares the origin names of a virtual author against the name list of
    a real author

    @param va_id: ID of the virtual author
    @type va_id: int
    @param ra_id: ID of the real author
    @type ra_id: int

    @return: The probability resulting from the name comparison.
    @rtype: float
    '''

    bconfig.LOGGER.info("|-> Start of name comparison (va %s : ra %s)"
                  % (va_id, ra_id))

    ra_names = get_realauthor_names_from_set(ra_id)
    va_nameid_recs = get_virtualauthor_records(va_id, tag='orig_authorname_id')
#    print "RA Names: ", ra_names
#    print "VA Name: ", va_name

    authorname_id = -1
    if va_nameid_recs:
        authorname_id = va_nameid_recs[0]['value']

    authorname_strings = get_name_and_db_name_strings(authorname_id)

    if not authorname_strings["name"]:
        return 0.0

    comparisons = []

    for ra_name in ra_names:
        comparison = compare_names(authorname_strings["name"], ra_name)
        bconfig.LOGGER.info("|-> %s & %s -> %s"
                            % (authorname_strings["name"],
                               ra_name, comparison))
        comparisons.append(comparison)

    #print "checking ",name_1," against ", name_2

    bconfig.LOGGER.debug("|--> Name comparisons: %s" % (comparisons))
    bconfig.LOGGER.info("|-> End of name comparison")

#    ret = average(comparisons)
    ret = float(sum(comparisons)) / len(comparisons)

    if ret < .1:
        ret = 0 #.1

    bconfig.LOGGER.info("|--> Resulting name probability: %s" % (ret))

    return ret


#def name_list_comparison(vaID1,vaID2):
#    """
#    Compares the list of names connected to two virtual authors
#    """
#
#    name_list_1 = bibauthorid_virtualauthor_utils.get_virtualauthor_target_names_string_p(vaID1)
#    name_list_2 = bibauthorid_virtualauthor_utils.get_virtualauthor_target_names_string_p(vaID2)
#
#    names_compat = 0
#    equal_names_count = 0
#    len_name_list_1 = len(name_list_1)
#    len_name_list_2 = len(name_list_2)
#
#    for  i in name_list_1:
#        for j in name_list_2:
#            if i[0]==j[0]:
#                names_compat += (1-abs(i[1]-j[1]))
#                equal_names_count += 1
#                name_list_2.remove(j)
#                break
#
#    if equal_names_count!=0:
#        names_compat = names_compat/float(equal_names_count)
#    else:
#        names_compat = 1
#
#    return names_compat * (1 - ((max(len_name_list_1, len_name_list_2) - equal_names_count) / max(len_name_list_1, len_name_list_2)))
