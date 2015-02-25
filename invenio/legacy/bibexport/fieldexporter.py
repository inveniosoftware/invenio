# -*- coding: utf-8 -*-
# $Id: search_engine_query_parser.py,v 1.12 2008/06/13 15:35:13 rivanov Exp $

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

# pylint: disable=C0301

"""Invenio Search Engine query parsers."""

__lastupdated__ = """$Date: 2008/06/13 15:35:13 $"""

__revision__ = "$Id: search_engine_query_parser.py,v 1.12 2008/06/13 15:35:13 rivanov Exp $"

from invenio.legacy.bibsched.bibtask import write_message

# imports used in FieldExporter class
import invenio.legacy.search_engine
from invenio.legacy import bibrecord
from invenio.legacy.bibdocfile import api as bibdocfile
import os

# imports used in perform_request_... methods
from invenio.config import CFG_SITE_LANG
from . import fieldexporter_dblayer

from invenio.legacy import template
fieldexporter_templates = template.load('bibexport')
from invenio.base.i18n import gettext_set_language

def run_export_method(jobname):
    """Main function, reading params and running the task."""
    write_message("bibexport_fieldexporter: job %s started." % jobname)

    job = fieldexporter_dblayer.get_job_by_name(jobname)
    job_result = _run_job(job)

    if job_result.STATUS_CODE_OK != job_result.get_status():
        error_message = job_result.get_status_message()
        write_message("Error during %s execution. Error message: %s" % (jobname, error_message) )

    write_message("bibexport_fieldexporter: job %s started." % jobname)

def _run_job(job):
    """Execute a job and saves the results

    @param job: Job object containing inforamtion about the job

    @return: JobResult object containing informatoin about the result
    of job execution
    """
    exporter = FieldExporter()

    job_result = exporter.execute_job(job)

    fieldexporter_dblayer.save_job_result(job_result)

    return job_result

class FieldExporter:
    """Provides mothods for exporting given fields from
    records corresponding to a given search criteria.

    It provides also methods for transforming the resulting
    MARC XML into other formats.
    """
    def __init__(self):
        """Nothing to init"""
        pass

    def _export_fields(self, search_criteria, output_fields):
        """Export fields that are among output_fields from
        all the records that match the search criteria.

        @param search_criteria: combination of search terms in Invenio
        @param output_fields: list of fields that should remain in the records

        @return: MARC XML with records containing only the fields that are
        among output fields
        """
        records = self._get_records(search_criteria)

        filtered_xml = self._filter_records_fields(records, output_fields)

        return filtered_xml

    def execute_query(self, query):
        """Executes a query and returns the result of execution.

        @param query: Query object containing information about the query.

        @return: QueryResult object containing the result.
        """
        search_criteria = query.get_search_criteria()
        output_fields = query.get_output_fields()

        xml_result = self._export_fields(search_criteria, output_fields)

        query_result = fieldexporter_dblayer.QueryResult(query, xml_result)

        return query_result

    def execute_job(self, job):
        """Executes a job and returns the result of execution.

        @param job: Job object containing information about the job.

        @return: JobResult object containing the result.
        """
        job_result = fieldexporter_dblayer.JobResult(job)

        job_queries = fieldexporter_dblayer.get_job_queries(job.get_id())

        for current_query in job_queries:
            current_query_result = self.execute_query(current_query)
            job_result.add_query_result(current_query_result)

        return job_result

    def _get_records(self, search_criteria):
        """Creates MARC XML containing all the records corresponding
        to a given search criteria.

        @param search_criteria: combination of search terms in Invenio

        @return: MARC XML containing all the records corresponding
        to the search criteria"""
        record_IDs = search_engine.perform_request_search(p = search_criteria)

        records_XML = self._create_records_xml(record_IDs)

        return records_XML

    def _filter_records_fields(self, records_xml, output_fields):
        """Leaves in the records only fields that are necessary.
        All the other fields are removed from the records.

        @param records_xml: MARC XML containing all the information about the records
        @param output_fields: list of fields that should remain in the records

        @return: MARC XML with records containing only fields that are
        in output_fields list.
        """
        # Add 001/970 to the output fields. 970 is necessary for system number
        # extraction when exporting in aleph marc. When we add more formats,
        # we can add it optionally only when exporting aleph marc.
        output_fields.append("001")
        output_fields.append("970")

        records = bibrecord.create_records(records_xml)
        output_records = []

        for (record, status_code, list_of_errors) in records:
            record = self._filter_fields(record, output_fields)
            # do not return empty records
            if not self._is_record_empty(record):
                output_records.append(record)

        output_xml = bibrecord.print_recs(output_records)

        return output_xml

    def _is_record_empty(self, record):
        """Check if a record is empty.

        We assume that record is empty if all the values of the
        tags are empty lists or the record dictionary itself is empty.

        @param record: record structure (@see: bibrecord.py for details)

        @return True if the record is empty
        """
        for value in record.values():
            if len(value) > 0:
                return False

        return True

    def _filter_fields(self, record, output_fields):
        """Removes from the record all the fields
        that are not output_fields.

        @param record: record structure (@see: bibrecord.py for details)
        @param output_fields: list of fields that should remain in the record

        @return: record containing only fields among output_fields
        """
        # Tibor's new implementation:
        for tag in record.keys():
            if tag not in output_fields:
                bibrecord.record_delete_fields(record, tag)
        return record

        # Rado's old implementation that leads to bibrecord-related
        # bug, see <https://savannah.cern.ch/task/?10267>:
        record_keys = record.keys()

        # Check if any of the tags, fields or subfields match
        # any value in output_fields. In case of match we leave
        # the element and its children in the record.
        #
        # If the element and all its children are not among the
        # output fields, it is deleted
        for tag in record_keys:
            tag = tag.lower()
            if tag not in output_fields:
                for (subfields, ind1, ind2, value, field_number) in record[tag]:
                    current_field = tag + ind1.strip() + ind2.strip()
                    current_field = current_field.lower()
                    if current_field not in output_fields:
                        delete_parents = True

                        for (code, value) in subfields:
                            current_subfield = current_field + code
                            current_subfield = current_subfield.lower()
                            if current_subfield not in output_fields:
                                bibrecord.record_delete_subfield(record, tag, code, ind1, ind2)
                            else:
                                delete_parents = False

                        if delete_parents:
                            bibrecord.record_delete_field(record, tag, ind1, ind2)
        return record

    def _create_records_xml(self, record_IDs):
        """Creates XML containing all the information
        for the records with the given identifiers

        @param record_IDs: list of identifiers of records

        @return: MARC XML containing all the information about the records
        """
        output_xml = "<collection>"

        for record_id in record_IDs:
            record_xml = search_engine.print_record(recID = record_id, format = "xm")
            output_xml += record_xml

        output_xml += "</collection>"

        return output_xml

def get_css():
    """Returns the CSS for field exporter pages."""
    return fieldexporter_templates.tmpl_styles()

def get_navigation_menu(language = CFG_SITE_LANG):
    """Returns HTML reresenting the navigation menu
    of field exporter

    @param language: language of the page
    """
    return fieldexporter_templates.tmpl_navigation_menu(language)

def perform_request_new_job(language = CFG_SITE_LANG):
    """Displays a page for creation of a new job.

    @param language: language of the page
    """
    job = fieldexporter_dblayer.Job()
    return fieldexporter_templates.tmpl_edit_job(job, language = language)

def perform_request_edit_job(job_id, user_id, language = CFG_SITE_LANG):
    """Displays a page where the user can edit information
    about a job.

    @param job_id: identifier of the job that will be edited
    @param user_id: identifier of the user
    @param language: language of the page
    """
    _check_user_ownership_on_job(user_id, job_id, language)

    job = fieldexporter_dblayer.get_job(job_id)
    return fieldexporter_templates.tmpl_edit_job(job, language = language)

def perform_request_save_job(job, user_id, language = CFG_SITE_LANG):
    """Saves a job.

    @param job: Object containing information about the job
    @param user_id: identifier of the user saving the job
    @param language: language of the page

    @return: identifier of the job
    """
    job_id = job.get_id()
    _check_user_ownership_on_job(user_id, job_id, language)

    return fieldexporter_dblayer.save_job(user_id, job)

def perform_request_delete_jobs(job_ids, user_id, language = CFG_SITE_LANG):
    """Deletes all the jobs which ids are given as a parameter.

    @param job_ids: list with identifiers of jobs that have to be deleted
    @param user_id: identifier of the user deleting the jobs
    @param language: language of the page
    """
    for job_id in job_ids:
        _check_user_ownership_on_job(user_id, job_id, language)
        fieldexporter_dblayer.delete_job(job_id)

def perform_request_run_jobs(job_ids, user_id, language = CFG_SITE_LANG):
    """Runs all the jobs which ids are given as a parameter

    @param job_ids: list with identifiers of jobs that have to be run
    @param user_id: identifier of the user running the jobs
    @param language: language of the page
    """
    for current_job_id in job_ids:
        _check_user_ownership_on_job(user_id, current_job_id, language)
        current_job = fieldexporter_dblayer.get_job(current_job_id)
        _run_job(current_job)

def perform_request_jobs(user_id, language = CFG_SITE_LANG):
    """Displays a page containing list of all
    jobs of the current user

    @param user_id: identifier of the user owning the jobs
    @param language: language of the page
    """
    all_jobs = fieldexporter_dblayer.get_all_jobs(user_id)
    return fieldexporter_templates.tmpl_display_jobs(jobs = all_jobs, language = language)

def perform_request_job_queries(job_id, user_id, language = CFG_SITE_LANG):
    """Displays a page containing list of all
    all queries for a given job

    @param job_id: identifier of the job containing the queries
    @param user_id: identifier of the current user
    @param language: language of the page
    """
    _check_user_ownership_on_job(user_id, job_id, language)
    queries = fieldexporter_dblayer.get_job_queries(job_id)
    return fieldexporter_templates.tmpl_display_job_queries(job_queries = queries,
                                                            job_id = job_id,
                                                            language = language)

def perform_request_new_query(job_id, user_id, language = CFG_SITE_LANG):
    """Displays a page for creation of new query.

    @param job_id: identifier of the job containing the query
    @param user_id: identifier of user creating the query
    @param language: language of the page
    """
    _check_user_ownership_on_job(user_id, job_id, language)
    query = fieldexporter_dblayer.Query()
    return fieldexporter_templates.tmpl_edit_query(query, job_id, language)

def perform_request_edit_query(query_id, job_id, user_id, language = CFG_SITE_LANG):
    """Displays a page where the user can edit information
    about a job.

    @param query_id: identifier of the query that will be edited
    @param job_id: identifier of the job containing the query
    @param user_id: identifier of the user editing the query
    @param language: language of the page
    """
    _check_user_ownership_on_job(user_id, job_id, language)
    _check_user_ownership_on_query(user_id, query_id, language)

    query = fieldexporter_dblayer.get_query(query_id)
    return fieldexporter_templates.tmpl_edit_query(query, job_id, language)

def perform_request_save_query(query, job_id, user_id, language = CFG_SITE_LANG):
    """Saves a query in database.

    @param query: Query objectect containing the necessary informatoin
    @param job_id: identifier of the job containing the query
    @param user_id: identifier of the user saving the query
    @param language: language of the page
    """
    _check_user_ownership_on_job(user_id, job_id, language)
    _check_user_ownership_on_query(user_id, query.get_id(), language)
    fieldexporter_dblayer.save_query(query, job_id)

def perform_request_delete_queries(query_ids, user_id, language = CFG_SITE_LANG):
    """Deletes all the queries which ids are given as a parameter.

    @param query_ids: list with identifiers of queries that have to be deleted
    @param user_id: identifier of the user deleting the queries
    @param language: language of the page
    """
    for query_id in query_ids:
        _check_user_ownership_on_query(user_id, query_id, language)
        fieldexporter_dblayer.delete_query(query_id)

def perform_request_run_queries(query_ids, user_id, job_id, language = CFG_SITE_LANG):
    """Displays a page contining results from execution of given queries.

    @param query_ids: list of query identifiers
    @param user_id: identifier of the user running the queries
    @param language: language of the page
    """
    exporter = FieldExporter()

    _check_user_ownership_on_job(user_id, job_id, language)
    job = fieldexporter_dblayer.get_job(job_id)
    job_result = fieldexporter_dblayer.JobResult(job)

    queries_results = []
    for current_id in query_ids:
        _check_user_ownership_on_query(user_id, current_id, language)
        current_query = fieldexporter_dblayer.get_query(current_id)
        current_result = exporter.execute_query(current_query)
        job_result.add_query_result(current_result)

    return fieldexporter_templates.tmpl_display_queries_results(job_result, language)

def perform_request_job_history(user_id, language = CFG_SITE_LANG):
    """Displays a page containing information about the executed jobs.

    @param user_id: identifier of the user owning the reuslts
    @param language: language of the page
    """
    job_result_identifiers = fieldexporter_dblayer.get_all_job_result_ids(user_id = user_id)
    job_results = fieldexporter_dblayer.get_job_results(job_result_identifiers)

    return fieldexporter_templates.tmpl_display_job_history(job_results, language)

def perform_request_job_results(job_result_id, user_id, language = CFG_SITE_LANG):
    """Displays a page with information about the results of a particular job.

    @param job_result_id: identifier of the job result that should be displayed
    @param user_id: identifier of the current user
    @param language: language of the page
    """
    _check_user_ownership_on_job_result(user_id, job_result_id, language)

    job_result = fieldexporter_dblayer.get_job_result(job_result_id)

    return fieldexporter_templates.tmpl_display_job_result_information(job_result, language)

def perform_request_download_job_result(req, job_result_id, output_format, user_id, language = CFG_SITE_LANG):
    """
    Returns to the browser zip file containing the content of the job result

    @param req: request as received from apache
    @param job_result_id: identifier of the job result that should be displayed
    @param user_id: identifier of the current user
    @param language: language of the page
    @param output_format: format for downloading the result
    """
    _check_user_ownership_on_job_result(user_id, job_result_id, language)

    job_result = fieldexporter_dblayer.get_job_result(job_result_id)
    if output_format != fieldexporter_dblayer.Job.OUTPUT_FORMAT_MISSING:
        job_result.get_job().set_output_format(output_format)

    download_file_name = "result.zip"
    temp_zip_file_path = ""

    try:
        temp_zip_file_path = fieldexporter_dblayer.create_temporary_zip_file_with_job_result(job_result)
        bibdocfile.stream_file(req, temp_zip_file_path, download_file_name)
    finally:
        if os.path.exists(temp_zip_file_path):
            os.remove(temp_zip_file_path)

def perform_request_display_job_result(job_result_id, output_format, user_id, language = CFG_SITE_LANG):
    """Displays a page with the results of a particular job.

    @param job_result_id: identifier of the job result that should be displayed
    @param user_id: identifier of the current user
    @param language: language of the page
    """
    _check_user_ownership_on_job_result(user_id, job_result_id, language)

    job_result = fieldexporter_dblayer.get_job_result(job_result_id)

    if output_format != fieldexporter_dblayer.Job.OUTPUT_FORMAT_MISSING:
        job_result.get_job().set_output_format(output_format)

    return fieldexporter_templates.tmpl_display_queries_results(job_result, language)

def _check_user_ownership_on_job(user_id, job_id, language = CFG_SITE_LANG):
    """Check if user owns a job. In case user is not the owner, exception is thrown.

    @param user_id: identifier of the user
    @param job_id: identifier of the job
    @param language: language of the page
    """
    if fieldexporter_dblayer.Job.ID_MISSING == job_id:
        return

    if not fieldexporter_dblayer.is_user_owner_of_job(user_id, job_id):
        _ = gettext_set_language(language)
        error_message = _("You are not authorised to access this resource.")
        raise AccessDeniedError(error_message)

def _check_user_ownership_on_job_result(user_id, job_result_id, language = CFG_SITE_LANG):
    """Check if user owns a job result. In case user is not the owner, exception is thrown.

    @param user_id: identifier of the user
    @param job_result_id: identifier of the job result
    @param language: language of the page
    """
    if fieldexporter_dblayer.JobResult.ID_MISSING == job_result_id:
        return

    if not fieldexporter_dblayer.is_user_owner_of_job_result(user_id, job_result_id):
        _ = gettext_set_language(language)
        error_message = _("You are not authorised to access this resource.")
        raise AccessDeniedError(error_message)

def _check_user_ownership_on_query(user_id, query_id, language = CFG_SITE_LANG):
    """Check if user owns a job result. In case user is not the owner, exception is thrown.

    @param user_id: identifier of the user
    @param job_result_id: identifier of the job result
    @param language: language of the page
    """
    if fieldexporter_dblayer.Query.ID_MISSING == query_id:
        return

    if not fieldexporter_dblayer.is_user_owner_of_query(user_id, query_id):
        _ = gettext_set_language(language)
        error_message = _("You are not authorised to access this resource.")
        raise AccessDeniedError(error_message)

class AccessDeniedError(Exception):
    """Exception indicating an error during exportting for Google scholar."""

    _error_message = ""
    _inner_exception = None

    def __init__(self, error_message, inner_exception = None):
        """Constructor of the exception"""
        Exception.__init__(self, error_message, inner_exception)

        self._error_message = error_message
        self._inner_exception = inner_exception

    def get_error_message(self):
        """Returns the error message that explains the reason for the exception"""
        return self._error_message

    def get_inner_exception(self):
        """Returns the inner exception that is the cause for the current exception"""
        return self._inner_exception

    def __str__(self):
        """Returns string representation"""
        return self._error_message
