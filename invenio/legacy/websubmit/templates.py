# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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

import cgi
import re
import operator

from invenio.config import CFG_SITE_URL, CFG_SITE_LANG, CFG_SITE_RECORD, \
     CFG_SITE_SECURE_URL, CFG_INSPIRE_SITE
from invenio.base.i18n import gettext_set_language
from invenio.utils.date import convert_datetext_to_dategui
from invenio.utils.url import create_html_link
from invenio.utils.mail import email_quoted_txt2html
from invenio.utils.html import escape_html, escape_javascript_string
from invenio.legacy.websubmit.config import CFG_WEBSUBMIT_CHECK_USER_LEAVES_SUBMISSION

class Template:

    # Parameters allowed in the web interface for fetching files
    files_default_urlargd = {
        'version': (str, ""), # version "" means "latest"
        'docname': (str, ""), # the docname (optional)
        'format' : (str, ""), # the format
        'verbose' : (int, 0), # the verbosity
        'subformat': (str, ""), # the subformat
        'download': (int, 0), # download as attachment
        }


    def tmpl_submit_home_page(self, ln, catalogues, user_info=None):
        """
        The content of the home page of the submit engine

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'catalogues' *string* - The HTML code for the catalogues list

          - 'user_info' *dict* - The user info object
        """

        # load the right message language
        _ = gettext_set_language(ln)

        login_note = ""
        if user_info and user_info['guest'] == '1':
            login_note = '<em>(' + create_html_link(CFG_SITE_SECURE_URL + '/youraccount/login',
                                          urlargd={'referer': CFG_SITE_SECURE_URL + user_info['uri'],
                                                   'ln': ln},
                                          link_label=cgi.escape(_("Login to display all document types you can access"))) + \
                                          ')</em>'

        return """
          <script type="text/javascript" language="Javascript1.2">
          var allLoaded = 1;
          </script>
           <table class="searchbox" width="100%%" summary="">
              <tr>
                  <th class="portalboxheader">%(document_types)s: %(login_note)s</th>
              </tr>
              <tr>
                  <td class="portalboxbody">
                    <br />
                    %(please_select)s:
                    <br /><br />
                    <table width="100%%">
                    <tr>
                        <td width="50%%" class="narrowsearchboxbody">
                            %(catalogues)s
                        </td>
                    </tr>
                    </table>
                  </td>
              </tr>
            </table>""" % {
              'document_types' : _("Document types available for submission"),
              'please_select' : _("Please select the type of document you want to submit"),
              'catalogues' : catalogues,
              'ln' : ln,
              'login_note' : login_note,
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
            out += "\n<ul>"
            out += self.tmpl_submit_home_catalogs_sub(ln, catalog)
            out += "\n</ul>\n"

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
            out = "<li><font size=\"+1\"><strong>%s</strong></font>\n" % catalog['name']
        else:
            if catalog['level'] == 2:
                out = "<li>%s\n" % cgi.escape(catalog['name'])
            else:
                if catalog['level'] > 2:
                    out = "<li>%s\n" % cgi.escape(catalog['name'])

        if len(catalog['docs']) or len(catalog['sons']):
            out += "<ul>\n"

        if len(catalog['docs']) != 0:
            for row in catalog['docs']:
                out += self.tmpl_submit_home_catalogs_doctype(ln, row)

        if len(catalog['sons']) != 0:
            for row in catalog['sons']:
                out += self.tmpl_submit_home_catalogs_sub(ln, row)

        if len(catalog['docs']) or len(catalog['sons']):
            out += "</ul></li>"
        else:
            out += "</li>"

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

        return """<li>%s</li>""" % create_html_link('%s/submit' % CFG_SITE_URL, {'doctype' : doc['id'], 'ln' : ln}, doc['name'])

    def tmpl_action_page(self, ln, uid, pid, now, doctype,
                         description, docfulldesc, snameCateg,
                         lnameCateg, actionShortDesc, indir,
                         statustext):
        """
        Recursive function that produces a catalog's HTML display

        Parameters:

          - 'ln' *string* - The language to display the interface in

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
              <script language="JavaScript" type="text/javascript">
              var checked = 0;
              function tester() {
              """

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
                </script>
                <form method="get" action="/submit">
                <input type="hidden" name="doctype" value="%(doctype)s" />
                <input type="hidden" name="indir" />
                <input type="hidden" name="access" value="%(now)i_%(pid)s" />

                <input type="hidden" name="act" />
                <input type="hidden" name="startPg" value="1" />
                <input type="hidden" name="mainmenu" value="/submit?doctype=%(doctype)s&amp;ln=%(ln)s" />

                <input type="hidden" name="ln" value="%(ln)s" />
                <table class="searchbox" width="100%%" summary="">
                  <tr>
                    <th class="portalboxheader">%(docfulldesc)s</th>
                  </tr>
                  <tr>
                      <td class="portalboxbody">%(description)s
                        <br />
                        <script language="JavaScript" type="text/javascript">
                        var nbimg = document.images.length + 1;
                        </script>
                        <br />
                        <table align="center" cellpadding="0" cellspacing="0" border="0">
                        <tr valign="top">
                """ % {
                      'select_cat' : _("Please select a category"),
                      'doctype' : doctype,
                      'now' : now,
                      'pid' : pid,
                      'docfulldesc' : docfulldesc,
                      'description' : description,
                      'ln' : ln,
                    }

        if len(snameCateg):
            out += """<td align="right">"""
            selected = ""
            if len(snameCateg) == 1:
                # If there is only one category, we check it automatically
                selected = "checked"
            for i in range(0, len(snameCateg)):
                out += """<label for="combo%(shortname)s">%(longname)s</label><input type="radio" name="combo%(doctype)s" id="combo%(shortname)s" %(selected)s value="%(shortname)s" onclick="clicked();" />&nbsp;<br />""" % {
                         'longname' : lnameCateg[i],
                         'doctype' : doctype,
                         'selected' : selected,
                         'shortname' : snameCateg[i],
                       }
            out += "</td>"
        out += "<td>"
        if len(snameCateg) < 2:
            out += '<script type="text/javascript">checked=1;</script>'
        out += """&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>
                  <td>
                    <table><tr><td>
               """
        #display list of actions
        for i in range(0, len(actionShortDesc)):
            out += """<input type="submit" class="adminbutton" value="%(status)s" onclick="if (tester()) { document.forms[0].indir.value='%(indir)s';document.forms[0].act.value='%(act)s';document.forms[0].submit();}; return false;" /><br />""" % {
                     'status' : statustext[i],
                     'indir' : indir[i],
                     'act' : actionShortDesc[i]
                   }
        out += """  </td></tr></table>
                    </td>
                </tr>
                </table>
                <br />"""
        if len(snameCateg) :
            out += """<strong class="headline">%(notice)s:</strong><br />
                    %(select_cat)s""" % {
                     'notice' : _("Notice"),
                     'select_cat' : _("Select a category and then click on an action button."),
                    }
        out += """
                <br /><br />

                </td>
                </tr>
                </table>
                </form>
                <form action="/submit/continue"><hr />
                  <font color="black"><small>%(continue_explain)s</small></font>
                  <table border="0" bgcolor="#CCCCCC" width="100%%"><tr>
                    <td width="100%%">
                    <small>Access Number: <input size="15" name="access" />
                      <input type="hidden" name="doctype" value="%(doctype)s" />
                      <input type="hidden" name="ln" value="%(ln)s" />
                      <input class="adminbutton" type="submit" value=" %(go)s " />
                    </small>
                    </td></tr>
                  </table>
                  <hr />
                 </form>
                 """ % {
                'continue_explain' : _("To continue with a previously interrupted submission, enter an access number into the box below:"),
                  'doctype' : doctype,
                  'go' : _("GO"),
                  'ln' : ln,
                }

        return out

    def tmpl_page_interface(self, ln, docname, actname, curpage, nbpages, nextPg, access, nbPg, doctype, act, fields, javascript, mainmenu):
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

          - 'mainmenu' *string* - the url of the main menu

        """

        # load the right message language
        _ = gettext_set_language(ln)

        # top menu
        out = """
                <form method="post" action="/submit" enctype="multipart/form-data" onsubmit="return tester();" accept-charset="UTF-8">
                <center><table cellspacing="0" cellpadding="0" border="0">
                  <tr>
                    <td class="submitHeader"><b>%(docname)s&nbsp;</b></td>
                    <td class="submitHeader"><small>&nbsp;%(actname)s&nbsp;</small></td>
                    <td valign="bottom">
                        <table cellspacing="0" cellpadding="0" border="0" width="100%%">
                        <tr><td class="submitEmptyPage">&nbsp;&nbsp;</td>
              """ % {
                'docname' : docname,
                'actname' : actname,
              }

        for i in range(1, nbpages+1):
            if i == int(curpage):
                out += """<td class="submitCurrentPage"><small>&nbsp;page: %s&nbsp;</small></td>""" % curpage
            else:
                out += """<td class="submitPage"><small>&nbsp;<a href='' onclick="if (tester2() == 1){document.forms[0].curpage.value=%s;user_must_confirm_before_leaving_page = false;document.forms[0].submit();return false;} else { return false; }">%s</a>&nbsp;</small></td>""" % (i, i)
        out += """        <td class="submitEmptyPage">&nbsp;&nbsp;
                        </td></tr></table>
                    </td>
                    <td class="submitHeader" align="right">&nbsp;<a href="" onclick="window.open('/submit/summary?doctype=%(doctype)s&amp;act=%(act)s&amp;access=%(access)s&amp;ln=%(ln)s','summary','scrollbars=yes,menubar=no,width=500,height=250');return false;"><font color="white"><small>%(summary)s(2)</small></font></a>&nbsp;</td>
                  </tr>
                  <tr><td colspan="5" class="submitHeader">
                    <table border="0" cellspacing="0" cellpadding="15" width="100%%" class="submitBody"><tr><td>
                     <br />
                     <input type="hidden" name="nextPg" value="%(nextPg)s" />
                     <input type="hidden" name="access" value="%(access)s" />
                     <input type="hidden" name="curpage" value="%(curpage)s" />
                     <input type="hidden" name="nbPg" value="%(nbPg)s" />
                     <input type="hidden" name="doctype" value="%(doctype)s" />
                     <input type="hidden" name="act" value="%(act)s" />
                     <input type="hidden" name="mode" value="U" />
                     <input type="hidden" name="step" value="0" />
                     <input type="hidden" name="ln" value="%(ln)s" />
                """ % {
                 'summary' : _("SUMMARY"),
                 'doctype' : cgi.escape(doctype),
                 'act' : cgi.escape(act),
                 'access' : cgi.escape(access),
                 'nextPg' : cgi.escape(nextPg),
                 'curpage' : cgi.escape(curpage),
                 'nbPg' : cgi.escape(nbPg),
                 'ln' : cgi.escape(ln),
               }

        for field in fields:
            if field['javascript']:
                out += """<script language="JavaScript1.1"  type="text/javascript">
                          %s
                          </script>
                       """ % field['javascript']

            # now displays the html form field(s)
            out += "%s\n%s\n" % (field['fullDesc'], field['text'])

        out += javascript
        out += "<br />&nbsp;<br />&nbsp;</td></tr></table></td></tr>\n"

        # Display the navigation cell
        # Display "previous page" navigation arrows
        out += """<tr><td colspan="5"><table border="0" cellpadding="0" cellspacing="0" width="100%%"><tr>"""
        if int(curpage) != 1:
            out += """ <td class="submitHeader" align="left">&nbsp;
                         <a href='' onclick="if (tester2() == 1) {document.forms[0].curpage.value=%(prpage)s;user_must_confirm_before_leaving_page = false;document.forms[0].submit();return false;} else { return false; }">
                           <img src="%(images)s/left-trans.gif" alt="%(prevpage)s" border="0" />
                             <strong><font color="white">%(prevpage)s</font></strong>
                         </a>
                       </td>
            """ % {
              'prpage' : int(curpage) - 1,
              'images' : CFG_SITE_URL + '/img',
              'prevpage' : _("Previous page"),
            }
        else:
            out += """ <td class="submitHeader">&nbsp;</td>"""
        # Display the submission number
        out += """ <td class="submitHeader" align="center"><small>%(submission)s: %(access)s</small></td>\n""" % {
                'submission' : _("Submission number") + '(1)',
                'access' : cgi.escape(access),
              }
        # Display the "next page" navigation arrow
        if int(curpage) != int(nbpages):
            out += """ <td class="submitHeader" align="right">
                         <a href='' onclick="if (tester2()){document.forms[0].curpage.value=%(nxpage)s;user_must_confirm_before_leaving_page = false;document.forms[0].submit();return false;} else {return false;}; return false;">
                          <strong><font color="white">%(nextpage)s</font></strong>
                          <img src="%(images)s/right-trans.gif" alt="%(nextpage)s" border="0" />
                        </a>
                       </td>
            """ % {
              'nxpage' : int(curpage) + 1,
              'images' : CFG_SITE_URL + '/img',
              'nextpage' : _("Next page"),
            }
        else:
            out += """ <td class="submitHeader">&nbsp;</td>"""
        out += """</tr></table></td></tr></table></center></form>

                  <br />
                  <br />
                 <a href="%(mainmenu)s" onclick="if (%(check_not_already_enabled)s){return confirm('%(surequit)s')}">
                 <img src="%(images)s/mainmenu.gif" border="0" alt="%(back)s" align="right" /></a>
                 <br /><br />
                 <hr />
                  <small>%(take_note)s</small><br />
                  <small>%(explain_summary)s</small><br />
               """ % {
                 'surequit' : _("Are you sure you want to quit this submission?"),
                 'check_not_already_enabled': CFG_WEBSUBMIT_CHECK_USER_LEAVES_SUBMISSION and 'false' or 'true',
                 'back' : _("Back to main menu"),
                 'mainmenu' : cgi.escape(mainmenu),
                 'images' : CFG_SITE_URL + '/img',
                 'take_note' : '(1) ' + _("This is your submission access number. It can be used to continue with an interrupted submission in case of problems."),
                 'explain_summary' : not CFG_INSPIRE_SITE and  '(2) ' + _("Mandatory fields appear in red in the SUMMARY window.") or ''
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
            ## Field is a textarea:
            text = "<textarea name=\"%s\" rows=\"%s\" cols=\"%s\">%s</textarea>" \
                  % (field['name'], field['rows'], field['cols'], cgi.escape(str(field['val']), 1))
        # If the field is a file upload
        elif field['type'] == 'F':
            ## the field is a file input:
            text = """<input type="file" name="%s" size="%s"%s />""" \
                   % (field['name'], field['size'], "%s" \
                      % ((field['maxlength'] in (0, None) and " ") or (""" maxlength="%s\"""" % field['maxlength'])) )
        # If the field is a text input
        elif field['type'] == 'I':
            ## Field is a text input:
            text = """<input type="text" name="%s" size="%s" value="%s"%s />""" \
                   % (field['name'], field['size'], field['val'], "%s" \
                      % ((field['maxlength'] in (0, None) and " ") or (""" maxlength="%s\"""" % field['maxlength'])) )
        # If the field is a hidden input
        elif field['type'] == 'H':
            text = "<input type=\"hidden\" name=\"%s\" value=\"%s\" />" % (field['name'], field['val'])
        # If the field is user-defined
        elif field['type'] == 'D':
            text = field['htmlcode']
        # If the field is a select box
        elif field['type'] == 'S':
            text = field['htmlcode']
        # If the field type is not recognized
        else:
            text = "%s: unknown field type" % field['typename']

        return text

    def tmpl_page_interface_js(self, ln, upload, field, fieldhtml, txt, check, level, curdir, values, select, radio, curpage, nbpages, returnto):
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

          - 'returnto' *array* - a structure with 'field' and 'page', if a mandatory field on antoher page was not completed
        """

        # load the right message language
        _ = gettext_set_language(ln)

        nbFields = len(upload)
        # if there is a file upload field, we change the encoding type
        out = """<script language="JavaScript1.1" type="text/javascript">
        /*<![CDATA[*/
              """
        for i in range(0, nbFields):
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
        for i in range(0, nbFields):
            if re.search("%s\[\]" % field[i], fieldhtml[i]):
                fieldname = "%s[]" % field[i]
            else:
                fieldname = field[i]
            out += "  el = document.forms[0].elements['%s'];\n" % fieldname
            # If the field must be checked we call the checking function
            if check[i] != "":
                out += """if (el !== undefined && %(check)s(el.value) == 0) {
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
                                'field_mandatory' : _("The field %(field)s is mandatory.", field=txt[i]) + '\\n' + _("Please make a choice in the select box")
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
                                'field_mandatory' : _("The field %(field)s is mandatory. Please fill it in.", field=txt[i])
                              }
        out += """  return 1;
                  }
               <!-- Fill the fields in with the previous saved values-->
               """

        # # # # # # # # # # # # # # # # # # # # # # # # #
        # Fill the fields with the previously saved values
        # # # # # # # # # # # # # # # # # # # # # # # # #
        for i in range(0, nbFields):
            if re.search("%s\[\]"%field[i], fieldhtml[i]):
                fieldname = "%s[]" % field[i]
            else:
                fieldname = field[i]
            text = values[i]

            if text != '':
                if select[i] != 0:
                    # If the field is a SELECT element
                    vals = text.split("\n")
                    tmp = ""
                    for val in vals:
                        if tmp != "":
                            tmp += " || "
                        tmp += "el.options[j].value == \"%s\" || el.options[j].text == \"%s\"" % \
                          (escape_javascript_string(val, escape_for_html=False),
                           escape_javascript_string(val, escape_for_html=False))
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
                                'text' : escape_javascript_string(text, escape_for_html=False),
                              }
                elif upload[i] == 0:
                    # If the field is not an upload element
                    out += """<!--input field found-->
                               el = document.forms[0].elements['%(fieldname)s'];
                               el.value="%(text)s";
                           """ % {
                             'fieldname' : fieldname,
                             'text': escape_javascript_string(text, escape_for_html=False),
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
                          user_must_confirm_before_leaving_page = false;
                          document.forms[0].submit();
                         }
                       """ % {
                         'msg' : _("The field %(field)s is mandatory.") % returnto + '\\n' \
                                 + _("Going back to page") \
                                 + " " + str(returnto['page']),
                         'page' : returnto['page']
                       }
            else:
                out += """ if (tester2()) {
                             $(this).attr("disabled", true);
                             document.forms[0].action="/submit";
                             document.forms[0].step.value=1;
                             user_must_confirm_before_leaving_page = false;
                             document.forms[0].submit();
                           } else {
                             return false;
                           }
                         }"""
        out += """ /*]]>*/</script>"""
        return out

    def tmpl_page_do_not_leave_submission_js(self, ln, enabled=CFG_WEBSUBMIT_CHECK_USER_LEAVES_SUBMISSION):
        """
        Code to ask user confirmation when leaving the page, so that the
        submission is not interrupted by mistake.

        All submission functions should set the Javascript variable
        'user_must_confirm_before_leaving_page' to 'false' before
        programmatically submitting the submission form.

        Parameters:
        - 'ln' *string* - The language to display the interface in
        - 'enabled' *bool* - If the check applies or not
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = '''
        <script language="JavaScript">
            var user_must_confirm_before_leaving_page = %s;

            window.onbeforeunload = confirmExit;
            function confirmExit() {
            if (user_must_confirm_before_leaving_page)
                return "%s";
            }

        </script>
        ''' % (enabled and 'true' or 'false',
               _('Your modifications will not be saved.').replace('"', '\\"'))

        return out

    def tmpl_page_endaction(self, ln, nextPg, startPg, access, curpage, nbPg, nbpages, doctype, act, docname, actname, mainmenu, finished, function_content, next_action):
        """
        Produces the pages after all the fields have been submitted.

        Parameters:

          - 'ln' *string* - The language to display the interface in

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


          - 'mainmenu' *string* - the url of the main menu

          - 'finished' *bool* - if the submission is finished

          - 'function_content' *string* - HTML code produced by some function executed

          - 'next_action' *string* - if there is another action to be completed, the HTML code for linking to it
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """
          <form ENCTYPE="multipart/form-data" action="/submit" onsubmit="user_must_confirm_before_leaving_page=false;" method="post" accept-charset="UTF-8">
          <input type="hidden" name="nextPg" value="%(nextPg)s" />
          <input type="hidden" name="startPg" value="%(startPg)s" />
          <input type="hidden" name="access" value="%(access)s" />
          <input type="hidden" name="curpage" value="%(curpage)s" />
          <input type="hidden" name="nbPg" value="%(nbPg)s" />
          <input type="hidden" name="doctype" value="%(doctype)s" />
          <input type="hidden" name="act" value="%(act)s" />
          <input type="hidden" name="fromdir" value="" />
          <input type="hidden" name="mainmenu" value="%(mainmenu)s" />

          <input type="hidden" name="mode" value="U" />
          <input type="hidden" name="step" value="1" />
          <input type="hidden" name="deleted" value="no" />
          <input type="hidden" name="file_path" value="" />
          <input type="hidden" name="userfile_name" value="" />

          <input type="hidden" name="ln" value="%(ln)s" />
          <center><table cellspacing="0" cellpadding="0" border="0"><tr>
             <td class="submitHeader"><b>%(docname)s&nbsp;</b></td>
             <td class="submitHeader"><small>&nbsp;%(actname)s&nbsp;</small></td>
             <td valign="bottom">
                 <table cellspacing="0" cellpadding="0" border="0" width="100%%">
                 <tr><td class="submitEmptyPage">&nbsp;&nbsp;</td>
              """ % {
                'nextPg' : cgi.escape(nextPg),
                'startPg' : cgi.escape(startPg),
                'access' : cgi.escape(access),
                'curpage' : cgi.escape(curpage),
                'nbPg' : cgi.escape(nbPg),
                'doctype' : cgi.escape(doctype),
                'act' : cgi.escape(act),
                'docname' : docname,
                'actname' : actname,
                'mainmenu' : cgi.escape(mainmenu),
                'ln' : cgi.escape(ln),
              }

        if finished == 1:
            out += """<td class="submitCurrentPage">%(finished)s</td>
                      <td class="submitEmptyPage">&nbsp;&nbsp;</td>
                     </tr></table>
                    </td>
                    <td class="submitEmptyPage" align="right">&nbsp;</td>
                   """ % {
                     'finished' : _("finished!"),
                   }
        else:
            for i in range(1, nbpages + 1):
                out += """<td class="submitPage"><small>&nbsp;
                            <a href='' onclick="document.forms[0].curpage.value=%s;document.forms[0].action='/submit';document.forms[0].step.value=0;user_must_confirm_before_leaving_page = false;document.forms[0].submit();return false;">%s</a>&nbsp;</small></td>""" % (i, i)
            out += """<td class="submitCurrentPage">%(end_action)s</td><td class="submitEmptyPage">&nbsp;&nbsp;</td></tr></table></td>
                      <td class="submitHeader" align="right">&nbsp;<a href='' onclick="window.open('/submit/summary?doctype=%(doctype)s&amp;act=%(act)s&amp;access=%(access)s&amp;ln=%(ln)s','summary','scrollbars=yes,menubar=no,width=500,height=250');return false;"><font color="white"><small>%(summary)s(2)</small></font></a>&nbsp;</td>""" % {
                        'end_action' : _("end of action"),
                        'summary' : _("SUMMARY"),
                        'doctype' : cgi.escape(doctype),
                        'act' : cgi.escape(act),
                        'access' : cgi.escape(access),
                        'ln' : cgi.escape(ln),
                      }
        out += """</tr>
                  <tr>
                    <td colspan="5" class="submitBody">
                      <small><br /><br />
                      %(function_content)s
                      %(next_action)s
                      <br /><br />
                    </td>
                </tr>
                <tr class="submitHeader">
                    <td class="submitHeader" colspan="5" align="center">""" % {
                       'function_content' : function_content,
                       'next_action' : next_action,
                     }
        if finished == 0:
            out += """<small>%(submission)s</small>&sup2;:
                      <small>%(access)s</small>""" % {
                        'submission' : _("Submission no"),
                        'access' : cgi.escape(access),
                      }
        else:
            out += "&nbsp;\n"
        out += """
            </td>
        </tr>
        </table>
        </center>
        </form>
        <br />
        <br />"""
        # Add the "back to main menu" button
        if finished == 0:
            out += """ <a href="%(mainmenu)s" onclick="if (%(check_not_already_enabled)s){return confirm('%(surequit)s')}">
                       <img src="%(images)s/mainmenu.gif" border="0" alt="%(back)s" align="right" /></a>
                       <br /><br />""" % {
                           'surequit' : _("Are you sure you want to quit this submission?"),
                           'back' : _("Back to main menu"),
                           'images' : CFG_SITE_URL + '/img',
                           'mainmenu' : cgi.escape(mainmenu),
                           'check_not_already_enabled': CFG_WEBSUBMIT_CHECK_USER_LEAVES_SUBMISSION and 'false' or 'true',
                           }
        else:
            out += """ <a href="%(mainmenu)s">
                       <img src="%(images)s/mainmenu.gif" border="0" alt="%(back)s" align="right" /></a>
                       <br /><br />""" % {
                     'back' : _("Back to main menu"),
                     'images' : CFG_SITE_URL + '/img',
                     'mainmenu' : cgi.escape(mainmenu),
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
            out += """<br /><br />%(function_list)s<P>
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
                          'result' : function['error'] and (_("Function %(x_name)s does not exist.", x_name=function['name']) + "<br />") or function['text']
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

        out = "<br /><br />%(haveto)s<ul>" % {
                'haveto' : _("You must now"),
              }
        i = 0
        for action in actions:
            if i > 0:
                out += " <b>" + _("or") + "</b> "
            i += 1
            out += """<li><a href="" onclick="document.forms[0].action='/submit';document.forms[0].curpage.value='%(page)s';document.forms[0].startPg.value='%(page)s';document.forms[0].act.value='%(action)s';document.forms[0].doctype.value='%(doctype)s';document.forms[0].indir.value='%(nextdir)s';document.forms[0].access.value='%(access)s';document.forms[0].fromdir.value='%(indir)s';user_must_confirm_before_leaving_page = falsedocument.forms[0].submit();return false;"> %(name)s </a></li>""" % action

        out += "</ul>"
        return out

    def tmpl_submit_summary (self, ln, values):
        """
        Displays the summary for the submit procedure.

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'values' *array* - The values of submit. Each of the records contain the following fields:

                - 'name' *string* - The name of the field

                - 'mandatory' *bool* - If the field is mandatory or not

                - 'value' *string* - The inserted value

                - 'page' *int* - The submit page on which the field is entered
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = """<body style="background-image: url(%(images)s/header_background.gif);"><table border="0">""" % \
              { 'images' : CFG_SITE_URL + '/img' }

        for value in values:
            if value['mandatory']:
                color = "red"
            else:
                color = ""
            out += """<tr>
                        <td align="right">
                          <small>
                            <a href='' onclick="window.opener.document.forms[0].curpage.value='%(page)s';window.opener.document.forms[0].action='/submit?ln=%(ln)s';window.opener.document.forms[0].submit();return false;">
                              <font color="%(color)s">%(name)s</font>
                            </a>
                          </small>
                        </td>
                        <td>
                          <i><small><font color="black">%(value)s</font></small></i>
                        </td>
                      </tr>""" % {
                        'color' : color,
                        'name' : value['name'],
                        'value' : value['value'],
                        'page' : value['page'],
                        'ln' : ln
                      }
        out += "</table>"
        return out

    def tmpl_yoursubmissions(self, ln, order, doctypes, submissions):
        """
        Displays the list of the user's submissions.

        Parameters:

          - 'ln' *string* - The language to display the interface in

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
                  <br />
                  <form action="">
                  <input type="hidden" value="%(order)s" name="order" />
                  <input type="hidden" name="deletedId" />
                  <input type="hidden" name="deletedDoctype" />
                  <input type="hidden" name="deletedAction" />
                  <input type="hidden" name="ln" value="%(ln)s"/>
                  <table class="searchbox" width="100%%" summary="" >
                    <tr>
                      <th class="portalboxheader">%(for)s&nbsp;
                        <select name="doctype" onchange="document.forms[0].submit();">
                          <option value="">%(alltype)s</option>
                  """ % {
                    'order' : order,
                    'for' : _("For"),
                    'alltype' : _("all types of document"),
                    'ln' : ln,
                  }
        for doctype in doctypes:
            out += """<option value="%(id)s" %(sel)s>%(name)s</option>""" % {
                     'id' : doctype['id'],
                     'name' : doctype['name'],
                     'sel' : doctype['selected'] and "selected=\"selected\"" or ""
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
                          <br/>&nbsp;<br/><h3>%(docname)s</h3>
                          <table border="0" class="searchbox" align="left" width="100%%">
                            <tr>
                              <th class="headerselected">%(action)s&nbsp;&nbsp;
                                <a href='' onclick='document.forms[0].order.value="actiondown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" alt="down" border="0" /></a>&nbsp;
                                <a href='' onclick='document.forms[0].order.value="actionup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" alt="up" border="0" /></a>
                              </th>
                              <th class="headerselected">%(status)s&nbsp;&nbsp;
                                <a href='' onclick='document.forms[0].order.value="statusdown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" alt="down" border="0" /></a>&nbsp;
                                <a href='' onclick='document.forms[0].order.value="statusup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" alt="up" border="0" /></a>
                              </th>
                              <th class="headerselected">%(id)s</th>
                              <th class="headerselected">%(reference)s&nbsp;&nbsp;
                                <a href='' onclick='document.forms[0].order.value="refdown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" alt="down" border="0" /></a>&nbsp;
                                <a href='' onclick='document.forms[0].order.value="refup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" alt="up" border="0" /></a>
                              </th>
                              <th class="headerselected">%(first)s&nbsp;&nbsp;
                                <a href='' onclick='document.forms[0].order.value="cddown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" alt="down" border="0" /></a>&nbsp;
                                <a href='' onclick='document.forms[0].order.value="cdup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" alt="up" border="0" /></a>
                              </th>
                              <th class="headerselected">%(last)s&nbsp;&nbsp;
                                <a href='' onclick='document.forms[0].order.value="mddown";document.forms[0].submit();return false;'><img src="%(images)s/smalldown.gif" alt="down" border="0" /></a>&nbsp;
                                <a href='' onclick='document.forms[0].order.value="mdup";document.forms[0].submit();return false;'><img src="%(images)s/smallup.gif" alt="up" border="0" /></a>
                              </th>
                            </tr>
                       """ % {
                         'docname' : submission['docname'],
                         'action' : _("Action"),
                         'status' : _("Status"),
                         'id' : _("Subm.No."),
                         'reference' : _("Reference"),
                         'images' : CFG_SITE_URL + '/img',
                         'first' : _("First access"),
                         'last' : _("Last access"),
                       }
            if submission['pending']:
                idtext = """<a href="submit/direct?access=%(id)s&sub=%(action)s%(doctype)s%(ln_link)s">%(id)s</a>
                            &nbsp;<a onclick='if (confirm("%(sure)s")){document.forms[0].deletedId.value="%(id)s";document.forms[0].deletedDoctype.value="%(doctype)s";document.forms[0].deletedAction.value="%(action)s";document.forms[0].submit();return true;}else{return false;}' href=''><img src="%(images)s/smallbin.gif" border="0" alt='%(delete)s' /></a>
                         """ % {
                           'images' : CFG_SITE_URL + '/img',
                           'id' : submission['id'],
                           'action' : submission['act'],
                           'doctype' : submission['doctype'],
                           'sure' : _("Are you sure you want to delete this submission?"),
                           'delete' : _("Delete submission %(x_id)s in %(x_docname)s") % {
                                        'x_id' : str(submission['id']),
                                        'x_docname' : str(submission['docname'])
                                      },
                           'ln_link': (ln != CFG_SITE_LANG and '&amp;ln=' + ln) or ''
                         }
            else:
                idtext = submission['id']

            if operator.mod(num, 2) == 0:
                color = "#e2e2e2"
            else:
                color = "#f0f0f0"

            if submission['reference']:
                reference = submission['reference']
                if not submission['pending']:
                    # record was integrated, so propose link:
                    reference = create_html_link('%s/search' % CFG_SITE_URL, {
                        'ln' : ln,
                        'p' : submission['reference'],
                        'f' : 'reportnumber'
                        }, submission['reference'])
            else:
                reference = """<font color="red">%s</font>""" % _("Reference not yet given")

            cdate = str(submission['cdate']).replace(" ", "&nbsp;")
            mdate = str(submission['mdate']).replace(" ", "&nbsp;")

            out += """
                     <tr bgcolor="%(color)s">
                       <td align="center" class="mycdscell">
                         %(actname)s
                       </td>
                       <td align="center" class="mycdscell">
                         %(status)s
                       </td>
                       <td class="mycdscell">
                         %(idtext)s
                       </td>
                       <td class="mycdscell">
                         &nbsp;%(reference)s
                       </td>
                       <td class="mycdscell">
                         %(cdate)s
                       </td>
                       <td class="mycdscell">
                         %(mdate)s
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
            out += """<ul><li><b>%(docname)s</b><ul>""" % doctype

            if doctype ['categories'] is None:
                out += '''<li><a href="publiline.py?doctype=%(doctype)s%(ln_link)s">%(generalref)s</a></li>''' % {
                    'docname' : doctype['docname'],
                    'doctype' : doctype['doctype'],
                    'generalref' : _("You are a general referee"),
                    'ln_link': '&amp;ln=' + ln}

            else:
                for category in doctype['categories']:
                    out += """<li><a href="publiline.py?doctype=%(doctype)s&amp;categ=%(categ)s%(ln_link)s">%(referee)s</a></li>""" % {
                        'referee' : _("You are a referee for category:") + ' ' + str(category['name']) + ' (' + str(category['id']) + ')',
                        'doctype' : doctype['doctype'],
                        'categ' : category['id'],
                        'ln_link': '&amp;ln=' + ln}

            out += "</ul><br /></li></ul>"

        out += "</td></tr></table>"
        out += '''<p>To see the status of documents for which approval has been requested, click <a href=\"%(url)s/publiline.py?flow=cplx\">here</a></p>''' % {'url' : CFG_SITE_URL}
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
              'select' : _("Select one of the following types of documents to check the documents status"),
            }

        for doc in docs:
            params = {'ln' : ln}
            params.update(doc)
            out += '<li><a href="publiline.py?doctype=%(doctype)s&amp;ln=%(ln)s">%(docname)s</a></li><br />' % params

        out += """</blockquote>
                </td>
            </tr>
        </table>

        <a href="publiline.py?flow=cplx&amp;ln=%s">%s</a>""" % (ln, _("Go to specific approval workflow"))
        return out

    def tmpl_publiline_selectcplxdoctype(self, ln, docs):
        """
        Displays the doctypes that the user can select in a complex workflow

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
              'select' : _("Select one of the following types of documents to check the documents status"),
            }

        for doc in docs:
            params = {'ln' : ln}
            params.update(doc)
            out += '<li><a href="publiline.py?flow=cplx&doctype=%(doctype)s&amp;ln=%(ln)s">%(docname)s</a></li><br />' % params

        out += """</blockquote> </td> </tr> </table> </li><br/>"""
        return out

    def tmpl_publiline_selectcateg(self, ln, doctype, title, categories):
        """
        Displays the categories from a doctype that the user can select

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'doctype' *string* - The doctype

          - 'title' *string* - The doctype name

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
                      <form action="publiline.py" method="get">
                          <input type="hidden" name="doctype" value="%(doctype)s" />
                          <input type="hidden" name="categ" value="" />
                          <input type="hidden" name="ln" value="%(ln)s" />
                          </form>
               <table>
                 <tr>
                 <td align="left">""" % {
                 'title' : title,
                 'doctype' : doctype,
                 'list_categ' : _("List of refereed categories"),
                 'choose_categ' : _("Please choose a category"),
                 'ln' : ln,
               }

        for categ in categories:
            num = categ['waiting'] + categ['approved'] + categ['rejected']

            if categ['waiting'] != 0:
                classtext = "class=\"blocknote\""
            else:
                classtext = ""

            out += """<a href="" onclick="document.forms[0].categ.value='%(id)s';document.forms[0].submit();return false;"><span %(classtext)s>%(id)s</span></a> (%(num)s document(s)""" % {
                     'id' : categ['id'],
                     'classtext' : classtext,
                     'num' : num,
                   }
            if categ['waiting'] != 0:
                out += """| %(waiting)s <img alt="%(pending)s" src="%(images)s/waiting_or.gif" border="0" />""" % {
                          'waiting' : categ['waiting'],
                          'pending' : _("Pending"),
                          'images' : CFG_SITE_URL + '/img',
                        }
            if categ['approved'] != 0:
                out += """| %(approved)s<img alt="%(approved_text)s" src="%(images)s/smchk_gr.gif" border="0" />""" % {
                          'approved' : categ['approved'],
                          'approved_text' : _("Approved"),
                          'images' : CFG_SITE_URL + '/img',
                        }
            if categ['rejected'] != 0:
                out += """| %(rejected)s<img alt="%(rejected_text)s" src="%(images)s/cross_red.gif" border="0" />""" % {
                          'rejected' : categ['rejected'],
                          'rejected_text' : _("Rejected"),
                          'images' : CFG_SITE_URL + '/img',
                        }
            out += ")<br />"

        out += """
                    </td>
                    <td>
                     <table class="searchbox" width="100%%" summary="">
                        <tr>
                            <th class="portalboxheader">%(key)s:</th>
                        </tr>
                        <tr>
                            <td>
                              <img alt="%(pending)s" src="%(images)s/waiting_or.gif" border="0" /> %(waiting)s<br />
                              <img alt="%(approved)s" src="%(images)s/smchk_gr.gif" border="0" /> %(already_approved)s<br />
                              <img alt="%(rejected)s" src="%(images)s/cross_red.gif" border="0" /> %(rejected_text)s<br /><br />
                              <small class="blocknote">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</small> %(somepending)s<br />
                            </td>
                        </tr>
                    </table>
                  </td>
                </tr>
                </table>
              </blockquote>
              </td>
             </tr>
            </table>""" % {
              'key' : _("Key"),
              'pending' : _("Pending"),
              'images' : CFG_SITE_URL + '/img',
              'waiting' : _("Waiting for approval"),
              'approved' : _("Approved"),
              'already_approved' : _("Already approved"),
              'rejected' : _("Rejected"),
              'rejected_text' : _("Rejected"),
              'somepending' : _("Some documents are pending."),
            }
        return out

    def tmpl_publiline_selectcplxcateg(self, ln, doctype, title, types):
        """
        Displays the categories from a doctype that the user can select

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'doctype' *string* - The doctype

          - 'title' *string* - The doctype name

          - 'categories' *array* - All the categories that the user can select:

              - 'id' *string* - The id of the category

              - 'waiting' *int* - The number of documents waiting

              - 'approved' *int* - The number of approved documents

              - 'rejected' *int* - The number of rejected documents
        """

        # load the right message language
        _ = gettext_set_language(ln)

        out = ""
        #out = """
        #       <table class="searchbox" width="100%%" summary="">
        #          <tr>
        #            <th class="portalboxheader">%(title)s: %(list_type)s</th>
        #          </tr>
        #       </table><br />
        #       <table class="searchbox" width="100%%" summary="">
        #          <tr>""" % {
        #          'title' : title,
        #          'list_type' : _("List of specific approvals"),
        #      }

        columns = []
        columns.append ({'apptype' : 'RRP',
                         'list_categ' : _("List of refereing categories"),
                         'id_form' : 0,
                       })
        #columns.append ({'apptype' : 'RPB',
        #                 'list_categ' : _("List of publication categories"),
        #                 'id_form' : 1,
        #               })
        #columns.append ({'apptype' : 'RDA',
        #                 'list_categ' : _("List of direct approval categories"),
        #                 'id_form' : 2,
        #               })

        for column in columns:
            out += """
                      <td>
                           <table class="searchbox" width="100%%" summary="">
                              <tr>
                                <th class="portalboxheader">%(list_categ)s</th>
                              </tr>
                              <tr>
                                  <td class="portalboxbody">
                                  %(choose_categ)s
                                  <blockquote>
                                  <form action="publiline.py" method="get">
                                      <input type="hidden" name="flow" value="cplx" />
                                      <input type="hidden" name="doctype" value="%(doctype)s" />
                                      <input type="hidden" name="categ" value="" />
                                      <input type="hidden" name="apptype" value="%(apptype)s" />
                                      <input type="hidden" name="ln" value="%(ln)s" />
                                      </form>
                           <table>
                             <tr>
                             <td align="left">""" % {
                             'doctype' : doctype,
                             'apptype' : column['apptype'],
                             'list_categ' : column['list_categ'],
                             'choose_categ' : _("Please choose a category"),
                             'ln' : ln,
                   }

            for categ in types[column['apptype']]:
                num = categ['waiting'] + categ['approved'] + categ['rejected'] + categ['cancelled']

                if categ['waiting'] != 0:
                    classtext = "class=\"blocknote\""
                else:
                    classtext = ""

                out += """<table><tr><td width="200px">*&nbsp<a href="" onclick="document.forms[%(id_form)s].categ.value='%(id)s';document.forms[%(id_form)s].submit();return false;"><small %(classtext)s>%(desc)s</small></td><td width="150px"></a><small> Total document(s) : %(num)s """ % {
                         'id' : categ['id'],
                         'id_form' : column['id_form'],
                         'classtext' : classtext,
                         'num' : num,
                         'desc' : categ['desc'],
                       }
                out += """<td width="100px">"""
                #if categ['waiting'] != 0:
                out += """ %(waiting)s &nbsp&nbsp<img alt="%(pending)s" src="%(images)s/waiting_or.gif" border="0" /></td>""" % {
                              'waiting' : categ['waiting'],
                              'pending' : _("Pending"),
                              'images' : CFG_SITE_URL + '/img',
                            }
                out += """<td width="100px">"""
                #if categ['approved'] != 0:
                out += """ %(approved)s &nbsp&nbsp<img alt="%(approved_text)s" src="%(images)s/smchk_gr.gif" border="0" /></td>""" % {
                              'approved' : categ['approved'],
                              'approved_text' : _("Approved"),
                              'images' : CFG_SITE_URL + '/img',
                            }
                out += """<td width="100px">"""
                #if categ['rejected'] != 0:
                out += """ %(rejected)s&nbsp&nbsp<img alt="%(rejected_text)s" src="%(images)s/cross_red.gif" border="0" /></td>""" % {
                              'rejected' : categ['rejected'],
                              'rejected_text' : _("Rejected"),
                              'images' : CFG_SITE_URL + '/img',
                            }
                out += """<td width="100px">"""
                #if categ['cancelled'] != 0:
                out += """ %(cancelled)s&nbsp&nbsp<img alt="%(cancelled_text)s" src="%(images)s/smchk_rd.gif" border="0" /></td>""" % {
                              'cancelled' : categ['cancelled'],
                              'cancelled_text' : _("Cancelled"),
                              'images' : CFG_SITE_URL + '/img',
                            }
                out += "</small></td></tr>"

            out += """
                                </table>
                                </td>
                            </tr>
                            </table>
                          </blockquote>
                          </td>
                         </tr>
                        </table>
                      </td>"""

        # Key
        out += """
               <table class="searchbox" width="100%%" summary="">
                        <tr>
                            <th class="portalboxheader">%(key)s:</th>
                        </tr>
                        <tr>
                            <td>
                              <img alt="%(pending)s" src="%(images)s/waiting_or.gif" border="0" /> %(waiting)s<br />
                              <img alt="%(approved)s" src="%(images)s/smchk_gr.gif" border="0" /> %(already_approved)s<br />
                              <img alt="%(rejected)s" src="%(images)s/cross_red.gif" border="0" /> %(rejected_text)s<br />
                              <img alt="%(cancelled)s" src="%(images)s/smchk_rd.gif" border="0" /> %(cancelled_text)s<br /><br />
                              <small class="blocknote">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</small> %(somepending)s<br />
                            </td>
                        </tr>
                </table>
              </blockquote>
              </td>
             </tr>
            </table>""" % {
              'key' : _("Key"),
              'pending' : _("Pending"),
              'images' : CFG_SITE_URL + '/img',
              'waiting' : _("Waiting for approval"),
              'approved' : _("Approved"),
              'already_approved' : _("Already approved"),
              'rejected' : _("Rejected"),
              'rejected_text' : _("Rejected"),
              'cancelled' : _("Cancelled"),
              'cancelled_text' : _("Cancelled"),
              'somepending' : _("Some documents are pending."),
            }
        return out

    def tmpl_publiline_selectdocument(self, ln, doctype, title, categ, docs):
        """
        Displays the documents that the user can select in the specified category

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'doctype' *string* - The doctype

          - 'title' *string* - The doctype name

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
                      <form action="publiline.py" method="get">
                        <input type="hidden" name="doctype" value="%(doctype)s" />
                        <input type="hidden" name="categ" value="%(categ)s" />
                        <input type="hidden" name="RN" value="" />
                        <input type="hidden" name="ln" value="%(ln)s">
                        </form>
                  <table class="searchbox">
                    <tr>
                      <th class="portalboxheader">%(report_no)s</th>
                      <th class="portalboxheader">%(pending)s</th>
                      <th class="portalboxheader">%(approved)s</th>
                      <th class="portalboxheader">%(rejected)s</th>
                    </tr>
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
                'ln': ln,
              }

        for doc in docs:
            status = doc ['status']

            if status == "waiting":
                out += """<tr>
                            <td align="center">
                              <a href="" onclick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</a>
                            </td>
                            <td align="center">
                              <img alt="check" src="%(images)s/waiting_or.gif" />
                            </td>
                            <td align="center">&nbsp;</td>
                            <td align="center">&nbsp;</td>
                          </tr>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : CFG_SITE_URL + '/img',
                       }
            elif status == "rejected":
                out += """<tr>
                            <td align="center">
                              <a href="" onclick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</a>
                            </td>
                            <td align="center">&nbsp;</td>
                            <td align="center">&nbsp;</td>
                            <td align="center"><img alt="check" src="%(images)s/cross_red.gif" /></td>
                          </tr>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : CFG_SITE_URL + '/img',
                       }
            elif status == "approved":
                out += """<tr>
                            <td align="center">
                              <a href="" onclick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</a>
                            </td>
                            <td align="center">&nbsp;</td>
                            <td align="center"><img alt="check" src="%(images)s/smchk_gr.gif" /></td>
                            <td align="center">&nbsp;</td>
                          </tr>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : CFG_SITE_URL + '/img',
                       }
        out += """  </table>
                    </blockquote>
                   </td>
                  </tr>
                 </table>"""
        return out

    def tmpl_publiline_selectcplxdocument(self, ln, doctype, title, categ, categname, docs, apptype):
        """
        Displays the documents that the user can select in the specified category

        Parameters:

          - 'ln' *string* - The language to display the interface in

          - 'doctype' *string* - The doctype

          - 'title' *string* - The doctype name

          - 'categ' *string* - the category

          - 'docs' *array* - All the categories that the user can select:

              - 'RN' *string* - The id of the document

              - 'status' *string* - The status of the document

          - 'apptype' *string* - the approval type
        """

        # load the right message language
        _ = gettext_set_language(ln)

        listtype = ""
        if apptype == "RRP":
            listtype = _("List of refereed documents")
        elif apptype == "RPB":
            listtype = _("List of publication documents")
        elif apptype == "RDA":
            listtype = _("List of direct approval documents")

        out = """
               <table class="searchbox" width="100%%" summary="">
                  <tr>
                    <th class="portalboxheader">%(title)s - %(categname)s: %(list)s</th>
                  </tr>
                  <tr>
                    <td class="portalboxbody">
                    %(choose_report)s
                    <blockquote>
                      <form action="publiline.py" method="get">
                        <input type="hidden" name="flow" value="cplx" />
                        <input type="hidden" name="doctype" value="%(doctype)s" />
                        <input type="hidden" name="categ" value="%(categ)s" />
                        <input type="hidden" name="RN" value="" />
                        <input type="hidden" name="apptype" value="%(apptype)s" />
                        <input type="hidden" name="ln" value="%(ln)s" />
                        </form>
                  <table class="searchbox">
                    <tr>
                      <th class="portalboxheader">%(report_no)s</th>
                      <th class="portalboxheader">%(pending)s</th>
                      <th class="portalboxheader">%(approved)s</th>
                      <th class="portalboxheader">%(rejected)s</th>
                      <th class="portalboxheader">%(cancelled)s</th>
                    </tr>
              """ % {
                'doctype' : doctype,
                'title' : title,
                'categname' : categname,
                'categ' : categ,
                'list' : listtype,
                'choose_report' : _("Click on a report number for more information."),
                'apptype' : apptype,
                'report_no' : _("Report Number"),
                'pending' : _("Pending"),
                'approved' : _("Approved"),
                'rejected' : _("Rejected"),
                'cancelled' : _("Cancelled"),
                'ln': ln,
              }

        for doc in docs:
            status = doc ['status']

            if status == "waiting":
                out += """<tr>
                            <td align="center">
                              <a href="" onclick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</a>
                            </td>
                            <td align="center"><img alt="check" src="%(images)s/waiting_or.gif" /></td>
                            <td align="center">&nbsp;</td>
                            <td align="center">&nbsp;</td>
                            <td align="center">&nbsp;</td>
                          </tr>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : CFG_SITE_URL + '/img',
                       }
            elif status == "rejected":
                out += """<tr>
                            <td align="center">
                              <a href="" onclick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</a>
                            </td>
                            <td align="center">&nbsp;</td>
                            <td align="center">&nbsp;</td>
                            <td align="center"><img alt="check" src="%(images)s/cross_red.gif" /></td>
                            <td align="center">&nbsp;</td>
                          </tr>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : CFG_SITE_URL + '/img',
                       }
            elif status == "approved":
                out += """<tr>
                            <td align="center">
                              <a href="" onclick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</a>
                            </td>
                            <td align="center">&nbsp;</td>
                            <td align="center"><img alt="check" src="%(images)s/smchk_gr.gif" /></td>
                            <td align="center">&nbsp;</td>
                            <td align="center">&nbsp;</td>
                          </tr>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : CFG_SITE_URL + '/img',
                       }
            elif status == "cancelled":
                out += """<tr>
                            <td align="center">
                              <a href="" onclick="document.forms[0].RN.value='%(rn)s';document.forms[0].submit();return false;">%(rn)s</a>
                            </td>
                            <td align="center">&nbsp;</td>
                            <td align="center">&nbsp;</td>
                            <td align="center">&nbsp;</td>
                            <td align="center"><img alt="check" src="%(images)s/smchk_rd.gif" /></td>
                          </tr>
                       """ % {
                         'rn' : doc['RN'],
                         'images' : CFG_SITE_URL + '/img',
                       }
        out += """  </table>
                    </blockquote>
                   </td>
                  </tr>
                 </table>"""
        return out

    def tmpl_publiline_displaydoc(self, ln, doctype, docname, categ, rn, status, dFirstReq, dLastReq, dAction, access, confirm_send, auth_code, auth_message, authors, title, sysno, newrn, note):
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

          - 'confirm_send' *bool* - must display a confirmation message about sending approval email

          - 'auth_code' *bool* - authorised to referee this document

          - 'auth_message' *string* - ???

          - 'authors' *string* - the authors of the submission

          - 'title' *string* - the title of the submission

          - 'sysno' *string* - the unique database id for the record

          - 'newrn' *string* - the record number assigned to the submission

          - 'note' *string* - Note about the approval request.
        """

        # load the right message language
        _ = gettext_set_language(ln)

        if status == "waiting":
            image = """<img src="%s/waiting_or.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        elif status == "approved":
            image = """<img src="%s/smchk_gr.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        elif status == "rejected":
            image = """<img src="%s/iconcross.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
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
            out += """<i><strong class="headline">%(requestsent)s</strong></i><br /><br />""" % {
                     'requestsent' : _("Your request has been sent to the referee."),
                   }

        out += """<form action="publiline.py">
                    <input type="hidden" name="RN" value="%(rn)s" />
                    <input type="hidden" name="categ" value="%(categ)s" />
                    <input type="hidden" name="doctype" value="%(doctype)s" />
                    <input type="hidden" name="ln" value="%(ln)s" />
                  <small>""" % {
                 'rn' : rn,
                 'categ' : categ,
                 'doctype' : doctype,
                 'ln' : ln,
               }
        if title != "unknown":
            out += """<strong class="headline">%(title_text)s</strong>%(title)s<br /><br />""" % {
                     'title_text' : _("Title:"),
                     'title' : title,
                   }

        if authors != "":
            out += """<strong class="headline">%(author_text)s</strong>%(authors)s<br /><br />""" % {
                     'author_text' : _("Author:"),
                     'authors' : authors,
                   }
        if sysno != "":
            out += """<strong class="headline">%(more)s</strong>
                        <a href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(sysno)s?ln=%(ln)s">%(click)s</a>
                        <br /><br />
                   """ % {
                     'more' : _("More information:"),
                     'click' : _("Click here"),
                     'siteurl' : CFG_SITE_URL,
                     'CFG_SITE_RECORD': CFG_SITE_RECORD,
                     'sysno' : sysno,
                     'ln' : ln,
                   }

        if note and auth_code == 0:
            out += """<table><tr><td valign="top"><strong class="headline">%(note_text)s</strong></td><td><em>%(note)s</em></td></tr></table>""" % {
                     'note_text' : _("Approval note:"),
                     'note' : cgi.escape(note).replace('\n', '<br />'),
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
                   """<input class="adminbutton" type="submit" name="send" value="%(send)s" onclick="return confirm('%(warning)s')" />""" % {
                     'send' : _("Send Again"),
                     'warning' : _("WARNING! Upon confirmation, an email will be sent to the referee.")
                   }
            if auth_code == 0:
                out += "<br />" + _("As a referee for this document, you may approve or reject it from the submission interface") + ":<br />" +\
                       """<input class="adminbutton" type="submit" name="approval" value="%(approve)s" onclick="window.location='%(siteurl)s/submit?doctype=%(doctype)s&amp;ln=%(ln)s';return false;" />""" % {
                         'approve' : _("Approve/Reject"),
                         'siteurl' : CFG_SITE_URL,
                         'doctype' : doctype,
                         'ln'      : ln
                       }
        if status == "approved":
            out += _("This document has been %(x_fmt_open)sapproved%(x_fmt_close)s.") % {'x_fmt_open': '<strong class="headline">', 'x_fmt_close': '</strong>'}
            out += '<br />' + _("Its approved reference is:") + ' <strong class="headline">' + str(newrn) + '</strong><br /><br />'
            out += _("It was first sent for approval on:") + ' <strong class="headline">' + str(dFirstReq) + '</strong><br />'
            if dLastReq == "0000-00-00 00:00:00":
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dFirstReq) + '</strong><br />'
            else:
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dLastReq) + '</strong><br />' +\
                       _("It was approved on:") + ' <strong class="headline">' + str(dAction) + '</strong><br />'
        if status == "rejected":
            out += _("This document has been %(x_fmt_open)srejected%(x_fmt_close)s.") % {'x_fmt_open': '<strong class="headline">', 'x_fmt_close': '</strong>'}
            out += "<br /><br />"
            out += _("It was first sent for approval on:") + ' <strong class="headline">' + str(dFirstReq) +'</strong><br />'
            if dLastReq == "0000-00-00 00:00:00":
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dFirstReq) + '</strong><br />'
            else:
                out += _("Last approval email was sent on:") + ' <strong class="headline">' + str(dLastReq) +'</strong><br />'
            out += _("It was rejected on:") + ' <strong class="headline">' + str(dAction) + '</strong><br />'

        out += """    </small></form>
                      <br />
                    </td>
                   </tr>
                  </table>"""
        return out

    def tmpl_publiline_displaycplxdoc(self, ln, doctype, docname, categ, rn, apptype, status, dates, isPubCom, isEdBoard, isReferee, isProjectLeader, isAuthor, authors, title, sysno, newrn):

        # load the right message language
        _ = gettext_set_language(ln)

        if status == "waiting":
            image = """<img src="%s/waiting_or.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        elif status == "approved":
            image = """<img src="%s/smchk_gr.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        elif status == "rejected":
            image = """<img src="%s/iconcross.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        elif status == "cancelled":
            image = """<img src="%s/smchk_rd.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
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

        out += """<form action="publiline.py">
                    <input type="hidden" name="flow" value="cplx" />
                    <input type="hidden" name="doctype" value="%(doctype)s" />
                    <input type="hidden" name="categ" value="%(categ)s" />
                    <input type="hidden" name="RN" value="%(rn)s" />
                    <input type="hidden" name="apptype" value="%(apptype)s" />
                    <input type="hidden" name="action" value="" />
                    <input type="hidden" name="ln" value="%(ln)s" />
                  """ % {
                 'rn' : rn,
                 'categ' : categ,
                 'doctype' : doctype,
                 'apptype' : apptype,
                 'ln': ln,
               }

        out += "<table><tr height='30px'><td width='120px'>"

        if title != "unknown":
            out += """<strong class="headline">%(title_text)s</strong></td><td>%(title)s</td></tr>""" % {
                     'title_text' : _("Title:"),
                     'title' : title,
                   }

        out += "<tr height='30px'><td width='120px'>"
        if authors != "":
            out += """<strong class="headline">%(author_text)s</strong></td><td>%(authors)s</td></tr>""" % {
                     'author_text' : _("Author:"),
                     'authors' : authors,
                   }
        out += "<tr height='30px'><td width='120px'>"
        if sysno != "":
            out += """<strong class="headline">%(more)s</strong>
                        </td><td><a href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(sysno)s?ln=%(ln)s">%(click)s</a>
                        </td></tr>
                   """ % {
                     'more' : _("More information:"),
                     'click' : _("Click here"),
                     'siteurl' : CFG_SITE_URL,
                     'CFG_SITE_RECORD': CFG_SITE_RECORD,
                     'sysno' : sysno,
                     'ln' : ln,
                   }

        out += "</table>"
        out += "<br /><br />"

        if apptype == "RRP":
            out += "<table><tr><td width='400px'>"
            out += _("It has first been asked for refereing process on the ") + "</td><td>" + ' <strong class="headline">' + str(dates['dFirstReq']) + '</strong><br /></td></tr>'

            out += "<tr><td width='400px'>"
            out += _("Last request e-mail was sent to the publication committee chair on the ") + "</td><td>" + ' <strong class="headline">' + str(dates['dLastReq']) + '</strong><br /></td></tr>'

            if dates['dRefereeSel'] != None:
                out += "<tr><td width='400px'>"
                out += _("A referee has been selected by the publication committee on the ") + "</td><td>" +  ' <strong class="headline">' + str(dates['dRefereeSel']) + '</strong><br /></td></tr>'
            else:
                out += "<tr><td width='400px'>"
                out += _("No referee has been selected yet.") + "</td><td>"
                if (status != "cancelled") and (isPubCom == 0):
                    out += displaycplxdoc_displayauthaction (action="RefereeSel", linkText=_("Select a referee"))
                out += '<br /></td></tr>'

            if dates['dRefereeRecom'] != None:
                out += "<tr><td width='400px'>"
                out += _("The referee has sent his final recommendations to the publication committee on the ") + "</td><td>" +  ' <strong class="headline">' + str(dates['dRefereeRecom']) + '</strong><br /></td></tr>'
            else:
                out += "<tr><td width='400px'>"
                out += _("No recommendation from the referee yet.") + "</td><td>"
                if (status != "cancelled") and (dates['dRefereeSel'] != None) and (isReferee == 0):
                    out += displaycplxdoc_displayauthaction (action="RefereeRecom", linkText=_("Send a recommendation"))
                out += '<br /></td></tr>'

            if dates['dPubComRecom'] != None:
                out += "<tr><td width='400px'>"
                out += _("The publication committee has sent his final recommendations to the project leader on the ") + "</td><td>" +  ' <strong class="headline">' + str(dates['dPubComRecom']) + '</strong><br /></td></tr>'
            else:
                out += "<tr><td width='400px'>"
                out += _("No recommendation from the publication committee yet.") + "</td><td>"
                if (status != "cancelled") and (dates['dRefereeRecom'] != None) and (isPubCom == 0):
                    out += displaycplxdoc_displayauthaction (action="PubComRecom", linkText=_("Send a recommendation"))
                out += '<br /></td></tr>'

            if status == "cancelled":
                out += "<tr><td width='400px'>"
                out += _("It has been cancelled by the author on the ") + "</td><td>" +  ' <strong class="headline">' + str(dates['dProjectLeaderAction']) + '</strong><br /></td></tr>'
            elif dates['dProjectLeaderAction'] != None:
                if status == "approved":
                    out += "<tr><td width='400px'>"
                    out += _("It has been approved by the project leader on the ") + "</td><td>" +  ' <strong class="headline">' + str(dates['dProjectLeaderAction']) + '</strong><br /></td></tr>'
                elif status == "rejected":
                    out += "<tr><td width='400px'>"
                    out += _("It has been rejected by the project leader on the ") + "</td><td>" +  ' <strong class="headline">' + str(dates['dProjectLeaderAction']) + '</strong><br /></td></tr>'
            else:
                out += "<tr><td width='400px'>"
                out += _("No final decision taken yet.") + "</td><td>"
                if (dates['dPubComRecom'] != None) and (isProjectLeader == 0):
                    out += displaycplxdoc_displayauthaction (action="ProjectLeaderDecision", linkText=_("Take a decision"))
                if isAuthor == 0:
                    out += displaycplxdoc_displayauthaction (action="AuthorCancel", linkText=_("Cancel"))
                out += '<br /></table>'

        elif apptype == "RPB":
            out += _("It has first been asked for refereing process on the ") + ' <strong class="headline">' + str(dates['dFirstReq']) + '</strong><br />'

            out += _("Last request e-mail was sent to the publication committee chair on the ") + ' <strong class="headline">' + str(dates['dLastReq']) + '</strong><br />'

            if dates['dEdBoardSel'] != None:
                out += _("An editorial board has been selected by the publication committee on the ") + ' <strong class="headline">' + str(dates['dEdBoardSel']) + '</strong>'
                if (status != "cancelled") and (isEdBoard == 0):
                    out += displaycplxdoc_displayauthaction (action="AddAuthorList", linkText=_("Add an author list"))
                out += '<br />'
            else:
                out += _("No editorial board has been selected yet.")
                if (status != "cancelled") and (isPubCom == 0):
                    out += displaycplxdoc_displayauthaction (action="EdBoardSel", linkText=_("Select an editorial board"))
                out += '<br />'

            if dates['dRefereeSel'] != None:
                out += _("A referee has been selected by the editorial board on the ") + ' <strong class="headline">' + str(dates['dRefereeSel']) + '</strong><br />'
            else:
                out += _("No referee has been selected yet.")
                if (status != "cancelled") and (dates['dEdBoardSel'] != None) and (isEdBoard == 0):
                    out += displaycplxdoc_displayauthaction (action="RefereeSel", linkText=_("Select a referee"))
                out += '<br />'

            if dates['dRefereeRecom'] != None:
                out += _("The referee has sent his final recommendations to the editorial board on the ") + ' <strong class="headline">' + str(dates['dRefereeRecom']) + '</strong><br />'
            else:
                out += _("No recommendation from the referee yet.")
                if (status != "cancelled") and (dates['dRefereeSel'] != None) and (isReferee == 0):
                    out += displaycplxdoc_displayauthaction (action="RefereeRecom", linkText=_("Send a recommendation"))
                out += '<br />'

            if dates['dEdBoardRecom'] != None:
                out += _("The editorial board has sent his final recommendations to the publication committee on the ") + ' <strong class="headline">' + str(dates['dRefereeRecom']) + '</strong><br />'
            else:
                out += _("No recommendation from the editorial board yet.")
                if (status != "cancelled") and (dates['dRefereeRecom'] != None) and (isEdBoard == 0):
                    out += displaycplxdoc_displayauthaction (action="EdBoardRecom", linkText=_("Send a recommendation"))
                out += '<br />'

            if dates['dPubComRecom'] != None:
                out += _("The publication committee has sent his final recommendations to the project leader on the ") + ' <strong class="headline">' + str(dates['dPubComRecom']) + '</strong><br />'
            else:
                out += _("No recommendation from the publication committee yet.")
                if (status != "cancelled") and (dates['dEdBoardRecom'] != None) and (isPubCom == 0):
                    out += displaycplxdoc_displayauthaction (action="PubComRecom", linkText=_("Send a recommendation"))
                out += '<br />'

            if status == "cancelled":
                out += _("It has been cancelled by the author on the ") + ' <strong class="headline">' + str(dates['dProjectLeaderAction']) + '</strong><br />'
            elif dates['dProjectLeaderAction'] != None:
                if status == "approved":
                    out += _("It has been approved by the project leader on the ") + ' <strong class="headline">' + str(dates['dProjectLeaderAction']) + '</strong><br />'
                elif status == "rejected":
                    out += _("It has been rejected by the project leader on the ") + ' <strong class="headline">' + str(dates['dProjectLeaderAction']) + '</strong><br />'
            else:
                out += _("No final decision taken yet.")
                if (dates['dPubComRecom'] != None) and (isProjectLeader == 0):
                    out += displaycplxdoc_displayauthaction (action="ProjectLeaderDecision", linkText=_("Take a decision"))
                if isAuthor == 0:
                    out += displaycplxdoc_displayauthaction (action="AuthorCancel", linkText=_("Cancel"))
                out += '<br />'

        elif apptype == "RDA":
            out += _("It has first been asked for refereing process on the ") + ' <strong class="headline">' + str(dates['dFirstReq']) + '</strong><br />'

            out += _("Last request e-mail was sent to the project leader on the ") + ' <strong class="headline">' + str(dates['dLastReq']) + '</strong><br />'

            if status == "cancelled":
                out += _("It has been cancelled by the author on the ") + ' <strong class="headline">' + str(dates['dProjectLeaderAction']) + '</strong><br />'
            elif dates['dProjectLeaderAction'] != None:
                if status == "approved":
                    out += _("It has been approved by the project leader on the ") + ' <strong class="headline">' + str(dates['dProjectLeaderAction']) + '</strong><br />'
                elif status == "rejected":
                    out += _("It has been rejected by the project leader on the ") + ' <strong class="headline">' + str(dates['dProjectLeaderAction']) + '</strong><br />'
            else:
                out += _("No final decision taken yet.")
                if isProjectLeader == 0:
                    out += displaycplxdoc_displayauthaction (action="ProjectLeaderDecision", linkText=_("Take a decision"))
                if isAuthor == 0:
                    out += displaycplxdoc_displayauthaction (action="AuthorCancel", linkText=_("Cancel"))
                out += '<br />'

        out += """    </form>
                      <br />
                    </td>
                   </tr>
                  </table>"""
        return out

    def tmpl_publiline_displaycplxdocitem(self,
                                          doctype, categ, rn, apptype, action,
                                          comments,
                                          (user_can_view_comments, user_can_add_comment, user_can_delete_comment),
                                          selected_category,
                                          selected_topic, selected_group_id, comment_subject, comment_body, ln):
        _ = gettext_set_language(ln)

        if comments and user_can_view_comments:

            comments_text = ''
            comments_overview = '<ul>'
            for comment in comments:
                (cmt_uid, cmt_nickname, cmt_title, cmt_body, cmt_date, cmt_priority, cmtid) = comment

                comments_overview += '<li><a href="#%s">%s - %s</a> (%s)</li>' % (cmtid, cmt_nickname, cmt_title, convert_datetext_to_dategui (cmt_date))

                comments_text += """
<table class="bskbasket">
  <thead class="bskbasketheader">
    <tr><td class="bsktitle"><a name="%s"></a>%s - %s (%s)</td><td><a href=%s/publiline.py?flow=cplx&doctype=%s&apptype=%s&categ=%s&RN=%s&reply=true&commentId=%s&ln=%s#add_comment>Reply</a></td><td><a href="#top">Top</a></td></tr>
  </thead>
  <tbody>
    <tr><td colspan="2">%s</td></tr>
  </tbody>
</table>""" % (cmtid, cmt_nickname, cmt_title, convert_datetext_to_dategui (cmt_date), CFG_SITE_URL, doctype, apptype, categ, rn, cmt_uid, ln, email_quoted_txt2html(cmt_body))

            comments_overview += '</ul>'
        else:
            comments_text = ''
            comments_overview = 'None.'

        body = ''
        if user_can_view_comments:
            body += """<h4>%(comments_label)s</h4>"""
        if user_can_view_comments:
            body += """%(comments)s"""
        if user_can_add_comment:
            validation = """
    <input type="hidden" name="validate" value="go" />
    <input type="submit" class="formbutton" value="%(button_label)s" />""" % {'button_label': _("Add Comment")}
            body += self.tmpl_publiline_displaywritecomment (doctype, categ, rn, apptype, action, _("Add Comment"), comment_subject, validation, comment_body, ln)

        body %= {
                'comments_label': _("Comments"),
                'action': action,
                'button_label': _("Write a comment"),
                'comments': comments_text}
        content = '<br />'

        out = """
<table class="bskbasket">
  <thead class="bskbasketheader">
    <tr>
      <td class="bsktitle">
        <a name="top"></a>
        <h4>%(comments_overview_label)s</h4>
        %(comments_overview)s
      </td>
      <td class="bskcmtcol"></td>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td colspan="2" style="padding: 5px;">
%(body)s
      </td>
    </tr>
  </tbody>
</table>""" % {
               'comments_overview_label' : _('Comments overview'),
               'comments_overview' : comments_overview,
               'body' : body,}

        return out

    def tmpl_publiline_displaywritecomment(self, doctype, categ, rn, apptype, action, write_label, title, validation, reply_message, ln):
        _ = gettext_set_language(ln)
        return """
<div style="width:100%%%%">
  <hr />
  <h2>%(write_label)s</h2>
  <form action="publiline.py">
    <input type="hidden" name="flow" value="cplx" />
    <input type="hidden" name="doctype" value="%(doctype)s" />
    <input type="hidden" name="categ" value="%(categ)s" />
    <input type="hidden" name="RN" value="%(rn)s" />
    <input type="hidden" name="apptype" value="%(apptype)s" />
    <input type="hidden" name="action" value="%(action)s" />
    <input type="hidden" name="ln" value="%(ln)s" />
    <p class="bsklabel">%(title_label)s:</p>
    <a name="add_comment"></a>
    <input type="text" name="msg_subject" size="80" value="%(title)s"/>
    <p class="bsklabel">%(comment_label)s:</p>
    <textarea name="msg_body" rows="20" cols="80">%(reply_message)s</textarea><br />
    %(validation)s
  </form>
</div>""" % {'write_label': write_label,
             'title_label': _("Title"),
             'title': title,
             'comment_label': _("Comment"),
             'rn' : rn,
             'categ' : categ,
             'doctype' : doctype,
             'apptype' : apptype,
             'action' : action,
             'validation' : validation,
             'reply_message' : reply_message,
             'ln' : ln,
            }

    def tmpl_publiline_displaydocplxaction(self, ln, doctype, categ, rn, apptype, action, status, authors, title, sysno, subtitle1, email_user_pattern, stopon1, users, extrausers, stopon2, subtitle2, usersremove, stopon3, validate_btn):

        # load the right message language
        _ = gettext_set_language(ln)

        if status == "waiting":
            image = """<img src="%s/waiting_or.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        elif status == "approved":
            image = """<img src="%s/smchk_gr.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        elif status == "rejected":
            image = """<img src="%s/iconcross.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        else:
            image = ""
        out = """
                <table class="searchbox" summary="">
                 <tr>
                  <th class="portalboxheader">%(image)s %(rn)s</th>
                 </tr>
                 <tr>
                   <td class="portalboxbody">
                     """ % {
                   'image' : image,
                   'rn' : rn,
                 }

        if title != "unknown":
            out += """<strong class="headline">%(title_text)s</strong>%(title)s<br /><br />""" % {
                     'title_text' : _("Title:"),
                     'title' : title,
                   }

        if authors != "":
            out += """<strong class="headline">%(author_text)s</strong>%(authors)s<br /><br />""" % {
                     'author_text' : _("Author:"),
                     'authors' : authors,
                   }
        if sysno != "":
            out += """<strong class="headline">%(more)s</strong>
                        <a href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(sysno)s?ln=%(ln)s">%(click)s</a>
                        <br /><br />
                   """ % {
                     'more' : _("More information:"),
                     'click' : _("Click here"),
                     'siteurl' : CFG_SITE_URL,
                     'CFG_SITE_RECORD': CFG_SITE_RECORD,
                     'sysno' : sysno,
                     'ln' : ln,
                   }

        out += """  <br />
                    </td>
                   </tr>
                 </table>"""

        if ((apptype == "RRP") or (apptype == "RPB")) and ((action == "EdBoardSel") or (action == "RefereeSel")):
            out += """
                    <table class="searchbox" summary="">
                     <tr>
                      <th class="portalboxheader">%(subtitle)s</th>
                     </tr>
                     <tr>
                       <td class="portalboxbody">""" % {
                       'subtitle' : subtitle1,
                     }

            out += """<form action="publiline.py">
                        <input type="hidden" name="flow" value="cplx" />
                        <input type="hidden" name="doctype" value="%(doctype)s" />
                        <input type="hidden" name="categ" value="%(categ)s" />
                        <input type="hidden" name="RN" value="%(rn)s" />
                        <input type="hidden" name="apptype" value="%(apptype)s" />
                        <input type="hidden" name="action" value="%(action)s" />
                        <input type="hidden" name="ln" value="%(ln)s" />""" % {
                     'rn' : rn,
                     'categ' : categ,
                     'doctype' : doctype,
                     'apptype' : apptype,
                     'action' : action,
                     'ln': ln,
                   }

            out += ' <span class="adminlabel">1. %s </span>\n' % _("search for user")
            out += ' <input class="admin_wvar" type="text" name="email_user_pattern" value="%s" />\n' % (email_user_pattern, )
            out += ' <input class="adminbutton" type="submit" value="%s"/>\n' % (_("search for users"), )

            if (stopon1 == "") and (email_user_pattern != ""):
                out += ' <br /><span class="adminlabel">2. %s </span>\n' % _("select user")
                out += ' <select name="id_user" class="admin_w200">\n'
                out += '  <option value="0">*** %s ***</option>\n' % _("select user")
                for elem in users:
                    elem_id = elem[0]
                    email = elem[1]
                    out += '  <option value="%s">%s</option>\n' % (elem_id, email)

                for elem in extrausers:
                    elem_id = elem[0]
                    email = elem[1]
                    out += '  <option value="%s">%s %s</option>\n' % (elem_id, email, _("connected"))

                out += ' </select>\n'
                out += ' <input class="adminbutton" type="submit" value="%s" />\n' % (_("add this user"), )

                out += stopon2

            elif stopon1 != "":
                out += stopon1

            out += """
                            </form>
                          <br />
                        </td>
                       </tr>
                     </table>"""

            if action == "EdBoardSel":
                out += """
                        <table class="searchbox" summary="">
                         <tr>
                          <th class="portalboxheader">%(subtitle)s</th>
                         </tr>
                         <tr>
                           <td class="portalboxbody">""" % {
                           'subtitle' : subtitle2,
                         }

                out += """<form action="publiline.py">
                            <input type="hidden" name="flow" value="cplx" />
                            <input type="hidden" name="doctype" value="%(doctype)s" />
                            <input type="hidden" name="categ" value="%(categ)s" />
                            <input type="hidden" name="RN" value="%(rn)s" />
                            <input type="hidden" name="apptype" value="%(apptype)s" />
                            <input type="hidden" name="action" value="%(action)s" />
                            <input type="hidden" name="ln" value="%(ln)s" />""" % {
                         'rn' : rn,
                         'categ' : categ,
                         'doctype' : doctype,
                         'apptype' : apptype,
                         'action' : action,
                         'ln': ln,
                       }

                out += ' <span class="adminlabel">1. %s </span>\n' % _("select user")
                out += ' <select name="id_user_remove" class="admin_w200">\n'
                out += '  <option value="0">*** %s ***</option>\n' % _("select user")
                for elem in usersremove:
                    elem_id = elem[0]
                    email = elem[1]
                    out += '  <option value="%s">%s</option>\n' % (elem_id, email)

                out += ' </select>\n'
                out += ' <input class="adminbutton" type="submit" value="%s" />\n' % (_("remove this user"), )

                out += stopon3

                out += """
                                </form>
                              <br />
                            </td>
                           </tr>
                         </table>"""

            if validate_btn != "":
                out += """<form action="publiline.py">
                            <input type="hidden" name="flow" value="cplx" />
                            <input type="hidden" name="doctype" value="%(doctype)s" />
                            <input type="hidden" name="categ" value="%(categ)s" />
                            <input type="hidden" name="RN" value="%(rn)s" />
                            <input type="hidden" name="apptype" value="%(apptype)s" />
                            <input type="hidden" name="action" value="%(action)s" />
                            <input type="hidden" name="validate" value="go" />
                            <input type="hidden" name="ln" value="%(ln)s" />
                            <input class="adminbutton" type="submit" value="%(validate_btn)s" />
                          </form>""" % {
                         'rn' : rn,
                         'categ' : categ,
                         'doctype' : doctype,
                         'apptype' : apptype,
                         'action' : action,
                         'validate_btn' : validate_btn,
                         'ln': ln,
                       }

        return out

    def tmpl_publiline_displaycplxrecom(self, ln, doctype, categ, rn, apptype, action, status, authors, title, sysno,  msg_to, msg_to_group, msg_subject):

        # load the right message language
        _ = gettext_set_language(ln)

        if status == "waiting":
            image = """<img src="%s/waiting_or.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        elif status == "approved":
            image = """<img src="%s/smchk_gr.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        elif status == "rejected":
            image = """<img src="%s/iconcross.gif" alt="" align="right" />""" % (CFG_SITE_URL + '/img')
        else:
            image = ""
        out = """
                <table class="searchbox" summary="">
                 <tr>
                  <th class="portalboxheader">%(image)s %(rn)s</th>
                 </tr>
                 <tr>
                   <td class="portalboxbody">
                    """ % {
                   'image' : image,
                   'rn' : rn,
                 }

        if title != "unknown":
            out += """<strong class="headline">%(title_text)s</strong>%(title)s<br /><br />""" % {
                     'title_text' : _("Title:"),
                     'title' : title,
                   }

        if authors != "":
            out += """<strong class="headline">%(author_text)s</strong>%(authors)s<br /><br />""" % {
                     'author_text' : _("Author:"),
                     'authors' : authors,
                   }
        if sysno != "":
            out += """<strong class="headline">%(more)s</strong>
                        <a href="%(siteurl)s/%(CFG_SITE_RECORD)s/%(sysno)s?ln=%(ln)s">%(click)s</a>
                        <br /><br />
                   """ % {
                     'more' : _("More information:"),
                     'click' : _("Click here"),
                     'siteurl' : CFG_SITE_URL,
                     'CFG_SITE_RECORD': CFG_SITE_RECORD,
                     'sysno' : sysno,
                     'ln' : ln,
                   }

        out += """    <br />
                    </td>
                   </tr>
                 </table>"""

        # escape forbidden character
        msg_to = escape_html(msg_to)
        msg_to_group = escape_html(msg_to_group)
        msg_subject = escape_html(msg_subject)

        write_box = """
<form action="publiline.py" method="post">
  <input type="hidden" name="flow" value="cplx" />
  <input type="hidden" name="doctype" value="%(doctype)s" />
  <input type="hidden" name="categ" value="%(categ)s" />
  <input type="hidden" name="RN" value="%(rn)s" />
  <input type="hidden" name="apptype" value="%(apptype)s" />
  <input type="hidden" name="action" value="%(action)s" />
  <input type="hidden" name="ln" value="%(ln)s" />
  <div style="float: left; vertical-align:text-top; margin-right: 10px;">
    <table class="mailbox">
      <thead class="mailboxheader">
        <tr>
          <td class="inboxheader" colspan="2">
            <table class="messageheader">
              <tr>
                <td class="mailboxlabel">%(to_label)s</td>"""

        if msg_to != "":
            addr_box = """
                <td class="mailboxlabel">%(users_label)s</td>
                <td style="width:100%%%%;" class="mailboxlabel">%(to_users)s</td>""" % {'users_label': _("User"),
                                                                                        'to_users' : msg_to,
                                                                                       }
            if msg_to_group != "":
                addr_box += """
              </tr>
              <tr>
                <td class="mailboxlabel">&nbsp;</td>
                <td class="mailboxlabel">%(groups_label)s</td>
                <td style="width:100%%%%;" class="mailboxlabel">%(to_groups)s</td>""" % {'groups_label': _("Group"),
                                                                                         'to_groups': msg_to_group,
                                                                                        }
        elif msg_to_group != "":
            addr_box = """
                <td class="mailboxlabel">%(groups_label)s</td>
                <td style="width:100%%%%;" class="mailboxlabel">%(to_groups)s</td>""" % {'groups_label': _("Group"),
                                                                                         'to_groups': msg_to_group,
                                                                                        }
        else:
            addr_box = """
                <td class="mailboxlabel">&nbsp;</td>
                <td class="mailboxlabel">&nbsp;</td>"""

        write_box += addr_box
        write_box += """
              </tr>
              <tr>
                <td class="mailboxlabel">&nbsp;</td>
                <td>&nbsp;</td>
                <td>&nbsp;</td>
              </tr>
              <tr>
                <td class="mailboxlabel">%(subject_label)s</td>
                <td colspan="2">
                  <input class="mailboxinput" type="text" name="msg_subject" value="%(subject)s" />
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </thead>
      <tfoot>
        <tr>
          <td style="height:0px" colspan="2"></td>
        </tr>
      </tfoot>
      <tbody class="mailboxbody">
        <tr>
          <td class="mailboxlabel">%(message_label)s</td>
          <td>
            <textarea name="msg_body" rows="10" cols="50"></textarea>
          </td>
        </tr>
        <tr class="mailboxfooter">
         <td>
             <select name="validate">
                 <option value="%(select)s"> %(select)s</option>
                 <option value="approve">%(approve)s</option>
                 <option value="reject">%(reject)s</option>
             </select>
          </td>

          <td colspan="2" class="mailboxfoot">
            <input type="submit" name="send_button" value="%(send_label)s" class="formbutton"/>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</form>
"""
        write_box = write_box % {'rn' : rn,
                                 'categ' : categ,
                                 'doctype' : doctype,
                                 'apptype' : apptype,
                                 'action' : action,
                                 'subject' : msg_subject,
                                 'to_label': _("To:"),
                                 'subject_label': _("Subject:"),
                                 'message_label': _("Message:"),
                                 'send_label': _("SEND"),
                                 'select' : _("Select:"),
                                 'approve' : _("approve"),
                                 'reject' : _("reject"),
                                 'ln': ln,
                                }

        out += write_box

        return out

    def tmpl_mathpreview_header(self, ln, https=False):
        """
        Metaheader to add to submit pages in order to preview equation
        rendered via MathJax.

        @param ln: language.
        @param https: True on https pages, False otherwise.
        """
        # By default, add tooltip to any suspected 'title' and
        # 'abstract' field, as well as those tagged with 'mathpreview'
        # class.

        # load the right message language
        _ = gettext_set_language(ln)

        return '''
         <script src="%(siteurl)s/js/jquery.mathpreview.js" type="text/javascript"></script>
         <script type="text/javascript">
         <!--
         $(document).ready(function() {
         $('textarea[name$="TITLE"], input[type="text"][name$="TITLE"],textarea[name$="ABSTRACT"], input[type="text"][name$="ABSTRACT"], textarea[name$="TTL"], input[type="text"][name$="TTL"], textarea[name$="ABS"], input[type="text"][name$="ABS"], textarea[name$="ABSTR"], input[type="text"][name$="ABSTR"], .mathpreview textarea, .mathpreview input[type="text"], input[type="text"].mathpreview, textarea.mathpreview').mathpreview(
         {'help-label': '%(help-label)s',
          'help-url'  : '%(siteurl)s/help/submit-guide#math-markup'});
         })
         -->
         </script>''' % {
         'siteurl': https and CFG_SITE_SECURE_URL or CFG_SITE_URL,
         'help-label': escape_javascript_string(_("Use '\\$' delimiters to write LaTeX markup. Eg: \\$e=mc^{2}\\$")),
         }

def displaycplxdoc_displayauthaction(action, linkText):
    return """ <strong class="headline">(<a href="" onclick="document.forms[0].action.value='%(action)s';document.forms[0].submit();return false;">%(linkText)s</a>)</strong>""" % {
        "action" : action,
        "linkText" : linkText
        }
