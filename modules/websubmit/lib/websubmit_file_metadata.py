# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""This is the metadata reader and writer module. Contains the
proper plugin containers in order to read/write metadata from images
or other files.

Public APIs:
  - metadata_extract()
  - metadata_update()
"""

import os, sys
from optparse import OptionParser
from invenio.pluginutils import PluginContainer
from invenio.config import CFG_PYLIBDIR
from invenio.bibdocfile import decompose_file


def plugin_builder_function(plugin_name, plugin_code):
    """Function used to build the plugin container,
       so it behaves as a dictionary.
       @param parameters: plugin_name, plugin_code
       @return: dict """
    ret = {}
    for funct_name in ('can_read_local',
                       'can_read_remote',
                       'can_write_local',
                       'install',
                       'extract_metadata',
                       'write_metadata',
                       'extract_metadata_remote'):
        funct = getattr(plugin_code, funct_name, None)
        if funct is not None:
            ret[funct_name] = funct
    return ret

def metadata_extract(inputfile, verbose=0,
                     force=None, remote=False, loginpw=None):
    """EXIF and IPTC metadata extraction and printing from images
       or other many kind of files
       @param parameters: (string) path to the image/file
                          (bool) verbosity
                          (string) plugin to force
                          (bool) remote file
       @return: (dict) - metadata_tag - (interpreted) value"""

    # Check file type (0 base,1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    if verbose:
        print ext.lower(), 'extension to extract from'

    # Plugins
    metadata_extractor_plugins = PluginContainer(
        os.path.join(CFG_PYLIBDIR,
                     'invenio', 'websubmit_file_metadata_plugins', '*.py'),
                     plugin_builder=plugin_builder_function
        )

    # Case that the plugin was called with force option
    if force:
        i = 0
        for key in metadata_extractor_plugins.keys():
            if key == force:
                break
            else:
                i = i + 1
        j = 0
        for plugin in metadata_extractor_plugins.values():
            if i == j:
                if remote:
                    return plugin['extract_metadata_remote'](inputfile,
                                                             verbose)
                else:
                    return plugin['extract_metadata'](inputfile, verbose)
            else:
                j = j + 1
        raise TypeError, 'Incorrect plugin for this file'


    # Loop through the plugins to find a good one for ext
    for plugin in metadata_extractor_plugins.values():
        # Local file
        if plugin.has_key('can_read_local') and \
            plugin['can_read_local'](inputfile) and not remote:
            return plugin['extract_metadata'](inputfile, verbose)
        # Remote file
        elif remote and plugin.has_key('can_read_remote') and \
            plugin['can_read_remote'](inputfile):
            return plugin['extract_metadata_remote'](inputfile,
                                                     verbose, loginpw)


    # Case of no plugin found, raise
    raise TypeError, 'Non-valid input file'

def metadata_update(inputfile, verbose=0,
                    metadata_dictionary=None, force=None):
    """EXIF and IPTC metadata writing, if -v
       previous tag printing, to images. If some tag not set,
       it is auto-added, but must be a valid exif or iptc tag.
       Now also pdf metadata updating, using pdftk tool.
       @param parameters: (string) path to the image
                          (bool) verbosity
                          (dict) metadata container dictionary
                          (string) plugin to force
       @return: (string) - empty string for image/
                           path to new pdf in pdf"""

    # Check file type (0 base,1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    if verbose:
        print ext.lower(), 'extension to write to'

    # Plugins
    metadata_extractor_plugins = PluginContainer(
        os.path.join(CFG_PYLIBDIR,
                     'invenio', 'websubmit_file_metadata_plugins', '*.py'),
                     plugin_builder=plugin_builder_function
        )


    # Case that the plugin was called with force option
    if force:
        i = 0
        for key in metadata_extractor_plugins.keys():
            if key == force:
                break
            else:
                i = i + 1
        j = 0
        for plugin in metadata_extractor_plugins.values():
            if i == j:
                return plugin['write_metadata'](inputfile, verbose,
                                                metadata_dictionary)
            else:
                j = j + 1
        raise TypeError, 'Incorrect plugin for this file'


    # Loop through the plugins to find a good one to ext
    for plugin in metadata_extractor_plugins.values():
        if plugin.has_key('can_write_local') and \
            plugin['can_write_local'](inputfile):
            return plugin['write_metadata'](inputfile, verbose,
                                            metadata_dictionary)

    # Case of no plugin found, raise
    raise TypeError, 'Non-valid input file'

def metadata_info():
    """Shows information about the available plugins"""

    # Plugins
    metadata_extractor_plugins = PluginContainer(
        os.path.join(CFG_PYLIBDIR,
                     'invenio', 'websubmit_file_metadata_plugins', '*.py'),
                     plugin_builder=plugin_builder_function
        )


    # Print each operation on each plugin
    for plugin_name, plugin_funcs in metadata_extractor_plugins.iteritems():
        for optn in plugin_funcs:
            print '--Plugin name: ' + plugin_name + ', operation: ' + optn
            #print plugin_function.__doc__ + '()\n'

def main():
    """Manages the arguments, in order to call the proper
    metadata handling function"""

    def dictionary_callback(option, opt, value, parser, *args, **kwargs):
        """callback function used to get strings from command line
        of the type tag=value and push it into a dictionary
        @param parameters: optparse parameters"""
        if '=' in value:
            key, val = value.split('=', 1)
            if getattr(parser.values, 'metadata', None) is None:
                parser.values.metadata = {}
            parser.values.metadata[key] = val
            return
        else:
            raise ValueError("%s is not in the form key=value" % value)

    # Parse arguments
    parser = OptionParser(usage="websubmit_file_metadata {-e | -u | -i} "  + \
                          "[-f arg2] [-v] [-d tag=value] [-r] [-l arg3] " + \
                          "/path/to/file")

    parser.add_option("-e", "--extract", dest="extract", action='store_true',
                      help="extract metadata from file", default=False)
    parser.add_option("-u", "--update", dest="update", action='store_true',
                      help="update file metadata", default=False)
    parser.add_option("-f", "--force", dest="force_plugin",
                      help="Plugin we want to be used", type="string",
                      default=None)
    parser.add_option('-v', '--verbose', type="int",
                      dest='verbose', help='shows detailed information',
                      default=1)
    parser.add_option('-r', '--remote', action='store_true',
                      dest='remote', help='working with remote file',
                      default=False)
    parser.add_option('-d', '--dictionary-entry',
                      action="callback",
                      callback=dictionary_callback, type="string",
                      help='metadata to update [-d tag=value]')
    parser.add_option('-i', '--info', action='store_true',
                      dest='info', help='shows plugin information',
                      default=False)
    parser.add_option("-l", "--loginpw", dest="loginpw",
                      help="Login and password to access remote server [login:pw]",
                      type="string", default=None)

    (options, args) = parser.parse_args()

    ## Get the input file from the arguments list (it should be the
    ## first argument):
    input_file = None
    if len(args) > 0:
        input_file = args[0]

    # If there is no option -d, we avoid metadata option being undefined
    if getattr(parser.values, 'metadata', None) is None:
        parser.values.metadata = {}


    # Make sure there is not extract / write / info at the same time
    if (options.extract and options.update) or \
       (options.extract and options.info) or \
       (options.info and options.update):
        print "Choose either --extract, --update or --info"
        print parser.get_usage()
        sys.exit(1)
    elif (options.extract and not input_file) or \
            (options.update and not input_file):
        print "Input file is missing"
        print parser.get_usage()
        sys.exit(1)

    # Function call based on args
    if options.extract:
        try:
            metadata_extract(input_file,
                             options.verbose,
                             options.force_plugin,
                             options.remote,
                             options.loginpw)
        except TypeError, err:
            print err
            return 1
    elif options.update:
        try:
            metadata_update(input_file,
                            options.verbose,
                            options.metadata,
                            options.force_plugin
                            )
        except TypeError, err:
            print err
            return 1
    elif options.info:
        try:
            metadata_info()
        except TypeError:
            print 'Problem retrieving plugin information\n'
            return 1
    else:
        parser.error("Incorrect number of arguments\n")


## Start proceedings for CLI calls:
if __name__ == "__main__":
    main()

