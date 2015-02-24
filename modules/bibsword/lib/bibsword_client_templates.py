# -*- coding: utf-8 -*-

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
BibSWORD Client Templates
'''

from invenio.config import CFG_SITE_URL, CFG_SITE_NAME, CFG_SITE_RECORD

class BibSwordTemplate:
    '''
        This class contains attributes and methods that allows to display all
        information used by the BibSword web user interface. Theses informations
        are form, validation or error messages
    '''

    def __init__(self):
        ''' No init necessary for this class '''

    #---------------------------------------------------------------------------
    # BibSword WebSubmit Interface
    #---------------------------------------------------------------------------

    def tmpl_display_submit_ack(self, remote_id, link):
        '''
            This method generate the html code that displays the acknoledgement
            message after the submission of a record.
            @param remote_id: id of the record given by arXiv
            @param link: links to modify or consult submission
            @return: string containing the html code
        '''

        html = ''

        html += '''<h1>Success !</h1>'''
        html += '''<p>The record has been successfully pushed to arXiv ! <br />''' \
                '''You will get an email once it will be accepted by ''' \
                '''arXiv moderator.</p>'''
        html += '''<p>The arXiv id of the submission is: <b>%s</b></p>''' % \
            remote_id
        html += '''<p><a href="www.arxiv.org/user">Manage your submission</a></p>'''

        return html

    #---------------------------------------------------------------------------
    # BibSword Administrator Interface
    #---------------------------------------------------------------------------

    def tmpl_display_admin_page(self, submissions, first_row, last_row,
                                total_rows, is_prev, is_last, offset,
                                error_messages=None):
        '''
            format the html code that display the submission table
            @param submissions: list of all submissions and their status
            @return: html code to be displayed
        '''

        if error_messages == None:
            error_messages = []

        body = '''
<form method="post" enctype="multipart/form-data" accept-charset="UTF-8" action="/bibsword">
    %(error_message)s

    <input type="hidden" name="status" value="display_submission"/>
    <input type="hidden" name="first_row" value="%(first_row)s"/>
    <input type="hidden" name="last_row" value="%(last_row)s"/>
    <input type="hidden" name="total_rows" value="%(total_rows)s" />

    <input type="submit" name="submit" value="New submission"/><br/>
    <br />
    <input type="submit" name="submit" value="Refresh all"/><br/>
    <br />
    Display
    <select name="offset">
        <option value="5" %(selected_1)s>5</option>
        <option value="10" %(selected_2)s>10</option>
        <option value="25" %(selected_3)s>25</option>
        <option value="50" %(selected_4)s>50</option>
        <option value=%(total_rows)s %(selected_5)s>all</option>
    </select>
    rows per page <input type="submit" name="submit" value="Select" /><br />
    <br />
    <input type="submit" name="submit" value="First" %(is_prev)s/>
    <input type="submit" name="submit" value="Prev" %(is_prev)s/>
    Pages %(first_row)s - %(last_row)s / %(total_rows)s
    <input type="submit" name="submit" value="Next" %(is_last)s/>
    <input type="submit" name="submit" value="Last" %(is_last)s/><br/>
    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="7" bgcolor="#e6e6fa">
                <h2>Submission state</h2>
            </td>
        </tr>
        <tr>
            <td align="center" bgcolor="#e6e6fa"><b>Remote server</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Submitter</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Record number</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Remote id</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Status</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Dates</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Links</b></td>
        </tr>
        %(submissions)s
    </table>
</form>''' % {
                 'error_message': \
                    self.display_error_message_row(error_messages),
                 'table_width'  : '100%',
                 'first_row'    : first_row,
                 'last_row'     : last_row,
                 'total_rows'   : total_rows,
                 'is_prev'      : is_prev,
                 'is_last'      : is_last,
                 'selected_1'   : offset[0],
                 'selected_2'   : offset[1],
                 'selected_3'   : offset[2],
                 'selected_4'   : offset[3],
                 'selected_5'   : offset[4],
                 'submissions'  : self.fill_submission_table(submissions)
                 }

        return body


    def tmpl_display_remote_server_info(self, server_info):
        '''
            Display a table containing all server informations
            @param server_info: tuple containing all server infos
            @return: html code for the table containing infos
        '''

        body =   '''<table width="%(table_width)s">\n''' \
                 '''    <tr>\n''' \
                 '''        <td bgcolor="#e6e6fa">ID</td>\n''' \
                 '''        <td>%(server_id)s</td>\n''' \
                 '''    </tr>\n ''' \
                 '''    <tr>\n''' \
                 '''        <td bgcolor="#e6e6fa">Name</td>\n''' \
                 '''        <td>%(server_name)s</td>\n''' \
                 '''    </tr>\n ''' \
                 '''    <tr>\n''' \
                 '''        <td bgcolor="#e6e6fa">Host</td>\n''' \
                 '''        <td>%(server_host)s</td>\n''' \
                 '''    </tr>\n ''' \
                 '''    <tr>\n''' \
                 '''        <td bgcolor="#e6e6fa">Username</td>\n''' \
                 '''        <td>%(username)s</td>\n''' \
                 '''    </tr>\n ''' \
                 '''    <tr>\n''' \
                 '''        <td bgcolor="#e6e6fa">Password</td>\n''' \
                 '''        <td>%(password)s</td>\n''' \
                 '''    </tr>\n ''' \
                 '''    <tr>\n''' \
                 '''        <td bgcolor="#e6e6fa">Email</td>\n''' \
                 '''        <td>%(email)s</td>\n''' \
                 '''    </tr>\n ''' \
                 '''    <tr>\n''' \
                 '''        <td bgcolor="#e6e6fa">Realm</td>\n''' \
                 '''        <td>%(realm)s</td>\n''' \
                 '''    </tr>\n ''' \
                 '''    <tr>\n''' \
                 '''        <td bgcolor="#e6e6fa">Record URL</td>\n''' \
                 '''        <td>%(url_base_record)s</td>\n''' \
                 '''    </tr>\n ''' \
                 '''    <tr>\n''' \
                 '''        <td bgcolor="#e6e6fa">URL Servicedocument</td>\n'''\
                 '''        <td>%(url_servicedocument)s</td>\n''' \
                 '''    </tr>\n ''' \
                 '''</table>''' % {
                    'table_width'        : '50%',
                    'server_id'          : server_info['server_id'],
                    'server_name'        : server_info['server_name'],
                    'server_host'        : server_info['server_host'],
                    'username'           : server_info['username'],
                    'password'           : server_info['password'],
                    'email'              : server_info['email'],
                    'realm'              : server_info['realm'],
                    'url_base_record'    : server_info['url_base_record'],
                    'url_servicedocument': server_info['url_servicedocument']
                 }

        return body


    def tmpl_display_remote_servers(self, remote_servers, id_record,
                                    error_messages):
        '''
            format the html code that display a dropdown list containing the
            servers
            @param self: reference to the current instance of the class
            @param remote_servers: list of tuple containing server's infos
            @return: string containing html code
        '''

        body = '''
<form method="post" enctype="multipart/form-data" accept-charset="UTF-8" action="/bibsword">
    <input type="hidden" name="status" value="select_server"/>
    %(error_message)s

    <input type="submit" name="submit" value="Cancel" />
    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="2" bgcolor="#e6e6fa">
                <h2>Forward a record</h2>
            </td>
        </tr>
        <tr>
            <td align="right" width="%(row_width)s">
                <p>Enter the number of the report to submit: </p>
            </td>
            <td align="left" width="%(row_width)s">
                <input type="text" name="id_record" size="20"
                       value="%(id_record)s"/>
            </td>
        </tr>
        <tr>
            <td align="right" width="%(row_width)s">
                <p>Select a remote server: </p>
            </td>
            <td align="left" width="%(row_width)s">
                <select name="id_remote_server" size="1">
                    <option value="0">-- select a remote server --</option>
                    %(remote_server)s
                </select>
            </td>
        </tr>
        <tr>
            <td colspan="2" align="center">
                <input type="submit" value="Select" name="submit"/>
            </td>
        </tr>
    </table>
</form>''' % {
                 'error_message': \
                    self.display_error_message_row(error_messages),
                 'table_width'   : '100%',
                 'row_width'     : '50%',
                 'id_record'     : id_record,
                 'remote_server': \
                    self.fill_dropdown_remote_servers(remote_servers)
                 }

        return body


    def tmpl_display_collections(self, selected_server, server_infos,
                                 collections, id_record, recid, error_messages):
        '''
            format the html code that display the selected server, the informations
            about the selected server and a dropdown list containing the server's
            collections
            @param self: reference to the current instance of the class
            @param selected_server: tuple containing selected server name and id
            @param server_infos: tuple containing infos about selected server
            @param collections: list contianing server's collections
            @return: string containing html code
        '''

        body = '''
<form method="post" enctype="multipart/form-data" accept-charset="UTF-8" action="/bibsword">
    <input type="hidden" name="status" value="select_collection"/>
    <input type="hidden" name="id_remote_server" value="%(id_server)s"/>
    <input type="hidden" name="id_record" value="%(id_record)s"/>
    <input type="hidden" name="recid" value="%(recid)s"/>

    %(error_message)s

    <input type="submit" name="submit" value="Cancel" />
    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="2" bgcolor="#e6e6fa">
            <h2>Remote server</h2></td>
        </tr>
        <tr>
            <td align="center" rowspan="2" valign="center">
                <h2>%(server_name)s</h2>
            </td>
            <td align="left">
                SWORD version: %(server_version)s
            </td>
        </tr>
        <tr>
            <td align="left">
                Max upload size [Kb]: %(server_maxUpload)s
            </td>
        </tr>
        <tr>
            <td align="left" colspan="2">
                <input type="submit" value="Modify server" name="submit"/>
            </td>
        </tr>
    </table>
    <p> </p>


    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="2" bgcolor="#e6e6fa"><h2>Collection</h2>
        </td>
        </tr>
        <tr>
            <td align="right" width="%(row_width)s">Select a collection: </td>
            <td align="left" width="%(row_width)s">
                <select name="id_collection" size="1">
                    <option value="0">-- select a collection --</option>
                    %(collection)s
                </select>
            </td>
        </tr>
        <tr>
            <td align="center" colspan="2">
                <input type="submit" value="Select" name="submit"/>
            </td>
        </tr>
    </table>

</form>''' % {
                 'table_width'     : '100%',
                 'row_width'       : '50%',
                 'error_message'   : \
                    self.display_error_message_row(error_messages),
                 'id_server'       : selected_server['id'],
                 'server_name'     : selected_server['name'],
                 'server_version'  : server_infos['version'],
                 'server_maxUpload': server_infos['maxUploadSize'],
                 'collection'      : \
                    self.fill_dropdown_collections(collections),
                 'id_record'       : id_record,
                 'recid'           : recid
                 }

        return body


    def tmpl_display_categories(self, selected_server, server_infos,
                                selected_collection, collection_infos,
                                primary_categories, secondary_categories,
                                id_record, recid, error_messages):
        '''
            format the html code that display the selected server, the informations
            about the selected server, the selected collections, the informations
            about the collection and a dropdown list containing the server's
            primary and secondary categories
            @param self: reference to the current instance of the class
            @param selected_server: tuple containing selected server name and id
            @param server_infos: tuple containing infos about selected server
            @param selected_collection: selected collection
            @param collection_infos: tuple containing infos about selected col
            @param primary_categories: list of mandated categories for the col
            @return: string containing html code
        '''

        body = '''
<form method="post" enctype="multipart/form-data" accept-charset="UTF-8" action="/bibsword">
    <input type="hidden" name="status" value="select_primary_category"/>
    <input type="hidden" name="id_remote_server" value="%(id_server)s"/>
    <input type="hidden" name="id_collection" value="%(id_collection)s"/>
    <input type="hidden" name="id_record" value="%(id_record)s"/>
    <input type="hidden" name="recid" value="%(recid)s"/>

    %(error_message)s

    <input type="submit" name="submit" value="Cancel" />
    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="2" bgcolor="#e6e6fa">
                <h2>Remote server</h2>
            </td>
        </tr>
        <tr>
            <td align="center" rowspan="2" valign="center">
                <h2>%(server_name)s</h2>
            </td>
            <td align="left">
                SWORD version: %(server_version)s
            </td>
        </tr>
        <tr>
            <td align="left">
                Max upload size [Kb]: %(server_maxUpload)s
            </td>
        </tr>
        <tr>
            <td align="left" colspan="2">
                <input type="submit" value="Modify server" name="submit"/>
            </td>
        </tr>
    </table>
    <p> </p>


    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="2" bgcolor="#e6e6fa">
                <h2>Collection</h2>
            </td>
        </tr>
        <tr>
            <td align="center" rowspan="2" valign="center">
                <h2>%(collection_name)s</h2>
            </td>
            <td align="left">
                URL: %(collection_url)s
            </td>
        </tr>
        <tr>
            <td align="left">
                Accepted media types:
                <ul>%(collection_accept)s</ul>
            </td>
        </tr>
        <tr>
            <td align="left" colspan=2>
                <input type="submit" value="Modify collection" name="submit"/>
            </td>
        </tr>
    </table>
    <p> </p>


    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="2" bgcolor="#e6e6fa">
                <h2>Mandatory category</h2>
            </td>
        </tr>
        <tr>
            <td align="right" width="%(row_width)s">
                <p>Select a mandated category: </p>
            </td>
            <td align="left" width="%(row_width)s">
                <select name="id_primary" size="1">
                    <option value="0">-- select a category --</option>
                    %(primary_categories)s
                </select>
            </td>
        </tr>
    </table>
    <p></p>


    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="2" bgcolor="#e6e6fa">
                <h2>Optional categories</h2>
            </td>
        </tr>
            <td align="right" width="%(row_width)s">
                <p>Select optional categories: </p>
            </td>
            <td align="left" width="%(row_width)s">
                <select name="id_categories" size="10" multiple>
                    %(secondary_categories)s
                </select>
            </td>
        </tr>
    </table>
    <p> </p>

    <center>
        <input type="submit" value="Select" name="submit"/>
    </center>

</form>''' % {
                 'table_width'           : '100%',
                 'row_width'             : '50%',
                 'error_message'        : self.display_error_message_row(
                                                 error_messages),

                 # hidden input
                 'id_server'             : selected_server['id'],
                 'id_collection'        : selected_collection['id'],
                 'id_record'             : id_record,
                 'recid'                   : recid,

                 # variables values
                 'server_name'           : selected_server['name'],
                 'server_version'       : server_infos['version'],
                 'server_maxUpload'    : server_infos['maxUploadSize'],

                 'collection_name'     : selected_collection['label'],

                 'collection_accept': ''.join([
                '''<li>%(name)s </li>''' % {
                        'name': accept
                } for accept in collection_infos['accept'] ]),

                 'collection_url'       : selected_collection['url'],
                 'primary_categories' : self.fill_dropdown_primary(
                                                 primary_categories),

                 'secondary_categories': self.fill_dropdown_secondary(
                                                 secondary_categories)
                 }

        return body


    def tmpl_display_metadata(self, user, server, collection, primary,
                              categories, medias, metadata, id_record, recid,
                              error_messages):
        '''
            format a string containing every informations before a submission
        '''


        body = '''
<form method="post" enctype="multipart/form-data" accept-charset="UTF-8" action="/bibsword">
    <input type="hidden" name="status" value="check_submission"/>
    <input type="hidden" name="id_remote_server" value="%(id_server)s"/>
    <input type="hidden" name="id_collection" value="%(id_collection)s"/>
    <input type="hidden" name="id_primary" value="%(id_primary)s"/>
    <input type="hidden" name="id_categories" value="%(id_categories)s"/>
    <input type="hidden" name="id_record" value="%(id_record)s"/>
    <input type="hidden" name="recid" value="%(recid)s"/>

    %(error_message)s

    <input type="submit" name="submit" value="Cancel" />
    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="2" bgcolor="#e6e6fa">
                <h2>Destination</h2>
            </td>
        </tr>
        <tr>
            <td align="center" rowspan="3" valign="center">
                <h2>%(server_name)s</h2>
            </td>
            <td align="left">
                Collection: %(collection_name)s ( %(collection_url)s )
            </td>
        </tr>
        <tr>
            <td align="left">
                Primary category: %(primary_name)s ( %(primary_url)s )
            </td>
        </tr>
%(categories)s
        <tr>
            <td align="left" colspan="2">
                <input type="submit" value="Modify destination" name="submit"/>
            </td>
        </tr>
    </table>
    <p> </p>


    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="4" bgcolor="#e6e6fa">
                <h2>Submitter</h2>
            </td>
        </tr>
        <tr>
            <td width="%(row_width)s">Name:</td>
            <td><input type="text" name="author_name" size="100"
                       value="%(user_name)s"/></td>
        </tr>
        <tr>
            <td>Email:</td>
            <td><input type="text" name="author_email" size="100"
                       value="%(user_email)s"/></td>
        </tr>
    </table>
    <p></p>

    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="4" bgcolor="#e6e6fa"><h2>Media</h2></td>
        </tr>
        <tr><td colspan="4">%(medias)s%(media_help)s</td></tr>
    </table>
    <p></p>


    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="3" bgcolor="#e6e6fa"><h2>Metadata</h2>   <font color="red"><b>Warning:</b> modification(s) will not be saved on the %(CFG_SITE_NAME)s</font>
            </td>
        </tr>
        <tr>
            <td align="left" width="%(row_width)s"><p>Report Number<span style="color:#f00">*</span>:</p></td>
            <td><input type="text" name="id" size="100" value="%(id)s"/></td>
        </tr>
        <tr>
            <td align="left" width="%(row_width)s"><p>Title<span style="color:#f00">*</span>:</p></td>
            <td><input type="text" name="title" size="100" value="%(title)s"/>
            </td>
        </tr>
        <tr>
            <td align="left" width="%(row_width)s"><p>Summary<span style="color:#f00">*</span>:</p></td>
            <td>
                <textarea name="summary" rows="4" cols="100">%(summary)s
                </textarea>
            </td>
        </tr>
%(contributors)s
%(journal_refs)s
%(report_nos)s
    </table>

    <p><font color="red">The fields having a * are mandatory</font></p>

    <center>
        <input type="submit" value="Submit" name="submit"/>
    </center>

<form>''' % {
                 'table_width'     : '100%',
                 'row_width'       : '25%',
                 'error_message'   : \
                    self.display_error_message_row(error_messages),
                 'CFG_SITE_NAME': CFG_SITE_NAME,

                 # hidden input
                 'id_server'         : server['id'],
                 'id_collection'     : collection['id'],
                 'id_primary'        : primary['id'],
                 'id_categories'     : self.get_list_id_categories(categories),
                 'id_record'         : id_record,
                 'recid'             : recid,

                 # variables values
                 'server_name'          : server['name'],
                 'collection_name'      : collection['label'],
                 'collection_url'       : collection['url'],
                 'primary_name'         : primary['label'],
                 'primary_url'          : primary['url'],
                 'categories'    : self.fill_optional_category_list(categories),

                 #user
                 'user_name'    : user['nickname'],
                 'user_email'   : user['email'],

                 # media
                 'medias'     : self.fill_media_list(medias, server['id']),
                 'media_help' : self.fill_arxiv_help_message(),

                 # metadata
                 'id'           : metadata['id'],
                 'title'        : metadata['title'],
                 'summary'      : metadata['summary'],
                 'contributors' : self.fill_contributors_list(
                                        metadata['contributors']),
                 'journal_refs' : self.fill_journal_refs_list(
                                        metadata['journal_refs']),
                 'report_nos'   : self.fill_report_nos_list(
                                        metadata['report_nos'])
             }

        return body


    def tmpl_display_list_submission(self, submissions):
        '''
            Display the data of submitted recods
        '''

        body = '''
<form method="post" enctype="multipart/form-data" accept-charset="UTF-8" action="/bibsword">
    <table border="1" valign="top" width="%(table_width)s">
        <tr>
            <td align="left" colspan="7" bgcolor="#e6e6fa">
                <h2>Document successfully submitted !</h2>
            </td>
        </tr>
        <tr>
            <td align="center" bgcolor="#e6e6fa"><b>Remote server</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Submitter</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Record id</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Remote id</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Status</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Dates</b></td>
            <td align="center" bgcolor="#e6e6fa"><b>Links</b></td>
        </tr>
        %(submissions)s
    </table>
    <a href=%(CFG_SITE_URL)s/bibsword>Return</a>
</form>''' % {
                 'table_width'    : '100%',
                 'submissions'    : self.fill_submission_table(submissions),
                 'CFG_SITE_URL'   : CFG_SITE_URL
                 }

        return body


    #***************************************************************************
    # Private functions
    #***************************************************************************


    def display_error_message_row(self, error_messages):
        '''
            return a list of error_message in form of a bullet list
            @param error_messages: list of error_messages to display
            @return: html code that display list of errors
        '''

        # if no errors, return nothing
        if len(error_messages) == 0:
            return ''

        if len(error_messages) == 1:
            # display a generic header message
            body = '''
<tr>
    <td align="left" colspan=2>
        <font color='red'>
        <p> The following error was found: </p>
        <ul>
'''

        else:
            # display a generic header message
            body = '''
<tr>
    <td align="left" colspan=2>
        <font color='red'>
        <p> Following errors were found: </p>
        <ul>
'''

        # insert each error lines
        for error_message in error_messages:
            body = body + '''
        <li>%(error)s</li>''' % {
            'error': error_message
        }

        body = body + '''
        </ul>
        </font>
    </td>
</tr>'''

        return body


    def fill_submission_table(self, submissions):
        '''
            This method return the body of the submission state table. each
            submissions given in parameters has one row
            @param submissions: submission status list
            @return: html table body
        '''

        return ''.join([
        '''  <tr>
        <td>%(id_server)s: <a href="%(server_infos)s">
            %(server_name)s</a></td>
        <td>%(user_name)s <br/> %(user_email)s</td
        <td>%(id_bibrec)s: <a href="%(cfg_site_url)s/%(CFG_SITE_RECORD)s/%(id_bibrec)s"
            target="_blank">%(no_bibrec)s</a></td>
        <td><a href="%(url_base_remote)s/%(id_remote)s" target="_blank">
            %(id_remote)s</a></td>
        <td>%(status)s</td>
        <td><b>submission: </b> %(submission_date)s <br/>
             <b>publication: </b> %(publication_date)s <br/>
             <b>removal: </b> %(removal_date)s </td>
        <td><b>media: </b> <a href="%(media_link)s" target="_blank">
            %(media_link)s</a> <br/>
             <b>metadata: </b> <a href="%(metadata_link)s" target="_blank">
                %(metadata_link)s</a> <br />
             <b>status: </b> <a href="%(status_link)s" target="_blank">
                %(status_link)s</a></td>
    </tr>''' % {
            'id_server'            : str(submission['id_server']),
            'server_infos'          : "%s/bibsword/remoteserverinfos?id=%s" % \
                                     (CFG_SITE_URL, submission['id_server']),
            'server_name'          : str(submission['server_name']),
            'user_name'            : str(submission['user_name']),
            'user_email'           : str(submission['user_email']),
            'id_bibrec'            : str(submission['id_record']),
            'no_bibrec'            : str(submission['report_no']),
            'id_remote'            : str(submission['id_remote']),
            'status'               : str(submission['status']),
            'submission_date'      : str(submission['submission_date']),
            'publication_date'     : str(submission['publication_date']),
            'removal_date'         : str(submission['removal_date']),
            'media_link'           : str(submission['link_medias']),
            'metadata_link'        : str(submission['link_metadata']),
            'status_link'          : str(submission['link_status']),
            'url_base_remote'      : str(submission['url_base_remote']),
            'cfg_site_url'         : CFG_SITE_URL,
            'CFG_SITE_RECORD'       : CFG_SITE_RECORD
        } for submission in submissions])


    def fill_dropdown_remote_servers(self, remote_servers):
        '''
            This method fill a dropdown list of remote servers.
            @return: html code to display
        '''

        return ''.join([
                '''<option value="%(id)s">%(name)s - %(host)s</option>''' % {
                        'id': str(remote_server['id']),
                        'name': remote_server['name'],
                        'host': remote_server['host']
                } for remote_server in remote_servers])


    def fill_dropdown_collections(self, collections):
        '''
            This method fill a dropdown list of collection.
            @param collections: list of all collections with name - url
            @return: html code to display
        '''

        return ''.join([
                '''<option value="%(id)s">%(name)s</option>''' % {
                        'id': str(collection['id']),
                        'name': collection['label']
                } for collection in collections])



    def fill_dropdown_primary(self, primary_categories):
        '''
            This method fill the primary dropdown list with the data given in
            parameter
            @param primary_categories: list of 'url' 'name' tuples
            @return: html code generated to display the list
        '''
        return ''.join([
                '''<option value="%(id)s">%(name)s</option>'''  % {
                        'id': primary_categorie['id'],
                        'name': primary_categorie['label']
                } for primary_categorie in primary_categories])


    def fill_dropdown_secondary(self, categories):
        '''
            This method fill a category list. This list is allows the multi-selection
            or items. To proced to select more than one categorie through a browser
            ctrl + clic
            @param categories: list of all categories in the format name - url
            @return: the html code that display each dropdown list
        '''

        if len(categories) == '':
            return ''

        return ''.join([
                '''<option value="%(id)s">%(name)s</option>''' % {
                        'id': category['id'],
                        'name': category['label']
        } for category in categories])



    def fill_optional_category_list(self, categories):
        '''
            This method fill a table row that contains name and url of the selected
            optional categories
            @param self: reference to the current instance of the class
            @param categories: list of tuples containing selected categories
            @return: html code generated to display the list
        '''

        if len(categories) == 0:
            return ''

        else:
            body = '<tr><td>'

            body = body + ''.join([
                '''<p>Category: %(category_name)s ( %(category_url)s )</p>'''%{
                    'category_name' : category['label'],
                    'category_url'  : category['url']
                } for category in categories
            ])

        body = body + '</td></tr>'
        return body


    def fill_media_list(self, medias, id_server, from_websubmit=False):
        '''
            Concatenate the string that contains all informations about the medias
        '''

        text = ''

        if id_server == 1:

            media_type = self.format_media_list_by_type(medias)

            text = '''<h2>Please select files you would like to push to arXiv:</h2>'''

            for mtype in media_type:
                text += '''<h3><b>%s: </b></h3>''' % mtype['media_type']
                text += '''<blockquote>'''
                for media in mtype['media_list']:
                    text += '''<input type='checkbox' name="media" value="%s" %s>%s</input><br />''' % (media['path'], media['selected'], media['name'])
                text += "</blockquote>"

            text += '''<h3>Upload</h3>'''
            text += '''<blockquote>'''
            text += '''<p>In addition, you can submit a new file (that will be added to the record as well):</p>'''

            if from_websubmit == False:
                text += '''<input type="file" name="new_media" size="60"/>'''
        return text


    def fill_arxiv_help_message(self):
        text = '''</blockquote><h3>Help</h3>'''
        text += '''<blockquote><p>For more help on which formats are supported by arXiv, please see:'''\
                '''<ul>'''\
                '''<li><a href="http://arxiv.org/help/submit" target="_blank">'''\
                    '''arXiv submission process</a></li>'''\
                '''<li><a href="http://arxiv.org/help/submit_tex" target="_blank">'''\
                    '''arXiv TeX submission</a></li>'''\
                '''<li><a href="http://arxiv.org/help/submit_docx" target="_blank">'''\
                    '''arXiv Docx submission</a></li>'''\
                '''<li><a href="http://arxiv.org/help/submit_pdf" target="_blank">'''\
                    '''arXiv PDF submission</a></li>'''\
                '''</ul></blockquote>'''
        return text


    def fill_contributors_list(self, contributors):
        '''
            This method display each contributors in the format of an editable input
            text. This allows the user to modifie it.
            @param contributors: The list of all contributors of the document
            @return: the html code that display each dropdown list
        '''

        output = ''

        is_author = True

        for author in contributors:

            nb_rows = 2

            author_name = \
            '''<LABEL for="name">Name: </LABEL><input type = "text" ''' \
            '''name = "contributor_name" size = "100" value = "%s" ''' \
            '''id="name"/>''' % author['name']

            author_email = \
            '''<LABEL for = "email">Email: </LABEL>''' \
            '''<input type = "text" name = "contributor_email" ''' \
            '''size = "100" value = "%s" id = "email"/>''' % author['email']

            author_affiliations = []
            for affiliation in author['affiliation']:
                affiliation_row = \
                '''<LABEL for = "affiliation">Affiliation: </LABEL> ''' \
                '''<input type="text" name = "contributor_affiliation" ''' \
                '''size = "100" value = "%s" id = "affiliation"/>''' % \
                    affiliation
                author_affiliations.append(affiliation_row)
                nb_rows = nb_rows + 1
            affiliation_row = \
            '''<LABEL for = "affiliation">Affiliation: </LABEL>''' \
            '''<input type = "text" name = "contributor_affiliation" ''' \
            '''size = "100" id = "affiliation"/>'''
            author_affiliations.append(affiliation_row)
            nb_rows = nb_rows + 1

            if is_author:
                output += '''<tr><td rowspan = "%s">Author: </td>''' % nb_rows
                is_author = False
            else:
                output += '''<tr><td rowspan = "%s">Contributor: </td>''' % \
                    nb_rows
            output += '''<td>%s</td></tr>''' % author_name
            if author_email != '':
                output += '''<tr><td>%s</td></tr>''' % author_email
            for affiliation in author_affiliations:
                output += '''<tr><td>%s</td></tr>''' % affiliation
            output += \
                '''<input type = "hidden" name = "contributor_affiliation" ''' \
                '''value = "next"/>'''

        return output


    def fill_journal_refs_list(self, journal_refs):
        '''
            This method display each journal references in the format of an editable
            input text. This allows the user to modifie it.
            @param journal_refs: The list of all journal references of the document
            @return: the html code that display each dropdown list
        '''

        html = ''

        if len(journal_refs) > 0:

            html += '''
            <tr>
                <td align="left"><p>Journal references: </p></td><td>
            '''

            html = html + ''.join([
                '''
                <p><input type="text" name="journal_refs" size="100" ''' \
                '''value="%(journal_ref)s"/></p>
                ''' % {
                        'journal_ref': journal_ref
                } for journal_ref in journal_refs
            ])

            html = html + '''
                </td>
            </tr>
            '''

        return html


    def fill_report_nos_list(self, report_nos):
        '''
            Concatate a string containing the report number html table rows
        '''

        html = ''

        if len(report_nos) > 0:

            html = '''
            <tr>
                <td align="left"><p>Report numbers: </p></td><td>
            '''

            html = html + ''.join([
                '''
                <p><input type="text" name="report_nos" size="100" ''' \
                '''value="%(report_no)s"/></p>''' % {
                        'report_no': report_no
                } for report_no in report_nos
            ])

            html = html + '''
                </td>
            </tr>
            '''

        return html


    def get_list_id_categories(self, categories):
        '''
            gives the id of the categores tuple
        '''

        id_categories = []

        for category in categories:
            id_categories.append(category['id'])

        return id_categories


    def format_media_list_by_type(self, medias):
        '''
            This function format the media by type (Main, Uploaded, ...)
        '''

        #format media list by type of document
        media_type = []

        for media in medias:

            # if it is the first media of this type, create a new type
            is_type_in_media_type = False
            for type in media_type:
                if media['collection'] == type['media_type']:
                    is_type_in_media_type = True

            if is_type_in_media_type == False:
                type = {}
                type['media_type'] = media['collection']
                type['media_list'] = []
                media_type.append(type)

            # insert the media in the good media_type element
            for type in media_type:
                if type['media_type'] == media['collection']:
                    type['media_list'].append(media)

        return media_type
