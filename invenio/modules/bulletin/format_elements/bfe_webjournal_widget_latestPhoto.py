# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
WebJournal widget - display photos from given collections
"""
from invenio.modules.formatter.engine import BibFormatObject
from invenio.legacy.search_engine import perform_request_search
from invenio.config import CFG_CERN_SITE, CFG_SITE_URL, CFG_SITE_RECORD

def format_element(bfo, collections, max_photos="3", separator="<br/>"):
    """
    Display the latest pictures from the given collection(s)

    @param collections: comma-separated list of collection form which photos have to be fetched
    @param max_photos: maximum number of photos to display
    @param separator: separator between photos
    """
    try:
        int_max_photos = int(max_photos)
    except:
        int_max_photos = 0

    try:
        collections_list = [coll.strip() for coll in collections.split(',')]
    except:
        collections_list = []

    out = get_widget_html(bfo.lang, int_max_photos,
                          collections_list, separator, bfo.lang)
    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

def get_widget_html(language, max_photos, collections, separator, ln):
    """
    Returns the content of the widget
    """
    latest_photo_ids = perform_request_search(c=collections,
                                              rg=max_photos,
                                              of='id')
    images_urls = []
    for recid in latest_photo_ids[:max_photos]:
        try:
            photo_record = BibFormatObject(recid)
        except:
            # todo: Exception, no photo in this selection
            continue

        if language == "fr":
            try:
                title = photo_record.fields('246_1a', escape=1)[0]
            except KeyError:
                try:
                    title = photo_record.fields('245__a', escape=1)[0]
                except:
                    title = ""
        else:
            try:
                title = photo_record.fields('245__a', escape=1)[0]
            except KeyError:
                # todo: exception, picture with no title
                title = ""

        if CFG_CERN_SITE and photo_record.fields('8567_'):
            # Get from 8567_
            dfs_images = photo_record.fields('8567_')
            for image_block in dfs_images:
                if image_block.get("y", '') == "Icon":
                    if image_block.get("u", '').startswith("http://"):
                        images_urls.append((recid, image_block["u"], title))
                        break # Just one image per record

        else:
            # Get from 8564_
            images = photo_record.fields('8564_')
            for image_block in images:
                if image_block.get("x", '').lower() == "icon":
                    if image_block.get("q", '').startswith("http://"):
                        images_urls.append((recid, image_block["q"], title))
                        break # Just one image per record

    # Build output
    html_out = separator.join(['<a href="%s/%s/%i?ln=%s"><img class="phr" width="100" height="67" src="%s"/>%s</a>' % (CFG_SITE_URL, CFG_SITE_RECORD, recid, ln, photo_url, title) for (recid, photo_url, title) in images_urls])

    return html_out
