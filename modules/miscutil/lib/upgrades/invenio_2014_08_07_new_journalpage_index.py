# -*- coding: utf-8 -*-
##
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

from invenio.dbquery import run_sql

depends_on = ['invenio_release_1_1_0']


def info():
    return "New journalpage tag, field and index."


def do_upgrade():
    """ Perform upgrade """
    pass


def do_upgrade_atlantis():
    """ Perform upgrade """

    # Create tag and field
    field_id = run_sql(
        """INSERT INTO field SET name='journal page', code='journalpage'"""
    )
    tag_id = run_sql(
        """INSERT INTO tag SET name='journal page', value='773__c'"""
    )
    run_sql(
        """INSERT INTO field_tag VALUES (%s, %s, 10)""",
        (field_id, tag_id)
    )

    # Create index
    index_last_used_id = run_sql("""SELECT MAX(id) FROM idxINDEX""")[0][0]
    index_id = run_sql(
        """
        INSERT INTO idxINDEX
        SET
            id = %s,
            name = 'journalpage',
            description =
              'This index contains words/phrases from the journal page field.',
            tokenizer = 'BibIndexJournalPageTokenizer'
        """,
        (index_last_used_id + 1,)
    )
    run_sql(
        """
        INSERT INTO idxINDEX_field (id_idxINDEX, id_field)
        VALUES (%s, %s)
        """,
        (index_id, field_id)
    )

    # Create index tables
    for index_type in ["WORD", "PAIR", "PHRASE"]:
        _create_index_front_table(index_type, index_id)
        _create_index_rear_table(index_type, index_id)


def estimate():
    """ Return estimate of upgrade time in seconds """
    return 1


def _create_index_front_table(index_type, index_id):
    table_name = "idx%s%02dF" % (index_type, index_id)
    return run_sql(
        """
        CREATE TABLE IF NOT EXISTS %s (
            id mediumint(9) unsigned NOT NULL auto_increment,
            term varchar(50) default NULL,
            hitlist longblob,
            PRIMARY KEY  (id),
            UNIQUE KEY term (term)
        ) ENGINE=MyISAM;
        """ % (table_name,)
    )


def _create_index_rear_table(index_type, index_id):
    table_name = "idx%s%02dR" % (index_type, index_id)
    run_sql(
        """
        CREATE TABLE IF NOT EXISTS %s (
            id_bibrec mediumint(9) unsigned NOT NULL,
            termlist longblob,
            type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL
                default 'CURRENT',
            PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """ % (table_name,)
    )