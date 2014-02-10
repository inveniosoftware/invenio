# -*- coding: utf-8 -*-
#
## This file is part of Invenio.
## Copyright (C) 2012, 2013 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02D111-1307, USA.

"""GOTO CLI interface."""

import optparse

from invenio.base.factory import with_app_context

from invenio.utils.text import wait_for_user
from invenio.utils.json import json, json_unicode_to_utf8
from ..api import (REDIRECT_METHODS, is_redirection_label_already_taken,
                   register_redirection, update_redirection,
                   drop_redirection, get_redirection_data)


@with_app_context()
def main():
    """
    Entry point for the CLI
    """
    def get_json_parameters_from_cli(option, dummy_opt_str, value, dummy_parser):
        try:
            option.parameters = json_unicode_to_utf8(json.loads(value))
        except Exception, err:
            raise optparse.OptionValueError("Cannot parse as a valid JSON serialization the provided parameters: %s. %s" % (value, err))

    def get_parameter_from_cli(option, dummy_opt_str, value, dummy_parser):
        if not hasattr(option, 'parameters'):
            option.parameters = {}
        param, value = value.split('=', 1)
        try:
            value = int(value)
        except:
            pass
        option.parameters[param] = value

    parser = optparse.OptionParser()

    plugin_group = optparse.OptionGroup(parser, "Plugin Administration Options")
    plugin_group.add_option("--list-plugins", action="store_const", dest="action", const="list-goto-plugins", help="List available GOTO plugins and their documentation")
    #plugin_group.add_option("--list-broken-plugins", action="store_const", dest="action", const="list-broken-goto-plugins", help="List broken GOTO plugins")
    parser.add_option_group(plugin_group)

    redirection_group = optparse.OptionGroup(parser, "Redirection Manipultation Options")
    redirection_group.add_option("-r", "--register-redirection", metavar="LABEL", action="store", dest="register", help="Register a redirection with the provided LABEL")
    redirection_group.add_option("-u", "--update-redirection", metavar="LABEL", action="store", dest="update", help="Update the redirection specified by the provided LABEL")
    redirection_group.add_option("-g", "--get-redirection", metavar="LABEL", action="store", dest="get_redirection", help="Get all information about a redirection specified by LABEL")
    redirection_group.add_option("-d", "--drop-redirection", metavar="LABEL", action="store", dest="drop_redirection", help="Drop an existing redirection specified by LABEL")
    parser.add_option_group(redirection_group)

    specific_group = optparse.OptionGroup(parser, "Specific Options")
    specific_group.add_option("-P", "--plugin", metavar="PLUGIN", action="store", dest="plugin", help="Specify the plugin to use when registering or updating a redirection")
    specific_group.add_option("-j", "--json-parameters", metavar="PARAMETERS", action="callback", type="string", callback=get_json_parameters_from_cli, help="Specify the parameters to provide to the plugin (serialized in JSON)")
    specific_group.add_option("-p", "--parameter", metavar="PARAM=VALUE", action="callback", callback=get_parameter_from_cli, help="Specify a single PARAM=VALUE parameter to be provided to the plugin (alternative to the JSON serialization)", type="string")
    parser.add_option_group(specific_group)

    (options, dummy_args) = parser.parse_args()
    if options.action == "list-goto-plugins":
        print "GOTO plugins found:"
        for component, goto in REDIRECT_METHODS.items():
            print component + ' -> ' + getattr(goto, '__doc__',
                                               'No documentation')
    #elif options.action == 'list-broken-goto-plugins':
    #    print "Broken GOTO plugins found:"
    #    for component, error in REDIRECT_METHODS.get_broken_plugins().items():
    #        print component + '->' + str(error)
    elif options.register:
        label = options.register
        plugin = options.plugin
        parameters = getattr(options, 'parameters', {})
        if not plugin in REDIRECT_METHODS:
            parser.error("%s is not a valid plugin" % plugin)
        if is_redirection_label_already_taken(label):
            parser.error("The specified label %s is already taken" % label)
        register_redirection(label, plugin, parameters)
        print "The redirection %s was successfully registered for the plugin %s with parameters %s" % (label, plugin, parameters)
    elif options.update:
        label = options.update
        if not is_redirection_label_already_taken(label):
            parser.error("The specified label %s does not exist" % label)
        redirection_data = get_redirection_data(label)
        plugin = options.plugin or redirection_data['plugin']
        parameters = options.parameters or redirection_data['parameters']
        if not plugin in REDIRECT_METHODS:
            parser.error("%s is not a valid plugin" % plugin)
        update_redirection(label, plugin, parameters=None)
        print "The redirection %s was successfully updated for the plugin %s with parameters %s" % (label, plugin, parameters)
    elif options.get_redirection:
        label = options.get_redirection
        if not is_redirection_label_already_taken(label):
            parser.error("The specified label %s does not exist" % label)
        print get_redirection_data(label)
    elif options.drop_redirection:
        label = options.drop_redirection
        if is_redirection_label_already_taken(label):
            wait_for_user("Are you sure you want to drop the redirection: %s\n%s" % (label, get_redirection_data(label)))
            drop_redirection(label)
            print "The redirection %s was successfully dropped" % label
        else:
            print "The specified label %s is not registered with any redirection" % label
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
