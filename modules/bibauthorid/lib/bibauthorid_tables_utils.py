# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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
"""
bibauthorid_tables_utils
    Bibauthorid's DB handler
"""
import sys
import re
import random

import bibauthorid_config as bconfig
import bibauthorid_structs as dat

from bibauthorid_utils import split_name_parts, create_normalized_name
from bibauthorid_utils import clean_name_string
from bibauthorid_authorname_utils import update_doclist

try:
    from search_engine import get_record
    from search_engine import get_fieldvalues
    from bibrank_citation_searcher import get_citation_dict
    from dbquery import run_sql, run_sql_many
    from dbquery import OperationalError, ProgrammingError
except ImportError:
    from invenio.search_engine import get_fieldvalues
    from invenio.search_engine import get_record
    from invenio.bibrank_citation_searcher import get_citation_dict
    from invenio.dbquery import run_sql, run_sql_many
    from invenio.dbquery import OperationalError, ProgrammingError

try:
    import unidecode
    UNIDECODE_ENABLED = True
except ImportError:
    bconfig.LOGGER.error("Authorid will run without unidecode support! "
                         "This is not recommended! Please install unidecode!")
    UNIDECODE_ENABLED = False


def get_papers_recently_modified(date=''):
    '''
    Returns the bibrecs with modification date more recent then date, or all
    the bibrecs if no date is specified.
    @param date: date
    '''
    papers = run_sql("select id from bibrec where  modification_date > %s",
                     (str(date),))
    if papers:
        bibrecs = [i[0] for i in papers]
        bibrecs.append(-1)
        min_date = run_sql("select max(modification_date) from bibrec where "
                           "id in %s", (tuple(bibrecs),))
    else:
        min_date = run_sql("select now()")
    return papers, min_date


def populate_authornames_bibrefs_from_authornames():
    '''
    Populates aidAUTHORNAMESBIBREFS.

    For each entry in aidAUTHORNAMES creates a corresponding entry in aidA.B. so it's possible to search
    by bibrec/bibref at a reasonable speed as well and not only by name.
    '''
    nids = run_sql("select id,bibrefs from aidAUTHORNAMES")
    for nid in nids:
        for bibref in nid[1].split(','):
            if bconfig.TABLES_UTILS_DEBUG:
                print ('populate_authornames_bibrefs_from_authornames: Adding: '
                       ' %s %s' % (str(nid[0]), str(bibref)))

            run_sql("insert into aidAUTHORNAMESBIBREFS (Name_id, bibref) "
                    "values (%s,%s)", (str(nid[0]), str(bibref)))

def authornames_tables_gc(bunch_size=50):
    '''
    Performs garbage collecting on the authornames tables.
    Potentially really slow.
    '''
    bunch_start = run_sql("select min(id) from aidAUTHORNAMESBIBREFS")
    if len(bunch_start) >= 1:
        bunch_start = int(bunch_start[0][0])
    else:
        return

    abfs_ids_bunch = run_sql("select id,Name_id,bibref from aidAUTHORNAMESBIBREFS limit %s, %s"
                            , (str(bunch_start - 1), str(bunch_size)))
    bunch_start += bunch_size

    while len(abfs_ids_bunch) >= 1:
        bib100list = []
        bib700list = []
        for i in abfs_ids_bunch:
            if i[2].split(':')[0] == '100':
                bib100list.append(i[2].split(':')[1])
            elif i[2].split(':')[0] == '700':
                bib700list.append(i[2].split(':')[1])

        bib100liststr = '( '
        for i in bib100list:
            bib100liststr += "'" + str(i) + "',"
        bib100liststr = bib100liststr[0:len(bib100liststr) - 1] + " )"

        bib700liststr = '( '
        for i in bib700list:
            bib700liststr += "'" + str(i) + "',"
        bib700liststr = bib700liststr[0:len(bib700liststr) - 1] + " )"

        if len(bib100list) >= 1:
            bib10xids = run_sql("select id from bib10x where id in %s"
                                % bib100liststr)
        else:
            bib10xids = []

        if len(bib700list) >= 1:
            bib70xids = run_sql("select id from bib70x where id in %s"
                                % bib700liststr)
        else:
            bib70xids = []

        bib10xlist = []
        bib70xlist = []

        for i in bib10xids:
            bib10xlist.append(str(i[0]))
        for i in bib70xids:
            bib70xlist.append(str(i[0]))

        bib100junk = set(bib100list).difference(set(bib10xlist))
        bib700junk = set(bib700list).difference(set(bib70xlist))

        idsdict = {}
        for i in abfs_ids_bunch:
            idsdict[i[2]] = [i[0], i[1]]

        junklist = []
        for i in bib100junk:
            junklist.append('100:' + i)
        for i in bib700junk:
            junklist.append('700:' + i)

        for junkref in junklist:
            try:
                id_to_remove = idsdict[junkref]

                run_sql("delete from aidAUTHORNAMESBIBREFS where id=%s",
                        (str(id_to_remove[0]),))
                if bconfig.TABLES_UTILS_DEBUG:
                    print "authornames_tables_gc: idAUTHORNAMESBIBREFS deleting row " + str(id_to_remove)
                authrow = run_sql("select id,Name,bibrefs,db_name from aidAUTHORNAMES where id=%s", (str(id_to_remove[1]),))
                if len(authrow[0][2].split(',')) == 1:
                    run_sql("delete from aidAUTHORNAMES where id=%s", (str(id_to_remove[1]),))
                    if bconfig.TABLES_UTILS_DEBUG:
                        print "authornames_tables_gc: aidAUTHORNAMES deleting " + str(authrow)
                else:
                    bibreflist = ''
                    for ref in authrow[0][2].split(','):
                        if ref != junkref:
                            bibreflist += ref + ','
                    bibreflist = bibreflist[0:len(bibreflist) - 1]
                    run_sql("update aidAUTHORNAMES set bibrefs=%s where id=%s",
                            (bibreflist, id_to_remove[1]))
                    if bconfig.TABLES_UTILS_DEBUG:
                        print "authornames_tables_gc: aidAUTHORNAMES updating " + str(authrow) + ' with ' + str(bibreflist)
            except:
                pass


        abfs_ids_bunch = run_sql("select id,Name_id,bibref from aidAUTHORNAMESBIBREFS limit %s,%s" ,
                            (str(bunch_start - 1), str(bunch_size)))
        bunch_start += bunch_size


def update_authornames_tables_from_paper(papers_list=[]):
    """
    Updates the authornames tables with the names on the given papers list
    @param papers_list: list of the papers which have been updated (bibrecs) ((1,),)

    For each paper of the list gathers all names, bibrefs and bibrecs to be added to aidAUTHORNAMES
    table, taking care of updating aidA.B. as well

    NOTE: update_authornames_tables_from_paper: just to remember: get record would be faster but
        we don't have the bibref there,
        maybe there is a way to rethink everything not to use bibrefs? How to address
        authors then?
    """


    def update_authornames_tables(name, bibref):
        '''
        Update the tables for one bibref,name touple
        '''
        authornames_row = run_sql("select id,Name,bibrefs,db_name from aidAUTHORNAMES where db_name like %s",
                            (str(name),))
        authornames_bibrefs_row = run_sql("select id,Name_id,bibref from aidAUTHORNAMESBIBREFS "
                                        "where bibref like %s", (str(bibref),))

#@XXX: update_authornames_tables: if i'm not wrong there should always be only one result; will be checked further on
        if ((len(authornames_row) > 1) or (len(authornames_bibrefs_row) > 1) or
            (len(authornames_row) < len(authornames_bibrefs_row))):
            if bconfig.TABLES_UTILS_DEBUG:
                print "update_authornames_tables: More then one result or missing authornames?? Something is wrong, not updating" + str(authornames_row) + str(authornames_bibrefs_row)
                return

        if len(authornames_row) == 1:
#            we have an hit for the name string; check if there is the 'new' bibref associated,
#            if yes there is nothing to do, otherwise shold add it here and in the ANbibrefs table
            if authornames_row[0][2].count(bibref) < 1:
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_authornames_tables: Adding new bibref to ' + str(authornames_row) + ' ' + str(name) + ' ' + str(bibref)
                run_sql("update aidAUTHORNAMES set bibrefs=%s where id=%s",
                            (authornames_row[0][2] + ',' + str(bibref), authornames_row[0][0]))
                if len(authornames_bibrefs_row) < 1:
#                we have to add the bibref to the name, would be strange if it would be already there
                    run_sql("insert into aidAUTHORNAMESBIBREFS  (Name_id,bibref) values (%s,%s)",
                        (authornames_row[0][0], str(bibref)))
            else:
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_authornames_tables: Nothing to add to ' + str(authornames_row) + ' ' + str(name) + ' ' + str(bibref)


        else:
#@NOTE: update_authornames_tables: we don't have the name string in the db: the name associated to the bibref is changed
#            or this is a new name? Experimenting with bibulpload looks like if a name on a paper changes a new bibref is created;
#
            if len(authornames_bibrefs_row) == 1:
#               If len(authornames_row) is zero but we have a row in authornames_bibrefs_row means that
#               the name string is changed, somehow!
#               @FIXME: update_authornames_tables: this case should really be considered?
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_authornames_tables: The name associated to the bibref is changed?? ' + str(name) + ' ' + str(bibref)

            else:
                artifact_removal = re.compile("[^a-zA-Z0-9]")
                authorname = ""

                test_name = name.decode('utf-8')

                if UNIDECODE_ENABLED:
                    test_name = unidecode.unidecode(name.decode('utf-8'))

                raw_name = artifact_removal.sub("", test_name)

                if len(raw_name) > 1:
                    authorname = name.decode('utf-8')

                if len(raw_name) > 1:
                    dbname = authorname
                else:
                    dbname = 'Error in name parsing!'

                clean_name = create_normalized_name(split_name_parts(name))
                authornamesid = run_sql("insert into aidAUTHORNAMES (Name,bibrefs,db_name) values (%s,%s,%s)",
                                (clean_name, str(bibref), dbname))
                run_sql("insert into aidAUTHORNAMESBIBREFS  (Name_id,bibref) values (%s,%s)",
                        (authornamesid, str(bibref)))
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_authornames_tables: Created new name ' + str(authornamesid) + ' ' + str(name) + ' ' + str(bibref)

    tables = [['bibrec_bib10x', 'bib10x', '100__a', '100'], ['bibrec_bib70x', 'bib70x', '700__a', '700']]
    for paper in papers_list:
        for table in tables:
            sqlstr = "select id_bibxxx from %s where id_bibrec=" % table[0]
            bibrefs = run_sql(sqlstr+"%s", (str(paper[0]),))
            for ref in bibrefs:
                sqlstr = "select value from %s where tag='%s' and id=" % (table[1], table[2])
                name = run_sql(sqlstr+"%s", (str(ref[0]),))
                if len(name) >= 1:
                    update_authornames_tables(name[0][0], table[3] + ':' + str(ref[0]))


def populate_authornames():
    """
    Author names table population from bib10x and bib70x
    Average Runtime: 376.61 sec (6.27 min) for 327k entries
    Should be called only with empty table, then use
    update_authornames_tables_from_paper with the new papers which
    are coming in or modified.
    """
    max_rows_per_run = bconfig.TABLE_POPULATION_BUNCH_SIZE

    if max_rows_per_run == -1:
        max_rows_per_run = 5000

    max100 = run_sql("SELECT COUNT(id) FROM bib10x WHERE tag = '100__a'")
    max700 = run_sql("SELECT COUNT(id) FROM bib70x WHERE tag = '700__a'")

    tables = "bib10x", "bib70x"
    authornames_is_empty_checked = 0
    authornames_is_empty = 1

#    Bring author names from bib10x and bib70x to authornames table

    for table in tables:

        if table == "bib10x":
            table_number = "100"
        else:
            table_number = "700"

        querylimiter_start = 0
        querylimiter_max = eval('max' + str(table_number) + '[0][0]')
        if bconfig.TABLES_UTILS_DEBUG:
            print "\nProcessing %s (%s entries):" % (table, querylimiter_max)
            sys.stdout.write("0% ")
            sys.stdout.flush()

        while querylimiter_start <= querylimiter_max:
            if bconfig.TABLES_UTILS_DEBUG:
                sys.stdout.write(".")
                sys.stdout.flush()
                percentage = int(((querylimiter_start + max_rows_per_run) * 100)
                                   / querylimiter_max)
                sys.stdout.write(".%s%%." % (percentage))
                sys.stdout.flush()

#            Query the Database for a list of authors from the correspondent
#            tables--several thousands at a time
            bib = run_sql("SELECT id, value FROM %s WHERE tag = '%s__a' "
                          "LIMIT %s, %s" % (table, table_number,
                                       querylimiter_start, max_rows_per_run))

            authorexists = None

            querylimiter_start += max_rows_per_run

            for i in bib:

                # For mental sanity, exclude things that are not names...
                # Yes, I know that there are strange names out there!
                # Yes, I read the 40 misconceptions about names.
                # Yes, I know!
                # However, these statistical outlaws are harmful.
                artifact_removal = re.compile("[^a-zA-Z0-9]")
                authorname = ""

                if not i[1]:
                    continue

                test_name = i[1].decode('utf-8')

                if UNIDECODE_ENABLED:
                    test_name = unidecode.unidecode(i[1].decode('utf-8'))

                raw_name = artifact_removal.sub("", test_name)

                if len(raw_name) > 1:
                    authorname = i[1].decode('utf-8')

                if not authorname:
                    continue

                if not authornames_is_empty_checked:
                    authornames_is_empty = run_sql("SELECT COUNT(id) "
                                                   "FROM aidAUTHORNAMES")
                    if authornames_is_empty[0][0] == 0:
                        authornames_is_empty_checked = 1
                        authornames_is_empty = 1

                if not authornames_is_empty:
#                    Find duplicates in the database and append id if
#                    duplicate is found
                    authorexists = run_sql("SELECT id, name, bibrefs, db_name "
                                           "FROM aidAUTHORNAMES "
                                           "WHERE db_name = %s",
                                           (authorname.encode("utf-8"),))


                bibrefs = "%s:%s" % (table_number, i[0])

                if not authorexists:
                    insert_name = ""

                    if len(authorname) > 240:
                        bconfig.LOGGER.warn("\nName too long, truncated to 254"
                                            " chars: %s" % (authorname))
                        insert_name = authorname[0:254]
                    else:
                        insert_name = authorname

                    cnn = create_normalized_name
                    snp = split_name_parts

                    aid_name = authorname

                    if UNIDECODE_ENABLED:
                        aid_name = cnn(snp(unidecode.unidecode(insert_name)))
                        aid_name = aid_name.replace("\"", "")
                    else:
                        aid_name = cnn(snp(insert_name))
                        aid_name = aid_name.replace(u"\u201c", "")
                        aid_name = aid_name.replace(u"\u201d", "")

                    run_sql("INSERT INTO aidAUTHORNAMES VALUES"
                            " (NULL, %s, %s, %s)",
                            (aid_name.encode('utf-8'), bibrefs,
                             insert_name.encode('utf-8')))

                    if authornames_is_empty:
                        authornames_is_empty = 0
                else:
                    if authorexists[0][2].count(bibrefs) >= 0:
                        upd_bibrefs = "%s,%s" % (authorexists[0][2], bibrefs)
                        run_sql("UPDATE aidAUTHORNAMES SET bibrefs = "
                                "%s WHERE id = %s",
                                (upd_bibrefs, authorexists[0][0]))
        if bconfig.TABLES_UTILS_DEBUG:
            sys.stdout.write(" Done.")
            sys.stdout.flush()


def get_bibref_name_string(bibref):
    '''
    Returns the name string associated with the given bibref
    @param: bibref ((100:123,),)
    '''
    name = run_sql("select db_name from aidAUTHORNAMES where id=(select Name_id from aidAUTHORNAMESBIBREFS where bibref=%s)", (str(bibref[0][0]),))
    if len(name) > 0:
        return name[0][0]
    else:
        return ''


def get_bibrefs_from_name_string(string):
    '''
    Returns bibrefs associated to a name string
    @param: string: name
    '''
    bibrefs = run_sql("select bibrefs from aidAUTHORNAMES where db_name=%s ", (str(string),))
    return bibrefs


def get_diff_marc10x70x_to_anames():
    '''
    Determines the difference between the union of bib10x and bib70x and the
    aidAUTHORNAMES table.
    It will return the entries which are present in bib10x and bib70x but not
    in aidAUTHORNAMES. Meant to be run periodically.

    @todo: get_diff_marc10x70x_to_anames: find meaningful use for the
        returned results.
    @return: a list of the author names not contained in the authornames table
    @rtype: list
    '''
    run_sql("DROP VIEW authors")
    run_sql("create view authors AS \
        (SELECT value FROM bib10x WHERE tag =\"100__a\") \
        UNION \
        (SELECT value FROM bib70x WHERE tag =\"700__a\")")
    diff = run_sql("SELECT value from authors LEFT JOIN aidAUTHORNAMES as b"
                   + " ON (authors.value = b.Name) WHERE b.name IS NULL")
    return diff


def populate_doclist_for_author_surname(surname, surname_variations=None):
    """
    Searches for all the documents containing a given surname and processes
    them: creates the virtual author for each author on a document.

    @param surname: The search is based on this last name.
    @type surname: string
    """
#    if not dat.CITES_DICT:
#        cites = get_citation_dict("citationdict")
#
#        for key in cites:
#            dat.CITES_DICT[key] = cites[key]
#
#    if not dat.CITED_BY_DICT:
#        cited_by = get_citation_dict("reversedict")
#
#        for key in cited_by:
#            dat.CITED_BY_DICT[key] = cited_by[key]

    bconfig.LOGGER.log(25, "Populating document list for %s" % (surname))

    if surname_variations:
        init_authornames(surname, surname_variations)
    else:
        init_authornames(surname)

    authors = [row for row in dat.AUTHOR_NAMES if not row['processed']]

    for author in authors:
        marc_100 = []
        marc_700 = []
        temp_marc = author['bibrefs'].split(',')

        for j in temp_marc:
            marcfield, internalid = j.split(':')

            if marcfield == '100':
                marc_100.append(internalid)
            elif marcfield == '700':
                marc_700.append(internalid)
            else:
                bconfig.LOGGER.error("Wrong MARC field. How did you do"
                                     " that?!--This should never happen! boo!")
        bibrecs = []

        if marc_100:
            for m100 in marc_100:
                refinfo = run_sql("SELECT id_bibrec FROM bibrec_bib10x "
                                  "WHERE id_bibxxx = %s", (m100,))

                if refinfo:
                    for recid in refinfo:
                        bibrecs.append((recid[0], "100:%s" % m100))

        if marc_700:
            for m700 in marc_700:
                refinfo = run_sql("SELECT id_bibrec FROM bibrec_bib70x "
                                  "WHERE id_bibxxx = %s", (m700,))

                if refinfo:
                    for recid in refinfo:
                        bibrecs.append((recid[0], "700:%s" % m700))

        relevant_records = []

        for bibrec in bibrecs:
            go_next = False

            for value in get_fieldvalues(bibrec[0], "980__c"):
                if value.lower().count('delete'):
                    go_next = True

            if go_next:
                continue

            for value in get_fieldvalues(bibrec[0], "980__a"):
                if value.lower().count('delet'):
                    go_next = True

                if bconfig.EXCLUDE_COLLECTIONS:
                    if value in bconfig.EXCLUDE_COLLECTIONS:
                        go_next = True
                        break

                if bconfig.LIMIT_TO_COLLECTIONS:
                    if not value in bconfig.LIMIT_TO_COLLECTIONS:
                        go_next = True
                    else:
                        go_next = False
                        break

            if go_next:
                continue

            relevant_records.append(bibrec)

        if load_records_to_mem_cache([br[0] for br in relevant_records]):
            for bibrec in relevant_records:
                update_doclist(bibrec[0], author['id'], bibrec[1])


def load_records_to_mem_cache(bibrec_ids):
    '''
    Loads all the records specified in the list into the memory storage
    facility. It will try to attach citation information to each record in
    the process.

    @param bibrec_ids: list of bibrec IDs to load to memory
    @type bibrec_ids: list

    @return: Success (True) or failure (False) of the process
    @rtype: boolean
    '''
    if not bibrec_ids:
        return False

    for bibrec in bibrec_ids:
        if not bibrec in dat.RELEVANT_RECORDS:
            rec = get_record(bibrec)

            if bconfig.LIMIT_AUTHORS_PER_DOCUMENT:
                is_collaboration = False
                authors = 0

                try:
                    for field in rec['710'][0][0]:
                        if field[0] == 'g':
                            is_collaboration = True
                            break
                except KeyError:
                    pass

                if is_collaboration:
                    # If experimentalists shall be excluded uncomment
                    # the following line
                    #continue
                    pass
                else:
                    try:
                        for field in rec['100'][0][0]:
                            if field[0] == 'a':
                                authors += 1
                                break
                    except KeyError:
                        pass

                    try:
                        for coauthor in rec['700']:
                            if coauthor[0][0][0] == 'a':
                                authors += 1
                    except KeyError:
                        pass

                    if authors > bconfig.MAX_AUTHORS_PER_DOCUMENT:
                        continue

            dat.RELEVANT_RECORDS[bibrec] = rec
            cites = []
            cited_by = []

            try:
#                cites = dat.CITES_DICT[bibrec]
                cites = get_citation_dict("citationdict")[bibrec]
            except KeyError:
                pass

            try:
#                cited_by = dat.CITED_BY_DICT[bibrec]
                cited_by = get_citation_dict("reversedict")[bibrec]
            except KeyError:
                pass

            dat.RELEVANT_RECORDS[bibrec]['cites'] = cites
            dat.RELEVANT_RECORDS[bibrec]['cited_by'] = cited_by

    return True


def init_authornames(surname, lastname_variations=None):
    '''
    Initializes the AUTHOR_NAMES memory storage

    @param surname: The surname to search for
    @type surname: string
    '''

    if len(dat.AUTHOR_NAMES) > 0:
        existing = [row for row in dat.AUTHOR_NAMES
                   if row['name'].split(",")[0] == surname]

        if existing:
            bconfig.LOGGER.log(25, "AUTHOR_NAMES already holds the "
                               "correct data.")
        else:
            bconfig.LOGGER.debug("AUTHOR_NAMES will have additional content")
            for updated in [row for row in dat.AUTHOR_NAMES
                            if not row['processed']]:
                updated['processed'] = True
            _perform_authornames_init(surname)
    else:
        _perform_authornames_init(surname, lastname_variations)


def _perform_authornames_init(surname, lastname_variations=None):
    '''
    Performs the actual AUTHOR_NAMES memory storage init by reading values
    from the database

    @param surname: The surname to search for
    @type surname: string
    '''
    db_authors = None

    if len(surname) < 4 and not lastname_variations:
        lastname_variations = [surname]

    if (not lastname_variations
        or (lastname_variations
            and [nm for nm in lastname_variations if nm.count("\\")])):

        sql_query = (r"SELECT id, name, bibrefs, db_name FROM aidAUTHORNAMES "
                     "WHERE name REGEXP %s")

        if (lastname_variations
            and [nm for nm in lastname_variations if nm.count("\\")]):
            x = sorted(lastname_variations, key=lambda k:len(k), reverse=True)
            # In order to fight escaping problems, we fall back to regexp mode
            # if we find a backslash somewhere.
            surname = x[0]

        # instead of replacing with ' ', this will construct the regex for the
        # SQL query as well as the next if statements.
        surname = clean_name_string(surname,
                                    replacement="[^0-9a-zA-Z]{0,2}",
                                    keep_whitespace=False)

        if not surname.startswith("[^0-9a-zA-Z]{0,2}"):
            surname = "[^0-9a-zA-Z]{0,2}%s" % (surname)

        if not surname.startswith("^"):
            surname = "^%s" % surname

        surname = surname + "[^0-9a-zA-Z ]{1,2}"

        if surname.count("\\"):
            surname.replace("\\", ".")

        try:
            db_authors = run_sql(sql_query, (surname,))
        except (OperationalError, ProgrammingError), emsg:
            bconfig.LOGGER.exception("Not able to select author name: %s" % emsg)

    else:
        qnames = []
        vari_query = ""

        for vname in lastname_variations:
            if vari_query:
                vari_query += " OR"
            vari_query += ' name like %s'
            vname_r = r"""%s""" % vname
            qnames.append(vname_r + ", %")

        if not vari_query:
            return

        sql_query = ("SELECT id, name, bibrefs, db_name "
                     "FROM aidAUTHORNAMES WHERE" + vari_query)
        try:
            db_authors = run_sql(sql_query, tuple(qnames))
        except (OperationalError, ProgrammingError), emsg:
            bconfig.LOGGER.exception("Not able to select author name: %s" % emsg)

    if not db_authors:
        return

    for author in db_authors:
        dat.AUTHOR_NAMES.append({'id': author[0],
                                 'name': author[1].decode('utf-8'),
                                 'bibrefs': author[2],
                                 'db_name': author[3].decode('utf-8'),
                                 'processed': False})


def find_all_last_names():
    '''
    Filters out all last names from all names in the database.

    @return: a list of last names
    @rtype: list of strings
    '''
    all_names = run_sql("SELECT Name FROM aidAUTHORNAMES")
    last_names = set()


    for dbname in all_names:
        if not dbname:
            continue

        full_name = dbname[0]
        name = split_name_parts(full_name.decode('utf-8'))[0]

        # For mental sanity, exclude things that are not names...
        #   - Single letter names
        #   - Single number names
        #   - Names containing only numbers and/or symbols
        # Yes, I know that there are strange names out there!
        # Yes, I read the 40 misconceptions about names.
        # Yes, I know!
        # However, these statistical outlaws are harmful to the data set.
        artifact_removal = re.compile("[^a-zA-Z0-9]")
        authorname = None

        test_name = name

        if UNIDECODE_ENABLED:
            test_name = unidecode.unidecode(name)

        raw_name = artifact_removal.sub("", test_name)

        if len(raw_name) > 1:
            authorname = name

        if not authorname:
            continue

        if len(raw_name) > 1:
            last_names.add(authorname)

    del(all_names)
    return list(last_names)


def write_mem_cache_to_tables(sanity_checks=False):
    '''
    Reads every memory cache and writes its contents to the appropriate
    table in the database.

    @param sanity_checks: Perform sanity checks before inserting (i.e. is the
        data already present in the db?) and after the insertion (i.e. is the
        data entered correctly?)
    @type sanity_checks: boolean
    '''
    ra_id_offset = run_sql("SELECT max(realauthorID) FROM"
                           + " aidREALAUTHORS")[0][0]
    va_id_offset = run_sql("SELECT max(virtualauthorID) FROM"
                           + " aidVIRTUALAUTHORS")[0][0]
    cluster_id_offset = run_sql("SELECT max(id) FROM"
                                " aidVIRTUALAUTHORSCLUSTERS")[0][0]

    if not ra_id_offset:
        ra_id_offset = 0

    if not va_id_offset:
        va_id_offset = 0

    if not cluster_id_offset:
        cluster_id_offset = 0

    max_va_id = dat.ID_TRACKER["va_id_counter"]
    if max_va_id <= 1:
        max_va_id = 2
    random_va_id = random.randint(1, max_va_id - 1)
    va_mem_data = [row['value'] for row in dat.VIRTUALAUTHOR_DATA
                   if (row["virtualauthorid"] == random_va_id
                       and row['tag'] == "orig_authorname_id")][0]

    if sanity_checks:
        if va_mem_data:
            check_on_va = run_sql("SELECT id,virtualauthorID,tag,value FROM aidVIRTUALAUTHORSDATA "
                                  "WHERE tag='orig_authorname_id' AND "
                                  "value=%s" , (va_mem_data,))

            if check_on_va:
                bconfig.LOGGER.error("Sanity check reported that the data "
                                     "exists. We'll skip this record for now. "
                                     "Please check the data set manually.")
                return False

    bconfig.LOGGER.log(25, "Writing to persistence layer")
    bconfig.LOGGER.log(25, "Offsets...RA: %s; VA: %s; CL: %s" % (ra_id_offset,
                                                        va_id_offset,
                                                        cluster_id_offset))

#    batch_max = bconfig.TABLE_POPULATION_BUNCH_SIZE

    query = []
    query_prelude = ("INSERT INTO aidVIRTUALAUTHORSCLUSTERS (cluster_name)"
                     " VALUES (%s)")

    for va_cluster in dat.VIRTUALAUTHOR_CLUSTERS:
        encoded_value = None
        not_encoded_value = va_cluster['clustername']

        try:
            if isinstance(not_encoded_value, unicode):
                encoded_value = not_encoded_value[0:59].encode('utf-8')
            elif isinstance(not_encoded_value, str):
                encoded_value = not_encoded_value[0:59]
            else:
                encoded_value = str(not_encoded_value)[0:59]
        except (UnicodeEncodeError, UnicodeDecodeError), emsg:
            bconfig.LOGGER.error("Cluster Data encoding error (%s): %s"
                                 % (type(not_encoded_value), emsg))
            continue

        query.append((encoded_value,))

    if query:
        try:
            run_sql_many(query_prelude, tuple(query))
        except (OperationalError, ProgrammingError), emsg:
            bconfig.LOGGER.critical("Inserting into virtual author "
                                    "cluster table failed: %s" % emsg)
            return False

        query = []

    query_prelude = ("INSERT INTO aidVIRTUALAUTHORSDATA "
                     "(virtualauthorID, tag, value) VALUES "
                     "(%s, %s, %s)")

    for va_data in dat.VIRTUALAUTHOR_DATA:
        encoded_value = None
        not_encoded_value = va_data['value']

        try:
            if isinstance(not_encoded_value, unicode):
                encoded_value = not_encoded_value[0:254].encode('utf-8')
            elif isinstance(not_encoded_value, str):
                encoded_value = not_encoded_value[0:254]
            else:
                encoded_value = str(not_encoded_value)[0:254]
        except (UnicodeEncodeError, UnicodeDecodeError), emsg:
            bconfig.LOGGER.error("VA Data encoding error (%s): %s"
                                 % (type(not_encoded_value), emsg))
            continue

        query.append((va_data['virtualauthorid'] + va_id_offset,
                        va_data['tag'], encoded_value))

    if query:
        try:
            run_sql_many(query_prelude, tuple(query))
        except (OperationalError, ProgrammingError), emsg:
            bconfig.LOGGER.critical("Inserting into virtual author "
                                    "data table failed: %s" % emsg)
            return False

        query = []

    query_prelude = ("INSERT INTO aidVIRTUALAUTHORS "
                     "(virtualauthorID, authornamesID, p, clusterID) "
                     "VALUES (%s, %s, %s, %s)")

    for va_entry in dat.VIRTUALAUTHORS:
        query.append((va_entry['virtualauthorid'] + va_id_offset,
                        va_entry['authornamesid'], va_entry['p'],
                        va_entry['clusterid'] + cluster_id_offset))

    if query:
        try:
            run_sql_many(query_prelude, tuple(query))
        except (OperationalError, ProgrammingError), emsg:
            bconfig.LOGGER.critical("Inserting into virtual author "
                                    "table failed: %s" % emsg)
            return False
        query = []

    query_prelude = ("INSERT INTO aidREALAUTHORDATA "
                      "(realauthorID, tag, value, va_count, "
                      "va_names_p, va_p) VALUES "
                      "(%s, %s, %s, %s, %s, %s)")

    for ra_data in dat.REALAUTHOR_DATA:
        if not ra_data['tag'] == 'outgoing_citation':
            encoded_value = None
            not_encoded_value = ra_data['value']

            try:
                if isinstance(not_encoded_value, unicode):
                    encoded_value = not_encoded_value[0:254].encode('utf-8')
                elif isinstance(not_encoded_value, str):
                    encoded_value = not_encoded_value[0:254]
                else:
                    encoded_value = str(not_encoded_value)[0:254]
            except (UnicodeEncodeError, UnicodeDecodeError), emsg:
                bconfig.LOGGER.error("RA Data encoding error (%s): %s"
                                     % (type(not_encoded_value), emsg))
                continue

            query.append((ra_data['realauthorid'] + ra_id_offset,
                            ra_data['tag'],
                            encoded_value,
                            ra_data['va_count'], ra_data['va_np'],
                            ra_data['va_p']))

    if query:
        try:
            run_sql_many(query_prelude, tuple(query))
        except (OperationalError, ProgrammingError), emsg:
            bconfig.LOGGER.critical("Inserting into real author "
                                    "data table failed: %s" % emsg)
            return False
        query = []

    query_prelude = ("INSERT INTO aidREALAUTHORS "
                  "(realauthorID, virtualauthorID, p) VALUES (%s, %s, %s)")

    for ra_entry in dat.REALAUTHORS:
        query.append((ra_entry['realauthorid'] + ra_id_offset,
                        ra_entry['virtualauthorid'] + va_id_offset,
                        ra_entry['p']))

    if query:
        try:
            run_sql_many(query_prelude, tuple(query))
        except (OperationalError, ProgrammingError), emsg:
            bconfig.LOGGER.critical("Inserting into real author "
                                    "table failed: %s" % emsg)
            return False
        query = []

    query_prelude = ("INSERT INTO aidDOCLIST "
                     "(bibrecID, processed_author) VALUES (%s, %s)")

    for doc in dat.DOC_LIST:
        for processed_author in doc['authornameids']:
            query.append((doc['bibrecid'], processed_author))

    if query:
        try:
            run_sql_many(query_prelude, tuple(query))
        except (OperationalError, ProgrammingError), emsg:
            bconfig.LOGGER.critical("Inserting into doc list "
                                    "table failed: %s" % emsg)
            return False
        query = []

    if sanity_checks:
        if va_mem_data:
            check_on_va = run_sql("SELECT id,virtualauthorID,tag,value FROM aidVIRTUALAUTHORSDATA "
                                  "WHERE tag='orig_authorname_id' AND "
                                  "value=%s" , (va_mem_data,))

            if not check_on_va:
                bconfig.LOGGER.error("Sanity check reported that no data "
                                     " exists in the database after writing "
                                     " to it.")
                return False

    bconfig.LOGGER.log(25, "Everything is now written to the database. "
                       "Thanks. Bye.")

    return True


def get_existing_last_names():
    '''
    Find all authors that have been processed and written to the database.
    Extract all last names from this list and return these last names.
    Especially helpful to exclude these clusters (last names) from a run.

    @return: list of last names
    @rtype: list of strings
    '''
    bconfig.LOGGER.log(25, "Reading info about existing authors from database")
    db_lnames = set()
    db_names = run_sql("select value from aidVIRTUALAUTHORSDATA where"
            + " tag='orig_name_string'")

    for i in db_names:
        db_lnames.add(i[0].split(',')[0])

    del(db_names)
    return list(db_lnames)


def get_len_authornames_bibrefs():
    '''
    Reads the lengths of authornames and bibrefs.
    Used to determine if esstential tables already exist.

    @return: dict({'names':-1, 'bibrefs':-1})
    @rtype: dict
    '''
    lengths = {'names':-1,
               'bibrefs':-1}

    if check_and_create_aid_tables():
        authornames_len = run_sql("SELECT count(id) from aidAUTHORNAMES")
        bibrefs_len = run_sql("SELECT count(id) from aidAUTHORNAMESBIBREFS")

        try:
            lengths['names'] = int(authornames_len[0][0])
            lengths['bibrefs'] = int(bibrefs_len[0][0])
        except (ValueError, TypeError):
            lengths['names'] = -1
            lengths['bibrefs'] = -1

    return lengths


def check_and_create_aid_tables():
    '''
    Checks if the database tables for Bibauthorid exist. If not, creates them

    @return: True if tables exist, False if there was an error
    @rtype: boolean
    '''

    try:
        if not run_sql("show tables like 'aidAUTHORNAMES';"):
            return False
    except (ProgrammingError, OperationalError):
        return False

    return True


def load_mem_cache_from_tables():
    '''
    Loads database content for an author's last name cluster into the
    memory storage facility.

    @precondition: memory storage facility needs to be loaded with respective
        authornames data (init_authornames(lastname))

    @return: Success (True) or failure (False) of the loading process
    @rtype: boolean
    '''
#    print "check for authornames mem table"

    if not dat.AUTHOR_NAMES:
        return False

    authornames_ids = [row['id'] for row in dat.AUTHOR_NAMES]

    if not authornames_ids:
        return False

#    print "Building offsets"
    ra_id_offset = run_sql("SELECT max(realauthorID) FROM"
                           " aidREALAUTHORS")[0][0]
    va_id_offset = run_sql("SELECT max(virtualauthorID) FROM"
                           " aidVIRTUALAUTHORS")[0][0]
    cluster_id_offset = run_sql("SELECT max(id) FROM"
                                " aidVIRTUALAUTHORSCLUSTERS")[0][0]
    dat.set_tracker("raid_counter", ra_id_offset + 1)
    dat.set_tracker("va_id_counter", va_id_offset + 1)
    dat.set_tracker("cluster_id", cluster_id_offset + 1)
#    print "working on authornames ids..."

    for authornames_id in authornames_ids:
        db_vas = run_sql("SELECT virtualauthorid, authornamesid, p, clusterid "
                         "from aidVIRTUALAUTHORS WHERE authornamesid = %s",
                         (authornames_id,))
#        print "loading VAs for authid %s" % authornames_id
        db_vas_set = set([row[0] for row in db_vas])

        if not db_vas_set:
            db_vas_set = (-1, -1)
        else:
            db_vas_set.add(-1)

        db_vas_tuple = tuple(db_vas_set)
        db_ras = run_sql("SELECT realauthorid FROM "
                         "aidREALAUTHORS WHERE virtualauthorid in %s"
                         , (tuple(db_vas_tuple),))

        if db_ras:
            db_ras_set = set([row[0] for row in db_ras])
            db_ras_set.add(-1)
            db_ras_tuple = tuple(db_ras_set)
            db_ra_vas = run_sql("SELECT virtualauthorid FROM aidREALAUTHORS "
                                "WHERE realauthorid in %s", (db_ras_tuple,))
            db_ra_vas_set = set([row[0] for row in db_ra_vas])
            db_ra_vas_set.add(-1)
            db_ras_tuple = tuple(db_ra_vas_set)
            db_vas_all = run_sql("SELECT virtualauthorid, authornamesid, p, "
                                 "clusterid FROM aidVIRTUALAUTHORS WHERE "
                                 "virtualauthorid in %s",
                                 (db_ras_tuple,))
        else:
            db_vas_all = db_vas

        for db_va in db_vas_all:
            dat.VIRTUALAUTHORS.append({'virtualauthorid': db_va[0],
                                       'authornamesid': db_va[1],
                                       'p': db_va[2],
                                       'clusterid': db_va[3]})

    if not dat.VIRTUALAUTHORS:
#        print "No Virtual Authors loaded. None created before."
        return True

#    print "Loading clusters"
    cluster_ids = set([row['clusterid'] for row in dat.VIRTUALAUTHORS])

    if not cluster_ids:
        cluster_ids = (-1, -1)
    else:
        cluster_ids.add(-1)

    db_va_clusters = run_sql("SELECT id, cluster_name FROM "
                             "aidVIRTUALAUTHORSCLUSTERS WHERE id in %s"
                             , (tuple(cluster_ids),))
#    print "Storing clusters"

    for db_va_cluster in db_va_clusters:
        dat.VIRTUALAUTHOR_CLUSTERS.append({'clusterid': db_va_cluster[0],
                                           'clustername': db_va_cluster[1]})

#    print "Loading VA data"
    va_ids = set([row['virtualauthorid'] for row in dat.VIRTUALAUTHORS])

    if not va_ids:
        va_ids = (-1, -1)
    else:
        va_ids.add(-1)

#    print "Storing VA data"
    db_va_data = run_sql("SELECT virtualauthorid, tag, value FROM "
                         "aidVIRTUALAUTHORSDATA WHERE virtualauthorid in %s"
                         , (tuple(va_ids),))

    for db_va_dat in db_va_data:
        dat.VIRTUALAUTHOR_DATA.append({'virtualauthorid' : db_va_dat[0],
                                       'tag': db_va_dat[1],
                                       'value': db_va_dat[2]})

#    print "Loading RAs"
    db_ras = run_sql("SELECT realauthorid, virtualauthorid, p FROM "
                     "aidREALAUTHORS WHERE virtualauthorid in %s"
                     , (tuple(va_ids),))
#    print "Storing RAs"

    for db_ra in db_ras:
        dat.REALAUTHORS.append({'realauthorid': db_ra[0],
                                'virtualauthorid': db_ra[1],
                                'p': db_ra[2]})

#    print "Loading RA data"
    ra_ids = set([row['realauthorid'] for row in dat.REALAUTHORS])

    if not ra_ids:
        ra_ids = (-1, -1)
    else:
        ra_ids.add(-1)

    db_ra_data = run_sql("SELECT realauthorid, tag, value, va_count, "
                         "va_names_p, va_p FROM aidREALAUTHORDATA WHERE "
                         "realauthorid in %s", (tuple(ra_ids),))
#    print "Storing RA data"

    for db_ra_dat in db_ra_data:
        dat.REALAUTHOR_DATA.append({'realauthorid': db_ra_dat[0],
                                    'tag': db_ra_dat[1],
                                    'value': db_ra_dat[2],
                                    'va_count': db_ra_dat[3],
                                    'va_np': db_ra_dat[4],
                                    'va_p': db_ra_dat[5]})

#    print "Loading doclist entries"
    bibrec_ids = set([int(row['value']) for row in dat.REALAUTHOR_DATA
                  if row['tag'] == "bibrec_id"])

    if not bibrec_ids:
        bibrec_ids = (-1, -1)
    else:
        bibrec_ids.add(-1)

    db_doclist = run_sql("SELECT bibrecid, processed_author FROM aidDOCLIST "
                         "WHERE bibrecid in %s", (tuple(bibrec_ids),))
#    print "Storing doclist entries"

    for db_doc in db_doclist:
        existing_item = [row for row in dat.DOC_LIST
                         if row['bibrecid'] == db_doc[0]]

        if existing_item:
            for update in [row for row in dat.DOC_LIST
                           if row['bibrecid'] == db_doc[0]]:
                if not db_doc[1] in update['authornameids']:
                    update['authornameids'].append(db_doc[1])
        else:
            dat.DOC_LIST.append({'bibrecid': db_doc[0],
                                 'authornameids': [db_doc[1]]})

    if set(bibrec_ids).remove(-1):
#        print "will load recs"

        if not load_records_to_mem_cache(list(bibrec_ids)):
#            print" FAILED loading records"
            return False

    return True


def update_tables_from_mem_cache(sanity_checks=False, return_ra_updates=False):
    '''
    Updates the tables in the database with the information in the memory
    storage while taking into account only changed data to optimize the time
    needed for the update.

    @param sanity_checks: Perform sanity checks while updating--slows down the
        process but might detect mistakes and prevent harm. Default: False
    @type sanity_checks: boolean
    @param return_ra_updates: Will force the method to return a list of real
        author ids that have been updated. Default: False
    @type return_ra_updates: boolean

    @return: Either True if update went through without trouble or False if it
        did not and a list of updated real authors or an empty list
    @rtype: tuple of (boolean, list)
    '''
    del_ra_ids = set([-1])
    del_va_ids = dat.UPDATES_LOG['deleted_vas'].union(
                     dat.UPDATES_LOG['touched_vas'])

    if del_va_ids:
        del_va_ids.add(-1)
        del_ra_ids_db = run_sql("SELECT realauthorid FROM aidREALAUTHORS "
                                "WHERE virtualauthorid in %s"
                                , (tuple(del_va_ids),))

        for ra_id in del_ra_ids_db:
            del_ra_ids.add(ra_id[0])

        if sanity_checks:
            va_count_db = run_sql("SELECT COUNT(DISTINCT virtualauthorid) "
                                  "FROM aidVIRTUALAUTHORS WHERE "
                                  "virtualauthorid in %s"
                                  , (tuple(del_va_ids),))

            try:
                va_count_db = int(va_count_db[0][0])
            except (ValueError, IndexError, TypeError):
                bconfig.LOGGER.exception("Error while reading number of "
                                         "virtual authors in database")
                va_count_db = -1

            if not (va_count_db == len(del_va_ids)):
                bconfig.LOGGER.error("Sanity checks reported that the number "
                                     "of virtual authors in the memory "
                                     "storage is not equal to the number of "
                                     "virtual authors in the database. "
                                     "Aborting update mission.")
                return (False, [])

        bconfig.LOGGER.log(25, "Removing updated entries from "
                               "persistence layer")

        run_sql("DELETE FROM aidVIRTUALAUTHORSDATA "
                "WHERE virtualauthorid in %s", (tuple(del_va_ids),))

        run_sql("DELETE FROM aidVIRTUALAUTHORS "
                "WHERE virtualauthorid in %s", (tuple(del_va_ids),))

        if len(tuple(del_ra_ids)) > 1:
            run_sql("DELETE FROM aidREALAUTHORDATA "
                    "WHERE realauthorid in %s", (tuple(del_ra_ids),))

            run_sql("DELETE FROM aidREALAUTHORS "
                    "WHERE realauthorid in %s", (tuple(del_ra_ids),))

    insert_ra_ids = dat.UPDATES_LOG['new_ras'].union(del_ra_ids)
    insert_va_ids = dat.UPDATES_LOG['new_vas'].union(
                        dat.UPDATES_LOG['touched_vas'])
    bconfig.LOGGER.log(25, "Writing to persistence layer")

    batch_max = bconfig.TABLE_POPULATION_BUNCH_SIZE

    ra_id_db_max = run_sql("SELECT max(realauthorID) FROM"
                           " aidREALAUTHORS")[0][0]
    va_id_db_max = run_sql("SELECT max(virtualauthorID) FROM"
                           " aidVIRTUALAUTHORS")[0][0]
    cluster_id_db_max = run_sql("SELECT max(id) FROM"
                                " aidVIRTUALAUTHORSCLUSTERS")[0][0]

    if not ra_id_db_max or not va_id_db_max or not cluster_id_db_max:
        return (False, [])

    new_clusters = [row for row in dat.VIRTUALAUTHOR_CLUSTERS
                    if row['clusterid'] > cluster_id_db_max]
    query = []

    if not insert_ra_ids or not insert_va_ids:
        bconfig.LOGGER.log(25, "Saving update to persistence layer finished "
                               "with success! (There was nothing to do.)")
        return (True, [])

    for va_cluster in new_clusters:
        if len(query) >= batch_max:
            try:
                run_sql(''.join(query))
            except:
                bconfig.LOGGER.critical("Inserting into virtual author "
                                        "cluster table failed")
                return (False, [])

            query = []

        if len(va_cluster['clustername']) > 150:
            bconfig.LOGGER.warning("Value for cluster table insertion "
                                   "truncated to 150 characters: %s"
                                   % (str(va_cluster['clustername'])))

        query.append("INSERT INTO aidVIRTUALAUTHORSCLUSTERS (cluster_name) "
                      "VALUES (\"%s\"); "
                     % (va_cluster['clustername'][0:149],))

    if query:
        try:
            run_sql(''.join(query))
        except:
            bconfig.LOGGER.critical("Inserting into virtual author "
                                    "cluster table failed")
            return (False, [])

        query = []

    va_data_to_insert = [row for row in dat.VIRTUALAUTHOR_DATA
                         if row['virtualauthorid'] in insert_va_ids]

    if sanity_checks:
        db_existing_va_ids = run_sql("SELECT COUNT(DISTINCT virtualauthorid) "
                                     "WHERE virtualauthorid in %s"
                                     , (tuple(insert_va_ids),))
        try:
            db_existing_va_ids = int(va_count_db[0][0])
        except (ValueError, IndexError, TypeError):
            bconfig.LOGGER.exception("Error while reading number of "
                                     "virtual authors in database")
            db_existing_va_ids = -1

        if not (db_existing_va_ids == 0):
            bconfig.LOGGER.error("Sanity checks reported that the "
                                 "virtual authors in the memory storage "
                                 "that shall be inserted already exist "
                                 "in the database. Aborting update mission.")
            return (False, [])

    for va_data in va_data_to_insert:
        if len(query) >= batch_max:
            try:
                run_sql(''.join(query))
            except:
                bconfig.LOGGER.critical("Inserting into virtual author "
                                        "data table failed")
                return (False, [])

            query = []

        query.append("INSERT INTO aidVIRTUALAUTHORSDATA "
                      "(virtualauthorID, tag, value) VALUES "
                      "(%d, \"%s\", \"%s\"); "
                     % (va_data['virtualauthorid'],
                        va_data['tag'], va_data['value']))

    if query:
        try:
            run_sql(''.join(query))
        except:
            bconfig.LOGGER.critical("Inserting into virtual author "
                                    "data table failed")
            return (False, [])

        query = []

    vas_to_insert = [row for row in dat.VIRTUALAUTHORS
                         if row['virtualauthorid'] in insert_va_ids]

    for va_entry in vas_to_insert:
        if len(query) >= batch_max:
            try:
                run_sql(''.join(query))
            except:
                bconfig.LOGGER.critical("Inserting into virtual author "
                                        "table failed")
                return (False, [])

            query = []

        query.append("INSERT INTO aidVIRTUALAUTHORS "
                      "(virtualauthorID, authornamesID, p, clusterID) VALUES "
                      "(%d, %d, \"%s\", %d); "
                     % (va_entry['virtualauthorid'],
                        va_entry['authornamesid'], va_entry['p'],
                        va_entry['clusterid']))

    if query:
        try:
            run_sql(''.join(query))
        except:
            bconfig.LOGGER.critical("Inserting into virtual author "
                                    "table failed")
            return (False, [])
        query = []

    if sanity_checks:
        db_existing_ra_ids = run_sql("SELECT COUNT(DISTINCT realauthorid) "
                                     "WHERE realauthorid in %s"
                                     , (tuple(insert_ra_ids),))
        try:
            db_existing_ra_ids = int(db_existing_ra_ids[0][0])
        except (ValueError, IndexError, TypeError):
            bconfig.LOGGER.exception("Error while reading number of "
                                     "real authors in database")
            db_existing_va_ids = -1

        if not (db_existing_ra_ids == 0):
            bconfig.LOGGER.error("Sanity checks reported that the "
                                 "real authors in the memory storage "
                                 "that shall be inserted already exist "
                                 "in the database. Aborting update mission.")
            return (False, [])

    ra_data_to_insert = [row for row in dat.REALAUTHOR_DATA
                         if row['realauthorid'] in insert_ra_ids]

    for ra_data in ra_data_to_insert:
        if len(query) >= batch_max:
            try:
                run_sql(''.join(query))
            except:
                bconfig.LOGGER.critical("Inserting into real author "
                                        "data table failed")
                return (False, [])

            query = []

        if len(ra_data['value']) > 254:
            bconfig.LOGGER.warning("Value for ra data table insertion "
                                   "truncated to 255 characters: %s"
                                   % (str(ra_data['value'])))

        if not ra_data['tag'] == 'outgoing_citation':
            query.append("INSERT INTO aidREALAUTHORDATA "
                          "(realauthorID, tag, value, va_count, "
                          "va_names_p, va_p) VALUES "
                          "(%d, \"%s\", \"%s\", %d, "
                          "%f, %f); "
                         % (ra_data['realauthorid'],
                            ra_data['tag'], ra_data['value'][0:254],
                            ra_data['va_count'], ra_data['va_np'],
                            ra_data['va_p']))

    if query:
        try:
            run_sql(''.join(query))
        except:
            bconfig.LOGGER.critical("Inserting into real author "
                                    "data table failed")
            return (False, [])
        query = []

    ras_to_insert = [row for row in dat.REALAUTHORS
                         if row['realauthorid'] in insert_ra_ids]


    for ra_entry in ras_to_insert:
        if len(query) >= batch_max:
            try:
                run_sql(''.join(query))
            except:
                bconfig.LOGGER.critical("Inserting into real author "
                                        "table failed")
                return (False, [])
            query = []

        query.append("INSERT INTO aidREALAUTHORS "
                      "(realauthorID, virtualauthorID, p) VALUES "
                      "(%d, %d, %f); "
                     % (ra_entry['realauthorid'],
                        ra_entry['virtualauthorid'],
                        ra_entry['p']))

    if query:
        try:
            run_sql(''.join(query))
        except:
            bconfig.LOGGER.critical("Inserting into real author "
                                    "table failed")
            return (False, [])
        query = []

    if sanity_checks:
        db_existing_ra_ids = run_sql("SELECT COUNT(DISTINCT realauthorid) "
                                     "WHERE realauthorid in %s"
                                     , (tuple(insert_ra_ids),))
        try:
            db_existing_ra_ids = int(db_existing_ra_ids[0][0])
        except (ValueError, IndexError, TypeError):
            bconfig.LOGGER.exception("Error while reading number of "
                                     "real authors in database")
            db_existing_ra_ids = -1

        if not (db_existing_ra_ids == len(insert_ra_ids)):
            bconfig.LOGGER.error("Sanity checks reported that the number of"
                                 "real authors in the memory storage "
                                 "that shall be inserted is not equal to "
                                 "the number of real authors now "
                                 "in the database. Aborting update mission.")
            return (False, [])

    recid_updates = dat.UPDATES_LOG["rec_updates"]

    if recid_updates:
        recid_updates.add(-1)
        run_sql("DELETE FROM aidDOCLIST WHERE bibrecid in %s"
                , (tuple(recid_updates),))

        doclist_insert = [row for row in dat.DOC_LIST
                          if row['bibrecid'] in dat.UPDATES_LOG["rec_updates"]]

        for doc in doclist_insert:
            if len(query) >= batch_max:
                try:
                    run_sql(''.join(query))
                except:
                    bconfig.LOGGER.critical("Inserting into doc list "
                                            "table failed")
                    return (False, [])
                query = []

            for processed_author in doc['authornameids']:
                query.append("INSERT INTO aidDOCLIST "
                             "(bibrecID, processed_author) VALUES "
                             "(%d, %d); "
                              % (doc['bibrecid'], processed_author))

        if query:
            try:
                run_sql(''.join(query))
            except:
                bconfig.LOGGER.critical("Inserting into doc list "
                                        "table failed")
                return (False, [])
            query = []

    bconfig.LOGGER.log(25, "Saving update to persistence layer finished "
                           "with success!")
    if return_ra_updates:
        ra_ids = [[row['realauthorid']] for row in ras_to_insert]
        return (True, ra_ids)
    else:
        return (True, [])
