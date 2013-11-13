## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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

"""Invenio BibMerge Engine."""

import os

from invenio.bibmerge_merger import merge_field_group, replace_field, \
                                    add_field, delete_field, merge_field, \
                                    add_subfield, replace_subfield, \
                                    delete_subfield, copy_R2_to_R1, merge_record
from invenio.search_engine import print_record, perform_request_search, \
        record_exists
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibedit_utils import cache_exists, cache_expired, \
    create_cache_file, delete_cache_file, get_cache_file_contents, \
    get_cache_mtime, latest_record_revision, record_locked_by_other_user, \
    record_locked_by_queue, save_xml_record, touch_cache_file, \
    update_cache_file_contents, _get_file_path, \
    get_record_revision_ids, revision_format_valid_p, split_revid, \
    get_marcxml_of_revision_id
from invenio.utils.html import remove_html_markup
from invenio.legacy.bibrecord import create_record, record_xml_output, record_add_field, \
                              record_order_subfields
from invenio.bibedit_config import CFG_BIBEDIT_TO_MERGE_SUFFIX

import invenio.template
bibmerge_templates = invenio.template.load('bibmerge')

def perform_request_init():
    """Handle the initial request.
    """
    errors   = []
    warnings = []
    body = ''

    # Build page structure and control panel.
    body += bibmerge_templates.controlpanel()
    body += """
    <div id="bibMergeContent">
    </div>"""

    return body, errors, warnings

def perform_request_ajax(req, uid, data):
    """Ajax request dispatcher.\
    """
    requestType = data['requestType']

    if requestType in ('getRecordCompare', 'submit', 'cancel', 'recCopy', \
           'recMerge', 'recMergeNC'):
        return perform_request_record(requestType, uid, data)

    elif requestType in ('getFieldGroup', 'getFieldGroupDiff', \
           'mergeFieldGroup', 'mergeNCFieldGroup', 'replaceField', 'addField', \
           'deleteField', 'mergeField'):
        return perform_request_update_record(requestType, uid, data)

    elif requestType in ('deleteSubfield', 'addSubfield', 'replaceSubfield',  \
           'diffSubfield'):
        return perform_small_request_update_record(requestType, uid, data)

    elif requestType == "searchCandidates" or requestType == "searchRevisions":
        return perform_candidate_record_search(requestType, data)

    else:
        return { 'resultCode': 1, 'resultText': 'Error unknown' }

def perform_candidate_record_search(requestType, data):
    """Handle search requests.
    """
    max_results = 999
    too_many = False
    result = {
        'resultCode': 0,
        'resultText': ''
        }
    if requestType == "searchCandidates":
        recids = perform_request_search( p=data['query'] )
        if len(recids) > max_results:
            too_many = True
        else:
            captions = [ search_result_info(x) for x in recids ]
            alternative_titles = [ remove_html_markup(print_record(x, "hs")) for x in recids ]
            search_results = [recids, captions, alternative_titles]
    elif requestType == "searchRevisions":
        revisions = get_record_revision_ids( data['recID1'] )
        captions = [ split_revid(x, 'datetext')[1] for x in revisions ]
        search_results = [revisions, captions]

    if too_many == True:
        result['resultCode'] = 1
        result['resultText'] = 'Too many results'
    else:
        result['results'] = search_results
        result['resultText'] = '%s results' % len(search_results[0])

    return result

def search_result_info(recid):
    """Return report number of a record or if it doen't exist return the recid
    itself.
    """
    report_numbers = get_fieldvalues(recid, '037__a')
    if len(report_numbers) == 0:
        return "#"+str(recid)
    else:
        return report_numbers[0]

def perform_request_record(requestType, uid, data):
    """Handle 'major' record related requests.
    Handle retrieving, submitting or cancelling the merging session.
    """
    #TODO add checks before submission and cancel, replace get_bibrecord call
    result = {
        'resultCode': 0,
        'resultText': ''
        }
    recid1 = data["recID1"]
    record1 = _get_record(recid1, uid, result)
    if result['resultCode'] != 0: #if record not accessible return error information
        return result

    if requestType == 'submit':
        if data.has_key('duplicate'):
            recid2 = data['duplicate']
            record2 = _get_record_slave(recid2, result, 'recid', uid)
            if result['resultCode'] != 0: #return in case of error
                return result
            # mark record2 as deleted
            record_add_field(record2, '980', ' ', ' ', '', [('c', 'DELETED')])
            # mark record2 as duplicate of record1
            record_add_field(record2, '970', ' ', ' ', '', [('d', str(recid1))])

            # submit record2 to be deleted
            xml_record2 = record_xml_output(record2)
            save_xml_record(recid2, uid, xml_record2)

            #submit record1
            xml_record1 = record_xml_output(record1)
            save_xml_record(recid1, uid, xml_record1)

            result['resultText'] = 'Records submitted'
            return result

        #submit record1 from cache
        save_xml_record(recid1, uid)

        # Delete cache file if it exists
        if cache_exists(recid1, uid):
            delete_cache_file(recid1, uid)

        result['resultText'] = 'Record submitted'
        return result

    elif requestType == 'cancel':
        delete_cache_file(recid1, uid)
        result['resultText'] = 'Cancelled'
        return result

    recid2 = data["recID2"]
    mode = data['record2Mode']
    record2 = _get_record_slave(recid2, result, mode, uid)
    if result['resultCode'] != 0: #if record not accessible return error information
        return result

    if requestType == 'getRecordCompare':
        result['resultHtml'] = bibmerge_templates.BM_html_all_diff(record1, record2)
        result['resultText'] = 'Records compared'

    elif requestType == 'recCopy':
        copy_R2_to_R1(record1, record2)
        result['resultHtml'] = bibmerge_templates.BM_html_all_diff(record1, record2)
        result['resultText'] = 'Record copied'

    elif requestType == 'recMerge':
        merge_record(record1, record2, merge_conflicting_fields=True)
        result['resultHtml'] = bibmerge_templates.BM_html_all_diff(record1, record2)
        result['resultText'] = 'Records merged'

    elif requestType == 'recMergeNC':
        merge_record(record1, record2, merge_conflicting_fields=False)
        result['resultHtml'] = bibmerge_templates.BM_html_all_diff(record1, record2)
        result['resultText'] = 'Records merged'

    else:
        result['resultCode'], result['resultText'] = 1, 'Wrong request type'

    return result

def perform_request_update_record(requestType, uid, data):
    """Handle record update requests for actions on a field level.
    Handle merging, adding, or replacing of fields.
    """
    result = {
        'resultCode': 0,
        'resultText': ''
        }
    recid1 = data["recID1"]
    recid2 = data["recID2"]
    record_content = get_cache_file_contents(recid1, uid)
    cache_dirty = record_content[0]
    rec_revision = record_content[1]
    record1 = record_content[2]
    pending_changes = record_content[3]
    disabled_hp_changes = record_content[4]
    # We will not be able to Undo/Redo correctly after any modifications
    # from the level of bibmerge are performed ! We clear all the undo/redo
    # lists
    undo_list = []
    redo_list = []

    mode = data['record2Mode']
    record2 = _get_record_slave(recid2, result, mode, uid)
    if result['resultCode'] != 0: #if record not accessible return error information
        return result

    if requestType == 'getFieldGroup':
        result['resultHtml'] = bibmerge_templates.BM_html_field_group(record1, record2, data['fieldTag'])
        result['resultText'] = 'Field group retrieved'
        return result
    elif requestType == 'getFieldGroupDiff':
        result['resultHtml'] = bibmerge_templates.BM_html_field_group(record1, record2, data['fieldTag'], True)
        result['resultText'] = 'Fields compared'
        return result
    elif requestType == 'mergeFieldGroup' or requestType == 'mergeNCFieldGroup':
        fnum, ind1, ind2 = _fieldtagNum_and_indicators(data['fieldTag'])
        if requestType == 'mergeNCFieldGroup':
            merge_field_group(record1, record2, fnum, ind1, ind2, False)
        else:
            merge_field_group(record1, record2, fnum, ind1, ind2, True)
        resultText = 'Field group merged'

    elif requestType == 'replaceField' or requestType == 'addField':
        fnum, ind1, ind2 = _fieldtagNum_and_indicators(data['fieldTag'])
        findex1 = _field_info( data['fieldCode1'] )[1]
        findex2 = _field_info( data['fieldCode2'] )[1]
        if findex2 == None:
            result['resultCode'], result['resultText'] = 1, 'No value in the selected field'
            return result
        if requestType == 'replaceField':
            replace_field(record1, record2, fnum, findex1, findex2)
            resultText = 'Field replaced'
        else: # requestType == 'addField'
            add_field(record1, record2, fnum, findex1, findex2)
            resultText = 'Field added'

    elif requestType == 'deleteField':
        fnum, ind1, ind2 = _fieldtagNum_and_indicators(data['fieldTag'])
        findex1 = _field_info( data['fieldCode1'] )[1]
        if findex1 == None:
            result['resultCode'], result['resultText'] = 1, 'No value in the selected field'
            return result
        delete_field(record1, fnum, findex1)
        resultText = 'Field deleted'

    elif requestType == 'mergeField':
        fnum, ind1, ind2 = _fieldtagNum_and_indicators(data['fieldTag'])
        findex1 = _field_info( data['fieldCode1'] )[1]
        findex2 = _field_info( data['fieldCode2'] )[1]
        if findex2 == None:
            result['resultCode'], result['resultText'] = 1, 'No value in the selected field'
            return result
        merge_field(record1, record2, fnum, findex1, findex2)
        resultText = 'Field merged'

    else:
        result['resultCode'], result['resultText'] = 1, 'Wrong request type'
        return result

    result['resultHtml'] = bibmerge_templates.BM_html_field_group(record1, record2, data['fieldTag'])
    result['resultText'] = resultText
    update_cache_file_contents(recid1, uid, rec_revision, record1, pending_changes, disabled_hp_changes, undo_list, redo_list)
    return result

def perform_small_request_update_record(requestType, uid, data):
    """Handle record update requests for actions on a subfield level.
    Handle adding, replacing or deleting of subfields.
    """
    result = {
        'resultCode': 0,
        'resultText': '',
        'resultHtml': ''
        }
    recid1 = data["recID1"]
    recid2 = data["recID2"]
    cache_content = get_cache_file_contents(recid1, uid) #TODO: check mtime, existence
    cache_dirty = cache_content[0]
    rec_revision = cache_content[1]
    record1 = cache_content[2]
    pending_changes = cache_content[3]
    disabled_hp_changes = cache_content[4]

    mode = data['record2Mode']
    record2 = _get_record_slave(recid2, result, mode, uid)
    if result['resultCode'] != 0: #if record not accessible return error information
        return result

    ftag, findex1 = _field_info(data['fieldCode1'])
    fnum = ftag[:3]
    findex2 = _field_info(data['fieldCode2'])[1]
    sfindex1 = data['sfindex1']
    sfindex2 = data['sfindex2']

    if requestType == 'deleteSubfield':
        delete_subfield(record1, fnum, findex1, sfindex1)
        result['resultText'] = 'Subfield deleted'
    elif requestType == 'addSubfield':
        add_subfield(record1, record2, fnum, findex1, findex2, sfindex1, sfindex2)
        result['resultText'] = 'Subfield added'
    elif requestType == 'replaceSubfield':
        replace_subfield(record1, record2, fnum, findex1, findex2, sfindex1, sfindex2)
        result['resultText'] = 'Subfield replaced'
    elif requestType == 'diffSubfield':
        result['resultHtml'] = bibmerge_templates.BM_html_subfield_row_diffed(record1, record2, fnum, findex1, findex2, sfindex1, sfindex2)
        result['resultText'] = 'Subfields diffed'

    update_cache_file_contents(recid1, uid, rec_revision, record1, pending_changes, disabled_hp_changes, [], [])
    return result

def _get_record(recid, uid, result, fresh_record=False):
    """Retrieve record structure.
    """
    record = None
    mtime = None
    cache_dirty = None
    record_status = record_exists(recid)
    existing_cache = cache_exists(recid, uid)
    if record_status == 0:
        result['resultCode'], result['resultText'] = 1, 'Non-existent record: %s' % recid
    elif record_status == -1:
        result['resultCode'], result['resultText'] = 1, 'Deleted record: %s' % recid
    elif not existing_cache and record_locked_by_other_user(recid, uid):
        result['resultCode'], result['resultText'] = 1, 'Record %s locked by user' % recid
    elif existing_cache and cache_expired(recid, uid) and \
        record_locked_by_other_user(recid, uid):
        result['resultCode'], result['resultText'] = 1, 'Record %s locked by user' % recid
    elif record_locked_by_queue(recid):
        result['resultCode'], result['resultText'] = 1, 'Record %s locked by queue' % recid
    else:
        if fresh_record:
            delete_cache_file(recid, uid)
            existing_cache = False
        if not existing_cache:
            record_revision, record = create_cache_file(recid, uid)
            mtime = get_cache_mtime(recid, uid)
            cache_dirty = False
        else:
            tmpRes = get_cache_file_contents(recid, uid)
            cache_dirty, record_revision, record = tmpRes[0], tmpRes[1], tmpRes[2]
            touch_cache_file(recid, uid)
            mtime = get_cache_mtime(recid, uid)
            if not latest_record_revision(recid, record_revision):
                result['cacheOutdated'] = True
        result['resultCode'], result['resultText'], result['cacheDirty'], result['cacheMTime'] = 0, 'Record OK', cache_dirty, mtime
    return record

def _get_record_slave(recid, result, mode=None, uid=None):
    """Check if record exists and return it in dictionary format.
       If any kind of error occurs returns None.
       If mode=='revision' then recid parameter is considered as revid."""
    record = None
    if recid == 'none':
        mode = 'none'
    if mode == 'recid':
        record_status = record_exists(recid)
        #check for errors
        if record_status == 0:
            result['resultCode'], result['resultText'] = 1, 'Non-existent record: %s' % recid
        elif record_status == -1:
            result['resultCode'], result['resultText'] = 1, 'Deleted record: %s' % recid
        elif record_locked_by_queue(recid):
            result['resultCode'], result['resultText'] = 1, 'Record %s locked by queue' % recid
        else:
            record = create_record( print_record(recid, 'xm') )[0]
            record_order_subfields(record)

    elif mode == 'tmpfile':
        file_path = '%s_%s.xml' % (_get_file_path(recid, uid),
                                       CFG_BIBEDIT_TO_MERGE_SUFFIX)
        if not os.path.isfile(file_path): #check if file doesn't exist
            result['resultCode'], result['resultText'] = 1, 'Temporary file doesnt exist'
        else: #open file
            tmpfile = open(file_path, 'r')
            record = create_record( tmpfile.read() )[0]
            tmpfile.close()

    elif mode == 'revision':
        if revision_format_valid_p(recid):
            marcxml = get_marcxml_of_revision_id(recid)
            if marcxml:
                record = create_record(marcxml)[0]
            else:
                result['resultCode'], result['resultText'] = 1, 'The specified revision does not exist'
        else:
            result['resultCode'], result['resultText'] = 1, 'Invalid revision id'

    elif mode == 'none':
        return {}

    else:
        result['resultCode'], result['resultText'] = 1, 'Invalid record mode for record2'
    return record

def _field_info(fieldIdCode):
    """Returns a tuple: (field-tag, field-index)
        eg.: _field_info('R1-8560_-2') --> ('8560_', 2) """
    info = fieldIdCode.split('-')
    if info[2] == 'None':
        info[2] = None
    else:
        info[2] = int(info[2])
    return tuple( info[1:] )

def _fieldtagNum_and_indicators(fieldTag):
    """Separate a 5-char field tag to a 3-character field-tag number and two
    indicators"""
    fnum, ind1, ind2 = fieldTag[:3], fieldTag[3], fieldTag[4]
    if ind1 == '_':
        ind1 = ' '
    if ind2 == '_':
        ind2 = ' '
    return (fnum, ind1, ind2)

