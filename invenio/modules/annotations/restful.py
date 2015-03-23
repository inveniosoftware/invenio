# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
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
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from flask import request
from flask_restful import abort, Resource

from invenio.modules.annotations.api import get_annotations, get_jsonld_multiple
from invenio.modules.deposit.restful import require_header


class AnnotationsListResource(Resource):

    def get(self):
        """GET method handler.

        Provides only minimal search query options and no JSON-LD export.
        Currently used only for IDentifying annotation objects.

        Request parameters are sent to MongoDB as a search query, in dictionary
        form.
        """
        annos = get_annotations(request.args.to_dict())
        return get_jsonld_multiple(annos, context={})

    @require_header('Content-Type', 'application/json')
    def post(self):
        """POST method handler.

        Allows performing complex queries and exporting annotations in JSON-LD
        format. It accepts a JSON document as input, with the following
        structure (defaults as values):
        {"query": {}       // Query to send to MongoDB, see
                           // http://docs.mongodb.org/manual/tutorial/query-documents/
         "ldexport: "full" // JSON-LD export format, can be: full, inline,
                           // compacted, expanded, flattened, framed,
                           // normalized.
         "context": "oaf"  // JSON-LD context or name/ URL of one to use for
                           // serialisation. Only "oaf" (Open Annotation) is
                           // currently supported
         "new_context": {} // new context to use for compacted format, tree
                           // tree structure for framed, options for normalised.

        Example requests:
        Get all annotation on record 1, full OA JSON-LD:
        curl invenio/api/annotations/export/ \
             -H "Content-Type: application/json" \
             --data '{"query": {"where.record": 1}, "ldexport": "full"}'

        Get specific annotation, compacted JSON-LD with field substitution:
        curl invenio/api/annotations/export/ \
             -H "Content-Type: application/json" \
             --data '{"query": {"_id": "3921323f-5849-4f47-83c4-97f048112b8f"},\
                      "ldexport": "compacted", \
                      "new_context":{"CUSTOM_BODY": "http://www.w3.org/ns/oa#hasBody"}}'

        Get specfic annotation, RDF triples in N-Quads format:
        curl invenio/api/annotations/export/ \
             -H "Content-Type: application/json" \
             --data '{"query": {"_id": "3921323f-5849-4f47-83c4-97f048112b8f"},\
                      "new_context":{"format": "application/nquads"}, \
                      "ldexport": "normalized"}'
        """
        rqj = request.json
        annos = get_annotations(rqj["query"])
        if "ldexport" in rqj:
            try:
                return get_jsonld_multiple(annos,
                                           context=rqj.get("context", "oaf"),
                                           new_context=rqj.get("new_context",
                                                               {}),
                                           format=rqj.get("ldexport", "full"))
            except:
                abort(400)
        return None

    def put(self):
        abort(405)

    def delete(self):
        abort(405)

    def head(self):
        abort(405)

    def options(self):
        abort(405)

    def patch(self):
        abort(405)


def setup_app(app, api):
    api.add_resource(AnnotationsListResource, '/api/annotations/export/',)
