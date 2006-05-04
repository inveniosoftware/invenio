## $Id$

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""PERSONAL FEATURES - YOUR ALERTS"""

import cgi
import time

from invenio.config import weburl, cdslang
from invenio.dbquery import run_sql
from invenio.webuser import isGuestUser
from invenio.webaccount import warning_guest_user
from invenio.webbasket import create_personal_baskets_selection_box
from invenio.messages import gettext_set_language
from invenio.dateutils import convert_datestruct_to_datetext, convert_datetext_to_dategui


import invenio.template
webalert_templates = invenio.template.load('webalert')

### IMPLEMENTATION

class AlertError(Exception):
    pass

def check_alert_name(alert_name, uid, ln=cdslang):
    """check this user does not have another alert with this name."""
    sql = """select id_query
           from user_query_basket
           where id_user=%s and alert_name='%s'"""%(uid, alert_name.strip())
    res =  run_sql( sql )

    # load the right message language
    _ = gettext_set_language(ln)

    if len( run_sql( sql ) ) > 0:
        raise AlertError( _("You already have an alert which name is <b>%(name)s</b>") % {'name' : alert_name} )

def get_textual_query_info_from_urlargs(urlargs, ln=cdslang):
    """Return nicely formatted search pattern and catalogue from urlargs of the search query.
    Suitable for 'your searches' display."""
    out = ""
    args = cgi.parse_qs(urlargs)
    return webalert_templates.tmpl_textual_query_info_from_urlargs(
             ln = ln,
             args = args,
           )
    return out


def perform_display(permanent, uid, ln=cdslang):
    """display the searches performed by the current user
    input:  default permanent="n"; permanent="y" display permanent queries(most popular)
    output: list of searches in formatted html
    """
    # load the right message language
    _ = gettext_set_language(ln)

    # first detect number of queries:
    nb_queries_total = 0
    nb_queries_distinct = 0
    id_queries_distinct = []
    query = "SELECT COUNT(*),COUNT(DISTINCT(id_query)) FROM user_query WHERE id_user=%s"
    res = run_sql(query, (uid,), 1)
    try:
        nb_queries_total = res[0][0]
        nb_queries_distinct = res[0][1]
    except:
        pass

    # query for queries:
    if permanent == "n":
        SQL_query = "SELECT DISTINCT(q.id),q.urlargs "\
                    "FROM query q, user_query uq "\
                    "WHERE uq.id_user='%s' "\
                    "AND uq.id_query=q.id "\
                    "ORDER BY q.id DESC" % uid
    else:
        # permanent="y"
        SQL_query = "SELECT q.id,q.urlargs "\
                    "FROM query q "\
                    "WHERE q.type='p'"
    query_result = run_sql(SQL_query)

    queries = []
    if len(query_result) > 0:
        for row in query_result :
            if permanent == "n":
                res = run_sql("SELECT DATE_FORMAT(MAX(date),'%%Y-%%m-%%d %%H:%%i:%%s') FROM user_query WHERE id_user=%s and id_query=%s",
                              (uid, row[0]))
                try:
                    lastrun = res[0][0]
                except:
                    lastrun = _("unknown")
            else:
                lastrun = ""
            queries.append({
                           'id' : row[0],
                           'args' : row[1],
                           'textargs' : get_textual_query_info_from_urlargs(row[1], ln=ln),
                           'lastrun' : lastrun,
                          })


    return webalert_templates.tmpl_display_alerts(
             ln = ln,
             permanent = permanent,
             nb_queries_total = nb_queries_total,
             nb_queries_distinct = nb_queries_distinct,
             queries = queries,
             guest = isGuestUser(uid),
             guesttxt = warning_guest_user(type="alerts", ln=ln),
             weburl = weburl
           )

def perform_input_alert(action, id_query, alert_name, frequency, notification, id_basket,uid, old_id_basket=None, ln = cdslang):
    """get the alert settings
    input:  action="add" for a new alert (blank form), action="modify" for an update
            (get old values)
            id_query id the identifier of the search to be alerted
            for the "modify" action specify old alert_name, frequency of checking,
            e-mail notification and basket id.
    output: alert settings input form"""
    # display query information
    res = run_sql("SELECT urlargs FROM query WHERE id=%s", (id_query,))
    try:
        urlargs = res[0][0]
    except:
        urlargs = "UNKNOWN"
    baskets = create_personal_baskets_selection_box(uid=uid,
                                                    html_select_box_name='idb',
                                                    selected_bsk_id=old_id_basket,
                                                    ln=cdslang)
    return webalert_templates.tmpl_input_alert(
             ln = ln,
             query = get_textual_query_info_from_urlargs(urlargs, ln = ln),
             action = action,
             frequency = frequency,
             notification = notification,
             alert_name = alert_name,
             baskets = baskets,
             old_id_basket = old_id_basket,
             id_basket = id_basket,
             id_query = id_query,
           )

def check_alert_is_unique(id_basket, id_query, uid, ln=cdslang ):
    """check the user does not have another alert for the specified query and basket"""
    _ = gettext_set_language(ln)
    sql = """select id_query
            from user_query_basket
            where id_user = %s and id_query = %s
            and id_basket= %s"""%(uid, id_query, id_basket)
    res =  run_sql(sql)
    if len(res):
        raise AlertError(_("You already have an alert defined for the specified query and basket"))

def perform_add_alert(alert_name, frequency, notification,
                      id_basket, id_query, uid, ln = cdslang):
    """add an alert to the database
    input:  the name of the new alert;
            alert frequency: 'month', 'week' or 'day';
            setting for e-mail notification: 'y' for yes, 'n' for no;
            basket identifier: 'no' for no basket;
            new basket name for this alert;
            identifier of the query to be alerted
    output: confirmation message + the list of alerts Web page"""
    alert_name = alert_name.strip()

    # load the right message language
    _ = gettext_set_language(ln)

    #check the alert name is not empty
    if alert_name.strip() == "":
        raise AlertError(_("The alert name cannot be <b>empty</b>."))

    #check if the alert can be created
    check_alert_name(alert_name, uid, ln)
    check_alert_is_unique(id_basket, id_query, uid, ln)

    # add a row to the alerts table: user_query_basket
    query = """INSERT INTO user_query_basket (id_user, id_query, id_basket,
                                              frequency, date_creation, date_lastrun,
                                              alert_name, notification)
               VALUES ('%s','%s','%s','%s','%s','','%s','%s')"""
    query %= (uid, id_query, id_basket,
              frequency, convert_datestruct_to_datetext(time.localtime()),
              alert_name, notification)
    run_sql(query)
    out = _("The alert %s has been added to your profile.")
    out %= '<b>' + alert_name + '</b>'
    out += perform_list_alerts(uid, ln=ln)
    return out


def perform_list_alerts (uid, ln=cdslang):
    """perform_list_alerts display the list of alerts for the connected user"""
    # set variables
    out = ""
    
    # query the database
    query = """ SELECT q.id, q.urlargs,
                       a.id_basket, b.name,
                       a.alert_name, a.frequency,a.notification,
                       DATE_FORMAT(a.date_creation,'%%Y-%%m-%%d %%H:%%i:%%s'),
                       DATE_FORMAT(a.date_lastrun,'%%Y-%%m-%%d %%H:%%i:%%s')
                FROM user_query_basket a LEFT JOIN query q ON a.id_query=q.id
                                         LEFT JOIN bskBASKET b ON a.id_basket=b.id
                WHERE a.id_user='%s' 
                ORDER BY a.alert_name ASC """ % uid
    res = run_sql(query)
    alerts = []
    for (qry_id, qry_args,
         bsk_id, bsk_name,
         alrt_name, alrt_frequency, alrt_notification, alrt_creation, alrt_last_run) in res:
        alerts.append({
            'queryid' : qry_id,
            'queryargs' : qry_args,
            'textargs' : get_textual_query_info_from_urlargs(qry_args, ln=ln),
            'userid' : uid,
            'basketid' : bsk_id,
            'basketname' : bsk_name,
            'alertname' : alrt_name,
            'frequency' : alrt_frequency,
            'notification' : alrt_notification,
            'created' : convert_datetext_to_dategui(alrt_creation),
            'lastrun' : convert_datetext_to_dategui(alrt_last_run)
            })

    # link to the "add new alert" form
    out = webalert_templates.tmpl_list_alerts(ln=ln, weburl=weburl, alerts=alerts,
                                              guest=isGuestUser(uid),
                                              guesttxt=warning_guest_user(type="alerts", ln=ln))
    return out

def perform_remove_alert(alert_name, id_user, id_query, id_basket, uid, ln=cdslang):
    """perform_remove_alert: remove an alert from the database
    input:  identifier of the user;
            identifier of the query;
            identifier of the basket
    output: confirmation message + the list of alerts Web page"""
    # set variables
    out = ""

    # remove a row from the alerts table: user_query_basket
    query = """DELETE FROM user_query_basket
               WHERE id_user='%s' AND id_query='%s' AND id_basket='%s'"""
    query %= (id_user, id_query, id_basket)
    run_sql(query)
    out += "The alert <b>%s</b> has been removed from your profile.<br /><br />\n" % alert_name
    out += perform_list_alerts(uid)
    return out


def perform_update_alert(alert_name, frequency, notification, id_basket, id_query, old_id_basket,uid, ln = cdslang):
    """update alert settings into the database
    input:  the name of the new alert;
            alert frequency: 'month', 'week' or 'day';
            setting for e-mail notification: 'y' for yes, 'n' for no;
            new basket identifier: 'no' for no basket;
            new basket name for this alert;
            identifier of the query to be alerted
            old identifier of the basket associated to the alert
    output: confirmation message + the list of alerts Web page"""
    #set variables
    out = ""
    
    # load the right message language
    _ = gettext_set_language(ln)

    #check the alert name is not empty
    if alert_name.strip() == "":
        raise AlertError(_("The alert name cannot be <b>empty</b>."))

    #check if the alert can be created
    sql = """select alert_name
            from user_query_basket
            where id_user=%s
            and id_basket=%s
            and id_query=%s"""%( uid, old_id_basket, id_query )
    old_alert_name = run_sql( sql )[0][0]
    if old_alert_name.strip()!="" and old_alert_name != alert_name:
        check_alert_name( alert_name, uid, ln)
    if id_basket != old_id_basket:
        check_alert_is_unique( id_basket, id_query, uid, ln)

    # update a row into the alerts table: user_query_basket
    query = """UPDATE user_query_basket 
               SET alert_name='%s',frequency='%s',notification='%s',
                   date_creation='%s',date_lastrun='',id_basket='%s'
               WHERE id_user='%s' AND id_query='%s' AND id_basket='%s'"""
    query %= (alert_name, frequency, notification,
              convert_datestruct_to_datetext(time.localtime()),
              id_basket, uid, id_query, old_id_basket)
    
    run_sql(query)

    out += _("The alert %s has been successfully updated.") % "<b>" + alert_name + "</b>"
    out += "<br /><br />\n" + perform_list_alerts(uid)
    return out

def is_selected(var, fld):
    "Checks if the two are equal, and if yes, returns ' selected'. Useful for select boxes."
    if var == fld:
        return " selected"
    else:
        return ""

def account_list_alerts(uid, ln=cdslang):
    """account_list_alerts: list alert for the account page
    input:  the user id
            language
    output: the list of alerts Web page"""
    query = """ SELECT q.id, q.urlargs, a.id_user, a.id_query,
                       a.id_basket, a.alert_name, a.frequency,
                       a.notification,
                       DATE_FORMAT(a.date_creation,'%%d %%b %%Y'),
                       DATE_FORMAT(a.date_lastrun,'%%d %%b %%Y'),
                       a.id_basket
                FROM query q, user_query_basket a
                WHERE a.id_user='%s' AND a.id_query=q.id
                ORDER BY a.alert_name ASC """ % uid
    res = run_sql(query)
    alerts = []
    if len(res):
        for row in res:
            alerts.append({
                            'id' : row[0],
                            'name' : row[5]
                          })

    return webalert_templates.tmpl_account_list_alerts(ln=ln, alerts=alerts)

def account_list_searches(uid, ln=cdslang):
    """ account_list_searches: list the searches of the user
        input:  the user id
        output: resume of the searches"""
    out =""
  # first detect number of queries:
    nb_queries_total = 0
    nb_queries_distinct = 0
    id_queries_distinct = []
    res = run_sql("SELECT COUNT(*),COUNT(DISTINCT(id_query)) FROM user_query WHERE id_user=%s", (uid,), 1)
    try:
        nb_queries_total = res[0][0]
        nb_queries_distinct = res[0][1]
    except:
        pass

    # load the right message language
    _ = gettext_set_language(ln)

    out += _("You have made %(number)s queries. A %(detailed_list)s is available with a posibility to (a) view search results and (b) subscribe for automatic email alerting service for these queries") % {
              'detailed_list' : """<a href="../youralerts.py/display">""" + _("detailed list") + """</a>""",
              'number' : nb_queries_total,
            }
    return out
