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

import sys

from invenio.ext.script import Manager

from .indexerext.config import ElasticSearchIndexFactory, NativeIndexFactory
from .indexerext.importer.json_importer import \
    JsonIndexerConfigurationImporter


manager = Manager(usage=__doc__)

option_yes_i_know = manager.option('--yes-i-know', action='store_true',
                                   dest='yes_i_know', help='use with care!')
option_quiet = manager.option('-q', '--quiet', action='store_true',
                              dest='quiet', help='show less output')

option_load_from_file = manager.option(
    '-f', '--filename', dest="filename",
    help='Specify a configuration\'s file (json format)')

option_namespace = manager.option(
    '-n', '--namespace', dest='namespace', action='append',
    help='Specify the namespace (e.g. -n records or -n documents')

option_fields = manager.option(
    '-i', '--fields', dest='indexer_fields', action='append',
    help='Specify the fields (e.g. -f title,author to choice title and '
    'author from all namespaces or -f records.title to specify title of '
    'namespace records')

option_exclude_fields = manager.option(
    '-e', '--exclude-fields', dest='exclude_fields', action='append',
    help='Specify the excluded fields (e.g. -e title,author')

option_range = manager.option(
    '-r', '--range', dest='range', action='append',
    help='Specify a range of ids')


class IndexerManager(object):

    """Utility to manage indexer."""

    def __init__(self, indexer_name, filename):
        """Init manager.

        :param indexer_name: indexer name (e.g. native or elasticsearch)
        :param filename: file name
        """
        self.factory = self._load_factory(indexer_name=indexer_name)
        self.data = self._load_config(filename=filename)
        self.config = self._load_configuration()
        self.engine = self._load_engine()

    def _load_config(self, filename=None):
        """Load the configuration.

        :param filename: file name
        :return: raw configuration data
        """
        if filename:
            # load from file
            with open(filename, 'r') as cfile:
                data = cfile.read()
        else:
            # load from stdin
            data = ''
            for line in sys.stdin:
                data += line

        return data

    def _load_factory(self, indexer_name):
        """Load factory.

        :param indexer_name: indexer name (e.g. native or elasticsearch)
        """
        if indexer_name == 'elasticsearch':
            return ElasticSearchIndexFactory()
        else:
            return NativeIndexFactory()

    def _load_configuration(self):
        """Load configuration."""
        importer = JsonIndexerConfigurationImporter(
            json_text=self.data,
            factory=self.factory
        )
        # TODO give the possibility to choice the importer
        return importer.load()

    def _load_engine(self):
        """Return a initialized engine."""
        engine = self.factory.get_engine()
        return engine(index_configuration=self.config)


@manager.command
@option_namespace
@option_fields
@option_exclude_fields
@option_load_from_file
@option_yes_i_know
def create(indexer, namespace=None, indexer_fields=None, exclude_fields=None,
           filename=None, yes_i_know=False):
    """Create indices."""
    manager = IndexerManager(indexer_name=indexer, filename=filename)
    manager.engine.create()


@manager.command
@option_namespace
@option_fields
@option_exclude_fields
@option_load_from_file
@option_yes_i_know
def drop(indexer, namespace=None, indexer_fields=None, exclude_fields=None,
         filename=None, yes_i_know=False):
    """Drop indices."""
    # TODO implement "yes-i-know!'
    manager = IndexerManager(indexer_name=indexer, filename=filename)
    manager.engine.drop()


@manager.command
@option_namespace
@option_fields
@option_exclude_fields
@option_load_from_file
@option_yes_i_know
def recreate(indexer, namespace=None, indexer_fields=None, exclude_fields=None,
             filename=None, yes_i_know=False):
    """Recreate indices."""
    manager = IndexerManager(indexer_name=indexer, filename=filename)
    manager.engine.drop()
    manager.engine.create()


@manager.command
@option_namespace
@option_fields
@option_exclude_fields
@option_load_from_file
def index(indexer, namespace=None, indexer_fields=None, exclude_fields=None,
          filename=None, yes_i_know=False):
    """Index indices."""
    manager = IndexerManager(indexer_name=indexer, filename=filename)
    manager.engine.index()


@manager.command
@option_namespace
@option_fields
@option_exclude_fields
@option_load_from_file
def reindex(indexer, namespace=None, indexer_fields=None, exclude_fields=None,
            filename=None, yes_i_know=False):
    """Re-index indices."""
    manager = IndexerManager(indexer_name=indexer, filename=filename)
    manager.engine.reindex()


@manager.command
@option_namespace
@option_fields
@option_exclude_fields
@option_load_from_file
def clear(indexer, namespace=None, indexer_fields=None, exclude_fields=None,
          filename=None, yes_i_know=False):
    """Clear indices."""
    manager = IndexerManager(indexer_name=indexer, filename=filename)
    manager.engine.clear()


def main():
    """Execute script."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
