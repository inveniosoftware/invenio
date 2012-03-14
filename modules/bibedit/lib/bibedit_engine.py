## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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
import difflib
import zlib

from invenio import bibrecord
from invenio import bibformat

from invenio.jsonutils import json, CFG_JSON_AVAILABLE
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
    CFG_BIBEDIT_KEYWORD_RDFLABEL

from invenio.config import CFG_SITE_LANG, CFG_DEVEL_SITE
from invenio.bibedit_dblayer import get_name_tags_all, reserve_record_id, \
    get_related_hp_changesets, get_hp_update_xml, delete_hp_change, \
    get_record_last_modification_date, get_record_revision_author, \
    get_marcxml_of_record_revision, delete_related_holdingpen_changes, \
    get_record_revisions

from invenio.bibedit_utils import cache_exists, cache_expired, \
    create_cache_file, delete_cache_file, get_bibrecord, \
    get_cache_file_contents, get_cache_mtime, get_record_templates, \
    get_record_template, latest_record_revision, record_locked_by_other_user, \
    record_locked_by_queue, save_xml_record, touch_cache_file, \
    update_cache_file_contents, get_field_templates, get_marcxml_of_revision, \
    revision_to_timestamp, timestamp_to_revision, \
    get_record_revision_timestamps, record_revision_exists, \
    can_record_have_physical_copies, extend_record_with_template, \
    merge_record_with_template

from invenio.bibrecord import create_record, print_rec, record_add_field, \
    record_add_subfield_into, record_delete_field, \
    record_delete_subfield_from, \
    record_modify_subfield, record_move_subfield, \
    create_field, record_replace_field, record_move_fields, \
    record_modify_controlfield, record_get_field_values, \
    record_get_subfields
from invenio.config import CFG_BIBEDIT_PROTECTED_FIELDS, CFG_CERN_SITE, \
    CFG_SITE_URL, CFG_SITE_RECORD, CFG_BIBEDIT_KB_SUBJECTS, \
    CFG_BIBEDIT_KB_INSTITUTIONS, CFG_BIBEDIT_AUTOCOMPLETE_INSTITUTIONS_FIELDS
from invenio.search_engine import record_exists, search_pattern
from invenio.webuser import session_param_get, session_param_set
from invenio.bibcatalog import bibcatalog_system
from invenio.webpage import page
from invenio.htmlutils import get_mathjax_header
from invenio.textutils import wash_for_xml
from invenio.bibknowledge import get_kbd_values_for_bibedit, get_kbr_values, \
     get_kbt_items_for_bibedit, kb_exists

from invenio.bibcirculation_dblayer import get_number_copies, has_copies
from invenio.bibcirculation_utils import create_item_details_url

import invenio.template
bibedit_templates = invenio.template.load('bibedit')

re_revdate_split = re.compile('^(\d\d\d\d)(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)')

def get_empty_fields_templates():
    """
    Returning the templates of empty fields::
     -an empty data field
     -an empty control field
    """
    return [{
                "name": "Empty field",
                "description": "The data field not containing any " + \
                               "information filled in",
                "tag" : "",
                "ind1" : "",
                "ind2" : "",
                "subfields" : [("","")],
                "isControlfield" : False
            },{
                "name" : "Empty control field",
                "description" : "The controlfield not containing any " + \
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
    history_url = '"' + CFG_SITE_URL + '/admin/bibedit/bibeditadmin.py/history"'
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


    if CFG_CERN_SITE:
        cern_site = 'true'
    data = {'gRECORD_TEMPLATES': record_templates,
            'gTAG_NAMES': tag_names,
            'gPROTECTED_FIELDS': protected_fields,
            'gSITE_URL': '"' + CFG_SITE_URL + '"',
            'gSITE_RECORD': '"' + CFG_SITE_RECORD + '"',
            'gHISTORY_URL': history_url,
            'gCERN_SITE': cern_site,
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
            'gAVAILABLE_KBS': get_available_kbs(),
            'gTagsToAutocomplete': CFG_BIBEDIT_AUTOCOMPLETE_INSTITUTIONS_FIELDS
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
    scripts = ['jquery.jeditable.mini.js', 'jquery.hotkeys.js', 'json2.js',
               'bibedit_display.js', 'bibedit_engine.js', 'bibedit_keys.js',
               'bibedit_menu.js', 'bibedit_holdingpen.js', 'marcxml.js',
               'bibedit_clipboard.js','jquery-ui.min.js']

    for script in scripts:
        body += '    <script type="text/javascript" src="%s/js/%s">' \
            '</script>\n' % (CFG_SITE_URL, script)

    body += '<link rel="stylesheet" type="text/css" href="/img/jquery-ui.css" />'

    # Build page structure and menu.
    # rec = create_record(format_record(235, "xm"))[0]
    #oaiId = record_extract_oai_id(rec)

    body += bibedit_templates.menu()
    body += '    <div id="bibEditContent"></div>\n'

    return body, errors, warnings

def get_available_kbs():
    """
    Return list of KBs that are available in the system to be used with
    BibEdit
    """
    kb_list = [CFG_BIBEDIT_KB_INSTITUTIONS, CFG_BIBEDIT_KB_SUBJECTS]
    available_kbs = [kb for kb in kb_list if kb_exists(kb)]
    return available_kbs

def get_xml_comparison(header1, header2, xml1, xml2):
    """
    Return diffs of two MARCXML records.
    """
    return "".join(difflib.unified_diff(xml1.splitlines(1),
        xml2.splitlines(1), header1, header2))

def get_marcxml_of_revision_id(recid, revid):
    """
    Return MARCXML string with corresponding to revision REVID
    (=RECID.REVDATE) of a record.  Return empty string if revision
    does not exist.
    """
    res = ""
    job_date = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(revid).groups()
    tmp_res = get_marcxml_of_record_revision(recid, job_date)
    if tmp_res:
        for row in tmp_res:
            res += zlib.decompress(row[0]) + "\n"
    return res

def perform_request_compare(ln, recid, rev1, rev2):
    """Handle a request for comparing two records"""
    body = ""
    errors = []
    warnings = []

    if (not record_revision_exists(recid, rev1)) or \
       (not record_revision_exists(recid, rev2)):
        body = "The requested record revision does not exist !"
    else:
        xml1 = get_marcxml_of_revision_id(recid, rev1)
        xml2 = get_marcxml_of_revision_id(recid, rev2)
        fullrevid1 = "%i.%s" % (recid, rev1)
        fullrevid2 = "%i.%s" % (recid, rev2)
        comparison = bibedit_templates.clean_value(
            get_xml_comparison(fullrevid1, fullrevid2, xml1, xml2),
            'text').replace('\n', '<br />\n           ')
        job_date1 = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(rev1).groups()
        job_date2 = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(rev2).groups()
        body += bibedit_templates.history_comparebox(ln, job_date1,
                                                 job_date2, comparison)
    return body, errors, warnings

def perform_request_newticket(recid, uid):
    """create a new ticket with this record's number
    @param recid: record id
    @param uid: user id
    @return: (error_msg, url)

    """
    t_url = ""
    errmsg = ""
    if bibcatalog_system is not None:
        t_id = bibcatalog_system.ticket_submit(uid, "", recid, "")
        if t_id:
            #get the ticket's URL
            t_url = bibcatalog_system.ticket_get_attribute(uid, t_id, 'url_modify')
        else:
            errmsg = "ticket_submit failed"
    else:
        errmsg = "No ticket system configured"
    return (errmsg, t_url)

def perform_request_ajax(req, recid, uid, data, isBulk = False, \
                         ln = CFG_SITE_LANG):
    """Handle Ajax requests by redirecting to appropriate function."""
    response = {}
    request_type = data['requestType']
    undo_redo = None
    if data.has_key("undoRedo"):
        undo_redo = data["undoRedo"]
    # Call function based on request type.
    if request_type == 'searchForRecord':
        # Search request.
        response.update(perform_request_search(data))
    elif request_type in ['changeTagFormat']:
        # User related requests.
        response.update(perform_request_user(req, request_type, recid, data))
    elif request_type in ('getRecord', 'submit', 'cancel', 'newRecord',
        'deleteRecord', 'deleteRecordCache', 'prepareRecordMerge', 'revert'):
        # 'Major' record related requests.
        response.update(perform_request_record(req, request_type, recid, uid,
                                               data))
    elif request_type in ('addField', 'addSubfields', \
                          'addFieldsSubfieldsOnPositions', 'modifyContent', \
                          'modifySubfieldTag', 'modifyFieldTag', \
                          'moveSubfield', 'deleteFields', 'moveField', \
                          'modifyField', 'otherUpdateRequest', \
                          'disableHpChange', 'deactivateHoldingPenChangeset'):
        # Record updates.
        cacheMTime = data['cacheMTime']
        if data.has_key('hpChanges'):
            hpChanges = data['hpChanges']
        else:
            hpChanges = {}

        response.update(perform_request_update_record(request_type, recid, \
                                                      uid, cacheMTime, data, \
                                                      hpChanges, undo_redo, \
                                                      isBulk, ln))
    elif request_type in ('autosuggest', 'autocomplete', 'autokeyword'):
        response.update(perform_request_autocomplete(request_type, recid, uid, \
                                                     data))

    elif request_type in ('getTickets', ):
        # BibCatalog requests.
        response.update(perform_request_bibcatalog(request_type, recid, uid))
    elif request_type in ('getHoldingPenUpdates', ):
        response.update(perform_request_holdingpen(request_type, recid))

    elif request_type in ('getHoldingPenUpdateDetails', \
                          'deleteHoldingPenChangeset'):
        updateId = data['changesetNumber']
        response.update(perform_request_holdingpen(request_type, recid, \
                                                   updateId))
    elif request_type in ('applyBulkUpdates', ):
        # a general version of a bulk request
        changes = data['requestsData']
        cacheMTime = data['cacheMTime']
        response.update(perform_bulk_request_ajax(req, recid, uid, changes, \
                                                  undo_redo, cacheMTime))
    elif request_type in ('preview', ):
        response.update(perform_request_preview_record(request_type, recid, uid))

    return response

def perform_bulk_request_ajax(req, recid, uid, reqsData, undoRedo, cacheMTime):
    """ An AJAX handler used when treating bulk updates """
    lastResult = {}
    lastTime = cacheMTime
    isFirst = True
    for data in reqsData:
        assert data != None
        data['cacheMTime'] = lastTime
        if isFirst and undoRedo != None:
            # we add the undo/redo handler to the first operation in order to
            # save the handler on the server side !
            data['undoRedo'] = undoRedo
            isFirst = False
        lastResult = perform_request_ajax(req, recid, uid, data, True)
        # now we have to update the cacheMtime in next request !
#        if lastResult.has_key('cacheMTime'):
        try:
            lastTime = lastResult['cacheMTime']
        except:
            raise Exception(str(lastResult))
    return lastResult

def perform_request_search(data):
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
    result_set = list(search_pattern(p=pattern))
    response['resultCode'] = 1
    response['resultSet'] = result_set[0:CFG_BIBEDIT_MAX_SEARCH_RESULTS]
    return response

def perform_request_user(req, request_type, recid, data):
    """Handle user related requests."""
    response = {}
    if request_type == 'changeTagFormat':
        try:
            tagformat_settings = session_param_get(req, 'bibedit_tagformat')
        except KeyError:
            tagformat_settings = {}
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
        response["changes"] = changes
    elif request_type == 'getHoldingPenUpdateDetails':
        # returning the list of changes related to the holding pen update
        # the format based on what the record difference xtool returns

        assert(changeId != None)
        hpContent = get_hp_update_xml(changeId)
        holdingPenRecord = create_record(hpContent[0], "xm")[0]
#        databaseRecord = get_record(hpContent[1])
        response['record'] = holdingPenRecord
        response['changeset_number'] = changeId
    elif request_type == 'deleteHoldingPenChangeset':
        assert(changeId != None)
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
            create_cache_file(recid, uid)
            response['resultCode'], response['newRecID'] = 6, new_recid

        elif new_type == 'template':
            # Create a new record from XML record template.
            template_filename = data['templateFilename']
            template = get_record_template(template_filename)
            if not template:
                response['resultCode']  = 108
            else:
                record = create_record(template)[0]
                if not record:
                    response['resultCode']  = 109
                else:
                    record_add_field(record, '001',
                                     controlfield_value=str(new_recid))
                    create_cache_file(new_recid, uid, record, True)
                    response['resultCode'], response['newRecID']  = 7, new_recid

        elif new_type == 'clone':
            # Clone an existing record (from the users cache).
            existing_cache = cache_exists(recid, uid)
            if existing_cache:
                try:
                    record = get_cache_file_contents(recid, uid)[2]
                except:
                    # if, for example, the cache format was wrong (outdated)
                    record = get_bibrecord(recid)
            else:
                # Cache missing. Fall back to using original version.
                record = get_bibrecord(recid)
            record_delete_field(record, '001')
            record_add_field(record, '001', controlfield_value=str(new_recid))
            create_cache_file(new_recid, uid, record, True)
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

        if data.has_key("inReadOnlyMode"):
            read_only_mode = data['inReadOnlyMode']

        if record_status == 0:
            response['resultCode'] = 102
        elif record_status == -1:
            response['resultCode'] = 103
        elif not read_only_mode and not existing_cache and \
                record_locked_by_other_user(recid, uid):
            response['resultCode'] = 104
        elif not read_only_mode and existing_cache and \
                cache_expired(recid, uid) and \
                record_locked_by_other_user(recid, uid):
            response['resultCode'] = 104
        elif not read_only_mode and record_locked_by_queue(recid):
            response['resultCode'] = 105
        else:
            if data.get('deleteRecordCache'):
                delete_cache_file(recid, uid)
                existing_cache = False
                pending_changes = []
                disabled_hp_changes = {}
            if read_only_mode:
                if data.has_key('recordRevision') and data['recordRevision'] != 'sampleValue':
                    record_revision_ts = data['recordRevision']
                    record_xml = get_marcxml_of_revision(recid, \
                                                         record_revision_ts)
                    record = create_record(record_xml)[0]
                    record_revision = timestamp_to_revision(record_revision_ts)
                    pending_changes = []
                    disabled_hp_changes = {}
                else:
                    # a normal cacheless retrieval of a record
                    record = get_bibrecord(recid)
                    record_revision = get_record_last_modification_date(recid)
                    if record_revision == None:
                        record_revision = datetime.now().timetuple()
                    pending_changes = []
                    disabled_hp_changes = {}
                cache_dirty = False
                mtime = 0
                undo_list = []
                redo_list = []
            elif not existing_cache:
                record_revision, record = create_cache_file(recid, uid)
                mtime = get_cache_mtime(recid, uid)
                pending_changes = []
                disabled_hp_changes = {}
                undo_list = []
                redo_list = []
                cache_dirty = False
            else:
                #TODO: This try except should be replaced with something nicer,
                #      like an argument indicating if a new cache file is to
                #      be created
                try:
                    cache_dirty, record_revision, record, pending_changes, \
                        disabled_hp_changes, undo_list, redo_list = \
                        get_cache_file_contents(recid, uid)
                    touch_cache_file(recid, uid)
                    mtime = get_cache_mtime(recid, uid)
                    if not latest_record_revision(recid, record_revision) and \
                            get_record_revisions(recid) != ():
                        # This sould prevent from using old cache in case of
                        # viewing old version. If there are no revisions,
                        # it means we should skip this step because this
                        # is a new record
                        response['cacheOutdated'] = True

                except:
                    record_revision, record = create_cache_file(recid, uid)
                    mtime = get_cache_mtime(recid, uid)
                    pending_changes = []
                    disabled_hp_changes = {}
                    cache_dirty = False
                    undo_list = []
                    redo_list = []
            if data.get('clonedRecord',''):
                response['resultCode'] = 9
            else:
                response['resultCode'] = 3
            revision_author = get_record_revision_author(recid, record_revision)
            latest_revision = get_record_last_modification_date(recid)
            if latest_revision == None:
                latest_revision = datetime.now().timetuple()
            last_revision_ts = revision_to_timestamp(latest_revision)

            revisions_history = get_record_revision_timestamps(recid)
            number_of_physical_copies = get_number_copies(recid)
            bibcirc_details_URL = create_item_details_url(recid, ln)
            can_have_copies = can_record_have_physical_copies(recid)

            # For some collections, merge template with record
            template_to_merge = extend_record_with_template(recid)
            if template_to_merge:
                record = merge_record_with_template(record, template_to_merge)
                create_cache_file(recid, uid, record, True)
                
            response['cacheDirty'], response['record'], \
                response['cacheMTime'], response['recordRevision'], \
                response['revisionAuthor'], response['lastRevision'], \
                response['revisionsHistory'], response['inReadOnlyMode'], \
                response['pendingHpChanges'], response['disabledHpChanges'], \
                response['undoList'], response['redoList'] = cache_dirty, \
                record, mtime, revision_to_timestamp(record_revision), \
                revision_author, last_revision_ts, revisions_history, \
                read_only_mode, pending_changes, disabled_hp_changes, \
                undo_list, redo_list
            response['numberOfCopies'] = number_of_physical_copies
            response['bibCirculationUrl'] = bibcirc_details_URL
            response['canRecordHavePhysicalCopies'] = can_have_copies
            # Set tag format from user's session settings.
            try:
                tagformat_settings = session_param_get(req, 'bibedit_tagformat')
                tagformat = tagformat_settings[recid]
            except KeyError:
                tagformat = CFG_BIBEDIT_TAG_FORMAT
            response['tagFormat'] = tagformat
            # KB information
            response['KBSubject'] = CFG_BIBEDIT_KB_SUBJECTS
            response['KBInstitution'] = CFG_BIBEDIT_KB_INSTITUTIONS

    elif request_type == 'submit':
        # Submit the record. Possible error situations:
        # - Missing cache file
        # - Cache file modified in other editor
        # - Record locked by other user
        # - Record locked by queue
        # - Invalid XML characters
        # If the cache is outdated cacheOutdated will be set to True in the
        # response.
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
            try:
                tmp_result = get_cache_file_contents(recid, uid)
                record_revision = tmp_result[1]
                record = tmp_result[2]
                pending_changes = tmp_result[3]
#                disabled_changes = tmp_result[4]

                xml_record = wash_for_xml(print_rec(record))
                record, status_code, list_of_errors = create_record(xml_record)
                if status_code == 0:
                    response['resultCode'], response['errors'] = 110, \
                        list_of_errors
                elif not data['force'] and \
                        not latest_record_revision(recid, record_revision):
                    response['cacheOutdated'] = True
                    if CFG_DEVEL_SITE:
                        response['record_revision'] = record_revision.__str__()
                        response['newest_record_revision'] = \
                            get_record_last_modification_date(recid).__str__()
                else:
                    save_xml_record(recid, uid)
                    response['resultCode'] = 4
            except Exception, e:
                response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV[ \
                    'error_wrong_cache_file_format']
                if CFG_DEVEL_SITE: # return debug information in the request
                    response['exception_message'] = e.__str__()
    elif request_type == 'revert':
        revId = data['revId']
        job_date = "%s-%s-%s %s:%s:%s" % re_revdate_split.search(revId).groups()
        revision_xml = get_marcxml_of_revision(recid, job_date)
        save_xml_record(recid, uid, revision_xml)
        if (cache_exists(recid, uid)):
            delete_cache_file(recid, uid)
        response['resultCode'] = 4

    elif request_type == 'cancel':
        # Cancel editing by deleting the cache file. Possible error situations:
        # - Cache file modified in other editor
        if cache_exists(recid, uid):
            if get_cache_mtime(recid, uid) == data['cacheMTime']:
                delete_cache_file(recid, uid)
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
                record_revision, record, pending_changes, \
                    deactivated_hp_changes, undo_list, redo_list = \
                    create_cache_file(recid, uid)
            else:
                try:
                    record_revision, record, pending_changes, \
                        deactivated_hp_changes, undo_list, redo_list = \
                        get_cache_file_contents(recid, uid)[1:]
                except:
                    record_revision, record, pending_changes, \
                        deactivated_hp_changes = create_cache_file(recid, uid)
            record_add_field(record, '980', ' ', ' ', '', [('c', 'DELETED')])
            undo_list = []
            redo_list = []
            update_cache_file_contents(recid, uid, record_revision, record, \
                                       pending_changes, \
                                       deactivated_hp_changes, undo_list, \
                                       redo_list)
            save_xml_record(recid, uid)
            delete_related_holdingpen_changes(recid) # we don't need any changes
                                                   # related to a deleted record
            response['resultCode'] = 10

    elif request_type == 'deleteRecordCache':
        # Delete the cache file. Ignore the request if the cache has been
        # modified in another editor.
        if cache_exists(recid, uid) and get_cache_mtime(recid, uid) == \
                data['cacheMTime']:
            delete_cache_file(recid, uid)
        response['resultCode'] = 11

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

    return response

def perform_request_update_record(request_type, recid, uid, cacheMTime, data, \
                                  hpChanges, undoRedoOp, isBulk=False, \
                                  ln=CFG_SITE_LANG):
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
    elif not get_cache_mtime(recid, uid) == cacheMTime and isBulk == False:
        # In case of a bulk request, the changes are deliberately performed
        # immediately one after another
        response['resultCode'] = 107
    else:
        try:
            record_revision, record, pending_changes, deactivated_hp_changes, \
                undo_list, redo_list = get_cache_file_contents(recid, uid)[1:]
        except:
            response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV[ \
                'error_wrong_cache_file_format']
            return response

        # process all the Holding Pen changes operations ... regardles the
        # request type
#        import rpdb2;
#        rpdb2.start_embedded_debugger('password', fAllowRemote=True)
        if hpChanges.has_key("toDisable"):
            for changeId in hpChanges["toDisable"]:
                pending_changes[changeId]["applied_change"] = True

        if hpChanges.has_key("toEnable"):
            for changeId in hpChanges["toEnable"]:
                pending_changes[changeId]["applied_change"] = False

        if hpChanges.has_key("toOverride"):
            pending_changes = hpChanges["toOverride"]

        if hpChanges.has_key("changesetsToDeactivate"):
            for changesetId in hpChanges["changesetsToDeactivate"]:
                deactivated_hp_changes[changesetId] = True

        if hpChanges.has_key("changesetsToActivate"):
            for changesetId in hpChanges["changesetsToActivate"]:
                deactivated_hp_changes[changesetId] = False

        # processing the undo/redo entries
        if undoRedoOp == "undo":
            try:
                redo_list = [undo_list[-1]] + redo_list
                undo_list = undo_list[:-1]
            except:
                raise Exception("An exception occured when undoing previous" + \
                                " operation. Undo list: " + str(undo_list) + \
                                " Redo list " + str(redo_list))
        elif undoRedoOp == "redo":
            try:
                undo_list = undo_list + [redo_list[0]]
                redo_list = redo_list[1:]
            except:
                raise Exception("An exception occured when redoing previous" + \
                                " operation. Undo list: " + str(undo_list) + \
                                " Redo list " + str(redo_list))
        else:
            # This is a genuine operation - we have to add a new descriptor
            # to the undo list and cancel the redo unless the operation is
            # a bulk operation
            if undoRedoOp != None:
                undo_list = undo_list + [undoRedoOp]
                redo_list = []
            else:
                assert isBulk == True

        field_position_local = data.get('fieldPosition')
        if field_position_local is not None:
            field_position_local = int(field_position_local)
        if request_type == 'otherUpdateRequest':
            # An empty request. Might be useful if we want to perform
            # operations that require only the actions performed globally,
            # like modifying the holdingPen changes list
            response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV[ \
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
            response['resultCode'] = CFG_BIBEDIT_AJAX_RESULT_CODES_REV[ \
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
                        record_add_field(record, tag, field_position_local = \
                                             int(position), \
                                             controlfield_value = \
                                                 controlfieldValue)
                    else:
                        subfields = fieldsToAdd[tag][position][0]
                        ind1 = fieldsToAdd[tag][position][1]
                        ind2 = fieldsToAdd[tag][position][2]
                        record_add_field(record, tag, ind1, ind2, subfields = \
                                             subfields, field_position_local = \
                                                int(position))
            # now adding the subfields
            for tag in subfieldsToAdd.keys():
                for fieldPosition in subfieldsToAdd[tag].keys(): #now the fields
                                                          #order not important !
                    subfieldsPositions = subfieldsToAdd[tag][fieldPosition]. \
                                           keys()
                    subfieldsPositions.sort()
                    for subfieldPosition in subfieldsPositions:
                        subfield = subfieldsToAdd[tag][fieldPosition]\
                            [subfieldPosition]
                        record_add_subfield_into(record, tag, subfield[0], \
                                                 subfield[1], \
                                                 subfield_position = \
                                                     int(subfieldPosition), \
                                                 field_position_local = \
                                                     int(fieldPosition))

            response['resultCode'] = \
                CFG_BIBEDIT_AJAX_RESULT_CODES_REV['added_positioned_subfields']

        elif request_type == 'modifyField': # changing the field structure
            # first remove subfields and then add new... change the indices
            subfields = data['subFields'] # parse the JSON representation of
                                          # the subfields here

            new_field = create_field(subfields, data['ind1'], data['ind2'])
            record_replace_field(record, data['tag'], new_field, \
                field_position_local = data['fieldPosition'])
            response['resultCode'] = 26

        elif request_type == 'modifyContent':
            if data['subfieldIndex'] != None:
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

            record_delete_field(record, data['oldTag'], ind1=data['oldInd1'], \
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

        response['cacheMTime'], response['cacheDirty'] = \
            update_cache_file_contents(recid, uid, record_revision,
                                       record, \
                                       pending_changes, \
                                       deactivated_hp_changes, \
                                       undo_list, redo_list), \
            True

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
        #we check if the data is properly defined
    fulltag = ''
    if data.has_key('maintag') and data.has_key('subtag1') and \
            data.has_key('subtag2') and data.has_key('subfieldcode'):
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
        #call the keyword-form-ontology function
        if fulltag and searchby:
            items = get_kbt_items_for_bibedit(CFG_BIBEDIT_KEYWORD_TAXONOMY, \
                                              CFG_BIBEDIT_KEYWORD_RDFLABEL, \
                                              searchby)
            response['autokeyword'] = items
    if (request_type == 'autosuggest'):
        #call knowledge base function to put the suggestions in an array..
        if fulltag and searchby and len(searchby) > 3:
            #add trailing '*' wildcard for 'search_unit_in_bibxxx()' if not already present
            suggest_values = get_kbd_values_for_bibedit(fulltag, "", searchby+"*")
            #remove ..
            new_suggest_vals = []
            for sugg in suggest_values:
                if sugg.startswith(searchby):
                    new_suggest_vals.append(sugg)
            response['autosuggest'] = new_suggest_vals
    if (request_type == 'autocomplete'):
        #call the values function with the correct kb_name
        if CFG_BIBEDIT_AUTOCOMPLETE_TAGS_KBS.has_key(fulltag):
            kbname = CFG_BIBEDIT_AUTOCOMPLETE_TAGS_KBS[fulltag]
            #check if the seachby field has semicolons. Take all
            #the semicolon-separated items..
            items = []
            vals = []
            if searchby:
                if searchby.rfind(';'):
                    items = searchby.split(';')
                else:
                    items = [searchby.strip()]
            for item in items:
                item = item.strip()
                kbrvals = get_kbr_values(kbname, item, '', 'e') #we want an exact match
                if kbrvals and kbrvals[0]: #add the found val into vals
                    vals.append(kbrvals[0])
            #check that the values are not already contained in other
            #instances of this field
            record = get_cache_file_contents(recid, uid)[2]
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

def perform_request_bibcatalog(request_type, recid, uid):
    """Handle request to BibCatalog (RT).

    """
    response = {}

    if request_type == 'getTickets':
        # Insert the ticket data in the response, if possible
        if bibcatalog_system is None:
            response['tickets'] = "<!--No ticket system configured-->"
        elif bibcatalog_system and uid:
            bibcat_resp = bibcatalog_system.check_system(uid)
            if bibcat_resp == "":
                tickets_found = bibcatalog_system.ticket_search(uid, \
                    status=['new', 'open'], recordid=recid)
                t_url_str = '' #put ticket urls here, formatted for HTML display
                for t_id in tickets_found:
                    #t_url = bibcatalog_system.ticket_get_attribute(uid, \
                    #    t_id, 'url_display')
                    ticket_info = bibcatalog_system.ticket_get_info( \
                        uid, t_id, ['url_display', 'url_close'])
                    t_url = ticket_info['url_display']
                    t_close_url = ticket_info['url_close']
                    #format..
                    t_url_str += "#" + str(t_id) + '<a href="' + t_url + \
                        '">[read]</a> <a href="' + t_close_url + \
                        '">[close]</a><br/>'
                #put ticket header and tickets links in the box
                t_url_str = "<strong>Tickets</strong><br/>" + t_url_str + \
                    "<br/>" + '<a href="new_ticket?recid=' + str(recid) + \
                    '>[new ticket]</a>'
                response['tickets'] = t_url_str
                #add a new ticket link
            else:
                #put something in the tickets container, for debug
                response['tickets'] = "<!--"+bibcat_resp+"-->"
        response['resultCode'] = 31
    return response

def perform_request_preview_record(request_type, recid, uid):
    """ Handle request to preview record with formatting

    """

    response = {}
    if request_type == "preview":
        if cache_exists(recid, uid):
            dummy1, dummy2, record, dummy3, dummy4, dummy5, dummy6 = get_cache_file_contents(recid, uid)
        else:
            record = get_bibrecord(recid)
    response['html_preview'] = _get_formated_record(record)

    return response

def _get_formated_record(record):
    """Returns a record in a given format

    @param record: BibRecord object
    """

    xml_record = bibrecord.record_xml_output(record)

    result =  "<html><head><title>Record preview</title></head>"
    result += get_mathjax_header(True)
    result += "<body><h2> Brief format preview </h2>"
    result += bibformat.format_record(recID=None,
                                     of="hb",
                                     xml_record=xml_record)
    result += "<h2> Detailed format preview </h2>"

    result += bibformat.format_record(recID=None,
                                     of="hd",
                                     xml_record=xml_record)

    result += "</body></html>"


    return result

########### Functions related to templates web interface #############

def perform_request_init_template_interface():
    """Handle a request to manage templates"""
    errors   = []
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
               'json2.js', 'bibedit_display.js', 'bibedit_template_interface.js']

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
        response['resultCode']  = 1
    else:
        response['templateMARCXML'] = template

    return response
