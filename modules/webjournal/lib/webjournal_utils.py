# -*- coding: utf-8 -*-
## $Id$
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

from invenio.bibformat_engine import BibFormatObject
from invenio.errorlib import register_exception
from invenio.search_engine import search_pattern
from invenio.config import CFG_ETCDIR, weburl, adminemail, CFG_CACHEDIR, cdslang
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.dbquery import run_sql
from xml.dom import minidom
from urllib2 import urlopen
import time
import datetime
import re
import os
import cPickle


############################ MAPPING FUNCTIONS ################################

def get_order_dict_from_recid_list(list, issue_number):
    """
    this is a centralized function that takes a list of recid's and brings it in
    order using a centralized algorithm. this always has to be in sync with
    the reverse function get_recid_from_order(order)

    parameters:
        list:   a list of all recid's that should be brought into order
        issue_number:   the issue_number for which we are deriving the order
                        (this has to be one number)

    returns:
            ordered_records: a dictionary with the recids ordered by keys
    """
    ordered_records = {}
    for record in list:
        temp_rec = BibFormatObject(record)
        issue_numbers = temp_rec.fields('773__n')
        order_number = temp_rec.fields('773__c')
        # todo: the marc fields have to be set'able by some sort of config interface
        n = 0
        for temp_issue in issue_numbers:
            if temp_issue == issue_number:
                try:
                    order_number = int(order_number[n])
                except:
                    # todo: Warning, record does not support numbering scheme
                    order_number = -1
            n+=1
        if order_number != -1:
            try:
                ordered_records[order_number] = record
            except:
                pass
                # todo: Error, there are two records with the same order_number in the issue
        else:
            ordered_records[max(ordered_records.keys()) + 1] = record

    return ordered_records

def get_records_in_same_issue_in_order(recid):
    """
    """
    raise ("Not implemented yet.")

def get_recid_from_order(order, rule, issue_number):
    """
    takes the order of a record in the journal as passed in the url arguments
    and derives the recid using the current issue number and the record
    rule for this kind of records.

    parameters:
        order:  the order at which the record appears in the journal as passed
                in the url
        rule:   the defining rule of the journal record category
        issue_number:   the issue number for which we are searching

    returns:
        recid:  the recid of the ordered record
    """
    # get the id list
    all_records = list(search_pattern(p="%s and 773__n:%s" %
                                      (rule, issue_number),
                                      f="&action_search=Search"))
    ordered_records = {}
    for record in all_records:
        temp_rec = BibFormatObject(record)
        issue_numbers = temp_rec.fields('773__n')
        order_number = temp_rec.fields('773__c')
        # todo: fields for issue number and order number have to become generic
        n = 0
        for temp_issue in issue_numbers:
            if temp_issue == issue_number:
                try:
                    order_number = int(order_number[n])
                except:
                    # todo: Warning, record does not support numbering scheme
                    order_number = -1
            n+=1

        if order_number != -1:
            try:
                ordered_records[order_number] = record
            except:
                pass
                # todo: Error, there are two records with the same order_number in the issue
        else:
            ordered_records[max(ordered_records.keys()) + 1] = record
    try:
        recid = ordered_records[int(order)]
    except:
        pass
        # todo: ERROR, numbering scheme inconsistency
    return recid

# todo: move to a template
def please_login(req, journal_name, ln="en", title="", message="", backlink=""):
    """
    """
    _ = gettext_set_language(ln)
    if title == "":
        title_out = _("Please login to perform this action.")
    else:
        title_out = title
    if message == "":
        message_out = _("In order to publish webjournal issues you must be logged \
                        in and be authorized for this kind of task. If you have a \
                        login, use the link \
                        below to login.")
    else:
        message_out = message

    if backlink == "":
        backlink_out = "%s/journal/issue_control?name=%s" % (weburl, journal_name)
    else:
        backlink_out = backlink

    title_msg = _("We need you to login")
    body_out = '''<div style="text-align: center;">
                <fieldset style="width:400px; margin-left: auto; margin-right: auto;background: url('%s/img/blue_gradient.gif') top left repeat-x;">
                    <legend style="color:#a70509;background-color:#fff;"><i>%s</i></legend>
                    <p style="text-align:center;">%s</p>
                    <br/>
                    <p><a href="%s/youraccount/login?referer=%s">Login</a></p>
                    <br/>
                    <div style="text-align:right;">Mail<a href="mailto:%s"> the Administrator.</a></div>
                </fieldset>
            </div>
            ''' % (weburl,
                   title_msg,
                   message_out,
                   weburl,
                   backlink_out,
                   adminemail)

    return page(title = title_out,
                body = body_out,
                description = "",
                keywords = "",
                language = ln,
                req = req)

def get_rule_string_from_rule_list(rule_list, category):
    """
    """
    i = 0
    current_category_in_list = 0
    for rule_string in rule_list:
                category_from_config = rule_string.split(",")[0]
                if category_from_config.lower() == category.lower():
                    current_category_in_list = i
                i+=1
    try:
        rule_string = rule_list[current_category_in_list]
    except:
        rule_string = ""
        # todo: exception
    return rule_string

def get_category_from_rule_string(rule_string):
    """
    """
    pass

def get_rule_string_from_category(category):
    """
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

def get_issue_number_display(issue_number, journal_name, language=cdslang):
    """
    Returns the display string for a given issue number.
    """
    journal_id = get_journal_id(journal_name, language)
    issue_display = run_sql("SELECT issue_display FROM jrnISSUE \
            WHERE issue_number=%s AND id_jrnJOURNAL=%s", (issue_number,
                                                          journal_id))[0][0]
    return issue_display

def get_current_issue_time(journal_name, language=cdslang):
    """
    Return the current issue of a journal as a time object.
    """
    current_issue = get_current_issue(language, journal_name)
    week_number = current_issue.split("/")[0]
    year = current_issue.split("/")[1]
    current_issue_time = issue_week_strings_to_times(['%s/%s' %
                                                      (week_number, year), ])[0]
    return current_issue_time

def get_all_issue_weeks(issue_time, journal_name, language):
    """
    Function that takes an issue_number, checks the DB for the issue_display
    which can contain the other (update) weeks involved with this issue and
    returns all issues in a list of timetuples (always for Monday of each
    week).
    """
    from invenio.webjournal_config import InvenioWebJournalIssueNotFoundDBError
    journal_id = get_journal_id(journal_name)
    issue_string = issue_times_to_week_strings([issue_time,])[0]
    try:
        issue_display = run_sql(
        "SELECT issue_display FROM jrnISSUE WHERE issue_number=%s \
        AND id_jrnJOURNAL=%s",
            (issue_string, journal_id))[0][0]
    except:
        raise InvenioWebJournalIssueNotFoundDBError(language, journal_name,
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
                to_append = issue_week_strings_to_times(['%s/%s' % (i, year),])[0]
                new_year_issues.append(to_append)
            all_issue_weeks += old_year_issues
            all_issue_weeks += new_year_issues
        else:
            for i in range(int(issue_bounds[0]), int(issue_bounds[1])+1):
                to_append = issue_week_strings_to_times(['%s/%s' % (i, year),])[0]
                all_issue_weeks.append(to_append)
    elif len(issue_bounds) == 1:
        to_append = issue_week_strings_to_times(['%s/%s' %
                                                 (issue_bounds[0], year),])[0]
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
                            language=cdslang, number=2):
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

def issue_times_to_week_strings(issue_times, language=cdslang):
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
        Limit = 5
        counter = 0
        success = False
        # try going up 5
        while success == False and counter <= Limit:
            counter += 1
            success = get_consistent_issue_week(issue, week)
            if success == False:
                week = count_week_string_up(week)
            else:
                break
        # try going down 5
        counter = 0
        while success == False and counter <= Limit:
            counter += 1
            success = get_consistent_issue_week(issue, week)
            if success == False:
                week = count_week_string_down(week)
            else:
                break

        from webjournal_config import InvenioWebJournalReleaseDBError
        if success == False:
            raise InvenioWebJournalReleaseDBError(language)

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

def issue_week_strings_to_times(issue_weeks, language=cdslang):
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

def release_journal_update(update_issue, journal_name, language=cdslang):
    """
    Releases an update to a journal.
    """
    journal_id = get_journal_id(journal_name, language)
    run_sql("UPDATE jrnISSUE set date_released=NOW() \
                WHERE issue_number=%s \
                AND id_jrnJOURNAL=%s", (update_issue,
                                        journal_id))

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

def release_journal_issue(publish_issues, journal_name, language=cdslang):
    """
    Releases a new issue.
    """
    journal_id = get_journal_id(journal_name, language)
    if len(publish_issues) > 1:
        publish_issues.sort(sort_by_week_number)
        low_bound = publish_issues[0]
        high_bound = publish_issues[-1]
        issue_display = '%s-%s/%s' % (low_bound.split("/")[0],
                                      high_bound.split("/")[0],
                                      high_bound.split("/")[1])
        # remember convention: if we are going over a new year, take the higher
    else:
        issue_display = publish_issues[0]
    # produce the DB lines
    for publish_issue in publish_issues:
        run_sql("INSERT INTO jrnISSUE (id_jrnJOURNAL, issue_number, issue_display) \
                VALUES(%s, %s, %s)", (journal_id,
                                      publish_issue,
                                      issue_display))
    # set first issue to published
    release_journal_update(publish_issues[0], journal_name, language)

def delete_journal_issue(issue, journal_name, language=cdslang):
    """
    Deletes an issue from the DB.
    """
    journal_id = get_journal_id(journal_name, language)
    run_sql("DELETE FROM jrnISSUE WHERE issue_number=%s \
            AND id_jrnJOURNAL=%s",(issue, journal_id))

def was_alert_sent_for_issue(issue, journal_name, language):
    """
    """
    journal_id = get_journal_id(journal_name, language)
    date_announced = run_sql("SELECT date_announced FROM jrnISSUE \
                                WHERE issue_number=%s \
                                AND id_jrnJOURNAL=%s", (issue, journal_id))[0][0]
    if date_announced == None:
        return False
    else:
        return date_announced.timetuple()

def update_DB_for_alert(issue, journal_name, language):
    """
    """
    journal_id = get_journal_id(journal_name, language)
    run_sql("UPDATE jrnISSUE set date_announced=NOW() \
                WHERE issue_number=%s \
                AND id_jrnJOURNAL=%s", (issue,
                                        journal_id))

def get_number_of_articles_for_issue(issue, journal_name, language=cdslang):
    """
    Function that returns a dictionary with all categories and number of
    articles in each category.
    """
    config_strings = get_xml_from_config(["rule",], journal_name)
    rule_list = config_strings["rule"]
    all_articles = {}
    for rule in rule_list:
        category_name = rule.split(",")[0]
        if issue[0] == "0" and len(issue) == 7:
            week_nr = issue.split("/")[0]
            year = issue.split("/")[1]
            issue_nr_alternative = "%s/%s" % (week_nr[1], year)

            all_records_of_a_type = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                      (category_name, issue),
                                      f="&action_search=Search"))
            all_records_of_a_type += list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                      (category_name, issue_nr_alternative),
                                      f="&action_search=Search"))
        else:
            all_records_of_a_type = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                      (category_name, issue),
                                      f="&action_search=Search"))
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

def get_release_time(issue, journal_name, language=cdslang):
    """
    Gets the date at which an issue was released from the DB.
    """
    journal_id = get_journal_id(journal_name, language)
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

def get_announcement_time(issue, journal_name, language=cdslang):
    """
    Get the date at which an issue was announced through the alert system.
    """
    journal_id = get_journal_id(journal_name, language)
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

def get_journal_id(journal_name, language=cdslang):
    """
    Get the id for this journal from the DB.
    """
    from invenio.webjournal_config import InvenioWebJournalJournalIdNotFoundDBError
    try:
        journal_id = run_sql("SELECT id FROM jrnJOURNAL WHERE name=%s",
                          (journal_name,))[0][0]
    except:
        raise InvenioWebJournalJournalIdNotFoundDBError(language, journal_name)
    return journal_id

def guess_journal_name(language):
    """
    tries to take a guess what a user was looking for on the server if not
    providing a name for the journal.
    if there is only one journal on the server, returns the name of which,
    otherwise redirects to a list with possible journals.
    """
    from invenio.webjournal_config import InvenioWebJournalNoJournalOnServerError
    from invenio.webjournal_config import InvenioWebJournalNoNameError
    all_journals = run_sql("SELECT * FROM jrnJOURNAL ORDER BY id")
    if len(all_journals) == 0:
        raise InvenioWebJournalNoJournalOnServerError(language)
    elif len(all_journals) == 1:
        return all_journals[0][1]
    else:
        raise InvenioWebJournalNoNameError(language)

def get_current_issue(language, journal_name):
    """
    Returns the current issue of a journal as a string.
    """
    journal_id = get_journal_id(journal_name, language)
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

def get_current_publication(journal_name, current_issue, language=cdslang):
    """
    Returns the current publication string (current issue + updates).
    """
    journal_id = get_journal_id(journal_name, language)
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

def parse_url_string(req):
    """
    centralized function to parse any url string given in webjournal.

    returns:
        args: all arguments in dict form
    """
    args = {}
    # first get what you can from the argument string
    try:
        argument_string =  req.args#"name=CERNBulletin&issue=22/2007"#req.args
    except:
        argument_string = ""
    try:
        arg_list = argument_string.split("&")
    except:
        # no arguments
        arg_list = []
    for entry in arg_list:
        try:
            key = entry.split("=")[0]
        except KeyError:
            # todo: WARNING, could not parse one argument
            continue
        try:
            val = entry.split("=")[1]
        except:
            # todo: WARNING, could not parse one argument
            continue
        try:
            args[key] = val
        except:
            # todo: WARNING, argument given twice
            continue

    # secondly try to get default arguments
    try:
        for entry in req.journal_defaults.keys():
            try:
                args[entry] = req.journal_defaults[entry]
            except:
                # todo: Error, duplicate entry from args and defaults
                pass
    except:
        # no defaults
        pass
    return args

######################## EMAIL HELPER FUNCTIONS ###############################

def createhtmlmail (html, text, subject, toaddr):
        """
        Create a mime-message that will render HTML in popular
        MUAs, text in better ones.
        """
        import MimeWriter
        import mimetools
        import cStringIO

        out = cStringIO.StringIO() # output buffer for our message
        htmlin = cStringIO.StringIO(html)
        txtin = cStringIO.StringIO(text)

        writer = MimeWriter.MimeWriter(out)
        #
        # set up some basic headers... we put subject here
        # because smtplib.sendmail expects it to be in the
        # message body
        #
        writer.addheader("Subject", subject)
        writer.addheader("MIME-Version", "1.0")
        writer.addheader("To", toaddr)
        #
        # start the multipart section of the message
        # multipart/alternative seems to work better
        # on some MUAs than multipart/mixed
        #
        writer.startmultipartbody("alternative")
        writer.flushheaders()
        #
        # the plain text section
        #
        subpart = writer.nextpart()
        subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
        #pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
        pout = subpart.startbody("text/plain", [("charset", 'utf-8')])
        mimetools.encode(txtin, pout, 'quoted-printable')
        txtin.close()
        #
        # start the html subpart of the message
        #
        subpart = writer.nextpart()
        subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
        txtin.close()
        #
        # start the html subpart of the message
        #
        subpart = writer.nextpart()
        subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
        #
        # returns us a file-ish object we can write to
        #
        #pout = subpart.startbody("text/html", [("charset", 'us-ascii')])
        pout = subpart.startbody("text/html", [("charset", 'utf-8')])
        mimetools.encode(htmlin, pout, 'quoted-printable')
        htmlin.close()
        #
        # Now that we're done, close our writer and
        # return the message body
        #
        writer.lastpart()
        msg = out.getvalue()
        out.close()
        print msg
        return msg

def put_css_in_file(html_message, journal_name):
    """
    Takes an external css file and puts all the content of it in the head
    of an HTML file in style tags. (Used for HTML emails)
    """
    config_strings = get_xml_from_config(["screen"], journal_name)
    try:
        css_path = config_strings["screen"][0]
    except:
        register_exception(req=None,
                           suffix="No css file for journal %s. Is this right?"
                           % journal_name)
        return
    css_file = urlopen('%s/%s' % (weburl, css_path))
    css = css_file.read()
    css = make_full_paths_in_css(css, journal_name)
    html_parted = html_message.split("</head>")
    if len(html_parted) > 1:
        html = '%s<style type="text/css">%s</style></head>%s' % (html_parted[0],
                                                        css,
                                                        html_parted[1])
    else:
        html_parted = html_message.split("<html>")
        if len(html_parted) > 1:
            html = '%s<html><head><style type="text/css">%s</style></head>%s' % (html_parted[0],
                                                                                 css,
                                                                                 html_parted[1])
        else:
            return
    return html

def make_full_paths_in_css(css, journal_name):
    """
    """
    url_pattern = re.compile('''url\(["']?\s*(?P<url>\S*)\s*["']?\)''',
                             re.DOTALL)
    url_iter = url_pattern.finditer(css)
    rel_to_full_path = {}
    for url in url_iter:
        url_string = url.group("url")
        url_string = url_string.replace("\"", "")
        url_string = url_string.replace("\'", "")
        if url_string[:6] != "http://":
            rel_to_full_path[url_string] = '"%s/img/%s/%s"' % (weburl,
                                                               journal_name,
                                                               url_string)
    for url in rel_to_full_path.keys():
        css = css.replace(url, rel_to_full_path[url])
    return css

############################ CACHING FUNCTIONS ################################

def cache_index_page(html, journal_name, category, issue, ln):
    """
    Caches the index page main area of a Bulletin
    (right hand menu cannot be cached)
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")
    if not (os.path.isdir('%s/webjournal/%s' % (CFG_CACHEDIR, journal_name) )):
        os.makedirs('%s/webjournal/%s' % (CFG_CACHEDIR, journal_name))
    cached_file = open('%s/webjournal/%s/%s_index_%s_%s.html' % (CFG_CACHEDIR,
                                                                 journal_name,
                                                                 issue, category,
                                                                 ln), "w")
    cached_file.write(html)
    cached_file.close()



def get_index_page_from_cache(journal_name, category, issue, ln):
    """
    Function to get an index page from the cache.
    False if not in cache.
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")
    try:
        cached_file = open('%s/webjournal/%s/%s_index_%s_%s.html'
                        % (CFG_CACHEDIR, journal_name, issue, category, ln)).read()
    except:
        return False
    return cached_file

def cache_article_page(html, journal_name, category, recid, issue, ln):
    """
    Caches an article view of a journal.
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")
    if not (os.path.isdir('%s/webjournal/%s' % (CFG_CACHEDIR, journal_name) )):
        os.makedirs('%s/webjournal/%s' % (CFG_CACHEDIR, journal_name))
    cached_file = open('%s/webjournal/%s/%s_article_%s_%s_%s.html'
                       % (CFG_CACHEDIR, journal_name, issue, category, recid, ln),
                       "w")
    cached_file.write(html)
    cached_file.close()

def get_article_page_from_cache(journal_name, category, recid, issue, ln):
    """
    Gets an article view of a journal from cache.
    False if not in cache.
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")
    try:
        cached_file = open('%s/webjournal/%s/%s_article_%s_%s_%s.html'
                % (CFG_CACHEDIR, journal_name, issue, category, recid, ln)).read()
    except:
        return False

    return cached_file

def clear_cache_for_article(journal_name, category, recid, issue):
    """
    Resets the cache for an article (e.g. after an article has been modified)
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")
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
    all_cached_files = os.listdir('%s/webjournal/%s/'
                                  % (CFG_CACHEDIR, journal_name))
    for cached_file in all_cached_files:
        if cached_file[:7] == issue:
            try:
                os.remove('%s/webjournal/%s/%s'
                          % (CFG_CACHEDIR, journal_name, cached_file))
            except:
                return False
    return True

def cache_recid_data_dict_CERNBulletin(recid, issue, rule, order):
    """
    The CERN Bulletin has a specific recid data dict that is cached
    using cPickle.
    """
    issue = issue.replace("/", "_")
    # get whats in there
    if not os.path.isdir('%s/webjournal/CERNBulletin' % CFG_CACHEDIR):
        os.makedirs('%s/webjournal/CERNBulletin' % CFG_CACHEDIR)
    try:
        temp_file = open('%s/webjournal/CERNBulletin/%s_recid_order_map.dat'
                         % (CFG_CACHEDIR, issue))
    except:
        temp_file = open('%s/webjournal/CERNBulletin/%s_recid_order_map.dat'
                         % (CFG_CACHEDIR, issue), "w")
    try:
        recid_map = cPickle.load(temp_file)
    except:
        recid_map = ""
    temp_file.close()
    # add new recid
    if recid_map == "":
        recid_map = {}
    if not recid_map.has_key(rule):
        recid_map[rule] = {}
    recid_map[rule][order] = recid
    # save back
    temp_file = open('%s/webjournal/CERNBulletin/%s_recid_order_map.dat'
                     % (CFG_CACHEDIR, issue), "w")
    cPickle.dump(recid_map, temp_file)
    temp_file.close()

def get_cached_recid_data_dict_CERNBulletin(issue, rule):
    """
    Function to restore from cache the dict Data Type that the CERN Bulletin
    uses for mapping between the order of an article and its recid.
    """
    issue = issue.replace("/", "_")
    try:
        temp_file = open('%s/webjournal/CERNBulletin/%s_recid_order_map.dat'
                         % (CFG_CACHEDIR, issue))
    except:
        return {}
    try:
        recid_map = cPickle.load(temp_file)
    except:
        return {}
    try:
        recid_dict = recid_map[rule]
    except:
        recid_dict = {}
    return recid_dict

######################### CERN SPECIFIC FUNCTIONS #############################

def get_order_dict_from_recid_list_CERNBulletin(list, issue_number):
    """
    special derivative of the get_order_dict_from_recid_list function that
    extends the behavior insofar as too return a dictionary in which every
    entry is a dict (there can be several number 1 articles) and every dict entry
    is a tuple with an additional boolean to indicate if there is a graphical "new"
    flag. the dict key on the second level is the upload time in epoch seconds.
    e.g.
    {1:{10349:(rec, true), 24792:(rec, false)}, 2:{736424:(rec,false)}, 24791:{1:(rec:false}}
    the ordering inside an order number is given by upload date. so it is an ordering
        1-level -> number
        2-level -> date
    """
    ordered_records = {}
    for record in list:
        temp_rec = BibFormatObject(record)
        issue_numbers = temp_rec.fields('773__n')
        order_number = temp_rec.fields('773__c')
        try:
#            upload_date = run_sql("SELECT modification_date FROM bibrec WHERE id=%s", (record, ))[0][0]
            upload_date = run_sql("SELECT creation_date FROM bibrec WHERE id=%s", (record, ))[0][0]
        except:
            pass
        #return repr(time.mktime(upload_date.timetuple()))
        # todo: the marc fields have to be set'able by some sort of config interface
        n = 0
        for temp_issue in issue_numbers:
            if temp_issue == issue_number:
                try:
                    order_number = int(order_number[n])
                except:
                    # todo: Warning, record does not support numbering scheme
                    order_number = -1
            n+=1
        if order_number != -1:
            try:
                if ordered_records.has_key(order_number):
                    ordered_records[order_number][int(time.mktime(upload_date.timetuple()))] = (record, True)
                else:
                    ordered_records[order_number] = {int(time.mktime(upload_date.timetuple())):(record, False)}
            except:
                pass
                # todo: Error, there are two records with the same order_number in the issue
        else:
            ordered_records[max(ordered_records.keys()) + 1] = record

    return ordered_records

def get_recid_from_order_CERNBulletin(order, rule, issue_number):
    """
    same functionality as get_recid_from_order above, but extends it for
    the CERN Bulletin in a way so multiple entries for the first article are
    possible.

    parameters:
        order:  the order at which the record appears in the journal as passed
                in the url
        rule:   the defining rule of the journal record category
        issue_number:   the issue number for which we are searching

    returns:
        recid:  the recid of the ordered record
    """
    # try to get it from cache
    recid_dict = {}
    recid_dict = get_cached_recid_data_dict_CERNBulletin(issue_number, rule)
    if recid_dict.has_key(order):
        recid = recid_dict[order]
        return recid
    alternative_issue_number = "00/0000"
    # get the id list
    if issue_number[0] == "0":
        alternative_issue_number = issue_number[1:]
        all_records = list(search_pattern(p="%s and 773__n:%s" %
                                      (rule, issue_number),
                                      f="&action_search=Search"))
        all_records += list(search_pattern(p="%s and 773__n:%s" %
                                      (rule, alternative_issue_number),
                                      f="&action_search=Search"))
    else:
        all_records = list(search_pattern(p="%s and 773__n:%s" %
                                      (rule, issue_number),
                                      f="&action_search=Search"))
    #raise repr(all_records)
    ordered_records = {}
    new_addition_records = []
    for record in all_records:
        temp_rec = BibFormatObject(record)  # todo: refactor with get_fieldValues from search_engine
        issue_numbers = temp_rec.fields('773__n')
        order_number = temp_rec.fields('773__c')
        #raise "%s:%s" % (repr(issue_numbers), repr(order_number))
        # todo: fields for issue number and order number have to become generic
        n = 0
        for temp_issue in issue_numbers:
            if temp_issue == issue_number or temp_issue == alternative_issue_number:
                try:
                    order_number = int(order_number[n])
                except:
                    register_exception(stream="warning", suffix="There \
                        was an article in the journal that does not support \
                        a numbering scheme")
                    order_number = -1000
            n+=1
        if order_number == -1000:
            ordered_records[max(ordered_records.keys()) + 1] = record
        elif order_number <= 1:
            new_addition_records.append(record)
        else:
            try:
                ordered_records[order_number] = record
            except:
                register_exception(stream='warning', suffix="There \
                        were double entries for an order in this journal.")

    # process the CERN Bulletin specific new additions
    if len(new_addition_records) > 1 and int(order) <= 1:
        # if we are dealing with a new addition (order number smaller 1)
        ordered_new_additions = {}
        for record in new_addition_records:
            #upload_date = run_sql("SELECT modification_date FROM bibrec WHERE id=%s", (record, ))[0][0]
            upload_date = run_sql("SELECT creation_date FROM bibrec WHERE id=%s", (record, ))[0][0]
            ordered_new_additions[int(time.mktime(upload_date.timetuple()))] = record
        i = 1
        while len(ordered_new_additions) > 0:
            temp_key = pop_oldest_article_CERNBulletin(ordered_new_additions)
            record = ordered_new_additions.pop(int(temp_key))
            ordered_records[i] = record
            i -=1
    else:
        # if we have only one record on 1 just push it through
        ordered_records[1] = new_addition_records[0]
    try:
        recid = ordered_records[int(order)]
    except:
        register_exception()

    cache_recid_data_dict_CERNBulletin(recid, issue_number, rule, order)
    return recid

def pop_newest_article_CERNBulletin(news_article_dict):
    """
    pop key of the most recent article (highest c-timestamp)
    """
    keys = news_article_dict.keys()
    keys.sort()
    key = keys[len(keys)-1]
    return key

def pop_oldest_article_CERNBulletin(news_article_dict):
    """
    pop key of the oldest article (lowest c-timestamp)
    """
    keys = news_article_dict.keys()
    keys.sort()
    key = keys[0]
    return key

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

# (<a\s*href=["']?(?P<hyperlink>\S*)["']?>)?\s*<center>\s*<img\s*(class=["']imageScale["'])*?\s*src=(?P<image>\S*)\s*border=1\s*(/)?>
# \s*</center>\s*(</a>)?(<br />|<br />|<br/>)*(<b>\s*<i>\s*<center>(?P<caption>.*?)</center>\s*</i>\s*</b>)?
#url(["']?(?P<url>\S*)["']?)
