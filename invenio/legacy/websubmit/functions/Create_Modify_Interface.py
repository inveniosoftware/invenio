# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2014 CERN.
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
"""
This is the Create_Modify_Interface function (along with its helpers).
It is used by WebSubmit for the "Modify Bibliographic Information" action.
"""
__revision__ = "$Id$"

import os
import re
import time
import pprint
import cgi

from invenio.legacy.dbquery import run_sql
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError
from invenio.legacy.websubmit.functions.Retrieve_Data import Get_Field
from invenio.ext.logging import register_exception
from invenio.utils.html import escape_javascript_string
from invenio.base.i18n import gettext_set_language, wash_language

def Create_Modify_Interface_getfieldval_fromfile(cur_dir, fld=""):
    """Read a field's value from its corresponding text file in 'cur_dir' (if it exists) into memory.
       Delete the text file after having read-in its value.
       This function is called on the reload of the modify-record page. This way, the field in question
       can be populated with the value last entered by the user (before reload), instead of always being
       populated with the value still found in the DB.
    """
    fld_val = ""
    if len(fld) > 0 and os.access("%s/%s" % (cur_dir, fld), os.R_OK|os.W_OK):
        fp = open( "%s/%s" % (cur_dir, fld), "r" )
        fld_val = fp.read()
        fp.close()
        try:
            os.unlink("%s/%s"%(cur_dir, fld))
        except OSError:
            # Cannot unlink file - ignore, let WebSubmit main handle this
            pass
        fld_val = fld_val.strip()
    return fld_val
def Create_Modify_Interface_getfieldval_fromDBrec(fieldcode, recid):
    """Read a field's value from the record stored in the DB.
       This function is called when the Create_Modify_Interface function is called for the first time
       when modifying a given record, and field values must be retrieved from the database.
    """
    fld_val = ""
    if fieldcode != "":
        for next_field_code in [x.strip() for x in fieldcode.split(",")]:
            fld_val += "%s\n" % Get_Field(next_field_code, recid)
        fld_val = fld_val.rstrip('\n')
    return fld_val
def Create_Modify_Interface_transform_date(fld_val):
    """Accept a field's value as a string. If the value is a date in one of the following formats:
          DD Mon YYYY (e.g. 23 Apr 2005)
          YYYY-MM-DD  (e.g. 2005-04-23)
       ...transform this date value into "DD/MM/YYYY" (e.g. 23/04/2005).
    """
    if re.search("^[0-9]{2} [a-z]{3} [0-9]{4}$", fld_val, re.IGNORECASE) is not None:
        try:
            fld_val = time.strftime("%d/%m/%Y", time.strptime(fld_val, "%d %b %Y"))
        except (ValueError, TypeError):
            # bad date format:
            pass
    elif re.search("^[0-9]{4}-[0-9]{2}-[0-9]{2}$", fld_val, re.IGNORECASE) is not None:
        try:
            fld_val = time.strftime("%d/%m/%Y", time.strptime(fld_val, "%Y-%m-%d"))
        except (ValueError,TypeError):
            # bad date format:
            pass
    return fld_val


def Create_Modify_Interface(parameters, curdir, form, user_info=None):
    """
    Create an interface for the modification of a document, based on
    the fields that the user has chosen to modify. This avoids having
    to redefine a submission page for the modifications, but rely on
    the elements already defined for the initial submission i.e. SBI
    action (The only page that needs to be built for the modification
    is the page letting the user specify a document to modify).

    This function should be added at step 1 of your modification
    workflow, after the functions that retrieves report number and
    record id (Get_Report_Number, Get_Recid). Functions at step 2 are
    the one executed upon successful submission of the form.

    Create_Modify_Interface expects the following parameters:

       * "fieldnameMBI" - the name of a text file in the submission
        working directory that contains a list of the names of the
        WebSubmit fields to include in the Modification interface.
        These field names are separated by"\n" or "+".

       * "prefix" - some content displayed before the main
         modification interface. Can contain HTML (i.e. needs to be
         pre-escaped). The prefix can make use of Python string
         replacement for common values (such as 'rn'). Percent signs
         (%) must consequently be escaped (with %%).

       * "suffix" - some content displayed after the main modification
         interface. Can contain HTML (i.e. needs to be
         pre-escaped). The suffix can make use of Python string
         replacement for common values (such as 'rn'). Percent signs
         (%) must consequently be escaped (with %%).

       * "button_label" - the label for the "END" button.

       * "button_prefix" - some content displayed before the button to
         submit the form. Can contain HTML (i.e. needs to be
         pre-escaped). The prefix can make use of Python string
         replacement for common values (such as 'rn'). Percent signs
         (%) must consequently be escaped (with %%).

       * "dates_conversion" - by default, values interpreted as dates
         are converted to their 'DD/MM/YYYY' format, whenever
         possible. Set another value for a different behaviour
         (eg. 'none' for no conversion)

    Given the list of WebSubmit fields to be included in the
    modification interface, the values for each field are retrieved
    for the given record (by way of each WebSubmit field being
    configured with a MARC Code in the WebSubmit database).  An HTML
    FORM is then created. This form allows a user to modify certain
    field values for a record.

    The file referenced by 'fieldnameMBI' is usually generated from a
    multiple select form field): users can then select one or several
    fields to modify

    Note that the function will display WebSubmit Response elements,
    but will not be able to set an initial value: this must be done by
    the Response element iteself.

    Additionally the function creates an internal field named
    'Create_Modify_Interface_DONE' on the interface, that can be
    retrieved in curdir after the form has been submitted.
    This flag is an indicator for the function that displayed values
    should not be retrieved from the database, but from the submitted
    values (in case the page is reloaded). You can also rely on this
    value when building your WebSubmit Response element in order to
    retrieve value either from the record, or from the submission
    directory.
    """
    ln = wash_language(form['ln'])
    _ = gettext_set_language(ln)

    global sysno,rn
    t = ""
    # variables declaration
    fieldname = parameters['fieldnameMBI']
    prefix = ''
    suffix = ''
    end_button_label = 'END'
    end_button_prefix = ''
    date_conversion_setting = ''
    if parameters.has_key('prefix'):
        prefix = parameters['prefix']
    if parameters.has_key('suffix'):
        suffix = parameters['suffix']
    if parameters.has_key('button_label') and parameters['button_label']:
        end_button_label = parameters['button_label']
    if parameters.has_key('button_prefix'):
        end_button_prefix = parameters['button_prefix']
    if parameters.has_key('dates_conversion'):
        date_conversion_setting = parameters['dates_conversion']
    # Path of file containing fields to modify

    the_globals = {
        'doctype' : doctype,
        'action' : action,
        'act' : action, ## for backward compatibility
        'step' : step,
        'access' : access,
        'ln' : ln,
        'curdir' : curdir,
        'uid' : user_info['uid'],
        'uid_email' : user_info['email'],
        'rn' : rn,
        'last_step' : last_step,
        'action_score' : action_score,
        '__websubmit_in_jail__' : True,
        'form': form,
        'sysno': sysno,
        'user_info' : user_info,
        '__builtins__' : globals()['__builtins__'],
        'Request_Print': Request_Print
    }

    if os.path.exists("%s/%s" % (curdir, fieldname)):
        fp = open( "%s/%s" % (curdir, fieldname), "r" )
        fieldstext = fp.read()
        fp.close()
        fieldstext = re.sub("\+","\n", fieldstext)
        fields = fieldstext.split("\n")
    else:
        res = run_sql("SELECT fidesc FROM sbmFIELDDESC WHERE  name=%s", (fieldname,))
        if len(res) == 1:
            fields = res[0][0].replace(" ", "")
            fields = re.findall("<optionvalue=.*>", fields)
            regexp = re.compile("""<optionvalue=(?P<quote>['|"]?)(?P<value>.*?)(?P=quote)""")
            fields = [regexp.search(x) for x in fields]
            fields = [x.group("value") for x in fields if x is not None]
            fields = [x for x in fields if x not in ("Select", "select")]
        else:
            raise InvenioWebSubmitFunctionError("cannot find fields to modify")
    #output some text
    if not prefix:
        t += "<center bgcolor=\"white\">The document <b>%s</b> has been found in the database.</center><br />Please modify the following fields:<br />Then press the '%s' button at the bottom of the page<br />\n" % \
          (rn, cgi.escape(_(end_button_label)))
    else:
        t += prefix % the_globals
    for field in fields:
        subfield = ""
        value = ""
        marccode = ""
        text = ""
        # retrieve and display the modification text
        t = t + "<FONT color=\"darkblue\">\n"
        res = run_sql("SELECT modifytext FROM sbmFIELDDESC WHERE  name=%s", (field,))
        if len(res)>0:
            t = t + "<small>%s</small> </FONT>\n" % (res[0][0] is None and ' ' or res[0][0],)
        # retrieve the marc code associated with the field
        res = run_sql("SELECT marccode FROM sbmFIELDDESC WHERE name=%s", (field,))
        if len(res) > 0:
            marccode = res[0][0]
        # then retrieve the previous value of the field
        if os.path.exists("%s/%s" % (curdir, "Create_Modify_Interface_DONE")):
            # Page has been reloaded - get field value from text file on server, not from DB record
            value = Create_Modify_Interface_getfieldval_fromfile(curdir, field)
        else:
            # First call to page - get field value from DB record
            value = Create_Modify_Interface_getfieldval_fromDBrec(marccode, sysno)
        if date_conversion_setting != 'none':
            # If field is a date value, transform date into format DD/MM/YYYY:
            value = Create_Modify_Interface_transform_date(value)
        res = run_sql("SELECT * FROM sbmFIELDDESC WHERE name=%s", (field,))
        if len(res) > 0:
            element_type = res[0][3]
            numcols = res[0][6]
            numrows = res[0][5]
            size = res[0][4]
            maxlength = res[0][7]
            val = res[0][8]
            fidesc = res[0][9]
            if element_type == "T":
                text = "<textarea name=\"%s\" rows=%s cols=%s wrap>%s</textarea>" % (field, numrows, numcols, cgi.escape(value))
            elif element_type == "F":
                text = "<input type=\"file\" name=\"%s\" size=%s maxlength=\"%s\">" % (field, size, maxlength)
            elif element_type == "I":
                text = "<input name=\"%s\" size=%s value=\"%s\"> " % (field, size, val and escape_javascript_string(val, escape_quote_for_html=True) or '')
                text = text + '''<script type="text/javascript">/*<![CDATA[*/
                document.forms[0].%s.value="%s";
                /*]]>*/</script>''' % (field, escape_javascript_string(value, escape_for_html=False))
            elif element_type == "H":
                text = "<input type=\"hidden\" name=\"%s\" value=\"%s\">" % (field, val and escape_javascript_string(val, escape_quote_for_html=True) or '')
                text = text + '''<script type="text/javascript">/*<![CDATA[*/
                document.forms[0].%s.value="%s";
                /*]]>*/</script>''' % (field, escape_javascript_string(value, escape_for_html=False))
            elif element_type == "S":
                values = re.split("[\n\r]+", value)
                text = fidesc
                if re.search("%s\[\]" % field, fidesc):
                    multipletext = "[]"
                else:
                    multipletext = ""
                if len(values) > 0 and not(len(values) == 1 and values[0] == ""):
                    text += '<script type="text/javascript">/*<![CDATA[*/\n'
                    text += "var i = 0;\n"
                    text += "el = document.forms[0].elements['%s%s'];\n" % (field, multipletext)
                    text += "max = el.length;\n"
                    for val in values:
                        text += "var found = 0;\n"
                        text += "var i=0;\n"
                        text += "while (i != max) {\n"
                        text += "  if (el.options[i].value == \"%s\" || el.options[i].text == \"%s\") {\n" % \
                          (escape_javascript_string(val, escape_for_html=False), escape_javascript_string(val, escape_for_html=False))
                        text += "    el.options[i].selected = true;\n"
                        text += "    found = 1;\n"
                        text += "  }\n"
                        text += "  i=i+1;\n"
                        text += "}\n"
                        #text += "if (found == 0) {\n"
                        #text += "  el[el.length] = new Option(\"%s\", \"%s\", 1,1);\n"
                        #text += "}\n"
                    text += "/*]]>*/</script>\n"
            elif element_type == "D":
                text = fidesc
            elif element_type == "R":
                try:
                    co = compile(fidesc.replace("\r\n", "\n"), "<string>", "exec")
                    ## Note this exec is safe WRT global variable because the
                    ## Create_Modify_Interface has already been parsed by
                    ## execfile within a protected environment.
                    the_globals['text'] = ''
                    exec co in the_globals
                    text = the_globals['text']
                except:
                    msg = "Error in evaluating response element %s with globals %s" % (pprint.pformat(field), pprint.pformat(globals()))
                    register_exception(req=None, alert_admin=True, prefix=msg)
                    raise InvenioWebSubmitFunctionError(msg)
            else:
                text = "%s: unknown field type" % field
            t = t + "<small>%s</small>" % text

    # output our flag field
    t += '<input type="hidden" name="Create_Modify_Interface_DONE" value="DONE\n" />'


    t += '<br />'

    if end_button_prefix:
        t += end_button_prefix % the_globals

    # output some more text
    t += "<br /><CENTER><small><INPUT type=\"button\" width=400 height=50 name=\"End\" value=\"%(end_button_label)s\" onClick=\"document.forms[0].step.value = 2;user_must_confirm_before_leaving_page = false;document.forms[0].submit();\"></small></CENTER></H4>" % {'end_button_label': escape_javascript_string(_(end_button_label), escape_quote_for_html=True)}

    if suffix:
        t += suffix % the_globals

    return t

