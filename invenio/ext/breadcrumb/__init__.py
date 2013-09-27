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
    invenio.ext.breadcrumb
    ----------------------

    Depends on `invenio.ext.menu` extension.
"""

from werkzeug import LocalProxy
from flask import current_app
from invenio.base.globals import current_function, current_blueprint
from invenio.ext.menu import MenuAlchemy, current_menu


class BreadcrumbAlchemy(MenuAlchemy):
    """
    Breadcrumb organizer for Invenio.
    """

    config = {}

    def init_app(self, app, *args, **kwargs):
        super(self.__class__, self).init_app(app, *args, **kwargs)

        app.config.setdefault('BREADCRUMB_ROOT', 'breadcrumbs')
        app.context_processor(BreadcrumbAlchemy._breadcrumbs_context_processor)

    # Proxy functions
    @staticmethod
    def _breadcrumb_root_path():
        """
        Backend function for breadcrumb_root_path proxy.
        """
        return current_app.config.get('BREADCRUMB_ROOT')

    @staticmethod
    def _current_path():
        """
        Determines current location in menu hierarchy.
        Backend function for current_path proxy.
        """
        # str(...) because __breadcrumb__ can hold a LocalProxy
        if hasattr(current_function, '__breadcrumb__'):
            return str(getattr(current_function, '__breadcrumb__', ''))

        if current_blueprint:
            return BreadcrumbAlchemy.blueprint_get_path(current_blueprint)

        return ''

    @staticmethod
    def _breadcrumbs():
        """
        Returns list of breadcrumbs.
        Backend function for breadcrumbs proxy.
        """
        # Construct breadcrumbs using their dynamic lists
        breadcrumb_list = []

        for entry in current_menu.list_path(breadcrumb_root_path, current_path) or []:
            breadcrumb_list += entry.dynamic_list

        return breadcrumb_list

    @staticmethod
    def _breadcrumbs_context_processor():
        """Adds variable 'breadcrumbs' to template context.

        It contains the list of menu entries to render as breadcrumbs.
        """
        return dict(breadcrumbs=breadcrumbs)

    @staticmethod
    def blueprint_get_path(blueprint):
        """
        :return: Path to root of bluerpint's branch.
        """
        return str(getattr(
            blueprint,
            '__breadcrumb__',
            breadcrumb_root_path + '.' + blueprint.name))

    @staticmethod
    def default_breadcrumb_root(blueprint, path):
        """Registers the default breadcrumb path
            for all endpoints in this blueprint.

        :param path: Path in the menu hierarchy.
        Should start with '.' to be relative to breadcrumb root.
        """

        if path.startswith('.'):
            # Path relative to breadcrumb root
            bl_path = LocalProxy(lambda:
                (breadcrumb_root_path + path).strip('.'))
        else:
            bl_path = path

        blueprint.__breadcrumb__ = bl_path

    @staticmethod
    def register_breadcrumb(blueprint, path, text,
                            endpoint_arguments_constructor=None,
                            dynamic_list_constructor=None):
        """Decorate endpoints that should be displayed as a breadcrumb.

        :param blueprint: Blueprint which owns the function.
        :param path: Path to this item in menu hierarchy
            ("breadcrumbs." is automatically added).
        :param text: Text displayed as link.
        :param order: Index of item among other items in the same menu.
        :param endpoint_arguments_constructor: Function returning dict of
            arguments passed to url_for when creating the link.
        :param dynamic_list_constructor: Function returning a list of
            breadcrumbs to be displayed by this item. Every object should
            have 'text' and 'url' properties/dict elements.
        """

        # Resolve blueprint-relative paths
        if path.startswith('.'):
            def _evaluate_path():
                bl_path = BreadcrumbAlchemy.blueprint_get_path(blueprint)
                return (bl_path + path).strip('.')

            func_path = LocalProxy(_evaluate_path)

        else:
            func_path = path

        # Get standard menu decorator
        menu_decorator = MenuAlchemy.register_menu(
            blueprint, func_path, text, 0,
            endpoint_arguments_constructor=endpoint_arguments_constructor,
            dynamic_list_constructor=dynamic_list_constructor)

        def breadcrumb_decorator(f):
            """Applies standard menu decorator and assign breadcrumb."""
            f.__breadcrumb__ = func_path

            return menu_decorator(f)

        return breadcrumb_decorator

# Proxies
breadcrumb_root_path = LocalProxy(BreadcrumbAlchemy._breadcrumb_root_path)
current_path = LocalProxy(BreadcrumbAlchemy._current_path)
breadcrumbs = LocalProxy(BreadcrumbAlchemy._breadcrumbs)

# Decorators and API
default_breadcrumb_root = BreadcrumbAlchemy.default_breadcrumb_root
register_breadcrumb = BreadcrumbAlchemy.register_breadcrumb
