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
bibauthorid_module_paperequality
    Checks, if the respective virtual author appears on a paper that has
    already been handled and attached to a real author
'''
from bibauthorid_realauthor_utils import get_realauthor_data
from bibauthorid_virtualauthor_utils import get_virtualauthor_records
import bibauthorid_config as bconfig

# NAME: Defines the name of the module for display purposes. [A-Za-z0-9 \-_]
MODULE_NAME = "Paper Equality"
# OPERATOR: Defines the operator to use for the final computation [+|*]
MODULE_OPERATOR = "*"
# WEIGHT: Defines the weight of this module for the final computation [0..1]
MODULE_WEIGHT = 0.0


def compare_va_to_ra(va_id, ra_id):
    '''
    Compares the currently processed paper with the list of already attributed
    papers of the real author. Should the currently processed paper be
    amongst the list of papers of the real author, the returned value will be
    1--the highest probability. And 0 otherwise.

    Due to the configuration of this function in the configuration file,
    a parity of the papers will nullify the entire calculation.

    @param va_id: ID of the virtual author
    @type va_id: int
    @param ra_id: ID of the real author
    @type ra_id: int

    @return: The probability resulting from the paper equality comparison.
    @rtype: float
    '''
    va_records_raw = get_virtualauthor_records(va_id, "bibrec_id")
    ra_records_raw = get_realauthor_data(ra_id, "bibrec_id")
    paper_parity = 0
    va_records = []
    ra_records = []

    for i in va_records_raw:
        va_records.append(i['value'])

    for i in ra_records_raw:
        ra_records.append(i['value'])

    for va_record in va_records:
        if va_record in ra_records:
            paper_parity += 1

    if paper_parity > 0:
        bconfig.LOGGER.warn("|-> Paper parity detected"
                      + " -> Impossibility of author equality")
        return 1.0
    else:
        return 0.0
