# -*- coding: utf-8 -*-
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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

"""
mod_python->WSGI Framework utilities

This code has been taken from mod_python original source code and rearranged
here to easying the migration from mod_python to wsgi.

The code taken from mod_python is under the following License.
"""

 # Copyright 2004 Apache Software Foundation
 #
 # Licensed under the Apache License, Version 2.0 (the "License"); you
 # may not use this file except in compliance with the License.  You
 # may obtain a copy of the License at
 #
 #      http://www.apache.org/licenses/LICENSE-2.0
 #
 # Unless required by applicable law or agreed to in writing, software
 # distributed under the License is distributed on an "AS IS" BASIS,
 # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
 # implied.  See the License for the specific language governing
 # permissions and limitations under the License.
 #
 # Originally developed by Gregory Trubetskoy.
 #
 # $Id: apache.py 468216 2006-10-27 00:54:12Z grahamd $

from wsgiref.headers import Headers
import time
import re
import os
import cgi
import cStringIO
import tempfile
from types import TypeType, ClassType, BuiltinFunctionType, MethodType, ListType
from invenio.config import CFG_TMPDIR, CFG_TMPSHAREDDIR
from invenio.webinterface_handler_config import \
    SERVER_RETURN, \
    HTTP_LENGTH_REQUIRED, \
    HTTP_BAD_REQUEST, \
    InvenioWebInterfaceWSGIContentLenghtError, \
    InvenioWebInterfaceWSGIContentTypeError, \
    InvenioWebInterfaceWSGIContentMD5Error

class table(Headers):
    add = Headers.add_header
    iteritems = Headers.items
    def __getitem__(self, name):
        ret = Headers.__getitem__(self, name)
        if ret is None:
            return ''
        else:
            return str(ret)


## Some functions made public
exists_config_define = lambda dummy: True

## Some constants


class metaCookie(type):

    def __new__(cls, clsname, bases, clsdict):

        _valid_attr = (
            "version", "path", "domain", "secure",
            "comment", "expires", "max_age",
            # RFC 2965
            "commentURL", "discard", "port",
            # Microsoft Extension
            "httponly" )

        # _valid_attr + property values
        # (note __slots__ is a new Python feature, it
        # prevents any other attribute from being set)
        __slots__ = _valid_attr + ("name", "value", "_value",
                                   "_expires", "__data__")

        clsdict["_valid_attr"] = _valid_attr
        clsdict["__slots__"] = __slots__

        def set_expires(self, value):

            if type(value) == type(""):
                # if it's a string, it should be
                # valid format as per Netscape spec
                try:
                    t = time.strptime(value, "%a, %d-%b-%Y %H:%M:%S GMT")
                except ValueError:
                    raise ValueError, "Invalid expires time: %s" % value
                t = time.mktime(t)
            else:
                # otherwise assume it's a number
                # representing time as from time.time()
                t = value
                value = time.strftime("%a, %d-%b-%Y %H:%M:%S GMT",
                                      time.gmtime(t))

            self._expires = "%s" % value

        def get_expires(self):
            return self._expires

        clsdict["expires"] = property(fget=get_expires, fset=set_expires)

        return type.__new__(cls, clsname, bases, clsdict)

class Cookie(object):
    """
    This class implements the basic Cookie functionality. Note that
    unlike the Python Standard Library Cookie class, this class represents
    a single cookie (not a list of Morsels).
    """

    __metaclass__ = metaCookie

    DOWNGRADE = 0
    IGNORE = 1
    EXCEPTION = 3

    def parse(Class, str, **kw):
        """
        Parse a Cookie or Set-Cookie header value, and return
        a dict of Cookies. Note: the string should NOT include the
        header name, only the value.
        """

        dict = _parse_cookie(str, Class, **kw)
        return dict

    parse = classmethod(parse)

    def __init__(self, name, value, **kw):

        """
        This constructor takes at least a name and value as the
        arguments, as well as optionally any of allowed cookie attributes
        as defined in the existing cookie standards.
        """
        self.name, self.value = name, value

        for k in kw:
            setattr(self, k.lower(), kw[k])

        # subclasses can use this for internal stuff
        self.__data__ = {}


    def __str__(self):

        """
        Provides the string representation of the Cookie suitable for
        sending to the browser. Note that the actual header name will
        not be part of the string.

        This method makes no attempt to automatically double-quote
        strings that contain special characters, even though the RFC's
        dictate this. This is because doing so seems to confuse most
        browsers out there.
        """

        result = ["%s=%s" % (self.name, self.value)]
        # pylint: disable=E1101
        # The attribute _valid_attr is provided by the metaclass 'metaCookie'.
        for name in self._valid_attr:
            if hasattr(self, name):
                if name in ("secure", "discard", "httponly"):
                    result.append(name)
                else:
                    result.append("%s=%s" % (name, getattr(self, name)))
        # pylint: enable=E1101
        return "; ".join(result)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__,
                                str(self))

# This is a simplified and in some places corrected
# (at least I think it is) pattern from standard lib Cookie.py

_cookiePattern = re.compile(
    r"(?x)"                       # Verbose pattern
    r"[,\ ]*"                        # space/comma (RFC2616 4.2) before attr-val is eaten
    r"(?P<key>"                   # Start of group 'key'
    r"[^;\ =]+"                     # anything but ';', ' ' or '='
    r")"                          # End of group 'key'
    r"\ *(=\ *)?"                 # a space, then may be "=", more space
    r"(?P<val>"                   # Start of group 'val'
    r'"(?:[^\\"]|\\.)*"'            # a doublequoted string
    r"|"                            # or
    r"[^;]*"                        # any word or empty string
    r")"                          # End of group 'val'
    r"\s*;?"                      # probably ending in a semi-colon
    )

def _parse_cookie(str, Class, names=None):
    # XXX problem is we should allow duplicate
    # strings
    result = {}

    matchIter = _cookiePattern.finditer(str)

    for match in matchIter:
        key, val = match.group("key"), match.group("val")

        # We just ditch the cookies names which start with a dollar sign since
        # those are in fact RFC2965 cookies attributes. See bug [#MODPYTHON-3].
        if key[0] != '$' and names is None or key in names:
            result[key] = Class(key, val)

    return result


def get_cookies(req, cls=Cookie, **kw):
    """
    A shorthand for retrieveing and parsing cookies given
    a Cookie class. The class must be one of the classes from
    this module.
    """
    if not "cookie" in getattr(req, "headers_in", {}):
        return {}

    cookies = req.headers_in["cookie"]
    if isinstance(cookies, list):
        cookies = '; '.join(cookies)

    return cls.parse(cookies, **kw)


def get_cookie(req, name, cls=Cookie, **kw):
    cookies = get_cookies(req, cls, names=[name], **kw)
    if name in cookies:
        return cookies[name]


parse_qs = cgi.parse_qs
parse_qsl = cgi.parse_qsl

# Maximum line length for reading. (64KB)
# Fixes memory error when upload large files such as 700+MB ISOs.
readBlockSize = 65368

""" The classes below are a (almost) a drop-in replacement for the
    standard cgi.py FieldStorage class. They should have pretty much the
    same functionality.

    These classes differ in that unlike cgi.FieldStorage, they are not
    recursive. The class FieldStorage contains a list of instances of
    Field class. Field class is incapable of storing anything in it.

    These objects should be considerably faster than the ones in cgi.py
    because they do not expect CGI environment, and are
    optimized specifically for Apache and mod_python.
"""

class Field:
    def __init__(self, name, *args, **kwargs):
        self.name = name

        # Some third party packages such as Trac create
        # instances of the Field object and insert it
        # directly into the list of form fields. To
        # maintain backward compatibility check for
        # where more than just a field name is supplied
        # and invoke an additional initialisation step
        # to process the arguments. Ideally, third party
        # code should use the add_field() method of the
        # form, but if they need to maintain backward
        # compatibility with older versions of mod_python
        # they will not have a choice but to use old
        # way of doing things and thus we need this code
        # for the forseeable future to cope with that.

        if args or kwargs:
            self.__bc_init__(*args, **kwargs)

    def __bc_init__(self, file, ctype, type_options,
                    disp, disp_options, headers = {}):
        self.file = file
        self.type = ctype
        self.type_options = type_options
        self.disposition = disp
        self.disposition_options = disp_options
        if disp_options.has_key("filename"):
            self.filename = disp_options["filename"]
        else:
            self.filename = None
        self.headers = headers

    def __repr__(self):
        """Return printable representation."""
        return "Field(%s, %s)" % (`self.name`, `self.value`)

    def __getattr__(self, name):
        if name != 'value':
            raise AttributeError, name
        if self.file:
            self.file.seek(0)
            value = self.file.read()
            self.file.seek(0)
        else:
            value = None
        return value

    def __del__(self):
        self.file.close()

class StringField(str):
    """ This class is basically a string with
    added attributes for compatibility with std lib cgi.py. Basically, this
    works the opposite of Field, as it stores its data in a string, but creates
    a file on demand. Field creates a value on demand and stores data in a file.
    """
    filename = None
    headers = {}
    ctype = "text/plain"
    type_options = {}
    disposition = None
    disp_options = None

    def __new__(cls, value):
        '''Create StringField instance. You'll have to set name yourself.'''
        obj = str.__new__(cls, value)
        obj.value = value
        return obj

    def __str__(self):
        return str.__str__(self)

    def __getattr__(self, name):
        if name != 'file':
            raise AttributeError, name
        self.file = cStringIO.StringIO(self.value)
        return self.file

    def __repr__(self):
        """Return printable representation (to pass unit tests)."""
        return "Field(%s, %s)" % (`self.name`, `self.value`)

class FieldList(list):

    def __init__(self):
        self.__table = None
        list.__init__(self)

    def table(self):
        if self.__table is None:
            self.__table = {}
            for item in self:
                if item.name in self.__table:
                    self.__table[item.name].append(item)
                else:
                    self.__table[item.name] = [item]
        return self.__table

    def __delitem__(self, *args):
        self.__table = None
        return list.__delitem__(self, *args)

    def __delslice__(self, *args):
        self.__table = None
        return list.__delslice__(self, *args)

    def __iadd__(self, *args):
        self.__table = None
        return list.__iadd__(self, *args)

    def __imul__(self, *args):
        self.__table = None
        return list.__imul__(self, *args)

    def __setitem__(self, *args):
        self.__table = None
        return list.__setitem__(self, *args)

    def __setslice__(self, *args):
        self.__table = None
        return list.__setslice__(self, *args)

    def append(self, *args):
        self.__table = None
        return list.append(self, *args)

    def extend(self, *args):
        self.__table = None
        return list.extend(self, *args)

    def insert(self, *args):
        self.__table = None
        return list.insert(self, *args)

    def pop(self, *args):
        self.__table = None
        return list.pop(self, *args)

    def remove(self, *args):
        self.__table = None
        return list.remove(self, *args)


class FieldStorage:

    def __init__(self, req, keep_blank_values=0, strict_parsing=0, file_callback=None, field_callback=None, to_tmp_shared=False):
        #
        # Whenever readline is called ALWAYS use the max size EVEN when
        # not expecting a long line. - this helps protect against
        # malformed content from exhausting memory.
        #

        self.list = FieldList()
        self.wsgi_input_consumed = False

        # always process GET-style parameters
        if req.args:
            pairs = parse_qsl(req.args, keep_blank_values)
            for pair in pairs:
                self.add_field(pair[0], pair[1])
        if req.method != "POST":
            return

        try:
            clen = int(req.headers_in["content-length"])
        except (KeyError, ValueError):
            # absent content-length is not acceptable
            raise SERVER_RETURN, HTTP_LENGTH_REQUIRED

        self.clen = clen
        self.count = 0
        if not req.headers_in.has_key("content-type"):
            ctype = "application/x-www-form-urlencoded"
        else:
            ctype = req.headers_in["content-type"]

        if ctype.startswith("application/x-www-form-urlencoded"):
            pairs = parse_qsl(req.read(clen), keep_blank_values)
            self.wsgi_input_consumed = True
            for pair in pairs:
                self.add_field(pair[0], pair[1])
            return
        elif not ctype.startswith("multipart/"):
            # we don't understand this content-type
            return
        self.wsgi_input_consumed = True

        # figure out boundary
        try:
            i = ctype.lower().rindex("boundary=")
            boundary = ctype[i+9:]
            if len(boundary) >= 2 and boundary[0] == boundary[-1] == '"':
                boundary = boundary[1:-1]
            boundary = re.compile("--" + re.escape(boundary) + "(--)?\r?\n")

        except ValueError:
            raise SERVER_RETURN, HTTP_BAD_REQUEST

        # read until boundary
        self.read_to_boundary(req, boundary, None)

        end_of_stream = False
        while not end_of_stream and not self.eof(): # jjj JIM BEGIN WHILE
            ## parse headers

            ctype, type_options = "text/plain", {}
            disp, disp_options = None, {}
            headers = table([])
            line = req.readline(readBlockSize)
            self.count += len(line)
            if self.eof():
                end_of_stream = True
            match = boundary.match(line)
            if (not line) or match:
                # we stop if we reached the end of the stream or a stop
                # boundary (which means '--' after the boundary) we
                # continue to the next part if we reached a simple
                # boundary in either case this would mean the entity is
                # malformed, but we're tolerating it anyway.
                end_of_stream = (not line) or (match.group(1) is not None)
                continue

            skip_this_part = False
            while line not in ('\r','\r\n'):
                nextline = req.readline(readBlockSize)
                self.count += len(nextline)
                if self.eof():
                    end_of_stream = True
                while nextline and nextline[0] in [ ' ', '\t']:
                    line = line + nextline
                    nextline = req.readline(readBlockSize)
                    self.count += len(nextline)
                    if self.eof():
                        end_of_stream = True
                # we read the headers until we reach an empty line
                # NOTE : a single \n would mean the entity is malformed, but
                # we're tolerating it anyway. We just raise an apache exception
                try:
                    h, v = line.split(":", 1)
                except ValueError:
                    raise SERVER_RETURN(HTTP_BAD_REQUEST)
                headers.add(h, v)
                h = h.lower()
                if h == "content-disposition":
                    disp, disp_options = parse_header(v)
                elif h == "content-type":
                    ctype, type_options = parse_header(v)
                    #
                    # NOTE: FIX up binary rubbish sent as content type
                    # from Microsoft IE 6.0 when sending a file which
                    # does not have a suffix.
                    #
                    if ctype.find('/') == -1:
                        ctype = 'application/octet-stream'

                line = nextline
                match = boundary.match(line)
                if (not line) or match:
                    # we stop if we reached the end of the stream or a
                    # stop boundary (which means '--' after the
                    # boundary) we continue to the next part if we
                    # reached a simple boundary in either case this
                    # would mean the entity is malformed, but we're
                    # tolerating it anyway.
                    skip_this_part = True
                    end_of_stream = (not line) or (match.group(1) is not None)
                    break

            if skip_this_part:
                continue

            if disp_options.has_key("name"):
                name = disp_options["name"]
            else:
                name = None

            # create a file object
            # is this a file?
            if disp_options.has_key("filename"):
                if file_callback and callable(file_callback):
                    file = file_callback(disp_options["filename"])
                else:
                    if to_tmp_shared:
                        file = tempfile.NamedTemporaryFile(dir=CFG_TMPSHAREDDIR)
                    else:
                        file = tempfile.NamedTemporaryFile(dir=CFG_TMPDIR)
            else:
                if field_callback and callable(field_callback):
                    file = field_callback()
                else:
                    file = cStringIO.StringIO()

            # read it in
            self.read_to_boundary(req, boundary, file)
            if self.eof():
                end_of_stream = True
            file.seek(0)

            # make a Field
            if disp_options.has_key("filename"):
                field = Field(name)
                field.filename = disp_options["filename"]
            else:
                field = StringField(file.read())
                field.name = name
            field.file = file
            field.type = ctype
            field.type_options = type_options
            field.disposition = disp
            field.disposition_options = disp_options
            field.headers = headers
            self.list.append(field)

    def add_field(self, key, value):
        """Insert a field as key/value pair"""
        item = StringField(value)
        item.name = key
        self.list.append(item)

    def __setitem__(self, key, value):
        table = self.list.table()
        if table.has_key(key):
            items = table[key]
            for item in items:
                self.list.remove(item)
        item = StringField(value)
        item.name = key
        self.list.append(item)

    def read_to_boundary(self, req, boundary, file):
        previous_delimiter = None
        while not self.eof():
            line = req.readline(readBlockSize)
            self.count += len(line)

            if not line:
                # end of stream
                if file is not None and previous_delimiter is not None:
                    file.write(previous_delimiter)
                return True

            match = boundary.match(line)
            if match:
                # the line is the boundary, so we bail out
                # if the two last chars are '--' it is the end of the entity
                return match.group(1) is not None

            if line[-2:] == '\r\n':
                # the line ends with a \r\n, which COULD be part
                # of the next boundary. We write the previous line delimiter
                # then we write the line without \r\n and save it for the next
                # iteration if it was not part of the boundary
                if file is not None:
                    if previous_delimiter is not None: file.write(previous_delimiter)
                    file.write(line[:-2])
                previous_delimiter = '\r\n'

            elif line[-1:] == '\r':
                # the line ends with \r, which is only possible if
                # readBlockSize bytes have been read. In that case the
                # \r COULD be part of the next boundary, so we save it
                # for the next iteration
                assert len(line) == readBlockSize
                if file is not None:
                    if previous_delimiter is not None: file.write(previous_delimiter)
                    file.write(line[:-1])
                previous_delimiter = '\r'

            elif line == '\n' and previous_delimiter == '\r':
                # the line us a single \n and we were in the middle of a \r\n,
                # so we complete the delimiter
                previous_delimiter = '\r\n'

            else:
                if file is not None:
                    if previous_delimiter is not None: file.write(previous_delimiter)
                    file.write(line)
                previous_delimiter = None

    def eof(self):
        return self.clen <= self.count

    def __getitem__(self, key):
        """Dictionary style indexing."""
        found = self.list.table()[key]
        if len(found) == 1:
            return found[0]
        else:
            return found

    def get(self, key, default):
        try:
            return self.__getitem__(key)
        except (TypeError, KeyError):
            return default

    def keys(self):
        """Dictionary style keys() method."""
        return self.list.table().keys()

    def __iter__(self):
        return iter(self.keys())

    def __repr__(self):
        return repr(self.list.table())

    def has_key(self, key):
        """Dictionary style has_key() method."""
        return (key in self.list.table())

    __contains__ = has_key

    def __len__(self):
        """Dictionary style len(x) support."""
        return len(self.list.table())

    def getfirst(self, key, default=None):
        """ return the first value received """
        try:
            return self.list.table()[key][0]
        except KeyError:
            return default

    def getlist(self, key):
        """ return a list of received values """
        try:
            return self.list.table()[key]
        except KeyError:
            return []

    def items(self):
        """Dictionary-style items(), except that items are returned in the same
        order as they were supplied in the form."""
        return [(item.name, item) for item in self.list]

    def __delitem__(self, key):
        table = self.list.table()
        values = table[key]
        for value in values:
            self.list.remove(value)

    def clear(self):
        self.list = FieldList()


def parse_header(line):
    """Parse a Content-type like header.

    Return the main content-type and a dictionary of options.

    """

    plist = map(lambda a: a.strip(), line.split(';'))
    key = plist[0].lower()
    del plist[0]
    pdict = {}
    for p in plist:
        i = p.find('=')
        if i >= 0:
            name = p[:i].strip().lower()
            value = p[i+1:].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
            pdict[name] = value
    return key, pdict

def apply_fs_data(object, fs, **args):
    """
    Apply FieldStorage data to an object - the object must be
    callable. Examine the args, and match then with fs data,
    then call the object, return the result.
    """

    # we need to weed out unexpected keyword arguments
    # and for that we need to get a list of them. There
    # are a few options for callable objects here:

    fc = None
    expected = []
    if hasattr(object, "func_code"):
        # function
        fc = object.func_code
        expected = fc.co_varnames[0:fc.co_argcount]
    elif hasattr(object, 'im_func'):
        # method
        fc = object.im_func.func_code
        expected = fc.co_varnames[1:fc.co_argcount]
    elif type(object) in (TypeType,ClassType):
        # class
        fc = object.__init__.im_func.func_code
        expected = fc.co_varnames[1:fc.co_argcount]
    elif type(object) is BuiltinFunctionType:
        # builtin
        fc = None
        expected = []
    elif hasattr(object, '__call__'):
        # callable object
        if type(object.__call__) is MethodType:
            fc = object.__call__.im_func.func_code
            expected = fc.co_varnames[1:fc.co_argcount]
        else:
            # abuse of objects to create hierarchy
            return apply_fs_data(object.__call__, fs, **args)

    # add form data to args
    for field in fs.list:
        if field.filename:
            val = field
        else:
            val = field.value
        args.setdefault(field.name, []).append(val)

    # replace lists with single values
    for arg in args:
        if ((type(args[arg]) is ListType) and
            (len(args[arg]) == 1)):
            args[arg] = args[arg][0]

    # remove unexpected args unless co_flags & 0x08,
    # meaning function accepts **kw syntax
    if fc is None:
        args = {}
    elif not (fc.co_flags & 0x08):
        for name in args.keys():
            if name not in expected:
                del args[name]

    return object(**args)

RE_CDISPOSITION_FILENAME = re.compile(r'filename=(?P<filename>[\w\.]*)')
def handle_file_post(req, allowed_mimetypes=None):
    """
    Handle the POST of a file.
    @return: the a tuple with the full path to the file saved on disk,
    and it's mimetype as provided by the request.
    @rtype: (string, string)
    """
    from invenio.bibdocfile import decompose_file, md5
    ## We retrieve the length
    clen = req.headers_in["Content-Length"]
    if clen is None:
        raise InvenioWebInterfaceWSGIContentLenghtError("Content-Length header is missing")
    try:
        clen = int(clen)
        assert (clen > 1)
    except (ValueError, AssertionError):
        raise InvenioWebInterfaceWSGIContentLenghtError("Content-Length header should contain a positive integer")
    ## Let's take the content type
    ctype = req.headers_in["Content-Type"]
    if allowed_mimetypes and ctype not in allowed_mimetypes:
        raise InvenioWebInterfaceWSGIContentTypeError("Content-Type not in allowed list of content types: %s" % allowed_mimetypes)
    ## Let's optionally accept a suggested filename
    suffix = prefix = ''
    g = RE_CDISPOSITION_FILENAME.search(req.headers_in.get("Content-Disposition", ""))
    if g:
        dummy, prefix, suffix = decompose_file(g.group("filename"))
    ## Let's optionally accept an MD5 hash (and use it later for comparison)
    cmd5 = req.headers_in["Content-MD5"]
    if cmd5:
        the_md5 = md5()

    ## Ok. We can initialize the file
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=CFG_TMPDIR)
    the_file = os.fdopen(fd, 'w')
    ## Let's read the file
    while True:
        chunk = req.read(min(10240, clen))
        if len(chunk) < min(10240, clen):
            ## We expected to read at least clen (which is different than 0)
            ## but chunk was shorter! Gosh! Error! Panic!
            the_file.close()
            os.close(fd)
            os.remove(path)
            raise InvenioWebInterfaceWSGIContentLenghtError("File shorter than what specified in Content-Length")
        if cmd5:
            ## MD5 was in the header let's compute it
            the_md5.update(chunk)
        ## And let's definitively write the content to disk :-)
        the_file.write(chunk)
        clen -= len(chunk)
        if clen == 0:
            ## That's it. Everything was read.
            break
    if cmd5 and the_md5.hexdigest().lower() != cmd5.strip().lower():
        ## Let's check the MD5
        the_file.close()
        os.close(fd)
        os.remove(path)
        raise InvenioWebInterfaceWSGIContentMD5Error("MD5 checksum does not match")
    ## Let's clean everything up
    the_file.close()
    return (path, ctype)
