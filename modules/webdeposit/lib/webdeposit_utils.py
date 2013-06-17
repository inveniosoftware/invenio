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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

""" WebDeposit Utils
Set of utilities to be used by blueprint, forms and fields.

It contains functions to start a workflow, retrieve it and edit its data.
The basic entities are the forms and fields which are stored in json.
(forms are referred as drafts before they haven't been submitted yet.)

The file field is handled separately and all the files are attached in the json
as a list in the 'files' key.

Some functions contain the keyword `preingest`. This refers to the json that is
stored in the 'pop_obj' key, which is used to store data before running the
workflow. This is being used e.g. in the wedbeposit api where the workflow is
being run without a user submitting the forms, so this json is being used to
preinsert data into the webdeposit workflow.
"""


import os
import shutil
from flask import request
from glob import iglob
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequestKeyError
from werkzeug import MultiDict
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound
from uuid import uuid1 as new_uuid
from urllib2 import urlopen, URLError

from invenio.cache import cache
from invenio.sqlalchemyutils import db
from invenio.webdeposit_model import WebDepositDraft
from invenio.bibworkflow_model import Workflow
from invenio.bibworkflow_config import CFG_WORKFLOW_STATUS
from invenio.webdeposit_load_forms import forms
from invenio.webdeposit_form import CFG_FIELD_FLAGS
from invenio.webuser_flask import current_user
from invenio.webdeposit_load_deposition_types import deposition_metadata
from invenio.webdeposit_workflow import DepositionWorkflow
from invenio.webdeposit_workflow_utils import render_form
from invenio.config import CFG_WEBDEPOSIT_UPLOAD_FOLDER


CFG_DRAFT_STATUS = {
    'unfinished': 0,
    'finished': 1
}


#
# Setters/Getters for bibworklflow
#

def draft_getter(step=None):
    """Returns a json with the current form values.
    If step is None, the latest draft is returned."""
    def draft_getter_func(json):
        try:
            if step is None:
                return json['drafts'][max(json['drafts'])]
            else:
                try:
                    return json['drafts'][step]
                except KeyError:
                    pass

                try:
                    return json['drafts'][unicode(step)]
                except KeyError:
                    pass
                raise NoResultFound
        except KeyError:
            try:
                return {'timestamp': json['pop_obj']['timestamp']}
            except KeyError:
                # there is no pop object
                return None
    return draft_getter_func


def draft_setter(step=None, key=None, value=None, data=None, field_setter=False):
    """Alters a draft's specified value.
    If the field_setter is true, it uses the key value to update
    the dictionary `form_values` otherwise it updates the draft."""
    def draft_setter_func(json):
        try:
            if step is None:
                draft = json['drafts'][max(json['drafts'])]
            else:
                draft = json['drafts'][step]
        except (ValueError, KeyError):
            # There are no drafts or they are empty
            return

        if key:
            if field_setter:
                draft['form_values'][key] = value
            else:
                draft[key] = value

        if data:
            if field_setter:
                draft['form_values'].update(data)
            else:
                draft.update(data)

        draft['timestamp'] = str(datetime.now())
    return draft_setter_func


def add_draft(draft):
    """ Adds a form draft. """
    def setter(json):
        step = draft.pop('step')
        if not 'drafts' in json:
            json['drafts'] = {}
        if not step in json['drafts'] and \
           not unicode(step) in json['drafts']:
            json['drafts'][step] = draft
    return setter


def draft_field_list_setter(field_name, value):
    def setter(json):
        try:
            draft = json['drafts'][max(json['drafts'])]
        except (ValueError, KeyError):
            # There are no drafts or they are empty
            return
        values = draft['form_values']
        try:
            if isinstance(values[field_name], list):
                values[field_name].append(value)
            else:
                new_values_list = [values[field_name]]
                new_values_list.append(value)
                values[field_name] = new_values_list
        except KeyError:
            values[field_name] = [value]

        draft['timestamp'] = str(datetime.now())
    return setter


#
# Workflow functions
#

def get_latest_or_new_workflow(deposition_type, user_id=None):
    """ Creates new workflow or returns a new one """

    user_id = user_id or current_user.get_id()
    wf = deposition_metadata[deposition_type]["workflow"]

    # get latest draft in order to get workflow's uuid
    try:
        latest_workflow = Workflow.get_most_recent(
            Workflow.user_id == user_id,
            Workflow.name == deposition_type,
            Workflow.module_name == 'webdeposit',
            Workflow.status != CFG_WORKFLOW_STATUS.FINISHED)
    except NoResultFound:
        # We didn't find other workflows
        # Let's create a new one
        return DepositionWorkflow(deposition_type=deposition_type,
                                  workflow=wf)

    # Create a new workflow
    # based on the latest draft's uuid
    uuid = latest_workflow. uuid
    return DepositionWorkflow(deposition_type=deposition_type,
                              workflow=wf, uuid=uuid)


def get_workflow(uuid, deposition_type=None):
    """ Returns a workflow instance with uuid=uuid or None """

    # Check if uuid exists first and get the deposition_type if None
    try:
        workflow = Workflow.get(uuid=uuid).one()
        if deposition_type is None:
            deposition_type = workflow.name
    except NoResultFound:
        return None

    try:
        wf = deposition_metadata[deposition_type]["workflow"]
    except KeyError:
        # deposition type not found
        return None
    return DepositionWorkflow(uuid=uuid,
                              deposition_type=deposition_type,
                              workflow=wf)


def create_workflow(deposition_type, user_id=None):
    """ Creates a new workflow and returns it """
    try:
        wf = deposition_metadata[deposition_type]["workflow"]
    except KeyError:
        # deposition type not found
        return None

    return DepositionWorkflow(deposition_type=deposition_type,
                              workflow=wf, user_id=user_id)


def delete_workflow(dummy_user_id, uuid):
    """ Deletes all workflow related data
        (workflow and drafts)
    """
    Workflow.delete(uuid=uuid)


#
# Form loading and saving functions
#
def get_form(user_id, uuid, step=None, formdata=None, load_draft=True,
             validate_draft=False):
    """
    Returns the current state of the workflow in a form or a previous
    state (step)

    @param user_id:

    @param uuid:

    @param step:

    @param formdata:
        Dictionary of formdata.
    @param validate_draft:
        If draft data exists, and no formdata is provided, the form will be
        validated if this parameter is set to true.
    """
    # Get draft data
    if load_draft:
        try:

            webdeposit_draft = \
                Workflow.get_extra_data(user_id=user_id,
                                        uuid=uuid,
                                        getter=draft_getter(step))
        except (ValueError, NoResultFound):
            # No drafts found
            return None

    # If a field is not present in formdata, Form.process() will assume it is
    # blank instead of using the draft_data value. Most of the time we are only
    # submitting a single field in JSON via AJAX requests. We therefore reset
    # non-submitted fields to the draft_data value.
    draft_data = webdeposit_draft['form_values'] if load_draft else {}
    if formdata:
        formdata = MultiDict(formdata)
    form = forms[webdeposit_draft['form_type']](formdata=formdata, **draft_data)
    if formdata:
        form.reset_field_data(exclude=formdata.keys())

    # Set field flags
    if load_draft:
        for name, flags in webdeposit_draft.get('form_field_flags', {}).items():
            for check_flags in CFG_FIELD_FLAGS:
                if check_flags in flags:
                    setattr(form[name].flags, check_flags, True)
                else:
                    setattr(form[name].flags, check_flags, False)

    # Process files
    if 'files' in draft_data:
        # FIXME: sql alchemy(0.8.0) returns the value from the
        #        column form_values with keys and values in unicode.
        #        This creates problem when the dict is rendered
        #        in the page to be used by javascript functions. There must
        #        be a more elegant way than decoding the dict from unicode.

        draft_data['files'] = decode_dict_from_unicode(draft_data['files'])
        for file_metadata in draft_data['files']:
            # Replace the path with the unique filename
            if isinstance(file_metadata, basestring):
                import json
                file_metadata = json.loads(file_metadata)
            filepath = file_metadata['file'].split('/')
            unique_filename = filepath[-1]
            file_metadata['unique_filename'] = unique_filename
        form.__setattr__('files', draft_data['files'])
    else:
        form.__setattr__('files', {})

    if validate_draft and draft_data and formdata is None:
        form.validate()

    return form


def save_form(user_id, uuid, form):
    """
    Saves the draft form_values and form_field_flags of a form.
    """
    json_data = dict((key, value) for key, value in form.json_data.items()
                if value is not None)

    draft_data_update = {
        'form_values': json_data,
        'form_field_flags': form.flags,
    }

    Workflow.set_extra_data(
        user_id=user_id,
        uuid=uuid,
        setter=draft_setter(data=draft_data_update)
    )


def get_form_status(user_id, uuid, step=None):
    try:
        webdeposit_draft = \
            Workflow.get_extra_data(user_id=user_id,
                                    uuid=uuid,
                                    getter=draft_getter(step))
    except ValueError:
        # No drafts found
        raise NoResultFound
    except NoResultFound:
        return None

    return webdeposit_draft['status']


def set_form_status(user_id, uuid, status, step=None):
    try:
        Workflow.set_extra_data(user_id=user_id,
                                uuid=uuid,
                                setter=draft_setter(step, 'status', status))
    except ValueError:
        # No drafts found
        raise NoResultFound
    except NoResultFound:
        return None


def get_last_step(steps):
    if type(steps[-1]) is list:
        return get_last_step[-1]
    else:
        return steps[-1]


def get_current_step(uuid):
    webdep_workflow = Workflow.get(Workflow.uuid == uuid).one()
    steps = webdep_workflow.task_counter

    return get_last_step(steps)


""" Draft Functions (or instances of forms)
"""


def draft_field_get(user_id, uuid, field_name, subfield_name=None):
    """ Returns the value of a field
        or, in case of error, None
    """

    values = \
        Workflow.get_extra_data(user_id=user_id, uuid=uuid,
                                getter=draft_getter())['form_values']

    try:
        if subfield_name is not None:
            return values[field_name][subfield_name]
        return values[field_name]
    except KeyError:
        return None


def draft_form_autocomplete(form_type, field_name, term, limit):
    """
    Auto-complete field value
    """
    try:
        form = forms[form_type]()
        return form.autocomplete(field_name, term, limit=limit)
    except KeyError:
        return []


def draft_form_process_and_validate(user_id, uuid, data):
    """
    Process, validate and store incoming form data and return response.
    """
    # The form is initialized with form and draft data. The original draft_data
    # is accessible in Field.object_data, Field.raw_data is the new form data
    # and Field.data is the processed form data or the original draft data.
    #
    # Behind the scences, Form.process() is called, which in turns call
    # Field.process_data(), Field.process_formdata() and any filters defined.
    #
    # Field.object_data contains the value of process_data(), while Field.data
    # contains the value of process_formdata() and any filters applied.
    form = get_form(user_id, uuid=uuid, formdata=data)

    # Run form validation which will call Field.pre_valiate(), Field.validators,
    # Form.validate_<field>() and Field.post_validate(). Afterwards Field.data
    # has been validated and any errors will be present in Field.errors.
    form.validate()

    # Call Form.run_processors() which in turn will call Field.run_processors()
    # that allow fields to set flags (hide/show) and values of other fields
    # after the entire formdata has been processed and validated.
    validated_flags, validated_data, validated_msgs = (
        form.flags, form.data, form.messages
    )
    form.post_process(fields=data.keys())
    post_processed_flags, post_processed_data, post_processed_msgs = (
        form.flags, form.data, form.messages
    )

    # Save draft data
    save_form(user_id, uuid, form)

    ### Build result dictionary
    process_field_names = data.keys()
    # Determine if some fields where changed during post-processing.
    changed_values = dict((name, value) for name, value in post_processed_data.items() if validated_data[name] != value)
    # Determine changed flags
    changed_flags = dict((name, flags) for name, flags in post_processed_flags.items() if validated_flags[name] != flags)
    # Determine changed messages
    changed_msgs = dict((name, messages) for name, messages in post_processed_msgs.items() if validated_msgs[name] != messages or name in process_field_names)

    result = {}
    if changed_msgs:
        result['messages'] = changed_msgs
    if changed_values:
        result['values'] = changed_values
    if changed_flags:
        for flag in CFG_FIELD_FLAGS:
            fields = [(name, flag in field_flags) for name, field_flags in changed_flags.items()]
            result[flag+'_on'] = map(lambda x: x[0], filter(lambda x: x[1], fields))
            result[flag+'_off'] = map(lambda x: x[0], filter(lambda x: not x[1], fields))

    return result


def draft_field_set(user_id, uuid, field_name, value):
    """ Alters the value of a field """

    Workflow.set_extra_data(user_id=user_id, uuid=uuid,
                            setter=draft_setter(key=field_name, value=value,
                                                field_setter=True))


def draft_field_list_add(user_id, uuid, field_name, value,
                         dummy_subfield=None):
    """Adds value to field
    Used for fields that contain multiple values
    e.g.1: { field_name : value1 } OR
           { field_name : [value1] }
           -->
           { field_name : [value1, value2] }
    e.g.2  { }
           -->
           { field_name : [value] }
    e.g.3  { }
           -->
           { field_name : {key : value} }
    """

    Workflow.set_extra_data(user_id=user_id, uuid=uuid,
                            setter=draft_field_list_setter(field_name, value))


def preingest_form_data(user_id, form_data, uuid=None,
                        append=False, cached_data=False):
    """Used to insert form data to the workflow before running it
    Creates an identical json structure to the draft json.
    If cached_data is enabled, the data will be used by the next workflow
    initiated by the user, so the uuid can be ommited in this case.

    @param user_id: the user id

    @param uuid: the id of the workflow

    @param form_data: a json with field_name -> value structure

    @param append: set to True if you want to append the values to the existing
                   ones

    @param cached_data: set to True if you want to cache the data.
    """
    def preingest_data(form_data, append):
        def preingest(json):
            if 'pop_obj' not in json:
                json['pop_obj'] = {}
            for field, value in form_data.items():
                if append:
                    try:
                        if isinstance(json['pop_obj'][field], list):
                            json['pop_obj'][field].append(value)
                        else:
                            new_values_list = [json['pop_obj'][field]]
                            new_values_list.append(value)
                            json['pop_obj'][field] = new_values_list
                    except KeyError:
                        json['pop_obj'][field] = [value]
                else:
                    json['pop_obj'][field] = value
            json['pop_obj']['timestamp'] = str(datetime.now())
        return preingest

    if cached_data:
        cache.set(str(user_id) + ':cached_form_data', form_data)
    else:
        Workflow.set_extra_data(user_id=user_id, uuid=uuid,
                                setter=preingest_data(form_data, append))

        # Ingest the data in the forms, in case there are any
        if append:
            for field_name, value in form_data.items():
                draft_field_list_add(user_id, uuid, field_name, value)
        else:
            for field_name, value in form_data.items():
                draft_field_set(user_id, uuid, field_name, value)


def get_preingested_form_data(user_id, uuid=None, key=None, cached_data=False):
    def get_preingested_data(key):
        def getter(json):
            if 'pop_obj' in json:
                if key is None:
                    return json['pop_obj']
                else:
                    return json['pop_obj'][key]
            else:
                return {}
        return getter

    if cached_data:
        return cache.get(str(user_id) + ':cached_form_data')
    return Workflow.get_extra_data(user_id, uuid=uuid,
                                   getter=get_preingested_data(key))


def validate_preingested_data(user_id, uuid, deposition_type=None):
    """Validates all preingested data by trying to match the json with every
    form. Then the validation function is being called for each form.
    """
    form_data = get_preingested_form_data(user_id, uuid)

    deposition = get_workflow(uuid, deposition_type)

    form_types = []
    # Get all form types from workflow
    for fun in deposition.workflow:
        if '__form_type__' in fun.__dict__:
            form_render = render_form(forms[fun.__form_type__])
            if form_render.func_code == fun.func_code:
                form_types.append(fun.__form_type__)

    errors = {}
    for form_type in form_types:
        form = forms[form_type]()
        for field in form:
            if field.name in form_data:
                field.data = form_data.pop(field.name)

        form.validate()

        errors.update(form.errors)

    return errors


def get_all_drafts(user_id):
    """ Returns a dictionary with deposition types and their """
    return dict(
        db.session.
        query(Workflow.name,
              db.func.count(Workflow.uuid)).
        filter(Workflow.status != CFG_WORKFLOW_STATUS.FINISHED,
               Workflow.user_id == user_id).
        group_by(Workflow.name).
        all())

    drafts = dict(
        db.session.query(Workflow.name,
                         db.func.count(
                         db.func.distinct(WebDepositDraft.uuid))).
        join(WebDepositDraft.workflow).
        filter(db.and_(Workflow.user_id == user_id,
                       Workflow.status != CFG_WORKFLOW_STATUS.FINISHED)).
        group_by(Workflow.name).all())

    return drafts


def get_draft(user_id, uuid, field_name=None):
    """ Returns draft values in a field_name => field_value dictionary
        or if field_name is defined, returns the associated value
    """

    draft = Workflow.get(user_id=user_id, uuid=uuid)

    form_values = draft['form_values']

    if field_name is None:
        return form_values
    else:
        try:
            return form_values[field_name]
        except KeyError:  # field_name doesn't exist
            return form_values  # return whole row


def draft_field_get_all(user_id, deposition_type):
    """ Returns a list with values of the field_names specified
        containing all the latest drafts
        of deposition of type=deposition_type
    """

    ## Select drafts with max step workflow.
    workflows = Workflow.get(Workflow.status != CFG_WORKFLOW_STATUS.FINISHED,
                             Workflow.user_id == user_id,
                             Workflow.name == deposition_type,
                             Workflow.module_name == 'webdeposit').all()

    drafts = []
    get_max_draft = draft_getter()

    class Draft(object):
        def __init__(self, dictionary, workflow):
            for k, v in dictionary.items():
                setattr(self, k, v)
            setattr(self, 'workflow', workflow)
            setattr(self, 'uuid', workflow.uuid)

    for workflow in workflows:
        max_draft = get_max_draft(workflow.extra_data)
        if max_draft is not None:
            drafts.append(Draft(max_draft, workflow))

    drafts = sorted(drafts, key=lambda d: d.timestamp, reverse=True)
    return drafts


def create_user_file_system(user_id, deposition_type, uuid):
    # Check if webdeposit folder exists
    if not os.path.exists(CFG_WEBDEPOSIT_UPLOAD_FOLDER):
        os.makedirs(CFG_WEBDEPOSIT_UPLOAD_FOLDER)

    # Create user filesystem
    # user/deposition_type/uuid/files
    CFG_USER_WEBDEPOSIT_FOLDER = os.path.join(CFG_WEBDEPOSIT_UPLOAD_FOLDER,
                                              "user_" + str(user_id))
    if not os.path.exists(CFG_USER_WEBDEPOSIT_FOLDER):
        os.makedirs(CFG_USER_WEBDEPOSIT_FOLDER)

    CFG_USER_WEBDEPOSIT_FOLDER = os.path.join(CFG_USER_WEBDEPOSIT_FOLDER,
                                              deposition_type)
    if not os.path.exists(CFG_USER_WEBDEPOSIT_FOLDER):
        os.makedirs(CFG_USER_WEBDEPOSIT_FOLDER)

    CFG_USER_WEBDEPOSIT_FOLDER = os.path.join(CFG_USER_WEBDEPOSIT_FOLDER,
                                              uuid)
    if not os.path.exists(CFG_USER_WEBDEPOSIT_FOLDER):
        os.makedirs(CFG_USER_WEBDEPOSIT_FOLDER)

    return CFG_USER_WEBDEPOSIT_FOLDER


def decode_dict_from_unicode(unicode_input):
    if isinstance(unicode_input, dict):
        return dict((decode_dict_from_unicode(key),
                     decode_dict_from_unicode(value))
                    for key, value in unicode_input.iteritems())
    elif isinstance(unicode_input, list):
        return [decode_dict_from_unicode(element) for element in unicode_input]
    elif isinstance(unicode_input, unicode):
        return unicode_input.encode('utf-8')
    else:
        return unicode_input


def url_upload(user_id, deposition_type, uuid, url, name=None, size=None):

    try:
        data = urlopen(url).read()
    except URLError:
        return "Error"

    CFG_USER_WEBDEPOSIT_FOLDER = create_user_file_system(user_id,
                                                         deposition_type,
                                                         uuid)
    unique_filename = str(new_uuid()) + name
    file_path = os.path.join(CFG_USER_WEBDEPOSIT_FOLDER,
                             unique_filename)
    f = open(file_path, 'wb')
    f.write(data)

    if size is None:
        size = os.path.getsize(file_path)
    if name is None:
        name = url.split('/')[-1]
    file_metadata = dict(name=name, file=file_path, size=size)
    draft_field_list_add(current_user.get_id(), uuid,
                         "files", file_metadata)

    return unique_filename


def deposit_files(user_id, deposition_type, uuid, preingest=False):
    """Attach files to a workflow
    Upload a single file or a file in chunks.
    Function must be called within a blueprint function that handles file
    uploading.

    Request post parameters:
        chunks: number of chunks
        chunk: current chunk number
        name: name of the file

    @param user_id: the user id

    @param deposition_type: the deposition the files will be attached

    @param uuid: the id of the deposition

    @param preingest: set to True if you want to store the file metadata in the
                      workflow before running the workflow, i.e. to bind the
                      files to the workflow and not in the last form draft.

    @return: the path of the uploaded file
    """
    if request.method == 'POST':
        try:
            chunks = request.form['chunks']
            chunk = request.form['chunk']
        except KeyError:
            chunks = None
            pass

        current_chunk = request.files['file']
        try:
            name = request.form['name']
        except BadRequestKeyError:
            name = current_chunk.filename
        try:
            filename = secure_filename(name) + "_" + chunk
        except UnboundLocalError:
            filename = secure_filename(name)

        CFG_USER_WEBDEPOSIT_FOLDER = create_user_file_system(user_id,
                                                             deposition_type,
                                                             uuid)

        # Save the chunk
        current_chunk.save(os.path.join(CFG_USER_WEBDEPOSIT_FOLDER, filename))

        unique_filename = ""

        if chunks is None:  # file is a single chunk
            unique_filename = str(new_uuid()) + filename
            old_path = os.path.join(CFG_USER_WEBDEPOSIT_FOLDER, filename)
            file_path = os.path.join(CFG_USER_WEBDEPOSIT_FOLDER,
                                     unique_filename)
            os.rename(old_path, file_path)  # Rename the chunk
            if current_chunk.content_length != 0:
                size = current_chunk.content_length
            else:
                size = os.path.getsize(file_path)
            content_type = current_chunk.content_type or ''
            file_metadata = dict(name=name, file=file_path,
                                 content_type=content_type, size=size)
            if preingest:
                preingest_form_data(user_id, uuid, {'files': file_metadata})
            else:
                draft_field_list_add(user_id, uuid,
                                     "files", file_metadata)
        elif int(chunk) == int(chunks) - 1:
            '''All chunks have been uploaded!
                start merging the chunks'''
            filename = secure_filename(name)
            chunk_files = []
            for chunk_file in iglob(os.path.join(CFG_USER_WEBDEPOSIT_FOLDER,
                                                 filename + '_*')):
                chunk_files.append(chunk_file)

            # Sort files in numerical order
            chunk_files.sort(key=lambda x: int(x.split("_")[-1]))

            unique_filename = str(new_uuid()) + filename
            file_path = os.path.join(CFG_USER_WEBDEPOSIT_FOLDER,
                                     unique_filename)
            destination = open(file_path, 'wb')
            for chunk in chunk_files:
                shutil.copyfileobj(open(chunk, 'rb'), destination)
                os.remove(chunk)
            destination.close()
            size = os.path.getsize(file_path)
            file_metadata = dict(name=name, file=file_path, size=size)
            if preingest:
                preingest_form_data(user_id, uuid, {'files': file_metadata},
                                    append=True)
            else:
                draft_field_list_add(user_id, uuid,
                                     "files", file_metadata)
    return unique_filename


def delete_file(user_id, uuid, preingest=False):
    if request.method == 'POST':
        files = draft_field_get(user_id, uuid, "files")
        result = "File Not Found"
        filename = request.form['filename']
        if preingest:
            files = get_preingested_form_data(user_id, uuid, 'files')
        else:
            files = draft_field_get(user_id, uuid, "files")

        for i, f in enumerate(files):
            if filename == f['file'].split('/')[-1]:
                # get the unique name from the path
                os.remove(f['file'])
                del files[i]
                result = str(files) + "              "
                if preingest:
                    preingest_form_data(user_id, uuid, files)
                else:
                    draft_field_set(current_user.get_id(), uuid,
                                    "files", files)
                result = "File " + f['name'] + " Deleted"
                break
    return result
