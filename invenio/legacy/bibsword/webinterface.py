'''
Forward to ArXiv.org source code
'''
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

__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

import os
from invenio.modules.access.engine import acc_authorize_action
from invenio.config import CFG_SITE_URL, CFG_TMPDIR
from invenio.legacy.webuser import page_not_authorized, collect_user_info
from invenio.legacy.bibsword.client import perform_display_sub_status, \
                                    perform_display_server_list, \
                                    perform_display_collection_list, \
                                    perform_display_category_list, \
                                    perform_display_metadata, \
                                    perform_submit_record, \
                                    perform_display_server_infos, \
                                    list_remote_servers
from invenio.legacy.webpage import page
from invenio.base.i18n import gettext_set_language
from invenio.ext.legacy.handler import wash_urlargd, WebInterfaceDirectory
from invenio.legacy.websubmit.functions.Get_Recid import \
                                           get_existing_records_for_reportnumber
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.bibsword.config import CFG_MARC_REPORT_NUMBER, CFG_MARC_ADDITIONAL_REPORT_NUMBER

class WebInterfaceSword(WebInterfaceDirectory):
    """ Handle /bibsword set of pages."""
    _exports = ['', 'remoteserverinfos']


    def __init__(self, reqid=None):
        '''Initialize'''
        self.reqid = reqid


    def __call__(self, req, form):

        errors = []
        warnings = []
        body = ''
        error_messages = []


        #***********************************************************************
        #  Get values from the form
        #***********************************************************************

        argd = wash_urlargd(form, {
            'ln' : (str, ''),

            # information of the state of the form submission
            'status' : (str, ''),
            'submit' : (str, ''),
            'last_row' : (str, ''),
            'first_row' : (str, ''),
            'offset' : (int, ''),
            'total_rows' : (str, ''),

            # mendatory informations
            'id_record' : (str, ''),
            'recid' : (int, 0),
            'id_remote_server' : (str, ''),
            'id_collection' : (str, ''),
            'id_primary' : (str, ''),
            'id_categories' : (list, []),

            'id' : (str, ''),
            'title' : (str, ''),
            'summary' : (str, ''),
            'author_name' : (str, ''),
            'author_email' : (str, ''),
            'contributor_name' : (list, []),
            'contributor_email' : (list, []),
            'contributor_affiliation' : (list, []),

            # optionnal informations
            'comment' : (str, ''),
            'doi' : (str, ''),
            'type' : (str, ''),
            'journal_refs' : (list, []),
            'report_nos' : (list, []),
            'media' : (list, []),
            'new_media' : (str, ''),
            'filename' : (str, '')
        })

        # set language for i18n text auto generation
        _ = gettext_set_language(argd['ln'])


        #authentication
        (auth_code, auth_message) = self.check_credential(req)
        if auth_code != 0:
            return page_not_authorized(req=req, referer='/bibsword',
                                       text=auth_message, navtrail='')


        user_info = collect_user_info(req)

        #Build contributor tuples {name, email and affiliation(s)}
        contributors = []
        contributor_id = 0
        affiliation_id = 0
        for name in argd['contributor_name']:
            contributor = {}
            contributor['name'] = name
            contributor['email'] = argd['contributor_email'][contributor_id]
            contributor['affiliation'] = []
            is_last_affiliation = False
            while is_last_affiliation == False and \
                  affiliation_id < len(argd['contributor_affiliation']):
                if argd['contributor_affiliation'][affiliation_id] == 'next':
                    is_last_affiliation = True
                elif argd['contributor_affiliation'][affiliation_id] != '':
                    contributor['affiliation'].append(\
                        argd['contributor_affiliation'][affiliation_id])
                affiliation_id += 1
            contributors.append(contributor)
            contributor_id += 1
        argd['contributors'] = contributors


        # get the uploaded file(s) (if there is one)
        for key, formfields in form.items():
            if key == "new_media" and hasattr(formfields, "filename") and formfields.filename:
                filename = formfields.filename
                fp = open(os.path.join(CFG_TMPDIR, filename), "w")
                fp.write(formfields.file.read())
                fp.close()
                argd['media'].append(os.path.join(CFG_TMPDIR, filename))
                argd['filename'] = os.path.join(CFG_TMPDIR, filename)

        # Prepare navtrail
        navtrail = '''<a class="navtrail" ''' \
                   '''href="%(CFG_SITE_URL)s/help/admin">Admin Area</a>''' \
                   % {'CFG_SITE_URL': CFG_SITE_URL}

        title = _("BibSword Admin Interface")

        #***********************************************************************
        #  Display admin main page
        #***********************************************************************

        if argd['status'] == '' and argd['recid'] != '' and argd['id_remote_server'] != '':
            remote_servers = list_remote_servers(argd['id_remote_server'])
            if len(remote_servers) == 0:
                error_messages.append("No corresponding remote server could be found")
                (body, errors, warnings) = perform_display_server_list(
                                                          error_messages,
                                                          argd['id_record'])
            else:
                title = _("Export with BibSword: Step 2/4")
                navtrail += ''' &gt; <a class="navtrail" ''' \
                            '''href="%(CFG_SITE_URL)s/bibsword">''' \
                            '''SWORD Interface</a>''' % \
                            {'CFG_SITE_URL' : CFG_SITE_URL}
                (body, errors, warnings) = perform_display_collection_list(
                                                       argd['id_remote_server'],
                                                       argd['id_record'],
                                                       argd['recid'],
                                                       error_messages)

        elif argd['status'] == '' or argd['submit'] == "Cancel":
            (body, errors, warnings) = perform_display_sub_status()

        elif argd['status'] == 'display_submission':

            if argd['submit'] == 'Refresh all':
                (body, errors, warnings) = \
                    perform_display_sub_status(1, argd['offset'], "refresh_all")

            elif argd['submit'] == 'Select':
                first_row = 1
                (body, errors, warnings) = \
                    perform_display_sub_status(first_row, argd['offset'])

            elif argd['submit'] == 'Next':
                first_row = int(argd['last_row']) + 1
                (body, errors, warnings) = \
                    perform_display_sub_status(first_row, argd['offset'])

            elif argd['submit'] == 'Prev':
                first_row = int(argd['first_row']) - int(argd['offset'])
                (body, errors, warnings) = \
                    perform_display_sub_status(first_row, argd['offset'])

            elif argd['submit'] == 'First':
                (body, errors, warnings) = \
                    perform_display_sub_status(1, argd['offset'])

            elif argd['submit'] == 'Last':
                first_row = int(argd['total_rows']) - int(argd['offset']) + 1
                (body, errors, warnings) = \
                    perform_display_sub_status(first_row, argd['offset'])


        #***********************************************************************
        #  Select remote server
        #***********************************************************************

            # when the user validated the metadata, display
            elif argd['submit'] == 'New submission':
                title = _("Export with BibSword: Step 1/4")
                navtrail += ''' &gt; <a class="navtrail" ''' \
                            '''href="%(CFG_SITE_URL)s/bibsword">''' \
                            '''SWORD Interface</a>''' % \
                            {'CFG_SITE_URL' : CFG_SITE_URL}

                (body, errors, warnings) = \
                    perform_display_server_list(error_messages)

        # check if the user has selected a remote server
        elif argd['status'] == 'select_server':
            title = _("Export with BibSword: Step 1/4")
            navtrail += ''' &gt; <a class="navtrail" ''' \
                        '''href="%(CFG_SITE_URL)s/bibsword">''' \
                        '''SWORD Interface</a>''' % \
                        {'CFG_SITE_URL' : CFG_SITE_URL}

            # check if given id_record exist and convert it in recid
            if argd['recid'] != 0:
                report_numbers = get_fieldvalues(argd['recid'], CFG_MARC_REPORT_NUMBER)
                report_numbers.extend(get_fieldvalues(argd['recid'], CFG_MARC_ADDITIONAL_REPORT_NUMBER))
                if report_numbers:
                    argd['id_record'] = report_numbers[0]

            elif argd['id_record'] == '':
                error_messages.append("You must specify a report number")

            else:
                recids = \
                    get_existing_records_for_reportnumber(argd['id_record'])
                if len(recids) == 0:
                    error_messages.append(\
                        "No document found with the given report number")
                elif len(recids) > 1:
                    error_messages.append(\
                    "Several documents have been found with given the report number")
                else:
                    argd['recid'] = recids[0]

            if argd['id_remote_server'] in ['0', '']:
                error_messages.append("No remote server was selected")

            if not argd['id_remote_server'] in ['0', '']:
                # get the server's name and host
                remote_servers = list_remote_servers(argd['id_remote_server'])
                if len(remote_servers) == 0:
                    error_messages.append("No corresponding remote server could be found")
                    argd['id_remote_server'] = '0'

            if argd['id_remote_server'] in ['0', ''] or argd['recid'] == 0:
                (body, errors, warnings) = perform_display_server_list(
                                                          error_messages,
                                                          argd['id_record'])

            else:
                title = _("Export with BibSword: Step 2/4")
                (body, errors, warnings) = perform_display_collection_list(
                                                       argd['id_remote_server'],
                                                       argd['id_record'],
                                                       argd['recid'],
                                                       error_messages)


        #***********************************************************************
        #  Select collection
        #***********************************************************************

        # check if the user wants to change the remote server
        elif argd['submit'] == 'Modify server':
            title = _("Export with BibSword: Step 1/4")
            navtrail += ''' &gt; <a class="navtrail" ''' \
                        '''href="%(CFG_SITE_URL)s/bibsword">''' \
                        '''SWORD Interface</a>''' % \
                        {'CFG_SITE_URL' : CFG_SITE_URL}
            (body, errors, warnings) = \
                perform_display_server_list(error_messages, argd['id_record'])

        # check if the user has selected a collection
        elif argd['status'] == 'select_collection':
            title = _("Export with BibSword: Step 2/4")
            navtrail += ''' &gt; <a class="navtrail" ''' \
                        '''href="%(CFG_SITE_URL)s/bibsword">''' \
                        '''SWORD Interface</a>''' % \
                        {'CFG_SITE_URL': CFG_SITE_URL}
            if argd['id_collection'] == '0':
                error_messages.append("No collection was selected")
                (body, errors, warnings) = perform_display_collection_list(
                                                       argd['id_remote_server'],
                                                       argd['id_record'],
                                                       argd['recid'],
                                                       error_messages)

            else:
                title = _("Export with BibSword: Step 3/4")
                (body, errors, warnings) = perform_display_category_list(
                                                       argd['id_remote_server'],
                                                       argd['id_collection'],
                                                       argd['id_record'],
                                                       argd['recid'],
                                                       error_messages)


        #***********************************************************************
        #  Select primary
        #***********************************************************************

        # check if the user wants to change the collection
        elif argd['submit'] == 'Modify collection':
            title = _("Export with BibSword: Step 2/4")
            navtrail += ''' &gt; <a class="navtrail" ''' \
                        '''href="%(CFG_SITE_URL)s/bibsword">''' \
                        '''SWORD Interface</a>''' % \
                        {'CFG_SITE_URL': CFG_SITE_URL}
            (body, errors, warnings) = perform_display_collection_list(
                                                       argd['id_remote_server'],
                                                       argd['id_record'],
                                                       argd['recid'],
                                                       error_messages)

        # check if the user has selected a primary category
        elif argd['status']  == 'select_primary_category':
            title = _("Export with BibSword: Step 3/4")
            navtrail += ''' &gt; <a class="navtrail" ''' \
                        '''href="%(CFG_SITE_URL)s/bibsword">''' \
                        '''SWORD Interface</a>''' % \
                        {'CFG_SITE_URL' : CFG_SITE_URL}
            if argd['id_primary'] == '0':
                error_messages.append("No primary category selected")
                (body, errors, warnings) = perform_display_category_list(
                                                       argd['id_remote_server'],
                                                       argd['id_collection'],
                                                       argd['id_record'],
                                                       argd['recid'],
                                                       error_messages)

            else:
                title = _("Export with BibSword: Step 4/4")
                (body, errors, warnings) = perform_display_metadata(user_info,
                                                  str(argd['id_remote_server']),
                                                  str(argd['id_collection']),
                                                  str(argd['id_primary']),
                                                  argd['id_categories'],
                                                  argd['id_record'],
                                                  argd['recid'],
                                                  error_messages)

        #***********************************************************************
        #  Check record media and metadata
        #***********************************************************************

        # check if the user wants to change the collection
        elif argd['submit'] == 'Modify destination':
            title = _("Export with BibSword: Step 3/4")
            navtrail += ''' &gt; <a class="navtrail" ''' \
                        '''href="%(CFG_SITE_URL)s/bibsword">''' \
                        '''SWORD Interface</a>''' % \
                        {'CFG_SITE_URL' : CFG_SITE_URL}
            (body, errors, warnings) = perform_display_category_list(
                                                       argd['id_remote_server'],
                                                       argd['id_collection'],
                                                       argd['id_record'],
                                                       argd['recid'],
                                                       error_messages)


        # check if the metadata are complet and well-formed
        elif argd['status']  == 'check_submission':
            title = _("Export with BibSword: Step 4/4")
            navtrail += ''' &gt; <a class="navtrail" ''' \
                        '''href="%(CFG_SITE_URL)s/bibsword">''' \
                        '''SWORD Interface</a>''' % \
                        {'CFG_SITE_URL' : CFG_SITE_URL}

            if argd['submit'] == "Upload":
                error_messages.append("Media loaded")

            if argd['id'] == '':
                error_messages.append("Id is missing")

            if argd['title'] == '':
                error_messages.append("Title is missing")

            if argd['summary'] == '':
                error_messages.append("summary is missing")
            elif len(argd['summary']) < 25:
                error_messages.append("summary must have at least 25 character")

            if argd['author_name'] == '':
                error_messages.append("No submitter name specified")

            if argd['author_email'] == '':
                error_messages.append("No submitter email specified")

            if len(argd['contributors']) == 0:
                error_messages.append("No author specified")

            if len(error_messages) > 0:

                (body, errors, warnings) = perform_display_metadata(user_info,
                                                  str(argd['id_remote_server']),
                                                  str(argd['id_collection']),
                                                  str(argd['id_primary']),
                                                  argd['id_categories'],
                                                  argd['id_record'],
                                                  argd['recid'],
                                                  error_messages,
                                                  argd)



            else:

                title = _("Export with BibSword: Acknowledgement")

                navtrail += ''' &gt; <a class="navtrail" ''' \
                        '''href="%(CFG_SITE_URL)s/bibsword">''' \
                        '''SWORD Interface</a>''' % \
                        {'CFG_SITE_URL' : CFG_SITE_URL}

                (body, errors, warnings) = perform_submit_record(user_info,
                                                 str(argd['id_remote_server']),
                                                 str(argd['id_collection']),
                                                 str(argd['id_primary']),
                                                 argd['id_categories'],
                                                 argd['recid'],
                                                 argd)


        # return of all the updated informations to be display
        return page(title        = title,
                    body         = body,
                    navtrail     = navtrail,
                    #uid         = uid,
                    lastupdated  = __lastupdated__,
                    req          = req,
                    language     = argd['ln'],
                    #errors       = errors,
                    warnings     = warnings,
                    navmenuid    = "yourmessages")


    def remoteserverinfos(self, req, form):
        '''
            This method handle the /bibsword/remoteserverinfos call
        '''

        argd = wash_urlargd(form, {
            'ln' : (str, ''),
            'id' : (str, '')
        })

        #authentication
        (auth_code, auth_message) = self.check_credential(req)
        if auth_code != 0:
            return page_not_authorized(req=req, referer='/bibsword',
                                       text=auth_message, navtrail='')


        body = perform_display_server_infos(argd['id'])

        navtrail = ''' &gt; <a class="navtrail" ''' \
                        '''href="%(CFG_SITE_URL)s/bibsword">''' \
                        '''SWORD Interface</a>''' % \
                        {'CFG_SITE_URL' : CFG_SITE_URL}


        # return of all the updated informations to be display
        return page(title        = 'Remote server infos',
                    body         = body,
                    navtrail     = navtrail,
                    #uid         = uid,
                    lastupdated  = __lastupdated__,
                    req          = req,
                    language     = argd['ln'],
                    errors       = '',
                    warnings     = '',
                    navmenuid    = "yourmessages")


    def check_credential(self, req):
        '''
            This method check if the user has the right to get into this
            function
        '''

        auth_code, auth_message = acc_authorize_action(req, 'runbibswordclient')
        return (auth_code, auth_message)


    index = __call__


