# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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
"""BibFormat element - OAI ready MARCXML

This element return the full MARCXML representation of a record with the marc
prefix and namespace and adding the leader.
"""

from invenio.modules.formatter.api import get_preformatted_record

def format_element(bfo):
    """
    Return the MARCXML representation of the record with the marc prefix and
    namespace and adding the leader.
    """
    formatted_record = get_preformatted_record(bfo.recID, 'xm')
    formatted_record = formatted_record.replace("<record>", "<marc:record xmlns:marc=\"http://www.loc.gov/MARC21/slim\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd\" type=\"Bibliographic\">\n     <marc:leader>00000coc  2200000uu 4500</marc:leader>")
    formatted_record = formatted_record.replace("<record xmlns=\"http://www.loc.gov/MARC21/slim\">", "<marc:record xmlns:marc=\"http://www.loc.gov/MARC21/slim\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd\" type=\"Bibliographic\">\n     <marc:leader>00000coc  2200000uu 4500</marc:leader>")
    formatted_record = formatted_record.replace("</record", "</marc:record")
    formatted_record = formatted_record.replace("<controlfield", "<marc:controlfield")
    formatted_record = formatted_record.replace("</controlfield", "</marc:controlfield")
    formatted_record = formatted_record.replace("<datafield", "<marc:datafield")
    formatted_record = formatted_record.replace("</datafield", "</marc:datafield")
    formatted_record = formatted_record.replace("<subfield", "<marc:subfield")
    formatted_record = formatted_record.replace("</subfield", "</marc:subfield")
    return formatted_record

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
