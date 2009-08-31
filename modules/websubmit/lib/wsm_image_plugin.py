## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


"""
WebSubmit Metadata Plugin - This is a plugin to extract/update
metadata from images.

Dependencies: Exiv2
"""

try:
    import pyexiv2
    IMPORTED_PYEXIV_2 = True
except ImportError, e:
    IMPORTED_PYEXIV_2 = False


import httplib
import tempfile
from invenio.bibdocfile import decompose_file
import base64



def can_read_local(inputfile):
    """Checks if inputfile is among metadata-readable
    file types
    @param inputfile: (string) path to the image
    @type inputfile: string
    @rtype: boolean
    @return: true if extension casn be handled"""

    # Check file type (0 base,1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    return ext.lower() in ['.jpg', '.tiff', '.jpeg', 'jpe',
                           '.jfif', '.jfi', '.jif']


# can_read_remote()
def can_read_remote(inputfile):
    """Checks if inputfile is among metadata-readable
    file types
    @param inputfile: (string) path to the image
    @type inputfile: string
    @rtype: boolean
    @return: true if extension casn be handled"""

    # Check file type (0 base,1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    return ext.lower() in ['.jpg', '.jpeg', 'jpe',
                           '.jfif', '.jfi', '.jif']

# can_write_local()
def can_write_local(inputfile):
    """Checks if inputfile is among metadata-writable
    file types
    @param inputfile: (string) path to the image
    @type inputfile: string
    @rtype: boolean
    @return: true if extension casn be handled"""

    # Check file type (0 base,1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    return ext.lower() in ['.jpg', '.tiff', '.jpeg', 'jpe',
                           '.jfif', '.jfi', '.jif']


def install():
    """Asks the user to install the needed libraries in
    order to use this plugin
    """

    install_message = 'Packages to install -> libexiv2-5, python-pyexiv2\n'
    print install_message
    return

    #inst = raw_input('Proceed installing?  [y]es/[n]o : ')
    #if inst == 'y':
    #    os.system('sudo apt-get install libexiv2-5 python-pyexiv2')
    #    print '\nInstallation complete\n'
    #    return True
    #else:
    #    print '\nNot installing packages\n'
    #    return False



def extract_metadata(inputfile, verbose):
    """EXIF and IPTC metadata extraction and printing from images
       @param inputfile: path to the image
       @type inputfile: string
       @param verbose: verbosity
       @type verbose: int
       @rtype: dict (metadata_tag - (interpreted) value)
       @return: dictionary with metadata"""

    # Check that pyexiv2 has been imported/installed
    if not IMPORTED_PYEXIV_2:
        install()
        raise RuntimeError, 'Missing libraries'


    # Load the image
    image = pyexiv2.Image(inputfile)

    # Read the metadata
    image.readMetadata()

    image_info = {}

    # EXIF metadata store and print
    if verbose:
        print '\nEXIF Metadata Information\n'

    for key in image.exifKeys():
        image_info[key] = image.interpretedExifValue(key)
        if verbose:
            print key, ' -> ', image.interpretedExifValue(key)

    # IPTC metadata store and print
    if verbose:
        print '\nIPTC Metadata Information\n'
    for key in image.iptcKeys():
        image_info[key] = repr(image[key])
        if verbose:
            print key, ' -> ', repr(image[key])

    if verbose:
        print '\n'

    # Return the dictionary
    return image_info



def write_metadata(inputfile, verbose, metadata_dictionary):
    """EXIF and IPTC metadata writing, previous tag printing,
       to images. If some tag not set, it is auto-added, but
       be a valid exif or iptc tag.
       @param inputfile: path to the image
       @type inputfile: string
       @param verbose: verbosity
       @type verbose: int
       @param metadata_dictionary: metadata information to update inputfile
       @type verbose: dict
       """


    # Check that pyexiv2 has been imported/installed
    if not IMPORTED_PYEXIV_2:
        install()
        raise RuntimeError, 'Missing libraries'


    # Load the image
    image = pyexiv2.Image(inputfile)

    # Read the metadata
    image.readMetadata()

    # EXIF metadata tag
    if verbose:
        print '\nEXIF Metadata Tags\n'

    for key in image.exifKeys():
        if verbose:
            print key

    # IPTC metadata
    if verbose:
        print '\nIPTC Metadata Tags\n'

    for key in image.iptcKeys():
        if verbose:
            print key

    if verbose:
        print '\nMetadata dictionary:\n', metadata_dictionary
    # Main Case: Dictionary received through option -d
    if not metadata_dictionary == {}:
        for tag in metadata_dictionary:
            if tag in image.exifKeys() or tag in image.iptcKeys():
                old_value = image[tag]
                print 'Tag found'
            else:
                old_value = 'unset'
                print 'Tag not found'
            try:
                image[tag] = metadata_dictionary[tag]
                if verbose:
                    print 'Image[', tag, '] from <', old_value , \
                        '> to <', image[tag], '>\n'
                image.writeMetadata()
            except Exception:
                print 'Tag or Value incorrect\n'


    # Alternative way: User interaction
    else:
        user_input = 'user_input'
        while (user_input):
            user_input = raw_input('[w]rite / [q]uit\n')
            if user_input == 'q':
                break
            else:
                tag = raw_input('Tag? (Any valid Exif or Iptc Tag) ')
                value = raw_input('Value? ')
                if tag in image.exifKeys() or tag in image.iptcKeys():
                    old_value = image[tag]
                else:
                    old_value = 'unset'
                try:
                    image[tag] = value
                    if verbose:
                        print 'Image[', tag, '] from <', old_value , \
                            '> to <', image[tag], '>\n'
                    image.writeMetadata()
                except Exception:
                    print 'Tag or Value incorrect\n'



def extract_metadata_remote(inputfile, verbose, loginpw):
    """EXIF and IPTC metadata extraction and printing from
       remote images
       @param inputfile: path to the remote image
       @type inputfile: string
       @param verbose: verbosity
       @type verbose: int
       @param loginpw: user and password to access secure servers
       @type loginpw: string
       @rtype: dict (metadata_tag - (interpreted) value)
       @return: dictionary with metadata"""

    # Check that pyexiv2 has been imported/installed
    if not IMPORTED_PYEXIV_2:
        install()
        raise RuntimeError, 'Missing libraries'


    # Check that inputfile is an URL
    secure = False
    pos = inputfile.lower().find('http://')
    if pos < 0:
        secure = True
        pos = inputfile.lower().find('https://')
    if pos < 0:
        raise ValueError, "Inputfile (" + inputfile + ") is " + \
                          "not an URL, non remote resource.\n"


    # Check if there is login and password
    if loginpw != None:
        (userid, passwd) = loginpw.split(':')

    # Make HTTPS Connection
    domain = inputfile.split('/')[2]
    if verbose > 3:
        print 'Domain: ', domain
    url = inputfile.split(domain)[1]
    if verbose > 3:
        print 'URL: ', url


    # Establish headers
    if loginpw != None:
        _headers = { "Accept": "*/*",
             "Authorization": "Basic" + \
             " " + base64.encodestring(userid + ':' + passwd).strip() }
        if verbose > 3:
            print 'HEADER WITH AUTH'
    else:
        _headers = {"Accept": "*/*"}
        if verbose > 3:
            print 'HEADER WITH NO AUTH'

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
            print 'Could not connect\n'
    # Case HTTP
    else:
        try:
            conn = httplib.HTTPConnection(domain)
            ## Request a connection
            conn.request("GET", url,
                  headers = _headers)
        except Exception:
            # Cannot connect
            print 'Could not connect\n'

    # Get response
    response = conn.getresponse()

    # Read first marker from image
    data = response.read(2)

    # Check if it is a valid image
    if data[0:2] != '\xff\xd8':
        raise ValueError, "URL does not brings to a valid image file.\n"
    else:
        if verbose:
            print 'Valid JPEG Standard-based image\n'

    # Start the fake image
    path_to_fake = fake_image_init(verbose)

    # Continue reading
    data = response.read(2)

    # Check if we find metadata (EXIF or IPTC)
    while data[0:2] != '\xff\xdb':
        if data[0:2] == '\xff\xe1' or data[0:2] == '\xff\xed':
            marker = data
            if verbose:
                print 'Metadata Marker->', repr(marker), '\nGetting data\n'
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
    return extract_metadata(path_to_fake, verbose)


def fake_image_init(verbose):
    """Initializes the fake image
       @param verbose: verbosity
       @type verbose: int
       @rtype: string
       @return: path to fake image"""

    # Create temp file for fake image
    (fdesc, path_to_fake) = tempfile.mkstemp(prefix='websubmit_file_metadata_')

    if verbose > 6:
        print 'Writing head to fake image\n'
    # Open fake image and write head to it
    fake_image = open(path_to_fake, 'a')
    image_head = '\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00' + \
                 '\x01\x01\x01\x00\x48\x00\x48\x00\x00'
    fake_image.write(image_head)
    fake_image.close()

    return path_to_fake


def fake_image_close(path_to_fake, verbose):
    """Closes the fake image
       @param path_to_fake: path to the fake image
       @type path_to_fake: string
       @param verbose: verbosity
       @type verbose: int
       """

    if verbose > 6:
        print 'Writing no metadata info to fake image\n'
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

    return


def insert_metadata(path_to_fake, marker, size, meta, verbose):
    """Insert metadata into the fake image
       @param path_to_fake: path to the fake image
       @type path_to_fake: string
       @param marker: JPEG marker
       @type marker: string
       @param size: size of a JPEG block
       @type marker: string
       @param meta: metadata information
       @type marker: string
       """

    if verbose > 6:
        print 'Writing Metadata to fake image\n'
    # Metadata insertion
    fake_image = open(path_to_fake, 'a')
    fake_image.write(marker)
    fake_image.write(size)
    fake_image.write(meta)

    fake_image.close()


    return
