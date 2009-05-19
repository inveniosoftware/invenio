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
                                    add_field, delete_field, merge_field
from invenio.search_engine import print_record, perform_request_search
from invenio.bibedit_utils import get_file_path, get_record, \
    record_locked_p, save_temp_record, save_xml_record
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
    result = {
        'resultCode': 0,
        'resultText': ''
        }

    if requestType == 'getRecordCompare':
        record1, result = _check_record_availability(recid1, uid, result)
        if result['resultCode'] != 0:
            return result
        record2, result = _check_record_availability(recid2, uid, result)
        if result['resultCode'] != 0:
            return result
        result['resultHtml'] = bibmerge_templates.BM_html_all_diff(record1, record2)
        result['resultText'] = 'Records compared'

    elif requestType == 'submit':
        save_xml_record(recid1)
        result['resultText'] = 'Record submitted'

    elif requestType == 'cancel':
        os.system("rm -f %s.tmp" % get_file_path(recid1))
        result['resultText'] = 'Cancelled'
    else:
        result['resultCode'], result['resultText'] = 1, 'Wrong request type'

    return result

def _check_record_availability(recid, uid, result):
    record = None
    result = {}
    record_status = record_exists(recid)
    if record_status == 0:
        result['resultCode'], result['resultText'] = 1, \
        'Error: Non-existent record: %s' % recid
    elif record_status == -1:
        result['resultCode'], result['resultText'] = 1, 'Error: Deleted ' \
            'record: ' % recid
    else:
        record = get_record(recid, uid)
        if not record:
            result['resultCode'], result['resultText'] = 1, 'Error: ' \
                'Locked record: %s - by user' % recid
        elif record_locked_p(recid):
            result['resultCode'], result['resultText'] = 1, 'Error: ' \
                'Locked record: %s - by queue' % recid
            os.system("rm %s.tmp" % get_file_path(recid))
        else:
            result['resultCode'], result['resultText'] = 0, 'Record OK'
    return record, result

def perform_request_update_record(requestType, recid1, recid2, uid, data):
    """Handle record update requests.
    Handle merging, adding, or replacing of fields or subfields.
    """
    result = {
        'resultCode': 0,
        'resultText': ''
        }
    record1 = get_record(recid1, uid)
    record2 = get_record(recid2, uid)

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

    save_temp_record(record1, uid, "%s.tmp" % get_file_path(recid1))
    return result

def _field_info(fieldIdCode):
    """Returns a tuple: (field-tag, field-index, subfield-code, subfield-index)
        eg.: _field_info('R1-8560_-2-f-None') --> ('8560_', 2, 'f', None) """
    info = fieldIdCode.split('-')
    if info[2] == 'None':
        info[2] = None
    else:
        info[2] = int(info[2])
    if info[4] == 'None':
        info[4] = None
    else:
        info[4] = int(info[4])
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

