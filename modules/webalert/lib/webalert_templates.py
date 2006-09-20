## $Id$
##
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

__revision__ = "$Id$"

import time
import string

from invenio.config import \
     alertengineemail, \
     cdsname, \
     supportemail, \
     weburl
from invenio.messages import gettext_set_language
from invenio.htmlparser import get_as_text, wrap
from invenio.alert_engine_config import CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL

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
            out += "<strong>" + _("Pattern") + ":</strong> " + string.join(args['p'], "; ") + "<br />"
        if args.has_key('f'):
            out += "<strong>" + _("Field") + ":</strong> " + string.join(args['f'], "; ") + "<br />"
        if args.has_key('p1'):
            out += "<strong>" + _("Pattern 1") + ":</strong> " + string.join(args['p1'], "; ") + "<br />"
        if args.has_key('f1'):
            out += "<strong>" + _("Field 1") + ":</strong> " + string.join(args['f1'], "; ") + "<br />"
        if args.has_key('p2'):
            out += "<strong>" + _("Pattern 2") + ":</strong> " + string.join(args['p2'], "; ") + "<br />"
        if args.has_key('f2'):
            out += "<strong>" + _("Field 2") + ":</strong> " + string.join(args['f2'], "; ") + "<br />"
        if args.has_key('p3'):
            out += "<strong>" + _("Pattern 3") + ":</strong> " + string.join(args['p3'], "; ") + "<br />"
        if args.has_key('f3'):
            out += "<strong>" + _("Field 3") + ":</strong> " + string.join(args['f3'], "; ") + "<br />"
        if args.has_key('c'):
            out += "<strong>" + _("Collections") + ":</strong> " + string.join(args['c'], "; ") + "<br />"
        elif args.has_key('cc'):
            out += "<strong>" + _("Collection") + ":</strong> " + string.join(args['cc'], "; ") + "<br />"
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
            out += """<option value="%(id)s">%(name)s</option>""" % alert
        out += """</select>
                &nbsp;<code class="blocknote">
                <input class="formbutton" type="submit" name="action" value="%(show)s" /></code>
                </form>""" % {
                  'show' : _("SHOW"),
                }
        return out

    def tmpl_input_alert(self, ln, query, alert_name, action, frequency, notification, baskets, old_id_basket, id_basket, id_query):
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
              <table style="border: 0px; padding:10px;>
                <tr>
                   <td style="text-align: right; vertical-align:top; font-weight: bold;">%(alert_name)s:</td>
                   <td><input type="text" name="name" size="20" maxlength="50" value="%(alert)s"></td>
                </tr>
                <tr>
                  <td style="text-align: right; font-weight: bold;">%(freq)s:</td>
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
                 'alert' : alert_name,
                 'freq' : _("Search-checking frequency:"),
                 'freq_month' : (frequency == 'month' and 'selected="selected"' or ""),
                 'freq_week' : (frequency == 'week' and 'selected="selected"' or ""),
                 'freq_day' : (frequency == 'day' and 'selected="selected"' or ""),
                 'monthly' : _("monthly"),
                 'weekly' : _("weekly"),
                 'daily' : _("daily"),
                 'send_email' : _("Send notification email?"),
                 'notif_yes' : (notification == 'y' and "selected" or ""),
                 'notif_no' : (notification == 'n' and "selected" or ""),
                 'yes' : _("yes"),
                 'no' : _("no"),
                 'specify' : _("if %(x_fmt_open)sno%(x_fmt_close)s you must specify a basket") % {'x_fmt_open': '<b>', 
                                                                                                  'x_fmt_close': '</b>'},
                 'store_basket' : _("Store results in basket?"),
                 'baskets': baskets 
               }
        
        out += """  </td>
                   </tr>
                   <tr>
                    <td colspan="2" style="text-align:center">
                      <input type="hidden" name="idq" value="%(idq)s" />
                      <input type="hidden" name="ln" value="%(ln)s" />
                      <code class="blocknote"><input class="formbutton" type="submit" name="action" value="&nbsp;%(set_alert)s&nbsp;" /></code>&nbsp;
                      <code class="blocknote"><input class="formbutton" type="reset" value="%(clear_data)s" /></code>
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

        out = '<p>' + _("Set a new alert from %(x_url1_open)syour searches%(x_url1_close)s, the %(x_url2_open)spopular_searches%(x_url2_close)s, or the input form.") + '</p>'
        out %= {'x_url1_open': '<a href="display?ln=' + ln + '">', 
                'x_url1_close': '</a>',
                'x_url2_open': '<a href="display?ln=' + ln + '&amp;p=y">', 
                'x_url2_close': '</a>',
                }
        if len(alerts):
            out += """<table class="alrtTable">
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
                    frequency = _("daily"),
                else:
                    if alert['frequency'] == "week":
                        frequency = _("weekly")
                    else:
                        frequency = _("monthly")

                if alert['notification'] == "y":
                    notification = _("yes")
                else:
                    notification = _("no")

                out += """<tr>
                              <td style="font-style: italic">#%(index)d</td>
                              <td style="font-weight: bold; text-wrap:none;">%(alertname)s</td>
                              <td>%(frequency)s</td>
                              <td style="text-align:center">%(notification)s</td>
                              <td style="text-wrap:none;">%(basketname)s</td>
                              <td style="text-wrap:none;">%(lastrun)s</td>
                              <td style="text-wrap:none;">%(created)s</td>
                              <td>%(textargs)s</td>
                              <td>
                                 <a href="./remove?ln=%(ln)s&amp;name=%(alertname)s&amp;idu=%(userid)d&amp;idq=%(queryid)d&amp;idb=%(basketid)d">%(remove)s</a><br />
                                 <a href="./modify?ln=%(ln)s&amp;idq=%(queryid)d&amp;name=%(alertname)s&amp;freq=%(freq)s&amp;notif=%(notif)s&amp;idb=%(basketid)d&amp;old_idb=%(basketid)d">%(modify)s</a><br />
                                 <a href="%(weburl)s/search?%(queryargs)s&amp;ln=%(ln)s">%(search)s</a>
                             </td>
                            </tr>""" % {
                    'index' : i,
                    'alertname' : alert['alertname'],
                    'frequency' : frequency,
                    'notification' : notification,
                    'basketname' : alert['basketname'],
                    'lastrun' : alert['lastrun'],
                    'created' : alert['created'],
                    'textargs' : alert['textargs'],
                    'userid' : alert['userid'],
                    'queryid' : alert['queryid'],
                    'basketid' : alert['basketid'],
                    'freq' : alert['frequency'],
                    'notif' : alert['notification'],
                    'ln' : ln,
                    'remove' : _("Remove"),
                    'modify' : _("Modify"),
                    'weburl' : weburl,
                    'search' : _("Execute search"),
                    'queryargs' : alert['queryargs']
                  }

            out += '</table>'
              
        out += '<p>' + (_("You have defined %s alerts.") % ('<b>' + str(len(alerts)) + '</b>' )) + '</p>'
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
            out = _("You have not executed any search yet. Please go to the %(x_url_open)ssearch interface%(x_url_close)s first.") % \
                {'x_url_open': '<a href="' + weburl + '/?ln=' + ln +'">',
                 'x_url_close': '</a>'}
            return out

        out = ''
        
        # display message: number of items in the list
        if permanent == "n":
            msg = _("You have performed %(x_nb1)s searches (%(x_nb2)s different questions) during the last 30 days or so.") % {'x_nb1': nb_queries_total, 
                                                                                                                               'x_nb2': nb_queries_distinct}
            out += '<p>' + msg + '</p>'
        else:
            # permanent="y"
            msg = _("Here are the %s most popular searches.") 
            msg %= ('<b>' + str(len(queries)) + '</b>')
            out += '<p>' + msg + '</p>'

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
        if permanent == "n":
            out += '<td  style="font-weight: bold">%s</td>' % _("Last Run")
        out += "</tr>\n"
        i = 0
        for query in queries :
            i += 1
            # id, pattern, base, search url and search set alert, date
            out += """<tr>
                        <td style="font-style: italic;">#%(index)d</TD>
                        <td>%(textargs)s</td>
                        <td><a href="%(weburl)s/search?%(args)s">%(execute_query)s</a><br />
                            <a href="./input?ln=%(ln)s&idq=%(id)d">%(set_alert)s</A></td>""" % {
                     'index' : i,
                     'textargs' : query['textargs'],
                     'weburl' : weburl,
                     'args' : query['args'],
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

    def tmpl_alert_email_headers(self, name, headers):
        
        headers['Subject'] = 'Alert %s run on %s' % (
            name, time.strftime("%Y-%m-%d"))
        
        headers['From'] = 'CDS Alert Engine <%s>' % alertengineemail

    
    def tmpl_alert_email_body(self, name, url, records, pattern,
                              catalogues, frequency):

        l = len(catalogues)
        if l == 0:
            collections = ''
        elif l == 1:
            collections = "collection: %s\n" % catalogues[0]
        else:
            collections = "collections: %s\n" % wrap(', '.join(catalogues))

        if pattern:
            pattern = 'pattern: %s\n' % pattern

        frequency = {'day': 'daily',
                     'month': 'monthly',
                     'year': 'yearly'}[frequency]

        l = len(records)
        if l == 1:
            total = '1 record'
        else:
            total = '%d records' % l

        
        body = """\
Hello:

Below are the results of the email notification alert that
you set up with the %(cdsname)s.
This is an automatic message, please don't reply to it.
For any question, please use <%(supportemail)s> instead.

alert name: %(name)s
%(pattern)s%(collections)sfrequency: %(frequency)s
run time: %(runtime)s
found: %(total)s
url: <%(url)s>
""" % {'supportemail': supportemail,
       'name': name,
       'cdsname': cdsname,
       'pattern': pattern,
       'collections': collections,
       'frequency': frequency,
       'runtime': time.strftime("%a %Y-%m-%d %H:%M:%S"),
       'total': total,
       'url': url}
        
        
        for index, recid in enumerate(records[:CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL]):
            body += "\n%i) " % (index + 1)
            body += self.tmpl_alert_email_record(recid)
            body += "\n"

        if len(records) > CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL:
            body += '''
Only the first %s records were displayed.  Please consult the search
URL given at the top of this email to see all the results.
''' % CFG_WEBALERT_MAX_NUM_OF_RECORDS_IN_ALERT_EMAIL


        body += '''
-- 
%s Alert Service <%s>
Unsubscribe?  See <%s>
Need human intervention?  Contact <%s>
''' % (cdsname, weburl, weburl + '/youralerts/list', supportemail)
        
        return body


    def tmpl_alert_email_record(self, recid):
        """ Format a single record."""

        out = wrap(get_as_text(recid))
        out += "Detailed record: <%s/record/%s>" % (weburl, recid)
        return out 
