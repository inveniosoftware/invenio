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
WebSearch service to do some basic math
"""
import re
import cgi
from invenio.config import CFG_SITE_LANG
from invenio.modules.search.services import SearchService

numerics_and_operators_re = re.compile('[^\s\d\+\-\*/\.\(\)]')
integers_re = re.compile('([^\.\d]*|^)(\d*(\.)?\d*)([^\.\d]*|$)')

__plugin_version__ = "Search Service Plugin API 1.0"

class MathCalculatorService(SearchService):
    """
    Do basic math
    """

    def get_description(self, ln=CFG_SITE_LANG):
        "Return service description"
        return "Return evaluated math expression"

    def answer(self, req, user_info, of, cc, colls_to_search, p, f, search_units, ln):
        """
        Answer question given by context.

        Return (relevance, html_string) where relevance is integer
        from 0 to 100 indicating how relevant to the question the
        answer is (see C{CFG_WEBSEARCH_SERVICE_MAX_SERVICE_ANSWER_RELEVANCE} for details) ,
        and html_string being a formatted answer.
        """
        if not p.strip():
            return (0, '')
        expression = numerics_and_operators_re.sub("", p)
        if expression == p:
            # That is safe expression

            def make_float(matchobj):
                prefix =  matchobj.group(1) or ''
                suffix = matchobj.group(4) or ''
                middle = matchobj.group(2) or ''
                if middle and not '.' in middle:
                    middle += '.0'
                return prefix + middle + suffix

            expression = integers_re.sub(make_float, expression)
            try:
                result = eval(expression)
                if result.is_integer():
                    result = int(result)
                return (100, '<strong>' + cgi.escape(p.strip()) + ' = '  + \
                        cgi.escape(str(result)) + \
                        '</strong>')
            except Exception, e:
                return (0, '')
        else:
            return (0, '')
