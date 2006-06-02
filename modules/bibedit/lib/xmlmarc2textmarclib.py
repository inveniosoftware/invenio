# -*- coding: utf-8 -*-
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

from invenio.bibrecord import create_records, create_record, record_get_field_values
from random import randint, seed
from os.path import basename
from __future__ import generators
import sys

__version__ = "$Id$"

## maximum length of an ALEPH MARC record line
max_line_len = 1500

def get_cds2aleph_changed_fieldnames():
    """Get a dictionary of CDS MARC field names to be replaced with ALEPH fieldnames in an ALEPH
       MARC record.
       @return: dict {'cds_fieldname' : 'replacement_aleph_fieldname',
                      'cds_fieldname' : 'replacement_aleph_fieldname',
                      [...]
                     }
    """
    return {
             '960' : 'BAS',
             '961' : 'CAT',
             '962' : 'LKR',
             '963' : 'OWN',
             '964' : 'ITM',
             '970' : 'SYS'
           }

def get_aleph_dropped_fieldnames():
    """Get a list of fieldnames to be dropped from an ALEPH MARC record.
       @return: list [fieldname, fieldname, [...]]
    """
    return [
             '961',
             '970'
           ]

def get_aleph_001(sysno):
    """Get a 001 string for an ALEPH MARC record, (without the SYS prefix).
       @return: string
    """
    return " 001   L %s" % (sysno,)

def get_aleph_FMT():
    """Get a FMT string for an ALEPH MARC record, (without the SYS prefix).
       @return: string
    """
    return " FMT   L BK"

def get_aleph_DEL():
    """Get a DEL string for an ALEPH MARC record, (without the SYS prefix).
       @return: string
    """
    return " DEL   L $$aY"

def get_aleph_LDR():
    """Get a LDR string for an ALEPH MARC record, (without the SYS prefix).
       @return: string
    """
    return " LDR   L ^^^^^nam^^22^^^^^^a^4500"

def get_aleph_008():
    """Get a 008 string for an ALEPH MARC record, (without the SYS prefix).
       @return: string
    """
    return " 008   L ^^^^^^s^^^^^^^^^^^^^^^^r^^^^^000^0^eng^d"

def _comp_subfieldinstances(x, y):
    """Comparison function, used by sort to sort subfields of a field in a record into ascending
       alphabetical order
    """
    if x[0][0].lower() < y[0][0].lower():
        return -1
    elif x[0][0].lower() == y[0][0].lower():
        return 0
    else:
        return 1

def _comp_datataginstances(x, y):
    """Comparison function, used by sort to sort instances of a field in a record into ascending
       alphabetical order
    """
    if x[1] < y[1]:
        return -1
    elif x[1] == y[1]:
        if x[2] < y[2]:
            return -1
        elif x[2] == y[2]:
            return 0
        else:
            return 1
    else:
        return 1

def get_sysno_generator():
    """Create and return a generator for an ALEPH system number.
       The generator will create a 9-digit string, i.e. it the sequence will
       end when it reaches 1000000000.
       @return: generator.
    """
    sysno = ""
    seed()
    ## make a 3-digit string for sysno's value:
    for i in range(0, 3):
        sysno += str(randint(1,9))
    sysno = int(sysno)
    while sysno < 1000000000:
        yield """%09d""" % (sysno,)
        sysno = sysno + 1

def print_record(record, sysno, options, sysno_generator=get_sysno_generator()):
    """Create a text-marc, or aleph-marc record from the contents of "record", and return it as a string.
       @param record: Internal representation of an XML MARC record, created by bibrecord.
       @param sysno: the system number to be used for the record
       @param options: the options about the MARC record to be created, as passed from command line
       @param sysno_generator: A static parameter to act as an ALEPH system number generator. Do not provide a
        value for this - it will be assigned upon first call to this function.
       @return: string (MARC record, either text-marc or ALEPH marc format, depending upon "options".
    """
    out = ""
    recordfields = record.keys()
    
    ## if ALEPH MARC is to be created:
    if options["aleph-marc"] == 1:
        display_001 = 1
        ## if the SYS is None, make a random SYS
        if sysno is None:
            ## get a value for the sysno:
            try:
                sysno = sysno_generator.next()
            except StopIteration:
                ## generator counter has overstepped the MAX ALEPH SYS!
                sys.stderr.write("""Error: Maximum ALEPH SYS has been reached - unable to continue.\n""")
                sys.exit(1)
            display_001 = 0
        ## ALEPH record headers:
        if 1 not in (options["modify-mode"], options["append-mode"]):
            ## give the record FMT and LDR fields:
            out += """%(sys)s%(fmt)s
%(sys)s%(ldr)s\n""" % { 'sys' : sysno,
                       'fmt' : get_aleph_FMT(),
                       'ldr' : get_aleph_LDR()
                     }
        if options["delete-mode"] == 1:
            ## delete mode - add the DEL field, and return the record, as it is complete:
            out += """%(sys)s%(del)s\n""" % { 'sys' : sysno,
                                              'del' : get_aleph_DEL()
                                            }
            return out
        elif 1 in (options["insert-mode"], options["replace-mode"]):
            ## insert or replace mode - add 008 field:
            out += """%(sys)s%(008)s\n""" % { 'sys' : sysno,
                                              '008' : get_aleph_008()
                                            }
        ## Remove fields unwanted in ALEPH:
        aleph_tagdrop = get_aleph_dropped_fieldnames()
        for deltag in aleph_tagdrop:
            try:
                del recordfields[recordfields.index(deltag)]
            except ValueError:
                ## tag doesn't exist anyway
                pass

    ## now add 001, since it is a special field:
    if options["text-marc"] == 1:
        try:
            ## get the 001 line(s):
            lines_001 = create_field_lines(fieldname="001", field=record["001"], sysno=sysno, alephmarc=options["aleph-marc"])
            ## print the 001 line(s):
            out += print_field(field_lines=lines_001, alephmarc=options["aleph-marc"])
        except KeyError:
            ## no 001 field
            pass
    elif (options["aleph-marc"] == 1 and display_001 == 1 and 1 in (options["insert-mode"], options["replace-mode"])):
        try:
            ## make the 001 line(s):
            line_leader = """%(sys)s """ % { 'sys' : sysno }
            line_leader += """%(fieldname)s   L """ % { 'fieldname' : "001" }
            lines_001 = [[["", line_leader], ["", sysno]]]
            ## print the 001 line(s):
            out += print_field(field_lines=lines_001, alephmarc=options["aleph-marc"])
        except KeyError:
            ## no 001 field
            pass
        
    ## delete 001 from the list of fields to output (if it exists):
    try:
        del recordfields[recordfields.index("001")]
    except ValueError:
        pass

    ## sort recordfields into ascending order:
    recordfields.sort()
    ## convert and display all remaining tags:
    aleph_tagnamechanges = get_cds2aleph_changed_fieldnames()
    for field in recordfields:
        try:
            field_lines = create_field_lines(fieldname=aleph_tagnamechanges[str(field)], field=record[field], sysno=sysno, alephmarc=options["aleph-marc"])
        except KeyError:
            field_lines = create_field_lines(fieldname=field, field=record[field], sysno=sysno, alephmarc=options["aleph-marc"])
        out += print_field(field_lines=field_lines, alephmarc=options["aleph-marc"])

    return out

def print_field(field_lines, alephmarc=0):
    """Create the lines of a record relating to a given field, and return these lines as a string.
       @param field_lines: A list of lists, whereby each item in the top-level list is an instance of a field
        (e.g. a "datafield" or "controlfield").
       @param alephmarc: an integer flag to tell the function whether or not the record being created is a pure text MARC
        record, or an ALEPH MARC record.
       @return: A string containing the record lines for the given field
    """
    if type(field_lines) not in (list, tuple):
        return ""
    out = ""
    if alephmarc == 0:
        ## creating a text-marc record
        for line in field_lines:
            ## create line in text-marc mode:
            for segment in line:
                out += "%(code)s%(value)s" % { 'code' : segment[0], 'value' : segment[1] }
            out += "\n"
    else:
        ## creating an aleph-marc record
        for line in field_lines:
            cur_line_len = 0
            glue_count    = 0
            num_linesegments = len(line)
            if num_linesegments > 1:
                line_leader_len = len(line[0][1])
                printable_line = ""
                i = 1
                while i < num_linesegments:
                    cur_segment_len = len(line[i][0]) + len(line[i][1])
                    if (line_leader_len + cur_line_len + cur_segment_len + 2 + len(str(glue_count))) > (max_line_len - 25):
                        ## adding this segment makes the line too long. It must be printed now with the ALEPH $$9 glue
                        ## how much of the current line can be printed?
                        space_remaining = (max_line_len - 25) - (line_leader_len + cur_line_len + 3) - len(line[i][0])
                        if space_remaining > 0:
                            ## there is space to add some of this line
                            printable_line += line[i][0] + line[i][1][0:space_remaining]
                            line[i][1] = line[i][1][space_remaining:]
                        ## print this line:
                        out += """%(sys)s$$9%(glue_count)s%(printable_line)s\n""" % { 'sys'            : line[0][1],
                                                                                      'glue_count'     : str(glue_count),
                                                                                      'printable_line' : printable_line
                                                                                    }
                        ## update glue count, and reset printable line
                        glue_count += 1
                        printable_line = ""
                        cur_line_len = 0
                    else:
                        ## including this line segment, the line fits within a maximum line length, so add it:
                        printable_line += line[i][0] + line[i][1]
                        cur_line_len += (len(line[i][0]) + len(line[i][1]))
                        i += 1

                ## now add to the display string, any of the line that remains in printable line:
                if len(printable_line) > 0:
                    if glue_count > 0:
                        out += """%(sys)s$$9%(glue_count)s%(printable_line)s\n""" % { 'sys'            : line[0][1],
                                                                                      'glue_count'     : str(glue_count),
                                                                                      'printable_line' : printable_line
                                                                                    }
                    else:
                        out += """%(sys)s%(printable_line)s\n""" % { 'sys'            : line[0][1],
                                                                     'printable_line' : printable_line
                                                                   }
            elif num_linesegments == 1:
                ## strange - only a SYS?
                out += "%(sys)s" % { 'sys' : line[0][1] }
    return out

def create_field_lines(fieldname, field, sysno, alephmarc=0):
    """From the internal representation of a field, as pulled from a record created by bibrecord, create a list of lists
       whereby each item in the top-level list represents a record line that should be created for the field, and each sublist
       represents the various components that make up that line (sysno, line label, subfields, etc...)
       @param fieldname: the name for the field (e.g. 001) - string
       @param field: the internal representation of the field, as created by bibrecord - list
       @param sysno: the system number to be used for the created field - string
       @param alephmarc: a flag telling the function whether a pure text MARC or an ALEPH MARC record is being created - int
       @return: list, containing the details of the created field lines
    """
    field_lines = []
    field.sort(_comp_datataginstances)
    field_line = []
    for field_instance in field:
        field_instance_line_segments = []
        out = """%(sys)s """ % { 'sys' : sysno }
        out += """%(fieldname)s""" % { 'fieldname' : fieldname }
        if alephmarc != 0:
            ## aleph marc record - format indicators properly:
            out += """%(ind1)s%(ind2)s L """ % { 
                                                 'ind1' : (field_instance[1] != "" and field_instance[1]) \
                                                           or ((field_instance[2] != "" and "_") or (" ")),
                                                 'ind2' : (field_instance[2] != "" and field_instance[2]) or (" ")
                                               }
        else:
            ## text marc record - when empty, indicators should appear as unserscores:
            out += """%(ind1)s%(ind2)s """ % {
                                               'ind1' : (field_instance[1] != "" and field_instance[1]) or ("_"),
                                               'ind2' : (field_instance[2] != "" and field_instance[2]) or ("_")
                                             }
        ## append field label to line segments list:
        field_instance_line_segments.append(["", out])
        ## now, loop through the subfields (or controlfield data) and add each of them to the line data
        subfield_label = ""
        subfield_value = ""
        if len(field_instance[0]) == 0 and field_instance[3] != "":
            ## this is a controlfield
            if fieldname != "001":
                subfield_label = "$$_"
            else:
                subfield_label = ""
            subfield_value = "%(subfield_value)s" % { 'subfield_value' : field_instance[3] }
            field_instance_line_segments.append([subfield_label, subfield_value])
        else:
            ## this should be a datafield:
            ## sort the subfields into ascending alphabetical order of subfield code
            field_instance[0].sort(_comp_subfieldinstances)
            for subfield in field_instance[0]:
                subfield_label = """$$%(subfield_code)s""" % { 'subfield_code' : subfield[0] }
                subfield_value = """%(subfield_value)s""" % { 'subfield_value' : subfield[1] }
                field_instance_line_segments.append([subfield_label, subfield_value])
        field_lines.append(field_instance_line_segments)
    return field_lines

def _get_sysno(record, options):
    """Function to get the system number for a record.
       In the case of a pure text MARC record being created, the sysno will be retrieved from 001.
       In the case of an ALEPH MARC record being created, the sysno will be retrieved from 970__a IF
       this field exists.  If not, None will be returned.
       @param record: the internal representation of the record (created by bibrecord) from which the sysno
        is to be retrieved.
       @param options: various options about the record to be created, as obtained from the command line.
       @return: a string containing a 9-digit SYSNO, -OR- None in certai cases for an ALEPH MARC record.
    """
    if options["text-marc"] != 0:
        vals001 = record_get_field_values(rec=record, tag="001")
        if len(vals001) > 1:
            ## multiple values for recid is illegal!
            sysno = None
        elif len(vals001) < 1:
            ## no value for recid is illegal!
            sysno = None
        else:
            ## get recid
            sysno = vals001[0]
            if len(sysno) < 9:
                sysno = "0"*(9-len(sysno)) + sysno
    else:
        vals970a = record_get_field_values(rec=record, tag="970", code="a")
        if len(vals970a) > 1:
            ## multiple SYS is illegal - return a list of them all, let other functions decide what to do
            return vals970a
        if len(vals970a) < 1:
            ## no SYS
            sysno = None
        else:
            ## get SYS
            sysno = vals970a[0][0:9]
    return sysno

def recxml2recmarc(xmltext, options):
    """The function that processes creating the records from an XML string, and prints these records to the
       standard output stream.
       @param xmltext: An XML MARC record in string form.
       @param options: Various options about the record to be created, as passed from the command line.
       @return: Nothing.
    """
    ## create internal record structure from xmltext:
    if xmltext.find("<collection") != -1:
        ## this is a collection of records:
        try:
            ## parse XML into internal records structure
            records = create_records(xmltext, 1, 1)
        except:
            ## xml parsing failed:
            sys.stderr.write("""Error: Unable to parse xml file.\n""")
            sys.exit(1)
        ## now loop through each record, get its sysno, and convert it:
        for record in records:
            sysno = _get_sysno(record=record[0], options=options)
            if sysno is None:
                if options["text-marc"] == 1:
                    ## cannot create text-marc for a record with no 001 (recid)!
                    sys.stderr.write("""Error: Unable to correctly determine recid (001) - record skipped.\n""")
                    continue
                elif options["aleph-marc"] ==  1 and 1 in (options["append-mode"], options["delete-mode"], \
                                                           options["modify-mode"], options["replace-mode"]):
                    ## cannot create ALEPH MARC to manipulate a record when SYS is unknown!
                    sys.stderr.write("""Error: Unable to create a ALEPH MARC to manipulate a record for which SYS is unknown! """\
                                     """Record skipped.\n""")
                    continue
            elif options["aleph-marc"] == 1 and type(sysno) in (list, tuple):
                ## multiple values for SYS in aleph-mode - not permitted
                sys.stderr.write("""Error: Multiple values for SYS (970__a) are not permitted when running in ALEPH MARC mode. """ \
                                 """Record skipped.\n""")
                continue
            sys.stdout.write("""%s""" % (print_record(record=record[0], sysno=sysno, options=options),))
    else:
        ## assuming that this is just a single record - not encapsulated by collection tags:
        try:
            ## parse XML into internal record structure
            (record, st, e) = create_record(xmltext, 1, 1)
        except:
            ## xml parsing failed:
            sys.stderr.write("""Error: Unable to parse xml file.\n""")
            sys.exit(1)
        if record is None:
            ## there was no record:
            sys.stderr.write("""Error: Unable to read record from xml file.\n""")
            sys.exit(1)

        ## now get the sysno for the record:
        sysno = _get_sysno(record=record, options=options)
        if sysno is None:
            if options["text-marc"] == 1:
                ## cannot create text-marc for a record with no 001 (recid)!
                sys.stderr.write("""Error: Unable to correctly determine recid (001) - record skipped.\n""")
                sys.exit(1)
            elif options["aleph-marc"] ==  1 and 1 in (options["append-mode"], options["delete-mode"], \
                                                       options["modify-mode"], options["replace-mode"]):
                ## cannot create ALEPH MARC to manipulate a record when SYS is unknown!
                sys.stderr.write("""Error: Unable to create a ALEPH MARC to manipulate a record for which SYS is unknown! """ \
                                 """Record skipped.\n""")
                sys.exit(1)
        elif options["aleph-marc"] == 1 and type(sysno) in (list, tuple):
            ## multiple values for SYS in aleph-mode - not permitted
            sys.stderr.write("""Error: Multiple values for SYS (970__a) are not permitted when running in ALEPH MARC mode. """ \
                             """Record skipped.\n""")
            sys.exit(1)
        sys.stdout.write("""%s""" % (print_record(record=record, sysno=sysno, options=options),))

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)

    sys.stderr.write ("""\
Usage: %s [options] marcxml_record_file

Convert an XML MARC record file to text MARC; Print to standard output stream

Command options:
  --text-marc   \t\t\tProduce text MARC output (default)
  --aleph-marc=[a, d, i, m, r]  \tProduce a ALEPH MARC output

  When running in --aleph-marc mode, provide one of the following values:
  \ta  \t\t\t\tCreate an "append" ALEPH record
  \td  \t\t\t\tCreate a "delete" ALEPH record
  \ti  \t\t\t\tCreate an "insert" ALEPH record
  \tm  \t\t\t\tCreate a "modify" ALEPH record
  \tr  \t\t\t\tCreate a "replace" ALEPH record

General options:
  -h, --help   \t\t\t Print this help.
  -V, --version\t\t\t Print version information.
""" % (basename(sys.argv[0]),))
    
    sys.exit(exitcode)
