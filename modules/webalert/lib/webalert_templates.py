## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

import cgi
import time
from urlparse import parse_qs
from datetime import date as datetime_date

from invenio.config import \
     CFG_WEBALERT_ALERT_ENGINE_EMAIL, \
     CFG_SITE_NAME, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_URL, \
     CFG_SITE_LANG, \
     CFG_SITE_SECURE_URL, \
     CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL, \
     CFG_SITE_RECORD
from invenio.messages import gettext_set_language
from invenio.htmlparser import get_as_text, wrap, wrap_records
from invenio.urlutils import create_html_link
from invenio.search_engine import guess_primary_collection_of_a_record, get_coll_ancestors
from invenio.dateutils import convert_datetext_to_datestruct

class Template:
    def tmpl_errorMsg(self, ln, error_msg, rest = ""):
        """
        Adds an error message to the output

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'error_msg' *string* - The error message

          - 'rest' *string* - The rest of the page
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<div class="quicknote">%(error)s</div><br />%(rest)s""" % {
                'error' : error_msg,
                'rest' : rest
              }
        return out

    def tmpl_textual_query_info_from_urlargs(self, ln, args):
        """
        Displays a human inteligible textual representation of a query

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'args' *array* - The URL arguments array (parsed)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        if args.has_key('p'):
            out += "<strong>" + _("Pattern") + ":</strong> " + "; ".join(args['p']) + "<br />"
        if args.has_key('f'):
            out += "<strong>" + _("Field") + ":</strong> " + "; ".join(args['f']) + "<br />"
        if args.has_key('p1'):
            out += "<strong>" + _("Pattern 1") + ":</strong> " + "; ".join(args['p1']) + "<br />"
        if args.has_key('f1'):
            out += "<strong>" + _("Field 1") + ":</strong> " + "; ".join(args['f1']) + "<br />"
        if args.has_key('p2'):
            out += "<strong>" + _("Pattern 2") + ":</strong> " + "; ".join(args['p2']) + "<br />"
        if args.has_key('f2'):
            out += "<strong>" + _("Field 2") + ":</strong> " + "; ".join(args['f2']) + "<br />"
        if args.has_key('p3'):
            out += "<strong>" + _("Pattern 3") + ":</strong> " + "; ".join(args['p3']) + "<br />"
        if args.has_key('f3'):
            out += "<strong>" + _("Field 3") + ":</strong> " + "; ".join(args['f3']) + "<br />"
        if args.has_key('c'):
            out += "<strong>" + _("Collections") + ":</strong> " + "; ".join(args['c']) + "<br />"
        elif args.has_key('cc'):
            out += "<strong>" + _("Collection") + ":</strong> " + "; ".join(args['cc']) + "<br />"
        return out

    def tmpl_account_list_alerts(self, ln, alerts):
        """
        Displays all the alerts in the main "Your account" page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'alerts' *array* - The existing alerts IDs ('id' + 'name' pairs)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<form name="displayalert" action="../youralerts/display" method="post">
                 %(you_own)s:
                <select name="id_alert">
                  <option value="0">- %(alert_name)s -</option>""" % {
                 'you_own' : _("You own the following alerts:"),
                 'alert_name' : _("alert name"),
               }
        for alert in alerts :
            out += """<option value="%(id)s">%(name)s</option>""" % \
                   {'id': alert['id'], 'name': cgi.escape(alert['name'])}
        out += """</select>
                &nbsp;<input class="formbutton" type="submit" name="action" value="%(show)s" />
                </form>""" % {
                  'show' : _("SHOW"),
                }
        return out

    def tmpl_input_alert(self,
                         ln,
                         query,
                         alert_name,
                         action,
                         frequency,
                         notification,
                         baskets,
                         old_id_basket,
                         id_basket,
                         id_query,
                         is_active,
                         guest,
                         guesttxt):
        """
        Displays an alert adding form.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'query' *string* - The HTML code of the textual representation of the query (as returned ultimately by tmpl_textual_query_info_from_urlargs...)

          - 'alert_name' *string* - The alert name

          - 'action' *string* - The action to complete ('update' or 'add')

          - 'frequency' *string* - The frequency of alert running ('day', 'week', 'month')

          - 'notification' *string* - If notification should be sent by email ('y', 'n')

          - 'baskets' *array* - The existing baskets ('id' + 'name' pairs)

          - 'old_id_basket' *string* - The id of the previous basket of this alert

          - 'id_basket' *string* - The id of the basket of this alert

          - 'id_query' *string* - The id of the query associated to this alert

          - 'is_active' *boolean* - is the alert active or not

          - 'guest' *bool* - If the user is a guest user

          - 'guesttxt' *string* - The HTML content of the warning box for guest users (produced by webaccount.tmpl_warning_guest_user)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        out += """<table style="border: 0px; padding: 2px; width: 650px;">
                    <tr><td colspan="3">%(notify_cond)s</td></tr>
                    <tr>
                      <td></td>
                      <td style="text-align: left; vertical-align: top; width: 10px; font-weight: bold;">%(query_text)s:</td>
                      <td style="text-align: left; vertical-align: top; width: 500px">%(query)s</td>
                    </tr>
                  </table>""" % {
                 'notify_cond' : _("This alert will notify you each time/only if a new item satisfies the following query:"),
                 'query_text' : _("QUERY"),
                 'query' : query,
               }

        out += """<form name="setalert" action="../youralerts/%(action)s" method="get">
        <table style="background-color:F1F1F1; border:thin groove grey; padding: 0px;">
          <tr>
            <td>
              <table style="border: 0px; padding:10px;">
                <tr>
                   <td style="text-align: right; vertical-align:top; font-weight: bold;">%(alert_name)s</td>
                   <td><input type="text" name="name" size="20" maxlength="30" value="%(alert)s" /></td>
                </tr>
                <tr>
                  <td style="text-align: right; font-weight: bold;">%(freq)s</td>
                  <td>
                    <select name="freq">
                      <option value="month" %(freq_month)s>%(monthly)s</option>
                      <option value="week" %(freq_week)s>%(weekly)s</option>
                      <option value="day" %(freq_day)s>%(daily)s</option>
                    </select>
                  </td>
                </tr>
                <tr>
                  <td style="text-align: right; vertical-align:top; font-weight: bold;">%(is_active_label)s</td>
                  <td><input type="checkbox" name="is_active" value="1" %(is_active_checkbox)s/></td>
                </tr>
                <tr>
                  <td style="text-align:right; font-weight: bold">%(send_email)s</td>
                  <td>
                    <select name="notif">
                      <option value="y" %(notif_yes)s>%(yes)s</option>
                      <option value="n" %(notif_no)s>%(no)s</option>
                    </select>
                    <small class="quicknote"> (%(specify)s)</small>
                  </td>
                </tr>
                <tr>
                  <td style="text-align: right; vertical-align:top; font-weight: bold;">%(store_basket)s</td>
                  <td>%(baskets)s</td>
                </tr>
               """ % {
                 'action': action,
                 'alert_name' : _("Alert identification name:"),
                 'alert' : cgi.escape(alert_name, 1),
                 'freq' : _("Search-checking frequency:"),
                 'freq_month' : (frequency == 'month' and 'selected="selected"' or ""),
                 'freq_week' : (frequency == 'week' and 'selected="selected"' or ""),
                 'freq_day' : (frequency == 'day' and 'selected="selected"' or ""),
                 'monthly' : _("monthly"),
                 'weekly' : _("weekly"),
                 'daily' : _("daily"),
                 'send_email' : _("Send notification email?"),
                 'notif_yes' : (notification == 'y' and 'selected="selected"' or ""),
                 'notif_no' : (notification == 'n' and 'selected="selected"' or ""),
                 'yes' : _("yes"),
                 'no' : _("no"),
                 'specify' : _("if %(x_fmt_open)sno%(x_fmt_close)s you must specify a basket") % {'x_fmt_open': '<b>',
                                                                                                  'x_fmt_close': '</b>'},
                 'store_basket' : _("Store results in basket?"),
                 'baskets': baskets,
                 'is_active_label' : _("Is the alert active?"),
                 'is_active_checkbox' : is_active and 'checked="checked" ' or '',
               }

        out += """<tr>
                    <td colspan="2" style="text-align:center">
                      <input type="hidden" name="idq" value="%(idq)s" />
                      <input type="hidden" name="ln" value="%(ln)s" />
                      <input class="formbutton" type="submit" name="action" value="&nbsp;%(set_alert)s&nbsp;" />&nbsp;
                      <input class="formbutton" type="reset" value="%(clear_data)s" />
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>""" % {'idq' : id_query,
                         'ln' : ln,
                         'set_alert' : _("SET ALERT"),
                         'clear_data' : _("CLEAR DATA"),}

        if action == "update":
            out += '<input type="hidden" name="old_idb" value="%s" />' % old_id_basket
        out += "</form>"

        if guest:
            out += guesttxt

        return out

    def tmpl_youralerts_display(self,
                                ln,
                                alerts,
                                nb_alerts,
                                nb_queries,
                                idq,
                                page,
                                step,
                                paging_navigation,
                                p,
                                popular_alerts_p):
        """
        Displays an HTML formatted list of the user alerts.
        If the user has specified a query id, only the user alerts based on that
        query will appear.

        @param ln: The language to display the interface in
        @type ln: string

        @param alerts: The user's alerts. A list of dictionaries each one consisting of:
            'queryid' *string* - The id of the associated query
            'queryargs' *string* - The query string
            'textargs' *string* - The textual description of the query string
            'userid' *string* - The user id
            'basketid' *string* - The basket id
            'basketname' *string* - The basket name
            'alertname' *string* - The alert name
            'frequency' *string* - The frequency of alert running ('day', 'week', 'month')
            'notification' *string* - If notification should be sent by email ('y', 'n')
            'created' *string* - The date of alert creation
            'lastrun' *string* - The last running date            
            'is_active' *boolean* - is the alert active or not
        @type alerts: list of dictionaries

        @param idq: The specified query id for which to display the user alerts
        @type idq: int

        @param page: the page to be displayed
        @type page: int

        @param step: the number of alerts to display per page
        @type step: int

        @param paging_navigation: values to help display the paging navigation arrows
        @type paging_navigation: tuple

        @param p: the search term (searching in alerts)
        @type p: string

        @param popular_alerts_p: are there any popular alerts already defined?
        @type popular_alerts_p: boolean
        """

        # load the right message language
        _ = gettext_set_language(ln)

        # In case the user has not yet defined any alerts display only the
        # following message
        if not nb_alerts:
            if idq and not p:
                if nb_queries:
                    msg = _('You have not defined any alerts yet based on that search query.')
                    msg += "<br />"
                    msg += _('You may want to %(new_alert)s or display all %(youralerts)s.') % \
                           {'new_alert': '<a href="%s/youralerts/input?ln=%s&amp;idq=%i">%s</a>' % (CFG_SITE_SECURE_URL, ln, idq, _('define one now')),
                            'youralerts': '<a href="%s/youralerts/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your alerts'))}
                else:
                    msg = _('The selected search query seems to be invalid.')
                    msg += "<br />"
                    msg += _('You may define new alert based on %(yoursearches)s%(popular_alerts)s or just by %(search_interface)s.') % \
                           {'yoursearches': '<a href="%s/yoursearches/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your searches')),
                            'popular_alerts': popular_alerts_p and ', <a href="%s/youralerts/popular?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('the popular alerts')) or '',
                            'search_interface': '<a href="%s/?ln=%s">%s</a>' %(CFG_SITE_URL, ln, _('searching for something new'))}
            elif p and not idq:
                msg = _('You have not defined any alerts yet including the terms %s.') % \
                      ('<strong>' + cgi.escape(p) + '</strong>',)
                msg += "<br />"
                msg += _('You may define new alert based on %(yoursearches)s%(popular_alerts)s or just by %(search_interface)s.') % \
                       {'yoursearches': '<a href="%s/yoursearches/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your searches')),
                        'popular_alerts': popular_alerts_p and ', <a href="%s/youralerts/popular?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('the popular alerts')) or '',
                        'search_interface': '<a href="%s/?ln=%s">%s</a>' %(CFG_SITE_URL, ln, _('searching for something new'))}
            elif p and idq:
                if nb_queries:
                    msg = _('You have not defined any alerts yet based on that search query including the terms %s.') % \
                          ('<strong>' + cgi.escape(p) + '</strong>',)
                    msg += "<br />"
                    msg += _('You may want to %(new_alert)s or display all %(youralerts)s.') % \
                           {'new_alert': '<a href="%s/youralerts/input?ln=%s&amp;idq=%i">%s</a>' % (CFG_SITE_SECURE_URL, ln, idq, _('define one now')),
                            'youralerts': '<a href="%s/youralerts/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your alerts'))}
                else:
                    msg = _('The selected search query seems to be invalid.')
                    msg += "<br />"
                    msg += _('You may define new alert based on %(yoursearches)s%(popular_alerts)s or just by %(search_interface)s.') % \
                           {'yoursearches': '<a href="%s/yoursearches/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your searches')),
                            'popular_alerts': popular_alerts_p and ', <a href="%s/youralerts/popular?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('the popular alerts')) or '',
                            'search_interface': '<a href="%s/?ln=%s">%s</a>' %(CFG_SITE_URL, ln, _('searching for something new'))}
            else:
                msg = _('You have not defined any alerts yet.')
                msg += '<br />'
                msg += _('You may define new alert based on %(yoursearches)s%(popular_alerts)s or just by %(search_interface)s.') % \
                       {'yoursearches': '<a href="%s/yoursearches/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your searches')),
                        'popular_alerts': popular_alerts_p and ', <a href="%s/youralerts/popular?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('the popular alerts')) or '',
                        'search_interface': '<a href="%s/?ln=%s">%s</a>' %(CFG_SITE_URL, ln, _('searching for something new'))}
            out = '<p>' + msg + '</p>'
            return out

        # Diplay a message about the number of alerts.
        if idq and not p:
            msg = _('You have defined %(number_of_alerts)s alerts based on that search query.') % \
                  {'number_of_alerts': '<strong>' + str(nb_alerts) + '</strong>'}
            msg += '<br />'
            msg += _('You may want to %(new_alert)s or display all %(youralerts)s.') % \
                   {'new_alert': '<a href="%s/youralerts/input?ln=%s&amp;idq=%i">%s</a>' % (CFG_SITE_SECURE_URL, ln, idq, _('define a new one')),
                    'youralerts': '<a href="%s/youralerts/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your alerts'))}
        elif p and not idq:
            msg = _('You have defined %(number_of_alerts)s alerts including the terms %(p)s.') % \
                  {'p': '<strong>' + cgi.escape(p) + '</strong>',
                   'number_of_alerts': '<strong>' + str(nb_alerts) + '</strong>'}
            msg += '<br />'
            msg += _('You may define new alert based on %(yoursearches)s%(popular_alerts)s or just by %(search_interface)s.') % \
                   {'yoursearches': '<a href="%s/yoursearches/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your searches')),
                    'popular_alerts': popular_alerts_p and ', <a href="%s/youralerts/popular?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('the popular alerts')) or '',
                    'search_interface': '<a href="%s/?ln=%s">%s</a>' %(CFG_SITE_URL, ln, _('searching for something new'))}
        elif idq and p:
            msg = _('You have defined %(number_of_alerts)s alerts based on that search query including the terms %(p)s.') % \
                  {'p': '<strong>' + cgi.escape(p) + '</strong>',
                   'number_of_alerts': '<strong>' + str(nb_alerts) + '</strong>'}
            msg += '<br />'
            msg += _('You may want to %(new_alert)s or display all %(youralerts)s.') % \
                   {'new_alert': '<a href="%s/youralerts/input?ln=%s&amp;idq=%i">%s</a>' % (CFG_SITE_SECURE_URL, ln, idq, _('define a new one')),
                    'youralerts': '<a href="%s/youralerts/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your alerts'))}
        else:
            msg = _('You have defined a total of %(number_of_alerts)s alerts.') % \
                  {'number_of_alerts': '<strong>' + str(nb_alerts) + '</strong>'}
            msg += '<br />'
            msg += _('You may define new alerts based on %(yoursearches)s%(popular_alerts)s or just by %(search_interface)s.') % \
                   {'yoursearches': '<a href="%s/yoursearches/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('your searches')),
                    'popular_alerts': popular_alerts_p and ', <a href="%s/youralerts/popular?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _('the popular alerts')) or '',
                    'search_interface': '<a href="%s/?ln=%s">%s</a>' %(CFG_SITE_URL, ln, _('searching for something new'))}
        out = '<p>' + msg + '</p>'

        # Search form
        search_form = """
        <form name="youralerts_search" action="%(action)s" method="get">
          <small><strong>%(search_text)s</strong></small>
          <input name="p" value="%(p)s" type="text" />
          <input class="formbutton" type="submit" value="%(submit_label)s" />
        </form>
        """ % {'search_text': _('Search all your alerts for'),
               'action': '%s/youralerts/display?ln=%s' % (CFG_SITE_SECURE_URL, ln),
               'p': cgi.escape(p),
               'submit_label': _('Search')}
        out += '<p>' + search_form + '</p>'

        counter = (page - 1) * step
        youralerts_display_html = ""
        for alert in alerts:
            counter += 1
            alert_name = alert['alertname']
            alert_query_id = alert['queryid']
            alert_query_args = alert['queryargs']
            # We don't need the text args, we'll use a local function to do a
            # better job.
            #alert_text_args = alert['textargs']
            # We don't need the user id. The alerts page is a logged in user
            # only page anyway.
            #alert_user_id = alert['userid']
            alert_basket_id = alert['basketid']
            alert_basket_name = alert['basketname']
            alert_frequency = alert['frequency']
            alert_notification = alert['notification']
            alert_creation_date = alert['created']
            alert_last_run_date = alert['lastrun']
            alert_active_p = alert['is_active']

            alert_details_frequency = _('Runs') + '&nbsp;' + \
                                      (alert_frequency == 'day' and '<strong>' + _('daily') + '</strong>' or \
                                       alert_frequency == 'week' and '<strong>' + _('weekly') + '</strong>' or \
                                       alert_frequency == 'month' and '<strong>' + _('monthly') + '</strong>')
            alert_details_notification = alert_notification == 'y' and _('You are notified by <strong>e-mail</strong>') or \
                                         alert_notification == 'n' and ''
            alert_details_basket = alert_basket_name and _('The results are automatically added to your basket:') + \
                                                         '&nbsp;' + '<strong>' + cgi.escape(alert_basket_name) + '</strong>' or ''
            alert_details_frequency_notification_basket = alert_details_frequency + \
                                                          (alert_details_notification and \
                                                           '&nbsp;/&nbsp;' + \
                                                           alert_details_notification) + \
                                                          (alert_details_basket and \
                                                           '&nbsp;/&nbsp;' + \
                                                           alert_details_basket)

            alert_details_search_query = get_html_user_friendly_alert_query_args(alert_query_args, ln)

            alert_details_creation_date = get_html_user_friendly_date_from_datetext(alert_creation_date, True, False, ln)
            alert_details_last_run_date = get_html_user_friendly_date_from_datetext(alert_last_run_date, True, False, ln)
            alert_details_creation_last_run_dates = _('Created:') + '&nbsp;' + \
                                                    alert_details_creation_date + \
                                                    '&nbsp;/&nbsp;' + \
                                                    _('Last run:') + '&nbsp;' + \
                                                    alert_details_last_run_date

            alert_details_options_pause_or_resume = create_html_link('%s/youralerts/%s' % \
                (CFG_SITE_SECURE_URL, alert_active_p and 'pause' or 'resume'),
                {'ln'     :   ln,
                 'idq'    :   alert_query_id,
                 'name'   :   alert_name,
                 'idb'    :   alert_basket_id,},
                alert_active_p and _('Pause') or _('Resume'))

            alert_details_options_edit = create_html_link('%s/youralerts/modify' % \
                                                          (CFG_SITE_SECURE_URL,),
                                                          {'ln'        : ln,
                                                           'idq'       : alert_query_id,
                                                           'name'      : alert_name,
                                                           'freq'      : alert_frequency,
                                                           'notif'     : alert_notification,
                                                           'idb'       : alert_basket_id,
                                                           'is_active' : alert_active_p,
                                                           'old_idb'   : alert_basket_id},
                                                          _('Edit'))

            alert_details_options_delete = create_html_link('%s/youralerts/remove' % \
                                                            (CFG_SITE_SECURE_URL,),
                                                            {'ln'     :   ln,
                                                             'idq'    :   alert_query_id,
                                                             'name'   :   alert_name,
                                                             'idb'    :   alert_basket_id},
                                                            _('Delete'),
                                                            {'onclick': 'return confirm(\'%s\')' % \
                                                             (_('Are you sure you want to permanently delete this alert?'),)})

            # TODO: find a nice way to format the display alert options
            alert_details_options = '<img src="%s/img/youralerts_alert_%s.png" />' % \
                                        (CFG_SITE_URL, alert_active_p and 'pause' or 'resume') + \
                                    alert_details_options_pause_or_resume + \
                                    '&nbsp;&middot;&nbsp;' + \
                                    '<img src="%s/img/youralerts_alert_edit.png" />&nbsp;' % \
                                        (CFG_SITE_URL,) + \
                                    alert_details_options_edit + \
                                    '&nbsp;&middot;&nbsp;' + \
                                    '<img src="%s/img/youralerts_alert_delete.png" />' % \
                                        (CFG_SITE_URL,) + \
                                    alert_details_options_delete

            youralerts_display_html += """
    <tr>
      <td class="youralerts_display_table_counter">
        %(counter)i.
      </td>
      <td class="youralerts_display_table_content" onMouseOver='this.className="youralerts_display_table_content_mouseover"' onMouseOut='this.className="youralerts_display_table_content"'>
        <div class="youralerts_display_table_content_container_main%(css_class_content_is_active_p)s">
          <div class="youralerts_display_table_content_name">%(warning_label_is_active_p)s%(alert_name)s</div>
          <div class="youralerts_display_table_content_details">%(alert_details_frequency_notification_basket)s</div>
          <div class="youralerts_display_table_content_search_query">%(alert_details_search_query)s</div>
        </div>
        <div class="youralerts_display_table_content_clear"></div>
        <div class="youralerts_display_table_content_container_left">
          <div class="youralerts_display_table_content_options">%(alert_details_options)s</div>
        </div>
        <div class="youralerts_display_table_content_container_right">
          <div class="youralerts_display_table_content_dates">%(alert_details_creation_last_run_dates)s</div>
        </div>
      </td>
    </tr>""" % {'counter': counter,
                'alert_name': cgi.escape(alert_name),
                'alert_details_frequency_notification_basket': alert_details_frequency_notification_basket,
                'alert_details_search_query': alert_details_search_query,
                'alert_details_options': alert_details_options,
                'alert_details_creation_last_run_dates': alert_details_creation_last_run_dates,
                'css_class_content_is_active_p' : not alert_active_p and ' youralerts_display_table_content_inactive' or '',
                'warning_label_is_active_p' : not alert_active_p and '<span class="warning">[&nbsp;%s&nbsp;]&nbsp;</span>' % _('paused') or '',
               }

        paging_navigation_html = ''
        if paging_navigation[0]:
            paging_navigation_html += """<a href="%s/youralerts/display?page=%i&amp;step=%i&amp;idq=%i&amp;ln=%s"><img src="%s" /></a>""" % \
                      (CFG_SITE_SECURE_URL, 1, step, idq, ln, '/img/sb.gif')
        if paging_navigation[1]:
            paging_navigation_html += """<a href="%s/youralerts/display?page=%i&amp;step=%i&amp;idq=%i&amp;ln=%s"><img src="%s" /></a>""" % \
                      (CFG_SITE_SECURE_URL, page - 1, step, idq, ln, '/img/sp.gif')
        paging_navigation_html += "&nbsp;"
        displayed_alerts_from = ((page - 1) * step) + 1
        displayed_alerts_to = paging_navigation[2] and (page * step) or nb_alerts
        paging_navigation_html += _('Displaying alerts <strong>%i to %i</strong> from <strong>%i</strong> total alerts') % \
               (displayed_alerts_from, displayed_alerts_to, nb_alerts)
        paging_navigation_html += "&nbsp;"
        if paging_navigation[2]:
            paging_navigation_html += """<a href="%s/youralerts/display?page=%i&amp;step=%i&amp;idq=%i&amp;ln=%s"><img src="%s" /></a>""" % \
                      (CFG_SITE_SECURE_URL, page + 1, step, idq, ln, '/img/sn.gif')
        if paging_navigation[3]:
            paging_navigation_html += """<a href="%s/youralerts/display?page=%i&amp;step=%i&amp;idq=%i&amp;ln=%s"><img src="%s" /></a>""" % \
                      (CFG_SITE_SECURE_URL, paging_navigation[3], step, idq, ln, '/img/se.gif')

        out += """
<table class="youralerts_display_table" cellspacing="0px">
  <thead class="youralerts_display_table_header">
    <tr>
      <td colspan="2">%(paging_navigation_html)s</td>
    </tr>
  </thead>
  <tfoot class="youralerts_display_table_footer">
    <tr>
      <td colspan="2">%(paging_navigation_html)s</td>
    </tr>
  </tfoot>
  <tbody>
    %(youralerts_display_html)s
  </tbody>
</table>""" % {'paging_navigation_html': paging_navigation_html,
               'youralerts_display_html': youralerts_display_html}

        return out

    def tmpl_alert_email_title(self, name):
        return 'Alert %s run on %s' % (
            name, time.strftime("%Y-%m-%d"))

    def tmpl_alert_email_from(self):
        return '%s Alert Engine <%s>' % (CFG_SITE_NAME, CFG_WEBALERT_ALERT_ENGINE_EMAIL)

    def tmpl_alert_email_body(self, name, description, url, records, pattern,
                              collection_list, frequency, add_to_basket_p):

        recids_by_collection = {}
        for recid in records[0]:
            primary_collection = guess_primary_collection_of_a_record(recid)
            if primary_collection in collection_list or \
                primary_collection == CFG_SITE_NAME: # common case, when the primary coll can not be guessed
                if not recids_by_collection.has_key(primary_collection):
                    recids_by_collection[primary_collection] = []
                recids_by_collection[primary_collection].append(recid)
            else:
                ancestors = get_coll_ancestors(primary_collection)
                ancestors.reverse()
                nancestors = 0
                for ancestor in ancestors:
                    nancestors += 1
                    if ancestor in collection_list:
                        if not recids_by_collection.has_key(ancestor):
                            recids_by_collection[ancestor] = []
                        recids_by_collection[ancestor].append(recid)
                        break
                    elif len(ancestors) == nancestors:
                        if not recids_by_collection.has_key('None of the above'):
                            recids_by_collection['None of the above'] = []
                        recids_by_collection['None of the above'].append(recid)

        collection_list = [coll for coll in recids_by_collection.keys() if coll != 'None of the above']
        for external_collection_results in records[1][0]:
            if external_collection_results[1][0]:
                collection_list.append(external_collection_results[0])

        l = len(collection_list)
        if l == 0:
            collections = ''
        elif l == 1:
            collections = "collection: %s\n" % collection_list[0]
        else:
            collections = "collections: %s\n" % wrap(', '.join(collection_list))

        l = len(records[0])
        for external_collection_results in records[1][0]:
            l += len(external_collection_results[1][0])
        if l == 1:
            total = '1 record'
        else:
            total = '%d records' % l

        if pattern:
            pattern = 'pattern: %s\n' % pattern

        frequency = {'day': 'daily',
                     'week': 'weekly',
                     'month': 'monthly'}[frequency]

        body = """\
Hello:

Below are the results of the email notification alert that
was set up with the %(sitename)s.
%(description)s
This is an automatic message, please don't reply to it.
For any question, please use <%(sitesupportemail)s> instead.

alert name: %(name)s
%(pattern)s%(collections)sfrequency: %(frequency)s
run time: %(runtime)s
found: %(total)s
url: <%(url)s>
""" % {'sitesupportemail': CFG_SITE_SUPPORT_EMAIL,
       'name': name,
       'sitename': CFG_SITE_NAME,
       'description': description and '\n' + description + '\n' or '',
       'pattern': pattern,
       'collections': collections,
       'frequency': frequency,
       'runtime': time.strftime("%a %Y-%m-%d %H:%M:%S"),
       'total': total,
       'url': url}

        index = 0

        for collection_recids in recids_by_collection.items():
            if collection_recids[0] != 'None of the above':
                body += "\nCollection: %s\n" % collection_recids[0]
                for recid in collection_recids[1]:
                    index += 1
                    body += "\n%i) " % (index)
                    body += self.tmpl_alert_email_record(recid=recid)
                    body += "\n"
                    if index == CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
                        break
                if index == CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
                    break

        if index < CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
            if recids_by_collection.has_key('None of the above'):
                if len(recids_by_collection.keys()) > 1:
                    body += "\nNone of the above collections:\n"
                else:
                    # if the uncategorized collection is the only collection then present
                    # all the records as belonging to CFG_SITE_NAME
                    body += "\nCollection: %s\n" % CFG_SITE_NAME
                for recid in recids_by_collection['None of the above']:
                    index += 1
                    body += "\n%i) " % (index)
                    body += self.tmpl_alert_email_record(recid=recid)
                    body += "\n"
                    if index == CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
                        break

        if index < CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
            for external_collection_results in records[1][0]:
                body += "\nCollection: %s\n" % external_collection_results[0]
                for recid in external_collection_results[1][0]:
                    index += 1
                    body += "\n%i) " % (index)
                    # TODO: extend function to accept xml_record!
                    body += self.tmpl_alert_email_record(xml_record=external_collection_results[1][1][recid])
                    body += "\n"
                    if index == CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
                        break
                if index == CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
                    break

        if l > CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
            body += '''
Only the first %s records were displayed. Please consult the search
URL given at the top of this email to see all the results.
''' % (CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL,)
            if add_to_basket_p:
                body += '''
Only the first %s records were added to your basket. To manually add more
records please consult the search URL as described before.
''' % (CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL,)


        body += '''
--
%s Alert Service <%s>
Unsubscribe?  See <%s>
Need human intervention?  Contact <%s>
''' % (CFG_SITE_NAME, CFG_SITE_URL, CFG_SITE_URL + '/youralerts/display', CFG_SITE_SUPPORT_EMAIL)

        return body


    def tmpl_alert_email_record(self, recid=0, xml_record=None):
        """ Format a single record."""

        if recid != 0:
            out = wrap_records(get_as_text(record_id=recid))
            out += "\nDetailed record: <%s/%s/%s>" % (CFG_SITE_URL, CFG_SITE_RECORD, recid)
        elif xml_record:
            out = wrap_records(get_as_text(xml_record=xml_record))
            # TODO: add Detailed record url for external records?
        return out

    def tmpl_youralerts_popular(self,
                                ln,
                                search_queries):
        """
        Display the popular alerts.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'search_queries' *array* - The existing queries:

              - 'id' *string* - The id of the associated query

              - 'args' *string* - The query string

              - 'textargs' *string* - The textual description of the query string

          - 'guest' *bool* - If the user is a guest user

          - 'guesttxt' *string* - The HTML content of the warning box for guest users (produced by webaccount.tmpl_warning_guest_user)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if not search_queries:
            out = _("There are no popular alerts defined yet.")
            return out

        out = ''

        # display the list of searches
        out += """<table class="alrtTable">
                    <tr class="pageboxlefttop">
                      <td style="font-weight: bold">%(no)s</td>
                      <td style="font-weight: bold">%(question)s</td>
                      <td style="font-weight: bold">%(action)s</td>""" % {
                      'no' : "#",
                      'question' : _("Question"),
                      'action' : _("Action")
                    }
        out += "</tr>\n"
        i = 0
        for search_query in search_queries :
            i += 1
            # id, pattern, base, search url and search set alert
            out += """<tr>
                        <td style="font-style: italic;">#%(index)d</td>
                        <td>%(textargs)s</td>
                        <td><a href="%(siteurl)s/search?%(args)s">%(execute_query)s</a><br />
                            <a href="%(siteurl)s/youralerts/input?ln=%(ln)s&amp;idq=%(id)d">%(set_alert)s</a></td>""" % {
                     'index' : i,
                     'textargs' : search_query['textargs'],
                     'siteurl' : CFG_SITE_URL,
                     'args' : cgi.escape(search_query['args']),
                     'id' : search_query['id'],
                     'ln': ln,
                     'execute_query' : _("Execute search"),
                     'set_alert' : _("Set new alert")
                   }
            out += """</tr>\n"""
        out += "</table><br />\n"

        return out

def get_html_user_friendly_alert_query_args(args,
                                             ln=CFG_SITE_LANG):
    """
    Internal function.
    Returns an HTML formatted user friendly description of a search query's
    arguments.

    @param args: The search query arguments as they apear in the search URL
    @type args: string

    @param ln: The language to display the interface in
    @type ln: string

    @return: HTML formatted user friendly description of a search query's
             arguments
    """

    # Load the right language
    _ = gettext_set_language(ln)

    # Arguments dictionary
    args_dict = parse_qs(args)

    if not args_dict.has_key('p') and not args_dict.has_key('p1') and not args_dict.has_key('p2') and not args_dict.has_key('p3'):
        search_patterns_html = _('Searching for everything')
    else:
        search_patterns_html = _('Searching for') + ' '
        if args_dict.has_key('p'):
            search_patterns_html += '<strong>' + cgi.escape(args_dict['p'][0]) + '</strong>'
            if args_dict.has_key('f'):
                search_patterns_html += ' ' + _('as') + ' ' + '<strong>' + cgi.escape(args_dict['f'][0]) + '</strong>'
        if args_dict.has_key('p1'):
            if args_dict.has_key('p'):
                search_patterns_html += ' ' + _('and') + ' '
            search_patterns_html += '<strong>' + cgi.escape(args_dict['p1'][0]) + '</strong>'
            if args_dict.has_key('f1'):
                search_patterns_html += ' ' + _('as') + ' ' + '<strong>' + cgi.escape(args_dict['f1'][0]) + '</strong>'
        if args_dict.has_key('p2'):
            if args_dict.has_key('p') or args_dict.has_key('p1'):
                if args_dict.has_key('op1'):
                    search_patterns_html += ' %s ' % (args_dict['op1'][0] == 'a' and _('and') or \
                                                      args_dict['op1'][0] == 'o' and _('or') or \
                                                      args_dict['op1'][0] == 'n' and _('and not') or
                                                      ', ',)
            search_patterns_html += '<strong>' + cgi.escape(args_dict['p2'][0]) + '</strong>'
            if args_dict.has_key('f2'):
                search_patterns_html += ' ' + _('as') + ' ' + '<strong>' + cgi.escape(args_dict['f2'][0]) + '</strong>'
        if args_dict.has_key('p3'):
            if args_dict.has_key('p') or args_dict.has_key('p1') or args_dict.has_key('p2'):
                if args_dict.has_key('op2'):
                    search_patterns_html += ' %s ' % (args_dict['op2'][0] == 'a' and _('and') or \
                                                      args_dict['op2'][0] == 'o' and _('or') or \
                                                      args_dict['op2'][0] == 'n' and _('and not') or
                                                      ', ',)
            search_patterns_html += '<strong>' + cgi.escape(args_dict['p3'][0]) + '</strong>'
            if args_dict.has_key('f3'):
                search_patterns_html += ' ' + _('as') + ' ' + '<strong>' + cgi.escape(args_dict['f3'][0]) + '</strong>'

    if not args_dict.has_key('c') and not args_dict.has_key('cc'):
        collections_html = _('in all the collections')
    else:
        collections_html = _('in the following collection(s)') + ': '
        if args_dict.has_key('c'):
            collections_html += ', '.join('<strong>' + cgi.escape(collection) + '</strong>' for collection in args_dict['c'])
        elif args_dict.has_key('cc'):
            collections_html += '<strong>' + cgi.escape(args_dict['cc'][0]) + '</strong>'

    search_query_args_html = search_patterns_html + '<br />' + collections_html

    return search_query_args_html


def get_html_user_friendly_date_from_datetext(given_date,
                                              show_full_date=True,
                                              show_full_time=True,
                                              ln=CFG_SITE_LANG):
    """
    Internal function.
    Returns an HTML formatted user friendly description of a search query's
    last run date.

    @param given_date: The search query last run date in the following format:
        '2005-11-16 15:11:57'
    @type given_date: string

    @param show_full_date: show the full date as well
    @type show_full_date: boolean

    @param show_full_time: show the full time as well
    @type show_full_time: boolean

    @param ln: The language to display the interface in
    @type ln: string

    @return: HTML formatted user friendly description of a search query's
             last run date
    """

    # Load the right language
    _ = gettext_set_language(ln)

    # Calculate how many days old the search query is base on the given date
    # and today
    # given_date_datestruct[0] --> year
    # given_date_datestruct[1] --> month
    # given_date_datestruct[2] --> day in month
    given_date_datestruct = convert_datetext_to_datestruct(given_date)
    today = datetime_date.today()
    if given_date_datestruct[0] != 0 and \
       given_date_datestruct[1] != 0 and \
       given_date_datestruct[2] != 0:
        days_old = (today - datetime_date(given_date_datestruct[0],
                                          given_date_datestruct[1],
                                          given_date_datestruct[2])).days
        if days_old == 0:
            out = _('Today')
        elif days_old < 7:
            out = str(days_old) + ' ' + _('day(s) ago')
        elif days_old == 7:
            out = _('A week ago')
        elif days_old < 14:
            out = _('More than a week ago')
        elif days_old == 14:
            out = _('Two weeks ago')
        elif days_old < 30:
            out = _('More than two weeks ago')
        elif days_old == 30:
            out = _('A month ago')
        elif days_old < 180:
            out = _('More than a month ago')
        elif days_old < 365:
            out = _('More than six months ago')
        else:
            out = _('More than a year ago')
        if show_full_date:
            out += '<span style="color: gray;">' + \
                   '&nbsp;' + _('on') + '&nbsp;' + \
                   given_date.split()[0] + '</span>'
            if show_full_time:
                out += '<span style="color: gray;">' + \
                       '&nbsp;' + _('at') + '&nbsp;' + \
                       given_date.split()[1] + '</span>'
    else:
        out = _('Unknown')

    return out
