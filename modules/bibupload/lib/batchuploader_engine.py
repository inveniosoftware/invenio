# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011, 2012, 2013 CERN.
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

"""
Batch Uploader core functions. Uploading metadata and documents.
"""

import os
import pwd
import grp
import sys
import time
import tempfile
import cgi
import re

from invenio.dbquery import run_sql, Error
from invenio.access_control_engine import acc_authorize_action
from invenio.webuser import collect_user_info, page_not_authorized
from invenio.config import CFG_BINDIR, CFG_TMPSHAREDDIR, CFG_LOGDIR, \
                            CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG, \
                            CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG, \
                            CFG_OAI_ID_FIELD, CFG_BATCHUPLOADER_DAEMON_DIR, \
                            CFG_BATCHUPLOADER_WEB_ROBOT_RIGHTS, \
                            CFG_BATCHUPLOADER_WEB_ROBOT_AGENTS, \
                            CFG_PREFIX, CFG_SITE_LANG
from invenio.textutils import encode_for_xml
from invenio.bibtask import task_low_level_submission
from invenio.messages import gettext_set_language
from invenio.textmarc2xmlmarc import transform_file
from invenio.shellutils import run_shell_command
from invenio.bibupload import xml_marc_to_records, bibupload
from invenio.access_control_firerole import _ip_matcher_builder, _ipmatch
from invenio.webinterface_handler_config import HTTP_BAD_REQUEST, HTTP_FORBIDDEN
import invenio.bibupload as bibupload_module

from invenio.bibrecord import create_records, \
                              record_strip_empty_volatile_subfields, \
                              record_strip_empty_fields

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

PERMITTED_MODES = ['-i', '-r', '-c', '-a', '-ir',
                   '--insert', '--replace', '--correct', '--append']

_CFG_BATCHUPLOADER_WEB_ROBOT_AGENTS_RE = re.compile(CFG_BATCHUPLOADER_WEB_ROBOT_AGENTS)

_CFG_BATCHUPLOADER_WEB_ROBOT_RIGHTS = []
for _network, _collection in CFG_BATCHUPLOADER_WEB_ROBOT_RIGHTS.items():
    if '/' not in _network:
        _network += '/32'
    _CFG_BATCHUPLOADER_WEB_ROBOT_RIGHTS.append((_ip_matcher_builder(_network), _collection))
    del _network
    del _collection



def cli_allocate_record(req):
    req.content_type = "text/plain"
    req.send_http_header()

    # check IP and useragent:
    if not _get_client_authorized_collections(_get_client_ip(req)):
        msg = "[ERROR] Sorry, client IP %s cannot use the service." % _get_client_ip(req)
        _log(msg)
        return _write(req, msg)
    if not _check_client_useragent(req):
        msg = '[ERROR] Sorry, the "%s" useragent cannot use the service.' % _get_useragent(req)
        _log(msg)
        return _write(req, msg)

    recid = run_sql("insert into bibrec (creation_date,modification_date) values(NOW(),NOW())")
    return recid

def cli_upload(req, file_content=None, mode=None, callback_url=None, nonce=None, special_treatment=None):
    """ Robot interface for uploading MARC files
    """
    req.content_type = "text/plain"

    # check IP and useragent:
    if not _get_client_authorized_collections(_get_client_ip(req)):
        msg = "[ERROR] Sorry, client IP %s cannot use the service." % _get_client_ip(req)
        _log(msg)
        req.status = HTTP_FORBIDDEN
        return _write(req, msg)
    if not _check_client_useragent(req):
        msg = "[ERROR] Sorry, the %s useragent cannot use the service." % _get_useragent(req)
        _log(msg)
        req.status = HTTP_FORBIDDEN
        return _write(req, msg)

    arg_mode = mode
    if not arg_mode:
        msg = "[ERROR] Please specify upload mode to use."
        _log(msg)
        req.status = HTTP_BAD_REQUEST
        return _write(req, msg)
    if arg_mode == '--insertorreplace':
        arg_mode = '-ir'
    if not arg_mode in PERMITTED_MODES:
        msg = "[ERROR] Invalid upload mode."
        _log(msg)
        req.status = HTTP_BAD_REQUEST
        return _write(req, msg)

    arg_file = file_content
    if hasattr(arg_file, 'read'):
        ## We've been passed a readable file, e.g. req
        arg_file = arg_file.read()
        if not arg_file:
            msg = "[ERROR] Please provide a body to your request."
            _log(msg)
            req.status = HTTP_BAD_REQUEST
            return _write(req, msg)
    else:
        if not arg_file:
            msg = "[ERROR] Please specify file body to input."
            _log(msg)
            req.status = HTTP_BAD_REQUEST
            return _write(req, msg)
        if hasattr(arg_file, "filename"):
            arg_file = arg_file.value
        else:
            msg = "[ERROR] 'file' parameter must be a (single) file"
            _log(msg)
            req.status = HTTP_BAD_REQUEST
            return _write(req, msg)

    # write temporary file:
    (fd, filename) = tempfile.mkstemp(prefix="batchupload_" + \
               time.strftime("%Y%m%d%H%M%S", time.localtime()) + "_",
               dir=CFG_TMPSHAREDDIR)

    filedesc = os.fdopen(fd, 'w')
    filedesc.write(arg_file)
    filedesc.close()

    # check if this client can run this file:
    client_ip = _get_client_ip(req)
    permitted_dbcollids = _get_client_authorized_collections(client_ip)
    if '*' not in permitted_dbcollids: # wildcard
        allow = _check_client_can_submit_file(client_ip, filename, req, 0)
        if not allow:
            msg = "[ERROR] Cannot submit such a file from this IP. (Wrong collection.)"
            _log(msg)
            req.status = HTTP_FORBIDDEN
            return _write(req, msg)

    # check validity of marcxml
    xmlmarclint_path = CFG_BINDIR + '/xmlmarclint'
    xmlmarclint_output, dummy1, dummy2 = run_shell_command('%s %s' % (xmlmarclint_path, filename))
    if xmlmarclint_output != 0:
        msg = "[ERROR] MARCXML is not valid."
        _log(msg)
        req.status = HTTP_BAD_REQUEST
        return _write(req, msg)
    args = ['bibupload', "batchupload", arg_mode, filename]
    # run upload command
    if callback_url:
        args += ["--callback-url", callback_url]
        if nonce:
            args += ["--nonce", nonce]
        if special_treatment:
            args += ["--special-treatment", special_treatment]
    task_low_level_submission(*args)
    msg = "[INFO] %s" % ' '.join(args)
    _log(msg)
    return _write(req, msg)

def metadata_upload(req, metafile=None, filetype=None, mode=None, exec_date=None,
                    exec_time=None, metafilename=None, ln=CFG_SITE_LANG,
                    priority="1", email_logs_to=None):
    """
    Metadata web upload service. Get upload parameters and exec bibupload for the given file.
    Finally, write upload history.
    @return: tuple (error code, message)
        error code: code that indicates if an error ocurred
        message: message describing the error
    """
    # start output:
    req.content_type = "text/html"
    req.send_http_header()

    error_codes = {'not_authorized': 1}

    user_info = collect_user_info(req)
    (fd, filename) = tempfile.mkstemp(prefix="batchupload_" + \
        user_info['nickname'] + "_" + time.strftime("%Y%m%d%H%M%S",
        time.localtime()) + "_", dir=CFG_TMPSHAREDDIR)
    filedesc = os.fdopen(fd, 'w')
    filedesc.write(metafile)
    filedesc.close()

    # check if this client can run this file:
    if req is not None:
        allow = _check_client_can_submit_file(req=req, metafile=metafile, webupload=1, ln=ln)
        if allow[0] != 0:
            return (error_codes['not_authorized'], allow[1])

    # run upload command:
    task_arguments = ('bibupload', user_info['nickname'], mode,
                      "--priority=" + priority, "-N", "batchupload")
    if exec_date:
        date = exec_date
        if exec_time:
            date += ' ' + exec_time
        task_arguments += ("-t", date)
    if email_logs_to:
        task_arguments += ('--email-logs-to', email_logs_to)
    task_arguments += (filename, )
    jobid = task_low_level_submission(*task_arguments)

    # write batch upload history
    run_sql("""INSERT INTO hstBATCHUPLOAD (user, submitdate,
            filename, execdate, id_schTASK, batch_mode)
            VALUES (%s, NOW(), %s, %s, %s, "metadata")""",
            (user_info['nickname'], metafilename,
            exec_date != "" and (exec_date + ' ' + exec_time)
            or time.strftime("%Y-%m-%d %H:%M:%S"), str(jobid), ))
    return (0, "Task %s queued" % str(jobid))

def document_upload(req=None, folder="", matching="", mode="", exec_date="", exec_time="", ln=CFG_SITE_LANG, priority="1", email_logs_to=None):
    """ Take files from the given directory and upload them with the appropiate mode.
    @parameters:
        + folder: Folder where the files to upload are stored
        + matching: How to match file names with record fields (report number, barcode,...)
        + mode: Upload mode (append, revise, replace)
    @return: tuple (file, error code)
        file: file name causing the error to notify the user
        error code:
            1 - More than one possible recID, ambiguous behaviour
            2 - No records match that file name
            3 - File already exists
    """
    import sys
    if sys.hexversion < 0x2060000:
        from md5 import md5
    else:
        from hashlib import md5
    from invenio.bibdocfile import BibRecDocs, file_strip_ext
    import shutil
    from invenio.search_engine import perform_request_search, \
                                      search_pattern, \
                                      guess_collection_of_a_record
    _ = gettext_set_language(ln)
    errors = []
    info = [0, []] # Number of files read, name of the files
    try:
        files = os.listdir(folder)
    except OSError, error:
        errors.append(("", error))
        return errors, info
    err_desc = {1: _("More than one possible recID, ambiguous behaviour"), 2: _("No records match that file name"),
                3: _("File already exists"), 4: _("A file with the same name and format already exists"),
                5: _("No rights to upload to collection '%s'")}
    # Create directory DONE/ if doesn't exist
    folder = (folder[-1] == "/") and folder or (folder + "/")
    files_done_dir = folder + "DONE/"
    try:
        os.mkdir(files_done_dir)
    except OSError:
        # Directory exists or no write permission
        pass
    for docfile in files:
        if os.path.isfile(os.path.join(folder, docfile)):
            info[0] += 1
            identifier = file_strip_ext(docfile)
            extension = docfile[len(identifier):]
            rec_id = None
            if identifier:
                rec_id = search_pattern(p=identifier, f=matching, m='e')
            if not rec_id:
                errors.append((docfile, err_desc[2]))
                continue
            elif len(rec_id) > 1:
                errors.append((docfile, err_desc[1]))
                continue
            else:
                rec_id = str(list(rec_id)[0])
            rec_info = BibRecDocs(rec_id)
            if rec_info.bibdocs:
                for bibdoc in rec_info.bibdocs:
                    attached_files = bibdoc.list_all_files()
                    file_md5 = md5(open(os.path.join(folder, docfile), "rb").read()).hexdigest()
                    num_errors = len(errors)
                    for attached_file in attached_files:
                        if attached_file.checksum == file_md5:
                            errors.append((docfile, err_desc[3]))
                            break
                        elif attached_file.get_full_name() == docfile:
                            errors.append((docfile, err_desc[4]))
                            break
                if len(errors) > num_errors:
                    continue
            # Check if user has rights to upload file
            if req is not None:
                file_collection = guess_collection_of_a_record(int(rec_id))
                auth_code, auth_message = acc_authorize_action(req, 'runbatchuploader', collection=file_collection)
                if auth_code != 0:
                    error_msg = err_desc[5] % file_collection
                    errors.append((docfile, error_msg))
                    continue
            # Move document to be uploaded to temporary folder
            (fd, tmp_file) = tempfile.mkstemp(prefix=identifier + "_" + time.strftime("%Y%m%d%H%M%S", time.localtime()) + "_", suffix=extension, dir=CFG_TMPSHAREDDIR)
            shutil.copy(os.path.join(folder, docfile), tmp_file)
            # Create MARC temporary file with FFT tag and call bibupload
            (fd, filename) = tempfile.mkstemp(prefix=identifier + '_', dir=CFG_TMPSHAREDDIR)
            filedesc = os.fdopen(fd, 'w')
            marc_content = """ <record>
                                    <controlfield tag="001">%(rec_id)s</controlfield>
                                        <datafield tag="FFT" ind1=" " ind2=" ">
                                            <subfield code="n">%(name)s</subfield>
                                            <subfield code="a">%(path)s</subfield>
                                        </datafield>
                               </record> """ % {'rec_id': rec_id,
                                                'name': encode_for_xml(identifier),
                                                'path': encode_for_xml(tmp_file),
                                                }
            filedesc.write(marc_content)
            filedesc.close()
            info[1].append(docfile)
            user = ""
            if req is not None:
                user_info = collect_user_info(req)
                user = user_info['nickname']
            if not user:
                user = "batchupload"
            # Execute bibupload with the appropiate mode

            task_arguments = ('bibupload', user, "--" + mode,
                              "--priority=" + priority, "-N", "batchupload")

            if exec_date:
                date = '--runtime=' + "\'" + exec_date + ' ' + exec_time + "\'"
                task_arguments += (date, )
            if email_logs_to:
                task_arguments += ("--email-logs-to", email_logs_to)
            task_arguments += (filename, )

            jobid = task_low_level_submission(*task_arguments)

            # write batch upload history
            run_sql("""INSERT INTO hstBATCHUPLOAD (user, submitdate,
                    filename, execdate, id_schTASK, batch_mode)
                    VALUES (%s, NOW(), %s, %s, %s, "document")""",
                    (user_info['nickname'], docfile,
                    exec_date != "" and (exec_date + ' ' + exec_time)
                    or time.strftime("%Y-%m-%d %H:%M:%S"), str(jobid)))

            # Move file to DONE folder
            done_filename = docfile + "_" + time.strftime("%Y%m%d%H%M%S", time.localtime()) + "_" + str(jobid)
            try:
                os.rename(os.path.join(folder, docfile), os.path.join(files_done_dir, done_filename))
            except OSError:
                errors.append('MoveError')
    return errors, info

def get_user_metadata_uploads(req):
    """Retrieve all metadata upload history information for a given user"""
    user_info = collect_user_info(req)
    upload_list = run_sql("""SELECT DATE_FORMAT(h.submitdate, '%%Y-%%m-%%d %%H:%%i:%%S'), \
                            h.filename, DATE_FORMAT(h.execdate, '%%Y-%%m-%%d %%H:%%i:%%S'), \
                            s.status \
                            FROM hstBATCHUPLOAD h INNER JOIN schTASK s \
                            ON h.id_schTASK = s.id \
                            WHERE h.user=%s and h.batch_mode="metadata"
                            ORDER BY h.submitdate DESC""", (user_info['nickname'],))
    return upload_list

def get_user_document_uploads(req):
    """Retrieve all document upload history information for a given user"""
    user_info = collect_user_info(req)
    upload_list = run_sql("""SELECT DATE_FORMAT(h.submitdate, '%%Y-%%m-%%d %%H:%%i:%%S'), \
                          h.filename, DATE_FORMAT(h.execdate, '%%Y-%%m-%%d %%H:%%i:%%S'), \
                          s.status \
                          FROM hstBATCHUPLOAD h INNER JOIN schTASK s \
                          ON h.id_schTASK = s.id \
                          WHERE h.user=%s and h.batch_mode="document"
                          ORDER BY h.submitdate DESC""", (user_info['nickname'],))
    return upload_list

def get_daemon_doc_files():
    """ Return all files found in batchuploader document folders """
    files = {}
    for folder in ['/revise', '/append']:
        try:
            daemon_dir = CFG_BATCHUPLOADER_DAEMON_DIR[0] == '/' and CFG_BATCHUPLOADER_DAEMON_DIR \
                         or CFG_PREFIX + '/' + CFG_BATCHUPLOADER_DAEMON_DIR
            directory = daemon_dir + '/documents' + folder
            files[directory] = [(filename, []) for filename in os.listdir(directory) if os.path.isfile(os.path.join(directory, filename))]
            for file_instance, info in files[directory]:
                stat_info = os.lstat(os.path.join(directory, file_instance))
                info.append("%s" % pwd.getpwuid(stat_info.st_uid)[0]) # Owner
                info.append("%s" % grp.getgrgid(stat_info.st_gid)[0]) # Group
                info.append("%d" % stat_info.st_size) # Size
                time_stat = stat_info.st_mtime
                time_fmt = "%Y-%m-%d %R"
                info.append(time.strftime(time_fmt, time.gmtime(time_stat))) # Last modified
        except OSError:
            pass
    return files

def get_daemon_meta_files():
    """ Return all files found in batchuploader metadata folders """
    files = {}
    for folder in ['/correct', '/replace', '/insert', '/append']:
        try:
            daemon_dir = CFG_BATCHUPLOADER_DAEMON_DIR[0] == '/' and CFG_BATCHUPLOADER_DAEMON_DIR \
                         or CFG_PREFIX + '/' + CFG_BATCHUPLOADER_DAEMON_DIR
            directory = daemon_dir + '/metadata' + folder
            files[directory] = [(filename, []) for filename in os.listdir(directory) if os.path.isfile(os.path.join(directory, filename))]
            for file_instance, info in files[directory]:
                stat_info = os.lstat(os.path.join(directory, file_instance))
                info.append("%s" % pwd.getpwuid(stat_info.st_uid)[0]) # Owner
                info.append("%s" % grp.getgrgid(stat_info.st_gid)[0]) # Group
                info.append("%d" % stat_info.st_size) # Size
                time_stat = stat_info.st_mtime
                time_fmt = "%Y-%m-%d %R"
                info.append(time.strftime(time_fmt, time.gmtime(time_stat))) # Last modified
        except OSError:
            pass
    return files

def user_authorization(req, ln):
    """ Check user authorization to visit page """
    auth_code, auth_message = acc_authorize_action(req, 'runbatchuploader')
    if auth_code != 0:
        referer = '/batchuploader/'
        return page_not_authorized(req=req, referer=referer,
                                   text=auth_message, navmenuid="batchuploader")
    else:
        return None

def perform_basic_upload_checks(xml_record):
    """ Performs tests that would provoke the bibupload task to fail with
    an exit status 1, to prevent batchupload from crashing while alarming
    the user wabout the issue
    """
    from invenio.bibupload import writing_rights_p

    errors = []
    if not writing_rights_p():
        errors.append("Error: BibUpload does not have rights to write fulltext files.")
    recs = create_records(xml_record, 1, 1)
    if recs == []:
        errors.append("Error: Cannot parse MARCXML file.")
    elif recs[0][0] is None:
        errors.append("Error: MARCXML file has wrong format: %s" % recs)
    return errors

def perform_upload_check(xml_record, mode):
    """ Performs a upload simulation with the given record and mode
    @return: string describing errors
    @rtype: string
    """
    error_cache = []
    def my_writer(msg, stream=sys.stdout, verbose=1):
        if verbose == 1:
            if 'DONE' not in msg:
                error_cache.append(msg.strip())

    orig_writer = bibupload_module.write_message
    bibupload_module.write_message = my_writer

    error_cache.extend(perform_basic_upload_checks(xml_record))
    if error_cache:
        # There has been some critical error
        return '\n'.join(error_cache)

    recs = xml_marc_to_records(xml_record)
    try:
        upload_mode = mode[2:]
        # Adapt input data for bibupload function
        if upload_mode == "r insert-or-replace":
            upload_mode = "replace_or_insert"
        for record in recs:
            if record:
                record_strip_empty_volatile_subfields(record)
                record_strip_empty_fields(record)
                bibupload(record, opt_mode=upload_mode, pretend=True)
    finally:
        bibupload_module.write_message = orig_writer

    return '\n'.join(error_cache)

def _get_useragent(req):
    """Return client user agent from req object."""
    user_info = collect_user_info(req)
    return user_info['agent']

def _get_client_ip(req):
    """Return client IP address from req object."""
    return str(req.remote_ip)

def _get_client_authorized_collections(client_ip):
    """
    Is this client permitted to use the service?
    Return list of collections for which the client is authorized
    """
    ret = []
    for network, collection in _CFG_BATCHUPLOADER_WEB_ROBOT_RIGHTS:
        if _ipmatch(client_ip, network):
            if '*' in collection:
                return ['*']
            ret += collection
    return ret

def _check_client_useragent(req):
    """
    Is this user agent permitted to use the service?
    """
    client_useragent = _get_useragent(req)
    if _CFG_BATCHUPLOADER_WEB_ROBOT_AGENTS_RE.match(client_useragent):
        return True
    return False

def _check_client_can_submit_file(client_ip="", metafile="", req=None, webupload=0, ln=CFG_SITE_LANG):
    """
    Is this client able to upload such a FILENAME?
    check 980 $a values and collection tags in the file to see if they are among the
    permitted ones as specified by CFG_BATCHUPLOADER_WEB_ROBOT_RIGHTS and ACC_AUTHORIZE_ACTION.
    Useful to make sure that the client does not override other records by
    mistake.
    """
    _ = gettext_set_language(ln)
    recs = create_records(metafile, 0, 0)
    user_info = collect_user_info(req)

    permitted_dbcollids = _get_client_authorized_collections(client_ip)
    if '*' in permitted_dbcollids:
        if not webupload:
            return True
        else:
            return (0, " ")

    filename_tag980_values = _detect_980_values_from_marcxml_file(recs)
    for filename_tag980_value in filename_tag980_values:
        if not filename_tag980_value:
            if not webupload:
                return False
            else:
                return(1, "Invalid collection in tag 980")
        if not webupload:
            if not filename_tag980_value in permitted_dbcollids:
                return False
        else:
            auth_code, auth_message = acc_authorize_action(req, 'runbatchuploader', collection=filename_tag980_value)
            if auth_code != 0:
                error_msg = _("The user '%(x_user)s' is not authorized to modify collection '%(x_coll)s'") % \
                            {'x_user': user_info['nickname'], 'x_coll': filename_tag980_value}
                return (auth_code, error_msg)

    filename_rec_id_collections = _detect_collections_from_marcxml_file(recs)

    for filename_rec_id_collection in filename_rec_id_collections:
        if not webupload:
            if not filename_rec_id_collection in permitted_dbcollids:
                return False
        else:
            auth_code, auth_message = acc_authorize_action(req, 'runbatchuploader', collection=filename_rec_id_collection)
            if auth_code != 0:
                error_msg = _("The user '%(x_user)s' is not authorized to modify collection '%(x_coll)s'") % \
                            {'x_user': user_info['nickname'], 'x_coll': filename_rec_id_collection}
                return (auth_code, error_msg)
    if not webupload:
        return True
    else:
        return (0, " ")

def _detect_980_values_from_marcxml_file(recs):
    """
    Read MARCXML file and return list of 980 $a values found in that file.
    Useful for checking rights.
    """
    from invenio.bibrecord import record_get_field_values

    collection_tag = run_sql("SELECT value FROM tag, field_tag, field \
                              WHERE tag.id=field_tag.id_tag AND \
                              field_tag.id_field=field.id AND \
                              field.code='collection'")
    collection_tag = collection_tag[0][0]
    dbcollids = {}
    for rec, dummy1, dummy2 in recs:
        if rec:
            for tag980 in record_get_field_values(rec,
                                                  tag=collection_tag[:3],
                                                  ind1=collection_tag[3],
                                                  ind2=collection_tag[4],
                                                  code=collection_tag[5]):
                dbcollids[tag980] = 1
    return dbcollids.keys()


def _detect_collections_from_marcxml_file(recs):
    """
    Extract all possible recIDs from MARCXML file and guess collections
    for these recIDs.
    """
    from invenio.bibrecord import record_get_field_values
    from invenio.search_engine import guess_collection_of_a_record
    from invenio.bibupload import find_record_from_sysno, \
                                  find_records_from_extoaiid, \
                                  find_record_from_oaiid

    dbcollids = {}
    sysno_tag = CFG_BIBUPLOAD_EXTERNAL_SYSNO_TAG
    oaiid_tag = CFG_BIBUPLOAD_EXTERNAL_OAIID_TAG
    oai_tag = CFG_OAI_ID_FIELD
    for rec, dummy1, dummy2 in recs:
        if rec:
            for tag001 in record_get_field_values(rec, '001'):
                collection = guess_collection_of_a_record(int(tag001))
                dbcollids[collection] = 1
            for tag_sysno in record_get_field_values(rec, tag=sysno_tag[:3],
                                                     ind1=sysno_tag[3],
                                                     ind2=sysno_tag[4],
                                                     code=sysno_tag[5]):
                record = find_record_from_sysno(tag_sysno)
                if record:
                    collection = guess_collection_of_a_record(int(record))
                    dbcollids[collection] = 1
            for tag_oaiid in record_get_field_values(rec, tag=oaiid_tag[:3],
                                                     ind1=oaiid_tag[3],
                                                     ind2=oaiid_tag[4],
                                                     code=oaiid_tag[5]):
                try:
                    records = find_records_from_extoaiid(tag_oaiid)
                except Error:
                    records = []
                if records:
                    record = records.pop()
                    collection = guess_collection_of_a_record(int(record))
                    dbcollids[collection] = 1
            for tag_oai in record_get_field_values(rec, tag=oai_tag[0:3],
                                                   ind1=oai_tag[3],
                                                   ind2=oai_tag[4],
                                                   code=oai_tag[5]):
                record = find_record_from_oaiid(tag_oai)
                if record:
                    collection = guess_collection_of_a_record(int(record))
                    dbcollids[collection] = 1
    return dbcollids.keys()

def _transform_input_to_marcxml(file_input=""):
    """
    Takes text-marc as input and transforms it
    to MARCXML.
    """
    # Create temporary file to read from
    tmp_fd, filename = tempfile.mkstemp(dir=CFG_TMPSHAREDDIR)
    os.write(tmp_fd, file_input)
    os.close(tmp_fd)
    try:
        # Redirect output, transform, restore old references
        old_stdout = sys.stdout
        new_stdout = StringIO()
        sys.stdout = new_stdout

        transform_file(filename)
    finally:
        sys.stdout = old_stdout

    return new_stdout.getvalue()

def _log(msg, logfile="webupload.log"):
    """
    Log MSG into LOGFILE with timestamp.
    """
    filedesc = open(CFG_LOGDIR + "/" + logfile, "a")
    filedesc.write(time.strftime("%Y-%m-%d %H:%M:%S") + " --> " + msg + "\n")
    filedesc.close()
    return

def _write(req, msg):
    """
    Write MSG to the output stream for the end user.
    """
    req.write(msg + "\n")
    return
