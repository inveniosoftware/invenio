# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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
BibCatalog task

Based on configured plug-ins this task will create tickets for records.
"""
import sys
import getopt
import os
import traceback

from invenio.legacy.bibsched.bibtask import \
    task_init, \
    task_set_option, \
    task_get_option, write_message, \
    task_update_progress, \
    task_sleep_now_if_required
from invenio.config import \
    CFG_VERSION, \
    CFG_PYLIBDIR
from invenio.legacy.docextract.task import \
    split_ids, \
    fetch_last_updated, \
    store_last_updated
from invenio.legacy.search_engine import \
    get_collection_reclist, \
    perform_request_search
from invenio.legacy.bibcatalog.api import BIBCATALOG_SYSTEM
from invenio.legacy.bibcatalog.utils import record_id_from_record
from invenio.legacy.bibcatalog.dblayer import \
    get_all_new_records, \
    get_all_modified_records
from invenio.legacy.bibedit.utils import get_bibrecord
from invenio.pluginutils import PluginContainer


class BibCatalogPluginException(Exception):
    """Raised when something is wrong with ticket plugins"""


class BibCatalogTicket(object):
    """
    Represents a Ticket to create using BibCatalog API.
    """
    def __init__(self, subject="", body="", queue="", ticketid=None, recid=-1):
        self.subject = subject
        self.queue = queue
        self.body = body
        self.ticketid = ticketid
        self.recid = recid

    def __repr__(self):
        return "<BibCatalogTicket(subject=%(subject)s,queue=%(queue)s,recid=%(recid)s)>" % {
            "subject": self.subject,
            "queue": self.queue,
            "recid": self.recid
        }

    def submit(self):
        """
        Submits the ticket using BibCatalog API.

        @raise Exception: if ticket creation is not successful.
        @return bool: True if created, False if not.
        """
        if not self.exists():
            self.ticketid = BIBCATALOG_SYSTEM.ticket_submit(
                                                  subject=self.subject,
                                                  queue=self.queue,
                                                  text=self.body,
                                                  recordid=self.recid)
            return True
        return False

    def exists(self):
        """
        Does the ticket already exist in the RT system?

        @return results: Evaluates to True if it exists, False if not.
        """
        results = BIBCATALOG_SYSTEM.ticket_search(None,
                                                  recordid=self.recid,
                                                  queue=self.queue,
                                                  subject=self.subject)
        return results


def task_check_options():
    """ Reimplement this method for having the possibility to check options
    before submitting the task, in order for example to provide default
    values. It must return False if there are errors in the options.
    """
    if not task_get_option('new') \
            and not task_get_option('modified') \
            and not task_get_option('recids') \
            and not task_get_option('collections')\
            and not task_get_option('reportnumbers'):
        print >>sys.stderr, 'Error: No records specified, you need' \
            ' to specify which records to run on'
        return False

    ticket_plugins = {}
    all_plugins, error_messages = load_ticket_plugins()

    if error_messages:
        # We got broken plugins. We alert only for now.
        print >>sys.stderr, "\n".join(error_messages)

    if task_get_option('tickets'):
        # Tickets specified
        for ticket in task_get_option('tickets'):
            if ticket not in all_plugins.get_enabled_plugins():
                print ticket
                print >>sys.stderr, 'Error: plugin %s is broken or does not exist'
                return False
            ticket_plugins[ticket] = all_plugins[ticket]
    elif task_get_option('all-tickets'):
        ticket_plugins = all_plugins.get_enabled_plugins()
    else:
        print >>sys.stderr, 'Error: No tickets specified, you need' \
            ' to specify at least one ticket type to create'
        return False

    task_set_option('tickets', ticket_plugins)

    if not BIBCATALOG_SYSTEM:
        print >>sys.stderr, 'Error: no cataloging system defined'
        return False

    res = BIBCATALOG_SYSTEM.check_system()
    if res:
        print >>sys.stderr, 'Error while checking cataloging system: %s' % \
            (res,)
    return True


def task_parse_options(key, value, opts, args):   # pylint: disable-msg=W0613
    """ Must be defined for bibtask to create a task """
    if args:
        # There should be no standalone arguments for any bibcatalog job
        # This will catch args before the job is shipped to Bibsched
        raise StandardError("Error: Unrecognised argument '%s'." % args[0])

    if key in ('-a', '--new'):
        task_set_option('new', True)
    elif key in ('-m', '--modified'):
        task_set_option('modified', True)
    elif key in ('-c', '--collections'):
        collections = task_get_option('collections')
        if not collections:
            collections = set()
            task_set_option('collections', collections)
        for v in value.split(","):
            collections.update(get_collection_reclist(v))
    elif key in ('-i', '--recids'):
        recids = task_get_option('recids')
        if not recids:
            recids = set()
            task_set_option('recids', recids)
        recids.update(split_ids(value))
    elif key in ('--tickets',):
        tickets = task_get_option('tickets')
        if not tickets:
            tickets = set()
            task_set_option('tickets', tickets)
        for item in value.split(','):
            tickets.add(item.strip())
    elif key in ('--all-tickets',):
        task_set_option('all-tickets', True)
    elif key in ('-q', '--query'):
        query = task_get_option('query')
        if not query:
            query = set()
            task_set_option('query', query)
        query.add(value)
    elif key in ('-r', '--reportnumbers'):
        reportnumbers = task_get_option('reportnumbers')
        if not reportnumbers:
            reportnumbers = set()
            task_set_option('reportnumbers', reportnumbers)
        reportnumbers.add(value)
    return True


def task_run_core():
    """
    Main daemon task.

    Returns True when run successfully. False otherwise.
    """
    # Dictionary of "plugin_name" -> func
    tickets_to_apply = task_get_option('tickets')
    write_message("Ticket plugins found: %s" %
                  (str(tickets_to_apply),), verbose=9)

    task_update_progress("Loading records")
    records_concerned = get_recids_to_load()
    write_message("%i record(s) found" %
                  (len(records_concerned),))

    records_processed = 0
    for record, last_date in load_records_from_id(records_concerned):
        records_processed += 1
        recid = record_id_from_record(record)
        task_update_progress("Processing records %s/%s (%i%%)"
                             % (records_processed, len(records_concerned),
                                int(float(records_processed) / len(records_concerned) * 100)))
        task_sleep_now_if_required(can_stop_too=True)
        for ticket_name, plugin in tickets_to_apply.items():
            if plugin:
                write_message("Running template %s for %s" % (ticket_name, recid),
                              verbose=5)
                try:
                    ticket = BibCatalogTicket(recid=int(recid))
                    if plugin['check_record'](ticket, record):
                        ticket = plugin['generate_ticket'](ticket, record)
                        write_message("Ticket to be generated: %s" % (ticket,), verbose=5)
                        res = ticket.submit()
                        if res:
                            write_message("Ticket #%s created for %s" %
                                         (ticket.ticketid, recid))
                        else:
                            write_message("Ticket already exists for %s" %
                                          (recid,))
                    else:
                        write_message("Skipping record %s", (recid,))
                except Exception, e:
                    write_message("Error submitting ticket for record %s:" % (recid,))
                    write_message(traceback.format_exc())
                    raise e
            else:
                raise BibCatalogPluginException("Plugin not valid in %s" % (ticket_name,))

        if last_date:
            store_last_updated(recid, last_date, name="bibcatalog")

    write_message("%i record(s) processed" %
                 (len(records_concerned),))
    return True


def load_ticket_plugins():
    """
    Will load all the ticket plugins found under CFG_BIBCATALOG_PLUGIN_DIR.

    Returns a tuple of plugin_object, list of errors.
    """
    # TODO add to configfile
    CFG_BIBCATALOG_PLUGIN_DIR = os.path.join(CFG_PYLIBDIR,
                                             "invenio",
                                             "bibcatalog_ticket_templates",
                                             "*.py")
    # Load plugins
    plugins = PluginContainer(CFG_BIBCATALOG_PLUGIN_DIR,
                              plugin_builder=_bibcatalog_plugin_builder)

    # Remove __init__ if applicable
    try:
        plugins.disable_plugin("__init__")
    except KeyError:
        pass

    error_messages = []
    # Check for broken plug-ins
    broken = plugins.get_broken_plugins()
    if broken:
        error_messages = []
        for plugin, info in broken.items():
            error_messages.append("Failed to load %s:\n"
                                  " %s" % (plugin, "".join(traceback.format_exception(*info))))
    return plugins, error_messages


def get_recids_to_load():
    """
    Generates the final list of record IDs to load.

    Returns a list of tuples like: (recid, date)
    """
    recids_given = task_get_option("recids", default=[])
    query_given = task_get_option("query")
    reportnumbers_given = task_get_option("reportnumbers")
    if query_given:
        write_message("Performing given search query: %s" % (query_given,))
        result = perform_request_search(p=query_given,
                                        of='id',
                                        rg=0,
                                        wl=0)
        recids_given.extend(result)

    if reportnumbers_given:
        write_message("Searching for records referring to given reportnumbers")
        for reportnumber in reportnumbers_given:
            result = perform_request_search(p='reportnumber:%s' % (reportnumber,),
                                            of='id',
                                            rg=0,
                                            wl=0)
            recids_given.extend(result)

    recids_given = [(recid, None) for recid in recids_given]

    last_id, last_date = fetch_last_updated(name="bibcatalog")
    records_found = []
    if task_get_option("new", default=False):
        records_found.extend(get_all_new_records(since=last_date, last_id=last_id))
    if task_get_option("modified", default=False):
        records_found.extend(get_all_modified_records(since=last_date, last_id=last_id))

    for recid, date in records_found:
        recids_given.append((recid, date))
    return recids_given


def load_records_from_id(records):
    """
    Given a record tuple of record id and last updated/created date,
    this function will yield a tuple with the record id replaced with
    a record structure iterativly.

    @param record: tuple of (recid, date-string) Ex: (1, 2012-12-12 12:12:12)
    @type record: tuple

    @yield: tuple of (record structure (dict), date-string)
    """
    for recid, date in records:
        record = get_bibrecord(int(recid))
        if not record:
            write_message("Error: could not load record %s" % (recid,))
            continue
        yield record, date


def _bibcatalog_plugin_builder(plugin_name, plugin_code):  # pylint: disable-msg=W0613
    """
    Custom builder for pluginutils.

    @param plugin_name: the name of the plugin.
    @type plugin_name: string
    @param plugin_code: the code of the module as just read from
        filesystem.
    @type plugin_code: module
    @return: the plugin
    """
    final_plugin = {}
    final_plugin["check_record"] = getattr(plugin_code, "check_record", None)
    final_plugin["generate_ticket"] = getattr(plugin_code, "generate_ticket", None)
    return final_plugin


def main():
    """Constructs the BibCatalog bibtask."""
    usage = """

  Non-daemon options:

  -l, --list-tickets      List available tickets.


  Scheduled (daemon) options:

  Selection of records (Required):

  -a, --new               Run on all newly inserted records.
  -m, --modified          Run on all newly modified records.
  -i, --recids=           Record id for extraction.
  -c, --collections=      Run on all records in a specific collection.
  -q, --query=            Specify a search query to fetch records to run on.
  -r, --reportnumbers=    Run on all records related with specific arXiv ids.

  Selection of tickets (Required):

  --tickets=         Specify which tickets to run.
  --all-tickets      Run on all tickets

  Examples:
   (run a periodical daemon job on a given ticket template)
      bibcatalog -a --tickets metadata_curation -s1h
   (run all tickets on a set of records)
      bibcatalog --recids 1,2 -i 3 --all-tickets
   (run some tickets on a collection)
      bibcatalog --collections "Articles" --tickets metadata_curation,reference_curation

    """
    try:
        opts, dummy = getopt.getopt(sys.argv[1:], "l", ["list-tickets"])
    except getopt.GetoptError:
        opts = []

    for opt, dummy in opts:
        if opt in ["-l", "--list-tickets"]:
            all_plugins, error_messages = load_ticket_plugins()
            if error_messages:
                # We got broken plugins. We alert only for now.
                print >>sys.stderr, "\n".join(error_messages)
            print "Enabled tickets:"
            for plugin in all_plugins.get_enabled_plugins():
                print " " + plugin
            print "Run `$ bibcatalog --tickets=<ticket-name>` to select a ticket template."
            return

    # Build and submit the task
    task_init(authorization_action='runbibcatalog',
              authorization_msg="BibCatalog Task Submission",
              description="",
              help_specific_usage=usage,
              version="Invenio v%s" % CFG_VERSION,
              specific_params=("hVv:i:c:q:r:am",
                                ["help",
                                 "version",
                                 "verbose=",
                                 "recids=",
                                 "collections=",
                                 "query=",
                                 "reportnumbers=",
                                 "new",
                                 "modified",
                                 "tickets=",
                                 "all-tickets"]),
              task_submit_elaborate_specific_parameter_fnc=task_parse_options,
              task_submit_check_options_fnc=task_check_options,
              task_run_fnc=task_run_core)
