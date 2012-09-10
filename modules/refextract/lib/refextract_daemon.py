# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""Initialise Refextract task
"""
import sys, os, time
from shutil import copyfile
from invenio.bibtask import task_init, task_set_option, \
                            task_get_option, write_message, \
                            task_has_option, task_get_task_param
from invenio.config import CFG_VERSION, CFG_TMPDIR, CFG_BINDIR, CFG_ETCDIR
from invenio.dbquery import run_sql
## Used to create a new record object, to obtain fulltexts
from invenio.bibdocfile import BibRecDocs
## Used to obtain the fulltexts for a given collection
from invenio.search_engine import get_collection_reclist
## begin_extraction() is the beginning method of extracting references,
## given that either standalone or non-standlone methods have been selected
from invenio.refextract import begin_extraction
## Help message is the usage() print out of how to use Refextract
from invenio.refextract import help_message
from invenio.refextract_config import CFG_REFEXTRACT_JOB_FILE_PARAMS

from tempfile import mkstemp

try:
    ## Used to obtain the file-type of input documents
    from invenio.config import CFG_PATH_GFILE
except ImportError:
    CFG_PATH_GFILE='/usr/bin/file'

def _task_name_exists(name):
    """Check if the task name is registered in the database."""
    res = run_sql("SELECT id, name, last_updated FROM xtrJOB WHERE name=%s", (name, ))
    if res:
        return res
    return False

def _collection_exists(collection_name):
    """Check if the collection name is registered in the database."""
    res = run_sql("SELECT name FROM collection WHERE name=%s",
        (collection_name,))
    if res:
        return res
    return False

def _recid_exists(recid):
    """Check if the recid number is registered in the database."""
    if run_sql("SELECT id FROM bibrec WHERE id=%s",
        (recid,)):
        return True
    return False

## What differs here from the extraction-job params: collection*s* and recid*s*
possible_task_option_keys = ('collections', 'recids', 'raw-references',
                             'output-raw-refs', 'xmlfile', 'dictfile',
                             'inspire', 'kb-journal', 'kb-report-number', 'verbose')

def _task_submit_elaborate_specific_parameter(key, value, opts, args):
    """ Must be defined for bibtask to create a task """
    if args and len(args) > 0:
        ## There should be no standalone arguments for any refextract job
        ## This will catch args before the job is shipped to Bibsched
        raise StandardError("Error: Unrecognised argument '%s'.\n" % args[0])

    ## Task name specified
    if key in ('-e', '--extraction-job'):

        ## Make sure that the user is not mixing job name with other defined
        ## Refextract flags on the command line
        if filter(lambda p: task_get_option(p), possible_task_option_keys):
            write_message("Error: cli and extraction-job extraction parameters specified together.")
            write_message("The extraction-job flag cannot be mixed with other cli flags.")
            return False

        ## ---- Get the task file with this name
        task_file_dir = os.path.join(CFG_ETCDIR, 'refextract')
        ## The job file name
        task_file =  value + '.cfg'
        abs_path = os.path.join(task_file_dir, task_file)
        try:
            ## Open and readlines from file
            file_hdl = open(abs_path, 'r')
            file_params = file_hdl.readlines()
            file_hdl.close()
        except IOError:
            write_message("Error: Unable to read job file '%s'" % \
                            abs_path, stream=sys.stdout, verbose=0)
            return False
        ## ---- Get the database 'last_updated' value for this name
        xtrJOB_row = _task_name_exists(value)
        ## Build the information for this extraction job
        ## These dictionaries will be extended with extra file parameters
        if xtrJOB_row:
            task_info = {'id'           :   xtrJOB_row[0][0],
                         'name'         :   xtrJOB_row[0][1],
                         'last_updated' :   xtrJOB_row[0][2],
                         'collections'  :   [],
                         'recids'       :   [],}
        else:
            ## Save the name as the input argument for this job
            task_info = {'name'         :   value,
                         'last_updated' :   None,
                         'collections'  :   [],
                         'recids'       :   [],}
        ## ---- Save job parameters
        for p in file_params:
            p = p.strip()
            ## Ignore comments and titles, and skip blank lines
            if (not p) or p.startswith('#') or p.startswith("["):
                continue
            ## Split arguments just once
            p_args = map(lambda x: x.strip(), p.split("=", 1))
            ## Check cfg file param against list of vaild params
            if not (p_args[0] in CFG_REFEXTRACT_JOB_FILE_PARAMS):
                write_message("Error: Unknown task param '%s' inside '%s'." \
                              % (p_args[0], task_file),
                    stream=sys.stdout, verbose=0)
                return False

            if p_args[0] == 'collection':
                ## Separate and strip collections
                collections = map(lambda c: c.strip(), p_args[1].split(','))
                task_info['collections'].extend([c for c in collections if c.strip()])

#FIXME add author extraction functionality
#            elif p_args[0] == 'extraction-mode':
#                if p_args[0] == 'authors':
#                    task_set_option('authors', p_args[1])

            elif p_args[0] == 'recid':
                recids = p_args[1].split(",")
                task_info['recids'].extend([r for r in recids if r.strip()])
            elif len(p_args) == 2:
                ## All other flags
                task_info[p_args[0]] = p_args[1]
            else:
                ## Standalone flag
                task_info[p_args[0]] = 1

        if not ('xmlfile' in task_info):
            task_info['xmlfile'] = _generate_default_xml_out()

        ## Used to flag the creation of a bibupload task
        task_set_option('extraction-job', task_info)

        ## using the extraction-job options...
        ## set the task options
        for option, value in task_info.items():
            if option == 'collections':
                for collection in value:
                    collection_row = _collection_exists(collection)
                    if not collection_row:
                        write_message("Error: '%s' is not a valid collection." % collection,
                            stream=sys.stdout, verbose=0)
                        return 0
                    ## Use the collection name matched from the database
                    task_get_option(option).append(collection_row[0][0])
            elif option == 'recids':
                for recid in value:
                    if not _recid_exists(recid):
                        write_message("Error: '%s' is not a valid record id." % recid,
                            stream=sys.stdout, verbose=0)
                        return 0
                    ## Add this valid record id to the list of record ids
                    task_get_option(option).append(recid)
            elif option not in ('id', 'name', 'last_updated'):
                ## Usual way of setting options, but this time from the extraction-job file
                task_set_option(option, value)

    else:
        ## Quick check to see if an extraction job has also been specified
        if task_has_option('extraction-job'):
            write_message("Error: cli and extraction-job extraction parameters specified together.")
            write_message("The extraction-job flag cannot be mixed with other cli flags.")
            return False

        # Recid option
        elif key in ("-i", "--recid"):
            split_recids = value.split(":")
            if len(split_recids) == 2:
                first = last = valid_range = None
                try:
                    first = int(split_recids[0])
                    last = int(split_recids[1])
                    valid_range = first < last
                except ValueError:
                    write_message("Error: Range values for --recid must be integers, "
                        "not '%s'." % value, stream=sys.stdout, verbose=0)
                if first is None or last is None:
                    return False
                if not _recid_exists(first) or not _recid_exists(last) or not valid_range:
                    write_message("Error: '%s' is not a valid range of record ID's." % value,
                        stream=sys.stdout, verbose=0)
                    return False
                task_get_option('recids').extend(range(first, last))
            else:
                int_val = None
                try:
                    int_val = int(value)
                except ValueError:
                    write_message("Error: The value specified for --recid must be a "
                        "valid integer, not '%s'." % value, stream=sys.stdout,
                        verbose=0)
                if not _recid_exists(value) or int_val is None:
                    write_message("Error: '%s' is not a valid record ID." % value,
                        stream=sys.stdout, verbose=0)
                    return False
                task_get_option('recids').append(value)
        # Collection option
        elif key in ("-c", "--collection"):
            collection_row = _collection_exists(value)
            if not collection_row:
                write_message("Error: '%s' is not a valid collection." % value,
                    stream=sys.stdout, verbose=0)
                return False
            task_get_option('collections').append(collection_row[0][0])
        elif key in ('-z', '--raw-references'):
            task_set_option('raw-references', True)
        elif key in ('-r', '--output-raw-refs'):
            task_set_option('output-raw-refs', True)
        elif key in ('-x', '--xmlfile'):
            task_set_option('xmlfile', value)
        elif key in ('-d', '--dictfile'):
            task_set_option('dictfile', value)
        elif key in ('-p', '--inspire'):
            task_set_option('inspire', True)
        elif key in ('-j', '--kb-journal'):
            task_set_option('kb-journal', value)
        elif key in ('-n', '--kb-report-number'):
            task_set_option('kb-report-number', value)
    return True

def _get_fulltext_args_from_recids(recids, task_info):
    """Get list of fulltext locations for input recids
    @param recids: (list) list of recids
    @return: (list) list of strings of the form 'recid:fulltext dir'
    """
    fulltext_arguments = []
    last_updated = None
    if task_info:
        last_updated = task_info['last_updated']

    if recids:
        if last_updated:
            q_get_outdated = "SELECT id FROM bibrec WHERE id IN (%s) AND " \
                             "modification_date > '%s';" % \
                             (",".join(map(lambda r: str(r), recids)), last_updated)
            ## Get records for reference extraction
            changed_records = run_sql(q_get_outdated)
        else:
            ## Make list of lists of input recids
            changed_records = [[r] for r in recids]
        if changed_records:
            for record_row in changed_records:
                record = record_row[0]
                bibrecdoc = BibRecDocs(record)
                ## Get the latest 'document items' for this record
                bibdocfiles = bibrecdoc.list_latest_files()
                if bibdocfiles:
                    doc_types = {'pdf'  : [],
                                 'pdfa' : [],
                                 'text' : [],}

                    bibdoc = bibrecdoc.list_bibdocs()
                    ## Get the text file for this record
                    if bibdoc and bibdoc[0].has_text():
                        doc_types['text'].append(bibdoc[0].get_text_path())

                    ## For each file, of a record
                    for doc in bibdocfiles:
                        pipe_gfile = \
                               os.popen("%s '%s'" \
                                        % (CFG_PATH_GFILE, doc.get_full_path().replace("'", "\\'")), "r")
                        res_gfile = pipe_gfile.readline()
                        pipe_gfile.close()

                        ## Look for : 1. Unstamped, original uploaded-by-user, pdf files
                        ## 2. Stamped, processed, pdf files
                        ## 3. Text files
                        if (res_gfile.lower().find('pdfa') != -1):
                            doc_types['pdfa'].append(doc.get_full_path())
                        elif (res_gfile.lower().find('pdf') != -1):
                            doc_types['pdf'].append(doc.get_full_path())

                    ## Choose the type in this order of priority
                    type_of_choice = doc_types['text'] or doc_types['pdf'] or doc_types['pdfa']
                    if type_of_choice:
                        fulltext_arguments.append(str(record).rstrip(".")+':'+type_of_choice[0])
                    else:
                        write_message("W: No pdf/text file for recid %s" % \
                                      str(record), stream=sys.stdout, verbose=0)
                else:
                    write_message("W: No files exist for recid %s" % \
                                  str(record), stream=sys.stdout, verbose=0)
        elif task_info:
            ## In the event that no records have been modified since the
            ## last reference extraction
            write_message("No newly modified records for extraction-job '%s'." \
                          % task_info['name'], stream=sys.stdout, verbose=0)
    return fulltext_arguments

def _task_run_core():
    """calls extract_references in refextract"""

    def _append_recid_collection_list(collection, current_recids):
        """Updated list of recids with new recids from collection
        @param collection: (string) collection name to use to obtain record
        ids
        @param current_recids: (list) list of current record ids
        which have already been obtained from previous collection or
        recid flags
        @return: (list) current record ids with newly appended recids
        from input collection
        """
        records = get_collection_reclist(collection)
        for r in records:
            if r not in current_recids:
                current_recids.append(r)
        return current_recids

    daemon_cli_opts = { 'treat_as_reference_section' : 0,
                        'fulltext'                   : [],
                        'output_raw'                 : 0,
                        'verbosity'                  : 0,
                        'xmlfile'                    : 0,
                        'dictfile'                   : 0,
                        'inspire'                    : 0,
                        'kb-journal'                 : 0,
                        'kb-report-number'           : 0,
                        'extraction-mode'            : 'ref',
                        'authors'                    : 0,
                        'affiliations'               : 0,
                        'treat_as_raw_section'       : 0,
                      }

    ## holds the name of the extraction job, and if it's already in the db
    task_info = task_get_option('extraction-job')

    ## Now set the cli options, from the set task options list
    if task_has_option('verbose'):
        v = task_get_option('verbose')
        if not v.isdigit():
            daemon_cli_opts['verbosity'] = 0
        elif int(v) not in xrange(0, 10):
            daemon_cli_opts['verbosity'] = 0
        else:
            daemon_cli_opts['verbosity'] = int(v)
    if task_has_option('raw-references'):
        daemon_cli_opts['treat_as_reference_section'] = 1
    if task_has_option('output-raw-refs'):
        daemon_cli_opts['output_raw'] = 1
    if task_has_option('xmlfile'):
        daemon_cli_opts['xmlfile'] = task_get_option('xmlfile')
    if task_has_option('dictfile'):
        daemon_cli_opts['dictfile'] = task_get_option('dictfile')
    if task_has_option('inspire'):
        daemon_cli_opts['inspire'] = 1
    if task_has_option('kb-journal'):
        daemon_cli_opts['kb-journal'] = task_get_option('kb-journal')
    if task_has_option('kb-report-number'):
        daemon_cli_opts['kb-report-number'] = task_get_option('kb-report-number')
    if task_get_option('recids'):
        ## Construct the fulltext argument equivalent from record id's
        ## (records, and arguments, which have valid files)
        try:
            fulltexts_for_collection = \
                _get_fulltext_args_from_recids(task_get_option('recids'), task_info)
            daemon_cli_opts['fulltext'].extend(fulltexts_for_collection)
        except Exception, err:
            write_message('Error: Unable to obtain fulltexts for recid %s. %s' \
                           % (str(task_get_option('recids')), err), \
                           stream=sys.stdout, verbose=0)
            raise StandardError
    if task_get_option('collections'):
        ## Construct the fulltext argument equivalent from record id's
        recids_from_collection = []
        for collection in task_get_option('collections'):
            recids_from_collection = \
                _append_recid_collection_list(collection, recids_from_collection)
        ## Construct the fulltext argument equivalent for collection recid's
        ## (records, and arguments, which have valid files)
        fulltexts_for_collection = \
            _get_fulltext_args_from_recids(recids_from_collection, task_info)
        daemon_cli_opts['fulltext'].extend(fulltexts_for_collection)

    ## If some records exist which actually need to have their references extracted
    if daemon_cli_opts['fulltext']:
        begin_extraction(daemon_cli_options=daemon_cli_opts)

        try:
            ## Always move contents of file holding xml into a file
            ## with a timestamp
            perm_file_fd, perm_file_name = \
                mkstemp(suffix='.xml', prefix="refextract_%s_" % \
                            time.strftime("%Y-%m-%d_%H:%M:%S"), \
                            dir=os.path.join(CFG_TMPDIR, "refextract"))
            copyfile(daemon_cli_opts['xmlfile'], perm_file_name)
            os.close(perm_file_fd)
        except IOError, err:
            write_message("Error: Unable to copy content to timestamped XML file, %s" \
                              % err)
            return 0

        ## Now, given the references have been output to option 'xmlfile'
        ## enrich the meta-data of the affected records, via bibupload
        ## Only if a named file was given as input
        if task_has_option('extraction-job'):
            cmd = "%s/bibupload -n -c '%s' " % (CFG_BINDIR, perm_file_name)
            errcode = 0
            try:
                errcode = os.system(cmd)
            except OSError, exc:
                write_message('Error: Command %s failed [%s].' % (cmd, exc),
                    stream=sys.stdout, verbose=0)
            if errcode != 0:
                write_message("Error: %s failed, error code is %d." %
                    (cmd, errcode), stream=sys.stdout, verbose=0)
                return 0
            ## Update the extraction_date for each record id,
            ## (only those which have been given to Refextract)
            if task_info['last_updated']:
                ## If the last updated time exists in the db.. update it
                run_sql("UPDATE xtrJOB SET last_updated = NOW() WHERE name=%s", \
                        (task_info['name'],))
            else:
                ## This task does not exist in the db, add it
                run_sql("INSERT INTO xtrJOB (name, last_updated) VALUES (%s, NOW())", \
                        (task_info['name'],))

            write_message("Reference extraction complete. Saved extraction-job XML file to %s" \
                              % (perm_file_name))

        ## When not calling a predefined extraction-job, display the
        ## directory of the outputted references.
        else:
            write_message("Reference extraction complete. Saved references XML file to %s" \
                              % (perm_file_name))

    return True

def _generate_default_xml_out():
    """Generates the default output xml file directory, corresponding
    to this refextract task id. This will be called in a user specified
    xml out file has not been provided.
    @return: (string) output xml file directory"""
    results_dir = os.path.join(CFG_TMPDIR, "refextract")
    # Write the changes to a temporary file.
    filename = "refextract_task_%d.xml" % task_get_task_param('task_id', 0)
    abs_path = os.path.join(results_dir, filename)
    ## Make the folder, if not exists
    if not os.path.isdir(results_dir):
        os.mkdir(results_dir)
    return abs_path

def _task_submit_check_options():
    """ Reimplement this method for having the possibility to check options
    before submitting the task, in order for example to provide default
    values. It must return False if there are errors in the options.
    """
    if not task_get_option('recids') and not task_get_option('collections'):
        write_message('Error: No input file specified', stream=sys.stdout, verbose=0),
        return False
    ## Output to a file in tmp, if the user has not specified an output file
    if not task_get_option('xmlfile', default=False):
        abs_path = _generate_default_xml_out()
        ## Set the output
        task_set_option('xmlfile', abs_path)
    return True

def refextract_daemon():
    """Constructs the refextract bibtask."""
    ## Build and submit the task
    task_init(authorization_action='runrefextract',
        authorization_msg="Refextract Task Submission",
        description="Extraction of references from pdf/text files, as XML.\n",
        # get the global help_message variable imported from refextract.py
        help_specific_usage= """Usage: refextract [options] -f recid:file1 [-f recid:file2 ...]
       refextract [options] --collection coll1 [--collection coll2 ...]
       refextract [options] --extraction-job refextract-job-name""" \
       + help_message + """
Scheduled (daemon) Refextract options:
  -i, --recid       Record id for extraction.
  -c, --collection  Entire Collection for extraction.
  -e, --extraction-job  Name of a pre-configured Refextract task.

  Examples:
   (run a daemon job)
      refextract --extraction-job refextract-job-preprints
   (run on groups of/specific recids)
      refextract --collection preprints
   (run as standalone)
      refextract -x /home/chayward/refs.xml -f 499:/home/chayward/thesis.pdf

""",
        version="Invenio v%s" % CFG_VERSION,
        specific_params=("hVv:zrx:d:pj:n:i:c:e:",
                            ["help",
                             "version",
                             "verbose=",
                             "raw-references",
                             "output-raw-refs",
                             "xmlfile=",
                             "dictfile=",
                             "inspire",
                             "kb-journal=",
                             "kb-report-number=",
                             "recid=",
                             "collection=",
                             "extraction-job=",]),
        task_submit_elaborate_specific_parameter_fnc=\
        _task_submit_elaborate_specific_parameter,
        task_submit_check_options_fnc=_task_submit_check_options,
        task_run_fnc=_task_run_core)
