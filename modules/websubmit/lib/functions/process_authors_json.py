# -*- coding: utf-8 -*-
#
# Copyright (C) 2014, 2015 CERN.
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

def encapsulate_id(id_dict, key, value):
    """
    """

    if (key in id_dict) and str(value).strip():
        return id_dict[key] % value
    else:
        return value

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
        "AUTHOR_ID": CFG_SUBFIELD_DEFINITIONS["id"],
    }

    filename = "%s/%s" % (curdir, json_field)
    if os.path.exists(filename):

        ## open the file that corresponds to the field
        ## and read its contents into a dictionary
        json_str = ParamFromFile(os.path.join(curdir, filename))
        obj = json.loads(json_str)

        field_values = []
        # For all the items in the field iterate their key,value
        # and place them in an array of dictionaries which contain
        # the tpl names that are going to be used as the keys and
        # their values as values.
        # (e.g. field_values[0]["AUTHOR_FULLNAME"] = "John Ellis")
        for items in obj["items"]:
            field_values.append(dict(CFG_TPL_FIELDS))
            # Make sure the the `field_key_to_separator` keys are list
            for key in field_key_to_separator.keys():
                field_values[-1][key] = []

            for key, value in items.iteritems():
                if key in CFG_JSON_TO_TPL_FIELDS.keys():
                    slug_id = CFG_JSON_TO_TPL_FIELDS[key]
                    encapsulated = encapsulate_id(
                        CFG_AUTHORITY_CONTAINER_DICTIONARY, key, value
                    )
                    if slug_id in field_key_to_separator.keys():
                        # Make sure that the appeded items are not empty
                        if value:
                            field_values[-1][slug_id].append(encapsulated)
                    else:
                        field_values[-1][slug_id] = encapsulated

        fields = list(set(CFG_JSON_TO_TPL_FIELDS.itervalues()))
        # For every field, take the field_values of each of the
        # elements and join the values (even the empty ones),
        # separating them with a newline, so bibconvert knows
        # which value corresponds to each element(author).
        for field in fields:
            attributes_to_write = []
            for field_value in field_values:
                if field in field_key_to_separator.keys():
                    items = field_value.get(field, "")
                    items_size = len(items)
                    if items_size > 1:
                        items[0] = "{0}</subfield>".format(items[0])
                        items[-1] = "<subfield code='{0}'>{1}".format(
                            field_key_to_separator.get(field), items[-1]
                        )
                        if items_size > 2:
                            for i in range(1, items_size - 1):
                                items[i] = "<subfield code='{0}'>{1}</subfield>".format(
                                    field_key_to_separator.get(field), items[i]
                                )
                    val = "".join(items)
                else:
                    val = str(field_value.get(field,"")).strip()
                # Check if value is empty
                val = val or "#None#"
                attributes_to_write.append(val)
            attributes_to_write = "\n".join(attributes_to_write)
            write_file(os.path.join(curdir,field),attributes_to_write)
