# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2015 CERN.
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
BibFormat element - Prints editors

"""


def format_element(bfo, limit, separator=' ; ',
                   extension='[...]', print_links="yes"):
    """
    Prints the list of editors of a record.

    @param limit: the maximum number of editors to display
    @param separator: the separator between editors.
    @param extension: a text printed if more editors than 'limit' exist
    @param print_links: if yes, print the editors as HTML link
           to their publications
    """
    from urllib import quote
    from invenio.config import CFG_BASE_URL
    from invenio.bibrecord import field_get_subfield_values, \
        record_get_field_instances

    authors = record_get_field_instances(bfo.get_record(), '100') + \
        record_get_field_instances(bfo.get_record(), '700')
    editors = [field_get_subfield_values(author, 'a')[0]
               for author in authors
               if len(field_get_subfield_values(author, "e")) > 0
               and field_get_subfield_values(author, "e")[0] == "ed."]

    if print_links.lower() == "yes":
        editors = ['<a href="%s/search?f=author&amp;p=%s&amp;ln=%s">%s</a>'
                   % (CFG_BASE_URL, quote(editor), bfo.lang, editor)
                   for editor in editors]

    if limit.isdigit() and len(editors) > int(limit):
        return separator.join(editors[:int(limit)]) + extension

    elif len(editors) > 0:
        return separator.join(editors)
