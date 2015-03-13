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

from flask import current_app

from invenio.ext.script import Manager, change_command_name, print_progress

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
    from invenio.ext.sqlalchemy.utils import initialize_database_user
    from invenio.utils.text import wrap_text_in_a_box, wait_for_user

    from sqlalchemy_utils.functions import database_exists, create_database, \
        drop_database

    from sqlalchemy.engine.url import URL
    from sqlalchemy import create_engine

    # Step 0: confirm deletion
    wait_for_user(wrap_text_in_a_box(
        "WARNING: You are going to destroy your database tables! Run first"
        " `inveniomanage database drop`."
    ))

    # Step 1: create URI to connect admin user
    cfg = current_app.config
    SQLALCHEMY_DATABASE_URI = URL(
        cfg.get('CFG_DATABASE_TYPE', 'mysql'),
        username=user,
        password=password,
        host=cfg.get('CFG_DATABASE_HOST'),
        database=cfg.get('CFG_DATABASE_NAME'),
        port=cfg.get('CFG_DATABASE_PORT'),
    )

    # Step 2: drop the database if already exists
    if database_exists(SQLALCHEMY_DATABASE_URI):
        drop_database(SQLALCHEMY_DATABASE_URI)
        print('>>> Database has been dropped.')

    # Step 3: create the database
    create_database(SQLALCHEMY_DATABASE_URI, encoding='utf8')
    print('>>> Database has been created.')

    # Step 4: setup connection with special user
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    engine.connect()

    # Step 5: grant privileges for the user
    initialize_database_user(
        engine=engine,
        database_name=current_app.config['CFG_DATABASE_NAME'],
        database_user=current_app.config['CFG_DATABASE_USER'],
        database_pass=current_app.config['CFG_DATABASE_PASS'],
    )
    print('>>> Database user has been initialized.')


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

    # Step 2: destroy associated data
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
                print('\r>>> problem with dropping {0}'.format(table))
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

    from invenio.utils.date import get_time_estimator
    from invenio.ext.sqlalchemy.utils import test_sqla_connection, \
        test_sqla_utf8_chain
    from invenio.ext.sqlalchemy import db, models
    from invenio.modules.jsonalchemy.wrappers import StorageEngine

    test_sqla_connection()
    test_sqla_utf8_chain()

    list(models)

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
                print('\r>>> problem with creating {0}'.format(table))
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
    return db.engine.dialect.dbapi.__version__


@manager.option('-v', '--verbose', action='store_true', dest='verbose',
                help='Display more details (driver version).')
@change_command_name
def driver_info(verbose=False):
    """Get name of running database driver."""
    from invenio.ext.sqlalchemy import db
    return db.engine.dialect.dbapi.__name__ + (('==' + version())
                                               if verbose else '')


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
