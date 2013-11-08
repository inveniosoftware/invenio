## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

"""PERSONAL FEATURES - YOUR ALERTS"""

__revision__ = "$Id$"

import cgi
import time
from urllib import quote

from invenio.config import CFG_SITE_LANG
from invenio.dbquery import run_sql
from invenio.webuser import isGuestUser
from invenio.errorlib import register_exception
from invenio.webaccount import warning_guest_user
from invenio.webbasket import create_personal_baskets_selection_box
from invenio.webbasket_dblayer import check_user_owns_baskets
from invenio.messages import gettext_set_language
from invenio.dateutils import convert_datestruct_to_datetext

import invenio.template
webalert_templates = invenio.template.load('webalert')

CFG_WEBALERT_YOURALERTS_MAX_NUMBER_OF_DISPLAYED_ALERTS = 20

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
        raise AlertError( _("You already have an alert named %s.") % ('<b>' + cgi.escape(alert_name) + '</b>',) )

def get_textual_query_info_from_urlargs(urlargs, ln=CFG_SITE_LANG):
    """
    Return nicely formatted search pattern and catalogue from urlargs of the search query.
    """

    out = ""
    args = cgi.parse_qs(urlargs)
    return webalert_templates.tmpl_textual_query_info_from_urlargs(
             ln = ln,
             args = args,
           )
    return out

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

def perform_input_alert(action,
                        id_query,
                        alert_name,
                        frequency,
                        notification,
                        id_basket,
                        uid,
                        is_active,
                        old_id_basket=None,
                        ln = CFG_SITE_LANG):
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

    # normalize is_active (it should be either 1 (True) or 0 (False))
    is_active = is_active and 1 or 0

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
             is_active = is_active,
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
    out = _("The alert %s has been added to your profile.")
    out %= '<b>' + cgi.escape(alert_name) + '</b>'
    out += perform_request_youralerts_display(uid, idq=0, ln=ln)
    return out

def perform_request_youralerts_display(uid,
                                       idq=0,
                                       page=1,
                                       step=CFG_WEBALERT_YOURALERTS_MAX_NUMBER_OF_DISPLAYED_ALERTS,
                                       p='',
                                       ln=CFG_SITE_LANG):
    """
    Display a list of the user defined alerts. If a specific query id is defined
    only the user alerts based on that query appear.

    @param uid: The user id
    @type uid: int

    @param idq: The specified query id for which to display the user alerts
    @type idq: int

    @param page: 
    @type page: integer

    @param step: 
    @type step: integer

    @param ln: The interface language
    @type ln: string

    @return: HTML formatted list of the user defined alerts.
    """

    # set variables
    out = ""

    if idq:
        idq_clause = "q.id=%i" % (idq,)
    else:
        idq_clause = ""

    search_clause = ""
    search_clause_urlargs = []
    search_clause_alert_name = []
    if p:
        p_stripped_args = p.split()
        sql_p_stripped_args = ['\'%%' + quote(p_stripped_arg).replace('%','%%') + '%%\'' for p_stripped_arg in p_stripped_args]
        for sql_p_stripped_arg in sql_p_stripped_args:
            search_clause_urlargs.append("q.urlargs LIKE %s" % (sql_p_stripped_arg,))
            search_clause_alert_name.append("uqb.alert_name LIKE %s" % (sql_p_stripped_arg,))
        search_clause = "((%s) OR (%s))" % (" AND ".join(search_clause_urlargs),
                                                " AND ".join(search_clause_alert_name))

    query_nb_alerts = """   SELECT      COUNT(IF((uqb.id_user=%%s
                                                  %s),uqb.id_query,NULL)),
                                        COUNT(q.id)
                            FROM        user_query_basket AS uqb
                            RIGHT JOIN  query AS q
                                ON      uqb.id_query=q.id
                                %s""" % ((search_clause and ' AND ' + search_clause),
                                         (idq_clause and ' WHERE ' + idq_clause))
    params_nb_alerts = (uid,)
    result_nb_alerts = run_sql(query_nb_alerts, params_nb_alerts)
    nb_alerts = result_nb_alerts[0][0]
    nb_queries = result_nb_alerts[0][1]

    # In case we do have some alerts, proceed with the needed calculations and
    # fetching them from the database
    if nb_alerts:
        # The real page starts counting from 0, i.e. minus 1 from the human page
        real_page = page - 1
        # The step needs to be a positive integer
        if (step <= 0):
            step = CFG_WEBALERT_YOURALERTS_MAX_NUMBER_OF_DISPLAYED_ALERTS
        # The maximum real page is the integer division of the total number of
        # searches and the searches displayed per page
        max_real_page = nb_alerts and ((nb_alerts / step) - (not (nb_alerts % step) and 1 or 0))
        # Check if the selected real page exceeds the maximum real page and reset
        # if needed
        if (real_page >= max_real_page):
            #if ((nb_queries_distinct % step) != 0):
            #    real_page = max_real_page
            #else:
            #    real_page = max_real_page - 1
            real_page = max_real_page
            page = real_page + 1
        elif (real_page < 0):
            real_page = 0
            page = 1
        # Calculate the start value for the SQL LIMIT constraint
        limit_start = real_page * step
        # Calculate the display of the paging navigation arrows for the template
        paging_navigation = (real_page >= 2,
                             real_page >= 1,
                             real_page <= (max_real_page - 1),
                             (real_page <= (max_real_page - 2)) and (max_real_page + 1))

        query = """ SELECT      q.id,
                                q.urlargs,
                                uqb.id_basket,
                                bsk.name,
                                uqb.alert_name,
                                uqb.frequency,
                                uqb.notification,
                                DATE_FORMAT(uqb.date_creation,'%s'),
                                DATE_FORMAT(uqb.date_lastrun,'%s'),
                                uqb.is_active
                    FROM        user_query_basket uqb
                    LEFT JOIN   query q
                        ON      uqb.id_query=q.id
                    LEFT JOIN   bskBASKET bsk
                        ON      uqb.id_basket=bsk.id
                    WHERE       uqb.id_user=%%s
                        %s
                        %s
                    ORDER BY    uqb.alert_name ASC
                    LIMIT       %%s,%%s""" % ('%%Y-%%m-%%d %%H:%%i:%%s',
                                              '%%Y-%%m-%%d %%H:%%i:%%s',
                                              (idq_clause and ' AND ' + idq_clause),
                                              (search_clause and ' AND ' + search_clause))
        params = (uid, limit_start, step)
        result = run_sql(query, params)

        alerts = []
        for (query_id,
             query_args,
             bsk_id,
             bsk_name,
             alert_name,
             alert_frequency,
             alert_notification,
             alert_creation,
             alert_last_run,
             alert_is_active) in result:
            try:
                if not query_id:
                    raise StandardError("""\
Warning: I have detected a bad alert for user id %d.
It seems one of his/her alert queries was deleted from the 'query' table.
Please check this and delete it if needed.
Otherwise no problem, I'm continuing with the other alerts now.
Here are all the alerts defined by this user: %s""" % (uid, repr(result)))
                alerts.append({'queryid'      : query_id,
                               'queryargs'    : query_args,
                               'textargs'     : get_textual_query_info_from_urlargs(query_args, ln=ln),
                               'userid'       : uid,
                               'basketid'     : bsk_id,
                               'basketname'   : bsk_name,
                               'alertname'    : alert_name,
                               'frequency'    : alert_frequency,
                               'notification' : alert_notification,
                               'created'      : alert_creation,
                               'lastrun'      : alert_last_run,
                               'is_active'    : alert_is_active})
            except StandardError:
                register_exception(alert_admin=True)
    else:
        alerts = []
        paging_navigation = ()

    out = webalert_templates.tmpl_youralerts_display(ln=ln,
                                                     alerts=alerts,
                                                     nb_alerts=nb_alerts,
                                                     nb_queries=nb_queries,
                                                     idq=idq,
                                                     page=page,
                                                     step=step,
                                                     paging_navigation=paging_navigation,
                                                     p=p)
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
    out += perform_request_youralerts_display(uid, idq=0, ln=ln)
    return out

def perform_pause_alert(alert_name, id_query, id_basket, uid, ln=CFG_SITE_LANG):
    """Pause an alert
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

    # DB call to pause the alert
    query = """ UPDATE  user_query_basket
                SET     is_active = 0
                WHERE   id_user=%s
                    AND id_query=%s
                    AND id_basket=%s"""
    params = (uid, id_query, id_basket)
    res = run_sql(query, params)

    if res:
        out += '<p class="info">%s</p>' % _('Alert successfully paused.')
    else:
        out += '<p class="warning">%s</p>' % _('Unable to pause alert.')

    out += perform_request_youralerts_display(uid, idq=0, ln=ln)

    return out

def perform_resume_alert(alert_name, id_query, id_basket, uid, ln=CFG_SITE_LANG):
    """Resume an alert
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

    # DB call to resume the alert
    query = """ UPDATE  user_query_basket
                SET     is_active = 1
                WHERE   id_user=%s
                    AND id_query=%s
                    AND id_basket=%s"""
    params = (uid, id_query, id_basket)
    res = run_sql(query, params)

    if res:
        out += '<p class="info">%s</p>' % _('Alert successfully resumed.')
    else:
        out += '<p class="warning">%s</p>' % _('Unable to resume alert.')

    out += perform_request_youralerts_display(uid, idq=0, ln=ln)

    return out

def perform_update_alert(alert_name,
                         frequency,
                         notification,
                         id_basket,
                         id_query,
                         old_id_basket,
                         uid,
                         is_active,
                         ln = CFG_SITE_LANG):
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
    if (None in (alert_name, frequency, notification, id_basket, id_query, old_id_basket, uid, is_active)):
        return out

    # normalize is_active (it should be either 1 (True) or 0 (False))
    is_active = is_active and 1 or 0

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
    query = """ UPDATE  user_query_basket
                SET     alert_name=%s,
                        frequency=%s,
                        notification=%s,
                        date_creation=%s,
                        date_lastrun='',
                        id_basket=%s,
                        is_active=%s
                WHERE   id_user=%s
                    AND id_query=%s
                    AND id_basket=%s"""
    params = (alert_name, frequency, notification,
              convert_datestruct_to_datetext(time.localtime()),
              id_basket, is_active, uid, id_query, old_id_basket)

    run_sql(query, params)

    out += _("The alert %s has been successfully updated.") % ("<b>" + cgi.escape(alert_name) + "</b>",)
    out += "<br /><br />\n" + perform_request_youralerts_display(uid, idq=0, ln=ln)
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

def perform_request_youralerts_popular(ln=CFG_SITE_LANG):
    """
    Display popular alerts.
    @param uid: the user id
    @type uid: integer
    @return: A list of searches queries in formatted html.
    """
    
    # load the right language
    _ = gettext_set_language(ln)

    # fetch the popular queries
    query = """ SELECT      q.id,
                            q.urlargs
                FROM        query q
                WHERE       q.type='p'"""
    result = run_sql(query)

    search_queries = []
    if result:
        for search_query in result:
            search_query_id = search_query[0]
            search_query_args = search_query[1]
            search_queries.append({'id' : search_query_id,
                                   'args' : search_query_args,
                                   'textargs' : get_textual_query_info_from_urlargs(search_query_args, ln=ln)})

    return webalert_templates.tmpl_youralerts_popular(ln = ln,
                                                       search_queries = search_queries)

def count_user_alerts_for_given_query(id_user,
                                      id_query):
    """
    Count the alerts the user has defined based on a specific query.

    @param user_id: The user id.
    @type user_id: integer

    @param user_id: The query id.
    @type user_id: integer

    @return: The number of alerts.
    """

    query = """ SELECT  COUNT(id_query)
                FROM    user_query_basket AS uqb
                WHERE   id_user=%s
                    AND id_query=%s"""
    params = (id_user, id_query)
    result = run_sql(query, params)

    return result[0][0]
