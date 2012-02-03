# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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
Invenio -> Flask adapter utilities
"""

from functools import wraps
from flask import Blueprint, current_app, request, session, redirect

from invenio.urlutils import create_url

## Placemark for the i18n function
_ = lambda x:x

class InvenioBlueprint(Blueprint):
    def __init__(self, name, import_name, url_prefix=None, config=None, breadcrumbs=None):
        Blueprint.__init__(self, name, import_name, url_prefix=url_prefix)
        self.config = config
        self.breadcrumbs = breadcrumbs or []
        self.breadcrumbs_map = {}

    def invenio_set_breadcrumb(self, label, name=None):
        def decorator(f):
            endpoint = '.'.join([self.name, name or f.__name__])
            self.breadcrumbs_map[endpoint] = [(_('Home'), '')] + self.breadcrumbs + [(label, endpoint)]
            return f
        return decorator

    def invenio_authenticated(self, f):
        @wraps(f)
        def decorator(*args, **kwds):
            if session["user_info"]['guest'] == '1':
                return redirect(create_url("/youraccount/login", {"referer": request.url}))
            else:
                return f(*args, **kwds)
        return decorator

    def invenio_wash_urlargd(self, config):
        def _invenio_wash_urlargd(f):
            @wraps(f)
            def decorator():
                argd = wash_urlargd(request.values, config)
                return f(**argd)
            return decorator
        return _invenio_wash_urlargd

def unicodifier(obj):
    """
    Tries to (recursively) convert the given object into unicode, assuming
    a UTF-8 encoding)

    :Parameters:
    - `obj`: the object to convert (can be e.g. unicode, str, list, tuple, dict...
    """
    if isinstance(obj, unicode):
        return obj
    elif isinstance(obj, str):
        return obj.decode('utf8')
    elif isinstance(obj, list):
        return [unicodifier(elem) for elem in obj]
    elif isinstance(obj, tuple):
        return tuple(unicodifier(elem) for elem in obj)
    elif isinstance(obj, dict):
        return dict((key, unicodifier(value)) for key, value in obj.iteritems())
    return obj

def wash_urlargd(form, content):
    """
    Wash the complete form based on the specification in
    content. Content is a dictionary containing the field names as a
    key, and a tuple (type, default) as value.

    'type' can be list, unicode, invenio.webinterface_handler_wsgi_utils.StringField, int, tuple, or
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
                result[k] = [x for x in value]
                continue

            if dst_type is tuple:
                result[k] = tuple([x for x in value])
                continue

            # in all the other cases, we are only interested in the
            # first value.
            value = value[0]

        # Maybe we already have what is expected? Then don't change
        # anything.
        if isinstance(value, dst_type):
            result[k] = value
            continue

        # Since we got here, 'value' is sure to be a single symbol,
        # not a list kind of structure anymore.
        if dst_type in (int, float, long):
            try:
                result[k] = dst_type(value)
            except:
                result[k] = default

        elif dst_type is tuple:
            result[k] = (value, )

        elif dst_type is list:
            result[k] = [value]

        else:
            raise ValueError('cannot cast form value %s of type %r into type %r' % (value, src_type, dst_type))

    return result
