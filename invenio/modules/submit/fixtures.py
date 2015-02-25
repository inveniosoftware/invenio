# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013 CERN.
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

import datetime
from fixture import DataSet


class SbmACTIONData(DataSet):

    class SbmACTION_APP:
        md = datetime.date(2002, 6, 11)
        lactname = u'Approve Record'
        statustext = u'Approve Record'
        actionbutton = u''
        sactname = u'APP'
        dir = u'approve'
        cd = datetime.date(2001, 11, 8)

    class SbmACTION_MBI:
        md = datetime.date(2001, 11, 7)
        lactname = u'Modify Record'
        statustext = u'Modify Record'
        actionbutton = u''
        sactname = u'MBI'
        dir = u'modify'
        cd = datetime.date(1998, 8, 17)

    class SbmACTION_SBI:
        md = datetime.date(2001, 8, 8)
        lactname = u'Submit New Record'
        statustext = u'Submit New Record'
        actionbutton = u''
        sactname = u'SBI'
        dir = u'running'
        cd = datetime.date(1998, 8, 17)

    class SbmACTION_SRV:
        md = datetime.date(2001, 11, 7)
        lactname = u'Submit New File'
        statustext = u'Submit New File'
        actionbutton = u''
        sactname = u'SRV'
        dir = u'revise'
        cd = None


class SbmALLFUNCDESCRData(DataSet):

    class SbmALLFUNCDESCR_Ask_For_Record_Details_Confirmation:
        function = u'Ask_For_Record_Details_Confirmation'
        description = u''

    class SbmALLFUNCDESCR_CaseEDS:
        function = u'CaseEDS'
        description = u''

    class SbmALLFUNCDESCR_Create_Modify_Interface:
        function = u'Create_Modify_Interface'
        description = None

    class SbmALLFUNCDESCR_Create_Recid:
        function = u'Create_Recid'
        description = None

    class SbmALLFUNCDESCR_Create_Upload_Files_Interface:
        function = u'Create_Upload_Files_Interface'
        description = u'Display generic interface to add/revise/delete files. To be used before function "Move_Uploaded_Files_to_Storage"'

    class SbmALLFUNCDESCR_Finish_Submission:
        function = u'Finish_Submission'
        description = u''

    class SbmALLFUNCDESCR_Get_Info:
        function = u'Get_Info'
        description = u''

    class SbmALLFUNCDESCR_Get_Recid:
        function = u'Get_Recid'
        description = u'This function gets the recid for a document with a given report-number (as stored in the global variable rn).'

    class SbmALLFUNCDESCR_Get_Report_Number:
        function = u'Get_Report_Number'
        description = None

    class SbmALLFUNCDESCR_Get_Sysno:
        function = u'Get_Sysno'
        description = None

    class SbmALLFUNCDESCR_Insert_Modify_Record:
        function = u'Insert_Modify_Record'
        description = u''

    class SbmALLFUNCDESCR_Insert_Record:
        function = u'Insert_Record'
        description = None

    class SbmALLFUNCDESCR_Is_Original_Submitter:
        function = u'Is_Original_Submitter'
        description = u''

    class SbmALLFUNCDESCR_Is_Referee:
        function = u'Is_Referee'
        description = u'This function checks whether the logged user is a referee for the current document'

    class SbmALLFUNCDESCR_Link_Records:
        function = u'Link_Records'
        description = u'Link two records toghether via MARC'

    class SbmALLFUNCDESCR_Mail_Approval_Request_to_Referee:
        function = u'Mail_Approval_Request_to_Referee'
        description = None

    class SbmALLFUNCDESCR_Mail_Approval_Withdrawn_to_Referee:
        function = u'Mail_Approval_Withdrawn_to_Referee'
        description = None

    class SbmALLFUNCDESCR_Mail_Submitter:
        function = u'Mail_Submitter'
        description = None

    class SbmALLFUNCDESCR_Make_Dummy_MARC_XML_Record:
        function = u'Make_Dummy_MARC_XML_Record'
        description = u''

    class SbmALLFUNCDESCR_Make_Modify_Record:
        function = u'Make_Modify_Record'
        description = None

    class SbmALLFUNCDESCR_Make_Record:
        function = u'Make_Record'
        description = u''

    class SbmALLFUNCDESCR_Move_CKEditor_Files_to_Storage:
        function = u'Move_CKEditor_Files_to_Storage'
        description = u'Transfer files attached to the record with the CKEditor'

    class SbmALLFUNCDESCR_Move_Files_to_Storage:
        function = u'Move_Files_to_Storage'
        description = u'Attach files received from chosen file input element(s)'

    class SbmALLFUNCDESCR_Move_From_Pending:
        function = u'Move_From_Pending'
        description = u''

    class SbmALLFUNCDESCR_Move_Photos_to_Storage:
        function = u'Move_Photos_to_Storage'
        description = u'Attach/edit the pictures uploaded with the "create_photos_manager_interface()" function'

    class SbmALLFUNCDESCR_Move_Revised_Files_to_Storage:
        function = u'Move_Revised_Files_to_Storage'
        description = u'Revise files initially uploaded with "Move_Files_to_Storage"'

    class SbmALLFUNCDESCR_Move_Uploaded_Files_to_Storage:
        function = u'Move_Uploaded_Files_to_Storage'
        description = u'Attach files uploaded with "Create_Upload_Files_Interface"'

    class SbmALLFUNCDESCR_Move_to_Done:
        function = u'Move_to_Done'
        description = None

    class SbmALLFUNCDESCR_Move_to_Pending:
        function = u'Move_to_Pending'
        description = None

    class SbmALLFUNCDESCR_Notify_URL:
        function = u'Notify_URL'
        description = u'Access URL, possibly to post content'

    class SbmALLFUNCDESCR_Print_Success:
        function = u'Print_Success'
        description = u''

    class SbmALLFUNCDESCR_Print_Success_APP:
        function = u'Print_Success_APP'
        description = u''

    class SbmALLFUNCDESCR_Print_Success_Approval_Request:
        function = u'Print_Success_Approval_Request'
        description = None

    class SbmALLFUNCDESCR_Print_Success_DEL:
        function = u'Print_Success_DEL'
        description = u'Prepare a message for the user informing them that their record was successfully deleted.'

    class SbmALLFUNCDESCR_Print_Success_MBI:
        function = u'Print_Success_MBI'
        description = None

    class SbmALLFUNCDESCR_Print_Success_SRV:
        function = u'Print_Success_SRV'
        description = None

    class SbmALLFUNCDESCR_Register_Approval_Request:
        function = u'Register_Approval_Request'
        description = None

    class SbmALLFUNCDESCR_Register_Referee_Decision:
        function = u'Register_Referee_Decision'
        description = None

    class SbmALLFUNCDESCR_Report_Number_Generation:
        function = u'Report_Number_Generation'
        description = None

    class SbmALLFUNCDESCR_Second_Report_Number_Generation:
        function = u'Second_Report_Number_Generation'
        description = u'Generate a secondary report number for a document.'

    class SbmALLFUNCDESCR_Send_APP_Mail:
        function = u'Send_APP_Mail'
        description = u''

    class SbmALLFUNCDESCR_Send_Approval_Request:
        function = u'Send_Approval_Request'
        description = None

    class SbmALLFUNCDESCR_Send_Delete_Mail:
        function = u'Send_Delete_Mail'
        description = u''

    class SbmALLFUNCDESCR_Send_Modify_Mail:
        function = u'Send_Modify_Mail'
        description = None

    class SbmALLFUNCDESCR_Send_SRV_Mail:
        function = u'Send_SRV_Mail'
        description = None

    class SbmALLFUNCDESCR_Set_Embargo:
        function = u'Set_Embargo'
        description = u'Set an embargo on all the documents of a given record.'

    class SbmALLFUNCDESCR_Set_RN_From_Sysno:
        function = u'Set_RN_From_Sysno'
        description = u'Set the value of global rn variable to the report number identified by sysno (recid)'

    class SbmALLFUNCDESCR_Stamp_Replace_Single_File_Approval:
        function = u'Stamp_Replace_Single_File_Approval'
        description = u'Stamp a single file when a document is approved.'

    class SbmALLFUNCDESCR_Stamp_Uploaded_Files:
        function = u'Stamp_Uploaded_Files'
        description = u'Stamp some of the files that were uploaded during a submission.'

    class SbmALLFUNCDESCR_Test_Status:
        function = u'Test_Status'
        description = u''

    class SbmALLFUNCDESCR_Update_Approval_DB:
        function = u'Update_Approval_DB'
        description = None

    class SbmALLFUNCDESCR_User_is_Record_Owner_or_Curator:
        function = u'User_is_Record_Owner_or_Curator'
        description = u'Check if user is owner or special editor of a record'

    class SbmALLFUNCDESCR_Video_Processing:
        function = u'Video_Processing'
        description = None

    class SbmALLFUNCDESCR_Withdraw_Approval_Request:
        function = u'Withdraw_Approval_Request'
        description = None

    class SbmALLFUNCDESCR_Run_PlotExtractor:
        function = u'Run_PlotExtractor'
        description = u'Run PlotExtractor on the current record'


class SbmCHECKSData(DataSet):

    class SbmCHECKS_AUCheck:
        md = None
        chefi1 = u''
        chefi2 = u''
        chdesc = u'function AUCheck(txt) {\r\n    var res=1;\r\n  tmp=txt.indexOf("\\015");\r\n while (tmp != -1) {\r\n     left=txt.substring(0,tmp);\r\n      right=txt.substring(tmp+2,txt.length);\r\n      txt=left + "\\012" + right;\r\n       tmp=txt.indexOf("\\015");\r\n }\r\n   tmp=txt.indexOf("\\012");\r\n if (tmp==-1){\r\n       line=txt;\r\n       txt=\'\';}\r\n  else{\r\n       line=txt.substring(0,tmp);\r\n      txt=txt.substring(tmp+1,txt.length);}\r\n   while (line != ""){\r\n       coma=line.indexOf(",");\r\n       left=line.substring(0,coma);\r\n        right=line.substring(coma+1,line.length);\r\n       coma2=right.indexOf(",");\r\n     space=right.indexOf(" ");\r\n     if ((coma==-1)||(left=="")||(right=="")||(space!=0)||(coma2!=-1)){\r\n          res=0;\r\n          error_log=line;\r\n     }\r\n       tmp=txt.indexOf("\\012");\r\n     if (tmp==-1){\r\n           line=txt;\r\n           txt=\'\';}\r\n      else{\r\n           line=txt.substring(0,tmp-1);\r\n            txt=txt.substring(tmp+1,txt.length);}\r\n   }\r\n   if (res == 0){\r\n      alert("This author name cannot be managed \\: \\012\\012" + error_log + " \\012\\012It is not in the required format!\\012Put one author per line and a comma (,) between the name and the firstname initial letters. \\012The name is going first, followed by the firstname initial letters.\\012Do not forget the whitespace after the comma!!!\\012\\012Example \\: Put\\012\\012Le Meur, J Y \\012Baron, T \\012\\012for\\012\\012Le Meur Jean-Yves & Baron Thomas.");\r\n     return 0;\r\n   }   \r\n    return 1;   \r\n}'
        chname = u'AUCheck'
        cd = datetime.date(1998, 8, 18)

    class SbmCHECKS_DatCheckNew:
        md = None
        chefi1 = u''
        chefi2 = u''
        chdesc = u'function DatCheckNew(txt) {\r\n    var res=1;\r\n  if (txt.length != 10){res=0;}\r\n   if (txt.indexOf("/") != 2){res=0;}\r\n    if (txt.lastIndexOf("/") != 5){res=0;}\r\n    tmp=parseInt(txt.substring(0,2),10);\r\n    if ((tmp > 31)||(tmp < 1)||(isNaN(tmp))){res=0;}\r\n    tmp=parseInt(txt.substring(3,5),10);\r\n    if ((tmp > 12)||(tmp < 1)||(isNaN(tmp))){res=0;}\r\n    tmp=parseInt(txt.substring(6,10),10);\r\n   if ((tmp < 1)||(isNaN(tmp))){res=0;}\r\n    if (txt.length  == 0){res=1;}\r\n   if (res == 0){\r\n      alert("Please enter a correct Date \\012Format: dd/mm/yyyy");\r\n     return 0;\r\n   }\r\n   return 1;   \r\n}'
        chname = u'DatCheckNew'
        cd = None


class SbmFORMATEXTENSIONData(DataSet):

    class SbmFORMATEXTENSION_CompressedPostScript_psgz:
        FILE_EXTENSION = u'.ps.gz'
        FILE_FORMAT = u'Compressed PostScript'

    class SbmFORMATEXTENSION_GIF_gif:
        FILE_EXTENSION = u'.gif'
        FILE_FORMAT = u'GIF'

    class SbmFORMATEXTENSION_HTML_htm:
        FILE_EXTENSION = u'.htm'
        FILE_FORMAT = u'HTML'

    class SbmFORMATEXTENSION_HTML_html:
        FILE_EXTENSION = u'.html'
        FILE_FORMAT = u'HTML'

    class SbmFORMATEXTENSION_JPEG_jpeg:
        FILE_EXTENSION = u'.jpeg'
        FILE_FORMAT = u'JPEG'

    class SbmFORMATEXTENSION_JPEG_jpg:
        FILE_EXTENSION = u'.jpg'
        FILE_FORMAT = u'JPEG'

    class SbmFORMATEXTENSION_Latex_tex:
        FILE_EXTENSION = u'.tex'
        FILE_FORMAT = u'Latex'

    class SbmFORMATEXTENSION_PDF_pdf:
        FILE_EXTENSION = u'.pdf'
        FILE_FORMAT = u'PDF'

    class SbmFORMATEXTENSION_PPT_ppt:
        FILE_EXTENSION = u'.ppt'
        FILE_FORMAT = u'PPT'

    class SbmFORMATEXTENSION_PostScript_ps:
        FILE_EXTENSION = u'.ps'
        FILE_FORMAT = u'PostScript'

    class SbmFORMATEXTENSION_TarredTextar_tar:
        FILE_EXTENSION = u'.tar'
        FILE_FORMAT = u'Tarred Tex (.tar)'

    class SbmFORMATEXTENSION_Text_txt:
        FILE_EXTENSION = u'.txt'
        FILE_FORMAT = u'Text'

    class SbmFORMATEXTENSION_WORD_doc:
        FILE_EXTENSION = u'.doc'
        FILE_FORMAT = u'WORD'


class SbmFUNDESCData(DataSet):

    class SbmFUNDESC_CaseEDS_casedefault:
        function = u'CaseEDS'
        param = u'casedefault'

    class SbmFUNDESC_CaseEDS_casesteps:
        function = u'CaseEDS'
        param = u'casesteps'

    class SbmFUNDESC_CaseEDS_casevalues:
        function = u'CaseEDS'
        param = u'casevalues'

    class SbmFUNDESC_CaseEDS_casevariable:
        function = u'CaseEDS'
        param = u'casevariable'

    class SbmFUNDESC_CreateModifyInterface_fieldnameMBI:
        function = u'Create_Modify_Interface'
        param = u'fieldnameMBI'

    class SbmFUNDESC_CreateUploadFilesInterface_canAddFormatDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'canAddFormatDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_canCommentDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'canCommentDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_canDeleteDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'canDeleteDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_canDescribeDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'canDescribeDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_canKeepDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'canKeepDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_canNameNewFiles:
        function = u'Create_Upload_Files_Interface'
        param = u'canNameNewFiles'

    class SbmFUNDESC_CreateUploadFilesInterface_canRenameDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'canRenameDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_canRestrictDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'canRestrictDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_canReviseDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'canReviseDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_commentLabel:
        function = u'Create_Upload_Files_Interface'
        param = u'commentLabel'

    class SbmFUNDESC_CreateUploadFilesInterface_createRelatedFormats:
        function = u'Create_Upload_Files_Interface'
        param = u'createRelatedFormats'

    class SbmFUNDESC_CreateUploadFilesInterface_defaultFilenameDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'defaultFilenameDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_descriptionLabel:
        function = u'Create_Upload_Files_Interface'
        param = u'descriptionLabel'

    class SbmFUNDESC_CreateUploadFilesInterface_doctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'doctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_endDoc:
        function = u'Create_Upload_Files_Interface'
        param = u'endDoc'

    class SbmFUNDESC_CreateUploadFilesInterface_fileLabel:
        function = u'Create_Upload_Files_Interface'
        param = u'fileLabel'

    class SbmFUNDESC_CreateUploadFilesInterface_filenameLabel:
        function = u'Create_Upload_Files_Interface'
        param = u'filenameLabel'

    class SbmFUNDESC_CreateUploadFilesInterface_keepDefault:
        function = u'Create_Upload_Files_Interface'
        param = u'keepDefault'

    class SbmFUNDESC_CreateUploadFilesInterface_maxFilesDoctypes:
        function = u'Create_Upload_Files_Interface'
        param = u'maxFilesDoctypes'

    class SbmFUNDESC_CreateUploadFilesInterface_maxsize:
        function = u'Create_Upload_Files_Interface'
        param = u'maxsize'

    class SbmFUNDESC_CreateUploadFilesInterface_minsize:
        function = u'Create_Upload_Files_Interface'
        param = u'minsize'

    class SbmFUNDESC_CreateUploadFilesInterface_restrictionLabel:
        function = u'Create_Upload_Files_Interface'
        param = u'restrictionLabel'

    class SbmFUNDESC_CreateUploadFilesInterface_restrictions:
        function = u'Create_Upload_Files_Interface'
        param = u'restrictions'

    class SbmFUNDESC_CreateUploadFilesInterface_showLinks:
        function = u'Create_Upload_Files_Interface'
        param = u'showLinks'

    class SbmFUNDESC_CreateUploadFilesInterface_startDoc:
        function = u'Create_Upload_Files_Interface'
        param = u'startDoc'

    class SbmFUNDESC_GetInfo_authorFile:
        function = u'Get_Info'
        param = u'authorFile'

    class SbmFUNDESC_GetInfo_emailFile:
        function = u'Get_Info'
        param = u'emailFile'

    class SbmFUNDESC_GetInfo_titleFile:
        function = u'Get_Info'
        param = u'titleFile'

    class SbmFUNDESC_GetRecid_recordsearchpattern:
        function = u'Get_Recid'
        param = u'record_search_pattern'

    class SbmFUNDESC_GetReportNumber_edsrn:
        function = u'Get_Report_Number'
        param = u'edsrn'

    class SbmFUNDESC_LinkRecords_directRelationship:
        function = u'Link_Records'
        param = u'directRelationship'

    class SbmFUNDESC_LinkRecords_edsrn:
        function = u'Link_Records'
        param = u'edsrn'

    class SbmFUNDESC_LinkRecords_edsrn2:
        function = u'Link_Records'
        param = u'edsrn2'

    class SbmFUNDESC_LinkRecords_keeporiginaledsrn2:
        function = u'Link_Records'
        param = u'keep_original_edsrn2'

    class SbmFUNDESC_LinkRecords_reverseRelationship:
        function = u'Link_Records'
        param = u'reverseRelationship'

    class SbmFUNDESC_MailApprovalRequesttoReferee_categfileappreq:
        function = u'Mail_Approval_Request_to_Referee'
        param = u'categ_file_appreq'

    class SbmFUNDESC_MailApprovalRequesttoReferee_categrnseekappreq:
        function = u'Mail_Approval_Request_to_Referee'
        param = u'categ_rnseek_appreq'

    class SbmFUNDESC_MailApprovalRequesttoReferee_edsrn:
        function = u'Mail_Approval_Request_to_Referee'
        param = u'edsrn'

    class SbmFUNDESC_MailApprovalWithdrawntoReferee_categfilewithd:
        function = u'Mail_Approval_Withdrawn_to_Referee'
        param = u'categ_file_withd'

    class SbmFUNDESC_MailApprovalWithdrawntoReferee_categrnseekwithd:
        function = u'Mail_Approval_Withdrawn_to_Referee'
        param = u'categ_rnseek_withd'

    class SbmFUNDESC_MailSubmitter_authorfile:
        function = u'Mail_Submitter'
        param = u'authorfile'

    class SbmFUNDESC_MailSubmitter_edsrn:
        function = u'Mail_Submitter'
        param = u'edsrn'

    class SbmFUNDESC_MailSubmitter_emailFile:
        function = u'Mail_Submitter'
        param = u'emailFile'

    class SbmFUNDESC_MailSubmitter_newrnin:
        function = u'Mail_Submitter'
        param = u'newrnin'

    class SbmFUNDESC_MailSubmitter_status:
        function = u'Mail_Submitter'
        param = u'status'

    class SbmFUNDESC_MailSubmitter_titleFile:
        function = u'Mail_Submitter'
        param = u'titleFile'

    class SbmFUNDESC_MakeDummyMARCXMLRecord_dummyreccreatetpl:
        function = u'Make_Dummy_MARC_XML_Record'
        param = u'dummyrec_create_tpl'

    class SbmFUNDESC_MakeDummyMARCXMLRecord_dummyrecsourcetpl:
        function = u'Make_Dummy_MARC_XML_Record'
        param = u'dummyrec_source_tpl'

    class SbmFUNDESC_MakeModifyRecord_modifyTemplate:
        function = u'Make_Modify_Record'
        param = u'modifyTemplate'

    class SbmFUNDESC_MakeModifyRecord_sourceTemplate:
        function = u'Make_Modify_Record'
        param = u'sourceTemplate'

    class SbmFUNDESC_MakeRecord_createTemplate:
        function = u'Make_Record'
        param = u'createTemplate'

    class SbmFUNDESC_MakeRecord_sourceTemplate:
        function = u'Make_Record'
        param = u'sourceTemplate'

    class SbmFUNDESC_MoveCKEditorFilestoStorage_inputfields:
        function = u'Move_CKEditor_Files_to_Storage'
        param = u'input_fields'

    class SbmFUNDESC_MoveFilestoStorage_documenttype:
        function = u'Move_Files_to_Storage'
        param = u'documenttype'

    class SbmFUNDESC_MoveFilestoStorage_iconsize:
        function = u'Move_Files_to_Storage'
        param = u'iconsize'

    class SbmFUNDESC_MoveFilestoStorage_pathsanddoctypes:
        function = u'Move_Files_to_Storage'
        param = u'paths_and_doctypes'

    class SbmFUNDESC_MoveFilestoStorage_pathsandrestrictions:
        function = u'Move_Files_to_Storage'
        param = u'paths_and_restrictions'

    class SbmFUNDESC_MoveFilestoStorage_pathsandsuffixes:
        function = u'Move_Files_to_Storage'
        param = u'paths_and_suffixes'

    class SbmFUNDESC_MoveFilestoStorage_rename:
        function = u'Move_Files_to_Storage'
        param = u'rename'

    class SbmFUNDESC_MovePhotostoStorage_iconformat:
        function = u'Move_Photos_to_Storage'
        param = u'iconformat'

    class SbmFUNDESC_MovePhotostoStorage_iconsize:
        function = u'Move_Photos_to_Storage'
        param = u'iconsize'

    class SbmFUNDESC_MoveRevisedFilestoStorage_createIconDoctypes:
        function = u'Move_Revised_Files_to_Storage'
        param = u'createIconDoctypes'

    class SbmFUNDESC_MoveRevisedFilestoStorage_createRelatedFormats:
        function = u'Move_Revised_Files_to_Storage'
        param = u'createRelatedFormats'

    class SbmFUNDESC_MoveRevisedFilestoStorage_elementNameToDoctype:
        function = u'Move_Revised_Files_to_Storage'
        param = u'elementNameToDoctype'

    class SbmFUNDESC_MoveRevisedFilestoStorage_iconsize:
        function = u'Move_Revised_Files_to_Storage'
        param = u'iconsize'

    class SbmFUNDESC_MoveRevisedFilestoStorage_keepPreviousVersionDoctypes:
        function = u'Move_Revised_Files_to_Storage'
        param = u'keepPreviousVersionDoctypes'

    class SbmFUNDESC_MoveUploadedFilestoStorage_createIconDoctypes:
        function = u'Move_Uploaded_Files_to_Storage'
        param = u'createIconDoctypes'

    class SbmFUNDESC_MoveUploadedFilestoStorage_forceFileRevision:
        function = u'Move_Uploaded_Files_to_Storage'
        param = u'forceFileRevision'

    class SbmFUNDESC_MoveUploadedFilestoStorage_iconsize:
        function = u'Move_Uploaded_Files_to_Storage'
        param = u'iconsize'

    class SbmFUNDESC_NotifyURL_adminemails:
        function = u'Notify_URL'
        param = u'admin_emails'

    class SbmFUNDESC_NotifyURL_attemptsleeptime:
        function = u'Notify_URL'
        param = u'attempt_sleeptime'

    class SbmFUNDESC_NotifyURL_attempttimes:
        function = u'Notify_URL'
        param = u'attempt_times'

    class SbmFUNDESC_NotifyURL_contenttype:
        function = u'Notify_URL'
        param = u'content_type'

    class SbmFUNDESC_NotifyURL_data:
        function = u'Notify_URL'
        param = u'data'

    class SbmFUNDESC_NotifyURL_url:
        function = u'Notify_URL'
        param = u'url'

    class SbmFUNDESC_NotifyURL_user:
        function = u'Notify_URL'
        param = u'user'

    class SbmFUNDESC_PrintSuccessAPP_decisionfile:
        function = u'Print_Success_APP'
        param = u'decision_file'

    class SbmFUNDESC_PrintSuccessAPP_newrnin:
        function = u'Print_Success_APP'
        param = u'newrnin'

    class SbmFUNDESC_PrintSuccess_edsrn:
        function = u'Print_Success'
        param = u'edsrn'

    class SbmFUNDESC_PrintSuccess_newrnin:
        function = u'Print_Success'
        param = u'newrnin'

    class SbmFUNDESC_PrintSuccess_status:
        function = u'Print_Success'
        param = u'status'

    class SbmFUNDESC_RegisterApprovalRequest_categfileappreq:
        function = u'Register_Approval_Request'
        param = u'categ_file_appreq'

    class SbmFUNDESC_RegisterApprovalRequest_categrnseekappreq:
        function = u'Register_Approval_Request'
        param = u'categ_rnseek_appreq'

    class SbmFUNDESC_RegisterApprovalRequest_notefileappreq:
        function = u'Register_Approval_Request'
        param = u'note_file_appreq'

    class SbmFUNDESC_RegisterRefereeDecision_decisionfile:
        function = u'Register_Referee_Decision'
        param = u'decision_file'

    class SbmFUNDESC_ReportNumberGeneration_autorngen:
        function = u'Report_Number_Generation'
        param = u'autorngen'

    class SbmFUNDESC_ReportNumberGeneration_counterpath:
        function = u'Report_Number_Generation'
        param = u'counterpath'

    class SbmFUNDESC_ReportNumberGeneration_edsrn:
        function = u'Report_Number_Generation'
        param = u'edsrn'

    class SbmFUNDESC_ReportNumberGeneration_initialvalue:
        function = u'Report_Number_Generation'
        param = u'initialvalue'

    class SbmFUNDESC_ReportNumberGeneration_nblength:
        function = u'Report_Number_Generation'
        param = u'nblength'

    class SbmFUNDESC_ReportNumberGeneration_rnformat:
        function = u'Report_Number_Generation'
        param = u'rnformat'

    class SbmFUNDESC_ReportNumberGeneration_rnin:
        function = u'Report_Number_Generation'
        param = u'rnin'

    class SbmFUNDESC_ReportNumberGeneration_yeargen:
        function = u'Report_Number_Generation'
        param = u'yeargen'

    class SbmFUNDESC_SecondReportNumberGeneration_2ndcounterpath:
        function = u'Second_Report_Number_Generation'
        param = u'2nd_counterpath'

    class SbmFUNDESC_SecondReportNumberGeneration_2ndnblength:
        function = u'Second_Report_Number_Generation'
        param = u'2nd_nb_length'

    class SbmFUNDESC_SecondReportNumberGeneration_2ndrncategfile:
        function = u'Second_Report_Number_Generation'
        param = u'2nd_rncateg_file'

    class SbmFUNDESC_SecondReportNumberGeneration_2ndrnfile:
        function = u'Second_Report_Number_Generation'
        param = u'2nd_rn_file'

    class SbmFUNDESC_SecondReportNumberGeneration_2ndrnformat:
        function = u'Second_Report_Number_Generation'
        param = u'2nd_rn_format'

    class SbmFUNDESC_SecondReportNumberGeneration_2ndrnyeargen:
        function = u'Second_Report_Number_Generation'
        param = u'2nd_rn_yeargen'

    class SbmFUNDESC_SendAPPMail_addressesAPP:
        function = u'Send_APP_Mail'
        param = u'addressesAPP'

    class SbmFUNDESC_SendAPPMail_categformatAPP:
        function = u'Send_APP_Mail'
        param = u'categformatAPP'

    class SbmFUNDESC_SendAPPMail_commentsfile:
        function = u'Send_APP_Mail'
        param = u'comments_file'

    class SbmFUNDESC_SendAPPMail_decisionfile:
        function = u'Send_APP_Mail'
        param = u'decision_file'

    class SbmFUNDESC_SendAPPMail_edsrn:
        function = u'Send_APP_Mail'
        param = u'edsrn'

    class SbmFUNDESC_SendAPPMail_newrnin:
        function = u'Send_APP_Mail'
        param = u'newrnin'

    class SbmFUNDESC_SendApprovalRequest_addressesDAM:
        function = u'Send_Approval_Request'
        param = u'addressesDAM'

    class SbmFUNDESC_SendApprovalRequest_authorfile:
        function = u'Send_Approval_Request'
        param = u'authorfile'

    class SbmFUNDESC_SendApprovalRequest_categformatDAM:
        function = u'Send_Approval_Request'
        param = u'categformatDAM'

    class SbmFUNDESC_SendApprovalRequest_directory:
        function = u'Send_Approval_Request'
        param = u'directory'

    class SbmFUNDESC_SendApprovalRequest_titleFile:
        function = u'Send_Approval_Request'
        param = u'titleFile'

    class SbmFUNDESC_SendDeleteMail_edsrn:
        function = u'Send_Delete_Mail'
        param = u'edsrn'

    class SbmFUNDESC_SendDeleteMail_recordmanagers:
        function = u'Send_Delete_Mail'
        param = u'record_managers'

    class SbmFUNDESC_SendModifyMail_addressesMBI:
        function = u'Send_Modify_Mail'
        param = u'addressesMBI'

    class SbmFUNDESC_SendModifyMail_emailFile:
        function = u'Send_Modify_Mail'
        param = u'emailFile'

    class SbmFUNDESC_SendModifyMail_fieldnameMBI:
        function = u'Send_Modify_Mail'
        param = u'fieldnameMBI'

    class SbmFUNDESC_SendModifyMail_sourceDoc:
        function = u'Send_Modify_Mail'
        param = u'sourceDoc'

    class SbmFUNDESC_SendSRVMail_addressesSRV:
        function = u'Send_SRV_Mail'
        param = u'addressesSRV'

    class SbmFUNDESC_SendSRVMail_categformatDAM:
        function = u'Send_SRV_Mail'
        param = u'categformatDAM'

    class SbmFUNDESC_SendSRVMail_emailFile:
        function = u'Send_SRV_Mail'
        param = u'emailFile'

    class SbmFUNDESC_SendSRVMail_noteFile:
        function = u'Send_SRV_Mail'
        param = u'noteFile'

    class SbmFUNDESC_SetEmbargo_datefile:
        function = u'Set_Embargo'
        param = u'date_file'

    class SbmFUNDESC_SetEmbargo_dateformat:
        function = u'Set_Embargo'
        param = u'date_format'

    class SbmFUNDESC_SetRNFromSysno_edsrn:
        function = u'Set_RN_From_Sysno'
        param = u'edsrn'

    class SbmFUNDESC_SetRNFromSysno_recordsearchpattern:
        function = u'Set_RN_From_Sysno'
        param = u'record_search_pattern'

    class SbmFUNDESC_SetRNFromSysno_reptags:
        function = u'Set_RN_From_Sysno'
        param = u'rep_tags'

    class SbmFUNDESC_StampReplaceSingleFileApproval_filetobestamped:
        function = u'Stamp_Replace_Single_File_Approval'
        param = u'file_to_be_stamped'

    class SbmFUNDESC_StampReplaceSingleFileApproval_latextemplate:
        function = u'Stamp_Replace_Single_File_Approval'
        param = u'latex_template'

    class SbmFUNDESC_StampReplaceSingleFileApproval_latextemplatevars:
        function = u'Stamp_Replace_Single_File_Approval'
        param = u'latex_template_vars'

    class SbmFUNDESC_StampReplaceSingleFileApproval_layer:
        function = u'Stamp_Replace_Single_File_Approval'
        param = u'layer'

    class SbmFUNDESC_StampReplaceSingleFileApproval_newfilename:
        function = u'Stamp_Replace_Single_File_Approval'
        param = u'new_file_name'

    class SbmFUNDESC_StampReplaceSingleFileApproval_stamp:
        function = u'Stamp_Replace_Single_File_Approval'
        param = u'stamp'

    class SbmFUNDESC_StampReplaceSingleFileApproval_switchfile:
        function = u'Stamp_Replace_Single_File_Approval'
        param = u'switch_file'

    class SbmFUNDESC_StampUploadedFiles_filestobestamped:
        function = u'Stamp_Uploaded_Files'
        param = u'files_to_be_stamped'

    class SbmFUNDESC_StampUploadedFiles_latextemplate:
        function = u'Stamp_Uploaded_Files'
        param = u'latex_template'

    class SbmFUNDESC_StampUploadedFiles_latextemplatevars:
        function = u'Stamp_Uploaded_Files'
        param = u'latex_template_vars'

    class SbmFUNDESC_StampUploadedFiles_layer:
        function = u'Stamp_Uploaded_Files'
        param = u'layer'

    class SbmFUNDESC_StampUploadedFiles_stamp:
        function = u'Stamp_Uploaded_Files'
        param = u'stamp'

    class SbmFUNDESC_StampUploadedFiles_switchfile:
        function = u'Stamp_Uploaded_Files'
        param = u'switch_file'

    class SbmFUNDESC_UpdateApprovalDB_categformatDAM:
        function = u'Update_Approval_DB'
        param = u'categformatDAM'

    class SbmFUNDESC_UpdateApprovalDB_decisionfile:
        function = u'Update_Approval_DB'
        param = u'decision_file'

    class SbmFUNDESC_UserisRecordOwnerorCurator_curatorflag:
        function = u'User_is_Record_Owner_or_Curator'
        param = u'curator_flag'

    class SbmFUNDESC_UserisRecordOwnerorCurator_curatorrole:
        function = u'User_is_Record_Owner_or_Curator'
        param = u'curator_role'

    class SbmFUNDESC_VideoProcessing_aspect:
        function = u'Video_Processing'
        param = u'aspect'

    class SbmFUNDESC_VideoProcessing_batchtemplate:
        function = u'Video_Processing'
        param = u'batch_template'

    class SbmFUNDESC_VideoProcessing_title:
        function = u'Video_Processing'
        param = u'title'

    class SbmFUNDESC_WithdrawApprovalRequest_categfilewithd:
        function = u'Withdraw_Approval_Request'
        param = u'categ_file_withd'

    class SbmFUNDESC_WithdrawApprovalRequest_categrnseekwithd:
        function = u'Withdraw_Approval_Request'
        param = u'categ_rnseek_withd'

    class SbmFUNDESC_Run_PlotExtractor_with_docname:
        function = u'Run_PlotExtractor'
        param = u'with_docname'

    class SbmFUNDESC_Run_PlotExtractor_with_doctype:
        function = u'Run_PlotExtractor'
        param = u'with_doctype'

    class SbmFUNDESC_Run_PlotExtractor_with_docformat:
        function = u'Run_PlotExtractor'
        param = u'with_docformat'

    class SbmFUNDESC_Run_PlotExtractor_extract_plots_switch_file:
        function = u'Run_PlotExtractor'
        param = u'extract_plots_switch_file'


class SbmGFILERESULTData(DataSet):

    class SbmGFILERESULT_CompressedPostScript_gzipcompresseddata:
        RESULT = u'gzip compressed data'
        FORMAT = u'Compressed PostScript'

    class SbmGFILERESULT_GIF_GIF:
        RESULT = u'GIF'
        FORMAT = u'GIF'

    class SbmGFILERESULT_HTML_HTMLdocument:
        RESULT = u'HTML document'
        FORMAT = u'HTML'

    class SbmGFILERESULT_JPEG_JPEGimage:
        RESULT = u'JPEG image'
        FORMAT = u'JPEG'

    class SbmGFILERESULT_PDF_PDFdocument:
        RESULT = u'PDF document'
        FORMAT = u'PDF'

    class SbmGFILERESULT_PostScript_HPPrinterJobLanguagedata:
        RESULT = u'HP Printer Job Language data'
        FORMAT = u'PostScript'

    class SbmGFILERESULT_PostScript_PostScriptdocument:
        RESULT = u'PostScript document'
        FORMAT = u'PostScript'

    class SbmGFILERESULT_PostScript_data:
        RESULT = u'data '
        FORMAT = u'PostScript'

    class SbmGFILERESULT_TarredTextar_tararchive:
        RESULT = u'tar archive'
        FORMAT = u'Tarred Tex (.tar)'

    class SbmGFILERESULT_WORD_data:
        RESULT = u'data'
        FORMAT = u'WORD'

    class SbmGFILERESULT_jpg_JPEGimage:
        RESULT = u'JPEG image'
        FORMAT = u'jpg'
