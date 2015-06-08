# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""Utilities for working with DataCite metadata."""

from __future__ import absolute_import

import re
import urllib2

from invenio.utils.xmlDict import ElementTree, XmlDictConfig


__all__ = (
    'DataciteMetadata',
)


class DataciteMetadata(object):

    """Helper class for working with DataCite metadata."""

    def __init__(self, doi):
        """Initialize object."""
        self.url = "http://data.datacite.org/application/x-datacite+xml/"
        self.error = False
        try:
            data = urllib2.urlopen(self.url + doi).read()
        except urllib2.HTTPError:
            self.error = True

        if not self.error:
            # Clean the xml for parsing
            data = re.sub('<\?xml.*\?>', '', data, count=1)

            # Remove the resource tags
            data = re.sub('<resource .*xsd">', '', data)
            self.data = '<?xml version="1.0"?><datacite>' + \
                data[0:len(data) - 11] + '</datacite>'
            self.root = ElementTree.XML(self.data)
            self.xml = XmlDictConfig(self.root)

    def get_creators(self, attribute='creatorName'):
        """Get DataCite creators."""
        if 'creators' in self.xml:
            if isinstance(self.xml['creators']['creator'], list):
                return [c[attribute] for c in self.xml['creators']['creator']]
            else:
                return self.xml['creators']['creator'][attribute]

        return None

    def get_titles(self):
        """Get DataCite titles."""
        if 'titles' in self.xml:
            return self.xml['titles']['title']
        return None

    def get_publisher(self):
        """Get DataCite publisher."""
        if 'publisher' in self.xml:
            return self.xml['publisher']
        return None

    def get_dates(self):
        """Get DataCite dates."""
        if 'dates' in self.xml:
            if isinstance(self.xml['dates']['date'], dict):
                return self.xml['dates']['date'].values()[0]
            return self.xml['dates']['date']
        return None

    def get_publication_year(self):
        """Get DataCite publication year."""
        if 'publicationYear' in self.xml:
            return self.xml['publicationYear']
        return None

    def get_language(self):
        """Get DataCite language."""
        if 'language' in self.xml:
            return self.xml['language']
        return None

    def get_related_identifiers(self):
        """Get DataCite related identifiers."""
        pass

    def get_description(self, description_type='Abstract'):
        """Get DataCite description."""
        if 'descriptions' in self.xml:
            if isinstance(self.xml['descriptions']['description'], list):
                for description in self.xml['descriptions']['description']:
                    if description_type in description:
                        return description[description_type]
            elif isinstance(self.xml['descriptions']['description'], dict):
                description = self.xml['descriptions']['description']
                if description_type in description:
                    return description[description_type]
                elif len(description) == 1:
                    # return the only description
                    return description.values()[0]

        return None

    def get_rights(self):
        """Get DataCite rights."""
        if 'titles' in self.xml:
            return self.xml['rights']
        return None
