# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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
from sre import search, sub
import sys
from time import localtime, strftime, mktime, sleep
from string import split
import smtplib
import datetime

from email.Header import Header
from email.Message import Message
from email.MIMEText import MIMEText

from invenio.config import \
     logdir, \
     supportemail, \
     version, \
     weburl
from invenio.search_engine import perform_request_search
from invenio.alert_engine_config import *
from invenio.webinterface_handler import wash_urlargd
from invenio.dbquery import run_sql
from invenio.htmlparser import *
from invenio.webuser import get_email
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


# def add_record_to_basket(record_id, basket_id):
#     if CFG_WEBALERT_DEBUG_LEVEL > 0:
#         print "-> adding record %s into basket %s" % (record_id, basket_id)
#     try:
#         return run_sql('insert into basket_record (id_basket, id_record) values(%s, %s);', (basket_id, record_id,))
#     except:
#         return 0


# def add_records_to_basket(record_ids, basket_id):
#     # TBD: generate the list and all all records in one step (see below)
#     for i in record_ids:
#         add_record_to_basket(i, basket_id)

# Optimized version:
def add_records_to_basket(record_ids, basket_id):

    nrec = len(record_ids)
    if nrec > 0:
        vals = '(%s,%s)' % (basket_id, record_ids[0])
        if nrec > 1:
            for i in record_ids[1:]:
                vals += ',(%s, %s)' % (basket_id, i)
        if CFG_WEBALERT_DEBUG_LEVEL > 0:
            print "-> adding %s records into basket %s: %s" % (nrec, basket_id, vals)
        try:
            if CFG_WEBALERT_DEBUG_LEVEL < 4:
                return run_sql('insert into basket_record (id_basket, id_record) values %s;' % vals) # Cannot use the run_sql(<query>, (<arg>,)) form for some reason
            else:
                print '   NOT ADDED, DEBUG LEVEL == 4'
                return 0
        except:
            return 0
    else:
        return 0


def get_query(alert_id):
    r = run_sql('select urlargs from query where id=%s', (alert_id,))
    return r[0][0]

def send_email(fromaddr, toaddr, body,
               attempt_times=1,
               attempt_sleeptime=10):
    """Send email to TOADDR from FROMADDR with message BODY.

       If sending fails, try to send it ATTEMPT_TIMES, and wait for
       ATTEMPT_SLEEPTIME seconds in between tries.

       Return 0 if email was sent okay, 1 if it was not.
    """

    if attempt_times < 1:
        log('Not attempting to send email to %s.' % toaddr)
        return 1

    try:
        server = smtplib.SMTP('localhost')
        if CFG_WEBALERT_DEBUG_LEVEL > 2:
            server.set_debuglevel(1)
        else:
            server.set_debuglevel(0)
        server.sendmail(fromaddr, toaddr, body)
        server.quit()
    except:
        if attempt_times > 1:
            if (CFG_WEBALERT_DEBUG_LEVEL > 1):
                print 'Error connecting to SMTP server, retrying in %d seconds. Exception raised: %s' % (attempt_sleeptime, sys.exc_info()[0])
            sleep(attempt_sleeptime)
            return send_email(fromaddr, toaddr, body, attempt_times-1, attempt_sleeptime)
        else:
            log('Error sending email to %s.  Giving up.' % toaddr)
            return 1

    return 0

def forge_email(fromaddr, toaddr, subject, content):
    msg = MIMEText(content, _charset='utf-8')

    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = Header(subject, 'utf-8')

    return msg.as_string()


def email_notify(alert, records, argstr):

    if len(records) == 0:
        return

    msg = ""

    if CFG_WEBALERT_DEBUG_LEVEL > 0:
        msg = "*** THIS MESSAGE WAS SENT IN DEBUG MODE ***\n\n"

    url = weburl + "/search?" + argstr

    # Extract the pattern and catalogue list from the formatted query
    query = parse_qs(argstr)
    pattern = query.get('p', [''])[0]
    catalogues = query.get('c', [])

    frequency = alert[3]

    msg += webalert_templates.tmpl_alert_email_body(
        alert[5], url, records, pattern, catalogues, frequency)
    msg = MIMEText(msg, _charset='utf-8')

    email = get_email(alert[0])

    if email == 'guest':
        print "********************************************************************************"
        print "The following alert was not send, because cannot detect user email address:"
        print "   " + repr(argstr)
        print "********************************************************************************"
        return

    msg['To'] = email

    # Let the template fill in missing fields
    webalert_templates.tmpl_alert_email_headers(alert[5], msg)

    sender = msg['From']

    body = msg.as_string()

    if CFG_WEBALERT_DEBUG_LEVEL > 0:
        print "********************************************************************************"
        print body
        print "********************************************************************************"

    if CFG_WEBALERT_DEBUG_LEVEL < 2:
        send_email(sender, email, body,
                   CFG_WEBALERT_SEND_EMAIL_NUMBER_OF_TRIES,
                   CFG_WEBALERT_SEND_EMAIL_SLEEPTIME_BETWEEN_TRIES)
    if CFG_WEBALERT_DEBUG_LEVEL == 4:
        send_email(sender, supportemail, body,
                   CFG_WEBALERT_SEND_EMAIL_NUMBER_OF_TRIES,
                   CFG_WEBALERT_SEND_EMAIL_SLEEPTIME_BETWEEN_TRIES)

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
        log = open(logdir + '/alertengine.log', 'a')
        log.write(strftime('%Y%m%d%H%M%S#'))
        log.write(msg + '\n')
        log.close()
    except:
        pass

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
