# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2012, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibConvert tool to convert records from any format to any format."""

from __future__ import print_function

__revision__ = "$Id$"

try:
    import string
    import os
    import sys
    import getopt
    import os.path
except ImportError as e:
    sys.stderr.write("Error: %s" % e)
    sys.exit(1)

try:
    from . import api as bibconvert
except ImportError as e:
    sys.stderr.write("Error: %s" % e)
    sys.exit(1)

try:
    from . import xslt_engine as bibconvert_xslt_engine
    from .registry import templates
except ImportError as e:
    sys.stderr.write("Warning: %s" % e)


def usage(exitcode=0, msg=""):
    """Print out when not enough parmeters given."""
    if msg:
        sys.stderr.write(msg)
    else:
        sys.stderr.write("BibConvert data convertor.")

    sys.stderr.write("""
Usage: [options] < input.dat
Examples:
       bibconvert -ctemplate.cfg < input.dat
       bibconvert -ctemplate.xsl < input.xml

 XSL options:
 -c,  --config             transformation stylesheet file

 Plain text-oriented options:
 -c,  --config             configuration template file
 -d,  --directory          source_data fields are located in separated files in 'directory'
 -h,  --help               print this help
 -V,  --version            print version number
 -l,  --length             minimum line length (default = 1)
 -o,  --oai                OAI identifier starts with specified value (default = 1)
 -b,  --header             insert file header
 -e,  --footer             insert file footer
 -B,  --record-header      insert record header
 -E,  --record-footer      insert record footer
 -s,  --separator          record separator, default empty line (EOLEOL)
 -t,  --output_separator

 -m0,  		           match records using query string, output *unmatched*
 -m1,                      match records using query string, output *matched*
 -m2,                      match records using query string, output *ambiguous*

 -Cx,                      alternative to -c when config split to several files, *extraction*
 -Cs,                      alternative to -c when config split to several files, *source*
 -Ct,                      alternative to -c when config split to several files, *target*

 BibConvert can convert:
  - XML data using XSL templates.
  - Plain text data using cfg templates files.

 Plain text-oriented options are not available with .xsl configuration files
""")
    sys.exit(exitcode)


def main():
    """Parse arguments and call bibconvert function."""
    ar_                  = []
    conv_setting         = bibconvert.set_conv()
    sysno                = bibconvert.generate("DATE(%w%H%M%S)")
    sysno500             = bibconvert.generate("DATE(%w%H%M%S)")
    separator            = ""
    tcounter             = 0
    source_data          = ""
    query_string         = ""
    match_mode           = -1
    begin_record_header  = ""
    ending_record_footer = ""
    output_rec_sep       = ""
    begin_header         = ""
    ending_footer        = ""
    oai_identifier_from  = 1
    extract_tpl          = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:],"c:d:hVl:o:b:e:B:E:s:m:C:",
                                   ["config",
                                    "directory",
                                    "help",
                                    "version",
                                    "length",
                                    "oai",
                                    "header",
                                    "footer",
                                    "record-header",
                                    "record-footer",
                                    "separator",
                                    "match",
                                    "config-alt"
                                    ])
    except getopt.GetoptError as err:
        usage(1, "Error: " + str(err))

# get options and arguments

    dirmode = 0
    Xcount = 0

    for opt, opt_value in opts:
        if opt in ["-c", "--config"]:
            if opt_value.endswith('.xsl'):
                pass
            else:
                separator            = bibconvert.get_other_par("_RECSEP_", opt_value)
                output_rec_sep       = ""
                query_string         = bibconvert.get_other_par("_QRYSTR_", opt_value)
                match_mode           = bibconvert.get_other_par("_MATCH_", opt_value)
                begin_header         = bibconvert.get_other_par("_HEAD_", opt_value)
                ending_footer        = bibconvert.get_other_par("_FOOT_", opt_value)
                begin_record_header  = bibconvert.get_other_par("_RECHEAD_", opt_value)
                ending_record_footer = bibconvert.get_other_par("_RECFOOT_", opt_value)
                if(match_mode == ""):
                    match_mode = -1

    for opt, opt_value in opts:
        if opt in ["-c", "--config"]:
            extract_tpl = templates.get(os.path.basename(opt_value), opt_value)
            if opt_value.endswith('.xsl'):
                pass
            else:
                extract_tpl_parsed  = bibconvert.parse_common_template(extract_tpl,1)

                source_tpl  = opt_value
                source_tpl_parsed  = bibconvert.parse_common_template(source_tpl,2)

                target_tpl  = opt_value
                target_tpl_parsed  = bibconvert.parse_common_template(target_tpl,3)

        elif opt in ["-d", "--directory"]:
            source_data       = opt_value
            source_data       = source_data + "/"
            extract_tpl       = "/"
            extract_tpl_parsed = None
            dirmode           = 1

        elif opt in ["-h", "--help"]:
            usage(0)

        elif opt in ["-V", "--version"]:
            print(__revision__)
            sys.exit(0)

        elif opt in ["-l", "--length"]:
            try:
                conv_setting[0] = string.atoi(opt_value)
            except ValueError as e:
                conv_setting[0] = 1

        elif opt in ["-o", "--oai"]:
            try:
                oai_identifier_from = string.atoi(opt_value)
            except ValueError as e:
                oai_identifier_from = 1

        elif opt in ["-b", "--header"]:
            begin_header         = opt_value

        elif opt in ["-e", "--footer"]:
            ending_footer        = opt_value

        elif opt in ["-B", "--record-header"]:
            begin_record_header  = opt_value

        elif opt in ["-E", "--record-footer"]:
            ending_record_footer = opt_value

        elif opt in ["-s", "--separator"]:
            separator            = opt_value

        elif opt in ["-t", "--output_separator"]:
            output_rec_sep       = opt_value

        elif opt in ["-m", "--match"]:
            match_mode           = string.atoi(opt_value[0:1])
            query_string         = opt_value[1:]

        elif opt in ["-C", "--config-alt"]:
            if opt_value[0:1] == "x":
                extract_tpl = templates.get(os.path.basename(opt_value[1:]), opt_value[1:])
                extract_tpl_parsed = bibconvert.parse_template(extract_tpl)
            if opt_value[0:1] == "t":
                target_tpl = templates.get(os.path.basename(opt_value[1:]), opt_value[1:])
                target_tpl_parsed  = bibconvert.parse_template(target_tpl)
            if opt_value[0:1] == "s":
                source_tpl = templates.get(os.path.basename(opt_value[1:]), opt_value[1:])
                source_tpl_parsed  = bibconvert.parse_template(source_tpl)

# Check if required arguments were given
    if(extract_tpl == ""):
        usage(1, "Error: configuration template missing")

    if opt_value.endswith('.xsl'):
        # BibConvert for XSLT
        source_xml = sys.stdin.read()
        try:
            res = bibconvert_xslt_engine.convert(source_xml, extract_tpl)
            if res is not None:
                print(res)
            else:
                sys.exit(1)
        except NameError:
            sys.stderr.write("Error: cannot use BibConvert XSL engine.\n")
            sys.stderr.write("A compliant XML parser is needed. See Invenio INSTALL guide.\n")
            sys.exit(1)
        except Exception as e:
            sys.stderr.write("An error occurred during the conversion.\n")
            sys.stderr.write(str(e))
            sys.exit(1)
    else:
        # BibConvert for cfg

        if(separator == "EOLEOL"):
            separator = ""

        ar_.append(dirmode)
        ar_.append(Xcount)
        ar_.append(conv_setting)
        ar_.append(sysno)
        ar_.append(sysno500)
        ar_.append(separator)
        ar_.append(tcounter)
        ar_.append(source_data)
        ar_.append(query_string)
        ar_.append(match_mode)
        ar_.append(begin_record_header)
        ar_.append(ending_record_footer)
        ar_.append(output_rec_sep)
        ar_.append(begin_header)
        ar_.append(ending_footer)
        ar_.append(oai_identifier_from)
        ar_.append(source_tpl)
        ar_.append(source_tpl_parsed)
        ar_.append(target_tpl)
        ar_.append(target_tpl_parsed)
        ar_.append(extract_tpl)
        ar_.append(extract_tpl_parsed)

        bibconvert.convert(ar_)
