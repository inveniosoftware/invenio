# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2014, 2015 CERN.
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

"""BibFormat element - Prints record as XML."""


def format_element(bfo, type='xm', encodeForXML='yes'):
    """Print the complete current record as XML.

    :param type: the type of xml. Can be 'xml', 'oai_dc', 'marcxml', 'xd'
    :param encodeForXML: if 'yes', replace all < > and & with html
        corresponding escaped characters.
    """
    assert type == 'xm'
    from invenio.modules.records.api import get_record
    from invenio.utils.text import encode_for_xml

    out = get_record(bfo.recID).legacy_export_as_marc()

    if encodeForXML.lower() == 'yes':
        return encode_for_xml(out)
    else:
        return out


def escape_values(bfo):
    """Check if output of this element should be escaped."""
    return 0
