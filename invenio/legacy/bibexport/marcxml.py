# -*- coding: utf-8 -*-
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

"""
BibExport plugin implementing MARCXML exporting method.

The main function is run_export_method(jobname) defined at the end.
This is what BibExport daemon calls for all the export jobs that use
this exporting method.

The MARCXML exporting method export as MARCXML all the records
matching a particular search query, zip them and move them to the
requested folder. The output of this exporting method is similar to
what one would get by listing the records in MARCXML from the web
search interface. The exporter also export all the records modified
in the last month.

* all exportable records:
    /export/marcxml/all_"export_name".xml.gz - where "export_name" is the name specified in the config

* records modified in the last month:

    /export/marcxml/lastmonth_"export_name".xml.gz - where "export_name" is the name specified in the config

"""

from invenio.config import CFG_WEBDIR, CFG_ETCDIR
from invenio.legacy.bibsched.bibtask import write_message
from invenio.legacy.search_engine import perform_request_search, print_record
from ConfigParser import ConfigParser
from six import iteritems
import os
import gzip
import datetime

def run_export_method(jobname):
    """Main function, reading params and running the task."""
    # read jobname's cfg file to detect export criterias
    jobconf = ConfigParser()
    jobconffile = CFG_ETCDIR + os.sep + 'bibexport' + os.sep + jobname + '.cfg'
    if not os.path.exists(jobconffile):
        write_message("ERROR: cannot find config file %s." % jobconffile)
        return None
    jobconf.read(jobconffile)
    export_criterias = dict(jobconf.items('export_criterias'))

    write_message("bibexport_marcxml: job %s started." % jobname)

    try:
        output_directory = CFG_WEBDIR + os.sep + "export" + os.sep + "marcxml"
        exporter = MARCXMLExporter(output_directory, export_criterias)
        exporter.export()
    except MARCXMLExportException as ex:
        write_message("%s Exception: %s" %(ex.get_error_message(), ex.get_inner_exception()))

    write_message("bibexport_marcxml: job %s finished." % jobname)

class MARCXMLExporter:
    """Export data to MARCXML"""

    _output_directory = ""
    _export_criterias = {}

    def __init__(self, output_directory, export_criterias):
        """Constructor of MARCXMLExporter

        @param output_directory: directory where files will be placed
        @param export_criterias: dictionary of names and associated search patterns
        """

        self.set_output_directory(output_directory)
        self._export_criterias = export_criterias

    def export(self):
        """Export all records and records modified last month"""
        for export_name, export_pattern in iteritems(self._export_criterias):
            LAST_MONTH_FILE_NAME = "lastmonth_" + export_name + '.xml'
            ALL_MONTH_FILE_NAME = "all_" + export_name + '.xml'

            # Export records modified last month
            records = self._get_records_modified_last_month(export_name, export_pattern)
            self._delete_files(self._output_directory, LAST_MONTH_FILE_NAME)
            #self._split_records_into_files(records, SPLIT_BY_RECORDS, LAST_MONTH_FILE_NAME_PATTERN, self._output_directory)
            self._save_records_into_file(records, LAST_MONTH_FILE_NAME, self._output_directory)

            # Export all records
            all_records = self._get_all_records(export_name, export_pattern)
            self._delete_files(self._output_directory, ALL_MONTH_FILE_NAME)
            self._save_records_into_file(all_records, ALL_MONTH_FILE_NAME, self._output_directory)

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
                self._report_error("Directory %s does not exist and cannot be created." % (directory, ), exception)

        # if it is not path to a directory report an error
        if not os.path.isdir(directory):
            self._report_error("%s is not a directory." % (directory, ))
            return

        self._output_directory = directory

    def _get_records_modified_last_month(self, export_name, export_pattern):
        """Returns all records modified last month and matching the criteria."""
        current_date = datetime.date.today()
        one_month_ago = current_date - datetime.timedelta(days = 31)

        return perform_request_search(dt="m", p=export_pattern, d1y = one_month_ago.year, d1m = one_month_ago.month, d1d = one_month_ago.day)

    def _get_all_records(self, export_name, export_pattern):
        """Return all records matching the criteria no matter of their modification date."""
        return perform_request_search(p=export_pattern)

    def _save_records_into_file(self, records, file_name, output_directory):
        """Save all the records into file in MARCXML

        file_name - the name of the file where records will be saved

        output_directory - directory where the file will be placed"""

        output_file = self._open_output_file(file_name, output_directory)
        self._write_to_output_file(output_file,
                                   '<?xml version="1.0" encoding="UTF-8"?>\n<collection xmlns="http://www.loc.gov/MARC21/slim">\n')

        for record in records:
            marcxml = self._get_record_MARCXML(record)
            output_file.write(marcxml)

        self._write_to_output_file(output_file, "\n</collection>")
        self._close_output_file(output_file)

    def _open_output_file(self, file_name, output_directory):
        """Opens new file for writing.

        file_name - the name of the file without the extention.

        output_directory - the directory where file will be created"""

        path = output_directory + os.sep + file_name + '.gz'

        try:
            output_file = gzip.GzipFile(filename = path, mode = "w")
            return output_file
        except (IOError, OSError) as exception:
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
        except (IOError, OSError) as exception:
            self._report_error("Failed to write to file " + output_file.name, exception)

    def _get_record_MARCXML(self, record):
        """Returns the record in MARCXML format."""
        return print_record(record, format='xm')

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
        raise MARCXMLExportException(error_message, exception)

class MARCXMLExportException(Exception):
    """Exception indicating an error when exporting to MARCXML."""

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
