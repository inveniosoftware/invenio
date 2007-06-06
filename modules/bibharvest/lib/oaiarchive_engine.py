## $Id$
## OAI repository archive and management tool

## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""OAI repository archive and management tool

   TODO: - Enable -c ('correct' or mode == 4) mode once correctly tested.
         - Fix problem of zombie records (records that are in not set, and
           can therefore not be removed) that can occurs with -c mode.
"""

__revision__ = "$Id$"

import os
import sys
import getopt
import time
import getpass
import marshal
import signal
import re

from invenio.config import \
     CFG_OAI_ID_FIELD, \
     CFG_OAI_ID_PREFIX, \
     CFG_OAI_SET_FIELD, \
     bindir, \
     cdsname, \
     tmpdir
from invenio.search_engine import perform_request_search
from invenio.dbquery import run_sql, escape_string
from invenio.access_control_engine import acc_authorize_action

##from invenio.config import *

options = {} # global variable to hold task options

sleep_time      = ""                           # default sleeptime
sched_time     = time.strftime("%Y-%m-%d %H:%M:%S") # scheduled execution time in the date/time format

def print_info():
    """Print help"""

    print " oaiarchive [options]\n"
    print "\n Options:"
    print "\n -o --oaiset=    Specify setSpec"
    print " -h --help       Print this help"
    print " -V --version    Print version information and exit"
    print "\n Modes"
    print " -a --add        Add records to OAI repository"
    print " -d --delete     Remove records from OAI repository"
    print " -r --report     Print OAI repository status"
    print " -i --info       Give info about OAI set (default)"
    print "\n Additional parameters:"
    print " -p --upload     Upload records"
    print " -u --user=USER       User name to submit the task as, password needed."
    print " -v --verbose=LEVEL   Verbose level (0=min,1=normal,9=max)."
    print " -s --sleeptime=SLEEP Time after which to repeat tasks (no)"
    print " -t --time=DATE       Moment for the task to be active (now)."

    print "\n Examples:\n"

    print " Expose set 'setname' via OAI repository gateway"
    print " oaiarchive --oaiset='setname' --add --upload"
    print " oaiarchive -apo 'setname'"
    print "\n"
    print " Remove records defined by set 'setname' from OAI repository"
    print " oaiarchive --oaiset='setname' --delete --upload"
    print " oaiarchive -dpo 'setname'"
    print "\n"
    print " Expose entire repository via OAI gateway"
    print " oaiarchive --set=global --add --upload"
    print " oaiarchive -apo global"
    print "\n" 
    print " Print OAI set status"
    print " oaiarchive --oaiset='setname' --info"
    print " oaiarchive -io 'setname'"
    print "\n"
    print " Print OAI repository status"
    print " oaiarchive -r"
    
    return

def all_sets():
    """
    Returns a list of sets.
    Each set is [id, setName, setSpec, setCollection, 
                 setDescription, setDefinition, setRecList, 
                 p1, f1, m1, p2, f2, m2, p3, f3, m3]
    """
    sets = []
    query = "select * from oaiARCHIVE"
    res = run_sql(query)
    for row in res:
        sets.append(list(row))

        # Split setDefinition column in columns collection, p1, f1, m1,
        # p2, f2, m2, p3, f3, m3
        
        # Mapping between argument name and column number in sql table
        arg_to_col_number = {'c': 3,
                             'p1': 7,
                             'f1': 8,
                             'm1': 9,
                             'p2': 10,
                             'f2': 11,
                             'm2': 12,
                             'p3': 13,
                             'f3': 14,
                             'm3': 15}

        params = parse_set_definition(row[5])
        for arg, value in params.iteritems():
            if arg_to_col_number.has_key(arg):
                sets[-1][arg_to_col_number[arg]] = value
            
    return sets

def parse_set_definition(set_definition):
    """
    Returns the parameters for the given set definition

    The returned structure is a dictionary with keys being
    c, p1, f1, m1, p2, f2, m2, p3, f3, m3 and corresponding values

    @param set_definition a string as returned by the database for column 'setDefinition'
    @return a dictionary
    """
    params = {'c':'',
              'p1':'', 'f1':'', 'm1':'',
              'p2':'', 'f2':'', 'm2':'',
              'p3':'', 'f3':'', 'm3':''}
    definitions = set_definition.split(';')
    for definition in definitions:
        arguments = definition.split('=')
        if len(arguments) == 2:
            params[arguments[0]] = arguments[1]
    return params
                
def repository_size():
    "Read repository size"

    return len(perform_request_search(p1=".*", f1=CFG_OAI_ID_FIELD, m1="r"))

def get_set_descriptions(setSpec):
    "Retrieve set descriptions from oaiARCHIVE table"

    set_descriptions = []

    query = "select * from oaiARCHIVE where setSpec='%s'" % setSpec
    res = run_sql(query)

    for row in res:
        params = parse_set_definition(row[5])
        params['setSpec'] = setSpec
        params['setName'] = row[1]
        ## set_descriptions_item = []
##         set_descriptions_item.append(setSpec)
##         set_descriptions_item.append(setSpec)
##         #set_descriptions_item.append(row[3])
##         set_descriptions_item.append(params['c'])
##         query_box = []
##         #query_box.append(row[4])
##         #query_box.append(row[5])
##         #query_box.append(row[6])
##         query_box.append(params['p1'])
##         query_box.append(params['f1'])
##         query_box.append(params['m1'])
##         set_descriptions_item.append(query_box)        
##         query_box = []
##         #query_box.append(row[7])
##         query_box.append(params['p1'])
##         #query_box.append(row[8])
##         query_box.append(params['f1'])
##         #query_box.append(row[9])
##         query_box.append(params['m1'])
##         set_descriptions_item.append(query_box)
        
##        set_descriptions.append(set_descriptions_item)
        set_descriptions.append(params)
    return set_descriptions

def get_recID_list(oai_set_descriptions, set):
    """Returns the list of records ID belonging to 'set'

    @param set The set object from which to retrieve the records (as in list returned by all_sets())
    @param oai_set_descriptions The list of descriptions for the set (as returned by get_set_descriptions())
    """
    setSpec          = ""
    setName          = ""
    setCoverage      = ""
    #list_of_sets     = []
    processed_sets   = []
    recID_list       = []

    for oai in oai_set_descriptions:

        if oai['setSpec'] in processed_sets :
            pass
        else:
            #list_of_sets.append(oai)
            processed_sets.append(oai['setSpec'])

        if(oai['setSpec'] == set):
        
            setSpec = oai['setSpec']
            setName = oai['setName']
            setCoverage += oai['c']
            setCoverage += " "

            recID_list_ = perform_request_search(c=[coll.strip() for coll in oai['c'].split(',')],
                                                 p1=oai['p1'],
                                                 f1=oai['f1'],
                                                 m1=oai['m1'],
                                                 op1='a',
                                                 p2=oai['p2'],
                                                 f2=oai['f2'],
                                                 m2=oai['m2'],
                                                 op2='a',
                                                 p3=oai['p3'],
                                                 f3=oai['f3'],
                                                 m3=oai['m3'])
            for recID in recID_list_:
                if recID in recID_list:
                    pass
                else:
                    recID_list.append(recID)

    if (setSpec == "global"):
        setCoverage = cdsname

    return (setSpec, setName, setCoverage, recID_list)


### MAIN ###

def oaiarchive_task(arg):
    """Main business logic code of oai_archive"""
    upload           = arg["upload"]
    oaisetentrycount = 0
    oaiIDentrycount  = 0
    mode             = arg["mode"]
    i                = 0
    nice             = arg["nice"]
    set              = arg["oaiset"]

    if(mode == 3):
    
        all_oai_sets = all_sets()
        repository_size_s = "%d" % repository_size()
    
        current_date = time.strftime("%d-%m-%y %H:%M:%S")
    
        sys.stdout.write("\n  ")
        sys.stdout.write(cdsname)
        sys.stdout.write(" OAI Repository Status\n")
        sys.stdout.write("  ")
        sys.stdout.write(current_date)
        sys.stdout.write("\n")
        sys.stdout.write("=" * 73)
        sys.stdout.write("\n")
        sys.stdout.write("  setSpec")
        sys.stdout.write(" " * 16)
        sys.stdout.write("  setName")
        sys.stdout.write(" " * 29)
        sys.stdout.write("  Volume")
        sys.stdout.write("\n")
        sys.stdout.write("-" * 73)
        sys.stdout.write("\n")
    
        for set in all_oai_sets:
    
            oai_sets = get_set_descriptions(set[2])
            setSpec, setName, setCoverage, recID_list = get_recID_list(oai_sets, set)
    
            oai_has_list = perform_request_search(c=cdsname, p1=set[2], f1=CFG_OAI_SET_FIELD, m1="e")
            oai_has_list_len = "%d" % len(oai_has_list)
            
            sys.stdout.write("  ")
            sys.stdout.write(set[2])
            sys.stdout.write(" " * (25 - len(set[2])))
            set_name = "%s" % set[1][:32]
            if (len(set_name) == 32):
                set_name = "%s..." % set_name
            sys.stdout.write(set_name)
            sys.stdout.write(" " * (35 - len(set_name)))
            sys.stdout.write(" " * (9 - len(oai_has_list_len)))
            sys.stdout.write(oai_has_list_len)
            sys.stdout.write("\n")
    
        sys.stdout.write("=" * 73)
        sys.stdout.write("\n  Total")
        sys.stdout.write(" " * 55)
        sys.stdout.write(" " * (9 - len(repository_size_s)))
        sys.stdout.write(repository_size_s)
        sys.stdout.write("\n")
        sys.stdout.write("\n")

        return 

    if(mode == 0):
    
        oai_sets = get_set_descriptions(set)
        setSpec, setName, setCoverage, recID_list   = get_recID_list(oai_sets, set)
    
        if(set == ""):
            print_info()
        else:
    
            oai_has_list = perform_request_search(c=cdsname, p1=set, f1=CFG_OAI_SET_FIELD, m1="e")
    
            sys.stdout.write("\n setSpec            : %s\n" % setSpec)
            sys.stdout.write(" setName            : %s\n" % setName)
            sys.stdout.write(" setDescription     : %s \n\n" % setCoverage)
            sys.stdout.write(" Coverage           : %d records\n" % (len(recID_list)))
            sys.stdout.write(" OAI repository has : %d records\n" % (len(oai_has_list)))
            sys.stdout.write(" To be uploaded     : %d records\n\n" % (len(recID_list) - len(oai_has_list)))

    else:
        task_update_progress("Fetching records in %s." % set)
        if mode == 1 or mode == 4:
            filename = tmpdir + "/oai_archive_%s" % time.strftime("%H%M%S", time.localtime())
            oai_out = open(filename,"w")
        if mode == 2 or mode == 4:
            filename2 = tmpdir + "/oai_archive_%s_2" % time.strftime("%H%M%S", time.localtime())
            oai_out2 = open(filename2,"w")
            
        oai_sets = get_set_descriptions(set)
    
        setSpec, setName, setCoverage, recID_list   = get_recID_list(oai_sets, set)

        i = 0
        for recID in recID_list:
            task_update_progress("Set %s: done %s out of %s records." % (setSpec, i, len(recID_list)))
            i += 1
            time.sleep(int(nice)/10)
            ID = "%d" % recID
    
    ### oaiIDentry validation
    ### Check if OAI identifier is already in the record or not
            add_ID_entry = True
            oaiIDentry = "<subfield code=\"%s\">oai:%s:%s</subfield>\n" % (CFG_OAI_ID_FIELD[5:6],
                                                                           CFG_OAI_ID_PREFIX,
                                                                           ID)

            query = "select b3.value from bibrec_bib%sx as br left join bib%sx as b3 on br.id_bibxxx=b3.id where b3.tag='%s' and br.id_bibrec='%s'" % (CFG_OAI_ID_FIELD[0:2], CFG_OAI_ID_FIELD[0:2], CFG_OAI_ID_FIELD, recID)
            res = run_sql(query)
            if(res):
                # No need to add identifier if already exists. (Check
                # that it INDEED exist, i.e. that field is not empty)
                for value in res:
                    if len(value) > 0 and value[0] != '':
                        add_ID_entry = False
                        
            if add_ID_entry:
                oaiIDentrycount += 1

            datafield_set_head = "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % (CFG_OAI_SET_FIELD[0:3],
                                                                                     CFG_OAI_SET_FIELD[3:4],
                                                                                     CFG_OAI_SET_FIELD[4:5])
            datafield_id_head  = "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % (CFG_OAI_ID_FIELD[0:3],
                                                                                     CFG_OAI_ID_FIELD[3:4],
                                                                                     CFG_OAI_ID_FIELD[4:5])

            oaisetentry = "<subfield code=\"%s\">%s</subfield>\n" % (CFG_OAI_SET_FIELD[5:6],
                                                                     set)
            oaisetentrycount += 1
            
    ### oaisetentry validation
    ### Check to which sets this record belongs
            query = "select b3.value from bibrec_bib%sx as br left join bib%sx as b3 on br.id_bibxxx=b3.id where b3.tag='%s' and br.id_bibrec='%s'" % (CFG_OAI_SET_FIELD[0:2], CFG_OAI_SET_FIELD[0:2], CFG_OAI_SET_FIELD, recID)
            res = run_sql(query)
    
            remaining_sets = []
            if(res):
                for item in res:
                    if (item[0]==set):
                        # The record will be removed from this set
                        oaisetentry = ''
                        oaisetentrycount -= 1
                    elif item[0]:
                        # Collect name of sets to which the record must still belong
                        remaining_sets.append(item[0])
    
            if (mode==2):
                # Delete mode
                
                oaisetentry = ''
                # Build sets that the record is still part of 
                for remaining_set in remaining_sets:
                    oaisetentry +=  "<subfield code=\"%s\">%s</subfield>\n" % (CFG_OAI_SET_FIELD[5:6], remaining_set)

                if (CFG_OAI_ID_FIELD[0:5] == CFG_OAI_SET_FIELD[0:5]):
                    # Put set and OAI ID in the same datafield
                    oai_out2.write("<record>\n")
                    oai_out2.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                    oai_out2.write(datafield_id_head)
                    oai_out2.write("\n")
                    if oaisetentry:
                        # Record is still part of some sets
                        oai_out2.write(oaiIDentry)
                        oai_out2.write(oaisetentry)
                    else:
                        # Remove record from OAI repository
                        oai_out2.write("<subfield code=\"")
                        oai_out2.write(CFG_OAI_ID_FIELD[5:6])
                        oai_out2.write("\"></subfield>\n")
                        oai_out2.write("<subfield code=\"")
                        oai_out2.write(CFG_OAI_SET_FIELD[5:6])
                        oai_out2.write("\"></subfield>\n")
                    oai_out2.write("</datafield>\n")
                    oai_out2.write("</record>\n")

                else:
                    oai_out2.write("<record>\n")
                    oai_out2.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                    if oaisetentry:
                        # Record is still part of some set
                        # Keep the OAI ID as such
                        pass
                    else:
                        # Remove record from OAI repository
                        # i.e. remove OAI ID
                        oai_out2.write(datafield_id_head)
                        oai_out2.write("\n")
                        oai_out2.write("<subfield code=\"")
                        oai_out2.write(CFG_OAI_ID_FIELD[5:6])
                        oai_out2.write("\"></subfield>\n")
                        oai_out2.write("</datafield>\n")

                    oai_out2.write(datafield_set_head)
                    oai_out2.write("\n")
                    if oaisetentry:
                        # Record is still part of some set
                        oai_out2.write(oaisetentry)
                    else:
                        # Remove record from OAI repository
                        oai_out2.write("<subfield code=\"")
                        oai_out2.write(CFG_OAI_SET_FIELD[5:6])
                        oai_out2.write("\"></subfield>\n")
                    oai_out2.write("</datafield>\n")
                    oai_out2.write("</record>\n")
                        
            elif (mode==1) or mode == 4:
                # Add mode (1)
                # or clean mode (4)
                
                if ((add_ID_entry)or(oaisetentry)):
                    if (CFG_OAI_ID_FIELD[0:5] == CFG_OAI_SET_FIELD[0:5]):
                        # Put set and OAI ID in the same datafield
                        oai_out.write("<record>\n")
                        oai_out.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                        oai_out.write(datafield_id_head)
                        oai_out.write("\n")
                        if(add_ID_entry):
                            oai_out.write(oaiIDentry)
                        if(oaisetentry):
                            oai_out.write(oaisetentry)
                        oai_out.write("</datafield>\n")
                        oai_out.write("</record>\n")
                    else:
                        oai_out.write("<record>\n")
                        oai_out.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                        if(add_ID_entry):
                            oai_out.write(datafield_id_head)
                            oai_out.write("\n")
                            oai_out.write(oaiIDentry)
                            oai_out.write("</datafield>\n")
                        if(oaisetentry):
                            oai_out.write(datafield_set_head)
                            oai_out.write("\n")
                            oai_out.write(oaisetentry)
                            oai_out.write("</datafield>\n")
                        oai_out.write("</record>\n")

        if mode == 4:
            
            # Update records that should no longer be in this set
            
            # Fetch records that are currently marked with this set in the database
            oai_has_list = perform_request_search(c=cdsname, p1=set, f1=CFG_OAI_SET_FIELD, m1="e")

            # Fetch records that should not be in this set (oai_has_list - recID_list)
            records_to_update = [rec_id for rec_id in oai_has_list \
                                 if not rec_id in recID_list]

            

            datafield_set_head = "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % (CFG_OAI_SET_FIELD[0:3],
                                                                                     CFG_OAI_SET_FIELD[3:4],
                                                                                     CFG_OAI_SET_FIELD[4:5])
            datafield_id_head  = "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % (CFG_OAI_ID_FIELD[0:3],
                                                                                     CFG_OAI_ID_FIELD[3:4],
                                                                                     CFG_OAI_ID_FIELD[4:5])

            for recID in records_to_update:
                oaiIDentry = "<subfield code=\"%s\">oai:%s:%s</subfield>\n" % (CFG_OAI_ID_FIELD[5:6],
                                                                               CFG_OAI_ID_PREFIX,
                                                                               recID)
                
                ### Check to which sets this record belongs
                query = "select b3.value from bibrec_bib%sx as br left join bib%sx as b3 on br.id_bibxxx=b3.id where b3.tag='%s' and br.id_bibrec='%s'" % (CFG_OAI_SET_FIELD[0:2], CFG_OAI_SET_FIELD[0:2], CFG_OAI_SET_FIELD, recID)
                res = run_sql(query)
                oaisetentry = ''
                for in_set in res:
                    if in_set[0] != set:
                        oaisetentry +=  "<subfield code=\"%s\">%s</subfield>\n" % (CFG_OAI_SET_FIELD[5:6], in_set[0])
                    
                if (CFG_OAI_ID_FIELD[0:5] == CFG_OAI_SET_FIELD[0:5]):
                    # Put set and OAI ID in the same datafield
                    oai_out2.write("<record>\n")
                    oai_out2.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                    oai_out2.write(datafield_id_head)
                    oai_out2.write("\n")
#                    if oaisetentry:
                    # Record is still part of some sets
                    oai_out2.write(oaiIDentry)
                    oai_out2.write(oaisetentry)
##                         else:
##                             # Remove record from OAI repository
##                             oai_out.write("<subfield code=\"")
##                             oai_out.write(CFG_OAI_ID_FIELD[5:6])
##                             oai_out.write("\"></subfield>\n")
##                             oai_out.write("<subfield code=\"")
##                             oai_out.write(CFG_OAI_SET_FIELD[5:6])
##                             oai_out.write("\"></subfield>\n")
                    oai_out2.write("</datafield>\n")
                    oai_out2.write("</record>\n")
                else:
                    oai_out2.write("<record>\n")
                    oai_out2.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
##                         if oaisetentry:
##                             # Record is still part of some set
##                             # Keep the OAI ID as such
##                             pass
##                         else:
##                             # Remove record from OAI repository
##                             # i.e. remove OAI ID
##                             oai_out.write(datafield_id_head)
##                             oai_out.write("\n")
##                             oai_out.write("<subfield code=\"")
##                             oai_out.write(CFG_OAI_ID_FIELD[5:6])
##                             oai_out.write("\"></subfield>\n")
##                             oai_out.write("</datafield>\n")
                    
                    oai_out2.write(datafield_set_head)
                    oai_out2.write("\n")
#                        if oaisetentry:
                            # Record is still part of some set
                    oai_out2.write(oaisetentry)
#                        else:
#                            # Remove record from OAI repository
#                            oai_out.write("<subfield code=\"")
#                            oai_out.write(CFG_OAI_SET_FIELD[5:6])
#                            oai_out.write("\"></subfield>\n")
                    oai_out2.write("</datafield>\n")
                    oai_out2.write("</record>\n")

        if mode == 1 or mode == 4:
            oai_out.close()
        if mode == 2 or mode == 4:
            oai_out2.close()
    
    if upload:
        if (mode == 1 or mode == 4) and oaisetentrycount:
            command = "%s/bibupload -a %s" % (bindir, filename)
            os.system(command)
        if mode == 2 or mode == 4:
            command = "%s/bibupload -c %s" % (bindir, filename2)
            os.system(command)





### Bibshed compatibility procedures
###

def get_date(var, format_string = "%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    date = time.time()
    shift_re = re.compile("([-\+]{0,1})([\d]+)([dhms])")
    factors = {"d":24*3600, "h":3600, "m":60, "s":1}
    match_date = shift_re.match(var)
    if match_date:
        sign = match_date.groups()[0] == "-" and -1 or 1
        factor = factors[match_date.groups()[2]]
        value = float(match_date.groups()[1])
        date = time.localtime(date + sign * factor * value)
        date = time.strftime(format_string, date)
    else:
        date = time.strptime(var, format_string)
        date = time.strftime(format_string, date)

    return date


def write_message(msg, stream=sys.stdout):
    """Prints message and flush output stream (may be sys.stdout or sys.stderr).  Useful for debugging stuff."""
    if stream == sys.stdout or stream == sys.stderr:
        stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
        try:
            stream.write("%s\n" % msg)
        except UnicodeEncodeError:
            stream.write("%s\n" % msg.encode('ascii', 'backslashreplace'))
        stream.flush()
    else:
        sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)


def task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_sleep(), got signal %s frame %s" % (sig, frame))
    write_message("sleeping...")
    task_update_status("SLEEPING")
    signal.pause() # wait for wake-up signal


def task_sig_wakeup(sig, frame):
    """Signal handler for the 'wakeup' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_wakeup(), got signal %s frame %s" % (sig, frame))
    write_message("continuing...")
    task_update_status("CONTINUING")


def task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_stop(), got signal %s frame %s" % (sig, frame))
    write_message("stopping...")
    task_update_status("STOPPING")
    write_message("flushing cache or whatever...")
    time.sleep(3)
    write_message("closing tables or whatever...")
    time.sleep(1)
    write_message("stopped")
    task_update_status("STOPPED")
    sys.exit(0)

    
def task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_suicide(), got signal %s frame %s" % (sig, frame))
    write_message("suiciding myself now...")
    task_update_status("SUICIDING")
    write_message("suicided")
    task_update_status("SUICIDED")
    sys.exit(0)


def task_sig_unknown(sig, frame):
    """Signal handler for the other unknown signals sent by shell or user."""
    # do nothing for unknown signals:
    write_message("unknown signal %d (frame %s) ignored" % (sig, frame)) 

def authenticate(user, header="OAI Archive Task Submission", action="runoaiarchive"):
    """Authenticate the user against the user database.
       Check for its password, if it exists.
       Check for action access rights.
       Return user name upon authorization success,
       do system exit upon authorization failure.
       """
    print header
    print "=" * len(header)
    if user == "":
        print >> sys.stdout, "\rUsername: ",
        user = sys.stdin.readline().lower().strip()
    else:
        print >> sys.stdout, "\rUsername:", user        
    ## first check user pw:
    res = run_sql("select id,password from user where email=%s", (user,), 1) + \
          run_sql("select id,password from user where nickname=%s", (user,), 1)
    if not res:
        print "Sorry, %s does not exist." % user
        sys.exit(1)        
    else:
        (uid_db, password_db) = res[0]
        if password_db:
            password_entered = getpass.getpass()
            if password_db == password_entered:
                pass
            else:
                print "Sorry, wrong credentials for %s." % user
                sys.exit(1)
        ## secondly check authorization for the action:
        (auth_code, auth_message) = acc_authorize_action(uid_db, action)
        if auth_code != 0:
            print auth_message
            sys.exit(1)
    return user

def task_submit():
    """Submits task to the BibSched task queue.  This is what people will be invoking via command line."""

    global options, sched_time, sleep_time

    ## sanity check: remove eventual "task" option:
    if options.has_key("task"):
        del options["task"]
    ## authenticate user:
    user = authenticate(options.get("user", ""))
    ## submit task:

    task_id = run_sql("""INSERT INTO schTASK (id,proc,user,status,arguments,sleeptime,runtime) VALUES (NULL,'oaiarchive',%s,'WAITING',%s,%s,%s)""",
                      (user, marshal.dumps(options),sleep_time,escape_string(sched_time)))
    ## update task number:
    options["task"] = task_id
    run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""", (marshal.dumps(options), task_id))
    write_message("Task #%d submitted." % task_id)
    return task_id


def task_update_progress(msg):
    """Updates progress information in the BibSched task table."""
    global options
    return run_sql("UPDATE schTASK SET progress=%s where id=%s", (msg, options["task"]))


def task_update_status(val):
    """Updates status information in the BibSched task table."""
    global options
    return run_sql("UPDATE schTASK SET status=%s where id=%s", (val, options["task"]))


def task_read_status(task_id):
    """Read status information in the BibSched task table."""
    res = run_sql("SELECT status FROM schTASK where id=%s", (task_id,), 1)
    try:
        out = res[0][0]
    except:
        out = 'UNKNOWN'
    return out


def task_get_options(task_id):
    """Returns options for the task 'task_id' read from the BibSched task queue table."""
    out = {}
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s AND proc='oaiarchive'", (task_id,))
    try:
        out = marshal.loads(res[0][0])
    except:
        write_message("Error: OAIarchive task %d does not seem to exist." % task_id)
        sys.exit(1)
    return out


def task_run(task_id):
    """Runs the task"""
    global options
    options = task_get_options(task_id) # get options from BibSched task table
    ## check task id:
    if not options.has_key("task"):
        write_message("Error: The task #%d does not seem to be a OAI archive task." % task_id)
        return

    ## check task status:
    task_status = task_read_status(task_id)
    if task_status != "WAITING":
        write_message("Error: The task #%d is %s.  I expected WAITING." % (task_id, task_status))
        return
    
    ## update task status:
    task_update_status("RUNNING")
    
    ## initialize signal handler:
    signal.signal(signal.SIGUSR1, task_sig_sleep)
    signal.signal(signal.SIGTERM, task_sig_stop)
    signal.signal(signal.SIGABRT, task_sig_suicide)
    signal.signal(signal.SIGCONT, task_sig_wakeup)
    signal.signal(signal.SIGINT, task_sig_unknown)
        
    ## run the task:
    oaiarchive_task(options)

    ## we are done:
    task_update_status("DONE")
    return


#########################


def main():
    """Main function that analyzes command line input and calls whatever is appropriate.
       Useful for learning on how to write BibSched tasks."""
    global options, sched_time, sleep_time
    ## parse command line:
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        ## A - run the task
        task_id = int(sys.argv[1])
        task_run(task_id)
    else:
        ## B - submit the task
        options = {} # will hold command-line options
        options["verbose"] = 1
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hVv:u:s:t:ado:pirn", ["help", "version", "verbose=", "user=", "sleeptime=", "time=", "add", "delete", "oaiset=", "upload", "info", "report", "no-process"])
        except getopt.GetoptError:
            print_info()
            sys.exit(1)

        ## set defaults
        options["upload"] = 0
        options["mode"]   = 0
        options["oaiset"] = ""
        options["nice"]   = 0

        try:

            for opt in opts:
                if opt[0] in ["-h", "--help"]:
                    print_info()
                    sys.exit(0)
                elif opt[0] in ["-V", "--version"]:
                    print __revision__
                    sys.exit(0)
                elif opt[0] in [ "-u", "--user"]:
                    options["user"]   = opt[1]
                elif opt[0] in ["-v", "--verbose"]:
                    options["verbose"]  = int(opt[1])
                elif opt[0] in ["-s", "--sleeptime" ]:
                    get_date(opt[1])    # see if it is a valid shift
                    sleep_time  = opt[1]
                elif opt[0] in [ "-t", "--time" ]:
                    sched_time = get_date(opt[1])
                elif opt[0] in ["-n", "--nice"]:
                    options["nice"] = opt[1]
                elif opt[0] in ["-o", "--oaiset"]:
                    options["oaiset"] = opt[1]
                elif opt[0] in ["-a", "--add"]:
                    options["mode"] = 1
                elif opt[0] in ["-d", "--delete"]:
                    options["mode"] = 2
                elif opt[0] in ["-c", "--clean"]:
                    options["mode"] = 4
                elif opt[0] in ["-p", "--upload"]:
                    options["upload"] = 1
                elif opt[0] in ["-i", "--info"]:
                    options["mode"] = 0
                elif opt[0] in ["-r", "--report"]:
                    options["mode"] = 3
                elif opt[0] in ["-n", "--no-process"]:
                    options["upload"] = 0

        except StandardError:
            print_info()
            sys.exit(1)
        task_submit()
    return

### okay, here we go:
if __name__ == '__main__':
    main()
