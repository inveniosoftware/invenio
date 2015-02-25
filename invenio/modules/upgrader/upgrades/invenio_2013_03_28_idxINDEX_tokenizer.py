# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2012, 2013 CERN.
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


from invenio.legacy.dbquery import run_sql

depends_on = ['invenio_2013_03_25_idxINDEX_html_markup']

def info():
    return "Introduces new columns for idxINDEX table: tokenizer"


def do_upgrade():
    #first step: change table
    stmt = run_sql('SHOW CREATE TABLE idxINDEX')[0][1]
    if '`tokenizer` varchar(50)' not in stmt:
        run_sql("ALTER TABLE idxINDEX ADD COLUMN tokenizer varchar(50) NOT NULL default '' AFTER remove_latex_markup")
    #second step: update table
    run_sql("""UPDATE idxINDEX SET tokenizer='BibIndexDefaultTokenizer' WHERE name IN
                            ('global', 'collection', 'abstract', 'keyword',
                             'reference', 'reportnumber', 'title', 'collaboration',
                             'affiliation', 'caption', 'exacttitle')""")
    run_sql("""UPDATE idxINDEX SET tokenizer='BibIndexAuthorTokenizer' WHERE name IN
                            ('author', 'firstauthor')""")
    run_sql("""UPDATE idxINDEX SET tokenizer='BibIndexExactAuthorTokenizer' WHERE name IN
                            ('exactauthor', 'exactfirstauthor')""")
    run_sql("""UPDATE idxINDEX SET tokenizer='BibIndexFulltextTokenizer' WHERE name='fulltext'""")
    run_sql("""UPDATE idxINDEX SET tokenizer='BibIndexAuthorCountTokenizer' WHERE name='authorcount'""")
    run_sql("""UPDATE idxINDEX SET tokenizer='BibIndexJournalTokenizer' WHERE name='journal'""")
    run_sql("""UPDATE idxINDEX SET tokenizer='BibIndexYearTokenizer' WHERE name='year'""")
    run_sql("""UPDATE idxINDEX SET tokenizer='BibIndexDefaultTokenizer' WHERE tokenizer = ''""")


def estimate():
    return 1

def pre_upgrade():
    pass

def post_upgrade():
    pass
