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

import urllib
import time
import cgi
import gettext
import string
import locale
import re
import operator

from invenio.config import *
from invenio.messages import gettext_set_language
from invenio.htmlparser import get_as_text, wrap

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

        out = """<div class="quicknote">%(error)s</div><br>%(rest)s""" % {
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
            out += "<strong>" + _("Pattern") + ":</strong> " + string.join(args['p'], "; ") + "<br>"
        if args.has_key('f'):
            out += "<strong>" + _("Field") + ":</strong> " + string.join(args['f'], "; ") + "<br>"
        if args.has_key('p1'):
            out += "<strong>" + _("Pattern 1") + ":</strong> " + string.join(args['p1'], "; ") + "<br>"
        if args.has_key('f1'):
            out += "<strong>" + _("Field 1") + ":</strong> " + string.join(args['f1'], "; ") + "<br>"
        if args.has_key('p2'):
            out += "<strong>" + _("Pattern 2") + ":</strong> " + string.join(args['p2'], "; ") + "<br>"
        if args.has_key('f2'):
            out += "<strong>" + _("Field 2") + ":</strong> " + string.join(args['f2'], "; ") + "<br>"
        if args.has_key('p3'):
            out += "<strong>" + _("Pattern 3") + ":</strong> " + string.join(args['p3'], "; ") + "<br>"
        if args.has_key('f3'):
            out += "<strong>" + _("Field 3") + ":</strong> " + string.join(args['f3'], "; ") + "<br>"
        if args.has_key('c'):
            out += "<strong>" + _("Collections") + ":</strong> " + string.join(args['c'], "; ") + "<br>"
        elif args.has_key('cc'):
            out += "<strong>" + _("Collection") + ":</strong> " + string.join(args['cc'], "; ") + "<br>"
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

        out = """<FORM name="displayalert" action="../youralerts.py/list" method="post">
                 %(you_own)s
                <SELECT name="id_alert">
                  <OPTION value="0">- %(alert_name)s -</OPTION>""" % {
                 'you_own' : _("You own following alerts:"),
                 'alert_name' : _("alert name"),
               }
        for alert in alerts :
                  out += """<OPTION value="%(id)s">%(name)s</OPTION>""" % alert
        out += """</SELECT>
                &nbsp;<CODE class="blocknote">
                <INPUT class="formbutton" type="submit" name="action" value="%(show)s"></CODE>
                </FORM>""" % {
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
        out += """<TABLE border="0" cellspacing="0" cellpadding="2" width="650">
                    <TR><TD colspan="3">%(notify_cond)s </TD></TR>
                    <TR>
                      <TD>&nbsp;&nbsp;</TD>
                      <TD align="left" valign="top" width="10"><B>%(query_text)s:</B></TD>
                      <TD align="left" valign="top" width="500">%(query)s</TD></TR>
                  </TABLE>""" % {
                 'notify_cond' : _("This alert will notify you each time/only if a new item satisfy the following query"),
                 'query_text' : _("QUERY"),
                 'query' : query,
               }

        out += """<FORM name="setalert" action="../youralerts.py/%(action)s" method="get">
        <TABLE style="background-color:F1F1F1; border:thin groove grey" cellspacing="0" cellpadding="0"><TR><TD>
                    <TABLE border="0" cellpadding="0" cellspacing ="10">
                      <TR>
                        <TD align="right" valign="top"><B>%(alert_name)s</B></TD>
                        <TD><INPUT type="text" name="name" size="20" maxlength="50" value="%(alert)s"></TD>
                      </TR>
                      <TR><TD align="right"><B>%(freq)s</B></TD>
                          <TD><SELECT name="freq">
                                <OPTION value="month" %(freq_month)s>%(monthly)s</OPTION>
                             <OPTION value="week" %(freq_week)s>%(weekly)s</OPTION>
                             <OPTION value="day" %(freq_day)s>%(daily)s</OPTION></SELECT>
                         </TD>
                      </TR>
                      <TR>
                        <TD align="right"><B>%(send_email)s</B></TD>
                        <TD><SELECT name="notif">
                            <OPTION value="y" %(notif_yes)s>%(yes)s</OPTION>
                            <OPTION value="n"%(notif_no)s>%(no)s</OPTION></SELECT>
                            <SMALL class="quicknote"> (%(specify)s)</SMALL>&nbsp;
                        </TD>
                      </TR>
                      <TR>
                        <TD align="right" valign="top"><B>%(store_basket)s</B></TD>
                        <TD>%(baskets)s
               """ % {
                 'action': action,
                 'alert_name' : _("Alert identification name:"),
                 'alert' : alert_name,
                 'freq' : _("Search-checking frequency:"),
                 'freq_month' : (frequency == 'month' and "selected" or ""),
                 'freq_week' : (frequency == 'week' and "selected" or ""),
                 'freq_day' : (frequency == 'day' and "selected" or ""),
                 'monthly' : _("monthly"),
                 'weekly' : _("weekly"),
                 'daily' : _("daily"),
                 'send_email' : _("Send notification e-mail?"),
                 'notif_yes' : (notification == 'y' and "selected" or ""),
                 'notif_no' : (notification == 'n' and "selected" or ""),
                 'yes' : _("yes"),
                 'no' : _("no"),
                 'specify' : _("if <B>no</B> you must specify a basket"),
                 'store_basket' : _("Store results in basket?"),
                 'baskets': baskets 
               }
        
        out += """  </TD>
                   </TR>
                   <TR>
                    <TD colspan="2" align="center"><BR>
                      <INPUT type="hidden" name="idq" value="%(idq)s">
                      <CODE class="blocknote"><INPUT class="formbutton" type="submit" name="action" value="&nbsp;%(set_alert)s&nbsp;"></CODE>&nbsp;
                      <CODE class="blocknote"><INPUT class="formbutton" type="reset" value="%(clear_data)s"></CODE>
                     </TD>
                    </TR>
                   </TABLE>
                  </TD>
                 </TR>
                </TABLE>
               """ % {
                     'idq' : id_query,
                     'set_alert' : _("SET ALERT"),
                     'clear_data' : _("CLEAR DATA"),
                   }
        if action == "update":
            out += """<INPUT type="hidden" name="old_idb" value="%s">""" % old_id_basket
        out += "</FORM>"

        return out

    def tmpl_list_alerts(self, ln, weburl, alerts, guest, guesttxt):
        """
        Displays the list of alerts

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The url of CDS Invenio

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

        out = """<P>%(set_new_alert)s</P>""" % {
                'set_new_alert' : _("Set a new alert from %(your_searches)s, the %(popular_searches)s or the input form.") % {
                                    'your_searches' : """<A href="display">%s</A>""" % _("your searches"),
                                    'popular_searches' : """<A href="display?p='y'">%s</A>""" % _("most popular searches"),
                                  }
              }

        if len(alerts):
              out += """<TABLE border="1" cellspacing="0" cellpadding="3" width="100%%">
                          <TR class="pageboxlefttop" align="center">
                            <TD><B>%(no)s</B></TD>
                            <TD><B>%(name)s</B></TD>
                            <TD><B>%(search_freq)s</B></TD>
                            <TD><B>%(notification)s</B></TD>
                            <TD><B>%(result_basket)s</B></TD>
                            <TD><B>%(date_run)s</B></TD>
                            <TD><B>%(date_created)s</B></TD>
                            <TD><B>%(query)s</B></TD>
                            <TD><B>%(action)s</B></TD></TR>""" % {
                       'no' : _("No"),
                       'name' : _("Name"),
                       'search_freq' : _("Search checking frequency"),
                       'notification' : _("Notification by e-mail"),
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

                  out += """<TR>
                              <TD><I>#%(index)d</I></TD>
                             <TD><B><NOBR>%(alertname)s<NOBR></B></TD>
                             <TD>%(frequency)s</TD>
                             <TD align="center">%(notification)s</TD>
                             <TD><NOBR>%(basketname)s<NOBR></TD>
                             <TD><NOBR>%(lastrun)s<NOBR></TD>
                             <TD><NOBR>%(created)s<NOBR></TD>
                             <TD>%(textargs)s</TD>
                             <TD><A href="./remove?name=%(alertname)s&idu=%(userid)d&idq=%(queryid)d&idb=%(basketid)d">%(remove)s</A><BR>
                                 <A href="./modify?idq=%(queryid)d&name=%(alertname)s&freq=%(freq)s&notif=%(notif)s&idb=%(basketid)d&old_idb=%(basketid)d">%(modify)s</A><BR>
                                 <A href="%(weburl)s/search.py?%(queryargs)s">%(search)s</A>
                             </TD>
                            </TR>""" % {
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
                    'remove' : _("Remove"),
                    'modify' : _("Modify"),
                    'weburl' : weburl,
                    'search' : _("Execute search"),
                    'queryargs' : alert['queryargs']
                  }

              out += '</TABLE>'
              
        out += """<P>%(defined)s</P>""" % {
                 'defined' : _("You have defined <B>%(number)s</B> alerts.") % { 'number' : len(alerts)}
               }

        if guest:
            out += guesttxt

        return out

    def tmpl_display_alerts(self, ln, weburl, permanent, nb_queries_total, nb_queries_distinct, queries, guest, guesttxt):
        """
        Displays the list of alerts

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The url of CDS Invenio

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
            return _("You have not executed any search yet. %(click_here)s for search.") % {
                     'click_here' : """<a href="%(weburl)s/search.py">%(click)s</a>""" % {
                                      'weburl' : weburl,
                                      'click' : _("Click here"),
                                    }
                   }

        out = ''
        
        # display message: number of items in the list
        if permanent=="n":
            out += """<P>""" + _("You have performed <B>%(number)d</B> searches (<strong>%(different)d</strong> different questions) during the last 30 days or so.""") % {
                     'number' : nb_queries_total,
                     'different' : nb_queries_distinct
                   } + """</P>"""
        else:
            # permanent="y"
            out += """<P>Here are listed the <B>%s</B> most popular searches.</P>""" % len(query_result)

        # display the list of searches
        out += """<TABLE border="1" cellspacing="0" cellpadding="3" width="100%%">
                    <TR class="pageboxlefttop"><TD><B>%(no)s</B></TD><TD><B>%(question)s</B></TD>
                    <TD><B>%(action)s</B></TD>""" % {
                      'no' : _("#"),
                      'question' : _("Question"),
                      'action' : _("Action")
                    }
        if permanent=="n":
            out += """<TD><B>%s</B></TD>""" % _("Last Run")
        out += """</TR>\n"""
        i = 0
        for query in queries :
            i += 1
            # id, pattern, base, search url and search set alert, date
            out += """<TR>
                        <TD><I>#%(index)d</I></TD>
                        <TD>%(textargs)s</TD>
                        <TD><A href="%(weburl)s/search.py?%(args)s">%(execute_query)s</A><BR><A href="./input?idq=%(id)d">%(set_alert)s</A></TD>""" % {
                     'index' : i,
                     'textargs' : query['textargs'],
                     'weburl' : weburl,
                     'args' : query['args'],
                     'id' : query['id'],
                     'execute_query' : _("Execute search"),
                     'set_alert' : _("Set new alert")
                   }
            if permanent=="n":
                out += """<TD>%(lastrun)s</TD>""" % query
            out += """</TR>\n"""
        out += """</TABLE><BR>\n"""
        if guest :
            out += guesttxt

        return out

    def tmpl_alert_email_headers(self, name, headers):
        
        headers['Subject'] = 'Alert %s run on %s' % (
            name, time.strftime("%Y-%m-%d"))
        
        headers['From'] = 'CDS Alert Engine <%s>' % alertengineemail

    
    def tmpl_alert_email_body(self, name, url, records, pattern,
                              catalogues, frequency):

        MAXIDS = 5


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
Hello,

Below are the results of the email alert that you set up with the CERN
Document Server. This is an automatic message, please don't reply to
its address.  For any question, use <%(supportemail)s> instead.

alert name: %(name)s
%(pattern)s%(collections)sfrequency: %(frequency)s
run time: %(runtime)s
found: %(total)s
url: <%(url)s>


""" % {'supportemail': supportemail,
       'name': name,
       'pattern': pattern,
       'collections': collections,
       'frequency': frequency,
       'runtime': time.strftime("%a %Y-%m-%d %H:%M:%S"),
       'total': total,
       'url': url}
        
        
        for index, recid in enumerate(records[:MAXIDS]):
            body += self.tmpl_alert_email_record(index, recid)

        if len(records) > MAXIDS:
            body += '''

Only the first %s records were displayed.  Please consult the search
URL given at the top of this email to see all the results.
''' % MAXIDS


        body += '''

-- 
CDS Invenio Alert Service <%s>
Unsubscribe?  See <%s>
Need human intervention?  Contact <%s>
''' % (weburl, weburl + '/youralerts.py/list', supportemail)
        
        return body


    def tmpl_alert_email_record(self, index, recid):
        """ Format a single record."""

        return wrap('\n\n%s) %s' % (index+1, get_as_text(recid))) + '\n'
