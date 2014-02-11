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

"""
Deposit Blueprint
"""

import json
from functools import wraps

from flask import current_app, Blueprint, \
    render_template, \
    request, \
    jsonify, \
    redirect, \
    url_for, \
    flash, \
    send_file, \
    abort, \
    make_response
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
from flask.ext.login import current_user, login_required
from flask.ext.breadcrumbs import default_breadcrumb_root, register_breadcrumb
from flask.ext.menu import register_menu

from invenio.base.i18n import _
from ..signals import template_context_created
from ..models import Deposition, DepositionType, \
    DepositionFile, InvalidDepositionType, DepositionDoesNotExists, \
    DraftDoesNotExists, FormDoesNotExists, DepositionNotDeletable, \
    DepositionDraftCacheManager, FilenameAlreadyExists, ForbiddenAction
from ..storage import ChunkedDepositionStorage, \
    DepositionStorage, ExternalFile, UploadError

blueprint = Blueprint(
    'webdeposit',
    __name__,
    url_prefix='/deposit',
    template_folder='../templates',
    static_folder='../static'
)

default_breadcrumb_root(blueprint, '.webdeposit')


def deposition_error_handler(endpoint='.index'):
    """
    Decorator to handle deposition exceptions
    """
    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except InvalidDepositionType:
                if request.is_xhr:
                    abort(400)
                flash(_("Invalid deposition type."), 'danger')
                return redirect(url_for(endpoint))
            except (DepositionDoesNotExists,):
                flash(_("Deposition does not exists."), 'danger')
                return redirect(url_for(endpoint))
            except (DepositionNotDeletable,):
                flash(_("Deposition cannot be deleted."), 'danger')
                return redirect(url_for(endpoint))
            except (DraftDoesNotExists,):
                abort(400)
            except (FormDoesNotExists,):
                abort(400)
            except (UploadError,):
                abort(400)
            except (ForbiddenAction,):
                flash(_("Not allowed."), 'danger')
                return redirect(url_for(endpoint))
            except (UploadError,):
                abort(400)
        return inner
    return decorator


@blueprint.route('/')
@login_required
@register_menu(blueprint, 'main.webdeposit', _('Deposit'), order=2)
@register_breadcrumb(blueprint, '.', _('Deposit'))
def index():
    """
    Renders the deposition index page

    The template context can be customized via the template_context_created
    signal.
    """
    draft_cache = DepositionDraftCacheManager.from_request()
    draft_cache.save()

    ctx = dict(
        deposition_types=DepositionType.all(),
        my_depositions=Deposition.get_depositions(current_user),
        prefill_data=draft_cache.data,
    )

    # Send signal to allow modifications to the template context
    template_context_created.send(
        '%s.%s' % (blueprint.name, index.__name__),
        context=ctx
    )

    return render_template(
        'deposit/index.html',
        **ctx
    )


@blueprint.route('/<depositions:deposition_type>')
@login_required
@register_breadcrumb(blueprint, '.type', _('Type')) # deptype.name_plural
def deposition_type_index(deposition_type):
    if len(DepositionType.keys()) <= 1 and DepositionType.get_default():
        abort(404)

    deptype = DepositionType.get(deposition_type)
    if not deptype.is_enabled():
        abort(404)

    draft_cache = DepositionDraftCacheManager.from_request()
    draft_cache.save()

    ctx = dict(
        my_depositions=Deposition.get_depositions(current_user, type=deptype),
        prefill_data=draft_cache.data,
        deposition_type=deptype
    )

    # Send signal to allow modifications to the template context
    template_context_created.send(
        '%s.%s' % (blueprint.name, deposition_type_index.__name__),
        context=ctx
    )

    return render_template(
        'deposit/deposition_type.html',
        **ctx
    )


@blueprint.route('/<depositions:deposition_type>/create', methods=['POST', 'GET'])
@blueprint.route('/create/', methods=['POST', 'GET'])
@login_required
@deposition_error_handler()
def create(deposition_type=None):
    """
    Create a new deposition
    """
    if request.is_xhr and request.method != 'POST':
        return ('', 405)

    deposition = Deposition.create(current_user, deposition_type)
    deposition.save()

    return (str(deposition.id), 200) if request.is_xhr else redirect(url_for(
        ".run",
        deposition_type=(
            None if deposition.type.is_default()
            else deposition.type.get_identifier()
        ),
        uuid=deposition.id
    ))


@blueprint.route('/<depositions:deposition_type>/<uuid>/<draft_id>', methods=['POST'])
@blueprint.route('/<uuid>/<draft_id>/', methods=['POST'])
@login_required
@deposition_error_handler()
def save(deposition_type=None, uuid=None, draft_id=None):
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

    deposition = Deposition.get(uuid, current_user, type=deposition_type)

    is_submit = request.args.get('submit') == '1'
    is_complete_form = request.args.get('all') == '1'

    data = request.json or MultiDict({})
    if data and 'files' in data:
        deposition.sort_files(data['files'])

    # get_draft() and process() will raise an exception if draft doesn't exist
    # or the draft does not have a form.
    draft = deposition.get_draft(draft_id)
    if draft.is_completed():
        abort(400)
    dummy_form, validated, result = draft.process(
        data, complete_form=is_complete_form
    )

    # Complete draft only if form validates.
    if validated and is_submit:
        draft.complete()

    deposition.save()

    try:
        return jsonify(result)
    except TypeError:
        return jsonify(None)


@blueprint.route('/<depositions:deposition_type>/delete')
@blueprint.route('/<uuid>/delete')
@login_required
@deposition_error_handler()
def delete(deposition_type=None, uuid=None):
    """
    Deletes the whole deposition with uuid=uuid (including form drafts) and
    redirect to index page.
    """
    deposition = Deposition.get(uuid, current_user, type=deposition_type)
    deposition.delete()

    flash(_('%(name)s deleted.', name=deposition.type.name), 'success')
    return redirect(url_for(".index"))


@blueprint.route('/<depositions:deposition_type>/<uuid>', methods=['GET', 'POST'])
@blueprint.route('/<uuid>/', methods=['GET', 'POST'])
@login_required
@deposition_error_handler()
def run(deposition_type=None, uuid=None):
    """
    Runs the workflows and shows the current output of the workflow.
    """
    deposition = Deposition.get(uuid, current_user, type=deposition_type)

    # Set breadcrumb
    #breadcrumb = [(_('Home'), '')] + blueprint.breadcrumbs
    #if not deposition.type.is_default():
    #    breadcrumb.append(
    #        (deposition.type.name, '.deposition_type_index', {
    #            'deposition_type': deposition.type.get_identifier()
    #        })
    #    )

    #breadcrumb.append(
    #    (deposition.title or _('Untitled'), '.run', {
    #        'deposition_type': deposition.type.get_identifier(),
    #        'uuid': deposition.id
    #    })
    #)
    #current_app.config['breadcrumbs_map'][request.endpoint] = breadcrumb

    return deposition.run_workflow()


@blueprint.route('/<depositions:deposition_type>/<uuid>/edit/',
                 methods=['GET', 'POST'])
@blueprint.route('/<uuid>/edit/', methods=['GET', 'POST'])
@login_required
@deposition_error_handler()
def edit(deposition_type=None, uuid=None):
    """
    Reinitialize a completed workflow (i.e. prepare it for editing)
    """
    deposition = Deposition.get(uuid, current_user, type=deposition_type)
    deposition.reinitialize_workflow()
    deposition.save()

    return redirect(url_for(
        ".run",
        deposition_type=(
            None if deposition.type.is_default()
            else deposition.type.get_identifier()
        ),
        uuid=deposition.id
    ))


@blueprint.route('/<depositions:deposition_type>/<uuid>/discard/',
                 methods=['GET', 'POST'])
@blueprint.route('/<uuid>/discard/', methods=['GET', 'POST'])
@login_required
@deposition_error_handler()
def discard(deposition_type=None, uuid=None):
    """
    Stop an inprogress workflow (i.e. discard editing changes)

    Only possible, if workflow already has a sip.
    """
    deposition = Deposition.get(uuid, current_user, type=deposition_type)
    deposition.stop_workflow()
    deposition.save()

    return redirect(url_for(
        ".run",
        deposition_type=(
            None if deposition.type.is_default()
            else deposition.type.get_identifier()
        ),
        uuid=deposition.id
    ))


@blueprint.route('/<depositions:deposition_type>/<uuid>/<draft_id>/status/',
                 methods=['GET', 'POST'])
@blueprint.route('/<uuid>/<draft_id>/status/', methods=['GET', 'POST'])
@login_required
@deposition_error_handler()
def status(deposition_type=None, uuid=None, draft_id=None):
    """
    Get the status of a draft (uncompleted/completed)
    """
    deposition = Deposition.get(uuid, current_user, type=deposition_type)
    completed = deposition.get_draft(draft_id).is_completed()
    return jsonify({"status": 1 if completed else 0})


#@blueprint.route('/%s/<uuid>/file/url/' % deptypes, methods=['POST'])
@blueprint.route('/<uuid>/file/url/', methods=['POST'])
@login_required
@deposition_error_handler()
def upload_url(deposition_type=None, uuid=None):
    """
    Upload a new file by use of a URL
    """
    deposition = Deposition.get(uuid, current_user, type=deposition_type)

    # TODO: Improve to read URL as a chunked file to prevent overfilling
    # memory.
    url_file = ExternalFile(
        request.form['url'],
        request.form.get('name', None),
    )

    df = DepositionFile(backend=DepositionStorage(deposition.id))

    for f in deposition.files:
        if f.name == url_file.filename:
            raise FilenameAlreadyExists(f.name)

    if df.save(url_file, filename=secure_filename(url_file.filename)):
        deposition.add_file(df)
        deposition.save()

    url_file.close()

    return jsonify(
        dict(filename=df.name, id=df.uuid, checksum=df.checksum)
    )


#@blueprint.route('/%s/<uuid>/file/' % deptypes, methods=['POST'])
@blueprint.route('/<uuid>/file/', methods=['POST'])
@login_required
@deposition_error_handler()
def upload_file(deposition_type=None, uuid=None):
    """
    Upload a new file (with chunking support)
    """
    deposition = Deposition.get(uuid, current_user, type=deposition_type)

    uploaded_file = request.files['file']
    filename = secure_filename(
        request.form.get('name') or uploaded_file.filename
    )
    chunk = request.form.get('chunk', None)
    chunks = request.form.get('chunks', None)

    if chunk is not None and chunks is not None:
        backend = ChunkedDepositionStorage(deposition.id)
        kwargs = dict(chunk=chunk, chunks=chunks)
    else:
        backend = DepositionStorage(deposition.id)
        kwargs = {}

    df = DepositionFile(backend=backend)

    if df.save(uploaded_file, filename=filename, **kwargs):
        try:
            deposition.add_file(df)
            deposition.save()
        except FilenameAlreadyExists as e:
            df.delete()
            raise e

        return jsonify(
            dict(filename=df.name, id=df.uuid, checksum=df.checksum)
        )

    return jsonify(dict(filename=df.name, id=df.uuid, checksum=None))


#@blueprint.route('/%s/<uuid>/file/delete/' % deptypes,
#                 methods=['POST'])
@blueprint.route('/<uuid>/file/delete/', methods=['POST'])
@login_required
@deposition_error_handler()
def delete_file(deposition_type=None, uuid=None):
    """
    Delete an uploaded file
    """
    deposition = Deposition.get(uuid, current_user, type=deposition_type)

    try:
        df = deposition.remove_file(request.form['file_id'])
        df.delete()

        deposition.save()

        return ('', 200)
    except Exception as e:
        current_app.logger.error('Deposition: delete file error', e)
        return ('', 400)


#@blueprint.route('/%s/<uuid>/file/' % deptypes, methods=['GET'])
@blueprint.route('/<uuid>/file/', methods=['GET'])
@login_required
@deposition_error_handler()
def get_file(deposition_type=None, uuid=None):
    """
    Download an uploaded file
    """
    deposition = Deposition.get(uuid, current_user, type=deposition_type)

    df = deposition.get_file(request.args.get('file_id'))

    if df.is_local():
        return send_file(
            df.get_syspath(),
            attachment_filename=df.name,
            as_attachment=True
        )
    else:
        return redirect(df.get_url())


@blueprint.route(
    '/<depositions:deposition_type>/<uuid>/<draft_id>/<field_name>/',
    methods=['GET', 'POST'])
@blueprint.route('/<uuid>/<draft_id>/<field_name>/', methods=['GET', 'POST'])
@login_required
def autocomplete(deposition_type=None, uuid=None, draft_id=None,
                 field_name=None):
    """
    Auto-complete a form field
    """
    term = request.args.get('term')  # value
    limit = request.args.get('limit', 50, type=int)

    deposition = Deposition.get(uuid, current_user, type=deposition_type)
    formclass = deposition.type.draft_definitions.get(draft_id)
    if formclass:
        form = formclass()
        result = form.autocomplete(field_name, term, limit=limit)
        result = result if result is not None else []
    else:
        result = []

    # jsonify doesn't return lists as top-level items.
    resp = make_response(
        json.dumps(result, indent=None if request.is_xhr else 2)
    )
    resp.mimetype = "application/json"
    return resp
