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

"""OAI Repository administration tool -

   Updates the metadata of the records to include OAI identifiers and
   OAI SetSpec according to the settings defined in OAI Repository
   admin interface

"""

__revision__ = "$Id$"

import os
import sys
import time

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from stat import ST_SIZE
from tempfile import mkstemp

from invenio.config import \
     CFG_OAI_ID_FIELD, \
     CFG_OAI_ID_PREFIX, \
     CFG_OAI_SET_FIELD, \
     CFG_BINDIR, \
     CFG_SITE_NAME, \
     CFG_TMPDIR
from invenio.search_engine import \
     perform_request_search, \
     get_fieldvalues, \
     get_record
from invenio.intbitset import intbitset as HitSet
from invenio.dbquery import run_sql
from invenio.bibtask import \
     task_get_option, \
     task_set_option, \
     write_message, \
     task_update_progress, \
     task_init, \
     task_sleep_now_if_required
from invenio.bibrecord import \
     record_delete_subfield, \
     field_xml_output

DATAFIELD_SET_HEAD = \
                   "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % \
                   (CFG_OAI_SET_FIELD[0:3],
                    CFG_OAI_SET_FIELD[3:4].replace('_', ' '),
                    CFG_OAI_SET_FIELD[4:5].replace('_', ' '))
DATAFIELD_ID_HEAD  = \
                  "<datafield tag=\"%s\" ind1=\"%s\" ind2=\"%s\">" % \
                  (CFG_OAI_ID_FIELD[0:3],
                   CFG_OAI_ID_FIELD[3:4].replace('_', ' '),
                   CFG_OAI_ID_FIELD[4:5].replace('_', ' '))

def get_set_definitions(set_spec):
    """
    Retrieve set definitions from oaiREPOSITORY table.

    The set definitions are the search patterns that define the records
    which are in the set
    """
    set_definitions = []

    query = "select setName, setDefinition from oaiREPOSITORY where setSpec=%s"
    res = run_sql(query, (set_spec, ))

    for (set_name, set_definition) in res:
        params = parse_set_definition(set_definition)
        params['setSpec'] = set_spec
        params['setName'] = set_name
        set_definitions.append(params)
    return set_definitions

def parse_set_definition(set_definition):
    """
    Returns the parameters for the given set definition.

    The returned structure is a dictionary with keys being
    c, p1, f1, m1, p2, f2, m2, p3, f3, m3 and corresponding values

    @param set_definition: a string as returned by the database for column 'setDefinition'
    @return: a dictionary
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

def all_set_specs():
    """
    Returns the list of (distinct) setSpecs defined in the settings.
    This also include the "empty" setSpec if any setting uses it.

    Note: there can be several times the same setSpec in the settings,
    given that a setSpec might be defined by several search
    queries. Here we return distinct values
    """
    query = "SELECT DISTINCT setSpec FROM oaiREPOSITORY"
    res = run_sql(query)

    return [row[0] for row in res]

def get_recids_for_set_spec(set_spec):
    """
    Returns the list (as HitSet) of recids belonging to 'set'

    Parameters:

      set_spec - *str* the set_spec for which we would like to get the
                 recids
    """
    recids = HitSet()

    for set_def in get_set_definitions(set_spec):
        new_recids = perform_request_search(c=[coll.strip() \
                                               for coll in set_def['c'].split(',')],
                                            p1=set_def['p1'],
                                            f1=set_def['f1'],
                                            m1=set_def['m1'],
                                            op1=set_def['op1'],
                                            p2=set_def['p2'],
                                            f2=set_def['f2'],
                                            m2=set_def['m2'],
                                            op2=set_def['op2'],
                                            p3=set_def['p3'],
                                            f3=set_def['f3'],
                                            m3=set_def['m3'],
                                            ap=0)

        recids = recids.union(HitSet(new_recids))

    return recids

def get_set_name_for_set_spec(set_spec):
    """
    Returns the OAI setName of a setSpec.

    Note that the OAI Repository admin lets the user add several set
    definition with the same setSpec, and possibly with different
    setNames... -> Returns the first (non empty) one found.

    Parameters:

      set_spec - *str* the set_spec for which we would like to get the
                 setName
    """
    query = "select setName from oaiREPOSITORY where setSpec=%s and setName!=''"
    res = run_sql(query, (set_spec, ))
    if len(res) > 0:
        return res[0][0]
    else:
        return ""

def print_repository_status(write_message=write_message,
                            verbose=0):
    """
    Prints the repository status to the standard output.

    Parameters:

      write_message - *function* the function used to write the output

            verbose - *int* the verbosity of the output
                       - 0: print repository size
                       - 1: print quick status of each set (numbers
                         can be wrong if the repository is in some
                         inconsistent state, i.e. a record is in an
                         OAI setSpec but has not OAI ID)
                       - 2: print detailed status of repository, with
                         number of records that needs to be
                         synchronized according to the sets
                         definitions. Precise, but ~slow...
    """
    repository_size_s = "%d" % repository_size()
    repository_recids_after_update = HitSet()

    write_message(CFG_SITE_NAME)
    write_message(" OAI Repository Status")

    set_spec_max_length = 19 # How many max char do we display for
    set_name_max_length = 20 # setName and setSpec?

    if verbose == 0:
        # Just print repository size
        write_message("  Total(**)" + " " * 29 +
                      " " * (9 - len(repository_size_s)) + repository_size_s)
        return
    elif verbose == 1:
        # We display few information: show longer set name and spec
        set_spec_max_length = 30
        set_name_max_length = 30

    write_message("=" * 80)
    header = "  setSpec" + " " * (set_spec_max_length - 7) + \
             "  setName" + " " * (set_name_max_length - 5) + " Volume"
    if verbose > 1:
        header += " " * 5 + "After update(*):"
    write_message(header)

    if verbose > 1:
        write_message(" " * 57 + "Additions  Deletions")

    write_message("-" * 80)

    for set_spec in all_set_specs():

        if verbose <= 1:
            # Get the records that are in this set. This is an
            # incomplete check, as it can happen that some records are
            # in this set (according to the metadata) but have no OAI
            # ID (so they are not exported). This can happen if the
            # repository has some records coming from external
            # sources, or if it has never been synchronized with this
            # tool.
            current_recids = perform_request_search(c=CFG_SITE_NAME,
                                                    p1=set_spec,
                                                    f1=CFG_OAI_SET_FIELD,
                                                    m1="e", ap=0)
            nb_current_recids = len(current_recids)
        else:
            # Get the records that are *currently* exported for this
            # setSpec
            current_recids = perform_request_search(c=CFG_SITE_NAME,
                                                    p1=set_spec,
                                                    f1=CFG_OAI_SET_FIELD,
                                                    m1="e", ap=0, op1="a",
                                                    p2="oai:*",
                                                    f2=CFG_OAI_ID_FIELD,
                                                    m2="e")
            nb_current_recids = len(current_recids)
            # Get the records that *should* be in this set according to
            # the admin defined settings, and compute how many should be
            # added or removed
            should_recids = get_recids_for_set_spec(set_spec)
            repository_recids_after_update = repository_recids_after_update.union(should_recids)

            nb_add_recids = len(HitSet(should_recids).difference(HitSet(current_recids)))
            nb_remove_recids = len(HitSet(current_recids).difference(HitSet(should_recids)))
            nb_should_recids = len(should_recids)
            nb_recids_after_update = len(repository_recids_after_update)


        # Adapt setName and setSpec strings lengths
        set_spec_str = set_spec
        if len(set_spec_str) > set_spec_max_length :
            set_spec_str = "%s.." % set_spec_str[:set_spec_max_length]
        set_name_str = get_set_name_for_set_spec(set_spec)
        if len(set_name_str) > set_name_max_length :
            set_name_str = "%s.." % set_name_str[:set_name_max_length]

        row = "  " + set_spec_str + \
               " " * ((set_spec_max_length + 2) - len(set_spec_str)) + set_name_str + \
               " " * ((set_name_max_length + 2) - len(set_name_str)) + \
               " " * (7 - len(str(nb_current_recids))) + str(nb_current_recids)
        if verbose > 1:
            row += \
                " " * max(9 - len(str(nb_add_recids)), 0) + '+' + str(nb_add_recids) + \
                " " * max(7 - len(str(nb_remove_recids)), 0) + '-' + str(nb_remove_recids) + " = " +\
                " " * max(7 - len(str(nb_should_recids)), 0) + str(nb_should_recids)
        write_message(row)

    write_message("=" * 80)
    footer = "  Total(**)" + " " * (set_spec_max_length + set_name_max_length - 7) + \
             " " * (9 - len(repository_size_s)) + repository_size_s
    if verbose > 1:
        footer += ' ' * (28 - len(str(nb_recids_after_update))) + str(nb_recids_after_update)
    write_message(footer)

    if verbose > 1:
        write_message('  *The "after update" columns show the repository after you run this tool.')
    else:
        write_message(' *"Volume" is indicative if repository is out of sync. Use --detailed-report.')
    write_message('**The "total" is not the sum of the above numbers, but the union of the records.')

def repository_size():
    "Read repository size"
    return len(perform_request_search(p1="oai:*",
                                      f1=CFG_OAI_ID_FIELD,
                                      m1="e",
                                      ap=0))

### MAIN ###

def oairepositoryupdater_task():
    """Main business logic code of oai_archive"""
    no_upload = task_get_option("no_upload")
    report = task_get_option("report")

    if report > 1:
        print_repository_status(verbose=report)
        return True

    task_update_progress("Fetching records to process")

    # Build the list of records to be processed, that is, search for
    # the records that match one of the search queries defined in OAI
    # Repository admin interface.
    recids_for_set = {} # Remember exactly which record belongs to which set
    recids = HitSet() # "Flat" set of the recids_for_set values
    for set_spec in all_set_specs():
        task_sleep_now_if_required(can_stop_too=True)
        _recids = get_recids_for_set_spec(set_spec)
        recids_for_set[set_spec] = _recids
        recids = recids.union(_recids)

    # Also get the list of records that are currently exported through
    # OAI and that might need to be refreshed
    oai_recids = perform_request_search(c=CFG_SITE_NAME,
                                        p1='oai:%s:*' % CFG_OAI_ID_PREFIX,
                                        f1=CFG_OAI_ID_FIELD,
                                        m1="e", ap=0)
    recids = recids.union(HitSet(oai_recids))

    # Prepare to save results in a tmp file
    (fd, filename) = mkstemp(dir=CFG_TMPDIR,
                                  prefix='oairepository_' + \
                                  time.strftime("%Y%m%d_%H%M%S_",
                                                time.localtime()))
    oai_out = os.fdopen(fd, "w")

    # Iterate over the recids
    i = 0
    for recid in recids:
        i += 1
        task_sleep_now_if_required(can_stop_too=True)
        task_update_progress("Done %s out of %s records." % \
                             (i, len(recids)))

        # Check if an OAI identifier is already in the record or
        # not.
        oai_id_entry = ""
        oai_ids = [_oai_id for _oai_id in \
                   get_fieldvalues(recid, CFG_OAI_ID_FIELD) \
                   if _oai_id.strip() != '']
        if len(oai_ids) == 0:
            oai_id_entry = "<subfield code=\"%s\">oai:%s:%s</subfield>\n" % \
                         (CFG_OAI_ID_FIELD[5:6], CFG_OAI_ID_PREFIX, recid)

        # Get the sets to which this record already belongs according
        # to the metadata
        current_oai_sets = set(\
            [_oai_set for _oai_set in \
             get_fieldvalues(recid, CFG_OAI_SET_FIELD) \
             if _oai_set.strip() != ''])

        # Get the sets that should be in this record according to
        # settings
        updated_oai_sets = set(\
            [_set for _set, _recids in recids_for_set.iteritems()
             if recid in _recids])

        # Ok, we have the old sets and the new sets. If they are equal
        # and oai ID does not need to be added, then great, nothing to
        # change . Otherwise apply the new sets.
        if current_oai_sets == updated_oai_sets and not oai_id_entry:
            continue # Jump to next recid

        # Generate the xml sets entry
        oai_set_entry = '\n'.join(["<subfield code=\"%s\">%s</subfield>" % \
                                 (CFG_OAI_SET_FIELD[5:6], _oai_set) \
                                 for _oai_set in updated_oai_sets]) + \
                                 "\n"

        # Also get all the datafields with tag and indicator matching
        # CFG_OAI_SET_FIELD[:5] and CFG_OAI_ID_FIELD[:5] but with
        # subcode != CFG_OAI_SET_FIELD[5:6] and subcode !=
        # CFG_OAI_SET_FIELD[5:6], so that we can preserve these values
        other_data = marcxml_filter_out_tags(recid, [CFG_OAI_SET_FIELD,
                                                     CFG_OAI_ID_FIELD])

        if oai_id_entry or oai_set_entry:
            if CFG_OAI_ID_FIELD[0:5] == CFG_OAI_SET_FIELD[0:5]:
                # Put set and OAI ID in the same datafield
                oai_out.write("<record>\n")
                oai_out.write("<controlfield tag=\"001\">%s"
                    "</controlfield>\n" % recid)
                oai_out.write(DATAFIELD_ID_HEAD)
                oai_out.write("\n")
                #if oai_id_entry:
                oai_out.write(oai_id_entry)
                #if oai_set_entry:
                oai_out.write(oai_set_entry)
                oai_out.write("</datafield>\n")
                oai_out.write(other_data)
                oai_out.write("</record>\n")
            else:
                oai_out.write("<record>\n")
                oai_out.write("<controlfield tag=\"001\">%s"
                    "</controlfield>\n" % recid)
                if oai_id_entry:
                    oai_out.write(DATAFIELD_ID_HEAD)
                    oai_out.write("\n")
                    oai_out.write(oai_id_entry)
                    oai_out.write("</datafield>\n")
                if oai_set_entry:
                    oai_out.write(DATAFIELD_SET_HEAD)
                    oai_out.write("\n")
                    oai_out.write(oai_set_entry)
                    oai_out.write("</datafield>\n")
                oai_out.write(other_data)
                oai_out.write("</record>\n")

    oai_out.close()
    write_message("Wrote to file %s" % filename)

    if not no_upload:
        task_sleep_now_if_required(can_stop_too=True)
        # Check if file is empty or not:
        len_file = os.stat(filename)[ST_SIZE]
        if len_file > 0:
            command = "%s/bibupload -c %s -u oairepository" % (CFG_BINDIR, filename)
            os.system(command)
        else:
            os.remove(filename)

    return True

def marcxml_filter_out_tags(recid, fields):
    """
    Returns the fields of record 'recid' that share the same tag and
    indicators as those specified in 'fields', but for which the
    subfield is different. This is nice to emulate a bibupload -c that
    corrects only specific subfields.

    Parameters:
           recid - *int* the id of the record to process

          fields - *list(str)* the list of fields that we want to filter
                   out. Eg ['909COp', '909COo']
    """
    out = ''

    record = get_record(recid)

    # Delete subfields that we want to replace
    for field in fields:
        record_delete_subfield(record,
                               tag=field[0:3],
                               ind1=field[3:4],
                               ind2=field[4:5],
                               subfield_code=field[5:6])

    # Select only datafields that share tag + indicators
    processed_tags_and_ind = []
    for field in fields:
        if not field[0:5] in processed_tags_and_ind:
            # Ensure that we do not process twice the same datafields
            processed_tags_and_ind.append(field[0:5])
            for datafield in record[field[0:3]]:
                if datafield[1] == field[3:4] and \
                       datafield[2] == field[4:5]:
                    out += field_xml_output(datafield, field[0:3])

    return out

#########################

def main():
    """Main that construct all the bibtask."""

    # if there is any -r or --report option (or other similar options)
    # in the arguments, just print the status and exit (do not run
    # through BibSched...)
    mode = -1
    if '-d' in sys.argv[1:] or '--detailed-report' in sys.argv[1:]:
        mode = 2
    elif '-r' in sys.argv[1:] or '--report' in sys.argv[1:]:
        mode = 1

    if mode != -1:
        def write_message(*args):
            """Overload BibTask function so that it does not need to
            run in BibSched environment"""
            sys.stdout.write(args[0] + '\n')
        print_repository_status(write_message=write_message,
                                verbose=mode)
        return

    task_init(authorization_action='runoairepository',
            authorization_msg="OAI Archive Task Submission",
            description="Examples:\n"
                " Expose records according to sets defined in OAI Repository admin interface\n"
                "   $ oairepositoryupdater \n"
                " Expose records according to sets defined in OAI Repository admin interface and update them every day\n"
                "   $ oairepositoryupdater -s24\n"
                " Print OAI repository status\n"
                "   $ oairepositoryupdater -r\n"
                " Print OAI repository detailed status\n"
                "   $ oairepositoryupdater -d\n\n",
            help_specific_usage="Options:\n"
                " -r --report\t\tOAI repository status\n"
                " -d --detailed-report\t\tOAI repository detailed status\n"
                " -n --no-process\tDo no upload the modifications\n",
            version=__revision__,
            specific_params=("rdn", [
                "report",
                "detailed-report",
                "no-process"]),
            task_submit_elaborate_specific_parameter_fnc=
                task_submit_elaborate_specific_parameter,
            task_run_fnc=oairepositoryupdater_task)

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """Elaborate specific CLI parameters of oairepositoryupdater"""
    if key in ("-r", "--report"):
        task_set_option("report", 1)
    if key in ("-d", "--detailed-report"):
        task_set_option("report", 2)
    elif key in ("-n", "--no-process"):
        task_set_option("no_upload", 1)
    else:
        return False
    return True

### okay, here we go:
if __name__ == '__main__':
    main()
