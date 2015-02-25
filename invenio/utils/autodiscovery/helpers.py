# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2013 CERN.
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

"""Autodiscovery helper functions."""

import inspect

from invenio.utils.text import wrap_text_in_a_box


def get_callable_signature_as_string(the_callable):
    """
    Returns a string representing a callable as if it would have been
    declared on the prompt.

    >>> def foo(arg1, arg2, arg3='val1', arg4='val2', *args, **argd):
    ...     pass
    >>> get_callable_signature_as_string(foo)
    def foo(arg1, arg2, arg3='val1', arg4='val2', *args, **argd)

    :param the_callable: the callable to be analyzed.
    :type the_callable: function/callable.
    :return: the signature.
    """
    args, varargs, varkw, defaults = inspect.getargspec(the_callable)
    tmp_args = list(args)
    args_dict = {}
    if defaults:
        defaults = list(defaults)
    else:
        defaults = []
    while defaults:
        args_dict[tmp_args.pop()] = defaults.pop()

    while tmp_args:
        args_dict[tmp_args.pop()] = None

    args_list = []
    for arg in args:
        if args_dict[arg] is not None:
            args_list.append("%s=%s" % (arg, repr(args_dict[arg])))
        else:
            args_list.append(arg)

    if varargs:
        args_list.append("*%s" % varargs)

    if varkw:
        args_list.append("**%s" % varkw)

    args_string = ', '.join(args_list)

    return "def %s(%s)" % (the_callable.__name__, args_string)


def get_callable_documentation(the_callable):
    """
    Returns a string with the callable signature and its docstring.

    :param the_callable: the callable to be analyzed.
    :type the_callable: function/callable.
    :return: the signature.
    """
    return wrap_text_in_a_box(
        title=get_callable_signature_as_string(the_callable),
        body=(getattr(the_callable, '__doc__') or 'No documentation').replace(
            '\n', '\n\n'),
        style='ascii_double')
