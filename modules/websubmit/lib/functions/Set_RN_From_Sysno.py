## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""WebSubmit function - Set the global variable 'rn' to the report
                        number of the record identified by sysno
"""
import os
from invenio.search_engine import get_fieldvalues

# Where to look for report numbers (in this order)
CFG_DEFAULT_RN_TAGS = ['037__a', '088__a', '021__a']

def Set_RN_From_Sysno(parameters, curdir, form, user_info=None):
    """
    Set the global variable 'rn' to the report number of the record
    identified by 'sysno' (recid) global variable.

    Useful at MBI step when the user specifies the record to modify
    using the recid instead of the report number.  Since most
    WebSubmit functions relies on the global 'rn' variable, it is
    necessary in these cases to include this function.

    This function MUST be preceded by 'Get_Recid' function.

    To identify the record to update via 'recid' instead of report
    number, one MUST on the MBI form request the recid/sysno using a
    form element named 'SN'.

    Parameters:

         edsrn - file where to write the report number if found

      rep_tags - comma-separater list of tags where the report number
                 can be found. Default is '037__a', '088__a', '021__a'
                 if no value is specified.
    """
    global rn, sysno
    if not sysno:
        return

    rn_tags = [tag.strip() for tag in parameters['rep_tags'].split(',') \
               if tag.strip()]
    if not rn_tags:
        rn_tags  = CFG_DEFAULT_RN_TAGS

    # Retrieve report number
    for rn_tag in rn_tags:
        possible_report_numbers = get_fieldvalues(sysno, rn_tag)
        if possible_report_numbers:
            rn = possible_report_numbers[0].strip()
            break

    edsrn = parameters['edsrn']
    path_to_repnum_file = os.path.join(curdir, edsrn)

    if rn and not os.path.exists(path_to_repnum_file) and \
           os.path.abspath(path_to_repnum_file).startswith(curdir):
        # Write report number to specified file
        fp = open(path_to_repnum_file, 'w')
        fp.write(rn)
        fp.close()
