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
* Part of the video platform prototype
* Creates a <select> element with <option> elements
  containing various information about video sources. The options are later
  evaluated by javascript and the video source is dynamically injected in the
  HTML5 video element.
* Based on bfe_video_selector.py
"""

from six import iteritems
from invenio.legacy.bibdocfile.api import BibRecDocs

def format_element(bfo):
    """ Format element function to create the select and option elements
    with HTML5 data attributes that store all the necesarry metadata to
    construct video sources with JavaScript."""
    videos = {
             '360p': {'width': 640, 'height': 360, 'poster': None, 'mp4': None, 'webm': None, 'ogv': None},
             '480p': {'width': 854,'height': 480, 'poster': None, 'mp4': None, 'webm': None, 'ogv': None,},
             '720p': {'width': 1280, 'height': 720, 'poster': None, 'mp4': None, 'webm': None, 'ogv': None},
             '1080p': {'width': 1920, 'height': 1080, 'poster': None, 'mp4': None, 'webm': None, 'ogv': None}
             }
    recdoc = BibRecDocs(bfo.recID)
    bibdocs = recdoc.list_bibdocs()
    ## Go through all the BibDocs and search for video related signatures
    for bibdoc in bibdocs:
        bibdocfiles = bibdoc.list_all_files()
        for bibdocfile in bibdocfiles:
            ## When a video signature is found, add the url to the videos dictionary
            if bibdocfile.get_superformat() in ('.mp4', '.webm', '.ogv') and bibdocfile.get_subformat() in ('360p', '480p', '720p', '1080p'):
                src = bibdocfile.get_url()
                codec = bibdocfile.get_superformat()[1:]
                size = bibdocfile.get_subformat()
                videos[size][codec] = src
            ## When a poster signature is found, add the url to the videos dictionary
            elif bibdocfile.get_comment() in ('SUGGESTIONTUMB', 'BIGTHUMB', 'POSTER', 'SMALLTHUMB') and bibdocfile.get_subformat() in ('360p', '480p', '720p', '1080p'):
                src = bibdocfile.get_url()
                size = bibdocfile.get_subformat()
                videos[size]['poster'] = src
    ## Build video select options for every video size format that was found
    select_options = []
    for key, options in iteritems(videos):
        ## If we have at least one url, the format is available
        if options['mp4'] or options['webm'] or options['ogv']:
            ## create am option element
            option_element = create_option_element(url_webm=options['webm'], url_ogv=options['ogv'], url_mp4=options['mp4'],
                                                   url_poster=options['poster'], width=options['width'], height=options['height'],
                                                   subformat=key)
            select_options.append(option_element)
    select_element = create_select_element(select_options)
    return select_element

def create_select_element(options):
    """ Creates the HTML select element that carries the video format options
    """
    text = """<select id="mejs-resolution">
              %s
              </select>
           """ % '\n'.join(options)
    return text


def create_option_element(width, height, subformat, url_webm=None, url_ogv=None, url_mp4=None, url_poster=None,):
    """ Creates an HTML option element that carries all video information
    """
    if url_webm:
        webm = """data-src-webm="%s" data-type-webm='video/webm; codecs="vp8, vorbis"'""" % url_webm
    else:
        webm = ""
    if url_ogv:
        ogv = """data-src-ogg="%s" data-type-ogv='video/ogv; codecs="theora, vorbis"'""" % url_ogv
    else:
        ogv = ""
    if url_mp4:
        mp4 = """data-src-mp4="%s" data-type-mp4='video/mp4; codecs="avc1.42E01E, mp4a.40.2"'""" % url_mp4
    else:
        mp4 = ""
    text = """<option %(webm)s %(ogv)s %(mp4)s data-poster="%(url_poster)s" data-video-width="%(width)spx" data-video-height="%(height)spx">%(subformat)s</option>""" % {
               'webm': webm,
               'ogv': ogv,
               'mp4': mp4,
               'url_poster': url_poster,
               'width': width,
               'height': height,
               'subformat': subformat
               }
    return text

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
