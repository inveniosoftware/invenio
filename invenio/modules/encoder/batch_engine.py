# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2011 CERN.
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

"""Bibencode batch processing submodule"""

from string import Template
from pprint import pprint
import os
import shutil
import uuid
from pprint import pformat

from invenio.legacy.bibsched.bibtask import (
                             task_update_progress,
                             write_message,
                             task_low_level_submission
                             )
from invenio.legacy.bibdocfile.api import BibRecDocs, compose_file, compose_format, decompose_file
from invenio.legacy.search_engine import (
                                   record_exists,
                                   get_collection_reclist,
                                   search_pattern,
                                   get_fieldvalues
                                   )
from invenio.modules.encoder.encode import encode_video, assure_quality
from invenio.modules.encoder.extract import extract_frames
from invenio.modules.encoder.profiles import (
                                        get_encoding_profile,
                                        get_extract_profile
                                        )
from invenio.legacy.bibdocfile.cli import cli_fix_marc
from invenio.modules.encoder.utils import chose2
from invenio.modules.encoder.metadata import (
                                        pbcore_metadata
                                        )
from invenio.modules.encoder.utils import getval, chose2, generate_timestamp
from invenio.modules.encoder.config import (
                                      CFG_BIBENCODE_DAEMON_DIR_NEWJOBS,
                                      CFG_BIBENCODE_PBCORE_MARC_XSLT,
                                      CFG_BIBENCODE_ASPECT_RATIO_MARC_FIELD
                                      )
from invenio.ext.email import send_email
from invenio.base.i18n import gettext_set_language
from invenio.legacy.webuser import emailUnique, get_user_preferences
from invenio.modules.formatter.engines.xslt import format
from invenio.utils.json import json, json_decode_file
import invenio.config

# Stored messages for email notifications
global _BATCH_STEP, _BATCH_STEPS
_BATCH_STEP = 1
_BATCH_STEPS = 1
global _MSG_HISTORY, _UPD_HISTORY
_MSG_HISTORY = []
_UPD_HISTORY = []

def _notify_error_admin(batch_job,
                        email_admin=invenio.config.CFG_SITE_ADMIN_EMAIL):
    """Sends a notification email to the specified address, containing
       admin-only information. Is called by process_batch_job() if an error
       occured during the processing.
    @param email_admin: email address of the admin
    @type email_admin: string
    """
    if not email_admin:
        return
    template = ("BibEncode batch processing has reported an error during the"
            "execution of a job within the batch description <br/><br/>"
            "This is the batch description: <br/><br/>"
            "%(batch_description)s <br/><br/>"
            "This is the message log: <br/><br/>"
            "%(message_log)s")
    html_text = template % {"batch_description": pformat(batch_job).replace("\n", "<br/>"),
             "message_log": "\n".join(_MSG_HISTORY)}
    text = html_text.replace("<br/>", "\n")
    send_email(fromaddr=invenio.config.CFG_SITE_ADMIN_EMAIL,
               toaddr=email_admin,
               subject="Error during BibEncode batch processing",
               content=text,
               html_content=html_text)

def _notify_error_user(email_user, original_filename, recid, submission_title, ln=invenio.config.CFG_SITE_LANG):
    """Sends an error notification to the specified address of the user.
       Is called by process_batch_job() if an error occured during the processing.
    @param email_user: email address of the user
    @type email_user: string
    @param email_admin: email address of the admin
    @type email_admin: string
    """
    if not email_user:
        return
    uid = emailUnique(email_user)
    if uid != -1 and uid != 0:
        language = getval(get_user_preferences(uid), "language")
        if language:
            ln = language
    _ = gettext_set_language(ln)
    rec_url = invenio.config.CFG_SITE_URL + "/record/" + str(recid)
    template = ("<br/>" +
            _("We are sorry, a problem has occured during the processing of"
            " your video upload%(submission_title)s.") +
            "<br/><br/>" +
            _("The file you uploaded was %(input_filename)s.") +
            "<br/><br/>" +
            _("Your video might not be fully available until intervention.") +
            "<br/>" +
            _("You can check the status of your video here: %(record_url)s.") +
            "<br/>" +
            _("You might want to take a look at "
            " %(guidelines_url)s"
            " and modify or redo your submission."))
    text = template % {"input_filename": "%s" % original_filename,
             "submission_title": " %s" % submission_title,
             "record_url": "%s" % rec_url,
             "guidelines_url": "localhost"}
    text = text.replace("<br/>", "\n")
    html_text = template % {"input_filename": "<strong>%s</strong>" % original_filename,
             "submission_title": " <strong>%s</strong>" % submission_title,
             "record_url": "<a href=\"%s\">%s</a>" % (rec_url, rec_url),
             "guidelines_url": "<a href=\"locahost\">%s</a>" % _("the video guidelines")}
    send_email(fromaddr=invenio.config.CFG_SITE_ADMIN_EMAIL,
               toaddr=email_user,
               subject="Problem during the processing of your video",
               content=text,
               html_content=html_text
               )

def _notify_success_user(email_user, original_filename, recid, submission_title, ln=invenio.config.CFG_SITE_LANG):
    """Sends an success notification to the specified address of the user.
       Is called by process_batch_job() if the processing was successful.
    @param email_user: email address of the user
    @type email_user: string
    @param email_admin: email address of the admin
    @type email_admin: string
    """
    uid = emailUnique(email_user)
    if uid != -1 and uid != 0:
        language = getval(get_user_preferences(uid), "language")
        if language:
            ln = language
    _ = gettext_set_language(ln)
    rec_url = invenio.config.CFG_SITE_URL + "/record/" + str(recid)
    template = ("<br/>" +
            _("Your video submission%(submission_title)s was successfully processed.") +
            "<br/><br/>" +
            _("The file you uploaded was %(input_filename)s.") +
            "<br/><br/>" +
            _("Your video is now available here: %(record_url)s.") +
            "<br/>" +
            _("If the videos quality is not as expected, you might want to take "
            "a look at %(guidelines_url)s"
            " and modify or redo your submission."))
    text = template % {"input_filename": "%s" % original_filename,
             "submission_title": " %s" % submission_title,
             "record_url": "%s" % rec_url,
             "guidelines_url": "localhost"}
    text = text.replace("<br/>", "\n")
    html_text = template % {"input_filename": "<strong>%s</strong>" % original_filename,
             "submission_title": " <strong>%s</strong>" % submission_title,
             "record_url": "<a href=\"%s\">%s</a>" % (rec_url, rec_url),
             "guidelines_url": "<a href=\"locahost\">%s</a>" % _("the video guidelines")}
    send_email(fromaddr=invenio.config.CFG_SITE_ADMIN_EMAIL,
               toaddr=email_user,
               subject="Your video submission is now complete",
               content=text,
               html_content=html_text
               )

def _task_update_overall_status(message):
    """ Generates an overall update message for the BibEncode task.
        Stores the messages in a global list for notifications
        @param message: the message that should be printed as task status
        @type message: string
    """
    message = "[%d/%d]%s" % (_BATCH_STEP, _BATCH_STEPS, message)
    task_update_progress(message)
    global _UPD_HISTORY
    _UPD_HISTORY.append(message)

def _task_write_message(message):
    """ Stores the messages in a global list for notifications
        @param message: the message that should be printed as task status
        @type message: string
    """
    write_message(message)
    global _MSG_HISTORY
    _MSG_HISTORY.append(message)

def clean_job_for_quality(batch_job_dict, fallback=True):
    """
    Removes jobs from the batch description that are not suitable for the master
    video's quality. It applies only for encoding jobs!
    @param batch_job_dict: the dict containing the batch description
    @type batch_job_dict: dict
    @param
    @return: the cleaned dict
    @rtype: dict
    """
    survived_jobs = []
    fallback_jobs = []
    other_jobs = []
    for job in batch_job_dict['jobs']:
        if job['mode'] == 'encode':
            if getval(job, 'fallback') and fallback:
                fallback_jobs.append(job)
            if getval(job, 'enforce'):
                survived_jobs.append(job)
            else:
                profile = None
                if getval(job, 'profile'):
                    profile = get_encoding_profile(job['profile'])
                if assure_quality(input_file=batch_job_dict['input'],
                        aspect=chose2('aspect', job, profile),
                        target_width=chose2('width', job, profile),
                        target_height=chose2('height', job, profile),
                        target_bitrate=chose2('videobitrate', job, profile)):
                    survived_jobs.append(job)
        else:
            other_jobs.append(job)
    if survived_jobs:
        survived_jobs.extend(other_jobs)
        new_jobs = survived_jobs
    else:
        fallback_jobs.extend(other_jobs)
        new_jobs = fallback_jobs
    pprint(locals())
    batch_job_dict['jobs'] = new_jobs
    return batch_job_dict

def create_update_jobs_by_collection(
                            batch_template_file,
                            collection,
                            job_directory=CFG_BIBENCODE_DAEMON_DIR_NEWJOBS):
    """ Creates the job description files to update a whole collection
    @param batch_template_file: fullpath to the template for the update
    @type batch_tempalte_file: string
    @param collection: name of the collection that should be updated
    @type collection: string
    @param job_directory: fullpath to the directory storing the job files
    @type job_directory: string
    """
    recids = get_collection_reclist(collection)
    return create_update_jobs_by_recids(recids, batch_template_file,
                                        job_directory)

def create_update_jobs_by_search(pattern,
                                 batch_template_file,
                                 job_directory=CFG_BIBENCODE_DAEMON_DIR_NEWJOBS
                                 ):
    """ Creates the job description files to update all records that fit a
        search pattern. Be aware of the search limitations!
    @param search_pattern: The pattern to search for
    @type search_pattern: string
    @param batch_template_file: fullpath to the template for the update
    @type batch_tempalte_file: string
    @param job_directory: fullpath to the directory storing the job files
    @type job_directory: string
    """
    recids = search_pattern(p=pattern)
    return create_update_jobs_by_recids(recids, batch_template_file,
                                        job_directory)

def create_update_jobs_by_recids(recids,
                                 batch_template_file,
                                 job_directory=CFG_BIBENCODE_DAEMON_DIR_NEWJOBS
                                 ):
    """ Creates the job description files to update all given recids
    @param recids: Iterable set of recids
    @type recids: iterable
    @param batch_template_file: fullpath to the template for the update
    @type batch_tempalte_file: string
    @param job_directory: fullpath to the directory storing the job files
    @type job_directory: string
    """
    batch_template = json_decode_file(batch_template_file)
    for recid in recids:
        task_update_progress("Creating Update Job for %d" % recid)
        write_message("Creating Update Job for %d" % recid)
        job = dict(batch_template)
        job['recid'] = recid
        timestamp = generate_timestamp()
        job_filename = "update_%d_%s.job" % (recid, timestamp)
        create_job_from_dictionary(job, job_filename, job_directory)
    return 1

def create_job_from_dictionary(
                    job_dict,
                    job_filename=None,
                    job_directory=CFG_BIBENCODE_DAEMON_DIR_NEWJOBS
                    ):
    """ Creates a job from a given dictionary
    @param job_dict: Dictionary that contains the job description
    @type job_dict: job_dict
    @param job_filename: Filename for the job
    @type job_filename: string
    @param job_directory: fullpath to the directory storing the job files
    @type job_directory: string
    """
    if not job_filename:
        job_filename = str(uuid.uuid4())
    if not job_filename.endswith(".job"):
        job_filename += ".job"
    job_fullpath = os.path.join(job_directory, job_filename)
    job_string = json.dumps(job_dict, sort_keys=False, indent=4)
    file = open(job_fullpath, "w")
    file.write(job_string)
    file.close()

def sanitise_batch_job(batch_job):
    """ Checks the correctness of the batch job dictionary and additionally
    sanitises some values.
    @param batch_job: The batch description dictionary
    @type batch_job: dictionary
    """
    def san_bitrate(bitrate):
        """ Sanitizes bitrates
        """
        if type(str()) == type(bitrate):
            if bitrate.endswith('k'):
                try:
                    bitrate = int(bitrate[:-1])
                    bitrate *= 1000
                    return bitrate
                except ValueError:
                    raise Exception("Could not parse bitrate")
        elif type(int) == type(bitrate):
            return bitrate
        else:
            raise Exception("Could not parse bitrate")

    if not getval(batch_job, 'update_from_master'):
        if not getval(batch_job, 'input'):
            raise Exception("No input file in batch description")

    if not getval(batch_job, 'recid'):
        raise Exception("No recid in batch description")

    if not getval(batch_job, 'jobs'):
        raise Exception("No job list in batch description")

    if getval(batch_job, 'update_from_master'):
        if (not getval(batch_job, 'bibdoc_master_comment') and
            not getval(batch_job, 'bibdoc_master_description') and
            not getval(batch_job, 'bibdoc_master_subformat')):
            raise Exception("If update_from_master ist set, a comment or"
                    " description or subformat for matching must be given")

    if getval(batch_job, 'marc_snippet'):
        if not os.path.exists(getval(batch_job, 'marc_snippet')):
            raise Exception("The marc snipped file %s was not found" %
                            getval(batch_job, 'marc_snippet'))

    for job in batch_job['jobs']:
        if job['mode'] == 'encode':
            if getval(job, 'videobitrate'):
                job['videobitrate'] = san_bitrate(getval(job, 'videobitrate'))
            if getval(job, 'audiobitrate'):
                job['audiobitrate'] = san_bitrate(getval(job, 'audiobitrate'))

    return batch_job

def process_batch_job(batch_job_file):
    """ Processes a batch job description dictionary

    @param batch_job_file: a fullpath to a batch job file
    @type batch_job_file: string
    @return: 1 if the process was successful, 0 if not
    @rtype; int
    """

    def upload_marcxml_file(marcxml):
        """ Creates a temporary marcxml file and sends it to bibupload
        """
        xml_filename = 'bibencode_'+ str(batch_job['recid']) + '_' + str(uuid.uuid4()) + '.xml'
        xml_filename = os.path.join(invenio.config.CFG_TMPSHAREDDIR, xml_filename)
        xml_file = file(xml_filename, 'w')
        xml_file.write(marcxml)
        xml_file.close()
        targs = ['-c', xml_filename]
        task_low_level_submission('bibupload', 'bibencode', *targs)

    #---------#
    # GENERAL #
    #---------#

    _task_write_message("----------- Handling Master -----------")

    ## Check the validity of the batch file here
    batch_job = json_decode_file(batch_job_file)

    ## Sanitise batch description and raise errrors
    batch_job = sanitise_batch_job(batch_job)

    ## Check if the record exists
    if record_exists(batch_job['recid']) < 1:
        raise Exception("Record not found")

    recdoc = BibRecDocs(batch_job['recid'])

    #--------------------#
    # UPDATE FROM MASTER #
    #--------------------#

    ## We want to add new stuff to the video's record, using the master as input
    if getval(batch_job, 'update_from_master'):
        found_master = False
        bibdocs = recdoc.list_bibdocs()
        for bibdoc in bibdocs:
            bibdocfiles = bibdoc.list_all_files()
            for bibdocfile in bibdocfiles:
                comment = bibdocfile.get_comment()
                description = bibdocfile.get_description()
                subformat = bibdocfile.get_subformat()
                m_comment = getval(batch_job, 'bibdoc_master_comment', comment)
                m_description = getval(batch_job, 'bibdoc_master_description', description)
                m_subformat = getval(batch_job, 'bibdoc_master_subformat', subformat)
                if (comment == m_comment and
                    description == m_description and
                    subformat == m_subformat):
                    found_master = True
                    batch_job['input'] = bibdocfile.get_full_path()
                    ## Get the aspect of the from the record
                    try:
                        ## Assumes pbcore metadata mapping
                        batch_job['aspect'] = get_fieldvalues(124, CFG_BIBENCODE_ASPECT_RATIO_MARC_FIELD)[0]
                    except IndexError:
                        pass
                    break
            if found_master:
                break
        if not found_master:
            _task_write_message("Video master for record %d not found"
                          % batch_job['recid'])
            task_update_progress("Video master for record %d not found"
                                 % batch_job['recid'])
            ## Maybe send an email?
            return 1

    ## Clean the job to do no upscaling etc
    if getval(batch_job, 'assure_quality'):
        batch_job = clean_job_for_quality(batch_job)

    global _BATCH_STEPS
    _BATCH_STEPS = len(batch_job['jobs'])

    ## Generate the docname from the input filename's name or given name
    bibdoc_video_docname, bibdoc_video_extension = decompose_file(batch_job['input'])[1:]
    if not bibdoc_video_extension or getval(batch_job, 'bibdoc_master_extension'):
        bibdoc_video_extension = getval(batch_job, 'bibdoc_master_extension')
    if getval(batch_job, 'bibdoc_master_docname'):
        bibdoc_video_docname = getval(batch_job, 'bibdoc_master_docname')

    write_message("Creating BibDoc for %s" % bibdoc_video_docname)
    ## If the bibdoc exists, receive it
    if bibdoc_video_docname in recdoc.get_bibdoc_names():
        bibdoc_video = recdoc.get_bibdoc(bibdoc_video_docname)
    ## Create a new bibdoc if it does not exist
    else:
        bibdoc_video = recdoc.add_bibdoc(docname=bibdoc_video_docname)

    ## Get the directory auf the newly created bibdoc to copy stuff there
    bibdoc_video_directory = bibdoc_video.get_base_dir()

    #--------#
    # MASTER #
    #--------#
    if not getval(batch_job, 'update_from_master'):
        if getval(batch_job, 'add_master'):
            ## Generate the right name for the master
            ## The master should be hidden first an then renamed
            ## when it is really available
            ## !!! FIX !!!
            _task_write_message("Adding %s master to the BibDoc"
                          % bibdoc_video_docname)
            master_format = compose_format(
                                    bibdoc_video_extension,
                                    getval(batch_job, 'bibdoc_master_subformat', 'master')
                                    )
            ## If a file of the same format is there, something is wrong, remove it!
            ## it might be caused by a previous corrupted submission etc.
            if bibdoc_video.format_already_exists_p(master_format):
                bibdoc_video.delete_file(master_format, 1)
            bibdoc_video.add_file_new_format(
                    batch_job['input'],
                    version=1,
                    description=getval(batch_job, 'bibdoc_master_description'),
                    comment=getval(batch_job, 'bibdoc_master_comment'),
                    docformat=master_format
                    )

    #-----------#
    # JOBS LOOP #
    #-----------#

    return_code = 1
    global _BATCH_STEP

    for job in batch_job['jobs']:

        _task_write_message("----------- Job %s of %s -----------"
                           % (_BATCH_STEP, _BATCH_STEPS))

        ## Try to substitute docname with master docname
        if getval(job, 'bibdoc_docname'):
            job['bibdoc_docname'] = Template(job['bibdoc_docname']).safe_substitute({'bibdoc_master_docname': bibdoc_video_docname})

        #-------------#
        # TRANSCODING #
        #-------------#

        if job['mode'] == 'encode':

            ## Skip the job if assure_quality is not set and marked as fallback
            if not getval(batch_job, 'assure_quality') and getval(job, 'fallback'):
                continue

            if getval(job, 'profile'):
                profile = get_encoding_profile(job['profile'])
            else:
                profile = None
            ## We need an extension defined fot the video container
            bibdoc_video_extension = getval(job, 'extension',
                                            getval(profile, 'extension'))
            if not bibdoc_video_extension:
                raise Exception("No container/extension defined")
            ## Get the docname and subformat
            bibdoc_video_subformat = getval(job, 'bibdoc_subformat')
            bibdoc_slave_video_docname = getval(job, 'bibdoc_docname', bibdoc_video_docname)
            ## The subformat is incompatible with ffmpegs name convention
            ## We do the encoding without and rename it afterwards
            bibdoc_video_fullpath = compose_file(
                                                 bibdoc_video_directory,
                                                 bibdoc_slave_video_docname,
                                                 bibdoc_video_extension
                                                 )
            _task_write_message("Transcoding %s to %s;%s" % (bibdoc_slave_video_docname,
                                bibdoc_video_extension,
                                bibdoc_video_subformat))
            ## We encode now directly into the bibdocs directory
            encoding_result = encode_video(
                 input_file=batch_job['input'],
                 output_file=bibdoc_video_fullpath,
                 acodec=getval(job, 'audiocodec'),
                 vcodec=getval(job, 'videocodec'),
                 abitrate=getval(job, 'videobitrate'),
                 vbitrate=getval(job, 'audiobitrate'),
                 resolution=getval(job, 'resolution'),
                 passes=getval(job, 'passes', 1),
                 special=getval(job, 'special'),
                 specialfirst=getval(job, 'specialfirst'),
                 specialsecond=getval(job, 'specialsecond'),
                 metadata=getval(job, 'metadata'),
                 width=getval(job, 'width'),
                 height=getval(job, 'height'),
                 aspect=getval(batch_job, 'aspect'), # Aspect for every job
                 profile=getval(job, 'profile'),
                 update_fnc=_task_update_overall_status,
                 message_fnc=_task_write_message
                 )
            return_code &= encoding_result
            ## only on success
            if  encoding_result:
                ## Rename it, adding the subformat
                os.rename(bibdoc_video_fullpath,
                          compose_file(bibdoc_video_directory,
                                       bibdoc_video_extension,
                                       bibdoc_video_subformat,
                                       1,
                                       bibdoc_slave_video_docname)
                          )
                #bibdoc_video._build_file_list()
                bibdoc_video.touch()
                bibdoc_video._sync_to_db()
                bibdoc_video_format = compose_format(bibdoc_video_extension,
                                                     bibdoc_video_subformat)
                if getval(job, 'bibdoc_comment'):
                    bibdoc_video.set_comment(getval(job, 'bibdoc_comment'),
                                              bibdoc_video_format)
                if getval(job, 'bibdoc_description'):
                    bibdoc_video.set_description(getval(job, 'bibdoc_description'),
                                                 bibdoc_video_format)

        #------------#
        # EXTRACTION #
        #------------#

        # if there are multiple extraction jobs, all the produced files
        # with the same name will be in the same bibdoc! Make sure that
        # you use different subformats or docname templates to avoid
        # conflicts.

        if job['mode'] == 'extract':
            if getval(job, 'profile'):
                profile = get_extract_profile(job['profile'])
            else:
                profile = {}
            bibdoc_frame_subformat = getval(job, 'bibdoc_subformat')
            _task_write_message("Extracting frames to temporary directory")
            tmpdir = invenio.config.CFG_TMPDIR + "/" + str(uuid.uuid4())
            os.mkdir(tmpdir)
            #Move this to the batch description
            bibdoc_frame_docname = getval(job, 'bibdoc_docname', bibdoc_video_docname)
            tmpfname = (tmpdir + "/" + bibdoc_frame_docname + '.'
                        + getval(profile, 'extension',
                        getval(job, 'extension', 'jpg')))
            extraction_result = extract_frames(input_file=batch_job['input'],
                           output_file=tmpfname,
                           size=getval(job, 'size'),
                           positions=getval(job, 'positions'),
                           numberof=getval(job, 'numberof'),
                           width=getval(job, 'width'),
                           height=getval(job, 'height'),
                           aspect=getval(batch_job, 'aspect'),
                           profile=getval(job, 'profile'),
                           update_fnc=_task_update_overall_status,
                           )
            return_code &= extraction_result

            ## only on success:
            if extraction_result:
                ## for every filename in the directorys, create a bibdoc that contains
                ## all sizes of the frame from the two directories
                files = os.listdir(tmpdir)
                for filename in files:
                    ## The docname was altered by BibEncode extract through substitution
                    ## Retrieve it from the filename again
                    bibdoc_frame_docname, bibdoc_frame_extension = os.path.splitext(filename)
                    _task_write_message("Creating new bibdoc for %s" % bibdoc_frame_docname)
                    ## If the bibdoc exists, receive it
                    if bibdoc_frame_docname in recdoc.get_bibdoc_names():
                        bibdoc_frame = recdoc.get_bibdoc(bibdoc_frame_docname)
                    ## Create a new bibdoc if it does not exist
                    else:
                        bibdoc_frame = recdoc.add_bibdoc(docname=bibdoc_frame_docname)

                    ## The filename including path from tmpdir
                    fname = os.path.join(tmpdir, filename)

                    bibdoc_frame_format = compose_format(bibdoc_frame_extension, bibdoc_frame_subformat)
                    ## Same as with the master, if the format allready exists,
                    ## override it, because something went wrong before
                    if bibdoc_frame.format_already_exists_p(bibdoc_frame_format):
                        bibdoc_frame.delete_file(bibdoc_frame_format, 1)
                    _task_write_message("Adding %s jpg;%s to BibDoc"
                                  % (bibdoc_frame_docname,
                                     getval(job, 'bibdoc_subformat')))
                    bibdoc_frame.add_file_new_format(
                                    fname,
                                    version=1,
                                    description=getval(job, 'bibdoc_description'),
                                    comment=getval(job, 'bibdoc_comment'),
                                    docformat=bibdoc_frame_format)
            ## Remove the temporary folders
            _task_write_message("Removing temporary directory")
            shutil.rmtree(tmpdir)

        _BATCH_STEP = _BATCH_STEP + 1

    #-----------------#
    # FIX BIBDOC/MARC #
    #-----------------#

    _task_write_message("----------- Handling MARCXML -----------")

    ## Fix the BibDoc for all the videos previously created
    _task_write_message("Updating BibDoc of %s" % bibdoc_video_docname)
    bibdoc_video._build_file_list()

    ## Fix the MARC
    _task_write_message("Fixing MARC")
    cli_fix_marc({}, [batch_job['recid']], False)

    if getval(batch_job, 'collection'):
        ## Make the record visible by moving in from the collection
        marcxml = ("<record><controlfield tag=\"001\">%d</controlfield>"
                   "<datafield tag=\"980\" ind1=\" \" ind2=\" \">"
                   "<subfield code=\"a\">%s</subfield></datafield></record>"
                   ) % (batch_job['recid'], batch_job['collection'])
        upload_marcxml_file(marcxml)

    #---------------------#
    # ADD MASTER METADATA #
    #---------------------#

    if getval(batch_job, 'add_master_metadata'):
        _task_write_message("Adding master metadata")
        pbcore = pbcore_metadata(input_file = getval(batch_job, 'input'),
                                 pbcoreIdentifier = batch_job['recid'],
                                 aspect_override = getval(batch_job, 'aspect'))
        marcxml = format(pbcore, CFG_BIBENCODE_PBCORE_MARC_XSLT)
        upload_marcxml_file(marcxml)

    #------------------#
    # ADD MARC SNIPPET #
    #------------------#

    if getval(batch_job, 'marc_snippet'):
        marc_snippet = open(getval(batch_job, 'marc_snippet'))
        marcxml = marc_snippet.read()
        marc_snippet.close()
        upload_marcxml_file(marcxml)

    #--------------#
    # DELETE INPUT #
    #--------------#

    if getval(batch_job, 'delete_input'):
        _task_write_message("Deleting input file")
        # only if successfull
        if not return_code:
            # only if input matches pattern
            if getval(batch_job, 'delete_input_pattern', '') in getval(batch_job, 'input'):
                try:
                    os.remove(getval(batch_job, 'input'))
                except OSError:
                    pass

    #--------------#
    # NOTIFICATION #
    #--------------#

    ## Send Notification emails on errors
    if not return_code:
        if getval(batch_job, 'notify_user'):
            _notify_error_user(getval(batch_job, 'notify_user'),
                               getval(batch_job, 'submission_filename', batch_job['input']),
                               getval(batch_job, 'recid'),
                               getval(batch_job, 'submission_title', ""))
            _task_write_message("Notify user because of an error")
        if getval(batch_job, 'notify_admin'):
            _task_write_message("Notify admin because of an error")
            if type(getval(batch_job, 'notify_admin') == type(str()) ):
                _notify_error_admin(batch_job,
                                    getval(batch_job, 'notify_admin'))

            else:
                _notify_error_admin(batch_job)
    else:
        if getval(batch_job, 'notify_user'):
            _task_write_message("Notify user because of success")
            _notify_success_user(getval(batch_job, 'notify_user'),
                               getval(batch_job, 'submission_filename', batch_job['input']),
                               getval(batch_job, 'recid'),
                               getval(batch_job, 'submission_title', ""))
    return 1

