# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011, 2013, 2014 CERN.
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
__lastupdated__ = "$Date$"

import datetime, cgi, urllib, os
import re
from invenio.config import \
     CFG_WEBDIR, \
     CFG_SITE_URL, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME
from invenio.legacy.webstat.engine import get_invenio_error_details

class Template:

    def tmpl_welcome(self, ln=CFG_SITE_LANG):
        """
        Generates a welcome page for the Webstat module.
        """
        return """<p>On these pages, you can review measurements of Invenio usage
                     and performance. Output is available in several formats, and its
                     raw data can be exported for offline processing. Further on, a general
                     overview is presented below under the label Current System Health.</p>"""

    def tmpl_system_health_list(self, recount, ln=CFG_SITE_LANG):
        """
        Generates a box with current information from the system providing the administrator
        an easy way of overlooking the 'health', i.e. the current performance/efficency, of
        the system.
        """
        temp_out = """<h3>Current system health</h3>
                    <p>Please, choose the information you want to review.</p>
                    <ul>
                    """
        if recount == 0:
            temp_out += """
                    <li class="warninggreen">
                        <a href="%s/stats/system_health%s">
                            Current system health</a>
                            (all records up to date!)</li>
                        """ % \
                    (CFG_SITE_URL, (CFG_SITE_LANG != ln and '?ln=' + ln) or '')
        else:
            temp_out += """
                    <li class="warningred">
                        <a href="%s/stats/system_health%s">
                            Current system health</a>
                            (around %s records pending)</li>
                        """ % \
                    (CFG_SITE_URL, (CFG_SITE_LANG != ln and '?ln=' + ln) \
                    or '', str(recount))
        temp_out += """
                    <li><a href="%s/stats/ingestion_health%s">
                        Check ingestion health for specific records</a></li>
                    </ul>
                    """ % \
                    (CFG_SITE_URL, (CFG_SITE_LANG != ln and '?ln=' + ln) or '')
        return temp_out

    def tmpl_system_health(self, health_statistics, ln=CFG_SITE_LANG):
        """
        Generates the system health list of parameters.
        """
        temp_out = ""
        for statistic in health_statistics:
            if statistic is None:
                temp_out += '\n'
            elif statistic[1] is None:
                temp_out += statistic[0] + '\n'
            else:
                # regular expression, just to extract the text
                # inside the link and view it's length
                aux = re.search('.*>(.*)<.*', str(statistic[1]))
                if aux is None:
                    temp_out += statistic[0] + " " + '.' * \
                                (85 - len(str(statistic[0])) - \
                                len(str(statistic[1]))) + " " + \
                                str(statistic[1]) + '\n'
                else:
                    temp_out += statistic[0] + " " + '.' * \
                                (85 - len(str(statistic[0])) - \
                                len(str(aux.group(1)))) + " " + \
                                str(statistic[1]) + '\n'
        temp_out = "<pre>" + temp_out + "</pre>"
        temp_out += '<a href="%s/stats/ingestion_health%s">Check ingestion \
                    health for specific records pending</a>' % (CFG_SITE_URL,
                    (CFG_SITE_LANG != ln and '?ln=' + ln) or '')
        return temp_out


    def tmpl_keyevent_list(self, ln=CFG_SITE_LANG):
        """
        Generates a list of available key statistics.
        """
        return """<h3>Key statistics</h3>
                  <p>Please choose a statistic from below to review it in detail.</p>
                  <ul>
                    <li><a href="%(CFG_SITE_URL)s/stats/collection_population%(ln_link)s">Collection population</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/new_records%(ln_link)s">New records</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/search_frequency%(ln_link)s">Search frequency</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/search_type_distribution%(ln_link)s">Search type distribution</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/download_frequency%(ln_link)s">Download frequency</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/comments_frequency%(ln_link)s">Comments frequency</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/number_of_loans%(ln_link)s">Number of circulation loans</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/web_submissions%(ln_link)s">Web submissions</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/loans_stats%(ln_link)s">Circulation loan statistics</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/loans_lists%(ln_link)s">Circulation loan lists</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/renewals_lists%(ln_link)s">Circulation renewals lists</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/returns_table%(ln_link)s">Number of circulation overdue returns</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/returns_graph%(ln_link)s">Percentage of circulation overdue returns</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/ill_requests_stats%(ln_link)s">Circulation ILL Requests statistics</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/ill_requests_lists%(ln_link)s">Circulation ILL Requests list</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/ill_requests_graph%(ln_link)s">Percentage of satisfied circulation ILL requests</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/items_stats%(ln_link)s">Circulation items statistics</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/items_list%(ln_link)s">Circulation items list</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/loans_requests%(ln_link)s">Circulation hold requests statistics</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/loans_request_lists%(ln_link)s">Circulation hold requests lists</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/user_stats%(ln_link)s">Circulation user statistics</a></li>
                    <li><a href="%(CFG_SITE_URL)s/stats/user_lists%(ln_link)s">Circulation user lists</a></li>
                  </ul>""" % {'CFG_SITE_URL': CFG_SITE_URL,
                              'ln_link': (CFG_SITE_LANG != ln and '?ln=' + ln) or ''}

    def tmpl_customevent_list(self, customevents, ln=CFG_SITE_LANG):
        """
        Generates a list of available custom statistics.
        """
        out = """<h3>Custom events</h3>
                 <p>The Webstat module supplies a mean for the administrators of Invenio
                 to define their own custom events, more abstract than the Key Statistics above.
                 A technical walk-through how to create these, is available <a href="%s/stats/customevent_help">here</a>.
                 When a custom event has been made available, it is displayed below.</p>
                 """ % CFG_SITE_URL


        temp_out = ""
        for event in customevents:
            temp_out += """<li><a href="%s/stats/customevent?ids=%s">%s</a></li>""" \
                        % (CFG_SITE_URL, event[0], (event[1] is None) and event[0] or event[1])
        if len(customevents) == 0:
            out += self.tmpl_error("There are currently no custom events available.", ln=ln)
        else:
            out += "<ul>" + temp_out + "</ul>"

        return out

    def tmpl_loans_statistics(self, ln=CFG_SITE_LANG):
        """
        Generates the tables with the bibcirculation statistics
        """
        out = """<h3>Bibcirculation stats</h3>"""
        return out

    def tmpl_error_log_statistics_list(self, ln=CFG_SITE_LANG):
        """
        Link to error log analyzer
        """
        return """<h3>Error log statistics</h3>
                 <p>Displays statistics about the last errors in the Invenio and Apache logs</p>
                 <ul><li><a href="%s/stats/error_log%s">Error log analyzer</a></li>
                 </ul>""" % (CFG_SITE_URL, (CFG_SITE_LANG != ln and '?ln=' + ln) or '')

    def tmpl_error_log_analyzer(self, invenio_ranking, invenio_last_errors, apache_ranking):
        """
        Generates the statistics of the last errors
        """
        out = """<h4>Invenio error log</h4>
                 <h5>Ranking</h5>
                 <pre>%s</pre>
                 <h5>Last errors</h5>
""" % (cgi.escape(invenio_ranking))
        lines = invenio_last_errors.splitlines()
        error_number = len(lines)
        for line in lines:
            out += """<div>
                          %(line)s<button id="bt_toggle%(error_number)s">Toggle</button>
                          <pre id="txt_error%(error_number)s">%(error_details)s</pre>
                      </div>
                      <script>
                          $("#txt_error%(error_number)s").slideToggle("fast");
                          $("#bt_toggle%(error_number)s").click(function () {
                              $("#txt_error%(error_number)s").slideToggle("fast");
                          });
                      </script>

""" % {'line': cgi.escape(line),
       'error_number': error_number,
       'error_details': cgi.escape(get_invenio_error_details(error_number))}
            error_number -= 1
        out += """<h4>Apache error log</h4>
                  <pre>%s</pre>""" % apache_ranking
        return out

    def tmpl_custom_summary(self, ln=CFG_SITE_LANG):
        """
        Link to custom annual report.
        """
        return """<h3>Library report</h3>
                 <ul><li><a href="%s/stats/custom_summary">Custom query summary</a></li></ul>
                 """ % CFG_SITE_URL

    def tmpl_yearly_report_list(self, ln=CFG_SITE_LANG):
        """
        Link to yearly report
        """
        return """<h3>Yearly report</h3>
                <p>Yearly report with the total number of circulation transactions
                (loans, renewals, returns, ILL requests, hold request).</p>
                <ul><li><a href="%s/stats/yearly_report">Yearly report</a></li></ul>
                """ % CFG_SITE_URL

    def tmpl_yearly_report(self, year_report, ln=CFG_SITE_LANG):
        """
        Display yearly report with the total number of circulation transactions.
        """
        temp_out = ""
        for info in year_report:
            if info is None:
                temp_out += '\n'
            elif info[1] is None:
                temp_out += info[0] + '\n'
            else:
                temp_out += info[0] + " " + \
                        '.' * (85 - len(str(info[0])) - \
                        len(str(info[1]))) + " " + str(info[1]) + '\n'
        return "<pre>" + temp_out + "</pre>"

    def tmpl_ingestion_health(self, general, req_ingestion=None, stats=None, ln=CFG_SITE_LANG):
        """
        Display the record status search box and the results of the last
        request, if done.
        """
        # Introduction and search box
        temp_out = """
            <p>Check the ingestion health for records pending or go to
            <a href="%s/stats/system_health%s">current system health</a>.</p>
            """ % \
            (CFG_SITE_URL, (CFG_SITE_LANG != ln and '?ln=' + ln) or '')
        if general == 0:
            temp_out += """
                    <p class="warninggreen">(all records up to date!)</p>
                        """
        else:
            temp_out += """
                    <p class="warningred">(around %s records pending)</p>
                        """ % str(general)

        temp_out += """
                <form method="get"> <input type="hidden" name="ln" value="%s" />
                """ % ln

        if req_ingestion == None:
            temp_out += self._tmpl_text_box("pattern", "", ln=ln)
        else:
            temp_out += self._tmpl_text_box("pattern", req_ingestion, ln=ln)
        temp_out += """
                    <input class="formbutton" type="submit" />
                    </form>
                    """
        if stats==None:
            return temp_out
        else:
            # results of the last request
            info_stats = self.tmpl_ingestion_list(stats, ln=ln)
            return  temp_out + info_stats

    def tmpl_ingestion_list(self, ingestion_statistics, ln=CFG_SITE_LANG):
        """
        Generates the system ingestion health.
        """
        temp_out = ""
        for statistic in ingestion_statistics:
            if statistic is None:
                temp_out += '\n'
            elif statistic[1] is None:
                temp_out += statistic[0] + '\n'
            else:
                # regular expression, just to extract the text
                # inside the link and view it's length
                aux = re.search('.*>(.*)<.*', str(statistic[0]))
                if aux is None:
                    temp_out += statistic[0] + " " + '.' * \
                                (85 - len(str(statistic[0])) - \
                                len(str(statistic[1]))) + " " + \
                                str(statistic[1]) + '\n'
                else:
                    temp_out += statistic[0] + " " + '.' * \
                                (85 - len(str(aux.group(1))) - \
                                len(str(statistic[1]))) + " " + \
                                str(statistic[1]) + '\n'
        temp_out = "<pre>" + temp_out + "</pre>"
        return temp_out

    def tmpl_collection_stats_main_list(self, ln=CFG_SITE_LANG):
        """
        Generates a list of available collections statistics.
        """
        out = """<h3>Collections stats</h3>
                 <ul>"""
        from invenio.modules.collections.models import Collection
        for collection in Collection.query.filter_by(
                name=CFG_SITE_NAME).one().collection_children_r:
            coll = collection.name
            out += """<li><a href="%s/stats/collections?%s">%s</a></li>""" \
                        % (CFG_SITE_URL, urllib.urlencode({'collection': coll}) +
                           ((CFG_SITE_LANG != ln and '&ln=' + ln) or ''), coll)
        out += """<li><a href="%s/stats/collection_stats%s">Other collections</a></li>""" \
                % (CFG_SITE_URL, (CFG_SITE_LANG != ln and '?ln=' + ln) or '')
        return out + "</ul>"

    def tmpl_collection_stats_complete_list(self, collections, ln=CFG_SITE_LANG):
        if len(collections) == 0:
            return self.tmpl_error("There are currently no collections available.", ln=ln)
        temp_out = """<h4>Collections stats</h4>
                 <ul>"""
        for coll in collections:
            temp_out += """<li><a href="%s/stats/collections?%s">%s</a></li>""" \
                        % (CFG_SITE_URL, urllib.urlencode({'collection': coll[0]}), coll[1])
        return temp_out + "</ul>"

    def tmpl_customevent_help(self, ln=CFG_SITE_LANG):
        """
        Display help for custom events.
        """
        return """<h3>General overview</h3>

                  <p>A custom event is a measure indicating the frequency of some kind of
                  "action", such as e.g. the number of advanced searches carried out using
                  the Swedish language interface. The custom event functionality is intended
                  to give administrators a mean to log abstract activity, as opposed to
                  trivial measurements like "collection population" and "search frequency".
                  Thus, a custom event is fully customizable and defined by an administrator
                  but it is important to understand that the Webstat module merely supplies
                  the mean to register an action and associate it with a predefined custom event,
                  while the actual use case leading up to the very registration of the action
                  is left to the user.</p>

                  <p>After a custom event has been created and the process of collecting data
                  has started, the event is accessible for review through the Webstat webpage.</p>

                  <h3>How to create a new custom event</h3>

                  <ol>
                    <li>Edit <strong>/opt/invenio/etc/webstat/webstat.cfg</strong> adding
                    the definition of the customevent:
                    <pre>
                    [webstat_custom_event_1]
                    name = baskets
                    param1 = action
                    param2 = basket
                    param3 = user</pre>
                    </li>
                    <li>The title must be <em>webstat_custom_event_(num)</em> where <em>(num)</em>
                    is a number. The number can not be repeated in two different customevents.
                    </li>
                    <li>The option <em>name</em> is the name of the customevent.</li>
                    <li>Each param in the customevent must be given as <em>param(num)</em> where
                    <em>(num)</em> is an unique number.</li>
                  </ol>"""

    def tmpl_error(self, msg, ln=CFG_SITE_LANG):
        """
        Provides a common way of outputting error messages.
        """
        return """<div class="important">%s</div>""" % msg

    def tmpl_keyevent_box(self, options, order, choosed, ln=CFG_SITE_LANG, list=False):
        """
        Generates a FORM box with dropdowns for keyevents.

        @param options: { parameter name: [(argument internal, argument full)]}
        @type options: { str: [(str, str)]}

        @param order: A permutation of the keys in options, for design purpose.
        @type order: [str]

        @param options: The selected parameters, and its values.
        @type options: { str: str }
        """
        # Create the FORM's header
        formheader = """<form method="get">
        <input type="hidden" name="ln" value="%s" />""" % ln

        # Create the headers using the options permutation
        headers = [[options[param][1] for param in order]]
        headers[0].append("")

        # Create all SELECT boxes
        sels = [[]]
        for param in order:
            if choosed[param] == 'select date':
                sels[0].append(self._tmpl_select_box(options[param][2], # SELECT box data
                    " - select " + options[param][1], # first item info
                    param, # name
                    [choosed['s_date'], choosed['f_date']], # selected value (perhaps several)
                    True, # multiple box?
                    ln=ln))
            elif options[param][0] == 'combobox':
                sels[0].append(self._tmpl_select_box(options[param][2], # SELECT box data
                    " - select " + options[param][1], # first item info
                    param, # name
                    choosed[param], # selected value (perhaps several)
                    type(choosed[param]) is list, # multiple box?
                    ln=ln))
            elif options[param][0] == 'textbox':
                sels[0].append(self._tmpl_text_box(param, # name
                    choosed[param], # selected value
                    ln=ln))

        # Create button
        sels[0].append("""<input class="formbutton" type="submit"
        name="action_gen" value="Generate"/>""")

        # Export option
        if list:
            sels[0].append("""<input class="formbutton" type="submit"
            name="format" value="Full list"/>""")
        # Create form footer
        formfooter = """</form>"""

        return self._tmpl_box(formheader, formfooter, ["keyevent_table"],
                              headers, sels, [""], ln=ln)

    def tmpl_customevent_box(self, options, choosed, ln=CFG_SITE_LANG):
        """
        Generates a FORM box with dropdowns for customevents.

        @param options: { parameter name: (header,  [(argument internal, argument full)]) or
                                          {param father: [(argument internal, argument full)]}}
                        The dictionary is for options that are dependient of other.
                        It's use for 'cols'
                        With "param father"="__header" the headers
                        With "param father"="__none" indicate the arguments by default
        @type options: { str: (str, [(str, str)])|{str: [(str, str)]}}

        @param choosed: The selected parameters, and its values.
        @type choosed: { str: str }
        """
        if choosed['ids'] == []:
            choosed['ids'] = [""]
            choosed['cols'] = [[("", "", "")]]
        num_ids = len(choosed['ids'])

        operators = [('and', 'AND'), ('or', 'OR'), ('and_not', 'AND NOT')]

        # Crate the ids of the tables
        table_id = ["time_format"]
        table_id.extend(['cols' + str(i) for i in range(num_ids)])

        # Create the headers using the options permutation
        headers = [(options['timespan'][0], options['format'][0])]
        headers.extend([(options['ids'][0], "", options['cols']['__header'], "value")
                        for event_id in choosed['ids']])

        # Create all SELECT boxes
        sels = [[]]
        for param in ['timespan', 'format']:
            if choosed[param] == 'select date':
                sels[0].append(self._tmpl_select_box(options[param][1], # SELECT box data
                    " - select " + options[param][0], # first item info
                    param, # name
                    [choosed['s_date'], choosed['f_date']], # selected value (perhaps several)
                    True, # multiple box?
                    ln=ln))
            else:
                sels[0].append(self._tmpl_select_box(options[param][1], # SELECT box data
                    " - select " + options[param][0], # first item info
                    param, # name
                    choosed[param], # selected value (perhaps several)
                    type(choosed[param]) is list, # multiple box?
                    ln=ln))
        for event_id, i in zip(choosed['ids'], range(num_ids)):
            select_table = []
            select_row = [self._tmpl_select_box(options['ids'][1],
                " - select " + options['ids'][0],
                'ids',
                event_id,
                attribute='onChange="javascript: \
                    changed_customevent(customevent[\'ids\'],%d);"' % i,
                ln=ln)]
            is_first_loop = True
            row = 0
            if len(choosed['cols']) <= i:
                choosed['cols'].append([("", "", "")])
            if choosed['cols'][i] == []:
                choosed['cols'][i] = [("", "", "")]
            for _, col, value in choosed['cols'][i]:
                select_row.append("")
                if not is_first_loop:
                    select_row.append(self._tmpl_select_box(operators, "", "bool%d" % i, bool))
                if event_id:
                    select_row.append(self._tmpl_select_box(options['cols'][event_id],
                                                    " - select " + options['cols']['__header'],
                                                    'cols' + str(i),
                                                    col,
                                                    ln=ln))
                else:
                    select_row.append(self._tmpl_select_box(options['cols']['__none'],
                                                    "Choose CustomEvent",
                                                    'cols' + str(i),
                                                    "",
                                                    ln=ln))
                if is_first_loop:
                    select_row.append("<input name=\"col_value%d\" value=\"%s\">" % (i, value))
                else:
                    select_row.append("""<input name="col_value%d" value="%s">
                            <a href="javascript:;" onclick="delrow(%d,%d);">Remove row</a>""" \
                            % (i, value, i, row))
                select_table.append(select_row)
                select_row = []
                if is_first_loop:
                    is_first_loop = False
                row += 1
            sels.append(select_table)

        # javascript for add col selectors
        sels_col = []
        sels_col.append(self._tmpl_select_box(options['ids'][1], " - select "
            + options['ids'][0], 'ids', "",
            False,
            attribute='onChange="javascript: \
                changed_customevent(customevent[\\\'ids\\\'],\' + col + \');"',
            ln=ln))
        sels_col.append("")
        sels_col.append(self._tmpl_select_box(options['cols']['__none'], "Choose CustomEvent",
                                            'cols\' + col + \'', "", False, ln=ln))
        sels_col.append("""<input name="col_value' + col + '">""")
        col_table = self._tmpl_box("", "", ["cols' + col + '"], headers[1:], [sels_col],
                    ["""<a id="add' + col + '" href="javascript:;"
                    onclick="addcol(\\'cols' + col + '\\', ' + col + ');">Add more arguments</a>
                    <a id="del' + col + '" href="javascript:;" onclick="delblock(' + col + ');">
                    Remove block</a>"""], ln=ln)
        col_table = col_table.replace('\n', '')
        formheader = """<script type="text/javascript">
                var col = %d;
                var col_select = new Array(%s,0);
                var block_pos_max = %d;
                var block_pos = new Array(%s,0);
                var rows_pos_max = [%s];
                var rows_pos = [%s];

                function addcol(id, num){
                    col_select[num]++;
                    var table = document.getElementById(id);
                    var body = table.getElementsByTagName('tbody')[0];
                    var row = document.createElement('tr');
                    var cel0 = document.createElement('td');
                    row.appendChild(cel0);
                    var cel1 = document.createElement('td');
                    cel1.innerHTML = '<select name="bool' + num + '"> <option value="and">AND</option> <option value="or">OR</option> <option value="and_not">AND NOT</option> </select>';
                    row.appendChild(cel1);
                    var cel2 = document.createElement('td');
                    cel2.innerHTML = '%s';
                    row.appendChild(cel2);
                    var cel3 = document.createElement('td');
                    cel3.innerHTML = '%s';
                    row.appendChild(cel3);
                    body.appendChild(row);

                    // Change arguments
                    arguments = document['customevent']['cols' + num]
                    if (col_select[1] == 0) {
                        value = document['customevent']['ids'].value;
                    } else {
                        value = document['customevent']['ids'][block_pos[num]].value;
                    }
                    _change_select_options(arguments[arguments.length -1], get_argument_list(value), '');
                    rows_pos[num][col_select[num]-1] = rows_pos_max[num];
                    rows_pos_max[num]++;
                } """ % (num_ids,
                        ','.join([str(len(choosed['cols'][i])) for i in range(num_ids)]),
                        num_ids,
                        ','.join([str(i) for i in range(num_ids)]),
                        ','.join([str(len(block)) for block in choosed['cols']]),
                        ','.join([str(range(len(block))) for block in choosed['cols']]),
                        sels_col[2].replace("' + col + '", "' + num + '"),
                        sels_col[3].replace("' + col + '", "' + num + '") + \
                                """ <a href="javascript:;" onclick="delrow(' + num + ',' + (col_select[num]-1) + ');">Remove row</a>""")
        formheader += """
                function addblock() {
                    col_select[col] = 1;
                    var ni = document.getElementById('block');
                    var newdiv = document.createElement('div'+col);
                    newdiv.innerHTML = '%s';
                    ni.appendChild(newdiv);
                    block_pos[col] = block_pos_max;
                    block_pos_max++;
                    rows_pos[col] = [0];
                    rows_pos_max[col] = 1;
                    col++;
                }""" % col_table
        formheader += """
                function delblock(id) {
                    var block = document.getElementById("cols" + id);
                    var add = document.getElementById("add" + id);
                    var del = document.getElementById("del" + id);
                    block.parentNode.removeChild(block);
                    add.parentNode.removeChild(add);
                    del.parentNode.removeChild(del);
                    for (var i = id+1; i < col_select.length; i++) {
                        block_pos[i]--;
                    }
                    block_pos_max--;
                }

                function delrow(table_id,row_num) {
                    var table = document.getElementById('cols' + table_id);
                    table.tBodies[0].deleteRow(rows_pos[table_id][row_num]);
                    col_select[table_id]--;
                    for (var i = row_num+1; i < rows_pos[table_id].length; i++) {
                        rows_pos[table_id][i]--;
                    }
                    rows_pos_max[table_id]--;
                } """
        formheader += """
                function change_select_options(selectList, isList, optionArray, chooseDefault) {
                    if (isList) {
                        for (var select = 0; select < selectList.length; select++) {
                            _change_select_options(selectList[select], optionArray, chooseDefault);
                        }
                    } else {
                        _change_select_options(selectList, optionArray, chooseDefault);
                    }
                }

                function _change_select_options(select, optionArray, chooseDefault) {
                    select.options.length = 0;
                    for (var option = 0; option*2 < optionArray.length - 1; option++) {
                        if (chooseDefault == optionArray[option*2+1]) {
                            select.options[option] = new Option(optionArray[option*2], optionArray[option*2+1], true, true);
                        } else {
                            select.options[option] = new Option(optionArray[option*2], optionArray[option*2+1]);
                        }
                    }
                }

                function changed_customevent(select, num){
                    if (select.length) {
                        value = select[block_pos[num]].value;
                    } else {
                        value = select.value;
                    }
                    list = get_argument_list(value);
                    select_list = (col_select[num] > 1);
                    change_select_options(document['customevent']['cols' + num], select_list, list, '');
                }

                function get_argument_list(value) {
                    if (value == "") {
                        return ['Choose CustomEvent',''];"""
        for event_id, cols in options['cols'].items():
            if event_id not in ['__header', '__none']:
                str_cols = "[' - select %s', ''," % options['cols']['__header']
                for internal, full in cols:
                    str_cols += "'%s','%s'," % (full, internal)
                str_cols = str_cols[:-1] + ']'
                formheader += """
                    } else if (value == "%s") {
                        return %s;""" % (event_id, str_cols)
        formheader += """
                    }
                }
            </script>"""

        # Create the FORM's header
        formheader += """<form method="get" name="customevent">
        <input type="hidden" name="ln"value="%s" />""" % ln

        # Create all footers
        footers = []
        footers.append("")
        footers.append("""<a href="javascript:;" onclick="addcol('cols0', 0);">
                            Add more arguments</a>""")
        for i in range(1, num_ids):
            footers.append("""
                    <a id="add%(i)d" href="javascript:;" onclick="addcol('cols%(i)d', %(i)d);">Add more arguments</a>
                    <a id="del%(i)d" href="javascript:;" onclick="delblock(%(i)d);">Remove block</a>
                    """ % {'i': i})
        footers[-1] += """<div  id="block"> </div>"""

        # Create formfooter
        formfooter = """<p><a href="javascript:;" onclick="addblock();">Add more events</a>
                    <input class="formbutton" type="submit" name="action_gen" value="Generate"></p>
                    </form>"""

        return self._tmpl_box(formheader, formfooter, table_id, headers, sels, footers, ln=ln)

    def tmpl_display_event_trend_ascii(self, title, filename, ln=CFG_SITE_LANG):
        """Displays a ASCII graph representing a trend"""
        try:
            return self.tmpl_display_trend(title, "<div><pre>%s</pre></div>" %
                                           open(filename, 'r').read(), ln=ln)
        except IOError:
            return "No data found"

    def tmpl_display_event_trend_image(self, title, filename, ln=CFG_SITE_LANG):
        """Displays an image graph representing a trend"""
        if os.path.isfile(filename):
            return self.tmpl_display_trend(title, """<div><img src="%s" /></div>""" %
                                    filename.replace(CFG_WEBDIR, CFG_SITE_URL), ln=ln)
        else:
            return "No data found"

    def tmpl_display_event_trend_text(self, title, filename, ln=CFG_SITE_LANG):
        """Displays a text representing a trend"""
        try:
            return self.tmpl_display_trend(title, "<div>%s</div>" %
                                           open(filename, 'r').read(), ln=ln)
        except IOError:
            return "No data found"

    def tmpl_display_numeric_stats(self, titles, avgs, maxs, mins):
        """Display average, max and min values"""
        if titles:
            out = ""
            for i in range(len(titles)):
                out += """<em>%s</em><br />
                          <b>Average:</b> %d<br />
                          <b>Max:</b> %d<br />
                          <b>Min:</b> %d<br />""" % (cgi.escape(titles[i]),
                                                    avgs[i], maxs[i], mins[i])
            return out
        else:
            return """<b>Average:</b> %d<br />
                      <b>Max:</b> %d<br />
                      <b>Min:</b> %d<br />""" % (avgs, maxs, mins)

    def tmpl_display_custom_summary(self, tag_name, data, title, query, tag,
                                    path, ln=CFG_SITE_LANG):
        """Display the custom summary (annual report)"""
        # Create the FORM's header
        formheader = """<form method="get">
        <input type="hidden" name="ln"value="%s" />""" % ln

        # Create the headers
        headers = [("Chart title", "Query", "Output tag", "")]

        # Create the body (text boxes and button)
        fields = (("""<input type="text" name="title" value="%s" size="20"/>""" % cgi.escape(title),
                   """<input type="text" name="query" value="%s" size="35"/>""" % cgi.escape(query),
                   """<input type="text" name="tag" value="%s" size="10"/>""" % cgi.escape(tag),
                   """<input class="formbutton" type="submit" name="action_gen" value="Generate"/>"""), )

        # Create form footer
        formfooter = """</form>"""


        out = self._tmpl_box(formheader, formfooter, [("custom_summary_table", )],
                             headers, fields, [""], ln=ln)

        out += """<div>
<table border>

<tr>

<td colspan=2>
<b><center>
Distribution across %s
</center>
</td>
</tr>

<tr>
<td align="right"><b>Nb.</b></td>
<td><b>%s</b></td>
</tr>

""" % (cgi.escape(tag_name), cgi.escape(tag_name[0].capitalize() + tag_name[1:]))
        if len(query) > 0:
            query += " and "
        for title, number in data:
            if title in ('Others', 'TOTAL'):
                out += """<tr>
<td align="right">%d</td>
<td>%s</td>
</tr>
""" % (number, cgi.escape(title))
            else:
                out += """<tr>
<td align="right"><a href="%s/search?p=%s&ln=%s">%d</a></td>
<td>%s</td>
</tr>
""" % (CFG_SITE_URL, cgi.escape(urllib.quote(query + " " + tag + ':"' + title + '"')), ln, number,
       cgi.escape(title))
        out += """</table></div>"""
        if path:
            out += """<div><img src="%s" /></div>""" % cgi.escape(path.replace(CFG_WEBDIR,
                                                                               CFG_SITE_URL))
        return out

    # INTERNALS
    def tmpl_display_trend(self, title, html, ln=CFG_SITE_LANG):
        """
        Generates a generic display box for showing graphs (ASCII and IMGs)
        alongside to some metainformational boxes.
        """
        return """<table class="narrowsearchbox">
                   <thead><tr><th colspan="2" class="narrowsearchboxheader" align="left">%s</th></tr></thead>
                   <tbody><tr><td class="narrowsearchboxbody" valign="top">%s</td></tr></tbody>
                  </table> """ % (title, html)

    def _tmpl_box(self, formheader, formfooter, table_id, headers, selectboxes,
                  footers, ln=CFG_SITE_LANG):
        """
        Aggregates together the parameters in order to generate the
        corresponding box for customevent.

        @param formheader: Start tag for the FORM element.
        @type formheader: str

        @param formfooter: End tag for the FORM element.
        @type formfooter: str

        @param table_id: id for each table
        @type table_id: list<str>

        @param headers: Headers for the SELECT boxes
        @type headers: list<list<str>>

        @param selectboxes: The actual HTML drop-down boxes, with appropriate content.
        @type selectboxes: list<list<str>>|list<list<list<str>>>

        @param footers: footer for each table
        @type footers: list<str>

        @return: HTML describing a particular FORM box.
        @type: str
        """
        out = formheader
        for table in range(len(table_id)):
            out += """<table id="%s" class="searchbox">
                    <thead>
                        <tr>""" % table_id[table]

            #Append the headers
            for header in headers[table]:
                out += """<th class="searchboxheader">%s</th>""" % header

            out += """</tr>
                </thead>
                <tbody>"""

            # Append the SELECT boxes
            is_first_loop = True
            out += """<tr valign="bottom">"""
            for selectbox in selectboxes[table]:
                if type(selectbox) is list:
                    if is_first_loop:
                        is_first_loop = False
                    else:
                        out += """</tr>
                                <tr valign="bottom">"""
                    for select in selectbox:
                        out += """<td class="searchboxbody" valign="top">%s</td>""" % select
                else:
                    out += """<td class="searchboxbody" valign="top">%s</td>""" % selectbox
            out += """
                </tr>"""
            out += """
                </tbody>
            </table>"""

            # Append footer
            out += footers[table]

        out += formfooter

        return out

    def _tmpl_select_box(self, iterable, explaination, name, preselected,
                         multiple=False, attribute="", ln=CFG_SITE_LANG):
        """
        Generates a HTML SELECT drop-down menu.

        @param iterable: A list of values and tag content to be used in the SELECT list
        @type iterable: [(str, str)]

        @param explaination: An explainatory string put as the tag content for the first OPTION.
        @type explaination: str

        @param name: The name of the SELECT tag. Important for FORM-parsing.
        @type name: str

        @param preselected: The value, or list of values, of the OPTION that should be
                            preselected. Blank or empty list for none.
        @type preselected: str | []

        @param attribute: Optionally add attributes to the select tag
        @type attribute: str

        @param multiple: Optionally sets the SELECT box to accept multiple entries.
        @type multiple: bool
        """


        if attribute:
            sel = """<select name="%s" %s>""" % (name, attribute)
        else:
            if name == "timespan":
                sel = """<script type="text/javascript">
                    function changeTimeSpanDates(val){
                        if(val == "select date"){
                            document.getElementById("selectDateTxt").style.display='block';}
                        else{
                            document.getElementById("selectDateTxt").style.display='none';}
                    }

                </script>
                <select name="timespan" id="timespan"
                    onchange="javascript: changeTimeSpanDates(this.value);">"""
            else:
                sel = """<select name="%s">""" % name

        if multiple is True and name != "timespan":
            sel = sel.replace("<select ", """<select multiple="multiple" size="5" """)
        elif explaination:
            sel += """<option value="">%s</option>""" % explaination

        for realname, printname in [(x[0], x[1]) for x in iterable]:
            if printname is None:
                printname = realname
            option = """<option value="%s">%s</option>""" % (realname, printname)
            if realname == preselected or (type(preselected) is list
                    and realname in preselected) or (name == "timespan" and
                                realname == 'select date' and multiple):
                option = option.replace('">', '" selected="selected">')
            sel += option
        sel += "</select>"
        if name == "timespan":
            if multiple:
                s_date = preselected[0]
                f_date = preselected[1]
            else:
                s_date = datetime.datetime.today().date().strftime("%m/%d/%Y %H:%M")
                f_date = datetime.datetime.now().strftime("%m/%d/%Y %H:%M")
            sel += """<link rel="stylesheet" href="%(CFG_SITE_URL)s/vendors/jquery-ui/themes/redmond/jquery-ui.min.css"
                        type="text/css" />
                      <link rel="stylesheet" href="%(CFG_SITE_URL)s/vendors/jqueryui-timepicker-addon/dist/jquery-ui-timepicker.min.css"
                        type="text/css" />
                      <script language="javascript" type="text/javascript" src="%(CFG_SITE_URL)s/vendors/jquery-ui/jquery-ui.min.js"></script>
                      <script type="text/javascript" src="%(CFG_SITE_URL)s/vendors/jqueryui-timepicker-addon/dist/jquery-ui-timepicker-addon.min.js"></script>

                      <div id="selectDateTxt" style="position:relative;display:none">
                      <table align="center">
                          <tr align="center">
                              <td align="right" class="searchboxheader">From: </td>
                              <td align="left"><input type="text" name="s_date" id="s_date" value="%(s_date)s" size="14" /></td>
                          </tr>
                          <tr align="center">
                              <td align="right" class="searchboxheader">To: </td>
                              <td align="left"><input type="text" name="f_date" id="f_date" value="%(f_date)s" size="14" /></td>
                          </tr>
                      </table>
                      </div>
                      <script type="text/javascript">
                        $('#s_date').datetimepicker();
                        $('#f_date').datetimepicker({
                          hour: 23,
                          minute: 59
                        });
                        if(document.getElementById("timespan").value == "select date"){
                            document.getElementById("selectDateTxt").style.display='block';
                        } </script>""" % {'CFG_SITE_URL': CFG_SITE_URL,
                                          's_date': cgi.escape(s_date),
                                          'f_date': cgi.escape(f_date)}
        return sel

    def _tmpl_text_box(self, name, preselected, ln=CFG_SITE_LANG):
        """
        Generates a HTML text-box menu.

        @param name: The name of the textbox label.
        @type name: str

        @param preselected: The value that should be preselected. Blank or empty
        list for none.
        @type preselected: str | []
        """
        if name == 'min_loans' or name == 'max_loans':
            return """<script type="text/javascript">
 function checkNumber(input){
   var num = input.value.replace(/\,/g,'');
   var newtext = parseInt(num);
   if(isNaN(newtext)){
         alert('You may enter only numbers in this field!');
         input.value = 0;
   }
   else {
         input.value = newtext;
   }
 }
</script>


<input type="text" name="%s" onchange="checkNumber(this)" value="%s" />""" % (name, preselected)
        else:
            return """<input type="text" name="%s" value="%s" />""" % (name, preselected)
