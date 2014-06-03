# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

import re
import redis

from invenio.bibrecord import create_record
from invenio.errorlib import register_exception
from invenio.sqlalchemyutils import db


REGEXP_RECORD = re.compile("<record.*?>(.*?)</record>", re.DOTALL)


class InvenioWorkflowDefinitionError(Exception):
    pass


def create_objects(path_to_file):
    from invenio.bibworkflow_model import BibWorkflowObject

    list_of_bwo = []
    f = open(path_to_file, "r")
    records = f.read()
    f.close()

    record_xmls = REGEXP_RECORD.findall(records)
    for record_xml in record_xmls:
        rec = "<record>"
        rec += record_xml
        rec += "</record>"
        rec = create_record(rec)[0]
        #check for errors, if record is empty

        bwo = BibWorkflowObject(rec, "bibrecord")
        list_of_bwo.append(bwo)
    return list_of_bwo


def get_workflow_definition(name):
    from invenio.bibworkflow_load_workflows import workflows
    if name in workflows:
        return workflows[name]
    else:
        raise InvenioWorkflowDefinitionError("Cannot find workflow %s"
                                             % (name,))


def determineDataType(data):
    # If data is a dictionary and contains type key,
    # we can directly derive the data_type
    if isinstance(data, dict):
        if 'type' in data:
            data_type = data['type']
        else:
            data_type = 'dict'
    else:
        from magic import Magic
        mime_checker = Magic(mime=True)

        # If data is not a dictionary, we try to guess MIME type
        # by using magic library
        try:
            data_type = mime_checker.from_buffer(data)  # noqa
        except:
            register_exception(stream="warning", prefix=
                               "BibWorkflowObject.determineDataType:" +
                               " Impossible to resolve data type.")
            data_type = ""
    return data_type


## TODO special thanks to http://code.activestate.com/recipes/440514-dictproperty-properties-for-dictionary-attributes/
class dictproperty(object):

    class _proxy(object):

        def __init__(self, obj, fget, fset, fdel):
            self._obj = obj
            self._fget = fget
            self._fset = fset
            self._fdel = fdel

        def __getitem__(self, key):
            try:
                return self._fget(self._obj, key)
            except TypeError:
                print "can't read item"

        def __setitem__(self, key, value):
            try:
                self._fset(self._obj, key, value)
            except TypeError:
                print "can't set item %s: %s" % (str(key), str(value),)

        def __delitem__(self, key):
            try:
                self._fdel(self._obj, key)
            except TypeError:
                print "can't delete item"

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self._fget = fget
        self._fset = fset
        self._fdel = fdel
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self._proxy(obj, self._fget, self._fset, self._fdel)


def create_hp_containers(iSortCol_0=None, sSortDir_0=None):
    """
    Looks for related HPItems and groups them together in HPContainers

    @type hpitems: list
    @return: A list containing all the HPContainers.
    """
    from invenio.bibworkflow_model import BibWorkflowObject

    print '-----------------------Setting up HPCONTAINERS!'

    if iSortCol_0:
        iSortCol_0 = int(iSortCol_0)

    if iSortCol_0 == 6:
        column = 'created'
        if sSortDir_0 == 'desc':
            bwobject_list = BibWorkflowObject.query.order_by(
                db.desc(column)).all()
        elif sSortDir_0 == 'asc':
            bwobject_list = BibWorkflowObject.query.order_by(db.asc(
                column)).all()

        return bwobject_list
    else:
        return BibWorkflowObject.query.filter(
            BibWorkflowObject.id_parent != 0).all()


def redis_create_search_entry(bwobject):
    redis_server = set_up_redis()

    #creates database entries to not loose key value pairs in redis
    for key, value in bwobject.extra_data["redis_search"].iteritems():
        redis_server.sadd("holdingpen_sort", str(key))
        redis_server.sadd("holdingpen_sort:%s" % (str(key),), str(value))
        redis_server.sadd("holdingpen_sort:%s:%s" % (str(key), str(value),),
                          bwobject.id)

    redis_server.sadd("holdingpen_sort", "owner")
    redis_server.sadd("holdingpen_sort:owner", bwobject.extra_data['owner'])
    redis_server.sadd("holdingpen_sort:owner:%s" % (bwobject.extra_data['owner'],),
                      bwobject.id)
    redis_server.sadd("holdingpen_sort:last_task_name:%s" % (bwobject.extra_data['last_task_name'],),
                      bwobject.id)


def filter_holdingpen_results(key, *args):
    """Function filters holdingpen entries by given key: value pair.
    It returns list of IDs."""
    redis_server = set_up_redis()
    new_args = []
    for a in args:
        new_args.append("holdingpen_sort:"+a)
    return redis_server.sinter("holdingpen_sort:"+key, *new_args)


def get_redis_keys(key=None):
    redis_server = set_up_redis()
    if key:
        return list(redis_server.smembers("holdingpen_sort:%s" % (str(key),)))
    else:
        return list(redis_server.smembers("holdingpen_sort"))


def get_redis_values(key):
    redis_server = set_up_redis()
    return redis_server.smembers("holdingpen_sort:%s" % (str(key),))


def set_up_redis():
    """
    Sets up the redis server for the saving of the HPContainers

    @type url: string
    @param url: address to setup the Redis server
    @return: Redis server object.
    """
    from flask import current_app
    redis_server = redis.Redis.from_url(
        current_app.config.get('CACHE_REDIS_URL', 'redis://localhost:6379')
    )
    return redis_server
