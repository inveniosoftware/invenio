# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2011, 2012, 2013 CERN.
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
    invenio.base.utils
    ------------------

    Implements various utils.
"""

import os
import pkg_resources
import re

from flask import has_app_context, current_app
from werkzeug.utils import import_string, find_modules
from functools import partial
from itertools import chain


def register_extensions(app):
    for ext_name in app.config.get('EXTENSIONS', []):

        ext = import_string(ext_name)
        ext = getattr(ext, 'setup_app', ext)
        #try:

        #except:
        #    continue

#        try:
        ext(app)
        #except Exception as e:
        #    app.logger.error('%s: %s' % (ext_name, str(e)))

    return app


def import_module_from_packages(name, app=None, packages=None, silent=False):
    if packages is None:
        if app is None and has_app_context():
            app = current_app
        if app is None:
            raise Exception('Working outside application context or provide app')
        #FIXME
        packages = app.config.get('PACKAGES', [])

    for package in packages:
        if package.endswith('.*'):
            for module in find_modules(package[:-2], include_packages=True):
                try:
                    yield import_string(module + '.' + name, silent)
                except ImportError:
                    pass
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    app.logger.error('Could not import: "%s.%s: %s',
                                     module, name, str(e))
                    pass
            continue
        try:
            yield import_string(package + '.' + name, silent)
        except ImportError:
            pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            app.logger.error('Could not import: "%s.%s: %s',
                             package, name, str(e))
            pass


def import_submodules_from_packages(name, app=None, packages=None,
                                    silent=False):
    discover = partial(import_module_from_packages, name)
    out = []
    for p in discover(app=app, packages=packages, silent=silent):
        if p is not None:
            for m in find_modules(p.__name__):
                try:
                    out.append(import_string(m, silent))
                except Exception as e:
                    if not silent:
                        raise e
    return out


collect_blueprints = partial(import_module_from_packages, 'views')
autodiscover_admin_views = partial(import_module_from_packages, 'admin')
autodiscover_user_settings = partial(import_module_from_packages,
                                     'user_settings')
autodiscover_configs = partial(import_module_from_packages, 'config')
autodiscover_facets = partial(import_submodules_from_packages, 'facets')
autodiscover_managers = partial(import_module_from_packages, 'manage')
autodiscover_workflows = partial(import_module_from_packages, 'workflows')
autodiscover_redirect_methods = partial(import_submodules_from_packages,
                                        'redirect_methods')
autodiscover_celery_tasks = partial(import_module_from_packages, 'tasks')
autodiscover_template_context_functions = partial(
    import_submodules_from_packages, 'template_context_functions')
autodiscover_format_elements = partial(
    import_submodules_from_packages, 'format_elements')
autodiscover_widgets = partial(import_module_from_packages, 'widgets')


def autodiscover_non_python_files(file_name, package_name, app=None, packages=None):
    """
    Helper function to autodiscover non python files that are included inside
    the package. (see MANIFEST.in)

    :param file_name: it could be a string or a regex to search for the files
    inside the package
    :type file_name: string or string regex
    :param package_name:
    :param app:
    :param packages:

    :return: List of full paths of non python files discovered
    """
    return [os.path.join(os.path.dirname(m.__file__), f)
            for m in import_module_from_packages(package_name, app, packages)
            for f in pkg_resources.resource_listdir(m.__name__, '')
            if re.match(file_name, f)]


def register_configurations(app):
    """Includes the configuration parameters of the config file.

    E.g. If the blueprint specify the config string `invenio.messages.config`
    any uppercase variable defined in the module `invenio.messages.config` is
    loaded into the system.
    """
    from flask import Config
    new_config = Config(app.config.root_path)
    for config in autodiscover_configs(app):
        new_config.from_object(config)

    new_config.update(app.config)
    app.config = new_config


def try_to_eval(string, context={}, **general_context):
    """
    This method takes care of evaluating the python expression, and, if an
    exception happens, it tries to import the needed module.

    @param string: String to evaluate
    @param context: Context needed, in some cases, to evaluate the string

    @return: The value of the expression inside string
    """
    if not string:
        return None

    res = None
    imports = []
    general_context.update(context)

    while (True):
        try:
            res = eval(string, globals().update(general_context), locals())  # kwalitee: disable=eval
        except NameError, err:
            #Try first to import using werkzeug import_string
            try:
                from werkzeug.utils import import_string
                part = string.split('.')[0]
                import_string(part)
                for i in string.split('.')[1:]:
                    part += '.' + i
                    import_string(part)
                continue
            except:
                pass

            import_name = str(err).split("'")[1]
            if not import_name in imports:
                if import_name in context:
                    globals()[import_name] = context[import_name]
                else:
                    globals()[import_name] = __import__(import_name)
                    imports.append(import_name)
                continue
            raise ImportError("Can't import the needed module to evaluate %s" (string, ))
        return res
