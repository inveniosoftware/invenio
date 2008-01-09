# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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
"""BibFormat element - Prints a links to fulltext
"""
__revision__ = "$Id$"

from invenio.bibformat_elements.bfe_fulltext import getFiles
from invenio.config import weburl, CFG_CERN_SITE
from cgi import escape

def format(bfo, style, separator='; ', show_icons='no'):
    """
    This is the format for formatting fulltext links in the mini panel.
    @param separator the separator between urls.
    @param style CSS class of the link
    @param show_icons if 'yes', print icons for fulltexts
    """
    out = ''

    # Retrieve files
    (parsed_urls, old_versions, additionals) = getFiles(bfo)

    main_urls = parsed_urls['main_urls']
    others_urls = parsed_urls['others_urls']
    if parsed_urls.has_key('cern_urls'):
        cern_urls = parsed_urls['cern_urls']

    # Prepare style
    if style != "":
        style = 'class="'+style+'"'

    # Build urls list.
    # Escape special chars for <a> tag value.

    additional_str = ''
    if additionals:
        additional_str = separator + '<small>(<a '+style+' href="'+weburl+'/record/'+str(bfo.recID)+'/files/">additional files</a>)</small>'

    versions_str = ''
    if old_versions:
        versions_str = separator + '<small>(<a '+style+' href="'+weburl+'/record/'+str(bfo.recID)+'/files/">older versions</a>)</small>'

    if main_urls:
        # Put a big file icon if only one file
        if len(main_urls.keys()) == 1 and len(main_urls.items()[0][1]) == 1 and \
               (not CFG_CERN_SITE or len(cern_urls) == 0) and len(others_urls.keys()) == 0 and \
               show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-34x48.gif" alt="Download fulltext" /><br />' % weburl

        elif show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-12x16.gif" alt="Download fulltext"/>' % weburl
        else:
            file_icon = ''

        last_name = ""
        for descr, urls in main_urls.items():
            out += '<small class="detailedRecordActions">%s:</small> ' % descr
            url_list = []
            urls.sort(lambda (url1, name1, format1), (url2, name2, format2): url1 < url2 and -1 or url1 > url2 and 1 or 0)

            for url, name, format in urls:
                if not name == last_name and len(main_urls) > 1:
                    print_name = "<em>%s</em> - " % name
                else:
                    print_name = ""
                last_name = name
                url_list.append(print_name + '<a '+style+' href="'+escape(url)+'">'+file_icon+format.upper()+'</a>')
            out += separator + separator.join(url_list) + \
                   additional_str + versions_str + '</div>'

    if CFG_CERN_SITE and cern_urls:
        # Put a big file icon if only one file
        if len(main_urls.keys()) == 0 and \
               len(cern_urls) == 1 and len(others_urls) == 0 and \
               show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-34x48.gif" alt="Download fulltext" /><br />' % weburl

        elif show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-12x16.gif" alt="Download fulltext"/>' % weburl
        else:
            file_icon = ''

        link_word = len(cern_urls) == 1 and 'link' or 'links'
        out += '<small class="detailedRecordActions">(CERN %s)</small><br />' % link_word
        url_list = []
        for url, descr in cern_urls:
            url_list.append('<a '+style+' href="'+escape(url)+'">'+file_icon+escape(str(descr))+'</a>')
        out += separator.join(url_list)

    if others_urls:
        # Put a big file icon if only one file
        if len(main_urls.keys()) == 0 and \
               (not CFG_CERN_SITE or len(cern_urls) == 0) and len(others_urls) == 1 and \
               show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-34x48.gif" alt="Download fulltext" /><br />' % weburl
        elif show_icons.lower() == 'yes':
            file_icon = '<img style="border:none" src="%s/img/file-icon-text-12x16.gif" alt="Download fulltext"/>' % weburl
        else:
            file_icon = ''
        link_word = len(others_urls) == 1 and 'link' or 'links'
        out += '<small class="detailedRecordActions">(external %s)</small>%s' % (link_word, separator)
        url_list = []
        for url, descr in others_urls:
            url_list.append('<a '+style+' href="'+escape(url)+'">'+file_icon+escape(str(descr))+'</a>')
        out += '<small>' + separator.join(url_list) + '</small>'
    if out.endswith('<br />'):
        out = out[:-len('<br />')]

    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
