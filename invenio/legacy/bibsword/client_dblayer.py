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
BibSWORD Client DBLayer
'''

import datetime
import time
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibsword.config import CFG_SUBMISSION_STATUS_PUBLISHED, \
                                                CFG_SUBMISSION_STATUS_REMOVED


def get_remote_server_auth(id_remoteserver):
    '''
        This function select the username and the password stored in the
        table swrREMOTESERVER to execute HTTP Request
        @param id_remoteserver: id of the remote server to contact
        @return: (authentication_info) dictionnary conating username - password
    '''

    authentication_info = {'error':'',
                           'hostname':'',
                           'username':'',
                           'password':'',
                           'realm':'',
                           'url_servicedocument':''}

    qstr = '''SELECT host, username, password, realm, url_servicedocument ''' \
           ''' FROM swrREMOTESERVER WHERE id=%s'''
    qres = run_sql(qstr, (id_remoteserver, ))

    if len(qres) == 0 :
        authentication_info['error'] = '''The server id doesn't correspond ''' \
                                       '''to any remote server'''
        return authentication_info

    (host, username, password, realm, url_servicedocument) = qres[0]

    authentication_info['hostname'] = host
    authentication_info['username'] = username
    authentication_info['password'] = password
    authentication_info['realm'] = realm
    authentication_info['url_servicedocument'] = url_servicedocument

    return authentication_info


def update_servicedocument(xml_servicedocument, id_remoteserver):
    '''
        This function update the servicedocument filed containing all the
        collections and categories for the given remote server
        @param xml_servicedocument: xml file
        @param id_remoteserver: id number of the remote server to update
        @return: (boolean) true if update successfull, false else
    '''

    # get the current time to keep the last update time
    current_type = datetime.datetime.now()
    formatted_current_time = time.mktime(current_type.timetuple())

    qstr =    '''UPDATE swrREMOTESERVER ''' \
              '''SET xml_servicedocument=%s, last_update=%s ''' \
              '''WHERE id=%s'''
    qres = run_sql(qstr, (xml_servicedocument, formatted_current_time,
                          id_remoteserver, ))

    return qres


def select_servicedocument(id_remoteserver):
    '''
        This function retreive the servicedocument of the given remote server
        @param id_remoteserver: id number of the remote server selected
        @return: (xml_file) servicedocument xml file that contains coll and cat
    '''

    qstr = '''SELECT xml_servicedocument ''' \
           '''FROM swrREMOTESERVER ''' \
           '''WHERE id=%s'''
    qres = run_sql(qstr, (id_remoteserver, ))

    if len(qres) == 0 :
        return ''

    return qres[0][0]


def get_last_update(id_remoteserver):
    '''
        This function return the last update time of the service document. This
        is usefull to know if the service collection needs to be refreshed
        @param id_remoteserver: id number of the remote server to check
        @return: (datetime) datetime of the last update (yyyy-mm-dd hh:mm:ss)
    '''

    qstr = '''SELECT last_update ''' \
           '''FROM swrREMOTESERVER ''' \
           '''WHERE id=%s '''
    qres = run_sql(qstr, (id_remoteserver, ))

    if len(qres) == 0:
        return '0'

    return qres[0][0]


def get_all_remote_server(id_server):
    '''
        This function select the name of all remote service implementing the
        SWORD protocol. It returns a list of dictionnary containing three fields:
        id, name and host
        @return: (remote_server) list of dictionnary (id - name - host) of each
                  remote server
    '''

    remote_servers = []

    if id_server == '':
        qstr = '''SELECT id, name, host FROM swrREMOTESERVER'''
        qres = run_sql(qstr)
    else :
        qstr = ''' SELECT id, name, host FROM swrREMOTESERVER WHERE id=%s'''
        qres = run_sql(qstr, (id_server, ))


    for res in qres:
        remote_server = {}
        remote_server['id'] = res[0]
        remote_server['name'] = res[1]
        remote_server['host'] = res[2]
        remote_servers.append(remote_server)

    return remote_servers


def is_record_sent_to_server(id_server, id_record):
    '''
        check in the table swrCLIENTDATA that the current record has not already
        been sent before
        @param id_server: id of the remote server where to send the record
        @param id_record: id of the record to send
        return : True if a value was found, false else
    '''

    qstr = '''SELECT COUNT(*) FROM swrCLIENTDATA ''' \
           '''WHERE id_swrREMOTESERVER=%s AND id_record=%s ''' \
           '''AND status NOT LIKE 'removed' '''
    qres = run_sql(qstr, (id_server, id_record, ))

    if (qres[0][0] == 0):
        return False
    else:
        return True


def insert_into_swr_clientdata(id_swr_remoteserver,
                               recid,
                               report_no,
                               remote_id,
                               id_user,
                               user_name,
                               user_email,
                               xml_media_deposit,
                               xml_metadata_submit,
                               link_media,
                               link_metadata,
                               link_status):
    '''
        This method insert a new row in the swrCLIENTDATA table. Some are given in
        parameters and some other such as the insertion time and the submission
        status are set by default
        @param id_swr_remoteserver: foreign key of the sword remote server
        @param recid: foreign key of the submitted record
        @param id_user: foreign key of the user who did the submission
        @param xml_media_deposit: xml response after the media deposit
        @param xml_metadata_submit: xml response after the metadata submission
        @param remote_id: record id given by the remote server in the response
        @param link_media: remote url where to find the depositted medias
        @param link_metadata: remote url where to find the submitted metadata
        @param link_status: remote url where to check the submission status
        @return: (result) the id of the new row inserted, 0 if the submission
                                 didn't work
    '''

    current_date = time.strftime("%Y-%m-%d %H:%M:%S")
    xml_media_deposit.replace("\"", "\'")
    xml_metadata_submit.encode('utf-8')

    qstr = '''INSERT INTO swrCLIENTDATA (id_swrREMOTESERVER, id_record, ''' \
             '''report_no, id_remote, id_user, user_name, user_email,  ''' \
             '''xml_media_deposit, xml_metadata_submit, submission_date, ''' \
             '''link_medias, link_metadata, link_status, last_update) ''' \
             '''VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ''' \
             '''%s, %s) '''
    qres = run_sql(qstr, (id_swr_remoteserver, recid, report_no, remote_id,
                          id_user, user_name, user_email, xml_media_deposit,
                          xml_metadata_submit, current_date, link_media,
                          link_metadata, link_status, current_date, ))
    return qres


def count_nb_submitted_record() :
    '''
        return : the amount of submitted records
    '''

    qstr = '''SELECT COUNT(*) FROM swrCLIENTDATA'''
    qres = run_sql(qstr, ())

    return qres[0][0]


def delete_from_swr_clientdata(id_submit):
    '''
        delete the given row from the swrCLIENTDATA table. Used by the test suit
        @param id_submit: id of the row to delete
        result : boolean, true if deleted, false else
    '''

    qstr = ''' DELETE FROM swrCLIENTDATA WHERE id=%s '''
    qres = run_sql(qstr, (id_submit, ))

    return qres


def select_submitted_record_infos(first_row=0, offset=10, row_id=''):
    '''
        this method return a bidimentionnal table containing all rows of the
        table swrCLIENTDATA. If sepecified, the search can be limited to a
        server, a record or a record on a server
        @param first_row: give the limit where to start the selection
        @param offset: give the maximal amount of rows to select
        @return: table of row containing each colomn of the table swrCLIENTDATA

        FIXME: first_row is apparently supposed to select the chosen
               id_swrREMOTESERVER, but it is currently strangely handled...
    '''

    wstr = ''
    if row_id != '' :
        wstr = '''WHERE d.id = %s '''
    qstr = '''SELECT d.id, d.id_swrREMOTESERVER, r.name, r.host , ''' \
           '''d.id_record, d.report_no, d.id_remote, d.id_user, ''' \
           '''d.user_name, d.user_email, d.submission_date, ''' \
           '''d.publication_date, d.removal_date, d.link_medias, ''' \
           '''d.link_metadata, d.link_status, d.status, r.url_base_record ''' \
           '''FROM swrCLIENTDATA as d inner join swrREMOTESERVER ''' \
           '''as r ON d.id_swrREMOTESERVER = r.id ''' + wstr + \
           '''ORDER BY d.last_update DESC LIMIT %s,%s'''
    if wstr != '' :
        qres = run_sql(qstr, (row_id, first_row, offset, ))
    else :
        qres = run_sql(qstr, (first_row, offset, ))

    results = []
    for res in qres :
        result = {'publication_date':'', 'removal_date':''}
        result['id'] = res[0]
        result['id_server'] = res[1]
        result['server_name'] = res[2]
        result['server_host'] = res[3]
        result['id_record'] = res[4]
        result['report_no'] = res[5]
        result['id_remote'] = res[6]
        result['id_user'] = res[7]
        result['user_name'] = res[8]
        result['user_email'] = res[9]
        result['submission_date'] = res[10].strftime("%Y-%m-%d %H:%M:%S")
        if res[11] != None :
            result['publication_date'] = res[11].strftime("%Y-%m-%d %H:%M:%S")
        if res[12] != None :
            result['removal_date'] = res[12].strftime("%Y-%m-%d %H:%M:%S")
        result['link_medias'] = res[13]
        result['link_metadata'] = res[14]
        result['link_status'] = res[15]
        result['status'] = res[16]
        result['url_base_remote'] = res[17]
        results.append(result)

    return results


def update_submission_status(id_record, status, remote_id=''):
    '''
        update the submission field with the new status of the submission
        @param id_record: id of the row to update
        @param status: new value to set in the status field
        @return: true if update done, else, false
    '''

    current_date = time.strftime("%Y-%m-%d %H:%M:%S")

    if status == CFG_SUBMISSION_STATUS_PUBLISHED and remote_id != '' :
        qstr = '''UPDATE swrCLIENTDATA SET status=%s, id_remote=%s, ''' \
                 '''publication_date=%s, last_update=%s WHERE id=%s '''
        qres = run_sql(qstr, (status, remote_id, current_date, current_date,
                            id_record, ))


    if status == CFG_SUBMISSION_STATUS_REMOVED :
        qstr = '''UPDATE swrCLIENTDATA SET status=%s, removal_date=%s, ''' \
                 '''last_update=%s WHERE id=%s '''
        qres = run_sql(qstr, (status, current_date, current_date, id_record, ))

    else :
        qstr = '''UPDATE swrCLIENTDATA SET status=%s, last_update=%s ''' \
                 '''WHERE id=%s '''
        qres = run_sql(qstr, (status, current_date, id_record, ))

    return qres


def select_remote_server_infos(id_server):
    '''
        Select fields of the given remote server and return it in a tuple
        @param id_server: id of the server to select
        @return: (server_info) tuple containing all the available infos
    '''

    server_info = {'server_id' : '',
                   'server_name' : '',
                   'server_host' : '',
                   'username' : '',
                   'password' : '',
                   'email' : '',
                   'realm' : '',
                   'url_base_record' : '',
                   'url_servicedocument' : ''}

    qstr = '''SELECT id, name, host, username, password, email, realm, ''' \
           '''url_base_record, url_servicedocument ''' \
           '''FROM swrREMOTESERVER WHERE id = %s '''
    qres = run_sql(qstr, (id_server, ))

    result = qres[0]

    server_info['server_id'] = result[0]
    server_info['server_name'] = result[1]
    server_info['server_host'] = result[2]
    server_info['username'] = result[3]
    server_info['password'] = result[4]
    server_info['email'] = result[5]
    server_info['realm'] = result[6]
    server_info['url_base_record'] = result[7]
    server_info['url_servicedocument'] = result[8]

    return server_info
