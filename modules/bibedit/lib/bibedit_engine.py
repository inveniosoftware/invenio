## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

# pylint: disable-msg=C0103
"""CDS Invenio BibEdit Engine."""

__revision__ = "$Id"

from invenio.bibedit_config import CFG_BIBEDIT_JS_HASH_CHECK_INTERVAL, \
    CFG_BIBEDIT_JS_CHECK_SCROLL_INTERVAL, CFG_BIBEDIT_JS_STATUS_ERROR_TIME, \
    CFG_BIBEDIT_JS_STATUS_INFO_TIME, CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR, \
    CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR_FADE_DURATION, \
    CFG_BIBEDIT_JS_NEW_FIELDS_COLOR, \
    CFG_BIBEDIT_JS_NEW_FIELDS_COLOR_FADE_DURATION, \
    CFG_BIBEDIT_AJAX_RESULT_CODES, CFG_BIBEDIT_MAX_SEARCH_RESULTS, \
    CFG_BIBEDIT_TAG_FORMAT
from invenio.bibedit_dblayer import get_name_tags_all, reserve_record_id
from invenio.bibedit_utils import cache_exists, cache_expired, \
    create_cache_file, delete_cache_file, get_bibrecord, \
    get_cache_file_contents, get_cache_mtime, get_record_templates, \
    get_record_template, latest_record_revision, record_locked_by_other_user, \
    record_locked_by_queue, save_xml_record, touch_cache_file, \
    update_cache_file_contents
from invenio.bibrecord import create_record, record_add_field, \
    record_add_subfield_into, record_delete_field, \
    record_delete_subfield_from, record_modify_controlfield, \
    record_modify_subfield, record_move_subfield
from invenio.config import CFG_BIBEDIT_PROTECTED_FIELDS, CFG_CERN_SITE, \
    CFG_SITE_URL
from invenio.search_engine import record_exists, search_pattern
from invenio.webuser import session_param_get, session_param_set
from invenio.bibcatalog import bibcatalog_system

import invenio.template

bibedit_templates = invenio.template.load('bibedit')

def perform_request_init():
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
    if CFG_CERN_SITE:
        cern_site = 'true'
    data = {'gRECORD_TEMPLATES': record_templates,
            'gTagNames': tag_names,
            'gProtectedFields': protected_fields,
            'gSiteURL': '"' + CFG_SITE_URL + '"',
            'gHistoryURL': history_url,
            'gCERNSite': cern_site,
            'gHASH_CHECK_INTERVAL': CFG_BIBEDIT_JS_HASH_CHECK_INTERVAL,
            'gCHECK_SCROLL_INTERVAL': CFG_BIBEDIT_JS_CHECK_SCROLL_INTERVAL,
            'gSTATUS_ERROR_TIME': CFG_BIBEDIT_JS_STATUS_ERROR_TIME,
            'gSTATUS_INFO_TIME': CFG_BIBEDIT_JS_STATUS_INFO_TIME,
            'gNEW_ADD_FIELD_FORM_COLOR':
                '"' + CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR + '"',
            'gNEW_ADD_FIELD_FORM_COLOR_FADE_DURATION':
                CFG_BIBEDIT_JS_NEW_ADD_FIELD_FORM_COLOR_FADE_DURATION,
            'gNEW_FIELDS_COLOR': '"' + CFG_BIBEDIT_JS_NEW_FIELDS_COLOR + '"',
            'gNEW_FIELDS_COLOR_FADE_DURATION':
                CFG_BIBEDIT_JS_NEW_FIELDS_COLOR_FADE_DURATION,
            'gRESULT_CODES': CFG_BIBEDIT_AJAX_RESULT_CODES,
            }
    body += '<script type="text/javascript">\n'
    for key in data:
        body += '    var %s = %s;\n' % (key, data[key])
    body += '    </script>\n'

    # Add scripts (the ordering is NOT irrelevant).
    scripts = ['jquery.min.js', 'effects.core.min.js',
               'effects.highlight.min.js', 'jquery.autogrow.js',
               'jquery.jeditable.mini.js', 'jquery.hotkeys.min.js', 'json2.js',
               'bibedit_display.js', 'bibedit_engine.js', 'bibedit_keys.js',
               'bibedit_menu.js']

    for script in scripts:
        body += '    <script type="text/javascript" src="%s/js/%s">' \
            '</script>\n' % (CFG_SITE_URL, script)

    # Build page structure and menu.
    body += bibedit_templates.menu()
    body += '    <div id="bibEditContent"></div>\n'

    return body, errors, warnings

def perform_request_ajax(req, recid, uid, data):
    """Handle Ajax requests by redirecting to appropriate function."""
    response = {}
    request_type = data['requestType']

    # Call function based on request type.
    if request_type == 'searchForRecord':
        # Search request.
        response.update(perform_request_search(data))
    elif request_type in ['changeTagFormat']:
        # User related requests.
        response.update(perform_request_user(req, request_type, recid, data))
    elif request_type in ('getRecord', 'submit', 'cancel', 'newRecord',
        'deleteRecord', 'deleteRecordCache', 'prepareRecordMerge'):
        # 'Major' record related requests.
        response.update(perform_request_record(req, request_type, recid, uid,
                                               data))
    else:
        # Record updates.
        response.update(perform_request_update_record(
                request_type, recid, uid, data))

    return response

def perform_request_search(data):
    """Handle search requests."""
    response = {}
    searchType = data['searchType']
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

def perform_request_record(req, request_type, recid, uid, data):
    """Handle 'major' record related requests like fetching, submitting or
    deleting a record, cancel editing or preparing a record for merging.

    """
    response = {}

    if request_type == 'newRecord':
        # Create a new record.
        recid = reserve_record_id()
        new_type = data['newType']
        if new_type == 'empty':
            # Create a new empty record.
            create_cache_file(recid, uid)
            response['resultCode'], response['recID'] = 6, recid

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
                                     controlfield_value=str(recid))
                    create_cache_file(recid, uid, record)
                    response['resultCode'], response['recID']  = 7, recid

        elif new_type == 'clone':
            # Clone an existing record (from the users cache).
            recid_to_clone = data['recIDToClone']
            existing_cache = cache_exists(recid_to_clone, uid)
            if not existing_cache:
                record = get_bibrecord(recid_to_clone)
            else:
                # Cache missing. Fall back to using original version.
                record = get_cache_file_contents(recid_to_clone, uid)[2]
            record_delete_field(record, '001')
            record_add_field(record, '001', controlfield_value=str(recid))
            create_cache_file(recid, uid, record)
            response['resultCode'], response['recID'] = 8, recid

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
        if record_status == 0:
            response['resultCode'] = 102
        elif record_status == -1:
            response['resultCode'] = 103
        elif not existing_cache and record_locked_by_other_user(recid, uid):
            response['resultCode'] = 104
        elif existing_cache and cache_expired(recid, uid) and \
                record_locked_by_other_user(recid, uid):
            response['resultCode'] = 104
        elif record_locked_by_queue(recid):
            response['resultCode'] = 105
        else:
            if data.get('deleteRecordCache'):
                delete_cache_file(recid, uid)
                existing_cache = False
            if not existing_cache:
                record_revision, record = create_cache_file(recid, uid)
                mtime = get_cache_mtime(recid, uid)
                cache_dirty = False
            else:
                cache_dirty, record_revision, record = \
                    get_cache_file_contents(recid, uid)
                touch_cache_file(recid, uid)
                mtime = get_cache_mtime(recid, uid)
                if not latest_record_revision(recid, record_revision):
                    response['cacheOutdated'] = True
            response['resultCode'], response['cacheDirty'], \
                response['record'], response['cacheMTime'] = 3, cache_dirty, \
                record, mtime
            # Insert the ticket data in the response, if possible
            if uid:
                bibcat_resp = bibcatalog_system.check_system(uid)
                if bibcat_resp == "":
                    tickets_found = bibcatalog_system.ticket_search(uid, recordid=recid)
                    t_url_str = '' #put ticket urls here, formatted for HTML display
                    for t_id in tickets_found:
                        #t_url = bibcatalog_system.ticket_get_attribute(uid, t_id, 'url_display')
                        ticket_info = bibcatalog_system.ticket_get_info(uid, t_id, ['url_display','url_close'])
                        t_url = ticket_info['url_display']
                        t_close_url = ticket_info['url_close']
                        #format..
                        t_url_str += "#"+str(t_id)+'<a href="'+t_url+'" target="_blank">[read]</a> <a href="'+t_close_url+'" target="_blank">[close]</a><br/>'
                    #put ticket header and tickets links in the box
                    t_url_str = "<strong>Tickets</strong><br/>"+t_url_str+"<br/>"+'<a href="new_ticket?recid='+str(recid)+'" target="_blank">[new ticket]<a>'
                    response['tickets'] = t_url_str
                    #add a new ticket link
                else:
                    #put something in the tickets container, for debug
                    response['tickets'] = "<!--"+bibcat_resp+"-->"
            # Set tag format from user's session settings.
            try:
                tagformat_settings = session_param_get(req, 'bibedit_tagformat')
                tagformat = tagformat_settings[recid]
            except KeyError:
                tagformat = CFG_BIBEDIT_TAG_FORMAT
            response['tagFormat'] = tagformat

    elif request_type == 'submit':
        # Submit the record. Possible error situations:
        # - Missing cache file
        # - Cache file modified in other editor
        # - Record locked by other user
        # - Record locked by queue
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
            record_revision, record = get_cache_file_contents(recid, uid)[1:]
            if not data['force'] and \
                    not latest_record_revision(recid, record_revision):
                response['cacheOutdated'] = True
            else:
                save_xml_record(recid, uid)
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
        if existing_cache and cache_expired(recid, uid) and \
                record_locked_by_other_user(recid, uid):
            response['resultCode'] = 104
        elif record_locked_by_queue(recid):
            response['resultCode'] = 105
        else:
            if not existing_cache:
                record_revision, record = create_cache_file(recid, uid)
            else:
                record_revision, record = get_cache_file_contents(
                    recid, uid)[1:]
            record_add_field(record, '980', ' ', ' ', '', [('c', 'DELETED')])
            update_cache_file_contents(recid, uid, record_revision, record)
            save_xml_record(recid, uid)
            response['resultCode'] = 9

    elif request_type == 'deleteRecordCache':
        # Delete the cache file. Ignore the request if the cache has been
        # modified in another editor.
        if cache_exists(recid, uid) and get_cache_mtime(recid, uid) == \
                data['cacheMTime']:
            delete_cache_file(recid, uid)
        response['resultCode'] = 10

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
            response['resultCode'] = 11

    return response

def perform_request_update_record(request_type, recid, uid, data):
    """Handle record update requests like adding, modifying, moving or deleting
    of fields or subfields. Possible common error situations:
    - Missing cache file
    - Cache file modified in other editor

    """
    response = {}

    if not cache_exists(recid, uid):
        response['resultCode'] = 106
    elif not get_cache_mtime(recid, uid) == data['cacheMTime']:
        response['resultCode'] = 107
    else:
        record_revision, record = get_cache_file_contents(recid, uid)[1:]

        # FIXME: Get BibRecord updated so that this conversion isn't necessary
        field_position = data.get('fieldPosition')
        if field_position:
            field_position_local = int(field_position)
            field_position_global = \
                record[data['tag']][int(field_position_local)][4]

        if request_type == 'addField':
            if data['controlfield']:
                record_add_field(record, data['tag'],
                                 controlfield_value=data['value'])
                response['resultCode'] = 20
            else:
                record_add_field(record, data['tag'], data['ind1'],
                                 data['ind2'], subfields=data['subfields'],
                                 field_position_local=data['fieldPosition'])
                response['resultCode'] = 21

        elif request_type == 'addSubfields':
            subfields = data['subfields']
            for subfield in subfields:
                record_add_subfield_into(record, data['tag'],
                    field_position_global, subfield[0], subfield[1], None)
            if len(subfields) == 1:
                response['resultCode'] = 22
            else:
                response['resultCode'] = 23

        elif request_type == 'modifyContent':
            if data['subfieldIndex'] != None:
                record_modify_subfield(record, data['tag'],
                    field_position_global, data['subfieldCode'],
                    data['value'], int(data['subfieldIndex']))
            else:
                record_modify_controlfield(record, data['tag'],
                    field_position_global, data['value'])
            response['resultCode'] = 24

        elif request_type == 'moveSubfield':
            record_move_subfield(record, data['tag'], field_position_global,
                int(data['subfieldIndex']), int(data['newSubfieldIndex']))
            response['resultCode'] = 25

        elif request_type == 'deleteFields':
            to_delete = data['toDelete']
            deleted_fields = 0
            deleted_subfields = 0
            for tag in to_delete:
                for field_position_local in to_delete[tag]:
                    field_position_global = \
                        record[tag][int(field_position_local)][4]
                    if not to_delete[tag][field_position_local]:
                        # No subfields specified - delete entire field.
                        record_delete_field(record, tag,
                            field_position_global=field_position_global)
                        deleted_fields += 1
                    else:
                        for subfield_index in \
                                to_delete[tag][field_position_local][::-1]:
                            # Delete subfields in reverse order (to keep the
                            # indexing correct).
                            record_delete_subfield_from(record, tag,
                                field_position_global, int(subfield_index))
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
            update_cache_file_contents(recid, uid, record_revision, record), \
            True

    return response

def perform_request_newticket(recid, uid):
    """create a new ticket with this record's number
       @param recid: record id
       @param uid: user id
       @return: (error_msg, url)
    """
    t_id = bibcatalog_system.ticket_submit(uid, "", recid, "")
    t_url = ""
    errmsg = ""
    if t_id:
        #get the ticket's URL
        t_url = bibcatalog_system.ticket_get_attribute(uid, t_id, 'url_modify')
    else:
        errmsg = "ticket_submit failed"
    return (errmsg, t_url)
