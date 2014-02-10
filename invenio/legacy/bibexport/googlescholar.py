# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2008, 2010, 2011 CERN.
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

"""
BibExport plugin implementing 'googlescholar' exporting method.

The main function is run_export_method(jobname) defined at the end.
This is what BibExport daemon calls for all the export jobs that use
this exporting method.

The Google Scholar exporting method answers this use case: every first
of the month, please export all records modified during the last month
and matching these search criteria in an NLM format in such a way that
the output is split into files containing not more than 1000 records
and compressed via gzip and placed in this place from where Google
Scholar would fetch them. The output files would be organized like
this:

* all exportable records:

    /export/googlescholar/all-index.html   - links to parts below
    /export/googlescholar/all-part1.xml.gz - first batch of 1000 records
    /export/googlescholar/all-part2.xml.gz - second batch of 1000 records
    ...
    /export/googlescholar/all-partM.xml.gz - last batch of 1000 records

* records modified in the last month:

    /export/googlescholar/lastmonth-index.html   - links to parts below
    /export/googlescholar/lastmonth-part1.xml.gz - first batch of 1000 records
    /export/googlescholar/lastmonth-part2.xml.gz - second batch of 1000 records
    ...
    /export/googlescholar/lastmonth-partN.xml.gz - last batch of 1000 records
"""

from invenio.config import CFG_WEBDIR, CFG_CERN_SITE
from invenio.legacy.bibsched.bibtask import write_message
from invenio.legacy.search_engine import perform_request_search, print_record
import os
import gzip
import datetime

def run_export_method(jobname):
    """Main function, reading params and running the task."""
    # FIXME: read jobname's cfg file to detect collection and fulltext status arguments
    write_message("bibexport_sitemap: job %s started." % jobname)

    try:
        output_directory = CFG_WEBDIR + os.sep + "export" + os.sep + "googlescholar"
        exporter = GoogleScholarExporter(output_directory)
        exporter.export()
    except GoogleScholarExportException, ex:
        write_message("%s Exception: %s" %(ex.get_error_message(), ex.get_inner_exception()))

    write_message("bibexport_sitemap: job %s finished." % jobname)

class GoogleScholarExporter:
    """Export data for google scholar"""

    _output_directory = ""
    _records_with_fulltext_only = True
    #FIXME: Read collections from configuration file
    _collections = ["Theses"]
    if CFG_CERN_SITE:
        _collections = ["CERN Theses"]

    def __init__(self, output_directory):
        """Constructor of GoogleScholarExporter

        output_directory - directory where files will be placed
        """

        self.set_output_directory(output_directory)

    def export(self):
        """Export all records and records modified last month"""
        LAST_MONTH_FILE_NAME_PATTERN = "lastmonth"
        ALL_MONTH_FILE_NAME_PATTERN = "all"
        SPLIT_BY_RECORDS = 1000

        # Export records modified last month
        records = self._get_records_modified_last_month()
        self._delete_files(self._output_directory, LAST_MONTH_FILE_NAME_PATTERN)
        self._split_records_into_files(records, SPLIT_BY_RECORDS, LAST_MONTH_FILE_NAME_PATTERN, self._output_directory)

        # Export all records
        all_records = self._get_all_records()
        self._delete_files(self._output_directory, ALL_MONTH_FILE_NAME_PATTERN)
        self._split_records_into_files(all_records, SPLIT_BY_RECORDS, ALL_MONTH_FILE_NAME_PATTERN, self._output_directory)

    def set_output_directory(self, path_to_directory):
        """Check if directory exists. If it does not exists it creates it."""

        directory = path_to_directory
        # remove the slash from the end of the path if exists
        if directory[-1] == os.sep:
            directory = directory[:-1]

        # if directory does not exists then create it
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except(IOError, OSError), exception:
                self._report_error("Directory %s does not exist and cannot be ctreated." % (directory, ), exception)

        # if it is not path to a directory report an error
        if not os.path.isdir(directory):
            self._report_error("%s is not a directory." % (directory, ))
            return

        self._output_directory = directory

    def _get_records_modified_last_month(self):
        """Returns all records modified last month and matching the criteria."""
        current_date = datetime.date.today()
        one_month_ago = current_date - datetime.timedelta(days = 31)

        #FIXME: Return only records with full texts available for Google Scholar
        #FIXME: There is a problem with searching in modification date. It searches only in creation date
        return perform_request_search(dt="m", c = self._collections, d1y = one_month_ago.year, d1m = one_month_ago.month, d1d = one_month_ago.day)

    def _get_all_records(self):
        """Return all records matching the criteria no matter of their modification date."""
        #FIXME: Return only records with full texts available for Google Scholar
        return perform_request_search(c = self._collections)

    def _split_records_into_files(self, records, max_records_per_file, file_name_pattern, output_directory):
        """Split and save records into files containing not more than max_records_per_file records.

        records - list of record numbers

        max_records_per_file - the maximum number of records per file

        file_name_pattern - the pattern used to name the files. Filenames will start with this
        pattern.

        output_directory - directory where all the files will be placed
        """
        file_number = 1
        file_name = self._get_part_file_name(file_name_pattern, file_number)
        begin = 0
        number_of_records = len(records)

        if 0 == number_of_records:
            return

        for end in xrange(max_records_per_file, number_of_records, max_records_per_file):
            self._save_records_into_file(records[begin:end], file_name, output_directory)
            begin = end
            file_number = file_number + 1
            file_name = self._get_part_file_name(file_name_pattern, file_number)

        if(begin != number_of_records):
            self._save_records_into_file(records[begin:number_of_records], file_name, output_directory)

        self._create_index_file(file_number, file_name_pattern, output_directory)

    def _get_part_file_name(self, file_name_pattern, file_number):
        """Returns name of the file containing part of the records

        file_name_pattern - the pattetn used to create the filename

        file_number - the number of the file in the sequence of files

        The result is filename like lastmonth-part2.xml.gz
        where lastmonth is the file_name_pattern and 2 is the file_number
        """
        file_name = "%s-part%d.xml.gz" % (file_name_pattern, file_number)

        return file_name

    def _create_index_file(self, number_of_files, file_name_pattern, output_directory):
        """Creates HTML file containing links to all files containing records"""

        try:
            index_file = open(output_directory + os.sep +file_name_pattern+"-index.html", "w")
            index_file.write("<html><body>\n")

            for file_number in xrange(1, number_of_files + 1):
                file_name = self._get_part_file_name(file_name_pattern, file_number)
                index_file.write('<a href="%s">%s</a><br>\n' % (file_name, file_name))

            index_file.write("</body></html>\n")
        except (IOError, OSError), exception:
            self._report_error("Failed to create index file.", exception)

        if index_file is not None:
            index_file.close()

    def _save_records_into_file(self, records, file_name, output_directory):
        """Save all the records into file in proper format (currently
        National Library of Medicine XML).

        file_name - the name of the file where records will be saved

        output_directory - directory where the file will be placed"""

        output_file = self._open_output_file(file_name, output_directory)
        self._write_to_output_file(output_file, "<articles>\n")

        for record in records:
            nlm_xml = self._get_record_NLM_XML(record)
            output_file.write(nlm_xml)

        self._write_to_output_file(output_file, "\n</articles>")
        self._close_output_file(output_file)

    def _open_output_file(self, file_name, output_directory):
        """Opens new file for writing.

        file_name - the name of the file without the extention.

        output_directory - the directory where file will be created"""

        path = output_directory + os.sep + file_name

        try:
            output_file = gzip.GzipFile(filename = path, mode = "w")
            return output_file
        except (IOError, OSError), exception:
            self._report_error("Failed to open file file %s." % (path, ), exception)
            return None

    def _close_output_file(self, output_file):
        """Closes the file"""
        if output_file is None:
            return
        output_file.close()

    def _write_to_output_file(self, output_file, text_to_write):
        """"Wirtes a the text passed as a parameter to file"""
        try:
            output_file.write(text_to_write)
        except (IOError, OSError), exception:
            self._report_error("Failed to write to file " + output_file.name, exception)

    def _get_record_NLM_XML(self, record):
        """Returns the record in National Library of Medicine XML format."""
        return print_record(record, format='xn')

    def _delete_files(self, path_to_directory, name_pattern):
        """Deletes files with file name starting with name_pattern
        from directory specified by path_to_directory"""

        files = os.listdir(path_to_directory)

        for current_file in files:
            if current_file.startswith(name_pattern):
                path_to_file = path_to_directory + os.sep + current_file
                os.remove(path_to_file)

    def _report_error(self, error_message, exception = None):
        """Reprts an error during exprotring"""
        raise GoogleScholarExportException(error_message, exception)

class GoogleScholarExportException(Exception):
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
