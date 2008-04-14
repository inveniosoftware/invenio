# -*- coding: utf-8 -*-
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
CDS Invenio international messages functions, to be used by all
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

from invenio.config import CFG_LOCALEDIR, CFG_SITE_LANG, CFG_SITE_LANGS

_LANG_GT_D = {}
for _alang in CFG_SITE_LANGS:
    _LANG_GT_D[_alang] = gettext.translation('cds-invenio',
                                             CFG_LOCALEDIR,
                                             languages = [_alang],
                                             fallback = True)

def gettext_set_language(ln):
    """
      Set the _ gettext function in every caller function

      Usage::
        _ = gettext_set_language(ln)
    """
    return _LANG_GT_D[ln].gettext

def wash_language(ln):
    """Look at language LN and check if it is one of allowed languages
       for the interface.  Return it in case of success, return the
       default language otherwise."""
    if not ln:
        return CFG_SITE_LANG
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
    """Return list of [short name, long name] for all enabled
       languages (if 'enabled_langs_only' is set to True) or all
       existing languages (if 'enabled_langs_only' is set to False).
    """
    all_language_names = {'bg': 'Български',
                          'ca': 'Català',
                          'cs': 'Česky',
                          'de': 'Deutsch',
                          'el': 'Ελληνικά',
                          'en': 'English',
                          'es': 'Español',
                          'fr': 'Français',
                          'hr': 'Hrvatski',
                          'it': 'Italiano',
                          'ja': '日本語',
                          'no': 'Norsk/Bokmål',
                          'pl': 'Polski',
                          'pt': 'Português',
                          'ru': 'Русский',
                          'sk': 'Slovensky',
                          'sv': 'Svenska',
                          'uk': 'Українська',
                          'zh_CN': '中文(简)',
                          'zh_TW': '中文(繁)',}

    return [[lang, lang_long] for lang, lang_long in all_language_names.iteritems() \
            if lang in CFG_SITE_LANGS or enabled_langs_only == False]

