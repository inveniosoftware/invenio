## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
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

import os
import random
import time
import glob
import re
import traceback

from invenio.legacy.bibupload.engine import (find_record_from_recid,
                                             find_record_from_sysno,
                                             find_records_from_extoaiid,
                                             find_record_from_oaiid,
                                             find_record_from_doi
                                             )
from invenio.legacy.oaiharvest.dblayer import create_oaiharvest_log_str

from invenio.base.config import (CFG_TMPSHAREDDIR,
                                 CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT,
                                 CFG_TMPDIR,
                                 CFG_INSPIRE_SITE)
from invenio.legacy.oaiharvest.utils import (record_extraction_from_file,
                                             collect_identifiers,
                                             harvest_step,
                                             translate_fieldvalues_from_latex,
                                             find_matching_files,
                                             )
from invenio.legacy.bibsched.bibtask import (task_sleep_now_if_required,
                                             task_low_level_submission
                                             )
from invenio.modules.oaiharvester.models import OaiHARVEST
from invenio.modules.records.api import Record
from invenio.modules.workflows.errors import WorkflowError
from invenio.legacy.refextract.api import extract_references_from_file_xml
from invenio.legacy.bibrecord import (create_records,
                                      record_xml_output
                                      )
from invenio.utils.plotextractor.output_utils import (create_MARC,
                                                      create_contextfiles,
                                                      prepare_image_data,
                                                      remove_dups
                                                      )
from invenio.utils.plotextractor.getter import (harvest_single,
                                                make_single_directory
                                                )

from invenio.utils.plotextractor.cli import (get_defaults,
                                             extract_captions,
                                             extract_context
                                             )
from invenio.utils.shell import (run_shell_command,
                                 Timeout
                                 )
import invenio.legacy.template
from invenio.utils.plotextractor.converter import (untar,
                                                   convert_images
                                                   )
from invenio.utils.serializers import deserialize_via_marshal

oaiharvest_templates = invenio.legacy.template.load('oaiharvest')

REGEXP_REFS = re.compile("<record.*?>.*?<controlfield .*?>.*?</controlfield>(.*?)</record>", re.DOTALL)
REGEXP_AUTHLIST = re.compile("<collaborationauthorlist.*?</collaborationauthorlist>", re.DOTALL)


def add_metadata_to_extra_data(obj, eng):
    """
    Creates bibrecord from object data and
    populates extra_data with metadata
    """
    from invenio.legacy.bibrecord import create_record, record_get_field_value

    record = create_record(obj.data)

    obj.extra_data['redis_search']['category'] = \
        record_get_field_value(record[0], '037', code='c')
    obj.extra_data['redis_search']['title'] = \
        record_get_field_value(record[0], '245', code='a')
    obj.extra_data['redis_search']['source'] = \
        record_get_field_value(record[0], '035', code='9')


add_metadata_to_extra_data.__title__ = "Metadata Extraction"
add_metadata_to_extra_data.__description__ = "Populates object's extra_data with metadata"


def approve_record(obj, eng):
    """
    Will add the approval widget to the record
    """

    obj.extra_data["last_task_name"] = 'Record Approval'
    eng.log.info("last task name: approve_record")
    try:
        obj.extra_data['message'] = 'Record needs approval. Click on widget to resolve.'
        eng.log.info("Adding the approval widget to %s" % obj.id)
        obj.extra_data['widget'] = 'approval_widget'
        eng.halt("Record needs approval")
    except KeyError:
        # Log the error
        obj.extra_data["error_msg"] = 'Could not assign widget'


approve_record.__title__ = "Record Approval"
approve_record.__description__ = "This task assigns the approval widget to a record."


def convert_record_to_bibfield(obj, eng):
    """
    Convert a record in data into a 'dictionary'
    thanks to BibField
    """
    from invenio.base.records.api import create_record

    eng.log.info("last task name: convert_record_to_bibfield")
    obj.data = create_record(obj.data).dumps()
    eng.log.info("Conversion succeed")


def init_harvesting(obj, eng):
    """
    This function gets all the option linked to the task and stores them into the
    object to be used later.
    """
    eng.log.info("last task name: init_harvesting")
    try:
        obj.extra_data["options"] = eng.extra_data["options"]
    except KeyError:
        eng.log.error("Non Critical Error: No options", "No options for this task have been found. It is possible"
                                                        "that the fillowing task could failed or work not as expected")
        obj.extra_data["options"] = {}
    eng.log.info("end of init_harvesting")


def get_repositories_list(repositories):
    """
    Here we are retrieving the oaiharvest configuration for the task.
    It will allows in the future to do all the correct operations.
    """

    def _get_repositories_list(obj, eng):


        eng.log.info("last task name: _get_repositories_list")

        reposlist_temp = None

        if repositories:
            for reposname in repositories:
                reposlist_temp = OaiHARVEST.get(OaiHARVEST.name == reposname).all()
        else:

            reposlist_temp = OaiHARVEST.get(OaiHARVEST.name != "").all()

        return reposlist_temp

    return _get_repositories_list


def harvest_records(obj, eng):
    """
    Run the harvesting task.  The row argument is the oaiharvest task
    queue row, containing if, arguments, etc.
    Return 1 in case of success and 0 in case of failure.
    """
    eng.log.info("last task name: harvest_records")
    obj.extra_data["last_task_name"] = 'harvest_records'
    harvested_identifier_list = []

    harvestpath = "%s_%d_%s_" % ("%s/oaiharvest_%s" % (CFG_TMPSHAREDDIR, eng.uuid),
                                 1, time.strftime("%Y%m%d%H%M%S"))

    # ## go ahead: check if user requested from-until harvesting
    try:
        if "dates" not in obj.extra_data["options"]:
            obj.extra_data["options"]["dates"] = {}
        if "identifiers" not in obj.extra_data["options"]:
            obj.extra_data["options"]["identifiers"] = {}
    except TypeError:
        obj.extra_data["options"] = {"dates": {}, "identifiers": {}}

    task_sleep_now_if_required()

    arguments = obj.extra_data["repository"].arguments
    if arguments:
        eng.log.info("running with post-processes: %r" % (arguments,))

    # Harvest phase
    try:
        harvested_files_list = harvest_step(obj.data,
                                            harvestpath,
                                            obj.extra_data["options"]["identifiers"],
                                            obj.extra_data["options"]["dates"])
    except Exception:
        eng.log.error("Error while harvesting %s. Skipping." % (obj.data,))

        raise WorkflowError("Error while harvesting %r. Skipping." % (obj.data,),
                            id_workflow=eng.uuid)

    if len(harvested_files_list) == 0:
        eng.log.error("No records harvested for %s" % (obj.data.name,))
        return None
        # Retrieve all OAI IDs and set active list

    harvested_identifier_list.append(collect_identifiers(harvested_files_list))

    if len(harvested_files_list) != len(harvested_identifier_list[0]):
        # Harvested files and its identifiers are 'out of sync', abort harvest
        msg = "Harvested files miss identifiers for %s" % (arguments,)
        eng.log.info(msg)
        raise WorkflowError(msg, id_workflow=eng.uuid)
    eng.log.info("%d files harvested and processed" % (len(harvested_files_list),))
    eng.log.info("End harvest records task")

harvest_records.__id__ = "h"


def get_records_from_file(path=None):
    def _get_records_from_file(obj, eng):

        eng.log.info("last task name: _get_records_from_file")

        if not "LoopData" in eng.extra_data:
            eng.extra_data["LoopData"] = {}

        if "get_records_from_file" not in eng.extra_data["LoopData"]:
            if path:
                eng.extra_data["LoopData"].update({"get_records_from_file": record_extraction_from_file(path)})
            else:
                eng.extra_data["LoopData"].update({"get_records_from_file": record_extraction_from_file(obj.data)})
        return eng.extra_data["LoopData"]["get_records_from_file"]

    return _get_records_from_file


def get_eng_uuid_harvested(obj, eng):
    """
    Simple function which allows to retrieve the uuid of the eng in the workflow
    for printing by example
    """
    eng.log.info("last task name: get_eng_uuid_harvested")
    return "*" + str(eng.uuid) + "*.harvested"


def get_files_list(path, parameter):
    def _get_files_list(obj, eng):
        eng.log.info("last task name: get_files_list")
        if callable(parameter):
            unknown = parameter(obj, eng)
        else:
            unknown = parameter
        result = glob.glob1(path, unknown)
        for i in range(0, len(result)):
            result[i] = path + os.sep + result[i]
        return result

    return _get_files_list


def convert_record(stylesheet="oaidc2marcxml.xsl"):
    def _convert_record(obj, eng):
        """
        Will convert the object data, if XML, using the given stylesheet
        """
        eng.log.info("last task name: convert_record")
        from invenio.legacy.bibconvert.xslt_engine import convert

        obj.extra_data["last_task_name"] = 'Convert Record'
        eng.log.info("Starting conversion using %s stylesheet" %
                     (stylesheet,))

        try:
            obj.data = convert(obj.data, stylesheet)
        except Exception as e:
            msg = "Could not convert record: %s\n%s" % \
                  (str(e), traceback.format_exc())
            obj.extra_data["error_msg"] = msg
            eng.log.error("Error: %s" % (msg,))
            raise WorkflowError("Error: %s" % (msg,),
                                id_workflow=eng.uuid)

    return _convert_record


def fulltext_download(obj, eng):
    """
    Performs the fulltext download step.
    Only for arXiv
    """
    eng.log.info("full-text attachment step started")
    task_sleep_now_if_required()

    if "pdf" not in obj.extra_data["options"]["identifiers"]:
        extract_path = make_single_directory(CFG_TMPSHAREDDIR, eng.uuid)
        tarball, pdf = harvest_single(obj.data["system_control_number"]["value"],
                                      extract_path, ["pdf"])
        time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT)
        arguments = obj.extra_data["repository"].arguments
        if not arguments['t_doctype'] == '':
            doctype = arguments['t_doctype']
        else:
            doctype = 'arXiv'
        if pdf:
            obj.extra_data["options"]["identifiers"]["pdf"] = pdf
            fulltext_xml = ("  <datafield tag=\"FFT\" ind1=\" \" ind2=\" \">\n"
                            "    <subfield code=\"a\">%(url)s</subfield>\n"
                            "    <subfield code=\"t\">%(doctype)s</subfield>\n"
                            "    </datafield>"
                            ) % {'url': obj.extra_data["options"]["identifiers"]["pdf"],
                                 'doctype': doctype}

            updated_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n<record>\n' + fulltext_xml + \
                          '</record>\n</collection>'
            from invenio.modules.records.api import create_record

            new_dict_representation = create_record(updated_xml).dumps()
            try:
                obj.data['fft'].append(new_dict_representation["fft"])
            except:
                obj.data['fft'] = [new_dict_representation['fft']]


def quick_match_record(obj, eng):
    """
    Retrieve the record Id from a record by using tag 001 or SYSNO or OAI ID or DOI
    tag. opt_mod is the desired mode.

    001 fields even in the insert mode
    """
    eng.log.info("last task name: quick_match_record")
    obj.extra_data["last_task_name"] = 'Quick Match Record'

    function_dictionnary = {'recid': find_record_from_recid, 'system_number': find_record_from_sysno,
                            'oaiid': find_record_from_oaiid, 'system_control_number': find_records_from_extoaiid,
                            'doi': find_record_from_doi}

    my_json_reader = Record(obj.data)
    try:
        identifiers = {}
        #identifiers = my_json_reader.get_persistent_identifiers()
    except KeyError:
        identifiers = {}

    if not "recid" in identifiers:
        for identifier in identifiers:
            recid = function_dictionnary[identifier](identifiers[identifier]["value"])
            if recid:
                obj.data['recid']['value'] = recid
                return True
        return False
    else:
        return True


def upload_record(mode="ir"):
    def _upload_record(obj, eng):
        eng.log.info("last task name: upload_record")
        from invenio.legacy.bibsched.bibtask import task_low_level_submission

        obj.extra_data["last_task_name"] = 'Upload Record'

        eng.log_info("Saving data to temporary file for upload")
        filename = obj.save_to_file()
        params = ["-%s" % (mode,), filename]
        task_id = task_low_level_submission("bibupload", "bibworkflow",
                                            *tuple(params))
        eng.log_info("Submitted task #%s" % (task_id,))

    _upload_record.__title__ = "Upload Record"
    _upload_record.__description__ = "Uploads the record using BibUpload"
    return _upload_record


upload_record.__id__ = "u"


def plot_extract(plotextractor_types):
    def _plot_extract(obj, eng):
        """
        Performs the plotextraction step.
        """

        eng.log.info("last task name: plot_extract")
        obj.extra_data["last_task_name"] = 'plotextraction'
        eng.log.info("plotextraction step started")
        # Download tarball for each harvested/converted record, then run plotextrator.
        # Update converted xml files with generated xml or add it for upload
        task_sleep_now_if_required()

        if 'latex' in plotextractor_types:
            # Run LaTeX plotextractor
            if "tarball" not in obj.extra_data["options"]["identifiers"]:
                # turn oaiharvest_23_1_20110214161632_converted -> oaiharvest_23_1_material
                # to let harvested material in same folder structure
                extract_path = make_single_directory(CFG_TMPSHAREDDIR, eng.uuid)
                tarball, pdf = harvest_single(obj.data["system_control_number"]["value"], extract_path, ["tarball"])
                tarball = str(tarball)
                time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT)

                if tarball is None:
                    raise WorkflowError("Error harvesting tarball from id: %s %s" %
                                        (obj.data["system_control_number"]["value"], extract_path),
                                        id_workflow=eng.uuid)
                obj.extra_data["options"]["identifiers"]["tarball"] = tarball
            else:
                tarball = obj.extra_data["options"]["identifiers"]["tarball"]

            sub_dir, refno = get_defaults(tarball, CFG_TMPDIR, "")

            tex_files = None
            image_list = None
            try:
                extracted_files_list, image_list, tex_files = untar(tarball, sub_dir)
            except Timeout:
                eng.log.error('Timeout during tarball extraction on %s' % (tarball,))

            converted_image_list = convert_images(image_list)
            eng.log.info('converted %d of %d images found for %s' % (len(converted_image_list),
                                                                     len(image_list),
                                                                     os.path.basename(tarball)))
            extracted_image_data = []
            if tex_files == [] or tex_files is None:
                eng.log.error('%s is not a tarball' % (os.path.split(tarball)[-1],))
                run_shell_command('rm -r %s', (sub_dir,))
            else:
                for tex_file in tex_files:
                # Extract images, captions and labels
                    partly_extracted_image_data = extract_captions(tex_file, sub_dir,
                                                                   converted_image_list)
                    if partly_extracted_image_data:
                        # Add proper filepaths and do various cleaning
                        cleaned_image_data = prepare_image_data(partly_extracted_image_data,
                                                                tex_file, converted_image_list)
                        # Using prev. extracted info, get contexts for each image found
                        extracted_image_data.extend((extract_context(tex_file, cleaned_image_data)))

            if extracted_image_data:
                extracted_image_data = remove_dups(extracted_image_data)
                create_contextfiles(extracted_image_data)
                marc_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n'
                marc_xml = marc_xml + create_MARC(extracted_image_data, tarball, None)
                marc_xml += "\n</collection>"

                if marc_xml:
                    from invenio.modules.records.api import create_record
                    # We store the path to the directory  the tarball contents live
                    # Read and grab MARCXML from plotextractor run
                    new_dict_representation = create_record(marc_xml).dumps()
                    try:
                        obj.data['fft'].append(new_dict_representation["fft"])
                    except KeyError:
                        obj.data['fft'] = [new_dict_representation['fft']]

    return _plot_extract


def refextract(obj, eng):
    """
    Performs the reference extraction step.
    """
    eng.log.info("refextraction step started")

    task_sleep_now_if_required()

    if "pdf" not in obj.extra_data["options"]["identifiers"]:
        extract_path = make_single_directory(CFG_TMPSHAREDDIR, eng.uuid)
        tarball, pdf = harvest_single(obj.data["system_control_number"]["value"], extract_path, ["pdf"])
        time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT)
        if pdf is not None:
            obj.extra_data["options"]["identifiers"]["pdf"] = pdf

    elif not os.path.isfile(obj.extra_data["options"]["identifiers"]["pdf"]):
        extract_path = make_single_directory(CFG_TMPSHAREDDIR, eng.uuid)
        tarball, pdf = harvest_single(obj.data["system_control_number"]["value"], extract_path, ["pdf"])
        time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT)
        if pdf is not None:
            obj.extra_data["options"]["identifiers"]["pdf"] = pdf

    if os.path.isfile(obj.extra_data["options"]["identifiers"]["pdf"]):

        cmd_stdout = extract_references_from_file_xml(obj.extra_data["options"]["identifiers"]["pdf"])
        references_xml = REGEXP_REFS.search(cmd_stdout)

        if references_xml:
            updated_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n<record>' + references_xml.group(1) + \
                          "</record>\n</collection>"

            from invenio.modules.records.api import create_record

            new_dict_representation = create_record(updated_xml).dumps()
            try:
                obj.data['reference'].append(new_dict_representation["reference"])
            except KeyError:
                if 'reference' in new_dict_representation:
                    obj.data['reference'] = [new_dict_representation['reference']]
    else:
        obj.log.error("Not able to download and process the PDF ")


def author_list(obj, eng):
    """
    Performs the special authorlist extraction step (Mostly INSPIRE/CERN related).
    """
    eng.log.info("last task name: author_list")
    eng.log.info("authorlist extraction step started")

    identifiers = obj.data["system_control_number"]["value"]
    task_sleep_now_if_required()

    if "tarball" not in obj.extra_data["options"]["identifiers"]:
        extract_path = make_single_directory(CFG_TMPSHAREDDIR, eng.uuid)
        tarball, pdf = harvest_single(obj.data["system_control_number"]["value"], extract_path, ["tarball"])
        tarball = str(tarball)
        time.sleep(CFG_PLOTEXTRACTOR_DOWNLOAD_TIMEOUT)
        if tarball is None:
            raise WorkflowError("Error harvesting tarball from id: %s %s" %
                                (identifiers, extract_path),
                                id_workflow=eng.uuid)
        obj.extra_data["options"]["identifiers"]["tarball"] = tarball

    sub_dir, dummy = get_defaults(obj.extra_data["options"]["identifiers"]["tarball"], CFG_TMPDIR, "")

    try:
        untar(obj.extra_data["options"]["identifiers"]["tarball"], sub_dir)
    except Timeout:
        eng.log.error('Timeout during tarball extraction on %s' % (obj.extra_data["options"]["identifiers"]["tarball"]))

    xml_files_list = find_matching_files(sub_dir, ["xml"])

    authors = ""

    for xml_file in xml_files_list:
        xml_file_fd = open(xml_file, "r")
        xml_content = xml_file_fd.read()
        xml_file_fd.close()

        match = REGEXP_AUTHLIST.findall(xml_content)
        if not match == []:
            authors += match[0]
            # Generate file to store conversion results
    if authors is not '':
        from invenio.legacy.bibconvert.xslt_engine import convert

        authors = convert(authors, "authorlist2marcxml.xsl")
        authorlist_record = create_records(authors)
        if len(authorlist_record) == 1:
            if authorlist_record[0][0] is None:
                eng.log.error("Error parsing authorlist record for id: %s" % (identifiers,))
            authorlist_record = authorlist_record[0][0]
            # Convert any LaTeX symbols in authornames
        translate_fieldvalues_from_latex(authorlist_record, '100', code='a')
        translate_fieldvalues_from_latex(authorlist_record, '700', code='a')
        # Look for any UNDEFINED fields in authorlist
        #key = "UNDEFINED"
        #matching_fields = record_find_matching_fields(key, authorlist_record, tag='100') +\
        #                  record_find_matching_fields(key, authorlist_record, tag='700')

        #if len(matching_fields) > 0:

        # UNDEFINED found. Create ticket in author queue
        #             ticketid = create_authorlist_ticket(matching_fields, \
        #                                                 identifiers, arguments.get('a_rt-queue'))
        #             if ticketid:
        #                 eng.log.info("authorlist RT ticket %d submitted for %s" % (ticketid, identifiers))
        #             else:
        #                 eng.log.error("Error while submitting RT ticket for %s" % (identifiers,))
        updated_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<collection>\n' + record_xml_output(authorlist_record) \
                      + '</collection>'
        if not None == updated_xml:
            from invenio.base.records.api import create_record
            # We store the path to the directory  the tarball contents live
            # Read and grab MARCXML from plotextractor run
            new_dict_representation = create_record(updated_xml).dumps()
            obj.data['authors'] = new_dict_representation["authors"]
            obj.data['number_of_authors'] = new_dict_representation["number_of_authors"]


author_list.__id__ = "u"


def upload_step(obj, eng):
    """
    Perform the upload step.
    """
    eng.log.info("upload step started")
    uploaded_task_ids = []
    #Work comment:
    #
    #Prepare in case of filtering the files to up,
    #no filtering, no other things to do

    new_dict_representation = Record(obj.data)
    marcxml_value = new_dict_representation.legacy_export_as_marc()

    task_id = None
    # Get a random sequence ID that will allow for the tasks to be
    # run in order, regardless if parallel task execution is activated
    sequence_id = random.randrange(1, 4294967296)
    task_sleep_now_if_required()
    extract_path = make_single_directory(CFG_TMPSHAREDDIR, eng.uuid)
    # Now we launch BibUpload tasks for the final MARCXML files
    filepath = extract_path + os.sep + str(obj.id)
    file_fd = open(filepath, 'w')
    file_fd.write(marcxml_value)
    file_fd.close()
    mode = ["-r", "-i"]

    arguments = obj.extra_data["repository"].arguments

    if os.path.exists(filepath):
        try:
            args = mode
            if sequence_id:
                args.extend(['-I', str(sequence_id)])
            if arguments.get('u_name', ""):
                args.extend(['-N', arguments.get('u_name', "")])
            if arguments.get('u_priority', 5):
                args.extend(['-P', str(arguments.get('u_priority', 5))])
            args.append(filepath)
            task_id = task_low_level_submission("bibupload", "oaiharvest", *tuple(args))
            create_oaiharvest_log(task_id, obj.extra_data["repository"].id, filepath)
        except Exception, msg:
            eng.log.error("An exception during submitting oaiharvest task occured : %s " % (str(msg)))
            return None
    else:
        eng.log.error("marcxmlfile %s does not exist" % (filepath,))
    if task_id is None:
        eng.log.error("an error occurred while uploading %s from %s" %
                      (filepath, obj.extra_data["repository"].name))
    else:
        uploaded_task_ids.append(task_id)
        eng.log.info("material harvested from source %s was successfully uploaded" %
                     (obj.extra_data["repository"].name,))

    if CFG_INSPIRE_SITE:
        # Launch BibIndex,Webcoll update task to show uploaded content quickly
        bibindex_params = ['-w', 'collection,reportnumber,global',
                           '-P', '6',
                           '-I', str(sequence_id),
                           '--post-process',
                           'bst_run_bibtask[taskname="webcoll", user="oaiharvest", P="6", c="HEP"]']
        task_low_level_submission("bibindex", "oaiharvest", *tuple(bibindex_params))
    eng.log.info("end of upload")


def create_oaiharvest_log(task_id, oai_src_id, marcxmlfile):
    """
    Function which creates the harvesting logs
    @param task_id bibupload task id
    """
    file_fd = open(marcxmlfile, "r")
    xml_content = file_fd.read(-1)
    file_fd.close()
    create_oaiharvest_log_str(task_id, oai_src_id, xml_content)
