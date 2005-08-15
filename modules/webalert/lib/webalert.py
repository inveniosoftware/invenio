## $Id$

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""PERSONAL FEATURES - YOUR ALERTS"""

import cgi
import string
import sys
import time
import urllib
import zlib

from config import *
from webpage import page
from dbquery import run_sql
from webuser import getUid, isGuestUser
from webaccount import warning_guest_user
from webbasket import perform_create_basket, BasketNameAlreadyExists
from mod_python import apache

from messages import gettext_set_language

import template
webalert_templates = template.load('webalert')

### IMPLEMENTATION

class AlertError(Exception):
    pass

def check_alert_name(alert_name, uid, ln = cdslang):
    #check this user does not have another alert with this name
    sql = """select id_query
           from user_query_basket
           where id_user=%s and alert_name='%s'"""%(uid, alert_name.strip())
    res =  run_sql( sql )

    # load the right message language
    _ = gettext_set_language(ln)

    if len( run_sql( sql ) ) > 0:
        raise AlertError( _("You already have an alert which name is <b>%(name)s</b>") % {'name' : alert_name} )

def get_textual_query_info_from_urlargs(urlargs, ln = cdslang):
    """Return nicely formatted search pattern and catalogue from urlargs of the search query.
    Suitable for 'your searches' display."""
    out = ""
    args = cgi.parse_qs(urlargs)
    return webalert_templates.tmpl_textual_query_info_from_urlargs(
             ln = ln,
             args = args,
           )
    return out

# perform_display(): display the searches performed by the current user
# input:  default permanent="n"; permanent="y" display permanent queries(most popular)
# output: list of searches in formatted html
def perform_display(permanent,uid, ln = cdslang):

    # set variables
    out = ""
    id_user = uid # XXX

    # load the right message language
    _ = gettext_set_language(ln)

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

    # query for queries:
    if permanent == "n":
        SQL_query = "SELECT DISTINCT(q.id),q.urlargs "\
                    "FROM query q, user_query uq "\
                    "WHERE uq.id_user='%s' "\
                    "AND uq.id_query=q.id "\
                    "ORDER BY q.id DESC" % id_user
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
                res = run_sql("SELECT DATE_FORMAT(MAX(date),'%%Y-%%m-%%d %%T') FROM user_query WHERE id_user=%s and id_query=%s",
                              (id_user, row[0]))
                try:
                    lastrun = res[0][0]
                except:
                    lastrun = _("unknown")
            else:
                lastrun = ""
            queries.append({
                           'id' : row[0],
                           'args' : row[1],
                           'textargs' : get_textual_query_info_from_urlargs(row[1], ln = ln),
                           'lastrun' : lastrun,
                          })


    return webalert_templates.tmpl_display_alerts(
             ln = ln,
             permanent = permanent,
             nb_queries_total = nb_queries_total,
             nb_queries_distinct = nb_queries_distinct,
             queries = queries,
             guest = isGuestUser(uid),
             guesttxt = warning_guest_user(type="alerts", ln = ln),
             weburl = weburl
           )


# perform_input_alert: get the alert settings
# input:  action="add" for a new alert (blank form), action="modify" for an update (get old values)
#         id_query id the identifier of the search to be alerted
#         for the "modify" action specify old alert_name, frequency of checking, e-mail notification and basket id.
# output: alert settings input form
def perform_input_alert(action, id_query, alert_name, frequency, notification, id_basket,uid, old_id_basket=None, ln = cdslang):

    # set variables
    out = ""
    frequency_month = frequency
    frequency_week = ""
    frequency_day = ""
    notification_yes = ""
    notification_no = ""
    id_user = uid # XXX

    # display query information
    res = run_sql("SELECT urlargs FROM query WHERE id=%s", (id_query,))
    try:
        urlargs = res[0][0]
    except:
        urlargs = "UNKNOWN"

    SQL_query = "SELECT b.id, b.name FROM basket b,user_basket ub "\
	  "WHERE ub.id_user='%s' AND ub.id_basket=b.id ORDER BY b.name ASC" % id_user
    query_result = run_sql(SQL_query)

    baskets = []
    for row in query_result :
        baskets.append({
                        'id' : row[0],
                        'name' : row[1],
                       })

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

def check_alert_is_unique( id_basket, id_query, uid, ln = cdslang ):
    #check the user does not have another alert for the specied query
    #   and basket
    sql = """select id_query
            from user_query_basket
            where id_user = %s and id_query = %s
            and id_basket= %s"""%(uid, id_query, id_basket)
    res =  run_sql( sql )
    if len( run_sql( sql ) ) > 0:
        raise AlertError(_("You already have an alert defined for the specified query and basket"))



# perform_add_alert: add an alert to the database
# input:  the name of the new alert;
#         alert frequency: 'month', 'week' or 'day';
#         setting for e-mail notification: 'y' for yes, 'n' for no;
#         basket identifier: 'no' for no basket;
#         new basket name for this alert;
#         identifier of the query to be alerted
# output: confirmation message + the list of alerts Web page
def perform_add_alert(alert_name, frequency, notification, id_basket, new_basket_name, id_query,uid, ln = cdslang):

    # set variables
    out = ""
    id_user=uid # XXX
    alert_name = alert_name.strip()

    # load the right message language
    _ = gettext_set_language(ln)

    #check the alert name is not empty
    if alert_name.strip() == "":
        raise AlertError(_("The alert name cannot be <b>empty</b>."))

    #check if the alert can be created
    check_alert_name( alert_name, uid, ln)
    check_alert_is_unique( id_basket, id_query, uid, ln)

    # set the basket identifier
    if new_basket_name != "":
        # create a new basket
        try:
            id_basket =  perform_create_basket(uid, new_basket_name, ln)
            basket_created = 1
            out += _("""The <I>private</I> basket <B>%(name)s</B> has been created.""") % {'name' : new_basket_name }+ """<BR>"""
        except BasketNameAlreadyExists, e:
            basket_created = 0
            out += _("You already have a basket which name is '%s'") % basket_name

    # add a row to the alerts table: user_query_basket
    SQL_query = "INSERT INTO user_query_basket (id_user, id_query, id_basket, frequency, date_creation, date_lastrun, alert_name, notification) "\
                "VALUES ('%s','%s','%s','%s','%s','','%s','%s') " \
                % (id_user, id_query, id_basket, frequency,time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), alert_name, notification)
    query_result = run_sql(SQL_query)
    out += _("""The alert <B>%s</B> has been added to your profile.""") % alert_name + """<BR><BR>"""
    out += perform_list_alerts(uid, ln = ln)
    return out


# perform_list_alerts display the list of alerts for the connected user
def perform_list_alerts (uid, ln = cdslang):
    # set variables
    out = ""
    id_user = uid # XXX

    # query the database
    SQL_query = """ SELECT q.id, q.urlargs, a.id_user, a.id_query,
                            a.id_basket, a.alert_name, a.frequency,
                            a.notification,
                            DATE_FORMAT(a.date_creation,'%%d %%b %%Y'),
                            DATE_FORMAT(a.date_lastrun,'%%d %%b %%Y'),
                            a.id_basket
                    FROM query q, user_query_basket a
                    WHERE a.id_user='%s' AND a.id_query=q.id
                    ORDER BY a.alert_name ASC """ % id_user
    query_result = run_sql(SQL_query)
    alerts = []
    if len(query_result) > 0:
        for row in query_result :
            sql = "select name from basket where id=%s"%row[10]
            res = run_sql(sql)
            if res:
              basket_name=res[0][0]
            else:
              basket_name=""

            alerts.append({
                           'queryid' : row[0],
                           'queryargs' : row[1],
                           'textargs' : get_textual_query_info_from_urlargs(row[1], ln = ln),
                           'userid' : row[2],
                           'basketid' : row[4],
                           'basketname' : basket_name,
                           'alertname' : row[5],
                           'frequency' : row[6],
                           'notification' : row[7],
                           'created' : row[8],
                           'lastrun' : row[9],
                          })

    # link to the "add new alert" form
    out = webalert_templates.tmpl_list_alerts(
           ln = ln,
           weburl = weburl,
           alerts = alerts,
           guest = isGuestUser(uid),
           guesttxt = warning_guest_user(type="alerts", ln = ln),
         )

    return out


# perform_remove_alert: remove an alert from the database
# input:  identifier of the user;
#         identifier of the query;
#         identifier of the basket
# output: confirmation message + the list of alerts Web page
def perform_remove_alert( alert_name, id_user, id_query, id_basket,uid, ln = cdslang):

    # set variables
    out = ""

    # remove a row from the alerts table: user_query_basket
    SQL_query = "DELETE FROM user_query_basket "\
                "WHERE id_user='%s' AND id_query='%s' AND id_basket='%s'" \
                % (id_user, id_query, id_basket)
    query_result = run_sql(SQL_query)
    out += """The alert <B>%s</B> has been removed from your profile.<BR><BR>\n""" % alert_name
    out += perform_list_alerts(uid)
    return out


# perform_update_alert: update alert settings into the database
# input:  the name of the new alert;
#         alert frequency: 'month', 'week' or 'day';
#         setting for e-mail notification: 'y' for yes, 'n' for no;
#         new basket identifier: 'no' for no basket;
#         new basket name for this alert;
#         identifier of the query to be alerted
#         old identifier of the basket associated to the alert
# output: confirmation message + the list of alerts Web page
def perform_update_alert(alert_name, frequency, notification, id_basket, new_basket_name, id_query, old_id_basket,uid, ln = cdslang):

    #set variables
    out = ""
    id_user = uid # XXX

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

    # set the basket identifier
    if new_basket_name != "":
        # create a new basket
        try:
            id_basket =  perform_create_basket(uid, new_basket_name, ln)
            basket_created = 1
            out += _("""The <I>private</I> basket <B>%(name)s</B> has been created.""") % {'name' : new_basket_name }+ """<BR>"""
        except BasketNameAlreadyExists, e:
            basket_created = 0
            out += _("You already have a basket which name is '%s'") % basket_name

    # update a row into the alerts table: user_query_basket
    SQL_query = "UPDATE user_query_basket "\
                "SET alert_name='%s',frequency='%s',notification='%s',date_creation='%s',date_lastrun='',id_basket='%s' "\
                "WHERE id_user='%s' AND id_query='%s' AND id_basket='%s'" \
                % (alert_name,frequency,notification,time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),id_basket,id_user,id_query,old_id_basket)
    #date_creation
    #date_lastrun
    query_result = run_sql(SQL_query)

    out += _("""The alert <B>%s</B> has been successfully updated.""") % alert_name + """<BR><BR>"""
    out += perform_list_alerts(uid)
    return out

def is_selected(var, fld):
    "Checks if the two are equal, and if yes, returns ' selected'. Useful for select boxes."
    if var == fld:
        return " selected"
    else:
        return ""

# account_list_alerts: list alert for the account page
# input:  the user id
#         id_alert: the identifier of the alert
#         id_basket: the identifier of the basket, to access to the alert
#         new basket identifier: 'no' for no basket;
#         new basket name for this alert;
#         identifier of the query to be alerted
# output: the list of alerts Web page
def account_list_alerts(uid, action="", id_alert=0,id_basket=0,old_id_basket=0,newname="",value="", ln = "en"):
    i=0
    id_user = uid # XXX
    out = ""
    SQL_query = """ SELECT q.id, q.urlargs, a.id_user, a.id_query,
                            a.id_basket, a.alert_name, a.frequency,
                            a.notification,
                            DATE_FORMAT(a.date_creation,'%%d %%b %%Y'),
                            DATE_FORMAT(a.date_lastrun,'%%d %%b %%Y'),
                            a.id_basket
                    FROM query q, user_query_basket a
                    WHERE a.id_user='%s' AND a.id_query=q.id
                    ORDER BY a.alert_name ASC """ % id_user
    query_result = run_sql(SQL_query)
    alerts = []
    if len(query_result) > 0 :
        for row in query_result :
            alerts.append({
                            'id' : row[0],
                            'name' : row[5]
                          })

    return webalert_templates.tmpl_account_list_alerts(
             ln = ln,
             alerts = alerts,
           )

# account_list_searches: list the searches of the user
# input:  the user id
# output: resume of the searches
def account_list_searches(uid, ln = "en"):
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

    out += _(""" You have made %(number)s queries. A %(detailed_list)s is available with a posibility to (a) view search results and (b) subscribe for automatic email alerting service for these queries""") % {
              'detailed_list' : """<A href="../youralerts.py/display">""" + _("detailed list") + """</A>""",
              'number' : nb_queries_total,
            }
    return out
