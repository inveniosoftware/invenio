# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
JournalHint service to display
"Were you looking for a journal reference? Try: <link>"
when the request is a journal reference
"""
from invenio.modules.search.services import SearchService
from invenio.config import (CFG_SITE_URL,
                            CFG_SITE_LANG)
from invenio.base.i18n import gettext_set_language
from invenio.legacy.search_engine import perform_request_search, print_record
from invenio.legacy.webuser import collect_user_info
from urllib import urlencode
import re
from cgi import escape

__plugin_version__ = "Search Service Plugin API 1.0"


class JournalHintService(SearchService):

    """Give hints on how to search the journal reference."""

    re_dot_comma_year = re.compile(r',|\([0-9]{4}\)')
    re_keyword = re.compile(
        r'^((f|fin|find)\s+)|^([a-zA-Z0-9_-]+\:)',
        re.IGNORECASE
    )

    @classmethod
    def seems_a_journal_reference(cls, reference):
        """Quickly check if `name` seems to be a journal reference."""
        # It must not be empty
        if not reference.strip():
            return False
        # There must be a comma or a year in parentesis
        if not cls.re_dot_comma_year.search(reference):
            return False
        # It must not start with a keyword
        if cls.re_keyword.search(reference):
            return False
        return True

    def get_description(self, ln=CFG_SITE_LANG):
        """Return service description."""
        return "Give hints on how to search the journal reference"

    def answer(self, req, user_info, of, cc,
               colls_to_search, p, f, search_units, ln):
        """Answer question given by context.

        Return (relevance, html_string) where relevance is integer
        from 0 to 100 indicating how relevant to the question the
        answer is (see C{CFG_WEBSEARCH_SERVICE_MAX_SERVICE_ANSWER_RELEVANCE}
        for details), and html_string being a formatted answer.
        """
        from invenio.refextract_api import search_from_reference

        _ = gettext_set_language(ln)

        if f or not self.seems_a_journal_reference(p):
            return (0, "")

        (field, pattern) = search_from_reference(p.decode('utf-8'))

        if field is not "journal":
            return (0, "")

        recids = perform_request_search(
            req=req, p=pattern, f=field, cc=cc, c=colls_to_search)

        if not recids:
            return (0, "")

        if len(recids) == 1:
            recid = recids.pop()
            user_info = collect_user_info(req)
            return (100, """\
<p><span class="journalhint">%s</span></p>
<table style="padding: 5px; border: 2px solid #ccc; margin: 20px"><tr><td>
%s
</td></tr></table>""" % (escape(_("Were you looking for this paper?")),
             print_record(recid, ln=ln, user_info=user_info)))

        query = "find rawref \"" + p + "\""
        query_link = CFG_SITE_URL + '/search?' + urlencode({'p': query})
        return (80, '<span class="journalhint">%s</span>' % (
                _("Were you looking for a journal reference? Try: %(x_href)s") %
                {"x_href": '<a href="{0}">{1}</a>'.format(
                 escape(query_link, True), escape(query))}, ))
