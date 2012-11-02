# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013 CERN.
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

__revision__ = "$Id$"

import re
import time
import os
import sys
import ConfigParser
from datetime import datetime
from itertools import islice

from invenio.dbquery import run_sql, \
                            deserialize_via_marshal
from invenio.bibindex_tokenizers.BibIndexJournalTokenizer import \
    CFG_JOURNAL_PUBINFO_STANDARD_FORM, \
    CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK
from invenio.search_engine import search_pattern, search_unit
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibformat_utils import parse_tag
from invenio.bibknowledge import get_kb_mappings
from invenio.bibtask import write_message, task_get_option, \
                     task_update_progress, task_sleep_now_if_required, \
                     task_get_task_param
from invenio.bibindex_engine_utils import get_field_tags
from invenio.docextract_record import get_record

INTBITSET_OF_DELETED_RECORDS = search_unit(p='DELETED', f='980', m='a')

re_CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK = re.compile(CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK)


def compute_weights():
    sql = "SELECT citee, COUNT(citer) FROM rnkCITATIONDICT GROUP BY citee"
    weights = {}
    for citee, c in run_sql(sql):
        weights[citee] = c
    return weights


def get_recids_matching_query(p, f, m='e'):
    """Return set of recIDs matching query for pattern p in field f."""
    return search_pattern(p=p, f=f, m=m) - INTBITSET_OF_DELETED_RECORDS


def get_citation_weight(rank_method_code, config, chunk_size=9000):
    """return a dictionary which is used by bibrank daemon for generating
    the index of sorted research results by citation information
    """
    quick = task_get_option("quick") != "no"

    # id option forces re-indexing a certain range
    # even if there are no new recs
    if task_get_option("id"):
        # construct a range of records to index
        updated_recids = []
        for first, last in task_get_option("id"):
            updated_recids += range(first, last+1)
        if len(updated_recids) > 10000:
            str_updated_recids = str(updated_recids[:10]) + ' ... ' + str(updated_recids[-10:])
        else:
            str_updated_recids = str(updated_recids)
        write_message('Records to process: %s' % str_updated_recids)
        index_update_time = None
    else:
        bibrank_update_time = get_bibrankmethod_lastupdate(rank_method_code)
        if not quick:
            bibrank_update_time = "0000-00-00 00:00:00"
        write_message("bibrank: %s" % bibrank_update_time)
        index_update_time = get_bibindex_update_time()
        write_message("bibindex: %s" % index_update_time)
        if index_update_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
            index_update_time = "0000-00-00 00:00:00"
        updated_recids = get_modified_recs(bibrank_update_time,
                                           index_update_time)
        if len(updated_recids) > 10000:
            str_updated_recids = str(updated_recids[:10]) + ' ... ' + str(updated_recids[-10:])
        else:
            str_updated_recids = str(updated_recids)
        write_message("%s records to update" % str_updated_recids)

    if updated_recids:
        begin_time = time.time()
        # Process fully the updated records
        weights = process_and_store(updated_recids, config, chunk_size)
        end_time = time.time()
        write_message("Total time of get_citation_weight(): %.2f sec" % \
                                                      (end_time - begin_time))
        task_update_progress("citation analysis done")
    else:
        weights = None
        write_message("No new records added since last time this " \
                      "rank method was executed")

    return weights, index_update_time


def process_and_store(recids, config, chunk_size):
    # If we have nothing to process
    # Do not update the weights dictionary
    modified = False
    # Process recent records first
    # The older records were most likely added by the above steps
    # to be reprocessed so they only have minor changes
    recids_iter = iter(sorted(recids, reverse=True))

    # Split records to process into chunks so that we do not
    # fill up too much memory
    while True:
        task_sleep_now_if_required()

        chunk = list(islice(recids_iter, chunk_size))
        if not chunk:
            break

        write_message("Processing chunk #%s to #%s" % (chunk[0], chunk[-1]))
        # The core work
        cites, refs = process_chunk(chunk, config)
        # Store processed citations/references
        store_dicts(chunk, refs, cites)
        modified = True

    # Compute new weights dictionary
    if modified:
        weights = compute_weights()
    else:
        weights = None

    return weights


def process_chunk(recids, config):
    tags = get_tags_config(config)

    # call the procedure that does the hard work by reading fields of
    # citations and references in the updated_recid's (but nothing else)!
    write_message("Entering get_citation_informations", verbose=9)
    citation_informations = get_citation_informations(recids, tags)

    write_message("Entering ref_analyzer", verbose=9)
    # call the analyser that uses the citation_informations to really
    # search x-cites-y in the coll..
    return ref_analyzer(citation_informations,
                        recids,
                        tags)


def get_bibrankmethod_lastupdate(rank_method_code):
    """return the last excution date of bibrank method
    """
    query = """SELECT DATE_FORMAT(last_updated, '%%Y-%%m-%%d %%H:%%i:%%s')
               FROM rnkMETHOD WHERE name =%s"""
    last_update_time = run_sql(query, [rank_method_code])
    try:
        r = last_update_time[0][0]
    except IndexError:
        r = "0000-00-00 00:00:00"

    return r


def get_bibindex_update_time():
    try:
        # check indexing times of `journal' and `reportnumber`
        # indexes, and only fetch records which have been indexed
        sql = "SELECT DATE_FORMAT(MIN(last_updated), " \
              "'%%Y-%%m-%%d %%H:%%i:%%s') FROM idxINDEX WHERE name IN (%s,%s)"
        index_update_time = run_sql(sql, ('journal', 'reportnumber'), 1)[0][0]
    except IndexError:
        write_message("Not running citation indexer since journal/reportnumber"
                      " indexes are not created yet.")
        index_update_time = "0000-00-00 00:00:00"

    return index_update_time


def get_modified_recs(bibrank_method_lastupdate, indexes_lastupdate):
    """Get records to be updated by bibrank indexing

    Return the list of records which have been modified between the last
    execution of bibrank method and the latest journal/report index updates.
    The result is expected to have ascending id order.
    """
    query = """SELECT id FROM bibrec
               WHERE modification_date >= %s
               AND modification_date < %s
               ORDER BY id ASC"""
    records = run_sql(query, (bibrank_method_lastupdate, indexes_lastupdate))
    return [r[0] for r in records]


def format_journal(format_string, mappings):
    """format the publ infostring according to the format"""

    def replace(char, data):
        return data.get(char, char)

    return ''.join(replace(c, mappings) for c in format_string)


def get_tags_config(config):
    """Fetch needs config from our config file"""
    # Probably "citation" unless this file gets renamed
    function = config.get("rank_method", "function")
    write_message("config function %s" % function, verbose=9)

    tags = {}

    # 037a: contains (often) the "hep-ph/0501084" tag of THIS record
    try:
        tag = config.get(function, "primary_report_number")
    except ConfigParser.NoOptionError:
        tags['record_pri_number'] = None
    else:
        tags['record_pri_number'] = tagify(parse_tag(tag))

    # 088a: additional short identifier for the record
    try:
        tag = config.get(function, "additional_report_number")
    except ConfigParser.NoOptionError:
        tags['record_add_number'] = None
    else:
        tags['record_add_number'] = tagify(parse_tag(tag))

    # 999C5r. this is in the reference list, refers to other records.
    # Looks like: hep-ph/0408002
    try:
        tag = config.get(function, "reference_via_report_number")
    except ConfigParser.NoOptionError:
        tags['refs_report_number'] = None
    else:
        tags['refs_report_number'] = tagify(parse_tag(tag))
    # 999C5s. this is in the reference list, refers to other records.
    # Looks like: Phys.Rev.,A21,78
    try:
        tag = config.get(function, "reference_via_pubinfo")
    except ConfigParser.NoOptionError:
        tags['refs_journal'] = None
    else:
        tags['refs_journal'] = tagify(parse_tag(tag))
    # 999C5a. this is in the reference list, refers to other records.
    # Looks like: 10.1007/BF03170733
    try:
        tag = config.get(function, "reference_via_doi")
    except ConfigParser.NoOptionError:
        tags['refs_doi'] = None
    else:
        tags['refs_doi'] = tagify(parse_tag(tag))

    # Fields needed to construct the journals for this record
    try:
        tag = {
            'pages': config.get(function, "pubinfo_journal_page"),
            'year': config.get(function, "pubinfo_journal_year"),
            'journal': config.get(function, "pubinfo_journal_title"),
            'volume': config.get(function, "pubinfo_journal_volume"),
        }
    except ConfigParser.NoOptionError:
        tags['publication'] = None
    else:
        tags['publication'] = {
            'pages': tagify(parse_tag(tag['pages'])),
            'year': tagify(parse_tag(tag['year'])),
            'journal': tagify(parse_tag(tag['journal'])),
            'volume': tagify(parse_tag(tag['volume'])),
        }

    # Fields needed to lookup the DOIs
    tags['doi'] = get_field_tags('doi')

    # 999C5s. A standardized way of writing a reference in the reference list.
    # Like: Nucl. Phys. B 710 (2000) 371
    try:
        tags['publication_format'] = config.get(function,
                                                "pubinfo_journal_format")
    except ConfigParser.NoOptionError:
        tags['publication_format'] = CFG_JOURNAL_PUBINFO_STANDARD_FORM

    # Print values of tags for debugging
    write_message("tag values: %r" % [tags], verbose=9)

    return tags


def get_journal_info(recid, tags):
    record_info = []

    record = get_record(recid)
    journals_fields = record.find_fields(tags['publication']['journal'][:5])
    for field in journals_fields:
        # we store the tags and their values here
        # like c->444 y->1999 p->"journal of foo",
        # v->20
        tagsvalues = {}
        try:
            tmp = field.get_subfield_values(tags['publication']['journal'][5])[0]
        except IndexError:
            pass
        else:
            tagsvalues["p"] = tmp

        try:
            tmp = field.get_subfield_values(tags['publication']['volume'][5])[0]
        except IndexError:
            pass
        else:
            tagsvalues["v"] = tmp

        try:
            tmp = field.get_subfield_values(tags['publication']['year'][5])[0]
        except IndexError:
            pass
        else:
            tagsvalues["y"] = tmp

        try:
            tmp = field.get_subfield_values(tags['publication']['pages'][5])[0]
        except IndexError:
            pass
        else:
            # if the page numbers have "x-y" take just x
            tagsvalues["c"] = tmp.split('-', 1)[0]

        # check if we have the required data
        ok = True
        for c in tags['publication_format']:
            if c in ('p', 'v', 'y', 'c'):
                if c not in tagsvalues:
                    ok = False

        if ok:
            publ = format_journal(tags['publication_format'], tagsvalues)
            record_info += [publ]

            alt_volume = get_alt_volume(tagsvalues['v'])
            if alt_volume:
                tagsvalues2 = tagsvalues.copy()
                tagsvalues2['v'] = alt_volume
                publ = format_journal(tags['publication_format'], tagsvalues2)
                record_info += [publ]

            # Add codens
            for coden in get_kb_mappings('CODENS',
                                         value=tagsvalues['p']):
                tagsvalues2 = tagsvalues.copy()
                tagsvalues2['p'] = coden['key']
                publ = format_journal(tags['publication_format'], tagsvalues2)
                record_info += [publ]

    return record_info


def get_alt_volume(volume):
    alt_volume = None
    if re.match(ur'[a-zA-Z]\d+', volume, re.U|re.I):
        alt_volume = volume[1:] + volume[0]
    elif re.match(ur'\d+[a-zA-Z]', volume, re.U|re.I):
        alt_volume = volume[-1] + volume[:-1]
    return alt_volume


def get_citation_informations(recid_list, tags, fetch_catchup_info=True):
    """scans the collections searching references (999C5x -fields) and
       citations for items in the recid_list
       returns a 4 list of dictionaries that contains the citation information
       of cds records
       examples: [ {} {} {} {} ]
                 [ {5: 'SUT-DP-92-70-5'},
                   { 93: ['astro-ph/9812088']},
                   { 93: ['Phys. Rev. Lett. 96 (2006) 081301'] }, {} ]
        NB: stuff here is for analysing new or changed records.
        see "ref_analyzer" for more.
    """
    begin_time = os.times()[4]

    records_info = {
        'report-numbers': {},
        'journals': {},
        'doi': {},
    }

    references_info = {
        'report-numbers': {},
        'journals': {},
        'doi': {},
    }

    # perform quick check to see if there are some records with
    # reference tags, because otherwise get.cit.inf would be slow even
    # if there is nothing to index:
    done = 0  # for status reporting
    for recid in recid_list:
        if done % 10 == 0:
            task_sleep_now_if_required()

        if done % 50 == 0:
            mesg = "get cit.inf done %s of %s" % (done, len(recid_list))
            write_message(mesg)
            task_update_progress(mesg)

        done += 1

        if recid in INTBITSET_OF_DELETED_RECORDS:
            # do not treat this record since it was deleted; we
            # skip it like this in case it was only soft-deleted
            # e.g. via bibedit (i.e. when collection tag 980 is
            # DELETED but other tags like report number or journal
            # publication info remained the same, so the calls to
            # get_fieldvalues() below would return old values)
            continue

        if tags['refs_report_number']:
            references_info['report-numbers'][recid] \
                    = get_fieldvalues(recid,
                                      tags['refs_report_number'],
                                      sort=False)
            msg = "references_info['report-numbers'][%s] = %r" \
                        % (recid, references_info['report-numbers'][recid])
            write_message(msg, verbose=9)
        if tags['refs_journal']:
            references_info['journals'][recid] = []
            for ref in get_fieldvalues(recid,
                                       tags['refs_journal'],
                                       sort=False):
                try:
                    # Inspire specific parsing
                    journal, volume, page = ref.split(',')
                except ValueError:
                    pass
                else:
                    alt_volume = get_alt_volume(volume)
                    if alt_volume:
                        alt_ref = ','.join([journal, alt_volume, page])
                        references_info['journals'][recid] += [alt_ref]
                references_info['journals'][recid] += [ref]
            msg = "references_info['journals'][%s] = %r" \
                              % (recid, references_info['journals'][recid])
            write_message(msg, verbose=9)
        if tags['refs_doi']:
            references_info['doi'][recid] \
                    = get_fieldvalues(recid, tags['refs_doi'], sort=False)
            msg = "references_info['doi'][%s] = %r" \
                                   % (recid, references_info['doi'][recid])
            write_message(msg, verbose=9)

        if not fetch_catchup_info:
            # We do not need the extra info
            continue

        if tags['record_pri_number'] or tags['record_add_number']:
            records_info['report-numbers'][recid] = []

            if tags['record_pri_number']:
                records_info['report-numbers'][recid] \
                    += get_fieldvalues(recid,
                                       tags['record_pri_number'],
                                       sort=False)
            if tags['record_add_number']:
                records_info['report-numbers'][recid] \
                    += get_fieldvalues(recid,
                                       tags['record_add_number'],
                                       sort=False)

            msg = "records_info[%s]['report-numbers'] = %r" \
                        % (recid, records_info['report-numbers'][recid])
            write_message(msg, verbose=9)

        if tags['doi']:
            records_info['doi'][recid] = []
            for tag in tags['doi']:
                records_info['doi'][recid] += get_fieldvalues(recid,
                                                              tag,
                                                              sort=False)
            msg = "records_info[%s]['doi'] = %r" \
                                      % (recid, records_info['doi'][recid])
            write_message(msg, verbose=9)

        # get a combination of
        # journal vol (year) pages
        if tags['publication']:
            records_info['journals'][recid] = get_journal_info(recid, tags)
            msg = "records_info[%s]['journals'] = %r" \
                                 % (recid, records_info['journals'][recid])
            write_message(msg, verbose=9)

    mesg = "get cit.inf done fully"
    write_message(mesg)
    task_update_progress(mesg)

    end_time = os.times()[4]
    write_message("Execution time for generating citation info "
                  "from record: %.2f sec" % (end_time - begin_time))

    return records_info, references_info


def standardize_report_number(report_number):
    # Remove category for arxiv papers
    report_number = re.sub(ur'(?:arXiv:)?(\d{4}\.\d{4}) \[[a-zA-Z\.-]+\]',
                  ur'arXiv:\g<1>',
                  report_number,
                  re.I | re.U)
    return report_number


def ref_analyzer(citation_informations, updated_recids, tags):
    """Analyze the citation informations and calculate the citation weight
       and cited by list dictionary.
    """
    citations = {}
    for recid in updated_recids:
        citations[recid] = set()
    references = {}
    for recid in updated_recids:
        references[recid] = set()

    def step(msg_prefix, recid, done, total):
        if done % 30 == 0:
            task_sleep_now_if_required()

        if done % 1000 == 0:
            mesg = "%s done %s of %s" % (msg_prefix, done, total)
            write_message(mesg)
            task_update_progress(mesg)

        write_message("Processing: %s" % recid, verbose=9)

    def add_to_cites(citer, citee):
        # Make sure we don't add ourselves
        # Workaround till we know why we are adding ourselves.
        if citer == citee:
            return

        citations[citee].add(citer)
        if citer in updated_recids:
            references[citer].add(citee)

    def add_to_refs(citer, citee):
        # Make sure we don't add ourselves
        # Workaround till we know why we are adding ourselves.
        if citer == citee:
            return

        if citee in updated_recids:
            citations[citee].add(citer)
        references[citer].add(citee)

    # dict of recid -> institute_give_publ_id
    records_info, references_info = citation_informations

    t1 = os.times()[4]

    # Try to find references based on 999C5r
    # e.g 8 -> ([astro-ph/9889],[hep-ph/768])
    # meaning: rec 8 contains these in bibliography
    write_message("Phase 1: Report numbers references")
    done = 0
    for thisrecid, refnumbers in references_info['report-numbers'].iteritems():
        step("Report numbers references", thisrecid, done,
                                        len(references_info['report-numbers']))
        done += 1

        for refnumber in (r for r in refnumbers if r):
            field = 'reportnumber'
            refnumber = standardize_report_number(refnumber)
            # Search for "hep-th/5644654 or such" in existing records
            recids = get_recids_matching_query(p=refnumber, f=field)
            write_message("These match searching %s in %s: %s" % \
                                   (refnumber, field, list(recids)), verbose=9)

            if not recids:
                insert_into_missing(thisrecid, refnumber)
            else:
                remove_from_missing(refnumber)

            if len(recids) > 1:
                store_citation_warning('multiple-matches', refnumber)
                msg = "Whoops: record '%d' report number value '%s' " \
                      "matches many records; taking only the first one. %s" % \
                      (thisrecid, refnumber, repr(recids))
                write_message(msg, stream=sys.stderr)

            for recid in list(recids)[:1]:  # take only the first one
                add_to_refs(thisrecid, recid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    t2 = os.times()[4]

    # Try to find references based on 999C5s
    # e.g. Phys.Rev.Lett. 53 (1986) 2285
    write_message("Phase 2: Journal references")
    done = 0
    for thisrecid, refs in references_info['journals'].iteritems():
        step("Journal references", thisrecid, done,
                                              len(references_info['journals']))
        done += 1

        for reference in (r for r in refs if r):
            p = reference
            field = 'journal'

            # check reference value to see whether it is well formed:
            if not re_CFG_JOURNAL_PUBINFO_STANDARD_FORM_REGEXP_CHECK.match(p):
                store_citation_warning('not-well-formed', p)
                msg = "Whoops, record '%d' reference value '%s' " \
                      "is not well formed; skipping it." % (thisrecid, p)
                write_message(msg, stream=sys.stderr)
                continue  # skip this ill-formed value

            recids = search_unit(p, field) - INTBITSET_OF_DELETED_RECORDS
            write_message("These match searching %s in %s: %s" \
                                 % (reference, field, list(recids)), verbose=9)

            if not recids:
                insert_into_missing(thisrecid, p)
            else:
                remove_from_missing(p)

            if len(recids) > 1:
                store_citation_warning('multiple-matches', p)
                msg = "Whoops: record '%d' reference value '%s' " \
                      "matches many records; taking only the first one. %s" % \
                      (thisrecid, p, repr(recids))
                write_message(msg, stream=sys.stderr)

            for recid in list(recids)[:1]:  # take only the first one
                add_to_refs(thisrecid, recid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    t3 = os.times()[4]

    # Try to find references based on 999C5a
    # e.g. 10.1007/BF03170733
    write_message("Phase 3: DOI references")
    done = 0
    for thisrecid, refs in references_info['doi'].iteritems():
        step("DOI references", thisrecid, done, len(references_info['doi']))
        done += 1

        for reference in (r for r in refs if r):
            p = reference
            field = 'doi'

            recids = get_recids_matching_query(p, field)
            write_message("These match searching %s in %s: %s" \
                                 % (reference, field, list(recids)), verbose=9)

            if not recids:
                insert_into_missing(thisrecid, p)
            else:
                remove_from_missing(p)

            if len(recids) > 1:
                store_citation_warning('multiple-matches', p)
                msg = "Whoops: record '%d' DOI value '%s' " \
                      "matches many records; taking only the first one. %s" % \
                      (thisrecid, p, repr(recids))
                write_message(msg, stream=sys.stderr)

            for recid in list(recids)[:1]:  # take only the first one
                add_to_refs(thisrecid, recid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    t4 = os.times()[4]

    # Search for stuff like CERN-TH-4859/87 in list of refs
    write_message("Phase 4: report numbers catchup")
    done = 0
    for thisrecid, reportcodes in records_info['report-numbers'].iteritems():
        step("Report numbers catchup", thisrecid, done,
                                           len(records_info['report-numbers']))
        done += 1

        for reportcode in (r for r in reportcodes if r):
            if reportcode.startswith('arXiv'):
                std_reportcode = standardize_report_number(reportcode)
                report_pattern = r'^%s( *\[[a-zA-Z.-]*\])?' % \
                                                re.escape(std_reportcode)
                recids = get_recids_matching_query(report_pattern,
                                                   tags['refs_report_number'],
                                                   'r')
            else:
                recids = get_recids_matching_query(reportcode,
                                                   tags['refs_report_number'],
                                                   'e')
            for recid in recids:
                add_to_cites(recid, thisrecid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    # Find this record's pubinfo in other records' bibliography
    write_message("Phase 5: journals catchup")
    done = 0
    t5 = os.times()[4]
    for thisrecid, rec_journals in records_info['journals'].iteritems():
        step("Journals catchup", thisrecid, done,
                                                 len(records_info['journals']))
        done += 1

        for journal in rec_journals:
            journal = journal.replace("\"", "")
            # Search the publication string like
            # Phys. Lett., B 482 (2000) 417 in 999C5s
            recids = search_unit(p=journal, f=tags['refs_journal'], m='a') \
                                                - INTBITSET_OF_DELETED_RECORDS
            write_message("These records match %s in %s: %s" \
                    % (journal, tags['refs_journal'], list(recids)), verbose=9)

            for recid in recids:
                add_to_cites(recid, thisrecid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    write_message("Phase 6: DOI catchup")
    done = 0
    t6 = os.times()[4]
    for thisrecid, dois in records_info['doi'].iteritems():
        step("DOI catchup", thisrecid, done, len(records_info['doi']))
        done += 1

        for doi in dois:
            # Search the publication string like
            # Phys. Lett., B 482 (2000) 417 in 999C5a
            recids = search_unit(p=doi, f=tags['refs_doi'], m='a') \
                                                - INTBITSET_OF_DELETED_RECORDS
            write_message("These records match %s in %s: %s" \
                            % (doi, tags['refs_doi'], list(recids)), verbose=9)

            for recid in recids:
                add_to_cites(recid, thisrecid)

    mesg = "done fully"
    write_message(mesg)
    task_update_progress(mesg)

    if task_get_task_param('verbose') >= 3:
        # Print only X first to prevent flood
        write_message("citation_list (x is cited by y):")
        write_message(dict(islice(citations.iteritems(), 10)))
        write_message("size: %s" % len(citations))
        write_message("reference_list (x cites y):")
        write_message(dict(islice(references.iteritems(), 10)))
        write_message("size: %s" % len(references))
        write_message("selfcitedbydic (x is cited by y and one of the " \
                      "authors of x same as y's):")

    t7 = os.times()[4]

    write_message("Execution time for analyzing the citation information " \
                  "generating the dictionary:")
    write_message("... checking ref report numbers: %.2f sec" % (t2-t1))
    write_message("... checking ref journals: %.2f sec" % (t3-t2))
    write_message("... checking ref DOI: %.2f sec" % (t4-t3))
    write_message("... checking rec report numbers: %.2f sec" % (t5-t4))
    write_message("... checking rec journals: %.2f sec" % (t6-t5))
    write_message("... checking rec DOI: %.2f sec" % (t7-t6))
    write_message("... total time of ref_analyze: %.2f sec" % (t7-t1))

    return citations, references


def store_dicts(recids, refs, cites):
    """Insert the reference and citation list into the database"""
    for recid in recids:
        replace_refs(recid, refs[recid])
        replace_cites(recid, cites[recid])


def replace_refs(recid, new_refs):
    old_refs = set(row[0] for row in run_sql("""SELECT citee
                                                FROM rnkCITATIONDICT
                                                WHERE citer = %s""", [recid]))

    refs_to_add = new_refs - old_refs
    refs_to_delete = old_refs - new_refs

    for ref in refs_to_add:
        write_message('adding ref %s %s' % (recid, ref), verbose=1)
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        run_sql("""INSERT INTO rnkCITATIONDICT (citer, citee, last_updated)
                   VALUES (%s, %s, %s)""", (recid, ref, now))

    for ref in refs_to_delete:
        write_message('deleting ref %s %s' % (recid, ref), verbose=1)
        run_sql("""DELETE FROM rnkCITATIONDICT
                   WHERE citer = %s and citee = %s""", (recid, ref))


def replace_cites(recid, new_cites):
    old_cites = set(row[0] for row in run_sql("""SELECT citer
                                                FROM rnkCITATIONDICT
                                                WHERE citee = %s""", [recid]))

    cites_to_add = new_cites - old_cites
    cites_to_delete = old_cites - new_cites

    for cite in cites_to_add:
        write_message('adding cite %s %s' % (recid, cite), verbose=1)
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        run_sql("""INSERT INTO rnkCITATIONDICT (citee, citer, last_updated)
                   VALUES (%s, %s, %s)""", (recid, cite, now))

    for cite in cites_to_delete:
        write_message('deleting cite %s %s' % (recid, cite), verbose=1)
        run_sql("""DELETE FROM rnkCITATIONDICT
                   WHERE citee = %s and citer = %s""", (recid, cite))


def insert_into_missing(recid, report):
    """put the referingrecordnum-publicationstring into
       the "we are missing these" table"""
    if len(report) >= 255:
        # Invalid report, it is too long
        # and does not fit in the database column
        # (currently varchar 255)
        return
    wasalready = run_sql("""SELECT id_bibrec
                            FROM rnkCITATIONDATAEXT
                            WHERE id_bibrec = %s
                            AND extcitepubinfo = %s""",
                          (recid, report))
    if not wasalready:
        run_sql("""INSERT INTO rnkCITATIONDATAEXT(id_bibrec, extcitepubinfo)
                   VALUES (%s,%s)""", (recid, report))


def remove_from_missing(report):
    """remove the recid-ref -pairs from the "missing" table for report x: prob
       in the case ref got in our library collection"""
    run_sql("""DELETE FROM rnkCITATIONDATAEXT
               WHERE extcitepubinfo = %s""", (report,))


def print_missing(num):
    """
    Print the contents of rnkCITATIONDATAEXT table containing external
    records that were cited by NUM or more internal records.

    NUM is by default taken from the -E command line option.
    """
    if not num:
        num = task_get_option("print-extcites")

    write_message("Listing external papers cited by %i or more \
                                                      internal records:" % num)

    res = run_sql("""SELECT COUNT(id_bibrec), extcitepubinfo
                     FROM rnkCITATIONDATAEXT
                     GROUP BY extcitepubinfo HAVING COUNT(id_bibrec) >= %s
                     ORDER BY COUNT(id_bibrec) DESC""", (num,))
    for cnt, brec in res:
        print str(cnt), "\t", brec

    write_message("Listing done.")


def tagify(parsedtag):
    """aux auf to make '100__a' out of ['100','','','a']"""
    tag = ""
    for t in parsedtag:
        if t == '':
            t = '_'
        tag += t
    return tag


def store_citation_warning(warning_type, cit_info):
    r = run_sql("""SELECT 1 FROM rnkCITATIONDATAERR
                   WHERE type = %s
                   AND citinfo = %s""", (warning_type, cit_info))
    if not r:
        run_sql("""INSERT INTO rnkCITATIONDATAERR (type, citinfo)
                   VALUES (%s, %s)""", (warning_type, cit_info))
