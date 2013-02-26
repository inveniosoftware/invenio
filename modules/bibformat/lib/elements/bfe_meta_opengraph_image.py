# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2013 CERN.
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

"""BibFormat element - return an image for the record"""

from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL, CFG_CERN_SITE
from invenio.bibdocfile import BibRecDocs, get_superformat_from_format
from invenio.config import CFG_WEBSEARCH_ENABLE_OPENGRAPH

def format_element(bfo, max_photos=''):
    """Return an image of the record, suitable for the Open Graph protocol.

    Will look for any icon stored with the record, and will fallback to any
    image file attached to the record. Returns nothing when no image is found.

    Some optional structured properties are not considered, for optimizing both generation of the page
    and page size.

    @param max_photos: the maximum number of photos to display
    """
    if not CFG_WEBSEARCH_ENABLE_OPENGRAPH:
        return ""
    bibarchive = BibRecDocs(bfo.recID)
    bibdocs = bibarchive.list_bibdocs()
    tags = []
    images = []

    if max_photos.isdigit():
        max_photos = int(max_photos)
    else:
        max_photos = len(bibdocs)

    for doc in bibdocs[:max_photos]:
        found_icons = []
        found_image_url = ''
        for docfile in doc.list_latest_files():
            if docfile.is_icon():
                found_icons.append((docfile.get_size(), docfile.get_url()))
            elif get_superformat_from_format(docfile.get_format()).lower() in [".jpg", ".gif", ".jpeg", ".png"]:
                found_image_url = docfile.get_url()
        found_icons.sort()

        for icon_size, icon_url in found_icons:
            images.append((icon_url, icon_url.replace(CFG_SITE_URL, CFG_SITE_SECURE_URL)))
        if found_image_url:
            images.append((found_image_url, found_image_url.replace(CFG_SITE_URL, CFG_SITE_SECURE_URL)))

    if CFG_CERN_SITE:
        # Add some more pictures from metadata
        additional_images = [(image_url, image_url.replace("http://mediaarchive.cern.ch/", "https://mediastream.cern.ch")) for image_url in bfo.fields("8567_u") if image_url.split('.')[-1] in ('jpg', 'png', 'jpeg', 'gif') and 'A5' in image_url]
        images.extend(additional_images)

    tags = ['<meta property="og:image" content="%s" />%s' % (image_url, image_url != image_secure_url and '\n<meta property="og:image:secure_url" content="%s" />' % image_secure_url or "") for image_url, image_secure_url in images]

    return "\n".join(tags)


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
