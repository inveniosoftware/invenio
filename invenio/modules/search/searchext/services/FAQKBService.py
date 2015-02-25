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
WebSearch service to answer based on BibKnowledge KB
"""
from invenio.config import CFG_SITE_LANG
from invenio.modules.search.services import KnowledgeBaseService
from invenio.base.i18n import gettext_set_language

__plugin_version__ = "Search Service Plugin API 1.0"

class FAQKBService(KnowledgeBaseService):

    def get_description(self, ln=CFG_SITE_LANG):
        "Return service description"
        return "Return links of interest based on query"

    def get_label(self, ln=CFG_SITE_LANG):
        "Return label for the list of answers"
        _ = gettext_set_language(ln)
        return _("You might be interested in:")

    def get_kbname(self):
        "Return name of KB to use"
        return "FAQ"
