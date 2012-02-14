# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2011 CERN.
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

"""Bibauthorid HTML templates"""

# pylint: disable=W0105
# pylint: disable=C0301


#from cgi import escape
#from urllib import quote
#
import invenio.bibauthorid_config as bconfig
from invenio.config import CFG_SITE_LANG
from invenio.config import CFG_SITE_URL
from invenio.config import CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL
from invenio.bibformat import format_record
from invenio.session import get_session
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibauthorid_config import EXTERNAL_SYSTEMS_LIST
from invenio.bibauthorid_webapi import get_person_redirect_link, get_canonical_id_from_person_id, get_person_names_from_id
from invenio.bibauthorid_webapi import get_personiID_external_ids
from invenio.bibauthorid_frontinterface import get_uid_from_personid
from invenio.bibauthorid_frontinterface import get_bibrefrec_name_string
from invenio.bibauthorid_frontinterface import get_canonical_id_from_personid
from invenio.messages import gettext_set_language, wash_language
from invenio.webuser import get_email
from invenio.htmlutils import escape_html
#from invenio.textutils import encode_for_xml

import xml.sax.saxutils

class Template:
    """Templating functions used by aid"""

    def __init__(self, language=CFG_SITE_LANG):
        """Set defaults for all aid template output"""

        self.language = language
        self._ = gettext_set_language(wash_language(language))


    def tmpl_person_detail_layout(self, content):
        '''
        writes HTML content into the person css container

        @param content: HTML content
        @type content: string

        @return: HTML code
        @rtype: string
        '''
        html = []
        h = html.append
        h('<div id="aid_person">')
        h(content)
        h('</div>')

        return "\n".join(html)


    def tmpl_transaction_box(self, teaser_key, messages, show_close_btn=True):
        '''
        Creates a notification box based on the jQuery UI style

        @param teaser_key: key to a dict which returns the teaser
        @type teaser_key: string
        @param messages: list of keys to a dict which return the message to display in the box
        @type messages: list of strings
        @param show_close_btn: display close button [x]
        @type show_close_btn: boolean

        @return: HTML code
        @rtype: string
        '''
        transaction_teaser_dict = { 'success': 'Success!',
                                    'failure': 'Failure!' }
        transaction_message_dict = { 'confirm_success': '%s transaction%s successfully executed.',
                                     'confirm_failure': '%s transaction%s failed. The system may have been updating during your operation. Please try again or contact %s to obtain help.',
                                     'reject_success': '%s transaction%s successfully executed.',
                                     'reject_failure': '%s transaction%s failed. The system may have been updating during your operation. Please try again or contact %s to obtain help.',
                                     'reset_success': '%s transaction%s successfully executed.',
                                     'reset_failure': '%s transaction%s failed. The system may have been updating during your operation. Please try again or contact %s to obtain help.' }

        teaser = self._(transaction_teaser_dict[teaser_key])

        html = []
        h = html.append
        for key in transaction_message_dict.keys():
            same_kind = [mes for mes in messages if mes == key]
            trans_no = len(same_kind)
            if trans_no == 0:
                continue
            elif trans_no == 1:
                args = [trans_no, '']
            else:
                args = [trans_no, 's']

            color = ''
            if teaser_key == 'failure':
                color = 'background: #FC2626;'
                args.append(CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL)

            message = self._(transaction_message_dict[key] % tuple(args))

            h('<div id="aid_notification_' + key + '" class="ui-widget ui-alert">')
            h('  <div style="%s margin-top: 20px; padding: 0pt 0.7em;" class="ui-state-highlight ui-corner-all">' % (color))
            h('    <p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-info"></span>')
            h('    <strong>%s</strong> %s' % (teaser, message))

            if show_close_btn:
                h('    <span style="float:right; margin-right: 0.3em;"><a rel="nofollow" href="#" class="aid_close-notify" style="border-style: none;">X</a></span></p>')

            h(' </div>')
            h('</div>')

        return "\n".join(html)

    def tmpl_notification_box(self, teaser_key, message_key, bibrefs, show_close_btn=True):
        '''
        Creates a notification box based on the jQuery UI style

        @param teaser_key: key to a dict which returns the teaser
        @type teaser_key: string
        @param message_key: key to a dict which returns the message to display in the box
        @type message_key: string
        @param bibrefs: bibrefs which are about to be assigned
        @type bibrefs: list of strings
        @param show_close_btn: display close button [x]
        @type show_close_btn: boolean

        @return: HTML code
        @rtype: string
        '''
        notification_teaser_dict = {'info': 'Info!' }
        notification_message_dict = {'attribute_papers': 'You are about to attribute the following paper%s:' }

        teaser = self._(notification_teaser_dict[teaser_key])
        arg = ''
        if len(bibrefs) > 1:
            arg = 's'
        message = self._(notification_message_dict[message_key] % (arg) )

        html = []
        h = html.append

        h('<div id="aid_notification_' + teaser_key + '" class="ui-widget ui-alert">')
        h('  <div style="margin-top: 20px; padding: 0pt 0.7em;" class="ui-state-highlight ui-corner-all">')
        h('    <p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-info"></span>')
        h('    <strong>%s</strong> %s' % (teaser, message))
        h("<ul>")
        for paper in bibrefs:
            if ',' in paper:
                pbibrec = paper.split(',')[1]
            else:
                pbibrec = paper
            h("<li>%s</li>" % (format_record(int(pbibrec), "ha")))
        h("</ul>")

        if show_close_btn:
            h('    <span style="float:right; margin-right: 0.3em;"><a rel="nofollow" href="#" class="aid_close-notify">X</a></span></p>')

        h(' </div>')
        h('</div>')

        return "\n".join(html)


    def tmpl_error_box(self, teaser_key, message_key, show_close_btn=True):
        '''
        Creates an error box based on the jQuery UI style

        @param teaser_key: key to a dict which returns the teaser
        @type teaser_key: string
        @param message_key: key to a dict which returns the message to display in the box
        @type message_key: string
        @param show_close_btn: display close button [x]
        @type show_close_btn: boolean

        @return: HTML code
        @rtype: string
        '''
        error_teaser_dict = {'sorry': 'Sorry.',
                             'error': 'Error:' }
        error_message_dict = {'check_entries': 'Please check your entries.',
                              'provide_transaction': 'Please provide at least one transaction.' }

        teaser = self._(error_teaser_dict[teaser_key])
        message = self._(error_message_dict[message_key])

        html = []
        h = html.append

        h('<div id="aid_notification_' + teaser_key + '" class="ui-widget ui-alert">')
        h('  <div style="background: #FC2626; margin-top: 20px; padding: 0pt 0.7em;" class="ui-state-error ui-corner-all">')
        h('    <p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-alert"></span>')
        h('    <strong>%s</strong> %s' % (teaser, message))

        if show_close_btn:
            h('    <span style="float:right; margin-right: 0.3em;"><a rel="nofollow" href="#" class="aid_close-notify">X</a></span></p>')

        h(' </div>')
        h('</div>')

        return "\n".join(html)


    def tmpl_ticket_box(self, teaser_key, message_key, trans_no, show_close_btn=True):
        '''
        Creates a semi-permanent box informing about ticket
        status notifications

        @param teaser_key: key to a dict which returns the teaser
        @type teaser_key: string
        @param message_key: key to a dict which returns the message to display in the box
        @type message_key: string
        @param trans_no: number of transactions in progress
        @type trans_no: integer
        @param show_close_btn: display close button [x]
        @type show_close_btn: boolean

        @return: HTML code
        @rtype: string
        '''
        ticket_teaser_dict = {'in_process': 'Claim in process!' }
        ticket_message_dict = {'transaction': 'There %s %s transaction%s in progress.' }

        teaser = self._(ticket_teaser_dict[teaser_key])

        if trans_no == 1:
            args = ['is', trans_no, '']
        else:
            args = ['are', trans_no, 's']

        message = self._(ticket_message_dict[message_key] % tuple(args))

        html = []
        h = html.append
        h('<div id="aid_notification_' + teaser_key + '" class="ui-widget ui-alert">')
        h('  <div style="margin-top: 20px; padding: 0pt 0.7em;" class="ui-state-highlight ui-corner-all">')
        h('    <p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-info"></span>')
        h('    <strong>%s</strong> %s ' % (teaser, message))
        h('<a rel="nofollow" id="checkout" href="action?checkout=True">' + self._('Click here to review the transactions.') + '</a>')
        h('<br>')

        if show_close_btn:
            h('    <span style="float:right; margin-right: 0.3em;"><a rel="nofollow" href="#" class="aid_close-notify">X</a></span></p>')

        h(' </div>')
        h('</div>')

        return "\n".join(html)

    def tmpl_search_ticket_box(self, teaser_key, message_key, bibrefs, show_close_btn=False):
        '''
        Creates a box informing about a claim in progress for
        the search.

        @param teaser_key: key to a dict which returns the teaser
        @type teaser_key: string
        @param message_key: key to a dict which returns the message to display in the box
        @type message_key: string
        @param bibrefs: bibrefs which are about to be assigned
        @type bibrefs: list of strings
        @param show_close_btn: display close button [x]
        @type show_close_btn: boolean

        @return: HTML code
        @rtype: string
        '''
        error_teaser_dict = {'person_search': 'Person search for assignment in progress!' }
        error_message_dict = {'assign_papers': 'You are searching for a person to assign the following paper%s:' }

        teaser = self._(error_teaser_dict[teaser_key])
        arg = ''
        if len(bibrefs) > 1:
            arg = 's'
        message = self._(error_message_dict[message_key] % (arg) )

        html = []
        h = html.append
        h('<div id="aid_notification_' + teaser_key + '" class="ui-widget ui-alert">')
        h('  <div style="margin-top: 20px; padding: 0pt 0.7em;" class="ui-state-highlight ui-corner-all">')
        h('    <p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-info"></span>')
        h('    <strong>%s</strong> %s ' % (teaser, message))
        h("<ul>")
        for paper in bibrefs:
            if ',' in paper:
                pbibrec = paper.split(',')[1]
            else:
                pbibrec = paper
            h("<li>%s</li>"
                   % (format_record(int(pbibrec), "ha")))
        h("</ul>")
        h('<a rel="nofollow" id="checkout" href="action?cancel_search_ticket=True">' + self._('Quit searching.') + '</a>')

        if show_close_btn:
            h('    <span style="float:right; margin-right: 0.3em;"><a rel="nofollow" href="#" class="aid_close-notify">X</a></span></p>')

        h(' </div>')
        h('</div>')
        h('<p>&nbsp;</p>')

        return "\n".join(html)


    def tmpl_meta_includes(self, kill_browser_cache=False):
        '''
        Generates HTML code for the header section of the document
        META tags to kill browser caching
        Javascript includes
        CSS definitions

        @param kill_browser_cache: Do we want to kill the browser cache?
        @type kill_browser_cache: boolean
        '''

        js_path = "%s/js" % CFG_SITE_URL
        imgcss_path = "%s/img" % CFG_SITE_URL

        result = []
        # Add browser cache killer, hence some notifications are not displayed
        # out of the session.
        if kill_browser_cache:
            result = [
                '<META HTTP-EQUIV="Pragma" CONTENT="no-cache">',
                '<META HTTP-EQUIV="Cache-Control" CONTENT="no-cache">',
                '<META HTTP-EQUIV="Pragma-directive" CONTENT="no-cache">',
                '<META HTTP-EQUIV="Cache-Directive" CONTENT="no-cache">',
                '<META HTTP-EQUIV="Expires" CONTENT="0">']

        scripts = ["jquery-ui.min.js",
                   "jquery.form.js",
                   "jquery.dataTables.min.js",
                   "bibauthorid.js"]

        result.append('<link rel="stylesheet" type="text/css" href='
                      '"%s/jquery-ui/themes/smoothness/jquery-ui.css" />'
                      % (imgcss_path))
        result.append('<link rel="stylesheet" type="text/css" href='
                      '"%s/datatables_jquery-ui.css" />'
                      % (imgcss_path))
        result.append('<link rel="stylesheet" type="text/css" href='
                      '"%s/bibauthorid.css" />'
                      % (imgcss_path))

        for script in scripts:
            result.append('<script type="text/javascript" src="%s/%s">'
                      '</script>' % (js_path, script))

        return "\n".join(result)


    def tmpl_author_confirmed(self, bibref, pid, verbiage_dict={'alt_confirm':'Confirmed.',
                                                                       'confirm_text':'This record assignment has been confirmed.',
                                                                       'alt_forget':'Forget decision!',
                                                                       'forget_text':'Forget assignment decision',
                                                                       'alt_repeal':'Repeal!',
                                                                       'repeal_text':'Repeal record assignment',
                                                                       'to_other_text':'Assign to another person',
                                                                       'alt_to_other':'To other person!'
                                                                       },
                              show_reset_button=True):
        '''
        Generate play per-paper links for the table for the
        status "confirmed"

        @param bibref: construct of unique ID for this author on this paper
        @type bibref: string
        @param pid: the Person ID
        @type pid: int
        @param verbiage_dict: language for the link descriptions
        @type verbiage_dict: dict
        '''

        stri = ('<!--2!--><span id="aid_status_details"> '
                '<img src="%(url)s/img/aid_check.png" alt="%(alt_confirm)s" />'
                '%(confirm_text)s <br>')
        if show_reset_button:
            stri = stri + (
                '<a rel="nofollow" id="aid_reset_gr" class="aid_grey" href="%(url)s/person/action?reset=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reset_gray.png" alt="%(alt_forget)s" style="margin-left:22px;" />'
                '%(forget_text)s</a><br>')
        stri = stri + (
                '<a rel="nofollow" id="aid_repeal" class="aid_grey" href="%(url)s/person/action?repeal=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reject_gray.png" alt="%(alt_repeal)s" style="margin-left:22px;"/>'
                '%(repeal_text)s</a><br>'
                '<a rel="nofollow" id="aid_to_other" class="aid_grey" href="%(url)s/person/action?to_other_person=True&selection=%(ref)s">'
                '<img src="%(url)s/img/aid_to_other_gray.png" alt="%(alt_to_other)s" style="margin-left:22px;"/>'
                '%(to_other_text)s</a> </span>')
        return (stri
                % ({'url': CFG_SITE_URL, 'ref': bibref, 'pid': pid,
                    'alt_confirm':verbiage_dict['alt_confirm'],
                    'confirm_text':verbiage_dict['confirm_text'],
                    'alt_forget':verbiage_dict['alt_forget'],
                    'forget_text':verbiage_dict['forget_text'],
                    'alt_repeal':verbiage_dict['alt_repeal'],
                    'repeal_text':verbiage_dict['repeal_text'],
                    'to_other_text':verbiage_dict['to_other_text'],
                    'alt_to_other':verbiage_dict['alt_to_other']}))


    def tmpl_author_repealed(self, bibref, pid, verbiage_dict={'alt_confirm':'Confirm!',
                                                                       'confirm_text':'Confirm record assignment.',
                                                                       'alt_forget':'Forget decision!',
                                                                       'forget_text':'Forget assignment decision',
                                                                       'alt_repeal':'Rejected!',
                                                                       'repeal_text':'Repeal this record assignment.',
                                                                       'to_other_text':'Assign to another person',
                                                                       'alt_to_other':'To other person!'
                                                                       } ):
        '''
        Generate play per-paper links for the table for the
        status "repealed"

        @param bibref: construct of unique ID for this author on this paper
        @type bibref: string
        @param pid: the Person ID
        @type pid: int
        @param verbiage_dict: language for the link descriptions
        @type verbiage_dict: dict
        '''
        stri = ('<!---2!--><span id="aid_status_details"> '
                '<img src="%(url)s/img/aid_reject.png" alt="%(alt_repeal)s" />'
                '%(repeal_text)s <br>'
                '<a rel="nofollow" id="aid_confirm" class="aid_grey" href="%(url)s/person/action?confirm=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_check_gray.png" alt="%(alt_confirm)s" style="margin-left: 22px;" />'
                '%(confirm_text)s</a><br>'
                '<a rel="nofollow" id="aid_to_other" class="aid_grey" href="%(url)s/person/action?to_other_person=True&selection=%(ref)s">'
                '<img src="%(url)s/img/aid_to_other_gray.png" alt="%(alt_to_other)s" style="margin-left:22px;"/>'
                '%(to_other_text)s</a> </span>')

        return (stri
                % ({'url': CFG_SITE_URL, 'ref': bibref, 'pid': pid,
                    'alt_confirm':verbiage_dict['alt_confirm'],
                    'confirm_text':verbiage_dict['confirm_text'],
                    'alt_forget':verbiage_dict['alt_forget'],
                    'forget_text':verbiage_dict['forget_text'],
                    'alt_repeal':verbiage_dict['alt_repeal'],
                    'repeal_text':verbiage_dict['repeal_text'],
                    'to_other_text':verbiage_dict['to_other_text'],
                    'alt_to_other':verbiage_dict['alt_to_other']}))


    def tmpl_author_undecided(self, bibref, pid, verbiage_dict={'alt_confirm':'Confirm!',
                                                                       'confirm_text':'Confirm record assignment.',
                                                                       'alt_repeal':'Rejected!',
                                                                       'repeal_text':'This record has been repealed.',
                                                                       'to_other_text':'Assign to another person',
                                                                       'alt_to_other':'To other person!'
                                                                       },
                              show_reset_button=True):
        '''
        Generate play per-paper links for the table for the
        status "no decision taken yet"

        @param bibref: construct of unique ID for this author on this paper
        @type bibref: string
        @param pid: the Person ID
        @type pid: int
        @param verbiage_dict: language for the link descriptions
        @type verbiage_dict: dict
        '''
        #batchprocess?mconfirm=True&bibrefs=['100:17,16']&pid=1
        string = ('<!--0!--><span id="aid_status_details"> '
                '<a rel="nofollow" id="aid_confirm" href="%(url)s/person/action?confirm=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_check.png" alt="%(alt_confirm)s" />'
                '%(confirm_text)s</a><br />'
                '<a rel="nofollow" id="aid_repeal" href="%(url)s/person/action?repeal=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reject.png" alt="%(alt_repeal)s" />'
                '%(repeal_text)s</a> <br />'
                '<a rel="nofollow" id="aid_to_other" href="%(url)s/person/action?to_other_person=True&selection=%(ref)s">'
                '<img src="%(url)s/img/aid_to_other.png" alt="%(alt_to_other)s" />'
                '%(to_other_text)s</a> </span>')
        return (string
                % ({'url': CFG_SITE_URL, 'ref': bibref, 'pid': pid,
                    'alt_confirm':verbiage_dict['alt_confirm'],
                    'confirm_text':verbiage_dict['confirm_text'],
                    'alt_repeal':verbiage_dict['alt_repeal'],
                    'repeal_text':verbiage_dict['repeal_text'],
                    'to_other_text':verbiage_dict['to_other_text'],
                    'alt_to_other':verbiage_dict['alt_to_other']}))


    def tmpl_open_claim(self, bibrefs, pid, last_viewed_pid,
                        search_enabled=True):
        '''
        Generate entry page for "claim or attribute this paper"

        @param bibref: construct of unique ID for this author on this paper
        @type bibref: string
        @param pid: the Person ID
        @type pid: int
        @param last_viewed_pid: last ID that had been subject to an action
        @type last_viewed_pid: int
        '''
        t_html = []
        h = t_html.append

        h(self.tmpl_notification_box('info', 'attribute_papers', bibrefs, show_close_btn=False))
        h('<p> ' + self._('Your options') + ': </p>')

        bibs = ''
        for paper in bibrefs:
            if bibs:
                bibs = bibs + '&'
            bibs = bibs + 'selection=' + str(paper)

        if pid > -1:
            h('<a rel="nofollow" id="clam_for_myself" href="%s/person/action?confirm=True&%s&pid=%s"> ' % (CFG_SITE_URL, bibs, str(pid)) )
            h(self._('Claim for yourself') + ' </a> <br>')

        if last_viewed_pid:
            h('<a rel="nofollow" id="clam_for_last_viewed" href="%s/person/action?confirm=True&%s&pid=%s"> ' % (CFG_SITE_URL, bibs, str(last_viewed_pid[0])) )
            h(self._('Attribute to') + ' %s </a> <br>' % (last_viewed_pid[1]) )

        if search_enabled:
            h('<a rel="nofollow" id="claim_search" href="%s/person/action?to_other_person=True&%s"> ' % (CFG_SITE_URL, bibs))
            h(self._('Search for a person to attribute the paper to') + ' </a> <br>')

        return "\n".join(t_html)


    def __tmpl_admin_records_table(self, form_id, person_id, bibrecids, verbiage_dict={'no_doc_string':'Sorry, there are currently no documents to be found in this category.',
                                                                                              'b_confirm':'Confirm',
                                                                                              'b_repeal':'Repeal',
                                                                                              'b_to_others':'Assign to other person',
                                                                                              'b_forget':'Forget decision'},
                                                                            buttons_verbiage_dict={'mass_buttons':{'no_doc_string':'Sorry, there are currently no documents to be found in this category.',
                                                                                                      'b_confirm':'Confirm',
                                                                                                      'b_repeal':'Repeal',
                                                                                                      'b_to_others':'Assign to other person',
                                                                                                      'b_forget':'Forget decision'},
                                                                                     'record_undecided':{'alt_confirm':'Confirm!',
                                                                                                         'confirm_text':'Confirm record assignment.',
                                                                                                         'alt_repeal':'Rejected!',
                                                                                                         'repeal_text':'This record has been repealed.'},
                                                                                     'record_confirmed':{'alt_confirm':'Confirmed.',
                                                                                                           'confirm_text':'This record assignment has been confirmed.',
                                                                                                           'alt_forget':'Forget decision!',
                                                                                                           'forget_text':'Forget assignment decision',
                                                                                                           'alt_repeal':'Repeal!',
                                                                                                           'repeal_text':'Repeal record assignment'},
                                                                                     'record_repealed':{'alt_confirm':'Confirm!',
                                                                                                        'confirm_text':'Confirm record assignment.',
                                                                                                        'alt_forget':'Forget decision!',
                                                                                                        'forget_text':'Forget assignment decision',
                                                                                                        'alt_repeal':'Rejected!',
                                                                                                        'repeal_text':'Repeal this record assignment.'}},
                                                                            show_reset_button=True):
        '''
        Generate the big tables for the person overview page

        @param form_id: name of the form
        @type form_id: string
        @param person_id: Person ID
        @type person_id: int
        @param bibrecids: List of records to display
        @type bibrecids: list
        @param verbiage_dict: language for the elements
        @type verbiage_dict: dict
        @param buttons_verbiage_dict: language for the buttons
        @type buttons_verbiage_dict: dict
        '''
        no_papers_html = ['<div style="text-align:left;margin-top:1em;"><strong>']
        no_papers_html.append('%s' % self._(verbiage_dict['no_doc_string']) )
        no_papers_html.append('</strong></div>')

        if not bibrecids or not person_id:
            return "\n".join(no_papers_html)

        pp_html = []
        h = pp_html.append

        h('<form id="%s" action="/person/action" method="post">'
                   % (form_id))

        h('<div class="aid_reclist_selector">') #+self._(' On all pages: '))
        h('<a rel="nofollow" rel="group_1" href="#select_all">' + self._('Select All') + '</a> | ')
        h('<a rel="nofollow" rel="group_1" href="#select_none">' + self._('Select None') + '</a> | ')
        h('<a rel="nofollow" rel="group_1" href="#invert_selection">' + self._('Invert Selection') + '</a> | ')
        h('<a rel="nofollow" id="toggle_claimed_rows" href="javascript:toggle_claimed_rows();" '
          'alt="hide">' + self._('Hide successful claims') + '</a>')
        h('</div>')

        h('<div class="aid_reclist_buttons">')
        h(('<img src="%s/img/aid_90low_right.png" alt="∟" />')
          % (CFG_SITE_URL))
        h('<input type="hidden" name="pid" value="%s" />' % (person_id))
        h('<input type="submit" name="confirm" value="%s" class="aid_btn_blue" />' % self._(verbiage_dict['b_confirm']) )
        h('<input type="submit" name="repeal" value="%s" class="aid_btn_blue" />' % self._(verbiage_dict['b_repeal']) )
        h('<input type="submit" name="to_other_person" value="%s" class="aid_btn_blue" />' % self._(verbiage_dict['b_to_others']) )
        #if show_reset_button:
        #    h('<input type="submit" name="reset" value="%s" class="aid_btn_blue" />' % verbiage_dict['b_forget'])
        h("  </div>")


        h('<table  class="paperstable" cellpadding="3" width="100%">')
        h("<thead>")
        h("  <tr>")
        h('    <th>&nbsp;</th>')
        h('    <th>' + self._('Paper Short Info') + '</th>')
        h('    <th>' + self._('Author Name') + '</th>')
        h('    <th>' + self._('Affiliation') + '</th>')
        h('    <th>' + self._('Date') + '</th>')
        h('    <th>' + self._('Experiment') + '</th>')
        h('    <th>' + self._('Actions') + '</th>')
        h('  </tr>')
        h('</thead>')
        h('<tbody>')


        for idx, paper in enumerate(bibrecids):
            h('  <tr style="padding-top: 6px; padding-bottom: 6px;">')

            h('    <td><input type="checkbox" name="selection" '
                           'value="%s" /> </td>' % (paper['bibref']))
            rec_info = format_record(int(paper['recid']), "ha")
            rec_info = str(idx + 1) + '.  ' + rec_info
            h("    <td>%s</td>" % (rec_info))
            h("    <td>%s</td>" % (paper['authorname']))
            aff = ""

            if paper['authoraffiliation']:
                aff = paper['authoraffiliation']
            else:
                aff = self._("Not assigned")

            h("    <td>%s</td>" % (aff))

            if paper['paperdate']:
                pdate = paper['paperdate']
            else:
                pdate = 'N.A.'
            h("    <td>%s</td>" % pdate)

            if paper['paperexperiment']:
                pdate = paper['paperexperiment']
            else:
                pdate = 'N.A.'
            h("    <td>%s</td>" % pdate)

            paper_status = self._("No status information found.")

            if paper['flag'] == 2:
                paper_status = self.tmpl_author_confirmed(paper['bibref'], person_id,
                                            verbiage_dict=buttons_verbiage_dict['record_confirmed'],
                                            show_reset_button=show_reset_button)
            elif paper['flag'] == -2:
                paper_status = self.tmpl_author_repealed(paper['bibref'], person_id,
                                            verbiage_dict=buttons_verbiage_dict['record_repealed'])
            else:
                paper_status = self.tmpl_author_undecided(paper['bibref'], person_id,
                                            verbiage_dict=buttons_verbiage_dict['record_undecided'],
                                            show_reset_button=show_reset_button)

            h('    <td><div id="bibref%s" style="float:left"><!--%s!-->%s &nbsp;</div>'
                           % (paper['bibref'], paper['flag'], paper_status))

            if 'rt_status' in paper and paper['rt_status']:
                h('<img src="%s/img/aid_operator.png" title="%s" '
                  'alt="actions pending" style="float:right" '
                  'height="24" width="24" />'
                  % (CFG_SITE_URL, self._("Operator review of user actions pending")))

            h('    </td>')
            h("  </tr>")

        h("  </tbody>")
        h("</table>")

        h('<div class="aid_reclist_selector">') #+self._(' On all pages: '))
        h('<a rel="nofollow" rel="group_1" href="#select_all">' + self._('Select All') + '</a> | ')
        h('<a rel="nofollow" rel="group_1" href="#select_none">' + self._('Select None') + '</a> | ')
        h('<a rel="nofollow" rel="group_1" href="#invert_selection">' + self._('Invert Selection') + '</a> | ')
        h('<a rel="nofollow" id="toggle_claimed_rows" href="javascript:toggle_claimed_rows();" '
          'alt="hide">' + self._('Hide successful claims') + '</a>')
        h('</div>')

        h('<div class="aid_reclist_buttons">')
        h(('<img src="%s/img/aid_90low_right.png" alt="∟" />')
          % (CFG_SITE_URL))
        h('<input type="hidden" name="pid" value="%s" />' % (person_id))
        h('<input type="submit" name="confirm" value="%s" class="aid_btn_blue" />' % verbiage_dict['b_confirm'])
        h('<input type="submit" name="repeal" value="%s" class="aid_btn_blue" />' % verbiage_dict['b_repeal'])
        h('<input type="submit" name="to_other_person" value="%s" class="aid_btn_blue" />' % verbiage_dict['b_to_others'])
        #if show_reset_button:
        #    h('<input type="submit" name="reset" value="%s" class="aid_btn_blue" />' % verbiage_dict['b_forget'])
        h("  </div>")
        h("</form>")
        return "\n".join(pp_html)


    def __tmpl_reviews_table(self, person_id, bibrecids, admin=False):
        '''
        Generate the table for potential reviews.

        @param form_id: name of the form
        @type form_id: string
        @param person_id: Person ID
        @type person_id: int
        @param bibrecids: List of records to display
        @type bibrecids: list
        @param admin: Show admin functions
        @type admin: boolean
        '''
        no_papers_html = ['<div style="text-align:left;margin-top:1em;"><strong>']
        no_papers_html.append(self._('Sorry, there are currently no records to be found in this category.'))
        no_papers_html.append('</strong></div>')

        if not bibrecids or not person_id:
            return "\n".join(no_papers_html)

        pp_html = []
        h = pp_html.append
        h('<form id="review" action="/person/batchprocess" method="post">')
        h('<table  class="reviewstable" cellpadding="3" width="100%">')
        h('  <thead>')
        h('    <tr>')
        h('      <th>&nbsp;</th>')
        h('      <th>' + self._('Paper Short Info') + '</th>')
        h('      <th>' + self._('Actions') + '</th>')
        h('    </tr>')
        h('  </thead>')
        h('  <tbody>')

        for paper in bibrecids:
            h('  <tr>')
            h('    <td><input type="checkbox" name="selected_bibrecs" '
                       'value="%s" /> </td>' % (paper))
            rec_info = format_record(int(paper[0]), "ha")

            if not admin:
                rec_info = rec_info.replace("person/search?q=", "author/")

            h("    <td>%s</td>" % (rec_info))
            h('    <td><a rel="nofollow" href="/person/batchprocess?selected_bibrecs=%s&mfind_bibref=claim">' + self._('Review Transaction') + '</a></td>'
                           % (paper))
            h("  </tr>")

        h("  </tbody>")
        h("</table>")

        h('<div style="text-align:left;"> ' + self._('On all pages') + ': ')
        h('<a rel="nofollow" rel="group_1" href="#select_all">' + self._('Select All') + '</a> | ')
        h('<a rel="nofollow" rel="group_1" href="#select_none">' + self._('Select None') + '</a> | ')
        h('<a rel="nofollow" rel="group_1" href="#invert_selection">' + self._('Invert Selection') + '</a>')
        h('</div>')

        h('<div style="vertical-align:middle;">')
        h('∟ ' + self._('With selected do') + ': ')
        h('<input type="hidden" name="pid" value="%s" />' % (person_id))
        h('<input type="hidden" name="mfind_bibref" value="claim" />')
        h('<input type="submit" name="submit" value="Review selected transactions" />')
        h("  </div>")
        h('</form>')

        return "\n".join(pp_html)


    def tmpl_admin_person_info_box(self, ln, person_id= -1, names=[]):
        '''
        Generate the box showing names

        @param ln: the language to use
        @type ln: string
        @param person_id: Person ID
        @type person_id: int
        @param names: List of names to display
        @type names: list
        '''
        html = []
        h = html.append

        if not ln:
            pass

        #class="ui-tabs ui-widget ui-widget-content ui-corner-all">
        h('<div id="aid_person_names"')
        h('<p><strong>' + self._('Names variants') + ':</strong></p>')
        h("<p>")
        h('<!--<span class="aid_lowlight_text">Person ID: <span id="pid%s">%s</span></span><br />!-->'
                      % (person_id, person_id))

        for name in names:
#            h(("%s "+self._('as appeared on')+" %s"+self._(' records')+"<br />")
#                             % (name[0], name[1]))
            h(("%s (%s); ")
                             % (name[0], name[1]))

        h("</p>")
        h("</div>")

        return "\n".join(html)


    def tmpl_admin_tabs(self, ln=CFG_SITE_LANG, person_id= -1,
                        rejected_papers=[],
                        rest_of_papers=[],
                        review_needed=[],
                        rt_tickets=[],
                        open_rt_tickets=[],
                        show_tabs=['records', 'repealed', 'review', 'comments', 'tickets', 'data'],
                        show_reset_button=True,
                        ticket_links=['delete', 'commit', 'del_entry', 'commit_entry'],
                        verbiage_dict={'confirmed':'Records', 'repealed':'Not this person\'s records',
                                         'review':'Records in need of review',
                                         'tickets':'Open Tickets', 'data':'Data',
                                         'confirmed_ns':'Papers of this Person',
                                         'repealed_ns':'Papers _not_ of this Person',
                                         'review_ns':'Papers in need of review',
                                         'tickets_ns':'Tickets for this Person',
                                         'data_ns':'Additional Data for this Person'},
                        buttons_verbiage_dict={'mass_buttons':{'no_doc_string':'Sorry, there are currently no documents to be found in this category.',
                                                                  'b_confirm':'Confirm',
                                                                  'b_repeal':'Repeal',
                                                                  'b_to_others':'Assign to other person',
                                                                  'b_forget':'Forget decision'},
                                                 'record_undecided':{'alt_confirm':'Confirm!',
                                                                     'confirm_text':'Confirm record assignment.',
                                                                     'alt_repeal':'Rejected!',
                                                                     'repeal_text':'This record has been repealed.'},
                                                 'record_confirmed':{'alt_confirm':'Confirmed.',
                                                                       'confirm_text':'This record assignment has been confirmed.',
                                                                       'alt_forget':'Forget decision!',
                                                                       'forget_text':'Forget assignment decision',
                                                                       'alt_repeal':'Repeal!',
                                                                       'repeal_text':'Repeal record assignment'},
                                                 'record_repealed':{'alt_confirm':'Confirm!',
                                                                    'confirm_text':'Confirm record assignment.',
                                                                    'alt_forget':'Forget decision!',
                                                                    'forget_text':'Forget assignment decision',
                                                                    'alt_repeal':'Rejected!',
                                                                    'repeal_text':'Repeal this record assignment.'}}):
        '''
        Generate the tabs for the person overview page

        @param ln: the language to use
        @type ln: string
        @param person_id: Person ID
        @type person_id: int
        @param rejected_papers: list of repealed papers
        @type rejected_papers: list
        @param rest_of_papers: list of attributed of undecided papers
        @type rest_of_papers: list
        @param review_needed: list of papers that need a review (choose name)
        @type review_needed:list
        @param rt_tickets: list of tickets for this Person
        @type rt_tickets: list
        @param open_rt_tickets: list of open request tickets
        @type open_rt_tickets: list
        @param show_tabs: list of tabs to display
        @type show_tabs: list of strings
        @param ticket_links: list of links to display
        @type ticket_links: list of strings
        @param verbiage_dict: language for the elements
        @type verbiage_dict: dict
        @param buttons_verbiage_dict: language for the buttons
        @type buttons_verbiage_dict: dict
        '''
        html = []
        h = html.append

        h('<div id="aid_tabbing">')
        h('  <ul>')
        if 'records' in show_tabs:
            r = verbiage_dict['confirmed']
            h('    <li><a rel="nofollow" href="#tabRecords"><span>%(r)s (%(l)s)</span></a></li>' %
              ({'r':r, 'l':len(rest_of_papers)}))
        if 'repealed' in show_tabs:
            r = verbiage_dict['repealed']
            h('    <li><a rel="nofollow" href="#tabNotRecords"><span>%(r)s (%(l)s)</span></a></li>' %
              ({'r':r, 'l':len(rejected_papers)}))
        if 'review' in show_tabs:
            r = verbiage_dict['review']
            h('    <li><a rel="nofollow" href="#tabReviewNeeded"><span>%(r)s (%(l)s)</span></a></li>' %
              ({'r':r, 'l':len(review_needed)}))
        if 'tickets' in show_tabs:
            r = verbiage_dict['tickets']
            h('    <li><a rel="nofollow" href="#tabTickets"><span>%(r)s (%(l)s)</span></a></li>' %
              ({'r':r, 'l':len(open_rt_tickets)}))
        if 'data' in show_tabs:
            r = verbiage_dict['data']
            h('    <li><a rel="nofollow" href="#tabData"><span>%s</span></a></li>' % r)
        h('  </ul>')

        if 'records' in show_tabs:
            h('  <div id="tabRecords">')
            r = verbiage_dict['confirmed_ns']
            h('<noscript><h5>%s</h5></noscript>' % r)
            h(self.__tmpl_admin_records_table("massfunctions",
                                             person_id, rest_of_papers,
                                             verbiage_dict=buttons_verbiage_dict['mass_buttons'],
                                             buttons_verbiage_dict=buttons_verbiage_dict,
                                             show_reset_button=show_reset_button))
            h("  </div>")

        if 'repealed' in show_tabs:
            h('  <div id="tabNotRecords">')
            r = verbiage_dict['repealed_ns']
            h('<noscript><h5>%s</h5></noscript>' % r)
            h(self._('These records have been marked as not being from this person.'))
            h('<br />' + self._('They will be regarded in the next run of the author ')
              + self._('disambiguation algorithm and might disappear from this listing.'))
            h(self.__tmpl_admin_records_table("rmassfunctions",
                                             person_id, rejected_papers,
                                             verbiage_dict=buttons_verbiage_dict['mass_buttons'],
                                              buttons_verbiage_dict=buttons_verbiage_dict,
                                              show_reset_button=show_reset_button))
            h("  </div>")

        if 'review' in show_tabs:
            h('  <div id="tabReviewNeeded">')
            r = verbiage_dict['review_ns']
            h('<noscript><h5>%s</h5></noscript>' % r)
            h(self.__tmpl_reviews_table(person_id, review_needed, True))
            h('  </div>')
        if 'tickets' in show_tabs:
            h('  <div id="tabTickets">')
            r = verbiage_dict['tickets']
            h('<noscript><h5>%s</h5></noscript>' % r)
            r = verbiage_dict['tickets_ns']
            h('<p>%s:</p>' % r)

            if rt_tickets:
                pass
#            open_rt_tickets = [a for a in open_rt_tickets if a[1] == rt_tickets]

            for t in open_rt_tickets:
                name = self._('Not provided')
                surname = self._('Not provided')
                uidip = self._('Not available')
                comments = self._('No comments')
                email = self._('Not provided')
                date = self._('Not Available')
                actions = []

                for info in t[0]:
                    if info[0] == 'firstname':
                        name = info[1]
                    elif info[0] == 'lastname':
                        surname = info[1]
                    elif info[0] == 'uid-ip':
                        uidip = info[1]
                    elif info[0] == 'comments':
                        comments = info[1]
                    elif info[0] == 'email':
                        email = info[1]
                    elif info[0] == 'date':
                        date = info[1]
                    elif info[0] in ['confirm', 'repeal']:
                        actions.append(info)

                if 'delete' in ticket_links:
                    h(('<strong>Ticket number: %(tnum)s </strong> <a rel="nofollow" id="cancel" href=%(url)s/person/action?cancel_rt_ticket=True&selection=%(tnum)s&pid=%(pid)s>' + self._(' Delete this ticket') + ' </a>')
                  % ({'tnum':t[1], 'url':CFG_SITE_URL, 'pid':str(person_id)}))

                if 'commit' in ticket_links:
                    h((' or <a rel="nofollow" id="commit" href=%(url)s/person/action?commit_rt_ticket=True&selection=%(tnum)s&pid=%(pid)s>' + self._(' Commit this entire ticket') + ' </a> <br>')
                  % ({'tnum':t[1], 'url':CFG_SITE_URL, 'pid':str(person_id)}))

                h('<dd>')
                h('Open from: %s, %s <br>' % (surname, name))
                h('Date: %s <br>' % date)
                h('identified by: %s <br>' % uidip)
                h('email: %s <br>' % email)
                h('comments: %s <br>' % comments)
                h('Suggested actions: <br>')
                h('<dd>')

                for a in actions:
                    bibref, bibrec = a[1].split(',')
                    pname = get_bibrefrec_name_string(bibref)
                    title = ""

                    try:
                        title = get_fieldvalues(int(bibrec), "245__a")[0]
                    except IndexError:
                        title = self._("No title available")
                    title = escape_html(title)

                    if 'commit_entry' in ticket_links:
                        h('<a rel="nofollow" id="action" href="%(url)s/person/action?%(action)s=True&pid=%(pid)s&selection=%(bib)s&rt_id=%(rt)s">%(action)s - %(name)s on %(title)s </a>'
                      % ({'action': a[0], 'url': CFG_SITE_URL,
                          'pid': str(person_id), 'bib':a[1],
                          'name': pname, 'title': title, 'rt': t[1]}))
                    else:
                        h('%(action)s - %(name)s on %(title)s'
                      % ({'action': a[0], 'name': pname, 'title': title}))

                    if 'del_entry' in ticket_links:
                        h(' - <a rel="nofollow" id="action" href="%(url)s/person/action?cancel_rt_ticket=True&pid=%(pid)s&selection=%(bib)s&rt_id=%(rt)s&rt_action=%(action)s"> Delete this entry </a>'
                      % ({'action': a[0], 'url': CFG_SITE_URL,
                          'pid': str(person_id), 'bib': a[1], 'rt': t[1]}))

                    h(' - <a rel="nofollow" id="show_paper" target="_blank" href="%(url)s/record/%(record)s"> View record <br>' % ({'url':CFG_SITE_URL, 'record':str(bibrec)}))
                h('</dd>')
                h('</dd><br>')
#            h(str(open_rt_tickets))
            h("  </div>")

        if 'data' in show_tabs:
            h('  <div id="tabData">')
            r = verbiage_dict['data_ns']
            h('<noscript><h5>%s</h5></noscript>' % r)
            canonical_name = str(get_canonical_id_from_person_id(person_id))
            if '.' in str(canonical_name) and not isinstance(canonical_name, int):
                canonical_name = canonical_name[0:canonical_name.rindex('.')]
            h('<div><div> <strong> Person id </strong> <br> %s <br>' % person_id)
            h('<strong> <br> Canonical name setup </strong>')
            h('<div style="margin-top: 15px;"> Current canonical name: %s  <form method="GET" action="%s/person/action" rel="nofollow">' % (canonical_name, CFG_SITE_URL))
            h('<input type="hidden" name="set_canonical_name" value="True" />')
            h('<input name="canonical_name" id="canonical_name" type="text" style="border:1px solid #333; width:500px;" value="%s" /> ' % canonical_name)
            h('<input type="hidden" name="pid" value="%s" />' % person_id)
            h('<input type="submit" value="set canonical name" class="aid_btn_blue" />')
            h('<br>NOTE: please note the a number is appended automatically to the name displayed above. This cannot be manually triggered so to ensure unicity of IDs.')
            h('To change the number if greater then one, please change all the other names first, then updating this one will do the trick. </div>')
            h('</form> </div></div>')

            userid = get_uid_from_personid(person_id)
            h('<div> <br>')
            h('<strong> Internal IDs </strong> <br>')
            if userid:
                email = get_email(int(userid))
                h('UserID: INSPIRE user %s is associated with this profile with email: %s' % (str(userid), str(email)))
            else:
                h('UserID: There is no INSPIRE user associated to this profile!')
            h('<br></div>')

            external_ids = get_personiID_external_ids(person_id)
            h('<div> <br>')
            h('<strong> External IDs </strong> <br>')

            h('<form method="GET" action="%s/person/action" rel="nofollow">' % (CFG_SITE_URL) )
            h('<input type="hidden" name="add_missing_external_ids" value="True">')
            h('<input type="hidden" name="pid" value="%s">' % person_id)
            h('<br> <input type="submit" value="add missing ids" class="aid_btn_blue"> </form>')

            h('<form method="GET" action="%s/person/action" rel="nofollow">' % (CFG_SITE_URL) )
            h('<input type="hidden" name="rewrite_all_external_ids" value="True">')
            h('<input type="hidden" name="pid" value="%s">' % person_id)
            h('<br> <input type="submit" value="rewrite all ids" class="aid_btn_blue"> </form> <br>')

            if external_ids:
                h('<form method="GET" action="%s/person/action" rel="nofollow">' % (CFG_SITE_URL) )
                h('   <input type="hidden" name="delete_external_ids" value="True">')
                h('   <input type="hidden" name="pid" value="%s">' % person_id)
                for idx in external_ids:
                    try:
                        sys = [s for s in EXTERNAL_SYSTEMS_LIST if EXTERNAL_SYSTEMS_LIST[s] == idx][0]
                    except (IndexError):
                        sys = ''
                    for k in external_ids[idx]:
                        h('<br> <input type="checkbox" name="existing_ext_ids" value="%s||%s"> <strong> %s: </strong> %s' % (idx, k, sys, k))
                h('        <br> <br> <input type="submit" value="delete selected ids" class="aid_btn_blue"> <br> </form>')
            else:
                h('UserID: There are no external users associated to this profile!')



            h('<br> <br>')
            h('<form method="GET" action="%s/person/action" rel="nofollow">' % (CFG_SITE_URL) )
            h('   <input type="hidden" name="add_external_id" value="True">')
            h('   <input type="hidden" name="pid" value="%s">' % person_id)
            h('   <select name="ext_system">')
            h('      <option value="" selected>-- ' + self._('Choose system') + ' --</option>')
            for el in EXTERNAL_SYSTEMS_LIST:
                h('  <option value="%s"> %s </option>' % (EXTERNAL_SYSTEMS_LIST[el], el))
            h('   </select>')
            h('   <input type="text" name="ext_id" id="ext_id" style="border:1px solid #333; width:350px;">')
            h('   <input type="submit" value="add external id" class="aid_btn_blue">')
            # h('<br>NOTE: please note that if you add an external id it will replace the previous one (if any).')
            h('<br> </form> </div>')

            h('</div> </div>')
        h('</div>')

        return "\n".join(html)


    def tmpl_bibref_check(self, bibrefs_auto_assigned, bibrefs_to_confirm):
        '''
        Generate overview to let user chose the name on the paper that
        resembles the person in question.

        @param bibrefs_auto_assigned: list of auto-assigned papers
        @type bibrefs_auto_assigned: list
        @param bibrefs_to_confirm: list of unclear papers and names
        @type bibrefs_to_confirm: list
        '''
        html = []
        h = html.append
        h('<form id="review" action="/person/action" method="post">')
        h('<p><strong>' + self._("Make sure we match the right names!")
          + '</strong></p>')
        h('<p>' + self._('Please select an author on each of the records that will be assigned.') + '<br/>')
        h(self._('Papers without a name selected will be ignored in the process.'))
        h('</p>')

        for person in bibrefs_to_confirm:
            if not "bibrecs" in bibrefs_to_confirm[person]:
                continue

            person_name = bibrefs_to_confirm[person]["person_name"]
            if person_name.isspace():
                h((self._('Claim for person with id') + ': %s. ') % person)
                h(self._('This seems to be an empty profile without names associated to it yet'))
                h(self._('(the names will be automatically gathered when the first paper is claimed to this profile).'))
            else:
                h((self._("Select name for") + " %s") % (person_name))
            pid = person

            for recid in bibrefs_to_confirm[person]["bibrecs"]:
                h('<div id="aid_moreinfo">')

                try:
                    fv = get_fieldvalues(int(recid), "245__a")[0]
                except (ValueError, IndexError, TypeError):
                    fv = self._('Error retrieving record title')
                fv = escape_html(fv)

                h(self._("Paper title: ") + fv)
                h('<select name="bibrecgroup%s">' % (recid))
                h('<option value="" selected>-- Choose author name --</option>')

                for bibref in bibrefs_to_confirm[person]["bibrecs"][recid]:
                    h('<option value="%s||%s">%s</option>'
                      % (pid, bibref[0], bibref[1]))

                h('</select>')
                h("</div>")

        if bibrefs_auto_assigned:
            h(self._('The following names have been automatically chosen:'))
            for person in bibrefs_auto_assigned:
                if not "bibrecs" in bibrefs_auto_assigned[person]:
                    continue

                h((self._("For") + " %s:") % bibrefs_auto_assigned[person]["person_name"])
                pid = person

                for recid in bibrefs_auto_assigned[person]["bibrecs"]:
                    try:
                        fv = get_fieldvalues(int(recid), "245__a")[0]
                    except (ValueError, IndexError, TypeError):
                        fv = self._('Error retrieving record title')
                    fv = escape_html(fv)

                    h('<div id="aid_moreinfo">')
                    h(('%s' + self._(' --  With name: ')) % (fv) )
                    #, bibrefs_auto_assigned[person]["bibrecs"][recid][0][1]))
                    # asbibref = "%s||%s" % (person, bibrefs_auto_assigned[person]["bibrecs"][recid][0][0])
                    pbibref = bibrefs_auto_assigned[person]["bibrecs"][recid][0][0]
                    h('<select name="bibrecgroup%s">' % (recid))
                    h('<option value="" selected>-- ' + self._('Ignore') + ' --</option>')

                    for bibref in bibrefs_auto_assigned[person]["bibrecs"][recid]:
                        selector = ""

                        if bibref[0] == pbibref:
                            selector = ' selected="selected"'

                        h('<option value="%s||%s"%s>%s</option>'
                          % (pid, bibref[0], selector, bibref[1]))

                    h('</select>')
#                    h('<input type="hidden" name="bibrecgroup%s" value="%s" />'
#                      % (recid, asbibref))
                    h('</div>')

        h('<div style="text-align:center;">')
        h('  <input type="submit" class="aid_btn_green" name="bibref_check_submit" value="Accept" />')
        h('  <input type="submit" class="aid_btn_blue" name="cancel_stage" value="Cancel" />')
        h("</div>")
        h('</form>')

        return "\n".join(html)


    def tmpl_invenio_search_box(self):
        '''
        Generate little search box for missing papers. Links to main invenio
        search on start papge.
        '''
        html = []
        h = html.append
        h('<div style="margin-top: 15px;"> <strong>Search for missing papers:</strong> <form method="GET" action="%s/search">' % CFG_SITE_URL)
        h('<input name="p" id="p" type="text" style="border:1px solid #333; width:500px;" /> ')
        h('<input type="submit" name="action_search" value="search" '
          'class="aid_btn_blue" />')
        h('</form> </div>')

        return "\n".join(html)


    def tmpl_person_menu(self):
        '''
        Generate the menu bar
        '''
        html = []
        h = html.append
        h('<div id="aid_menu">')
        h('  <ul>')
        h('    <li>' + self._('Navigation:') + '</li>')
        h(('    <li><a rel="nofollow" href="%s/person/search">' + self._('Run paper attribution for another author') + '</a></li>') % CFG_SITE_URL)
        h('    <!--<li><a rel="nofollow" href="#">' + self._('Person Interface FAQ') + '</a></li>!-->')
        h('  </ul>')
        h('</div>')

        return "\n".join(html)

    def tmpl_person_menu_admin(self):
        '''
        Generate the menu bar
        '''
        html = []
        h = html.append
        h('<div id="aid_menu">')
        h('  <ul>')
        h('    <li>' + self._('Navigation:') + '</li>')
        h(('    <li><a rel="nofollow" href="%s/person/search">' + self._('Person Search') + '</a></li>') % CFG_SITE_URL)
        h(('    <li><a rel="nofollow" href="%s/person/tickets_admin">' + self._('Open tickets') + '</a></li>') % CFG_SITE_URL)
        h('    <!--<li><a rel="nofollow" href="#">' + self._('Person Interface FAQ') + '</a></li>!-->')
        h('  </ul>')
        h('</div>')

        return "\n".join(html)

    def tmpl_ticket_final_review(self, req, mark_yours=[], mark_not_yours=[],
                                 mark_theirs=[], mark_not_theirs=[]):
        '''
        Generate final review page. Displaying transactions if they
        need confirmation.

        @param req: Apache request object
        @type req: Apache request object
        @param mark_yours: papers marked as 'yours'
        @type mark_yours: list
        @param mark_not_yours: papers marked as 'not yours'
        @type mark_not_yours: list
        @param mark_theirs: papers marked as being someone else's
        @type mark_theirs: list
        @param mark_not_theirs: papers marked as NOT being someone else's
        @type mark_not_theirs: list
        '''
        def html_icon_legend():
            html = []
            h = html.append
            h('<div id="legend">')
            h("<p>")
            h(self._("Symbols legend: "))
            h("</p>")
            h('<span style="margin-left:25px; vertical-align:middle;">')
            h('<img src="%s/img/aid_granted.png" '
              'alt="%s" width="30" height="30" />'
              % (CFG_SITE_URL, self._("Everything is shiny, captain!")))
            h(self._('The result of this request will be visible immediately'))
            h('</span><br />')
            h('<span style="margin-left:25px; vertical-align:middle;">')
            h('<img src="%s/img/aid_warning_granted.png" '
              'alt="%s" width="30" height="30" />'
              % (CFG_SITE_URL, self._("Confirmation needed to continue")))
            h(self._('The result of this request will be visible immediately but we need your confirmation to do so for this paper has been manually claimed before'))
            h('</span><br />')
            h('<span style="margin-left:25px; vertical-align:middle;">')
            h('<img src="%s/img/aid_denied.png" '
              'alt="%s" width="30" height="30" />'
              % (CFG_SITE_URL, self._("This will create a change request for the operators")))
            h(self._("The result of this request will be visible upon confirmation through an operator"))
            h("</span>")
            h("</div>")

            return "\n".join(html)


        def mk_ticket_row(ticket):
            recid = -1
            rectitle = ""
            recauthor = "No Name Found."
            personname = "No Name Found."

            try:
                recid = ticket['bibref'].split(",")[1]
            except (ValueError, KeyError, IndexError):
                return ""

            try:
                rectitle = get_fieldvalues(int(recid), "245__a")[0]
            except (ValueError, IndexError, TypeError):
                rectitle = self._('Error retrieving record title')
            rectitle = escape_html(rectitle)

            if "authorname_rec" in ticket:
                recauthor = ticket['authorname_rec']

            if "person_name" in ticket:
                personname = ticket['person_name']

            html = []
            h = html.append

#            h("Debug: " + str(ticket) + "<br />")
            h('<td width="25">&nbsp;</td>')
            h('<td>')
            h(rectitle)
            h('</td>')
            h('<td>')
            h((personname + " (" + self._("Selected name on paper") + ": %s)") % recauthor)
            h('</td>')
            h('<td>')

            if ticket['status'] == "granted":
                h('<img src="%s/img/aid_granted.png" '
                  'alt="%s" width="30" height="30" />'
                  % (CFG_SITE_URL, self._("Everything is shiny, captain!")))
            elif ticket['status'] == "warning_granted":
                h('<img src="%s/img/aid_warning_granted.png" '
                  'alt="%s" width="30" height="30" />'
                  % (CFG_SITE_URL, self._("Verification needed to continue")))
            else:
                h('<img src="%s/img/aid_denied.png" '
                  'alt="%s" width="30" height="30" />'
                  % (CFG_SITE_URL, self._("This will create a request for the operators")))

            h('</td>')
            h('<td>')
            h('<a rel="nofollow" href="%s/person/action?checkout_remove_transaction=%s ">'
              'Cancel'
              '</a>' % (CFG_SITE_URL, ticket['bibref']))
            h('</td>')

            return "\n".join(html)


        session = get_session(req)
        pinfo = session["personinfo"]
        ulevel = pinfo["ulevel"]

        html = []
        h = html.append

#        h(html_icon_legend())

        if "checkout_faulty_fields" in pinfo and pinfo["checkout_faulty_fields"]:
            h(self.tmpl_error_box('sorry', 'check_entries'))

        if ("checkout_faulty_fields" in pinfo
            and pinfo["checkout_faulty_fields"]
            and "tickets" in pinfo["checkout_faulty_fields"]):
            h(self.tmpl_error_box('error', 'provide_transaction'))

#        h('<div id="aid_checkout_teaser">' +
#          self._('Almost done! Please use the button "Confirm these changes" '
#                 'at the end of the page to send this request to an operator '
#                 'for review!') + '</div>')

        h('<div id="aid_person_names" '
          'class="ui-tabs ui-widget ui-widget-content ui-corner-all"'
          'style="padding:10px;">')

        h("<h4>" + self._('Please provide your information') + "</h4>")
        h('<form id="final_review" action="%s/person/action" method="post">'
          % (CFG_SITE_URL))

        if ("checkout_faulty_fields" in pinfo
            and pinfo["checkout_faulty_fields"]
            and "user_first_name" in pinfo["checkout_faulty_fields"]):
            h("<p class='aid_error_line'>" + self._('Please provide your first name') + "</p>")

        h("<p>")
        if "user_first_name_sys" in pinfo and pinfo["user_first_name_sys"]:
            h((self._("Your first name:") + " %s") % pinfo["user_first_name"])
        else:
            h(self._('Your first name:') + ' <input type="text" name="user_first_name" value="%s" />'
              % pinfo["user_first_name"])

        if ("checkout_faulty_fields" in pinfo
            and pinfo["checkout_faulty_fields"]
            and "user_last_name" in pinfo["checkout_faulty_fields"]):
            h("<p class='aid_error_line'>" + self._('Please provide your last name') + "</p>")

        h("</p><p>")

        if "user_last_name_sys" in pinfo and pinfo["user_last_name_sys"]:
            h((self._("Your last name:") + " %s") % pinfo["user_last_name"])
        else:
            h(self._('Your last name:') + ' <input type="text" name="user_last_name" value="%s" />'
              % pinfo["user_last_name"])

        h("</p>")

        if ("checkout_faulty_fields" in pinfo
            and pinfo["checkout_faulty_fields"]
            and "user_email" in pinfo["checkout_faulty_fields"]):
            h("<p class='aid_error_line'>" + self._('Please provide your eMail address') + "</p>")

        if ("checkout_faulty_fields" in pinfo
            and pinfo["checkout_faulty_fields"]
            and "user_email_taken" in pinfo["checkout_faulty_fields"]):
            h("<p class='aid_error_line'>" +
              self._('This eMail address is reserved by a user. Please log in or provide an alternative eMail address')
              + "</p>")

        h("<p>")
        if "user_email_sys" in pinfo and pinfo["user_email_sys"]:
            h((self._("Your eMail:") + " %s") % pinfo["user_email"])
        else:
            h((self._('Your eMail:') + ' <input type="text" name="user_email" value="%s" />')
              % pinfo["user_email"])
        h("</p><p>")

        h(self._("You may leave a comment (optional)") + ":<br>")
        h('<textarea name="user_comments">')

        if "user_ticket_comments" in pinfo:
            h(pinfo["user_ticket_comments"])

        h("</textarea>")

        h("</p>")
        h("<p>&nbsp;</p>")

        h('<div style="text-align: center;">')
        h(('  <input type="submit" name="checkout_continue_claiming" class="aid_btn_green" value="%s" />')
          % self._("Continue claiming*"))
        h(('  <input type="submit" name="checkout_submit" class="aid_btn_green" value="%s" />')
          % self._("Confirm these changes**"))
        h('<span style="margin-left:150px;">')
        h(('  <input type="submit" name="cancel" class="aid_btn_red" value="%s" />')
          % self._("!Delete the entire request!"))
        h('</span>')
        h('</div>')
        h("</form>")
        h('</div>')

        h('<div id="aid_person_names" '
          'class="ui-tabs ui-widget ui-widget-content ui-corner-all"'
          'style="padding:10px;">')
        h('<table width="100%" border="0" cellspacing="0" cellpadding="4">')

        if not ulevel == "guest":
            h('<tr>')
            h("<td colspan='5'><h4>" + self._('Mark as your documents') + "</h4></td>")
            h('</tr>')

            if mark_yours:
                for idx, ticket in enumerate(mark_yours):
                    h('<tr id="aid_result%s">' % ((idx + 1) % 2))
                    h(mk_ticket_row(ticket))
                    h('</tr>')
            else:
                h('<tr>')
                h('<td width="25">&nbsp;</td>')
                h('<td colspan="4">Nothing staged as yours</td>')
                h("</tr>")

            h('<tr>')
            h("<td colspan='5'><h4>" + self._("Mark as _not_ your documents") + "</h4></td>")
            h('</tr>')

            if mark_not_yours:
                for idx, ticket in enumerate(mark_not_yours):
                    h('<tr id="aid_result%s">' % ((idx + 1) % 2))
                    h(mk_ticket_row(ticket))
                    h('</tr>')
            else:
                h('<tr>')
                h('<td width="25">&nbsp;</td>')
                h('<td colspan="4">' + self._('Nothing staged as not yours') + '</td>')
                h("</tr>")

        h('<tr>')
        h("<td colspan='5'><h4>" + self._('Mark as their documents') + "</h4></td>")
        h('</tr>')

        if mark_theirs:
            for idx, ticket in enumerate(mark_theirs):
                h('<tr id="aid_result%s">' % ((idx + 1) % 2))
                h(mk_ticket_row(ticket))
                h('</tr>')
        else:
            h('<tr>')
            h('<td width="25">&nbsp;</td>')
            h('<td colspan="4">' + self._('Nothing staged in this category') + '</td>')
            h("</tr>")

        h('<tr>')
        h("<td colspan='5'><h4>" + self._('Mark as _not_ their documents') + "</h4></td>")
        h('</tr>')

        if mark_not_theirs:
            for idx, ticket in enumerate(mark_not_theirs):
                h('<tr id="aid_result%s">' % ((idx + 1) % 2))
                h(mk_ticket_row(ticket))
                h('</tr>')
        else:
            h('<tr>')
            h('<td width="25">&nbsp;</td>')
            h('<td colspan="4">' + self._('Nothing staged in this category') + '</td>')
            h("</tr>")

        h('</table>')
        h("</div>")
        h("<p>")
        h(self._("  * You can come back to this page later. Nothing will be lost. <br />"))
        h(self._("  ** Performs all requested changes. Changes subject to permission restrictions "
                 "will be submitted to an operator for manual review."))
        h("</p>")

        h(html_icon_legend())

        return "\n".join(html)


    def tmpl_author_search(self, query, results,
                           search_ticket=None, author_pages_mode=True,
                           fallback_mode=False, fallback_title='',
                           fallback_message='', new_person_link=False):
        '''
        Generates the search for Person entities.

        @param query: the query a user issued to the search
        @type query: string
        @param results: list of results
        @type results: list
        @param search_ticket: search ticket object to inform about pending
            claiming procedure
        @type search_ticket: dict
        '''
        linktarget = "person"

        if author_pages_mode:
            linktarget = "author"

        if not query:
            query = ""

        html = []
        h = html.append

        h('<form id="searchform" action="/person/search" method="GET">')
        h('Find author clusters by name. e.g: <i>Ellis, J</i>: <br>')
        h('<input placeholder="Search for a name, e.g: Ellis, J" type="text" name="q" style="border:1px solid #333; width:500px;" '
                    'maxlength="250" value="%s" class="focus" />' % query)
        h('<input type="submit" value="Search" />')
        h('</form>')

        if fallback_mode:
            if fallback_title:
                h('<div id="header">%s</div>' % fallback_title)
            if fallback_message:
                h('%s' % fallback_message)

        if not results and not query:
            h('</div>')
            return "\n".join(html)

        h("<p>&nbsp;</p>")

        if query and not results:
            authemail = CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL
            h(('<strong>' + self._("We do not have a publication list for '%s'." +
                                 " Try using a less specific author name, or check" +
                                 " back in a few days as attributions are updated " +
                                 "frequently.  Or you can send us feedback, at ") +
                                 "<a rel='nofollow' href=\"mailto:%s\">%s</a>.</strong>") % (query, authemail, authemail))
            h('</div>')
            if new_person_link:
                link = "%s/person/action?confirm=True&pid=%s" % (CFG_SITE_URL, '-3')
                if search_ticket:
                    for r in search_ticket['bibrefs']:
                        link = link + '&selection=%s' % str(r)
                h('<div>')
                h('<a rel="nofollow" href="%s">' % (link))
                h(self._("Create a new Person for your search"))
                h('</a>')
                h('</div>')
            return "\n".join(html)

#        base_color = 100
#        row_color = 0

        for index, result in enumerate(results):
#            if len(results) > base_color:
#                row_color += 1
#            else:
#                row_color = base_color - (base_color - index *
#                                          (base_color / len(results)))

            pid = result[0]
            names = result[1]
            papers = result[2]
            try:
                total_papers = result[3]
                if total_papers > 1:
                    papers_string = '(%s Papers)' % str(total_papers)
                elif total_papers == 1:
                    if (len(papers) == 1 and
                        len(papers[0]) == 1 and
                        papers[0][0] == 'Not retrieved to increase performances.'):
                        papers_string = ''
                    else:
                        papers_string = '(1 Paper)'
                else:
                    papers_string = '(No papers)'
            except IndexError:
                papers_string = ''

            h('<div id="aid_result%s">' % (index % 2))
            h('<div style="padding-bottom:5px;">')
#            h('<span style="color:rgb(%d,%d,%d);">%s. </span>'
#                         % (row_color, row_color, row_color, index + 1))
            h('<span>%s. </span>' % (index + 1))

#            for nindex, name in enumerate(names):
#                color = row_color + nindex * 35
#                color = min(color, base_color)
#                h('<span style="color:rgb(%d,%d,%d);">%s; </span>'
#                            % (color, color, color, name[0]))
            for name in names:
                h('<span style="margin-right:20px;">%s </span>'
                            % (name[0]))
            h('</div>')
            h('<em style="padding-left:1.5em;">')
            if index < bconfig.PERSON_SEARCH_RESULTS_SHOW_PAPERS_PERSON_LIMIT:
                h(('<a rel="nofollow" href="#" id="aid_moreinfolink" class="mpid%s">'
                            '<img src="../img/aid_plus_16.png" '
                            'alt = "toggle additional information." '
                            'width="11" height="11"/> '
                            + self._('Recent Papers') +
                            '</a></em>')
                            % (pid))
            else:
                h("</em>")

            if search_ticket:
                link = "%s/person/action?confirm=True&pid=%s" % (CFG_SITE_URL, pid)

                for r in search_ticket['bibrefs']:
                    link = link + '&selection=%s' % str(r)

                h(('<span style="margin-left: 120px;">'
                            '<em><a rel="nofollow" href="%s" id="confirmlink">'
                            '<strong>' + self._('YES!') + '</strong>'
                            + self._(' Attribute Papers To ') +
                            '%s %s </a></em></span>')
                            % (link, get_person_redirect_link(pid), papers_string))
            else:
                h(('<span style="margin-left: 40px;">'
                            '<em><a rel="nofollow" href="%s/%s/%s" id="aid_moreinfolink">'
                            + self._('Publication List ') + '(%s) %s </a></em></span>')
                            % (CFG_SITE_URL, linktarget,
                               get_person_redirect_link(pid),
                               get_person_redirect_link(pid), papers_string))
            h('<div class="more-mpid%s" id="aid_moreinfo">' % (pid))

            if papers and index < bconfig.PERSON_SEARCH_RESULTS_SHOW_PAPERS_PERSON_LIMIT:
                h((self._('Showing the') + ' %d ' + self._('most recent documents:')) % len(papers))
                h("<ul>")

                for paper in papers:
                    h("<li>%s</li>"
                           % (format_record(int(paper[0]), "ha")))

                h("</ul>")
            elif not papers:
                h("<p>" + self._('Sorry, there are no documents known for this person') + "</p>")
            elif index >= bconfig.PERSON_SEARCH_RESULTS_SHOW_PAPERS_PERSON_LIMIT:
                h("<p>" + self._('Information not shown to increase performances. Please refine your search.') + "</p>")

            h(('<span style="margin-left: 40px;">'
                        '<em><a rel="nofollow" href="%s/%s/%s" target="_blank" id="aid_moreinfolink">'
                        + self._('Publication List ') + '(%s)</a> (in a new window or tab)</em></span>')
                        % (CFG_SITE_URL, linktarget,
                           get_person_redirect_link(pid),
                           get_person_redirect_link(pid)))
            h('</div>')
            h('</div>')

        if new_person_link:
            link = "%s/person/action?confirm=True&pid=%s" % (CFG_SITE_URL, '-3')
            if search_ticket:
                for r in search_ticket['bibrefs']:
                    link = link + '&selection=%s' % str(r)
            h('<div>')
            h('<a rel="nofollow" href="%s">' % (link))
            h(self._("Create a new Person for your search"))
            h('</a>')
            h('</div>')

        return "\n".join(html)


    def tmpl_welcome_start(self):
        '''
        Shadows the behaviour of tmpl_search_pagestart
        '''
        return '<div class="pagebody"><div class="pagebodystripemiddle">'


    def tmpl_welcome_arxiv(self):
        '''
        SSO landing/welcome page.
        '''
        html = []
        h = html.append
        h('<p><b>Congratulations! you have now successfully connected to INSPIRE via arXiv.org!</b></p>')

        h('<p>Right now, you can verify your'
        ' publication records, which will help us to produce better publication lists and'
        ' citation statistics.'
        '</p>')

        h('<p>We are currently importing your publication list from arXiv.org .'
        'When we\'re done, you\'ll see a link to verify your'
        ' publications below; please claim the papers that are yours '
        ' and remove the ones that are not. This information will be automatically processed'
        ' or be sent to our operator for approval if needed, usually within 24'
        ' hours.'
        '</p>')
        h('If you have '
          'any questions or encounter any problems please contact us here: '
          '<a rel="nofollow" href="mailto:%s">%s</a></p>'
          % (CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL,
             CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL))

        return "\n".join(html)


    def tmpl_welcome(self):
        '''
        SSO landing/welcome page.
        '''
        html = []
        h = html.append
        h('<p><b>Congratulations! you have successfully logged in!</b></p>')

        h('<p>We are currently creating your publication list. When we\'re done, you\'ll see a link to correct your '
          'publications below.</p>')

        h('<p>When the link appears we invite you to confirm the papers that are '
          'yours and to reject the ones that you are not author of. If you have '
          'any questions or encounter any problems please contact us here: '
          '<a rel="nofollow" href="mailto:%s">%s</a></p>'
          % (CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL,
             CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL))

        return "\n".join(html)


    def tmpl_claim_profile(self):
        '''
        claim profile
        '''
        html = []
        h = html.append

        h('<p>Unfortunately it was not possible to automatically match your arXiv account to an INSPIRE person profile. Please choose the correct person profile from the list below.')

        h('If your profile is not in the list or none of them represents you correctly, please select the one which fits you best or choose '
          'to create a new one; keep in mind that no matter what your choice is, you will be able to correct your publication list until it contains all of your publications.'
          ' In case of any question please do not hesitate to contact us at <a rel="nofollow" href="mailto:%s">%s</a></p>' % (CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL,
             CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL))

        return "\n".join(html)


    def tmpl_profile_option(self, top5_list):
        '''
        show profile option
        '''
        html = []
        h = html.append

        h('<table border="0"> <tr>')
        for pid in top5_list:
            pid = int(pid)
            canonical_id = get_canonical_id_from_personid(pid)
            full_name = get_person_names_from_id(pid)
            name_length = 0
            most_common_name = ""
            for name in full_name:
                if len(name[0]) > name_length:
                    most_common_name = name [0]

            if len(full_name) > 0:
                name_string = most_common_name
            else:
                name_string = "[No name available]  "

            if len(canonical_id) > 0:
                canonical_name_string = "(" + canonical_id[0][0] + ")"
                canonical_id = canonical_id[0][0]
            else:
                canonical_name_string = "(" + pid + ")"
                canonical_id = pid

            h('<td>')
            h('%s ' % (name_string))
            h('<a href="%s/author/%s" target="_blank"> %s </a>' % (CFG_SITE_URL, canonical_id, canonical_name_string))
            h('</td>')
            h('<td>')
            h('<INPUT TYPE="BUTTON" VALUE="This is my profile" ONCLICK="window.location.href=\'welcome?chosen_profile=%s\'">' % (str(pid)))
            h('</td>')
            h('</tr>')
        h('</table>')
        h('</br>')
        if top5_list:
            h('If none of the above is your profile it seems that you cannot match any of the existing accounts.</br>Would you like to create one?')
            h('<INPUT TYPE="BUTTON" VALUE="Create an account" ONCLICK="window.location.href=\'welcome?chosen_profile=%s\'">' % (str(-1)))


        else:
            h('It seems that you cannot match any of the existig accounts.</br>Would you like to create one?')
            h('<INPUT TYPE="BUTTON" VALUE="Create an account" ONCLICK="window.location.href=\'welcome?chosen_profile=%s\'">' % (str(-1)))

        return "\n".join(html)

    def tmpl_profile_not_available(self):
        '''
        show profile option
        '''
        html = []
        h = html.append

        h('<p> Unfortunately the profile that you previously chose is no longer available. A new empty profile has been created. You will be able to correct '
          'your publication list until it contains all of your publications.</p>')
        return "\n".join(html)

    def tmpl_profile_assigned_by_user  (self):
        html = []
        h = html.append

        h('<p> Congratulations you have successfully claimed the chosen profile.</p>')
        return "\n".join(html)


    def tmpl_claim_stub(self, person='-1'):
        '''
        claim stub page
        '''
        html = []
        h = html.append

        h(' <ul><li><a rel="nofollow" href=%s> Login through arXiv.org </a> <small>' % bconfig.BIBAUTHORID_CFG_INSPIRE_LOGIN)
        h(' - Use this option if you have an arXiv account and have claimed your papers in arXiv.')
        h('(If you login through arXiv.org, INSPIRE will immediately verify you as an author and process your claimed papers.) </small><br><br>')
        h(' <li><a rel="nofollow" href=%s/person/%s?open_claim=True> Continue as a guest </a> <small>' % (CFG_SITE_URL, person))
        h(' - Use this option if you DON\'T have an arXiv account, or you have not claimed any paper in arXiv.')
        h('(If you login as a guest, INSPIRE will need to confirm you as an author before processing your claimed papers.) </small><br><br>')
        h('If you login through arXiv.org we can verify that you are the author of these papers and accept your claims rapidly, '
          'as well as adding additional claims from arXiv. <br>If you choose not to login via arXiv your changes will '
          'be publicly visible only after our editors check and confirm them, usually a few days.<br>  '
          'Either way, claims made on behalf of another author will go through our staff and may take longer to display. '
          'This applies as well to papers which have been previously claimed, by yourself or someone else.')
        return "\n".join(html)

    def tmpl_welcome_link(self):
        '''
        Creates the link for the actual user action.
        '''
        return '<a rel="nofollow" href=action?checkout=True><b>' + \
            self._('Correct my publication lists!') + \
            '</b></a>'

    def tmpl_welcome_personid_association(self, pid):
        """
        """
        canon_name = get_canonical_id_from_personid(pid)
        head = "<br>"
        if canon_name:
            body = ("Your arXiv.org account is associated "
                    "with person %s." % canon_name[0][0])
        else:
            body = ("Warning: your arXiv.org account is associated with an empty profile. "
                    "This can happen if it is the first time you log in and you do not have any "
                    "paper directly claimed in arXiv.org."
                    " In this case, you are welcome to search and claim your papers to your"
                    " new profile manually, or please contact us to get help.")

        body += ("<br>You are very welcome to contact us shall you need any help or explanation"
                 " about the management of"
                 " your profile page"
                 " in INSPIRE and it's connections with arXiv.org: "
                 '''<a href="mailto:authors@inspirehep.net?subject=Help on arXiv.org SSO login and paper claiming"> authors@inspirehep.net </a>''')
        tail = "<br>"

        return head + body + tail


    def tmpl_welcome_arXiv_papers(self, paps):
        '''
        Creates the list of arXiv papers
        '''
        plist = "<br><br>"
        if paps:
            plist = plist + "We have got and we are about to automatically claim for You the following papers from arXiv.org: <br>"
            for p in paps:
                plist = plist + "  " + str(p) + "<br>"
        else:
            plist = "We have got no papers from arXiv.org which we could claim automatically for You. <br>"
        return plist

    def tmpl_welcome_end(self):
        '''
        Shadows the behaviour of tmpl_search_pageend
        '''
        return '</div></div>'

    def tmpl_tickets_admin(self, tickets=[]):
        '''
        Open tickets short overview for operators.
        '''
        html = []
        h = html.append
        if len(tickets) > 0:
            h('List of open tickets: <br><br>')
            for t in tickets:
                h('<a rel="nofollow" href=%(cname)s#tabTickets> %(longname)s - (%(cname)s - PersonID: %(pid)s): %(num)s open tickets. </a><br>'
                  % ({'cname':str(t[1]), 'longname':str(t[0]), 'pid':str(t[2]), 'num':str(t[3])}))
        else:
            h('There are currently no open tickets.')
        return "\n".join(html)

    def tmpl_update_hep_name_headers(self):
        """
        Headers used for the hepnames update form
        """
        html = []
        html.append(r"""<style type="text/css">
                            .form1
                            {
                                margin-left: auto;
                                margin-right: auto;
                            }

                            #tblGrid {
                                margin-left: 5%;
                            }

                            #tblGrid td {
                                padding-left: 60px;
                            }

                            .form2
                            {
                                margin-left: 15%;
                                margin-right: 30%;
                            }

                            .span_float_right
                            {
                                float:right;
                            }

                            .span_float_left
                            {
                                float:left;
                            }
                       </style>
                       <script type="text/javascript" src="/js/hepname_update.js"></script>
                        """)
        return "\n".join(html)

    def tmpl_update_hep_name(self, full_name, display_name, email,
                             status, research_field_list,
                             institution_list, phd_advisor_list,
                             experiment_list, web_page):
        """
        Create form to update a hep name
        """
        # Prepare parameters
        try:
            phd_advisor = phd_advisor_list[0]
        except IndexError:
            phd_advisor = ''
        try:
            phd_advisor2 = phd_advisor_list[1]
        except IndexError:
            phd_advisor2 = ''
        is_active = is_retired = is_departed = is_deceased = ''
        if status == 'ACTIVE':
            is_active = 'selected'
        elif status == 'RETIRED':
            is_retired = 'selected'
        if status == 'DEPARTED':
            is_departed = 'selected'
        if status == 'DECEASED':
            is_deceased = 'selected'

        research_field_html = """
                              <TD><INPUT TYPE=CHECKBOX VALUE=ACC-PHYS  name=field>acc-phys</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=ASTRO-PH name=field>astro-ph</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=ATOM-PH name=field>atom-ph</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=CHAO-DYN name=field>chao-dyn</TD></TR>
                              <tr><TD><INPUT TYPE=CHECKBOX VALUE=CLIMATE name=field>climate</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=COMP name=field>comp</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=COND-MAT name=field>cond-mat</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=GENL-TH name=field>genl-th</TD></TR>
                              <tr><TD><INPUT TYPE=CHECKBOX VALUE=GR-QC name=field>gr-qc</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=HEP-EX name=field>hep-ex</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=HEP-LAT name=field>hep-lat</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=HEP-PH name=field>hep-ph</TD></TR>
                              <TR>
                              <TD><INPUT TYPE=CHECKBOX VALUE=HEP-TH name=field>hep-th</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=INSTR name=field>instr</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=LIBRARIAN name=field>librarian</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=MATH name=field>math</TD></TR>
                              <TR>
                              <TD><INPUT TYPE=CHECKBOX VALUE=MATH-PH name=field>math-ph</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=MED-PHYS name=field>med-phys</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=NLIN name=field>nlin</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=NUCL-EX name=field>nucl-ex</TD></TR>
                              <TR>
                              <TD><INPUT TYPE=CHECKBOX VALUE=NUCL-TH name=field>nucl-th</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=PHYSICS name=field>physics</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=PLASMA-PHYS name=field>plasma-phys</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=Q-BIO name=field>q-bio</TD></TR>
                              <TR>
                              <TD><INPUT TYPE=CHECKBOX VALUE=QUANT-PH name=field>quant-ph</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=SSRL name=field>ssrl</TD>
                              <TD><INPUT TYPE=CHECKBOX VALUE=OTHER name=field>other</TD>
                              """
        for research_field in research_field_list:
            research_field_html = research_field_html.replace('VALUE=' + research_field, 'checked ' + 'VALUE=' + research_field)

        institutions_html = ""
        institution_num = 1
        for institution_entry in institution_list:
            institution = """
                          <tr>
                          <td>&nbsp;   </td>
                          <td  class="cell_padding"><input name="aff.str" type="hidden">
                          <input type="text" name="inst%(institution_num)s" size="35" value =%(institution_name)s /></td>
                          <td  class="cell_padding"><select name="rank%(institution_num)s">
                          <option selected value=''> </option>
                          <option value='SENIOR'>Senior(permanent)</option>
                          <option value='JUNIOR'>Junior(leads to Senior)</option>
                          <option value='STAFF'>Staff(non-research)</option>
                          <option value='VISITOR'>Visitor</option>
                          <option value='PD'>PostDoc</option>
                          <option value='PHD'>PhD</option>
                          <option value='MAS'>Masters</option>
                          <option value='UG'>Undergrad</option></select></td>
                          <TD  class="cell_padding"><INPUT TYPE="TEXT" value=%(start_year)s name="sy%(institution_num)s" SIZE="4"/> &nbsp;&nbsp;
                          <INPUT TYPE="TEXT" value=%(end_year)s name="ey%(institution_num)s" SIZE="4"/></TD>
                          <TD  class="cell_padding"> <INPUT TYPE=CHECKBOX VALUE='Y' name="current%(institution_num)s">&nbsp;&nbsp;
                          <input type="button" value="Delete row" class="formbutton" onclick="removeRow(this);" />
                          </td>
                          </tr>
                          """% { 'institution_name': xml.sax.saxutils.quoteattr(institution_entry[0]),
                                 'start_year': xml.sax.saxutils.quoteattr(institution_entry[2]),
                                 'end_year': xml.sax.saxutils.quoteattr(institution_entry[3]),
                                 'institution_num': institution_num
                               }
            institution_num += 1
            institution = institution.replace('value=' + '\'' + institution_entry[1] + '\'', 'selected ' + 'VALUE=' + institution_entry[1])
            if institution_entry[4] == 'Current':
                institution = institution.replace("VALUE='Y'", 'checked ' + "VALUE='Y'")

            institutions_html += institution

        institutions_html += "<script>occcnt = %s; </script>" % (institution_num-1)
        experiments_html = """
                           <select name=exp id=exp multiple=yes>
                           <option value="">           </option>
                           <option value=AMANDA>AMANDA</option>
                           <option value=AMS>AMS</option>
                           <option value=ANTARES>ANTARES</option>
                           <option value=AUGER>AUGER</option>
                           <option value=BAIKAL>BAIKAL</option>
                           <option value=BNL-E-0877>BNL-E-0877</option>
                           <option value=BNL-LEGS>BNL-LEGS</option>
                           <option value=BNL-RHIC-BRAHMS>BNL-RHIC-BRAHMS</option>
                           <option value=BNL-RHIC-PHENIX>BNL-RHIC-PHENIX</option>
                           <option value=BNL-RHIC-PHOBOS>BNL-RHIC-PHOBOS</option>
                           <option value=BNL-RHIC-STAR>BNL-RHIC-STAR</option>
                           <option value=CDMS>CDMS</option>
                           <option value=CERN-LEP-ALEPH>CERN-LEP-ALEPH</option>
                           <option value=CERN-LEP-DELPHI>CERN-LEP-DELPHI</option>
                           <option value=CERN-LEP-L3>CERN-LEP-L3</option>
                           <option value=CERN-LEP-OPAL>CERN-LEP-OPAL</option>
                           <option value=CERN-LHC-ALICE>CERN-LHC-ALICE</option>
                           <option value=CERN-LHC-ATLAS>CERN-LHC-ATLAS</option>
                           <option value=CERN-LHC-B>CERN-LHC-B</option>
                           <option value=CERN-LHC-CMS>CERN-LHC-CMS</option>
                           <option value=CERN-LHC-LHCB>CERN-LHC-LHCB</option>
                           <option value=CERN-NA-060>CERN-NA-060</option>
                           <option value=CERN-NA-061>CERN-NA-061</option>
                           <option value=CERN-NA-062>CERN-NA-062</option>
                           <option value=CERN-PS-214>CERN-PS-214 (HARP)</option>
                           <option value=CESR-CLEO>CESR-CLEO</option>
                           <option value=CESR-CLEO-C>CESR-CLEO-C</option>
                           <option value=CESR-CLEO-II>CESR-CLEO-II</option>
                           <option value=CHIMERA>CHIMERA</option>
                           <option value=COBRA>COBRA</option>
                           <option value=COSY-ANKE>COSY-ANKE</option>
                           <option value=CUORE>CUORE</option>
                           <option value=COUPP>COUPP</option>
                           <option value=DAYA-BAY>DAYA-BAY</option>
                           <option value=DESY-DORIS-ARGUS>DESY-DORIS-ARGUS</option>
                           <option value=DESY-HERA-B>DESY-HERA-B</option>
                           <option value=DESY-HERA-H1>DESY-HERA-H1</option>
                           <option value=DESY-HERA-HERMES>DESY-HERA-HERMES</option>
                           <option value=DESY-HERA-ZEUS>DESY-HERA-ZEUS</option>
                           <option value=DESY-PETRA-MARK-J>DESY-PETRA-MARK-J</option>
                           <option value=DESY-PETRA-PLUTO-2>DESY-PETRA-PLUTO-2</option>
                           <option value=DESY-PETRA-TASSO>DESY-PETRA-TASSO</option>
                           <option value=DOUBLE-CHOOZ>DOUBLE-CHOOZ</option>
                           <option value=DRIFT>DRIFT</option>
                           <option value=EXO>EXO</option>
                           <option value=FERMI-LAT>FERMI-LAT</option>
                           <option value=FNAL-E-0687>FNAL-E-0687</option>
                           <option value=FNAL-E-0690>FNAL-E-0690</option>
                           <option value=FNAL-E-0706>FNAL-E-0706</option>
                           <option value=FNAL-E-0740>FNAL-E-0740 (D0 Run I)</option>
                           <option value=FNAL-E-0741>FNAL-E-0741 (CDF Run I)</option>
                           <option value=FNAL-E-0799>FNAL-E-0799 (KTeV)</option>
                           <option value=FNAL-E-0815>FNAL-E-0815 (NuTeV)</option>
                           <option value=FNAL-E-0823>FNAL-E-0823 (D0 Run II)</option>
                           <option value=FNAL-E-0830>FNAL-E-0830 (CDF Run II)</option>
                           <option value=FNAL-E-0831>FNAL-E-0831 (FOCUS)</option>
                           <option value=FNAL-E-0832>FNAL-E-0832 (KTeV)</option>
                           <option value=FNAL-E-0872>FNAL-E-0872 (DONUT)</option>
                           <option value=FNAL-E-0875>FNAL-E-0875 (MINOS)</option>
                           <option value=FNAL-E-0886>FNAL-E-0886 (FNPL)</option>
                           <option value=FNAL-E-0892>FNAL-E-0892 (USCMS)</option>
                           <option value=FNAL-E-0898>FNAL-E-0898 (MiniBooNE)</option>
                           <option value=FNAL-E-0904>FNAL-E-0904 (MUCOOL)</option>
                           <option value=FNAL-E-0906>FNAL-E-0906 (NuSea)</option>
                           <option value=FNAL-E-0907>FNAL-E-0907 (MIPP)</option>
                           <option value=FNAL-E-0907>FNAL-E-0918 (BTeV)</option>
                           <option value=FNAL-E-0907>FNAL-E-0973 (Mu2e)</option>
                           <option value=FNAL-E-0937>FNAL-E-0937 (FINeSSE)</option>
                           <option value=FNAL-E-0938>FNAL-E-0938 (MINERvA)</option>
                           <option value=FNAL-E-0954>FNAL-E-0954 (SciBooNE)</option>
                           <option value=FNAL-E-0961>FNAL-E-0961 (COUPP)</option>
                           <option value=FNAL-E-0974>FNAL-E-0974</option>
                           <option value=FNAL-LC>FNAL-LC</option>
                           <option value=FNAL-P-0929>FNAL-P-0929 (NOvA)</option>
                           <option value=FNAL-T-0962>FNAL-T-0962 (ArgoNeuT)</option>
                           <option value=FRASCATI-DAFNE-KLOE>FRASCATI-DAFNE-KLOE</option>
                           <option value=FREJUS-NEMO-3>FREJUS-NEMO-3</option>
                           <option value=GERDA>GERDA</option>
                           <option value=GSI-HADES>GSI-HADES</option>
                           <option value=GSI-SIS-ALADIN>GSI-SIS-ALADIN</option>
                           <option value=HARP>HARP</option>
                           <option value=HESS>HESS</option>
                           <option value=ICECUBE>ICECUBE</option>
                           <option value=ILC>ILC</option>
                           <option value=JLAB-E-01-104>JLAB-E-01-104</option>
                           <option value=KAMLAND>KAMLAND</option>
                           <option value=KASCADE-GRANDE>KASCADE-GRANDE</option>
                           <option value=KATRIN>KATRIN</option>
                           <option value=KEK-BF-BELLE>KEK-BF-BELLE</option>
                           <option value=KEK-BF-BELLE-II>KEK-BF-BELLE-II</option>
                           <option value=KEK-T2K>KEK-T2K</option>
                           <option value=LBNE>LBNE</option>
                           <option value=LIGO>LIGO</option>
                           <option value=LISA>LISA</option>
                           <option value=LSST>LSST</option>
                           <option value=MAGIC>MAGIC</option>
                           <option value=MAJORANA>MAJORANA</option>
                           <option value=MICE>MICE</option>
                           <option value=PICASSO>PICASSO</option>
                           <option value=PLANCK>PLANCK</option>
                           <option value=SDSS>SDSS</option>
                           <option value=SIMPLE>SIMPLE</option>
                           <option value=SLAC-PEP2-BABAR>SLAC-PEP2-BABAR</option>
                           <option value=SNAP>SNAP</option>
                           <option value=SSCL-GEM>SSCL-GEM</option>
                           <option value=SUDBURY-SNO>SUDBURY-SNO</option>
                           <option value=SUDBURY-SNO+>SUDBURY-SNO+</option>
                           <option value=SUPER-KAMIOKANDE>SUPER-KAMIOKANDE</option>
                           <option value=VERITAS>VERITAS</option>
                           <option value=VIRGO>VIRGO</option>
                           <option value=WASA-COSY>WASA-COSY</option>
                           <option value=WMAP>WMAP</option>
                           <option value=XENON>XENON</option>
                           </select>
                           """
        for experiment in experiment_list:
            experiments_html = experiments_html.replace('value=' + experiment, 'selected ' + 'value=' + experiment)

        html = []
        html.append("""<H4>Changes to Existing Records</H4>
                        <P>Send us your details (or someone else's).  See our <a href="http://www.slac.stanford.edu/spires/hepnames/help/adding.shtml">help
                         for additions</A>.<BR>If something doesnt fit in the form, just put it in
                        the comments section.</P>
                        <FORM name="hepnames_addition"
                        onSubmit="return OnSubmitCheck();"
                        action=http://www.slac.stanford.edu/cgi-bin/form-mail.pl
                        method=post><INPUT type=hidden value=nowhere   name=to id=tofield>
                        <INPUT type=hidden value="New HEPNames Posting" name=subject> <INPUT
                        type=hidden value=2bsupplied name=form_contact id=formcont> <INPUT
                        type=hidden value=/spires/hepnames/hepnames_msgupd.file name=email_msg_file>
                        <INPUT type=hidden value=/spires/hepnames/hepnames_resp_msg.file
                        name=response_msg_file><INPUT type=hidden value=0 name=debug>
                        <INPUT type=hidden value="1095498" name=key>
                        <INPUT type=hidden value="" name=field>
                        <INPUT type=hidden value="" name=current1>
                        <INPUT type=hidden value="" name=inst2><INPUT type=hidden value="" name=rank2>
                        <INPUT type=hidden value="" name=ey2><INPUT type=hidden value="" name=sy2>
                        <INPUT type=hidden value="" name=current2>
                        <INPUT type=hidden value="" name=inst3><INPUT type=hidden value="" name=rank3>
                        <INPUT type=hidden value="" name=ey3><INPUT type=hidden value="" name=sy3>
                        <INPUT type=hidden value="" name=current3>
                        <INPUT type=hidden value="" name=inst4><INPUT type=hidden value="" name=rank4>
                        <INPUT type=hidden value="" name=ey4><INPUT type=hidden value="" name=sy4>
                        <INPUT type=hidden value="" name=current4>
                        <INPUT type=hidden value="" name=inst5><INPUT type=hidden value="" name=rank5>
                        <INPUT type=hidden value="" name=ey5><INPUT type=hidden value="" name=sy5>
                        <INPUT type=hidden value="" name=current5>
                        <INPUT type=hidden value="" name=inst7><INPUT type=hidden value="" name=rank7>
                        <INPUT type=hidden value="" name=ey7><INPUT type=hidden value="" name=sy7>
                        <INPUT type=hidden value="" name=current7>
                        <INPUT type=hidden value="" name=inst6><INPUT type=hidden value="" name=rank6>
                        <INPUT type=hidden value="" name=ey6><INPUT type=hidden value="" name=sy6>
                        <INPUT type=hidden value="" name=current6>
                        <INPUT type=hidden value="" name=inst8><INPUT type=hidden value="" name=rank8>
                        <INPUT type=hidden value="" name=ey8><INPUT type=hidden value="" name=sy8>
                        <INPUT type=hidden value="" name=current8>
                        <INPUT type=hidden value="" name=inst9><INPUT type=hidden value="" name=rank9>
                        <INPUT type=hidden value="" name=ey9><INPUT type=hidden value="" name=sy9>
                        <INPUT type=hidden value="" name=current9>
                        <INPUT type=hidden value="" name=inst10><INPUT type=hidden value="" name=rank10>
                        <INPUT type=hidden value="" name=ey10><INPUT type=hidden value="" name=sy10>
                        <INPUT type=hidden value="" name=current10>
                        <INPUT type=hidden value="" name=inst11><INPUT type=hidden value="" name=rank11>
                        <INPUT type=hidden value="" name=ey11><INPUT type=hidden value="" name=sy11>
                        <INPUT type=hidden value="" name=current11>
                        <INPUT type=hidden value="" name=inst12><INPUT type=hidden value="" name=rank12>
                        <INPUT type=hidden value="" name=ey12><INPUT type=hidden value="" name=sy12>
                        <INPUT type=hidden value="" name=current12>
                        <INPUT type=hidden value="" name=inst13><INPUT type=hidden value="" name=rank13>
                        <INPUT type=hidden value="" name=ey13><INPUT type=hidden value="" name=sy13>
                        <INPUT type=hidden value="" name=current13>
                        <INPUT type=hidden value="" name=inst14><INPUT type=hidden value="" name=rank14>
                        <INPUT type=hidden value="" name=ey14><INPUT type=hidden value="" name=sy14>
                        <INPUT type=hidden value="" name=current14>
                        <INPUT type=hidden value="" name=inst15><INPUT type=hidden value="" name=rank15>
                        <INPUT type=hidden value="" name=ey15><INPUT type=hidden value="" name=sy15>
                        <INPUT type=hidden value="" name=current15>
                        <INPUT type=hidden value="" name=inst17><INPUT type=hidden value="" name=rank17>
                        <INPUT type=hidden value="" name=ey17><INPUT type=hidden value="" name=sy17>
                        <INPUT type=hidden value="" name=current17>
                        <INPUT type=hidden value="" name=inst16><INPUT type=hidden value="" name=rank16>
                        <INPUT type=hidden value="" name=ey16><INPUT type=hidden value="" name=sy16>
                        <INPUT type=hidden value="" name=current16>
                        <INPUT type=hidden value="" name=inst18><INPUT type=hidden value="" name=rank18>
                        <INPUT type=hidden value="" name=ey18><INPUT type=hidden value="" name=sy18>
                        <INPUT type=hidden value="" name=current18>
                        <INPUT type=hidden value="" name=inst19><INPUT type=hidden value="" name=rank19>
                        <INPUT type=hidden value="" name=ey19><INPUT type=hidden value="" name=sy19>
                        <INPUT type=hidden value="" name=current19>
                        <INPUT type=hidden value="" name=inst20><INPUT type=hidden value="" name=rank20>
                        <INPUT type=hidden value="" name=ey20><INPUT type=hidden value="" name=sy20>
                        <INPUT type=hidden value="" name=current20>
                        <INPUT type=hidden value="today" name=DV>
                        <TABLE class=form1>
                        <TBODY>
                        <TR>
                        <TD><STRONG>Full name</STRONG></TD>
                        <TD><INPUT SIZE=24 value=%(full_name)s name=authorname> <FONT SIZE=2>E.G.
                        Lampen, John Francis</FONT> </TD></TR>
                        <TR>
                        <TD><STRONG>Display Name</STRONG></TD>
                        <TD><INPUT SIZE=24 value=%(display_name)s name='dispname'> <FONT SIZE=2>E.G.
                        LampC)n, John </FONT><//TD></TR>
                        <TR>
                        <TD><STRONG> Your Email</STRONG></TD>
                        <TD><INPUT SIZE=24 value=%(email)s name='username' ID='username'><FONT SIZE=2>(<STRONG>REQ'D
                        </strong> but not displayed -  contact only)</font> </TD></TR>
                        <TR>
                        <TD><STRONG>Email </STRONG>(Public)</TD>
                        <TD><INPUT SIZE=24 value=%(email_public)s name='email' id='email'>
                        <input type='button' value='Same as Above' class='formbutton' onclick='copyem();'/>
                        </TD></TR><tr><TD><STRONG>Status</STRONG></TD><TD>
                        <SELECT NAME=status>
                        <OPTION %(is_active)s value=ACTIVE>Active</OPTION>
                        <OPTION %(is_retired)s value=RETIRED>Retired</OPTION>
                        <OPTION %(is_departed)s value=DEPARTED>Departed</OPTION>
                        <OPTION %(is_deceased)s value=DECEASED>Deceased</OPTION>
                        </SELECT></TD></TR>
                        <tr><TD><STRONG>Field of research</STRONG></TD><td> <table><tbody><tr>
                        %(research_field_html)s
                        </TR></TBODY></TABLE></TD></TR>
                        <table id="tblGrid" >
                        <tr>
                        <td>&nbsp;&nbsp;</td>
                        <td class="cell_padding"><strong> Institution History</strong><br>
                        <FONT size=2>Please take this name from <A href="http://inspirehep.net/Institutions"
                        target=_TOP>Institutions</A><FONT color=red><SUP>*</SUP></FONT></TD>
                        <td class="cell_padding"><strong>Rank</td>
                        <td class="cell_padding"><strong>Start Year  End Year</td>
                        <td class="cell_padding"><strong>Current</strong></td>
                        </tr>
                        %(institutions_html)s
                        </table>
                        <table><tr>
                        <a href="javascript:addRow();"> Click to add new Institution field row
                        <img src="/img/rightarrow.gif" ></a></tr></table>
                        <hr>
                        <table class="form2"><tbody><tr>
                        <TD><span class="span_float_right"><STRONG>Ph.D. Advisor</STRONG></span></TD>
                        <TD><span class="span_float_left"><INPUT SIZE=24 value=%(phd_advisor)s name=Advisor1> <FONT SIZE=2>E.G.
                        Beacom, John Francis</FONT> </span></TD></TR>
                        <tr><TD><span class="span_float_right"><STRONG>2nd Ph.D. Advisor</STRONG></span></TD>
                        <TD><span class="span_float_left"><INPUT SIZE=24 value=%(phd_advisor2)s name=Advisor2> <FONT SIZE=2>E.G.
                        Beacom, John Francis</FONT> </span></TD></TR>
                        <TD><span class="span_float_right"><STRONG>Experiments</STRONG></span>
                        <br /><span class="span_float_right"><FONT size=2>Hold the Control key to choose multiple current or past experiments <br> Experiments not listed can be added in the Comments field below </font></span></td>
                        <td><span class="span_float_left">
                        %(experiments_html)s
                        </span></td></tr>
                        <TR>
                        <TD><span class="span_float_right"><STRONG>Your web page</STRONG></span></TD>
                        <TD><span class="span_float_left"><INPUT SIZE=50 value=%(web)s name= URL></span></TD></TR>
                        <TR>
                        <TD><span class="span_float_right">Please send us your <STRONG>Comments</STRONG></span></td>
                        <TD><span class="span_float_left"><TEXTAREA NAME=Abstract ROWS=3 COLS=30></textarea><FONT SIZE=2>(not displayed)</FONT></span></TD></TR>
                        <tr><TD> <span class="span_float_right"><font size="1">SPAM Robots have been sending us submissions via this form, in order to prevent this we ask that you confirm that you are a real person by answering this question, which should be
                        easy for you, and hard for a SPAM robot. Cutting down on the extraneous submissions we get means that we can handle real requests faster.</font></span></td><td><span class="span_float_left">
                        <script type="text/javascript" src="http://www.slac.stanford.edu/spires/hepnames/spbeat.js">
                        </SCRIPT><br /><STRONG> How many people in image</STRONG>  <SELECT NAME=beatspam ID=beatspam> <OPTION VALUE=""> </OPTION>
                        <option value="1"> one person</option>
                        <option value="2"> two people</option><option value="3"> three people</option>
                        <option value="4"> more than three</option></select></span></td></tr>

                        </TBODY></TABLE><INPUT type=submit class="formbutton" value="Send Request"><br /><FONT
                        color=red><SUP>*</SUP></FONT>Institution name should be in the form given
                        in the <A href="http://inspirehep.net/Institutions"
                        target=_TOP>INSTITUTIONS</A> database<BR>(e.g. Harvard U. * Paris U.,
                        VI-VII * Cambridge U., DAMTP * KEK, Tsukuba). </FORM>
                        """% {'full_name': xml.sax.saxutils.quoteattr(full_name),
                              'display_name': xml.sax.saxutils.quoteattr(display_name),
                              'email': xml.sax.saxutils.quoteattr(email),
                              'email_public': xml.sax.saxutils.quoteattr(email),
                              'phd_advisor': xml.sax.saxutils.quoteattr(phd_advisor),
                              'phd_advisor2': xml.sax.saxutils.quoteattr(phd_advisor2),
                              'web': xml.sax.saxutils.quoteattr(web_page),
                              'is_active': is_active,
                              'is_retired': is_retired,
                              'is_departed': is_departed,
                              'is_deceased': is_deceased,
                              'research_field_html': research_field_html,
                              'institutions_html': institutions_html,
                              'experiments_html' : experiments_html
                             })
        return "\n".join(html)

# pylint: enable=C0301

