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

from flask import render_template, Blueprint, redirect, url_for, flash, request, current_app
from flask.ext.login import login_required

from ..models import BibWorkflowObject, Workflow
from ..loader import widgets
from invenio.base.decorators import templated, wash_arguments
from invenio.modules.formatter.engine import format_record
from invenio.base.i18n import _
from invenio.ext.breadcrumb import default_breadcrumb_root, register_breadcrumb
from invenio.ext.menu import register_menu
from invenio.utils.date import pretty_date
from ..utils import (get_workflow_definition,
                     sort_bwolist)
from ..api import continue_oid_delayed, start


blueprint = Blueprint('holdingpen', __name__, url_prefix="/admin/holdingpen",
                      template_folder='../templates',
                      static_folder='../static')

default_breadcrumb_root(blueprint, '.holdingpen')


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@login_required
@register_menu(blueprint, 'main.admin.holdingpen', _('Holdingpen'))
@register_breadcrumb(blueprint, '.', _('Holdingpen'))
@templated('workflows/hp_index.html')
def index():
    """
    Displays main interface of Holdingpen.
    Acts as a hub for catalogers (may be removed)
    """
    from ..containers import bwolist

    # FIXME: need to autodiscover widgets properly
    widget_list = {}
    for widget in widgets:
        widget_list[widget] = [0, []]

    for bwo in bwolist:
        if ('widget' in bwo.get_extra_data()) and \
           (bwo.get_extra_data()['widget'] is not None) \
                and (bwo.version == 2):
            widget_list[bwo.get_extra_data()['widget']][1].append(bwo)
    for key in widget_list:
        widget_list[key][0] = len(widget_list[key][1])

    return dict(tasks=widget_list)


@blueprint.route('/maintable', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.records', _('Records'))
@login_required
@templated('workflows/hp_maintable.html')
def maintable():
    """
    Displays main table interface of Holdingpen.
    """
    from ..containers import bwolist

    # FIXME: need to autodiscover widgets properly
    widget_list = {}
    for widget in widgets:
        widget_list[widget] = [0, []]

    for bwo in bwolist:
        if ('widget' in bwo.get_extra_data()) and \
           (bwo.get_extra_data()['widget'] is not None) \
                and (bwo.version != 1):
            widget_list[bwo.get_extra_data()['widget']][1].append(bwo)
    for key in widget_list:
        widget_list[key][0] = len(widget_list[key][1])

    return dict(bwolist=bwolist, widget_list=widget_list)


@blueprint.route('/refresh', methods=['GET', 'POST'])
@login_required
def refresh():
    """
    Reloads the bibworkflow_containers file,
    thus rebuilding the BWObject list.
    """
    # FIXME: Temp hack until redis is hooked up
    import invenio.modules.workflows.containers
    reload(invenio.modules.workflows.containers)
    return 'Records Refreshed'


@blueprint.route('/batch_widget', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwolist': (unicode, "")})
def batch_widget(bwolist):
    """
    Renders widget accepting single or multiple records.
    """
    from ..utils import parse_bwids
    bwolist = parse_bwids(bwolist)

    try:
        bwolist = map(int, bwolist)
    except ValueError:
        print 'Error in IDs'

    objlist = []
    workflow_list = []
    workflow_func_list = []
    w_metadata_list = []
    info_list = []
    widgetlist = []
    bwo_parent_list = []
    logtext_list = []

    objlist = [BibWorkflowObject.query.get(i) for i in bwolist]

    for bwobject in objlist:
        extracted_data = extract_data(bwobject)
        bwo_parent_list.append(extracted_data['bwparent'])
        logtext_list.append(extracted_data['logtext'])
        info_list.append(extracted_data['info'])
        w_metadata_list.append(extracted_data['w_metadata'])
        workflow_func_list.append(extracted_data['workflow_func'])
        if bwobject.get_extra_data()['widget'] not in widgetlist:
            widgetlist.append(bwobject.get_extra_data()['widget'])

    widget_form = widgets[widgetlist[0]]

    result = widget_form().render(objlist, bwo_parent_list, info_list,
                                  logtext_list, w_metadata_list,
                                  workflow_func_list)
    url, parameters = result

    return render_template(url, **parameters)


@blueprint.route('/load_table', methods=['GET', 'POST'])
@login_required
@templated('workflows/hp_maintable.html')
def load_table():
    """
    Function used for the passing of JSON data to the DataTable
    """
    from ..containers import bwolist

    # sSearch will be used for searching later
    a_search = request.args.get('sSearch')

    i_sortcol_0 = request.args.get('iSortCol_0')
    s_sortdir_0 = request.args.get('sSortDir_0')

    i_display_start = int(request.args.get('iDisplayStart'))
    i_display_length = int(request.args.get('iDisplayLength'))

    if a_search:
        # FIXME: Temp measure until Redis is hooked up
        from ..containers import create_hp_containers
        bwolist = create_hp_containers(sSearch=a_search)

    if 'iSortCol_0' in current_app.config:
        i_sortcol_0 = int(i_sortcol_0)
        if i_sortcol_0 != current_app.config['iSortCol_0'] \
           or s_sortdir_0 != current_app.config['sSortDir_0']:
            bwolist = sort_bwolist(bwolist, i_sortcol_0, s_sortdir_0)

    current_app.config['iDisplayStart'] = i_display_start
    current_app.config['iDisplayLength'] = i_display_length
    current_app.config['iSortCol_0'] = i_sortcol_0
    current_app.config['sSortDir_0'] = s_sortdir_0

    table_data = {
        "aaData": []
    }

    for bwo in bwolist[i_display_start:i_display_start+i_display_length]:
        try:
            widgetname = widgets[bwo.get_extra_data()['widget']].__title__
        except KeyError:
            widgetname = 'None'

        table_data['sEcho'] = int(request.args.get('sEcho')) + 1
        table_data['iTotalRecords'] = len(bwolist)
        table_data['iTotalDisplayRecords'] = len(bwolist)
        #This will be simplified once Redis is utilized.
        if 'title' in bwo.get_extra_data()['redis_search']:
            title = bwo.get_extra_data()['redis_search']['title']
        else:
            title = None
        if 'source' in bwo.get_extra_data()['redis_search']:
            source = bwo.get_extra_data()['redis_search']['source']
        else:
            source = None
        if 'category' in bwo.get_extra_data()['redis_search']:
            category = bwo.get_extra_data()['redis_search']['category']
        else:
            category = None
        if not bwo.get_extra_data()['owner']:
            owner = "None"
        table_data['aaData'].append(
            [str(bwo.id),
             title,
             source,
             category,
             str(bwo.id_workflow),
             owner,
             str(pretty_date(bwo.created))+'#'+str(bwo.created),
             bwo.version,
             str(bwo.id),
             str(bwo.get_extra_data()['widget'])+'#'+widgetname,
             ])
    return table_data


@blueprint.route('/details', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.details', "Record Details")
@login_required
@wash_arguments({'bwobject_id': (int, 0)})
def details(bwobject_id):
    """
    Displays info about the object, and presents the data
    of all available versions of the object. (Initial, Error, Final)
    """
    bwobject = BibWorkflowObject.query.get(bwobject_id)

    extracted_data = extract_data(bwobject)

    # FIXME: need to determine right format
    recformat = "hd"

    return render_template('workflows/hp_details.html',
                           bwobject=bwobject,
                           bwparent=extracted_data['bwparent'],
                           info=extracted_data['info'],
                           log=extracted_data['logtext'],
                           data_preview=_entry_data_preview(
                               bwobject.get_data(), recformat),
                           workflow_func=extracted_data['workflow_func'],
                           workflow=extracted_data['w_metadata'])


@blueprint.route('/restart_record', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwobject_id': (int, 0)})
def restart_record(bwobject_id, start_point='continue_next'):
    """
    Restarts the initial object in its workflow
    """
    bwobject = BibWorkflowObject.query.get(bwobject_id)

    workflow = Workflow.query.filter(
        Workflow.uuid == bwobject.id_workflow).first()

    start(workflow.name, [bwobject.get_data()])
    return 'Record Restarted'


@blueprint.route('/continue_record', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwobject_id': (int, 0)})
def continue_record(bwobject_id):
    """
    Restarts the initial object in its workflow
    """
    continue_oid_delayed(oid=bwobject_id, start_point='continue_next')
    return 'Record continued workflow'


@blueprint.route('/restart_record_prev', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwobject_id': (int, 0)})
def restart_record_prev(bwobject_id):
    """
    Restarts the initial object in its workflow from the current task
    """
    continue_oid_delayed(oid=bwobject_id, start_point="restart_task")
    return 'Record restarted current task'


@blueprint.route('/delete_from_db', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwobject_id': (int, 0)})
def delete_from_db(bwobject_id):
    """
    Deletes all available versions of the object from the db
    """
    # FIXME: Temp hack until redis is hooked up
    # import invenio.modules.workflows.containers
    _delete_from_db(bwobject_id)
    # reload invenio.modules.workflows.containers
    flash('Record Deleted')
    return 'Record Deleted'
    # return redirect(url_for('holdingpen.index'))


def _delete_from_db(bwobject_id):
    from invenio.ext.sqlalchemy import db
    # delete every BibWorkflowObject version from the db
    # TODO: THIS NEEDS FIXING
    BibWorkflowObject.query.filter(BibWorkflowObject.id == bwobject_id).delete()
    db.session.commit()


@blueprint.route('/delete_multi', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwolist': (unicode, "")})
def delete_multi(bwolist):
    from ..utils import parse_bwids
    bwolist = parse_bwids(bwolist)

    for bwobject_id in bwolist:
        _delete_from_db(bwobject_id)
    return 'Records Deleted'


@blueprint.route('/widget', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.widget', "Widget")
@login_required
@wash_arguments({'bwobject_id': (int, 0),
                 'widget': (unicode, 'default')})
def show_widget(bwobject_id, widget):
    """
    Renders the widget assigned to a specific record
    """
    bwobject = BibWorkflowObject.query.get(bwobject_id)

    widget_form = widgets[widget]

    extracted_data = extract_data(bwobject)

    result = widget_form().render([bwobject],
                                  [extracted_data['bwparent']],
                                  [extracted_data['info']],
                                  [extracted_data['logtext']],
                                  [extracted_data['w_metadata']],
                                  [extracted_data['workflow_func']])
    url, parameters = result

    return render_template(url, **parameters)


@blueprint.route('/resolve_widget', methods=['POST'])
@login_required
@wash_arguments({'bwobject_id': (unicode, '0'),
                                 'widget': (unicode, 'default')})
def resolve_widget(bwobject_id, widget):
    """
    Resolves the action taken in a widget.
    Calls the run_widget function of the specific widget.
    """
    widget_form = widgets[widget]
    widget_form().run_widget(bwobject_id, request)
    return "Done"


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
@login_required
@wash_arguments({'oid': (unicode, '0'),
                 'recformat': (unicode, 'default')})
def entry_data_preview(oid, recformat):
    """
    Presents the data in a human readble form or in xml code
    """
    from flask import jsonify, Markup

    bwobject = BibWorkflowObject.query.get(int(oid))

    formatted_data = _entry_data_preview(bwobject.get_data(), recformat)
    if recformat in ("xm", "xml", "marcxml"):
        data = Markup.escape(formatted_data)
    else:
        data = formatted_data
    return jsonify(data=data)


def get_info(bwobject):
    """
    Parses the hpobject and extracts its info to a dictionary
    """
    info = {}
    if bwobject.get_extra_data()['owner'] != {}:
        info['owner'] = bwobject.get_extra_data()['owner']
    else:
        info['owner'] = 'None'
    info['parent id'] = bwobject.id_parent
    info['workflow id'] = bwobject.id_workflow
    info['object id'] = bwobject.id
    info['widget'] = bwobject.get_extra_data()['widget']
    return info


def _entry_data_preview(data, recformat='hd'):
    """
    Formats the data using format_record
    """
    if recformat != 'xm':
        return format_record(recID=None, of=recformat, xml_record=data)
    else:
        from xml.dom.minidom import parseString
        pretty_data = parseString(data)
        return pretty_data.toprettyxml()


def extract_data(bwobject):
    """
    Extracts metadata for BibWorkflowObject needed for rendering
    the Record's details and widget page.
    """
    extracted_data = {}

    extracted_data['bwparent'] = \
        BibWorkflowObject.query.get(bwobject.id_parent)

    # TODO: read the logstuff from the db
    extracted_data['loginfo'] = ""
    extracted_data['logtext'] = {}

    for log in extracted_data['loginfo']:
        extracted_data['logtext'][log.get_extra_data()['last_task_name']] = \
            log.message

    extracted_data['info'] = get_info(bwobject)
    try:
        extracted_data['info']['widget'] = bwobject.get_extra_data()['widget']
    except (KeyError, AttributeError):
        pass

    extracted_data['w_metadata'] = \
        Workflow.query.filter(Workflow.uuid == bwobject.id_workflow).first()

    extracted_data['workflow_func'] = \
        get_workflow_definition(extracted_data['w_metadata'].name).workflow

    return extracted_data
