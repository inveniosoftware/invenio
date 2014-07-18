# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2012 CERN.
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

"""mod_python->WSGI Framework"""

import sys
import os
import re
import cgi
import gc
import inspect
import socket
from fnmatch import fnmatch
from urlparse import urlparse, urlunparse

from wsgiref.validate import validator
from wsgiref.util import FileWrapper

if __name__ != "__main__":
    # Chances are that we are inside mod_wsgi.
    ## You can't write to stdout in mod_wsgi, but some of our
    ## dependecies do this! (e.g. 4Suite)
    sys.stdout = sys.stderr

from invenio.urlutils import redirect_to_url
from invenio.session import get_session
from invenio.webinterface_handler import (CFG_HAS_HTTPS_SUPPORT,
                                          CFG_FULL_HTTPS,
                                          ClientDisconnected)
from invenio.webinterface_layout import invenio_handler
from invenio.webinterface_handler_wsgi_utils import table, FieldStorage
from invenio.webinterface_handler_config import \
    HTTP_STATUS_MAP, SERVER_RETURN, OK, DONE, \
    HTTP_NOT_FOUND, HTTP_INTERNAL_SERVER_ERROR
from invenio.config import CFG_WEBDIR, CFG_SITE_LANG, \
    CFG_WEBSTYLE_HTTP_STATUS_ALERT_LIST, CFG_DEVEL_SITE, CFG_SITE_URL, \
    CFG_SITE_SECURE_URL, CFG_WEBSTYLE_REVERSE_PROXY_IPS
from invenio.errorlib import register_exception, get_pretty_traceback

## Static files are usually handled directly by the webserver (e.g. Apache)
## However in case WSGI is required to handle static files too (such
## as when running wsgiref simple server), then this flag can be
## turned on (it is done automatically by wsgi_handler_test).
CFG_WSGI_SERVE_STATIC_FILES = False


## Magic regexp to search for usage of CFG_SITE_URL within src/href or
## any src usage of an external website
_RE_HTTPS_REPLACES = re.compile(r"\b((?:src\s*=|url\s*\()\s*[\"']?)http\://", re.I)

## Regexp to verify that the IP starts with a number (filter cases where 'unknown')
## It is faster to verify only the start (585 ns) compared with verifying
## the whole ip address - re.compile('^\d+\.\d+\.\d+\.\d+$') (1.01 µs)
_RE_IPADDRESS_START = re.compile(r"^\d+\.")

## Regexp to match IE User-Agent
_RE_BAD_MSIE = re.compile(r"MSIE\s+(\d+\.\d+)")


def _http_replace_func(match):
    ## src external_site -> CFG_SITE_SECURE_URL/sslredirect/external_site
    return match.group(1) + CFG_SITE_SECURE_URL + '/sslredirect/'

_ESCAPED_CFG_SITE_URL = cgi.escape(CFG_SITE_URL, True)
_ESCAPED_CFG_SITE_SECURE_URL = cgi.escape(CFG_SITE_SECURE_URL, True)
def https_replace(html):
    html = html.replace(_ESCAPED_CFG_SITE_URL, _ESCAPED_CFG_SITE_SECURE_URL)
    return _RE_HTTPS_REPLACES.sub(_http_replace_func, html)


class InputProcessed(object):
    """
    Auxiliary class used when reading input.
    @see: <http://www.wsgi.org/wsgi/Specifications/handling_post_forms>.
    """
    def read(self, *args):
        raise EOFError('The wsgi.input stream has already been consumed')
    readline = readlines = __iter__ = read

class SimulatedModPythonRequest(object):
    """
    mod_python like request object.
    Minimum and cleaned implementation to make moving out of mod_python
    easy.
    @see: <http://www.modpython.org/live/current/doc-html/pyapi-mprequest.html>
    """
    def __init__(self, environ, start_response):
        self.__environ = environ
        self.__start_response = start_response
        self.__response_sent_p = False
        self.__buffer = ''
        self.__low_level_headers = []
        self.__headers = table(self.__low_level_headers)
        self.__headers.add = self.__headers.add_header
        self.__status = "200 OK"
        self.__filename = None
        self.__disposition_type = None
        self.__bytes_sent = 0
        self.__allowed_methods = []
        self.__cleanups = []
        self.headers_out = self.__headers
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
        for key, value in environ.iteritems():
            if key.startswith('HTTP_'):
                self.__headers_in[key[len('HTTP_'):].replace('_', '-')] = value
        if environ.get('CONTENT_LENGTH'):
            self.__headers_in['content-length'] = environ['CONTENT_LENGTH']
        if environ.get('CONTENT_TYPE'):
            self.__headers_in['content-type'] = environ['CONTENT_TYPE']

    def set_cookie(self, cookie):
        """
        This function is used to cumulate identical cookies.
        """
        self.__cookies_out[cookie.name] = cookie

    def _write_cookies(self):
        if self.__cookies_out:
            if not self.headers_out.has_key("Set-Cookie"):
                g = _RE_BAD_MSIE.search(self.headers_in.get('User-Agent', "MSIE 6.0"))
                bad_msie = g and float(g.group(1)) < 9.0
                if not (bad_msie and self.is_https()):
                    self.headers_out.add("Cache-Control", 'no-cache="set-cookie"')
            for cookie in self.__cookies_out.values():
                self.headers_out.add("Set-Cookie", str(cookie))

    def get_wsgi_environ(self):
        return self.__environ

    def get_post_form(self):
        self.__tainted = True
        post_form = self.__environ.get('wsgi.post_form')
        input = self.__environ['wsgi.input']
        if (post_form is not None
            and post_form[0] is input):
            return post_form[2]
        # This must be done to avoid a bug in cgi.FieldStorage
        self.__environ.setdefault('QUERY_STRING', '')

        ## Video handler hack:
        uri = self.__environ['PATH_INFO']
        if uri.endswith("upload_video"):
            tmp_shared = True
        else:
            tmp_shared = False
        fs = FieldStorage(self, keep_blank_values=1, to_tmp_shared=tmp_shared)
        if fs.wsgi_input_consumed:
            new_input = InputProcessed()
            post_form = (new_input, input, fs)
            self.__environ['wsgi.post_form'] = post_form
            self.__environ['wsgi.input'] = new_input
        else:
            post_form = (input, None, fs)
            self.__environ['wsgi.post_form'] = post_form
        return fs

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
                        self.__write(self.__buffer)
                    if self.track_writings:
                        if self.__replace_https:
                            self.__what_was_written += https_replace(self.__buffer)
                        else:
                            self.__what_was_written += self.__buffer
            except IOError, err:
                if "failed to write data" in str(err) or "client connection closed" in str(err):
                    # The Client disconnected, just ignore the exception
                    if self.method == 'GET':
                        raise ClientDisconnected()
                else:
                    raise
            self.__buffer = ''

    def set_content_type(self, content_type):
        self.__headers['content-type'] = content_type
        if self.__is_https:
            if content_type.startswith("text/html") or content_type.startswith("application/rss+xml"):
                self.__replace_https = True

    def get_content_type(self):
        return self.__headers['content-type']

    def send_http_header(self):
        if not self.__response_sent_p:
            self._write_cookies()
            self.__tainted = True
            if self.__allowed_methods and self.__status.startswith('405 ') or self.__status.startswith('501 '):
                self.__headers['Allow'] = ', '.join(self.__allowed_methods)

            ## See: <http://www.python.org/dev/peps/pep-0333/#the-write-callable>
            #print self.__low_level_headers
            self.__write = self.__start_response(self.__status, self.__low_level_headers)
            self.__response_sent_p = True
            #print "Response sent: %s" % self.__headers

    def get_unparsed_uri(self):
        return '?'.join([self.__environ['PATH_INFO'], self.__environ['QUERY_STRING']])

    def get_uri(self):
        return self.__environ['PATH_INFO']

    def get_headers_in(self):
        return self.__headers_in

    def get_subprocess_env(self):
        return self.__environ

    def add_common_vars(self):
        pass

    def get_args(self):
        return self.__environ['QUERY_STRING']

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
        return self.__environ.get('REMOTE_ADDR')

    def get_remote_host(self):
        return self.__environ.get('REMOTE_HOST')

    def get_header_only(self):
        return self.__environ['REQUEST_METHOD'] == 'HEAD'

    def set_status(self, status):
        self.__status = '%s %s' % (status, HTTP_STATUS_MAP.get(int(status), 'Explanation not available'))

    def get_status(self):
        return int(self.__status.split(' ')[0])

    def get_wsgi_status(self):
        return self.__status

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
        except socket.error, e:
            if e.errno == 54:
                # Client disconnected, ignore
                pass
            else:
                raise
        except IOError, err:
            if "failed to write data" in str(err) or "client connection closed" in str(err):
                ## Let's just log this exception without alerting the admin:
                register_exception(req=self)
            else:
                raise
        return self.__bytes_sent

    def set_content_length(self, content_length):
        if content_length is not None:
            self.__headers['content-length'] = str(content_length)
        else:
            del self.__headers['content-length']

    def is_https(self):
        return self.__is_https

    def get_method(self):
        return self.__environ['REQUEST_METHOD']

    def get_hostname(self):
        return self.__environ.get('HTTP_HOST', '')

    def set_filename(self, filename):
        self.__filename = filename
        if self.__disposition_type is None:
            self.__disposition_type = 'inline'
        self.__headers['content-disposition'] = '%s; filename=%s' % (self.__disposition_type, self.__filename)

    def set_encoding(self, encoding):
        if encoding:
            self.__headers['content-encoding'] = str(encoding)
        else:
            del self.__headers['content-encoding']

    def get_bytes_sent(self):
        return self.__bytes_sent

    def log_error(self, message):
        self.__errors.write(message.strip() + '\n')

    def get_content_type_set_p(self):
        return bool(self.__headers['content-type'])

    def allow_methods(self, methods, reset=0):
        if reset:
            self.__allowed_methods = []
        self.__allowed_methods += [method.upper().strip() for method in methods]

    def get_allowed_methods(self):
        return self.__allowed_methods

    def readline(self, hint=None):
        try:
            return self.__environ['wsgi.input'].readline(hint)
        except TypeError:
            ## the hint param is not part of wsgi pep, although
            ## it's great to exploit it in when reading FORM
            ## with large files, in order to avoid filling up the memory
            ## Too bad it's not there :-(
            return self.__environ['wsgi.input'].readline()

    def readlines(self, hint=None):
        return self.__environ['wsgi.input'].readlines(hint)

    def read(self, hint=None):
        return self.__environ['wsgi.input'].read(hint)

    def register_cleanup(self, callback, data=None):
        self.__cleanups.append((callback, data))

    def get_cleanups(self):
        return self.__cleanups

    def get_referer(self):
        return self.headers_in.get('referer')

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

def application(environ, start_response):
    """
    Entry point for wsgi.
    """
    ## Needed for mod_wsgi, see: <http://code.google.com/p/modwsgi/wiki/ApplicationIssues>
    req = SimulatedModPythonRequest(environ, start_response)
    #print 'Starting mod_python simulation'

    try:
        if (CFG_FULL_HTTPS or (CFG_HAS_HTTPS_SUPPORT and get_session(req).need_https)) and not req.is_https():
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

        possible_module, possible_handler = is_mp_legacy_publisher_path(environ['PATH_INFO'])
        if possible_module is not None:
            mp_legacy_publisher(req, possible_module, possible_handler)
        elif CFG_WSGI_SERVE_STATIC_FILES:
            possible_static_path = is_static_path(environ['PATH_INFO'])
            if possible_static_path is not None:
                from invenio.bibdocfile import stream_file
                stream_file(req, possible_static_path)
            else:
                ret = invenio_handler(req)
        else:
            ret = invenio_handler(req)
        req.flush()
    except SERVER_RETURN, status:
        status = int(str(status))
        if status not in (OK, DONE):
            req.status = status
            req.headers_out['content-type'] = 'text/html'
            admin_to_be_alerted = alert_admin_for_server_status_p(status,
                                              req.headers_in.get('referer'))
            if admin_to_be_alerted:
                register_exception(req=req, alert_admin=True)
            if not req.response_sent_p:
                start_response(req.get_wsgi_status(), req.get_low_level_headers(), sys.exc_info())
            return generate_error_page(req, admin_to_be_alerted)
        else:
            req.flush()
    except ClientDisconnected:
        pass
    except:
        register_exception(req=req, alert_admin=True)
        if not req.response_sent_p:
            req.status = HTTP_INTERNAL_SERVER_ERROR
            req.headers_out['content-type'] = 'text/html'
            start_response(req.get_wsgi_status(), req.get_low_level_headers(), sys.exc_info())
            if CFG_DEVEL_SITE:
                return ["<pre>%s</pre>" % cgi.escape(get_pretty_traceback(req=req, exc_info=sys.exc_info()))]
                from cgitb import html
                return [html(sys.exc_info())]
            return generate_error_page(req)
        else:
            return generate_error_page(req, page_already_started=True)
    finally:
        try:
            ## Let's save the session.
            session = get_session(req)
            try:
                if req.is_https() or not session.need_https:
                    ## We save the session only if it's safe to do it, i.e.
                    ## if we well had a valid session.
                    session.dirty = True
                    session.save()
                if 'user_info' in req._session:
                    del req._session['user_info']
            finally:
                del session
        except Exception:
            ## What could have gone wrong?
            register_exception(req=req, alert_admin=True)
        if hasattr(req, '_session'):
            ## The session handler saves for caching a request_wrapper
            ## in req.
            ## This saves req as an attribute, creating a circular
            ## reference.
            ## Since we have have reached the end of the request handler
            ## we can safely drop the request_wrapper so to avoid
            ## memory leaks.
            delattr(req, '_session')
        if hasattr(req, '_user_info'):
            ## For the same reason we can delete the user_info.
            delattr(req, '_user_info')

        for (callback, data) in req.get_cleanups():
            callback(data)

    return []

def generate_error_page(req, admin_was_alerted=True, page_already_started=False):
    """
    Returns an iterable with the error page to be sent to the user browser.
    """
    from invenio.webpage import page
    from invenio import template
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
    path = path.split('/')
    for index, component in enumerate(path):
        if component.endswith('.py'):
            possible_module = os.path.abspath(CFG_WEBDIR + os.path.sep + os.path.sep.join(path[:index + 1]))
            possible_handler = '/'.join(path[index + 1:]).strip()
            if possible_handler.startswith('_'):
                return None, None
            if not possible_handler:
                possible_handler = 'index'
            if os.path.exists(possible_module) and possible_module.startswith(CFG_WEBDIR):
                return (possible_module, possible_handler)
    else:
        return None, None

def mp_legacy_publisher(req, possible_module, possible_handler):
    """
    mod_python legacy publisher minimum implementation.
    """
    the_module = open(possible_module).read()
    module_globals = {}
    exec(the_module, module_globals)
    if possible_handler in module_globals and callable(module_globals[possible_handler]):
        from invenio.webinterface_handler import _check_result
        ## req is the required first parameter of any handler
        expected_args = list(inspect.getargspec(module_globals[possible_handler])[0])
        if not expected_args or 'req' != expected_args[0]:
            ## req was not the first argument. Too bad!
            raise SERVER_RETURN, HTTP_NOT_FOUND
        ## the req.form must be casted to dict because of Python 2.4 and earlier
        ## otherwise any object exposing the mapping interface can be
        ## used with the magic **
        form = dict(req.form)
        for key, value in form.items():
            ## FIXME: this is a backward compatibility workaround
            ## because most of the old administration web handler
            ## expect parameters to be of type str.
            ## When legacy publisher will be removed all this
            ## pain will go away anyway :-)
            if isinstance(value, str):
                form[key] = str(value)
            else:
                ## NOTE: this is a workaround for e.g. legacy webupload
                ## that is still using legacy publisher and expect to
                ## have a file (Field) instance instead of a string.
                form[key] = value

        if (CFG_FULL_HTTPS or CFG_HAS_HTTPS_SUPPORT and get_session(req).need_https) and not req.is_https():
            from invenio.urlutils import redirect_to_url
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
        except TypeError, err:
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

def check_wsgiref_testing_feasability():
    """
    In order to use wsgiref for running Invenio, CFG_SITE_URL and
    CFG_SITE_SECURE_URL must not use HTTPS because SSL is not supported.
    """
    if CFG_SITE_URL.lower().startswith('https'):
        print >> sys.stderr, """
ERROR: SSL is not supported by the wsgiref simple server implementation.
Please set CFG_SITE_URL not to start with "https".
Currently CFG_SITE_URL is set to: "%s".""" % CFG_SITE_URL
        sys.exit(1)
    if CFG_SITE_SECURE_URL.lower().startswith('https'):
        print >> sys.stderr, """
ERROR: SSL is not supported by the wsgiref simple server implementation.
Please set CFG_SITE_SECURE_URL not to start with "https".
Currently CFG_SITE_SECURE_URL is set to: "%s".""" % CFG_SITE_SECURE_URL
        sys.exit(1)

def wsgi_handler_test(port=80):
    """
    Simple WSGI testing environment based on wsgiref.
    """
    from wsgiref.simple_server import make_server
    global CFG_WSGI_SERVE_STATIC_FILES
    CFG_WSGI_SERVE_STATIC_FILES = True
    check_wsgiref_testing_feasability()
    validator_app = validator(application)
    httpd = make_server('', port, validator_app)
    print "Serving on port %s..." % port
    httpd.serve_forever()

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-t', '--test', action='store_true',
                      dest='test', default=False,
                      help="Run a WSGI test server via wsgiref (not using Apache).")
    parser.add_option('-p', '--port', type='int', dest='port', default='80',
                      help="The port where the WSGI test server will listen. [80]")
    (options, args) = parser.parse_args()
    if options.test:
        wsgi_handler_test(options.port)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
