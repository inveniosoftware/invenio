# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
ArXiv Pdf Checker Task

Checks arxiv records for missing pdfs and downloads them from arXiv
"""

import os
import time
import re
from datetime import datetime
from tempfile import NamedTemporaryFile
from xml.dom import minidom
import socket

from invenio.intbitset import intbitset
from invenio.bibdocfilecli import bibupload_ffts
from invenio.docextract_task import store_last_updated, \
                                    fetch_last_updated
from invenio.shellutils import split_cli_ids_arg
from invenio.dbquery import run_sql
from invenio.bibtask import task_low_level_submission
from invenio.refextract_api import record_has_fulltext, \
                                   record_can_extract_refs
from invenio.bibtask import task_init, \
                            write_message, \
                            task_update_progress, \
                            task_get_option, \
                            task_set_option, \
                            task_sleep_now_if_required
from invenio.search_engine_utils import get_fieldvalues
from invenio.search_engine import search_pattern
from invenio.config import CFG_VERSION, \
                           CFG_TMPSHAREDDIR, \
                           CFG_TMPDIR, \
                           CFG_ARXIV_URL_PATTERN
# Help message is the usage() print out of how to use Refextract
from invenio.docextract_record import get_record
from invenio.bibdocfile import BibRecDocs, \
                               calculate_md5
from invenio.oai_harvest_dblayer import get_oai_src
from invenio import oai_harvest_daemon
from invenio.filedownloadutils import (download_external_url,
                                       InvenioFileDownloadError)


NAME = 'arxiv-pdf-checker'
ARXIV_VERSION_PATTERN = re.compile(ur'v\d$', re.UNICODE)

STATUS_OK = 'ok'
STATUS_MISSING = 'missing'


class PdfNotAvailable(Exception):
    pass


class FoundExistingPdf(Exception):
    pass


class AlreadyHarvested(Exception):
    def __init__(self, status):
        Exception.__init__(self)
        self.status = status


def build_arxiv_url(arxiv_id, version):
    return CFG_ARXIV_URL_PATTERN % (arxiv_id, version)


def extract_arxiv_ids_from_recid(recid):
    """Extract arxiv # for given recid

    We get them from the record which has this format:
    037__ $9arXiv$arXiv:1010.1111
    """
    record = get_record(recid)
    for report_number_field in record.get('037', []):
        try:
            source = report_number_field.get_subfield_values('9')[0]
        except IndexError:
            continue
        else:
            if source != 'arXiv':
                continue

        try:
            report_number = report_number_field.get_subfield_values('a')[0]
        except IndexError:
            continue
        else:
            # Extract arxiv id
            if report_number.startswith('arXiv'):
                report_number = report_number.split(':')[1]
            if ARXIV_VERSION_PATTERN.search(report_number):
                report_number = report_number[:-2]
            yield report_number


def cb_parse_option(key, value, opts, args):
    """Parse command line options"""
    if args:
        # There should be no standalone arguments
        raise StandardError("Error: Unrecognised argument '%s'." % args[0])

    if key in ('-i', '--id'):
        recids = task_get_option('recids')
        if not recids:
            recids = set()
            task_set_option('recids', recids)
        recids.update(split_cli_ids_arg(value))

    return True


def store_arxiv_pdf_status(recid, status, version):
    """Store pdf harvesting status in the database"""
    valid_status = (STATUS_OK, STATUS_MISSING)
    if status not in valid_status:
        raise ValueError('invalid status %s' % status)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_sql("""REPLACE INTO bibARXIVPDF (id_bibrec, status, date_harvested, version)
            VALUES (%s, %s, %s, %s)""", (recid, status, now, version))


def fetch_arxiv_pdf_status(recid):
    """Fetch from the database the harvest status of given recid"""
    ret = run_sql("""SELECT status, version FROM bibARXIVPDF
                     WHERE id_bibrec = %s""", [recid])
    return ret and ret[0] or (None, None)


def download_one(recid, version):
    """Download given version of the PDF from arxiv"""
    write_message('fetching %s' % recid)
    for count, arxiv_id in enumerate(extract_arxiv_ids_from_recid(recid)):
        if count != 0:
            write_message("Warning: %s has multiple arxiv #" % recid)
            continue

        url_for_pdf = build_arxiv_url(arxiv_id, version)
        filename_arxiv_id = arxiv_id.replace('/', '_')
        temp_file = NamedTemporaryFile(prefix="arxiv-pdf-checker",
                                       dir=CFG_TMPSHAREDDIR,
                                       suffix="%s.pdf" % filename_arxiv_id)
        write_message('downloading pdf from %s' % url_for_pdf)
        path = download_external_url(url_for_pdf,
                                     temp_file.name,
                                     content_type='pdf')

        # Check if it is not an html not found page
        filesize = os.path.getsize(path)
        if filesize < 25000:
            f = open(path)
            try:
                for line in f:
                    if 'PDF unavailable' in line:
                        raise PdfNotAvailable()
            finally:
                f.close()

        docs = BibRecDocs(recid)
        bibdocfiles = docs.list_latest_files(doctype="arXiv")

        needs_update = False
        try:
            bibdocfile = bibdocfiles[0]
        except IndexError:
            bibdocfile = None
            needs_update = True
        else:
            existing_md5 = calculate_md5(bibdocfile.fullpath)
            new_md5 = calculate_md5(path.encode('utf-8'))
            if new_md5 != existing_md5:
                write_message('md5 differs updating')
                needs_update = True
            else:
                write_message('md5 matches existing pdf, skipping')

        if needs_update:
            if bibdocfiles:
                write_message('adding as new version')
                docs.add_new_version(path, docname=bibdocfile.name)
            else:
                write_message('adding as new file')
                docs.add_new_file(path,
                                  doctype="arXiv",
                                  docname="arXiv:%s" % filename_arxiv_id)
        else:
            raise FoundExistingPdf()


def oai_harvest_query(arxiv_id, prefix='arXivRaw', verb='GetRecord',
                      max_retries=5, repositories=[]):
    """Wrapper of oai_harvest_daemon.oai_harvest_get that handles retries"""
    if not repositories:
        repositories.extend(get_oai_src(params={'name': 'arxiv'}))

    try:
        repository = repositories[0]
    except IndexError:
        raise Exception('arXiv repository information missing from database')

    harvestpath = os.path.join(CFG_TMPDIR, "arxiv-pdf-checker-oai-")

    def get():
        return oai_harvest_daemon.oai_harvest_get(
                                    prefix=prefix,
                                    baseurl=repository['baseurl'],
                                    harvestpath=harvestpath,
                                    verb=verb,
                                    identifier='oai:arXiv.org:%s' % arxiv_id)

    responses = None
    for retry_count in range(1, max_retries + 1):
        try:
            responses = get()
        except (socket.timeout, socket.error):
            write_message('socket error, arxiv is down?')
        else:
            if not responses:
                write_message('no responses from oai server')
            break

        if retry_count <= 2:
            write_message('sleeping for 10s')
            time.sleep(10)
        else:
            write_message('sleeping for 30 minutes')
            time.sleep(1800)

    if responses is None:
        raise Exception('arXiv is down')

    return responses

def fetch_arxiv_version(recid):
    """Query arxiv and extract the version of the pdf from the response"""

    for count, arxiv_id in enumerate(extract_arxiv_ids_from_recid(recid)):
        if count != 0:
            write_message("Warning: %s has multiple arxiv #" % recid)
            continue

        responses = oai_harvest_query(arxiv_id)
        if not responses:
            return None

        # The response is roughly in this format
        # <OAI-PMH>
        #   <GetRecord>
        #     <metadata>
        #       <version version="v1">
        #         <date>Mon, 15 Apr 2013 19:33:21 GMT</date>
        #         <size>609kb</size>
        #         <source_type>D</source_type>
        #       <version version="v2">
        #         <date>Mon, 25 Apr 2013 19:33:21 GMT</date>
        #         <size>620kb</size>
        #         <source_type>D</source_type>
        #       </version>
        #     </<metadata>
        #   </<GetRecord>
        # </<OAI-PMH>

        # We pass one arxiv id, we are assuming a single response file
        tree = minidom.parse(responses[0])
        version_tags = tree.getElementsByTagName('version')
        if version_tags:
            version = version_tags[-1].getAttribute('version')
        else:
            version = 'v1'

        # We have to remove the responses files manually
        # For some written the response is written to disk instead of
        # being a string
        for file_path in responses:
            os.unlink(file_path)

        return int(version[1:])


def process_one(recid):
    """Checks given recid for updated pdfs on arxiv"""
    write_message('checking %s' % recid)

    # Last version we have harvested
    harvest_status, harvest_version = fetch_arxiv_pdf_status(recid)

    # Fetch arxiv version
    arxiv_version = fetch_arxiv_version(recid)
    if not arxiv_version:
        msg = 'version information unavailable'
        write_message(msg)
        raise PdfNotAvailable(msg)

    write_message('harvested_version %s' % harvest_version)
    write_message('arxiv_version %s' % arxiv_version)

    if record_has_fulltext(recid) and harvest_version == arxiv_version:
        write_message('our version matches arxiv')
        raise AlreadyHarvested(status=harvest_status)

    # We already tried to harvest this record but failed
    if harvest_status == STATUS_MISSING and harvest_version == arxiv_version:
        raise PdfNotAvailable()

    updated = False

    try:
        download_one(recid, arxiv_version)
    except PdfNotAvailable:
        store_arxiv_pdf_status(recid, STATUS_MISSING, arxiv_version)
        raise
    except FoundExistingPdf:
        store_arxiv_pdf_status(recid, STATUS_OK, arxiv_version)
        raise
    else:
        store_arxiv_pdf_status(recid, STATUS_OK, arxiv_version)
        updated = True

    return updated


def submit_fixmarc_task(recids):
    """Submit a task that synchronizes the 8564 tags

    This should be done right after changing the files attached to a record"""
    field = [{'doctype' : 'FIX-MARC'}]
    ffts = {}
    for recid in recids:
        ffts[recid] = field
    bibupload_ffts(ffts, append=False, interactive=False)


def submit_refextract_task(recids):
    """Submit a refextract task if needed"""
    # First filter out recids we cannot safely extract references from
    # (mostly because they have been curated)
    recids = [recid for recid in recids if not record_can_extract_refs(recid)]

    if recids:
        recids_str = ','.join(str(recid) for recid in recids)
        task_low_level_submission('refextract', NAME, '-i', recids_str,
                                  '--overwrite')

_RE_ARXIV_ID = re.compile(re.escape("<identifier>oai:arXiv.org:") + "(.+?)" + re.escape("</identifier>"), re.M)
def fetch_updated_arxiv_records(date):
    """Fetch all the arxiv records modified since the last run"""

    from invenio.oai_harvest_getter import harvest
    harvested_files = harvest("export.arxiv.org", "/oai2", {
        "verb": "ListIdentifiers",
        "from": date.strftime("%Y-%m-%d"),
        "metadataPrefix": "arXiv"},
        output=os.path.join(CFG_TMPDIR, "arxiv-pdf-checker-oai-tmp-"))
    modified_arxiv_ids = []
    for harvested_file in harvested_files:
        modified_arxiv_ids += _RE_ARXIV_ID.findall(open(harvested_file).read())
        os.remove(harvested_file)
    recids = intbitset()
    for arxiv_id in modified_arxiv_ids:
        recids |= search_pattern(p='035__a:"oai:arXiv.org:%s"' % arxiv_id)
    return recids - search_pattern(p="980:DELETED")


def task_run_core(name=NAME):
    """Entry point for the arxiv-pdf-checker task"""

    # First gather recids to process
    recids = task_get_option('recids')
    if recids:
        start_date = None
    else:
        start_date = datetime.now()
        dummy, last_date = fetch_last_updated(name)
        recids = fetch_updated_arxiv_records(last_date)

    updated_recids = set()

    try:

        for count, recid in enumerate(recids):
            if count % 50 == 0:
                msg = 'Done %s of %s' % (count, len(recids))
                write_message(msg)
                task_update_progress(msg)

            # BibTask sleep
            task_sleep_now_if_required(can_stop_too=True)

            write_message('processing %s' % recid, verbose=9)
            try:
                if process_one(recid):
                    updated_recids.add(recid)
                time.sleep(6)
            except AlreadyHarvested:
                write_message('already harvested successfully')
                time.sleep(6)
            except FoundExistingPdf:
                write_message('pdf already attached (matching md5)')
                time.sleep(6)
            except PdfNotAvailable:
                write_message("no pdf available")
                time.sleep(20)
            except InvenioFileDownloadError, e:
                write_message("failed to download: %s" % e)
                time.sleep(20)

    finally:
        # We want to process updated records even in case we are interrupted
        msg = 'Updated %s records' % len(updated_recids)
        write_message(msg)
        task_update_progress(msg)
        write_message(repr(updated_recids))

        # For all updated records, we want to sync the 8564 tags
        # and reextract references
        if updated_recids:
            submit_fixmarc_task(updated_recids)
            submit_refextract_task(updated_recids)

    # Store last run date of the daemon
    # not if it ran on specific recids from the command line with --id
    # but only if it ran on the modified records
    if start_date:
        store_last_updated(0, start_date, name)

    return True


def main():
    """Constructs the refextract bibtask."""
    # Build and submit the task
    task_init(authorization_action='runarxivpdfchecker',
        authorization_msg="Arxiv Pdf Checker Task Submission",
        description="""Daemon that checks if we have the latest version of arxiv PDFs""",
        # get the global help_message variable imported from refextract.py
        help_specific_usage="""
  Scheduled (daemon) options:
  -i, --id       Record id to check.

  Examples:
   (run a daemon job)
      arxiv-pdf-checker

""",
        version="Invenio v%s" % CFG_VERSION,
        specific_params=("i:", ["id="]),
        task_submit_elaborate_specific_parameter_fnc=cb_parse_option,
        task_run_fnc=task_run_core)
