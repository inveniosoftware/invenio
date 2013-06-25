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
"""Holding Pen web interface"""

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

from flask import render_template
from invenio.bibworkflow_model import BibWorkflowObject, Workflow
from invenio.config import CFG_LOGDIR
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.bibworkflow_utils import getWorkflowDefinition
from invenio.bibworkflow_api import continue_oid, run
from invenio.bibworkflow_hp_load_widgets import widgets
from invenio.bibworkflow_model import Workflow

from flask import redirect, url_for, flash
from invenio.bibformat_engine import format_record

from invenio.bibworkflow_utils import create_hp_containers

blueprint = InvenioBlueprint('bibholdingpen', __name__,
                             url_prefix="/admin/bibholdingpen",
                             menubuilder=[('main.admin.bibholdingpen',
                                          _('Holdingpen'),
                                           'bibholdingpen.index')],
                             breadcrumbs=[(_('Administration'), 'help.admin'),
                                          (_('Holdingpen'),
                                           'bibholdingpen.index')])


@blueprint.route('/index', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_templated('bibholdingpen_index.html')
def index():
    """
    Displays main interface of BibHoldingpen.
    """
    containers = create_hp_containers()
    return dict(hpcontainers=containers)


@blueprint.route('/load_table', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_templated('bibholdingpen_index.html')
def load_table():
    """
    Function used for the passing of JSON data to the DataTable
    """
    from flask import request

    iDisplayStart = request.args.get('iDisplayStart')
    iDisplayLength = request.args.get('iDisplayLength')
    sSearch = request.args.get('sSearch')
    iSortCol_0 = request.args.get('iSortCol_0')
    sSortDir_0 = request.args.get('sSortDir_0')
    containers = create_hp_containers(iSortCol_0, sSortDir_0, sSearch)

    iDisplayStart = int(request.args.get('iDisplayStart'))
    iDisplayLength = int(request.args.get('iDisplayLength'))

    table_data = {
        "aaData": []
    }

    for container in containers[iDisplayStart:iDisplayStart+iDisplayLength]:
        table_data['sEcho'] = int(request.args.get('sEcho')) + 1
        table_data['iTotalRecords'] = len(containers)
        table_data['iTotalDisplayRecords'] = len(containers)
        if container.final:
            container.version = \
                '<span class="label label-success">Final</span>'
        elif container.error:
            container.version = \
                '<span class="label label-warning">Halted</span>'
        if container.widget:
            widget_link = '<a class="btn btn-info"' + \
                          'href="/admin/bibholdingpen/widget?widget=' + \
                          container.widget + \
                          '&hpcontainerid=' + \
                          str(container.id) + \
                          '"><i class="icon-wrench"></i></a>'
        else:
            widget_link = None
        table_data['aaData'].append(
            [str(container.initial.id),
             None,
             None,
             None,
             str(container.initial.workflow_id),
             str(container.current.extra_data['owner']),
             str(container.initial.created),
             str(container.version),
             '<a id="info_button" ' +
             'class="btn btn-info pull-center text-center"' +
             'href="/admin/bibholdingpen/details?hpcontainerid=' +
             str(container.id) +
             '"><i class="icon-white icon-zoom-in"></i></a>',
             widget_link,
             ])
    return table_data


@blueprint.route('/resolve_approval', methods=['GET', 'POST'])
@blueprint.invenio_wash_urlargd({'hpcontainerid': (int, 0)})
def resolve_approval(hpcontainerid):
    """
    Resolves the action taken in the approval widget
    """
    from flask import request
    if request.form['submitButton'] == 'Accept':
        continue_oid(hpcontainerid)
        flash('Record Accepted')
    elif request.form['submitButton'] == 'Reject':
        _delete_from_db(hpcontainerid)
        flash('Record Rejected')
    return redirect(url_for('bibholdingpen.index'))


@blueprint.route('/details', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'hpcontainerid': (int, 0)})
def details(hpcontainerid):
    """
    Displays info about the hpcontainer, and presents the data
    of all available versions of the object. (Initial, Error, Final)
    """
    containers = create_hp_containers()

    # search for parents
    bwobject = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              hpcontainerid).first()
    if bwobject.parent_id:
        hpcontainerid = bwobject.parent_id

    # search in the containers for our hpcontainerid
    for hpc in containers:
        if hpc.id == int(hpcontainerid):
            hpcontainer = hpc

    info = get_info(hpcontainer.current)
    try:
        info['widget'] = hpcontainer.error.extra_data['widget']
    except:
        try:
            info['widget'] = hpcontainer.final.extra_data['widget']
        except:
            pass

    w_metadata = Workflow.query.filter(Workflow.uuid ==
                                       hpcontainer.initial.workflow_id).first()
    # read the logtext from the file system
    try:
        f = open(CFG_LOGDIR + "/object_" + str(hpcontainer.initial.id)
                 + "_w_" + str(hpcontainer.initial.workflow_id) + ".log", "r")
        logtext = f.read()
    except IOError:
        logtext = ""
    return render_template('bibholdingpen_details.html',
                           hpcontainer=hpcontainer,
                           info=info, log=logtext,
                           data_preview=_entry_data_preview(
                               hpcontainer.initial.data['data']),
                           workflow_func=getWorkflowDefinition(
                               w_metadata.name))


@blueprint.route('/restart_record', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'hpcontainerid': (int, 0)})
def restart_record(hpcontainerid, start_point='beginning'):
    """
    Restarts the initial object in its workflow
    """
    workflow_id = BibWorkflowObject.query.filter(
        BibWorkflowObject.id == hpcontainerid).first().workflow_id
    wname = Workflow.query.filter(Workflow.uuid == workflow_id).first().name
    run(wname, [{'id': hpcontainerid}])
    flash('Record Restarted')
    return "Record restarted"


@blueprint.route('/restart_record_prev', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'hpcontainerid': (int, 0)})
def restart_record_prev(hpcontainerid):
    """
    Restarts the initial object in its workflow from the current task
    """
    continue_oid(hpcontainerid, "restart_task")
    return "Record restarted from previous task"


@blueprint.route('/delete_from_db', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'hpcontainerid': (int, 0)})
def delete_from_db(hpcontainerid):
    """
    Deletes all available versions of the object from the db
    """
    _delete_from_db(hpcontainerid)
    flash('Record Deleted')
    return redirect(url_for('bibholdingpen.index'))


def _delete_from_db(hpcontainerid):
    from invenio.sqlalchemyutils import db
    containers = create_hp_containers()

    for hpc in containers:
        if hpc.id == int(hpcontainerid):
            hpcontainer = hpc

    # delete every BibWorkflowObject version from the db
    BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                   hpcontainer.id).delete()
    if hpcontainer.error:
        BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                       hpcontainer.error.id).delete()
    if hpcontainer.final:
        BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                       hpcontainer.final.id).delete()

    db.session.commit()


@blueprint.route('/widget', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'hpcontainerid': (int, 0),
                                 'widget': (unicode, ' ')})
def show_widget(hpcontainerid, widget):
    """
    Renders the bibmatch widget for a specific record
    """
    bwobject = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              hpcontainerid).first()
    containers = create_hp_containers()

    for hpc in containers:
        if hpc.id == int(hpcontainerid):
            hpcontainer = hpc
    # set the WTForm of the widget
    widget_form = widgets[widget]

    if widget == 'bibmatch_widget':
        # setting up bibmatch widget
        try:
            matches = bwobject.extra_data['tasks_results']['match_record']
        except:
            bwobject = BibWorkflowObject.query.filter(
                BibWorkflowObject.parent_id == bwobject.id).first()
            matches = bwobject.extra_data['tasks_results']['match_record']

        print matches
        match_preview = []
        # adding dummy matches
        match_preview.append(BibWorkflowObject.query.filter(
            BibWorkflowObject.id == hpcontainerid).first())
        match_preview.append(BibWorkflowObject.query.filter(
            BibWorkflowObject.id == hpcontainerid).first())
        data_preview = _entry_data_preview(bwobject.data['data'])

        return render_template('bibholdingpen_'+widget+'.html',
                               hpcontainer=hpcontainer,
                               widget=widget_form,
                               match_preview=match_preview, matches=matches,
                               data_preview=data_preview)

    elif widget == 'approval_widget':
        # setting up approval widget
        data_preview = _entry_data_preview(bwobject.data['data'])
        return render_template('bibholdingpen_approval_widget.html',
                               hpcontainer=hpcontainer,
                               widget=widget_form, data_preview=data_preview)


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'oid': (unicode, '0'),
                                 'recformat': (unicode, 'default')})
def entry_data_preview(oid, recformat):
    """
    Presents the data in a human readble form or in xml code
    """
    hpobject = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              int(oid)).first()
    return _entry_data_preview(hpobject.data, recformat)


def get_info(hpobject):
    """
    Parses the hpobject and extracts its info to a dictionary
    """
    info = {}
    info['version'] = hpobject.version
    info['owner'] = hpobject.extra_data['owner']
    info['parent id'] = hpobject.parent_id
    info['task counter'] = hpobject.extra_data['task_counter']
    info['workflow id'] = hpobject.workflow_id
    info['object id'] = hpobject.id
    info['last task name'] = hpobject.extra_data['last_task_name']
    info['widget'] = hpobject.extra_data['widget']
    return info


def _entry_data_preview(data, recformat='hd'):
    """
    Formats the data using format_record
    """
    if recformat == 'hd' or recformat == 'xm':
        try:
            data['data'] = format_record(recID=None, of=recformat,
                                         xml_record=data['data'])
        except:
            print "This is not a XML string"
    try:
        return data['data']
    except:
        return data
