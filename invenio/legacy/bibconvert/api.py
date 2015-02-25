# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

"""BibConvert tool to convert bibliographic records from any format to any format."""

__revision__ = "$Id$"

import fileinput
import string
import os
import re
import sys
from time import strftime, localtime

#FIXME: pu
from invenio.config import CFG_OAI_ID_PREFIX
from invenio.legacy.search_engine import perform_request_search

from .registry import kb

### Matching records with database content


def parse_query_string(query_string):
    """Parse query string, e.g.:
Input: 245__a::REP(-, )::SHAPE::SUP(SPACE, )::MINL(4)::MAXL(8)::EXPW(PUNCT)::WORDS(4,L)::SHAPE::SUP(SPACE, )||700__a::MINL(2)::REP(COMMA,).
Output:[['245__a','REP(-,)','SHAPE','SUP(SPACE, )','MINL(4)','MAXL(8)','EXPW(PUNCT)','WORDS(4,L)','SHAPE','SUP(SPACE, )'],['700__a','MINL(2)','REP(COMMA,)']]
    """

    query_string_out    = []
    query_string_out_in = []

    query_string_split_1 = query_string.split('||')

    for item_1 in query_string_split_1:
        query_string_split_2 = item_1.split('::')
        query_string_out_in = []
        for item in query_string_split_2:
            query_string_out_in.append(item)
        query_string_out.append(query_string_out_in)

    return query_string_out


def set_conv():
    """
    bibconvert common settings
    =======================
    minimal length of output line = 1
    maximal length of output line = 4096
    """

    conv_setting = [
                         1,
                         4096
                   ]

    return conv_setting


def get_pars(fn):
    "Read function and its parameters into list"

    out = []

    out.append(re.split('\(|\)', fn)[0])
    out.append(re.split(',', re.split('\(|\)', fn)[1]))

    return out

def get_other_par(par, cfg):
    "Get other parameter (par) from the configuration file (cfg)"

    out = ""

    other_parameters = {

    '_QRYSTR_' : '_QRYSTR_---.*$',
    '_MATCH_'  : '_MATCH_---.*$',
    '_RECSEP_' : '_RECSEP_---.*$',
    '_EXTCFG_' : '_EXTCFG_---.*$',
    '_SRCTPL_' : '_SRCTPL_---.*$',
    '_DSTTPL_' : '_DSTTPL_---.*$',
    '_RECHEAD_': '_RECHEAD_---.*$',
    '_RECFOOT_': '_RECFOOT_---.*$',
    '_HEAD_'   : '_HEAD_---.*$',
    '_FOOT_'   : '_FOOT_---.*$',
    '_EXT_'    : '_EXT_---.*$',
    '_SEP_'    : '_SEP_---.*$',
    '_COD_'    : '_COD_---.*$',
    '_FRK_'    : '_FRK_---.*$',
    '_NC_'     : '_NC_---.*$',
    '_MCH_'    : '_MCH_---.*$',
    '_UPL_'    : '_UPL_---.*$',
    '_AUTO_'   : '_AUTO_---.*$'

    }

    parameters = other_parameters.keys()

    for line in fileinput.input(cfg):

        pattern   = re.compile(other_parameters[par])
        items     = pattern.findall(line)
        for item in items:
            out  = item.split('---')[1]

    return out


def append_to_output_file(filename, output):
    "bibconvert output file creation by output line"

    try:
        file = open(filename, 'a')
        file.write(output)
        file.close()
    except IOError as e:
        exit_on_error("Cannot write into %s" % filename)

    return 1

def sub_keywd(out):
    "bibconvert keywords literal substitution"


    out = string.replace(out, "EOL", "\n")
    out = string.replace(out, "_CR_", "\r")
    out = string.replace(out, "_LF_", "\n")
    out = string.replace(out, "\\", '\\')
    out = string.replace(out, "\r", '\r')
    out = string.replace(out, "BSLASH", '\\')
    out = string.replace(out, "COMMA", ',')
    out = string.replace(out, "LEFTB", '[')
    out = string.replace(out, "RIGHTB", ']')
    out = string.replace(out, "LEFTP", '(')
    out = string.replace(out, "RIGHTP", ')')

    return out


def check_split_on(data_item_split, sep, tpl_f):
    """
    bibconvert conditional split with following conditions
    ===================================================
    ::NEXT(N,TYPE,SIDE)         - next N chars are of the TYPE having the separator on the SIDE
    ::PREV(N,TYPE,SIDE)         - prev.N chars are of the TYPE having the separator on the SIDE
    """

    fn   = get_pars(tpl_f)[0]
    par  = get_pars(tpl_f)[1]


    done = 0
    while (done == 0):

        if ( (( fn  == "NEXT" ) and ( par[2]=="R" )) or
             (( fn  == "PREV" ) and ( par[2]=="L" )) ):

            test_value = data_item_split[0][-(string.atoi(par[0])):]

        elif ( ((fn  == "NEXT") and ( par[2]=="L")) or
               ((fn  == "PREV") and ( par[2]=="R")) ):

            test_value = data_item_split[1][:(string.atoi(par[0]))]

        data_item_split_tmp = []

        if ((FormatField(test_value, "SUP(" + par[1] + ",)") != "") \
            or (len(test_value) < string.atoi(par[0]))):
            data_item_split_tmp = data_item_split[1].split(sep, 1)

            if(len(data_item_split_tmp)==1):
                done = 1
                data_item_split[0] = data_item_split[0] + sep + \
                                     data_item_split_tmp[0]
                data_item_split[1] = ""
            else:
                data_item_split[0] = data_item_split[0] + sep + \
                                     data_item_split_tmp[0]
                data_item_split[1] = data_item_split_tmp[1]
        else:
            done = 1

    return data_item_split

def get_subfields(data, subfield, src_tpl):
    "Get subfield according to the template"

    out = []

    for data_item in data:
        found = 0
        for src_tpl_item in src_tpl:
            if (src_tpl_item[:2] == "<:"):
                if (src_tpl_item[2:-2] == subfield):
                    found = 1
            else:
                sep_in_list = src_tpl_item.split("::")
                sep = sep_in_list[0]

                data_item_split = data_item.split(sep, 1)

                if (len(data_item_split)==1):
                    data_item = data_item_split[0]
                else:
                    if (len(sep_in_list) > 1):
                        data_item_split = check_split_on(data_item.split(sep, 1),
                                                         sep_in_list[0],
                                                         sep_in_list[1])
                    if(found == 1):
                        data_item = data_item_split[0]
                    else:
                        data_item = string.join(data_item_split[1:], sep)

        out.append(data_item)

    return out

def exp_n(word):
    "Replace newlines and carriage return's from string."

    out = ""

    for ch in word:
        if ((ch != '\n') and (ch != '\r')):
            out = out + ch
    return out

def exp_e(list):
    "Expunge empty elements from a list"

    out = []

    for item in list:
        item = exp_n(item)
        if ((item != '\r\n' and item != '\r' \
             and item != '\n' and item !="" \
             and len(item)!=0)):
            out.append(item)
    return out

def sup_e(word):
    "Replace spaces"

    out = ""

    for ch in word:
        if (ch != ' '):
            out = out + ch
    return out

def select_line(field_code, list):
    "Return appropriate item from a list"

    out = ['']

    for field in list:

        field[0] = sup_e(field[0])
        field_code = sup_e(field_code)

        if (field[0] == field_code):

            out = field[1]

    return out

def parse_field_definition(source_field_definition):
    "Create list of source_field_definition"

    word_list = []
    out       = []
    word      = ""
    counter   = 0

    if (len(source_field_definition.split("---"))==4):
        out = source_field_definition.split("---")

    else:

        element_list_high = source_field_definition.split("<:")
        for word_high in element_list_high:
            element_list_low = word_high.split(':>')
            for word_low in element_list_low:
                word_list.append(word_low)
                word_list.append(":>")
            word_list.pop()
            word_list.append("<:")
        word_list.pop()

        for item in word_list:
            word = word + item
            if (item == "<:"):
                counter = counter + 1
            if (item == ":>"):
                counter = counter - 1

            if counter == 0:
                out.append(word)
                word = ""

    return out


def parse_template(template):
    """
    bibconvert parse template
    ======================
    in                          - template filename
    out                         - [ [ field_code , [ field_template_parsed ] , [] ]
    """
    out       = []

    for field_def in read_file(template, 1):

        field_tpl_new = []

        if ((len(field_def.split("---", 1)) > 1) and (field_def[:1] != "#")):

            field_code = field_def.split("---", 1)[0]
            field_tpl  = parse_field_definition(field_def.split("---", 1)[1])

            field_tpl_new = field_tpl
            field_tpl  = exp_e(field_tpl_new)

            out_data = [field_code, field_tpl]
            out.append(out_data)

    return out

def parse_common_template(template, part):
    """
    bibconvert parse template
    =========================
    in                          - template filename
    out                         - [ [ field_code , [ field_template_parsed ] , [] ]
    """
    out       = []
    counter   = 0

    for field_def in read_file(template, 1):

        if (exp_n(field_def)[:3] == "==="):
            counter = counter + 1

        elif (counter == part):

            field_tpl_new = []
            if ((len(field_def.split("---", 1)) > 1) and (field_def[:1]!="#")):

                field_code = field_def.split("---", 1)[0]
                field_tpl  = parse_field_definition(field_def.split("---", 1)[1])

                field_tpl_new = field_tpl
                field_tpl  = exp_e(field_tpl_new)

                out_data = [field_code, field_tpl]
                out.append(out_data)

    return out

def parse_input_data_f(source_data_open, source_tpl):
    """
    bibconvert parse input data
    ========================
    in                          - input source data location (filehandle)
                                  source data template
                                  source_field_code  list of source field codes
                                  source_field_data  list of source field data values (repetitive fields each line one occurence)
    out                         - [ [ source_field_code , [ source_field_data ] ] , [] ]

    source_data_template entry  - field_code---[const]<:subfield_code:>[const][<:subfield_code:>][]
    destination_templace entry  - [::GFF()]---[const]<:field_code::subfield_code[::FF()]:>[]

    input data file; by line:   - fieldcode  value
    """

    global separator

    out                   = [['', []]]
    count                 = 0
    values                = []


    while (count < 1):

        line = source_data_open.readline()
        if (line == ""):
            return(-1)
        line_split = line.split(" ", 1)

        if (re.sub("\s", "", line) == separator):
            count = count + 1

        if (len(line_split) == 2):

            field_code = line_split[0]
            field_value = exp_n(line_split[1])

            values.append([field_code, field_value])

    item_prev = ""
    stack = ['']

    for item in values:

        if ((item[0]==item_prev)or(item_prev == "")):
            stack.append(item[1])
            item_prev = item[0]
        else:
            out.append([item_prev, stack])
            item_prev = item[0]
            stack = []
            stack.append(item[1])

    try:
        if (stack[0] != ""):
            if (out[0][0]==""):
                out = []
            out.append([field_code, stack])
    except IndexError as e:
        out = out

    return out

def parse_input_data_fx(source_tpl):
    """
    bibconvert parse input data
    ========================
    in                          - input source data location (filehandle)
                                  source data template
                                  source_field_code  list of source field codes
                                  source_field_data  list of source field data values (repetitive fields each line one occurence)
    out                         - [ [ source_field_code , [ source_field_data ] ] , [] ]

    extraction_template_entry   -

    input data file        - specified by extract_tpl
    """

    global separator

    count   = 0
    record  = ""
    field_data_1_in_list = []
    out     = [['', []]]

    while (count <10):
        line = sys.stdin.readline()
        if (line == ""):
            count = count + 1
        if (record == "" and count):
            return (-1)
        if (re.sub("\s", "", line) == separator):
            count = count + 10
        else:
            record = record + line

    for field_defined in extract_tpl_parsed:
        try:
            field_defined[1][0] = sub_keywd(field_defined[1][0])
            field_defined[1][1] = sub_keywd(field_defined[1][1])
        except IndexError as e:
            field_defined = field_defined

        try:
            field_defined[1][2] = sub_keywd(field_defined[1][2])
        except IndexError as e:
            field_defined = field_defined

        field_data_1 =""


        if ((field_defined[1][0][0:2] == '//') and \
            (field_defined[1][0][-2:] == '//')):

            field_defined_regexp = field_defined[1][0][2:-2]

            try:
####
                if (len(re.split(field_defined_regexp, record)) == 1):
                    field_data_1 = ""
                    field_data_1_in_list = []
                else:
                    field_data_1_tmp = re.split(field_defined_regexp, record, 1)[1]
                    field_data_1_in_list = field_data_1_tmp.split(field_defined_regexp)

            except IndexError as e:
                field_data_1 = ""
        else:
            try:
                if (len(record.split(field_defined[1][0])) == 1):
                    field_data_1 = ""
                    field_data_1_in_list = []
                else:
                    field_data_1_tmp = record.split(field_defined[1][0], 1)[1]
                    field_data_1_in_list = field_data_1_tmp.split(field_defined[1][0])
            except IndexError as e:
                field_data_1 = ""

        spliton      = []
        outvalue     = ""
        field_data_2 = ""
        field_data   = ""

        try:
            if ((field_defined[1][1])=="EOL"):
                spliton = ['\n']
            elif ((field_defined[1][1])=="MIN"):
                spliton = ['\n']
            elif ((field_defined[1][1])=="MAX"):
                for item in extract_tpl_parsed:
                    try:
                        spliton.append(item[1][0])
                    except IndexError as e:
                        spliton = spliton
            elif (field_defined[1][1][0:2] == '//') and \
                     (field_defined[1][1][-2:] == '//'):
                spliton = [field_defined[1][1][2:-2]]

            else:
                spliton = [field_defined[1][1]]

        except IndexError as e:
            spliton = ""

        outvalues = []

        for field_data in field_data_1_in_list:
            outvalue = ""

            for splitstring in spliton:

                field_data_2 = ""
                if (len(field_data.split(splitstring))==1):
                    if (outvalue == ""):
                        field_data_2 = field_data
                    else:
                        field_data_2 = outvalue
                else:
                    field_data_2 = field_data.split(splitstring)[0]

                outvalue   = field_data_2
                field_data = field_data_2

            outvalues.append(outvalue)
            outvalues = exp_e(outvalues)

        if (len(outvalues) > 0):
            if (out[0][0]==""):
                out = []

            outstack = []

            if (len(field_defined[1])==3):

                spliton  = [field_defined[1][2]]
                if (field_defined[1][2][0:2] == '//') and \
                       (field_defined[1][2][-2:] == '//'):
                    spliton = [field_defined[1][2][2:-2]]


                for item in outvalues:
                    stack = re.split(spliton[0], item)
                    for stackitem in stack:
                        outstack.append(stackitem)
            else:
                outstack = outvalues

            out.append([field_defined[0], outstack])
    return out


def parse_input_data_d(source_data, source_tpl):
    """
    bibconvert parse input data
    ========================
    in                          - input source data location (directory)
                                  source data template
                                  source_field_code  list of source field codes
                                  source_field_data  list of source field data values (repetitive fields each line one occurence)
    out                         - [ [ source_field_code , [ source_field_data ] ] , [] ]

    source_data_template entry  - field_code---[const]<:subfield_code:>[const][<:subfield_code:>][]
    destination_templace entry  - [::GFF()]---[const]<:field_code::subfield_code[::FF()]:>[]

    input data dir; by file:    - fieldcode value per line
    """

    out = []

    for source_field_tpl in read_file(source_tpl, 1):
        source_field_code = source_field_tpl.split("---")[0]
        source_field_data = read_file(source_data + source_field_code, 0)

        source_field_data = exp_e(source_field_data)

        out_data = [source_field_code, source_field_data]
        out.append(out_data)

    return out


def sub_empty_lines(value):
    out = re.sub('\n\n+', '', value)
    return out

def set_par_defaults(par1, par2):
    "Set default parameter when not defined"

    par_new_in_list = par2.split(",")
    i = 0
    out = []
    for par in par_new_in_list:

        if (len(par1)>i):
            if (par1[i] == ""):
                out.append(par)
            else:
                out.append(par1[i])
        else:
            out.append(par)
        i = i + 1

    return out

def generate(keyword):
    """
    bibconvert generaded values:
    =========================
    SYSNO()                     - generate date as '%w%H%M%S'
    WEEK(N)                     - generate date as '%V' with shift (N)
    DATE(format)                - generate date in specifieddate FORMAT
    VALUE(value)                - enter value literarly
    OAI()                       - generate oai_identifier, starting value given at command line as -o<value>
    """

    out = keyword

    fn  = keyword + "()"

    par = get_pars(fn)[1]
    fn = get_pars(fn)[0]


    par = set_par_defaults(par, "")

    if (fn == "SYSNO"):
        out = sysno500
    if (fn == "SYSNO330"):
        out = sysno
    if (fn == "WEEK"):
        par = set_par_defaults(par, "0")
        out = "%02d" % (string.atoi(strftime("%V", localtime())) \
                        + string.atoi(par[0]))
        if (string.atoi(out)<0):
            out = "00"

    if (fn == "VALUE"):
        par = set_par_defaults(par, "")
        out = par[0]
    if (fn == "DATE"):
        par = set_par_defaults(par, "%w%H%M%S," + "%d" % set_conv()[1])
        out = strftime(par[0], localtime())
        out = out[:string.atoi(par[1])]
    if (fn == "XDATE"):
        par = set_par_defaults(par,"%w%H%M%S," + ",%d" % set_conv()[1])
        out = strftime(par[0], localtime())
        out = par[1] + out[:string.atoi(par[2])]
    if (fn == "OAI"):
        out = "%s:%d" % (CFG_OAI_ID_PREFIX, tcounter + oai_identifier_from)

    return out

def read_file(filename, exception):
    "Read file into list"

    out = []

    if (os.path.isfile(filename)):
        file = open(filename,'r')
        out = file.readlines()
        file.close()
    else:
        if exception:
            exit_on_error("Cannot access file: %s" % filename)
    return out

def crawl_KB(filename, value, mode):
    """
    bibconvert look-up value in KB_file in one of following modes:
    ===========================================================
    1                           - case sensitive     / match  (default)
    2                           - not case sensitive / search
    3                           - case sensitive     / search
    4                           - not case sensitive / match
    5                           - case sensitive     / search (in KB)
    6                           - not case sensitive / search (in KB)
    7                           - case sensitive     / search (reciprocal)
    8                           - not case sensitive / search (reciprocal)
    9                           - replace by _DEFAULT_ only
    R                           - not case sensitive / search (reciprocal) (8) replace
    """

    if (os.path.isfile(filename) != 1):
        # Look for KB in same folder as extract_tpl, if exists
        try:
            pathtmp = string.split(extract_tpl,"/")
            pathtmp.pop()
            path = string.join(pathtmp,"/")
            filename = path + "/" + filename
        except NameError:
            # File was not found. Try to look inside default KB
            # directory
            filename = kb.get(filename, '')

    # FIXME: Remove \n from returned value?
    if (os.path.isfile(filename)):

        file_to_read = open(filename,"r")

        file_read = file_to_read.readlines()
        for line in file_read:
            code = string.split(line, "---")

            if (mode == "2"):
                value_to_cmp   = string.lower(value)
                code[0]        = string.lower(code[0])

                if ((len(string.split(value_to_cmp, code[0])) > 1) \
                    or (code[0]=="_DEFAULT_")):
                    value = code[1]
                    return value

            elif ((mode == "3") or (mode == "0")):
                if ((len(string.split(value, code[0])) > 1) or \
                    (code[0] == "_DEFAULT_")):
                    value = code[1]
                    return value

            elif (mode == "4"):
                value_to_cmp   = string.lower(value)
                code[0]        = string.lower(code[0])
                if ((code[0] == value_to_cmp) or \
                    (code[0] == "_DEFAULT_")):
                    value = code[1]
                    return value

            elif (mode == "5"):
                if ((len(string.split(code[0], value)) > 1) or \
                    (code[0] == "_DEFAULT_")):
                    value = code[1]
                    return value

            elif (mode == "6"):
                value_to_cmp   = string.lower(value)
                code[0]        = string.lower(code[0])
                if ((len(string.split(code[0], value_to_cmp)) > 1) or \
                    (code[0] == "_DEFAULT_")):
                    value = code[1]
                    return value

            elif (mode == "7"):
                if ((len(string.split(code[0], value)) > 1) or \
                    (len(string.split(value,code[0])) > 1) or \
                    (code[0] == "_DEFAULT_")):
                    value = code[1]
                    return value

            elif (mode == "8"):
                value_to_cmp   = string.lower(value)
                code[0]        = string.lower(code[0])
                if ((len(string.split(code[0], value_to_cmp)) > 1) or \
                    (len(string.split(value_to_cmp, code[0])) > 1) or \
                    (code[0] == "_DEFAULT_")):
                    value = code[1]
                    return value

            elif (mode == "9"):
                if (code[0]=="_DEFAULT_"):
                    value = code[1]
                    return value

            elif (mode == "R"):
                value_to_cmp   = string.lower(value)
                code[0]        = string.lower(code[0])
                if ((len(string.split(code[0], value_to_cmp)) > 1) or \
                    (len(string.split(value_to_cmp, code[0])) > 1) or \
                    (code[0] == "_DEFAULT_")):
                    value = value.replace(code[0], code[1])

            else:
                if ((code[0] == value) or (code[0]=="_DEFAULT_")):
                    value = code[1]
                    return value
    else:
        sys.stderr.write("Warning: given KB could not be found. \n")

    return value


def FormatField(value, fn):
    """
    bibconvert formatting functions:
    ================================
    ADD(prefix,suffix)          - add prefix/suffix
    KB(kb_file,mode)            - lookup in kb_file and replace value
    ABR(N,suffix)               - abbreviate to N places with suffix
    ABRX()                      - abbreviate exclusively words longer
    ABRW()                      - abbreviate word (limit from right)
    REP(x,y)                    - replace
    SUP(type)                   - remove characters of certain TYPE
    LIM(n,side)                 - limit to n letters from L/R
    LIMW(string,side)           - L/R after split on string
    WORDS(n,side)               - limit to n words from L/R
    IF(value,valueT,valueF)     - replace on IF condition
    MINL(n)                     - replace words shorter than n
    MINLW(n)                    - replace words shorter than n
    MAXL(n)                     - replace words longer than n
    EXPW(type)                  - replace word from value containing TYPE
    EXP(STR,0/1)                - replace word from value containing string
    NUM()                       - take only digits in given string
    SHAPE()                     - remove extra space
    UP()                        - to uppercase
    DOWN()                      - to lowercase
    CAP()                       - make capitals each word
    SPLIT(n,h,str,from)         - only for final Aleph field, i.e. AB , maintain whole words
    SPLITW(sep,h,str,from)      - only for final Aleph field, split on string
    CONF(filed,value,0/1)       - confirm validity of output line (check other field)
    CONFL(substr,0/1)           - confirm validity of output line (check field being processed)
    CUT(prefix,postfix)         - remove substring from side
    RANGE(MIN,MAX)              - select items in repetitive fields
    RE(regexp)                  - regular expressions
    IFDEFP(field,value,0/1)     - confirm validity of output line (check other field)
                                  NOTE: This function works for CONSTANT
                                  lines - those without any variable values in
                                  them.
    JOINMULTILINES(prefix,suffix) - Given a field-value with newlines in it,
                                    split the field on the new lines (\n), separating
                                    them with prefix, then suffix. E.g.:
                                    For the field XX with the value:
                                       Test
                                       Case, A
                                    And the function call:
                                    <:XX^::XX::JOINMULTILINES(<subfield code="a">,</subfield>):>
                                    The results would be:
                                    <subfield code="a">Test</subfield><subfield code="a">Case, A</subfield>
                                    One note on this: <:XX^::XX:
                                    Without the ^ the newlines will be lost as
                                    bibconvert will remove them, so you'll
                                    never see an effect from this function.


    bibconvert character TYPES
    ==========================
    ALPHA                       - alphabetic
    NALPHA                      - not alpphabetic
    NUM                         - numeric
    NNUM                        - not numeric
    ALNUM                       - alphanumeric
    NALNUM                      - non alphanumeric
    LOWER                       - lowercase
    UPPER                       - uppercase
    PUNCT                       - punctual
    NPUNCT                      - non punctual
    SPACE                       - space
    """

    global data_parsed

    out     = value
    fn      = fn + "()"
    par     = get_pars(fn)[1]
    fn      = get_pars(fn)[0]
    regexp  = "//"
    NRE     = len(regexp)
    value   = sub_keywd(value)
    par_tmp = []

    for item in par:
        item = sub_keywd(item)
        par_tmp.append(item)
    par = par_tmp


    if (fn == "RE"):

        new_value = ""
        par = set_par_defaults(par,".*,0")

        if (re.search(par[0], value) and (par[1] == "0")):
            new_value = value

        out = new_value

    if (fn == "KB"):
        new_value = ""

        par = set_par_defaults(par, "KB,0")

        new_value = crawl_KB(par[0], value, par[1])

        out = new_value

    elif (fn == "ADD"):

        par = set_par_defaults(par, ",")
        out = par[0] + value + par[1]

    elif (fn == "ABR"):
        par = set_par_defaults(par, "1,.")
        out = value[:string.atoi(par[0])] + par[1]

    elif (fn == "ABRW"):

        tmp = FormatField(value, "ABR(1,.)")
        tmp = tmp.upper()
        out = tmp

    elif (fn == "ABRX"):
        par = set_par_defaults(par, ",")
        toout = []
        tmp = value.split(" ")
        for wrd in tmp:

            if (len(wrd) > string.atoi(par[0])):
                wrd = wrd[:string.atoi(par[0])] + par[1]
            toout.append(wrd)
        out = string.join(toout, " ")

    elif (fn == "SUP"):

        par = set_par_defaults(par, ",")

        if(par[0]=="NUM"):
            out = re.sub('\d+', par[1], value)

        if(par[0]=="NNUM"):
            out = re.sub('\D+', par[1], value)

        if(par[0]=="ALPHA"):
            out = re.sub('[a-zA-Z]+', par[1], value)

        if(par[0]=="NALPHA"):
            out = re.sub('[^a-zA-Z]+', par[1], value)

        if((par[0]=="ALNUM") or (par[0] == "NPUNCT")):
            out = re.sub('\w+', par[1], value)

        if(par[0]=="NALNUM"):
            out = re.sub('\W+', par[1], value)

        if(par[0]=="PUNCT"):
            out = re.sub('\W+', par[1], value)


        if(par[0]=="LOWER"):
            out = re.sub('[a-z]+', par[1], value)

        if(par[0]=="UPPER"):
            out = re.sub('[A-Z]+', par[1], value)

        if(par[0]=="SPACE"):
            out = re.sub('\s+', par[1], value)

    elif (fn == "LIM"):
        par = set_par_defaults(par,",")

        if (par[1] == "L"):
            out = value[(len(value) - string.atoi(par[0])):]
        if (par[1] == "R"):
            out = value[:string.atoi(par[0])]

    elif (fn == "LIMW"):
        par = set_par_defaults(par,",")
        if (par[0]!= ""):
            if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
                par[0] = par[0][NRE:-NRE]
                if re.search(par[0], value):
                    par[0] = re.search(par[0], value).group()
                else:
                    par[0] = None
        if par[0]:
            tmp = value.split(par[0], 1) # split into two parts only
            if (par[1] == "L"):
                out = par[0] + tmp[1]
            if (par[1] == "R"):
                out = tmp[0] + par[0]
        else:
            # split by empty par means keep value full
            out = value

    elif (fn == "WORDS"):
        par = set_par_defaults(par, ",")
        words = value.split(" ")
        try:
            max_num_words = int(par[0])
        except ValueError:
            max_num_words = len(words)

        if (par[1] == "L"):
            words.reverse()
            wordlist = words[:max_num_words]
            wordlist.reverse()
        else:
            wordlist = words[:max_num_words]
        out = " ".join(wordlist)

    elif (fn == "MINL"):

        par = set_par_defaults(par, "1")

        tmp = value.split(" ")
        tmp2 = []
        i = 0
        for wrd in tmp:
            if (len(wrd) >= string.atoi(par[0])):
                tmp2.append(wrd)
        out = string.join(tmp2, " ")

    elif (fn == "MINLW"):
        par = set_par_defaults(par, "1")
        if (len(value) >= string.atoi(par[0])):
            out = value
        else:
            out = ""

    elif (fn == "MAXL"):
        par = set_par_defaults(par, "4096")
        tmp = value.split(" ")
        tmp2 = []
        i = 0
        for wrd in tmp:
            if (len(wrd) <= string.atoi(par[0])):
                tmp2.append(wrd)
        out = string.join(tmp2, " ")

    elif (fn == "REP"):
        set_par_defaults(par, ",")
        if (par[0]!= ""):
            if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
                par[0] = par[0][NRE:-NRE]
                out = re.sub(par[0], par[1], value)
            else:
                out = value.replace(par[0], par[1])

    elif (fn == "SHAPE"):

        if (value != ""):
            out = value.strip()

    elif (fn == "UP"):
        out = unicode(value,'utf-8').upper().encode('utf-8')

    elif (fn == "DOWN"):
        out = unicode(value,'utf-8').lower().encode('utf-8')

    elif (fn == "CAP"):
        tmp = value.split(" ")
        out2 = []
        for wrd in tmp:
            wrd2 = wrd.capitalize()
            out2.append(wrd2)
        out = string.join(out2, " ")

    elif (fn == "IF"):
        par = set_par_defaults(par, ",,")

        N = 0
        while N < 3:
            if (par[N][0:NRE] == regexp and par[N][-NRE:] == regexp):
                par[N] = par[N][NRE:-NRE]
                if re.search(par[N], value):
                    par[N] = re.search(par[N], value).group()
            N += 1

        if (value == par[0]):
            out = par[1]
        else:
            out = par[2]
        if (out == "ORIG"):
            out = value

    elif (fn == "EXP"):

        par = set_par_defaults(par, ",0")
        if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
            par[0] = par[0][NRE:-NRE]
            if re.search(par[0], value):
                par[0] = re.search(par[0], value).group()

        tmp = value.split(" ")
        out2 = []
        for wrd in tmp:
            if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
                par[0] = par[0][NRE:-NRE]
                if ((re.search(par[0], wrd).group() == wrd) and \
                    (par[1] == "1")):
                    out2.append(wrd)
                if ((re.search(par[0], wrd).group() != wrd) and \
                    (par[1] == "0")):
                    out2.append(wrd)
            else:
                if ((len(wrd.split(par[0])) == 1) and \
                    (par[1] == "1")):
                    out2.append(wrd)
                if ((len(wrd.split(par[0])) != 1) and \
                    (par[1] == "0")):
                    out2.append(wrd)
        out = string.join(out2," ")

    elif (fn == "EXPW"):

        par = set_par_defaults(par,",0")

        tmp = value.split(" ")
        out2 = []
        for wrd in tmp:
            if ((FormatField(wrd,"SUP(" + par[0] + ")") == wrd) and \
                (par[1] == "1")):
                out2.append(wrd)
            if ((FormatField(wrd,"SUP(" + par[0] + ")") != wrd) and \
                (par[1] == "0")):
                out2.append(wrd)

        out = string.join(out2," ")

    elif fn == "JOINMULTILINES":
        ## Take a string, split it on newlines, and join them together, with
        ## a prefix and suffix for each segment. If prefix and suffix are
        ## empty strings, make suffix a single space.
        prefix = par[0]
        suffix = par[1]
        if prefix == "" and suffix == "":
            ## Values should at least be separated by something;
            ## make suffix a space:
            suffix = " "
        new_value = ""
        vals_list = value.split("\n")
        for item in vals_list:
            new_value += "%s%s%s" % (prefix, item, suffix)

        new_value.rstrip(" ")
        ## Update "out" with the newly created value:
        out = new_value

    elif (fn == "SPLIT"):
        par = set_par_defaults(par, "%d,0,,1" % conv_setting[1])

        length = string.atoi(par[0]) + (string.atoi(par[1]))
        header = string.atoi(par[1])
        headerplus = par[2]
        starting = string.atoi(par[3])

        line = ""
        tmp2 = []
        tmp3 = []
        tmp = value.split(" ")

        linenumber = 1
        if (linenumber >= starting):
            tmp2.append(headerplus)
            line = line + headerplus

        for wrd in tmp:
            line = line + " " + wrd

            tmp2.append(wrd)
            if (len(line) > length):
                linenumber = linenumber + 1
                line = tmp2.pop()
                toout = string.join(tmp2)
                tmp3.append(toout)
                tmp2 = []
                line2 = value[:header]
                if (linenumber >= starting):
                    line3 = line2 + headerplus + line
                else:
                    line3 = line2 + line
                line = line3
                tmp2.append(line)

        tmp3.append(line)
        out = string.join(tmp3, "\n")
        out = FormatField(out, "SHAPE()")

    elif (fn == "SPLITW"):

        par = set_par_defaults(par, ",0,,1")
        if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
            par[0] = par[0][NRE:-NRE]

        stri = re.search(par[0], value)
        if stri:
            stri = stri.group(0)
        else:
            stri = ""
        header = string.atoi(par[1])
        headerplus = par[2]
        starting = string.atoi(par[3])
        counter = 1

        tmp2 = []
        tmp = re.split(par[0], value)

        last = tmp.pop()

        for wrd in tmp:

            counter = counter + 1
            if (counter >= starting):
                tmp2.append(value[:header] + headerplus + wrd + stri)
            else:
                tmp2.append(value[:header] + wrd + stri)
        if (last != ""):
            counter = counter + 1
            if (counter >= starting):
                tmp2.append(value[:header] + headerplus + last)
            else:
                tmp2.append(value[:header] + last)

        out = string.join(tmp2,"\n")

    elif (fn == "CONF"):

        par = set_par_defaults(par, ",,1")

        found = 0
        par1  = ""

        data = select_line(par[0], data_parsed)

        for line in data:
            if (par[1][0:NRE] == regexp and par[1][-NRE:] == regexp):
                par1 = par[1][NRE:-NRE]
            else:
                par1 = par[1]

            if (par1 == ""):
                if (line == ""):
                    found = 1

            elif (len(re.split(par1,line)) > 1 ):
                found = 1

        if ((found == 1) and (string.atoi(par[2]) == 1)):
            out = value
        if ((found == 1) and (string.atoi(par[2]) == 0)):
            out = ""
        if ((found == 0) and (string.atoi(par[2]) == 1)):
            out = ""
        if ((found == 0) and (string.atoi(par[2]) == 0)):
            out = value
        return out

    elif (fn == "IFDEFP"):

        par = set_par_defaults(par, ",,1")

        found = 0
        par1  = ""

        data = select_line(par[0], data_parsed)

        if len(data) == 0 and par[1] == "":
            ## The "found" condition is that the field was empty
            found = 1
        else:
            ## Seeking a value in the field - conduct the search:
            for line in data:
                if (par[1][0:NRE] == regexp and par[1][-NRE:] == regexp):
                    par1 = par[1][NRE:-NRE]
                else:
                    par1 = par[1]

                if (par1 == ""):
                    if (line == ""):
                        found = 1

                elif (len(re.split(par1,line)) > 1 ):
                    found = 1

        if ((found == 1) and (string.atoi(par[2]) == 1)):
            out = value
        if ((found == 1) and (string.atoi(par[2]) == 0)):
            out = ""
        if ((found == 0) and (string.atoi(par[2]) == 1)):
            out = ""
        if ((found == 0) and (string.atoi(par[2]) == 0)):
            out = value
        return out

    elif (fn == "CONFL"):

        set_par_defaults(par,",1")
        if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
            par[0] = par[0][NRE:-NRE]

        if (re.search(par[0], value)):
            if (string.atoi(par[1]) == 1):
                out = value
            else:
                out = ""
        else:
            if (string.atoi(par[1]) == 1):
                out = ""
            else:
                out = value
        return out

    elif (fn == "CUT"):
        par = set_par_defaults(par, ",")
        left  = value[:len(par[0])]
        right = value[-(len(par[1])):]

        if (left == par[0]):
            out = out[len(par[0]):]
        if (right == par[1]):
            out = out[:-(len(par[1]))]

        return out

    elif (fn == "NUM"):
        tmp = re.findall('\d', value)
        out = string.join(tmp, "")

    return out

def format_field(value, fn):
    """
    bibconvert formatting functions:
    ================================
    ADD(prefix,suffix)          - add prefix/suffix
    KB(kb_file,mode)            - lookup in kb_file and replace value
    ABR(N,suffix)               - abbreviate to N places with suffix
    ABRX()                      - abbreviate exclusively words longer
    ABRW()                      - abbreviate word (limit from right)
    REP(x,y)                    - replace
    SUP(type)                   - remove characters of certain TYPE
    LIM(n,side)                 - limit to n letters from L/R
    LIMW(string,side)           - L/R after split on string
    WORDS(n,side)               - limit to n words from L/R
    IF(value,valueT,valueF)     - replace on IF condition
    MINL(n)                     - replace words shorter than n
    MINLW(n)                    - replace words shorter than n
    MAXL(n)                     - replace words longer than n
    EXPW(type)                  - replace word from value containing TYPE
    EXP(STR,0/1)                - replace word from value containing string
    NUM()                       - take only digits in given string
    SHAPE()                     - remove extra space
    UP()                        - to uppercase
    DOWN()                      - to lowercase
    CAP()                       - make capitals each word
    SPLIT(n,h,str,from)         - only for final Aleph field, i.e. AB , maintain whole words
    SPLITW(sep,h,str,from)      - only for final Aleph field, split on string
    CONF(filed,value,0/1)       - confirm validity of output line (check other field)
    CONFL(substr,0/1)           - confirm validity of output line (check field being processed)
    CUT(prefix,postfix)         - remove substring from side
    RANGE(MIN,MAX)              - select items in repetitive fields
    RE(regexp)                  - regular expressions

    bibconvert character TYPES
    ==========================
    ALPHA                       - alphabetic
    NALPHA                      - not alpphabetic
    NUM                         - numeric
    NNUM                        - not numeric
    ALNUM                       - alphanumeric
    NALNUM                      - non alphanumeric
    LOWER                       - lowercase
    UPPER                       - uppercase
    PUNCT                       - punctual
    NPUNCT                      - non punctual
    SPACE                       - space
    """

    global data_parsed

    out     = value
    fn      = fn + "()"
    par     = get_pars(fn)[1]
    fn      = get_pars(fn)[0]
    regexp  = "//"
    NRE     = len(regexp)
    value   = sub_keywd(value)
    par_tmp = []

    for item in par:
        item = sub_keywd(item)
        par_tmp.append(item)
    par = par_tmp


    if (fn == "RE"):

        new_value = ""
        par = set_par_defaults(par, ".*,0")

        if (re.search(par[0], value) and (par[1] == "0")):
            new_value = value

        out = new_value

    if (fn == "KB"):
        new_value = ""

        par = set_par_defaults(par, "KB,0")

        new_value = crawl_KB(par[0], value, par[1])

        out = new_value

    elif (fn == "ADD"):

        par = set_par_defaults(par, ",")
        out = par[0] + value + par[1]

    elif (fn == "ABR"):
        par = set_par_defaults(par, "1,.")
        out = value[:string.atoi(par[0])] + par[1]

    elif (fn == "ABRW"):

        tmp = format_field(value,"ABR(1,.)")
        tmp = tmp.upper()
        out = tmp

    elif (fn == "ABRX"):
        par = set_par_defaults(par, ",")
        toout = []
        tmp = value.split(" ")
        for wrd in tmp:

            if (len(wrd) > string.atoi(par[0])):
                wrd = wrd[:string.atoi(par[0])] + par[1]
            toout.append(wrd)
        out = string.join(toout, " ")

    elif (fn == "SUP"):

        par = set_par_defaults(par, ",")

        if(par[0] == "NUM"):
            out = re.sub('\d+', par[1], value)

        if(par[0] == "NNUM"):
            out = re.sub('\D+', par[1], value)

        if(par[0] == "ALPHA"):
            out = re.sub('[a-zA-Z]+', par[1], value)

        if(par[0] == "NALPHA"):
            out = re.sub('[^a-zA-Z]+', par[1], value)

        if((par[0] == "ALNUM") or (par[0] == "NPUNCT")):
            out = re.sub('\w+', par[1], value)

        if(par[0] == "NALNUM"):
            out = re.sub('\W+', par[1], value)

        if(par[0] == "PUNCT"):
            out = re.sub('\W+', par[1], value)


        if(par[0] == "LOWER"):
            out = re.sub('[a-z]+', par[1], value)

        if(par[0] == "UPPER"):
            out = re.sub('[A-Z]+', par[1], value)

        if(par[0] == "SPACE"):
            out = re.sub('\s+', par[1], value)

    elif (fn == "LIM"):
        par = set_par_defaults(par, ",")

        if (par[1] == "L"):
            out = value[(len(value) - string.atoi(par[0])):]
        if (par[1] == "R"):
            out = value[:string.atoi(par[0])]

    elif (fn == "LIMW"):
        par = set_par_defaults(par, ",")
        if (par[0]!= ""):
            if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
                par[0] = par[0][NRE:-NRE]
                par[0] = re.search(par[0], value).group()
        tmp = value.split(par[0])
        if (par[1] == "L"):
            out = par[0] + tmp[1]
        if (par[1] == "R"):
            out = tmp[0] + par[0]

    elif (fn == "WORDS"):
        tmp2 = [value]
        par = set_par_defaults(par, ",")
        if (par[1] == "R"):
            tmp = value.split(" ")
            tmp2 = []
            i = 0
            while (i < string.atoi(par[0])):
                tmp2.append(tmp[i])
                i = i + 1
        if (par[1] == "L"):
            tmp = value.split(" ")
            tmp.reverse()
            tmp2 = []
            i = 0
            while (i < string.atoi(par[0])):
                tmp2.append(tmp[i])
                i = i + 1
            tmp2.reverse()
        out = string.join(tmp2, " ")

    elif (fn == "MINL"):

        par = set_par_defaults(par, "1")

        tmp = value.split(" ")
        tmp2 = []
        i = 0
        for wrd in tmp:
            if (len(wrd) >= string.atoi(par[0])):
                tmp2.append(wrd)
        out = string.join(tmp2, " ")

    elif (fn == "MINLW"):
        par = set_par_defaults(par, "1")
        if (len(value) >= string.atoi(par[0])):
            out = value
        else:
            out = ""

    elif (fn == "MAXL"):
        par = set_par_defaults(par, "4096")
        tmp = value.split(" ")
        tmp2 = []
        i = 0
        for wrd in tmp:
            if (len(wrd) <= string.atoi(par[0])):
                tmp2.append(wrd)
        out = string.join(tmp2, " ")

    elif (fn == "REP"):
        set_par_defaults(par, ",")
        if (par[0]!= ""):
            if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
                par[0] = par[0][NRE:-NRE]
                out = re.sub(par[0], par[1], value)
            else:
                out = value.replace(par[0], par[1])

    elif (fn == "SHAPE"):

        if (value != ""):
            out = value.strip()

    elif (fn == "UP"):
        out = unicode(value,'utf-8').upper().encode('utf-8')

    elif (fn == "DOWN"):
        out = unicode(value,'utf-8').lower().encode('utf-8')

    elif (fn == "CAP"):
        tmp = value.split(" ")
        out2 = []
        for wrd in tmp:
            wrd2 = wrd.capitalize()
            out2.append(wrd2)
        out = string.join(out2," ")

    elif (fn == "IF"):
        par = set_par_defaults(par,",,")

        N = 0
        while N < 3:
            if (par[N][0:NRE] == regexp and par[N][-NRE:] == regexp):
                par[N] = par[N][NRE:-NRE]
                par[N] = re.search(par[N], value).group()
            N += 1

        if (value == par[0]):
            out = par[1]
        else:
            out = par[2]
        if (out == "ORIG"):
            out = value

    elif (fn == "EXP"):

        par = set_par_defaults(par, ",0")
        if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
            par[0] = par[0][NRE:-NRE]
            if re.search(par[0], value):
                par[0] = re.search(par[0], value).group()

        tmp = value.split(" ")
        out2 = []
        for wrd in tmp:
            if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
                par[0] = par[0][NRE:-NRE]
                if ((re.search(par[0], wrd).group() == wrd) and \
                    (par[1] == "1")):
                    out2.append(wrd)
                if ((re.search(par[0], wrd).group() != wrd) and \
                    (par[1] == "0")):
                    out2.append(wrd)
            else:
                if ((len(wrd.split(par[0])) == 1) and \
                    (par[1] == "1")):
                    out2.append(wrd)
                if ((len(wrd.split(par[0])) != 1) and \
                    (par[1] == "0")):
                    out2.append(wrd)
        out = string.join(out2," ")

    elif (fn == "EXPW"):

        par = set_par_defaults(par,",0")

        tmp = value.split(" ")
        out2 = []
        for wrd in tmp:
            if ((format_field(wrd,"SUP(" + par[0] + ")") == wrd) and \
                (par[1] == "1")):
                out2.append(wrd)
            if ((format_field(wrd,"SUP(" + par[0] + ")") != wrd) and \
                (par[1] == "0")):
                out2.append(wrd)

        out = string.join(out2," ")


    elif (fn == "SPLIT"):
        par = set_par_defaults(par, "%d,0,,1" % conv_setting[1])

        length = string.atoi(par[0]) + (string.atoi(par[1]))
        header = string.atoi(par[1])
        headerplus = par[2]
        starting = string.atoi(par[3])

        line = ""
        tmp2 = []
        tmp3 = []
        tmp = value.split(" ")

        linenumber = 1
        if (linenumber >= starting):
            tmp2.append(headerplus)
            line = line + headerplus

        for wrd in tmp:
            line = line + " " + wrd

            tmp2.append(wrd)
            if (len(line) > length):
                linenumber = linenumber + 1
                line = tmp2.pop()
                toout = string.join(tmp2)
                tmp3.append(toout)
                tmp2 = []
                line2 = value[:header]
                if (linenumber >= starting):
                    line3 = line2 + headerplus + line
                else:
                    line3 = line2 + line
                line = line3
                tmp2.append(line)

        tmp3.append(line)
        out = string.join(tmp3, "\n")
        out = format_field(out, "SHAPE()")

    elif (fn == "SPLITW"):

        par = set_par_defaults(par, ",0,,1")
        if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
            par[0] = par[0][NRE:-NRE]

        str = re.search(par[0], value)

        header = string.atoi(par[1])
        headerplus = par[2]
        starting = string.atoi(par[3])
        counter = 1

        tmp2 = []
        tmp = re.split(par[0], value)

        last = tmp.pop()

        for wrd in tmp:

            counter = counter + 1
            if (counter >= starting):
                tmp2.append(value[:header] + headerplus + wrd + str)
            else:
                tmp2.append(value[:header] + wrd + str)
        if (last != ""):
            counter = counter + 1
            if (counter >= starting):
                tmp2.append(value[:header] + headerplus + last)
            else:
                tmp2.append(value[:header] + last)

        out = string.join(tmp2, "\n")

    elif (fn == "CONF"):

        par = set_par_defaults(par, ",,1")

        found = 0
        par1  = ""

        data = select_line(par[0], data_parsed)

        for line in data:
            if (par[1][0:NRE] == regexp and par[1][-NRE:] == regexp):
                par1 = par[1][NRE:-NRE]
            else:
                par1 = par[1]

            if (par1 == ""):
                if (line == ""):
                    found = 1

            elif (len(re.split(par1,line)) > 1 ):
                found = 1

        if ((found == 1) and (string.atoi(par[2]) == 1)):
            out = value
        if ((found == 1) and (string.atoi(par[2]) == 0)):
            out = ""
        if ((found == 0) and (string.atoi(par[2]) == 1)):
            out = ""
        if ((found == 0) and (string.atoi(par[2]) == 0)):
            out = value

        return out

    elif (fn == "CONFL"):

        set_par_defaults(par,",1")
        if (par[0][0:NRE] == regexp and par[0][-NRE:] == regexp):
            par[0] = par[0][NRE:-NRE]

        if (re.search(par[0], value)):
            if (string.atoi(par[1]) == 1):
                out = value
            else:
                out = ""
        else:
            if (string.atoi(par[1]) == 1):
                out = ""
            else:
                out = value
        return out

    elif (fn == "CUT"):
        par = set_par_defaults(par, ",")
        left  = value[:len(par[0])]
        right = value[-(len(par[1])):]

        if (left == par[0]):
            out = out[len(par[0]):]
        if (right == par[1]):
            out = out[:-(len(par[1]))]

        return out

    elif (fn == "NUM"):
        tmp = re.findall('\d', value)
        out = string.join(tmp, "")

    return out

# Match records with the database content
#

def match_in_database(record, query_string):
    "Check if record is in alreadey in database with an oai identifier. Returns recID if present, 0 otherwise."

    query_string_parsed = parse_query_string(query_string)
    search_pattern = []
    search_field   = []

    for query_field in query_string_parsed:
        ind1 = query_field[0][3:4]
        if ind1 == "_":
            ind1 = ""

        ind2 = query_field[0][4:5]
        if ind2 == "_":
            ind2 = ""

        stringsplit = "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\"><subfield code=\"%s\">" % (query_field[0][0:3], ind1, ind2, query_field[0][5:6])

        formatting = query_field[1:]

        record1 = string.split(record, stringsplit)

        if len(record1) > 1:

            matching_value = string.split(record1[1], "<")[0]

            for fn in formatting:
                matching_value = FormatField(matching_value, fn)

            search_pattern.append(matching_value)

        search_field.append(query_field[0])

    search_field.append("")
    search_field.append("")
    search_field.append("")
    search_pattern.append("")
    search_pattern.append("")
    search_pattern.append("")

    recID_list = perform_request_search(p1=search_pattern[0],
                                        f1=search_field[0],
                                        p2=search_pattern[1],
                                        f2=search_field[1],
                                        p3=search_pattern[2],
                                        f3=search_field[2])


    return recID_list


def exit_on_error(error_message):
    "exit when error occured"

    sys.stderr.write("\n    bibconvert data convertor\n")
    sys.stderr.write("    Error: %s\n" % error_message)
    sys.exit()
    return 0


def create_record(begin_record_header,
                  ending_record_footer,
                  query_string,
                  match_mode,
                  Xcount):
    "Create output record"

    global data_parsed

    out_to_print         = ""
    out                  = []
    field_data_item_LIST = []
    ssn5cnt = "%3d" % Xcount
    sysno                = generate("DATE(%w%H%M%S)")
    sysno500             = generate("XDATE(%w%H%M%S)," + ssn5cnt)



    for T_tpl_item_LIST in target_tpl_parsed:
        # the line is printed only if the variables inside are not empty
        print_line = 0
        to_output = []
        rows      = 1
        for field_tpl_item_STRING in T_tpl_item_LIST[1]:
            save_field_newlines = 0
            DATA = []
            if (field_tpl_item_STRING[:2]=="<:"):
                field_tpl_item_STRING = field_tpl_item_STRING[2:-2]
                field = field_tpl_item_STRING.split("::")[0]
                if (len(field_tpl_item_STRING.split("::")) == 1):
                    value = generate(field)
                    to_output.append([value])
                else:
                    subfield = field_tpl_item_STRING.split("::")[1]
                    if (field[-1] == "*"):
                        repetitive = 1
                        field = field[:-1]
                    elif field[-1] == "^":
                        ## Keep the newlines in a field's value:
                        repetitive = 0
                        save_field_newlines = 1
                        field = field[:-1]
                    else:
                        repetitive = 0
                    if dirmode:
                        DATA    = select_line(field, data_parsed)
                    else:
                        DATA    = select_line(field, data_parsed)

                    if save_field_newlines == 1:
                        ## put newlines back into the element value:
                        DATA = [string.join(DATA, "\n")]
                    elif (repetitive == 0):
                        DATA = [string.join(DATA, " ")]
                    SRC_TPL = select_line(field, source_tpl_parsed)
                    try:
                        ## Get the components that this field is composed of:
                        field_components = field_tpl_item_STRING.split("::")
                        num_field_components = len(field_components)
                        ## Test the number of components. If it is greater that 2,
                        ## some kind of functions must be called on the value of
                        ## the field, and it should therefore be evaluated. If however,
                        ## the field is made-up of only 2 components, (i.e. no functions
                        ## are called on its value, AND the value is empty, do not bother
                        ## to evaluate it.
                        ##
                        ## E.g. In the following line:
                        ## 300---<Pages><:Num::Num:><:Num::Num::IF(,mult. p):></Pages>
                        ##
                        ## If we have a value "3" for page number (Num), we want the following result:
                        ## <Pages>3 p</Pages>
                        ## If however, we have no value for page number (Num), we want this result:
                        ## <Pages>mult. p</Pages>
                        ## The functions relating to the datafield must therefore be executed
                        ##
                        ## If however, the template contains this line:
                        ## 300---<Pages><:Num::Num:></Pages>
                        ##
                        ## If we have a value "3" for page number (Num), we want the following result:
                        ## <Pages>3</Pages>
                        ## If however, we have no value for page number (Num), we do NOT want the line
                        ## to be printed at all - we should SKIP the element and not return an empty
                        ## value (<Pages></Pages> would be pointless.)

                        if (DATA[0] != "" or num_field_components > 2):
                            DATA = get_subfields(DATA, subfield, SRC_TPL)
                            FF = field_tpl_item_STRING.split("::")
                            if (len(FF) > 2):
                                FF = FF[2:]
                                for fn in FF:
#                                    DATAFORMATTED = []
                                    if (len(DATA) != 0):
                                        DATA = get_subfields(DATA, subfield, SRC_TPL)
                                        FF = field_tpl_item_STRING.split("::")
                                        if (len(FF) > 2):
                                            FF = FF[2:]
                                            for fn2 in FF:
                                                DATAFORMATTED = []
                                    for item in DATA:
                                        item = FormatField(item, fn)
                                        if item != "":
                                            DATAFORMATTED.append(item)
                                    DATA = DATAFORMATTED
                            if (len(DATA) > rows):
                                rows = len(DATA)
                            if DATA[0] != "":
                                print_line = 1
                            to_output.append(DATA)
                    except IndexError as e:
                        pass
            else:
                to_output.append([field_tpl_item_STRING])
        current = 0
        default_print = 0
        while (current < rows):
            line_to_print = []
            for item in to_output:
                if (item == []):
                    item = ['']
                if (len(item) <= current):
                    printout = item[0]
                else:
                    printout = item[current]
                line_to_print.append(printout)
            output = exp_n(string.join(line_to_print,""))
            global_formatting_functions = T_tpl_item_LIST[0].split("::")[1:]
            for GFF in global_formatting_functions:
                if (GFF[:5] == "RANGE"):
                    parR       = get_pars(GFF)[1]
                    parR       = set_par_defaults(parR,"MIN,MAX")
                    if (parR[0]!="MIN"):
                        if (string.atoi(parR[0]) > (current+1)):
                            output = ""
                    if (parR[1]!="MAX"):
                        if (string.atoi(parR[1]) < (current+1)):
                            output = ""
                elif (GFF[:6] == "IFDEFP"):
                    ## Like a DEFP and a CONF combined. I.e. Print the line
                    ## EVEN if its a constant, but ONLY IF the condition in
                    ## the IFDEFP is met.
                    ## If the value returned is an empty string, no line will
                    ## be printed.
                    output = FormatField(output, GFF)
                    print_line = 1
                elif (GFF[:4] == "DEFP"):
                    default_print = 1
                else:
                    output = FormatField(output, GFF)

            if ((len(output) > set_conv()[0] and print_line == 1) or default_print):
                out_to_print = out_to_print + output + "\n"

            current = current + 1

###
    out_flag = 0

    if query_string:

        recID = match_in_database(out_to_print, query_string)

        if len(recID) == 1 and match_mode == 1:
            ctrlfield = "<controlfield tag=\"001\">%d</controlfield>" % (recID[0])
            out_to_print = ctrlfield + "\n" + out_to_print
            out_flag = 1

        if len(recID) == 0 and match_mode == 0:
            out_flag = 1

        if len(recID) > 1 and match_mode == 2:
            out_flag = 1


    if out_flag or match_mode == -1:
        if begin_record_header != "":
            out_to_print = begin_record_header + "\n" + out_to_print
        if ending_record_footer != "":
            out_to_print = out_to_print + "\n" + ending_record_footer
    else:
        out_to_print = ""

    return out_to_print


def convert(ar_):

    global dirmode, Xcount, conv_setting, sysno, sysno500, separator, tcounter, source_data, query_string, match_mode, begin_record_header, ending_record_footer, output_rec_sep, begin_header, ending_footer, oai_identifier_from, source_tpl, source_tpl_parsed, target_tpl, target_tpl_parsed, extract_tpl, extract_tpl_parsed, data_parsed

    dirmode, Xcount, conv_setting, sysno, sysno500, separator, tcounter, source_data, query_string, match_mode, begin_record_header, ending_record_footer, output_rec_sep, begin_header, ending_footer, oai_identifier_from, source_tpl, source_tpl_parsed, target_tpl, target_tpl_parsed, extract_tpl, extract_tpl_parsed = ar_
#    separator = spt

    # Added by Alberto
    separator = sub_keywd(separator)

    if dirmode:
        if (os.path.isdir(source_data)):
            data_parsed = parse_input_data_d(source_data, source_tpl)

            record = create_record(begin_record_header, ending_record_footer, query_string, match_mode, Xcount)
            if record != "":
                print record
                tcounter = tcounter + 1
                if output_rec_sep != "":
                    print output_rec_sep
        else:
            exit_on_error("Cannot access directory: %s" % source_data)

    else:
        done = 0
        print begin_header
        while (done == 0):
            data_parsed = parse_input_data_fx(source_tpl)
            if (data_parsed == -1):
                done = 1
            else:
                if (data_parsed[0][0]!= ''):
                    record = create_record(begin_record_header, ending_record_footer, query_string, match_mode, Xcount)
                    Xcount += 1
                    if record != "":
                        print record
                        tcounter = tcounter + 1
                        if output_rec_sep != "":
                            print output_rec_sep
    print ending_footer

    return

