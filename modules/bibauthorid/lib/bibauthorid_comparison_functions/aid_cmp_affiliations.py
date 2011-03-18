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
bibauthorid_module_affilations
    Meant for calculating probabilities of a virtual author and a real author
    being the same based on the affiliation and the date of the affiliation.
'''
from bibauthorid_realauthor_utils import get_realauthor_data
from bibauthorid_realauthor_utils import set_realauthor_data
from bibauthorid_utils import get_field_values_on_condition, str_to_int
from bibauthorid_virtualauthor_utils import get_virtualauthor_records
from bibauthorid_authorname_utils import get_name_and_db_name_strings
from math import exp
from datetime import date

import bibauthorid_config as bconfig

# NAME: Defines the name of the module for display purposes. [A-Za-z0-9 \-_]
MODULE_NAME = "Affiliation Comparison"
# OPERATOR: Defines the operator to use for the final computation [+|*]
MODULE_OPERATOR = "+"
# WEIGHT: Defines the weight of this module for the final computation [0..1]
MODULE_WEIGHT = 0.75


def get_information_from_dataset(va_id, ra_id= -1):
    '''
    Retrieves information about the affiliation of a virtual author
    from the data set.

    In dependency of the real author ID, the information will be written to the
    real author holding this ID. If the real author ID should be the default
    '-1', a list with all the affiliations will be returned.

    @param va_id: Virtual author ID to get the info from
    @type va_id: int
    @param ra_id: Real author ID to set information for.
    @type ra_id: int

    @return: A list of affiliations or simply True, if ra_id is set.
    @rtype: list of strings or True if ra_id > -1
    '''

    va_data = get_virtualauthor_records(va_id)
    authorname_id = -1
    bibrec_id = ""

    for va_data_item in va_data:
        if va_data_item['tag'] == "bibrec_id":
            bibrec_id = va_data_item['value']
        elif va_data_item['tag'] == "orig_authorname_id":
            authorname_id = va_data_item['value']

    authorname_strings = get_name_and_db_name_strings(authorname_id)
    bconfig.LOGGER.info("| Reading affiliations for va %s: %s  recid %s"
                  % (va_id, authorname_strings["name"], bibrec_id))
    affiliations = get_field_values_on_condition(
                                        bibrec_id, ['100', '700'], 'u', 'a',
                                        authorname_strings["db_name"])
    record_date = get_field_values_on_condition(bibrec_id, '269', 'c')
    constructed_date = []
    datearray = []

    if len(record_date) > 0:
        datearray = list(record_date)[0].split("-")
    else:
        datearray = ['0000', '00']

    length = len(datearray)

    if length == 3:
        datearray.pop()
        constructed_date = datearray
    elif length == 2:
        constructed_date = datearray
    else:
        constructed_date = datearray
        constructed_date += ['10']

    affiliation_date = "%s-%s" % (constructed_date[0], constructed_date[1])

    is_aff = False
    is_aff_date = False

    if not affiliations:
        bconfig.LOGGER.info("|-> No Affiliation for this record. Set to None")
        affiliations = ["None"]
    else:
        bconfig.LOGGER.info("|-> Affiliation found: %s" % (affiliations))
        is_aff = True

    if affiliation_date == "0000-00":
        bconfig.LOGGER.info("|-> No Affiliation Date set to 0000-00")
    else:
        bconfig.LOGGER.info("|-> Affiliation date: %s" % (affiliation_date))
        is_aff_date = True

    aff_collection = []

    if is_aff or is_aff_date:
        for affiliation in affiliations:
            bconfig.LOGGER.info("|--> Found Affiliation: %s;;%s;;%s"
                          % (affiliation_date, authorname_strings["name"],
                             affiliation))
            aff_collection.append("%s;;%s;;%s" % (affiliation_date,
                                                  authorname_strings["name"],
                                                  affiliation))

    if ra_id > -1:
        for affiliation in aff_collection:
            set_realauthor_data(ra_id, "affiliation", affiliation)

        return True
    else:
        return aff_collection


def compare_va_to_ra(va_id, ra_id):
    '''
    Compares the affiliation of a virtual author with all the affiliations of
    a real author.

    Distribution of probabilities for the time delta: e^(-0.05x^.7)
    Where x is the difference of the dates in month.

    @param va_id: Virtual author ID
    @type va_id: int
    @param ra_id: Real author ID
    @type ra_id: int

    @return: the probability of the virtual author belonging to the real author
    @rtype: float
    '''

    bconfig.LOGGER.info("|-> Start of affiliation comparison (va %s : ra %s)"
                  % (va_id, ra_id))

    ra_affiliation_data = get_realauthor_data(ra_id, "affiliation")
    va_affiliation_data = get_information_from_dataset(va_id)

    if (len(ra_affiliation_data) == 0) and (len(va_affiliation_data) == 0):
        bconfig.LOGGER.info("|-> End of affiliation comparison")
        return 0

    ra_dict = dict()
    va_dict = dict()

    for ra_affiliation in ra_affiliation_data:
        ra_data = ra_affiliation['value'].split(";;")

        if ra_dict.has_key(ra_data[2]):
            ra_dict[ra_data[2]] += [ra_data[0]]
        else:
            ra_dict[ra_data[2]] = [ra_data[0]]

    for va_affiliation in va_affiliation_data:
        va_data = va_affiliation.split(";;")
        if va_dict.has_key(va_data[2]):
            va_dict[va_data[2]] += [va_data[0]]
        else:
            va_dict[va_data[2]] = [va_data[0]]

    probability = 0.0
    aff_common = set(ra_dict.keys()).intersection(set(va_dict.keys()))

    aff_date_common = set([y for i in ra_dict.values()
                           for y in i]).intersection(set([x for j in
                                                          va_dict.values()
                                                          for x in j]))

    aff_p = []
    aff_date_p = [0]

    if len(aff_common) > 0:
        for aff in aff_common:
            if aff == "None":
                bconfig.LOGGER.info("|--> Only 'unknown' affiliation in common."
                              + " Doesn't help => skip.")
                aff_p.append(0)
            else:
                bconfig.LOGGER.info("|--> Nice: va in ra")
                aff_p.append(1)

                if len(aff_date_common) > 0:
                    bconfig.LOGGER.info("|---> Date Matches found: %s => "
                                        "Horray?! Dates: %s ... "
                                   % (len(aff_date_common), aff_date_common))

                for ra_date in ra_dict[aff]:
                    for va_date in va_dict[aff]:
                        rdate = ra_date.split("-")
                        vdate = va_date.split("-")

                        if not (rdate[0] == '0000' or vdate[0] == '0000'):
                            ryear = str_to_int(rdate[0])
                            rmonth = str_to_int(rdate[1])
                            vyear = str_to_int(vdate[0])
                            vmonth = str_to_int(vdate[1])

                            if rmonth == 0:
                                rmonth = 10

                            if vmonth == 0:
                                vmonth = 10

                            time_delta = (date(ryear, rmonth, 1) -
                                          date(vyear, vmonth, 1))
                            date_delta = abs(time_delta.days / 30)

                            if date_delta <= 600:
                                if ((len(aff_date_p) == 1)
                                    and (aff_date_p[0] == 0)):
                                    aff_date_p.pop()

                                result = exp(-.05 * pow(date_delta, .7))
                                bconfig.LOGGER.debug("|---> Delta: %s => "
                                                     "Result: %s"
                                                     % (date_delta, result))
                                aff_date_p.append(result)

                            else:
                                bconfig.LOGGER.debug("|---> Date delta "
                                                     "too high.")
                                aff_date_p.append(0)
                        else:
                            bconfig.LOGGER.debug("|---> Date delta not "
                                                 "computable")

#        probability = average(aff_p) + average(aff_date_p)
        probability = ((float(sum(aff_p)) / len (aff_p))
                       + (float(sum(aff_date_p)) / len (aff_date_p)))
    else:
        bconfig.LOGGER.info("|--> No affiliation in common.")
        probability = 0

    bconfig.LOGGER.info("|--> Affiliation comparison result: %s"
                  % (probability / 2))
    bconfig.LOGGER.info("|-> End of affiliation comparison")

    return probability / 2
