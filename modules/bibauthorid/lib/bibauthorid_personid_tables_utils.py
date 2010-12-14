# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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
bibauthorid_personid_tables_utils
    Bibauthorid's personid related DB handler
"""
import sys
import time
import threading

import bibauthorid_config as bconfig
import bibauthorid_structs as dat

from search_engine import get_record
from dbquery import run_sql
from dbquery import OperationalError, ProgrammingError
from bibauthorid_utils import split_name_parts, create_normalized_name
from bibauthorid_utils import clean_name_string
from bibauthorid_authorname_utils import compare_names
from threading import Thread
from access_control_engine import acc_authorize_action


def update_personID_table_from_paper(papers_list=[]):
    '''
    Updates the personID table removing the bibrec/bibrefs couples no longer existing (after a paper has been
    updated (name changed))
    @param: list of papers to consider for the update (bibrecs) (('1'),)
    '''
    for paper in papers_list:
        fullbibrefs100 = run_sql("select id_bibxxx from bibrec_bib10x where id_bibrec=%s", (paper[0],))
        fullbibrefs700 = run_sql("select id_bibxxx from bibrec_bib70x where id_bibrec=%s", (paper[0],))

        fullbibrefs100str = '( '
        for i in fullbibrefs100:
            fullbibrefs100str += " '" + str(i[0]) + "',"
        fullbibrefs100str = fullbibrefs100str[0:len(fullbibrefs100str) - 1] + ' )'

        fullbibrefs700str = '( '
        for i in fullbibrefs700:
            fullbibrefs700str += " '" + str(i[0]) + "',"
        fullbibrefs700str = fullbibrefs700str[0:len(fullbibrefs700str) - 1] + ' )'

        if len(fullbibrefs100) >= 1:
            bibrefs100 = run_sql("select id from bib10x where tag='100__a' and id in %s" % fullbibrefs100str)
        else:
            bibrefs100 = []
        if len(fullbibrefs700) >= 1:
            bibrefs700 = run_sql("select id from bib70x where tag='700__a' and id in %s" % fullbibrefs700str)
        else:
            bibrefs700 = []

        bibrecreflist = []
        for i in bibrefs100:
            bibrecreflist.append('100:' + str(i[0]) + ',' + str(paper[0]))
        for i in bibrefs700:
            bibrecreflist.append('700:' + str(i[0]) + ',' + str(paper[0]))

        if bconfig.TABLES_UTILS_DEBUG:
            print "update_personID_table_from_paper: searching for pids owning " + str(paper[0])
        pid_rows = run_sql("select * from aidPERSONID where tag='paper' and data like %s", ('%,' + str(paper[0]),))

        #finally, if a bibrec/ref pair is in the authornames table but not in this list that name of that paper
        #is no longer existing and must be removed from the table. The new one will be addedd by the
        #update procedure in future; this entry will be risky becouse the garbage collector may
        #decide to kill the bibref in the bibX0x table
        for row in pid_rows:
            if row[3] not in bibrecreflist:
                if bconfig.TABLES_UTILS_DEBUG:
                    print "update_personID_table_from_paper: deleting " + str(row[0])
                run_sql("delete from aidPERSONID where id = %s", (str(row[0]),))
            else:
                if bconfig.TABLES_UTILS_DEBUG:
                    print "update_personID_table_from_paper: not touching " + str(row[0])

def personid_perform_cleanup():
    '''
    Performs a consistency cleanup on the data in personID tables.
    It is  usually not needed to have papers manually assigned to a personID
    to be even rejected from a different personID.
    This method thus takes care of eliminating such a redudancy in the table where
    it happens. It's not done during the update process for speed reasons.
    '''
    #consistency check:
    #papers which have been assigned by users should appear in only one place
    #This will no longer be needed if the update_from_algorithm will  be modified
    #to take that into account, now it is not for performance reasons
    run_sql("delete from aidPERSONID where tag='paper' and flag <='-1' and \
            data in (select data from aidPERSONID where tag='paper' and flag='2')")


def confirm_papers_to_person(pid, papers, user_level):
    '''
    Confirms the relationship between pid and paper, as from user input.
    @param pid: id of the person
    @type pid: ('2',)
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    '''
    #expects a pid ('2',)
    #and a lst of papers (('100:7531,9024',),)

    class names_gatherer(Thread):
        def __init__ (self, pid):
            Thread.__init__(self)
            self.pid = pid

        def run(self):
            update_personID_names_string_set(self.pid)

    updated_pids = []
    for p in papers:
        old_owners = run_sql("select personid from aidPERSONID where tag=%s and data=%s", ('paper', str(p[0]),))
        if len(old_owners) > 0:
            for owner in old_owners:
                updated_pids.append((str(owner[0]),))
        run_sql("delete from aidPERSONID where tag=%s and data=%s", ('paper', str(p[0]),))
        run_sql("insert into aidPERSONID (PersonID, tag, data, flag, lcul) values (%s,'paper',%s,'2', %s)",
                (str(pid[0]), str(p[0]), user_level))
    update_personID_names_string_set((pid,))

    upd_thread = names_gatherer(tuple(updated_pids))
    upd_thread.start()



def reject_papers_from_person(pid, papers, user_level=0):
    '''
    Confirms the negative relationship between pid and paper, as from user input.
    @param pid: id of the person
    @type pid: ('2',)
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    '''
    #expects a pid ('2',)
    #and a lst of papers (('100:7531,9024',),)
    #check if already assigned by user and skip those ones
    for p in papers:
        run_sql("update aidPERSONID set flag=%s,lcul=%s where PersonID=%s and data=%s",
                ('-2', user_level, str(pid[0]), str(p[0])))
    update_personID_names_string_set((pid,))


def reset_papers_flag(pid, papers):
    '''
    Resets the flag associated to the papers to '0'
    @param papers: list of papers to confirm
    @type papers: (('100:7531,9024',),)
    '''
    for p in papers:
        run_sql("update aidPERSONID set flag=%s,lcul='0' where tag=%s and data=%s", ('0', 'paper', str(p[0])))
    update_personID_names_string_set((pid,))



def get_papers_status(papers):
    '''
    Gets the personID and flag assiciated to papers
    @param papers: list of papers
    @type papers: (('100:7531,9024',),)
    @return: (('data','personID','flag',),)
    @rtype: tuple of tuples
    '''
    #lst of papers (('100:7531,9024',),)
    #for each paper gives: personid, assignment status
    papersstr = '( '
    for p in papers:
        papersstr += '\'' + str(p[0]) + '\','
    papersstr = papersstr[0:len(papersstr) - 1] + ' )'
    if len(papers) >= 1:
        return run_sql("select data,PersonID,flag from aidPERSONID where tag=%s and data in " + papersstr,
                    ('paper',))
    else:
        return []


def get_person_papers(pid, flag, show_author_name=False, show_title=False):
    '''
    Returns all the paper associated to a person with a flag greater or equal
    than the given one. Eventually returns even author name and title
    associated to the papers.

    @param pid: person id
    @type pid: ('2',)
    @param flag: numerical flag, the convention is documented with the
                 database table creation script
    @type papers: integer
    @param show_author_name: Also return authorname in dict?
    @type show_author_name: Boolean
    @param show_title: Also return title in dict?
    @type show_title: Boolean

    @return: [{'data': "", 'flag': "", 'author_name': "", 'title': ""}]
             author_name and title will be returned depending on the params
    @rtype: list of dicts
    '''
    #expects a pid ('2',)
    #and a flag 0
    paperslist = []
    try:
        flag = int(flag)
    except ValueError:
        return paperslist

    docs = run_sql("SELECT data,flag FROM aidPERSONID where personid = %s"
                    " and tag = %s and flag >= %s",
                    (pid[0], 'paper', flag))

    for doc in docs:
        listdict = {}

        if show_title:
            title = "No title on paper..."
            try:
                rec_id = int(doc[0].split(',')[1])
                title = get_record(rec_id)['245'][0][0][0][1]
            except (IndexError, KeyError, ValueError):
                title = "Problem encountered while retrieving document title"
            listdict["title"] = title

        dsplit = doc[0].split(',')
        tnum = "70"
        if str(dsplit[0].split(':')[0]) == "100":
            tnum = "10"
        sqlstr = ("SELECT value FROM bib%sx WHERE  id = " % (tnum)) + '%s'
        authorname = run_sql(sqlstr, (dsplit[0].split(':')[1],))
        try:
            authorname = authorname[0][0]
            if show_author_name:
                listdict["authorname"] = authorname
            listdict["data"] = doc[0]
            listdict["flag"] = doc[1]
            paperslist.append(listdict)
        except IndexError:
            #The paper has been modified and this bibref is no longer there
            #@TODO: this must call bibsched to update_personid_table_from_paper
            continue

    return paperslist


def get_person_data(person_id, tag=None):
    '''
    Returns all the records associated to a person.
    If tag != None only rows for the selected tag will be returned.

    @param person_id: id of the person to read the attribute from
    @type person_id: int
    @param tag: the tag to read. Optional. Default: None
    @type tag: string

    @return: the data associated with a virtual author
    @rtype: tuple of tuples
    '''
    rows = []

    if tag:
        rows = run_sql("SELECT tag, data FROM aidPERSONID "
                       "WHERE personid = %s AND tag = %s", (person_id, tag))
    else:
        rows = run_sql("SELECT tag, data FROM aidPERSONID "
                       "WHERE personid = %s", (person_id,))
    return rows


def set_person_data(person_id, tag, value, user_level=0):
    '''
    Change the value associated to the given tag for a certain person.
    @param person_id: ID of the person
    @type person_id: int
    @param tag: tag to be updated
    @type tag: string
    @param value: value to be written for the tag
    @type value: string
    '''
    current_tag_value = run_sql("SELECT data FROM aidPERSONID "
                                "WHERE personid = %s AND tag = %s AND "
                                "data = %s", (person_id, tag, value))

    if len(current_tag_value) > 0:
        run_sql("UPDATE aidPERSONID SET tag = %s, data = %s WHERE "
                "personid = %s AND tag = %s AND lcul = %s", (tag, value, person_id, tag, user_level))
    else:
        run_sql("INSERT INTO aidPERSONID (`personid`, `tag`, `data`, `flag`, `lcul`) "
                "VALUES (%s, %s, %s, %s, %s);", (person_id, tag, value, '0', user_level))


def get_person_names_count(pid):
    '''
    Returns the set of name strings and count associated to a person id
    @param pid: ID of the person
    @type pid: ('2',)
    @param value: value to be written for the tag
    @type value: string
    '''
    return run_sql("select data,flag from aidPERSONID where PersonID=%s and tag=%s",
                    (str(pid[0]), 'gathered_name',))

def get_person_names_set(pid):
    '''
    Returns the set of name strings associated to a person id
    @param pid: ID of the person
    @type pid: ('2',)
    @param value: value to be written for the tag
    @type value: string
    '''
    #expects a pid ('2',)
    docs = run_sql("SELECT `data` FROM `aidPERSONID` where PersonID=%s and tag=%s and flag>=%s",
                    (str(pid[0]), 'paper', '-1',))
    authornames = set()
    for doc in docs:
        dsplit = doc[0].split(',')
        tnum = "70"
        if str(dsplit[0].split(':')[0]) == "100":
            tnum = "10"
        sqlstr = "SELECT value FROM bib%sx WHERE  id = " % tnum + "%s"
        authorname = run_sql(sqlstr, (dsplit[0].split(':')[1],))
        authornames.add(authorname[0])
    return list(authornames)


def find_personIDs_by_name_string(namestring):
    '''
    Search engine to find persons matching the given string
    @param: string name, 'surname, names I.'
    @type: string
    @return: pid list of lists [pid,[[name string, occur count, compatibility]]]
    
    The matching is done on the surname first, and names if present. 
    An ordered list (per compatibility) of pids and found names is returned.
    '''
    namestring_parts = split_name_parts(namestring)

#   The following lines create the regexp used in the query.
    surname = clean_name_string(namestring_parts[0],
#                                replacement=".{0,3}",
                                replacement="%",
                                keep_whitespace=False,
                                trim_whitespaces=True)

#    if not surname.startswith(".{0,3}"):
#        surname = "^['`-]*%s*" % (surname)
    surname = '%' + surname + '%'
    print surname
    #The regexp is not used anymore because it's not finding all the strings it should have ;
    #the 'like' statement is slower, the regexp will be fixed asap

    #    matching_pids_names_tuple = run_sql('select personid, data, flag '
    #                                        'from aidPERSONID as a where '
    #                                        'tag=\'gathered_name\' and '
    #                                        'data REGEXP "%s"'
    #                                        % (surname))

#@fixme: find_personIDs_by_name_string: the search can be done on authornames table and match the bibrefs, probably faster.

    matching_pids_names_tuple = run_sql("select personid, data, flag from aidPERSONID as a where "
                                        "tag=\'gathered_name\' and data like %s", (surname,))

    matching_pids = []
    for name in matching_pids_names_tuple:
        comparison = compare_names(namestring, name[1])
        matching_pids.append([name[0], name[1], name[2], comparison])
#   matching_pids = sorted(matching_pids, key=lambda k: k[3], reverse=True)
    persons = {}
    for n in matching_pids:
        if n[3] >= 0.0:
            if n[0] not in persons:
                persons[n[0]] = sorted([[p[1], p[2], p[3]] for p in  matching_pids if p[0] == n[0]],
                                key=lambda k: k[2], reverse=True)
    porderedlist = []
    for i in persons.iteritems():
        porderedlist.append([i[0], i[1]])
    porderedlist = sorted(porderedlist, key=lambda k: k[1][0][0], reverse=False)
    porderedlist = sorted(porderedlist, key=lambda k: k[1][0][2], reverse=True)
    return porderedlist

def update_personID_names_string_set(PIDlist=[]):
    '''
    Updates the personID table with the names gathered from documents
    @param: list of pids to consider, if omitted performs an update on the entire db
    @type: tuple of tuples
    
    Gets all the names associated to the bibref/bibrec couples of the person and builds a set of
    names, counting the occurrencies. The values are store in the gathered_name/flag fields of each
    person.
    The gathering of names is an expensive operation for the database (many joins), so the operation
    is threaded so to have as many parallell queries as possible.
    '''
    if len(PIDlist) == 0:
        PIDlist = run_sql('SELECT DISTINCT `personid` FROM `aidPERSONID`')# LIMIT 1 , 15')

    class names_gatherer(Thread):
        def __init__ (self, pid):
            Thread.__init__(self)
            self.pid = pid
            self.pstr = ''

        def run(self):
            self.namesdict = dict()
            self.person_papers = run_sql("select data from `aidPERSONID` where  tag=\'paper\' and "
                                          " flag >= \'-1\' and PersonID=%s",
                                            (str(self.pid[0]),))
            for p in self.person_papers:
                self.pname = run_sql("select Name from aidAUTHORNAMES where id = "
                 "(select Name_id from aidAUTHORNAMESBIBREFS where bibref = %s)",
                                    (str(p[0].split(',')[0]),))
                if self.pname[0][0] not in self.namesdict:
                    self.namesdict[self.pname[0][0]] = 1
                else:
                    self.namesdict[self.pname[0][0]] += 1

            self.current_namesdict = dict(run_sql("select data,flag from aidPERSONID where personID=%s "
                                    "and tag=\'gathered_name\'", (str(self.pid[0]),)))

            self.needs_update = False
            if self.current_namesdict != self.namesdict:
                self.needs_update = True
            else:
                for i in self.namesdict.iteritems():
                    if i[1] != self.current_namesdict[i[0]]:
                        self.needs_update = True
                        if bconfig.TABLES_UTILS_DEBUG:
                            pass
#                            sys.stdout.write(str(self.pid) + str(i[1]) + ' differs  from ' + str(self.current_namesdict[i[0]]))
#                            sys.stdout.flush()

            if self.needs_update:
                if bconfig.TABLES_UTILS_DEBUG:
                    pass
#                    sys.stdout.write(str(self.pid) + ' updating!')
#                    sys.stdout.flush()
                run_sql("delete from `aidPERSONID` where PersonID=%s and tag=%s", (str(self.pid[0]), 'gathered_name'))
                for name in self.namesdict:
#                    self.pstr += '  ' + str(self.pid[0]) + '    ...processing: ' + str(name) + ' ' + str(self.namesdict[name])
                    run_sql('insert into aidPERSONID (PersonID, tag, data, flag) values ('
                            + str(self.pid[0]) + ',\'gathered_name\',\"' + str(name)
                            + '\",\"' + str(self.namesdict[name]) + '\")')
#                else:
#                    sys.stdout.write(str(self.pid) + ' not updating!')
#                    sys.stdout.flush()
#                sys.stdout.write(self.pstr + '\n')
#                sys.stdout.flush()

    tgath = []
    for pid in PIDlist:
        current = names_gatherer(pid)
        tgath.append(current)
        current.start()
        if bconfig.TABLES_UTILS_DEBUG:
            sys.stdout.write(str(pid) + '.\n')
            sys.stdout.flush()
        while threading.activeCount() > bconfig.PERSONID_SQL_MAX_THREADS:
            time.sleep(0.02)
    for t in tgath:
        t.join()

def update_personID_from_algorithm(RAlist=[]):
    '''
    Updates the personID table with the results of the algorithm, taking into account
    user inputs
    @param: list of realauthors to consider, if omitted performs an update on the entire db
    @type: tuple of tuples
    
    This is the core of the matching between the bibauthorid world and the personid world.
    For each RA of the list, tries to find the person it should be (in an ideal world there is 
    100% matching in the list of papers, and the association is trivial).
    In the real world an RA might be wrongly carrying papers of more then one person (or a person 
    might have papers of more then one RAs) so the matching must be done on a best-effort basis:
    -find the most compatible person
        -if it's compatible enough, merge the person papers with the ra papers (after
             a backtracking to find all the other RAs which the person might 'contain')
        -if nobody is compatible enough create a new person with RA papers
        
    Given the fuzzy nature of both the computation of RAs and the matching with persons, it has been
    decided to stick to the person all and only the papers which are carried by the RAs over a certain
    threshold.
    '''

    def get_bibreclist(currentRA):
        #[['700:157610,453095', '1.0']]
        VAlist = run_sql("SELECT `virtualauthorID`,`p` FROM `aidREALAUTHORS`  WHERE `realauthorID`=%s",
                        (str(currentRA[0]),))

        bibreclist = []
        bibrecstruct = []

        class get_va_bibreclist(Thread):
            def __init__ (self, va):
                Thread.__init__(self)
                self.va = va
                self.bibreclist = []

            def run(self):
                if bconfig.TABLES_UTILS_DEBUG:
                    pass
                    #print '   --debug: thread spawn for bibreclist of va: ' + str(self.va)
                bibrec = dict(run_sql("SELECT `tag`,`value` FROM `aidVIRTUALAUTHORSDATA` WHERE "
                            "virtualauthorID=%s and (tag=%s or tag=%s)",
                            (str(self.va[0]), 'bibrec_id', 'orig_authorname_id')))

                if (not bibrec.has_key("orig_authorname_id")) or (not bibrec.has_key("bibrec_id")):
                    if bconfig.TABLES_UTILS_DEBUG:
                        print ("WARNING: VA %s holds no data." % self.va[0])
                    return

                bibreflist = run_sql("SELECT `bibrefs` FROM `aidAUTHORNAMES` WHERE `id`=%s",
                                    (str(bibrec['orig_authorname_id']),))
                bibreflist = bibreflist[0][0].split(',')

                bibref100string = '('
                bibref700string = '('

                for br in bibreflist:
                    if br.split(':')[0] == '100':
                        bibref100string += '\'' + br.split(':')[1] + '\','
                    else:
                        bibref700string += '\'' + br.split(':')[1] + '\','

                if bibref100string[len(bibref100string) - 1] == ',':
                    bibref100string = bibref100string[0:len(bibref100string) - 1] + ')'
                else:
                    bibref100string = ''

                if bibref700string[len(bibref700string) - 1] == ',':
                    bibref700string = bibref700string[0:len(bibref700string) - 1] + ')'
                else:
                    bibref700string = ''

                if bibref100string:
                    bibrec100list = run_sql("SELECT `id_bibxxx` FROM `bibrec_bib10x` WHERE `id_bibrec`=%s"
                                            " and `id_bibxxx` in " + bibref100string,
                                            (str(bibrec['bibrec_id']),))
                else:
                    bibrec100list = []

                if bibref700string:
                    bibrec700list = run_sql("SELECT `id_bibxxx` FROM `bibrec_bib70x` WHERE `id_bibrec`=%s"
                                            " and `id_bibxxx` in" + bibref700string,
                                            (str(bibrec['bibrec_id']),))
                else:
                    bibrec700list = []

                for br in bibreflist:
                    if (long(br.split(':')[1]),) in bibrec100list:
                        if br not in self.bibreclist:
                            self.bibreclist.append([br + ',' + bibrec['bibrec_id'] , str(self.va[1])])
                        break
                    elif (long(br.split(':')[1]),) in bibrec700list:
                        if br not in self.bibreclist:
                            self.bibreclist.append([br + ',' + bibrec['bibrec_id'] , str(self.va[1])])
                        break

        tbibreclist = []
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: get_bibreclist threads: '
        for va in VAlist:
            current = get_va_bibreclist(va)
            tbibreclist.append(current)
            if bconfig.TABLES_UTILS_DEBUG:
                sys.stdout.write('.')
                sys.stdout.flush()
            current.start()
            while threading.activeCount() > bconfig.PERSONID_SQL_MAX_THREADS:
                time.sleep(0.02)

        for t in tbibreclist:
            t.join()
            for b in t.bibreclist:
                if b not in bibreclist:
                    bibreclist.append(b)

        if bconfig.TABLES_UTILS_DEBUG:
            print '\nupdate_personID_from_algorithm: get_bibreclist ---------------- Considering RA: ' + str(currentRA)
        return bibreclist

    def create_new_person(bibreclist):
        #creating new personid
        PID = max(run_sql('SELECT  MAX(PersonID) FROM `aidPERSONID`')[0][0], -1) + 1
        SQLquery = ''
        for br in bibreclist:
            flag = 0
            if br[1] >= bconfig.PERSONID_CNP_FLAG_1:
                flag = 1
            elif br[1] < bconfig.PERSONID_CNP_FLAG_MINUS1:
                flag = -1
            SQLquery += ('insert into `aidPERSONID` (PersonID, tag, data, flag) values ('
                + str(PID) + ', \'paper\',%s,\'' + str(flag) + '\');') % ('\'' + br[0] + '\'')
        if SQLquery:
            run_sql(SQLquery)
        update_personID_names_string_set(((str(PID),),))
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: create_new_person ---------------- ' + str(PID)

    def get_person_ra(person_papers):
        inverse_ra_list = []
        papers_vas = []

        class get_va_from_paper(Thread):
            def __init__ (self, paper):
                Thread.__init__(self)
                self.paper = paper
                self.vas = []
            def run(self):
                self.authnameid = run_sql("select Name_id from aidAUTHORNAMESBIBREFS where bibref=%s",
                        (str(self.paper[0].split(',')[0]),))
                self.va = run_sql(
                  "select a.virtualauthorID from aidVIRTUALAUTHORSDATA as a inner join "
                  "aidVIRTUALAUTHORSDATA as b on a.virtualauthorID=b.virtualauthorID "
                  "where ((a.tag=%s and a.value=%s) and (b.tag=%s and b.value=%s))",
                  ('bibrec_id', str(self.paper[0].split(',')[1]), 'orig_authorname_id', str(self.authnameid[0][0])))

                #This is left here for benchmarking, it is still not clear which approach is the fastest
                #self.va = run_sql('select virtualauthorID from `aidVIRTUALAUTHORSDATA` where ( virtualauthorID in ('
                #         + ('select virtualauthorID from `aidVIRTUALAUTHORSDATA` where tag=\'bibrec_id\' and value=\'%s\'')
                #             % (str(self.paper[0].split(',')[1]))
                #         + ')) and ((tag, value) = (\'orig_authorname_id\', \''
                #         + str(authnameid[0][0]) + '\'))')
                for i in self.va:
                    self.vas.append(i[0])

        tvapaper = []
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: get_va_from_paper threads: '
        for paper in person_papers:
            current = get_va_from_paper(paper)
            tvapaper.append(current)
            if bconfig.TABLES_UTILS_DEBUG:
                sys.stdout.write('.')
                sys.stdout.flush()
            current.start()
            while threading.activeCount() > bconfig.PERSONID_SQL_MAX_THREADS:
                time.sleep(0.02)

        for t in tvapaper:
            t.join()
            for b in t.vas:
                if b not in papers_vas:
                    papers_vas.append(b)

        papers_vas_string = '( '
        for i in papers_vas:
            papers_vas_string += '\'' + str(i) + '\','
        papers_vas_string = papers_vas_string[0:len(papers_vas_string) - 1] + ' )'
        if len(papers_vas) >= 1:
            inverse_ra_list.append(run_sql("select distinct `realauthorID` "
                    " from `aidREALAUTHORS` where virtualauthorID in " + papers_vas_string))
        else:
            inverse_ra_list = []
        if bconfig.TABLES_UTILS_DEBUG:
            print '\nupdate_personID_from_algorithm: get_person_ra ---------------- on ' + str(person_papers)
        return inverse_ra_list

    def merge_update_person_with_ra(pids, person_paper_list, currentRA, bibreclist):
        ras = get_person_ra(person_paper_list)
#        bibrecslists = []
        bibrecset = set()
        person_rejected_papers = run_sql("select data from `aidPERSONID` where "
                        ' tag=%s and  flag=%s and PersonID=%s',
                        ('paper', '-2', str(pids[0])))
        person_confirmed_papers = run_sql("select data from `aidPERSONID` where "
                        ' tag=%s and  flag=%s and PersonID=%s',
                        ('paper', '2', str(pids[0])))

        person_rejected_papers_set = set()
        for paper in person_rejected_papers:
            person_rejected_papers_set.add(paper[0])

        person_confirmed_papers_set = set()
        for paper in person_confirmed_papers:
            person_confirmed_papers_set.add(paper[0])

        for ra in ras:
            list = get_bibreclist(ra[0])
#            bibrecslists.append(list)
            for doc in list:
                if doc[1] >= bconfig.PERSONID_MIN_P_FROM_BCTKD_RA:
                    bibrecset.add(doc[0])

        for doc in bibreclist:
            if doc[1] >= bconfig.PERSONID_MIN_P_FROM_NEW_RA:
                bibrecset.add(doc[0])

        person_paper_set = set()
        for paper in person_paper_list:
            person_paper_set.add(paper[0])

        p_to_add = bibrecset.difference(person_paper_set)
        p_to_add = p_to_add.difference(person_rejected_papers_set)
        p_to_add = p_to_add.difference(person_confirmed_papers_set)

#       we might consider the case in which the algorithm is clustering two papers which are
#       manually assigned to different persons. That would mean adding a potentially really slow query
#       and once tthe algorithm will be able to take into consideration user input logs that should never happen
#       so this will be left to be done once we will see if it is really necessary to slow down everything
#       when the algorithm is clustering nicely this shouldn't happen anyway

        p_to_remove = person_paper_set.difference(bibrecset)
        p_to_remove = p_to_remove.difference(person_confirmed_papers_set)
        p_to_remove = p_to_remove.difference(person_rejected_papers_set)
        SQLquery = ''
        for br in p_to_add:
            SQLquery += ('insert into `aidPERSONID` (PersonID, tag, data, flag) values ('
                        + str(pids[0]) + ', \'paper\',%s,\'0\');') % ('\'' + br + '\'')
        if SQLquery:
            run_sql(SQLquery)
        SQLquery = ''
        for br in p_to_remove:
            SQLquery += ('delete from `aidPERSONID` where PersonID=\''
                         + str(pids[0]) + '\' and tag=\'paper\' and data=\''
                         + str(br) + '\';')
        if SQLquery:
            run_sql(SQLquery)
        update_personID_names_string_set((pids,))
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: Merging ----------------' + str(pids) + ' with realauthor ' + str(currentRA) + ' and found ras ' + str(ras)
#        print 'adding ' + str(p_to_add)
#        print 'removing ' + str(p_to_remove)

    if len(RAlist) == 0:
        RAlist = run_sql('SELECT DISTINCT `realauthorID` FROM `aidREALAUTHORS`')# LIMIT 1 , 15')


    for currentRA in RAlist:
        print '---|||||--- considering RA ' + str(currentRA)
        #bibreclist is the list of bibrefs associated with a RA
        bibreclist = get_bibreclist(currentRA)

        if not bibreclist:
            if bconfig.TABLES_UTILS_DEBUG:
                print "update_personID_from_algorithm: Skipping RA. Got no data from VA."
            continue

        bibrecsqlstring = '( '
        for i in bibreclist:
            bibrecsqlstring += '\'' + str(i[0]) + '\','
        bibrecsqlstring = bibrecsqlstring[0:(len(bibrecsqlstring) - 1)] + ' )'
        sqlstr = "SELECT DISTINCT PersonID FROM `aidPERSONID` WHERE tag=%s and `flag` >= %s and `data` in " + bibrecsqlstring
        if len(bibreclist) >= 1:
            pids = run_sql(sqlstr, ('paper', '0'))
        else:
            pids = []
        if bconfig.TABLES_UTILS_DEBUG:
            print 'update_personID_from_algorithm: Possible PIDS: ' + str(pids)

        if len(pids) < 1:
            create_new_person(bibreclist)

        else:
            #collect all the bibrefs
            #find all RA involved
            #decide which ones are really connected (>threshold)
            #merge them in the person found

            person_paper_list = []
            for pid in pids:
                person_papers = run_sql("select data from `aidPERSONID` where tag=%s and "
                                         "flag >= %s and PersonID=%s",
                                         ('paper', str(bconfig.PERSONID_UPFA_PPLMF), str(pid[0])))
                person_paper_list.append(person_papers)

            docn = len(bibreclist)
            bibrectdict = dict(bibreclist)
            compatibility_list = []
            for pid in person_paper_list:
                sum = 0.0
                for doc in pid:
                    try:
                        sum += float(bibrectdict[doc[0]])
                    except:
                        pass
                        #print 'noindex exception!'
                compatibility_list.append(sum / docn)

            if bconfig.TABLES_UTILS_DEBUG:
                print 'update_personID_from_algorithm: Compatibility list: ' + str(compatibility_list)

            if max(compatibility_list) < bconfig.PERSONID_MAX_COMP_LIST_MIN_TRSH:
                if bconfig.TABLES_UTILS_DEBUG:
                    print 'update_personID_from_algorithm: Max compatibility list < than 0.5!!!'
                create_new_person(bibreclist)
            else:
                maxcount = compatibility_list.count(max(compatibility_list))
                if maxcount == 1:
                    #merge
                    pidindex = compatibility_list.index(max(compatibility_list))
                    merge_update_person_with_ra(pids[pidindex],
                        person_paper_list[pidindex], currentRA, bibreclist)
                elif maxcount > 1:
                    if bconfig.TABLES_UTILS_DEBUG:
                        print 'update_personID_from_algorithm: !!!!!!!!!!!!! Passing by, no maximum in compatibility list??'
                    #resolve merge
                else:
                    if bconfig.TABLES_UTILS_DEBUG:
                        print 'update_personID_from_algorithm: !!!!!!!!!!!!! Error: no one is compatible!!? not doing anything...'

def export_personid_to_spiresid_validation(filename='/tmp/inspirepid', filename_oids='/tmp/inspirepidoids'):
    '''
    WARNING: still to be consolidated, but output is usable
    WARNING^2: S  L  O  W  .
    @fixme: export_personid_to_spiresid_validation: use get_record, might be much faster
    '''
    fp = open(filename, 'w')
    fp2 = open(filename_oids, 'w')
    fp.write('Personid->inspireid match:\n\n')
    fp2.write('Personid->inspireid match: INSPERE IDS only \n\n')
    pids = run_sql('SELECT personid FROM `aidPERSONID` WHERE 1 group by personid')
    for pid in pids:
        print 'considering:' + str(pid)
        fp.write('Considering pid' + str(pid) + '\n')
        fp2.write('Considering pid' + str(pid) + '\n')
        papers = run_sql('select data from aidPERSONID where tag=\'paper\' and '
                         'personid=\'' + str(pid[0]) + '\' ')
        parray = []
        for paper in papers:
            if paper[0].split(':')[0] == '700':
                print '  -' + str(paper)
                fields = run_sql('select id,value from bib70x where '
                                 '(tag=\'700__a\') and '
                                 'id=\'' + str(paper[0].split(',')[0].split(':')[1])
                                 + '\'')
                insid = run_sql('select id,value from bib70x where tag=\'700__i\' '
                         'and (id) in '
                         '(select a.id_bibxxx from bibrec_bib70x as a inner join '
                         'bibrec_bib70x as b using(id_bibrec)'
                         'where a.field_number = b.field_number and '
                         'b.id_bibxxx = \'' + str(paper[0].split(',')[0].split(':')[1])
                         + '\' and b.id_bibrec = \'' +
                         str(paper[0].split(',')[1]) + '\')')
                parray.append([fields, insid, paper])
        for p in parray:
            fp.write('  - ' + str(p[0]) + ' ' + str(p[1]) + ' from ' + str(p[2]) + '\n')
            if len(p[1]) >= 1:
                fp2.write('  - ' + str(p[0]) + ' ' + str(p[1]) + ' from ' + str(p[2]) + '\n')
    fp.close()
    fp2.close()

def export_spiresid_to_personid_validation(filename='/tmp/inspireid'):
    '''WARNING: still to be consolidated'''
    fp = open(filename, 'w')
    bibrefs = run_sql('SELECT id,tag,value,count(value)  FROM `bib70x` WHERE '
                      '`tag` LIKE \'700__i\' group by value order by value')
    realbibrefs = []
    fp.write('Inspireid->personid match:\n\n')
    for i in bibrefs:
        print 'considering:' + str(i)
#        bibref = run_sql('select id,value from bib70x where tag=\'700__a\' '
#                         'and (id) in (select id_bibxxx from bibrec_bib70x where '
#                         '(id_bibrec,field_number) in '
#                         '(select id_bibrec,field_number from bibrec_bib70x '
#                         'where id_bibxxx = \''+str(i[0])+'\'))')
        bibref = run_sql('select id,value from bib70x where tag=\'700__a\' '
                         'and (id) in '
                         '(select a.id_bibxxx from bibrec_bib70x as a inner join '
                         'bibrec_bib70x as b using(id_bibrec)'
                         'where a.field_number = b.field_number and '
                         'b.id_bibxxx = \'' + str(i[0]) + '\')')

        print '  found ' + str(bibref)
        for bib in bibref:
            fp.write(' -\n')
            pids = run_sql('select personid from aidPERSONID where tag=\'paper\''
                           ' and data like \'700:%,' + str(bib[0]) + '\'')
            fp.write(str(i) + ':\n')
            for pid in pids:
                names = run_sql('select data,flag from aidPERSONID where'
                                ' tag=\'gathered_name\''
                                ' and personID=\'' + str(pid[0]) + '\'')
                fp.write('  -' + str(pid) + ': ' + str(names) + '\n ')
        fp.write('\n')
    fp.close()

'''
User log case usages and contents reference.

Table structure:
    id  trans_id    timestamp   userinfo    personID    action  tag     value   comment
    int int         time        char255     int         char50  char50  char200 text
Operations on papers:
* Assignment:
    - assign bibrec,bibref to personid
        id    trans_id    timestamp   userinfo          personID    action   tag     value          comment
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        assign   paper   x00:xxxx,xxxx  NULL
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        assign   paper   x00:xxxx,xxxx  'telephone request of the author bla bla bla'
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        assign   paper   x00:xxxx,xxxx  'first manual assignment, moved from pid: xxxx'

* Rejection:
    - reject bibrec,bibref from personid
        id    trans_id    timestamp   userinfo          personID    action   tag     value          comment
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reject   paper   x00:xxxx,xxxx  NULL
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reject   paper   x00:xxxx,xxxx  'telephone request of the author bla bla bla'
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reject   paper   x00:xxxx,xxxx  'manual inspection of the paper'

* Reset:
    - Reset bibrec,bibref status (don't know who really is the author)
        id    trans_id    timestamp   userinfo          personID    action   tag     value          comment
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reset    paper   x00:xxxx,xxxx  NULL
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reset    paper   x00:xxxx,xxxx  'discovered error'
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        reset    paper   x00:xxxx,xxxx  'not enough information on the paper'

Action,tag allowed couples:
    * assign,paper
    * reject,paper
    * reset,paper

Operations on person ids:
* Add:
    - assign info to personid
        id    trans_id    timestamp   userinfo          personID    action   tag              value            comment
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        data_add inspire_uid      uid_inspire_xxx  NULL
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        data_add email_addr       xxx@xxx.xxx      NULL
        xxx   xxxxx       xxxx-xx-xx  uid_inspire_xxx   xxxx        data_mod email_addr       zzz@xxx.xxx      NULL

Action,tag allowed couples:
    * data_add,inspire_uid
    * data_add,email_addr
    * data_add,full_name
    * data_add,address
    * data_add,telephone_[home|office|...]
    ** data_mod, data_del: same as data_add

NOTE: new action/tag can be addedd as needed
NOTE: in case of need comment can be used instead of value (which is limited to 255 chars), but it is
        important to be consistent: if a field is using comment instead of value that _must_ be done _always_.

Automated operations:
* Table updates:
    - Update_authornames_table_from_paper
        id    trans_id    timestamp   userinfo          personID    action   tag       value          comment
        xxx   xxxxx       xxxx-xx-xx  daemon            -1          UATFP    bibsched  status         NULL

Actions:
    * update_auntornames_table_from_paper: UATFP
    * authornames_tables_gc: ATGC
    * update_personid_table_from_paper: UPITFP
'''
def get_user_log(transactionid='', userinfo='', personID='', action='', tag='', value='', comment='', only_most_recent=False):
    '''
    Get user log table entry matching all the given parameters; all of them are optional.
    IF no parameters are given retuns the complete log table
    @param transactionid: id of the transaction
    @param userinfo: user name or identifier
    @param personid: id of the person involved
    @param action: action
    @param tag: tag
    @param value: value
    @param comment: comment
    '''
    sql_query = 'select * from aidUSERINPUTLOG where 1 '
    if transactionid:
        sql_query += ' and transactionid=\'' + str(transactionid) + '\''
    if userinfo:
        sql_query += ' and userinfo=\'' + str(userinfo) + '\''
    if personID:
        sql_query += ' and personid=\'' + str(personID) + '\''
    if action:
        sql_query += ' and action=\'' + str(action) + '\''
    if tag:
        sql_query += ' and tag=\'' + str(tag) + '\''
    if value:
        sql_query += ' and value=\'' + str(value) + '\''
    if comment:
        sql_query += ' and comment=\'' + str(comment) + '\''
    if only_most_recent:
        sql_query += ' order by timestamp desc limit 0,1'
    return run_sql(sql_query)

def insert_user_log(userinfo, personid, action, tag, value, comment='', transactionid=0, timestamp=''):
    '''
    Instert log entries in the user log table. For example of entres look at the table generation script.
    @param userinfo: username or user identifier
    @type: string
    @param personid: personid involved in the transaction
    @type: longint
    @param action: action type
    @type: string
    @param tag: tag
    @type: string
    @param value: value for the transaction
    @type: string
    @param comment: optional comment for the transaction
    @type: string
    @param transactionid: optional id for the transaction
    @type: longint
    @return: the transactionid
    @type: longint
    '''
    if transactionid == 0:
        transactionid = max(run_sql('SELECT  MAX(transactionid) FROM `aidUSERINPUTLOG`')[0][0], -1) + 1

    if timestamp:
        tsui = '\',\'' + str(timestamp) + '\',\'' + str(userinfo)
    else:
        tsui = '\',now(),\'' + str(userinfo)

    run_sql('insert into aidUSERINPUTLOG (transactionid,timestamp,userinfo,personid,'
            'action,tag,value,comment) values'
            '(\'' + str(transactionid) +
            tsui +
            '\',\'' + str(personid) +
            '\',\'' + str(action) +
            '\',\'' + str(tag) +
            '\',\'' + str(value) +
            '\',\'' + str(comment) + '\')')
    return transactionid


def create_persistent_tables():
    '''
    Creates the personID tables. Separated process from create_database_tables()
    becouse those would like to be persistent tables while the others are likely
    to change as the algorithm gets improved.

    This script is kept here as a development utility, to allow easy db tables creation
    without need of a reinstall of invenio.
    '''
#    source = open("/opt/cds-invenio/etc/bibauthorid/personid_table_structures.sql", 'r')
#    query = source.read()
#    qcount = query.count("CREATE")

#    if qcount > 0:
#        run_sql(query)
#        run_sql("COMMIT;")

#    bconfig.LOGGER.log(25, "Done. Created %s tables. Please check if there "
#                        "now exist %s tables with the prefix 'aid_'."
#                        % (qcount, qcount))
    run_sql('''
    --
--WARNING: this creation scripts are carboncopied in miscutil/sql/tabcreate.sql
--  to have all the tables created at installation time.
-- Remember to propagate any changes!
--

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- Table structure for table `aid_personid`
--
-- 1	1	paper	100:1234	2
-- 2    5	hepname	123456		1
--		name|affiliation|whatever
-- flag values:
--  +2: user approved the paper-person assignment -> don't touch!
--  +1: Automatically attached by authorid algorithm with a probability of >= .75
--   0: Automatically attached by authorid algorithm with a probability of >= .5
--  -1: Automatically attached by authorid algorithm with a probability of < .5
--     and serves as an indicator for showing the record on the UI. Prevents
--     error-prone merges in the person id creator.
--  -2: user disapproved the paper-person assignment -> try to find
--     new person in the next iteration of the algo while disregarding
--     the paper-person assigned defined by this row
--  <-2 or >2: Internal algorithm flags. Free for future use.

CREATE TABLE IF NOT EXISTS `aidPERSONID` (
  `id` bigint(15) NOT NULL AUTO_INCREMENT,
  `personid` bigint(15) NOT NULL,
  `tag` varchar(50) NOT NULL,
  `data` varchar(250) NOT NULL,
  `flag` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  INDEX `personid-b` (`personid`),
  INDEX `tag-b` (`tag`),
  INDEX `data-b` (`data`),
  FULLTEXT  INDEX `data-t` (`data`),
  INDEX `flag-b` (`flag`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 ;

-- --------------------------------------------------------
--
-- Table structure for table `aid_user_input_log`
--
-- 1  1  2010-09-30 19:30  admin||10.0.0.1  1  assign  paper  1133:4442 'from 23'
--	a paper has been assigned to 1 (flag = 2); before it was of 23
-- 2  1  2010-09-30 19:30  admin||10.0.0.1  1  assign  paper  8147:4442
-- 3  2  2010-09-30 19:35  admin||10.0.0.1  1  reject  paper  72:4442
--	paper 72:4442 was surely not written by 1 (flag=-2)
-- 4  3  2010-09-30 19:40  admin||10.0.0.1  2  assign  paper  1133:4442
-- 5  4  2010-09-30 19:48  admin||10.0.0.1  12 reset   paper  1133:4442 'from 12'
--	somehow we no longer have info on 1133:4442 (flag=0)
-- 6  5  2010-09-30 19:48  admin||10.0.0.1  5  data_add data	name:cristoforocolombo 'not sure of the spelling'
-- 7  6  2010-09-30 19:48  admin||10.0.0.1  5  data_rem data 	name:cristoforocolombo 'it was wrong'
-- 8  7  2010-09-30 19:48  admin||10.0.0.1  6  data_alter data	email:aoeu@aoeu.oue 'got new valid address'

CREATE TABLE IF NOT EXISTS `aidUSERINPUTLOG` (
  `id` bigint(15) NOT NULL AUTO_INCREMENT,
  `transactionid` bigint(15) NOT NULL,
  `timestamp` datetime NOT NULL,
  `userinfo` varchar(255) NOT NULL,
  `personid` bigint(15) NOT NULL,
  `action` varchar(50) NOT NULL,
  `tag` varchar(50) NOT NULL,
  `value` varchar(200) NOT NULL,
  `comment` text,
  PRIMARY KEY (`id`),
  INDEX `transactionid-b` (`transactionid`),
  INDEX `timestamp-b` (`timestamp`),
  INDEX `userinfo-b` (`userinfo`),
  FULLTEXT INDEX `userinfo-t` (`userinfo`),
  INDEX `personid-b` (`personid`),
  INDEX `action-b` (`action`),
  INDEX `tag-b` (`tag`),
  INDEX `value-b` (`value`),
  FULLTEXT INDEX `value-t` (`value`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;
    ''')


def export_personID_to_human_readable_file(filename='/tmp/hrexport.txt', Pids=[]):
    '''
    @deprecated: support for legacy software
    Export the personID of each document to a human readable file, for brief inspection purposes.
    @param file: filename to output to
    @type: string
    @param Pids: list of persons ids to limit the export
    @type: (('2',),)
    '''
    if len(Pids) == 0:
        Pids = run_sql('SELECT DISTINCT `PersonID` FROM `aidPERSONID`')# LIMIT 1,20')

    destfile = open(filename, 'w')

    for pid in Pids:
        if bconfig.TABLES_UTILS_DEBUG:
            print 'Exporting ' + str(pid) + '...'
        infos = run_sql('SELECT tag,data FROM `aidPERSONID` where PersonID=\''
                       + str(pid[0]) + '\' and not tag=\'paper\'')
        docs = run_sql('SELECT `data` FROM `aidPERSONID` where PersonID=\''
                      + str(pid[0]) + '\' and tag=\'paper\' and flag>=\'-1\'')
        destfile.write('Person ID: ' + str(pid[0]) + '\n')
        for info in infos:
            destfile.write('  info [' + str(info[0]) + ']: ' + str(info[1]) + '\n')
        for doc in docs:
            #title = run_sql('SELECT `value` FROM `bib24x` WHERE  `id` in \
            #        ((select id_bibxxx from bibrec_bib24x where id_bibrec=\'' + str(doc[0].split(',')[1]) + '\')) and tag=\'245__a\'')
            #id = run_sql('SELECT `id_bibxxx` FROM `bibrec_bib' + ('10' if str(doc[0].split(',')[0].split(':')[0]) == '100' else '70')
            #              + 'x` WHERE  and `id`=\'' + str(doc[0].split(',')[0].split(':')[1]) + '\'')

            title = "No title on paper..."

            try:
                title = get_record(int(doc[0].split(',')[1]))['245'][0][0][0][1]
            except (IndexError, KeyError, ValueError):
                title = "Problem encountered while retrieving document title"

            dsplit = doc[0].split(',')
            tnum = "70"

            if str(dsplit[0].split(':')[0]) == "100":
                tnum = "10"

            authorname = run_sql("SELECT value FROM bib%sx "
                                 "WHERE  id = %s" %
                                 (tnum, dsplit[0].split(':')[1]))
            destfile.write('  name: ' + str(authorname)
                + ' paper: [' + str(doc[0]) + ']: ' + str(title) + '\n')
        destfile.write('------------------------------------------------------------------------------\n')
    destfile.close()


def export_personID_to_spires(filename='/tmp/spiresexport.txt', Pids=[]):
    '''
    @deprecated: support for legacy software
    Export the personID of each document to SPIRES syntax.
    @param file: filename to output to
    @type: string
    @param Pids: list of persons ids to limit the export
    @type: (('2',),)
    '''
    if len(Pids) == 0:
        Pids = run_sql('SELECT DISTINCT `PersonID` FROM `aidPERSONID`')# LIMIT 0,20')

    destfile = open(filename, 'w')

    for pid in Pids:
        if bconfig.TABLES_UTILS_DEBUG:
            print 'Exporting ' + str(pid) + '...'
        docs = run_sql('SELECT `data` FROM `aidPERSONID` where PersonID=\''
                      + str(pid[0]) + '\' and tag=\'paper\' and flag>=\'-1\'')
        for doc in docs:
            f970a = docs = run_sql('SELECT `value` FROM `bib97x` where id=\''
                                + str(doc[0].split(',')[1])
                                + '\' and tag=\'970__a\'')

            dsplit = doc[0].split(',')
            tnum = "70"

            if str(dsplit[0].split(':')[0]) == "100":
                tnum = "10"

            author_number = run_sql("SELECT field_number FROM bibrec_bib%sx "
                                    "WHERE  id_bibrec = %s "
                                    "AND id_bibxxx = %s" %
                                    (tnum, dsplit[1], dsplit[0].split(':')[1]))

            author_offset = run_sql("SELECT min(field_number) FROM bibrec_bib%sx "
                                    "WHERE id_bibrec = %s" %
                                    (tnum, dsplit[1]))

#            print  f970a, author_number, doc
#            if len(author_number) >= 1:
#                destfile.write('merge = ' + str(f970a[0][0].split('-')[1]) + ';\nastr('
#                               + str(author_number[0][0]) + ');\nauthor-note(100)=INSPIRE-AUTO-'
#                               + str(pid[0]) + ';\n;\n')


            if str(doc[0].split(',')[0].split(':')[0]) == '100':
                author_exp = 1
            else:
                if len(author_number) >= 1:
                    author_exp = author_number[0][0] - author_offset[0][0] + 2
                else:
                    if bconfig.TABLES_UTILS_DEBUG:
                        print "No authornumber, setting -1!!!"
                    author_exp = -1


            if bconfig.TABLES_UTILS_DEBUG:
                print  f970a, author_number, author_offset, author_exp, doc


            destfile.write('merge = ' + str(f970a[0][0].split('-')[1]) + ';\nastr('
                           + str(author_exp) + ');\nauthor-note(100)=INSPIRE-AUTO-'
                           + str(pid[0]) + ';\n;\n')

    destfile.close()
    #        IRN = <value of 970a>;
    #        ASTR;
    #        A= <author name from record>;
    #        AFF = <affiliation from record 100/700u>;
    #        DESY-AUTHOR = INSPIRE-BIBAUTHOR-<ID from bibauthor>;

def user_can_modify_data(uid, pid):
    '''
    Return True if the uid can modify data of this personID, false otherwise.
    @param uid: the user id
    @type: int
    @param pid: the person id
    @type: int
    '''
    pid_uid = run_sql("select data from aidPERSONID where tag = %s and personid = %s", ('uid', str(pid)))
    if len(pid_uid) >= 1:
        if str(uid) == str(pid_uid[0][0]):
            if acc_authorize_action(uid, bconfig.CMP_CHANGE_OWN_DATA)[0] == 0:
                return True
        if acc_authorize_action(uid, bconfig.CMP_CHANGE_OTHERS_DATA)[0] == 0:
            return True

        return False
    else:
        if acc_authorize_action(uid, bconfig.CMP_CHANGE_OTHERS_DATA)[0] == 0:
            return True

        return False

def user_can_modify_paper(uid, paper):
    '''
    Return True if the uid can modify this paper, false otherwise.
    If the paper is assigned more then one time (from algorithms) consider the most privileged
    assignment.
    @param uid: the user id
    @type: int
    @param paper: the paper bibref,bibrec pair x00:1234,4321
    @type: str
    '''
    prow = run_sql("select * from aidPERSONID where tag=%s and data =%s"
                   "order by lcul desc limit 0,1", ('paper', str(paper)))

    if len(prow) == 0:
        if ((acc_authorize_action(uid, bconfig.CMP_CLAIM_OWN_PAPERS)[0] == 0) or (acc_authorize_action(uid, bconfig.CMP_CLAIM_OTHERS_PAPERS)[0] == 0)):
            return True

        return False

    min_req_acc_n = int(prow[0][5])
    req_acc = resolve_paper_access_right(bconfig.CMP_CLAIM_OWN_PAPERS)
    pid_uid = run_sql("select data from aidPERSONID where tag = %s and personid = %s", ('uid', str(prow[0][1])))
    if len(pid_uid) > 0:
        if (str(pid_uid[0][0]) != str(uid)) and min_req_acc_n > 0:
            req_acc = resolve_paper_access_right(bconfig.CMP_CLAIM_OTHERS_PAPERS)

    if min_req_acc_n < req_acc:
        min_req_acc_n = req_acc

    min_req_acc = resolve_paper_access_right(min_req_acc_n)

    if (acc_authorize_action(uid, min_req_acc)[0] == 0) and (resolve_paper_access_right(min_req_acc) >= min_req_acc_n):
        return True
    else:
        return False

def resolve_paper_access_right(acc):
    '''
    Given a string or an integer, resolves to the corresponding integer or string
    If asked for a wrong/not present parameter falls back to the minimum privilege.
    '''
    access_dict = {bconfig.CMP_VIEW_PID_UNIVERSE: 0,
                  bconfig.CMP_CLAIM_OWN_PAPERS: 25,
                  bconfig.CMP_CLAIM_OTHERS_PAPERS: 50}

    if isinstance(acc, str):
        try:
            return access_dict[acc]
        except:
            return 0

    inverse_dict = dict([[v, k] for k, v in access_dict.items()])
    lower_accs = [a for a in inverse_dict.keys() if a <= acc]
    try:
        return inverse_dict[max(lower_accs)]
    except:
        return bconfig.CMP_VIEW_PID_UNIVERSE


def resolve_data_access_right(acc):
    '''
    Given a string or an integer, resolves to the corresponding integer or string
    If asked for a wrong/not present parameter falls back to the minimum privilege.
    '''
    access_dict = {bconfig.CMP_VIEW_PID_UNIVERSE: 0,
                   bconfig.CMP_CHANGE_OWN_DATA: 25,
                   bconfig.CMP_CHANGE_OTHERS_DATA: 50}

    if isinstance(acc, str):
        try:
            return access_dict[acc]
        except:
            return 0

    inverse_dict = dict([[v, k] for k, v in access_dict.items()])
    lower_accs = [a for a in inverse_dict.keys() if a <= acc]
    try:
        return inverse_dict[max(lower_accs)]
    except:
        return bconfig.CMP_VIEW_PID_UNIVERSE


def person_bibref_is_touched(pid, bibref):
    '''
    Determines if a record attached to a person has been touched by a human
    by checking the flag.

    @param pid: The Person ID of the person to check the assignment from
    @type pid: int
    @param bibref: The paper identifier to be checked (e.g. "100:12,144")
    @type bibref: string
    '''
    if not isinstance(pid, int):
        try:
            pid = int(pid)
        except (ValueError, TypeError):
            raise ValueError("Person ID has to be a number!")

    if not bibref:
        raise ValueError("A bibref is expected!")

    flag = run_sql("SELECT flag FROM aidPERSONID WHERE "
                   "personid = %s AND tag = 'paper' AND data = %s"
                   , (pid, bibref))

    try:
        flag = flag[0][0]
    except (IndexError):
        return False

    if not flag:
        return False
    elif - 2 < flag < 2:
        return False
    else:
        return True
#action list:
#view_pid_world
#change_own_data
#change_others_dataĹ
#claim_own_papers
#claim_others_papers
