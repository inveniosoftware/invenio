# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

__revision__ = "$Id$"

import cgi
import time

from invenio.config import \
     CFG_WEBALERT_ALERT_ENGINE_EMAIL, \
     CFG_SITE_NAME, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_SITE_URL, \
     CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL, \
     CFG_SITE_RECORD
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webalert.htmlparser import get_as_text, wrap, wrap_records
from invenio.utils.url import create_html_link

from invenio.legacy.search_engine import guess_primary_collection_of_a_record, get_coll_ancestors

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
        if 'p' in args:
            out += "<strong>" + _("Pattern") + ":</strong> " + "; ".join(args['p']) + "<br />"
        if 'f' in args:
            out += "<strong>" + _("Field") + ":</strong> " + "; ".join(args['f']) + "<br />"
        if 'p1' in args:
            out += "<strong>" + _("Pattern 1") + ":</strong> " + "; ".join(args['p1']) + "<br />"
        if 'f1' in args:
            out += "<strong>" + _("Field 1") + ":</strong> " + "; ".join(args['f1']) + "<br />"
        if 'p2' in args:
            out += "<strong>" + _("Pattern 2") + ":</strong> " + "; ".join(args['p2']) + "<br />"
        if 'f2' in args:
            out += "<strong>" + _("Field 2") + ":</strong> " + "; ".join(args['f2']) + "<br />"
        if 'p3' in args:
            out += "<strong>" + _("Pattern 3") + ":</strong> " + "; ".join(args['p3']) + "<br />"
        if 'f3' in args:
            out += "<strong>" + _("Field 3") + ":</strong> " + "; ".join(args['f3']) + "<br />"
        if 'c' in args:
            out += "<strong>" + _("Collections") + ":</strong> " + "; ".join(args['c']) + "<br />"
        elif 'cc' in args:
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

        out = """<form name="displayalert" action="../youralerts/list" method="post">
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

    def tmpl_input_alert(self, ln, query, alert_name, action, frequency, notification,
                         baskets, old_id_basket, id_basket, id_query,
                         guest, guesttxt):
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
                      <td class="label label-info" style="text-align: left; vertical-align: top; max-width: 500px">%(query)s</td>
                    </tr>
                  </table>""" % {
                 'notify_cond' : _("This alert will notify you each time/only if a new item satisfies the following query:"),
                 'query_text' : _("QUERY"),
                 'query' : query,
               }

        out += """<form name="setalert" action="../youralerts/%(action)s" method="get"><br /><br />
        <table padding: 0px;">
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
                  <td>%(baskets)s
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
                 'specify' : _("if %(x_fmt_open)sno%(x_fmt_close)s you must specify a basket",
                               x_fmt_open='<b>', x_fmt_close='</b>'),
                 'store_basket' : _("Store results in basket?"),
                 'baskets': baskets
               }

        out += """  </td>
                   </tr>
                   <tr>
                    <td colspan="2" style="text-align:center">
                      <input type="hidden" name="idq" value="%(idq)s" />
                      <input type="hidden" name="ln" value="%(ln)s" />
                      <input class="btn btn-small btn-primary" type="submit" name="action" value="&nbsp;%(set_alert)s&nbsp;" />&nbsp;
                      <input class="btn btn-small btn-primary" type="reset" value="%(clear_data)s" />
                     </td>
                    </tr>
                   </table>
                  </td>
                 </tr>
                </table>
               """ % {
                     'idq' : id_query,
                     'ln' : ln,
                     'set_alert' : _("SET ALERT"),
                     'clear_data' : _("CLEAR DATA"),
                   }
        if action == "update":
            out += '<input type="hidden" name="old_idb" value="%s" />' % old_id_basket
        out += "</form>"

        if guest:
            out += guesttxt

        return out

    def tmpl_list_alerts(self, ln, alerts, guest, guesttxt):
        """
        Displays the list of alerts

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'alerts' *array* - The existing alerts:

              - 'queryid' *string* - The id of the associated query

              - 'queryargs' *string* - The query string

              - 'textargs' *string* - The textual description of the query string

              - 'userid' *string* - The user id

              - 'basketid' *string* - The basket id

              - 'basketname' *string* - The basket name

              - 'alertname' *string* - The alert name

              - 'frequency' *string* - The frequency of alert running ('day', 'week', 'month')

              - 'notification' *string* - If notification should be sent by email ('y', 'n')

              - 'created' *string* - The date of alert creation

              - 'lastrun' *string* - The last running date

          - 'guest' *bool* - If the user is a guest user

          - 'guesttxt' *string* - The HTML content of the warning box for guest users (produced by webaccount.tmpl_warning_guest_user)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '<p>'
        out += _("Set a new alert from %(x_url1_open)syour searches%(x_url1_close)s, the %(x_url2_open)spopular searches%(x_url2_close)s, or the input form.", **{
            'x_url1_open': '<a href="display?ln=' + ln + '">',
            'x_url1_close': '</a>',
            'x_url2_open': '<a href="display?ln=' + ln + '&amp;p=y">',
            'x_url2_close': '</a>',
            })
        out += '</p>'
        if len(alerts):
            out += """<table class="table table-hover">
                          <tr class="pageboxlefttop" style="text-align: center;">
                            <td style="font-weight: bold">%(no)s</td>
                            <td style="font-weight: bold">%(name)s</td>
                            <td style="font-weight: bold">%(search_freq)s</td>
                            <td style="font-weight: bold">%(notification)s</td>
                            <td style="font-weight: bold">%(result_basket)s</td>
                            <td style="font-weight: bold">%(date_run)s</td>
                            <td style="font-weight: bold">%(date_created)s</td>
                            <td style="font-weight: bold">%(query)s</td>
                            <td style="font-weight: bold">%(action)s</td></tr>""" % {
                       'no' : _("No"),
                       'name' : _("Name"),
                       'search_freq' : _("Search checking frequency"),
                       'notification' : _("Notification by email"),
                       'result_basket' : _("Result in basket"),
                       'date_run' : _("Date last run"),
                       'date_created' : _("Creation date"),
                       'query' : _("Query"),
                       'action' : _("Action"),
                     }
            i = 0
            for alert in alerts:
                i += 1
                if alert['frequency'] == "day":
                    frequency = _("daily")
                else:
                    if alert['frequency'] == "week":
                        frequency = _("weekly")
                    else:
                        frequency = _("monthly")

                if alert['notification'] == "y":
                    notification = _("yes")
                else:
                    notification = _("no")

                # we clean up the HH:MM part of lastrun, since it is always 00:00
                lastrun = alert['lastrun'].split(',')[0]
                created = alert['created'].split(',')[0]

                out += """<tr>
                              <td style="font-style: italic">#%(index)d</td>
                              <td style="font-weight: bold; text-wrap:none;">%(alertname)s</td>
                              <td>%(frequency)s</td>
                              <td style="text-align:center">%(notification)s</td>
                              <td style="text-wrap:none;">%(basketname)s</td>
                              <td style="text-wrap:none;">%(lastrun)s</td>
                              <td style="text-wrap:none;">%(created)s</td>
                              <td><span class="label label-info">%(textargs)s</span></td>
                              <td>
                                %(remove_link)s<br />
                                %(modify_link)s<br />
                                <a href="%(siteurl)s/search?%(queryargs)s&amp;ln=%(ln)s" style="white-space:nowrap">%(search)s</a>
                              </td>
                            </tr>""" % {
                    'index' : i,
                    'alertname' : cgi.escape(alert['alertname']),
                    'frequency' : frequency,
                    'notification' : notification,
                    'basketname' : alert['basketname'] and cgi.escape(alert['basketname']) \
                                                       or "- " + _("no basket") + " -",
                    'lastrun' : lastrun,
                    'created' : created,
                    'textargs' : alert['textargs'],
                    'queryid' : alert['queryid'],
                    'basketid' : alert['basketid'],
                    'freq' : alert['frequency'],
                    'notif' : alert['notification'],
                    'ln' : ln,
                    'modify_link': create_html_link("./modify",
                                                    {'ln': ln,
                                                     'idq': alert['queryid'],
                                                     'name': alert['alertname'],
                                                     'freq': frequency,
                                                     'notif':notification,
                                                     'idb':alert['basketid'],
                                                     'old_idb':alert['basketid']},
                                                    _("Modify")),
                    'remove_link': create_html_link("./remove",
                                                    {'ln': ln,
                                                     'idq': alert['queryid'],
                                                     'name': alert['alertname'],
                                                     'idb':alert['basketid']},
                                                    _("Remove")),
                    'siteurl' : CFG_SITE_URL,
                    'search' : _("Execute search"),
                    'queryargs' : cgi.escape(alert['queryargs'])
                  }

            out += '</table>'

        out += '<p>' + (_("You have defined %(num)s alerts.", num='<b>' + str(len(alerts)) + '</b>')) + '</p>'
        if guest:
            out += guesttxt
        return out

    def tmpl_display_alerts(self, ln, permanent, nb_queries_total, nb_queries_distinct, queries, guest, guesttxt):
        """
        Displays the list of alerts

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'permanent' *string* - If displaying most popular searches ('y') or only personal searches ('n')

          - 'nb_queries_total' *string* - The number of personal queries in the last period

          - 'nb_queries_distinct' *string* - The number of distinct queries in the last period

          - 'queries' *array* - The existing queries:

              - 'id' *string* - The id of the associated query

              - 'args' *string* - The query string

              - 'textargs' *string* - The textual description of the query string

              - 'lastrun' *string* - The last running date (only for personal queries)

          - 'guest' *bool* - If the user is a guest user

          - 'guesttxt' *string* - The HTML content of the warning box for guest users (produced by webaccount.tmpl_warning_guest_user)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if len(queries) == 0:
            out = _("You have not executed any search yet. Please go to the %(x_url_open)ssearch interface%(x_url_close)s first.",
                    x_url_open='<a href="' + CFG_SITE_URL + '/?ln=' + ln + '">',
                    x_url_close='</a>')
            return out

        out = ''

        # display message: number of items in the list
        if permanent == "n":
            msg = _("You have performed %(x_nb1)s searches (%(x_nb2)s different questions) during the last 30 days or so.",
                    x_nb1=nb_queries_total, x_nb2=nb_queries_distinct)
            out += '<p>' + msg + '</p>'
        else:
            # permanent="y"
            msg = _("Here are the %(x_name)s most popular searches.", x_name=('<b>' + str(len(queries)) + '</b>'))
            out += '<p>' + msg + '</p>'

        # display the list of searches
        out += """<table class="table table-hover">
                    <tr class="pageboxlefttop">
                      <td style="font-weight: bold">%(no)s</td>
                      <td style="font-weight: bold">%(question)s</td>
                      <td style="font-weight: bold">%(action)s</td>""" % {
                      'no' : "#",
                      'question' : _("Question"),
                      'action' : _("Action")
                    }
        if permanent == "n":
            out += '<td  style="font-weight: bold">%s</td>' % _("Last Run")
        out += "</tr>\n"
        i = 0
        for query in queries :
            i += 1
            # id, pattern, base, search url and search set alert, date
            out += """<tr>
                        <td style="font-style: italic;">#%(index)d</td>
                        <td><span class="label label-info">%(textargs)s</td></span>
                        <td><a href="%(siteurl)s/search?%(args)s&amp" class=" btn btn-mini btn-primary">%(execute_query)s</a>
                            <a href="%(siteurl)s/youralerts/input?ln=%(ln)s&amp;idq=%(id)d "class="btn btn-mini btn-primary">%(set_alert)s</a></td>""" % {
                     'index' : i,
                     'textargs' : query['textargs'],
                     'siteurl' : CFG_SITE_URL,
                     'args' : cgi.escape(query['args']),
                     'id' : query['id'],
                     'ln': ln,
                     'execute_query' : _("Execute search"),
                     'set_alert' : _("Set new alert")
                   }
            if permanent == "n":
                out += '<td>%s</td>' % query['lastrun']
            out += """</tr>\n"""
        out += "</table><br />\n"
        if guest :
            out += guesttxt

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
                if primary_collection not in recids_by_collection:
                    recids_by_collection[primary_collection] = []
                recids_by_collection[primary_collection].append(recid)
            else:
                ancestors = get_coll_ancestors(primary_collection)
                ancestors.reverse()
                nancestors = 0
                for ancestor in ancestors:
                    nancestors += 1
                    if ancestor in collection_list:
                        if ancestor not in recids_by_collection:
                            recids_by_collection[ancestor] = []
                        recids_by_collection[ancestor].append(recid)
                        break
                    elif len(ancestors) == nancestors:
                        if 'None of the above' not in recids_by_collection:
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
            if 'None of the above' in recids_by_collection:
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
''' % (CFG_SITE_NAME, CFG_SITE_URL, CFG_SITE_URL + '/youralerts/list', CFG_SITE_SUPPORT_EMAIL)

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
