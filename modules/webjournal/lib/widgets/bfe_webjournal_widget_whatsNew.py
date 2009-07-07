# -*- coding: utf-8 -*-
## $Id: bfe_webjournal_widget_whatsNew.py,v 1.19 2008/01/18 11:12:20 ghase Exp $
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
import time
import os

from invenio.errorlib import register_exception
from invenio.search_engine import search_pattern, perform_request_search
from invenio.bibformat_engine import BibFormatObject
from invenio.config import weburl, cachedir

from invenio.webjournal_utils import get_xml_from_config, \
                                parse_url_string, \
                                get_current_issue, \
                                get_order_dict_from_recid_list_CERNBulletin, \
                                pop_newest_article_CERNBulletin
from invenio.webjournal_config import InvenioWebJournalNoArticleRuleError
    
def _get_breaking_news(lang, journal_name):
    """
    Gets the Breaking News articles that are currently active according to
    start and end dates.
    """
    # first look for breaking news that are active
    breaking_news_recids = list(search_pattern(p='980__a:BULLETINBREAKING',
                                               f="&action_search=Search"))
    today = time.mktime(time.localtime())
    breaking_news = '<li>'
    for recid in breaking_news_recids:
        temp_rec = BibFormatObject(recid)
        try:
            internal_notes = temp_rec.fields('595__a')
            if 'Open Day' in internal_notes:
                openday = True
            else:
                openday = False
        except:
            openday = False
        try:
            end_date = time.mktime(time.strptime(temp_rec.field("925__b"),
                                                 "%m/%d/%Y"))
        except:
            end_date = time.mktime(time.strptime("01/01/1970", "%m/%d/%Y"))
        if end_date < today:
            continue
        try:
            start_date = time.mktime(time.strptime(temp_rec.field("925__a"),
                                                   "%m/%d/%Y"))
        except:
            start_date = time.mktime(time.strptime("01/01/2050", "%m/%d/%Y"))
        if start_date > today:
            continue
        publish_date = temp_rec.field("269__c")
        if lang == 'fr':
            title = temp_rec.field("246_1a")
        else:
            title = temp_rec.field("245__a")
        breaking_news += '''
<h2 class="%s">%s<br/>
    <strong>
        <a href="%s/journal/popup?name=%s&type=breaking_news&record=%s&ln=%s" target="_blank">%s</a>
    </strong>
</h2>
''' % ((openday==True) and "openday" or "",
    publish_date, weburl, journal_name, recid, lang, title)
    breaking_news += '</li>'
    
    return breaking_news.decode('utf-8')

def _get_whatsNew_from_cache(journal_name, ln):
    """
    Trys to get the whats new box from cache.
    """
    try:
        last_update = os.path.getctime('%s/webjournal/%s_whatsNew_%s.html' % (cachedir,
                                                             journal_name,
                                                             ln))
    except:
        return False

    now = time.time()
    if (last_update + 30*60) < now: # inavlidate after 30 minutes
        return False
    
    try:
        cached_file = open('%s/webjournal/%s_whatsNew_%s.html' % (cachedir,
                                                               journal_name,
                                                               ln)).read()
    except:
        return False
    return cached_file
    
def cache_whatsNew(html, journal_name, ln):
    """
    caches the whats new box for 30 minutes.
    """
    cache_file = open('%s/webjournal/%s_whatsNew_%s.html' % (cachedir,
                                             journal_name,
                                             ln), "w")
    cache_file.write(html)
    cache_file.close()

def format(bfo):
    """
    creates the whats new box from breaking news articles and new submissions
    in the respective categories.
    """
    journal_name = bfo.req.journal_defaults["name"]
    issue_number = bfo.req.journal_defaults["issue"]
    # try to get HTML from cache
    cached_html = _get_whatsNew_from_cache(journal_name, bfo.lang)
    if cached_html:
        return cached_html
    config_strings = get_xml_from_config(["rule"], journal_name)
    rule_list = config_strings["rule"]
    try:
        if len(rule_list) == 0:
            raise InvenioWebJournalNoArticleRuleError() 
    except InvenioWebJournalNoArticleRuleError, e:     
        register_exception(req=req)
        return e.user_box()
    whats_new_articles = {}
    for rule in rule_list:
        category_name = rule.split(",")[0]
        whats_new_articles[category_name] = {}
        rule_part = rule.split(",")[1].replace(" ", "")
        marc_tag = rule_part.split(":")[0]
        marc_name = rule_part.split(":")[1]
        # todo: check for issue number
        if issue_number[0] == '0':
            alternative_issue_number = issue_number[1:]    
            menu_recids = list(search_pattern(p="%s:%s and 773__n:%s" %
                                                     (marc_tag,
                                                      marc_name,
                                                      issue_number),
                                                     f="&action_search=Search"))
            alternative_menu_recids = list(search_pattern(p="%s:%s and 773__n:%s" %
                                                     (marc_tag,
                                                      marc_name,
                                                      alternative_issue_number),
                                                     f="&action_search=Search"))
            if len(menu_recids) > 0:
                ordered_articles = get_order_dict_from_recid_list_CERNBulletin(menu_recids,
                                                                    issue_number)
            else:
                ordered_articles = get_order_dict_from_recid_list_CERNBulletin(alternative_menu_recids,
                                                                    alternative_issue_number)
        else:
            menu_recids = list(search_pattern(p="%s:%s and 773__n:%s" %
                                                     (marc_tag,
                                                      marc_name,
                                                      issue_number),
                                                     f="&action_search=Search"))
            ordered_articles = get_order_dict_from_recid_list_CERNBulletin(menu_recids,
                                                                    issue_number)
        
        try:
            if len(ordered_articles[1]) > 1:
                while len(ordered_articles[1]) > 1:
                    index = 2 - len(ordered_articles[1])
                    key = pop_newest_article_CERNBulletin(ordered_articles[1])
                    whats_new_articles[category_name][index] = ordered_articles[1].pop(key)[0]
        except:
            pass
    
    html_out = u''
    html_out += _get_breaking_news(bfo.lang, journal_name)
    
    for category in whats_new_articles.keys():
        if len(whats_new_articles[category].keys()) > 0:
            html_out += '''<li><h3>
            <a href="%s/journal/?name=%s&category=%s&ln=%s">%s</a>
            </h3><ul class="whatsNew">''' % (weburl, journal_name,
                                            category, bfo.lang, category)
            for article_index in whats_new_articles[category].keys():
                index = article_index
                recid = whats_new_articles[category][index]
                link = '%s/journal/article?name=%s&issue=%s&category=%s&number=%s&ln=%s' % (weburl,
                                                                                            journal_name,
                                                                                            issue_number,
                                                                                            category,
                                                                                            index,
                                                                                            bfo.lang)
                temp_rec = BibFormatObject(recid)
                if bfo.lang == 'fr':
                    try:
                        title = temp_rec.fields('246_1a')[0]
                    except:
                        continue
                else:
                    try:
                        title = temp_rec.field('245__a')
                    except:
                        continue
                try:
                    html_out += u'<li><a href="%s">%s</a></li>' % (link,
                                                        title.decode('utf-8'))
                except:
                    pass
            html_out += '</ul></li>'
            
    if html_out == "":
        html_out = '<i>there are no new articles at this moment</i>'
        
    cache_whatsNew(html_out.encode('utf-8'), journal_name, bfo.lang)
    return html_out.encode('utf-8')
            
def escape_values(bfo):
    """
    """
    return 0 
        
if __name__ == "__main__":
    from invenio.bibformat_engine import BibFormatObject
    myrec = BibFormatObject(52)
    format(myrec)
