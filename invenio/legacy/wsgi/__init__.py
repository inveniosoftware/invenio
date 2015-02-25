# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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

"""mod_python->WSGI Framework"""

import sys
import os
import re
import cgi
import gc
import inspect
import socket
from fnmatch import fnmatch
from six.moves.urllib.parse import urlparse, urlunparse
from six import iteritems
from wsgiref.util import FileWrapper

from invenio.legacy.wsgi.utils import table
from invenio.utils.apache import \
    HTTP_STATUS_MAP, SERVER_RETURN, OK, DONE, \
    HTTP_NOT_FOUND, HTTP_INTERNAL_SERVER_ERROR
from invenio.config import CFG_WEBDIR, CFG_SITE_LANG, \
    CFG_WEBSTYLE_HTTP_STATUS_ALERT_LIST, CFG_DEVEL_SITE, CFG_SITE_URL, \
    CFG_SITE_SECURE_URL, CFG_WEBSTYLE_REVERSE_PROXY_IPS
from invenio.ext.logging import register_exception
from invenio.utils.datastructures import flatten_multidict
# TODO for future reimplementation of stream_file
#from invenio.legacy.bibdocfile.api import StreamFileException
from flask import request, after_this_request


# Magic regexp to search for usage of CFG_SITE_URL within src/href or
# any src usage of an external website
_RE_HTTPS_REPLACES = re.compile(r"\b((?:src\s*=|url\s*\()\s*[\"']?)http\://", re.I)

# Regexp to verify that the IP starts with a number (filter cases where 'unknown')
# It is faster to verify only the start (585 ns) compared with verifying
# the whole ip address - re.compile('^\d+\.\d+\.\d+\.\d+$') (1.01 µs)
_RE_IPADDRESS_START = re.compile("^\d+\.")


def _http_replace_func(match):
    ## src external_site -> CFG_SITE_SECURE_URL/sslredirect/external_site
    return match.group(1) + CFG_SITE_SECURE_URL + '/sslredirect/'

_ESCAPED_CFG_SITE_URL = cgi.escape(CFG_SITE_URL, True)
_ESCAPED_CFG_SITE_SECURE_URL = cgi.escape(CFG_SITE_SECURE_URL, True)


def https_replace(html):
    html = html.decode('utf-8').replace(_ESCAPED_CFG_SITE_URL,
                                        _ESCAPED_CFG_SITE_SECURE_URL)
    return _RE_HTTPS_REPLACES.sub(_http_replace_func, html)


class InputProcessed(object):
    """
    Auxiliary class used when reading input.
    @see: <http://www.wsgi.org/wsgi/Specifications/handling_post_forms>.
    """
    def read(self, *args):
        raise EOFError('The wsgi.input stream has already been consumed')
    readline = readlines = __iter__ = read


from werkzeug import (BaseResponse, ResponseStreamMixin,
                      CommonResponseDescriptorsMixin)


class Response(BaseResponse, ResponseStreamMixin,
               CommonResponseDescriptorsMixin):
    """
    Full featured response object implementing :class:`ResponseStreamMixin`
    to add support for the `stream` property.
    """


class SimulatedModPythonRequest(object):
    """
    mod_python like request object.
    Minimum and cleaned implementation to make moving out of mod_python
    easy.
    @see: <http://www.modpython.org/live/current/doc-html/pyapi-mprequest.html>
    """
    def __init__(self, environ, start_response):
        self.response = Response()
        self.__environ = environ
        self.__start_response = start_response
        self.__response_sent_p = False
        self.__content_type_set_p = False
        self.__buffer = ''
        self.__low_level_headers = []
        self.__filename = None
        self.__disposition_type = None
        self.__bytes_sent = 0
        self.__allowed_methods = []
        self.__cleanups = []
        self.headers_out = {'Cache-Control': None}
        #self.headers_out.update(dict(request.headers))
        ## See: <http://www.python.org/dev/peps/pep-0333/#the-write-callable>
        self.__write = None
        self.__write_error = False
        self.__errors = environ['wsgi.errors']
        self.__headers_in = table([])
        self.__tainted = False
        self.__is_https = self.__environ.get('wsgi.url_scheme') == 'https'
        self.__replace_https = False
        self.track_writings = False
        self.__what_was_written = ""
        self.__cookies_out = {}
        self.g = {} ## global dictionary in case it's needed
        for key, value in iteritems(environ):
            if key.startswith('HTTP_'):
                self.__headers_in[key[len('HTTP_'):].replace('_', '-')] = value
        if environ.get('CONTENT_LENGTH'):
            self.__headers_in['content-length'] = environ['CONTENT_LENGTH']
        if environ.get('CONTENT_TYPE'):
            self.__headers_in['content-type'] = environ['CONTENT_TYPE']

    def get_wsgi_environ(self):
        return self.__environ

    def get_post_form(self):
        """ Returns only POST form. """
        self.__tainted = True
        form = flatten_multidict(request.values)

        if request.files:
            for name, file_ in iteritems(request.files):
                setattr(file_, 'file', file_.stream)
                form[name] = file_
        return form

    def get_response_sent_p(self):
        return self.__response_sent_p

    def get_low_level_headers(self):
        return self.__low_level_headers

    def get_buffer(self):
        return self.__buffer

    def write(self, string, flush=1):
        if isinstance(string, unicode):
            self.__buffer += string.encode('utf8')
        else:
            self.__buffer += string

        if flush:
            self.flush()

    def flush(self):
        self.send_http_header()
        if self.__buffer:
            self.__bytes_sent += len(self.__buffer)
            try:
                if not self.__write_error:
                    if self.__replace_https:
                        self.__write(https_replace(self.__buffer))
                    else:
                        if self.__buffer:
                            self.__write(self.__buffer)
                    if self.track_writings:
                        if self.__replace_https:
                            self.__what_was_written += https_replace(self.__buffer)
                        else:
                            self.__what_was_written += self.__buffer
            except IOError as err:
                if "failed to write data" in str(err) or "client connection closed" in str(err):
                    ## Let's just log this exception without alerting the admin:
                    register_exception(req=self)
                    self.__write_error = True ## This flag is there just
                        ## to not report later other errors to the admin.
                else:
                    raise
            self.__buffer = ''

    def set_content_type(self, content_type):
        self.__content_type_set_p = True
        self.response.content_type = content_type
        if self.__is_https:
            if content_type.startswith("text/html") or content_type.startswith("application/rss+xml"):
                self.__replace_https = True

    def get_content_type(self):
        return self.response.content_type

    def send_http_header(self):
        for (k, v) in self.__low_level_headers:
            self.response.headers[k] = v
        for k, v in iteritems(self.headers_out):
            self.response.headers[k] = v

        self.__write = self.response.stream.write

    def get_unparsed_uri(self):
        return '?'.join([self.__environ['PATH_INFO'], self.__environ['QUERY_STRING']])

    def get_uri(self):
        return request.environ['PATH_INFO']

    def get_full_uri(self):
        if self.is_https():
            return CFG_SITE_SECURE_URL + self.get_unparsed_uri()
        else:
            return CFG_SITE_URL + self.get_unparsed_uri()

    def get_headers_in(self):
        return request.headers

    def get_subprocess_env(self):
        return self.__environ

    def add_common_vars(self):
        pass

    def get_args(self):
        return request.environ['QUERY_STRING']

    def get_remote_ip(self):
        if 'X-FORWARDED-FOR' in self.__headers_in and \
               self.__headers_in.get('X-FORWARDED-SERVER', '') == \
               self.__headers_in.get('X-FORWARDED-HOST', '') == \
               urlparse(CFG_SITE_URL)[1]:
            # we are using proxy setup
            if self.__environ.get('REMOTE_ADDR') in CFG_WEBSTYLE_REVERSE_PROXY_IPS:
                # we trust this proxy
                ip_list = self.__headers_in['X-FORWARDED-FOR'].split(',')
                for ip in ip_list:
                    if _RE_IPADDRESS_START.match(ip):
                        return ip
                # no IP has the correct format, return a default IP
                return '10.0.0.10'
            else:
                # we don't trust this proxy
                register_exception(prefix="You are running in a proxy configuration, but the " + \
                                   "CFG_WEBSTYLE_REVERSE_PROXY_IPS variable does not contain " + \
                                   "the IP of your proxy, thus the remote IP addresses of your " + \
                                   "clients are not trusted.  Please configure this variable.",
                                   alert_admin=True)
                return '10.0.0.11'
        return request.remote_addr

    def get_remote_host(self):
        return request.environ.get('REMOTE_HOST',  # apache
                                   request.environ.get('HTTP_HOST',
                                                       '0.0.0.0'))  # not found

    def get_header_only(self):
        return request.environ['REQUEST_METHOD'] == 'HEAD'

    def set_status(self, status):
        self.response.status_code = status

    def get_status(self):
        return self.response.status_code

    def get_wsgi_status(self):
        return '%s %s' % (self.response.status_code,
                          HTTP_STATUS_MAP.get(int(self.response.status_code),
                                              'Explanation not available'))

    def sendfile(self, path, offset=0, the_len=-1):
        try:
            self.send_http_header()
            file_to_send = open(path)
            file_to_send.seek(offset)
            file_wrapper = FileWrapper(file_to_send)
            count = 0
            if the_len < 0:
                for chunk in file_wrapper:
                    count += len(chunk)
                    self.__bytes_sent += len(chunk)
                    self.__write(chunk)
            else:
                for chunk in file_wrapper:
                    if the_len >= len(chunk):
                        the_len -= len(chunk)
                        count += len(chunk)
                        self.__bytes_sent += len(chunk)
                        self.__write(chunk)
                    else:
                        count += the_len
                        self.__bytes_sent += the_len
                        self.__write(chunk[:the_len])
                        break
        except socket.error as e:
            if e.errno == 54:
                # Client disconnected, ignore
                pass
            else:
                raise
        except IOError as err:
            if "failed to write data" in str(err) or "client connection closed" in str(err):
                ## Let's just log this exception without alerting the admin:
                register_exception(req=self)
            else:
                raise
        return self.__bytes_sent

    def set_content_length(self, content_length):
        if content_length is not None:
            self.response.headers['content-length'] = str(content_length)
        else:
            del self.response.headers['content-length']

    def is_https(self):
        return self.__is_https

    def get_method(self):
        return request.environ['REQUEST_METHOD']

    def get_hostname(self):
        return request.environ.get('HTTP_HOST', '')

    def set_filename(self, filename):
        self.__filename = filename
        if self.__disposition_type is None:
            self.__disposition_type = 'inline'
        self.response.headers['content-disposition'] = '%s; filename=%s' % (self.__disposition_type, self.__filename)

    def set_encoding(self, encoding):
        if encoding:
            self.response.headers['content-encoding'] = str(encoding)
        else:
            del self.response.headers['content-encoding']

    def get_bytes_sent(self):
        return self.__bytes_sent

    def log_error(self, message):
        self.__errors.write(message.strip() + '\n')

    def get_content_type_set_p(self):
        return self.__content_type_set_p and \
            bool(self.response.headers['content-type'])

    def allow_methods(self, methods, reset=0):
        if reset:
            self.__allowed_methods = []
        self.__allowed_methods += [method.upper().strip() for method in methods]

    def get_allowed_methods(self):
        return self.__allowed_methods

    def readline(self, hint=None):
        try:
            return request.stream.readline(hint)
        except TypeError:
            ## the hint param is not part of wsgi pep, although
            ## it's great to exploit it in when reading FORM
            ## with large files, in order to avoid filling up the memory
            ## Too bad it's not there :-(
            return request.stream.readline()

    def readlines(self, hint=None):
        return request.stream.readlines(hint)

    def read(self, hint=None):
        return request.stream.read(hint)

    def register_cleanup(self, callback, data=None):
        @after_this_request
        def f(response):
            callback(data)

    def get_cleanups(self):
        return self.__cleanups

    def get_referer(self):
        return request.referrer

    def get_what_was_written(self):
        return self.__what_was_written

    def __str__(self):
        from pprint import pformat
        out = ""
        for key in dir(self):
            try:
                if not callable(getattr(self, key)) and not key.startswith("_SimulatedModPythonRequest") and not key.startswith('__'):
                    out += 'req.%s: %s\n' % (key, pformat(getattr(self, key)))
            except:
                pass
        return out

    def get_original_wsgi_environment(self):
        """
        Return the original WSGI environment used to initialize this request
        object.
        @return: environ, start_response
        @raise AssertionError: in case the environment has been altered, i.e.
            either the input has been consumed or something has already been
            written to the output.
        """
        assert not self.__tainted, "The original WSGI environment is tainted since at least req.write or req.form has been used."
        return self.__environ, self.__start_response

    def get_environ(self):
        return self.__environ

    environ = property(get_environ)
    content_type = property(get_content_type, set_content_type)
    unparsed_uri = property(get_unparsed_uri)
    uri = property(get_uri)
    full_uri = property(get_full_uri)
    headers_in = property(get_headers_in)
    subprocess_env = property(get_subprocess_env)
    args = property(get_args)
    header_only = property(get_header_only)
    status = property(get_status, set_status)
    method = property(get_method)
    hostname = property(get_hostname)
    filename = property(fset=set_filename)
    encoding = property(fset=set_encoding)
    bytes_sent = property(get_bytes_sent)
    content_type_set_p = property(get_content_type_set_p)
    allowed_methods = property(get_allowed_methods)
    response_sent_p = property(get_response_sent_p)
    form = property(get_post_form)
    remote_ip = property(get_remote_ip)
    remote_host = property(get_remote_host)
    referer = property(get_referer)
    what_was_written = property(get_what_was_written)

def alert_admin_for_server_status_p(status, referer):
    """
    Check the configuration variable
    CFG_WEBSTYLE_HTTP_STATUS_ALERT_LIST to see if the exception should
    be registered and the admin should be alerted.
    """
    status = str(status)
    for pattern in CFG_WEBSTYLE_HTTP_STATUS_ALERT_LIST:
        pattern = pattern.lower()
        must_have_referer = False
        if pattern.endswith('r'):
            ## e.g. "404 r"
            must_have_referer = True
            pattern = pattern[:-1].strip() ## -> "404"
        if fnmatch(status, pattern) and (not must_have_referer or referer):
            return True
    return False

def application(environ, start_response, handler=None):
    """
    Entry point for wsgi.
    """
    ## Needed for mod_wsgi, see: <http://code.google.com/p/modwsgi/wiki/ApplicationIssues>
    req = SimulatedModPythonRequest(environ, start_response)
    #print 'Starting mod_python simulation'

    try:
        if handler is None:
            from invenio.ext.legacy.layout import invenio_handler
            invenio_handler(req)
        else:
            handler(req)
        req.flush()
    ## TODO for future reimplementation of stream_file
    #except StreamFileException as e:
    #    return e.value
    except SERVER_RETURN as status:
        redirection, = status.args
        from werkzeug.wrappers import BaseResponse
        if isinstance(redirection, BaseResponse):
            return redirection
        status = int(str(status))
        if status == 404:
            from werkzeug.exceptions import NotFound
            raise NotFound()
        if status not in (OK, DONE):
            req.status = status
            req.headers_out['content-type'] = 'text/html'
            admin_to_be_alerted = alert_admin_for_server_status_p(status,
                                              req.headers_in.get('referer'))
            if admin_to_be_alerted:
                register_exception(req=req, alert_admin=True)
            if not req.response_sent_p:
                start_response(req.get_wsgi_status(), req.get_low_level_headers(), sys.exc_info())
            map(req.write, generate_error_page(req, admin_to_be_alerted))

        req.flush()

    finally:
        ##for (callback, data) in req.get_cleanups():
        ##    callback(data)
        #if hasattr(req, '_session'):
        #    ## The session handler saves for caching a request_wrapper
        #    ## in req.
        #    ## This saves req as an attribute, creating a circular
        #    ## reference.
        #    ## Since we have have reached the end of the request handler
        #    ## we can safely drop the request_wrapper so to avoid
        #    ## memory leaks.
        #    delattr(req, '_session')
        #if hasattr(req, '_user_info'):
        #    ## For the same reason we can delete the user_info.
        #    delattr(req, '_user_info')

        ## as suggested in
        ## <http://www.python.org/doc/2.3.5/lib/module-gc.html>
        del gc.garbage[:]
    return req.response


def generate_error_page(req, admin_was_alerted=True, page_already_started=False):
    """
    Returns an iterable with the error page to be sent to the user browser.
    """
    from invenio.legacy.webpage import page
    from invenio.legacy import template
    webstyle_templates = template.load('webstyle')
    ln = req.form.get('ln', CFG_SITE_LANG)
    if page_already_started:
        return [webstyle_templates.tmpl_error_page(status=req.get_wsgi_status(), ln=ln, admin_was_alerted=admin_was_alerted)]
    else:
        return [page(title=req.get_wsgi_status(), body=webstyle_templates.tmpl_error_page(status=req.get_wsgi_status(), ln=ln, admin_was_alerted=admin_was_alerted), language=ln, req=req)]

def is_static_path(path):
    """
    Returns True if path corresponds to an exsting file under CFG_WEBDIR.
    @param path: the path.
    @type path: string
    @return: True if path corresponds to an exsting file under CFG_WEBDIR.
    @rtype: bool
    """
    path = os.path.abspath(CFG_WEBDIR + path)
    if path.startswith(CFG_WEBDIR) and os.path.isfile(path):
        return path
    return None

def is_mp_legacy_publisher_path(path):
    """
    Checks path corresponds to an exsting Python file under CFG_WEBDIR.
    @param path: the path.
    @type path: string
    @return: the path of the module to load and the function to call there.
    @rtype: tuple
    """
    from invenio.legacy.registry import webadmin
    path = path.split('/')
    module = ''
    for index, component in enumerate(path):
        if component.endswith('.py'):
            possible_module = webadmin.get(module+component[:-3])
            possible_handler = '/'.join(path[index + 1:]).strip()
            if possible_handler.startswith('_'):
                return None, None
            if not possible_handler:
                possible_handler = 'index'
            if possible_module and os.path.exists(possible_module.__file__):
                return (possible_module.__file__, possible_handler)
        module = component + '/'
    else:
        return None, None

def mp_legacy_publisher(req, possible_module, possible_handler):
    """
    mod_python legacy publisher minimum implementation.
    """
    from invenio.legacy.websession.session import get_session
    from invenio.ext.legacy.handler import CFG_HAS_HTTPS_SUPPORT, CFG_FULL_HTTPS
    if possible_module.endswith('.pyc'):
        possible_module = possible_module[:-1]
    the_module = open(possible_module).read()
    module_globals = {}
    exec(the_module, module_globals)
    if possible_handler in module_globals and callable(module_globals[possible_handler]):
        from invenio.ext.legacy.handler import _check_result
        ## req is the required first parameter of any handler
        expected_args = list(inspect.getargspec(module_globals[possible_handler])[0])
        if not expected_args or 'req' != expected_args[0]:
            ## req was not the first argument. Too bad!
            raise SERVER_RETURN, HTTP_NOT_FOUND
        ## the req.form must be casted to dict because of Python 2.4 and earlier
        ## otherwise any object exposing the mapping interface can be
        ## used with the magic **
        form = dict()
        for key, value in req.form.items():
            ## FIXME: this is a backward compatibility workaround
            ## because most of the old administration web handler
            ## expect parameters to be of type str.
            ## When legacy publisher will be removed all this
            ## pain will go away anyway :-)
            if isinstance(value, unicode):
                form[key] = value.encode('utf8')
            else:
                ## NOTE: this is a workaround for e.g. legacy webupload
                ## that is still using legacy publisher and expect to
                ## have a file (Field) instance instead of a string.
                form[key] = value

        if (CFG_FULL_HTTPS or CFG_HAS_HTTPS_SUPPORT and get_session(req).need_https) and not req.is_https():
            from invenio.utils.url import redirect_to_url
            # We need to isolate the part of the URI that is after
            # CFG_SITE_URL, and append that to our CFG_SITE_SECURE_URL.
            original_parts = urlparse(req.unparsed_uri)
            plain_prefix_parts = urlparse(CFG_SITE_URL)
            secure_prefix_parts = urlparse(CFG_SITE_SECURE_URL)

            # Compute the new path
            plain_path = original_parts[2]
            plain_path = secure_prefix_parts[2] + \
                         plain_path[len(plain_prefix_parts[2]):]

            # ...and recompose the complete URL
            final_parts = list(secure_prefix_parts)
            final_parts[2] = plain_path
            final_parts[-3:] = original_parts[-3:]

            target = urlunparse(final_parts)
            redirect_to_url(req, target)

        try:
            return _check_result(req, module_globals[possible_handler](req, **form))
        except TypeError as err:
            if ("%s() got an unexpected keyword argument" % possible_handler) in str(err) or ('%s() takes at least' % possible_handler) in str(err):
                inspected_args = inspect.getargspec(module_globals[possible_handler])
                expected_args = list(inspected_args[0])
                expected_defaults = list(inspected_args[3])
                expected_args.reverse()
                expected_defaults.reverse()
                register_exception(req=req, prefix="Wrong GET parameter set in calling a legacy publisher handler for %s: expected_args=%s, found_args=%s" % (possible_handler, repr(expected_args), repr(req.form.keys())), alert_admin=CFG_DEVEL_SITE)
                cleaned_form = {}
                for index, arg in enumerate(expected_args):
                    if arg == 'req':
                        continue
                    if index < len(expected_defaults):
                        cleaned_form[arg] = form.get(arg, expected_defaults[index])
                    else:
                        cleaned_form[arg] = form.get(arg, None)
                return _check_result(req, module_globals[possible_handler](req, **cleaned_form))
            else:
                raise
    else:
        raise SERVER_RETURN, HTTP_NOT_FOUND
