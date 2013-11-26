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


import json
from flask import Blueprint, \
    request, \
    jsonify

from ..loader import deposition_types
from invenio.modules.workflows.config import CFG_WORKFLOW_STATUS
from invenio.webdeposit_utils import create_workflow,\
    get_workflow, \
    set_form_status, \
    preingest_form_data, \
    get_preingested_form_data, \
    validate_preingested_data, \
    deposit_files, \
    InvenioWebDepositNoDepositionType
from flask.ext.login import current_user
from invenio.modules.apikeys import api_key_required
from invenio.utils.json import wash_for_json

blueprint = Blueprint('webdeposit_api', __name__, url_prefix='/api/deposit',
                      template_folder='../templates',
                      static_folder='../static')


class enum(object):
    def __init__(self, **enums):
        for enum, code in enums.items():
            self.__setattr__(enum, code)

ERROR = enum(INVALID_DEPOSITION=1)


@blueprint.route('/create/<deposition_type>/', methods=['POST', 'GET'])
@api_key_required
def deposition_create(deposition_type):

    user_id = current_user.get_id()

    if deposition_type not in deposition_types:
        return False, jsonify({'error': ERROR.INVALID_DEPOSITION,
                               'message': 'Invalid deposition.'})

    workflow = create_workflow(deposition_type, user_id)
    return jsonify({'uuid': str(workflow.get_uuid())})


@blueprint.route('/set/<deposition_type>/', methods=['GET', 'POST'])
@api_key_required
def json_set(deposition_type):
    if deposition_type not in deposition_types:
        return False, jsonify({'error': ERROR.INVALID_DEPOSITION,
                               'message': 'Invalid deposition.'})

    user_id = current_user.get_id()
    uuid = request.values['uuid']
    if 'form_data' in request.values:
        form_data = request.form['form_data']
        form_data = wash_for_json(form_data)
        form_data = json.loads(form_data)
        preingest_form_data(user_id, uuid, form_data)

    if request.files:
        deposit_files(user_id, deposition_type, uuid, preingest=True)

    return 'OK'


@blueprint.route('/get/<deposition_type>/', methods=['GET'])
@api_key_required
def json_get(deposition_type):
    if request.method == 'GET':
        uuid = request.args['uuid']
        user_id = current_user.get_id()
        form_data = get_preingested_form_data(user_id, uuid)
        # edit the form_data.pop('files') and return it with the actual url of
        # the file
        return jsonify(form_data)
    else:
        return ''

@blueprint.route('/list/', methods=['GET'])
@api_key_required
def depositions_list():
    pass
    # TODO: implement this function :P


@blueprint.route('/delete/', methods=['GET'])
@api_key_required
def delete():
    pass
    # TODO: implement this function :P


@blueprint.route('/submit/<deposition_type>/', methods=['GET'])
@api_key_required
def deposition_submit(deposition_type):
    uuid = request.values['uuid']

    user_id = current_user.get_id()
    try:
        workflow = get_workflow(uuid, deposition_type)
    except InvenioWebDepositNoDepositionType:
        return jsonify
    errors = validate_preingested_data(user_id, uuid, deposition_type=None)
    if errors:
        return jsonify(errors)

    workflow_status = CFG_WORKFLOW_STATUS.RUNNING
    while workflow_status != CFG_WORKFLOW_STATUS.FINISHED:
        # Continue workflow
        workflow.run()
        set_form_status(1, uuid, CFG_WORKFLOW_STATUS.FINISHED)
        workflow_status = workflow.get_status()

    return jsonify({})
