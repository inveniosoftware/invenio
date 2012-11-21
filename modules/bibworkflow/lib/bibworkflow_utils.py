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
import logging

from invenio.bibrecord import create_record
from sqlalchemy import func
from invenio.sqlalchemyutils import db
from invenio.webdeposit_model import WebDepositDraft, \
                                     WebDepositWorkflow
from invenio.pluginutils import PluginContainer
from invenio.config import CFG_PYLIBDIR

REGEXP_RECORD = re.compile("<record.*?>(.*?)</record>", re.DOTALL)


def create_objects(path_to_file):
    from invenio.bibworkflow_object import BibWorkflowObject

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


def authorize_user(user_id=None):
    def user_auth(obj, eng):
        if user_id is not None:
            obj.data['user_id'] = user_id
        else:
            from invenio.webuser_flask import current_user
            obj.data['user_id'] = current_user.get_id()
    return user_auth


def render_form(form):
    def render(obj, eng):
        uuid = eng.uuid
        # if 'user_id' in obj.data:
        #     user_id = obj.data['user_id']
        # else:
        #     from invenio.webuser_flask import current_user
        #     user_id = current_user.get_id()
        # deposition_type = obj.data['deposition_type']

        # TODO: get the current step from the object
        step = max(obj.db_obj.task_counter)  # data['step']
        form_type = form.__name__
        webdeposit_draft = WebDepositDraft(uuid=uuid,
                                  form_type=form_type,
                                  form_values={},
                                  step=step,
                                  timestamp=func.current_timestamp())
        db.session.add(webdeposit_draft)
        db.session.commit()
    return render


def wait_for_submission():
    def wait(obj, eng):
        eng.haltProcessing(msg='Waiting for form submission.')
        #obj.data['break'] = True
        #eng.current_step -= 1
    return wait


def getWorkflowDefinition(name):
    workflows = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'bibworkflow', 'workflows', '*.py'))
    return workflows.get_enabled_plugins()[name]().get_definition()


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
                print "can't set item"

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
