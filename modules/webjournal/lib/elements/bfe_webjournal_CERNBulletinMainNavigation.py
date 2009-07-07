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
from xml.dom import minidom

from invenio.bibformat_engine import BibFormatObject
from invenio.config import etcdir, weburl
from invenio.errorlib import register_exception

from invenio.webjournal_utils import parse_url_string, get_xml_from_config
from invenio.webjournal_config import InvenioWebJournalNoArticleRuleError
# todo: put in msg file
french_menu = {"News Articles": "Actualités",
               "Official News": "Communications officielles",
               "Training and Development": "Formation et développement",
               "General Information": "Informations générales"}

def format(bfo):
    """
    Creates the Main Navigation for the CERN Bulletin.
    """
    journal_name = bfo.req.journal_defaults["name"]
    issue_number = bfo.req.journal_defaults["issue"]
    try:
        category = bfo.req.journal_defaults["category"]
    except:
        category = ""
    category = category.replace("%20", " ")
    # get and open the config file
    config_strings = get_xml_from_config(["rule",], journal_name)
    nav_entry_list = config_strings["rule"]
    try:
        if len(nav_entry_list) == 0:
            raise InvenioWebJournalNoArticleRuleError(language, journal_name) 
    except InvenioWebJournalNoArticleRuleError, e:     
        register_exception(req=req)
        return e.user_box()
    navigation = '<div id="mainmenu">'
    i = 0
    for entry in nav_entry_list:
        category_link = entry.split(",")[0]
        category_name = category_link
        if bfo.lang == "fr":
            try:
                category_name = french_menu[category_name]
            except KeyError:
                pass
        if category.lower() == category_link.lower():
            try:
                navigation += '''<span class="mainactive">
    <img width="4" height="12" src="%s/img/webjournal_CERNBulletin/Objects/Common/ListIcon-%s.gif"/>
    <a href="%s/%s">%s</a></span>''' % (weburl, bfo.lang, weburl,
'journal/?name=' + journal_name + '&issue=' + issue_number + '&category=' + category_link + '&ln=' + bfo.lang,                                                                                                                                         
category_name)
            except:
                continue
                #return "ERROR on parsing %s" % category_link
        else:
            try:
                navigation += '''
<span>
<img width="4" height="12" src="%s/img/webjournal_CERNBulletin/Objects/Common/ListIcon-%s.gif"/>
<a href="%s/%s">%s</a></span>''' % (weburl,bfo.lang,weburl,
'journal/?name=' + journal_name + '&issue=' + issue_number + '&category=' + category_link + '&ln=' + bfo.lang,
category_name)                                                                                                                                                       
            except:
                continue
                #return "ERROR on parsing %s" % category_name
        i+=1
    navigation += '</div>'
    return navigation


def escape_values(bfo):
    """
    """
    return 0

if __name__ == "__main__":
    myrec = BibFormatObject(7)
    myrec.journal_defaults= {}
    myrec.journal_defaults["name"] = "CERNBulletin"
    myrec.journal_defaults["issue"] = "22/2007"
    format(myrec)
