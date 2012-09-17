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

from flask import g, render_template, \
                  request, jsonify, redirect, url_for, current_app
from invenio.cache import cache
from invenio.webinterface_handler_flask_utils import _, InvenioBlueprint
from werkzeug import *
from invenio.SherpaRomeo import SherpaRomeoSearch
import json
from webdeposit_utils import *
from wtforms import Form
from invenio.config import CFG_PYLIBDIR
from invenio.pluginutils import PluginContainer
import os

def plugin_builder(plugin_name, plugin_code):
    all = getattr(plugin_code, '__all__')
    for name in all:
        candidate = getattr(plugin_code, name)
        if issubclass(candidate, Form):
            return candidate

CFG_FORMS = PluginContainer(os.path.join(CFG_PYLIBDIR, 'invenio', 'webdeposit_forms', '*.py'), plugin_builder=plugin_builder)


""" Change the names of the forms
    from the file names to the class names """
forms = []
for form in CFG_FORMS.itervalues():
    if form is not None:
        forms.append((form.__name__, form))

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
    current_draft = get_current_draft(current_user.get_id())

    response = dict()
    response['issn'] = s.parser.getISSN()
    response['conditions'] = s.parser.getConditions()

    draft_field_set(current_user.get_id(), current_draft, "issn", response['issn'])
    draft_field_set(current_user.get_id(), current_draft, "conditions", response['conditions'])

    return json.dumps(response)


@blueprint.route('/websubmit_add/_errorCheck')
def errorCheck():
    val = request.args.get('attribute')
    name = request.args.get('name')

    from invenio.webuser_flask import current_user

    current_draftID = get_current_draft(current_user.get_id())
    draft_field_set(current_user.get_id(), current_draftID, str(name), str(val))


    if name == "issn" or name == "journal" :
        draft_field_set(current_user.get_id(), current_draftID, "conditions", None)
    elif name == "date":
        draft_field_set(current_user.get_id(), current_draftID, "date", str(val))

    form = ArticleForm()
    form.__dict__["_fields"][name].process_data(val)

    return jsonify(form.__dict__["_fields"][name].pre_validate())


@blueprint.route('/websubmit_delete/')
@blueprint.route('/websubmit_delete/<int:draftid>')
def delete(draftid=None):
    from invenio.webuser_flask import current_user

    if draftid is None:
        draftid = get_current_draft(current_user.get_id())

    latestDraft = delete_draft(current_user.get_id(), str(draftid))

    return redirect(url_for("websubmit.add", draftid=latestDraft))


@blueprint.route('/websubmit_add/')
@blueprint.route('/websubmit_add/<int:draftid>')
def add(draftid=None):
    from invenio.webuser_flask import current_user

    form = ArticleForm()
    if current_user.get_id() == 0:
        return render_template('websubmit_add.html', form=form, drafts=[])

    if draftid is None: # get the latest draft        

        draftid = get_current_draft(current_user.get_id())

        if draftid is None:
            draftid = new_draft(current_user.get_id())

        draft = get_draft(current_user.get_id(), draftid)

    elif draftid == 0:
        draftid = new_draft(current_user.get_id())
        return redirect(url_for("websubmit.add", draftid=draftid))
        draft = get_draft(current_user.get_id(), str(draftid))
    else:
        draft = get_draft(current_user.get_id(), draftid)
        if draft is None:
            draftid = new_draft(current_user.get_id())
            return redirect(url_for("websubmit.add", draftid=draftid))

    set_current_draft(current_user.get_id(), draftid)

    for fieldName, fieldData in form.data.iteritems():
        if fieldName in draft:
            form[fieldName].process_data(draft[fieldName])

    conditions = draft_field_get(current_user.get_id(), draftid, "conditions")
    drafts = get_drafts(current_user.get_id())
    if type(conditions) is not str and conditions is not None :
        conds = []
        for condition in conditions:
            conds.append(escape(condition))
        conditions = conds
        return render_template('websubmit_add.html', form=form, conditions=conditions, drafts=drafts, draftid=draftid)
    elif conditions is not None:
        conditions = [escape(conditions)]
        return render_template('websubmit_add.html', form=form, conditions=conditions, drafts=drafts, draftid=draftid)
    else:
        return render_template('websubmit_add.html', form=form, drafts=drafts, draftid=draftid)

