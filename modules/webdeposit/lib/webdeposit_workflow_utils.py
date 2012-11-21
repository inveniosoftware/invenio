# -*- coding: utf-8 -*-
##
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

from invenio.sqlalchemyutils import db
from invenio.webdeposit_model import WebDepositWorkflow
from invenio.bibworkflow_engine import BibWorkflowEngine


class JsonCookerMixin(object):
    def cook_json(self, json_reader):
        """
        This is a stub implementation.
        """
        return json_reader


def JsonCookerMixinBuilder(key):
    class CustomJsonCookerMixin(JsonCookerMixin):
        def cook_json(self, json_reader):
            value = self.data
            json_reader[key] = value
            return json_reader
    return CustomJsonCookerMixin


def create_deposition_document(deposition_type, user_id):
    def create_dep_doc(obj, eng):
        obj['deposition_type'] = deposition_type
        uuid = obj['uuid']
        temp_obj = dict(obj)
        temp_obj.pop('uuid')
        temp_obj.pop('step')

        eng = BibWorkflowEngine(name=deposition_type, uuid=uuid, module_name="webdeposit")
        eng.setWorkflow(eng.workflow)
        eng.save()
        return

        webdeposit_workflow = WebDepositWorkflow(uuid=uuid,
                                                 deposition_type=deposition_type,
                                                 user_id=user_id,
                                                 obj_json=temp_obj,
                                                 current_step=0,
                                                 status=0)
        db.session.add(webdeposit_workflow)
        db.session.commit()
    return create_dep_doc
