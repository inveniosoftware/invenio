# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2015 CERN.
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
"""BibFormat element - Prints author data from an Authority Record.
"""
from invenio.config import CFG_SITE_URL, CFG_SITE_NAME
from urllib import quote
import re

__revision__ = "$Id$"

def format_element(bfo, main_name='yes', detail='no'):
    """ Prints the data of an author authority record in HTML. By default prints
    brief version.

    @param detail: whether the 'detailed' rather than the 'brief' format
    @type detail: 'yes' or 'no'
    """

    from invenio.base.i18n import gettext_set_language
    _ = gettext_set_language(bfo.lang)    # load the right message language
    # return value
    out = ""
    # local function
    def stringify_dict(d):
        """ return string composed values in d """
        _str = ""
        if 'a' in d:
            _str += d['a']
            if 'd' in d:
                _str += ", " + d['d']
        return _str or ''
    # brief
    main_dicts = bfo.fields('100%%')
    if len(main_dicts) and main_name=='yes':
        main_dict = main_dicts[0]
        main = stringify_dict(main_dict)
        ## out += "<p style='margin-top:0px;margin-bottom:0px'>" + "<strong>" + _("Main %s name") % _("author") + "</strong>" + ": " + main + "</p>"
        out += "<a href='" +"/record/"+ str(bfo.recID) +"?ln=" + bfo.lang + "' >" + main + "</a>"
    # detail
    if detail.lower() == "yes":
        sees = [stringify_dict(see_dict) for see_dict in bfo.fields('400%%')]
        sees = filter(None, sees) # fastest way to remove empty ""s
        sees = [re.sub(",{2,}",",", x) for x in sees] # prevent ",,"
        if len(sees):
            out += "<p>" + "<strong>" + _("Name variant(s)") + "</strong>" + ": <ul><li>" + "</li><li>".join(sees) + "</li></ul></p>"
        see_alsos = [stringify_dict(see_also_dict) for see_also_dict in bfo.fields('500%%')]
        see_alsos = filter(None, see_alsos) # fastest way to remove empty ""s
        see_alsos = [re.sub(",{2,}",",", x) for x in see_alsos] # prevent ",,"
        if len(see_alsos):
            out += "<p>" + "<strong>" + _("See also") + "</strong>" + ": <ul><li>" + ",</li><li>".join(see_alsos) + "</li></ul></p>"
    # return
    return out

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0
