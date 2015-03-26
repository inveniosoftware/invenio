# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Alert engine implementation."""

# rest of the Python code goes below

__revision__ = "$Id$"

from cgi import parse_qs
from re import search, sub
from time import strftime
import datetime

from invenio.config import \
     CFG_LOGDIR, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_URL, \
     CFG_WEBALERT_SEND_EMAIL_NUMBER_OF_TRIES, \
     CFG_WEBALERT_SEND_EMAIL_SLEEPTIME_BETWEEN_TRIES, \
     CFG_SITE_NAME, \
     CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL
from invenio.legacy.webbasket.db_layer import get_basket_owner_id, add_to_basket
from invenio.legacy.webbasket.api import format_external_records
from invenio.legacy.search_engine import perform_request_search, \
     check_user_can_view_record
from invenio.ext.legacy.handler import wash_urlargd
from invenio.legacy.dbquery import run_sql
from invenio.legacy.webuser import get_email, collect_user_info
from invenio.ext.email import send_email
from invenio.ext.logging import register_exception
from invenio.legacy.webalert.alert_engine_config import CFG_WEBALERT_DEBUG_LEVEL

from invenio.legacy.websearch_external_collections.config import \
CFG_EXTERNAL_COLLECTION_TIMEOUT, \
CFG_EXTERNAL_COLLECTION_MAXRESULTS_ALERTS
from invenio.legacy.websearch_external_collections.getter import HTTPAsyncPageGetter, async_download
from invenio.legacy.websearch_external_collections.utils import get_collection_id
from invenio.modules.collections.models import Collection

import invenio.legacy.template
websearch_templates = invenio.legacy.template.load('websearch')
webalert_templates = invenio.legacy.template.load('webalert')

def update_date_lastrun(alert):
    """Update the last time this alert was ran in the database."""

    return run_sql('update user_query_basket set date_lastrun=%s where id_user=%s and id_query=%s and id_basket=%s;', (strftime("%Y-%m-%d"), alert[0], alert[1], alert[2],))

def get_alert_queries(frequency):
    """Return all the queries for the given frequency."""

    return run_sql('select distinct id, urlargs from query q, user_query_basket uqb where q.id=uqb.id_query and uqb.frequency=%s and uqb.date_lastrun <= now();', (frequency,))

def get_alert_queries_for_user(uid):
    """Returns all the queries for the given user id."""

    return run_sql('select distinct id, urlargs, uqb.frequency from query q, user_query_basket uqb where q.id=uqb.id_query and uqb.id_user=%s and uqb.date_lastrun <= now();', (uid,))

def get_alerts(query, frequency):
    """Returns a dictionary of all the records found for a specific query and frequency along with other informationm"""

    r = run_sql('select id_user, id_query, id_basket, frequency, date_lastrun, alert_name, notification, alert_desc, alert_recipient from user_query_basket where id_query=%s and frequency=%s;', (query['id_query'], frequency,))
    return {'alerts': r, 'records': query['records'], 'argstr': query['argstr'], 'date_from': query['date_from'], 'date_until': query['date_until']}

def add_records_to_basket(records, basket_id):
    """Add the given records to the given baskets"""

    index = 0
    owner_uid = get_basket_owner_id(basket_id)
    # We check that the owner of the recipient basket would be allowed
    # to view the records. This does not apply to external records
    # (hosted collections).
    user_info = collect_user_info(owner_uid)
    filtered_records = ([], records[1])
    filtered_out_recids = [] # only set in debug mode
    for recid in records[0]:
        (auth_code, auth_msg) = check_user_can_view_record(user_info, recid)
        if auth_code == 0:
            filtered_records[0].append(recid)
        elif CFG_WEBALERT_DEBUG_LEVEL > 2:
            # only keep track of this in DEBUG mode
            filtered_out_recids.append(recid)

    nrec = len(filtered_records[0])
    index += nrec
    if index > CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
        index = CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL
    if nrec > 0:
        nrec_to_add = nrec < index and nrec or index
        if CFG_WEBALERT_DEBUG_LEVEL > 0:
            print("-> adding %i records into basket %s: %s" % (nrec_to_add, basket_id, filtered_records[0][:nrec_to_add]))
            if nrec > nrec_to_add:
                print("-> not added %i records into basket %s: %s due to maximum limit restrictions." % (nrec - nrec_to_add, basket_id, filtered_records[0][nrec_to_add:]))
        try:
            if CFG_WEBALERT_DEBUG_LEVEL == 0:
                add_to_basket(owner_uid, filtered_records[0][:nrec_to_add], 0, basket_id)
            else:
                print('   NOT ADDED, DEBUG LEVEL > 0')
        except Exception:
            register_exception()

    if CFG_WEBALERT_DEBUG_LEVEL > 2 and filtered_out_recids:
        print("-> these records have been filtered out, as user id %s did not have access:\n%s" % \
              (owner_uid, repr(filtered_out_recids)))

    if index < CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
        for external_collection_results in filtered_records[1][0]:
            nrec = len(external_collection_results[1][0])
            # index_tmp: the number of maximum allowed records to be added to
            # the basket for the next collection.
            index_tmp = CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL - index
            index += nrec
            if index > CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
                index = CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL
            if nrec > 0 and index_tmp > 0:
                nrec_to_add = nrec < index_tmp and nrec or index_tmp
                if CFG_WEBALERT_DEBUG_LEVEL > 0:
                    print("-> adding %s external records (collection \"%s\") into basket %s: %s" % (nrec_to_add, external_collection_results[0], basket_id, external_collection_results[1][0][:nrec_to_add]))
                    if nrec > nrec_to_add:
                        print("-> not added %s external records (collection \"%s\") into basket %s: %s due to maximum limit restriction" % (nrec - nrec_to_add, external_collection_results[0], basket_id, external_collection_results[1][0][nrec_to_add:]))
                try:
                    if CFG_WEBALERT_DEBUG_LEVEL == 0:
                        collection_id = get_collection_id(external_collection_results[0])
                        added_items = add_to_basket(owner_uid, external_collection_results[1][0][:nrec_to_add], collection_id, basket_id)
                        format_external_records(added_items, of="xm")
                    else:
                        print('   NOT ADDED, DEBUG LEVEL > 0')
                except Exception:
                    register_exception()
            elif nrec > 0 and CFG_WEBALERT_DEBUG_LEVEL > 0:
                print("-> not added %s external records (collection \"%s\") into basket %s: %s due to maximum limit restriction" % (nrec, external_collection_results[0], basket_id, external_collection_results[1][0]))
    elif CFG_WEBALERT_DEBUG_LEVEL > 0:
        for external_collection_results in filtered_records[1][0]:
            nrec = len(external_collection_results[1][0])
            if nrec > 0:
                print("-> not added %i external records (collection \"%s\") into basket %s: %s due to maximum limit restrictions" % (nrec, external_collection_results[0], basket_id, external_collection_results[1][0]))

def get_query(alert_id):
    """Returns the query for that corresponds to this alert id."""

    r = run_sql('select urlargs from query where id=%s', (alert_id,))
    return r[0][0]

def email_notify(alert, records, argstr):
    """Send the notification e-mail for a specific alert."""
    if CFG_WEBALERT_DEBUG_LEVEL > 2:
        print("+" * 80 + '\n')
    uid = alert[0]
    user_info = collect_user_info(uid)
    frequency = alert[3]
    alert_name = alert[5]
    alert_description = alert[7]
    alert_recipient_email = alert[8] # set only by admin. Bypasses access-right checks.
    filtered_out_recids = [] # only set in debug mode

    if not alert_recipient_email:
        # Filter out records that user (who setup the alert) should
        # not see. This does not apply to external records (hosted
        # collections).
        filtered_records = ([], records[1])
        for recid in records[0]:
            (auth_code, auth_msg) = check_user_can_view_record(user_info, recid)
            if auth_code == 0:
                filtered_records[0].append(recid)
            elif CFG_WEBALERT_DEBUG_LEVEL > 2:
                # only keep track of this in DEBUG mode
                filtered_out_recids.append(recid)
    else:
        # If admin has decided to send to some mailing-list, we cannot
        # verify that recipients have access to the records. So keep
        # all of them.
        filtered_records = records

    if len(filtered_records[0]) == 0:
        total_n_external_records = 0
        for external_collection_results in filtered_records[1][0]:
            total_n_external_records += len(external_collection_results[1][0])
        if total_n_external_records == 0:
            return

    msg = ""

    if CFG_WEBALERT_DEBUG_LEVEL > 2 and filtered_out_recids:
        print("-> these records have been filtered out, as user id %s did not have access:\n%s" % \
              (uid, repr(filtered_out_recids)))

    if CFG_WEBALERT_DEBUG_LEVEL > 0:
        msg = "*** THIS MESSAGE WAS SENT IN DEBUG MODE ***\n\n"

    url = CFG_SITE_URL + "/search?" + argstr

    # Extract the pattern, the collection list, the current collection
    # and the sc (split collection) from the formatted query
    query = parse_qs(argstr)
    pattern = query.get('p', [''])[0]
    collection_list = query.get('c', [])
    current_collection = query.get('cc', [''])
    sc = query.get('sc', ['1'])
    collections = calculate_desired_collection_list(collection_list, current_collection, int(sc[0]))

    msg += webalert_templates.tmpl_alert_email_body(alert_name,
                                                    alert_description,
                                                    url,
                                                    filtered_records,
                                                    pattern,
                                                    collections,
                                                    frequency,
                                                    alert_use_basket_p(alert))

    email = alert_recipient_email or get_email(uid)

    if email == 'guest':
        print("********************************************************************************")
        print("The following alert was not send, because cannot detect user email address:")
        print("   " + repr(argstr))
        print("********************************************************************************")
        return

    if CFG_WEBALERT_DEBUG_LEVEL > 0:
        print("********************************************************************************")
        print(msg)
        print("********************************************************************************")

    if CFG_WEBALERT_DEBUG_LEVEL < 2:
        send_email(fromaddr=webalert_templates.tmpl_alert_email_from(),
                   toaddr=email,
                   subject=webalert_templates.tmpl_alert_email_title(alert_name),
                   content=msg,
                   header='',
                   footer='',
                   attempt_times=CFG_WEBALERT_SEND_EMAIL_NUMBER_OF_TRIES,
                   attempt_sleeptime=CFG_WEBALERT_SEND_EMAIL_SLEEPTIME_BETWEEN_TRIES)
    if CFG_WEBALERT_DEBUG_LEVEL == 4:
        send_email(fromaddr=webalert_templates.tmpl_alert_email_from(),
                   toaddr=CFG_SITE_ADMIN_EMAIL,
                   subject=webalert_templates.tmpl_alert_email_title(alert_name),
                   content=msg,
                   header='',
                   footer='',
                   attempt_times=CFG_WEBALERT_SEND_EMAIL_NUMBER_OF_TRIES,
                   attempt_sleeptime=CFG_WEBALERT_SEND_EMAIL_SLEEPTIME_BETWEEN_TRIES)

def _date_to_tuple(date):
    """Private function. Converts a date as a tuple of string into a list of integers."""

    return [int(part) for part in (date.year, date.month, date.day)]

def get_record_ids(argstr, date_from, date_until):
    """Returns the local and external records found for a specific query and timeframe."""

    argd = wash_urlargd(parse_qs(argstr), websearch_templates.search_results_default_urlargd)
    p       = argd.get('p', [])
    c       = argd.get('c', [])
    cc      = argd.get('cc', [])
    aas     = argd.get('aas', [])
    f       = argd.get('f', [])
    so      = argd.get('so', [])
    sp      = argd.get('sp', [])
    ot      = argd.get('ot', [])
    p1      = argd.get('p1', [])
    f1      = argd.get('f1', [])
    m1      = argd.get('m1', [])
    op1     = argd.get('op1', [])
    p2      = argd.get('p2', [])
    f2      = argd.get('f2', [])
    m2      = argd.get('m2', [])
    op2     = argd.get('op3', [])
    p3      = argd.get('p3', [])
    f3      = argd.get('f3', [])
    m3      = argd.get('m3', [])
    sc      = argd.get('sc', [])

    d1y, d1m, d1d = _date_to_tuple(date_from)
    d2y, d2m, d2d = _date_to_tuple(date_until)

    #alerts might contain collections that have been deleted
    #check if such collections are in the query, and if yes, do not include them in the search
    cc = Collection.query.filter_by(name=cc).value('name')
    if not cc and not c: #the alarm was for an entire collection that does not exist anymore
        return ([], ([], []))
    if c: # some collections were defined in the query
        c = [c_norm_name for c_norm_name in [
            Collection.query.filter_by(name=c_name).value('name')
            for c_name in c] if c_norm_name]
        # remove unknown collections from c
        if not c: #none of the collection selected in the alert still exist
            return ([], ([], []))

    # washed_colls = wash_colls(cc, c, sc, 0)
    # hosted_colls = washed_colls[3]
    # if hosted_colls:
    #     req_args = "p=%s&f=%s&d1d=%s&d1m=%s&d1y=%s&d2d=%s&d2m=%s&d2y=%s&ap=%i" % (p, f, d1d, d1m, d1y, d2d, d2m, d2y, 0)
    #     external_records = calculate_external_records(req_args, [p, p1, p2, p3], f, hosted_colls, CFG_EXTERNAL_COLLECTION_TIMEOUT, CFG_EXTERNAL_COLLECTION_MAXRESULTS_ALERTS)
    # else:
    # FIXME: removed support for hosted collections
    external_records = ([], [])

    recids = perform_request_search(of='id', p=p, c=c, cc=cc, f=f, so=so, sp=sp, ot=ot,
                                  aas=aas, p1=p1, f1=f1, m1=m1, op1=op1, p2=p2, f2=f2,
                                  m2=m2, op2=op2, p3=p3, f3=f3, m3=m3, sc=sc, d1y=d1y,
                                  d1m=d1m, d1d=d1d, d2y=d2y, d2m=d2m, d2d=d2d)

    return (recids, external_records)

def run_query(query, frequency, date_until):
    """Return a dictionary containing the information of the performed query.

    The information contains the id of the query, the arguments as a
    string, and the list of found records."""

    if frequency == 'day':
        date_from = date_until - datetime.timedelta(days=1)

    elif frequency == 'week':
        date_from = date_until - datetime.timedelta(weeks=1)

    else:
        # Months are not an explicit notion of timedelta (it's the
        # most ambiguous too). So we explicitely take the same day of
        # the previous month.
        d, m, y = (date_until.day, date_until.month, date_until.year)
        m = m - 1

        if m == 0:
            m = 12
            y = y - 1

        date_from = datetime.date(year=y, month=m, day=d)

    recs = get_record_ids(query[1], date_from, date_until)

    n = len(recs[0])
    if n:
        log('query %08s produced %08s records for all the local collections' % (query[0], n))

    for external_collection_results in recs[1][0]:
        n = len(external_collection_results[1][0])
        if n:
            log('query %08s produced %08s records for external collection \"%s\"' % (query[0], n, external_collection_results[0]))

    if CFG_WEBALERT_DEBUG_LEVEL > 2:
        print("[%s] run query: %s with dates: from=%s, until=%s\n  found rec ids: %s" % (
            strftime("%c"), query, date_from, date_until, recs))

    return {'id_query': query[0], 'argstr': query[1],
            'records': recs, 'date_from': date_from, 'date_until': date_until}

def process_alert_queries(frequency, date):
    """Run the alerts according to the frequency.

    Retrieves the queries for which an alert exists, performs it, and
    processes the corresponding alerts."""

    alert_queries = get_alert_queries(frequency)

    for aq in alert_queries:
        q = run_query(aq, frequency, date)
        alerts = get_alerts(q, frequency)
        process_alerts(alerts)

def process_alert_queries_for_user(uid, date):
    """Process the alerts for the given user id.

    All alerts are with reference date set as the current local time."""

    alert_queries = get_alert_queries_for_user(uid)

    for aq in alert_queries:
        frequency = aq[2]
        q = run_query(aq, frequency, date)
        alerts = get_alerts(q, frequency)
        process_alerts(alerts)

def replace_argument(argstr, argname, argval):
    """Replace the given date argument value with the new one.

    If the argument is missing, it is added."""

    if search('%s=\d+' % argname, argstr):
        r = sub('%s=\d+' % argname, '%s=%s' % (argname, argval), argstr)
    else:
        r = argstr + '&%s=%s' % (argname, argval)

    return r

def update_arguments(argstr, date_from, date_until):
    """Replace date arguments in argstr with the ones specified by date_from and date_until.

    Absent arguments are added."""

    d1y, d1m, d1d = _date_to_tuple(date_from)
    d2y, d2m, d2d = _date_to_tuple(date_until)

    r = replace_argument(argstr, 'd1y', d1y)
    r = replace_argument(r, 'd1m', d1m)
    r = replace_argument(r, 'd1d', d1d)
    r = replace_argument(r, 'd2y', d2y)
    r = replace_argument(r, 'd2m', d2m)
    r = replace_argument(r, 'd2d', d2d)

    return r

def log(msg):
    """Logs the given message in the alert engine log."""

    try:
        logfile = open(CFG_LOGDIR + '/alertengine.log', 'a')
        logfile.write(strftime('%Y%m%d%H%M%S#'))
        logfile.write(msg + '\n')
        logfile.close()
    except Exception:
        register_exception()

def process_alerts(alerts):
    """Process the given alerts and store the records found to the user defined baskets
    and/or notify them by e-mail"""

    # TBD: do not generate the email each time, forge it once and then
    # send it to all appropriate people

    for a in alerts['alerts']:
        if alert_use_basket_p(a):
            add_records_to_basket(alerts['records'], a[2])
        if alert_use_notification_p(a):
            argstr = update_arguments(alerts['argstr'], alerts['date_from'], alerts['date_until'])
            try:
                email_notify(a, alerts['records'], argstr)
            except Exception:
                # There were troubles sending this alert, so register
                # this exception and continue with other alerts:
                register_exception(alert_admin=True,
                                   prefix="Error when sending alert %s, %s\n." % \
                                   (repr(a), repr(argstr)))
        # Inform the admin when external collections time out
        if len(alerts['records'][1][1]) > 0:
            register_exception(alert_admin=True,
                               prefix="External collections %s timed out when sending alert %s, %s\n." % \
                                      (", ".join(alerts['records'][1][1]), repr(a), repr(argstr)))

        update_date_lastrun(a)

def alert_use_basket_p(alert):
    """Boolean. Should this alert store the records found in a basket?"""

    return alert[2] != 0

def alert_use_notification_p(alert):
    """Boolean. Should this alert send a notification e-mail about the records found?"""

    return alert[6] == 'y'

def run_alerts(date):
    """Run the alerts.

    First decide which alerts to run according to the current local
    time, and runs them."""

    if date.day == 1:
        process_alert_queries('month', date)

    if date.isoweekday() == 1: # first day of the week
        process_alert_queries('week', date)

    process_alert_queries('day', date)

# External records related functions
def calculate_external_records(req_args, pattern_list, field, hosted_colls, timeout=CFG_EXTERNAL_COLLECTION_TIMEOUT, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS_ALERTS):
    """Function that returns the external records found and the potential time outs
    given a search pattern and a list of hosted collections."""

    (external_search_engines, basic_search_units) = calculate_external_search_params(pattern_list, field, hosted_colls)

    return do_calculate_external_records(req_args, basic_search_units, external_search_engines, timeout, limit)

def calculate_external_search_params(pattern_list, field, hosted_colls):
    """Function that calculates the basic search units given the search pattern.
    Also returns a set of hosted collections engines."""

    from invenio.legacy.search_engine import create_basic_search_units
    from invenio.legacy.websearch_external_collections import bind_patterns
    from invenio.legacy.websearch_external_collections import select_hosted_search_engines as select_external_search_engines

    pattern = bind_patterns(pattern_list)
    basic_search_units = create_basic_search_units(None, pattern, field)

    external_search_engines = select_external_search_engines(hosted_colls)

    return (external_search_engines, basic_search_units)

def do_calculate_external_records(req_args, basic_search_units, external_search_engines, timeout=CFG_EXTERNAL_COLLECTION_TIMEOUT, limit=CFG_EXTERNAL_COLLECTION_MAXRESULTS_ALERTS):
    """Function that returns the external records found and the potential time outs
    given the basic search units or the req arguments and a set of hosted collections engines."""

    # list to hold the hosted search engines and their respective search urls
    engines_list = []
    # list to hold the non timed out results
    results_list = []
    # list to hold all the results
    full_results_list = []
    # list to hold all the timeouts
    timeout_list = []

    for engine in external_search_engines:
        url = engine.build_search_url(basic_search_units, req_args, limit=limit)
        if url:
            engines_list.append([url, engine])
    # we end up with a [[search url], [engine]] kind of list

    # create the list of search urls to be handed to the asynchronous getter
    pagegetters_list = [HTTPAsyncPageGetter(engine[0]) for engine in engines_list]

    # function to be run on every result
    def finished(pagegetter, data, dummy_time):
        """Function called, each time the download of a web page finish.
        Will parse and print the results of this page."""
        # each pagegetter that didn't timeout is added to this list
        results_list.append((pagegetter, data))

    # run the asynchronous getter
    finished_list = async_download(pagegetters_list, finished, engines_list, timeout)

    # create the complete list of tuples, one for each hosted collection, with the results and other information,
    # including those that timed out
    for (finished, engine) in zip(finished_list, engines_list): #finished_and_engines_list:
        if finished:
            for result in results_list:
                if result[1] == engine:
                    engine[1].parser.parse_and_get_results(result[0].data, feedonly=True)
                    full_results_list.append((engine[1].name, engine[1].parser.parse_and_extract_records(of="xm")))
                    break
        elif not finished:
            timeout_list.append(engine[1].name)

    return (full_results_list, timeout_list)

def calculate_desired_collection_list(c, cc, sc):
    """Function that calculates the user desired collection list when sending a webalert e-mail"""

    if not cc[0]:
        cc = [CFG_SITE_NAME]

    # quickly create the reverse function of collection.is_hosted
    def is_not_hosted_collection(coll):
        collection = Collection.query.filter_by(name=coll).first()
        return collection and not collection.is_hosted

    def get_coll_sons(coll):
        collection = Collection.query.filter_by(name=coll).first()
        return [c.name for c in collection.collection_children_r]

    # calculate the list of non hosted, non restricted, regular sons of cc
    washed_cc_sons = filter(is_not_hosted_collection, get_coll_sons(cc[0]))
    # clean up c removing hosted collections
    washed_c = filter(is_not_hosted_collection, c)

    # try to simulate the wash_colls function behavior when calculating the collections to return
    if not washed_c and not washed_cc_sons: #no collections found: cc has no sons, c not defined
        return cc
    if washed_cc_sons == washed_c:
        if sc == 0:
            return cc
        elif sc == 1:
            return washed_c
    else:
        if sc == 0:
            return washed_c
        elif sc == 1:
            washed_c_sons = []
            for coll in washed_c:
                if coll in washed_cc_sons:
                    washed_c_sons.extend(get_coll_sons(coll))
                else:
                    washed_c_sons.append(coll)
            return washed_c_sons
