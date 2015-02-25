# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012 CERN.
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
File handling utilities.

Main API usage:
    >>> from filedownloadutils import download_url
    >>> new_file = download_url("http://duckduckgo.com", content_type="html")

Raises InvenioFileDownloadError exception.
"""

import urllib2
import time
import os
import socket
import urllib
import tempfile
import shutil
import sys

from invenio.utils.url import make_invenio_opener

URL_OPENER = make_invenio_opener('filedownloadutils')

from invenio.config import (CFG_TMPSHAREDDIR,
                            CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS,
                            CFG_WEBSUBMIT_STORAGEDIR)

#: block size when performing I/O.
CFG_FILEUTILS_BLOCK_SIZE = 1024 * 8


class InvenioFileDownloadError(Exception):
    """A generic download exception."""
    def __init__(self, msg, code=None):
        Exception.__init__(self, msg)
        self.code = code


class InvenioFileCopyError(Exception):
    """A generic file copy exception."""
    pass


def download_url(url, content_type=None, download_to_file=None,
                 retry_count=10, timeout=10.0):
    """
    Will download a file from given URL (either local or external) to the
    desired path (or generate one if none is given). Local files are copied
    directly.

    The function will retry a number of times based on retry_count (default 10)
    parameter and sleeps a number of seconds based on given timeout
    (default 10.0 sec) after each failed request.

    Returns the path to the downloaded file if successful.
    Otherwise an exception is raised.

    Given a content_type and an external URL, the function will make sure
    that the desired content_type is equal to the content-type of returned
    file.

    @param url: where the file lives on the interwebs
    @type url: string

    @param content_type: desired content_type to check for in external URLs.
                         (optional)
    @type content_type: string

    @param download_to_file: where the file should live after download.
                             (optional)
    @type download_to_file: string

    @param retry_count: number of times to retry. Defaults to 10.
                        (optional)
    @type retry_count: int

    @param timeout: number of seconds to sleep between attempts.
                    Defaults to 10.0 seconds. (optional)
    @type timeout: float

    @return: the path of the downloaded/copied file
    @raise InvenioFileDownloadError: raised upon URL/HTTP errors, file errors or wrong format
    """
    if not download_to_file:
        download_to_file = safe_mkstemp(suffix=".tmp",
                                        prefix="filedownloadutils_")

    try:
        if is_url_a_local_file(url):
            downloaded_file = download_local_file(url,
                                                  download_to_file)
        else:
            downloaded_file = download_external_url(url,
                                                    download_to_file,
                                                    content_type=content_type,
                                                    retry_count=retry_count,
                                                    timeout=timeout)
    except InvenioFileDownloadError:
        raise

    return downloaded_file


def download_external_url(url, download_to_file, content_type=None,
                          retry_count=10, timeout=10.0, verbose=False):
    """
    Download a url (if it corresponds to a remote file) and return a
    local url to it. If format is specified, a check will be performed
    in order to make sure that the format of the downloaded file is equal
    to the expected format.

    @param url: the URL to download
    @type url: string

    @param download_to_file: the path to download the file to
    @type download_to_file: string

    @param content_type: the content_type of the file (optional)
    @type content_type: string

    @param retry_count: max number of retries for downloading the file
    @type retry_count: int

    @param timeout: time to sleep in between attemps
    @type timeout: int

    @return: the path to the download local file
    @rtype: string
    @raise StandardError: if the download failed
    """
    error_str = ""
    error_code = None
    retry_attempt = 0

    while retry_attempt < retry_count:
        try:
            # Attempt to download the external file
            request = open_url(url)
            if request.code == 200 and "Refresh" in request.headers:
                # PDF is being generated, they ask us to wait for
                # n seconds.
                # New arxiv responses, we are not sure if the old ones are
                # deactivated
                try:
                    retry_after = int(request.headers["Refresh"])
                    # We make sure that we do not retry too often even if
                    # they tell us to retry after 1s
                    retry_after = max(retry_after, timeout)
                except ValueError:
                    retry_after = timeout
                if verbose:
                    msg = "retrying after %ss" % (retry_after,)
                    print >> sys.stderr, msg
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
            if verbose:
                msg = "retrying after %ss" % (retry_after,)
                print >> sys.stderr, msg
            time.sleep(retry_after)
            retry_attempt += 1
        except (urllib2.URLError,
                socket.timeout,
                socket.gaierror,
                socket.error), e:
            if verbose:
                error_str = str(e)
                msg = "socket error, retrying after %ss" % (timeout,)
                print >> sys.stderr, msg
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
    msg = 'URL could not be opened: %s' % (error_str,)
    raise InvenioFileDownloadError(msg, code=error_code)


def finalize_download(url, download_to_file, content_type, request):
    """
    Finalizes the download operation by doing various checks, such as format
    type, size check etc.
    """
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
            msg = "Error when downloading %s into %s: %s" % \
                  (url, download_to_file, e)
            raise InvenioFileDownloadError(msg)
    finally:
        to_file.close()

    # Check Size
    filesize = os.path.getsize(download_to_file)
    if filesize == 0:
        raise InvenioFileDownloadError("%s seems to be empty" % (url,))

    # download successful, return the new path
    return download_to_file


def download_local_file(filename, download_to_file):
    """
    Copies a local file to Invenio's temporary directory.

    @param filename: the name of the file to copy
    @type filename: string

    @param download_to_file: the path to save the file to
    @type download_to_file: string

    @return: the path of the temporary file created
    @rtype: string
    @raise StandardError: if something went wrong
    """
    # Try to copy.
    try:
        path = urllib2.urlparse.urlsplit(urllib.unquote(filename))[2]
        if os.path.abspath(path) != path:
            msg = "%s is not a normalized path (would be %s)." \
                  % (path, os.path.normpath(path))
            raise InvenioFileCopyError(msg)

        allowed_path_list = CFG_BIBUPLOAD_FFT_ALLOWED_LOCAL_PATHS
        allowed_path_list.append(CFG_TMPSHAREDDIR)
        allowed_path_list.append(CFG_WEBSUBMIT_STORAGEDIR)
        for allowed_path in allowed_path_list:
            if path.startswith(allowed_path):
                shutil.copy(path, download_to_file)
                if os.path.getsize(download_to_file) == 0:
                    os.remove(download_to_file)
                    msg = "%s seems to be empty" % (filename,)
                    raise InvenioFileCopyError(msg)
                break
        else:
            msg = "%s is not in one of the allowed paths." % (path,)
            raise InvenioFileCopyError()
    except Exception, e:
        msg = "Impossible to copy the local file '%s' to %s: %s" % \
              (filename, download_to_file, str(e))
        raise InvenioFileCopyError(msg)

    return download_to_file


def is_url_a_local_file(url):
    """Return True if the given URL is pointing to a local file."""
    protocol = urllib2.urlparse.urlsplit(url)[0]
    return protocol in ('', 'file')


def safe_mkstemp(suffix, prefix='filedownloadutils_'):
    """Create a temporary filename that don't have any '.' inside a part
    from the suffix."""
    tmpfd, tmppath = tempfile.mkstemp(suffix=suffix,
                                      prefix=prefix,
                                      dir=CFG_TMPSHAREDDIR)
    # Close the file and leave the responsability to the client code to
    # correctly open/close it.
    os.close(tmpfd)

    if '.' not in suffix:
        # Just in case format is empty
        return tmppath
    while '.' in os.path.basename(tmppath)[:-len(suffix)]:
        os.remove(tmppath)
        tmpfd, tmppath = tempfile.mkstemp(suffix=suffix,
                                          prefix=prefix,
                                          dir=CFG_TMPSHAREDDIR)
        os.close(tmpfd)
    return tmppath


def open_url(url, headers=None):
    """
    Opens a URL. If headers are passed as argument, no check is performed and
    the URL will be opened.

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
    return URL_OPENER.open(request)
