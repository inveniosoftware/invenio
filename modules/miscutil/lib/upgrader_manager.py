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

from flask.ext.script import Manager

manager = Manager(usage="Perform upgrade engine operations.")


@manager.command
def run():
    """
    Command for applying upgrades
    """
    from invenio import config as conf
    from invenio.inveniocfg_upgrader import cmd_upgrade
    cmd_upgrade(conf)


@manager.command
def show_pending():
    """
    Command for showing upgrades ready to be applied
    """
    from invenio import config as conf
    from invenio.inveniocfg_upgrader import cmd_upgrade_show_pending
    cmd_upgrade_show_pending(conf)


@manager.command
def show_applied():
    """
    Command for showing all upgrades already applied.
    """
    from invenio import config as conf
    from invenio.inveniocfg_upgrader import cmd_upgrade_show_applied
    cmd_upgrade_show_applied(conf)


@manager.option('-p', '--path', dest='path')
def create_release_recipe(path):
    """
    Create a new release upgrade recipe (for developers).
    """
    from invenio import config as conf
    from invenio.inveniocfg_upgrader import cmd_upgrade_create_release_recipe
    cmd_upgrade_create_release_recipe(conf, path)


@manager.option('-p', '--path', dest='path')
@manager.option('-d', '--depends_on', dest='depends_on')
@manager.option('-r', '--release', dest='release')
def create_standard_recipe(path, depends_on=None, release=False):
    """
    Create a new upgrade recipe (for developers).
    """
    from invenio import config as conf
    from invenio.inveniocfg_upgrader import cmd_upgrade_create_standard_recipe
    cmd_upgrade_create_standard_recipe(conf, path, depends_on=depends_on,
                                       release=release)


def main():
    from invenio.webinterface_handler_flask import create_invenio_flask_app
    app = create_invenio_flask_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
