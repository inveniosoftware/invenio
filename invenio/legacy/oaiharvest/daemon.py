# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
OAI Harvest daemon - harvest records from OAI repositories.

If started via CLI with --verb parameters, starts a manual single-shot
harvesting. Otherwise starts a BibSched task for periodical harvesting
of repositories defined in the OAI Harvest admin interface
"""

from __future__ import print_function

import sys
import getopt
import getpass
import time
from six.moves import urllib

from sqlalchemy import orm
from invenio.config import (CFG_OAI_FAILED_HARVESTING_STOP_QUEUE,
                            CFG_OAI_FAILED_HARVESTING_EMAILS_ADMIN,
                            CFG_SITE_SUPPORT_EMAIL)

from invenio.modules.oaiharvester.models import OaiHARVEST

from invenio.legacy.bibsched.bibtask import (task_get_task_param,
                                             task_get_option, task_set_option,
                                             write_message, task_init)

from invenio.legacy.oaiharvest.config import InvenioOAIHarvestWarning

from invenio.legacy.oaiharvest import getter
from invenio.ext.logging import register_exception

from invenio.base.factory import with_app_context

from invenio.legacy.oaiharvest.utils import (compare_timestamps_with_tolerance,
                                             generate_harvest_report,
                                             create_ticket)

from invenio.legacy.webuser import email_valid_p
from invenio.ext.email import send_email

from invenio.modules.workflows.models import (BibWorkflowEngineLog, Workflow,
                                              BibWorkflowObjectLog)
from invenio.modules.workflows.registry import workflows as registry_workflows
from invenio.modules.workflows.api import start
from invenio.modules.workflows.errors import WorkflowError
import invenio.legacy.template

oaiharvest_templates = invenio.legacy.template.load('oaiharvest')


def task_run_core():
    """Core task of oaiharvest.

    This function will run all the operations needed
    to run an oaiharvest task into bibsched.

    :return: :raise InvenioOAIHarvestWarning:
    """
    workflow_id_preservation = 0
    workflow = None
    start_time = time.time()
    list_of_workflow_without_repository = []
    list_of_repository_per_workflow = {}

    repository = task_get_option("repository")
    if not repository:
        workflow_option = task_get_option("workflow")

        if isinstance(workflow_option, list):
            for name in workflow_option:
                if name not in list_of_workflow_without_repository:
                    list_of_workflow_without_repository.append(name)

        else:
            list_of_workflow_without_repository.append(workflow_option)
    else:
        if task_get_option("workflow"):

            workflow_option = task_get_option("workflow")
            if isinstance(workflow_option, list):
                for name in workflow_option:
                    if name not in list_of_repository_per_workflow:
                        list_of_repository_per_workflow[name] = repository

            else:
                list_of_repository_per_workflow[workflow_option] = repository

        elif isinstance(repository, list):

            for name_repository in repository:
                name_workflow = OaiHARVEST.get(
                    OaiHARVEST.name == name_repository).one().workflows
                if name_workflow not in list_of_repository_per_workflow:
                    list_of_repository_per_workflow[name_workflow] = [
                        name_repository]
                else:
                    list_of_repository_per_workflow[name_workflow].append(
                        name_repository)

        else:
            workflow_found = OaiHARVEST.get(
                OaiHARVEST.name == repository).one().workflows
            list_of_repository_per_workflow[workflow_found] = repository
    try:
        if list_of_repository_per_workflow:
            for workflow_to_launch in list_of_repository_per_workflow:
                options = task_get_option(None)
                options["repository"] = list_of_repository_per_workflow[
                    workflow_to_launch]
                workflow = start(workflow_to_launch,
                                 data=[""],
                                 stop_on_error=True,
                                 options=options)
        else:
            for workflow_to_launch in list_of_workflow_without_repository:
                workflow = start(workflow_to_launch,
                                 data=[""],
                                 stop_on_error=True,
                                 options=task_get_option(None))
        if workflow:
            workflow_id_preservation = workflow.uuid
            workflowlog = BibWorkflowEngineLog.query.filter(
                BibWorkflowEngineLog.id_object == workflow.uuid
            ).all()
            for log in workflowlog:
                write_message(log.message)
        execution_time = round(time.time() - start_time, 2)
        write_message("Execution time :" + str(execution_time))
    except WorkflowError as e:
        write_message("ERRORS HAPPENED")
        write_message("____________Workflow log output____________")
        workflow_id_preservation = e.id_workflow
        workflowlog = BibWorkflowEngineLog.query.filter(
            BibWorkflowEngineLog.id_object == e.id_workflow
        ).filter(BibWorkflowEngineLog.log_type >= 40).all()

        for log in workflowlog:
            write_message(log.message)

        for i in e.payload:
            write_message("\n\n____________Workflow " + i + " log output____________")
            workflowlog = BibWorkflowEngineLog.query.filter(
                BibWorkflowEngineLog.id_object == i
            ).filter(BibWorkflowEngineLog.log_type >= 40).all()
            for log in workflowlog:
                write_message(log.message)

        write_message("____________Object log output____________")

        objectlog = BibWorkflowObjectLog.query.filter(
            BibWorkflowObjectLog.id_object == e.id_object
        ).filter(BibWorkflowEngineLog.log_type >= 40).all()

        for log in objectlog:
            write_message(log.message)

        execution_time = round(time.time() - start_time, 2)
        write_message("Execution time :" + str(execution_time))

    # Generate reports
    ticket_queue = task_get_option("create-ticket-in")
    notification_email = task_get_option("notify-email-to")
    workflow_main = Workflow.query.filter(
        Workflow.uuid == workflow_id_preservation
    ).one()

    if ticket_queue or notification_email:

        subject, text = generate_harvest_report(
            workflow_main,
            current_task_id=task_get_task_param("task_id")
        )
        # Create ticket for finished harvest?
        if ticket_queue:
            ticketid = create_ticket(ticket_queue, subject=subject, text=text)
            if ticketid:
                write_message("Ticket %s submitted." % (str(ticketid),))

        # Send e-mail for finished harvest?
        if notification_email:
            send_email(fromaddr=CFG_SITE_SUPPORT_EMAIL,
                       toaddr=notification_email,
                       subject=subject,
                       content=text)

    if workflow_main.counter_error:
        if CFG_OAI_FAILED_HARVESTING_STOP_QUEUE == 0 or \
           not task_get_task_param("sleeptime") or \
           workflow_main.counter_error > 1:
            # Admin want BibSched to stop, or the task is not set to
            # run at a later date: we must stop the queue.
            write_message("An error occurred. Task is configured to stop")
            return False
        else:
            # An error happened, but it can be recovered at next run
            # (task is re-scheduled) and admin set BibSched to
            # continue even after failure.
            write_message("Error occurred, but task is configured to continue")
            if CFG_OAI_FAILED_HARVESTING_EMAILS_ADMIN:
                try:
                    raise InvenioOAIHarvestWarning(
                        "OAIHarvest (task #%s) failed at fully harvesting."
                        " BibSched has NOT been stopped, and OAIHarvest will"
                        " try to recover at next run" %
                        (task_get_task_param("task_id"),)
                    )
                except InvenioOAIHarvestWarning:
                    register_exception(stream='warning', alert_admin=True)
            return True
    else:
        return True


def get_dates(dates):
    """Validate and process the dates input by the user."""
    twodates = []
    if dates:
        datestring = dates.split(":")
        if len(datestring) == 2:
            for date in datestring:
                ### perform some checks on the date format
                datechunks = date.split("-")
                if len(datechunks) == 3:
                    try:
                        if int(datechunks[0]) and int(datechunks[1]) and \
                                int(datechunks[2]):
                            twodates.append(date)
                    except StandardError:
                        write_message("Dates have invalid format, not "
                                      "'yyyy-mm-dd:yyyy-mm-dd'")
                        twodates = None
                        return twodates
                else:
                    write_message("Dates have invalid format, not "
                                  "'yyyy-mm-dd:yyyy-mm-dd'")
                    twodates = None
                    return twodates
                    ## final check.. date1 must me smaller than date2
            date1 = str(twodates[0]) + " 01:00:00"
            date2 = str(twodates[1]) + " 01:00:00"
            if compare_timestamps_with_tolerance(date1, date2) != -1:
                write_message("First date must be before second date.")
                twodates = None
                return twodates
        else:
            write_message("Dates have invalid format, not "
                          "'yyyy-mm-dd:yyyy-mm-dd'")
            twodates = None
    else:
        twodates = None
    return twodates


def get_repository_names(repositories):
    """ A method to validate the repository names input by the user."""
    repository_names = []
    if repositories:
        names = repositories.split(",")
        for name in names:
            ### take into account both single word names and multiple word
            ### names (which get wrapped around "" or '')
            name = name.strip()
            if name.startswith("'"):
                name = name.strip("'")
            elif name.startswith('"'):
                name = name.strip('"')
            repository_names.append(name)
    else:
        repository_names = None
    return repository_names


def get_identifier_names(identifier):
    """Return list of identifiers from a comma-separated string."""
    if identifier:
        # Let's see if the user had a comma-separated list of OAI ids.
        stripped_idents = []
        for ident in identifier.split(","):
            ident = ident.strip()
            if not ident.startswith("oai:arXiv.org"):
                if "oai:arxiv.org" in ident.lower():
                    ident = ident.replace("oai:arxiv.org", "oai:arXiv.org")
                elif "arXiv" in ident:
                    # New style arXiv ID
                    ident = ident.replace("arXiv", "oai:arXiv.org")
            stripped_idents.append(ident)
        return stripped_idents


def usage(exitcode=0, msg=""):
    """Print out info. Only used when run in 'manual' harvesting mode."""
    sys.stderr.write("*Manual single-shot harvesting mode*\n")
    if msg:
        sys.stderr.write(msg + "\n")
    sys.exit(exitcode)


@with_app_context()
def main():
    """Start the tool.

    If the command line arguments are those of the 'manual' mode, then
    starts a manual one-time harvesting. Else trigger a BibSched task
    for automated harvesting based on the OAIHarvest admin settings.
    """
    # Let's try to parse the arguments as used in manual harvesting:
    try:

        opts, args = getopt.getopt(sys.argv[1:], "o:v:m:p:i:s:f:u:r:c:k:l:w:",
                                   ["output=",
                                    "verb=",
                                    "method=",
                                    "metadataPrefix=",
                                    "identifier=",
                                    "set=",
                                    "from=",
                                    "until=",
                                    "resumptionToken=",
                                    "certificate=",
                                    "key=",
                                    "user=",
                                    "password=",
                                    "workflow=",
                                    ])

        # So everything went smoothly: start harvesting in manual mode
        if len([opt for opt, opt_value in opts
                if opt in ['-v', '--verb']]) > 0:
            # verb parameter is given
            http_param_dict = {}
            method = "POST"
            output = ""
            user = None
            password = None
            cert_file = None
            key_file = None
            sets = []
            # get options and arguments
            for opt, opt_value in opts:
                if opt in ["-v", "--verb"]:
                    http_param_dict['verb'] = opt_value
                elif opt in ["-m", '--method']:
                    if opt_value == "GET" or opt_value == "POST":
                        method = opt_value
                elif opt in ["-p", "--metadataPrefix"]:
                    http_param_dict['metadataPrefix'] = opt_value
                elif opt in ["-i", "--identifier"]:
                    http_param_dict['identifier'] = opt_value
                elif opt in ["-s", "--set"]:
                    sets = opt_value.split()
                elif opt in ["-f", "--from"]:
                    http_param_dict['from'] = opt_value
                elif opt in ["-u", "--until"]:
                    http_param_dict['until'] = opt_value
                elif opt in ["-r", "--resumptionToken"]:
                    http_param_dict['resumptionToken'] = opt_value
                elif opt in ["-o", "--output"]:
                    output = opt_value
                elif opt in ["-c", "--certificate"]:
                    cert_file = opt_value
                elif opt in ["-k", "--key"]:
                    key_file = opt_value
                elif opt in ["-l", "--user"]:
                    user = opt_value
                elif opt in ["-w", "--password"]:
                    password = opt_value
                elif opt in ["-V", "--version"]:
                    print(__revision__)
                    sys.exit(0)
                else:
                    usage(1, "Option %s is not allowed" % opt)

            if len(args) > 0:
                base_url = args[-1]
                if not base_url.lower().startswith('http'):
                    base_url = 'http://' + base_url
                (addressing_scheme, network_location, path, dummy1,
                 dummy2, dummy3) = urllib.parse(base_url)
                secure = (addressing_scheme == "https")

                if (cert_file and not key_file) or \
                        (key_file and not cert_file):
                    # Both are needed if one specified
                    usage(1, "You must specify both certificate and key files")

                if password and not user:
                    # User must be specified when password is given
                    usage(1, "You must specify a username")
                elif user and not password:
                    if not secure:
                        sys.stderr.write(
                            "*WARNING* Your password will be sent in clear!\n")
                    try:
                        password = getpass.getpass()
                    except KeyboardInterrupt as error:
                        sys.stderr.write("\n%s\n" % (error,))
                        sys.exit(0)

                getter.harvest(network_location, path,
                               http_param_dict, method,
                               output, sets, secure, user,
                               password, cert_file,
                               key_file)

                sys.stderr.write("Harvesting completed at: %s\n\n" %
                                 time.strftime("%Y-%m-%d %H:%M:%S --> ",
                                               time.localtime()))
                return
            else:
                usage(1, "You must specify the URL to harvest")
        else:
            # verb is not given. We will continue with periodic
            # harvesting. But first check if URL parameter is given:
            # if it is, then warn directly now

            if len([opt for opt, opt_value in opts if
                    opt in ['-i', '--identifier']]) == 0 \
                and len(args) > 1 or \
                    (len(args) == 1 and not args[0].isdigit()):
                usage(1, "You must specify the --verb parameter")
    except getopt.error:
        # So could it be that we are using different arguments? Try to
        # start the BibSched task (automated harvesting) and see if it
        # validates
        pass
        # BibSched mode - periodical harvesting
    # Note that the 'help' is common to both manual and automated
    # mode.

    num_of_critical_parameter = 0
    num_of_critical_parameterb = 0
    repositories = []

    for opt in sys.argv[1:]:
        if opt in "-r" or opt in "--repository":
            num_of_critical_parameter += 1
        elif opt in "--workflow":
            num_of_critical_parameterb += 1
        if num_of_critical_parameter > 1 or num_of_critical_parameterb > 1:
            usage(1, "You can't specify twice -r or --workflow")

    if num_of_critical_parameter == 1:
        if "-r" in sys.argv:
            position = sys.argv.index("-r")
        else:
            position = sys.argv.index("--repository")
        repositories = sys.argv[position + 1].split(",")
        if len(repositories) > 1 and \
                ("-i" in sys.argv or "--identifier" in sys.argv):
            usage(1,
                  "It is impossible to harvest an identifier from several "
                  "repositories.")

    if num_of_critical_parameterb == 1:

        position = sys.argv.index("--workflow")
        workflows = sys.argv[position + 1].split(",")

        for workflow_candidate in workflows:
            if workflow_candidate not in registry_workflows:
                usage(1, "The workflow %s doesn't exist." % workflow_candidate)

    if num_of_critical_parameter == 1 and num_of_critical_parameterb == 0:

        for name_repository in repositories:
            try:
                oaiharvest_instance = OaiHARVEST.get(
                    OaiHARVEST.name == name_repository).one()
                if oaiharvest_instance.workflows not in registry_workflows:
                    usage(1,
                          "The repository %s doesn't have a valid workflow specified." % name_repository)
            except orm.exc.NoResultFound:
                usage(1,
                      "The repository %s doesn't exist in our database." % name_repository)

    elif num_of_critical_parameter == 1 and num_of_critical_parameterb == 1:

        for name_repository in repositories:
            try:
                OaiHARVEST.get(OaiHARVEST.name == name_repository).one()
            except orm.exc.NoResultFound:
                usage(1,
                      "The repository %s doesn't exist in our database." % name_repository)

        print("A workflow has been specified, overriding the repository one.")

    task_set_option("repository", None)
    task_set_option("dates", None)
    task_set_option("workflow", None)
    task_set_option("identifiers", None)
    task_init(authorization_action='runoaiharvest',
              authorization_msg="oaiharvest Task Submission",
              description="""
Harvest records from OAI sources.
Manual vs automatic harvesting:
   - Manual harvesting retrieves records from the specified URL,
     with the specified OAI arguments. Harvested records are displayed
     on the standard output or saved to a file, but are not integrated
     into the repository. This mode is useful to 'play' with OAI
     repositories or to build special harvesting scripts.
   - Automatic harvesting relies on the settings defined in the OAI
     Harvest admin interface to periodically retrieve the repositories
     and sets to harvest. It also take care of harvesting only new or
     modified records. Records harvested using this mode are converted
     and integrated into the repository, according to the settings
     defined in the OAI Harvest admin interface.

Examples:
Manual (single-shot) harvesting mode:
   Save to /tmp/z.xml records from CDS added/modified between 2004-04-01
   and 2004-04-02, in MARCXML:
     $ oaiharvest -vListRecords -f2004-04-01 -u2004-04-02 -pmarcxml -o/tmp/z.xml http://cds.cern.ch/oai2d
Automatic (periodical) harvesting mode:
   Schedule daily harvesting of all repositories defined in OAIHarvest admin:
     $ oaiharvest -s 24h
   Schedule daily harvesting of repository 'arxiv', defined in OAIHarvest admin:
     $ oaiharvest -r arxiv -s 24h
   Harvest in 10 minutes from 'pubmed' repository records added/modified
   between 2005-05-05 and 2005-05-10:
     $ oaiharvest -r pubmed -d 2005-05-05:2005-05-10 -t 10m
""",

              help_specific_usage='Manual single-shot harvesting mode:\n'
                                  '  -o, --output         specify output file\n'
                                  '  -v, --verb           OAI verb to be executed\n'
                                  '  -m, --method         http method (default POST)\n'
                                  '  -p, --metadataPrefix metadata format\n'
                                  '  -i, --identifier     OAI identifier\n'
                                  '  -s, --set            OAI set(s). Whitespace-separated list\n'
                                  '  -r, --resuptionToken Resume previous harvest\n'
                                  '  -f, --from           from date (datestamp)\n'
                                  '  -u, --until          until date (datestamp)\n'
                                  '  -c, --certificate    path to public certificate (in case of certificate-based harvesting)\n'
                                  '  -k, --key            path to private key (in case of certificate-based harvesting)\n'
                                  '  -l, --user           username (in case of password-protected harvesting)\n'
                                  '  -w, --password       password (in case of password-protected harvesting)\n'
                                  'Deamon mode (periodical or one-shot harvesting mode):\n'
                                  '  -r, --repository="repo A"[,"repo B"] \t which repositories to harvest (default=all)\n'
                                  '  -d, --dates=yyyy-mm-dd:yyyy-mm-dd \t reharvest given dates only\n'
                                  '  -i, --identifier     OAI identifier if wished to run in as a task.\n'
                                  '  --notify-email-to    Receive notifications on given email on successful upload and/or finished harvest.\n'
                                  '  --workflow       specify the workflow to execute.\n'
                                  '  --create-ticket-in   Provide desired ticketing queue to create a ticket in it on upload and/or finished harvest.\n'
                                  '                       Requires a configured ticketing system (BibCatalog).\n',
              specific_params=(
                  "r:i:d:W",
                  ["repository=", "identifier=", "dates=", "workflow=",
                   "notify-email-to=", "create-ticket-in="]),
              task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
              task_run_fnc=task_run_core)


def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """Elaborate specific cli parameters for oaiharvest."""
    if key in ("-r", "--repository"):
        task_set_option('repository', get_repository_names(value))
    elif key in ("--workflow"):
        task_set_option('workflow', get_repository_names(value))
    elif key in ("-i", "--identifier"):
        task_set_option('identifiers', get_identifier_names(value))
    elif key in ("-d", "--dates"):
        task_set_option('dates', get_dates(value))
        if value is not None and task_get_option("dates") is None:
            raise StandardError("Date format not valid.")
    elif key in ("--notify-email-to",):
        if email_valid_p(value):
            task_set_option('notify-email-to', value)
        else:
            raise StandardError("E-mail format not valid.")
    elif key in ("--create-ticket-in",):
        task_set_option('create-ticket-in', value)
    else:
        return False
    return True
