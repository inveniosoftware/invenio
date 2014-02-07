# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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
from invenio.bibworkflow_utils import get_workflow_definition
from invenio.bibworkflow_api import continue_oid_delayed
from invenio.bibworkflow_hp_load_widgets import widgets
from invenio.bibworkflow_config import CFG_OBJECT_VERSION

from flask import redirect, url_for, flash
from invenio.bibformat_engine import format_record

from invenio.bibworkflow_utils import create_hp_containers
# from invenio.bibworkflow_containers import bwolist

blueprint = InvenioBlueprint('holdingpen', __name__,
                             url_prefix="/admin/holdingpen",
                             menubuilder=[('main.admin.holdingpen',
                                          _('Holdingpen'),
                                           'holdingpen.index')],
                             breadcrumbs=[(_('Administration'), 'help.admin'),
                                          (_('Holdingpen'),
                                           'holdingpen.index')])


@blueprint.route('/index', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_templated('bibworkflow_hp_index.html')
def index():
    """
    Displays main interface of BibHoldingpen.
    """
    bwolist = create_hp_containers()
    return dict(hpcontainers=bwolist)


@blueprint.route('/refresh', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def refresh():
    import invenio.bibworkflow_containers
    reload(invenio.bibworkflow_containers)
    return 'Records Refreshed'


@blueprint.route('/load_table', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_templated('bibworkflow_hp_index.html')
def load_table():
    """
    Function used for the passing of JSON data to the DataTable
    """
    from flask import request

    from invenio.bibworkflow_containers import bwolist

    iDisplayStart = request.args.get('iDisplayStart')
    iDisplayLength = request.args.get('iDisplayLength')
    # sSearch will be used for searching later
    # sSearch = request.args.get('sSearch')
    # iSortCol_0 = request.args.get('iSortCol_0')
    # sSortDir_0 = request.args.get('sSortDir_0')

    iDisplayStart = int(request.args.get('iDisplayStart'))
    iDisplayLength = int(request.args.get('iDisplayLength'))

    table_data = {
        "aaData": []
    }

    for bwo in bwolist[iDisplayStart:iDisplayStart+iDisplayLength]:
        table_data['sEcho'] = int(request.args.get('sEcho')) + 1
        table_data['iTotalRecords'] = len(bwolist)
        table_data['iTotalDisplayRecords'] = len(bwolist)

        if bwo.version == CFG_OBJECT_VERSION.FINAL:
            bwo_version = \
                '<span class="label label-success">Final</span>'
        elif bwo.version == CFG_OBJECT_VERSION.HALTED:
            bwo_version = \
                '<span class="label label-warning">Halted</span>'
        else:
            bwo_version = \
                '<span class="label label-success">Running</span>'
        if bwo.extra_data['widget'] is not None:
            widget_link = '<a class="btn btn-info"' + \
                          'href="/admin/holdingpen/widget?widget=' + \
                          bwo.extra_data['widget'] + \
                          '&bwobject_id=' + \
                          str(bwo.id) + \
                          '"><i class="icon-wrench"></i></a>'
        else:
            widget_link = None
        table_data['aaData'].append(
            [str(bwo.id),
             None,
             None,
             None,
             str(bwo.id_workflow),
             str(bwo.extra_data['owner']),
             str(bwo.created),
             bwo_version,
             '<a id="info_button" ' +
             'class="btn btn-info pull-center text-center"' +
             'href="/admin/holdingpen/details?bwobject_id=' +
             str(bwo.id) +
             '"><i class="icon-white icon-zoom-in"></i></a>',
             widget_link,
             ])
    return table_data


@blueprint.route('/resolve_approval', methods=['GET', 'POST'])
@blueprint.invenio_wash_urlargd({'bwobject_id': (int, 0)})
def resolve_approval(bwobject_id):
    """
    Resolves the action taken in the approval widget
    """
    from flask import request
    if request.form['submitButton'] == 'Accept':
        continue_oid_delayed(bwobject_id)
        flash('Record Accepted')
    elif request.form['submitButton'] == 'Reject':
        _delete_from_db(bwobject_id)
        flash('Record Rejected')
    return redirect(url_for('holdingpen.index'))


@blueprint.route('/details', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'bwobject_id': (int, 0)})
def details(bwobject_id):
    """
    Displays info about the hpcontainer, and presents the data
    of all available versions of the object. (Initial, Error, Final)
    """
    # search for parents
    bwobject = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              bwobject_id).first()

    bwparent = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              bwobject.id_parent).first()

    info = get_info(bwobject)
    try:
        info['widget'] = bwobject.extra_data['widget']
    except (KeyError, AttributeError):
        pass

    w_metadata = Workflow.query.filter(Workflow.uuid ==
                                       bwobject.id_workflow).first()
    # read the logtext from the file system
    try:
        f = open(CFG_LOGDIR + "/object_" + str(bwobject.id)
                 + "_w_" + str(bwobject.id_workflow) + ".log", "r")
        logtext = f.read()
    except IOError:
        logtext = ""

    print bwobject.get_data()
    print _entry_data_preview(bwobject.get_data())

    return render_template('bibworkflow_hp_details.html',
                           bwobject=bwobject,
                           bwparent=bwparent,
                           info=info, log=logtext,
                           data_preview=_entry_data_preview(
                               bwobject.get_data()),
                           workflow_func=get_workflow_definition(
                               w_metadata.name).workflow)


@blueprint.route('/restart_record', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'bwobject_id': (int, 0)})
def restart_record(bwobject_id, start_point='continue_next'):
    """
    Restarts the initial object in its workflow
    """
    continue_oid_delayed(oid=bwobject_id, start_point=start_point)
    return 'Record Restarted'


@blueprint.route('/restart_record_prev', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'bwobject_id': (int, 0)})
def restart_record_prev(bwobject_id):
    """
    Restarts the initial object in its workflow from the current task
    """
    continue_oid_delayed(oid=bwobject_id, start_point="restart_task")
    print "Record restarted from previous task"


@blueprint.route('/delete_from_db', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'bwobject_id': (int, 0)})
def delete_from_db(bwobject_id):
    """
    Deletes all available versions of the object from the db
    """
    import invenio.bibworkflow_containers
    _delete_from_db(bwobject_id)
    reload(invenio.bibworkflow_containers)
    flash('Record Deleted')
    return redirect(url_for('holdingpen.index'))


def _delete_from_db(bwobject_id):
    from invenio.sqlalchemyutils import db

    # delete every BibWorkflowObject version from the db
    BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                   bwobject_id).delete()
    db.session.commit()


@blueprint.route('/widget', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'bwobject_id': (int, 0),
                                 'widget': (unicode, ' ')})
def show_widget(bwobject_id, widget):
    """
    Renders the bibmatch widget for a specific record
    """
    bwobject = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              bwobject_id).first()
    bwparent = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              bwobject.id_parent).first()

    widget_form = widgets[widget]

    if widget == 'bibmatch_widget':
        # setting up bibmatch widget
        try:
            matches = bwobject.extra_data['tasks_results']['match_record']
        except:
            pass

        match_preview = []
        # adding dummy matches
        match_preview.append(BibWorkflowObject.query.filter(
            BibWorkflowObject.id == bwobject_id).first())
        match_preview.append(BibWorkflowObject.query.filter(
            BibWorkflowObject.id == bwobject_id).first())

        data_preview = _entry_data_preview(bwobject.get_data())

        return render_template('bibworkflow_hp_'+widget+'.html',
                               bwobject=bwobject,
                               widget=widget_form,
                               match_preview=match_preview, matches=matches,
                               data_preview=data_preview)

    elif widget == 'approval_widget':
        # setting up approval widget
        data_preview = _entry_data_preview(bwobject.get_data())
        return render_template('bibworkflow_hp_approval_widget.html',
                               bwobject=bwobject,
                               bwparent=bwparent,
                               widget=widget_form, data_preview=data_preview)


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
@blueprint.invenio_wash_urlargd({'oid': (unicode, '0'),
                                 'recformat': (unicode, 'default')})
def entry_data_preview(oid, recformat):
    """
    Presents the data in a human readble form or in xml code
    """
    bwobject = BibWorkflowObject.query.filter(BibWorkflowObject.id ==
                                              int(oid)).first()
    return _entry_data_preview(bwobject.get_data(), recformat)


def get_info(bwobject):
    """
    Parses the hpobject and extracts its info to a dictionary
    """
    info = {}
    info['version'] = bwobject.version
    info['owner'] = bwobject.extra_data['owner']
    info['parent id'] = bwobject.id_parent
    info['task counter'] = bwobject.extra_data['task_counter']
    info['workflow id'] = bwobject.id_workflow
    info['object id'] = bwobject.id
    info['last task name'] = bwobject.extra_data['last_task_name']
    info['widget'] = bwobject.extra_data['widget']
    return info


def _entry_data_preview(data, recformat='hd'):
    """
    Formats the data using format_record
    """
    if recformat == 'hd' or recformat == 'xm':
        try:
            data = format_record(recID=None, of=recformat,
                                 xml_record=data)
        except:
            print "This is not a XML string"

    if data is "" or data is None:
        print 'NAI EINAI ADEIO'
        data = 'Could not render data'
    else:
        pass
    return data
