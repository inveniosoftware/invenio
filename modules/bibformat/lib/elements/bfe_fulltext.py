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

from invenio.file import BibRecDocs, file_strip_ext
from invenio.config import weburl, CFG_CERN_SITE
from cgi import escape
from urlparse import urlparse
from os.path import basename, splitext

def format(bfo, style, separator='; ', show_icons='no'):
    """
    This is the default format for formatting full-text reference.
    @param separator the separator between urls.
    @param style CSS class of the link
    @param show_icons if 'yes', print icons for fulltexts
    """

    urls = bfo.fields("8564_")

    ret = ""
    bibarchive = BibRecDocs(bfo.recID)
    old_version_there = False
    main_urls = {} # Urls hosted by Invenio (bibdocs)
    others_urls = {} # External urls
    if CFG_CERN_SITE:
        cern_urls = {} # cern.ch urls
    additionals = False

    for complete_url in urls:
        if complete_url.has_key('u'):
            url = complete_url['u']
            (dontcare, host, path, dontcare, dontcare, dontcare) = urlparse(url)
            filename = basename(path)
            name = file_strip_ext(filename)
            format = filename[len(name):]
            if format.startswith('.'):
                format = format[1:]

            descr = ''
            if complete_url.has_key('z'): # Let's take the description
                descr = complete_url['z']
            elif complete_url.has_key('y'):
                descr = complete_url['y']
            if not url.startswith(weburl): # Not a bibdoc?
                if not descr: # For not bibdoc let's have a description
                    if '/setlink?' in url: # Setlink (i.e. hosted on doc.cern.ch)
                        descr = "Fulltext" # Surely a fulltext
                    else:
                        #FIXME remove eventual ?parameters
                        descr = filename or host # Let's take the name from the url
                if CFG_CERN_SITE and 'cern.ch' in host:
                    cern_urls[url] = descr # Obsolete cern.ch url (we're migrating)
                else:
                    others_urls[url] = descr # external url
            else: # It's a bibdoc!
                assigned = False
                for doc in bibarchive.listBibDocs():
                    if int(doc.getLatestVersion()) > 1:
                        old_version_there = True
                    if filename in [f.fullname for f in doc.listAllFiles()]:
                        assigned = True
                        if not doc.type == 'Main':
                            additionals = True
                        else:
                            if not descr:
                                descr = 'Main file(s)'
                            if not main_urls.has_key(descr):
                                main_urls[descr] = []
                            main_urls[descr].append((url, name, format))
                if not assigned: # Url is not a bibdoc :-S
                    if not descr:
                        descr = filename
                    others_urls[url] = descr # Let's put it in a general other url

    if style != "":
        style = 'class="'+style+'"'

    # Build urls list.
    # Escape special chars for <a> tag value.

    additional_str = ''
    if additionals:
        additional_str = ' <small>(<a '+style+' href="'+weburl+'/record/'+str(bfo.recID)+'/files/">additional files</a>)</small>'

    versions_str = ''
    if old_version_there:
        versions_str = ' <small>(<a '+style+' href="'+weburl+'/record/'+str(bfo.recID)+'/files/">older versions</a>)</small>'

    if main_urls:
        # Put a big file icon if only one file
        if len(main_urls) == 1 and len(main_urls[0][1]) == 1 and \
               (not CFG_CERN_SITE or len(cern_urls) == 0) and len(others_urls) == 0 and \
               show_icons.lower() == 'yes':
            file_icon = '<img src="%s/img/file-icon-text-96x128.gif" alt="Download fulltext" height="64px"/><br />' % weburl
        elif show_icons.lower() == 'yes':
            file_icon = '<img src="%s/img/file-icon-text-15x20.gif" alt="Download fulltext"/>' % weburl
        else:
            file_icon = ''
            
        last_name = ""
        for descr, urls in main_urls.items():
            ret += "<small>%s:</small> " % descr
            url_list = []
            urls.sort(lambda (url1, name1, format1), (url2, name2, format2): url1 < url2 and -1 or url1 > url2 and 1 or 0)

            for url, name, format in urls:
                if not name == last_name and len(main_urls) > 1:
                    print_name = "<em>%s</em> - " % name
                else:
                    print_name = ""
                last_name = name
                url_list.append(print_name + '<a '+style+' href="'+escape(url)+'">'+file_icon+format.upper()+'</a>')
            ret += separator.join(url_list) + additional_str + versions_str + '<br />'

    if CFG_CERN_SITE and cern_urls:
        # Put a big file icon if only one file
        if len(main_urls) == 0 and \
               len(cern_urls) == 1 and len(others_urls) == 0 and \
               show_icons.lower() == 'yes': 
            file_icon = '<img src="%s/img/file-icon-text-96x128.gif" alt="Download fulltext" height="64px"/><br />' % weburl
        elif show_icons.lower() == 'yes':
            file_icon = '<img src="%s/img/file-icon-text-15x20.gif" alt="Download fulltext"/>' % weburl
        else:
            file_icon = ''
            
        link_word = len(cern_urls) == 1 and 'link' or 'links'
        ret += '<small>(CERN %s)</small><br />' % link_word
        url_list = []
        for url,descr in cern_urls.items():
            url_list.append('<a '+style+' href="'+escape(url)+'">'+file_icon+escape(str(descr))+'</a>')
        ret += separator.join(url_list) + '<br />'

    if others_urls:
        # Put a big file icon if only one file
        if len(main_urls) == 0 and \
               (not CFG_CERN_SITE or len(cern_urls) == 0) and len(others_urls) == 1 and \
               show_icons.lower() == 'yes':
            file_icon = '<img src="%s/img/file-icon-text-96x128.gif" alt="Download fulltext" height="64px"/><br />' % weburl
        elif show_icons.lower() == 'yes':
            file_icon = '<img src="%s/img/file-icon-text-15x20.gif" alt="Download fulltext"/>' % weburl
        else:
            file_icon = ''
        link_word = len(others_urls) == 1 and 'link' or 'links'
        ret += '<small>(external %s)</small>:<br/>' % link_word
        url_list = []
        for url,descr in others_urls.items():
            url_list.append('<a '+style+' href="'+escape(url)+'">'+file_icon+escape(str(descr))+'</a>')
        ret += '<small>' + separator.join(url_list) + '</small><br />'
    if ret.endswith('<br />'):
        ret = ret[:-len('<br />')]

    if ret == '' and show_icons.lower() == 'yes':
        ret += '<img src="%s/img/file-icon-none-96x128.gif" alt="Download fulltext" height="64px"/><br /><span style="color:#aaa">No fulltext</span>' % weburl
        
    return ret

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
