# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013, 2014, 2015 CERN.
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

__revision__ = "$Id$"
__lastupdated__ = "$Date$"

import os
import time
import re
import datetime
from six.moves import cPickle
import calendar
from datetime import timedelta
from urllib import quote

from invenio.legacy import template
from invenio.config import \
     CFG_WEBDIR, \
     CFG_TMPDIR, \
     CFG_SITE_URL, \
     CFG_SITE_LANG, \
     CFG_WEBSTAT_BIBCIRCULATION_START_YEAR
from invenio.legacy.webstat.config import CFG_WEBSTAT_CONFIG_PATH
from invenio.legacy.bibindex.engine_utils import get_all_indexes
from invenio.modules.indexer.tokenizers.BibIndexJournalTokenizer import CFG_JOURNAL_TAG
from invenio.legacy.search_engine import get_coll_i18nname, \
    wash_index_term
from invenio.legacy.dbquery import run_sql, wash_table_column_name
from invenio.legacy.bibsched.cli import is_task_scheduled, \
    get_task_ids_by_descending_date, \
    get_task_options

# Imports handling key events and error log
from invenio.legacy.webstat.engine import get_keyevent_trend_collection_population, \
    get_keyevent_trend_new_records, \
    get_keyevent_trend_search_frequency, \
    get_keyevent_trend_search_type_distribution, \
    get_keyevent_trend_download_frequency, \
    get_keyevent_trend_comments_frequency, \
    get_keyevent_trend_number_of_loans, \
    get_keyevent_trend_web_submissions, \
    get_keyevent_snapshot_apache_processes, \
    get_keyevent_snapshot_bibsched_status, \
    get_keyevent_snapshot_uptime_cmd, \
    get_keyevent_snapshot_sessions, \
    get_keyevent_bibcirculation_report, \
    get_keyevent_loan_statistics, \
    get_keyevent_loan_lists, \
    get_keyevent_renewals_lists, \
    get_keyevent_returns_table, \
    get_keyevent_trend_returns_percentage, \
    get_keyevent_ill_requests_statistics, \
    get_keyevent_ill_requests_lists, \
    get_keyevent_trend_satisfied_ill_requests_percentage, \
    get_keyevent_items_statistics, \
    get_keyevent_items_lists, \
    get_keyevent_loan_request_statistics, \
    get_keyevent_loan_request_lists, \
    get_keyevent_user_statistics, \
    get_keyevent_user_lists, \
    _get_doctypes, \
    _get_item_statuses, \
    _get_item_doctype, \
    _get_request_statuses, \
    _get_libraries, \
    _get_loan_periods, \
    get_invenio_error_log_ranking, \
    get_invenio_last_n_errors, \
    update_error_log_analyzer, \
    get_apache_error_log_ranking, \
    get_last_updates, \
    get_list_link, \
    get_general_status, \
    get_ingestion_matching_records, \
    get_record_ingestion_status, \
    get_specific_ingestion_status, \
    get_title_ingestion, \
    get_record_last_modification

# Imports handling custom events
from invenio.legacy.webstat.engine import get_customevent_table, \
    get_customevent_trend, \
    get_customevent_dump

# Imports handling custom report
from invenio.legacy.webstat.engine import get_custom_summary_data, \
    _get_tag_name, \
    create_custom_summary_graph

# Imports for handling outputting
from invenio.legacy.webstat.engine import create_graph_trend, \
    create_graph_dump, \
    create_graph_table, \
    get_numeric_stats

# Imports for handling exports
from invenio.legacy.webstat.engine import export_to_python, \
    export_to_csv, \
    export_to_file

from sqlalchemy.exc import ProgrammingError

TEMPLATES = template.load('webstat')

# Constants
WEBSTAT_CACHE_INTERVAL = 600 # Seconds, cache_* functions not affected by this.
                             # Also not taking into account if BibSched has
                             # webstatadmin process.
WEBSTAT_RAWDATA_DIRECTORY = CFG_TMPDIR + "/"
WEBSTAT_GRAPH_DIRECTORY = CFG_WEBDIR + "/img/"

TYPE_REPOSITORY = [('gnuplot', 'Image - Gnuplot'),
                   ('asciiart', 'Image - ASCII art'),
                   ('flot', 'Image - Flot'),
                   ('asciidump', 'Image - ASCII dump'),
                   ('python', 'Data - Python code', export_to_python),
                   ('csv', 'Data - CSV', export_to_csv)]


def get_collection_list_plus_all():
    """ Return all the collection names plus the name All"""
    coll = [('All', 'All')]
    res = run_sql("SELECT name FROM collection WHERE (dbquery IS NULL OR dbquery \
NOT LIKE 'hostedcollection:%') ORDER BY name ASC")
    for c_name in res:
        # make a nice printable name (e.g. truncate c_printable for
        # long collection names in given language):
        c_printable_fullname = get_coll_i18nname(c_name[0], CFG_SITE_LANG, False)
        c_printable = wash_index_term(c_printable_fullname, 30, False)
        if c_printable != c_printable_fullname:
            c_printable = c_printable + "..."
        coll.append([c_name[0], c_printable])
    return coll

# Key event repository, add an entry here to support new key measures.
KEYEVENT_REPOSITORY = {'collection population':
                          {'fullname': 'Collection population',
                            'specificname':
                                   'Population in collection "%(collection)s"',
                            'description':
                                   ('The collection population is the number of \
documents existing in the selected collection.', ),
                            'gatherer':
                                   get_keyevent_trend_collection_population,
                            'extraparams': {'collection': ('combobox', 'Collection',
                                   get_collection_list_plus_all)},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(collection)s_%(timespan)s',
                            'ylabel': 'Number of records',
                            'multiple': None,
                            'output': 'Graph'},
                        'new records':
                          {'fullname': 'New records',
                            'specificname':
                                   'New records in collection "%(collection)s"',
                            'description':
                                   ('The graph shows the new documents created in \
the selected collection and time span.', ),
                            'gatherer':
                                   get_keyevent_trend_new_records,
                            'extraparams': {'collection': ('combobox', 'Collection',
                                   get_collection_list_plus_all)},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(collection)s_%(timespan)s',
                            'ylabel': 'Number of records',
                            'multiple': None,
                            'output': 'Graph'},
                        'search frequency':
                          {'fullname': 'Search frequency',
                            'specificname': 'Search frequency',
                            'description':
                                   ('The search frequency is the number of searches \
performed in a specific time span.', ),
                            'gatherer': get_keyevent_trend_search_frequency,
                            'extraparams': {},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(timespan)s',
                            'ylabel': 'Number of searches',
                            'multiple': None,
                            'output': 'Graph'},
                        'search type distribution':
                          {'fullname': 'Search type distribution',
                            'specificname': 'Search type distribution',
                            'description':
                                   ('The search type distribution shows both the \
number of simple searches and the number of advanced searches in the same graph.', ),
                            'gatherer':
                                   get_keyevent_trend_search_type_distribution,
                            'extraparams': {},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(timespan)s',
                            'ylabel': 'Number of searches',
                            'multiple': ['Simple searches',
                                         'Advanced searches'],
                            'output': 'Graph'},
                        'download frequency':
                          {'fullname': 'Download frequency',
                            'specificname': 'Download frequency in collection "%(collection)s"',
                            'description':
                                   ('The download frequency is the number of fulltext \
downloads of the documents.', ),
                            'gatherer': get_keyevent_trend_download_frequency,
                            'extraparams': {'collection': ('combobox', 'Collection',
                                                    get_collection_list_plus_all)},
                            'cachefilename': 'webstat_%(event_id)s_%(collection)s_%(timespan)s',
                            'ylabel': 'Number of downloads',
                            'multiple': None,
                            'output': 'Graph'},
                         'comments frequency':
                          {'fullname': 'Comments frequency',
                            'specificname': 'Comments frequency in collection "%(collection)s"',
                            'description':
                                   ('The comments frequency is the amount of comments written \
for all the documents.', ),
                            'gatherer': get_keyevent_trend_comments_frequency,
                            'extraparams': {'collection': ('combobox', 'Collection',
                                                    get_collection_list_plus_all)},
                            'cachefilename': 'webstat_%(event_id)s_%(collection)s_%(timespan)s',
                            'ylabel': 'Number of comments',
                            'multiple': None,
                            'output': 'Graph'},
                        'number of loans':
                          {'fullname': 'Number of circulation loans',
                            'specificname': 'Number of circulation loans',
                            'description':
                                   ('The number of loans shows the total number of records loaned \
 over a time span', ),
                            'gatherer': get_keyevent_trend_number_of_loans,
                            'extraparams': {},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(timespan)s',
                            'ylabel': 'Number of loans',
                            'multiple': None,
                            'output': 'Graph',
                            'type': 'bibcirculation'},
                        'web submissions':
                          {'fullname': 'Number of web submissions',
                            'specificname':
                                   'Number of web submissions of "%(doctype)s"',
                            'description':
                                   ("The web submissions are the number of submitted \
documents using the web form.", ),
                            'gatherer': get_keyevent_trend_web_submissions,
                            'extraparams': {
                                'doctype': ('combobox', 'Type of document', _get_doctypes)},
                            'cachefilename':
                                'webstat_%(event_id)s_%(doctype)s_%(timespan)s',
                            'ylabel': 'Web submissions',
                            'multiple': None,
                            'output': 'Graph'},
                        'loans statistics':
                          {'fullname': 'Circulation loans statistics',
                            'specificname': 'Circulation loans statistics',
                            'description':
                                   ('The loan statistics consist on different numbers \
related to the records loaned. It is important to see the difference between document \
and item. The item is the physical representation of a document (like every copy of a \
book). There may be more items than documents, but never the opposite.', ),
                            'gatherer':
                                   get_keyevent_loan_statistics,
                            'extraparams': {
                                'udc': ('textbox', 'UDC'),
                                'item_status': ('combobox', 'Item status', _get_item_statuses),
                                'publication_date': ('textbox', 'Publication date'),
                                'creation_date': ('textbox', 'Creation date')},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(udc)s_%(item_status)s_%(publication_date)s' + \
                                '_%(creation_date)s_%(timespan)s',
                            'rows': ['Number of documents loaned',
                                         'Number of items loaned on the total number of items (%)',
                                         'Number of items never loaned on the \
                                         total number of items (%)',
                                         'Average time between the date of \
the record creation and the date of the first loan (in days)'],
                            'output': 'Table',
                            'type': 'bibcirculation'},
                         'loans lists':
                           {'fullname': 'Circulation loans lists',
                            'specificname': 'Circulation loans lists',
                            'description':
                                   ('The loan lists show the most loaned and the never loaned \
records in a time span. The most loaned record are calculated as the number of loans by copy.', ),
                            'gatherer':
                                   get_keyevent_loan_lists,
                            'extraparams': {
                                'udc': ('textbox', 'UDC'),
                                'loan_period': ('combobox', 'Loan period', _get_loan_periods),
                                'max_loans': ('textbox', 'Maximum number of loans'),
                                'min_loans': ('textbox', 'Minimum number of loans'),
                                'publication_date': ('textbox', 'Publication date'),
                                'creation_date': ('textbox', 'Creation date')},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(udc)s_%(loan_period)s' + \
                                 '_%(min_loans)s_%(max_loans)s_%(publication_date)s_' + \
                                 '%(creation_date)s_%(timespan)s',
                            'rows': [],
                            'output': 'List',
                            'type': 'bibcirculation'},
                          'renewals':
                           {'fullname': 'Circulation renewals',
                            'specificname': 'Circulation renewals',
                            'description':
                                   ('Here the list of most renewed items stored is shown \
by decreasing order', ),
                            'gatherer':
                                   get_keyevent_renewals_lists,
                            'extraparams': {
                                'udc': ('textbox', 'UDC')},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(udc)s_%(timespan)s',
                            'rows': [],
                            'output': 'List',
                            'type': 'bibcirculation'},
                          'number returns':
                           {'fullname': 'Number of circulation overdue returns',
                            'specificname': 'Number of circulation overdue returns',
                            'description':
                                   ('The number of overdue returns is the number of loans \
that has not been returned by the due date (they may have been returned after or never).', ),
                            'gatherer':
                                   get_keyevent_returns_table,
                            'extraparams': {},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(timespan)s',
                            'rows': ['Number of overdue returns'],
                            'output': 'Table',
                            'type': 'bibcirculation'},
                          'percentage returns':
                           {'fullname': 'Percentage of circulation overdue returns',
                            'specificname': 'Percentage of overdue returns',
                            'description':
                                   ('This graphs shows both the overdue returns and the total \
of returns.', ),
                            'gatherer':
                                   get_keyevent_trend_returns_percentage,
                            'extraparams': {},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(timespan)s',
                            'ylabel': 'Percentage of overdue returns',
                            'multiple': ['Overdue returns',
                                         'Total returns'],
                            'output': 'Graph',
                            'type': 'bibcirculation'},
                        'ill requests statistics':
                          {'fullname': 'Circulation ILL Requests statistics',
                            'specificname': 'Circulation ILL Requests statistics',
                            'description':
                                   ('The ILL requests statistics are different numbers \
related to the requests to other libraries.', ),
                            'gatherer':
                                   get_keyevent_ill_requests_statistics,
                            'extraparams': {
                                'doctype': ('combobox', 'Type of document', _get_item_doctype),
                                'status': ('combobox', 'Status of request', _get_request_statuses),
                                'supplier': ('combobox', 'Supplier', _get_libraries)},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(doctype)s_%(status)s_%(supplier)s_%(timespan)s',
                            'rows': ['Number of ILL requests',
                                     'Number of satisfied ILL requests 2 weeks \
                                     after the date of request creation',
                                     'Average time between the day \
                                     of the ILL request date and day \
                                     of the delivery item to the user (in days)',
                                     'Average time between the day \
                                     the ILL request was sent to the supplier and \
                                     the day of the delivery item (in days)'],
                            'output': 'Table',
                            'type': 'bibcirculation'},
                          'ill requests list':
                           {'fullname': 'Circulation ILL Requests list',
                            'specificname': 'Circulation ILL Requests list',
                            'description':
                                   ('The ILL requests list shows 50 requests to other \
libraries on the selected time span.', ),
                            'gatherer':
                                   get_keyevent_ill_requests_lists,
                            'extraparams': {
                                'doctype': ('combobox', 'Type of document', _get_item_doctype),
                                'supplier': ('combobox', 'Supplier', _get_libraries)},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(doctype)s_%(supplier)s_%(timespan)s',
                            'rows': [],
                            'output': 'List',
                            'type': 'bibcirculation'},
                          'percentage satisfied ill requests':
                           {'fullname': 'Percentage of circulation satisfied ILL requests',
                            'specificname': 'Percentage of circulation satisfied ILL requests',
                            'description':
                                   ('This graph shows both the satisfied ILL requests and \
the total number of requests in the selected time span.', ),
                            'gatherer':
                                   get_keyevent_trend_satisfied_ill_requests_percentage,
                            'extraparams': {
                                'doctype': ('combobox', 'Type of document', _get_item_doctype),
                                'status': ('combobox', 'Status of request', _get_request_statuses),
                                'supplier': ('combobox', 'Supplier', _get_libraries)},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(doctype)s_%(status)s_%(supplier)s_%(timespan)s',
                            'ylabel': 'Percentage of satisfied ILL requests',
                            'multiple': ['Satisfied ILL requests',
                                         'Total requests'],
                            'output': 'Graph',
                            'type': 'bibcirculation'},
                          'items stats':
                           {'fullname': 'Circulation items statistics',
                            'specificname': 'Circulation items statistics',
                            'description':
                                   ('The items statistics show the total number of items at \
the moment and the number of new items in the selected time span.', ),
                            'gatherer':
                                   get_keyevent_items_statistics,
                            'extraparams': {
                                'udc': ('textbox', 'UDC'),
                                },
                            'cachefilename':
                                   'webstat_%(event_id)s_%(udc)s_%(timespan)s',
                            'rows': ['The total number of items', 'Total number of new items'],
                            'output': 'Table',
                            'type': 'bibcirculation'},
                          'items list':
                           {'fullname': 'Circulation items list',
                            'specificname': 'Circulation items list',
                            'description':
                                   ('The item list shows data about the existing items.', ),
                            'gatherer':
                                   get_keyevent_items_lists,
                            'extraparams': {
                                'library': ('combobox', 'Library', _get_libraries),
                                'status': ('combobox', 'Status', _get_item_statuses)},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(library)s_%(status)s',
                            'rows': [],
                            'output': 'List',
                            'type': 'bibcirculation'},
                        'loan request statistics':
                          {'fullname': 'Circulation hold requests statistics',
                            'specificname': 'Circulation hold requests statistics',
                            'description':
                                   ('The hold requests statistics show numbers about the \
requests for documents. For the numbers to be correct, there must be data in the loanrequest \
custom event.', ),
                            'gatherer':
                                   get_keyevent_loan_request_statistics,
                            'extraparams': {
                                'item_status': ('combobox', 'Item status', _get_item_statuses)},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(item_status)s_%(timespan)s',
                            'rows': ['Number of hold requests, one week after the date of \
                                        request creation',
                                         'Number of successful hold requests transactions',
                                         'Average time between the hold request date and \
                                         the date of delivery document  in a year'],
                            'output': 'Table',
                            'type': 'bibcirculation'},
                         'loan request lists':
                           {'fullname': 'Circulation hold requests lists',
                            'specificname': 'Circulation hold requests lists',
                            'description':
                                   ('The hold requests list shows the most requested items.', ),
                            'gatherer':
                                   get_keyevent_loan_request_lists,
                            'extraparams': {
                                'udc': ('textbox', 'UDC')},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(udc)s_%(timespan)s',
                            'rows': [],
                            'output': 'List',
                            'type': 'bibcirculation'},
                         'user statistics':
                           {'fullname': 'Circulation users statistics',
                            'specificname': 'Circulation users statistics',
                            'description':
                                   ('The user statistics show the number of active users \
(at least one transaction) in the selected timespan.', ),
                            'gatherer':
                                   get_keyevent_user_statistics,
                            'extraparams': {},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(timespan)s',
                            'rows': ['Number of active users'],
                            'output': 'Table',
                            'type': 'bibcirculation'},
                         'user lists':
                           {'fullname': 'Circulation users lists',
                            'specificname': 'Circulation users lists',
                            'description':
                                   ('The user list shows the most intensive users \
(ILL requests + Loans)', ),
                            'gatherer':
                                   get_keyevent_user_lists,
                            'extraparams': {},
                            'cachefilename':
                                   'webstat_%(event_id)s_%(timespan)s',
                            'rows': [],
                            'output': 'List',
                            'type': 'bibcirculation'}

                       }

# CLI

def create_customevent(event_id=None, name=None, cols=[]):
    """
    Creates a new custom event by setting up the necessary MySQL tables.

    @param event_id: Proposed human-readable id of the new event.
    @type event_id: str

    @param name: Optionally, a descriptive name.
    @type name: str

    @param cols: Optionally, the name of the additional columns.
    @type cols: [str]

    @return: A status message
    @type: str
    """
    if event_id is None:
        return "Please specify a human-readable ID for the event."

    # Only accept id and name with standard characters
    if not re.search("[^\w]", str(event_id) + str(name)) is None:
        return "Please note that both event id and event name needs to be " + \
                  "written without any non-standard characters."

    # Make sure the chosen id is not already taken
    if len(run_sql("SELECT NULL FROM staEVENT WHERE id = %s",
                   (event_id, ))) != 0:
        return "Event id [%s] already exists! Aborted." % event_id

    # Check if the cols are valid titles
    for argument in cols:
        if (argument == "creation_time") or (argument == "id"):
            return "Invalid column title: %s! Aborted." % argument

    # Insert a new row into the events table describing the new event
    sql_param = [event_id]
    if name is not None:
        sql_name = "%s"
        sql_param.append(name)
    else:
        sql_name = "NULL"
    if len(cols) != 0:
        sql_cols = "%s"
        sql_param.append(cPickle.dumps(cols))
    else:
        sql_cols = "NULL"
    run_sql("INSERT INTO staEVENT (id, name, cols) VALUES (%s, " + \
                sql_name + ", " + sql_cols + ")", tuple(sql_param))

    tbl_name = get_customevent_table(event_id)

    # Create a table for the new event
    sql_query = ["CREATE TABLE %s (" % wash_table_column_name(tbl_name)]
    sql_query.append("id MEDIUMINT unsigned NOT NULL auto_increment,")
    sql_query.append("creation_time TIMESTAMP DEFAULT NOW(),")
    for argument in cols:
        arg = wash_table_column_name(argument)
        sql_query.append("`%s` MEDIUMTEXT NULL," % arg)
        sql_query.append("INDEX `%s` (`%s` (50))," % (arg, arg))
    sql_query.append("PRIMARY KEY (id))")
    sql_str = ' '.join(sql_query)
    run_sql(sql_str)

    # We're done! Print notice containing the name of the event.
    return ("Event table [%s] successfully created.\n" +
            "Please use event id [%s] when registering an event.") \
            % (tbl_name, event_id)


def modify_customevent(event_id=None, name=None, cols=[]):
    """
    Modify a custom event. It can modify the columns definition
    or/and the descriptive name

    @param event_id: Human-readable id of the event.
    @type event_id: str

    @param name: Optionally, a descriptive name.
    @type name: str

    @param cols: Optionally, the name of the additional columns.
    @type cols: [str]

    @return: A status message
    @type: str
    """
    if event_id is None:
        return "Please specify a human-readable ID for the event."

    # Only accept name with standard characters
    if not re.search("[^\w]", str(name)) is None:
        return "Please note that event name needs to be written " + \
            "without any non-standard characters."

    # Check if the cols are valid titles
    for argument in cols:
        if (argument == "creation_time") or (argument == "id"):
            return "Invalid column title: %s! Aborted." % argument

    res = run_sql("SELECT CONCAT('staEVENT', number), cols " + \
                      "FROM staEVENT WHERE id = %s", (event_id, ))
    if not res:
        return "Invalid event id: %s! Aborted" % event_id
    if not run_sql("SHOW TABLES LIKE %s", res[0][0]):
        run_sql("DELETE FROM staEVENT WHERE id=%s", (event_id, ))
        create_customevent(event_id, event_id, cols)
        return
    cols_orig = cPickle.loads(res[0][1])

    # add new cols
    cols_add = []
    for col in cols:
        if not col in cols_orig:
            cols_add.append(col)

    # del old cols
    cols_del = []
    for col in cols_orig:
        if not col in cols:
            cols_del.append(col)

    #modify event table
    if cols_del or cols_add:
        sql_query = ["ALTER TABLE %s " % wash_table_column_name(res[0][0])]
        # check if a column was renamed
        for col_del in cols_del:
            result = -1
            while result < 1 or result > len(cols_add) + 1:
                print("""What do you want to do with the column %s in event %s?:
1.- Delete it""" % (col_del, event_id))
                for i in range(len(cols_add)):
                    print("%d.- Rename it to %s" % (i + 2, cols_add[i]))
                result = int(raw_input("\n"))
            if result == 1:
                sql_query.append("DROP COLUMN `%s`" % col_del)
                sql_query.append(", ")
            else:
                col_add = cols_add[result-2]
                sql_query.append("CHANGE `%s` `%s` MEDIUMTEXT NULL"%(col_del, col_add))
                sql_query.append(", ")
                cols_add.remove(col_add)

        # add the rest of the columns
        for col_add in cols_add:
            sql_query.append("ADD COLUMN `%s` MEDIUMTEXT NULL, " % col_add)
            sql_query.append("ADD INDEX `%s` (`%s`(50))" % (col_add, col_add))
            sql_query.append(", ")
        sql_query[-1] = ";"
        run_sql("".join(sql_query))

    #modify event definition
    sql_query = ["UPDATE staEVENT SET"]
    sql_param = []
    if cols_del or cols_add:
        sql_query.append("cols = %s")
        sql_query.append(",")
        sql_param.append(cPickle.dumps(cols))
    if name:
        sql_query.append("name = %s")
        sql_query.append(",")
        sql_param.append(name)
    if sql_param:
        sql_query[-1] = "WHERE id = %s"
        sql_param.append(event_id)
        sql_str = ' '.join(sql_query)
        run_sql(sql_str, sql_param)

    # We're done! Print notice containing the name of the event.
    return ("Event table [%s] successfully modified." % (event_id, ))


def destroy_customevent(event_id=None):
    """
    Removes an existing custom event by destroying the MySQL tables and
    the event data that might be around. Use with caution!

    @param event_id: Human-readable id of the event to be removed.
    @type event_id: str

    @return: A status message
    @type: str
    """
    if event_id is None:
        return "Please specify an existing event id."

    # Check if the specified id exists
    if len(run_sql("SELECT NULL FROM staEVENT WHERE id = %s",
                   (event_id, ))) == 0:
        return "Custom event ID '%s' doesn't exist! Aborted." % event_id
    else:
        tbl_name = get_customevent_table(event_id)
        run_sql("DROP TABLE %s" % wash_table_column_name(tbl_name)) # kwalitee: disable=sql
        run_sql("DELETE FROM staEVENT WHERE id = %s", (event_id, ))
        return ("Custom event ID '%s' table '%s' was successfully destroyed.\n") \
                % (event_id, tbl_name)

def destroy_customevents():
    """
    Removes all existing custom events by destroying the MySQL tables and
    the events data that might be around. Use with caution!

    @return: A status message
    @type: str
    """
    msg = ''
    try:
        res = run_sql("SELECT id FROM staEVENT")
    except ProgrammingError:
        return msg
    for event in res:
        msg += destroy_customevent(event[0])
    return msg

def register_customevent(event_id, *arguments):
    """
    Registers a custom event. Will add to the database's event tables
    as created by create_customevent().

    This function constitutes the "function hook" that should be
    called throughout Invenio where one wants to register a
    custom event! Refer to the help section on the admin web page.

    @param event_id: Human-readable id of the event to be registered
    @type event_id: str

    @param *arguments: The rest of the parameters of the function call
    @type *arguments: [params]
    """
    res = run_sql("SELECT CONCAT('staEVENT', number),cols " + \
                      "FROM staEVENT WHERE id = %s", (event_id, ))
    if not res:
        return # the id does not exist
    tbl_name = res[0][0]
    if res[0][1]:
        col_titles = cPickle.loads(res[0][1])
    else:
        col_titles = []
    if len(col_titles) != len(arguments[0]):
        return # there is different number of arguments than cols

    # Make sql query
    if len(arguments[0]) != 0:
        sql_param = []
        sql_query = ["INSERT INTO %s (" % wash_table_column_name(tbl_name)]
        for title in col_titles:
            sql_query.append("`%s`" % title)
            sql_query.append(",")
        sql_query.pop() # del the last ','
        sql_query.append(") VALUES (")
        for argument in arguments[0]:
            sql_query.append("%s")
            sql_query.append(",")
            sql_param.append(argument)
        sql_query.pop() # del the last ','
        sql_query.append(")")
        sql_str = ''.join(sql_query)
        run_sql(sql_str, tuple(sql_param))
    else:
        run_sql("INSERT INTO %s () VALUES ()" % wash_table_column_name(tbl_name)) # kwalitee: disable=sql


def cache_keyevent_trend(ids=[]):
    """
    Runs the rawdata gatherer for the specific key events.
    Intended to be run mainly but the BibSched daemon interface.

    For a specific id, all possible timespans' rawdata is gathered.

    @param ids: The key event ids that are subject to caching.
    @type ids: []
    """
    args = {}

    for event_id in ids:
        args['event_id'] = event_id
        if 'type' in KEYEVENT_REPOSITORY[event_id] and \
             KEYEVENT_REPOSITORY[event_id]['type'] == 'bibcirculation':
            timespans = _get_timespans(bibcirculation_stat=True)[:-1]
        else:
            timespans = _get_timespans()[:-1]
        extraparams = KEYEVENT_REPOSITORY[event_id]['extraparams']

        # Construct all combinations of extraparams and store as
        # [{param name: arg value}] so as we can loop over them and just
        # pattern-replace the each dictionary against
        # the KEYEVENT_REPOSITORY['event_id']['cachefilename'].
        combos = [[]]
        for extra in [[(param, extra[0]) for extra in extraparams[param][1]()]
                  for param in extraparams]:
            combos = [i + [y] for y in extra for i in combos]
        combos = [dict(extra) for extra in combos]

        for i in range(len(timespans)):
            # Get timespans parameters
            args['timespan'] = timespans[i][0]

            args.update({'t_start': timespans[i][2], 't_end': timespans[i][3],
                          'granularity': timespans[i][4],
                          't_format': timespans[i][5],
                          'xtic_format': timespans[i][6]})

            for combo in combos:
                args.update(combo)

                # Create unique filename for this combination of parameters
                filename = KEYEVENT_REPOSITORY[event_id]['cachefilename'] \
                            % dict([(param, re.subn("[^\w]", "_",
                                           args[param])[0]) for param in args])

                # Create closure of gatherer function in case cache
                # needs to be refreshed
                gatherer = lambda: KEYEVENT_REPOSITORY[event_id] \
                    ['gatherer'](args)

                # Get data file from cache, ALWAYS REFRESH DATA!
                _get_file_using_cache(filename, gatherer, True).read()

    return True


def cache_customevent_trend(ids=[]):
    """
    Runs the rawdata gatherer for the specific custom events.
    Intended to be run mainly but the BibSched daemon interface.

    For a specific id, all possible timespans' rawdata is gathered.

    @param ids: The custom event ids that are subject to caching.
    @type ids: []
    """
    args = {}
    timespans = _get_timespans()

    for event_id in ids:
        args['event_id'] = event_id
        args['cols'] = []

        for i in range(len(timespans)):
            # Get timespans parameters
            args['timespan'] = timespans[i][0]
            args.update({'t_start': timespans[i][2], 't_end': timespans[i][3],
                          'granularity': timespans[i][4],
                          't_format': timespans[i][5],
                          'xtic_format': timespans[i][6]})

            # Create unique filename for this combination of parameters
            filename = "webstat_customevent_%(event_id)s_%(timespan)s" \
                        % {'event_id': re.subn("[^\w]", "_", event_id)[0],
                        'timespan': re.subn("[^\w]", "_", args['timespan'])[0]}

            # Create closure of gatherer function in case cache
            # needs to be refreshed
            gatherer = lambda: get_customevent_trend(args)

            # Get data file from cache, ALWAYS REFRESH DATA!
            _get_file_using_cache(filename, gatherer, True).read()

    return True


def basket_display():
    """
    Display basket statistics.
    """
    tbl_name = get_customevent_table("baskets")
    if not tbl_name:
        # custom event baskets not defined, so return empty output:
        return []
    try:
        res = run_sql("SELECT creation_time FROM %s ORDER BY creation_time" % wash_table_column_name(tbl_name)) # kwalitee: disable=sql
        days = (res[-1][0] - res[0][0]).days + 1
        public = run_sql("SELECT COUNT(*) FROM %s " % wash_table_column_name(tbl_name) + " WHERE action = 'display_public'")[0][0] # kwalitee: disable=sql
        users = run_sql("SELECT COUNT(DISTINCT user) FROM %s" % wash_table_column_name(tbl_name))[0][0] # kwalitee: disable=sql
        adds = run_sql("SELECT COUNT(*) FROM %s WHERE action = 'add'" % wash_table_column_name(tbl_name))[0][0] # kwalitee: disable=sql
        displays = run_sql("SELECT COUNT(*) FROM %s " % wash_table_column_name(tbl_name) + " WHERE action = 'display' OR action = 'display_public'")[0][0] # kwalitee: disable=sql
        hits = adds + displays
        average = hits / days

        res = [("Basket page hits", hits)]
        res.append(("   Average per day", average))
        res.append(("   Unique users", users))
        res.append(("   Additions", adds))
        res.append(("   Public", public))
    except IndexError:
        res = []

    return res


def alert_display():
    """
    Display alert statistics.
    """
    tbl_name = get_customevent_table("alerts")
    if not tbl_name:
        # custom event alerts not defined, so return empty output:
        return []
    try:
        res = run_sql("SELECT creation_time FROM %s ORDER BY creation_time"
                      % wash_table_column_name(tbl_name))
        days = (res[-1][0] - res[0][0]).days + 1
        res = run_sql("SELECT COUNT(DISTINCT user),COUNT(*) FROM %s" % wash_table_column_name(tbl_name)) # kwalitee: disable=sql
        users = res[0][0]
        hits = res[0][1]
        displays = run_sql("SELECT COUNT(*) FROM %s WHERE action = 'list'"
                           % wash_table_column_name(tbl_name))[0][0]
        search = run_sql("SELECT COUNT(*) FROM %s WHERE action = 'display'"
                         % wash_table_column_name(tbl_name))[0][0]
        average = hits / days

        res = [("Alerts page hits", hits)]
        res.append(("   Average per day", average))
        res.append(("   Unique users", users))
        res.append(("   Displays", displays))
        res.append(("   Searches history display", search))
    except IndexError:
        res = []

    return res


def loan_display():
    """
    Display loan statistics.
    """
    try:
        loans, renewals, returns, illrequests, holdrequests = \
                get_keyevent_bibcirculation_report()
        res = [("Yearly report", '')]
        res.append(("   Loans", loans))
        res.append(("   Renewals", renewals))
        res.append(("   Returns", returns))
        res.append(("   ILL requests", illrequests))
        res.append(("   Hold requests", holdrequests))
        return res
    except IndexError:
        return []


def get_url_customevent(url_dest, event_id, *arguments):
    """
    Get an url for registers a custom event. Every time is load the
    url will register a customevent as register_customevent().

    @param url_dest: url to redirect after register the event
    @type url_dest: str

    @param event_id: Human-readable id of the event to be registered
    @type event_id: str

    @param *arguments: The rest of the parameters of the function call
                       the param "WEBSTAT_IP" will tell webstat that here
                       should be the IP who request the url
    @type *arguments: [params]

    @return: url for register event
    @type: str
    """
    return "%s/stats/customevent_register?event_id=%s&arg=%s&url=%s" % \
            (CFG_SITE_URL, event_id, ','.join(arguments[0]), quote(url_dest))

# WEB

def perform_request_index(ln=CFG_SITE_LANG):
    """
    Displays some informative text, the health box, and a the list of
    key/custom events.
    """
    out = TEMPLATES.tmpl_welcome(ln=ln)

    # Display the health box
    out += TEMPLATES.tmpl_system_health_list(get_general_status(), ln=ln)

    # Produce a list of the key statistics
    out += TEMPLATES.tmpl_keyevent_list(ln=ln)

    # Display the custom statistics
    out += TEMPLATES.tmpl_customevent_list(_get_customevents(), ln=ln)

    # Display error log analyzer
    out += TEMPLATES.tmpl_error_log_statistics_list(ln=ln)

    # Display annual report
    out += TEMPLATES.tmpl_custom_summary(ln=ln)
    out += TEMPLATES.tmpl_yearly_report_list(ln=ln)

    # Display test for collections
    out += TEMPLATES.tmpl_collection_stats_main_list(ln=ln)

    return out

def perform_display_current_system_health(ln=CFG_SITE_LANG):
    """
    Display the current general system health:
        - Uptime/load average
        - Apache status
        - Session information
        - Searches recount
        - New records
        - Bibsched queue
        - New/modified records
        - Indexing, ranking, sorting and collecting methods
        - Baskets
        - Alerts
    """
    from ConfigParser import ConfigParser
    conf = ConfigParser()
    conf.read(CFG_WEBSTAT_CONFIG_PATH)

    # Prepare the health base data
    health_indicators = []
    now = datetime.datetime.now()
    yesterday = (now - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")
    tomorrow = (now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    # Append uptime and load average to the health box
    if conf.get("general", "uptime_box") == "True":
        health_indicators.append(("Uptime cmd",
                                  get_keyevent_snapshot_uptime_cmd()))

    # Append number of Apache processes to the health box
    if conf.get("general", "apache_box") == "True":
        health_indicators.append(("Apache processes",
                                  get_keyevent_snapshot_apache_processes()))
        health_indicators.append(None)

    # Append session information to the health box
    if conf.get("general", "visitors_box") == "True":
        sess = get_keyevent_snapshot_sessions()
        health_indicators.append(("Total active visitors", sum(sess)))
        health_indicators.append(("    Logged in", sess[1]))
        health_indicators.append(None)

    # Append searches information to the health box
    if conf.get("general", "search_box") == "True":
        args = {'t_start': today, 't_end': tomorrow,
                 'granularity': "day", 't_format': "%Y-%m-%d"}
        searches = get_keyevent_trend_search_type_distribution(args)
        health_indicators.append(("Searches since midnight",
                                  sum(searches[0][1])))
        health_indicators.append(("    Simple", searches[0][1][0]))
        health_indicators.append(("    Advanced", searches[0][1][1]))
        health_indicators.append(None)

    # Append new records information to the health box
    if conf.get("general", "record_box") == "True":
        args = {'collection': "All", 't_start': today,
                 't_end': tomorrow, 'granularity': "day",
                 't_format': "%Y-%m-%d"}
        try:
            tot_records = get_keyevent_trend_collection_population(args)[0][1]
        except IndexError:
            tot_records = 0
        args = {'collection': "All", 't_start': yesterday,
                 't_end': today, 'granularity': "day", 't_format': "%Y-%m-%d"}
        try:
            new_records = tot_records - \
                get_keyevent_trend_collection_population(args)[0][1]
        except IndexError:
            new_records = 0
        health_indicators.append(("Total records", tot_records))
        health_indicators.append(("    New records since midnight",
                                  new_records))
        health_indicators.append(None)

    # Append status of BibSched queue to the health box
    if conf.get("general", "bibsched_box") == "True":
        bibsched = get_keyevent_snapshot_bibsched_status()
        health_indicators.append(("BibSched queue",
                                  sum([x[1] for x in bibsched])))
        for item in bibsched:
            health_indicators.append(("    " + item[0], str(item[1])))
        health_indicators.append(None)

    # Append records pending
    if conf.get("general", "waiting_box") == "True":
        last_index, last_rank, last_sort, last_coll=get_last_updates()
        index_categories = zip(*get_all_indexes(with_ids=True))[1]
        rank_categories = ('wrd', 'demo_jif', 'citation',
                            'citerank_citation_t',
                            'citerank_pagerank_c',
                            'citerank_pagerank_t')
        sort_categories = ('latest first', 'title', 'author', 'report number',
                            'most cited')

        health_indicators.append(("Records pending per indexing method since", last_index))
        for ic in index_categories:
            health_indicators.append(("   - " + str(ic), get_list_link('index', ic)))
        health_indicators.append(None)
        health_indicators.append(("Records pending per ranking method since", last_rank))
        for rc in rank_categories:
            health_indicators.append(("   - " + str(rc), get_list_link('rank', rc)))
        health_indicators.append(None)
        health_indicators.append(("Records pending per sorting method since", last_sort))
        for sc in sort_categories:
            health_indicators.append(("   - " + str(sc), get_list_link('sort', sc)))
        health_indicators.append(None)
        health_indicators.append(("Records pending for webcolling since", last_coll))
        health_indicators.append(("   - webcoll", get_list_link('collect')))
        health_indicators.append(None)

    # Append basket stats to the health box
    if conf.get("general", "basket_box") == "True":
        health_indicators += basket_display()
        health_indicators.append(None)

    # Append alerts stats to the health box
    if conf.get("general", "alert_box") == "True":
        health_indicators += alert_display()
        health_indicators.append(None)

    # Display the health box
    return TEMPLATES.tmpl_system_health(health_indicators, ln=ln)

def perform_display_ingestion_status(req_ingestion, ln=CFG_SITE_LANG):
    """
    Display the updating status for the records matching a
    given request.

    @param req_ingestion: Search pattern request
    @type req_ingestion: str
    """
    # preconfigured values
    index_methods = zip(*get_all_indexes(with_ids=True))[1]
    rank_methods = ('wrd', 'demo_jif', 'citation', 'citerank_citation_t',
                    'citerank_pagerank_c', 'citerank_pagerank_t')
    sort_methods = ('latest first', 'title', 'author', 'report number',
                    'most cited')
    from ConfigParser import ConfigParser
    conf = ConfigParser()
    conf.read(CFG_WEBSTAT_CONFIG_PATH)
    general = get_general_status()
    flag = 0  # match with pending records
    stats = []

    list_records = get_ingestion_matching_records(req_ingestion, \
                    int(conf.get("general", "max_ingestion_health")))
    if list_records == []:
        stats.append(("No matches for your query!", " "*60))
        return TEMPLATES.tmpl_ingestion_health(general, req_ingestion, stats, \
               ln=ln)
    else:
        for record in list_records:
            if record == 0:
                return TEMPLATES.tmpl_ingestion_health(general, None, \
                                                       None, ln=ln)
            elif record == -1:
                stats.append(("Invalid pattern! Please retry", " "*60))
                return TEMPLATES.tmpl_ingestion_health(general, None, \
                                                       stats, ln=ln)
            else:
                stat = get_record_ingestion_status(record)
                last_mod = get_record_last_modification(record)
                if stat != 0:
                    flag = 1 # match
                    # Indexing
                    stats.append((get_title_ingestion(record, last_mod)," "*90))
                    stats.append(("Pending for indexing methods:", " "*80))
                    for im in index_methods:
                        last = get_specific_ingestion_status(record,"index", im)
                        if last != None:
                            stats.append(("    - %s"%im, "last: " + last))
                    # Ranking
                    stats.append(("Pending for ranking methods:", " "*80))
                    for rm in rank_methods:
                        last = get_specific_ingestion_status(record, "rank", rm)
                        if last != None:
                            stats.append(("    - %s"%rm, "last: " + last))
                    # Sorting
                    stats.append(("Pending for sorting methods:", " "*80))
                    for sm in sort_methods:
                        last = get_specific_ingestion_status(record, "sort", sm)
                        if last != None:
                            stats.append(("    - %s"%sm, "last: " + last))
                    # Collecting
                    stats.append(("Pending for webcolling:", " "*80))
                    last = get_specific_ingestion_status(record, "collect", )
                    if last != None:
                        stats.append(("    - webcoll", "last: " + last))
    # if there was no match
    if flag == 0:
        stats.append(("All matching records up to date!", " "*60))
    return TEMPLATES.tmpl_ingestion_health(general, req_ingestion, stats, ln=ln)

def perform_display_yearly_report(ln=CFG_SITE_LANG):
    """
    Display the year recount
    """
    # Append loans stats to the box
    year_report = []
    year_report += loan_display()
    year_report.append(None)
    return TEMPLATES.tmpl_yearly_report(year_report, ln=ln)

def perform_display_keyevent(event_id=None, args={},
                             req=None, ln=CFG_SITE_LANG):
    """
    Display key events using a certain output type over the given time span.

    @param event_id: The ids for the custom events that are to be displayed.
    @type event_id: [str]

    @param args: { param name: argument value }
    @type args: { str: str }

    @param req: The Apache request object, necessary for export redirect.
    @type req:
    """
    # Get all the option lists:
    # { parameter name: [(argument internal name, argument full name)]}
    options = dict()
    order = []
    for param in KEYEVENT_REPOSITORY[event_id]['extraparams']:
        # Order of options
        order.append(param)

        if KEYEVENT_REPOSITORY[event_id]['extraparams'][param][0] == 'combobox':
            options[param] = ('combobox',
                     KEYEVENT_REPOSITORY[event_id]['extraparams'][param][1],
                      KEYEVENT_REPOSITORY[event_id]['extraparams'][param][2]())
        else:
            options[param] = (KEYEVENT_REPOSITORY[event_id]['extraparams'][param][0],
                     (KEYEVENT_REPOSITORY[event_id]['extraparams'][param][1]))

    # Build a dictionary for the selected parameters:
    # { parameter name: argument internal name }
    choosed = dict([(param, args[param]) for param in KEYEVENT_REPOSITORY
                    [event_id]['extraparams']])
    if KEYEVENT_REPOSITORY[event_id]['output'] == 'Graph':
        options['format'] = ('combobox', 'Output format', _get_formats())
        choosed['format'] = args['format']
        order += ['format']
    if event_id != 'items list':
        if 'type' in KEYEVENT_REPOSITORY[event_id] and \
            KEYEVENT_REPOSITORY[event_id]['type'] == 'bibcirculation':
            options['timespan'] = ('combobox', 'Time span', _get_timespans(bibcirculation_stat=True))
        else:
            options['timespan'] = ('combobox', 'Time span', _get_timespans())
        choosed['timespan'] = args['timespan']
        order += ['timespan']
        choosed['s_date'] = args['s_date']
        choosed['f_date'] = args['f_date']

    # Send to template to prepare event customization FORM box
    list = KEYEVENT_REPOSITORY[event_id]['output'] == 'List'
    out = "\n".join(["<p>%s</p>" % parr for parr in KEYEVENT_REPOSITORY[event_id]['description']]) \
            + TEMPLATES.tmpl_keyevent_box(options, order, choosed, ln=ln, list=list)

    # Arguments OK?

    # Check for existance. If nothing, only show FORM box from above.
    if len(choosed) == 0:
        return out

    # Make sure extraparams are valid, if any
    if KEYEVENT_REPOSITORY[event_id]['output'] == 'Graph' and \
            event_id != 'percentage satisfied ill requests':
        for param in choosed:
            if param in options and options[param] == 'combobox' and \
                    not choosed[param] in [x[0] for x in options[param][2]]:
                return out + TEMPLATES.tmpl_error(
                'Please specify a valid value for parameter "%s".'
                                               % options[param][0], ln=ln)

    # Arguments OK beyond this point!

    # Get unique name for caching purposes (make sure that the params used
    # in the filename are safe!)
    filename = KEYEVENT_REPOSITORY[event_id]['cachefilename'] \
               % dict([(param, re.subn("[^\w]", "_", choosed[param])[0])
                       for param in choosed] +
                      [('event_id', re.subn("[^\w]", "_", event_id)[0])])

    # Get time parameters from repository
    if 'timespan' in choosed:
        if choosed['timespan'] == "select date":
            t_args = _get_time_parameters_select_date(args["s_date"], args["f_date"])
        else:
            t_args = _get_time_parameters(options, choosed['timespan'])
    else:
        t_args = args
    for param in KEYEVENT_REPOSITORY[event_id]['extraparams']:
        t_args[param] = choosed[param]

    if 'format' in args and args['format'] == 'Full list':
        gatherer = lambda: KEYEVENT_REPOSITORY[event_id]['gatherer'](t_args, limit=-1)
        export_to_file(gatherer(), req)
        return out

    # Create closure of frequency function in case cache needs to be refreshed
    gatherer = lambda return_sql: KEYEVENT_REPOSITORY[event_id]['gatherer'](t_args, return_sql=return_sql)

    # Determine if this particular file is due for scheduling cacheing,
    # in that case we must not allow refreshing of the rawdata.
    allow_refresh = not _is_scheduled_for_cacheing(event_id)

    # Get data file from cache (refresh if necessary)
    force = 'timespan' in choosed and choosed['timespan'] == "select date"
    data = eval(_get_file_using_cache(filename, gatherer, force,
                                      allow_refresh=allow_refresh).read())

    if KEYEVENT_REPOSITORY[event_id]['output'] == 'Graph':
        # If type indicates an export, run the export function and we're done
        if _is_type_export(choosed['format']):
            _get_export_closure(choosed['format'])(data, req)
            return out
        # Prepare the graph settings that are being passed on to grapher
        settings = {"title": KEYEVENT_REPOSITORY[event_id]['specificname']\
                     % choosed,
                  "xlabel": t_args['t_fullname'] + ' (' + \
                     t_args['granularity'] + ')',
                  "ylabel": KEYEVENT_REPOSITORY[event_id]['ylabel'],
                  "xtic_format": t_args['xtic_format'],
                  "format": choosed['format'],
                  "multiple": KEYEVENT_REPOSITORY[event_id]['multiple']}
    else:
        settings = {"title": KEYEVENT_REPOSITORY[event_id]['specificname']\
                     % choosed, "format": 'Table',
                     "rows": KEYEVENT_REPOSITORY[event_id]['rows']}
    if args['sql']:
        sql = gatherer(True)
    else:
        sql = ''
    return out + _perform_display_event(data,
                        os.path.basename(filename), settings, ln=ln) + sql


def perform_display_customevent(ids=[], args={}, req=None, ln=CFG_SITE_LANG):
    """
    Display custom events using a certain output type over the given time span.

    @param ids: The ids for the custom events that are to be displayed.
    @type ids: [str]

    @param args: { param name: argument value }
    @type args: { str: str }

    @param req: The Apache request object, necessary for export redirect.
    @type req:
    """
    # Get all the option lists:
    # { parameter name: [(argument internal name, argument full name)]}
    cols_dict = _get_customevent_cols()
    cols_dict['__header'] = 'Argument'
    cols_dict['__none'] = []
    options = {'ids': ('Custom event', _get_customevents()),
                'timespan': ('Time span', _get_timespans()),
                'format': ('Output format', _get_formats(True)),
                'cols': cols_dict}

    # Build a dictionary for the selected parameters:
    # { parameter name: argument internal name }
    choosed = {'ids': args['ids'], 'timespan': args['timespan'],
                'format': args['format'], 's_date': args['s_date'],
                'f_date': args['f_date']}
    # Calculate cols
    index = []
    for key in args.keys():
        if key[:4] == 'cols':
            index.append(key[4:])
    index.sort()
    choosed['cols'] = [zip([""] + args['bool' + i], args['cols' + i],
                            args['col_value' + i]) for i in index]
    # Send to template to prepare event customization FORM box
    out = TEMPLATES.tmpl_customevent_box(options, choosed, ln=ln)

    # Arguments OK?

    # Make sure extraparams are valid, if any
    for param in ['ids', 'timespan', 'format']:
        legalvalues = [x[0] for x in options[param][1]]

        if type(args[param]) is list:
            # If the argument is a list, like the content of 'ids'
            # every value has to be checked
            if len(args[param]) == 0:
                return out + TEMPLATES.tmpl_error(
                    'Please specify a valid value for parameter "%s".'
                    % options[param][0], ln=ln)
            for arg in args[param]:
                if not arg in legalvalues:
                    return out + TEMPLATES.tmpl_error(
                        'Please specify a valid value for parameter "%s".'
                        % options[param][0], ln=ln)
        else:
            if not args[param] in legalvalues:
                return out + TEMPLATES.tmpl_error(
                    'Please specify a valid value for parameter "%s".'
                        % options[param][0], ln=ln)

    # Fetch time parameters from repository
    if choosed['timespan'] == "select date":
        args_req = _get_time_parameters_select_date(args["s_date"],
                                                    args["f_date"])
    else:
        args_req = _get_time_parameters(options, choosed['timespan'])

    # ASCII dump data is different from the standard formats
    if choosed['format'] == 'asciidump':
        data = perform_display_customevent_data_ascii_dump(ids, args,
                                                           args_req, choosed)
    else:
        data = perform_display_customevent_data(ids, args_req, choosed)

    # If type indicates an export, run the export function and we're done
    if _is_type_export(args['format']):
        _get_export_closure(args['format'])(data, req)
        return out

    # Get full names, for those that have them
    names = []
    events = _get_customevents()
    for event_id in ids:
        temp = events[[x[0] for x in events].index(event_id)]
        if temp[1] != None:
            names.append(temp[1])
        else:
            names.append(temp[0])

    # Generate a filename for the graph
    filename = "tmp_webstat_customevent_" + ''.join([re.subn("[^\w]", "",
                                       event_id)[0] for event_id in ids]) + "_"
    if choosed['timespan'] == "select date":
        filename += args_req['t_start'] + "_" + args_req['t_end']
    else:
        filename += choosed['timespan']
    settings = {"title": 'Custom event',
                 "xlabel": args_req['t_fullname'] + ' (' + \
                     args_req['granularity'] + ')',
                 "ylabel": "Action quantity",
                 "xtic_format": args_req['xtic_format'],
                 "format": choosed['format'],
                 "multiple": (type(ids) is list) and names or []}

    return out + _perform_display_event(data, os.path.basename(filename),
                                        settings, ln=ln)


def perform_display_customevent_data(ids, args_req, choosed):
    """Returns the trend data"""
    data_unmerged = []
    for event_id, i in [(ids[i], str(i)) for i in range(len(ids))]:
        # Calculate cols
        args_req['cols'] = choosed['cols'][int(i)]

        # Get unique name for the rawdata file (wash arguments!)
        filename = "webstat_customevent_" + re.subn("[^\w]", "", event_id + \
                   "_" + choosed['timespan'] + "_" + '-'.join([':'.join(col)
                                            for col in args_req['cols']]))[0]

        # Add the current id to the gatherer's arguments
        args_req['event_id'] = event_id

        # Prepare raw data gatherer, if cache needs refreshing.
        gatherer = lambda x: get_customevent_trend(args_req)

        # Determine if this particular file is due for scheduling cacheing,
        # in that case we must not allow refreshing of the rawdata.
        allow_refresh = not _is_scheduled_for_cacheing(event_id)

        # Get file from cache, and evaluate it to trend data
        force = choosed['timespan'] == "select date"
        data_unmerged.append(eval(_get_file_using_cache(filename, gatherer,
                             force, allow_refresh=allow_refresh).read()))

    # Merge data from the unmerged trends into the final destination
    return [(x[0][0], tuple([y[1] for y in x])) for x in zip(*data_unmerged)]


def perform_display_customevent_data_ascii_dump(ids, args, args_req, choosed):
    """Returns the trend data"""
    for i in [str(j) for j in range(len(ids))]:
        args['bool' + i].insert(0, "")
        args_req['cols' + i] = zip(args['bool' + i], args['cols' + i],
                                 args['col_value' + i])
    filename = "webstat_customevent_" + re.subn("[^\w]", "", ''.join(ids) +
                "_" + choosed['timespan'] + "_" + '-'.join([':'.join(col) for
                col in [args['cols' + str(i)] for i in range(len(ids))]]) +
                                                "_asciidump")[0]
    args_req['ids'] = ids
    gatherer = lambda: get_customevent_dump(args_req)
    force = choosed['timespan'] == "select date"
    return eval(_get_file_using_cache(filename, gatherer, force).read())


def perform_display_coll_list(req=None, ln=CFG_SITE_LANG):
    """
    Display list of collections

    @param req: The Apache request object, necessary for export redirect.
    @type req:
    """
    return TEMPLATES.tmpl_collection_stats_complete_list(get_collection_list_plus_all())


def perform_display_stats_per_coll(args={}, req=None, ln=CFG_SITE_LANG):
    """
    Display general statistics for a given collection

    @param args: { param name: argument value }
    @type args: { str: str }

    @param req: The Apache request object, necessary for export redirect.
    @type req:
    """
    events_id = ('collection population', 'download frequency', 'comments frequency')
    # Get all the option lists:
    # Make sure extraparams are valid, if any
    if not args['collection'] in [x[0] for x in get_collection_list_plus_all()]:
        return TEMPLATES.tmpl_error('Please specify a valid value for parameter "Collection".')

    # { parameter name: [(argument internal name, argument full name)]}
    options = {'collection': ('combobox', 'Collection', get_collection_list_plus_all()),
               'timespan': ('combobox', 'Time span', _get_timespans()),
               'format': ('combobox', 'Output format', _get_formats())}
    order = options.keys()

    # Arguments OK beyond this point!

    # Get unique name for caching purposes (make sure that the params
    # used in the filename are safe!)
    out = TEMPLATES.tmpl_keyevent_box(options, order, args, ln=ln)
    out += "<table>"
    pair = False
    for event_id in events_id:
        # Get unique name for caching purposes (make sure that the params used
        # in the filename are safe!)
        filename = KEYEVENT_REPOSITORY[event_id]['cachefilename'] \
               % dict([(param, re.subn("[^\w]", "_", args[param])[0])
                       for param in args] +
                      [('event_id', re.subn("[^\w]", "_", event_id)[0])])

        # Get time parameters from repository
        if args['timespan'] == "select date":
            t_args = _get_time_parameters_select_date(args["s_date"], args["f_date"])
        else:
            t_args = _get_time_parameters(options, args['timespan'])
        for param in KEYEVENT_REPOSITORY[event_id]['extraparams']:
            t_args[param] = args[param]
        # Create closure of frequency function in case cache needs to be refreshed
        gatherer = lambda return_sql: KEYEVENT_REPOSITORY[event_id]['gatherer'](t_args, return_sql=return_sql)

        # Determine if this particular file is due for scheduling cacheing,
        # in that case we must not allow refreshing of the rawdata.
        allow_refresh = not _is_scheduled_for_cacheing(event_id)

        # Get data file from cache (refresh if necessary)
        data = eval(_get_file_using_cache(filename, gatherer, allow_refresh=allow_refresh).read())

        # Prepare the graph settings that are being passed on to grapher
        settings = {"title": KEYEVENT_REPOSITORY[event_id]['specificname'] % t_args,
                  "xlabel":  t_args['t_fullname'] + ' (' + \
                     t_args['granularity'] + ')',
                  "ylabel": KEYEVENT_REPOSITORY[event_id]['ylabel'],
                  "xtic_format": t_args['xtic_format'],
                  "format": args['format'],
                  "multiple": KEYEVENT_REPOSITORY[event_id]['multiple'],
                  "size": '360,270'}
        if not pair:
            out += '<tr>'
        out += '<td>%s</td>' % _perform_display_event(data,
                                    os.path.basename(filename), settings, ln=ln)
        if pair:
            out += '</tr>'
        pair = not pair
    return out + "</table>"


def perform_display_customevent_help(ln=CFG_SITE_LANG):
    """Display the custom event help"""
    return TEMPLATES.tmpl_customevent_help(ln=ln)


def perform_display_error_log_analyzer(ln=CFG_SITE_LANG):
    """Display the error log analyzer"""
    update_error_log_analyzer()
    return TEMPLATES.tmpl_error_log_analyzer(get_invenio_error_log_ranking(),
                                             get_invenio_last_n_errors(5),
                                             get_apache_error_log_ranking())


def perform_display_custom_summary(args, ln=CFG_SITE_LANG):
    """Display the custom summary (annual report)

    @param args: { param name: argument value } (chart title, search query and output tag)
    @type args: { str: str }
    """
    if args['tag'] == '':
        args['tag'] = CFG_JOURNAL_TAG.replace("%", "p")
    data = get_custom_summary_data(args['query'], args['tag'])
    tag_name = _get_tag_name(args['tag'])
    if tag_name == '':
        tag_name = args['tag']
    path = WEBSTAT_GRAPH_DIRECTORY + os.path.basename("tmp_webstat_custom_summary_"
                                                + args['query'] + args['tag'])
    if not create_custom_summary_graph(data[:-1], path, args['title']):
        path = None
    return TEMPLATES.tmpl_display_custom_summary(tag_name, data, args['title'],
                                    args['query'], args['tag'], path, ln=ln)

# INTERNALS

def _perform_display_event(data, name, settings, ln=CFG_SITE_LANG):
    """
    Retrieves a graph or a table.

    @param data: The trend/dump data
    @type data: [(str, str|int|(str|int,...))] | [(str|int,...)]

    @param name: The name of the trend (to be used as basename of graph file)
    @type name: str

    @param settings: Dictionary of graph parameters
    @type settings: dict

    @return: The URL of the graph (ASCII or image)
    @type: str
    """
    path = WEBSTAT_GRAPH_DIRECTORY + "tmp_" + name

    # Generate, and insert using the appropriate template
    if settings["format"] == "asciidump":
        path += "_asciidump"
        create_graph_dump(data, path)
        out = TEMPLATES.tmpl_display_event_trend_ascii(settings["title"],
                                                        path, ln=ln)

    if settings["format"] == "Table":
        create_graph_table(data, path, settings)
        return TEMPLATES.tmpl_display_event_trend_text(settings["title"], path, ln=ln)

    create_graph_trend(data, path, settings)
    if settings["format"] == "asciiart":
        out = TEMPLATES.tmpl_display_event_trend_ascii(
            settings["title"], path, ln=ln)
    else:
        if settings["format"] == "gnuplot":
            try:
                import Gnuplot
            except ImportError:
                out = 'Gnuplot is not installed. Returning ASCII art.' + \
                       TEMPLATES.tmpl_display_event_trend_ascii(
                    settings["title"], path, ln=ln)

            out = TEMPLATES.tmpl_display_event_trend_image(
                settings["title"], path, ln=ln)
        elif settings["format"] == "flot":
            out = TEMPLATES.tmpl_display_event_trend_text(
                settings["title"], path, ln=ln)
        else:
            out = TEMPLATES.tmpl_display_event_trend_ascii(
                    settings["title"], path, ln=ln)
    avgs, maxs, mins = get_numeric_stats(data, settings["multiple"] is not None)
    return out + TEMPLATES.tmpl_display_numeric_stats(settings["multiple"],
                    avgs, maxs, mins)


def _get_customevents():
    """
    Retrieves registered custom events from the database.

    @return: [(internal name, readable name)]
    @type: [(str, str)]
    """
    return [(x[0], x[1]) for x in run_sql("SELECT id, name FROM staEVENT")]


def _get_timespans(dttime=None, bibcirculation_stat=False):
    """
    Helper function that generates possible time spans to be put in the
    drop-down in the generation box. Computes possible years, and also some
    pre-defined simpler values. Some items in the list returned also tweaks the
    output graph, if any, since such values are closely related to the nature
    of the time span.

    @param dttime: A datetime object indicating the current date and time
    @type dttime: datetime.datetime

    @return: [(Internal name, Readable name, t_start, t_end, granularity, format, xtic_format)]
    @type [(str, str, str, str, str, str, str)]
    """
    if dttime is None:
        dttime = datetime.datetime.now()

    dtformat = "%Y-%m-%d"
    # Helper function to return a timediff object reflecting a diff of x days
    d_diff = lambda x: datetime.timedelta(days=x)
    # Helper function to return the number of days in the month x months ago
    d_in_m = lambda x: calendar.monthrange(
        ((dttime.month - x < 1) and dttime.year - 1 or dttime.year),
                                           (((dttime.month - 1) - x) % 12 + 1))[1]
    to_str = lambda x: x.strftime(dtformat)
    dt_str = to_str(dttime)

    spans = [("today", "Today",
              dt_str,
              to_str(dttime + d_diff(1)),
              "hour", dtformat, "%H"),
             ("this week", "This week",
              to_str(dttime - d_diff(dttime.weekday())),
              to_str(dttime + d_diff(1)),
              "day", dtformat, "%a"),
             ("last week", "Last week",
              to_str(dttime - d_diff(dttime.weekday() + 7)),
              to_str(dttime - d_diff(dttime.weekday())),
              "day", dtformat, "%a"),
             ("this month", "This month",
              to_str(dttime - d_diff(dttime.day) + d_diff(1)),
              to_str(dttime + d_diff(1)),
              "day", dtformat, "%d"),
             ("last month", "Last month",
              to_str(dttime - d_diff(d_in_m(1)) - d_diff(dttime.day) + d_diff(1)),
              to_str(dttime - d_diff(dttime.day) + d_diff(1)),
              "day", dtformat, "%d"),
             ("last three months", "Last three months",
              to_str(dttime - d_diff(d_in_m(1)) - d_diff(d_in_m(2)) -
                     d_diff(dttime.day) + d_diff(1)),
              dt_str,
              "month", dtformat, "%b"),
             ("last year", "Last year",
              to_str((dttime - datetime.timedelta(days=365)).replace(day=1)),
              to_str((dttime + datetime.timedelta(days=31)).replace(day=1)),
              "month", dtformat, "%b")]

    # Get first year as indicated by the content's in bibrec or
    # CFG_WEBSTAT_BIBCIRCULATION_START_YEAR
    try:
        if bibcirculation_stat and CFG_WEBSTAT_BIBCIRCULATION_START_YEAR:
            year1 = int(CFG_WEBSTAT_BIBCIRCULATION_START_YEAR)
        else:
            year1 = run_sql("SELECT creation_date FROM bibrec ORDER BY \
                    creation_date LIMIT 1")[0][0].year
    except:
        year1 = dttime.year

    year2 = time.localtime()[0]
    diff_year = year2 - year1
    if diff_year >= 2:
        spans.append(("last 2 years", "Last 2 years",
                      to_str((dttime - datetime.timedelta(days=365 * 2)).replace(day=1)),
                      to_str((dttime + datetime.timedelta(days=31)).replace(day=1)),
                      "month", dtformat, "%b"))
    if diff_year >= 5:
        spans.append(("last 5 years", "Last 5 years",
                      to_str((dttime - datetime.timedelta(days=365 * 5)).replace(day=1)),
                      to_str((dttime + datetime.timedelta(days=31)).replace(day=1)),
                      "year", dtformat, "%Y"))
    if diff_year >= 10:
        spans.append(("last 10 years", "Last 10 years",
                      to_str((dttime - datetime.timedelta(days=365 * 10)).replace(day=1)),
                      to_str((dttime + datetime.timedelta(days=31)).replace(day=1)),
                      "year", dtformat, "%Y"))
    spans.append(("full history", "Full history", str(year1), str(year2 + 1),
                  "year", "%Y", "%Y"))
    spans.extend([(str(x), str(x), str(x), str(x + 1), "month", "%Y", "%b")
                  for x in range(year2, year1 - 1, -1)])

    spans.append(("select date", "Select date...", "", "",
                  "hour", dtformat, "%H"))

    return spans


def _get_time_parameters(options, timespan):
    """
    Returns the time parameters from the repository when it is a default timespan
    @param options: A dictionary with the option lists
    @type options: { parameter name: [(argument internal name, argument full name)]}

    @param timespan: name of the chosen timespan
    @type timespan: str

    @return: [(Full name, t_start, t_end, granularity, format, xtic_format)]
    @type [(str, str, str, str, str, str, str)]
    """
    if len(options['timespan']) == 2:
        i = 1
    else:
        i = 2
    _, t_fullname, t_start, t_end, granularity, t_format, xtic_format = \
            options['timespan'][i][[x[0]
                          for x in options['timespan'][i]].index(timespan)]
    return {'t_fullname': t_fullname, 't_start': t_start, 't_end': t_end,
            'granularity': granularity, 't_format': t_format,
            'xtic_format': xtic_format}


def _get_time_parameters_select_date(s_date, f_date):
    """
    Returns the time parameters from the repository when it is a custom timespan
    @param s_date: start date for the graph
    @type s_date: str %m/%d/%Y %H:%M

    @param f_date: finish date for the graph
    @type f_date: str %m/%d/%Y %H:%M

    @return: [(Full name, t_start, t_end, granularity, format, xtic_format)]
    @type [(str, str, str, str, str, str, str)]
    """

    t_fullname = "%s-%s" % (s_date, f_date)
    dt_start = datetime.datetime(*(time.strptime(s_date, "%m/%d/%Y %H:%M")[0:6]))
    dt_end = datetime.datetime(*(time.strptime(f_date, "%m/%d/%Y %H:%M")[0:6]))
    if dt_end - dt_start <= timedelta(hours=1):
        xtic_format = "%m:%s"
        granularity = 'second'
    elif dt_end - dt_start <= timedelta(days=1):
        xtic_format = "%H:%m"
        granularity = 'minute'
    elif dt_end - dt_start <= timedelta(days=7):
        xtic_format = "%H"
        granularity = 'hour'
    elif dt_end - dt_start <= timedelta(days=60):
        xtic_format = "%a"
        granularity = 'day'
    elif dt_end - dt_start <= timedelta(days=730):
        xtic_format = "%d"
        granularity = 'month'
    else:
        xtic_format = "%H"
        granularity = 'hour'
    t_format = "%Y-%m-%d %H:%M:%S"
    t_start = dt_start.strftime("%Y-%m-%d %H:%M:%S")
    t_end = dt_end.strftime("%Y-%m-%d %H:%M:%S")
    return {'t_fullname': t_fullname, 't_start': t_start, 't_end': t_end,
            'granularity': granularity, 't_format': t_format,
            'xtic_format': xtic_format}


def _get_formats(with_dump=False):
    """
    Helper function to retrieve a Invenio friendly list of all possible
    output types (displaying and exporting) from the central repository as
    stored in the variable self.types at the top of this module.

    @param with_dump: Optionally displays the custom-event only type 'asciidump'
    @type with_dump: bool

    @return: [(Internal name, Readable name)]
    @type [(str, str)]
    """
    # The third tuple value is internal
    if with_dump:
        return [(x[0], x[1]) for x in TYPE_REPOSITORY]
    else:
        return [(x[0], x[1]) for x in TYPE_REPOSITORY if x[0] != 'asciidump']


def _get_customevent_cols(event_id=""):
    """
    List of all the diferent name of columns in customevents.

    @return: {id: [(internal name, readable name)]}
    @type: {str: [(str, str)]}
    """
    sql_str = "SELECT id,cols FROM staEVENT"
    sql_param = []
    if event_id:
        sql_str += "WHERE id = %s"
        sql_param.append(event_id)
    cols = {}
    for event in run_sql(sql_str, sql_param):
        if event[0]:
            if event[1]:
                cols[event[0]] = [(name, name) for name
                                   in cPickle.loads(event[1])]
            else:
                cols[event[0]] = []
    return cols


def _is_type_export(typename):
    """
    Helper function that consults the central repository of types to determine
    whether the input parameter represents an export type.

    @param typename: Internal type name
    @type typename: str

    @return: Information whether a certain type exports data
    @type: bool
    """
    return len(TYPE_REPOSITORY[[x[0] for x in
                                TYPE_REPOSITORY].index(typename)]) == 3


def _get_export_closure(typename):
    """
    Helper function that for a certain type, gives back the corresponding export
    closure.

    @param typename: Internal type name
    @type typename: str

    @return: Closure that exports data to the type's format
    @type: function
    """
    return TYPE_REPOSITORY[[x[0] for x in TYPE_REPOSITORY].index(typename)][2]


def _get_file_using_cache(filename, closure, force=False, allow_refresh=True):
    """
    Uses the Invenio cache, i.e. the tempdir, to see if there's a recent
    cached version of the sought-after file in there. If not, use the closure to
    compute a new, and return that instead. Relies on Invenio configuration
    parameter WEBSTAT_CACHE_INTERVAL.

    @param filename: The name of the file that might be cached
    @type filename: str

    @param closure: A function, that executed will return data to be cached. The
                    function should return either a string, or something that
                    makes sense after being interpreted with str().
    @type closure: function

    @param force: Override cache default value.
    @type force: bool


    """
    # Absolute path to cached files, might not exist.
    filename = os.path.normpath(WEBSTAT_RAWDATA_DIRECTORY + filename)

    # Get the modification time of the cached file (if any).
    try:
        mtime = os.path.getmtime(filename)
    except OSError:
        # No cached version of this particular file exists, thus the
        # modification time is set to 0 for easy logic below.
        mtime = 0

    # Consider refreshing cache if FORCE or NO CACHE AT ALL,
    # or CACHE EXIST AND REFRESH IS ALLOWED.
    if force or mtime == 0 or (mtime > 0 and allow_refresh):

        # Is the file modification time recent enough?
        if force or (time.time() - mtime > WEBSTAT_CACHE_INTERVAL):

            # No! Use closure to compute new content
            content = closure(False)

            # Cache the data
            open(filename, 'w').write(str(content))

    # Return the (perhaps just) cached file
    return open(filename, 'r')


def _is_scheduled_for_cacheing(event_id):
    """
    @param event_id: The event id
    @type event_id: str

    @return: Indication of if the event id is scheduling for BibSched execution.
    @type: bool
    """
    if not is_task_scheduled('webstatadmin'):
        return False

    # Get the task id
    try:
        task_id = get_task_ids_by_descending_date('webstatadmin',
                                                  ['RUNNING', 'WAITING'])[0]
    except IndexError:
        return False
    else:
        args = get_task_options(task_id)
        return event_id in (args['keyevents'] + args['customevents'])
