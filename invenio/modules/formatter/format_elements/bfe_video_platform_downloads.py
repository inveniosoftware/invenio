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
"""BibFormat element
* Part of the Video Platform Prototype
* Generates a list of links to download videos directly
* The list includes the codec/container, subformat/resolution and file size
"""

from invenio.legacy.bibdocfile.api import BibRecDocs

html_skeleton_popup = """<!-- DOWNLOAD POPUP -->
<div id="video_download_popup_box">
    %(elements)s
</div>
"""

html_skeleton_element = """<!-- DOWNLOAD POPUP ELEMENT -->
<div class="video_download_popup_element">
    <a href="%(video_url)s">
        <div class="video_download_popup_element_codec">
            %(video_codec)s
        </div>
        <div class="video_download_popup_element_filesize">
            %(video_size)s
        </div>
        <div class="video_download_popup_element_resolution">
            %(video_resolution)s
        </div>
    </a>
</div>
"""

def format_element(bfo):
    """Format Element Function"""
    return create_download_popup(bfo)

def create_download_popup(bfo):
    """Create the complete download popup"""
    elements = []
    recdoc = BibRecDocs(bfo.recID)
    bibdocs = recdoc.list_bibdocs()
    ## Go through all the BibDocs and search for video related signatures
    for bibdoc in bibdocs:
        bibdocfiles = bibdoc.list_all_files()
        for bibdocfile in bibdocfiles:
            ## When a video signature is found, add it as an element
            if bibdocfile.get_superformat() in ('.mp4', '.webm', '.ogv', 
                                                '.mov', '.wmv', '.avi', 
                                                '.mpeg', '.flv', '.mkv'):
                url = bibdocfile.get_url()
                codec = bibdocfile.get_superformat()[1:]
                resolution = bibdocfile.get_subformat()
                size = bibdocfile.get_size()
                elements.append(create_download_element(url, codec, 
                                                        size, resolution))
    if elements:
        return html_skeleton_popup % {
                    'elements': "\n".join(elements)
                    }
    else:
        return ""

def create_download_element(url, codec, size, resolution):
    """Creates an HTML element based on the element skeleton"""
    return html_skeleton_element % {
            'video_url': url + "&download=1",
            'video_codec': codec.upper(),
            'video_size': human_size(size),
            'video_resolution': resolution
            }

def human_size(byte_size):
    for x in ['bytes','KB','MB','GB','TB']:
        if byte_size < 1024.0:
            return "%3.1f %s" % (byte_size, x)
        byte_size /= 1024.0

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
