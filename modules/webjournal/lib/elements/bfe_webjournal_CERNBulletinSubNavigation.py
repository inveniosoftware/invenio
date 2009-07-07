# -*- coding: utf-8 -*-
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
from invenio.search_engine import search_pattern
from invenio.bibformat_engine import BibFormatObject
from invenio.config import weburl

from invenio.webjournal_utils import get_order_dict_from_recid_list, \
                                get_order_dict_from_recid_list_CERNBulletin, \
                                pop_newest_article_CERNBulletin
from invenio.webjournal_utils import parse_url_string

def format(bfo):
    """
    Creates a navigation for articles in the same issue and category.
    """
    # get variables
    try:
        args = parse_url_string(bfo.req)
        this_recid = bfo.control_field('001')
        this_journal_name = bfo.req.journal_defaults["name"]
        this_issue_number = bfo.req.journal_defaults["issue"]
        category_name = bfo.req.journal_defaults["category"]
        this_title = ""
        if bfo.lang == "fr":
            try:
                this_title = bfo.fields('246_1a')[0]
            except KeyError:
                return ""
        else:
            try:
                this_title = bfo.fields('245__a')[0]
            except KeyError:
                return ""
        if this_issue_number[0] == '0':
            alternative_issue_number = this_issue_number[1:]
            menu_recids = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                                         (category_name,
                                                          this_issue_number),
                                                         f="&action_search=Search"))
            alternative_menu_recids = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                                         (category_name,
                                                          alternative_issue_number),
                                                         f="&action_search=Search"))
            if len(menu_recids) > 0:
                ordered_articles = get_order_dict_from_recid_list_CERNBulletin(menu_recids,
                                                                this_issue_number)
            else:
                ordered_articles = get_order_dict_from_recid_list_CERNBulletin(alternative_menu_recids,
                                                                alternative_issue_number)
        else:   
            menu_recids = list(search_pattern(p='65017a:"%s" and 773__n:%s' %
                                                         (category_name,
                                                          this_issue_number),
                                                         f="&action_search=Search"))
            ordered_articles = get_order_dict_from_recid_list_CERNBulletin(menu_recids,
                                                                this_issue_number)
        menu_out = ''
        if len(ordered_articles.keys()) > 0:
            number_of_articles = len(ordered_articles.keys()) + len(
                ordered_articles[1].keys()) -1
            ordered_articles_indexes = ordered_articles.keys()
            ordered_articles_indexes.sort()
        else:
            number_of_articles = 0
            ordered_articles_indexes = []
        i = 0
        while i < number_of_articles:
            flag = False
            number = str(ordered_articles_indexes[i])
            try:
                temp_recid_dict = ordered_articles[ordered_articles_indexes[i]]
                if len(temp_recid_dict.keys()) > 1:
                    i = -1 # cycle through 2nd level in 1
                    number_of_articles = number_of_articles -1
                    number = 2-len(temp_recid_dict.keys())
                    # go in the other direction of 1 -> 0, -1, -2, etc.
                    key = pop_newest_article_CERNBulletin(temp_recid_dict)
                    temp_news_tuple = temp_recid_dict.pop(int(key))
                    temp_recid = temp_news_tuple[0]
                    flag = temp_news_tuple[1]
                else:
                    temp_news_tuple = temp_recid_dict.popitem()
                    temp_recid = temp_news_tuple[1][0]
            except:
                continue
            if str(this_recid) == str(temp_recid):
                menu_out += '''<div class="active">
                <div class="litem%s">%s</div></div>''' % (flag and " new" or "",
                                                        this_title)
            else:
                temp_rec = BibFormatObject(temp_recid)
                if bfo.lang == "fr":
                    try:
                        title = temp_rec.fields('246_1a')[0]
                    except:
                        i+=1
                        continue
                else:
                    title = temp_rec.fields('245__a')[0]
                menu_out += '''<div class="litem%s">
                <a href="%s/journal/article?%s">%s</a></div>
                ''' % (flag and " new" or "", weburl,                                                                                        
    'issue=' + this_issue_number + '&name=' + this_journal_name + '&category=' + category_name + '&number=' + str(number) + '&ln=' + bfo.lang,
    title)
            i+=1
        # add rss link
        menu_out += '''
        <a href="http://cdsweb.cern.ch/search?cc=%s&of=xr" target="_blank"><small>subscribe by: </small>
            <img src="%s/img/webjournal_CERNBulletin/Objects/Common/rss.png" style="border: medium none ; padding-left: 10px;padding-top:40px;"/>
        </a>
        ''' % (category_name, weburl)
        return menu_out
    except Exception, e:
        pass
        #return "Error: %s" % e

def escape_values(bfo):
    """
    """
    return 0

if __name__ == "__main__":
    myrec = BibFormatObject(20)
    format(myrec)