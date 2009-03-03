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

import os

from invenio.bibedit_dblayer import get_name_tags_all
from invenio.bibedit_utils import get_file_path, get_record, \
    record_locked_p, save_temp_record, save_xml_record
from invenio.bibrecord import record_add_field, record_add_subfield_into, \
    record_modify_controlfield, record_modify_subfield, record_move_subfield, \
    record_delete_subfield_from, record_delete_field_from
from invenio.config import CFG_BIBEDIT_PROTECTED_FIELDS, CFG_CERN_SITE, \
    CFG_SITE_URL
from invenio.search_engine import record_exists
from invenio.webuser import session_param_get, session_param_set

import invenio.template
bibedit_templates = invenio.template.load('bibedit')

def perform_request_init():
    """Handle the initial request.

    Add menu and Javascript to the page.

    """
    errors   = []
    warnings = []
    body = ''

    # Add script data.
    tag_names = get_name_tags_all()
    protected_fields = ['001']
    protected_fields.extend(CFG_BIBEDIT_PROTECTED_FIELDS.split(','))
    history_url = '"' + CFG_SITE_URL + '/admin/bibedit/bibeditadmin.py/history"'
    cern_site = 'false'
    if CFG_CERN_SITE:
        cern_site = 'true'
    data = {'gTagNames': tag_names,
            'gProtectedFields': protected_fields,
            'gSiteURL': '"' + CFG_SITE_URL + '"',
            'gHistoryURL': history_url,
            'gCERNSite': cern_site}
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

def perform_request_user(req, requestType, recid,  data):
    """Handle user related requests."""
    result = {
        'resultCode': 0,
        'resultText': ''
        }

    if requestType == 'changeTagFormat':
        try:
            tagformat_settings = session_param_get(req, 'bibedit_tagformat')
        except KeyError:
            tagformat_settings = {}
        tagformat_settings[recid] = data['tagFormat']
        session_param_set(req, 'bibedit_tagformat', tagformat_settings)
        result['resultText'] = 'Format changed'

    return result

def perform_request_record(req, requestType, recid, uid):
    """Handle 'major' record related requests.

    Handle retrieving, submitting or deleting the record or cancelling the
    editing session.

    """
    result = {
        'resultCode': 0,
        'resultText': ''
        }

    if requestType == 'getRecord':
        record_status = record_exists(recid)
        if record_status == 0:
            result['resultCode'], result['resultText'] = 1, \
            'Error: Non-existent record'
        elif record_status == -1:
            result['resultCode'], result['resultText'] = 1, 'Error: Deleted ' \
                'record'
        else:
            record = get_record(recid, uid)
            if not record:
                result['resultCode'], result['resultText'] = 1, 'Error: ' \
                    'Locked record - by user'
            elif record_locked_p(recid):
                result['resultCode'], result['resultText'] = 1, 'Error: ' \
                    'Locked record - by queue'
                os.system("rm %s.tmp" % get_file_path(recid))
            else:
                result['record'], result['resultText'] = record, 'Record loaded'
                try:
                    tagformat_settings = session_param_get(req,
                                                           'bibedit_tagformat')
                    tagformat = tagformat_settings[recid]
                except KeyError:
                    tagformat = 'MARC'
                result['tagFormat'] = tagformat

    elif requestType == 'submit':
        save_xml_record(recid)
        result['resultText'] = 'Record submitted'

    elif requestType == 'cancel':
        os.system("rm -f %s.tmp" % get_file_path(recid))
        result['resultText'] = 'Cancelled'

    elif requestType == 'deleteRecord':
        record = get_record(recid, uid)
        record_add_field(record, '980', ' ', ' ', '', [('c', 'DELETED')])
        save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))
        save_xml_record(recid)
        result['resultText'] = 'Record deleted'

    return result

def perform_request_update_record(requestType, recid, uid, data):
    """Handle record update requests.

    Handle adding, modifying, moving or deleting of fields or subfields.

    """
    result = {
        'resultCode': 0,
        'resultText': ''
        }
    record = get_record(recid, uid)

    if requestType == 'addField':
        if data['controlfield']:
            record_add_field(record, data['tag'],
                             controlfield_value=data['value'])
            result['resultText'] = 'Added controlfield'
        else:
            field_number = record_add_field(record, data['tag'], data['ind1'],
                                            data['ind2'])
            for subfield in data['subfields']:
                record_add_subfield_into(record, data['tag'], field_number,
                                         subfield[0], subfield[1])
            result['resultText'] = 'Added field'

    elif requestType == 'addSubfields':
        subfields = data['subfields']
        for subfield in subfields:
            record_add_subfield_into(record, data['tag'],
                int(data['fieldNumber']), subfield[0], subfield[1], None)
        if len(subfields) == 1:
            resultText = 'Added subfield'
        else:
            resultText = 'Added subfields'
        result['resultText'] = resultText

    elif requestType == 'modifyContent':
        if data['subfieldIndex'] != None:
            record_modify_subfield(record, data['tag'],
                int(data['fieldNumber']), data['subfieldCode'], data['value'],
                int(data['subfieldIndex']))
        else:
            record_modify_controlfield(record, data['tag'],
                int(data['fieldNumber']), data['value'])
        result['resultText'] = 'Content modified'

    elif requestType == 'moveSubfield':
        record_move_subfield(record, data['tag'], int(data['fieldNumber']),
            int(data['subfieldIndex']), int(data['newSubfieldIndex']))
        result['resultText'] = 'Subfield moved'

    elif requestType == 'deleteFields':
        to_delete = data['toDelete']
        deleted_fields = 0
        deleted_subfields = 0
        for tag in to_delete:
            for field_number in to_delete[tag]:
                if not to_delete[tag][field_number]:
                    # No subfields specified - delete entire field.
                    record_delete_field_from(record, tag, int(field_number))
                    deleted_fields += 1
                else:
                    for subfield_index in to_delete[tag][field_number][::-1]:
                        # Delete subfields in reverse order (to keep the
                        # indexing correct).
                        record_delete_subfield_from(record, tag,
                            int(field_number), int(subfield_index))
                        deleted_subfields += 1
        if deleted_fields == 1 and deleted_subfields == 0:
            result['resultText'] = 'Field deleted'
        elif deleted_fields and deleted_subfields == 0:
            result['resultText'] = 'Fields deleted'
        elif deleted_subfields == 1 and deleted_fields == 0:
            result['resultText'] = 'Subfield deleted'
        elif deleted_subfields and deleted_fields == 0:
            result['resultText'] = 'Subfields deleted'
        else:
            result['resultText'] = 'Selection deleted'

    save_temp_record(record, uid, "%s.tmp" % get_file_path(recid))

    return result
