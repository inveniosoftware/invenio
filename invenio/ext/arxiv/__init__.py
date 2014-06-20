# -*- coding: utf-8 -*-
##
## This file is part of Invenio
## Copyright (C) 2014 CERN.
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
## along with Invenio; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Arxiv extension.

Arxiv extension is initialized like this:

>>> from flask import Flask
>>> from invenio.ext.arxiv import Arxiv
>>> app = Flask("myapp")
>>> ext = Arxiv(app=app)

Configuration Settings
----------------------
The details of the ArXiv URL and endpoint can be customized in the application
settings.

================= ============================================================
`ARXIV_API_URL`   The URL of ArXiV query API.
                  **Default:** `https://export.arxiv.org/api/query`
`ARXIV_ENDPOINT`  The name of Flask endpoint for new application route.
                  If the value is `False` (or `None`) the url rule is not
                  registered.  **Default:** `_arxiv.search`
`ARXIV_URL_RULE`  The URL for `ARXIV_ENPOINT` (i.e.
                  `url_for(current_app.config['ARXIV_ENDPOINT'])` is equal to
                  `current_app.config['ARXIV_ENDPOINT']`).
                  **Default:** `/arxiv/search`
================= ============================================================

"""

from __future__ import absolute_import

import requests

from flask import current_app, request, jsonify
from flask.ext.login import login_required
from lxml.etree import fromstring

from invenio.utils.xmlhelpers import etree_to_dict


class Arxiv(object):

    """Arxiv extension implementation.

    Initialization of the extension:

    >>> from flask import Flask
    >>> from invenio.ext.arxiv import Arxiv
    >>> app = Flask("myapp")
    >>> ext = Arxiv(app=app)

    or alternatively using the factory pattern:

    >>> app = Flask("myapp")
    >>> ext = Arxiv()
    >>> ext.init_app(app)
    """

    def __init__(self, app=None):
        """Initialize extension."""
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize a Flask application."""
        app.config.setdefault("ARXIV_API_URL",
                              "https://export.arxiv.org/api/query")
        app.config.setdefault("ARXIV_ENDPOINT", "_arxiv.search")
        app.config.setdefault("ARXIV_URL_RULE", "/arxiv/search")

        # Follow the Flask guidelines on usage of app.extensions
        if not hasattr(app, "extensions"):
            app.extensions = {}
        if "arxiv" in app.extensions:
            raise RuntimeError("Flask application already initialized")
        app.extensions["arxiv"] = self

        if app.config["ARXIV_ENDPOINT"]:
            app.add_url_rule(app.config["ARXIV_URL_RULE"],
                             app.config["ARXIV_ENDPOINT"],
                             login_required(self.search))

    def get_response(self, arxiv_id, max_results=1):
        """Get ArXiv response from the ``ARXIV_API_URL`` page."""
        response = requests.get(
            current_app.config["ARXIV_API_URL"],
            params=dict(
                search_query="all:{term}".format(term=arxiv_id.strip()),
                max_results=max_results
            ),
        )
        return response

    def get_json(self, arxiv_id):
        """Get ArXiv json data."""
        response = self.get_response(arxiv_id)
        data = etree_to_dict(fromstring(response.content))
        query = {}

        for d in data["feed"]:
            query.update(dict(d.items()))
        del data["feed"]

        # Check if totalResults == 0 - this means the ArXiv ID was not found
        if query["totalResults"] == "0":
            query = {}
            query["status"] = "notfound"
        else:
            for d in query["entry"]:
                query.update(dict(d.items()))
            del query["entry"]
            query["status"] = "success"

        data["source"] = "arxiv"
        data["query"] = query

        return data

    def search(self, arxiv=None):
        """Search for given ArXiv ID."""
        arxiv = arxiv or request.args.get("arxiv")

        from invenio.modules.records.utils import get_unique_record_json
        from invenio.utils.washers import remove_underscore_keys

        # query the database
        result = get_unique_record_json(arxiv)
        result["query"] = remove_underscore_keys(result["query"])
        if result["query"]["status"] == "notfound":
            # query arxiv
            result = self.get_json(arxiv)

        return jsonify(result)

__all__ = ("Arxiv", )
