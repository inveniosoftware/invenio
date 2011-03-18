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
bibauthorid_general_functions
    Provides the plug-in (module) functionality and handles the final chaining
    of the comparison functions in the modules which result in a final
    probability of a virtual author belonging to a real author entity.
"""

import glob
import os.path as osp
import sys

import bibauthorid_config as bconfig


def cmp_virtual_to_real_author(va_id, ra_id):
    """
    Chain function to compare a virtualauthor to a realauthor.
    Functions are specified in the config file and are chained
    and weighted as specified in the configfile.

    config file entry in format: function_name,[+|*],[0..1]
    the last two parameters are optional

    @param va_id: The ID of the virtual author
    @type va_id: in
    @param ra_id: The ID of the real author to compare to

    @return: The probability of the compatability of VA and RA
    @rtype: float
    """
    module = None
    module_paths = glob.glob(bconfig.MODULE_PATH)

    if not module_paths:
        bconfig.LOGGER.exception("Sorry, no modules found for comparison.")
        raise Exception('ModuleError')


    sum_count = 1.0
    sum_result = 0.0
    mult_result = 1.0
    decrease_sum_counter = -1
    comparison_result_str = "RA: %s" % (ra_id)

#    consideration_threshold = float(
#        get_config_parameter('CONSIDERATION_THRESHOLD')[0])

    consideration_threshold = bconfig.CONSIDERATION_THRESHOLD

    if consideration_threshold == "-1":
        return - 1

    for module_path in module_paths:
        module_id = osp.splitext(osp.basename(module_path))[0]
        module = None
        module_import_name = ("bibauthorid_comparison_functions.%s"
                              % (module_id))

        try:
            __import__(module_import_name)
            module = sys.modules[module_import_name]
        except ImportError, err:
            bconfig.LOGGER.exception("Error while importing %s" % (module_id))
            print err
            continue

        module_name = ""
        module_operator = ""
        module_weight = 0.0

        try:
            module_name = module.MODULE_NAME
        except AttributeError:
            module_name = "Default Module Name"

        try:
            module_operator = module.MODULE_OPERATOR
        except AttributeError:
            module_operator = "+"

        try:
            module_weight = module.MODULE_WEIGHT
        except AttributeError:
            module_weight = 1.0

#        comparison_result_str = "%s, %s:" % (comparison_result_str,
#                                                      module_name)
        chain_link_result = -1

        try:
            chain_link_result = module.compare_va_to_ra(va_id, ra_id)
        except AttributeError:
            bconfig.LOGGER.info("The module %s does not have a comparison"
                                " method. Please check your files!"
                                % (module_id))

        if chain_link_result >= consideration_threshold:
            if module_operator == '+':
                sum_count += 1
                sum_result += float(module_weight) * float(chain_link_result)
            elif module_operator == '*':
                mult_result *= float(module_weight) * float(chain_link_result)

        comparison_result_str = "%s %s %s %.2f*%.2f" % (comparison_result_str,
                                                   module_operator,
                                                   module_name,
                                                   float(module_weight),
                                                   float(chain_link_result))

    if sum_count == 0.0:
        sum_count = 1.0

    if sum_count > 2.0:
        sum_count = sum_count - 1

    if decrease_sum_counter > -1:
        sum_count -= decrease_sum_counter

    comparison_result = (sum_result / sum_count) * mult_result

    if comparison_result > 1.0:
        comparison_result = 1.0

    bconfig.LOGGER.log(25, "|--> Final comparison: [%s] => %s / %s = %s"
                  % (comparison_result_str, sum_count * comparison_result,
                     sum_count, comparison_result))

    return comparison_result
