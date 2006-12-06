## $Id$

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

__revision__ = "$Id$"

import urllib
import time
import cgi
import gettext
import string
import locale
import re
import operator
import os

from invenio.config import \
     accessurl, \
     images, \
     version, \
     weburl
from invenio.messages import gettext_set_language

class Template:

    # Parameters allowed in the web interface for fetching files
    files_default_urlargd = {
        'version': (str, "") # version "" means "latest"
        }


    def tmpl_submit_home_page(self, ln, catalogues):
        """
        The content of the home page of the submit engine

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'catalogues' *string* - The HTML code for the catalogues list
        """

        # load the right message language
        _ = gettext_set_language(ln)

        return """
          <SCRIPT TYPE="text/javascript" LANGUAGE="Javascript1.2">
          var allLoaded = 1;
          </SCRIPT>
           <table class="searchbox" width="100%%" summary="">
              <tr>
                  <th class="portalboxheader">%(document_types)s:</th>
              </tr>
              <tr>
                  <td class="portalboxbody">
                    <BR>
                    %(please_select)s:
                    <BR><BR>
                    <TABLE width="100%%">
                    <TR>
                        <TD width="50%%" class="narrowsearchboxbody">
                          <FORM method=get action="/submit">
                            <INPUT type="hidden" name="doctype">
                              %(catalogues)s
                        </TD>
                    </TR>
                    </TABLE>
                    </FORM>
                  </td>
              </tr>
            </table>""" % {
              'document_types' : _("Document types available for submission"),
              'please_select' : _("Please select the type of document you want to submit."),
              'catalogues' : catalogues,
            }

    def tmpl_submit_home_catalog_no_content(self, ln):
        """
        The content of the home page of submit in case no doctypes are available

        Parameters:

          - 'ln' *string* - The language to display the interface in
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = "<h3>" + _("No document types available.") + "</h3>\n"
        return out

    def tmpl_submit_home_catalogs(self, ln, catalogs):
        """
        Produces the catalogs' list HTML code

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'catalogs' *array* - The catalogs of documents, each one a hash with the properties:
                - 'id' - the internal id
                - 'name' - the name
                - 'sons' - sub-catalogs
                - 'docs' - the contained document types, in the form:
                      - 'id' - the internal id
                      - 'name' - the name
            There is at least one catalog
        """

        # load the right message language
        _ = gettext_set_language(ln)

        # import pprint
        # out = "<pre>" + pprint.pformat(catalogs)
        out = ""
        for catalog in catalogs:
            out += "<UL>"
            out += self.tmpl_submit_home_catalogs_sub(ln, catalog)

        return out

    def tmpl_submit_home_catalogs_sub(self, ln, catalog):
        """
        Recursive function that produces a catalog's HTML display

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'catalog' *array* - A catalog of documents, with the properties:
                - 'id' - the internal id
                - 'name' - the name
                - 'sons' - sub-catalogs
                - 'docs' - the contained document types, in the form:
                      - 'id' - the internal id
                      - 'name' - the name
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if catalog['level'] == 1:
            out = "<LI><font size=\"+1\"><strong>%s</strong></font>\n" % catalog['name']
        else:
            if catalog['level'] == 2:
                out = "<LI>%s\n" % catalog['name']
            else:
                if catalog['level'] > 2:
                    out = "<LI>%s\n" % catalog['name']

        if len(catalog['docs']) or len(catalog['sons']):
            out += "<UL>"

        if len(catalog['docs']) != 0:
            for row in catalog['docs']:
                out += self.tmpl_submit_home_catalogs_doctype(ln, row)

        if len(catalog['sons']) != 0:
            for row in catalog['sons']:
                out += self.tmpl_submit_home_catalogs_sub(ln, row)

        if len(catalog['docs']) or len(catalog['sons']):
            out += "</UL>"

        return out

    def tmpl_submit_home_catalogs_doctype(self, ln, doc):
        """
        Recursive function that produces a catalog's HTML display

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'doc' *array* - A catalog of documents, with the properties:
                      - 'id' - the internal id
                      - 'name' - the name
        """

        # load the right message language
        _ = gettext_set_language(ln)

        return """<LI><a href="" onClick="document.forms[0].doctype.value='%(id)s';document.forms[0].submit();return false;">%(name)s</a>""" % doc

    def tmpl_action_page(self, ln, uid, guest, pid, now, doctype,
                         description, docfulldesc, snameCateg,
                         lnameCateg, actionShortDesc, indir,
                         statustext):
        """
        Recursive function that produces a catalog's HTML display

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'guest' *boolean* - If the user is logged in or not

          - 'pid' *string* - The current process id

          - 'now' *string* - The current time (security control features)

          - 'doctype' *string* - The selected doctype

          - 'description' *string* - The description of the doctype

          - 'docfulldesc' *string* - The title text of the page

          - 'snameCateg' *array* - The short names of all the categories of documents

          - 'lnameCateg' *array* - The long names of all the categories of documents

          - 'actionShortDesc' *array* - The short names (codes) for the different actions

          - 'indir' *array* - The directories for each of the actions

          - 'statustext' *array* - The names of the different action buttons
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""

        out += """
              <SCRIPT LANGUAGE="JavaScript" TYPE="text/javascript">
              var checked = 0;
              function tester() {
              """
        if (guest):
            out += "alert(\"%(please_login_js)s\");return false;\n" % {
                     'please_login_js' : _("Please log in first.") + '\\n' + _("Use the top-right menu to log in.")
                   }

        out += """
                    if (checked == 0) {
                        alert ("%(select_cat)s");
                        return false;
                    } else {
                        return true;
                    }
                }

                function clicked() {
                    checked=1;
                }

                function selectdoctype(nb) {
                    document.forms[0].act.value = docname[nb];
                }
                </SCRIPT>
                <FORM method="get" action="/submit">
                <INPUT type="hidden" name="doctype" value="%(doctype)s">
                <INPUT type="hidden" name="indir">
                <input type="hidden" name="access" value="%(now)i_%(pid)s">

                <INPUT type="hidden" name="act">
                <INPUT type="hidden" name="startPg" value="1">
                <INPUT type="hidden" name="mainmenu" value="/submit?doctype=%(doctype)s">

                <table class="searchbox" width="100%%" summary="">
                  <tr>
                    <th class="portalboxheader">%(docfulldesc)s</th>
                  </tr>
                  <tr>
                      <td class="portalboxbody">%(description)s
                        <BR>
                        <SCRIPT LANGUAGE="JavaScript" TYPE="text/javascript">
                        var nbimg = document.images.length + 1;
                        </SCRIPT>
                        <BR>
                        <TABLE align="center" cellpadding="0" cellspacing="0" border="0">
                        <TR valign="top">
                """ % {
                      'select_cat' : _("Please select a category"),
                      'doctype' : doctype,
                      'now' : now,
                      'pid' : pid,
                      'docfulldesc' : docfulldesc,
                      'description' : description,
                    }

        if len(snameCateg) :
            out += """<TD align="right">"""
            for i in range(0, len(snameCateg)):
                out += """%(longname)s<INPUT type="radio" name="combo%(doctype)s" value="%(shortname)s" onClick="clicked();">&nbsp;<BR />""" % {
                         'longname' : lnameCateg[i],
                         'doctype' : doctype,
                         'shortname' : snameCateg[i],
                       }
            out += "</TD>"
        else:
            out += "<SCRIPT>checked=1;</SCRIPT>"
        out += """<TD>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</TD>
                  <td>
                    <table>
               """
        #display list of actions
        for i in range(0,len(actionShortDesc)):
            out += """<input type="submit" class="adminbutton" value="%(status)s" onClick="if (tester()) { document.forms[0].indir.value='%(indir)s';document.forms[0].act.value='%(act)s';document.forms[0].submit();}; return false;"><br>""" % {
                     'status' : statustext[i],
                     'indir' : indir[i],
                     'act' : actionShortDesc[i]
                   }
        out += """  </TABLE>
                    </TD>
                </TR>
                </TABLE>
                <BR>"""
        if len(snameCateg) :
            out += """<STRONG class="headline">%(notice)s:</STRONG><BR>
                    %(select_cat)s""" % {
                     'notice' : _("Notice"),
                     'select_cat' : _("Select a category and then click on an action button."),
                    }
        out += """
                <BR><BR>
                <BR>
                </FORM>
                <FORM action="/submit"><HR>
                  <font color="black"><small>%(continue_explain)s</small></FONT>
                  <TABLE border=0 bgcolor="#CCCCCC" width="100%%"><TR>
                    <TD width="100%%">
                    <small>Access Number: <INPUT size=15 name=AN>
                      <INPUT type="hidden" name="doctype" value="%(doctype)s">
                      <INPUT class="adminbutton" type="submit" value=" %(go)s ">
                    </small>
                    </TD></TR>
                  </TABLE>
                  <HR>
                 </FORM>
                        </td>
                    </tr>
                </table>""" % {
                'continue_explain' : _("To continue with a previously interrupted submission, enter an access number into the box below:"),
                  'doctype' : doctype,
                  'go' : _("GO"),
                }

        return out

    def tmpl_warning_message(self, ln, msg):
        """
        Produces a warning message for the specified text

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'msg' *string* - The message to display
        """

        # load the right message language
        _ = gettext_set_language(ln)

        return """<center><font color="red">%s</font></center>""" % msg

    def tmpl_page_interface(self, ln, docname, actname, curpage, nbpages, file, nextPg, access, nbPg, doctype, act, indir, fields, javascript, images, mainmenu):
        """
        Produces a page with the specified fields (in the submit chain)

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'doctype' *string* - The document type

          - 'docname' *string* - The document type name

          - 'actname' *string* - The action name

          - 'act' *string* - The action

          - 'curpage' *int* - The current page of submitting engine

          - 'nbpages' *int* - The total number of pages

          - 'nextPg' *int* - The next page

          - 'access' *string* - The submission number

          - 'nbPg' *string* - ??

          - 'indir' *string* - the directory of submitting

          - 'fields' *array* - the fields to display in the page, with each record having the structure:

              - 'fullDesc' *string* - the description of the field

              - 'text' *string* - the HTML code of the field

              - 'javascript' *string* - if the field has some associated javascript code

              - 'type' *string* - the type of field (T, F, I, H, D, S, R)

              - 'name' *string* - the name of the field

              - 'rows' *string* - the number of rows for textareas

              - 'cols' *string* - the number of columns for textareas

              - 'val' *string* - the default value of the field

              - 'size' *string* - the size for text fields

              - 'maxlength' *string* - the maximum length for text fields

              - 'htmlcode' *string* - the complete HTML code for user-defined fields

              - 'typename' *string* - the long name of the type

          - 'javascript' *string* - the javascript code to insert in the page

          - 'images' *string* - the path to the images

          - 'mainmenu' *string* - the url of the main menu

        """

        # load the right message language
        _ = gettext_set_language(ln)

        # top menu
        out = """
                <FORM method="POST" action="/submit" onSubmit="return tester();">
                <center><TABLE cellspacing="0" cellpadding="0" border="0">
                  <TR>
                    <TD class="submitHeader"><B>%(docname)s&nbsp;</B></TD>
                    <TD class="submitHeader"><small>&nbsp;%(actname)s&nbsp;</small></TD>
                    <TD valign="bottom">
                        <TABLE cellspacing="0" cellpadding="0" border="0" width="100%%">
                        <TR><TD class="submitEmptyPage">&nbsp;&nbsp;</TD>
              """ % {
                'docname' : docname,
                'actname' : actname,
              }

        for i in range(1, nbpages+1):
            if i == int(curpage):
                out += """<TD class="submitCurrentPage"><small>&nbsp;page: %s&nbsp;</small></TD>""" % curpage
            else:
                out += """<TD class="submitPage"><small>&nbsp;<A HREF='' onClick="if (tester2() == 1){document.forms[0].curpage.value=%s;document.forms[0].submit();return false;} else { return false; }">%s</A>&nbsp;</small></TD>""" % (i,i)
        out += """        <TD class="submitEmptyPage">&nbsp;&nbsp;
                        </TD></TR></TABLE>
                    </TD>
                    <TD class="submitHeader" align="right">&nbsp;<A HREF='' onClick="window.open('/submit/summary?doctype=%(doctype)s&act=%(act)s&access=%(access)s&indir=%(indir)s','summary','scrollbars=yes,menubar=no,width=500,height=250');return false;"><font color="white"><small>%(summary)s(2)</small></font></A>&nbsp;</TD>
                  </TR>
                  <TR><TD colspan="5" class="submitHeader">
                    <TABLE border="0" cellspacing="0" cellpadding="15" width="100%%" class="submitBody"><TR><TD>
                     <BR>
                     <INPUT type="hidden" name="file" value="%(file)s">
                     <INPUT type="hidden" name="nextPg" value="%(nextPg)s">
                     <INPUT type="hidden" name="access" value="%(access)s">
                     <INPUT type="hidden" name="curpage" value="%(curpage)s">
                     <INPUT type="hidden" name="nbPg" value="%(nbPg)s">
                     <INPUT type="hidden" name="doctype" value="%(doctype)s">
                     <INPUT type="hidden" name="act" value="%(act)s">
                     <INPUT type="hidden" name="indir" value="%(indir)s">
                     <INPUT type="hidden" name="mode" value="U">
                     <INPUT type="hidden" name="step" value="0">
                """ % {
                 'summary' : _("SUMMARY"),
                 'doctype' : doctype,
                 'act' : act,
                 'access' : access,
                 'indir' : indir,
                 'file' : file,
                 'nextPg' : nextPg,
                 'curpage' : curpage,
                 'nbPg' : nbPg,
               }

        for field in fields:
            if field['javascript']:
                out += """<SCRIPT LANGUAGE="JavaScript1.1"  TYPE="text/javascript">
                          %s
                          </SCRIPT>
                       """ % field['javascript'];

            # now displays the html form field(s)
            out += "%s\n%s\n" % (field['fullDesc'], field['text'])

        out += javascript
        out += "<BR>&nbsp;<BR>&nbsp;</TD></TR></TABLE></TD></TR>\n"

        # Display the navigation cell
        # Display "previous page" navigation arrows
        out += """<TR><TD colspan="5"><TABLE border="0" cellpadding="0" cellspacing="0" width="100%%"><TR>"""
        if int(curpage) != 1:
            out += """ <TD class="submitHeader" align="left">&nbsp;
                         <A HREF='' onClick="if (tester2() == 1) {document.forms[0].curpage.value=%(prpage)s;document.forms[0].submit();return false;} else { return false; }">
                           <IMG SRC="%(images)s/left-trans.gif" alt="%(prevpage)s" border="0">
                             <strong><font color="white">%(prevpage)s</font></strong>
                         </A>
                       </TD>
            """ % {
              'prpage' : int(curpage) - 1,
              'images' : images,
              'prevpage' : _("Previous page"),
            }
        else:
            out += """ <TD class="submitHeader">&nbsp;</TD>"""
        # Display the submission number
        out += """ <TD class="submitHeader" align="center"><small>%(submission)s: %(access)s</small></TD>\n""" % {
                'submission' : _("Submission number") + '(1)',
                'access' : access,
              }
        # Display the "next page" navigation arrow
        if int(curpage) != int(nbpages):
            out += """ <TD class="submitHeader" align="right">
                         <A HREF='' onClick="if (tester2()){document.forms[0].curpage.value=%(nxpage)s;document.forms[0].submit();return false;} else {return false;}; return false;">
                          <strong><font color="white">%(nextpage)s</font></strong>
                          <IMG SRC="%(images)s/right-trans.gif" alt="%(nextpage)s" border="0">
                        </A>
                       </TD>
            """ % {
              'nxpage' : int(curpage) + 1,
              'images' : images,
              'nextpage' : _("Next page"),
            }
        else:
            out += """ <TD class="submitHeader">&nbsp;</TD>"""
        out += """</TR></TABLE></TD></TR></TABLE></center></FORM>

                  <BR>
                  <BR>
                 <A HREF="%(mainmenu)s" onClick="return confirm('%(surequit)s')">
                 <IMG SRC="%(images)s/mainmenu.gif" border="0" ALT="%(back)s" align="right"></A>
                 <BR><BR>
                 <HR>
                  <small>%(take_note)s</small><BR>
                  <small>%(explain_summary)s</small><BR>
               """ % {
                 'surequit' : _("Are you sure you want to quit this submission?"),
                 'back' : _("Back to main menu"),
                 'mainmenu' : mainmenu,
                 'images' : images,
                 'take_note' : '(1) ' + _("This is your submission access number. It can be used to continue with an interrupted submission in case of problems."),
                 'explain_summary' : '(2) ' + _("Mandatory fields appear in red in the SUMMARY window."),
               }
        return out

    def tmpl_submit_field(self, ln, field):
        """
        Produces the HTML code for the specified field

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'field' *array* - the field to display in the page, with the following structure:

              - 'javascript' *string* - if the field has some associated javascript code

              - 'type' *string* - the type of field (T, F, I, H, D, S, R)

              - 'name' *string* - the name of the field

              - 'rows' *string* - the number of rows for textareas

              - 'cols' *string* - the number of columns for textareas

              - 'val' *string* - the default value of the field

              - 'size' *string* - the size for text fields

              - 'maxlength' *string* - the maximum length for text fields

              - 'htmlcode' *string* - the complete HTML code for user-defined fields

              - 'typename' *string* - the long name of the type

        """

        # load the right message language
        _ = gettext_set_language(ln)

        # If the field is a textarea
        if field['type'] == 'T':
            text="<TEXTAREA name=\"%s\" rows=\"%s\" cols=\"%s\">%s</TEXTAREA>" % (field['name'],field['rows'],field['cols'],field['val'])
        # If the field is a file upload
        elif field['type'] == 'F':
            text="<INPUT TYPE=file name=\"%s\" size=\"%s\" maxlength=\"%s\">" % (field['name'],field['size'], field['maxlength']);
        # If the field is a text input
        elif field['type'] == 'I':
            text="<INPUT name=\"%s\" size=\"%s\" value=\"%s\">" % (field['name'],field['size'],field['val'])
        # If the field is a hidden input
        elif field['type'] == 'H':
            text="<INPUT type=\"hidden\" name=\"%s\" value=\"%s\">" % (field['name'],field['val'])
        # If the field is user-defined
        elif field['type'] == 'D':
            text=field['htmlcode']
        # If the field is a select box
        elif field['type'] == 'S':
            text=field['htmlcode']
        # If the field type is not recognized
        else:
            text="%s: unknown field type" % field['typename']

        return text

    def tmpl_page_interface_js(self, ln, upload, field, fieldhtml, txt, check, level, curdir, values, select, radio, curpage, nbpages, images, returnto):
        """
        Produces the javascript for validation and value filling for a submit interface page

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'upload' *array* - booleans if the field is a <input type="file"> field

          - 'field' *array* - the fields' names

          - 'fieldhtml' *array* - the fields' HTML representation

          - 'txt' *array* - the fields' long name

          - 'check' *array* - if the fields should be checked (in javascript)

          - 'level' *array* - strings, if the fields should be filled (M) or not (O)

          - 'curdir' *array* - the current directory of the submission

          - 'values' *array* - the current values of the fields

          - 'select' *array* - booleans, if the controls are "select" controls

          - 'radio' *array* - booleans, if the controls are "radio" controls

          - 'curpage' *int* - the current page

          - 'nbpages' *int* - the total number of pages

          - 'images' *int* - the path to the images

          - 'returnto' *array* - a structure with 'field' and 'page', if a mandatory field on antoher page was not completed
        """

        # load the right message language
        _ = gettext_set_language(ln)

        nbFields = len(upload)
        # if there is a file upload field, we change the encoding type
        out = """<SCRIPT LANGUAGE="JavaScript1.1" TYPE="text/javascript">
              """
        for i in range(0,nbFields):
            if upload[i] == 1:
                out += "document.forms[0].encoding = \"multipart/form-data\";\n"
                break
        # we don't want the form to be submitted if the user enters 'Return'
        # tests if mandatory fields are well filled
        out += """function tester(){
                   return false;
                  }
                  function tester2() {
               """
        for i in range(0,nbFields):
            if re.search("%s\[\]" % field[i],fieldhtml[i]):
                fieldname = "%s[]" % field[i]
            else:
                fieldname = field[i]
            out += "  el = document.forms[0].elements['%s'];\n" % fieldname
            # If the field must be checked we call the checking function
            if check[i] != "":
                out += """if (%(check)s(el.value) == 0) {
                            el.focus();
                            return 0;
                          } """ % {
                            'check' : check[i]
                          }
            # If the field is mandatory, we check a value has been selected
            if level[i] == 'M':
                if select[i] != 0:
                    # If the field is a select box
                    out += """if ((el.selectedIndex == -1)||(el.selectedIndex == 0)){
                                    alert("%(field_mandatory)s");
                                    return 0;
                              } """ % {
                                'field_mandatory' : _("The field %s is mandatory.") % txt[i] + '\\n' + _("Please make a choice in the select box")
                              }
                elif radio[i] != 0:
                    # If the field is a radio buttonset
                    out += """var check=0;
                              for (var j = 0; j < el.length; j++) {
                                if (el.options[j].checked){
                                  check++;
                                }
                              }
                              if (check == 0) {
                                alert("%(press_button)s");
                                return 0;
                              }""" % {
                                'press_button':_("Please press a button.")
                              }
                else:
                    # If the field is a text input
                    out += """if (el.value == '') {
                               alert("%(field_mandatory)s");
                               return 0;
                              }""" % {
                                'field_mandatory' : _("The field %s is mandatory. Please fill it in.") % txt[i]
                              }
        out += """  return 1;
                  }
               <!-- Fill the fields in with the previous saved values-->
               """

        # # # # # # # # # # # # # # # # # # # # # # # # #
        # Fill the fields with the previously saved values
        # # # # # # # # # # # # # # # # # # # # # # # # #
        for i in range(0,nbFields):
            if re.search("%s\[\]"%field[i],fieldhtml[i]):
                fieldname = "%s[]" % field[i]
            else:
                fieldname = field[i]
            text = values[i]

            if text != '':
                if select[i] != 0:
                    # If the field is a SELECT element
                    vals = text.split("\n")
                    tmp=""
                    for val in vals:
                        if tmp != "":
                            tmp = tmp + " || "
                        tmp = tmp + "el.options[j].value == \"%s\" || el.options[j].text == \"%s\"" % (val,val)
                    if tmp != "":
                        out += """
                                 <!--SELECT field found-->
                                 el = document.forms[0].elements['%(fieldname)s'];
                                 for (var j = 0; j < el.length; j++){
                                   if (%(tmp)s){
                                     el.options[j].selected = true;
                                   }
                                 }""" % {
                                   'fieldname' : fieldname,
                                   'tmp' : tmp,
                                 }
                elif radio[i] != 0:
                    # If the field is a RADIO element
                    out += """<!--RADIO field found-->
                              el = document.forms[0].elements['%(fieldname)s'];
                              if (el.value == "%(text)s"){
                                el.checked=true;
                              }""" % {
                                'fieldname' : fieldname,
                                'text' : text,
                              }
                elif upload[i] == 0:
                    text = text.replace('"','\"')
                    text = text.replace("\n","\\n")
                    # If the field is not an upload element
                    out += """<!--INPUT field found-->
                               el = document.forms[0].elements['%(fieldname)s'];
                               el.value="%(text)s";
                           """ % {
                             'fieldname' : fieldname,
                             'text' : text,
                           }
        out += """<!--End Fill in section-->
               """

        # JS function finish
        # This function tests each mandatory field in the whole submission and checks whether
        # the field has been correctly filled in or not
        # This function is called when the user presses the "End
        # Submission" button
        if int(curpage) == int(nbpages):
            out += """function finish() {
                   """
            if returnto:
                out += """alert ("%(msg)s");
                          document.forms[0].curpage.value="%(page)s";
                          document.forms[0].submit();
                         }
                       """ % {
                         'msg' : _("The field %(field)s is mandatory.") + '\n' + _("Going back to page") + returnto['page'],
                         'page' : returnto['page']
                       }
            else:
                out += """ if (tester2()) {
                             document.forms[0].action="/submit";
                             document.forms[0].step.value=1;
                             document.forms[0].submit();
                           } else {
                             return false;
                           }
                         }"""
        out += """</SCRIPT>"""
        return out

    def tmpl_page_endaction(self, ln, weburl, file, nextPg, startPg, access, curpage, nbPg, nbpages, doctype, act, docname, actname, indir, mainmenu, finished, function_content, next_action, images):
        """
        Produces the pages after all the fields have been submitted.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The url of CDS Invenio

          - 'doctype' *string* - The document type

          - 'act' *string* - The action

          - 'docname' *string* - The document type name

          - 'actname' *string* - The action name

          - 'curpage' *int* - The current page of submitting engine

          - 'startPg' *int* - The start page

          - 'nextPg' *int* - The next page

          - 'access' *string* - The submission number

          - 'nbPg' *string* - total number of pages

          - 'nbpages' *string* - number of pages (?)

          - 'indir' *string* - the directory of submitting

          - 'file' *string* - ??

          - 'mainmenu' *string* - the url of the main menu

          - 'finished' *bool* - if the submission is finished

          - 'images' *string* - the path to the images

          - 'function_content' *string* - HTML code produced by some function executed

          - 'next_action' *string* - if there is another action to be completed, the HTML code for linking to it
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
          <FORM ENCTYPE="multipart/form-data" action="/submit" method="POST">
          <INPUT type="hidden" name="file" value="%(file)s">
          <INPUT type="hidden" name="nextPg" value="%(nextPg)s">
          <INPUT type="hidden" name="startPg" value="%(startPg)s">
          <INPUT type="hidden" name="access" value="%(access)s">
          <INPUT type="hidden" name="curpage" value="%(curpage)s">
          <INPUT type="hidden" name="nbPg" value="%(nbPg)s">
          <INPUT type="hidden" name="doctype" value="%(doctype)s">
          <INPUT type="hidden" name="act" value="%(act)s">
          <INPUT type="hidden" name="indir" value="%(indir)s">
          <INPUT type="hidden" name="fromdir" value="">
          <INPUT type="hidden" name="mainmenu" value="%(mainmenu)s">

          <INPUT type="hidden" name="mode" value="U">
          <INPUT type="hidden" name="step" value="1">
          <INPUT type="hidden" name="deleted" value="no">
          <INPUT type="hidden" name="file_path" value="">
          <INPUT type="hidden" name="userfile_name" value="">

          <center><TABLE cellspacing="0" cellpadding="0" border="0"><TR>
             <TD class="submitHeader"><B>%(docname)s&nbsp;</B></TD>
             <TD class="submitHeader"><small>&nbsp;%(actname)s&nbsp;</small></TD>
             <TD valign="bottom">
                 <TABLE cellspacing="0" cellpadding="0" border="0" width="100%%">
                 <TR><TD class="submitEmptyPage">&nbsp;&nbsp;</TD>
              """ % {
                'file' : file,
                'nextPg' : nextPg,
                'startPg' : startPg,
                'access' : access,
                'curpage' : curpage,
                'nbPg' : nbPg,
                'doctype' : doctype,
                'act' : act,
                'docname' : docname,
                'actname' : actname,
                'indir' : indir,
                'mainmenu' : mainmenu,
              }

        if finished == 1:
            out += """<TD class="submitCurrentPage">%(finished)s</TD>
                      <TD class="submitEmptyPage">&nbsp;&nbsp;</TD>
                     </TR></TABLE>
                    </TD>
                    <TD class="submitEmptyPage" align="right">&nbsp;</TD>
                   """ % {
                     'finished' : _("finished!"),
                   }
        else:
            for i in range(1, nbpages + 1):
                out += """<TD class="submitPage"><small>&nbsp;
                            <A HREF='' onClick="document.forms[0].curpage.value=%s;document.forms[0].action='/submit';document.forms[0].step.value=0;document.forms[0].submit();return false;">%s</A>&nbsp;</small></TD>""" % (i,i)
            out += """<TD class="submitCurrentPage">%(end_action)s</TD><TD class="submitEmptyPage">&nbsp;&nbsp;</TD></TR></TABLE></TD>
                      <TD class="submitHeader" align="right">&nbsp;<A HREF='' onClick="window.open('/submit/summary?doctype=%(doctype)s&act=%(act)s&access=%(access)s&indir=%(indir)s','summary','scrollbars=yes,menubar=no,width=500,height=250');return false;"><font color="white"><small>%(summary)s(2)</small></font></A>&nbsp;</TD>""" % {
                        'end_action' : _("end of action"),
                        'summary' : _("SUMMARY"),
                        'doctype' : doctype,
                        'act' : act,
                        'access' : access,
                        'indir' : indir,
                      }
        out += """</TR>
                  <TR>
                    <TD colspan="5" class="submitBody">
                      <small><BR><BR>
                      %(function_content)s
                      %(next_action)s
                      <BR><BR>
                    </TD>
                </TR>
                <TR class="submitHeader">
                    <TD class="submitHeader" colspan="5" align="center">""" % {
                       'function_content' : function_content,
                       'next_action' : next_action,
                     }
        if finished == 0:
            out += """<small>%(submission)s</small>&sup2;:
                      <small>%(access)s</small>""" % {
                        'submission' : _("Submission no"),
                        'access' : access,
                      }
        else:
            out += "&nbsp;\n"
        out += """
            </TD>
        </TR>
        </TABLE>
        </center>
        </form>
        <br>
        <br>"""
        # Add the "back to main menu" button
        if finished == 0:
            out += """ <A HREF="%(mainmenu)s" onClick="return confirm('%(surequit)s')">""" % {
                     'surequit' : _("Are you sure you want to quit this submission?"),
                     'mainmenu' : mainmenu,
                   }
        else:
            out += """ <A HREF="%(mainmenu)s">
                       <IMG SRC="%(images)s/mainmenu.gif" border="0" ALT="%(back)s" align="right"></A>
                       <BR><BR>""" % {
                     'back' : _("Back to main menu"),
                     'images' : images,
                     'mainmenu' : mainmenu,
                   }

        return out

    def tmpl_function_output(self, ln, display_on, action, doctype, step, functions):
        """
        Produces the output of the functions.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'display_on' *bool* - If debug information should be displayed

          - 'doctype' *string* - The document type

          - 'action' *string* - The action

          - 'step' *int* - The current step in submission

          - 'functions' *aray* - HTML code produced by functions executed and informations about the functions

              - 'name' *string* - the name of the function

              - 'score' *string* - the score of the function

              - 'error' *bool* - if the function execution produced errors

              - 'text' *string* - the HTML code produced by the function
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        if display_on:
            out += """<br><br>%(function_list)s<P>
                      <table border="1" cellpadding="15">
                        <tr><th>%(function)s</th><th>%(score)s</th><th>%(running)s</th></tr>
                   """ % {
                     'function_list' : _("Here is the %(x_action)s function list for %(x_doctype)s documents at level %(x_step)s") % {
                                         'x_action' : action,
                                         'x_doctype' : doctype,
                                         'x_step' : step,
                                       },
                     'function' : _("Function"),
                     'score' : _("Score"),
                     'running' : _("Running function"),
                   }
            for function in functions:
                out += """<tr><td>%(name)s</td><td>%(score)s</td><td>%(result)s</td></tr>""" % {
                          'name' : function['name'],
                          'score' : function['score'],
                          'result' : function['error'] and (_("Function %s does not exist.") % function['name'] + "<br>") or function['text']
                        }
            out += "</table>"
        else:
            for function in functions:
                if not function['error']:
                    out += function['text']

        return out

    def tmpl_next_action(self, ln, actions):
        """
        Produces the output of the functions.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'actions' *array* - The actions to display, in the structure

              - 'page' *string* - the starting page

              - 'action' *string* - the action (in terms of submission)

              - 'doctype' *string* - the doctype

              - 'nextdir' *string* - the path to the submission data

              - 'access' *string* - the submission number

              - 'indir' *string* - ??

              - 'name' *string* - the name of the action
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = "<BR><BR>%(haveto)s<ul>" % {
                'haveto' : _("You must now"),
              }
        i = 0
        for action in actions:
            if i > 0:
                out += " <b>" + _("or") + "</b> "
            i += 1
            out += """<LI><A HREF="" onClick="document.forms[0].action='/submit';document.forms[0].curpage.value='%(page)s';document.forms[0].startPg.value='%(page)s';document.forms[0].act.value='%(action)s';document.forms[0].doctype.value='%(doctype)s';document.forms[0].indir.value='%(nextdir)s';document.forms[0].access.value='%(access)s';document.forms[0].fromdir.value='%(indir)s';document.forms[0].submit();return false;"> %(name)s </a>""" % action

        out += "</ul>"
        return out

    def tmpl_filelist(self, ln, filelist, recid, docid, version):
        """
        Displays the file list for a record.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'recid' *string* - The record id

          - 'docid' *string* - The document id

          - 'version' *string* - The version of the document

          - 'filelist' *string* - The HTML string of the filelist (produced by the BibDoc classes)
        """

        # load the right message language
        _ = gettext_set_language(ln)

        title = _("record") + ' #' + '<a href="%s/record/%s">%s</a>' % (weburl, recid, recid)
        if docid != "":
            title += ' ' + _("document") + ' #' + str(docid)
        if version != "":
            title += ' ' + _("version") + ' #' + str(version)

        out = """<center><table class="searchbox" summary="" width="500"><tr><th class="portalboxheader">Access&nbsp;to&nbsp;Fulltext&nbsp;&nbsp;&nbsp;&nbsp;<font size=-2>[%s]</font></th></tr><tr><td class="portalboxbody"><!--start file list-->
                  %s
                <!--end file list--></td></tr></table></center>
              """ % (title, filelist)

        return out

    def tmpl_bibrecdoc_filelist(self, ln, types):
        """
        Displays the file list for a record.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'types' *array* - The different types to display, each record in the format:

               - 'name' *string* - The name of the format

               - 'content' *array of string* - The HTML code produced by tmpl_bibdoc_filelist, for the right files
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        for mytype in types:
            out += "<small><b>%s</b> %s:</small>" % (mytype['name'], _("file(s)"))
            out += "<ul>"
            for content in mytype['content']:
                out += content
            out += "</ul>"
        return out

    def tmpl_bibdoc_filelist(self, ln, weburl, versions, imagepath, docname, id):
        """
        Displays the file list for a record.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The url of CDS Invenio

          - 'versions' *array* - The different versions to display, each record in the format:

               - 'version' *string* - The version

               - 'content' *string* - The HTML code produced by tmpl_bibdocfile_filelist, for the right file

               - 'previous' *bool* - If the file has previous versions

          - 'imagepath' *string* - The path to the image of the file

          - 'docname' *string* - The name of the document

         - 'id' *int* - The id of the document

        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<table border="0" cellspacing="1" class="searchbox">
                   <tr>
                     <td align="left" colspan="2" class="portalboxheader">
                       <img src='%(imagepath)s' border=0>&nbsp;&nbsp;%(docname)s
                     </td>
                   </tr>""" % {
                     'imagepath' : imagepath,
                     'docname' : docname
                   }
        for version in versions:
            if version['previous']:
                versiontext =  """<br>(%(see)s <a href="%(weburl)s/getfile.py?docid=%(id)s&version=all">%(previous)s</a>)""" % {
                                 'see' : _("see"),
                                 'weburl' : weburl,
                                 'id' : id,
                                 'previous': _("previous"),
                               }
            else:
                versiontext = ""
            out += """<tr>
                        <td class="portalboxheader">
                          <font size="-2">%(version)s %(ver)s%(text)s</font>
                        </td>
                        <td>
                          <table>
                        """ % {
                          'version' : _("version"),
                          'ver' : version['version'],
                          'text' : versiontext,
                        }
            for content in version['content']:
                out += content
            out += "</table></td></tr>"
        out += "</table>"
        return out

    def tmpl_bibdocfile_filelist(self, ln, weburl, id, name, selfformat, version, format, size):
        """
        Displays a file in the file list.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'weburl' *string* - The url of CDS Invenio

          - 'id' *int* - The id of the document

          - 'name' *string* - The name of the file

          - 'selfformat' *string* - The format to pass in parameter

          - 'version' *string* - The version

          - 'format' *string* - The display format

          - 'size' *string* - The size of the file
        """

        # load the right message language
        _ = gettext_set_language(ln)

        return """<tr>
                    <td valign="top">
                      <small><a href="%(weburl)s/getfile.py?docid=%(docid)s&name=%(quotedname)s&format=%(selfformat)s&version=%(version)s">
                        %(name)s%(format)s
                      </a></small>
                    </td>
                    <td valign="top">
                      <font size="-2" color="green">[%(size)s&nbsp;B]</font>
                    </td></tr>""" % {
                      'weburl' : weburl,
                      'docid' : id,
                      'quotedname' : urllib.quote(name),
                      'selfformat' : urllib.quote(selfformat),
                      'version' : version,
                      'name' : name,
                      'format' : format,
                      'size' : size
                    }

    def tmpl_submit_summary (self, ln, values, images):
        """
        Displays the summary for the submit procedure.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'values' *array* - The values of submit. Each of the records contain the following fields:

                - 'name' *string* - The name of the field

                - 'mandatory' *bool* - If the field is mandatory or not

                - 'value' *string* - The inserted value

                - 'page' *int* - The submit page on which the field is entered

          - 'images' *string* - the path to the images
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<body style="background-image: url(%(images)s/header_background.gif);"><table border="0">""" % \
              { 'images' : images }
        
        for value in values:
            if value['mandatory']:
                color = "red"
            else:
                color = ""
            out += """<tr>
                        <td align="right">
                          <small>
                            <A HREF='' onClick="window.opener.document.forms[0].curpage.value='%(page)s';window.opener.document.forms[0].action='/submit';window.opener.document.forms[0].submit();return false;">
                              <FONT color="%(color)s">%(name)s</FONT>
                            </A>
                          </small>
                        </td>
                        <td>
                          <I><small><font color="black">%(value)s</font></small></I>
                        </td>
                      </tr>""" % {
                        'color' : color,
                        'name' : value['name'],
                        'value' : value['value'],
                        'page' : value['page']
                      }
        out += "</table>"
        return out

    def tmpl_yoursubmissions(self, ln, images, weburl, order, doctypes, submissions):
        """
        Displays the list of the user's submissions.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'images' *string* - the path to the images

          - 'weburl' *string* - The url of CDS Invenio

          - 'order' *string* - The ordering parameter

          - 'doctypes' *array* - All the available doctypes, in structures:

              - 'id' *string* - The doctype id

              - 'name' *string* - The display name of the doctype

              - 'selected' *bool* - If the doctype should be selected

          - 'submissions' *array* - The available submissions, in structures:

              - 'docname' *string* - The document name

              - 'actname' *string* - The action name

              - 'status' *string* - The status of the document

              - 'cdate' *string* - Creation date

              - 'mdate' *string* - Modification date

              - 'id' *string* - The id of the submission

              - 'reference' *string* - The display name of the doctype

              - 'pending' *bool* - If the submission is pending

              - 'act' *string* - The action code

              - 'doctype' *string* - The doctype code
        """

        # load the right message language
        _ = gettext_set_language(ln)


        out = ""
        out += """
                  <BR>
                  <SMALL>
                  <form>
                  <input type="hidden" value='%(order)s' name="order">
                  <input type="hidden" name="deletedId">
                  <input type="hidden" name="deletedDoctype">
                  <input type="hidden" name="deletedAction">
                  <table class="searchbox" width="100%%" summary="">
                    <tr>
                      <th class="portalboxheader">%(for)s&nbsp;
                        <select name="doctype" onchange="document.forms[0].submit();">
                          <option value="">%(alltype)s</option>
                  """ % {
                    'order' : order,
                    'for' : _("For"),
                    'alltype' : _("all types of document"),
                  }
        for doctype in doctypes:
            out += """<option value="%(id)s" %(sel)s>%(name)s</option>""" % {
                     'id' : doctype['id'],
                     'name' : doctype['name'],
                     'sel' : doctype['selected'] and "SELECTED=\"SELECTED\"" or ""
                   }
        out += """     </select>
                      </th>
                    </tr>
                    <tr>
                     <td class="portalboxbody">
                      <table>
                        <tr>
                          <td></td>
                        </tr>
               """

        num = 0
        docname = ""
        for submission in submissions:
            if submission['docname'] != docname:
                docname = submission['docname']
                out += """</table>
                          %(docname)s<br>
                          <table border="0" class="searchbox" align="left" width="100%%">
                            <tr>
                              <th class="headerselected">%(action)s&nbsp;&nbsp;
                                <a href='' onClick='document.forms[0].order.value="actiondown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" border="0"></a>&nbsp;
                                <a href='' onClick='document.forms[0].order.value="actionup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" border="0"></a>
                              </th>
                              <th class="headerselected">%(status)s&nbsp;&nbsp;
                                <a href='' onClick='document.forms[0].order.value="statusdown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" border="0"></a>&nbsp;
                                <a href='' onClick='document.forms[0].order.value="statusup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" border="0"></a>
                              </th>
                              <th class="headerselected">%(id)s</th>
                              <th class="headerselected">%(reference)s&nbsp;&nbsp;
                                <a href='' onClick='document.forms[0].order.value="refdown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" border="0"></a>&nbsp;
                                <a href='' onClick='document.forms[0].order.value="refup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" border="0"></a>
                              </th>
                              <th class="headerselected">%(first)s&nbsp;&nbsp;
                                <a href='' onClick='document.forms[0].order.value="cddown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" border="0"></a>&nbsp;
                                <a href='' onClick='document.forms[0].order.value="cdup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" border="0"></a>
                              </th>
                              <th class="headerselected">%(last)s&nbsp;&nbsp;
                                <a href='' onClick='document.forms[0].order.value="mddown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" border="0"></a>&nbsp;
                                <a href='' onClick='document.forms[0].order.value="mdup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" border="0"></a>
                              </th>
                            </tr>
                       """ % {
                         'docname' : submission['docname'],
                         'action' : _("Action"),
                         'status' : _("Status"),
                         'id' : _("Id"),
                         'reference' : _("Reference"),
                         'images' : images,
                         'first' : _("First access"),
                         'last' : _("Last access"),
                       }
            if submission['pending']:
                idtext = """<a href="submit/sub?access=%(id)s@%(action)s%(doctype)s">%(id)s</a>
                            &nbsp;<a onClick='if (confirm("%(sure)s")){document.forms[0].deletedId.value="%(id)s";document.forms[0].deletedDoctype.value="%(doctype)s";document.forms[0].deletedAction.value="%(action)s";document.forms[0].submit();return true;}else{return false;}' href=''><img src="%(images)s/smallbin.gif" border="0" alt='%(delete)s'></a>
                         """ % {
                           'images' : images,
                           'id' : submission['id'],
                           'action' : submission['act'],
                           'doctype' : submission['doctype'],
                           'sure' : _("Are you sure you want to delete this submission?"),
                           'delete' : _("Delete submission %(x_id)s in %(x_docname)s") % {
                                        'x_id' : str(submission['id']),
                                        'x_docname' : str(submission['docname'])
                                      }
                         }
            else:
                idtext = submission['id']

            if operator.mod(num,2) == 0:
                color = "#e0e0e0"
            else:
                color = "#eeeeee"

            if submission['reference']:
                reference = submission['reference']
            else:
                reference = """<font color="red">%s</font>""" % _("Reference not yet given")

            cdate = str(submission['cdate']).replace(" ","&nbsp;")
            mdate= str(submission['mdate']).replace(" ","&nbsp;")

            out += """
                     <tr bgcolor="%(color)s">
                       <td align="center" class="mycdscell">
                         <small>%(actname)s</small>
                       </td>
                       <td align="center" class="mycdscell">
                         <small>%(status)s</small>
                       </td>
                       <td class="mycdscell">
                         <small>%(idtext)s</small>
                       </td>
                       <td class="mycdscell">
                         <small>&nbsp;%(reference)s</small>
                       </td>
                       <td class="mycdscell">
                         <small>%(cdate)s</small>
                       </td>
                       <td class="mycdscell">
                         <small>%(mdate)s</small>
                       </td>
                     </tr>
                   """ % {
                     'color' : color,
                     'actname' : submission['actname'],
                     'status' : submission['status'],
                     'idtext' : idtext,
                     'reference' : reference,
                     'cdate' : cdate,
                     'mdate' : mdate,
                   }
            num += 1

        out += "</table></td></tr></table></form>"
        return out


    def tmpl_yourapprovals(self, ln, referees):
        """
        Displays the doctypes and categories for which the user is referee

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'referees' *array* - All the doctypes for which the user is referee:

              - 'doctype' *string* - The doctype

              - 'docname' *string* - The display name of the doctype

              - 'categories' *array* - The specific categories for which the user is referee:

                    - 'id' *string* - The category id

                    - 'name' *string* - The display name of the category
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """ <table class="searchbox" width="100%%" summary="">
                    <tr>
                        <th class="portalboxheader">%(refdocs)s</th>
                    </tr>
                    <tr>
                    <td class="portalboxbody">""" % {
                      'refdocs' : _("Refereed Documents"),
                    }

        for doctype in referees:
            out += """<UL><LI><b>%(docname)s</b><UL><small>""" % doctype

            if doctype ['categories'] is None:            
                out += '''<LI><A HREF="publiline.py?doctype=%(doctype)s">%(generalref)s</a><br>''' % {
                    'docname' : doctype['docname'],
                    'doctype' : doctype['doctype'],
                    'generalref' : _("You are a general referee")}

            else:
                for category in doctype['categories']:
                    out += """<LI><A HREF="publiline.py?doctype=%(doctype)s&categ=%(categ)s">%(referee)s</a><br>""" % {
                        'referee' : _("You are a referee for category:") + ' ' + str(category['name']) + ' (' + str(category['id']) + ')',
			'doctype' : doctype['doctype'],
                        'categ' : category['id']}
                    
            out += "</small></UL></UL>"

        out += "</td></tr></table>"
        return out

    def tmpl_publiline_selectdoctype(self, ln, docs):
        """
        Displays the doctypes that the user can select

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'docs' *array* - All the doctypes that the user can select:

              - 'doctype' *string* - The doctype

              - 'docname' *string* - The display name of the doctype
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
               <table class="searchbox" width="100%%" summary="">
                  <tr>
                      <th class="portalboxheader">%(list)s</th>
                  </tr>
                  <tr>
                      <td class="portalboxbody">
              %(select)s:
            </small>
            <blockquote>""" % {
              'list' : _("List of refereed types of documents"),
              'select' : _("Select one of the following types of documents to check the documents status."),
            }

        for doc in docs:
            out += "<li><A HREF='publiline.py?doctype=%(doctype)s'>%(docname)s</A><BR>" % doc

        out += """</blockquote>
                </td>
            </tr>
        </table>"""
        return out

    def tmpl_publiline_selectcateg(self, ln, doctype, title, categories, images):
        """
        Displays the categories from a doctype that the user can select

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'doctype' *string* - The doctype

          - 'title' *string* - The doctype name

          - 'images' *string* - the path to the images

          - 'categories' *array* - All the categories that the user can select:

              - 'id' *string* - The id of the category

              - 'waiting' *int* - The number of documents waiting

              - 'approved' *int* - The number of approved documents

              - 'rejected' *int* - The number of rejected documents
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
               <table class="searchbox" width="100%%" summary="">
                  <tr>
                    <th class="portalboxheader">%(title)s: %(list_categ)s</th>
                  </tr>
                  <tr>
                      <td class="portalboxbody">
                      %(choose_categ)s
                      <blockquote>
                      <FORM action="publiline.py" method="get">
                          <INPUT type="hidden" name="doctype" value='%(doctype)s'>
                          <INPUT type="hidden" name="categ" value=''>
                          </FORM>
               <TABLE>
                 <TR>
                   <TD align=left>""" % {
                 'title' : title,
                 'doctype' : doctype,
                 'list_categ' : _("List of refereed categories"),
                 'choose_categ' : _("Please choose a category"),
               }

        for categ in categories:
            num = categ['waiting'] + categ['approved'] + categ['rejected']

            if categ['waiting'] != 0:
                classtext = "class=\"blocknote\""
            else:
                classtext = ""

            out += """<A href="" onClick="document.forms[0].categ.value='%(id)s';document.forms[0].submit();return false;"><SMALL %(classtext)s>%(id)s</SMALL></A><SMALL> (%(num)s document(s)</SMALL>""" % {
                     'id' : categ['id'],
                     'classtext' : classtext,
                     'num' : num,
                   }
            if categ['waiting'] != 0:
                out += """| %(waiting)s <IMG ALT="%(pending)s" SRC="%(images)s/waiting_or.gif" border="0">""" % {
                          'waiting' : categ['waiting'],
                          'pending' : _("Pending"),
                          'images' : images,
                        }
            if categ['approved'] != 0:
                out += """| %(approved)s<IMG ALT="%(approved_text)s" SRC="%(images)s/smchk_gr.gif" border="0">""" % {
                          'approved' : categ['approved'],
                          'approved_text' : _("Approved"),
                          'images' : images,
                        }
            if categ['rejected'] != 0:
                out += """| %(rejected)s<IMG ALT="%(rejected_text)s" SRC="%(images)s/cross_red.gif" border="0">""" % {
                          'rejected' : categ['rejected'],
                          'rejected_text' : _("Rejected"),
                          'images' : images,
                        }
            out += ")</SMALL><BR>"

        out += """
                    </TD>
                    <TD>
                     <table class="searchbox" width="100%%" summary="">
                        <tr>
                            <th class="portalboxheader">%(key)s:</th>
                        <tr>
                        <tr>
                            <td>
                              <IMG ALT="%(pending)s" SRC="%(images)s/waiting_or.gif" border="0"> %(waiting)s<BR>
                              <IMG ALT="%(approved)s" SRC="%(images)s/smchk_gr.gif" border="0"> %(already_approved)s<BR>
                              <IMG ALT="%(rejected)s" SRC="%(images)s/cross_red.gif" border="0"> %(rejected_text)s<BR><BR>
                              <SMALL class="blocknote">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</SMALL> %(somepending)s<BR></SMALL>
                            </td>
                        </tr>
                    </table>
                  </TD>
                </TR>
                </TABLE>
              </blockquote>
              </td>
             </tr>
            </table>""" % {
              'key' : _("Key"),
              'pending' : _("Pending"),
              'images' : images,
              'waiting' : _("Waiting for approval"),
              'approved' : _("Approved"),
              'already_approved' : _("Already approved"),
              'rejected' : _("Rejected"),
              'rejected_text' : _("Rejected"),
              'somepending' : _("Some documents are pending."),
            }
        return out

    def tmpl_publiline_selectdocument(self, ln, doctype, title, categ, images, docs):
        """
        Displays the documents that the user can select in the specified category

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'doctype' *string* - The doctype

          - 'title' *string* - The doctype name

          - 'images' *string* - the path to the images

          - 'categ' *string* - the category

          - 'docs' *array* - All the categories that the user can select:

              - 'RN' *string* - The id of the document

              - 'status' *string* - The status of the document
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
               <table class="searchbox" width="100%%" summary="">
                  <tr>
                    <th class="portalboxheader">%(title)s - %(categ)s: %(list)s</th>
                  </tr>
                  <tr>
                    <td class="portalboxbody">
                    %(choose_report)s
                    <blockquote>
                      <FORM action="publiline.py" method="get">
                        <INPUT type="hidden" name="doctype" value='%(doctype)s'>
                        <INPUT type="hidden" name="categ" value='%(categ)s'>
                        <INPUT type="hidden" name="RN" value=''>
                        </FORM>
                  <TABLE class="searchbox">
                    <TR>
                      <TH class="portalboxheader">%(report_no)s</TH>
                      <TH class="portalboxheader">%(pending)s</TH>
                      <TH class="portalboxheader">%(approved)s</TH>
                      <TH class="portalboxheader">%(rejected)s</TH>
                    </TR>
              """ % {
                'doctype' : doctype,
                'title' : title,
                'categ' : categ,
                'list' : _("List of refereed documents"),
                'choose_report' : _("Click on a report number for more information."),
                'report_no' : _("Report Number"),
                'pending' : _("Pending"),
                'approved' : _("Approved"),
                'rejected' : _("Rejected"),
              }

        for doc in docs:
            status = doc ['status']
            
            if status == "waiting":
                out += """<TR>
                            <TD align="center">
                              <A HREF="" onClick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</A>
                            </TD>
                            <TD align="center">
                              <IMG ALT="check" SRC="%(images)s/waiting_or.gif">
                            </TD>
                            <TD align="center">&nbsp;</TD>
                            <TD align="center">&nbsp;</TD>
                          </TR>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : images,
                       }
            elif status == "rejected":
                out += """<TR>
                            <TD align="center">
                              <A HREF="" onClick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</A>
                            </TD>
                            <TD align="center">&nbsp;</TD>
                            <TD align="center">&nbsp;</TD>
                            <TD align="center"><IMG ALT="check" SRC="%(images)s/cross_red.gif"></TD>
                          </TR>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : images,
                       }
            elif status == "approved":
                out += """<TR>
                            <TD align="center">
                              <A HREF="" onClick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</A>
                            </TD>
                            <TD align="center">&nbsp;</TD>
                            <TD align="center"><IMG ALT="check" SRC="%(images)s/smchk_gr.gif"></TD>
                            <TD align="center">&nbsp;</TD>
                          </TR>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : images,
                       }
        out += """  </TABLE>
                    </blockquote>
                   </td>
                  </tr>
                 </table>"""
        return out

    def tmpl_publiline_displaydoc(self, ln, doctype, docname, categ, rn, status, dFirstReq, dLastReq, dAction, access, images, accessurl, confirm_send, auth_code, auth_message, authors, title, sysno, newrn):
        """
        Displays the categories from a doctype that the user can select

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'doctype' *string* - The doctype

          - 'docname' *string* - The doctype name

          - 'categ' *string* - the category

          - 'rn' *string* - The document RN (id number)

          - 'status' *string* - The status of the document

          - 'dFirstReq' *string* - The date of the first approval request

          - 'dLastReq' *string* - The date of the last approval request

          - 'dAction' *string* - The date of the last action (approval or rejection)

          - 'images' *string* - the path to the images

          - 'accessurl' *string* - the URL of the publications

          - 'confirm_send' *bool* - must display a confirmation message about sending approval email

          - 'auth_code' *bool* - authorised to referee this document

          - 'auth_message' *string* - ???

          - 'authors' *string* - the authors of the submission

          - 'title' *string* - the title of the submission

          - 'sysno' *string* - the unique database id for the record

          - 'newrn' *string* - the record number assigned to the submission
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if status == "waiting":
            image = """<IMG SRC="%s/waiting_or.gif" ALT="" align="right">""" % images
        elif status == "approved":
            image = """<IMG SRC="%s/smchk_gr.gif" ALT="" align="right">""" % images
        elif status == "rejected":
            image = """<IMG SRC="%s/iconcross.gif" ALT="" align="right">""" % images
        else:
            image = ""
        out = """
                <table class="searchbox" summary="">
                 <tr>
                  <th class="portalboxheader">%(image)s %(rn)s</th>
                 </tr>
                 <tr>
                   <td class="portalboxbody">""" % {
                   'image' : image,
                   'rn' : rn,
                 }
        if confirm_send:
            out += """<I><strong class="headline">%(requestsent)s</strong></I><BR><BR>""" % {
                     'requestsent' : _("Your request has been sent to the referee."),
                   }

        out += """<FORM action="publiline.py">
                    <INPUT type="hidden" name="RN" value="%(rn)s">
                    <INPUT type="hidden" name="categ" value="%(categ)s">
                    <INPUT type="hidden" name="doctype" value="%(doctype)s">
                  <SMALL>""" % {
                 'rn' : rn,
                 'categ' : categ,
                 'doctype' : doctype,
               }
        if title != "unknown":
            out += """<strong class="headline">%(title_text)s</strong>%(title)s<BR><BR>""" % {
                     'title_text' : _("Title:"),
                     'title' : title,
                   }

        if authors != "":
            out += """<strong class="headline">%(author_text)s</strong>%(authors)s<BR><BR>""" % {
                     'author_text' : _("Author:"),
                     'authors' : authors,
                   }
        if sysno != "":
            out += """<strong class="headline">%(more)s</strong>
                        <a href="%(url)s?id=%(sysno)s">%(click)s</a>
                        <br /><br />
                   """ % {
                     'more' : _("More information:"),
                     'click' : _("Click here"),
                     'url' : accessurl,
                     'sysno' : sysno,
                   }

        if status == "waiting":
            out += _("This document is still %(x_fmt_open)swaiting for approval%(x_fmt_close)s.") % {'x_fmt_open': '<strong class="headline">', 
                                                                                                     'x_fmt_close': '</strong>'}
	    out += "<br /><br />"
	    out += _("It was first sent for approval on:") + ' <strong class="headline">' + str(dFirstReq) + '</strong><br />'
            if dLastReq == "0000-00-00 00:00:00":
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dFirstReq) + '</strong><br />'
            else:
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dLastReq) + '</strong><br />'
            out += "<br />" + _("You can send an approval request email again by clicking the following button:") + " <br />" +\
                   """<input class="adminbutton" type="submit" name="send" value="%(send)s" onClick="return confirm('%(warning)s')">""" % {
                     'send' : _("Send Again"),
                     'warning' : _("WARNING! Upon confirmation, an email will be sent to the referee.")
                   }
            if auth_code == 0:
                out += "<br />" + _("As a referee for this document, you may click this button to approve or reject it.") + ":<br />" +\
                       """<input class="adminbutton" type="submit" name="approval" value="%(approve)s" onClick="window.location='approve.py?%(access)s';return false;">""" % {
                         'approve' : _("Approve/Reject"),
                         'access' : access
                       }
        if status == "approved":
            out += _("This document has been %(x_fmt_open)sapproved%(x_fmt_close)s.") % {'x_fmt_open': '<strong class="headline">', 
                                                                                         'x_fmt_close': '</strong>'}
            out += '<br />' + _("Its approved reference is:") + ' <strong class="headline">' + str(newrn) + '</strong><br /><br />'
            out += _("It was first sent for approval on:") + ' <strong class="headline">' + str(dFirstReq) + '</strong><br />'
            if dLastReq == "0000-00-00 00:00:00":
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dFirstReq) + '</strong><br />'
            else:
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dLastReq) + '</strong><br />' +\
                       _("It was approved on:") + ' <strong class="headline">' + str(dAction) + '</strong><br />'
        if status == "rejected":
            out += _("This document has been %(x_fmt_open)srejected%(x_fmt_close)s.") % {'x_fmt_open': '<strong class="headline">',
                                                                                         'x_fmt_close': '</strong>'} 
            out += "<br /><br />"
            out += _("It was first sent for approval on:") + ' <strong class="headline">' + str(dFirstReq) +'</strong><br />'
            if dLastReq == "0000-00-00 00:00:00":
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dFirstReq) + '</strong><br />'
            else:
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dLastReq) +'</strong><br />'
            out += _("It was rejected on:") + ' <strong class="headline">' + str(dAction) + '</strong><br />'

        out += """    </SMALL></FORM>
                      <BR></TD></TR></TABLE>
                     </blockquote>
                    </td>
                   </tr>
                  </table>"""
        return out
