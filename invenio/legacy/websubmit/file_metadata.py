# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2009, 2010, 2011, 2014 CERN.
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

"""This is the metadata reader and writer module.

Contains the proper plugin containers in order to read/write metadata
from images or other files.

from __future__ import print_function

Public APIs:
  - read_metadata()
  - write_metadata()
"""

from __future__ import print_function

__required_plugin_API_version__ = "WebSubmit File Metadata Plugin API 1.0"

import sys
from optparse import OptionParser
from six import iteritems

from invenio.legacy.bibdocfile.api import decompose_file
from invenio.legacy.websubmit.config import (
    InvenioWebSubmitFileMetadataRuntimeError
)
from invenio.legacy.websubmit.registry import file_metadata_plugins
from invenio.utils.datastructures import LazyDict

metadata_extractor_plugins = LazyDict(lambda: dict(filter(None, map(
    plugin_builder_function,
    file_metadata_plugins
))))


def read_metadata(inputfile, force=None, remote=False,
                  loginpw=None, verbose=0):
    """Return metadata extracted from given file as dictionary.

    Availability depends on input file format and installed plugins
    (return C{TypeError} if unsupported file format).

    @param inputfile: path to a file
    @type inputfile: string
    @param verbose: verbosity
    @type verbose: int
    @param force: name of plugin to use, to skip plugin auto-discovery
    @type force: string
    @param remote: if the file is accessed remotely or not
    @type remote: boolean
    @param loginpw: credentials to access secure servers (username:password)
    @type loginpw: string
    @return: dictionary of metadata tags as keys, and (interpreted)
             value as value
    @rtype: dict
    @raise TypeError: if file format is not supported.
    @raise RuntimeError: if required library to process file is missing.
    @raise InvenioWebSubmitFileMetadataRuntimeError:
    when metadata cannot be read.
    """
    metadata = None
    # Check file type (0 base, 1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    if verbose > 5:
        print(ext.lower(), 'extension to extract from')

    # Loop through the plugins to find a good one for given file
    for plugin_name, plugin in iteritems(metadata_extractor_plugins):
        # Local file
        if 'can_read_local' in plugin and \
            plugin['can_read_local'](inputfile) and not remote and \
                (not force or plugin_name == force):
            if verbose > 5:
                print('Using ' + plugin_name)
            fetched_metadata = plugin['read_metadata_local'](inputfile,
                                                             verbose)
            if not metadata:
                metadata = fetched_metadata
            else:
                metadata.update(fetched_metadata)

        # Remote file
        elif remote and 'can_read_remote' in plugin and \
            plugin['can_read_remote'](inputfile) and \
                (not force or plugin_name == force):
            if verbose > 5:
                print('Using ' + plugin_name)
            fetched_metadata = plugin['read_metadata_remote'](inputfile,
                                                              loginpw,
                                                              verbose)
            if not metadata:
                metadata = fetched_metadata
            else:
                metadata.update(fetched_metadata)

    # Return in case we have something
    if metadata is not None:
        return metadata

    # Case of no plugin found, raise
    raise TypeError('Unsupported file type')


def write_metadata(inputfile, outputfile, metadata_dictionary,
                   force=None, verbose=0):
    """Write metadata to given file.

    Availability depends on input file format and installed plugins
    (return C{TypeError} if unsupported file format).

    @param inputfile: path to a file
    @type inputfile: string
    @param outputfile: path to the resulting file.
    @type outputfile: string
    @param verbose: verbosity
    @type verbose: int
    @param metadata_dictionary: keys and values of metadata to update.
    @type metadata_dictionary: dict
    @param force: name of plugin to use, to skip plugin auto-discovery
    @type force: string
    @return: output of the plugin
    @rtype: string
    @raise TypeError: if file format is not supported.
    @raise RuntimeError: if required library to process file is missing.
    @raise InvenioWebSubmitFileMetadataRuntimeError:
    when metadata cannot be updated.
    """
    # Check file type (0 base, 1 name, 2 ext)
    ext = decompose_file(inputfile)[2]
    if verbose > 5:
        print(ext.lower(), 'extension to write to')

    # Loop through the plugins to find a good one to ext
    for plugin_name, plugin in iteritems(metadata_extractor_plugins):
        if 'can_write_local' in plugin and \
            plugin['can_write_local'](inputfile) and \
                (not force or plugin_name == force):
            if verbose > 5:
                print('Using ' + plugin_name)
            return plugin['write_metadata_local'](inputfile,
                                                  outputfile,
                                                  metadata_dictionary,
                                                  verbose)

    # Case of no plugin found, raise
    raise TypeError('Unsupported file type')


def metadata_info(verbose=0):
    """Show information about the available plugins."""
    print('Plugin APIs version: %s' % str(__required_plugin_API_version__))

    # Plugins
    print('Available plugins:')

    # Print each operation on each plugin
    for plugin_name, plugin_funcs in iteritems(metadata_extractor_plugins):
        if len(plugin_funcs) > 0:
            print('-- Name: ' + plugin_name)
            print('   Supported operation%s: ' %
                  (len(plugin_funcs) > 1 and 's' or '') +
                  ', '.join(plugin_funcs))

    # Are there any unloaded plugins?
    # broken_plugins = metadata_extractor_plugins.get_broken_plugins()
    # if len(broken_plugins.keys()) > 0:
    #     print 'Could not load the following plugin%s:' % \
    #           (len(broken_plugins.keys()) > 1 and 's' or '')
    #     for broken_plugin_name, broken_plugin_trace_info in iteritems(broken_plugins):
    #         print '-- Name: ' + broken_plugin_name
    #         if verbose > 5:
    #             formatted_traceback = \
    #                                   traceback.format_exception(broken_plugin_trace_info[0],
    #                                                            broken_plugin_trace_info[1],
    #                                                            broken_plugin_trace_info[2])
    #             print '    ' + ''.join(formatted_traceback).replace('\n', '\n    ')
    #         elif verbose > 0:
    #             print '    ' + str(broken_plugin_trace_info[1])


def print_metadata(metadata):
    """Pretty-print metadata returned by the plugins to standard output.

    @param metadata: object returned by the plugins when reading metadata
    @type metadata: dict
    """
    if metadata:
        max_key_length = max([len(key) for key in metadata.keys()])
        for key, value in iteritems(metadata):
            print(key, "." * (max_key_length - len(key)), str(value))
    else:
        print('(No metadata)')


def plugin_builder_function(plugin):
    """Internal function used to build the plugin container.

    It behaves as a dictionary.

    @param plugin_name: plugin_name
    @param plugin_code: plugin_code
    @return: the plugin container
    @rtype: dict
    """
    name = plugin.__name__.split('.')[-1]
    if not name.startswith('wsm_'):
        return

    ## Let's check for API version.
    api_version = getattr(plugin, '__plugin_version__', None)
    if api_version != __required_plugin_API_version__:
        raise Exception("Plugin version mismatch."
                        " Expected %s, found %s" %
                        (__required_plugin_API_version__,
                         api_version))
    ret = {}
    for funct_name in ('can_read_local',
                       'can_read_remote',
                       'can_write_local',
                       'read_metadata_local',
                       'write_metadata_local',
                       'read_metadata_remote'):
        funct = getattr(plugin, funct_name, None)
        if funct is not None:
            ret[funct_name] = funct
    return name, ret


def main():
    """Manage the arguments.

    In order to call the proper metadata handling function
    """
    def dictionary_callback(option, opt, value, parser, *args, **kwargs):
        """Callback function.

        It is used to get strings from command line
        of the type tag=value and push it into a dictionary
        @param parameters: optparse parameters
        """
        if '=' in value:
            key, val = value.split('=', 1)
            if getattr(parser.values, 'metadata', None) is None:
                parser.values.metadata = {}
            parser.values.metadata[key] = val
            return
        else:
            raise ValueError("%s is not in the form key=value" % value)

    # Parse arguments
    parser = OptionParser(usage="websubmit_file_metadata {-e | -u | -i} " +
                          "[-f arg2] [-v] [-d tag=value] [-r] [-l arg3] " +
                          "/path/to/file")

    parser.add_option("-e", "--extract", dest="extract", action='store_true',
                      help="extract metadata from file", default=False)
    parser.add_option("-u", "--update", dest="update", action='store_true',
                      help="update file metadata", default=False)
    parser.add_option("-o", "--output-file", dest="output_file",
                      help="Place to save updated file (when --update). " +
                      " Default is same as input file",
                      type="string", default=None)
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
                      help="Login and password to access remote server " +
                      " [login:pw]",
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

    # Is output file specified?
    if options.update and not options.output_file:
        if options.verbose > 5:
            print("Option --output-file not specified. Updating input file.")
        options.output_file = input_file
    elif options.extract and options.output_file:
        print("Option --output-file cannot be used with --extract.")
        print(parser.get_usage())
        sys.exit(1)

    # Make sure there is not extract / write / info at the same time
    if (options.extract and options.update) or \
       (options.extract and options.info) or \
       (options.info and options.update):
        print("Choose either --extract, --update or --info")
        print(parser.get_usage())
        sys.exit(1)
    elif (options.extract and not input_file) or \
            (options.update and not input_file):
        print("Input file is missing")
        print(parser.get_usage())
        sys.exit(1)

    # Function call based on args
    if options.extract:
        try:
            metadata = read_metadata(input_file,
                                     options.force_plugin,
                                     options.remote,
                                     options.loginpw,
                                     options.verbose)
            print_metadata(metadata)
        except TypeError as err:
            print(err)
            return 1
        except RuntimeError as err:
            print(err)
            return 1
        except InvenioWebSubmitFileMetadataRuntimeError as err:
            print(err)
            return 1
    elif options.update:
        try:
            write_metadata(input_file,
                           options.output_file,
                           options.metadata,
                           options.force_plugin,
                           options.verbose)
        except TypeError as err:
            print(err)
            return 1
        except RuntimeError as err:
            print(err)
            return 1
        except InvenioWebSubmitFileMetadataRuntimeError as err:
            print(err)
            return 1
    elif options.info:
        try:
            metadata_info(options.verbose)
        except TypeError:
            print('Problem retrieving plugin information\n')
            return 1
    else:
        parser.error("Incorrect number of arguments\n")


if __name__ == "__main__":
    main()
