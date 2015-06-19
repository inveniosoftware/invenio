# -*- coding: utf-8 -*-
# This file is part of Invenio.
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

"""Command-line tools for assets."""

import argparse
import os

import warnings

from flask import current_app, json

from flask_assets import ManageAssets

from flask_script import Command, Option

import pkg_resources

from .registry import bundles


class AssetsCommand(ManageAssets):

    """Command-line operation for assets."""

    def run(self, args):
        """Run the command-line.

        It loads the bundles from the :py:data:`bundles registry
        <invenio.ext.assets.registry.bundles>`.

        """
        if not self.env:
            self.env = current_app.jinja_env.assets_environment
            self.log = current_app.logger

        for pkg, bundle in bundles:
            output = "{0}: {1.output}:".format(pkg, bundle)
            for content in bundle.contents:
                output += "\n - {0}".format(content)
            self.log.info(output)
            self.env.register(bundle.output, bundle)

        return super(AssetsCommand, self).run(args)


class BowerCommand(Command):

    """Command-line operation for bower."""

    option_list = (
        Option("-i", "--bower-json", help="base input file",
               dest="filename", default=None),
        Option("-o", "--output-file", help="write bower.json to output file",
               dest="output_file", metavar="FILENAME",
               type=argparse.FileType(mode='w')),
        Option("-x", "--override", help="(DEPRECATED) override the input file",
               dest="override", action="store_const", const=True),
    )

    def run(self, filename=None, override=False, output_file=None):
        """Generate a bower.json file.

        It comes with default values for the ignore. Name and version are set
        to be invenio's.
        """
        output = {
            "name": "invenio",
            "version": pkg_resources.get_distribution("invenio").version,
            "dependencies": {},
            "resolutions": {
                "jquery": "~1.11",  # <2 would pick 1.7.2 (thx jquery.treeview)
                "bootstrap": "~3.3"
            }
        }

        if filename and os.path.exists(filename):
            with open(filename, "r") as f:
                output = dict(output, **json.load(f))

        for pkg, bundle in bundles:
            if bundle.bower:
                current_app.logger.debug((pkg, bundle.bower))
            output['dependencies'].update(bundle.bower)

        # Remove together with override kwarg, and Option object.
        if override:
            warnings.warn("Use of --override is deprecated and will "
                          "be removed. Please use --output-file instead.",
                          DeprecationWarning)
            if filename and os.path.exists(filename) and output_file is None:
                output_file = open(filename, 'w')

        options = dict(indent=4)
        if output_file is None:
            print(json.dumps(output, **options)).encode("utf-8")
        else:
            json.dump(output, output_file, **options)
            output_file.close()
