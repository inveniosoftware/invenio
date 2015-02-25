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
WebJournal widget - Display Indico seminars
"""
from invenio.config import CFG_CACHEDIR, CFG_SITE_LANG
from xml.dom import minidom
from invenio.utils.url import create_Indico_request_url, make_invenio_opener
import time
import base64
import socket

from invenio.legacy.webjournal.utils import \
     parse_url_string, WEBJOURNAL_OPENER
from invenio.base.i18n import gettext_set_language

update_frequency = 3600 # in seconds

def format_element(bfo, indico_baseurl="https://indico.cern.ch", indico_what='categ', indico_loc="", indico_id="1l7", indico_key="", indico_sig="", indico_onlypublic='yes', indico_from="today", indico_to='today', indico_credential_path=""):
    """
    Display the list of seminar from the given Indico instance

    See Indico HTTP Export APIs:
    http://indico.cern.ch/ihelp/html/ExportAPI/index.html

    @param indico_baseurl: Indico base URL from which to retrieve information
    @param indico_what: element to export
    @type indico_what: one of the strings: C{categ}, C{event}, C{room}, C{reservation}
    @param indico_loc: location of the element(s) specified by ID (only used for some elements)
    @param indico_id: ID of the element to be exported
    @type indico_id: a string or a list/tuple of strings
    @param indico_type: output format
    @type indico_type: one of the strings: C{json}, C{jsonp}, C{xml}, C{html}, C{ics}, C{atom}
    @param indico_params: parameters of the query. See U{http://indico.cern.ch/ihelp/html/ExportAPI/common.html}
    @param indico_key: API key provided for the given Indico instance
    @param indico_sig: API secret key (signature) provided for the given Indico instance
    @param indico_credential_path: if provided, load 'indico_key' and 'indico_sig' from this path
    """
    args = parse_url_string(bfo.user_info['uri'])
    journal_name = args["journal_name"]
    cached_filename = "webjournal_widget_seminars_%s.xml" % journal_name
    out = get_widget_html(bfo, indico_baseurl, indico_what, indico_loc, indico_id,
                          indico_onlypublic, indico_from, indico_to,
                          indico_key, indico_sig, indico_credential_path,
                          cached_filename, bfo.lang)
    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

def get_widget_html(bfo, indico_baseurl, indico_what, indico_loc, indico_id,
                    indico_onlypublic, indico_from, indico_to, indico_key,
                    indico_sig, indico_credential_path,
                    cached_filename, ln=CFG_SITE_LANG):
    """
    Indico seminars of the day service
    Gets seminars of the day from CERN Indico every 60 minutes and displays
    them in a widget.
    """

    _ = gettext_set_language(ln)

    try:
        seminar_xml = minidom.parse('%s/%s' % (CFG_CACHEDIR, cached_filename))
    except:
        try:
            _update_seminars(indico_baseurl, indico_what, indico_loc, indico_id,
                             indico_onlypublic, indico_from, indico_to, indico_key,
                             indico_sig, indico_credential_path, cached_filename)
            seminar_xml = minidom.parse('%s/%s' % (CFG_CACHEDIR, cached_filename))
        except:
            return "<ul><li><i>" + _("No information available") + "</i></li></ul>"

    try:
        timestamp = seminar_xml.firstChild.getAttribute("time")
    except:
        timestamp = time.struct_time()

    last_update = time.mktime(time.strptime(timestamp,
                                            "%a, %d %b %Y %H:%M:%S %Z"))
    now = time.mktime(time.gmtime())

    if last_update + update_frequency < now:
        try:
            _update_seminars(indico_baseurl, indico_what, indico_loc, indico_id,
                             indico_onlypublic, indico_from, indico_to, indico_key,
                             indico_sig, indico_credential_path, cached_filename)
            seminar_xml = minidom.parse('%s/%s' % (CFG_CACHEDIR, cached_filename))
        except:
            return "<ul><li><i>" + _("No information available") + "</i></li></ul>"

    seminars = seminar_xml.getElementsByTagName("seminar")

    if not seminars:
        return "<ul><li><i>" + _("No seminars today") + "</i></li></ul>"

    html = ""

    for seminar in seminars:

        html += "<li>"

        try:
            seminar_time = seminar.getElementsByTagName("start_time")[0].firstChild.toxml(encoding="utf-8")
        except:
            seminar_time = ""

        try:
            category = seminar.getElementsByTagName("category")[0].firstChild.toxml(encoding="utf-8")
        except:
            category = "Seminar"

        html += '%s %s<br/>' % (seminar_time, category)

        try:
            title = seminar.getElementsByTagName("title")[0].firstChild.toxml(encoding="utf-8")
        except:
            title = ""

        try:
            url = seminar.getElementsByTagName("url")[0].firstChild.toxml(encoding="utf-8")
        except:
            url = "#"

        try:
            speaker = seminar.getElementsByTagName("chair")[0].firstChild.toxml(encoding="utf-8")
        except:
            try:
                speaker = seminar.getElementsByTagName("creator")[0].firstChild.toxml(encoding="utf-8")
            except:
                speaker = ""

        if title:
            html += '<strong><a href="%s">%s</a></strong>, %s<br />' % (url, title, speaker)

        try:
            location = seminar.getElementsByTagName("location")[0].firstChild.toxml(encoding="utf-8") + " "
        except:
            location = ""

        html += location

        try:
            room = seminar.getElementsByTagName("room")[0].firstChild.toxml(encoding="utf-8")
        except:
            room = ""

        html += room

        html += "</li>"

    html = "<ul>" + html + "</ul>"

    return html

def _update_seminars(indico_baseurl, indico_what, indico_loc, indico_id,
                     indico_onlypublic, indico_from, indico_to,
                     indico_key, indico_sig, indico_credential_path,
                     cached_filename):
    """
    helper function that gets the xml data source from CERN Indico and creates
    a dedicated xml file in the cache for easy use in the widget.
    """
    if indico_credential_path:
        indico_key, indico_sig = get_indico_credentials(indico_credential_path)
    url = create_Indico_request_url(indico_baseurl,
                                    indico_what,
                                    indico_loc,
                                    indico_id,
                                    'xml',
                                    {'onlypublic': indico_onlypublic,
                                     'from': indico_from,
                                     'to': indico_to},
                                    indico_key, indico_sig)
    default_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(2.0)
    try:
        try:
            indico_xml = WEBJOURNAL_OPENER.open(url)
        except:
            return
    finally:
        socket.setdefaulttimeout(default_timeout)
    xml_file_handler = minidom.parseString(indico_xml.read())
    seminar_xml = ['<Indico_Seminars time="%s">' % time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()), ]
    agenda_items = xml_file_handler.getElementsByTagName("conference")
    for item in agenda_items:
        seminar_xml.extend(["<seminar>", ])

        for childNode in item.childNodes:

            if childNode.tagName == "startDate":
                key = "start_time"
                value = childNode.firstChild.toxml(encoding="utf-8")
                value = value and value[11:16] or ""
                seminar_xml.extend(["<%s>%s</%s>" % (key, value, key), ])
                continue

            #if childNode.tagName == "endDate":
            #    continue

            if childNode.tagName == "creator":
                for extraChildNode in childNode.getElementsByTagName("fullName"):
                    key = "creator"
                    value = extraChildNode.firstChild.toxml(encoding="utf-8")
                    seminar_xml.extend(["<%s>%s</%s>" % (key, value, key), ])
                    # Only get the first childNode
                    break
                continue

            #if childNode.tagName == "hasAnyProtection":
            #    continue

            #if childNode.tagName == "roomFullname":
            #    continue

            #if childNode.tagName == "modificationDate":
            #    continue

            #if childNode.tagName == "timezone":
            #    continue

            if childNode.tagName == "category":
                key = "category"
                value = childNode.firstChild.toxml(encoding="utf-8")
                value = value.split("/")[-1].replace("&amp;", "").replace("nbsp;", "").replace("&nbsp;", "")
                seminar_xml.extend(["<%s>%s</%s>" % (key, value, key), ])
                continue

            if childNode.tagName == "title":
                key = "title"
                value = childNode.firstChild.toxml(encoding="utf-8")
                seminar_xml.extend(["<%s>%s</%s>" % (key, value, key), ])
                continue

            if childNode.tagName == "location":
                key = "location"
                value = childNode.firstChild.toxml(encoding="utf-8")
                seminar_xml.extend(["<%s>%s</%s>" % (key, value, key), ])
                continue

            #if childNode.tagName == "type":
            #    continue

            #if childNode.tagName == "categoryId":
            #    continue

            #if childNode.tagName == "description":
            #    continue

            #if childNode.tagName == "roomMapURL":
            #    continue

            #if childNode.tagName == "material":
            #    continue

            #if childNode.tagName == "visibility":
            #    continue

            #if childNode.tagName == "address":
            #    continue

            #if childNode.tagName == "creationDate":
            #    continue

            if childNode.tagName == "room":
                key = "room"
                value = childNode.firstChild.toxml(encoding="utf-8")
                seminar_xml.extend(["<%s>%s</%s>" % (key, value, key), ])
                continue

            if childNode.tagName == "chairs":
                for extraChildNode in childNode.getElementsByTagName("fullName"):
                    key = "chair"
                    value = extraChildNode.firstChild.toxml(encoding="utf-8")
                    seminar_xml.extend(["<%s>%s</%s>" % (key, value, key), ])
                    # Only get the first childNode
                    break
                continue

            if childNode.tagName == "url":
                key = "url"
                value = childNode.firstChild.toxml(encoding="utf-8")
                seminar_xml.extend(["<%s>%s</%s>" % (key, value, key), ])
                continue

        seminar_xml.extend(["</seminar>", ])
    seminar_xml.extend(["</Indico_Seminars>", ])
    # write the created file to cache
    fptr = open("%s/%s" % (CFG_CACHEDIR, cached_filename), "w")
    fptr.write("\n".join(seminar_xml))
    fptr.close()

def get_indico_credentials(path):
    """
    Returns the Indico API key and (secret) signature as a tuple
    (public_key, private_key).
    """
    try:
        fd = open(path, "r")
        _indico_credentials = fd.read()
        fd.close()
    except IOError as e:
        return ('', '')

    return base64.decodestring(_indico_credentials).split('\n', 1)

_ = gettext_set_language('en')
dummy = _("What's on today")
dummy = _("Seminars of the week")
