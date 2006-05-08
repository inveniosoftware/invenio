# -*- coding: utf-8 -*-

import cgi
from invenio.config import weburl, cdslang
from invenio.websubmitadmin_config import websubmitadmin_weburl

def create_html_table_from_tuple(tableheader=None, tablebody=None, start="", end=""):
    """Create a table from a tuple or a list.
       @param header:      optional header for the columns (MUST be a list of header titles)
       @param tablebody:   table body (rows - tuple of tuples)
       @param start:       text to be added in the beginning, most likely beginning of a form
       @param end:         text to be added in the end, most likely end of a form.
    """
    if type(tableheader) is None:
        tableheader = ()
    if type(tablebody) is None:
        tablebody = ()
    ## determine table cells alignment based upon first row alignment
    align = []
    try:
        if type(tablebody[0]) in [int, long]: 
            align = ['admintdright']
        elif type(tablebody[0]) in [str, dict]:
            align = ['admintdleft']
        else:
            for item in tablebody[0]:
                if type(item) is int:
                    align.append('admintdright')
                else:
                    align.append('admintdleft')
    except IndexError:
        ## Empty tablebody
        pass

    ## table header row:
    tblstr = ""
    for hdr in tableheader:
        tblstr += """  <th class="adminheader">%s</th>\n""" % (hdr,)
    if tblstr != "":
        tblstr = """ <tr>\n%s</tr>\n""" % (tblstr, )

    tblstr = start + """<table class="admin_wvar_nomargin">\n""" + tblstr

    ## table body
    if len(tablebody) > 0:
        for row in tablebody:
            tblstr += """ <tr>\n"""
            if type(row) not in [int, long, str, dict]:
                for i in range(len(row)):
                    tblstr += """<td class="%s">%s</td>\n""" % (align[i], row[i])
            else:
                tblstr += """  <td class="%s">%s</td>\n""" % (align[0], row)
            tblstr += """ </tr>\n"""
    else:
        # Empty tuple of table data - display message:
        tblstr += """<tr>
         <td class="admintdleft" colspan="%s"><span class="info">None</span></td>
        </tr>
        """ % (len(tableheader),)

    tblstr += """</table>\n"""
    tblstr += end
    return tblstr

def create_html_select_list(select_name, option_list, selected_values="", default_opt="", multiple="", list_size="", css_style="", css_class=""):
    """Make a HTML "select" element from the parameters passed.
       @param select_name: Name given to the HTML "select" element
       @param option_list: a tuple of tuples containing the options (their values, followed by their
        display text).  Thus: ( (opt_val, opt_txt), (opt_val, opt_txt) )
        It is also possible to provide a tuple of single-element tuples in the case when it is not desirable
        to have different option text to the value, thus: ( (opt_val,), (opt_val,) ).
       @param selected_value: can be a list/tuple of strings, or a single string/unicode string.  Treated as
        the "selected" values for the select list's options.  E.g. if a value in the "option_list" param was
        "test", and the "selected_values" parameter contained "test", then the test option would appear as
        follows: '<option value="test" selected>'.
       @param default_opt: The default option (value and displayed text) for the select list. If left blank, there
        will be no default option, and the first "natural" option will appear first in the list.
        If the value of "default_opt" is a string, then this string will be used both as the value and the displayed
        text of the default option.  If the value of "default_opt" is a tuple/list, then the first option will be
        used as the option "value", and the second will be used as the option "displayed text".  In the case that
        the list/tuple length is only 1, the value will be used for both option "value" and "displayed text".
       @param multiple: shall this be a multiple select box? If present, select box will be marked as "multiple".
       @param list_size: the size for a multiple select list. If mutiple is present, then this optional size can
        be provided.  If not provided, the list size attribute will automatically be given the value of the list
        length, up to 30.
       @param css_style: A string: any additional CSS style information to be placed as the select element's "style"
        attribute value.
       @param css_class: A string: any class value for CSS.
       @return: a string containing the completed HTML Select element
    """
    ## sanity checking:
    if type(css_style) not in (str, unicode):
        css_style = ""
    if type(option_list) not in (list, tuple):
        option_list = ()
    txt = """\n   <select name="%s"%s""" % ( cgi.escape(select_name, 1),
                                             (multiple != "" and " multiple") or ("")
                                           )
    if multiple != "":
        ## Size attribute for multiple-select list
        if (type(list_size) is str and list_size.isdigit()) or type(list_size) is int:
            txt += """ size="%s\"""" % (list_size,)
        else:
            txt += """ size="%s\"""" % ( (len(option_list) <= 30 and str(len(option_list))) or ("30"),)
    if css_style != "":
        txt += """ style="%s\"""" % (cgi.escape(css_style, 1),)
    txt += """>\n"""
    if default_opt != "":
        if type(default_opt) in (str, unicode):
            ## default_opt is a string - use its value as both option value and displayed text
            txt += """    <option value="%(deflt_opt)s">%(deflt_opt)s</option>\n""" % {'deflt_opt' : cgi.escape(default_opt, 1)}
        elif type(default_opt) in (list, tuple):
            try:
                txt += """    <option value="%(deflt_opt)s">""" % {'deflt_opt' : cgi.escape(default_opt[0], 1) }
                try:
                    txt += """%(deflt_opt)s""" % {'deflt_opt' : cgi.escape(default_opt[1], 1) }
                except IndexError:
                    txt += """%(deflt_opt)s""" % {'deflt_opt' : cgi.escape(default_opt[0], 1) }
                txt += """</option>\n"""
            except IndexError:
                ## seems to be an empty list - there will be no default opt
                pass
    for option in option_list:
        try:
            txt += """    <option value="%(option_val)s\"""" % { 'option_val' : cgi.escape(option[0], 1) }
            if type(selected_values) in (list, tuple):
                txt += """%(option_selected)s""" % \
                 { 'option_selected' : (option[0] in selected_values and " selected") or ("") }
            elif type(selected_values) in (str, unicode) and selected_values != "":
                txt += """%(option_selected)s""" % \
                 { 'option_selected' : (option[0] == selected_values and " selected") or ("") }
            try:
                txt += """>%(option_txt)s</option>\n""" % { 'option_txt' : cgi.escape(option[1], 1) }
            except IndexError:
                txt += """>%(option_txt)s</option>\n""" % { 'option_txt' : cgi.escape(option[0], 1) }
        except IndexError:
            ## empty option tuple - skip
            pass
    txt += """   </select>\n"""
    return txt


## def create_html_select_list(select_name, option_list, selected_values="", multiple="", list_size=""):
##     """Make a HTML "select" element from the parameters passed.
##        @param select_name: Name given to the HTML "select" element
##        @param option_list: a tuple of tuples containing the options (their values, followed by their
##         display text).  Thus: ( (opt_val, opt_txt), (opt_val, opt_txt) )
##         It is also possible to provide a tuple of single-element tuples in the case when it is not desirable
##         to have different option text to the value, thus: ( (opt_val,), (opt_val,) ).
##        @param selected_value: can be a list/tuple of strings, or a single string/unicode string.  Treated as
##         the "selected" values for the select list's options.  E.g. if a value in the "option_list" param was
##         "test", and the "selected_values" parameter contained "test", then the test option would appear as
##         follows: '<option value="test" selected>'.
##        @param multiple: shall this be a multiple select box? If present, select box will be marked as "multiple".
##        @param list_size: the size for a multiple select list. If mutiple is present, then this optional size can
##         be provided.  If not provided, the list size attribute will automatically be given the value of the list
##         length, up to 30.
##        @return: a string containing the completed HTML Select element
##     """
##     ## sanity checking:
##     if type(option_list) not in (list, tuple):
##         option_list = ()
##     txt = """\n   <select name="%s"%s""" % ( cgi.escape(select_name, 1),
##                                              (multiple != "" and " multiple") or ("")
##                                            )
##     if multiple != "":
##         ## Size attribute for multiple-select list
##         if (type(list_size) is str and list_size.isdigit()) or type(list_size) is int:
##             txt += """ size="%s\"""" % (list_size,)
##         else:
##             txt += """ size="%s\"""" % ( (len(option_list) <= 30 and str(len(option_list))) or ("30"),)
##     txt += """>
##     <option value="NO_VALUE">Select:</option>\n"""
##     for option in option_list:
##         try:
##             txt += """    <option value="%(option_val)s\"""" % { 'option_val' : cgi.escape(option[0], 1) }
##             if type(selected_values) in (list, tuple):
##                 txt += """%(option_selected)s""" % \
##                  { 'option_selected' : (option[0] in selected_values and " selected") or ("") }
##             elif type(selected_values) in (str, unicode) and selected_values != "":
##                 txt += """%(option_selected)s""" % \
##                  { 'option_selected' : (option[0] == selected_values and " selected") or ("") }
##             try:
##                 txt += """>%(option_txt)s</option>\n""" % { 'option_txt' : cgi.escape(option[1], 1) }
##             except IndexError:
##                 txt += """>%(option_txt)s</option>\n""" % { 'option_txt' : cgi.escape(option[0], 1) }
##         except IndexError:
##             ## empty option tuple - skip
##             pass
##     txt += """   </select>\n"""
##     return txt


class Template:
    """CDS Invenio Template class for creating Web interface"""
    def tmpl_navtrail(self, ln=cdslang):
        """display the navtrail, e.g.:
           Home > Admin Area > WebSubmit Administration > Available WebSubmit Actions
           @param title: the last part of the navtrail. Is not a link
           @param ln: language
           return html formatted navtrail
        """
        nav_h1 =  '<a class="navtrail" href="%s/admin/">Admin Area</a>'
        nav_h1 += ' &gt; <a class="navtrail" href="%s/admin/websubmit/websubmitadmin.py/">WebSubmit Admin</a>'
        return  nav_h1 % (weburl, weburl)

    def _create_adminbox(self, header="", datalist=[], cls="admin_wvar"):
        """Create an adminbox  table around the main data on a page - row based.
           @param header: the header for the "adminbox".
           @param datalist: contents of the "body" to be encapsulated by the "adminbox".
           @param cls: css-class to format the look of the table.
           @return: the "adminbox" and its contents.
        """
        if len(datalist) == 1:
            per = "100"
        else:
            per = "75"
        output = """
       <table class="%s" width="95%%">
""" % (cls,)
        output += """
        <thead>
         <tr>
          <th class="adminheaderleft" colspan="%s">
           %s
          </th>
         </tr>
        </thead>
        <tbody>""" % (len(datalist), header)
        output += """
         <tr>
          <td style="vertical-align: top; margin-top: 5px; width: %s;">
           %s
          </td>
""" % (per+'%', datalist[0])
        if len(datalist) > 1:
            output += """
          <td style="vertical-align: top; margin-top: 5px; width: %s;">
           %s
          </td>""" % ('25%', datalist[1])
        output += """
         </tr>
        </tbody>
       </table>
    """
        return output

    def _create_user_message_string(self, user_msg):
        """Create and return a string containing any message(s) to be shown to the user.
           In particular, these messages are generally info/warning messages.
           @param user_msg: The message to be shown to the user.  This parameter can have either a
            string value (in the case where one message is to be shown to the user), or a list/tuple
            value, where each value in the list is a string containing the message to be shown to the
            user.
           @return: EITHER: a string containing a HTML "DIV" section, which contains the message(s) to be
            displayed to the user.  In the case where there were multiple messages, each message will be
            placed on its own line, by means of a "<br />" tag.
                    OR: an empty string - in the case that the parameter "user_msg" was an empty string.
        """
        user_msg_str = ""
        user_msg_str_end = ""
        if type(user_msg) in (str, unicode):
            if user_msg == "":
                user_msg = ()
            else:
                user_msg = (user_msg,)
        if len(user_msg) > 0:
            user_msg_str += """<div align="center">\n"""
            user_msg_str_end = """</div><br />\n"""
        for msg in user_msg:
            user_msg_str += """<span class="info">%s</span><br />\n""" % (cgi.escape(msg, 1),)
        user_msg_str += user_msg_str_end
        return user_msg_str

    def _create_websubmitadmin_main_menu_header(self):
        """Create the main menu to be displayed on WebSubmit Admin pages."""
        menu_body = """
        <div>
        <table>
         <tr>
          <td>0.&nbsp;<small><a href="%(adminurl)s/showall">Show all</a></small></td>
          <td>&nbsp;1.&nbsp;<small><a href="%(adminurl)s/doctypelist">Available Document Types</a></small></td>
          <td>&nbsp;2.&nbsp;<small><a href="%(adminurl)s/doctypeadd">Add New Document Type</a></small></td>
          <td>&nbsp;3.&nbsp;<small><a href="%(adminurl)s/doctyperemove">Remove Document Type</a></small></td>
          <td>&nbsp;4.&nbsp;<small><a href="%(adminurl)s/actionlist">Available Actions</a></small></td>
          <td>&nbsp;5.&nbsp;<small><a href="%(adminurl)s/jschecklist">Available Checks</a></small></td>
         </tr>
         <tr>
          <td>6.&nbsp;<small><a href="%(adminurl)s/elementlist">Available Element descriptions</a></small></td>
          <td>&nbsp;7.&nbsp;<small><a href="%(adminurl)s/functionlist">Available Functions</a></small></td>
          <td>&nbsp;8.&nbsp;<small><a href="%(adminurl)s/cataloguelist">Organise Main Page</a></small></td>
          <td colspan=2>&nbsp;9.&nbsp;<small><a href="%(adminurl)s/">WebSubmit Admin Guide</a></small></td>
         </tr>
        </table>
        </div>
        <br />
        """ % {'adminurl' : websubmitadmin_weburl}
        return self._create_adminbox(header="Main Menu", datalist=[menu_body])

    def _element_display_preview(self,
                                 elname="",
                                 eltype="",
                                 elsize="",
                                 elrows="",
                                 elcols="",
                                 elval="",
                                 elfidesc=""
                                ):
        """Return a form containing a preview of an element, based on the values of the parameters provided
           @param elname: element name
           @param eltype: element type (e.g. text, user-defined, etc)
           @param elsize: element size (e.g. for text input element)
           @param elrows: number of rows (e.g. for textarea element)
           @param elcols: number of columns (e.g. for textarea element)
           @param elval: value of element (e.g. for text input element)
           @param elfidesc: description for element (e.g. for user-defined element)
           @return: string of HTML making up a preview of the element in a table
        """
        ## Open a dummy form and table in which to display a preview of the element
        body = """<div><br />
        <form name="dummyeldisplay" action="%(adminurl)s/elementlist">
        <table class="admin_wvar" align="center">
        <thead>
         <tr>
          <th class="adminheaderleft" colspan="1">
           Element Preview:
          </th>
         </tr>
        </thead>
        <tbody>
        <tr>
        <td>
        <br />&nbsp;&nbsp;
        """ % {'adminurl' : websubmitadmin_weburl}
        ## Based on element type, display a preview of element:
        try:
            preview = {"D" : """&nbsp;&nbsp;%s&nbsp;&nbsp;""" % (elfidesc,),
                       "F" : """<input type="file" %sname="dummyfile">""" % \
                           ( (elsize != "" and """size="%s" """ % (cgi.escape(elsize, 1),) ) or (""),),
                       "H" : """<span class="info">Hidden Input. Contains Following Value: %s</span>""" % (cgi.escape(elval, 1),),
                       "I" : """<input type="text" %sname="dummyinput" value="%s">""" % \
                         ( (elsize != "" and """size="%s" """ % (cgi.escape(elsize, 1),) ) or (""), cgi.escape(elval, 1)),
                       "R" : """<span class="info">Cannot Display Response Element - See Element Description</span>""",
                       "S" : """&nbsp;%s&nbsp;""" % (elfidesc,),
                       "T" : """<textarea name="dummytextarea" %s%s></textarea>""" % \
                           ( (elrows != "" and """rows="%s" """ % (cgi.escape(elrows, 1),) ) or (""),
                             (elcols != "" and """cols="%s" """ % (cgi.escape(elcols, 1),) ) or (""),)
                      }[eltype]
        except KeyError:
            ## Unknown element type - display warning:
            preview = """<span class="info">Element Type not Recognised - Cannot Display</span>"""
        body += preview
        ## Close dummy form and preview table:
        body += """&nbsp;&nbsp;<br />
        </td>
        </tr>
        </tbody>
        </table>
        </form>
        </div>"""
        return body

    def tmpl_display_addelementform(self,
                                    elname="",
                                    elmarccode="",
                                    eltype="",
                                    elsize="",
                                    elrows="",
                                    elcols="",
                                    elmaxlength="",
                                    elval="",
                                    elfidesc="",
                                    elmodifytext="",
                                    elcookie="",
                                    elcd="",
                                    elmd="",
                                    perform_act="elementadd",
                                    user_msg="",
                                    el_use_tuple=""
                                   ):
        """Display Web form used to add a new element to the database
           @param elname: element name
           @param elmarccode: marc code of element
           @param eltype: element type (e.g. text, user-defined, etc)
           @param elsize: element size (e.g. for text input element)
           @param elrows: number of rows (e.g. for textarea element)
           @param elcols: number of columns (e.g. for textarea element)
           @param elmaxlength: maximum length of a text input field
           @param elval: value of element (e.g. for text input element)
           @param elfidesc: description for element (e.g. for user-defined element)
           @param elmodifytext: element's modification text
           @param elcookie: Is a cookie to be set for the element?
           @param elcd: creation date of element
           @param elmd: last modification date of element
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           @param el_use_tuple:
           @return: HTML page body.
        """
        ## First, get a rough preview of the element:
        output = ""
        etypes = {"D" : "User Defined Input", "F" : "File Input", "H" : "Hidden Input", "I" : "Text Input", \
                  "R" : "Response", "S" : "Select Box", "T" : "Text Area Element"}
        etypeids = etypes.keys()
        etypeids.sort()
        body_content = ""
        if user_msg != "":
            ## Status message to display:
            output += """<div align="center"><span class="info">%s</span></div><br />""" % (cgi.escape(user_msg, 1),)
        if perform_act != "elementadd":
            body_content += self._element_display_preview(elname=elname, eltype=eltype, elsize=elsize, \
                                                         elrows=elrows, elcols=elcols, elval=elval, elfidesc=elfidesc)
        else:
            body_content += "<br />"

        body_content += """<form method="post" action="%(websubadmin_url)s/%(perform_action)s">""" \
                       % {'websubadmin_url': websubmitadmin_weburl, 'perform_action': perform_act}
        body_content += """
        <table width="100%%" class="admin_wvar">
         <thead>
         <tr>
          <th class="adminheaderleft" colspan="2">
           Enter Element Details:
          </th>
         </tr>
         </thead>
         <tbody>
         <tr>
          <td width="20%%">&nbsp;</td>
          <td width="80%%">&nbsp;</td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Element Name:</span></td>
          <td width="80%%">"""
        if perform_act == "elementadd":
            body_content += """
          <input type="text" size=30 name="elname" value="%(el_name)s" />""" % {'el_name' : cgi.escape(elname, 1)}
        else:
            body_content += """<span class="info">%(el_name)s</span><input type="hidden" name="elname" value="%(el_name)s" />""" \
                            % {'el_name' : cgi.escape(elname, 1)}
        body_content += """</td>
         </tr>"""
        if elcd != "" and elcd != None:
            body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Creation Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(elcd), 1),)
        if elmd != "" and elmd != None:
                body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Last Modification Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(elmd), 1),)
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Modification Text:</span></td>
          <td width="80%%"><input type="text" size=90 name="elmodifytext" value="%(el_modifytext)s" /></td>
         </tr>""" % {'el_modifytext' : cgi.escape(elmodifytext, 1)}

        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Element Type:</span></td>
          <td width="80%%">
          <select name="eltype">
           <option value="NONE_SELECTED">Select:</option>\n"""
        for itm in etypeids:
            body_content += """           <option value="%s"%s>%s</option>\n""" % \
                            ( itm, (eltype == itm and " selected" ) or (""), cgi.escape(etypes[itm], 1) )
        body_content += """          </select>
          </td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Marc Code:</span></td>
          <td width="80%%"><input type="text" size=15 name="elmarccode" value="%(el_marccode)s" /></td>
         </tr>
        """ % {'el_marccode' : cgi.escape(elmarccode, 1)}
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Size <i><small>(text elements)</small></i>:</span></td>
          <td width="80%%"><input type="text" size=10 name="elsize" value="%(el_size)s" /></td>
         </tr>
        """ % {'el_size' : cgi.escape(elsize, 1)}
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">No. Rows <i><small>(textarea elements)</small></i>:</span></td>
          <td width="80%%"><input type="text" size=6 name="elrows" value="%(el_rows)s" /></td>
         </tr>
        """ % {'el_rows' : cgi.escape(elrows, 1)}
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">No. Columns <i><small>(textarea elements)</small></i>:</span></td>
          <td width="80%%"><input type="text" size=6 name="elcols" value="%(el_cols)s" /></td>
         </tr>
        """ % {'el_cols' : cgi.escape(elcols, 1)}
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Maximum Length <i><small>(text elements)</small></i>:</span></td>
          <td width="80%%"><input type="text" size=6 name="elmaxlength" value="%(el_maxlength)s" /></td>
         </tr>
        """ % {'el_maxlength' : cgi.escape(elmaxlength, 1)}
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Value <i><small>(text/hidden elements)</small></i>:</span></td>
          <td width="80%%"><input type="text" size=90 name="elval" value="%(el_val)s" /></td>
         </tr>
        """ % {'el_val' : cgi.escape(elval, 1)}
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Element Description <i><small>(e.g. user-defined elements)</small></i>:</span></td>
          <td width="80%%"><textarea cols=100 rows=30 name="elfidesc" wrap="nowarp">%(el_fidesc)s</textarea></td>
         </tr>
        """ % {'el_fidesc' : cgi.escape(elfidesc, 1)}
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Sets Cookie:</span></td>
          <td width="80%%"><select name="elcookie">
            <option value="0"%s>No</option>
            <option value="1"%s>Yes</option>
           </select>
          </td>
         </tr>
        """ % ( (elcookie == "0" and " selected" ) or (""),
                (elcookie == "1" and " selected" ) or ("")
              )
        body_content += """
         <tr>
          <td width="20%%">&nbsp;</td>
          <td width="80%%"><input name="elcommit" class="adminbutton" type="submit" value="Save Details" /></td>
         </tr>
         </tbody>
        </table>
        </form>
        """
        ## If there is information about which submission pages use this element, display it:
        if type(el_use_tuple) is tuple and len(el_use_tuple) > 0:
            body_content += """<br /><br />
            <table width="100%%" class="admin_wvar">
             <thead>
             <tr>
              <th class="adminheaderleft" colspan="2">
               Element Usage:
              </th>
             </tr>
             </thead>
             <tbody>
             <tr>
              <td width="20%%">&nbsp;</td>
              <td width="80%%">"""
            for usecase in el_use_tuple:
                try:
                    body_content += """<small>&nbsp;%(subname)s: Page %(pageno)s</small><br />\n""" % {'subname' : usecase[0], 'pageno' : usecase[1]}
                except KeyError, e:
                    pass
            body_content += """&nbsp;</td>
             </tr>
             </tbody>
            </table>
            """

        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Element Details:", datalist=[body_content])
        return output

    def tmpl_display_addactionform(self,
                                   actid="",
                                   actname="",
                                   working_dir="",
                                   status_text="",
                                   perform_act = "actionadd",
                                   cd="",
                                   md="",
                                   user_msg=""):
        """Display web form used to add a new action to Websubmit.
           @param actid: Value of the "sactname" (action id) parameter of the Websubmit action.
           @param actname: Value of the "lactname" (long action name) parameter of the Websubmit action.
           @param working_dir: Value of the "dir" (action working/archive directory) parameter of the Websubmit action.
           @param status_text: Value of the "statustext" (action status text) parameter of the WebSubmit action.
           @param perform_act: action for form (minus websubmitadmin base url)
           @param cd: Creation date of action.
           @param md: Modification date of action.
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           @return: HTML page body.
        """
        output = ""
        if user_msg != "":
            ## Status message to display:
            output += """<div align="center"><span class="info">%s</span></div><br>""" % (cgi.escape(user_msg, 1),)
        body_content = """<form method="post" action="%(websubadmin_url)s/%(perform_action)s">""" \
                       % {'websubadmin_url': websubmitadmin_weburl, 'perform_action': perform_act}
        body_content += """
        <table width="90%%">
         <tr>
          <td width="20%%"><span class="adminlabel">Action Code:</span></td>
          <td width="80%%">"""
        if perform_act == "actionadd":
            body_content += """
          <input type="text" size="6" name="actid" value="%(ac_id)s" />""" % {'ac_id' : cgi.escape(actid, 1)}
        else:
            body_content += """<span class="info">%(ac_id)s</span><input type="hidden" name="actid" value="%(ac_id)s" />""" \
                            % {'ac_id' : cgi.escape(actid, 1)}
        body_content += """</td>
         </tr>"""
        if "" not in (cd, md):
            if cd != None:
                body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Creation Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(cd), 1),)
            if md != None:
                body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Last Modification Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(md), 1), )
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Action Description:</span></td>
          <td width="80%%"><input type="text" size="60" name="actname" value="%(ac_name)s" /></td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Action dir:</span></td>
          <td width="80%%"><input type="text" size="40" name="working_dir" value="%(w_dir)s" /></td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Action Status Text:</span></td>
          <td width="80%%"><input type="text" size="60" name="status_text" value="%(s_txt)s" /></td>
         </tr>""" % {'ac_name' : cgi.escape(actname, 1), 'w_dir' : cgi.escape(working_dir, 1), \
                     's_txt' : cgi.escape(status_text, 1)}
        body_content += """
         <tr>
          <td width="20%%">&nbsp;</td>
          <td width="80%%"><input name="actcommit" class="adminbutton" type="submit" value="Save Details" /></td>
         </tr>
        </table>
        </form>
        """
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Enter Action Details:", datalist=[body_content])
        return output


    def tmpl_display_addjscheckform(self,
                                   chname="",
                                   chdesc="",
                                   perform_act = "jscheckadd",
                                   cd="",
                                   md="",
                                   user_msg=""):
        """Display web form used to add a new Check to Websubmit.
           @param chname: Value of the "chname" (check ID/name) parameter of the WebSubmit Check.
           @param chdesc: Value of the "chdesc" (check description - i.e. JS code) parameter of the
                           WebSubmit Check.
           @param perform_act: action for form (minus websubmitadmin base url)
           @param cd: Creation date of check.
           @param md: Modification date of check.
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           @return: HTML page body.
        """
        output = ""
        if user_msg != "":
            ## Status message to display:
            output += """<div align="center"><span class="info">%s</span></div><br>""" % (cgi.escape(user_msg, 1),)
        body_content = """<form method="post" action="%(websubadmin_url)s/%(perform_action)s">""" \
                       % {'websubadmin_url': websubmitadmin_weburl, 'perform_action': perform_act}
        body_content += """
        <table width="90%%">
         <tr>
          <td width="20%%"><span class="adminlabel">Check Name:</span></td>
          <td width="80%%">"""

        if perform_act == "jscheckadd":
            body_content += """
          <input type="text" size="15" name="chname" value="%(ch_name)s" />""" % {'ch_name' : cgi.escape(chname, 1)}
        else:
            body_content += """<span class="info">%(ch_name)s</span><input type="hidden" name="chname" value="%(ch_name)s" />""" \
                            % {'ch_name' : cgi.escape(chname, 1)}
        body_content += """</td>
         </tr>"""
        if "" not in (cd, md):
            if cd != None:
                body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Creation Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(cd), 1),)
            if md != None:
                body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Last Modification Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(md), 1),)
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Check Description:</span></td>
          <td width="80%%">
           <textarea cols="90" rows="22" name="chdesc">%(ch_descr)s</textarea>
          </td>
         </tr>
         <tr>
          <td width="20%%">&nbsp;</td>
          <td width="80%%"><input name="chcommit" class="adminbutton" type="submit" value="Save Details" /></td>
         </tr>
        </table>
        </form>
        """ % {'ch_descr' : cgi.escape(chdesc, 1)}
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Enter Action Details:", datalist=[body_content])
        return output


##     def tmpl_display_adddoctype_form(self, doctype="", doctypename="", doctypedescr="", clonefrom="", alldoctypes="", user_msg=""):
##         """TODO : DOCSTRING"""
##         output = ""
##         body_content = ""
##         output += self._create_user_message_string(user_msg)
##         if type(alldoctypes) not in (list, tuple):
##             ## bad list of document types - reset
##             alldoctypes = ()
##         body_content += """<form method="get" action="%(websubadmin_url)s/doctypeadd">""" \
##                    % { 'websubadmin_url' : websubmitadmin_weburl }
##         body_content += """
##         <table width="90%%">
##          <tr>
##           <td width="20%%"><span class="adminlabel">Document Type ID:</span></td>
##           <td width="80%%"><input type="text" size="15" name="doctype" value="%(doctype_id)s" /></td>
##          </tr>
##          <tr>
##           <td width="20%%"><span class="adminlabel">Document Type Name:</span></td>
##           <td width="80%%"><input type="text" size="60" name="doctypename" value="%(doctype_name)s" /></td>
##          </tr>
##          <tr>
##           <td width="20%%"><span class="adminlabel">Document Type Description:</span></td>
##           <td width="80%%"><textarea name="doctypedescr" cols="60" rows="8">%(doctype_description)s</textarea></td>
##          </tr>
##          <tr>
##           <td width="20%%"><span class="adminlabel">Document Type to Clone:</span></td>
##           <td width="80%%">%(doctype_select_list)s</td>
##          </tr>
##          <tr>
##           <td width="20%%">&nbsp;</td>
##           <td width="80%%"><input name="doctypeaddcommit" class="adminbutton" type="submit" value="Save Details" /></td>
##          </tr>
##         </table>
##         </form>
##         """ % { 'doctype_id' : cgi.escape(doctype, 1),
##                 'doctype_name' : cgi.escape(doctypename, 1),
##                 'doctype_description' : cgi.escape(doctypedescr, 1),
##                 'doctype_select_list' : create_html_select_list(select_name="clonefrom", option_list=alldoctypes, selected_values=clonefrom, default_opt=('None', 'Select:'))
##               }

##         output += self._create_websubmitadmin_main_menu_header()
##         output += self._create_adminbox(header="Add a new Document Type:", datalist=[body_content])
##         return output

        

    def tmpl_display_addfunctionform(self,
                                     funcname="",
                                     funcdescr="",
                                     func_parameters=None,
                                     all_websubmit_func_parameters=None,
                                     perform_act="functionadd",
                                     user_msg=""):
        """Display web form used to add a new function to Websubmit.
           @param funcname: Value of the "function" (unique function name) parameter
           @param chdesc: Value of the "description" (function textual description) parameter
           @param perform_act: action for form (minus websubmitadmin base url)
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           @return: HTML page body.
        """
        if type(func_parameters) not in (list, tuple):
            ## bad parameters list - reset
            func_parameters = ()
        if type(all_websubmit_func_parameters) not in (list, tuple):
            ## bad list of function parameters - reset
            all_websubmit_func_parameters = ()

        output = ""
        if user_msg != "":
            ## Status message to display:
            output += """<div align="center"><span class="info">%s</span></div><br>""" % (cgi.escape(user_msg, 1),)

        body_content = """<form method="post" action="%(websubadmin_url)s/%(perform_action)s">""" \
                       % {'websubadmin_url' : websubmitadmin_weburl, 'perform_action': perform_act}

        ## Function Name and description:
        body_content += """<br />
        <table width="100%%" class="admin_wvar">
         <thead>
         <tr>
          <th class="adminheaderleft" colspan="2">
           %sFunction Details:
          </th>
         </tr>
         </thead>
         <tbody>
         <tr>
          <td width="20%%">&nbsp;</td>
          <td width="80%%">&nbsp;</td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Function Name:</span></td>
          <td width="80%%">""" % ((funcname != "" and cgi.escape(funcname, 1) + " ") or (""), )
        if perform_act == "functionadd" and funcname == "":
            body_content += """
           <input type="text" size="30" name="funcname" />"""
        else:
            body_content += """<span class="info">%(func_name)s</span><input type="hidden" name="funcname" value="%(func_name)s" />""" \
                            % {'func_name' : cgi.escape(funcname, 1)}
        body_content += """</td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Function Description:</span></td>
          <td width="80%%"><input type="text" size="90" name="funcdescr" value="%(func_descr)s" />
         </tr>""" % {'func_descr' : cgi.escape(funcdescr, 1)}
        body_content += """
         <tr>
          <td width="20%%" colspan="2">&nbsp;</td>
         </tr>
         <tr>
          <td width="20%%" colspan="2"><input name="%s" class="adminbutton" type="submit" value="Save Details" /></td>
         </tr>
         </tbody>
        </table>""" % ( ((perform_act == "functionadd" and funcname == "") and "funcaddcommit") or ("funcdescreditcommit"), )
        if funcname not in  ("", None):
            body_content += """<br />
            <table width="100%%" class="admin_wvar">
             <thead>
             <tr>
              <th class="adminheaderleft">
               Parameters for Function %(func_name)s:
              </th>
             </tr>
             </thead>
             <tbody>
             <tr>
              <td><br />""" % {'func_name' : cgi.escape(funcname, 1)}
            params_tableheader = ["Parameter", "&nbsp;"]
            params_tablebody = []
            for parameter in func_parameters:
                params_tablebody.append( ("<small>%s</small>" % (cgi.escape(parameter[0], 1),),
                                          """<small><a href="%(websubadmin_url)s/functionedit?funcparamdelcommit=funcparamdelcommit""" \
                                          """&amp;funcname=%(func_name)s&amp;funceditdelparam=%(delparam_name)s">delete</a></small>""" \
                                          % { 'websubadmin_url' : websubmitadmin_weburl,
                                              'func_name' : cgi.escape(funcname, 1),
                                              'delparam_name' : cgi.escape(parameter[0], 1)
                                            }
                                         ) )
            body_content += create_html_table_from_tuple(tableheader=params_tableheader, tablebody=params_tablebody)
            body_content += """</td>
             </tr>
             </tbody>
            </table>
            <br />"""

            ## Add a parameter?
            body_content += """<table width="100%%" class="admin_wvar">
             <thead>
             <tr>
              <th class="adminheaderleft" colspan="2">
               Add Parameter to Function %(func_name)s:
              </th>
             </tr>
             </thead>
             <tbody>""" % {'func_name' : cgi.escape(funcname, 1)}
            body_content += """
             <tr>
              <td width="20%%"><span class="adminlabel">Add Parameter:</span></td>
              <td width="80%%"><small>Select a parameter to add to function:</small>&nbsp;%s&nbsp;&nbsp;""" \
                % (create_html_select_list(select_name="funceditaddparam", option_list=all_websubmit_func_parameters),)
            body_content += """<small>-Or-</small>&nbsp;&nbsp;<small>Enter a new parameter:</small>&nbsp;&nbsp;<input type="text" """ \
             + """name="funceditaddparamfree" size="15" /><input name="funcparamaddcommit" class="adminbutton" """ \
             + """type="submit" value="Add" /></td>
             </tr>
             </tbody>
            </table>"""

        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Enter Function Details:", datalist=[body_content])
        return output


    def tmpl_display_function_usage(self, funcname, func_usage, user_msg=""):
        """Display a table containing the details of a function's usage in the various actions of the various doctypes.
           Displayed will be information about the document type and action, and the score and step at which
           the function is called within that action.
           @param funcname: function name.
           @param func_usage: A tuple of tuples, each containing details of the function usage:
               (doctype, docname, function-step, function-score, action id, action name)
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           @return: HTML page body.
        """
        output = ""
        body_content = ""
        header = ["Doctype", "&nbsp;", "Action", "&nbsp;", "Score", "Step", "Show Details"]
        tbody = []
        
        if user_msg != "":
            ## Status message to display:
            output += """<div align="center"><span class="info">%s</span></div><br>""" % (cgi.escape(user_msg, 1),)

        body_content += "<br />"
        for usage in func_usage:
            tbody.append( ("<small>%s</small>" % (cgi.escape(usage[0], 1),),
                           "<small>%s</small>" % (cgi.escape(usage[1], 1),),
                           "<small>%s</small>" % (cgi.escape(usage[2], 1),),
                           "<small>%s</small>" % (cgi.escape(usage[3], 1),),
                           "<small>%s</small>" % (cgi.escape(usage[4], 1),),
                           "<small>%s</small>" % (cgi.escape(usage[5], 1),),
                           """<small><a href="%s/XXXXX">Show</a></small>""" % (websubmitadmin_weburl,)
                          )
                        )
        body_content += create_html_table_from_tuple(tableheader=header, tablebody=tbody)
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="""Usage of the "%s" Function:""" % (cgi.escape(funcname, 1),), datalist=[body_content])
        return output


    def tmpl_display_allactions(self,
                                actions,
                                user_msg=""):
        """Create the page body used for displaying all Websubmit actions.
           @param actions: A tuple of tuples containing the action id, and the action name (actid, actname).
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           @return: HTML page body.
        """
        output = ""
        if user_msg != "":
            ## Status message to display:
            output += """<div align="center"><span class="info">%s</span></div><br>""" % (cgi.escape(user_msg, 1),)
        body_content = """<div>
<table>
"""
        for action in actions:
            body_content += """<tr>
<td align="left">&nbsp;&nbsp;<a href="%s/actionedit?actid=%s">%s: %s</a></td>
</tr>
""" % (websubmitadmin_weburl, cgi.escape(action[0], 1), cgi.escape(action[0], 1), cgi.escape(action[1], 1))
        body_content += """</table>"""
        ## Button to create new action:
        body_content += """<br><form action="%s/actionadd" METHOD="post"><input class="adminbutton" type="submit" value="Add Action" /></form>""" \
                        % (websubmitadmin_weburl,)
        body_content += """</div>"""
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Select an Action:", datalist=[body_content])
        return output


    def tmpl_display_alldoctypes(self,
                                doctypes,
                                user_msg = ""):
        """Create the page body used for displaying all Websubmit document types.
           @param doctypes: A tuple of tuples containing the doctype id, and the doctype name (docid, docname).
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           return: HTML page body.
        """
        output = ""
        output += self._create_user_message_string(user_msg)
        body_content = """<div>
<table>
"""
        for doctype in doctypes:
            body_content += """<tr>
<td align="left">&nbsp;&nbsp;<a href="%s/doctypeconfigure?doctype=%s">**%s**&nbsp;&nbsp;&nbsp;%s</a></td>
</tr>
""" % (websubmitadmin_weburl, cgi.escape(doctype[0], 1), cgi.escape(doctype[0], 1), cgi.escape(doctype[1], 1))
        body_content += """</table>"""
        ## Button to create new action:
        body_content += """<br><form action="%s/doctypeadd" METHOD="post"><input class="adminbutton" type="submit" value="Add New Doctype" /></form>""" \
                        % (websubmitadmin_weburl,)
        body_content += """</div>"""
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Select a Document Type:", datalist=[body_content])
        return output


    def tmpl_display_alljschecks(self,
                                 jschecks,
                                 user_msg = ""):
        """Create the page body used for displaying all Websubmit JavaScript Checks.
           @param jschecks: A tuple of tuples containing the check name (chname, which is unique for
                            each check.)
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           return: HTML page body.
        """
        output = ""
        if user_msg != "":
            ## Status message to display:
            output += """<div align="center"><span class="info">%s</span></div><br>""" % (cgi.escape(user_msg, 1),)
        body_content = """<div>
<table>
"""
        for jscheck in jschecks:
            body_content += """<tr>
<td align="left">&nbsp;&nbsp;<a href="%s/jscheckedit?chname=%s">%s</a></td>
</tr>
""" % (websubmitadmin_weburl, cgi.escape(jscheck[0], 1), cgi.escape(jscheck[0], 1))
        body_content += """</table>"""
        ## Button to create new action:
        body_content += """<br><form action="%s/jscheckadd" METHOD="post"><input class="adminbutton" type="submit" value="Add Check" /></form>""" \
                        % (websubmitadmin_weburl,)
        body_content += """</div>"""
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Select a Checking Function:", datalist=[body_content])
        return output


    def tmpl_display_allfunctions(self,
                                  functions,
                                  user_msg = ""):
        """Create the page body used for displaying all Websubmit functions.
           @param functions: A tuple of tuples containing the function name, and the function
                             description (function, description).
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           return: HTML page body.
        """
        output = ""
        header = ["Function Name", "View Usage", "Edit Details"]
        if user_msg != "":
            ## Status message to display:
            output += """<div align="center"><span class="info">%s</span></div><br>""" % (cgi.escape(user_msg, 1),)
        body_content = """<div><br />\n"""
        tbody = []
        for function in functions:
            tbody.append(("&nbsp;&nbsp;%s" % (cgi.escape(function[0], 1),),
                          """<small><a href="%s/functionusage?funcname=%s">View Usage</a></small>""" % \
                              (websubmitadmin_weburl, cgi.escape(function[0], 1)),
                          """<small><a href="%s/functionedit?funcname=%s">Edit Details</a></small>""" % \
                          (websubmitadmin_weburl, cgi.escape(function[0], 1))
                         ))
        button_newfunc = """<form action="%s/functionadd" METHOD="post">
          <input class="adminbutton" type="submit" value="Add New Function" />
          </form>""" % (websubmitadmin_weburl,)
        body_content += create_html_table_from_tuple(tableheader=header, tablebody=tbody, end=button_newfunc)
        body_content += """</div>"""
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="WebSubmit Functions:", datalist=[body_content])
        return output


    def tmpl_display_allelements(self,
                                 elements,
                                 user_msg = ""):
        """Create the page body used for displaying all Websubmit elements.
           @param elements: A tuple of tuples containing the element name (name).
           @param user_msg: Any message to be displayed on screen, such as a status report for the last task, etc.
           return: HTML page body.
        """
        output = ""
        if user_msg != "":
            ## Status message to display:
            output += """<div align="center"><span class="info">%s</span></div><br>""" % (cgi.escape(user_msg, 1),)
        body_content = """<div>
<table style="align:center;">
"""
        for element in elements:
            body_content += """<tr>
<td align="left">&nbsp;&nbsp;<a href="%s/elementedit?elname=%s">%s</a></td>
</tr>
""" % (websubmitadmin_weburl, cgi.escape(element[0], 1), cgi.escape(element[0], 1))
        body_content += """</table>"""
        ## Button to create new action:
        body_content += """<br><form action="%s/elementadd" METHOD="post"><input class="adminbutton" type="submit" value="Add New Element" /></form>""" \
                        % (websubmitadmin_weburl,)
        body_content += """</div>"""
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Select an Element:", datalist=[body_content])
        return output

    def tmpl_display_delete_doctype_form(self, doctype="", alldoctypes="", user_msg=""):
        """TODO: DOCSTRING"""
        output = ""
        output += self._create_user_message_string(user_msg)
        body_content = "<div>"
        if doctype not in ("", None) and type(doctype) in (str, unicode):
            ## Display the confirmation message:
            body_content += """<form method="get" action="%(websubadmin_url)s/doctyperemove">""" \
                            """<input type="hidden" name="doctype" value="%(doc_type)s" />\n""" \
                            % { 'websubadmin_url' : websubmitadmin_weburl, 'doc_type' : cgi.escape(doctype, 1) }
            body_content += """<div><span class="info"><i>Really</i> remove document type "%s" and all of its configuration details?</span> <input name="doctypedeleteconfirm" class="adminbutton\""""\
             """type="submit" value="Confirm" /></div>\n</form>\n""" % (cgi.escape(doctype,) )
        else:
            ## just display the list of document types to delete:
            if type(alldoctypes) not in (list, tuple):
                ## bad list of document types - reset
                alldoctypes = ()
            body_content += """<form method="get" action="%(websubadmin_url)s/doctyperemove">""" \
                       % { 'websubadmin_url' : websubmitadmin_weburl }
            body_content += """
            <table width="100%%" class="admin_wvar">
             <thead>
             <tr>
              <th class="adminheaderleft">
               Select a Document Type to Remove:
              </th>
             </tr>
             </thead>
             <tbody>
             <tr>
              <td>&nbsp;&nbsp;%s&nbsp;&nbsp;<input name="doctypedelete" class="adminbutton" type="submit" value="Remove" /></td>
             </tr>
            </table>
            </form>""" \
                % (create_html_select_list(select_name="doctype", option_list=alldoctypes),)

        body_content += """</div>"""
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Remove a Document Type:", datalist=[body_content])
        return output

## DOCTYPE CONFIGURE

    def tmpl_display_submission_clone_form(self,
                                           doctype,
                                           action,
                                           clonefrom_list,
                                           user_msg=""
                                          ):
        if type(clonefrom_list) not in (list, tuple):
            clonefrom_list = ()
        output = ""
        output += self._create_user_message_string(user_msg)
        body_content = """<form method="get" action="%(websubadmin_url)s/%(formaction)s">""" \
                   % { 'websubadmin_url' : websubmitadmin_weburl , 'formaction' : cgi.escape("doctypeconfigure", 1) }
        body_content += """
        <input type="hidden" name="doctype" value="%(doctype)s" />
        <input type="hidden" name="action" value="%(action)s" />
        <table width="90%%">
         <tr>
          <td width="20%%"><span class="adminlabel">Clone from Document Type:</span></td>
          <td width="80%%">
           %(clonefrom)s
          </td>
         </tr>
         <tr>
          <td width="20%%">&nbsp;</td>
          <td width="80%%">
           <input name="doctypesubmissionaddclonechosen" class="adminbutton" type="submit" value="Continue" />&nbsp;
           <input name="doctypesubmissionaddclonechosencancel" class="adminbutton" type="submit" value="Cancel" />&nbsp;
          </td>
         </tr>
        </table>
        </form>""" % { 'doctype'   : cgi.escape(doctype, 1),
                       'action'    : cgi.escape(action, 1),
                       'clonefrom' : create_html_select_list(select_name="doctype_cloneactionfrom",
                                                             option_list=clonefrom_list,
                                                             default_opt=("None", "Do not clone from another Document Type/Submission"),
                                                             css_style="margin: 5px 10px 5px 10px;"
                                                            )
                     }
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Add Submission '%s' to Document Type '%s':" % (action, doctype),
                                        datalist=[body_content])
        return output

    def tmpl_display_delete_doctypesubmission_form(self, doctype="", action="", user_msg=""):
        """TODO: DOCSTRING"""
        output = ""
        output += self._create_user_message_string(user_msg)
        body_content = """<div>"""
        ## Display the confirmation message:
        body_content += """<form method="get" action="%(websubadmin_url)s/%(formaction)s">""" \
                        """<input type="hidden" name="doctype" value="%(doctype)s" />\n""" \
                        """<input type="hidden" name="action" value="%(action)s" />\n""" \
                        % { 'websubadmin_url' : websubmitadmin_weburl,
                            'formaction'      : "doctypeconfigure",
                            'doctype'         : cgi.escape(doctype, 1),
                            'action'          : cgi.escape(action, 1)
                          }
        body_content += """<div><span class="info"><i>Really</i> remove the Submission "%s" and all related details from Document Type "%s"?</span> <input name="doctypesubmissiondeleteconfirm" class="adminbutton" """ \
                        """type="submit" value="Confirm" /></div>\n</form>\n""" % (cgi.escape(action, 1), cgi.escape(doctype, 1) )

        body_content += """</div>"""
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="""Delete Submission "%s" from Document Type "%s"\"""" % (action, doctype), datalist=[body_content])
        return output

    def tmpl_display_submissiondetails_form(self,
                                            doctype,
                                            action,
                                            displayed="",
                                            buttonorder="",
                                            statustext="",
                                            level="",
                                            score="",
                                            stpage="",
                                            endtxt="",
                                            cd="",
                                            md="",
                                            user_msg="",
                                            perform_act="doctypeconfigure",
                                            saveaction="edit"
                                           ):
        output = ""
        output += self._create_user_message_string(user_msg)
        body_content = """<form method="get" action="%(websubadmin_url)s/%(action)s">""" \
                   % { 'websubadmin_url' : websubmitadmin_weburl , 'action' : cgi.escape(perform_act, 1) }
        body_content += """
        <table width="90%%">"""

        if cd not in ("", None):
            body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Creation Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(cd), 1),)
        if md not in ("", None):
            body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Last Modification Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(md), 1),)

        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Submission Displayed on Start Page:</span></td>
          <td width="80%%">
           <select name="displayed">
            <option value="Y"%s>Yes</option>
            <option value="N"%s>No</option>
           </select>
          </td>
         </tr>""" % ( (displayed == "Y" and " selected") or (""),
                      (displayed == "N" and " selected") or ("")
                    )

        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Button Order:</span></td>
          <td width="80%%">
           <input type="text" size="4" name="buttonorder" value="%(buttonorder)s" />
          </td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Status Text:</span></td>
          <td width="80%%">
           <input type="text" size="35" name="statustext" value="%(statustext)s" />
          </td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Level:</span></td>
          <td width="80%%">
           <input type="text" size="4" name="level" value="%(level)s" />
          </td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Score:</span></td>
          <td width="80%%">
           <input type="text" size="4" name="score" value="%(score)s" />
          </td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Stpage:</span></td>
          <td width="80%%">
           <input type="text" size="4" name="stpage" value="%(stpage)s" />
          </td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">End Text:</span></td>
          <td width="80%%">
           <input type="text" size="35" name="endtxt" value="%(endtxt)s" />
          </td>
         </tr>
         <tr>
          <td width="20%%">&nbsp;</td>
          <td width="80%%">
           <input type="hidden" name="doctype" value="%(doctype)s" />
           <input type="hidden" name="action" value="%(action)s" />
           <input name="%(savebutton)s" class="adminbutton" type="submit" value="Save Details" />
           &nbsp;
           <input name="doctypesubmissiondetailscancel" class="adminbutton" type="submit" value="Cancel" />
          </td>
         </tr>
        </table>
        </form>
        """ % { 'doctype'     : cgi.escape(doctype, 1),
                'action'      : cgi.escape(action, 1),
                'displayed'   : cgi.escape(displayed, 1),
                'buttonorder' : cgi.escape(buttonorder, 1),
                'statustext'  : cgi.escape(statustext, 1),
                'level'       : cgi.escape(level, 1),
                'score'       : cgi.escape(score, 1),
                'stpage'      : cgi.escape(stpage, 1),
                'endtxt'      : cgi.escape(endtxt, 1),
                'cd'          : cgi.escape(cd, 1),
                'md'          : cgi.escape(md, 1),
                'savebutton'  : ((saveaction == "edit" and "doctypesubmissioneditdetailscommit") or ("doctypesubmissionadddetailscommit"))
              }
               
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Enter Details of '%s' Submission of '%s' Document Type:" % (action, doctype),
                                        datalist=[body_content])
        return output

    def tmpl_display_doctypedetails_form(self, doctype="", doctypename="", doctypedescr="", cd="", md="", clonefrom="", \
                                     alldoctypes="", user_msg="", perform_act="doctypeadd"):
        """TODO : DOCSTRING"""
        output = ""
        body_content = ""
        if perform_act == "doctypeadd":
            formheader = "Add a new Document Type:"
        else:
            formheader = "Edit Document Type Details:"
        output += self._create_user_message_string(user_msg)
        if type(alldoctypes) not in (list, tuple):
            ## bad list of document types - reset
            alldoctypes = ()
        body_content += """<form method="get" action="%(websubadmin_url)s/%(action)s">""" \
                   % { 'websubadmin_url' : websubmitadmin_weburl , 'action' : cgi.escape(perform_act, 1) }
        body_content += """
        <table width="90%%">
         <tr>
          <td width="20%%"><span class="adminlabel">Document Type ID:</span></td>
          <td width="80%%">"""
        if perform_act == "doctypeadd":
            body_content += """<input type="text" size="15" name="doctype" value="%(doctype_id)s" />""" \
                            % {'doctype_id' : cgi.escape(doctype, 1)}
        else:
            body_content += """<span class="info">%(doctype_id)s</span><input type="hidden" name="doctype" value="%(doctype_id)s" />""" \
                            % {'doctype_id' : cgi.escape(doctype, 1)}
        body_content += """</td>
         </tr>"""

        if perform_act != "doctypeadd":
            if cd not in ("", None):
                body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Creation Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(cd), 1),)
            if md not in ("", None):
                body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Last Modification Date:</span></td>
          <td width="80%%"><span class="info">%s</span></td>
         </tr>""" % (cgi.escape(str(md), 1), )
        body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Document Type Name:</span></td>
          <td width="80%%"><input type="text" size="60" name="doctypename" value="%(doctype_name)s" /></td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Document Type Description:</span></td>
          <td width="80%%"><textarea name="doctypedescr" cols="60" rows="8">%(doctype_description)s</textarea></td>
         </tr>"""  % { 'doctype_name' : cgi.escape(doctypename, 1),
                       'doctype_description' : cgi.escape(doctypedescr, 1)
                     }

        if perform_act == "doctypeadd":
            body_content += """
         <tr>
          <td width="20%%"><span class="adminlabel">Document Type to Clone:</span></td>
          <td width="80%%">%(doctype_select_list)s</td>
         </tr>""" % { 'doctype_select_list' :
                       create_html_select_list(select_name="clonefrom",
                                               option_list=alldoctypes,
                                               selected_values=clonefrom,
                                               default_opt=('None', 'Select:')
                                              )
                    }
        body_content += """
         <tr>
          <td width="20%%">&nbsp;</td>
          <td width="80%%">
           <input name="doctypedetailscommit" class="adminbutton" type="submit" value="Save Details" />"""
        if perform_act != "doctypeadd":
            ## add a cancel button if this is not a call to add a new document type:
            body_content += """
           &nbsp;
           <input name="doctypedetailscommitcancel" class="adminbutton" type="submit" value="cancel" />"""
        body_content += """
          </td>
         </tr>
        </table>
        </form>\n"""

        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header=formheader, datalist=[body_content])
        return output

    def _tmpl_configire_doctype_overview_create_doctype_details(self, doctype="", doctypename="", doctypedescr="",
                                                                doctype_cdate="", doctype_mdate="", perform_act="doctypeconfigure"
                                                               ):
        """Display the details of a document type"""
        txt = """
        <table class="admin_wvar" rules="rows" width="100%%">
         <thead>
         <tr style="border-bottom: hidden">
         <th class="adminheaderleft" colspan="2">
           %(doctype_id)s Document Type Details:
          </th>
         </tr>
         </thead>
         <tbody>
         <tr style="border-top: hidden; border-bottom: hidden">
          <td width="20%%">&nbsp;</td>
          <td width="80%%">&nbsp;</td>
         </tr>
         <tr>
          <td width="20%%" style="border-bottom: hidden"><span class="adminlabel">Document Type ID:</span></td>
          <td width="80%%"><span class="info">%(doctype_id)s</span></td>
         </tr>
         <tr>
         <td width="20%%" style="border-bottom: hidden"><span class="adminlabel">Creation Date:</span></td>
          <td width="80%%"><span class="info">%(doctype_cdate)s</span></td>
         </tr>
         <tr>
         <td width="20%%" style="border-bottom: hidden"><span class="adminlabel">Modification Date:</span></td>
          <td width="80%%"><span class="info">%(doctype_mdate)s</span></td>
         </tr>
         <tr>
         <td width="20%%" style="border-top: hidden; border-bottom: hidden"><span class="adminlabel">Document Type Name:</span></td>
          <td width="80%%"><span>%(doctype_name)s</span></td>
         </tr>
         <tr style="border-bottom: hidden">
         <td width="20%%" style="border-top: hidden"><span class="adminlabel">Document Type Description:</span></td>
          <td width="80%%"><span>%(doctype_descr)s</span></td>
         </tr>
         <tr style="border-top: hidden">
          <td colspan="2">
           <form method="post" action="%(websubadmin_url)s/%(performaction)s">
           <input name="doctype" type="hidden" value="%(doctype_id)s" />
           <input name="doctypedetailsedit" class="adminbutton" type="submit" value="Edit Details" />
          </form>
          </td>
         </tr>
         </tbody>
        </table>\n""" % { 'doctype_id' : cgi.escape(doctype, 1),
                          'doctype_cdate' : "%s" % ((doctype_cdate not in ("", None) and cgi.escape(str(doctype_cdate), 1)) or (""),),
                          'doctype_mdate' : "%s" % ((doctype_mdate not in ("", None) and cgi.escape(str(doctype_mdate), 1)) or (""),),
                          'doctype_name' : cgi.escape(doctypename, 1),
                          'doctype_descr' : doctypedescr,
                          'performaction' : cgi.escape(perform_act, 1),
                          'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                        }
        return txt

    def _tmpl_configure_doctype_overview_create_categories_view(self,
                                                                doctype="",
                                                                doctype_categories="",
                                                                perform_act="doctypeconfigure"
                                                               ):
        """Display the details of the categories for a given document type"""
        ## sanity checking for categories list:
        if type(doctype_categories) not in (list, tuple):
            doctype_categories = ()
        txt = """
        <table class="admin_wvar" width="100%%">
         <thead>
         <tr>
         <th class="adminheaderleft">
           Categories of Document Type %(doctype_id)s:
          </th>
         </tr>
         </thead>
         <tbody>
         <tr>
          <td><br />""" % { 'doctype_id' : cgi.escape(doctype, 1) }
        modify_categ_txt = ""
        try:
            categs_tableheader = ["Categ ID", "Description", "&nbsp;", "&nbsp;"]
            categs_tablebody = []
            for categ in doctype_categories:
                categs_tablebody.append( ("%s" % (cgi.escape(categ[0], 1),),
                                          "%s" % (cgi.escape(categ[1], 1),),
                                          """<form class="hyperlinkform" method="get" action="%(websubadmin_url)s/%(performaction)s">""" \
                                          """<input class="hyperlinkformHiddenInput" name="doctype" value="%(doctype)s" type""" \
                                          """="hidden" />""" \
                                          """<input class="hyperlinkformHiddenInput" name="categid" value="%(category)s" type""" \
                                          """="hidden" />""" \
                                          """<input type="submit" name="doctypecategoryedit" value="edit" """\
                                          """class="hyperlinkformSubmitButton" />""" \
                                          """</form>""" % { 'doctype' : cgi.escape(doctype, 1),
                                                            'category' : cgi.escape(str(categ[0]), 1),
                                                            'performaction' : cgi.escape(perform_act, 1),
                                                            'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                                                          },
                                          """<form class="hyperlinkform" method="get" action="%(websubadmin_url)s/%(performaction)s">""" \
                                          """<input class="hyperlinkformHiddenInput" name="doctype" value="%(doctype)s" type""" \
                                          """="hidden" />""" \
                                          """<input class="hyperlinkformHiddenInput" name="categid" value="%(category)s" type""" \
                                          """="hidden" />""" \
                                          """<input type="submit" name="doctypecategorydelete" value="delete" """\
                                          """class="hyperlinkformSubmitButton" />""" \
                                          """</form>""" % { 'doctype' : cgi.escape(doctype, 1),
                                                            'category' : cgi.escape(str(categ[0]), 1),
                                                            'performaction' : cgi.escape(perform_act, 1),
                                                            'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                                                          }
                                         ) )
            txt += create_html_table_from_tuple(tableheader=categs_tableheader, tablebody=categs_tablebody)
        except IndexError:
            ## categs tuple was not in expected format ((sname, lname), (sname, lname)[, ...])
            txt += """<span class="info">Unable to correctly display categories</span>"""
        txt += """</td>
         </tr>
         <tr>
          <td><br />
          </td>
         </tr>"""

        ## form to add a new category:
        txt += """
         <tr>
          <td>
           <span class="adminlabel">Add a new Category:</span><br />
           <form method="post" action="%(websubadmin_url)s/%(formaction)s">
            <input name="doctype" type="hidden" value="%(doctype)s" />
            <small style="color: navy;">ID:&nbsp;</small>
            <input style="margin: 5px 10px 5px 10px;" name="categid" type="text" size="10" />&nbsp;
            <small style="color: navy;">Description:&nbsp;</small>
            <input style="margin: 5px 10px 5px 10px;" name="categdescr" type="text" size="25" />&nbsp;
            <input name="doctypecategoryadd" class="adminbutton" type="submit" value="Save Category" />
           </form>
          </td>
         </tr>
         </tbody>
        </table>""" % { 'formaction' : cgi.escape(perform_act, 1),
                        'doctype' : cgi.escape(doctype, 1),
                        'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                      }
        return txt

    def _tmpl_configure_doctype_overview_create_submissions_view(self,
                                                                 doctype="",
                                                                 doctype_submissions="",
                                                                 add_actions_list=None,
                                                                 perform_act="doctypeconfigure"
                                                                ):
        """Display the details of the submissions for a given document type"""
        ## sanity checking for submissions list:
        if type(doctype_submissions) not in (list, tuple):
            doctype_submissions = ()
        if type(add_actions_list) not in (list, tuple):
            add_actions_list = ()
        txt = """
        <table class="admin_wvar" width="100%%">
         <thead>
         <tr>
         <th class="adminheaderleft">
           Submissions of Document Type %(doctype_id)s:
          </th>
         </tr>
         </thead>
         <tbody>
         <tr>
          <td><br />""" % { 'doctype_id' : cgi.escape(doctype, 1) }

        try:
            submissions_tableheader = ["Action", "Creation<br />Date", "Modification<br />Date", "Displayed?", "No.<br />Pages", \
                                       "Button<br />Order", "Status<br />Text", "Level", "Score", "Stpage", "End<br />Text", \
                                       "View Submission<br />Interface", "View Submission<br />Functions", \
                                       "Edit Submission<br />Details", "Delete<br />Submission"]
            submissions_tablebody = []
            for subm in doctype_submissions:
                submissions_tablebody.append( ("%s" % (cgi.escape(str(subm[2]), 1),),
                                               "%s" % (cgi.escape(str(subm[5]), 1),),
                                               "%s" % (cgi.escape(str(subm[6]), 1),),
                                               "%s" % (cgi.escape(str(subm[3]), 1),),
                                               "%s" % (cgi.escape(str(subm[4]), 1),),
                                               "%s" % (cgi.escape(str(subm[7]), 1),),
                                               "%s" % (cgi.escape(str(subm[8]), 1),),
                                               "%s" % (cgi.escape(str(subm[9]), 1),),
                                               "%s" % (cgi.escape(str(subm[10]), 1),),
                                               "%s" % (cgi.escape(str(subm[11]), 1),),
                                               "%s" % (cgi.escape(str(subm[12]), 1),),
                                               """<form class="hyperlinkform" method="get" action="%(websubadmin_url)s/%(formaction)s">""" \
                                               """<input class="hyperlinkformHiddenInput" name="doctype" value="%(doctype)s" type""" \
                                               """="hidden" />""" \
                                               """<input class="hyperlinkformHiddenInput" name="action" value="%(action)s" type""" \
                                               """="hidden" />""" \
                                               """<input type="submit" name="viewSubmissionInterface" value="view interface" """\
                                               """class="hyperlinkformSubmitButton" />""" \
                                               """</form>""" % { 'doctype' : cgi.escape(doctype, 1),
                                                                 'action' : cgi.escape(str(subm[2]), 1),
                                                                 'formaction' : cgi.escape(perform_act, 1),
                                                                 'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                                                               },
                                               """<form class="hyperlinkform" method="get" action="%(websubadmin_url)s/%(formaction)s">""" \
                                               """<input class="hyperlinkformHiddenInput" name="doctype" value="%(doctype)s" type""" \
                                               """="hidden" />""" \
                                               """<input class="hyperlinkformHiddenInput" name="action" value="%(action)s" type""" \
                                               """="hidden" />""" \
                                               """<input type="submit" name="viewSubmissionFunctions" value="view functions" """\
                                               """class="hyperlinkformSubmitButton" />""" \
                                               """</form>""" % { 'doctype' : cgi.escape(doctype, 1),
                                                                 'action' : cgi.escape(str(subm[2]), 1),
                                                                 'formaction' : cgi.escape(perform_act, 1),
                                                                 'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                                                               },
                                               """<form class="hyperlinkform" method="get" action="%(websubadmin_url)s/%(formaction)s">""" \
                                               """<input class="hyperlinkformHiddenInput" name="doctype" value="%(doctype)s" type""" \
                                               """="hidden" />""" \
                                               """<input class="hyperlinkformHiddenInput" name="action" value="%(action)s" type""" \
                                               """="hidden" />""" \
                                               """<input type="submit" name="doctypesubmissionedit" value="edit submission" """\
                                               """class="hyperlinkformSubmitButton" />""" \
                                               """</form>""" % { 'doctype' : cgi.escape(doctype, 1),
                                                                 'action' : cgi.escape(str(subm[2]), 1),
                                                                 'formaction' : cgi.escape(perform_act, 1),
                                                                 'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                                                               },
                                               """<form class="hyperlinkform" method="get" action="%(websubadmin_url)s/%(formaction)s">""" \
                                               """<input class="hyperlinkformHiddenInput" name="doctype" value="%(doctype)s" type""" \
                                               """="hidden" />""" \
                                               """<input class="hyperlinkformHiddenInput" name="action" value="%(action)s" type""" \
                                               """="hidden" />""" \
                                               """<input type="submit" name="doctypesubmissiondelete" value="delete submission" """\
                                               """class="hyperlinkformSubmitButton" />""" \
                                               """</form>""" % { 'doctype' : cgi.escape(doctype, 1),
                                                                 'action' : cgi.escape(str(subm[2]), 1),
                                                                 'formaction' : cgi.escape(perform_act, 1),
                                                                 'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                                                               }
                                            ) )

            txt += create_html_table_from_tuple(tableheader=submissions_tableheader, tablebody=submissions_tablebody)
        except IndexError:
            ## submissions tuple was not in expected format
            txt += """<span class="info">Unable to correctly display details of submissions</span>"""

        txt += """</td>
         </tr>"""
        ## now, display a list of actions that can be added
        txt += """
         <tr>
          <td>
           <span class="adminlabel">Add a new Submission:</span><br />"""

        if len(add_actions_list) > 0:
            txt += """
           <form method="get" action="%(websubadmin_url)s/%(performaction)s">
            <input type="hidden" name="doctype" value="%(doctype)s" />
            %(submissions_list)s
            <input name="doctypesubmissionadd" class="adminbutton" type="submit" value="Add Submission" />
           </form>""" \
                    % { 'doctype' : cgi.escape(doctype, 1),
                        'performaction' : cgi.escape(perform_act, 1),
                        'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1),
                        'submissions_list' : create_html_select_list(select_name="action", option_list=add_actions_list,
                                                                     css_style="margin: 5px 10px 5px 10px;")
                      }
        else:
            txt += """
           <br />
           <span class="info">No Available Actions to Add</span>"""
        txt += """
          </td>
         </tr>
        </tbody>
       </table>"""
                
        return txt

    def _tmpl_configure_doctype_overview_create_referees_view(self,
                                                              doctype="",
                                                              doctype_referees="",
                                                              perform_act="doctypeconfigure"
                                                             ):
        """Display the details of the referees of the various categories of a given document type"""
        ## sanity checking for doctype_referees:
        if type(doctype_referees) is not dict:
            doctype_referees = {}
        txt = """
        <table class="admin_wvar" width="100%%">
         <thead>
         <tr>
         <th class="adminheaderleft">
           Manage Referees for Document Type %(doctype_id)s:
          </th>
         </tr>
         </thead>
         <tbody>
         <tr>
          <td><br />""" % { 'doctype_id' : cgi.escape(doctype, 1) }

        try:
            referees_tableheader = ["Referee", "Delete"]
            referees_tablebody = []
            referee_roles = doctype_referees.keys()
            referee_roles.sort()
            for role in referee_roles:
                if doctype_referees[role][0] == "*":
                    referees_tablebody.append( ("""<span style="color: navy;">%s</span>""" % (cgi.escape(doctype_referees[role][1], 1)),
                                                "&nbsp;") )
                else:
                    referees_tablebody.append( ("""<span style="color: navy;">%s (%s)</span>""" % (cgi.escape(doctype_referees[role][0], 1), \
                                                                                           cgi.escape(doctype_referees[role][1], 1)),
                                                "&nbsp;") )
                for referee in doctype_referees[role][2]:
                    referees_tablebody.append( ("""<small>%s</small>""" % (cgi.escape(referee[1], 1),),
                                                """<form class="hyperlinkform" method="get" action="%(websubadmin_url)s/%(performaction)s">""" \
                                                """<input class="hyperlinkformHiddenInput" name="doctype" value="%(doctype)s" type="hidden" />""" \
                                                """<input class="hyperlinkformHiddenInput" name="categid" value="%(categ)s" type="hidden" />""" \
                                                """<input class="hyperlinkformHiddenInput" name="refereeid" value="%(refereeid)s" type="hidden" />""" \
                                                """<input type="submit" name="doctyperefereedelete" class="hyperlinkformSubmitButton" value="delete" />""" \
                                                """</form>""" \
                                                % { 'doctype' : cgi.escape(doctype, 1),
                                                    'categ' : cgi.escape(doctype_referees[role][0], 1),
                                                    'refereeid' : cgi.escape(str(int(referee[0])), 1),
                                                    'performaction' : cgi.escape(perform_act, 1),
                                                    'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                                                  }
                                             ) )

            txt += create_html_table_from_tuple(tableheader=referees_tableheader, tablebody=referees_tablebody)
        except IndexError:
            ## referees dictionary was not in expected format
            txt += """<span class="info">Unable to correctly display details of referees</span>"""

        txt += """
          </td>
         </tr>
         <tr>
          <td>
           <form method="post" action="%(websubadmin_url)s/%(performaction)s">
            <input name="managerefereesdoctype" class="adminbutton" type="submit" value="Add Referees" />
           </form>
          </td>
         </tr>
         </tbody>
        </table>""" % { 'doctype_id' : cgi.escape(doctype, 1),
                        'performaction' : cgi.escape(perform_act, 1),
                        'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
                      }
        return txt

    def tmpl_configure_doctype_overview(self, doctype="", doctypename="", doctypedescr="", doctype_cdate="", doctype_mdate="", \
                                        doctype_categories="", doctype_submissions="", doctype_referees="", user_msg="", \
                                        add_actions_list=None, perform_act="doctypeconfigure"):
        """TODO : DOCSTRING"""
        ## sanity checking:
        if type(doctype_categories) not in (list, tuple):
            doctype_categories = ()
        if type(doctype_submissions) not in (list, tuple):
            doctype_submissions = ()
        if type(add_actions_list) not in (list, tuple):
            add_actions_list = ()

        output = ""        
        body_content = ""
        output += self._create_user_message_string(user_msg)
        ## table containing document type details:
        body_content += """<br />%s""" % (self._tmpl_configire_doctype_overview_create_doctype_details(doctype=doctype,
                                                                                                       doctypename=doctypename,
                                                                                                       doctypedescr=doctypedescr,
                                                                                                       doctype_cdate=doctype_cdate,
                                                                                                       doctype_mdate=doctype_mdate,
                                                                                                       perform_act=perform_act
                                                                                                      )
                                         )

        body_content += """<hr style="width: 80%%;" />"""
        ## this document type's submissions:
        body_content += """<br />%s""" % (self._tmpl_configure_doctype_overview_create_submissions_view(doctype=doctype,
                                                                                                        doctype_submissions=doctype_submissions,
                                                                                                        add_actions_list=add_actions_list,
                                                                                                        perform_act=perform_act
                                                                                                       )
                                         )
        
        body_content += """<hr style="width: 80%%;" />"""
        ## table containing document type's categories:
        body_content += """<br />%s""" % (self._tmpl_configure_doctype_overview_create_categories_view(doctype=doctype,
                                                                                                       doctype_categories=doctype_categories,
                                                                                                       perform_act=perform_act
                                                                                                      )
                                         )

        body_content += """<hr style="width: 80%%;" />"""
        ## button for allocation of referees:
        body_content += """<br />%s""" % (self._tmpl_configure_doctype_overview_create_referees_view(doctype=doctype,
                                                                                                     doctype_referees=doctype_referees,
                                                                                                     perform_act=perform_act
                                                                                                    )
                                         )

        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Configure Document Type:", datalist=[body_content])
        return output

    def tmpl_display_edit_category_form(self, doctype, categid, categdescr, user_msg="", perform_act="doctypeconfigure"):
        output = ""
        body_content = "<div>"
        output += self._create_user_message_string(user_msg)

        body_content += """
        <form method="get" action="%(websubadmin_url)s/%(performaction)s">
        <table width="90%%">
         <tr>
          <td width="20%%"><span class="adminlabel">Category Name:</span></td>
          <td width="80%%"><span class="info">%(categid)s</span></td>
         </tr>
         <tr>
          <td width="20%%"><span class="adminlabel">Category Description:</span></td>
          <td width="80%%"><input type="text" size="60" name="categdescr" value="%(categdescr)s" /></td>
         </tr>
         <tr>
          <td width="20%%">&nbsp;&nbsp;</td>
          <td width="80%%">
           <input type="hidden" name="doctype" value="%(doctype)s" />
           <input type="hidden" name="categid" value="%(categid)s" />
           <input name="doctypecategoryeditcommit" class="adminbutton" type="submit" value="Save Details" />
           &nbsp;
           <input name="doctypecategoryeditcancel" class="adminbutton" type="submit" value="Cancel" />
          </td>
         </tr>
        </table>
        </form>
        """ % {
               'categid'    : cgi.escape(categid, 1),
               'doctype'    : cgi.escape(doctype, 1),
               'categdescr' : cgi.escape(categdescr, 1),
               'performaction' : cgi.escape(perform_act, 1),
               'websubadmin_url' : cgi.escape(websubmitadmin_weburl, 1)
              }
        output += self._create_websubmitadmin_main_menu_header()
        output += self._create_adminbox(header="Edit Details of '%(categid)s' Category of '%(doctype)s' Document Type:" \
                                        % { 'doctype' : cgi.escape(doctype, 1), 'categid' : cgi.escape(categid, 1) },
                                        datalist=[body_content])
        return output


