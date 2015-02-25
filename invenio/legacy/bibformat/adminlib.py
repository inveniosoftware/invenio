# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2014, 2015 CERN.
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

"""Handle requests from the web interface to configure BibFormat."""

__revision__ = "$Id$"

import os
import re

from invenio.modules.formatter.config import \
     CFG_BIBFORMAT_TEMPLATES_PATH, \
     CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION
from invenio.modules.formatter import engine as bibformat_engine


def get_outputs_that_use_template(filename):
    """Return a list of output formats that call the given format template.

    The returned output formats also give their dependencies on tags.
    We don't return the complete output formats but some reference to
    them (filename + names)::

        [ {'filename':"filename_1.bfo"
           'names': {'en':"a name", 'fr': "un nom", 'generic':"a name"}
           'tags': ['710__a', '920__']
          },
          ...
        ]

    :param filename: a format template filename
    :return: output formats references sorted by (generic) name
    """
    output_formats_list = {}
    tags = []
    output_formats = bibformat_engine.get_output_formats(with_attributes=True)
    for output_format in output_formats:
        name = output_formats[output_format]['attrs']['names']['generic']
        # First look at default template, and add it if necessary
        if output_formats[output_format]['default'] == filename:
            output_formats_list[name] = {'filename':output_format,
                                         'names':output_formats[output_format]['attrs']['names'],
                                         'tags':[]}
        # Second look at each rule
        found = False
        for rule in output_formats[output_format]['rules']:
            if rule['template'] == filename:
                found = True
                tags.append(rule['field']) #Also build dependencies on tags

        # Finally add dependency on template from rule (overwrite default dependency,
        # which is weaker in term of tag)
        if found:
            output_formats_list[name] = {'filename':output_format,
                                         'names':output_formats[output_format]['attrs']['names'],
                                         'tags':tags}



    keys = output_formats_list.keys()
    keys.sort()
    return map(output_formats_list.get, keys)

def get_elements_used_by_template(filename):
    """
    Returns a list of format elements that are called by the given format template.
    The returned elements also give their dependencies on tags.

    Dependencies on tag might be approximative. See get_tags_used_by_element()
    doc string.

    We must handle usage of bfe_field in a special way if we want to retrieve
    used tag: used tag is given in "tag" parameter, not inside element code.

    The list is returned sorted by name::

        [ {'filename':"filename_1.py"
           'name':"filename_1"
           'tags': ['710__a', '920__']
          },
          ...
        ]

    :param filename: a format template filename
    :return: elements sorted by name
    """
    format_elements = {}
    format_template = bibformat_engine.get_format_template(filename=filename, with_attributes=True)
    code = format_template['code']
    format_elements_iter = bibformat_engine.pattern_tag.finditer(code)
    for result in format_elements_iter:
        function_name = result.group("function_name").lower()
        if function_name is not None and function_name not in format_elements \
               and not function_name == "field":
            filename = bibformat_engine.resolve_format_element_filename("BFE_"+function_name)
            if filename is not None:
                tags = get_tags_used_by_element(filename)
                format_elements[function_name] = {'name':function_name.lower(),
                                                  'filename':filename,
                                                  'tags':tags}
        elif function_name == "field":
            # Handle bfe_field element in a special way
            if function_name not in format_elements:
                #Indicate usage of bfe_field if not already done
                filename = bibformat_engine.resolve_format_element_filename("BFE_"+function_name)
                format_elements[function_name] = {'name':function_name.lower(),
                                                  'filename':filename,
                                                  'tags':[]}
            # Retrieve value of parameter "tag"
            all_params = result.group('params')
            function_params_iterator = bibformat_engine.pattern_function_params.finditer(all_params)
            for param_match in function_params_iterator:
                name = param_match.group('param')
                if name == "tag":
                    value = param_match.group('value')
                    if not value in format_elements[function_name]['tags']:
                        format_elements[function_name]['tags'].append(value)
                    break

    keys = format_elements.keys()
    keys.sort()
    return map(format_elements.get, keys)


# Format Elements Dependencies
#

def get_tags_used_by_element(filename):
    """
    Returns a list of tags used by given format element

    APPROXIMATIVE RESULTS: the tag are retrieved in field(), fields()
    and control_field() function. If they are used computed, or saved
    in a variable somewhere else, they are not retrieved
    @TODO: There is room for improvements. For example catch
    call to BibRecord functions.

    :param filename: a format element filename
    :return: tags sorted by value
    """
    tags = {}

    format_element = bibformat_engine.get_format_element(filename)
    if format_element is None:
        return []
    elif format_element['type']=="field":
        tags = format_element['attrs']['tags']
        return tags

    filename = bibformat_engine.resolve_format_element_filename(filename)
    path = bibformat_engine.get_format_element_path(filename)
    format = open(path, 'r')
    code = format.read()
    format.close
    tags_pattern = re.compile('''
    (field|fields|control_field)\s*       #Function call
    \(\s*                                 #Opening parenthesis
    [\'"]+                                #Single or double quote
    (?P<tag>.+?)                          #Tag
    [\'"]+\s*                             #Single or double quote
    (,[^\)]+)*                            #Additional function param
    \)                                    #Closing parenthesis
     ''', re.VERBOSE | re.MULTILINE)

    tags_iter = tags_pattern.finditer(code)
    for result in tags_iter:
        tags[result.group("tag")] = result.group("tag")

    return tags.values()


def get_templates_that_use_element(name):
    """Return a list of format templates that call the given format element.

    The returned format templates also give their dependencies on tags::

        [ {'filename':"filename_1.bft"
           'name': "a name"
           'tags': ['710__a', '920__']
          },
          ...
        ]

    :param name: a format element name
    :return: templates sorted by name
    """
    format_templates = {}
    tags = []
    files = os.listdir(CFG_BIBFORMAT_TEMPLATES_PATH) #Retrieve all templates
    for possible_template in files:
        if possible_template.endswith(CFG_BIBFORMAT_FORMAT_TEMPLATE_EXTENSION):
            format_elements = get_elements_used_by_template(possible_template) #Look for elements used in template
            format_elements = map(lambda x: x['name'].lower(), format_elements)
            try: #Look for element
                format_elements.index(name.lower()) #If not found, get out of "try" statement

                format_template = bibformat_engine.get_format_template(filename=possible_template, with_attributes=True)
                template_name = format_template['attrs']['name']
                format_templates[template_name] = {'name':template_name,
                                                   'filename':possible_template}
            except:
                pass

    keys = format_templates.keys()
    keys.sort()
    return map(format_templates.get, keys)

# Output Formats Dependencies
#

def get_templates_used_by_output(code):
    """Return a list of templates used inside an output format give by its code.

    The returned format templates also give their dependencies on elements and tags::

        [ {'filename':"filename_1.bft"
           'name': "a name"
           'elements': [{'filename':"filename_1.py", 'name':"filename_1", 'tags': ['710__a', '920__']
          }, ...]
          },
          ...
        ]

    :param code: outpout format code
    :return: templates sorted by name
    """
    format_templates = {}
    output_format = bibformat_engine.get_output_format(code, with_attributes=True)

    filenames = map(lambda x: x['template'], output_format['rules'])
    if output_format['default'] != "":
        filenames.append(output_format['default'])

    for filename in filenames:
        template = bibformat_engine.get_format_template(filename, with_attributes=True)
        name = template['attrs']['name']
        elements = get_elements_used_by_template(filename)
        format_templates[name] = {'name':name,
                                  'filename':filename,
                                  'elements':elements}


    keys = format_templates.keys()
    keys.sort()
    return map(format_templates.get, keys)
