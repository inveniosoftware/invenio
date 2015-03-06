# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Helper methods for accounts."""

from datetime import timedelta

from flask import render_template, url_for

from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.ext.email import send_email


def send_account_activation_email(user):
    """Send an account activation email."""
    from invenio.modules.access.mailcookie import \
        mail_cookie_create_mail_activation

    expires_in = cfg.get('CFG_WEBSESSION_ADDRESS_ACTIVATION_EXPIRE_IN_DAYS')

    address_activation_key = mail_cookie_create_mail_activation(
        user.email,
        cookie_timeout=timedelta(days=expires_in)
    )

    # Render context.
    ctx = {
        "ip_address": None,
        "user": user,
        "email": user.email,
        "activation_link": url_for(
            'webaccount.access',
            mailcookie=address_activation_key,
            _external=True,
            _scheme='https',
        ),
        "days": expires_in,
    }

    # Send email
    send_email(
        cfg.get('CFG_SITE_SUPPORT_EMAIL'),
        user.email,
        _("Account registration at %(sitename)s",
          sitename=cfg['CFG_SITE_NAME']),
        render_template("accounts/emails/activation.tpl", **ctx)
    )
