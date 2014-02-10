## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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
    invenio.modules.search.washers
    ------------------------------

    Implements search washers.
"""
from invenio.base.globals import cfg
from invenio.utils.datastructures import LazyDict


def get_search_results_default_urlargd():
    """Returns default config for search results arguments."""
    return {
        'cc': (str, cfg['CFG_SITE_NAME']),
        'c': (list, []),
        'p': (str, ""), 'f': (str, ""),
        'rg': (int, cfg['CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS']),
        'sf': (str, ""),
        'so': (str, "d"),
        'sp': (str, ""),
        'rm': (str, ""),
        'of': (str, "hb"),
        'ot': (list, []),
        'em': (str,""),
        'aas': (int, cfg['CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE']),
        'as': (int, cfg['CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE']),
        'p1': (str, ""), 'f1': (str, ""), 'm1': (str, ""), 'op1':(str, ""),
        'p2': (str, ""), 'f2': (str, ""), 'm2': (str, ""), 'op2':(str, ""),
        'p3': (str, ""), 'f3': (str, ""), 'm3': (str, ""),
        'sc': (int, 0),
        'jrec': (int, 0),
        'recid': (int, -1), 'recidb': (int, -1), 'sysno': (str, ""),
        'id': (int, -1), 'idb': (int, -1), 'sysnb': (str, ""),
        'action': (str, "search"),
        'action_search': (str, ""),
        'action_browse': (str, ""),
        'd1': (str, ""),
        'd1y': (int, 0), 'd1m': (int, 0), 'd1d': (int, 0),
        'd2': (str, ""),
        'd2y': (int, 0), 'd2m': (int, 0), 'd2d': (int, 0),
        'dt': (str, ""),
        'ap': (int, 1),
        'verbose': (int, 0),
        'ec': (list, []),
        'wl': (int, cfg['CFG_WEBSEARCH_WILDCARD_LIMIT']),
        }

search_results_default_urlargd = LazyDict(get_search_results_default_urlargd)


def wash_search_urlargd(form):
    """
    Create canonical search arguments from those passed via web form.
    """
    from invenio.ext.legacy.handler import wash_urlargd
    argd = wash_urlargd(form, search_results_default_urlargd)
    if argd.has_key('as'):
        argd['aas'] = argd['as']
        del argd['as']
    if argd.get('aas', cfg['CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE']) \
            not in cfg['CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES']:
        argd['aas'] = cfg['CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE']

    # Sometimes, users pass ot=245,700 instead of
    # ot=245&ot=700. Normalize that.
    ots = []
    for ot in argd['ot']:
        ots += ot.split(',')
    argd['ot'] = ots

    # We can either get the mode of function as
    # action=<browse|search>, or by setting action_browse or
    # action_search.
    if argd['action_browse']:
        argd['action'] = 'browse'
    elif argd['action_search']:
        argd['action'] = 'search'
    else:
        if argd['action'] not in ('browse', 'search'):
            argd['action'] = 'search'

    del argd['action_browse']
    del argd['action_search']

    if argd['em'] != "":
        argd['em'] = argd['em'].split(",")

    return argd
