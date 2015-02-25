# -*- coding: utf-8 -*-
# $Id: webmessage_webinterface.py,v 1.13 2008/03/12 16:48:08 tibor Exp $
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

"""FieldExporter web interface"""

__revision__ = "$Id: webmessage_webinterface.py,v 1.13 2008/03/12 16:48:08 tibor Exp $"

__lastupdated__ = """$Date: 2008/03/12 16:48:08 $"""

import re
from invenio.legacy.webpage import page
from invenio.ext.legacy.handler import WebInterfaceDirectory, \
                                         wash_urlargd
from invenio.utils.url import redirect_to_url
from invenio.config import CFG_SITE_URL, \
                           CFG_SITE_SECURE_URL
from invenio.utils.date import convert_datestruct_to_datetext, \
                              convert_datetext_to_datestruct
from invenio.base.i18n import gettext_set_language
from invenio.legacy.bibexport.fieldexporter import get_css, \
                                        get_navigation_menu, \
                                        perform_request_edit_query, \
                                        perform_request_edit_job, \
                                        perform_request_jobs, \
                                        perform_request_new_job, \
                                        perform_request_save_job, \
                                        perform_request_delete_jobs, \
                                        perform_request_run_jobs, \
                                        perform_request_job_queries, \
                                        perform_request_new_query, \
                                        perform_request_save_query, \
                                        perform_request_delete_queries, \
                                        perform_request_run_queries, \
                                        perform_request_job_history, \
                                        perform_request_job_results, \
                                        perform_request_display_job_result, \
                                        perform_request_download_job_result, \
                                        AccessDeniedError
from invenio.legacy.bibexport.fieldexporter_dblayer import Job, \
                                                           Query, \
                                                           JobResult
from invenio.legacy.webuser import collect_user_info, \
                            page_not_authorized
from invenio.modules.access.engine import acc_authorize_action

class WebInterfaceFieldExporterPages(WebInterfaceDirectory):
    """Defines the set of /fieldexporter pages."""

    _exports = ["", "jobs", "edit_job",
                "job_queries", "edit_query",
                "job_results", "display_job_result", "download_job_result",
                "history", "not_authorized"]

    # constats containig URL to the pages
    _EXPORT_URL = "%s/exporter" % (CFG_SITE_URL, )
    _JOBS_URL = "%s/exporter/jobs" % (CFG_SITE_URL, )
    _EDIT_JOB_URL = "%s/exporter/edit_job" % (CFG_SITE_URL, )
    _EDIT_QUERY_URL = "%s/exporter/edit_query" % (CFG_SITE_URL, )
    _JOB_QUERIES_URL = "%s/exporter/job_queries" % (CFG_SITE_URL, )
    _JOB_HISTORY_URL = "%s/exporter/history" % (CFG_SITE_URL, )
    _NOT_AUTHORIZED_URL = "%s/exporter/not_authorized" % (CFG_SITE_URL, )

    _LOGIN_URL = "%s/youraccount/login" % (CFG_SITE_SECURE_URL,)

    _NAVTRAIL_EXPORT = """<a href="/exporter" class="navtrail">Export</a>"""

    def index(self, req, form):
        """ The function called by default"""
        redirect_to_url(req, self._JOB_HISTORY_URL)

    __call__ = index

    def jobs(self, req, form):
        """Displays all the jobs of a given user
        and allows creation, deletion and execution of jobs"""

        argd = wash_urlargd(form, {
                                   "new_button": (str, ""),
                                   "run_button": (str, ""),
                                   "delete_button": (str, ""),
                                   "selected_jobs": (list, "")
                                   })

        # load the right message language
        language = argd["ln"]
        _ = gettext_set_language(language)

        self._check_user_credentials(req, language)

        user_id = self._get_user_id(req)

        try:
            # if the form is submitted through some of the buttons
            # we should perform the appropriate action
            if argd["new_button"]:
                self._redirect_to_page(req, self._EDIT_JOB_URL, language)
            elif argd["delete_button"]:
                job_ids = argd["selected_jobs"]
                perform_request_delete_jobs(job_ids = job_ids,
                                            user_id = user_id,
                                            language = language)
            elif argd["run_button"]:
                job_ids = argd["selected_jobs"]
                perform_request_run_jobs(job_ids = job_ids,
                                         user_id = user_id,
                                         language = language)
                self._redirect_to_page(req, self._JOB_HISTORY_URL, language)

            user_id = self._get_user_id(req)
            body = perform_request_jobs(user_id = user_id,
                                        language = language)
        except AccessDeniedError:
            self._redirect_to_not_authorised_page(req, language)

        return page(title = _("Export Job Overview"),
                    metaheaderadd = get_css(),
                    body = body,
                    req = req,
                    navmenuid = "fieldexporter",
                    titleprologue = get_navigation_menu(language),
                    navtrail = self._NAVTRAIL_EXPORT,
                    language = language)

    def edit_job(self, req, form):
        """Edits an existing job or creates a new one"""

        # Create an empty job and use its default values
        # to init missing parameters
        job = Job()

        argd = wash_urlargd(form,
                            {"job_name": (str, job.get_name()),
                            "output_directory": (str, job.get_output_directory()),
                            "job_frequency": (int, job.get_frequency()),
                            "output_format": (int, job.get_output_format()),
                            "last_run": (str, convert_datestruct_to_datetext(job.get_last_run())),
                            "id": (int, job.get_id()),
                            "save_button": (str, ""),
                            "cancel_button": (str, ""),
                            "edit_queries_button": (str, "")
                            })
        language = argd["ln"]
        # load the right message language
        _ = gettext_set_language(language)

        self._check_user_credentials(req, language)

        user_id = self._get_user_id(req)
        job_id = argd["id"]

        job = Job(job_id = job_id,
                  name = argd["job_name"],
                  frequency = argd["job_frequency"],
                  output_format = argd["output_format"],
                  last_run = convert_datetext_to_datestruct(argd["last_run"]),
                  output_directory = argd["output_directory"])
        try:
            if argd["cancel_button"]:
                self._redirect_to_page(req, self._JOBS_URL, language)
            elif argd["save_button"]:
                perform_request_save_job(job = job,
                                         user_id = user_id,
                                         language = language)
                self._redirect_to_page(req, self._JOBS_URL, language)
            elif argd["edit_queries_button"]:
                result_job_id = perform_request_save_job(job = job,
                                         user_id = user_id,
                                         language = language)
                edit_queries_url = "%s?job_id=%s" % (self._JOB_QUERIES_URL, result_job_id)
                self._redirect_to_page(req, edit_queries_url, language)
            elif Job.ID_MISSING == job_id:
                title = _("New Export Job")
                body = perform_request_new_job(language = language)
            else:
                title = _("Edit Export Job")
                body = perform_request_edit_job(job_id = job_id,
                                                user_id = user_id,
                                                language = language)
        except AccessDeniedError:
            self._redirect_to_not_authorised_page(req, language)

        return page(title = title,
                    metaheaderadd=get_css(),
                    body = body,
                    req = req,
                    navmenuid = "fieldexporter",
                    titleprologue = get_navigation_menu(language),
                    navtrail = self._NAVTRAIL_EXPORT,
                    language = language)

    def job_queries(self, req, form):
        """Allows edition and manipulations of the queries of a job"""

        argd = wash_urlargd(form, {
                                   "new_button": (str, ""),
                                   "run_button": (str, ""),
                                   "delete_button": (str, ""),
                                   "selected_queries": (list, ""),
                                   "job_id": (int, -1)
                                   })
        # load the right message language
        language = argd["ln"]
        _ = gettext_set_language(language)

        self._check_user_credentials(req, language)

        user_id = self._get_user_id(req)
        job_id = argd["job_id"]

        try:
            # if the form is submitted through some of the buttons
            # we should perform the appropriate action
            if argd["new_button"]:
                new_query_url = "%s?job_id=%s" % (self._EDIT_QUERY_URL, job_id)
                self._redirect_to_page(req, new_query_url, language)
            if argd["delete_button"]:
                query_ids = argd["selected_queries"]
                perform_request_delete_queries(query_ids = query_ids,
                                               user_id = user_id,
                                               language = language)
            if argd["run_button"]:
                title = _("Query Results")
                query_ids = argd["selected_queries"]
                body = perform_request_run_queries(query_ids = query_ids,
                                                   user_id = user_id,
                                                   job_id = job_id,
                                                   language = language)
            else:
                title = _("Export Job Queries")
                body = perform_request_job_queries(job_id = job_id,
                                                   user_id = user_id,
                                                   language = language)
        except AccessDeniedError:
            self._redirect_to_not_authorised_page(req, language)

        return page(title = title,
                    metaheaderadd=get_css(),
                    body = body,
                    req = req,
                    navmenuid = "fieldexporter",
                    titleprologue = get_navigation_menu(language),
                    navtrail = self._NAVTRAIL_EXPORT,
                    language = language)

    def edit_query(self, req, form):
        """Edits an existing query or creates a new one"""

        # Create an empty job and use its default values
        # to init missing parameters
        query = Query()
        name = query.get_name()
        output_fields = ", ".join(query.get_output_fields())
        search_criteria = query.get_search_criteria()
        comment = query.get_comment()
        query_id = query.get_id()

        argd = wash_urlargd(form,
                            {"name": (str, name),
                            "search_criteria": (str, search_criteria),
                            "output_fields": (str, output_fields),
                            "comment": (str, comment),
                            "id": (int, query_id),
                            "job_id": (int, Job.ID_MISSING),
                            "save_button": (str, ""),
                            "cancel_button": (str, "")
                            })
        # load the right message language
        language = argd["ln"]
        _ = gettext_set_language(language)

        self._check_user_credentials(req, language)

        user_id = self._get_user_id(req)
        query_id = argd["id"]
        job_id = argd["job_id"]

        current_job_queries_url = "%s?job_id=%s" %(self._JOB_QUERIES_URL, job_id)

        try:
            if argd["cancel_button"]:
                self._redirect_to_page(req, current_job_queries_url, language)
            elif argd["save_button"]:
                name = argd["name"]
                search_criteria = argd["search_criteria"]
                comment = argd["comment"]

                # split the text entered by user to different fields
                outoutput_fields_text = argd["output_fields"]
                re_split_pattern = re.compile(r',\s*')
                output_fields = re_split_pattern.split(outoutput_fields_text)

                query = Query(query_id,
                              name,
                              search_criteria,
                              comment,
                              output_fields)
                perform_request_save_query(query = query,
                                           job_id = job_id,
                                           user_id = user_id,
                                           language = language)
                self._redirect_to_page(req, current_job_queries_url, language)
            elif Query.ID_MISSING == query_id:
                title = _("New Query")
                body = perform_request_new_query(job_id = job_id,
                                                 user_id = user_id,
                                                 language = language)
            else:
                title = _("Edit Query")
                body = perform_request_edit_query(query_id = query_id,
                                                  job_id = job_id,
                                                  user_id = user_id,
                                                  language = language)
        except AccessDeniedError:
            self._redirect_to_not_authorised_page(req, language)

        return page(title = title,
                    metaheaderadd=get_css(),
                    body = body,
                    req = req,
                    navmenuid   = "fieldexporter",
                    titleprologue = get_navigation_menu(language),
                    navtrail = self._NAVTRAIL_EXPORT,
                    language = language)

    def job_results(self, req, form):
        """Displays information about the results of a job"""
        argd = wash_urlargd(form, {
                           "result_id": (int, -1)
                           })
        # load the right message language
        language = argd["ln"]
        _ = gettext_set_language(language)

        self._check_user_credentials(req, language)

        user_id = self._get_user_id(req)
        job_result_id = argd["result_id"]

        title = _("Export Job Results")
        try:
            body = perform_request_job_results(job_result_id = job_result_id,
                                               user_id = user_id,
                                               language = language)
        except AccessDeniedError:
            self._redirect_to_not_authorised_page(req, language)

        return page(title = title,
                    metaheaderadd = get_css(),
                    body = body,
                    req = req,
                    navmenuid   = "fieldexporter",
                    titleprologue = get_navigation_menu(language),
                    navtrail = self._NAVTRAIL_EXPORT,
                    language = language)

    def display_job_result(self, req, form):
        """Displays the results of a job"""
        argd = wash_urlargd(form, {
                           "result_id": (int, JobResult.ID_MISSING),
                           "output_format" : (int, Job.OUTPUT_FORMAT_MISSING)
                           })
        # load the right message language
        language = argd["ln"]
        _ = gettext_set_language(language)

        self._check_user_credentials(req, language)

        user_id = self._get_user_id(req)
        job_result_id = argd["result_id"]
        output_format = argd["output_format"]

        title = _("Export Job Result")
        try:
            body = perform_request_display_job_result(job_result_id = job_result_id,
                                                      output_format = output_format,
                                                      user_id = user_id,
                                                      language = language)
        except AccessDeniedError:
            self._redirect_to_not_authorised_page(req, language)

        return page(title = title,
                    metaheaderadd = get_css(),
                    body = body,
                    req = req,
                    navmenuid   = "fieldexporter",
                    titleprologue = get_navigation_menu(language),
                    navtrail = self._NAVTRAIL_EXPORT,
                    language = language)

    def download_job_result(self, req, form):
        """Returns to the browser zip file containing the job result"""
        argd = wash_urlargd(form, {
                           "result_id" : (int, JobResult.ID_MISSING),
                           "output_format" : (int, Job.OUTPUT_FORMAT_MISSING)
                           })
        # load the right message language
        language = argd["ln"]
        job_result_id = argd["result_id"]
        output_format = argd["output_format"]
        user_id = self._get_user_id(req)

        _ = gettext_set_language(language)

        self._check_user_credentials(req, language)

        title = _("Export Job Result")
        try:
            perform_request_download_job_result(req = req,
                                                job_result_id = job_result_id,
                                                output_format = output_format,
                                                user_id = user_id,
                                                language = language)
        except AccessDeniedError:
            self._redirect_to_not_authorised_page(req, language)

    def history(self, req, form):
        """Displays history of the jobs"""
        argd = wash_urlargd(form, {})

        # load the right message language
        language = argd["ln"]
        _ = gettext_set_language(language)

        self._check_user_credentials(req, language)

        title = _("Export Job History")
        user_id = self._get_user_id(req)
        body = perform_request_job_history(user_id, language)

        return page(title = title,
                    metaheaderadd = get_css(),
                    body = body,
                    req = req,
                    navmenuid = "fieldexporter",
                    titleprologue = get_navigation_menu(language),
                    navtrail = self._NAVTRAIL_EXPORT,
                    language = language)

    def not_authorized(self, req, form):
        """Displays page telling the user that
        he is not authorised to access the resource"""
        argd = wash_urlargd(form, {})

        # load the right message language
        language = argd["ln"]
        _ = gettext_set_language(language)

        text = _("You are not authorised to access this resource.")
        return page_not_authorized(req = req, ln = language, text = text)

    def _check_user_credentials(self, req, language):
        """Check if the user is allowed to use field exporter

        @param req: request as received from apache
        @param language: the language of the page
        """
        user_info = collect_user_info(req)

        #redirect guests to login page
        if "1" == user_info["guest"]:
            referer_url = "%s?ln=%s" % (self._EXPORT_URL, language)
            redirect_url = "%s?ln=%s&referer=%s" % (self._LOGIN_URL,
                                                     language,
                                                     referer_url)
            redirect_to_url(req, redirect_url)
        #redirect unauthorized user to not_authorized page
        (auth_code, auth_msg) = acc_authorize_action(user_info, 'cfgbibexport')
        if 0 != auth_code:
            self._redirect_to_not_authorised_page(req, language)

    def _redirect_to_not_authorised_page(self, req, language):
        """Redirects user to page telling him that he is not
        authorised to do something

        @param req: request as received from apache
        @param language: the language of the page
        """
        self._redirect_to_page(req, self._NOT_AUTHORIZED_URL, language)

    def _redirect_to_page(self, req, url, language):
        """Redirects user to a page with the given URL
        and language.

        @param req: request as received from apache
        @param language: the language of the page
        @param url: url to redirect to
        """
        # check which symbol to use for appending the parameters
        # if this is the only parameter use ?
        if -1 == url.find("?"):
            append_symbol = "?"
        # if there are other parameters already appended, use &
        else:
            append_symbol = "&"

        redirect_url = "%s%sln=%s" % (url, append_symbol, language)
        redirect_to_url(req, redirect_url)

    def _get_user_id(self, req):
        """Return the identifier of the currently loged user.

        @param req: request as received from apache

        @return: identifier of currently logged user
        """
        user_info = collect_user_info(req)
        user_id = user_info['uid']

        return user_id
