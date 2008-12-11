# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibClassify daemon.

FIXME: the code below requires collection table to be updated to add column:
   clsMETHOD_fk mediumint(9) unsigned NOT NULL,
This is not clean and should be fixed.
"""

import sys
import time
import os

from invenio.dbquery import run_sql
from invenio.bibtask import task_init, write_message, task_update_progress, \
    task_set_option, task_get_option, task_sleep_now_if_required, \
    task_get_task_param
from invenio.bibclassify_engine import output_keywords_for_local_file
from invenio.config import CFG_BINDIR, CFG_TMPDIR
from invenio.intbitset import intbitset
from invenio.search_engine import get_collection_reclist
from invenio.bibdocfile import BibRecDocs
from invenio.bibclassify_text_extractor import is_pdf
from invenio.config import CFG_VERSION

# Global variables allowing to retain the progress of the task.
_index = 0
_recids_number = 0

def _ontology_exists(ontology_name):
    """Check if the ontology name is registered in the database."""
    if run_sql("SELECT name FROM clsMETHOD WHERE name=%s",
        (ontology_name,)):
        return True
    return False

def _collection_exists(collection_name):
    """Check if the collection name is registered in the database."""
    if run_sql("SELECT name FROM collection WHERE name=%s",
        (collection_name,)):
        return True
    return False

def _recid_exists(recid):
    """Check if the recid number is registered in the database."""
    if run_sql("SELECT id FROM bibrec WHERE id=%s",
        (recid,)):
        return True
    return False

def get_recids_foreach_ontology(recids=None, collections=None, taxonomy=None):
    """Returns an array containing hash objects containing the
    collection, its corresponding ontology and the records belonging to
    the given collection."""
    rec_onts = []

    # User specified record IDs.
    if recids:
        rec_onts.append({
            'ontology': taxonomy,
            'collection': None,
            'recIDs': recids,
        })
        return rec_onts

    # User specified collections.
    if collections:
        for collection in collections:
            records = get_collection_reclist(collection)
            if records:
                rec_onts.append({
                    'ontology': taxonomy,
                    'collection': collection,
                    'recIDs': records
                })
        return rec_onts

    # Use rules found in collection_clsMETHOD.
    result = run_sql("SELECT clsMETHOD.name, clsMETHOD.last_updated, "
        "collection.name FROM clsMETHOD JOIN collection_clsMETHOD ON "
        "clsMETHOD.id=id_clsMETHOD JOIN collection ON "
        "id_collection=collection.id")

    for ontology, date_last_run, collection in result:
        records = get_collection_reclist(collection)
        if records:
            if not date_last_run:
                write_message("INFO: Collection %s has not been previously "
                    "analyzed." % collection, stream=sys.stderr, verbose=3)
                modified_records = intbitset(run_sql("SELECT id FROM bibrec"))
            else:
                modified_records = intbitset(run_sql("SELECT id FROM bibrec "
                    "WHERE modification_date >= %s", (date_last_run, )))
            records &= modified_records
            if records:
                rec_onts.append({
                    'ontology': ontology,
                    'collection': collection,
                    'recIDs': records
                })
            else:
                write_message("WARNING: All records from collection '%s' have "
                    "already been analyzed for keywords with ontology '%s' "
                    "on %s." % (collection, ontology, date_last_run),
                    stream=sys.stderr, verbose=2)
        else:
            write_message("ERROR: Collection '%s' doesn't contain any record. "
                "Cannot analyse keywords." % (ontology, collection),
                stream=sys.stderr, verbose=0)

    return rec_onts

def update_date_of_last_run(runtime):
    """Update bibclassify daemon table information about last run time."""
    run_sql("UPDATE clsMETHOD SET last_updated=%s", (runtime,))

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """Given the string key it checks it's meaning, eventually using the
    value. Usually it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    eg:
    if key in ('-n', '--number'):
        task_get_option(\1) = value
        return True
    return False
    """

    # Recid option
    if key in ("-i", "--recid"):
        try:
            value = int(value)
        except ValueError:
            print >> sys.stderr, ("The value specified for --recid must be a "
                "valid integer, not '%s'." % value)
        if not _recid_exists(value):
            print >> sys.stderr, ("'%s' is not a valid record ID." % value)
            return False
        recids = task_get_option("recids")
        recids = recids or []
        recids.append(value)
        task_set_option("recids", recids)

    # Collection option
    elif key in ("-c", "--collection"):
        if not _collection_exists(value):
            print >> sys.stderr, ("'%s' is not a valid collection." % value)
            return False
        collections = task_get_option("collections")
        collections = collections or []
        collections.append(value)
        task_set_option("collections", collections)

    # Taxonomy option
    elif key in ("-k", "--taxonomy"):
        if not _ontology_exists(value):
            print >> sys.stderr, ("'%s' is not a valid taxonomy name." % value)
            return False
        task_set_option("taxonomy", value)
    else:
        return False

    return True

def task_run_core():
    """Runs anayse_documents for each ontology, collection, record ids
    set."""
    automated_daemon_mode_p = True
    recids = task_get_option('recids')
    collections = task_get_option('collections')
    taxonomy = task_get_option('taxonomy')

    if recids or collections:
        # We want to run some records/collection only, so we are not
        # in the automated daemon mode; this will be useful later.
        automated_daemon_mode_p = False

    # Check if the user specified which documents to extract keywords from.
    if recids:
        onto_recids = get_recids_foreach_ontology(recids=recids,
            taxonomy=taxonomy)
    elif collections:
        onto_recids = get_recids_foreach_ontology(collections=collections,
            taxonomy=taxonomy)
    else:
        onto_recids = get_recids_foreach_ontology()

    if not onto_recids:
        # Nothing to do.
        if automated_daemon_mode_p:
            update_date_of_last_run(task_get_task_param('task_starting_time'))
        return 1

    changes = []
    changes.append('<?xml version="1.0" encoding="UTF-8"?>')
    changes.append('<collection xmlns="http://www.loc.gov/MARC21/slim">')

    # Count the total number of records in order to update the progression.
    global _recids_number
    for onto_rec in onto_recids:
        _recids_number += len(onto_rec['recIDs'])

    for onto_rec in onto_recids:
        task_sleep_now_if_required(can_stop_too=False)
        write_message('INFO: Applying taxonomy %s to collection %s (%s '
            'records)' % (onto_rec['ontology'], onto_rec['collection'],
            len(onto_rec['recIDs'])), stream=sys.stderr, verbose=0)
        if onto_rec['recIDs']:
            changes.append(analyze_documents(onto_rec['recIDs'],
                onto_rec['ontology'], onto_rec['collection']))

    changes.append('</collection>')

    # Write the changes to a temporary file.
    tmp_directory = "%s/bibclassify" % CFG_TMPDIR
    filename = "bibclassifyd_%s.xml" % time.strftime("%Y%m%d%H%M%S",
        time.localtime())
    abs_path = tmp_directory + os.sep + filename

    if not os.path.isdir(tmp_directory):
        os.mkdir(tmp_directory)

    file_desc = open(abs_path, "w")
    file_desc.write('\n'.join(changes))
    file_desc.close()

    # Apply the changes.
    if changes:
        cmd = "%s/bibupload -n -c '%s' " % (CFG_BINDIR, abs_path)
        errcode = 0
        try:
            errcode = os.system(cmd)
        except OSError, exc:
            write_message('ERROR: Command %s failed [%s].' % (cmd, exc),
                stream=sys.stderr, verbose=0)
        if errcode != 0:
            write_message("ERROR: %s failed, error code is %d." %
                (cmd, errcode), stream=sys.stderr, verbose=0)
            return 0

    # Update the date of last run in the clsMETHOD table, but only if
    # we were running in an automated mode.
    if automated_daemon_mode_p:
        update_date_of_last_run(task_get_task_param('task_starting_time'))
    return 1

def analyze_documents(records, ontology, collection):
    """For each collection, parse the documents attached to the records
    in collection with the corresponding ontology."""
    global _index
    global _recids_number

    if not records:
        # No records could be found.
        write_message("WARNING: No record were found in collection %s." %
            collection, stream=sys.stderr, verbose=2)
        return False

    # Process records:
    output = []
    for record in records:
        bibdocfiles = BibRecDocs(record).list_latest_files()
        output.append('<record>')
        output.append('<controlfield tag="001">%s</controlfield>' % record)
        for doc in bibdocfiles:
            # Get the keywords for each PDF document contained in the record.
            if is_pdf(doc.get_full_path()):
                write_message('INFO: Generating keywords for record %d.' %
                    record, stream=sys.stderr, verbose=3)
                fulltext = doc.get_full_path()

                output.append(output_keywords_for_local_file(fulltext,
                    taxonomy=ontology, output_mode="marcxml", output_limit=3,
                    match_mode="partial", with_author_keywords=True,
                    verbose=task_get_option('verbose')))

        _index += 1

        output.append('</record>')

        task_update_progress('Done %d out of %d.' % (_index, _recids_number))
        task_sleep_now_if_required(can_stop_too=False)

    return '\n'.join(output)

def task_submit_check_options():
    """Required by bibtask. Checks the options."""
    recids = task_get_option('recids')
    collections = task_get_option('collections')
    taxonomy = task_get_option('taxonomy')

    # If a recid or a collection is specified, check that the taxonomy
    # is also specified.
    if (recids is not None or collections is not None) and \
        taxonomy is None:
        print >> sys.stderr, ("When specifying a record ID or a collection, "
            "you have to precise which\ntaxonomy to use.")
        return False

    return True

def bibclassify_daemon():
    """Constructs the bibclassify bibtask."""
    task_init(authorization_action='runbibclassify',
        authorization_msg="BibClassify Task Submission",
        description="Extract keywords and create a BibUpload "
            "task.\nExamples:\n"
            "    $ bibclassify\n"
            "    $ bibclassify -i 79 -k HEP\n"
            "    $ bibclassify -c 'Articles' -k HEP\n",
        help_specific_usage="  -i, --recid\t\tkeywords are extracted from "
        "this record\n"
        "  -c, --collection\t\tkeywords are extracted from this collection\n"
        "  -k, --taxonomy\t\tkeywords are based on that reference",
        version="CDS Invenio v%s" % CFG_VERSION,
        specific_params=("i:c:k:",
            [
             "recid=",
             "collection=",
             "taxonomy=",
            ]),
        task_submit_elaborate_specific_parameter_fnc=
            task_submit_elaborate_specific_parameter,
        task_submit_check_options_fnc=task_submit_check_options,
        task_run_fnc=task_run_core)

# FIXME: outfiledesc can be multiple files, e.g. when processing
#    100000 records it is good to store results by 1000 records
#    (see oaiharvest)
