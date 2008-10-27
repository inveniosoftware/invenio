# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""
Various utilities for WebJournal, e.g. config parser, etc.
"""

import time
import datetime
import re
import os
import cPickle
import urllib
from MySQLdb import OperationalError
from xml.dom import minidom

from invenio.config import \
     CFG_ETCDIR, \
     CFG_SITE_URL, \
     CFG_CACHEDIR, \
     CFG_SITE_LANG, \
     CFG_ACCESS_CONTROL_LEVEL_SITE
from invenio.dbquery import run_sql
from invenio.bibformat_engine import BibFormatObject
from invenio.search_engine import search_pattern

########################### REGULAR EXPRESSIONS ###############################

header_pattern = re.compile('<p\s*(align=justify)??>\s*<strong>(?P<header>.*?)</strong>\s*</p>')
para_pattern = re.compile('<p.*?>(?P<paragraph>.+?)</p>', re.DOTALL)
image_pattern = re.compile(r'''
                               (<a\s*href=["']?(?P<hyperlink>\S*)["']?>)?# get the link location for the image
                               \s*# after each tag we can have arbitrary whitespaces
                               <center># the image is always centered
                               \s*
                               <img\s*(class=["']imageScale["'])*?\s*src=(?P<image>\S*)\s*border=1\s*(/)?># getting the image itself
                               \s*
                               </center>
                               \s*
                               (</a>)?
                               (<br />|<br />|<br/>)*# the caption can be separated by any nr of line breaks
                               (
                               <b>
                               \s*
                               <i>
                               \s*
                               <center>(?P<caption>.*?)</center># getting the caption
                               \s*
                               </i>
                               \s*
                               </b>
                               )?''',  re.DOTALL | re.VERBOSE | re.IGNORECASE )
                               #''',re.DOTALL | re.IGNORECASE | re.VERBOSE | re.MULTILINE)



############################ MAPPING FUNCTIONS ################################

def get_featured_records(journal_name):
    """
    Returns the 'featured' records i.e. records chosen to be displayed
    with an image on the main page, in the widgets section, for the
    given journal.

    parameter:

       journal_name - (str) the name of the journal for which we want
                      to get the featured records

    returns:
       list of tuples (recid, img_url)
    """
    try:
        feature_file = open('%s/webjournal/%s/featured_record' % \
                            (CFG_ETCDIR, journal_name))
    except:
        return []
    records = feature_file.readlines()
    return [(record.split('---', 1)[0], record.split('---', 1)[1]) \
            for record in records if "---" in record]

def add_featured_record(journal_name, recid, img_url):
    """
    Adds the given record to the list of featured records of the given
    journal.

    parameters:

       journal_name - (str) the name of the journal to which the record
                      should be added.

       recid        - (int) the record id of the record to be featured.

       img_url      - (str) a url to an image icon displayed along the
                      featured record.
    returns:
         0 if everything went ok
         1 if record is already in the list
         2 if other problems
    """
    # Check that record is not already there
    featured_records = get_featured_records(journal_name)
    for featured_recid, featured_img in featured_records:
        if featured_recid == str(recid):
            return 1

    try:
        fptr = open('%s/webjournal/%s/featured_record'
                    % (CFG_ETCDIR, journal_name), "a")
        fptr.write(str(recid) + '---' + img_url + '\n')
        fptr.close()
    except:
        return 2
    return 0

def remove_featured_record(journal_name, recid):
    """
    Removes the given record from the list of featured records of the
    given journal.

    parameters:

       journal_name - (str) the name of the journal to which the record
                      should be added.

       recid        - (int) the record id of the record to be featured.
    """
    featured_records = get_featured_records(journal_name)
    try:
        fptr = open('%s/webjournal/%s/featured_record'
                    % (CFG_ETCDIR, journal_name), "w")
        for featured_recid, featured_img in featured_records:
            if str(featured_recid) != str(recid):
                fptr.write(str(featured_recid) + '---' + featured_img + \
                           '\n')
        fptr.close()
    except:
        return 1
    return 0

def get_order_dict_from_recid_list(recids, issue_number):
    """
    Returns the ordered list of input recids, for given
    'issue_number'.

    Since there might be several articles at the same position, the
    returned structure is a dictionary with keys being order number
    indicated in record metadata, and values being list of recids for
    this order number (recids for one position are ordered from
    highest to lowest recid).
            Eg: {'1': [2390, 2386, 2385],
                 '3': [2388],
                 '2': [2389],
                 '4': [2387]}

    parameters:
        recids:   a list of all recid's that should be brought into order
        issue_number:   the issue_number for which we are deriving the order
                        (this has to be one number)

    returns:
            ordered_records: a dictionary with the recids ordered by keys

    """
    ordered_records = {}
    records_without_defined_order = []
    for record in recids:
        temp_rec = BibFormatObject(record)
        articles_info = temp_rec.fields('773__')
        for article_info in articles_info:
            if article_info.get('n', '') == issue_number:
                if article_info.has_key('c'):
                    order_number = article_info.get('c', '')
                    if ordered_records.has_key(order_number):
                        ordered_records[order_number].append(record)
                    else:
                        ordered_records[order_number] = [record]
                else:
                    # No order? No problem! Append it at the end.
                    records_without_defined_order.append(record)

    for record in records_without_defined_order:
        ordered_records[max(ordered_records.keys()) + 1] = record

    for (order, records) in ordered_records.iteritems():
        # Reverse so that if there are several articles at same
        # positon, newest appear first
        records.reverse()

    return ordered_records

def get_records_in_same_issue_in_order(recid):
    """
    TODO: Remove?
    """
    raise ("Not implemented yet.")

def get_rule_string_from_rule_list(rule_list, category):
    """
    """
    i = 0
    current_category_in_list = 0
    for rule_string in rule_list:
        category_from_config = rule_string.split(",")[0]
        if category_from_config.lower() == category.lower():
            current_category_in_list = i
        i += 1
    try:
        rule_string = rule_list[current_category_in_list]
    except:
        rule_string = ""
        # todo: exception
    return rule_string

def get_categories_from_rule_list(rule_list):
    """
    Returns the list of categories defined for this configuration
    """
    categories = [rule_string.split(',')[0] \
                  for rule_string in rule_list]

    return categories

def get_category_from_rule_string(rule_string):
    """
    TODO: Remove?
    """
    pass

def get_rule_string_from_category(category):
    """
    TODO: Remove?
    """
    pass

######################## TIME / ISSUE FUNCTIONS ###############################

def get_monday_of_the_week(week_number, year):
    """
    CERN Bulletin specific function that returns a string indicating the
    Monday of each week as: Monday <dd> <Month> <Year>
    """
    timetuple = issue_week_strings_to_times(['%s/%s' % (week_number, year), ])[0]
    return time.strftime("%A %d %B %Y", timetuple)

def get_issue_number_display(issue_number, journal_name, ln=CFG_SITE_LANG):
    """
    Returns the display string for a given issue number.
    """
    journal_id = get_journal_id(journal_name, ln)
    issue_display = run_sql("SELECT issue_display FROM jrnISSUE \
            WHERE issue_number=%s AND id_jrnJOURNAL=%s", (issue_number,
                                                          journal_id))[0][0]
    return issue_display

def get_current_issue_time(journal_name, ln=CFG_SITE_LANG):
    """
    Return the current issue of a journal as a time object.
    """
    current_issue = get_current_issue(ln, journal_name)
    week_number = current_issue.split("/")[0]
    year = current_issue.split("/")[1]
    current_issue_time = issue_week_strings_to_times(['%s/%s' %
                                                      (week_number, year), ])[0]
    return current_issue_time

def get_all_issue_weeks(issue_time, journal_name, ln):
    """
    Function that takes an issue_number, checks the DB for the issue_display
    which can contain the other (update) weeks involved with this issue and
    returns all issues in a list of timetuples (always for Monday of each
    week).
    """
    from invenio.webjournal_config import InvenioWebJournalIssueNotFoundDBError
    journal_id = get_journal_id(journal_name)
    issue_string = issue_times_to_week_strings([issue_time])[0]
    try:
        issue_display = run_sql(
        "SELECT issue_display FROM jrnISSUE WHERE issue_number=%s \
        AND id_jrnJOURNAL=%s",
            (issue_string, journal_id))[0][0]
    except:
        raise InvenioWebJournalIssueNotFoundDBError(ln, journal_name,
                                                    issue_string)
    issue_bounds = issue_display.split("/")[0].split("-")
    year = issue_display.split("/")[1]
    all_issue_weeks = []
    if len(issue_bounds) == 2:
        # is the year changing? -> "52-02/2008"
        if int(issue_bounds[0]) > int(issue_bounds[1]):
            # get everything from the old year
            old_year_issues = []
            low_bound_time = issue_week_strings_to_times(['%s/%s' %
                                                          (issue_bounds[0],
                                                           str(int(year)-1)), ])[0]
            # if the year changes over the week we always take the higher year
            low_bound_date = datetime.date(int(time.strftime("%Y", low_bound_time)),
                                            int(time.strftime("%m", low_bound_time)),
                                            int(time.strftime("%d", low_bound_time)))
            week_counter = datetime.timedelta(weeks=1)
            date = low_bound_date
            # count up the weeks until you get to the new year
            while date.year != int(year):
                old_year_issues.append(date.timetuple())
                #format = time.strftime("%W/%Y", date.timetuple())
                date = date + week_counter
            # get everything from the new year
            new_year_issues = []
            for i in range(1, int(issue_bounds[1])+1):
                to_append = issue_week_strings_to_times(['%s/%s' % (i, year)])[0]
                new_year_issues.append(to_append)
            all_issue_weeks += old_year_issues
            all_issue_weeks += new_year_issues
        else:
            for i in range(int(issue_bounds[0]), int(issue_bounds[1])+1):
                to_append = issue_week_strings_to_times(['%s/%s' % (i, year)])[0]
                all_issue_weeks.append(to_append)
    elif len(issue_bounds) == 1:
        to_append = issue_week_strings_to_times(['%s/%s' %
                                                 (issue_bounds[0], year)])[0]
        all_issue_weeks.append(to_append)
    else:
        return False

    return all_issue_weeks

def count_down_to_monday(current_time):
    """
    Takes a timetuple and counts it down to the next monday and returns
    this time.
    """
    next_monday = datetime.date(int(time.strftime("%Y", current_time)),
                        int(time.strftime("%m", current_time)),
                        int(time.strftime("%d", current_time)))
    counter = datetime.timedelta(days=-1)
    while next_monday.weekday() != 0:
        next_monday = next_monday + counter
    return next_monday.timetuple()

def get_next_journal_issues(current_issue_time, journal_name,
                            ln=CFG_SITE_LANG, number=2):
    """
    Returns the <number> next issue numbers from the current_issue_time.
    """
    #now = '%s-%s-%s 00:00:00' % (int(time.strftime("%Y", current_issue_time)),
    #                                     int(time.strftime("%m", current_issue_time)),
    #                                     int(time.strftime("%d", current_issue_time)))
    #
    now = datetime.date(int(time.strftime("%Y", current_issue_time)),
                        int(time.strftime("%m", current_issue_time)),
                        int(time.strftime("%d", current_issue_time)))
    week_counter = datetime.timedelta(weeks=1)
    date = now
    next_issues = []
    for i in range(1, number+1):
        date = date + week_counter
        #date = run_sql("SELECT %s + INTERVAL 1 WEEK", (date,))[0][0]
        #date_formated = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        #raise '%s  %s' % (repr(now), repr(date_formated))
        next_issues.append(date.timetuple())
        #next_issues.append(date_formated)
    return next_issues

def issue_times_to_week_strings(issue_times, ln=CFG_SITE_LANG):
    """
    Function that approaches a correct python time to MySQL time week string
    conversion by looking up and down the time horizon and always rechecking
    the python time with the mysql result until a week string match is found.
    """
    issue_strings = []
    for issue in issue_times:
        # do the initial pythonic week view
        week = time.strftime("%W/%Y", issue)
        week += " Monday"
        limit = 5
        counter = 0
        success = False
        # try going up 5
        while success == False and counter <= limit:
            counter += 1
            success = get_consistent_issue_week(issue, week)
            if success == False:
                week = count_week_string_up(week)
            else:
                break
        # try going down 5
        counter = 0
        while success == False and counter <= limit:
            counter += 1
            success = get_consistent_issue_week(issue, week)
            if success == False:
                week = count_week_string_down(week)
            else:
                break

        from invenio.webjournal_config import InvenioWebJournalReleaseDBError
        if success == False:
            raise InvenioWebJournalReleaseDBError(ln)

        #check_for_time = run_sql("SELECT STR_TO_DATE(%s, %s)",
        #                     (week, conversion_rule))[0][0]
        #while (issue != check_for_time.timetuple()):
        #    week = str(int(week.split("/")[0]) + 1) + "/" + week.split("/")[1]
        #    if week[1] == "/":
        #        week = "0" + week
        #    #raise repr(week)
        #    check_for_time = run_sql("SELECT STR_TO_DATE(%s, %s)",
        #                     (week, conversion_rule))[0][0]
        issue_strings.append(week.split(" ")[0])
    return issue_strings

def count_week_string_up(week):
    """
    Function that takes a week string representation and counts it up by one.
    """
    week_nr = week.split("/")[0]
    year = week.split("/")[1]
    if week_nr == "53":
        week_nr = "01"
        year = str(int(year) + 1)
    else:
        week_nr = str(int(week_nr) + 1)
        if len(week_nr) == 1:
            week_nr = "0" + week_nr
    return "%s/%s" % (week_nr, year)

def count_week_string_down(week):
    """
    Function that takes a week string representation and counts it down by one.
    """
    week_nr = week.split("/")[0]
    year = week.split("/")[1]
    if week_nr == "01":
        week_nr = "53"
        year = str(int(year)-1)
    else:
        week_nr = str(int(week_nr)-1)
        if len(week_nr) == 1:
            week_nr = "0" + week_nr
    return "%s/%s" % (week_nr, year)

def get_consistent_issue_week(issue_time, issue_week):
    """
    This is the central consistency function between our Python and MySQL dates.
    We use mysql times because of a bug in Scientific Linux that does not allow
    us to reconvert a week number to a timetuple.
    The function takes a week string, e.g. "02/2008" and its according timetuple
    from our functions. Then it retrieves the mysql timetuple for this week and
    compares the two times. If they are equal our times are consistent, if not,
    we return False and some function should try to approach a consisten result
    (see example in issue_times_to_week_strings()).
    """
    conversion_rule = '%v/%x %W'
    mysql_repr = run_sql("SELECT STR_TO_DATE(%s, %s)",
                             (issue_week, conversion_rule))[0][0]
    if mysql_repr.timetuple() == issue_time:
        return issue_week
    else:
        return False

def issue_week_strings_to_times(issue_weeks, ln=CFG_SITE_LANG):
    """
    Converts a list of issue week strings (WW/YYYY) to python time objects.
    """
    issue_times = []
    for issue in issue_weeks:
        week_number = issue.split("/")[0]
        year = issue.split("/")[1]
        to_convert = '%s/%s Monday' % (year, week_number)
        conversion_rule = '%x/%v %W'
        result = run_sql("SELECT STR_TO_DATE(%s, %s)",
                         (to_convert, conversion_rule))[0][0]
        issue_times.append(result.timetuple())
    return issue_times

def sort_by_week_number(x, y):
    """
    Sorts a list of week numbers.
    """
    year_x = x.split("/")[1]
    year_y = y.split("/")[1]
    if cmp(year_x, year_y) != 0:
        return cmp(year_x, year_y)
    else:
        week_x = x.split("/")[0]
        week_y = y.split("/")[0]
        return cmp(week_x, week_y)

def get_number_of_articles_for_issue(issue, journal_name, ln=CFG_SITE_LANG):
    """
    Function that returns a dictionary with all categories and number of
    articles in each category.
    """
    config_strings = get_xml_from_config(["rule"], journal_name)
    rule_list = config_strings["rule"]
    all_articles = {}
    for rule in rule_list:
        category_name = rule.split(",")[0]
        if issue[0] == "0" and len(issue) == 7:
            week_nr = issue.split("/")[0]
            year = issue.split("/")[1]
            issue_nr_alternative = "%s/%s" % (week_nr[1], year)

            all_records_of_a_type = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                      (category_name, issue)))
            all_records_of_a_type += list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                      (category_name, issue_nr_alternative)))
        else:
            all_records_of_a_type = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                      (category_name, issue)))
        all_articles[category_name] = len(all_records_of_a_type)
    return all_articles

def get_list_of_issues_for_publication(publication):
    """
    Takes a publication string, e.g. 23-24/2008 and splits it down to a list
    of single issues.
    """
    year = publication.split("/")[1]
    issues_string = publication.split("/")[0]
    bounds = issues_string.split("-")
    issues = []
    if len(bounds) == 2:
        low_bound = issues_string.split("-")[0]
        high_bound = issues_string.split("-")[1]
        if int(low_bound) < int(high_bound):
            for i in range(int(low_bound), int(high_bound)+1):
                issue_nr = str(i)
                if len(issue_nr) == 1:
                    issue_nr = "0" + issue_nr
                issues.append("%s/%s" % (issue_nr, year))
        else:
            for i in range(int(low_bound), 53+1):
                issue_nr = str(i)
                if len(issue_nr) == 1:
                    issue_nr = "0" + issue_nr
                issues.append("%s/%s" % (issue_nr, str(int(year)-1)))
            for i in range(1, int(high_bound) + 1):
                issue_nr = str(i)
                if len(issue_nr) == 1:
                    issue_nr = "0" + issue_nr
                issues.append("%s/%s" % (issue_nr, year))
    else:
        issues.append("%s/%s" % (bounds[0], year))
    return issues

def get_release_time(issue, journal_name, ln=CFG_SITE_LANG):
    """
    Gets the date at which an issue was released from the DB.
    Returns False if issue has not yet been released.
    """
    journal_id = get_journal_id(journal_name, ln)
    try:
        release_date = run_sql("SELECT date_released FROM jrnISSUE \
                           WHERE issue_number=%s AND id_jrnJOURNAL=%s",
                            (issue, journal_id))[0][0]
    except:
        return False
    if release_date == None:
        return False
    else:
        return release_date.timetuple()

def get_announcement_time(issue, journal_name, ln=CFG_SITE_LANG):
    """
    Get the date at which an issue was announced through the alert system.
    """
    journal_id = get_journal_id(journal_name, ln)
    try:
        announce_date = run_sql("SELECT date_announced FROM jrnISSUE \
                           WHERE issue_number=%s AND id_jrnJOURNAL=%s",
                            (issue, journal_id))[0][0]
    except:
        return False
    if announce_date == None:
        return False
    else:
        return announce_date.timetuple()

######################## GET DEFAULTS FUNCTIONS ###############################

def get_journal_info_path(journal_name):
    """
    Returns the path to the info file of the given journal. The info
    file should be used to get information about a journal when database
    is not available.

    Returns None if path cannot be determined
    """
    # We must make sure we don't try to read outside of webjournal
    # cache dir
    info_path = os.path.realpath("%s/webjournal/%s/info.dat"% \
                                 (CFG_CACHEDIR, journal_name))
    if info_path.startswith(CFG_CACHEDIR + '/webjournal/'):
        return info_path
    else:
        return None

def get_journal_id(journal_name, ln=CFG_SITE_LANG):
    """
    Get the id for this journal from the DB. If DB is down, try to get
    from cache.
    """
    journal_id = None
    from invenio.webjournal_config import InvenioWebJournalJournalIdNotFoundDBError

    if CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
        # do not connect to the database as the site is closed for
        # maintenance:
        journal_info_path = get_journal_info_path(journal_name)
        try:
            journal_info_file = open(journal_info_path, 'r')
            journal_info = cPickle.load(journal_info_file)
            journal_id = journal_info.get('journal_id', None)
        except cPickle.PickleError, e:
            journal_id = None
        except IOError:
            journal_id = None
    else:
        try:
            res = run_sql("SELECT id FROM jrnJOURNAL WHERE name=%s",
                          (journal_name,))
            if len(res) > 0:
                journal_id = res[0][0]
        except OperationalError, e:
            # Cannot connect to database. Try to read from cache
            journal_info_path = get_journal_info_path(journal_name)
            try:
                journal_info_file = open(journal_info_path, 'r')
                journal_info = cPickle.load(journal_info_file)
                journal_id = journal_info['journal_id']
            except cPickle.PickleError, e:
                journal_id = None
            except IOError:
                journal_id = None

    if journal_id is None:
        raise InvenioWebJournalJournalIdNotFoundDBError(ln, journal_name)

    return journal_id

def guess_journal_name(ln):
    """
    tries to take a guess what a user was looking for on the server if not
    providing a name for the journal.
    if there is only one journal on the server, returns the name of which,
    otherwise redirects to a list with possible journals.
    """
    from invenio.webjournal_config import InvenioWebJournalNoJournalOnServerError
    from invenio.webjournal_config import InvenioWebJournalNoNameError

    journals_id_and_names = get_journals_ids_and_names()
    if len(journals_id_and_names) == 0:
        raise InvenioWebJournalNoJournalOnServerError(ln)
    elif len(journals_id_and_names) > 0 and \
             journals_id_and_names[0].has_key('journal_name'):
        return journals_id_and_names[0]['journal_name']
    else:
        raise InvenioWebJournalNoNameError(ln)

##     all_journals = run_sql("SELECT * FROM jrnJOURNAL ORDER BY id")
##     if len(all_journals) == 0:
##         # try to get from file, in case DB is down
##         raise InvenioWebJournalNoJournalOnServerError(ln)
##     elif len(all_journals) > 0:
##         return all_journals[0][1]
##     else:
##         raise InvenioWebJournalNoNameError(ln)

def get_journals_ids_and_names():
    """
    Returns the list of existing journals IDs and names. Try to read
    from the DB, or from cache if DB is not accessible.
    """
    journals = []

    if CFG_ACCESS_CONTROL_LEVEL_SITE == 2:
        # do not connect to the database as the site is closed for
        # maintenance:
        files = os.listdir("%s/webjournal" % CFG_CACHEDIR)
        info_files = [path + os.sep + 'info.dat' for path in files if \
                      os.path.isdir(path) and \
                      os.path.exists(path + os.sep + 'info.dat')]
        for info_file in info_files:
            try:
                journal_info_file = open(info_file, 'r')
                journal_info = cPickle.load(journal_info_file)
                journal_id = journal_info.get('journal_id', None)
                journal_name = journal_info.get('journal_name', None)
                current_issue = journal_info.get('current_issue', None)
                if journal_id is not None and \
                       journal_name is not None:
                    journals.append({'journal_id': journal_id,
                                     'journal_name': journal_name,
                                     'current_issue': current_issue})
            except cPickle.PickleError, e:
                # Well, can't do anything...
                continue
            except IOError:
                # Well, can't do anything...
                continue
    else:
        try:
            res = run_sql("SELECT id, name FROM jrnJOURNAL ORDER BY id")
            for journal_id, journal_name in res:
                journals.append({'journal_id': journal_id,
                                 'journal_name': journal_name})
        except OperationalError, e:
            # Cannot connect to database. Try to read from cache
            files = os.listdir("%s/webjournal" % CFG_CACHEDIR)
            info_files = [path + os.sep + 'info.dat' for path in files if \
                          os.path.isdir(path) and \
                          os.path.exists(path + os.sep + 'info.dat')]
            for info_file in info_files:
                try:
                    journal_info_file = open(info_file, 'r')
                    journal_info = cPickle.load(journal_info_file)
                    journal_id = journal_info.get('journal_id', None)
                    journal_name = journal_info.get('journal_name', None)
                    current_issue = journal_info.get('current_issue', None)
                    if journal_id is not None and \
                           journal_name is not None:
                        journals.append({'journal_id': journal_id,
                                         'journal_name': journal_name,
                                         'current_issue': current_issue})
                except cPickle.PickleError, e:
                    # Well, can't do anything...
                    continue
                except IOError:
                    # Well, can't do anything...
                    continue

    return journals

def get_current_issue(ln, journal_name):
    """
    Returns the current issue of a journal as a string.
    """
    journal_id = get_journal_id(journal_name, ln)
    try:
        current_issue = run_sql("SELECT issue_number FROM jrnISSUE \
                WHERE date_released <= NOW() AND id_jrnJOURNAL=%s \
                ORDER BY date_released DESC LIMIT 1", (journal_id,))[0][0]
    except:
        # start the first journal ever with the day of today
        current_issue = time.strftime("%W/%Y", time.localtime())
        run_sql("INSERT INTO jrnISSUE \
                (id_jrnJOURNAL, issue_number, issue_display) \
                VALUES(%s, %s, %s)", (journal_id,
                                      current_issue,
                                      current_issue))
    return current_issue

def get_current_publication(journal_name, current_issue, ln=CFG_SITE_LANG):
    """
    Returns the current publication string (current issue + updates).
    """
    journal_id = get_journal_id(journal_name, ln)
    current_publication =  run_sql("SELECT issue_display FROM jrnISSUE \
                                   WHERE issue_number=%s AND \
                                    id_jrnJOURNAL=%s",
                                    (current_issue, journal_id))[0][0]
    return current_publication

def get_xml_from_config(xpath_list, journal_name):
    """
    wrapper for minidom.getElementsByTagName()
    Takes a list of string expressions and a journal name and searches the config
    file of this journal for the given xpath queries. Returns a dictionary with
    a key for each query and a list of string (innerXml) results for each key.
    Has a special field "config_fetching_error" that returns an error when
    something has gone wrong.
    """
    # get and open the config file
    results = {}
    config_path = '%s/webjournal/%s/config.xml' % (CFG_ETCDIR, journal_name)
    config_file = minidom.Document
    try:
        config_file = minidom.parse("%s" % config_path)
    except:
        #todo: raise exception "error: no config file found"
        results["config_fetching_error"] = "could not find config file"
        return results
    for xpath in xpath_list:
        result_list = config_file.getElementsByTagName(xpath)
        results[xpath] = []
        for result in result_list:
            try:
                result_string = result.firstChild.toxml(encoding="utf-8")
            except:
                # WARNING, config did not have a value
                continue
            results[xpath].append(result_string)
    return results

def parse_url_string(uri):
    """
    Centralized function to parse any url string given in
    webjournal. Useful to retrieve current category, journal,
    etc. from within format elements

    returns:
        args: all arguments in dict form
    """
    args = {'journal_name'  : '',
            'issue_year'    : '',
            'issue_number'  : '',
            'issue'         : '',
            'category'      : '',
            'recid'         : '',
            'verbose'       : 0,
            'ln'            : CFG_SITE_LANG,
            'archive_year'  : ''}

    # Take everything after journal and before first question mark
    splitted_uri = uri.split('journal', 1)
    second_part = splitted_uri[1]
    splitted_uri = second_part.split('?')
    uri_middle_part = splitted_uri[0]
    uri_arguments = ''
    if len(splitted_uri) > 1:
        uri_arguments = splitted_uri[1]

    arg_list = uri_arguments.split("&")
    args['ln'] = 'en'
    args['verbose'] = 0
    for arg_pair in arg_list:
        arg_and_value = arg_pair.split('=')
        if len(arg_and_value) == 2:
            if arg_and_value[0] == 'ln':
                args['ln'] = arg_and_value[1]
            elif arg_and_value[0] == 'verbose' and \
                     arg_and_value[1].isdigit():
                args['verbose'] = arg_and_value[1]
            elif arg_and_value[0] == 'archive_year':
                args['archive_year'] = arg_and_value[1]
            elif arg_and_value[0] == 'name':
                args['journal_name'] = arg_and_value[1]

    arg_list = uri_middle_part.split("/")
    if len(arg_list) > 1 and arg_list[1] not in ['search', 'contact']:
        args['journal_name'] = urllib.unquote(arg_list[1])
    elif arg_list[1] not in ['search', 'contact']:
        args['journal_name'] = guess_journal_name(args['ln'])
    if len(arg_list) > 2:
        args['issue_year'] = urllib.unquote(arg_list[2])
    else:
        issue = get_current_issue(args['ln'],
                                  args['journal_name'])
        args['issue'] = issue
        args['issue_year'] = issue.split('/')[1]
        args['issue_number'] = issue.split('/')[0]
    if len(arg_list) > 3:
        args['issue_number'] = urllib.unquote(arg_list[3])
        args['issue'] = args['issue_number'] + "/" + args['issue_year']
    if len(arg_list) > 4:
        args['category'] = urllib.unquote(arg_list[4])
    if len(arg_list) > 5:
        args['recid'] = urllib.unquote(arg_list[5])

    # TODO : wash arguments
    return args

def make_journal_url(current_uri, custom_parameters={}):
    """
    Create a url, using the current uri and overriding values
    with the given custom_parameters
    """
    default_params = parse_url_string(current_uri)
    for key, value in custom_parameters.iteritems():
        # Override default params with custom params
        default_params[key] = str(value)

    uri = CFG_SITE_URL + '/journal/'
    if default_params['journal_name']:
        uri += urllib.quote(default_params['journal_name']) + '/'
        if default_params['issue_year']:
            uri += urllib.quote(default_params['issue_year']) + '/'
            if default_params['issue_number']:
                uri += urllib.quote(default_params['issue_number']) + '/'
                if default_params['category']:
                    uri += urllib.quote(default_params['category'])
                    if default_params['recid']:
                        uri += '/' + urllib.quote(str(default_params['recid']))

    printed_question_mark = False
    if default_params['ln']:
        uri += '?ln=' + default_params['ln']
        printed_question_mark = True

    if default_params['verbose'] != 0:
        if printed_question_mark:
            uri += '&amp;verbose=' + str(default_params['verbose'])
        else:
            uri += '?verbose=' + str(default_params['verbose'])

    return uri

############################" CACHING FUNCTIONS ################################

def cache_index_page(html, journal_name, category, issue, ln):
    """
    Caches the index page main area of a Bulletin
    (right hand menu cannot be cached)
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")

    cache_path = os.path.realpath('%s/webjournal/%s/%s_index_%s_%s.html' % \
                                  (CFG_CACHEDIR, journal_name,
                                   issue, category,
                                   ln))
    if not cache_path.startswith(CFG_CACHEDIR + '/webjournal'):
        # Mmh, not accessing correct path. Stop caching
        return False

    cache_path_dir = '%s/webjournal/%s' % (CFG_CACHEDIR, journal_name)
    if not os.path.isdir(cache_path_dir):
        os.makedirs(cache_path_dir)
    cached_file = open(cache_path, "w")
    cached_file.write(html)
    cached_file.close()

def get_index_page_from_cache(journal_name, category, issue, ln):
    """
    Function to get an index page from the cache.
    False if not in cache.
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")

    cache_path = os.path.realpath('%s/webjournal/%s/%s_index_%s_%s.html' % \
                                  (CFG_CACHEDIR, journal_name,
                                   issue, category, ln))
    if not cache_path.startswith(CFG_CACHEDIR + '/webjournal'):
        # Mmh, not accessing correct path. Stop reading cache
        return False

    try:
        cached_file = open(cache_path).read()
    except:
        return False
    return cached_file

def cache_article_page(html, journal_name, category, recid, issue, ln):
    """
    Caches an article view of a journal.
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")
    cache_path = os.path.realpath('%s/webjournal/%s/%s_article_%s_%s_%s.html' % \
                                  (CFG_CACHEDIR, journal_name,
                                   issue, category, recid, ln))
    if not cache_path.startswith(CFG_CACHEDIR + '/webjournal'):
        # Mmh, not accessing correct path. Stop caching
        return
    cache_path_dir = '%s/webjournal/%s' % (CFG_CACHEDIR, journal_name)
    if not os.path.isdir(cache_path_dir):
        os.makedirs(cache_path_dir)
    cached_file = open(cache_path, "w")
    cached_file.write(html)
    cached_file.close()

def get_article_page_from_cache(journal_name, category, recid, issue, ln):
    """
    Gets an article view of a journal from cache.
    False if not in cache.
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")

    cache_path = os.path.realpath('%s/webjournal/%s/%s_article_%s_%s_%s.html' % \
                                  (CFG_CACHEDIR, journal_name,
                                   issue, category, recid, ln))
    if not cache_path.startswith(CFG_CACHEDIR + '/webjournal'):
        # Mmh, not accessing correct path. Stop reading cache
        return False
    try:
        cached_file = open(cache_path).read()
    except:
        return False

    return cached_file

def clear_cache_for_article(journal_name, category, recid, issue):
    """
    Resets the cache for an article (e.g. after an article has been modified)
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")

    cache_path = os.path.realpath('%s/webjournal/%s/%s_article_%s_%s_%s.html' % \
                                  (CFG_CACHEDIR, journal_name))
    if not cache_path.startswith(CFG_CACHEDIR + '/webjournal'):
        # Mmh, not accessing correct path. Stop deleting cache
        return False

    # try to delete the article cached file
    try:
        os.remove('%s/webjournal/%s/%s_article_%s_%s_en.html' %
                  (CFG_CACHEDIR, journal_name, issue, category, recid))
    except:
        pass
    try:
        os.remove('%s/webjournal/%s/%s_article_%s_%s_fr.html' %
                  (CFG_CACHEDIR, journal_name, issue, category, recid))
    except:
        pass
    # delete the index page for the category
    try:
        os.remove('%s/webjournal/%s/%s_index_%s_en.html'
                  % (CFG_CACHEDIR, journal_name, issue, category))
    except:
        pass
    try:
        os.remove('%s/webjournal/%s/%s_index_%s_fr.html'
                  % (CFG_CACHEDIR, journal_name, issue, category))
    except:
        pass
    # delete the entry in the recid_order_map
    # todo: make this per entry
    try:
        os.remove('%s/webjournal/%s/%s_recid_order_map.dat'
                  % (CFG_CACHEDIR, journal_name, issue))
    except:
        pass
    return True

def clear_cache_for_issue(journal_name, issue):
    """
    clears the cache of a whole issue.
    """
    issue = issue.replace("/", "_")
    cache_path_dir = os.path.realpath('%s/webjournal/%s' % \
                                      (CFG_CACHEDIR, journal_name))
    if not cache_path_dir.startswith(CFG_CACHEDIR + '/webjournal'):
        # Mmh, not accessing correct path. Stop deleting cache
        return False

    all_cached_files = os.listdir(cache_path_dir)
    for cached_file in all_cached_files:
        if cached_file[:7] == issue:
            try:
                os.remove(cache_path_dir + '/' + cached_file)
            except:
                return False
    return True

## def cache_recid_data_dict_CERNBulletin(recid, issue, rule, order):
##     """
##     The CERN Bulletin has a specific recid data dict that is cached
##     using cPickle.
##     """
##     issue = issue.replace("/", "_")
##     # get whats in there
##     if not os.path.isdir('%s/webjournal/CERNBulletin' % CFG_CACHEDIR):
##         os.makedirs('%s/webjournal/CERNBulletin' % CFG_CACHEDIR)
##     try:
##         temp_file = open('%s/webjournal/CERNBulletin/%s_recid_order_map.dat'
##                          % (CFG_CACHEDIR, issue))
##     except:
##         temp_file = open('%s/webjournal/CERNBulletin/%s_recid_order_map.dat'
##                          % (CFG_CACHEDIR, issue), "w")
##     try:
##         recid_map = cPickle.load(temp_file)
##     except:
##         recid_map = ""
##     temp_file.close()
##     # add new recid
##     if recid_map == "":
##         recid_map = {}
##     if not recid_map.has_key(rule):
##         recid_map[rule] = {}
##     recid_map[rule][order] = recid
##     # save back
##     temp_file = open('%s/webjournal/CERNBulletin/%s_recid_order_map.dat'
##                      % (CFG_CACHEDIR, issue), "w")
##     cPickle.dump(recid_map, temp_file)
##     temp_file.close()

## def get_cached_recid_data_dict_CERNBulletin(issue, rule):
##     """
##     Function to restore from cache the dict Data Type that the CERN Bulletin
##     uses for mapping between the order of an article and its recid.
##     """
##     issue = issue.replace("/", "_")
##     try:
##         temp_file = open('%s/webjournal/CERNBulletin/%s_recid_order_map.dat'
##                          % (CFG_CACHEDIR, issue))
##     except:
##         return {}
##     try:
##         recid_map = cPickle.load(temp_file)
##     except:
##         return {}
##     try:
##         recid_dict = recid_map[rule]
##     except:
##         recid_dict = {}
##     return recid_dict


######################### CERN SPECIFIC FUNCTIONS #############################

def get_recid_from_legacy_number(issue_number, category, number):
    """
    Returns the recid based on the issue number, category and
    'number'.

    This is used to support URLs using the now deprecated 'number'
    argument.  The function tries to reproduce the behaviour of the
    old way of doing, even keeping some of its 'problems' (so that we
    reach the same article as before with a given number)..

    Returns the recid as int, or -1 if not found
    """
    recids = []
    if issue_number[0] == "0":
        alternative_issue_number = issue_number[1:]
        recids = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                      (category, issue_number)))
        recids.extend(list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                      (category, alternative_issue_number))))
    else:
        recids = list(search_pattern(p='65017:"%s" and 773__n:%s' %
                                      (category, issue_number)))

    # Now must order the records and pick the one at index 'number'.
    # But we have to take into account that there can be multiple
    # records at position 1, and that these additional records should
    # be numbered with negative numbers:
    # 1, 1, 1, 2, 3 -> 1, -1, -2, 2, 3...
    negative_index_records = {}
    positive_index_records = {}
    # Fill in 'negative_index_records' and 'positive_index_records'
    # lists with the following loop
    for recid in recids:
        bfo = BibFormatObject(recid)
        order = [subfield['c'] for subfield in bfo.fields('773__') if \
                 issue_number in subfield['n']]

        if len(order) > 0:
            # If several orders are defined for the same article and
            # the same issue, keep the first one
            order = order[0]
            if order.isdigit():
                # Order must be an int. Otherwise skip
                order = int(order)
                if order == 1 and positive_index_records.has_key(1):
                    # This is then a negative number for this record
                    index = (len(negative_index_records.keys()) > 0 and \
                             min(negative_index_records.keys()) -1) or 0
                    negative_index_records[index] = recid
                else:
                    # Positive number for this record
                    if not positive_index_records.has_key(order):
                        positive_index_records[order] = recid
                    else:
                        # We make the assumption that we cannot have
                        # twice the same position for two
                        # articles. Previous WebJournal module was not
                        # clear about that. Just drop this record
                        # (better than crashing or looping forever..)
                        pass

    recid_to_return = -1
    # Ok, we can finally pick the recid corresponding to 'number'
    if number <= 0:
        negative_indexes = negative_index_records.keys()
        negative_indexes.sort()
        negative_indexes.reverse()
        if len(negative_indexes) > abs(number):
            recid_to_return = negative_index_records[negative_indexes[abs(number)]]
    else:
        #positive_indexes = positive_index_records.keys()
        #positive_indexes.sort()
        #if len(positive_indexes) >= number:
        #    recid_to_return = positive_index_records[positive_indexes[number -1]]
        if positive_index_records.has_key(number):
            recid_to_return = positive_index_records[number]

    return recid_to_return
