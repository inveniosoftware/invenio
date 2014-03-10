## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""OAI Repository administration tool -

   Updates the metadata of the records to include OAI identifiers and
   OAI SetSpec according to the settings defined in OAI Repository
   admin interface

"""

import os
import sys
import time

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from tempfile import mkstemp
from pprint import pformat

from invenio.config import \
     CFG_OAI_ID_FIELD, \
     CFG_OAI_ID_PREFIX, \
     CFG_OAI_SET_FIELD, \
     CFG_OAI_PREVIOUS_SET_FIELD, \
     CFG_SITE_NAME, \
     CFG_TMPSHAREDDIR
from invenio.oai_repository_config import CFG_OAI_REPOSITORY_MARCXML_SIZE, \
     CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC
from invenio.search_engine import perform_request_search, get_record, search_unit_in_bibxxx
from invenio.intbitset import intbitset
from invenio.dbquery import run_sql
from invenio.bibtask import \
     task_get_option, \
     task_set_option, \
     write_message, \
     task_update_progress, \
     task_init, \
     task_sleep_now_if_required, \
     task_low_level_submission
from invenio.bibrecord import \
     record_get_field_value, \
     record_get_field_values, \
     record_add_field, \
     record_xml_output

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
    Returns the list (as intbitset) of recids belonging to 'set'

    Parameters:

      set_spec - *str* the set_spec for which we would like to get the
                 recids
    """
    recids = intbitset()

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

        recids |= intbitset(new_recids)

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

def print_repository_status(local_write_message=write_message,
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
    repository_recids_after_update = intbitset()

    local_write_message(CFG_SITE_NAME)
    local_write_message(" OAI Repository Status")

    set_spec_max_length = 19 # How many max char do we display for
    set_name_max_length = 20 # setName and setSpec?

    if verbose == 0:
        # Just print repository size
        local_write_message("  Total(**)" + " " * 29 +
                      " " * (9 - len(repository_size_s)) + repository_size_s)
        return
    elif verbose == 1:
        # We display few information: show longer set name and spec
        set_spec_max_length = 30
        set_name_max_length = 30

    local_write_message("=" * 80)
    header = "  setSpec" + " " * (set_spec_max_length - 7) + \
             "  setName" + " " * (set_name_max_length - 5) + " Volume"
    if verbose > 1:
        header += " " * 5 + "After update(*):"
    local_write_message(header)

    if verbose > 1:
        local_write_message(" " * 57 + "Additions  Deletions")

    local_write_message("-" * 80)

    for set_spec in all_set_specs():

        if verbose <= 1:
            # Get the records that are in this set. This is an
            # incomplete check, as it can happen that some records are
            # in this set (according to the metadata) but have no OAI
            # ID (so they are not exported). This can happen if the
            # repository has some records coming from external
            # sources, or if it has never been synchronized with this
            # tool.
            current_recids = get_recids_for_set_spec(set_spec)
            nb_current_recids = len(current_recids)
        else:
            # Get the records that are *currently* exported for this
            # setSpec
            current_recids = search_unit_in_bibxxx(p=set_spec, f=CFG_OAI_SET_FIELD, type='e')
            nb_current_recids = len(current_recids)
            # Get the records that *should* be in this set according to
            # the admin defined settings, and compute how many should be
            # added or removed
            should_recids = get_recids_for_set_spec(set_spec)
            repository_recids_after_update |= should_recids

            nb_add_recids = len(should_recids -  current_recids)
            nb_remove_recids = len(current_recids - should_recids)
            nb_should_recids = len(should_recids)


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
        local_write_message(row)

    local_write_message("=" * 80)
    footer = "  Total(**)" + " " * (set_spec_max_length + set_name_max_length - 7) + \
             " " * (9 - len(repository_size_s)) + repository_size_s
    if verbose > 1:
        footer += ' ' * (28 - len(str(len(repository_recids_after_update)))) + str(len(repository_recids_after_update))
    local_write_message(footer)

    if verbose > 1:
        local_write_message('  *The "after update" columns show the repository after you run this tool.')
    else:
        local_write_message(' *"Volume" is indicative if repository is out of sync. Use --detailed-report.')
    local_write_message('**The "total" is not the sum of the above numbers, but the union of the records.')

def repository_size():
    """Read repository size"""
    return len(search_unit_in_bibxxx(p="*", f=CFG_OAI_SET_FIELD, type="e"))

### MAIN ###
def oairepositoryupdater_task():
    """Main business logic code of oai_archive"""
    no_upload = task_get_option("no_upload")
    report = task_get_option("report")

    if report > 1:
        print_repository_status(verbose=report)
        return True

    if run_sql("SELECT id FROM schTASK WHERE proc='bibupload:oairepository' AND status='WAITING'"):
        write_message("Previous requests of oairepository still being elaborated. Let's skip this execution.")
        return True

    initial_snapshot = {}
    for set_spec in all_set_specs():
        initial_snapshot[set_spec] = get_set_definitions(set_spec)
    write_message("Initial set snapshot: %s" % pformat(initial_snapshot), verbose=2)

    task_update_progress("Fetching records to process")

    recids_with_oaiid = search_unit_in_bibxxx(p='*', f=CFG_OAI_ID_FIELD, type='e')
    write_message("%s recids have an OAI ID" % len(recids_with_oaiid), verbose=2)

    all_current_recids = search_unit_in_bibxxx(p='*', f=CFG_OAI_SET_FIELD, type='e')
    no_more_exported_recids = intbitset(all_current_recids)
    write_message("%s recids are currently exported" % (len(all_current_recids)), verbose=2)

    all_affected_recids = intbitset()
    all_should_recids = intbitset()
    recids_for_set = {}
    for set_spec in all_set_specs():
        if not set_spec:
            set_spec = CFG_OAI_REPOSITORY_GLOBAL_SET_SPEC
        should_recids = get_recids_for_set_spec(set_spec)
        recids_for_set[set_spec] = should_recids
        no_more_exported_recids -= should_recids
        all_should_recids |= should_recids
        current_recids = search_unit_in_bibxxx(p=set_spec, f=CFG_OAI_SET_FIELD, type='e')
        write_message("%s recids should be in %s. Currently %s are in %s" % (len(should_recids), set_spec, len(current_recids), set_spec), verbose=2)
        to_add = should_recids - current_recids
        write_message("%s recids should be added to %s" % (len(to_add), set_spec), verbose=2)
        to_remove = current_recids - should_recids
        write_message("%s recids should be removed from %s" % (len(to_remove), set_spec), verbose=2)
        affected_recids = to_add | to_remove
        write_message("%s recids should be hence updated for %s" % (len(affected_recids), set_spec), verbose=2)
        all_affected_recids |= affected_recids

    missing_oaiid = all_should_recids - recids_with_oaiid
    write_message("%s recids are missing an oaiid" % len(missing_oaiid))
    write_message("%s recids should no longer be exported" % len(no_more_exported_recids))

    ## Let's add records with missing OAI ID
    all_affected_recids |= missing_oaiid | no_more_exported_recids
    write_message("%s recids should updated" % (len(all_affected_recids)), verbose=2)

    if not all_affected_recids:
        write_message("Nothing to do!")
        return True

    # Prepare to save results in a tmp file
    (fd, filename) = mkstemp(dir=CFG_TMPSHAREDDIR,
                                  prefix='oairepository_' + \
                                  time.strftime("%Y%m%d_%H%M%S_",
                                                time.localtime()))
    oai_out = os.fdopen(fd, "w")
    oai_out.write("<collection>")

    tot = 0
    # Iterate over the recids
    for i, recid in enumerate(all_affected_recids):
        task_sleep_now_if_required(can_stop_too=True)
        task_update_progress("Done %s out of %s records." % \
                             (i, len(all_affected_recids)))

        write_message("Elaborating recid %s" % recid, verbose=3)
        record = get_record(recid)
        if not record:
            write_message("Record %s seems empty. Let's skip it." % recid, verbose=3)
            continue
        new_record = {}

        # Check if an OAI identifier is already in the record or
        # not.
        assign_oai_id_entry = False
        oai_id_entry = record_get_field_value(record, tag=CFG_OAI_ID_FIELD[:3], ind1=CFG_OAI_ID_FIELD[3], ind2=CFG_OAI_ID_FIELD[4], code=CFG_OAI_ID_FIELD[5])
        if not oai_id_entry:
            assign_oai_id_entry = True
            oai_id_entry = "oai:%s:%s" % (CFG_OAI_ID_PREFIX, recid)
            write_message("Setting new oai_id %s for record %s" % (oai_id_entry, recid), verbose=3)
        else:
            write_message("Already existing oai_id %s for record %s" % (oai_id_entry, recid), verbose=3)

        # Get the sets to which this record already belongs according
        # to the metadata
        current_oai_sets = set(record_get_field_values(record, tag=CFG_OAI_SET_FIELD[:3], ind1=CFG_OAI_SET_FIELD[3], ind2=CFG_OAI_SET_FIELD[4], code=CFG_OAI_SET_FIELD[5]))
        write_message("Record %s currently belongs to these oai_sets: %s" % (recid, ", ".join(current_oai_sets)), verbose=3)

        current_previous_oai_sets = set(record_get_field_values(record, tag=CFG_OAI_PREVIOUS_SET_FIELD[:3], ind1=CFG_OAI_PREVIOUS_SET_FIELD[3], ind2=CFG_OAI_PREVIOUS_SET_FIELD[4], code=CFG_OAI_PREVIOUS_SET_FIELD[5]))
        write_message("Record %s currently doesn't belong anymore to these oai_sets: %s" % (recid, ", ".join(current_previous_oai_sets)), verbose=3)

        # Get the sets that should be in this record according to
        # settings
        updated_oai_sets = set(_set for _set, _recids in recids_for_set.iteritems()
             if recid in _recids)
        write_message("Record %s now belongs to these oai_sets: %s" % (recid, ", ".join(updated_oai_sets)), verbose=3)

        updated_previous_oai_sets = set(_set for _set in (current_previous_oai_sets - updated_oai_sets) |
             (current_oai_sets - updated_oai_sets))
        write_message("Record %s now doesn't belong anymore to these oai_sets: %s" % (recid, ", ".join(updated_previous_oai_sets)), verbose=3)

        # Ok, we have the old sets and the new sets. If they are equal
        # and oai ID does not need to be added, then great, nothing to
        # change . Otherwise apply the new sets.
        if current_oai_sets == updated_oai_sets and not assign_oai_id_entry:
            write_message("Nothing has changed for record %s, let's move on!" % recid, verbose=3)
            continue # Jump to next recid

        write_message("Something has changed for record %s, let's update it!" % recid, verbose=3)
        subfields = [(CFG_OAI_ID_FIELD[5], oai_id_entry)]
        for oai_set in updated_oai_sets:
            subfields.append((CFG_OAI_SET_FIELD[5], oai_set))
        for oai_set in updated_previous_oai_sets:
            subfields.append((CFG_OAI_PREVIOUS_SET_FIELD[5], oai_set))

        record_add_field(new_record, tag="001", controlfield_value=str(recid))
        record_add_field(new_record, tag=CFG_OAI_ID_FIELD[:3], ind1=CFG_OAI_ID_FIELD[3], ind2=CFG_OAI_ID_FIELD[4], subfields=subfields)
        oai_out.write(record_xml_output(new_record))
        tot += 1
        if tot == CFG_OAI_REPOSITORY_MARCXML_SIZE:
            oai_out.write("</collection>")
            oai_out.close()
            write_message("Wrote to file %s" % filename)
            if not no_upload:
                if task_get_option("notimechange"):
                    task_low_level_submission('bibupload', 'oairepository', '-c', filename, '-n', '-Noairepository', '-P', '-1')
                else:
                    task_low_level_submission('bibupload', 'oairepository', '-c', filename, '-Noairepository', '-P', '-1')
            # Prepare to save results in a tmp file
            (fd, filename) = mkstemp(dir=CFG_TMPSHAREDDIR,
                                        prefix='oairepository_' + \
                                        time.strftime("%Y%m%d_%H%M%S_",
                                                        time.localtime()))
            oai_out = os.fdopen(fd, "w")
            oai_out.write("<collection>")
            tot = 0
            task_sleep_now_if_required(can_stop_too=True)

    oai_out.write("</collection>")
    oai_out.close()
    write_message("Wrote to file %s" % filename)

    if tot > 0:
        if not no_upload:
            task_sleep_now_if_required(can_stop_too=True)
            if task_get_option("notimechange"):
                task_low_level_submission('bibupload', 'oairepository', '-c', filename, '-n')
            else:
                task_low_level_submission('bibupload', 'oairepository', '-c', filename)
    else:
        os.remove(filename)

    return True

#########################

def main():
    """Main that construct all the bibtask."""

    # if there is any -r or --report option (or other similar options)
    # in the arguments, just print the status and exit (do not run
    # through BibSched...)
    if (CFG_OAI_ID_FIELD[:5] != CFG_OAI_SET_FIELD[:5]) or \
            (CFG_OAI_ID_FIELD[:5] != CFG_OAI_PREVIOUS_SET_FIELD[:5]):
        print >> sys.stderr, """\
ERROR: since Invenio 1.0 the OAI ID and the OAI Set must be stored in the same
field. Please revise your configuration for the variables
    CFG_OAI_ID_FIELD (currently set to %s)
    CFG_OAI_SET_FIELD (currently set to %s)
    CFG_OAI_PREVIOUS_SET_FIELD (currently set to %s)""" % (
            CFG_OAI_ID_FIELD,
            CFG_OAI_SET_FIELD,
            CFG_OAI_PREVIOUS_SET_FIELD
        )
        sys.exit(1)
    mode = -1
    if '-d' in sys.argv[1:] or '--detailed-report' in sys.argv[1:]:
        mode = 2
    elif '-r' in sys.argv[1:] or '--report' in sys.argv[1:]:
        mode = 1

    if mode != -1:
        def local_write_message(*args):
            """Overload BibTask function so that it does not need to
            run in BibSched environment"""
            sys.stdout.write(args[0] + '\n')
        print_repository_status(local_write_message=local_write_message, verbose=mode)
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
                " -n --no-process\tDo no upload the modifications\n"
                " --notimechange\tDo not update record modification_date\n"
                "NOTE: --notimechange should be used with care, basically only the first time a new set is added.",
            specific_params=("rdn", [
                "report",
                "detailed-report",
                "no-process",
                "notimechange"]),
            task_submit_elaborate_specific_parameter_fnc=
                task_submit_elaborate_specific_parameter,
            task_run_fnc=oairepositoryupdater_task)

def task_submit_elaborate_specific_parameter(key, _value, _opts, _args):
    """Elaborate specific CLI parameters of oairepositoryupdater"""
    if key in ("-r", "--report"):
        task_set_option("report", 1)
    if key in ("-d", "--detailed-report"):
        task_set_option("report", 2)
    elif key in ("-n", "--no-process"):
        task_set_option("no_upload", 1)
    elif key in ("--notimechange",):
        task_set_option("notimechange", 1)
    else:
        return False
    return True

### okay, here we go:
if __name__ == '__main__':
    main()
