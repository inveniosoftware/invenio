# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Print photos of the record (if bibdoc file)
"""

import cgi
from invenio.bibdocfile import BibRecDocs
from invenio.urlutils import create_html_link

def format_element(bfo, separator=" ", style='', img_style='', text_style='font-size:small',
                   print_links='yes', max_photos='', show_comment='yes',
                   img_max_width='250px', display_all_version_links='yes'):
    """
    Lists the photos of a record. Display the icon version, linked to
    its original version.

    This element works for photos appended to a record as BibDoc
    files, for which a preview icon has been generated. If there are
    several formats for one photo, use the first one found.

    @param separator: separator between each photo
    @param print_links: if 'yes', print links to the original photo
    @param style: style attributes of the whole image block. Eg: "padding:2px;border:1px"
    @param img_style: style attributes of the images. Eg: "width:50px;border:none"
    @param text_style: style attributes of the text. Eg: "font-size:small"
    @param max_photos: the maximum number of photos to display
    @param show_comment: if 'yes', display the comment of each photo
    @param display_all_version_links: if 'yes', print links to additional (sub)formats
    """
    photos = []
    bibarchive = BibRecDocs(bfo.recID)
    bibdocs = bibarchive.list_bibdocs()

    if max_photos.isdigit():
        max_photos = int(max_photos)
    else:
        max_photos = len(bibdocs)

    for doc in bibdocs[:max_photos]:
        found_icons = []
        found_url = ''
        for docfile in doc.list_latest_files():
            if docfile.is_icon():
                found_icons.append((docfile.get_size(), docfile.get_url()))
            else:
                found_url = docfile.get_url()
        found_icons.sort()

        if found_icons:
            additional_links = ''
            name = bibarchive.get_docname(doc.id)
            comment = doc.list_latest_files()[0].get_comment()

            preview_url = None
            if len(found_icons) > 1:
                preview_url = found_icons[1][1]
                additional_urls = [(docfile.get_size(), docfile.get_url(), \
                                    docfile.get_superformat(), docfile.get_subformat()) \
                                   for docfile in doc.list_latest_files() if not docfile.is_icon()]
                additional_urls.sort()
                additional_links = [create_html_link(url, urlargd={}, \
                                                     linkattrd={'style': 'font-size:x-small'}, \
                                                     link_label="%s %s (%s)" % (format.strip('.').upper(), subformat, format_size(size))) \
                                    for (size, url, format, subformat) in additional_urls]
            img = '<img src="%(icon_url)s" alt="%(name)s" style="max-width:%(img_max_width)s;_width:%(img_max_width)s;%(img_style)s" />' % \
                  {'icon_url': cgi.escape(found_icons[0][1], True),
                   'name': cgi.escape(name, True),
                   'img_style': img_style,
                   'img_max_width': img_max_width}

            if print_links.lower() == 'yes':
                img = '<a href="%s">%s</a>' % (cgi.escape(preview_url or found_url, True), img)
            if display_all_version_links.lower() == 'yes' and additional_links:
                img += '<br />' + '&nbsp;'.join(additional_links) + '<br />'

            if show_comment.lower() == 'yes' and comment:
                img += '<div style="margin-auto;text-align:center;%(text_style)s">%(comment)s</div>' % \
                       {'comment': comment.replace('\n', '<br/>'),
                        'text_style': text_style}
            img = '<div style="vertical-align: middle;text-align:center;display:inline-block;display: -moz-inline-stack;zoom: 1;*display: inline;max-width:%(img_max_width)s;_width:%(img_max_width)s;text-align:center;%(style)s">%(img)s</div>' % \
                  {'img_max_width': img_max_width,
                   'style': style,
                   'img': img}

            photos.append(img)

    return '<div>' + separator.join(photos) + '</div>'

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0


def format_size(size):
    """
    Get human-readable string for the given size in Bytes
    """
    if size < 1024:
        return "%d byte%s" % (size, size != 1 and 's' or '')
    elif size < 1024 * 1024:
        return "%.1f KB" % (size / 1024)
    elif size < 1024 * 1024 * 1024:
        return "%.1f MB" % (size / (1024 * 1024))
    else:
        return "%.1f GB" % (size / (1024 * 1024 * 1024))
