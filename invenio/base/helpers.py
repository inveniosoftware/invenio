# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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
    invenio.base.helpers
    --------------------

    Implements various helpers.
"""

from functools import wraps
from flask import Flask, current_app, has_app_context


def with_app_context(app=None, new_context=False, **kwargs_config):
    """Run function within application context"""

    def get_application():
        """Returns an application instance."""
        if app is not None and not isinstance(app, Flask) and callable(app):
            return app(**kwargs_config)
        else:
            from .factory import create_app
            return create_app(**kwargs_config)

    def decorator(f):
        @wraps(f)
        def decorated_func(*args, **kwargs):
            """This function has to run within application context."""

            if not has_app_context() or new_context:
                with get_application().test_request_context('/'):
                    #FIXME we should use maybe app_context()
                    current_app.preprocess_request()
                    result = f(*args, **kwargs)
            else:
                result = f(*args, **kwargs)
            return result
        return decorated_func
    return decorator


def unicodifier(obj):
    """
    Tries to (recursively) convert the given object into unicode, assuming
    a UTF-8 encoding)

    :param obj: the object to convert
        (can be e.g. unicode, str, list, tuple, dict)
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
