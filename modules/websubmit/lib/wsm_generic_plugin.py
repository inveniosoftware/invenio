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
WebSubmit Metadata Plugin - This is the generic metadata extraction
plugin. Contains methods to extract metadata from many kinds of files.

Dependencies: extractor
"""

try:
    import extractor
    IMPORTED_EXTRACTOR = True
except ImportError, e:
    IMPORTED_EXTRACTOR = False

from invenio.bibdocfile import decompose_file



def can_read_local(inputfile):
    """Checks if inputfile is among metadata-readable
    file types
    @param inputfile: (string) path to the image
    @type inputfile: string
    @rtype: boolean
    @return: true if extension casn be handled"""

    # Check file type (0 base,1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    return ext.lower() in ['.html', '.pdf', '.doc', '.ps', '.xls', '.ppt',
                           '.ps', '.sxw', '.sdw', '.dvi', '.man', '.flac',
                           '.mp3', '.nsf', '.sid', '.ogg', '.wav', '.png',
                           '.deb', '.rpm', '.tar.gz', '.zip', '.elf',
                           '.s3m', '.xm', '.it', '.flv', '.real', '.avi',
                           '.mpeg', '.qt', '.asf']


def install():
    """Asks the user to install the needed libraries in
    order to use this plugin
    """

    install_message = 'Packages to install -> ' + \
                      'libextractor1c2a, python-extractor\n'
    print install_message
    return

    #inst = raw_input('Proceed installing?  [y]es/[n]o : ')
    #if inst == 'y':
    #    os.system('sudo apt-get install libextractor1c2a python-extractor')
    #    print '\nInstallation complete\n'
    #    return True
    #else:
    #    print '\nNot installing packages\n'
    #    return False



def extract_metadata(inputfile, verbose):
    """Metadata extraction from many kind of files
       @param inputfile: path to the image
       @type inputfile: string
       @param verbose: verbosity
       @type verbose: int
       @rtype: dict (metadata_tag - (interpreted) value)
       @return: dictionary with metadata"""

    # Check that pyexiv2 has been imported/installed
    if not IMPORTED_EXTRACTOR:
        install()
        raise RuntimeError, 'Missing libraries'

    # Initialization dict
    meta_info = {}

    # Extraction
    xtract = extractor.Extractor()

    # Get the keywords
    keys = xtract.extract(inputfile)

    if verbose:
        print '\nMetadata in file '+inputfile+'\n'

    # Loop to print values and dump data to the dict
    for keyword_type, keyword in keys:
        if verbose:
            print "%s  ->  %s" % (keyword_type.encode('iso-8859-1'),
                                  keyword.encode('iso-8859-1'))
        meta_info[keyword_type.encode('iso-8859-1')] = \
            keyword.encode('iso-8859-1')

    # Return the dictionary
    return meta_info



