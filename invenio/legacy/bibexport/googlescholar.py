# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2008, 2010, 2011, 2014 CERN.
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
BibExport plugin implementing 'googlescholar' exporting method.

The main function is run_export_method(jobname) defined at the end.
This is what BibExport daemon calls for all the export jobs that use
this exporting method.

The Google Scholar exporting method produces a sitemap of all the
records matching the collections defined in "googlescholar.cfg", as
well as a second sitemap that list all records modified in the last
months in these collections. The produced files contain at most
MAX_RECORDS records and weight at most MAX_SIZE bytes. The output
files would be organized like this:

* all exportable records:

    /export/googlescholar/all-index.xml.gz   - links to parts below
    /export/googlescholar/all-part1.xml.gz - first batch of 1000 records
    /export/googlescholar/all-part2.xml.gz - second batch of 1000 records
    ...
    /export/googlescholar/all-partM.xml.gz - last batch of 1000 records

* records modified in the last month:

    /export/googlescholar/lastmonth-index.xml.gz   - links to parts below
    /export/googlescholar/lastmonth-part1.xml.gz - first batch of 1000 records
    /export/googlescholar/lastmonth-part2.xml.gz - second batch of 1000 records
    ...
    /export/googlescholar/lastmonth-partN.xml.gz - last batch of 1000 records
"""
import os
import datetime

from invenio.config import \
     CFG_WEBDIR, \
     CFG_SITE_URL, \
     CFG_SITE_RECORD
from invenio.legacy.bibsched.bibtask import write_message, task_update_progress, task_sleep_now_if_required
from invenio.legacy.search_engine import get_collection_reclist, get_all_restricted_recids
from intbitset import intbitset
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibexport.sitemap import \
     get_config_parameter, \
     SitemapWriter, \
     SitemapIndexWriter, \
     get_all_public_records


DEFAULT_PRIORITY_RECORDS = 0.8
DEFAULT_CHANGEFREQ_RECORDS = 'weekly'

LAST_MONTH_FILE_NAME_PATTERN = "lastmonth"
ALL_MONTH_FILE_NAME_PATTERN = "all"

MAX_RECORDS = 50000
MAX_SIZE = 10000000

def run_export_method(jobname):
    """Main function, reading params and running the task."""
    write_message("bibexport_sitemap: job %s started." % jobname)

    collections = get_config_parameter(jobname=jobname, parameter_name="collection", is_parameter_collection = True)
    output_directory = CFG_WEBDIR + os.sep + "export" + os.sep + "googlescholar"

    try:
        init_output_directory(output_directory)
    except GoogleScholarExportException, ex:
        write_message("%s Exception: %s" %(ex.get_error_message(), ex.get_inner_exception()))
        return

    # Export records modified last month
    records = get_all_public_records_modified_last_month(collections)
    _delete_files(output_directory, LAST_MONTH_FILE_NAME_PATTERN)
    generate_sitemaps_index(records, output_directory, LAST_MONTH_FILE_NAME_PATTERN)

    # Export all records
    all_records = get_all_public_records(collections)
    _delete_files(output_directory, ALL_MONTH_FILE_NAME_PATTERN)
    generate_sitemaps_index(all_records, output_directory, ALL_MONTH_FILE_NAME_PATTERN)

    write_message("bibexport_sitemap: job %s finished." % jobname)

def generate_sitemaps_index(records, output_directory, sitemap_name):
    """main function. Generates the sitemap index and the sitemaps

    @param records: the list of (recid, modification_date) tuples to process
    @param output_directory: directory where to store the sitemaps
    @param sitemap_name: the name (prefix) of the sitemap files(s)
    """
    write_message("Generating all sitemaps...")
    sitemap_index_writer = SitemapIndexWriter(os.path.join(output_directory, sitemap_name + '-index.xml.gz'))
    generate_sitemaps(sitemap_index_writer, records, output_directory, sitemap_name)

def generate_sitemaps(sitemap_index_writer, records, output_directory, sitemap_name):
    """
    Generate sitemaps themselves.

    @param sitemap_index_writer: the instance of SitemapIndexWriter that will refer to these sitemaps
    @param records: the list of (recid, modification_date) tuples to process
    @param output_directory: directory where to store the sitemaps
    @param sitemap_name: the name (prefix) of the sitemap files(s)
    """
    sitemap_id = 1
    writer = SitemapWriter(sitemap_id, output_directory, sitemap_name)
    sitemap_index_writer.add_url(writer.get_sitemap_url())
    nb_urls = 0
    write_message("... Getting sitemap '%s'..." % sitemap_name)
    write_message("... Generating urls for %s records..." % len(records))
    task_sleep_now_if_required(can_stop_too=True)
    for i, (recid, lastmod) in enumerate(records):
        if nb_urls % 100 == 0 and (writer.get_size() >= MAX_SIZE or nb_urls >= MAX_RECORDS):
            sitemap_id += 1
            writer = SitemapWriter(sitemap_id, output_directory, sitemap_name)
            sitemap_index_writer.add_url(writer.get_sitemap_url())
        nb_urls = writer.add_url(CFG_SITE_URL + '/%s/%s' % (CFG_SITE_RECORD, recid),
                                lastmod = lastmod,
                                changefreq = DEFAULT_CHANGEFREQ_RECORDS,
                                priority = DEFAULT_PRIORITY_RECORDS)
        if i % 100 == 0:
            task_update_progress("Google Scholar sitemap '%s' for recid %s/%s" % (sitemap_name, i + 1, len(records)))
            task_sleep_now_if_required(can_stop_too=True)

def init_output_directory(path_to_directory):
    """Check if directory exists. If it does not exists it creates it."""
    directory = path_to_directory
    # remove the slash from the end of the path if exists
    if directory[-1] == os.sep:
        directory = directory[:-1]

    # if directory does not exists then create it
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except(IOError, OSError) as exception:
            raise GoogleScholarExportException("Directory %s does not exist and cannot be ctreated." % (directory, ), exception)

    # if it is not path to a directory report an error
    if not os.path.isdir(directory):
        raise GoogleScholarExportException("%s is not a directory." % (directory, ))

def _delete_files(path_to_directory, name_pattern):
    """Deletes files with file name starting with name_pattern
    from directory specified by path_to_directory"""
    try:
        files = os.listdir(path_to_directory)
    except OSError:
        return

    for current_file in files:
        if current_file.startswith(name_pattern):
            path_to_file = path_to_directory + os.sep + current_file
            os.remove(path_to_file)

def get_all_public_records_modified_last_month(collections):
    """ Get all records which exist (i.e. not suppressed ones) and are in
    accessible collection.
    returns list of (recid, last_modification) tuples
    """
    all_restricted_recids = get_all_restricted_recids()
    current_date = datetime.date.today()
    one_month_ago = current_date - datetime.timedelta(days = 31)
    recids = intbitset()
    for collection in collections:
        recids += get_collection_reclist(collection)
    recids = recids.difference(all_restricted_recids)
    query = 'SELECT id, modification_date FROM bibrec WHERE modification_date > %s'
    res = run_sql(query, (one_month_ago,))
    return [(recid, lastmod) for (recid, lastmod) in res if recid in recids]

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
