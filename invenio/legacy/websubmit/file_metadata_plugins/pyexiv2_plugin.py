# This file is part of Invenio.
# Copyright (C) 2010, 2011 CERN.
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
"""
WebSubmit Metadata Plugin - This is a plugin to extract/update
metadata from images.

from __future__ import print_function

Dependencies: Exiv2
"""

__plugin_version__ = "WebSubmit File Metadata Plugin API 1.0"

import os
import base64
import httplib
import tempfile
import shutil
import pyexiv2
from invenio.legacy.bibdocfile.api import decompose_file
from invenio.config import CFG_TMPDIR
from invenio.legacy.websubmit.config import InvenioWebSubmitFileMetadataRuntimeError

def can_read_local(inputfile):
    """
    Checks if inputfile is among metadata-readable file types

    @param inputfile: path to the image
    @type inputfile: string
    @rtype: boolean
    @return: True if file can be processed
    """
    # Check file type (0 base, 1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    return ext.lower() in ['.jpg', '.tiff', '.jpeg', 'jpe',
                           '.jfif', '.jfi', '.jif']

def can_read_remote(inputfile):
    """Checks if inputfile is among metadata-readable
    file types
    @param inputfile: (string) path to the image
    @type inputfile: string
    @rtype: boolean
    @return: true if extension casn be handled"""

    # Check file type (0 base, 1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    return ext.lower() in ['.jpg', '.jpeg', 'jpe',
                           '.jfif', '.jfi', '.jif']

def can_write_local(inputfile):
    """
    Checks if inputfile is among metadata-writable file types

    @param inputfile: path to the image
    @type inputfile: string
    @rtype: boolean
    @return: True if file can be processed
    """
    # Check file type (0 base, 1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    return ext.lower() in ['.jpg', '.tiff', '.jpeg', 'jpe',
                           '.jfif', '.jfi', '.jif']

def read_metadata_local(inputfile, verbose):
    """
    EXIF and IPTC metadata extraction and printing from images

    @param inputfile: path to the image
    @type inputfile: string
    @param verbose: verbosity
    @type verbose: int
    @rtype: dict
    @return: dictionary with metadata
    """
    # Load the image
    image = pyexiv2.Image(inputfile)

    # Read the metadata
    image.readMetadata()

    image_info = {}

    # EXIF metadata
    for key in image.exifKeys():
        image_info[key] = image.interpretedExifValue(key)

    # IPTC metadata
    for key in image.iptcKeys():
        image_info[key] = repr(image[key])

    # Return the dictionary
    return image_info

def write_metadata_local(inputfile, outputfile, metadata_dictionary, verbose):
    """
    EXIF and IPTC metadata writing, previous tag printing, to
    images. If some tag not set, it is auto-added, but be a valid exif
    or iptc tag.

    @param inputfile: path to the image
    @type inputfile: string
    @param outputfile: path to the resulting image
    @type outputfile: string
    @param verbose: verbosity
    @type verbose: int
    @param metadata_dictionary: metadata information to update inputfile
    @rtype: dict
    """
    if inputfile != outputfile:
        # Create copy of inputfile
        try:
            shutil.copy2(inputfile, outputfile)
        except Exception as err:
            raise InvenioWebSubmitFileMetadataRuntimeError(err)

    # Load the image
    image = pyexiv2.Image(inputfile)

    # Read the metadata
    image.readMetadata()

    # Main Case: Dictionary received through option -d
    if metadata_dictionary:
        for tag in metadata_dictionary:
            if tag in image.exifKeys() or tag in image.iptcKeys():
                # Updating
                if verbose > 0:
                    print("Updating %(tag)s from <%(old_value)s> to <%(new_value)s>" % \
                          {'tag': tag,
                           'old_value': image[tag],
                           'new_value': metadata_dictionary[tag]})
            else:
                # Adding
                if verbose > 0:
                    print("Adding %(tag)s with value <%(new_value)s>" % \
                          {'tag': tag,
                           'new_value': metadata_dictionary[tag]})
            try:
                image[tag] = metadata_dictionary[tag]
                image.writeMetadata()
            except Exception:
                print('Tag or Value incorrect')

    # Alternative way: User interaction
    else:
        data_modified = False
        user_input = 'user_input'
        print("Entering interactive mode. Choose what you want to do:")
        while (user_input):
            if not data_modified:
                try:
                    user_input = raw_input('[w]rite / [q]uit\n')
                except:
                    print("Aborting")
                    return
            else:
                try:
                    user_input = raw_input('[w]rite / [q]uit and apply / [a]bort \n')
                except:
                    print("Aborting")
                    return

            if user_input == 'q':
                if not data_modified:
                    return
                break
            elif user_input == 'w':
                try:
                    tag = raw_input('Tag to update (Any valid Exif or Iptc Tag):\n')
                    value = raw_input('With value:\n')
                    data_modified = True
                except:
                    print("Aborting")
                    return
                try:
                    image[tag] = value
                except Exception as err:
                    print('Tag or Value incorrect')
            elif user_input == 'a':
                return
            else:
                print("Invalid option: ")
        try:
            image.writeMetadata()
        except Exception as err:
            raise InvenioWebSubmitFileMetadataRuntimeError("Could not update metadata: " + err)

def read_metadata_remote(inputfile, loginpw, verbose):
    """
    EXIF and IPTC metadata extraction and printing from remote images

    @param inputfile: path to the remote image
    @type inputfile: string
    @param verbose: verbosity
    @type verbose: int
    @param loginpw: credentials to access secure servers (username:password)
    @type loginpw: string
    @return: dictionary with metadata
    @rtype: dict
    """
    # Check that inputfile is an URL
    secure = False
    pos = inputfile.lower().find('http://')
    if pos < 0:
        secure = True
        pos = inputfile.lower().find('https://')
    if pos < 0:
        raise InvenioWebSubmitFileMetadataRuntimeError("Inputfile (" + inputfile + ") is " + \
                                                       "not an URL, nor remote resource.")

    # Check if there is login and password
    if loginpw != None:
        (userid, passwd) = loginpw.split(':')

    # Make HTTPS Connection
    domain = inputfile.split('/')[2]
    if verbose > 3:
        print('Domain: ', domain)
    url = inputfile.split(domain)[1]
    if verbose > 3:
        print('URL: ', url)

    # Establish headers
    if loginpw != None:
        _headers = {"Accept": "*/*",
                    "Authorization": "Basic " + \
                    base64.encodestring(userid + ':' + passwd).strip()}
    else:
        _headers = {"Accept": "*/*"}

    conn = None

    # Establish connection
    # Case HTTPS
    if secure:
        try:
            conn = httplib.HTTPSConnection(domain)
            ## Request a connection
            conn.request("GET", url,
                  headers = _headers)
        except Exception:
            # Cannot connect
            print('Could not connect')
    # Case HTTP
    else:
        try:
            conn = httplib.HTTPConnection(domain)
            ## Request a connection
            conn.request("GET", url,
                  headers = _headers)
        except Exception:
            # Cannot connect
            print('Could not connect')

    # Get response
    if verbose > 5:
        print("Fetching data from remote server.")
    response = conn.getresponse()
    if verbose > 2:
        print(response.status, response.reason)

    if response.status == 401:
        # Authentication required
        raise InvenioWebSubmitFileMetadataRuntimeError("URL requires authentication. Use --loginpw option")

    # Read first marker from image
    data = response.read(2)

    # Check if it is a valid image
    if data[0:2] != '\xff\xd8':
        raise InvenioWebSubmitFileMetadataRuntimeError("URL does not brings to a valid image file.")
    else:
        if verbose > 5:
            print('Valid JPEG Standard-based image')

    # Start the fake image
    path_to_fake = fake_image_init(verbose)

    # Continue reading
    data = response.read(2)

    # Check if we find metadata (EXIF or IPTC)
    while data[0:2] != '\xff\xdb':
        if data[0:2] == '\xff\xe1' or data[0:2] == '\xff\xed':
            marker = data
            if verbose > 5:
                print('Metadata Marker->', repr(marker), '\nGetting data')
            size = response.read(2)
            length = ord(size[0]) * 256 + ord(size[1])
            meta = response.read(length-2)
            insert_metadata(path_to_fake, marker, size, meta, verbose)
            break
        else:
            data = response.read(2)

    # Close connection
    conn.close()

    # Close fake image
    fake_image_close(path_to_fake, verbose)

    # Extract metadata once fake image is done
    return read_metadata_local(path_to_fake, verbose)

def fake_image_init(verbose):
    """
    Initializes the fake image

    @param verbose: verbosity
    @type verbose: int
    @rtype: string
    @return: path to fake image
    """
    # Create temp file for fake image
    (fd, path_to_fake) = tempfile.mkstemp(prefix='wsm_image_plugin_img_',
                                             dir=CFG_TMPDIR)
    os.close(fd)

    # Open fake image and write head to it
    fake_image = open(path_to_fake, 'a')
    image_head = '\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00' + \
                 '\x01\x01\x01\x00\x48\x00\x48\x00\x00'
    fake_image.write(image_head)
    fake_image.close()

    return path_to_fake

def fake_image_close(path_to_fake, verbose):
    """
    Closes the fake image

    @param path_to_fake: path to the fake image
    @type path_to_fake: string
    @param verbose: verbosity
    @type verbose: int
    """
    # Open fake image and write image structure info
    # (Huffman table[s]...) to it
    fake_image = open(path_to_fake, 'a')

    image_tail = '\xff\xdb\x00\x43\x00\x05\x03\x04\x04\x04\x03\x05' + \
                 '\x04\x04\x04\x05\x05\x05\x06\x07\x0c\x08\x07\x07' + \
                 '\x07\x07\x0f\x0b\x0b\x09\x0c\x11\x0f\x12\x12\x11' + \
                 '\x0f\x11\x11\x13\x16\x1c\x17\x13\x14\x1a\x15\x11' + \
                 '\x11\x18\x21\x18\x1a\x1d\x1d\x1f\x1f\x1f\x13\x17' + \
                 '\x22\x24\x22\x1e\x24\x1c\x1e\x1f\x1e\xff\xdb\x00' + \
                 '\x43\x01\x05\x05\x05\x07\x06\x07\x0e\x08\x08\x0e' + \
                 '\x1e\x14\x11\x14\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e' + \
                 '\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e' + \
                 '\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e' + \
                 '\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e\x1e' + \
                 '\x1e\x1e\x1e\x1e\x1e\x1e\xff\xc0\x00\x11\x08\x00' + \
                 '\x01\x00\x01\x03\x01\x22\x00\x02\x11\x01\x03\x11' + \
                 '\x01\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00' + \
                 '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08' + \
                 '\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00' + \
                 '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4' + \
                 '\x00\x14\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00' + \
                 '\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x14' + \
                 '\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + \
                 '\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01' + \
                 '\x00\x02\x11\x03\x11\x00\x3f\x00\xb2\xc0\x07\xff\xd9'
    fake_image.write(image_tail)
    fake_image.close()

def insert_metadata(path_to_fake, marker, size, meta, verbose):
    """
    Insert metadata into the fake image

    @param path_to_fake: path to the fake image
    @type path_to_fake: string
    @param marker: JPEG marker
    @type marker: string
    @param size: size of a JPEG block
    @type size: string
    @param meta: metadata information
    @type meta: string
    """
    # Metadata insertion
    fake_image = open(path_to_fake, 'a')
    fake_image.write(marker)
    fake_image.write(size)
    fake_image.write(meta)
    fake_image.close()
