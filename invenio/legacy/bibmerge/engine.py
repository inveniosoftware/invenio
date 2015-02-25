# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014, 2015 CERN.
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

# pylint: disable=C0103

"""Invenio BibMerge Engine."""

import os
import random
import re

from invenio.config import \
     CFG_BIBUPLOAD_INTERNAL_DOI_PATTERN, \
     CFG_BIBEDIT_INTERNAL_DOI_PROTECTION_LEVEL, CFG_SITE_RECORD
from invenio.legacy.bibmerge.merger import merge_field_group, replace_field, \
                                    add_field, delete_field, merge_field, \
                                    add_subfield, replace_subfield, \
                                    delete_subfield, copy_R2_to_R1, merge_record
from invenio.legacy.search_engine import print_record, perform_request_search, \
        record_exists
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.bibedit.utils import cache_exists, cache_expired, \
    create_cache, delete_cache, get_cache_contents, \
    get_cache_mtime, latest_record_revision, record_locked_by_other_user, \
    record_locked_by_queue, save_xml_record, touch_cache, \
    update_cache_contents, _get_file_path, \
    get_record_revision_ids, revision_format_valid_p, split_revid, \
    get_marcxml_of_revision_id
from invenio.utils.html import remove_html_markup
from invenio.legacy.bibrecord import create_record, record_xml_output, record_add_field, \
                              record_order_subfields, \
                              record_extract_dois

from invenio.base.globals import cfg

import invenio.legacy.template
bibmerge_templates = invenio.legacy.template.load('bibmerge')

def perform_request_init():
    """Handle the initial request.
    """
    errors   = []
    warnings = []
    body = ''

    # Add script data.

    data = {'gSITE_RECORD': '"' + CFG_SITE_RECORD + '"'}

    body += '<script type="text/javascript">\n'
    for key in data:
        body += '    var %s = %s;\n' % (key, data[key])
    body += '    </script>\n'

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
        if 'duplicate' in data:
            recid2 = data['duplicate']
            record2 = _get_record_slave(recid2, result, 'recid', uid)
            if result['resultCode'] != 0: #return in case of error
                return result
            (errcode, message) = check_doi_status_after_merge(data["recID1"], data['duplicate'],
                                                              record1, record2,
                                                              record2_marked_as_duplicate_p=data.has_key('duplicate'),
                                                              submit_confirmed_p=data.get('additional_data', {'confirmed_submit': False}).get('confirmed_submit', False))
            if errcode:
                result['resultCode'] = errcode
                result['resultText'] = message
                return result

            # mark record2 as deleted
            record_add_field(record2, '980', ' ', ' ', '', [('c', 'DELETED')])
            # mark record2 as duplicate of record1
            record_add_field(record2, '970', ' ', ' ', '', [('d', str(recid1))])
            # add recid of deleted record to master record
            record_add_field(record1, '981', ' ', ' ', '', [('a', str(recid2))])

            # To ensure updates happen in order, use a seq id
            sequence_id = str(random.randrange(1, 4294967296))

            # submit record2 to be deleted
            xml_record2 = record_xml_output(record2)
            save_xml_record(recid2, uid, xml_record2, task_name="bibmerge",
                            sequence_id=sequence_id)

            # submit record1
            xml_record1 = record_xml_output(record1)
            save_xml_record(recid1, uid, xml_record1, task_name="bibmerge",
                            sequence_id=sequence_id)

            # Delete cache file if it exists
            if cache_exists(recid1, uid):
                delete_cache(recid1, uid)

            result['resultText'] = 'Records submitted'
            return result

        (errcode, message) = check_doi_status_after_merge(data["recID1"], data["recID2"],
                                                          record1, None,
                                                          submit_confirmed_p=data.get('additional_data', {'confirmed_submit': False}).get('confirmed_submit', False))
        if errcode:
            result['resultCode'] = errcode
            result['resultText'] = message
            return result

        #submit record1 from cache
        save_xml_record(recid1, uid, task_name="bibmerge")

        # Delete cache file if it exists
        if cache_exists(recid1, uid):
            delete_cache(recid1, uid)

        result['resultText'] = 'Record submitted'
        return result

    elif requestType == 'cancel':
        delete_cache(recid1, uid)
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
    record_content = get_cache_contents(recid1, uid)
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
    update_cache_contents(recid1, uid, rec_revision, record1, pending_changes, disabled_hp_changes, undo_list, redo_list)
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
    cache_content = get_cache_contents(recid1, uid) #TODO: check mtime, existence
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

    update_cache_contents(recid1, uid, rec_revision, record1, pending_changes, disabled_hp_changes, [], [])
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
            delete_cache(recid, uid)
            existing_cache = False
        if not existing_cache:
            record_revision, record = create_cache(recid, uid)
            mtime = get_cache_mtime(recid, uid)
            cache_dirty = False
        else:
            tmpRes = get_cache_contents(recid, uid)
            cache_dirty, record_revision, record = tmpRes[0], tmpRes[1], tmpRes[2]
            touch_cache(recid, uid)
            mtime = get_cache_mtime(recid, uid)
            if not latest_record_revision(recid, record_revision):
                result['cacheOutdated'] = True
        result['resultCode'], result['resultText'], result['cacheDirty'], result['cacheMTime'] = 0, 'Record OK', cache_dirty, mtime
    record_order_subfields(record)
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

    elif mode == 'tmpfile':
        file_path = '%s_%s.xml' % (_get_file_path(recid, uid),
                                       cfg['CFG_BIBEDIT_TO_MERGE_SUFFIX'])
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
    record_order_subfields(record)
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

def get_dois(record, internal_only_p=False):
    """
    Return the list of DOIs in the given record. If C{internal_only_p}
    is set to True, only those DOIs that are considered owned/managed
    by this installation (as defined in
    CFG_BIBUPLOAD_INTERNAL_DOI_PATTERN) will be returned.

    @param record: the record we want to get DOIs from
    @type record: BibRecord object
    @param internal_only_p: if True, returns only DOIs managed/owned by the system
    @type internal_only_p: bool
    @rtype: list(string)
    """
    return [doi for doi in record_extract_dois(record) if \
            not internal_only_p or re.compile(CFG_BIBUPLOAD_INTERNAL_DOI_PATTERN).match(doi)]

def check_doi_status_after_merge(original_recid1, original_recid2, final_record1, final_record_2, record2_marked_as_duplicate_p=False, submit_confirmed_p=False):
    """
    Check that the result of the merge does not removed DOIs managed
    by the system, and that not duplicate DOI would be
    created. Returns a tuple(error_code, message).

    @param original_recid1: the record ID of the original record 1 (master)
    @type original_recid1: int
    @param original_recid2: the record ID of the original record 2 (slave)
    @type original_recid2: int
    @param final_record1: the resulting merged record
    @type final_record1: BibRecord object
    @param final_record_2: the resulting slave "merged" record (optional when record2_marked_as_duplicate_p is False)
    @type final_record_2: BibRecord object
    @param record2_marked_as_duplicate_p: True if the record 2 will be marked as duplicate (and deleted)
    @type record2_marked_as_duplicate_p: bool
    @param submit_confirmed_p: if the user has already confirmed to proceed with submission, according to previous messages displayed. If True, do not ask again confirmation and proceed if all tests pass.
    @type submit_confirmed_p: bool
    """
    errcode = 0
    message = ''
    new_record1_dois = get_dois(final_record1)
    new_record1_managed_dois = get_dois(final_record1, internal_only_p=True)
    original_record1_managed_dois = get_dois(create_record(print_record(original_recid1, 'xm'))[0],
                                             internal_only_p=True)
    original_record2_dois = get_dois(create_record(print_record(original_recid2, 'xm'))[0])

    # Are there any DOI from record 1 (master) lost in the merging?
    lost_dois_in_record1 = [doi for doi in original_record1_managed_dois \
                            if not doi in new_record1_managed_dois]

    # Enough to check for duplicate DOI creation in this record,
    # not whole DB
    duplicate_dois_after_merge = [doi for doi in new_record1_dois if new_record1_dois.count(doi) > 1]

    if record2_marked_as_duplicate_p:
        new_record2_managed_dois = get_dois(final_record_2, internal_only_p=True)
        original_record2_managed_dois = get_dois(create_record(print_record(original_recid2, 'xm'))[0],
                                                 internal_only_p=True)
        # Are there any DOI from record 2 (slave) lost in the merging?
        lost_dois_in_record2 = [doi for doi in original_record2_managed_dois \
                                    if not doi in new_record1_managed_dois]
    else:
        lost_dois_in_record2 = []
        duplicate_dois_after_merge += [doi for doi in new_record1_dois if doi in original_record2_dois]

    if ((lost_dois_in_record1 or lost_dois_in_record2) and \
        CFG_BIBEDIT_INTERNAL_DOI_PROTECTION_LEVEL > 0) or \
        duplicate_dois_after_merge:

        if CFG_BIBEDIT_INTERNAL_DOI_PROTECTION_LEVEL == 1 and \
               not duplicate_dois_after_merge and \
               not submit_confirmed_p:
            errcode = 1
            message = 'The resulting merged record misses DOI(s) managed by the system.<script type="text/javascript">%(check_duplicate_box)sif (confirm(\'The resulting merged record will lose DOI(s) managed by the system.\\n' + \
                      'The following DOI(s) were in the original record (#1) but are not in the final merged one:\\n' + '\\n'.join(lost_dois_in_record1) + \
                      '\\nAre you sure that you want to submit the merged records without the DOI(s)?\')) {onclickSubmitButton(confirm_p=false, additional_data={\'confirmed_submit\': true})}</script>'
        elif duplicate_dois_after_merge and lost_dois_in_record1:
            errcode = 1
            message = 'The changes cannot be submitted because the resulting merged record (a) misses DOI(s) managed by the system and/or (b) will create duplicate DOIs.<script type="text/javascript">%(check_duplicate_box)salert(\'The changes cannot be submitted because the resulting merged record (a) misses DOI(s) managed by the system and (b) will create duplicate DOIs.\\n' + \
                      'The following DOI(s) were in the original record (#1) but are not in the final merged one:\\n' + '\\n'.join(lost_dois_in_record1) + \
                      '\\nThe following DOI(s) would be duplicate after merge:\\n' + '\\n'.join(duplicate_dois_after_merge) + \
                      '\\nMake sure that the mentionned DOI(s) are included in the final merged record and/or no duplicate DOIs are created (suggestion: merge in the other way around).\');</script>'
        elif duplicate_dois_after_merge:
            errcode = 1
            message = 'The changes cannot be submitted because the resulting merged record will create a duplicate DOI.<script type="text/javascript">%(check_duplicate_box)salert(\'The changes cannot be submitted because the resulting merged record will create a duplicate DOI.\\n' + \
                      'The following DOI(s) would be duplicate after merge:\\n' + '\\n'.join(duplicate_dois_after_merge) + \
                      '\\nMake sure that the mentionned DOI(s) are not duplicated (suggestion: merge in the other way around).\');</script>'
        elif not (CFG_BIBEDIT_INTERNAL_DOI_PROTECTION_LEVEL == 1 and submit_confirmed_p):
            # lost DOIs after merge
            errcode = 1
            message = 'The changes cannot be submitted because the resulting merged record misses DOI(s) managed by the system.<script type="text/javascript">%(check_duplicate_box)salert(\'The changes cannot be submitted because the resulting merged record misses the DOI(s) managed by the system.\\n' + \
                      'The following DOI(s) were in the original record (#1) but are not in the final merged one:\\n' + '\\n'.join(lost_dois_in_record1) + \
                          '\\nMake sure that the mentionned DOI(s) are included in the final merged record.\');</script>'

    message = message % {'check_duplicate_box': record2_marked_as_duplicate_p and '$(\'#bibMergeDupeCheckbox\').attr(\'checked\', true);' or ''}

    return (errcode, message)
