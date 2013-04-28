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
"""Holding Pen & BibWorkflow web interface"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from flask import render_template
from pprint import pformat
from invenio.bibworkflow_model import Workflow, WfeObject
from invenio.bibworkflow_api import run
import os
from invenio.pluginutils import PluginContainer
from invenio.config import CFG_PYLIBDIR, CFG_LOGDIR
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.bibworkflow_utils import getWorkflowDefinition
from invenio.bibholdingpen_item import HoldingPenItem

import traceback

blueprint = InvenioBlueprint('bibworkflow', __name__,
                             url_prefix="/admin/bibworkflow",
                             menubuilder=[('main.admin.bibworkflow',
                                           _('BibWorkflow'),
                                          'bibworkflow.index')],
                             breadcrumbs=[(_('Administration'),
                                           'help.admin'),
                                          (_('BibWorkflow'),
                                           'bibworkflow.index')],)


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_templated('bibworkflow_index.html')
def index():
    """
    Dispalys main interface of BibWorkflow.
    """
    w = Workflow.query.all()
    return dict(workflows=w)


@blueprint.route('/entry_details', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'entry_id': (int, 0)})
def entry_details(entry_id):
    """
    Dispalys entry details.
    """
    wfe_object = WfeObject.query.filter(WfeObject.id == entry_id).first()
    try:
        #object_210_w_18
        f = open(CFG_LOGDIR + "/object_" + str(wfe_object.id) + "_w_" +
                 str(wfe_object.workflow_id) + ".log", "r")
        logtext = f.read()
    except IOError:
        # no file
        logtext = ""

    return render_template('bibworkflow_entry_details.html',
                           entry=wfe_object, log=logtext,
                           data_preview=_entry_data_preview(wfe_object.data, 'hd'),
                           workflow_func=getWorkflowDefinition(wfe_object.bwlWORKFLOW.name))


@blueprint.route('/workflow_details', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'workflow_id': (unicode, "")})
def workflow_details(workflow_id):
    w_metadata = Workflow.query.filter(Workflow.uuid == workflow_id).first()

    try:
        f = open(CFG_LOGDIR + "/workflow_" + str(workflow_id) + ".log", "r")
        logtext = f.read()
    except IOError:
        # no file
        logtext = ""

    return render_template('bibworkflow_workflow_details.html',
                           workflow_metadata=w_metadata,
                           log=logtext,
                           workflow_func=getWorkflowDefinition(w_metadata.name))


@blueprint.route('/workflows', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_templated('bibworkflow_workflows.html')
def workflows():
    loaded_workflows = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio',
                                       'bibworkflow', 'workflows', '*.py'))
    open(os.path.join(CFG_LOGDIR, 'broken-bibworkflow-workflows.log'), 'w').\
        write(pformat(loaded_workflows.get_broken_plugins()))

    return dict(workflows=loaded_workflows.get_enabled_plugins(),
                broken_workflows=loaded_workflows.get_broken_plugins())


@blueprint.route('/run_workflow', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'workflow_name': (unicode, ""), 'extra_save': (unicode, "")})
def run_workflow(workflow_name, extra_save):
    try:
        data = open('test_record2').read()
        data = [{'data': data}]

        external_save = None
        if(extra_save == 'hp'):
            external_save = HoldingPenItem
        run(workflow_name, data, external_save=external_save)
    except:
        traceback.print_exc()
    return "Workflow has been started."


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'oid': (int, 0),
                                'format': (unicode, 'default')})
def entry_data_preview(oid, format):
    workflow_object = WfeObject.query.filter(WfeObject.id == oid).first()
    return _entry_data_preview(workflow_object.data, format)


def _entry_data_preview(data, format='default'):
    if format == 'hd' or format == 'xm':
        from invenio.bibformat import format_record
        try:
            data['record'] = format_record(recID=None, of=format,
                                           xml_record=data['record'])
        except:
            print "This is not a XML string"
    try:
        return data['record']
    except:
        return data
