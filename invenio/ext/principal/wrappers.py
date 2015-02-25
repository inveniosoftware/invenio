# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

"""Define action class and registry."""

import six

from werkzeug.local import LocalProxy


class ActionsRegistry(type):

    """Action registry."""

    __actions_registry__ = []

    def __init__(cls, name, bases, dct):
        """Register cls to actions registry."""
        if not dct.get('__prototype__', False):
            cls.__actions_registry__.append(cls)
        super(ActionsRegistry, cls).__init__(name, bases, dct)

    @property
    def name(cls):
        """Return lowercased action class name."""
        return cls.__name__.lower()

    @property
    def description(cls):
        """Return stripped class documentation string."""
        return cls.__doc__.strip()

actions = LocalProxy(lambda: ActionsRegistry.__actions_registry__)
"""List of registered actions."""


@six.add_metaclass(ActionsRegistry)
class Action(object):

    """Default action description."""

    __prototype__ = True  # do not register this class

    allowedkeywords = []

    optional = False
