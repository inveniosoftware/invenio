# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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
This module implement a generic plugin container facility.
"""

import sys
import os
import glob
import inspect
import imp

from invenio.config import CFG_PYLIBDIR
from invenio.textutils import wrap_text_in_a_box

class InvenioPluginContainerError(Exception):
    """
    Exception raised when some error happens during plugin loading.
    """
    pass


class PluginContainer(object):
    """
    This class implements a I{plugin container}.

    This class implements part of the dict interface with the condition
    that only correctly enabled plugins can be retrieved by their plugin_name.

    >>> ## Loading all the plugin within a directory.
    >>> websubmit_functions = PluginContainer(
    ...     os.path.join(CFG_PYLIBDIR,
    ...     'invenio', 'websubmit_functions', '*.py')
    ... )
    >>> ## Loading an explicit plugin.
    >>> case_eds = websubmit_functions['CaseEDS']

    @param plugin_pathnames: zero or more plugins_pathnames from where to load
        the plugins.
    @type plugin_pathnames: string/list
    @param plugin_builder: a callable with the signature
        C{plugin_builder(plugin_name, plugin_code)} that will be called
        to extract the actual plugin from the module stored in plugin_code.
    @type plugin_builder: callable
    @param api_version: the API version of the plugin. If specified, plugins
        which specify different versions will fail to be loaded. Default value
        is C{None} which turns off the version checking.
    @type api_version: integer
    @param plugin_signature: a stub to be used in order to check if a loaded
        plugin respect a particular signature or not.
    @type plugin_signature: class/function

    @ivar _plugin_map: a map between plugin_name and a dict with keys
        "error", "plugin", "plugin_path", "enabled", "api_version"
    @type _plugin_map: dict
    @ivar _plugin_pathnames: the list of normalized plugin pathnames
        corresponding to the plugins to be loaded.
    @type _plugin_pathnames: list
    @ivar _plugin_builder: the plugin builder as passed to the constructor.
    @type plugin_builder: function
    @ivar api_version: the version as provided to the constructor.
    @type api_version: integer

    @group Mapping interface: __contains__,__getitem__,get,has_key,items,
        iteritems,iterkeys,itervalues,keys,values,__len__
    @group Main API: __init__,add_plugin_pathnames,get_enabled_plugins,
        get_broken_plugins,get_plugin,reload_plugins

    """

    def __init__(self,
            plugin_pathnames=None,
            plugin_builder=None,
            api_version=None,
            plugin_signature=None,
            external=False):
        self._plugin_map = {}
        self._plugin_pathnames = []
        self._external = external
        self.api_version = api_version
        if plugin_builder is None:
            self._plugin_builder = self.default_plugin_builder
        else:
            self._plugin_builder = plugin_builder
        self._plugin_signature = plugin_signature
        if plugin_pathnames:
            self.add_plugin_pathnames(plugin_pathnames)

    def default_plugin_builder(plugin_name, plugin_code):
        """
        Default plugin builder used to extract the plugin from the module
        that contains it.

        @note: By default it will look for a class or function with the same
            name of the plugin.

        @param plugin_name: the name of the plugin.
        @type plugin_name: string
        @param plugin_code: the code of the module as just read from
            filesystem.
        @type plugin_code: module
        @return: the plugin
        """
        return getattr(plugin_code, plugin_name)
    default_plugin_builder = staticmethod(default_plugin_builder)

    def add_plugin_pathnames(self, plugin_pathnames):
        """
        Add a one or more plugin pathnames, i.e. full plugin path exploiting
        wildcards, e.g. "bibformat_elements/bfe_*.py".

        @note: these plugins_pathnames will be added to the current list of
            plugin_pathnames, and all the plugins will be reloaded.

        @param plugin_pathnames: one or more plugins_pathnames
        @type plugin_pathnames: string/list
        """
        if type(plugin_pathnames) is str:
            self._plugin_pathnames.append(plugin_pathnames)
        else:
            self._plugin_pathnames.extend(plugin_pathnames)
        self.reload_plugins()

    def enable_plugin(self, plugin_name):
        """
        Enable plugin_name.

        @param plugin_name: the plugin name.
        @type plugin_name: string
        @raise KeyError: if the plugin does not exists.
        """
        self._plugin_map[plugin_name]['enabled'] = True

    def disable_plugin(self, plugin_name):
        """
        Disable plugin_name.

        @param plugin_name: the plugin name.
        @type plugin_name: string
        @raise KeyError: if the plugin does not exists.
        """
        self._plugin_map[plugin_name]['enabled'] = False

    def plugin_enabled_p(self, plugin_name):
        """
        Returns True if the plugin is correctly enabled.

        @param plugin_name: the plugin name.
        @type plugin_name: string
        @return: True if the plugin is correctly enabled..
        @rtype: bool
        @raise KeyError: if the plugin does not exists.
        """
        return self._plugin_map[plugin_name]['enabled']

    def get_plugin_filesystem_path(self, plugin_name):
        """
        Returns the filesystem path from where the plugin was loaded.

        @param plugin_name: the plugin name.
        @type plugin_name: string
        @return: the filesystem path.
        @rtype: string
        @raise KeyError: if the plugin does not exists.
        """
        return self._plugin_map[plugin_name]['plugin_path']

    def get_plugin(self, plugin_name):
        """
        Returns the plugin corresponding to plugin_name.

        @param plugin_name: the plugin name,
        @type plugin_name: string
        @return: the plugin
        @raise KeyError: if the plugin does not exists or is not enabled.
        """
        if self._plugin_map[plugin_name]['enabled']:
            return self._plugin_map[plugin_name]['plugin']
        else:
            raise KeyError('"%s" is not enabled' % plugin_name)

    def get_broken_plugins(self):
        """
        Returns a map between plugin names and errors, in the form of
        C{sys.exc_info} structure.

        @return: plugin_name -> sys.exc_info().
        @rtype: dict
        """
        ret = {}
        for plugin_name, plugin in self._plugin_map.iteritems():
            if plugin['error']:
                ret[plugin_name] = plugin['error']
        return ret

    def reload_plugins(self, reload=False):
        """
        For the plugins found through iterating in the plugin_pathnames, loads
        and working plugin.

        @note: if a plugin has the same plugin_name of an already loaded
            plugin, the former will override the latter (provided that the
            former had a compatible signature to the latter).
        @note: any plugin that fails to load will be added to the plugin
            map as disabled and the sys.exc_info() captured during the
            Exception will be stored. (if the failed plugin was supposed to
            override an existing one, the latter will be overridden by
            the failed former).
        """
        # The reload keyword argument exists for backwards compatibility.
        # Previously, reload_plugins, would not reload a module due to a bug.
        for plugin_path in self._plugin_pathnames_iterator():
            self._load_plugin(plugin_path, reload=reload)

    def normalize_plugin_path(self, plugin_path):
        """
        Returns a normalized plugin_path.

        @param plugin_path: the plugin path.
        @type plugin_path: string
        @return: the normalized plugin path.
        @rtype: string
        @raise ValueError: if the path is not under CFG_PYLIBDIR/invenio
        """
        invenio_path = os.path.abspath(os.path.join(CFG_PYLIBDIR, 'invenio'))
        plugin_path = os.path.abspath(plugin_path)
        if not self._external and not os.path.abspath(plugin_path).startswith(invenio_path):
            raise ValueError('A plugin should be stored under "%s" ("%s" was'
                ' specified)' % (invenio_path, plugin_path))
        return plugin_path

    def _plugin_pathnames_iterator(self):
        """
        Returns an iterator over all the normalized plugin path.

        @note: older plugin_pathnames are considered first, and newer
            plugin_pathnames later, so that plugin overriding is possible.

        @return: the iterator over plugin paths.
        @rtype: iterator
        """
        for plugin_pathname in self._plugin_pathnames:
            for plugin_path in glob.glob(plugin_pathname):
                yield self.normalize_plugin_path(plugin_path)

    def get_plugin_name(plugin_path):
        """
        Returns the name of the plugin after the plugin_path.

        @param plugin_path: the filesystem path to the plugin code.
        @type plugin_path: string
        @return: the plugin name.
        @rtype: string
        """
        plugin_name = os.path.basename(plugin_path)
        if plugin_name.endswith('.py'):
            plugin_name = plugin_name[:-len('.py')]
        return plugin_name
    get_plugin_name = staticmethod(get_plugin_name)

    def _load_plugin(self, plugin_path, reload=False):
        """
        Load a plugin in the plugin map.

        @note: if the plugin_name calculated from plugin_path corresponds to
            an already existing plugin, the old plugin will be overridden and
            if the old plugin was correctly loaded but disabled also the
            new plugin will be disabled.

        @param plugin_path: the plugin path.
        @type plugin_path: string
        """
        api_version = None
        try:
            plugin_name = self.get_plugin_name(plugin_path)

            # Let's see if the module is already loaded
            plugin = None
            if plugin_name in sys.modules:
                mod = sys.modules[plugin_name]
                if os.path.splitext(mod.__file__)[0] == os.path.splitext(plugin_path)[0]:
                    plugin = mod

            if not plugin or reload:
                # Let's load the plugin module.
                plugin_fp, plugin_path, plugin_desc = imp.find_module(
                    plugin_name, [os.path.dirname(plugin_path)]
                )

                try:
                    plugin = imp.load_module(
                            plugin_name, plugin_fp, plugin_path, plugin_desc
                    )
                finally:
                    if plugin_fp:
                        plugin_fp.close()

            ## Let's check for API version.
            api_version = getattr(plugin, '__plugin_version__', None)
            if self.api_version and api_version != self.api_version:
                raise InvenioPluginContainerError("Plugin version mismatch."
                    " Expected %s, found %s" % (self.api_version, api_version))

            ## Let's load the actual plugin
            plugin = self._plugin_builder(plugin_name, plugin)

            ## Are we overriding an already loaded plugin?
            enabled = True
            if plugin_name in self._plugin_map:
                old_plugin = self._plugin_map[plugin_name]
                if old_plugin['error'] is None:
                    enabled = old_plugin['enabled']
                    check_signature(plugin_name, old_plugin['plugin'], plugin)

            ## Let's check the plugin signature.
            if self._plugin_signature:
                check_signature(plugin_name, self._plugin_signature, plugin)

            self._plugin_map[plugin_name] = {
                'plugin': plugin,
                'error': None,
                'plugin_path': plugin_path,
                'enabled': enabled,
                'api_version': api_version,
            }
        except Exception as e:

            self._plugin_map[plugin_name] = {
                'plugin': None,
                'error': sys.exc_info(),
                'plugin_path': plugin_path,
                'enabled': False,
                'api_version': api_version,
            }

    def __getitem__(self, plugin_name):
        """
        As in C{dict.__getitem__} but apply plugin name normalization and check
        if the plugin is correctly enabled.

        @param plugin_name: the name of the plugin
        @type plugin_name: string
        @return: the plugin.
        @raise KeyError: if the corresponding plugin is not enabled or there
        were some errors.
        """
        plugin_name = self.get_plugin_name(plugin_name)
        if plugin_name in self._plugin_map and \
                self._plugin_map[plugin_name]['enabled'] is True:
            return self._plugin_map[plugin_name]['plugin']
        else:
            raise KeyError('"%s" does not exists or is not correctly enabled' %
                plugin_name)

    def __contains__(self, plugin_name):
        """
        As in C{dict.__contains__} but apply plugin name normalization and
        check if the plugin is correctly enabled.

        @param plugin_name: the name of the plugin
        @type plugin_name: string
        @return: True if plugin_name is correctly there.
        @rtype: bool
        """
        plugin_name = self.get_plugin_name(plugin_name)
        return plugin_name in self._plugin_map and \
            self._plugin_map[plugin_name]['enabled'] is True

    def __len__(self):
        """
        As in C{dict.__len__} but consider only correctly enabled plugins.

        @return: the total number of plugins correctly enabled.
        @rtype: integer
        """
        count = 0
        for plugin in self._plugin_map.values():
            if plugin['enabled']:
                count += 1
        return count

    def get(self, plugin_name, default=None):
        """
        As in C{dict.get} but consider only correctly enabled plugins.

        @param plugin_name: the name of the plugin
        @type plugin_name: string
        @param default: the default value to return if plugin_name does not
            correspond to a correctly enabled plugin.
        @return: the total number of plugins correctly enabled.
        @rtype: integer
        """
        try:
            return self.__getitem__(plugin_name)
        except KeyError:
            return default

    def has_key(self, plugin_name):
        """
        As in C{dict.has_key} but apply plugin name normalization and check
        if the plugin is correctly enabled.

        @param plugin_name: the name of the plugin
        @type plugin_name: string
        @return: True if plugin_name is correctly there.
        @rtype: bool
        """
        return self.__contains__(plugin_name)

    def items(self):
        """
        As in C{dict.items} but checks if the plugin are correctly enabled.

        @return: list of (plugin_name, plugin).
        @rtype: [(plugin_name, plugin), ...]
        """
        ret = []
        for plugin_name, plugin in self._plugin_map.iteritems():
            if plugin['enabled']:
                ret.append((plugin_name, plugin['plugin']))
        return ret

    def iteritems(self):
        """
        As in C{dict.iteritems} but checks if the plugin are correctly enabled.

        @return: an iterator over the (plugin_name, plugin) items.
        """
        for plugin_name, plugin in self._plugin_map.iteritems():
            if plugin['enabled']:
                yield (plugin_name, plugin['plugin'])

    def iterkeys(self):
        """
        As in C{dict.iterkeys} but checks if the plugin are correctly enabled.

        @return: an iterator over the plugin_names.
        """
        for plugin_name, plugin in self._plugin_map.iteritems():
            if plugin['enabled']:
                yield plugin_name

    __iter__ = iterkeys

    def itervalues(self):
        """
        As in C{dict.itervalues} but checks if the plugin are correctly
        enabled.

        @return: an iterator over the plugins.
        """
        for plugin in self._plugin_map.itervalues():
            if plugin['enabled']:
                yield plugin['plugin']

    def keys(self):
        """
        As in C{dict.keys} but checks if the plugin are correctly enabled.

        @return: the list of enabled plugin_names.
        @rtype: list of strings
        """
        ret = []
        for plugin_name, plugin in self._plugin_map.iteritems():
            if plugin['enabled']:
                ret.append(plugin_name)
        return ret

    def values(self):
        """
        As in C{dict.values} but checks if the plugin are correctly enabled.

        @return: the list of enabled plugin codes.
        """
        return [plugin['plugin'] \
            for plugin in self._plugin_map.values() if plugin['enabled']]

    def get_enabled_plugins(self):
        """
        Return a map of the correctly enabled plugins.

        @return: a map plugin_name -> plugin
        @rtype: dict
        """
        ret = {}
        for plugin_name, plugin in self._plugin_map.iteritems():
            if plugin['enabled']:
                ret[plugin_name] = plugin['plugin']
        return ret


def check_signature(object_name, reference_object, other_object):
    """
    Given a reference class or function check if an other class or function
    could be substituted without causing any instantiation/usage issues.

    @param object_name: the name of the object being checked.
    @type object_name: string
    @param reference_object: the reference class or function.
    @type reference_object: class/function
    @param other_object: the other class or function to be checked.
    @type other_object: class/function
    @raise InvenioPluginContainerError: in case the other object is not
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
                        inspect.getmembers(other_object, inspect.isroutine):
                        if other_method_name in reference_object_map:
                            check_signature(object_name,
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
                            raise InvenioPluginContainerError('"%s", which'
                                ' exists in the reference class, does not'
                                ' exist in the other class, and the reference'
                                ' class is not an anchestor of the other' %
                                reference_method_name)
            else:
                ## We are comparing apples and oranges!
                raise InvenioPluginContainerError("%s (the reference object)"
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
                            raise InvenioPluginContainerError('Argument "%s"'
                                ' in reference function %s does not exist in'
                                ' the other function %s' % (reference_arg,
                                reference_object, other_object))

                ## Check for presence of additional parameters in other
                ## function
                if not (reference_varargs or reference_varkw):
                    for other_arg in other_args:
                        if other_arg not in reference_args:
                            raise InvenioPluginContainerError('Argument "%s"'
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
                        raise InvenioPluginContainerError('Argument "%s" in'
                            ' the other function is in the position of'
                            ' argument "%s" in the reference function, i.e.'
                            ' the order of arguments is not respected' %
                            (other_arg, reference_arg))

                if len(reference_defaults) != len(other_defaults) and \
                        not (reference_args or reference_varargs
                        or other_args or other_varargs):
                    raise InvenioPluginContainerError("Default parameters in"
                        " the other function are not corresponding to the"
                        " default of parameters of the reference function")
            else:
                ## We are comparing apples and oranges!
                raise InvenioPluginContainerError('%s (the reference object)'
                    ' is a function while %s (the other object) is not a'
                    ' function' % (reference_object, other_object))
    except InvenioPluginContainerError, err:
        try:
            sourcefile = inspect.getsourcefile(other_object)
            sourceline = inspect.getsourcelines(other_object)[1]
        except IOError:
            ## other_object is not loaded from a real file
            sourcefile = 'N/A'
            sourceline = 'N/A'
        raise InvenioPluginContainerError('Error in checking signature for'
            ' "%s" as defined at "%s" (line %s): %s' %
            (object_name, sourcefile, sourceline, err))


def create_enhanced_plugin_builder(
        compulsory_objects=None, optional_objects=None, other_data=None):
    """
    Creates a plugin_builder function suitable to extract some specific
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

    @param compulsory_objects: map of name of an object to look for inside
        the C{plugin_code} and a I{signature} for a class or callable. Every
        name specified in this map B{must exists} in the plugin_code, otherwise
        the plugin will fail to load.
    @type compulsory_objects: dict
    @param optional_objects: map of name of an object to look for inside
        the C{plugin_code} and a I{signature} for a class or callable. Every
        name specified in this map must B{can exists} in the plugin_code.
    @type optional_objects: dict
    @param other_data: map of other simple data that can be loaded from
        the plugin_code. The map has the same format of the C{content}
        parameter of L{invenio.webinterface_handler.wash_urlargd}.
    @type other_data: dict
    @return: a I{plugin_builder} function that can be used with the
        C{PluginContainer} constructor. Such function will build the plugin
        in the form of a map, where every key is one of the keys inside
        the three maps provided as parameters and the corresponding value
        is the expected class or callable or simple data.
    """
    from invenio.webinterface_handler import wash_urlargd

    def plugin_builder(plugin_name, plugin_code):
        """
        Enhanced plugin_builder created by L{create_enhanced_plugin_builder}.

        @param plugin_name: the name of the plugin.
        @type plugin_name: string
        @param plugin_code: the code of the module as just read from
            filesystem.
        @type plugin_code: module
        @return: the plugin in the form of a map.
        """
        plugin = {}

        if compulsory_objects:
            for object_name, object_signature in \
                    compulsory_objects.iteritems():
                the_object = getattr(plugin_code, object_name, None)
                if the_object is None:
                    raise InvenioPluginContainerError('Plugin "%s" does not '
                        'contain compulsory object "%s"' % (plugin_name,
                        object_name))
                try:
                    check_signature(object_name, the_object, object_signature)
                except InvenioPluginContainerError, err:
                    raise InvenioPluginContainerError('Plugin "%s" contains '
                        'object "%s" with a wrong signature: %s' %
                        (plugin_name, object_name, err))
                plugin[object_name] = the_object

        if optional_objects:
            for object_name, object_signature in optional_objects.iteritems():
                the_object = getattr(plugin_code, object_name, None)
                if the_object is not None:
                    try:
                        check_signature(
                            object_name,
                            the_object,
                            object_signature)
                    except InvenioPluginContainerError, err:
                        raise InvenioPluginContainerError('Plugin "%s" '
                            'contains object "%s" with a wrong signature: %s' %
                            (plugin_name, object_name, err))
                    plugin[object_name] = the_object

        if other_data:
            the_other_data = {}
            for data_name, (dummy, data_default) in other_data.iteritems():
                the_other_data[data_name] = getattr(
                    plugin_code, data_name, data_default)

            try:
                the_other_data = wash_urlargd(the_other_data, other_data)
            except Exception, err:
                raise InvenioPluginContainerError('Plugin "%s" contains other '
                    'data with problems: %s' % (plugin_name, err))

            plugin.update(the_other_data)
        return plugin

    return plugin_builder


def get_callable_signature_as_string(the_callable):
    """
    Returns a string representing a callable as if it would have been
    declared on the prompt.

    >>> def foo(arg1, arg2, arg3='val1', arg4='val2', *args, **argd):
    ...     pass
    >>> get_callable_signature_as_string(foo)
    def foo(arg1, arg2, arg3='val1', arg4='val2', *args, **argd)

    @param the_callable: the callable to be analyzed.
    @type the_callable: function/callable.
    @return: the signature.
    @rtype: string
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

    @param the_callable: the callable to be analyzed.
    @type the_callable: function/callable.
    @return: the signature.
    @rtype: string
    """
    return wrap_text_in_a_box(
        title=get_callable_signature_as_string(the_callable),
        body=(getattr(the_callable, '__doc__') or 'No documentation').replace(
            '\n', '\n\n'),
        style='ascii_double')


def check_arguments_compatibility(the_callable, argd):
    """
    Check if calling the_callable with the given arguments would be correct
    or not.

    >>> def foo(arg1, arg2, arg3='val1', arg4='val2', *args, **argd):
    ...     pass
    >>> try: check_arguments_compatibility(foo, {'arg1': 'bla', 'arg2': 'blo'})
    ... except ValueError, err: print 'failed'
    ... else: print 'ok'
    ok
    >>> try: check_arguments_compatibility(foo, {'arg1': 'bla'})
    ... except ValueError, err: print 'failed'
    ... else: print 'ok'
    failed

    Basically this function is simulating the call:
    >>> the_callable(**argd)
    but it only checks for the correctness of the arguments, without
    actually calling the_callable.

    @param the_callable: the callable to be analyzed.
    @type the_callable: function/callable
    @param argd: the arguments to be passed.
    @type argd: dict
    @raise ValueError: in case of uncompatibility
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

    for arg, dummy_value in argd.iteritems():
        if arg in args_dict:
            del args_dict[arg]
        elif not varkw:
            raise ValueError('Argument %s not expected when calling callable '
                '"%s" with arguments %s' % (
                    arg, get_callable_signature_as_string(the_callable), argd))

    for arg in args_dict.keys():
        if arg in optional_args:
            del args_dict[arg]

    if args_dict:
        raise ValueError('Arguments %s not specified when calling callable '
            '"%s" with arguments %s' % (
                ', '.join(args_dict.keys()),
                get_callable_signature_as_string(the_callable),
                argd))
