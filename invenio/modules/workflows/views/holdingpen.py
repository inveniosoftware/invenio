# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
    invenio.modules.workflows.views.holdingpen
    ------------------------------------------

    Holding Pen is an overlay over all objects (BibWorkflowObject) that
    have run through a workflow (BibWorkflowEngine). This area is targeted
    to catalogers and super users for inspecting ingestion workflows and
    submissions/depositions.

    Note: Currently work-in-progress.
"""

import re

from six import iteritems, text_type

from flask import (render_template, Blueprint,
                   request, current_app,
                   jsonify, url_for,
                   flash)
from flask.ext.login import login_required
from flask.ext.breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask.ext.menu import register_menu

from invenio.base.decorators import templated, wash_arguments
from invenio.base.i18n import _
from invenio.utils.date import pretty_date

from ..models import BibWorkflowObject, Workflow, ObjectVersion
from ..registry import widgets
from ..utils import (get_workflow_definition,
                     sort_bwolist)
from ..api import continue_oid_delayed, start


blueprint = Blueprint('holdingpen', __name__, url_prefix="/admin/holdingpen",
                      template_folder='../templates',
                      static_folder='../static')

default_breadcrumb_root(blueprint, '.holdingpen')

REG_TD = re.compile("<td title=\"(.+?)\">(.+?)</td>", re.DOTALL)


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@login_required
@register_menu(blueprint, 'personalize.holdingpen', _('Your Pending Actions'))
@register_breadcrumb(blueprint, '.', _('Holdingpen'))
@templated('workflows/hp_index.html')
def index():
    """
    Displays main interface of Holdingpen.
    Acts as a hub for catalogers (may be removed)
    """
    # FIXME: Add user filtering
    bwolist = get_holdingpen_objects(version_showing=[ObjectVersion.HALTED])
    widget_list = get_widget_list(bwolist)

    return dict(tasks=widget_list)


@blueprint.route('/maintable', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.records', _('Records'))
@login_required
@templated('workflows/hp_maintable.html')
def maintable():
    """
    Displays main table interface of Holdingpen.
    """
    bwolist = get_holdingpen_objects()
    widget_list = get_widget_list(bwolist)
    widget_static = []
    for name, widget in iteritems(widgets):
        if getattr(widget, "static", None):
            widget_static.extend(widget.static)

    return dict(bwolist=bwolist,
                widget_list=widget_list,
                widget_static=widget_static)


@blueprint.route('/batch_widget', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwolist': (text_type, "")})
def batch_widget(bwolist):
    """
    Renders widget accepting single or multiple records.
    """
    from ..utils import parse_bwids

    bwolist = parse_bwids(bwolist)

    try:
        bwolist = map(int, bwolist)
    except ValueError:
        # Bad ID, we just pass for now
        pass

    objlist = []
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
        if bwobject.get_widget() not in widgetlist:
            widgetlist.append(bwobject.get_widget())

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
    1] First checks for what record version to show
    2] then sorting direction,
    3] then if the user searched for something
    and finally it builds the JSON to send.
    """
    version_showing = []
    req = request.json
    s_search = request.args.get('sSearch', None)

    if req is not None:
        if "final" in req:
            version_showing.append(ObjectVersion.FINAL)
        if "halted" in req:
            version_showing.append(ObjectVersion.HALTED)
        if "running" in req:
            version_showing.append(ObjectVersion.RUNNING)
        if "initial" in req:
            version_showing.append(ObjectVersion.INITIAL)
        current_app.config['VERSION_SHOWING'] = version_showing
    elif "VERSION_SHOWING" in current_app.config:
        version_showing = current_app.config.get('VERSION_SHOWING', [])

    try:
        i_sortcol_0 = request.args.get('iSortCol_0')
        s_sortdir_0 = request.args.get('sSortDir_0')
        i_display_start = int(request.args.get('iDisplayStart'))
        i_display_length = int(request.args.get('iDisplayLength'))
        sEcho = int(request.args.get('sEcho')) + 1
    except:
        i_sortcol_0 = current_app.config.get('iSortCol_0', 0)
        s_sortdir_0 = current_app.config.get('sSortDir_0', None)
        i_display_start = current_app.config.get('iDisplayStart', 0)
        i_display_length = current_app.config.get('iDisplayLength', 10)
        sEcho = current_app.config.get('sEcho', 0) + 1

    bwolist = get_holdingpen_objects(ssearch=s_search,
                                     version_showing=version_showing)

    if 'iSortCol_0' in current_app.config:
        i_sortcol_0 = int(i_sortcol_0)
        if i_sortcol_0 != current_app.config['iSortCol_0'] \
        or s_sortdir_0 != current_app.config['sSortDir_0']:
            bwolist = sort_bwolist(bwolist, i_sortcol_0, s_sortdir_0)

    current_app.config['iDisplayStart'] = i_display_start
    current_app.config['iDisplayLength'] = i_display_length
    current_app.config['iSortCol_0'] = i_sortcol_0
    current_app.config['sSortDir_0'] = s_sortdir_0
    current_app.config['sEcho'] = sEcho

    table_data = {
        "aaData": []
    }

    try:
        table_data['iTotalRecords'] = len(bwolist)
        table_data['iTotalDisplayRecords'] = len(bwolist)
    except:
        bwolist = get_holdingpen_objects(version_showing=version_showing)
        table_data['iTotalRecords'] = len(bwolist)
        table_data['iTotalDisplayRecords'] = len(bwolist)

    # This will be simplified once Redis is utilized.
    records_showing = 0

    for bwo in bwolist[i_display_start:i_display_start + i_display_length]:
        widget_name = bwo.get_widget()
        widget = widgets.get(widget_name, None)

        # if widget != None and bwo.version in VERSION_SHOWING:
        records_showing += 1

        mini_widget = getattr(widget, "mini_widget", None)
        record = bwo.get_data()
        if not isinstance(record, dict):
            record = {}
        extra_data = bwo.get_extra_data()
        category_list = record.get('subject_term', [])
        if isinstance(category_list, dict):
            category_list = [category_list]
        categories = ["%s (%s)" % (subject['term'], subject['scheme'])
                      for subject in category_list]
        row = render_template('workflows/row_formatter.html',
                              object=bwo,
                              record=record,
                              extra_data=extra_data,
                              categories=categories,
                              widget=widget,
                              mini_widget=mini_widget,
                              pretty_date=pretty_date)

        d = {}
        for key, value in REG_TD.findall(row):
            d[key] = value.strip()

        table_data['aaData'].append(
            [d['id'],
             d['checkbox'],
             d['title'],
             d['source'],
             d['category'],
             d['pretty_date'],
             d['version'],
             d['type'],
             d['details'],
             d['widget']
             ]
        )

    table_data['sEcho'] = sEcho
    table_data['iTotalRecords'] = len(bwolist)
    table_data['iTotalDisplayRecords'] = len(bwolist)
    return jsonify(table_data)


@blueprint.route('/get_version_showing', methods=['GET', 'POST'])
@login_required
def get_version_showing():
    """
    Returns current version showing, saved in current_app.config
    """
    try:
        return current_app.config['VERSION_SHOWING']
    except KeyError:
        return None


@blueprint.route('/details/<int:objectid>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.details', _("Record Details"))
@login_required
def details(objectid):
    """
    Displays info about the object, and presents the data
    of all available versions of the object. (Initial, Error, Final)
    """
    of = "hd"
    bwobject = BibWorkflowObject.query.get(objectid)

    formatted_data = bwobject.get_formatted_data(of)
    extracted_data = extract_data(bwobject)

    try:
        edit_record_widget = widgets['edit_record_widget']()
    except KeyError:
        # Could not load edit_record_widget
        edit_record_widget = []

    return render_template('workflows/hp_details.html',
                           bwobject=bwobject,
                           bwparent=extracted_data['bwparent'],
                           info=extracted_data['info'],
                           log=extracted_data['logtext'],
                           data_preview=formatted_data,
                           workflow_func=extracted_data['workflow_func'],
                           workflow=extracted_data['w_metadata'],
                           edit_record_widget=edit_record_widget)


@blueprint.route('/restart_record', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (int, 0)})
def restart_record(objectid, start_point='continue_next'):
    """
    Restarts the initial object in its workflow
    """
    bwobject = BibWorkflowObject.query.get(objectid)

    workflow = Workflow.query.filter(
        Workflow.uuid == bwobject.id_workflow).first()

    start(workflow.name, [bwobject.get_data()])
    return 'Record Restarted'


@blueprint.route('/continue_record', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (int, 0)})
def continue_record(objectid):
    """
    Restarts the initial object in its workflow
    """
    continue_oid_delayed(oid=objectid, start_point='continue_next')
    return 'Record continued workflow'


@blueprint.route('/restart_record_prev', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (int, 0)})
def restart_record_prev(objectid):
    """
    Restarts the initial object in its workflow from the current task
    """
    continue_oid_delayed(oid=objectid, start_point="restart_task")
    return 'Record restarted current task'


@blueprint.route('/delete', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (int, 0)})
def delete_from_db(objectid):
    """
    Deletes all available versions of the object from the db
    """
    BibWorkflowObject.delete(objectid)
    return 'Record Deleted'


@blueprint.route('/delete_multi', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwolist': (text_type, "")})
def delete_multi(bwolist):
    from ..utils import parse_bwids

    bwolist = parse_bwids(bwolist)
    for objectid in bwolist:
        delete_from_db(objectid)
    return 'Records Deleted'


@blueprint.route('/action/<objectid>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.widget', _("Widget"))
@login_required
def show_widget(objectid):
    """
    Renders the widget assigned to a specific record
    """
    bwobject = BibWorkflowObject.query.filter(
        BibWorkflowObject.id == objectid).first_or_404()

    widget = bwobject.get_widget()
    # FIXME: add case here if no widget
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


@blueprint.route('/resolve', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (text_type, '-1'),
                 'widget': (text_type, 'default')})
def resolve_widget(objectid, widget):
    """
    Resolves the action taken in a widget.
    Calls the run_widget function of the specific widget.
    """
    widget_form = widgets[widget]
    widget_form().run_widget(objectid)
    return "Done"


@blueprint.route('/resolve_edit', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (text_type, '0'),
                 'form': (text_type, '')})
def resolve_edit(objectid, form):
    """
    Performs the changes to the record made in the edit record widget.
    """
    if request:
        edit_record(request.form)
    return 'Record Edited'


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (text_type, '0'),
                 'of': (text_type, None)})
def entry_data_preview(objectid, of):
    """
    Presents the data in a human readble form or in xml code
    """
    from flask import Markup
    from pprint import pformat

    bwobject = BibWorkflowObject.query.get(int(objectid))

    if not bwobject:
        flash("No object found for %s" % (objectid,))
        return jsonify(data={})

    formatted_data = bwobject.get_formatted_data(of)
    if isinstance(formatted_data, dict):
        formatted_data = pformat(formatted_data)
    if of and of in ("xm", "xml", "marcxml"):
        data = Markup.escape(formatted_data)
    else:
        data = formatted_data
    return jsonify(data=data)


@blueprint.route('/get_context', methods=['GET', 'POST'])
@login_required
def get_context():
    """
    Returns a JSON structure with URL maps for Holding Pen.
    """
    context = {}
    context['url_prefix'] = blueprint.url_prefix
    context['holdingpen'] = {
        "url_load": url_for('holdingpen.load_table'),
        "url_preview": url_for('holdingpen.entry_data_preview'),
        "url_restart_record": url_for('holdingpen.restart_record'),
        "url_restart_record_prev": url_for('holdingpen.restart_record_prev'),
        "url_continue_record": url_for('holdingpen.continue_record'),
        "url_resolve_edit": url_for('holdingpen.resolve_edit')
    }
    try:
        context['version_showing'] = current_app.config['VERSION_SHOWING']
    except KeyError:
        context['version_showing'] = ObjectVersion.HALTED

    context['widgets'] = [name for name, widget in iteritems(widgets)
                          if getattr(widget, "static", None)]
    return jsonify(context)


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
    info['widget'] = bwobject.get_widget()
    return info


def extract_data(bwobject):
    """
    Extracts metadata for BibWorkflowObject needed for rendering
    the Record's details and widget page.
    """
    extracted_data = {}

    if bwobject.id_parent is not None:
        extracted_data['bwparent'] = \
            BibWorkflowObject.query.get(bwobject.id_parent)
    else:
        extracted_data['bwparent'] = None

    # TODO: read the logstuff from the db
    extracted_data['loginfo'] = ""
    extracted_data['logtext'] = {}

    for log in extracted_data['loginfo']:
        extracted_data['logtext'][log.get_extra_data()['last_task_name']] = \
            log.message

    extracted_data['info'] = get_info(bwobject)
    try:
        extracted_data['info']['widget'] = bwobject.get_widget()
    except (KeyError, AttributeError):
        pass

    extracted_data['w_metadata'] = \
        Workflow.query.filter(Workflow.uuid == bwobject.id_workflow).first()

    extracted_data['workflow_func'] = \
        get_workflow_definition(extracted_data['w_metadata'].name).workflow

    return extracted_data


def edit_record(form):
    """
    Will call the edit record widget resolve function
    """
    for key in form.iterkeys():
        # print '%s: %s' % (key, form[key])
        pass


def get_widget_list(object_list):
    """
    Returns a dict of widget names mapped to
    the number of halted objects associated with that widget.
    """
    widget_dict = {}
    found_widgets = []

    # First get a list of all to count up later
    for bwo in object_list:
        widget_name = bwo.get_widget()
        if widget_name is not None:
            found_widgets.append(widget_name)

    # Get "real" widget name only once per widget
    for widget_name in set(found_widgets):
        if widget_name not in widgets:
            # Perhaps some old widget? Use stored name.
            widget_nicename = widget_name
        else:
            widget = widgets[widget_name]
            widget_nicename = getattr(widget, "__title__", widget_name)
        widget_dict[widget_nicename] = found_widgets.count(widget_name)
    return widget_dict


def get_holdingpen_objects(isortcol_0=None,
                           ssortdir_0=None,
                           ssearch=None,
                           version_showing=(ObjectVersion.HALTED,)):
    """
    Looks for related BibWorkflowObject's for display in Holding Pen.

    Uses DataTable naming for filtering/sorting. Work in progress.
    """
    if isortcol_0:
        isortcol_0 = int(isortcol_0)

    bwobject_list = BibWorkflowObject.query.filter(
        BibWorkflowObject.version.in_(version_showing)
    ).all()

    if ssearch and len(ssearch) < 2:
        bwobject_list_tmp = []
        for bwo in bwobject_list:
            extra_data = bwo.get_extra_data()
            if bwo.id_parent == ssearch:
                bwobject_list_tmp.append(bwo)
            elif bwo.id_user == ssearch:
                bwobject_list_tmp.append(bwo)
            elif bwo.id_workflow == ssearch:
                bwobject_list_tmp.append(bwo)
            elif extra_data['_last_task_name'] == ssearch:
                bwobject_list_tmp.append(bwo)
            else:
                widget_name = bwo.get_widget()
                if widget_name:
                    widget = widgets[widget_name]
                    if ssearch in widget.__title__ or ssearch in widget_name:
                        bwobject_list_tmp.append(bwo)
        bwobject_list = bwobject_list_tmp

    if isortcol_0 == -6:
        if ssortdir_0 == 'desc':
            bwobject_list.reverse()

    return bwobject_list
