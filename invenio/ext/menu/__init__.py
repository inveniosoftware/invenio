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
    invenio.ext.menualchemy
    ----
    This extension allows creation of menus organised in a tree structure.
    Those menus can be then displayed using templates.
"""

from flask import url_for, current_app
from werkzeug import LocalProxy

CONDITION_TRUE = (lambda: True)
CONDITION_FALSE = (lambda: False)


class MenuAlchemy(object):
    """Extension object for invenio.ext.menualchemy"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.extensions['menualchemy'] = MenuEntryMixin('', None)
        app.context_processor(lambda: dict(
            current_menu=current_menu))

    config = {}

    @staticmethod
    def root():
        """
        :return: Root entry of current application's menu.
        """
        return current_app.extensions['menualchemy']

    @staticmethod
    def register_menu(blueprint, path, text, order=0,
                      endpoint_arguments_constructor=None,
                      dynamic_list_constructor=None,
                      active_when=CONDITION_FALSE,
                      visible_when=CONDITION_TRUE):
        """Decorate endpoints that should be displayed in a menu.

        Example::

            @register_menu(blueprint, '.', _('Your Tags'))
            def index():
                pass

        :param blueprint: Blueprint which owns the function.
        :param path: Path to this item in menu hierarchy,
            for example 'main.category.item'. Path can be an object
            with custom __str__ method: it will be converted on first request,
            therefore you can use current_app inside this __str__ method.
        :param text: Text displayed as link.
        :param order: Index of item among other items in the same menu.
        :param endpoint_arguments_constructor: Function returning dict of
            arguments passed to url_for when creating the link.
        :param active_when: Function returning True when the item
            should be displayed as active.
        :param visible_when: Function returning True when this item
            should be displayed.
        :param dynamic_list_constructor: Function returning a list of
            entries to be displayed by this item. Every object should
            have 'text' and 'url' properties/dict elements. This property
            will not be directly affect the menu system, but allows
            other systems to use it while rendering.
        """

        #Decorator function
        def menu_decorator(f):
            endpoint = blueprint.name + '.' + f.__name__

            @blueprint.before_app_first_request
            def _register_menu_item():
                # str(path) allows path to be a string-convertible object
                # that may be useful for delayed evaluation of path
                item = current_menu.submenu(str(path))
                item.register(
                    endpoint,
                    text,
                    order,
                    endpoint_arguments_constructor=endpoint_arguments_constructor,
                    dynamic_list_constructor=dynamic_list_constructor,
                    active_when=active_when,
                    visible_when=visible_when)
            return f

        return menu_decorator


class MenuEntryMixin(object):
    """Represents a entry node in the menu tree.

    Provides information for displaying links (text, url, visible, active).
    Navigate the hierarchy using :meth:`children` and :meth:`submenu`.
    """

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

        self._child_entries = dict()
        self._endpoint = None
        self._text = None
        self._order = 0
        self._endpoint_arguments_constructor = None
        self._dynamic_list_constructor = None
        self._active_when = CONDITION_FALSE
        self._visible_when = CONDITION_TRUE

    def register(self, endpoint, text, order=0,
                 endpoint_arguments_constructor=None,
                 dynamic_list_constructor=None,
                 active_when=CONDITION_FALSE,
                 visible_when=CONDITION_TRUE):
        """Assigns endpoint and display values."""
        self._endpoint = endpoint
        self._text = text
        self._order = order
        self._endpoint_arguments_constructor = endpoint_arguments_constructor
        self._dynamic_list_constructor = dynamic_list_constructor
        self._active_when = active_when or CONDITION_FALSE
        self._visible_when = visible_when or CONDITION_TRUE

    def submenu(self, path, auto_create=True):
        """Returns submenu placed at the given path in the hierarchy.

        If it does not exist, a new one is created.
        Returns None if path string is invalid.

        :param path: Path to submenu as a string 'qua.bua.cua'
        :param auto_create: If True, missing entries will be created
            to satisfy the given path.
        :return: Submenu placed at the given path in the hierarchy.
        """

        if not path:
            return self

        (path_head, dot, path_tail) = path.partition('.')

        # Create the entry if it does not exist
        if path_head not in self._child_entries:
            if auto_create:
                # The entry was not found so create a new one
                self._child_entries[path_head] = \
                    MenuEntryMixin(path_head, self)
            else:
                # The entry was not found, but we are forbidden to create
                return None

        next_entry = self._child_entries[path_head]

        if path_tail:
            return next_entry.submenu(path_tail, auto_create)
        else:
            # that was the last part of the path
            return next_entry

    def list_path(self, from_path, to_path):
        """
            Lists all items on path between two specified entries,
            if one of them is an ancestor of the other.

            :param from_path: The ancestor entry.
            :param to_path: The child entry.

            :return: List of entries between those items or None if
                they are on different branches.
        """

        ancestor_entry = self.submenu(from_path)
        child_entry = self.submenu(to_path)

        if not (ancestor_entry and child_entry):
            # Incorrect paths
            return None

        branch_list = [child_entry]
        while (child_entry.parent is not None) \
                and (child_entry != ancestor_entry):
            child_entry = child_entry.parent
            branch_list.append(child_entry)

        # This means the search reached root, but the ancestor
        # was not encountered. Therefore, entries are on different branches.
        if branch_list[-1] != ancestor_entry:
            return None
        else:
            branch_list.reverse()
            return branch_list

    def hide(self):
        """Makes the entry always hidden."""
        self._visible_when = CONDITION_FALSE

    @property
    def dynamic_list(self):
        """ Extends this entry into a list if the
            dynamic list constructor was specified"""
        if self._dynamic_list_constructor:
            return self._dynamic_list_constructor()
        else:
            return [self]

    @property
    def order(self):
        return self._order

    @property
    def children(self):
        return sorted(self._child_entries.values(),
                      key=lambda entry: getattr(entry, 'order', 0))

    @property
    def text(self):
        return self._text or 'Menu item not initialised'

    @property
    def url(self):
        if not self._endpoint:
            return '#'

        if self._endpoint_arguments_constructor:
            return url_for(self._endpoint,
                           **self._endpoint_arguments_constructor())
        return url_for(self._endpoint)

    @property
    def active(self):
        return self._active_when()

    @property
    def visible(self):
        return self._text is not None and self._visible_when()


## Global object that is proxy to the current application menu.
current_menu = LocalProxy(MenuAlchemy.root)

## Decorator for menu item registration.
register_menu = MenuAlchemy.register_menu

def setup_app(app):
    """Creates a menu instance attached to the application."""
    MenuAlchemy(app)
    return app

__all__ = ['current_menu', 'register_menu', 'MenuAlchemy', 'setup_app']
