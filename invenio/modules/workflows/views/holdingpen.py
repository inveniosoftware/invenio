# -*- coding: utf-8 -*-
##
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
Holding Pen

Holding Pen is an overlay over all objects (BibWorkflowObject) that
have run through a workflow (BibWorkflowEngine). This area is targeted
to catalogers and super users for inspecting ingestion workflows and
submissions/depositions.

Note: Currently work-in-progress.
"""

from six import iteritems, text_type

from flask import (render_template, Blueprint, request, jsonify,
                   url_for, flash, session)
from flask.ext.login import login_required
from flask.ext.breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask.ext.menu import register_menu

from invenio.base.decorators import templated, wash_arguments
from invenio.base.i18n import _
from invenio.utils.date import pretty_date

from ..models import BibWorkflowObject, Workflow, ObjectVersion
from ..registry import actions
from ..utils import (sort_bwolist, extract_data, get_action_list,
                     get_formatted_holdingpen_object,
                     get_holdingpen_objects)
from ..api import continue_oid_delayed, start_delayed

blueprint = Blueprint('holdingpen', __name__, url_prefix="/admin/holdingpen",
                      template_folder='../templates',
                      static_folder='../static')

default_breadcrumb_root(blueprint, '.holdingpen')


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@login_required
@register_menu(blueprint, 'personalize.holdingpen', _('Your Pending Actions'))
@register_breadcrumb(blueprint, '.', _('Holdingpen'))
@templated('workflows/hp_index.html')
def index():
    """
    Display main interface of Holdingpen.

    Acts as a hub for catalogers (may be removed)
    """
    # FIXME: Add user filtering
    bwolist = get_holdingpen_objects()
    action_list = get_action_list(bwolist)

    return dict(tasks=action_list)


@blueprint.route('/maintable', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.records', _('Records'))
@login_required
@templated('workflows/hp_maintable.html')
def maintable():
    """Display main table interface of Holdingpen."""
    bwolist = get_holdingpen_objects()
    action_list = get_action_list(bwolist)
    tags = session.get("holdingpen_tags", list())

    if 'version' in request.args:
        if ObjectVersion.MAPPING[int(request.args.get('version'))] not in tags:
            tags += ObjectVersion.MAPPING[[int(request.args.get('version'))]]
    tags_to_print = ""
    for tag in tags:
        if tag:
            tags_to_print += tag + ','
    return dict(bwolist=bwolist,
                action_list=action_list,
                tags=tags_to_print)


@blueprint.route('/details/<int:objectid>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.details', _("Record Details"))
@login_required
def details(objectid):
    """Display info about the object."""
    of = "hd"
    bwobject = BibWorkflowObject.query.get(objectid)
    from invenio.ext.sqlalchemy import db

    formatted_data = bwobject.get_formatted_data(of)
    extracted_data = extract_data(bwobject)

    action_name = bwobject.get_action()
    if action_name:
        action = actions[action_name]
        rendered_actions = action().render(bwobject)
    else:
        rendered_actions = {}

    if bwobject.id_parent:
        hbwobject_db_request = BibWorkflowObject.query.filter(
            db.or_(BibWorkflowObject.id_parent == bwobject.id_parent,
                   BibWorkflowObject.id == bwobject.id_parent,
                   BibWorkflowObject.id == bwobject.id)).all()

    else:
        hbwobject_db_request = BibWorkflowObject.query.filter(
            db.or_(BibWorkflowObject.id_parent == bwobject.id,
                   BibWorkflowObject.id == bwobject.id)).all()

    hbwobject = {ObjectVersion.FINAL: [], ObjectVersion.HALTED: [],
                 ObjectVersion.INITIAL: [], ObjectVersion.RUNNING: []}

    for hbobject in hbwobject_db_request:
        hbwobject[hbobject.version].append({"id": hbobject.id,
                                            "version": hbobject.version,
                                            "date": pretty_date(hbobject.created),
                                            "true_date": hbobject.modified})

    for list_of_object in hbwobject:
        hbwobject[list_of_object].sort(key=lambda x: x["true_date"], reverse=True)

    hbwobject_final = (
        hbwobject[ObjectVersion.INITIAL] +
        hbwobject[ObjectVersion.HALTED] +
        hbwobject[ObjectVersion.FINAL]
    )

    results = []
    for label, res in iteritems(bwobject.get_tasks_results()):
        res_dicts = [item.to_dict() for item in res]
        results.append((label, res_dicts))

    return render_template('workflows/hp_details.html',
                           bwobject=bwobject,
                           rendered_actions=rendered_actions,
                           hbwobject=hbwobject_final,
                           bwparent=extracted_data['bwparent'],
                           info=extracted_data['info'],
                           log=extracted_data['logtext'],
                           data_preview=formatted_data,
                           workflow_func=extracted_data['workflow_func'],
                           workflow=extracted_data['w_metadata'],
                           task_results=results)


@blueprint.route('/restart_record', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (int, 0)})
def restart_record(objectid, start_point='continue_next'):
    """Restart the initial object in its workflow."""
    bwobject = BibWorkflowObject.query.get(objectid)

    workflow = Workflow.query.filter(
        Workflow.uuid == bwobject.id_workflow).first()

    start_delayed(workflow.name, [bwobject.get_data()])
    return 'Record Restarted'


@blueprint.route('/continue_record', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (int, 0)})
def continue_record(objectid):
    """Continue workflow for current object."""
    continue_oid_delayed(oid=objectid, start_point='continue_next')
    return 'Record continued workflow'


@blueprint.route('/restart_record_prev', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (int, 0)})
def restart_record_prev(objectid):
    """Restart the last task for current object."""
    continue_oid_delayed(oid=objectid, start_point="restart_task")
    return 'Record restarted current task'


@blueprint.route('/delete', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (int, 0)})
def delete_from_db(objectid):
    """Delete the object from the db."""
    BibWorkflowObject.delete(objectid)
    return 'Record Deleted'


@blueprint.route('/delete_multi', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwolist': (text_type, "")})
def delete_multi(bwolist):
    """Delete list of objects from the db."""
    from ..utils import parse_bwids

    bwolist = parse_bwids(bwolist)
    for objectid in bwolist:
        delete_from_db(objectid)
    return 'Records Deleted'


@blueprint.route('/resolve', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (text_type, '-1')})
def resolve_action(objectid):
    """Resolve the action taken.

    Will call the resolve() function of the specific action.
    """
    bwobject = BibWorkflowObject.query.get(int(objectid))
    action_name = bwobject.get_action()
    action_form = actions[action_name]
    res = action_form().resolve(bwobject)
    return jsonify(res)


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (text_type, '0'),
                 'of': (text_type, None)})
def entry_data_preview(objectid, of):
    """Present the data in a human readble form or in xml code."""
    from flask import Markup
    from pprint import pformat

    bwobject = BibWorkflowObject.query.get(int(objectid))

    if not bwobject:
        flash("No object found for %s" % (objectid,))
        return jsonify(data={})

    formatted_data = bwobject.get_formatted_data()
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
    """Return the a JSON structure with URL maps and actions."""
    context = {}
    context['url_prefix'] = blueprint.url_prefix
    context['holdingpen'] = {
        "url_load": url_for('holdingpen.load_table'),
        "url_preview": url_for('holdingpen.entry_data_preview'),
        "url_restart_record": url_for('holdingpen.restart_record'),
        "url_restart_record_prev": url_for('holdingpen.restart_record_prev'),
        "url_continue_record": url_for('holdingpen.continue_record'),
    }

    return jsonify(context)


@blueprint.route('/load_table', methods=['GET', 'POST'])
@login_required
@templated('workflows/hp_maintable.html')
def load_table():
    """Get JSON data for the Holdingpen table.

    Function used for the passing of JSON data to DataTables:

    1. First checks for what record version to show
    2. Then the sorting direction.
    3. Then if the user searched for something.

    :return: JSON formatted str from dict of DataTables args.
    """
    tags = session.setdefault("holdingpen_tags", list())
    if request.method == "POST":
        if request.json and "tags" in request.json:
            tags = request.json["tags"]
            session["holdingpen_tags"] = tags
        # This POST came from tags-input.
        # We return here as DataTables will call a GET here after.
        return None

    i_sortcol_0 = request.args.get('iSortCol_0', session.get('iSortCol_0', 0))
    s_sortdir_0 = request.args.get('sSortDir_0', session.get('sSortDir_0', None))

    session["holdingpen_iDisplayStart"] = int(request.args.get('iDisplayStart', session.get('iDisplayLength', 10)))
    session["holdingpen_iDisplayLength"] = int(request.args.get('iDisplayLength', session.get('iDisplayLength', 0)))
    session["holdingpen_sEcho"] = int(request.args.get('sEcho', session.get('sEcho', 0))) + 1

    bwobject_list = get_holdingpen_objects(tags)

    if (i_sortcol_0 and s_sortdir_0) or ("holdingpen_iSortCol_0" in session and "holdingpen_sSortDir_0" in session):
        if i_sortcol_0:
            i_sortcol = int(str(i_sortcol_0))
        else:
            i_sortcol = session["holdingpen_iSortCol_0"]

        if not ('holdingpen_iSortCol_0' in session and "holdingpen_sSortDir_0" in session) or i_sortcol != session['holdingpen_iSortCol_0'] or s_sortdir_0 != session['holdingpen_sSortDir_0']:
            bwobject_list = sort_bwolist(bwobject_list, i_sortcol, s_sortdir_0)
        else:
            bwobject_list = sort_bwolist(bwobject_list, session["holdingpen_iSortCol_0"], session["holdingpen_sSortDir_0"])

    session["holdingpen_iSortCol_0"] = i_sortcol_0
    session["holdingpen_sSortDir_0"] = s_sortdir_0

    table_data = {'aaData': [],
                  'iTotalRecords': len(bwobject_list),
                  'iTotalDisplayRecords': len(bwobject_list),
                  'sEcho': session["holdingpen_sEcho"]}

    records_showing = 0
    for bwo in bwobject_list[
            session["holdingpen_iDisplayStart"]:session["holdingpen_iDisplayStart"]
            + session["holdingpen_iDisplayLength"]]:
        records_showing += 1
        action_name = bwo.get_action()
        action_message = bwo.get_action_message()
        if not action_message:
            action_message = ""

        preformatted = get_formatted_holdingpen_object(bwo)

        action = actions.get(action_name, None)
        mini_action = None
        if action:
            mini_action = getattr(action, "render_mini", None)
        extra_data = bwo.get_extra_data()
        record = bwo.get_data()

        if not hasattr(record, "get"):
            try:
                record = dict(record)
            except (ValueError, TypeError):
                record = {}

        row = render_template('workflows/row_formatter.html',
                              title=preformatted["title"],
                              object=bwo,
                              record=record,
                              extra_data=extra_data,
                              description=preformatted["description"],
                              action=action,
                              mini_action=mini_action,
                              action_message=action_message,
                              pretty_date=pretty_date,
                              )

        row = row.split("<!--sep-->")

        table_data['aaData'].append(row)
    return jsonify(table_data)
