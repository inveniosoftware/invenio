# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

"""PERSONAL FEATURES - YOUR ALERTS"""

__revision__ = "$Id$"

import cgi
import time

from invenio.config import CFG_SITE_LANG
from invenio.legacy.dbquery import run_sql
from invenio.legacy.webuser import isGuestUser
from invenio.ext.logging import register_exception
from invenio.legacy.websession.webaccount import warning_guest_user
from invenio.legacy.webbasket.api import create_personal_baskets_selection_box
from invenio.legacy.webbasket.db_layer import check_user_owns_baskets
from invenio.base.i18n import gettext_set_language
from invenio.utils.date import convert_datestruct_to_datetext, convert_datetext_to_dategui

import invenio.legacy.template
webalert_templates = invenio.legacy.template.load('webalert')

### IMPLEMENTATION

class AlertError(Exception):
    pass

def check_alert_name(alert_name, uid, ln=CFG_SITE_LANG):
    """check this user does not have another alert with this name."""

    # load the right language
    _ = gettext_set_language(ln)

    sql = """select id_query
           from user_query_basket
           where id_user=%s and alert_name=%s"""
    res =  run_sql(sql, (uid, alert_name.strip()))
    if len(res) > 0:
        raise AlertError( _("You already have an alert named %(x_name)s.", x_name=('<b>' + cgi.escape(alert_name) + '</b>',)))

def get_textual_query_info_from_urlargs(urlargs, ln=CFG_SITE_LANG):
    """Return nicely formatted search pattern and catalogue from urlargs of the search query.
    Suitable for 'your searches' display."""
    out = ""
    args = cgi.parse_qs(urlargs)
    return webalert_templates.tmpl_textual_query_info_from_urlargs(
             ln = ln,
             args = args,
           )
    return out

def perform_display(permanent, uid, ln=CFG_SITE_LANG):
    """display the searches performed by the current user
    input:  default permanent="n"; permanent="y" display permanent queries(most popular)
    output: list of searches in formatted html
    """
    # load the right language
    _ = gettext_set_language(ln)

    # first detect number of queries:
    nb_queries_total = 0
    nb_queries_distinct = 0
    query = "SELECT COUNT(*),COUNT(DISTINCT(id_query)) FROM user_query WHERE id_user=%s"
    res = run_sql(query, (uid,), 1)
    try:
        nb_queries_total = res[0][0]
        nb_queries_distinct = res[0][1]
    except:
        pass

    # query for queries:
    params = ()
    if permanent == "n":
        SQL_query = "SELECT DISTINCT(q.id),q.urlargs "\
                    "FROM query q, user_query uq "\
                    "WHERE uq.id_user=%s "\
                    "AND uq.id_query=q.id "\
                    "ORDER BY q.id DESC"
        params = (uid,)
    else:
        # permanent="y"
        SQL_query = "SELECT q.id,q.urlargs "\
                    "FROM query q "\
                    "WHERE q.type='p'"
    query_result = run_sql(SQL_query, params)

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
             guesttxt = warning_guest_user(type="alerts", ln=ln)
           )

def check_user_can_add_alert(id_user, id_query):
    """Check if ID_USER has really alert adding rights on ID_QUERY
    (that is, the user made the query herself or the query is one of
    predefined `popular' queries) and return True or False
    accordingly.  Useful to filter out malicious users trying to guess
    idq URL parameter values in order to access potentially restricted
    query alerts."""
    # is this a predefined popular query?
    res = run_sql("""SELECT COUNT(*) FROM query
                      WHERE id=%s AND type='p'""", (id_query,))
    if res and res[0][0]:
        return True
    # has the user performed this query in the past?
    res = run_sql("""SELECT COUNT(*) FROM user_query
                      WHERE id_query=%s AND id_user=%s""", (id_query, id_user))
    if res and res[0][0]:
        return True
    return False

def perform_input_alert(action, id_query, alert_name, frequency, notification, id_basket, uid, old_id_basket=None, ln = CFG_SITE_LANG):
    """get the alert settings
    input:  action="add" for a new alert (blank form), action="modify" for an update
            (get old values)
            id_query id the identifier of the search to be alerted
            for the "modify" action specify old alert_name, frequency of checking,
            e-mail notification and basket id.
    output: alert settings input form"""
    # load the right language
    _ = gettext_set_language(ln)
    # security check:
    if not check_user_can_add_alert(uid, id_query):
        raise AlertError(_("You do not have rights for this operation."))
    # display query information
    res = run_sql("SELECT urlargs FROM query WHERE id=%s", (id_query,))
    try:
        urlargs = res[0][0]
    except:
        urlargs = "UNKNOWN"
    baskets = create_personal_baskets_selection_box(uid=uid,
                                                    html_select_box_name='idb',
                                                    selected_bskid=old_id_basket,
                                                    ln=ln)
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
             guest = isGuestUser(uid),
             guesttxt = warning_guest_user(type="alerts", ln=ln)
           )

def check_alert_is_unique(id_basket, id_query, uid, ln=CFG_SITE_LANG ):
    """check the user does not have another alert for the specified query and basket"""
    _ = gettext_set_language(ln)
    sql = """select id_query
            from user_query_basket
            where id_user = %s and id_query = %s
            and id_basket = %s"""
    res =  run_sql(sql, (uid, id_query, id_basket))
    if len(res):
        raise AlertError(_("You already have an alert defined for the specified query and basket."))

def perform_add_alert(alert_name, frequency, notification,
                      id_basket, id_query, uid, ln = CFG_SITE_LANG):
    """add an alert to the database
    input:  the name of the new alert;
            alert frequency: 'month', 'week' or 'day';
            setting for e-mail notification: 'y' for yes, 'n' for no;
            basket identifier: 'no' for no basket;
            new basket name for this alert;
            identifier of the query to be alerted
    output: confirmation message + the list of alerts Web page"""
    # sanity check
    if (None in (alert_name, frequency, notification, id_basket, id_query, uid)):
        return ''
    # load the right language
    _ = gettext_set_language(ln)
    # security check:
    if not check_user_can_add_alert(uid, id_query):
        raise AlertError(_("You do not have rights for this operation."))
    # check the alert name is not empty
    alert_name = alert_name.strip()
    if alert_name == "":
        raise AlertError(_("The alert name cannot be empty."))
    # check if the alert can be created
    check_alert_name(alert_name, uid, ln)
    check_alert_is_unique(id_basket, id_query, uid, ln)
    if id_basket != 0 and not check_user_owns_baskets(uid, id_basket):
        raise AlertError( _("You are not the owner of this basket.") )

    # add a row to the alerts table: user_query_basket
    query = """INSERT INTO user_query_basket (id_user, id_query, id_basket,
                                              frequency, date_creation, date_lastrun,
                                              alert_name, notification)
               VALUES (%s,%s,%s,%s,%s,'',%s,%s)"""
    params = (uid, id_query, id_basket,
              frequency, convert_datestruct_to_datetext(time.localtime()),
              alert_name, notification)
    run_sql(query, params)
    out = _("The alert %(x_name)s has been added to your profile.", x_name='<b>' + cgi.escape(alert_name) + '</b>')
    # out %= '<b>' + cgi.escape(alert_name) + '</b>'
    out += perform_list_alerts(uid, ln=ln)
    return out

def perform_list_alerts(uid, ln=CFG_SITE_LANG):
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
                WHERE a.id_user=%s
                ORDER BY a.alert_name ASC """
    res = run_sql(query, (uid,))
    alerts = []
    for (qry_id, qry_args,
         bsk_id, bsk_name,
         alrt_name, alrt_frequency, alrt_notification, alrt_creation, alrt_last_run) in res:
        try:
            if not qry_id:
                raise StandardError("""\
Warning: I have detected a bad alert for user id %d.
It seems one of his/her alert queries was deleted from the 'query' table.
Please check this and delete it if needed.
Otherwise no problem, I'm continuing with the other alerts now.
Here are all the alerts defined by this user: %s""" % (uid, repr(res)))
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
        except StandardError:
            register_exception(alert_admin=True)

    # link to the "add new alert" form
    out = webalert_templates.tmpl_list_alerts(ln=ln, alerts=alerts,
                                              guest=isGuestUser(uid),
                                              guesttxt=warning_guest_user(type="alerts", ln=ln))
    return out

def perform_remove_alert(alert_name, id_query, id_basket, uid, ln=CFG_SITE_LANG):
    """perform_remove_alert: remove an alert from the database
    input:  alert name
            identifier of the query;
            identifier of the basket
            uid
    output: confirmation message + the list of alerts Web page"""
    # load the right language
    _ = gettext_set_language(ln)
    # security check:
    if not check_user_can_add_alert(uid, id_query):
        raise AlertError(_("You do not have rights for this operation."))
    # set variables
    out = ""
    if (None in (alert_name, id_query, id_basket, uid)):
        return out
    # remove a row from the alerts table: user_query_basket
    query = """DELETE FROM user_query_basket
               WHERE id_user=%s AND id_query=%s AND id_basket=%s"""
    params = (uid, id_query, id_basket)
    res = run_sql(query, params)
    if res:
        out += "The alert <b>%s</b> has been removed from your profile.<br /><br />\n" % cgi.escape(alert_name)
    else:
        out += "Unable to remove alert <b>%s</b>.<br /><br />\n" % cgi.escape(alert_name)
    out += perform_list_alerts(uid, ln=ln)
    return out


def perform_update_alert(alert_name, frequency, notification, id_basket, id_query, old_id_basket, uid, ln = CFG_SITE_LANG):
    """update alert settings into the database
    input:  the name of the new alert;
            alert frequency: 'month', 'week' or 'day';
            setting for e-mail notification: 'y' for yes, 'n' for no;
            new basket identifier: 'no' for no basket;
            new basket name for this alert;
            identifier of the query to be alerted
            old identifier of the basket associated to the alert
    output: confirmation message + the list of alerts Web page"""
    out = ''
    # sanity check
    if (None in (alert_name, frequency, notification, id_basket, id_query, old_id_basket, uid)):
        return out

    # load the right language
    _ = gettext_set_language(ln)

    # security check:
    if not check_user_can_add_alert(uid, id_query):
        raise AlertError(_("You do not have rights for this operation."))

    # check the alert name is not empty
    if alert_name.strip() == "":
        raise AlertError(_("The alert name cannot be empty."))

    # check if the alert can be created
    sql = """select alert_name
            from user_query_basket
            where id_user=%s
            and id_basket=%s
            and id_query=%s"""
    try:
        old_alert_name = run_sql(sql, (uid, old_id_basket, id_query))[0][0]
    except IndexError:
        # FIXME: I18N since this technique of the below raise message,
        # since this technique (detecting old alert IDs) is not nice
        # and should be replaced some day soon.
        raise AlertError("Unable to detect old alert name.")
    if old_alert_name.strip()!="" and old_alert_name != alert_name:
        check_alert_name( alert_name, uid, ln)
    if id_basket != old_id_basket:
        check_alert_is_unique( id_basket, id_query, uid, ln)

    # update a row into the alerts table: user_query_basket
    query = """UPDATE user_query_basket
               SET alert_name=%s,frequency=%s,notification=%s,
                   date_creation=%s,date_lastrun='',id_basket=%s
               WHERE id_user=%s AND id_query=%s AND id_basket=%s"""
    params = (alert_name, frequency, notification,
              convert_datestruct_to_datetext(time.localtime()),
              id_basket, uid, id_query, old_id_basket)

    run_sql(query, params)

    out += _("The alert %(x_name)s has been successfully updated.", x_name=("<b>" + cgi.escape(alert_name) + "</b>",))
    out += "<br /><br />\n" + perform_list_alerts(uid, ln=ln)
    return out

def is_selected(var, fld):
    "Checks if the two are equal, and if yes, returns ' selected'. Useful for select boxes."
    if var == fld:
        return " selected"
    else:
        return ""

def account_list_alerts(uid, ln=CFG_SITE_LANG):
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
                WHERE a.id_user=%s AND a.id_query=q.id
                ORDER BY a.alert_name ASC """
    res = run_sql(query, (uid,))
    alerts = []
    if len(res):
        for row in res:
            alerts.append({
                            'id' : row[0],
                            'name' : row[5]
                          })

    return webalert_templates.tmpl_account_list_alerts(ln=ln, alerts=alerts)

def account_list_searches(uid, ln=CFG_SITE_LANG):
    """ account_list_searches: list the searches of the user
        input:  the user id
        output: resume of the searches"""
    out = ""
    # first detect number of queries:
    nb_queries_total = 0
    res = run_sql("SELECT COUNT(*) FROM user_query WHERE id_user=%s", (uid,), 1)
    try:
        nb_queries_total = res[0][0]
    except:
        pass

    # load the right language
    _ = gettext_set_language(ln)

    out += _("You have made %(x_nb)s queries. A %(x_url_open)sdetailed list%(x_url_close)s is available with a possibility to (a) view search results and (b) subscribe to an automatic email alerting service for these queries.") % {'x_nb': nb_queries_total, 'x_url_open': '<a href="../youralerts/display?ln=%s">' % ln, 'x_url_close': '</a>'}
    return out
