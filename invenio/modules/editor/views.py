# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2015 CERN.
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

"""Record editor interface."""

from __future__ import unicode_literals

import json

from flask import Blueprint, jsonify, render_template, request

from flask_breadcrumbs import register_breadcrumb

from flask_login import login_required

from invenio.base.decorators import wash_arguments
from invenio.base.globals import cfg
from invenio.base.i18n import _
from invenio.config import (CFG_BIBCATALOG_SYSTEM_RT_URL,
                            CFG_BIBEDIT_AUTOCOMPLETE,
                            CFG_BIBEDIT_INTERNAL_DOI_PROTECTION_LEVEL,
                            CFG_BIBEDIT_SHOW_HOLDING_PEN_REMOVED_FIELDS,
                            CFG_CERN_SITE,
                            CFG_INSPIRE_SITE,
                            CFG_SITE_RECORD,
                            CFG_SITE_URL)
from invenio.ext.principal import permission_required
from invenio.legacy.bibcatalog.api import BIBCATALOG_SYSTEM
from invenio.legacy.bibedit.db_layer import (get_info_of_record_revision,
                                             get_name_tags_all)

blueprint = Blueprint('editor', __name__, url_prefix='/record/edit',
                      template_folder='templates', static_folder='static')


@blueprint.route('/', methods=["GET", "POST"])
@register_breadcrumb(blueprint, '.', _('Editor'))
@login_required
@permission_required('runbibedit')
def index():
    """Editor index page."""
    from invenio.legacy.bibedit.utils import get_record_templates
    from invenio.legacy.bibedit.engine import (get_available_kbs,
                                               get_available_fields_templates)

    # Add script data.
    record_templates = get_record_templates()
    record_templates.sort()
    tag_names = get_name_tags_all()
    protected_fields = ['001']
    protected_fields.extend(cfg['CFG_BIBEDIT_PROTECTED_FIELDS'].split(','))
    cern_site = 'false'
    if CFG_CERN_SITE:
        cern_site = 'true'

    data = {
        'gRECORD_TEMPLATES': record_templates,
        'gTAG_NAMES': tag_names,
        'gPROTECTED_FIELDS': protected_fields,
        'gINTERNAL_DOI_PROTECTION_LEVEL':
            CFG_BIBEDIT_INTERNAL_DOI_PROTECTION_LEVEL,
        'gSITE_URL': CFG_SITE_URL,
        'gSITE_RECORD': CFG_SITE_RECORD,
        'gCERN_SITE': cern_site,
        'gINSPIRE_SITE': CFG_INSPIRE_SITE,
        'gHASH_CHECK_INTERVAL': cfg['CFG_BIBEDIT_JS_HASH_CHECK_INTERVAL'],
        'gCHECK_SCROLL_INTERVAL': cfg['CFG_BIBEDIT_JS_CHECK_SCROLL_INTERVAL'],
        'gSTATUS_ERROR_TIME': cfg['CFG_BIBEDIT_JS_STATUS_ERROR_TIME'],
        'gSTATUS_INFO_TIME': cfg['CFG_BIBEDIT_JS_STATUS_INFO_TIME'],
        'gCLONED_RECORD_COLOR':
            '"' + cfg['CFG_BIBEDIT_JS_CLONED_RECORD_COLOR'] + '"',
        'gCLONED_RECORD_COLOR_FADE_DURATION':
            cfg['CFG_BIBEDIT_JS_CLONED_RECORD_COLOR_FADE_DURATION'],
        'gNEW_ADD_FIELD_FORM_COLOR':
            '"' + cfg['CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR'] + '"',
        'gNEW_ADD_FIELD_FORM_COLOR_FADE_DURATION':
            cfg['CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR_FADE_DURATION'],
        'gNEW_CONTENT_COLOR': '"' +
            cfg['CFG_BIBEDIT_JS_NEW_CONTENT_COLOR'] + '"',
        'gNEW_CONTENT_COLOR_FADE_DURATION':
            cfg['CFG_BIBEDIT_JS_NEW_CONTENT_COLOR_FADE_DURATION'],
        'gNEW_CONTENT_HIGHLIGHT_DELAY':
            cfg['CFG_BIBEDIT_JS_NEW_CONTENT_HIGHLIGHT_DELAY'],
        'gTICKET_REFRESH_DELAY': cfg['CFG_BIBEDIT_JS_TICKET_REFRESH_DELAY'],
        'gRESULT_CODES': cfg['CFG_BIBEDIT_AJAX_RESULT_CODES'],
        'gAUTOSUGGEST_TAGS': cfg['CFG_BIBEDIT_AUTOSUGGEST_TAGS'],
        'gAUTOCOMPLETE_TAGS': cfg['CFG_BIBEDIT_AUTOCOMPLETE_TAGS_KBS'].keys(),
        'gKEYWORD_TAG': '"' + cfg['CFG_BIBEDIT_KEYWORD_TAG'] + '"',
        'gREQUESTS_UNTIL_SAVE': cfg['CFG_BIBEDIT_REQUESTS_UNTIL_SAVE'],
        'gAVAILABLE_KBS': get_available_kbs(),
        'gDOILookupField': '"' + cfg['CFG_BIBEDIT_DOI_LOOKUP_FIELD'] + '"',
        'gDisplayReferenceTags': cfg['CFG_BIBEDIT_DISPLAY_REFERENCE_TAGS'],
        'gDisplayAuthorTags': cfg['CFG_BIBEDIT_DISPLAY_AUTHOR_TAGS'],
        'gExcludeCuratorTags': cfg['CFG_BIBEDIT_EXCLUDE_CURATOR_TAGS'],
        'gSHOW_HP_REMOVED_FIELDS': CFG_BIBEDIT_SHOW_HOLDING_PEN_REMOVED_FIELDS,
        'gBIBCATALOG_SYSTEM_RT_URL': repr(CFG_BIBCATALOG_SYSTEM_RT_URL),
        'gAutoComplete': json.dumps(CFG_BIBEDIT_AUTOCOMPLETE)
    }

    fieldTemplates = get_available_fields_templates()

    def convert(data):
        """Return JS friendly strings."""
        if isinstance(data, unicode):
            return str(data)
        else:
            return json.dumps(data)

    for key in data:
        data[key] = convert(data[key])

    try:
        BIBCATALOG_SYSTEM.ticket_search(0)
        can_search_for_ticket = True
    except NotImplementedError:
        can_search_for_ticket = False

    ctx = {
        "data": data,
        "fieldTemplates": json.dumps(fieldTemplates),
        "can_search_for_ticket": can_search_for_ticket
    }

    return render_template('editor/index.html', **ctx)


@blueprint.route('/api', methods=["POST"])
@login_required
@permission_required('runbibedit')
def api():
    """Handle AJAX requests."""
    from invenio.ext.login import current_user
    from invenio.utils.json import json_unicode_to_utf8
    from invenio.legacy.bibedit.utils import user_can_edit_record_collection
    from invenio.legacy.bibedit.engine import perform_request_ajax

    uid = current_user.get_id()
    json_data = json.loads(request.form['jsondata'].encode("utf-8"))
    json_data = json_unicode_to_utf8(json_data)
    json_response = {'resultCode': 0, 'ID': json_data['ID']}

    recid = None
    if 'recID' in json_data:
        recid = int(json_data['recID'])
        json_response.update({'recID': recid})

    if json_data['requestType'] == "getRecord":
        # Authorize access to record.
        if not user_can_edit_record_collection(request, recid):
            json_response.update({'resultCode': 101})
            return json.dumps(json_response)

    # Handle AJAX request.
    json_response.update(perform_request_ajax(request, recid, uid,
                                              json_data))
    return jsonify(json_response)


@blueprint.route('/compare_revisions')
@register_breadcrumb(blueprint, '.compare_revisions', _('Compare revisions'))
@login_required
@wash_arguments({"rev1": (unicode, ''),
                 "rev2": (unicode, ''),
                 "recid": (int, 0)})
@permission_required('runbibedit')
def compare_revisions(rev1, rev2, recid):
    """Compare two revisions of a record."""
    from invenio.legacy.bibedit.engine import (get_marcxml_of_revision_id,
                                               re_revdate_split)
    from invenio.legacy.bibrecord.xmlmarc2textmarc import create_marc_record
    from invenio.legacy.bibrecord import create_record
    from invenio.legacy.bibedit.utils import record_revision_exists
    from invenio.utils.text import show_diff
    person1 = ""
    person2 = ""

    if (not record_revision_exists(recid, rev1)) or \
       (not record_revision_exists(recid, rev2)):
        return render_template("editor/revision_comparison_error.html")
    else:
        xml1 = get_marcxml_of_revision_id(recid, rev1)
        xml2 = get_marcxml_of_revision_id(recid, rev2)
        # Create MARC representations of the records
        marc1 = create_marc_record(
            create_record(xml1)[0], '', {"text-marc": 1, "aleph-marc": 0})
        marc2 = create_marc_record(
            create_record(xml2)[0], '', {"text-marc": 1, "aleph-marc": 0})
        comparison = show_diff(
            marc1,
            marc2,
            prefix="<pre>", suffix="</pre>",
            prefix_removed='<strong class="diff_field_deleted">',
            suffix_removed='</strong>',
            prefix_added='<strong class="diff_field_added">',
            suffix_added='</strong>')
        job_date1 = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(rev1
                                                                  ).groups()
        job_date2 = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(rev2
                                                                  ).groups()
        # Getting the author of each revision
        info1 = get_info_of_record_revision(recid, job_date1)
        info2 = get_info_of_record_revision(recid, job_date2)
        if info1:
            person1 = info1[0][1]
        if info2:
            person2 = info2[0][1]

        ctx = {
            "job_date1": job_date1,
            "job_date2": job_date2,
            "person1": person1,
            "person2": person2,
            "comparison": comparison
        }

        return render_template("editor/revision_comparison.html", **ctx)
