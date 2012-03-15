# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2007, 2008, 2009, 2010, 2011 CERN.
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
Various utilities for WebJournal, e.g. config parser, etc.
"""

import time
import datetime
import calendar
import re
import os
import cPickle
import math
import urllib
from MySQLdb import OperationalError
from xml.dom import minidom
from urlparse import urlparse

from invenio.config import \
     CFG_ETCDIR, \
     CFG_SITE_URL, \
     CFG_CACHEDIR, \
     CFG_SITE_LANG, \
     CFG_ACCESS_CONTROL_LEVEL_SITE, \
     CFG_SITE_SUPPORT_EMAIL, \
     CFG_DEVEL_SITE
from invenio.dbquery import run_sql
from invenio.bibformat_engine import BibFormatObject
from invenio.search_engine import search_pattern, record_exists
from invenio.messages import gettext_set_language
from invenio.errorlib import register_exception

########################### REGULAR EXPRESSIONS ######################

header_pattern = re.compile('<p\s*(align=justify)??>\s*<strong>(?P<header>.*?)</strong>\s*</p>')
header_pattern2 = re.compile('<p\s*(class="articleHeader").*?>(?P<header>.*?)</p>')
para_pattern = re.compile('<p.*?>(?P<paragraph>.+?)</p>', re.DOTALL)
img_pattern = re.compile('<img.*?src=("|\')?(?P<image>\S+?)("|\'|\s).*?/>', re.DOTALL)
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
                               #'


############################## FEATURED RECORDS ######################

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


############################ ARTICLES RELATED ########################

def get_order_dict_from_recid_list(recids, journal_name, issue_number,
                                   newest_first=False,
                                   newest_only=False):
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

    Parameters:

              recids - a list of all recid's that should be brought
                       into order

        journal_name - the name of the journal

        issue_number - *str* the issue_number for which we are
                       deriving the order

        newest_first - *bool* if True, new articles should be placed
                       at beginning of the list. If so, their
                       position/order will be negative integers

         newest_only - *bool* if only new articles should be returned

    Returns:

            ordered_records: a dictionary with the recids ordered by
                             keys
    """
    ordered_records = {}
    ordered_new_records = {}
    records_without_defined_order = []
    new_records_without_defined_order = []

    for record in recids:
        temp_rec = BibFormatObject(record)
        articles_info = temp_rec.fields('773__')
        for article_info in articles_info:
            if article_info.get('n', '') == issue_number or \
                   '0' + article_info.get('n', '') == issue_number:
                if article_info.has_key('c') and \
                       article_info['c'].isdigit():
                    order_number = int(article_info.get('c', ''))
                    if (newest_first or newest_only) and \
                           is_new_article(journal_name, issue_number, record):
                        if ordered_new_records.has_key(order_number):
                            ordered_new_records[order_number].append(record)
                        else:
                            ordered_new_records[order_number] = [record]
                    elif not newest_only:
                        if ordered_records.has_key(order_number):
                            ordered_records[order_number].append(record)
                        else:
                            ordered_records[order_number] = [record]
                else:
                    # No order? No problem! Append it at the end.
                    if newest_first and is_new_article(journal_name, issue_number, record):
                        new_records_without_defined_order.append(record)
                    elif not newest_only:
                        records_without_defined_order.append(record)

    # Append records without order at the end of the list
    if records_without_defined_order:
        if ordered_records:
            ordered_records[max(ordered_records.keys()) + 1] = records_without_defined_order
        else:
            ordered_records[1] = records_without_defined_order

    # Append new records without order at the end of the list of new
    # records
    if new_records_without_defined_order:
        if ordered_new_records:
            ordered_new_records[max(ordered_new_records.keys()) + 1] = new_records_without_defined_order
        else:
            ordered_new_records[1] = new_records_without_defined_order

    # Append new records at the beginning of the list of 'old'
    # records. To do so, use negative integers
    if ordered_new_records:
        highest_new_record_order = max(ordered_new_records.keys())
        for order, new_records in ordered_new_records.iteritems():
            ordered_records[- highest_new_record_order + order - 1] = new_records

    for (order, records) in ordered_records.iteritems():
        # Reverse so that if there are several articles at same
        # positon, newest appear first
        records.reverse()

    return ordered_records

def get_journal_articles(journal_name, issue, category,
                         newest_first=False, newest_only=False):
    """
    Returns the recids in given category and journal, for given issue
    number. The returned recids are grouped according to their 773__c
    field.
    Example of returned value:
                {'1': [2390, 2386, 2385],
                 '3': [2388],
                 '2': [2389],
                 '4': [2387]}

    Parameters:

       journal_name  - *str* the name of the journal (as used in URLs)
              issue  - *str* the issue. Eg: "08/2007"
           category  - *str* the name of the category

        newest_first - *bool* if True, new articles should be placed
                       at beginning of the list. If so, their
                       position/order will be negative integers

         newest_only - *bool* if only new articles should be returned

    """
    use_cache = True
    current_issue = get_current_issue(CFG_SITE_LANG, journal_name)
    if issue_is_later_than(issue, current_issue):
        # If we are working on unreleased issue, do not use caching
        # mechanism
        use_cache = False

    if use_cache:
        cached_articles = _get_cached_journal_articles(journal_name, issue, category)
        if cached_articles is not None:
            ordered_articles = get_order_dict_from_recid_list(cached_articles,
                                                              journal_name,
                                                              issue,
                                                              newest_first,
                                                              newest_only)
            return ordered_articles

    # Retrieve the list of rules that map Category -> Search Pattern.
    # Keep only the rule matching our category
    config_strings = get_xml_from_config(["record/rule"], journal_name)
    category_to_search_pattern_rules = config_strings["record/rule"]

    try:
        matching_rule = [rule.split(',', 1) for rule in \
                         category_to_search_pattern_rules \
                         if rule.split(',')[0] == category]
    except:
        return []


    recids_issue = search_pattern(p='773__n:%s' % issue)
    recids_rule = search_pattern(p=matching_rule[0][1])
    if issue[0] == '0':
        # search for 09/ and 9/
        recids_issue.union_update(search_pattern(p='773__n:%s' % issue.lstrip('0')))

    recids_rule.intersection_update(recids_issue)
    recids = [recid for recid in recids_rule if record_exists(recid) == 1]

    if use_cache:
        _cache_journal_articles(journal_name, issue, category, recids)
    ordered_articles = get_order_dict_from_recid_list(recids,
                                                      journal_name,
                                                      issue,
                                                      newest_first,
                                                      newest_only)

    return ordered_articles

def _cache_journal_articles(journal_name, issue, category, articles):
    """
    Caches given articles IDs.
    """
    journal_cache_path = get_journal_article_cache_path(journal_name,
                                                        issue)
    try:
        journal_cache_file = open(journal_cache_path, 'r')
        journal_info = cPickle.load(journal_cache_file)
        journal_cache_file.close()
    except cPickle.PickleError, e:
        journal_info = {}
    except IOError:
        journal_info = {}
    except EOFError:
        journal_info = {}

    if not journal_info.has_key('journal_articles'):
        journal_info['journal_articles'] = {}
    journal_info['journal_articles'][category] = articles

    # Create cache directory if it does not exist
    journal_cache_dir = os.path.dirname(journal_cache_path)
    if not os.path.exists(journal_cache_dir):
        try:
            os.makedirs(journal_cache_dir)
        except:
            return False

    journal_cache_file = open(journal_cache_path, 'w')
    cPickle.dump(journal_info, journal_cache_file)
    journal_cache_file.close()
    return True

def _get_cached_journal_articles(journal_name, issue, category):
    """
    Retrieve the articles IDs cached for this journal.

    Returns None if cache does not exist or more than 5 minutes old
    """
    # Check if our cache is more or less up-to-date (not more than 5
    # minutes old)
    try:
        journal_cache_path = get_journal_article_cache_path(journal_name,
                                                            issue)
        last_update = os.path.getctime(journal_cache_path)
    except Exception, e :
        return None
    now = time.time()
    if (last_update + 5*60) < now:
        return None

    # Get from cache
    try:
        journal_cache_file = open(journal_cache_path, 'r')
        journal_info = cPickle.load(journal_cache_file)
        journal_articles = journal_info.get('journal_articles', {}).get(category, None)
        journal_cache_file.close()
    except cPickle.PickleError, e:
        journal_articles = None
    except IOError:
        journal_articles = None
    except EOFError:
        journal_articles = None

    return journal_articles

def is_new_article(journal_name, issue, recid):
    """
    Check if given article should be considered as new or not.

    New articles are articles that have never appeared in older issues
    than given one.
    """
    article_found_in_older_issue = False
    temp_rec = BibFormatObject(recid)
    publication_blocks = temp_rec.fields('773__')

    for publication_block in publication_blocks:
        this_issue_number, this_issue_year = issue.split('/')
        issue_number, issue_year = publication_block.get('n', '/').split('/', 1)

        if int(issue_year) < int(this_issue_year):
            # Found an older issue
            article_found_in_older_issue = True
            break
        elif int(issue_year) == int(this_issue_year) and \
                 int(issue_number) < int(this_issue_number):
            # Found an older issue
            article_found_in_older_issue = True
            break

    return not article_found_in_older_issue


############################ CATEGORIES RELATED ######################

def get_journal_categories(journal_name, issue=None):
    """
    List the categories for the given journal and issue.
    Returns categories in same order as in config file.

    Parameters:

      journal_name  - *str* the name of the journal (as used in URLs)

              issue - *str* the issue. Eg:'08/2007'. If None, consider
                      all categories defined in journal config
    """
    categories = []

    current_issue = get_current_issue(CFG_SITE_LANG, journal_name)
    config_strings = get_xml_from_config(["record/rule"], journal_name)
    all_categories = [rule.split(',')[0] for rule in \
                      config_strings["record/rule"]]

    if issue is None:
        return all_categories

    for category in all_categories:
        recids = get_journal_articles(journal_name,
                                      issue,
                                      category)
        if len(recids.keys()) > 0:
            categories.append(category)

    return categories

def get_category_query(journal_name, category):
    """
    Returns the category definition for the given category and journal name

    Parameters:

      journal_name  - *str* the name of the journal (as used in URLs)

            categoy - *str* a category name, as found in the XML config
    """
    config_strings = get_xml_from_config(["record/rule"], journal_name)
    category_to_search_pattern_rules = config_strings["record/rule"]

    try:
        matching_rule = [rule.split(',', 1)[1].strip() for rule in \
                         category_to_search_pattern_rules \
                         if rule.split(',')[0] == category]
    except:
        return None

    return matching_rule[0]


######################### JOURNAL CONFIG VARS ######################

cached_parsed_xml_config = {}
def get_xml_from_config(nodes, journal_name):
    """
    Returns values from the journal configuration file.

    The needed values can be specified by node name, or by a hierarchy
    of nodes names using '/' as character to mean 'descendant of'.
    Eg. 'record/rule' to get all the values of 'rule' tags inside the
    'record' node

    Returns a dictionary with a key for each query and a list of
    strings (innerXml) results for each key.

    Has a special field "config_fetching_error" that returns an error when
    something has gone wrong.
    """
    # Get and open the config file
    results = {}
    if cached_parsed_xml_config.has_key(journal_name):
        config_file = cached_parsed_xml_config[journal_name]
    else:
        config_path = '%s/webjournal/%s/%s-config.xml' % \
                      (CFG_ETCDIR, journal_name, journal_name)
        config_file = minidom.Document
        try:
            config_file = minidom.parse("%s" % config_path)
        except:
            # todo: raise exception "error: no config file found"
            results["config_fetching_error"] = "could not find config file"
            return results
        else:
            cached_parsed_xml_config[journal_name] = config_file

    for node_path in nodes:
        node = config_file
        for node_path_component in node_path.split('/'):
            # pylint: disable=E1103
            # The node variable can be rewritten in the loop and therefore
            # its type can change.
            if node != config_file and node.length > 0:
                # We have a NodeList object: consider only first child
                node = node.item(0)
            # pylint: enable=E1103
            try:
                node = node.getElementsByTagName(node_path_component)
            except:
                # WARNING, config did not have such value
                node = []
                break

        results[node_path] = []
        for result in node:
            try:
                result_string = result.firstChild.toxml(encoding="utf-8")
            except:
                # WARNING, config did not have such value
                continue
            results[node_path].append(result_string)

    return results

def get_journal_issue_field(journal_name):
    """
    Returns the MARC field in which this journal expects to find
    the issue number. Read this from the journal config file

    Parameters:

      journal_name  - *str* the name of the journal (as used in URLs)

    """
    config_strings = get_xml_from_config(["issue_number"], journal_name)

    try:
        issue_field = config_strings["issue_number"][0]
    except:
        issue_field = '773__n'

    return issue_field

def get_journal_css_url(journal_name, type='screen'):
    """
    Returns URL to this journal's CSS.

    Parameters:

      journal_name  - *str* the name of the journal (as used in URLs)

               type - *str* 'screen' or 'print', depending on the kind
               of CSS
    """
    config_strings = get_xml_from_config([type], journal_name)
    css_path = ''
    try:
        css_path = config_strings["screen"][0]
    except Exception:
        register_exception(req=None,
                           suffix="No css file for journal %s. Is this right?" % \
                           journal_name)
    return CFG_SITE_URL + '/' + css_path

def get_journal_submission_params(journal_name):
    """
    Returns the (doctype, identifier element, identifier field) for
    the submission of articles in this journal, so that it is possible
    to build direct submission links.

    Parameter:
          journal_name  - *str* the name of the journal (as used in URLs)
    """
    doctype = ''
    identifier_field = ''
    identifier_element = ''

    config_strings = get_xml_from_config(["submission/doctype"], journal_name)
    if config_strings.get('submission/doctype', ''):
        doctype = config_strings['submission/doctype'][0]

    config_strings = get_xml_from_config(["submission/identifier_element"], journal_name)
    if config_strings.get('submission/identifier_element', ''):
        identifier_element = config_strings['submission/identifier_element'][0]

    config_strings = get_xml_from_config(["submission/identifier_field"], journal_name)
    if config_strings.get('submission/identifier_field', ''):
        identifier_field = config_strings['submission/identifier_field'][0]
    else:
        identifier_field = '037__a'

    return (doctype, identifier_element, identifier_field)

def get_journal_draft_keyword_to_remove(journal_name):
    """
    Returns the keyword that should be removed from the article
    metadata in order to move the article from Draft to Ready
    """
    config_strings = get_xml_from_config(["draft_keyword"], journal_name)
    if config_strings.get('draft_keyword', ''):
        return config_strings['draft_keyword'][0]
    return ''

def get_journal_alert_sender_email(journal_name):
    """
    Returns the email address that should be used as send of the alert
    email.
    If not specified, use CFG_SITE_SUPPORT_EMAIL
    """
    config_strings = get_xml_from_config(["alert_sender"], journal_name)
    if config_strings.get('alert_sender', ''):
        return config_strings['alert_sender'][0]
    return CFG_SITE_SUPPORT_EMAIL

def get_journal_alert_recipient_email(journal_name):
    """
    Returns the default email address of the recipients of the email
    Return a string of comma-separated emails.
    """
    if CFG_DEVEL_SITE:
        # To be on the safe side, do not return the default alert recipients.
        return ''
    config_strings = get_xml_from_config(["alert_recipients"], journal_name)
    if config_strings.get('alert_recipients', ''):
        return config_strings['alert_recipients'][0]
    return ''

def get_journal_collection_to_refresh_on_release(journal_name):
    """
    Returns the list of collection to update (WebColl) upon release of
    an issue.
    """
    from invenio.search_engine import collection_reclist_cache
    config_strings = get_xml_from_config(["update_on_release/collection"], journal_name)
    return [coll for coll in config_strings.get('update_on_release/collection', []) if \
            collection_reclist_cache.cache.has_key(coll)]

def get_journal_index_to_refresh_on_release(journal_name):
    """
    Returns the list of indexed to update (BibIndex) upon release of
    an issue.
    """
    from invenio.bibindex_engine import get_index_id_from_index_name
    config_strings = get_xml_from_config(["update_on_release/index"], journal_name)
    return [index for index in config_strings.get('update_on_release/index', []) if \
            get_index_id_from_index_name(index) != '']

def get_journal_template(template, journal_name, ln=CFG_SITE_LANG):
    """
    Returns the journal templates name for the given template type
    Raise an exception if template cannot be found.
    """
    from invenio.webjournal_config import \
         InvenioWebJournalTemplateNotFoundError
    config_strings = get_xml_from_config([template], journal_name)

    try:
        index_page_template = 'webjournal' + os.sep + \
                              config_strings[template][0]
    except:
        raise InvenioWebJournalTemplateNotFoundError(ln,
                                                     journal_name,
                                                     template)

    return index_page_template

def get_journal_name_intl(journal_name, ln=CFG_SITE_LANG):
    """
    Returns the nice name of the journal, translated if possible
    """
    _ = gettext_set_language(ln)

    config_strings = get_xml_from_config(["niceName"], journal_name)
    if config_strings.get('niceName', ''):
        return _(config_strings['niceName'][0])
    return ''

def get_journal_languages(journal_name):
    """
    Returns the list of languages defined for this journal
    """
    config_strings = get_xml_from_config(["languages"], journal_name)
    if config_strings.get('languages', ''):
        return [ln.strip() for ln in \
                config_strings['languages'][0].split(',')]
    return []

def get_journal_issue_grouping(journal_name):
    """
    Returns the number of issue that are typically released at the
    same time.

    This is used if every two weeks you release an issue that should
    contains issue of next 2 weeks (eg. at week 16, you relase an
    issue named '16-17/2009')

    This number should help in the admin interface to guess how to
    release the next issue (can be overidden by user).
    """
    config_strings = get_xml_from_config(["issue_grouping"], journal_name)
    if config_strings.get('issue_grouping', ''):
        issue_grouping = config_strings['issue_grouping'][0]
        if issue_grouping.isdigit() and int(issue_grouping) > 0:
            return int(issue_grouping)
    return 1

def get_journal_nb_issues_per_year(journal_name):
    """
    Returns the default number of issues per year for this journal.

    This number should help in the admin interface to guess the next
    issue number (can be overidden by user).
    """
    config_strings = get_xml_from_config(["issues_per_year"], journal_name)
    if config_strings.get('issues_per_year', ''):
        issues_per_year = config_strings['issues_per_year'][0]
        if issues_per_year.isdigit() and int(issues_per_year) > 0:
            return int(issues_per_year)
    return 52

def get_journal_preferred_language(journal_name, ln):
    """
    Returns the most adequate language to display the journal, given a
    language.
    """
    languages = get_journal_languages(journal_name)
    if ln in languages:
        return ln
    elif CFG_SITE_LANG in languages:
        return CFG_SITE_LANG
    elif languages:
        return languages
    else:
        return CFG_SITE_LANG

def get_unreleased_issue_hiding_mode(journal_name):
    """
    Returns how unreleased issue should be treated. Can be one of the
    following string values:

       'future' - only future unreleased issues are hidden. Past
                  unreleased one can be viewed

          'all' - any unreleased issue (past and future) have to be
                  hidden

       - 'none' - no unreleased issue is hidden
    """
    config_strings = get_xml_from_config(["hide_unreleased_issues"], journal_name)
    if config_strings.get('hide_unreleased_issues', ''):
        hide_unreleased_issues = config_strings['hide_unreleased_issues'][0]
        if hide_unreleased_issues in ['future', 'all', 'none']:
            return hide_unreleased_issues
    return 'all'

def get_first_issue_from_config(journal_name):
    """
    Returns the first issue as defined from config. This should only
    be useful when no issue have been released.

    If not specified, returns the issue made of current week number
    and year.
    """
    config_strings = get_xml_from_config(["first_issue"], journal_name)
    if config_strings.has_key('first_issue'):
        return config_strings['first_issue'][0]
    return time.strftime("%W/%Y", time.localtime())

######################## TIME / ISSUE FUNCTIONS ######################

def get_current_issue(ln, journal_name):
    """
    Returns the current issue of a journal as a string.
    Current issue is the latest released issue.
    """
    journal_id = get_journal_id(journal_name, ln)
    try:
        current_issue = run_sql("""SELECT issue_number
                                     FROM jrnISSUE
                                    WHERE date_released <= NOW()
                                      AND id_jrnJOURNAL=%s
                                 ORDER BY date_released DESC
                                    LIMIT 1""",
                                (journal_id,))[0][0]
    except:
        # start the first journal ever
        current_issue = get_first_issue_from_config(journal_name)
        run_sql("""INSERT INTO jrnISSUE (id_jrnJOURNAL, issue_number, issue_display)
                        VALUES(%s, %s, %s)""",
                (journal_id,
                 current_issue,
                 current_issue))
    return current_issue

def get_all_released_issues(journal_name):
    """
    Returns the list of released issue, ordered by release date

    Note that it only includes the issues that are considered as
    released in the DB: it will not for example include articles that
    have been imported in the system but not been released
    """
    journal_id = get_journal_id(journal_name)
    res = run_sql("""SELECT issue_number
                     FROM jrnISSUE
                     WHERE id_jrnJOURNAL = %s
                       AND UNIX_TIMESTAMP(date_released) != 0
                     ORDER BY date_released DESC""",
                  (journal_id,))
    if res:
        return [row[0] for row in res]
    else:
        return []

def get_next_journal_issues(current_issue_number, journal_name, n=2):
    """
    This function suggests the 'n' next issue numbers
    """
    number, year = current_issue_number.split('/', 1)
    number = int(number)
    year = int(year)
    number_issues_per_year = get_journal_nb_issues_per_year(journal_name)
    next_issues = [make_issue_number(journal_name,
                                     ((number - 1 + i) % (number_issues_per_year)) + 1,
                                      year + ((number - 1 + i) / number_issues_per_year)) \
                   for i in range(1, n + 1)]

    return next_issues

def get_grouped_issues(journal_name, issue_number):
    """
    Returns all the issues grouped with a given one.

    Issues are sorted from the oldest to newest one.
    """
    grouped_issues = []
    journal_id = get_journal_id(journal_name, CFG_SITE_LANG)
    issue_display = get_issue_number_display(issue_number, journal_name)
    res = run_sql("""SELECT issue_number
                     FROM jrnISSUE
                     WHERE id_jrnJOURNAL=%s AND issue_display=%s""",
                  (journal_id,
                   issue_display))
    if res:
        grouped_issues = [row[0] for row in res]
        grouped_issues.sort(compare_issues)

    return grouped_issues

def compare_issues(issue1, issue2):
    """
    Comparison function for issues.

    Returns:
        -1 if issue1 is older than issue2
         0 if issues are equal
         1 if issue1 is newer than issue2
    """
    issue1_number, issue1_year = issue1.split('/', 1)
    issue2_number, issue2_year = issue2.split('/', 1)

    if int(issue1_year) == int(issue2_year):
        return cmp(int(issue1_number), int(issue2_number))
    else:
        return cmp(int(issue1_year), int(issue2_year))

def issue_is_later_than(issue1, issue2):
    """
    Returns true if issue1 is later than issue2
    """
    issue_number1, issue_year1 = issue1.split('/', 1)
    issue_number2, issue_year2 = issue2.split('/', 1)

    if int(issue_year1) > int(issue_year2):
        return True
    elif int(issue_year1) == int(issue_year2):
        return int(issue_number1) > int(issue_number2)
    else:
        return False

def get_issue_number_display(issue_number, journal_name,
                             ln=CFG_SITE_LANG):
    """
    Returns the display string for a given issue number.
    """
    journal_id = get_journal_id(journal_name, ln)
    issue_display = run_sql("""SELECT issue_display
                                 FROM jrnISSUE
                                WHERE issue_number=%s
                                  AND id_jrnJOURNAL=%s""",
                            (issue_number, journal_id))
    if issue_display:
        return issue_display[0][0]
    else:
        # Not yet released...
        return issue_number

def make_issue_number(journal_name, number, year, for_url_p=False):
    """
    Creates a normalized issue number representation with given issue
    number (as int or str) and year (as int or str).

    Reverse the year and number if for_url_p is True
    """
    number_issues_per_year = get_journal_nb_issues_per_year(journal_name)
    precision = len(str(number_issues_per_year))
    number = int(str(number))
    year = int(str(year))
    if for_url_p:
        return ("%i/%0" + str(precision) + "i") % \
               (year, number)
    else:
        return ("%0" + str(precision) + "i/%i") % \
               (number, year)

def get_release_datetime(issue, journal_name, ln=CFG_SITE_LANG):
    """
    Gets the date at which an issue was released from the DB.
    Returns None if issue has not yet been released.

    See issue_to_datetime() to get the *theoretical* release time of an
    issue.
    """
    journal_id = get_journal_id(journal_name, ln)
    try:
        release_date = run_sql("""SELECT date_released
                                    FROM jrnISSUE
                                   WHERE issue_number=%s
                                     AND id_jrnJOURNAL=%s""",
                               (issue, journal_id))[0][0]
    except:
        return None
    if release_date:
        return release_date
    else:
        return None

def get_announcement_datetime(issue, journal_name, ln=CFG_SITE_LANG):
    """
    Get the date at which an issue was announced through the alert system.
    Return None if not announced
    """
    journal_id = get_journal_id(journal_name, ln)
    try:
        announce_date = run_sql("""SELECT date_announced
                                     FROM jrnISSUE
                                    WHERE issue_number=%s
                                      AND id_jrnJOURNAL=%s""",
                            (issue, journal_id))[0][0]
    except:
        return None
    if announce_date:
        return announce_date
    else:
        return None

def datetime_to_issue(issue_datetime, journal_name):
    """
    Returns the issue corresponding to the given datetime object.

    If issue_datetime is too far in the future or in the past, gives
    the best possible matching issue, or None, if it does not seem to
    exist.

    #If issue_datetime is too far in the future, return the latest
    #released issue.
    #If issue_datetime is too far in the past, return None

    Parameters:

      issue_datetime - *datetime* date of the issue to be retrieved

        journal_name - *str* the name of the journal (as used in URLs)
    """
    issue_number = None
    journal_id = get_journal_id(journal_name)

    # Try to discover how much days an issue is valid
    nb_issues_per_year = get_journal_nb_issues_per_year(journal_name)
    this_year_number_of_days = 365
    if calendar.isleap(issue_datetime.year):
        this_year_number_of_days = 366

    issue_day_lifetime = math.ceil(float(this_year_number_of_days)/nb_issues_per_year)

    res = run_sql("""SELECT issue_number, date_released
                       FROM jrnISSUE
                      WHERE date_released < %s
                        AND id_jrnJOURNAL = %s
                   ORDER BY date_released DESC LIMIT 1""",
                  (issue_datetime, journal_id))
    if res and res[0][1]:
        issue_number = res[0][0]
        issue_release_date = res[0][1]

        # Check that the result is not too far in the future:
        if issue_release_date + datetime.timedelta(issue_day_lifetime) < issue_datetime:
            # In principle, the latest issue will no longer be valid
            # at that time
            return None
    else:
        # Mmh, are we too far in the past? This can happen in the case
        # of articles that have been imported in the system but never
        # considered as 'released' in the database. So we should still
        # try to approximate/match an issue:
        if round(issue_day_lifetime) in [6, 7, 8]:
            # Weekly issues. We can use this information to better
            # match the issue number
            issue_nb = int(issue_datetime.strftime('%W')) # = week number
        else:
            # Compute the number of days since beginning of year, and
            # divide by the lifetime of an issue: we get the
            # approximate issue_number
            issue_nb = math.ceil((int(issue_datetime.strftime('%j')) / issue_day_lifetime))
        issue_number = ("%0" + str(len(str(nb_issues_per_year)))+ "i/%i") % (issue_nb, issue_datetime.year)
        # Now check if this issue exists in the system for this
        # journal
        if not get_journal_categories(journal_name, issue_number):
            # This issue did not exist
            return None

    return issue_number

DAILY   = 1
WEEKLY  = 2
MONTHLY = 3

def issue_to_datetime(issue_number, journal_name, granularity=None):
    """
    Returns the *theoretical* date of release for given issue: useful
    if you release on Friday, but the issue date of the journal
    should correspond to the next Monday.

    This will correspond to the next day/week/month, depending on the
    number of issues per year (or the 'granularity' if specified) and
    the release time (if close to the end of a period defined by the
    granularity, consider next period since release is made a bit in
    advance).

    See get_release_datetime() for the *real* release time of an issue

    THIS FUNCTION SHOULD ONLY BE USED FOR INFORMATIVE DISPLAY PURPOSE,
    AS IT GIVES APPROXIMATIVE RESULTS. Do not use it to make decisions.

    Parameters:

      issue_number - *str* issue number to consider

      journal_name - *str* the name of the journal (as used in URLs)

      granularity  - *int* the granularity to consider
    """
    # If we have released, we can use this information. Otherwise we
    # have to approximate.
    issue_date = get_release_datetime(issue_number, journal_name)
    if not issue_date:
        # Approximate release date
        number, year = issue_number.split('/')
        number = int(number)
        year = int(year)
        nb_issues_per_year = get_journal_nb_issues_per_year(journal_name)
        this_year_number_of_days = 365
        if calendar.isleap(year):
            this_year_number_of_days = 366
        issue_day_lifetime = float(this_year_number_of_days)/nb_issues_per_year
        # Compute from beginning of the year
        issue_date = datetime.datetime(year, 1, 1) + \
                     datetime.timedelta(days=int(round((number - 1) * issue_day_lifetime)))
        # Okay, but if last release is not too far in the past, better
        # compute from the release.
        current_issue = get_current_issue(CFG_SITE_LANG, journal_name)
        current_issue_time = get_release_datetime(current_issue, journal_name)
        if current_issue_time.year == issue_date.year:
            current_issue_number, current_issue_year = current_issue.split('/')
            current_issue_number = int(current_issue_number)
            # Compute from last release
            issue_date = current_issue_time + \
                               datetime.timedelta(days=int((number - current_issue_number) * issue_day_lifetime))

    # If granularity is not specifed, deduce from config
    if granularity is None:
        nb_issues_per_year = get_journal_nb_issues_per_year(journal_name)
        if nb_issues_per_year > 250:
            granularity = DAILY
        elif nb_issues_per_year > 40:
            granularity = WEEKLY
        else:
            granularity = MONTHLY

    # Now we can adapt the date to match the granularity
    if granularity == DAILY:
        if issue_date.hour >= 15:
            # If released after 3pm, consider it is the issue of the next
            # day
            issue_date = issue_date + datetime.timedelta(days=1)
    elif granularity == WEEKLY:
        (year, week_nb, day_nb) = issue_date.isocalendar()
        if day_nb > 4:
            # If released on Fri, Sat or Sun, consider that it is next
            # week's issue.
            issue_date = issue_date + datetime.timedelta(weeks=1)
        # Get first day of the week
        issue_date = issue_date - datetime.timedelta(days=issue_date.weekday())
    else:
        if issue_date.day > 22:
            # If released last week of the month, consider release for
            # next month
            issue_date = issue_date.replace(month=issue_date.month+1)
        date_string = issue_date.strftime("%Y %m 1")
        issue_date = datetime.datetime(*(time.strptime(date_string, "%Y %m %d")[0:6]))

    return issue_date

def get_number_of_articles_for_issue(issue, journal_name, ln=CFG_SITE_LANG):
    """
    Function that returns a dictionary with all categories and number of
    articles in each category.
    """
    all_articles = {}
    categories = get_journal_categories(journal_name, issue)
    for category in categories:
        all_articles[category] = len(get_journal_articles(journal_name, issue, category))

    return all_articles

########################## JOURNAL RELATED ###########################

def get_journal_info_path(journal_name):
    """
    Returns the path to the info file of the given journal. The info
    file should be used to get information about a journal when database
    is not available.

    Returns None if path cannot be determined
    """
    # We must make sure we don't try to read outside of webjournal
    # cache dir
    info_path = os.path.abspath("%s/webjournal/%s/info.dat" % \
                                 (CFG_CACHEDIR, journal_name))
    if info_path.startswith(CFG_CACHEDIR + '/webjournal/'):
        return info_path
    else:
        return None

def get_journal_article_cache_path(journal_name, issue):
    """
    Returns the path to cache file of the articles of a given issue

    Returns None if path cannot be determined
    """
    # We must make sure we don't try to read outside of webjournal
    # cache dir
    cache_path = os.path.abspath("%s/webjournal/%s/%s_articles_cache.dat" % \
                                  (CFG_CACHEDIR, journal_name,
                                   issue.replace('/', '_')))
    if cache_path.startswith(CFG_CACHEDIR + '/webjournal/'):
        return cache_path
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

def guess_journal_name(ln, journal_name=None):
    """
    Tries to take a guess what a user was looking for on the server if
    not providing a name for the journal, or if given journal name
    does not match case of original journal.
    """
    from invenio.webjournal_config import InvenioWebJournalNoJournalOnServerError
    from invenio.webjournal_config import InvenioWebJournalNoNameError

    journals_id_and_names = get_journals_ids_and_names()
    if len(journals_id_and_names) == 0:
        raise InvenioWebJournalNoJournalOnServerError(ln)

    elif not journal_name and \
             journals_id_and_names[0].has_key('journal_name'):
        return journals_id_and_names[0]['journal_name']

    elif len(journals_id_and_names) > 0:
        possible_journal_names = [journal_id_and_name['journal_name'] for journal_id_and_name \
                                  in journals_id_and_names \
                                  if journal_id_and_name.get('journal_name', '').lower() == journal_name.lower()]
        if possible_journal_names:
            return possible_journal_names[0]
        else:
            raise InvenioWebJournalNoNameError(ln)

    else:
        raise InvenioWebJournalNoNameError(ln)

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

def parse_url_string(uri):
    """
    Centralized function to parse any url string given in
    webjournal. Useful to retrieve current category, journal,
    etc. from within format elements

    The webjournal interface handler should already have cleaned the
    URI beforehand, so that journal name exist, issue number is
    correct, etc.  The only remaining problem might be due to the
    capitalization of journal name in contact, search and popup pages,
    so clean the journal name

    returns:
        args: all arguments in dict form
    """
    args = {'journal_name'  : '',
            'issue_year'    : '',
            'issue_number'  : None,
            'issue'         : None,
            'category'      : '',
            'recid'         : -1,
            'verbose'       : 0,
            'ln'            : CFG_SITE_LANG,
            'archive_year'  : None,
            'archive_search': ''}

    if not uri.startswith('/journal'):
        # Mmh, incorrect context. Still, keep language if available
        url_params = urlparse(uri)[4]
        args['ln'] = dict([part.split('=') for part in url_params.split('&') \
                           if len(part.split('=')) == 2]).get('ln', CFG_SITE_LANG)
        return args

    # Take everything after journal and before first question mark
    splitted_uri = uri.split('journal', 1)
    second_part = splitted_uri[1]
    splitted_uri = second_part.split('?')
    uri_middle_part = splitted_uri[0]
    uri_arguments = ''
    if len(splitted_uri) > 1:
        uri_arguments = splitted_uri[1]

    arg_list = uri_arguments.split("&")
    args['ln'] = CFG_SITE_LANG
    args['verbose'] = 0
    for arg_pair in arg_list:
        arg_and_value = arg_pair.split('=')
        if len(arg_and_value) == 2:
            if arg_and_value[0] == 'ln':
                args['ln'] = arg_and_value[1]
            elif arg_and_value[0] == 'verbose' and \
                     arg_and_value[1].isdigit():
                args['verbose'] = int(arg_and_value[1])
            elif arg_and_value[0] == 'archive_year' and \
                     arg_and_value[1].isdigit():
                args['archive_year'] = int(arg_and_value[1])
            elif arg_and_value[0] == 'archive_search':
                args['archive_search'] = arg_and_value[1]
            elif arg_and_value[0] == 'name':
                args['journal_name'] = guess_journal_name(args['ln'],
                                                          arg_and_value[1])

    arg_list = uri_middle_part.split("/")
    if len(arg_list) > 1 and arg_list[1] not in ['search', 'contact', 'popup']:
        args['journal_name'] = urllib.unquote(arg_list[1])
    elif arg_list[1] not in ['search', 'contact', 'popup']:
        args['journal_name'] = guess_journal_name(args['ln'],
                                                  args['journal_name'])

    cur_issue = get_current_issue(args['ln'], args['journal_name'])
    if len(arg_list) > 2:
        try:
            args['issue_year'] = int(urllib.unquote(arg_list[2]))
        except:
            args['issue_year'] = int(cur_issue.split('/')[1])
    else:
        args['issue'] = cur_issue
        args['issue_year'] = int(cur_issue.split('/')[1])
        args['issue_number'] = int(cur_issue.split('/')[0])

    if len(arg_list) > 3:
        try:
            args['issue_number'] = int(urllib.unquote(arg_list[3]))
        except:
            args['issue_number'] = int(cur_issue.split('/')[0])
        args['issue'] = make_issue_number(args['journal_name'],
                                          args['issue_number'],
                                          args['issue_year'])

    if len(arg_list) > 4:
        args['category'] = urllib.unquote(arg_list[4])
    if len(arg_list) > 5:
        try:
            args['recid'] = int(urllib.unquote(arg_list[5]))
        except:
            pass

    args['ln'] = get_journal_preferred_language(args['journal_name'],
                                                args['ln'])

    # FIXME : wash arguments?
    return args

def make_journal_url(current_uri, custom_parameters=None):
    """
    Create a URL, using the current URI and overriding values
    with the given custom_parameters

    Parameters:
             current_uri - *str* the current full URI

       custom_parameters - *dict* a dictionary of parameters that
                           should override those of curent_uri
    """
    if not custom_parameters:
        custom_parameters = {}

    default_params = parse_url_string(current_uri)
    for key, value in custom_parameters.iteritems():
        # Override default params with custom params
        default_params[key] = str(value)

    uri = CFG_SITE_URL + '/journal/'
    if default_params['journal_name']:
        uri += urllib.quote(default_params['journal_name']) + '/'
        if default_params['issue_year'] and default_params['issue_number']:
            uri += make_issue_number(default_params['journal_name'],
                                     default_params['issue_number'],
                                     default_params['issue_year'],
                                     for_url_p=True) + '/'
            if default_params['category']:
                uri += urllib.quote(default_params['category'])
                if default_params['recid'] and \
                       default_params['recid'] != -1:
                    uri += '/' + str(default_params['recid'])

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

############################ HTML CACHING FUNCTIONS ############################

def cache_index_page(html, journal_name, category, issue, ln):
    """
    Caches the index page main area of a Bulletin
    (right hand menu cannot be cached)
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")

    cache_path = os.path.abspath('%s/webjournal/%s/%s_index_%s_%s.html' % \
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

    cache_path = os.path.abspath('%s/webjournal/%s/%s_index_%s_%s.html' % \
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
    cache_path = os.path.abspath('%s/webjournal/%s/%s_article_%s_%s_%s.html' % \
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

    cache_path = os.path.abspath('%s/webjournal/%s/%s_article_%s_%s_%s.html' % \
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
    Resets the cache for an article (e.g. after an article has been
    modified)
    """
    issue = issue.replace("/", "_")
    category = category.replace(" ", "")

    cache_path = os.path.abspath('%s/webjournal/%s/' %
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

    try:
        path = get_journal_article_cache_path(journal_name, issue)
        os.remove(path)
    except:
        pass

    return True

def clear_cache_for_issue(journal_name, issue):
    """
    clears the cache of a whole issue.
    """
    issue = issue.replace("/", "_")
    cache_path_dir = os.path.abspath('%s/webjournal/%s' % \
                                      (CFG_CACHEDIR, journal_name))
    if not cache_path_dir.startswith(CFG_CACHEDIR + '/webjournal'):
        # Mmh, not accessing correct path. Stop deleting cache
        return False

    all_cached_files = os.listdir(cache_path_dir)
    non_deleted = []
    for cached_file in all_cached_files:
        if cached_file.startswith(issue.replace('/', '_')):
            try:
                os.remove(cache_path_dir + '/' + cached_file)
            except:
                return False
        else:
            non_deleted.append(cached_file)

    return True


######################### CERN SPECIFIC FUNCTIONS #################

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
                 issue_number in subfield.get('n', '')]

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
        if positive_index_records.has_key(number):
            recid_to_return = positive_index_records[number]

    return recid_to_return

def is_recid_in_released_issue(recid):
    """
    Returns True if recid is part of the latest issue of the given
    journal.

    WARNING: the function does not check that the article does not
    belong to the draft collection of the record. This is wanted, in
    order to workaround the time needed for a record to go from the
    draft collection to the final collection
    """
    bfo = BibFormatObject(recid)
    journal_name = ''
    journal_names = [journal_name for journal_name in bfo.fields('773__t') if journal_name]
    if journal_names:
        journal_name = journal_names[0]
    else:
        return False

    existing_journal_names = [o['journal_name'] for o in get_journals_ids_and_names()]
    if not journal_name in existing_journal_names:
        # Try to remove whitespace
        journal_name = journal_name.replace(' ', '')
        if not journal_name in existing_journal_names:
            # Journal name unknown from WebJournal
            return False

    config_strings = get_xml_from_config(["draft_image_access_policy"], journal_name)
    if config_strings['draft_image_access_policy'] and \
       config_strings['draft_image_access_policy'][0] != 'allow':
        # The journal does not want to optimize access to images
        return False

    article_issues = bfo.fields('773__n')
    current_issue = get_current_issue(CFG_SITE_LANG, journal_name)
    for article_issue in article_issues:
        # Check each issue until a released one is found
        if get_release_datetime(article_issue, journal_name):
            # Release date exists, issue has been released
            return True
        else:
            # Unreleased issue. Do we still allow based on journal config?
            unreleased_issues_mode = get_unreleased_issue_hiding_mode(journal_name)
            if (unreleased_issues_mode == 'none' or \
                (unreleased_issues_mode == 'future' and \
                 not issue_is_later_than(article_issue, current_issue))):
                return True

    return False
