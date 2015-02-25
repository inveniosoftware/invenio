# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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

from invenio.base.globals import cfg
from invenio.modules.jsonalchemy.reader import Reader
from invenio.modules.jsonalchemy.wrappers import SmartJsonLD


class QueryIterator():

    def __init__(self, cls, cursor):
        self.cursor = cursor
        self.i = -1
        self.cls = cls

    def __iter__(self):
        return self

    def next(self):
        self.i += 1
        if self.i >= self.cursor.count():
            raise StopIteration
        else:
            return self.cls(self.cursor[self.i])

    def count(self):
        return self.cursor.count()

    def __getitem__(self, i):
        return self.cls(self.cursor[i])


class Annotation(SmartJsonLD):

    __storagename__ = 'annotations'

    @classmethod
    def create(cls, data, model='annotation'):
        dic = Reader.translate(data, cls, model=model, master_format='json',
                               namespace="annotationsext")
        cls.storage_engine.save_one(dic.dumps())
        return dic

    @classmethod
    def search(cls, query):
        return QueryIterator(cls, cls.storage_engine.search(query))

    def translate(self, context_name, ctx):
        dump = self.dumps()
        res = {}
        if context_name == "oaf":
            from invenio.modules.accounts.models import User

            res["@id"] = cfg["CFG_SITE_URL"] + \
                "/api/annotations/export/?_id=" + \
                dump["_id"]
            res["@type"] = "oa:Annotation"

            u = User.query.filter(User.id == dump["who"]).one()
            res["annotatedBy"] = {
                "@id": cfg["CFG_SITE_URL"] +
                "/api/accounts/account/?id=" +
                str(u.id),
                "@type": "foaf:Person",
                "name": u.nickname,
                "mbox": {"@id": "mailto:" + u.email}}

            if "annotation" in self.model_info["names"]:
                res["hasTarget"] = {
                    "@type": ["cnt:ContentAsXML", "dctypes:Text"],
                    "@id": cfg["CFG_SITE_URL"] + dump["where"],
                    "cnt:characterEncoding": "utf-8",
                    "format": "text/html"}
            elif "annotation_note" in self.model_info["names"]:
                res["hasTarget"] = {
                    "@id": "oa:hasTarget",
                    "@type": "oa:SpecificResource",
                    "hasSource": cfg["CFG_SITE_URL"] + "/record/" +
                    str(dump["where"]["record"]),
                    "hasSelector":  {
                        "@id": "oa:hasSelector",
                        "@type": "oa:FragmentSelector",
                        "value": dump["where"]["marker"],
                        "dcterms:conformsTo": cfg["CFG_SITE_URL"] +
                        "/api/annotations/notes_specification"}}

            res["motivatedBy"] = "oa:commenting"

            res["hasBody"] = {
                "@id": "oa:hasBody",
                "@type": ["cnt:ContentAsText", "dctypes:Text"],
                "chars": dump["what"],
                "cnt:characterEncoding": "utf-8",
                "format": "text/plain"}

            res["annotatedAt"] = dump["when"]
            return res
        raise NotImplementedError


def get_jsonld_multiple(annos, context="oaf", new_context={}, format="full"):
    return [a.get_jsonld(context=context, new_context=new_context,
                         format=format) for a in annos]


def add_annotation(model='annotation', **kwargs):
    return Annotation.create(kwargs, model)


def get_annotations(which):
    return Annotation.search(which)


def get_count(uid, target):
    private = 0
    if uid:
        private = get_annotations({"where": target,
                                   "who": uid,
                                   "perm":
                                   {"public": False, "groups": []}}).count()
    public = get_annotations({"where": target,
                              "perm": {"public": True, "groups": []}}).count()
    return {"public": public, "private": private, "total": public+private}
