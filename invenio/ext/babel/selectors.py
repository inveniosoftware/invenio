# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Implement various localization selectors."""

from flask import request, session, current_app
from flask_login import current_user


def get_locale():
    """Compute the language needed to return the answer to the client."""
    from invenio.base.i18n import wash_language
    required_ln = None
    passed_ln = request.values.get('ln', type=str)
    if passed_ln:
        ## If ln is specified explictly as a GET or POST argument
        ## let's take it!
        required_ln = wash_language(passed_ln)
        if passed_ln != required_ln:
            ## But only if it was a valid language
            required_ln = None
    if required_ln is None and 'ln' not in session:
        ## If there is no language saved into the session...
        user_language = current_user.get('language')
        if user_language:
            ## ... and the user is logged in, we try to take it from its
            ## settings.
            required_ln = user_language
        else:
            ## Otherwise we try to guess it from its request headers
            for value, quality in request.accept_languages:
                value = str(value)
                ln = wash_language(value)
                if ln == value or ln[:2] == value[:2]:
                    required_ln = ln
                    break
            else:
                ## Too bad! We stick to the default :-)
                required_ln = current_app.config.get('CFG_SITE_LANG')
    elif required_ln is None:
        required_ln = session.get('ln')

    assert required_ln is not None

    if required_ln != session.get('ln',
                                  current_app.config.get('CFG_SITE_LANG')):
        session['ln'] = required_ln

    return required_ln


def get_timezone():
    """Return the timezone from user settings."""
    return current_user.get('timezone')
