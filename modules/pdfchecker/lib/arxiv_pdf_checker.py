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
import urllib2
import socket

from invenio.bibdocfilecli import bibupload_ffts
from invenio.docextract_task import store_last_updated, \
                                    fetch_last_updated
from invenio.shellutils import split_cli_ids_arg
from invenio.dbquery import run_sql
from invenio.bibtask import task_low_level_submission
from invenio.refextract_api import record_has_fulltext, \
                                   check_record_for_refextract
from invenio.bibtask import task_init, \
                            write_message, \
                            task_update_progress, \
                            task_get_option, \
                            task_set_option, \
                            task_sleep_now_if_required
from invenio.search_engine_utils import get_fieldvalues
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


NAME = 'arxiv-pdf-checker'
ARXIV_VERSION_PATTERN = re.compile(ur'v\d$', re.UNICODE)

STATUS_OK = 'ok'
STATUS_MISSING = 'missing'


class InvenioFileDownloadError(Exception):
    """A generic download exception."""
    def __init__(self, msg, code=None):
        Exception.__init__(self, msg)
        self.code = code


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
    for report_number_field in record['037']:
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


### File utils temporary acquisition

# Block size when performing I/O.
CFG_FILEUTILS_BLOCK_SIZE = 1024 * 8


def open_url(url, headers=None):
    """
    Opens a URL. If headers are passed as argument, no check is performed and
    the URL will be opened. Otherwise checks if the URL is present in
    CFG_BIBUPLOAD_FFT_ALLOWED_EXTERNAL_URLS and uses the headers specified in
    the config variable.

    @param url: the URL to open
    @type url: string
    @param headers: the headers to use
    @type headers: dictionary
    @return: a file-like object as returned by urllib2.urlopen.
    """
    request = urllib2.Request(url)
    if headers:
        for key, value in headers.items():
            request.add_header(key, value)
    return urllib2.urlopen(request)


def download_external_url(url, download_to_file, content_type=None,
                          retry_count=10, timeout=10.0):
    """
    Download a url (if it corresponds to a remote file) and return a
    local url to it. If format is specified, a check will be performed
    in order to make sure that the format of the downloaded file is equal
    to the expected format.

    @param url: the URL to download
    @type url: string

    @param download_to_file: the path to download the file to
    @type url: string

    @param content_type: the content_type of the file (optional)
    @type format: string

    @param retry_count: max number of retries for downloading the file
    @type url: int

    @param timeout: time to sleep in between attemps
    @type url: int

    @return: the path to the download local file
    @rtype: string
    @raise InvenioFileDownloadError: if the download failed
    """
    error_str = ""
    error_code = None
    retry_attempt = 0

    while retry_attempt < retry_count:
        try:
            # Attempt to download the external file
            request = open_url(url)
            if request.code == 200 and "Refresh" in request.headers:
                # PDF is being generated, they ask us to wait for n seconds
                # New arxiv responses, we are not sure if the old ones are
                # desactivated
                try:
                    retry_after = int(request.headers["Refresh"])
                    # We make sure that we do not retry too often even if
                    # they tell us to retry after 1s
                    retry_after = max(retry_after, timeout)
                except ValueError:
                    retry_after = timeout
                write_message("retrying after %ss" % retry_after)
                time.sleep(retry_after)
                retry_attempt += 1
                continue
        except urllib2.HTTPError, e:
            error_code = e.code
            error_str = str(e)
            retry_after = timeout
            # This handling is the same as OAI queries.
            # We are getting 503 errors when PDFs are being generated
            if e.code == 503 and "Retry-After" in e.headers:
                # PDF is being generated, they ask us to wait for n seconds
                try:
                    retry_after = int(e.headers["Retry-After"])
                    # We make sure that we do not retry too often even if
                    # they tell us to retry after 1s
                    retry_after = max(retry_after, timeout)
                except ValueError:
                    pass
            write_message("retrying after %ss" % retry_after)
            time.sleep(retry_after)
            retry_attempt += 1
        except (urllib2.URLError, socket.timeout, socket.gaierror, socket.error), e:
            error_str = str(e)
            write_message("socket error, retrying after %ss" % retry_after)
            time.sleep(timeout)
            retry_attempt += 1
        else:
            # When we get here, it means that the download was a success.
            try:
                finalize_download(url, download_to_file, content_type, request)
            finally:
                request.close()
            return download_to_file

    # All the attempts were used, but no successfull download - so raise error
    raise InvenioFileDownloadError('URL could not be opened: %s' % (error_str,), code=error_code)


def finalize_download(url, download_to_file, content_type, request):
    # If format is given, a format check is performed.
    if content_type and content_type not in request.headers['content-type']:
        msg = 'The downloaded file is not of the desired format'
        raise InvenioFileDownloadError(msg)

    # Save the downloaded file to desired or generated location.
    to_file = open(download_to_file, 'w')
    try:
        try:
            while True:
                block = request.read(CFG_FILEUTILS_BLOCK_SIZE)
                if not block:
                    break
                to_file.write(block)
        except Exception, e:
            raise InvenioFileDownloadError("Error when downloading %s into %s: %s" %
                    (url, download_to_file, e))
    finally:
        to_file.close()

    # Check Size
    filesize = os.path.getsize(download_to_file)
    if filesize == 0:
        raise InvenioFileDownloadError("%s seems to be empty" % (url,))

    # Check if it is not an html not found page
    if filesize < 25000:
        f = open(download_to_file)
        try:
            for line in f:
                if 'PDF unavailable' in line:
                    raise PdfNotAvailable()
        finally:
            f.close()

    # download successful, return the new path
    return download_to_file


### End of file utils temporary acquisition


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
    recids = [recid for recid in recids if check_record_for_refextract(recid)]

    if recids:
        recids_str = ','.join(str(recid) for recid in recids)
        task_low_level_submission('refextract', NAME, '-r', recids_str)


def fetch_updated_arxiv_records(date):
    """Fetch all the arxiv records modified since the last run"""

    def check_arxiv(recid):
        """Returns True for arxiv papers"""
        for report_number in get_fieldvalues(recid, '037__9'):
            if report_number == 'arXiv':
                return True
        return False

    # Fetch all records inserted since last run
    sql = "SELECT `id`, `modification_date` FROM `bibrec` " \
          "WHERE `modification_date` >= %s " \
          "ORDER BY `modification_date`"
    records = run_sql(sql, [date.isoformat()])
    records = [(r, mod_date) for r, mod_date in records if check_arxiv(r)]

    # Show all records for debugging purposes
    if task_get_option('verbose') >= 9:
        write_message('recids:', verbose=9)
        for recid, mod_date in records:
            write_message("* %s, %s" % (recid, mod_date), verbose=9)

    task_update_progress("Done fetching %s arxiv record ids" % len(records))
    return records


def task_run_core(name=NAME):
    """Entry point for the arxiv-pdf-checker task"""

    # First gather recids to process
    recids = task_get_option('recids')
    if recids:
        start_date = None
        recids = [(recid, None) for recid in recids]
    else:
        start_date = datetime.now()
        dummy, last_date = fetch_last_updated(name)
        recids = fetch_updated_arxiv_records(last_date)

    updated_recids = set()

    try:

        for count, (recid, dummy) in enumerate(recids):
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
