# -*- coding: utf-8 -*-
##
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

"""Alert engine implementation."""

## rest of the Python code goes below

__revision__ = "$Id$"

from cgi import parse_qs
from re import search, sub
from time import strftime
import datetime

from invenio.config import \
     CFG_LOGDIR, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_URL
from invenio.webbasket_dblayer import get_basket_owner_id, add_to_basket
from invenio.search_engine import perform_request_search
from invenio.webinterface_handler import wash_urlargd
from invenio.dbquery import run_sql
from invenio.webuser import get_email
from invenio.mailutils import send_email
from invenio.errorlib import register_exception
from invenio.alert_engine_config import CFG_WEBALERT_DEBUG_LEVEL, \
    CFG_WEBALERT_SEND_EMAIL_NUMBER_OF_TRIES, \
    CFG_WEBALERT_SEND_EMAIL_SLEEPTIME_BETWEEN_TRIES
import invenio.template
websearch_templates = invenio.template.load('websearch')
webalert_templates = invenio.template.load('webalert')

def update_date_lastrun(alert):
    return run_sql('update user_query_basket set date_lastrun=%s where id_user=%s and id_query=%s and id_basket=%s;', (strftime("%Y-%m-%d"), alert[0], alert[1], alert[2],))


def get_alert_queries(frequency):
    return run_sql('select distinct id, urlargs from query q, user_query_basket uqb where q.id=uqb.id_query and uqb.frequency=%s and uqb.date_lastrun <= now();', (frequency,))

def get_alert_queries_for_user(uid):
    return run_sql('select distinct id, urlargs, uqb.frequency from query q, user_query_basket uqb where q.id=uqb.id_query and uqb.id_user=%s and uqb.date_lastrun <= now();', (uid,))

def get_alerts(query, frequency):
    r = run_sql('select id_user, id_query, id_basket, frequency, date_lastrun, alert_name, notification from user_query_basket where id_query=%s and frequency=%s;', (query['id_query'], frequency,))
    return {'alerts': r, 'records': query['records'], 'argstr': query['argstr'], 'date_from': query['date_from'], 'date_until': query['date_until']}

# Optimized version:
def add_records_to_basket(record_ids, basket_id):
    nrec = len(record_ids)
    if nrec > 0:
        if CFG_WEBALERT_DEBUG_LEVEL > 0:
            print "-> adding %s records into basket %s: %s" % (nrec, basket_id, record_ids)
        try:
            if CFG_WEBALERT_DEBUG_LEVEL < 4:
                owner_uid = get_basket_owner_id(basket_id)
                add_to_basket(owner_uid, record_ids, [basket_id])
            else:
                print '   NOT ADDED, DEBUG LEVEL == 4'
        except Exception:
            register_exception()


def get_query(alert_id):
    r = run_sql('select urlargs from query where id=%s', (alert_id,))
    return r[0][0]

def email_notify(alert, records, argstr):

    if len(records) == 0:
        return

    msg = ""

    if CFG_WEBALERT_DEBUG_LEVEL > 0:
        msg = "*** THIS MESSAGE WAS SENT IN DEBUG MODE ***\n\n"

    url = CFG_SITE_URL + "/search?" + argstr

    # Extract the pattern and catalogue list from the formatted query
    query = parse_qs(argstr)
    pattern = query.get('p', [''])[0]
    catalogues = query.get('c', [])

    frequency = alert[3]

    msg += webalert_templates.tmpl_alert_email_body(
        alert[5], url, records, pattern, catalogues, frequency)

    email = get_email(alert[0])

    if email == 'guest':
        print "********************************************************************************"
        print "The following alert was not send, because cannot detect user email address:"
        print "   " + repr(argstr)
        print "********************************************************************************"
        return

    if CFG_WEBALERT_DEBUG_LEVEL > 0:
        print "********************************************************************************"
        print msg
        print "********************************************************************************"

    if CFG_WEBALERT_DEBUG_LEVEL < 2:
        send_email(fromaddr=webalert_templates.tmpl_alert_email_from(),
                   toaddr=email,
                   subject=webalert_templates.tmpl_alert_email_title(alert[5]),
                   content=msg,
                   header='',
                   footer='',
                   attempt_times=CFG_WEBALERT_SEND_EMAIL_NUMBER_OF_TRIES,
                   attempt_sleeptime=CFG_WEBALERT_SEND_EMAIL_SLEEPTIME_BETWEEN_TRIES)
    if CFG_WEBALERT_DEBUG_LEVEL == 4:
        send_email(fromaddr=webalert_templates.tmpl_alert_email_from(),
                   toaddr=CFG_SITE_SUPPORT_EMAIL,
                   subject=webalert_templates.tmpl_alert_email_title(alert[5]),
                   content=msg,
                   header='',
                   footer='',
                   attempt_times=CFG_WEBALERT_SEND_EMAIL_NUMBER_OF_TRIES,
                   attempt_sleeptime=CFG_WEBALERT_SEND_EMAIL_SLEEPTIME_BETWEEN_TRIES)

def get_argument(args, argname):
    if args.has_key(argname):
        return args[argname]
    else:
        return []

def _date_to_tuple(date):
    return [int(part) for part in (date.year, date.month, date.day)]

def get_record_ids(argstr, date_from, date_until):
    argd = wash_urlargd(parse_qs(argstr), websearch_templates.search_results_default_urlargd)
    p       = get_argument(argd, 'p')
    c       = get_argument(argd, 'c')
    cc      = get_argument(argd, 'cc')
    as      = get_argument(argd, 'as')
    f       = get_argument(argd, 'f')
    so      = get_argument(argd, 'so')
    sp      = get_argument(argd, 'sp')
    ot      = get_argument(argd, 'ot')
    as      = get_argument(argd, 'as')
    p1      = get_argument(argd, 'p1')
    f1      = get_argument(argd, 'f1')
    m1      = get_argument(argd, 'm1')
    op1     = get_argument(argd, 'op1')
    p2      = get_argument(argd, 'p2')
    f2      = get_argument(argd, 'f2')
    m2      = get_argument(argd, 'm2')
    op2     = get_argument(argd, 'op2')
    p3      = get_argument(argd, 'p3')
    f3      = get_argument(argd, 'f3')
    m3      = get_argument(argd, 'm3')
    sc      = get_argument(argd, 'sc')

    d1y, d1m, d1d = _date_to_tuple(date_from)
    d2y, d2m, d2d = _date_to_tuple(date_until)

    return perform_request_search(of='id', p=p, c=c, cc=cc, f=f, so=so, sp=sp, ot=ot,
                                  as=as, p1=p1, f1=f1, m1=m1, op1=op1, p2=p2, f2=f2,
                                  m2=m2, op2=op2, p3=p3, f3=f3, m3=m3, sc=sc, d1y=d1y,
                                  d1m=d1m, d1d=d1d, d2y=d2y, d2m=d2m, d2d=d2d)


def get_argument_as_string(argstr, argname):
    args = parse_qs(argstr)
    a = get_argument(args, argname)
    r = ''
    if len(a):
        r = a[0]
    for i in a[1:len(a)]:
        r += ", %s" % i
    return r

def get_pattern(argstr):
    return get_argument_as_string(argstr, 'p')

def get_catalogue(argstr):
    return get_argument_as_string(argstr, 'c')

def get_catalogue_num(argstr):
    args = parse_qs(argstr)
    a = get_argument(args, 'c')
    return len(a)


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

    n = len(recs)
    if n:
        log('query %08s produced %08s records' % (query[0], len(recs)))

    if CFG_WEBALERT_DEBUG_LEVEL > 2:
        print "[%s] run query: %s with dates: from=%s, until=%s\n  found rec ids: %s" % (
            strftime("%c"), query, date_from, date_until, recs)

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
    try:
        log = open(CFG_LOGDIR + '/alertengine.log', 'a')
        log.write(strftime('%Y%m%d%H%M%S#'))
        log.write(msg + '\n')
        log.close()
    except Exception:
        register_exception()

def process_alerts(alerts):
    # TBD: do not generate the email each time, forge it once and then
    # send it to all appropriate people

    for a in alerts['alerts']:
        if alert_use_basket_p(a):
            add_records_to_basket(alerts['records'], a[2])
        if alert_use_notification_p(a):
            argstr = update_arguments(alerts['argstr'], alerts['date_from'], alerts['date_until'])
            email_notify(a, alerts['records'], argstr)

        update_date_lastrun(a)


def alert_use_basket_p(alert):
    return alert[2] != 0


def alert_use_notification_p(alert):
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

def process_alert_queries_for_user(uid, date):
    """Process the alerts for the given user id.

    All alerts are with reference date set as the current local time."""

    alert_queries = get_alert_queries_for_user(uid)
    print alert_queries

    for aq in alert_queries:
        frequency = aq[2]
        q = run_query(aq, frequency, date)
        alerts = get_alerts(q, frequency)
        process_alerts(alerts)
