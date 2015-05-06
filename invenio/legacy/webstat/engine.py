# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011, 2013, 2014, 2015 CERN.
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

from __future__ import print_function

__revision__ = "$Id$"
__lastupdated__ = "$Date$"

import calendar, commands, datetime, time, os, cPickle, random, cgi
from operator import itemgetter
from invenio.config import CFG_TMPDIR, \
    CFG_SITE_URL, \
    CFG_SITE_NAME, \
    CFG_BINDIR, \
    CFG_CERN_SITE, \
    CFG_BIBCIRCULATION_ITEM_STATUS_CANCELLED, \
    CFG_BIBCIRCULATION_ITEM_STATUS_CLAIMED, \
    CFG_BIBCIRCULATION_ITEM_STATUS_IN_PROCESS, \
    CFG_BIBCIRCULATION_ITEM_STATUS_NOT_ARRIVED, \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_ORDER, \
    CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF, \
    CFG_BIBCIRCULATION_ITEM_STATUS_OPTIONAL, \
    CFG_BIBCIRCULATION_REQUEST_STATUS_DONE, \
    CFG_BIBCIRCULATION_ILL_STATUS_CANCELLED
from invenio.modules.indexer.tokenizers.BibIndexJournalTokenizer import CFG_JOURNAL_TAG
from invenio.utils.url import redirect_to_url
from invenio.legacy.search_engine import perform_request_search, \
    get_collection_reclist, \
    get_most_popular_field_values, \
    search_pattern
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.dbquery import run_sql, \
    wash_table_column_name
from invenio.legacy.websubmit.admin_dblayer import get_docid_docname_alldoctypes
from invenio.legacy.bibcirculation.utils import book_title_from_MARC, \
    book_information_from_MARC
from invenio.legacy.bibcirculation.db_layer import get_id_bibrec, \
    get_borrower_data
CFG_CACHE_LAST_UPDATED_TIMESTAMP_FILE = None
from invenio.utils.date import convert_datetext_to_datestruct, convert_datestruct_to_dategui
from invenio.legacy.bibsched.bibtask import get_modified_records_since


WEBSTAT_SESSION_LENGTH = 48 * 60 * 60 # seconds
WEBSTAT_GRAPH_TOKENS = '-=#+@$%&XOSKEHBC'

# KEY EVENT TREND SECTION

def get_keyevent_trend_collection_population(args, return_sql=False):
    """
    Returns the quantity of documents in Invenio for
    the given timestamp range.

    @param args['collection']: A collection name
    @type args['collection']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    # collect action dates
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    if args.get('collection', 'All') == 'All':
        sql_query_g = _get_sql_query("creation_date", args['granularity'],
                        "bibrec")
        sql_query_i = "SELECT COUNT(id) FROM bibrec WHERE creation_date < %s"
        initial_quantity = run_sql(sql_query_i, (lower, ))[0][0]
        return _get_keyevent_trend(args, sql_query_g, initial_quantity=initial_quantity,
                            return_sql=return_sql, sql_text=
                            "Previous count: %s<br />Current count: %%s" % (sql_query_i),
                            acumulative=True)
    else:
        ids = get_collection_reclist(args['collection'])
        if len(ids) == 0:
            return []
        g = get_keyevent_trend_new_records(args, return_sql, True)
        sql_query_i = "SELECT id FROM bibrec WHERE creation_date < %s"
        if return_sql:
            return "Previous count: %s<br />Current count: %s" % (sql_query_i % lower, g)
        initial_quantity = len(filter(lambda x: x[0] in ids, run_sql(sql_query_i, (lower, ))))
        return _get_trend_from_actions(g, initial_quantity, args['t_start'],
                          args['t_end'], args['granularity'], args['t_format'], acumulative=True)


def get_keyevent_trend_new_records(args, return_sql=False, only_action=False):
    """
    Returns the number of new records uploaded during the given timestamp range.

    @param args['collection']: A collection name
    @type args['collection']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """

    if args.get('collection', 'All') == 'All':
        return _get_keyevent_trend(args, _get_sql_query("creation_date", args['granularity'],
                            "bibrec"),
                            return_sql=return_sql)
    else:
        lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
        upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
        ids = get_collection_reclist(args['collection'])
        if len(ids) == 0:
            return []
        sql = _get_sql_query("creation_date", args["granularity"], "bibrec",
                             extra_select=", id", group_by=False, count=False)
        if return_sql:
            return sql % (lower, upper)

        recs = run_sql(sql, (lower, upper))
        if recs:
            def add_count(i_list, element):
                """ Reduce function to create a dictionary with the count of ids
                for each date """
                if i_list and element == i_list[-1][0]:
                    i_list[-1][1] += 1
                else:
                    i_list.append([element, 1])
                return i_list
            action_dates = reduce(add_count,
                            map(lambda x: x[0], filter(lambda x: x[1] in ids, recs)),
                            [])
        else:
            action_dates = []
        if only_action:
            return action_dates
        return _get_trend_from_actions(action_dates, 0, args['t_start'],
                          args['t_end'], args['granularity'], args['t_format'])


def get_keyevent_trend_search_frequency(args, return_sql=False):
    """
    Returns the number of searches (of any kind) carried out
    during the given timestamp range.

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """

    return _get_keyevent_trend(args, _get_sql_query("date", args["granularity"],
                "query INNER JOIN user_query ON id=id_query"),
                            return_sql=return_sql)


def get_keyevent_trend_comments_frequency(args, return_sql=False):
    """
    Returns the number of comments (of any kind) carried out
    during the given timestamp range.

    @param args['collection']: A collection name
    @type args['collection']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    if args.get('collection', 'All') == 'All':
        sql = _get_sql_query("date_creation", args["granularity"],
            "cmtRECORDCOMMENT")
    else:
        sql = _get_sql_query("date_creation", args["granularity"],
            "cmtRECORDCOMMENT", conditions=
            _get_collection_recids_for_sql_query(args['collection']))
    return _get_keyevent_trend(args, sql, return_sql=return_sql)


def get_keyevent_trend_search_type_distribution(args, return_sql=False):
    """
    Returns the number of searches carried out during the given
    timestamp range, but also partion them by type Simple and
    Advanced.

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    # SQL to determine all simple searches:
    simple = _get_sql_query("date", args["granularity"],
                    "query INNER JOIN user_query ON id=id_query",
                    conditions="urlargs LIKE '%%p=%%'")

    # SQL to determine all advanced searches:
    advanced = _get_sql_query("date", args["granularity"],
                    "query INNER JOIN user_query ON id=id_query",
                    conditions="urlargs LIKE '%%as=1%%'")

    # Compute the trend for both types
    s_trend = _get_keyevent_trend(args, simple,
                        return_sql=return_sql, sql_text="Simple: %s")
    a_trend = _get_keyevent_trend(args, advanced,
                        return_sql=return_sql, sql_text="Advanced: %s")

    # Assemble, according to return type
    if return_sql:
        return "%s <br /> %s" % (s_trend, a_trend)
    return [(s_trend[i][0], (s_trend[i][1], a_trend[i][1]))
            for i in range(len(s_trend))]


def get_keyevent_trend_download_frequency(args, return_sql=False):
    """
    Returns the number of full text downloads carried out
    during the given timestamp range.

    @param args['collection']: A collection name
    @type args['collection']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    # Collect list of timestamps of insertion in the specific collection
    if args.get('collection', 'All') == 'All':
        return _get_keyevent_trend(args, _get_sql_query("download_time",
                args["granularity"], "rnkDOWNLOADS"), return_sql=return_sql)
    else:
        lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
        upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
        ids = get_collection_reclist(args['collection'])
        if len(ids) == 0:
            return []
        sql = _get_sql_query("download_time", args["granularity"], "rnkDOWNLOADS",
                             extra_select=", GROUP_CONCAT(id_bibrec)")
        if return_sql:
            return sql % (lower, upper)

        action_dates = []
        for result in run_sql(sql, (lower, upper)):
            count = result[1]
            for id in result[2].split(","):
                if id == '' or not int(id) in ids:
                    count -= 1
            action_dates.append((result[0], count))
        return _get_trend_from_actions(action_dates, 0, args['t_start'],
                          args['t_end'], args['granularity'], args['t_format'])


def get_keyevent_trend_number_of_loans(args, return_sql=False):
    """
    Returns the number of loans carried out
    during the given timestamp range.

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    return _get_keyevent_trend(args, _get_sql_query("loaned_on",
            args["granularity"], "crcLOAN"), return_sql=return_sql)


def get_keyevent_trend_web_submissions(args, return_sql=False):
    """
    Returns the quantity of websubmissions in Invenio for
    the given timestamp range.

    @param args['doctype']: A doctype name
    @type args['doctype']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    if args['doctype'] == 'all':
        sql = _get_sql_query("cd", args["granularity"], "sbmSUBMISSIONS",
                conditions="action='SBI' AND status='finished'")
        res = _get_keyevent_trend(args, sql, return_sql=return_sql)
    else:
        sql = _get_sql_query("cd", args["granularity"], "sbmSUBMISSIONS",
                conditions="doctype=%s AND action='SBI' AND status='finished'")
        res = _get_keyevent_trend(args, sql, extra_param=[args['doctype']],
                                  return_sql=return_sql)

    return res


def get_keyevent_loan_statistics(args, return_sql=False):
    """
    Data:
      - Number of documents (=records) loaned
      - Number of items loaned on the total number of items
      - Number of items never loaned on the total number of items
      - Average time between the date of the record creation and  the date of the first loan
    Filter by
      - in a specified time span
      - by UDC (see MARC field 080__a - list to be submitted)
      - by item status (available, missing)
      - by date of publication (MARC field 260__c)
      - by date of the record creation in the database

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['udc']: MARC field 080__a
    @type args['udc']: str

    @param args['item_status']: available, missing...
    @type args['item_status']: str

    @param args['publication_date']: MARC field 260__c
    @type args['publication_date']: str

    @param args['creation_date']: date of the record creation in the database
    @type args['creation_date']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    # collect action dates
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcLOAN l "
    sql_where = "WHERE loaned_on > %s AND loaned_on < %s "

    param = [lower, upper]
    if 'udc' in args and args['udc'] != '':
        sql_where += "AND l." + _check_udc_value_where()
        param.append(_get_udc_truncated(args['udc']))
    if 'item_status' in args and args['item_status'] != '':
        sql_from += ", crcITEM i "
        sql_where += "AND l.barcode = i.barcode AND i.status = %s "
        param.append(args['item_status'])
    if 'publication_date' in args and args['publication_date'] != '':
        sql_where += "AND l.id_bibrec IN ( SELECT brb.id_bibrec \
FROM bibrec_bib26x brb, bib26x b WHERE brb.id_bibxxx = b.id AND tag='260__c' \
AND value LIKE %s)"
        param.append('%%%s%%' % args['publication_date'])
    if 'creation_date' in args and args['creation_date'] != '':
        sql_from += ", bibrec br "
        sql_where += "AND br.id=l.id_bibrec AND br.creation_date LIKE %s "
        param.append('%%%s%%' % args['creation_date'])
    param = tuple(param)

    # Number of loans:
    loans_sql = "SELECT COUNT(DISTINCT l.id_bibrec) " + sql_from + sql_where
    items_loaned_sql = "SELECT COUNT(DISTINCT l.barcode) " + sql_from + sql_where
    # Only the CERN site wants the items of the collection "Books & Proceedings"
    if CFG_CERN_SITE:
        items_in_book_coll = _get_collection_recids_for_sql_query("Books & Proceedings")
        if items_in_book_coll == "":
            total_items_sql = 0
        else:
            total_items_sql = "SELECT COUNT(*) FROM crcITEM WHERE %s" % \
                                    items_in_book_coll
    else: # The rest take all the items
        total_items_sql = "SELECT COUNT(*) FROM crcITEM"

    # Average time between the date of the record creation and  the date of the first loan
    avg_sql = "SELECT AVG(DATEDIFF(loaned_on, br.creation_date)) " + sql_from
    if not ('creation_date' in args and args['creation_date'] != ''):
        avg_sql += ", bibrec br "
    avg_sql += sql_where
    if not ('creation_date' in args and args['creation_date'] != ''):
        avg_sql += "AND br.id=l.id_bibrec "
    if return_sql:
        return "<ol><li>%s</li><li>Items loaned * 100 / Number of items <ul><li>\
Items loaned: %s </li><li>Number of items: %s</li></ul></li><li>100 - Items \
loaned on total number of items</li><li>%s</li></ol>" % \
            (loans_sql % param, items_loaned_sql % param, total_items_sql, avg_sql % param)
    loans = run_sql(loans_sql, param)[0][0]
    items_loaned = run_sql(items_loaned_sql, param)[0][0]
    if total_items_sql:
        total_items = run_sql(total_items_sql)[0][0]
    else:
        total_items = 0
    if total_items == 0:
        loaned_on_total = 0
        never_loaned_on_total = 0
    else:
        # Number of items loaned on the total number of items:
        loaned_on_total = float(items_loaned) * 100 / float(total_items)
        # Number of items never loaned on the total number of items:
        never_loaned_on_total = 100L - loaned_on_total
    avg = run_sql(avg_sql, param)[0][0]
    if avg:
        avg = float(avg)
    else:
        avg = 0L
    return ((loans, ), (loaned_on_total, ), (never_loaned_on_total, ), (avg, ))


def get_keyevent_loan_lists(args, return_sql=False, limit=50):
    """
    Lists:
      - List of documents (= records) never loaned
      - List of most loaned documents  (columns: number of loans,
        number of copies and the creation date of the record, in
        order to calculate the number of loans by copy), sorted
        by decreasing order (50 items)
    Filter by
      - in a specified time span
      - by UDC (see MARC field 080__a - list to be submitted)
      - by loan period (4 week loan, one week loan...)
      - by a certain number of loans
      - by date of publication (MARC field 260__c)
      - by date of the record creation in the database

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['udc']: MARC field 080__a
    @type args['udc']: str

    @param args['loan_period']: 4 week loan, one week loan...
    @type args['loan_period']: str

    @param args['min_loan']: minimum number of loans
    @type args['min_loan']: int

    @param args['max_loan']: maximum number of loans
    @type args['max_loan']: int

    @param args['publication_date']: MARC field 260__c
    @type args['publication_date']: str

    @param args['creation_date']: date of the record creation in the database
    @type args['creation_date']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_where = []
    param = []
    sql_from = ""

    if 'udc' in args and args['udc'] != '':
        sql_where.append("i." + _check_udc_value_where())
        param.append(_get_udc_truncated(args['udc']))
    if 'loan_period' in args and args['loan_period'] != '':
        sql_where.append("loan_period = %s")
        param.append(args['loan_period'])
    if 'publication_date' in args and args['publication_date'] != '':
        sql_where.append("i.id_bibrec IN ( SELECT brb.id_bibrec \
FROM bibrec_bib26x brb, bib26x b WHERE brb.id_bibxxx = b.id AND tag='260__c' \
AND value LIKE %s)")
        param.append('%%%s%%' % args['publication_date'])
    if 'creation_date' in args and args['creation_date'] != '':
        sql_from += ", bibrec br"
        sql_where.append("br.id=i.id_bibrec AND br.creation_date LIKE %s")
        param.append('%%%s%%' % args['creation_date'])
    if sql_where:
        sql_where = "WHERE %s AND" % " AND ".join(sql_where)
    else:
        sql_where = "WHERE"
    param = tuple(param + [lower, upper])

    # SQL for both queries
    check_num_loans = "HAVING "
    if 'min_loans' in args and args['min_loans'] != '':
        check_num_loans += "COUNT(*) >= %s" % args['min_loans']
    if 'max_loans' in args and args['max_loans'] != '' and args['max_loans'] != 0:
        if check_num_loans != "HAVING ":
            check_num_loans += " AND "
        check_num_loans += "COUNT(*) <= %s" % args['max_loans']
    # Optimized to get all the data in only one query (not call get_fieldvalues several times)
    mldocs_sql = "SELECT i.id_bibrec, COUNT(*) \
FROM crcLOAN l, crcITEM i%s %s l.barcode=i.barcode AND type = 'normal' AND \
loaned_on > %%s AND loaned_on < %%s GROUP BY i.id_bibrec %s" % \
        (sql_from, sql_where, check_num_loans)
    limit_n = ""
    if limit > 0:
        limit_n = "LIMIT %d" % limit
    nldocs_sql = "SELECT id_bibrec, COUNT(*) FROM crcITEM i%s %s \
barcode NOT IN (SELECT id_bibrec FROM crcLOAN WHERE loaned_on > %%s AND \
loaned_on < %%s AND type = 'normal') GROUP BY id_bibrec ORDER BY COUNT(*) DESC %s" % \
        (sql_from, sql_where, limit_n)

    items_sql = """SELECT id_bibrec, COUNT(*) items FROM "crcITEM" GROUP BY id_bibrec"""
    creation_date_sql = "SELECT creation_date FROM bibrec WHERE id=%s"
    authors_sql = "SELECT bx.value FROM bib10x bx, bibrec_bib10x bibx \
WHERE bx.id = bibx.id_bibxxx AND bx.tag LIKE '100__a' AND bibx.id_bibrec=%s"
    title_sql = "SELECT GROUP_CONCAT(bx.value SEPARATOR ' ') value FROM bib24x bx, bibrec_bib24x bibx \
WHERE bx.id = bibx.id_bibxxx AND bx.tag LIKE %s AND bibx.id_bibrec=%s GROUP BY bibx.id_bibrec"
    edition_sql = "SELECT bx.value FROM bib25x bx, bibrec_bib25x AS bibx \
WHERE bx.id = bibx.id_bibxxx AND bx.tag LIKE '250__a' AND bibx.id_bibrec=%s"

    if return_sql:
        return "Most loaned: %s<br \>Never loaned: %s" % \
            (mldocs_sql % param, nldocs_sql % param)

    mldocs = run_sql(mldocs_sql, param)
    items = dict(run_sql(items_sql))
    order_m = []
    for mldoc in mldocs:
        order_m.append([mldoc[0], mldoc[1], items[mldoc[0]], \
                      float(mldoc[1]) / float(items[mldoc[0]])])
    order_m = sorted(order_m, key=itemgetter(3))
    order_m.reverse()
    # Check limit values
    if limit > 0:
        order_m = order_m[:limit]

    res = [("", "Title", "Author", "Edition", "Number of loans",
            "Number of copies", "Date of creation of the record")]
    for mldoc in order_m:
        res.append(("Most loaned documents",
            _check_empty_value(run_sql(title_sql, ('245__%%', mldoc[0], ))),
            _check_empty_value(run_sql(authors_sql, (mldoc[0], ))),
            _check_empty_value(run_sql(edition_sql, (mldoc[0], ))),
            mldoc[1], mldoc[2],
            _check_empty_value(run_sql(creation_date_sql, (mldoc[0], )))))

    nldocs = run_sql(nldocs_sql, param)
    for nldoc in nldocs:
        res.append(("Not loaned documents",
            _check_empty_value(run_sql(title_sql, ('245__%%', nldoc[0], ))),
            _check_empty_value(run_sql(authors_sql, (nldoc[0], ))),
            _check_empty_value(run_sql(edition_sql, (nldoc[0], ))),
            0, items[nldoc[0]],
            _check_empty_value(run_sql(creation_date_sql, (nldoc[0], )))))
#    nldocs = run_sql(nldocs_sql, param_n)
    return (res)


def get_keyevent_renewals_lists(args, return_sql=False, limit=50):
    """
    Lists:
      - List of most renewed items stored by decreasing order (50 items)
    Filter by
      - in a specified time span
      - by UDC (see MARC field 080__a - list to be submitted)
      - by collection

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['udc']: MARC field 080__a
    @type args['udc']: str

    @param args['collection']: collection of the record
    @type args['collection']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcLOAN l, crcITEM i "
    sql_where = "WHERE loaned_on > %s AND loaned_on < %s AND i.barcode = l.barcode "
    param = [lower, upper]
    if 'udc' in args and args['udc'] != '':
        sql_where += "AND l." + _check_udc_value_where()
        param.append(_get_udc_truncated(args['udc']))
    filter_coll = False
    if 'collection' in args and args['collection'] != '':
        filter_coll = True
        recid_list = get_collection_reclist(args['collection'])

    param = tuple(param)

    if limit > 0:
        limit = "LIMIT %d" % limit
    else:
        limit = ""
    sql = "SELECT i.id_bibrec, SUM(number_of_renewals) %s %s \
GROUP BY i.id_bibrec ORDER BY SUM(number_of_renewals) DESC %s" \
            % (sql_from, sql_where, limit)
    if return_sql:
        return sql % param
    # Results:
    res = [("Title", "Author", "Edition", "Number of renewals")]
    for rec, renewals in run_sql(sql, param):
        if filter_coll and rec not in recid_list:
            continue
        author = get_fieldvalues(rec, "100__a")
        if len(author) > 0:
            author = author[0]
        else:
            author = ""
        edition = get_fieldvalues(rec, "250__a")
        if len(edition) > 0:
            edition = edition[0]
        else:
            edition = ""
        res.append((book_title_from_MARC(rec), author, edition, int(renewals)))
    return (res)


def get_keyevent_returns_table(args, return_sql=False):
    """
    Data:
      - Number of overdue returns in a timespan

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    # Overdue returns:
    sql = """SELECT COUNT(*) FROM "crcLOAN" l WHERE loaned_on > %s AND loaned_on < %s AND \
due_date < NOW() AND (returned_on IS NULL OR returned_on > due_date)"""

    if return_sql:
        return sql % (lower, upper)
    return ((run_sql(sql, (lower, upper))[0][0], ), )


def get_keyevent_trend_returns_percentage(args, return_sql=False):
    """
    Returns the number of overdue returns and the total number of returns

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    # SQL to determine overdue returns:
    overdue = _get_sql_query("due_date", args["granularity"], "crcLOAN",
                conditions="due_date < NOW() AND due_date IS NOT NULL \
AND (returned_on IS NULL OR returned_on > due_date)",
                dates_range_param="loaned_on")

    # SQL to determine all returns:
    total = _get_sql_query("due_date", args["granularity"], "crcLOAN",
                conditions="due_date < NOW() AND due_date IS NOT NULL",
                dates_range_param="loaned_on")

    # Compute the trend for both types
    o_trend = _get_keyevent_trend(args, overdue,
                        return_sql=return_sql, sql_text="Overdue: %s")
    t_trend = _get_keyevent_trend(args, total,
                        return_sql=return_sql, sql_text="Total: %s")

    # Assemble, according to return type
    if return_sql:
        return "%s <br /> %s" % (o_trend, t_trend)
    return [(o_trend[i][0], (o_trend[i][1], t_trend[i][1]))
            for i in range(len(o_trend))]


def get_keyevent_ill_requests_statistics(args, return_sql=False):
    """
    Data:
    - Number of ILL requests
    - Number of satisfied ILL requests 2 weeks after the date of request
        creation on a timespan

    - Average time between the date and  the hour of the ill request
        date and the date and the hour of the delivery item to the user
        on a timespan
    - Average time between the date and  the hour the ILL request
        was sent to the supplier and the date and hour of the
        delivery item on a timespan

    Filter by
      - in a specified time span
      - by type of document (book or article)
      - by status of the request (= new, sent, etc.)
      - by supplier

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['doctype']: type of document (book or article)
    @type args['doctype']: str

    @param args['status']: status of the request (= new, sent, etc.)
    @type args['status']: str

    @param args['supplier']: supplier
    @type args['supplier']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcILLREQUEST ill "
    sql_where = "WHERE period_of_interest_from > %s AND period_of_interest_from < %s "

    param = [lower, upper]

    if 'doctype' in args and args['doctype'] != '':
        sql_where += "AND  ill.request_type=%s"
        param.append(args['doctype'])
    if 'status' in args and args['status'] != '':
        sql_where += "AND ill.status = %s "
        param.append(args['status'])
    else:
        sql_where += "AND ill.status != %s "
        param.append(CFG_BIBCIRCULATION_ILL_STATUS_CANCELLED)
    if 'supplier' in args and args['supplier'] != '':
        sql_from += ", crcLIBRARY lib "
        sql_where += "AND lib.id=ill.id_crcLIBRARY AND lib.name=%s "
        param.append(args['supplier'])

    param = tuple(param)
    requests_sql = "SELECT COUNT(*) %s %s" % (sql_from, sql_where)
    satrequests_sql = "SELECT COUNT(*) %s %s \
AND arrival_date IS NOT NULL AND \
DATEDIFF(arrival_date, period_of_interest_from) < 14 " % (sql_from, sql_where)
    avgdel_sql = "SELECT AVG(TIMESTAMPDIFF(DAY, period_of_interest_from, arrival_date)) %s %s \
AND arrival_date IS NOT NULL" % (sql_from, sql_where)
    avgsup_sql = "SELECT AVG(TIMESTAMPDIFF(DAY, request_date, arrival_date)) %s %s \
AND arrival_date IS NOT NULL \
AND request_date IS NOT NULL" % (sql_from, sql_where)
    if return_sql:
        return "<ol><li>%s</li><li>%s</li><li>%s</li><li>%s</li></ol>" % \
            (requests_sql % param, satrequests_sql % param,
             avgdel_sql % param, avgsup_sql % param)
    # Number of requests:
    requests = run_sql(requests_sql, param)[0][0]

    # Number of satisfied ILL requests 2 weeks after the date of request creation:
    satrequests = run_sql(satrequests_sql, param)[0][0]

    # Average time between the date and the hour of the ill request date and
    # the date and the hour of the delivery item to the user
    avgdel = run_sql(avgdel_sql, param)[0][0]
    if avgdel:
        avgdel = float(avgdel)
    else:
        avgdel = 0
    # Average time between the date and  the hour the ILL request was sent to
    # the supplier and the date and hour of the delivery item
    avgsup = run_sql(avgsup_sql, param)[0][0]
    if avgsup:
        avgsup = float(avgsup)
    else:
        avgsup = 0

    return ((requests, ), (satrequests, ), (avgdel, ), (avgsup, ))


def get_keyevent_ill_requests_lists(args, return_sql=False, limit=50):
    """
    Lists:
      - List of ILL requests
    Filter by
      - in a specified time span
      - by type of request (article or book)
      - by supplier

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['doctype']: type of request (article or book)
    @type args['doctype']: str

    @param args['supplier']: supplier
    @type args['supplier']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = """FROM "crcILLREQUEST" ill """
    sql_where = "WHERE status != '%s' AND request_date > %%s AND request_date < %%s " \
                    % CFG_BIBCIRCULATION_ITEM_STATUS_CANCELLED

    param = [lower, upper]

    if 'doctype' in args and args['doctype'] != '':
        sql_where += "AND ill.request_type=%s "
        param.append(args['doctype'])
    if 'supplier' in args and args['supplier'] != '':
        sql_from += ", crcLIBRARY lib "
        sql_where += """AND lib.id=ill."id_crcLIBRARY" AND lib.name=%s """
        param.append(args['supplier'])
    param = tuple(param)

    if limit > 0:
        limit = "LIMIT %d" % limit
    else:
        limit = ""
    sql = "SELECT ill.id, item_info %s %s %s" % (sql_from, sql_where, limit)
    if return_sql:
        return sql % param
    # Results:
    res = [("Id", "Title", "Author", "Edition")]
    for req_id, item_info in run_sql(sql, param):
        item_info = eval(item_info)
        try:
            res.append((req_id, item_info['title'], item_info['authors'], item_info['edition']))
        except KeyError:
            pass
    return (res)


def get_keyevent_trend_satisfied_ill_requests_percentage(args, return_sql=False):
    """
    Returns the number of satisfied ILL requests 2 weeks after the date of request
    creation and the total number of ILL requests

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['doctype']: type of document (book or article)
    @type args['doctype']: str

    @param args['status']: status of the request (= new, sent, etc.)
    @type args['status']: str

    @param args['supplier']: supplier
    @type args['supplier']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    sql_from = "crcILLREQUEST ill "
    sql_where = ""
    param = []

    if 'doctype' in args and args['doctype'] != '':
        sql_where += "AND ill.request_type=%s"
        param.append(args['doctype'])
    if 'status' in args and args['status'] != '':
        sql_where += "AND ill.status = %s "
        param.append(args['status'])
    else:
        sql_where += "AND ill.status != %s "
        param.append(CFG_BIBCIRCULATION_ILL_STATUS_CANCELLED)
    if 'supplier' in args and args['supplier'] != '':
        sql_from += ", crcLIBRARY lib "
        sql_where += "AND lib.id=ill.id_crcLIBRARY AND lib.name=%s "
        param.append(args['supplier'])

    # SQL to determine satisfied ILL requests:
    satisfied = _get_sql_query("request_date", args["granularity"], sql_from,
                  conditions="ADDDATE(request_date, 14) < NOW() AND \
(arrival_date IS NULL OR arrival_date < ADDDATE(request_date, 14)) " + sql_where)

    # SQL to determine all ILL requests:
    total = _get_sql_query("request_date", args["granularity"], sql_from,
                  conditions="ADDDATE(request_date, 14) < NOW() "+ sql_where)

    # Compute the trend for both types
    s_trend = _get_keyevent_trend(args, satisfied, extra_param=param,
                        return_sql=return_sql, sql_text="Satisfied: %s")
    t_trend = _get_keyevent_trend(args, total, extra_param=param,
                        return_sql=return_sql, sql_text="Total: %s")

    # Assemble, according to return type
    if return_sql:
        return "%s <br /> %s" % (s_trend, t_trend)
    return [(s_trend[i][0], (s_trend[i][1], t_trend[i][1]))
            for i in range(len(s_trend))]


def get_keyevent_items_statistics(args, return_sql=False):
    """
    Data:
      - The total number of items
      - Total number of new items added in last year
    Filter by
      - in a specified time span
      - by collection
      - by UDC (see MARC field 080__a - list to be submitted)

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['udc']: MARC field 080__a
    @type args['udc']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcITEM i "
    sql_where = "WHERE "

    param = []

    if 'udc' in args and args['udc'] != '':
        sql_where += "i." + _check_udc_value_where()
        param.append(_get_udc_truncated(args['udc']))

    # Number of items:
    if sql_where == "WHERE ":
        sql_where = ""
    items_sql = "SELECT COUNT(i.id_bibrec) %s %s" % (sql_from, sql_where)

    # Number of new items:
    if sql_where == "":
        sql_where = "WHERE creation_date > %s AND creation_date < %s "
    else:
        sql_where += " AND creation_date > %s AND creation_date < %s "
    new_items_sql = "SELECT COUNT(i.id_bibrec) %s %s" % (sql_from, sql_where)

    if return_sql:
        return "Total: %s <br />New: %s" % (items_sql % tuple(param), new_items_sql % tuple(param + [lower, upper]))
    return ((run_sql(items_sql, tuple(param))[0][0], ), (run_sql(new_items_sql, tuple(param + [lower, upper]))[0][0], ))


def get_keyevent_items_lists(args, return_sql=False, limit=50):
    """
    Lists:
      - The list of items
    Filter by
      - by library (=physical location of the item)
      - by status (=on loan, available, requested, missing...)

    @param args['library']: physical location of the item
    @type args[library'']: str

    @param args['status']: on loan, available, requested, missing...
    @type args['status']: str
    """

    sql_from = "FROM crcITEM i "
    sql_where = "WHERE "

    param = []

    if 'library' in args and args['library'] != '':
        sql_from += ", crcLIBRARY li "
        sql_where += "li.id=i.id_crcLIBRARY AND li.name=%s "
        param.append(args['library'])

    if 'status' in args and args['status'] != '':
        if sql_where != "WHERE ":
            sql_where += "AND "
        sql_where += "i.status = %s "
        param.append(args['status'])
    param = tuple(param)
    # Results:
    res = [("Title", "Author", "Edition", "Barcode", "Publication date")]
    if sql_where == "WHERE ":
        sql_where = ""
    if limit > 0:
        limit = "LIMIT %d" % limit
    else:
        limit = ""
    sql = "SELECT i.barcode, i.id_bibrec %s %s %s" % (sql_from, sql_where, limit)
    if len(param) == 0:
        sqlres = run_sql(sql)
    else:
        sqlres = run_sql(sql, tuple(param))
        sql = sql % param
    if return_sql:
        return sql

    for barcode, rec in sqlres:
        author = get_fieldvalues(rec, "100__a")
        if len(author) > 0:
            author = author[0]
        else:
            author = ""
        edition = get_fieldvalues(rec, "250__a")
        if len(edition) > 0:
            edition = edition[0]
        else:
            edition = ""
        res.append((book_title_from_MARC(rec),
                    author, edition, barcode,
                    book_information_from_MARC(int(rec))[1]))
    return (res)


def get_keyevent_loan_request_statistics(args, return_sql=False):
    """
    Data:
      - Number of hold requests, one week after the date of request creation
      - Number of successful hold requests transactions
      - Average time between the hold request date and the date of delivery document  in a year
    Filter by
      - in a specified time span
      - by item status (available, missing)

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['item_status']: available, missing...
    @type args['item_status']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcLOANREQUEST lr "
    sql_where = "WHERE request_date > %s AND request_date < %s "

    param = [lower, upper]

    if 'item_status' in args and args['item_status'] != '':
        sql_from += ", crcITEM i "
        sql_where += "AND lr.barcode = i.barcode AND i.status = %s "
        param.append(args['item_status'])
    param = tuple(param)

    custom_table = get_customevent_table("loanrequest")
    # Number of hold requests, one week after the date of request creation:
    holds = "SELECT COUNT(*) %s, %s ws %s AND ws.request_id=lr.id AND \
DATEDIFF(ws.creation_time, lr.request_date) >= 7" % (sql_from, custom_table, sql_where)

    # Number of successful hold requests transactions
    succesful_holds = "SELECT COUNT(*) %s %s AND lr.status='%s'" % (sql_from, sql_where,
                                                        CFG_BIBCIRCULATION_REQUEST_STATUS_DONE)

    # Average time between the hold request date and the date of delivery document in a year
    avg_sql = "SELECT AVG(DATEDIFF(ws.creation_time, lr.request_date)) \
%s, %s ws %s AND ws.request_id=lr.id" % (sql_from, custom_table, sql_where)

    if return_sql:
        return "<ol><li>%s</li><li>%s</li><li>%s</li></ol>" % \
            (holds % param, succesful_holds % param, avg_sql % param)
    avg = run_sql(avg_sql, param)[0][0]
    if avg is int:
        avg = int(avg)
    else:
        avg = 0
    return ((run_sql(holds, param)[0][0], ),
        (run_sql(succesful_holds, param)[0][0], ), (avg, ))


def get_keyevent_loan_request_lists(args, return_sql=False, limit=50):
    """
    Lists:
      - List of the most requested items
    Filter by
      - in a specified time span
      - by UDC (see MARC field 080__a - list to be submitted)

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['udc']: MARC field 080__a
    @type args['udc']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcLOANREQUEST lr "
    sql_where = "WHERE request_date > %s AND request_date < %s "

    param = [lower, upper]

    if 'udc' in args and args['udc'] != '':
        sql_where += "AND lr." + _check_udc_value_where()
        param.append(_get_udc_truncated(args['udc']))
    if limit > 0:
        limit = "LIMIT %d" % limit
    else:
        limit = ""
    sql = "SELECT lr.barcode %s %s GROUP BY barcode \
ORDER BY COUNT(*) DESC %s" % (sql_from, sql_where, limit)
    if return_sql:
        return sql
    res = [("Title", "Author", "Edition", "Barcode")]

    # Most requested items:
    for barcode in run_sql(sql, param):
        rec = get_id_bibrec(barcode[0])
        author = get_fieldvalues(rec, "100__a")
        if len(author) > 0:
            author = author[0]
        else:
            author = ""
        edition = get_fieldvalues(rec, "250__a")
        if len(edition) > 0:
            edition = edition[0]
        else:
            edition = ""
        res.append((book_title_from_MARC(rec), author, edition, barcode[0]))

    return (res)


def get_keyevent_user_statistics(args, return_sql=False):
    """
    Data:
      - Total number of  active users (to be defined = at least one transaction in the past year)
    Filter by
      - in a specified time span
      - by registration date

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from_ill = "FROM crcILLREQUEST ill "
    sql_from_loan = "FROM crcLOAN l "
    sql_where_ill = "WHERE request_date > %s AND request_date < %s "
    sql_where_loan = "WHERE loaned_on > %s AND loaned_on < %s "
    param = (lower, upper, lower, upper)

    # Total number of  active users:
    users = """SELECT COUNT(DISTINCT user) FROM ((SELECT "id_crcBORROWER" user %s %s)
UNION (SELECT "id_crcBORROWER" user %s %s)) res""" % \
        (sql_from_ill, sql_where_ill, sql_from_loan, sql_where_loan)

    if return_sql:
        return users % param
    return ((run_sql(users, param)[0][0], ), )


def get_keyevent_user_lists(args, return_sql=False, limit=50):
    """
    Lists:
      - List of most intensive users (ILL requests + Loan)
    Filter by
      - in a specified time span
      - by registration date

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    param = (lower, upper, lower, upper)

    if limit > 0:
        limit = "LIMIT %d" % limit
    else:
        limit = ""
    sql = """SELECT user, SUM(trans) FROM
((SELECT "id_crcBORROWER" user, COUNT(*) trans FROM "crcILLREQUEST" ill
WHERE request_date > %%s AND request_date < %%s GROUP BY "id_crcBORROWER") UNION
(SELECT "id_crcBORROWER" user, COUNT(*) trans FROM "crcLOAN" l WHERE loaned_on > %%s AND
loaned_on < %%s GROUP BY "id_crcBORROWER")) res GROUP BY user ORDER BY SUM(trans) DESC
%s""" % (limit)

    if return_sql:
        return sql % param
    res = [("Name", "Address", "Mailbox", "E-mail", "Number of transactions")]

    # List of most intensive users (ILL requests + Loan):
    for borrower_id, trans in run_sql(sql, param):
        name, address, mailbox, email = get_borrower_data(borrower_id)
        res.append((name, address, mailbox, email, int(trans)))

    return (res)

# KEY EVENT SNAPSHOT SECTION

def get_keyevent_snapshot_uptime_cmd():
    """
    A specific implementation of get_current_event().

    @return: The std-out from the UNIX command 'uptime'.
    @type: str
    """
    return _run_cmd('uptime').strip().replace('  ', ' ')


def get_keyevent_snapshot_apache_processes():
    """
    A specific implementation of get_current_event().

    @return: The std-out from the UNIX command 'uptime'.
    @type: str
    """
    # The number of Apache processes (root+children)
    return _run_cmd('ps -e | grep apache2 | grep -v grep | wc -l')


def get_keyevent_snapshot_bibsched_status():
    """
    A specific implementation of get_current_event().

    @return: Information about the number of tasks in the different status modes.
    @type: [(str, int)]
    """
    sql = """SELECT status, COUNT(status) FROM "schTASK" GROUP BY status"""
    return [(x[0], int(x[1])) for x in run_sql(sql)]


def get_keyevent_snapshot_sessions():
    """
    A specific implementation of get_current_event().

    @return: The current number of website visitors (guests, logged in)
    @type: (int, int)
    """
    # SQL to retrieve sessions in the Guests
    sql = "SELECT COUNT(session_expiry) " + \
          "FROM session INNER JOIN user ON uid=id " + \
          "WHERE email = '' AND " + \
          "session_expiry-%d < unix_timestamp() AND " \
          % WEBSTAT_SESSION_LENGTH + \
          "unix_timestamp() < session_expiry"
    guests = run_sql(sql)[0][0]

    # SQL to retrieve sessions in the Logged in users
    sql = "SELECT COUNT(session_expiry) " + \
          "FROM session INNER JOIN user ON uid=id " + \
          "WHERE email <> '' AND " + \
          "session_expiry-%d < unix_timestamp() AND " \
          % WEBSTAT_SESSION_LENGTH + \
          "unix_timestamp() < session_expiry"
    logged_ins = run_sql(sql)[0][0]

    # Assemble, according to return type
    return (guests, logged_ins)


def get_keyevent_bibcirculation_report(freq='yearly'):
    """
    Monthly and yearly report with the total number of circulation
    transactions (loans, renewals, returns, ILL requests, hold request).
    @param freq: yearly or monthly
    @type freq: str

    @return: loans, renewals, returns, ILL requests, hold request
    @type: (int, int, int, int, int)
    """
    if freq == 'monthly':
        datefrom = datetime.date.today().strftime("%Y-%m-01 00:00:00")
    else: #yearly
        datefrom = datetime.date.today().strftime("%Y-01-01 00:00:00")
    loans, renewals = run_sql("""SELECT COUNT(*),
SUM(number_of_renewals)
FROM "crcLOAN" WHERE loaned_on > %s""", (datefrom, ))[0]
    returns = run_sql("""SELECT COUNT(*) FROM "crcLOAN"
WHERE returned_on!='0000-00-00 00:00:00' and loaned_on > %s""", (datefrom, ))[0][0]
    illrequests = run_sql("""SELECT COUNT(*) FROM "crcILLREQUEST" WHERE request_date > %s""",
                          (datefrom, ))[0][0]
    holdrequest = run_sql("""SELECT COUNT(*) FROM "crcLOANREQUEST" WHERE request_date > %s""",
                          (datefrom, ))[0][0]
    return (loans, renewals, returns, illrequests, holdrequest)


def get_last_updates():
    """
    List date/time when the last updates where done (easy reading format).

    @return: last indexing, last ranking, last sorting, last webcolling
    @type: (datetime, datetime, datetime, datetime)
    """
    try:
        last_index = convert_datestruct_to_dategui(convert_datetext_to_datestruct \
                    (str(run_sql("""SELECT last_updated FROM "idxINDEX" WHERE
                    name='global'""")[0][0])))
        last_rank = convert_datestruct_to_dategui(convert_datetext_to_datestruct \
                    (str(run_sql("""SELECT last_updated FROM "rnkMETHOD" ORDER BY
                            last_updated DESC LIMIT 1""")[0][0])))
        last_sort = convert_datestruct_to_dategui(convert_datetext_to_datestruct \
                    (str(run_sql("""SELECT last_updated FROM "bsrMETHODDATA" ORDER BY
                            last_updated DESC LIMIT 1""")[0][0])))
        file_coll_last_update = open(CFG_CACHE_LAST_UPDATED_TIMESTAMP_FILE, 'r')
        last_coll = convert_datestruct_to_dategui(convert_datetext_to_datestruct \
                    (str(file_coll_last_update.read())))
        file_coll_last_update.close()
    # database not filled
    except IndexError:
        return ("", "", "", "")
    return (last_index, last_rank, last_sort, last_coll)

def get_list_link(process, category=None):
    """
    Builds the link for the list of records not indexed, ranked, sorted or
    collected.
    @param process: kind of process the records are waiting for (index, rank,
                    sort, collect)
    @type process: str
    @param category: specific sub-category of the process.
                     Index: global, collection, abstract, author, keyword,
                            reference, reportnumber, title, fulltext, year,
                            journal, collaboration, affiliation, exactauthor,
                            caption, firstauthor, exactfirstauthor, authorcount)
                     Rank:  wrd, demo_jif, citation, citerank_citation_t,
                            citerank_pagerank_c, citerank_pagerank_t
                     Sort:  latest first, title, author, report number,
                            most cited
                     Collect: Empty / None
    @type category: str

    @return: link text
    @type: string
    """
    if process == "index":
        list_registers = run_sql("""SELECT id FROM bibrec WHERE
                            modification_date > (SELECT last_updated FROM
                            "idxINDEX" WHERE name=%s)""", (category,))
    elif process == "rank":
        list_registers = run_sql("""SELECT id FROM bibrec WHERE
                            modification_date > (SELECT last_updated FROM
                            "rnkMETHOD" WHERE name=%s)""", (category,))
    elif process == "sort":
        list_registers = run_sql("""SELECT id FROM bibrec WHERE
                            modification_date > (SELECT last_updated FROM
                            "bsrMETHODDATA" WHERE "id_bsrMETHOD"=(SELECT id
                            FROM "bsrMETHOD" WHERE name=%s))""", (category,))
    elif process == "collect":
        file_coll_last_update = open(CFG_CACHE_LAST_UPDATED_TIMESTAMP_FILE, 'r')
        coll_last_update = file_coll_last_update.read()
        file_coll_last_update.close()
        list_registers = zip(get_modified_records_since(coll_last_update).tolist())

    # build the link
    if len(list_registers) == 0:
        return "Up to date"
    link = '<a href="' + CFG_SITE_URL + '/search?p='
    for register in list_registers:
        link += 'recid%3A' + str(register[0]) + '+or+'
    # delete the last '+or+'
    link = link[:len(link)-4]
    link += '">' + str(len(list_registers)) + '</a>'
    return link

def get_search_link(record_id):
    """
    Auxiliar, builds the direct link for a given record.
    @param record_id: record's id number
    @type record_id: int

    @return: link text
    @type: string
    """
    link = '<a href="' + CFG_SITE_URL + '/record/' + \
            str(record_id) + '">Record [' + str(record_id) + ']</a>'
    return link

def get_ingestion_matching_records(request=None, limit=25):
    """
    Fetches all the records matching a given pattern, arranges them by last
    modificaton date and returns a list.
    @param request: requested pattern to match
    @type request: str

    @return: list of records matching a pattern,
             (0,) if no request,
             (-1,) if the request was invalid
    @type: list
    """
    if request==None or request=="":
        return (0,)
    try:
        records = list(search_pattern(p=request))
    except:
        return (-1,)
    if records == []:
        return records

    # order by most recent modification date
    query = 'SELECT id FROM bibrec WHERE '
    for r in records:
        query += 'id="' + str(r) + '" OR '
    query = query[:len(query)-4]
    query += ' ORDER BY modification_date DESC LIMIT %s'

    list_records = run_sql(query, (limit,))
    final_list = []
    for lr in list_records:
        final_list.append(lr[0])
    return final_list

def get_record_ingestion_status(record_id):
    """
    Returns the amount of ingestion methods not updated yet to a given record.
    If 0, the record is up to date.
    @param record_id: record id number
    @type record_id: int

    @return: number of methods not updated for the record
    @type: int
    """
    counter = 0
    counter += run_sql("""SELECT COUNT(*) FROM bibrec WHERE
                        id=%s AND modification_date > (SELECT last_updated FROM
                        "idxINDEX" WHERE name='global')""", (record_id, ))[0][0]

    counter += run_sql("""SELECT COUNT(*) FROM bibrec WHERE
                        id=%s AND modification_date > (SELECT last_updated FROM
                        "rnkMETHOD" ORDER BY last_updated DESC LIMIT 1)""", \
                        (record_id, ))[0][0]

    counter = run_sql("""SELECT COUNT(*) FROM bibrec WHERE
                        id=%s AND modification_date > (SELECT last_updated FROM
                        "bsrMETHODDATA" ORDER BY last_updated DESC LIMIT 1)""", \
                        (record_id, ))[0][0]
    file_coll_last_update = open(CFG_CACHE_LAST_UPDATED_TIMESTAMP_FILE, 'r')
    last_coll = file_coll_last_update.read()
    file_coll_last_update.close()
    counter += run_sql('SELECT COUNT(*) FROM bibrec WHERE \
                        id=%s AND \
                        modification_date >\
                         %s', (record_id, last_coll,))[0][0]
    return counter

def get_specific_ingestion_status(record_id, process, method=None):
    """
    Returns whether a record is or not up to date for a given
    process and method.

    @param record_id: identification number of the record
    @type record_id: int
    @param process: kind of process the records may be waiting for (index,
                    rank, sort, collect)
    @type process: str
    @param method: specific sub-method of the process.
                     Index: global, collection, abstract, author, keyword,
                            reference, reportnumber, title, fulltext, year,
                            journal, collaboration, affiliation, exactauthor,
                            caption, firstauthor, exactfirstauthor, authorcount
                     Rank:  wrd, demo_jif, citation, citerank_citation_t,
                            citerank_pagerank_c, citerank_pagerank_t
                     Sort:  latest first, title, author, report number,
                            most cited
                     Collect: Empty / None
    @type category: str

    @return: text: None if the record is up to date
                   Last time the method was updated if it is waiting
    @type: date/time string
    """
    exist = run_sql('SELECT COUNT(*) FROM bibrec WHERE id=%s', (record_id, ))
    if exist[0][0] == 0:
        return "REG not in DB"

    if process == "index":
        list_registers = run_sql('SELECT COUNT(*) FROM bibrec WHERE \
                                id=%s AND modification_date > (SELECT \
                                last_updated FROM "idxINDEX" WHERE name=%s)',
                                (record_id, method,))
        last_time = run_sql ('SELECT last_updated FROM "idxINDEX" WHERE \
                            name=%s', (method,))[0][0]
    elif process == "rank":
        list_registers = run_sql("""SELECT COUNT(*) FROM bibrec WHERE
                                id=%s AND modification_date > (SELECT
                                last_updated FROM "rnkMETHOD" WHERE name=%s)""",
                                (record_id, method,))
        last_time = run_sql ("""SELECT last_updated FROM "rnkMETHOD" WHERE
                            name=%s""", (method,))[0][0]
    elif process == "sort":
        list_registers = run_sql("""SELECT COUNT(*) FROM bibrec WHERE
                                id=%s AND modification_date > (SELECT
                                last_updated FROM "bsrMETHODDATA" WHERE
                                "id_bsrMETHOD"=(SELECT id FROM "bsrMETHOD"
                                WHERE name=%s))""", (record_id, method,))
        last_time = run_sql ("""SELECT last_updated FROM "bsrMETHODDATA" WHERE
                            "id_bsrMETHOD"=(SELECT id FROM "bsrMETHOD"
                            WHERE name=%s)""", (method,))[0][0]
    elif process == "collect":
        file_coll_last_update = open(CFG_CACHE_LAST_UPDATED_TIMESTAMP_FILE, 'r')
        last_time = file_coll_last_update.read()
        file_coll_last_update.close()
        list_registers = run_sql('SELECT COUNT(*) FROM bibrec WHERE id=%s \
                                AND modification_date > %s',
                                (record_id, last_time,))
    # no results means the register is up to date
    if list_registers[0][0] == 0:
        return None
    else:
        return convert_datestruct_to_dategui(convert_datetext_to_datestruct \
                    (str(last_time)))

def get_title_ingestion(record_id, last_modification):
    """
    Auxiliar, builds a direct link for a given record, with its last
    modification date.
    @param record_id: id number of the record
    @type record_id: string
    @param last_modification: date/time of the last modification
    @type last_modification: string

    @return: link text
    @type: string
    """
    return '<h3><a href="%s/record/%s">Record [%s] last modification: %s</a></h3>' \
            % (CFG_SITE_URL, record_id, record_id, last_modification)

def get_record_last_modification (record_id):
    """
    Returns the date/time of the last modification made to a given record.
    @param record_id: id number of the record
    @type record_id: int

    @return: date/time of the last modification
    @type: string
    """
    return convert_datestruct_to_dategui(convert_datetext_to_datestruct \
                    (str(run_sql('SELECT modification_date FROM bibrec \
                    WHERE id=%s', (record_id,))[0][0])))

def get_general_status():
    """
    Returns an aproximate amount of ingestions processes not aplied to new or
    updated records, using the "global" category.

    @return: number of processes not updated
    @type: int
    """
    return run_sql("""SELECT COUNT(*) FROM bibrec WHERE
                    modification_date > (SELECT last_updated FROM
                    "idxINDEX" WHERE name='global')""")[0][0]



# ERROR LOG STATS

def update_error_log_analyzer():
    """Creates splitted files for today's errors"""
    _run_cmd('bash %s/webstat -e -is' % CFG_BINDIR)


def get_invenio_error_log_ranking():
    """ Returns the ranking of the errors in the invenio log"""
    return _run_cmd('bash %s/webstat -e -ir' % CFG_BINDIR)


def get_invenio_last_n_errors(nerr):
    """Returns the last nerr errors in the invenio log (without details)"""
    return _run_cmd('bash %s/webstat -e -il %d' % (CFG_BINDIR, nerr))


def get_invenio_error_details(error):
    """Returns the complete text of the invenio error."""
    out = _run_cmd('bash %s/webstat -e -id %s' % (CFG_BINDIR, error))
    return out


def get_apache_error_log_ranking():
    """ Returns the ranking of the errors in the apache log"""
    return _run_cmd('bash %s/webstat -e -ar' % CFG_BINDIR)

# CUSTOM EVENT SECTION

def get_customevent_trend(args):
    """
    Returns trend data for a custom event over a given
    timestamp range.

    @param args['event_id']: The event id
    @type args['event_id']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str

    @param args['cols']: Columns and it's content that will be include
                         if don't exist or it's empty it will include all cols
    @type args['cols']: [ [ str, str ], ]
    """
    # Get a MySQL friendly date
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    tbl_name = get_customevent_table(args['event_id'])
    col_names = get_customevent_args(args['event_id'])

    where = []
    sql_param = [lower, upper]
    for col_bool, col_title, col_content in args['cols']:
        if not col_title in col_names:
            continue
        if col_content:
            if col_bool == "" or not where:
                where.append(wash_table_column_name(col_title))
            elif col_bool == "and":
                where.append("AND %s"
                                 % wash_table_column_name(col_title))
            elif col_bool == "or":
                where.append("OR %s"
                                 % wash_table_column_name(col_title))
            elif col_bool == "and_not":
                where.append("AND NOT %s"
                                 % wash_table_column_name(col_title))
            else:
                continue
            where.append(" LIKE %s")
            sql_param.append("%" + col_content + "%")

    sql = _get_sql_query("creation_time", args['granularity'], tbl_name, " ".join(where))

    return _get_trend_from_actions(run_sql(sql, tuple(sql_param)), 0,
                                   args['t_start'], args['t_end'],
                                   args['granularity'], args['t_format'])


def get_customevent_dump(args):
    """
    Similar to a get_event_trend implemention, but NO refining aka frequency
    handling is carried out what so ever. This is just a dump. A dump!

    @param args['event_id']: The event id
    @type args['event_id']: str

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str

    @param args['cols']: Columns and it's content that will be include
                         if don't exist or it's empty it will include all cols
    @type args['cols']: [ [ str, str ], ]
    """
    # Get a MySQL friendly date
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    # Get customevents
    # events_list = [(creation_time, event, [arg1, arg2, ...]), ...]
    event_list = []
    event_cols = {}
    for event_id, i in [(args['ids'][i], str(i))
                         for i in range(len(args['ids']))]:
        # Get all the event arguments and creation times
        tbl_name = get_customevent_table(event_id)
        col_names = get_customevent_args(event_id)

        sql_query = ["SELECT * FROM %s WHERE creation_time > '%%s'" % wash_table_column_name(tbl_name), (lower,)] # kwalitee: disable=sql
        sql_query.append("AND creation_time < '%s'" % upper)
        sql_param = []
        for col_bool, col_title, col_content in args['cols' + i]:
            if not col_title in col_names:
                continue
            if col_content:
                if col_bool == "and" or col_bool == "":
                    sql_query.append("AND %s" % \
                                         wash_table_column_name(col_title))
                elif col_bool == "or":
                    sql_query.append("OR %s" % \
                                         wash_table_column_name(col_title))
                elif col_bool == "and_not":
                    sql_query.append("AND NOT %s" % \
                                         wash_table_column_name(col_title))
                else:
                    continue
                sql_query.append(" LIKE %s")
                sql_param.append("%" + col_content + "%")
        sql_query.append("ORDER BY creation_time DESC")
        sql = ' '.join(sql_query)
        res = run_sql(sql, tuple(sql_param))

        for row in res:
            event_list.append((row[1], event_id, row[2:]))
        # Get the event col names
        try:
            event_cols[event_id] = cPickle.loads(run_sql(
                    """SELECT cols FROM "staEVENT" WHERE id = %s""",
                    (event_id, ))[0][0])
        except TypeError:
            event_cols[event_id] = ["Unnamed"]
    event_list.sort()

    output = []
    for row in event_list:
        temp = [row[1], row[0].strftime('%Y-%m-%d %H:%M:%S')]

        arguments = ["%s: %s" % (event_cols[row[1]][i],
                                 row[2][i]) for i in range(len(row[2]))]

        temp.extend(arguments)
        output.append(tuple(temp))

    return output


def get_customevent_table(event_id):
    """
    Helper function that for a certain event id retrives the corresponding
    event table name.
    """
    res = run_sql(
        """SELECT CONCAT("staEVENT", number) FROM "staEVENT" WHERE id = %s""", (event_id, ))
    try:
        return res[0][0]
    except IndexError:
        # No such event table
        return None


def get_customevent_args(event_id):
    """
    Helper function that for a certain event id retrives the corresponding
    event argument (column) names.
    """
    res = run_sql("""SELECT cols FROM "staEVENT" WHERE id = %s""", (event_id, ))
    try:
        if res[0][0]:
            return cPickle.loads(res[0][0])
        else:
            return []
    except IndexError:
        # No such event table
        return None

# CUSTOM SUMMARY SECTION

def get_custom_summary_data(query, tag):
    """Returns the annual report data for the specified year

    @param query: Search query to make customized report
    @type query: str

    @param tag: MARC tag for the output
    @type tag: str
    """

    # Check arguments
    if tag == '':
        tag = CFG_JOURNAL_TAG.replace("%", "p")

    # First get records of the year
    recids = perform_request_search(p=query, of="id", wl=0)

    # Then return list by tag
    pub = get_most_popular_field_values(recids, tag)

    if len(pub) == 0:
        return []
    if CFG_CERN_SITE:
        total = sum([x[1] for x in pub])
    else:
        others = 0
        total = 0
        first_other = -1
        for elem in pub:
            total += elem[1]
            if elem[1] < 2:
                if first_other == -1:
                    first_other = pub.index(elem)
                others += elem[1]
        del pub[first_other:]

        if others != 0:
            pub.append(('Others', others))
    pub.append(('TOTAL', total))

    return pub


def create_custom_summary_graph(data, path, title):
    """
    Creates a pie chart with the information from the custom summary and
    saves it in the file specified by the path argument
    """
    # If no input, we don't bother about anything
    if len(data) == 0:
        return False
    os.environ['HOME'] = CFG_TMPDIR

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except:
        from invenio.errorlib import register_exception
        register_exception()
        return False

    # make a square figure and axes
    matplotlib.rcParams['font.size'] = 8
    labels = [x[0] for x in data]
    numb_elem = len(labels)
    width = 6 + float(numb_elem) / 7
    gfile = plt.figure(1, figsize=(width, 6))

    plt.axes([0.1, 0.1, 4.2 / width, 0.7])

    numb = [x[1] for x in data]
    total = sum(numb)
    fracs = [x * 100 / total for x in numb]
    colors = []

    random.seed()
    for i in range(numb_elem):
        col = 0.5 + float(i) / (float(numb_elem) * 2.0)
        rand = random.random() / 2.0
        if i % 3 == 0:
            red = col
            green = col + rand
            blue = col - rand
            if green > 1.0:
                green = 1
        elif i % 3 == 1:
            red = col - rand
            green = col
            blue = col + rand
            if blue > 1.0:
                blue = 1
        elif i % 3 == 2:
            red = col + rand
            green = col - rand
            blue = col
            if red > 1.0:
                red = 1
        colors.append((red, green, blue))
    patches = plt.pie(fracs, colors=tuple(colors), labels=labels,
                      autopct='%1i%%', pctdistance=0.8, shadow=True)[0]
    ttext = plt.title(title)
    plt.setp(ttext, size='xx-large', color='b', family='monospace', weight='extra bold')
    legend_keywords = {"prop": {"size": "small"}}
    plt.figlegend(patches, labels, 'lower right', **legend_keywords)
    plt.savefig(path)
    plt.close(gfile)
    return True
# GRAPHER

def create_graph_trend(trend, path, settings):
    """
    Creates a graph representation out of data produced from get_event_trend.

    @param trend: The trend data
    @type trend: [(str, str|int|(str|int,...))]

    @param path: Where to store the graph
    @type path: str

    @param settings: Dictionary of graph parameters
    @type settings: dict
    """
    # If no input, we don't bother about anything
    if not trend or len(trend) == 0:
        return

    # If no filename is given, we'll assume STD-out format and ASCII.
    if path == '':
        settings["format"] = 'asciiart'
    if settings["format"] == 'asciiart':
        create_graph_trend_ascii_art(trend, path, settings)
    elif settings["format"] == 'gnuplot':
        create_graph_trend_gnu_plot(trend, path, settings)
    elif settings["format"] == "flot":
        create_graph_trend_flot(trend, path, settings)


def create_graph_trend_ascii_art(trend, path, settings):
    """Creates the graph trend using ASCII art"""
    out = ""

    if settings["multiple"] is not None:
        # Tokens that will represent the different data sets (maximum 16 sets)
        # Set index (=100) to the biggest of the histogram sums
        index = max([sum(x[1]) for x in trend])

        # Print legend box
        out += "Legend: %s\n\n" % ", ".join(["%s (%s)" % x
                    for x in zip(settings["multiple"], WEBSTAT_GRAPH_TOKENS)])
    else:
        index = max([x[1] for x in trend])

    width = 82

    # Figure out the max length of the xtics, in order to left align
    xtic_max_len = max([len(_to_datetime(x[0]).strftime(
                    settings["xtic_format"])) for x in trend])

    for row in trend:
        # Print the xtic
        xtic = _to_datetime(row[0]).strftime(settings["xtic_format"])
        out_row = xtic + ': ' + ' ' * (xtic_max_len - len(xtic)) + '|'

        try:
            col_width = (1.0 * width / index)
        except ZeroDivisionError:
            col_width = 0

        if settings["multiple"] is not None:
            # The second value of the row-tuple, represents the n values from
            # the n data sets. Each set, will be represented by a different
            # ASCII character, chosen from the randomized string
            # 'WEBSTAT_GRAPH_TOKENS'.
            # NOTE: Only up to 16 (len(WEBSTAT_GRAPH_TOKENS)) data
            # sets are supported.
            total = sum(row[1])

            for i in range(len(row[1])):
                col = row[1][i]
                try:
                    out_row += WEBSTAT_GRAPH_TOKENS[i] * int(1.0 * col * col_width)
                except ZeroDivisionError:
                    break
            if len([i for i in row[1] if type(i) is int and i > 0]) - 1 > 0:
                out_row += out_row[-1]

        else:
            total = row[1]
            try:
                out_row += '-' * int(1.0 * total * col_width)
            except ZeroDivisionError:
                break

        # Print sentinel, and the total
        out += out_row + '>' + ' ' * (xtic_max_len + 4 +
                                    width - len(out_row)) + str(total) + '\n'

    # Write to destination file
    if path == '':
        print(out)
    else:
        open(path, 'w').write(out)


def create_graph_trend_gnu_plot(trend, path, settings):
    """Creates the graph trend using the GNU plot library"""
    try:
        import Gnuplot
    except ImportError:
        return

    gnup = Gnuplot.Gnuplot()

    gnup('set style data steps')
    if 'size' in settings:
        gnup('set terminal png tiny size %s' % settings['size'])
    else:
        gnup('set terminal png tiny')
    gnup('set output "%s"' % path)

    if settings["title"] != '':
        gnup.title(settings["title"].replace("\"", ""))
    if settings["xlabel"] != '':
        gnup.xlabel(settings["xlabel"])
    if settings["ylabel"] != '':
        gnup.ylabel(settings["ylabel"])

    if settings["xtic_format"] != '':
        xtics = 'set xtics ('
        xtics += ', '.join(['"%s" %d' %
                            (_to_datetime(trend[i][0], '%Y-%m-%d \
                 %H:%M:%S').strftime(settings["xtic_format"]), i)
                            for i in range(len(trend))]) + ')'
        gnup(xtics)
    gnup('set format y "%.0f"')

    # If we have multiple data sets, we need to do
    # some magic to make Gnuplot eat it,
    # This is basically a matrix transposition,
    # and the addition of index numbers.
    if settings["multiple"] is not None:
        cols = len(trend[0][1])
        rows = len(trend)
        plot_items = []
        y_max = 0
        y_min = 0
        for col in range(cols):
            data = []
            for row in range(rows):
                data.append([row, trend[row][1][col]])
            data.append([rows, trend[-1][1][col]])
            plot_items.append(Gnuplot.PlotItems
                                  .Data(data, title=settings["multiple"][col]))
            tmp_max = max([x[col] for x in data])
            tmp_min = min([x[col] for x in data])
            if tmp_max > y_max:
                y_max = tmp_max
            if tmp_min < y_min:
                y_min = tmp_min
        if y_max - y_min < 5 and y_min != 0:
            gnup('set ytic %d, 1, %d' % (y_min - 1, y_max + 2))
        elif y_max < 5:
            gnup('set ytic 1')
        gnup.plot(*plot_items)
    else:
        data = [x[1] for x in trend]
        data.append(trend[-1][1])
        y_max = max(data)
        y_min = min(data)
        if y_max - y_min < 5 and y_min != 0:
            gnup('set ytic %d, 1, %d' % (y_min - 1, y_max + 2))
        elif y_max < 5:
            gnup('set ytic 1')
        gnup.plot(data)


def create_graph_trend_flot(trend, path, settings):
    """Creates the graph trend using the flot library"""
    size = settings.get("size", "500,400").split(",")
    title = cgi.escape(settings["title"].replace(" ", "")[:10])
    out = """<!--[if IE]><script language="javascript" type="text/javascript"
                    src="%(site)s/vendors/flot/excanvas.min.js"></script><![endif]-->
              <script language="javascript" type="text/javascript" src="%(site)s/vendors/flot/jquery.flot.js"></script>
              <script language="javascript" type="text/javascript" src="%(site)s/vendors/flot/jquery.flot.selection.js"></script>
              <script id="source" language="javascript" type="text/javascript">
                     document.write('<div style="float:left"><div id="placeholder%(title)s" style="width:%(width)spx;height:%(height)spx"></div></div>'+
              '<div id="miniature%(title)s" style="float:left;margin-left:20px;margin-top:50px">' +
              '<div id="overview%(title)s" style="width:%(hwidth)dpx;height:%(hheigth)dpx"></div>' +
              '<p id="overviewLegend%(title)s" style="margin-left:10px"></p>' +
              '</div>');
                     $(function () {
                             function parseDate%(title)s(sdate){
                                 var div1 = sdate.split(' ');
                                 var day = div1[0].split('-');
                                 var hour = div1[1].split(':');
                                 return new Date(day[0], day[1]-1, day[2], hour[0], hour[1], hour[2]).getTime() - (new Date().getTimezoneOffset() * 60 * 1000) ;
                             }
                             function getData%(title)s() {""" % \
        {'site': CFG_SITE_URL, 'width': size[0], 'height': size[1], 'hwidth': int(size[0]) / 2,
         'hheigth': int(size[1]) / 2, 'title': title}
    if(len(trend) > 1):
        granularity_td = (_to_datetime(trend[1][0], '%Y-%m-%d %H:%M:%S') -
                        _to_datetime(trend[0][0], '%Y-%m-%d %H:%M:%S'))
    else:
        granularity_td = datetime.timedelta()
    # Create variables with the format dn = [[x1,y1], [x2,y2]]
    minx = trend[0][0]
    maxx = trend[0][0]
    if settings["multiple"] is not None:
        cols = len(trend[0][1])
        rows = len(trend)
        first = 0
        for col in range(cols):
            out += """var d%d = [""" % (col)
            for row in range(rows):
                if(first == 0):
                    first = 1
                else:
                    out += ", "
                if trend[row][0] < minx:
                    minx = trend[row][0]
                if trend[row][0] > maxx:
                    maxx = trend[row][0]
                out += '[parseDate%s("%s"),%d]' % \
                    (title, _to_datetime(trend[row][0], '%Y-%m-%d \
%H:%M:%S'), trend[row][1][col])
            out += ", [parseDate%s('%s'), %d]];\n" % (title,
                    _to_datetime(maxx, '%Y-%m-%d %H:%M:%S')+ granularity_td,
                    trend[-1][1][col])
        out += "return [\n"
        first = 0
        for col in range(cols):
            if first == 0:
                first = 1
            else:
                out += ", "
            out += '{data : d%d, label : "%s"}' % \
                (col, settings["multiple"][col])
        out += "];\n}\n"
    else:
        out += """var d1 = ["""
        rows = len(trend)
        first = 0
        for row in range(rows):
            if trend[row][0] < minx:
                minx = trend[row][0]
            if trend[row][0] > maxx:
                maxx = trend[row][0]
            if first == 0:
                first = 1
            else:
                out += ', '
            out += '[parseDate%s("%s"),%d]' % \
                (title, _to_datetime(trend[row][0], '%Y-%m-%d %H:%M:%S'),
                 trend[row][1])
        out += """, [parseDate%s("%s"), %d]];
                     return [d1];
                      }
            """ % (title, _to_datetime(maxx, '%Y-%m-%d %H:%M:%S') +
                   granularity_td, trend[-1][1])

    # Set options
    tics = """yaxis: {
                tickDecimals : 0
        },"""
    if settings["xtic_format"] != '':
        current =  _to_datetime(maxx, '%Y-%m-%d %H:%M:%S')
        next = current + granularity_td
        if (granularity_td.seconds + granularity_td.days * 24 * 3600) > 2592000:
            next = current.replace(day=31)
        tics += 'xaxis: { mode:"time",min:parseDate%s("%s"),max:parseDate%s("%s")},'\
            % (title, _to_datetime(minx, '%Y-%m-%d %H:%M:%S'), title, next)

    out += """var options%s ={
                series: {
                   lines: { steps: true, fill: true},
                   points: { show: false }
                },
                legend: {show: false},
                %s
                grid: { hoverable: true, clickable: true },
                selection: { mode: "xy" }
                };
                """ % (title, tics, )
        # Write the plot method in javascript

    out += """var startData%(title)s = getData%(title)s();
        var plot%(title)s = $.plot($("#placeholder%(title)s"), startData%(title)s, options%(title)s);

        // setup overview
        var overview%(title)s = $.plot($("#overview%(title)s"), startData%(title)s, {
                 legend: { show: true, container: $("#overviewLegend%(title)s") },
                 series: {
                    lines: { steps: true, fill: true, lineWidth: 1},
                    shadowSize: 0
                 },
                 %(tics)s
                 grid: { color: "#999" },
                 selection: { mode: "xy" }
               });
               """ % {"title": title, "tics": tics}

        # Tooltip and zoom
    out += """
    function showTooltip%(title)s(x, y, contents) {
        $('<div id="tooltip%(title)s">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y - 5,
            left: x + 10,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    var previousPoint%(title)s = null;
    $("#placeholder%(title)s").bind("plothover", function (event, pos, item) {

        if (item) {
            if (previousPoint%(title)s != item.datapoint) {
                previousPoint%(title)s = item.datapoint;

                $("#tooltip%(title)s").remove();
                var y = item.datapoint[1];

                showTooltip%(title)s(item.pageX, item.pageY, y);
            }
        }
        else {
            $("#tooltip%(title)s").remove();
            previousPoint%(title)s = null;
        }
    });

    $("#placeholder%(title)s").bind("plotclick", function (event, pos, item) {
        if (item) {
            plot%(title)s.highlight(item.series, item.datapoint);
        }
    });

    // now connect the two
    $("#placeholder%(title)s").bind("plotselected", function (event, ranges) {
        // clamp the zooming to prevent eternal zoom
        if (ranges.xaxis.to - ranges.xaxis.from < 0.00001){
            ranges.xaxis.to = ranges.xaxis.from + 0.00001;}
        if (ranges.yaxis.to - ranges.yaxis.from < 0.00001){
            ranges.yaxis.to = ranges.yaxis.from + 0.00001;}

        // do the zooming
        plot%(title)s = $.plot($("#placeholder%(title)s"), getData%(title)s(ranges.xaxis.from, ranges.xaxis.to),
                      $.extend(true, {}, options%(title)s, {
                          xaxis: { min: ranges.xaxis.from, max: ranges.xaxis.to },
                          yaxis: { min: ranges.yaxis.from, max: ranges.yaxis.to }
                      }));

        // don't fire event on the overview to prevent eternal loop
        overview%(title)s.setSelection(ranges, true);
    });
    $("#overview%(title)s").bind("plotselected", function (event, ranges) {
        plot%(title)s.setSelection(ranges);
    });
});
                </script>
<noscript>Your browser does not support JavaScript!
Please, select another output format</noscript>""" % {'title' : title}
    open(path, 'w').write(out)


def get_numeric_stats(data, multiple):
    """ Returns average, max and min values for data """
    data = [x[1] for x in data]
    if data == []:
        return (0, 0, 0)
    if multiple:
        lists = []
        for i in range(len(data[0])):
            lists.append([x[i] for x in data])
        return ([float(sum(x)) / len(x) for x in lists], [max(x) for x in lists],
                [min(x) for x in lists])
    else:
        return (float(sum(data)) / len(data), max(data), min(data))


def create_graph_table(data, path, settings):
    """
    Creates a html table representation out of data.

    @param data: The data
    @type data: (str,...)

    @param path: Where to store the graph
    @type path: str

    @param settings: Dictionary of table parameters
    @type settings: dict
    """
    out = """<table border="1">
"""
    if settings['rows'] == []:
        for row in data:
            out += """<tr>
"""
            for value in row:
                out += """<td>%s</td>
""" % value
            out += "</tr>"
    else:
        for dta, value in zip(settings['rows'], data):
            out += """<tr>
                 <td>%s</td>
                 <td>
""" % dta
            for vrow in value:
                out += """%s<br />
                        """ % vrow
                out = out[:-6] + "</td></tr>"
    out += "</table>"
    open(path, 'w').write(out)


def create_graph_dump(dump, path):
    """
    Creates a graph representation out of data produced from get_event_trend.

    @param dump: The dump data
    @type dump: [(str|int,...)]

    @param path: Where to store the graph
    @type path: str
    """
    out = ""

    if len(dump) == 0:
        out += "No actions for this custom event " + \
            "are registered in the given time range."
    else:
        # Make every row in dump equally long, insert None if appropriate.
        max_len = max([len(x) for x in dump])
        events = [tuple(list(x) + [None] * (max_len - len(x))) for x in dump]

        cols = ["Event", "Date and time"] + ["Argument %d" % i
                                             for i in range(max_len - 2)]

        column_widths = [max([len(str(x[i])) \
                    for x in events + [cols]]) + 3 for i in range(len(events[0]))]

        for i in range(len(cols)):
            out += cols[i] + ' ' * (column_widths[i] - len(cols[i]))
        out += "\n"
        for i in range(len(cols)):
            out += '=' * (len(cols[i])) + ' ' * (column_widths[i] - len(cols[i]))
        out += "\n\n"

        for action in dump:
            for i in range(len(action)):
                if action[i] is None:
                    temp = ''
                else:
                    temp = action[i]
                out += str(temp) + ' ' * (column_widths[i] - len(str(temp)))
            out += "\n"

    # Write to destination file
    if path == '':
        print(out)
    else:
        open(path, 'w').write(out)

# EXPORT DATA TO SLS

def get_search_frequency(day=datetime.datetime.now().date()):
    """Returns the number of searches performed in the chosen day"""
    searches = get_keyevent_trend_search_type_distribution(get_args(day))
    return sum(searches[0][1])


def get_total_records(day=datetime.datetime.now().date()):
    """Returns the total number of records which existed in the chosen day"""
    tomorrow = (datetime.datetime.now() +
                datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    args = {'collection': CFG_SITE_NAME, 't_start': day.strftime("%Y-%m-%d"),
            't_end': tomorrow, 'granularity': "day", 't_format': "%Y-%m-%d"}
    try:
        return get_keyevent_trend_collection_population(args)[0][1]
    except IndexError:
        return 0


def get_new_records(day=datetime.datetime.now().date()):
    """Returns the number of new records submitted in the chosen day"""
    args = {'collection': CFG_SITE_NAME,
            't_start': (day - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            't_end': day.strftime("%Y-%m-%d"), 'granularity': "day",
            't_format': "%Y-%m-%d"}
    try:
        return (get_total_records(day) -
             get_keyevent_trend_collection_population(args)[0][1])
    except IndexError:
        return 0


def get_download_frequency(day=datetime.datetime.now().date()):
    """Returns the number of downloads during the chosen day"""
    return get_keyevent_trend_download_frequency(get_args(day))[0][1]


def get_comments_frequency(day=datetime.datetime.now().date()):
    """Returns the number of comments during the chosen day"""
    return get_keyevent_trend_comments_frequency(get_args(day))[0][1]


def get_loans_frequency(day=datetime.datetime.now().date()):
    """Returns the number of comments during the chosen day"""
    return get_keyevent_trend_number_of_loans(get_args(day))[0][1]


def get_web_submissions(day=datetime.datetime.now().date()):
    """Returns the number of web submissions during the chosen day"""
    args = get_args(day)
    args['doctype'] = 'all'
    return get_keyevent_trend_web_submissions(args)[0][1]


def get_alerts(day=datetime.datetime.now().date()):
    """Returns the number of alerts during the chosen day"""
    args = get_args(day)
    args['cols'] = [('', '', '')]
    args['event_id'] = 'alerts'
    return get_customevent_trend(args)[0][1]


def get_journal_views(day=datetime.datetime.now().date()):
    """Returns the number of journal displays during the chosen day"""
    args = get_args(day)
    args['cols'] = [('', '', '')]
    args['event_id'] = 'journals'
    return get_customevent_trend(args)[0][1]


def get_basket_views(day=datetime.datetime.now().date()):
    """Returns the number of basket displays during the chosen day"""
    args = get_args(day)
    args['cols'] = [('', '', '')]
    args['event_id'] = 'baskets'
    return get_customevent_trend(args)[0][1]


def get_args(day):
    """Returns the most common arguments for the exporting to SLS methods"""
    return {'t_start': day.strftime("%Y-%m-%d"),
            't_end': (day + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
         'granularity': "day", 't_format': "%Y-%m-%d"}

# EXPORTER

def export_to_python(data, req):
    """
    Exports the data to Python code.

    @param data: The Python data that should be exported
    @type data: []

    @param req: The Apache request object
    @type req:
    """
    _export("text/x-python", str(data), req)


def export_to_csv(data, req):
    """
    Exports the data to CSV.

    @param data: The Python data that should be exported
    @type data: []

    @param req: The Apache request object
    @type req:
    """
    csv_list = [""""%s",%s""" % (x[0], ",".join([str(y) for y in \
                 ((type(x[1]) is tuple) and x[1] or (x[1], ))])) for x in data]
    _export('text/csv', '\n'.join(csv_list), req)


def export_to_file(data, req):
    """
    Exports the data to a file.

    @param data: The Python data that should be exported
    @type data: []

    @param req: The Apache request object
    @type req:
    """
    try:
        import xlwt
        book = xlwt.Workbook(encoding="utf-8")
        sheet1 = book.add_sheet('Sheet 1')
        for row in range(0, len(data)):
            for col in range(0, len(data[row])):
                sheet1.write(row, col, "%s" % data[row][col])
        filename = CFG_TMPDIR + "/webstat_export_" + \
            str(time.time()).replace('.', '') + '.xls'
        book.save(filename)
        redirect_to_url(req, '%s/stats/export?filename=%s&mime=%s' \
                        % (CFG_SITE_URL, os.path.basename(filename), 'application/vnd.ms-excel'))
    except ImportError:
        csv_list = []
        for row in data:
            row = ['"%s"' % str(col) for col in row]
            csv_list.append(",".join(row))
        _export('text/csv', '\n'.join(csv_list), req)
# INTERNAL

def _export(mime, content, req):
    """
    Helper function to pass on the export call. Create a
    temporary file in which the content is stored, then let
    redirect to the export web interface.
    """
    filename = CFG_TMPDIR + "/webstat_export_" + \
        str(time.time()).replace('.', '')
    open(filename, 'w').write(content)
    redirect_to_url(req, '%s/stats/export?filename=%s&mime=%s' \
                        % (CFG_SITE_URL, os.path.basename(filename), mime))


def _get_trend_from_actions(action_dates, initial_value,
                            t_start, t_end, granularity, dt_format, acumulative=False):
    """
    Given a list of dates reflecting some sort of action/event, and some additional parameters,
    an internal data format is returned. 'initial_value' set to zero, means that the frequency
    will not be accumulative, but rather non-causal.

    @param action_dates: A list of dates, indicating some sort of action/event.
    @type action_dates: [datetime.datetime]

    @param initial_value: The numerical offset the first action's value should make use of.
    @type initial_value: int

    @param t_start: Start time for the time domain in dt_format
    @type t_start: str

    @param t_end: End time for the time domain in dt_format
    @type t_end: str

    @param granularity: The granularity of the time domain, span between values.
                        Possible values are [year,month,day,hour,minute,second].
    @type granularity: str

    @param dt_format: Format of the 't_start' and 't_stop' parameters
    @type dt_format: str

    @return: A list of tuples zipping a time-domain and a value-domain
    @type: [(str, int)]
    """
    # Append the maximum date as a sentinel indicating we're done
    action_dates = list(action_dates)

    # Construct the datetime tuple for the stop time
    stop_at = _to_datetime(t_end, dt_format) - datetime.timedelta(seconds=1)

    vector = [(None, initial_value)]

    try:
        upcoming_action = action_dates.pop()
        #Do not count null values (when year, month or day is 0)
        if granularity in ("year", "month", "day") and upcoming_action[0] == 0:
            upcoming_action = action_dates.pop()
    except IndexError:
        upcoming_action = (datetime.datetime.max, 0)

    # Create an iterator running from the first day of activity
    for current in _get_datetime_iter(t_start, granularity, dt_format):
        # Counter of action_dates in the current span, set the initial value to
        # zero to avoid accumlation.
        if acumulative:
            actions_here = vector[-1][1]
        else:
            actions_here = 0
        # Check to see if there's an action date in the current span
        if upcoming_action[0] == {"year": current.year,
            "month": current.month,
            "day": current.day,
            "hour": current.hour,
            "minute": current.minute,
            "second": current.second
            }[granularity]:
            actions_here += upcoming_action[1]
            try:
                upcoming_action = action_dates.pop()
            except IndexError:
                upcoming_action = (datetime.datetime.max, 0)

        vector.append((current.strftime('%Y-%m-%d %H:%M:%S'), actions_here))

        # Make sure to stop the iteration at the end time
        if {"year": current.year >= stop_at.year,
            "month": current.month >= stop_at.month and current.year == stop_at.year,
            "day": current.day >= stop_at.day and current.month == stop_at.month,
            "hour": current.hour >= stop_at.hour and current.day == stop_at.day,
            "minute": current.minute >= stop_at.minute and current.hour == stop_at.hour,
            "second": current.second >= stop_at.second and current.minute == stop_at.minute
            }[granularity]:
            break
    # Remove the first bogus tuple, and return
    return vector[1:]


def _get_keyevent_trend(args, sql, initial_quantity=0, extra_param=[],
                        return_sql=False, sql_text='%s', acumulative=False):
    """
    Returns the trend for the sql passed in the given timestamp range.

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    # collect action dates
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    param = tuple([lower, upper] + extra_param)
    if return_sql:
        sql = sql % param
        return sql_text % sql

    return _get_trend_from_actions(run_sql(sql, param), initial_quantity, args['t_start'],
                          args['t_end'], args['granularity'], args['t_format'], acumulative)


def _get_datetime_iter(t_start, granularity='day',
                       dt_format='%Y-%m-%d %H:%M:%S'):
    """
    Returns an iterator over datetime elements starting at an arbitrary time,
    with granularity of a [year,month,day,hour,minute,second].

    @param t_start: An arbitrary starting time in format %Y-%m-%d %H:%M:%S
    @type t_start: str

    @param granularity: The span between iterable elements, default is 'days'.
                        Possible values are [year,month,day,hour,minute,second].
    @type granularity: str

    @param dt_format: Format of the 't_start' parameter
    @type dt_format: str

    @return: An iterator of points in time
    @type: iterator over datetime elements
    """
    tim = _to_datetime(t_start, dt_format)

    # Make a time increment depending on the granularity and the current time
    # (the length of years and months vary over time)
    span = ""
    while True:
        yield tim

        if granularity == "year":
            span = (calendar.isleap(tim.year) and ["days=366"] or ["days=365"])[0]
        elif granularity == "month":
            span = "days=" + str(calendar.monthrange(tim.year, tim.month)[1])
        elif granularity == "day":
            span = "days=1"
        elif granularity == "hour":
            span = "hours=1"
        elif granularity == "minute":
            span = "minutes=1"
        elif granularity == "second":
            span = "seconds=1"
        else:
            # Default just in case
            span = "days=1"
        tim += eval("datetime.timedelta(" + span + ")")

def _to_datetime(dttime, dt_format='%Y-%m-%d %H:%M:%S'):
    """
    Transforms a string into a datetime
    """
    return datetime.datetime(*time.strptime(dttime, dt_format)[:6])


def _run_cmd(command):
    """
    Runs a certain command and returns the string output. If the command is
    not found a string saying so will be returned. Use with caution!

    @param command: The UNIX command to execute.
    @type command: str

    @return: The std-out from the command.
    @type: str
    """
    return commands.getoutput(command)


def _get_doctypes():
    """Returns all the possible doctypes of a new submission"""
    doctypes = [("all", "All")]
    for doctype in get_docid_docname_alldoctypes():
        doctypes.append(doctype)
    return doctypes


def _get_item_statuses():
    """Returns all the possible status of an item"""
    return [(CFG_BIBCIRCULATION_ITEM_STATUS_CANCELLED, "Cancelled"),
            (CFG_BIBCIRCULATION_ITEM_STATUS_CLAIMED, "Claimed"),
            (CFG_BIBCIRCULATION_ITEM_STATUS_IN_PROCESS, "In process"),
            (CFG_BIBCIRCULATION_ITEM_STATUS_NOT_ARRIVED, "Not arrived"),
            (CFG_BIBCIRCULATION_ITEM_STATUS_ON_LOAN, "On loan"),
            (CFG_BIBCIRCULATION_ITEM_STATUS_ON_ORDER, "On order"),
            (CFG_BIBCIRCULATION_ITEM_STATUS_ON_SHELF, "On shelf")] + \
            [(status, status) for status in CFG_BIBCIRCULATION_ITEM_STATUS_OPTIONAL]


def _get_item_doctype():
    """Returns all the possible types of document for an item"""
    dts = []
    for dat in run_sql("""SELECT DISTINCT(request_type)
        FROM "crcILLREQUEST" ORDER BY request_type ASC"""):
        dts.append((dat[0], dat[0]))
    return dts


def _get_request_statuses():
    """Returns all the possible statuses for an ILL request"""
    dts = []
    for dat in run_sql("""SELECT DISTINCT(status) FROM "crcILLREQUEST" ORDER BY status ASC"""):
        dts.append((dat[0], dat[0]))
    return dts


def _get_libraries():
    """Returns all the possible libraries"""
    dts = []
    for dat in run_sql("""SELECT name FROM "crcLIBRARY" ORDER BY name ASC"""):
        if not CFG_CERN_SITE or not "CERN" in dat[0]: # do not add internal libraries for CERN site
            dts.append((dat[0], dat[0]))
    return dts


def _get_loan_periods():
    """Returns all the possible loan periods for an item"""
    dts = []
    for dat in run_sql("""SELECT DISTINCT(loan_period) FROM "crcITEM" ORDER BY loan_period ASC"""):
        dts.append((dat[0], dat[0]))
    return dts


def _get_tag_name(tag):
    """
    For a specific MARC tag, it returns the human-readable name
    """
    res = run_sql("SELECT name FROM tag WHERE value LIKE %s", ('%' + tag + '%',))
    if res:
        return res[0][0]
    res = run_sql("SELECT name FROM tag WHERE value LIKE %s", ('%' + tag[:-1] + '%',))
    if res:
        return res[0][0]
    return ''

def _get_collection_recids_for_sql_query(coll):
    ids = get_collection_reclist(coll).tolist()
    if len(ids) == 0:
        return ""
    return "id_bibrec IN %s" % str(ids).replace('[', '(').replace(']', ')')

def _check_udc_value_where():
    return "id_bibrec IN (SELECT brb.id_bibrec \
FROM bibrec_bib08x brb, bib08x b WHERE brb.id_bibxxx = b.id AND tag='080__a' \
AND value LIKE %s) "

def _get_udc_truncated(udc):
    if udc[-1] == '*':
        return "%s%%" % udc[:-1]
    if udc[0] == '*':
        return "%%%s" % udc[1:]
    return "%s" % udc

def _check_empty_value(value):
    if len(value) == 0:
        return ""
    else:
        return value[0][0]

def _get_granularity_sql_functions(granularity):
    try:
        return {
            "year": ("YEAR",),
            "month": ("YEAR", "MONTH",),
            "day": ("MONTH", "DAY",),
            "hour": ("DAY", "HOUR",),
            "minute": ("HOUR", "MINUTE",),
            "second": ("MINUTE", "SECOND")
            }[granularity]
    except KeyError:
        return ("MONTH", "DAY",)

def _get_sql_query(creation_time_name, granularity, tables_from, conditions="",
                   extra_select="", dates_range_param="", group_by=True, count=True):
    if len(dates_range_param) == 0:
        dates_range_param = creation_time_name
    conditions = "%s > %%s AND %s < %%s %s" % (dates_range_param, dates_range_param,
                                    len(conditions) > 0 and "AND %s" % conditions or "")
    values = {'creation_time_name': creation_time_name,
         'granularity_sql_function': _get_granularity_sql_functions(granularity)[-1],
         'count': count and ", COUNT(*)" or "",
         'tables_from': tables_from,
         'conditions': conditions,
         'extra_select': extra_select,
         'group_by': ""}
    if group_by:
        values['group_by'] = "GROUP BY "
        for fun in _get_granularity_sql_functions(granularity):
            values['group_by'] += "%s(%s), " % (fun, creation_time_name)
        values['group_by'] = values['group_by'][:-2]
    return "SELECT %(granularity_sql_function)s(%(creation_time_name)s) %(count)s %(extra_select)s \
FROM %(tables_from)s WHERE %(conditions)s \
%(group_by)s \
ORDER BY %(creation_time_name)s DESC" % values
