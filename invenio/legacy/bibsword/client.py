# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2015 CERN.
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

from __future__ import print_function

'''
BibSWORD Client Engine
'''
import getopt
import sys
import datetime
import time
from tempfile import NamedTemporaryFile
from invenio.legacy.bibsword.config import CFG_SUBMISSION_STATUS_SUBMITTED, \
                                    CFG_SUBMISSION_STATUS_REMOVED, \
                                    CFG_SUBMISSION_STATUS_PUBLISHED, \
                                    CFG_BIBSWORD_SERVICEDOCUMENT_UPDATE_TIME
from invenio.legacy.bibsword.client_http import RemoteSwordServer
from invenio.legacy.bibsword.client_formatter import format_remote_server_infos, \
                                              format_remote_collection, \
                                              format_collection_informations, \
                                              format_primary_categories, \
                                              format_secondary_categories, \
                                              get_media_from_recid, \
                                              get_medias_to_submit, \
                                              format_file_to_zip_archiv, \
                                              format_marcxml_file, \
                                              format_link_from_result, \
                                              get_report_number_from_macrxml, \
                                              format_links_from_submission, \
                                              format_id_from_submission, \
                                              update_marcxml_with_remote_id, \
                                              ArXivFormat, \
                                              format_submission_status, \
                                              format_author_from_marcxml, \
                                              upload_fulltext, \
                                              update_marcxml_with_info
from invenio.legacy.bibsword.client_dblayer import get_all_remote_server, \
                                            get_last_update, \
                                            update_servicedocument, \
                                            select_servicedocument, \
                                            get_remote_server_auth, \
                                            is_record_sent_to_server, \
                                            select_submitted_record_infos, \
                                            update_submission_status, \
                                            insert_into_swr_clientdata, \
                                            count_nb_submitted_record, \
                                            select_remote_server_infos
from invenio.legacy.bibsword.client_templates import BibSwordTemplate
from invenio.config import CFG_TMPDIR, CFG_SITE_ADMIN_EMAIL

#-------------------------------------------------------------------------------
# Implementation of the BibSword API
#-------------------------------------------------------------------------------

def list_remote_servers(id_server=''):
    '''
        Get the list of remote servers implemented by the Invenio SWORD API.
        @return: list of tuples [ { 'id', 'name' } ]
    '''

    return get_all_remote_server(id_server)


def list_server_info(id_server):
    '''
        Get all informations about the server's options such as SWORD version,
        maxUploadSize, ... These informations are found in the servicedocument of
        the given server.
        @param id_server: #id of the server in the table swrREMOTESERVER
        @return: tuple { 'version', 'maxUploadSize', 'verbose', 'noOp' }
    '''

    service = get_servicedocument(id_server)
    return format_remote_server_infos(service)


def list_collections_from_server(id_server):
    '''
        List all the collections found in the servicedocument of the given server.
        @param id_server: #id of the server in the table swrRMOTESERVER
        @return: list of information's tuples [ { 'id', 'label', 'url' } ]
    '''

    service = get_servicedocument(id_server)
    if service == '':
        return ''
    return format_remote_collection(service)


def list_collection_informations(id_server, id_collection):
    '''
        List all information concerning the collection such as the list of
        accepted type of media, if the collection allows mediation, if the
        collection accept packaging, ...
        @param id_server: #id of the server in the table swrRMOTESERVER
        @param id_collection: id of the collection found in collection listing
        @return: information's tuple: {[accept], 'collectionPolicy', 'mediation',
                                                  'treatment', 'acceptPackaging'}
    '''

    service = get_servicedocument(id_server)
    if service == '':
        return ''
    return format_collection_informations(service, id_collection)


def list_mandated_categories(id_server, id_collection):
    '''
        The mandated categories are the categories that must be specified to the
        remote server's collection.
        In some SWORD implementation, they are not used but in some they do.
        @param id_server: #id of the server in the table swrRMOTESERVER
        @param id_collection: id of the collection found by listing them
        @return: list of category's tuples [ { 'id', 'label', 'url' } ]
    '''

    service = get_servicedocument(id_server)
    if service == '':
        return ''
    return format_primary_categories(service, id_collection)


def list_optional_categories(id_server, id_collection):
    '''
        The optional categories are only used as search option to retrieve the
        resource.
        @param id_server: #id of the server in the table swrRMOTESERVER
        @param id_collection: id of the collection found by listing them
        @return: list of category's tuples [ { 'id', 'label', 'url' } ]
    '''

    service = get_servicedocument(id_server)
    if service == '':
        return ''
    return format_secondary_categories(service, id_collection)


def list_submitted_resources(first_row, offset, action="submitted"):
    '''
        List the swrCLIENTDATA table informations such as submitter, date of submission,
        link to the resource and status of the submission.
        It is possible to limit the amount of result by specifing a remote server,
        the id of the bibRecord or both
        @return: list of submission's tuple [ { 'id', 'links', 'type, 'submiter',
                                                              'date', 'status'} ]
    '''

    #get all submission from the database
    if action == 'submitted':
        submissions = select_submitted_record_infos(first_row, offset)
    else:
        nb_submission = count_nb_submitted_record()
        submissions = select_submitted_record_infos(0, nb_submission)

    authentication_info = get_remote_server_auth(1)
    connection = RemoteSwordServer(authentication_info)

    #retrieve the status of all submission and update it if necessary
    for submission in submissions:
        if action == 'submitted' and submission['status'] != \
            CFG_SUBMISSION_STATUS_SUBMITTED:
            continue
        status_xml = connection.get_submission_status(submission['link_status'])
        if status_xml != '':
            status = format_submission_status(status_xml)
            if status['status'] != submission['status']:
                update_submission_status(submission['id'],
                                         status['status'],
                                         status['id_submission'])

                if status['status'] == CFG_SUBMISSION_STATUS_PUBLISHED:
                    update_marcxml_with_remote_id(submission['id_record'],
                                                  submission['id_remote'])
                if status['status'] == CFG_SUBMISSION_STATUS_REMOVED:
                    update_marcxml_with_remote_id(submission['id_record'],
                                                  submission['id_remote'],
                                                  "delete")
                    update_marcxml_with_info(submission['id_record'],
                                             submission['user_name'],
                                             submission['submission_date'],
                                             submission['id_remote'], "delete")

    return select_submitted_record_infos(first_row, offset)


def get_marcxml_from_record(recid):
    '''
        Return a string containing the metadata in the format of a marcxml file.
        The marcxml is retreived by using the given record id.
        @param recid: id of the record to be retreive on the database
        @return: string containing the marcxml file of the record
    '''
    from invenio.modules.record.api import get_record
    return get_record(recid).legacy_export_as_marc()


def get_media_list(recid, selected_medias=None):
    '''
        Parse the marcxml file to retrieve the link toward the media. Get every
        media through its URL and set each of them and their type in a list of
        tuple.
        @param recid: recid of the record to consider
        @return: list of tuples: [ { 'link', 'type', 'file' } ]
    '''

    if selected_medias == None:
        selected_medias = []

    medias = get_media_from_recid(recid)

    for media in medias:
        for selected_media in selected_medias:
            if selected_media == media['path']:
                media['selected'] = 'checked="yes"'
                selected_medias.remove(selected_media)
                break


    for selected_media in selected_medias:

        media = {}
        media['path'] = selected_media
        media['file'] = open(selected_media, 'r').read()
        media['size'] = str(len(media['file']))

        if selected_media.endswith('pdf'):
            media['type'] = 'application/pdf'
        elif selected_media.endswith('zip'):
            media['type'] = 'application/zip'
        elif selected_media.endswith('tar'):
            media['type'] = 'application/tar'
        elif selected_media.endswith('docx'):
            media['type'] = 'application/docx'
        elif selected_media.endswith('pdf'):
            media['type'] = 'application/pdf'
        else:
            media['type'] = ''

        media['loaded'] = True
        media['selected'] = 'checked="yes"'
        medias.append(media)

    return medias


def compress_media_file(media_file_list):
    '''
        Compress each file of the given list in a single zipped archive and return
        this archive in a new media file list containing only one tuple.
        @param media_file_list: list of tuple [ { 'type', 'file' } ]
        @return: list containing only one tuple { 'type=zip', 'file=archive' }
    '''

    filelist = []



    return format_file_to_zip_archiv(filelist)


def deposit_media(server_id, media, deposit_url, username='',
                  email=''):
    '''
        Deposit all media containing in the given list in the deposit_url (usually
        the url of the selected collection. A user name and password could be
        selected if the submission is made 'on behalf of' an author
        @param server_id: id of the remote server to deposit media
        @param media: list of tuple [ { 'type', 'file' } ]
        @param deposit_url: url of the deposition on the internet
        @param username: name of the user depositing 'on behalf of' an author
        @param email: allow user to get an acknowledgement of the deposit
        @return: list of xml result file (could'd be sword error xml file)
    '''

    response = {'result': [], 'error': ''}

    authentication_info = get_remote_server_auth(server_id)

    if authentication_info['error'] != '':
        return authentication_info['error']

    connection = RemoteSwordServer(authentication_info)
    if username != '' and email != '':
        onbehalf = '''"%s" <%s>''' % (username, email)
    else:
        onbehalf = ''

    result = connection.deposit_media(media, deposit_url, onbehalf)

    return result


def format_metadata(marcxml, deposit_result, user_info, metadata=None):
    '''
        Format an xml atom entry containing the metadata for the submission and
        the list of url where the media have been deposited.
        @param deposit_result: list of obtained response during deposition
        @param marcxml: marc file where to find metadata
        @param metadata: optionaly give other metadata that those from marcxml
        @return: xml atom entry containing foramtted metadata and links
    '''

    if metadata == None:
        metadata = {}

    # retrive all metadata from marcxml file
    metadata_from_marcxml = format_marcxml_file(marcxml)
    metadata['error'] = []


    #---------------------------------------------------------------------------
    # get the author name and email of the document (mandatory)
    #---------------------------------------------------------------------------

    if 'author_name' not in metadata:
        if 'nickname' not in user_info:
            metadata['error'].append("No submitter name given !")
            metadata['author_name'] = ''
        elif user_info['nickname'] == '':
            metadata['error'].append("No submitter name given !")
        else:
            metadata['author_name'] = user_info['nickname']

    if 'author_email' not in metadata:
        if 'email' not in user_info:
            metadata['error'].append("No submitter email given !")
            metadata['author_email'] = ''
        elif user_info['email'] == '':
            metadata['error'].append("No submitter email given !")
        else:
            metadata['author_email'] = user_info['email']


    #---------------------------------------------------------------------------
    # get url and label of the primary category of the document (mandatory)
    #---------------------------------------------------------------------------

    if 'primary_label' not in metadata:
        metadata['error'].append('No primary category label given !')
        metadata['primary_label'] = ''
    elif metadata['primary_label'] == '':
        metadata['error'].append('No primary category label given !')

    if 'primary_url' not in metadata:
        metadata['error'].append('No primary category url given !')
        metadata['primary_url'] = ''
    elif metadata['primary_url'] == '':
        metadata['error'].append('No primary category url given !')


    #---------------------------------------------------------------------------
    # get the link to the deposited fulltext of the document (mandatory)
    #---------------------------------------------------------------------------

    if deposit_result in ([], ''):
        metadata['error'].append('No links to the media deposit found !')
        metadata['links'] = []
    else:
        metadata['links'] = format_link_from_result(deposit_result)


    #---------------------------------------------------------------------------
    # get the id of the document (mandatory)
    #---------------------------------------------------------------------------

    if 'id' not in metadata:
        if 'id' not in metadata_from_marcxml:
            metadata['error'].append("No document id given !")
            metadata['id'] = ''
        elif metadata_from_marcxml['id'] == '':
            metadata['error'].append("No document id given !")
            metadata['id'] = ''
        else:
            metadata['id'] = metadata_from_marcxml['id']
    elif metadata['id'] == '':
        metadata['error'].append("No document id given !")


    #---------------------------------------------------------------------------
    # get the title of the document (mandatory)
    #---------------------------------------------------------------------------

    if 'title' not in metadata:
        if 'title' not in metadata_from_marcxml or \
               not metadata_from_marcxml['title']:
            metadata['error'].append("No title given !")
            metadata['title'] = ''
        else:
            metadata['title'] = metadata_from_marcxml['title']
    elif metadata['title'] == '':
        metadata['error'].append("No title given !")


    #---------------------------------------------------------------------------
    # get the contributors of the document (mandatory)
    #---------------------------------------------------------------------------

    contributors = []
    if 'contributors' not in metadata:
        if 'contributors' not in metadata_from_marcxml:
            metadata['error'].append('No author given !')
        elif metadata_from_marcxml['contributors'] == '':
            metadata['error'].append('No author given !')
        elif len(metadata_from_marcxml['contributors']) == 0:
            metadata['error'].append('No author given !')

        else:
            for contributor in metadata_from_marcxml['contributors']:
                if contributor != '':
                    contributors.append(contributor)
            if len(contributors) == 0:
                metadata['error'].append('No author given !')

        metadata['contributors'] = contributors


    #---------------------------------------------------------------------------
    # get the summary of the document (mandatory)
    #---------------------------------------------------------------------------

    if 'summary' not in metadata:
        if 'summary' not in metadata and \
               not metadata_from_marcxml['summary']:
            metadata['error'].append('No summary given !')
            metadata['summary'] = ""
        else:
            metadata['summary'] = metadata_from_marcxml['summary']
    else:
        if metadata['summary'] == '':
            metadata['error'].append(
                    'No summary given !')


    #---------------------------------------------------------------------------
    # get the url and the label of the categories for the document (mandatory)
    #---------------------------------------------------------------------------

    if 'categories' not in metadata:
        metadata['categories'] = []


    #---------------------------------------------------------------------------
    # get the report number of the document (optional)
    #---------------------------------------------------------------------------

    if 'report_nos' not in metadata:
        metadata['report_nos'] = []
        if 'report_nos' in metadata_from_marcxml:
            for report_no in metadata_from_marcxml['report_nos']:
                if report_no != '':
                    metadata['report_nos'].append(report_no)

    if metadata.get('id_record') == '' and len(metadata['report_nos']) > 0:
        metadata['id_record'] = metadata['report_nos'][0]


    #---------------------------------------------------------------------------
    # get the journal references of the document (optional)
    #---------------------------------------------------------------------------

    if 'journal_refs' not in metadata:
        metadata['journal_refs'] = []
        if 'journal_refs' in metadata_from_marcxml:
            for journal_ref in metadata_from_marcxml['journal_refs']:
                if journal_ref != '':
                    metadata['journal_refs'].append(journal_ref)


    #---------------------------------------------------------------------------
    # get the doi of the document (optional)
    #---------------------------------------------------------------------------

    if 'doi' not in metadata:
        if 'doi' not in metadata_from_marcxml:
            metadata['doi'] = ""
        else:
            metadata['doi'] = metadata_from_marcxml['doi']


    #---------------------------------------------------------------------------
    # get the comment of the document (optional)
    #---------------------------------------------------------------------------

    if 'comment' not in metadata:
        if 'comment' not in metadata_from_marcxml:
            metadata['comment'] = ""
        else:
            metadata['comment'] = metadata_from_marcxml['comment']

    return metadata


def submit_metadata(server_id, deposit_url, metadata, username= '', email=''):
    '''
        Submit the given metadata xml entry to the deposit_url. A username and
        an email address maight be used to proced on behalf of the real author
        of the document
        @param metadata: xml atom entry containing every metadata and links
        @param deposit_url: url of the deposition (usually a collection' url)
        @param username: name of the user depositing 'on behalf of' an author
        @param email: allow user to get an acknowledgement of the deposit
        @return: xml atom entry containing submission acknowledgement or error
    '''

    if username != '' and email != '':
        onbehalf = '''"%s" <%s>''' % (username, email)
    else:
        onbehalf = ''

    authentication_info = get_remote_server_auth(server_id)
    connection = RemoteSwordServer(authentication_info)

    tmp_file = open("/tmp/file", "w")
    tmp_file.write(deposit_url + '\n' + onbehalf)

    return connection.metadata_submission(deposit_url, metadata, onbehalf)


def perform_submission_process(server_id, collection, recid, user_info,
                               metadata=None, medias=None, marcxml=""):
    '''
        This function is an abstraction of the 2 steps submission process. It
        submit the media to a collection, format the metadata and submit them
        to the same collection. In case of error in one of the 3 operations, it
        stops the process and send an error message back. In addition, this
        function insert informations in the swrCLIENTDATA and MARC to avoid sending a
        record twice in the same remote server
        @param server_id: remote server id on the swrREMOTESERVER table
        @param user_info: invenio user infos of the submitter
        @param metadata: dictionnary containing some informations
        @param collection: url of the place where to deposit the record
        @param marcxml: place where to find important information to the record
        @param recid: id of the record that can be found if no marcxml
        return: tuple containing deposit informations and submission informations
    '''

    if metadata == None:
        metadata = {}

    if medias == None:
        medias = []

    # dictionnary containing 2 steps response and possible errors
    response = {'error':'',
                'message':'',
                'deposit_media':'',
                'submit_metadata':'',
                'row_id': ''}

    # get the marcxml file (if needed)
    if marcxml == '':
        if recid == '':
            response['error'] = 'You must give a marcxml file or a record id'
            return response
        marcxml = get_marcxml_from_record(recid)


    #***************************************************************************
    # Check if record was already submitted
    #***************************************************************************

    # get the record id in the marcxml file
    record_id = ''
    record_id = get_report_number_from_macrxml(marcxml)
    if record_id == '':
        response['error'] = 'The marcxml file has no record_id'
        return response

    # check if record already sent to the server
    if(is_record_sent_to_server(server_id, recid) == True):
        response['error'] = \
            'The record was already sent to the specified server'
        return response


    #***************************************************************************
    # Get informations for a 'on-behalf-of' submission if needed
    #***************************************************************************

    username = ''
    email = ''
    author = format_author_from_marcxml(marcxml)

    if author['name'] == user_info['nickname']:
        author['email'] = user_info['email']
    else:
        username = author['name']
        email = user_info['email']


    #***************************************************************************
    # Get the media from the marcxml (if not already made)
    #***************************************************************************


    media = get_medias_to_submit(medias)
    if media == {}:
        response['error'] = 'No media to submit'
        return response

    deposit_status = deposit_media(server_id, media, collection, username,
                                   email)

    # check if any answer was given
    if deposit_status == '':
        response['error'] = 'Error during media deposit process'
        return response

    tmpfd = NamedTemporaryFile(mode='w', suffix='.xml', prefix='bibsword_media_',
                               dir=CFG_TMPDIR, delete=False)
    tmpfd.write(deposit_status)
    tmpfd.close()


    #***************************************************************************
    # format the metadata files
    #***************************************************************************

    metadata = format_metadata(marcxml, deposit_status, user_info,
                               metadata)

    arxiv = ArXivFormat()
    metadata_atom = arxiv.format_metadata(metadata)


    #***************************************************************************
    # submit the metadata
    #***************************************************************************

    tmpfd = NamedTemporaryFile(mode='w', suffix='.xml', prefix='bibsword_metadata_',
                               dir=CFG_TMPDIR, delete=False)
    tmpfd.write(metadata_atom)
    tmpfd.close()

    submit_status = submit_metadata(server_id, collection, metadata_atom,
                                    username, email)

    tmpfd = NamedTemporaryFile(mode='w', suffix='.xml', prefix='bibsword_submit_',
                               dir=CFG_TMPDIR, delete=False)
    tmpfd.write(submit_status)
    tmpfd.close()

    # check if any answer was given
    if submit_status == '':
        response['message'] = ''
        response['error'] = 'Problem during submission process'
        return response


    #***************************************************************************
    # Parse the submit result
    #***************************************************************************

    # get the submission's remote id from the response
    remote_id = format_id_from_submission(submit_status)
    response['remote_id'] = remote_id

    #get links to medias, metadata and status
    links = format_links_from_submission(submit_status)
    response['links'] = links

    #insert the submission in the swrCLIENTDATA entry
    row_id = insert_into_swr_clientdata(server_id,
                                        recid,
                                        metadata['id_record'],
                                        remote_id,
                                        user_info['id'],
                                        user_info['nickname'],
                                        user_info['email'],
                                        deposit_status,
                                        submit_status,
                                        links['media'],
                                        links['metadata'],
                                        links['status'])

    #insert information field in the marc file
    current_date = time.strftime("%Y-%m-%d %H:%M:%S")
    update_marcxml_with_info(recid, user_info['nickname'], current_date,
                             remote_id)

    # format and return the response
    response['submit_metadata'] = submit_status
    response['row_id'] = row_id

    return response


def get_servicedocument(id_server):
    '''
        This metode get the xml service document file discribing the collections
        and the categories of a remote server. If the servicedocument is saved
        in the swrREMOTESERVER table or if it has not been load since a certain
        time, it is dynamically loaded from the SWORD remote server.
        @param id_server: id of the server where to get the servicedocument
        @return: service document in a String
    '''

    last_update = get_last_update(id_server)

    time_machine = datetime.datetime.now()
    time_now = int(time.mktime(time_machine.timetuple()))

    delta_time = time_now - int(last_update)

    service = select_servicedocument(id_server)

    update = 0
    if delta_time > CFG_BIBSWORD_SERVICEDOCUMENT_UPDATE_TIME:
        update = 1
    elif service == '':
        update = 1

    if update == 1:
        authentication_info = get_remote_server_auth(id_server)
        connection = RemoteSwordServer(authentication_info)
        service = connection.get_remote_collection(\
            authentication_info['url_servicedocument'])
        if service == '':
            service = select_servicedocument(id_server)
        else:
            update_servicedocument(service, id_server)

    return service


#-------------------------------------------------------------------------------
# Implementation of the Command line client
#-------------------------------------------------------------------------------

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("*************************************************"\
                         "***********************************\n")
        sys.stderr.write("                                          ERROR\n")
        sys.stderr.write("message: %s \n" % msg)
        sys.stderr.write("*************************************************"\
                         "***********************************\n")
    sys.stderr.write("\n")
    sys.stderr.write("Usage: %s [options] \n" % sys.argv[0])
    sys.stderr.write("\n")
    sys.stderr.write("*****************************************************"\
                         "**********************************\n")
    sys.stderr.write("                                             OPTIONS\n")
    sys.stderr.write("*****************************************************"\
                         "**********************************\n")
    sys.stderr.write("-h, --help      : Print this help.\n")
    sys.stderr.write("-s, --simulation: Proceed in a simulation mode\n")
    sys.stderr.write("\n")
    sys.stderr.write("*****************************************************"\
                         "**********************************\n")
    sys.stderr.write("                                             HELPERS\n")
    sys.stderr.write("*****************************************************"\
                         "**********************************\n")
    sys.stderr.write("-r, --list-remote-servers:    List all available remote"\
                         " server\n")
    sys.stderr.write("-i, --list-server-info --server-id: Display SWORD"\
                         " informations about the server \n")
    sys.stderr.write("-c, --list-collections --server-id: List collections "\
                         "for the specified server\n")
    sys.stderr.write("-n, --list-collection-info --server-id --collection_id:"\
                         " Display infos about collection \n")
    sys.stderr.write("-p, --list-primary-categories --server-id "\
                         "--colleciton_id: List mandated categories\n")
    sys.stderr.write("-o, --list-optional-categories --server-id "\
                         "--collection_id: List secondary categories\n")
    sys.stderr.write("-v, --list-submission [--server-id --id_record]: "\
                         "List submission entry in swrCLIENTDATA\n")
    sys.stderr.write("\n")
    sys.stderr.write("*****************************************************"\
                         "**********************************\n")
    sys.stderr.write("                                             OERATIONS\n")
    sys.stderr.write("*****************************************************"\
                         "**********************************\n")
    sys.stderr.write("-m, --get-marcxml-from-recid --recid: Display the"\
                         " MARCXML file for the given record\n")
    sys.stderr.write("-e, --get-media-resource [--marcxml-file|--recid]: "\
                         "Display type and url of the media\n")
    sys.stderr.write("-z, --compress-media-file [--marcxml-file|--recid]: "\
                         "Dipsplay the zipped size archive\n")
    sys.stderr.write("-d, --deposit-media --server-id --collection_id "\
                         "--media: deposit media in colleciton\n")
    sys.stderr.write("-f, --format-metadata --server-id --metadata "\
                         "--marcxml: format metadata for the server\n")
    sys.stderr.write("-l, --submit-metadata --server-id --collection-id "\
                         "--metadata: submit metadata to server\n")
    sys.stderr.write("-a, --proceed-submission --server-id --recid "\
                         "--metadata: do the entire deposit process\n")
    sys.stderr.write("\n")
    sys.exit(exitcode)


def main():
    """
        main entry point for webdoc via command line
    """
    options = {'action':'',
               'server-id':0,
               'recid':0,
               'collection-id':0,
               'mode':2,
               'marcxml-file': '',
               'collection_url':'',
               'deposit-result':'',
               'metadata':'',
               'proceed-submission':'',
               'list-submission':''}

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                    "hsricnpovmezdfla",
                                    ["help",
                                    "simulation",
                                    "list-remote-servers",
                                    "list-server-info",
                                    "list-collections",
                                    "list-collection-info",
                                    "list-primary-categories",
                                    "list-optional-categories",
                                    "list-submission",
                                    "get-marcxml-from-recid",
                                    "get-media-resource",
                                    "compress-media-file",
                                    "deposit-media",
                                    "format-metadata",
                                    "submit-metadata",
                                    "proceed-submission",
                                    "server-id=",
                                    "collection-id=",
                                    "recid=",
                                    "marcxml-file=",
                                    "collection_url=",
                                    "deposit-result=",
                                    "metadata=",
                                    "yes-i-know"
                                    ])

    except getopt.GetoptError as err:
        usage(1, err)

    if len(opts) == 0:
        usage(1, 'No options given')

    if not '--yes-i-know' in sys.argv[1:]:
        print("This is an experimental tool. It is disabled for the moment.")
        sys.exit(0)

    try:
        for opt in opts:
            if opt[0] in ["-h", "--help"]:
                usage(0)

            elif opt[0] in ["-s", "--simulation"]:
                options["simulation"]  = int(opt[1])

            #-------------------------------------------------------------------

            elif opt[0] in ["-r", "--list-remote-servers"]:
                options["action"] = "list-remote-servers"

            elif opt[0] in ["-i", "--list-server-info"]:
                options["action"] = "list-server-info"

            elif opt[0] in ["-c", "--list-collections"]:
                options["action"] = "list-collections"

            elif opt[0] in ["-n", "--list-collection-info"]:
                options["action"] = "list-collection-info"

            elif opt[0] in ["-p", "--list-primary-categories"]:
                options["action"] = "list-primary-categories"

            elif opt[0] in ["-o", "--list-optional-categories"]:
                options["action"] = "list-optional-categories"

            elif opt[0] in ["-v", "--list-submission"]:
                options['action'] = 'list-submission'

            elif opt[0] in ["-m", "--get-marcxml-from-recid"]:
                options["action"] = "get-marcxml-from-recid"

            elif opt[0] in ["-e", "--get-media-resource"]:
                options['action'] = "get-media-resource"

            elif opt[0] in ["-z", "--compress-media-file"]:
                options['action'] = "compress-media-file"

            elif opt[0] in ["-d", "--deposit-media"]:
                options['action'] = "deposit-media"

            elif opt[0] in ["-f", "--format-metadata"]:
                options['action'] = "format-metadata"

            elif opt[0] in ["l", "--submit-metadata"]:
                options['action'] = "submit-metadata"

            elif opt[0] in ["-a", "--proceed-submission"]:
                options['action'] = 'proceed-submission'


            #-------------------------------------------------------------------

            elif opt[0] in ["--server-id"]:
                options["server-id"] = int(opt[1])

            elif opt[0] in ["--collection-id"]:
                options["collection-id"] = int(opt[1])

            elif opt[0] in ["--recid"]:
                options["recid"] = int(opt[1])

            elif opt[0] in ['--marcxml-file']:
                options['marcxml-file'] = opt[1]

            elif opt[0] in ['--collection_url']:
                options['collection_url'] = opt[1]

            elif opt[0] in ['--deposit-result']:
                options['deposit-result'] = opt[1]

            elif opt[0] in ['--metadata']:
                options['metadata'] = opt[1]


    except StandardError as message:
        usage(message)

    #---------------------------------------------------------------------------
    # --check parameters type
    #---------------------------------------------------------------------------

    try:
        options["server-id"] = int(options["server-id"])
    except ValueError:
        usage(1, "--server-id must be an integer")

    try:
        options["collection-id"] = int(options["collection-id"])
    except ValueError:
        usage(1, "--collection-id must be an integer")

    try:
        options["recid"] = int(options["recid"])
    except ValueError:
        usage(1, "--recid must be an integer")


    #---------------------------------------------------------------------------
    # --list-remote-servers
    #---------------------------------------------------------------------------

    if options['action'] == "list-remote-servers":
        servers = list_remote_servers()
        for server in servers:
            print(str(server['id']) +': '+ server['name'] + \
                  ' ( ' + server['host'] + ' ) ')


    #---------------------------------------------------------------------------
    # --list-server-info
    #---------------------------------------------------------------------------

    if options['action'] == "list-server-info":

        info = list_server_info(options['server-id'])

        if info == {}:
            print('Error, no infos found !')
        else:
            print('SWORD version: ' + info['version'])
            print('Maximal upload size [Kb]: ' + info['maxUploadSize'])
            print('Implements verbose mode: ' + info['verbose'])
            print('Implementes simulation mode: ' + info['noOp'])


    #---------------------------------------------------------------------------
    # --list-collections
    #---------------------------------------------------------------------------

    if options['action'] == "list-collections":

        collections = list_collections_from_server(str(options["server-id"]))

        if len(collections) == 0:
            usage(1, "Wrong server id, try --get-remote-servers")

        for collection in collections:
            print(collection['id'] +': '+ collection['label'] + ' - ' + \
                  collection['url'])


    #---------------------------------------------------------------------------
    # --list-collection-info
    #---------------------------------------------------------------------------

    if options['action'] == "list-collection-info":

        info = list_collection_informations(str(options['server-id']),
                                            options['collection-id'])

        print('Accepted media types:')

        accept_list = info['accept']
        for accept in accept_list:
            print('- ' + accept)

        print('collection policy: ' + info['collectionPolicy'])
        print('mediation allowed: ' + info['mediation'])
        print('treatment mode: ' + info['treatment'])
        print('location of accept packaging list: ' + info['acceptPackaging'])

    #---------------------------------------------------------------------------
    # --list-primary-categories
    #---------------------------------------------------------------------------

    if options['action'] == "list-primary-categories":

        categories = list_mandated_categories(\
            str(options["server-id"]), options["collection-id"])

        if len(categories) == 0:
            usage(1, "Wrong server id, try --get-collections")

        for category in categories:
            print(category['id'] +': '+ category['label'] + ' - ' + \
                    category['url'])


    #---------------------------------------------------------------------------
    # --list-optional-categories
    #---------------------------------------------------------------------------

    if options['action'] == "list-optional-categories":

        categories = list_optional_categories(\
            str(options["server-id"]), options["collection-id"])

        if len(categories) == 0:
            usage(1, "Wrong server id, try --get-collections")

        for category in categories:
            print(category['id'] +': '+ category['label'] + ' - ' + \
                    category['url'])


    #---------------------------------------------------------------------------
    # --list-submission
    #---------------------------------------------------------------------------

    if options['action'] == "list-submission":

        results = select_submitted_record_infos()

        for result in results:
            print('\n')
            print('submission id: ' + str(result[0]))
            print('remote server id: ' + str(result[1]))
            print('submitter id: ' + str(result[4]))
            print('local record id: ' + result[2])
            print('remote record id: ' + str(result[3]))
            print('submit date: ' + result[5])
            print('document type: ' + result[6])
            print('media link: ' + result[7])
            print('metadata link: ' + result[8])
            print('status link: ' + result[9])


    #---------------------------------------------------------------------------
    # --get-marcxml-from-recid
    #---------------------------------------------------------------------------

    if options['action'] == "get-marcxml-from-recid":

        marcxml = get_marcxml_from_record(options['recid'])

        if marcxml == '':
            usage(1, "recid %d unknown" % options['recid'])

        else:
            print(marcxml)


    #---------------------------------------------------------------------------
    # --get-media-resource
    #---------------------------------------------------------------------------

    if options['action'] == "get-media-resource":

        if options['marcxml-file'] == '':
            if options ['recid'] == 0:
                usage (1, "you must provide a metadata file or a valid recid")
            else:
                options['marcxml-file'] = \
                    get_marcxml_from_record(options['recid'])
        else:
            options['marcxml-file'] = open(options['marcxml-file']).read()

        medias = get_media_list(options['recid'])

        for media in medias:
            print('media_link = '+ media['path'])
            print('media_type = '+ media['type'])

    #---------------------------------------------------------------------------
    # --compress-media-file
    #---------------------------------------------------------------------------

    if options['action'] == "compress-media-file":

        if options['marcxml-file'] != '':
            options['media-file-list'] = \
                get_media_list(options['recid'])
        elif options ['recid'] != 0:
            options['marcxml-file'] = \
                get_marcxml_from_record(options['recid'])
            options['media-file-list'] = \
                get_media_list(options['recid'])
        else:
            usage (1, "you must provide a media file list, a metadata file or"+
                      " a valid recid")

        print(compress_media_file(options['media-file-list']))


    #---------------------------------------------------------------------------
    # --deposit-media
    #---------------------------------------------------------------------------

    if options['action'] == "deposit-media":

        if options["server-id"] == 0:
            usage (1, "You must select a server where to deposit the resource."+
                         "\nDo: ./bibSword -l")

        if options['marcxml-file'] != '':
            options['media-file-list'] = \
                get_media_list(options['recid'])
        elif options ['recid'] != 0:
            options['marcxml-file'] = get_marcxml_from_record(options['recid'])
            options['media-file-list'] = \
                get_media_list(options['recid'])
        else:
            usage (1, "you must provide a media file list, a metadata file" +
                      " or a valid recid")

        collection = 'https://arxiv.org/sword-app/physics-collection'
        medias = options['media-file-list']
        server_id = options["server-id"]

        print(collection)
        for media in medias:
            print(media['type'])
        print(server_id)

        result = deposit_media(server_id, medias, collection)

        for result in results:
            print(result)


    #---------------------------------------------------------------------------
    # --format-metadata
    #---------------------------------------------------------------------------
    user_info = {'id':'1',
                 'nickname':'admin',
                 'email': CFG_SITE_ADMIN_EMAIL}

    if options['action'] == "format-metadata":

        if options['marcxml-file'] == '':
            if options ['recid'] != 0:
                options['marcxml-file'] = \
                    get_marcxml_from_record(options['recid'])
            else:
                usage (1, "you must provide a metadata file or a valid recid")

        deposit = []
        deposit.append(options['deposit-result'])

        print(format_metadata(options['marcxml-file'], deposit,
                              user_info))


    #---------------------------------------------------------------------------
    # --submit-metadata
    #---------------------------------------------------------------------------

    if options['action'] == "submit-metadata":

        if options['collection_url'] == '':
            if options['server-id'] == '' or options['collection-id'] == '':
                usage(1, \
               "You must enter a collection or a server-id and a collection-id")

        if options['metadata'] == '':
            usage(1, \
                "You must enter the location of the metadata file to submit")

        if options['server-id'] == '':
            usage(1, "You must specify the server id")

        metadata = open(options['metadata']).read()

        print(submit_metadata(options['server-id'],
                              options['collection_url'],
                              metadata,
                              user_info['nickname'],
                              user_info['email']))


    #---------------------------------------------------------------------------
    # --proceed-submission
    #---------------------------------------------------------------------------

    if options['action'] == "proceed-submission":

        if options["server-id"] == 0:
            usage (1, "You must select a server where to deposit the resource."+
                         "\nDo: ./bibSword -l")

        if options["recid"] == 0:
            usage(1, "You must specify the record to submit")

        metadata = {'title':'',
                  'id':'',
                  'updated':'',
                  'author_name':'Invenio Admin',
                  'author_email': CFG_SITE_ADMIN_EMAIL,
                  'contributors': [],
                  'summary':'',
                  'categories':[],
                  'primary_label':'High Energy Astrophysical Phenomena',
                  'primary_url':'http://arxiv.org/terms/arXiv/astro-ph.HE',
                  'comment':'',
                  'doi':'',
                  'report_nos':[],
                  'journal_refs':[],
                  'links':[]}

        collection =  'https://arxiv.org/sword-app/physics-collection'

        server_id = 1

        response = perform_submission_process(options["server-id"], user_info,
                                              metadata, collection, '', '',
                                              options['recid'])

        if response['error'] != '':
            print('error: ' + response['error'])

        if response['message'] != '':
            print('message: ' + response['message'])

        for deposit_media in response['deposit_media']:
            print('deposit_media: \n ' + deposit_media)

        if response['submit_metadata'] != '':
            print('submit_metadata: \n ' + response['submit_metadata'])


#-------------------------------------------------------------------------------
#  avoid launching file during inclusion
#-------------------------------------------------------------------------------

if __name__ == "__main__":
    main()



#-------------------------------------------------------------------------------
# Implementation of the Web Client
#-------------------------------------------------------------------------------

def perform_display_sub_status(first_row=1, offset=10,
                               action="submitted"):
    '''
        Get the given submission status and display it in a html table
        @param first_row: first row of the swrCLIENTDATA table to display
        @param offset: nb of row to select
        @return: html code containing submission status table
    '''

    #declare return values
    body = ''
    errors = []
    warnings = []

    if first_row < 1:
        first_row = 1

    submissions = list_submitted_resources(int(first_row)-1, offset, action)

    total_rows = count_nb_submitted_record()
    last_row = first_row + offset - 1
    if last_row > total_rows:
        last_row = total_rows

    selected_offset = []
    if offset == 5:
        selected_offset.append('selected')
    else:
        selected_offset.append('')

    if offset == 10:
        selected_offset.append('selected')
    else:
        selected_offset.append('')

    if offset == 25:
        selected_offset.append('selected')
    else:
        selected_offset.append('')

    if offset == 50:
        selected_offset.append('selected')
    else:
        selected_offset.append('')

    if offset == total_rows:
        selected_offset.append('selected')
    else:
        selected_offset.append('')

    if first_row == 1:
        is_first = 'disabled'
    else:
        is_first = ''

    tmp_last = total_rows - offset

    if first_row > tmp_last:
        is_last = 'disabled'
    else:
        is_last = ''

    bibsword_template = BibSwordTemplate()
    body = bibsword_template.tmpl_display_admin_page(submissions,
                                                     first_row,
                                                     last_row,
                                                     total_rows,
                                                     is_first,
                                                     is_last,
                                                     selected_offset)

    return (body, errors, warnings)


def perform_display_server_infos(id_server):
    '''
        This function get the server infos in the swrREMOTESERVER table
        and display it as an html table
        @param id_server: id of the server to get the infos
        @return: html table code to display
    '''

    server_infos = select_remote_server_infos(id_server)
    bibsword_template = BibSwordTemplate()
    return bibsword_template.tmpl_display_remote_server_info(server_infos)


def perform_display_server_list(error_messages, id_record=""):
    '''
        Get the list of remote SWORD server implemented by the BibSword API
        and generate the html code that display it as a dropdown list
        @param error_messages: list of errors that may happens in validation
        @return: string containing the generated html code
    '''

    #declare return values
    body = ''
    errors = []
    warnings = []

    # define the list that will contains the remote servers
    remote_servers = []

    # get the remote servers from the API
    remote_servers = list_remote_servers()

    # check that the list contains at least one remote server
    if len(remote_servers) == 0:
        # add an error to the error list
        errors.append('There is no remote server to display')

    else:
        # format the html body string to containing remote server dropdown list
        bibsword_template = BibSwordTemplate()
        body = bibsword_template.tmpl_display_remote_servers(remote_servers,
                                                             id_record,
                                                             error_messages)

    return (body, errors, warnings)


def perform_display_collection_list(id_server, id_record, recid,
                                    error_messages=None):
    '''
        Get the list of collections contained in the given remote server and
        generate the html code that display it as a dropdown list
        @param id_server: id of the remote server selected by the user
        @param error_messages: list of errors that may happens in validation
        @return: string containing the generated html code
    '''

    if error_messages == None:
        error_messages = []

    #declare return values
    body = ''
    errors = []
    warnings = []

    # get the server's name and host
    remote_servers = list_remote_servers(id_server)
    if len(remote_servers) > 0:
        remote_server = remote_servers[0]

    # get the server's informations to display
    remote_server_infos = list_server_info(id_server)
    if remote_server_infos['error'] != '':
        error_messages.append(remote_server_infos['error'])

    # get the server's collections
    collections = list_collections_from_server(id_server)

    if len(collections) == 0:
        # add an error to the error list
        error_messages.append('There are no collection to display')

     # format the html body string to containing remote server's dropdown list
    bibsword_template = BibSwordTemplate()
    body = bibsword_template.tmpl_display_collections(remote_server,
                                                      remote_server_infos,
                                                      collections,
                                                      id_record,
                                                      recid,
                                                      error_messages)

    return (body, errors, warnings)


def perform_display_category_list(id_server, id_collection, id_record, recid,
                                             error_messages=None):
    '''
        Get the list of mandated and optional categories contained in the given
        collection and generate the html code that display it as a dropdown list
        @param id_server: id of the remote server selected by the user
        @param id_collection: id of the collection selected by the user
        @param error_messages: list of errors that may happens in validation
        @return: string containing the generated html code
    '''

    if error_messages == None:
        error_messages = []

    #declare return values
    body = ''
    errors = []
    warnings = []

    # get the server's name and host
    remote_servers = list_remote_servers(id_server)
    if len(remote_servers) > 0:
        remote_server = remote_servers[0]

    # get the server's informations to display
    remote_server_infos = list_server_info(id_server)

    # get the collection's name and link
    collections = list_collections_from_server(id_server)
    collection = {}
    for item in collections:
        if item['id'] == id_collection:
            collection = item

    # get the collection's informations to display
    collection_infos = list_collection_informations(id_server, id_collection)

    # get primary category list
    primary_categories = list_mandated_categories(id_server, id_collection)

    # get optional categories
    optional_categories = list_optional_categories(id_server, id_collection)

    # format the html body string to containing category's dropdown list
    bibsword_template = BibSwordTemplate()
    body = bibsword_template.tmpl_display_categories(remote_server,
                                                     remote_server_infos,
                                                     collection,
                                                     collection_infos,
                                                     primary_categories,
                                                     optional_categories,
                                                     id_record,
                                                     recid,
                                                     error_messages)

    return (body, errors, warnings)


def perform_display_metadata(user, id_server, id_collection, id_primary,
                             id_categories, id_record, recid,
                             error_messages=None, metadata=None):
    '''
        Get the list of metadata contained in the given marcxml or given by
        the users and generate the html code that display it as the summary list
        for the submission
        @param id_server: id of the remote server selected by the user
        @param id_collection: id of the collection selected by the user
        @param id_primary: primary collection selected by the user
        @param id_record: record number entered by the user
        @param recid: record id corresponding to the selected record
        @param error_messages: list of errors that may happens in validation
        @param metadata: if present, replace the default entry from marcxml
        @return: string containing the generated html code
    '''

    if error_messages == None:
        error_messages = []

    if metadata == None:
        metadata = {}

    #declare return values
    body = ''
    errors = []
    warnings = []


    # get the server's name and host
    remote_servers = list_remote_servers(id_server)
    if len(remote_servers) > 0:
        remote_server = remote_servers[0]


    # get the collection's name and link
    collections = list_collections_from_server(id_server)
    collection = {}
    for item in collections:
        if item['id'] == id_collection:
            collection = item
            break


    # get primary category name and host
    primary_categories = list_mandated_categories(id_server, id_collection)
    primary = {}
    for category in primary_categories:
        if category['id'] == id_primary:
            primary = category
            break


    categories = []
    if len(id_categories) > 0:
        # get optional categories name and host
        optional_categories = list_optional_categories(id_server, id_collection)
        for item in optional_categories:
            category = {}
            for id_category in id_categories:
                if item['id'] == id_category:
                    category = item
                    categories.append(category)
                    break

    # get the marcxml file
    marcxml = get_marcxml_from_record(recid)

    # select the medias
    if 'selected_medias' in metadata:
        medias = get_media_list(recid, metadata['selected_medias'])
    else:
        medias = get_media_list(recid)

    # get the uploaded media
    if 'uploaded_media' in metadata:
        if len(metadata['uploaded_media'])  > 30:
            file_extention = ''
            if metadata['type'] == 'application/zip':
                file_extention = 'zip'
            elif metadata['type'] == 'application/tar':
                file_extention = 'tar'
            elif metadata['type'] == 'application/docx':
                file_extention = 'docx'
            elif metadata['type'] == 'application/pdf':
                file_extention = 'pdf'

            file_path = '%s/uploaded_file_1.%s' % (CFG_TMPDIR, file_extention)

            # save the file on the tmp directory
            tmp_media = open(file_path, 'w')
            tmp_media.write(metadata['uploaded_media'])

            media = {'file': metadata['uploaded_media'] ,
                     'size': str(len(metadata['uploaded_media'])),
                     'type': metadata['type'],
                     'path': file_path,
                     'selected': 'checked="yes"',
                     'loaded': True }
            medias.append(media)

    if metadata == {}:
        # get metadata from marcxml
        metadata = format_marcxml_file(marcxml)


    # format the html body string to containing category's dropdown list
    bibsword_template = BibSwordTemplate()
    body = bibsword_template.tmpl_display_metadata(user, remote_server,
                                                   collection, primary,
                                                   categories, medias,
                                                   metadata, id_record,
                                                   recid, error_messages)


    return (body, errors, warnings)


def perform_submit_record(user, id_server, id_collection, id_primary,
                          id_categories, recid, metadata=None):
    '''
        Get the given informations and submit them to the SWORD remote server
        Display the result of the submission or an error message if something
        went wrong.
        @param user: informations about the submitter
        @param id_server: id of the remote server selected by the user
        @param id_collection: id of the collection selected by the user
        @param id_primary: primary collection selected by the user
        @param recid: record id corresponding to the selected record
        @param metadata: contains all the metadata to submit
        @return: string containing the generated html code
    '''

    if metadata == None:
        metadata = {}

    #declare return values
    body = ''
    errors = []
    warnings = []

    # get the collection's name and link
    collections = list_collections_from_server(id_server)
    collection = {}
    for item in collections:
        if item['id'] == id_collection:
            collection = item

    # get primary category name and host
    primary_categories = list_mandated_categories(id_server, id_collection)
    primary = {}
    for category in primary_categories:
        if category['id'] == id_primary:
            primary = category
            metadata['primary_label'] = primary['label']
            metadata['primary_url'] = primary['url']
            break

    # get the secondary categories name and host
    categories = []
    if len(id_categories) > 0:
        # get optional categories name and host
        optional_categories = list_optional_categories(id_server, id_collection)
        for item in optional_categories:
            category = {}
            for id_category in id_categories:
                if item['id'] == id_category:
                    category = item
                    categories.append(category)

    metadata['categories'] = categories

    # get the marcxml file
    marcxml = get_marcxml_from_record(recid)

    user_info = {'id':user['uid'],
                 'nickname':user['nickname'],
                 'email':user['email']}

    result = perform_submission_process(id_server, collection['url'], recid,
                                        user_info, metadata, metadata['media'],
                                        marcxml)

    body = result

    if result['error'] != '':
        body = '<h2>'+result['error']+'</h2>'

    else:
        submissions = select_submitted_record_infos(0, 1, result['row_id'])
        if metadata['filename'] != '':
            upload_fulltext(recid, metadata['filename'])

        bibsword_template = BibSwordTemplate()
        body = bibsword_template.tmpl_display_list_submission(submissions)

    return (body, errors, warnings)
