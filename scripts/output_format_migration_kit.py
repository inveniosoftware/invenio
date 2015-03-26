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

"""Perform output format migration operation."""

from __future__ import print_function

import os
import yaml

from flask import current_app
from invenio.ext.script import Manager

manager = Manager(usage="Perform output format migration operations.")


def get_output_format(filename):
    output_format = {'rules': [], 'default': ""}

    format_file = open(filename)

    current_tag = ''
    for line in format_file:
        line = line.strip()
        if line == "":
            # Ignore blank lines
            continue
        if line.endswith(":"):
            # Retrieve tag

            # Remove : spaces and eol at the end of line
            clean_line = line.rstrip(": \n\r")
            # The tag starts at second position
            current_tag = "".join(clean_line.split()[1:]).strip()
        elif line.find('---') != -1:
            words = line.split('---')
            template = words[-1].strip()
            condition = ''.join(words[:-1])

            output_format['rules'].append({'field': current_tag,
                                           'value': condition,
                                           'template': template,
                                           })

        elif line.find(':') != -1:
            # Default case
            default = line.split(':')[1].strip()
            output_format['default'] = default

    return output_format


@manager.option('-o', '--output', dest='output', default=".")
def run(output):
    """Convert *bfo* to *yml*."""
    from invenio.legacy.dbquery import run_sql
    from flask_registry import PkgResourcesDirDiscoveryRegistry, \
        ModuleAutoDiscoveryRegistry, RegistryProxy
    from invenio.utils.datastructures import LazyDict

    output_formats_directories = RegistryProxy(
        'legacy_output_formats_directories',
        ModuleAutoDiscoveryRegistry,
        'output_formats'
    )

    output_formats = RegistryProxy(
        'legacy_output_formats',
        PkgResourcesDirDiscoveryRegistry,
        '.', registry_namespace=output_formats_directories
    )

    def create_output_formats_lookup():
        """Create output formats."""
        out = {}

        for f in output_formats:
            of = os.path.basename(f).lower()
            if not of.endswith('.bfo'):
                continue
            of = of[:-4]
            if of in out:
                continue
            out[of] = f
        return out

    output_formats_lookup = LazyDict(create_output_formats_lookup)

    for row in run_sql('SELECT id, name, code, description, content_type, '
                       ' mime_type, visibility FROM format'):
        code = row[2].lower()
        out = {
            'name': row[1],
            'description': row[3],
            'visibility': 1 if row[6] == '1' else 0,
            'content_type': row[4],
        }
        if row[5]:
            out['mime_type'] = row[5]

        try:
            out.update(get_output_format(output_formats_lookup[code]))
            with open(os.path.join(output, code + '.yml'), 'w') as f:
                yaml.dump(out, stream=f)
            # print('echo "{0}" > {1}/{2}.yml'.format(
            #     yaml.dump(out), output, code))
        except Exception:
            current_app.logger.exception(
                "Could not convert '{0}'".format(code)
            )


def main():
    """Run manager."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
