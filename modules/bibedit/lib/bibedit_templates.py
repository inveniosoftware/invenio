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

from invenio.bibedit_dblayer import *
from invenio.bibedit_config  import *
from invenio.config          import tmpdir, weburl
from invenio.messages        import gettext_set_language, language_list_long

## Link of edit and delete button:
btn_delete_url = "../../../img/iconcross.gif"
btn_edit_url   = "../../../img/iconpen.gif"
weburl_bibedit = "%s/admin/bibedit/bibeditadmin.py" % weburl

class Template:
    
    def tmpl_table_header(self, type_table, recID, temp="false", format_tag='marc',
                          tag='', format_view='s', num_field=None, add=0):        
        """ Return the Header of table. """
        
        start_form = ''
        (tag, ind1,ind2, _) = marc_to_split_tag(tag)
        tag = tag + ind1 + ind2 + "%"
        
        if type_table != "record":

            if add == 1:
                print_input_add_form = " <input type=\"hidden\" value=\"2\" name=\"add\"> "
            else:
                print_input_add_form = ''
                
            print_action_add_subfield = """ %s
                                            <input type=\"hidden\" value=\"%s\" name=\"num_field\">
                                            <br\> """ % (print_input_add_form, str(num_field))
                                            
            if add != 1:
                print_action_add_subfield = """
                    <a href=\"%s/edit?recID=%s&tag=%s&num_field=%s&format_tag=%s&temp=true&add=1\">
                      Add Subfield
                    </a>&nbsp; """ % (weburl_bibedit, str(recID), tag[:3], str(num_field), format_tag)

            if add == 1:
                link_form = "edit"
            else:
                link_form = "index"
                
            result = """ <form action=\"%s/%s\" method=\"POST\">
                           <input type=\"hidden\" value=\"%s\"   name=\"recID\">
                           <input type=\"hidden\" value=\"true\" name=\"temp\">
                         <div align=\"right\">
                           <font size=\"2\">
                           Record:
                           <a href=\"%s/index?cancel=%s\">Cancel</a>
                           &nbsp;&nbsp;&nbsp;
                           Action :
                           %s
                           </font>
                         </div> """ % (weburl_bibedit, link_form, recID, weburl_bibedit, recID, print_action_add_subfield)
                     
        else:
            
            link_submit = ''
            link_add_field = " <a href=\"%s/index?recID=%i&temp=true&add=3&format_tag=%s#add\">Add Field</a> | " \
                             %(weburl_bibedit, recID, format_tag)
            
            if temp != "false" and add != 3:
                link_submit = " <a href=\"%s/submit?recID=%i\">Submit</a> | " %(weburl_bibedit, recID)
            if add == 3:
                link_add_field = ''
                result = ''
            else:
                result = """ <div align=\"right\">
                               <font size=\"2\">
                                 Action :
                                 %s
                                 <a href=\"%s/index?cancel=%s\">Cancel</a>
                                 &nbsp;&nbsp;&nbsp;
                                 Record :
                                 %s
                                 <a href=\"%s/index?confirm_delete=1&delete=%s\">Delete</a> 
                                 &nbsp;&nbsp;&nbsp;
                                 Display : %s | %s
                                 &nbsp;
                               </font>
                             </div> """  % (link_submit,    weburl_bibedit, str(recID),
                                            link_add_field, weburl_bibedit, str(recID),
                                            self.tmpl_link_view("Verbose", recID, temp, "s",    format_view),
                                            self.tmpl_link_view("MARC",    recID, temp, "marc", format_view))
                                        
        return """ <table bgcolor=\"#ECECEC\" border=\"0\" cellspacing=\"0\">
                     <tr bgcolor=\"#CCCCCC\">
                       <td colspan=\"6\">
                         <b>&nbsp;Record #%s</b>
                         %s
                       </td>
                     </tr> """ % (str(recID), result)

        
    def tmpl_table_value(self, recID, temp, tag, field, format_tag, type_table, add, form_add=0):        
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
                print_link_function = self.tmpl_link_function(len_subfields, recID, tag, num_field, format_tag, temp)
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

            ##result = print_tag_field + ":" + str(num_field) + "<br\>" + str(subfields) + "<br\>"    
            result = """ <td rowspan=\"%i\" valign=\"top\" align=\"right\">
                            <font size=\"2\">
                              <b>&nbsp;%s&nbsp;</b>
                              %s
                            </font>
                          </td>
                          %s
                          %s """ % (len_subfields,
                                    print_tag_field,
                                    print_tag_form,
                                    self.tmpl_subfields(temp, recID, subfields[0][0], subfields[0][1],
                                                        tag_field, format_tag, type_table,
                                                        0, num_field, len_subfields),
                                    print_link_function)

            if len_subfields != 1:
                num_value = -1
                for subfield in subfields:
                    num_value += 1
                    if num_value != 0:
                        result += """ <tr>
                                        %s
                                      </tr> """ % self.tmpl_subfields(temp, recID, subfield[0], subfield[1],
                                                                      tag_field, format_tag,
                                                                      type_table, num_value,
                                                                      num_field, len_subfields)
            if add == 1:
                result += """ <tr>
                                %s
                              </tr> """ % self.tmpl_subfields(temp, add=add)
                
        else:
            result = """ <td valign=\"top\" align=\"right\">
                           <font size=\"2\">
                             <form action=\"%s/index\" method=\"POST\">
                               <input type=\"hidden\" value=\"%s\" name=\"recID\">
                               <input type=\"hidden\" value=4 name=\"add\">
                               <input type=\"hidden\" value=true name=\"temp\">
                               <b>
                                 &nbsp;<a name=\"add\">Tag</a>:
                                 <input type=\"text\" name=\"add_tag\"  maxlength=\"3\" size=\"3\">
                                 &nbsp;ind1:
                                 <input type=\"text\" name=\"add_ind1\" maxlength=\"1\" size=\"1\">
                                 &nbsp;ind2:
                                 <input type=\"text\" name=\"add_ind2\" maxlength=\"1\" size=\"1\">
                               </b>
                           </font>
                         </td> """ % (weburl_bibedit, recID)
            
            result += """ 
                          %s
                           """ % self.tmpl_subfields(temp, add=add)
            
        return """ <tr><td></td></tr>                   
                   <tr>
                     %s
                   </tr> """ % result

        
    def tmpl_table_footer(self, type_table, add=0):        
        """ Return a footer of table. """
        
        if type_table != "record" or add == 3:
            form = """   <input class=\"formbutton\" type=\"reset\" value=\"Discard changes\">&nbsp;
                         <input class=\"formbutton\" type=\"submit\" value=\"Save changes\">&nbsp;
                       </form> """
        else:
            form = ''
            
        return """   <tr>
                       <td align=\"right\" colspan=\"6\">
                         %s
                       </td>
                     </tr>
                   </table> """ % form
    

    def tmpl_subfields(self, temp, recID='', tag_subfield='', value='', tag_field='', format_tag='marc',
                       type_table='', num_value='', num_field='', len_subfields='', add=0):        
        """ This function return the content of subfield. """

        if add == 1 or add == 3:
            print_tag_subfield = """ $$&nbsp;<input type=\"text\" name=\"add_subcode\" maxlength=\"1\" size=\"1\"> """
        else:
            if type_table != "record":
                print_tag_subfield = """ $$&nbsp;<input type=\"text\" value=\"%s\" name=\"subcode%s\" maxlength=\"1\" size=\"1\"> """ % (tag_subfield, str(num_value))
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
                print_old_subcode = " <input type=\"hidden\" value=\"%s\" name=\"old_subcode%s\"> " \
                                     % (tag_subfield, str(num_value))
                print_old_value   = " <input type=\"hidden\" value=\"%s\" name=\"old_value%s\"> " \
                                     % (value, str(num_value))
                
                if len(value) < 75:
                    print_value = """ <input type=\"text\" value=\"%s\" name=\"value%s\" style=\"width:100%c;\"> """ \
                                  % (value, str(num_value), '%')
                else:
                    print_value = """ <textarea name=\"value%s\" cols=\"70\" rows=\"10\" style=\"width:100%c;\">%s
                                      </textarea> """ % (str(num_value), '%', value)
                    
                if len_subfields > 1:
                    print_btn = """
                            <td>
                              <a href=\"%s/edit?recID=%s&tag=%s&num_field=%s&format_tag=%s&temp=true&del_subfield=1\">
                                <img border=\"0\" src=\"%s\">
                              </a>
                            </td> """ % (weburl_bibedit, str(recID), tag_field[:-1]+ tag_subfield,
                                         num_field, format_tag, btn_delete_url)
            
                
        else:
            print_value = value
            print_bgcolor = " bgcolor=\"#FFFFFF\" "
            
        return """ <td bgcolor=\"#F5F5F5\" align=\"right\" valign=\"top\">
                     <font size=\"2\">&nbsp;%s&nbsp;</font>
                     %s
                   </td>
                   <td style=\"padding-left:5px; padding-right:5px;\" %s  width=\"700\">
                     <font size=\"2\">
                       %s
                     </font>
                       %s
                   </td>
                   %s  
                   <td></td> """ % (print_tag_subfield, print_old_subcode, print_bgcolor, print_value,
                                    print_old_value, print_btn)


    def tmpl_link_function(self, len_subfields, recID, tag, num_field, format_tag, temp):        
        """ Print button function to edit and delete information. """
        
        btn_edit = """ <a href=\"%s/edit?recID=%i&tag=%s&num_field=%s&format_tag=%s&temp=true\">
                         <img border=\"0\" src=\"%s\" alt=\"edit\">
                       </a> """ % (weburl_bibedit, recID, tag, num_field, format_tag, btn_edit_url)
        
        btn_delete = """ <a href=\"%s/index?recID=%i&delete_tag=%s&num_field=%s&format_tag=%s&temp=true\">
                              <img border=\"0\" src=\"%s\" alt=\"delete\">
                         </a> """ % (weburl_bibedit, recID, tag, num_field, format_tag, btn_delete_url)
        
        return """ <td rowspan=\"%i\" align=\"center\" valign=\"top\">
                     %s
                   </td>
                   <td rowspan=\"%i\" align=\"center\" valign=\"top\">
                     %s
                   </td> """ % (len_subfields, btn_edit, len_subfields, btn_delete)
    

    def tmpl_link_view(self, name, recID, temp, format_tag, format_view='s'):        
        """ Print link ti change user display. """
        
        return """ <a href=\"%s/index?recID=%i&temp=%s&format_tag=%s\">%s</a> """ \
               % (weburl_bibedit, recID, temp, format_tag, name)


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


    def tmpl_warning_temp_file(self):        
        """ Return a warning message for user who use a temp file. """
        
        return """ <span style=\"color: #000000;
                                 background: #ffcccc;
                                 padding: 1px;
                                 font-weight: bold;
                                 border-spacing: 3px;
                                 border: 2px solid #990000;\">
                     Your changes are TEMPORARY.  To save this record, please click on submit.
                   </span><br/><br/> """ 


    def tmpl_record_choice_box(self, message):        
        """ Return a little for; for choice a record to edit. """

        if message == 1:
            result = """ <span class=\"errorbox\">
                            <b>This record doesn't exist.  Please try another record ID.</b>
                         </span><br/><br/>  """ 
                
        elif message == 2:
             result = """ <span class=\"errorbox\">
                             <b>This record is currently being edited by somebody else.  Please try to come back later.</b>
                          </span><br/><br/>  """
            
        else:
            result = ''
            
        result += """ <form action=\"%s/index\"  method=\"POST\">
                        <table bgcolor=\"#DDDDDD\">
                          <tr><td></td></tr>
                          <tr>
                            <td>
                              &nbsp;Please enter <b>record ID</b> to edit:&nbsp;
                              <input name=\"recID\"  value=\"\">
                              <input class=\"formbutton\" type=\"submit\" value=\"Edit\">
                              &nbsp;&nbsp;
                            </td>
                          </tr>
                          <tr><td></td></tr>
                        </table>
                      </form> """ % weburl_bibedit
        
        return result

    def tmpl_submit(self):        
        """ Return a end message of Bibedit. """
        
        return """ Your modifications have now been submitted.  They will be processed as soon as the task queue is empty.<br\>
                   <br\>You can now go back to <a href=\"%s/admin/bibedit/index\">BibEdit Admin Interface</a>.""" % (weburl)

    def tmpl_deleted(self, message='', recID=''):
        """ Return a deleted message of Bibedit. """

        if message == 1:
            return """ Do you really want to delete this record ? <br\>
                       <a href=\"%s/index?delete=%s\">YES</a>&nbsp;&nbsp;&nbsp;<a href=\"\">NO</a>
                   """ % (weburl_bibedit, str(recID))
            
        else:    
            return """ The record as soon deleted when the task queue is empty.<br\>
                        <br\>You can now go back to <a href=\"%s/admin/bibedit/index\">
                        BibEdit Admin Interface</a>.""" % (weburl)

 
