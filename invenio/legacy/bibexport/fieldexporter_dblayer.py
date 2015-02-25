# -*- coding: utf-8 -*-
#
# $Id: webmessage_dblayer.py,v 1.28 2008/08/08 13:28:15 cparker Exp $
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

from __future__ import print_function

"""Every db-related function of plugin field exporter"""

__revision__ = "$Id: webmessage_dblayer.py,v 1.28 2008/08/08 13:28:15 cparker Exp $"

import os
import zipfile
import tempfile
import shutil
from time import localtime

from invenio.legacy.dbquery import run_sql
from invenio.utils.date import convert_datestruct_to_datetext, \
                              convert_datetext_to_datestruct
from invenio.legacy import bibrecord as bibrecord
from invenio.legacy.bibrecord import xmlmarc2textmarc as xmlmarc2textmarc

class Job:
    """Represents job that will run certain number of queries
    and save the results in a given location"""
    # Constants defining different output formats
    OUTPUT_FORMAT_MISSING = -1
    OUTPUT_FORMAT_MARCXML = 0
    OUTPUT_FORMAT_MARC = 1

    # Value indicating that the ID is not specified
    ID_MISSING = -1

    # ID of the job in the database
    _id = ID_MISSING

    # Name of the job, used to identify the job among the other jobs
    _name = ""

    # Frequence of execution of the job in hours
    _frequency = 0

    # Output format for displaying the results
    _output_format = 0

    # Last time when the job has run. If it is in the future the job will
    # run in the specified time
    _last_run = localtime()

    # Directory where the output of the queries will be stored
    _output_directory = ""

    def __init__(self, job_id = ID_MISSING,
                 name = "",
                 frequency = 0,
                 output_format = OUTPUT_FORMAT_MARCXML,
                 last_run = localtime(),
                 output_directory="" ):
        """Initialize the state of the object

        @param job_id: id of the job
        @param name: name of the job
        @param frequency: frequency of execution in hours
        @param last_run: last time when job has run
        @param output_directory: directory where the output of
                                the job will be stored
        """
        self._id = job_id
        self.set_name(name)
        self.set_frequency(frequency)
        self.set_output_format(output_format)
        self.set_last_run(last_run)
        self.set_output_directory(output_directory)

    def get_name(self):
        """Returns the name of the job"""
        return self._name

    def set_name(self, value):
        """Sets the name of the job"""
        self._name = value

    def get_frequency(self):
        """Returns the freqency of execution in hours"""
        return self._frequency

    def set_frequency(self, value):
        """Sets the freqency of execution in hours

        @param value: integer representing frequency of
        execution in hours
        """
        self._frequency = value

    def get_output_format(self):
        """Returns value indicating the ouput format of the job.

        @return: integer value representing output format"""
        return self._output_format

    def set_output_format(self, value):
        """Sets the output format of the job

        @param value: integer indicating the output format"""
        self._output_format = value

    def get_last_run(self):
        """Returns the last run time of the job.

        @return: datestruct representing last run"""
        return self._last_run

    def set_last_run(self, value):
        """Sets the last run time of the job.

        @param value: datestruct representing last run"""
        self._last_run = value

    def get_output_directory(self):
        """Returns the output directory"""
        return self._output_directory

    def set_output_directory(self, value):
        """Sets the output directory"""
        self._output_directory = value

    def get_id(self):
        """Returns identifier of the job"""
        return self._id

class Query:
    """Represents query that will return certain fields
    from the records that match the criteria of the query."""
    # Value indicating that the ID is not specified
    ID_MISSING = -1

    # ID of the query in the database
    _id = ID_MISSING

    # name of the query - it is defined by librarians and
    # helps them to identify their queries
    _name = ""

    # combination of search terms written the same way we
    # write them in the search box in Invenio
    _search_criteria = ""

    # free text that describes the query
    _comment = ""

    # list of fields that will be retrieved for every record
    _output_fields = []

    def __init__(self, query_id = ID_MISSING,
                 name = "",
                 search_criteria = "",
                 comment = "",
                 output_fields = []):
        """Initialize the state of the object

        @param id: id of the query in database
        @param  search_criteria: criteria used for searching records
        @param comment: text describing the query
        @param output_fields: list containing the fields that will be written in the output
        """
        self._id = query_id
        self.set_name(name)
        self.set_search_criteria(search_criteria)
        self.set_comment(comment)
        self.set_output_fields(output_fields)

    def get_search_criteria(self):
        """Returns the search criteria of the query"""
        return self._search_criteria

    def set_search_criteria(self, value):
        """Sets the search criteria of the query"""
        self._search_criteria = value

    def get_output_fields(self):
        """Returns a list of the fields that will
        be used to filter the output
        """
        return self._output_fields

    def set_output_fields(self, value):
        """
        Sets the fields that will be used to filter the output.
        Only these fields will be printed in the output
        """
        self._output_fields = value

    def get_name(self):
        """Returns the name of the query"""
        return self._name

    def set_name(self, value):
        """Sets the name of the query"""
        self._name = value

    def get_comment(self):
        """Returns description of the query"""
        return self._comment

    def set_comment(self, value):
        """Sets description of the query"""
        self._comment = value

    def get_id(self):
        """Returns identifier of the job"""
        return self._id

class QueryResult:
    """Class containing the result of query execution."""
    # Constants defining different kind of status of the query
    STATUS_CODE_OK = 0
    STATUS_CODE_ERROR = 1
    # Value indicating that the ID is not specified
    ID_MISSING = -1
    # ID of the query in the database
    _id = ID_MISSING
    # Query object representing the query related to this query result
    _query = None
    # Thu result of execution of the query
    _result = ""
    # Status of execution of the query
    # Contains information if the execution was successful or
    # there are errors during execution
    _status = STATUS_CODE_OK
    # Contains additional information about the status
    _status_message = ""

    def __init__(self, query,
                 result,
                 id = ID_MISSING,
                 status = STATUS_CODE_OK,
                 status_message = ""):
        """Initialize the state of the object

        @param id: identifier of the result in the database
        @param query: Query object with informatioin about query causing result
        @param result: the result of query execution
        @param status: status of execution
        @param status_message: text containing additional information about
        the status
        """
        self._id = id
        self.set_query(query)
        self.set_result(result)
        self.set_status(status)
        self.set_status_message(status_message)

    def get_result(self, output_format = Job.OUTPUT_FORMAT_MARCXML):
        """Returns MARC XML with the records that are
        result of the query execution"""
        # Originaly the result is kept in MARCXML
        result = self._result

        if output_format == Job.OUTPUT_FORMAT_MARC:
            result = self._create_marc(records_xml = result)

        return result

    def set_result(self, value):
        """Sets the result of execution

        @param value: MARC XML containing information
        for the records that are result of execution"""
        self._result = value

    def get_status(self):
        """Returns the status of the result

        @return: Integer value representing the status of execution"""
        return self._status

    def set_status(self, value):
        """Sets the status of the result.

        @param value: Integer value reperesenting the status of execution"""
        self._status = value

    def get_status_message(self):
        """Sets the status message of the result

        @return: string containing the message"""
        return self._status_message

    def set_status_message(self, value):
        """Returns the status message of the result

        @param value: string containing the message"""
        self._status_message = value

    def get_query(self):
        """Returns the query causing the result"""
        return self._query

    def set_query(self, value):
        """Sets the query causing the result

        @param value: Query object"""
        self._query = value

    def get_id(self):
        """Returns identifier of the query result"""
        return self._id

    def get_number_of_records_found(self):
        """Returns the number of records in the result"""
        records = bibrecord.create_records(self._result)
        records_count = len(records)

        return records_count

    def _create_marc(self, records_xml):
        """Creates MARC from MARCXML.

        @param records_xml: MARCXML containing information about the records

        @return: string containing information about the records
        in MARC format
        """
        aleph_marc_output = ""

        records = bibrecord.create_records(records_xml)
        for (record, status_code, list_of_errors) in records:
            sysno_options = {"text-marc":1}
            sysno = xmlmarc2textmarc.get_sysno_from_record(record,
                                                              sysno_options)
            options = {"aleph-marc":0, "correct-mode":1, "append-mode":0,
                       "delete-mode":0, "insert-mode":0, "replace-mode":0,
                       "text-marc":1}
            aleph_record = xmlmarc2textmarc.create_marc_record(record,
                                                                  sysno,
                                                                  options)
            aleph_marc_output += aleph_record

        return aleph_marc_output

class JobResult:
    """Class containing the result of job execution."""
    # Constants defining different kind of status of the job
    STATUS_CODE_OK = 0
    STATUS_CODE_ERROR = 1
    # Value indicating that the ID is not specified
    ID_MISSING = -1
    # ID of the query in the database
    _id = ID_MISSING
    # Query object representing the query related to this query result
    _job = None
    # List of query results (one result per query in the job)
    _query_results = []
    # Status of execution of the job
    # Contains information if the execution was successful or
    # there are errors during execution
    _status = STATUS_CODE_OK
    # Contains additional information about the status
    _status_message = ""
    # Date and time of job execution
    _execution_date_time = localtime()

    def __init__(self, job,
                 query_results = [],
                 execution_date_time = localtime(),
                 id = ID_MISSING,
                 status = STATUS_CODE_OK,
                 status_message = ""):
        """Initialize the state of the object

        @param id: identifier of the job result in the database
        @param query_results: List of query results
        (one result per query in the job)
        @param status: status of execution
        @param status_message: text containing additional information about
        the status
        """
        self._id = id
        self.set_job(job)
        self.set_query_results(query_results)
        self.set_execution_date_time(execution_date_time)
        self.set_status(status)
        self.set_status_message(status_message)

    def get_query_results(self):
        """Returns list of results from the queries in the job

        @return: List of QueryResult objects"""
        return self._query_results

    def set_query_results(self, value):
        """Sets the results of execution of the job queries.

        @param value: list of QueryResult objects
        """
        self._query_results = value

    def add_query_result(self, query_result):
        """Adds a aquery result to the results

        @param query_result: QueryResult object containing information
        about the result
        """
        self._query_results.append(query_result)

    def get_status(self):
        """Returns the status of the execution

        @return: Integer value representing the status of execution"""
        return self._status

    def set_status(self, value):
        """Sets the status of the execution.

        @param value: Integer value reperesenting the status of execution"""
        self._status = value

    def get_status_message(self):
        """Sets the status message of the result

        @return: string containing the message"""
        return self._status_message

    def set_status_message(self, value):
        """Returns the status message of the result

        @param value: string containing the message"""
        self._status_message = value

    def get_job(self):
        """Sets the job causing the result"""
        return self._job

    def add_status_message(self, message):
        """Adds additional message to status message field

        @param message: string containing the additional message
        """
        self._status_message += "\n"
        self._status_message += message

    def set_job(self, value):
        """Returns the job causing the result"""
        self._job = value

    def get_id(self):
        """Returns identifier of the job result"""
        return self._id

    def get_execution_date_time(self):
        """Returns the date and time of job execution.

        @return: datestruct representing date and time of execution"""
        return self._execution_date_time

    def set_execution_date_time(self, value):
        """Sets the last run time of the job.

        @param value: datestruct representing date and time of execution"""
        self._execution_date_time = value

    def get_number_of_records_found(self):
        """Returns the number of records in the job result"""
        records_count = 0

        for query_result in self.get_query_results():
            records_count += query_result.get_number_of_records_found()

        return records_count

class FieldExporterDBException(Exception):
    """
    Exception indicating an error during
    databese operation in field exproter.
    """
    _error_message = ""
    _inner_exception = None

    def __init__(self, error_message, inner_exception = None):
        """Constructor of the exception"""
        Exception.__init__(self, error_message, inner_exception)

        self._error_message = error_message
        self._inner_exception = inner_exception

    def get_error_message(self):
        """
        Returns the error message that explains
        the reason for the exception
        """
        return self._error_message

    def get_inner_exception(self):
        """
        Returns the inner exception that is the
        cause for the current exception
        """
        return self._inner_exception

def save_job(user_id, job):
    """Saves job in the database. If the job already exists it will be updated.

    @param user_id: identifier of the user owning the job
    @param job: Object containing information about the job

    @return: Returns the identifier of the job
    """
    job_id = job.get_id()

    if _exist_job(job_id):
        return _update_job(job)
    else:
        return _insert_job(user_id, job)

def delete_job(job_id):
    """Deletes a job from the database

    @param job_id: identifier of the job that has to be deleted

    @return 1 if delete was successful
    """

    query = """UPDATE expJOB SET deleted = 1 WHERE id=%s"""
    query_parameters = (job_id, )

    result = run_sql(query, query_parameters)
    return int(result)

def _exist_job(job_id):
    """Checks if a job exist in the database

    @param job_id: identifier of the job

    @return: True if the job exists, otherwise return False
    """

    query = """SELECT COUNT(id) FROM expJOB WHERE id=%s"""

    result = run_sql(query, (job_id, ))

    if 1 == result[0][0]:
        return True

    return False

def get_job(job_id):
    """Loads job from the database.

    @param job_id: identifier of the job

    @return: Job object containf information about the job
    or None if the job does not exist"""

    if not _exist_job(job_id):
        return None

    query = """SELECT id,
                        jobname,
                        jobfreq,
                        output_format,
                        DATE_FORMAT(lastrun,'%%Y-%%m-%%d %%H:%%i:%%s'),
                        output_directory
                FROM expJOB WHERE id=%s"""
    query_result = run_sql(query, (job_id,))

    (id, name, frequency, output_format, last_run, output_directory) = query_result[0]

    job = Job(id,
              name,
              frequency,
              output_format,
              convert_datetext_to_datestruct(last_run),
              output_directory)

    return job

def get_job_by_name(job_name):
    """Loads the first job with the given name found in database.

    @param job_name: name of the job

    @return: Job object containf information about the job
    or None if the job does not exist"""

    query = """SELECT id,
                        jobname,
                        jobfreq,
                        output_format,
                        DATE_FORMAT(lastrun,'%%Y-%%m-%%d %%H:%%i:%%s'),
                        output_directory
                FROM expJOB WHERE jobname=%s"""
    query_result = run_sql(query, (job_name,))

    if 0 == len(query_result):
        return None

    (id, name, frequency, output_format, last_run, output_directory) = query_result[0]

    job = Job(id,
              name,
              frequency,
              output_format,
              convert_datetext_to_datestruct(last_run),
              output_directory)

    return job

def get_all_jobs(user_id):
    """Loads all jobs from the database.

    @param user_id: identifier of the user owning the jobs

    @return: list of Job objects containing all the jobs
    owned by the user given as a parameter"""

    query = """SELECT expJOB.id,
                        expJOB.jobname,
                        expJOB.jobfreq,
                        expJOB.output_format,
                        DATE_FORMAT(expJOB.lastrun,'%%Y-%%m-%%d %%H:%%i:%%s'),
                        expJOB.output_directory
                FROM expJOB
                INNER JOIN user_expJOB
                ON expJOB.id = user_expJOB.id_expJOB
                WHERE user_expJOB.id_user = %s
                AND expJOB.deleted = 0
            """
    query_parameters = (user_id, )
    query_result = run_sql(query, query_parameters)

    all_jobs = []

    for (job_id, name, frequency, output_format, last_run, output_directory) in query_result:
        job = Job(job_id,
                  name,
                  frequency,
                  output_format,
                  convert_datetext_to_datestruct(last_run),
                  output_directory)
        all_jobs.append(job)

    return all_jobs

def _insert_job(user_id, job):
    """Inserts new job into database.

    @param user_id: identifier of the user owning the job
    @param job: Job object containing information about the job

    @return: Returns the identifier of the job"""
    job_id = run_sql("""INSERT INTO expJOB(jobname,
                                           jobfreq,
                                           output_format,
                                           lastrun,
                                           output_directory)
                        VALUES(%s, %s, %s, %s, %s)""",
                        (job.get_name(),
                         job.get_frequency(),
                         job.get_output_format(),
                         convert_datestruct_to_datetext(job.get_last_run()),
                         job.get_output_directory()
                         ))
    # create relation between job and user
    run_sql("""INSERT INTO user_expJOB(id_user,
                                           id_expJOB)
                        VALUES(%s, %s)""",
                        (user_id,
                         job_id
                        ))
    return job_id

def _update_job(job):
    """Updates data about existing job in the database.

    @param job: Object containing information about the job.
    """
    run_sql("""UPDATE expJOB SET jobname = %s,
                                 jobfreq = %s,
                                 output_format = %s,
                                 lastrun = %s,
                                 output_directory = %s
                            WHERE id=%s""",
                (job.get_name(),
                job.get_frequency(),
                job.get_output_format(),
                convert_datestruct_to_datetext(job.get_last_run()),
                job.get_output_directory(),
                job.get_id()
                ))

    return job.get_id()

def save_query(query, job_id):
    """Saves query in database. If the query already exists it will be updated.

    @param query: Object containing information about the query
    @param job_id: identifier of the job, containing the query

    @return: Returns the identifier of the query
    """

    query_id = query.get_id()

    if _exist_query(query_id):
        return _update_query(query)
    else:
        return _insert_query(query, job_id)

def _exist_query(query_id):
    """Checks if a query exist in the database

    @param query_id: identifier of the query

    @return: True if the query exists, otherwise return False
    """

    query = """SELECT COUNT(id) FROM expQUERY WHERE id=%s"""
    query_parameters = (query_id, )

    query_result = run_sql(query, query_parameters)

    if 1 == query_result[0][0]:
        return True

    return False

def _insert_query(query, job_id):
    """Inserts new query into database.

    @param query: Object containing information about the query
    @param job_id: Identifier of the job owning the query

    @return: Returns the identifier of the query"""

    # WE always attach a query to a job. If the given job id
    # does not exists it is an error
    if not _exist_job(job_id):
        raise FieldExporterDBException("There is no job with id %s" %(job_id,))

    output_fields = ",".join(query.get_output_fields())

    query_id = run_sql("""INSERT INTO expQUERY(name,
                                           search_criteria,
                                           output_fields,
                                           notes)
                        VALUES(%s, %s, %s, %s)""",
                        (query.get_name(),
                         query.get_search_criteria(),
                         output_fields,
                         query.get_comment()
                         ))

    run_sql("""INSERT INTO expJOB_expQUERY(id_expJOB,
                                           id_expQUERY)
                        VALUES(%s, %s)""",
                        (job_id,
                         query_id
                        ))

    return query_id

def _update_query(query):
    """Updates data about existing query in the database.

    @param query: Object containing information about the query.
    """

    output_fields = ",".join(query.get_output_fields())

    run_sql("""UPDATE expQUERY SET name = %s,
                                 search_criteria = %s,
                                 output_fields = %s,
                                 notes = %s
                            WHERE id=%s""",
                (query.get_name(),
                         query.get_search_criteria(),
                         output_fields,
                         query.get_comment(),
                         query.get_id()
                ))

    return query.get_id()

def get_job_queries(job_id):
    """Returns a list of all job queries

    @param job_id: identifier of the job

    @return: list of Query objects"""

    query = """SELECT id,
                        expQUERY.name,
                        expQUERY.search_criteria,
                        expQUERY.output_fields,
                        expQUERY.notes
                        FROM expQUERY
                        INNER JOIN expJOB_expQUERY
                        ON expQUERY.id = expJOB_expQUERY.id_expQUERY
                        WHERE expJOB_expQUERY.id_expJOB = %s
                        AND expQUERY.deleted = 0
                        """
    query_parameters = (job_id, )

    query_result = run_sql(query, query_parameters)

    all_queries = []

    for (query_id, name, search_criteria, output_fields, comment) in query_result:
        output_fields_list = output_fields.split(",")
        query = Query(query_id,
                      name,
                      search_criteria,
                      comment,
                      output_fields_list)
        all_queries.append(query)

    return all_queries

def get_query(query_id):
    """Loads query from the database.

    @param query_id: identifier of the query

    @return: Query object containf information about the query
    or None if the query does not exist"""

    if not _exist_query(query_id):
        return None

    query = """SELECT id,
                        name,
                        search_criteria,
                        output_fields,
                        notes
                        FROM expQUERY WHERE id=%s"""
    query_parameters = (query_id, )

    query_result = run_sql(query, query_parameters)

    (id, name, search_criteria, output_fields_text, comment) = query_result[0]
    output_fields = output_fields_text.split(",")

    job_query = Query(id, name, search_criteria, comment, output_fields)

    return job_query

def delete_query(query_id):
    """Deletes a query from the database

    @param query_id: identifier of the query that has to be deleted

    @return 1 if deletion was successful
    """
    query = """UPDATE expQUERY SET deleted = 1 WHERE id=%s"""
    query_parameters = (query_id, )

    result = run_sql(query, query_parameters)

    return int(result)

def save_job_result(job_result):
    """Saves a job result

    @param job_result: JobResult object containing information about
    the job and its result

    @return: Returns the identifier of the job result
    """
    #Save results in output directory
    _save_job_result_in_output_directory(job_result)

    # insert information about the job result in
    # expJOBRESULT table
    job_id = job_result.get_job().get_id()
    execution_time = convert_datestruct_to_datetext(job_result.get_execution_date_time())
    status = job_result.get_status()
    status_message = job_result.get_status_message()

    job_result_id = run_sql("""INSERT INTO expJOBRESULT(id_expJOB,
                                           execution_time,
                                           status,
                                           status_message)
                        VALUES(%s, %s, %s, %s)""",
                        (job_id,
                         execution_time,
                         status,
                         status_message
                         ))

    query_results = job_result.get_query_results()
    for current_query_result in query_results:
        _insert_query_result(current_query_result, job_result_id)

    return job_result_id

def _save_job_result_in_output_directory(job_result):
    """Saves a job result to the output directory of the job
    if it is specified

    @param job_result: JobResult object containing information about
    the job and its result
    """

    output_directory = job_result.get_job().get_output_directory()

    if "" == output_directory or None == output_directory:
        return

    # remove the slash from the end of the path if exists
    if output_directory[-1] == os.sep:
        output_directory = output_directory[:-1]

    # if directory does not exists then create it
    if not os.path.exists(output_directory):
        try:
            os.makedirs(output_directory)
        except(IOError, OSError), exception:
            job_result.set_status(job_result.STATUS_CODE_ERROR)
            job_result.set_status_message("Output directory %s does not exist and cannot be ctreated."
                                          % (output_directory, ))
            return

    # if it is not path to a directory report an error
    if not os.path.isdir(output_directory):
        job_result.set_status(job_result.STATUS_CODE_ERROR)
        job_result.add_status_message("%s is not a directory."
                                      % (output_directory, ))
        return

    query_results = job_result.get_query_results()
    output_format = job_result.get_job().get_output_format()

    for current_query_result in query_results:
        try:
            _save_query_result_in_file(current_query_result, output_directory, output_format)
        except (IOError, OSError) as exception:
            job_result.set_status(job_result.STATUS_CODE_ERROR)
            job_result.add_status_message("Failed to write result in file for query " +
                               current_query_result.get_query().get_name())

def _save_query_result_in_file(query_result, output_directory, output_format):
    """Saves query result in a file in a specified directory

    @param query_result: QueryResult object containing information about the query result
    @param output_directory: path to a directory where the new file will be placed
    """
    file_name = query_result.get_query().get_name()
    path = output_directory + os.sep + file_name
    print(path)

    output_file = None
    try:
        output_file = open(path, "w")
        text_to_write = query_result.get_result(output_format)
        output_file.write(text_to_write)
    finally:
        if not output_file is None:
            output_file.close()

def create_temporary_zip_file_with_job_result(job_result):
    """Creates temporary file containing the zipped content
    of the job result and returns the path to the file.

    The caller of the method is responsible for deleting the
    temporary file when done with it.

    @param job_result: job result that should be stored in the file

    @return: the absolute path name to the temporary file where the infromation
    is stored."""
    # create temporary directory
    path_to_temporary_directory = tempfile.mkdtemp()
    # save the job result into the temporary directory
    job_result.get_job().set_output_directory(path_to_temporary_directory)
    _save_job_result_in_output_directory(job_result)
    # create temporary file for zipping the content of the directory
    (temp_zip_file, path_to_temp_zip_file) = tempfile.mkstemp(suffix = ".zip")
    os.close(temp_zip_file)
    # zip the content of the directory
    _zip_directory_content_to_file(path_to_temporary_directory,
                                   path_to_temp_zip_file)
    # delete the temporary directory
    shutil.rmtree(path_to_temporary_directory)
    # return the path to the temporary file
    return path_to_temp_zip_file

def _zip_directory_content_to_file(path_to_directory, file):
    """
    Zips the whole content of a directory and adds it to
    a file

    @param path_to_directory: directory which content will be
    added to the archive
    @param file: path to a file (a string) or a file-like object
    where content will be added.
    """
    zip_file = zipfile.ZipFile(file = file, mode = "w")

    _write_directory_to_zip_file(path_to_directory, zip_file)

    zip_file.close()

def _write_directory_to_zip_file(path_to_directory, zip_file, arcname = ""):
    """Writes content of a directory to a zip file. If the directory
    contains subdirectories they are also added in the archive

    @param path_to_directory: directory which content will be
    added to the archive
    @param zip_file: ZipFile object where directory content will be written
    @param arcname: archive name of the directory
    """
    file_list = os.listdir(path_to_directory)

    for current_file_name in file_list:
        path_to_current_file = path_to_directory + os.sep + current_file_name
        # add directly the files
        if os.path.isfile(path_to_current_file):
            zip_file.write(path_to_current_file, arcname + current_file_name)
        # traverse recursively the directories and add their content
        if os.path.isdir(path_to_current_file):
            current_arcname = arcname + current_file_name + os.sep
            current_path_to_directory = path_to_directory + os.sep + current_file_name

            _write_directory_to_zip_file(current_path_to_directory, zip_file, current_arcname)

def get_all_job_result_ids(user_id):
    """Return list of the identifieres of all job reults.

    The list is sorted in descending according to execution date of the jobs.

    @param user_id: identifier of the user owning the jobs,
    that produce the results

    @return: list of identifiers (integer numbers)
    of the results owned by the given user
    """
    query = """SELECT expJOBRESULT.id
                FROM expJOBRESULT
                INNER JOIN user_expJOB
                ON expJOBRESULT.id_expJOB = user_expJOB.id_expJOB
                WHERE id_user = %s
                ORDER BY execution_time DESC
            """
    query_parameters = (user_id, )
    query_result = run_sql(query, query_parameters)

    all_job_ids = []
    for (current_job_result_id, ) in query_result:
        all_job_ids.append(current_job_result_id)

    return all_job_ids

def get_job_results(result_identifiers):
    """Return a list of JobResult objects corresponding to identifiers
    given as a parameter

    @return: List of JobResult objects

    The order of the results in the list is the same as their
    corresponding identifiers in the input list
    """
    job_results = []

    for job_result_id in result_identifiers:
        current_result = get_job_result(job_result_id)
        job_results.append(current_result)

    return job_results

def get_job_result(job_result_id):
    """Loads job result from the database.

    @param job_result_id: identifier of the job result

    @return: JobResult object containing information about the job result
    or None if job result with this identifier does not exist"""

    if not _exist_job_result(job_result_id):
        return None

    query = """SELECT id,
                        id_expJOB,
                        DATE_FORMAT(execution_time,'%%Y-%%m-%%d %%H:%%i:%%s'),
                        status,
                        status_message
                        FROM expJOBRESULT WHERE id=%s"""
    query_result = run_sql(query, (job_result_id,))

    (id, job_id, execution_date_time, status, status_message) = query_result[0]

    job = get_job(job_id)
    query_results = _get_query_results_for_job_result(id)

    job_result = JobResult(job,
                           query_results,
                           convert_datetext_to_datestruct(execution_date_time),
                           id,
                           status,
                           status_message)
    return job_result

def _get_query_results_for_job_result(job_result_id):
    """Retrieves all query results owned by a given job result.

    @param job_result_id: identifier of the job result that owns the queryes.

    @return: list of QueryReusult objects
    contaning information about the query results
    """
    query = """SELECT expQUERYRESULT.id,
                        expQUERYRESULT.id_expQUERY,
                        expQUERYRESULT.result,
                        expQUERYRESULT.status,
                        expQUERYRESULT.status_message
            FROM expQUERYRESULT
            INNER JOIN expJOBRESULT_expQUERYRESULT
            ON expQUERYRESULT.id = expJOBRESULT_expQUERYRESULT.id_expQUERYRESULT
            WHERE expJOBRESULT_expQUERYRESULT.id_expJOBRESULT = %s
            """
    query_parameters = (job_result_id, )

    query_result = run_sql(query, query_parameters)
    print(query_result)

    all_query_results = []

    for (query_result_id, query_id, result, status, status_message) in query_result:
        current_query = get_query(query_id)
        current_result = QueryResult(current_query,
                                     result,
                                     query_result_id,
                                     status,
                                     status_message)
        all_query_results.append(current_result)

    return all_query_results

def is_user_owner_of_job(user_id, job_id):
    """Checks if a user is owner of a job

    @param user_id: identifier of the user
    @param job_id: identifier of the job

    @return: True if user is owner of the job, otherwise return False
    """
    query = """SELECT COUNT(id_user)
                        FROM user_expJOB
                        WHERE id_user=%s and id_expJOB=%s"""
    result = run_sql(query, (user_id, job_id))

    if 1 == result[0][0]:
        return True

    return False

def is_user_owner_of_job_result(user_id, job_result_id):
    """Checks if a user is owner of a job result

    @param user_id: identifier of the user
    @param job_result_id: identifier of the job result

    @return: True if user is owner of the job result, otherwise return False
    """
    job_result = get_job_result(job_result_id)

    if None == job_result:
        return False

    job_id = job_result.get_job().get_id()

    return is_user_owner_of_job(user_id, job_id)

def is_user_owner_of_query(user_id, query_id):
    """Checks if a user is owner of a query

    @param user_id: identifier of the user
    @param job_query_id: identifier of the query

    @return: True if user is owner of the query, otherwise return False
    """
    query = """SELECT COUNT(user_expJOB.id_user)
                FROM user_expJOB
                INNER JOIN expJOB_expQUERY
                ON user_expJOB.id_expJOB = expJOB_expQUERY.id_expJOB
                WHERE id_user = %s AND expJOB_expQUERY.id_expQUERY = %s
            """
    result = run_sql(query, (user_id, query_id))

    if 1 == result[0][0]:
        return True

    return False

def _insert_query_result(query_result, job_result_id):
    """Inserts new query result into database.

    @param query_result: QueryResult object containing
    information about the query result
    @param job_result_id: Identifier of the job result owning the query result

    @return: Returns the identifier of the query result"""

    # WE always attach a query to a job. If the given job id
    # does not exists it is an error
    if not _exist_job_result(job_result_id):
        raise FieldExporterDBException("There is no job result with id %s"
                                       %(job_result_id,))

    query_id = query_result.get_query().get_id()
    result = query_result.get_result()
    status = query_result.get_status()
    status_message = query_result.get_status_message()

    query_result_id = run_sql("""INSERT INTO expQUERYRESULT(id_expQUERY,
                                           result,
                                           status,
                                           status_message)
                        VALUES(%s, %s, %s, %s)""",
                        (query_id,
                         result,
                         status,
                         status_message
                         ))

    run_sql("""INSERT INTO expJOBRESULT_expQUERYRESULT(id_expJOBRESULT,
                                           id_expQUERYRESULT)
                        VALUES(%s, %s)""",
                        (job_result_id,
                         query_result_id
                        ))

    return query_result_id

def _exist_job_result(job_result_id):
    """Checks if a job result exist in the database

    @param job_result_id: identifier of the job result

    @return: True if the job result exists, otherwise return False
    """

    query = """SELECT COUNT(id) FROM expJOBRESULT WHERE id=%s"""

    result = run_sql(query, (job_result_id, ))

    if 1 == result[0][0]:
        return True

    return False
