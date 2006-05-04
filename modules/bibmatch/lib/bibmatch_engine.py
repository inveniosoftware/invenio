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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibMatch tool to match records with database content."""

__version__ = "$Id$"

try:
    import fileinput
    import string
    import os
    import sys
    import getopt
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)
try:
    from invenio.search_engine import perform_request_search
    from invenio.config import *
    from invenio.bibrecord import *
    from invenio import bibconvert
    from invenio.dbquery import run_sql
except ImportError, e:
    print "Error: %s" % e
    sys.exit(1)

def usage():
    """Print help"""

    print >> sys.stderr, \
    """ Usage: %s [options]

 Examples:

 $ bibmatch [--print-new] --field=\"title\" < input.xml > output.xml
 $ bibmatch --print-match --field=\"245__a\" --mode=\"a\" < input.xml > output.xml
 $ bibmatch --print-ambiguous --query-string=\"245__a||100__a\" < input.xml > output.xml

 $bibmatch [options] < input.xml > output.xml

 Options:

 Output:

 -0 --print-new (default)
 -1 --print-match
 -2 --print-ambiguous
 -b --batch-output=(filename)

 Simple query:

 -f --field=(field)

 Advanced query:

 -c --config=(config-filename)
 -q --query-string=(uploader_querystring)
 -m --mode=(a|e|o|p|r)[3]
 -o --operator=(a|o)[2]

 General options:

 -h,  --help               print this help and exit
 -V,  --version            print version information and exit
 -v,  --verbose=LEVEL      verbose level (from 0 to 9, default 1)

    """ % sys.argv[0]
    sys.exit(1)

    return

class Querystring:
    "Holds the information about querystring (p1,f1,m1,op1,p2,f2,m2,op2,p3,f3,m3,as)."

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
        self.advanced = 0
        return

    def from_qrystr(self, qrystr="", search_mode="eee", operator="aa"):
        """Converts qrystr into querystring (uploader format)"""

        self.default()
        self.field  = []
        self.format = []
        self.mode   = ["e","e","e"]
        fields = string.split(qrystr,"||")
        for field in fields:
            tags =  string.split(field, "::")
            i = 0
            format = []
            for tag in tags:
                if(i==0):
                    self.field.append(tag)
                else:
                    format.append(tag)
                i +=1
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
        self.pattern.append("")
        self.pattern.append("")
        self.pattern.append("")
        self.field.append("245__a")
        self.field.append("")
        self.field.append("")
        self.mode.append("a")
        self.mode.append("")
        self.mode.append("")
        self.operator.append("")
        self.operator.append("")
        self.format.append([])
        self.format.append([])
        self.format.append([])
        self.advanced = 1
        return

    def change_search_mode(self, mode="a"):
        self.mode     = [mode,mode,mode]
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
                i+=1
                field__ = "%s%s" % (field__,letter)
            field_.append(field__)
        self.field = field_    
        return


def get_field_tags(field):
    "Gets list of field 'field' for the record with 'sysno' system number from the database."

    query = "select tag.value from tag left join field_tag on tag.id=field_tag.id_tag left join field on field_tag.id_field=field.id where field.code='%s'" % field;
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

def matched_records(recID_lists):
    "Analyze list of matches. Ambiguous record result is always preferred."

    recID_tmp = []

    for recID_list in recID_lists:
        if(len(recID_list) > 1):
            return 2
        if(len(recID_list) == 1):
            if(len(recID_tmp) == 0):
                recID_tmp.append(recID_list[0])
            else:
                if(recID_list[0] in recID_tmp):
                    pass
                else:
                    return 2

    if(len(recID_tmp) == 1):
        return 1

    return 0

def matched_records_min(recID_lists):
    "Analyze lists of matches. New record result is preferred if result is unmatched."

    min = 2

    for recID_list in recID_lists:
        if(len(recID_list) < min):
            min = len(recID_list)
        if(min==1):
            return min
    return min

def matched_records_max(recID_lists):
    "Analyze lists of matches. Ambiguous result is preferred if result is unmatched."

    max = 0
    
    for recID_list in recID_lists:
        if(len(recID_list) == 1):
            return 1
        if(len(recID_list) > max):
            max = len(recID_list)

    if (max > 1):
        return 2
    elif (max == 1):
        return 1
    else:
        return 0
    return 2

def main():
    # Record matches database content when defined search gives exactly one record in the result set.
    # By default the match is done on the title field.
    # Using advanced search only 3 fields can be queried concurrently
    # qrystr - querystring in the UpLoader format
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"012hVm:f:q:c:nv:o:b:",
                 [
                   "print-new",
                   "print-match",
                   "print-ambiguous",
                   "help",
                   "version",
                   "mode=",
                   "field=",
                   "query-string=",
                   "config=",
                   "no-process",
                   "verbose=",
                   "operator=",
                   "batch-output="
                 ])
    
    except getopt.GetoptError, e:
            usage()
    
    recs_out    = []
    recID_list  = []
    recID_lists = []
    qrystrs     = []
    match_mode  = 0                 # default match mode to print new records
    rec_new     = 0                 # indicator that record is new
    rec_match   = 0                 # indicator that record is matched
    matched     = 0                 # number of records matched
    record_counter = 0              # number of records processed
    noprocess   = 0
    result      = [0,0,0]
    perform_request_search_mode = "eee"
    operator    = "aa"
    verbose     = 1                 # 0..be quiet
    level       = 1                 # 1..exact match
    file_read   = ""
    records     = []
    batch_output = ""
    predefined_fields = ["title", "author"]
    
    
    for opt, opt_value in opts:
    
        if opt in ["-0", "--print-new"]:
            match_mode = 0
        if opt in ["-1", "--print-match"]:
            match_mode = 1
        if opt in ["-2", "--print-ambiguous"]:
            match_mode = 2
        if opt in ["-n", "--no-process"]:
            noprocess = 1
        if opt in ["-h", "--help"]:
            usage()
            sys.exit(0)
        if opt in ["-V", "--version"]:
            print __version__
            sys.exit(0)
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
        if opt in ["-f", "--field"]: 
            alternate_querystring = []
            if opt_value in predefined_fields:
                alternate_querystring = get_field_tags(opt_value)
                for item in alternate_querystring:
                    qrystrs.append(item)
            else:
                qrystrs.append(opt_value)
        if opt in ["-c", "--config"]:
            config_file      = opt_value
            config_file_read = bibconvert.read_file(config_file, 0)
            for line in config_file_read:
                tmp = string.split(line, "---")
                if(tmp[0] == "QRYSTR"):
                    qrystrs.append(tmp[1])
                    
    if verbose:
        sys.stderr.write("\nBibMatch: Parsing input file ... ")
        
    for line_in in sys.stdin:
        file_read += line_in
    
    records = create_records(file_read)
    
    if len(records) == 0:
        if verbose:
            sys.stderr.write("\nBibMatch: Input file contains no records.\n")
        sys.exit()
    else:
        if verbose:
            sys.stderr.write("read %d records" % len(records))
            sys.stderr.write("\nBibMatch: Matching ...")
    
    ### Prepare batch output
    
        if (batch_output != ""):
            out_0 = []
            out_1 = []
            out_2 = []
    
        for rec in records:
    
    ### for each query-string
    
            record_counter += 1
    
            if (verbose > 1):
                
                sys.stderr.write("\n Processing record: #%d .." % record_counter)
    
            recID_lists = []
    
            if(len(qrystrs)==0):
                qrystrs.append("")
    
            more_detailed_info = ""
    
            for qrystr in qrystrs:
    
                querystring = Querystring()
                querystring.default()
    
                if(qrystr != ""):
                    querystring.from_qrystr(qrystr, perform_request_search_mode, operator)
                else:
                    querystring.default()
    
    
    ### search engine qrystr encode
    
                querystring.search_engine_encode()
    
    ### get field values
    
                inst = []
    
                ### get appropriate corresponding fields from database
    
                i = 0
                for field in querystring.field:
    
    
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
                        sbf = get_subfield(record_get_field_instances(rec[0], tag, ind1, ind2), code)
                        inst.append(sbf)
                    elif(field in ["001"]):
                        sbf = record_get_field_values(rec[0], field, ind1="", ind2="", code="")
                        inst.append(sbf)
                    else:
                        inst.append("")
                    i += 1
    
    ### format acquired field values
    
                i = 0
                for instance in inst:
                    for format in querystring.format[i]:
                        inst[i] = bibconvert.FormatField(inst[i],format)
                    i += 1
    
    ### perform sensible request search only
    
                if(inst[0]!=""):
                    recID_list = perform_request_search(
                          p1=inst[0], f1=querystring.field[0], m1=querystring.mode[0], op1=querystring.operator[0],
                          p2=inst[1], f2=querystring.field[1], m2=querystring.mode[1], op2=querystring.operator[1],
                          p3=inst[2], f3=querystring.field[2], m3=querystring.mode[2], as=querystring.advanced)
                else:
                    recID_list = []

                recID_lists.append(recID_list)

    ### more detailed info ...
    
                if(verbose > 8):
                    more_detailed_info = "%s\n  Matched recIDs: %s" % (more_detailed_info, recID_lists)
                if(verbose > 2):
                    more_detailed_info = "%s\n  On query: %s, %s, %s, %s\n            %s, %s, %s, %s\n            %s, %s, %s\n" % (more_detailed_info, inst[0], querystring.field[0], querystring.mode[0], querystring.operator[0], inst[1], querystring.field[1], querystring.mode[1], querystring.operator[1], inst[2], querystring.field[2], querystring.mode[2])
    

    ### for multitagged fields (e.g. title), unmatched result corresponds to the item in extreme
            rec_match = matched_records_max(recID_lists)
    
    ### print-new
    
            if (rec_match==0):
                result[0] += 1
                if(match_mode==0):
                    recs_out.append(rec)
                if (batch_output != ""):
                    out_0.append(rec)
    
                if verbose:
                    sys.stderr.write(".")
                if (verbose > 1):
                    sys.stderr.write("NEW")
    
    ### print-match
    
            elif (rec_match <= level):
                result[1] += 1
                if(match_mode==1):
                    recs_out.append(rec)
                if (batch_output != ""):
                    out_1.append(rec)
    
                if verbose:
                    sys.stderr.write(".")
                if (verbose > 1):
                    sys.stderr.write("MATCH")
    
    
    ### print-ambiguous
    
            elif(rec_match > level):
                result[2] += 1
                if(match_mode==2):
                    recs_out.append(rec)
                if (batch_output != ""):
                    out_2.append(rec)
    
                if verbose:
                    sys.stderr.write(".")
                if (verbose > 1):
                    sys.stderr.write("AMBIGUOUS")
    
            else:
                pass
    
            sys.stderr.write(more_detailed_info)
    
    if verbose:
        sys.stderr.write("\n\n Bibmatch report\n")
        sys.stderr.write("=" * 35)
        sys.stderr.write("\n New records         : %d" % result[0])
        sys.stderr.write("\n Matched records     : %d" % result[1])
        sys.stderr.write("\n Ambiguous records   : %d\n" % result[2])
        sys.stderr.write("=" * 35)
        sys.stderr.write("\n Total records       : %d\n" % record_counter)
    
    if noprocess:
        pass
    else:
        for record in recs_out:
            print print_rec(record[0])
    
        if (batch_output != ""):
            filename = "%s.0" % batch_output
            file_0 = open(filename,"w")
            filename = "%s.1" % batch_output
            file_1 = open(filename,"w")
            filename = "%s.2" % batch_output
            file_2 = open(filename,"w")
            for record in out_0:
                file_0.write(print_rec(record[0]))
            for record in out_1:
                file_1.write(print_rec(record[0]))
            for record in out_2:
                file_2.write(print_rec(record[0]))
            file_0.close()
            file_1.close()
            file_2.close()








