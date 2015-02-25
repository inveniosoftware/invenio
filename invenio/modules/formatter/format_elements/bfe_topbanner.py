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

"""
BibFormat element - Prints HTML topbanner with category, rep. number, etc.
"""

__revision__ = "$Id$"

import cgi

def format_element(bfo, kb_name="dbcollid2coll"):
    """
    HTML top page banner containing category, rep. number, etc
    """
    collection_indicator = bfo.kb(kb_name, bfo.field("980__a"))
    collection_indicator = cgi.escape(collection_indicator)
    subject = bfo.field("65017a")
    subject = cgi.escape(subject)
    subject_2 = bfo.field("65027a")
    subject_2 = cgi.escape(subject_2)
    additional_report_numbers = bfo.fields("088__a")

    source_of_aquisition = bfo.field("037__a")
    source_of_aquisition = cgi.escape(source_of_aquisition)


    if subject:
        subject = " / " + subject

    if subject_2:
        subject_2 = " / " + subject_2

    if len(source_of_aquisition) > 0:
        source_of_aquisition = '<td align="right"><strong>'+ source_of_aquisition + "</strong></td>"

    report_numbers_out = ''
    for report_number in additional_report_numbers:
        report_numbers_out += "<td><small><strong>" + \
                              cgi.escape(report_number) + \
                              " </strong></small></td>"

    out = '''
    <table border="0" width="100%%">
      <tr>
        <td>%(collection_indicator)s<small>%(subject)s%(subject_2)s</small></td>
        <td><small><strong>%(report_number)s</strong></small></td>
        %(source_of_aquisition)s
      </tr>
    </table>
    ''' % {'collection_indicator': collection_indicator,
           'subject': subject,
           'subject_2': subject_2,
           'report_number': report_numbers_out,
           'source_of_aquisition': source_of_aquisition}

    if collection_indicator or \
           subject or \
           subject_2 or \
           source_of_aquisition or \
           report_numbers_out:
        return out
    else:
        return ''

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
