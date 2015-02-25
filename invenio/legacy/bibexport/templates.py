# -*- coding: utf-8 -*-
# $Id: webmessage_templates.py,v 1.32 2008/03/26 23:26:23 tibor Exp $
#
# handles rendering of webmessage module
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011 CERN.
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

""" Templates for field exporter plugin """

__revision__ = "$Id: webmessage_templates.py,v 1.32 2008/03/26 23:26:23 tibor Exp $"

import cgi

from invenio.config import CFG_SITE_LANG, CFG_SITE_URL
from invenio.base.i18n import gettext_set_language
from invenio.utils.date import convert_datestruct_to_datetext, convert_datetext_to_dategui, convert_datestruct_to_dategui
from invenio.legacy.bibexport.fieldexporter_dblayer import Job, JobResult

class Template:
    """Templates for field exporter plugin"""

    _JOBS_URL = "%s/exporter/jobs" % (CFG_SITE_URL, )
    _EDIT_JOB_URL = "%s/exporter/edit_job" % (CFG_SITE_URL, )
    _EDIT_QUERY_URL = "%s/exporter/edit_query" % (CFG_SITE_URL, )
    _JOB_RESULTS_URL = "%s/exporter/job_results" % (CFG_SITE_URL, )
    _DISPLAY_JOB_RESULT_URL = "%s/exporter/display_job_result" % (CFG_SITE_URL, )
    _DOWNLOAD_JOB_RESULT_URL = "%s/exporter/download_job_result" % (CFG_SITE_URL, )
    _JOB_HISTORY_URL = "%s/exporter/history" % (CFG_SITE_URL, )

    def tmpl_styles(self):
        """Defines the local CSS styles used in the plugin"""

        styles = """
<style type="text/css">

.label{
    white-space: nowrap;
    padding-right: 15px;
}

.textentry{
    width: 350px;
}

table.spacedcells td{
    padding-right: 20px;
    white-space: nowrap;
}
table.spacedcells th{
    padding-right: 20px;
    text-align: left;
}

</style>

<script type="text/javascript">
<!--
function SetAllCheckBoxes(FormName, FieldName, CheckValue)
{
    if(!document.forms[FormName])
        return;
    var objCheckBoxes = document.forms[FormName].elements[FieldName];
    if(!objCheckBoxes)
        return;
    var countCheckBoxes = objCheckBoxes.length;
    if(!countCheckBoxes)
        objCheckBoxes.checked = CheckValue;
    else
        // set the check value for all check boxes
        for(var i = 0; i < countCheckBoxes; i++)
            objCheckBoxes[i].checked = CheckValue;
}
// -->
</script>
        """
        return styles

    def tmpl_navigation_menu(self, language = CFG_SITE_LANG):
        """Returns HTML representing navigation menu for field exporter."""

        _ = gettext_set_language(language)

        navigation_menu = """
           <table class="headermodulebox">
             <tbody><tr>
               <td class="headermoduleboxbody">
                     <a class="header" href="%(job_verview_url)s?ln=%(language)s">%(label_job_overview)s</a>
               </td>
               <td class="headermoduleboxbody">
                     <a class="header" href="%(edit_job_url)s?ln=%(language)s">%(label_new_job)s</a>
               </td>

               <td class="headermoduleboxbody">
                     <a class="header" href="%(job_history_url)s?ln=%(language)s">%(label_job_history)s</a>
               </td>
           </tr></tbody></table>
        """ %   {"edit_job_url" : self._EDIT_JOB_URL,
                "job_verview_url" : self._JOBS_URL,
                "job_history_url" : self._JOB_HISTORY_URL,
                "language" : language,
                "label_job_overview" : _("Export Job Overview"),
                "label_new_job" : _("New Export Job"),
                "label_job_history" : _("Export Job History")
                }
        return navigation_menu

    def tmpl_display_jobs(self, jobs, language = CFG_SITE_LANG):
        """
        Creates page for displaying of all the jobs.

        @param jobs: list of the jobs that have to be displayed
        @param language: language of the page
        """

        _ = gettext_set_language(language)

        table_rows = ""
        for current_job in jobs:
            # convert last run date into text proper to be shown to the user
            datetext = convert_datestruct_to_datetext(current_job.get_last_run())
            last_run = convert_datetext_to_dategui(datetext, language)
            # obtain text corresponding to the frequency of execution
            frequency = current_job.get_frequency()
            frequency_text = self._get_frequency_text(frequency)

            row = """<tr>
            <td><input type="checkbox" name="selected_jobs" value="%(job_id)s"></input></td>
            <td><a href="%(edit_job_url)s?id=%(job_id)s&ln=%(language)s">%(name)s</a></td>
            <td>%(frequency)s</td>
            <td>%(last_run)s</td>
            </tr>""" %  self._html_escape_dictionary({
                        "edit_job_url" : self._EDIT_JOB_URL,
                        "job_id" : current_job.get_id(),
                        "name" : current_job.get_name(),
                        "frequency" : frequency_text,
                        "language" : language,
                        "last_run" : last_run
                        })
            table_rows += row

        select_all_none_row = """
            <tr><td colspan="4">
                <small>%s</small><br><br>
            </td></tr>""" \
            %(self._get_select_all_none_html("jobsForm",
                                               "selected_jobs",
                                               language))
        table_rows += select_all_none_row

        buttons_row = """<tr>
            <td colspan="3">
                <input type="Submit" name="run_button" value="%(label_run)s" class="formbutton">
                <input type="Submit" name="delete_button" value="%(label_delete)s" class="formbutton">
            </td>
            <td align="right">
                <input type="Submit" name="new_button" value="%(label_new)s" class="formbutton">
            </td>
        </tr>""" % {
                        "label_run" : _("Run"),
                        "label_delete" : _("Delete"),
                        "label_new" : _("New")
                        }
        table_rows += buttons_row

        body = """
<form method="post" name="jobsForm">

<table class="spacedcells">
    <th></th>
    <th>%(label_name)s</th>
    <th>%(label_frequency)s</th>
    <th>%(label_last_run)s</th>
    %(table_rows)s
</table>

</form>
        """ % {
            "table_rows" : table_rows,
            "label_name" : _("Name"),
            "label_frequency" : _("Run"),
            "label_last_run" : _("Last run")
            }

        return body

    def tmpl_edit_job(self, job, language = CFG_SITE_LANG):
        """
        Creates page for editing of jobs.

        @param job: The job that will be edited
        @param language: language of the page
        """

        _ = gettext_set_language(language)

        job_frequency = job.get_frequency()
        frequency_select_box_html = self._create_frequency_select_box("job_frequency", job_frequency, language)
        output_format_select_box_html = self._create_output_format_select_box(selected_value = job.get_output_format())

        body = """
<form method="post">
<input type="Hidden" name="id" value="%(job_id)s">
<table>
    <tr>
        <td class = "label">%(name_label)s</td>
        <td colspan="2"><input type="text" name="job_name" class="textentry" value="%(job_name)s"></td>
    </tr>
    <tr>
        <td class = "label">%(frequency_label)s</td>
        <td colspan="2">%(frequency_select_box)s</td>
    </tr>
    <tr>
        <td class = "label">%(output_format_label)s</td>
        <td colspan="2">%(output_format_select_box)s</td>
    </tr>
    <tr>
        <td class = "label">%(start_label)s</td>
        <td colspan="2"><input type="text" name="last_run" class="textentry" value="%(job_last_run)s"></td>
    </tr>
    <tr>
        <td class = "label">%(output_directory_label)s</td>
        <td colspan="2"><input type="text" name="output_directory" class="textentry" value="%(output_directory)s"></td>
    </tr>
    <tr>
        <td></td>
        <td>
            <input type="Submit" name="save_button" value="%(save_label)s" class="formbutton">
            <input type="Submit" name="cancel_button" value="%(cancel_label)s" class="formbutton">

        </td>
        <td align="right">
            <input type="Submit" name="edit_queries_button" value="%(edit_queries_label)s" class="formbutton">
        </td>
    </tr>

</table>

</form>
        """ % {
            "name_label" : _("Name"),
            "frequency_label" : _("Frequency"),
            "output_format_label" : _("Output Format"),
            "start_label" : _("Start"),
            "output_directory_label" : _("Output Directory"),
            "save_label" : _("Save"),
            "cancel_label" : _("Cancel"),
            "edit_queries_label" : _("Edit Queries"),
            "job_id" : self._html_escape_content(job.get_id()),
            "job_name" : self._html_escape_content(job.get_name()),
            "frequency_select_box" : frequency_select_box_html,
            "output_format_select_box" : output_format_select_box_html,
            "job_last_run" : convert_datestruct_to_datetext(job.get_last_run()),
            "output_directory" : self._html_escape_content(job.get_output_directory())
            }

        return body

    def tmpl_display_job_queries(self, job_queries, job_id, language = CFG_SITE_LANG):
        """
        Creates page for displaying of queries of a given jobs.

        @param job_queries: list of JobQuery objects that have to be displayed
        @param job_id: identifier of the job that own the queries
        @param language: language of the page
        """
        _ = gettext_set_language(language)

        table_rows = ""
        for current_query in job_queries:
            output_fields = ", ".join(current_query.get_output_fields())

            row = """<tr>
            <td><input type="checkbox" name="selected_queries" value="%(query_id)s"></input></td>
            <td><a href="%(edit_query_url)s?id=%(query_id)s&job_id=%(job_id)s&ln=%(language)s">%(name)s</a></td>
            <td><input type="text" value="%(search_criteria)s" readonly style="border: none; width: 130px"></td>
            <td><input type="text" value="%(output_fields)s" readonly style="border: none; width: 130px"></td>
            <td><input type="text" value="%(comment)s" readonly style="border: none; width: 130px"></td>
            </tr>""" % self._html_escape_dictionary({
                        "edit_query_url" : self._EDIT_QUERY_URL,
                        "language" : language,
                        "query_id" : current_query.get_id(),
                        "search_criteria" : current_query.get_search_criteria(),
                        "name" : current_query.get_name(),
                        "comment" : current_query.get_comment(),
                        "output_fields" : output_fields,
                        "job_id" : job_id
                        })
            table_rows += row

        select_all_none_row = """
            <tr><td colspan="4">
                <small>%s</small><br><br>
            </td></tr>""" \
            % (self._get_select_all_none_html("queriesForm",
                                              "selected_queries",
                                              language))
        table_rows += select_all_none_row

        buttons_row = """<tr>
            <td colspan="4">
                <input type="Submit" name="run_button" value="%(label_run)s" class="formbutton">
                <input type="Submit" name="delete_button" value="%(label_delete)s" class="formbutton">
            </td>
            <td align="right">
                <input type="Submit" name="new_button" value="%(label_new)s" class="formbutton">
            </td>
        </tr>""" % {
                        "label_run" : _("Run"),
                        "label_delete" : _("Delete"),
                        "label_new" : _("New")
                        }
        table_rows += buttons_row

        body = """
<form method="post" name="queriesForm">
<input type="Hidden" name="job_id" value="%(job_id)s">

<table class="spacedcells">
    <th></th>
    <th>%(label_name)s</th>
    <th>%(label_search_criteria)s</th>
    <th>%(label_output_fields)s</th>
    <th>%(label_comment)s</th>
    %(table_rows)s
</table>

</form>
        """ % {
            "table_rows" : table_rows,
            "label_name" : _("Name"),
            "label_search_criteria" : _("Query"),
            "label_comment" : _("Comment"),
            "label_output_fields" : _("Output Fields"),
            "job_id" : self._html_escape_content(job_id)
            }

        return body

    def tmpl_edit_query(self, query, job_id, language = CFG_SITE_LANG):
        """
        Creates page for editing of a query.

        @param query: the query that will be edited
        @param language: language of the page

        @return: The HTML content of the page
        """
        _ = gettext_set_language(language)

        body = """
<form method="post">
<input type="Hidden" name="id" value="%(id)s">
<input type="Hidden" name="job_id" value="%(job_id)s">
<table >
    <tr>
        <td class = "label">%(name_label)s</td>
        <td><input type="text" name="name" class="textentry" value="%(name)s"></td>
    </tr>
    <tr>
        <td class = "label">%(query_label)s</td>
        <td><input type="text" name="search_criteria" class="textentry" value="%(search_criteria)s"></td>
    </tr>
    <tr>
        <td class = "label">%(output_fields_label)s</td>
        <td><input type="text" name="output_fields" class="textentry" value="%(output_fields)s"></td>
    </tr>
    <tr>
        <td class = "label">%(comment_label)s</td>
        <td><textarea name="comment" rows="6" class="textentry">%(comment)s</textarea></td>
    </tr>
    <tr>
        <td></td>
        <td>
            <input type="Submit" name="save_button" value="%(save_label)s" class="formbutton">
            <input type="Submit" name="cancel_button" value="%(cancel_label)s" class="formbutton">
        </td>
    </tr>

</table>

</form>
        """ % self._html_escape_dictionary({
            "name_label" : _("Name"),
            "query_label" : _("Query"),
            "output_fields_label" : _("Output fields"),
            "comment_label" : _("Comment"),
            "save_label" : _("Save"),
            "cancel_label" : _("Cancel"),
            "job_id" : job_id,
            "id" : query.get_id(),
            "name" : query.get_name(),
            "search_criteria" : query.get_search_criteria(),
            "output_fields" : ", ".join(query.get_output_fields()),
            "comment" : query.get_comment(),
            })
        return body

    def tmpl_display_queries_results(self, job_result, language = CFG_SITE_LANG):
        """Creates a page displaying results from execution of multiple queries.

        @param job_result: JobResult object containing the job results
        that will be displayed
        @param language: language of the page

        @return: The HTML content of the page
        """
        _ = gettext_set_language(language)
        queries_results = job_result.get_query_results()
        output_format = job_result.get_job().get_output_format()
        job_result_id = job_result.get_id()

        body = ""

        if job_result_id != JobResult.ID_MISSING:
            download_and_format_html = """
            <a href="%(download_job_results_url)s?result_id=%(job_result_id)s&ln=%(language)s"><input type="button" value="%(label_download)s" class="formbutton"></a>
            &nbsp;&nbsp;&nbsp;&nbsp;
            <strong>%(label_view_as)s</strong>
            <a href="%(display_job_result_url)s?result_id=%(job_result_id)s&output_format=%(output_format_marcxml)s&ln=%(language)s">MARCXML</a>
            <a href="%(display_job_result_url)s?result_id=%(job_result_id)s&output_format=%(output_format_marc)s&ln=%(language)s">MARC</a>

            """ %  self._html_escape_dictionary({
                    "label_download" : _("Download"),
                    "label_view_as" : _("View as: "),
                    "output_format_marcxml" : Job.OUTPUT_FORMAT_MARCXML,
                    "output_format_marc" : Job.OUTPUT_FORMAT_MARC,
                    "download_job_results_url" : self._DOWNLOAD_JOB_RESULT_URL,
                    "language" : language,
                    "display_job_result_url" : self._DISPLAY_JOB_RESULT_URL,
                    "job_result_id" : job_result_id
                    })
            body += download_and_format_html

        for query_result in queries_results:
            query = query_result.get_query()
            results = query_result.get_result(output_format)

            html = """
<h2>%(name)s</h2>
<strong>%(query_label)s: </strong>%(search_criteria)s<br>
<strong>%(output_fields_label)s: </strong>%(output_fields)s<br>
<textarea rows="10" style="width: 100%%" wrap="off" readonly>%(results)s</textarea></td>
            """ % self._html_escape_dictionary({
            "query_label" : _("Query"),
            "output_fields_label" : _("Output fields"),
            "name" : query.get_name(),
            "search_criteria" : query.get_search_criteria(),
            "output_fields" : ",".join(query.get_output_fields()),
            "results" : results
            })

            body += html

        return body

    def tmpl_display_job_history(self, job_results, language = CFG_SITE_LANG):
        """Creates a page displaying information about
        the job results given as a parameter.

        @param job_results: List of JobResult objects containing
        information about the job results that have to be displayed
        @param language: language of the page

        @return: The HTML content of the page
        """
        _ = gettext_set_language(language)

        table_rows = ""
        for current_job_result in job_results:
            current_job = current_job_result.get_job()
            # convert execution date into text proper to be shown to the user
            execution_date_time = current_job_result.get_execution_date_time()
            date = convert_datestruct_to_dategui(execution_date_time)
            # obtain text corresponding to the frequency of execution
            frequency = current_job.get_frequency()
            frequency_text = self._get_frequency_text(frequency, language)
            # set the status text
            if current_job_result.STATUS_CODE_OK == current_job_result.get_status():
                status = _("OK")
            else:
                status = _("Error")

            records_found = current_job_result.get_number_of_records_found()

            row = """<tr>
            <td><a href="%(job_results_url)s?result_id=%(job_result_id)s&ln=%(language)s">%(job_name)s</a></td>
            <td>%(job_frequency)s</td>
            <td>%(execution_date)s</td>
            <td><b>%(status)s</b>
                <a href="%(display_job_result_url)s?result_id=%(job_result_id)s&ln=%(language)s">
                <small>%(number_of_records_found)s %(label_records_found)s</small>
                </a>
            </td>
            </tr>""" %  self._html_escape_dictionary({
                        "job_name" : current_job.get_name(),
                        "job_frequency" : frequency_text,
                        "execution_date" : date,
                        "status" : status,
                        "number_of_records_found" : records_found,
                        "label_records_found" : _("records found"),
                        "job_results_url" : self._JOB_RESULTS_URL,
                        "display_job_result_url" : self._DISPLAY_JOB_RESULT_URL,
                        "language" : language,
                        "job_result_id" : current_job_result.get_id()
                        })
            table_rows += row

        body = """
        <table class="spacedcells">
            <th>%(label_job_name)s</th>
            <th>%(label_job_frequency)s</th>
            <th>%(label_execution_date)s</th>
            <th>%(label_status)s</th>
            %(table_rows)s
        </table>
        """ % {
            "table_rows" : table_rows,
            "label_job_name" : _("Job"),
            "label_job_frequency" : _("Run"),
            "label_execution_date" : _("Date"),
            "label_status" : _("Status")
            }

        return body

    def tmpl_display_job_result_information(self, job_result, language = CFG_SITE_LANG):
        """Creates a page with information about a given job result

        @param job_result: JobResult object with containg the job result

        @param language: language of the page

        @return: The HTML content of the page
        """
        _ = gettext_set_language(language)

        table_rows = ""
        for current_query_result in job_result.get_query_results():
            current_query_name = current_query_result.get_query().get_name()
            # set the status text
            if current_query_result.STATUS_CODE_OK == current_query_result.get_status():
                status = _("OK")
            else:
                status = _("Error")

            records_found = current_query_result.get_number_of_records_found()

            row = """<tr>
            <td>%(query_name)s</td>
            <td><b>%(status)s</b></td>
            <td><small>%(number_of_records_found)s %(label_records_found)s</small></td>
            </tr>""" %  self._html_escape_dictionary({
                        "query_name" : current_query_name,
                        "status" : status,
                        "number_of_records_found" : records_found,
                        "label_records_found" : _("records found")
                        })
            table_rows += row

        number_of_all_records_found = job_result.get_number_of_records_found()
        job_result_id = job_result.get_id()

        final_row = """
        <tr>
            <td></td>
            <td><b>%(label_total)s</b></td>
            <td>
                <a href="%(display_job_results_url)s?result_id=%(job_result_id)s&ln=%(language)s">
                    <b>%(number_of_all_records_found)s %(label_records_found)s</b>
                </a>
            </td>
        </tr>""" %  self._html_escape_dictionary({
                "label_total" : _("Total"),
                "number_of_all_records_found" : number_of_all_records_found,
                "label_records_found" : _("records found"),
                "display_job_results_url" : self._DISPLAY_JOB_RESULT_URL,
                "language" : language,
                "job_result_id" : job_result_id
                })
        table_rows += final_row

        download_row = """
        <tr>
            <td></td><td></td><td>
                <a href="%(download_job_results_url)s?result_id=%(job_result_id)s&ln=%(language)s">
                    <input type="button" value="%(label_download)s" class="formbutton">
                </a>
            </td>
        </tr>""" %  self._html_escape_dictionary({
                "label_download" : _("Download"),
                "download_job_results_url" : self._DOWNLOAD_JOB_RESULT_URL,
                "language" : language,
                "job_result_id" : job_result_id
                })
        table_rows += download_row

        job_name = self._html_escape_content(job_result.get_job().get_name())
        if(job_result.get_status() == job_result.STATUS_CODE_ERROR):
            status_messasge = job_result.get_status_message()
        else:
            status_messasge = ""
        status_messasge = self._html_escape_content(status_messasge)

        body = """
        <h2>%(job_name)s</h2>

        <table class="spacedcells">
            <th>%(label_query)s</th>
            <th>%(label_status)s</th>
            <th></th>
            %(table_rows)s
        </table>
        <br>
        <pre style="color: Red;">%(status_message)s</pre>
        """ % {
            "table_rows" : table_rows,
            "label_query" : _("Query"),
            "label_status" : _("Status"),
            "job_name" : job_name,
            "status_message" : status_messasge
            }

        return body

    def _get_select_all_none_html(self, form_name, field_name, language = CFG_SITE_LANG):
        """Returns HTML providing Select All|None links

        @param form_name: the name of the form containing the checkboxes
        @param field_name: the name of the checkbox fields that will be affected
        @param language: language for output
        """
        _ = gettext_set_language(language)

        output_html = """
        %(label_select)s: <a href="javascript:SetAllCheckBoxes('%(form_name)s', '%(field_name)s', true);">%(label_all)s</a>, <a href="javascript:SetAllCheckBoxes('%(form_name)s', '%(field_name)s', false);">%(label_none)s</a>
        """% {
            "label_select" : _("Select"),
            "label_all" : _("All"),
            "label_none" : _("None"),
            "form_name" : form_name,
            "field_name" : field_name
            }

        return output_html

    def _get_frequency_text(self, frequency, language = CFG_SITE_LANG):
        """
        Returns text representation of the frequency: Manually, Daily, Weekly, Monthly

        @param frequency: integer containg the number of hours between every execution.

        @param language: language for output
        """
        _ = gettext_set_language(language)

        if 0 == frequency:
            frequency_text = _("Manually")
        elif 24 == frequency:
            frequency_text = _("Daily")
        elif 168 == frequency:
            frequency_text = _("Weekly")
        elif 720 == frequency:
            frequency_text = _("Monthly")
        else:
            frequency_text = "Every %s hours" % (frequency,)

        return frequency_text

    def _create_output_format_select_box(self, selected_value = 0):
        """
        Creates a select box for output format of a job.

        @param name: name of the control
        @param language: language of the menu
        @param selected_value: value selected in the control

        @return: HTML string representing HTML select control.
        """
        items = [("MARCXML", Job.OUTPUT_FORMAT_MARCXML),
                 ("MARC", Job.OUTPUT_FORMAT_MARC)]

        html_output = self._create_select_box("output_format", items, selected_value)

        return html_output

    def _create_frequency_select_box(self, name, selected_value = 0, language = CFG_SITE_LANG):
        """
        Creates a select box for frequency of an action/task.

        @param name: name of the control
        @param language: language of the menu
        @param selected_value: value selected in the control

        @return: HTML string representing HTML select control.
        """
        items = [(self._get_frequency_text(0, language), 0),
                 (self._get_frequency_text(24, language), 24),
                 (self._get_frequency_text(168, language), 168),
                 (self._get_frequency_text(720, language), 720)]

        html_output = self._create_select_box(name, items, selected_value)

        return html_output

    def _create_select_box(self, name, items, selected_value = None):
        """ Returns the HTML code for a select box.

        @param name: the name of the control
        @param items: list of (text, value) tuples where text is the text to be displayed
        and value is the value corresponding to the text in the select box
        e.g. [("first", 1), ("second", 2), ("third", 3)]
        @param selected_value: the value that will be selected
        in the select box.
        """
        html_output = """<select name="%s">""" % name

        for text, value in items:
            if selected_value == value:
                selected = 'selected="selected"'
            else:
                selected = ""

            current_option = """<option value="%(value)s" %(selected)s>%(text)s</option>""" % self._html_escape_dictionary({
                "value" : value,
                "text" : text,
                "selected" :selected
                })
            html_output += current_option

        html_output += """</select>"""
        return html_output

    def _html_escape_dictionary(self, dictionaty_to_escape):
        """Escapes all the values in the dictionary and transform
        them in strings that are safe to siplay in HTML page.

        HTML special symbols are replaced with their sage equivalents.

        @param dictionaty_to_escape: dictionary containing values
        that have to be escaped.

        @return: returns dictionary with the same keys where the
        values are escaped strings"""
        for key in dictionaty_to_escape:
            value = "%s" % dictionaty_to_escape[key]
            dictionaty_to_escape[key] = cgi.escape(value)

        return dictionaty_to_escape

    def _html_escape_content(self, content_to_escape):
        """Escapes the value given as parameter and
        trasforms it to a string that is safe for display in HTML page.

        @param content_to_escape: contains the content that have to be escaped.

        @return: string containing the escaped content
        """
        text_content = "%s" % content_to_escape
        escaped_content = cgi.escape(text_content)
        return escaped_content
