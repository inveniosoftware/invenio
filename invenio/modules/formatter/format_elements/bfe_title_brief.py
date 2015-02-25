# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints short title
"""
__revision__ = "$Id$"

def format_element(bfo, highlight="no", multilang='no'):
    """
    Prints a short title, suitable for brief format.

    @param highlight: highlights the words corresponding to search query if set to 'yes'
    """
    if multilang == 'yes':
        if bfo.lang == 'fr':
            title = bfo.field('246_1a')
        else:
            title = bfo.field('245__a')
    else:
        title = bfo.field('245__a')
    title_remainder = bfo.field('245__b')
    title_tome = bfo.field('245__n')
    title_part = bfo.field('245__p')
    edition_statement = bfo.field('250__a')

    out = title
    if len(title_remainder) > 0:
        out += ": " + title_remainder
    if len(edition_statement) > 0:
        out += "; " + edition_statement
    if len(title_tome) > 0:
        out += ", " + title_tome
    if len(title_part) > 0:
        out += ": " + title_part

    #Try to display 'Conference' title if other titles were not found
    if out == '':
        out += bfo.field('111__a')

    if highlight == 'yes':
        from invenio.modules.formatter import utils as bibformat_utils
        out = bibformat_utils.highlight(out, bfo.search_pattern,
                                        prefix_tag="<span style='font-weight: bolder'>",
                                        suffix_tag='</style>')

    return out

