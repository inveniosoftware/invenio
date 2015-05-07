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

"""Tasks used in OAI harvesting together with repository information."""

import os
import random
import re

from functools import wraps

from invenio.base.globals import cfg


REGEXP_AUTHLIST = re.compile(
    "<collaborationauthorlist.*?>.*?</collaborationauthorlist>", re.DOTALL)
REGEXP_REFS = re.compile(
    "<record.*?>.*?<controlfield .*?>.*?</controlfield>(.*?)</record>",
    re.DOTALL)


def _attach_files_to_obj(obj, new_ffts):
    """Given a SmartJSON representation, add any missing fft entries to obj."""
    if not new_ffts or new_ffts.get("fft") is None:
        obj.log.error("No files to add")
        return
    if "fft" not in obj.data:
        obj.data['fft'] = new_ffts["fft"]
        return
    if not isinstance(new_ffts["fft"], list):
        new_ffts["fft"] = [new_ffts["fft"]]
    if not isinstance(obj.data["fft"], list):
        obj.data["fft"] = [obj.data["fft"]]
    for element in new_ffts["fft"]:
        if element.get("url", "") in obj.data.get("fft.url", []):
            continue
        obj.data['fft'].append(element)


def post_process_selected(post_process):
    """Check if post process is selected."""
    @wraps(post_process_selected)
    def _post_process_selected(obj, eng):
        try:
            post_process_list = obj.extra_data["repository"]["postprocess"]
        except KeyError:
            # No post process list, we return False
            eng.log.info("No post-process for {0}".format(post_process))
            return False
        if post_process in post_process_list:
            eng.log.info("Post-process found for {0}".format(post_process))
            return True
        return False
    return _post_process_selected


def convert_record_with_repository(stylesheet=""):
    """Convert a MARC record to another one thanks to the stylesheet.

    This function converts a record to a marcxml representation by using a
    style sheet which should be in parameter or which should have been stored
    into extra data of the object.

    The priority is given to the stylesheet into the extra data of the object.
    The parameter should be used in case the stylesheet is missing from extra data
    or when you want to do a simple workflow which doesn't need to be dynamic.

    :param stylesheet: it is the name of the stylesheet that you want to use
    to convert a oai record to a marcxml one
    :type stylesheet: str
    """
    @wraps(convert_record_with_repository)
    def _convert_record(obj, eng):
        from invenio.modules.workflows.tasks.marcxml_tasks import convert_record
        if not stylesheet:
            repository = obj.extra_data.get("repository", {})
            arguments = repository.get("arguments", {})
            stylesheet_to_use = arguments.get('c_stylesheet')
        else:
            stylesheet_to_use = stylesheet
        convert_record(stylesheet_to_use)(obj, eng)

    return _convert_record


def arxiv_fulltext_download(obj, eng):
    """Perform the fulltext download step for arXiv records.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    from invenio.utils.plotextractor.api import get_pdf_from_arxiv

    if "result" not in obj.extra_data:
        obj.extra_data["_result"] = {}

    if "pdf" not in obj.extra_data["_result"]:
        extract_path = os.path.join(
            cfg.get('OAIHARVESTER_STORAGEDIR', cfg.get('CFG_TMPSHAREDDIR')),
            str(eng.uuid)
        )
        pdf = get_pdf_from_arxiv(
            obj.data.get(cfg.get('OAIHARVESTER_RECORD_ARXIV_ID_LOOKUP')),
            extract_path
        )
        arguments = obj.extra_data["repository"]["arguments"]
        try:
            if not arguments['t_doctype'] == '':
                doctype = arguments['t_doctype']
            else:
                doctype = 'arXiv'
        except KeyError:
            eng.log.error("WARNING: HASARDOUS BEHAVIOUR EXPECTED, "
                          "You didn't specified t_doctype in argument"
                          " for fulltext_download,"
                          "try to recover by using the default one!")
            doctype = 'arXiv'
        if pdf:
            obj.extra_data["_result"]["pdf"] = pdf
            new_dict_representation = {
                "fft": [
                    {
                        "url": pdf,
                        "docfile_type": doctype
                    }
                ]
            }
            _attach_files_to_obj(obj, new_dict_representation)
            fileinfo = {
                "type": "fulltext",
                "filename": os.path.basename(pdf),
                "full_path": pdf,
            }
            obj.update_task_results(
                "PDF",
                [{
                    "name": "PDF",
                    "result": fileinfo,
                    "template": "workflows/results/fft.html"
                }]
            )
        else:
            obj.log.info("No PDF found.")
    else:
        eng.log.info("There was already a pdf register for this record,"
                     "perhaps a duplicate task in you workflow.")


def plot_extract(plotextractor_types=("latex",)):
    """Perform the plotextraction step.

    Download tarball for each harvested/converted record,
    then run plotextrator.

    Update converted xml files with generated xml or add it for upload.

    :param plotextractor_types:
    :return: :raise workflows_error.WorkflowError:
    """
    @wraps(plot_extract)
    def _plot_extract(obj, eng):
        from invenio.utils.plotextractor.api import (
            get_tarball_from_arxiv,
            get_marcxml_plots_from_tarball
        )
        from invenio.modules.workflows.utils import convert_marcxml_to_bibfield
        from invenio.utils.shell import Timeout

        if "_result" not in obj.extra_data:
            obj.extra_data["_result"] = {}

        repository = obj.extra_data.get("repository", {})
        arguments = repository.get("arguments", {})

        chosen_type = plotextractor_types

        if not chosen_type:
            chosen_type = arguments.get('p_extraction-source', [])

        if not isinstance(chosen_type, list):
            chosen_type = [chosen_type]

        if 'latex' in chosen_type:
            # Run LaTeX plotextractor
            if "tarball" not in obj.extra_data["_result"]:
                extract_path = os.path.join(
                    cfg.get('OAIHARVESTER_STORAGEDIR', cfg.get('CFG_TMPSHAREDDIR')),
                    str(eng.uuid)
                )
                tarball = get_tarball_from_arxiv(
                    obj.data.get(cfg.get('OAIHARVESTER_RECORD_ARXIV_ID_LOOKUP')),
                    extract_path
                )
                if tarball is None:
                    obj.log.error("No tarball found")
                    return
                obj.extra_data["_result"]["tarball"] = tarball
            else:
                tarball = obj.extra_data["_result"]["tarball"]

            try:
                marcxml = get_marcxml_plots_from_tarball(tarball)
            except Timeout:
                eng.log.error(
                    'Timeout during tarball extraction on {0}'.format(tarball)
                )
            if marcxml:
                # We store the path to the directory the tarball contents lives
                new_dict = convert_marcxml_to_bibfield(marcxml)
                _attach_files_to_obj(obj, new_dict)
                obj.update_task_results(
                    "Plots",
                    [{
                        "name": "Plots",
                        "result": new_dict["fft"],
                        "template": "workflows/results/plots.html"
                    }]
                )

    return _plot_extract


def refextract(obj, eng):
    """Perform the reference extraction step.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    from invenio.legacy.refextract.api import extract_references_from_file_xml
    from invenio.utils.plotextractor.api import get_pdf_from_arxiv
    from invenio.modules.workflows.utils import convert_marcxml_to_bibfield

    if "_result" not in obj.extra_data:
        obj.extra_data["_result"] = {}

    try:
        pdf = obj.extra_data["_result"]["pdf"]
    except KeyError:
        pdf = None

    if not pdf:
        extract_path = os.path.join(
            cfg.get('OAIHARVESTER_STORAGEDIR', cfg.get('CFG_TMPSHAREDDIR')),
            str(eng.uuid)
        )
        pdf = get_pdf_from_arxiv(
            obj.data.get(cfg.get('OAIHARVESTER_RECORD_ARXIV_ID_LOOKUP')),
            extract_path
        )
        obj.extra_data["_result"]["pdf"] = pdf

    if pdf and os.path.isfile(pdf):
        references_xml = extract_references_from_file_xml(
            obj.extra_data["_result"]["pdf"]
        )
        if references_xml:
            updated_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' \
                          '<collection>\n' + references_xml + \
                          "\n</collection>"
            new_dict_representation = convert_marcxml_to_bibfield(updated_xml)
            obj.data["reference"] = new_dict_representation["reference"]
            obj.log.info("Extracted {0} references".format(len(obj.data["reference"])))
            obj.update_task_results(
                "References",
                [{"name": "References",
                  "result": new_dict_representation['reference'],
                  "template": "workflows/results/refextract.html"}]
            )
        else:
            obj.log.info("No references extracted")
    else:
        obj.log.error("Not able to download and process the PDF")


def author_list(obj, eng):
    """Perform the special authorlist extraction step.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    from invenio.legacy.oaiharvest.utils import (translate_fieldvalues_from_latex,
                                                 find_matching_files)
    from invenio.legacy.bibrecord import create_records, record_xml_output
    from invenio.legacy.bibconvert.xslt_engine import convert
    from invenio.utils.plotextractor.api import get_tarball_from_arxiv
    from invenio.utils.plotextractor.cli import get_defaults
    from invenio.modules.workflows.utils import convert_marcxml_to_bibfield
    from invenio.utils.plotextractor.converter import untar
    from invenio.utils.shell import Timeout

    identifiers = obj.data.get(cfg.get('OAIHARVESTER_RECORD_ARXIV_ID_LOOKUP'), "")
    if "_result" not in obj.extra_data:
        obj.extra_data["_result"] = {}
    if "tarball" not in obj.extra_data["_result"]:
        extract_path = os.path.join(
            cfg.get('OAIHARVESTER_STORAGEDIR', cfg.get('CFG_TMPSHAREDDIR')),
            str(eng.uuid)
        )
        tarball = get_tarball_from_arxiv(
            obj.data.get(cfg.get('OAIHARVESTER_RECORD_ARXIV_ID_LOOKUP')),
            extract_path
        )
        if tarball is None:
            obj.log.error("No tarball found")
            return
    else:
        tarball = obj.extra_data["_result"]["tarball"]

    # FIXME
    tarball = str(tarball)
    sub_dir, dummy = get_defaults(tarball,
                                  cfg['CFG_TMPDIR'], "")

    try:
        untar(tarball, sub_dir)
        obj.log.info("Extracted tarball to: {0}".format(sub_dir))
    except Timeout:
        eng.log.error('Timeout during tarball extraction on %s' % (
            obj.extra_data["_result"]["tarball"]))

    xml_files_list = find_matching_files(sub_dir, ["xml"])

    obj.log.info("Found xmlfiles: {0}".format(xml_files_list))

    authors = ""

    for xml_file in xml_files_list:
        xml_file_fd = open(xml_file, "r")
        xml_content = xml_file_fd.read()
        xml_file_fd.close()

        match = REGEXP_AUTHLIST.findall(xml_content)
        if match:
            obj.log.info("Found a match for author extraction")

            a_stylesheet = obj.extra_data["repository"]["arguments"].get(
                "a_stylesheet"
            ) or "authorlist2marcxml.xsl"
            authors = convert(xml_content, a_stylesheet)
            authorlist_record = create_records(authors)
            if len(authorlist_record) == 1:
                if authorlist_record[0][0] is None:
                    eng.log.error("Error parsing authorlist record for id: %s" % (
                        identifiers,))
                authorlist_record = authorlist_record[0][0]

            # Convert any LaTeX symbols in authornames
            translate_fieldvalues_from_latex(authorlist_record, '100', code='a')
            translate_fieldvalues_from_latex(authorlist_record, '700', code='a')

            author_xml = record_xml_output(authorlist_record)
            if author_xml:
                updated_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n' \
                              + record_xml_output(authorlist_record) + '</collection>'
                new_dict_representation = convert_marcxml_to_bibfield(updated_xml)
                obj.data["authors"] = new_dict_representation["authors"]
                obj.update_task_results(
                    "authors",
                    [{
                        "name": "authors",
                        "results": new_dict_representation["authors"]
                    }]
                )
                obj.update_task_results(
                    "number_of_authors",
                    [{
                        "name": "number_of_authors",
                        "results": new_dict_representation["number_of_authors"]
                    }]
                )
                break


def upload_step(obj, eng):
    """Perform the upload step.

    :param obj: BibWorkflowObject to process
    :param eng: BibWorkflowEngine processing the object
    """
    from invenio.legacy.oaiharvest.dblayer import create_oaiharvest_log_str
    from invenio.modules.records.api import Record
    from invenio.legacy.bibsched.bibtask import task_low_level_submission

    repository = obj.extra_data.get("repository", {})
    sequence_id = random.randrange(1, 60000)

    arguments = repository.get("arguments", {})

    default_args = []
    default_args.extend(['-I', str(sequence_id)])
    if arguments.get('u_name', ""):
        default_args.extend(['-N', arguments.get('u_name', "")])
    if arguments.get('u_priority', 5):
        default_args.extend(['-P', str(arguments.get('u_priority', 5))])

    extract_path = os.path.join(
        cfg.get('OAIHARVESTER_STORAGEDIR', cfg.get('CFG_TMPSHAREDDIR')),
        str(eng.uuid)
    )
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)

    filepath = extract_path + os.sep + str(obj.id)
    if "f" in repository.get("postprocess", []):
        # We have a filter.
        file_uploads = [
            ("{0}.insert.xml".format(filepath), ["-i"]),
            ("{0}.append.xml".format(filepath), ["-a"]),
            ("{0}.correct.xml".format(filepath), ["-c"]),
            ("{0}.holdingpen.xml".format(filepath), ["-o"]),
        ]
    else:
        # We do not, so we get the data from the record
        marcxml_value = Record(obj.data.dumps()).legacy_export_as_marc()
        file_fd = open(filepath, 'w')
        file_fd.write(marcxml_value)
        file_fd.close()
        file_uploads = [(filepath, ["-r", "-i"])]

    task_id = None
    for location, mode in file_uploads:
        if os.path.exists(location):
            try:
                args = mode + [filepath] + default_args
                task_id = task_low_level_submission("bibupload",
                                                    "oaiharvest",
                                                    *tuple(args))
                repo_id = repository.get("id")
                if repo_id:
                    create_oaiharvest_log_str(
                        task_id,
                        repo_id,
                        obj.get_data()
                    )
            except Exception as msg:
                eng.log.error(
                    "An exception during submitting oaiharvest task occured : %s " % (
                        str(msg)))
    if task_id is None:
        eng.log.error("an error occurred while uploading %s from %s" %
                      (filepath, repository.get("name", "Unknown")))
    else:
        eng.log.info(
            "material harvested from source %s was successfully uploaded" %
            (repository.get("name", "Unknown"),))
    eng.log.info("end of upload")


def filter_step(obj, eng):
    """Run an external python script."""
    from invenio.modules.records.api import Record
    from invenio.utils.shell import run_shell_command

    repository = obj.extra_data.get("repository", {})
    arguments = repository.get("arguments", {})
    script_name = arguments.get("f_filter-file")
    if script_name:
        marcxml_value = Record(obj.data.dumps()).legacy_export_as_marc()
        extract_path = os.path.join(
            cfg.get('OAIHARVESTER_STORAGEDIR', cfg.get('CFG_TMPSHAREDDIR')),
            str(eng.uuid)
        )
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)

        # Now we launch BibUpload tasks for the final MARCXML files
        marcxmlfile = extract_path + os.sep + str(obj.id)
        file_fd = open(marcxmlfile, 'w')
        file_fd.write(marcxml_value)
        file_fd.close()

        exitcode, cmd_stdout, cmd_stderr = run_shell_command(
            cmd="%s '%s'",
            args=(str(script_name),
                  str(marcxmlfile)))
        if exitcode != 0 or cmd_stderr != "":
            obj.log.error(
                "Error while running filtering script on %s\nError:%s"
                % (marcxmlfile, cmd_stderr)
            )
        else:
            obj.log.info(cmd_stdout)
    else:
        obj.log.error("No script file found!")


def check_record(obj, eng):
    """Check if there is a valid record in the data.

    If not, skip this object.
    """
    try:
        assert obj.data
        assert obj.data != '<?xml version="1.0"?>\n<collection/>\n'
    except AssertionError as e:
        obj.log.info("No data found in record. Skipping: {0}".format(str(e)))
        eng.continueNextToken()
