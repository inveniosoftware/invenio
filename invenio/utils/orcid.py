# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import subprocess
from json import json

class OrcidSearch:

    def search_authors(self, query):
        query = query.replace(" ", "+")
        """
        FIXME: Don't create a process to do this!
        """
        p = subprocess.Popen("curl -H 'Accept: application/orcid+json' \
                             'http://pub.sandbox-1.orcid.org/search/orcid-bio?q=" + \
                             query + "&start=0&rows=10'", \
                             shell=True, \
                             stdout=subprocess.PIPE, \
                             stderr=subprocess.STDOUT)
        jsonResults = ""
        for line in p.stdout.readlines():
            jsonResults = line

        self.authorsDict = json.loads(jsonResults)

    def get_authors_names(self):
        author_names = []
        try:
            for author in self.authorsDict['orcid-search-results']['orcid-search-result']:
                given_name = author['orcid-profile']['orcid-bio']['personal-details']['given-names']['value']
                family_name = author['orcid-profile']['orcid-bio']['personal-details']['family-name']['value']
                name = family_name + " " + given_name
                author_names.append(name)
            return author_names
        except KeyError:
            return []
