# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Holding Pen is a web interface overlay for all BibWorkflowObject's.

This area is targeted to catalogers and administrators for inspecting
and reacting to workflows executions. More importantly, allowing users to deal
with halted workflows.

For example, accepting submissions or other tasks.
"""

from __future__ import unicode_literals

import json
import os

from flask import (
    Blueprint,
    flash,
    jsonify,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask_login import login_required
from flask_menu import register_menu

from invenio.base.decorators import templated, wash_arguments
from invenio.base.i18n import _
from invenio.ext.principal import permission_required
from invenio.utils.date import pretty_date
from invenio.utils.pagination import Pagination

from six import text_type

from ..acl import viewholdingpen
from ..api import continue_oid_delayed, start_delayed
from ..models import BibWorkflowObject, ObjectVersion, Workflow
from ..registry import actions, workflows
from ..utils import (
    alert_response_wrapper,
    extract_data,
    get_action_list,
    get_data_types,
    get_formatted_holdingpen_object,
    get_holdingpen_objects,
    get_previous_next_objects,
    get_rendered_task_results,
    sort_bwolist,
)

blueprint = Blueprint('holdingpen', __name__, url_prefix="/admin/holdingpen",
                      template_folder='../templates',
                      static_folder='../static')

default_breadcrumb_root(blueprint, '.holdingpen')
HOLDINGPEN_WORKFLOW_STATES = {
    ObjectVersion.HALTED: {
        'message': _(ObjectVersion.name_from_version(ObjectVersion.HALTED)),
        'class': 'danger'
    },
    ObjectVersion.WAITING: {
        'message': _(ObjectVersion.name_from_version(ObjectVersion.WAITING)),
        'class': 'warning'
    },
    ObjectVersion.ERROR: {
        'message': _(ObjectVersion.name_from_version(ObjectVersion.ERROR)),
        'class': 'danger'
    },
    ObjectVersion.COMPLETED: {
        'message': _(ObjectVersion.name_from_version(ObjectVersion.COMPLETED)),
        'class': 'success'
    },
    ObjectVersion.INITIAL: {
        'message': _(ObjectVersion.name_from_version(ObjectVersion.INITIAL)),
        'class': 'info'
    },
    ObjectVersion.RUNNING: {
        'message': _(ObjectVersion.name_from_version(ObjectVersion.RUNNING)),
        'class': 'warning'
    }
}


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@login_required
@register_menu(blueprint, 'personalize.holdingpen', _('Your Pending Actions'))
@register_breadcrumb(blueprint, '.', _('Holdingpen'))
@templated('workflows/index.html')
def index():
    """
    Display main interface of Holdingpen.

    Acts as a hub for catalogers (may be removed)
    """
    # FIXME: Add user filtering
    bwolist = get_holdingpen_objects([ObjectVersion.name_from_version(ObjectVersion.HALTED)])
    action_list = get_action_list(bwolist)

    return dict(tasks=action_list)


@blueprint.route('/load', methods=['GET', 'POST'])
@login_required
@templated('workflows/list.html')
@permission_required(viewholdingpen.name)
@wash_arguments({
    'page': (int, 1),
    'per_page': (int, 0),
    'sort_key': (unicode, "created"),
})
def load(page, per_page, sort_key):
    """Load objects for the table."""
    # FIXME: Load tags in this way until wash_arguments handles lists.
    tags = request.args.getlist("tags[]") or []
    sort_key = request.args.get(
        'sort_key', session.get('holdingpen_sort_key', "created")
    )
    per_page = per_page or session.get('holdingpen_per_page') or 10
    object_list = get_holdingpen_objects(tags)
    object_list = sort_bwolist(object_list, sort_key)

    page = max(page, 1)
    pagination = Pagination(page, per_page, len(object_list))

    # Make sure requested page is within limits.
    if pagination.page > pagination.pages:
        pagination.page = pagination.pages

    pages_iteration = []
    for iter_page in pagination.iter_pages():
        res = {"page": iter_page}
        if iter_page == pagination.page:
            res["active"] = True
        else:
            res["active"] = False
        pages_iteration.append(res)

    table_data = {'rows': [],
                  'pagination': {
                    "page": pagination.page,
                    "pages": pagination.pages,
                    "iter_pages": pages_iteration,
                    "per_page": pagination.per_page,
                    "total_count": pagination.total_count
                  }}

    # Add current ids in table for use by previous/next
    session['holdingpen_current_ids'] = [o.id for o in object_list]
    session['holdingpen_sort_key'] = sort_key
    session['holdingpen_per_page'] = per_page
    session['holdingpen_tags'] = tags

    display_start = max(pagination.per_page*(pagination.page-1), 0)
    display_end = min(
        pagination.per_page*pagination.page,
        pagination.total_count
    )
    for bwo in object_list[display_start:display_end]:
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
        bwo._class = HOLDINGPEN_WORKFLOW_STATES[bwo.version]["class"]
        bwo.message = HOLDINGPEN_WORKFLOW_STATES[bwo.version]["message"]
        row = render_template('workflows/list_row.html',
                              title=preformatted["title"],
                              object=bwo,
                              record=record,
                              extra_data=extra_data,
                              description=preformatted["description"],
                              action=action,
                              mini_action=mini_action,
                              action_message=action_message,
                              pretty_date=pretty_date,
                              version=ObjectVersion,
                              )
        table_data['rows'].append(row)
    table_data["rendered_rows"] = "".join(table_data["rows"])
    return jsonify(table_data)


@blueprint.route('/list', methods=['GET', ])
@register_breadcrumb(blueprint, '.records', _('Records'))
@login_required
@permission_required(viewholdingpen.name)
def list_objects():
    """Display main table interface of Holdingpen."""
    tags = session.get(
        "holdingpen_tags",
        [ObjectVersion.name_from_version(ObjectVersion.HALTED)]
    )
    object_list = get_holdingpen_objects(tags)
    action_list = get_action_list(object_list)
    type_list = get_data_types()

    if 'version' in request.args:
        for key, value in ObjectVersion.MAPPING.items():
            if value == int(request.args.get('version')):
                if key not in tags:
                    tags.append(key)

    tags_to_print = []
    for tag in tags:
        if tag:
            tags_to_print.append({
                "text": str(_(tag)),
                "value": tag,
            })

    return render_template(
        'workflows/list.html',
        action_list=action_list,
        tags=json.dumps(tags_to_print),
        object_list=object_list,
        type_list=type_list,
        per_page=session.get('holdingpen_per_page')
    )


@blueprint.route('/<int:objectid>', methods=['GET', 'POST'])
@blueprint.route('/details/<int:objectid>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.details', _("Object Details"))
@login_required
@permission_required(viewholdingpen.name)
def details(objectid):
    """Display info about the object."""
    from ..utils import get_workflow_info
    from invenio.ext.sqlalchemy import db
    from itertools import groupby

    of = "hd"
    bwobject = BibWorkflowObject.query.get_or_404(objectid)
    previous_object, next_object = get_previous_next_objects(
        session.get("holdingpen_current_ids"),
        objectid
    )

    formatted_data = bwobject.get_formatted_data(of)
    extracted_data = extract_data(bwobject)

    action_name = bwobject.get_action()
    if action_name:
        action = actions[action_name]
        rendered_actions = action().render(bwobject)
    else:
        rendered_actions = {}

    if bwobject.id_parent:
        history_objects_db_request = BibWorkflowObject.query.filter(
            db.or_(BibWorkflowObject.id_parent == bwobject.id_parent,
                   BibWorkflowObject.id == bwobject.id_parent,
                   BibWorkflowObject.id == bwobject.id)).all()
    else:
        history_objects_db_request = BibWorkflowObject.query.filter(
            db.or_(BibWorkflowObject.id_parent == bwobject.id,
                   BibWorkflowObject.id == bwobject.id)).all()

    history_objects = {}
    temp = groupby(history_objects_db_request,
                   lambda x: x.version)
    for key, value in temp:
        if key != ObjectVersion.RUNNING:
            value = list(value)
            value.sort(key=lambda x: x.modified, reverse=True)
            history_objects[key] = value

    history_objects = sum(history_objects.values(), [])
    for obj in history_objects:
        obj._class = HOLDINGPEN_WORKFLOW_STATES[obj.version]["class"]
        obj.message = HOLDINGPEN_WORKFLOW_STATES[obj.version]["message"]
    results = get_rendered_task_results(bwobject)
    workflow_definition = get_workflow_info(extracted_data['workflow_func'])
    task_history = bwobject.get_extra_data().get('_task_history', [])
    return render_template('workflows/details.html',
                           bwobject=bwobject,
                           rendered_actions=rendered_actions,
                           history_objects=history_objects,
                           bwparent=extracted_data['bwparent'],
                           info=extracted_data['info'],
                           log=extracted_data['logtext'],
                           data_preview=formatted_data,
                           workflow=extracted_data['w_metadata'],
                           task_results=results,
                           previous_object=previous_object,
                           next_object=next_object,
                           task_history=task_history,
                           workflow_definition=workflow_definition,
                           versions=ObjectVersion,
                           pretty_date=pretty_date,
                           workflow_class=workflows.get(extracted_data['w_metadata'].name),
                           )


@blueprint.route('/files/<int:object_id>/<path:filename>',
                 methods=['POST', 'GET'])
@login_required
@permission_required(viewholdingpen.name)
def get_file_from_task_result(object_id=None, filename=None):
    """Send the requested file to user from a workflow task result.

    Expects a certain file meta-data structure in task result:

    .. code-block:: python

        {
            "type": "Fulltext",
            "filename": "file.pdf",
            "full_path": "/path/to/file",
        }

    """
    bwobject = BibWorkflowObject.query.get_or_404(object_id)
    task_results = bwobject.get_tasks_results()
    if filename in task_results and task_results[filename]:
        fileinfo = task_results[filename][0].get("result", dict())
        directory, actual_filename = os.path.split(fileinfo.get("full_path", ""))
        return send_from_directory(directory, actual_filename)


@blueprint.route('/restart_record', methods=['GET', 'POST'])
@login_required
@permission_required(viewholdingpen.name)
@wash_arguments({'objectid': (int, 0)})
@alert_response_wrapper
def restart_record(objectid, start_point='continue_next'):
    """Restart the initial object in its workflow."""
    bwobject = BibWorkflowObject.query.get_or_404(objectid)

    workflow = Workflow.query.filter(
        Workflow.uuid == bwobject.id_workflow).first()

    start_delayed(workflow.name, [bwobject.get_data()])
    return jsonify(dict(
        category="success",
        message=_("Object restarted successfully.")
    ))


@blueprint.route('/continue_record', methods=['GET', 'POST'])
@login_required
@permission_required(viewholdingpen.name)
@wash_arguments({'objectid': (int, 0)})
@alert_response_wrapper
def continue_record(objectid):
    """Continue workflow for current object."""
    continue_oid_delayed(oid=objectid, start_point='continue_next')
    return jsonify(dict(
        category="success",
        message=_("Object continued with next task successfully.")
    ))


@blueprint.route('/restart_record_prev', methods=['GET', 'POST'])
@login_required
@permission_required(viewholdingpen.name)
@wash_arguments({'objectid': (int, 0)})
@alert_response_wrapper
def restart_record_prev(objectid):
    """Restart the last task for current object."""
    continue_oid_delayed(oid=objectid, start_point="restart_task")
    return jsonify(dict(
        category="success",
        message=_("Object restarted task successfully.")
    ))


@blueprint.route('/delete', methods=['GET', 'POST'])
@login_required
@permission_required(viewholdingpen.name)
@wash_arguments({'objectid': (int, 0)})
@alert_response_wrapper
def delete_from_db(objectid):
    """Delete the object from the db."""
    BibWorkflowObject.delete(objectid)
    return jsonify(dict(
        category="success",
        message=_("Object deleted successfully.")
    ))


@blueprint.route('/delete_multi', methods=['GET', 'POST'])
@login_required
@permission_required(viewholdingpen.name)
@wash_arguments({'bwolist': (text_type, "")})
@alert_response_wrapper
def delete_multi(bwolist):
    """Delete list of objects from the db."""
    from ..utils import parse_bwids
    bwolist = parse_bwids(bwolist)
    for objectid in bwolist:
        delete_from_db(objectid)
    return jsonify(dict(
        category="success",
        message=_("Objects deleted successfully.")
    ))


@blueprint.route('/resolve', methods=['GET', 'POST'])
@login_required
@permission_required(viewholdingpen.name)
def resolve_action():
    """Resolve the action taken.

    Will call the resolve() function of the specific action.
    """
    objectids = request.values.getlist('objectids[]') or []
    ids_length = len(objectids)

    for objectid in objectids:
        bwobject = BibWorkflowObject.query.get_or_404(objectid)
        action_name = bwobject.get_action()
        action_form = actions[action_name]
        res = action_form().resolve(bwobject)

    if ids_length == 1:
        return jsonify(res)
    else:
        return jsonify({
            "message": "{0} number of records resolved.".format(ids_length),
            "category": "info"
        })


@blueprint.route('/entry_data_preview', methods=['GET', 'POST'])
@login_required
@permission_required(viewholdingpen.name)
@wash_arguments({'objectid': (int, 0),
                 'of': (text_type, None)})
def entry_data_preview(objectid, of):
    """Present the data in a human readble form or in xml code."""
    bwobject = BibWorkflowObject.query.get_or_404(objectid)
    if not bwobject:
        flash("No object found for %s" % (objectid,))
        return jsonify(data={})
    formatted_data = bwobject.get_formatted_data(of)
    return jsonify(data=formatted_data)


@blueprint.route('/get_context', methods=['GET', 'POST'])
@login_required
@permission_required(viewholdingpen.name)
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
