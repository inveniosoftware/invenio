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

import inspect

from six import iteritems

from .errors import AutodiscoveryError, AutodiscoveryCheckerError
from .helpers import get_callable_signature_as_string


def check_signature(object_name, reference_object, other_object):
    """
    Given a reference class or function check if an other class or function
    could be substituted without causing any instantiation/usage issues.

    :param object_name: the name of the object being checked.
    :type object_name: string
    :param reference_object: the reference class or function.
    :type reference_object: class/function
    :param other_object: the other class or function to be checked.
    :type other_object: class/function
    :raise AutodiscoveryCheckerError: in case the other object is not
        compatible with the reference object.
    """
    try:
        if inspect.isclass(reference_object):
            ## if the reference_object is a class
            if inspect.isclass(other_object):
                ## if the other_object is a class
                if issubclass(other_object, reference_object):
                    ## if the other_object is derived from the reference we
                    ## should check for all the method in the former that
                    ## exists in the the latter, wethever they recursively have
                    ## the same signature.
                    reference_object_map = dict(
                        inspect.getmembers(reference_object,
                                           inspect.isroutine))
                    for other_method_name, other_method_code in \
                            inspect.getmembers(other_object,
                                               inspect.isroutine):
                        if other_method_name in reference_object_map:
                            check_signature(
                                object_name,
                                reference_object_map[other_method_name],
                                other_method_code)
                else:
                    ## if the other_object is not derived from the
                    ## reference_object then all the method declared in the
                    ## latter should exist in the former and they should
                    ## recursively have the same signature.
                    other_object_map = dict(
                        inspect.getmembers(other_object, inspect.isroutine))
                    for reference_method_name, reference_method_code in \
                        inspect.getmembers(
                            reference_object, inspect.isroutine):
                        if reference_method_name in other_object_map:
                            check_signature(
                                object_name, reference_method_code,
                                other_method_code)
                        else:
                            raise AutodiscoveryCheckerError(
                                '"%s", which'
                                ' exists in the reference class, does not'
                                ' exist in the other class, and the reference'
                                ' class is not an anchestor of the other' %
                                reference_method_name)
            else:
                ## We are comparing apples and oranges!
                raise AutodiscoveryCheckerError(
                    "%s (the reference object)"
                    " is a class while %s (the other object) is not a class" %
                    (reference_object, other_object))
        elif inspect.isroutine(reference_object):
            ## if the reference_object is a function
            if inspect.isroutine(other_object):
                ## if the other_object is a function we will compare the
                ## reference_object and other_object function signautre i.e.
                ## their parameters.
                reference_args, reference_varargs, reference_varkw, \
                    reference_defaults = inspect.getargspec(reference_object)
                other_args, other_varargs, other_varkw, \
                    other_defaults = inspect.getargspec(other_object)
                ## We normalize the reference_defaults to be a list
                if reference_defaults is not None:
                    reference_defaults = list(reference_defaults)
                else:
                    reference_defaults = []

                ## We normalize the other_defaults to be a list
                if other_defaults is not None:
                    other_defaults = list(other_defaults)
                else:
                    other_defaults = []

                ## Check for presence of missing parameters in other function
                if not (other_varargs or other_varkw):
                    for reference_arg in reference_args:
                        if reference_arg not in other_args:
                            raise AutodiscoveryCheckerError(
                                'Argument "%s"'
                                ' in reference function %s does not exist in'
                                ' the other function %s' % (reference_arg,
                                reference_object, other_object))

                ## Check for presence of additional parameters in other
                ## function
                if not (reference_varargs or reference_varkw):
                    for other_arg in other_args:
                        if other_arg not in reference_args:
                            raise AutodiscoveryCheckerError(
                                'Argument "%s"'
                                ' in other function %s does not exist in the'
                                ' reference function %s' % (other_arg,
                                other_object, reference_object))

                ## Check sorting of arguments
                for reference_arg, other_arg in map(
                        None, reference_args, other_args):
                    if not((reference_arg == other_arg) or
                        (reference_arg is None and
                            (reference_varargs or reference_varkw)) or
                        (other_arg is None and
                            (other_args or other_varargs))):
                        raise AutodiscoveryCheckerError(
                            'Argument "%s" in'
                            ' the other function is in the position of'
                            ' argument "%s" in the reference function, i.e.'
                            ' the order of arguments is not respected' %
                            (other_arg, reference_arg))

                if len(reference_defaults) != len(other_defaults) and \
                        not (reference_args or reference_varargs
                        or other_args or other_varargs):
                    raise AutodiscoveryCheckerError(
                        "Default parameters in"
                        " the other function are not corresponding to the"
                        " default of parameters of the reference function")
            else:
                ## We are comparing apples and oranges!
                raise AutodiscoveryCheckerError(
                    '%s (the reference object)'
                    ' is a function while %s (the other object) is not a'
                    ' function' % (reference_object, other_object))
    except AutodiscoveryCheckerError as err:
        try:
            sourcefile = inspect.getsourcefile(other_object)
            sourceline = inspect.getsourcelines(other_object)[1]
        except IOError:
            ## other_object is not loaded from a real file
            sourcefile = 'N/A'
            sourceline = 'N/A'
        raise AutodiscoveryCheckerError(
            'Error in checking signature for'
            ' "%s" as defined at "%s" (line %s): %s' %
            (object_name, sourcefile, sourceline, err))


def check_arguments_compatibility(the_callable, argd):
    """
    Check if calling the_callable with the given arguments would be correct
    or not.

    >>> def foo(arg1, arg2, arg3='val1', arg4='val2', *args, **argd):
    ...     pass
    >>> try: check_arguments_compatibility(foo, {'arg1': 'bla', 'arg2': 'blo'})
    ... except ValueError as err: print 'failed'
    ... else: print 'ok'
    ok
    >>> try: check_arguments_compatibility(foo, {'arg1': 'bla'})
    ... except ValueError as err: print 'failed'
    ... else: print 'ok'
    failed

    Basically this function is simulating the call:

    >>> the_callable(**argd)

    but it only checks for the correctness of the arguments, without
    actually calling the_callable.

    :param the_callable: the callable to be analyzed.
    :type the_callable: function/callable
    :param argd: the arguments to be passed.
    :type argd: dict
    :raise ValueError: in case of uncompatibility
    """
    if not argd:
        argd = {}
    args, dummy, varkw, defaults = inspect.getargspec(the_callable)
    tmp_args = list(args)
    optional_args = []
    args_dict = {}
    if defaults:
        defaults = list(defaults)
    else:
        defaults = []
    while defaults:
        arg = tmp_args.pop()
        optional_args.append(arg)
        args_dict[arg] = defaults.pop()

    while tmp_args:
        args_dict[tmp_args.pop()] = None

    for arg, dummy_value in iteritems(argd):
        if arg in args_dict:
            del args_dict[arg]
        elif not varkw:
            raise ValueError(
                'Argument %s not expected when calling callable '
                '"%s" with arguments %s' % (
                    arg, get_callable_signature_as_string(the_callable), argd))

    for arg in args_dict.keys():
        if arg in optional_args:
            del args_dict[arg]

    if args_dict:
        raise ValueError(
            'Arguments %s not specified when calling callable '
            '"%s" with arguments %s' % (
                ', '.join(args_dict.keys()),
                get_callable_signature_as_string(the_callable),
                argd))


def create_enhanced_plugin_builder(compulsory_objects=None,
                                   optional_objects=None,
                                   other_data=None):
    """
    Creates a plugin builder function suitable to extract some specific
    objects (either compulsory or optional) and other simpler data

    >>> def dummy_needed_funct1(foo, bar):
    ...     pass
    >>> class dummy_needed_class1:
    ...     def __init__(self, baz):
    ...         pass
    >>> def dummy_optional_funct2(boo):
    ...     pass
    >>> create_enhanced_plugin_builder(
    ...    compulsory_objects={
    ...         'needed_funct1' : dummy_needed_funct1,
    ...         'needed_class1' : dummy_needed_class1
    ...     },
    ...     optional_objects={
    ...         'optional_funct2' : dummy_optional_funct2,
    ...     },
    ...     other_data={
    ...         'CFG_SOME_DATA' : (str, ''),
    ...         'CFG_SOME_INT' : (int, 0),
    ...     })
    <function plugin_builder at 0xb7812064>

    :param compulsory_objects: map of name of an object to look for inside
        the `plugin` and a *signature* for a class or callable. Every
        name specified in this map **must exists** in the plugin, otherwise
        the plugin will fail to load.
    :type compulsory_objects: dict
    :param optional_objects: map of name of an object to look for inside
        the C{plugin} and a I{signature} for a class or callable. Every
        name specified in this map must B{can exists} in the plugin.
    :type optional_objects: dict
    :param other_data: map of other simple data that can be loaded from
        the plugin. The map has the same format of the C{content}
        parameter of L{invenio.ext.legacy.handler.wash_urlargd}.
    :type other_data: dict
    :return: a I{plugin_builder} function that can be used with the
        map function. Such function will build the plugin
        in the form of a map, where every key is one of the keys inside
        the three maps provided as parameters and the corresponding value
        is the expected class or callable or simple data.
    """
    from invenio.ext.legacy.handler import wash_urlargd

    def plugin_builder(the_plugin):
        """
        Enhanced plugin_builder created by L{create_enhanced_plugin_builder}.

        :param plugin: the code of the module as just read from package.
        :return: the plugin in the form of a map.
        """
        plugin_name = the_plugin.__name__
        plugin = {}

        if compulsory_objects:
            for object_name, object_signature in \
                    iteritems(compulsory_objects):
                the_object = getattr(the_plugin, object_name, None)
                if the_object is None:
                    raise AutodiscoveryError('Plugin "%s" does not '
                        'contain compulsory object "%s"' % (plugin_name,
                        object_name))
                try:
                    check_signature(object_name, the_object, object_signature)
                except AutodiscoveryError as err:
                    raise AutodiscoveryError('Plugin "%s" contains '
                        'object "%s" with a wrong signature: %s' %
                        (plugin_name, object_name, err))
                plugin[object_name] = the_object

        if optional_objects:
            for object_name, object_signature in iteritems(optional_objects):
                the_object = getattr(the_plugin, object_name, None)
                if the_object is not None:
                    try:
                        check_signature(
                            object_name,
                            the_object,
                            object_signature)
                    except AutodiscoveryError as err:
                        raise AutodiscoveryError('Plugin "%s" '
                            'contains object "%s" with a wrong signature: %s' %
                            (plugin_name, object_name, err))
                    plugin[object_name] = the_object

        if other_data:
            the_other_data = {}
            for data_name, (dummy, data_default) in iteritems(other_data):
                the_other_data[data_name] = getattr(the_plugin, data_name,
                                                    data_default)

            try:
                the_other_data = wash_urlargd(the_other_data, other_data)
            except Exception as err:
                raise AutodiscoveryError('Plugin "%s" contains other '
                    'data with problems: %s' % (plugin_name, err))

            plugin.update(the_other_data)
        return plugin

    return plugin_builder
