# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
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
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from flask import g
from werkzeug.local import LocalProxy

from invenio.base.globals import cfg
from invenio.modules.jsonalchemy.wrappers import SmartJson
from invenio.modules.jsonalchemy.jsonext.engines.mongodb_pymongo import \
    MongoDBStorage
from invenio.modules.jsonalchemy.jsonext.readers.json_reader import reader

from .models import Annotation as SQLAnnotation


def get_storage_engine():
    if not hasattr(g, "annotations_storage_engine"):
        g.annotations_storage_engine = \
            MongoDBStorage(SQLAnnotation.__name__,
                           host=cfg["CFG_ANNOTATIONS_MONGODB_HOST"],
                           port=cfg["CFG_ANNOTATIONS_MONGODB_PORT"],
                           database=cfg["CFG_ANNOTATIONS_MONGODB_DATABASE"])
    return g.annotations_storage_engine


class Annotation(SmartJson):
    storage_engine = LocalProxy(get_storage_engine)

    @classmethod
    def create(cls, data, model='annotation', verbose=False):
        parsed = reader(data, model=model, namespace="annotationsext")
        dic = cls(parsed.translate())
        uuid = cls.storage_engine.save_one(dic.dumps())
        if verbose:
            del dic["__meta_metadata__"]
            print dic
        return uuid

    @classmethod
    def search(cls, query):
        return cls.storage_engine.search(query)


def add_annotation(model='annotation', **kwargs):
    Annotation.create(kwargs, model)


def get_annotations(which):
    return Annotation.search(which)
