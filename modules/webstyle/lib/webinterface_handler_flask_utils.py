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

import types
from functools import wraps
from flask import Blueprint, current_app, request, session, redirect, abort, g, \
                  render_template, jsonify, get_flashed_messages, flash, \
                  Response, _request_ctx_stack, stream_with_context, Request
from invenio.webuser_flask import current_user, login_required
from invenio.urlutils import create_url
from invenio.sqlalchemyutils import db
from invenio.cache import cache
from sqlalchemy.sql import operators

## Placemark for the i18n function
_ = lambda x: x


def register_template_context_processor(f):
    g._template_context_processor.append(f)


class InvenioRequest(Request):
    """
    Flask Request wrapper which adds support for converting the request into
    legacy request (SimulatedModPythonRequest). This is primarily useful
    when Flaskifying modules, that still depends on old code.
    """
    def dummy_start_response(self, *args, **kwargs):
        pass

    def get_legacy_request(self):
        from invenio.webinterface_handler_wsgi import SimulatedModPythonRequest
        return SimulatedModPythonRequest(self.environ, self.dummy_start_response)


class InvenioBlueprint(Blueprint):

    ## Cache decorator alias
    #TODO language independent cache
    def invenio_cached(self, *cargs, **ckwargs):
        try:
            return cache.cached(*cargs, **ckwargs)
        except:
            def decorator(f):
                @wraps(f)
                def decorated_func(*args, **kwargs):
                    current_app.logger.error('Check the cache engine')
                    return f(*args, **kwargs)
                return decorated_func
            return decorator

    def invenio_memoize(self, *cargs, **ckwargs):
        try:
            return cache.memoize(*cargs, **ckwargs)
        except:
            def decorator(f):
                @wraps(f)
                def decorated_func(*args, **kwargs):
                    current_app.logger.error('Check the cache engine')
                    return f(*args, **kwargs)
                return decorated_func
            return decorator


    def __init__(self, name, import_name, url_prefix=None, config=None,
                 breadcrumbs=None, menubuilder=None, force_https=False):
        """
        Invenio extension of standard Flask blueprint.

        @param name: blueprint unique text identifier
        @param import_name: class name (usually __name__)
        @param url_prefix: URL prefix for all blueprints' view functions
        @param config: importable config class
        @param breadcrumbs: list of breadcrumbs
        @param menubuilder: list of menus
        @param force_https: requires blueprint to be accessible only via https
        """
        Blueprint.__init__(self, name, import_name, url_prefix=url_prefix)
        self.config = config
        self.breadcrumbs = breadcrumbs or []
        self.breadcrumbs_map = {}
        self.menubuilder = menubuilder or []
        self.menubuilder_map = {}
        self._force_https = force_https

    def invenio_set_breadcrumb(self, label, name=None):
        def decorator(f):
            endpoint = '.'.join([self.name, name or f.__name__])
            self.breadcrumbs_map[endpoint] = [(_('Home'), '')] + self.breadcrumbs + [(label, endpoint)]
            return f
        return decorator

    def invenio_add_menuitem(self, name=None, *args):
        def decorator(f):
            endpoint = '.'.join([self.name, name or f.__name__])
            self.menubuilder_map[endpoint] = args
        return decorator

    def invenio_templated(self, template=None, stream=False,
                          mimetype='text/html'):
        """
        The idea of this decorator is that you return a dictionary with the
        values passed to the template from the view function and the template
        is automatically rendered or a JSON object is generated if it is reply
        to an AJAX request.

        @note: user password ... TODO

        @see: http://flask.pocoo.org/docs/patterns/viewdecorators/
        """

        def stream_template(template_name, **context):
            """
            The jinja2 template supports rendering templates piece by piece,
            however the request context is not kept during whole time of
            template rendering process.

            @ see: http://flask.pocoo.org/docs/patterns/streaming/
            """
            current_app.update_template_context(context)
            t = current_app.jinja_env.get_template(template_name)
            rv = t.stream(context)

            return stream_with_context(rv)

            ### Get real objects from Werkzeug proxy objects.
            #app = current_app._get_current_object()
            #rq = request._get_current_object()
            #def wrap_context():
            #    """
            #    This iterator wrapper tries to solve problem of keeping
            #    request context until the template is fully rendered.
            #    """
            #    with app.request_context(rq.environ):
            #        for r in rv:
            #            yield r
            #return wrap_context()

        if stream:
            render = lambda template, **ctx: \
                        Response(stream_template(template, **ctx),
                                 mimetype=mimetype)
        else:
            render = render_template

        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                template_name = template
                if template_name is None:
                    template_name = request.endpoint \
                        .replace('.', '/') + '.html'
                ctx = f(*args, **kwargs)
                if ctx is None:
                    ctx = {}
                elif not isinstance(ctx, dict):
                    return ctx

                if request.is_xhr:
                    #FIXME think about more possible types
                    for k,v in ctx.iteritems():
                        if isinstance(v, list):
                            try:
                                ctx[k] = [dict(zip(x.keys(), [dict(i) for i in x])) for x in v]
                            except:
                                ctx[k] = v
                        else:
                            try:
                                ctx[k] = dict(v)
                            except:
                                ctx[k] = v
                    ctx['_messages'] = get_flashed_messages(with_categories=True)
                    return jsonify(**ctx)

                return render(template_name, **ctx)
            return decorated_function
        return decorator

    def invenio_sorted(self, model=None, cols=None):
        """
        This decorator fills `sort` argument with `ORDER BY` expression used by
        sqlalchemy for defined URL arguments `sort_by` and `order`.
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                sort_by = request.args.get('sort_by', None)
                order_fn = {'asc': db.asc,
                            'desc': db.desc}.get(
                                request.args.get('order', 'asc'), db.asc)
                sort = False
                if model is not None and sort_by is not None and (
                    cols is None or sort_by in cols):
                    try:
                        sort_keys = sort_by.split('.')
                        if hasattr(model, sort_keys[0]):
                            sort = order_fn(reduce(lambda x,y:
                                getattr(x.property.table.columns, y), sort_keys[1:],
                                getattr(model,sort_keys[0])))
                    except:
                        flash(_("Invalid sorting key '%s'.") % sort_by)
                kwargs['sort'] = sort
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def invenio_filtered(self, model=None, columns=None, form=None,
                         filter_empty=False):
        """
        This decorator

        The `filter_form` is also injected to template context
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not model or not columns:
                    return f(*args, **kwargs)
                where = []
                for column, op in columns.iteritems():
                    try:
                        values = request.values.getlist(column)
                        if not values:
                            continue
                        column_keys = column.split('.')
                        if hasattr(model, column_keys[0]):
                            cond = reduce(lambda x,y:
                                getattr(x.property.table.columns, y),
                                column_keys[1:],
                                getattr(model,column_keys[0]))
                            current_app.logger.info("Filtering by: %s = %s" % \
                                                    (cond, values))

                            # Multi-values support
                            if len(values) > 0:
                                # Ignore empty values when using start with,
                                # contains or similar.
                                # FIXME: add per field configuration
                                values = [value for value in values
                                    if len(value) > 0 or filter_empty]
                                if op == operators.eq:
                                    where.append(db.in_(values))
                                else:
                                    or_list = []
                                    for value in values:
                                        or_list.append(op(cond, value))
                                    where.append(db.or_(*or_list))
                            else:
                                where.append(op(cond, value))
                    except:
                        flash(_("Invalid filtering key '%s'.") % column)
                if form is not None:
                    filter_form = form(request.values)
                    @register_template_context_processor
                    def inject_filter_form():
                        return dict(filter_form=filter_form)
                # Generate ClauseElement for filtered columns.
                kwargs['filter'] = db.and_(*where)
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    @property
    def invenio_force_https(self):
        """
        Decorator: This forces the view function be available only through
        HTTPS.
        """
        def decorator(f):
            f._force_https = True
            return f
        return decorator

    def invenio_authenticated(self, f):
        """
        Decorator: This requires user to be logged in otherwise login manager
        redirects request to defined view or returns http error 401.
        """
        return login_required(f)

    def invenio_authorized(self, action, **params):
        """
        Decorator: This checks is current user is authorized to the action.
        When not authorized returns http error 401.
        """
        def decorator(f):
            @wraps(f)
            def inner(*a, **kw):
                try:
                    from invenio.access_control_engine import acc_authorize_action
                    auth, message = acc_authorize_action(
                        current_user.get_id(),
                        action,
                        **dict((k,v() if callable(v) else v) \
                            for (k,v) in params.iteritems()))
                    if auth == 1:
                        current_app.logger.info(message)
                        abort(401)
                except:
                    #FIXME add some better message to log
                    current_app.logger.info("NOT KEY FOR AUTHORIZATION")
                    abort(401)
                return f(*a, **kw)
            return inner
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

        # Allow passing argument modyfing function.
        if isinstance(dst_type, types.FunctionType):
            result[k] = dst_type(value)
            continue

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
