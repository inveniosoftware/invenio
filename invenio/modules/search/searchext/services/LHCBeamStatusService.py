# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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
WebSearch service to display LHC beam status
"""
from invenio.modules.search.services import SearchService
from invenio.base.i18n import gettext_set_language
from invenio.config import CFG_SITE_LANG, CFG_SITE_URL

__plugin_version__ = "Search Service Plugin API 1.0"

class LHCBeamStatusService(SearchService):
    """
    Display LHC Beam Status
    """

    def get_description(self, ln=CFG_SITE_LANG):
        "Return service description"
        return "Return LHC Beam status info"

    def answer(self, req, user_info, of, cc, colls_to_search, p, f, search_units, ln):
        """
        Answer question given by context.

        Return (relevance, html_string) where relevance is integer
        from 0 to 100 indicating how relevant to the question the
        answer is (see C{CFG_WEBSEARCH_SERVICE_MAX_SERVICE_ANSWER_RELEVANCE} for details) ,
        and html_string being a formatted answer.
        """
        if f:
            return (0, '')

        words = [unit[1].lower() for unit in search_units if unit[2] == ""]

        if not words:
            return (0, '')

        _ = gettext_set_language(ln)
        if 'vistars' in words or \
           (('lhc' in words or 'beam' in words) and \
            'status' in words):
            out = '''
            <img id="vistar" src="%(CFG_SITE_URL)s/img/loading.gif"/>
<script language="javascript" type="text/javascript">
function refresh()
{
    imgobj = $("#vistar")
	imgobj.attr("src", 'http://cs-ccr-www3.cern.ch/vistar_capture/lhc1.png'+ '?'+Math.random()).stop(true,true).hide().show();
    imgobj.attr("style", "max-width:600px");
	setTimeout("refresh()", 8000);
}
$(document).ready(function(){
	refresh();
});
</script>
'''  % {'CFG_SITE_URL': CFG_SITE_URL}

            return (70, out)

        return (0, '')
