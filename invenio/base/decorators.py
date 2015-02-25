# -*- coding: utf-8 -*-
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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
    invenio.base.decorators
    -----------------------

    Implements custom decorators.

    Requires::

    * `invenio.ext.sqlalchemy:db`
    * `invenio.ext.template.context_processor:\
       register_template_context_processor`
"""
from six import iteritems

from flask import request, jsonify, current_app, stream_with_context, \
    Response, render_template, get_flashed_messages, flash, g
from functools import wraps
from sqlalchemy.sql import operators

from invenio.ext.sqlalchemy import db
from invenio.ext.template.context_processor import \
    register_template_context_processor


def templated(template=None, stream=False, mimetype='text/html'):
    """
    The idea of this decorator is that you return a dictionary with the
    values passed to the template from the view function and the template
    is automatically rendered or a JSON object is generated if it is reply
    to an AJAX request.

    see::
        http://flask.pocoo.org/docs/patterns/viewdecorators/
    """

    def stream_template(template_name, **context):
        """
        The jinja2 template supports rendering templates piece by piece,
        however the request context is not kept during whole time of
        template rendering process.

        see::
            http://flask.pocoo.org/docs/patterns/streaming/
        """
        current_app.update_template_context(context)
        t = current_app.jinja_env.get_template(template_name)
        rv = t.stream(context)

        return stream_with_context(rv)

    if stream:
        render = lambda template, **ctx: Response(
            stream_template(template, **ctx), mimetype=mimetype)
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
                for k, v in iteritems(ctx):
                    if isinstance(v, list):
                        try:
                            ctx[k] = [dict(zip(x.keys(),
                                               [dict(i) for i in x])
                                           ) for x in v]
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


def sorted_by(model=None, cols=None):
    """
    This decorator fills `sort` argument with `ORDER BY` expression used by
    sqlalchemy for defined URL arguments `sort_by` and `order`.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            sort_by = request.args.get('sort_by', None)
            order_fn = {'asc': db.asc,
                        'desc': db.desc}.get(request.args.get('order', 'asc'),
                                             db.asc)
            sort = False
            if model is not None and sort_by is not None and (
                    cols is None or sort_by in cols):
                try:
                    sort_keys = sort_by.split('.')
                    if hasattr(model, sort_keys[0]):
                        sort = order_fn(reduce(lambda x, y: getattr(
                            x.property.table.columns, y), sort_keys[1:],
                            getattr(model, sort_keys[0])))
                except:
                    flash(g._("Invalid sorting key '%(x_key)s'.", x_key=sort_by))
            kwargs['sort'] = sort
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def filtered_by(model=None, columns=None, form=None, filter_empty=False):
    """
    This decorator adds `filter` argument with 'WHERE' exression.
    The `filter_form` is also injected to template context.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not model or not columns:
                return f(*args, **kwargs)
            where = []
            for column, op in iteritems(columns):
                try:
                    values = request.values.getlist(column)
                    if not values:
                        continue
                    column_keys = column.split('.')
                    if hasattr(model, column_keys[0]):
                        cond = reduce(lambda x, y:
                                      getattr(x.property.table.columns, y),
                                      column_keys[1:],
                                      getattr(model, column_keys[0]))
                        current_app.logger.debug("Filtering by: %s = %s" %
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
                    flash(g._("Invalid filtering key '%(x_key)s'.", x_key=column))
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


def wash_arguments(config):
    def _decorated(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            from invenio.utils.washers import wash_urlargd
            argd = wash_urlargd(request.values, config)
            argd.update(kwargs)
            return f(*args, **argd)
        return decorator
    return _decorated
