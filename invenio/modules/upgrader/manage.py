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

from invenio.ext.script import Manager

manager = Manager(usage="Perform upgrade engine operations.")


@manager.command
def run():
    """
    Command for applying upgrades
    """
    from invenio.modules.upgrader.commands import cmd_upgrade
    cmd_upgrade()


@manager.command
def check():
    """
    Command for checking upgrades
    """
    from invenio.modules.upgrader.commands import cmd_upgrade_check
    cmd_upgrade_check()


show = Manager(usage="Display pending or applied upgrades.")
manager.add_command("show", show)


@show.command
def pending():
    """
    Command for showing upgrades ready to be applied
    """
    from invenio.modules.upgrader.commands import cmd_upgrade_show_pending
    cmd_upgrade_show_pending()


@show.command
def applied():
    """
    Command for showing all upgrades already applied.
    """
    from invenio.modules.upgrader.commands import \
        cmd_upgrade_show_applied
    cmd_upgrade_show_applied()


create = Manager(usage="Display pending or applied upgrades.")
manager.add_command("create", create)


@create.option('-p', '--path', dest='path')
@create.option('-r', '--repository', dest='repository', default='invenio')
def release(path, repository):
    """
    Create a new release upgrade recipe (for developers).
    """
    from invenio.modules.upgrader.commands import \
        cmd_upgrade_create_release_recipe
    cmd_upgrade_create_release_recipe(path, repository)


@create.option('-p', '--package', dest='package', required=True,
               help="Import path of module where to create recipe (required).")
@create.option('-o', '--path', dest='output_path',
               help="Override output path.")
@create.option('-r', '--repository', dest='repository',
               help="Override repository name")
@create.option('-n', '--name', dest='name',
               help="Name of upgrade file")
@create.option('-d', '--depends_on', dest='depends_on',
               help="List of recipes to depend on.")
@create.option('-a', '--auto', dest='auto', action='store_true',
               help="Auto-generate upgrade (default: False).")
@create.option('--release', dest='release', action='store_true')
@create.option('--overwrite', dest='overwrite', action='store_true')
def recipe(package, repository=None, depends_on=None, release=False,
           output_path=None, auto=False, overwrite=False, name=None):
    """
    Create a new upgrade recipe (for developers).
    """
    from invenio.modules.upgrader.commands import \
        cmd_upgrade_create_standard_recipe
    cmd_upgrade_create_standard_recipe(
        package,
        depends_on=depends_on,
        repository=repository,
        release=release,
        output_path=output_path,
        auto=auto,
        overwrite=overwrite,
        name=name,
    )


def main():
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
