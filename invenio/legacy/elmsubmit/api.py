# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011 CERN.
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

__revision__ = "$Id$"

# import sys
import os
import smtplib

import invenio.legacy.elmsubmit.EZEmail as elmsubmit_EZEmail
import invenio.legacy.elmsubmit.submission_parser as elmsubmit_submission_parser

# import the config file

from invenio.config import CFG_TMPDIR, CFG_SITE_NAME
import invenio.legacy.elmsubmit.config as elmsubmit_config

import invenio.legacy.elmsubmit.field_validation as elmsubmit_field_validation

from invenio.legacy.elmsubmit.misc import random_alphanum_string as _random_alphanum_string

import invenio.legacy.elmsubmit.generate_marc as elmsubmit_generate_marc

def process_email(email_string):
    """ main entry point of the module, handles whole processing of the email
    """

    # See if we can parse the email:

    try:
        e = elmsubmit_EZEmail.ParseMessage(email_string)
    except elmsubmit_EZEmail.EZEmailParseError as err:
        try:
            if err.basic_email_info['from'] is None:
                raise ValueError


            response = elmsubmit_EZEmail.CreateMessage(to=err.basic_email_info['from'],
                                                       _from=elmsubmit_config.CFG_ELMSUBMIT_PEOPLE['admin'],
                                                       message=elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['bad_email'],
                                                       subject="Re: " + (err.basic_email_info.get('Subject', '') or ''),
                                                       references=[err.basic_email_info.get('message-id', '') or ''],
                                                       wrap_message=False)
            _send_smtp(_from=elmsubmit_config.CFG_ELMSUBMIT_PEOPLE['admin'], to=err.basic_email_info['from'], msg=response)
            raise elmsubmitError("Email could not be parsed. Reported to sender.")
        except ValueError:
            raise elmsubmitError("From: field of submission email could not be parsed. Could not report to sender.")

    # See if we can parse the submission fields in the email:

    try:
        # Note that this returns a dictionary loaded with utf8 byte strings:
        submission_dict = elmsubmit_submission_parser.parse_submission(e.primary_message.encode('utf8'))
        # Add the submitter's email:
        submission_dict['SuE'] = e.from_email.encode('utf8')

    except elmsubmit_submission_parser.SubmissionParserError:
        _notify(msg=e, response=elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['bad_submission'])
        raise elmsubmitSubmissionError("Could not parse submission.")

    # Check we have been given the required fields:
    available_fields = submission_dict.keys()

    if not len(filter(lambda x: x in available_fields, elmsubmit_config.CFG_ELMSUBMIT_REQUIRED_FIELDS)) == len(elmsubmit_config.CFG_ELMSUBMIT_REQUIRED_FIELDS):
        response = elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['missing_fields_1'] + elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['missing_fields_2'] + "\n\n" + repr(elmsubmit_config.CFG_ELMSUBMIT_REQUIRED_FIELDS)
        _notify(msg=e, response=response)
        raise elmsubmitSubmissionError("Submission does not contain the required fields %s." % (elmsubmit_config.CFG_ELMSUBMIT_REQUIRED_FIELDS))

    # Check that the fields we have been given validate OK:

    map(lambda field: validate_submission_field(e, submission_dict, field, submission_dict[field]), elmsubmit_config.CFG_ELMSUBMIT_REQUIRED_FIELDS)

    # Get a submission directory:

    folder_name = 'elmsubmit_' +  _random_alphanum_string(15)

    storage_dir  = os.path.join(CFG_TMPDIR, folder_name)

    try:
        os.makedirs(storage_dir)
    except EnvironmentError:
        _notify(msg=e, response=elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['temp_problem'])
        _notify_admin(response="Could not create directory: %s" % (storage_dir))
        raise elmsubmitError("Could not create directory: %s" % (storage_dir))

    # Process the files list:

    process_files(e, submission_dict, storage_dir)

    #generate the appropriate Marc_XML for the submission

    marc_xml = elmsubmit_generate_marc.generate_marc(submission_dict)

    # Write the Marc to a file in CFG_TMPDIR

    file_name = folder_name + '.xml'
    fullpath = os.path.join(CFG_TMPDIR, file_name)

    try:
        open(fullpath, 'wb').write(marc_xml)
    except EnvironmentError:
        response_email = elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['temp_problem']
        admin_response_email = "There was a problem writing data to directory %s." % (storage_dir)
        error = elmsubmitError("There was a problem writing data to directory %s." % (storage_dir))
        return (response_email, admin_response_email, error)

    # print  marc_xml

    return marc_xml


def validate_submission_field(msg, submission_dict, field, value):

    try:
        (field_documentation, fixed_value, validation_success) = getattr(elmsubmit_field_validation, field)(value.decode('utf8'))
        submission_dict[field] = fixed_value.encode('utf8')

        if not validation_success:
            _notify(msg=msg, response=elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['bad_field'] + ' ' + field.upper() + '\n\n'
                    + elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['correct_format'] + '\n\n' + field_documentation)
            raise elmsubmitSubmissionError("Submission contains field %s which does not validate." % (field))
    except AttributeError:
        # No validation defined for this field:
        pass

def process_files(msg, submission_dict, storage_dir):
    """ extract the files out of the email and include them in the submission dict
    """
    files = map(lambda filename: filename.decode('utf8'), submission_dict['files'])

    # Check for the special filename 'all': if we find it, add all of
    # the files attached to the email to the list of files to submit:

    if 'all' in files:

        f = lambda attachment: attachment['filename'] is not None
        g = lambda attachment: attachment['filename'].lower()
        attached_filenames = map(g, filter(f, msg.attachments))

        files.extend(attached_filenames)
        files = filter(lambda name: name != 'all', files)

    # Filter out duplicate filenames:
    _temp = {}
    map(lambda filename: _temp.update({ filename : 1}), files)
    files = _temp.keys()

    # Get the files out of the mail message:

    # file dictionary with file content needed for saving the file to proper directory
    file_dict = {}

    # file list needed to be included in submission_dict
    file_list = []

    for filename in files:

        # See if we have special keyword self (which uses the mail message itself as the file):
        if filename == 'self':
            file_attachment = msg.original_message
            filename = _random_alphanum_string(8) + '_' + msg.date_sent_utc.replace(' ', '_').replace(':', '-') + '.msg'
        else:
            nominal_attachments = filter(lambda attachment: attachment['filename'].lower() == filename, msg.attachments)

            try:
                file_attachment = nominal_attachments[0]['file']
            except IndexError:
                _notify(msg=msg, response=elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['missing_attachment'] + ' ' + filename)
                raise elmsubmitSubmissionError("Submission is missing attached file: %s" % (filename))

        file_dict[filename.encode('utf8')] = file_attachment

        #merge the file name and the storage dir in the submission_dict

        full_file_name = os.path.join(storage_dir, filename.encode('utf8'))
        file_list.append(full_file_name)

    submission_dict['files'] = file_list

    def create_files((path, dictionary_or_data)):
        """
        Take any dictionary, eg.:

        { 'title' : 'The loveliest title.',
          'name'  : 'Pete the dog.',
          'info'  : 'pdf file content'
        }

        and create a set of files in the given directory:
        directory/title
        directory/name
        directory/info
        so that each filename is a dictionary key, and the contents of
        each file is the value that the key pointed to.
        """

        fullpath = os.path.join(storage_dir, path)

        try:
            dictionary_or_data.has_key
        except AttributeError:
            open(fullpath, 'wb').write(dictionary_or_data)

    try:
        map(create_files, file_dict.items())
    except EnvironmentError:
        response_email = elmsubmit_config.CFG_ELMSUBMIT_NOLANGMSGS['temp_problem']
        admin_response_email = "There was a problem writing data to directory %s." % (storage_dir)
        error = elmsubmitError("There was a problem writing data to directory %s." % (storage_dir))
        return (response_email, admin_response_email, error)

    return None



def _send_smtp(_from, to, msg):

    s = smtplib.SMTP()
    s.connect(host=elmsubmit_config.CFG_ELMSUBMIT_SERVERS['smtp'])
    s.sendmail(_from, to, msg)
    s.close()

def _notify(msg, response):
    response = elmsubmit_EZEmail.CreateMessage(to=[(msg.from_name, msg.from_email)],
                                               _from=elmsubmit_config.CFG_ELMSUBMIT_PEOPLE['admin'],
                                               message=response,
                                               subject="Re: " + msg.subject,
                                               references=[msg.message_id],
                                               wrap_message=False)

    _send_smtp(_from=elmsubmit_config.CFG_ELMSUBMIT_PEOPLE['admin'], to=msg.from_email, msg=response)

def _notify_admin(response):
    response = elmsubmit_EZEmail.CreateMessage(to=elmsubmit_config.CFG_ELMSUBMIT_PEOPLE['admin'],
                                               _from=elmsubmit_config.CFG_ELMSUBMIT_PEOPLE['admin'],
                                               message=response,
                                               subject="%s / elmsubmit problem." % CFG_SITE_NAME,
                                               wrap_message=False)
    _send_smtp(_from=elmsubmit_config.CFG_ELMSUBMIT_PEOPLE['admin'], to=elmsubmit_config.CFG_ELMSUBMIT_PEOPLE['admin'], msg=response)

class elmsubmitError(Exception):
    pass

class elmsubmitSubmissionError(elmsubmitError):
    pass

class _elmsubmitPrivateError(Exception):
    """
    An emtpy parent class for all the private errors in this module.
    """
    pass


