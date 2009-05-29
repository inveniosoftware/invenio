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

"""CDS Invenio BibMerge Engine."""

import os

from invenio.config import CFG_SITE_URL
from invenio.bibmerge_merger import merge_field_group, replace_field, \
                                    add_field, delete_field, merge_field, \
                                    add_subfield, replace_subfield, \
                                    delete_subfield
from invenio.search_engine import print_record, perform_request_search
from invenio.bibedit_utils import cache_exists, cache_expired, \
    create_cache_file, delete_cache_file, get_cache_file_contents, \
    get_cache_mtime, latest_record_revision, record_locked_by_other_user, \
    record_locked_by_queue, save_xml_record, touch_cache_file, \
    update_cache_file_contents, get_bibrecord
from invenio.search_engine import record_exists, search_pattern
from invenio.bibrecord import create_record

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

def perform_record_compare(recid1, recid2):
    """First comparison of two records."""
    rec1 = create_record(print_record(recid1, 'xm'))[0]
    rec2 = create_record(print_record(recid2, 'xm'))[0]
    return bibmerge_templates.BM_html_all_diff(rec1, rec2)

def perform_candidate_record_search(query):
    """Handle search requests."""
    search_results = perform_request_search( p=query )
    max_results = 1000
    htmlresults = ""
    if len(search_results) <= max_results:
        for recid in search_results:
            htmlresults += "\n<option>%s</option>" % recid

    return { "results": htmlresults,
             "resultsLen": len(search_results),
             "resultsMaxLen": max_results }

def perform_request_record(req, requestType, recid1, recid2, uid):
    """Handle 'major' record related requests.
    Handle retrieving, submitting or cancelling the merging session.
    """
    #TODO add checks before submission and cancel, replace get_bibrecord call
    result = {
        'resultCode': 0,
        'resultText': ''
        }

    if requestType == 'getRecordCompare':
        record1, result = get_record(recid1, uid, result)
        if result['resultCode'] != 0:
            return result
        record2 = get_bibrecord(recid2)
        if result['resultCode'] != 0:
            return result
        result['resultHtml'] = bibmerge_templates.BM_html_all_diff(record1, record2)
        result['resultText'] = 'Records compared'

    elif requestType == 'submit':
        save_xml_record(recid1, uid)
        result['resultText'] = 'Record submitted'

    elif requestType == 'cancel':
        delete_cache_file(recid1, uid)
        result['resultText'] = 'Cancelled'
    else:
        result['resultCode'], result['resultText'] = 1, 'Wrong request type'

    return result

def get_record(recid, uid, result, fresh_record=False):
    record = {}
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
            cache_dirty, record_revision, record = \
                 get_cache_file_contents(recid, uid)
            touch_cache_file(recid, uid)
            mtime = get_cache_mtime(recid, uid)
            if not latest_record_revision(recid, record_revision):
                result['cacheOutdated'] = True
        result['resultCode'], result['resultText'], result['cacheDirty'], result['cacheMTime'] = 0, 'Record OK', cache_dirty, mtime
    return record, result

def perform_request_update_record(requestType, recid1, recid2, uid, data):
    """Handle record update requests for actions on a field level.
    Handle merging, adding, or replacing of fields.
    """
    result = {
        'resultCode': 0,
        'resultText': ''
        }
    cache_dirty, rec_revision, record1 = get_cache_file_contents(recid1, uid) #TODO: check mtime, existence
    record2 = get_bibrecord(recid2) #TODO: replace with get_slave_rec

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

    update_cache_file_contents(recid1, uid, rec_revision, record1)
    return result

def perform_small_request_update_record(requestType, data, uid):
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
    cache_dirty, rec_revision, record1 = get_cache_file_contents(recid1, uid) #TODO: check mtime, existence
    record2 = get_bibrecord(recid2) #TODO: replace with get_slave_rec

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

    update_cache_file_contents(recid1, uid, rec_revision, record1)
    return result


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

