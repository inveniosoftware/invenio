# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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
Apache request handler mechanism.

It gives the tools to map url to functions, handles the legacy url
scheme (/search.py queries), HTTP/HTTPS switching, language
specification,...
"""

__revision__ = "$Id$"

## Import the remote debugger as a first thing, if allowed
try:
    import invenio.remote_debugger as remote_debugger
except:
    remote_debugger = None

import urlparse
import cgi
import sys
import re
import os
import gc

from invenio import webinterface_handler_config as apache
from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL, CFG_TMPDIR, \
    CFG_SITE_RECORD, CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.messages import wash_language
from invenio.urlutils import redirect_to_url
from invenio.errorlib import register_exception
from invenio.webuser import get_preferred_user_language, isGuestUser, \
    getUid, isUserSuperAdmin, collect_user_info, setUid
from invenio.webinterface_handler_wsgi_utils import StringField
from invenio.session import get_session
from invenio import web_api_key
from invenio.access_control_engine import acc_authorize_action


## The following variable is True if the installation make any difference
## between HTTP Vs. HTTPS connections.
CFG_HAS_HTTPS_SUPPORT = CFG_SITE_SECURE_URL.startswith("https://")

## The following variable is True if HTTPS is used for *any* URL.
CFG_FULL_HTTPS = CFG_SITE_URL.lower().startswith("https://")


## Set this to True in order to log some more information.
DEBUG = False

# List of URIs for which the 'ln' argument must not be added
# automatically
CFG_NO_LANG_RECOGNITION_URIS = ['/rss',
                                '/oai2d',
                                '/journal']


RE_SLASHES = re.compile('/+')
RE_SPECIAL_URI = re.compile('^/%s/\d+|^/collection/.+' % CFG_SITE_RECORD)

_RE_BAD_MSIE = re.compile("MSIE\s+(\d+\.\d+)")


def _debug(req, msg):
    """
    Log the message.

    @param req: the request.
    @param msg: the message.
    @type msg: string
    """
    if DEBUG:
        req.log_error(msg)


def _check_result(req, result):
    """
    Check that a page handler actually wrote something, and
    properly finish the apache request.

    @param req: the request.
    @param result: the produced output.
    @type result: string
    @return: an apache error code
    @rtype: int
    @raise apache.SERVER_RETURN: in case of a HEAD request.
    @note: that this function actually takes care of writing the result
        to the client.
    """

    if result or req.bytes_sent > 0:

        if result is None:
            result = ""
        else:
            result = str(result)

        # unless content_type was manually set, we will attempt
        # to guess it
        if not req.content_type_set_p:
            # make an attempt to guess content-type
            if result[:100].strip()[:6].lower() == '<html>' \
               or result.find('</') > 0:
                req.content_type = 'text/html'
            else:
                req.content_type = 'text/plain'

        if req.header_only:
            if req.status in (apache.HTTP_NOT_FOUND, ):
                raise apache.SERVER_RETURN, req.status
        else:
            req.write(result)

        return apache.OK

    else:
        req.log_error("publisher: %s returned nothing." % `object`)
        return apache.HTTP_INTERNAL_SERVER_ERROR


class TraversalError(Exception):
    """
    Exception raised in case of an error in parsing the URL of the request.
    """
    pass


class WebInterfaceDirectory(object):
    """
    A directory groups web pages, and can delegate dispatching of
    requests to the actual handler. This has been heavily borrowed
    from Quixote's dispatching mechanism, with specific adaptations.
    """

    # Lists the valid URLs contained in this directory.
    _exports = []

    # Set this to True in order to redirect queries over HTTPS
    _force_https = False

    def _translate(self, component):
        """(component : string) -> string | None

        Translate a path component into a Python identifier.  Returning
        None signifies that the component does not exist.
        """
        if component in self._exports:
            if component == '':
                return 'index' # implicit mapping
            else:
                return component
        else:
            # check for an explicit external to internal mapping
            for value in self._exports:
                if isinstance(value, tuple):
                    if value[0] == component:
                        return value[1]
            else:
                return None

    def _lookup(self, component, path):
        """ Override this method if you need to map dynamic URLs.

        It can eat up as much of the remaining path as needed, and
        return the remaining parts, so that the traversal can
        continue.
        """
        return None, path

    def _traverse(self, req, path, do_head=False, guest_p=True):
        """ Locate the handler of an URI by traversing the elements of
        the path."""

        _debug(req, 'traversing %r' % path)

        component, path = path[0], path[1:]

        name = self._translate(component)

        if name is None:
            obj, path = self._lookup(component, path)
        else:
            obj = getattr(self, name)

        if obj is None:
            _debug(req, 'could not resolve %s' % repr((component, path)))
            raise TraversalError()

        # We have found the next segment. If we know that from this
        # point our subpages are over HTTPS, do the switch.

        if (CFG_FULL_HTTPS or CFG_HAS_HTTPS_SUPPORT and (self._force_https or get_session(req).need_https)) and not req.is_https():
            # We need to isolate the part of the URI that is after
            # CFG_SITE_URL, and append that to our CFG_SITE_SECURE_URL.
            original_parts = urlparse.urlparse(req.unparsed_uri)
            plain_prefix_parts = urlparse.urlparse(CFG_SITE_URL)
            secure_prefix_parts = urlparse.urlparse(CFG_SITE_SECURE_URL)

            # Compute the new path
            plain_path = original_parts[2]
            plain_path = secure_prefix_parts[2] + \
                         plain_path[len(plain_prefix_parts[2]):]

            # ...and recompose the complete URL
            final_parts = list(secure_prefix_parts)
            final_parts[2] = plain_path
            final_parts[-3:] = original_parts[-3:]

            target = urlparse.urlunparse(final_parts)
            ## The following condition used to allow certain URLs to
            ## by-pass the forced SSL redirect. Since SSL certificates
            ## are deployed on INSPIRE, this is no longer needed
            ## Will be left here for reference.
            #from invenio.config import CFG_INSPIRE_SITE
            #if not CFG_INSPIRE_SITE or plain_path.startswith('/youraccount/login'):
            redirect_to_url(req, target)

        # Continue the traversal. If there is a path, continue
        # resolving, otherwise call the method as it is our final
        # renderer. We even pass it the parsed form arguments.
        if path:
            if hasattr(obj, '_traverse'):
                return obj._traverse(req, path, do_head, guest_p)
            else:
                raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

        if do_head:
            req.content_type = "text/html; charset=UTF-8"
            raise apache.SERVER_RETURN, apache.DONE

        form = req.form
        if 'ln' not in form and \
                req.uri not in CFG_NO_LANG_RECOGNITION_URIS:
            ln = get_preferred_user_language(req)
            form.add_field('ln', ln)
        result = _check_result(req, obj(req, form))
        return result

    def __call__(self, req, form):
        """ Maybe resolve the final / of a directory """

        # When this method is called, we either are a directory which
        # has an 'index' method, and we redirect to it, or we don't
        # have such a method, in which case it is a traversal error.

        if "" in self._exports:
            if not form:
                # Fix missing trailing slash as a convenience, unless
                # we are processing a form (in which case it is better
                # to fix the form posting).
                redirect_to_url(req, req.uri + "/", apache.HTTP_MOVED_PERMANENTLY)

        _debug(req, 'directory %r is not callable' % self)
        raise TraversalError()


def create_handler(root):
    """ Return a handler function that will dispatch apache requests
    through the URL layout passed in parameter."""

    def _profiler(req):
        """ This handler wrap the default handler with a profiler.
        Profiling data is written into
        CFG_TMPDIR/invenio-profile-stats-datetime.raw, and
        is displayed at the bottom of the webpage.
        To use add profile=1 to your url. To change sorting algorithm you
        can provide profile=algorithm_name. You can add more than one
        profile requirement like ?profile=time&profile=cumulative.
        The list of available algorithm is displayed at the end of the profile.
        """
        args = {}
        if req.args:
            args = cgi.parse_qs(req.args)

        user_info = collect_user_info(req)

        # Permissions to run the profiler?
        if acc_authorize_action(user_info, 'profiling')[0]:
            return _handler(req)

        if user_info.get('enable_profiling') and 'profile' not in args:
            args['profile'] = 'cumulative'

        # Profiler enabled?
        if 'profile' in args:

            if 'memory' in args.get('profile', []):
                gc.set_debug(gc.DEBUG_LEAK)
                ret = _handler(req)
                req.write("\n<pre>%s</pre>" % gc.garbage)
                gc.collect()
                req.write("\n<pre>%s</pre>" % gc.garbage)
                gc.set_debug(0)
                return ret

            from cStringIO import StringIO
            try:
                import pstats
            except ImportError:
                ret = _handler(req)
                req.write("<pre>%s</pre>" % "The Python Profiler is not installed!")
                return ret
            import datetime
            date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            filename = '%s/invenio-profile-stats-%s.raw' % (CFG_TMPDIR, date)
            existing_sorts = pstats.Stats.sort_arg_dict_default.keys()
            required_sorts = []
            profile_dump = []
            for sort in args['profile']:
                if sort not in existing_sorts:
                    sort = 'cumulative'
                if sort not in required_sorts:
                    required_sorts.append(sort)
            if sys.hexversion < 0x02050000:
                import hotshot
                import hotshot.stats
                pr = hotshot.Profile(filename)
                ret = pr.runcall(_handler, req)
                for sort_type in required_sorts:
                    tmp_out = sys.stdout
                    sys.stdout = StringIO()
                    hotshot.stats.load(filename).strip_dirs().sort_stats(sort_type).print_stats()
                    # pylint: disable=E1103
                    # This is a hack. sys.stdout was replaced by a StringIO.
                    profile_dump.append(sys.stdout.getvalue())
                    # pylint: enable=E1103
                    sys.stdout = tmp_out
            else:
                import cProfile
                pr = cProfile.Profile()
                ret = pr.runcall(_handler, req)
                for sort_type in required_sorts:
                    strstream = StringIO()
                    pstats.Stats(pr, stream=strstream).strip_dirs().sort_stats(sort_type).print_stats()
                    profile_dump.append(strstream.getvalue())
            profile_dump = '\n'.join(profile_dump)
            profile_dump += '\nYou can use profile=%s or profile=memory' % existing_sorts
            req.write("\n<pre>%s</pre>" % profile_dump)
            return ret
        elif 'debug' in args and args['debug']:
            #remote_debugger.start(["3"]) # example starting debugger on demand
            if remote_debugger:
                debug_starter = remote_debugger.get_debugger(args['debug'])
                if debug_starter:
                    try:
                        debug_starter()
                    except Exception, msg:
                        # TODO - should register_exception?
                        raise Exception('Cannot start the debugger %s, please read instructions inside remote_debugger module. %s' % (debug_starter.__name__, msg))
                else:
                    raise Exception('Debugging requested, but no debugger registered: "%s"' % args['debug'])
            return _handler(req)
        else:
            return _handler(req)

    def _handler(req):
        """ This handler is invoked by mod_python with the apache request."""
        allowed_methods = ("GET", "POST", "HEAD", "OPTIONS", "PUT")
        req.allow_methods(allowed_methods, 1)
        if req.method not in allowed_methods:
            raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

        if req.method == 'OPTIONS':
            ## OPTIONS is used to now which method are allowed
            req.headers_out['Allow'] = ', '.join(allowed_methods)
            raise apache.SERVER_RETURN, apache.OK

        # Set user agent for fckeditor.py, which needs it here
        os.environ["HTTP_USER_AGENT"] = req.headers_in.get('User-Agent', '')

        # Check if REST authentication can be performed
        if req.args:
            args = cgi.parse_qs(req.args)
            if 'apikey' in args and req.is_https():
                uid = web_api_key.acc_get_uid_from_request(req.uri, req.args)
                if uid < 0:
                    raise apache.SERVER_RETURN, apache.HTTP_UNAUTHORIZED
                else:
                    setUid(req=req, uid=uid)

        guest_p = isGuestUser(getUid(req), run_on_slave=False)

        uri = req.uri
        if uri == '/':
            path = ['']
        else:
            ## Let's collapse multiple slashes into a single /
            uri = RE_SLASHES.sub('/', uri)
            path = uri[1:].split('/')

        if CFG_ACCESS_CONTROL_LEVEL_SITE > 1:
            ## If the site is under maintainance mode let's return
            ## 503 to casual crawler to avoid having the site being
            ## indexed
            req.status = 503

        g = _RE_BAD_MSIE.search(req.headers_in.get('User-Agent', "MSIE 6.0"))
        bad_msie = g and float(g.group(1)) < 9.0
        if uri.startswith('/yours') or not guest_p:
            ## Private/personalized request should not be cached
            if bad_msie and req.is_https():
                req.headers_out['Cache-Control'] = 'private, max-age=0, must-revalidate'
            else:
                req.headers_out['Cache-Control'] = 'private, no-cache, no-store, max-age=0, must-revalidate'
                req.headers_out['Pragma'] = 'no-cache'
                req.headers_out['Vary'] = '*'
        elif not (bad_msie and req.is_https()):
            req.headers_out['Cache-Control'] = 'public, max-age=3600'
            req.headers_out['Vary'] = 'Cookie, ETag, Cache-Control'

        try:
            if req.header_only and not RE_SPECIAL_URI.match(req.uri):
                return root._traverse(req, path, True, guest_p)
            else:
                ## bibdocfile have a special treatment for HEAD
                return root._traverse(req, path, False, guest_p)
        except TraversalError:
            raise apache.SERVER_RETURN(apache.HTTP_NOT_FOUND)
        except apache.SERVER_RETURN:
            ## This is one of mod_python way of communicating
            raise
        except IOError, exc:
            if not ('Write failed, client closed connection' in str(exc) or 'request data read error' in str(exc)):
                ## Workaround for considering as false positive exceptions
                ## rised by mod_python when the user close the connection
                ## or in some other rare and not well identified cases.
                register_exception(req=req, alert_admin=True)
                raise
            else:
                raise apache.SERVER_RETURN(apache.HTTP_BAD_REQUEST)
        except Exception:
            # send the error message, much more convenient than log hunting
            if remote_debugger:
                args = {}
                if req.args:
                    args = cgi.parse_qs(req.args)
                    if 'debug' in args:
                        remote_debugger.error_msg(args['debug'])
            register_exception(req=req, alert_admin=True)
            raise

        # Serve an error by default.
        raise apache.SERVER_RETURN(apache.HTTP_NOT_FOUND)
    return _profiler


def wash_urlargd(form, content):
    """
    Wash the complete form based on the specification in
    content. Content is a dictionary containing the field names as a
    key, and a tuple (type, default) as value.

    'type' can be list, str, invenio.webinterface_handler_wsgi_utils.StringField, int, tuple, or
    invenio.webinterface_handler_wsgi_utils.Field (for
    file uploads).

    The specification automatically includes the 'ln' field, which is
    common to all queries.

    Arguments that are not defined in 'content' are discarded.

    Note that in case {list,tuple} were asked for, we assume that
    {list,tuple} of strings is to be returned.  Therefore beware when
    you want to use wash_urlargd() for multiple file upload forms.

    @Return: argd dictionary that can be used for passing function
    parameters by keywords.
    """

    result = {}

    content['ln'] = (str, '')

    for k, (dst_type, default) in content.items():
        try:
            value = form[k]
        except KeyError:
            result[k] = default
            continue

        src_type = type(value)

        # First, handle the case where we want all the results. In
        # this case, we need to ensure all the elements are strings,
        # and not Field instances.
        if src_type in (list, tuple):
            if dst_type is list:
                result[k] = [str(x) for x in value]
                continue

            if dst_type is tuple:
                result[k] = tuple([str(x) for x in value])
                continue

            # in all the other cases, we are only interested in the
            # first value.
            value = value[0]

        # Maybe we already have what is expected? Then don't change
        # anything.
        if isinstance(value, dst_type):
            if isinstance(value, StringField):
                result[k] = str(value)
            else:
                result[k] = value
            continue

        # Since we got here, 'value' is sure to be a single symbol,
        # not a list kind of structure anymore.
        if dst_type in (str, int):
            try:
                result[k] = dst_type(value)
            except:
                result[k] = default

        elif dst_type is tuple:
            result[k] = (str(value), )

        elif dst_type is list:
            result[k] = [str(value)]

        else:
            raise ValueError('cannot cast form value %s of type %r into type %r' % (value, src_type, dst_type))

    result['ln'] = wash_language(result['ln'])

    return result
