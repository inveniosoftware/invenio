# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
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

"""Implement washers for search arguments."""

import re
import time

from invenio.base.globals import cfg
from invenio.utils.datastructures import LazyDict
from invenio.utils.text import wash_for_utf8

re_pattern_wildcards_after_spaces = re.compile(r'(\s)[\*\%]+')
re_pattern_single_quotes = re.compile("'(.*?)'")
re_pattern_double_quotes = re.compile("\"(.*?)\"")
re_pattern_parens_quotes = re.compile(r'[\'\"]{1}[^\'\"]*(\([^\'\"]*\))[^\'\"]'
                                      '*[\'\"]{1}')
re_pattern_regexp_quotes = re.compile(r"\/(.*?)\/")
re_pattern_short_words = re.compile(r'([\s\"]\w{1,3})[\*\%]+')
re_pattern_space = re.compile("__SPACE__")
re_pattern_today = re.compile(r"\$TODAY\$")


def get_search_results_default_urlargd():
    """Return default config for search results arguments."""
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
        'em': (str, ""),
        'aas': (int, cfg['CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE']),
        'as': (int, cfg['CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE']),
        'p1': (str, ""), 'f1': (str, ""), 'm1': (str, ""), 'op1': (str, ""),
        'p2': (str, ""), 'f2': (str, ""), 'm2': (str, ""), 'op2': (str, ""),
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


def wash_pattern(p):
    """Wash pattern passed in URL.

    Check for sanity of the wildcard by removing wildcards if they are appended
    to extremely short words (1-3 letters).
    """
    # strip accents:
    # p = strip_accents(p) # FIXME: when available, strip accents all the time
    # add leading/trailing whitespace for the two following wildcard-sanity
    # checking regexps:
    p = " " + p + " "
    # replace spaces within quotes by __SPACE__ temporarily:
    p = re_pattern_single_quotes.sub(
        lambda x: "'" + x.group(1).replace(' ', '__SPACE__') + "'", p)
    p = re_pattern_double_quotes.sub(
        lambda x: "\""+x.group(1).replace(' ', '__SPACE__') + "\"", p)
    p = re_pattern_regexp_quotes.sub(
        lambda x: "/" + x.group(1).replace(' ', '__SPACE__') + "/", p)
    # get rid of unquoted wildcards after spaces:
    p = re_pattern_wildcards_after_spaces.sub("\\1", p)
    # get rid of extremely short words (1-3 letters with wildcards):
    # p = re_pattern_short_words.sub("\\1", p)
    # replace back __SPACE__ by spaces:
    p = re_pattern_space.sub(" ", p)
    # replace special terms:
    p = re_pattern_today.sub(time.strftime("%Y-%m-%d", time.localtime()), p)
    # remove unnecessary whitespace:
    p = p.strip()
    # remove potentially wrong UTF-8 characters:
    p = wash_for_utf8(p)
    return p


def wash_output_format(ouput_format):
    """Wash output format FORMAT.

    Currently only prevents input like 'of=9' for backwards-compatible format
    that prints certain fields only (for this task, 'of=tm' is preferred).
    """
    if str(ouput_format[0:3]).isdigit() and len(ouput_format) != 6:
        # asked to print MARC tags, but not enough digits,
        # so let's switch back to HTML brief default
        return 'hb'
    return ouput_format


def wash_field(f):
    """Wash field passed by URL."""
    if f:
        # get rid of unnecessary whitespace and make it lowercase
        # (e.g. Author -> author) to better suit iPhone etc input
        # mode:
        f = f.strip().lower()
    # wash legacy 'f' field names, e.g. replace 'wau' or `au' by
    # 'author', if applicable:
    return cfg.get('CFG_WEBSEARCH_FIELDS_CONVERT', {}).get(f, f)


def wash_dates(d1="", d1y=0, d1m=0, d1d=0, d2="", d2y=0, d2m=0, d2d=0):
    """Wash date passed by URL.

    Take user-submitted date arguments D1 (full datetime string) or
    (D1Y, D1M, D1Y) year, month, day tuple and D2 or (D2Y, D2M, D2Y)
    and return (YYY1-M1-D2 H1:M1:S2, YYY2-M2-D2 H2:M2:S2) datetime
    strings in the YYYY-MM-DD HH:MM:SS format suitable for time
    restricted searching.

    Note that when both D1 and (D1Y, D1M, D1D) parameters are present,
    the precedence goes to D1.  Ditto for D2*.

    Note that when (D1Y, D1M, D1D) are taken into account, some values
    may be missing and are completed e.g. to 01 or 12 according to
    whether it is the starting or the ending date.
    """
    datetext1, datetext2 = "", ""
    # sanity checking:
    if d1 == "" and d1y == 0 and d1m == 0 and d1d == 0 and \
            d2 == "" and d2y == 0 and d2m == 0 and d2d == 0:
        return ("", "")  # nothing selected, so return empty values
    # wash first (starting) date:
    if d1:
        # full datetime string takes precedence:
        datetext1 = d1
    else:
        # okay, first date passed as (year,month,day):
        if d1y:
            datetext1 += "%04d" % d1y
        else:
            datetext1 += "0000"
        if d1m:
            datetext1 += "-%02d" % d1m
        else:
            datetext1 += "-01"
        if d1d:
            datetext1 += "-%02d" % d1d
        else:
            datetext1 += "-01"
        datetext1 += " 00:00:00"
    # wash second (ending) date:
    if d2:
        # full datetime string takes precedence:
        datetext2 = d2
    else:
        # okay, second date passed as (year,month,day):
        if d2y:
            datetext2 += "%04d" % d2y
        else:
            datetext2 += "9999"
        if d2m:
            datetext2 += "-%02d" % d2m
        else:
            datetext2 += "-12"
        if d2d:
            datetext2 += "-%02d" % d2d
        else:
            datetext2 += "-31"
            # NOTE: perhaps we should add max(datenumber) in given month,
            # but for our quering it's not needed, 31 will always do.
        datetext2 += " 00:00:00"
    # okay, return constructed YYYY-MM-DD HH:MM:SS datetexts:
    return (datetext1, datetext2)


def wash_search_urlargd(form):
    """
    Create canonical search arguments from those passed via web form.
    """
    from invenio.ext.legacy.handler import wash_urlargd
    argd = wash_urlargd(form, search_results_default_urlargd)
    if 'as' in argd:
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
