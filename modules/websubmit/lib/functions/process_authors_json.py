## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

__revision__ = "$Id$"

import os
import json
from invenio.websubmit_functions.Shared_Functions import \
    get_dictionary_from_string, \
    ParamFromFile, \
    write_file
from invenio.websubmit_config import \
    CFG_SUBFIELD_DEFINITIONS, \
    CFG_JSON_TO_TPL_FIELDS, \
    CFG_AUTHORITY_CONTAINER_DICTIONARY, \
    CFG_TPL_FIELDS

def _encapsulate_id(id_dict, key, value):
    """
    """

    if (key in id_dict) and str(value).strip():
        return id_dict[key] % value
    else:
        return value

def _convert_json_to_field_value_dictionary(json_str):
    field_key_to_separator = {
        "AUTHOR_ID": "</subfield><subfield code=\"%s\">" % CFG_SUBFIELD_DEFINITIONS["id"],
    }
    obj = json.loads(json_str)
    field_values = []
    # For all the items in the field iterate their key,value
    # and place them in an array of dictionaries which contain
    # the tpl names that are going to be used as the keys and
    # their values as values.
    # (e.g. field_values[0]["AUTHOR_FULLNAME"] = "John Ellis")
    for items in obj["items"]:
        field_values.append(dict(CFG_TPL_FIELDS))
        for k, v in items.iteritems():
            if CFG_JSON_TO_TPL_FIELDS.get(k):
                if field_values[-1].get(CFG_JSON_TO_TPL_FIELDS[k]) and field_key_to_separator.get(CFG_JSON_TO_TPL_FIELDS[k]):
                    field_values[-1][CFG_JSON_TO_TPL_FIELDS[k]] += \
                        field_key_to_separator[CFG_JSON_TO_TPL_FIELDS[k]] + _encapsulate_id(CFG_AUTHORITY_CONTAINER_DICTIONARY, k, v)
                else:
                    field_values[-1][CFG_JSON_TO_TPL_FIELDS[k]] = _encapsulate_id(CFG_AUTHORITY_CONTAINER_DICTIONARY, k, v)
    return field_values

def process_authors_json(parameters, curdir, form, user_info=None):
    """
    Converts the field value (from its repective file) from JSON
    to a format that bibconvert understands.
    """

    global sysno

    ## the name of the field that has the json inside
    json_field = parameters.get("authors_json", None)

    ## separators in case a field has more than one values
    field_key_to_separator = {
        "AUTHOR_ID": "</subfield><subfield code=\"%s\">" % (CFG_SUBFIELD_DEFINITIONS["id"],),
    }

    filename = "%s/%s" % (curdir, json_field)
    if os.path.exists(filename):

        ## open the file that corresponds to the field
        ## and read its contents into a dictionary
        json_str = ParamFromFile(os.path.join(curdir, filename))

        field_values = _convert_json_to_field_value_dictionary(json_str)

        fields = list(set(CFG_JSON_TO_TPL_FIELDS.itervalues()))
        # For every field, take the field_values of each of the
        # elements and join the values (even the empty ones),
        # separating them with a newline, so bibconvert knows
        # which value corresponds to each element(author).
        for field in fields:
            attributes_to_write = []
            for field_value in field_values:
                val = str(field_value.get(field,"")).strip().encode("string_escape")
                if not val:
                    val = "#None#"
                attributes_to_write.append(val)
            attributes_to_write = "\n".join(attributes_to_write)
            write_file(os.path.join(curdir,field),attributes_to_write)
