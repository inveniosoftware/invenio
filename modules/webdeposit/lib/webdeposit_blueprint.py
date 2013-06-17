# -*- coding: utf-8 -*-
##
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

"""WebDeposit Flask Blueprint"""

import os

from flask import current_app, \
    render_template, \
    request, \
    jsonify, \
    redirect, \
    url_for, \
    flash, \
    send_file, \
    abort
from werkzeug.utils import secure_filename
from uuid import uuid1 as new_uuid

from invenio.cache import cache
from invenio.webdeposit_load_deposition_types import deposition_types, \
    deposition_metadata
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.webdeposit_utils import get_form, \
    draft_field_list_add, \
    delete_workflow, \
    create_workflow, \
    get_latest_or_new_workflow, \
    get_workflow, \
    draft_field_get_all, \
    draft_form_process_and_validate, \
    draft_form_autocomplete, \
    draft_field_get, \
    set_form_status, \
    get_form_status, \
    create_user_file_system, \
    CFG_DRAFT_STATUS, \
    url_upload,\
    get_all_drafts, \
    deposit_files, \
    delete_file, \
    save_form
from invenio.webuser_flask import current_user
from invenio.bibworkflow_config import CFG_WORKFLOW_STATUS

blueprint = InvenioBlueprint('webdeposit', __name__,
                             url_prefix='/deposit',
                             config='invenio.websubmit_config',
                             menubuilder=[('main.webdeposit',
                                          _('Deposit'),
                                          'webdeposit.index_deposition_types',
                                          2)],
                             breadcrumbs=[(_('Deposit'),
                                          'webdeposit.index_deposition_types')])


@blueprint.route('/upload_from_url/<deposition_type>/<uuid>', methods=['POST'])
@blueprint.invenio_authenticated
def upload_from_url(deposition_type, uuid):
    if request.method == 'POST':
        url = request.form['url']

        if "name" in request.form:
            name = request.form['name']
        else:
            name = None

        if "size" in request.form:
            size = request.form['size']
        else:
            size = None

        unique_filename = url_upload(current_user.get_id(),
                                     deposition_type,
                                     uuid, url, name, size)
        return unique_filename


@blueprint.route('/upload/<deposition_type>/<uuid>', methods=['POST'])
@blueprint.invenio_authenticated
def plupload(deposition_type, uuid):
    """ The file is splitted in chunks on the client-side
        and it is merged again on the server-side

        @return: the path of the uploaded file
    """
    return deposit_files(current_user.get_id(), deposition_type, uuid)


@blueprint.route('/plupload_delete/<uuid>', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def plupload_delete(uuid):
    return delete_file(current_user.get_id(), uuid)


@blueprint.route('/plupload_get_file/<uuid>', methods=['GET'])
@blueprint.invenio_authenticated
def plupload_get_file(uuid):
    filename = request.args.get('filename')
    tmp = ""
    files = draft_field_get(current_user.get_id(), uuid, "files")
    for f in files:
        tmp += f['file'].split('/')[-1] + '<br><br>'
        if filename == f['file'].split('/')[-1]:
            return send_file(f['file'],
                             attachment_filename=f['name'],
                             as_attachment=True)

    return "filename: " + filename + '<br>' + tmp


@blueprint.route('/check_status/<uuid>/', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def check_status(uuid):
    form_status = get_form_status(current_user.get_id(), uuid)
    return jsonify({"status": form_status})


@blueprint.route('/autocomplete/<form_type>/<field>', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def autocomplete(form_type, field):
    """ Returns a list with of suggestions for the field
        based on the current value
    """
    term = request.args.get('term')  # value
    limit = request.args.get('limit', 50, type=int)

    result = draft_form_autocomplete(
        form_type, field, term, limit
    )

    return jsonify(results=result)


@blueprint.route('/save/<uuid>', methods=['POST'])
@blueprint.invenio_authenticated
def error_check(uuid):
    """
    Save and run error check on field values

    The request body must contain a JSON-serialized field/value-dictionary.
    A single or multiple fields may be passed in the dictionary, and values
    may be any JSON-serializable object. Example::

        {
            'title': 'Invenio Software',
            'authors': [['Smith, Joe', 'CERN'],['Smith, Jane','CERN']]
        }

    The response is a JSON-serialized dictionary with the keys:

    * messages: Field/messages-dictionary
    * values: Field/value-dictionary of unsubmitted fields that changed value.
    * <flag>_on: List of fields, which flag changed to on.
    * <flag>_off: List of fields, which flag changed to off.


    The field/messages-dictionary looks like this::

        {'title': {'state': '<state>', 'messages': [,...]}}

    where <state> is either 'success' if field was validated successfully,
    'info' if an information message should be displayed, and respectively the
    same for 'warning' and 'error'.

        Example response::

        {
            'messages': {'title': {'state': '<state>', 'messages': [,...]}},
            'values': {'<field>': <value>, ...},
            'hidden_on': ['<field>', ...],
            'hidden_off': ['<field>', ...],
            'disabled_on': ['<field>', ...],
            'disabled_off': ['<field>', ...],
        }

    @return: A JSON-serialized field/result-dictionary (see above)
    """
    if request.method != 'POST':
        abort(400)

    # Process data, run validation, set in workflow object and return result
    result = draft_form_process_and_validate(current_user.get_id(), uuid, request.json)

    try:
        return jsonify(result)
    except TypeError:
        return jsonify(None)


@blueprint.route('/<deposition_type>/delete/<uuid>')
@blueprint.invenio_authenticated
def delete(deposition_type, uuid):
    """ Deletes the whole deposition with uuid=uuid
        (including form drafts)
        redirects to load another workflow
    """
    if deposition_type not in deposition_metadata:
        flash(_('Invalid deposition type `%s`.' % deposition_type), 'error')
        return redirect(url_for('.index_deposition_types'))
    delete_workflow(current_user.get_id(), uuid)
    flash(deposition_type + _(' deposition deleted!'), 'error')
    return redirect(url_for("webdeposit.index",
                            deposition_type=deposition_type))


@blueprint.route('/<deposition_type>/new/')
@blueprint.invenio_authenticated
def create_new(deposition_type):
    """ Creates new deposition
    """
    if deposition_type not in deposition_metadata:
        flash(_('Invalid deposition type `%s`.' % deposition_type), 'error')
        return redirect(url_for('.index_deposition_types'))
    workflow = create_workflow(deposition_type, current_user.get_id())
    uuid = workflow.get_uuid()
    flash(deposition_type + _(' deposition created!'), 'info')
    return redirect(url_for("webdeposit.add",
                            deposition_type=deposition_type,
                            uuid=uuid))


@blueprint.route('/')
def index_deposition_types():
    """ Renders the deposition types (workflows) list """
    current_app.config['breadcrumbs_map'][request.endpoint] = [
        (_('Home'), '')] + blueprint.breadcrumbs
    drafts = get_all_drafts(current_user.get_id())

    return render_template('webdeposit_index_deposition_types.html',
                           deposition_types=deposition_types,
                           drafts=drafts)


@blueprint.route('/<deposition_type>/')
@blueprint.invenio_authenticated
def index(deposition_type):
    if deposition_type not in deposition_metadata:
        flash(_('Invalid deposition type `%s`.' % deposition_type), 'error')
        return redirect(url_for('.index_deposition_types'))
    current_app.config['breadcrumbs_map'][request.endpoint] = [
        (_('Home'), '')] + blueprint.breadcrumbs + [(deposition_type, None)]
    user_id = current_user.get_id()
    drafts = draft_field_get_all(user_id, deposition_type)

    from invenio.bibworkflow_model import Workflow
    past_depositions = \
        Workflow.get(Workflow.name == deposition_type,
                     Workflow.user_id == user_id,
                     Workflow.status == CFG_WORKFLOW_STATUS.FINISHED).\
        all()

    return render_template('webdeposit_index.html', drafts=drafts,
                           deposition_type=deposition_type,
                           deposition_types=deposition_types,
                           past_depositions=past_depositions)


@blueprint.route('/<deposition_type>/<uuid>', methods=['GET', 'POST'])
@blueprint.invenio_authenticated
def add(deposition_type, uuid):
    """
        Runs the workflows and shows the current form/output of the workflow
        Loads the associated to the uuid workflow.

        if the current step of the workflow renders a form, it loads it.
        if the workflow is finished or in case of error,
        it redirects to the deposition types page
        flashing also the associated message.

        Moreover, it handles a form's POST request for the fields and files,
        and validates the whole form after the submission.

        @param deposition_type: the type of the deposition to be run.
        @param uuid: the universal unique identifier for the workflow.
    """

    status = 0

    if deposition_type not in deposition_metadata:
        flash(_('Invalid deposition type `%s`.' % deposition_type), 'error')
        return redirect(url_for('.index_deposition_types'))

    elif uuid is None:
        # get the latest one. if there is no workflow created
        # lets create a new workflow with given deposition type
        workflow = get_latest_or_new_workflow(deposition_type)
        uuid = workflow.get_uuid()
        #flash(_('Deposition %s') % (uuid,), 'info')
        return redirect(url_for('.add', deposition_type=deposition_type,
                                uuid=uuid))
    else:
        # get workflow with specific uuid
        workflow = get_workflow(uuid, deposition_type)
        if workflow is None:
            flash(_('Deposition with uuid `') + uuid + '` not found.', 'error')
            return redirect(url_for('.index_deposition_types'))

    cache.delete_many(str(current_user.get_id()) + ":current_deposition_type",
                      str(current_user.get_id()) + ":current_uuid")
    cache.add(str(current_user.get_id()) + ":current_deposition_type",
              deposition_type)
    cache.add(str(current_user.get_id()) + ":current_uuid", uuid)

    current_app.config['breadcrumbs_map'][request.endpoint] = [
        (_('Home'), '')] + blueprint.breadcrumbs + \
        [(deposition_type, 'webdeposit.index',
         {'deposition_type': deposition_type}),
         (uuid, 'webdeposit.add',
         {'deposition_type': deposition_type, 'uuid': uuid})]

    if request.method == 'POST':
        # Save the files
        for uploaded_file in request.files.values():
            filename = secure_filename(uploaded_file.filename)
            if filename == "":
                continue

            CFG_USER_WEBDEPOSIT_FOLDER = create_user_file_system(current_user.get_id(),
                                                                 deposition_type,
                                                                 uuid)
            unique_filename = str(new_uuid()) + filename
            file_path = os.path.join(CFG_USER_WEBDEPOSIT_FOLDER,
                                     unique_filename)
            uploaded_file.save(file_path)
            size = os.path.getsize(file_path)
            file_metadata = dict(name=filename, file=file_path, size=size)
            draft_field_list_add(current_user.get_id(), uuid,
                                 "files", file_metadata)

        # Save form values
        form = get_form(current_user.get_id(), uuid, formdata=request.form)

        # Validate form
        if not form.validate():
            # render the form with error messages
            # the `workflow.get_output` function returns also the template
            form.post_process()
            save_form(current_user.get_id(), uuid, form)
            return render_template(**workflow.get_output(form=form,
                                                         form_validation=True))
        #Set the latest form status to finished
        set_form_status(current_user.get_id(), uuid,
                        CFG_DRAFT_STATUS['finished'])
        save_form(current_user.get_id(), uuid, form)

    workflow.run()
    status = workflow.get_status()
    if status != CFG_WORKFLOW_STATUS.FINISHED and \
            status != CFG_WORKFLOW_STATUS.ERROR:
        # render current step of the workflow
        # the `workflow.get_output` function returns also the template
        return render_template(**workflow.get_output())
    elif status == CFG_WORKFLOW_STATUS.FINISHED:
        msg = deposition_type + _(' deposition has been successfully finished.')
        recid = workflow.get_data('recid')
        if recid is not None:
            msg += ' Record available <a href=/record/%s>here</a>.' % recid
        flash(msg, 'success')
        return redirect(url_for('.index_deposition_types'))
    elif status == CFG_WORKFLOW_STATUS.ERROR:
        flash(deposition_type + _(' deposition %s has returned error.'), 'error')
        current_app.logger.error('Deposition: %s has returned error. %d' % uuid)
        return redirect(url_for('.index_deposition_types'))
