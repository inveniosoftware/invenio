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

from invenio.file import *
from invenio.config import weburl
from cgi import escape

def format(bfo, style, separator='; '):
    """
    This is the default format for formatting full-text reference.
    @param separator the separator between urls.
    @param style CSS class of the link
    """

    urls = bfo.fields("8564_")

    ret = ""
    #ret += "%s<br />" % urls
    bibarchive = BibRecDocs(bfo.recID)
    old_version_there = False
    main_urls = {}
    others_urls = {}
    cern_urls = {}
    additionals = False

    for complete_url in urls:
        if complete_url.has_key('u'):
            url = complete_url['u']
            descr = ''
            #ret += "1 descr=%s<br />" % descr
            if complete_url.has_key('z'):
                #ret += "2 descr=%s<br />" % descr
                descr = complete_url['z']
                #ret += "3 descr=%s<br />" % descr
            elif complete_url.has_key('y'):
                #ret += "2 descr=%s<br />" % descr
                descr = complete_url['y']
                #ret += "3 descr=%s<br />" % descr
            #ret += "4 descr=%s<br />" % descr
            if not url.startswith(weburl):
                #ret += "%s doesn't start with %s<br />" % (url, weburl)
                #ret += "5 descr=%s<br />" % descr
                if not descr:
                    if '/setlink?' in url:
                        descr = "Fulltext"
                    else:
                    #ret += "6 descr=%s<br />" % descr
                        descr = url.split('/')[-1]
                    #ret += "7 descr=%s<br />" % descr
                #ret += "8 descr=%s<br />" % descr
                if 'cern.ch' in url:
                    cern_urls[url] = descr
                else:
                    others_urls[url] = descr

            else:
                #ret += "%s starts with %s!!!<br />" % (url, weburl)
                filename = url.split('/')[-1]
                name = file_strip_ext(filename)
                format = filename[len(name):]
                if format and format[0] == '.':
                    format = format[1:]
                #ret += "%s -> (%s, %s, %s)<br />" % (url, filename, name, format)

                assigned = False
                for doc in bibarchive.listBibDocs():

                    if int(doc.getLatestVersion()) > 1:
                        old_version_there = True
                    #ret += "Sto operando sul file %s" % doc
                    #ret += "%s<br />" % [f.fullname for f in doc.listAllFiles()]
                    if filename in [f.fullname for f in doc.listAllFiles()]:
                        assigned = True
                        #ret += " --> ok!!!<br />"
                        if not doc.type == 'Main':
                            additionals = True
                            #ret += "Additionals?!<br />"
                        else:
                            #ret += "Main!!!<br />"
                            #ret += "9 descr=%s<br />" % descr
                            if not descr:
                                #ret += "10 descr=%s<br />" % descr
                                descr = 'Main file(s)'
                                #ret += "11 descr=%s<br />" % descr
                            #ret += "12 descr=%s<br />" % descr
                            if not main_urls.has_key(descr):
                                main_urls[descr] = []
                            #ret += "Appendo a %s (%s, %s)<br />" % (descr, url, format)
                            main_urls[descr].append((url, name, format))
                if not assigned:
                    if not descr:
                        descr = url.split('/')[-1]
                    others_urls[url] = descr

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
        last_name = ""
        for descr, urls in main_urls.items():
            ret += "<strong>"+descr+":</strong> "
            url_list = []
            urls.sort(lambda (url1, name1, format1), (url2, name2, format2): url1 < url2 and -1 or url1 > url2 and 1 or 0)
            for url, name, format in urls:
                if not name == last_name and len(urls) > 1:
                    print_name = "<em>%s</em> - " % name
                else:
                    print_name = ""
                last_name = name
                url_list.append(print_name + '<a '+style+' href="'+escape(url)+'">'+format.upper()+'</a>')
            ret += separator.join(url_list) + additional_str + versions_str + '<br />'

    if cern_urls:
        ret += '<strong>CERN links</strong>: '
        url_list = []
        for url,descr in cern_urls.items():
            url_list.append('<a '+style+' href="'+escape(url)+'">'+escape(str(descr))+'</a>')
        ret += separator.join(url_list) + '<br />'

    if others_urls:
        ret += '<strong>External links</strong>: '
        url_list = []
        for url,descr in others_urls.items():
            url_list.append('<a '+style+' href="'+escape(url)+'">'+escape(str(descr))+'</a>')
        ret += separator.join(url_list) + '<br />'
    if ret.endswith('<br />'):
        ret = ret[:-len('<br />')]
    return ret

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
