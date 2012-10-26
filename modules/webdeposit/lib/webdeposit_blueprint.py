# -*- coding: utf-8 -*-
##
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

"""WebDeposit Flask Blueprint"""
import os
import shutil
import json
from werkzeug import *
from glob import iglob
from flask import g, render_template, \
                  request, jsonify, redirect, url_for, current_app, \
                  send_from_directory
from wtforms import Form

from invenio.cache import cache
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from invenio.SherpaRomeo import SherpaRomeoSearch

from webdeposit_utils import *
from webdeposit_load_forms import forms

globals().update(forms)


#from invenio.webuser_flask import current_user

blueprint = InvenioBlueprint('websubmit', __name__,
                              url_prefix="/submit",
                              config='invenio.websubmit_config',
                              #breadcrumbs=[(_('Comments'),
                              #              'webcomment.subscribtions')],
                              menubuilder=[('main.websubmit',
                                          _('Submit'),
                                            'websubmit.add', 2)],
                              breadcrumbs=[(_('Submit'), 'submit'),
                                          (_('Add an Article'), 'websubmit.add')])


@blueprint.route('/websubmit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        doctitle = request.form['doctitle']
        author = request.form['author']
        abstract = request.form['abstract']
        pagesnum = request.form['pagesnum']
        language = request.form['language']
        date = request.form['date']
        keywords = request.form['keywords']
        keywords2 = request.form['keywords2']
        notes = request.form['notes']
        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        return render_template('websubmit_submitted.html', \
                                doctitle=doctitle, author=author , abstract=abstract , \
                                pagesnum=pagesnum , language=language , date=date , \
                                keywords=keywords, keywords2=keywords2, notes=notes , validated=True)
    else:
        return render_template('websubmit_submitted.html', validated=False)


@blueprint.route('/websubmit_add/_upload', methods=['GET', 'POST'])
def plupload():
    #r = rediscache.get("request")
    #rediscache.set("request", r + "\n" + str(request.form))
    if request.method == 'POST':
        try:
            chunks = request.form['chunks']
            chunk = request.form['chunk']
        except KeyError:
            chunks = None
            pass
        name = request.form['name']
        uploaded_files_urls = []

        upload_folder = '/opt/invenio/var/tmp/webdeposit_uploads'
        current_chunk = request.files['file']

        try:
            filename = name + "_" + chunk
        except Exception:
            filename = name
        current_chunk.save(os.path.join(upload_folder, filename))

        if chunks is None: #file is a single chunk
            file_path = os.path.join(upload_folder, name)
            from invenio.webuser_flask import current_user
            form = ArticleForm()
            form_type = form.__class__.__name__
            current_draft_id = get_current_draft(current_user.get_id()).draft_id
            draft_field_list_add(current_user.get_id(), \
                                 current_draft_id, \
                                 form_type, \
                                 "files", \
                                 file_path)
        elif int(chunk) == int(chunks) - 1:
            '''All chunks have been uploaded!
                start merging the chunks'''

            chunk_files = []
            for filename in iglob(os.path.join(upload_folder, name + '_*')):
                chunk_files.append(filename)

            #Sort files in numerical order
            chunk_files.sort(key=lambda x: int(x.split("_")[-1]))

            file_path = os.path.join(upload_folder, name)
            destination = open(file_path, 'wb')
            for filename in chunk_files:
                shutil.copyfileobj(open(filename, 'rb'), destination)
            destination.close()

            from invenio.webuser_flask import current_user
            form = ArticleForm()
            form_type = form.__class__.__name__
            current_draft_id = get_current_draft(current_user.get_id()).draft_id
            draft_field_list_add(current_user.get_id(), \
                                 current_draft_id, \
                                 form_type, \
                                 "files", \
                                 file_path)

#               from random import randint
#               filename = filename + str(randint(1, 10000))
        #else:
            #Concatenate the rest chunks to the first file
        #    chunked_file = open(os.path.join(upload_folder, name), 'wb')
         #   shutil.copyfileobj(current_chunk, chunked_file)
          #  chunked_file.close()

#        for key, file in request.files.iteritems():
#           if file:
#               uploaded_file = request.files['file']
#               filename = secure_filename(uploaded_file.filename)
#               
#               from random import randint
#               filename = filename + str(randint(1, 10000))

               #uploaded_files_urls.append(url_for('get_file_url', filename=filename))
    #return uploaded_files_urls[0]
               #uploaded_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
               #send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
               #saved_files_urls.append(url_for('uploaded_file', filename=filename))
    return ""

@blueprint.route('/websubmit_add/uploads/<path:filename>')
def get_file_url(filename):
    return send_from_directory('/opt/invenio/var/tmp/webdeposit_uploads', \
                               filename)#as_attachment=True

@blueprint.route('/websubmit_add/_autocomplete', methods=['GET', 'POST'])
def autocomplete():
    #query = request.args.get('query')
    query = request.args.get('term')
    type = request.args.get('type')

    form = ArticleForm()
    form.__dict__["_fields"][type].process_data(query)

    #Check if field has an autocomplete function
    if hasattr(form.__dict__["_fields"][type], "autocomplete"):
        return json.dumps(form.__dict__["_fields"][type].autocomplete())
    else:
        return []

    #response = SR_Search(query, type)
    #return json.dumps(response)

"""
#@cache.cached(timeout=150, key_prefix='sherpa_romeo')
@cache.memoize(150)
def SR_Search(query, type):
    s = SherpaRomeoSearch()
    if (type == 'journal'):
        response = s.searchTitle(query)
    elif (type == 'publisher'):
        response = s.searchPublisher(query)
    else:
        response = []

    return response
"""

@blueprint.route('/websubmit_add/_ISSN', methods=['GET', 'POST'])
#@cache.cached(timeout=50, key_prefix='issn')
def autocomplete_ISSN_Conditions():
    from invenio.webuser_flask import current_user
    query = request.args.get('title')

    s = SherpaRomeoSearch()

    s.searchTitle(query)
    current_draft_id = get_current_draft(current_user.get_id()).draft_id

    response = dict()
    response['issn'] = s.parser.getISSN()
    response['conditions'] = s.parser.getConditions()

    form = ArticleForm()
    form_type = form.__class__.__name__

    draft_field_set(current_user.get_id(), current_draft_id, form_type, "issn", response['issn'])
    draft_field_set(current_user.get_id(), current_draft_id, form_type, "conditions", response['conditions'])

    return json.dumps(response)


@blueprint.route('/websubmit_add/_errorCheck')
def error_check():
    val = request.args.get('attribute')
    name = request.args.get('name')

    from invenio.webuser_flask import current_user

    form = ArticleForm()
    form_type = form.__class__.__name__

    current_draft_id = get_current_draft(current_user.get_id()).draft_id
    draft_field_set(current_user.get_id(), current_draft_id, form_type, str(name), str(val))



    if name == "issn" or name == "journal" :
        draft_field_set(current_user.get_id(), current_draft_id, form_type, "conditions", None)
    elif name == "date":
        draft_field_set(current_user.get_id(), current_draft_id, form_type, "date", str(val))


    form.__dict__["_fields"][name].process_data(val)

    return jsonify(form.__dict__["_fields"][name].pre_validate())


@blueprint.route('/websubmit_delete/')
@blueprint.route('/websubmit_delete/<int:draft_id>')
def delete(draft_id=None):
    from invenio.webuser_flask import current_user

    if draft_id is None:
        draft_id = get_current_draft(current_user.get_id()).draft_id

    latestDraft = delete_draft(current_user.get_id(), str(draft_id))

    return redirect(url_for("websubmit.add", draft_id=latest_draft))


@blueprint.route('/websubmit_add/')
@blueprint.route('/websubmit_add/<int:draft_id>')
def add(draft_id=None):
    from invenio.webuser_flask import current_user

    form = ArticleForm()
    form_type = form.__class__.__name__

    if current_user.get_id() == 0 or not form._drafting: #if guest user or drafting is not enabled
        return render_template('websubmit_add.html', form=form, drafts=[])

    if draft_id is None: # get the latest draft

        draft_id = get_current_draft(current_user.get_id()).draft_id

        if draft_id is None:
            draft_id = new_draft(current_user.get_id(), form_type)
            return redirect(url_for("websubmit.add", draft_id=draft_id))

        draft = get_draft(current_user.get_id(), draft_id, form_type)

    elif draft_id == 0:
        draft_id = new_draft(current_user.get_id(), form_type)
        return redirect(url_for("websubmit.add", draft_id=draft_id))
        draft = get_draft(current_user.get_id(), str(draft_id))
    else:
        draft = get_draft(current_user.get_id(), draft_id, form_type)
        if draft is None:
            draft_id = new_draft(current_user.get_id())
            return redirect(url_for("websubmit.add", draft_id=draft_id))

    set_current_draft(current_user.get_id(), draft_id)

    for fieldName, fieldData in form.data.iteritems():
        if fieldName in draft:
            form[fieldName].process_data(draft[fieldName])

    conditions = draft_field_get(current_user.get_id(), draft_id, form_type, "conditions")
    drafts = draft_field_get_all(current_user.get_id(), form_type, "title")
    if not isinstance(conditions, str) and conditions is not None :
        conds = []
        for condition in conditions:
            conds.append(escape(condition))
        conditions = conds
        return render_template('websubmit_add.html', \
                               form=form, \
                               conditions=conditions, \
                               drafts=drafts, \
                               draft_id=draft_id)
    elif conditions is not None:
        conditions = [escape(conditions)]
        return render_template('websubmit_add.html', \
                               form=form, \
                               conditions=conditions, \
                               drafts=drafts, \
                               draft_id=draft_id)
    else:
        return render_template('websubmit_add.html', \
                               form=form, \
                               drafts=drafts, \
                               draft_id=draft_id)

