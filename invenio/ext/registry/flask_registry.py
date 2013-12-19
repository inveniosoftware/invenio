# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
Flask-Registry extension
"""
import os

from werkzeug.utils import import_string, find_modules
from werkzeug.local import LocalProxy
from pkg_resources import iter_entry_points, resource_listdir, resource_isdir
from flask import current_app, has_app_context


class RegistryError(Exception):
    pass


class Registry(object):
    """
    Flask-Registry
    """
    def __init__(self, app=None):
        self._registry = dict()
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['registry'] = self

    def __iter__(self):
        return self._registry.__iter__()

    def __len__(self):
        return self._registry.__len__()

    def __contains__(self, item):
        return self._registry.__contains__(item)

    def __getitem__(self, key):
        return self._registry[key]

    def __setitem__(self, key, value):
        if key in self._registry:
            raise RegistryError("Namespace %s already taken." % key)
        self._registry[key] = value
        self._registry[key]._namespace = key

    def __delitem__(self, key):
        self._registry.__delitem__(key)

    def __missing__(self, key):
        return self._registry.__missing__(key)

    def items(self):
        return self._registry.items()


class RegistryBase(object):
    """
    Base class for all registries
    """
    @property
    def namespace(self):
        return self._namespace

    def register(self, *args, **kwargs):
        raise NotImplementedError()

    def unregister(self, *args, **kwargs):
        raise NotImplementedError()


class ListRegistry(RegistryBase):
    """
    Basic registry that just keeps a list of items.
    """
    def __init__(self):
        self.registry = []

    def __iter__(self):
        return self.registry.__iter__()

    def __len__(self):
        return self.registry.__len__()

    def __contains__(self, item):
        return self.registry.__contains__(item)

    def register(self, item):
        self.registry.append(item)

    def unregister(self, item):
        self.registry.remove(item)


class DictRegistry(RegistryBase):
    """
    Basic registry that just keeps a key, value pairs.
    """
    def __init__(self):
        self.registry = {}

    def __iter__(self):
        return self.registry.__iter__()

    def __len__(self):
        return self.registry.__len__()

    def __contains__(self, item):
        return self.registry.__contains__(item)

    def __getitem__(self, key):
        return self.registry[key]

    def __missing__(self, key):
        return self.registry.__missing__(key)


class ExtensionRegistry(ListRegistry):
    """
    Flask extensions registry

    Loads all extensions specified by EXTENSIONS configuration variable. The
    registry will look for a setup_app function in the extension and call it if
    it exists.

    Example::

        EXTENSIONS = [
            'invenio.ext.debug_toolbar',
            'flask.ext.menu:Menu',
        ]
    """
    def __init__(self, app):
        """
        :param app: Flask application to get configuration from.
        """
        super(ExtensionRegistry, self).__init__()
        for ext_name in app.config.get('EXTENSIONS', []):
            self.register(app, ext_name)

    def register(self, app, ext_name):
        ext = import_string(ext_name)
        super(ExtensionRegistry, self).register(ext_name)
        ext = getattr(ext, 'setup_app', ext)
        ext(app)

    def unregister(self):
        raise NotImplementedError()


class ImportPathRegistry(ListRegistry):
    """
    Import path registry

    Example::

        registry = ImportPathRegistry(initial=[
            'invenio.core.*',
            'invenio.modules.record',
        ])

        for impstr in registry:
            print impstr
    """
    def __init__(self, initial=None):
        super(ImportPathRegistry, self).__init__()
        if initial:
            for import_path in initial:
                self.register(import_path)

    def register(self, import_path):
        if import_path.endswith('.*'):
            for p in find_modules(import_path[:-2], include_packages=True):
                super(ImportPathRegistry, self).register(p)
        else:
            super(ImportPathRegistry, self).register(import_path)

    def unregister(self):
        raise NotImplementedError()


class ModuleRegistry(ListRegistry):
    """
    Registry for Python modules

    Each module may provide a ``setup()'' and ``teardown()'' function which
    will be called when the module is registered. The name of the methods
    can be customized by subclassing and setting the class attributes
    ``setup_func_name'' and ``teardown_func_name''.

    Any extra arguments and keyword arguments to ``register'' and
    ``unregister'' is passed to the setup and teardown functions.

    Example::
        import mod

        registry = ModuleRegistry(with_setup=True)
        registry.register(mod, arg1, arg2, kw1=...)
    """
    setup_func_name = 'setup'
    teardown_func_name = 'teardown'

    def __init__(self, with_setup=True):
        super(ModuleRegistry, self).__init__()
        self.with_setup = with_setup

    def register(self, module, *args, **kwargs):
        super(ModuleRegistry, self).register(module)
        if self.with_setup:
            setup_func = getattr(module, self.setup_func_name, None)
            if setup_func and callable(setup_func):
                setup_func(*args, **kwargs)

    def unregister(self, module, *args, **kwargs):
        super(ModuleRegistry, self).unregister(module)
        if self.with_setup:
            teardown_func = getattr(module, self.teardown_func_name, None)
            if teardown_func and callable(teardown_func):
                teardown_func(*args, **kwargs)


class PackageRegistry(ImportPathRegistry):
    """
    Specialized import path registry that takes the initial list of import
    paths from PACKAGES configuration variable.

    Example::

        app.extensions['registry']['packages'] = PackageRegistry()

        for impstr in app.extensions['registry']['packages']:
            print impstr
    """
    def __init__(self, app):
        super(PackageRegistry, self).__init__(
            initial=app.config.get('PACKAGES', [])
        )


class DiscoverRegistry(ModuleRegistry):
    """
    Python module registry with discover capabilities.

    The registry will discover module with a given name from packages specified
    in a ``PackageRegistry''.

    Example::
        app.config['PACKAGES'] = ['invenio.modules.*', ...]
        app.config['PACKAGES_VIEWS_EXCLUDE'] = ['invenio.modules.oldstuff']

        app.extensions['registry']['packages'] = PackageRegistry()
        app.extensions['registry']['views'] = DiscoverRegistry('views')
        app.extensions['registry']['views'].discover(app)

    :param module_name: Name of module to look for in packages
    :param registry_namespace: Name of registry containing the package
        registry. Defaults to ``packages''.
    :param with_setup: Call ``setup'' and ``teardown'' functions on module.
    """
    def __init__(self, module_name, registry_namespace=None, with_setup=False,
                 silent=False):

        self.module_name = module_name
        self.silent = silent
        if registry_namespace is not None and \
                isinstance(registry_namespace, (RegistryProxy, RegistryBase)):
            self.registry_namespace = registry_namespace.namespace
        else:
            self.registry_namespace = registry_namespace or 'packages'
        # Setup config variable prefix
        self.cfg_var_prefix = self.registry_namespace
        self.cfg_var_prefix.upper()
        self.cfg_var_prefix.replace('.', '_')
        super(DiscoverRegistry, self).__init__(with_setup=with_setup)

    def discover(self, app=None, *args, **kwargs):
        """
        Discover modules

        Specific modules can be excluded with the configuration variable
        ``<NAMESPACE>_<MODULE_NAME>_EXCLUDE'' (e.g PACKAGES_VIEWS_EXCLUDE).
        The namespace name is capitalized and have dots replace by underscore.

        :param module_name: Name of module to look for in packages
        :param registry_namespace: Name of registry containing the package
            registry. Defaults to ``packages''.
        :param with_setup: Call ``setup'' and ``teardown'' functions on module.
        """
        if app is None and has_app_context():
            app = current_app
        if app is None and hasattr(self, 'app'):
            app = getattr(self, 'app')
        if app is None:
            RegistryError("You must provide a Flask application.")
        self.app = app

        blacklist = app.config.get(
            '%s_%s_EXCLUDE' % (self.cfg_var_prefix, self.module_name.upper()),
            []
        )

        for pkg in app.extensions['registry'][self.registry_namespace]:
            if not isinstance(pkg, basestring):
                pkg = pkg.__name__

            if pkg in blacklist:
                continue

            self._discover_module(pkg)

    def _discover_module(self, pkg):
        import_str = pkg + '.' + self.module_name

        try:
            module = import_string(import_str, self.silent)
            self.register(module)
        except ImportError:
            pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.app.logger.error('Could not import: "%s: %s',
                                  import_str, str(e))


class AutoDiscoverRegistry(DiscoverRegistry):

    def __init__(self, module_name, app=None, *args, **kwargs):
        super(AutoDiscoverRegistry, self).__init__(module_name, *args, **kwargs)
        self.app = app
        self.discover(app=app)


class AutoDiscoverSubRegistry(AutoDiscoverRegistry):

    def _discover_module(self, pkg):
        import_str = pkg + '.' + self.module_name

        try:
            import_string(import_str)
        except ImportError:
            return

        for m in find_modules(import_str):
            try:
                module = import_string(m, silent=True)
                if module is not None:
                    self.register(module)
            except ImportError:
                pass
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.app.logger.error('Could not import: "%s: %s',
                                      import_str, str(e))

from flask import Blueprint


class BlueprintAutoDiscoveryRegistry(AutoDiscoverRegistry):
    def __init__(self, app=None, module_name=None):
        super(BlueprintAutoDiscoveryRegistry, self).__init__(
            module_name or 'views', app=app
        )

    def _discover_module(self, pkg):
        import_str = pkg + '.' + self.module_name

        try:
            view_module = import_string(import_str, self.silent)

            if 'blueprints' in dir(view_module):
                candidates = getattr(view_module, 'blueprints')
            elif 'blueprint' in dir(view_module):
                candidates = [getattr(view_module, 'blueprint')]
            else:
                candidates = []

            for candidate in candidates:
                if isinstance(candidate, Blueprint):
                    self.app.register_blueprint(
                        candidate,
                        url_prefix=self.app.config.get(
                            'BLUEPRINTS_URL_PREFIXES', {}
                        ).get(candidate.name)
                    )
                    self.register(candidate)
        except ImportError:
            pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.app.logger.error('Could not import: "%s: %s',
                                  import_str, str(e))


class PkgResourcesDiscoverRegistry(AutoDiscoverRegistry):

    def _discover_module(self, pkg):
        if pkg is not None and resource_isdir(pkg, self.module_name):
            for f in resource_listdir(pkg, self.module_name):
                self.register(os.path.join(
                    os.path.dirname(import_string(pkg).__file__),
                    self.module_name, f))


class ConfigurationRegistry(DiscoverRegistry):
    """
    Specialized import path registry that takes the initial list of import
    paths from PACKAGES configuration variable.

    Example::

        app.extensions['registry']['packages'] = PackageRegistry()
        app.extendsions['registry']['config'] = ConfigurationRegistry(
            _app, base_config='invenio.core.config'
        )
    """
    def __init__(self, app, registry_namespace=None):
        super(ConfigurationRegistry, self).__init__(
            'config',
            registry_namespace=registry_namespace,
            with_setup=False,
        )

        # Create a new configuration module to collect configuration in.
        from flask import Config
        self.new_config = Config(app.config.root_path)

        # Auto-discover configuration in packages
        self.discover(app)

        # Overwrite default configuration with user specified configuration
        self.new_config.update(app.config)
        app.config.update(self.new_config)

    def register(self, new_object):
        self.new_config.from_object(new_object)
        super(ConfigurationRegistry, self).register(new_object)

    def unregister(self, *args, **kwargs):
        raise NotImplementedError()


class EntryPointRegistry(DictRegistry):
    """
    Entry point registry

    Example::
        setup(
            entry_points = {
                'invenio.modules.pidstore.providers': [
                'doi = invenio.modules.pidstore.providers:DataCiteDOIProvider',
                'doi = invenio.modules.pidstore.providers:LocalDOIProvider',
                ]
            }
        )

        providers = RegistryProxy(__name__, EntryPointRegistry)
        for p in providers['doi']:
            myprovider = p()


    :param entry_point_ns: Namespace of entry points.
    :param load: Load entry points. Defaults to true.
    """

    def __init__(self, entry_point_ns, load=True):
        super(EntryPointRegistry, self).__init__()
        self.load = load
        for entry_point_group in iter_entry_points(iter_entry_points):
            self.register(entry_point_group)

    def register(self, entry_point):
        if entry_point.name not in self.registry:
            self.registry[entry_point.name] = []
        self.registry[entry_point.name].append(
            entry_point.load() if self.load else entry_point
        )


class RegistryProxy(LocalProxy):
    """
    Proxy object to a registry in the current app. Allows you to define your
    registry in your module without needing to initialize it first (since you
    need the Flaks application).
    """
    def __init__(self, namespace, registry_class, *args, **kwargs):
        def _lookup():
            if not 'registry' in current_app.extensions:
                raise RegistryError('Registry is not initialized.')
            if namespace not in current_app.extensions['registry']:
                current_app.extensions['registry'][namespace] = registry_class(
                    *args, **kwargs
                )
            return current_app.extensions['registry'][namespace]
        super(RegistryProxy, self).__init__(_lookup)
