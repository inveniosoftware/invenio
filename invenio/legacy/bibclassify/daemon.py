# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013, 2014 CERN.
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
BibClassify daemon.

FIXME: the code below requires collection table to be updated to add column:
   clsMETHOD_fk mediumint(9) unsigned NOT NULL,
This is not clean and should be fixed.

This module IS NOT standalone safe - it should never be run so.
"""

import sys
import time
import os

from invenio.legacy.bibclassify import config as bconfig
from invenio.legacy.bibclassify import text_extractor
from invenio.legacy.bibclassify import engine
from invenio.legacy.bibclassify import webinterface

from invenio.legacy.bibsched import bibtask
from invenio.legacy.dbquery import run_sql
from intbitset import intbitset
from invenio.legacy.search_engine import get_collection_reclist
from invenio.legacy.bibdocfile.api import BibRecDocs

# Global variables allowing to retain the progress of the task.
_INDEX = 0
_RECIDS_NUMBER = 0


# INTERFACE

def bibclassify_daemon():
    """Constructs the BibClassify bibtask."""
    bibtask.task_init(authorization_action='runbibclassify',
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
                      version="Invenio BibClassify v%s" % bconfig.VERSION,
                      specific_params=("i:c:k:f",
                                       [
                                           "recid=",
                                           "collection=",
                                           "taxonomy=",
                                           "force"
                                       ]),
                      task_submit_elaborate_specific_parameter_fnc=
                      _task_submit_elaborate_specific_parameter,
                      task_submit_check_options_fnc=_task_submit_check_options,
                      task_run_fnc=_task_run_core)


# PRIVATE METHODS

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


def _get_recids_foreach_ontology(recids=None, collections=None, taxonomy=None):
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
                bibtask.write_message(
                    "INFO: Collection %s has not been previously "
                    "analyzed." % collection, stream=sys.stderr, verbose=3)
                modified_records = intbitset(run_sql("SELECT id FROM bibrec"))
            elif bibtask.task_get_option('force'):
                bibtask.write_message(
                    "INFO: Analysis is forced for collection %s." %
                    collection, stream=sys.stderr, verbose=3)
                modified_records = intbitset(run_sql("SELECT id FROM bibrec"))
            else:
                modified_records = bibtask.get_modified_records_since(date_last_run)

            records &= modified_records
            if records:
                rec_onts.append({
                    'ontology': ontology,
                    'collection': collection,
                    'recIDs': records
                })
            else:
                bibtask.write_message(
                    "WARNING: All records from collection '%s' have "
                    "already been analyzed for keywords with ontology '%s' "
                    "on %s." % (collection, ontology, date_last_run),
                    stream=sys.stderr, verbose=2)
        else:
            bibtask.write_message(
                "ERROR: Collection '%s' doesn't contain any record. "
                "Cannot analyse keywords." % (collection,),
                stream=sys.stderr, verbose=0)

    return rec_onts


def _update_date_of_last_run(runtime):
    """Update bibclassify daemon table information about last run time."""
    run_sql("UPDATE clsMETHOD SET last_updated=%s", (runtime,))


def _task_submit_elaborate_specific_parameter(key, value, opts, args):
    """Given the string key it checks it's meaning, eventually using the
    value. Usually it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    eg:
    if key in ('-n', '--number'):
        bibtask.task_get_option(\1) = value
        return True
    return False
    """
    # Recid option
    if key in ("-i", "--recid"):
        try:
            value = int(value)
        except ValueError:
            bibtask.write_message("The value specified for --recid must be a "
                                  "valid integer, not '%s'." % value,
                                  stream=sys.stderr,
                                  verbose=0)
        if not _recid_exists(value):
            bibtask.write_message(
                "ERROR: '%s' is not a valid record ID." % value,
                stream=sys.stderr, verbose=0)
            return False
        recids = bibtask.task_get_option('recids')
        if recids is None:
            recids = []
        recids.append(value)
        bibtask.task_set_option('recids', recids)

    # Collection option
    elif key in ("-c", "--collection"):
        if not _collection_exists(value):
            bibtask.write_message(
                "ERROR: '%s' is not a valid collection." % value,
                stream=sys.stderr, verbose=0)
            return False
        collections = bibtask.task_get_option("collections")
        collections = collections or []
        collections.append(value)
        bibtask.task_set_option("collections", collections)

    # Taxonomy option
    elif key in ("-k", "--taxonomy"):
        if not _ontology_exists(value):
            bibtask.write_message(
                "ERROR: '%s' is not a valid taxonomy name." % value,
                stream=sys.stderr, verbose=0)
            return False
        bibtask.task_set_option("taxonomy", value)
    elif key in ("-f", "--force"):
        bibtask.task_set_option("force", True)
    else:
        return False

    return True


def _task_run_core():
    """Runs analyse_documents for each ontology, collection, record ids
    set."""

    automated_daemon_mode_p = True
    recids = bibtask.task_get_option('recids')
    collections = bibtask.task_get_option('collections')
    taxonomy = bibtask.task_get_option('taxonomy')

    if recids or collections:
        # We want to run some records/collection only, so we are not
        # in the automated daemon mode; this will be useful later.
        automated_daemon_mode_p = False

    # Check if the user specified which documents to extract keywords from.
    if recids:
        onto_recids = _get_recids_foreach_ontology(recids=recids,
                                                   taxonomy=taxonomy)
    elif collections:
        onto_recids = _get_recids_foreach_ontology(collections=collections,
                                                   taxonomy=taxonomy)
    else:
        onto_recids = _get_recids_foreach_ontology()

    if not onto_recids:
        # Nothing to do.
        if automated_daemon_mode_p:
            _update_date_of_last_run(
                bibtask.task_get_task_param('task_starting_time'))
        return 1

    # We will write to a temporary file as we go, because we might be processing
    # big collections with many docs
    _rid = time.strftime("%Y%m%d%H%M%S", time.localtime())
    abs_path = engine.get_tmp_file(_rid)
    fo = open(abs_path, 'w')

    fo.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    fo.write('<collection xmlns="http://www.loc.gov/MARC21/slim">\n')

    # Count the total number of records in order to update the progression.
    global _RECIDS_NUMBER
    for onto_rec in onto_recids:
        _RECIDS_NUMBER += len(onto_rec['recIDs'])

    rec_added = False

    for onto_rec in onto_recids:
        bibtask.task_sleep_now_if_required(can_stop_too=False)

        if onto_rec['collection'] is not None:
            bibtask.write_message(
                'INFO: Applying taxonomy %s to collection %s (%s '
                'records)' % (onto_rec['ontology'], onto_rec['collection'],
                              len(onto_rec['recIDs'])), stream=sys.stderr,
                verbose=3)
        else:
            bibtask.write_message('INFO: Applying taxonomy %s to recIDs %s. ' %
                                  (onto_rec['ontology'],
                                   ', '.join([str(recid) for recid in
                                              onto_rec['recIDs']])),
                                  stream=sys.stderr, verbose=3)
        if onto_rec['recIDs']:
            xml = _analyze_documents(onto_rec['recIDs'],
                                     onto_rec['ontology'],
                                     onto_rec['collection'])
            if len(xml) > 5:
                fo.write(xml)
                rec_added = True

    fo.write('</collection>\n')
    fo.close()

    # Apply the changes.
    if rec_added:
        if bconfig.CFG_DB_SAVE_KW:
            webinterface.upload_keywords(abs_path)
        else:
            bibtask.write_message(
                "INFO: CFG_DB_SAVE_KW is false, we don't save results",
                stream=sys.stderr, verbose=0)
    else:
        bibtask.write_message(
            "WARNING: No keywords found, recids: %s" % onto_recids,
            stream=sys.stderr, verbose=0)
        os.remove(abs_path)

    # Update the date of last run in the clsMETHOD table, but only if
    # we were running in an automated mode.
    if automated_daemon_mode_p:
        _update_date_of_last_run(
            bibtask.task_get_task_param('task_starting_time'))
    return 1


def _analyze_documents(records, taxonomy_name, collection,
                       output_limit=bconfig.CFG_BIBCLASSIFY_DEFAULT_OUTPUT_NUMBER):
    """For each collection, parse the documents attached to the records
    in collection with the corresponding taxonomy_name.
    @var records: list of recids to process
    @var taxonomy_name: str, name of the taxonomy, e.g. HEP
    @var collection: str, collection name
    @keyword output_limit: int, max number of keywords to extract [3]
    @return: str, marcxml output format of results
    """
    global _INDEX

    if not records:
        # No records could be found.
        bibtask.write_message(
            "WARNING: No records were found in collection %s." %
            collection, stream=sys.stderr, verbose=2)
        return False

    # Process records:
    output = []
    for record in records:
        bibdocfiles = BibRecDocs(
            record).list_latest_files()  # TODO: why this doesn't call list_all_files() ?
        keywords = {}
        akws = {}
        acro = {}
        single_keywords = composite_keywords = author_keywords = acronyms = None

        for doc in bibdocfiles:
            # Get the keywords for all PDF documents contained in the record.
            if text_extractor.is_pdf(doc.get_full_path()):
                bibtask.write_message(
                    'INFO: Generating keywords for record %d.' %
                    record, stream=sys.stderr, verbose=3)
                fulltext = doc.get_path()

                single_keywords, composite_keywords, author_keywords, acronyms = \
                    engine.get_keywords_from_local_file(fulltext,
                                                        taxonomy_name,
                                                        with_author_keywords=True,
                                                        output_mode="raw",
                                                        output_limit=output_limit,
                                                        match_mode='partial')
            else:
                bibtask.write_message('WARNING: BibClassify does not know how to process \
                    doc: %s (type: %s) -- ignoring it.' %
                                      (doc.fullpath, doc.doctype),
                                      stream=sys.stderr, verbose=3)

            if single_keywords or composite_keywords:
                cleaned_single = engine.clean_before_output(single_keywords)
                cleaned_composite = engine.clean_before_output(
                    composite_keywords)
                # merge the groups into one
                keywords.update(cleaned_single)
                keywords.update(cleaned_composite)
            acro.update(acronyms)
            akws.update(author_keywords)

        if len(keywords):
            output.append('<record>')
            output.append('<controlfield tag="001">%s</controlfield>' % record)
            output.append(engine._output_marc(keywords.items(), (), akws, acro,
                                              spires=bconfig.CFG_SPIRES_FORMAT))
            output.append('</record>')
        else:
            bibtask.write_message('WARNING: No keywords found for record %d.' %
                                  record, stream=sys.stderr, verbose=0)

        _INDEX += 1

        bibtask.task_update_progress(
            'Done %d out of %d.' % (_INDEX, _RECIDS_NUMBER))
        bibtask.task_sleep_now_if_required(can_stop_too=False)

    return '\n'.join(output)


def _task_submit_check_options():
    """Required by bibtask. Checks the options."""
    recids = bibtask.task_get_option('recids')
    collections = bibtask.task_get_option('collections')
    taxonomy = bibtask.task_get_option('taxonomy')

    # If a recid or a collection is specified, check that the taxonomy
    # is also specified.
    if (recids is not None or collections is not None) and \
                    taxonomy is None:
        bibtask.write_message(
            "ERROR: When specifying a record ID or a collection, "
            "you have to precise which\ntaxonomy to use.", stream=sys.stderr,
            verbose=0)
        return False

    return True

# FIXME: outfiledesc can be multiple files, e.g. when processing
#    100000 records it is good to store results by 1000 records
#    (see oaiharvest)
