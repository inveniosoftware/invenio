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

"""OAI repository archive and management tool"""

__revision__ = "$Id$"

import fileinput 
import string
import os
import sys
import getopt
import time

from invenio.config import \
     CFG_OAI_ID_FIELD, \
     CFG_OAI_ID_PREFIX, \
     CFG_OAI_SET_FIELD, \
     bibupload, \
     bindir, \
     cdsname, \
     version, \
     tmpdir
from invenio.search_engine import perform_request_search
from invenio.dbquery import run_sql

def printInfo():
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
    print " -n --no-process Do not upload records (default)\n"
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

def get_recID_list(oai_sets, set):

    setSpec          = ""
    setName          = ""
    setCoverage      = ""
    #list_of_sets     = []
    processed_sets   = []
    recID_list       = []

    for oai in oai_sets:

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

            recID_list_ = perform_request_search(c=oai['c'].split(','),
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
    
    elif(mode == 0):
    
        oai_sets = get_set_descriptions(set)
        setSpec, setName, setCoverage, recID_list   = get_recID_list(oai_sets, set)
    
        if(set == ""):
            printInfo()
        else:
    
            oai_has_list = perform_request_search(c=cdsname, p1=set, f1=CFG_OAI_SET_FIELD, m1="e")
    
            sys.stdout.write("\n setSpec            : %s\n" % setSpec)
            sys.stdout.write(" setName            : %s\n" % setName)
            sys.stdout.write(" setDescription     : %s \n\n" % setCoverage)
            sys.stdout.write(" Coverage           : %d records\n" % (len(recID_list)))
            sys.stdout.write(" OAI repository has : %d records\n" % (len(oai_has_list)))
            sys.stdout.write(" To be uploaded     : %d records\n\n" % (len(recID_list) - len(oai_has_list)))

    else:

        filename = tmpdir + "/oai_archive_%s" % time.strftime("%H%M%S",time.localtime())
    
        oai_sets = get_set_descriptions(set)
        oai_out = open(filename,"w")
    
        setSpec, setName, setCoverage, recID_list   = get_recID_list(oai_sets, set)
    
        for recID in recID_list:
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
                    oai_out.write("<record>\n")
                    oai_out.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                    oai_out.write(datafield_id_head)
                    oai_out.write("\n")
                    if oaisetentry:
                        # Record is still part of some sets
                        oai_out.write(oaiIDentry)
                        oai_out.write(oaisetentry)
                    else:
                        # Remove record from OAI repository
                        oai_out.write("<subfield code=\"")
                        oai_out.write(CFG_OAI_ID_FIELD[5:6])
                        oai_out.write("\"></subfield>\n")
                        oai_out.write("<subfield code=\"")
                        oai_out.write(CFG_OAI_SET_FIELD[5:6])
                        oai_out.write("\"></subfield>\n")
                    oai_out.write("</datafield>\n")
                    oai_out.write("</record>\n")

                else:
                    oai_out.write("<record>\n")
                    oai_out.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                    if oaisetentry:
                        # Record is still part of some set
                        # Keep the OAI ID as such
                        pass
                    else:
                        # Remove record from OAI repository
                        # i.e. remove OAI ID
                        oai_out.write(datafield_id_head)
                        oai_out.write("\n")
                        oai_out.write("<subfield code=\"")
                        oai_out.write(CFG_OAI_ID_FIELD[5:6])
                        oai_out.write("\"></subfield>\n")
                        oai_out.write("</datafield>\n")

                    oai_out.write(datafield_set_head)
                    oai_out.write("\n")
                    if oaisetentry:
                        # Record is still part of some set
                        oai_out.write(oaisetentry)
                    else:
                        # Remove record from OAI repository
                        oai_out.write("<subfield code=\"")
                        oai_out.write(CFG_OAI_SET_FIELD[5:6])
                        oai_out.write("\"></subfield>\n")
                    oai_out.write("</datafield>\n")
                    oai_out.write("</record>\n")
                        
            elif (mode==1):
                # Add mode
                
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
        oai_out.close()
    
    if upload:
        if(mode==1) and oaisetentrycount:
            command="%s/bibupload -a %s" % (bindir, filename)
            os.system(command)
        if(mode==2):
            command="%s/bibupload -c %s" % (bindir, filename)
            os.system(command)
