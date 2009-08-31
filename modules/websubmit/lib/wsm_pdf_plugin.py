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
WebSubmit Metadata Plugin - This is the plugin to update metadata from
PDF files.

Dependencies: pdftk
"""

import os
from invenio.bibdocfile import decompose_file


def can_write_local(inputfile):
    """Checks if inputfile is among metadata-writable
       file types (pdf)
    @param inputfile: (string) path to the image
    @type inputfile: string
    @rtype: boolean
    @return: true if extension casn be handled"""

    ext = os.path.splitext(inputfile)[1]
    return ext.lower() in ['.pdf']


def install():
    """Asks the user to install the needed tool in
       order to use this plugin
    """

    install_message = 'Installation of needed packages -> pdftk\n'
    print install_message
    return

    #inst = raw_input('Proceed installing?  [y]es/[n]o : ')
    #if inst == 'y':
    #    os.system('sudo apt-get install pdftk')
    #    print '\nInstallation complete\n'
    #    return True
    #else:
    #    print '\nNot installing packages\n'
    #    return False



def write_metadata(inputfile, verbose, metadata_dictionary):
    """Metadata write method, takes the .pdf as input
       and creates a new one with the new info.
       @param inputfile: path to the pdf
       @type inputfile: string
       @param verbose: verbosity
       @type verbose: int
       @param metadata_dictionary: metadata information to update inputfile
       @type verbose: dict
       """

    # Take the file name (0 base,1 name, 2 ext)
    filename = decompose_file(inputfile)[1]



    status = os.system('which pdftk')
    if status != 0:
        install()
        raise RuntimeError, 'Missing PDFTK\n'

    # Print pdf metadata
    if verbose:
        print 'Metadata information in the PDF file '+filename+': \n'
        try:
            os.system('sudo pdftk '+inputfile+' dump_data')
        except Exception:
            print 'Problem with inputfile to PDFTK\n'

    # Info file for pdftk
    file_in = open('/opt/cds-invenio/var/tmp/in.info', 'w')

    # User interaction to form the info file
    # Main Case: Dictionary received through option -d
    if not metadata_dictionary == {}:
        for tag in metadata_dictionary:
            line = 'InfoKey: '+tag+'\nInfoValue '+metadata_dictionary[tag]+'\n'
            if verbose:
                print line
            file_in.writelines(line)
    else:
        user_input = 'user_input'
        while (user_input):
            user_input = raw_input('[w]rite / [q]uit\n')
            if user_input == 'q':
                break
            else:
                tag = raw_input('Tag? (Among shown InfoKey) \n')
                value = raw_input('Value? \n')
                # Write to info file
                line = 'InfoKey: '+tag+'\nInfoValue: '+value+'\n'
                if verbose:
                    print line
                file_in.writelines(line)

    file_in.close()

    # Now we call pdftk tool to update the info on a pdf
    try:
        os.system('sudo pdftk '+inputfile+' update_info ' + \
                  '/opt/cds-invenio/var/tmp/in.info output ' + \
                  '/opt/cds-invenio/var/tmp/'+filename+'Updated.pdf')

        # Grant permission to new pdf
        os.system('sudo chmod 777 ' + \
                  '/opt/cds-invenio/var/tmp/'+filename+'Updated.pdf')

        # No need of info file anymore
        os.system('sudo rm /opt/cds-invenio/var/tmp/in.info')

        # Delete the old pdf, and move-rename the new one
        os.system('sudo rm '+inputfile+'')
        os.system('sudo mv ' + \
                  '/opt/cds-invenio/var/tmp/'+filename+'' + \
                  'Updated.pdf '+inputfile+'')
    except Exception:
        print 'Error forming the info file ' + \
              '(wrong InfoKeys) or with pdftk-update\n'


    return


