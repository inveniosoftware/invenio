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
Holding Pen

Holding Pen is an overlay over all objects (BibWorkflowObject) that
have run through a workflow (BibWorkflowEngine). This area is targeted
to catalogers and super users for inspecting ingestion workflows and
submissions/depositions.

Note: Currently work-in-progress.
"""

import re

from six import iteritems, text_type

from flask import (render_template,
                   Blueprint, request,
                   jsonify, url_for,
                   flash, session, current_app)
from flask.ext.login import login_required
from flask.ext.breadcrumbs import (default_breadcrumb_root,
                                   register_breadcrumb,
)
from flask.ext.menu import register_menu

from invenio.base.decorators import templated, wash_arguments
from invenio.base.i18n import _
from invenio.utils.date import pretty_date

from ..models import BibWorkflowObject, Workflow, ObjectVersion
from ..registry import actions
from ..utils import (get_workflow_definition,
                     sort_bwolist,
)
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
    action_static = []
    for name, action in iteritems(actions):
        if getattr(action, "static", None):
            action_static.extend(action.static)
    my_tags = current_app.config.get('VERSION_SHOWING', [])
    tags_to_print = ""
    for tag in my_tags:
        if tag == ObjectVersion.FINAL:
            tags_to_print += "Done,"
        if tag == ObjectVersion.HALTED:
            tags_to_print += "Need action,"
        if tag == ObjectVersion.RUNNING:
            tags_to_print += "In process,"
        if tag == ObjectVersion.INITIAL:
            tags_to_print += "New,"

    return dict(bwolist=bwolist,
                action_list=action_list,
                action_static=action_static,
                tags=tags_to_print)

@blueprint.route('/batch_action', methods=['GET', 'POST'])
@login_required
@wash_arguments({'bwolist': (text_type, "")})
def batch_action(bwolist):
    """Render action accepting single or multiple records."""
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
    actionlist = []
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
        if bwobject.get_action() not in actionlist:
            actionlist.append(bwobject.get_action())

    action_form = actions[actionlist[0]]

    result = action_form().render(objlist, bwo_parent_list, info_list,
                                  logtext_list, w_metadata_list,
                                  workflow_func_list)
    url, parameters = result

    return render_template(url, **parameters)


@blueprint.route('/load_table', methods=['GET', 'POST'])
@login_required
@templated('workflows/hp_maintable.html')
def load_table():
    """Get JSON data for the Holdingpen table.

    Function used for the passing of JSON data to the DataTable
    1] First checks for what record version to show
    2] then sorting direction,
    3] then if the user searched for something
    and finally it builds the JSON to send.
    """
    version_showing = []
    req = request.json

    if req is not None:
        if "final" in req:
            version_showing.append(ObjectVersion.FINAL)
        if "halted" in req:
            version_showing.append(ObjectVersion.HALTED)
        if "running" in req:
            version_showing.append(ObjectVersion.RUNNING)
        if "initial" in req:
            version_showing.append(ObjectVersion.INITIAL)
        session['workflows_version_showing'] = version_showing
    elif 'workflows_version_showing' in session:
        version_showing = session.get('workflows_version_showing', [])

    i_sortcol_0 = request.args.get('iSortCol_0')
    if i_sortcol_0 == 0:
        i_sortcol_0 = session.get('iSortCol_0', 0)
    s_sortdir_0 = request.args.get('sSortDir_0')
    if not s_sortdir_0:
        s_sortdir_0 = session.get('sSortDir_0', None)
    i_display_start = int(request.args.get('iDisplayStart'))
    i_display_length = int(request.args.get('iDisplayLength'))

    if i_display_length == 0:
        i_display_length = current_app.config.get('iDisplayLength', 10)
    sEcho = int(request.args.get('sEcho')) + 1
    if sEcho == 0:
        sEcho = session.get('sEcho', 0) + 1
    s_search = request.args.get('sSearch', None)
    bwolist = get_holdingpen_objects(ssearch=s_search,
                                     version_showing=version_showing)

    if 'iSortCol_0' in session:
        i_sortcol_0 = int(i_sortcol_0)
        if i_sortcol_0 != session['iSortCol_0'] \
           or s_sortdir_0 != session['sSortDir_0']:
            bwolist = sort_bwolist(bwolist, i_sortcol_0, s_sortdir_0)

    session['iDisplayStart'] = i_display_start
    session['iDisplayLength'] = i_display_length
    session['iSortCol_0'] = i_sortcol_0
    session['sSortDir_0'] = s_sortdir_0
    session['sEcho'] = sEcho

    table_data = {
        "aaData": []
    }

    try:
        table_data['iTotalRecords'] = len(bwolist)
        table_data['iTotalDisplayRecords'] = len(bwolist)
    except TypeError:
        bwolist = get_holdingpen_objects(version_showing=version_showing)
        table_data['iTotalRecords'] = len(bwolist)
        table_data['iTotalDisplayRecords'] = len(bwolist)

    # This will be simplified once Redis is utilized.
    records_showing = 0

    for bwo in bwolist[i_display_start:i_display_start + i_display_length]:
        action_name = bwo.get_action()
        action_message = bwo.get_action_message()
        if not action_message:
            action_message = ""
        action = actions.get(action_name, None)

        records_showing += 1

        mini_action = getattr(action, "mini_action", None)
        record = bwo.get_data()
        if not hasattr(record, "get"):
            try:
                record = dict(record)
            except:
                record = {}

        categories = get_subject_categories(record)
        title = get_title(record)
        identifiers = get_identifiers(record)

        extra_data = bwo.get_extra_data()
        row = render_template('workflows/row_formatter.html',
                              title=title,
                              object=bwo,
                              record=record,
                              extra_data=extra_data,
                              categories=categories,
                              action=action,
                              mini_action=mini_action,
                              action_message=action_message,
                              pretty_date=pretty_date,
                              identifiers=identifiers)

        d = {}
        for key, value in REG_TD.findall(row):
            d[key] = value.strip()

        table_data['aaData'].append(
            [d['id'],
             d['checkbox'],
             d['title'],
             d['identifiers'],
             d['category'],
             d['pretty_date'],
             d['version'],
             d['type'],
             d['details'],
             d['action']
             ]
        )

    table_data['sEcho'] = sEcho
    table_data['iTotalRecords'] = len(bwolist)
    table_data['iTotalDisplayRecords'] = len(bwolist)
    return jsonify(table_data)


@blueprint.route('/get_version_showing', methods=['GET', 'POST'])
@login_required
def get_version_showing():
    """Return current version showing, from flask session."""
    try:
        return session['workflows_version_showing']
    except KeyError:
        return None


@blueprint.route('/details/<int:objectid>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.details', _("Record Details"))
@login_required
def details(objectid):
    """Display info about the object."""
    of = "hd"
    bwobject = BibWorkflowObject.query.get(objectid)
    from sqlalchemy import or_
    formatted_data = bwobject.get_formatted_data(of)

    extracted_data = extract_data(bwobject)
    if bwobject.id_parent:
        hbwobject_db_request = BibWorkflowObject.query.filter(or_(BibWorkflowObject.id_parent == bwobject.id_parent, BibWorkflowObject.id == bwobject.id, BibWorkflowObject.id == bwobject.id_parent)).all()
    else:
        hbwobject_db_request = BibWorkflowObject.query.filter(or_(BibWorkflowObject.id_parent == bwobject.id, BibWorkflowObject.id == bwobject.id)).all()
    hbwobject = []

    for hbobject in hbwobject_db_request:
        hbwobject.append({"id": hbobject.id, "version": hbobject.version, "date": pretty_date(hbobject.created), "true_date": hbobject.created})

    hbwobject.sort(key=lambda x: x["id"])

    try:
        edit_record_action = actions['edit_record_action']()
    except KeyError:
        # Could not load edit_record_action
        edit_record_action = []

    return render_template('workflows/hp_details.html',
                           bwobject=bwobject,
                           hbwobject=hbwobject,
                           bwparent=extracted_data['bwparent'],
                           info=extracted_data['info'],
                           log=extracted_data['logtext'],
                           data_preview=formatted_data,
                           workflow_func=extracted_data['workflow_func'],
                           workflow=extracted_data['w_metadata'],
                           edit_record_action=edit_record_action)


@blueprint.route('/restart_record', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (int, 0)})
def restart_record(objectid, start_point='continue_next'):
    """Restart the initial object in its workflow."""
    bwobject = BibWorkflowObject.query.get(objectid)

    workflow = Workflow.query.filter(
        Workflow.uuid == bwobject.id_workflow).first()

    start(workflow.name, [bwobject.get_data()])
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
    """Delete list of objects from the db"""
    from ..utils import parse_bwids

    bwolist = parse_bwids(bwolist)
    for objectid in bwolist:
        delete_from_db(objectid)
    return 'Records Deleted'


@blueprint.route('/action/<objectid>', methods=['GET', 'POST'])
@register_breadcrumb(blueprint, '.action', _("Action"))
@login_required
def show_action(objectid):
    """Render the action assigned to a specific record."""
    bwobject = BibWorkflowObject.query.filter(
        BibWorkflowObject.id == objectid).first_or_404()

    action = bwobject.get_action()
    # FIXME: add case here if no action
    action_form = actions[action]
    extracted_data = extract_data(bwobject)
    result = action_form().render([bwobject],
                                  [extracted_data['bwparent']],
                                  [extracted_data['info']],
                                  [extracted_data['logtext']],
                                  [extracted_data['w_metadata']],
                                  [extracted_data['workflow_func']])
    url, parameters = result
    #### message
    from sqlalchemy import or_
    if bwobject.id_parent:
        hbwobject_db_request = BibWorkflowObject.query.filter(or_(BibWorkflowObject.id_parent == bwobject.id_parent, BibWorkflowObject.id == bwobject.id, BibWorkflowObject.id == bwobject.id_parent)).all()
    else:
        hbwobject_db_request = BibWorkflowObject.query.filter(or_(BibWorkflowObject.id_parent == bwobject.id, BibWorkflowObject.id == bwobject.id)).all()
    hbwobject = []

    for hbobject in hbwobject_db_request:
        hbwobject.append({"id": hbobject.id, "version": hbobject.version, "date": pretty_date(hbobject.created), "true_date": hbobject.created})

    hbwobject.sort(key=lambda x: x["id"])

    parameters["message"] = bwobject.get_action_message()
    parameters["hbwobject"] = hbwobject
    return render_template("workflows/hp_approval_widget.html", **parameters)


@blueprint.route('/resolve', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (text_type, '-1'),
                 'action': (text_type, 'default')})
def resolve_action(objectid, action):
    """Resolves the action taken.

    Will call the run() function of the specific action.
    """
    action_form = actions[action]
    action_form().run(objectid)
    return "Done"


@blueprint.route('/resolve_edit', methods=['GET', 'POST'])
@login_required
@wash_arguments({'objectid': (text_type, '0'),
                 'form': (text_type, '')})
def resolve_edit(objectid, form):
    """Performs the changes to the record."""
    if request:
        edit_record(request.form)
    return 'Record Edited'


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
    """Return the a JSON structure with URL maps and actions."""
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
        context['version_showing'] = session['workflows_version_showing']
    except KeyError:
        context['version_showing'] = ObjectVersion.HALTED

    context['actions'] = [name for name, action in iteritems(actions)
                          if getattr(action, "static", None)]
    return jsonify(context)


def get_info(bwobject):
    """Parse the hpobject and extract info to a dictionary"""
    info = {}
    if bwobject.get_extra_data()['owner'] != {}:
        info['owner'] = bwobject.get_extra_data()['owner']
    else:
        info['owner'] = 'None'
    info['parent id'] = bwobject.id_parent
    info['workflow id'] = bwobject.id_workflow
    info['object id'] = bwobject.id
    info['action'] = bwobject.get_action()
    return info


def extract_data(bwobject):
    """Extracts needed metadata from BibWorkflowObject.

    Used for rendering the Record's holdingpen table row and
    details and action page.
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
        extracted_data['info']['action'] = bwobject.get_action()
    except (KeyError, AttributeError):
        pass

    extracted_data['w_metadata'] = \
        Workflow.query.filter(Workflow.uuid == bwobject.id_workflow).first()

    workflow_def = get_workflow_definition(extracted_data['w_metadata'].name)
    extracted_data['workflow_func'] = workflow_def
    return extracted_data


def edit_record(form):
    """Call the edit record action."""
    for key in form.iterkeys():
        pass


def get_action_list(object_list):
    """Return a dict of action names mapped to halted objects.

    Get a dictionary mapping from action name to number of Pending
    actions (i.e. halted objects). Used in the holdingpen.index page.
    """
    action_dict = {}
    found_actions = []

    # First get a list of all to count up later
    for bwo in object_list:
        action_name = bwo.get_action()
        if action_name is not None:
            found_actions.append(action_name)

    # Get "real" action name only once per action
    for action_name in set(found_actions):
        if action_name not in actions:
            # Perhaps some old action? Use stored name.
            action_nicename = action_name
        else:
            action = actions[action_name]
            action_nicename = getattr(action, "__title__", action_name)
        action_dict[action_nicename] = found_actions.count(action_name)
    return action_dict


def get_holdingpen_objects(isortcol_0=None,
                           ssortdir_0=None,
                           ssearch=None,
                           version_showing=(ObjectVersion.HALTED,)):
    """Get BibWorkflowObject's for display in Holding Pen.

    Uses DataTable naming for filtering/sorting. Work in progress.
    """
    if isortcol_0:
        isortcol_0 = int(isortcol_0)

    bwobject_list = BibWorkflowObject.query.filter(
        BibWorkflowObject.id_parent==None
        ).filter(not version_showing or BibWorkflowObject.version.in_(version_showing)).all()

    if ssearch and len(ssearch) > 2:
        bwobject_list_tmp = []
        for bwo in bwobject_list:
            extra_data = bwo.get_extra_data()

            if hasattr(bwo.get_data(), "get"):
                data = bwo.get_data()
            else:
                data = {}

            all_parameters = {"record": data, "extra_data": extra_data,
                              "bwo": bwo}
            if not isinstance(ssearch, list):
                if "," in ssearch:
                    ssearch = ssearch.split(",")
                else:
                    ssearch = [ssearch]

            checking_functions = {"title": get_title,
                                  "category": get_subject_categories,
                                  "identifiers": get_identifiers,
                                  "created": get_pretty_date,
                                  "type": get_type

            }

            confirm = 0
            to_add = True
            for term in ssearch:
                for function in checking_functions:
                    if check_ssearch_over_data(term,
                                               checking_functions[function](
                                                       **dict(
                                                               (
                                                                       checking_functions[
                                                                           function].func_code.co_varnames[
                                                                           i],
                                                               all_parameters[
                                                                   checking_functions[
                                                                       function].func_code.co_varnames[
                                                                       i]]) for
                                                               i in
                                                               range(0,
                                                                     checking_functions[
                                                                         function].func_code.co_argcount)))):
                        confirm += 1
                if confirm == 0:
                    to_add = False
                confirm = 0

            if to_add:
                bwobject_list_tmp.append(bwo)
        bwobject_list = bwobject_list_tmp

    if isortcol_0 == -6:
        if ssortdir_0 == 'desc':
            bwobject_list.reverse()

    return bwobject_list


def check_ssearch_over_data(ssearch, data):
    if not isinstance(ssearch, list):
        if "," in ssearch:
            ssearch = ssearch.split(",")
        else:
            ssearch = [ssearch]
    if not isinstance(data, list):
        data = [data]
    count = 0
    for terms in ssearch:
        for datum in data:
            if terms.lower() in datum.lower():
                count += 1
    if count > 0:
        return True
    else:
        return False


def get_subject_categories(record):
    """
    Get the subject categories.
    """
    if hasattr(record, "get"):
        if 'subject' in record:
            lookup = ["subject", "term"]
        elif "subject_term":
            lookup = ["subject_term", "term"]
        else:
            lookup = None
        categories = []
        if lookup:
            primary, secondary = lookup
            category_list = record.get(primary, [])
            if isinstance(category_list, dict):
                category_list = [category_list]
            for subject in category_list:
                category = subject[secondary]
                if len(subject) == 2:
                    if subject.keys()[1] == secondary:
                        source_list = subject[subject.keys()[0]]
                    else:
                        source_list = subject[subject.keys()[1]]
                else:
                    try:
                        source_list = subject['source']
                    except KeyError:
                        source_list = ""
                categories.append(category + "(" + source_list + ")")
        else:
            categories = [" No categories"]
        return categories
    return [" No categories"]


def get_pretty_date(bwo):
    return pretty_date(bwo.created)


def get_type(bwo):
    return bwo.data_type


def get_title(record):
    """
    Get the title.
    """

    extracted_title = []

    if hasattr(record, "get") and "title" in record:
        if isinstance(record["title"], str):
            extracted_title = [record["title"]]
        else:
            for a_title in record["title"]:
                extracted_title.append(record["title"][a_title])
    else:
        extracted_title = [" No title"]
    return extracted_title


def get_identifiers(record):
    """
    Get record identifiers.
    """
    #FIXME: after solving the bibfield problem use the oaiidentifier
    if hasattr(record, "get"):
        return [record.get("system_control_number", {}).get("value", 'No ids')]
    else:
        return ' No ids'

