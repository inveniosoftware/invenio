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
"""Holding Pen & BibWorkflow web interface"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from flask import render_template, Blueprint
from flask.ext.login import login_required
from ..models import Workflow, BibWorkflowObject
from invenio.base.i18n import _
from invenio.base.decorators import wash_arguments, templated
from invenio.ext.breadcrumb import default_breadcrumb_root, register_breadcrumb
from invenio.ext.menu import register_menu
from invenio.bibworkflow_api import start_delayed
from invenio.bibworkflow_load_workflows import workflows
from invenio.bibworkflow_utils import (get_workflow_definition,
                                       get_redis_keys as utils_get_redis_keys,
                                       filter_holdingpen_results)

import traceback

blueprint = Blueprint('bibworkflow', __name__, url_prefix="/admin/bibworkflow",
                      template_folder='../templates',
                      static_folder='../static')

default_breadcrumb_root(blueprint, '.admin.bibworkflow')


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@login_required
@register_breadcrumb(blueprint, '.', _('Workflows'))
@templated('workflows/index.html')
def index():
    """
    Dispalys main interface of BibWorkflow.
    """
    w = Workflow.query.all()
    filter_keys = utils_get_redis_keys()
    return dict(workflows=w, filter_keys=filter_keys)


@blueprint.route('/entry_details', methods=['GET', 'POST'])
@login_required
@wash_arguments({'id_entry': (int, 0)})
def entry_details(id_entry):
    """
    Displays entry details.
    """
    wfe_object = BibWorkflowObject.query.filter(BibWorkflowObject.id == id_entry).first()

    return render_template('workflows/entry_details.html',
                           entry=wfe_object, log="",
                           data_preview=_entry_data_preview(wfe_object.data, 'hd'),
                           workflow_func=get_workflow_definition(wfe_object.bwlWORKFLOW.name))


@blueprint.route('/workflow_details', methods=['GET', 'POST'])
@login_required
@wash_arguments({'id_workflow': (unicode, "")})
def workflow_details(id_workflow):
    w_metadata = Workflow.query.filter(Workflow.uuid == id_workflow).first()

    return render_template('workflows/workflow_details.html',
                           workflow_metadata=w_metadata,
                           log="",
                           workflow_func=get_workflow_definition(w_metadata.name))


@blueprint.route('/workflows', methods=['GET', 'POST'])
@login_required
@templated('workflows/workflows.html')
def show_workflows():
    return dict(workflows=workflows)


@blueprint.route('/run_workflow', methods=['GET', 'POST'])
@login_required
@wash_arguments({'workflow_name': (unicode, "")})
def run_workflow(workflow_name, data={"data": 10}):
    try:
        print "Starting workflow '%s'" % (workflow_name,)
        start_delayed(workflow_name, data)
    except:
        traceback.print_exc()
    return "Workflow has been started."


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
@login_required
@wash_arguments({'oid': (int, 0),
                 'of': (unicode, 'default')})
def entry_data_preview(oid, of):
    workflow_object = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                                     oid).first()
    return _entry_data_preview(workflow_object.data, of)


@blueprint.route('/get_redis_keys', methods=['GET', 'POST'])
@login_required
@wash_arguments({'key': (unicode, "")})
def get_redis_keys(key):
    keys = utils_get_redis_keys(str(key))
    options = ""
    for key in keys:
        options += "<option>%s</option>" % (key,)
    return options


@blueprint.route('/get_redis_values', methods=['GET', 'POST'])
@login_required
@wash_arguments({'key': (unicode, "")})
def get_redis_values(key):
    keys = key.split()
    print keys
    values = filter_holdingpen_results(*keys)
    return str(values)


def _entry_data_preview(data, of='default'):
    if format == 'hd' or format == 'xm':
        from invenio.bibformat import format_record
        try:
            data['record'] = format_record(recID=None, of=of,
                                           xml_record=data['record'])
        except:
            print "This is not a XML string"
    try:
        return data['record']
    except:
        return data
