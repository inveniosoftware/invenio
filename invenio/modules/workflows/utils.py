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

from invenio.legacy.bibrecord import create_record
from invenio.ext.logging import register_exception
from invenio.ext.sqlalchemy import db

REGEXP_RECORD = re.compile("<record.*?>(.*?)</record>", re.DOTALL)


class InvenioWorkflowDefinitionError(Exception):
    pass


def get_workflow_definition(name):
    from .loader import workflows
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

        # If data is not a dictionary, we try to guess MIME type
        # by using magic library
        try:
            from magic import Magic
            mime_checker = Magic(mime=True)
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


def redis_create_search_entry(bwobject):
    redis_server = set_up_redis()

    extra_data = bwobject.get_extra_data()
    #creates database entries to not loose key value pairs in redis

    for key, value in extra_data["redis_search"].iteritems():
        redis_server.sadd("holdingpen_sort", str(key))
        redis_server.sadd("holdingpen_sort:%s" % (str(key),), str(value))
        redis_server.sadd("holdingpen_sort:%s:%s" % (str(key), str(value),),
                          bwobject.id)

    redis_server.sadd("holdingpen_sort", "owner")
    redis_server.sadd("holdingpen_sort:owner", extra_data['owner'])
    redis_server.sadd("holdingpen_sort:owner:%s" % (extra_data['owner'],),
                      bwobject.id)
    redis_server.sadd("holdingpen_sort:last_task_name:%s" %
                     (extra_data['last_task_name'],), bwobject.id)


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


def empty_redis():
    redis_server = set_up_redis()
    redis_server.flushall()


def sort_bwolist(bwolist, iSortCol_0, sSortDir_0):
    if iSortCol_0 == 0:
        if sSortDir_0 == 'desc':
            bwolist.sort(key=lambda x: x.id, reverse=True)
        else:
            bwolist.sort(key=lambda x: x.id, reverse=False)
    elif iSortCol_0 == 1:
        pass
        # if sSortDir_0 == 'desc':
        #     bwolist.sort(key=lambda x: x.id_user, reverse=True)
        # else:
        #     bwolist.sort(key=lambda x: x.id_user, reverse=False)
    elif iSortCol_0 == 2:
        pass
        # if sSortDir_0 == 'desc':
        #     bwolist.sort(key=lambda x: x.id_user, reverse=True)
        # else:
        #     bwolist.sort(key=lambda x: x.id_user, reverse=False)
    elif iSortCol_0 == 3:
        pass
        # if sSortDir_0 == 'desc':
        #     bwolist.sort(key=lambda x: x.id_user, reverse=True)
        # else:
        #     bwolist.sort(key=lambda x: x.id_user, reverse=False)
    elif iSortCol_0 == 4:
        if sSortDir_0 == 'desc':
            bwolist.sort(key=lambda x: x.id_workflow, reverse=True)
        else:
            bwolist.sort(key=lambda x: x.id_workflow, reverse=False)
    elif iSortCol_0 == 5:
        if sSortDir_0 == 'desc':
            bwolist.sort(key=lambda x: x.id_user, reverse=True)
        else:
            bwolist.sort(key=lambda x: x.id_user, reverse=False)
    elif iSortCol_0 == 6:
        if sSortDir_0 == 'desc':
            bwolist.sort(key=lambda x: x.created, reverse=True)
        else:
            bwolist.sort(key=lambda x: x.created, reverse=False)
    elif iSortCol_0 == 7:
        if sSortDir_0 == 'desc':
            bwolist.sort(key=lambda x: x.version, reverse=True)
        else:
            bwolist.sort(key=lambda x: x.version, reverse=False)
    elif iSortCol_0 == 8:
        if sSortDir_0 == 'desc':
            bwolist.sort(key=lambda x: x.version, reverse=True)
        else:
            bwolist.sort(key=lambda x: x.version, reverse=False)
    elif iSortCol_0 == 9:
        if sSortDir_0 == 'desc':
            bwolist.sort(key=lambda x: x.version, reverse=True)
        else:
            bwolist.sort(key=lambda x: x.version, reverse=False)

    return bwolist


def parse_bwids(bwlist):
    import ast
    return [item.encode('ascii') for item in ast.literal_eval(bwlist)]
