## This file is part of Invenio.
## Copyright (C) 2012 CERN.
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

import os
import re

from invenio.bibrecord import create_record
from invenio.pluginutils import PluginContainer
from invenio.config import CFG_PYLIBDIR
from invenio.errorlib import register_exception

REGEXP_RECORD = re.compile("<record.*?>(.*?)</record>", re.DOTALL)


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


def getWorkflowDefinition(name):
    workflows = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'bibworkflow', 'workflows', '*.py'))
    return workflows.get_enabled_plugins()[name]().get_definition()

def determineDataType(data):
    # If data is a dictionary and contains type key,
    # we can directly derive the data_type
    if isinstance(data, dict):
        if data.has_key('type'):
            data_type = data['type']
        else:
            data_type = 'dict'
    else:
        from magic import Magic
        mime_checker = Magic(mime=True)

        # If data is not a dictionary, we try to guess MIME type
        # by using magic library
        try:
            data_type = mime_checker.from_buffer(data)
        except:
            register_exception(stream="warning", prefix="BibWorkflowObject.determineDataType: Impossible to resolve data type.")
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
