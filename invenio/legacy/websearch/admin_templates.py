# -*- coding: utf-8 -*-
#
# handles rendering of webmessage module
#
# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

""" templates for webmessage module """

__revision__ = "$Id$"

from invenio.utils.mail import email_quoted_txt2html, email_quote_txt
from invenio.modules.messages.config import \
    CFG_WEBMESSAGE_STATUS_CODE, \
    CFG_WEBMESSAGE_SEPARATOR, \
    CFG_WEBMESSAGE_RESULTS_FIELD
from invenio.config import CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES
from invenio.utils.date import convert_datetext_to_dategui, \
                              datetext_default, \
                              create_day_selectbox, \
                              create_month_selectbox, \
                              create_year_selectbox
from invenio.utils.url import create_html_link, create_url
from invenio.utils.html import escape_html
from invenio.config import CFG_SITE_URL, CFG_SITE_LANG
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webuser import get_user_info


class Template:
    """Templates for WebMessage module"""
