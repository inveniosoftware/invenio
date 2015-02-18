# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2010, 2011, 2014, 2015 CERN.
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

__revision__ = "$Id$"

import ConfigParser

import math

import re

import sys

import time

import urllib

from six import iteritems

from intbitset import intbitset

from invenio.ext.logging import register_exception
from invenio.legacy.dbquery import run_sql
from invenio.legacy.bibindex.engine import beautify_range_list, \
    kill_sleepy_mysql_threads, create_range_list
from invenio.legacy.bibindex.engine_stemmer import is_stemmer_available_for_language, stem
from invenio.legacy.bibindex.engine_stopwords import is_stopword
from invenio.legacy.bibsched.bibtask import write_message, task_get_option, task_update_progress, \
    task_update_status, task_sleep_now_if_required
from invenio.legacy.search_engine import perform_request_search, wash_index_term
from invenio.modules.ranker.registry import configuration
from invenio.utils.serializers import serialize_via_marshal, deserialize_via_marshal
from invenio.utils.text import strip_accents

from sqlalchemy.exc import DatabaseError


options = {} # global variable to hold task options

# safety parameters concerning DB thread-multiplication problem:
CFG_CHECK_MYSQL_THREADS = 0 # to check or not to check the problem?
CFG_MAX_MYSQL_THREADS = 50 # how many threads (connections) we consider as still safe
CFG_MYSQL_THREAD_TIMEOUT = 20 # we'll kill threads that were sleeping for more than X seconds

# override urllib's default password-asking behaviour:
class MyFancyURLopener(urllib.FancyURLopener):
    def prompt_user_passwd(self, host, realm):
        # supply some dummy credentials by default
        return ("mysuperuser", "mysuperpass")
    def http_error_401(self, url, fp, errcode, errmsg, headers):
        # do not bother with protected pages
        raise IOError, (999, 'unauthorized access')
        return None

#urllib._urlopener = MyFancyURLopener()


nb_char_in_line = 50  # for verbose pretty printing
chunksize = 1000 # default size of chunks that the records will be treated by
base_process_size = 4500 # process base size

# Dictionary merging functions
def dict_union(list1, list2):
    "Returns union of the two dictionaries."
    union_dict = {}

    for (e, count) in iteritems(list1):
        union_dict[e] = count
    for (e, count) in iteritems(list2):
        if e not in union_dict:
            union_dict[e] = count
        else:
            union_dict[e] = (union_dict[e][0] + count[0], count[1])

    #for (e, count) in iteritems(list2):
    #    list1[e] = (list1.get(e, (0, 0))[0] + count[0], count[1])

    #return list1
    return union_dict

# tagToFunctions mapping. It offers an indirection level necesary for
# indexing fulltext. The default is get_words_from_phrase
tagToWordsFunctions = {}

def get_words_from_phrase(phrase, weight, lang="",
                          chars_punctuation=r"[\.\,\:\;\?\!\"]",
                          chars_alphanumericseparators=r"[1234567890\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]",
                          split=str.split):
    "Returns list of words from phrase 'phrase'."
    words = {}
    phrase = strip_accents(phrase)
    phrase = phrase.lower()
    #Getting rid of strange characters
    phrase = re.sub("&eacute;", 'e', phrase)
    phrase = re.sub("&egrave;", 'e', phrase)
    phrase = re.sub("&agrave;", 'a', phrase)
    phrase = re.sub("&nbsp;", ' ', phrase)
    phrase = re.sub("&laquo;", ' ', phrase)
    phrase = re.sub("&raquo;", ' ', phrase)
    phrase = re.sub("&ecirc;", ' ', phrase)
    phrase = re.sub("&amp;", ' ', phrase)
    if phrase.find("</") > -1:
        #Most likely html, remove html code
        phrase = re.sub("(?s)<[^>]*>|&#?\w+;", ' ', phrase)
    #removes http links
    phrase = re.sub("(?s)http://[^( )]*", '', phrase)
    phrase = re.sub(chars_punctuation, ' ', phrase)

    #By doing this like below, characters standing alone, like c a b is not added to the inedx, but when they are together with characters like c++ or c$ they are added.
    for word in split(phrase):
        if options["remove_stopword"] == "True" and not is_stopword(word) and check_term(word, 0):
            if lang and lang !="none" and options["use_stemming"]:
                word = stem(word, lang)
                if word not in words:
                    words[word] = (0, 0)
            else:
                if word not in words:
                    words[word] = (0, 0)
            words[word] = (words[word][0] + weight, 0)
        elif options["remove_stopword"] == "True" and not is_stopword(word):
            phrase = re.sub(chars_alphanumericseparators, ' ', word)
            for word_ in split(phrase):
                if lang and lang !="none" and options["use_stemming"]:
                    word_ = stem(word_, lang)
                if word_:
                    if word_ not in words:
                        words[word_] = (0,0)
                    words[word_] = (words[word_][0] + weight, 0)
    return words

class WordTable:
    "A class to hold the words table."

    def __init__(self, tablename, fields_to_index, separators="[^\s]"):
        "Creates words table instance."
        self.tablename = tablename
        self.recIDs_in_mem = []
        self.fields_to_index = fields_to_index
        self.separators = separators
        self.value = {}

    def get_field(self, recID, tag):
        """Returns list of values of the MARC-21 'tag' fields for the
           record 'recID'."""

        out = []
        bibXXx = "bib" + tag[0] + tag[1] + "x"
        bibrec_bibXXx = "bibrec_" + bibXXx
        query = """SELECT value FROM %s AS b, %s AS bb
                WHERE bb.id_bibrec=%s AND bb.id_bibxxx=b.id
                AND tag LIKE '%s'""" % (bibXXx, bibrec_bibXXx, recID, tag);
        res = run_sql(query)
        for row in res:
            out.append(row[0])
        return out

    def clean(self):
        "Cleans the words table."
        self.value={}

    def put_into_db(self, mode="normal"):
        """Updates the current words table in the corresponding DB
           rnkWORD table.  Mode 'normal' means normal execution,
           mode 'emergency' means words index reverting to old state.
           """
        write_message("%s %s wordtable flush started" % (self.tablename,mode))
        write_message('...updating %d words into %sR started' % \
                (len(self.value), self.tablename[:-1]))
        task_update_progress("%s flushed %d/%d words" % (self.tablename, 0, len(self.value)))

        self.recIDs_in_mem = beautify_range_list(self.recIDs_in_mem)

        if mode == "normal":
            for group in self.recIDs_in_mem:
                query = """UPDATE %sR SET type='TEMPORARY' WHERE id_bibrec
                BETWEEN '%d' AND '%d' AND type='CURRENT'""" % \
                (self.tablename[:-1], group[0], group[1])
                write_message(query, verbose=9)
                run_sql(query)

        nb_words_total = len(self.value)
        nb_words_report = int(nb_words_total/10)
        nb_words_done = 0
        for word in self.value.keys():
            self.put_word_into_db(word, self.value[word])
            nb_words_done += 1
            if nb_words_report!=0 and ((nb_words_done % nb_words_report) == 0):
                write_message('......processed %d/%d words' % (nb_words_done, nb_words_total))
                task_update_progress("%s flushed %d/%d words" % (self.tablename, nb_words_done, nb_words_total))
        write_message('...updating %d words into %s ended' % \
                (nb_words_total, self.tablename), verbose=9)

        #if options["verbose"]:
        #    write_message('...updating reverse table %sR started' % self.tablename[:-1])
        if mode == "normal":
            for group in self.recIDs_in_mem:
                query = """UPDATE %sR SET type='CURRENT' WHERE id_bibrec
                BETWEEN '%d' AND '%d' AND type='FUTURE'""" % \
                (self.tablename[:-1], group[0], group[1])
                write_message(query, verbose=9)
                run_sql(query)
                query = """DELETE FROM %sR WHERE id_bibrec
                BETWEEN '%d' AND '%d' AND type='TEMPORARY'""" % \
                (self.tablename[:-1], group[0], group[1])
                write_message(query, verbose=9)
                run_sql(query)
            write_message('End of updating wordTable into %s' % self.tablename, verbose=9)
        elif mode == "emergency":
            write_message("emergency")
            for group in self.recIDs_in_mem:
                query = """UPDATE %sR SET type='CURRENT' WHERE id_bibrec
                BETWEEN '%d' AND '%d' AND type='TEMPORARY'""" % \
                (self.tablename[:-1], group[0], group[1])
                write_message(query, verbose=9)
                run_sql(query)
                query = """DELETE FROM %sR WHERE id_bibrec
                BETWEEN '%d' AND '%d' AND type='FUTURE'""" % \
                (self.tablename[:-1], group[0], group[1])
                write_message(query, verbose=9)
                run_sql(query)
            write_message('End of emergency flushing wordTable into %s' % self.tablename, verbose=9)
        #if options["verbose"]:
        #    write_message('...updating reverse table %sR ended' % self.tablename[:-1])

        self.clean()
        self.recIDs_in_mem = []
        write_message("%s %s wordtable flush ended" % (self.tablename, mode))
        task_update_progress("%s flush ended" % (self.tablename))

    def load_old_recIDs(self,word):
        """Load existing hitlist for the word from the database index files."""
        query = "SELECT hitlist FROM %s WHERE term=%%s" % self.tablename
        res = run_sql(query, (word,))
        if res:
            return deserialize_via_marshal(res[0][0])
        else:
            return None

    def merge_with_old_recIDs(self,word,recIDs, set):
        """Merge the system numbers stored in memory (hash of recIDs with value[0] > 0 or -1
        according to whether to add/delete them) with those stored in the database index
        and received in set universe of recIDs for the given word.

        Return 0 in case no change was done to SET, return 1 in case SET was changed.
        """

        set_changed_p = 0
        for recID,sign in iteritems(recIDs):
            if sign[0] == -1 and recID in set:
                # delete recID if existent in set and if marked as to be deleted
                del set[recID]
                set_changed_p = 1
            elif sign[0] > -1 and recID not in set:
                # add recID if not existent in set and if marked as to be added
                set[recID] = sign
                set_changed_p = 1
            elif sign[0] > -1 and sign[0] != set[recID][0]:
                set[recID] = sign
                set_changed_p = 1

        return set_changed_p

    def put_word_into_db(self, word, recIDs, split=str.split):
        """Flush a single word to the database and delete it from memory"""
        set = self.load_old_recIDs(word)
        #write_message("%s %s" % (word, self.value[word]))
        if set is not None: # merge the word recIDs found in memory:
            options["modified_words"][word] = 1
            if not self.merge_with_old_recIDs(word, recIDs, set):
                # nothing to update:
                write_message("......... unchanged hitlist for ``%s''" % word, verbose=9)
                pass
            else:
                # yes there were some new words:
                write_message("......... updating hitlist for ``%s''" % word, verbose=9)
                run_sql("UPDATE %s SET hitlist=%%s WHERE term=%%s" % self.tablename,
                        (serialize_via_marshal(set), word))
        else: # the word is new, will create new set:
            write_message("......... inserting hitlist for ``%s''" % word, verbose=9)
            set = self.value[word]
            if len(set) > 0:
                #new word, add to list
                options["modified_words"][word] = 1
                try:
                    run_sql("INSERT INTO %s (term, hitlist) VALUES (%%s, %%s)" % self.tablename,
                            (word, serialize_via_marshal(set)))
                except Exception as e:
                    ## FIXME: This is for debugging encoding errors
                    register_exception(prefix="Error when putting the term '%s' into db (hitlist=%s): %s\n" % (repr(word), set, e), alert_admin=True)
        if not set: # never store empty words
            run_sql("DELETE from %s WHERE term=%%s" % self.tablename,
                    (word,))

        del self.value[word]

    def display(self):
        "Displays the word table."
        keys = self.value.keys()
        keys.sort()
        for k in keys:
            write_message("%s: %s" % (k, self.value[k]))

    def count(self):
        "Returns the number of words in the table."
        return len(self.value)

    def info(self):
        "Prints some information on the words table."
        write_message("The words table contains %d words." % self.count())

    def lookup_words(self, word=""):
        "Lookup word from the words table."

        if not word:
            done = 0
            while not done:
                try:
                    word = raw_input("Enter word: ")
                    done = 1
                except (EOFError, KeyboardInterrupt):
                    return

        if word in self.value:
            write_message("The word '%s' is found %d times." \
                % (word, len(self.value[word])))
        else:
            write_message("The word '%s' does not exist in the word file."\
                              % word)

    def update_last_updated(self, rank_method_code, starting_time=None):
        """Update last_updated column of the index table in the database.
        Puts starting time there so that if the task was interrupted for record download,
        the records will be reindexed next time."""
        if starting_time is None:
            return None
        write_message("updating last_updated to %s..." % starting_time, verbose=9)
        return run_sql("UPDATE rnkMETHOD SET last_updated=%s WHERE name=%s",
                       (starting_time, rank_method_code,))

    def add_recIDs(self, recIDs):
        """Fetches records which id in the recIDs arange list and adds
        them to the wordTable.  The recIDs arange list is of the form:
        [[i1_low,i1_high],[i2_low,i2_high], ..., [iN_low,iN_high]].
        """
        global chunksize
        flush_count = 0
        records_done = 0
        records_to_go = 0

        for arange in recIDs:
            records_to_go = records_to_go + arange[1] - arange[0] + 1

        time_started = time.time() # will measure profile time
        for arange in recIDs:
            i_low = arange[0]
            chunksize_count = 0
            while i_low <= arange[1]:
                # calculate chunk group of recIDs and treat it:
                i_high = min(i_low+task_get_option("flush")-flush_count-1,arange[1])
                i_high = min(i_low+chunksize-chunksize_count-1, i_high)
                try:
                    self.chk_recID_range(i_low, i_high)
                except StandardError as e:
                    write_message("Exception caught: %s" % e, sys.stderr)
                    register_exception()
                    task_update_status("ERROR")
                    sys.exit(1)
                write_message("%s adding records #%d-#%d started" % \
                        (self.tablename, i_low, i_high))
                if CFG_CHECK_MYSQL_THREADS:
                    kill_sleepy_mysql_threads()
                task_update_progress("%s adding recs %d-%d" % (self.tablename, i_low, i_high))
                self.del_recID_range(i_low, i_high)
                just_processed = self.add_recID_range(i_low, i_high)
                flush_count = flush_count + i_high - i_low + 1
                chunksize_count = chunksize_count + i_high - i_low + 1
                records_done = records_done + just_processed
                write_message("%s adding records #%d-#%d ended  " % \
                        (self.tablename, i_low, i_high))
                if chunksize_count >= chunksize:
                    chunksize_count = 0
                # flush if necessary:
                if flush_count >= task_get_option("flush"):
                    self.put_into_db()
                    self.clean()
                    write_message("%s backing up" % (self.tablename))
                    flush_count = 0
                    self.log_progress(time_started,records_done,records_to_go)
                # iterate:
                i_low = i_high + 1
        if flush_count > 0:
            self.put_into_db()
            self.log_progress(time_started,records_done,records_to_go)

    def add_recIDs_by_date(self, dates=""):
        """Add recIDs modified between DATES[0] and DATES[1].
           If DATES is not set, then add records modified since the last run of
           the ranking method.
        """
        if not dates:
            write_message("Using the last update time for the rank method")
            query = """SELECT last_updated FROM rnkMETHOD WHERE name='%s'
            """ % options["current_run"]
            res = run_sql(query)

            if not res:
                return
            if not res[0][0]:
                dates = ("0000-00-00",'')
            else:
                dates = (res[0][0],'')

        query = """SELECT b.id FROM bibrec AS b WHERE b.modification_date >=
        '%s'""" % dates[0]
        if dates[1]:
            query += "and b.modification_date <= '%s'" % dates[1]
        query += " ORDER BY b.id ASC"""
        res = run_sql(query)

        alist = create_range_list([row[0] for row in res])
        if not alist:
            write_message( "No new records added. %s is up to date" % self.tablename)
        else:
            self.add_recIDs(alist)
        return alist


    def add_recID_range(self, recID1, recID2):
        """Add records from RECID1 to RECID2."""
        wlist = {}
        normalize = {}

        self.recIDs_in_mem.append([recID1,recID2])
        # secondly fetch all needed tags:

        for (tag, weight, lang) in self.fields_to_index:
            if tag in tagToWordsFunctions.keys():
                get_words_function = tagToWordsFunctions[tag]
            else:
                get_words_function = get_words_from_phrase
            bibXXx = "bib" + tag[0] + tag[1] + "x"
            bibrec_bibXXx = "bibrec_" + bibXXx
            query = """SELECT bb.id_bibrec,b.value FROM %s AS b, %s AS bb
                    WHERE bb.id_bibrec BETWEEN %d AND %d
                    AND bb.id_bibxxx=b.id AND tag LIKE '%s'""" % (bibXXx, bibrec_bibXXx, recID1, recID2, tag)
            res = run_sql(query)
            nb_total_to_read = len(res)
            verbose_idx = 0     # for verbose pretty printing
            for row in res:
                recID, phrase = row
                if recID in options["validset"]:
                    if recID not in wlist: wlist[recID] = {}
                    new_words = get_words_function(phrase, weight, lang) # ,self.separators
                    wlist[recID] = dict_union(new_words,wlist[recID])

        # were there some words for these recIDs found?
        if len(wlist) == 0: return 0
        recIDs = wlist.keys()
        for recID in recIDs:
            # was this record marked as deleted?
            if "DELETED" in self.get_field(recID, "980__c"):
                wlist[recID] = {}
                write_message("... record %d was declared deleted, removing its word list" % recID, verbose=9)
            write_message("... record %d, termlist: %s" % (recID, wlist[recID]), verbose=9)

        # put words into reverse index table with FUTURE status:
        for recID in recIDs:
            run_sql("INSERT INTO %sR (id_bibrec,termlist,type) VALUES (%%s,%%s,'FUTURE')" % self.tablename[:-1],
                    (recID, serialize_via_marshal(wlist[recID])))
            # ... and, for new records, enter the CURRENT status as empty:
            try:
                run_sql("INSERT INTO %sR (id_bibrec,termlist,type) VALUES (%%s,%%s,'CURRENT')" % self.tablename[:-1],
                        (recID, serialize_via_marshal([])))
            except DatabaseError:
                # okay, it's an already existing record, no problem
                pass

        # put words into memory word list:
        put = self.put
        for recID in recIDs:
            for (w, count) in iteritems(wlist[recID]):
                put(recID, w, count)

        return len(recIDs)

    def log_progress(self, start, done, todo):
        """Calculate progress and store it.
        start: start time,
        done: records processed,
        todo: total number of records"""
        time_elapsed = time.time() - start
        # consistency check
        if time_elapsed == 0 or done > todo:
            return

        time_recs_per_min = done/(time_elapsed/60.0)
        write_message("%d records took %.1f seconds to complete.(%1.f recs/min)"\
                % (done, time_elapsed, time_recs_per_min))

        if time_recs_per_min:
            write_message("Estimated runtime: %.1f minutes" % \
                    ((todo-done)/time_recs_per_min))

    def put(self, recID, word, sign):
        "Adds/deletes a word to the word list."
        try:
            word = wash_index_term(word)
            if word in self.value:
                # the word 'word' exist already: update sign
                self.value[word][recID] = sign
                # PROBLEM ?
            else:
                self.value[word] = {recID: sign}
        except:
            write_message("Error: Cannot put word %s with sign %d for recID %s." % (word, sign, recID))


    def del_recIDs(self, recIDs):
        """Fetches records which id in the recIDs range list and adds
        them to the wordTable.  The recIDs range list is of the form:
        [[i1_low,i1_high],[i2_low,i2_high], ..., [iN_low,iN_high]].
        """
        count = 0
        for range in recIDs:
            self.del_recID_range(range[0],range[1])
            count = count + range[1] - range[0]
        self.put_into_db()

    def del_recID_range(self, low, high):
        """Deletes records with 'recID' system number between low
           and high from memory words index table."""
        write_message("%s fetching existing words for records #%d-#%d started" % \
                (self.tablename, low, high), verbose=3)
        self.recIDs_in_mem.append([low,high])
        query = """SELECT id_bibrec,termlist FROM %sR as bb WHERE bb.id_bibrec
        BETWEEN '%d' AND '%d'""" % (self.tablename[:-1], low, high)
        recID_rows = run_sql(query)
        for recID_row in recID_rows:
            recID = recID_row[0]
            wlist = deserialize_via_marshal(recID_row[1])
            for word in wlist:
                self.put(recID, word, (-1, 0))
        write_message("%s fetching existing words for records #%d-#%d ended" % \
                (self.tablename, low, high), verbose=3)

    def check_bad_words(self):
        """
        Finds bad words in reverse tables. Returns the number of bad words.
        """
        query = """SELECT count(1) FROM %sR WHERE type IN ('TEMPORARY','FUTURE')""" % (self.tablename[:-1])
        res = run_sql(query)
        return res[0][0]

    def report_on_table_consistency(self):
        """Check reverse words index tables (e.g. rnkWORD01R) for
        interesting states such as 'TEMPORARY' state.
        Prints small report (no of words, no of bad words).
        """
        # find number of words:
        query = """SELECT COUNT(*) FROM %s""" % (self.tablename)
        res = run_sql(query, None, 1)
        if res:
            nb_words = res[0][0]
        else:
            nb_words = 0

        # report stats:
        write_message("%s contains %d words" % (self.tablename, nb_words))

        # find possible bad states in reverse tables:
        nb_bad_words = self.check_bad_words()
        if nb_bad_words:
            write_message("EMERGENCY: %s needs to repair %d of %d index records" %
                          (self.tablename, nb_bad_words, nb_words))
        else:
            write_message("%s is in consistent state" % (self.tablename))

    def repair(self):
        """Repair the whole table"""
        # find possible bad states in reverse tables:
        if self.check_bad_words() == 0:
            return

        query = """SELECT id_bibrec FROM %sR WHERE type in ('TEMPORARY','FUTURE')""" \
                % (self.tablename[:-1])
        res = intbitset(run_sql(query))
        recIDs = create_range_list(list(res))

        flush_count = 0
        records_done = 0
        records_to_go = 0

        for range in recIDs:
            records_to_go = records_to_go + range[1] - range[0] + 1

        time_started = time.time() # will measure profile time
        for range in recIDs:
            i_low = range[0]
            chunksize_count = 0
            while i_low <= range[1]:
                # calculate chunk group of recIDs and treat it:
                i_high = min(i_low+task_get_option("flush")-flush_count-1,range[1])
                i_high = min(i_low+chunksize-chunksize_count-1, i_high)
                try:
                    self.fix_recID_range(i_low, i_high)
                except StandardError as e:
                    write_message("Exception caught: %s" % e, sys.stderr)
                    register_exception()
                    task_update_status("ERROR")
                    sys.exit(1)

                flush_count = flush_count + i_high - i_low + 1
                chunksize_count = chunksize_count + i_high - i_low + 1
                records_done = records_done + i_high - i_low + 1
                if chunksize_count >= chunksize:
                    chunksize_count = 0
                # flush if necessary:
                if flush_count >= task_get_option("flush"):
                    self.put_into_db("emergency")
                    self.clean()
                    flush_count = 0
                    self.log_progress(time_started,records_done,records_to_go)
                # iterate:
                i_low = i_high + 1
        if flush_count > 0:
            self.put_into_db("emergency")
            self.log_progress(time_started,records_done,records_to_go)
        write_message("%s inconsistencies repaired." % self.tablename)

    def chk_recID_range(self, low, high):
        """Check if the reverse index table is in proper state"""
        ## check db
        query = """SELECT COUNT(*) FROM %sR WHERE type <> 'CURRENT'
        AND id_bibrec BETWEEN '%d' AND '%d'""" % (self.tablename[:-1], low, high)
        res = run_sql(query, None, 1)
        if res[0][0]==0:
            write_message("%s for %d-%d is in consistent state"%(self.tablename,low,high))
            return # okay, words table is consistent

        ## inconsistency detected!
        write_message("EMERGENCY: %s inconsistencies detected..." % self.tablename)
        write_message("""EMERGENCY: Errors found. You should check consistency of the %s - %sR tables.\nRunning 'bibrank --repair' is recommended.""" \
            % (self.tablename, self.tablename[:-1]))
        raise StandardError

    def fix_recID_range(self, low, high):
        """Try to fix reverse index database consistency (e.g. table rnkWORD01R) in the low,high doc-id range.

        Possible states for a recID follow:
        CUR TMP FUT: very bad things have happened: warn!
        CUR TMP    : very bad things have happened: warn!
        CUR     FUT: delete FUT (crash before flushing)
        CUR        : database is ok
            TMP FUT: add TMP to memory and del FUT from memory
                     flush (revert to old state)
            TMP    : very bad things have happened: warn!
                FUT: very bad things have happended: warn!
        """

        state = {}
        query = "SELECT id_bibrec,type FROM %sR WHERE id_bibrec BETWEEN '%d' AND '%d'"\
                % (self.tablename[:-1], low, high)
        res = run_sql(query)
        for row in res:
            if row[0] not in state:
                state[row[0]]=[]
            state[row[0]].append(row[1])

        ok = 1 # will hold info on whether we will be able to repair
        for recID in state.keys():
            if not 'TEMPORARY' in state[recID]:
                if 'FUTURE' in state[recID]:
                    if 'CURRENT' not in state[recID]:
                        write_message("EMERGENCY: Index record %d is in inconsistent state. Can't repair it" % recID)
                        ok = 0
                    else:
                        write_message("EMERGENCY: Inconsistency in index record %d detected" % recID)
                        query = """DELETE FROM %sR
                        WHERE id_bibrec='%d'""" % (self.tablename[:-1], recID)
                        run_sql(query)
                        write_message("EMERGENCY: Inconsistency in index record %d repaired." % recID)
            else:
                if 'FUTURE' in state[recID] and not 'CURRENT' in state[recID]:
                    self.recIDs_in_mem.append([recID,recID])
                    # Get the words file
                    query = """SELECT type,termlist FROM %sR
                    WHERE id_bibrec='%d'""" % (self.tablename[:-1], recID)
                    write_message(query, verbose=9)
                    res = run_sql(query)
                    for row in res:
                        wlist = deserialize_via_marshal(row[1])
                        write_message("Words are %s " % wlist, verbose=9)
                        if row[0] == 'TEMPORARY':
                            sign = 1
                        else:
                            sign = -1
                        for word in wlist:
                            self.put(recID, word, wlist[word])

                else:
                    write_message("EMERGENCY: %s for %d is in inconsistent state. Couldn't repair it." % (self.tablename, recID))
                    ok = 0

        if not ok:
            write_message("""EMERGENCY: Unrepairable errors found. You should check consistency
                of the %s - %sR tables. Deleting affected TEMPORARY and FUTURE entries
                from these tables is recommended; see the BibIndex Admin Guide.
                (The repairing procedure is similar for bibrank word indexes.)""" % (self.tablename, self.tablename[:-1]))
            raise StandardError

def word_index(run):
    """Run the indexing task.  The row argument is the BibSched task
    queue row, containing if, arguments, etc.
    Return 1 in case of success and 0 in case of failure.
    """
    global languages

    max_recid = 0
    res = run_sql("SELECT max(id) FROM bibrec")
    if res and res[0][0]:
        max_recid = int(res[0][0])

    options["run"] = []
    options["run"].append(run)
    for rank_method_code in options["run"]:
        task_sleep_now_if_required(can_stop_too=True)
        method_starting_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        write_message("Running rank method: %s" % getName(rank_method_code))
        try:
            config_file = configuration.get(rank_method_code + '.cfg', '')
            config = ConfigParser.ConfigParser()
            config.readfp(open(config_file))
        except StandardError as e:
            write_message("Cannot find configurationfile: %s" % config_file, sys.stderr)
            raise StandardError
        options["current_run"] = rank_method_code
        options["modified_words"] = {}
        options["table"] = config.get(config.get("rank_method", "function"), "table")
        options["use_stemming"] = config.get(config.get("rank_method","function"),"stemming")
        options["remove_stopword"] = config.get(config.get("rank_method","function"),"stopword")
        tags = get_tags(config) #get the tags to include
        options["validset"] = get_valid_range(rank_method_code) #get the records from the collections the method is enabled for
        function = config.get("rank_method","function")
        wordTable = WordTable(options["table"], tags)
        wordTable.report_on_table_consistency()
        try:
            if task_get_option("cmd") == "del":
                if task_get_option("id"):
                    wordTable.del_recIDs(task_get_option("id"))
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("collection"):
                    l_of_colls = task_get_option("collection").split(",")
                    recIDs = perform_request_search(c=l_of_colls)
                    recIDs_range = []
                    for recID in recIDs:
                        recIDs_range.append([recID,recID])
                    wordTable.del_recIDs(recIDs_range)
                    task_sleep_now_if_required(can_stop_too=True)
                else:
                    write_message("Missing IDs of records to delete from index %s.", wordTable.tablename,
                                  sys.stderr)
                    raise StandardError
            elif task_get_option("cmd") == "add":
                if task_get_option("id"):
                    wordTable.add_recIDs(task_get_option("id"))
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("collection"):
                    l_of_colls = task_get_option("collection").split(",")
                    recIDs = perform_request_search(c=l_of_colls)
                    recIDs_range = []
                    for recID in recIDs:
                        recIDs_range.append([recID,recID])
                    wordTable.add_recIDs(recIDs_range)
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("last_updated"):
                    wordTable.add_recIDs_by_date("")
                    # only update last_updated if run via automatic mode:
                    wordTable.update_last_updated(rank_method_code, method_starting_time)
                    task_sleep_now_if_required(can_stop_too=True)
                elif task_get_option("modified"):
                    wordTable.add_recIDs_by_date(task_get_option("modified"))
                    task_sleep_now_if_required(can_stop_too=True)
                else:
                    wordTable.add_recIDs([[0,max_recid]])
                    task_sleep_now_if_required(can_stop_too=True)
            elif task_get_option("cmd") == "repair":
                wordTable.repair()
                check_rnkWORD(options["table"])
                task_sleep_now_if_required(can_stop_too=True)
            elif task_get_option("cmd") == "check":
                check_rnkWORD(options["table"])
                options["modified_words"] = {}
                task_sleep_now_if_required(can_stop_too=True)
            elif task_get_option("cmd") == "stat":
                rank_method_code_statistics(options["table"])
                task_sleep_now_if_required(can_stop_too=True)
            else:
                write_message("Invalid command found processing %s" % \
                     wordTable.tablename, sys.stderr)
                raise StandardError
            update_rnkWORD(options["table"], options["modified_words"])
            task_sleep_now_if_required(can_stop_too=True)
        except StandardError as e:
            register_exception(alert_admin=True)
            write_message("Exception caught: %s" % e, sys.stderr)
            sys.exit(1)
        wordTable.report_on_table_consistency()
    # We are done. State it in the database, close and quit

    return 1

def get_tags(config):
    """Get the tags that should be used creating the index and each tag's parameter"""
    tags = []
    function = config.get("rank_method","function")
    i = 1
    shown_error = 0

    #try:
    if 1:
        while config.has_option(function,"tag%s"% i):
            tag = config.get(function, "tag%s" % i)
            tag = tag.split(",")
            tag[1] = int(tag[1].strip())
            tag[2] = tag[2].strip()

            #check if stemmer for language is available
            if config.get(function, "stemming") and stem("information", "en") != "inform":
                if shown_error == 0:
                    write_message("Warning: Stemming not working. Please check it out!")
                    shown_error = 1
            elif tag[2] and tag[2] != "none" and config.get(function,"stemming") and not is_stemmer_available_for_language(tag[2]):
                write_message("Warning: Stemming not available for language '%s'." % tag[2])
            tags.append(tag)
            i += 1
    #except Exception:
    #    write_message("Could not read data from configuration file, please check for errors")
    #    raise StandardError

    return tags

def get_valid_range(rank_method_code):
    """Returns which records are valid for this rank method, according to which collections it is enabled for."""

    #if options["verbose"] >=9:
    #    write_message("Getting records from collections enabled for rank method.")
    #res = run_sql("SELECT collection.name FROM collection,collection_rnkMETHOD,rnkMETHOD WHERE collection.id=id_collection and id_rnkMETHOD=rnkMETHOD.id and rnkMETHOD.name='%s'" %  rank_method_code)
    #l_of_colls = []
    #for coll in res:
    #    l_of_colls.append(coll[0])
    #if len(l_of_colls) > 0:
    #    recIDs = perform_request_search(c=l_of_colls)
    #else:
    #    recIDs = []

    valid = intbitset(trailing_bits=1)
    valid.discard(0)

    #valid.addlist(recIDs)
    return valid

def check_term(term, termlength):
    """Check if term contains not allowed characters, or for any other reasons for not using this term."""
    try:
        if len(term) <= termlength:
            return False
        reg = re.compile(r"[1234567890\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]")
        if re.search(reg, term):
            return False
        term = str.replace(term, "-", "")
        term = str.replace(term, ".", "")
        term = str.replace(term, ",", "")
        if int(term):
            return False
    except StandardError as e:
        pass
    return True

def check_rnkWORD(table):
    """Checks for any problems in rnkWORD tables."""
    i = 0
    errors = {}
    termslist = run_sql("SELECT term FROM %s" % table)
    N = run_sql("select max(id_bibrec) from %sR" % table[:-1])[0][0]
    write_message("Checking integrity of rank values in %s" % table)
    terms = map(lambda x: x[0], termslist)

    while i < len(terms):
        query_params = ()
        for j in range(i, ((i+5000)< len(terms) and (i+5000) or len(terms))):
            query_params += (terms[j],)
        terms_docs = run_sql("SELECT term, hitlist FROM %s WHERE term IN (%s)" % (table, (len(query_params)*"%s,")[:-1]),
                             query_params)
        for (t, hitlist) in terms_docs:
            term_docs = deserialize_via_marshal(hitlist)
            if ("Gi" in term_docs and term_docs["Gi"][1] == 0) or "Gi" not in term_docs:
                write_message("ERROR: Missing value for term: %s (%s) in %s: %s" % (t, repr(t), table, len(term_docs)))
                errors[t] = 1
        i += 5000
    write_message("Checking integrity of rank values in %sR" % table[:-1])
    i = 0
    while i < N:
        docs_terms = run_sql("SELECT id_bibrec, termlist FROM %sR WHERE id_bibrec>=%s and id_bibrec<=%s" % (table[:-1], i, i+5000))
        for (j, termlist) in docs_terms:
            termlist = deserialize_via_marshal(termlist)
            for (t, tf) in iteritems(termlist):
                if tf[1] == 0 and t not in errors:
                    errors[t] = 1
                    write_message("ERROR: Gi missing for record %s and term: %s (%s) in %s" % (j,t,repr(t), table))
                    terms_docs = run_sql("SELECT term, hitlist FROM %s WHERE term=%%s" % table, (t,))
                    termlist = deserialize_via_marshal(terms_docs[0][1])
            i += 5000

    if len(errors) == 0:
        write_message("No direct errors found, but nonconsistent data may exist.")
    else:
        write_message("%s errors found during integrity check, repair and rebalancing recommended." % len(errors))
    options["modified_words"] = errors

def rank_method_code_statistics(table):
    """Shows some statistics about this rank method."""

    maxID = run_sql("select max(id) from %s" % table)
    maxID = maxID[0][0]
    terms = {}
    Gi = {}

    write_message("Showing statistics of terms in index:")
    write_message("Important: For the 'Least used terms', the number of terms is shown first, and the number of occurences second.")
    write_message("Least used terms---Most important terms---Least important terms")
    i = 0
    while i < maxID:
        terms_docs=run_sql("SELECT term, hitlist FROM %s WHERE id>= %s and id < %s" % (table, i, i + 10000))
        for (t, hitlist) in terms_docs:
            term_docs=deserialize_via_marshal(hitlist)
            terms[len(term_docs)] = terms.get(len(term_docs), 0) + 1
            if "Gi" in term_docs:
                Gi[t] = term_docs["Gi"]
        i=i + 10000
    terms=terms.items()
    terms.sort(lambda x, y: cmp(y[1], x[1]))
    Gi=Gi.items()
    Gi.sort(lambda x, y: cmp(y[1], x[1]))
    for i in range(0, 20):
        write_message("%s/%s---%s---%s" % (terms[i][0],terms[i][1], Gi[i][0],Gi[len(Gi) - i - 1][0]))

def update_rnkWORD(table, terms):
    """Updates rnkWORDF and rnkWORDR with Gi and Nj values. For each term in rnkWORDF, a Gi value for the term is added. And for each term in each document, the Nj value for that document is added. In rnkWORDR, the Gi value for each term in each document is added. For description on how things are computed, look in the hacking docs.
    table - name of forward index to update
    terms - modified terms"""
    from invenio.config import CFG_SITE_URL

    zero_division_msg = """\
ERROR: %s captured. This might be caused by not enough balanced indexes.
Please, schedule a regular, e.g. weekly, rebalancing of the word similarity
ranking indexes, by using e.g.
"bibrank -f50000 -R -wwrd -s14d -LSunday"
as recommended in %s/help/admin/howto-run"""

    stime = time.time()
    Gi = {}
    Nj = {}
    N = run_sql("select count(id_bibrec) from %sR" % table[:-1])[0][0]

    if len(terms) == 0 and task_get_option("quick") == "yes":
        write_message("No terms to process, ending...")
        return ""
    elif task_get_option("quick") == "yes": #not used -R option, fast calculation (not accurate)
        write_message("Beginning post-processing of %s terms" % len(terms))

        #Locating all documents related to the modified/new/deleted terms, if fast update,
        #only take into account new/modified occurences
        write_message("Phase 1: Finding records containing modified terms")
        terms = terms.keys()
        i = 0

        while i < len(terms):
            terms_docs = get_from_forward_index(terms, i, (i+5000), table)
            for (t, hitlist) in terms_docs:
                term_docs = deserialize_via_marshal(hitlist)
                if "Gi" in term_docs:
                    del term_docs["Gi"]
                for (j, tf) in iteritems(term_docs):
                    if (task_get_option("quick") == "yes" and tf[1] == 0) or task_get_option("quick") == "no":
                        Nj[j] = 0
            write_message("Phase 1: ......processed %s/%s terms" % ((i+5000>len(terms) and len(terms) or (i+5000)), len(terms)))
            i += 5000
        write_message("Phase 1: Finished finding records containing modified terms")

        #Find all terms in the records found in last phase
        write_message("Phase 2: Finding all terms in affected records")
        records = Nj.keys()
        i = 0
        while i < len(records):
            docs_terms = get_from_reverse_index(records, i, (i + 5000), table)
            for (j, termlist) in docs_terms:
                doc_terms = deserialize_via_marshal(termlist)
                for (t, tf) in iteritems(doc_terms):
                    Gi[t] = 0
            write_message("Phase 2: ......processed %s/%s records " % ((i+5000>len(records) and len(records) or (i+5000)), len(records)))
            i += 5000
        write_message("Phase 2: Finished finding all terms in affected records")

    else: #recalculate
        max_id = run_sql("SELECT MAX(id) FROM %s" % table)
        max_id = max_id[0][0]
        write_message("Beginning recalculation of %s terms" % max_id)

        terms = []
        i = 0
        while i < max_id:
            terms_docs = get_from_forward_index_with_id(i, (i+5000), table)
            for (t, hitlist) in terms_docs:
                Gi[t] = 0
                term_docs = deserialize_via_marshal(hitlist)
                if "Gi" in term_docs:
                    del term_docs["Gi"]
                for (j, tf) in iteritems(term_docs):
                    Nj[j] = 0
            write_message("Phase 1: ......processed %s/%s terms" % ((i+5000)>max_id and max_id or (i+5000), max_id))
            i += 5000

        write_message("Phase 1: Finished finding which records contains which terms")
        write_message("Phase 2: Jumping over..already done in phase 1 because of -R option")

    terms = Gi.keys()
    Gi = {}
    i = 0
    if task_get_option("quick") == "no":
        #Calculating Fi and Gi value for each term
        write_message("Phase 3: Calculating importance of all affected terms")
        while i < len(terms):
            terms_docs = get_from_forward_index(terms, i, (i+5000), table)
            for (t, hitlist) in terms_docs:
                term_docs = deserialize_via_marshal(hitlist)
                if "Gi" in term_docs:
                    del term_docs["Gi"]
                Fi = 0
                Gi[t] = 1
                for (j, tf) in iteritems(term_docs):
                    Fi += tf[0]
                for (j, tf) in iteritems(term_docs):
                    if tf[0] != Fi:
                        Gi[t] = Gi[t] + ((float(tf[0]) / Fi) * math.log(float(tf[0]) / Fi) / math.log(2)) / math.log(N)
            write_message("Phase 3: ......processed %s/%s terms" % ((i+5000>len(terms) and len(terms) or (i+5000)), len(terms)))
            i += 5000
        write_message("Phase 3: Finished calculating importance of all affected terms")
    else:
        #Using existing Gi value instead of calculating a new one. Missing some accurancy.
        write_message("Phase 3: Getting approximate importance of all affected terms")
        while i < len(terms):
            terms_docs = get_from_forward_index(terms, i, (i+5000), table)
            for (t, hitlist) in terms_docs:
                term_docs = deserialize_via_marshal(hitlist)
                if "Gi" in term_docs:
                    Gi[t] = term_docs["Gi"][1]
                elif len(term_docs) == 1:
                    Gi[t] = 1
                else:
                    Fi = 0
                    Gi[t] = 1
                    for (j, tf) in iteritems(term_docs):
                        Fi += tf[0]
                    for (j, tf) in iteritems(term_docs):
                        if tf[0] != Fi:
                            Gi[t] = Gi[t] + ((float(tf[0]) / Fi) * math.log(float(tf[0]) / Fi) / math.log(2)) / math.log(N)
            write_message("Phase 3: ......processed %s/%s terms" % ((i+5000>len(terms) and len(terms) or (i+5000)), len(terms)))
            i += 5000
        write_message("Phase 3: Finished getting approximate importance of all affected terms")

    write_message("Phase 4: Calculating normalization value for all affected records and updating %sR" % table[:-1])
    records = Nj.keys()
    i = 0
    while i < len(records):
        #Calculating the normalization value for each document, and adding the Gi value to each term in each document.
        docs_terms = get_from_reverse_index(records, i, (i + 5000), table)
        for (j, termlist) in docs_terms:
            doc_terms = deserialize_via_marshal(termlist)
            try:
                for (t, tf) in iteritems(doc_terms):
                    if t in Gi:
                        Nj[j] = Nj.get(j, 0) + math.pow(Gi[t] * (1 + math.log(tf[0])), 2)
                        Git = int(math.floor(Gi[t]*100))
                        if Git >= 0:
                            Git += 1
                        doc_terms[t] = (tf[0], Git)
                    else:
                        Nj[j] = Nj.get(j, 0) + math.pow(tf[1] * (1 + math.log(tf[0])), 2)
                Nj[j] = 1.0 / math.sqrt(Nj[j])
                Nj[j] = int(Nj[j] * 100)
                if Nj[j] >= 0:
                    Nj[j] += 1
                run_sql("UPDATE %sR SET termlist=%%s WHERE id_bibrec=%%s" % table[:-1],
                        (serialize_via_marshal(doc_terms), j))
            except (ZeroDivisionError, OverflowError) as e:
                ## This is to try to isolate division by zero errors.
                write_message(zero_division_msg % (e, CFG_SITE_URL), stream=sys.stderr)
                register_exception(prefix=zero_division_msg % (e, CFG_SITE_URL), alert_admin=True)
        write_message("Phase 4: ......processed %s/%s records" % ((i+5000>len(records) and len(records) or (i+5000)), len(records)))
        i += 5000
    write_message("Phase 4: Finished calculating normalization value for all affected records and updating %sR" % table[:-1])
    write_message("Phase 5: Updating %s with new normalization values" % table)
    i = 0
    terms = Gi.keys()
    while i < len(terms):
        #Adding the Gi value to each term, and adding the normalization value to each term in each document.
        terms_docs = get_from_forward_index(terms, i, (i+5000), table)
        for (t, hitlist) in terms_docs:
            try:
                term_docs = deserialize_via_marshal(hitlist)
                if "Gi" in term_docs:
                    del term_docs["Gi"]
                for (j, tf) in iteritems(term_docs):
                    if j in Nj:
                        term_docs[j] = (tf[0], Nj[j])
                Git = int(math.floor(Gi[t]*100))
                if Git >= 0:
                    Git += 1
                term_docs["Gi"] = (0, Git)
                run_sql("UPDATE %s SET hitlist=%%s WHERE term=%%s" % table,
                        (serialize_via_marshal(term_docs), t))
            except (ZeroDivisionError, OverflowError) as e:
                write_message(zero_division_msg % (e, CFG_SITE_URL), stream=sys.stderr)
                register_exception(prefix=zero_division_msg % (e, CFG_SITE_URL), alert_admin=True)
        write_message("Phase 5: ......processed %s/%s terms" % ((i+5000>len(terms) and len(terms) or (i+5000)), len(terms)))
        i += 5000
    write_message("Phase 5:  Finished updating %s with new normalization values" % table)
    write_message("Time used for post-processing: %.1fmin" % ((time.time() - stime) / 60))
    write_message("Finished post-processing")


def get_from_forward_index(terms, start, stop, table):
    terms_docs = ()
    for j in range(start, (stop < len(terms) and stop or len(terms))):
        terms_docs += run_sql("SELECT term, hitlist FROM %s WHERE term=%%s" % table,
                              (terms[j],))
    return terms_docs

def get_from_forward_index_with_id(start, stop, table):
    terms_docs = run_sql("SELECT term, hitlist FROM %s WHERE id BETWEEN %s AND %s" % (table, start, stop))
    return terms_docs

def get_from_reverse_index(records, start, stop, table):
    current_recs = "%s" % records[start:stop]
    current_recs = current_recs[1:-1]
    docs_terms = run_sql("SELECT id_bibrec, termlist FROM %sR WHERE id_bibrec IN (%s)" % (table[:-1], current_recs))
    return docs_terms

#def test_word_separators(phrase="hep-th/0101001"):
    #"""Tests word separating policy on various input."""
    #print "%s:" % phrase
    #gwfp = get_words_from_phrase(phrase)
    #for (word, count) in iteritems(gwfp):
        #print "\t-> %s - %s" % (word, count)

def getName(methname, ln=None, type='ln'):
    """Returns the name of the rank method, either in default language or given language.
    methname = short name of the method
    ln - the language to get the name in
    type - which name "type" to get."""
    from invenio.config import CFG_SITE_LANG
    if ln is None:
        ln = CFG_SITE_LANG
    try:
        rnkid = run_sql("SELECT id FROM rnkMETHOD where name='%s'" % methname)
        if rnkid:
            rnkid = str(rnkid[0][0])
            res = run_sql("SELECT value FROM rnkMETHODNAME where type='%s' and ln='%s' and id_rnkMETHOD=%s" % (type, ln, rnkid))
            if not res:
                res = run_sql("SELECT value FROM rnkMETHODNAME WHERE ln='%s' and id_rnkMETHOD=%s and type='%s'"  % (CFG_SITE_LANG, rnkid, type))
            if not res:
                return methname
            return res[0][0]
        else:
            raise Exception
    except Exception as e:
        write_message("Cannot run rank method, either given code for method is wrong, or it has not been added using the webinterface.")
        raise Exception

def word_similarity(run):
    """Call correct method"""
    return word_index(run)
