## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2010, 2011 CERN.
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

__revision__ = "$Id$"
__lastupdated__ = "$Date$"

import calendar, commands, datetime, time, os, cPickle, random
try:
    import xlwt
    xlwt_imported = True
except ImportError:
    xlwt_imported = False
from invenio.config import CFG_TMPDIR, CFG_SITE_URL, CFG_SITE_NAME, CFG_BINDIR
from invenio.urlutils import redirect_to_url
from invenio.search_engine import perform_request_search, \
    get_collection_reclist, \
    get_fieldvalues, \
    get_most_popular_field_values
from invenio.dbquery import run_sql, \
    wash_table_column_name
from invenio.websubmitadmin_dblayer import get_docid_docname_alldoctypes
from invenio.bibcirculation_utils import book_title_from_MARC, \
    book_information_from_MARC
from invenio.bibcirculation_dblayer import get_id_bibrec, \
    get_borrower_data

WEBSTAT_SESSION_LENGTH = 48 * 60 * 60 # seconds
WEBSTAT_GRAPH_TOKENS = '-=#+@$%&XOSKEHBC'

# KEY EVENT TREND SECTION

def get_keyevent_trend_collection_population(args):
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
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    if args.get('collection','All') == 'All':
        sql_query_g = ("SELECT creation_date FROM bibrec WHERE " + \
                     "creation_date > '%s' AND creation_date < '%s' " + \
                     "ORDER BY creation_date DESC") % \
                     (lower, upper)
        sql_query_i = "SELECT COUNT(id) FROM bibrec " + \
                "WHERE creation_date < '%s'" % (lower)
    else:
        ids = perform_request_search(cc=args['collection'])
        if len(ids) == 0:
            return []
        ids_str = str(ids).replace('[', '(').replace(']', ')')
        sql_query_g = ("SELECT creation_date FROM bibrec WHERE id IN %s AND " + \
                     "creation_date > '%s' AND creation_date < '%s' " + \
                     "ORDER BY creation_date DESC") % \
                     (ids_str, lower, upper)
        sql_query_i = "SELECT COUNT(id) FROM bibrec " + \
                "WHERE id IN %s AND creation_date < '%s'" % (ids_str, lower)

    action_dates = [x[0] for x in run_sql(sql_query_g)]
    initial_quantity = run_sql(sql_query_i)[0][0]

    return _get_trend_from_actions(action_dates, initial_quantity,
                                   args['t_start'], args['t_end'],
                                   args['granularity'], args['t_format'])


def get_keyevent_trend_search_frequency(args):
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
    # collect action dates
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    sql = "SELECT date FROM query INNER JOIN user_query ON id=id_query " + \
          "WHERE date > '%s' AND date < '%s' ORDER BY date DESC" % \
          (lower, upper)
    action_dates = [x[0] for x in run_sql(sql)]

    return _get_trend_from_actions(action_dates, 0, args['t_start'],
                          args['t_end'], args['granularity'], args['t_format'])


def get_keyevent_trend_comments_frequency(args):
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
    # collect action dates
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    if args.get('collection','All') == 'All':
        sql = "SELECT date_creation FROM cmtRECORDCOMMENT " + \
          "WHERE date_creation > '%s' AND date_creation < '%s'" \
          % (lower, upper) + " ORDER BY date_creation DESC"
    else:
        ids = get_collection_reclist(args['collection']).tolist()
        if len(ids) == 0:
            return []
        ids_str = str(ids).replace('[', '(').replace(']', ')')
        sql = "SELECT date_creation FROM cmtRECORDCOMMENT \
            WHERE date_creation > '%s' AND date_creation < '%s'  \
            AND id_bibrec IN %s ORDER BY date_creation DESC" \
            % (lower, upper, ids_str)
    action_dates = [x[0] for x in run_sql(sql)]

    return _get_trend_from_actions(action_dates, 0, args['t_start'],
                          args['t_end'], args['granularity'], args['t_format'])


def get_keyevent_trend_search_type_distribution(args):
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
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    # SQL to determine all simple searches:
    sql = "SELECT date FROM query INNER JOIN user_query ON id=id_query " + \
          "WHERE urlargs LIKE '%p=%' " + \
          "AND date > '%s' AND date < '%s' ORDER BY date DESC" % (lower, upper)
    simple = [x[0] for x in run_sql(sql)]

    # SQL to determine all advanced searches:
    sql = "SELECT date FROM query INNER JOIN user_query ON id=id_query " + \
          "WHERE urlargs LIKE '%as=1%' " + \
          "AND date > '%s' AND date < '%s' ORDER BY date DESC" % (lower, upper)
    advanced = [x[0] for x in run_sql(sql)]

    # Compute the trend for both types
    s_trend = _get_trend_from_actions(simple, 0, args['t_start'],
                         args['t_end'], args['granularity'], args['t_format'])
    a_trend = _get_trend_from_actions(advanced, 0, args['t_start'],
                         args['t_end'], args['granularity'], args['t_format'])

    # Assemble, according to return type
    return [(s_trend[i][0], (s_trend[i][1], a_trend[i][1]))
            for i in range(len(s_trend))]


def get_keyevent_trend_download_frequency(args):
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

    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    # Collect list of timestamps of insertion in the specific collection
    if args.get('collection','All') == 'All':
        sql = "SELECT download_time FROM rnkDOWNLOADS WHERE download_time > '%s' \
            AND download_time < '%s'  ORDER BY download_time DESC" % (lower, upper)
    else:
        ids = get_collection_reclist(args['collection']).tolist()
        if len(ids) == 0:
            return []
        ids_str = str(ids).replace('[', '(').replace(']', ')')
        sql = "SELECT download_time FROM rnkDOWNLOADS WHERE download_time > '%s' \
            AND download_time < '%s' AND id_bibrec IN %s \
            ORDER BY download_time DESC" % (lower, upper, ids_str)
    actions = [x[0] for x in run_sql(sql)]

    return _get_trend_from_actions(actions, 0, args['t_start'],
                          args['t_end'], args['granularity'], args['t_format'])


def get_keyevent_trend_number_of_loans(args):
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
    # collect action dates
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    sql = "SELECT loaned_on FROM crcLOAN " + \
          "WHERE loaned_on > '%s' AND loaned_on < '%s' ORDER BY loaned_on DESC"\
          % (lower, upper)
    action_dates = [x[0] for x in run_sql(sql)]

    return _get_trend_from_actions(action_dates, 0, args['t_start'],
                          args['t_end'], args['granularity'], args['t_format'])


def get_keyevent_trend_web_submissions(args):
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
    # collect action dates
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()
    if args['doctype'] == 'all':
        sql_query = "SELECT cd FROM sbmSUBMISSIONS " + \
            "WHERE action='SBI' AND cd > '%s' AND cd < '%s'" % (lower, upper) + \
            " AND status='finished' ORDER BY cd DESC"
    else:
        sql_query = "SELECT cd FROM sbmSUBMISSIONS " + \
            "WHERE doctype='%s' AND action='SBI' " % args['doctype'] + \
            "AND cd > '%s' AND cd < '%s' " % (lower, upper) + \
            "AND status='finished' ORDER BY cd DESC"
    action_dates = [x[0] for x in run_sql(sql_query)]
    return _get_trend_from_actions(action_dates, 0,
                                   args['t_start'], args['t_end'],
                                   args['granularity'], args['t_format'])


def get_keyevent_loan_statistics(args):
    """
    Data:
    - Number of documents (=records) loaned
    - Number of items loaned on the total number of items
    - Number of items never loaned on the total number of items
    - Average time between the date of the record creation and  the date of the first loan
    Filter by
    - in a specified time span
    - by user address (=Department)
    - by UDC (see MARC field 080__a - list to be submitted)
    - by item status (available, missing)
    - by date of publication (MARC field 260__c)
    - by date of the record creation in the database


    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['user_address']: borrower address
    @type args['user_address']: str

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
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcLOAN l "
    sql_where = "WHERE loaned_on > '%s' AND loaned_on < '%s' " % (lower, upper)

    if 'user_address' in args and args['user_address'] != '':
        sql_from += ", crcBORROWER bor "
        sql_where += """AND l.id_crcBORROWER = bor.id AND
             bor.address LIKE '%%%s%%' """ % args['user_address']
    if 'udc' in args and args['udc'] != '':
        sql_where += "AND l.id_bibrec IN ( SELECT brb.id_bibrec \
                  FROM bibrec_bib08x brb, bib08x b \
                  WHERE brb.id_bibxxx = b.id AND tag='080__a' \
                  AND value LIKE '%%%s%%')" % args['udc']
    if 'item_status' in args and args['item_status'] != '':
        sql_from += ", crcITEM i "
        sql_where += "AND l.barcode = i.barcode AND i.status = '%s' " % args['item_status']
    if 'publication_date' in args and args['publication_date'] != '':
        sql_where += "AND l.id_bibrec IN ( SELECT brb.id_bibrec \
                                   FROM bibrec_bib26x brb, bib26x b \
                                   WHERE brb.id_bibxxx = b.id AND tag='260__c' \
                               AND value LIKE '%%%s%%') " % args['publication_date']
    if 'creation_date' in args and args['creation_date'] != '':
        sql_from += ", bibrec br "
        sql_where += """AND br.id=l.id_bibrec AND br.creation_date
            LIKE '%%%s%%' """ % args['creation_date']
    # Number of loans:
    loans = run_sql("SELECT COUNT(DISTINCT l.id_bibrec) " + sql_from + sql_where)[0][0]

    # Number of items loaned on the total number of items:
    items_loaned = run_sql("SELECT COUNT(DISTINCT l.barcode) " + sql_from + sql_where)[0][0]
    total_items = run_sql("SELECT COUNT(*) FROM crcITEM")[0][0]
    loaned_on_total = float(items_loaned) / float(total_items)

    # Number of items never loaned on the total number of items
    never_loaned_on_total = float(total_items - items_loaned) / float(total_items)

    # Average time between the date of the record creation and  the date of the first loan
    avg_sql = "SELECT DATEDIFF(MIN(loaned_on), MIN(br.creation_date)) " + sql_from
    if not ('creation_date' in args and args['creation_date'] != ''):
        avg_sql += ", bibrec br "
    avg_sql += sql_where
    if not ('creation_date' in args and args['creation_date'] != ''):
        avg_sql += "AND br.id=l.id_bibrec "
    avg_sql += "GROUP BY l.id_bibrec, br.id"
    res_avg = run_sql(avg_sql)
    if len(res_avg) > 0:
        avg = res_avg[0][0]
    else:
        avg = 0

    return ((loans, ), (loaned_on_total, ), (never_loaned_on_total, ), (avg, ))


def get_keyevent_loan_lists(args):
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
    - by user address (=Department)

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

    @param args['user_address']: borrower address
    @type args['user_address']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcLOAN l "
    sql_where = "WHERE type = 'normal' AND loaned_on > %s AND loaned_on < %s "
    param = [lower, upper]

    if 'user_address' in args and args['user_address'] != '':
        sql_from += ", crcBORROWER bor "
        sql_where += "AND l.id_crcBORROWER = bor.id AND bor.address LIKE %s "
        param.append('%%%s%%' % args['user_address'])
    if 'udc' in args and args['udc'] != '':
        sql_where += "AND l.id_bibrec IN ( SELECT brb.id_bibrec \
                  FROM bibrec_bib08x brb, bib08x b \
                  WHERE brb.id_bibxxx = b.id AND tag='080__a' \
                  AND value LIKE %s)"
        param.append('%%%s%%' % args['udc'])
    if 'loan_period' in args and args['loan_period'] != '':
        sql_from += ", crcITEM i "
        sql_where += "AND l.barcode = i.barcode AND i.loan_period = %s "
        param.append(args['loan_period'])
    if 'publication_date' in args and args['publication_date'] != '':
        sql_where += "AND l.id_bibrec IN ( SELECT brb.id_bibrec \
                                   FROM bibrec_bib26x brb, bib26x b \
                                   WHERE brb.id_bibxxx = b.id AND tag='260__c' \
                               AND value LIKE %s) "
        param.append('%%%s%%' % args['publication_date'])
    if 'creation_date' in args and args['creation_date'] != '':
        sql_from += ", bibrec br "
        sql_where += "AND br.id=l.id_bibrec AND br.creation_date LIKE %s "
        param.append('%%%s%%' % args['creation_date'])
    param = tuple(param)
    res = [("", "Title", "Author", "Edition", "Number of loans",
            "Number of copies", "Date of creation of the record")]
    # Documents (= records) never loaned:
    for rec, copies in run_sql("""SELECT id_bibrec, COUNT(*) FROM crcITEM WHERE
            id_bibrec NOT IN (SELECT l.id_bibrec """ + sql_from + sql_where +
            ") GROUP BY id_bibrec", param):
        loans = run_sql("SELECT COUNT(*) %s %s AND l.id_bibrec=%s" %
                        (sql_from, sql_where, rec), param)[0][0]
        try:
            creation = run_sql("SELECT creation_date FROM bibrec WHERE id=%s", (rec, ))[0][0]
        except:
            creation = datetime.datetime(1970, 01, 01)
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
        res.append(('Documents never loaned', book_title_from_MARC(rec), author,
                    edition, loans, copies, creation))

    # Most loaned documents
    most_loaned = []
    check_num_loans = ""
    if 'min_loans' in args and args['min_loans'] != '':
        check_num_loans += "COUNT(*) >= %s" % args['min_loans']
    if 'max_loans' in args and args['max_loans'] != '' and args['max_loans'] != 0:
        if check_num_loans != "":
            check_num_loans += " AND "
        check_num_loans += "COUNT(*) <= %s" % args['max_loans']
    if check_num_loans != "":
        check_num_loans = " HAVING " + check_num_loans
    mldocs = run_sql("SELECT l.id_bibrec, COUNT(*) " + sql_from + sql_where +
                " GROUP BY l.id_bibrec " + check_num_loans, param)

    for rec, loans in mldocs:
        copies = run_sql("SELECT COUNT(*) FROM crcITEM WHERE id_bibrec=%s", (rec, ))[0][0]
        most_loaned.append((rec, loans, copies, loans / copies))
    if most_loaned == []:
        return (res)
    most_loaned.sort(cmp=lambda x, y: cmp(x[3], y[3]))
    if len(most_loaned) > 50:
        most_loaned = most_loaned[:49]
    most_loaned.reverse()
    for rec, loans, copies, _ in most_loaned:
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
        try:
            creation = run_sql("SELECT creation_date FROM bibrec WHERE id=%s", (rec, ))[0][0]
        except:
            creation = datetime.datetime(1970, 01, 01)
        res.append(('Most loaned documents', book_title_from_MARC(rec), author,
                    edition, loans, copies, creation))
    return (res)


def get_keyevent_renewals_lists(args):
    """
    Lists:
    - List of most renewed items stored by decreasing order (50 items)
    Filter by
    - in a specified time span
    - by UDC (see MARC field 080__a - list to be submitted)
    - by collection
    - by user address (=Department)

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['udc']: MARC field 080__a
    @type args['udc']: str

    @param args['collection']: collection of the record
    @type args['collection']: str

    @param args['user_address']: borrower address
    @type args['user_address']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcLOAN l, crcITEM i "
    sql_where = "WHERE loaned_on > %s AND loaned_on < %s AND i.barcode = l.barcode "
    param = [lower, upper]
    if 'user_address' in args and args['user_address'] != '':
        sql_from += ", crcBORROWER bor "
        sql_where += "AND l.id_crcBORROWER = bor.id AND bor.address LIKE %s "
        param.append('%%%s%%' % args['user_address'])
    if 'udc' in args and args['udc'] != '':
        sql_where += "AND l.id_bibrec IN ( SELECT brb.id_bibrec \
                  FROM bibrec_bib08x brb, bib08x b \
                  WHERE brb.id_bibxxx = b.id AND tag='080__a' \
                  AND value LIKE %s)"
        param.append('%%%s%%' % args['udc'])
    filter_coll = False
    if 'collection' in args and args['collection'] != '':
        filter_coll = True
        recid_list = get_collection_reclist(args['collection'])

    param = tuple(param)
    # Results:
    res = [("Title", "Author", "Edition", "Number of renewals")]
    for rec, renewals in run_sql("SELECT i.id_bibrec, SUM(number_of_renewals) "
            + sql_from + sql_where +
            " GROUP BY i.id_bibrec ORDER BY SUM(number_of_renewals) DESC LIMIT 50", param):
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


def get_keyevent_returns_table(args):
    """
    Data:
    - Number of overdue returns in a year

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
    returns = run_sql("SELECT COUNT(*) FROM crcLOAN l \
                     WHERE loaned_on > %s AND loaned_on < %s AND \
                         due_date < NOW() AND (returned_on = '0000-00-00 00:00:00' \
                         OR returned_on > due_date)", (lower, upper))[0][0]

    return ((returns, ), )


def get_keyevent_trend_returns_percentage(args):
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
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    # SQL to determine overdue returns:
    sql = "SELECT due_date FROM crcLOAN " + \
          "WHERE  loaned_on > %s AND loaned_on < %s AND " + \
            "due_date < NOW() AND (returned_on = '0000-00-00 00:00:00' " + \
            "OR returned_on > due_date) ORDER BY due_date DESC"
    overdue = [x[0] for x in run_sql(sql, (lower, upper))]

    # SQL to determine all returns:
    sql = "SELECT due_date FROM crcLOAN " + \
          "WHERE loaned_on > %s AND loaned_on < %s AND " + \
           "due_date < NOW() ORDER BY due_date DESC"
    total = [x[0] for x in run_sql(sql, (lower, upper))]

    # Compute the trend for both types
    s_trend = _get_trend_from_actions(overdue, 0, args['t_start'],
                         args['t_end'], args['granularity'], args['t_format'])
    a_trend = _get_trend_from_actions(total, 0, args['t_start'],
                         args['t_end'], args['granularity'], args['t_format'])

    # Assemble, according to return type
    return [(s_trend[i][0], (s_trend[i][1], a_trend[i][1]))
            for i in range(len(s_trend))]


def get_keyevent_ill_requests_statistics(args):
    """
    Data:
    - Number of ILL requests
    - Number of satisfied ILL requests 3 months after the date of request
        creation on a period of one year
    - Percentage of satisfied ILL requests 3 months after the date of
        request creation on a period of one year

    - Average time between the date and  the hour of the ill request
        date and the date and the hour of the delivery item to the user
        on a period of one year (with flexibility in the choice of the dates)
    - Average time between the date and  the hour the ILL request
        was sent to the supplier and the date and hour of the
        delivery item on a period of one year (with flexibility in
        the choice of the dates)

    Filter by
    - in a specified time span
    - by type of document (book or article)
    - by user address
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

    @param args['user_address']: borrower address
    @type args['user_address']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcILLREQUEST ill "
    sql_where = "WHERE period_of_interest_from > %s AND period_of_interest_from < %s "

    param = [lower, upper]

    if 'user_address' in args and args['user_address'] != '':
        sql_from += ", crcBORROWER bor "
        sql_where += "AND ill.id_crcBORROWER = bor.id AND bor.address LIKE %s "
        param.append('%%%s%%' % args['user_address'])
    if 'doctype' in args and args['doctype'] != '':
        sql_where += "AND  ill.request_type=%s"
        param.append(args['doctype'])
    if 'status' in args and args['status'] != '':
        sql_where += "AND ill.status = %s "
        param.append(args['status'])
    if 'supplier' in args and args['supplier'] != '':
        sql_from += ", crcLIBRARY lib "
        sql_where += "AND lib.id=ill.id_crcLIBRARY AND lib.name=%s "
        param.append(args['supplier'])

    param = tuple(param)

    # Number of requests:
    requests = run_sql("SELECT COUNT(*) " + sql_from + sql_where, param)[0][0]

    # Number of satisfied ILL requests 3 months after the date of request creation:
    satrequests = run_sql("SELECT COUNT(*) " + sql_from + sql_where +
                          "AND arrival_date != '0000-00-00 00:00:00' AND \
                          DATEDIFF(arrival_date, period_of_interest_from) < 90 ", param)[0][0]

    # Average time between the date and the hour of the ill request date and
    # the date and the hour of the delivery item to the user
    avgdel = run_sql("SELECT AVG(TIMESTAMPDIFF(HOUR, period_of_interest_from, request_date)) "
                     + sql_from + sql_where, param)[0][0]
    if avgdel is int:
        avgdel = int(avgdel)
    else:
        avgdel = 0
    # Average time between the date and  the hour the ILL request was sent to
    # the supplier and the date and hour of the delivery item
    avgsup = run_sql("SELECT AVG(TIMESTAMPDIFF(HOUR, arrival_date, request_date)) "
                     + sql_from + sql_where, param)[0][0]
    if avgsup is int:
        avgsup = int(avgsup)
    else:
        avgsup = 0

    return ((requests, ), (satrequests, ), (avgdel, ), (avgsup, ))


def get_keyevent_ill_requests_lists(args):
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

    sql_from = "FROM crcILLREQUEST ill "
    sql_where = "WHERE request_date > %s AND request_date < %s "

    param = [lower, upper]

    if 'doctype' in args and args['doctype'] != '':
        sql_where += "AND  ill.request_type=%s"
        param.append(args['doctype'])
    if 'supplier' in args and args['supplier'] != '':
        sql_from += ", crcLIBRARY lib "
        sql_where += "AND lib.id=ill.id_crcLIBRARY AND lib.name=%s "
        param.append(args['supplier'])

    # Results:
    res = [("Title", "Author", "Edition")]
    for item_info in run_sql("SELECT item_info " + sql_from + sql_where + " LIMIT 100", param):
        item_info = eval(item_info[0])
        try:
            res.append((item_info['title'], item_info['authors'], item_info['edition']))
        except KeyError:
            None
    return (res)


def get_keyevent_trend_satisfied_ill_requests_percentage(args):
    """
    Returns the number of satisfied ILL requests 3 months after the date of request
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

    @param args['user_address']: borrower address
    @type args['user_address']: str

    @param args['granularity']: Granularity of date and time
    @type args['granularity']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcILLREQUEST ill "
    sql_where = "WHERE request_date > %s AND request_date < %s "
    param = [lower, upper]

    if 'user_address' in args and args['user_address'] != '':
        sql_from += ", crcBORROWER bor "
        sql_where += "AND ill.id_crcBORROWER = bor.id AND bor.address LIKE %s "
        param.append('%%%s%%' % args['user_address'])
    if 'doctype' in args and args['doctype'] != '':
        sql_where += "AND  ill.request_type=%s"
        param.append(args['doctype'])
    if 'status' in args and args['status'] != '':
        sql_where += "AND ill.status = %s "
        param.append(args['status'])
    if 'supplier' in args and args['supplier'] != '':
        sql_from += ", crcLIBRARY lib "
        sql_where += "AND lib.id=ill.id_crcLIBRARY AND lib.name=%s "
        param.append(args['supplier'])

    # SQL to determine satisfied ILL requests:
    sql = "SELECT request_date " + sql_from + sql_where + \
            "AND ADDDATE(request_date, 90) < NOW() AND (arrival_date != '0000-00-00 00:00:00' " + \
            "OR arrival_date < ADDDATE(request_date, 90)) ORDER BY request_date DESC"
    satisfied = [x[0] for x in run_sql(sql, param)]

    # SQL to determine all ILL requests:
    sql = "SELECT request_date " + sql_from + sql_where + \
           " AND ADDDATE(request_date, 90) < NOW() ORDER BY request_date DESC"
    total = [x[0] for x in run_sql(sql, param)]

    # Compute the trend for both types
    s_trend = _get_trend_from_actions(satisfied, 0, args['t_start'],
                         args['t_end'], args['granularity'], args['t_format'])
    a_trend = _get_trend_from_actions(total, 0, args['t_start'],
                         args['t_end'], args['granularity'], args['t_format'])

    # Assemble, according to return type
    return [(s_trend[i][0], (s_trend[i][1], a_trend[i][1]))
            for i in range(len(s_trend))]


def get_keyevent_items_statistics(args):
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
        sql_where += "i.id_bibrec IN ( SELECT brb.id_bibrec \
                  FROM bibrec_bib08x brb, bib08x b \
                  WHERE brb.id_bibxxx = b.id AND tag='080__a' \
                  AND value LIKE %s)"
        param.append('%%%s%%' % args['udc'])

    # Number of items:
    if sql_where == "WHERE ":
        sql_where = ""
    items = run_sql("SELECT COUNT(i.id_bibrec) " + sql_from + sql_where, param)[0][0]

    # Number of new items:
    param += [lower, upper]
    if sql_where == "":
        sql_where = "WHERE creation_date > %s AND creation_date < %s "
    else:
        sql_where += " AND creation_date > %s AND creation_date < %s "
    new_items = run_sql("SELECT COUNT(i.id_bibrec) " + sql_from + sql_where, param)[0][0]

    return ((items, ), (new_items, ))


def get_keyevent_items_lists(args):
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

    # Results:
    res = [("Title", "Author", "Edition", "Barcode", "Publication date")]
    if sql_where == "WHERE ":
        sql_where = ""
    if len(param) == 0:
        sqlres = run_sql("SELECT i.barcode, i.id_bibrec " +
                       sql_from + sql_where + " LIMIT 100")
    else:
        sqlres = run_sql("SELECT i.barcode, i.id_bibrec " +
                       sql_from + sql_where + " LIMIT 100", tuple(param))
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


def get_keyevent_loan_request_statistics(args):
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

    custom_table = get_customevent_table("loanrequest")
    # Number of hold requests, one week after the date of request creation:
    holds = run_sql("""SELECT COUNT(*) %s, %s ws %s AND ws.request_id=lr.id AND
        DATEDIFF(ws.creation_time, lr.request_date) >= 7""" %
        (sql_from, custom_table, sql_where), param)[0][0]

    # Number of successful hold requests transactions
    succesful_holds = run_sql("SELECT COUNT(*) %s %s AND lr.status='done'" %
                              (sql_from, sql_where), param)[0][0]

    # Average time between the hold request date and the date of delivery document in a year
    avg = run_sql("""SELECT AVG(DATEDIFF(ws.creation_time, lr.request_date))
        %s, %s ws %s AND ws.request_id=lr.id""" %
        (sql_from, custom_table, sql_where), param)[0][0]

    if avg is int:
        avg = int(avg)
    else:
        avg = 0
    return ((holds, ), (succesful_holds, ), (avg, ))


def get_keyevent_loan_request_lists(args):
    """
    Lists:
    - List of the most requested items
    Filter by
    - in a specified time span
    - by UDC (see MARC field 080__a - list to be submitted)
    - by user address (=Department)

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['udc']: MARC field 080__a
    @type args['udc']: str

    @param args['user_address']: borrower address
    @type args['user_address']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from = "FROM crcLOANREQUEST lr "
    sql_where = "WHERE request_date > %s AND request_date < %s "

    param = [lower, upper]

    if 'user_address' in args and args['user_address'] != '':
        sql_from += ", crcBORROWER bor "
        sql_where += "AND lr.id_crcBORROWER = bor.id AND bor.address LIKE %s "
        param.append('%%%s%%' % args['user_address'])
    if 'udc' in args and args['udc'] != '':
        sql_where += "AND lr.id_bibrec IN ( SELECT brb.id_bibrec \
                  FROM bibrec_bib08x brb, bib08x b \
                  WHERE brb.id_bibxxx = b.id AND tag='080__a' \
                  AND value LIKE %s)"
        param.append('%%%s%%' % args['udc'])

    res = [("Title", "Author", "Edition", "Barcode")]

    # Most requested items:
    for barcode in run_sql("SELECT lr.barcode " + sql_from + sql_where +
                           " GROUP BY barcode ORDER BY COUNT(*) DESC", param):
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


def get_keyevent_user_statistics(args):
    """
    Data:
    - Total number of  active users (to be defined = at least one transaction in the past year)
    Filter by
    - in a specified time span
    - by user address
    - by registration date

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['user_address']: borrower address
    @type args['user_address']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from_ill = "FROM crcILLREQUEST ill "
    sql_from_loan = "FROM crcLOAN l "
    sql_where_ill = "WHERE request_date > %s AND request_date < %s "
    sql_where_loan = "WHERE loaned_on > %s AND loaned_on < %s "
    sql_address = ""
    param = [lower, upper, lower, upper]
    if 'user_address' in args and args['user_address'] != '':
        sql_address += ", crcBORROWER bor WHERE id = user AND \
                       address LIKE %s "
        param.append('%%%s%%' % args['user_address'])

    # Total number of  active users:
    users = run_sql("""SELECT COUNT(DISTINCT user)
        FROM ((SELECT id_crcBORROWER user %s %s) UNION
        (SELECT id_crcBORROWER user %s %s)) res %s""" %
        (sql_from_ill, sql_where_ill, sql_from_loan,
         sql_where_loan, sql_address), param)[0][0]

    return ((users, ), )


def get_keyevent_user_lists(args):
    """
    Lists:
    - List of most intensive users (ILL requests + Loan)
    Filter by
    - in a specified time span
    - by user address
    - by registration date

    @param args['t_start']: Date and time of start point
    @type args['t_start']: str

    @param args['t_end']: Date and time of end point
    @type args['t_end']: str

    @param args['user_address']: borrower address
    @type args['user_address']: str

    @param args['t_format']: Date and time formatting string
    @type args['t_format']: str
    """
    lower = _to_datetime(args['t_start'], args['t_format']).isoformat()
    upper = _to_datetime(args['t_end'], args['t_format']).isoformat()

    sql_from_ill = "FROM crcILLREQUEST ill "
    sql_from_loan = "FROM crcLOAN l "
    sql_where_ill = "WHERE request_date > %s AND request_date < %s "
    sql_where_loan = "WHERE loaned_on > %s AND loaned_on < %s "
    sql_address = ""
    param = [lower, upper, lower, upper]
    if 'user_address' in args and args['user_address'] != '':
        sql_address += ", crcBORROWER bor WHERE id = user AND \
                       address LIKE %s "
        param.append('%%%s%%' % args['user_address'])

    res = [("Name", "Address", "Mailbox", "E-mail", "Number of transactions")]

    # List of most intensive users (ILL requests + Loan):
    for borrower_id, trans in run_sql("SELECT user, SUM(trans) FROM \
             ((SELECT id_crcBORROWER user, COUNT(*) trans %s %s GROUP BY id_crcBORROWER) UNION \
             (SELECT id_crcBORROWER user, COUNT(*) trans %s %s GROUP BY id_crcBORROWER)) res %s \
             GROUP BY user ORDER BY SUM(trans) DESC"
    % (sql_from_ill, sql_where_ill, sql_from_loan, sql_where_loan, sql_address), param):
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
    sql = "SELECT status, COUNT(status) FROM schTASK GROUP BY status"
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
    loans, renewals, returns = run_sql("""SELECT COUNT(*),
        SUM(number_of_renewals), COUNT(returned_on<>'0000-00-00')
        FROM crcLOAN WHERE loaned_on > %s""", (datefrom, ))[0]
    illrequests = run_sql("SELECT COUNT(*) FROM crcILLREQUEST WHERE request_date > %s",
                          (datefrom, ))[0][0]
    holdrequest = run_sql("SELECT COUNT(*) FROM crcLOANREQUEST WHERE request_date > %s",
                          (datefrom, ))[0][0]
    return (loans, renewals, returns, illrequests, holdrequest)

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

    sql_query = ["SELECT creation_time FROM %s WHERE creation_time > '%s'"
                 % (tbl_name, lower)]
    sql_query.append("AND creation_time < '%s'" % upper)
    sql_param = []
    for col_bool, col_title, col_content in args['cols']:
        if not col_title in col_names:
            continue
        if col_content:
            if col_bool == "and" or col_bool == "":
                sql_query.append("AND %s"
                                 % wash_table_column_name(col_title))
            elif col_bool == "or":
                sql_query.append("OR %s"
                                 % wash_table_column_name(col_title))
            elif col_bool == "and_not":
                sql_query.append("AND NOT %s"
                                 % wash_table_column_name(col_title))
            else:
                continue
            sql_query.append(" LIKE %s")
            sql_param.append("%" + col_content + "%")
    sql_query.append("ORDER BY creation_time DESC")
    sql = ' '.join(sql_query)

    dates = [x[0] for x in run_sql(sql, tuple(sql_param))]
    return _get_trend_from_actions(dates, 0, args['t_start'], args['t_end'],
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
        sql_query = ["SELECT * FROM %s WHERE creation_time > '%s'" % (tbl_name,
                                 lower)] # Note: SELECT * technique is okay here
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
                    "SELECT cols FROM staEVENT WHERE id = %s",
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
        "SELECT CONCAT('staEVENT', number) FROM staEVENT WHERE id = %s", (event_id, ))
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
    res = run_sql("SELECT cols FROM staEVENT WHERE id = %s", (event_id, ))
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
    @param year: Year of publication on the journal
    @type year: int

    @param query: Search query to make customized report
    @type query: str

    @param tag: MARC tag for the output
    @type tag: str
    """

    # Check arguments
    if tag == '':
        tag = "909C4p"

    # First get records of the year
    recids = perform_request_search(p=query, of="id")

    # Then return list by tag
    pub = list(get_most_popular_field_values(recids, tag))

    sel = 0
    for elem in pub:
        sel += elem[1]
    if len(pub) == 0:
        return []
    if len(recids) - sel != 0:
        pub.append(('Others', len(recids) - sel))
    pub.append(('TOTAL', len(recids)))

    return pub


def create_custom_summary_graph(data, path, title):
    """
    Creates a pie chart with the information from the custom summary and
    saves it in the file specified by the path argument
    """
    # If no input, we don't bother about anything
    if len(data) == 0:
        return
    os.environ['HOME'] = CFG_TMPDIR

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return
    # make a square figure and axes
    matplotlib.rcParams['font.size'] = 8
    labels = [x[0] for x in data]
    numb_elem = float(len(labels))
    width = 6 + numb_elem / 7
    gfile = plt.figure(1, figsize=(width, 6))

    plt.axes([0.1, 0.1, 4.2 / width, 0.7])

    numb = [x[1] for x in data]
    total = sum(numb)
    fracs = [x * 100 / total for x in numb]
    colors = []

    random.seed()
    for i in range(numb_elem):
        col = 0.5 + float(i) / (numb_elem * 2.0)
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
    if len(trend) == 0:
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
        print out
    else:
        open(path, 'w').write(out)


def create_graph_trend_gnu_plot(trend, path, settings):
    """Creates the graph trend using the GNU plot library"""
    try:
        import Gnuplot
    except ImportError:
        return

    gnup = Gnuplot.Gnuplot()

    gnup('set style data linespoints')
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
        y_max = max(data)
        y_min = min(data)
        if y_max - y_min < 5 and y_min != 0:
            gnup('set ytic %d, 1, %d' % (y_min - 1, y_max + 2))
        elif y_max < 5:
            gnup('set ytic 1')
        gnup.plot(data)


def create_graph_trend_flot(trend, path, settings):
    """Creates the graph trend using the flot library"""
    out = """<!--[if IE]><script language="javascript" type="text/javascript"
                    src="%(site)s/js/excanvas.min.js"></script><![endif]-->
              <script language="javascript" type="text/javascript" src="%(site)s/js/jquery.min.js"></script>
              <script language="javascript" type="text/javascript" src="%(site)s/js/jquery.flot.min.js"></script>
              <script language="javascript" type="text/javascript" src="%(site)s/js/jquery.flot.selection.min.js"></script>
              <script id="source" language="javascript" type="text/javascript">
                     document.write('<div style="float:left"><div id="placeholder" style="width:500px;height:400px"></div></div>'+
              '<div id="miniature" style="float:left;margin-left:20px;margin-top:50px">' +
              '<div id="overview" style="width:250px;height:200px"></div>' +
              '<p id="overviewLegend" style="margin-left:10px"></p>' +
              '</div>');
                     $(function () {
                             function parseDate(sdate){
                                 var div1 = sdate.split(' ');
                                 var day = div1[0].split('-');
                                 var hour = div1[1].split(':');
                                 return new Date(day[0], day[1]-1, day[2], hour[0], hour[1], hour[2]).getTime()
                                 - (new Date().getTimezoneOffset() * 60 * 1000) ;
                             }
                             function getData() {""" % \
        {'site': CFG_SITE_URL}
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
                out += '[parseDate("%s"),%d]' % \
                    (_to_datetime(trend[row][0], '%Y-%m-%d \
                     %H:%M:%S'), trend[row][1][col])
            out += "];\n"
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
            out += '[parseDate("%s"),%d]' % \
                (_to_datetime(trend[row][0], '%Y-%m-%d %H:%M:%S'),
                 trend[row][1])
        out += """];
                     return [d1];
                      }
            """


    # Set options
    tics = ""
    if settings["xtic_format"] != '':
        tics = 'xaxis: { mode:"time",min:parseDate("%s"),max:parseDate("%s")},'\
            % (_to_datetime(minx, '%Y-%m-%d %H:%M:%S'),
               _to_datetime(maxx, '%Y-%m-%d %H:%M:%S'))
    tics += """
        yaxis: {
                tickDecimals : 0
        },
        """
    out += """var options ={
                series: {
                   lines: { show: true },
                   points: { show: false }
                },
                legend: { show : false},
                %s
                grid: { hoverable: true, clickable: true },
                selection: { mode: "xy" }
                };
                """ % tics
        # Write the plot method in javascript

    out += """var startData = getData();
        var plot = $.plot($("#placeholder"), startData, options);
        var overview = $.plot($("#overview"), startData, {
                 legend: { show: true, container: $("#overviewLegend") },
                 series: {
                    lines: { show: true, lineWidth: 1 },
                    shadowSize: 0
                 },
                 %s
                 grid: { color: "#999" },
                 selection: { mode: "xy" }
               });
               """ % tics

        # Tooltip and zoom
    out += """    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
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

    var previousPoint = null;
    $("#placeholder").bind("plothover", function (event, pos, item) {

        if (item) {
            if (previousPoint != item.datapoint) {
                previousPoint = item.datapoint;

                $("#tooltip").remove();
                var y = item.datapoint[1];

                showTooltip(item.pageX, item.pageY, y);
            }
        }
        else {
            $("#tooltip").remove();
            previousPoint = null;
        }
    });

    $("#placeholder").bind("plotclick", function (event, pos, item) {
        if (item) {
            plot.highlight(item.series, item.datapoint);
        }
    });
        $("#placeholder").bind("plotselected", function (event, ranges) {
        // clamp the zooming to prevent eternal zoom

        if (ranges.xaxis.to - ranges.xaxis.from < 0.00001){
            ranges.xaxis.to = ranges.xaxis.from + 0.00001;}
        if (ranges.yaxis.to - ranges.yaxis.from < 0.00001){
            ranges.yaxis.to = ranges.yaxis.from + 0.00001;}

        // do the zooming
        plot = $.plot($("#placeholder"), startData,
                      $.extend(true, {}, options, {
                          xaxis: { min: ranges.xaxis.from, max: ranges.xaxis.to },
                          yaxis: { min: ranges.yaxis.from, max: ranges.yaxis.to }
                      }));

        // don't fire event on the overview to prevent eternal loop
        overview.setSelection(ranges, true);
    });
    $("#overview").bind("plotselected", function (event, ranges) {
        plot.setSelection(ranges);
    });
});
                </script>
<noscript>Your browser does not support JavaScript!
Please, select another output format</noscript>"""
    open(path, 'w').write(out)


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
        print out
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


def export_to_excel(data, req):
    """
    Exports the data to excel.

    @param data: The Python data that should be exported
    @type data: []

    @param req: The Apache request object
    @type req:
    """
    if not xlwt_imported:
        raise Exception("Module xlwt not installed")
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
                            t_start, t_end, granularity, dt_format):
    """
    Given a list of dates reflecting some sort of action/event, and some additional parameters,
    an internal data format is returned. 'initial_value' set to zero, means that the frequency
    will not be accumulative, but rather non-causal.

    @param action_dates: A list of dates, indicating some sort of action/event.
    @type action_dates: [datetime.datetime]

    @param initial_value: The numerical offset the first action's value should make use of.
    @type initial_value: int

    @param t_start: Start time for the time domain in format %Y-%m-%d %H:%M:%S
    @type t_start: str

    @param t_stop: End time for the time domain in format %Y-%m-%d %H:%M:%S
    @type t_stop: str

    @param granularity: The granularity of the time domain, span between values.
                        Possible values are [year,month,day,hour,minute,second].
    @type granularity: str

    @param dt_format: Format of the 't_start' and 't_stop' parameters
    @type dt_format: str

    @return: A list of tuples zipping a time-domain and a value-domain
    @type: [(str, int)]
    """
    # Append the maximum date as a sentinel indicating we're done
    action_dates.insert(0, datetime.datetime.max)

    # Create an iterator running from the first day of activity
    dt_iter = _get_datetime_iter(t_start, granularity, dt_format)

    # Construct the datetime tuple for the stop time
    stop_at = _to_datetime(t_end, dt_format) - datetime.timedelta(seconds=1)

    # If our t_start is more recent than the initial action_dates, we need to
    # drop those.
    t_start_dt = _to_datetime(t_start, dt_format)
    while action_dates[-1] < t_start_dt:
        action_dates = action_dates[:-1]

    vector = [(None, initial_value)]
    # pylint: disable=E1101
    old = dt_iter.next()
    # pylint: enable=E1101
    upcoming_action = action_dates.pop()

    for current in dt_iter:
        # Counter of action_dates in the current span, set the initial value to
        # zero to avoid accumlation.
        if initial_value != 0:
            actions_here = vector[-1][1]
        else:
            actions_here = 0

        # Check to see if there's an action date in the current span
        while old <= upcoming_action < current:
            actions_here += 1
            try:
                upcoming_action = action_dates.pop()
            except IndexError:
                upcoming_action = datetime.datetime.max

        vector.append((old.strftime('%Y-%m-%d %H:%M:%S'), actions_here))
        old = current

        # Make sure to stop the iteration at the end time
        if current > stop_at:
            break

    # Remove the first bogus tuple, and return
    return vector[1:]


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

    @param format: Format of the 't_start' parameter
    @type format: str

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
    return [("available", "Available"), ("requested", "Requested"),
            ("on loan", "On loan"), ("missing", "Missing")]


def _get_item_doctype():
    """Returns all the possible types of document for an item"""
    dts = []
    for dat in run_sql("""SELECT DISTINCT(request_type)
        FROM crcILLREQUEST ORDER BY request_type ASC"""):
        dts.append((dat[0], dat[0]))
    return dts


def _get_request_statuses():
    """Returns all the possible statuses for an ILL request"""
    dts = []
    for dat in run_sql("SELECT DISTINCT(status) FROM crcILLREQUEST ORDER BY status ASC"):
        dts.append((dat[0], dat[0]))
    return dts


def _get_libraries():
    """Returns all the possible libraries"""
    dts = []
    for dat in run_sql("SELECT name FROM crcLIBRARY ORDER BY name ASC"):
        dts.append((dat[0], dat[0]))
    return dts


def _get_loan_periods():
    """Returns all the possible loan periods for an item"""
    dts = []
    for dat in run_sql("SELECT DISTINCT(loan_period) FROM crcITEM ORDER BY loan_period ASC"):
        dts.append((dat[0], dat[0]))
    return dts


def _get_tag_name(tag):
    """
    For a specific MARC tag, it returns the human-readable name
    """
    res = run_sql("SELECT name FROM tag WHERE value LIKE '%%%s%%'" % (tag))
    if res:
        return res[0][0]
    res = run_sql("SELECT name FROM tag WHERE value LIKE '%%%s%%'" % (tag[:-1]))
    if res:
        return res[0][0]
    return ''
