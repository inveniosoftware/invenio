# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014 CERN.
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

"""Manage redirector module."""

from __future__ import print_function

from invenio.ext.script import Manager

manager = Manager(usage=__doc__)


@manager.command
@manager.option("-u", "--update", dest="update_redirection",
                action="store_true")
def create(label, plugin, parameters, update_redirection=False):
    """Register redirection page."""
    from invenio.utils.json import json, json_unicode_to_utf8
    from .api import register_redirection

    parameters = json_unicode_to_utf8(json.loads(parameters))
    register_redirection(label, plugin, parameters, update_redirection)


@manager.command
def read(label):
    """Return all information about an redirection."""
    import json
    from .api import get_redirection_data
    for k, v in sorted(get_redirection_data(label).items()):
        if k != 'parameters':
            print("{0}: {1}".format(k, v))
        else:
            print("{0}: {1}".format(k, json.dumps(v)))


@manager.command
@manager.option("-p", "--parameters", dest="parameters")
def update(label, plugin, parameters=None):
    """Update an existing redirection."""
    from invenio.utils.json import json, json_unicode_to_utf8
    from .api import update_redirection
    parameters = parameters or '{}'
    parameters = json_unicode_to_utf8(json.loads(parameters))
    update_redirection(label, plugin, parameters)


@manager.command
def delete(label):
    """Delete an existing redirection."""
    from .api import drop_redirection
    drop_redirection(label)


@manager.command
def list():
    """Get a list of available plugins."""
    from .registry import redirect_methods
    for key in redirect_methods:
        print(key)


def main():
    """Execute script."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
