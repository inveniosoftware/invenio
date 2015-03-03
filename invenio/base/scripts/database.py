# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2013, 2014, 2015 CERN.
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

"""Database script functions."""

from __future__ import print_function

import datetime

import os

import sys

from pipes import quote

from flask import current_app

from invenio.ext.script import Manager, change_command_name, print_progress

from six import iteritems

manager = Manager(usage="Perform database operations")

# Shortcuts for manager options to keep code DRY.
option_yes_i_know = manager.option('--yes-i-know', action='store_true',
                                   dest='yes_i_know', help='use with care!')
option_quiet = manager.option('--quiet', action='store_true',
                              dest='quiet', help='show less output')
option_default_data = manager.option(
    '--no-data', action='store_false',
    dest='default_data',
    help='do not populate tables with default data'
)


@manager.option('-u', '--user', dest='user', default="root")
@manager.option('-p', '--password', dest='password', default="")
@option_yes_i_know
def init(user='root', password='', yes_i_know=False):
    """Initialize database and user."""
    from invenio.ext.sqlalchemy import db
    from invenio.utils.text import wrap_text_in_a_box, wait_for_user

    # Step 0: confirm deletion
    wait_for_user(wrap_text_in_a_box(
        "WARNING: You are going to destroy your database tables! Run first"
        " `inveniomanage database drop`."
    ))

    # Step 1: drop database and recreate it
    if db.engine.name == 'mysql':
        # FIXME improve escaping
        args = dict((k, str(v).replace('$', '\$'))
                    for (k, v) in iteritems(current_app.config)
                    if k.startswith('CFG_DATABASE'))
        args = dict(zip(args, map(quote, args.values())))
        prefix = ('{cmd} -u {user} --password={password} '
                  '-h {CFG_DATABASE_HOST} -P {CFG_DATABASE_PORT} ')
        cmd_prefix = prefix.format(cmd='mysql', user=user, password=password,
                                   **args)
        cmd_admin_prefix = prefix.format(cmd='mysqladmin', user=user,
                                         password=password,
                                         **args)
        cmds = [
            cmd_prefix + '-e "DROP DATABASE IF EXISTS {CFG_DATABASE_NAME}"',
            (cmd_prefix + '-e "CREATE DATABASE IF NOT EXISTS '
             '{CFG_DATABASE_NAME} DEFAULT CHARACTER SET utf8 '
             'COLLATE utf8_general_ci"'),
            # Create user and grant access to database.
            (cmd_prefix + '-e "GRANT ALL PRIVILEGES ON '
             '{CFG_DATABASE_NAME}.* TO {CFG_DATABASE_USER}@localhost '
             'IDENTIFIED BY {CFG_DATABASE_PASS}"'),
            cmd_admin_prefix + 'flush-privileges'
        ]
        for cmd in cmds:
            cmd = cmd.format(**args)
            print(cmd)
            if os.system(cmd):
                print("ERROR: failed execution of", cmd, file=sys.stderr)
                sys.exit(1)
        print('>>> Database has been installed.')


@option_yes_i_know
@option_quiet
def drop(yes_i_know=False, quiet=False):
    """Drop database tables."""
    print(">>> Going to drop tables and related data on filesystem ...")

    from invenio.utils.date import get_time_estimator
    from invenio.utils.text import wrap_text_in_a_box, wait_for_user
    from invenio.ext.sqlalchemy.utils import test_sqla_connection, \
        test_sqla_utf8_chain
    from invenio.ext.sqlalchemy import db, models
    from invenio.modules.jsonalchemy.wrappers import StorageEngine

    # Step 0: confirm deletion
    wait_for_user(wrap_text_in_a_box(
        "WARNING: You are going to destroy your database tables and related "
        "data on filesystem!"))

    # Step 1: test database connection
    test_sqla_connection()
    test_sqla_utf8_chain()
    list(models)

    # Step 2: disable foreign key checks
    if db.engine.name == 'mysql':
        db.engine.execute('SET FOREIGN_KEY_CHECKS=0;')

    # Step 3: destroy associated data
    try:
        from invenio.legacy.webstat.api import destroy_customevents
        msg = destroy_customevents()
        if msg:
            print(msg)
    except Exception:
        print("ERROR: Could not destroy customevents.")

    tables = list(reversed(db.metadata.sorted_tables))

    def _dropper(items, prefix, dropper):
        N = len(items)
        prefix = prefix.format(N)
        e = get_time_estimator(N)
        dropped = 0
        if quiet:
            print(prefix)

        for i, table in enumerate(items):
            try:
                if not quiet:
                    print_progress(
                        1.0 * (i+1) / N, prefix=prefix,
                        suffix=str(datetime.timedelta(seconds=e()[0])))
                dropper(table)
                dropped += 1
            except Exception:
                print('\r', '>>> problem with dropping ', table)
                current_app.logger.exception(table)

        if dropped == N:
            print(">>> Everything has been dropped successfully.")
        else:
            print("ERROR: not all items were properly dropped.")
            print(">>> Dropped", dropped, 'out of', N)

    _dropper(StorageEngine.__storage_engine_registry__,
             '>>> Dropping {0} storage engines ...',
             lambda api: api.storage_engine.drop())

    _dropper(tables, '>>> Dropping {0} tables ...',
             lambda table: table.drop(bind=db.engine, checkfirst=True))


@option_default_data
@option_quiet
def create(default_data=True, quiet=False):
    """Create database tables from sqlalchemy models."""
    print(">>> Going to create tables...")

    from sqlalchemy import event
    from invenio.utils.date import get_time_estimator
    from invenio.ext.sqlalchemy.utils import test_sqla_connection, \
        test_sqla_utf8_chain
    from invenio.ext.sqlalchemy import db, models
    from invenio.modules.jsonalchemy.wrappers import StorageEngine

    test_sqla_connection()
    test_sqla_utf8_chain()

    list(models)

    def cfv_after_create(target, connection, **kw):
        print
        print(">>> Modifing table structure...")
        from invenio.legacy.dbquery import run_sql
        run_sql('ALTER TABLE collection_field_fieldvalue DROP PRIMARY KEY')
        run_sql('ALTER TABLE collection_field_fieldvalue ADD INDEX id_collection(id_collection)')
        run_sql('ALTER TABLE collection_field_fieldvalue CHANGE id_fieldvalue id_fieldvalue mediumint(9) unsigned')
        #print(run_sql('SHOW CREATE TABLE collection_field_fieldvalue'))

    from invenio.modules.search.models import CollectionFieldFieldvalue
    event.listen(CollectionFieldFieldvalue.__table__, "after_create", cfv_after_create)

    tables = db.metadata.sorted_tables

    def _creator(items, prefix, creator):
        N = len(items)
        prefix = prefix.format(N)
        e = get_time_estimator(N)
        created = 0
        if quiet:
            print(prefix)

        for i, table in enumerate(items):
            try:
                if not quiet:
                    print_progress(
                        1.0 * (i+1) / N, prefix=prefix,
                        suffix=str(datetime.timedelta(seconds=e()[0])))
                creator(table)
                created += 1
            except Exception:
                print('\r', '>>> problem with creating ', table)
                current_app.logger.exception(table)

        if created == N:
            print(">>> Everything has been created successfully.")
        else:
            print("ERROR: not all items were properly created.")
            print(">>> Created", created, 'out of', N)

    _creator(tables, '>>> Creating {0} tables ...',
             lambda table: table.create(bind=db.engine))

    _creator(StorageEngine.__storage_engine_registry__,
             '>>> Creating {0} storage engines ...',
             lambda api: api.storage_engine.create())


@manager.command
def dump():
    """Export all the tables, similar to `dbdump`."""
    print('>>> Dumping the DataBase.')


@manager.command
def diff():
    """Diff database against SQLAlchemy models."""
    try:
        from migrate.versioning import schemadiff  # noqa
    except ImportError:
        print(">>> Required package sqlalchemy-migrate is not installed. "
              "Please install with:")
        print(">>> pip install sqlalchemy-migrate")
        return

    from invenio.ext.sqlalchemy import db
    print(db.schemadiff())


@option_yes_i_know
@option_default_data
@option_quiet
def recreate(yes_i_know=False, default_data=True, quiet=False):
    """Recreate database tables (same as issuing 'drop' and then 'create')."""
    drop(quiet=quiet)
    create(default_data=default_data, quiet=quiet)


@manager.command
def uri():
    """Print SQLAlchemy database uri."""
    from flask import current_app
    print(current_app.config['SQLALCHEMY_DATABASE_URI'])


def version():
    """Get running version of database driver."""
    from invenio.ext.sqlalchemy import db
    try:
        return db.engine.dialect.dbapi.__version__
    except Exception:
        import MySQLdb
        return MySQLdb.__version__


@manager.option('-v', '--verbose', action='store_true', dest='verbose',
                help='Display more details (driver version).')
@change_command_name
def driver_info(verbose=False):
    """Get name of running database driver."""
    from invenio.ext.sqlalchemy import db
    try:
        return db.engine.dialect.dbapi.__name__ + (('==' + version())
                                                   if verbose else '')
    except Exception:
        import MySQLdb
        return MySQLdb.__name__ + (('==' + version()) if verbose else '')


@manager.option('-l', '--line-format', dest='line_format', default="%s: %s")
@manager.option('-s', '--separator', dest='separator', default="\n")
@change_command_name
def mysql_info(separator=None, line_format=None):
    """Detect and print MySQL details.

    Useful for debugging problems on various OS.
    """
    from invenio.ext.sqlalchemy import db
    if db.engine.name != 'mysql':
        raise Exception('Database engine is not mysql.')

    from invenio.legacy.dbquery import run_sql
    out = []
    for key, val in run_sql("SHOW VARIABLES LIKE 'version%'") + \
            run_sql("SHOW VARIABLES LIKE 'charact%'") + \
            run_sql("SHOW VARIABLES LIKE 'collat%'"):
        if False:
            print("    - %s: %s" % (key, val))
        elif key in ['version',
                     'character_set_client',
                     'character_set_connection',
                     'character_set_database',
                     'character_set_results',
                     'character_set_server',
                     'character_set_system',
                     'collation_connection',
                     'collation_database',
                     'collation_server']:
            out.append((key, val))

    if separator is not None:
        if line_format is None:
            line_format = "%s: %s"
        return separator.join(map(lambda i: line_format % i, out))

    return dict(out)


def main():
    """Main."""
    from invenio.base.factory import create_app
    app = create_app()
    manager.app = app
    manager.run()

if __name__ == '__main__':
    main()
