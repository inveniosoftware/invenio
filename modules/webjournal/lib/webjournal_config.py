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

from invenio.config import adminemail, supportemail, etcdir, weburl, cdslang
from invenio.messages import gettext_set_language
from invenio.webpage import page
from invenio.webjournal_utils import parse_url_string
import os

class InvenioWebJournalNoIndexTemplateError(Exception):
    """Exception if no index template is specified in the config."""
    def __init__(self, journal_name):
        """Initialisation."""
        self.journal = journal_name
    def __str__(self):
        """String representation."""
        return 'Admin did not provide a template for the index page of journal: %s. \
        The path to such a file should be given in the config.xml of this journal \
        under the tag <format_template><index>...</index></format_template>' % repr(self.journal)
    
class InvenioWebJournalNoArticleRuleError(Exception):
    """
    Exception if there are no article type rules defined.
    """
    def __init__(self, journal_name):
        """
        Initialisation.
        """
        self.journal = journal_name
    def __str__(self):
        """
        String representation.
        """
        return 'The config.xml file for journal: %s does not contain any article \
        rules. These rules are needed to associate collections from your Invenio \
        installation to navigable article types. A rule should have the form of \
        <rule>NameOfArticleType, marc_tag:ExpectedContentOfMarcTag' % repr(self.journal)
    
class InvenioWebJournalNoIssueNumberTagError(Exception):
    """
    Exception if there is no marc tag for issue number defined.
    """
    def __init__(self, journal_name):
        """
        Initialisation.
        """
        self.journal = journal_name
    def __str__(self):
        """
        String representation.
        """
        return 'The config.xml file for journal: %s does not contain a marc tag \
        to deduce the issue number from. WebJournal is an issue number based \
        system, meaning you have to give some form of numbering system in a \
        dedicated marc tag, so the system can see which is the active journal \
        publication of the date.' % repr(self.journal)
    
class InvenioWebJournalNoArticleNumberError(Exception):
    """
    Exception if an article was called without its order number.
    """
    def __init__(self, journal_name):
        """
        Initialisation.
        """
        self.journal = journal_name
        
    def __str__(self):
        """
        String representation.
        """
        return 'In Journal %s an article was called without specifying the order \
        of this article in the issue. This parameter is mandatory and should be \
        provided by internal links in any case. Maybe this was a bad direct url \
        hack. Check where the request came from.' % repr(self.journal)
    
class InvenioWebJournalNoArticleTemplateError(Exception):
    """
    Exception if an article was called without its order number.
    """
    def __init__(self, journal_name):
        """
        Initialisation.
        """
        self.journal = journal_name
        
    def __str__(self):
        """
        String representation.
        """
        return 'Admin did not provide a template for the article view page of journal: %s. \
        The path to such a file should be given in the config.xml of this journal \
        under the tag <format_template><detailed>...</detailed></format_template>' % repr(self.journal)

def webjournal_missing_info_box(req, title, msg_title, msg):
    """
    returns a box indicating that the given journal was not found on the
    server, leaving the opportunity to select an existing journal from a list.
    """
    params = parse_url_string(req)
    try:
        language = params["ln"]
    except:
        language = cdslang
    _ = gettext_set_language(language)
    title = _(title)
    box_title = _(msg_title)
    box_text = _(msg)
    box_list_title = _("Available Journals")
    find_journals = lambda path: [entry for entry in os.listdir(str(path)) if os.path.isdir(str(path)+str(entry))]
    try:
        all_journals = find_journals('%s/webjournal/' % etcdir)
    except:
        all_journals = []
    box = '''<div style="text-align: center;">
                <fieldset style="width:400px; margin-left: auto; margin-right: auto;background: url('%s/img/blue_gradient.gif') top left repeat-x;">
                    <legend style="color:#a70509;background-color:#fff;"><i>%s</i></legend>
                    <p style="text-align:center;">%s</p>
                    <h2 style="color:#0D2B88;">%s</h2>
                    <ul class="webjournalBoxList">
                        %s
                    </ul>
                    <br/>
                    <div style="text-align:right;">Mail<a href="mailto:%s"> the Administrator.</a></div>
                </fieldset>
            </div>
            ''' % (weburl,
                   box_title,
                   box_text,
                   box_list_title,
                   "".join(['<li><a href="%s/journal/?name=%s">%s</a></li>' % (weburl, journal, journal) for journal in all_journals]),
                   adminemail)
    return page(title=title, body=box)

def webjournal_error_box(req, title, title_msg, msg):
    """
    """
    params = parse_url_string(req)
    try:
        language = params["ln"]
    except:
        language = cdslang
    _ = gettext_set_language(language)
    title = _(title)
    title_msg = _(title_msg)
    msg = _(msg)
    box = '''<div style="text-align: center;">
                <fieldset style="width:400px; margin-left: auto; margin-right: auto;background: url('%s/img/red_gradient.gif') top left repeat-x;">
                    <legend style="color:#a70509;background-color:#fff;"><i>%s</i></legend>
                    <p style="text-align:center;">%s</p>
                    <br/>
                    <div style="text-align:right;">Mail<a href="mailto:%s"> the Developers.</a></div>
                </fieldset>
            </div>
            ''' % (weburl, title_msg, msg, supportemail)
    return page(title=title, body=box)
    
