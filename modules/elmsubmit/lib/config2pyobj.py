# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import ConfigParser
import re

# Config file functions:

limited_python_identifier = r'^[a-zA-Z][a-zA-Z_0-9]*$'

class Config(object):

    def __init__(self, config_name, config_dict):
        self._config_name = config_name

        f = lambda (section_name, section_dict): config_dict.update({section_name : ConfigSection(config_name, section_name, section_dict)})
        map(f, config_dict.items())
        
        self._config_dict = config_dict

    def __getattr__(self, section_name):
        try:
            return self._config_dict[section_name]
        except:
            raise ConfigGetSectionError("config object '%s' does not contain section '%s'" % (self._config_name, section_name))

    def __setattr__(self, attr, value):
        if attr in ['_config_name', '_config_dict']:
            self.__dict__[attr] = value
        else:
            raise ConfigSetError('this class provides read only config access: setting attributes is not possible')

class ConfigSection(object):
    def __init__(self, config_name, section_name, section_dict):
        self._config_name = config_name
        self._section_name = section_name
        self._section_dict = section_dict
        
    def __getattr__(self, key_name):
        try:
            return self._section_dict[key_name]
        except KeyError:
            raise ConfigGetKeyError("config object '%s', section '%s' does not contain key '%s'" % (self._config_name, self._section_name, key_name))

    def __setattr__(self, attr, value):
        if attr in ['_config_name', '_section_name', '_section_dict']:
            self.__dict__[attr] = value
        else:
            raise ConfigSetError('this class provides read only config access: setting attributes is not possible')

def configobj(files, name=None):
    try:
        # file[0][0] does not work to see if we have a list of string
        # like objects, since pythons character are just strings.
        # hence string[0][0][0][0][0][0][0][0]... is valid.
        files[0][1]
    except:
        raise ValueError("function configobj has first argument named files: this must be a list of filenames")
    
    if name is None:
        name = files[0]
    
    conf = ConfigParser.ConfigParser()
    # Read configuration files:
    map(lambda file: conf.readfp(open(file, 'rb')), files)

    # Make sure each section and key in the config file is a valid
    # python identifier:
    for section in conf.sections():
        if not re.search(limited_python_identifier, section):
            raise ConfigParseError(("config section '%s' is not a valid python identifier string matching regexp " +
                                   r"r'^[a-zA-Z][a-zA-Z_0-9]*$'") % (section))

        for item, value in conf.items(section):
            if not re.search(limited_python_identifier, item):
                raise ConfigParseError(("key '%s' in config section '%s' is not a valid python identifier string matching regexp " +
                                   r"r'^[a-zA-Z][a-zA-Z_0-9]*$'") % (item, section))
            
    # Create a dictionary from their contents:
    config_dict = {}
    f = lambda section: config_dict.update({ section : dict(conf.items(section)) })
    map(f, conf.sections())

    return Config(name, config_dict)
        
class ConfigError(Exception):
    pass

class ConfigParseError(ConfigError):
    pass

class ConfigSetError(ConfigError):
    pass

class ConfigGetError(ConfigError):
    pass

class ConfigGetSectionError(ConfigGetError):
    pass

class ConfigGetKeyError(ConfigGetError):
    pass


