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

"""Module importer from dict for indexerext configuration."""

from . import IndexerConfigurationImporter
from ..config import IndexFactory, IndexerConfiguration, VirtualIndex


class DictIndexerConfigurationImporter(IndexerConfigurationImporter):

    """Import indexer configuration from dict."""

    def __init__(self, conf, factory=None):
        """Load dict.

        :param conf: dict configuration.
        :param factory: a IndexFactory object
        """
        self.factory = factory or IndexFactory()
        self.conf = conf

    def load(self):
        """Load configuration.

        :return: indexer configuration
        """
        indices = []
        for (name, index) in self.conf['indices'].iteritems():
            index['name'] = name
            index_class = self.factory.get_index()
            indices.append(index_class(**index))

        virtual_indices = []
        for (name, virtual_index) in self.conf['virtual_indices'].iteritems():
            # search index objects
            indices_of_vi = {}
            for index_name in virtual_index['indices']:
                index = next((i for i in indices if i.name == index_name), None)
                if index:
                    indices_of_vi[index.name] = index
            virtual_index['indices'] = indices_of_vi
            virtual_index['name'] = name
            virtual_indices.append(VirtualIndex(**virtual_index))

        return IndexerConfiguration(virtual_indices=virtual_indices)
