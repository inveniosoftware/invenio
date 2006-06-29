## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

import string
from invenio.bibedit_dblayer import *
from invenio.bibedit_config  import *
from invenio.config          import tmpdir, weburl
from invenio.messages        import gettext_set_language, language_list_long

## Link of edit and delete button:
btn_delete_url = "../../../img/iconcross.gif"
btn_edit_url   = "../../../img/iconpen.gif"
weburl_bibedit = "%s/admin/bibedit/bibeditadmin.py" % weburl

class Template:
    
    def tmpl_table_header(self, ln, type_table, recID, temp="false", format_tag='marc',
                          tag='', num_field=None, add=0):        
        """ Return the Header of table. """

        _ = gettext_set_language(ln)

        start_form = ''
        (tag, ind1,ind2, junk) = marc_to_split_tag(tag)
        tag = tag + ind1 + ind2 + "%"
        
        if type_table != "record":

            if add == 1:
                print_input_add_form = " <input type=\"hidden\" value=\"2\" name=\"add\"> "
            else:
                print_input_add_form = ''
                
            print_action_add_subfield = """ %(print_input_add_form)s
                                            <input type=\"hidden\" value=\"%(num_field)s\" name=\"num_field\">
                                            <br\> """ % {'num_field'            : str(num_field),
                                                         'print_input_add_form' : print_input_add_form}
                                            
            if add != 1:
                link_add_subfields = self.tmpl_link(ln, _("Add Subfield"), weburl_bibedit, 'edit',
                                                    {'recID'      : str(recID),
                                                     'tag'        : tag[:3],
                                                     'num_field'  : str(num_field),
                                                     'format_tag' : format_tag,
                                                     'temp'       : 'true',
                                                     'add'        : 1})
                
                print_action_add_subfield = """ %(field)s: 
                                                %(link_add_subfields)s
                                                &nbsp;
                                            """ % {'field'              : _("Field"),
                                                   'link_add_subfields' : link_add_subfields}
                
            if add == 1:
                link_form = "edit"
            else:
                link_form = "index"
                
            result = """ <form action=\"%(weburl_bibedit)s/%(link_form)s\" method=\"POST\">
                           <input type=\"hidden\" value=\"%(recID)s\" name=\"recID\">
                           <input type=\"hidden\" value=\"true\" name=\"temp\">
                           <input type=\"hidden\" value=\"%(ln)s\" name=\"ln\">
                         <div align=\"right\">
                           <font size=\"2\">
                           &nbsp;&nbsp;&nbsp;
                           %(print_action_add_subfield)s
                           </font>
                         </div>
                     """ % {'weburl_bibedit'            : weburl_bibedit,
                            'recID'                     : str(recID),
                            'ln'                        : ln,
                            'link_form'                 : link_form,
                            'print_action_add_subfield' : print_action_add_subfield}
                     
        else:
            link_submit         = ''
            link_add_field      = self.tmpl_link(ln, _("Add Field"), weburl_bibedit, 'index',
                                                 {'recID'      : str(recID),
                                                  'tag'        : tag[:3],
                                                  'format_tag' : format_tag,
                                                  'temp'       : 'true',
                                                  'add'        : 3}, 'add') + " | "
            
            link_diplay_verbose = self.tmpl_link(ln, _("Verbose"), weburl_bibedit, 'index',
                                                 {'recID'      : str(recID),
                                                  'format_tag' : 's',
                                                  'temp'       : temp})
            
            link_diplay_marc    = self.tmpl_link(ln, _("MARC"), weburl_bibedit, 'index',
                                                 {'recID'      : str(recID),
                                                  'format_tag' : 'marc',
                                                  'temp'       : temp})                              
                                                     
            if temp != "false" and add != 3:
                link_submit = self.tmpl_link(ln, _("Submit"), weburl_bibedit, 'submit',{'recID' : str(recID)}) + " | "
                
            if add == 3:
                link_add_field = ''
                result = ''
            else:
                link_cancel = self.tmpl_link(ln, _("Cancel"), weburl_bibedit, 'index',{'cancel' : str(recID)}) 
                link_delete = self.tmpl_link(ln, _("Delete"), weburl_bibedit, 'index',{'delete' : str(recID),
                                                                                   'confirm_delete' :1,
                                                                                   'temp' : temp})
                
                result = """ <div align=\"right\">
                               <font size=\"2\">
                                 %(action)s : %(link_submit)s%(link_cancel)s
                                 &nbsp;&nbsp;&nbsp;
                                 %(record)s : %(link_add_field)s%(link_delete)s
                                 &nbsp;&nbsp;&nbsp;
                                 %(display)s : %(link_diplay_verbose)s | %(link_diplay_marc)s
                                 &nbsp;
                               </font>
                             </div> """  % {'action'              : _("Action"),
                                            'record'              : _("Record"),
                                            'display'             : _("Display"),
                                            'link_submit'         : link_submit,
                                            'link_add_field'      : link_add_field,
                                            'link_diplay_verbose' : link_diplay_verbose,
                                            'link_diplay_marc'    : link_diplay_marc,
                                            'link_cancel'         : link_cancel,
                                            'link_delete'         : link_delete}
                                        
        return """ <table bgcolor=\"#ECECEC\" border=\"0\" cellspacing=\"0\">
                     <tr bgcolor=\"#CCCCCC\">
                       <td colspan=\"6\">
                         <b>&nbsp;%(record)s #%(recID)s</b>
                         %(result)s
                       </td>
                     </tr> """ % {'record' : _("Record"),
                                  'recID'  : str(recID),
                                  'result' : result}

        
    def tmpl_table_value(self, ln, recID, temp, tag, field, format_tag, type_table, add, form_add=0):        
        """ Return a field to print in table. """

        if form_add == 0:
        
            subfields = field[0]
            num_field = field[4]
            tag_field = split_tag_to_marc(tag, field[1], field[2])

            if format_tag != 's':
                print_tag_field = tag_field[:-1]

            else:
                tag_field = tag_field[:-1] + '%'

                if get_name_tag(tag_field) != tag_field:
                    print_tag_field = get_name_tag(tag_field)   
                else:
                    print_tag_field = tag_field[:-1]

            len_subfields = len(subfields)

            if type_table == "record" and add != 3:
                print_link_function = self.tmpl_link_function(ln, len_subfields, recID, tag, num_field, format_tag, temp)
                print_tag_form = ''
            else:
                print_link_function = ''
                if add == 1:
                    print_tag_form = " <input type=\"hidden\" value=\"%s\" name=\"tag\"> " \
                                     % get_tag_name(print_tag_field)
                else:
                    print_tag_form = " <input type=\"hidden\" value=\"%s\" name=\"edit_tag\"> " \
                                     % get_tag_name(print_tag_field)

            if add == 1:
                len_subfields += 1
                type_table = "record"

  
            result = """ <td rowspan=\"%(len_subfields)s\" valign=\"top\" align=\"right\">
                            <font size=\"2\">
                              <b>&nbsp;%(print_tag_field)s&nbsp;</b>
                              %(print_tag_form)s
                            </font>
                          </td>
                          %(subfield)s
                          %(print_link_function)s
                     """ % {'len_subfields'       : len_subfields,
                            'print_tag_field'     : print_tag_field,
                            'print_tag_form'      : print_tag_form,
                            'subfield'            : self.tmpl_subfields(ln, temp, recID,
                                                                        subfields[0][0], subfields[0][1],
                                                                        tag_field, format_tag, type_table,
                                                                        0, num_field, len_subfields),
                            'print_link_function' : print_link_function}

            if len_subfields != 1:
                num_value = -1
                for subfield in subfields:
                    num_value += 1
                    if num_value != 0:
                        result += """ <tr>
                                        %s
                                      </tr> """ % self.tmpl_subfields(ln, temp, recID, subfield[0], subfield[1],
                                                                      tag_field, format_tag,
                                                                      type_table, num_value,
                                                                      num_field, len_subfields)
            if add == 1:
                result += """ <tr>
                                %s
                              </tr> """ % self.tmpl_subfields(ln, temp, add=add)
                
        else:
            result = """ <td valign=\"top\" align=\"right\">
                           <font size=\"2\">
                             <form action=\"%(weburl_bibedit)s/index\" method=\"POST\">
                               <input type=\"hidden\" value=\"%(recID)s\" name=\"recID\">
                               <input type=\"hidden\" value=4 name=\"add\">
                               <input type=\"hidden\" value=true name=\"temp\">
                               <input type=\"hidden\" value=\"%(ln)s\" name=\"ln\">
                               <b>
                                 &nbsp;<a name=\"add\">Tag</a>:
                                 <input type=\"text\" name=\"add_tag\"  maxlength=\"3\" size=\"3\">
                                 &nbsp;ind1:
                                 <input type=\"text\" name=\"add_ind1\" maxlength=\"1\" size=\"1\">
                                 &nbsp;ind2:
                                 <input type=\"text\" name=\"add_ind2\" maxlength=\"1\" size=\"1\">
                               </b>
                           </font>
                         </td> """ % {'weburl_bibedit' : weburl_bibedit,
                                      'recID'          : str(recID),
                                      'ln'             : ln}
            
            result += """ 
                          %s
                           """ % self.tmpl_subfields(ln, temp, add=add)
            
        return """ <tr><td></td></tr>                   
                   <tr>
                     %s
                   </tr> """ % result

        
    def tmpl_table_footer(self, ln, type_table, add=0):        
        """ Return a footer of table. """

        _ = gettext_set_language(ln)

        if add == 1 or add == 3:
           button  = _("Save")
        else:
           button  = _("Return to Record")
            
        if type_table != "record" or add == 3:
            form = """   <input class=\"formbutton\" type=\"submit\" value=\"%(button)s\">&nbsp;
                       </form>
                   """ % {'button' : button}
        else:
            form = ''
            
        return """   <tr>
                       <td align=\"right\" colspan=\"6\">
                         %(form)s
                       </td>
                     </tr>
                   </table> """ % {'form' : form}
    

    def tmpl_subfields(self, ln, temp, recID='', tag_subfield='', value='', tag_field='', format_tag='marc',
                       type_table='', num_value='', num_field='', len_subfields='', add=0):        
        """ This function return the content of subfield. """

        if add == 1 or add == 3:
            print_tag_subfield = """ $$&nbsp;<input type=\"text\" name=\"add_subcode\" maxlength=\"1\" size=\"1\"> """
        else:
            if type_table != "record":
                print_tag_subfield = """ $$&nbsp;
                                         <input type=\"text\" value=\"%(tag_subfield)s\" name=\"subcode%(num_value)s\" maxlength=\"1\" size=\"1\">
                                     """ % {'tag_subfield' : tag_subfield,
                                            'num_value'    : str(num_value)}
                
            elif format_tag != 's':
                print_tag_subfield = "$$&nbsp;%s" % tag_subfield
            else:
                print_tag_subfield = "%s%s" % (tag_field[:-1], tag_subfield)
                
                if get_name_tag(print_tag_subfield) != print_tag_subfield:
                    print_tag_subfield = get_name_tag(print_tag_subfield)
                else:
                    print_tag_subfield = "$$&nbsp;%s" % tag_subfield
                
        value = self.tmpl_clean_value(value, "record")
        
        print_value       = ''
        print_old_value   = ''
        print_btn         = ''
        print_bgcolor     = ''
        print_old_subcode = ''
        
        if type_table != "record" or add == 3:
                
            if add == 1 or add == 3:
                print_value = " <input type=\"text\" name=\"add_value\" size=\"115%c\"> " % ('%')
                
            else:
                print_old_subcode = """<input type=\"hidden\" value=\"%(tag_subfield)s\" name=\"old_subcode%(num_value)s\">
                                    """ % {'tag_subfield' : tag_subfield,
                                           'num_value'    : str(num_value)}
                
                print_old_value   = """ <input type=\"hidden\" value=\"%(value)s\" name=\"old_value%(num_value)s\">
                                    """ % {'num_value' : str(num_value),
                                           'value'     : value}
                
                if len(value) < 75:
                    print_value = """ <input type=\"text\" value=\"%(value)s\" name=\"value%(num_value)s\" style=\"width:100%(pourcentage)c;\"> """  % {'num_value'   : str(num_value),
                             'pourcentage' : '%',
                             'value'       : value}
                else:
                    print_value = """ <textarea name=\"value%(num_value)s\" cols=\"70\" rows=\"5\" style=\"width:100%(pourcentage)c;\">%(value)s</textarea> """ \
                                  % {'num_value'   : str(num_value),
                                     'pourcentage' : '%',
                                     'value'       : value}
                    
                if len_subfields > 1:

                   print_btn = "<td>%s</td>" \
                               % self.tmpl_link(ln, "<img border=\"0\" src=\"%s\" alt=\"delete\">" % btn_delete_url,
                                                weburl_bibedit, 'edit',
                                                {'recID'        : str(recID),
                                                 'tag'          : tag_field[:-1]+ tag_subfield,
                                                 'num_field'    : num_field,
                                                 'format_tag'   : format_tag,
                                                 'temp'         : 'true',
                                                 'del_subfield' : 1})           
                
        else:
            print_value = value
            print_bgcolor = " bgcolor=\"#FFFFFF\" "
            
        return """ <td bgcolor=\"#F5F5F5\" align=\"right\" valign=\"top\">
                     <font size=\"2\">&nbsp;%(print_tag_subfield)s&nbsp;</font>
                     %(print_old_subcode)s
                   </td>
                   <td style=\"padding-left:5px; padding-right:5px;\" %(print_bgcolor)s  width=\"700\">
                     <font size=\"2\">
                       %(print_value)s
                     </font>
                       %(print_old_value)s
                   </td>
                   %(print_btn)s  
                   <td></td> """ % {'print_tag_subfield' : print_tag_subfield,
                                    'print_old_subcode'  : print_old_subcode,
                                    'print_bgcolor'      : print_bgcolor,
                                    'print_value'        : print_value,
                                    'print_old_value'    : print_old_value,
                                    'print_btn'          : print_btn}


    def tmpl_link_function(self, ln, len_subfields, recID, tag, num_field, format_tag, temp):        
        """ Print button function to edit and delete information. """

        btn_edit = self.tmpl_link(ln, "<img border=\"0\" src=\"%s\" alt=\"edit\">" % btn_edit_url,
                                  weburl_bibedit, 'edit',
                                  {'recID'        : str(recID),
                                   'tag'          : tag,
                                   'num_field'    : num_field,
                                   'format_tag'   : format_tag,
                                   'temp'         : 'true'})

        btn_delete = self.tmpl_link(ln, "<img border=\"0\" src=\"%s\" alt=\"edit\">" % btn_delete_url,
                                    weburl_bibedit, 'index',
                                    {'recID'      : str(recID),
                                     'delete_tag' : tag,
                                     'num_field'  : num_field,
                                     'format_tag' : format_tag,
                                     'temp'       : 'true'})
                                    
        return """ <td rowspan=\"%(len_subfields)s\" align=\"center\" valign=\"top\">
                     %(btn_edit)s
                   </td>
                   <td rowspan=\"%(len_subfields)s\" align=\"center\" valign=\"top\">
                     %(btn_delete)s
                   </td>
               """ % {'len_subfields' : len_subfields,
                      'btn_edit'      : btn_edit,
                      'btn_delete'    : btn_delete}

    def tmpl_clean_value(self, value, format):        
        """ This function clean value for HTML interface and inverse. """
        
        if format != "html":
            value = value.replace('"', '&quot;')
            value = value.replace('<', '&lt;')
            value = value.replace('>', '&gt;')
            
        else:
            value = value.replace('&quot;', '"')
            value = value.replace('&lt;', '<')
            value = value.replace('&gt;', '>')
            
        return value


    def tmpl_warning_temp_file(self, ln):        
        """ Return a warning message for user who use a temp file. """

        _ = gettext_set_language(ln)
        
        return """ <span style=\"color: #000000;
                                 background: #ffcccc;
                                 padding: 1px;
                                 font-weight: bold;
                                 border-spacing: 3px;
                                 border: 2px solid #990000;\">
                      %(message1)s %(message2)s  
                   </span><br/><br/>
               """ % {'message1' : _("Your changes are TEMPORARY."),
                      'message2' : _("To save this record, please click on submit.")}


    def tmpl_record_choice_box(self, ln, message):        
        """ Return a little for; for choice a record to edit. """

        _ = gettext_set_language(ln)
        
        if message == 1:
            result = """ <span class=\"errorbox\">
                            <b>
                               %(message1)s %(message2)s
                             </b>
                         </span><br/><br/>
                     """ % {'message1' : _("This record doesn't exist."),
                            'message2' : _("Please try another record ID.")}
            
        elif message == 2:
             result = """ <span class=\"errorbox\">
                             <b>
                               %(message1)s %(message2)s
                             </b>
                          </span><br/><br/>
                      """ % {'message1' : _("This record is currently being edited by somebody else."),
                             'message2' : _("Please try to come back later.")}
            
        else:
            result = ''
            
        result += """ <form action=\"%(weburl_bibedit)s/index\"  method=\"POST\">
                        <input type=\"hidden\" value=\"%(ln)s\" name=\"ln\">
                        <table bgcolor=\"#DDDDDD\">
                          <tr><td></td></tr>
                          <tr>
                            <td>
                              &nbsp;%(message1)s <b>%(message2)s</b> %(message3)s:&nbsp;
                              <input name=\"recID\"  value=\"\">
                              <input class=\"formbutton\" type=\"submit\" value=\"%(edit)s\">
                              &nbsp;&nbsp;
                            </td>
                          </tr>
                          <tr><td></td></tr>
                        </table>
                      </form> """ % {'weburl_bibedit' : weburl_bibedit,
                                     'ln'             : ln,
                                     'message1'       : _("Please enter"),
                                     'message2'       : _("record ID"),
                                     'message3'       : _("to edit"),
                                     'edit'           : _("Edit")}
        
        return result

    def tmpl_submit(self, ln):
        """ Return a end message of Bibedit. """

        _ = gettext_set_language(ln)
         
        return """  %(message1)s<br\>
                    %(message2)s<br\><br\>
                    %(message3)s:
                   <a href=\"%(weburl)s/admin/bibedit/index?ln=%(ln)s\">%(link)s</a>.
               """ % {'message1': _("Your modifications have now been submitted."),
                      'message2': _("They will be processed as soon as the task queue is empty."),
                      'message3': _("You can now go back to"),
                      'link'    : _("BibEdit Admin Interface"),
                      'weburl'  : weburl,
                      'ln'      : ln}
    
    def tmpl_deleted(self, ln, message='', recID='', temp='', format_tag=''):
        """ Return a deleted message of Bibedit. """

        _ = gettext_set_language(ln)
        
        if message == 1:
            return """ %(message)s
                       <div style=\"float:left;\">
                         <form action=\"%(weburl_bibedit)s/index?delete=%(recID)s\" method=\"POST\">
                           <input type=\"hidden\" value=\"%(ln)s\" name=\"ln\">
                           <input class=\"formbutton\" type=\"submit\" value=\"%(yes)s\"/>
                         </form>
                       </div>
                       <div style=\"float:left;\">
                         <form action=\"%(weburl_bibedit)s/index?recID=%(recID)s&temp=%(temp)s&format_tag=%(format_tag)s\" method=\"POST\">
                           <input type=\"hidden\" value=\"%(ln)s\" name=\"ln\">
                           <input class=\"formbutton\" type=\"submit\" value=\"%(no)s\"/>
                         </form>
                       </div>
                   """ % {'message'        : _("Do you really want to delete this record ?"),
                          'yes'            : _("yes"),
                          'no'             : _("no"), 
                          'weburl_bibedit' : weburl_bibedit,
                          'recID'          : str(recID),
                          'ln'             : ln,
                          'temp'           : temp,
                          'format_tag'     : format_tag}
        
        else:    
            return """ %(message)s:
                       <a href=\"%(weburl)s/admin/bibedit/index?ln=&(ln)s\">%(link)s</a>.
                   """ % {'message': _("The record as soon deleted when the task queue is empty.You can now go back to"),
                          'link'   : _("BibEdit Admin Interface"),
                          'weburl' : weburl,
                          'ln'     : ln}
                       
    def tmpl_link(self, ln, object, weburl, dest, dict_args={}, ancre=''):
        """ Return a link. """

        list_args = dict_args.items()
        
        if len(list_args) == 0:
            link_args = ''
        else:
            link_args = '?'
            for arg in list_args:
                link_args += "%(name)s=%(value)s&" % {'name'  : str(arg[0]),
                                                      'value' : str(arg[1])} 
            link_args += "ln=%s" % ln
            
        if ancre != '':
            ancre = '#' + ancre
            
        return  """ <a href=\"%(weburl)s/%(dest)s%(args)s%(ancre)s\"> %(object)s </a>
                """ % {'object' : object,
                       'weburl' : weburl,
                       'dest'   : dest,
                       'args'   : link_args,
                       'ancre'  : ancre}
