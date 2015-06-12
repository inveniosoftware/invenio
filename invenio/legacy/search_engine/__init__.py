# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012,
#               2013, 2014, 2015 CERN.
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

# pylint: disable=C0301,W0703

"""Invenio Search Engine in mod_python."""

import warnings

from invenio_utils.deprecation import RemovedInInvenio23Warning

warnings.warn("Legacy search_engine will be removed in 2.3. Please check "
              "'invenio_search' module.",
              RemovedInInvenio23Warning)

__lastupdated__ = """$Date$"""

__revision__ = "$Id$"

# import general modules:
import cgi
import re
import urllib
import urlparse
import zlib

from flask_login import current_user

from invenio.config import CFG_SITE_NAME, CFG_SITE_LANG, CFG_SITE_URL, \
    CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS

# import Invenio stuff:
from invenio.legacy.bibrecord import get_fieldvalues
from .utils import record_exists

from invenio.legacy.dbquery import run_sql

from invenio.base.i18n import gettext_set_language
from invenio.modules.collections.models import Collection

# em possible values
EM_REPOSITORY={"body" : "B",
               "header" : "H",
               "footer" : "F",
               "search_box" : "S",
               "see_also_box" : "L",
               "basket" : "K",
               "alert" : "A",
               "search_info" : "I",
               "overview" : "O",
               "all_portalboxes" : "P",
               "te_portalbox" : "Pte",
               "tp_portalbox" : "Ptp",
               "np_portalbox" : "Pnp",
               "ne_portalbox" : "Pne",
               "lt_portalbox" : "Plt",
               "rt_portalbox" : "Prt",
               "search_services": "SER"};



def create_navtrail_links(cc=CFG_SITE_NAME, aas=0, ln=CFG_SITE_LANG, self_p=1, tab=''):
    """Creates navigation trail links, i.e. links to collection
    ancestors (except Home collection).  If aas==1, then links to
    Advanced Search interfaces; otherwise Simple Search.
    """
    return ''


from invenio_search.washers import wash_pattern, wash_output_format, \
    wash_field, wash_dates


def get_coll_ancestors(coll):
    "Returns a list of ancestors for collection 'coll'."
    coll_ancestors = []
    coll_ancestor = coll
    while 1:
        res = run_sql("""SELECT c.name FROM collection AS c
                          LEFT JOIN collection_collection AS cc ON c.id=cc.id_dad
                          LEFT JOIN collection AS ccc ON ccc.id=cc.id_son
                          WHERE ccc.name=%s ORDER BY cc.id_dad ASC LIMIT 1""",
                      (coll_ancestor,))
        if res:
            coll_name = res[0][0]
            coll_ancestors.append(coll_name)
            coll_ancestor = coll_name
        else:
            break
    # ancestors found, return reversed list:
    coll_ancestors.reverse()
    return coll_ancestors


def search_pattern(req=None, p=None, f=None, m=None, ap=0, of="id", verbose=0,
                   ln=CFG_SITE_LANG, display_nearest_terms_box=True, wl=0):
    """Search for complex pattern 'p' within field 'f' according to
       matching type 'm'.  Return hitset of recIDs.

       The function uses multi-stage searching algorithm in case of no
       exact match found.  See the Search Internals document for
       detailed description.

       The 'ap' argument governs whether an alternative patterns are to
       be used in case there is no direct hit for (p,f,m).  For
       example, whether to replace non-alphanumeric characters by
       spaces if it would give some hits.  See the Search Internals
       document for detailed description.  (ap=0 forbits the
       alternative pattern usage, ap=1 permits it.)
       'ap' is also internally used for allowing hidden tag search
       (for requests coming from webcoll, for example). In this
       case ap=-9

       The 'of' argument governs whether to print or not some
       information to the user in case of no match found.  (Usually it
       prints the information in case of HTML formats, otherwise it's
       silent).

       The 'verbose' argument controls the level of debugging information
       to be printed (0=least, 9=most).

       All the parameters are assumed to have been previously washed.

       This function is suitable as a mid-level API.
    """
    from invenio_search.api import Query
    results = Query(p).search()
    import warnings
    warnings.warn(
        'Deprecated search_pattern(p={0}, f={1}, m={2}) = {3}.'.format(
            p, f, m, results),
        stacklevel=2
    )
    return results


def guess_primary_collection_of_a_record(recID):
    """Return primary collection name a record recid belongs to, by
       testing 980 identifier.
       May lead to bad guesses when a collection is defined dynamically
       via dbquery.
       In that case, return 'CFG_SITE_NAME'."""
    out = CFG_SITE_NAME
    dbcollids = get_fieldvalues(recID, "980__a")
    for dbcollid in dbcollids:
        variants = ("collection:" + dbcollid,
                    'collection:"' + dbcollid + '"',
                    "980__a:" + dbcollid,
                    '980__a:"' + dbcollid + '"',
                    '980:' + dbcollid ,
                    '980:"' + dbcollid + '"')
        res = run_sql("SELECT name FROM collection WHERE dbquery IN (%s,%s,%s,%s,%s,%s)", variants)
        if res:
            out = res[0][0]
            break

    return out


_re_collection_url = re.compile('/collection/(.+)')
def guess_collection_of_a_record(recID, referer=None, recreate_cache_if_needed=True):
    """Return collection name a record recid belongs to, by first testing
       the referer URL if provided and otherwise returning the
       primary collection."""
    if referer:
        dummy, hostname, path, dummy, query, dummy = urlparse.urlparse(referer)
        # requests can come from different invenio installations, with
        # different collections
        if CFG_SITE_URL.find(hostname) < 0:
            return guess_primary_collection_of_a_record(recID)
        g = _re_collection_url.match(path)
        if g:
            name = urllib.unquote_plus(g.group(1))
            # check if this collection actually exist (also normalize the name
            # if case-insensitive)
            name = Collection.query.filter_by(name=name).value('name')
        elif path.startswith('/search'):
            query = cgi.parse_qs(query)
            for name in query.get('cc', []) + query.get('c', []):
                name = Collection.query.filter_by(name=name).value('name')
    return guess_primary_collection_of_a_record(recID)


def get_all_collections_of_a_record(recID, recreate_cache_if_needed=True):
    """Return all the collection names a record belongs to.
    Note this function is O(n_collections)."""
    ret = []
    return ret


def slice_records(recIDs, jrec, rg):
    if not jrec:
        jrec = 1
    if rg:
        recIDs = recIDs[jrec-1:jrec-1+rg]
    else:
        recIDs = recIDs[jrec-1:]
    return recIDs


def get_interval_for_records_to_sort(nb_found, jrec=None, rg=None):
    """calculates in which interval should the sorted records be
    a value of 'rg=-9999' means to print all records: to be used with care."""

    if not jrec:
        jrec = 1

    if not rg:
        #return all
        return jrec-1, nb_found

    if rg == -9999: # print all records
        rg = nb_found
    else:
        rg = abs(rg)
    if jrec < 1: # sanity checks
        jrec = 1
    if jrec > nb_found:
        jrec = max(nb_found-rg+1, 1)

    # will sort records from irec_min to irec_max excluded
    irec_min = jrec - 1
    irec_max = irec_min + rg
    if irec_min < 0:
        irec_min = 0
    if irec_max > nb_found:
        irec_max = nb_found

    return irec_min, irec_max


def get_record(recid):
    """Directly the record object corresponding to the recid."""
    import warnings
    warnings.warn('Deprecated get_record({}).'.format(str(recid)),
                  stacklevel=2)
    from invenio_records import api
    try:
        return api.get_record(recid).legacy_create_recstruct()
    except AttributeError:
        return api.Record.create({'recid': recid}, 'json').legacy_create_recstruct()

def print_record(recID, format='hb', ot='', ln=CFG_SITE_LANG, decompress=zlib.decompress,
                 search_pattern=None, user_info=None, verbose=0, sf='', so='d',
                 sp='', rm='', brief_links=True):
    """
    Print record 'recID' formatted according to 'format'.

    'sf' is sort field and 'rm' is ranking method that are passed here
    only for proper linking purposes: e.g. when a certain ranking
    method or a certain sort field was selected, keep it selected in
    any dynamic search links that may be printed.
    """
    from invenio_formatter import format_record
    return format_record(
        recID, of=format, ln=ln, verbose=verbose,
        search_pattern=search_pattern
    ) if record_exists(recID) != 0 else ""


def create_add_to_search_pattern(p, p1, f1, m1, op1):
    """Create the search pattern """
    if not p1:
        return p
    init_search_pattern = p
    # operation: AND, OR, AND NOT
    if op1 == 'a' and p: # we don't want '+' at the begining of the query
        op =  ' +'
    elif op1 == 'o':
        op = ' |'
    elif op1 == 'n':
        op = ' -'
    else:
        op = ' ' if p else ''

    # field
    field = ''
    if f1:
        field = f1 + ':'

    # type of search
    pattern = p1
    start = '('
    end = ')'
    if m1 == 'e':
        start = end = '"'
    elif m1 == 'p':
        start = end = "'"
    elif m1 == 'r':
        start = end = '/'
    else: # m1 == 'o' or m1 =='a'
        words = p1.strip().split(' ')
        if len(words) == 1:
            start = end = ''
            pattern = field + words[0]
        elif m1 == 'o':
            pattern = ' |'.join([field + word for word in words])
        else:
            pattern = ' '.join([field + word for word in words])
        #avoid having field:(word1 word2) since this is not currently correctly working
        return init_search_pattern + op + start + pattern + end
    if not pattern:
        return ''
    #avoid having field:(word1 word2) since this is not currently correctly working
    return init_search_pattern + op + field + start + pattern + end


### CALLABLES

def perform_request_search(req=None, cc=CFG_SITE_NAME, c=None, p="", f="", rg=None, sf="", so="a", sp="", rm="", of="id", ot="", aas=0,
                        p1="", f1="", m1="", op1="", p2="", f2="", m2="", op2="", p3="", f3="", m3="", sc=0, jrec=0,
                        recid=-1, recidb=-1, sysno="", id=-1, idb=-1, sysnb="", action="", d1="",
                        d1y=0, d1m=0, d1d=0, d2="", d2y=0, d2m=0, d2d=0, dt="", verbose=0, ap=0, ln=CFG_SITE_LANG, ec=None, tab="",
                        wl=0, em=""):
    kwargs = prs_wash_arguments(req=req, cc=cc, c=c, p=p, f=f, rg=rg, sf=sf, so=so, sp=sp, rm=rm, of=of, ot=ot, aas=aas,
                                p1=p1, f1=f1, m1=m1, op1=op1, p2=p2, f2=f2, m2=m2, op2=op2, p3=p3, f3=f3, m3=m3, sc=sc, jrec=jrec,
                                recid=recid, recidb=recidb, sysno=sysno, id=id, idb=idb, sysnb=sysnb, action=action, d1=d1,
                                d1y=d1y, d1m=d1m, d1d=d1d, d2=d2, d2y=d2y, d2m=d2m, d2d=d2d, dt=dt, verbose=verbose, ap=ap, ln=ln, ec=ec,
                                tab=tab, wl=wl, em=em)

    import warnings
    warnings.warn('Deprecated perform_request_search({}).'.format(str(kwargs)),
                  stacklevel=2)
    from invenio_search.api import Query
    p = create_add_to_search_pattern(p, p1, f1, m1, "")
    p = create_add_to_search_pattern(p, p2, f2, m2, op1)
    p = create_add_to_search_pattern(p, p3, f3, m3, op2)
    return Query(p).search(collection=cc)


def prs_wash_arguments(req=None, cc=CFG_SITE_NAME, c=None, p="", f="", rg=CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS,
                      sf="", so="d", sp="", rm="", of="id", ot="", aas=0,
                      p1="", f1="", m1="", op1="", p2="", f2="", m2="", op2="", p3="", f3="", m3="",
                      sc=0, jrec=0, recid=-1, recidb=-1, sysno="", id=-1, idb=-1, sysnb="", action="", d1="",
                      d1y=0, d1m=0, d1d=0, d2="", d2y=0, d2m=0, d2d=0, dt="", verbose=0, ap=0, ln=CFG_SITE_LANG,
                      ec=None, tab="", uid=None, wl=0, em="", **dummy):
    """
    Sets the (default) values and checks others for the PRS call
    """

    # wash output format:
    of = wash_output_format(of)

    # wash all arguments requiring special care
    p = wash_pattern(p)
    f = wash_field(f)
    p1 = wash_pattern(p1)
    f1 = wash_field(f1)
    p2 = wash_pattern(p2)
    f2 = wash_field(f2)
    p3 = wash_pattern(p3)
    f3 = wash_field(f3)
    (d1y, d1m, d1d, d2y, d2m, d2d) = map(int, (d1y, d1m, d1d, d2y, d2m, d2d))
    datetext1, datetext2 = wash_dates(d1, d1y, d1m, d1d, d2, d2y, d2m, d2d)


    if id > 0 and recid == -1:
        recid = id
    if idb > 0 and recidb == -1:
        recidb = idb
    # deduce collection we are in (if applicable):
    if recid > 0:
        referer = None
        if req:
            referer = req.headers_in.get('Referer')
        cc = guess_collection_of_a_record(recid, referer)
    # deduce user id (if applicable):
    if uid is None:
        try:
            uid = current_user.get_id()
        except:
            uid = 0

    _ = gettext_set_language(ln)

    kwargs = {'req': req, 'cc': cc, 'c': c, 'p': p, 'f': f, 'rg': rg, 'sf': sf,
              'so': so, 'sp': sp, 'rm': rm, 'of': of, 'ot': ot, 'aas': aas,
              'p1': p1, 'f1': f1, 'm1': m1, 'op1': op1, 'p2': p2, 'f2': f2,
              'm2': m2, 'op2': op2, 'p3': p3, 'f3': f3, 'm3': m3, 'sc': sc,
              'jrec': jrec, 'recid': recid, 'recidb': recidb, 'sysno': sysno,
              'id': id, 'idb': idb, 'sysnb': sysnb, 'action': action, 'd1': d1,
              'd1y': d1y, 'd1m': d1m, 'd1d': d1d, 'd2': d2, 'd2y': d2y,
              'd2m': d2m, 'd2d': d2d, 'dt': dt, 'verbose': verbose, 'ap': ap,
              'ln': ln, 'ec': ec, 'tab': tab, 'wl': wl, 'em': em,
              'datetext1': datetext1, 'datetext2': datetext2, 'uid': uid,
              '_': _,
              'selected_external_collections_infos': None,
              }

    kwargs.update(**dummy)
    return kwargs
