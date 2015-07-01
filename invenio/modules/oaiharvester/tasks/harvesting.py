# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Tasks used for main OAI harvesting workflow."""

import os
import time

from functools import wraps

from invenio.base.globals import cfg


def init_harvesting(obj, eng):
    """Get all the options from previous state.

    This function gets all the option linked to the task and stores them into the
    object to be used later.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    try:
        obj.extra_data["options"] = eng.extra_data["options"]
    except KeyError:
        eng.log.error("No options for this task have been found. It is possible"
                      "that the following task could failed or work not as expected")
        obj.extra_data["options"] = {}
    eng.log.info("end of init_harvesting")


init_harvesting.description = 'Start harvesting'


def filtering_oai_pmh_identifier(obj, eng):
    """Check if the current OAI record has been processed already this run."""
    from ..utils import identifier_extraction_from_string

    if "oaiharvest" not in eng.extra_data:
        eng.extra_data["oaiharvest"] = {}
    if "identifiers" not in eng.extra_data["oaiharvest"]:
        eng.extra_data["oaiharvest"]["identifiers"] = []

    if not obj.data:
        obj.log.error("No data found in object!")
        return False
    elif isinstance(obj.data, list):
        # In case it is a list
        obj.data = obj.data[0]

    identifier = (identifier_extraction_from_string(obj.data) or
                  identifier_extraction_from_string(obj.data, oai_namespace="") or
                  "")
    obj.extra_data["oai_identifier"] = identifier
    if identifier in eng.extra_data["oaiharvest"]["identifiers"]:
        # The record has already been harvested in this run
        return False
    else:
        eng.extra_data["oaiharvest"]["identifiers"].append(identifier)
        return True


def get_repositories_list(repositories=()):
    """Get repository list in options.

    Here we are retrieving the oaiharvest configuration for the task.
    It will allows in the future to do all the correct operations.
    :param repositories:
    """
    from invenio.modules.oaiharvester.models import OaiHARVEST
    from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

    @wraps(get_repositories_list)
    def _get_repositories_list(obj, eng):
        repositories_to_harvest = repositories
        reposlist_temp = []
        if obj.extra_data["options"]["repository"]:
            repositories_to_harvest = obj.extra_data["options"]["repository"]
        if repositories_to_harvest:
            for reposname in repositories_to_harvest:
                try:
                    reposlist_temp.append(
                        OaiHARVEST.get(OaiHARVEST.name == reposname).one())
                except (MultipleResultsFound, NoResultFound):
                    eng.log.critical(
                        "Repository %s doesn't exit into our database",
                        reposname)
        else:
            reposlist_temp = OaiHARVEST.get(OaiHARVEST.name != "").all()
        true_repo_list = []
        for repo in reposlist_temp:
            true_repo_list.append(repo.to_dict())

        if true_repo_list:
            return true_repo_list
        else:
            eng.halt(
                "No Repository named %s. Impossible to harvest non-existing things."
                % repositories_to_harvest)

    return _get_repositories_list


def harvest_records(obj, eng):
    """Run the harvesting task.

    The row argument is the oaiharvest task queue row, containing if, arguments,
    etc.
    Return 1 in case of success and 0 in case of failure.
    :param obj: BibworkflowObject being
    :param eng: BibWorkflowEngine processing the object
    """
    from invenio.modules.oaiharvester.utils import collect_identifiers
    from invenio.modules.workflows.errors import WorkflowError

    harvested_identifier_list = []

    harvestpath = "%s_%d_%s_" % (
        "%s/oaiharvest_%s" % (cfg['CFG_TMPSHAREDDIR'], eng.uuid),
        1, time.strftime("%Y%m%d%H%M%S"))

    # ## go ahead: check if user requested from-until harvesting
    try:
        if "dates" not in obj.extra_data["options"]:
            obj.extra_data["options"]["dates"] = []
        if "identifiers" not in obj.extra_data["options"]:
            obj.extra_data["options"]["identifiers"] = []
    except TypeError:
        obj.extra_data["options"] = {"dates": [], "identifiers": []}

    arguments = obj.extra_data["repository"]["arguments"]
    if arguments:
        eng.log.info("running with post-processes: %r" % (arguments,))
    else:
        eng.log.error(
            "No arguments found... It can be causing major error after this point.")

    # Harvest phase
    if obj.extra_data["options"]["identifiers"]:
        # Harvesting is done per identifier instead of server-updates
        harvested_files_list = harvest_by_identifiers(obj, harvestpath)
    else:
        harvested_files_list = harvest_by_dates(obj, harvestpath)

    if len(harvested_files_list) == 0:
        eng.log.info("No records harvested for %s" % (obj.data["name"],))
        # Retrieve all OAI IDs and set active list

    harvested_identifier_list.append(collect_identifiers(harvested_files_list))

    if len(harvested_files_list) != len(harvested_identifier_list[0]):
        # Harvested files and its identifiers are 'out of sync', abort harvest

        raise WorkflowError(
            "Harvested files miss identifiers for %s" % (arguments,),
            id_workflow=eng.uuid,
            id_object=obj.id)
    obj.extra_data['harvested_files_list'] = harvested_files_list
    eng.log.info(
        "%d files harvested and processed \n End harvest records task" % (
            len(harvested_files_list),))


def get_records_from_file(path=None):
    """Allow to retrieve the records from a file."""
    from ..utils import record_extraction_from_file

    @wraps(get_records_from_file)
    def _get_records_from_file(obj, eng):
        if "_LoopData" not in eng.extra_data:
            eng.extra_data["_LoopData"] = {}
        if "get_records_from_file" not in eng.extra_data["_LoopData"]:
            eng.extra_data["_LoopData"]["get_records_from_file"] = {}
            if path:
                eng.extra_data["_LoopData"]["get_records_from_file"].update(
                    {"data": record_extraction_from_file(path)})
            else:
                eng.extra_data["_LoopData"]["get_records_from_file"].update(
                    {"data": record_extraction_from_file(obj.data)})
                eng.extra_data["_LoopData"]["get_records_from_file"][
                    "path"] = obj.data

        elif os.path.isfile(obj.data) and obj.data != \
                eng.extra_data["_LoopData"]["get_records_from_file"]["path"]:
            eng.extra_data["_LoopData"]["get_records_from_file"].update(
                {"data": record_extraction_from_file(obj.data)})
        return eng.extra_data["_LoopData"]["get_records_from_file"]["data"]

    return _get_records_from_file


def harvest_by_identifiers(obj, harvestpath):
    """Harvest an OAI repository by identifiers using a workflow object.

    Given a repository "object" (dict from DB) and a list of OAI identifiers
    of records in the repository perform a OAI harvest using GetRecord
    for each.

    The records will be harvested into the specified filepath.
    """
    from ..getter import oai_harvest_get

    harvested_files_list = []
    for oai_identifier in obj.extra_data["options"]["identifiers"]:
        harvested_files_list.extend(oai_harvest_get(prefix=obj.data["metadataprefix"],
                                                    baseurl=obj.data["baseurl"],
                                                    harvestpath=harvestpath,
                                                    verb="GetRecord",
                                                    identifier=oai_identifier))
    return harvested_files_list


def harvest_by_dates(obj, harvestpath):
    """
    Harvest an OAI repository by dates.

    Given a repository "object" (dict from DB) and from/to dates,
    this function will perform an OAI harvest request for records
    updated between the given dates.

    If no dates are given, the repository is harvested from the beginning.

    If you set fromdate == last-run and todate == None, then the repository
    will be harvested since last time (most common type).

    The records will be harvested into the specified filepath.
    """
    from ..getter import oai_harvest_get

    if obj.extra_data["options"]["dates"]:
        fromdate = str(obj.extra_data["options"]["dates"][0])
        todate = str(obj.extra_data["options"]["dates"][1])
    elif obj.data["lastrun"] is None or obj.data["lastrun"] == '':
        fromdate = None
        todate = None
        obj.extra_data["_should_last_run_be_update"] = True
    else:
        fromdate = str(obj.data["lastrun"]).split()[0]
        todate = None
        obj.extra_data["_should_last_run_be_update"] = True

    return oai_harvest_get(prefix=obj.data["metadataprefix"],
                           baseurl=obj.data["baseurl"],
                           harvestpath=harvestpath,
                           fro=fromdate,
                           until=todate,
                           setspecs=obj.data["setspecs"])
