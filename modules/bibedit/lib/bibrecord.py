# -*- coding: utf-8 -*-
##
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

"""
BibRecord - XML MARC processing library for CDS Invenio
"""

### IMPORT INTERESTING MODULES AND XML PARSERS
    
## import interesting modules:
try:
    import sys
    import re
    from zlib import decompress
    import_error = 0
except ImportError, e:
    import_error = 1
    imperr = e
        
## test available parsers:
try:
    import sys
    import string
    err=[]
except ImportError, e:
    parser = -3
    err1 = e

try:
    from invenio.bibrecord_config import *
    verbose = cfg_bibrecord_default_verbose_level
    correct = cfg_bibrecord_default_correct
    parsers = cfg_bibrecord_parsers_available
except ImportError, e:
    parser = -2
    verbose = 0
    correct = 0
    parsers = []

if parsers == []:
    print 'No parser available'
    sys.exit(2)
else:
    j,i=1,1

    if 2 in parsers:
        try:
            import pyRXP
            parser = 2
    ## function to show the pyRXP_parser warnings ##
            def warnCB(s):
                """ function used to treat the PyRXP parser warnings"""
                global err
                err.append((0,'Parse warning:\n'+s))
        
            err2 = ""
        except ImportError,e :
            err2=e
            i=0
    elif 1 in parsers:
        try:
            from Ft.Xml.Domlette import NonvalidatingReader
            parser = 1
        except ImportError,e :
            err2=e
            j=0
    elif 0 in parsers:
        try:
            from xml.dom.minidom import parseString
            parser = 0
        except ImportError,e :
            err2=e
            parser = -1

    if not i:
        if 1 in parsers:
            try:
                from Ft.Xml.Domlette import NonvalidatingReader
                parser = 1
            except ImportError,e :
                err2=e
                j=0
        elif 0 in parsers:
            try:
                from xml.dom.minidom import parseString
                parser = 0
            except ImportError,e :
                err2=e
                parser = -1
        else:
            parser = -1

    if not j:
        if 0 in parsers:
            try:
                from xml.dom.minidom import parseString
                parser = 0
            except ImportError,e :
                err2=e
                parser = -1
        else:
            parser = -1

### INTERFACE / VISIBLE FUNCTIONS

def create_records(xmltext,verbose=verbose,correct=correct):
	"""
	creates a list of records 
	"""
        global import_error
        err = []

        if import_error == 1:
            err.append((6,imperr))
        else:
            if sys.version >= '2.3':
                pat = r"<record.*?>.*?</record>"
                p = re.compile(pat,re.DOTALL) # DOTALL - to ignore whitespaces
                list = p.findall(xmltext)
            else:
                l = xmltext.split('<record>')
                n=len(l)
                ind = (l[n-1]).rfind('</record>')
                aux = l[n-1][:ind+9]
                l[n-1] = aux
                list=[]
                for s in l:
                    if s != '':
                        i = -1
                        while (s[i].isspace()):
                            i=i-1
                        if i == -1:#in case there are no spaces  at the end
                            i=len(s)-1
                        if s[:i+1].endswith('</record>'):
                            list.append('<record>'+s)            
            listofrec = map((lambda x:create_record(x,verbose,correct)),list)
            return listofrec
        return []

# Record :: {tag : [Field]}
# Field :: (Subfields,ind1,ind2,value)
# Subfields :: [(code,value)]

def create_record(xmltext,verbose = verbose, correct=correct):
    """
    creates a record object and returns it
    uses pyRXP if installed else uses 4Suite domlette or xml.dom.minidom
    """
    global parser

    (i,errors) = testImports(parser)
    if i==0:
        print "Error: no suitable XML parsers found.  Please read INSTALL file."
        sys.exit()

    try:
        if parser==2:
            ## the following is because of DTD validation
            t = """<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE collection SYSTEM "file://%s">
            <collection>\n""" % cfg_marc21_dtd
            t = "%s%s" % (t,xmltext)
            t = "%s</collection>" % t
            xmltext = t
            (rec,er) = create_record_RXP(xmltext,verbose,correct)
        elif parser:
            (rec,er) = create_record_4suite(xmltext,verbose,correct)
        else:
            (rec,er) = create_record_minidom(xmltext,verbose,correct)
        errs = warnings(er)
    except Exception, e:
        print e
        errs = warnings(concat(err))
        return (None,0,errs)
    
    if errs == []: 
        return (rec,1,errs)
    else:
        return (rec,0,errs)


        
def record_get_field_instances(rec, tag="", ind1="", ind2=""):
    """Return the list of field instances of record REC matching TAG and IND1 and IND2.
       When TAG is an emtpy string, then return all field instances."""
    out = []
    if tag:
        if record_has_field(rec, tag):
            for possible_field_instance in rec[tag]:
                if possible_field_instance[1] == ind1 and \
                   possible_field_instance[2] == ind2:
                       out.append(possible_field_instance)
    else:
        return rec.items()
    return out

def record_has_field(rec,tag):
    """checks whether record 'rec' contains tag 'tag'"""
    return rec.has_key(tag)
        
def record_add_field(rec, tag, ind1="", ind2="", controlfield_value="", datafield_subfield_code_value_tuples=[]):
    """
    Add a new field TAG to record REC with the following values:

       In case of creating a controlfield, only one argument matters:

           controlfield_value - value of the control field, in case
                                this field is a controlfield.

       In case of creating a datafield, only these arguments matter:

           ind1, ind2 - indicators of the datafield

           datafield_subfield_code_value_tuples - list of subfield code and
             value tuples, e.g.: [('a', 'Ellis, J'), ('e', 'editor')]
       
    Return the field number of newly created field.
    """

    # detect field number to be used for insertion:
    vals=rec.values()
    if vals != []:
        try:
            newfield_number = 1 + max([f[4] for v in vals for f in v])
        except ValueError:
            # vals could have been a list of empty lists, see test_add_delete_add_field_to_empty_record()
            newfield_number = 1
    else:
        newfield_number = 1

    # create new field object:
    if controlfield_value:        
        newfield = ([], ind1, ind2, str(controlfield_value), newfield_number)
    else:
        newfield = (datafield_subfield_code_value_tuples, ind1, ind2, "", newfield_number)

    # add it to the record structure:
    if rec.has_key(tag):
        rec[tag].append(newfield)
    else:
        rec[tag] = [newfield]

    # return new field number:
    return newfield_number
        
def record_delete_field(rec,tag,ind1="",ind2=""):
    """
    delete all fields defined with marc tag 'tag' and indicators 'ind1' and 'ind2'
    from record 'rec'
    """
    newlist = []
    if rec.has_key(tag):
        for field in rec[tag]:
            if not (field[1]==ind1 and field[2]==ind2):
                newlist.append(field)
        rec[tag] = newlist
        
def record_get_field_value(rec,tag,ind1="",ind2="",code=""):
    """
    retrieves the value of the first field containing tag 'tag' and indicators 'ind1' and 'ind2'
    inside record 'rec'. Returns the found value as a string. If no matching field is found
    returns the empty string.
    if the tag has a '%', it will retrieve the value of first field containg tag, which first characters are those before '%' in tag. The ind1, ind2 and code parameters will be ignored
    """

    s = tag.split('%')
    if len(s) > 1:
        t = s[0]
        keys=rec.keys()
        tags=[k for k in keys if k.startswith(t)]
        for tag in tags:
            fields = rec[tag]
            for field in fields:
                if field[3] != "":
                    return field[3]
                else:
                    for subfield in field[0]:
                            return subfield[1]
    else:
        if rec.has_key(tag):
            fields = rec[tag]
            for field in fields:
                if field[1]==ind1 and field[2]==ind2:
                    if field[3] != "":
                        return field[3]
                    else:
                        for subfield in field[0]:
                            if subfield[0]==code:
                               return subfield[1]
      
    return ""

def record_get_field_values(rec,tag,ind1="",ind2="",code=""):
    """
    retrieves the values of all the fields containing tag 'tag' and indicators 'ind1' and 'ind2'
    inside record 'rec'. Returns the found values as a list. If no matching field is found
    returns an empty list.
    if the tag has a '%', it will retrieve the value of all fields containg tag, which first characters are those before '%' in tag.  The ind1, ind2 and code parameters will be ignored
    """
    tmp = []

    s = tag.split('%')
    if len(s) > 1:
        t = s[0]
        keys=rec.keys()
        tags=[k for k in keys if k.startswith(t)]
        for tag in tags:
            fields = rec[tag]
            for field in fields:
                if field[3] != "":
                    tmp.append(field[3])
                else:
                    for subfield in field[0]:
                            tmp.append(subfield[1])
    else:
        if rec.has_key(tag):
            fields = rec[tag]
            for field in fields:
                if field[1]==ind1 and field[2]==ind2:
                    if field[3] != "":
                        tmp.append(field[3])
                    else:
                        for subfield in field[0]:
                            if subfield[0]==code:
                                tmp.append(subfield[1])
      
    return tmp

def print_rec(rec,format=1):
    """prints a record
       format = 1 -- XML
       format = 2 -- HTML (not implemented)
      """

    if format==1:
        text = record_xml_output(rec)
    else:
        return ''

    return text

def print_recs(listofrec,format=1):
    """prints a list of records
       format = 1 -- XML
       format = 2 -- HTML (not implemented)
       if 'listofrec' is not a list it returns empty string
    """
    text = ""
    
    if type(listofrec).__name__ !='list':
        return ""
    else:
        for rec in listofrec:
            text = "%s\n%s" % (text,print_rec(rec,format))
    return text

def record_xml_output(rec):
    """generates the XML for record 'rec' and returns it as a string"""
    xmltext = "<record>\n"
    if rec:
        # add the tag 'tag' to each field in rec[tag]
        fields=[]
        for tag in rec.keys():
            for field in rec[tag]:
                fields.append((tag,field))
        record_order_fields(fields)    
        for field in fields:
            xmltext += str(field_xml_output(field[1],field[0]))
    xmltext = "%s</record>" % xmltext
    return xmltext

def records_xml_output(listofrec):
    """generates the XML for the list of records 'listofrec' and returns it as a string"""
    xmltext = """<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE collection SYSTEM "file://%s">
    <collection>\n""" % cfg_marc21_dtd
    
    for rec in listofrec:
        xmltext = "%s%s" % (xmltext, record_xml_output(rec))
    xmltext = "%s</collection>" % xmltext
    return xmltext
    
def field_get_subfield_instances(field):
    """returns the list of subfields associated with field 'field'"""
    return field[0]

def field_get_subfield_values(field_instance, code):
    """Return subfield CODE values of the field instance FIELD."""
    out = []
    for sf_code, sf_value in field_instance[0]:
        if sf_code == code:
            out.append(sf_value)
    return out
        
def field_add_subfield(field,code,value):
    """adds a subfield to field 'field'"""
    field[0].append(create_subfield(code,value))        


### IMPLEMENTATION / INVISIBLE FUNCTIONS

def create_record_RXP(xmltext, verbose=verbose, correct=correct):
    """
    creates a record object and returns it
    uses the RXP parser
    
    If verbose>3 then the parser will be strict and will stop in case of well-formedness errors
    or DTD errors
    If verbose=0, the parser will not give warnings
    If 0<verbose<=3, the parser will not give errors, but will warn the user about possible mistakes

    correct != 0 -> We will try to correct errors such as missing attributtes
    correct = 0 -> there will not be any attempt to correct errors
    
    """
    
    record = {}
    global err

    ord = 1 # this is needed because of the record_xml_output function, where we need to know
            # the order of the fields


    TAG, ATTRS,CHILD_LIST = range(3)
    
    if verbose > 3:
        p = pyRXP.Parser(ErrorOnValidityErrors=1,
                         ProcessDTD=1,
                         ErrorOnUnquotedAttributeValues=1,
                         warnCB = warnCB,
                         srcName='string input')
    else:
        p = pyRXP.Parser(ErrorOnValidityErrors=0,
                         ProcessDTD=1,
                         ErrorOnUnquotedAttributeValues=0,
                         warnCB = warnCB,
                         srcName='string input')

    
    if correct:
        (rec,e) = wash(xmltext)
        err.extend(e)
        return (rec,e)

    
    root1=p(xmltext) #root = (tagname, attr_dict, child_list, reserved)

    if root1[0]=='collection':
        recs = [t for t in root1[CHILD_LIST] if type(t).__name__=='tuple' and t[TAG]=="record"]
        if recs !=[]:
            root = recs[0]
        else:
            root = None
    else:
        root=root1
    
    

    # get childs of 'controlfield'
    childs_controlfield = []
    if not root[2]==None:
        childs_controlfield =[t for t in root[CHILD_LIST] if type(t).__name__=='tuple' and t[TAG]=="controlfield"]
        
    # get childs of 'datafield'
    childs_datafield = []
    if not root[CHILD_LIST]==None:
        childs_datafield =[t for t in root[CHILD_LIST] if type(t).__name__=='tuple' and t[TAG]=="datafield"]
        
    for controlfield in childs_controlfield:
        s=controlfield[ATTRS]["tag"]
        value=''
        if not controlfield==None:
            value=''.join([ n for n in controlfield[CHILD_LIST] if type(n).__name__ == 'str'])

        name = type(value).__name__
        
        if name in ["int","long"] :
            st = str(value)
        elif name in ['str', 'unicode']:
            st = value
        else:
            if verbose:
                err.append((7,'Type found: ' + name))
            st = "" # the type of value is not correct. (user insert something like a list...)
        

        field = ([],"","",st,ord) #field = (subfields, ind1, ind2,value,ord)

        if record.has_key(s):
            record[s].append(field)
        else:
            record[s]=[field]
            
        ord = ord+1

    for datafield in childs_datafield:

        #create list of subfields
        subfields = []

        childs_subfield = []
        if not datafield[CHILD_LIST]==None:
            childs_subfield =[t for t in datafield[CHILD_LIST] if type(t).__name__=='tuple' and t[0]=="subfield"]

        for subfield in childs_subfield:
            value=''
            if not subfield==None:
                value=''.join([ n for n in subfield[CHILD_LIST] if type(n).__name__ == 'str'])
                                       #get_string_value(subfield)
            if subfield[ATTRS].has_key('code'):
                subfields.append((subfield[ATTRS]["code"],value))
            else:
                subfields.append(('!',value))

        #create field

        if datafield[ATTRS].has_key('tag'):
            s = datafield[ATTRS]["tag"]
        else:
            s = '!'

        if datafield[ATTRS].has_key('ind1'):
            ind1 = datafield[ATTRS]["ind1"]
        else:
            ind1 = '!'

        if datafield[ATTRS].has_key('ind2'):
            ind2 = datafield[ATTRS]["ind2"]
        else:
            ind2 = '!'
        
        field = (subfields,ind1,ind2,"",ord)
            
        if record.has_key(s):
            record[s].append(field)
        else:
            record[s]=[field]

        ord = ord+1
    
    return (record,err)


    
def create_record_minidom(xmltext, verbose=verbose, correct=correct):
    """
    creates a record object and returns it
    uses xml.dom.minidom
    """
    
    record = {}
    ord=1
    global err

    if correct:
        xmlt = xmltext
        (rec,e) = wash(xmlt,0)
        err.extend(e)
        return (rec,err)
        
    dom = parseString(xmltext)
    root = dom.childNodes[0]

    for controlfield in get_childs_by_tag_name(root,"controlfield"):
        s = controlfield.getAttribute("tag")

        text_nodes = controlfield.childNodes
        v = u''.join([ n.data for n in text_nodes ]).encode("utf-8")

        name = type(v).__name__
        if (name in ["int","long"]) :
            field = ([],"","",str(v),ord) # field = (subfields, ind1, ind2,value)
        elif name in ['str', 'unicode']:
            field = ([],"","",v,ord)
        else:
            if verbose:
                err.append((7,'Type found: ' + name))
  
            field = ([],"","","",ord)# the type of value is not correct. (user insert something like a list...)

        if record.has_key(s):
            record[s].append(field)
        else:
            record[s]=[field]
        ord=ord+1

    for datafield in get_childs_by_tag_name(root,"datafield"):
        subfields = []
        
        for subfield in get_childs_by_tag_name(datafield,"subfield"):
            text_nodes = subfield.childNodes
            v = u''.join([ n.data for n in text_nodes ]).encode("utf-8")
            code = subfield.getAttributeNS(None,'code').encode("utf-8")
            if code != '':
                subfields.append((code,v))
            else:
                subfields.append(('!',v))

        s = datafield.getAttribute("tag").encode("utf-8")
        if s == '':
            s = '!'
            
        ind1 = datafield.getAttribute("ind1").encode("utf-8")
        
        ind2 = datafield.getAttribute("ind2").encode("utf-8")         
        
        if record.has_key(s):
            record[s].append((subfields,ind1,ind2,"",ord))
        else:
            record[s]=[(subfields,ind1,ind2,"",ord)]
        ord = ord+1

    return (record,err)


def create_record_4suite(xmltext,verbose=verbose,correct=correct):
    """
    creates a record object and returns it
    uses 4Suite domlette
    """

    record = {}
    global err

    if correct:
        xmlt = xmltext
        (rec,e) = wash(xmlt,1)
        err.extend(e)
        return (rec,e)
        
    dom = NonvalidatingReader.parseString(xmltext,"urn:dummy")
    
    root = dom.childNodes[0]
    
    ord=1
    for controlfield in get_childs_by_tag_name(root,"controlfield"):
        s = controlfield.getAttributeNS(None,"tag")

        text_nodes = controlfield.childNodes
        v = u''.join([ n.data for n in text_nodes ]).encode("utf-8")

        name = type(v).__name__
        if (name in ["int","long"]) :
            field = ([],"","",str(v),ord) # field = (subfields, ind1, ind2,value)
        elif name in ['str','unicode']:
            field = ([],"","",v,ord)
        else:
            if verbose:
                err.append((7,'Type found: ' + name))

            field = ([],"","","",ord)# the type of value is not correct. (user insert something like a list...)
        

        if record.has_key(s):
            record[s].append(field)
        else:
            record[s]=[field]
        ord=ord+1


    for datafield in get_childs_by_tag_name(root,"datafield"):
        subfields = []

        for subfield in get_childs_by_tag_name(datafield,"subfield"):
             text_nodes = subfield.childNodes
             v = u''.join([ n.data for n in text_nodes ]).encode("utf-8")

             code = subfield.getAttributeNS(None,'code').encode("utf-8")
             if code != '':
                 subfields.append((code,v))
             else:
                subfields.append(('!',v))

        s = datafield.getAttributeNS(None,"tag").encode("utf-8")
        if s == '':
            s = '!'
            
        ind1 = datafield.getAttributeNS(None,"ind1").encode("utf-8")
        
        ind2 = datafield.getAttributeNS(None,"ind2").encode("utf-8")
                     
  
        if record.has_key(s):
            record[s].append((subfields,ind1,ind2,"",ord))
        else:
            record[s]=[(subfields,ind1,ind2,"",ord)]
        ord=ord+1

    return (record,err)

def record_order_fields(rec,fun="order_by_ord"):
    """orders field inside record 'rec' according to a function"""
    rec.sort(eval(fun))
    return

def record_order_subfields(rec,fun="order_by_code"):
    """orders subfield inside record 'rec' according to a function"""
    for tag in rec:
        for field in rec[tag]:
            field[0].sort(eval(fun))
    return
    
def concat(list):
    """concats a list of lists"""
    newl = []
    for l in list:
        newl.extend(l)
    return newl

def create_subfield(code, value):
    """Create a subfield object and return it."""
    if type(value).__name__ in ["int","long"]:
        s = str(value)
    else:
        s = value
    subfield = (code, s)    
    return subfield
    
def field_add_subfield(field,code,value):
    """adds a subfield to field 'field'"""
    field[0].append(create_subfield(code,value))
        
def field_xml_output(field,tag):
    """generates the XML for field 'field' and returns it as a string"""
    xmltext = ""
    if field[3] != "":
        xmltext = "%s  <controlfield tag=\"%s\">%s</controlfield>\n" % (xmltext,tag,encode_for_xml(field[3]))
    else:
        xmltext = "%s  <datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">\n" % (xmltext,tag,field[1],field[2])
        for subfield in field[0]:
            xmltext = "%s%s" % (xmltext,subfield_xml_output(subfield))
        xmltext = "%s </datafield>\n" % xmltext
    return xmltext
        
def subfield_xml_output(subfield):
    """generates the XML for a subfield object and return it as a string"""
    xmltext = "    <subfield code=\"%s\">%s</subfield>\n" % (subfield[0],encode_for_xml(subfield[1]))
    return xmltext
        
def order_by_ord(field1, field2):
    """function used to order the fields according to their ord value"""
    return cmp(field1[1][4], field2[1][4])
    
def order_by_code(subfield1,subfield2):
    """function used to order the subfields according to their code value"""
    return cmp(subfield1[0],subfield2[0])
    
def get_childs_by_tag_name(node, local):
    """retrieves all childs from node 'node' with name 'local' and returns them as a list"""
    cNodes = list(node.childNodes)
    res = [child for child in cNodes if child.nodeName==local]
    return res

def get_string_value(node):
    """gets all child text nodes of node 'node' and returns them as a unicode string"""
    text_nodes = node.childNodes
    return u''.join([ n.data for n in text_nodes ])
    
def get_childs_by_tag_name_RXP(listofchilds,tag):
    """retrieves all childs from 'listofchilds' with tag name 'tag' and returns them as a list.
       listofchilds is a list returned by the RXP parser
    """
    l=[]
    if not listofchilds==None:
        l =[t for t in listofchilds if type(t).__name__=='tuple' and t[0]==tag]
  
    return l
    
def getAttribute_RXP(root, attr):
    """ returns the attributte 'attr' from root 'root'
        root is a node returned by RXP parser
    """
    try:
        return u''.join(root[1][attr])
    except KeyError,e:
        return ""

def get_string_value_RXP(node):
    """gets all child text nodes of node 'node' and returns them as a unicode string"""
    if not node==None:
        return ''.join([ n for n in node[2] if type(n).__name__ == 'str'])
    else:
        return ""

def encode_for_xml(s):
    "Encode special chars in string so that it would be XML-compliant."
    s = string.replace(s, '&', '&amp;')
    s = string.replace(s, '<', '&lt;')
    return s

def print_errors(list):
    """ creates a unique string with the strings in list, using '\n' as a separator """
    text=""
    
    for l in list:
        text = '%s\n%s'% (text,l)

    return text

def wash(xmltext, parser=2):
    """
    Check the structure of the xmltext. Returns a record structure and a list of errors.
    parser = 1 - 4_suite
    parser = 2 - pyRXP
    parser = 0 - minidom
    """
    
    errors=[]
    i,e1 = tagclose('datafield',xmltext)
    j,e2 = tagclose('controlfield',xmltext)
    k,e3 = tagclose('subfield',xmltext)
    w,e4 = tagclose('record',xmltext)
    errors.extend(e1)
    errors.extend(e2)
    errors.extend(e3)
    errors.extend(e4)
    
    if i and j and k and w and parser!=-3:
        if parser==1:
            (rec,ee) = create_record_4suite(xmltext,0,0)
        elif parser==2:
            (rec,ee) = create_record_RXP(xmltext,0,0)
        else:
            (rec,ee) = create_record_minidom(xmltext,0,0)
    else:
        return (None,errors)
        

    
    keys = rec.keys()
    
    for tag in keys:
        upper_bound = '999'
        n = len(tag)
        
        if n>3:
            i=n-3
            while i>0:
                upper_bound = '%s%s' % ('0',upper_bound)
                i = i-1
        
        if tag == '!': # missing tag
            errors.append((1, '(field number(s): ' + ([f[4] for f in rec[tag]]).__str__()+')'))
            v=rec[tag]
            rec.__delitem__(tag)
            rec['000'] = v
            tag = '000'
        elif not ("001" <= tag <=upper_bound):
            errors.append(2)
            v = rec[tag]
            rec.__delitem__(tag)
            rec['000'] = v
            tag = '000'
            
        fields =[]
        for field in rec[tag]:
            if field[0]==[] and field[3]=='': ## datafield without any subfield
                errors.append((8,'(field number: '+field[4].__str__()+')'))
            
            subfields=[]
            for subfield in field[0]:
                if subfield[0]=='!': 
                    errors.append((3,'(field number: '+field[4].__str__()+')'))
                    newsub = ('',subfield[1])
                else:
                    newsub = subfield
                subfields.append(newsub)
                    
            if field[1]=='!':
                errors.append((4,'(field number: '+field[4].__str__()+')'))
                ind1 = ""
            else:
                ind1 = field[1]

            if field[2]=='!':
                errors.append((5,'(field number: '+field[4].__str__()+')'))
                ind2 = ""
            else:
                ind2=field[2]
                
            newf = (subfields,ind1,ind2,field[3],field[4])
            fields.append(newf)
            
        rec[tag]=fields
    
    return (rec,errors)
                         
def tagclose(tagname,xmltext):
    """ checks if an XML document does not hae any missing tag with name tagname
    """
    import re
    errors=[]
    pat_open = '<'+tagname+'.*?>'
    pat_close = '</'+tagname+'>'
    p_open = re.compile(pat_open,re.DOTALL) # DOTALL - to ignore whitespaces
    p_close = re.compile(pat_close,re.DOTALL)
    list1 = p_open.findall(xmltext)
    list2 = p_close.findall(xmltext)

    if len(list1)!=len(list2):
        errors.append((99,'(Tagname : ' + tagname + ')'))
        return (0,errors)
    else:
        return (1,errors)
        
def testImports(c):
    """ Test if the import statements did not failed"""
    errors=[]
    global err1,err2
    
    if c==-1:
        i = 0
        errors.append((6,err2))
    elif c == -3:
        i=0
        errors.append((6,err1))
    else:
        i=1
    return (i,errors)

def warning(code):
    """ It returns a warning message of code 'code'.
        If code = (cd, str) it returns the warning message of code 'cd'
        and appends str at the end"""
    
    ws = cfg_bibrecord_warning_msgs
    s=''

    if type(code).__name__ == 'str':
        return code
    
    if type(code).__name__ == 'tuple':
        if type(code[1]).__name__ == 'str':
            s = code[1]
            c = code[0]
    else:
        c = code
    if ws.has_key(c):
        return ws[c]+s
    else:
        return ""

def warnings(l):
    """it applies the function warning to every element in l"""
    list = []
    for w in l:
        list.append(warning(w))
    return list

