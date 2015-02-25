# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2010, 2011 CERN.
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
Exports just one function w3c_validate which validate a text against the W3C validator
"""

__revision__ = "$Id$"

import httplib
import mimetypes
import re
import time
from xml.sax.saxutils import unescape
from invenio.config import CFG_CERN_SITE


if CFG_CERN_SITE:
    # A host mirroring W3C validator
    CFG_W3C_VALIDATOR_HOST = 'pcuds12.cern.ch'

    # The selector for checking the page
    CFG_W3C_VALIDATOR_SELECTOR = '/w3c-markup-validator/check'

    # Whethever to sleep for 1s for kindness to the server
    CFG_W3C_VALIDATOR_SLEEP_P = False
else:
    CFG_W3C_VALIDATOR_HOST = 'validator.w3.org'
    CFG_W3C_VALIDATOR_SELECTOR = '/check'
    CFG_W3C_VALIDATOR_SLEEP_P = True


# Whethever we automatically exploit regression tests for validating pages.
CFG_TESTS_REQUIRE_HTML_VALIDATION = False


def w3c_validate(text, host=CFG_W3C_VALIDATOR_HOST,
        selector=CFG_W3C_VALIDATOR_SELECTOR,
        sleep_p=CFG_W3C_VALIDATOR_SLEEP_P):
    """ Validate the text against W3C validator like host, with a given selector
    and eventually sleeping for a second.
    Return a triple, with True if the document validate as the first element.
    If False, then the second and third elements contain respectively a list of
    errors and of warnings of the form: (line number, column, error, row involved).
    """

    if sleep_p:
        time.sleep(1)
    h = _post_multipart(host, selector, \
        [('output', 'soap12')], [('uploaded_file', 'foobar.html', text)])
    errcode, errmsg, headers = h.getreply()
    if 'X-W3C-Validator-Status' in headers:
        if headers['X-W3C-Validator-Status'] == 'Valid':
            return (True, [], [])
        else:
            errors, warnings = _parse_validator_soap(h.file.read(), text.split('\n'))
            return (False, errors, warnings)
    else:
        return (False, [], [])

def w3c_errors_to_str(errors, warnings):
    """ Pretty print errors and warnings coming from w3c_validate """
    ret = ''
    if errors:
        ret += '%s errors:\n' % len(errors)
        for line, col, msg, text in errors:
            ret += '%s (%s:%s):\n' % (unescape(msg, {'&quot;': "'"}), line, col)
            ret += text + '\n'
            ret += ' '*(int(col)-1) + '^\n'
            ret += '---\n'
    if warnings:
        ret += '%s warnings:\n' % len(warnings)
        for line, col, msg, text in warnings:
            ret += '%s (%s:%s):\n' % (unescape(msg, {'&quot;': "'"}), line, col)
            ret += text + '\n'
            ret += ' '*(int(col)-1) + '^\n'
            ret += '---\n'
    return ret

def w3c_validate_p(text, host=CFG_W3C_VALIDATOR_HOST,
        selector=CFG_W3C_VALIDATOR_SELECTOR,
        sleep_p=CFG_W3C_VALIDATOR_SLEEP_P):
    """ Validate the text against W3C validator like host, with a given selector
    and eventually sleeping for a second.
    Return a True if the document validate.
    """

    if sleep_p:
        time.sleep(1)
    h = _post_multipart(host, selector, \
        [('output', 'soap12')], [('uploaded_file', 'foobar.html', text)])
    errcode, errmsg, headers = h.getreply()
    if 'X-W3C-Validator-Status' in headers:
        return headers['X-W3C-Validator-Status'] == 'Valid'
    return False


_errors_re = re.compile(r'<m:errors>.*<m:errorcount>(?P<errorcount>[\d]+)\</m:errorcount>.*<m:errorlist>(?P<errors>.*)</m:errorlist>.*</m:errors>', re.M | re.S)
_warnings_re = re.compile(r'<m:warnings>.*<m:warningcount>(?P<warningcount>[\d]+)</m:warningcount>.*<m:warninglist>(?P<warnings>.*)</m:warninglist>.*</m:warnings>', re.M | re.S)

_error_re = re.compile(r'<m:error>.*<m:line>(?P<line>[\d]+)</m:line>.*<m:col>(?P<col>[\d]+)</m:col>.*<m:message>(?P<message>.+)</m:message>.*</m:error>', re.M | re.S)

_warning_re = re.compile(r'<m:warning>.*<m:line>(?P<line>[\d]+)</m:line>.*<m:col>(?P<col>[\d]+)</m:col>.*<m:message>(?P<message>.+)</m:message>.*</m:warning>', re.M | re.S)


def _parse_validator_soap(soap_output, rows):
    """ Given the soap output provided by W3C validator it returns a tuple
    containing the list of errors in the form (line, col, error_msg) and
    the list of warnings in the same form.
    """

    errors = _errors_re.search(soap_output)
    warnings = _warnings_re.search(soap_output)
    if errors:
        errors = _error_re.findall(errors.group('errors'))
        errors = map(lambda error: (error[0], error[1], error[2], rows[int(error[0])-1]), errors)
    else:
        errors = []
    if warnings:
        warnings = _warning_re.findall(warnings.group('warnings'))
        warnings = map(lambda warning: (warning[0], warning[1], warning[2], rows[int(warning[0])-1]), warnings)
    else:
        warnings = []
    return (errors, warnings)

def _post_multipart(host, selector, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's responses.
    """
    content_type, body = _encode_multipart_formdata(fields, files)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    return h

def _encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % _get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def _get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

