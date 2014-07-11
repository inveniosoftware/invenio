# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2012, 2013, 2014 CERN.
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
"""
    invenio.modules.workflows.views.admin
    -------------------------------------

    Workflows admin area for an overview over available workflow
    definitions, workflows and objects created.

    WARNING: Currently not fully working.
"""

from six import text_type

from flask import Blueprint
from flask.ext.login import login_required

from invenio.base.i18n import _
from invenio.base.decorators import wash_arguments, templated
from flask.ext.breadcrumbs import default_breadcrumb_root, register_breadcrumb

from ..api import start_delayed
from ..utils import get_workflow_definition

from ..models import Workflow, BibWorkflowObject, BibWorkflowEngineLog
from ..registry import workflows

blueprint = Blueprint('workflows', __name__, url_prefix="/admin/workflows",
                      template_folder='../templates',
                      static_folder='../static')

default_breadcrumb_root(blueprint, '.workflows')


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
    return dict(workflows=w)


@blueprint.route('/details/<int:objectid>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.details', _("Record Details"))
@login_required
@templated('workflows/entry_details.html')
def details(objectid):
    """
    Displays entry details.
    """
    from flask import Markup
    from pprint import pformat

    of = "hd"

    bwobject = BibWorkflowObject.query.filter(
        BibWorkflowObject.id == objectid
    ).first()

    workflow_object = Workflow.query.filter(
        Workflow.uuid == bwobject.id_workflow
    ).first()

    workflow_tasks = get_workflow_definition(workflow_object.name)
    formatted_data = bwobject.get_formatted_data(of)
    if isinstance(formatted_data, dict):
        formatted_data = pformat(formatted_data)
    if of and of in ("xm", "xml", "marcxml"):
        data = Markup.escape(formatted_data)
    else:
        data = formatted_data

    engine_log = BibWorkflowEngineLog.query.filter(
        BibWorkflowEngineLog.id_object == workflow_object.uuid
    )
    return dict(entry=bwobject,
                log=engine_log,
                data_preview=data,
                workflow_tasks=workflow_tasks)


@blueprint.route('/workflow_details/<id_workflow>',
                 methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.workflow_details', _("Workflow Details"))
@login_required
@templated('workflows/workflow_details.html')
def workflow_details(id_workflow):
    workflow_object = Workflow.query.filter(
        Workflow.uuid == id_workflow
    ).first()

    workflow_tasks = get_workflow_definition(workflow_object.name)
    return dict(workflow_metadata=workflow_object,
                log="",
                workflow_tasks=workflow_tasks)


@blueprint.route('/workflows', methods=['GET', 'POST'])
@login_required
@templated('workflows/workflow_list.html')
def show_workflows():
    return dict(workflows=workflows)


@blueprint.route('/run_workflow', methods=['GET', 'POST'])
@login_required
@wash_arguments({'workflow_name': (text_type, "")})
def run_workflow(workflow_name, data={"data": 10}):
    start_delayed(workflow_name, data)
    return "Workflow has been started."


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
@login_required
@wash_arguments({'oid': (int, 0),
                 'of': (text_type, 'default')})
def entry_data_preview(oid, of):
    workflow_object = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                                     oid).first()
    return _entry_data_preview(workflow_object.get_data(), of)


def _entry_data_preview(data, of='default'):
    if format == 'hd' or format == 'xm':
        from invenio.modules.formatter import format_record

        data['record'] = format_record(recID=None, of=of,
                                       xml_record=data['record'])
        return data['record']
    return data
