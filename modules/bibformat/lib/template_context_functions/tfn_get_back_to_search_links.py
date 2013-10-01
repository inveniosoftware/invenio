# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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


from invenio.config import \
    CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT, \
    CFG_SITE_URL, \
    CFG_SITE_NAME
from invenio.urlutils import create_html_link
from invenio.messages import gettext_set_language
import invenio.template
from flask import session

"""
BibFormat element - Display links (previous, next, back-to-search)
to navigate through the records.
"""

def template_context_function(recID, ln):
    """
    Displays next-hit/previous-hit/back-to-search links
    on the detailed record pages in order to be able to quickly
    flip between detailed record pages
    @param recID: detailed record ID
    @type recID: string
    @param ln: language of the page
    @type ln: string
    @return: html output
    @rtype: html
    """

    _ = gettext_set_language(ln)
    websearch_templates = invenio.template.load('websearch')
    search_results_default_urlargd = websearch_templates.search_results_default_urlargd
    out = ""

    # this variable is set to zero so nothing is displayed
    if not CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT:
        return out

    # search for a specific record having not done
    # any search before
    try:
        last_query = session['websearch-last-query']
        recids = session["websearch-last-query-hits"]
    except:
        return out

    last_query = CFG_SITE_URL + last_query
    # did not get the limit CFG_WEBSEARCH_PREV_NEXT_HIT_LIMIT,
    # so it will only displayed the "back to search" link
    if not recids:
        out += '''<div><span class="moreinfo">
                    %(back)s </span></div>''' % \
                    {'back': create_html_link(last_query, {}, _("Back to search"), {'class': "moreinfo"})}
        return out

    nb_recids = len(recids)
    # if there is only one hit,
    # to show only the "back to search" link
    if nb_recids == 1:
        out += '''<div><span class="moreinfo>
                    %(back)s </span></div>''' % \
                    {'back': create_html_link(last_query, {}, _("Back to search"), {'class': "moreinfo"})}
    elif nb_recids > 1:
        pos = recids.index(int(recID))
        numrec = pos + 1
        if pos == 0:
            recIDnext = recids[pos + 1]
            recIDlast = recids[nb_recids - 1]
            # to display only the links to the next and last record
            out += '''<div><span class="moreinfo">
                                <span>%(numrec)s %(nb_recids)s</span> %(next)s %(last)s </span></div> ''' % {
                            'numrec': _("%s of") % ('<strong>' + websearch_templates.tmpl_nice_number(numrec, ln) + '</strong>'),
                            'nb_recids': ("%s") % ('<strong>' + websearch_templates.tmpl_nice_number(nb_recids, ln) + '</strong>'),
                            'next': create_html_link(websearch_templates.build_search_url(recid=recIDnext, ln=ln),
                                    {}, ('<i class="icon-angle-right icon-large"></i>'), {'class': "moreinfo"}),
                            'last': create_html_link(websearch_templates.build_search_url(recid=recIDlast, ln=ln),
                                    {}, ('<i class="icon-double-angle-right icon-large"></i>'), {'class': "moreinfo"})}
        elif pos == nb_recids - 1:
            recIDfirst = recids[0]
            recIDprev = recids[pos - 1]
            # to display only the links to the first and previous record
            out += '''<div><span class="moreinfo">
                                %(first)s %(previous)s <span>%(numrec)s %(nb_recids)s</span></span></div>''' % {
                            'first': create_html_link(websearch_templates.build_search_url(recid=recIDfirst, ln=ln),
                                        {}, ('<i class="icon-double-angle-left icon-large"></i>'), {'class': "moreinfo"}),
                            'previous': create_html_link(websearch_templates.build_search_url(recid=recIDprev, ln=ln),
                                        {}, ('<i class="icon-angle-left icon-large"></i>'), {'class': "moreinfo"}),
                            'numrec': _("%s of") % ('<strong>' + websearch_templates.tmpl_nice_number(numrec, ln) + '</strong>'),
                            'nb_recids': ("%s") % ('<strong>' + websearch_templates.tmpl_nice_number(nb_recids, ln) + '</strong>')}
        else:
            # to display all links: first, previous, next, last record, and "back to search"
            recIDfirst = recids[0]
            recIDprev = recids[pos - 1]
            recIDnext = recids[pos + 1]
            recIDlast = recids[len(recids) - 1]
            out += '''<div><span class="moreinfo">
                                %(first)s %(previous)s
                                <span class="outof">%(numrec)s %(nb_recids)s</span> %(next)s %(last)s </span></div>''' % {
                            'first': create_html_link(websearch_templates.build_search_url(recid=recIDfirst, ln=ln),
                                        {}, ('<i class="icon-double-angle-left icon-large"></i>'),
                                        {'class': "moreinfo"}),
                            'previous': create_html_link(websearch_templates.build_search_url(recid=recIDprev, ln=ln),
                                        {}, ('<i class="icon-angle-left icon-large"></i>'), {'class': "moreinfo"}),
                            'numrec': _("%s of") % ('<strong>' + websearch_templates.tmpl_nice_number(numrec, ln) + '</strong>'),
                            'nb_recids': ("%s") % ('<strong>' + websearch_templates.tmpl_nice_number(nb_recids, ln) + '</strong>'),
                            'next': create_html_link(websearch_templates.build_search_url(recid=recIDnext, ln=ln),
                                        {}, ('<i class="icon-angle-right icon-large"></i>'), {'class': "moreinfo"}),
                            'last': create_html_link(websearch_templates.build_search_url(recid=recIDlast, ln=ln),
                                        {}, ('<i class="icon-double-angle-right icon-large"></i>'), {'class': "moreinfo"})}
        out += '''<div><span class="moreinfo">
                    %(back)s </span></div>''' % {
                'back': create_html_link(last_query, {}, _("Back to search"), {'class': "moreinfo"})}
    return out
