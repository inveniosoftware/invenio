## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibMatch tool to match records with database content."""

__revision__ = "$Id$"

import sys
if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set #for "&" intersection
    # pylint: enable=W0622

import os
import getopt
from tempfile import mkstemp

from invenio.config import CFG_SITE_URL
from invenio.invenio_connector import InvenioConnector
from invenio.bibrecord import create_records, record_get_field_instances, \
    record_get_field_values, record_xml_output, record_modify_controlfield, \
    record_has_field, record_add_field
from invenio import bibconvert
from invenio.dbquery import run_sql
from invenio.textmarc2xmlmarc import transform_file
from invenio.xmlmarc2textmarc import get_sysno_from_record, create_marc_record

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def usage():
    """Print help"""

    print >> sys.stderr, \
    """ Usage: %s [options]

 Options:

 Output:

 -0 --print-new (default) print unmatched in stdout
 -1 --print-match print matched records in stdout
 -2 --print-ambiguous print records that match more than 1 existing records
 -3 --print-fuzzy print records that match the longest words in existing records

 -b --batch-output=(filename). filename.0 will be new records, filename.1 will be matched,
      filename.2 will be ambiguous, filename.3 will be fuzzy match
 -t --text-marc-output transform the output to text-marc format instead of the default MARCXML

 Simple query:

 -f --field=(field)

 Advanced query:

 -c --config=(config-filename)
 -q --query-string=(uploader_querystring)
 -m --mode=(a|e|o|p|r)
 -o --operator=(a|o)

 Where mode is:
  "a" all of the words,
  "o" any of the words,
  "e" exact phrase,
  "p" partial phrase,
  "r" regular expression.

 Operator is:
  "a" and,
  "o" or.

 General options:

 -n   --noprocess          Do not print records in stdout.
 -i,  --input              use a named file instead of stdin for input
 -h,  --help               print this help and exit
 -V,  --version            print version information and exit
 -v,  --verbose=LEVEL      verbose level (from 0 to 9, default 1)
 -r,  --remote=URL         match against a remote invenio installation (URL, no trailing '/')
                           Beware: Only searches public records attached to home collection
 -a,  --alter-recid        The recid (controlfield 001) of matched or fuzzy matched records in
                           output will be replaced by the 001 value of the matched record.
                           Useful to prepare files to then be used with BibUpload.

 Common predefined fields used in querystrings: (for Invenio demo site, your fields may vary!)

 'abstract', 'affiliation', 'anyfield', 'author', 'coden', 'collaboration',
 'collection', 'datecreated', 'datemodified', 'division', 'exactauthor',
 'experiment', 'fulltext', 'isbn', 'issn', 'journal', 'keyword', 'recid',
 'reference', 'reportnumber', 'subject', 'title', 'year'

 Examples:

 $ bibmatch -b -n < input.xml
 $ bibmatch --field=title < input.xml >  unmatched.xml
 $ bibmatch --field=245__a --mode=a < input.xml > unmatched.xml
 $ bibmatch --print-ambiguous --query-string="245__a||author" < input.xml > ambigmatched.xml
 $ bibmatch --print-match -i input.xml -r 'http://cdsweb.cern.ch'
 $ bibmatch -a -1 < input.xml > modified_match.xml
 $ bibmatch [options] < input.xml > unmatched.xml

    """ % sys.argv[0]
    sys.exit(1)

    return

class Querystring:
    "Holds the information about querystring (p1,f1,m1,op1,p2,f2,m2,op2,p3,f3,m3,aas)."

    def __init__(self, mode="1"):
        """Creates querystring instance"""
        self.pattern  = []
        self.field    = []
        self.mode     = []
        self.operator = []
        self.format   = []
        self.pattern.append("")
        self.pattern.append("")
        self.pattern.append("")
        self.field.append("")
        self.field.append("")
        self.field.append("")
        self.mode.append("")
        self.mode.append("")
        self.mode.append("")
        self.operator.append("")
        self.operator.append("")
        self.format.append([])
        self.format.append([])
        self.format.append([])
        return

    def from_qrystr(self, qrystr="", search_mode="eee", operator="aa"):
        """Converts qrystr into querystring (uploader format)"""
        self.default()
        self.field  = []
        self.format = []
        self.mode   = ["e", "e", "e"]
        fields = qrystr.split("||")
        for field in fields:
            tags = field.split("::")
            i = 0
            format = []
            for tag in tags:
                if(i==0):
                    self.field.append(tag)
                else:
                    format.append(tag)
                i += 1
            self.format.append(format)

        while(len(self.format) < 3):
            self.format.append("")

        while(len(self.field) < 3):
            self.field.append("")

        i = 0
        for lett in search_mode:
            self.mode[i] = lett
            i += 1

        i = 0
        for lett in operator:
            self.operator[i] = lett
            i += 1

        return

    def default(self):
        self.pattern  = []
        self.field    = []
        self.mode     = []
        self.operator = []
        self.format   = []
        self.pattern.append("") #default: no pattern
        self.pattern.append("")
        self.pattern.append("")
        self.field.append("245__a") #default: this field
        self.field.append("")
        self.field.append("")
        self.mode.append("") #default: no mode
        self.mode.append("")
        self.mode.append("")
        self.operator.append("")
        self.operator.append("")
        self.format.append([])
        self.format.append([])
        self.format.append([])
        return

    def change_search_mode(self, mode="a"):
        self.mode     = [mode, mode, mode]
        return

    def search_engine_encode(self):
        field_ = []
        for field in self.field:
            i = 0
            field__ = ""
            for letter in field:
                if(letter == "%"):
                    if(i==5):
                        letter = "a"
                    else:
                        letter = "_"
                i += 1
                field__ += str(letter)
            field_.append(field__)
        self.field = field_
        return


def get_field_tags(field):
    "Gets list of field 'field' for the record with 'sysno' system number from the database."

    query = "select tag.value from tag left join field_tag on tag.id=field_tag.id_tag " \
            + "left join field on field_tag.id_field=field.id where field.code='%s'" % (field, )
    out = []
    res = run_sql(query)
    for row in res:
        out.append(row[0])
    return out

def get_subfield(field, subfield):
    "Return subfield of a field."
    for sbf in field:
        if(sbf[0][0][0] == subfield):
            return sbf[0][0][1]

    return ""

def bylen(word1, word2):
    return len(word1) - len(word2)

def main_words_list(wstr):
    """Select the longest words for matching"""
    words = []
    if wstr:
        words = wstr.split()
        words.sort(cmp=bylen)
        words.reverse()
        words = words[:5]
    return words

def match_result_output(recID_list, server_url, qrystr, matchmode="no match"):
    """Generates result as XML comments from passed record and matching parameters.

    @param record: record tuple containing results
    @type record: list

    @param server_url: url to the server the matching has been performed
    @type server_url: str

    @param qrystrs: Querystrings
    @type qrystrs: list of object

    @param matchmode: matching type
    @type matchmode: str

    @rtype str
    @return XML result string
    """
    result = []
    for recID in recID_list:
        result.append("<!-- BibMatch-Matching-Found: %s/record/%s -->" \
                             % (server_url, recID))
    result.append("<!-- BibMatch-Matching-Mode: %s -->" \
                              % (matchmode, ))
    query = []
    for field in qrystr.field:
        if field != "":
            query.append(field)
    result.append("<!-- BibMatch-Matching-Criteria: %s -->" \
                              % ("||".join(query), ))
    return "\n".join(result)

def match_records(records, qrystrs=None, perform_request_search_mode="eee", \
                  operator="a", verbose=1, server_url=CFG_SITE_URL, modify=0):
    """ Match passed records with existing records on a local or remote Invenio
    installation. Returns which records are new (no match), which are matched,
    which are ambiguous and which are fuzzy-matched. A formatted result of each
    records matching are appended to each record tuple:
    (record, status_code, list_of_errors, result)

    @param records: records to analyze
    @type records: list of records

    @param qrystrs: Querystrings
    @type qrystrs: list of object

    @param server_url: which server to search on. Local installation by default
    @type server_url: str

    @param perform_request_search_mode: run the query in this mode
    @type perform_request_search_mode: string

    @param operator: "o" "a"
    @type operator: str

    @param verbose: be loud
    @type verbose: int

    @param modify: output modified records of matches
    @type modify: int

    @rtype: list of lists
    @return an array of arrays of records, like this [newrecs,matchedrecs,
                                                      ambiguousrecs,fuzzyrecs]
    """

    server = InvenioConnector(server_url)

    newrecs = []
    matchedrecs = []
    ambiguousrecs = []
    fuzzyrecs = []

    record_counter = 0
    for rec in records:
        record_counter += 1
        if (verbose > 1):
            sys.stderr.write("\n Processing record: #%d .." % record_counter)

        if qrystrs == None:
            qrystrs = []

        if len(qrystrs)==0:
            qrystrs.append("")

        more_detailed_info = ""

        for qrystr in qrystrs:
            querystring = Querystring()
            querystring.default()

            if(qrystr != ""):
                querystring.from_qrystr(qrystr,
                                        perform_request_search_mode,
                                        operator)
            else:
                querystring.default()

            querystring.search_engine_encode()

            ### get field values for record instance

            inst = []

            ### get appropriate fields from database
            for field in querystring.field:
                tags = get_field_tags(field)
                if len(tags) > 0:
                    # Fetch value from input record of first tag only
                    # FIXME: Extracting more then first tag, evaluating each
                    field = tags[0]
                ### use expanded tags
                tag  = field[0:3]
                ind1 = field[3:4]
                ind2 = field[4:5]
                code = field[5:6]

                if((ind1 == "_")or(ind1 == "%")):
                    ind1 = ""
                if((ind2 == "_")or(ind2 == "%")):
                    ind2 = ""
                if((code == "_")or(code == "%")):
                    code = "a"

                if(field != "001"):
                    finsts = record_get_field_instances(rec[0], tag, ind1, ind2)
                    sbf = get_subfield(finsts, code)
                    inst.append(sbf)
                elif(field in ["001"]):
                    sbf = record_get_field_values(rec[0], field, ind1="",
                                                  ind2="", code="")
                    inst.append(sbf)
                else:
                    inst.append("")


            ### format acquired field values

            i = 0
            for instance in inst:
                for format in querystring.format[i]:
                    inst[i] = bibconvert.FormatField(inst[i], format)
                i += 1

            ### perform the search

            if(inst[0] != ""):
                p1 = inst[0]
                f1 = querystring.field[0]
                m1 = querystring.mode[0]
                op1 = querystring.operator[0]

                p2 = inst[1]
                f2 = querystring.field[1]
                m2 = querystring.mode[1]
                op2 = querystring.operator[1]

                p3 = inst[2]
                f3 = querystring.field[2]
                m3 = querystring.mode[2]

                #1st run the basic perform_req_search
                recID_list = server.search(
                    p1=p1, f1=f1, m1=m1, op1=op1,
                    p2=p2, f2=f2, m2=m2, op2=op2,
                    p3=p3, f3=f3, m3=m3, of='id')

                if (verbose > 8):
                    sys.stderr.write("\nperform_request_search with values"+\
                     " p1="+str(p1)+" f1="+str(f1)+" m1="+str(m1)+" op1="+str(op1)+\
                     " p2="+str(p2)+" f2="+str(f2)+" m2="+str(m2)+" op2="+str(op2)+\
                     " p3="+str(p3)+" f3="+str(f3)+" m3="+str(m3)+\
                     " result="+str(recID_list)+"\n")

                if len(recID_list) > 1: #ambig match
                    ambiguousrecs.append(rec + (match_result_output(recID_list, \
                                                server_url, querystring, "ambiguous-matched"), ))
                    if (verbose > 8):
                        sys.stderr.write("ambiguous\n")
                if len(recID_list) == 1: #match
                    if modify:
                        if record_has_field(rec[0], '001'):
                            record_modify_controlfield(rec[0], '001', \
                                                       controlfield_value=str(recID_list[0]), \
                                                       field_position_global=1)
                        else:
                            record_add_field(rec[0], '001', controlfield_value=str(recID_list[0]))
                    matchedrecs.append(rec + (match_result_output(recID_list, \
                                                server_url, querystring, "exact-matched"), ))
                    if (verbose > 8):
                        sys.stderr.write("match\n")
                if len(recID_list) == 0: #no match..
                    #try fuzzy matching
                    intersected = None
                    #check if all the words appear in the
                    #field of interest
                    words1 = main_words_list(p1)
                    words2 = main_words_list(p2)
                    words3 = main_words_list(p3)

                    for word in words1:
                        word = "'"+word+"'"
                        ilist = server.search(p=word, f=f1, of="id")
                        if (verbose > 8):
                            sys.stderr.write("fuzzy perform_request_search with values"+\
                                             " p="+str(word)+" f="+str(f1)+" res "+str(ilist)+"\n")
                        if intersected == None:
                            intersected = ilist
                        intersected =  list(set(ilist)&set(intersected))

                    for word in words2:
                        word = "'"+word+"'"
                        ilist = server.search(p=word, f=f2, of="id")
                        if (verbose > 8):
                            sys.stderr.write("fuzzy perform_request_search with values"+\
                                             " p="+str(word)+" f="+str(f2)+" res "+str(ilist)+"\n")
                        if intersected == None:
                            intersected = ilist
                        intersected =  list(set(ilist)&set(intersected))

                    for word in words3:
                        word = "'"+word+"'"
                        ilist = server.search(p=word, f=f3, of="id")
                        if (verbose > 8):
                            sys.stderr.write("fuzzy perform_request_search with values"+\
                                             " p="+str(word)+" f="+str(f3)+" res "+str(ilist)+"\n")
                        if intersected == None:
                            intersected = ilist
                        intersected =  list(set(ilist)&set(intersected))

                    if intersected:
                        #this was a fuzzy match
                        if modify:
                            if record_has_field(rec[0], '001'):
                                record_modify_controlfield(rec[0], '001', \
                                      controlfield_value=str(intersected[0]), field_position_global=1)
                            else:
                                record_add_field(rec[0], '001', controlfield_value=str(intersected[0]))
                        fuzzyrecs.append(rec + (match_result_output(intersected, \
                                                server_url, querystring, "fuzzy-matched"), ))
                        if (verbose > 8):
                            sys.stderr.write("fuzzy\n")
                    else:
                        #no match
                        newrecs.append(rec + (match_result_output(recID_list, \
                                                server_url, querystring), ))
                        if (verbose > 8):
                            sys.stderr.write("new\n")
    #return results
    return [newrecs, matchedrecs, ambiguousrecs, fuzzyrecs]

def transform_input_to_marcxml(filename, file_input=""):
    """ Takes the filename or input of text-marc and transforms it
    to MARCXML. """
    if not filename:
        # Create temporary file to read from
        tmp_fd, filename = mkstemp()
        os.write(tmp_fd, file_input)
        os.close(tmp_fd)
    try:
        # Redirect output, transform, restore old references
        old_stdout = sys.stdout
        new_stdout = StringIO()
        sys.stdout = new_stdout

        transform_file(filename)
    finally:
        sys.stdout = old_stdout
    return new_stdout.getvalue()

def main():
    """ Record matches database content when defined search gives
    exactly one record in the result set. By default the match is
    done on the title field.
    Using advanced search only 3 fields can be queried concurrently
    qrystr - querystring in the UpLoader format. """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "0123hVFm:q:c:nv:o:b:i:r:ta",
                 [
                   "print-new",
                   "print-match",
                   "print-ambiguous",
                   "print-fuzzy",
                   "help",
                   "version",
                   "mode=",
                   "field=",
                   "query-string=",
                   "config=",
                   "no-process",
                   "verbose=",
                   "operator=",
                   "batch-output=",
                   "input=",
                   "remote=",
                   "text-marc-output",
                   "alter-recid"
                 ])

    except getopt.GetoptError, e:
        usage()
    match_results = []
    qrystrs     = []                #query strings
    print_mode  = 0                 # default match mode to print new records
    noprocess   = 0
    perform_request_search_mode = "eee"
    operator    = "aa"
    verbose     = 1                 # 0..be quiet
    file_read   = ""                #input buffer
    records     = []
    batch_output = ""               #print stuff in files
    f_input = ""                    #read from where, if param "i"
    server_url = CFG_SITE_URL       #url to server performing search, local by default
    modify = 0                      #alter output with matched record identifiers
    textmarc_output = 0

    for opt, opt_value in opts:
        if opt in ["-0", "--print-new"]:
            print_mode = 0
        if opt in ["-1", "--print-match"]:
            print_mode = 1
        if opt in ["-2", "--print-ambiguous"]:
            print_mode = 2
        if opt in ["-3", "--print-fuzzy"]:
            print_mode = 3
        if opt in ["-n", "--no-process"]:
            noprocess = 1
        if opt in ["-h", "--help"]:
            usage()
            sys.exit(0)
        if opt in ["-V", "--version"]:
            print __revision__
            sys.exit(0)
        if opt in ["-F", "--fuzzy"]:
            fuzzy = 1
        if opt in ["-t", "--text-marc-output"]:
            textmarc_output = 1
        if opt in ["-v", "--verbose"]:
            verbose = int(opt_value)
        if opt in ["-q", "--query-string"]:
            qrystrs.append(opt_value)
        if opt in ["-m", "--mode"]:
            perform_request_search_mode = opt_value
        if opt in ["-o", "--operator"]:
            operator         = opt_value
        if opt in ["-b", "--batch-output"]:
            batch_output     = opt_value
        if opt in ["-i", "--input"]:
            f_input     = opt_value
        if opt in ["-r", "--remote"]:
            server_url = opt_value
        if opt in ["-a", "--alter-recid"]:
            modify = 1
        if opt in ["-f", "--field"]:
            alternate_querystring = get_field_tags(opt_value)
            if len(alternate_querystring) > 0:
                for item in alternate_querystring:
                    qrystrs.append(item)
            else:
                qrystrs.append(opt_value)
        if opt in ["-c", "--config"]:
            config_file      = opt_value
            config_file_read = bibconvert.read_file(config_file, 0)
            for line in config_file_read:
                tmp = line.split("---")
                if(tmp[0] == "QRYSTR"):
                    qrystrs.append(tmp[1])

    if verbose:
        sys.stderr.write("\nBibMatch: Parsing input file "+f_input+"... ")

    if not f_input:
        for line_in in sys.stdin:
            file_read += line_in
    else:
        f = open(f_input)
        for line_in in f:
            file_read += line_in
        f.close()

    # Detect input type
    if not file_read.startswith('<'):
        # Not xml, assume type textmarc
        file_read = transform_input_to_marcxml(f_input, file_read)

    records = create_records(file_read)

    if len(records) == 0:
        if verbose:
            sys.stderr.write("\nBibMatch: Input file contains no records.\n")
        sys.exit()
    else:
        if verbose:
            sys.stderr.write("read %d records" % len(records))
            sys.stderr.write("\nBibMatch: Matching ...")
        match_results = match_records(records,
                                      qrystrs,
                                      perform_request_search_mode,
                                      operator,
                                      verbose,
                                      server_url,
                                      modify)
    # set the output according to print..
    # 0-newrecs 1-matchedrecs 2-ambiguousrecs 3-fuzzyrecs
    recs_out = match_results[print_mode]

    if verbose:
        sys.stderr.write("\n\n Bibmatch report\n")
        sys.stderr.write("=" * 35)
        sys.stderr.write("\n New records         : %d" % len(match_results[0]))
        sys.stderr.write("\n Matched records     : %d" % len(match_results[1]))
        sys.stderr.write("\n Ambiguous records   : %d" % len(match_results[2]))
        sys.stderr.write("\n Fuzzy records       : %d\n" % len(match_results[3]))
        sys.stderr.write("=" * 35)
        sys.stderr.write("\n Total records       : %d\n" % len(records))

    if not noprocess:
        options = {'text-marc':1, 'aleph-marc':0}
        for record in recs_out:
            if textmarc_output:
                sysno = get_sysno_from_record(record[0], options)
                print create_marc_record(record[0], sysno, options)
            else:
                print record[3]
                print record_xml_output(record[0])

    if batch_output:
        i = 0
        options = {'text-marc':1, 'aleph-marc':0}
        for result in match_results:
            filename = "%s.%i" % (batch_output, i)
            file_fd = open(filename,"w")
            for record in result:
                out = ""
                if textmarc_output:
                    sysno = get_sysno_from_record(record[0], options)
                    out += create_marc_record(record[0], sysno, options)
                else:
                    out += record[3]
                    out += record_xml_output(record[0])
                file_fd.write(out + '\n')
            file_fd.close()
            i += 1
