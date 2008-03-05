## $Id$
## OAI repository archive and management tool

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
import time
from stat import ST_SIZE

from invenio.config import \
     CFG_OAI_ID_FIELD, \
     CFG_OAI_ID_PREFIX, \
     CFG_OAI_SET_FIELD, \
     bindir, \
     cdsname, \
     tmpdir
from invenio.search_engine import perform_request_search
from invenio.dbquery import run_sql
from invenio.bibtask import task_get_option, task_set_option, write_message, \
    task_update_progress, task_init

def all_sets():
    """
    Returns a list of sets.
    Each set is [id, setName, setSpec, setCollection,
                 setDescription, setDefinition, setRecList,
                 p1, f1, m1, p2, f2, m2, p3, f3, m3]

    but parameters p1, f1, m1, p2, f2, m2, p3, f3, m3 should not be used.
    Use parse_set_definition(setDefinition) instead.
    """
    sets = []
    query = """SELECT id, setName, setSpec, setCollection, setDescription,
                      setDefinition, setRecList,
                      p1, f1, m1, p2, f2, m2, p3, f3, m3
               FROM oaiARCHIVE"""
    res = run_sql(query)
    for (setID, setName, setSpec, setCollection, setDescription,
         setDefinition, setRecList, p1, f1, m1, p2, f2, m2, p3, f3, m3) in res:

        params = parse_set_definition(setDefinition)
        set = [setID,
               setName,
               setSpec,
               setCollection,
               setDescription,
               setDefinition,
               setRecList,
               params['p1'],
               params['f1'],
               params['m1'],
               params['p2'],
               params['f2'],
               params['m2'],
               params['p3'],
               params['f3'],
               params['m3']]

        sets.append(set)

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
              'p3':'', 'f3':'', 'm3':'',
              'op1':'a', 'op2':'a'}
    definitions = set_definition.split(';')
    for definition in definitions:
        arguments = definition.split('=')
        if len(arguments) == 2:
            params[arguments[0]] = arguments[1]
    return params

def repository_size():
    "Read repository size"

    return len(perform_request_search(p1="oai:*", f1=CFG_OAI_ID_FIELD, m1="e", ap=0))

def get_set_descriptions(setSpec):
    "Retrieve set descriptions from oaiARCHIVE table"

    set_descriptions = []

    query = "select setName, setDefinition from oaiARCHIVE where setSpec=%s"
    res = run_sql(query, (setSpec, ))

    for (set_name, set_definition) in res:
        params = parse_set_definition(set_definition)
        params['setSpec'] = setSpec
        params['setName'] = set_name
        set_descriptions.append(params)
    return set_descriptions

def get_recID_list(oai_set_descriptions, set):
    """Returns the list of records ID belonging to 'set'

    @param set The set object from which to retrieve the records
    (as in list returned by all_sets())
    @param oai_set_descriptions The list of descriptions for the set
    (as returned by get_set_descriptions())
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

            recID_list_ = perform_request_search(c=[coll.strip()
                    for coll in oai['c'].split(',')],
                    p1=oai['p1'],
                    f1=oai['f1'],
                    m1=oai['m1'],
                    op1=oai['op1'],
                    p2=oai['p2'],
                    f2=oai['f2'],
                    m2=oai['m2'],
                    op2=oai['op2'],
                    p3=oai['p3'],
                    f3=oai['f3'],
                    m3=oai['m3'],
                    ap=0)

            for recID in recID_list_:
                if recID in recID_list:
                    pass
                else:
                    recID_list.append(recID)

    if (setSpec == "global"):
        setCoverage = cdsname

    return (setSpec, setName, setCoverage, recID_list)


### MAIN ###

def oaiarchive_task():
    """Main business logic code of oai_archive"""
    upload = task_get_option("upload")
    mode   = task_get_option("mode")
    nice   = task_get_option("nice")
    sets   = task_get_option("oaiset")

    if(mode == 3):
        # Print repository status
        all_oai_sets = all_sets()
        repository_size_s = "%d" % repository_size()

        write_message(cdsname)
        write_message(" OAI Repository Status")
        write_message("=" * 73)
        write_message("  setSpec" + " " * 16 + "  setName" +
            " " * 29 + "  Volume")
        write_message("-" * 73)

        for _set in all_oai_sets:

            oai_sets = get_set_descriptions(_set[2])
            setSpec, setName, setCoverage, recID_list = \
                get_recID_list(oai_sets, _set)

            oai_has_list = perform_request_search(c=cdsname, p1=_set[2],
                f1=CFG_OAI_SET_FIELD, m1="e", ap=0)
            oai_has_list_len = "%d" % len(oai_has_list)

            set_name = "%s" % _set[1][:32]
            if (len(set_name) == 32):
                set_name = "%s..." % set_name
            write_message("  " + _set[2] + " " * (25 - len(_set[2])) + set_name +
                " " * (35 - len(set_name)) +
                " " * (9 - len(oai_has_list_len)) +
                oai_has_list_len)

        write_message("=" * 73)
        write_message("  Total" + " " * 55 +
            " " * (9 - len(repository_size_s)) + repository_size_s)

        return True

    # Mode 1, 2 and 4

    if isinstance(sets, str):
        # Backward compatibility with old way of storing 'oaiset' parameter
        sets = list(sets)

    set_number = 0
    for set in sets:
        set_number += 1

        # Reset some variables
        oaisetentrycount = 0
        oaiIDentrycount  = 0
        i                = 0

        if(mode == 0):

            oai_sets = get_set_descriptions(set)
            setSpec, setName, setCoverage, recID_list = \
                get_recID_list(oai_sets, set)

            if(set == ""):
                raise StandardError
            else:

                oai_has_list = perform_request_search(c=cdsname, p1=set,
                    f1=CFG_OAI_SET_FIELD, m1="e", ap=0)

                write_message(" setSpec            : %s" % setSpec)
                write_message(" setName            : %s" % setName)
                write_message(" setDescription     : %s" % setCoverage)
                write_message(" Coverage           : %d records" %
                    (len(recID_list)))
                write_message(" OAI repository has : %d records" %
                    (len(oai_has_list)))
                write_message(" To be uploaded     : %d records" %
                    (len(recID_list) - len(oai_has_list)))

        else:
            task_update_progress("[%i/%i] Fetching records in %s." % \
                                 (set_number, len(sets), set))
            if mode == 1 or mode == 4:
                filename = tmpdir + "/oai_archive_%s" % time.strftime(
                    "%Y%m%d_%H%M%S", time.localtime())
                oai_out = open(filename,"w")
            if mode == 2 or mode == 4:
                filename2 = tmpdir + "/oai_archive_%s_2" % time.strftime(
                    "%Y%m%d_H%M%S", time.localtime())
                oai_out2 = open(filename2,"w")

            oai_sets = get_set_descriptions(set)

            setSpec, setName, setCoverage, recID_list = \
                get_recID_list(oai_sets, set)

            i = 0
            for recID in recID_list:
                task_update_progress("[%i/%i] Set %s: done %s out of %s records." % \
                    (set_number, len(sets), setSpec, i, len(recID_list)))
                i += 1
                time.sleep(int(nice)/10)
                ID = "%d" % recID

        ### oaiIDentry validation
        ### Check if OAI identifier is already in the record or not
                add_ID_entry = True
                oaiIDentry = "<subfield code=\"%s\">oai:%s:%s</subfield>\n" % \
                    (CFG_OAI_ID_FIELD[5:6], CFG_OAI_ID_PREFIX,ID)

                query = "select b3.value from bibrec_bib%sx as br " \
                    "left join bib%sx as b3 on br.id_bibxxx=b3.id " \
                    "where b3.tag=%%s and br.id_bibrec=%%s" % \
                    (CFG_OAI_ID_FIELD[0:2], CFG_OAI_ID_FIELD[0:2])
                res = run_sql(query, (CFG_OAI_ID_FIELD, recID))
                if(res):
                    # No need to add identifier if already exists. (Check
                    # that it INDEED exist, i.e. that field is not empty)
                    for value in res:
                        if len(value) > 0 and value[0] != '':
                            add_ID_entry = False

                if add_ID_entry:
                    oaiIDentrycount += 1

                datafield_set_head = \
                    "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % \
                    (CFG_OAI_SET_FIELD[0:3],
                     CFG_OAI_SET_FIELD[3:4].replace('_', ' '),
                     CFG_OAI_SET_FIELD[4:5].replace('_', ' '))
                datafield_id_head  = \
                    "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % \
                    (CFG_OAI_ID_FIELD[0:3],
                     CFG_OAI_ID_FIELD[3:4].replace('_', ' '),
                     CFG_OAI_ID_FIELD[4:5].replace('_', ' '))

                oaisetentry = "<subfield code=\"%s\">%s</subfield>\n" % \
                    (CFG_OAI_SET_FIELD[5:6], set)
                oaisetentrycount += 1

        ### oaisetentry validation
        ### Check to which sets this record belongs
                query = "select b3.value from bibrec_bib%sx as br " \
                    "left join bib%sx as b3 on br.id_bibxxx=b3.id " \
                    "where b3.tag=%%s and br.id_bibrec=%%s" % \
                    (CFG_OAI_SET_FIELD[0:2], CFG_OAI_SET_FIELD[0:2])
                res = run_sql(query, (CFG_OAI_SET_FIELD, recID))

                remaining_sets = []
                if(res):
                    for item in res:
                        if (item[0]==set):
                            # No need to add set to metadata if already there
                            oaisetentry = ''
                            oaisetentrycount -= 1
                        elif item[0]:
                            # Collect name of the other sets to which the
                            # record must also belong (in case we are in
                            # mode == 2)
                            remaining_sets.append(item[0])

                if (mode==2):
                    # Delete mode

                    oaisetentry = ''
                    # Build sets that the record is still part of
                    for remaining_set in remaining_sets:
                        oaisetentry +=  "<subfield code=\"%s\">%s</subfield>\n" % \
                            (CFG_OAI_SET_FIELD[5:6], remaining_set)

                    if (CFG_OAI_ID_FIELD[0:5] == CFG_OAI_SET_FIELD[0:5]):
                        # Put set and OAI ID in the same datafield
                        oai_out2.write("<record>\n")
                        oai_out2.write("<controlfield tag=\"001\">%s"
                            "</controlfield>\n" % recID)
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
                        oai_out2.write("<controlfield tag=\"001\">%s"
                            "</controlfield>\n" % recID)
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
                            oai_out.write("<controlfield tag=\"001\">%s"
                                "</controlfield>\n" % recID)
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
                            oai_out.write("<controlfield tag=\"001\">%s"
                                "</controlfield>\n" % recID)
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

                # Fetch records that are currently marked with this set in
                # the database
                oai_has_list = perform_request_search(c=cdsname, p1=set,
                    f1=CFG_OAI_SET_FIELD, m1="e", ap=0)

                # Fetch records that should not be in this set
                # (oai_has_list - recID_list)
                records_to_update = [rec_id for rec_id in oai_has_list \
                                     if not rec_id in recID_list]



                datafield_set_head = "<datafield tag=\"%s\" ind1=\"%s\"" \
                    " ind2=\"%s\">" % (CFG_OAI_SET_FIELD[0:3], \
                    CFG_OAI_SET_FIELD[3:4].replace('_', ' '), \
                    CFG_OAI_SET_FIELD[4:5].replace('_', ' '))
                datafield_id_head  = "<datafield tag=\"%s\" ind1=\"%s\"" \
                    " ind2=\"%s\">" % (CFG_OAI_ID_FIELD[0:3], \
                    CFG_OAI_ID_FIELD[3:4].replace('_', ' '), \
                    CFG_OAI_ID_FIELD[4:5].replace('_', ' '))

                for recID in records_to_update:
                    oaiIDentry = "<subfield code=\"%s\">oai:%s:%s</subfield>\n" % \
                        (CFG_OAI_ID_FIELD[5:6], CFG_OAI_ID_PREFIX, recID)

                    ### Check to which sets this record belongs
                    query = "select b3.value from bibrec_bib%sx as br " \
                        "left join bib%sx as b3 on br.id_bibxxx=b3.id " \
                        "where b3.tag=%%s and br.id_bibrec=%%s" % \
                        (CFG_OAI_SET_FIELD[0:2], CFG_OAI_SET_FIELD[0:2])
                    res = run_sql(query, (CFG_OAI_SET_FIELD, recID))
                    oaisetentry = ''
                    for in_set in res:
                        if in_set[0] != set:
                            oaisetentry +=  "<subfield code=\"%s\">%s" \
                                "</subfield>\n" % \
                                (CFG_OAI_SET_FIELD[5:6], in_set[0])

                    if (CFG_OAI_ID_FIELD[0:5] == CFG_OAI_SET_FIELD[0:5]):
                        # Put set and OAI ID in the same datafield
                        oai_out2.write("<record>\n")
                        oai_out2.write("<controlfield tag=\"001\">%s"
                            "</controlfield>\n" % recID)
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
                        oai_out2.write("<controlfield tag=\"001\">%s"
                            "</controlfield>\n" % recID)
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
            if (mode == 1 or mode == 4) and oaisetentrycount > 0:
                # Check if file is empty or not:
                len_file = os.stat(filename)[ST_SIZE]
                if len_file > 0:
                    command = "%s/bibupload -a %s" % (bindir, filename)
                    os.system(command)
            if mode == 2 or mode == 4:
                # Check if file is empty or not:
                len_file = os.stat(filename2)[ST_SIZE]
                if len_file > 0:
                    command = "%s/bibupload -c %s" % (bindir, filename2)
                    os.system(command)

    return True

#########################

def main():
    """Main that construct all the bibtask."""
    task_set_option('upload', 0)
    task_set_option('mode', 0)
    task_set_option('oaiset', 0)
    task_set_option('nice', 0)
    task_init(authorization_action='runoaiarchive',
            authorization_msg="OAI Archive Task Submission",
            description="Examples:\n"
                " Expose set 'setSpec' via OAI repository gateway\n"
                " oaiarchive --oaiset='setSpec' --add --upload\n"
                " oaiarchive -apo 'setSpec'\n\n"
                " Expose multiple sets via OAI repository gateway\n"
                " oaiarchive --oaiset='setSpec1 setSpec2 setSpec3' --add --upload\n"
                " oaiarchive -apo 'setSpec1 setSpec2 setSpec3'\n\n"
                " Remove records defined by 'setSpec' from OAI repository\n"
                " oaiarchive --oaiset='setSpec' --delete --upload\n"
                " oaiarchive -dpo 'setSpec'\n\n"
                " Expose entire repository via OAI gateway\n"
                " oaiarchive --set=global --add --upload\n"
                " oaiarchive -apo global\n\n"
                " Print OAI set status\n"
                " oaiarchive --oaiset='setSpec' --info\n"
                " oaiarchive -io 'setSpec'\n\n"
                " Print OAI repository status\n"
                " oaiarchive -r\n\n",
            help_specific_usage="Options:\n"
                "  -o --oaiset=    Specify setSpec(s) (whitespace separated list of setSpecs) to expose via OAI\n"
                "Modes\n"
                "  -a --add        Add records to OAI repository\n"
                "  -d --delete     Remove records from OAI repository\n"
                "  -r --report OAI repository status\n"
                "  -i --info       Give info about OAI set (default)\n"
                "Additional parameters:\n"
                "  -p --upload     Upload records\n",
            version=__revision__,
            specific_params=("ado:pirn", [
                "add",
                "delete",
                "oaiset=",
                "upload",
                "info",
                "report",
                "no-process"]),
            task_submit_elaborate_specific_parameter_fnc=
                task_submit_elaborate_specific_parameter,
            task_run_fnc=oaiarchive_task)

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """Elaborate specific CLI parameters of oaiarchive"""
    if key in ("-n", "--nice"):
        task_set_option("nice", value)
    elif key in ("-o", "--oaiset"):
        sets = [set for set in value.split(' ') if set != '']
        task_set_option("oaiset", sets)
    elif key in ("-a", "--add"):
        task_set_option("mode", 1)
    elif key in ("-d", "--delete"):
        task_set_option("mode", 2)
    elif key in ("-c", "--clean"):
        task_set_option("mode", 4)
    elif key in ("-p", "--upload"):
        task_set_option("upload", 1)
    elif key in ("-i", "--info"):
        task_set_option("mode", 0)
    elif key in ("-r", "--report"):
        task_set_option("mode", 3)
    elif key in ("-n", "--no-process"):
        task_set_option("upload", 0)
    else:
        return False
    return True

### okay, here we go:
if __name__ == '__main__':
    main()
