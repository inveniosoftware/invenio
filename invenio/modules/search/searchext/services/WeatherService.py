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
WebSearch service to display weather information
"""
from invenio.modules.search.services import SearchService
from invenio.base.i18n import gettext_set_language
from invenio.modules.bulletin.format_elements import \
    bfe_webjournal_widget_weather
try:
    from invenio.modules.bulletin.format_elements import \
        bfe_webjournal_widget_weather_meteoblue
    meteoblue_widget_available_p = True
except:
    meteoblue_widget_available_p = False
from invenio.modules.formatter.engine import BibFormatObject
from invenio.config import CFG_SITE_LANG

__plugin_version__ = "Search Service Plugin API 1.0"

class WeatherService(SearchService):
    """
    Display local weather info
    """

    def get_description(self, ln=CFG_SITE_LANG):
        "Return service description"
        return "Return weather info"

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
        if not _("weather").lower() in words and \
               not "météo" in words and \
               not "meteo" in words:
            return (0, '')

        bfo = BibFormatObject(0)
        if meteoblue_widget_available_p:
            output = bfe_webjournal_widget_weather_meteoblue.format_element(bfo)
        else:
            output = bfe_webjournal_widget_weather.format_element(bfo, display_weather_icon='true')
        if not output:
            return (0, '')

        return (100, output)
