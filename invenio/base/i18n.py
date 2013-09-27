# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Invenio international messages functions, to be used by all
I18N interfaces.  Typical usage in the caller code is:

   from messages import gettext_set_language
   [...]
   def square(x, ln=CFG_SITE_LANG):
       _ = gettext_set_language(ln)
       print _("Hello there!")
       print _("The square of %s is %s.") % (x, x*x)

In the caller code, all output strings should be made translatable via
the _() convention.

For more information, see ABOUT-NLS file.
"""

__revision__ = "$Id$"

import gettext
from flask import current_app
from werkzeug.local import LocalProxy
from invenio.utils.datastructures import LazyDict

CFG_SITE_LANG = LocalProxy(lambda: current_app.config.get('CFG_SITE_LANG'))
CFG_SITE_LANGS = LocalProxy(lambda: current_app.config.get('CFG_SITE_LANGS'))

## Placemark for the i18n function
_ = lambda x: x


def _lang_gt_d():
    """Returns translation functions."""
    CFG_LOCALEDIR = current_app.config.get('CFG_LOCALEDIR')
    CFG_SITE_LANGS = current_app.config.get('CFG_SITE_LANGS')
    out = {}
    for _alang in CFG_SITE_LANGS:
        out[_alang] = gettext.translation('invenio', CFG_LOCALEDIR,
                                          languages=[_alang], fallback=True)
    return out

_LANG_GT_D = LazyDict(_lang_gt_d)


def gettext_set_language(ln, use_unicode=False):
    """Set the _ gettext function in every caller function

    Usage::
        _ = gettext_set_language(ln)
    """
    if use_unicode:
        def unicode_gettext_wrapper(*args, **kwargs):
            return _LANG_GT_D[ln].gettext(*args, **kwargs).decode('utf-8')
        return unicode_gettext_wrapper
    return _LANG_GT_D[ln].gettext


def wash_language(ln):
    """Look at language LN and check if it is one of allowed languages
       for the interface.  Return it in case of success, return the
       default language otherwise."""
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
    """Look at list of languages LNS and check if there's at least one
       of the allowed languages for the interface. Return it in case
       of success, return the default language otherwise."""
    for ln in lns:
        if ln:
            ln = ln.replace('-', '_')
            if ln in CFG_SITE_LANGS:
                return ln
            elif ln[:2] in CFG_SITE_LANGS:
                return ln[:2]
    return CFG_SITE_LANG


def language_list_long(enabled_langs_only=True):
    """
    Return list of [short name, long name] for all enabled languages,
    in the same language order as they appear in CFG_SITE_LANG.

    If 'enabled_langs_only' is set to False, then return all possibly
    existing Invenio languages, even if they were not enabled on the
    site by the local administrator.  Useful for recognizing all I18N
    translations in webdoc sources or bibformat templates.
    """
    all_language_names = {'af': 'Afrikaans',
                          'ar': 'العربية',
                          'bg': 'Български',
                          'ca': 'Català',
                          'cs': 'Česky',
                          'de': 'Deutsch',
                          'el': 'Ελληνικά',
                          'en': 'English',
                          'es': 'Español',
                          'fa': 'فارسی',
                          'fr': 'Français',
                          'hr': 'Hrvatski',
                          'gl': 'Galego',
                          'it': 'Italiano',
                          'ka': 'ქართული',
                          'rw': 'Kinyarwanda',
                          'lt': 'Lietuvių',
                          'hu': 'Magyar',
                          'ja': '日本語',
                          'no': 'Norsk/Bokmål',
                          'pl': 'Polski',
                          'pt': 'Português',
                          'ro': 'Română',
                          'ru': 'Русский',
                          'sk': 'Slovensky',
                          'sv': 'Svenska',
                          'uk': 'Українська',
                          'zh_CN': '中文(简)',
                          'zh_TW': '中文(繁)',
                          }

    if enabled_langs_only:
        enabled_lang_list = []
        for lang in CFG_SITE_LANGS:
            enabled_lang_list.append([lang, all_language_names[lang]])
        return enabled_lang_list
    else:
        return [[lang, lang_long] for lang, lang_long in
                all_language_names.iteritems()]


def is_language_rtl(ln):
    """
    Returns True or False depending on whether language is
    right-to-left direction.

    @param ln: language
    @type ln: str
    @return: is language right-to-left direction?
    @rtype: bool
    """
    if ln in ('ar', 'fa'):
        return True
    return False
