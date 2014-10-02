# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
Refextract task

Sends references to parse through bibsched
"""

import sys
import os
from datetime import datetime, timedelta
from tempfile import mkstemp

from invenio.bibtask import task_init, task_set_option, \
                            task_get_option
from invenio.config import CFG_VERSION, \
                           CFG_SITE_SECURE_URL, \
                           CFG_REFEXTRACT_TICKET_QUEUE, \
                           CFG_INSPIRE_SITE, \
                           CFG_TMPSHAREDDIR
from invenio.dbquery import run_sql
from invenio.search_engine import perform_request_search
# Help message is the usage() print out of how to use Refextract
from invenio.refextract_cli import HELP_MESSAGE, DESCRIPTION
from invenio.refextract_api import extract_references_from_record, \
                                   FullTextNotAvailable, \
                                   record_can_extract_refs, \
                                   record_can_overwrite_refs
from invenio.refextract_config import CFG_REFEXTRACT_FILENAME
from invenio.bibtask import task_low_level_submission
from invenio.docextract_task import task_run_core_wrapper, \
                                    split_ids
from invenio.docextract_utils import setup_loggers, write_message
from invenio.docextract_record import print_records
from invenio.bibedit_utils import get_bibrecord
from invenio.bibrecord import record_get_field_instances, \
                              field_get_subfield_values
from invenio.bibcatalog import BIBCATALOG_SYSTEM


class NotSafeForExtraction(Exception):
    pass


def check_options():
    """ Reimplement this method for having the possibility to check options
    before submitting the task, in order for example to provide default
    values. It must return False if there are errors in the options.
    """
    if not task_get_option('new') \
            and not task_get_option('recids') \
            and not task_get_option('collections'):
        print >>sys.stderr, 'Error: No records specified, you need' \
            ' to specify which files to run on'
        return False

    return True


def cb_parse_option(key, value, opts, args):
    """ Must be defined for bibtask to create a task """
    if args and len(args) > 0:
        # There should be no standalone arguments for any refextract job
        # This will catch args before the job is shipped to Bibsched
        raise StandardError("Error: Unrecognised argument '%s'." % args[0])

    if key in ('-a', '--new'):
        task_set_option('new', True)
        task_set_option('no-overwrite', True)
    elif key == '--inspire':
        msg = """The --inspire option does not exist anymore.
Please set the config variable CFG_INSPIRE_SITE instead."""
        raise StandardError(msg)
    elif key in ('--create-ticket', ):
        task_set_option('create-ticket', True)
    elif key in ('--no-overwrite', ):
        msg = """The --no-overwrite option does not exist anymore.
This option is set by default. Please use --overwrite to overwrite references."""
        raise StandardError(msg)
    elif key in ('--overwrite', ):
        task_set_option('overwrite', True)
    elif key in ('-c', '--collections'):
        collections = task_get_option('collections')
        if not collections:
            collections = set()
            task_set_option('collections', collections)
        for v in value.split(","):
            collections.update(perform_request_search(c=v))
    elif key in ('-i', '--id'):
        recids = task_get_option('recids')
        if not recids:
            recids = set()
            task_set_option('recids', recids)
        recids.update(split_ids(value))
    elif key in ('-r', '--recids'):
        msg = """The --recids has been renamed.
please use --id for specifying recids."""
        raise StandardError(msg)
    elif key == '-f':
        msg = """refextract is now used to run in daemon mode only.
If you would like to run reference extraction on a standalone PDF file,
please use "docextract file.pdf\""""
        raise StandardError(msg)

    return True


def create_ticket(recid, bibcatalog_system, queue=CFG_REFEXTRACT_TICKET_QUEUE):
    write_message('ticket system: %s' % bibcatalog_system.__class__.__name__)
    write_message('queue: %s' % queue)
    if bibcatalog_system and queue:
        results = bibcatalog_system.ticket_search(None,
                                                  recordid=recid,
                                                  queue=queue)
        if results:
            write_message("Ticket #%s found" % results[0])
        else:
            _create_ticket(recid, bibcatalog_system, queue)


def _create_ticket(recid, bibcatalog_system, queue):
    subject = "Refs for #%s" % recid

    if CFG_INSPIRE_SITE:
        # Add report number in the subjecet
        report_number = ""
        record = get_bibrecord(recid)

        in_core = False
        for collection_tag in record_get_field_instances(record, "980"):
            for collection in field_get_subfield_values(collection_tag, 'a'):
                if collection == 'CORE':
                    in_core = True
                if collection == 'arXiv':
                    # Do not create tickets for arxiv papers
                    # Tickets for arxiv papers are created in bibcatelog
                    write_message("arXiv paper", verbose=1)
                    return

        # Only create tickets for CORE papers
        if not in_core:
            write_message("not in core papers", verbose=1)
            return

        # Do not create tickets for old records
        creation_date = run_sql("""SELECT creation_date FROM bibrec
                                   WHERE id = %s""", [recid])[0][0]
        if creation_date < datetime.now() - timedelta(days=30*4):
            return

        for report_tag in record_get_field_instances(record, "037"):
            for report_number in field_get_subfield_values(report_tag, 'a'):
                subject += " " + report_number
                break

    text = '%s/record/edit/#state=edit&recid=%s' % (CFG_SITE_SECURE_URL,
                                                    recid)
    bibcatalog_system.ticket_submit(subject=subject,
                                    queue=queue,
                                    text=text,
                                    recordid=recid)


def task_run_core(recid, records, bibcatalog_system=None):
    setup_loggers(None, use_bibtask=True)
    try:
        extract_one(recid=recid,
                    records=records,
                    overwrite=task_get_option('overwrite'),
                    create_a_ticket=task_get_option('new') or task_get_option('create-ticket'),
                    bibcatalog_system=bibcatalog_system)
    except FullTextNotAvailable:
        write_message("No full text available for %s" % recid)
    except NotSafeForExtraction:
        write_message('Record not safe for re-extraction, skipping')


def extract_one(recid, records, overwrite=False, bibcatalog_system=None,
                create_a_ticket=False):
    msg = "Extracting references for %s" % recid
    if overwrite:
        write_message("%s (overwrite)" % msg)
        safe_to_extract = record_can_overwrite_refs(recid)
    else:
        write_message(msg)
        safe_to_extract = record_can_extract_refs(recid)

    if safe_to_extract:
        record = extract_references_from_record(recid)
        records.append(record)
        # Create a RT ticket if necessary
        if create_a_ticket:
            create_ticket(recid, bibcatalog_system)
    else:
        raise NotSafeForExtraction()



def cb_submit_bibupload(bibcatalog_system=None, records=None):
    if records:
        references_xml = print_records(records)

        # Save new record to file
        temp_fd, temp_path = mkstemp(prefix=CFG_REFEXTRACT_FILENAME,
                                     dir=CFG_TMPSHAREDDIR)
        with os.fdopen(temp_fd, 'w') as temp_file:
            temp_file.write(references_xml)

        # Update record
        task_low_level_submission('bibupload', 'refextract', '-c', temp_path)


def main():
    """Constructs the refextract bibtask."""
    extra_vars = {'bibcatalog_system': BIBCATALOG_SYSTEM, 'records': []}
    # Build and submit the task
    task_init(authorization_action='runrefextract',
        authorization_msg="Refextract Task Submission",
        description=DESCRIPTION,
        # get the global help_message variable imported from refextract.py
        help_specific_usage=HELP_MESSAGE + """

  Scheduled (daemon) options:
  -a, --new          Run on all newly inserted pdfs.
  -i, --id           Record id for extraction.
  -c, --collections  Entire Collection for extraction.

  Special (daemon) options:
  --create-ticket    Create a RT ticket for record references

  Examples:
   (run a daemon job)
      refextract --new
   (run on a set of records)
      refextract --id 1,2 -i 3
   (run on a collection)
      refextract --collections "Reports"
   (run as standalone)
      docextract -o /home/chayward/refs.xml /home/chayward/thesis.pdf

""",
        version="Invenio v%s" % CFG_VERSION,
        specific_params=("hVv:x:c:r:nai:f:",
                            ["help",
                             "version",
                             "verbose=",
                             "id=",
                             "recids=",
                             "collections=",
                             "new",
                             "inspire",
                             "overwrite",
                             "no-overwrite",
                             "create-ticket"]),
        task_submit_elaborate_specific_parameter_fnc=cb_parse_option,
        task_submit_check_options_fnc=check_options,
        task_run_fnc=task_run_core_wrapper('refextract',
                                           task_run_core,
                                           extra_vars=extra_vars,
                                           post_process=cb_submit_bibupload))
