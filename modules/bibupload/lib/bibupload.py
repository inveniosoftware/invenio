# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
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
BibUpload: Receive MARC XML file and update the appropriate database
tables according to options.

    Usage: bibupload [options] input.xml
    Examples:
      $ bibupload -i input.xml

    Options:
     -a, --append            new fields are appended to the existing record
     -c, --correct           fields are replaced by the new ones in the
        existing record
     -f, --format            takes only the FMT fields into account.
        Does not update
     -i, --insert            insert the new record in the database
     -r, --replace           the existing record is entirely replaced
        by the new one
     -z, --reference         update references (update only 999 fields)
     -s, --stage=STAGE       stage to start from in the algorithm
        (0: always done; 1: FMT tags;
         2: FFT tags; 3: BibFmt; 4: Metadata update; 5: time update)
     -n, --notimechange      do not change record last modification date
        when updating
     -o, --holdingpen        Makes bibupload insert into holding pen instead
                             the normal database
    Scheduling options:
     -u, --user=USER         user name to store task, password needed

    General options:
     -h, --help              print this help and exit
     -v, --verbose=LEVEL     verbose level (from 0 to 9, default 1)
     -V  --version           print the script version
"""

__revision__ = "$Id$"

import os
import re
import sys
import time
from zlib import compress
import urllib2
import socket
import marshal

from invenio.config import CFG_OAI_ID_FIELD, CFG_SITE_URL, \
     CFG_SITE_SECURE_URL, \
     CFG_BIBUPLOAD_REFERENCE_TAG, \
     CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, \
     CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, \
     CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG, \
     CFG_BIBUPLOAD_STRONG_TAGS, \
     CFG_BIBUPLOAD_CONTROLLED_PROVENANCE_TAGS, \
     CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE

from invenio.bibupload_config import CFG_BIBUPLOAD_CONTROLFIELD_TAGS, \
    CFG_BIBUPLOAD_SPECIAL_TAGS
from invenio.dbquery import run_sql, \
                            Error
from invenio.bibrecord import create_records, \
                              record_add_field, \
                              record_delete_field, \
                              record_xml_output, \
                              record_get_field_instances, \
                              record_get_field_values, \
                              field_get_subfield_values, \
                              record_extract_oai_id
from invenio.search_engine import get_record
from invenio.dateutils import convert_datestruct_to_datetext
from invenio.errorlib import register_exception
from invenio.bibformat import format_record
from invenio.intbitset import intbitset
from invenio.config import CFG_WEBSUBMIT_FILEDIR
from invenio.bibtask import task_init, write_message, \
    task_set_option, task_get_option, task_get_task_param, task_update_status, \
    task_update_progress, task_sleep_now_if_required, fix_argv_paths
from invenio.bibdocfile import BibRecDocs, file_strip_ext, normalize_format, \
    get_docname_from_url, get_format_from_url, check_valid_url, download_url, \
    KEEP_OLD_VALUE, decompose_bibdocfile_url, bibdocfile_url_p, \
    InvenioWebSubmitFileError

#Statistic variables
stat = {}
stat['nb_records_to_upload'] = 0
stat['nb_records_updated'] = 0
stat['nb_records_inserted'] = 0
stat['nb_errors'] = 0
stat['nb_holdingpen'] = 0
stat['exectime'] = time.localtime()

## Let's set a reasonable timeout for URL request (e.g. FFT)
socket.setdefaulttimeout(40)

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
def bibupload(record, opt_tag=None, opt_mode=None,
        opt_stage_to_start_from=1, opt_notimechange=0, oai_rec_id = ""):
    """Main function: process a record and fit it in the tables
    bibfmt, bibrec, bibrec_bibxxx, bibxxx with proper record
    metadata.

    Return (error_code, recID) of the processed record.
    """
    assert(opt_mode in ('insert', 'replace', 'replace_or_insert', 'reference',
        'correct', 'append', 'format', 'holdingpen'))
    error = None
    # If there are special tags to proceed check if it exists in the record
    if opt_tag is not None and not(record.has_key(opt_tag)):
        write_message("    Failed: Tag not found, enter a valid tag to update.",
                    verbose=1, stream=sys.stderr)
        return (1, -1)

    # Extraction of the Record Id from 001, SYSNO or OAIID tags:
    rec_id = retrieve_rec_id(record, opt_mode)
    if rec_id == -1:
        return (1, -1)
    elif rec_id > 0:
        write_message("   -Retrieve record ID (found %s): DONE." % rec_id, verbose=2)
        if not record.has_key('001'):
            # Found record ID by means of SYSNO or OAIID, and the
            # input MARCXML buffer does not have this 001 tag, so we
            # should add it now:
            error = record_add_field(record, '001', '', '', rec_id, [], 0)
            if error is None:
                write_message("   Failed: " \
                                            "Error during adding the 001 controlfield "  \
                                            "to the record", verbose=1, stream=sys.stderr)
                return (1, int(rec_id))
            else:
                error = None
            write_message("   -Added tag 001: DONE.", verbose=2)
    write_message("   -Check if the xml marc file is already in the database: DONE" , verbose=2)

    # Reference mode check if there are reference tag
    if opt_mode == 'reference':
        error = extract_tag_from_record(record, CFG_BIBUPLOAD_REFERENCE_TAG)
        if error is None:
            write_message("   Failed: No reference tags has been found...",
                        verbose=1, stream=sys.stderr)
            return (1, -1)
        else:
            error = None
            write_message("   -Check if reference tags exist: DONE", verbose=2)

    record_deleted_p = False
    if opt_mode == 'insert' or \
    (opt_mode == 'replace_or_insert' and rec_id is None):
        insert_mode_p = True
        # Insert the record into the bibrec databases to have a recordId
        rec_id = create_new_record()
        write_message("   -Creation of a new record id (%d): DONE" % rec_id, verbose=2)

        # we add the record Id control field to the record
        error = record_add_field(record, '001', '', '', rec_id, [], 0)
        if error is None:
            write_message("   Failed: " \
                                        "Error during adding the 001 controlfield "  \
                                        "to the record", verbose=1, stream=sys.stderr)
            return (1, int(rec_id))
        else:
            error = None

    elif opt_mode != 'insert' and opt_mode != 'format' and \
            opt_stage_to_start_from != 5:
        insert_mode_p = False
        # Update Mode
        # Retrieve the old record to update
        rec_old = get_record(rec_id)
        if rec_old is None:
            write_message("   Failed during the creation of the old record!",
                        verbose=1, stream=sys.stderr)
            return (1, int(rec_id))
        else:
            write_message("   -Retrieve the old record to update: DONE", verbose=2)

        # In Replace mode, take over old strong tags if applicable:
        if opt_mode == 'replace' or \
            opt_mode == 'replace_or_insert':
            copy_strong_tags_from_old_record(record, rec_old)

        # Delete tags to correct in the record
        if opt_mode == 'correct' or opt_mode == 'reference':
            delete_tags_to_correct(record, rec_old, opt_tag)
            write_message("   -Delete the old tags to correct in the old record: DONE",
                        verbose=2)

        # Append new tag to the old record and update the new record with the old_record modified
        if opt_mode == 'append' or opt_mode == 'correct' or \
            opt_mode == 'reference':
            record = append_new_tag_to_old_record(record, rec_old,
                opt_tag, opt_mode)
            write_message("   -Append new tags to the old record: DONE", verbose=2)

        # now we clear all the rows from bibrec_bibxxx from the old
        # record (they will be populated later (if needed) during
        # stage 4 below):
        delete_bibrec_bibxxx(rec_old, rec_id)
        record_deleted_p = True
        write_message("   -Clean bibrec_bibxxx: DONE", verbose=2)
    write_message("   -Stage COMPLETED", verbose=2)

    try:
        # Have a look if we have FMT tags
        write_message("Stage 1: Start (Insert of FMT tags if exist).", verbose=2)
        if opt_stage_to_start_from <= 1 and \
            extract_tag_from_record(record, 'FMT') is not None:
            record = insert_fmt_tags(record, rec_id, opt_mode)
            if record is None:
                write_message("   Stage 1 failed: Error while inserting FMT tags",
                            verbose=1, stream=sys.stderr)
                return (1, int(rec_id))
            elif record == 0:
                # Mode format finished
                stat['nb_records_updated'] += 1
                return (0, int(rec_id))
            write_message("   -Stage COMPLETED", verbose=2)
        else:
            write_message("   -Stage NOT NEEDED", verbose=2)

        # Have a look if we have FFT tags
        write_message("Stage 2: Start (Process FFT tags if exist).", verbose=2)
        record_had_FFT = False
        if opt_stage_to_start_from <= 2 and \
            extract_tag_from_record(record, 'FFT') is not None:
            record_had_FFT = True
            if not writing_rights_p():
                write_message("   Stage 2 failed: Error no rights to write fulltext files",
                    verbose=1, stream=sys.stderr)
                task_update_status("ERROR")
                sys.exit(1)
            try:
                record = elaborate_fft_tags(record, rec_id, opt_mode)
            except Exception, e:
                register_exception()
                write_message("   Stage 2 failed: Error while elaborating FFT tags: %s" % e,
                    verbose=1, stream=sys.stderr)
                return (1, int(rec_id))
            if record is None:
                write_message("   Stage 2 failed: Error while elaborating FFT tags",
                            verbose=1, stream=sys.stderr)
                return (1, int(rec_id))
            write_message("   -Stage COMPLETED", verbose=2)
        else:
            write_message("   -Stage NOT NEEDED", verbose=2)

        # Have a look if we have FFT tags
        write_message("Stage 2B: Start (Synchronize 8564 tags).", verbose=2)
        has_bibdocs = run_sql("SELECT count(id_bibdoc) FROM bibrec_bibdoc JOIN bibdoc ON id_bibdoc=id WHERE id_bibrec=%s AND status<>'DELETED'", (rec_id, ))[0][0] > 0
        if opt_stage_to_start_from <= 2 and (has_bibdocs or record_had_FFT or extract_tag_from_record(record, '856') is not None):
            try:
                record = synchronize_8564(rec_id, record, record_had_FFT)
            except Exception, e:
                register_exception(alert_admin=True)
                write_message("   Stage 2B failed: Error while synchronizing 8564 tags: %s" % e,
                    verbose=1, stream=sys.stderr)
                return (1, int(rec_id))
            if record is None:
                write_message("   Stage 2B failed: Error while synchronizing 8564 tags",
                            verbose=1, stream=sys.stderr)
                return (1, int(rec_id))
            write_message("   -Stage COMPLETED", verbose=2)
        else:
            write_message("   -Stage NOT NEEDED", verbose=2)

        # Update of the BibFmt
        write_message("Stage 3: Start (Update bibfmt).", verbose=2)
        if opt_stage_to_start_from <= 3:
            # format the single record as xml
            rec_xml_new = record_xml_output(record)
            # Update bibfmt with the format xm of this record
            if opt_mode != 'format':
                error = update_bibfmt_format(rec_id, rec_xml_new, 'xm')
                if error == 1:
                    write_message("   Failed: error during update_bibfmt_format 'xm'",
                                verbose=1, stream=sys.stderr)
                    return (1, int(rec_id))
                if CFG_BIBUPLOAD_SERIALIZE_RECORD_STRUCTURE:
                    error = update_bibfmt_format(rec_id, marshal.dumps(record), 'recstruct')
                    if error == 1:
                        write_message("   Failed: error during update_bibfmt_format 'recstruct'",
                                    verbose=1, stream=sys.stderr)
                        return (1, int(rec_id))
                # archive MARCXML format of this record for version history purposes:
                error = archive_marcxml_for_history(rec_id)
                if error == 1:
                    write_message("   Failed to archive MARCXML for history",
                                verbose=1, stream=sys.stderr)
                    return (1, int(rec_id))
                else:
                    write_message("   -Archived MARCXML for history : DONE", verbose=2)
            write_message("   -Stage COMPLETED", verbose=2)

        # Update the database MetaData
        write_message("Stage 4: Start (Update the database with the metadata).",
                    verbose=2)
        if opt_stage_to_start_from <= 4:
            if opt_mode == 'insert' or \
            opt_mode == 'replace' or \
            opt_mode == 'replace_or_insert' or \
            opt_mode == 'append' or \
            opt_mode == 'correct' or \
            opt_mode == 'reference':
                update_database_with_metadata(record, rec_id, oai_rec_id)
                record_deleted_p = False
            else:
                write_message("   -Stage NOT NEEDED in mode %s" % opt_mode,
                            verbose=2)
            write_message("   -Stage COMPLETED", verbose=2)
        else:
            write_message("   -Stage NOT NEEDED", verbose=2)

        # Finally we update the bibrec table with the current date
        write_message("Stage 5: Start (Update bibrec table with current date).",
                    verbose=2)
        if opt_stage_to_start_from <= 5 and \
        opt_notimechange == 0 and \
        not insert_mode_p:
            now = convert_datestruct_to_datetext(time.localtime())
            write_message("   -Retrieved current localtime: DONE", verbose=2)
            update_bibrec_modif_date(now, rec_id)
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
        return (0, int(rec_id))
    finally:
        if record_deleted_p:
            ## BibUpload has failed living the record deleted. We should
            ## back the original record then.
            update_database_with_metadata(rec_old, rec_id, oai_rec_id)
            write_message("   Restored original record", verbose=1, stream=sys.stderr)

def insert_record_into_holding_pen(record, oai_id):
    query = "INSERT INTO oaiHOLDINGPEN (oai_id, date_inserted, record_XML) VALUES (%s, NOW(), %s)"
    xml_record = record_xml_output(record)
    run_sql(query, (oai_id, xml_record))
    # record_id is logged as 0! ( We are not inserting into the main database)
    log_record_uploading(oai_id, task_get_task_param('task_id', 0), 0, 'H')
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
        marc_file = open(path,'r')
        marc = marc_file.read()
        marc_file.close()
    except IOError, erro:
        write_message("Error: %s" % erro, verbose=1, stream=sys.stderr)
        write_message("Exiting.", sys.stderr)
        task_update_status("ERROR")
        sys.exit(1)
    return marc

def xml_marc_to_records(xml_marc):
    """create the records"""
    # Creation of the records from the xml Marc in argument
    recs = create_records(xml_marc, 1, 1)
    if recs == []:
        write_message("Error: Cannot parse MARCXML file.", verbose=1, stream=sys.stderr)
        write_message("Exiting.", sys.stderr)
        task_update_status("ERROR")
        sys.exit(1)
    elif recs[0][0] is None:
        write_message("Error: MARCXML file has wrong format: %s" % recs,
            verbose=1, stream=sys.stderr)
        write_message("Exiting.", sys.stderr)
        task_update_status("ERROR")
        sys.exit(1)
    else:
        recs = map((lambda x:x[0]), recs)
        return recs

def find_record_format(rec_id, format):
    """Look whether record REC_ID is formatted in FORMAT,
       i.e. whether FORMAT exists in the bibfmt table for this record.

       Return the number of times it is formatted: 0 if not, 1 if yes,
       2 if found more than once (should never occur).
    """
    out = 0
    query = """SELECT COUNT(id) FROM bibfmt WHERE id_bibrec=%s AND format=%s"""
    params = (rec_id, format)
    res = []
    try:
        res = run_sql(query, params)
        out = res[0][0]
    except Error, error:
        write_message("   Error during find_record_format() : %s " % error, verbose=1, stream=sys.stderr)
    return out

def find_record_from_recid(rec_id):
    """
    Try to find record in the database from the REC_ID number.
    Return record ID if found, None otherwise.
    """
    try:
        res = run_sql("SELECT id FROM bibrec WHERE id=%s",
                      (rec_id,))
    except Error, error:
        write_message("   Error during find_record_bibrec() : %s "
            % error, verbose=1, stream=sys.stderr)
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
    try:
        res = run_sql("""SELECT bb.id_bibrec FROM %(bibrec_bibxxx)s AS bb,
            %(bibxxx)s AS b WHERE b.tag=%%s AND b.value=%%s
            AND bb.id_bibxxx=b.id""" % \
                      {'bibxxx': bibxxx,
                       'bibrec_bibxxx': bibrec_bibxxx},
                      (CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, sysno,))
    except Error, error:
        write_message("   Error during find_record_from_sysno(): %s " % error,
                      verbose=1, stream=sys.stderr)
    if res:
        return res[0][0]
    else:
        return None

def find_records_from_extoaiid(extoaiid, extoaisrc=None):
    """
    Try to find records in the database from the external EXTOAIID number.
    Return list of record ID if found, None otherwise.
    """
    from invenio.search_engine import print_record
    assert(CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[:5] == CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG[:5])
    bibxxx = 'bib'+CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:2]+'x'
    bibrec_bibxxx = 'bibrec_' + bibxxx
    try:
        write_message('   Looking for extoaiid="%s" with extoaisrc="%s"' % (extoaiid, extoaisrc), verbose=9)
        id_bibrecs = intbitset(run_sql("""SELECT bb.id_bibrec FROM %(bibrec_bibxxx)s AS bb,
            %(bibxxx)s AS b WHERE b.tag=%%s AND b.value=%%s
            AND bb.id_bibxxx=b.id""" % \
                      {'bibxxx': bibxxx,
                       'bibrec_bibxxx': bibrec_bibxxx},
                      (CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, extoaiid,)))
        write_message('   Partially found %s for extoaiid="%s"' % (id_bibrecs, extoaiid), verbose=9)
        ret = intbitset()
        for id_bibrec in id_bibrecs:
            record = get_record(id_bibrec)
            instances = record_get_field_instances(record, CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[0:3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[3], CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG[4])
            write_message('   recid %s -> instances "%s"' % (id_bibrec, instances), verbose=9)
            for instance in instances:
                provenance = field_get_subfield_values(instance, CFG_BIBUPLOAD_EXTERNAL_OAIID_PROVENANCE_TAG[5])
                write_message('   recid %s -> provenance "%s"' % (id_bibrec, provenance), verbose=9)
                provenance = provenance and provenance[0] or None
                if provenance is None:
                    if extoaisrc is None:
                        write_message('Found recid %s for extoaiid="%s"' % (id_bibrec, extoaiid), verbose=9)
                        ret.add(id_bibrec)
                        break
                    else:
                        raise Error('Found recid %s for extoaiid="%s" that doesn\'t specify any provenance, while input record does.' % (id_bibrec, extoaiid))
                else:
                    if extoaiid is None:
                        raise Error('Found recid %s for extoaiid="%s" that specify as provenance "%s", while input record does not specify any provenance.' % (id_bibrec, extoaiid, provenance))
                    elif provenance == extoaisrc:
                        write_message('Found recid %s for extoaiid="%s" with provenance="%s"' % (id_bibrec, extoaiid, extoaisrc), verbose=9)
                        ret.add(id_bibrec)
                        break
        return ret
    except Error, error:
        write_message("   Error during find_records_from_extoaiid(): %s "
            % error, verbose=1, stream=sys.stderr)
        raise

def find_record_from_oaiid(oaiid):
    """
    Try to find record in the database from the OAI ID number and OAI SRC.
    Return record ID if found, None otherwise.
    """
    bibxxx = 'bib'+CFG_OAI_ID_FIELD[0:2]+'x'
    bibrec_bibxxx = 'bibrec_' + bibxxx
    try:
        res = run_sql("""SELECT bb.id_bibrec FROM %(bibrec_bibxxx)s AS bb,
            %(bibxxx)s AS b WHERE b.tag=%%s AND b.value=%%s
            AND bb.id_bibxxx=b.id""" % \
                      {'bibxxx': bibxxx,
                       'bibrec_bibxxx': bibrec_bibxxx},
                      (CFG_OAI_ID_FIELD, oaiid,))
    except Error, error:
        write_message("   Error during find_record_from_oaiid(): %s " % error,
                      verbose=1, stream=sys.stderr)
    if res:
        return res[0][0]
    else:
        return None

def extract_tag_from_record(record, tag_number):
    """ Extract the tag_number for record."""
    # first step verify if the record is not already in the database
    if record:
        return record.get(tag_number, None)
    return None

def retrieve_rec_id(record, opt_mode):
    """Retrieve the record Id from a record by using tag 001 or SYSNO or OAI ID
    tag. opt_mod is the desired mode."""

    rec_id = None

    # 1st step: we look for the tag 001
    tag_001 = extract_tag_from_record(record, '001')
    if tag_001 is not None:
        # We extract the record ID from the tag
        rec_id = tag_001[0][3]
        # if we are in insert mode => error
        if opt_mode == 'insert':
            write_message("   Failed : Error tag 001 found in the xml" \
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
            else:
                # The record doesn't exist yet. We shall have try to check
                # the SYSNO or OAI id later.
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
                    try:
                        rec_ids = find_records_from_extoaiid(extoaiid, extoaisrc)
                    except Error, e:
                        write_message(e, verbose=1, stream=sys.stderr)
                        return -1
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

    # Now we should have detected rec_id from SYSNO or OAIID
    # tags.  (None otherwise.)
    if rec_id:
        if opt_mode == 'insert':
            write_message("   Failed : Record found in the database," \
                          " you should use the option replace," \
                          " correct or append to replace an existing" \
                          " record. (-h for help)",
                          verbose=1, stream=sys.stderr)
            return -1
    else:
        if opt_mode != 'insert' and \
           opt_mode != 'replace_or_insert':
            write_message("   Failed : Record not found in the database."\
                          " Please insert the file before updating it."\
                          " (-h for help)", verbose=1, stream=sys.stderr)
            return -1

    return rec_id and int(rec_id) or None

### Insert functions

def create_new_record():
    """Create new record in the database"""
    now = convert_datestruct_to_datetext(time.localtime())
    query = """INSERT INTO bibrec (creation_date, modification_date)
                VALUES (%s, %s)"""
    params = (now, now)
    try:
        rec_id = run_sql(query, params)
        return rec_id
    except Error, error:
        write_message("   Error during the creation_new_record function : %s "
            % error, verbose=1, stream=sys.stderr)
    return None

def insert_bibfmt(id_bibrec, marc, format, modification_date='1970-01-01 00:00:00'):
    """Insert the format in the table bibfmt"""
    # compress the marc value
    pickled_marc =  compress(marc)
    try:
        time.strptime(modification_date, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        modification_date = '1970-01-01 00:00:00'

    query = """INSERT INTO  bibfmt (id_bibrec, format, last_updated, value)
        VALUES (%s, %s, %s, %s)"""
    try:
        row_id  = run_sql(query, (id_bibrec, format, modification_date, pickled_marc))
        return row_id
    except Error, error:
        write_message("   Error during the insert_bibfmt function : %s "
            % error, verbose=1, stream=sys.stderr)
    return None

def insert_record_bibxxx(tag, value):
    """Insert the record into bibxxx"""
    # determine into which table one should insert the record
    table_name = 'bib'+tag[0:2]+'x'

    # check if the tag, value combination exists in the table
    query = """SELECT id,value FROM %s """ % table_name
    query += """ WHERE tag=%s AND value=%s"""
    params = (tag, value)
    try:
        res = run_sql(query, params)
    except Error, error:
        write_message("   Error during the insert_record_bibxxx function : %s "
            % error, verbose=1, stream=sys.stderr)

    # Note: compare now the found values one by one and look for
    # string binary equality (e.g. to respect lowercase/uppercase
    # match), regardless of the charset etc settings.  Ideally we
    # could use a BINARY operator in the above SELECT statement, but
    # we would have to check compatibility on various MySQLdb versions
    # etc; this approach checks all matched values in Python, not in
    # MySQL, which is less cool, but more conservative, so it should
    # work better on most setups.
    for row in res:
        row_id = row[0]
        row_value = row[1]
        if row_value == value:
            return (table_name, row_id)

    # We got here only when the tag,value combination was not found,
    # so it is now necessary to insert the tag,value combination into
    # bibxxx table as new.
    query = """INSERT INTO %s """ % table_name
    query += """ (tag, value) values (%s , %s)"""
    params = (tag, value)
    try:
        row_id = run_sql(query, params)
    except Error, error:
        write_message("   Error during the insert_record_bibxxx function : %s "
            % error, verbose=1, stream=sys.stderr)
    return (table_name, row_id)

def insert_record_bibrec_bibxxx(table_name, id_bibxxx,
        field_number, id_bibrec):
    """Insert the record into bibrec_bibxxx"""
    # determine into which table one should insert the record
    full_table_name = 'bibrec_'+ table_name

    # insert the proper row into the table
    query = """INSERT INTO %s """ % full_table_name
    query += """(id_bibrec,id_bibxxx, field_number) values (%s , %s, %s)"""
    params = (id_bibrec, id_bibxxx, field_number)
    try:
        res = run_sql(query, params)
    except Error, error:
        write_message("   Error during the insert_record_bibrec_bibxxx"
            " function 2nd query : %s " % error, verbose=1, stream=sys.stderr)
    return res

def synchronize_8564(rec_id, record, record_had_FFT):
    """Sinchronize the 8564 tags for record with actual files. descriptions
    should be a dictionary docname:description for the new description to be
    inserted.
    If record_had_FFT the algorithm assume that every fulltext operation
    has been performed through FFT, hence it discard current 8564 local tags,
    and rebuild them after bibdocfile tables. Otherwise it first import
    from 8564 tags the $y and $z subfields corresponding to local files and
    merge them into bibdocfile tables.
    """
    def merge_marc_into_bibdocfile(field):
        """Given the 8564 tag it retrieve the corresponding bibdoc and
        merge the $y and $z subfields."""
        url = field_get_subfield_values(field, 'u')[:1]
        description = field_get_subfield_values(field, 'y')[:1]
        comment = field_get_subfield_values(field, 'z')[:1]
        if url:
            recid, docname, format = decompose_bibdocfile_url(url[0])
            try:
                bibdoc = BibRecDocs(recid).get_bibdoc(docname)
                if description:
                    bibdoc.set_description(description[0], format)
                if comment:
                    bibdoc.set_comment(comment[0], format)
            except InvenioWebSubmitFileError:
                ## Apparently the referenced docname doesn't exist anymore.
                ## Too bad. Let's skip it.
                write_message("WARNING: docname %s doesn't exist for record %s. Has it been renamed outside FFT?" % (docname, recid), stream=sys.stderr)

    write_message("Synchronizing MARC of recid '%s' with:\n%s" % (rec_id, record), verbose=9)
    tags8564s = record_get_field_instances(record, '856', '4', ' ')
    filtered_tags8564s = []

    # Let's discover all the previous internal urls, in order to rebuild them!
    for field in tags8564s:
        to_be_removed = False
        for value in field_get_subfield_values(field, 'u') + field_get_subfield_values(field, 'q'):
            try:
                recid, docname, format = decompose_bibdocfile_url(value)
                if recid == rec_id:
                    if not record_had_FFT:
                        ## If the submission didn't have FFTs, i.e. could be
                        ## not FFTs aware, and it specify 8564s pointing to local
                        ## owned files, then we should import comment and
                        ## description from the 8564s tags.
                        ## Anything else will be discarded.
                        merge_marc_into_bibdocfile(field)
                    to_be_removed = True
            except InvenioWebSubmitFileError:
                ## The URL is not a bibdocfile URL.
                pass
        if not to_be_removed:
            filtered_tags8564s.append(field)

    # Let's keep in the record only external 8564
    record_delete_field(record, '856', '4', ' ') # First we delete 8564
    for field in filtered_tags8564s: # Then we readd external ones
        record_add_field(record, '856', '4', ' ', '', field[0])

    # Now we refresh with existing internal 8564
    bibrecdocs = BibRecDocs(rec_id)
    latest_files = bibrecdocs.list_latest_files()
    for afile in latest_files:
        url = afile.get_url()
        description = afile.get_description()
        comment = afile.get_comment()
        new_subfield = [('u', url)]
        if description:
            new_subfield.append(('y', description))
        if comment:
            new_subfield.append(('z', comment))
        record_add_field(record, '856', '4', ' ', '', new_subfield)

    # Let'handle all the icons
    for bibdoc in bibrecdocs.list_bibdocs():
        icon = bibdoc.get_icon()
        if icon:
            icon = icon.list_all_files()
            if icon:
                url = icon[0].get_url() ## The 1st format found should be ok
                new_subfield = [('q', url)]
                new_subfield.append(('x', 'icon'))
                record_add_field(record, '856', '4', ' ', '', new_subfield)
    return record

def elaborate_fft_tags(record, rec_id, mode):
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
    def _add_new_format(bibdoc, url, format, docname, doctype, newname, description, comment):
        """Adds a new format for a given bibdoc. Returns True when everything's fine."""
        write_message('Add new format to %s url: %s, format: %s, docname: %s, doctype: %s, newname: %s, description: %s, comment: %s' % (repr(bibdoc), url, format, docname, doctype, newname, description, comment), verbose=9)
        try:
            if not url: # Not requesting a new url. Just updating comment & description
                return _update_description_and_comment(bibdoc, docname, format, description, comment)
            tmpurl = download_url(url, format)
            try:
                try:
                    bibdoc.add_file_new_format(tmpurl, description=description, comment=comment)
                except StandardError, e:
                    write_message("('%s', '%s', '%s', '%s', '%s', '%s', '%s') not inserted because format already exists (%s)." % (url, format, docname, doctype, newname, description, comment, e), stream=sys.stderr)
                    raise
            finally:
                os.remove(tmpurl)
        except Exception, e:
            write_message("Error in downloading '%s' because of: %s" % (url, e), stream=sys.stderr)
            raise
        return True

    def _add_new_version(bibdoc, url, format, docname, doctype, newname, description, comment):
        """Adds a new version for a given bibdoc. Returns True when everything's fine."""
        write_message('Add new version to %s url: %s, format: %s, docname: %s, doctype: %s, newname: %s, description: %s, comment: %s' % (repr(bibdoc), url, format, docname, doctype, newname, description, comment))
        try:
            if not url:
                return _update_description_and_comment(bibdoc, docname, format, description, comment)
            tmpurl = download_url(url, format)
            try:
                try:
                    bibdoc.add_file_new_version(tmpurl, description=description, comment=comment)
                except StandardError, e:
                    write_message("('%s', '%s', '%s', '%s', '%s', '%s', '%s') not inserted because '%s'." % (url, format, docname, doctype, newname, description, comment, e), stream=sys.stderr)
                    raise
            finally:
                os.remove(tmpurl)
        except Exception, e:
            write_message("Error in downloading '%s' because of: %s" % (url, e), stream=sys.stderr)
            raise
        return True

    def _update_description_and_comment(bibdoc, docname, format, description, comment):
        """Directly update comments and descriptions."""
        write_message('Just updating description and comment for %s with format %s with description %s and comment %s' % (docname, format, description, comment), verbose=9)
        try:
            bibdoc.set_description(description, format)
            bibdoc.set_comment(comment, format)
        except StandardError, e:
            write_message("('%s', '%s', '%s', '%s') description and comment not updated because '%s'." % (docname, format, description, comment, e))
            raise
        return True

    def _add_new_icon(bibdoc, url, restriction):
        """Adds a new icon to an existing bibdoc, replacing the previous one if it exists. If url is empty, just remove the current icon."""
        if not url:
            bibdoc.delete_icon()
        else:
            try:
                path = urllib2.urlparse.urlsplit(url)[2]
                filename = os.path.split(path)[-1]
                format = filename[len(file_strip_ext(filename)):]
                tmpurl = download_url(url, format)
                try:
                    try:
                        icondoc = bibdoc.add_icon(tmpurl, 'icon-%s' % bibdoc.get_docname())
                        if restriction and restriction != KEEP_OLD_VALUE:
                            icondoc.set_status(restriction)
                    except StandardError, e:
                        write_message("('%s', '%s') icon not added because '%s'." % (url, format, e), stream=sys.stderr)
                        raise
                finally:
                    os.remove(tmpurl)
            except Exception, e:
                write_message("Error in downloading '%s' because of: %s" % (url, e), stream=sys.stderr)
                raise
        return True

    tuple_list = extract_tag_from_record(record, 'FFT')
    if tuple_list: # FFT Tags analysis
        write_message("FFTs: "+str(tuple_list), verbose=9)
        docs = {} # docnames and their data

        for fft in record_get_field_instances(record, 'FFT', ' ', ' '):
            # Let's discover the type of the document
            # This is a legacy field and will not be enforced any particular
            # check on it.
            doctype = field_get_subfield_values(fft, 't')
            if doctype:
                doctype = doctype[0]
            else: # Default is Main
                doctype = 'Main'

            # Let's discover the url.
            url = field_get_subfield_values(fft, 'a')
            if url:
                url = url[0]
                try:
                    check_valid_url(url)
                except StandardError, e:
                    raise StandardError, "fft '%s' specify an url ('%s') with problems: %s" % (fft, url, e)
            else:
                url = ''

            # Let's discover the description
            description = field_get_subfield_values(fft, 'd')
            if description != []:
                description = description[0]
            else:
                if mode == 'correct' and doctype != 'FIX-MARC':
                    ## If the user require to correct, and do not specify
                    ## a description this means she really want to
                    ## modify the description.
                    description = ''
                else:
                    description = KEEP_OLD_VALUE

            # Let's discover the desired docname to be created/altered
            name = field_get_subfield_values(fft, 'n')
            if name:
                name = file_strip_ext(name[0])
            else:
                if url:
                    name = get_docname_from_url(url)
                else:
                    write_message("Warning: fft '%s' doesn't specifies neither a url nor a name" % str(fft), stream=sys.stderr)
                    continue

            # Let's discover the desired new docname in case we want to change it
            newname = field_get_subfield_values(fft, 'm')
            if newname:
                newname = file_strip_ext(newname[0])
            else:
                newname = name

            # Let's discover the desired format
            format = field_get_subfield_values(fft, 'f')
            if format:
                format = format[0]
            else:
                if url:
                    format = get_format_from_url(url)
                else:
                    format = ''

            format = normalize_format(format)

            # Let's discover the icon
            icon = field_get_subfield_values(fft, 'x')
            if icon != []:
                icon = icon[0]
                if icon != KEEP_OLD_VALUE:
                    try:
                        check_valid_url(icon)
                    except StandardError, e:
                        raise StandardError, "fft '%s' specify an icon ('%s') with problems: %s" % (fft, icon, e)
            else:
                if mode == 'correct' and doctype != 'FIX-MARC':
                    ## See comment on description
                    icon = ''
                else:
                    icon = KEEP_OLD_VALUE

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

            version = field_get_subfield_values(fft, 'v')
            if version:
                version = version[0]
            else:
                version = ''

            if docs.has_key(name): # new format considered
                (doctype2, newname2, restriction2, icon2, version2, urls) = docs[name]
                if doctype2 != doctype:
                    raise StandardError, "fft '%s' specifies a different doctype from previous fft with docname '%s'" % (str(fft), name)
                if newname2 != newname:
                    raise StandardError, "fft '%s' specifies a different newname from previous fft with docname '%s'" % (str(fft), name)
                if restriction2 != restriction:
                    raise StandardError, "fft '%s' specifies a different restriction from previous fft with docname '%s'" % (str(fft), name)
                if icon2 != icon:
                    raise StandardError, "fft '%x' specifies a different icon than the previous fft with docname '%s'" % (str(fft), name)
                if version2 != version:
                    raise StandardError, "fft '%x' specifies a different version than the previous fft with docname '%s'" % (str(fft), name)
                for (url2, format2, description2, comment2) in urls:
                    if format == format2:
                        raise StandardError, "fft '%s' specifies a second file '%s' with the same format '%s' from previous fft with docname '%s'" % (str(fft), url, format, name)
                if url or format:
                    urls.append((url, format, description, comment))
            else:
                if url or format:
                    docs[name] = (doctype, newname, restriction, icon, version, [(url, format, description, comment)])
                else:
                    docs[name] = (doctype, newname, restriction, icon, version, [])

        write_message('Result of FFT analysis:\n\tDocs: %s' % (docs,), verbose=9)

        # Let's remove all FFT tags
        record_delete_field(record, 'FFT', ' ', ' ')

        # Preprocessed data elaboration
        bibrecdocs = BibRecDocs(rec_id)

        if mode == 'replace': # First we erase previous bibdocs
            for bibdoc in bibrecdocs.list_bibdocs():
                bibdoc.delete()
            bibrecdocs.build_bibdoc_list()

        for docname, (doctype, newname, restriction, icon, version, urls) in docs.iteritems():
            write_message("Elaborating olddocname: '%s', newdocname: '%s', doctype: '%s', restriction: '%s', icon: '%s', urls: '%s', mode: '%s'" % (docname, newname, doctype, restriction, icon, urls, mode), verbose=9)
            if mode in ('insert', 'replace'): # new bibdocs, new docnames, new marc
                if newname in bibrecdocs.get_bibdoc_names():
                    write_message("('%s', '%s') not inserted because docname already exists." % (newname, urls), stream=sys.stderr)
                    raise StandardError
                try:
                    bibdoc = bibrecdocs.add_bibdoc(doctype, newname)
                    bibdoc.set_status(restriction)
                except Exception, e:
                    write_message("('%s', '%s', '%s') not inserted because: '%s'." % (doctype, newname, urls, e), stream=sys.stderr)
                    raise StandardError
                for (url, format, description, comment) in urls:
                    assert(_add_new_format(bibdoc, url, format, docname, doctype, newname, description, comment))
                if icon and not icon == KEEP_OLD_VALUE:
                    assert(_add_new_icon(bibdoc, icon, restriction))
            elif mode == 'replace_or_insert': # to be thought as correct_or_insert
                for bibdoc in bibrecdocs.list_bibdocs():
                    if bibdoc.get_docname() == docname:
                        if doctype not in ('PURGE', 'DELETE', 'EXPUNGE', 'REVERT', 'FIX-ALL', 'FIX-MARC', 'DELETE-FILE'):
                            if newname != docname:
                                try:
                                    bibdoc.change_name(newname)
                                    icon = bibdoc.get_icon()
                                    if icon:
                                        icon.change_name('icon-%s' % newname)
                                except StandardError, e:
                                    write_message(e, stream=sys.stderr)
                                    raise
                found_bibdoc = False
                for bibdoc in bibrecdocs.list_bibdocs():
                    if bibdoc.get_docname() == newname:
                        found_bibdoc = True
                        if doctype == 'PURGE':
                            bibdoc.purge()
                        elif doctype == 'DELETE':
                            bibdoc.delete()
                        elif doctype == 'EXPUNGE':
                            bibdoc.expunge()
                        elif doctype == 'FIX-ALL':
                            bibrecdocs.fix(docname)
                        elif doctype == 'FIX-MARC':
                            pass
                        elif doctype == 'DELETE-FILE':
                            if urls:
                                for (url, format, description, comment) in urls:
                                    bibdoc.delete_file(format, version)
                        elif doctype == 'REVERT':
                            try:
                                bibdoc.revert(version)
                            except Exception, e:
                                write_message('(%s, %s) not correctly reverted: %s' % (newname, version, e), stream=sys.stderr)
                                raise
                        else:
                            if restriction != KEEP_OLD_VALUE:
                                bibdoc.set_status(restriction)
                            # Since the docname already existed we have to first
                            # bump the version by pushing the first new file
                            # then pushing the other files.
                            if urls:
                                (first_url, first_format, first_description, first_comment) = urls[0]
                                other_urls = urls[1:]
                                assert(_add_new_version(bibdoc, first_url, first_format, docname, doctype, newname, first_description, first_comment))
                                for (url, format, description, comment) in other_urls:
                                    assert(_add_new_format(bibdoc, url, format, docname, doctype, newname, description, comment))
                        if icon != KEEP_OLD_VALUE:
                            assert(_add_new_icon(bibdoc, icon, restriction))
                if not found_bibdoc:
                    bibdoc = bibrecdocs.add_bibdoc(doctype, newname)
                    for (url, format, description, comment) in urls:
                        assert(_add_new_format(bibdoc, url, format, docname, doctype, newname, description, comment))
                    if icon and not icon == KEEP_OLD_VALUE:
                        assert(_add_new_icon(bibdoc, icon, restriction))
            elif mode == 'correct':
                for bibdoc in bibrecdocs.list_bibdocs():
                    if bibdoc.get_docname() == docname:
                        if doctype not in ('PURGE', 'DELETE', 'EXPUNGE', 'REVERT', 'FIX-ALL', 'FIX-MARC', 'DELETE-FILE'):
                            if newname != docname:
                                try:
                                    bibdoc.change_name(newname)
                                    icon = bibdoc.get_icon()
                                    if icon:
                                        icon.change_name('icon-%s' % newname)
                                except StandardError, e:
                                    write_message('Error in renaming %s to %s: %s' % (docname, newname, e), stream=sys.stderr)
                                    raise
                found_bibdoc = False
                for bibdoc in bibrecdocs.list_bibdocs():
                    if bibdoc.get_docname() == newname:
                        found_bibdoc = True
                        if doctype == 'PURGE':
                            bibdoc.purge()
                        elif doctype == 'DELETE':
                            bibdoc.delete()
                        elif doctype == 'EXPUNGE':
                            bibdoc.expunge()
                        elif doctype == 'FIX-ALL':
                            bibrecdocs.fix(newname)
                        elif doctype == 'FIX-MARC':
                            pass
                        elif doctype == 'DELETE-FILE':
                            if urls:
                                for (url, format, description, comment) in urls:
                                    bibdoc.delete_file(format, version)
                        elif doctype == 'REVERT':
                            try:
                                bibdoc.revert(version)
                            except Exception, e:
                                write_message('(%s, %s) not correctly reverted: %s' % (newname, version, e), stream=sys.stderr)
                                raise
                        else:
                            if restriction != KEEP_OLD_VALUE:
                                bibdoc.set_status(restriction)
                            if urls:
                                (first_url, first_format, first_description, first_comment) = urls[0]
                                other_urls = urls[1:]
                                assert(_add_new_version(bibdoc, first_url, first_format, docname, doctype, newname, first_description, first_comment))
                                for (url, format, description, comment) in other_urls:
                                    assert(_add_new_format(bibdoc, url, format, docname, description, doctype, newname, description, comment))
                        if icon != KEEP_OLD_VALUE:
                            _add_new_icon(bibdoc, icon, restriction)
                if not found_bibdoc:
                    write_message("('%s', '%s', '%s') not added because '%s' docname didn't existed." % (doctype, newname, urls, docname), stream=sys.stderr)
                    raise StandardError
            elif mode == 'append':
                try:
                    found_bibdoc = False
                    for bibdoc in bibrecdocs.list_bibdocs():
                        if bibdoc.get_docname() == docname:
                            found_bibdoc = True
                            for (url, format, description, comment) in urls:
                                assert(_add_new_format(bibdoc, url, format, docname, doctype, newname, description, comment))
                            if icon not in ('', KEEP_OLD_VALUE):
                                assert(_add_new_icon(bibdoc, icon, restriction))
                    if not found_bibdoc:
                        try:
                            bibdoc = bibrecdocs.add_bibdoc(doctype, docname)
                            bibdoc.set_status(restriction)
                            for (url, format, description, comment) in urls:
                                assert(_add_new_format(bibdoc, url, format, docname, doctype, newname, description, comment))
                            if icon and not icon == KEEP_OLD_VALUE:
                                assert(_add_new_icon(bibdoc, icon, restriction))
                        except Exception, e:
                            register_exception()
                            write_message("('%s', '%s', '%s') not appended because: '%s'." % (doctype, newname, urls, e), stream=sys.stderr)
                            raise
                except:
                    register_exception()
                    raise
    return record

def insert_fmt_tags(record, rec_id, opt_mode):
    """Process and insert FMT tags"""

    fmt_fields = record_get_field_instances(record, 'FMT')
    if fmt_fields:
        for fmt_field in fmt_fields:
            # Get the d, f, g subfields of the FMT tag
            try:
                d_value = field_get_subfield_values(fmt_field, "d")[0]
            except IndexError:
                d_value = ""
            try:
                f_value = field_get_subfield_values(fmt_field, "f")[0]
            except IndexError:
                f_value = ""
            try:
                g_value = field_get_subfield_values(fmt_field, "g")[0]
            except IndexError:
                g_value = ""
            # Update the format
            res = update_bibfmt_format(rec_id, g_value, f_value, d_value)
            if res == 1:
                write_message("   Failed: Error during update_bibfmt", verbose=1, stream=sys.stderr)

        # If we are in format mode, we only care about the FMT tag
        if opt_mode == 'format':
            return 0
        # We delete the FMT Tag of the record
        record_delete_field(record, 'FMT')
        write_message("   -Delete field FMT from record : DONE", verbose=2)
        return record

    elif opt_mode == 'format':
        write_message("   Failed: Format updated failed : No tag FMT found", verbose=1, stream=sys.stderr)
        return None
    else:
        return record


### Update functions

def update_bibrec_modif_date(now, bibrec_id):
    """Update the date of the record in bibrec table """
    query = """UPDATE bibrec SET modification_date=%s WHERE id=%s"""
    params = (now, bibrec_id)
    try:
        run_sql(query, params)
        write_message("   -Update record modification date : DONE" , verbose=2)
    except Error, error:
        write_message("   Error during update_bibrec_modif_date function : %s" % error,
                      verbose=1, stream=sys.stderr)

def update_bibfmt_format(id_bibrec, format_value, format_name, modification_date=None):
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
        query = """UPDATE bibfmt SET last_updated=%s, value=%s WHERE id_bibrec=%s AND format=%s"""
        params = (modification_date, pickled_format_value, id_bibrec, format_name)
        try:
            row_id  = run_sql(query, params)
            if row_id is None:
                write_message("   Failed: Error during update_bibfmt_format function", verbose=1, stream=sys.stderr)
                return 1
            else:
                write_message("   -Update the format %s in bibfmt : DONE" % format_name , verbose=2)
                return 0
        except Error, error:
            write_message("   Error during the update_bibfmt_format function : %s " % error, verbose=1, stream=sys.stderr)

    elif nb_found > 1:
        write_message("   Failed: Same format %s found several time in bibfmt for the same record." % format_name, verbose=1, stream=sys.stderr)
        return 1
    else:
        # Insert the format information in BibFMT
        res = insert_bibfmt(id_bibrec, format_value, format_name, modification_date)
        if res is None:
            write_message("   Failed: Error during insert_bibfmt", verbose=1, stream=sys.stderr)
            return 1
        else:
            write_message("   -Insert the format %s in bibfmt : DONE" % format_name , verbose=2)
            return 0

def archive_marcxml_for_history(recID):
    """
    Archive current MARCXML format of record RECID from BIBFMT table
    into hstRECORD table.  Useful to keep MARCXML history of records.

    Return 0 if everything went fine.  Return 1 otherwise.
    """
    try:
        res = run_sql("SELECT id_bibrec, value, last_updated FROM bibfmt WHERE format='xm' AND id_bibrec=%s",
                      (recID,))
        if res:
            run_sql("""INSERT INTO hstRECORD (id_bibrec, marcxml, job_id, job_name, job_person, job_date, job_details)
                                      VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    (res[0][0], res[0][1], task_get_task_param('task_id', 0), 'bibupload', task_get_task_param('user','UNKNOWN'), res[0][2],
                     'mode: ' + task_get_option('mode','UNKNOWN') + '; file: ' + task_get_option('file_path','UNKNOWN') + '.'))
    except Error, error:
        write_message("   Error during archive_marcxml_for_history: %s " % error,
                      verbose=1, stream=sys.stderr)
        return 1
    return 0

def update_database_with_metadata(record, rec_id, oai_rec_id = "oai"):
    """Update the database tables with the record and the record id given in parameter"""
    for tag in record.keys():
        # check if tag is not a special one:
        if tag not in CFG_BIBUPLOAD_SPECIAL_TAGS:
            # for each tag there is a list of tuples representing datafields
            tuple_list = record[tag]
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
                    # nothing to do for special tags (FFT, FMT)
                    pass
                elif tag in CFG_BIBUPLOAD_CONTROLFIELD_TAGS and tag != "001":
                    value = single_tuple[3]
                    # get the full tag
                    full_tag = ''.join(tag_list)

                    # update the tables
                    write_message("   insertion of the tag "+full_tag+" with the value "+value, verbose=9)
                    # insert the tag and value into into bibxxx
                    (table_name, bibxxx_row_id) = insert_record_bibxxx(full_tag, value)
                    #print 'tname, bibrow', table_name, bibxxx_row_id;
                    if table_name is None or bibxxx_row_id is None:
                        write_message("   Failed : during insert_record_bibxxx", verbose=1, stream=sys.stderr)
                    # connect bibxxx and bibrec with the table bibrec_bibxxx
                    res = insert_record_bibrec_bibxxx(table_name, bibxxx_row_id, datafield_number, rec_id)
                    if res is None:
                        write_message("   Failed : during insert_record_bibrec_bibxxx", verbose=1, stream=sys.stderr)
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
                        (table_name, bibxxx_row_id) = insert_record_bibxxx(full_tag, value)
                        if table_name is None or bibxxx_row_id is None:
                            write_message("   Failed : during insert_record_bibxxx", verbose=1, stream=sys.stderr)
                        # connect bibxxx and bibrec with the table bibrec_bibxxx
                        res = insert_record_bibrec_bibxxx(table_name, bibxxx_row_id, datafield_number, rec_id)
                        if res is None:
                            write_message("   Failed : during insert_record_bibrec_bibxxx", verbose=1, stream=sys.stderr)
                        # remove the subtag from the list
                        tag_list.pop()
                tag_list.pop()
                tag_list.pop()
            tag_list.pop()
    write_message("   -Update the database with metadata : DONE", verbose=2)

    log_record_uploading(oai_rec_id, task_get_task_param('task_id', 0), rec_id, 'P')

def append_new_tag_to_old_record(record, rec_old, opt_tag, opt_mode):
    """Append new tags to a old record"""
    if opt_tag is not None:
        tag = opt_tag
        if tag in CFG_BIBUPLOAD_CONTROLFIELD_TAGS:
            if tag == '001':
                pass
            else:
                # if it is a controlfield,just access the value
                for single_tuple in record[tag]:
                    controlfield_value = single_tuple[3]
                    # add the field to the old record
                    newfield_number = record_add_field(rec_old, tag, "", "", controlfield_value)
                    if newfield_number is None:
                        write_message("   Error when adding the field"+tag, verbose=1, stream=sys.stderr)
        else:
            # For each tag there is a list of tuples representing datafields
            for single_tuple in record[tag]:
                # We retrieve the information of the tag
                subfield_list = single_tuple[0]
                ind1 = single_tuple[1]
                ind2 = single_tuple[2]
                # We add the datafield to the old record
                write_message("      Adding tag: %s ind1=%s ind2=%s code=%s" % (tag, ind1, ind2, subfield_list), verbose=9)
                newfield_number = record_add_field(rec_old, tag, ind1, ind2, "", subfield_list)
                if newfield_number is None:
                    write_message("Error when adding the field"+tag, verbose=1, stream=sys.stderr)
    else:
        # Go through each tag in the appended record
        for tag in record.keys():
            # Reference mode append only reference tag
            if opt_mode == 'reference':
                if tag == CFG_BIBUPLOAD_REFERENCE_TAG:
                    for single_tuple in record[tag]:
                        # We retrieve the information of the tag
                        subfield_list = single_tuple[0]
                        ind1 = single_tuple[1]
                        ind2 = single_tuple[2]
                        # We add the datafield to the old record
                        write_message("      Adding tag: %s ind1=%s ind2=%s code=%s" % (tag, ind1, ind2, subfield_list), verbose=9)
                        newfield_number = record_add_field(rec_old, tag, ind1, ind2, "", subfield_list)
                        if newfield_number is None:
                            write_message("   Error when adding the field"+tag, verbose=1, stream=sys.stderr)
            else:
                if tag in CFG_BIBUPLOAD_CONTROLFIELD_TAGS:
                    if tag == '001':
                        pass
                    else:
                        # if it is a controlfield,just access the value
                        for single_tuple in record[tag]:
                            controlfield_value = single_tuple[3]
                            # add the field to the old record
                            newfield_number = record_add_field(rec_old, tag, "", "", controlfield_value)
                            if newfield_number is None:
                                write_message("   Error when adding the field"+tag, verbose=1, stream=sys.stderr)
                else:
                    # For each tag there is a list of tuples representing datafields
                    for single_tuple in record[tag]:
                        # We retrieve the information of the tag
                        subfield_list = single_tuple[0]
                        ind1 = single_tuple[1]
                        ind2 = single_tuple[2]
                        # We add the datafield to the old record
                        write_message("      Adding tag: %s ind1=%s ind2=%s code=%s" % (tag, ind1, ind2, subfield_list), verbose=9)
                        newfield_number = record_add_field(rec_old, tag, ind1, ind2, "", subfield_list)
                        if newfield_number is None:
                            write_message("   Error when adding the field"+tag, verbose=1, stream=sys.stderr)
    return rec_old

def copy_strong_tags_from_old_record(record, rec_old):
    """
    Look for strong tags in RECORD and REC_OLD.  If no strong tags are
    found in RECORD, then copy them over from REC_OLD.  This function
    modifies RECORD structure on the spot.
    """
    for strong_tag in CFG_BIBUPLOAD_STRONG_TAGS:
        if not record_get_field_instances(record, strong_tag):
            strong_tag_old_field_instances = record_get_field_instances(rec_old, strong_tag)
            if strong_tag_old_field_instances:
                for strong_tag_old_field_instance in strong_tag_old_field_instances:
                    sf_vals, fi_ind1, fi_ind2, controlfield, dummy = strong_tag_old_field_instance
                    record_add_field(record, strong_tag, fi_ind1, fi_ind2, controlfield, sf_vals)
    return

### Delete functions

def delete_tags_to_correct(record, rec_old, opt_tag):
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
        # do we have to delete only a special tag or any tag?
        if opt_tag is None or opt_tag == tag:
            # check if the tag exists in the old record too:
            if tag in rec_old and tag != '001':
                # the tag does exist, so delete all record's tag+ind1+ind2 combinations from rec_old
                for dummy_sf_vals, ind1, ind2, dummy_cf, field_number in record[tag]:
                    write_message("      Delete tag: " + tag + " ind1=" + ind1 + " ind2=" + ind2, verbose=9)
                    record_delete_field(rec_old, tag, ind1, ind2)

    ## Ok, we readd necessary fields!
    for tag, fields in fields_to_readd.iteritems():
        for sf_vals in fields:
            write_message("      Adding tag: " + tag[:3] + " ind1=" + tag[3] + " ind2=" + tag[4] + " code=" + str(sf_vals), verbose=9)
            record_add_field(rec_old, tag[:3], tag[3], tag[4], datafield_subfield_code_value_tuples=sf_vals)

def delete_bibrec_bibxxx(record, id_bibrec):
    """Delete the database record from the table bibxxx given in parameters"""
    # we clear all the rows from bibrec_bibxxx from the old record
    for tag in record.keys():
        if tag not in CFG_BIBUPLOAD_SPECIAL_TAGS:
            # for each name construct the bibrec_bibxxx table name
            table_name = 'bibrec_bib'+tag[0:2]+'x'
            # delete all the records with proper id_bibrec
            query = """DELETE FROM `%s` where id_bibrec = %s"""
            params = (table_name, id_bibrec)
            try:
                run_sql(query % params)
            except Error, error:
                write_message("   Error during the delete_bibrec_bibxxx function : %s " % error, verbose=1, stream=sys.stderr)

def wipe_out_record_from_all_tables(recid):
    """
    Wipe out completely the record and all its traces of RECID from
    the database (bibrec, bibrec_bibxxx, bibxxx, bibfmt).  Useful for
    the time being for test cases.
    """
    # delete all the linked bibdocs
    for bibdoc in BibRecDocs(recid).list_bibdocs():
        bibdoc.expunge()
    # delete from bibrec:
    run_sql("DELETE FROM bibrec WHERE id=%s", (recid,))
    # delete from bibrec_bibxxx:
    for i in range(0, 10):
        for j in range(0, 10):
            run_sql("DELETE FROM %(bibrec_bibxxx)s WHERE id_bibrec=%%s" % \
                    {'bibrec_bibxxx': "bibrec_bib%i%ix" % (i, j)},
                    (recid,))
    # delete all unused bibxxx values:
    for i in range(0, 10):
        for j in range(0, 10):
            run_sql("DELETE %(bibxxx)s FROM %(bibxxx)s " \
                    " LEFT JOIN %(bibrec_bibxxx)s " \
                    " ON %(bibxxx)s.id=%(bibrec_bibxxx)s.id_bibxxx " \
                    " WHERE %(bibrec_bibxxx)s.id_bibrec IS NULL" % \
                    {'bibxxx': "bib%i%ix" % (i, j),
                     'bibrec_bibxxx': "bibrec_bib%i%ix" % (i, j)})
    # delete from bibfmt:
    run_sql("DELETE FROM bibfmt WHERE id_bibrec=%s", (recid,))
    # delete from bibrec_bibdoc:
    run_sql("DELETE FROM bibrec_bibdoc WHERE id_bibrec=%s", (recid,))
    return

def delete_bibdoc(id_bibrec):
    """Delete document from bibdoc which correspond to the bibrec id given in parameter"""
    query = """UPDATE bibdoc SET status='DELETED'
                WHERE id IN (SELECT id_bibdoc FROM bibrec_bibdoc
                              WHERE id_bibrec=%s)"""
    params = (id_bibrec,)
    try:
        run_sql(query, params)
    except Error, error:
        write_message("   Error during the delete_bibdoc function : %s " % error,
                      verbose=1, stream=sys.stderr)

def delete_bibrec_bibdoc(id_bibrec):
    """Delete the bibrec record from the table bibrec_bibdoc given in parameter"""
    # delete all the records with proper id_bibrec
    query = """DELETE FROM bibrec_bibdoc WHERE id_bibrec=%s"""
    params = (id_bibrec,)
    try:
        run_sql(query, params)
    except Error, error:
        write_message("   Error during the delete_bibrec_bibdoc function : %s " % error,
                      verbose=1, stream=sys.stderr)
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
  -c, --correct\t\tfields are replaced by the new ones in the existing record
  -f, --format\t\ttakes only the FMT fields into account. Does not update
  -i, --insert\t\tinsert the new record in the database
  -r, --replace\t\tthe existing record is entirely replaced by the new one
  -z, --reference\tupdate references (update only 999 fields)
  -S, --stage=STAGE\tstage to start from in the algorithm (0: always done; 1: FMT tags;
\t\t\t2: FFT tags; 3: BibFmt; 4: Metadata update; 5: time update)
  -n, --notimechange\tdo not change record last modification date when updating
  -o, --holdingpen\t\tInsert record into holding pen instead of the normal database
""",
            version=__revision__,
            specific_params=("ircazS:fno",
                 [
                   "insert",
                   "replace",
                   "correct",
                   "append",
                   "reference",
                   "stage=",
                   "format",
                   "notimechange",
                   "holdingpen",
                 ]),
            task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
            task_run_fnc=task_run_core)

def task_submit_elaborate_specific_parameter(key, value, opts, args):
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
        task_set_option('file_path', os.path.realpath(args[0]))

    # Replace mode option
    elif key in ("-r", "--replace"):
        if task_get_option('mode') == 'insert':
            # if also insert found, then set to replace_or_insert
            task_set_option('mode', 'replace_or_insert')
        else:
            task_set_option('mode', 'replace')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.realpath(args[0]))
    # Holding pen mode option
    elif key in ("-o", "--holdingpen"):
        write_message("Holding pen mode", verbose=3)
        task_set_option('mode', 'holdingpen')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.realpath(args[0]))
    # Correct mode option
    elif key in ("-c", "--correct"):
        task_set_option('mode', 'correct')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.realpath(args[0]))

    # Append mode option
    elif key in ("-a", "--append"):
        task_set_option('mode', 'append')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.realpath(args[0]))

    # Reference mode option
    elif key in ("-z", "--reference"):
        task_set_option('mode', 'reference')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.realpath(args[0]))

    # Format mode option
    elif key in ("-f", "--format"):
        task_set_option('mode', 'format')
        fix_argv_paths([args[0]])
        task_set_option('file_path', os.path.realpath(args[0]))

    # Stage
    elif key in ("-S", "--stage"):
        try:
            value = int(value)
        except ValueError:
            print >> sys.stderr, """The value specified for --stage must be a valid integer, not %s""" % value
            return False
        if not (0 <= value <= 5):
            print >> sys.stderr, """The value specified for --stage must be comprised between 0 and 5"""
            return False
        task_set_option('stage_to_start_from', value)
    else:
        return False
    return True


def task_submit_check_options():
    """ Reimplement this method for having the possibility to check options
    before submitting the task, in order for example to provide default
    values. It must return False if there are errors in the options.
    """
    if task_get_option('mode') is None:
        write_message("Please specify at least one update/insert mode!")
        return False

    if task_get_option('file_path') is None:
        write_message("Missing filename! -h for help.")
        return False
    return True

def writing_rights_p():
    """Return True in case bibupload has the proper rights to write in the
    fulltext file folder."""
    filename = os.path.join(CFG_WEBSUBMIT_FILEDIR, 'test.txt')
    try:
        if not os.path.exists(CFG_WEBSUBMIT_FILEDIR):
            os.makedirs(CFG_WEBSUBMIT_FILEDIR)
        open(filename, 'w').write('TEST')
        assert(open(filename).read() == 'TEST')
        os.remove(filename)
    except:
        register_exception()
        return False
    return True

def task_run_core():
    """ Reimplement to add the body of the task."""
    error = 0
    write_message("Input file '%s', input mode '%s'." %
            (task_get_option('file_path'), task_get_option('mode')))
    write_message("STAGE 0:", verbose=2)

    if task_get_option('file_path') is not None:
        write_message("start preocessing", verbose=3)
        task_update_status("Reading XML input")
        recs = xml_marc_to_records(open_marc_file(task_get_option('file_path')))
        stat['nb_records_to_upload'] = len(recs)
        write_message("   -Open XML marc: DONE", verbose=2)
        task_sleep_now_if_required(can_stop_too=True)
        write_message("Entering records loop", verbose=3)
        if recs is not None:
            # We proceed each record by record
            for record in recs:
                record_id = record_extract_oai_id(record)
                task_sleep_now_if_required(can_stop_too=True)
                if task_get_option("mode") == "holdingpen":
                    #inserting into the holding pen
                    write_message("Inserting into holding pen", verbose=3)
                    insert_record_into_holding_pen(record, record_id)
                else:
                    write_message("Inserting into main database", verbose=3)
                    error = bibupload(
                        record,
                        opt_tag=task_get_option('tag'),
                        opt_mode=task_get_option('mode'),
                        opt_stage_to_start_from=task_get_option('stage_to_start_from'),
                        opt_notimechange=task_get_option('notimechange'),
                        oai_rec_id = record_id)
                    if error[0] == 1:
                        if record:
                            write_message(record_xml_output(record),
                                          stream=sys.stderr)
                        else:
                            write_message("Record could not have been parsed",
                                          stream=sys.stderr)
                        stat['nb_errors'] += 1
                    elif error[0] == 2:
                        if record:
                            write_message(record_xml_output(record),
                                          stream=sys.stderr)
                        else:
                            write_message("Record could not have been parsed",
                                          stream=sys.stderr)

                task_update_progress("Done %d out of %d." % \
                    (stat['nb_records_inserted'] + \
                    stat['nb_records_updated'],
                    stat['nb_records_to_upload']))
        else:
            write_message("   Error bibupload failed: No record found",
                        verbose=1, stream=sys.stderr)

    if task_get_task_param('verbose') >= 1:
        # Print out the statistics
        print_out_bibupload_statistics()

    # Check if they were errors
    return not stat['nb_errors'] >= 1

def log_record_uploading(oai_rec_id, task_id, bibrec_id, insertion_db):
    if oai_rec_id != "" and oai_rec_id != None:
        query = """UPDATE oaiHARVESTLOG SET date_inserted=NOW(), inserted_to_db=%s, id_bibrec=%s WHERE oai_id = %s AND bibupload_task_id = %s ORDER BY date_harvested LIMIT 1"""
        try:
            run_sql(query, (str(insertion_db), str(bibrec_id), str(oai_rec_id), str(task_id), ))
        except Error, error:
            write_message("   Error during the log_record_uploading function : %s "
                          % error, verbose=1, stream=sys.stderr)
if __name__ == "__main__":
    main()
