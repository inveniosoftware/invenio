# This file is part of Invenio.
# Copyright (C) 2010, 2011 CERN.
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

'''
BibSWORD Client for WebSubmit
'''

__revision__ = "$Id$"

    ##
    ## Name:           Export_With_Sword
    ## Description:    function Export_With_Sword
    ##                 This function submit the given record to the remote SWORD
    ##                 server specified in parameters. The user can specify the
    ##                 the remote collection and the categories where he wants
    ##                 to put the record.
    ##
    ## Author:         M. Barras
    ##
    ## PARAMETERS:   - the database id of the remote server (in swrREMOTESERVER)
    ##               - the id of the record to export
    ##               - the remote collection url
    ##               - the remote primary category url
    ##               - the list remote secondary categories url (optionnal)
    ##               - the marcxml (optionnal, only if it has been modified)
    ##               - the file list (optionnal, list of fulltext to export)
    ## OUTPUT: HTML
    ##

import os
import re
from invenio.legacy.bibsword.client import list_collections_from_server, \
                                    list_mandated_categories, \
                                    list_optional_categories, \
                                    get_marcxml_from_record, \
                                    get_media_list, \
                                    perform_submission_process
from invenio.legacy.bibsword.client_templates import BibSwordTemplate
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionStop


def Export_Via_SWORD(parameters, curdir, form, user_info=None):
    '''
        This function get informations about the SWORD remote server where to
        export the given record.
        If a marcxml file is given in parameters, it use it as metadata source.
        If no marcxml file is given, it get the marcxml file using the given
        recid.
        If a list of file is given in parameters, it export those file. If not,
        it get fulltext files from the URL found in the marcxml file
    '''

    global sysno, rn

    metadata = {'id_record': rn}

    #---------------------------------------------------------------------------
    #  get remote server id
    #---------------------------------------------------------------------------

    #Path of file containing remote server id
    if os.path.exists("%s/%s" % (curdir, parameters['serverid'])):
        tmp_file = open("%s/%s" % (curdir, parameters['serverid']),"r")
        serverid = tmp_file.read()
        serverid = re.sub("[\n\r ]+", "", serverid)
    else:
        return 'Collection not found !'


    #---------------------------------------------------------------------------
    #  get collection's url and id
    #---------------------------------------------------------------------------

    #Path of file containing primary category url
    if os.path.exists("%s/%s" % (curdir, parameters['collection'])):
        tmp_file = open("%s/%s" % (curdir, parameters['collection']),"r")
        col = tmp_file.read()
        col = re.sub("[\n\r ]+", "", col)
    else:
        return 'Collection not found !'

    selected_collection = {}

    collections = list_collections_from_server(serverid)

    for collection in collections :
        if col == collection['url'] :
            selected_collection = collection

    #---------------------------------------------------------------------------
    #  get selected primary category url and label
    #---------------------------------------------------------------------------

    #Path of file containing primary category url
    if os.path.exists("%s/%s" % (curdir, parameters['primary'])):
        tmp_file = open("%s/%s" % (curdir, parameters['primary']),"r")
        pc_from_param = tmp_file.read()
        pc_from_param = re.sub("[\n\r ]+", "", pc_from_param)
    else:
        return 'Primary category not found !'

    primary_categories = \
        list_mandated_categories(str(serverid), selected_collection['id'])

    for primary_category in primary_categories :
        if pc_from_param == primary_category['url'] :
            metadata['primary_url'] = primary_category['url']
            metadata['primary_label'] = primary_category['label']


    #---------------------------------------------------------------------------
    #  get selected secondary categories url and label (if any)
    #---------------------------------------------------------------------------

    metadata['categories'] = []

    #Path of file containing primary category url
    if os.path.exists("%s/%s" % (curdir, parameters['secondary'])):
        tmp_file = open("%s/%s" % (curdir, parameters['secondary']), "r")
        sc_from_param = tmp_file.read()
        sc_from_param = re.sub("\+", "\n", sc_from_param)
        list_sc_from_param = sc_from_param.split('\n')

        secondary_categories = \
            list_optional_categories(str(serverid), selected_collection['id'])


        for secondary_category in secondary_categories :
            for sc_element in list_sc_from_param :
                if sc_element == secondary_category['url'] :
                    secondary = {}
                    secondary['url'] = secondary_category['url']
                    secondary['label'] = secondary_category['label']
                    metadata['categories'].append(secondary)


    #---------------------------------------------------------------------------
    #  get the marcxml file
    #---------------------------------------------------------------------------

    #if os.path.exists("%s/%s" % (curdir, parameters['marcxml'])):
    #    tmp_file = open("%s/%s" % (curdir, parameters['marcxml']),"r")
    #    marcxml = tmp_file.read()

    #else :
    marcxml = get_marcxml_from_record(sysno)

    #---------------------------------------------------------------------------
    #  get the media file
    #---------------------------------------------------------------------------

    media_paths = []

    if os.path.exists("%s/%s" % (curdir, 'media')):
        tmp_file = open("%s/%s" % (curdir, 'media'), "r")
        path_medias_from_file = tmp_file.read()
        path_medias_list = re.sub("\+", "\n", path_medias_from_file)
        media_paths = path_medias_from_file.split("\n")

    if os.path.exists("%s/%s" % (curdir, 'DEMOSWR_UPLOAD')):
        tmp_file = open("%s/%s" % (curdir, 'DEMOSWR_UPLOAD'), "r")
        uploaded_file = tmp_file.read()
        path_uploaded_media = re.sub("\+", "\n", uploaded_file)
        media_paths.append("%s/files/DEMOSWR_UPLOAD/%s" % (curdir, path_uploaded_media.split('\n')[0]))

    temp_file = open('/tmp/result.txt', 'w')
    for media_path in media_paths :
        temp_file.write(media_path)

    #---------------------------------------------------------------------------
    #  format user infos
    #---------------------------------------------------------------------------

    user = {}
    user['id'] = user_info['uid']
    user['nickname'] = user_info['nickname']
    user['email'] = user_info['email']

    result = perform_submission_process(serverid, selected_collection['url'],
                                        sysno, user, metadata, media_paths,
                                        marcxml)

    if result['error'] == '' :
        bibsword_templates = BibSwordTemplate()
        return bibsword_templates.tmpl_display_submit_ack(result['remote_id'],
                                                          result['links'])
    else :
        raise InvenioWebSubmitFunctionStop("""
<SCRIPT>
    document.forms[0].action="/submit";
    document.forms[0].curpage.value = 1;
    document.forms[0].step.value = 2;
    user_must_confirm_before_leaving_page = false;
    document.forms[0].submit();
    alert('%s');
</SCRIPT>""" % result['error'])

    return ""
