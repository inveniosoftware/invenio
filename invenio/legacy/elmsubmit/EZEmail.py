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

from __future__ import print_function

"""
# Side note: CJK codecs at http://cjkpython.i18n.org/.

Exports blah blah blah.

Speed:

Testing it on a random sample of 1500 messages culled from my INBOX,
it took an average of 5/100ths seconds to process each
message. (Running on a Linux P4 2Ghz machine).

Shortcomings:

- Does not support message/partial mime type.

  The message/partial mime type is designed to allow mailers to split
  up the body of large messages into several 'message/partial' parts,
  which can then be sent inside seperate email messages to the
  intended receipient (see RFC2046 for the precise semantics). Upon
  receipt the MUA is supposed to recombine the parts into the orignal
  message. Supporting this fairly rare MIME type would add a lot of
  complexity to the module; there would have to be a mechanism for
  passing several email messages to the Message class constructor; further,

- Simply deletes RFC2231 language specification extensions from
  RFC2047 encoded header text. The rest of RFC2231 relating to header
  parameter values is observed. Note that a language specfication is
  different from a charset. This is an issue in very few
  circumstances. Hopefully it won't be an issue at all eventually,
  because soon charsets should allow language specifications to be
  built into them, and whatever happens in the future to unicode (and
  accordingly python's unicode object and function) will adapt to
  this. Quoting from RFC2231:

  > 8.  Character sets which allow specification of language
  >
  > In the future it is likely that some character sets will provide
  > facilities for inline language labeling. Such facilities are
  > inherently more flexible than those defined here as they allow for
  > language switching in the middle of a string.
  >
  > If and when such facilities are developed they SHOULD be used in
  > preference to the language labeling facilities specified here. Note
  > that all the mechanisms defined here allow for the omission of
  > language labels so as to be able to accommodate this possible future
  > usage.

"""

__revision__ = "$Id$"

# Quicker to do "from email import *" but this gives us a reminder of
# what's available:

import email

import email.Message
import email.Parser
import email.Generator
import email.Header
import email.Charset
import email.Encoders

import email.MIMENonMultipart
import email.MIMEMultipart
import email.MIMEMessage
import email.MIMEText
import email.Utils

import email.Errors

import mimetypes

# Non email imports:

import binascii
import time
import datetime
import os

from StringIO import StringIO
import quopri
import uu
import base64

import re

cfg_elmsubmit_have_rtflib = 0
try:
    import rtf.Rtf2Txt
    from rtf.RtfParser import RtfException as _RtfException
    cfg_elmsubmit_have_rtflib = 1
except ImportError:
    pass

import invenio.legacy.elmsubmit.richtext2txt as _richtext2txt
import invenio.legacy.elmsubmit.enriched2txt as _enriched2txt
import invenio.legacy.elmsubmit.html2txt as _html2txt

from invenio.legacy.elmsubmit.misc import concat as _concat
from invenio.legacy.elmsubmit.misc import cr2lf as _cr2lf
from invenio.legacy.elmsubmit.misc import random_alphanum_string as _random_alphanum_string
from invenio.legacy.elmsubmit.misc import wrap_text as _wrap_text

from invenio.legacy.elmsubmit.filename_generator import generate_filename as _generate_filename

import invenio.legacy.elmsubmit.EZArchive as elmsubmit_EZArchive

# Message Parsing:

# (Search down to "# Message Creation:" also.)

_default_handling_hints = { 'generate_filename' : 'always',
                            'descend_message_rfc822_attachments' : True,
                            'archive_format' : 'tar.gz',
                            'archive_multipart_unrecognized': True,
                            'archive_multipart_parallel': True,
                            'archive_multipart_related': True,
                            'generate_filename' : 'if_missing' }

class ParseMessage(object):

    """
    This class provides a very simple representation of an email
    message. It is basically a wrapper around the class ParseMessage
    provided by the Email package that comes with Python.

    It is designed to give simple access to the body text, attachments
    etc. without the programmer having to consider the evil
    complexities of MIME. It READ ONLY. ie. Don't expect to produce a
    new email by mutating the data returned by the class methods!

    Instance properties:

    self.headers

        Returns the headers of the message as a Python dictionary
        object.

        The data structure _headers might look as follows:

         _headers = { 'to' : [u"alice@example.com, bob@example.org"],
                      'recieved' : [u"from cernfe02.cern.ch ([137.138 etc...",
                                    u"from client.cern.ch ([137.138. etc..."],
                      'date' : [u"Wed, 4 Aug 2004 15:07:17 +0200 (W. Europe Daylight Time)"] }

        ie. It is a python dictionary: the keys are headers and the
        values are lists of header values (note that an email
        (RFC822) message may contain duplicate headers). Each list
        contains the header values in the relative order they appear
        in the original message. rfc822 headers are case-insensitive
        so we store them in lowercase.

        Header processing decodes each header from its RFC2047 encoded
        format then further decodes it from the native charsets into
        unicode. Hence the list values in the data structure are
        unicode strings. Note that the _keys_ are just regular ascii
        strings, since we should be able to rely on header keys being
        7-bit ascii only.

    self.received_data
    self.primary_message

        Returns the best guess at what the intended message is.

    self.original_message

        Returns the orignal message as supplied to the constructor.

    self.attachments
    self.inline_attachments
    self.from_header
    self.subject
    self.from_name
    self.from_email
    self.message_id
    self.date_sent_utc

        Returns an ISO8601 formatted unicode string of the date the
        email was sent (in UST/GMT).  ISO8601 strings look like this:
        "YYYY-MM-DD HH:MM:SS". If the Date: header is not present or
        unparsable, the current time on the system (in GMT) is
        substituted instead.
    """

    def __init__(self, message_string, strict=True, hints=_default_handling_hints):

        # message_string is a string representing an email (aka rfc822
        # message). strict determines +++++++++++++

        # Save the original message string (can be accessed later by
        # self.origMessage method)

        self.original_message = message_string

        # Create an email.Message object from the plain text.

        msg = email.message_from_string(message_string)

        # Now populate self.headers; intended to be accessed later by
        # self.headers method. The data structure is described in the
        # .headers method docstring.

        self.headers = _process_headers(msg, msg.items(), force_processing=(not strict))

        # Now we move on to calculating _from_name, _from_email

        # Of course, there might not be a From: header in a very
        # broken email, so we raise a FromHeaderError if this is the
        # case.

        try:
            # KeyError means email is missing 'from' field:
            from_header = self.headers['from'][0] # If mutliple From: fields, use 1st.

            self.from_addr = from_header

            # from_header could be None if we are operating with
            # strict=False and we failed to decode the header:
            if from_header is None: raise FromHeaderParsingError(msg)

            (from_name, from_email) = _parse_from_header(msg, from_header)
        except KeyError:
            if strict:
                raise FromHeaderMissingError(msg)
            else:
                from_name = None
                from_email = None
        except FromHeaderParsingError:
            if strict:
                raise # Reraise the error.
            else:
                from_name = None
                from_email = None

        self.from_name = from_name
        self.from_email = from_email

        try:
            self.subject = self.headers['subject'][0]
        except KeyError:
            self.subject = '' # Should we put None here?

        try:
            self.message_id = self.headers['message-id'][0]
        except KeyError:
            self.message_id = '' # Should we put None here?

        # Process the received headers, extracting the 'received from' host and ip address:

        try:
            self.received_data = map(_received_ip_and_host, self.headers['received'])
        except KeyError:
            # There were no recieved headers; should this be an error
            # in strict mode or not?
            # I think not, since people can save email locally without sending it.
            self.received_data = None

        # Now calculate _date_sent_utc. Test to see if there actually
        # is a date header and if we can parse it. If running in
        # strict mode, then we throw an error. If not, then simply use
        # the localtime.

        try:
            date_in_rfc2822_format = self.headers['date'][0]
            remote_struct_time_with_utc_offset = email.Utils.parsedate_tz(date_in_rfc2822_format)

            # email.Utils.parsedate_tz returns None on failure.
            if remote_struct_time_with_utc_offset is None: raise _ParseDateError()

            remote_struct_time = remote_struct_time_with_utc_offset[0:9]
            (remote_offset_from_utc_in_seconds,) = remote_struct_time_with_utc_offset[9:10]

            if remote_offset_from_utc_in_seconds is None: raise _ParseDateError()
        except (KeyError, _ParseDateError):

            if strict: raise ParseDateError(msg)

            else:
                # Use local time on error.
                remote_struct_time = time.gmtime()
                remote_offset_from_utc_in_seconds = 0

        date_time_args = remote_struct_time[0:6] # datetime constructor only needs first 6 parts of struct_time tuple

#         filter(lambda x: x is None: date_time_args)
#         if filter != []: raise ParseDateError(msg)

        remote_time = datetime.datetime(*date_time_args)
        remote_utc_delta = datetime.timedelta(seconds=remote_offset_from_utc_in_seconds)

#       local_utc_delta = datetime.timedelta(seconds= -time.timezone)

        utc_time = remote_time - remote_utc_delta
#       local_time = utc_time + local_utc_delta

        # Now that we have the date sent in utc, we just format it to
        # an ISO8601 string and convert that to a unicode
        # object. Since the ISO8601 string will only contain us-ascii,
        # this conversion should not fail and so we need not check for
        # decoding errors.

        self.date_sent_utc = unicode(utc_time.isoformat(sep=' '), 'us-ascii')

#       self._date_sent_local = local_time.isoformat(sep=' ')

        # Now we parse the email and attempt to calculate what the
        # primary message (ie. what would pop-up in the message pane
        # of your email client) would be.

        (self.attachments,
         self.inline_attachments,
         self.primary_message) = _get_msg_structure(msg, strict, hints)


def contents(filename):

    f = file(filename, "r")

    p = email.Parser.Parser()
    msg = p.parse(f)

    def walk_email(msg,indent=0):

        print("-"*indent, msg.get_content_type())

        if msg.is_multipart():
            for part in msg.get_payload():
                walk_email(part,indent+8)

    walk_email(msg)

    f.close()

####### __main__

# f = open('blower.eml','r')
# e = f.read()

# f = open('testSpliter/torture-test.eml','r')
# tort = f.read()


# f = open('just_text.eml','r')
# e2 = f.read()

# f = open('hello.eml','r')
# e3 = f.read()

# f = open('rtf2.eml')
# e4 = f.read()

# f = open('attached_msg.eml')
# e5 = f.read()

# f = open('/tmp/eg/example.jpg','r')
# jpg = f.read()

# f = open('/tmp/eg/example.msword.doc','r')
# word = f.read()

# f = open('/tmp/eg/example.xls','r')
# excel = f.read()

# f = open('/tmp/eg/example.pdf','r')
# pdf = f.read()

# f = open('/tmp/eg/example.reg.gz','r')
# reg = f.read()

# f = open('/tmp/eg/example.wk3','r')
# lotus = f.read()

# f = open('/tmp/eg/example.xml','r')
# xml = f.read()

# f = open('/tmp/eg/example.tar.gz','r')
# targz = f.read()

# f = open('/tmp/eg/example.tar','r')
# tar = f.read()

# f = open('/tmp/eg/example.zip','r')
# zip_data = f.read()

# f = open('/tmp/eg/example.xml.bz2','r')
# bz2eg = f.read()


# Support functions.

def _received_ip_and_host(received_header):

    host_re = re.compile(r"""from\ (        # from marks the start of the received target
                             [a-z0-9]+(?:[a-z0-9_.-]+[a-z0-9])? # Match a domain string.
                             )              # Allow illegal but common underscores
                                            # (eg. the famous dear_raed.blogspot.com)
                             [)\s]          # Terminate with space or a closing bracket depending on the format.
                          """,re.VERBOSE|re.IGNORECASE)

    ipad_re = re.compile(r"""[[(]          # match opening bracket or parenthesis
                                             # (should be a bracket if following standards)
                           ((?:\d{1,3}\.){3} # match three octets with dots
                           \d{1,3})      # match a single octet with no dot
                           [])]                # match the closing bracket/parenthesis
                           """, re.VERBOSE|re.IGNORECASE)

    host_match = host_re.search(received_header)
    if host_match is not None:
        host = host_match.group(1)
    else:
        host = None

    ipad_match = ipad_re.search(received_header)
    if ipad_match is not None:
        ipad = ipad_match.group(1)
    else:
        ipad = None

    return (host, ipad)

def _basic_email_info(msg):

    """
    Takes an email.Message object and returns a dictionary, formatted
    like the following example, containing a basic subset of
    information about the message:

    { from: u'Ann Other <person@example.org>'
      from_email  : u'person@example.org',
      from_name  :  u'Ann Other',
      subject : u'This email is about...',
      message-id : u'1234567890@host.example.com', }

    Any header which cannot be decoded to unicode will be returned in
    it original encoded form. Check with type(value) = unicode.

    This function can be used when throwing an error to gather just
    enough information about the message so clients of the
    elmsubmit_EZEmail.ParseMessage class can respond to the email author
    reporting the error.
    """

    # Items we want to try and return:
    # If you wish to tailor this list, note that basic_headers MUST
    # have 'from' in it, otherwise the following code breaks!

    basic_headers = ['from', 'subject', 'message-id'] # 'from_name' and 'from_email' aren't headers;
                                                      # they are derivatives of the 'from' header.

    # The hash to be built up and returned:

    return_dict = {}

    # Get all header/value pairs for which the header is also in list
    # basic_headers (case insensitively):

    basic_items = filter(lambda (k,v): k.lower() in basic_headers,
                         msg.items())

    # Now attempt to decode the basic headers to unicode objects:

    basic_decoded_headers = _process_headers(msg=None, header_value_pairs=basic_items, force_processing=True)

    # Since we're just using this for error output, we don't need to
    # worry about headers with the same header key; just accept the
    # first one present (and note that the list of headers in
    # basic_headers are all ones which _should_ only be appearing
    # once).

    basic_decoded_headers = dict(map(lambda (k,v): (k,v[0]),
                                     basic_decoded_headers.items()))

    try:

        # If the from header is missing this access will cause
        # KeyError:

        from_value = basic_decoded_headers['from']

        # If from_header is None, we couldn't decode it and so can't
        # proceed in splitting it into from_name and from_email. Raise
        # TypeError.

        if from_value is None: raise TypeError

        # Could cause FromHeaderParsingError:
        (from_name, from_email) = _parse_from_header(msg, from_value)

        return_dict.update({ 'from_name': from_name,
                             'from_email': from_email })

    except (TypeError, KeyError, FromHeaderParsingError):
        return_dict.update({ 'from_name': None,
                             'from_email': None })

    # This loops over basic_headers and tries to index
    # basic_decoded_headers by each value. Anything that isn't present
    # (ie. we've failed to decode), we look up directly in the orginal
    # msg object (and return the value as a string in whatever charset
    # and RFC2047 encoding it arrived in) if _that_ fails (ie. the
    # header is missing from the message altogether) we set the value
    # in the hash to None.

    for header in basic_headers:
        value = basic_decoded_headers.get(header, None)

        if value is None:
            value = msg.get(header, None)

        return_dict[header] = value

    return return_dict

def _native2unicode(value_nc, native_charset=None, strict=True):

    """
    Function native2unicode is a wrapper around builtin function
    unicode. The difference is that native2unicode will accept a
    charset of None which will cause it to default to decoding from
    us-ascii.

    It also raises a custom error _UnicodeDecodingError which returns
    the problem value and charset, rather than LookupError/ValueError
    raised by the unicode builtin.
    """
    errors = { True : 'strict',
               False: 'replace'}[strict]

    # Non-RFC2047 encoded parts return charset as None; we assume then
    # that they are us-ascii bytes.

    if native_charset is None: native_charset = 'us-ascii'

    # Remove RFC2123 language specification from document if present.
    # This is delimited from the charset by the '*' character.  eg. We
    # might have
    # native_charset = 'us-ascii*en'
    # and we need to remove '*en'.

    # This is the key reason we have function _native2unicode, and
    # aren't just calling .decode(charset)!

    native_charset = re.sub(r'\*.*$', '', native_charset)

    # Search this document for RFC2123 for more information.

    # unicode function might not recognize the native_charset and
    # hence throw a LookupError. Or it might fail to do the conversion
    # and throw a UnicodeError

    try:
        return unicode(value_nc, native_charset, errors)
    except (LookupError, UnicodeError):
        raise _UnicodeDecodingError(value_nc, native_charset)

def _process_headers(msg, header_value_pairs, force_processing=False):

    return reduce(lambda headers, (header,value): \
                     _process_header(msg, headers, header, value, force_processing),
                  header_value_pairs, {})

def _decode_rfc2231_tuple(msg, value):

    try:
        try:
            (charset, lang_specification, encoded_value) = value

            # If charset is unspecified, then we can assume us-ascii:
            if charset == '': charset = 'us-ascii'
            return _native2unicode(encoded_value, charset, strict=True)
        except ValueError:

            # Data was not RFC2231 encoded. ie. value should be just an
            # ascii-string.

            # Note however that some broken email clients mistakenly use
            # RFC2047 encoding in parameterized header fields such as
            # Content-Type and Content-Disposition. This is disallowed by
            # RFC2047:

            # >  + An 'encoded-word' MUST NOT be used in parameter of a
            # >  MIME Content-Type or Content-Disposition field, or in any
            # >  structured field body except within a 'comment' or
            # >  'phrase'.

            # In order to support these clients, if we get a string back
            # which wasn't RFC2231 encoded, we check instead to see if it
            # can be RFC2047 decoded.

            # Note that header='rfc2231_param' is just a dummy value;
            # we're not really decoding an rfc2047 encoded header;
            # just trying to support clients that mistakenly use
            # rfc2047 encoding for parameters _within_ structured
            # headers.

            return _decode_rfc2047_header(msg, header='rfc2231_param', value=value)
    except (_UnicodeDecodingError, HeaderCharsetError, HeaderRFC2047Error):
        return None

def _decode_and_join_structured_header_pair(msg, key, value):

    # Take input that looks like this:
    #
    # key = 'title'
    # value = ('us-ascii', 'en', "This is even more ***fun*** isn't it!")
    #
    # And return it looking like this:
    #
    # u'title="This is even more ***fun*** isn't it!"'

    # The key should always be just a us-ascii string:

    try:
        decoded_key = _native2unicode(key, 'us-ascii')
    except _UnicodeDecodingError:
        raise _StructuredHeaderPairError(key, value)

    if value == '':
        # We have a structured entry that is not in key=value form. eg. The multipart/mixed in
        # 'Content-Type: multipart/mixed; boundary="------------050902070901080909090201"'

        return decoded_key

    else:
        decoded_value = _decode_rfc2231_tuple(msg, value)
        if decoded_value is None: raise _StructuredHeaderPairError(key, value)

    # Now escape string for addition of quotes either side:
    # Escape backslashes:
    decoded_value = re.sub(r'\\', r'\\\\', decoded_value)
    # Escape quotes:
    decoded_value = re.sub(r'"', r'\\"', decoded_value)

    return decoded_key + '="' + decoded_value + '"'

def _decode_rfc2231_header(msg, header, value, force_processing=False):

    # We get the key/value pairs from the structured header by calling
    # the email.ParseMessage class's get_params method. This method deals
    # with all of the RFC2231 decoding for us, and so we just have to
    # reconstruct the tuples it gives us into a unicode string.

    # This means these headers are no longer suitable for parsing by
    # machine, but does make them suitable for display (which is
    # prefered from two mutually incompatable options; if you want to
    # start parsing Content-Type parameters, then you want to be using
    # the Python email package directly!).

#     Take a value that looks like:
#     value =
#     And turn it into a unicode string that looks like:
#     u'"This is even more ***fun*** isn't it!"'

#     The values in the tuple are from left to right are a charset,
#     language specification and string of encoded text.

#     We ignore the language specification. See list of module
#     shortcomings.
#     """

    params = msg.get_params(None, header)

    # param should never return failobj None since we have already
    # verified the header we are requesting exists.
    if params is None: raise _EmailPackageError

    try:

        f = lambda (k,v): _decode_and_join_structured_header_pair(msg, k, v)
        joined_pairs = map(f, params)
        unicode_value = '; '.join(joined_pairs)

    except _StructuredHeaderPairError as e:
        if force_processing:
            unicode_value = None
        else:
            raise HeaderRFC2231Error(msg, header, value, e.key, e.value)

    return unicode_value

def _decode_rfc2047_header(msg, header, value, force_processing=False):
    """
    Take an rfc2047 encoded string and convert it to unicode.
    """

    # For each header value two decoding steps happen:
    # 1. We decode the header from its RFC2047 encoded format.
    # 2. We decode the resulting information from its native
    #    charset to a unicode object.

    # decode_header takes the RFC2047 encoded form and returns a list
    # of tuples (string_in_native_charset, charset_name). It is a
    # *list* not a single tuple, since it is permissible to use
    # multiple charsets in a single header value!

    # Although undocumented in the python library documentation,
    # looking at the email.Header source suggests decode_header might
    # raise an 'email.Errors.HeaderParseError'. We catch this and
    # raise our own 'HeaderRFC2047Error'.

    try:
        decoded_parts = email.Header.decode_header(value)

        # The _native2unicode function might not recognise one of the
        # charsets and so throw a private _UnicodeDecodingError. If we
        # get one, then we catch it and raise public error
        # "HeaderCharsetError".

        unicode_decoded_parts = map(lambda (value, charset): \
                                          _native2unicode(value, charset, not force_processing),
                                    decoded_parts)

        # Since all members of decoded_parts are now in unicode we can
        # concatenate them into a single header value string.

        unicode_value = u''.join(unicode_decoded_parts)

    except email.Errors.HeaderParseError:
        if force_processing:
            unicode_value = None
        else:
            raise HeaderRFC2047Error(msg, header, value)
    except _UnicodeDecodingError as e:
        if force_processing:
            unicode_value = None
        else:
            raise HeaderCharsetError(msg, header, value, e.value, e.charset)

    return unicode_value

def _process_header(msg, headers, header, value, force_processing=False):

    # Function _process_header takes a partial headers dictionary
    # and a header/value pair and updates the dictionary with this
    # pair.

    # Headers are decoded from their RFC2231 encoding and turned into
    # unicode strings.

    # For Content-Type and Content-Disposition headers only, an
    # alternative decoding step happens; we attempt to decode these
    # structured headers from their RFC2231 encoding and rebuild them
    # as unicode strings.

    if header.lower() in ('content-type', 'content-disposition'):
        unicode_value = _decode_rfc2231_header(msg, header, value, force_processing)
    else:
        unicode_value = _decode_rfc2047_header(msg, header, value, force_processing)

    # Repeated header keys are legal, so we store dictionary
    # values as a list. Therefore we must check if this header
    # key has already been initialized in the dictionary.

    header = header.lower()
    headers.setdefault(header, []) # If key header isn't present, add it with value []
    headers[header].append(unicode_value)

    return headers

def _parse_from_header(msg, from_header):

    ### !!! Need to do some thinking about internationalized email
    ### !!! addresses and domain names to check what problems
    ### !!! these may cause.

    (from_name, from_email) = email.Utils.parseaddr(from_header)

    # Check we were able to parse the From: field
    # (email.Utils.parseaddr returns ('','') on failure) and that
    # from_email is not empty. Otherwise raise a FromHeaderParsingError

    # empty from_name is OK, since we just use from_email as the
    # author's 'name'.

    if (from_name, from_email) == ('','') or from_email == '':
        raise FromHeaderParsingError(msg)
    elif from_name == '':
        from_name = from_email

    return (from_name, from_email)

def _get_msg_structure(msg, strict, hints):

    mime_helper = _MimeHelper(msg)
#    mime_helper.maintype = 'multipart'
#    mime_helper.subtype = 'parallel'
    mime_handler = _get_mime_handler(mime_helper.maintype, mime_helper.subtype)

    nominal_attachments = mime_handler(msg, mime_helper, strict, hints)
    attachments = []
    inline_attachments = []
    primary_msg = ''

    for item in nominal_attachments:

        if item['disposition'] != 'attachment':
            if item['maintype'] == 'text' and item['downgrading_to_text'] is None:
                primary_msg += _force_ends_in_newline(item['file'])
                inline_attachments.append(item)
            elif item['downgrading_to_text'] is not None:
                primary_msg += _force_ends_in_newline(item['downgrading_to_text'])
                inline_attachments.append(item)
            else:
                attachments.append(item)
        else:
            attachments.append(item)

    return (attachments, inline_attachments, primary_msg)

def _force_ends_in_newline(string):

    if string == '' or string[-1] != '\n':
        return string + '\n'
    else:
        return string

def _get_mime_handler(maintype, subtype):

    try:
        handler = _mime_handler_map[maintype][subtype]
    except KeyError:
        try:
            handler = _mime_handler_map_unrecognized_subtype[maintype]
        except KeyError:
            handler = _mime_handler_unrecognized_maintype

    # Create a 'wrapper' function which does preparatory checks we
    # want to happen for all mime type before executing the real mime
    # handler (possibly we could have used a class based approach to
    # allow for more levels of wrapping, but I think this may have
    # been a sledgehammer on nut):

    def parent_handler(msg, mhe, strict, hints):

        if mhe.decoded_payload is None: # and not mhe.msg_part.is_multipart():
            if strict:
                raise MIMEPartError(msg, mhe, 'cte_decoding')
            else:
                return []

        if mhe.filename == ['FilenameDecodingError']:
            if strict:
                raise MIMEPartError(msg, mhe, 'filename_decoding')
            else:
                mhe.filename = None

        if maintype == 'text':

            # Make sure text data has unix newline conventions.
            mhe.decoded_payload = _cr2lf(mhe.decoded_payload)

            try:
                mhe.file = _native2unicode(mhe.decoded_payload, mhe.charset, strict)
            except _UnicodeDecodingError:
                if strict:
                    raise MIMEPartError(msg, mhe, 'unicode_conversion')
                else:
                    return []
        return handler(msg, mhe, strict, hints)

    return parent_handler

# Generate filename values: never, always, if_missing

def _format_msg_part_data(mhe, hints):

    part_info = {}
    part_info['file'] = mhe.file #'UNCOMMENT THIS TO SEE FILE!!!!!' #mhe.file
    part_info['downgrading_to_text'] = mhe.downgrading_to_text
    part_info['maintype'] = mhe.maintype
    part_info['subtype'] = mhe.subtype
    part_info['filename'] = mhe.filename
    part_info['disposition'] = mhe.disposition
    if mhe.maintype == 'text':
        part_info['original_charset'] = mhe.charset
    part_info['signature'] = mhe.signature
    part_info['encrypted'] = mhe.encrypted
    part_info['mac_resource_fork'] = mhe.mac_resource_fork
    part_info['rejected_alternatives'] = mhe.rejected_alternatives

    # Now see if we need to generate a filename:
    gf = hints['generate_filename']

    if gf == 'always' or (gf == 'if_missing' and (mhe.filename is None or mhe.filename == '')):
        generated_filename = _generate_filename(file=mhe.decoded_payload, content_type=(mhe.maintype + '/' + mhe.subtype))
    else:
        generated_filename = None

    part_info['generated_filename'] = generated_filename
    return part_info

def _get_part_disposition(msg_part):
    """
    Look to see whether this part is designated as inline, attachment
    or something else.
    """

    # BNF of Content-Disposition header quoted from RFC2183:

    #     disposition := "Content-Disposition" ":"
    #                    disposition-type
    #                    *(";" disposition-parm)
    #
    #     disposition-type := "inline"
    #                       / "attachment"
    #                       / extension-token
    #                       ; values are not case-sensitive

    # The BNF states only "inline" or "attachment" are valid tokens
    # for disposition-type, so there is now need to worry about
    # RFC2231 encoded data. (And any extension tokens should be
    # similarly restricted to simple ascii).

    # This dictates that the disposition-type must be the first element in
    # the header. get_params returns something like this:

    # >>> msg_part.get_params(None, 'Content-Disposition')
    # [('inline', ''), ('filename', 'email.txt')]

    # So we have to index by [0][0] to get the disposition-type keyword.

    try:
        return msg_part.get_params(None, 'Content-Disposition')[0][0]
    except (TypeError, IndexError):
        return None

def _get_part_filename(msg_part):

    """
    Attempt to discover a filename associated with a message body
    part.

    Note that the filename, if it exists, is returned as a unicode
    string. Filenames may not be as simple as you expect; what you get
    may be a string of Arabic characters.
    """

    # Note, we could just use the email.ParseMessage method get_filename to
    # try and discover a filename. However, this only checks the
    # Content-Disposition header for the filename parameter whereas we
    # would like to support crufty old clients which are still using
    # the Content-Type name parameter.

    missing = []

    #First try content-disposition:
    filename = msg_part.get_param('filename', missing, 'content-disposition')
    if filename != missing:

        filename = _decode_rfc2231_tuple(msg_part, filename)
        if filename is None:
            return ['FilenameDecodingError']
        else:
            return filename
    else:

        # If filename parameter of content-disposition is not
        # available, try name parameter of content-type:
        filename = msg_part.get_param('name', missing, 'content-type')

        if filename != missing:
            filename = _decode_rfc2231_tuple(msg_part, filename)
            if filename is None:
                return ['FilenameDecodingError']
        else:
            # No filename available:
            return None

def _cte_decode(msg_part):

    """
    Return a message part's payload, decoded from its content
    transfer encoding.
    """

    # Note that it is possible to use
    # msg_part.get_payload(decode=True) to do the CTE
    # decoding. Unfortunately, the error reporting of this method is
    # not very helpful; if CTE decoding fails, it just returns the
    # undecoded payload. This makes it hard to tell if there has been
    # success or not. Initially I thought decoding failure could be
    # identified by checking if:

    # msg_part.get_payload(decode=True) == msg_part.get_payload(decode=False)

    # But this method would flag false errors. For example, if text
    # contains no 'nasty characters' it will be the same both before
    # and after quoted-printable encoding (see the quoted-printable
    # RFC for a definition of 'nasty characters!); ie. for such text
    # quoted-printable encoding is an identity map.

    # The following function is essentially a cut-and-paste of the
    # Email.Message.Message class's get_payload method, edited to
    # raise _CTEDecodingError upon decoding failure.

    # In the case we are passed a multipart message part, we cannot
    # decode it and so throw _MultipartCTEDecodingAttempt:
    if msg_part.is_multipart(): raise _MultipartCTEDecodingAttempt

    payload = msg_part.get_payload(decode=False)
    cte = msg_part.get('content-transfer-encoding', '').lower()

    try:

        if cte == 'quoted-printable':
            # Could cause binascii.Error/Incomplete
            payload = quopri.decodestring(payload)
        elif cte == 'base64':
            # Could cause
            payload = _base64decode(payload)
        elif cte in ('x-uuencode', 'uuencode', 'uue', 'x-uue'):
            sfp = StringIO()

            uu.decode(StringIO(payload+'\n'), sfp)
            payload = sfp.getvalue()

    except (binascii.Error, binascii.Incomplete, uu.Error):
        raise _CTEDecodingError

    return payload

def _base64decode(s):
    """
    Decode bas64 encoded string.
    """

    # This is a cut and paste of email.Utils._bdecode.  We can't call
    # _bdecode directly, because its a private function of the Utils
    # modules and therefore not safe to import.

    # We can't quite use base64.encodestring() since it tacks on a "courtesy
    # newline".  Blech!
    if not s:
        return s
    value = base64.decodestring(s)
    if not s.endswith('\n') and value.endswith('\n'):
        return value[:-1]
    return value

# MIME Handlers:

def _get_flattened_payload(msg_part, with_mime_headers=False):

    flattened_data = msg_part.as_string(unixfrom=False)

    # if with_mime_headers is false, then remove them:
    if not with_mime_headers:
        # Regex should remove from the start of the string up to the
        # first double newline '\n\n', with possibly space in-between
        # the newlines. This should chop of the mime_headers.

        # (?s) in the regex sets the DOTALL flag; ie. '.' matches everything including newline.
        flattened_data = re.sub(r'(?s)(.*?\n\n)', r'', flattened_data, count=1)

    return flattened_data

def _email_structure_to_directory_structure(email_structure, directory_base=''):

    files = []
    used_random = {}
    alt_part_number = 0

    for item in email_structure:
        try:
            # Is it a list? (ie. a list of alternative parts):
            item.append # Does this throw AttributeError? If not, it is list like.
            alt_part_number += 1
            files.extend(_email_structure_to_directory_structure(email_structure=item,
                                                                 directory_base=os.path.join(directory_base,
                                                                                             ('alternative_data_' + str(alt_part_number)))))
        except AttributeError:
            # Or a dictionary? (ie. an actual part):
            possible_filenames = [item['filename'],
                                  item['generated_filename'],
                                  'unamed_part_' + _get_unused_random(lambda: _random_alphanum_string(length=8), used_random)]
            available_filenames = filter(lambda x: x is not None, possible_filenames)
            filename = available_filenames[0]

            if item['file'] is not None:
                files.append((os.path.join(directory_base, filename), item['file']))
            else:
                files.append((filename, ''))

            if item['downgrading_to_text'] is not None:
                files.append((os.path.join(directory_base, filename + '.txt'), item['downgrading_to_text']))

    return files

def _archive_part(msg, mhe, strict, hints):

    processed_parts = _get_mime_handler('multipart', 'mixed')(msg, mhe, strict, hints)
    files = _email_structure_to_directory_structure(processed_parts)

    mhe.file = elmsubmit_EZArchive.create(files, input_disposition='named_byte_strings',
                                          compress_to='byte_string',
                                          compression=hints['archive_format'],
                                          force_file_permissions=0664,
                                          force_dir_permissions=0775)

    mhe.filename = '_'.join([_random_alphanum_string(length=8), mhe.maintype, mhe.subtype,
                             'archive.' + hints['archive_format']])

def _pick_from_alternatives(processed_parts):

    processed_parts.sort(multipart_alternative_sort)
    return (processed_parts[0], processed_parts[1:])

def multipart_alternative_sort(part1, part2):

    # We deal with multipart/alternative by prefering in descending
    # order:
    # text/plain, score 6
    # text/html, score 5
    # text/enriched, score 4
    # text/richtext, score 3
    # text/rtf, score 2
    # application/rtf, score 1

    # (the later five we make use of their 'downgrading_to_text')

    # Although text/richtext is a simpler format than text/html, it
    # has theoretically been obsoleted by text/enriched and so comes
    # lower in order of preference.

    # A note on the rich text mess: "Why are their four types of rich
    # text? Surely they're all the same thing?" Unfortunately not...

    # - RFC1341 defines a simple text markup for mime type
    # 'text/richtext'.

    # - RFC1896 (and some RFCS before it which 1896 obsoletes) defines
    #   'text/enriched' which is designed to solve the shortcomings of
    #   'text/richtext'; use of 'text/richtext' is deprecated in
    #   favour of 'text/enriched'

    # - 'text/rtf' and 'application/rtf' refer to Microsoft's RTF file
    # format, and are not specified in any RFC (that I know of). They
    # are the same file format; it's just that the registration got
    # duplicated (people weren't sure whether to describe rtf as a
    # plaintext format; ie. readable when unparsed by humans, or
    # application (ie. needs to be parsed to make any sense of)!

    # Some useful reading:

    # http://mango.human.cornell.edu/kens/etf.html (text/enriched primer)
    # http://www.faqs.org/rfcs/rfc1896.html (text/enriched RFC)
    # http://www.faqs.org/rfcs/rfc1341.html (text/richtext RFC)
    # News message ID: <199306081944.AA13622@mudhoney.micro.umn.edu>
    #                  (the thread this message sits in contains the
    #                   registrations of text/rtf and application/rtf)

    liked_formats = [ 'text/plain',
                      'text/html',
                      'text/enriched',
                      'text/richtext',
                      'text/rtf',
                      'application/rtf' ]

    scorecard = dict(zip(liked_formats, range(len(liked_formats), 0, -1)))

    # Create something that looks like this:

    #     {'application/rtf': 1,
    #      'text/enriched': 4,
    #      'text/html': 5,
    #      'text/plain': 6,
    #      'text/richtext': 3,
    #      'text/rtf': 2}

    # Doing the calculation instead of hardcoding allows liked_formats
    # to be rearranged more easily!

    # Part types not in this list get score 0.

    score1 = scorecard.get(part1['maintype'] + '/' + part1['subtype'], 0)
    score2 = scorecard.get(part2['maintype'] + '/' + part2['subtype'], 0)
    # We want the list in reverse order, big down to small:
    return cmp(score2, score1)

def _get_unused_random(rand_function, used_random):

    r = rand_function()

    while r in used_random:
        r = rand_function()

    used_random[r] = True
    return r

class _MimeHelper(object):

    def __init__(self, msg_part):

        self.msg_part = msg_part
        self.maintype = msg_part.get_content_maintype()
        self.subtype = msg_part.get_content_subtype()
        if self.maintype == 'text':
            self.charset = msg_part.get_content_charset('us-ascii')
        else:
            self.charset = None
        self.disposition = _get_part_disposition(msg_part)
        self.filename = _get_part_filename(msg_part)
        self.signed = False
        self.signature = None
        self.encrypted = False
        self.mac_resource_fork = None
        self.downgrading_to_text = None
        self.rejected_alternatives = None

        if msg_part.is_multipart():
            # If multipart, get the flattened payload.
            self.decoded_payload = _get_flattened_payload(msg_part, with_mime_headers=False)
        else:
            # If its not multipart, attempt CTE decoding and store
            # result:
            try:
                self.decoded_payload = _cte_decode(msg_part)
            except (_CTEDecodingError, _MultipartCTEDecodingAttempt):
                self.decoded_payload = None

def _mime_handler_application_applefile(msg, mhe, strict, hints):
    return [{mhe.maintype : 'not implemented yet'}]

def _mime_handler_application_octetstream(msg, mhe, strict, hints):

    # application/octet-stream requires no special handling. All of
    # the necessary work has been done in the parent handler.

    mhe.file = mhe.decoded_payload
    return [ _format_msg_part_data(mhe, hints) ]

def _mime_handler_application_pgpencrypted(msg, mhe, strict, hints):
    return [{mhe.maintype : 'not implemented yet', mhe.subtype : 'problems!'}]
def _mime_handler_application_pgpkeys(msg, mhe, strict, hints):
    return [{mhe.maintype : 'not implemented yet', mhe.subtype : 'problems!'}]
def _mime_handler_application_pgpsignature(msg, mhe, strict, hints):
    return [{mhe.maintype : 'not implemented yet', mhe.subtype : 'problems!'}]
def _mime_handler_application_rtf(msg, mhe, strict, hints):

    # application/rtf is same as text/rtf, so call _get_mime_handler
    # to retrieve correct handler.

    # Note that we can't just execute _mime_handler_text_rtf directly,
    # because this would miss the neccessary parent_handler code,
    # which depends on knowing if maintype is 'text' (which the
    # misregistered application/rtf would hide):
    return _get_mime_handler('text', 'rtf')(msg, mhe, strict, hints)

def _mime_handler_message_externalbody(msg, mhe, strict, hints):
    return [{mhe.maintype : 'not implemented yet', mhe.subtype : 'problems!'}]

# def _mime_handler_message_news(msg, mhe, strict, hints):
#     pass
# Currently just treat as application/octet-stream.

def _mime_handler_message_partial(msg, mhe, strict, hints):

    if strict:
        raise MIMEPartError(msg, mhe, 'not_implemented')
    else:
        return []

def _mime_handler_message_rfc822(msg, mhe, strict, hints):

    if not hints['descend_message_rfc822_attachments']:
        # Treat as a binary attachment.
        return _get_mime_handler('application', 'octet-stream')(msg, mhe, strict, hints)
    else:
        # Descend into the message as if it were a multipart/mixed
        # type.
        return _get_mime_handler('multipart', 'mixed')(msg, mhe, strict, hints)

def _mime_handler_multipart_alternative(msg, mhe, strict, hints):

    # We handle multipart alternative just like multipart mixed, but
    # then pick our prefered alternative, storing the remaining
    # alternatives in mhe.rejected_alternatives.

    (prefered, rejects) = _pick_from_alternatives(_get_mime_handler('multipart', 'mixed')(msg, mhe, strict, hints))
    prefered['rejected_alternatives'] = rejects
    return [ prefered ]

def _mime_handler_multipart_appledouble(msg, mhe, strict, hints):
    return [{mhe.maintype : 'not implemented yet', mhe.subtype : 'problems!'}]
def _mime_handler_multipart_encrypted(msg, mhe, strict, hints):
    return [{mhe.maintype : 'not implemented yet', mhe.subtype : 'problems!'}]
def _mime_handler_multipart_mixed(msg, mhe, strict, hints):

    # We ignore Content-Disposition for multipart/mixed parts, as want
    # to process them the same regardless.

    # Generate mime helpers for each part of the multipart collection:
    mime_helpers = map(_MimeHelper, mhe.msg_part.get_payload())

    # Get a mime handler for each part, and execute it:
    f = lambda mhe: _get_mime_handler(mhe.maintype, mhe.subtype)(msg, mhe, strict, hints)

    list_of_lists_of_processed_parts = map(f, mime_helpers)

    # Flatten the results:
    return _concat(list_of_lists_of_processed_parts)

def _mime_handler_multipart_signed(msg, mhe, strict, hints):
    return [{mhe.maintype : 'not implemented yet', mhe.subtype : 'problems!'}]

def _mime_handler_multipart_unrecognized(msg, mhe, strict, hints):

    if hints['archive_multipart_unrecognized']:
        _archive_part(msg, mhe, strict, hints)
        return [ _format_msg_part_data(mhe, hints) ]
    else:
        # Descend into the message as if it were a multipart/mixed
        # type.
        return _get_mime_handler('multipart', 'mixed')(msg, mhe, strict, hints)

def _mime_handler_multipart_parallel(msg, mhe, strict, hints):

    if hints['archive_multipart_parallel']:
        _archive_part(msg, mhe, strict, hints)
        return [ _format_msg_part_data(mhe, hints) ]
    else:
        # Descend into the message as if it were a multipart/mixed
        # type.
        return _get_mime_handler('multipart', 'mixed')(msg, mhe, strict, hints)

def _mime_handler_multipart_related(msg, mhe, strict, hints):

    if hints['archive_multipart_related']:
        _archive_part(msg, mhe, strict, hints)
        return [ _format_msg_part_data(mhe, hints) ]
    else:
        # Descend into the message as if it were a multipart/mixed
        # type.
        return _get_mime_handler('multipart', 'mixed')(msg, mhe, strict, hints)

def _mime_handler_text_enriched(msg, mhe, strict, hints):

    # Covert the text/enriched data to plain text and store it:
    # mhe.file is already a unicode string.

    # enriched2txt function doesn't have any public errors:
    mhe.downgrading_to_text = _enriched2txt.enriched2txt(_native2unicode(mhe.decoded_payload, native_charset=mhe.charset, strict=strict))
    return [ _format_msg_part_data(mhe, hints) ]

def _mime_handler_text_html(msg, mhe, strict, hints):

    # Covert the text/richtext data to plain text and store it. We
    # pass richtext2txt the original non-unicode text string and it
    # will pass us back a unicode string:

    try:
        # html2txt expects unicode in, and spits unicode out:
        mhe.downgrading_to_text = _html2txt.html2txt(_native2unicode(mhe.decoded_payload, native_charset=mhe.charset, strict=strict), cols=72)
    except _html2txt.HTMLParsingFailed:
        if strict:
            raise MIMEPartError(msg, mhe, 'downgrading_to_text')
        else:
            mhe.downgrading_to_text = None

    return [ _format_msg_part_data(mhe, hints) ]

def _mime_handler_text_plain(msg, mhe, strict, hints):

    return [ _format_msg_part_data(mhe, hints) ]

def _mime_handler_text_richtext(msg, mhe, strict, hints):

    # Covert the text/richtext data to plain text and store it. We
    # pass richtext2txt the original non-unicode text string and it
    # will pass us back a unicode string:

    try:
        # richtext2txt always returns unicode for us:
        mhe.downgrading_to_text = _richtext2txt.richtext2txt(mhe.decoded_payload, charset=mhe.charset,
                                                            convert_iso_8859_tags=True, force_conversion=(not strict))
    except _richtext2txt.RichTextConversionError:
        if strict:
            raise MIMEPartError(msg, mhe, 'downgrading_to_text')
        else:
            mhe.downgrading_to_text = None

    return [ _format_msg_part_data(mhe, hints) ]

def _mime_handler_text_rtf(msg, mhe, strict, hints):

    # Note: This parser has some unicode issues which need to be
    # fixed! The project seems fairly active...

    # Use RtfLib to convert rtf string to text.
    try:
        mhe.downgrading_to_text = rtf.Rtf2Txt.getTxt(_native2unicode(mhe.decoded_payload, native_charset=mhe.charset, strict=strict))
    except _RtfException:
        if strict:
            raise MIMEPartError(msg, mhe, 'downgrading_to_text')
        else:
            mhe.downgrading_to_text = None

    return [ _format_msg_part_data(mhe, hints) ]

# Content-Type to Handler mappings:

_mime_handler_map_application = { 'applefile'     : _mime_handler_application_applefile,
                                  'octet-stream'  : _mime_handler_application_octetstream,
                                  'pgp-encrypted' : _mime_handler_application_pgpencrypted,
                                  'pgp-keys'      : _mime_handler_application_pgpkeys,
                                  'pgp-signature' : _mime_handler_application_pgpsignature,
                                  'rtf'           : _mime_handler_application_rtf }

_mime_handler_map_audio = { } # No special audio handlers defined.

_mime_handler_map_image = { } # No special image handlers defined.

_mime_handler_map_message = { 'external-body' : _mime_handler_message_externalbody,
#                             'news'          : _mime_handler_application_octetstream,
                              'partial'       : _mime_handler_message_partial, # not supported!
                              'rfc822'        : _mime_handler_message_rfc822 }

_mime_handler_map_model = { } # No special models handlers defined.

_mime_handler_map_multipart = { 'alternative' : _mime_handler_multipart_alternative,
                                'appledouble' : _mime_handler_multipart_appledouble,
                                'encrypted'   : _mime_handler_multipart_encrypted,
                                'mixed'       : _mime_handler_multipart_mixed,
                                'parallel'    : _mime_handler_multipart_parallel,
                                'related'     : _mime_handler_multipart_related,
                                'signed'      : _mime_handler_multipart_signed }

_mime_handler_map_text = { 'enriched' : _mime_handler_text_enriched,
                           'html'     : _mime_handler_text_html,
                           'plain'    : _mime_handler_text_plain,
                           'richtext' : _mime_handler_text_richtext,
                           'rtf'      : _mime_handler_text_rtf }

_mime_handler_map_video = { } # No special video handlers defined.

_mime_handler_map = { 'application'  : _mime_handler_map_application,
                      'audio'        : _mime_handler_map_audio,
                      'image'        : _mime_handler_map_image,
                      'message'      : _mime_handler_map_message,
                      'model'        : _mime_handler_map_model,
                      'multipart'    : _mime_handler_map_multipart,
                      'text'         : _mime_handler_map_text,
                      'video'        : _mime_handler_map_video }

# Unrecognized types are handled according to the recomendations of
# RFC2046 which mandates that unrecognized parts of given maintype be
# dealt with as follows:

# application  -> application/octet-stream
# audio        -> application/octet-stream
# image        -> application/octet-stream
# message      -> application/octet-stream
# model        -> application/octet-stream

# In the multipart case, however, we give the module client two
# choices of how to treat unrecognized multipart sections: either as
# multipart/mixed, or to wrap up each of the sub-parts into a tar.gz
# and present this as if it had been a single attachment.

# multipart    -> multipart/mixed
# text         -> text/plain
# video        -> application/octet-stream

_mime_handler_map_unrecognized_subtype  = { 'application'  : _mime_handler_application_octetstream,
                                            'audio'        : _mime_handler_application_octetstream,
                                            'image'        : _mime_handler_application_octetstream,
                                            'message'      : _mime_handler_application_octetstream,
                                            'model'        : _mime_handler_application_octetstream,
                                            'multipart'    : _mime_handler_multipart_unrecognized,
                                            'text'         : _mime_handler_text_plain,
                                            'video'        : _mime_handler_application_octetstream }

_mime_handler_unrecognized_maintype = _mime_handler_application_octetstream

# Message Creation:

# Whereas ParseMessage is a class, CreateMessage is just a function
# which returns the email as an ascii byte string.

# Creation is an order of magnitude simpler than parsing. When parsing
# we have to try and be able to cope with everything seen out 'in the
# wild'. With creation, we can simply restrict what is allowed to be
# created to a sensible set of options.

# CreateMessage restricts you to a single plain text body plus any
# number of attached files and any number of attached emails. This
# will all be stuffed into a single multipart/mixed container (unless
# there is only a single part to be added, in which case we skip the
# multipart/mixed container). This is how email should be sent by good
# internet citizens. If this doesn't fit your needs, then your needs
# are esoteric (and if you want to send html email, then you're just
# plain evil)!

def CreateMessage(_from,
                  to,
                  subject,
                  cc=None,
                  bcc=None,
                  message=None,
                  attach_messages=[],
                  attach_files=[],
                  message_id=None,
                  references=None,
                  in_reply_to=None,
                  date=None,
                  wrap_message=False,
                  cols=80):

    """
    Returns a byte string containing the email constructed from the
    following arguments:

    _from: Either:   1. An ascii string already suitable for inclusion
                        in this email header (eg. a string you have
                        torn directory out of another email.

                     2. A 2-tuple (name, email_address), where name is
                        a persons name and email_address is their
                        email address. name must be a unicode object.
                        email_address can be either a unicode object
                        or a byte string.

    to,
    cc,
    bcc: Either:     1. An ascii string already suitable for inclusion
                        in this email header (eg. a string you have
                        torn directory out of another email.

                     2. A _list_ of items defined in the same way as
                        _from option 1.

    subject: Either: 1. An ascii string already suitable for inclusion
                        in this email header (eg. a string you have
                        torn directory out of another email.

                     2. A unicode object.

    message:            A unicode object containing what will be the
                        message body text.

    attach_files:       A list of 2-tuples, (filename, open_file_object)
                        where filename must be a unicode object and
                        open_file_object must be an open python file
                        object in mode 'rb'.

    message_id:         An ascii string containing a message-id.

    references:         A list of objects defined like argument message_id.

    in_reply_to:        A list of objects defined like argument message_id.

    date:               A ascii string containing an rfc822 formatted date string.

    wrap_message:       True/False whether you want to have the message body
                        wrapped to the width given in argument cols.

    cols:               A integer column width.
    """

    if message is not None:
        mime_message = [_mimeify_message(message, wrap_message, cols)]
    else:
        mime_message = []

    mime_attached_messages = map(_mimeify_attach_message, attach_messages)
    mime_attached_files = map(_mimeify_attach_file, attach_files)

    mime_parts = mime_message + mime_attached_messages + mime_attached_files

    if mime_parts == []:
        raise EZEmailCreateError("At least one of message, attach_messages or attach_files must be specified.")
    elif len(mime_parts) == 1:
        # Only one payload, so don't need multipart.
        main_part = mime_parts[0]
    else:
        main_part = email.MIMEMultipart.MIMEMultipart()
        map(main_part.attach, mime_parts)
        main_part.preamble = 'This message requires a mime aware email reader to be viewed correctly.\n'
        # Force ending in newline:
        main_part.epilogue = ''

    eH = email.Header.Header

    # The .encode() call here shouldn't be doing any encoding other
    # splitting the header onto multiple continuation lines, since we
    # are already providing eH with safely asciified strings.

    main_part['From'] = eH(_mimeify_address(_from)).encode()
    main_part['Subject'] = eH(_mimeify_unstructured(subject)).encode()

    for (header, value) in [('To', to),('Cc', cc), ('Bcc', bcc)]:

        if value is None:
            continue

        if isinstance(value, str):
            main_part[header] = eH(value).encode()
        else:
            main_part[header] = eH(', '.join(map(_mimeify_address, value))).encode()

    if message_id is not None:
        main_part['Message-ID'] = eH(message_id).encode()
    else:
        main_part['Message-ID'] = email.Utils.make_msgid()

    if references is not None:
        main_part['References'] = eH(', '.join(references)).encode()

    if in_reply_to is not None:
        main_part['In-Reply-To'] = eH(in_reply_to).encode()

    if date is not None:
        main_part['Date'] = eH(date).encode()
    else:
        main_part['Date'] = email.Utils.formatdate()

#     s = smtplib.SMTP()
#     print ">>>fnah"
#     s.connect(host='smtp.ox.ac.uk')
#     s.sendmail('one@tes.la', 'foo@tes.la', main_part.as_string())
#     s.close()

    return main_part.as_string()

def _mimeify_message(message, wrap_message, cols):

    if wrap_message:
        message = _wrap_text(message, cols)

    if _just_ascii(message):
        charset = 'us-ascii'
    else:
        charset = 'utf8'

    msg_part = email.MIMEText.MIMEText(_text=message.encode(charset),
                                       _subtype='plain',
                                       _charset=charset)

    msg_part.add_header('Content-Disposition', 'inline')

    return msg_part

def _mimeify_attach_message(message_rfc822):

    message_rfc822 = email.message_from_string(message_rfc822)
    return email.MIMEMessage.MIMEMessage(message_rfc822, 'rfc822')

def _mimeify_attach_file((filename_unicode, fh)):
    # fh = python file handle

    # Guess the content type based on file extension.
    content_type, encoding = mimetypes.guess_type(filename_unicode)

    if encoding == 'gzip':
        content_type = 'application/x-gzip'
    elif encoding == 'compress':
        content_type = 'application/x-gzip'
    elif encoding is not None:
        # we don't recognize the encoding:
        content_type = 'application/octet-stream'
    else:
        # encoding is None; we are safe to use the content_type
        # returned by mimetypes.
        pass

    # Check that mimetypes actually returned a content_type:
    if content_type is None:
        content_type = 'application/octet-stream'

    maintype, subtype = content_type.split('/', 1)

    if maintype == 'text':

        # This is what we should be doing:

        # msg_part = email.MIMEText.MIMEText(fh.read(), _subtype=subtype)

        # but until I gather together character encoding detection,
        # everything text is going to be attached as
        # application/octet-stream.

        msg_part = email.MIMEBase.MIMEBase('application', 'octet-stream')
        msg_part.set_payload(fh.read())

        # Encode the payload using Base64
        email.Encoders.encode_base64(msg_part)

    elif maintype == 'image':
        msg_part = email.MIMEImage.MIMEImage(fh.read(), _subtype=subtype)
    elif maintype == 'audio':
        msg_part = email.MIMEAudio.MIMEAudio(fh.read(), _subtype=subtype)
    else:

        msg_part = email.MIMEBase.MIMEBase(maintype, subtype)
        msg_part.set_payload(fh.read())

        # Encode the payload using Base64
        email.Encoders.encode_base64(msg_part)

    # Set the filename parameter
    msg_part.add_header('Content-Disposition', 'attachment')
    _set_filename(msg_part, filename_unicode)
    return msg_part

def _mimeify_address(address):

    if isinstance(address, str):
        return address
    else:
        (name, email_addr) = address
        return email.Utils.formataddr((_mimeify_unstructured(name), email_addr))

def _set_filename(msg_part, filename_unicode):

    # Filename parameter of structured header gets rfc2231 encoded:
    if _just_ascii(filename_unicode):
        filename = filename_unicode.encode('us-ascii')
        msg_part.set_param(param='filename', value=filename,
                           header='Content-Disposition')
    else:
        charset = 'utf8'
        filename = filename_unicode.encode('utf8')
        msg_part.set_param(param='filename', value=filename,
                           header='Content-Disposition', charset=charset)

def _mimeify_unstructured(string):

    if not isinstance(string, unicode):
        # Unstructured fields get RFC2047 encoded.
        return string
    elif _just_ascii(string):
        return string.encode('us-ascii')
    else:
        return str(email.Header.make_header([(string.encode('utf8'), 'utf8')]))

def _just_ascii(unicode_string):
    # Are are the objects in the unicode string ascii character?:
    return unicode_string.encode('utf8') == unicode_string.encode('us-ascii', 'ignore')

# Error classes.

class _EmailPackageError(Exception):
    """
    Private error that will only be thrown for suspected programming
    errors in the Python email package.
    """

class EZEmailError(Exception):
    pass

class EZEmailParseError(EZEmailError):

    """
    An emtpy parent class for all public errors in this module.
    """

    def __init__(self, msg):

        """
        """

        self.basic_email_info = _basic_email_info(msg)
        Exception.__init__(self)

class EZEmailCreateError(EZEmailError):
    pass

class _EZEmailPrivateError(Exception):

    """
    An emtpy parent class for all private errors in this module.
    """

    pass

class _UnicodeDecodingError(_EZEmailPrivateError):

    """
    This is a private error which can be raised if attempting to use
    the unicode builtin fails because the charset we try to decode
    from isn't recognized.
    """

    def __init__(self, value, charset):

        """
        Constructor takes single argument; a string giving the name of
        the problem charset.
        """

        self.value = value
        self.charset = charset


class _StructuredHeaderPairError(_EZEmailPrivateError):

    """
    This is a private error which will be raised if there is an error
    trying to parse and rejoin a key/value pair from a structured
    header.
    """

    def __init__(self, key, value):

        self.key = key
        self.value = value

class HeaderRFC2231Error(EZEmailParseError):

    """
    This error is raised if we can't decode a structured header
    (eg. Content-Type or Content-Disposition) successfully.
    """

    def __init__(self, msg, header, header_value, key, key_value):

        self.header = header
        self.header_value = header_value
        self.key = key
        self.key_value = key_value

        EZEmailParseError.__init__(self, msg)

class HeaderCharsetError(EZEmailParseError):

    """
    This error is raised if we can't recognize one of the charsets
    used in a particular header.
    """

    def __init__(self, msg, header, header_value, problem_part, charset):

        """
        Constructor takes an email.Message message object and header,
        value and charset (in their original rfc2047 encoding) as
        arguments and stores them.
        """

        self.header = header
        self.header_value = header_value
        self.problem_part = problem_part
        self.charset = charset

        EZEmailParseError.__init__(self, msg)

    def __str__(self):
        return "header: %s\nheader value: %s\nproblem part: %s\ncharset: %s" % (self.header, self.header_value, self.problem_part, self.charset)

class HeaderRFC2047Error(EZEmailParseError):

    """
    This error is raised if we can't parse the RFC2047 encoding used
    in a particular header.
    """

    def __init__(self, msg, header, value):

        """

        Constructor takes an email.Message message object and header,
        value and charset (in their original rfc2047 encoding) as
        arguments and stores them.

        """

        self.header = header
        self.value = value

        EZEmailParseError.__init__(self)

    def __str__(self):
        return "\nheader: %s\nvalue: %s\ninfo: %s" % (self.header, self.value, self.basic_email_info)


class FromHeaderParsingError(EZEmailParseError):

    """
    We have a From: header we can't parse.
    """
    def __str__(self):
        return "\ninfo: %s" % (self.basic_email_info)


class FromHeaderMissingError(EZEmailParseError):

    """
    Somehow we have recieved a seriously broken email with no From: header. Reject!
    """

    pass


class _ParseDateError(_EZEmailPrivateError):

    """

    Private error raised when email.Utils.parsedate or
    email.Utils.parsedate_tz fails to parse a date header value.

    """

    pass

class ParseDateError(EZEmailParseError):

    """

    Public error raised when email.Utils.parsedate or
    email.Utils.parsedate_tz fails to parse a date header value.

    """

    pass

class _CTEDecodingError(_EZEmailPrivateError):

    pass

class _MultipartCTEDecodingAttempt(_EZEmailPrivateError):

    """
    Raised if an attempt is made to CTE decode a multipart message
    part.
    """

    pass

class MIMEPartError(EZEmailParseError):

    def __init__(self, msg, mhe, error_type):

        self.maintype = mhe.maintype
        self.subtype = mhe.subtype
        self.filename = mhe.filename

        if mhe.decoded_payload is None or mhe.msg_part.is_multipart():
            # If we haven't decoded payload successfully, take sample
            # from CTE encoded payload:
            self.sample = mhe.msg_part.get_payload()[0:100]
        else:
            # Otherwise, take sample from CTE decoded payload:
            self.sample = mhe.decoded_payload[0:100]

        if error_type in self.valid_error_types:
            self.error_type = error_type
        else:
            raise ValueError('Programming Error: error_type = \'' + error_type +
                             '\' is not valid for MIME parts')

        EZEmailParseError.__init__(self, msg)

    valid_error_types = ['cte_decoding', 'filename_decoding', 'downgrading_to_text',
                         'unicode_conversion', 'not_implemented']

    def __str__(self):

        return "maintype: %s\nsubtype: %s\nfilename: %s\nsample: %s\nerror_type: %s" % (self.maintype, self.subtype, self.filename, self.sample, self.error_type)

if __name__ == "__main__":
    import sys
#    import profile
    def f():
        for filename in sys.stdin.xreadlines():
            print(filename, end=' ')
            filename = filename[:-1]
            contents(filename)
            print("===")
            a = ParseMessage(open(filename, 'rb').read(), strict=False)
            print(a.primary_message())
    f()
#    profile.run('f()')


