# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
"""BibFormat element - ScienceWise.info

This elements displays a linking icon to ScienceWise.info for arXiv
records.
"""

import cgi
import re

from invenio.config import CFG_BASE_URL, CFG_SITE_LANG, CFG_CERN_SITE
from invenio.messages import gettext_set_language

_RE_MODERN_ARXIV = re.compile('(arxiv:)?(?P<number>\d{4}.\d{4}(v\d+)?)')
_RE_OLD_ARXIV = re.compile('(arxiv:)?(?P<number>\w+-\w+/\d{7}(v\d+)?)')
_RE_BAD_OLD_ARXIV = re.compile('(arxiv:)?(?P<archive>\w+-\w+)-(?P<number>\d{7}(v\d+)?)')

def format_element(bfo):
    """
    If the record has an ArXiv reportnumber, displays a ScienceWise icon
    to bookmark it.
    """
    _ = gettext_set_language(bfo.lang)
    for tag in ('037__a', '088__a'):
        for reportnumber in bfo.fields(tag):
            icon = create_sciencewise_icon(reportnumber)
            if icon:
                return icon
    if CFG_CERN_SITE:
        return create_sciencewise_icon(bfo.recID, cds=True)
    return ""

def get_arxiv_reportnumber(bfo):
    """
    Return an ArXiv reportnumber (if any) from the corresponding record.
    Return empty string otherwise.
    """
    for tag in ('037__a', '088__a'):
        for reportnumber in bfo.fields(tag):
            reportnumber = reportnumber.lower()
            for regexp in (_RE_MODERN_ARXIV, _RE_OLD_ARXIV):
                g = regexp.match(reportnumber)
                if g:
                    return g.group('number')
    return ""


def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0

def create_sciencewise_url(reportnumber, cds=False):
    """
    If the reportnumber is a valid arXiv reportnumber return a ScienceWise.info
    URL.
    """
    if cds:
        return "http://sciencewise.info/bookmarks/cds:%s/add" % reportnumber
    reportnumber = reportnumber.lower()
    g = _RE_BAD_OLD_ARXIV.match(reportnumber)
    if g:
        reportnumber = '%s/%s' % (g.group('archive'), g.group('number'))
    for regexp in (_RE_MODERN_ARXIV, _RE_OLD_ARXIV):
        g = regexp.match(reportnumber)
        if g:
            return "http://sciencewise.info/bookmarks/%s/add" % g.group('number')
    return ""

def create_sciencewise_icon(reportnumber, lang=CFG_SITE_LANG, cds=False):
    """
    If the reportnumber is a valid arXiv reportnumber return a ScienceWise.info
    icon.
    """
    _ = gettext_set_language(lang)
    if cds:
        return """\
    <a href="http://sciencewise.info/bookmarks/cds:%(id)s/add" target="_blank" title="%(title)s"><img src="%(siteurl)s/img/sciencewise.png" width="23" height="16" alt="ScienceWise.info icon" /></a>""" % {
                'id': cgi.escape(reportnumber, True),
                'title': cgi.escape(_("Add this document to your ScienceWise.info bookmarks"), True),
                'siteurl': cgi.escape(CFG_BASE_URL, True)
            }
    reportnumber = reportnumber.lower()
    g = _RE_BAD_OLD_ARXIV.match(reportnumber)
    if g:
        reportnumber = '%s/%s' % (g.group('archive'), g.group('number'))
    for regexp in (_RE_MODERN_ARXIV, _RE_OLD_ARXIV):
        g = regexp.match(reportnumber)
        if g:
            return """\
    <a href="http://sciencewise.info/bookmarks/%(id)s/add" target="_blank" title="%(title)s"><img src="%(siteurl)s/img/sciencewise.png" width="23" height="16" alt="ScienceWise.info icon" /></a>""" % {
                'id': cgi.escape(g.group('number'), True),
                'title': cgi.escape(_("Add this article to your ScienceWise.info bookmarks"), True),
                'siteurl': cgi.escape(CFG_BASE_URL, True)
            }
    return ""
