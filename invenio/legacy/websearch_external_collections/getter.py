# -*- coding: utf-8 -*-

from __future__ import print_function

# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""Module to download web pages using asyncore.

Example 1, downloading a set of webpages :

from invenio.legacy.websearch_external_collections.getter import *
urls = ['http://www.google.fr', 'http://linuxfr.org']
pagegetters = [HTTPAsyncPageGetter(url) for url in urls]
async_download(pagegetters)
for pagegetter in pagegetters:
    if pagegetter.done:
        print pagegetter.data
    else:
        print "Error downloading : " + pagegetter.uri

Example 2, downloading a set of webpages but with callback function.

def func(pagegetter, data, current_time):
    print "OK (%f): " % current_time + pagegetter.uri + " - " + data

from invenio.legacy.websearch_external_collections.getter import *
urls = ['http://www.google.fr', 'http://linuxfr.org']
pagegetters = [HTTPAsyncPageGetter(url) for url in urls]
async_download(pagegetters, func, ['info1', 'info2'], 10)
"""

__revision__ = "$Id$"

import asyncore
import mimetools
import socket
import sys
import StringIO
import time
import urlparse
#from .config import CFG_EXTERNAL_COLLECTION_TIMEOUT
from invenio.config import CFG_WEBSEARCH_EXTERNAL_COLLECTION_SEARCH_TIMEOUT
CFG_EXTERNAL_COLLECTION_TIMEOUT = CFG_WEBSEARCH_EXTERNAL_COLLECTION_SEARCH_TIMEOUT

def async_download(pagegetter_list, finish_function=None, datastructure_list=None, timeout=15, print_search_info=True, print_body=True):
    """Download web pages asynchronously with timeout.
    pagegetter_list : list of HTTPAsyncPageGetter objects
    finish_function : function called when a web page is downloaded;
        prototype def funct(pagetter, datastructure, current_time, print_search_info(optional))
    datastructure_list : list (same size as pagegetter_list) with information to pass as datastructure
        to the finish function.
    timeout : float, timeout in seconds.
    print_search_info: boolean, whether to print the search info or not in the finish function"""
    time_start = time.time()
    finished_list = [False] * len(pagegetter_list)

    nb_remaining = 0
    check_redirected(pagegetter_list)
    for pagegetter in pagegetter_list:
        if pagegetter and not pagegetter.done:
            nb_remaining += 1

    while (time.time() - time_start < timeout) and nb_remaining > 0:
        if sys.hexversion < 0x2040000:
            asyncore.poll(0.01)
        else:
            asyncore.loop(0.01, True, None, 1)
        check_redirected(pagegetter_list)
        for i in range(len(pagegetter_list)):
            if pagegetter_list[i] and not finished_list[i] and pagegetter_list[i].done:
                nb_remaining -= 1
                if finish_function:
                    if datastructure_list:
                        datastructure = datastructure_list[i]
                    else:
                        datastructure = None
                    current_time = time.time() - time_start
                    try:
                        finish_function(pagegetter_list[i], datastructure, current_time, print_search_info, print_body)
                    except TypeError:
                        finish_function(pagegetter_list[i], datastructure, current_time)
                finished_list[i] = True

    return finished_list

class HTTPAsyncPageGetter(asyncore.dispatcher_with_send):
    """Class to download a web page using asyncore."""

    def __init__(self, uri):
        asyncore.dispatcher_with_send.__init__(self)

        self.uri = uri
        self.redirected = None
        self.status = None
        self.header = None
        self.done = False
        self.data = ""
        self.header_data = ""

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.request, self.host, self.port = build_rest_request(self.uri)
        try:
            self.connect((self.host, self.port))
        except:
            self.done = True

    def handle_connect(self):
        """Handle the connection event. By sending the request to the server."""
        try:
            self.send(self.request)
        except socket.error:
            # do nothing because self.done is false by default
            pass

    def handle_expt(self):
        """Handle an exception. Close the socket and put done at True."""
        self.close()
        self.done = True

    def handle_read(self):
        """Handle a read event."""
        data = self.recv(1024)
        if not self.header:
            self.header_data += data
            (self.status, self.header, data) = decode_header(self.header_data)
            if self.status is not None:
                if self.status[1] in ("301", "302"):
                    self.redirected = self.header["location"]
        self.data += data

    def handle_close(self):
        """Handle a close event."""
        self.done = True
        self.close()

    def log_info(self, message, type='info'):
        """
        Workaround broken asyncore log_info method that tries to print
        to stdout.
        """
        print("%s: %s" % (type, message), file=sys.stderr)

def build_rest_request(uri):
    """Build an http request for a specific url."""

    scheme, host, path, params, query, dummy = urlparse.urlparse(uri)
    assert scheme == "http", "only supports HTTP requests (uri = " + uri + ")"

    host, port = decode_host_port(host)
    path = encode_path(path, params, query)

    request = "GET %s HTTP/1.0\r\n" % (path) + \
        "User-Agent: Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/48 (like Gecko) Safari/48\r\n" + \
        "Accept: text/html, image/jpeg, image/png, text/*, image/*, */*\r\n" + \
        "Accept-Charset: utf-8, utf-8;q=0.5, *;q=0.5\r\n" + \
        "Host: %s\r\n" % (host) + \
        "Connection: close\r\n\r\n"

    return (request, host, port)

def decode_host_port(host):
    """Decode the host string in an (host, port) pair."""

    try:
        host, port = host.split(":", 1)
        port = int(port)
    except (TypeError, ValueError):
        port = 80
    return (host, port)

def encode_path(path, params, query):
    """Bind the path, the params and the query in a unique http path."""

    if not path:
        path = "/"
    if params:
        path = path + ";" + params
    if query:
        path = path + "?" + query
    return path

def decode_header(data):
    """Try to decode an html header.

    If the header can be decoded, will return (status, header, remaining_data)
    If it cannot, (None, None, data)
    """
    i = data.find("\r\n\r\n")
    size = 4
    if i == -1:
        i = data.find("\n\n")
        size = 2
        if i == -1:
            return (None, None, data)

    # parse header
    header_fp = StringIO.StringIO(data[:i+size])
    # status line is "HTTP/version status message"
    status = header_fp.readline()
    status = status.split(" ", 2)
    # followed by a rfc822-style message header
    header = mimetools.Message(header_fp)
    # followed by a newline, and the payload (if any)
    data = data[i+size:]

    return (status, header, data)

def check_redirected(pagegetter_list):
    """Check if a redirection occured in the engines_list."""

    for i in range(len(pagegetter_list)):
        getter = pagegetter_list[i]
        if getter and getter.redirected is not None:
            if getter.redirected.startswith('http://'):
                getter = HTTPAsyncPageGetter(getter.redirected)
            else:
                getter.done = True
        pagegetter_list[i] = getter

def fetch_url_content(urls, timeout=CFG_EXTERNAL_COLLECTION_TIMEOUT):
    """Given a list of urls this function returns a list of their contents
    using a optional custom timeout."""

    urls_content = []
    try:
        pagegetters_list = [HTTPAsyncPageGetter(url) for url in urls]
    except AssertionError:
        return [None] * len(urls)
    async_download(pagegetters_list, None, None, timeout)
    for i in range(len(pagegetters_list)):
        if pagegetters_list[i].done: urls_content.append(pagegetters_list[i].data)
        else: urls_content.append(None)
    return urls_content
