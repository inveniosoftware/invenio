# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from fixture import DataSet


class SbmFIELDDESCData(DataSet):

    class SbmFIELDDESC_UploadFiles:
        md = None
        rows = None
        name = u'Upload_Files'
        val = None
        marccode = u''
        fddfi2 = None
        cols = None
        cd = None
        fidesc = u'"""\r\nThis is an example of element that creates a file upload interface.\r\nClone it, customize it and integrate it into your submission. Then add function \r\n\'Move_Uploaded_Files_to_Storage\' to your submission functions list, in order for files \r\nuploaded with this interface to be attached to the record. More information in \r\nthe WebSubmit admin guide.\r\n"""\r\nimport os\r\nfrom invenio.bibdocfile_managedocfiles import create_file_upload_interface\r\nfrom invenio.websubmit_functions.Shared_Functions import ParamFromFile\r\n\r\nindir = ParamFromFile(os.path.join(curdir, \'indir\'))\r\ndoctype = ParamFromFile(os.path.join(curdir, \'doctype\'))\r\naccess = ParamFromFile(os.path.join(curdir, \'access\'))\r\ntry:\r\n    sysno = int(ParamFromFile(os.path.join(curdir, \'SN\')).strip())\r\nexcept:\r\n    sysno = -1\r\nln = ParamFromFile(os.path.join(curdir, \'ln\'))\r\n\r\n"""\r\nRun the following to get the list of parameters of function \'create_file_upload_interface\':\r\necho -e \'from invenio.bibdocfile_managedocfiles import create_file_upload_interface as f\\nprint f.__doc__\' | python\r\n"""\r\ntext = create_file_upload_interface(recid=sysno,\r\n                                 print_outside_form_tag=False,\r\n                                 include_headers=True,\r\n                                 ln=ln,\r\n                                 doctypes_and_desc=[(\'main\',\'Main document\'),\r\n                                                    (\'additional\',\'Figure, schema, etc.\')],\r\n                                 can_revise_doctypes=[\'*\'],\r\n                                 can_describe_doctypes=[\'main\'],\r\n                                 can_delete_doctypes=[\'additional\'],\r\n                                 can_rename_doctypes=[\'main\'],\r\n                                 sbm_indir=indir, sbm_doctype=doctype, sbm_access=access)[1]\r\n'
        cookie = 0L
        maxlength = None
        size = None
        type = u'R'
        alephcode = None
        modifytext = None

    class SbmFIELDDESC_UploadPhotos:
        md = None
        rows = None
        name = u'Upload_Photos'
        val = None
        marccode = u''
        fddfi2 = None
        cols = None
        cd = None
        fidesc = u'"""\r\nThis is an example of element that creates a photos upload interface.\r\nClone it, customize it and integrate it into your submission. Then add function \r\n\'Move_Photos_to_Storage\' to your submission functions list, in order for files \r\nuploaded with this interface to be attached to the record. More information in \r\nthe WebSubmit admin guide.\r\n"""\r\n\r\nfrom invenio.websubmit_functions.Shared_Functions import ParamFromFile\r\nfrom invenio.websubmit_functions.Move_Photos_to_Storage import \\\r\n    read_param_file, \\\r\n    create_photos_manager_interface, \\\r\n    get_session_id\r\n\r\n# Retrieve session id\r\ntry:\r\n    # User info is defined only in MBI/MPI actions...\r\n    session_id = get_session_id(None, uid, user_info) \r\nexcept:\r\n    session_id = get_session_id(req, uid, {})\r\n\r\n# Retrieve context\r\nindir = curdir.split(\'/\')[-3]\r\ndoctype = curdir.split(\'/\')[-2]\r\naccess = curdir.split(\'/\')[-1]\r\n\r\n# Get the record ID, if any\r\nsysno = ParamFromFile("%s/%s" % (curdir,\'SN\')).strip()\r\n\r\n"""\r\nModify below the configuration of the photos manager interface.\r\nNote: `can_reorder_photos\' parameter is not yet fully taken into consideration\r\n\r\nDocumentation of the function is available at <http://localhost/admin/websubmit/websubmitadmin.py/functionedit?funcname=Move_Photos_to_Storage>\r\n"""\r\ntext += create_photos_manager_interface(sysno, session_id, uid,\r\n                                        doctype, indir, curdir, access,\r\n                                        can_delete_photos=True,\r\n                                        can_reorder_photos=True,\r\n                                        can_upload_photos=True,\r\n                                        editor_width=700,\r\n                                        editor_height=400,\r\n                                        initial_slider_value=100,\r\n                                        max_slider_value=200,\r\n                                        min_slider_value=80)'
        cookie = 0L
        maxlength = None
        size = None
        type = u'R'
        alephcode = None
        modifytext = None
