# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

"""Generate JSONSchema output from existing JSONAlchemy models."""

from __future__ import print_function

import json

from flask import current_app

from invenio.ext.script import Manager

manager = Manager(usage=__doc__)


@manager.command
@manager.option('-n', '--namespace', dest='namespace', default='recordext',
                help="Desired namespace")
@manager.option('-m', '--model', dest='model', default='__default__',
                help="Desired model. e.g. 'hep'")
def jsonschema(model, namespace="recordext"):
    """Print JSONSchema output from existing JSONAlchemy models."""
    from invenio.modules.jsonalchemy.parser import ModelParser
    from invenio.modules.jsonalchemy.parser import FieldParser

    out = {"$schema": "http://json-schema.org/schema#",
           "id": "%(site_url)s/schemas/%(model)s-0.0.1.json" % {
               'site_url': current_app.config['CFG_SITE_URL'],
               'model': model
               },
           "type": "object",
           "properties": {},
           "required": []}
    fields = ModelParser.resolve_models(model, namespace).get('fields', {})
    out['required'] = []
    for field in fields:
        parsed_field = FieldParser.field_definition_model_based(field, model,
                                                                namespace)
        description = parsed_field.pop('description', None)
        sub_properties = {}
        try:
            for sub_property in parsed_field['producer']['json_for_marc'][0][1].values():
                sub_properties[sub_property] = {'type': 'string'}
        except (KeyError, IndexError):
            pass
        cerberus_schema = parsed_field.get('schema', {}).get('field', {})
        if cerberus_schema.get('force', False):
            out['required'].append(field)
        cerberus_type = cerberus_schema.get('type')
        schema_type = 'object'
        if cerberus_type == 'dict':
            schema_type = 'object'
        elif cerberus_type in ('list', 'set'):
            schema_type = 'array'
        elif not cerberus_type and field.lower().endswith('s'):
            schema_type = 'array'
        if schema_type == 'array':
            property_ = out['properties'][field] = {'type': 'array',
                                                    'uniqueItems': True,
                                                    'items': {'type': 'object',
                                                              'properties':
                                                                  sub_properties},
                                                    'other': str(parsed_field)}
        else:
            property_ = out['properties'][field] = {'type': 'object',
                                                    'properties':
                                                        sub_properties,
                                                    'other': str(parsed_field)}

        if description:
            property_['description'] = description

    print(json.dumps(out, indent=4, sort_keys=True))


def main():
    """Run manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
