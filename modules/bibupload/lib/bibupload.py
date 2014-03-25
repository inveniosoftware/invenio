# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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
BibUpload: Receive MARC XML file and update the appropriate database
tables according to options.
"""

__revision__ = "$Id$"

import os
import re
import sys
import time
from datetime import datetime
from zlib import compress
import socket
import marshal
import copy
import tempfile
import urlparse
import urllib2
import urllib

from invenio.config import CFG_OAI_ID_FIELD, \
     CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, \
     CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, \
     CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG, \
     CFG_BIBUPLOAD_STRONG_TAGS, \
     CFG_BIBUPLOAD_CONTROLLED_PROVENANCE_TAGS, \
     CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE, \
     CFG_BIBUPLOAD_DELETE_FORMATS, \
     CFG_SITE_URL, \
     CFG_SITE_SECURE_URL, \
     CFG_SITE_RECORD, \
     CFG_OAI_PROVENANCE_ALTERED_SUBFIELD, \
     CFG_BIBUPLOAD_DISABLE_RECORD_REVISIONS, \
     CFG_BIBUPLOAD_CONFLICTING_REVISION_TICKET_QUEUE, \
     CFG_CERN_SITE, \
     CFG_BIBUPLOAD_MATCH_DELETED_RECORDS

from invenio.jsonutils import json, CFG_JSON_AVAILABLE
from invenio.bibupload_config import CFG_BIBUPLOAD_CONTROLFIELD_TAGS, \
    CFG_BIBUPLOAD_SPECIAL_TAGS, \
    CFG_BIBUPLOAD_DELETE_CODE, \
    CFG_BIBUPLOAD_DELETE_VALUE, \
    CFG_BIBUPLOAD_OPT_MODES
from invenio.dbquery import run_sql
from invenio.bibrecord import create_records, \
                              record_add_field, \
                              record_delete_field, \
                              record_xml_output, \
                              record_get_field_instances, \
                              record_get_field_value, \
                              record_get_field_values, \
                              field_get_subfield_values, \
                              field_get_subfield_instances, \
                              record_modify_subfield, \
                              record_delete_subfield_from, \
                              record_delete_fields, \
                              record_add_subfield_into, \
                              record_find_field, \
                              record_extract_oai_id, \
                              record_extract_dois, \
                              record_has_field, \
                              records_identical, \
                              record_drop_duplicate_fields
from invenio.search_engine import get_record, record_exists, search_pattern
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.errorlib import register_exception
from invenio.bibcatalog import BIBCATALOG_SYSTEM
from invenio.intbitset import intbitset
from invenio.urlutils import make_user_agent_string
from invenio.textutils import wash_for_xml
from invenio.config import CFG_BIBDOCFILE_FILEDIR
from invenio.bibtask import task_init, write_message, \
    task_set_option, task_get_option, task_get_task_param, \
    task_update_progress, task_sleep_now_if_required, fix_argv_paths, \
    RecoverableError
from invenio.bibdocfile import BibRecDocs, file_strip_ext, normalize_format, \
    get_docname_from_url, check_valid_url, download_url, \
    KEEP_OLD_VALUE, decompose_bibdocfile_url, InvenioBibDocFileError, \
    bibdocfile_url_p, CFG_BIBDOCFILE_AVAILABLE_FLAGS, guess_format_from_url, \
    BibRelation, MoreInfo

from invenio.search_engine import search_pattern

from invenio.bibupload_revisionverifier import RevisionVerifier, \
                                               InvenioBibUploadConflictingRevisionsError, \
                                               InvenioBibUploadInvalidRevisionError, \
                                               InvenioBibUploadMissing005Error, \
                                               InvenioBibUploadUnchangedRecordError

#Statistic variables
stat = {}
stat['nb_records_to_upload'] = 0
stat['nb_records_updated'] = 0
stat['nb_records_inserted'] = 0
stat['nb_errors'] = 0
stat['nb_holdingpen'] = 0
stat['exectime'] = time.localtime()

_WRITING_RIGHTS = None

CFG_BIBUPLOAD_ALLOWED_SPECIAL_TREATMENTS = ('oracle', )

CFG_HAS_BIBCATALOG = "UNKNOWN"
def check_bibcatalog():
    """
    Return True if bibcatalog is available.
    """
    global CFG_HAS_BIBCATALOG # pylint: disable=W0603
    if CFG_HAS_BIBCATALOG != "UNKNOWN":
        return CFG_HAS_BIBCATALOG
    CFG_HAS_BIBCATALOG = True
    if BIBCATALOG_SYSTEM is not None:
        bibcatalog_response = BIBCATALOG_SYSTEM.check_system()
    else:
        bibcatalog_response = "No ticket system configured"
    if bibcatalog_response != "":
        write_message("BibCatalog error: %s\n" % (bibcatalog_response,))
        CFG_HAS_BIBCATALOG = False
    return CFG_HAS_BIBCATALOG

## Let's set a reasonable timeout for URL request (e.g. FFT)
socket.setdefaulttimeout(40)

def parse_identifier(identifier):
    """Parse the identifier and determine if it is temporary or fixed"""
    id_str = str(identifier)
    if not id_str.startswith("TMP:"):
        return (False, identifier)
    else:
        return (True, id_str[4:])

def resolve_identifier(tmps, identifier):
    """Resolves an identifier. If the identifier is not temporary, this
    function is an identity on the second argument. Otherwise, a resolved
    value is returned or an exception raised"""

    is_tmp, tmp_id = parse_identifier(identifier)
    if is_tmp:
        if not tmp_id in tmps:
            raise StandardError("Temporary identifier %s not present in the dictionary" % (tmp_id, ))
        if tmps[tmp_id] == -1:
            # the identifier has been signalised but never assigned a value - probably error during processing
            raise StandardError("Temporary identifier %s has been declared, but never assigned a value. Probably an error during processign of an appropriate FFT has happened. Please see the log" % (tmp_id, ))
        return int(tmps[tmp_id])
    else:
        return int(identifier)

_re_find_001 = re.compile('<controlfield\\s+tag=("001"|\'001\')\\s*>\\s*(\\d*)\\s*</controlfield>', re.S)
def bibupload_pending_recids():
    """This function embed a bit of A.I. and is more a hack than an elegant
    algorithm. It should be updated in case bibupload/bibsched are modified
    in incompatible ways.
    This function return the intbitset of all the records that are being
    (or are scheduled to be) touched by other bibuploads.
    """
    options = run_sql("""SELECT arguments FROM schTASK WHERE status<>'DONE' AND
        proc='bibupload' AND (status='RUNNING' OR status='CONTINUING' OR
        status='WAITING' OR status='SCHEDULED' OR status='ABOUT TO STOP' OR
        status='ABOUT TO SLEEP')""")
    ret = intbitset()
    xmls = []
    if options:
        for arguments in options:
            arguments = marshal.loads(arguments[0])
            for argument in arguments[1:]:
                if argument.startswith('/'):
                    # XMLs files are recognizable because they're absolute
                    # files...
                    xmls.append(argument)
    for xmlfile in xmls:
        # Let's grep for the 001
        try:
            xml = open(xmlfile).read()
            ret += [int(group[1]) for group in _re_find_001.findall(xml)]
        except:
            continue
    return ret

### bibupload engine functions:
def bibupload(record, opt_mode=None, opt_notimechange=0, oai_rec_id="", pretend=False,
        tmp_ids=None, tmp_vers=None):
    """Main function: process a record and fit it in the tables
    bibfmt, bibrec, bibrec_bibxxx, bibxxx with proper record
    metadata.

    Return (error_code, recID) of the processed record.
    """
    if tmp_ids is None:
        tmp_ids = {}
    if tmp_vers is None:
        tmp_vers = {}
    if opt_mode == 'reference':
        ## NOTE: reference mode has been deprecated in favour of 'correct'
        opt_mode = 'correct'

    assert(opt_mode in CFG_BIBUPLOAD_OPT_MODES)

    try:
        record_xml_output(record).decode('utf-8')
    except UnicodeDecodeError:
        msg = "    Failed: Invalid utf-8 characters."
        write_message(msg, verbose=1, stream=sys.stderr)
        return (1, -1, msg)


    error = None
    affected_tags = {}
    original_record = {}
    rec_old = {}
    now = datetime.now() # will hold record creation/modification date
    record_had_altered_bit = False
    is_opt_mode_delete = False

    # Extraction of the Record Id from 001, SYSNO or OAIID or DOI tags:
    rec_id = retrieve_rec_id(record, opt_mode, pretend=pretend)
    if rec_id == -1:
        msg = "    Failed: either the record already exists and insert was " \
            "requested or the record does not exists and " \
            "replace/correct/append has been used"
        write_message(msg, verbose=1, stream=sys.stderr)
        return (1, -1, msg)
    elif rec_id > 0:
        write_message("   -Retrieve record ID (found %s): DONE." % rec_id, verbose=2)
        (unique_p, msg) = check_record_doi_is_unique(rec_id, record)
        if not unique_p:
            write_message(msg, verbose=1, stream=sys.stderr)
            return (1, int(rec_id), msg)
        if not record.has_key('001'):
            # Found record ID by means of SYSNO or OAIID or DOI, and the
            # input MARCXML buffer does not have this 001 tag, so we
            # should add it now:
            error = record_add_field(record, '001', controlfield_value=rec_id)
            if error is None:
                msg = "   Failed: Error during adding the 001 controlfield "  \
                    "to the record"
                write_message(msg, verbose=1, stream=sys.stderr)
                return (1, int(rec_id), msg)
            else:
                error = None
            write_message("   -Added tag 001: DONE.", verbose=2)

            write_message("   -Check if the xml marc file is already in the database: DONE" , verbose=2)

    record_deleted_p = False
    if opt_mode == 'insert' or \
    (opt_mode == 'replace_or_insert') and rec_id is None:
        insert_mode_p = True
        # Insert the record into the bibrec databases to have a recordId
        rec_id = create_new_record(pretend=pretend)
        write_message("   -Creation of a new record id (%d): DONE" % rec_id, verbose=2)

        # we add the record Id control field to the record
        error = record_add_field(record, '001', controlfield_value=rec_id)
        if error is None:
            msg = "   Failed: Error during adding the 001 controlfield "  \
                  "to the record"
            write_message(msg, verbose=1, stream=sys.stderr)
            return (1, int(rec_id), msg)
        else:
            error = None

        if '005' not in record:
            error = record_add_field(record, '005', controlfield_value=now.strftime("%Y%m%d%H%M%S.0"))
            if error is None:
                msg = "   ERROR: during adding to 005 controlfield to record"
                write_message(msg, verbose=1, stream=sys.stderr)
                return (1, int(rec_id), msg)
            else:
                error = None
        else:
            write_message("   Note: 005 already existing upon inserting of new record. Keeping it.", verbose=2)

    elif opt_mode != 'insert':
        insert_mode_p = False
        # Update Mode
        # Retrieve the old record to update
        rec_old = get_record(rec_id)
        record_had_altered_bit = record_get_field_values(rec_old, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4], CFG_OAI_PROVENANCE_ALTERED_SUBFIELD)
        # Also save a copy to restore previous situation in case of errors
        original_record = get_record(rec_id)

        if rec_old is None:
            msg = "   Failed during the creation of the old record!"
            write_message(msg, verbose=1, stream=sys.stderr)
            return (1, int(rec_id), msg)
        else:
            write_message("   -Retrieve the old record to update: DONE", verbose=2)

        # flag to check whether the revisions have been verified and patch generated.
        # If revision verification failed, then we need to manually identify the affected tags
        # and process them
        revision_verified = False
        rev_verifier = RevisionVerifier()
        #check for revision conflicts before updating record
        if record_has_field(record, '005') and not CFG_BIBUPLOAD_DISABLE_RECORD_REVISIONS:
            write_message("     -Upload Record has 005. Verifying Revision", verbose=2)
            try:
                rev_res = rev_verifier.verify_revision(record, original_record, opt_mode)
                if rev_res:
                    opt_mode = rev_res[0]
                    record = rev_res[1]
                    affected_tags = rev_res[2]
                    revision_verified = True
                    write_message(lambda: "     -Patch record generated. Changing opt_mode to correct.\nPatch:\n%s " % record_xml_output(record), verbose=2)
                else:
                    write_message("     -No Patch Record.", verbose=2)
            except InvenioBibUploadUnchangedRecordError, err:
                msg = "     -ISSUE: %s" % err
                write_message(msg, verbose=1, stream=sys.stderr)
                write_message(msg, "     Continuing anyway in case there are FFT or other tags")
            except InvenioBibUploadConflictingRevisionsError, err:
                msg = "     -ERROR: Conflicting Revisions - %s" % err
                write_message(msg, verbose=1, stream=sys.stderr)
                submit_ticket_for_holding_pen(rec_id, err, "Conflicting Revisions. Inserting record into holding pen.", pretend=pretend)
                insert_record_into_holding_pen(record, str(rec_id), pretend=pretend)
                return (2, int(rec_id), msg)
            except InvenioBibUploadInvalidRevisionError, err:
                msg = "     -ERROR: Invalid Revision - %s" % err
                write_message(msg)
                submit_ticket_for_holding_pen(rec_id, err, "Invalid Revisions. Inserting record into holding pen.", pretend=pretend)
                insert_record_into_holding_pen(record, str(rec_id), pretend=pretend)
                return (2, int(rec_id), msg)
            except InvenioBibUploadMissing005Error, err:
                msg = "     -ERROR: Missing 005 - %s" % err
                write_message(msg)
                submit_ticket_for_holding_pen(rec_id, err, "Missing 005. Inserting record into holding pen.", pretend=pretend)
                insert_record_into_holding_pen(record, str(rec_id), pretend=pretend)
                return (2, int(rec_id), msg)
        else:
            write_message("     - No 005 Tag Present. Resuming normal flow.", verbose=2)

        # dictionaries to temporarily hold original recs tag-fields
        existing_tags = {}
        retained_tags = {}

        # in case of delete operation affected tags should be deleted in delete_bibrec_bibxxx
        # but should not be updated again in STAGE 4
        # utilising the below flag
        is_opt_mode_delete = False
        if not revision_verified:
            # either 005 was not present or opt_mode was not correct/replace
            # in this case we still need to find out affected tags to process
            write_message("     - Missing 005 or opt_mode!=Replace/Correct.Revision Verifier not called.", verbose=2)
            # Identify affected tags
            if opt_mode == 'correct' or opt_mode == 'replace' or opt_mode == 'replace_or_insert':
                rec_diff = rev_verifier.compare_records(record, original_record, opt_mode)
                affected_tags = rev_verifier.retrieve_affected_tags_with_ind(rec_diff)
            elif opt_mode == 'delete':
                # populate an intermediate dictionary
                # used in upcoming step related to 'delete' mode
                is_opt_mode_delete = True
                for tag, fields in original_record.iteritems():
                    existing_tags[tag] = [tag + (field[1] != ' ' and field[1] or '_') + (field[2] != ' ' and field[2] or '_') for field in fields]
            elif opt_mode == 'append':
                for tag, fields in record.iteritems():
                    if tag not in CFG_BIBUPLOAD_CONTROLFIELD_TAGS:
                        affected_tags[tag] = [(field[1], field[2]) for field in fields]

        # In Replace mode, take over old strong tags if applicable:
        if opt_mode == 'replace' or \
            opt_mode == 'replace_or_insert':
            copy_strong_tags_from_old_record(record, rec_old)

        # Delete tags to correct in the record
        if opt_mode == 'correct':
            delete_tags_to_correct(record, rec_old)
            write_message("   -Delete the old tags to correct in the old record: DONE",
                        verbose=2)

        # Delete tags specified if in delete mode
        if opt_mode == 'delete':
            record = delete_tags(record, rec_old)
            for tag, fields in record.iteritems():
                retained_tags[tag] = [tag + (field[1] != ' ' and field[1] or '_') + (field[2] != ' ' and field[2] or '_') for field in fields]
            #identify the tags that have been deleted
            for tag in existing_tags.keys():
                if tag not in retained_tags:
                    for item in existing_tags[tag]:
                        tag_to_add = item[0:3]
                        ind1, ind2 = item[3], item[4]
                        if tag_to_add in affected_tags and (ind1, ind2) not in affected_tags[tag_to_add]:
                            affected_tags[tag_to_add].append((ind1, ind2))
                        else:
                            affected_tags[tag_to_add] = [(ind1, ind2)]
                else:
                    deleted = list(set(existing_tags[tag]) - set(retained_tags[tag]))
                    for item in deleted:
                        tag_to_add = item[0:3]
                        ind1, ind2 = item[3], item[4]
                        if tag_to_add in affected_tags and (ind1, ind2) not in affected_tags[tag_to_add]:
                            affected_tags[tag_to_add].append((ind1, ind2))
                        else:
                            affected_tags[tag_to_add] = [(ind1, ind2)]

            write_message("   -Delete specified tags in the old record: DONE", verbose=2)

        # Append new tag to the old record and update the new record with the old_record modified
        if opt_mode == 'append' or opt_mode == 'correct':
            record = append_new_tag_to_old_record(record, rec_old)
            write_message("   -Append new tags to the old record: DONE", verbose=2)

        write_message("     -Affected Tags found after comparing upload and original records: %s"%(str(affected_tags)), verbose=2)

        # 005 tag should be added everytime the record is modified
        # If an exiting record is modified, its 005 tag should be overwritten with a new revision value
        if record.has_key('005'):
            record_delete_field(record, '005')
            write_message("  Deleted the existing 005 tag.", verbose=2)
        last_revision = run_sql("SELECT MAX(job_date) FROM hstRECORD WHERE id_bibrec=%s", (rec_id, ))[0][0]
        if last_revision and last_revision.strftime("%Y%m%d%H%M%S.0") == now.strftime("%Y%m%d%H%M%S.0"):
            ## We are updating the same record within the same seconds! It's less than
            ## the minimal granularity. Let's pause for 1 more second to take a breath :-)
            time.sleep(1)
            now = datetime.now()

        error = record_add_field(record, '005', controlfield_value=now.strftime("%Y%m%d%H%M%S.0"))
        if error is None:
            write_message("   Failed: Error during adding to 005 controlfield to record", verbose=1, stream=sys.stderr)
            return (1, int(rec_id))
        else:
            error=None
            write_message(lambda: "   -Added tag 005: DONE. " + str(record_get_field_value(record, '005', '', '')), verbose=2)

        # adding 005 to affected tags will delete the existing 005 entry
        # and update with the latest timestamp.
        if '005' not in affected_tags:
            affected_tags['005'] = [(' ', ' ')]

    write_message("   -Stage COMPLETED", verbose=2)

    record_deleted_p = False
    try:
        if not record_is_valid(record):
            msg = "ERROR: record is not valid"
            write_message(msg, verbose=1, stream=sys.stderr)
            return (1, -1, msg)

        # Have a look if we have FFT tags
        write_message("Stage 2: Start (Process FFT tags if exist).", verbose=2)
        record_had_FFT = False
        bibrecdocs = None
        if extract_tag_from_record(record, 'FFT') is not None:
            record_had_FFT = True
            if not writing_rights_p():
                msg = "ERROR: no rights to write fulltext files"
                write_message("   Stage 2 failed: %s" % msg,
                    verbose=1, stream=sys.stderr)
                raise StandardError(msg)
            try:
                bibrecdocs = BibRecDocs(rec_id)
                record = elaborate_fft_tags(record, rec_id, opt_mode,
                                        pretend=pretend, tmp_ids=tmp_ids,
                                        tmp_vers=tmp_vers, bibrecdocs=bibrecdocs)
            except Exception, e:
                register_exception()
                msg = "   Stage 2 failed: ERROR: while elaborating FFT tags: %s" % e
                write_message(msg, verbose=1, stream=sys.stderr)
                return (1, int(rec_id), msg)
            if record is None:
                msg = "   Stage 2 failed: ERROR: while elaborating FFT tags"
                write_message(msg, verbose=1, stream=sys.stderr)
                return (1, int(rec_id), msg)
            write_message("   -Stage COMPLETED", verbose=2)
        else:
            write_message("   -Stage NOT NEEDED", verbose=2)

        # Have a look if we have FFT tags
        write_message("Stage 2B: Start (Synchronize 8564 tags).", verbose=2)
        if record_had_FFT or extract_tag_from_record(record, '856') is not None:
            try:
                if bibrecdocs is None:
                    bibrecdocs = BibRecDocs(rec_id)
                record = synchronize_8564(rec_id, record, record_had_FFT, bibrecdocs, pretend=pretend)
                # in case if FFT is in affected list make appropriate changes
                if not insert_mode_p: # because for insert, all tags are affected
                    if ('4', ' ') not in affected_tags.get('856', []):
                        if '856' not in affected_tags:
                            affected_tags['856'] = [('4', ' ')]
                        elif ('4', ' ') not in affected_tags['856']:
                            affected_tags['856'].append(('4', ' '))
                    write_message("     -Modified field list updated with FFT details: %s" % str(affected_tags), verbose=2)
            except Exception, e:
                register_exception(alert_admin=True)
                msg = "   Stage 2B failed: ERROR: while synchronizing 8564 tags: %s" % e
                write_message(msg, verbose=1, stream=sys.stderr)
                return (1, int(rec_id), msg)
            if record is None:
                msg = "   Stage 2B failed: ERROR: while synchronizing 8564 tags"
                write_message(msg, verbose=1, stream=sys.stderr)
                return (1, int(rec_id), msg)
            write_message("   -Stage COMPLETED", verbose=2)
        else:
            write_message("   -Stage NOT NEEDED", verbose=2)

        write_message("Stage 3: Start (Apply fields deletion requests).", verbose=2)
        write_message(lambda: "     Record before deletion:\n%s" % record_xml_output(record), verbose=9)
        # remove fields with __DELETE_FIELDS__
        # NOTE:creating a temporary deep copy of record for iteration to avoid RunTimeError
        # RuntimeError due to change in dictionary size during iteration
        tmp_rec = copy.deepcopy(record)
        for tag in tmp_rec:
            for data_tuple in record[tag]:
                if (CFG_BIBUPLOAD_DELETE_CODE, CFG_BIBUPLOAD_DELETE_VALUE) in data_tuple[0]:
                    # delete the tag with particular indicator pairs from original record
                    record_delete_field(record, tag, data_tuple[1], data_tuple[2])

        write_message(lambda: "     Record after cleaning up fields to be deleted:\n%s" % record_xml_output(record), verbose=9)

        if opt_mode == 'append':
            write_message("Stage 3b: Drop duplicate fields in append mode.", verbose=2)
            record = record_drop_duplicate_fields(record)
            write_message(lambda: "     Record after dropping duplicate fields:\n%s" % record_xml_output(record), verbose=9)

        # Update of the BibFmt
        write_message("Stage 4: Start (Update bibfmt).", verbose=2)

        updates_exist = not records_identical(record, original_record)
        if updates_exist:
            # if record_had_altered_bit, this must be set to true, since the
            # record has been altered.
            if record_had_altered_bit:
                oai_provenance_fields = record_get_field_instances(record, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4])
                for oai_provenance_field in oai_provenance_fields:
                    for i, (code, dummy_value) in enumerate(oai_provenance_field[0]):
                        if code == CFG_OAI_PROVENANCE_ALTERED_SUBFIELD:
                            oai_provenance_field[0][i] = (code, 'true')
                            tmp_indicators = (CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3] == '_' and ' ' or CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4] == '_' and ' ' or CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4])
                            if tmp_indicators not in affected_tags.get(CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:3], []):
                                if CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:3] not in affected_tags:
                                    affected_tags[CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:3]] = [tmp_indicators]
                                else:
                                    affected_tags[CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:3]].append(tmp_indicators)

            write_message(lambda: "  Updates exists:\n%s\n!=\n%s" % (record, original_record), verbose=9)
            # format the single record as xml
            rec_xml_new = record_xml_output(record)
            # Update bibfmt with the format xm of this record
            modification_date = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(record_get_field_value(record, '005'), '%Y%m%d%H%M%S.0'))
            error = update_bibfmt_format(rec_id, rec_xml_new, 'xm', modification_date, pretend=pretend)
            if error == 1:
                msg = "   Failed: ERROR: during update_bibfmt_format 'xm'"
                write_message(msg, verbose=1, stream=sys.stderr)
                return (1, int(rec_id), msg)
            if CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE:
                error = update_bibfmt_format(rec_id, marshal.dumps(record), 'recstruct', modification_date, pretend=pretend)
                if error == 1:
                    msg = "   Failed: ERROR: during update_bibfmt_format 'recstruct'"
                    write_message(msg, verbose=1, stream=sys.stderr)
                    return (1, int(rec_id), msg)
            if not CFG_BIBUPLOAD_DISABLE_RECORD_REVISIONS:
                # archive MARCXML format of this record for version history purposes:
                if insert_mode_p:
                    error = archive_marcxml_for_history(rec_id, affected_fields={}, pretend=pretend)
                else:
                    error = archive_marcxml_for_history(rec_id, affected_fields=affected_tags, pretend=pretend)
                if error == 1:
                    msg = "   ERROR: Failed to archive MARCXML for history"
                    write_message(msg, verbose=1, stream=sys.stderr)
                    return (1, int(rec_id), msg)
                else:
                    write_message("   -Archived MARCXML for history: DONE", verbose=2)

        # delete some formats like HB upon record change:
        if updates_exist or record_had_FFT:
            for format_to_delete in CFG_BIBUPLOAD_DELETE_FORMATS:
                try:
                    delete_bibfmt_format(rec_id, format_to_delete, pretend=pretend)
                except:
                    # OK, some formats like HB could not have been deleted, no big deal
                    pass
        write_message("   -Stage COMPLETED", verbose=2)

        ## Let's assert that one and only one 005 tag is existing at this stage.
        assert len(record['005']) == 1

        # Update the database MetaData
        write_message("Stage 5: Start (Update the database with the metadata).",
                    verbose=2)
        if insert_mode_p:
            update_database_with_metadata(record, rec_id, oai_rec_id, pretend=pretend)
            write_message("   -Stage COMPLETED", verbose=2)
        elif opt_mode in ('replace', 'replace_or_insert',
            'append', 'correct', 'delete') and updates_exist:
            # now we clear all the rows from bibrec_bibxxx from the old
            record_deleted_p = True
            delete_bibrec_bibxxx(rec_old, rec_id, affected_tags, pretend=pretend)
            # metadata update will insert tags that are available in affected_tags.
            # but for delete, once the tags have been deleted from bibrec_bibxxx, they dont have to be inserted
            # except for 005.
            if is_opt_mode_delete:
                tmp_affected_tags = copy.deepcopy(affected_tags)
                for tag in tmp_affected_tags:
                    if tag != '005':
                        affected_tags.pop(tag)
            write_message("   -Clean bibrec_bibxxx: DONE", verbose=2)
            update_database_with_metadata(record, rec_id, oai_rec_id, affected_tags, pretend=pretend)
            write_message("   -Stage COMPLETED", verbose=2)
        else:
            write_message("   -Stage NOT NEEDED in mode %s" % opt_mode,
                        verbose=2)
        record_deleted_p = False

        # Finally we update the bibrec table with the current date
        write_message("Stage 6: Start (Update bibrec table with current date).",
                    verbose=2)
        if opt_notimechange == 0 and (updates_exist or record_had_FFT):
            bibrec_now = convert_datestruct_to_datetext(time.localtime())
            write_message("   -Retrieved current localtime: DONE", verbose=2)
            update_bibrec_date(bibrec_now, rec_id, insert_mode_p, pretend=pretend)
            write_message("   -Stage COMPLETED", verbose=2)
        else:
            write_message("   -Stage NOT NEEDED", verbose=2)

        # Increase statistics
        if insert_mode_p:
            stat['nb_records_inserted'] += 1
        else:
            stat['nb_records_updated'] += 1

        # Upload of this record finish
        write_message("Record "+str(rec_id)+" DONE", verbose=1)
        return (0, int(rec_id), "")
    finally:
        if record_deleted_p:
            ## BibUpload has failed living the record deleted. We should
            ## back the original record then.
            update_database_with_metadata(original_record, rec_id, oai_rec_id, pretend=pretend)
            write_message("   Restored original record", verbose=1, stream=sys.stderr)

def record_is_valid(record):
    """
    Check if the record is valid. Currently this simply checks if the record
    has exactly one rec_id.

    @param record: the record
    @type record: recstruct
    @return: True if the record is valid
    @rtype: bool
    """
    rec_ids = record_get_field_values(record, tag="001")
    if len(rec_ids) != 1:
        write_message("    The record is not valid: it has not a single rec_id: %s" % (rec_ids), stream=sys.stderr)
        return False
    return True

def find_record_ids_by_oai_id(oaiId):
    """
    A method finding the records identifier provided the oai identifier
    returns a list of identifiers matching a given oai identifier
    """
    # Is this record already in invenio (matching by oaiid)
    if oaiId:
        recids = search_pattern(p=oaiId, f=CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, m='e')

        # Is this record already in invenio (matching by reportnumber i.e.
        # particularly 037. Idea: to avoid double insertions)
        repnumber = oaiId.split(":")[-1]
        if repnumber:
            recids |= search_pattern(p = repnumber,
                                    f = "reportnumber",
                                    m = 'e' )

        # Is this record already in invenio (matching by reportnumber i.e.
        # particularly 037. Idea:  to avoid double insertions)
        repnumber = "arXiv:" + oaiId.split(":")[-1]
        recids |= search_pattern(p = repnumber,
                                f = "reportnumber",
                                m = 'e' )

        if CFG_BIBUPLOAD_MATCH_DELETED_RECORDS:
            return recids
        else:
            if CFG_CERN_SITE:
                return recids - (search_pattern(p='DELETED', f='980__%', m='e') | search_pattern(p='DUMMY', f='980__%', m='e'))
            else:
                return recids - search_pattern(p='DELETED', f='980__%', m='e')
    else:
        return intbitset()

def bibupload_post_phase(record, mode=None, rec_id="", pretend=False,
                         tmp_ids=None, tmp_vers=None):
    def _elaborate_tag(record, tag, fun):
        if extract_tag_from_record(record, tag) is not None:
            try:
                record = fun()
            except Exception, e:
                register_exception()
                write_message("   Stage failed: ERROR: while elaborating %s tags: %s" % (tag, e),
                              verbose=1, stream=sys.stderr)
                return (1, int(rec_id)) # TODO: ?
            if record is None:
                write_message("   Stage failed: ERROR: while elaborating %s tags" % (tag, ),
                              verbose=1, stream=sys.stderr)
                return (1, int(rec_id))
            write_message("   -Stage COMPLETED", verbose=2)
        else:
            write_message("   -Stage NOT NEEDED", verbose=2)
    if tmp_ids is None:
        tmp_ids = {}
    if tmp_vers is None:
        tmp_vers = {}
    _elaborate_tag(record, "BDR", lambda: elaborate_brt_tags(record, rec_id = rec_id,
                                                     mode = mode,
                                                     pretend = pretend,
                                                     tmp_ids = tmp_ids,
                                                     tmp_vers = tmp_vers))


    _elaborate_tag(record, "BDM", lambda: elaborate_mit_tags(record, rec_id = rec_id,
                                                     mode = mode,
                                                     pretend = pretend,
                                                     tmp_ids = tmp_ids,
                                                     tmp_vers = tmp_vers))

def submit_ticket_for_holding_pen(rec_id, err, msg, pretend=False):
    """
    Submit a ticket via BibCatalog to report about a record that has been put
    into the Holding Pen.
    @rec_id: the affected record
    @err: the corresponding Exception
    msg: verbose message
    """
    from invenio import bibtask
    from invenio.webuser import get_email_from_username, get_uid_from_email
    user = task_get_task_param("user")
    uid = None
    if user:
        try:
            uid = get_uid_from_email(get_email_from_username(user))
        except Exception, err:
            write_message("WARNING: can't reliably retrieve uid for user %s: %s" % (user, err), stream=sys.stderr)

    if check_bibcatalog():
        text = """
%(msg)s found for record %(rec_id)s: %(err)s

See: <%(siteurl)s/record/edit/#state=edit&recid=%(rec_id)s>

BibUpload task information:
    task_id: %(task_id)s
    task_specific_name: %(task_specific_name)s
    user: %(user)s
    task_params: %(task_params)s
    task_options: %(task_options)s""" % {
            "msg": msg,
            "rec_id": rec_id,
            "err": err,
            "siteurl": CFG_SITE_SECURE_URL,
            "task_id": task_get_task_param("task_id"),
            "task_specific_name": task_get_task_param("task_specific_name"),
            "user": user,
            "task_params": bibtask._TASK_PARAMS,
            "task_options": bibtask._OPTIONS}
        if not pretend:
            BIBCATALOG_SYSTEM.ticket_submit(subject="%s: %s by %s" % (msg, rec_id, user), recordid=rec_id, text=text, queue=CFG_BIBUPLOAD_CONFLICTING_REVISION_TICKET_QUEUE, owner=uid)

def insert_record_into_holding_pen(record, oai_id, pretend=False):
    query = "INSERT INTO bibHOLDINGPEN (oai_id, changeset_date, changeset_xml, id_bibrec) VALUES (%s, NOW(), %s, %s)"
    xml_record = record_xml_output(record)
    bibrec_ids = find_record_ids_by_oai_id(oai_id)  # here determining the identifier of the record
    if len(bibrec_ids) > 0:
        bibrec_id = bibrec_ids.pop()
    else:
        # id not found by using the oai_id, let's use a wider search based
        # on any information we might have.
        bibrec_id = retrieve_rec_id(record, 'holdingpen', pretend=pretend)
        if bibrec_id is None:
            bibrec_id = 0

    if not pretend:
        run_sql(query, (oai_id, compress(xml_record), bibrec_id))

    # record_id is logged as 0! ( We are not inserting into the main database)
    log_record_uploading(oai_id, task_get_task_param('task_id', 0), 0, 'H', pretend=pretend)
    stat['nb_holdingpen'] += 1

def print_out_bibupload_statistics():
    """Print the statistics of the process"""
    out = "Task stats: %(nb_input)d input records, %(nb_updated)d updated, " \
          "%(nb_inserted)d inserted, %(nb_errors)d errors, %(nb_holdingpen)d inserted to holding pen.  " \
          "Time %(nb_sec).2f sec." % { \
              'nb_input': stat['nb_records_to_upload'],
              'nb_updated': stat['nb_records_updated'],
              'nb_inserted': stat['nb_records_inserted'],
              'nb_errors': stat['nb_errors'],
              'nb_holdingpen': stat['nb_holdingpen'],
              'nb_sec': time.time() - time.mktime(stat['exectime']) }
    write_message(out)

def open_marc_file(path):
    """Open a file and return the data"""
    try:
        # open the file containing the marc document
        marc_file = open(path, 'r')
        marc = marc_file.read()
        marc_file.close()
    except IOError, erro:
        write_message("ERROR: %s" % erro, verbose=1, stream=sys.stderr)
        if erro.errno == 2:
            # No such file or directory
            # Not scary
            e = RecoverableError('File does not exist: %s' % path)
        else:
            e = StandardError('File not accessible: %s' % path)
        raise e
    return marc

def xml_marc_to_records(xml_marc):
    """create the records"""
    # Creation of the records from the xml Marc in argument
    xml_marc = wash_for_xml(xml_marc)
    recs = create_records(xml_marc, 1, 1)
    if recs == []:
        msg = "ERROR: Cannot parse MARCXML file."
        write_message(msg, verbose=1, stream=sys.stderr)
        raise StandardError(msg)
    elif recs[0][0] is None:
        msg = "ERROR: MARCXML file has wrong format: %s" % recs
        write_message(msg, verbose=1, stream=sys.stderr)
        raise RecoverableError(msg)
    else:
        recs = map((lambda x:x[0]), recs)
        return recs

def find_record_format(rec_id, bibformat):
    """Look whether record REC_ID is formatted in FORMAT,
       i.e. whether FORMAT exists in the bibfmt table for this record.

       Return the number of times it is formatted: 0 if not, 1 if yes,
       2 if found more than once (should never occur).
    """
    out = 0
    query = """SELECT COUNT(*) FROM bibfmt WHERE id_bibrec=%s AND format=%s"""
    params = (rec_id, bibformat)
    res = []
    res = run_sql(query, params)
    out = res[0][0]
    return out

def find_record_from_recid(rec_id):
    """
    Try to find record in the database from the REC_ID number.
    Return record ID if found, None otherwise.
    """
    res = run_sql("SELECT id FROM bibrec WHERE id=%s",
                    (rec_id,))
    if res:
        return res[0][0]
    else:
        return None

def find_record_from_sysno(sysno):
    """
    Try to find record in the database from the external SYSNO number.
    Return record ID if found, None otherwise.
    """
    bibxxx = 'bib'+CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:2]+'x'
    bibrec_bibxxx = 'bibrec_' + bibxxx
    res = run_sql("""SELECT bb.id_bibrec FROM %(bibrec_bibxxx)s AS bb,
        %(bibxxx)s AS b WHERE b.tag=%%s AND b.value=%%s
        AND bb.id_bibxxx=b.id""" %
                    {'bibxxx': bibxxx,
                    'bibrec_bibxxx': bibrec_bibxxx},
                    (CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, sysno,))
    for recid in res:
        if CFG_BIBUPLOAD_MATCH_DELETED_RECORDS:
            return recid[0]
        else:
            if record_exists(recid[0]) > 0: ## Only non deleted records
                return recid[0]
    return None

def find_records_from_extoaiid(extoaiid, extoaisrc=None):
    """
    Try to find records in the database from the external EXTOAIID number.
    Return list of record ID if found, None otherwise.
    """
    assert(CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:5] == CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG[:5])
    bibxxx = 'bib'+CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:2]+'x'
    bibrec_bibxxx = 'bibrec_' + bibxxx

    write_message('   Looking for extoaiid="%s" with extoaisrc="%s"' % (extoaiid, extoaisrc), verbose=9)
    id_bibrecs = intbitset(run_sql("""SELECT bb.id_bibrec FROM %(bibrec_bibxxx)s AS bb,
        %(bibxxx)s AS b WHERE b.tag=%%s AND b.value=%%s
        AND bb.id_bibxxx=b.id""" %
                    {'bibxxx': bibxxx,
                    'bibrec_bibxxx': bibrec_bibxxx},
                    (CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, extoaiid,)))
    write_message('   Partially found %s for extoaiid="%s"' % (id_bibrecs, extoaiid), verbose=9)

    ret = intbitset()
    for id_bibrec in id_bibrecs:

        if not CFG_BIBUPLOAD_MATCH_DELETED_RECORDS:
            if record_exists(id_bibrec) < 1:
                ## We don't match not existing records
                continue

        record = get_record(id_bibrec)
        instances = record_get_field_instances(record, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4])
        write_message('   recid %s -> instances "%s"' % (id_bibrec, instances), verbose=9)
        for instance in instances:
            this_extoaisrc = field_get_subfield_values(instance, CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG[5])
            this_extoaisrc = this_extoaisrc and this_extoaisrc[0] or None
            this_extoaiid = field_get_subfield_values(instance, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5])
            this_extoaiid = this_extoaiid and this_extoaiid[0] or None
            write_message("        this_extoaisrc -> %s, this_extoaiid -> %s" % (this_extoaisrc, this_extoaiid), verbose=9)
            if this_extoaiid == extoaiid:
                write_message('   recid %s -> provenance "%s"' % (id_bibrec, this_extoaisrc), verbose=9)
                if this_extoaisrc == extoaisrc:
                    write_message('Found recid %s for extoaiid="%s" with provenance="%s"' % (id_bibrec, extoaiid, extoaisrc), verbose=9)
                    ret.add(id_bibrec)
                    break
                if this_extoaisrc is None:
                    write_message('WARNING: Found recid %s for extoaiid="%s" that doesn\'t specify any provenance, while input record does.' % (id_bibrec, extoaiid), stream=sys.stderr)
                if extoaisrc is None:
                    write_message('WARNING: Found recid %s for extoaiid="%s" that specify a provenance (%s), while input record does not have a provenance.' % (id_bibrec, extoaiid, this_extoaisrc), stream=sys.stderr)
    return ret

def find_record_from_oaiid(oaiid):
    """
    Try to find record in the database from the OAI ID number and OAI SRC.
    Return record ID if found, None otherwise.
    """
    bibxxx = 'bib'+CFG_OAI_ID_FIELD[0:2]+'x'
    bibrec_bibxxx = 'bibrec_' + bibxxx
    res = run_sql("""SELECT bb.id_bibrec FROM %(bibrec_bibxxx)s AS bb,
        %(bibxxx)s AS b WHERE b.tag=%%s AND b.value=%%s
        AND bb.id_bibxxx=b.id""" %
                    {'bibxxx': bibxxx,
                    'bibrec_bibxxx': bibrec_bibxxx},
                    (CFG_OAI_ID_FIELD, oaiid,))
    for recid in res:
        if CFG_BIBUPLOAD_MATCH_DELETED_RECORDS:
            return recid[0]
        else:
            if record_exists(recid[0]) > 0: ## Only non deleted records
                return recid[0]
    return None

def find_record_from_doi(doi):
    """
    Try to find record in the database from the given DOI.
    Return record ID if found, None otherwise.
    """
    bibxxx = 'bib02x'
    bibrec_bibxxx = 'bibrec_' + bibxxx
    res = run_sql("""SELECT bb.id_bibrec, bb.field_number
        FROM %(bibrec_bibxxx)s AS bb, %(bibxxx)s AS b
        WHERE b.tag=%%s AND b.value=%%s
        AND bb.id_bibxxx=b.id""" %
                    {'bibxxx': bibxxx,
                    'bibrec_bibxxx': bibrec_bibxxx},
                    ('0247_a', doi,))

    # For each of the result, make sure that it is really tagged as doi
    for (id_bibrec, field_number) in res:

        if not CFG_BIBUPLOAD_MATCH_DELETED_RECORDS:
            if record_exists(id_bibrec) < 1:
                ## We don't match not existing records
                continue

        res = run_sql("""SELECT bb.id_bibrec
        FROM %(bibrec_bibxxx)s AS bb, %(bibxxx)s AS b
        WHERE b.tag=%%s AND b.value=%%s
        AND bb.id_bibxxx=b.id and bb.field_number=%%s and bb.id_bibrec=%%s""" %
                    {'bibxxx': bibxxx,
                    'bibrec_bibxxx': bibrec_bibxxx},
                    ('0247_2', "doi", field_number, id_bibrec))
        if res and res[0][0] == id_bibrec:
            return res[0][0]

    return None

def extract_tag_from_record(record, tag_number):
    """ Extract the tag_number for record."""
    # first step verify if the record is not already in the database
    if record:
        return record.get(tag_number, None)
    return None

def retrieve_rec_id(record, opt_mode, pretend=False, post_phase = False):
    """Retrieve the record Id from a record by using tag 001 or SYSNO or OAI ID or DOI
    tag. opt_mod is the desired mode.

    @param post_phase Tells if we are calling this method in the postprocessing phase. If true, we accept presence of 001 fields even in the insert mode
    @type post_phase boolean
    """

    rec_id = None

    # 1st step: we look for the tag 001
    tag_001 = extract_tag_from_record(record, '001')
    if tag_001 is not None:
        # We extract the record ID from the tag
        rec_id = tag_001[0][3]
        # if we are in insert mode => error
        if opt_mode == 'insert' and not post_phase:
            write_message("   Failed: tag 001 found in the xml" \
                          " submitted, you should use the option replace," \
                          " correct or append to replace an existing" \
                          " record. (-h for help)",
                          verbose=1, stream=sys.stderr)
            return -1
        else:
            # we found the rec id and we are not in insert mode => continue
            # we try to match rec_id against the database:
            if find_record_from_recid(rec_id) is not None:
                # okay, 001 corresponds to some known record
                return int(rec_id)
            elif opt_mode in ('replace', 'replace_or_insert'):
                if task_get_option('force'):
                    # we found the rec_id but it's not in the system and we are
                    # requested to replace records. Therefore we create on the fly
                    # a empty record allocating the recid.
                    write_message("   WARNING: tag 001 found in the xml with"
                                " value %(rec_id)s, but rec_id %(rec_id)s does"
                                " not exist. Since the mode replace was"
                                " requested the rec_id %(rec_id)s is allocated"
                                " on-the-fly." % {"rec_id": rec_id},
                                stream=sys.stderr)
                    return create_new_record(rec_id=rec_id, pretend=pretend)
                else:
                    # Since --force was not used we are going to raise an error
                    write_message("   Failed: tag 001 found in the xml"
                                  " submitted with value %(rec_id)s. The"
                                  " corresponding record however does not"
                                  " exists. If you want to really create"
                                  " such record, please use the --force"
                                  " parameter when calling bibupload." % {
                                    "rec_id": rec_id}, stream=sys.stderr)
                    return -1
            else:
                # The record doesn't exist yet. We shall have try to check
                # the SYSNO or OAI or DOI id later.
                write_message("   -Tag 001 value not found in database.",
                              verbose=9)
                rec_id = None
    else:
        write_message("   -Tag 001 not found in the xml marc file.", verbose=9)

    if rec_id is None:
        # 2nd step we look for the SYSNO
        sysnos = record_get_field_values(record,
            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[0:3],
            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] != "_" and \
            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[3:4] or "",
            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] != "_" and \
            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[4:5] or "",
            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[5:6])
        if sysnos:
            sysno = sysnos[0] # there should be only one external SYSNO
            write_message("   -Checking if SYSNO " + sysno + \
                          " exists in the database", verbose=9)
            # try to find the corresponding rec id from the database
            rec_id = find_record_from_sysno(sysno)
            if rec_id is not None:
                # rec_id found
                pass
            else:
                # The record doesn't exist yet. We will try to check
                # external and internal OAI ids later.
                write_message("   -Tag SYSNO value not found in database.",
                              verbose=9)
                rec_id = None
        else:
            write_message("   -Tag SYSNO not found in the xml marc file.",
                verbose=9)

    if rec_id is None:
        # 2nd step we look for the external OAIID
        extoai_fields = record_get_field_instances(record,
            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3],
            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] != "_" and \
            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3:4] or "",
            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] != "_" and \
            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4:5] or "")
        if extoai_fields:
            for field in extoai_fields:
                extoaiid = field_get_subfield_values(field, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[5:6])
                extoaisrc = field_get_subfield_values(field, CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG[5:6])
                if extoaiid:
                    extoaiid = extoaiid[0]
                    if extoaisrc:
                        extoaisrc = extoaisrc[0]
                    else:
                        extoaisrc = None
                    write_message("   -Checking if EXTOAIID %s (%s) exists in the database" % (extoaiid, extoaisrc), verbose=9)
                    # try to find the corresponding rec id from the database
                    rec_ids = find_records_from_extoaiid(extoaiid, extoaisrc)
                    if rec_ids:
                        # rec_id found
                        rec_id = rec_ids.pop()
                        break
                    else:
                        # The record doesn't exist yet. We will try to check
                        # OAI id later.
                        write_message("   -Tag EXTOAIID value not found in database.",
                                    verbose=9)
                        rec_id = None
        else:
            write_message("   -Tag EXTOAIID not found in the xml marc file.", verbose=9)

    if rec_id is None:
        # 4th step we look for the OAI ID
        oaiidvalues = record_get_field_values(record,
            CFG_OAI_ID_FIELD[0:3],
            CFG_OAI_ID_FIELD[3:4] != "_" and \
            CFG_OAI_ID_FIELD[3:4] or "",
            CFG_OAI_ID_FIELD[4:5] != "_" and \
            CFG_OAI_ID_FIELD[4:5] or "",
            CFG_OAI_ID_FIELD[5:6])
        if oaiidvalues:
            oaiid = oaiidvalues[0] # there should be only one OAI ID
            write_message("   -Check if local OAI ID " + oaiid + \
                          " exist in the database", verbose=9)

            # try to find the corresponding rec id from the database
            rec_id = find_record_from_oaiid(oaiid)
            if rec_id is not None:
                # rec_id found
                pass
            else:
                write_message("   -Tag OAI ID value not found in database.",
                              verbose=9)
                rec_id = None
        else:
            write_message("   -Tag SYSNO not found in the xml marc file.",
                verbose=9)

    if rec_id is None:
        # 5th step we look for the DOI.
        record_dois = record_extract_dois(record)
        matching_recids = set()
        if record_dois:
            # try to find the corresponding rec id from the database
            for record_doi in record_dois:
                possible_recid = find_record_from_doi(record_doi)
                if possible_recid:
                    matching_recids.add(possible_recid)
            if len(matching_recids) > 1:
                # Oops, this record refers to DOI existing in multiple records.
                # Dunno which one to choose.
                write_message("   Failed: Multiple records found in the" \
                          " database %s that match the DOI(s) in the input" \
                          " MARCXML %s" % (repr(matching_recids), repr(record_dois)),
                          verbose=1, stream=sys.stderr)
                return -1
            elif len(matching_recids) == 1:
                rec_id = matching_recids.pop()
                if opt_mode == 'insert':
                    write_message("   Failed: DOI tag matching record #%s found in the xml" \
                          " submitted, you should use the option replace," \
                          " correct or append to replace an existing" \
                          " record. (-h for help)" % rec_id,
                          verbose=1, stream=sys.stderr)
                    return -1
            else:
                write_message("   - Tag DOI value not found in database.",
                                  verbose=9)
                rec_id = None
        else:
            write_message("   -Tag DOI not found in the xml marc file.",
                verbose=9)

    # Now we should have detected rec_id from SYSNO or OAIID
    # tags.  (None otherwise.)
    if rec_id:
        if opt_mode == 'insert':
            write_message("   Failed: Record found in the database," \
                          " you should use the option replace," \
                          " correct or append to replace an existing" \
                          " record. (-h for help)",
                          verbose=1, stream=sys.stderr)
            return -1
    else:
        if opt_mode != 'insert' and \
           opt_mode != 'replace_or_insert':
            write_message("   Failed: Record not found in the database."\
                          " Please insert the file before updating it."\
                          " (-h for help)", verbose=1, stream=sys.stderr)
            return -1

    return rec_id and int(rec_id) or None

def check_record_doi_is_unique(rec_id, record):
    """
    Check that DOI found in 'record' does not exist in any other
    record than 'recid'.

    Return (boolean, msg) where 'boolean' would be True if the DOI is
    unique.
    """
    record_dois = record_extract_dois(record)
    if record_dois:
        matching_recids = set()
        for record_doi in record_dois:
            possible_recid = find_record_from_doi(record_doi)
            if possible_recid:
                matching_recids.add(possible_recid)
        if len(matching_recids) > 1:
            # Oops, this record refers to DOI existing in multiple records.
            msg = "   Failed: Multiple records found in the" \
                      " database %s that match the DOI(s) in the input" \
                      " MARCXML %s" % (repr(matching_recids), repr(record_dois))
            return (False, msg)
        elif len(matching_recids) == 1:
            matching_recid = matching_recids.pop()
            if str(matching_recid) != str(rec_id):
                # Oops, this record refers to DOI existing in a different record.
                msg = "   Failed: DOI(s) %s found in this record (#%s)" \
                      " already exist(s) in another other record (#%s)" % \
                      (repr(record_dois), rec_id, matching_recid)
                return (False, msg)
    return (True, "")

### Insert functions

def create_new_record(rec_id=None, pretend=False):
    """
    Create new record in the database

    @param rec_id: if specified the new record will have this rec_id.
    @type rec_id: int
    @return: the allocated rec_id
    @rtype: int

    @note: in case of errors will be returned None
    """
    if rec_id is not None:
        try:
            rec_id = int(rec_id)
        except (ValueError, TypeError), error:
            write_message("   ERROR: during the creation_new_record function: %s "
        % error, verbose=1, stream=sys.stderr)
            return None
        if run_sql("SELECT id FROM bibrec WHERE id=%s", (rec_id, )):
            write_message("   ERROR: during the creation_new_record function: the requested rec_id %s already exists." % rec_id)
            return None
    if pretend:
        if rec_id:
            return rec_id
        else:
            return run_sql("SELECT max(id)+1 FROM bibrec")[0][0]
    if rec_id is not None:
        return run_sql("INSERT INTO bibrec (id, creation_date, modification_date) VALUES (%s, NOW(), NOW())", (rec_id, ))
    else:
        return run_sql("INSERT INTO bibrec (creation_date, modification_date) VALUES (NOW(), NOW())")

def insert_bibfmt(id_bibrec, marc, bibformat, modification_date='1970-01-01 00:00:00', pretend=False):
    """Insert the format in the table bibfmt"""
    # compress the marc value
    pickled_marc =  compress(marc)
    try:
        time.strptime(modification_date, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        modification_date = '1970-01-01 00:00:00'

    query = """INSERT LOW_PRIORITY INTO bibfmt (id_bibrec, format, last_updated, value)
        VALUES (%s, %s, %s, %s)"""
    if not pretend:
        row_id  = run_sql(query, (id_bibrec, bibformat, modification_date, pickled_marc))
        return row_id
    else:
        return 1

def insert_record_bibxxx(tag, value, pretend=False):
    """Insert the record into bibxxx"""
    # determine into which table one should insert the record
    table_name = 'bib'+tag[0:2]+'x'

    # check if the tag, value combination exists in the table
    query = """SELECT id,value FROM %s """ % table_name
    query += """ WHERE tag=%s AND value=%s"""
    params = (tag, value)
    res = None
    res = run_sql(query, params)

    # Note: compare now the found values one by one and look for
    # string binary equality (e.g. to respect lowercase/uppercase
    # match), regardless of the charset etc settings.  Ideally we
    # could use a BINARY operator in the above SELECT statement, but
    # we would have to check compatibility on various MySQLdb versions
    # etc; this approach checks all matched values in Python, not in
    # MySQL, which is less cool, but more conservative, so it should
    # work better on most setups.
    if res:
        for row in res:
            row_id = row[0]
            row_value = row[1]
            if row_value == value:
                return (table_name, row_id)

    # We got here only when the tag, value combination was not found,
    # so it is now necessary to insert the tag, value combination into
    # bibxxx table as new.
    query = """INSERT INTO %s """ % table_name
    query += """ (tag, value) values (%s , %s)"""
    params = (tag, value)
    if not pretend:
        row_id = run_sql(query, params)
    else:
        return (table_name, 1)
    return (table_name, row_id)

def insert_record_bibrec_bibxxx(table_name, id_bibxxx,
        field_number, id_bibrec, pretend=False):
    """Insert the record into bibrec_bibxxx"""
    # determine into which table one should insert the record
    full_table_name = 'bibrec_'+ table_name

    # insert the proper row into the table
    query = """INSERT INTO %s """ % full_table_name
    query += """(id_bibrec,id_bibxxx, field_number) values (%s , %s, %s)"""
    params = (id_bibrec, id_bibxxx, field_number)
    if not pretend:
        res = run_sql(query, params)
    else:
        return 1
    return res

def synchronize_8564(rec_id, record, record_had_FFT, bibrecdocs, pretend=False):
    """
    Synchronize 8564_ tags and BibDocFile tables.

    This function directly manipulate the record parameter.

    @type rec_id: positive integer
    @param rec_id: the record identifier.
    @param record: the record structure as created by bibrecord.create_record
    @type record_had_FFT: boolean
    @param record_had_FFT: True if the incoming bibuploaded-record used FFT
    @return: the manipulated record (which is also modified as a side effect)
    """
    def merge_marc_into_bibdocfile(field, pretend=False):
        """
        Internal function that reads a single field and stores its content
        in BibDocFile tables.
        @param field: the 8564_ field containing a BibDocFile URL.
        """
        write_message('Merging field: %s' % (field, ), verbose=9)
        url = field_get_subfield_values(field, 'u')[:1] or field_get_subfield_values(field, 'q')[:1]
        description = field_get_subfield_values(field, 'y')[:1]
        comment = field_get_subfield_values(field, 'z')[:1]
        if url:
            recid, docname, docformat = decompose_bibdocfile_url(url[0])
            if recid != rec_id:
                write_message("INFO: URL %s is not pointing to a fulltext owned by this record (%s)" % (url, recid), stream=sys.stderr)
            else:
                try:
                    bibdoc = bibrecdocs.get_bibdoc(docname)
                    if description and not pretend:
                        bibdoc.set_description(description[0], docformat)
                    if comment and not pretend:
                        bibdoc.set_comment(comment[0], docformat)
                except InvenioBibDocFileError:
                    ## Apparently the referenced docname doesn't exist anymore.
                    ## Too bad. Let's skip it.
                    write_message("WARNING: docname %s does not seem to exist for record %s. Has it been renamed outside FFT?" % (docname, recid), stream=sys.stderr)

    def merge_bibdocfile_into_marc(field, subfields):
        """
        Internal function that reads BibDocFile table entries referenced by
        the URL in the given 8564_ field and integrate the given information
        directly with the provided subfields.

        @param field: the 8564_ field containing a BibDocFile URL.
        @param subfields: the subfields corresponding to the BibDocFile URL
                          generated after BibDocFile tables.
        """
        write_message('Merging subfields %s into field %s' % (subfields, field), verbose=9)
        subfields = dict(subfields) ## We make a copy not to have side-effects
        subfield_to_delete = []
        for subfield_position, (code, value) in enumerate(field_get_subfield_instances(field)):
            ## For each subfield instance already existing...
            if code in subfields:
                ## ...We substitute it with what is in BibDocFile tables
                record_modify_subfield(record, '856', code, subfields[code],
                    subfield_position, field_position_global=field[4])
                del subfields[code]
            else:
                ## ...We delete it otherwise
                subfield_to_delete.append(subfield_position)

        subfield_to_delete.sort()

        for counter, position in enumerate(subfield_to_delete):
            ## FIXME: Very hackish algorithm. Since deleting a subfield
            ## will alterate the position of following subfields, we
            ## are taking note of this and adjusting further position
            ## by using a counter.
            record_delete_subfield_from(record, '856', position - counter,
                field_position_global=field[4])

        subfields = subfields.items()
        subfields.sort()
        for code, value in subfields:
            ## Let's add non-previously existing subfields
            record_add_subfield_into(record, '856', code, value,
                field_position_global=field[4])

    def get_bibdocfile_managed_info():
        """
        Internal function, returns a dictionary of
        BibDocFile URL -> wanna-be subfields.
        This information is retrieved from internal BibDoc
        structures rather than from input MARC XML files

        @rtype: mapping
        @return: BibDocFile URL -> wanna-be subfields dictionary
        """
        ret = {}
        latest_files = bibrecdocs.list_latest_files(list_hidden=False)
        for afile in latest_files:
            url = afile.get_url()
            ret[url] = {'u': url}
            description = afile.get_description()
            comment = afile.get_comment()
            subformat = afile.get_subformat()
            size = afile.get_size()
            if description:
                ret[url]['y'] = description
            if comment:
                ret[url]['z'] = comment
            if subformat:
                ret[url]['x'] = subformat
            ret[url]['s'] = str(size)

        return ret

    write_message("Synchronizing MARC of recid '%s' with:\n%s" % (rec_id, record), verbose=9)
    tags856s = record_get_field_instances(record, '856', '%', '%')
    write_message("Original 856%% instances: %s" % tags856s, verbose=9)
    tags8564s_to_add = get_bibdocfile_managed_info()
    write_message("BibDocFile instances: %s" % tags8564s_to_add, verbose=9)
    positions_tags8564s_to_remove = []

    for local_position, field in enumerate(tags856s):
        if field[1] == '4' and field[2] == ' ':
            write_message('Analysing %s' % (field, ), verbose=9)
            for url in field_get_subfield_values(field, 'u') + field_get_subfield_values(field, 'q'):
                if url in tags8564s_to_add:
                    # there exists a link in the MARC of the record and the connection exists in BibDoc tables
                    if record_had_FFT:
                        merge_bibdocfile_into_marc(field, tags8564s_to_add[url])
                    else:
                        merge_marc_into_bibdocfile(field, pretend=pretend)
                    del tags8564s_to_add[url]
                    break
                elif bibdocfile_url_p(url) and decompose_bibdocfile_url(url)[0] == rec_id:
                    # The link exists and is potentially correct-looking link to a document
                    # moreover, it refers to current record id ... but it does not exist in
                    # internal BibDoc structures. This could have happen in the case of renaming a document
                    # or its removal. In both cases we have to remove link... a new one will be created
                    positions_tags8564s_to_remove.append(local_position)
                    write_message("%s to be deleted and re-synchronized" % (field, ),  verbose=9)
                    break

    record_delete_fields(record, '856', positions_tags8564s_to_remove)

    tags8564s_to_add = tags8564s_to_add.values()
    tags8564s_to_add.sort()
    ## FIXME: we are not yet able to preserve the sorting
    ## of 8564 tags WRT FFT in BibUpload.
    ## See ticket #1606.
    for subfields in tags8564s_to_add:
        subfields = subfields.items()
        subfields.sort()
        record_add_field(record, '856', '4', ' ', subfields=subfields)

    write_message('Final record: %s' % record, verbose=9)
    return record

def _get_subfield_value(field, subfield_code, default=None):
    res = field_get_subfield_values(field, subfield_code)
    if res != [] and res != None:
        return res[0]
    else:
        return default


def elaborate_mit_tags(record, rec_id, mode, pretend = False, tmp_ids = {},
                       tmp_vers = {}):
    """
    Uploading MoreInfo -> BDM tags
    """
    tuple_list = extract_tag_from_record(record, 'BDM')

    # Now gathering information from BDR tags - to be processed later
    write_message("Processing BDM entries of the record ")
    recordDocs = BibRecDocs(rec_id)

    if tuple_list:
        for mit in record_get_field_instances(record, 'BDM', ' ', ' '):
            relation_id = _get_subfield_value(mit, "r")
            bibdoc_id = _get_subfield_value(mit, "i")
            # checking for a possibly temporary ID
            if not (bibdoc_id is None):
                bibdoc_id = resolve_identifier(tmp_ids, bibdoc_id)

            bibdoc_ver = _get_subfield_value(mit, "v")
            if not (bibdoc_ver is None):
                bibdoc_ver = resolve_identifier(tmp_vers, bibdoc_ver)

            bibdoc_name = _get_subfield_value(mit, "n")
            bibdoc_fmt = _get_subfield_value(mit, "f")
            moreinfo_str = _get_subfield_value(mit, "m")

            if bibdoc_id == None:
                if bibdoc_name == None:
                    raise StandardError("Incorrect relation. Neither name nor identifier of the first obejct has been specified")
                else:
                    # retrieving the ID based on the document name (inside current record)
                    # The document is attached to current record.
                    try:
                        bibdoc_id = recordDocs.get_docid(bibdoc_name)
                    except:
                        raise StandardError("BibDoc of a name %s does not exist within a record" % (bibdoc_name, ))
            else:
                if bibdoc_name != None:
                    write_message("WARNING: both name and id of the first document of a relation have been specified. Ignoring the name", stream=sys.stderr)
            if (moreinfo_str is None or mode in ("replace", "correct")) and (not pretend):

                MoreInfo(docid=bibdoc_id , version = bibdoc_ver,
                         docformat = bibdoc_fmt, relation = relation_id).delete()

            if (not moreinfo_str is None) and (not pretend):
                MoreInfo.create_from_serialised(moreinfo_str,
                                                docid=bibdoc_id,
                                                version = bibdoc_ver,
                                                docformat = bibdoc_fmt,
                                                relation = relation_id)
    return record

def elaborate_brt_tags(record, rec_id, mode, pretend=False, tmp_ids = {}, tmp_vers = {}):
    """
    Process BDR tags describing relations between existing objects
    """
    tuple_list = extract_tag_from_record(record, 'BDR')

    # Now gathering information from BDR tags - to be processed later
    relations_to_create = []
    write_message("Processing BDR entries of the record ")
    recordDocs = BibRecDocs(rec_id) #TODO: check what happens if there is no record yet ! Will the class represent an empty set?

    if tuple_list:
        for brt in record_get_field_instances(record, 'BDR', ' ', ' '):

            relation_id = _get_subfield_value(brt, "r")

            bibdoc1_id = None
            bibdoc1_name = None
            bibdoc1_ver = None
            bibdoc1_fmt = None
            bibdoc2_id = None
            bibdoc2_name = None
            bibdoc2_ver = None
            bibdoc2_fmt = None

            if not relation_id:
                bibdoc1_id = _get_subfield_value(brt, "i")
                bibdoc1_name = _get_subfield_value(brt, "n")


                if bibdoc1_id == None:
                    if bibdoc1_name == None:
                        raise StandardError("Incorrect relation. Neither name nor identifier of the first obejct has been specified")
                    else:
                        # retrieving the ID based on the document name (inside current record)
                        # The document is attached to current record.
                        try:
                            bibdoc1_id = recordDocs.get_docid(bibdoc1_name)
                        except:
                            raise StandardError("BibDoc of a name %s does not exist within a record" % \
                                                    (bibdoc1_name, ))
                else:
                    # resolving temporary identifier
                    bibdoc1_id = resolve_identifier(tmp_ids, bibdoc1_id)
                    if bibdoc1_name != None:
                        write_message("WARNING: both name and id of the first document of a relation have been specified. Ignoring the name", stream=sys.stderr)

                bibdoc1_ver = _get_subfield_value(brt, "v")
                if not (bibdoc1_ver is None):
                    bibdoc1_ver = resolve_identifier(tmp_vers, bibdoc1_ver)
                bibdoc1_fmt = _get_subfield_value(brt, "f")

                bibdoc2_id = _get_subfield_value(brt, "j")
                bibdoc2_name = _get_subfield_value(brt, "o")

                if bibdoc2_id == None:
                    if bibdoc2_name == None:
                        raise StandardError("Incorrect relation. Neither name nor identifier of the second obejct has been specified")
                    else:
                        # retrieving the ID based on the document name (inside current record)
                        # The document is attached to current record.
                        try:
                            bibdoc2_id = recordDocs.get_docid(bibdoc2_name)
                        except:
                            raise StandardError("BibDoc of a name %s does not exist within a record" % (bibdoc2_name, ))
                else:
                    bibdoc2_id = resolve_identifier(tmp_ids, bibdoc2_id)
                    if bibdoc2_name != None:
                        write_message("WARNING: both name and id of the first document of a relation have been specified. Ignoring the name", stream=sys.stderr)



                bibdoc2_ver = _get_subfield_value(brt, "w")
                if not (bibdoc2_ver is None):
                    bibdoc2_ver = resolve_identifier(tmp_vers, bibdoc2_ver)
                bibdoc2_fmt = _get_subfield_value(brt, "g")

            control_command = _get_subfield_value(brt, "d")
            relation_type = _get_subfield_value(brt, "t")

            if not relation_type and not relation_id:
                raise StandardError("The relation type must be specified")

            more_info = _get_subfield_value(brt, "m")

            # the relation id might be specified in the case of updating
            # MoreInfo table instead of other fields
            rel_obj = None
            if not relation_id:
                rels = BibRelation.get_relations(rel_type = relation_type,
                                                 bibdoc1_id = bibdoc1_id,
                                                 bibdoc2_id = bibdoc2_id,
                                                 bibdoc1_ver = bibdoc1_ver,
                                                 bibdoc2_ver = bibdoc2_ver,
                                                 bibdoc1_fmt = bibdoc1_fmt,
                                                 bibdoc2_fmt = bibdoc2_fmt)
                if len(rels) > 0:
                    rel_obj = rels[0]
                    relation_id = rel_obj.id
            else:
                rel_obj = BibRelation(rel_id=relation_id)

            relations_to_create.append((relation_id, bibdoc1_id, bibdoc1_ver,
                                 bibdoc1_fmt, bibdoc2_id, bibdoc2_ver,
                                 bibdoc2_fmt, relation_type, more_info,
                                 rel_obj, control_command))

    record_delete_field(record, 'BDR', ' ', ' ')

    if mode in ("insert", "replace_or_insert", "append", "correct", "replace"):
        # now creating relations between objects based on the data
        if not pretend:
            for (relation_id, bibdoc1_id, bibdoc1_ver, bibdoc1_fmt,
                 bibdoc2_id,  bibdoc2_ver, bibdoc2_fmt, rel_type,
                 more_info, rel_obj, control_command) in relations_to_create:
                if rel_obj == None:
                    rel_obj = BibRelation.create(bibdoc1_id = bibdoc1_id,
                                                    bibdoc1_ver = bibdoc1_ver,
                                                    bibdoc1_fmt = bibdoc1_fmt,
                                                    bibdoc2_id = bibdoc2_id,
                                                    bibdoc2_ver = bibdoc2_ver,
                                                    bibdoc2_fmt = bibdoc2_fmt,
                                                    rel_type = rel_type)
                    relation_id = rel_obj.id

                if mode in ("replace"):
                    # Clearing existing MoreInfo content
                    rel_obj.get_more_info().delete()

                if more_info:
                    MoreInfo.create_from_serialised(more_info, relation = relation_id)

                if control_command == "DELETE":
                    rel_obj.delete()
    else:
        write_message("BDR tag is not processed in the %s mode" % (mode, ))
    return record

def elaborate_fft_tags(record, rec_id, mode, pretend=False,
                       tmp_ids = {}, tmp_vers = {}, bibrecdocs=None):
    """
    Process FFT tags that should contain $a with file pathes or URLs
    to get the fulltext from.  This function enriches record with
    proper 8564 URL tags, downloads fulltext files and stores them
    into var/data structure where appropriate.

    CFG_BIBUPLOAD_WGET_SLEEP_TIME defines time to sleep in seconds in
    between URL downloads.

    Note: if an FFT tag contains multiple $a subfields, we upload them
    into different 856 URL tags in the metadata.  See regression test
    case test_multiple_fft_insert_via_http().
    """

    # Let's define some handy sub procedure.
    def _add_new_format(bibdoc, url, docformat, docname, doctype, newname, description, comment, flags, modification_date, pretend=False):
        """Adds a new format for a given bibdoc. Returns True when everything's fine."""
        write_message('Add new format to %s url: %s, format: %s, docname: %s, doctype: %s, newname: %s, description: %s, comment: %s, flags: %s, modification_date: %s' % (repr(bibdoc), url, docformat, docname, doctype, newname, description, comment, flags, modification_date), verbose=9)
        try:
            if not url: # Not requesting a new url. Just updating comment & description
                return _update_description_and_comment(bibdoc, docname, docformat, description, comment, flags, pretend=pretend)
            try:
                if not pretend:
                    bibdoc.add_file_new_format(url, description=description, comment=comment, flags=flags, modification_date=modification_date)
            except StandardError, e:
                write_message("('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s') not inserted because format already exists (%s)." % (url, docformat, docname, doctype, newname, description, comment, flags, modification_date, e), stream=sys.stderr)
                raise
        except Exception, e:
            write_message("ERROR: in adding '%s' as a new format because of: %s" % (url, e), stream=sys.stderr)
            raise
        return True

    def _add_new_version(bibdoc, url, docformat, docname, doctype, newname, description, comment, flags, modification_date, pretend=False):
        """Adds a new version for a given bibdoc. Returns True when everything's fine."""
        write_message('Add new version to %s url: %s, format: %s, docname: %s, doctype: %s, newname: %s, description: %s, comment: %s, flags: %s' % (repr(bibdoc), url, docformat, docname, doctype, newname, description, comment, flags), verbose=9)
        try:
            if not url:
                return _update_description_and_comment(bibdoc, docname, docformat, description, comment, flags, pretend=pretend)
            try:
                if not pretend:
                    bibdoc.add_file_new_version(url, description=description, comment=comment, flags=flags, modification_date=modification_date)
            except StandardError, e:
                write_message("('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s') not inserted because '%s'." % (url, docformat, docname, doctype, newname, description, comment, flags, modification_date, e), stream=sys.stderr)
                raise
        except Exception, e:
            write_message("ERROR: in adding '%s' as a new version because of: %s" % (url, e), stream=sys.stderr)
            raise
        return True

    def _update_description_and_comment(bibdoc, docname, docformat, description, comment, flags, pretend=False):
        """Directly update comments and descriptions."""
        write_message('Just updating description and comment for %s with format %s with description %s, comment %s and flags %s' % (docname, docformat, description, comment, flags), verbose=9)
        try:
            if not pretend:
                bibdoc.set_description(description, docformat)
                bibdoc.set_comment(comment, docformat)
                for flag in CFG_BIBDOCFILE_AVAILABLE_FLAGS:
                    if flag in flags:
                        bibdoc.set_flag(flag, docformat)
                    else:
                        bibdoc.unset_flag(flag, docformat)
        except StandardError, e:
            write_message("('%s', '%s', '%s', '%s', '%s') description and comment not updated because '%s'." % (docname, docformat, description, comment, flags, e))
            raise
        return True

    def _process_document_moreinfos(more_infos, docname, version, docformat, mode):
        if not mode in ('correct', 'append', 'replace_or_insert', 'replace', 'insert'):
            #print "exited because the mode is incorrect"
            return

        docid = None
        try:
            docid = bibrecdocs.get_docid(docname)
        except:
            raise StandardError("MoreInfo: No document of a given name associated with the record")

        if not version:
            # We have to retrieve the most recent version ...
            version = bibrecdocs.get_bibdoc(docname).get_latest_version()

        doc_moreinfo_s, version_moreinfo_s, version_format_moreinfo_s, format_moreinfo_s = more_infos

        if mode in ("replace", "replace_or_insert"):
            if doc_moreinfo_s: #only if specified, otherwise do not touch
                MoreInfo(docid = docid).delete()

            if format_moreinfo_s: #only if specified... otherwise do not touch
                MoreInfo(docid = docid, docformat = docformat).delete()

        if not doc_moreinfo_s is None:
            MoreInfo.create_from_serialised(ser_str = doc_moreinfo_s, docid = docid)

        if not version_moreinfo_s is None:
            MoreInfo.create_from_serialised(ser_str = version_moreinfo_s,
                                            docid = docid, version = version)
        if not version_format_moreinfo_s is None:
            MoreInfo.create_from_serialised(ser_str = version_format_moreinfo_s,
                                            docid = docid, version = version,
                                            docformat = docformat)
        if not format_moreinfo_s is None:
            MoreInfo.create_from_serialised(ser_str = format_moreinfo_s,
                                            docid = docid, docformat = docformat)

    if mode == 'delete':
        raise StandardError('FFT tag specified but bibupload executed in --delete mode')

    tuple_list = extract_tag_from_record(record, 'FFT')


    if tuple_list: # FFT Tags analysis
        write_message("FFTs: "+str(tuple_list), verbose=9)
        docs = {} # docnames and their data

        for fft in record_get_field_instances(record, 'FFT', ' ', ' '):
            # Very first, we retrieve the potentially temporary odentifiers...
            #even if the rest fails, we should include them in teh dictionary

            version = _get_subfield_value(fft, 'v', '')
            # checking if version is temporary... if so, filling a different varaible
            is_tmp_ver, bibdoc_tmpver = parse_identifier(version)
            if is_tmp_ver:
                version = None
            else:
                bibdoc_tmpver = None
            if not version: #treating cases of empty string etc...
                version = None

            bibdoc_tmpid = field_get_subfield_values(fft, 'i')
            if bibdoc_tmpid:
                bibdoc_tmpid = bibdoc_tmpid[0]
            else:
                bibdoc_tmpid
            is_tmp_id, bibdoc_tmpid = parse_identifier(bibdoc_tmpid)
            if not is_tmp_id:
                bibdoc_tmpid = None


            # In the case of having temporary id's, we dont resolve them yet but signaklise that they have been used
            # value -1 means that identifier has been declared but not assigned a value yet
            if bibdoc_tmpid:
                if bibdoc_tmpid in tmp_ids:
                    write_message("WARNING: the temporary identifier %s has been declared more than once. Ignoring the second occurance" % (bibdoc_tmpid, ), stream=sys.stderr)
                else:
                    tmp_ids[bibdoc_tmpid] = -1

            if bibdoc_tmpver:
                if bibdoc_tmpver in tmp_vers:
                    write_message("WARNING: the temporary version identifier %s has been declared more than once. Ignoring the second occurance" % (bibdoc_tmpver, ), stream=sys.stderr)
                else:
                    tmp_vers[bibdoc_tmpver] = -1


            # Let's discover the type of the document
            # This is a legacy field and will not be enforced any particular
            # check on it.
            doctype = _get_subfield_value(fft, 't', 'Main') #Default is Main

            # Let's discover the url.
            url = field_get_subfield_values(fft, 'a')
            if url:
                url = url[0]
                try:
                    check_valid_url(url)
                except StandardError, e:
                    raise StandardError, "fft '%s' specifies in $a a location ('%s') with problems: %s" % (fft, url, e)
            else:
                url = ''

#TODO: a lot of code can be compactified using similar syntax ... should be more readable on the longer scale
#      maybe right side expressions look a bit cryptic, but the elaborate_fft function would be much clearer


            if mode == 'correct' and doctype != 'FIX-MARC':
                arg2 = ""
            else:
                arg2 = KEEP_OLD_VALUE
            description =  _get_subfield_value(fft, 'd', arg2)

            # Let's discover the description
#            description = field_get_subfield_values(fft, 'd')
#            if description != []:
#                description = description[0]
#            else:
#                if mode == 'correct' and doctype != 'FIX-MARC':
                    ## If the user require to correct, and do not specify
                    ## a description this means she really want to
                    ## modify the description.
#                    description = ''
#                else:
#                    description = KEEP_OLD_VALUE

            # Let's discover the desired docname to be created/altered
            name = field_get_subfield_values(fft, 'n')
            if name:
                ## Let's remove undesired extensions
                name = file_strip_ext(name[0] + '.pdf')
            else:
                if url:
                    name = get_docname_from_url(url)
                elif mode != 'correct' and doctype != 'FIX-MARC':
                    raise StandardError, "WARNING: fft '%s' doesn't specifies either a location in $a or a docname in $n" % str(fft)
                else:
                    continue

            # Let's discover the desired new docname in case we want to change it
            newname = field_get_subfield_values(fft, 'm')
            if newname:
                newname = file_strip_ext(newname[0] + '.pdf')
            else:
                newname = name

            # Let's discover the desired format
            docformat = field_get_subfield_values(fft, 'f')
            if docformat:
                docformat = normalize_format(docformat[0])
            else:
                if url:
                    docformat = guess_format_from_url(url)
                else:
                    docformat = ""

            # Let's discover the icon
            icon = field_get_subfield_values(fft, 'x')
            if icon != []:
                icon = icon[0]
                if icon != KEEP_OLD_VALUE:
                    try:
                        check_valid_url(icon)
                    except StandardError, e:
                        raise StandardError, "fft '%s' specifies in $x an icon ('%s') with problems: %s" % (fft, icon, e)
            else:
                icon = ''

            # Let's discover the comment
            comment = field_get_subfield_values(fft, 'z')
            if comment != []:
                comment = comment[0]
            else:
                if mode == 'correct' and doctype != 'FIX-MARC':
                    ## See comment on description
                    comment = ''
                else:
                    comment = KEEP_OLD_VALUE

            # Let's discover the restriction
            restriction = field_get_subfield_values(fft, 'r')
            if restriction != []:
                restriction = restriction[0]
            else:
                if mode == 'correct' and doctype != 'FIX-MARC':
                    ## See comment on description
                    restriction = ''
                else:
                    restriction = KEEP_OLD_VALUE


            document_moreinfo = _get_subfield_value(fft, 'w')
            version_moreinfo = _get_subfield_value(fft, 'p')
            version_format_moreinfo = _get_subfield_value(fft, 'b')
            format_moreinfo = _get_subfield_value(fft, 'u')


            # Let's discover the timestamp of the file (if any)
            timestamp = field_get_subfield_values(fft, 's')
            if timestamp:
                try:
                    timestamp = datetime(*(time.strptime(timestamp[0], "%Y-%m-%d %H:%M:%S")[:6]))
                except ValueError:
                    write_message('WARNING: The timestamp is not in a good format, thus will be ignored. The format should be YYYY-MM-DD HH:MM:SS', stream=sys.stderr)
                    timestamp = ''
            else:
                timestamp = ''

            flags = field_get_subfield_values(fft, 'o')

            for flag in flags:
                if flag not in CFG_BIBDOCFILE_AVAILABLE_FLAGS:
                    raise StandardError, "fft '%s' specifies a non available flag: %s" % (fft, flag)

            if docs.has_key(name): # new format considered
                (doctype2, newname2, restriction2, version2, urls, dummybibdoc_moreinfos2, dummybibdoc_tmpid2, dummybibdoc_tmpver2 ) = docs[name]
                if doctype2 != doctype:
                    raise StandardError, "fft '%s' specifies a different doctype from previous fft with docname '%s'" % (str(fft), name)
                if newname2 != newname:
                    raise StandardError, "fft '%s' specifies a different newname from previous fft with docname '%s'" % (str(fft), name)
                if restriction2 != restriction:
                    raise StandardError, "fft '%s' specifies a different restriction from previous fft with docname '%s'" % (str(fft), name)
                if version2 != version:
                    raise StandardError, "fft '%s' specifies a different version than the previous fft with docname '%s'" % (str(fft), name)
                for (dummyurl2, format2, dummydescription2, dummycomment2, dummyflags2, dummytimestamp2) in urls:
                    if docformat == format2:
                        raise StandardError, "fft '%s' specifies a second file '%s' with the same format '%s' from previous fft with docname '%s'" % (str(fft), url, docformat, name)
                if url or docformat:
                    urls.append((url, docformat, description, comment, flags, timestamp))
                if icon:
                    urls.append((icon, icon[len(file_strip_ext(icon)):] + ';icon', description, comment, flags, timestamp))
            else:
                if url or docformat:
                    docs[name] = (doctype, newname, restriction, version, [(url, docformat, description, comment, flags, timestamp)], [document_moreinfo, version_moreinfo, version_format_moreinfo, format_moreinfo], bibdoc_tmpid, bibdoc_tmpver)
                    if icon:
                        docs[name][4].append((icon, icon[len(file_strip_ext(icon)):] + ';icon', description, comment, flags, timestamp))
                elif icon:
                    docs[name] = (doctype, newname, restriction, version, [(icon, icon[len(file_strip_ext(icon)):] + ';icon', description, comment, flags, timestamp)], [document_moreinfo, version_moreinfo, version_format_moreinfo, format_moreinfo], bibdoc_tmpid, bibdoc_tmpver)
                else:
                    docs[name] = (doctype, newname, restriction, version, [], [document_moreinfo, version_moreinfo, version_format_moreinfo, format_moreinfo], bibdoc_tmpid, bibdoc_tmpver)

        write_message('Result of FFT analysis:\n\tDocs: %s' % (docs,), verbose=9)

        # Let's remove all FFT tags
        record_delete_field(record, 'FFT', ' ', ' ')

        ## Let's pre-download all the URLs to see if, in case of mode 'correct' or 'append'
        ## we can avoid creating a new revision.


        for docname, (doctype, newname, restriction, version, urls, more_infos, bibdoc_tmpid, bibdoc_tmpver ) in docs.items():
            downloaded_urls = []
            try:
                bibdoc = bibrecdocs.get_bibdoc(docname)
            except InvenioBibDocFileError:
                ## A bibdoc with the given docname does not exists.
                ## So there is no chance we are going to revise an existing
                ## format with an identical file :-)
                bibdoc = None

            new_revision_needed = False
            for url, docformat, description, comment, flags, timestamp in urls:
                if url:
                    try:
                        downloaded_url = download_url(url, docformat)
                        write_message("%s saved into %s" % (url, downloaded_url), verbose=9)
                    except Exception, err:
                        write_message("ERROR: in downloading '%s' because of: %s" % (url, err), stream=sys.stderr)
                        raise
                    if mode == 'correct' and bibdoc is not None and not new_revision_needed:
                        downloaded_urls.append((downloaded_url, docformat, description, comment, flags, timestamp))
                        if not bibrecdocs.check_file_exists(downloaded_url, docformat):
                            new_revision_needed = True
                        else:
                            write_message("WARNING: %s is already attached to bibdoc %s for recid %s" % (url, docname, rec_id), stream=sys.stderr)
                    elif mode == 'append' and bibdoc is not None:
                        if not bibrecdocs.check_file_exists(downloaded_url, docformat):
                            downloaded_urls.append((downloaded_url, docformat, description, comment, flags, timestamp))
                        else:
                            write_message("WARNING: %s is already attached to bibdoc %s for recid %s" % (url, docname, rec_id), stream=sys.stderr)
                    else:
                        downloaded_urls.append((downloaded_url, docformat, description, comment, flags, timestamp))
                else:
                    downloaded_urls.append(('', docformat, description, comment, flags, timestamp))
            if mode == 'correct' and bibdoc is not None and not new_revision_needed:
                ## Since we don't need a new revision (because all the files
                ## that are being uploaded are different)
                ## we can simply remove the urls but keep the other information
                write_message("No need to add a new revision for docname %s for recid %s" % (docname, rec_id), verbose=2)
                docs[docname] = (doctype, newname, restriction, version, [('', docformat, description, comment, flags, timestamp) for (dummy, docformat, description, comment, flags, timestamp) in downloaded_urls], more_infos, bibdoc_tmpid, bibdoc_tmpver)
                for downloaded_url, dummy, dummy, dummy, dummy, dummy in downloaded_urls:
                    ## Let's free up some space :-)
                    if downloaded_url and os.path.exists(downloaded_url):
                        os.remove(downloaded_url)
            else:
                if downloaded_urls or mode != 'append':
                    docs[docname] = (doctype, newname, restriction, version, downloaded_urls, more_infos, bibdoc_tmpid, bibdoc_tmpver)
                else:
                    ## In case we are in append mode and there are no urls to append
                    ## we discard the whole FFT
                    del docs[docname]

        if mode == 'replace': # First we erase previous bibdocs
            if not pretend:
                for bibdoc in bibrecdocs.list_bibdocs():
                    bibdoc.delete()
                    bibrecdocs.dirty = True

        for docname, (doctype, newname, restriction, version, urls, more_infos, bibdoc_tmpid, bibdoc_tmpver) in docs.iteritems():
            write_message("Elaborating olddocname: '%s', newdocname: '%s', doctype: '%s', restriction: '%s', urls: '%s', mode: '%s'" % (docname, newname, doctype, restriction, urls, mode), verbose=9)
            if mode in ('insert', 'replace'): # new bibdocs, new docnames, new marc
                if newname in bibrecdocs.get_bibdoc_names():
                    write_message("('%s', '%s') not inserted because docname already exists." % (newname, urls), stream=sys.stderr)
                    raise StandardError("('%s', '%s') not inserted because docname already exists." % (newname, urls), stream=sys.stderr)
                try:
                    if not pretend:
                        bibdoc = bibrecdocs.add_bibdoc(doctype, newname)
                        bibdoc.set_status(restriction)
                    else:
                        bibdoc = None
                except Exception, e:
                    write_message("('%s', '%s', '%s') not inserted because: '%s'." % (doctype, newname, urls, e), stream=sys.stderr)
                    raise e
                for (url, docformat, description, comment, flags, timestamp) in urls:
                    assert(_add_new_format(bibdoc, url, docformat, docname, doctype, newname, description, comment, flags, timestamp, pretend=pretend))
            elif mode == 'replace_or_insert': # to be thought as correct_or_insert
                try:
                    bibdoc = bibrecdocs.get_bibdoc(docname)
                    found_bibdoc = True
                except InvenioBibDocFileError:
                    found_bibdoc = False
                else:
                    if doctype not in ('PURGE', 'DELETE', 'EXPUNGE', 'REVERT', 'FIX-ALL', 'FIX-MARC', 'DELETE-FILE'):
                        if newname != docname:
                            try:
                                if not pretend:
                                    bibrecdocs.change_name(newname=newname, docid=bibdoc.id)
                                    write_message(lambda: "After renaming: %s" % bibrecdocs, verbose=9)
                            except StandardError, e:
                                write_message('ERROR: in renaming %s to %s: %s' % (docname, newname, e), stream=sys.stderr)
                                raise
                try:
                    bibdoc = bibrecdocs.get_bibdoc(newname)
                    found_bibdoc = True
                except InvenioBibDocFileError:
                    found_bibdoc = False
                else:
                    if doctype == 'PURGE':
                        if not pretend:
                            bibdoc.purge()
                            bibrecdocs.dirty = True
                    elif doctype == 'DELETE':
                        if not pretend:
                            bibdoc.delete()
                            bibrecdocs.dirty = True
                    elif doctype == 'EXPUNGE':
                        if not pretend:
                            bibdoc.expunge()
                            bibrecdocs.dirty = True
                    elif doctype == 'FIX-ALL':
                        if not pretend:
                            bibrecdocs.fix(docname)
                    elif doctype == 'FIX-MARC':
                        pass
                    elif doctype == 'DELETE-FILE':
                        if urls:
                            for (url, docformat, description, comment, flags, timestamp) in urls:
                                if not pretend:
                                    bibdoc.delete_file(docformat, version)
                    elif doctype == 'REVERT':
                        try:
                            if not pretend:
                                bibdoc.revert(version)
                        except Exception, e:
                            write_message('(%s, %s) not correctly reverted: %s' % (newname, version, e), stream=sys.stderr)
                            raise
                    else:
                        if restriction != KEEP_OLD_VALUE:
                            if not pretend:
                                bibdoc.set_status(restriction)
                        # Since the docname already existed we have to first
                        # bump the version by pushing the first new file
                        # then pushing the other files.
                        if urls:
                            (first_url, first_format, first_description, first_comment, first_flags, first_timestamp) = urls[0]
                            other_urls = urls[1:]
                            assert(_add_new_version(bibdoc, first_url, first_format, docname, doctype, newname, first_description, first_comment, first_flags, first_timestamp, pretend=pretend))
                            for (url, docformat, description, comment, flags, timestamp) in other_urls:
                                assert(_add_new_format(bibdoc, url, docformat, docname, doctype, newname, description, comment, flags, timestamp, pretend=pretend))
                    ## Let's refresh the list of bibdocs.
                if not found_bibdoc:
                    if not pretend:
                        bibdoc = bibrecdocs.add_bibdoc(doctype, newname)
                        bibdoc.set_status(restriction)
                        for (url, docformat, description, comment, flags, timestamp) in urls:
                            assert(_add_new_format(bibdoc, url, docformat, docname, doctype, newname, description, comment, flags, timestamp))
            elif mode == 'correct':
                try:
                    bibdoc = bibrecdocs.get_bibdoc(docname)
                    found_bibdoc = True
                except InvenioBibDocFileError:
                    found_bibdoc = False
                else:
                    if doctype not in ('PURGE', 'DELETE', 'EXPUNGE', 'REVERT', 'FIX-ALL', 'FIX-MARC', 'DELETE-FILE'):
                        if newname != docname:
                            try:
                                if not pretend:
                                    bibrecdocs.change_name(newname=newname, docid=bibdoc.id)
                                    write_message(lambda: "After renaming: %s" % bibrecdocs, verbose=9)
                            except StandardError, e:
                                write_message('ERROR: in renaming %s to %s: %s' % (docname, newname, e), stream=sys.stderr)
                                raise
                try:
                    bibdoc = bibrecdocs.get_bibdoc(newname)
                    found_bibdoc = True
                except InvenioBibDocFileError:
                    found_bibdoc = False
                else:
                    if doctype == 'PURGE':
                        if not pretend:
                            bibdoc.purge()
                            bibrecdocs.dirty = True
                    elif doctype == 'DELETE':
                        if not pretend:
                            bibdoc.delete()
                            bibrecdocs.dirty = True
                    elif doctype == 'EXPUNGE':
                        if not pretend:
                            bibdoc.expunge()
                            bibrecdocs.dirty = True
                    elif doctype == 'FIX-ALL':
                        if not pretend:
                            bibrecdocs.fix(newname)
                    elif doctype == 'FIX-MARC':
                        pass
                    elif doctype == 'DELETE-FILE':
                        if urls:
                            for (url, docformat, description, comment, flags, timestamp) in urls:
                                if not pretend:
                                    bibdoc.delete_file(docformat, version)
                    elif doctype == 'REVERT':
                        try:
                            if not pretend:
                                bibdoc.revert(version)
                        except Exception, e:
                            write_message('(%s, %s) not correctly reverted: %s' % (newname, version, e), stream=sys.stderr)
                            raise
                    else:
                        if restriction != KEEP_OLD_VALUE:
                            if not pretend:
                                bibdoc.set_status(restriction)
                        if doctype and doctype != KEEP_OLD_VALUE:
                            if not pretend:
                                bibdoc.change_doctype(doctype)
                        if urls:
                            (first_url, first_format, first_description, first_comment, first_flags, first_timestamp) = urls[0]
                            other_urls = urls[1:]
                            assert(_add_new_version(bibdoc, first_url, first_format, docname, doctype, newname, first_description, first_comment, first_flags, first_timestamp, pretend=pretend))
                            for (url, docformat, description, comment, flags, timestamp) in other_urls:
                                assert(_add_new_format(bibdoc, url, docformat, docname, doctype, newname, description, comment, flags, timestamp, pretend=pretend))
                if not found_bibdoc:
                    if doctype in ('PURGE', 'DELETE', 'EXPUNGE', 'FIX-ALL', 'FIX-MARC', 'DELETE-FILE', 'REVERT'):
                        write_message("('%s', '%s', '%s') not performed because '%s' docname didn't existed." % (doctype, newname, urls, docname), stream=sys.stderr)
                        raise StandardError
                    else:
                        if not pretend:
                            bibdoc = bibrecdocs.add_bibdoc(doctype, newname)
                            bibdoc.set_status(restriction)
                            for (url, docformat, description, comment, flags, timestamp) in urls:
                                assert(_add_new_format(bibdoc, url, docformat, docname, doctype, newname, description, comment, flags, timestamp))
            elif mode == 'append':
                found_bibdoc = False
                try:
                    bibdoc = bibrecdocs.get_bibdoc(docname)
                    found_bibdoc = True
                except InvenioBibDocFileError:
                    found_bibdoc = False
                else:
                    for (url, docformat, description, comment, flags, timestamp) in urls:
                        assert(_add_new_format(bibdoc, url, docformat, docname, doctype, newname, description, comment, flags, timestamp, pretend=pretend))
                if not found_bibdoc:
                    try:
                        if not pretend:
                            bibdoc = bibrecdocs.add_bibdoc(doctype, docname)
                            bibdoc.set_status(restriction)
                            for (url, docformat, description, comment, flags, timestamp) in urls:
                                assert(_add_new_format(bibdoc, url, docformat, docname, doctype, newname, description, comment, flags, timestamp))
                    except Exception, e:
                        register_exception()
                        write_message("('%s', '%s', '%s') not appended because: '%s'." % (doctype, newname, urls, e), stream=sys.stderr)
                        raise
            if not pretend and doctype not in ('PURGE', 'DELETE', 'EXPUNGE'):
                _process_document_moreinfos(more_infos, newname, version, urls and urls[0][1], mode)

            # resolving temporary version and identifier
            if bibdoc_tmpid:
                if bibdoc_tmpid in tmp_ids and tmp_ids[bibdoc_tmpid] != -1:
                    write_message("WARNING: the temporary identifier %s has been declared more than once. Ignoring the second occurance" % (bibdoc_tmpid, ), stream=sys.stderr)
                else:
                    tmp_ids[bibdoc_tmpid] = bibrecdocs.get_docid(docname)

            if bibdoc_tmpver:
                if bibdoc_tmpver in tmp_vers and tmp_vers[bibdoc_tmpver] != -1:
                    write_message("WARNING: the temporary version identifier %s has been declared more than once. Ignoring the second occurance" % (bibdoc_tmpver, ), stream=sys.stderr)
                else:
                    if version == None:
                        if version:
                            tmp_vers[bibdoc_tmpver] = version
                        else:
                            tmp_vers[bibdoc_tmpver] = bibrecdocs.get_bibdoc(docname).get_latest_version()
                    else:
                        tmp_vers[bibdoc_tmpver] = version
    return record


### Update functions

def update_bibrec_date(now, bibrec_id, insert_mode_p, pretend=False):
    """Update the date of the record in bibrec table """
    if insert_mode_p:
        query = """UPDATE bibrec SET creation_date=%s, modification_date=%s WHERE id=%s"""
        params = (now, now, bibrec_id)
    else:
        query = """UPDATE bibrec SET modification_date=%s WHERE id=%s"""
        params = (now, bibrec_id)
    if not pretend:
        run_sql(query, params)
    write_message("   -Update record creation/modification date: DONE" , verbose=2)

def update_bibfmt_format(id_bibrec, format_value, format_name, modification_date=None, pretend=False):
    """Update the format in the table bibfmt"""
    if modification_date is None:
        modification_date = time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        try:
            time.strptime(modification_date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            modification_date = '1970-01-01 00:00:00'

    # We check if the format is already in bibFmt
    nb_found = find_record_format(id_bibrec, format_name)
    if nb_found == 1:
        # we are going to update the format
        # compress the format_value value
        pickled_format_value =  compress(format_value)
        # update the format:
        query = """UPDATE LOW_PRIORITY bibfmt SET last_updated=%s, value=%s WHERE id_bibrec=%s AND format=%s"""
        params = (modification_date, pickled_format_value, id_bibrec, format_name)
        if not pretend:
            row_id  = run_sql(query, params)
        if not pretend and row_id is None:
            write_message("   ERROR: during update_bibfmt_format function", verbose=1, stream=sys.stderr)
            return 1
        else:
            write_message("   -Update the format %s in bibfmt: DONE" % format_name , verbose=2)
            return 0

    elif nb_found > 1:
        write_message("   Failed: Same format %s found several time in bibfmt for the same record." % format_name, verbose=1, stream=sys.stderr)
        return 1
    else:
        # Insert the format information in BibFMT
        res = insert_bibfmt(id_bibrec, format_value, format_name, modification_date, pretend=pretend)
        if res is None:
            write_message("   ERROR: during insert_bibfmt", verbose=1, stream=sys.stderr)
            return 1
        else:
            write_message("   -Insert the format %s in bibfmt: DONE" % format_name , verbose=2)
            return 0

def delete_bibfmt_format(id_bibrec, format_name, pretend=False):
    """
    Delete format FORMAT_NAME from bibfmt table fo record ID_BIBREC.
    """
    if not pretend:
        run_sql("DELETE LOW_PRIORITY FROM bibfmt WHERE id_bibrec=%s and format=%s", (id_bibrec, format_name))
    return 0


def archive_marcxml_for_history(recID, affected_fields, pretend=False):
    """
    Archive current MARCXML format of record RECID from BIBFMT table
    into hstRECORD table.  Useful to keep MARCXML history of records.

    Return 0 if everything went fine.  Return 1 otherwise.
    """
    res = run_sql("SELECT id_bibrec, value, last_updated FROM bibfmt WHERE format='xm' AND id_bibrec=%s",
                    (recID,))

    db_affected_fields = ""
    if affected_fields:
        tmp_affected_fields = {}
        for field in affected_fields:
            if field.isdigit(): #hack for tags from RevisionVerifier
                for ind in affected_fields[field]:
                    tmp_affected_fields[(field + ind[0] + ind[1] + "%").replace(" ", "_")] = 1
            else:
                pass #future implementation for fields
        tmp_affected_fields = tmp_affected_fields.keys()
        tmp_affected_fields.sort()
        db_affected_fields = ",".join(tmp_affected_fields)
    if res and not pretend:
        run_sql("""INSERT INTO hstRECORD (id_bibrec, marcxml, job_id, job_name, job_person, job_date, job_details, affected_fields)
                                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (res[0][0], res[0][1], task_get_task_param('task_id', 0), 'bibupload', task_get_task_param('user', 'UNKNOWN'), res[0][2],
                    'mode: ' + task_get_option('mode', 'UNKNOWN') + '; file: ' + task_get_option('file_path', 'UNKNOWN') + '.',
                db_affected_fields))
    return 0

def update_database_with_metadata(record, rec_id, oai_rec_id="oai", affected_tags=None, pretend=False):
    """Update the database tables with the record and the record id given in parameter"""

    # extract only those tags that have been affected.
    # check happens at subfield level. This is to prevent overhead
    # associated with inserting already existing field with given ind pair
    write_message("update_database_with_metadata: record=%s, rec_id=%s, oai_rec_id=%s, affected_tags=%s" % (record, rec_id, oai_rec_id, affected_tags), verbose=9)
    tmp_record = {}
    if affected_tags:
        for tag in record.keys():
            if tag in affected_tags.keys():
                write_message("     -Tag %s found to be modified.Setting up for update" % tag, verbose=9)
                # initialize new list to hold affected field
                new_data_tuple_list = []
                for data_tuple in record[tag]:
                    ind1 = data_tuple[1]
                    ind2 = data_tuple[2]
                    if (ind1, ind2) in affected_tags[tag]:
                        write_message("     -Indicator pair (%s, %s) added to update list" % (ind1, ind2), verbose=9)
                        new_data_tuple_list.append(data_tuple)
                tmp_record[tag] = new_data_tuple_list
        write_message(lambda: "     -Modified fields: \n%s" % record_xml_output(tmp_record), verbose=2)
    else:
        tmp_record = record

    for tag in tmp_record.keys():
        # check if tag is not a special one:
        if tag not in CFG_BIBUPLOAD_SPECIAL_TAGS:
            # for each tag there is a list of tuples representing datafields
            tuple_list = tmp_record[tag]
            # this list should contain the elements of a full tag [tag, ind1, ind2, subfield_code]
            tag_list = []
            tag_list.append(tag)
            for single_tuple in tuple_list:
                # these are the contents of a single tuple
                subfield_list = single_tuple[0]
                ind1 = single_tuple[1]
                ind2 = single_tuple[2]
                # append the ind's to the full tag
                if ind1 == '' or ind1 == ' ':
                    tag_list.append('_')
                else:
                    tag_list.append(ind1)
                if ind2 == '' or ind2 == ' ':
                    tag_list.append('_')
                else:
                    tag_list.append(ind2)
                datafield_number = single_tuple[4]

                if tag in CFG_BIBUPLOAD_SPECIAL_TAGS:
                    # nothing to do for special tags (FFT, BDR, BDM)
                    pass
                elif tag in CFG_BIBUPLOAD_CONTROLFIELD_TAGS and tag != "001":
                    value = single_tuple[3]
                    # get the full tag
                    full_tag = ''.join(tag_list)

                    # update the tables
                    write_message("   insertion of the tag "+full_tag+" with the value "+value, verbose=9)
                    # insert the tag and value into into bibxxx
                    (table_name, bibxxx_row_id) = insert_record_bibxxx(full_tag, value, pretend=pretend)
                    #print 'tname, bibrow', table_name, bibxxx_row_id;
                    if table_name is None or bibxxx_row_id is None:
                        write_message("   Failed: during insert_record_bibxxx", verbose=1, stream=sys.stderr)
                    # connect bibxxx and bibrec with the table bibrec_bibxxx
                    res = insert_record_bibrec_bibxxx(table_name, bibxxx_row_id, datafield_number, rec_id, pretend=pretend)
                    if res is None:
                        write_message("   Failed: during insert_record_bibrec_bibxxx", verbose=1, stream=sys.stderr)
                else:
                    # get the tag and value from the content of each subfield
                    for subfield in subfield_list:
                        subtag = subfield[0]
                        value = subfield[1]
                        tag_list.append(subtag)
                        # get the full tag
                        full_tag = ''.join(tag_list)
                        # update the tables
                        write_message("   insertion of the tag "+full_tag+" with the value "+value, verbose=9)
                        # insert the tag and value into into bibxxx
                        (table_name, bibxxx_row_id) = insert_record_bibxxx(full_tag, value, pretend=pretend)
                        if table_name is None or bibxxx_row_id is None:
                            write_message("   Failed: during insert_record_bibxxx", verbose=1, stream=sys.stderr)
                        # connect bibxxx and bibrec with the table bibrec_bibxxx
                        res = insert_record_bibrec_bibxxx(table_name, bibxxx_row_id, datafield_number, rec_id, pretend=pretend)
                        if res is None:
                            write_message("   Failed: during insert_record_bibrec_bibxxx", verbose=1, stream=sys.stderr)
                        # remove the subtag from the list
                        tag_list.pop()
                tag_list.pop()
                tag_list.pop()
            tag_list.pop()
    write_message("   -Update the database with metadata: DONE", verbose=2)

    log_record_uploading(oai_rec_id, task_get_task_param('task_id', 0), rec_id, 'P', pretend=pretend)

def append_new_tag_to_old_record(record, rec_old):
    """Append new tags to a old record"""

    def _append_tag(tag):
        if tag in CFG_BIBUPLOAD_CONTROLFIELD_TAGS:
            if tag == '001':
                pass
            else:
                # if it is a controlfield, just access the value
                for single_tuple in record[tag]:
                    controlfield_value = single_tuple[3]
                    # add the field to the old record
                    newfield_number = record_add_field(rec_old, tag,
                        controlfield_value=controlfield_value)
                    if newfield_number is None:
                        write_message("   ERROR: when adding the field"+tag, verbose=1, stream=sys.stderr)
        else:
            # For each tag there is a list of tuples representing datafields
            for single_tuple in record[tag]:
                # We retrieve the information of the tag
                subfield_list = single_tuple[0]
                ind1 = single_tuple[1]
                ind2 = single_tuple[2]
                if '%s%s%s' % (tag, ind1 == ' ' and '_' or ind1, ind2 == ' ' and '_' or ind2) in (CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:5], CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG[:5]):
                    ## We don't want to append the external identifier
                    ## if it is already existing.
                    if record_find_field(rec_old, tag, single_tuple)[0] is not None:
                        write_message("      Not adding tag: %s ind1=%s ind2=%s subfields=%s: it's already there" % (tag, ind1, ind2, subfield_list), verbose=9)
                        continue
                # We add the datafield to the old record
                write_message("      Adding tag: %s ind1=%s ind2=%s subfields=%s" % (tag, ind1, ind2, subfield_list), verbose=9)
                newfield_number = record_add_field(rec_old, tag, ind1,
                    ind2, subfields=subfield_list)
                if newfield_number is None:
                    write_message("   ERROR: when adding the field"+tag, verbose=1, stream=sys.stderr)

    # Go through each tag in the appended record
    for tag in record:
        _append_tag(tag)
    return rec_old

def copy_strong_tags_from_old_record(record, rec_old):
    """
    Look for strong tags in RECORD and REC_OLD.  If no strong tags are
    found in RECORD, then copy them over from REC_OLD.  This function
    modifies RECORD structure on the spot.
    """
    for strong_tag in CFG_BIBUPLOAD_STRONG_TAGS:
        if not record_get_field_instances(record, strong_tag, strong_tag[3:4] or '%', strong_tag[4:5] or '%'):
            strong_tag_old_field_instances = record_get_field_instances(rec_old, strong_tag)
            if strong_tag_old_field_instances:
                for strong_tag_old_field_instance in strong_tag_old_field_instances:
                    sf_vals, fi_ind1, fi_ind2, controlfield, dummy = strong_tag_old_field_instance
                    record_add_field(record, strong_tag, fi_ind1, fi_ind2, controlfield, sf_vals)
    return

### Delete functions
def delete_tags(record, rec_old):
    """
    Returns a record structure with all the fields in rec_old minus the
    fields in record.

    @param record: The record containing tags to delete.
    @type record: record structure

    @param rec_old: The original record.
    @type rec_old: record structure

    @return: The modified record.
    @rtype: record structure
    """
    returned_record = copy.deepcopy(rec_old)
    for tag, fields in record.iteritems():
        if tag in ('001', ):
            continue
        for field in fields:
            local_position = record_find_field(returned_record, tag, field)[1]
            if local_position is not None:
                record_delete_field(returned_record, tag, field_position_local=local_position)
    return returned_record

def delete_tags_to_correct(record, rec_old):
    """
    Delete tags from REC_OLD which are also existing in RECORD.  When
    deleting, pay attention not only to tags, but also to indicators,
    so that fields with the same tags but different indicators are not
    deleted.
    """
    ## Some fields are controlled via provenance information.
    ## We should re-add saved fields at the end.
    fields_to_readd = {}
    for tag in CFG_BIBUPLOAD_CONTROLLED_PROVENANCE_TAGS:
        if tag[:3] in record:
            tmp_field_instances = record_get_field_instances(record, tag[:3], tag[3], tag[4]) ## Let's discover the provenance that will be updated
            provenances_to_update = []
            for instance in tmp_field_instances:
                for code, value in instance[0]:
                    if code == tag[5]:
                        if value not in provenances_to_update:
                            provenances_to_update.append(value)
                        break
                else:
                    ## The provenance is not specified.
                    ## let's add the special empty provenance.
                    if '' not in provenances_to_update:
                        provenances_to_update.append('')
            potential_fields_to_readd = record_get_field_instances(rec_old, tag[:3], tag[3], tag[4]) ## Let's take all the field corresponding to tag
            ## Let's save apart all the fields that should be updated, but
            ## since they have a different provenance not mentioned in record
            ## they should be preserved.
            fields = []
            for sf_vals, ind1, ind2, dummy_cf, dummy_line in potential_fields_to_readd:
                for code, value in sf_vals:
                    if code == tag[5]:
                        if value not in provenances_to_update:
                            fields.append(sf_vals)
                        break
                else:
                    if '' not in provenances_to_update:
                        ## Empty provenance, let's protect in any case
                        fields.append(sf_vals)
            fields_to_readd[tag] = fields

    # browse through all the tags from the MARCXML file:
    for tag in record:
        # check if the tag exists in the old record too:
        if tag in rec_old and tag != '001':
            # the tag does exist, so delete all record's tag+ind1+ind2 combinations from rec_old
            for dummy_sf_vals, ind1, ind2, dummy_cf, dummyfield_number in record[tag]:
                write_message("      Delete tag: " + tag + " ind1=" + ind1 + " ind2=" + ind2, verbose=9)
                record_delete_field(rec_old, tag, ind1, ind2)

    ## Ok, we readd necessary fields!
    for tag, fields in fields_to_readd.iteritems():
        for sf_vals in fields:
            write_message("      Adding tag: " + tag[:3] + " ind1=" + tag[3] + " ind2=" + tag[4] + " code=" + str(sf_vals), verbose=9)
            record_add_field(rec_old, tag[:3], tag[3], tag[4], subfields=sf_vals)

def delete_bibrec_bibxxx(record, id_bibrec, affected_tags={}, pretend=False):
    """Delete the database record from the table bibxxx given in parameters"""

    # we clear all the rows from bibrec_bibxxx from the old record
    # clearing only those tags that have been modified.
    write_message(lambda: "delete_bibrec_bibxxx(record=%s, id_bibrec=%s, affected_tags=%s)" % (record, id_bibrec, affected_tags), verbose=9)
    for tag in affected_tags:
        # sanity check with record keys just to make sure its fine.
        if tag not in CFG_BIBUPLOAD_SPECIAL_TAGS:
            write_message("%s found in record"%tag, verbose=2)
            # for each name construct the bibrec_bibxxx table name
            table_name = 'bib'+tag[0:2]+'x'
            bibrec_table = 'bibrec_'+table_name
            # delete all the records with proper id_bibrec. Indicators matter for individual affected tags
            tmp_ind_1 = ''
            tmp_ind_2 = ''
            # construct exact tag value using indicators
            for ind_pair in affected_tags[tag]:
                if ind_pair[0] == ' ':
                    tmp_ind_1 = '_'
                else:
                    tmp_ind_1 = ind_pair[0]

                if ind_pair[1] == ' ':
                    tmp_ind_2 = '_'
                else:
                    tmp_ind_2 = ind_pair[1]
                # need to escape incase of underscore so that mysql treats it as a char
                tag_val = tag+"\\"+tmp_ind_1+"\\"+tmp_ind_2 + '%'
                query = """DELETE br.* FROM `%s` br,`%s` b where br.id_bibrec=%%s and br.id_bibxxx=b.id and b.tag like %%s""" % (bibrec_table, table_name)
                params = (id_bibrec, tag_val)
                write_message(query % params, verbose=9)
                if not pretend:
                    run_sql(query, params)
        else:
            write_message("%s not found"%tag, verbose=2)

def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action='runbibupload',
            authorization_msg="BibUpload Task Submission",
            description="""Receive MARC XML file and update appropriate database
tables according to options.
Examples:
    $ bibupload -i input.xml
""",
            help_specific_usage="""  -a, --append\t\tnew fields are appended to the existing record
  -c, --correct\t\tfields are replaced by the new ones in the existing record, except
\t\t\twhen overridden by CFG_BIBUPLOAD_CONTROLLED_PROVENANCE_TAGS
  -i, --insert\t\tinsert the new record in the database
  -r, --replace\t\tthe existing record is entirely replaced by the new one,
\t\t\texcept for fields in CFG_BIBUPLOAD_STRONG_TAGS
  -d, --delete\t\tspecified fields are deleted in existing record
  -n, --notimechange\tdo not change record last modification date when updating
  -o, --holdingpen\tInsert record into holding pen instead of the normal database
  --pretend\t\tdo not really insert/append/correct/replace the input file
  --force\t\twhen --replace, use provided 001 tag values, even if the matching
\t\t\trecord does not exist (thus allocating it on-the-fly)
  --callback-url\tSend via a POST request a JSON-serialized answer (see admin guide), in
\t\t\torder to provide a feedback to an external service about the outcome of the operation.
  --nonce\t\twhen used together with --callback add the nonce value in the JSON message.
  --special-treatment=MODE\tif "oracle" is specified, when used together with --callback_url,
\t\t\tPOST an application/x-www-form-urlencoded request where the JSON message is encoded
\t\t\tinside a form field called "results".
""",
            version=__revision__,
            specific_params=("ircazdnoS:",
                 [
                   "insert",
                   "replace",
                   "correct",
                   "append",
                   "reference",
                   "delete",
                   "notimechange",
                   "holdingpen",
                   "pretend",
                   "force",
                   "callback-url=",
                   "nonce=",
                   "special-treatment=",
                   "stage=",
                 ]),
            task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
            task_run_fnc=task_run_core,
            task_submit_check_options_fnc=task_submit_check_options)

def task_submit_elaborate_specific_parameter(key, value, opts, args): # pylint: disable=W0613
    """ Given the string key it checks it's meaning, eventually using the
    value. Usually it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    eg:
    if key in ['-n', '--number']:
        task_get_option(\1) = value
        return True
    return False
    """

    # No time change option
    if key in ("-n", "--notimechange"):
        task_set_option('notimechange', 1)

    # Insert mode option
    elif key in ("-i", "--insert"):
        if task_get_option('mode') == 'replace':
            # if also replace found, then set to replace_or_insert
            task_set_option('mode', 'replace_or_insert')
        else:
            task_set_option('mode', 'insert')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.abspath(args[0]))

    # Replace mode option
    elif key in ("-r", "--replace"):
        if task_get_option('mode') == 'insert':
            # if also insert found, then set to replace_or_insert
            task_set_option('mode', 'replace_or_insert')
        else:
            task_set_option('mode', 'replace')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.abspath(args[0]))
    # Holding pen mode option
    elif key in ("-o", "--holdingpen"):
        write_message("Holding pen mode", verbose=3)
        task_set_option('mode', 'holdingpen')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.abspath(args[0]))
    # Correct mode option
    elif key in ("-c", "--correct"):
        task_set_option('mode', 'correct')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.abspath(args[0]))

    # Append mode option
    elif key in ("-a", "--append"):
        task_set_option('mode', 'append')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.abspath(args[0]))

    # Deprecated reference mode option (now correct)
    elif key in ("-z", "--reference"):
        task_set_option('mode', 'correct')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.abspath(args[0]))

    elif key in ("-d", "--delete"):
        task_set_option('mode', 'delete')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.abspath(args[0]))

    elif key in ("--pretend",):
        task_set_option('pretend', True)
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.abspath(args[0]))

    elif key in ("--force",):
        task_set_option('force', True)
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.abspath(args[0]))

    elif key in ("--callback-url", ):
        task_set_option('callback_url', value)
    elif key in ("--nonce", ):
        task_set_option('nonce', value)
    elif key in ("--special-treatment", ):
        if value.lower() in CFG_BIBUPLOAD_ALLOWED_SPECIAL_TREATMENTS:
            if value.lower() == 'oracle':
                task_set_option('oracle_friendly', True)
        else:
            print >> sys.stderr, """The specified value is not in the list of allowed special treatments codes: %s""" % CFG_BIBUPLOAD_ALLOWED_SPECIAL_TREATMENTS
            return False
    elif key in ("-S", "--stage"):
        print >> sys.stderr, """WARNING: the --stage parameter is deprecated and ignored."""
    else:
        return False
    return True


def task_submit_check_options():
    """ Reimplement this method for having the possibility to check options
    before submitting the task, in order for example to provide default
    values. It must return False if there are errors in the options.
    """
    if task_get_option('mode') is None:
        write_message("Please specify at least one update/insert mode!",
                      stream=sys.stderr)
        return False

    file_path = task_get_option('file_path')
    if file_path is None:
        write_message("Missing filename! -h for help.", stream=sys.stderr)
        return False

    try:
        open(file_path).read().decode('utf-8')
    except IOError:
        write_message("""File is not accessible: %s""" % file_path,
                      stream=sys.stderr)
        return False
    except UnicodeDecodeError:
        write_message("""File encoding is not valid utf-8: %s""" % file_path,
                      stream=sys.stderr)
        return False

    return True

def writing_rights_p():
    """Return True in case bibupload has the proper rights to write in the
    fulltext file folder."""
    if _WRITING_RIGHTS is not None:
        return _WRITING_RIGHTS
    try:
        if not os.path.exists(CFG_BIBDOCFILE_FILEDIR):
            os.makedirs(CFG_BIBDOCFILE_FILEDIR)
        fd, filename = tempfile.mkstemp(suffix='.txt', prefix='test', dir=CFG_BIBDOCFILE_FILEDIR)
        test = os.fdopen(fd, 'w')
        test.write('TEST')
        test.close()
        if open(filename).read() != 'TEST':
            raise IOError("Can not successfully write and readback %s" % filename)
        os.remove(filename)
    except:
        register_exception(alert_admin=True)
        return False
    return True

def post_results_to_callback_url(results, callback_url):
    write_message("Sending feedback to %s" % callback_url)
    if not CFG_JSON_AVAILABLE:
        from warnings import warn
        warn("--callback-url used but simplejson/json not available")
        return
    json_results = json.dumps(results)

    write_message("Message to send: %s" % json_results, verbose=9)
    ## <scheme>://<netloc>/<path>?<query>#<fragment>
    scheme, dummynetloc, dummypath, dummyquery, dummyfragment = urlparse.urlsplit(callback_url)
    ## See: http://stackoverflow.com/questions/111945/is-there-any-way-to-do-http-put-in-python
    if scheme == 'http':
        opener = urllib2.build_opener(urllib2.HTTPHandler)
    elif scheme == 'https':
        opener = urllib2.build_opener(urllib2.HTTPSHandler)
    else:
        raise ValueError("Scheme not handled %s for callback_url %s" % (scheme, callback_url))
    if task_get_option('oracle_friendly'):
        write_message("Oracle friendly mode requested", verbose=9)
        request = urllib2.Request(callback_url, data=urllib.urlencode({'results': json_results}))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    else:
        request = urllib2.Request(callback_url, data=json_results)
        request.add_header('Content-Type', 'application/json')
    request.add_header('User-Agent', make_user_agent_string('BibUpload'))
    write_message("Headers about to be sent: %s" % request.headers, verbose=9)
    write_message("Data about to be sent: %s" % request.data, verbose=9)
    res = opener.open(request)
    msg = res.read()
    write_message("Result of posting the feedback: %s %s" % (res.code, res.msg), verbose=9)
    write_message("Returned message is: %s" % msg, verbose=9)
    return res

def bibupload_records(records, opt_mode=None, opt_notimechange=0,
                      pretend=False, callback_url=None, results_for_callback=None):
    """perform the task of uploading a set of records
    returns list of (error_code, recid) tuples for separate records
    """
    #Dictionaries maintaining temporary identifiers
    # Structure: identifier -> number

    tmp_ids = {}
    tmp_vers = {}

    results = []
    # The first phase -> assigning meaning to temporary identifiers

    if opt_mode == 'reference':
        ## NOTE: reference mode has been deprecated in favour of 'correct'
        opt_mode = 'correct'

    record = None
    for record in records:
        record_id = record_extract_oai_id(record)
        task_sleep_now_if_required(can_stop_too=True)
        if opt_mode == "holdingpen":
                    #inserting into the holding pen
            write_message("Inserting into holding pen", verbose=3)
            insert_record_into_holding_pen(record, record_id, pretend=pretend)
        else:
            write_message("Inserting into main database", verbose=3)
            error = bibupload(
                record,
                opt_mode = opt_mode,
                opt_notimechange = opt_notimechange,
                oai_rec_id = record_id,
                pretend = pretend,
                tmp_ids = tmp_ids,
                tmp_vers = tmp_vers)
            results.append(error)
            if error[0] == 1:
                if record:
                    write_message(lambda: record_xml_output(record),
                                  stream=sys.stderr)
                else:
                    write_message("Record could not have been parsed",
                                  stream=sys.stderr)
                stat['nb_errors'] += 1
                if callback_url:
                    results_for_callback['results'].append({'recid': error[1], 'success': False, 'error_message': error[2]})
            elif error[0] == 2:
                if record:
                    write_message(lambda: record_xml_output(record),
                                  stream=sys.stderr)
                else:
                    write_message("Record could not have been parsed",
                                  stream=sys.stderr)
                if callback_url:
                    results_for_callback['results'].append({'recid': error[1], 'success': False, 'error_message': error[2]})
            elif error[0] == 0:
                if callback_url:
                    from invenio.search_engine import print_record
                    results_for_callback['results'].append({'recid': error[1], 'success': True, "marcxml": print_record(error[1], 'xm'), 'url': "%s/%s/%s" % (CFG_SITE_URL, CFG_SITE_RECORD, error[1])})
            else:
                if callback_url:
                    results_for_callback['results'].append({'recid': error[1], 'success': False, 'error_message': error[2]})
            # stat us a global variable
            task_update_progress("Done %d out of %d." % \
                                     (stat['nb_records_inserted'] + \
                                          stat['nb_records_updated'],
                                      stat['nb_records_to_upload']))

    # Second phase -> Now we can process all entries where temporary identifiers might appear (BDR, BDM)

    write_message("Identifiers table after processing: %s  versions: %s" % (str(tmp_ids), str(tmp_vers)), verbose=2)
    write_message("Uploading BDR and BDM fields")
    if opt_mode != "holdingpen":
        for record in records:
            record_id = retrieve_rec_id(record, opt_mode, pretend=pretend, post_phase = True)
            bibupload_post_phase(record,
                                 rec_id = record_id,
                                 mode = opt_mode,
                                 pretend = pretend,
                                 tmp_ids = tmp_ids,
                                 tmp_vers = tmp_vers)


    return results

def task_run_core():
    """ Reimplement to add the body of the task."""
    write_message("Input file '%s', input mode '%s'." %
            (task_get_option('file_path'), task_get_option('mode')))
    write_message("STAGE 0:", verbose=2)

    if task_get_option('file_path') is not None:
        write_message("start preocessing", verbose=3)
        task_update_progress("Reading XML input")
        recs = xml_marc_to_records(open_marc_file(task_get_option('file_path')))
        stat['nb_records_to_upload'] = len(recs)
        write_message("   -Open XML marc: DONE", verbose=2)
        task_sleep_now_if_required(can_stop_too=True)
        write_message("Entering records loop", verbose=3)
        callback_url = task_get_option('callback_url')
        results_for_callback = {'results': []}

        if recs is not None:
            # We proceed each record by record
            bibupload_records(records=recs, opt_mode=task_get_option('mode'),
                              opt_notimechange=task_get_option('notimechange'),
                              pretend=task_get_option('pretend'),
                              callback_url=callback_url,
                              results_for_callback=results_for_callback)
        else:
            write_message("   ERROR: bibupload failed: No record found",
                        verbose=1, stream=sys.stderr)
        callback_url = task_get_option("callback_url")
        if callback_url:
            nonce = task_get_option("nonce")
            if nonce:
                results_for_callback["nonce"] = nonce
            post_results_to_callback_url(results_for_callback, callback_url)

    if task_get_task_param('verbose') >= 1:
        # Print out the statistics
        print_out_bibupload_statistics()

    # Check if they were errors
    return not stat['nb_errors'] >= 1

def log_record_uploading(oai_rec_id, task_id, bibrec_id, insertion_db, pretend=False):
    if oai_rec_id != "" and oai_rec_id != None:
        query = """UPDATE oaiHARVESTLOG SET date_inserted=NOW(), inserted_to_db=%s, id_bibrec=%s WHERE oai_id = %s AND bibupload_task_id = %s ORDER BY date_harvested LIMIT 1"""
        if not pretend:
            run_sql(query, (str(insertion_db), str(bibrec_id), str(oai_rec_id), str(task_id), ))

if __name__ == "__main__":
    main()
