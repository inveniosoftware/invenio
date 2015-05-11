# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013, 2014, 2015 CERN.
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

"""Upgrade command line."""

from __future__ import absolute_import

import os
import os.path

import sys

from datetime import date

from werkzeug.utils import import_string

from .engine import InvenioUpgrader
from .operations import produce_upgrade_operations


UPGRADE_TEMPLATE = """# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) %(year)s CERN.
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

import warnings

from invenio.ext.sqlalchemy import db
from invenio.modules.upgrader.api import op
from invenio.utils.text import wait_for_user

from sqlalchemy import *

%(imports)s

# Important: Below is only a best guess. You MUST validate which previous
# upgrade you depend on.
depends_on = %(depends_on)s


def info():
    \"\"\"Info message.\"\"\"
    return "Short description of upgrade displayed to end-user"


def do_upgrade():
    \"\"\"Implement your upgrades here.\"\"\"
%(operations)s


def estimate():
    \"\"\"Estimate running time of upgrade in seconds (optional).\"\"\"
    return 1


def pre_upgrade():
    \"\"\"Run pre-upgrade checks (optional).\"\"\"
    # Example of raising errors:
    # raise RuntimeError("Description of error 1", "Description of error 2")


def post_upgrade():
    \"\"\"Run post-upgrade checks (optional).\"\"\"
    # Example of issuing warnings:
    # warnings.warn("A continuable error occurred")
"""


def cmd_upgrade_check(upgrader=None):
    """Command for running pre-upgrade checks."""
    if not upgrader:
        upgrader = InvenioUpgrader()
    logger = upgrader.get_logger()

    try:
        # Run upgrade pre-checks
        upgrades = upgrader.get_upgrades()

        # Check if there's anything to upgrade
        if not upgrades:
            logger.info("All upgrades have been applied.")
            sys.exit(0)

        logger.info("Following upgrade(s) have not been applied yet:")
        for u in upgrades:
            title = u['__doc__']
            if title:
                logger.info(" * %s (%s)" % (u['id'], title))
            else:
                logger.info(" * %s" % u['id'])

        logger.info("Running pre-upgrade checks...")
        upgrader.pre_upgrade_checks(upgrades)
        logger.info("Upgrade check successful - estimated time for upgrading"
                    " Invenio is %s..." % upgrader.human_estimate(upgrades))
    except RuntimeError as e:
        for msg in e.args:
            logger.error(unicode(msg))
        logger.error("Upgrade check failed. Aborting.")
        sys.exit(1)


def cmd_upgrade(upgrader=None):
    """Command for applying upgrades."""
    from invenio.config import CFG_LOGDIR
    from invenio.utils.text import wrap_text_in_a_box, wait_for_user

    logfilename = os.path.join(CFG_LOGDIR, 'invenio_upgrader.log')
    if not upgrader:
        upgrader = InvenioUpgrader()
    logger = upgrader.get_logger(logfilename=logfilename)

    try:
        upgrades = upgrader.get_upgrades()

        if not upgrades:
            logger.info("All upgrades have been applied.")
            return

        logger.info("Following upgrade(s) will be applied:")

        for u in upgrades:
            title = u['__doc__']
            if title:
                logger.info(" * %s (%s)" % (u['id'], title))
            else:
                logger.info(" * %s" % u['id'])

        logger.info("Running pre-upgrade checks...")
        upgrader.pre_upgrade_checks(upgrades)

        logger.info("Calculating estimated upgrade time...")
        estimate = upgrader.human_estimate(upgrades)

        wait_for_user(wrap_text_in_a_box(
            "WARNING: You are going to upgrade your installation "
            "(estimated time: %s)!" % estimate))

        for u in upgrades:
            title = u['__doc__']
            if title:
                logger.info("Applying %s (%s)" % (u['id'], title))
            else:
                logger.info("Applying %s" % u['id'])
            upgrader.apply_upgrade(u)

        logger.info("Running post-upgrade checks...")
        upgrader.post_upgrade_checks(upgrades)

        if upgrader.has_warnings():
            logger.warning("Upgrade completed with %s warnings - please check "
                           "log-file for further information:\nless %s"
                           % (upgrader.get_warnings_count(), logfilename))
        else:
            logger.info("Upgrade completed successfully.")
    except RuntimeError as e:
        for msg in e.args:
            logger.error(unicode(msg))
        logger.info("Please check log file for further information:\n"
                    "less %s" % logfilename)
        sys.exit(1)


def cmd_upgrade_show_pending(upgrader=None):
    """Command for showing upgrades ready to be applied."""
    if not upgrader:
        upgrader = InvenioUpgrader()
    logger = upgrader.get_logger()

    try:
        upgrades = upgrader.get_upgrades()

        if not upgrades:
            logger.info("All upgrades have been applied.")
            return

        logger.info("Following upgrade(s) are ready to be applied:")

        for u in upgrades:
            title = u['__doc__']
            if title:
                logger.info(" * %s (%s)" % (u['id'], title))
            else:
                logger.info(" * %s" % u['id'])
    except RuntimeError as e:
        for msg in e.args:
            logger.error(unicode(msg))
        sys.exit(1)


def cmd_upgrade_show_applied(upgrader=None):
    """Command for showing all upgrades already applied."""
    if not upgrader:
        upgrader = InvenioUpgrader()
    logger = upgrader.get_logger()

    try:
        upgrades = upgrader.get_history()

        if not upgrades:
            logger.info("No upgrades have been applied.")
            return

        logger.info("Following upgrade(s) have been applied:")

        for u_id, applied in upgrades:
            logger.info(" * %s (%s)" % (u_id, applied))
    except RuntimeError as e:
        for msg in e.args:
            logger.error(unicode(msg))
        sys.exit(1)


def cmd_upgrade_create_release_recipe(pkg_path, repository=None,
                                      output_path=None, upgrader=None):
    """Create a new release upgrade recipe (for developers)."""
    if not upgrader:
        upgrader = InvenioUpgrader()
    logger = upgrader.get_logger()

    try:
        endpoints = upgrader.find_endpoints()

        if not endpoints:
            logger.error("No upgrades found.")
            sys.exit(1)

        depends_on = []
        for repo, upgrades in endpoints.items():
            depends_on.extend(upgrades)

        return cmd_upgrade_create_standard_recipe(pkg_path,
                                                  repository=repository,
                                                  depends_on=depends_on,
                                                  release=True,
                                                  output_path=output_path,
                                                  upgrader=upgrader)
    except RuntimeError as e:
        for msg in e.args:
            logger.error(unicode(msg))
        sys.exit(1)


def cmd_upgrade_create_standard_recipe(pkg_path, repository=None,
                                       depends_on=None, release=False,
                                       upgrader=None, output_path=None,
                                       auto=False, overwrite=False, name=None):
    """Create a new upgrade recipe (for developers)."""
    if not upgrader:
        upgrader = InvenioUpgrader()
    logger = upgrader.get_logger()

    try:
        path, found_repository = _upgrade_recipe_find_path(pkg_path)

        if output_path:
            path = output_path

        if not repository:
            repository = found_repository

        if not os.path.exists(path):
            raise RuntimeError("Path does not exists: %s" % path)
        if not os.path.isdir(path):
            raise RuntimeError("Path is not a directory: %s" % path)

        # Generate upgrade filename
        if release:
            filename = "%s_release_x_y_z.py" % repository
        else:
            filename = "%s_%s_%s.py" % (repository,
                                        date.today().strftime("%Y_%m_%d"),
                                        name or 'rename_me')

        # Check if generated repository name can be parsed
        test_repository = upgrader._parse_plugin_id(filename[:-3])
        if repository != test_repository:
            raise RuntimeError(
                "Generated repository name cannot be parsed. "
                "Please override it with --repository option."
            )

        upgrade_file = os.path.join(path, filename)

        if os.path.exists(upgrade_file):
            if not overwrite:
                raise RuntimeError(
                    "Could not generate upgrade - %s already exists."
                    % upgrade_file
                )

        # Determine latest installed upgrade
        if depends_on is None:
            depends_on = ["CHANGE_ME"]

            u = upgrader.latest_applied_upgrade(repository=repository)
            if u:
                depends_on = [u]

        # Write upgrade template file
        _write_template(upgrade_file, depends_on, repository, auto=auto)

        logger.info("Created new upgrade %s" % upgrade_file)
    except RuntimeError as e:
        for msg in e.args:
            logger.error(unicode(msg))
        sys.exit(1)


#
# Helper functions
#
def _write_template(upgrade_file, depends_on, repository, auto=False):
    """Write template to upgrade file."""
    if auto:
        # Ensure all models are loaded
        from invenio.ext.sqlalchemy import models
        list(models)
        template_args = produce_upgrade_operations()
        operations_str = template_args['upgrades']
        import_str = template_args['imports']
    else:
        operations_str = "    pass"
        import_str = ""

    with open(upgrade_file, 'w') as f:
        f.write(UPGRADE_TEMPLATE % {
            'depends_on': depends_on,
            'repository': repository,
            'year': date.today().year,
            'operations': operations_str,
            'imports': import_str
        })


def _upgrade_recipe_find_path(import_str, create=True):
    """Determine repository name and path for new upgrade.

    It is based on package import path.
    """
    try:
        # Import package
        m = import_string(import_str)

        # Check if package or module
        if m.__package__ is not None and m.__package__ != m.__name__:
            raise RuntimeError(
                "Expected package but found module at '%s'." % import_str
            )

        # Create upgrade directory if it does not exists
        path = os.path.join(os.path.dirname(m.__file__), "upgrades")
        if not os.path.exists(path) and create:
            os.makedirs(path)

        # Create init file if it does not exists
        init = os.path.join(path, "__init__.py")
        if not os.path.exists(init) and create:
            open(init, 'a').close()

        repository = m.__name__.split(".")[-1]

        return (path, repository)
    except ImportError:
        raise RuntimeError("Could not find module '%s'." % import_str)
    except SyntaxError:
        raise RuntimeError("Module '%s' has syntax errors." % import_str)
