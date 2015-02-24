# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
"""BibFormat element - Prints client info
"""
__revision__ = "$Id$"

def format_element(bfo, var=''):
    '''
    Print several client specific variables.
    @param var: the name of the desired variable. Can be one of: ln, search_pattern, uid, referer, uri, nickname, email
           ln: the current language of the user
           search_pattern: the list of keywords used by the user
           uid: the current user id
           referer: the url the user came from
           uri: the current uri
           nickname: the user nickname
           email: the user email
    '''

    if var == '':
        out =  ''
    elif var == 'ln':
        out = bfo.lang
    elif var == 'search_pattern':
        out = ' '.join(bfo.search_pattern)
    elif var == 'uid':
        out = bfo.user_info['uid']
    elif var == 'referer':
        out = bfo.user_info['referer']
    elif var == 'uri':
        out = bfo.user_info['uri']
    elif var == 'nickname':
        out = bfo.user_info['nickname']
    elif var == 'email':
        out = bfo.user_info['email']
    else:
        out = 'Unknown variable: %s' % (var)

    return out
