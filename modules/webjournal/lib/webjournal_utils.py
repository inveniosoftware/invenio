# -*- coding: utf-8 -*-
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

from invenio.bibformat_engine import BibFormatObject
from invenio.errorlib import register_exception
from invenio.search_engine import search_pattern
from invenio.config import etcdir, weburl, adminemail
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.dbquery import run_sql
from xml.dom import minidom
from urllib2 import urlopen
import time
import re

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
    # get the id list
    all_records = list(search_pattern(p="%s and 773__n:%s" %
                                      (rule, issue_number),
                                      f="&action_search=Search"))
    ordered_records = {}
    new_addition_records = []
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
                    register_exception(stream="warning", verbose_description="There \
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
                register_exception(stream='warning', verbose_description="There \
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
    config_path = '%s/webjournal/%s/config.xml' % (etcdir, journal_name)     
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
                        in and be registered by your system administrator for \
                        this kind of task. If you have a login, use the link \
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

def get_current_issue(journal_name):
    """
    checks the flat files for issue numbers of this journal and returns
    the most recent issue number.
    """
    try:
        current_issue = open('%s/webjournal/%s/current_issue' % (etcdir,
                                                                 journal_name)).read()
    except:
        #todo: Error, no current issue number, returning this week
        return '%s/%s' (time.strptime("%U/%Y", time.localtime()))
    issue_number = current_issue.split(" - ")[0].replace(" ", "")
    return issue_number

def cache_page():
    """
    """
    pass

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

def get_monday_of_the_week(week_number, year):
    """
    CERN Bulletin specific function that returns a string indicating the
    Monday of each week as: Monday <dd> <Month> <Year>
    """
    timetuple = time.strptime('1-%s-%s' % (week_number, year), "%w-%W-%Y")
    return time.strftime("%A %d %B %Y", timetuple)

def createhtmlmail (html, text, subject):
        """Create a mime-message that will render HTML in popular
           MUAs, text in better ones"""
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
    """
    config_strings = get_xml_from_config(["screen"], journal_name)
    try:
        css_path = config_strings["screen"][0]
    except:
        register_exception(req=req, suffix="No css file for journal %s. Is this right?" % journal_name)
        return
    # todo: error handling on not found    
    css_file = urlopen('%s/%s' % (weburl, css_path))
    css = css_file.read()
    css = make_full_paths_in_css(css, journal_name)
    html_parted = html_message.split("</head>")
    if len(html_parted) > 1:
        html = '%s<style type="text/css">%s</style>%s' % (html_parted[0],
                                                        css,
                                                        html_parted[1])
    else:
        html_parted = html_message.split("<html>")
        if len(html_parted) > 1:
            html = '%s<html><head><style type="text/css">%s</style></head>%s' % (html_parted[0],
                                                                                 css,
                                                                                 html_parted[1])
        else:
            return "no html"
            # todo: exception
            
    
    return html

def make_full_paths_in_css(css, journal_name):
    """
    """
    url_pattern = re.compile('''url\(["']?\s*(?P<url>\S*)\s*["']?\)''', re.DOTALL)
    url_iter = url_pattern.finditer(css)
    rel_to_full_path = {}
    for url in url_iter:
        url_string = url.group("url")
        url_string = url_string.replace("\"", "")
        url_string = url_string.replace("\'", "")
        if url_string[:6] != "http://":
            rel_to_full_path[url_string] = '"%s/img/%s/%s"' % (weburl, journal_name, url_string)
    
    for url in rel_to_full_path.keys():
        css = css.replace(url, rel_to_full_path[url])
        
    return css



#url(["']?(?P<url>\S*)["']?)
