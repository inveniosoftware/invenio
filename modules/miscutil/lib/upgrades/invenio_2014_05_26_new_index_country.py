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
    return "New index country."


def estimate():
    """ Return estimate of upgrade time in seconds """
    return 2


def do_upgrade():
    pass


def do_upgrade_atlantis():
    # Index and index tables
    index_last_used_id = run_sql("""SELECT MAX(id) FROM idxINDEX""")[0][0]
    index_id = run_sql(
        """
        INSERT INTO idxINDEX
        SET
            id = %s,
            name = 'country',
            description = 'This index contains country names of the affiliated institutes of the authors',
            last_updated = '0000-00-00 00:00:00',
            stemming_language = '',
            indexer = 'native',
            synonym_kbrs = '',
            remove_stopwords = 'No',
            remove_html_markup = 'No',
            remove_latex_markup = 'No',
            tokenizer = 'BibIndexCountryTokenizer'
        """,
        (index_last_used_id + 1,)
    )

    run_sql(
        """
        CREATE TABLE IF NOT EXISTS idxWORD%02dF (
          id mediumint(9) unsigned NOT NULL auto_increment,
          term varchar(50) default NULL,
          hitlist longblob,
          PRIMARY KEY  (id),
          UNIQUE KEY term (term)
        ) ENGINE=MyISAM;
        """ % index_id
    )
    run_sql(
        """
        CREATE TABLE IF NOT EXISTS idxWORD%02dR (
          id_bibrec mediumint(9) unsigned NOT NULL,
          termlist longblob,
          type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
          PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """ % index_id
    )
    run_sql(
        """
        CREATE TABLE IF NOT EXISTS idxPAIR%02dF (
          id mediumint(9) unsigned NOT NULL auto_increment,
          term varchar(100) default NULL,
          hitlist longblob,
          PRIMARY KEY  (id),
          UNIQUE KEY term (term)
        ) ENGINE=MyISAM;
        """ % index_id
    )
    run_sql(
        """
        CREATE TABLE IF NOT EXISTS idxPAIR%02dR (
          id_bibrec mediumint(9) unsigned NOT NULL,
          termlist longblob,
          type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
          PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """ % index_id
    )
    run_sql(
        """
        CREATE TABLE IF NOT EXISTS idxPHRASE%02dF (
          id mediumint(9) unsigned NOT NULL auto_increment,
          term text default NULL,
          hitlist longblob,
          PRIMARY KEY  (id),
          KEY term (term(50))
        ) ENGINE=MyISAM;
        """ % index_id
    )
    run_sql(
        """
        CREATE TABLE IF NOT EXISTS idxPHRASE%02dR (
          id_bibrec mediumint(9) unsigned NOT NULL,
          termlist longblob,
          type enum('CURRENT','FUTURE','TEMPORARY') NOT NULL default 'CURRENT',
          PRIMARY KEY (id_bibrec,type)
        ) ENGINE=MyISAM;
        """ % index_id
    )

    # Field and index to field mapping
    field_id = run_sql(
        """
        INSERT INTO field
        SET
            name = 'country',
            code = 'country'
        """
    )

    run_sql(
        """
        INSERT INTO idxINDEX_field (id_idxINDEX, id_field)
        VALUES (%d,%d)
        """,
        (index_id, field_id)
    )

    # Tags
    tag_100__u_id = run_sql(
        """
        SELECT id FROM tag
        WHERE value = '100__u'
        """
    )
    tag_700__u_id = run_sql(
        """
        SELECT id FROM tag
        WHERE value = '700__u'
        """
    )
    tag_110__u_id = run_sql(
        """
        INSERT INTO tag
        SET
            name = 'SPIRES name'
            value = '110__u'
        """
    )
    tag_371__d_id = run_sql(
        """
        INSERT INTO tag
        SET
            name = 'country name'
            value = '371__d'
        """
    )
    tag_371__g_id = run_sql(
        """
        INSERT INTO tag
        SET
            name = 'country code'
            value = '371__g'
        """
    )
    tag_371__x_id = run_sql(
        """
        INSERT INTO tag
        SET
            name = 'extra'
            value = '371__x'
        """
    )

    # Tags to field mpping
    run_sql(
        """
        INSERT INTO field_tag (id_field, id_tag, score) VALUES (%d, %d, 10)
        """,
        (field_id, tag_100__u_id)
    )
    run_sql(
        """
        INSERT INTO field_tag (id_field, id_tag, score) VALUES (%d, %d, 10)
        """,
        (field_id, tag_700__u_id)
    )
    run_sql(
        """
        INSERT INTO field_tag (id_field, id_tag, score) VALUES (%d, %d, 10)
        """,
        (field_id, tag_110__u_id)
    )
    run_sql(
        """
        INSERT INTO field_tag (id_field, id_tag, score) VALUES (%d, %d, 10)
        """,
        (field_id, tag_371__d_id)
    )
    run_sql(
        """
        INSERT INTO field_tag (id_field, id_tag, score) VALUES (%d, %d, 10)
        """,
        (field_id, tag_371__g_id)
    )
    run_sql(
        """
        INSERT INTO field_tag (id_field, id_tag, score) VALUES (%d, %d, 10)
        """,
        (field_id, tag_371__x_id)
    )
