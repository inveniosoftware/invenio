# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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

"""
textmarc2xmlmarc utility.
"""

__version__ = ""

import fileinput
import getopt
import string
import sys
import re
import os.path

from codecs import BOM_UTF8

class Field:
    "A class to hold information on bibliographic field and its value."

    def __init__(self, value_as_string=""):
        "Creates field instance from a string of the form '$$aElis$2editor'."

        self.value = {}
        if value_as_string:
            s = value_as_string
            if s[0:2] != '$$': # if does not start by subfield, add artificial beginning subfield
                s = '$$ '+ s
            for chunk in string.split(s, '$$'):
                if chunk:
                    aleph_spread = alephsplit(chunk[1:])
                    if len(aleph_spread) > 1:
                        self.add('0',aleph_spread[1])

                    self.add(chunk[0], aleph_spread[0]) # add subfield
                    # self.add(chunk[0], chunk[1:])

    def has_subfield(self, subfield_code):
        "Does the field contain this subfield?"
        if self.value.has_key(subfield_code):
            return 1
        else:
            return 0

    def get_subfield(self, subfield_code=''):
        "Returns the value of a given subfield."
        if self.value.has_key(subfield_code):
            return self.value[subfield_code][0] # return first subfield
        else:
            return ""

    def add(self, subfield_code, subfield_value):
        "Adds subfield to the field."
        c = string.strip(subfield_code)
        v = string.strip(subfield_value)
        if v: # let us disregard empty subfields
            if self.value.has_key(c):
                self.value[c].append(v)
            else:
                self.value[c] = [v]

    def display(self,field_type = "datafield"):
        "Displays field in xml format."
        keys = self.value.keys()
        keys.sort()
        out = ""

        for subfield_code in keys:
            for subfield_value in self.value[subfield_code]:
                subfield_value = encode_for_xml(subfield_value)
                if subfield_value:
                    if out != "":
                        out = out + "\n"
                    if field_type == "datafield":
                        out = out + "      <subfield code=\"%s\">%s</subfield>" % (subfield_code, subfield_value)
                    else:
                        out = out + "%s" % subfield_value
        return out


class Record:
    "A class to hold information on bibliographic record."

    def __init__(self, sysno="0"):
        "Creates record instance."
        self.sysno = string.strip(sysno)
        self.field = {}

    def add(self, field_tag, field_value):
        "Adds the field to the record."
        t = string.strip(field_tag)
        if self.field.has_key(t):
            self.field[t].append(field_value)
        else:
            self.field[t] = [field_value]

    def has_basenb(self, bases):
        "Tests whether one of record's BASE values is among one of the values passed in argument tuple."
        if self.field.has_key('BASE'):
            for f in self.field['BASE']:
                try:
                    b = int(f.get_subfield()) # get BASE number
                    if b in bases:
                        return 1
                except:
                    pass
        if self.field.has_key('BA'):
            for f in self.field['BA']:
                try:
                    b = int(f.get_subfield()) # get BASE number
                    if b in bases:
                        return 1
                except:
                    pass
        if self.field.has_key('BAS'):
            for f in self.field['BAS']:
                try:
                    b = int(f.get_subfield('a')) # get BASE number
                    if b in bases:
                        return 1
                except:
                    pass
        if self.field.has_key('960'):
            for f in self.field['960']:
                try:
                    b = int(f.get_subfield('a')) # get BASE number
                    if b in bases:
                        return 1
                except:
                    pass
        return 0

    def display(self, filehandle):
        "Displays record in the xml format."

        ## display record header
        print '<record>'
        print '   <controlfield tag="001">%d</controlfield>' % int(self.sysno)

        ## display record body
        keys = self.field.keys()

        keys.sort()
        for field_tag in keys:
            for field_instance in self.field[field_tag]:
                if field_tag[0] >= '0' and field_tag[0] <= '9': # are we using numbers for field tag name?
                    tag = field_tag[0:3] # yes, so the first three chars constitute MARC-21 tag name
                    i1 = field_tag[3:4]  # next char is 1st indicator
                    if i1 == "_" or i1 == " ":
                        i1 = " "
                    i2 = field_tag[4:5]  # next char is 2nd indicator
                    if i2 == "_" or i2 == " ":
                        i2 = " "
                else:
                    tag = field_tag
                    i1 = " "
                    i2 = " "


                if tag[:2] == "00":
                    field_type = "controlfield"
                else:
                    field_type = "datafield"
                instance_to_print = field_instance.display(field_type)
                if instance_to_print:
                    if tag[:2] != "00":
                        print "   <datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % (tag, i1, i2)
                        print instance_to_print
                        print "   </datafield>"
                    else:
                        if not (tag == "001" and int(self.sysno) == int(instance_to_print)):
                            print "   <controlfield tag=\"%s\">%s</controlfield>" % (tag,instance_to_print)


        ## display record footer
        print "</record>"

def log_on_exec(command):
    "Execute command and create record in log file"
    return os.system(command)

def alephsplit(value):
    "splits value on <<foo=bar>> and returns list with two elements (foo and bar)"

    out = []
    y = re.split("(<<.*?>>)",value)

    if y!=None:

        outf1 = ""
        outf0 = ""
        count = 0

        for item in y:
            if (re.match("<<.*?>>",item) == None):
                outf1 = outf1 + item
                outf0 = outf0 + item
            else:
                if re.search("=",item):
                    z = re.search("<<.*?=",item)
                    if z!= None:
                        outf1 = outf1 + z.group()[2:-1]
                    z = re.search("=.*?>>",item)
                    if z!= None:
                        outf0 = outf0 + z.group()[1:-2]
                        count = count + 1
                else:
                    z = re.search("<<.+>>",item)
                    if z!=None:
                        outf1 = outf1 + z.group()[2:-2]

        out.append(outf1)
        if count > 0:
            out.append(outf0)
        else:
            out.append("")

    return out


def clean(x,values):
    "Empty when already in list of values"

    for v in values:
        if (v == x):
            x = ""
    return x


def transform_record(rec, errors):
    "Transforms record from MARC-21 format to XML format."
    out = Record(rec.sysno)
    is_deleted = 0
    original_collids = []

    for tag in rec.field.keys():
        if tag == "BAS":
            for field_instance in rec.field[tag]:
                out.add("960", field_instance)
        elif tag == "DEL":
            is_deleted = 1
        elif tag == "591":
            pass # we drop 591 field that is of secret internal note nature (TS 20070123)
        elif tag == "CAT" or tag == "961":
            first_CAT = ""
            last_CAT = ""
            for field_instance in rec.field[tag]:
                if first_CAT == "":
                    first_CAT = field_instance
                last_CAT = field_instance
            outf = Field()
            if first_CAT.has_subfield('x'):
                outf.add('x',string.replace(first_CAT.get_subfield('x'),'-',''))
            elif first_CAT.has_subfield('c'):
                outf.add('x',string.replace(first_CAT.get_subfield('c'),'-',''))
            if last_CAT.has_subfield('c'):
                outf.add('c',string.replace(last_CAT.get_subfield('c'),'-',''))
            if last_CAT.has_subfield('l'):
                outf.add('l',last_CAT.get_subfield('l'))
            if last_CAT.has_subfield('h'):
                outf.add('h',last_CAT.get_subfield('h'))
            out.add('961', outf)
        elif tag == "LKR":
            for field_instance in rec.field[tag]:
                out.add("962", field_instance)
        elif tag == "OWN":
            for field_instance in rec.field[tag]:
                out.add("963", field_instance)
        elif (tag == "520" or tag == "590"):
            topfield = 1000
            outfa = Field()
            outfb = Field()
            listvaluesa = {}
            listvaluesb = {}
            listordersa = []
            listordersb = []
            valuea = ''
            valueb = ''
            for field_instance in rec.field[tag]:
                if field_instance.has_subfield('b'):
                    partial = field_instance.get_subfield('b')
                    if field_instance.has_subfield('9') and field_instance.get_subfield('9') != "":
                        order = int(field_instance.get_subfield('9'))
                    else:
                        order = topfield
                        topfield = topfield + 1
                    listordersb.append(order)
                    listvaluesb[order]=partial
                elif field_instance.has_subfield('a'):
                    partial = field_instance.get_subfield('a')
                    if field_instance.has_subfield('9') and field_instance.get_subfield('9').isdigit():
                        order = int(field_instance.get_subfield('9'))
                    else:
                        order = topfield
                        topfield = topfield + 1
                    listordersa.append(order)
                    listvaluesa[order]=partial
                else:
                    out.add(tag, field_instance)
            listordersa.sort()
            for order in listordersa:
                valuea = valuea + " " + listvaluesa[order]
            if valuea != '':
                outfa.add('a',valuea)
                out.add(tag, outfa)
            listordersb.sort()
            for order in listordersb:
                valueb = valueb + " " + listvaluesb[order]
            if valueb != '':
                outfb.add('b',valueb)
                out.add(tag, outfb)
        elif tag == "980":
            for field_instance in rec.field[tag]:
                original_collids.append(field_instance)
        elif tag!="FMT" and tag!="LDR" and tag!="008" and tag!="OWN" and tag!="0248" and tag!="---" and tag[0] in string.digits and tag[1] in string.digits and tag[2] in string.digits:
            for field_instance in rec.field[tag]:
                out.add(tag, field_instance)

    #deleted collection field
    if is_deleted:
        outf = Field()
        outf.add('c','DELETED')
        out.add('980',outf)

    return out

class ParseError(Exception):
    """
    Contains info about a parsing error occurred while parsing textmarc
    """
    def __init__(self, lineno=-1, linecontent="", message=""):
        self.lineno = lineno
        self.linecontent = linecontent
        self.message = message
        fileinput.close()

    def __str__(self):
        return repr(self.message)

def transform_file(filename):
    "Reads ALEPH 500 sequential data file and transforms them into XML format."

    re_field_tag = re.compile("^\d\d\d[\s\w]{2}$")
    # This regexp is good enough for the moment, could be further improved if
    # needed
    re_content = re.compile('^(\$\$[a-z0-9].+)+$')

    record_no = 0
    filehandle = ""

    errors = {} # dict that holds 'bad' fields as keys and list of sysnos for which they occurred as values

    record_current = Record() # will hold current bibliographic record as we read through input file
    sysno_old, field_old, value_old = None, None, None # will hold values from previous line

    ## go through all the input file
    for line in fileinput.input(filename):
        if line.startswith(BOM_UTF8):
            ## When files are created with notepad, or in general on Windows,
            ## let's skip the BOM character which would otherwise be included
            ## as such in Python.
            line = line[len(BOM_UTF8):]
        if re.sub("\s","",line) != "":
            # parse the input line with MARC sequential format
            sysno, field, value = line[0:9], line[10:15], line[16:]
            if not re_field_tag.match(field):
                raise ParseError(fileinput.lineno(), line,
                    "Field tag \"%s\" does not match format \d\d\d[\s\w]{2}" % field)
            elif not re_content.match(value):
                raise ParseError(fileinput.lineno(), line,
                    "Content of field \"%s\" is not well formed" % value)
            if field[0] == " " or field[1] == " " or field[2] == " ":
                text = "\nRecord %s: Error in field definition %s\n" % (sysno,field)
                if field[0] == " ":
                    field = string.replace(field," ","0",1)
                if field[1] == " ":
                    field = string.replace(field," ","0",1)
                if field[2] == " ":
                    field = string.replace(field," ","0",1)
                sys.stderr.write(text)
                raise ValueError("Record %s: Error in field definition %s\n" % (sysno,field))
            sysno, field, value = string.strip(sysno), string.strip(field), string.strip(value)
            if sysno == record_current.sysno: # we are in the same bibliographic record
                record_current.add(field_old, Field(value_old))
                field_old, value_old = field, value

            else: # end of current record found, so transform it
                record_no = record_no + 1 # count records
                if field_old and value_old: # add previous line
                    record_current.add(field_old, Field(value_old))

                record_tmp = transform_record(record_current, errors)
                if record_tmp.sysno != "0":
                    record_tmp.display(filehandle)
                record_current = Record(sysno) # set up a new current record
                field_old, value_old = field, value


    ## after all the input lines have been read, display last record
    record_current.add(field_old, Field(value_old))
    record_tmp = transform_record(record_current, errors)

    if record_tmp.sysno != "0":
        record_tmp.display(filehandle)
    ## display eventual errors
    errors_keys = errors.keys(); errors_keys.sort()
    for t in errors_keys:
        sys.stderr.write("\n\nUnknown tag %s occurred for the following SYSNOs:\n   " % t)
        nbchars = 5
        for s in errors[t]:
            sys.stderr.write("%s " % s)
            nbchars = nbchars + len(s)
            if nbchars >= 72:
                sys.stderr.write("\n   ")
                nbchars = 5
        sys.stderr.write("\n")

def usage(code, msg=''):
    "Prints usage for this module."
    sys.stderr.write("%s\n" % __version__)
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s file.seq ...].\n" % sys.argv[0])
    sys.stderr.write("Options: \n")
    sys.stderr.write("     -h, --help      print this help\n")
    sys.exit(code)

def encode_for_xml(s):
    "Encode special chars in string so that it would be XML-compliant."
    s = string.replace(s, '&', '&amp;')
    s = string.replace(s, '<', '&lt;')
    s = re.sub("[\x00-\x19\x7F\x1C\x1D]","",s)     # remove ctrl characters
    #   s = unicode(s,'latin1','ignore').encode('utf-8','replace')
    return s

def main():
    "Main function that does conversion from ALEPH 500 into XML."

    ## read command-line options
    try:
        opts, dummy_args = getopt.getopt(sys.argv[1:], "h", ['help'])
    except getopt.error, msg:
        usage(1, msg)

    help_p = 0           # default is not to print help

    ## guess about desired output format
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            help_p = 1

    ## guess about possible input files
    files = []
    for arg in sys.argv[1:]:
        if arg[0] != "-" and len(arg)>3:
            files.append(arg)

    ## process all the input, finally
    if help_p == 1:
        usage(0)
    else:
        print '<?xml version="1.0" encoding="UTF-8"?>'
        print '<collection xmlns="http://www.loc.gov/MARC21/slim">'
        if files:
            for afile in files:
                try:
                    transform_file(afile)
                except ValueError:
                    print >> sys.stderr, "WARNING: %s skipped" % afile
        else:
            try:
                transform_file("-")
            except ValueError:
                print >> sys.stderr, "WARNING: ignoring input"
        print '</collection>'

    sys.stderr.close()

### okay, here we go:
if __name__ == '__main__':
    main()
