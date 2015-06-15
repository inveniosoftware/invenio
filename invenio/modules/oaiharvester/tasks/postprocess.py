# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
    from invenio.utils.plotextractor.getter import harvest_single
    from invenio.modules.workflows.utils import convert_marcxml_to_bibfield

    if "result" not in obj.extra_data:
        obj.extra_data["_result"] = {}

    if "pdf" not in obj.extra_data["_result"]:
        extract_path = os.path.join(
            cfg['CFG_TMPSHAREDDIR'],
            str(eng.uuid)
        )
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)
        tarball, pdf = harvest_single(
            obj.data["system_control_number"]["value"],
            extract_path, ["pdf"])
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
            fulltext_xml = (
                "  <datafield tag=\"FFT\" ind1=\" \" ind2=\" \">\n"
                "    <subfield code=\"a\">%(url)s</subfield>\n"
                "    <subfield code=\"t\">%(doctype)s</subfield>\n"
                "    </datafield>"
            ) % {'url': obj.extra_data["_result"]["pdf"],
                 'doctype': doctype}
            updated_xml = '<?xml version="1.0"?>\n' \
                          '<collection>\n<record>\n' + fulltext_xml + \
                          '</record>\n</collection>'

            new_dict_representation = convert_marcxml_to_bibfield(updated_xml)
            try:
                if isinstance(new_dict_representation["fft"], list):
                    for element in new_dict_representation["fft"]:
                        obj.data['fft'].append(element)
                else:
                    obj.data['fft'].append(new_dict_representation["fft"])
            except (KeyError, TypeError):
                obj.data['fft'] = [new_dict_representation['fft']]

            filename = os.path.basename(pdf)
            fileinfo = {
                "type": "Fulltext",
                "filename": filename,
                "full_path": pdf,
            }

            obj.add_task_result(filename,
                                fileinfo,
                                "workflows/results/files.html")
        else:
            obj.log.error("No PDF found.")
    else:
        eng.log.info("There was already a pdf register for this record,"
                     "perhaps a duplicate task in you workflow.")


def plot_extract(plotextractor_types=("latex",)):
    """Perform the plotextraction step.

    :param plotextractor_types:
    :return: :raise workflows_error.WorkflowError:
    """
    @wraps(plot_extract)
    def _plot_extract(obj, eng):
        """Perform the plotextraction step.

        Download tarball for each harvested/converted record,
        then run plotextrator.

        Update converted xml files with generated xml or add it for upload.
        """
        from invenio.utils.plotextractor.output_utils import (create_MARC,
                                                              create_contextfiles,
                                                              prepare_image_data,
                                                              remove_dups)
        from invenio.utils.plotextractor.cli import (get_defaults, extract_captions,
                                                     extract_context)
        from invenio.utils.plotextractor.converter import convert_images
        from invenio.utils.plotextractor.getter import harvest_single
        from invenio.utils.plotextractor.converter import untar
        from invenio.modules.workflows.errors import WorkflowError
        from invenio.modules.workflows.utils import convert_marcxml_to_bibfield
        from invenio.utils.shell import run_shell_command, Timeout

        if "_result" not in obj.extra_data:
            obj.extra_data["_result"] = {}

        repository = obj.extra_data.get("repository", {})
        arguments = repository.get("arguments", {})

        if 'p_extraction-source' not in arguments:
            p_extraction_source = plotextractor_types
        else:
            p_extraction_source = arguments.get('p_extraction-source', "")

        if not isinstance(p_extraction_source, list):
            p_extraction_source = [p_extraction_source]

        if 'latex' in p_extraction_source:
            # Run LaTeX plotextractor
            if "tarball" not in obj.extra_data["_result"]:
                extract_path = os.path.join(
                    cfg['CFG_TMPSHAREDDIR'],
                    str(eng.uuid)
                )
                if not os.path.exists(extract_path):
                    os.makedirs(extract_path)
                tarball, pdf = harvest_single(
                    obj.data["system_control_number"]["value"], extract_path,
                    ["tarball"])
                tarball = str(tarball)
                if tarball is None:
                    raise WorkflowError(
                        str("Error harvesting tarball from id: %s %s" %
                            (obj.data["system_control_number"]["value"],
                             extract_path)),
                        eng.uuid,
                        id_object=obj.id)

                obj.extra_data["_result"]["tarball"] = tarball
            else:
                tarball = obj.extra_data["_result"]["tarball"]

            sub_dir, refno = get_defaults(tarball, cfg['CFG_TMPDIR'], "")

            tex_files = None
            image_list = None
            try:
                extracted_files_list, image_list, tex_files = untar(tarball,
                                                                    sub_dir)
            except Timeout:
                eng.log.error(
                    'Timeout during tarball extraction on %s' % (tarball,))

            converted_image_list = convert_images(image_list)
            eng.log.info('converted %d of %d images found for %s' % (
                len(converted_image_list),
                len(image_list),
                os.path.basename(tarball)))
            extracted_image_data = []
            if tex_files == [] or tex_files is None:
                eng.log.error(
                    '%s is not a tarball' % (os.path.split(tarball)[-1],))
                run_shell_command('rm -r %s', (sub_dir,))
            else:
                for tex_file in tex_files:
                    # Extract images, captions and labels
                    partly_extracted_image_data = extract_captions(tex_file,
                                                                   sub_dir,
                                                                   converted_image_list)
                    if partly_extracted_image_data:
                        # Add proper filepaths and do various cleaning
                        cleaned_image_data = prepare_image_data(
                            partly_extracted_image_data,
                            tex_file, converted_image_list)
                        # Using prev. extracted info, get contexts for each
                        # image found
                        extracted_image_data.extend(
                            (extract_context(tex_file, cleaned_image_data)))

            if extracted_image_data:
                extracted_image_data = remove_dups(extracted_image_data)
                create_contextfiles(extracted_image_data)
                marc_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n'
                marc_xml += create_MARC(extracted_image_data, tarball, None)
                marc_xml += "\n</collection>"

                if marc_xml:
                    # We store the path to the directory  the tarball
                    # contents live
                    # Read and grab MARCXML from plotextractor run
                    new_dict = convert_marcxml_to_bibfield(marc_xml)

                    try:
                        if isinstance(new_dict["fft"], list):
                            for element in new_dict["fft"]:
                                obj.data['fft'].append(element)
                        else:
                            obj.data['fft'].append(new_dict["fft"])

                    except KeyError:
                        obj.data['fft'] = [new_dict['fft']]
                    obj.add_task_result("filesfft", new_dict["fft"])
                    obj.add_task_result("number_picture_converted",
                                        len(converted_image_list))
                    obj.add_task_result("number_of_picture_total",
                                        len(image_list))

    return _plot_extract


def refextract(obj, eng):
    """Perform the reference extraction step.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    from invenio.legacy.refextract.api import extract_references_from_file_xml
    from invenio.utils.plotextractor.getter import harvest_single
    from invenio.modules.workflows.utils import convert_marcxml_to_bibfield

    if "_result" not in obj.extra_data:
        obj.extra_data["_result"] = {}

    pdf = None

    if "_result" in obj.extra_data and "pdf" in obj.extra_data["_result"]:
        pdf = obj.extra_data["_result"]["pdf"]

    if not pdf:
        extract_path = os.path.join(
            cfg['CFG_TMPSHAREDDIR'],
            str(eng.uuid)
        )
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)
        tarball, pdf = harvest_single(
            obj.data["system_control_number"]["value"], extract_path, ["pdf"]
        )
        obj.extra_data["_result"]["pdf"] = pdf

    if pdf and os.path.isfile(obj.extra_data["_result"]["pdf"]):
        references_xml = extract_references_from_file_xml(
            obj.extra_data["_result"]["pdf"])
        if references_xml:
            obj.log.info("Found references: {0}".format(references_xml))
            updated_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' \
                          '<collection>\n' + references_xml + \
                          "\n</collection>"

            new_dict_representation = convert_marcxml_to_bibfield(updated_xml)
            try:
                obj.data['reference'].append(
                    new_dict_representation["reference"])
            except KeyError:
                if 'reference' in new_dict_representation:
                    obj.data['reference'] = [
                        new_dict_representation['reference']]
            obj.add_task_result("References",
                                new_dict_representation['reference'],
                                "workflows/results/refextract.html")
        else:
            obj.log.info("No references")
    else:
        obj.log.error("Not able to download and process the PDF ")


def author_list(obj, eng):
    """Perform the special authorlist extraction step.

    :param obj: Bibworkflow Object to process
    :param eng: BibWorkflowEngine processing the object
    """
    from invenio.legacy.oaiharvest.utils import (translate_fieldvalues_from_latex,
                                                 find_matching_files)
    from invenio.legacy.bibrecord import create_records, record_xml_output
    from invenio.legacy.bibconvert.xslt_engine import convert
    from invenio.utils.plotextractor.cli import get_defaults
    from invenio.modules.workflows.utils import convert_marcxml_to_bibfield
    from invenio.utils.plotextractor.getter import harvest_single
    from invenio.modules.workflows.errors import WorkflowError
    from invenio.utils.plotextractor.converter import untar
    from invenio.utils.shell import Timeout

    identifiers = obj.data["system_control_number"]["value"]
    if "_result" not in obj.extra_data:
        obj.extra_data["_result"] = {}
    if "tarball" not in obj.extra_data["_result"]:
        extract_path = os.path.join(
            cfg['CFG_TMPSHAREDDIR'],
            str(eng.uuid)
        )
        if not os.path.exists(extract_path):
            os.makedirs(extract_path)
        tarball, pdf = harvest_single(
            obj.data["system_control_number"]["value"], extract_path,
            ["tarball"])
        tarball = str(tarball)
        if tarball is None:
            raise WorkflowError(str(
                "Error harvesting tarball from id: %s %s" % (
                    identifiers, extract_path)), eng.uuid, id_object=obj.id)
        obj.extra_data["_result"]["tarball"] = tarball

    sub_dir, dummy = get_defaults(obj.extra_data["_result"]["tarball"],
                                  cfg['CFG_TMPDIR'], "")

    try:
        untar(obj.extra_data["_result"]["tarball"], sub_dir)
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

            updated_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n' \
                          + record_xml_output(authorlist_record) + '</collection>'
            if not None == updated_xml:
                # We store the path to the directory  the tarball contents live
                # Read and grab MARCXML from plotextractor run
                new_dict_representation = convert_marcxml_to_bibfield(updated_xml)
                obj.data['authors'] = new_dict_representation["authors"]
                obj.data['number_of_authors'] = new_dict_representation[
                    "number_of_authors"]
                obj.add_task_result("authors", new_dict_representation["authors"])
                obj.add_task_result("number_of_authors",
                                    new_dict_representation["number_of_authors"])
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
        cfg['CFG_TMPSHAREDDIR'],
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
            cfg['CFG_TMPSHAREDDIR'],
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
