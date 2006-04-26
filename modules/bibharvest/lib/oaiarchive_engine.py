## $Id$
## OAI repository archive and management tool

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""OAI repository archive and management tool"""

try:
    import fileinput 
    import string
    import os
    import sys
    import getopt
    import time
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)
try:
    from cdsware.search_engine import perform_request_search
    from cdsware.config import *
    from cdsware.dbquery import run_sql
except ImportError, e:
    print "Error: %s" % e
    sys.exit(1)

__version__ = "$Id$"

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

    sets = []
    query = "select * from oaiARCHIVE"
    res = run_sql(query)
    for row in res:
        sets.append(list(row))
    return sets

def repository_size():
    "Read repository size"

    return len(perform_request_search(p1=".*", f1=oaiidfield, m1="r"))

def get_set_descriptions(setSpec):
    "Retrieve set descriptions from oaiARCHIVE table"

    set_descriptions = []

    query = "select * from oaiARCHIVE where setSpec='%s'" % setSpec
    res = run_sql(query)

    for row in res:

        set_descriptions_item = []
        set_descriptions_item.append(setSpec)
        set_descriptions_item.append(setSpec)
        set_descriptions_item.append(row[3])
        query_box = []
        query_box.append(row[4])
        query_box.append(row[5])
        query_box.append(row[6])
        set_descriptions_item.append(query_box)        
        query_box = []
        query_box.append(row[7])
        query_box.append(row[8])
        query_box.append(row[9])
        set_descriptions_item.append(query_box)
        set_descriptions.append(set_descriptions_item)

    return set_descriptions

def get_recID_list(oai_sets, set):

    setSpec          = ""
    setName          = ""
    setCoverage      = ""
    list_of_sets     = []
    list_of_sets_1   = []
    recID_list       = []

    for oai in oai_sets:

        if oai[1] in list_of_sets_1:
            pass
        else:
            list_of_sets.append(oai)
            list_of_sets_1.append(oai[1])

        if(oai[1]==set):
        
            setSpec = oai[1]
            setName = oai[0]
            setCoverage += oai[2]
            setCoverage += " "

            recID_list_ = perform_request_search(c=oai[2], p1=oai[3][0], f1=oai[3][1], m1=oai[3][2], op1='a', p2=oai[4][0], f2=oai[4][1], m2=oai[4][2])

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
    
            oai_has_list = perform_request_search(c=cdsname, p1=set[2], f1=oaisetfield, m1="e")
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
    
            oai_has_list = perform_request_search(c=cdsname, p1=set, f1=oaisetfield, m1="e")
    
            sys.stdout.write("\n setSpec            : %s\n" % setSpec)
            sys.stdout.write(" setName            : %s\n" % setName)
            sys.stdout.write(" setDescription     : %s \n\n" % setCoverage)
            sys.stdout.write(" Coverage           : %d records\n" % (len(recID_list)))
            sys.stdout.write(" OAI repository has : %d records\n" % (len(oai_has_list)))
            sys.stdout.write(" To be uploaded     : %d records\n\n" % (len(recID_list) - len(oai_has_list)))

    else:

        filename = "/tmp/oai_archive_%s" % time.strftime("%H%M%S",time.localtime())
    
        oai_sets = get_set_descriptions(set)
        oai_out = open(filename,"w")
    
        setSpec, setName, setCoverage, recID_list   = get_recID_list(oai_sets, set)
    
        for recID in recID_list:
            time.sleep(int(nice)/10)
            ID = "%d" % recID
    
    ### oaiIDentry validation
            
            query = "select b3.value from bibrec_bib%sx as br left join bib%sx as b3 on br.id_bibxxx=b3.id where b3.tag='%s' and br.id_bibrec='%s'" % (oaiidfield[0:2], oaiidfield[0:2], oaiidfield, recID)
            res = run_sql(query)        
            if(res):
                oaiIDentry = ''
            else:
                oaiIDentry = "<subfield code=\"%s\">oai:%s:%s</subfield>\n" % (oaiidfield[5:6], oaiidprefix, ID)
                oaiIDentrycount += 1

            datafield_set_head = "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % (oaisetfield[0:3], oaisetfield[3:4], oaisetfield[4:5])
            datafield_id_head  = "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % (oaiidfield[0:3], oaiidfield[3:4], oaiidfield[4:5])

            oaisetentry = "<subfield code=\"%s\">%s</subfield>\n" % (oaisetfield[5:6], set)
            oaisetentrycount += 1


            
    ### oaisetentry validation
            query = "select b3.value from bibrec_bib%sx as br left join bib%sx as b3 on br.id_bibxxx=b3.id where b3.tag='%s' and br.id_bibrec='%s'" % (oaisetfield[0:2], oaisetfield[0:2], oaisetfield, recID)
            res = run_sql(query)
    
    
            if(res):
                for item in res:
                    if (item[0]==set):
                        oaisetentry = ''
                        oaisetentrycount -= 1
    
            if (mode==2):
    
                if (oaiidfield[0:5] == oaisetfield[0:5]):
                
                    oai_out.write("<record>\n")
                    oai_out.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                    oai_out.write(datafield_id_head)
                    oai_out.write("\n")
                    oai_out.write("<subfield code=\"")
                    oai_out.write(oaiidfield[5:6])
                    oai_out.write("\"></subfield>\n")
                    oai_out.write("<subfield code=\"")
                    oai_out.write(oaisetfield[5:6])
                    oai_out.write("\"></subfield>\n")
                    oai_out.write("</datafield>\n")
                    oai_out.write("</record>\n")

                else:
                    
                    oai_out.write("<record>\n")
                    oai_out.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                    oai_out.write(datafield_id_head)
                    oai_out.write("\n")
                    oai_out.write("<subfield code=\"")
                    oai_out.write(oaiidfield[5:6])
                    oai_out.write("\"></subfield>\n")
                    oai_out.write("</datafield>\n")

                    oai_out.write(datafield_set_head)
                    oai_out.write("\n")
                    oai_out.write("<subfield code=\"")
                    oai_out.write(oaisetfield[5:6])
                    oai_out.write("\"></subfield>\n")
                    oai_out.write("</datafield>\n")
                    oai_out.write("</record>\n")
                        
            elif (mode==1):

                if ((oaiIDentry)or(oaisetentry)):
                    if (oaiidfield[0:5] == oaisetfield[0:5]):                
                        oai_out.write("<record>\n")
                        oai_out.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                        oai_out.write(datafield_id_head)
                        oai_out.write("\n")
                        if(oaiIDentry):
                            oai_out.write(oaiIDentry)
                        if(oaisetentry):
                            oai_out.write(oaisetentry)
                        oai_out.write("</datafield>\n")
                        oai_out.write("</record>\n")
                    else:
                        oai_out.write("<record>\n")
                        oai_out.write("<controlfield tag=\"001\">%s</controlfield>\n" % recID)
                        oai_out.write(datafield_id_head)
                        oai_out.write("\n")
                        if(oaiIDentry):
                            oai_out.write(oaiIDentry)
                        oai_out.write("</datafield>\n")

                        oai_out.write(datafield_set_head)
                        oai_out.write("\n")
                        if(oaisetentry):
                            oai_out.write(oaisetentry)
                        oai_out.write("</datafield>\n")
                        oai_out.write("</record>\n")
                    
        oai_out.close()
    
    
    if(upload):
        if(mode==1):
            command="%s/bibupload -a %s" % (bindir, filename)
            os.system(command)
        if(mode==2):
            command="%s/bibupload -c %s" % (bindir, filename)
            os.system(command)
