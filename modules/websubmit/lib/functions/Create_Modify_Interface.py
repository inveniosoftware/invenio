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

   ## Description:   function Create_Modify_Interface
   ##                This function creates the html form allowing the user to
   ##                some bibliographic fields
   ## Author:         T.Baron
   ## PARAMETERS:    fieldnameMBI: name of the file containing the 
   ##                              "+"-separated list of fields to modify

execfile("%s/invenio/websubmit_functions/Retrieve_Data.py" % pylibdir)
import re,os

def Create_Modify_Interface_getfieldval_fromfile(cur_dir, fld=""):
    """Read a field's value from its corresponding text file in 'cur_dir' (if it exists) into memory.
       Delete the text file after having read-in its value.
       This function is called on the reload of the modify-record page. This way, the field in question
       can be populated with the value last entered by the user (before reload), instead of always being
       populated with the value still found in the DB.
    """
    fld_val = ""
    if len(fld) > 0 and os.access("%s/%s" % (cur_dir,fld), os.R_OK|os.W_OK):
        fp = open( "%s/%s" % (cur_dir,fld), "r" )
        fld_val = fp.read()
        fp.close()
        try:
            os.unlink("%s/%s"%(cur_dir,fld))
        except OSError:
            # Cannot unlink file - ignore, let websubmit main deal with this
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
        fld_val = Get_Field(fieldcode,recid)
    return fld_val
def Create_Modify_Interface_transform_date(fld_val):
    """Accept a field's value as a string. If the value is a date in one of the following formats:
          DD Mon YYYY (e.g. 23 Apr 2005)
          YYYY-MM-DD  (e.g. 2005-04-23)
       ...transform this date value into "DD/MM/YYYY" (e.g. 23/04/2005).
    """
    if re.search("^[0-9]{2} [a-z]{3} [0-9]{4}$",fld_val,re.IGNORECASE) is not None:
        try:
            fld_val = time.strftime("%d/%m/%Y",time.strptime(fld_val,"%d %b %Y"))
        except (ValueError,TypeError):
            # bad date format:
            pass
    elif re.search("^[0-9]{4}-[0-9]{2}-[0-9]{2}$",fld_val,re.IGNORECASE) is not None:
        try:
            fld_val = time.strftime("%d/%m/%Y",time.strptime(fld_val,"%Y-%m-%d"))
        except (ValueError,TypeError):
            # bad date format:
            pass
    return fld_val


def Create_Modify_Interface(parameters,curdir,form):
    """Create an interface for the modification of a document, based on the fields that the user has
       chosen to modify
    """
    global sysno,rn
    t=""
    # variables declaration
    fieldname = parameters['fieldnameMBI']
    # Path of file containing fields to modify
    if os.path.exists("%s/%s" % (curdir,fieldname)):
        fp = open( "%s/%s" % (curdir,fieldname), "r" )
        fieldstext = fp.read()
        fp.close()
    else:
        raise functionError("cannot find fields to modify")
    fieldstext = re.sub("\+","\n",fieldstext)
    fields = fieldstext.split("\n")
    #output some text    
    t=t+"<CENTER bgcolor=\"white\">The document <B>%s</B> has been found in the database.</CENTER><BR>Please modify the following fields:<BR>Then press the 'END' button at the bottom of the page<BR>\n" % rn
    for field in fields:
        subfield = ""
        value = ""
        marccode = ""
        text = ""
        # retrieve and display the modification text
        t=t+"<FONT color=\"darkblue\">\n"
        res = run_sql("SELECT modifytext FROM sbmFIELDDESC WHERE  name=%s", (field,))
        if len(res)>0:
            t=t+"<small>%s</small> </FONT>\n" % res[0][0]
        # retrieve the marc code associated with the field
        res = run_sql("SELECT marccode FROM sbmFIELDDESC WHERE name=%s", (field,))
        if len(res) > 0:
            marccode = res[0][0]
        # then retrieve the previous value of the field
        if os.path.exists("%s/%s" % (curdir,"Create_Modify_Interface_DONE")):
            # Page has been reloaded - get field value from text file on server, not from DB record
            value = Create_Modify_Interface_getfieldval_fromfile(curdir,field)
        else:
            # First call to page - get field value from DB record
            value = Create_Modify_Interface_getfieldval_fromDBrec(marccode, sysno)
        # If field is a date value, transform date into format DD/MM/YYYY:
        value = Create_Modify_Interface_transform_date(value)
        res = run_sql("SELECT * FROM sbmFIELDDESC WHERE name=%s", (field,))
        if len(res) > 0:
            type = res[0][3]
            numcols = res[0][6]
            numrows = res[0][5]
            size = res[0][4]
            maxlength = res[0][7]
            val = res[0][8]
            fidesc = res[0][9]
            if type == "T":
                text="<TEXTAREA name=\"%s\" rows=%s cols=%s wrap>%s</TEXTAREA>" % (field,numrows,numcols,value)
            elif type == "F":
                text="<INPUT TYPE=\"file\" name=\"%s\" size=%s maxlength=%s>" % (field,size,maxlength)
            elif type == "I":
                # JY correction, 15.6.01
                value = re.sub("[\n\r\t]+","",value)
                text="<INPUT name=\"%s\" size=%s value=\"%s\"> " % (field,size,val)
                text= text + "<SCRIPT>document.forms[0].%s.value=\"%s\";</SCRIPT>" % (field,value)
            elif type == "H":
                text="<INPUT type=\"hidden\" name=\"%s\" value=\"%s\">" % (field,val)
                text=text+"<SCRIPT>document.forms[0].%s.value=\"%s\";</SCRIPT>" % (field,value)
            elif type == "S":
                values = re.split("[\n\r]+",value)
                text=fidesc
                if re.search("%s\[\]" % field,fidesc):
                    multipletext = "[]"
                else:
                    multipletext = ""
                if len(values) > 0 and not(len(values) == 1 and values[0] == ""):
                    text += "<SCRIPT>\n"
                    text += "var i = 0;\n"
                    text += "el = document.forms[0].elements['%s%s'];\n" % (field,multipletext)
                    text += "max = el.length;\n"
                    for val in values:
                        text += "var found = 0;\n"
                        text += "var i=0;\n"
                        text += "while (i != max) {\n"
                        text += "  if (el.options[i].value == \"%s\" || el.options[i].text == \"%s\") {\n" % (val,val)
                        text += "    el.options[i].selected = true;\n"
                        text += "    found = 1;\n"
                        text += "  }\n"
                        text += "  i=i+1;\n"
                        text += "}\n"
                        #text += "if (found == 0) {\n"
                        #text += "  el[el.length] = new Option(\"%s\", \"%s\", 1,1);\n"
                        #text += "}\n"
                    text += "</SCRIPT>\n"
            elif type == "D":
                text=fidesc
            elif type == "R":
                co = compile(fidesc.replace("\r\n","\n"),"<string>","exec")
                exec(co)
            else:
                text="%s: unknown field type" % field
            t = t+"<small>%s</small>" % text
    # output some more text
    t=t+"<BR><BR><CENTER><small><INPUT type=\"button\" width=400 height=50 name=\"End\" value=\"END\" onClick=\"document.forms[0].step.value = 2;document.forms[0].submit();\"></small></CENTER></H4>"
    # Flag File to be written if first call to page, which tells function that if page is reloaded,
    # it should get field values from text files in curdir, instead of from DB record:
    if not os.path.exists("%s/%s" % (curdir,"Create_Modify_Interface_DONE")):
        # Write flag file:
        try:
            fp = open( "%s/%s" % (curdir,"Create_Modify_Interface_DONE"), "w")
            fp.write("DONE\n")
            fp.flush()
            fp.close()
        except IOError, e:
            # Can't open flag file for writing
            pass
    return t

