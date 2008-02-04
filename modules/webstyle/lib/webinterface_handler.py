# -*- coding: utf-8 -*-
## $Id$

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
Apache request handler mechanism.

It gives the tools to map url to functions, handles the legacy url
scheme (/search.py queries), HTTP/HTTPS switching, language
specification,...
"""

__revision__ = "$Id$"

import urlparse
import cgi
import sys

# The following mod_python imports are done separately in a particular
# order (util first) because I was getting sometimes publisher import
# error when testing weird situations, preventing util from being
# imported and leading to a traceback later.  When this happened,
# importing util was okay, only publisher import caused troubles, so
# that importing in special order prevents these problems.
try:
    from mod_python import util
    from mod_python import apache
    from mod_python import publisher
except ImportError:
    pass

from invenio.config import cdslang, weburl, sweburl, tmpdir
from invenio.messages import wash_language
from invenio.urlutils import redirect_to_url

has_https_support = weburl != sweburl


DEBUG = False

def _debug(msg):
    if DEBUG:
        apache.log_error(msg, apache.APLOG_WARNING)
    return

def _check_result(req, result):
    """ Check that a page handler actually wrote something, and
    properly finish the apache request."""

    if result or req.bytes_sent > 0 or req.next:

        if result is None:
            result = ""
        else:
            result = str(result)

        # unless content_type was manually set, we will attempt
        # to guess it
        if not req._content_type_set:
            # make an attempt to guess content-type
            if result[:100].strip()[:6].lower() == '<html>' \
               or result.find('</') > 0:
                req.content_type = 'text/html'
            else:
                req.content_type = 'text/plain'

        if req.method != "HEAD":
            req.write(result)
        else:
            req.write("")

        return apache.OK

    else:
        req.log_error("mod_python.publisher: %s returned nothing." % `object`)
        return apache.HTTP_INTERNAL_SERVER_ERROR



class TraversalError(Exception):
    pass

class WebInterfaceDirectory(object):
    """ A directory groups web pages, and can delegate dispatching of
    requests to the actual handler. This has been heavily borrowed
    from Quixote's dispatching mechanism, with specific adaptations."""

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

    def _traverse(self, req, path):
        """ Locate the handler of an URI by traversing the elements of
        the path."""

        _debug('traversing %r' % path)

        component, path = path[0], path[1:]

        name = self._translate(component)

        if name is None:
            obj, path = self._lookup(component, path)
        else:
            obj = getattr(self, name)

        if obj is None:
            _debug('could not resolve %s' % repr((component, path)))
            raise TraversalError()

        # We have found the next segment. If we know that from this
        # point our subpages are over HTTPS, do the switch.
        if has_https_support and self._force_https:
            is_over_https = req.subprocess_env.has_key('HTTPS') \
                            and req.subprocess_env['HTTPS'] == 'on'

            if not is_over_https:
                # We need to isolate the part of the URI that is after
                # weburl, and append that to our sweburl.
                original_parts = urlparse.urlparse(req.unparsed_uri)
                plain_prefix_parts = urlparse.urlparse(weburl)
                secure_prefix_parts = urlparse.urlparse(sweburl)

                # Compute the new path
                plain_path = original_parts[2]
                plain_path = secure_prefix_parts[2] + plain_path[len(plain_prefix_parts[2]):]

                # ...and recompose the complete URL
                final_parts = list(secure_prefix_parts)
                final_parts[2] = plain_path
                final_parts[-3:] = original_parts[-3:]

                target = urlparse.urlunparse(final_parts)
                redirect_to_url(req, target)

        # Continue the traversal. If there is a path, continue
        # resolving, otherwise call the method as it is our final
        # renderer. We even pass it the parsed form arguments.
        if path:
            return obj._traverse(req, path)

        form = util.FieldStorage(req, keep_blank_values=True)

        result = obj(req, form)
        return _check_result(req, result)

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
                util.redirect(req, req.uri + "/", permanent=True)

        _debug('directory %r is not callable' % self)
        raise TraversalError()



def create_handler(root):
    """ Return a handler function that will dispatch apache requests
    through the URL layout passed in parameter."""

    def _profiler(req):
        """ This handler wrap the default handler with a profiler.
        Profiling data is written into ${tmpdir}/invenio-profile-stats-datetime.raw, and
        is displayed at the bottom of the webpage.
        To use add profile=1 to your url. To change sorting algorithm you
        can provide profile=algorithm_name. You can add more than one
        profile requirement like ?profile=time&profile=cumulative.
        The list of available algorithm is displayed at the end of the profile.
        """
        if req.args and cgi.parse_qs(req.args).has_key('profile'):
            from cStringIO import StringIO
            try:
                import pstats
            except ImportError:
                ret = _handler(req)
                req.write("<pre>%s</pre>" % "The Python Profiler is not installed!")
                return ret
            import datetime
            date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            filename = '%s/invenio-profile-stats-%s.raw' % (tmpdir, date)
            existing_sorts = pstats.Stats.sort_arg_dict_default.keys()
            required_sorts = []
            profile_dump = []
            for sort in cgi.parse_qs(req.args)['profile']:
                if sort not in existing_sorts:
                    sort = 'cumulative'
                if sort not in required_sorts:
                    required_sorts.append(sort)
            if sys.hexversion < 0x02050000:
                import hotshot, hotshot.stats
                pr = hotshot.Profile(filename)
                ret = pr.runcall(_handler, req)
                for sort_type in required_sorts:
                    tmp_out = sys.stdout
                    sys.stdout = StringIO()
                    hotshot.stats.load(filename).strip_dirs().sort_stats(sort_type).print_stats()
                    profile_dump.append(sys.stdout.getvalue())
                    sys.stdout = tmp_out
            else:
                import cProfile
                pr = cProfile.Profile()
                ret = pr.runcall(_handler, req)
                pr.dump_stats(filename)
                for sort_type in required_sorts:
                    strstream = StringIO()
                    pstats.Stats(filename, stream=strstream).strip_dirs().sort_stats(sort_type).print_stats()
                    profile_dump.append(strstream.getvalue())
            profile_dump = ''.join(["<pre>%s</pre>" % single_dump for single_dump in profile_dump])
            profile_dump += '\nYou can use sort_profile=%s' % existing_sorts
            req.write("<pre>%s</pre>" % profile_dump)
            return ret
        else:
            return _handler(req)

    def _handler(req):
        """ This handler is invoked by mod_python with the apache request."""

        req.allow_methods(["GET", "POST"])
        if req.method not in ["GET", "POST"]:
            raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

        try:
            uri = req.uri
            if uri == '/':
                path = ['']
            else:
                path = uri[1:].split('/')

            return root._traverse(req, path)

        except TraversalError:
            return apache.HTTP_NOT_FOUND

        # Serve an error by default.
        return apache.HTTP_NOT_FOUND


    return _profiler



def wash_urlargd(form, content):
    """
    Wash the complete form based on the specification in
    content. Content is a dictionary containing the field names as a
    key, and a tuple (type, default) as value.

    'type' can be list, str, int, tuple, or mod_python.util.Field (for
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

    content['ln'] = (str, cdslang)

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
        if src_type is dst_type:
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
            result[k] = (str(value),)

        elif dst_type is list:
            result[k] = [str(value)]

        else:
            raise ValueError('cannot cast form into type %r' % dst_type)

    result['ln'] = wash_language(result['ln'])

    return result

