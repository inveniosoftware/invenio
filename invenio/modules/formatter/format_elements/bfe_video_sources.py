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
"""BibFormat element - Creates <source> elements for html5 videos
"""

from invenio.legacy.bibdocfile.api import BibRecDocs

def format_element(bfo, subformat="480p"):
    """ Creates HTML5 source elements for the given subformat. 
    
    MP4, WebM and OGV are currently supported as video sources.
    The function will scan the bibdocfiles attached to the record for
    videos with these formats and the fiven subformat.
    
    @param subformat: BibDocFile subformat to create the sources from (e.g. 480p)
    """
    video_sources = []
    recdoc = BibRecDocs(bfo.recID)
    bibdocs = recdoc.list_bibdocs()
    for bibdoc in bibdocs:
        bibdocfiles = bibdoc.list_all_files()
        for bibdocfile in bibdocfiles:
            if bibdocfile.get_superformat() in ('.mp4', '.webm', '.ogv') and bibdocfile.get_subformat() == subformat:
                src = bibdocfile.get_url()
                ftype = bibdocfile.get_superformat()[1:]
                if ftype == 'mp4':
                    codecs = 'avc1.42E01E, mp4a.40.2'
                elif ftype == 'webm':
                    codecs = 'vp8, vorbis'
                elif ftype == 'ogv':
                    codecs = 'theora, vorbis'
                source = '<source src=\"%s\" type=\'video/%s; codecs=\"%s\"\' />' % (src, ftype, codecs)
                video_sources.append(source)
    return "\n".join(video_sources)

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
