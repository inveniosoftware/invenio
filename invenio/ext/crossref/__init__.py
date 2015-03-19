# -*- coding: utf-8 -*-
#
# This file is part of Invenio
# Copyright (C) 2014, 2015 CERN.
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
# along with Invenio; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CrossRef extension.

CrossRef extension is initialized like this:

>>> from flask import Flask
>>> from invenio.ext.crossref import CrossRef
>>> app = Flask("myapp")
>>> ext = CrossRef(app=app)

Configuration Settings
----------------------
The details of the CrossRef URL and endpoint can be customized in the application
settings.

========================= =====================================================
`CROSSREF_API_URL`        The URL of CrossRef query API.
                          **Default:** `http://api.crossref.org/works`
`CROSSREF_ENDPOINT`       The name of Flask endpoint for new application route.
                          If the value is `False` (or `None`) the url rule is
                          not registered.  **Default:** `_crossref.search`
`CROSSREF_URL_RULE`       The URL for `CROSSREF_ENPOINT` (i.e.
                          `url_for(current_app.config['CROSSREF_ENDPOINT'])`
                          is equal TO `current_app.config['CROSSREF_ENDPOINT']`
                          ). **Default:** `/crossref/search`
`CROSSREF_SEARCH_PREFIX`  The prefix used to perform the database search.
========================= =====================================================

"""

from __future__ import absolute_import

import requests
from urlparse import urljoin

from flask import current_app, request, jsonify
from flask_login import login_required

response_code = {'success': 200,
                 'notfound': 404,
                 'malformed': 422,
                 'multiplefound': 300}


class CrossRef(object):

    """CrossRef extension implementation.

    Initialization of the extension:

    >>> from flask import Flask
    >>> from invenio.ext.crossref import CrossRef
    >>> app = Flask("myapp")
    >>> ext = CrossRef(app=app)

    or alternatively using the factory pattern:

    >>> app = Flask("myapp")
    >>> ext = CrossRef()
    >>> ext.init_app(app)
    """

    def __init__(self, app=None):
        """Initialize extension."""
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize a Flask application."""
        app.config.setdefault("CROSSREF_API_URL",
                              "http://api.crossref.org/works/")
        app.config.setdefault("CROSSREF_ENDPOINT", "_doi.search")
        app.config.setdefault("CROSSREF_URL_RULE", "/doi/search")

        # Follow the Flask guidelines on usage of app.extensions
        if not hasattr(app, "extensions"):
            app.extensions = {}
        if "crossref" in app.extensions:
            raise RuntimeError("Flask application already initialized")
        app.extensions["crossref"] = self

        if app.config["CROSSREF_ENDPOINT"]:
            app.add_url_rule(app.config["CROSSREF_URL_RULE"],
                             app.config["CROSSREF_ENDPOINT"],
                             login_required(self.search))

    def get_response(self, crossref_doi):
        """Get CrossRef response from the ``CROSSREF_API_URL`` page."""
        response = requests.get(
            urljoin(
                current_app.config["CROSSREF_API_URL"],
                "{term}".format(term=crossref_doi.strip()),
            ),
        )
        return response

    def get_json(self, doi):
        """Get CrossRef json data."""
        response = self.get_response(doi)
        data, query = {}, {}

        if response.status_code == 200:
            if 'message' in response.json():
                query = response.json().get('message')
            else:
                query = response.json()
            data["status"] = "success"
        elif response.status_code == 404:
            data["status"] = "notfound"

        data["source"] = "crossref"
        data["query"] = query

        return data

    def search(self, doi=None):
        """Search for given DOI."""
        doi = (self.app.config.get("CROSSREF_SEARCH_PREFIX", "") + doi if doi
               else request.args.get("doi"))

        from invenio.modules.records.utils import get_unique_record_json

        # query the database
        result = get_unique_record_json(doi)
        if result["status"] == "notfound":
            # query crossref
            result = self.get_json(doi)

        resp = jsonify(result)
        resp.status_code = response_code.get(result['status'], 200)
        return resp

__all__ = ("CrossRef", )
