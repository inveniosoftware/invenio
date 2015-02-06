# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2015 CERN.
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

"""Manage indexer module."""

from __future__ import print_function

from invenio.ext.script import Manager

manager = Manager(usage=__doc__)

option_yes_i_know = manager.option('--yes-i-know', action='store_true',
                                   dest='yes_i_know', help='use with care!')
option_quiet = manager.option('--quiet', action='store_true',
                              dest='quiet', help='show less output')
option_namespace = manager.option(
    '-n', '--namespace', dest='namespace', action='append',
    help='Specify the namespace (e.g. -n records or -n documents')

option_fields = manager.option(
    '-f', '--fields', dest='fields', action='append',
    help='Specify the fields (e.g. -f title,author to choice title and '
    'author from all namespaces or -f records.title to specify title of '
    'namespace records')

option_exclude_fields = manager.option(
    '-e', '--exclude-fields', dest='exclude_fields', action='append',
    help='Specify the excluded fields (e.g. -e title,author')

option_range = manager.option(
    '-r', '--range', dest='range', action='append',
    help='Specify a range of ids')


@manager.command
@option_namespace
@option_fields
@option_exclude_fields
@option_yes_i_know
def create(namespace=None, fields=None, exclude_fields=None, yes_i_know=False):
    """Create indices."""
    return NotImplemented


@manager.command
@option_namespace
@option_fields
@option_exclude_fields
@option_yes_i_know
def drop(namespace=None, fields=None, exclude_fields=None, yes_i_know=False):
    """Drop indices."""
    print("drop")
    return NotImplemented


@manager.command
@option_namespace
@option_fields
@option_exclude_fields
@option_yes_i_know
def recreate(namespace=None, fields=None, exclude_fields=None, yes_i_know=False):
    """Recreate indices."""
    create(namespace=namespace, fields=fields,
           exclude_fields=exclude_fields, yes_i_know=yes_i_know)
    drop(namespace=namespace, fields=fields,
         exclude_fields=exclude_fields, yes_i_know=yes_i_know)
    return NotImplemented


@manager.command
def index(label):
    """Index indices."""
    print("index")
    return NotImplemented


@manager.command
def reindex():
    """Re-index indices."""
    print("reindex")
    return NotImplemented


@manager.command
def clear():
    """Clear indices."""
    print("clear")
    return NotImplemented


def main():
    """Execute script."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
