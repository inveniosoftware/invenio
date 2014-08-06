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

depends_on = ['invenio_2014_06_11_new_field_datasource']


def info():
    return "Converts author and exactauthor reguar indexes to virtual " + \
           "indexes; adds related indexes simpleauthor, canonicalauthor, " + \
           "parentauthor, parentcanonicalauthor, exactsimpleauthor, " + \
           "exactparentauthor; adds fields simpleauthor, exactsimpleauthor"


def do_upgrade():
    pass


def do_upgrade_atlantis():
    # Create tags
    tag_datasource_id = run_sql(
        """
        SELECT id FROM tag
        WHERE name = 'data source'
        """
    )

    # Read and create fields
    field_datasource_id = run_sql(
        """
        SELECT id FROM field
        VALUES code = 'datasource'
        """
    )
    field_simpleauthor_id = run_sql(
        """
        INSERT INTO field (name, code)
        VALUES ('simple author','simpleauthor')
        """
    )
    field_author_id = run_sql(
        """
        SELECT id FROM field
        WHERE code = 'author'
        """
    )[0][0]
    field_exactsimpleauthor_id = run_sql(
        """
        INSERT INTO field (name, code)
        VALUES ('exact simple author','exactsimpleauthor')
        """
    )
    field_exactauthor_id = run_sql(
        """
        SELECT id FROM field
        WHERE code = 'exactauthor'
        """
    )[0][0]

    # Create and update field-tag mapping
    run_sql(
        """
        UPDATE field_tag
        SET id_field = %s
        WHERE id_field = %s
        """,
        (field_simpleauthor_id, field_author_id)
    )
    run_sql(
        """
        UPDATE field_tag
        SET id_field = %s
        WHERE id_field = %s
        """,
        (field_exactsimpleauthor_id, field_exactauthor_id)
    )
    run_sql(
        """
        INSERT INTO field_tag (id_field, id_tag)
        VALUES (%s, %s)
        """,
        (field_datasource_id, tag_datasource_id)
    )

    # Create and update indexes
    run_sql(
        """
        UPDATE idxINDEX
        SET
            description = 'This index contains words/phrases from author indexes.',
            tokenizer = 'BibIndexEmptyTokenizer'
        WHERE name = 'author'
        """
    )
    index_author_id = run_sql(
        """
        SELECT id FROM idxINDEX
        WHERE name = 'author'
        """
    )[0][0]
    index_last_used_id = run_sql("""SELECT MAX(id) FROM idxINDEX""")[0][0]
    index_simpleauthor_id = index_last_used_id = run_sql(
        """
        INSERT INTO idxINDEX
        SET
            id = %s,
            name = 'simpleauthor',
            description = 'This index contains fuzzy words/phrases from author fields.',
            tokenizer = 'BibIndexAuthorTokenizer'
        """,
        (index_last_used_id + 1,)
    )
    index_canonicalauthor_id = index_last_used_id = run_sql(
        """
        INSERT INTO idxINDEX
        SET
            id = %s,
            name = 'canonicalauthor',
            description = 'This index contains canonical author ids from the record',
            tokenizer = 'BibIndexCanonicalAuthorTokenizer'
        """,
        (index_last_used_id + 1,)
    )
    index_parentauthor_id = index_last_used_id = run_sql(
        """
        INSERT INTO idxINDEX
        SET
            id = %s,
            name = 'parentauthor',
            description = 'This index contains fuzzy words/phrases from the parent record author fields.',
            tokenizer = 'BibIndexParentAuthorTokenizer'
        """,
        (index_last_used_id + 1,)
    )
    index_parentcanonicalauthor_id = index_last_used_id = run_sql(
        """
        INSERT INTO idxINDEX
        SET
            id = %s,
            name = 'parentcanonicalauthor',
            description = 'This index contains canonical author ids from the parent record.',
            tokenizer = 'BibIndexParentCanonicalAuthorTokenizer'
        """,
        (index_last_used_id + 1,)
    )
    run_sql(
        """
        UPDATE idxINDEX
        SET
            description = 'This index contains words/phrases from exact author indexes.',
            tokenizer = 'BibIndexEmptyTokenizer'
        WHERE name = 'exactauthor'
        """
    )
    index_exactauthor_id = run_sql(
        """
        SELECT id FROM idxINDEX
        WHERE name = 'exactauthor'
        """
    )[0][0]
    index_exactsimpleauthor_id = index_last_used_id = run_sql(
        """
        INSERT INTO idxINDEX
        SET
            id = %s,
            name = 'exactsimpleauthor',
            description = 'This index contains exact words/phrases from author fields.',
            tokenizer = 'BibIndexExactAuthorTokenizer'
        """,
        (index_last_used_id + 1,)
    )
    index_exactparentauthor_id = index_last_used_id = run_sql(
        """
        INSERT INTO idxINDEX
        SET
            id = %s,
            name = 'exactparentauthor',
            description = 'This index contains exact words/phrases from the parent record author fields.',
            tokenizer = 'BibIndexExactParentAuthorTokenizer'
        """,
        (index_last_used_id + 1,)
    )

    # Create index tables
    for index_type in ["WORD", "PAIR", "PHRASE"]:
        # Virtual index tables
        for index_id in [index_author_id, index_exactauthor_id]:
            _create_index_queue_table(index_type, index_id)
            # The front and rear tables already exist

        # Regular index tables
        for index_id in [index_simpleauthor_id,
                         index_canonicalauthor_id,
                         index_parentauthor_id,
                         index_parentcanonicalauthor_id,
                         index_exactsimpleauthor_id,
                         index_exactparentauthor_id]:
            _create_index_front_table(index_type, index_id)
            _create_index_rear_table(index_type, index_id)

    # Create index-field mapping
    run_sql(
        """
        INSERT INTO idxINDEX_field (id_idxINDEX, id_field)
        VALUES (%s, %s)
        """,
        (index_simpleauthor_id, field_simpleauthor_id)
    )
    run_sql(
        """
        INSERT INTO idxINDEX_field (id_idxINDEX, id_field)
        VALUES (%s, %s)
        """,
        (index_parentauthor_id, field_datasource_id)
    )
    run_sql(
        """
        INSERT INTO idxINDEX_field (id_idxINDEX, id_field)
        VALUES (%s, %s)
        """,
        (index_parentcanonicalauthor_id, field_datasource_id)
    )
    run_sql(
        """
        INSERT INTO idxINDEX_field (id_idxINDEX, id_field)
        VALUES (%s, %s)
        """,
        (index_exactsimpleauthor_id, field_exactsimpleauthor_id)
    )
    run_sql(
        """
        INSERT INTO idxINDEX_field (id_idxINDEX, id_field)
        VALUES (%s, %s)
        """,
        (index_exactparentauthor_id, field_datasource_id)
    )

    # Create virtual index mappig
    new_virtual_index_mappings = [
        (index_author_id, index_simpleauthor_id),
        (index_author_id, index_canonicalauthor_id),
        (index_author_id, index_parentauthor_id),
        (index_author_id, index_parentcanonicalauthor_id),
        (index_exactauthor_id, index_exactsimpleauthor_id),
        (index_exactauthor_id, index_canonicalauthor_id),
        (index_exactauthor_id, index_exactparentauthor_id),
        (index_exactauthor_id, index_parentcanonicalauthor_id)
    ]
    for id_virtual, id_normal in new_virtual_index_mappings:
        run_sql(
            """
            INSERT INTO idxINDEX_idxINDEX (id_virtual, id_normal)
            VALUES (%s, %s)
            """,
            (index_author_id, index_simpleauthor_id)
        )


def estimate():
    """  Estimate running time of upgrade in seconds. """
    return 10


def _create_index_queue_table(index_type, index_id):
    table_name = "idx%s%02dQ" % (index_type, index_id)
    return run_sql(
        """
        CREATE TABLE IF NOT EXISTS %s (
            id mediumint(10) unsigned NOT NULL auto_increment,
            runtime datetime NOT NULL default '0000-00-00 00:00:00',
            id_bibrec_low mediumint(9) unsigned NOT NULL,
            id_bibrec_high mediumint(9) unsigned NOT NULL,
            index_name varchar(50) NOT NULL default '',
            mode varchar(50) NOT NULL default 'update',
            PRIMARY KEY (id),
            INDEX (index_name),
            INDEX (runtime)
        ) ENGINE=MyISAM;
        """ % (table_name,)
    )


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
