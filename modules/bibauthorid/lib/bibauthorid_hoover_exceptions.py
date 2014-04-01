##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from hashlib import md5
from invenio.bibauthorid_dbinterface import get_canonical_name_of_author, get_name_by_bibref
from invenio.config import CFG_SITE_URL


class HooverException(Exception):

    """Main class for hoover exceptions.

    Arguments:
    message -- a string with the message to be displayed to the user
    """

    def __init__(self, message):
        Exception.__init__(self, message)
        self.recid = -1

    def get_message_body(self):
        """Return the body of the message to be reported by the exception"""
        raise NotImplementedError(self.__repr__())

    def get_message_subject(self):
        """Return the subject of the message to be reported by the exception"""
        raise NotImplementedError(self.__repr__())

    def hash(self):
        """Return the hash of the message to be reported by the exception"""
        raise NotImplementedError(self.__repr__())


class InconsistentIdentifiersException(HooverException):

    """Exception Class in case an author is found with 2 different
    identifiers connected to his profile.

    Arguments:
    message -- the message to be displayed when the exceptions is raised
    pid -- the pid of the author that caused the exception
    identifier_type -- the type of the identifiers
    ids_list -- an iterable holding all the values of the identifiers
    """

    def __init__(self, message, pid, identifier_type, ids_list):
        HooverException.__init__(self, message)
        self.pid = pid
        self.identifier_type = identifier_type
        self.ids_list = ids_list

    def get_message_subject(self):
        """Return the subject of the message to be reported by the exception"""
        return '[Hoover] Author found with multiple derived identifiers of the same kind'

    def get_message_body(self):
        """Return the body of the message to be reported by the exception"""
        msg = [
            "Found multiple different %s identifiers (%s) on profile: " %
            (self.identifier_type,
             ','.join(
                 self.ids_list))]
        msg.append(
            "%s/author/profile/%s" %
            (CFG_SITE_URL, get_canonical_name_of_author(
                self.pid)[0]))
        # msg.append(self.message)
        return '\n'.join(msg)

    def hash(self):
        """Return the hash of the message to be reported by the exception"""
        return md5(self.__repr__() +
                   str(self.pid) +
                   str(self.identifier_type)).hexdigest()


class DuplicatePaperException(HooverException):

    """Base class for duplicated papers conflicts

    Arguments:
    message -- the message to be displayed when the exceptions is raised
    pid -- the pid of the author that caused the exception
    signature -- the signature that raised the exception
    present_signatures -- the signatures that are already present in the paper
    """

    def __init__(self, message, pid, signature, present_signatures):
        HooverException.__init__(self, message)
        self.pid = pid
        self.signature = signature
        self.present_signatures = present_signatures

    def hash(self):
        """Return the hash of the message to be reported by the exception"""
        return md5(self.__repr__() +
                   str(self.pid) +
                   str(self.signature)).hexdigest()


class DuplicateClaimedPaperException(DuplicatePaperException):

    """Class for duplicated papers conflicts when one of them is claimed"""

    def get_message_subject(self):
        return '[Hoover] Wrong signature claimed to profile'

    def get_message_body(self):
        """Return the body of the message to be reported by the exception"""
        msg = ['Found wrong signature claimed to profile ']
        try:
            cname = get_canonical_name_of_author(self.pid)[0]
        except IndexError:
            cname = self.pid

        msg.append("%s/author/profile/%s" % (CFG_SITE_URL, cname))
        sig_name = get_name_by_bibref(self.signature[0:2])
        p_sigs = [(x, get_name_by_bibref(x[0:2]))
                  for x in self.present_signatures]

        p_sig_strings = ",".join(
            '%s (%s on record %s)' %
            (x[0], x[1], x[0][2]) for x in p_sigs)

        msg.append(
            "want to move %s (%s on record %s) to this profile but [%s] are already present and claimed" %
            (self.signature, sig_name, self.signature[2], p_sig_strings))
        msg.append("%s/record/%s" % (CFG_SITE_URL, self.signature[2]))
        # msg.append(self.message)
        return '\n'.join(msg)

# This class does not have any usage yet


class DuplicateUnclaimedPaperException(DuplicatePaperException):

    """Class for duplicated papers conflicts when one of them is unclaimed"""
    pass


class BrokenHepNamesRecordException(HooverException):

    """Base class for broken HepNames records

    Arguments:
    message -- the message to be displayed when the exceptions is raised
    recid -- the recid of the record that caused the exception
    identifier_type -- the type of the identifier that caused the exception
    """

    def __init__(self, message, recid, identifier_type):
        HooverException.__init__(self, message)
        self.recid = recid
        self.identifier_type = identifier_type

    def get_message_subject(self):
        return '[Hoover] Found a broken HepNames record'

    def get_message_body(self):
        """Return the body of the message to be reported by the exception"""
        msg = [
            'Found broken hepnames record %s/record/%s' %
            (CFG_SITE_URL, self.recid)]
        msg.append(
            'Something went wrong while trying to read the %s identifier' %
            self.identifier_type)
        # msg.append(self.message)
        return '\n'.join(msg)

    def hash(self):
        """Return the hash of the message to be reported by the exception"""
        return md5(self.__repr__() +
                   str(self.recid) +
                   str(self.identifier_type)).hexdigest()


class NoCanonicalNameException(HooverException):

    """Base class for no canonical name found for a pid.

    Arguments:
    message -- the message to be displayed when the exceptions is raised
    pid -- the pid of the author that lacks a canonical name
    """

    def __init__(self, message, pid):
        HooverException.__init__(self, message)
        self.pid = pid

    def hash(self):
        """Return the hash of the message to be reported by the exception"""
        return md5(self.__repr__() + str(self.pid)).hexdigest()


class ConflictingIdsOnRecordException(HooverException):

    """Exception class for when there are 2 different identifiers of the same
    type associated with one signature inside a record.

    Arguments:
    message -- the message to be displayed when the exceptions is raised
    pid -- the pid of the author that the signature belogs to
    identifier_type -- the type of the the identifier
    ids_list -- an iterable holding all the values of the identifiers
    recid -- the recid of the record that caused the exception
    """

    def __init__(self, message, pid, identifier_type, ids_list, signature):
        HooverException.__init__(self, message)
        self.pid = pid
        self.identifier_type = identifier_type
        self.ids_list = ids_list
        self.signature = signature

    def get_message_subject(self):
        """Return the subject of the message to be reported by the exception"""
        return '[Hoover] Signature on record holds more then one identifiers of the same kind'

    def get_message_body(self):
        """Return the body of the message to be reported by the exception"""
        #msg = ['Signature on record holds more then one identifiers of the same kind']
        try:
            cname = get_canonical_name_of_author(self.pid)[0]
        except IndexError:
            cname = self.pid

        msg = ["Profile: %s/author/profile/%s" % (CFG_SITE_URL, cname)]
        msg.append(
            "Record: %s/record/%s" %
            (CFG_SITE_URL, self.signature[2]))
        msg.append("Signature: %s" % str(self.signature))
        msg.append(
            "The following identifiers are associated with the signature: %s" %
            ', '.join(
                self.ids_list))
        # msg.append(self.message)
        return '\n'.join(msg)

    def hash(self):
        """Return the hash of the message to be reported by the exception"""
        return md5(self.__repr__() +
                   str(self.signature[2]) +
                   str(self.identifier_type)).hexdigest()


class MultipleAuthorsWithSameIdException(HooverException):

    """Base class for multiple authors with the same id

    Arguments:
    message -- the message to be displayed when the exceptions is raised
    pids -- an iterable with the pids that have the same id
    identifier_type -- the type of the identifier that caused the exception
    """

    def __init__(self, message, pids, identifier_type):
        HooverException.__init__(self, message)
        self.pids = tuple(pids)
        self.identifier_type = identifier_type

    def get_message_subject(self):
        """Return the subject of the message to be reported by the exception"""
        return '[Hoover] Found conflicting profile user-verified identifiers'

    def get_message_body(self):
        """Return the body of the message to be reported by the exception"""
        msg = [
            'Found conflicting profiles with conflicting user-verified identifiers: ']
        msg += ['%s/author/profile/%s' %
                (CFG_SITE_URL, r) for r in self.pids]
        msg.append(
            'Those profiles are sharing the same %s identifier!' %
            self.identifier_type)
        # msg.append(self.message)
        return '\n'.join(msg)

    def hash(self):
        """Return the hash of the message to be reported by the exception"""
        return md5(self.__repr__() +
                   str(sorted(self.pids)) +
                   str(self.identifier_type)).hexdigest()


class MultipleIdsOnSingleAuthorException(HooverException):

    """Base class for multiple ids on a single author

    Arguments:
    message -- the message to be displayed when the exceptions is raised
    pid -- the pid of the author
    ids -- an iterable with the identifiers of the author
    identifier -- the type of the identifier that caused the exception
    """

    def __init__(self, message, pid, identifier_type, ids):
        HooverException.__init__(self, message)
        self.pid = pid
        self.ids = tuple(ids)
        self.identifier_type = identifier_type

    def get_message_subject(self):
        """Return the subject of the message to be reported by the exception"""
        return '[Hoover] Profile with multiple user-verified identifiers of the same kind'

    def get_message_body(self):
        """Return the body of the message to be reported by the exception"""
        #msg = ['Found profile with multiple conflicting user-verified identifiers: ']
        msg = ['Profile: %s/author/profile/%s' % (CFG_SITE_URL, self.pid)]
        msg.append(
            'This profile has all this %s identifiers:' %
            self.identifier_type)
        msg.append(', '.join(str(x) for x in self.ids))
        msg.append(
            'Each profile should have only one identifier of each kind.')
        # msg.append(self.message)
        return '\n'.join(msg)

    def hash(self):
        """Return the hash of the message to be reported by the exception"""
        return md5(self.__repr__() +
                   str(self.pid) +
                   str(self.identifier_type)).hexdigest()


class MultipleHepnamesRecordsWithSameIdException(HooverException):

    """Base class for conflicting HepNames records

    Arguments:
    message -- the message to be displayed when the exceptions is raised
    recids -- an iterable with the record ids that are conflicting
    identifier -- the type of the identifier that caused the exception
    """

    def __init__(self, message, recids, identifier_type):
        HooverException.__init__(self, message)
        self.recids = tuple(recids)
        self.recid = recids[0]
        self.identifier_type = identifier_type

    def get_message_subject(self):
        """Return the subject of the message to be reported by the exception"""
        return '[Hoover] Found conflicting hepnames records'

    def get_message_body(self):
        """Return the body of the message to be reported by the exception"""
        msg = ['Found conflicting hepnames records: ']
        msg += ['%s/record/%s' % (CFG_SITE_URL, r) for r in self.recids]
        msg.append(
            'Those records are sharing the same %s identifier!' %
            self.identifier_type)
        # msg.append(self.message)
        return '\n'.join(msg)

    def hash(self):
        """Return the hash of the message to be reported by the exception"""
        return md5(self.__repr__() +
                   str(sorted(self.recids)) +
                   str(self.identifier_type)).hexdigest()
