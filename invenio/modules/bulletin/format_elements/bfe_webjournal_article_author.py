#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014 CERN.
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

"""WebJournal Element - display article author(s)."""

from invenio.config import (CFG_SITE_URL,
                            CFG_WEBSTYLE_EMAIL_ADDRESSES_OBFUSCATION_MODE)

from invenio.utils.url import create_html_mailto
from invenio.base.i18n import gettext_set_language


def format_element(
        bfo, separator, display_email='yes',
        email_obfuscation_mode=CFG_WEBSTYLE_EMAIL_ADDRESSES_OBFUSCATION_MODE):
    """Display article author(s).

    @param separator: separator between authors
    @param display_email: if yes, display link to authors' emails
    @param email_obfuscation_mode: how email are protected.
    See possible values in CFG_WEBSTYLE_EMAIL_ADDRESSES_OBFUSCATION_MODE
    in invenio.conf.
    """
    ln = bfo.lang
    _ = gettext_set_language(ln)

    try:
        email_obfuscation_mode_int = int(str(email_obfuscation_mode))
    except:
        email_obfuscation_mode_int = (
            CFG_WEBSTYLE_EMAIL_ADDRESSES_OBFUSCATION_MODE
        )

    email_subject = _("About your article at %(x_url)s",
                      x_url=CFG_SITE_URL + bfo.user_info['uri'])

    authors = bfo.fields('100__a', escape=1)
    emails = bfo.fields('859__a', escape=1)
    # Add empty items to match length of authors list
    emails += ['']*(len(authors) - len(emails))

    authors_list = []
    for author, email in zip(authors, emails):
        if not author:
            continue
        if email.strip() and display_email.lower() == 'yes':
            authors_list.append(create_html_mailto(
                email,
                link_label=author,
                subject=email_subject,
                email_obfuscation_mode=email_obfuscation_mode_int))
        else:
            authors_list.append(author)

    return separator.join(authors_list)


def escape_values(bfo):
    """Escape values.

    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
