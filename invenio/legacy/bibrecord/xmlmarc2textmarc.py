# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2010, 2011, 2013 CERN.
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

"""Library of functions for the xmlmarc2textmarc utility."""

from __future__ import generators
import getopt, sys
from os.path import basename
from random import randint, seed


from invenio.base.globals import cfg

from invenio.legacy.bibrecord import \
     create_records, \
     record_get_field_values, \
     record_order_fields


# maximum length of an ALEPH MARC record line
CFG_MAXLEN_ALEPH_LINE = 1500


def get_fieldname_changes():
    """Get a dictionary of CDS MARC field names to be replaced
       with ALEPH fieldnames in an ALEPH MARC record.
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
             '970' : 'SYS',
           }


def get_fields_dropped_in_aleph():
    """Get a list of fieldnames to be dropped from an ALEPH MARC record.
       These fields are dropped before the function
       'get_fieldname_changes' is called, so even if they
       appear in the dictionary of field-name changes returned by that
       function, they won't appear in the output Aleph MARC record.
       @return: list [fieldname, fieldname, [...]]
    """
    return [
             '961',
             '970',
             '980',
             'FFT',
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


def get_aleph_OWN():
    """Get an "OWN$$aPUBLIC" string for an ALEPH MARC record, (without
       the SYS prefix).
       @return: string
    """
    return " OWN   L $$aPUBLIC"


def get_aleph_DEL():
    """Get a "DEL$$aY" string for an ALEPH MARC record, (without the
       SYS prefix).
       @return: string
    """
    return " DEL   L $$aY"


def get_aleph_LDR():
    """Get a LDR string for an ALEPH MARC record, (without the SYS prefix).
       @return: string
    """
    return " LDR   L ^^^^^nam^^22^^^^^^a^4500"


def get_aleph_003():
    """Get a 003 string for an ALEPH MARC record, (without the SYS prefix).
       @return: string
    """
    return " 003   L %s" % cfg['CFG_ORGANIZATION_IDENTIFIER']


def get_aleph_008():
    """Get a 008 string for an ALEPH MARC record, (without the SYS prefix).
       @return: string
    """
    return " 008   L ^^^^^^s^^^^^^^^^^^^^^^^r^^^^^000^0^eng^d"


def get_sysno_generator():
    """Create and return a generator for an ALEPH system number.
       The generator will create a 9-digit string, i.e. the sequence
       will end when it reaches 1000000000.
       @return: generator.
    """
    sysno = ""
    seed()
    ## make a 3-digit string for sysno's value:
    for dummy in range(0, 3):
        sysno += str(randint(1, 9))
    sysno = int(sysno)
    while sysno < 1000000000:
        yield """%09d""" % sysno
        sysno = sysno + 1


def create_marc_record(record, sysno, options):
    """Create a text-marc, or aleph-marc record from the contents
       of "record", and return it as a string.
       @param record: Internal representation of an XML MARC
        record, created by bibrecord.
       @param sysno: the system number to be used for the record
       @param options: the options about the MARC record to be created,
        as passed from command line
       @return: string (MARC record, either text-marc or ALEPH marc format,
        depending upon "options".
    """
    out = ""  ## String containing record to be printed
    display_001 = 0  ## Flag used in ALEPH MARC mode to determine whether
                     ## or not to print the "001" field

    ## Get a dictionary containing the names of fields to change for
    ## the output record:
    if options["aleph-marc"] == 1:
        fieldname_changes = get_fieldname_changes()
    else:
        fieldname_changes = {}

    if options["aleph-marc"] == 1:
        ## Perform some ALEPH-MARC specific tasks:
        ## Assume that we will NOT display "001":
        display_001 = 0

        ## Add ALEPH record headers to the output record:
        if 1 not in (options["correct-mode"], options["append-mode"]):
            ## This is not an ALEPH "correct" or "append" record. The
            ## record must therefore have FMT and LDR fields. E.g.:
            ## 123456789 FMT   L BK
            ## 123456789 LDR   L ^^^^^nam^^22^^^^^^a^4500
            out += """%(sys)s%(fmt)s
%(sys)s%(ldr)s\n""" % { 'sys' : sysno,
                       'fmt' : get_aleph_FMT(),
                       'ldr' : get_aleph_LDR()
                     }

        if options["delete-mode"] == 1:
            ## This is an ALEPH 'delete' record. Add the DEL field
            ## then return the 'completed' record (in delete mode,
            ## the record only needs the leaders, and a 'DEL' field, e.g.:
            ## 123456789 FMT   L BK
            ## 123456789 LDR   L ^^^^^nam^^22^^^^^^a^4500
            ## 123456789 DEL   L $$aY
            out += """%(sys)s%(del)s\n""" % { 'sys' : sysno,
                                              'del' : get_aleph_DEL()
                                            }
            return out
        elif 1 in (options["insert-mode"], options["replace-mode"]):
            ## Either an ALEPH 'insert' or 'replace' record is being created.
            ## It needs to have 008 and OWN fields. E.g.:
            ## 123456789 008   L ^^^^^^s^^^^^^^^^^^^^^^^r^^^^^000^0^eng^d
            ## 123456789 OWN   L $$aPUBLIC
            out += """%(sys)s%(008)s\n""" % { 'sys' : sysno,
                                              '008' : get_aleph_008()
                                            }
            ## The "OWN" field should only be printed at this level if the
            ## MARC XML did not have an OWN (963__a) field:
            if "PUBLIC" not in \
               record_get_field_values(record, "963", code="a"):
                ## Add OWN field:
                out += """%(sys)s%(own)s\n""" % { 'sys' : sysno,
                                                  'own' : get_aleph_OWN() }

            if options["replace-mode"] == 1:
                ## In 'replace' mode, the record should have a 001 field:
                display_001 = 1

        ## Remove fields unwanted in ALEPH MARC:
        for deltag in get_fields_dropped_in_aleph():
            try:
                del record[deltag]
            except KeyError:
                ## tag doesn't exist in record:
                pass

    ## now add 001, since it is a special field:
    if options["text-marc"] == 1:
        try:
            ## get the 001 line(s):
            lines_001 = create_field_lines(fieldname="001", \
                                           field=record["001"][0], \
                                           sysno=sysno, \
                                           alephmarc=options["aleph-marc"])
            ## print the 001 line(s):
            out += print_field(field_lines=lines_001, \
                               alephmarc=options["aleph-marc"])
        except KeyError:
            ## no 001 field
            pass
    elif options["aleph-marc"] == 1:
        ## If desirable, build the "001" line:
        if display_001 == 1:
            try:
                ## make the 001 line(s):
                line_leader = """%(sys)s """ % { 'sys' : sysno }
                line_leader += """%(fieldname)s   L """ % { 'fieldname' : "001" }
                lines_001 = [[["", line_leader], ["", sysno]]]
                ## print the 001 line(s):
                out += print_field(field_lines=lines_001, \
                                   alephmarc=options["aleph-marc"])
            except KeyError:
                ## no 001 field
                pass

        ## Now, if running in "insert" or "replace" mode, add "003":
        ## 003 is a mandatory field in an ALEPH record. It contains the
        ## identifier for the organization that has generated the SYS (001)
        ## for the record. As such, it is necessary to drop any existing 003
        ## from the record, then add our own 003.

        ## First, drop the "003" field from the record:
        try:
            del record["003"]
        except KeyError:
            ## There was no 003
            pass

        ## Now add a correct 003 (if desirable):
        if 1 in (options["insert-mode"], options["replace-mode"]):
            out += """%(sys)s%(own)s\n""" % { 'sys' : sysno,
                                              'own' : get_aleph_003() }

    ## delete 001 from the list of fields to output (if it exists):
    try:
        del record["001"]
    except KeyError:
        ## There was no 001
        pass

    ## Get the fields of this record, and order them correctly (using the same
    ## order as that of the original MARC XML file):
    fields = []
    tags = record.keys()
    tags.sort()
    for tag in tags:
        for field in record[tag]:
            fields.append((tag, field))

    ## Finally, loop through all fields and display them in the record:
    for field in fields:
        ## Should the field-name be changed?
        try:
            fieldname = fieldname_changes[str(field[0])]
        except KeyError:
            ## Don't change this fieldname:
            fieldname = field[0]
        ## get the subfields, etc, for this field:
        fielddata = field[1]

        ## Create the MARC lines for this field:
        field_lines = create_field_lines(fieldname, \
                                         fielddata, \
                                         sysno, \
                                         options["aleph-marc"])

        ## Now create the formatted MARC lines:
        out += print_field(field_lines, options["aleph-marc"])
    ## Return the formatted MARC record:
    return out


def print_field(field_lines, alephmarc=0):
    """Create the lines of a record relating to a given field,
       and return these lines as a string.
       @param field_lines: A list of lists, whereby each item in
        the top-level list is an instance of a field
        (e.g. a "datafield" or "controlfield").
       @param alephmarc: an integer flag to tell the function whether
        or not the record being created is a pure text MARC
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
                segment[1] = segment[1].replace(" \n", " ")
                segment[1] = segment[1].replace("\n", " ")
                out += "%(code)s%(value)s" % { 'code' : segment[0],
                                               'value' : segment[1] }
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
                    line[i][1] = line[i][1].replace(" \n", " ")
                    line[i][1] = line[i][1].replace("\n", " ")
                    cur_segment_len = len(line[i][0]) + len(line[i][1])
                    if (line_leader_len + cur_line_len + cur_segment_len + 2 \
                        + len(str(glue_count))) > (CFG_MAXLEN_ALEPH_LINE - 25):
                        ## adding this segment makes the line too long. It
                        ## must be printed now with the ALEPH $$9 glue.
                        ## How much of the current line can be printed?
                        space_remaining = (CFG_MAXLEN_ALEPH_LINE - 25) - \
                                          (line_leader_len + cur_line_len + 3) \
                                          - len(line[i][0])
                        if space_remaining > 0:
                            ## there is space to add some of this line
                            printable_line += line[i][0] + \
                                              line[i][1][0:space_remaining]
                            line[i][1] = line[i][1][space_remaining:]
                        ## print this line:
                        out += """%(sys)s$$9%(glue_count)s""" \
                               """%(printable_line)s\n""" \
                               % { 'sys'            : line[0][1],
                                   'glue_count'     : str(glue_count),
                                   'printable_line' : printable_line,
                                 }
                        ## update glue count, and reset printable line
                        glue_count += 1
                        printable_line = ""
                        cur_line_len = 0
                    else:
                        ## Including this line segment, the line fits within a
                        ## maximum line length, so add it:
                        printable_line += line[i][0] + line[i][1]
                        cur_line_len += (len(line[i][0]) + len(line[i][1]))
                        i += 1

                ## Now add to the display string, any of the line
                ## that remains in printable line:
                if len(printable_line) > 0:
                    if glue_count > 0:
                        out += """%(sys)s$$9%(glue_count)s""" \
                               """%(printable_line)s\n""" \
                               % { 'sys'            : line[0][1],
                                   'glue_count'     : str(glue_count),
                                   'printable_line' : printable_line
                                 }
                    else:
                        out += """%(sys)s%(printable_line)s\n""" \
                               % { 'sys'            : line[0][1],
                                   'printable_line' : printable_line
                                 }
            elif num_linesegments == 1:
                ## strange - only a SYS?
                out += "%(sys)s\n" % { 'sys' : line[0][1] }
    return out


def create_field_lines(fieldname, field, sysno, alephmarc=0):
    """From the internal representation of a field, as pulled from
       a record created by bibrecord, create a list of lists
       whereby each item in the top-level list represents a record
       line that should be created for the field, and each sublist
       represents the various components that make up that line
       (sysno, line label, subfields, etc...)
       @param fieldname: the name for the field (e.g. 001) - string
       @param field: the internal representation of the field, as
        created by bibrecord - list
       @param sysno: the system number to be used for the created
        field - string
       @param alephmarc: a flag telling the function whether a pure
        text MARC or an ALEPH MARC record is being created - int
       @return: list, containing the details of the created field
        lines
    """
    field_lines = []
    field_instance_line_segments = []
    out = """%(sys)s """ % { 'sys' : sysno }
    out += """%(fieldname)s""" % { 'fieldname' : fieldname }
    if alephmarc != 0:
        ## aleph marc record - format indicators properly:
        out += """%(ind1)s%(ind2)s L """ \
               % {
                   'ind1' : (field[1] not in ("", " ") and field[1]) \
                            or ((field[2] not in ("", " ") and "_") or (" ")),
                   'ind2' : (field[2] not in ("", " ") and field[2]) or (" ")
                 }
    else:
        ## text marc record - when empty, indicators should appear as unserscores:
        out += """%(ind1)s%(ind2)s """ \
               % {
                   'ind1' : (field[1] not in ("", " ") and field[1]) or ("_"),
                   'ind2' : (field[2] not in ("", " ") and field[2]) or ("_"),
                 }
    ## append field label to line segments list:
    field_instance_line_segments.append(["", out])
    ## now, loop through the subfields (or controlfield data) and
    ## add each of them to the line data
    subfield_label = ""
    subfield_value = ""
    if len(field[0]) == 0 and field[3] != "":
        ## this is a controlfield
        if fieldname not in ("001", "002", "003", "004", \
                             "005", "006", "007", "008", "009"):
            subfield_label = "$$_"
        else:
            subfield_label = ""
        subfield_value = "%(subfield_value)s" % { 'subfield_value' : field[3] }
        field_instance_line_segments.append([subfield_label, subfield_value])
    else:
        ## this should be a datafield:
        for subfield in field[0]:
            subfield_label = """$$%(subfield_code)s""" \
                             % { 'subfield_code' : subfield[0] }
            subfield_value = """%(subfield_value)s""" \
                             % { 'subfield_value' : subfield[1] }
            field_instance_line_segments.append([subfield_label, \
                                                 subfield_value])
    field_lines.append(field_instance_line_segments)
    return field_lines


def get_sysno_from_record(record, options):
    """Function to get the system number for a record.
       In the case of a pure text MARC record being created, the
       sysno will be retrieved from 001 (i.e. the 'recid' will be returned).
       In the case of an Aleph MARC record being created, the sysno
       will be retrieved from 970__a IF this field exists.  If not,
       None will be returned.
       @param record: the internal representation of the record
        (created by bibrecord) from which the sysno is to be retrieved.
       @param options: various options about the record to be created,
        as obtained from the command line.
       @return: a string containing a 9-digit SYSNO, -OR- None in
       certain cases for an Aleph MARC record.
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
            ## multiple SYS is illegal - return a list of them all,
            ## let other functions decide what to do
            return vals970a
        if len(vals970a) < 1:
            ## no SYS
            sysno = None
        else:
            ## get SYS
            sysno = vals970a[0][0:9]
    return sysno


def recxml2recmarc(xmltext, options, sysno_generator=get_sysno_generator()):
    """The function that processes creating the records from
       an XML string, and prints these records to the
       standard output stream.
       @param xmltext: An XML MARC record in string form.
       @param options: Various options about the record to be
        created, as passed from the command line.
       @param sysno_generator: A static parameter to act as an Aleph
        system number generator. Do not provide a value for this - it
        will be assigned upon first call to this function.
    """
    rec_count = 0  ## Counter used to record the number of the rec
                   ## that is being processed. Used in error messages
                   ## for the user, when a record cannot be processed

    ## create internal records structure from xmltext:
    records = create_records(xmltext, 1, 1)

    ## now loop through each record, get its sysno, and convert it:
    for rec_tuple in records:
        rec_count += 1
        ## Get the record-dictionary itself from the record-tuple:
        record = rec_tuple[0]

        if record is None:
            ## if the record is None, there was probably a problem
            ## with the MARC XML. Display a warning message on stderr and
            ## move past this record:
            sys.stderr.write("E: Unable to process record number %s; The XML " \
                             " may be broken for this record.\n" \
                             % str(rec_count))
            continue

        ## From the record, get the SYS if running in ALEPH-MARC mode, or
        ## the recid (001) if running in TEXT-MARC mode:
        sysno = get_sysno_from_record(record, options)

        if sysno is None:
            ## No 'sysno' was found in the record:
            if options["text-marc"] == 1:
                ## 'sysno' (001) (which is actually the recid) is mandatory
                ## for the creation of TEXT-MARC. Report the error and skip
                ## past the record:
                sys.stderr.write("E: Record number %s has no 'recid' (001). " \
                                 "This field is mandatory for the " \
                                 "creation of TEXT MARC. The record has been " \
                                 "skipped.\n" % str(rec_count))
                continue
            elif options["aleph-marc"] ==  1 and \
                     1 in (options["append-mode"], options["delete-mode"], \
                           options["correct-mode"], options["replace-mode"]):
                ## When creating ALEPH-MARC that will be used to manipulate
                ## a record in some way (i.e. correct, append, delete, replace),
                ## the ALEPH SYS (970__a in MARC XML) is mandatory. Report the
                ## error and skip past the record:
                sys.stderr.write("E: Record number %s has no ALEPH 'SYS' " \
                                 "(970__a). This field is mandatory for the " \
                                 "creation of ALEPH MARC that is used for the" \
                                 " manipulation of records (i.e. replace, " \
                                 "correct, append, delete). The record has " \
                                 "been skipped.\n" % str(rec_count))
                continue
        elif options["aleph-marc"] == 1 and type(sysno) in (list, tuple):
            ## multiple values for SYS (970__a) in ALEPH-MARC mode are not
            ## permitted. Report the error and skip past the record:
            sys.stderr.write("E: Multiple values have been found for the " \
                             "ALEPH SYS (970__a) in record number %s. This " \
                             "is not permitted when running in ALEPH-MARC " \
                             "mode. The record has been skipped." \
                             % str(rec_count))
            continue

        if options["aleph-marc"] == 1 and options["insert-mode"] == 1:
            ## Creating an ALEPH "insert" record. Since the resulting record
            ## should be treated as a new insert into ALEPH, any 'sysno' that
            ## may have been found in the MARC XML record cannot be used -
            ## that would be dangerous. Therefore, set 'sysno' to None and
            ## create a random sysno:
            sysno = None
            try:
                sysno = sysno_generator.next()
            except StopIteration:
                ## generator counter has overstepped the MAX ALEPH SYS!
                ## Without a SYS, we cannot create ALEPH MARC
                sys.stderr.write("""E: Maximum ALEPH SYS has been """ \
                                 """reached - unable to continue.\n""")
                sys.exit(1)


        ## No problems were encountered with SYS or recid. Display the
        ## translated record:
        rec_out = create_marc_record(record, sysno, options)
        sys.stdout.write(rec_out)
        sys.stdout.flush()


def usage(exitcode=1, wmsg=""):
    """Prints usage info."""
    if wmsg:
        sys.stderr.write("Error: %s.\n" % wmsg)

    sys.stderr.write ("""\
Usage: %s [options] marcxml_record_file

Convert an XML MARC record file to text MARC; Print to standard output stream

Command options:
  --text-marc   \t\t\tProduce text MARC output (default)
  --aleph-marc=[a, d, i, c, r]  \tProduce a ALEPH MARC output

  When running in --aleph-marc mode, provide one of the following values:
  \ta  \t\t\t\tCreate an ALEPH "append"  record
  \td  \t\t\t\tCreate an ALEPH "delete"  record
  \ti  \t\t\t\tCreate an ALEPH "insert"  record
  \tc  \t\t\t\tCreate an ALEPH "correct" record
  \tr  \t\t\t\tCreate an ALEPH "replace" record

General options:
  -h, --help   \t\t\t Print this help.
  -V, --version\t\t\t Print version information.
""" % (basename(sys.argv[0]),))

    sys.exit(exitcode)


def get_cli_options():
    """Get the various arguments and options from the command line and populate
       a dictionary of cli_options.
       @return: (tuple) of 2 elements. First element is a dictionary of cli
        options and flags, set as appropriate; Second element is a list of cli
        arguments.
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hV", [
            "help", "version", "text-marc", "aleph-marc="])
    except getopt.GetoptError as err:
        usage(1, err)

    options = { "append-mode"  : 0,
                "insert-mode"  : 0,
                "delete-mode"  : 0,
                "replace-mode" : 0,
                "correct-mode" : 0,
                "aleph-marc"   : 0,
                "text-marc"    : 0
              }

    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            ## Display usage (help) message and exit successfully:
            usage(0)
        elif opt in ["-V", "--version"]:
            ## Display version on stdout and exit successfully:
            sys.stdout.write("%s\n" % __revision__)
            sys.exit(0)
        elif opt == "--aleph-marc":
            ## Running in ALEPH-MARC mode:
            options["aleph-marc"] = 1
            if arg == "a":
                ## Create an ALEPH "APPEND" record:
                options["append-mode"] = 1
            elif arg == "d":
                ## Create an ALEPH "DELETE" record:
                options["delete-mode"] = 1
            elif arg == "i":
                ## Create an ALEPH "INSERT" record:
                options["insert-mode"] = 1
            elif arg == "c":
                ## Create an ALEPH "CORRECT" record:
                options["correct-mode"] = 1
            elif arg == "r":
                ## Create an ALEPH "REPLACE" record:
                options["replace-mode"] = 1
            else:
                ## Invalid option for ALEPH-MARC mode.
                ## Display usage (help) message and exit with failure:
                usage(1)
        elif opt == "--text-marc":
            ## Running in TEXT-MARC mode:
            options["text-marc"] = 1
        else:
            ## Invalid option. Display an error message to the user,
            ## display usage (help) message, and exit with failure:
            sys.stderr.write("Bad option, %s\n" % opt)
            usage(1)

    if options["aleph-marc"] + options["text-marc"] > 1:
        ## User has specified both ALEPH-MARC and TEXT-MARC modes.
        ## This is not permitted, display error message, usage message, and
        ## exit with failure:
        err_msg = "Choose either aleph-marc mode or text-marc mode - not both."
        usage(1, err_msg)
    elif options["aleph-marc"] + options["text-marc"] == 0:
        ## User has not specified whether to run in ALEPH-MARC or TEXT-MARC
        ## mode. Run in the default TEXT-MARC mode.
        options["text-marc"] = 1

    if options["aleph-marc"] == 1:
        ## Running in ALEPH-MARC mode. Conduct some final ALEPH-MODE-specific
        ## checks:
        if options["append-mode"] + options["insert-mode"] \
               + options["delete-mode"] + options["replace-mode"] \
               + options["correct-mode"] != 1:
            ## Invalid option for ALEPH-MARC mode.
            ## Display error message, usage info, and exit with failure.
            err_msg = "A valid mode must be supplied for aleph-marc"
            usage(1, err_msg)

        if 1 in (options["insert-mode"], options["replace-mode"]) and \
           cfg['CFG_ORGANIZATION_IDENTIFIER'].strip() == "":
            ## It is ILLEGAL to create an ALEPH-MARC mode INSERT or
            ## REPLACE record if the organization's identifier is not known.
            ## Write out an error mesage and exit with failure.
            sys.stderr.write("Error: ***cfg['CFG_ORGANIZATION_IDENTIFIER'] IS NOT " \
                             "SET!*** Unable to create ALEPH INSERT or " \
                             "REPLACE records. Please inform your %s" \
                             " Administrator.\n" % cgf['CFG_SITE_NAME'])
            sys.exit(1)

    ## Check that a filename for the MARC XML file was provided:
    if len(args) == 0:
        ## No arguments, therefore no XML file. Display a
        ## usage message, and exit with failure:
        err_msg = ""
        usage(1)

    return (options, args)


def main():
    """Main function."""
    ## process CLI options/arguments:
    (options, args) = get_cli_options()

    ## Read in the XML file and process it:
    xmlfile = args[0]
    ## open file:
    try:
        xmltext = open(xmlfile, 'r').read()
    except IOError:
        sys.stderr.write("Error: File %s not found.\n\n" % xmlfile)
        usage(1)

    ## Process record conversion:
    recxml2recmarc(xmltext=xmltext, options=options)

