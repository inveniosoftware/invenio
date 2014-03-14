## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2013 CERN.
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

# pylint: disable=C0103
"""Invenio BibEdit Engine."""

__revision__ = "$Id"

from datetime import datetime

import re
import zlib
import copy
import urllib
import urllib2
import cookielib

from invenio import bibformat

from invenio.errorlib import register_exception
from invenio.jsonutils import json, CFG_JSON_AVAILABLE
from invenio.urlutils import auto_version_url
from invenio.xmlmarc2textmarc import create_marc_record
from invenio.bibedit_config import CFG_BIBEDIT_AJAX_RESULT_CODES, \
    CFG_BIBEDIT_JS_CHECK_SCROLL_INTERVAL, CFG_BIBEDIT_JS_HASH_CHECK_INTERVAL, \
    CFG_BIBEDIT_JS_CLONED_RECORD_COLOR, \
    CFG_BIBEDIT_JS_CLONED_RECORD_COLOR_FADE_DURATION, \
    CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR, \
    CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR_FADE_DURATION, \
    CFG_BIBEDIT_JS_NEW_CONTENT_COLOR, \
    CFG_BIBEDIT_JS_NEW_CONTENT_COLOR_FADE_DURATION, \
    CFG_BIBEDIT_JS_NEW_CONTENT_HIGHLIGHT_DELAY, \
    CFG_BIBEDIT_JS_STATUS_ERROR_TIME, CFG_BIBEDIT_JS_STATUS_INFO_TIME, \
    CFG_BIBEDIT_JS_TICKET_REFRESH_DELAY, CFG_BIBEDIT_MAX_SEARCH_RESULTS, \
    CFG_BIBEDIT_TAG_FORMAT, CFG_BIBEDIT_AJAX_RESULT_CODES_REV, \
    CFG_BIBEDIT_AUTOSUGGEST_TAGS, CFG_BIBEDIT_AUTOCOMPLETE_TAGS_KBS,\
    CFG_BIBEDIT_KEYWORD_TAXONOMY, CFG_BIBEDIT_KEYWORD_TAG, \
    CFG_BIBEDIT_KEYWORD_RDFLABEL, CFG_BIBEDIT_REQUESTS_UNTIL_SAVE, \
    CFG_BIBEDIT_DOI_LOOKUP_FIELD, CFG_DOI_USER_AGENT, \
    CFG_BIBEDIT_DISPLAY_REFERENCE_TAGS, CFG_BIBEDIT_DISPLAY_AUTHOR_TAGS, \
    CFG_BIBEDIT_EXCLUDE_CURATOR_TAGS, CFG_BIBEDIT_AUTHOR_DISPLAY_THRESHOLD

from invenio.config import (CFG_SITE_LANG,
    CFG_BIBCATALOG_SYSTEM_RT_URL, CFG_BIBEDIT_SHOW_HOLDING_PEN_REMOVED_FIELDS,
    CFG_BIBCATALOG_SYSTEM, CFG_BIBEDIT_AUTOCOMPLETE)

from invenio.bibedit_dblayer import get_name_tags_all, reserve_record_id, \
    get_related_hp_changesets, get_hp_update_xml, delete_hp_change, \
    get_record_last_modification_date, get_record_revision_author, \
    get_marcxml_of_record_revision, delete_related_holdingpen_changes, \
    get_record_revisions, get_info_of_record_revision, \
    deactivate_cache

from invenio.bibedit_utils import cache_exists, cache_expired, \
    create_cache, delete_cache, get_bibrecord, \
    get_cache_contents, get_cache_mtime, get_record_templates, \
    get_record_template, latest_record_revision, record_locked_by_other_user, \
    record_locked_by_queue, save_xml_record, touch_cache, \
    update_cache_contents, get_field_templates, get_marcxml_of_revision, \
    revision_to_timestamp, timestamp_to_revision, \
    get_record_revision_timestamps, get_record_revision_authors, record_revision_exists, \
    can_record_have_physical_copies, extend_record_with_template, \
    replace_references, merge_record_with_template, record_xml_output, \
    record_is_conference, add_record_cnum, get_xml_from_textmarc, \
    record_locked_by_user_details, crossref_process_template, \
    modify_record_timestamp, get_affiliation_for_paper, InvalidCache, \
    get_new_ticket_RT_info

from invenio.bibrecord import create_record, print_rec, record_add_field, \
    record_add_subfield_into, record_delete_field, \
    record_delete_subfield_from, \
    record_modify_subfield, record_move_subfield, \
    create_field, record_replace_field, record_move_fields, \
    record_modify_controlfield, record_get_field_values, \
    record_get_subfields, record_get_field_instances, record_add_fields, \
    record_strip_empty_fields, record_strip_empty_volatile_subfields, \
    record_strip_controlfields, record_order_subfields, \
    field_add_subfield, field_get_subfield_values, field_xml_output, \
    record_extract_dois

from invenio.config import CFG_BIBEDIT_PROTECTED_FIELDS, CFG_CERN_SITE, \
    CFG_SITE_URL, CFG_SITE_RECORD, CFG_BIBEDIT_KB_SUBJECTS, \
    CFG_INSPIRE_SITE, CFG_BIBUPLOAD_INTERNAL_DOI_PATTERN, \
    CFG_BIBEDIT_INTERNAL_DOI_PROTECTION_LEVEL
from invenio.search_engine import record_exists, perform_request_search, \
    guess_primary_collection_of_a_record
from invenio.webuser import session_param_get, session_param_set
from invenio.bibcatalog import BIBCATALOG_SYSTEM
from invenio.bibcatalog_system import get_bibcat_from_prefs
from invenio.webpage import page
from invenio.htmlutils import get_mathjax_header
from invenio.textutils import wash_for_xml, show_diff
from invenio.bibknowledge import get_kbd_values_for_bibedit, get_kbr_values, \
     get_kbt_items_for_bibedit, kb_exists

from invenio.batchuploader_engine import perform_upload_check

from invenio.bibcirculation_dblayer import get_number_copies, has_copies
from invenio.bibcirculation_utils import create_item_details_url

from invenio.refextract_api import FullTextNotAvailable, \
                                   get_pdf_doc, \
                                   record_has_fulltext

from invenio import xmlmarc2textmarc as xmlmarc2textmarc
from invenio.crossrefutils import get_marcxml_for_doi, CrossrefError

import invenio.template
bibedit_templates = invenio.template.load('bibedit')

try:
    BIBCATALOG_SYSTEM.ticket_search(0)
    CFG_CAN_SEARCH_FOR_TICKET = True
except NotImplementedError:
    CFG_CAN_SEARCH_FOR_TICKET = False

re_revdate_split = re.compile(r'^(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)')


def bibedit_register_exception(data):
    register_exception(alert_admin=True,
                       prefix="\n".join(data['action_log']))


def get_empty_fields_templates():
    """
    Returning the templates of empty fields::
     -an empty data field
     -an empty control field
    """
    return [{
                "name": "Empty field",
                "description": "The data field not containing any " +
                               "information filled in",
                "tag" : "",
                "ind1" : "",
                "ind2" : "",
                "subfields" : [("", "")],
                "isControlfield" : False
            }, {
                "name" : "Empty control field",
                "description" : "The controlfield not containing any " +
                                "data or tag description",
                "isControlfield" : True,
                "tag" : "",
                "value" : ""
            }]

def get_available_fields_templates():
    """
    A method returning all the available field templates
    Returns a list of descriptors. Each descriptor has
    the same structure as a full field descriptor inside the
    record
    """
    templates = get_field_templates()
    result = get_empty_fields_templates()
    for template in templates:
        tplTag = template[3].keys()[0]
        field = template[3][tplTag][0]

        if (field[0] == []):
        # if the field is a controlField, add different structure
            result.append({
                    "name" : template[1],
                    "description" : template[2],
                    "isControlfield" : True,
                    "tag" : tplTag,
                    "value" : field[3]
                })
        else:
            result.append({
                    "name": template[1],
                    "description": template[2],
                    "tag" : tplTag,
                    "ind1" : field[1],
                    "ind2" : field[2],
                    "subfields" : field[0],
                    "isControlfield" : False
                    })
    return result

def perform_request_init(uid, ln, req, lastupdated):
    """Handle the initial request by adding menu and JavaScript to the page."""
    errors   = []
    warnings = []
    body = ''

    # Add script data.
    record_templates = get_record_templates()
    record_templates.sort()
    tag_names = get_name_tags_all()
    protected_fields = ['001']
    protected_fields.extend(CFG_BIBEDIT_PROTECTED_FIELDS.split(','))
    cern_site = 'false'

    if not CFG_JSON_AVAILABLE:
        title = 'Record Editor'
        body = '''Sorry, the record editor cannot operate when the
                `simplejson' module is not installed.  Please see the INSTALL
                file.'''
        return page(title       = title,
                    body        = body,
                    errors      = [],
                    warnings    = [],
                    uid         = uid,
                    language    = ln,
                    navtrail    = "",
                    lastupdated = lastupdated,
                    req         = req)


    body += '<link rel="stylesheet" type="text/css" href="/img/jquery-ui.css" />'
    body += '<link rel="stylesheet" type="text/css" href="%s/%s" />' % (CFG_SITE_URL,
            auto_version_url("img/" + 'bibedit.css'))

    if CFG_CERN_SITE:
        cern_site = 'true'
    data = {'gRECORD_TEMPLATES': record_templates,
            'gTAG_NAMES': tag_names,
            'gPROTECTED_FIELDS': protected_fields,
            'gINTERNAL_DOI_PROTECTION_LEVEL': CFG_BIBEDIT_INTERNAL_DOI_PROTECTION_LEVEL,
            'gSITE_URL': '"' + CFG_SITE_URL + '"',
            'gSITE_RECORD': '"' + CFG_SITE_RECORD + '"',
            'gCERN_SITE': cern_site,
            'gINSPIRE_SITE': CFG_INSPIRE_SITE,
            'gHASH_CHECK_INTERVAL': CFG_BIBEDIT_JS_HASH_CHECK_INTERVAL,
            'gCHECK_SCROLL_INTERVAL': CFG_BIBEDIT_JS_CHECK_SCROLL_INTERVAL,
            'gSTATUS_ERROR_TIME': CFG_BIBEDIT_JS_STATUS_ERROR_TIME,
            'gSTATUS_INFO_TIME': CFG_BIBEDIT_JS_STATUS_INFO_TIME,
            'gCLONED_RECORD_COLOR':
                '"' + CFG_BIBEDIT_JS_CLONED_RECORD_COLOR + '"',
            'gCLONED_RECORD_COLOR_FADE_DURATION':
                CFG_BIBEDIT_JS_CLONED_RECORD_COLOR_FADE_DURATION,
            'gNEW_ADD_FIELD_FORM_COLOR':
                '"' + CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR + '"',
            'gNEW_ADD_FIELD_FORM_COLOR_FADE_DURATION':
                CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR_FADE_DURATION,
            'gNEW_CONTENT_COLOR': '"' + CFG_BIBEDIT_JS_NEW_CONTENT_COLOR + '"',
            'gNEW_CONTENT_COLOR_FADE_DURATION':
                CFG_BIBEDIT_JS_NEW_CONTENT_COLOR_FADE_DURATION,
            'gNEW_CONTENT_HIGHLIGHT_DELAY':
                CFG_BIBEDIT_JS_NEW_CONTENT_HIGHLIGHT_DELAY,
            'gTICKET_REFRESH_DELAY': CFG_BIBEDIT_JS_TICKET_REFRESH_DELAY,
            'gRESULT_CODES': CFG_BIBEDIT_AJAX_RESULT_CODES,
            'gAUTOSUGGEST_TAGS' : CFG_BIBEDIT_AUTOSUGGEST_TAGS,
            'gAUTOCOMPLETE_TAGS' : CFG_BIBEDIT_AUTOCOMPLETE_TAGS_KBS.keys(),
            'gKEYWORD_TAG' : '"' + CFG_BIBEDIT_KEYWORD_TAG  + '"',
            'gREQUESTS_UNTIL_SAVE' : CFG_BIBEDIT_REQUESTS_UNTIL_SAVE,
            'gAVAILABLE_KBS': get_available_kbs(),
            'gDOILookupField': '"' + CFG_BIBEDIT_DOI_LOOKUP_FIELD + '"',
            'gDisplayReferenceTags': CFG_BIBEDIT_DISPLAY_REFERENCE_TAGS,
            'gDisplayAuthorTags': CFG_BIBEDIT_DISPLAY_AUTHOR_TAGS,
            'gExcludeCuratorTags': CFG_BIBEDIT_EXCLUDE_CURATOR_TAGS,
            'gSHOW_HP_REMOVED_FIELDS': CFG_BIBEDIT_SHOW_HOLDING_PEN_REMOVED_FIELDS,
            'gBIBCATALOG_SYSTEM_RT_URL': repr(CFG_BIBCATALOG_SYSTEM_RT_URL),
            'gAutoComplete': json.dumps(CFG_BIBEDIT_AUTOCOMPLETE)
            }
    body += '<script type="text/javascript">\n'
    for key in data:
        body += '    var %s = %s;\n' % (key, data[key])
    body += '    </script>\n'

    # Adding the information about field templates
    fieldTemplates = get_available_fields_templates()
    body += "<script>\n" + \
            "   var fieldTemplates = %s\n" % (json.dumps(fieldTemplates), ) + \
            "</script>\n"
    # Add scripts (the ordering is NOT irrelevant).
    scripts = ['jquery-ui.min.js',  'jquery.jeditable.mini.js', 'jquery.hotkeys.js',
               'json2.js', 'bibedit_refextract.js', 'bibedit_display.js', 'bibedit_engine.js', 'bibedit_keys.js',
               'bibedit_menu.js', 'bibedit_holdingpen.js', 'marcxml.js',
               'bibedit_clipboard.js']

    for script in scripts:
        body += '    <script type="text/javascript" src="%s/%s">' \
            '</script>\n' % (CFG_SITE_URL, auto_version_url("js/" + script))

    # Init BibEdit
    body += '<script>$(init_bibedit);</script>'

    # Build page structure and menu.
    # rec = create_record(format_record(235, "xm"))[0]
    #oaiId = record_extract_oai_id(rec)

    body += bibedit_templates.menu()
    body += bibedit_templates.focuson()
    body += """<div id="bibEditContent">
               <div class="revisionLine"></div>
               <div id="Toptoolbar"></div>
               <div id="bibEditMessage"></div>
               <div id="bibEditContentTable"></div>
               </div>"""

    return body, errors, warnings


def get_available_kbs():
    """
    Return list of KBs that are available in the system to be used with
    BibEdit
    """
    kb_list = [CFG_BIBEDIT_KB_SUBJECTS]
    available_kbs = [kb for kb in kb_list if kb_exists(kb)]
    return available_kbs


def get_marcxml_of_revision_id(recid, revid):
    """
    Return MARCXML string with corresponding to revision REVID
    (=RECID.REVDATE) of a record.  Return empty string if revision
    does not exist.
    """
    job_date = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(revid).groups()
    tmp_res = get_marcxml_of_record_revision(recid, job_date)
    if tmp_res:
        for row in tmp_res:
            xml = zlib.decompress(row[0]) + "\n"
            # xml contains marcxml of record
            # now we create a record object from this xml and sort fields and subfields
            # and return marcxml
            rec = create_record(xml)[0]
            record_order_subfields(rec)
            marcxml = record_xml_output(rec, order_fn="_order_by_tags")
    return marcxml


def perform_request_compare(ln, recid, rev1, rev2):
    """Handle a request for comparing two records"""

    body = ""
    errors = []
    warnings = []
    person1 = ""
    person2 = ""

    if (not record_revision_exists(recid, rev1)) or \
       (not record_revision_exists(recid, rev2)):
        body = "The requested record revision does not exist !"
    else:
        xml1 = get_marcxml_of_revision_id(recid, rev1)
        xml2 = get_marcxml_of_revision_id(recid, rev2)
        # Create MARC representations of the records
        marc1 = create_marc_record(create_record(xml1)[0], '', {"text-marc": 1, "aleph-marc": 0})
        marc2 = create_marc_record(create_record(xml2)[0], '', {"text-marc": 1, "aleph-marc": 0})
        comparison = show_diff(marc1,
                               marc2,
                               prefix="<pre>", suffix="</pre>",
                               prefix_removed='<strong class="diff_field_deleted">',
                               suffix_removed='</strong>',
                               prefix_added='<strong class="diff_field_added">',
                               suffix_added='</strong>')
        job_date1 = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(rev1).groups()
        job_date2 = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(rev2).groups()
        # Geting the author of each revision
        info1 = get_info_of_record_revision(recid, job_date1)
        info2 = get_info_of_record_revision(recid, job_date2)
        if info1:
            person1 = info1[0][1]
        if info2:
            person2 = info2[0][1]
        body += bibedit_templates.history_comparebox(ln, job_date1, job_date2,
                                                person1, person2, comparison)
    return body, errors, warnings

def perform_request_newticket(recid, uid):
    """create a new ticket with this record's number
    @param recid: record id
    @param uid: user id
    @return: (error_msg, url)

    """
    t_url = ""
    errmsg = ""
    if CFG_BIBCATALOG_SYSTEM is not None:
        t_id = BIBCATALOG_SYSTEM.ticket_submit(uid, "", recid, "")
        if t_id:
            #get the ticket's URL
            t_url = BIBCATALOG_SYSTEM.ticket_get_attribute(uid, t_id, 'url_modify')
        else:
            errmsg = "ticket_submit failed"
    else:
        errmsg = "No ticket system configured"
    return (errmsg, t_url)


def perform_request_ajax(req, recid, uid, data, isBulk=False):
    try:
        return _perform_request_ajax(req, recid, uid, data, isBulk)
    except:   # pylint: disable=W0702
        # Custom error exception for bibedit
        # We have an action log that we want to display in full
        bibedit_register_exception(data)
        return {'resultCode': CFG_BIBEDIT_AJAX_RESULT_CODES_REV['server_error']}


def _perform_request_ajax(req, recid, uid, data, isBulk=False):
    """Handle Ajax requests by redirecting to appropriate function."""
    response = {}
    request_type = data['requestType']
    undo_redo = None
    if "undoRedo" in data:
        undo_redo = data["undoRedo"]
    # Call function based on request type.
    if request_type == 'searchForRecord':
        # Search request.
        response.update(perform_request_bibedit_search(data, req))
    elif request_type in ['changeTagFormat']:
        # User related requests.
        response.update(perform_request_user(req, request_type, recid, data))
    elif request_type in ('getRecord', 'submit', 'cancel', 'newRecord',
        'deleteRecord', 'deleteRecordCache', 'prepareRecordMerge', 'revert',
        'updateCacheRef', 'submittextmarc'):
        # 'Major' record related requests.
        response.update(perform_request_record(req, request_type, recid, uid,
                                               data))
    elif request_type in ('addField', 'addSubfields',
                          'addFieldsSubfieldsOnPositions', 'modifyContent',
                          'modifySubfieldTag', 'modifyFieldTag',
                          'moveSubfield', 'deleteFields', 'moveField',
                          'modifyField', 'otherUpdateRequest',
                          'disableHpChange', 'deactivateHoldingPenChangeset'):
        # Record updates.
        cacheMTime = data['cacheMTime']
        if 'hpChanges' in data:
            hpChanges = data['hpChanges']
        else:
            hpChanges = {}

        response.update(perform_request_update_record(request_type, recid,
                                                      uid, cacheMTime, data,
                                                      hpChanges, undo_redo,
                                                      isBulk))
    elif request_type in ('autosuggest', 'autocomplete', 'autokeyword'):
        response.update(perform_request_autocomplete(request_type, recid, uid,
                                                     data))

    elif request_type in ('getTickets', 'closeTicket', 'openTicket', 'createTicket','getNewTicketRTInfo'):
        # BibCatalog requests.
        response.update(perform_request_bibcatalog(request_type, uid, data))
    elif request_type in ('getHoldingPenUpdates', ):
        response.update(perform_request_holdingpen(request_type, recid))

    elif request_type in ('getHoldingPenUpdateDetails',
                          'deleteHoldingPenChangeset'):
        updateId = data['changesetNumber']
        response.update(perform_request_holdingpen(request_type, recid,
                                                   updateId))
    elif request_type in ('applyBulkUpdates', ):
        # a general version of a bulk request
        changes = data['requestsData']
        cacheMTime = data['cacheMTime']
        response.update(perform_bulk_request_ajax(req, recid, uid, changes,
                                                  undo_redo, cacheMTime))
    elif request_type in ('preview', ):
        response.update(perform_request_preview_record(request_type, recid, uid, data))
    elif request_type in ('get_pdf_url', ):
        response.update(perform_request_get_pdf_url(recid))
    elif request_type in ('refextract', ):
        txt = None
        if 'txt' in data:
            txt = data["txt"]
        response.update(perform_request_ref_extract(recid, uid, txt))
    elif request_type in ('refextracturl', ):
        response.update(perform_request_ref_extract_url(recid, uid, data['url']))
    elif request_type == 'getTextMarc':
        response.update(perform_request_get_textmarc(recid, uid))
    elif request_type == "getTableView":
        response.update(perform_request_get_tableview(recid, uid, data))
    elif request_type == "DOISearch":
        response.update(perform_doi_search(data['doi']))
    elif request_type == "deactivateRecordCache":
        deactivate_cache(recid, uid)
        response.update({"cacheMTime": data['cacheMTime']})
    elif request_type == "guessAffiliations":
        response.update(perform_guess_affiliations(uid, data))

    return response

def perform_bulk_request_ajax(req, recid, uid, reqsData, undoRedo, cacheMTime):
    """ An AJAX handler used when treating bulk updates """
    lastResult = {}
    lastTime = cacheMTime
    if get_cache_mtime(recid, uid) != cacheMTime:
        return {"resultCode": 107}
    isFirst = True
    for data in reqsData:
        assert data is not None
        data['cacheMTime'] = lastTime
        if isFirst and undoRedo is not None:
            # we add the undo/redo handler to the first operation in order to
            # save the handler on the server side !
            data['undoRedo'] = undoRedo
            isFirst = False
        lastResult = _perform_request_ajax(req, recid, uid, data, isBulk=True)
        lastTime = lastResult['cacheMTime']
    return lastResult


def perform_request_bibedit_search(data, req):
    """Handle search requests."""
    response = {}
    searchType = data['searchType']
    if searchType is None:
        searchType = "anywhere"
    searchPattern = data['searchPattern']
    if searchType == 'anywhere':
        pattern = searchPattern
    else:
        pattern = searchType + ':' + searchPattern

    pattern = urllib.unquote(pattern)
    result_set = list(perform_request_search(req=req, p=pattern))
    response['resultCode'] = 1
    response['resultSet'] = result_set[0:CFG_BIBEDIT_MAX_SEARCH_RESULTS]
    return response


def perform_request_user(req, request_type, recid, data):
    """Handle user related requests."""
    response = {}
    if request_type == 'changeTagFormat':
        tagformat_settings = session_param_get(req, 'bibedit_tagformat', {})
        tagformat_settings[recid] = data['tagFormat']
        session_param_set(req, 'bibedit_tagformat', tagformat_settings)
        response['resultCode'] = 2
    return response


def perform_request_holdingpen(request_type, recId, changeId=None):
    """
    A method performing the holdingPen ajax request. The following types of
    requests can be made::
     -getHoldingPenUpdates: retrieving the holding pen updates pending
                            for a given record
    """
    response = {}
    if request_type == 'getHoldingPenUpdates':
        changeSet = get_related_hp_changesets(recId)
        changes = []
        for change in changeSet:
            changes.append((str(change[0]), str(change[1])))
        changes.reverse()  # newest to older order
        response["changes"] = changes
    elif request_type == 'getHoldingPenUpdateDetails':
        # returning the list of changes related to the holding pen update
        # the format based on what the record difference xtool returns
        assert(changeId is not None)
        hpContent = get_hp_update_xml(changeId)
        holdingPenRecord = create_record(hpContent[0], "xm")[0]
        if not holdingPenRecord:
            response['resultCode'] = 107
        else:
            template_to_merge = extend_record_with_template(recId)
            if template_to_merge:
                merged_record = merge_record_with_template(holdingPenRecord,
                                                           template_to_merge,
                                                           is_hp_record=True)
                if merged_record:
                    holdingPenRecord = merged_record


            # order subfields alphabetically
            record_order_subfields(holdingPenRecord)
    #        databaseRecord = get_record(hpContent[1])
            response['record'] = holdingPenRecord
            response['changeset_number'] = changeId

    elif request_type == 'deleteHoldingPenChangeset':
        assert(changeId is not None)
        delete_hp_change(changeId)
    return response


def perform_request_record(req, request_type, recid, uid, data, ln=CFG_SITE_LANG):
    """Handle 'major' record related requests like fetching, submitting or
    deleting a record, cancel editing or preparing a record for merging.

    """
    response = {}

    if request_type == 'newRecord':
        # Create a new record.
        new_recid = reserve_record_id()
        new_type = data['newType']
        if new_type == 'empty':
            # Create a new empty record.
            create_cache(recid, uid)
            response['resultCode'], response['newRecID'] = 6, new_recid

        elif new_type == 'template':
            # Create a new record from XML record template.
            template_filename = data['templateFilename']
            template = get_record_template(template_filename)
            if not template:
                response['resultCode'] = 108
            else:
                record = create_record(template)[0]
                if not record:
                    response['resultCode'] = 109
                else:
                    record_add_field(record, '001',
                                     controlfield_value=str(new_recid))
                    create_cache(new_recid, uid, record, True)
                    response['cacheMTime'] = get_cache_mtime(new_recid, uid)
                    response['resultCode'], response['newRecID'] = 7, new_recid

        elif new_type == 'import':
            # Import data from external source, using DOI
            doi = data['doi']
            if not doi:
                response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_no_doi_specified']
            else:
                try:
                    marcxml_template = get_marcxml_for_doi(doi)
                except CrossrefError, inst:
                    response['resultCode'] = \
                        CFG_BIBEDIT_AJAX_RESULT_CODES_REV[inst.code]
                else:
                    record = crossref_process_template(marcxml_template, CFG_INSPIRE_SITE)
                    if not record:
                        response['resultCode'] = 109
                    else:
                        record_add_field(record, '001',
                                         controlfield_value=str(new_recid))
                        template_to_merge = extend_record_with_template(recstruct=record)
                        if template_to_merge:
                            merged_record = merge_record_with_template(record, template_to_merge)
                            if merged_record:
                                record = merged_record

                        create_cache(new_recid, uid, record, True)
                        response['cacheMTime'] = get_cache_mtime(new_recid, uid)
                        response['resultCode'], response['newRecID'] = 7, new_recid
        elif new_type == 'clone':
            # Clone an existing record (from the users cache).
            existing_cache = cache_exists(recid, uid)
            if existing_cache:
                try:
                    cache = get_cache_contents(recid, uid)
                    record = cache[2]
                except InvalidCache:
                    # if, for example, the cache format was wrong (outdated)
                    record = get_bibrecord(recid)
            else:
                # Cache missing. Fall back to using original version.
                record = get_bibrecord(recid)
            record_delete_field(record, '001')
            record_delete_field(record, '005')
            record_add_field(record, '001', controlfield_value=str(new_recid))
            create_cache(new_recid, uid, record, True)
            response['resultCode'], response['newRecID'] = 8, new_recid
    elif request_type == 'getRecord':
        # Fetch the record. Possible error situations:
        # - Non-existing record
        # - Deleted record
        # - Record locked by other user
        # - Record locked by queue
        # A cache file will be created if it does not exist.
        # If the cache is outdated (i.e., not based on the latest DB revision),
        # cacheOutdated will be set to True in the response.
        record_status = record_exists(recid)
        existing_cache = cache_exists(recid, uid)
        read_only_mode = False

        if "inReadOnlyMode" in data:
            read_only_mode = data['inReadOnlyMode']

        if data.get('deleteRecordCache'):
            delete_cache(recid, uid)
            existing_cache = False
            pending_changes = []
            disabled_hp_changes = {}

        if record_status == 0:
            response['resultCode'] = 102
        elif not read_only_mode and not existing_cache and \
                record_locked_by_other_user(recid, uid):
            name, email, locked_since = record_locked_by_user_details(recid, uid)
            response['locked_details'] = {'name': name,
                                          'email': email,
                                          'locked_since': locked_since}
            response['resultCode'] = 104
        elif not read_only_mode and existing_cache and \
                cache_expired(recid, uid) and \
                record_locked_by_other_user(recid, uid):
            response['resultCode'] = 104
        elif not read_only_mode and record_locked_by_queue(recid):
            response['resultCode'] = 105
        else:
            if read_only_mode:
                if 'recordRevision' in data and data['recordRevision'] != 'sampleValue':
                    record_revision_ts = data['recordRevision']
                    record_xml = get_marcxml_of_revision(recid,
                                                         record_revision_ts)
                    record = create_record(record_xml)[0]
                    record_revision = timestamp_to_revision(record_revision_ts)
                    pending_changes = []
                    disabled_hp_changes = {}
                else:
                    # a normal cacheless retrieval of a record
                    record = get_bibrecord(recid)
                    record_revision = get_record_last_modification_date(recid)
                    if record_revision is None:
                        record_revision = datetime.now().timetuple()
                    pending_changes = []
                    disabled_hp_changes = {}
                cache_dirty = False
                mtime = 0
                undo_list = []
                redo_list = []
            else:
                try:
                    cache_dirty, record_revision, record, pending_changes, \
                        disabled_hp_changes, undo_list, redo_list = \
                        get_cache_contents(recid, uid)
                except InvalidCache:
                    # No cache found in the DB
                    record_revision, record = create_cache(recid, uid)
                    if not record:
                        response['resultCode'] = 103
                        return response
                    pending_changes = []
                    disabled_hp_changes = {}
                    cache_dirty = False
                    undo_list = []
                    redo_list = []
                else:
                    touch_cache(recid, uid)
                    if not latest_record_revision(recid, record_revision) and \
                            get_record_revisions(recid) != ():
                        # This sould prevent from using old cache in case of
                        # viewing old version. If there are no revisions,
                        # it means we should skip this step because this
                        # is a new record
                        response['cacheOutdated'] = True

                mtime = get_cache_mtime(recid, uid)

            if data.get('clonedRecord', ''):
                response['resultCode'] = 9
            else:
                response['resultCode'] = 3
            revision_author = get_record_revision_author(recid, record_revision)
            latest_revision = get_record_last_modification_date(recid)
            if latest_revision is None:
                latest_revision = datetime.now().timetuple()
            last_revision_ts = revision_to_timestamp(latest_revision)

            revisions_history = get_record_revision_timestamps(recid)
            revisions_authors = get_record_revision_authors(recid)
            number_of_physical_copies = get_number_copies(recid)
            bibcirc_details_URL = create_item_details_url(recid, ln)
            can_have_copies = can_record_have_physical_copies(recid)
            managed_DOIs = [doi for doi in record_extract_dois(record) if \
                            re.compile(CFG_BIBUPLOAD_INTERNAL_DOI_PATTERN).match(doi)]

            # For some collections, merge template with record
            template_to_merge = extend_record_with_template(recid)
            if template_to_merge and not read_only_mode:
                merged_record = merge_record_with_template(record, template_to_merge)
                if merged_record:
                    record = merged_record
                    mtime = update_cache_contents(recid, uid, record_revision,
                                                  record, pending_changes,
                                                  disabled_hp_changes,
                                                  undo_list, redo_list)

            if record_status == -1:
                # The record was deleted
                response['resultCode'] = 103

            response['record_has_pdf'] = record_has_fulltext(recid)

            response['record_hide_authors'] = check_hide_authors(record)

            response['cacheDirty'], response['record'], \
                response['cacheMTime'], response['recordRevision'], \
                response['revisionAuthor'], response['lastRevision'], \
                response['revisionsHistory'], response['revisionsAuthors'], \
                response['inReadOnlyMode'], response['pendingHpChanges'], \
                response['disabledHpChanges'], response['undoList'], \
                response['redoList'] = cache_dirty, \
                record, mtime, revision_to_timestamp(record_revision), \
                revision_author, last_revision_ts, revisions_history, \
                revisions_authors, read_only_mode, pending_changes, \
                disabled_hp_changes, undo_list, redo_list
            response['numberOfCopies'] = number_of_physical_copies
            response['managed_DOIs'] = managed_DOIs
            response['bibCirculationUrl'] = bibcirc_details_URL
            response['canRecordHavePhysicalCopies'] = can_have_copies
            # Set tag format from user's session settings.
            tagformat_settings = session_param_get(req, 'bibedit_tagformat')
            tagformat = (tagformat_settings is not None) and tagformat_settings.get(recid, CFG_BIBEDIT_TAG_FORMAT) or CFG_BIBEDIT_TAG_FORMAT
            response['tagFormat'] = tagformat
            # KB information
            response['KBSubject'] = CFG_BIBEDIT_KB_SUBJECTS
            # Autocomplete information
            response['primaryCollection'] = guess_primary_collection_of_a_record(recid)

    elif request_type == 'submit':
        # Submit the record. Possible error situations:
        # - Missing cache file
        # - Cache file modified in other editor
        # - Record locked by other user
        # - Record locked by queue
        # If the cache is outdated cacheOutdated will be set to True in the
        # response.
        perform_request_submit(recid=recid,
                               uid=uid,
                               data=data,
                               response=response)
    elif request_type == 'revert':
        revId = data['revId']
        job_date = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(revId).groups()
        revision_xml = get_marcxml_of_revision(recid, job_date)
        # Modify the 005 tag in order to merge with the latest version of record
        last_revision_ts = data['lastRevId'] + ".0"
        revision_xml = modify_record_timestamp(revision_xml, last_revision_ts)
        save_xml_record(recid, uid, revision_xml)
        if (cache_exists(recid, uid)):
            delete_cache(recid, uid)
        response['resultCode'] = 4

    elif request_type == 'cancel':
        # Cancel editing by deleting the cache file. Possible error situations:
        # - Cache file modified in other editor
        if cache_exists(recid, uid):
            if get_cache_mtime(recid, uid) == data['cacheMTime']:
                delete_cache(recid, uid)
                response['resultCode'] = 5
            else:
                response['resultCode'] = 107
        else:
            response['resultCode'] = 5

    elif request_type == 'deleteRecord':
        # Submit the record. Possible error situations:
        # - Record locked by other user
        # - Record locked by queue
        # As the user is requesting deletion we proceed even if the cache file
        # is missing and we don't check if the cache is outdated or has
        # been modified in another editor.
        existing_cache = cache_exists(recid, uid)
        pending_changes = []

        if has_copies(recid):
            response['resultCode'] = \
                CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_physical_copies_exist']
        elif existing_cache and cache_expired(recid, uid) and \
                record_locked_by_other_user(recid, uid):
            response['resultCode'] = \
                CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_rec_locked_by_user']
        elif record_locked_by_queue(recid):
            response['resultCode'] = \
                CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_rec_locked_by_queue']
        else:
            if not existing_cache:
                create_cache(recid, uid)
                record_revision, record, pending_changes, \
                    deactivated_hp_changes, undo_list, redo_list = \
                        get_cache_contents(recid, uid)[1:]
            else:
                try:
                    dummy_cache_dirty, record_revision, record, \
                        pending_changes, deactivated_hp_changes, undo_list, \
                        redo_list = get_cache_contents(recid, uid)
                except InvalidCache:
                    record_revision, record, pending_changes, \
                        deactivated_hp_changes = create_cache(recid, uid)
            record_add_field(record, '980', ' ', ' ', '', [('c', 'DELETED')])
            undo_list = []
            redo_list = []
            update_cache_contents(recid, uid, record_revision, record,
                                  pending_changes, deactivated_hp_changes,
                                  undo_list, redo_list)
            save_xml_record(recid, uid)
            delete_related_holdingpen_changes(recid) # we don't need any changes
                                                   # related to a deleted record
            response['resultCode'] = 10

    elif request_type == 'deleteRecordCache':
        # Delete the cache file. Ignore the request if the cache has been
        # modified in another editor.
        if 'cacheMTime' in data:
            if cache_exists(recid, uid) and get_cache_mtime(recid, uid) == \
                                                            data['cacheMTime']:
                delete_cache(recid, uid)
        response['resultCode'] = 11
    elif request_type == 'updateCacheRef':
        # Update cache with the contents coming from BibEdit JS interface
        # Used when updating references using ref extractor
        record_revision, record, pending_changes, \
                        deactivated_hp_changes, undo_list, redo_list = \
                        get_cache_contents(recid, uid)[1:]

        record = create_record(data['recXML'])[0]

        response['cacheMTime'] = update_cache_contents(recid,
                                                       uid,
                                                       record_revision,
                                                       record,
                                                       pending_changes,
                                                       deactivated_hp_changes,
                                                       undo_list,
                                                       redo_list)
        response['cacheDirty'] = True
        response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['cache_updated_with_references']

    elif request_type == 'prepareRecordMerge':
        # We want to merge the cache with the current DB version of the record,
        # so prepare an XML file from the file cache, to be used by BibMerge.
        # Possible error situations:
        # - Missing cache file
        # - Record locked by other user
        # - Record locked by queue
        # We don't check if cache is outdated (a likely scenario for this
        # request) or if it has been modified in another editor.
        if not cache_exists(recid, uid):
            response['resultCode'] = 106
        elif cache_expired(recid, uid) and \
                record_locked_by_other_user(recid, uid):
            response['resultCode'] = 104
        elif record_locked_by_queue(recid):
            response['resultCode'] = 105
        else:
            save_xml_record(recid, uid, to_upload=False, to_merge=True)
            response['resultCode'] = 12

    elif request_type == 'submittextmarc':
        # Textmarc content coming from the user
        textmarc_record = data['textmarc']
        xml_conversion_status = get_xml_from_textmarc(recid, textmarc_record, uid)

        if xml_conversion_status['resultMsg'] == "textmarc_parsing_error":
            response.update(xml_conversion_status)
            return response

        # Simulate upload to catch errors
        errors_upload = perform_upload_check(xml_conversion_status['resultXML'], '--replace')
        if errors_upload:
            response['resultCode'], response['errors'] = 113, \
                errors_upload
            return response

        response.update(xml_conversion_status)
        if xml_conversion_status['resultMsg'] == 'textmarc_parsing_success':
            create_cache(recid, uid,
                create_record(response['resultXML'])[0])
            save_xml_record(recid, uid)
            response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV["record_submitted"]

    return response


def perform_request_update_record(request_type, recid, uid, cacheMTime, data,
                                  hpChanges, undoRedoOp, isBulk=False):
    """
    Handle record update requests like adding, modifying, moving or deleting
    of fields or subfields. Possible common error situations::
     - Missing cache file
     - Cache file modified in other editor
    @param undoRedoOp: Indicates in "undo"/"redo"/undo_descriptor operation is
                       performed by a current request.
    """

    response = {}
    if not cache_exists(recid, uid):
        response['resultCode'] = 106
    elif get_cache_mtime(recid, uid) != cacheMTime and isBulk is False:
        # In case of a bulk request, the changes are deliberately performed
        # immediately one after another
        response['resultCode'] = 107
    else:
        record_revision, record, pending_changes, deactivated_hp_changes, \
            undo_list, redo_list = get_cache_contents(recid, uid)[1:]

        # process all the Holding Pen changes operations ... regardles the
        # request type
        if "toDisable" in hpChanges:
            for changeId in hpChanges["toDisable"]:
                pending_changes[changeId]["applied_change"] = True

        if "toEnable" in hpChanges:
            for changeId in hpChanges["toEnable"]:
                pending_changes[changeId]["applied_change"] = False

        if "toOverride" in hpChanges:
            pending_changes = hpChanges["toOverride"]

        if "changesetsToDeactivate" in hpChanges:
            for changesetId in hpChanges["changesetsToDeactivate"]:
                deactivated_hp_changes[changesetId] = True

        if "changesetsToActivate" in hpChanges:
            for changesetId in hpChanges["changesetsToActivate"]:
                deactivated_hp_changes[changesetId] = False

        # processing the undo/redo entries
        if undoRedoOp == "undo":
            try:
                redo_list = [undo_list[-1]] + redo_list
                undo_list = undo_list[:-1]
            except:
                raise Exception("An exception occured when undoing previous" +
                                " operation. Undo list: " + str(undo_list) +
                                " Redo list " + str(redo_list))
        elif undoRedoOp == "redo":
            try:
                undo_list = undo_list + [redo_list[0]]
                redo_list = redo_list[1:]
            except:
                raise Exception("An exception occured when redoing previous" +
                                " operation. Undo list: " + str(undo_list) +
                                " Redo list " + str(redo_list))
        else:
            # This is a genuine operation - we have to add a new descriptor
            # to the undo list and cancel the redo unless the operation is
            # a bulk operation
            if undoRedoOp is not None:
                undo_list = undo_list + [undoRedoOp]
                redo_list = []
            else:
                assert isBulk is True

        field_position_local = data.get('fieldPosition')
        if field_position_local is not None:
            field_position_local = int(field_position_local)
        if request_type == 'otherUpdateRequest':
            # An empty request. Might be useful if we want to perform
            # operations that require only the actions performed globally,
            # like modifying the holdingPen changes list
            response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV[
                'editor_modifications_changed']
        elif request_type == 'deactivateHoldingPenChangeset':
            # the changeset has been marked as processed ( user applied it in
            # the editor). Marking as used in the cache file.
            # CAUTION: This function has been implemented here because logically
            #          it fits with the modifications made to the cache file.
            #          No changes are made to the Holding Pen physically. The
            #          changesets are related to the cache because we want to
            #          cancel the removal every time the cache disappears for
            #          any reason
            response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV[
                'disabled_hp_changeset']
        elif request_type == 'addField':
            if data['controlfield']:
                record_add_field(record, data['tag'],
                                 controlfield_value=data['value'])
                response['resultCode'] = 20
            else:
                record_add_field(record, data['tag'], data['ind1'],
                                 data['ind2'], subfields=data['subfields'],
                                 field_position_local=field_position_local)
                response['resultCode'] = 21

        elif request_type == 'addSubfields':
            subfields = data['subfields']
            for subfield in subfields:
                record_add_subfield_into(record, data['tag'], subfield[0],
                    subfield[1], subfield_position=None,
                    field_position_local=field_position_local)
            if len(subfields) == 1:
                response['resultCode'] = 22
            else:
                response['resultCode'] = 23
        elif request_type == 'addFieldsSubfieldsOnPositions':
            #1) Sorting the fields by their identifiers
            fieldsToAdd = data['fieldsToAdd']
            subfieldsToAdd = data['subfieldsToAdd']
            for tag in fieldsToAdd.keys():
                positions = fieldsToAdd[tag].keys()
                positions.sort()
                for position in positions:
                    # now adding fields at a position

                    isControlfield = (len(fieldsToAdd[tag][position][0]) == 0)
                    # if there are n subfields, this is a control field
                    if isControlfield:
                        controlfieldValue = fieldsToAdd[tag][position][3]
                        record_add_field(record, tag,
                                         field_position_local=int(position),
                                         controlfield_value=controlfieldValue)
                    else:
                        subfields = fieldsToAdd[tag][position][0]
                        ind1 = fieldsToAdd[tag][position][1]
                        ind2 = fieldsToAdd[tag][position][2]
                        record_add_field(record, tag, ind1, ind2,
                                         subfields=subfields,
                                         field_position_local=int(position))
            # now adding the subfields
            for tag in subfieldsToAdd.keys():
                for fieldPosition in subfieldsToAdd[tag].keys():  # now the fields
                                                                  # order not important !
                    subfieldsPositions = subfieldsToAdd[tag][fieldPosition]. \
                                           keys()
                    subfieldsPositions.sort()
                    for subfieldPosition in subfieldsPositions:
                        subfield = subfieldsToAdd[tag][fieldPosition][subfieldPosition]
                        record_add_subfield_into(record, tag, subfield[0], subfield[1],
                                                 subfield_position=int(subfieldPosition),
                                                 field_position_local=int(fieldPosition))

            response['resultCode'] = \
                CFG_BIBEDIT_AJAX_RESULT_CODES_REV['added_positioned_subfields']

        elif request_type == 'modifyField': # changing the field structure
            # first remove subfields and then add new... change the indices
            subfields = data['subFields'] # parse the JSON representation of
                                          # the subfields here

            new_field = create_field(subfields, data['ind1'], data['ind2'])
            record_replace_field(record, data['tag'], new_field,
                field_position_local=data['fieldPosition'])
            response['resultCode'] = 26

        elif request_type == 'modifyContent':
            if data['subfieldIndex'] is not None:
                record_modify_subfield(record, data['tag'],
                    data['subfieldCode'], data['value'],
                    int(data['subfieldIndex']),
                    field_position_local=field_position_local)
            else:
                record_modify_controlfield(record, data['tag'], data["value"],
                  field_position_local=field_position_local)
            response['resultCode'] = 24

        elif request_type == 'modifySubfieldTag':
            record_add_subfield_into(record, data['tag'], data['subfieldCode'],
            data["value"], subfield_position= int(data['subfieldIndex']),
            field_position_local=field_position_local)

            record_delete_subfield_from(record, data['tag'], int(data['subfieldIndex']) + 1,
            field_position_local=field_position_local)

            response['resultCode'] = 24

        elif request_type == 'modifyFieldTag':
            subfields = record_get_subfields(record, data['oldTag'],
            field_position_local=field_position_local)

            record_add_field(record, data['newTag'], data['ind1'],
                             data['ind2'] , subfields=subfields)

            record_delete_field(record, data['oldTag'], ind1=data['oldInd1'],
                                ind2=data['oldInd2'], field_position_local=field_position_local)
            response['resultCode'] = 32

        elif request_type == 'moveSubfield':
            record_move_subfield(record, data['tag'],
                int(data['subfieldIndex']), int(data['newSubfieldIndex']),
                field_position_local=field_position_local)
            response['resultCode'] = 25

        elif request_type == 'moveField':
            if data['direction'] == 'up':
                final_position_local = field_position_local-1
            else: # direction is 'down'
                final_position_local = field_position_local+1
            record_move_fields(record, data['tag'], [field_position_local],
                final_position_local)
            response['resultCode'] = 32

        elif request_type == 'deleteFields':
            to_delete = data['toDelete']
            deleted_fields = 0
            deleted_subfields = 0
            for tag in to_delete:
                #Sorting the fields in a edcreasing order by the local position!
                fieldsOrder = to_delete[tag].keys()
                fieldsOrder.sort(lambda a, b: int(b) - int(a))
                for field_position_local in fieldsOrder:
                    if not to_delete[tag][field_position_local]:
                        # No subfields specified - delete entire field.
                        record_delete_field(record, tag,
                            field_position_local=int(field_position_local))
                        deleted_fields += 1
                    else:
                        for subfield_position in \
                                to_delete[tag][field_position_local][::-1]:
                            # Delete subfields in reverse order (to keep the
                            # indexing correct).
                            record_delete_subfield_from(record, tag,
                                int(subfield_position),
                                field_position_local=int(field_position_local))
                            deleted_subfields += 1
            if deleted_fields == 1 and deleted_subfields == 0:
                response['resultCode'] = 26
            elif deleted_fields and deleted_subfields == 0:
                response['resultCode'] = 27
            elif deleted_subfields == 1 and deleted_fields == 0:
                response['resultCode'] = 28
            elif deleted_subfields and deleted_fields == 0:
                response['resultCode'] = 29
            else:
                response['resultCode'] = 30

        response['cacheMTime'] = update_cache_contents(recid,
                                                       uid,
                                                       record_revision,
                                                       record,
                                                       pending_changes,
                                                       deactivated_hp_changes,
                                                       undo_list, redo_list)
        response['cacheDirty'] = True

    return response


def perform_request_autocomplete(request_type, recid, uid, data):
    """
    Perfrom an AJAX request associated with the retrieval of autocomplete
    data.

    @param request_type: Type of the currently served request
    @param recid: the identifer of the record
    @param uid: The identifier of the user being currently logged in
    @param data: The request data containing possibly important additional
                 arguments
    """
    response = {}
    # get the values based on which one needs to search
    searchby = data['value']
        # we check if the data is properly defined
    fulltag = ''
    if 'maintag' in data and 'subtag1' in data and \
            'subtag2' in data and 'subfieldcode' in data:
        maintag = data['maintag']
        subtag1 = data['subtag1']
        subtag2 = data['subtag2']
        u_subtag1 = subtag1
        u_subtag2 = subtag2
        if (not subtag1) or (subtag1 == ' '):
            u_subtag1 = '_'
        if (not subtag2) or (subtag2 == ' '):
            u_subtag2 = '_'
        subfieldcode = data['subfieldcode']
        fulltag = maintag+u_subtag1+u_subtag2+subfieldcode
    if (request_type == 'autokeyword'):
        # call the keyword-form-ontology function
        if fulltag and searchby:
            items = get_kbt_items_for_bibedit(CFG_BIBEDIT_KEYWORD_TAXONOMY,
                                              CFG_BIBEDIT_KEYWORD_RDFLABEL,
                                              searchby)
            response['autokeyword'] = items
    if (request_type == 'autosuggest'):
        # call knowledge base function to put the suggestions in an array..
        if fulltag and searchby and len(searchby) > 3:
            # add trailing '*' wildcard for 'search_unit_in_bibxxx()' if not already present
            suggest_values = get_kbd_values_for_bibedit(fulltag, "", searchby+"*")
            # remove ..
            new_suggest_vals = []
            for sugg in suggest_values:
                if sugg.startswith(searchby):
                    new_suggest_vals.append(sugg)
            response['autosuggest'] = new_suggest_vals
    if (request_type == 'autocomplete'):
        # call the values function with the correct kb_name
        if fulltag in CFG_BIBEDIT_AUTOCOMPLETE_TAGS_KBS:
            kbname = CFG_BIBEDIT_AUTOCOMPLETE_TAGS_KBS[fulltag]
            # check if the seachby field has semicolons. Take all
            # the semicolon-separated items..
            items = []
            vals = []
            if searchby:
                if searchby.rfind(';'):
                    items = searchby.split(';')
                else:
                    items = [searchby.strip()]
            for item in items:
                item = item.strip()
                kbrvals = get_kbr_values(kbname, item, '', 'e')  # we want an exact match
                if kbrvals and kbrvals[0]:  # add the found val into vals
                    vals.append(kbrvals[0])
            #check that the values are not already contained in other
            #instances of this field
            record = get_cache_contents(recid, uid)[2]
            xml_rec = wash_for_xml(print_rec(record))
            record, status_code, dummy_errors = create_record(xml_rec)
            existing_values = []
            if (status_code != 0):
                existing_values = record_get_field_values(record,
                                                          maintag,
                                                          subtag1,
                                                          subtag2,
                                                          subfieldcode)
            #get the new values.. i.e. vals not in existing
            new_vals = vals
            for val in new_vals:
                if val in existing_values:
                    new_vals.remove(val)
            response['autocomplete'] = new_vals
    response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['autosuggestion_scanned']
    return response


def perform_request_bibcatalog(request_type, uid, data):
    """Handle request to BibCatalog (RT).

    """
    response = {}

    if request_type == 'getTickets':
        # Insert the tickets data in the response, if possible
        if not CFG_BIBCATALOG_SYSTEM or not CFG_CAN_SEARCH_FOR_TICKET:
            response['tickets'] = "<!--No ticket system configured-->"
        elif uid:
            bibcat_resp = BIBCATALOG_SYSTEM.check_system(uid)
            if bibcat_resp == "":
                tickets_found = BIBCATALOG_SYSTEM.ticket_search(uid,
                    status=['new', 'open'], recordid=data['recID'])
                tickets = []
                for t_id in tickets_found:
                    ticket_info = BIBCATALOG_SYSTEM.ticket_get_info(
                        uid, t_id, ['url_display', 'url_close', 'subject', 'text', 'queue', 'created'])
                    t_url = ticket_info['url_display']
                    t_close_url = ticket_info['url_close']
                    t_subject = ticket_info['subject']
                    t_text = ticket_info['text']
                    t_queue = ticket_info['queue']
                    date_string = ticket_info['created']
                    date_splitted = date_string.split(" ")
                    # convert date to readable format
                    try:
                        t_date = date_splitted[2] + ' ' + date_splitted[1] +\
                        " " + date_splitted[4] + " " +\
                        date_splitted[3].split(":")[0] + ":" +\
                        date_splitted[3].split(":")[1]
                    except IndexError:
                        t_date = date_string

                    ticket = {"id": str(t_id), "queue": t_queue, "date": t_date, "url": t_url,
                              "close_url": t_close_url, "subject": t_subject, "text": t_text}
                    tickets.append(ticket)
                response['tickets'] = tickets
                response['resultCode'] = 31
            else:
                # put something in the tickets container, for debug
                response['tickets'] = "Error connecting to RT<!--" + bibcat_resp + "-->"
                response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_rt_connection']
    # closeTicket usecase
    elif request_type == 'closeTicket':
        if not CFG_BIBCATALOG_SYSTEM or not CFG_CAN_SEARCH_FOR_TICKET:
            response['ticket_closed_description'] = "<!--No ticket system configured-->"
            response['ticket_closed_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_ticket_closed']
        elif uid:
            bibcat_resp = BIBCATALOG_SYSTEM.check_system(uid)
            if bibcat_resp == "":
                un, pw = get_bibcat_from_prefs(uid)
                if un and pw:
                    BIBCATALOG_SYSTEM.ticket_steal(uid, data['ticketid'])
                    ticket_closed = BIBCATALOG_SYSTEM.ticket_set_attribute(uid, data['ticketid'], 'status', 'resolved')
                    if ticket_closed == 1:
                        response['ticket_closed_description'] = 'Ticket resolved'
                        response['ticket_closed_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['ticket_closed']
                    else:
                        response['ticket_closed_description'] = 'Ticket could not be resolved.Try again'
                        response['ticket_closed_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_ticket_closed']
                else:
                    response['ticket_closed_description'] = 'RT user does not exist'
                    response['ticket_closed_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_ticket_closed']
            else:
                #put something in the tickets container, for debug
                response['ticket_closed_description'] = "Error connecting to RT<!--" + bibcat_resp + "-->"
                response['ticket_closed_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_rt_connection']
        response['ticketid'] = data['ticketid']
    elif request_type == 'openTicket':
        if not CFG_BIBCATALOG_SYSTEM or not CFG_CAN_SEARCH_FOR_TICKET:
            response['ticket_opened_description'] = "<!--No ticket system configured-->"
            response['ticket_opened_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_ticket_opened']
        elif uid:
            bibcat_resp = BIBCATALOG_SYSTEM.check_system(uid)
            if bibcat_resp == "":
                un, pw = get_bibcat_from_prefs(uid)
                if un and pw:
                    ticket_opened = BIBCATALOG_SYSTEM.ticket_set_attribute(uid, data['ticketid'], 'status', 'open')
                    if ticket_opened == 1:
                        response['ticket_opened_description'] = 'Ticket opened'
                        response['ticket_opened_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['ticket_opened']
                    else:
                        response['ticket_opened_description'] = 'Ticket could not be opened.Try again'
                        response['ticket_opened_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_ticket_opened']
                else:
                    response['ticket_opened_description'] = 'RT user does not exist'
                    response['ticket_opened_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_ticket_opened']
            else:
                #put something in the tickets container, for debug
                response['ticket_opened_description'] = "Error connecting to RT<!--" + bibcat_resp + "-->"
                response['ticket_opened_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_rt_connection']
        response['ticketid'] = data['ticketid']
    elif request_type == 'createTicket':
        if BIBCATALOG_SYSTEM is None:
            response['ticket_created_description'] = "<!--No ticket system configured-->"
            response['ticket_created_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_ticket_created']
        elif BIBCATALOG_SYSTEM and uid:
            bibcat_resp = BIBCATALOG_SYSTEM.check_system(uid)
            if bibcat_resp == "":
                un, pw = get_bibcat_from_prefs(uid)
                if un and pw:
                    ticket_created = BIBCATALOG_SYSTEM.ticket_submit(uid, data['subject'], data['recID'],
                                     data['text'], data['queue'], data['priority'], data['owner'], data['requestor'])
                    if ticket_created:
                        response['ticket_created_description'] = ticket_created
                        response['ticket_created_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['ticket_created']
                    else:
                        response['ticket_created_description'] = 'Ticket could not be created.Try again'
                        response['ticket_created_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_ticket_created']
                else:
                    response['ticket_created_description'] = 'RT user does not exist'
                    response['ticket_created_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_ticket_created']
            else:
                #put something in the tickets container, for debug
                response['ticket_created_description'] = "Error connecting to RT<!--" + bibcat_resp + "-->"
                response['ticket_created_code'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['error_rt_connection']
    elif request_type == 'getNewTicketRTInfo':
        # Insert the tickets data in the response, if possible
        response = get_new_ticket_RT_info(uid, data['recID'])
    return response


def _add_curated_references_to_record(recid, uid, bibrec):
    """
    Adds references from the cache that have been curated (contain $$9CURATOR)
    to the bibrecord object

    @param recid: record id, used to retrieve cache
    @param uid: id of the current user, used to retrieve cache
    @param bibrec: bibrecord object to add references to
    """
    dummy1, dummy2, record, dummy3, dummy4, dummy5, dummy6 = get_cache_contents(recid, uid)
    for field_instance in record_get_field_instances(record, "999", "C", "5"):
        for subfield_instance in field_instance[0]:
            if subfield_instance[0] == '9' and subfield_instance[1] == 'CURATOR':
                # Add reference field on top of references, removing first $$o
                field_instance = ([subfield for subfield in field_instance[0]
                                   if subfield[0] != 'o'], field_instance[1],
                                   field_instance[2], field_instance[3],
                                   field_instance[4])
                record_add_fields(bibrec, '999', [field_instance],
                                  field_position_local=0)


def _xml_to_textmarc_references(bibrec):
    """
    Convert XML record to textmarc and return the lines related to references

    @param bibrec: bibrecord object to be converted

    @return: textmarc lines with references
    @rtype: string
    """
    sysno = ""

    options = {"aleph-marc": 0, "correct-mode": 1, "append-mode": 0,
               "delete-mode": 0, "insert-mode": 0, "replace-mode": 0,
               "text-marc": 1}

    # Using deepcopy as function create_marc_record() modifies the record passed
    textmarc_references = [line.strip() for line
        in xmlmarc2textmarc.create_marc_record(copy.deepcopy(bibrec),
            sysno, options).split('\n')
        if '999C5' in line]

    return textmarc_references


def perform_request_ref_extract_url(recid, uid, url):
    """
    Making use of the refextractor API, extract references from the url
    received from the client

    @param recid: opened record id
    @param uid: active user id
    @param url: URL to extract references from

    @return response to be returned to the client code
    """
    response = {}
    try:
        recordExtended = replace_references(recid, uid, url=url)
    except FullTextNotAvailable:
        response['ref_xmlrecord'] = False
        response['ref_msg'] = "File not found. Server returned code 404"
        return response
    except:
        response['ref_xmlrecord'] = False
        response['ref_msg'] = """Error while fetching PDF. Bad URL or file could
                                 not be retrieved """
        return response

    if not recordExtended:
        response['ref_msg'] = """No references were found in the given PDF """
        return response

    ref_bibrecord = create_record(recordExtended)[0]
    _add_curated_references_to_record(recid, uid, ref_bibrecord)

    response['ref_bibrecord'] = ref_bibrecord
    response['ref_xmlrecord'] = record_xml_output(ref_bibrecord)

    textmarc_references = _xml_to_textmarc_references(ref_bibrecord)

    response['ref_textmarc'] = '<div class="refextracted">' + '<br />'.join(textmarc_references) + "</div>"

    return response


def perform_request_ref_extract(recid, uid, txt=None):
    """ Handle request to extract references in the given record

    @param recid: record id from which the references should be extracted
    @type recid: str
    @param txt: string containing references
    @type txt: str
    @param uid: user id
    @type uid: int

    @return: xml record with references extracted
    @rtype: dictionary
    """

    text_no_references_found_msg = """ No references extracted. The automatic
                            extraction did not recognize any reference in the
                            pasted text.<br /><br />If you want to add the references
                            manually, an easily recognizable format is:<br/><br/>
                            &nbsp;&nbsp;&nbsp;&nbsp;[1] Phys. Rev A71 (2005) 42<br />
                            &nbsp;&nbsp;&nbsp;&nbsp;[2] ATLAS-CMS-2007-333
                            """

    pdf_no_references_found_msg = """ No references were found in the attached
                                    PDF.
                                  """

    response = {}
    response['ref_xmlrecord'] = False
    recordExtended = None
    try:
        if txt:
            recordExtended = replace_references(recid, uid,
                                                txt=txt.decode('utf-8'))
            if not recordExtended:
                response['ref_msg'] = text_no_references_found_msg
        else:
            recordExtended = replace_references(recid, uid)
            if not recordExtended:
                response['ref_msg'] = pdf_no_references_found_msg
    except FullTextNotAvailable:
        response['ref_msg'] = """ The fulltext is not available.
                              """
    except:
        response['ref_msg'] = """ An error ocurred while extracting references.
                              """

    if not recordExtended:
        return response

    ref_bibrecord = create_record(recordExtended)[0]

    _add_curated_references_to_record(recid, uid, ref_bibrecord)

    response['ref_bibrecord'] = ref_bibrecord
    response['ref_xmlrecord'] = record_xml_output(ref_bibrecord)

    textmarc_references = _xml_to_textmarc_references(ref_bibrecord)
    response['ref_textmarc'] = '<div class="refextracted">' + '<br />'.join(textmarc_references) + "</div>"

    return response


def perform_request_preview_record(request_type, recid, uid, data):
    """ Handle request to preview record with formatting

    """
    response = {}
    if request_type == "preview":
        if data["submitMode"] == "textmarc":
            textmarc_record = data['textmarc']
            xml_conversion_status = get_xml_from_textmarc(recid, textmarc_record, uid)
            if xml_conversion_status['resultMsg'] == 'textmarc_parsing_error':
                response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['textmarc_parsing_error']
                response.update(xml_conversion_status)
                return response
            record = create_record(xml_conversion_status["resultXML"])[0]
        elif cache_exists(recid, uid):
            dummy1, dummy2, record, dummy3, dummy4, dummy5, dummy6 = get_cache_contents(recid, uid)
        else:
            record = get_bibrecord(recid)

    # clean the record from unfilled volatile fields
    record_strip_empty_volatile_subfields(record)
    record_strip_empty_fields(record)
    response['html_preview'] = _get_formated_record(record, data['new_window'])

    # clean the record from unfilled volatile fields
    record_strip_empty_volatile_subfields(record)
    record_strip_empty_fields(record)
    response['html_preview'] = _get_formated_record(record, data['new_window'])

    return response


def perform_request_get_pdf_url(recid):
    """ Handle request to get the URL of the attached PDF
    """
    response = {}
    doc = get_pdf_doc(recid)
    if doc:
        response['pdf_url'] = doc.get_url()
    else:
        response['pdf_url'] = ""
    return response


def perform_request_get_textmarc(recid, uid):
    """ Get record content from cache, convert it to textmarc and return it
    """
    textmarc_options = {"aleph-marc": 0, "correct-mode": 1, "append-mode": 0,
                        "delete-mode": 0, "insert-mode": 0, "replace-mode": 0,
                        "text-marc": 1}

    bibrecord = get_cache_contents(recid, uid)[2]
    record_strip_empty_fields(bibrecord)
    record_strip_controlfields(bibrecord)

    textmarc = xmlmarc2textmarc.create_marc_record(
            copy.deepcopy(bibrecord), sysno="", options=textmarc_options)

    return {'textmarc': textmarc}


def perform_request_get_tableview(recid, uid, data):
    """ Convert textmarc inputed by user to marcxml and if there are no
    parsing errors, create cache file
    """
    response = {}
    textmarc_record = data['textmarc']
    if not textmarc_record:
        response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['tableview_change_success']
    xml_conversion_status = get_xml_from_textmarc(recid, textmarc_record, uid)
    response.update(xml_conversion_status)

    if xml_conversion_status['resultMsg'] == 'textmarc_parsing_error':
        response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['textmarc_parsing_error']
    else:
        create_cache(recid, uid,
            create_record(xml_conversion_status['resultXML'])[0], data['recordDirty'],
                            disabled_hp_changes=data['disabled_hp_changes'])
        response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV['tableview_change_success']
        response['cacheMTime'] = get_cache_mtime(recid, uid)
    return response


def _get_formated_record(record, new_window):
    """Returns a record in a given format

    @param record: BibRecord object
    @param new_window: Boolean, indicates if it is needed to add all the headers
    to the page (used when clicking Preview button)
    """
    from invenio.config import CFG_WEBSTYLE_TEMPLATE_SKIN

    xml_record = wash_for_xml(record_xml_output(record))

    result = ''
    if new_window:
        result = """ <html><head><title>Record preview</title>
                      <script type="text/javascript" src="%(site_url)s/js/jquery.min.js"></script>
                      <link rel="stylesheet" href="%(site_url)s/img/invenio%(cssskin)s.css" type="text/css"></head>
                   """ % {'site_url': CFG_SITE_URL,
                         'cssskin': CFG_WEBSTYLE_TEMPLATE_SKIN != 'default' and '_' + CFG_WEBSTYLE_TEMPLATE_SKIN or ''
                         }
        result += get_mathjax_header(True) + '<body>'
        result += "<h2> Brief format preview </h2><br />"
        result += bibformat.format_record(0,
                                          of="hb",
                                          xml_record=xml_record) + "<br />"

    result += "<br /><h2> Detailed format preview </h2><br />"
    result += bibformat.format_record(0,
                                      of="hd",
                                      xml_record=xml_record)
    #Preview references
    result += "<br /><h2> References </h2><br />"

    result += bibformat.format_record(0,
                                     'hdref',
                                      xml_record=xml_record)

    result += """<script>
                    $('#referenceinp_link').hide();
                    $('#referenceinp_link_span').hide();
                </script>
              """
    if new_window:
        result += "</body></html>"


    return result

########### Functions related to templates web interface #############

def perform_request_init_template_interface():
    """Handle a request to manage templates"""
    errors = []
    warnings = []
    body = ''

    # Add script data.
    record_templates = get_record_templates()
    record_templates.sort()

    data = {'gRECORD_TEMPLATES': record_templates,
            'gSITE_RECORD': '"' + CFG_SITE_RECORD + '"',
            'gSITE_URL': '"' + CFG_SITE_URL + '"'}

    body += '<script type="text/javascript">\n'
    for key in data:
        body += '    var %s = %s;\n' % (key, data[key])
    body += '    </script>\n'

    # Add scripts (the ordering is NOT irrelevant).
    scripts = ['jquery-ui.min.js',
               'json2.js', 'bibedit_display.js',
               'bibedit_template_interface.js']

    for script in scripts:
        body += '    <script type="text/javascript" src="%s/js/%s">' \
            '</script>\n' % (CFG_SITE_URL, script)

    body += '    <div id="bibEditTemplateList"></div>\n'
    body += '    <div id="bibEditTemplateEdit"></div>\n'

    return body, errors, warnings


def perform_request_ajax_template_interface(data):
    """Handle Ajax requests by redirecting to appropriate function."""
    response = {}
    request_type = data['requestType']

    if request_type == 'editTemplate':
        # Edit a template request.
        response.update(perform_request_edit_template(data))

    return response


def perform_request_edit_template(data):
    """ Handle request to edit a template """
    response = {}
    template_filename = data['templateFilename']
    template = get_record_template(template_filename)
    if not template:
        response['resultCode'] = 1
    else:
        response['templateMARCXML'] = template

    return response


def perform_doi_search(doi):
    """Search for DOI on the dx.doi.org page
    @return: the url returned by this page"""
    response = {}
    url = "http://dx.doi.org/"
    val = {'hdl': doi}
    url_data = urllib.urlencode(val)
    cj = cookielib.CookieJar()
    header = [('User-Agent', CFG_DOI_USER_AGENT)]
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = header
    try:
        resp = opener.open(url, url_data)
    except:
        return response
    else:
        response['doi_url'] = resp.geturl()
    return response


def check_hide_authors(record):
    """ Check if authors should be hidden by default in the user interface """
    return sum([len(record.get(tag, [])) for tag in CFG_BIBEDIT_DISPLAY_AUTHOR_TAGS]) > CFG_BIBEDIT_AUTHOR_DISPLAY_THRESHOLD


def perform_guess_affiliations(uid, data):
    response = {}
    recid = data["recID"]
    record_revision, record, pending_changes, deactivated_hp_changes, \
        undo_list, redo_list = get_cache_contents(recid, uid)[1:]

    # Let's guess affiliations
    result = {}
    for tag in CFG_BIBEDIT_DISPLAY_AUTHOR_TAGS:
        result[tag] = {}
        author_field_instances = record_get_field_instances(record, tag)
        for field_pos, instance in enumerate(author_field_instances):
            subfields_to_add = []
            current_affilations = field_get_subfield_values(instance, code="u")
            if not current_affilations or current_affilations[0].startswith("VOLATILE:"):
                # This author does not have affiliation
                try:
                    author_name = field_get_subfield_values(instance, code="a")[0]
                except IndexError:
                    author_name = author_name[0]
                aff_guess = get_affiliation_for_paper(recid, author_name)
                if aff_guess:
                    for aff in aff_guess:
                        field_add_subfield(instance, code="u", value=aff)
                        subfields_to_add.append(["u", aff])
            if subfields_to_add:
                result[tag][field_pos] = subfields_to_add

    response['cacheMTime'] = update_cache_contents(recid, uid, record_revision,
                                                   record, pending_changes,
                                                   deactivated_hp_changes,
                                                   undo_list, redo_list)
    response['subfieldsToAdd'] = result

    return response


def perform_request_submit(recid, uid, data, response):
    if not cache_exists(recid, uid):
        response['resultCode'] = 106
    elif not get_cache_mtime(recid, uid) == data['cacheMTime']:
        response['resultCode'] = 107
    elif cache_expired(recid, uid) and \
            record_locked_by_other_user(recid, uid):
        response['resultCode'] = 104
    elif record_locked_by_queue(recid):
        response['resultCode'] = 105
    else:
        dummy_cache_dirty, record_revision, record, dummy_pending_changes, \
            disabled_hp_changes, dummy_undo_list, dummy_redo_list \
                                            = get_cache_contents(recid, uid)

        xml_record = wash_for_xml(print_rec(record))
        record, status_code, list_of_errors = create_record(xml_record)

        # Simulate upload to catch errors
        errors_upload = perform_upload_check(xml_record, '--replace')
        if errors_upload:
            response['resultCode'], response['errors'] = 113, \
                errors_upload
            return response
        elif status_code == 0:
            response['resultCode'], response['errors'] = 110, \
                list_of_errors
        if not data['force'] and not latest_record_revision(recid, record_revision):
            response['cacheOutdated'] = True
        else:
            if record_is_conference(record):
                new_cnum = add_record_cnum(recid, uid)
                if new_cnum:
                    response["new_cnum"] = new_cnum

            save_xml_record(recid, uid)
            response['resultCode'] = 4
