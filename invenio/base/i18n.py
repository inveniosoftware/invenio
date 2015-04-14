# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013, 2014, 2015 CERN.
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

"""Invenio international messages functions.

To be used by all I18N interfaces.  Typical usage in the caller code is:

.. code-block:: python

   from messages import gettext_set_language
   [...]
   def square(x, ln=CFG_SITE_LANG):
       _ = gettext_set_language(ln)
       print _("Hello there!")
       print _("The square of %(x_num)s is %(x_value)s.", x_num=x, x_value=x*x)

In the caller code, all output strings should be made translatable via
the _() convention.

For more information, see ABOUT-NLS file.
"""

from __future__ import unicode_literals

import babel

from flask_babel import gettext, lazy_gettext

# Placemark for the i18n function
_ = lazy_gettext


def gettext_set_language(ln):
    """Set the _ gettext function in every caller function.

    Usage::
        _ = gettext_set_language(ln)
    """
    from invenio.ext.babel import set_locale
    with set_locale(ln):
        return gettext


def wash_language(ln):
    """Look at language LN and check if it's one of allowed languages.

    Return it in case of success, return the default language otherwise.
    """
    from invenio.config import CFG_SITE_LANG, CFG_SITE_LANGS
    if not ln:
        return CFG_SITE_LANG
    if isinstance(ln, list):
        ln = ln[0]
    ln = ln.replace('-', '_')
    if ln in CFG_SITE_LANGS:
        return ln
    elif ln[:2] in CFG_SITE_LANGS:
        return ln[:2]
    else:
        return CFG_SITE_LANG


def wash_languages(lns):
    """Check in the languages list if there's at least one of the allowed langs.

    Return it in case of success, return the default language otherwise.
    """
    from invenio.config import CFG_SITE_LANG, CFG_SITE_LANGS
    for ln in lns:
        if ln:
            ln = ln.replace('-', '_')
            if ln in CFG_SITE_LANGS:
                return ln
            elif ln[:2] in CFG_SITE_LANGS:
                return ln[:2]
    return CFG_SITE_LANG


def language_list_long(enabled_langs_only=True):
    """Return list of [short name, long name] for all enabled languages.

    Return in the same language order as they appear in CFG_SITE_LANG.

    If 'enabled_langs_only' is set to False, then return all possibly
    existing Invenio languages, even if they were not enabled on the
    site by the local administrator.  Useful for recognizing all I18N
    translations in webdoc sources or bibformat templates.
    """
    if enabled_langs_only:
        from invenio.config import CFG_SITE_LANGS
    else:
        from invenio.base.config import CFG_SITE_LANGS

    return map(lambda ln: [ln, babel.Locale.parse(ln).get_language_name()],
               CFG_SITE_LANGS)


def is_language_rtl(ln):
    """Return True if the language is right-to-left direction.

    :param ln: language
    :type ln: str
    :return: is language right-to-left direction?
    :rtype: bool
    """
    if ln in ('ar', 'fa'):
        return True
    return False
