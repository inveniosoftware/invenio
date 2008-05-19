# -*- coding: utf-8 -*-
## $Id$
##
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

from invenio.bibformat_engine import BibFormatObject
from invenio.search_engine import perform_request_search

CDS_Photo_URL = "http://cdsweb.cern.ch/search?cc=Press+Office+Photo+Selection&as=1&rg=1&of=xm"
Recursion_Upper_Limit = 10

def format(bfo):
    """
    """
    out = get_widget_HTML(bfo.lang, 1)
    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

def get_widget_HTML(language, number):
    """
    """
    # limit the recursion
    if int(number) > int(Recursion_Upper_Limit):
        return ""
    latest_photo_id = perform_request_search(cc='Press Office Photo Selection', rg=number, as=1, of='id') # todo: change cc='Press+Office+Photo+Selection'
    try:
        latest_photo_record = BibFormatObject(latest_photo_id[number - 1])
    except:
        # todo: Exception, no photo in this selection
        return ""
    recid = latest_photo_record.control_field("001")
    if language == "fr":
        try:
            title = latest_photo_record.fields('246_1a')[0]
        except KeyError:
            title = ""
    else:
        try:
            title = latest_photo_record.fields('245__a')[0]
        except KeyError:
            # todo: exception, picture with no title
            title = ""
    # first try to get the images from dfs, this should be the format they are in!
    icon_url = {}
    i = 1
    dfs_images = latest_photo_record.fields('8567_')
    for image_block in dfs_images:
        try:
            if image_block["y"] == "Icon":
                if image_block["u"][:7] == "http://":
                    if image_block["8"] != "":
                        icon_url[int(image_block["8"])] = image_block["u"]
                    else:
                        try:
                            icon_url[i] = image_block["u"]
                        except:
                            # icon could not be added
                            pass
        except:
            # probably some key error, thats ok
            pass
        i+=1
    # todo: does this return the first?
    try:
        icon_tuple = icon_url.popitem()
        icon_url = icon_tuple[1]
    except:
        # oh well, no dfs data... try to go for doc machine
        doc_machine_images = latest_photo_record.fields('8564_')
        # todo: implement parsing for external doc machine pages!
    html_out = ""
    if icon_url == "":
        html_out = get_widget_HTML("en", number+1)
    else:
        # assemble the HTML
        html_out = '<a href="%s" target="_blank"><img class="phr" width="100" height="67" alt="latest Photo" src="%s"/>%s</a>' % ("http://test-multimedia-gallery.web.cern.ch/test-multimedia-gallery/PhotoGallery_Detailed.aspx?searchTerm=recid:" + recid + "&page=1&order=1",
                                                                                                                  icon_url,
                                                                                                                  title)
#        <a title="link to cds or to a page of ours, similar to the gallery interface?" href="#">
#<img class="phr" width="100" height="67" alt="#" src="Objects/Home/PhotoWeek.jpg"/>
#Detail of the sensor from the first CMS half tracker inner barrel
#</a>
    return html_out
if __name__ == "__main__":
    get_widget_HTML("en", 1)
