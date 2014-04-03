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


# from cgi import escape
# from urllib import quote
#
import invenio.bibauthorid_config as bconfig
from invenio.config import CFG_SITE_LANG
from invenio.config import CFG_SITE_URL, CFG_SITE_SECURE_URL, CFG_BASE_URL
from invenio.config import CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL, CFG_WEBAUTHORPROFILE_CFG_HEPNAMES_EMAIL
from invenio.bibformat import format_record
from invenio.session import get_session
from invenio.search_engine_utils import get_fieldvalues
from invenio.bibauthorid_config import PERSONID_EXTERNAL_IDENTIFIER_MAP, CREATE_NEW_PERSON
from invenio.bibauthorid_webapi import get_person_redirect_link, get_canonical_id_from_person_id, \
     get_person_names_from_id, get_person_info_by_pid
from invenio.bibauthorid_frontinterface import get_uid_of_author
from invenio.bibauthorid_frontinterface import get_bibrefrec_name_string
from invenio.bibauthorid_frontinterface import get_canonical_name_of_author
from invenio.messages import gettext_set_language, wash_language
from invenio.webuser import get_email
from invenio.htmlutils import escape_html
from jinja2 import DictLoader, Environment

# from invenio.textutils import encode_for_xml


class WebProfileMenu():

    def get_menu_items(self):
        return self.menu

    def _set_is_owner(self, is_owner):
        if isinstance(is_owner, bool):
            self.owner = is_owner

    def _set_is_admin(self, is_admin):
        if isinstance(is_admin, bool):
            self.is_admin = is_admin

    def _set_canonical_name(self, canonical_name):
        if isinstance(canonical_name, str):
            self.canonical_name = canonical_name

    def _configure_localisation(self, ln):
        self.localise = gettext_set_language(ln)

    def _set_active_menu_item(self, current_page):
        for item in self.menu:
            if item['page'] == current_page:
                item['active'] = True

    def _get_standard_menu_items(self):
        personalise = ""
        if self.owner:
            personalise = "Your "

        menu = [
            {
                'page': "profile",
                'text': "%s" % self.localise("View %sProfile" % personalise),
                "static": False,
                "active": False,
                "canonical_name": self.canonical_name,
                "disabled": self.canonical_name is ""
            },
            {
                'page': "manage_profile",
                'text': "%s" % self.localise("Manage %sProfile" % personalise),
                'static': False,
                'active': False,
                "canonical_name": self.canonical_name,
                "disabled": self.canonical_name is ""
            },
            {
                'page': "claim",
                'text': "%s" % self.localise("Manage %sPublications" % personalise),
                'static': False,
                'active': False,
                "canonical_name": self.canonical_name,
                "disabled": self.canonical_name is ""
            },
            {
                'page': "search",
                'text': "%s" % self.localise("Search Profiles"),
                'static': True,
                'active': False
            },
            {
                'page': "help",
                'text': "%s" % self.localise("Help"),
                'static': True,
                'active': False,
            }
        ]

        return menu

    def _get_admin_menu_items(self):
        admin_menu_items = self._get_standard_menu_items()
        open_tickets_item = {
            'page': "claim/tickets_admin",
            'text': "%s" % self.localise("Open Tickets"),
            'static': True,
            'active': False
        }
        admin_menu_items.append(open_tickets_item)
        return list(admin_menu_items)

    def _create_menu(self, current_page):
        if self.is_admin:
            self.menu = self._get_admin_menu_items()
        else:
            self.menu = self._get_standard_menu_items()

        self._set_active_menu_item(current_page)

    def __init__(self, canonical_name, current_page, ln, is_owner=False, is_admin=False):
        self._configure_localisation(ln)
        self._set_canonical_name(canonical_name)
        self._set_is_owner(is_owner)
        self._set_is_admin(is_admin)
        self._create_menu(current_page)


class WebProfilePage():


    def __init__(self, page, heading, no_cache=False):
        self.css_dir = CFG_BASE_URL + "/img"
        self.img_dir = CFG_BASE_URL + "/img"
        self.scripts_dir = CFG_BASE_URL + "/js"
        self.url = CFG_BASE_URL + "/author"

        self.scripts = [
                        "jquery-ui.min.js",
                        "jquery.form.js",
                        "jquery.dataTables.min.js",
                        "jquery-lightbox/js/jquery.lightbox-0.5.js",
                        "jquery.omniwindow.js",
                        # "jquery.blockUI.js",
                        "spin.min.js",
                        "sly.min.js",
                        "parsley.js",
                        "bootstrap.min.js",
                        "underscore-min.js",
                        "backbone.js",
                        "handlebars.js",
                        "bibauthorid.js",
                        "webauthorprofile.js",
                        ]

        self.stylesheets = [
                        "jquery-ui/themes/smoothness/jquery-ui.css",
                        "datatables_jquery-ui.css",
                        "bibauthorid.css",
                        "bootstrap.min.css"
                        ]

        self.template_files = {
                        'head.html': """\
                                {% if no_cache %}
                        <!-- Meta -->
                        <META HTTP-EQUIV="Pragma" CONTENT="no-cache">
                        <META HTTP-EQUIV="Cache-Control" CONTENT="no-cache">
                        <META HTTP-EQUIV="Pragma-directive" CONTENT="no-cache">
                        <META HTTP-EQUIV="Cache-Directive" CONTENT="no-cache">
                        <META HTTP-EQUIV="Expires" CONTENT="0">
                        {% endif %}

                {% if scripts %}
                <!-- Scripts -->
                {% for item in scripts %}<script type="text/javascript" src="{{ scripts_dir }}/{{ item }}"></script>
                {% endfor %}
                {% endif %}

                <script type="text/x-mathjax-config">
                MathJax.Hub.Config({
                        tex2jax: {inlineMath: [['$','$']],
                        processEscapes: true},
                        showProcessingMessages: false,
                        messageStyle: "none"
                        });
                </script>
                <script src="/MathJax/MathJax.js?config=TeX-AMS_HTML" type="text/javascript">
                </script>

                {% if stylesheets %}
                <!-- Stylesheets -->
                {% for item in stylesheets %}<link rel="stylesheet" type="text/css" href="{{ css_dir }}/{{ item }}" />
                {% endfor %}
                {% endif %}
                """,
                'profile_menu.html': """
                <span class="bsw"><ul id="authorid_menu" class="nav nav-pills">
                {% for item in menu %}\
                        <li{{ ' class="active"' if item.active }}{{ ' class="disabled"' if item.disabled }}>
                <a href="{{ url }}/{{ item.page }}{% if not item.static %}/{{ item.canonical_name }}{% endif %}">{{ item.text }}</a>
                </li>
                {% endfor %}
                </ul></span>
                """,
                'index.html': """\

{% if bootstrap %}<div class="hidden" id="jsbootstrap">{{ bootstrap|e }}</div>{% endif %}
<div class="ow-overlay ow-closed"></div>
<span class="bsw">
{% if debug %}{% include 'debug_block.html' %}{% endif %}



<div id="person_name"><h1 class="authornametitle">{{ title }}</h1></div>
<div id="person_menu">\
        {% if menu %}{% include 'profile_menu.html' %}{% endif %}
</div>



<div id="bai_content">
{% block content %}{% endblock %}
</div>
</span>
""",
'generic_wrapper.html': """
{% extends "index.html" %}
{% block content %}
{{ html|safe }}
{% endblock%}
""",
'debug_block.html': """
<div id="debug_info"><span class="bsw">
<table class="table table-striped">
<caption><h2>Debug Information</h2></caption>
<thead>
<tr>
<th>Key</th>
<th>Value</th>
</tr>
</thead>
<tbody>
{% for key, value in debug.iteritems() %}
<tr>
<td>{{ key|e}}</td>
<td>{{ value|e }}</td>
</tr>
{% endfor %}
</tbody>
</table>
</span></div>
"""
}

        self._initialise_class_variables()
        self.no_cache = no_cache
        self.heading = heading
        self.page = page
        self.bootstrap_data = None

        self.loader = DictLoader(self.template_files)
        self.environment = Environment(loader=self.loader)


    def _initialise_class_variables(self):
        self.menu = None
        self.debug = None

    def create_profile_menu(self, canonical_name, ln, is_owner=False, is_admin=False):
        menu = WebProfileMenu(canonical_name, self.page, ln, is_owner, is_admin)
        self.menu = menu.get_menu_items()

    def add_profile_menu(self, menu):
        self.menu = menu.get_menu_items()

    def add_debug_info(self, debug):
        self.debug = debug

    def add_bootstrapped_data(self, data):
        self.bootstrap_data = data

    def get_head(self):
        if self.page.lower() != 'profile' and "webauthorprofile.js" in self.scripts:
            self.scripts.remove("webauthorprofile.js")

        return self.environment.get_template("head.html").render({
            'no_cache': self.no_cache,
            'scripts': self.scripts,
            'stylesheets': self.stylesheets,
            'css_dir': self.css_dir,
            'scripts_dir': self.scripts_dir
        })

    def get_body(self):
        return self.environment.get_template("index.html").render({
            'title': self.heading,
            'menu': self.menu,
            'url': self.url,
            'debug': self.debug,
            'bootstrap': self.bootstrap_data
        })

    def get_wrapped_body(self, content):
        return self.environment.get_template("generic_wrapper.html").render({
            'title': self.heading,
            'menu': self.menu,
            'url': self.url,
            'html': content,
            'debug': self.debug,
            'bootstrap': self.bootstrap_data
        })


import xml.sax.saxutils

class Template:
    """Templating functions used by aid"""

    # Class level variable for profile menu bar
    DEFAULT_PROFILE_MENU_ITEMS = [
                ("/author/profile/","View Profile",False),
                ("/author/manage_profile/","Manage Profile",False),
                ("/author/claim/","Manage Publications",False),
                ("/author/profile/","Help",True)
    ]

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
                                     'confirm_operation': '%s transaction%s successfully ticketized.',
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
                color = 'background: #FFC2C2;'
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


    def tmpl_merge_transaction_box(self, teaser_key, messages, show_close_btn=True):
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
        transaction_message_dict = { 'confirm_success': '%s merge transaction%s successfully executed.',
                                     'confirm_failure': '%s merge transaction%s failed. This happened because there is at least one profile in the merging list that is either connected to a user or it has claimed papers.'
                                     ' Please edit the list accordingly.',
                                     'confirm_operation': '%s merge transaction%s successfully ticketized.'}

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
                color = 'background: #FFC2C2;'

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

    def tmpl_login_transaction_box(self, teaser_key, messages, show_close_btn=True):
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
        transaction_message_dict = { 'confirm_success': 'You are now connected to Inspire through arXiv.'}

        teaser = self._(transaction_teaser_dict[teaser_key])

        html = []
        h = html.append
        for key in transaction_message_dict.keys():
            same_kind = [mes for mes in messages if mes == key]
            trans_no = len(same_kind)

            color = ''
            if teaser_key == 'failure':
                color = 'background: #FFC2C2;'

            message = self._(transaction_message_dict[key])

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
        notification_message_dict = {'attribute_papers': 'You are about to assign the following paper%s:' }

        teaser = self._(notification_teaser_dict[teaser_key])
        arg = ''
        if len(bibrefs) > 1:
            arg = 's'
        message = self._(notification_message_dict[message_key] % (arg))

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
        h('  <div style="background: #FFC2C2; margin-top: 20px; padding: 0pt 0.7em; color:#000000;" class="ui-state-error ui-corner-all">')
        h('    <p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-alert"></span>')
        h('    <strong>%s</strong> %s' % (teaser, message))

        if show_close_btn:
            h('    <span style="float:right; margin-right: 0.3em;"> ')
            h('<a rel="nofollow" href="#" style="color: #000000; border: 1px #000000 solid;" class="aid_close-notify">X</a></span>')

        h('</p> </div>')
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
        h('<a rel="nofollow" id="checkout" href="%s/author/claim/action?checkout=True">' % (CFG_SITE_URL,) + self._('Click here to review the transactions.') + '</a>')
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
        message = self._(error_message_dict[message_key] % (arg))

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
        h('<a rel="nofollow" id="checkout" href="%s/author/claim/action?cancel_search_ticket=True">' % (CFG_SITE_URL,) + self._('Quit searching.') + '</a>')

        if show_close_btn:
            h('    <span style="float:right; margin-right: 0.3em;"><a rel="nofollow" href="#" class="aid_close-notify">X</a></span></p>')

        h(' </div>')
        h('</div>')
        h('<p>&nbsp;</p>')

        return "\n".join(html)


    def tmpl_merge_ticket_box(self, teaser_key, message_key, primary_cname):

        message = self._('When you merge a set of profiles, all the information stored will be assigned to the primary profile. This includes papers, ids or citations.'
                       ' After merging, only the primary profile will remain in the system, all other profiles will be automatically deleted.</br>')

        error_teaser_dict = {'person_search': message }
        error_message_dict = {'merge_profiles': 'You are about to merge the following profiles:' }

        teaser = self._(error_teaser_dict[teaser_key])
        message = self._(error_message_dict[message_key])

        html = []
        h = html.append
        h('<div id="aid_notification_' + teaser_key + '" class="ui-widget ui-alert">')
        h('  <div style="margin-top: 20px; padding: 0pt 0.7em;" class="ui-state-highlight ui-corner-all">')
        h('    <p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-info"></span>')
        h('    <strong>%s</strong> </br>%s ' % (teaser, message))
        h("<table id=\"mergeList\" >\
            <tr></tr>\
              <th></th>\
              <th></th>\
              <th></th>\
              <th></th>\
            <tr></tr>")

        h("<tr><td></td><td><a id=\"primaryProfile\" href='%s/author/profile/%s'target='_blank'>%s</a></td><td id=\"primaryProfileTd\">primary profile</td><td></td></tr>"
          % (CFG_SITE_URL, primary_cname, primary_cname))
        # for profile in profiles:
        #     h("<li><a href='%s'target='_blank' class=\"profile\" >%s</a><a class=\"setPrimaryProfile\">Set as primary</a> <a class=\"removeProfile\">Remove</a></li>"
        #            % (profile, profile))
        h("</table>")
        h('<div id="mergeListButtonWrapper">')
        h('<form action="%s/author/claim/action" method="get"><input type="hidden" name="cancel_merging" value="True" /> <input type="hidden" name="primary_profile" value="%s" />  <input type="submit" id="cancelMergeButton" class="aid_btn_red" value="%s" /></form>' %
                    (CFG_SITE_URL, primary_cname, self._('Cancel merging')))
        h('<form action="%s/author/claim/action" method="get"><input type="hidden" name="merge" value="True" /><input type="submit" id="mergeButton" class="aid_btn_green" value="%s" /></form>' %
                    (CFG_SITE_URL, self._('Merge profiles')))
        h(' </div>')
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
                   "bibauthorid.js",
                   "bootstrap.min.js"]

        result.append('<link rel="stylesheet" type="text/css" href='
                      '"%s/jquery-ui/themes/smoothness/jquery-ui.css" />'
                      % (imgcss_path))
        result.append('<link rel="stylesheet" type="text/css" href='
                      '"%s/datatables_jquery-ui.css" />'
                      % (imgcss_path))
        result.append('<link rel="stylesheet" type="text/css" href='
                      '"%s/bibauthorid.css" />'
                      % (imgcss_path))

        result.append('<link rel="stylesheet" type="text/css" href='
                      '"%s/bootstrap.min.css" />'
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
                '<a rel="nofollow" id="aid_reset_gr" class="aid_grey op_action" href="%(url)s/author/claim/action?reset=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reset_gray.png" alt="%(alt_forget)s" style="margin-left:22px;" />'
                '%(forget_text)s</a><br>')
        stri = stri + (
                '<a rel="nofollow" id="aid_repeal" class="aid_grey op_action" href="%(url)s/author/claim/action?repeal=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reject_gray.png" alt="%(alt_repeal)s" style="margin-left:22px;"/>'
                '%(repeal_text)s</a><br>'
                '<a rel="nofollow" id="aid_to_other" class="aid_grey op_action" href="%(url)s/author/claim/action?to_other_person=True&selection=%(ref)s">'
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
                                                                       }):
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
                '<a rel="nofollow" id="aid_confirm" class="aid_grey op_action" href="%(url)s/author/claim/action?confirm=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_check_gray.png" alt="%(alt_confirm)s" style="margin-left: 22px;" />'
                '%(confirm_text)s</a><br>'
                '<a rel="nofollow" id="aid_to_other" class="aid_grey op_action" href="%(url)s/author/claim/action?to_other_person=True&selection=%(ref)s">'
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
                                                                       }):
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
        # batchprocess?mconfirm=True&bibrefs=['100:17,16']&pid=1
        string = ('<!--0!--><span id="aid_status_details"> '
                '<a rel="nofollow" id="aid_confirm" class="op_action" href="%(url)s/author/claim/action?confirm=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_check.png" alt="%(alt_confirm)s" />'
                '%(confirm_text)s</a><br />'
                '<a rel="nofollow" id="aid_repeal" class="op_action" href="%(url)s/author/claim/action?repeal=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reject.png" alt="%(alt_repeal)s" />'
                '%(repeal_text)s</a> <br />'
                '<a rel="nofollow" id="aid_to_other" class="op_action" href="%(url)s/author/claim/action?to_other_person=True&selection=%(ref)s">'
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
            h('<div><a rel="nofollow" id="clam_for_myself" href="%s/author/claim/action?confirm=True&%s&pid=%s" '
                    'class="confirmlink"><button type="button">%s</div></br>' % (CFG_SITE_URL, bibs, str(pid), self._("Claim for yourself")))

        if last_viewed_pid:
            h('<div><a rel="nofollow" id="clam_for_last_viewed" href="%s/author/claim/action?confirm=True&%s&pid=%s" '
                    'class="confirmlink"><button type="button">%s</div></br>' % (CFG_SITE_URL, bibs, str(last_viewed_pid[0]), self._('Assign to') + str(last_viewed_pid[1])))

        if search_enabled:
            h('<div><a rel="nofollow" id="claim_search" href="%s/author/claim/action?to_other_person=True&%s" '
                    'class="confirmlink"><button type="button">%s</div></br>' % (CFG_SITE_URL, bibs, self._('Search for a person to assign the paper to')))

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
        no_papers_html.append('%s' % self._(verbiage_dict['no_doc_string']))
        no_papers_html.append('</strong></div>')

        if not bibrecids or not person_id:
            return "\n".join(no_papers_html)

        pp_html = []
        h = pp_html.append

        h('<form id="%s" action="/author/claim/action" method="post">'
                   % (form_id))

        # +self._(' On all pages: '))
        h('<div class="aid_reclist_selector">')
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
        h('<input type="submit" name="assign" value="%s" class="aid_btn_blue" />' % self._(verbiage_dict['b_confirm']))
        h('<input type="submit" name="reject" value="%s" class="aid_btn_blue" />' % self._(verbiage_dict['b_repeal']))
        h('<input type="submit" name="to_other_person" value="%s" class="aid_btn_blue" />' % self._(verbiage_dict['b_to_others']))
        # if show_reset_button:
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
                                            verbiage_dict=buttons_verbiage_dict['record_undecided'])

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

        # +self._(' On all pages: '))
        h('<div class="aid_reclist_selector">')
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
        h('<input type="submit" name="assign" value="%s" class="aid_btn_blue" />' % verbiage_dict['b_confirm'])
        h('<input type="submit" name="reject" value="%s" class="aid_btn_blue" />' % verbiage_dict['b_repeal'])
        h('<input type="submit" name="to_other_person" value="%s" class="aid_btn_blue" />' % verbiage_dict['b_to_others'])
        # if show_reset_button:
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
        h('<form id="review" action="/author/claim/batchprocess" method="post">')
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
            h('    <td><a rel="nofollow" href="%s/author/claim/batchprocess?selected_bibrecs=%s&mfind_bibref=claim">'% (CFG_SITE_URL, paper) +
                self._('Review Transaction') + '</a></td>')
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

        h('<div class="accordion" id="accordion1">')
        h('<div class="accordion-group">')

        # Define accordion heading
        h('<span class=\"bsw\"><div class="accordion-heading">')
        h('<a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion1" href="#collapseVariants">')
        h('%s</a>' % self._('View name variants'))
        h('</div>')

        h('<div id="collapseVariants" class="accordion-body collapse">')  # Start variants accordion body

        # Populate accordion with name variants
        h('<div class="accordion-inner">')
        for name in names:
            h("%s (%s)<br>" % (name[0], name[1]))
        h('</div>')

        h('</div>')  # Close variants accordion body
        h('</div>')  # Close accordion group
        h('</div></span>')  # Close accordion

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

            userid = get_uid_of_author(person_id)
            if userid:
                h('<img src="%s/img/webbasket_user.png" alt="%s" width="30" height="30" />' %
                   (CFG_SITE_URL, self._("The author has an internal ID!")))
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
                    elif info[0] in ['assign', 'reject']:
                        actions.append(info)

                if 'delete' in ticket_links:
                    h(('<strong>Ticket number: %(tnum)s </strong> <a rel="nofollow" id="cancel" href=%(url)s/author/claim/action?cancel_rt_ticket=True&selection=%(tnum)s&pid=%(pid)s>' + self._(' Delete this ticket') + ' </a>')
                  % ({'tnum':t[1], 'url':CFG_SITE_URL, 'pid':str(person_id)}))

                if 'commit' in ticket_links:
                    h((' or <a rel="nofollow" id="commit" href=%(url)s/author/claim/action?commit_rt_ticket=True&selection=%(tnum)s&pid=%(pid)s>' + self._(' Commit this entire ticket') + ' </a> <br>')
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
                        h('<a rel="nofollow" id="action" href="%(url)s/author/claim/action?%(action)s=True&pid=%(pid)s&selection=%(bib)s&rt_id=%(rt)s">%(action)s - %(name)s on %(title)s </a>'
                      % ({'action': a[0], 'url': CFG_SITE_URL,
                          'pid': str(person_id), 'bib':a[1],
                          'name': pname, 'title': title, 'rt': t[1]}))
                    else:
                        h('%(action)s - %(name)s on %(title)s'
                      % ({'action': a[0], 'name': pname, 'title': title}))

                    if 'del_entry' in ticket_links:
                        h(' - <a rel="nofollow" id="action" href="%(url)s/author/claim/action?cancel_rt_ticket=True&pid=%(pid)s&selection=%(bib)s&rt_id=%(rt)s&rt_action=%(action)s"> Delete this entry </a>'
                      % ({'action': a[0], 'url': CFG_SITE_URL,
                          'pid': str(person_id), 'bib': a[1], 'rt': t[1]}))

                    h(' - <a rel="nofollow" id="show_paper" target="_blank" href="%(url)s/record/%(record)s"> View record <br>' % ({'url':CFG_SITE_URL, 'record':str(bibrec)}))
                h('</dd>')
                h('</dd><br>')
                # h(str(open_rt_tickets))
            h("  </div>")

        if 'data' in show_tabs:
            h('  <div id="tabData">')
            r = verbiage_dict['data_ns']
            h('<noscript><h5>%s</h5></noscript>' % r)
            full_canonical_name = str(get_canonical_id_from_person_id(person_id))

            if '.' in str(full_canonical_name) and not isinstance(full_canonical_name, int):
                canonical_name = full_canonical_name[0:full_canonical_name.rindex('.')]
            else:
                canonical_name = str(person_id)

            h('<div> <strong> Person id </strong> <br> %s <br>' % person_id)
            h('<strong> <br> Canonical name setup </strong>')
            h('<div style="margin-top: 15px;"> Current canonical name: %s' % full_canonical_name)
            h('<form method="GET" action="%s/author/claim/action" rel="nofollow">' % CFG_SITE_URL)
            h('<input type="hidden" name="set_canonical_name" value="True" />')
            h('<input name="canonical_name" id="canonical_name" type="text" style="border:1px solid #333; width:500px;" value="%s" /> ' % canonical_name)
            h('<input type="hidden" name="pid" value="%s" />' % person_id)
            h('<input type="submit" value="set canonical name" class="aid_btn_blue" />')

            h('<br>NOTE: If the canonical ID is without any number (e.g. J.Ellis), it will take the first available number. ')
            h('If the canonical ID is complete (e.g. J.Ellis.1) that ID will be assigned to the current person ')
            h('and if another person had that ID, he will lose it and get a new one. </form>')
            h('</div>')
            userid = get_uid_of_author(person_id)
            h('<div> <br>')
            h('<strong> Internal IDs </strong> <br>')
            if userid:
                email = get_email(int(userid))
                h('UserID: INSPIRE user %s is associated with this profile with email: %s' % (str(userid), str(email)))
            else:
                h('UserID: There is no INSPIRE user associated to this profile!')
            h('<br></div>')

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
        h('<form id="review" action="/author/claim/action" method="post">')
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
                h('<option value="" >-- ' + self._('Ignore') + ' --</option>')
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
                    h(('%s' + self._(' --  With name: ')) % (fv))
                    # , bibrefs_auto_assigned[person]["bibrecs"][recid][0][1]))
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
                    # h('<input type="hidden" name="bibrecgroup%s" value="%s" />'
                    #          % (recid, asbibref))
                    h('</div>')

        h('<div style="text-align:center;">')
        h('  <input type="submit" class="aid_btn_green" name="bibref_check_submit" value="Accept" />')
        h('  <input type="submit" class="aid_btn_blue" name="cancel_stage" value="Delete all transactions" />')
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

    @staticmethod
    def tmpl_profile_navigation_bar(person_info, ln, active, menu_items=None):
        """
        Generates a profile specific navigation bar.

        The menu_items parameter is a list of tuples with three components.

        The third component is a boolean that represents whether the content is static, i.e. It is not specific to
        a particular profile. Set it to False if the canonical name of the profile should be appended after the route.
        True indicates that the content is static and remains the same regardless of the profile and thus will not append
        the canonical name of the profile to the route.

        @param person_info: A dict describing a person, must contain key 'canonical_name'
        @param ln: Localisation
        @param active: Sets a menu item to active if it contains the passed substring.
        @param menu_items: List of 3-tuples e.g. ("/path/of/route/","Menu Item Name",False)
        @return: HTML markup wrapped in 'ul' tags
        @rtype: string
        """
        # Default navigation bar content
        if menu_items is None:
            menu_items = Template.DEFAULT_PROFILE_MENU_ITEMS
        _ = gettext_set_language(ln)
        navigation_bar = "<span class=\"bsw\"><ul id=\"authorid_menu\" class=\"nav nav-pills\">"

        for item in menu_items:
            (rel_url, link_text, static) = item
            if not static:
                if person_info['canonical_name']:
                    rel_url += str(person_info['canonical_name'])
            link_text = _(link_text)

            if active.lower() in link_text.lower():
                navigation_bar += "<li class=\"bsw active\"><a href=\"%s%s\">%s</a></li>" % (CFG_SITE_URL, rel_url, link_text)
            else:
                navigation_bar += "<li><a href=\"%s%s\">%s</a></li>" % (CFG_SITE_URL, rel_url, link_text)

        return navigation_bar + "</ul></span>"

    def tmpl_person_menu(self, pid, ln):
        '''
        Generate the menu bar
        '''

        person_info = get_person_info_by_pid(pid)
        profile_menu = Template.tmpl_profile_navigation_bar(person_info, ln, "Manage Publications")
        return "\n" + profile_menu

    def tmpl_person_menu_admin(self, pid, ln):
        '''
        Generate the menu bar
        '''
        person_info = get_person_info_by_pid(pid)
        menu_items = list(Template.DEFAULT_PROFILE_MENU_ITEMS)
        menu_items.append(("/author/claim/tickets_admin", "Open Tickets", True))
        profile_menu = Template.tmpl_profile_navigation_bar(person_info, ln, "Manage Publications", menu_items)

        return "\n" + profile_menu

    def tmpl_ticket_final_review(self, req, mark_yours=[], mark_not_yours=[],
                                 mark_theirs=[], mark_not_theirs=[], autoclaim=False):
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


        def mk_ticket_row(ticket, autoclaim = False):
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

            # h("Debug: " + str(ticket) + "<br />")
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
            h('<a rel="nofollow" href="%s/author/claim/action?checkout_remove_transaction=%s ">'
              'Cancel'
              '</a>' % (CFG_SITE_URL, ticket['bibref']))
            h('</td>')

            return "\n".join(html)


        session = get_session(req)
        pinfo = session["personinfo"]
        ulevel = pinfo["ulevel"]

        html = []
        h = html.append

        # h(html_icon_legend())

        if "checkout_faulty_fields" in pinfo and pinfo["checkout_faulty_fields"]:
            h(self.tmpl_error_box('sorry', 'check_entries'))

        if ("checkout_faulty_fields" in pinfo
            and pinfo["checkout_faulty_fields"]
            and "tickets" in pinfo["checkout_faulty_fields"]):
            h(self.tmpl_error_box('error', 'provide_transaction'))

        # h('<div id="aid_checkout_teaser">' +
        #          self._('Almost done! Please use the button "Confirm these changes" '
        #                 'at the end of the page to send this request to an operator '
        #                 'for review!') + '</div>')

        h('<div id="aid_person_names" '
          'class="ui-tabs ui-widget ui-widget-content ui-corner-all"'
          'style="padding:10px;">')

        h("<h4>" + self._('Please provide your information') + "</h4>")
        h('<form id="final_review" action="%s/author/claim/action" method="post">'
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
        if not autoclaim:
            h(('  <input type="submit" name="checkout_continue_claiming" class="aid_btn_green" value="%s" />')
              % self._("Continue claiming*"))
        h(('  <input type="submit" name="checkout_submit" class="aid_btn_green" value="%s" />')
          % self._("Confirm these changes**"))
        h('<span style="margin-left:150px;">')
        if not autoclaim:
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
                    h(mk_ticket_row(ticket, autoclaim))
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
                    h(mk_ticket_row(ticket, autoclaim))
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
                h(mk_ticket_row(ticket, autoclaim))
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
                h(mk_ticket_row(ticket, autoclaim))
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

    def tmpl_choose_profile_search_new_person_generator(self):
        def stub():
            text = self._("Create new profile")
            link = "%s/author/claim/action?associate_profile=True&pid=%s" % (CFG_SITE_URL, str(-1))
            return text, link

        return stub

    def tmpl_assigning_search_new_person_generator(self, bibrefs):
        def stub():
            text = self._("Create a new Person")
            link = "%s/author/claim/action?confirm=True&pid=%s" % (CFG_SITE_URL, str(CREATE_NEW_PERSON))

            for r in bibrefs:
                link = link + '&selection=%s' % str(r)

            return text, link

        return stub

    def tmpl_choose_profile_search_button_generator(self):
        def stub(pid, search_param):
            text = self._("This is my profile")
            parameters = [('associate_profile', True), ('pid', str(pid)), ('search_param', search_param)]
            link = "%s/author/claim/action" % (CFG_SITE_URL)
            css_class = ""
            to_disable = True

            return text, link, parameters, css_class , to_disable

        return stub

    def tmpl_assigning_search_button_generator(self, bibrefs):
        def stub(pid, search_param):
            text = self._("Assign paper")
            parameters = [('confirm', True), ('pid', str(pid)), ('search_param', search_param)]
            for r in bibrefs:
                parameters.append(('selection', str(r)))

            link = "%s/author/claim/action" % (CFG_SITE_URL)
            css_class = ""
            to_disable = False

            return text, link, parameters, css_class, to_disable

        return stub

    def merge_profiles_button_generator(self):
        def stub(pid, search_param):
            text = self._("Add to merge list")
            parameters = []
            link = ""
            css_class = "addToMergeButton"
            to_disable = False

            return text, link, parameters, css_class, to_disable

        return stub

    def tmpl_choose_profile_search_bar(self):
        def stub(search_param):
            activated = True
            parameters = [('search_param', search_param)]
            link = "%s/author/choose_profile" % ( CFG_SITE_URL, )
            return activated, parameters, link

        return stub

    def tmpl_general_search_bar(self):
        def stub(search_param,):
            activated = True
            parameters = [('q', search_param)]
            link = "%s/author/search"  % ( CFG_SITE_URL, )
            return activated, parameters, link

        return stub

    def tmpl_merge_profiles_search_bar(self, primary_profile):
        def stub(search_param):
            activated = True
            parameters = [('search_param', search_param), ('primary_profile', primary_profile)]
            link = "%s/author/merge_profiles"  % ( CFG_SITE_URL, )
            return activated, parameters, link

        return stub

    def tmpl_author_search(self, query, results, shown_element_functions):
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

        if not query:
            query = ""

        html = []
        h = html.append

        search_bar_activated = False
        if 'show_search_bar' in shown_element_functions.keys():
            search_bar_activated, parameters, link = shown_element_functions['show_search_bar'](query)

        if search_bar_activated:
            h('<div class="fg-toolbar ui-toolbar ui-widget-header ui-corner-tl ui-corner-tr ui-helper-clearfix" id="aid_search_bar">')
            h('<form id="searchform" action="%s" method="GET">' % (link,))
            h('Find author clusters by name. e.g: <i>Ellis, J</i>: <br>')

            for param in parameters[1:]:
                h('<input type="hidden" name=%s value=%s>' % (param[0], param[1]))

            h('<input placeholder="Search for a name, e.g: Ellis, J" type="text" name=%s style="border:1px solid #333; width:500px;" '
                        'maxlength="250" value="%s" class="focus" />' % (parameters[0][0], parameters[0][1]))
            h('<input type="submit" value="Search" />')
            h('</form>')
            if 'new_person_gen' in shown_element_functions.keys():
                new_person_text, new_person_link = shown_element_functions['new_person_gen']()
                h('<a rel="nofollow" href="%s" ><button type="button" id="new_person_link">%s' % (new_person_link, new_person_text))
                h('</button></a>')
            h('</div>')

        if not results and not query:
            h('</div>')
            return "\n".join(html)

        if query and not results:
            authemail = CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL
            h(('<strong>' + self._("We do not have a publication list for '%s'." +
                                 " Try using a less specific author name, or check" +
                                 " back in a few days as attributions are updated " +
                                 "frequently.  Or you can send us feedback, at ") +
                                 "<a rel='nofollow' href=\"mailto:%s\">%s</a>.</strong>") % (query, authemail, authemail))
            h('</div>')
            return "\n".join(html)

        show_action_button = False
        if 'button_gen' in shown_element_functions.keys():
            show_action_button = True

        show_status = False
        if 'show_status' in shown_element_functions.keys():
            show_status = True
        pass_status = False
        if 'pass_status' in shown_element_functions.keys():
            pass_status = True
        # base_color = 100
        # row_color = 0
        # html table
        h('<table id="personsTable">')
        h('<!-- Table header -->\
                <thead>\
                    <tr>\
                     <th scope="col" id="Number" style="width:75px;">Number</th>\
                        <th scope="col" id="Identifier">Identifier</th>\
                        <th scope="col" id="Names">Names</th>\
                        <th scope="col" id="IDs">IDs</th>\
                        <th scope="col" id="Papers" style="width:350px">Papers</th>\
                        <th scope="col" id="Link">Link</th>')
        if show_status:
            h('         <th scope="col" id="Status" >Status</th>')
        if show_action_button:
            h('         <th scope="col" id="Action">Action</th>')
        h('         </tr>\
                </thead>\
           <!-- Table body -->\
                <tbody>')
        for index, result in enumerate(results):
            # if len(results) > base_color:
                # row_color += 1
            # else:
            #     row_color = base_color - (base_color - index *
            #                 base_color / len(results)))

            pid = result['pid']
            canonical_id = result['canonical_id']

            # person row
            h('<tr id="pid'+ str(pid) + '">')
            h('<td>%s</td>' % (index + 1))
#            for nindex, name in enumerate(names):
#                color = row_color + nindex * 35
#                color = min(color, base_color)
#                h('<span style="color:rgb(%d,%d,%d);">%s; </span>'
#                            % (color, color, color, name[0]))
            #Identifier
            if canonical_id:
                h('<td>%s</td>' % (canonical_id,))
            else:
                canonical_id = ''
                h('<td>%s</td>' % ('No canonical id',))
            #Names
            h('<td class="emptyName' + str(pid) + '">')
            #html.extend(self.tmpl_gen_names(names))
            h('</td>')
            # IDs
            h('<td class="emptyIDs' + str(pid) + '" >')#style="text-align:left;padding-left:35px;"
            #html.extend(self.tmpl_gen_ext_ids(external_ids))
            h('</td>')
            # Recent papers
            h('<td>')
            h(('<a rel="nofollow" href="#" id="aid_moreinfolink" class="mpid%s">'
                        '<img src="../img/aid_plus_16.png" '
                        'alt = "toggle additional information." '
                        'width="11" height="11"/> '
                        + self._('Recent Papers') +
                        '</a>')
                        % (pid))
            h('<div class="more-mpid%s" id="aid_moreinfo">' % (pid))
            h('</div>')
            h('</td>')

            #Link
            h('<td>')
            h(('<span>'
                    '<em><a rel="nofollow" href="%s/author/profile/%s" id="aid_moreinfolink" target="_blank">'
                    + self._('Publication List ') + '(%s)</a></em></span>')
                    % (CFG_SITE_URL,get_person_redirect_link(pid),
                       get_person_redirect_link(pid)))
            h('</td>')

            hidden_status = ""
            if pass_status:
                if result["status"]:
                    status = "Available"
                else:
                    status = "Not available"
                hidden_status = '<input type="hidden" name="profile_availability" value="%s"/>' % status
                if show_status:
                    h('<td>%s</td>' % (status))
            if show_action_button:
                action_button_text, action_button_link, action_button_parameters, action_button_class, action_button_to_disable = shown_element_functions['button_gen'](pid, query)#class
                #Action link
                h('<td class="uncheckedProfile' + str(pid) + '" style="text-align:center; vertical-align:middle;">')
                parameters_sublink = ''

                if action_button_link:
                    parameters_sublink = '<input type="hidden" name="%s" value="%s" />' % (action_button_parameters[0][0], str(action_button_parameters[0][1]))

                    for (param_type,param_value) in action_button_parameters[1:]:
                        parameters_sublink += '<input type="hidden" name="%s" value="%s" />' % (param_type, str(param_value))

                disabled = ""
                if show_status:
                    if not result["status"] and action_button_to_disable:
                        disabled = "disabled"
                h('<form action="%s" method="get">%s%s<input type="submit" name="%s" class="%s aid_btn_blue" value="%s" %s/></form>' %
                    (action_button_link, parameters_sublink, hidden_status, canonical_id, action_button_class, action_button_text, disabled))  #confirmlink check if canonical id
                h('</td>')
            h('</tr>')
        h('</tbody>')
        h('</table>')

        return "\n".join(html)

    def tmpl_gen_papers(self, papers):
        """
            Generates the recent papers html code.
            Returns a list of strings
        """
        html = []
        h = html.append

        if papers:
            h((self._('Showing the') + ' %d ' + self._('most recent documents:')) % len(papers))
            h("<ul>")

            for paper in papers:
                h("<li>%s</li>"
                       % (format_record(int(paper[0]), "ha")))

            h("</ul>")
        elif not papers:
            h("<p>" + self._('Sorry, there are no documents known for this person') + "</p>")
        return html

    def tmpl_gen_names(self, names):
        """
            Generates the names html code.
            Returns a list of strings
        """
        html = []
        h = html.append
        delimiter = ";"
        if names:
            for i,name in enumerate(names):
                if i == 0:
                    h('<span>%s</span>'
                            % (name[0],))
                else:
                    h('<span">%s  &nbsp%s</span>'
                            % (delimiter, name[0]))
        else:
            h('%s' % ('No names found',))
        return html


    def tmpl_gen_ext_ids(self, external_ids):
        """
            Generates the external ids html code.
            Returns a list of strings
        """
        html = []
        h = html.append

        if external_ids:
            h('<table id="externalIDsTable">')
            for key, value in external_ids.iteritems():
                h('<tr>')
                h('<td style="margin-top:5px; width:1px;  padding-right:2px;">%s:</td>' % key)
                h('<td style="padding-left:5px;width:1px;">')
                for i, item in enumerate(value):
                    if i == 0:
                        h('%s' % item)
                    else:
                        h('; %s' % item)
                h('</td>')
                h('</tr>')
            h('</table>')
        else:
            h('%s' % ('No external ids found',))

        return html


    def tmpl_choose_profile_start(self):
        '''
        Shadows the behaviour of tmpl_search_pagestart
        '''
        return '<div class="pagebody"><div class="pagebodystripemiddle">'

    def tmpl_choose_profile_footer(self):

        return ('<br>In case you don\'t find the correct match or your profile is already taken, please contact us here:  <a rel="nofollow" href="mailto:%s">%s</a></p>'
                % (CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL,
                  CFG_BIBAUTHORID_AUTHOR_TICKET_ADMIN_EMAIL))

    def tmpl_probable_profile_suggestion(self, probable_profile_suggestion_info, last_viewed_profile_suggestion_info, search_param):
        '''
        Suggest the most likely profile that the user can be based on his papers in external systems that is logged in through.
        '''
        html = []
        h = html.append
        last_viewed_profile_message = self._("The following profile is the one you were viewing before logging in: ")

        # if the user has searched then his choice should be remembered in case the chosen profile is not available
        param=''
        if search_param:
            param = '&search_param=' + search_param

        h('<ul>')
        if probable_profile_suggestion_info:
            probable_profile_message = self._("Out of %s paper(s) claimed to your arXiv account, %s match this profile: " %
                                               (probable_profile_suggestion_info['num_of_arXiv_papers'],
                                                probable_profile_suggestion_info['num_of_recids_intersection']))
            h('<li>')
            h('%s %s ' % (probable_profile_message, probable_profile_suggestion_info['name_string']))
            h('<a href="%s/author/profile/%s" target="_blank"> %s </a>' % (CFG_SITE_URL, probable_profile_suggestion_info['canonical_id'],
                                                                           probable_profile_suggestion_info['canonical_name_string']))
            h('<a rel="nofollow" href="%s/author/claim/action?associate_profile=True&pid=%s%s" class="confirmlink"><button type="button">%s</a>' % ( CFG_SITE_URL,
                                                                                str(probable_profile_suggestion_info['pid']), param, 'This is my profile'))
            h('</li>')
        if last_viewed_profile_suggestion_info:
            h('<li>')
            h('%s %s ' % (last_viewed_profile_message, last_viewed_profile_suggestion_info['name_string']))
            h('<a href="%s/author/profile/%s" target="_blank"> %s </a>' % (CFG_SITE_URL, last_viewed_profile_suggestion_info['canonical_id'],
                                                                           last_viewed_profile_suggestion_info['canonical_name_string']))
            h('<a rel="nofollow" href="%s/author/claim/action?associate_profile=True&pid=%s%s" class="confirmlink"><button type="button">%s</a>' % ( CFG_SITE_URL,
                                                                                str(last_viewed_profile_suggestion_info['pid']), param, 'This is my profile'))
            h('</li>')
        h("</ul>")
        message = self._("If none of the options suggested above apply, you can look for other possible options from the list below:")
        h('<p>%s</p>' % (message,))
        h('</br>')

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
        h(' <li><a rel="nofollow" href=%s/author/claim/%s?open_claim=True> Continue as a guest </a> <small>' % (CFG_SITE_URL, person))
        h(' - Use this option if you DON\'T have an arXiv account, or you have not claimed any paper in arXiv.')
        h('(If you login as a guest, INSPIRE will need to confirm you as an author before processing your claimed papers.) </small><br><br>')
        h('If you login through arXiv.org we can verify that you are the author of these papers and accept your claims rapidly, '
          'as well as adding additional claims from arXiv. <br>If you choose not to login via arXiv your changes will '
          'be publicly visible only after our editors check and confirm them, usually a few days.<br>  '
          'Either way, claims made on behalf of another author will go through our staff and may take longer to display. '
          'This applies as well to papers which have been previously claimed, by yourself or someone else.')
        return "\n".join(html)

    def tmpl_welcome_end(self):
        '''
        Shadows the behaviour of tmpl_search_pageend
        '''
        return '</div></div>'


    def tmpl_choose_profile(self, failed):
        '''
        SSO landing/choose_profile page.
        '''
        html = []
        h = html.append
        if failed:
            h('<p><strong><font color="red">Unfortunately the profile you chose is no longer available.</font></strong></p>')
            h('<p>We apologise for the inconvenience. Please select another one.</br>Keep in mind that you can create an empty profile and then claim all of your papers in it.')
        else:
            h('<p><b>You have now successfully logged in via arXiv.org, please choose your profile among these suggestions: </b></p>')

        return "\n".join(html)

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
                        <script type="text/javascript" src="https://www.slac.stanford.edu/spires/hepnames/spbeat.js">
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
    def loading_html(self):
        return '<img src=/img/ui-anim_basic_16x16.gif> Loading...'

    def tmpl_personnametitle(self, person_info, ln, loading=False):
        _ = gettext_set_language(ln)
        if loading:
            html_header = '<span id="personnametitle">' + self.loading_html() + '</span>'
        else:
            if not person_info['name']:
                display_name = " Name not available"
            else:
                display_name = str(person_info['name']) + ' (' + str(person_info['canonical_name']) + ')'

            html_header = ('<h1><span id="personnametitle">%s</span></h1>'
                          % (display_name))

        return html_header


    def tmpl_profile_management(self, ln, person_data, arxiv_data, orcid_data, claim_paper_data,
                                int_ids_data, ext_ids_data, autoclaim_data, support_data,
                                merge_data, hepnames_data):
        '''
        SSO landing/manage profile page.
        '''
        html = list()
        html_arxiv = self.tmpl_arxiv_box(arxiv_data, ln, loading=False)
        html_orcid = self.tmpl_orcid_box(orcid_data, ln, loading=False)
        html_claim_paper = self.tmpl_claim_paper_box(claim_paper_data, ln, loading=False)
        if ext_ids_data:
            html_ext_ids = self.tmpl_ext_ids_box(person_data['pid'], int_ids_data, ext_ids_data, ln, loading=False)
        html_autoclaim = self.tmpl_autoclaim_box(autoclaim_data, ln, loading=True)

        html_support = self.tmpl_support_box(support_data, ln, loading=False)
        html_merge = self.tmpl_merge_box(merge_data, ln, loading=False)
        html_hepnames = self.tmpl_hepnames_box(hepnames_data, ln, loading=False)

        g = self._grid

        left_side_elements = list()
        left_side_elements.append(g(1, 1, cell_padding=5)(html_arxiv))
        left_side_elements.append(g(1, 1, cell_padding=5)(html_claim_paper))
        if not autoclaim_data['hidden']:
            left_side_elements.append(g(1, 1, cell_padding=5)(html_autoclaim))

        left_len = len(left_side_elements)
        left_side = g(left_len, 1)(*left_side_elements)

        right_side_elements = list()
        right_side_elements.append(g(1, 1, cell_padding=5)(html_orcid))
        if ext_ids_data:
            right_side_elements.append(g(1, 1, cell_padding=5)(html_ext_ids))
        right_side_elements.append(g(1, 1, cell_padding=5)(html_hepnames))
        right_side_elements.append(g(1, 1, cell_padding=5)(html_merge))
        right_side_elements.append(g(1, 1, cell_padding=5)(html_support))

        right_len = len(right_side_elements)
        right_side = g(right_len, 1)(*right_side_elements)

        page = g(1, 2)(left_side, right_side)

        html.append(page)

        return ' '.join(html)

    def tmpl_print_searchresultbox(self, bid, header, body):
        """ Print a nicely formatted box for search results. """

        # first find total number of hits:
        out = ('<table class="searchresultsbox" ><thead><tr><th class="searchresultsboxheader">'
            + header + '</th></tr></thead><tbody><tr><td id ="%s" class="searchresultsboxbody">' % bid
            + body + '</td></tr></tbody></table>')
        return out

    def tmpl_arxiv_box(self, arxiv_data, ln, add_box=True, loading=True):
        _ = gettext_set_language(ln)
        html_head = _("""<span title="Login through arXiv is needed to verify this is your profile. When you log in your publication list will automatically update with all your arXiv publications.
You may also continue as a guest. In this case your input will be processed by our staff and will take longer to display."><strong> Login with your arXiv.org account </strong></span>""")

        if arxiv_data['login'] == True:
            if arxiv_data['view_own_profile'] == True:
                html_arxiv = _("You have succesfully logged in via arXiv. </br> You can now manage your profile.</br>")
            elif arxiv_data['user_has_pid']:
                html_arxiv = _("You have succesfully logged in via arXiv.</br><div> <font color='red'>However the profile you are viewing is not your profile.</br></br></font>")
                own_profile_link = "%s/author/manage_profile/%s" % (CFG_SITE_URL, arxiv_data['user_pid'])
                own_profile_text = _("Manage your profile")
                html_arxiv += '<span class=\"bsw\"><a rel="nofollow" href="%s" class="btn">%s</a></span>' % (own_profile_link, own_profile_text)
            else:
                html_arxiv = _("You have succesfully logged in, but </br><div><font color='red'> you are not associated to a person yet. Please use the button below to choose your profile </br></br></font>")
                login_link = '%s/author/choose_profile' % CFG_SITE_URL
                login_text = _("Choose your profile")
                html_arxiv += '<br><span class=\"bsw\"><a rel="nofollow" href="%s" class="btn">%s</a></span>' % (login_link, login_text)
        else:
            html_arxiv = _("Please log in through arXiv to manage your profile.</br>")
            login_link = "https://arxiv.org/inspire_login"
            login_text = _("Login into Inspire through arXiv.org")
            html_arxiv += '<br><span class=\"bsw\"><a rel="nofollow" href="%s" class="btn">%s</a></span>' % (login_link, login_text)
        if loading:
            html_arxiv = self.loading_html()
        if add_box:
            arxiv_box = self.tmpl_print_searchresultbox('arxiv', html_head, html_arxiv)
            return arxiv_box
        else:
            return html_arxiv

    def tmpl_orcid_box(self, orcid_data, ln, add_box=True, loading=True):
        _ = gettext_set_language(ln)

        html_head = _(""" <span title="ORCiD (Open Researcher and Contributor ID) is a unique researcher identifier that distinguishes you from other researchers.
It holds a record of all your research activities. You can add your ORCiD to all your works to make sure they are associated with you. ">
        <strong> Connect this profile to an ORCiD </strong> <span>""")
        html_orcid = ""

        if orcid_data['orcids']:
            html_orcid += _('This profile is already connected to the following ORCiD: <strong>%s</strong></br>' % (",".join(orcid_data['orcids']),))
            if orcid_data['arxiv_login'] and orcid_data['own_profile']:
                html_orcid += '<br><span class=\"bsw\"><a rel="nofollow" href="%s" class="btn">%s</a></span>' % ("%s/author/manage_profile/import_orcid_pubs" % CFG_SITE_SECURE_URL, _("Import your publications from ORCID") )
                html_orcid += '<br><br><span class=\"bsw\"><a rel="nofollow" href="http://orcid.org/%s" class="btn">%s</a></span>' % (orcid_data['orcids'][0], _("Visit your profile in ORCID") )
        else:
            html_orcid += "This profile has not been connected to an ORCiD account yet. "
            if orcid_data['arxiv_login'] and (orcid_data['own_profile'] or orcid_data['add_power']):
                add_link = "%s/youraccount/oauth2?provider=%s" % (CFG_SITE_URL, 'orcid')
                add_text = _("Connect an ORCiD to this profile")
                html_orcid += '<br><br><span class=\"bsw\"><a rel="nofollow" href="%s" class="btn">%s</a></span>' % (add_link, add_text)
            else:
                suggest_text = _("Suggest an ORCiD for this profile:")
                html_orcid += '<br><br><span class=\"bsw\"> %s <br> <br>' % suggest_text

                html_orcid += '<form class="form-inline"><div class="input-append"><input class="input-xlarge" id="suggested_orcid" type="text">'
                html_orcid += '&nbsp;<a id="orcid_suggestion" class="btn" href="#">'
                html_orcid += '<span class="pid hidden">%s</span>%s</a></div></form>' % (orcid_data['pid'], 'Submit Suggestion')

                #html_orcid += '<form method="GET" action="%s/author/manage_profile/suggest_orcid" rel="nofollow">' % CFG_SITE_URL
                #html_orcid += '<input name="orcid" id="orcid" type="text" style="border:1px solid #333; width:300px;"/>'
                #html_orcid += '<input type="hidden" name="pid" value="%s">' % orcid_data['pid']
                #html_orcid += '<input type="submit" class="btn" value="%s"> </form>' % ('Submit suggestion',)

                #html_orcid += '<a rel="nofollow" href="%s" class="btn">%s</a>' % (suggest_link, suggest_text)

                html_orcid += '</span>'
        if loading:
            html_orcid = self.loading_html()
        if add_box:
            orcid_box = self.tmpl_print_searchresultbox('orcid', html_head, html_orcid)
            return orcid_box
        else:
            return html_orcid

    def tmpl_claim_paper_box(self, claim_paper_data, ln, add_box=True, loading=True):
        _ = gettext_set_language(ln)

        html_head = _("""<span title="When you add more publications you make sure your publication list and citations appear correctly on your profile.
You can also assign publications to other authors. This will help INSPIRE provide more accurate publication and citation statistics. "><strong> Manage publications </strong><span>""")
        html_claim_paper = ("")

        link = "%s/author/claim/%s?open_claim=True" % (CFG_SITE_URL, claim_paper_data['canonical_id'])
        text = _("Manage publication list")
        html_claim_paper += 'Assign publications to your INSPIRE profile to keep it up to date. </br></br> <span class=\"bsw\"><a rel="nofollow" href="%s" class="btn">%s</a></span>' % (link, text)

        if loading:
            html_claim_paper = self.loading_html()
        if add_box:
            claim_paper_box = self.tmpl_print_searchresultbox('claim_paper', html_head, html_claim_paper)
            return claim_paper_box
        else:
            return html_claim_paper

    def tmpl_ext_ids_box(self, personid,  int_ids_data, ext_ids_data, ln, add_box=True, loading=True):
        _ = gettext_set_language(ln)

        html_head = _("<strong> Person identifiers, internal and external </strong>")

        html_ext_ids = 'This is personID: %s <br>' % personid

        html_ext_ids += '<span class=\"bsw\"><div> <strong> External ids: </strong><br>'

        # if the user has permission to add/remove ids, in other words if the profile is his or he is admin
        if ext_ids_data['person_id'] == ext_ids_data['user_pid'] or ext_ids_data['ulevel'] == "admin":
            add_text = _('add external id')
            add_parameter = 'add_external_id'
            remove_text = _('delete selected ids')
            remove_parameter = 'delete_external_ids'
            add_missing_text = _('Harvest missing external ids from claimed papers')
            add_missing_parameter = 'add_missing_external_ids'
        else:
            add_text = _('suggest external id to add')
            add_parameter = 'suggest_external_id_to_add'
            remove_text = _('suggest selected ids to delete')
            remove_parameter = 'suggest_external_ids_to_delete'
            add_missing_text = _('suggest missing ids')
            add_missing_parameter = 'suggest_missing_external_ids'

        html_ext_ids += '<form method="GET" action="%s/author/claim/action" rel="nofollow">' % (CFG_SITE_URL)
        html_ext_ids += '<input type="hidden" name="%s" value="True">' % (add_missing_parameter,)
        html_ext_ids += '<input type="hidden" name="pid" value="%s">' % ext_ids_data['person_id']
        html_ext_ids += '<br> <input type="submit" class="btn" value="%s"> </form>' % (add_missing_text,)

        if 'ext_ids' in ext_ids_data and ext_ids_data['ext_ids']:
            html_ext_ids += '<form method="GET" action="%s/author/claim/action" rel="nofollow">' % (CFG_SITE_URL)
            html_ext_ids += '   <input type="hidden" name="%s" value="True">' % (remove_parameter,)
            html_ext_ids += '   <input type="hidden" name="pid" value="%s">' % ext_ids_data['person_id']
            for key in ext_ids_data['ext_ids']:
                try:
                    sys = [system for system in PERSONID_EXTERNAL_IDENTIFIER_MAP if PERSONID_EXTERNAL_IDENTIFIER_MAP[system] == key][0]
                except (IndexError):
                    sys = ''
                for id_value in ext_ids_data['ext_ids'][key]:
                    html_ext_ids += '<br> <input type="checkbox" name="existing_ext_ids" value="%s||%s"> <strong> %s: </strong> %s' % (key, id_value, sys, id_value)
            html_ext_ids += '        <br> <br> <input type="submit" class="btn" value="%s"> <br> </form>' % (remove_text,)
        else:
            html_ext_ids += 'UserID: There are no external users associated to this profile!'

        html_ext_ids += '<br> <br>'
        html_ext_ids += '<form method="GET" action="%s/author/claim/action" rel="nofollow">' % (CFG_SITE_URL)
        html_ext_ids += '   <input type="hidden" name="%s" value="True">' % (add_parameter,)
        html_ext_ids += '   <input type="hidden" name="pid" value="%s">' % ext_ids_data['person_id']
        html_ext_ids += '   <select name="ext_system">'
        html_ext_ids += '      <option value="" selected>-- ' + self._('Choose system') + ' --</option>'
        for el in PERSONID_EXTERNAL_IDENTIFIER_MAP:
            html_ext_ids += '  <option value="%s"> %s </option>' % (PERSONID_EXTERNAL_IDENTIFIER_MAP[el], el)
        html_ext_ids += '   </select>'
        html_ext_ids += '   <input type="text" name="ext_id" id="ext_id" style="border:1px solid #333; width:350px;">'
        html_ext_ids += '   <input type="submit" class="btn" value="%s" >' % (add_text,)
        # html_ext_ids += '<br>NOTE: please note that if you add an external id it will replace the previous one (if any).')
        html_ext_ids += '<br> </form> </div></span>'


        html_ext_ids += '<br> <div> <strong> Inspire user ID: </strong> <br>'
        html_ext_ids += "Current user id: %s <br>" % repr(int_ids_data['uid'])
        html_ext_ids += "Previous user ids: %s <br> " % repr(int_ids_data['old_uids'])
        html_ext_ids += '<br>'
        html_ext_ids += '<form method="GET" action="%s/author/claim/action" rel="nofollow">' % (CFG_SITE_URL)
        html_ext_ids += '   <input type="text" name="uid" id="uid" style="border:1px solid #333; width:350px;">'
        html_ext_ids += '   <input type="hidden" name="%s" value="True">' % ('set_uid',)
        html_ext_ids += '   <input type="hidden" name="pid" value="%s">' % ext_ids_data['person_id']
        html_ext_ids += '   <input type="submit" class="btn" value="%s"> </form>' % ('Set (steal!) user id',)
        html_ext_ids += '</div>'

        if loading:
            html_ext_ids += self.loading_html()
        if add_box:
            ext_ids_box = self.tmpl_print_searchresultbox('external_ids', html_head, html_ext_ids)
            return ext_ids_box
        else:
            return html_ext_ids

    # for ajax requests add_box and loading are false
    def tmpl_autoclaim_box(self, autoclaim_data, ln, add_box=True, loading=True):
        _ = gettext_set_language(ln)

        html_head = None

        if autoclaim_data['hidden']:
            return None

        html_head = _("""<span title="You don’t need to add all your publications one by one.
This list contains all your publications that were automatically assigned to your INSPIRE profile through arXiv and ORCiD. "><strong> Automatically assigned publications </strong> </span>""")

        if loading:
            if autoclaim_data['num_of_claims'] == 0:
                html_autoclaim = ''
            else:
                html_autoclaim = _("<span id=\"autoClaimMessage\">Please wait as we are assigning %s papers from external systems to your"
                                   " Inspire profile</span></br>"% (str(autoclaim_data["num_of_claims"])))

                html_autoclaim += self.loading_html();
        else:
            html_autoclaim = ''
# FIXME: unsuccesful claims temporarily hidden until autoclaim ticket implementation is finished
#            if "unsuccessfull_recids" in autoclaim_data.keys() and autoclaim_data["unsuccessfull_recids"]:
#
#                message = ''
#                if autoclaim_data["num_of_unsuccessfull_recids"] > 1:
#                    message = _("The following %s publications need your review before they can be assigned to your profile:" % (str(autoclaim_data["num_of_unsuccessfull_recids"]),))
#                else:
#                    message = _("The following publications need your review before they can be assigned to your profile:")
#                html_autoclaim += "<br><span id=\"autoClaimUnSuccessMessage\">%s</span></br>"% (message,)
#                html_autoclaim += '<div style="border:2px;height:100px;overflow:scroll;overflow-y:auto;overflow-x:auto;">'
#                html_autoclaim += '<br><strong>Publication title</strong> <ol type="1"> <br>'
#                for rec in autoclaim_data['unsuccessfull_recids']:
#                    html_autoclaim += '<li> <a href="%s/record/%s"> <b> ' % (CFG_SITE_URL, rec) + autoclaim_data['recids_to_external_ids'][rec] + '</b></a></li>\n'
#                html_autoclaim += '</ol><br>\n</div>'
#
#                link = "%s/author/claim/action?confirm=True&pid=%s&autoclaim_show_review=True" % (CFG_SITE_URL, autoclaim_data['person_id'])
#                text = _("Review assigning")
#                html_autoclaim += '<br><span class=\"bsw\"><a rel="nofollow" href="%s" class="btn">%s</a></span><br><br>' % (link, text)

            if "successfull_recids" in autoclaim_data.keys() and autoclaim_data["successfull_recids"]:
                message = _('The following publications have been successfully assigned to your profile:')
                html_autoclaim += "<span id=\"autoClaimSuccessMessage\">%s</span><br>" % (message,)
                html_autoclaim += '<div style="border:2px;height:300px;overflow:scroll;overflow-y:auto;overflow-x:auto;">'
                html_autoclaim += '<br><strong>Publication title</strong> <ol type="1" style="padding-left:20px"> <br>'
                for rec in autoclaim_data['successfull_recids']:
                    html_autoclaim += '<li> <a href="%s/record/%s"> <b> ' % (CFG_SITE_URL, rec) + autoclaim_data['recids_to_external_ids'][rec] + '</b></a></li>\n'
                html_autoclaim += '</ol><br>\n</div>'

            if not html_autoclaim:
                html_autoclaim = 'There are no publications to be automatically assigned'

        if add_box:
            autoclaim_box = self.tmpl_print_searchresultbox('autoclaim', html_head, html_autoclaim)
            return autoclaim_box
        else:
            return html_autoclaim

    def tmpl_support_box(self, support_data, ln, add_box=True, loading=True):
        _ = gettext_set_language(ln)

        help_link = "%s/author/help" % (CFG_SITE_URL)
        help_text = _("Get help!")
        html_head = _("<strong> Contact </strong>")
        html_support = _("Please contact our user support in case you need help or you just want to suggest some new ideas. We will get back to you. </br>")

        html_support += '<br><span class=\"bsw\"><a rel="nofollow" href="%s" class="btn">%s</a></span>' % (help_link, help_text)
        if loading:
            html_support = self.loading_html()
        if add_box:
            support_box = self.tmpl_print_searchresultbox('support', html_head, html_support)
            return support_box
        else:
            return html_support

    def tmpl_merge_box(self, merge_data, ln, add_box=True, loading=True):
        _ = gettext_set_language(ln)

        html_head = _("""<span title="It sometimes happens that somebody's publications are scattered among two or more profiles for various reasons
(different spelling, change of name, multiple people with the same name). You can merge a set of profiles together.
This will assign all the information (including publications, IDs and citations) to the profile you choose as a primary profile.
After the merging only the primary profile will exist in the system and all others will be automatically deleted. "><strong> Merge profiles </strong><span>""")
        html_merge = _("If your or somebody else's publications in INSPIRE exist in multiple profiles, you can fix that here. </br>")

        merge_link = "%s/author/merge_profiles?search_param=%s&primary_profile=%s" % (CFG_SITE_URL, merge_data['search_param'], merge_data['canonical_id'])
        merge_text = _("Merge profiles")
        html_merge += '<br><span class=\"bsw\"><a rel="nofollow" href="%s" class="btn">%s</a></span>' % (merge_link, merge_text)

        if loading:
            html_merge = self.loading_html()
        if add_box:
            merge_box = self.tmpl_print_searchresultbox('merge', html_head, html_merge)
            return merge_box
        else:
            return html_merge

    def tmpl_hepnames_box(self, hepnames_data, ln, add_box=True, loading=True):
        _ = gettext_set_language(ln)

        if not loading:
            try:
                heprec = str(hepnames_data['heprecord'][0])
            except (TypeError, KeyError, IndexError):
                heprec = ''
            if hepnames_data['HaveHep']:
                contents = hepnames_data['heprecord']
            else:
                contents = ''
                if not hepnames_data['HaveChoices']:
                    contents += ("There is no HepNames record associated with this profile. "
                                 "<a href='http://slac.stanford.edu/spires/hepnames/additions.shtml'> Create a new one! </a> <br>"
                                 "The new HepNames record will be visible and associated <br> to this author "
                                 "after manual revision, usually within a few days.")
                else:
                    #<a href="mailto:address@domain.com?subject=title&amp;body=something">Mail Me</a>
                    contents += ("There is no unique HepNames record associated "
                                 "with this profile. <br> Please tell us if you think it is one of "
                                 "the following, or <a href='http://slac.stanford.edu/spires/hepnames/additions.shtml'> Create a new one! </a> <br>"
                                 "<br><br> Possible choices are: ")
                    #mailbody = ("Hello! Please connect the author profile %s "
                    #           "with the HepNames record %s. Best regards" % (hepnames_data['cid'], '%s'))
                    #mailstr = '<form method="GET" action="%s/author/manage_profile/connect_author_with_hepname" rel="nofollow">' \
                    #          '<input type="hidden" name="cname" value="%s">' \
                    #          '<input type="hidden" name="hepname" value="%s">' \
                    #          '<input type="submit" class="btn" value="%s"> </form>' % (CFG_SITE_URL, hepnames_data['cid'], '%s', 'This is the right one!',)
                    #mailstr = ('''<class="choose_hepname" cname="%s" hepname_rec=%s> This is the right one! </class="choose_hepname">''' % (hepnames_data['cid'], '%s'))
                    #mailstr = ('''<a href='mailto:%s?subject=HepNames record match: %s %s&amp;body=%s'>'''
                    #           '''This is the right one!</a>''' % ('%s', hepnames_data['cid'], heprec, '%s'))
                    mailstr = ('''<a id="hepname_connection" class="btn" href="#"><span class="cname hidden">%s</span><span class="hepname hidden">%s</span>%s</a>''' % (hepnames_data['cid'], '%s', 'This is the right one!'))
                    choices = ['<tr><td>' + x[0] + '</td><td>&nbsp;&nbsp;</td><td  align="right">' + mailstr % x[1] + '</td></tr>'
                               for x in hepnames_data['HepChoices']]

                    contents += '<table>' + ' '.join(choices) + '</table>'
        else:
            contents = self.loading_html()

        if not add_box:
            return contents
        else:
            return self.tmpl_print_searchresultbox('hepdata', '<strong> HepNames data </strong>', contents)

    def tmpl_open_table(self, width_pcnt=False, cell_padding=False, height_pcnt=False):
        options = []

        if height_pcnt:
            options.append('height=%s' % height_pcnt)

        if width_pcnt:
            options.append('width=%s' % width_pcnt)
        else:
            options.append('width=100%')

        if cell_padding:
            options.append('cellpadding=%s' % cell_padding)
        else:
            options.append('cellpadding=0')

        return '<table border=0 %s >' % ' '.join(options)

    def tmpl_close_table(self):
        return "</table>"

    def tmpl_open_row(self):
        return "<tr>"
    def tmpl_close_row(self):
        return "</tr>"
    def tmpl_open_col(self):
        return "<td valign='top'>"
    def tmpl_close_col(self):
        return "</td>"

    def _grid(self, rows, cols, table_width=False, cell_padding=False):
        tmpl = self
        def cont(*boxes):
            out = []
            h = out.append
            idx = 0
            h(tmpl.tmpl_open_table(width_pcnt=table_width, cell_padding=cell_padding))
            for _ in range(rows):
                h(tmpl.tmpl_open_row())
                for _ in range(cols):
                    h(tmpl.tmpl_open_col())
                    h(boxes[idx])
                    idx += 1
                    h(tmpl.tmpl_close_col())
                h(tmpl.tmpl_close_row())
            h(tmpl.tmpl_close_table())
            return '\n'.join(out)
        return cont

    def tmpl_message_form(self, last_page_visited,  name_to_prefill, email_to_prefill, incomplete_params):
        html = []
        h = html.append
        #h('<div style="display: block; width: 600px; text-align: left;">')
        h('<div style="width:100%; minheight: 500px;">')

        h(    '<div  style="background-color: #F1F1FA; display: table; border-radius: 10px; padding: 20px; color: #3366CC; font: Helvetica 12pt;border: 1px solid black; margin: 0px auto;">')
        h(      '<div align="center">')
        h(          '<p style="font-size: 20px; font-weight: bold;"> Get help!</p>')
        h(          '<p style="font-size: 14px; font-weight: bold;"> Write here on any issue, suggestions or technical request.</p>')
        if incomplete_params:
            h(      '<p style="font-size: 14px; font-weight: bold;"> <font color="red">Please fill the forms correctly!</font></p>')
        h(      '</div>')
        h(      '<form action="%s/author/claim/action" method="post">'  % ( CFG_SITE_URL, ))
        h(        '<fieldset style="border: 0; display: inline-block;">')
        h(          '<p><label for="Name"> Name: </label><input style="float: right; border-radius: 4px;" required="True" name="Name" value="%s" type="text"  size="40"></p>' % (name_to_prefill))
        h(          '<p><label for="E-mail"> E-mail: </label><input style="float: right; border-radius: 4px;" name="E-mail" value="%s" type="email" size="40"></p>'
                                                                                                                                          % (email_to_prefill))
        h(          '<input type="hidden" name="last_page_visited" value="%s" />' % (str(last_page_visited),))
        h(          '<p>Comment:</p>')
        h(          '<p><textarea style="max-width:500px; min-width:500px; min-height:300px; border-radius: 4px;" name="Comment" cols="60" rows="5" required="True" id="Comment"></textarea></p>')
        h(       '</fieldset>')
        h(       '<button class="aid_btn_blue" style="display: block; margin: 0 auto;" type="submit" name="send_message">Submit</button>')

        h(     '</form>')

        h(  '</div>')

        h('</div>')

        return ' '.join(html)
    # pylint: enable=C0301

    def tmpl_help_page(self):
        helphtml = """
     <iframe src="/img/bibauthorid-help.html" seamless style="width:100%;height:6000px"></iframe>
        """
        return helphtml

verbiage_dict = {'guest': {'confirmed': 'Papers',
                           'repealed': 'Papers removed from this profile',
                           'review': 'Papers in need of review',
                           'tickets': 'Open Tickets', 'data': 'Data',
                           'confirmed_ns': 'Papers of this Person',
                           'repealed_ns': 'Papers _not_ of this Person',
                           'review_ns': 'Papers in need of review',
                           'tickets_ns': 'Tickets for this Person',
                           'data_ns': 'Additional Data for this Person'},
                 'user': {'owner': {'confirmed': 'Your papers',
                                    'repealed': 'Not your papers',
                                    'review': 'Papers in need of review',
                                    'tickets': 'Your tickets', 'data': 'Data',
                                    'confirmed_ns': 'Your papers',
                                    'repealed_ns': 'Not your papers',
                                    'review_ns': 'Papers in need of review',
                                    'tickets_ns': 'Your tickets',
                                    'data_ns': 'Additional Data for this Person'},
                          'not_owner': {'confirmed': 'Papers',
                                        'repealed': 'Papers removed from this profile',
                                        'review': 'Papers in need of review',
                                        'tickets': 'Your tickets', 'data': 'Data',
                                        'confirmed_ns': 'Papers of this Person',
                                        'repealed_ns': 'Papers _not_ of this Person',
                                        'review_ns': 'Papers in need of review',
                                        'tickets_ns': 'Tickets you created about this person',
                                        'data_ns': 'Additional Data for this Person'}},
                 'admin': {'confirmed': 'Papers',
                           'repealed': 'Papers removed from this profile',
                           'review': 'Papers in need of review',
                           'tickets': 'Tickets', 'data': 'Data',
                           'confirmed_ns': 'Papers of this Person',
                           'repealed_ns': 'Papers _not_ of this Person',
                           'review_ns': 'Papers in need of review',
                           'tickets_ns': 'Request Tickets',
                           'data_ns': 'Additional Data for this Person'}}

buttons_verbiage_dict = {'guest': {'mass_buttons': {'no_doc_string': 'Sorry, there are currently no documents to be found in this category.',
                                                    'b_confirm': 'Yes, those papers are by this person.',
                                                    'b_repeal': 'No, those papers are not by this person',
                                                    'b_to_others': 'Assign to other person',
                                                    'b_forget': 'Forget decision'},
                                   'record_undecided': {'alt_confirm': 'Confirm!',
                                                        'confirm_text': 'Yes, this paper is by this person.',
                                                        'alt_repeal': 'Rejected!',
                                                        'repeal_text': 'No, this paper is <i>not</i> by this person',
                                                        'to_other_text': 'Assign to another person',
                                                        'alt_to_other': 'To other person!'},
                                   'record_confirmed': {'alt_confirm': 'Confirmed.',
                                                        'confirm_text': 'Marked as this person\'s paper',
                                                        'alt_forget': 'Forget decision!',
                                                        'forget_text': 'Forget decision.',
                                                        'alt_repeal': 'Repeal!',
                                                        'repeal_text': 'But it\'s <i>not</i> this person\'s paper.',
                                                        'to_other_text': 'Assign to another person',
                                                        'alt_to_other': 'To other person!'},
                                   'record_repealed': {'alt_confirm': 'Confirm!',
                                                       'confirm_text': 'But it <i>is</i> this person\'s paper.',
                                                       'alt_forget': 'Forget decision!',
                                                       'forget_text': 'Forget decision.',
                                                       'alt_repeal': 'Repealed',
                                                       'repeal_text': 'Marked as not this person\'s paper',
                                                       'to_other_text': 'Assign to another person',
                                                       'alt_to_other': 'To other person!'}},
                         'user': {'owner': {'mass_buttons': {'no_doc_string': 'Sorry, there are currently no documents to be found in this category.',
                                                             'b_confirm': 'These are mine!',
                                                             'b_repeal': 'These are not mine!',
                                                             'b_to_others': 'It\'s not mine, but I know whose it is!',
                                                             'b_forget': 'Forget decision'},
                                            'record_undecided': {'alt_confirm': 'Mine!',
                                                                 'confirm_text': 'This is my paper!',
                                                                 'alt_repeal': 'Not mine!',
                                                                 'repeal_text': 'This is not my paper!',
                                                                 'to_other_text': 'Assign to another person',
                                                                 'alt_to_other': 'To other person!'},
                                            'record_confirmed': {'alt_confirm': 'Not Mine.',
                                                                 'confirm_text': 'Marked as my paper!',
                                                                 'alt_forget': 'Forget decision!',
                                                                 'forget_text': 'Forget assignment decision',
                                                                 'alt_repeal': 'Not Mine!',
                                                                 'repeal_text': 'But this is not mine!',
                                                                 'to_other_text': 'Assign to another person',
                                                                 'alt_to_other': 'To other person!'},
                                            'record_repealed': {'alt_confirm': 'Mine!',
                                                                'confirm_text': 'But this is my paper!',
                                                                'alt_forget': 'Forget decision!',
                                                                'forget_text': 'Forget decision!',
                                                                'alt_repeal': 'Not Mine!',
                                                                'repeal_text': 'Marked as not your paper.',
                                                                'to_other_text': 'Assign to another person',
                                                                'alt_to_other': 'To other person!'}},
                                  'not_owner': {'mass_buttons': {'no_doc_string': 'Sorry, there are currently no documents to be found in this category.',
                                                                 'b_confirm': 'Yes, those papers are by this person.',
                                                                 'b_repeal': 'No, those papers are not by this person',
                                                                 'b_to_others': 'Assign to other person',
                                                                 'b_forget': 'Forget decision'},
                                                'record_undecided': {'alt_confirm': 'Confirm!',
                                                                     'confirm_text': 'Yes, this paper is by this person.',
                                                                     'alt_repeal': 'Rejected!',
                                                                     'repeal_text': 'No, this paper is <i>not</i> by this person',
                                                                     'to_other_text': 'Assign to another person',
                                                                     'alt_to_other': 'To other person!'},
                                                'record_confirmed': {'alt_confirm': 'Confirmed.',
                                                                     'confirm_text': 'Marked as this person\'s paper',
                                                                     'alt_forget': 'Forget decision!',
                                                                     'forget_text': 'Forget decision.',
                                                                     'alt_repeal': 'Repeal!',
                                                                     'repeal_text': 'But it\'s <i>not</i> this person\'s paper.',
                                                                     'to_other_text': 'Assign to another person',
                                                                     'alt_to_other': 'To other person!'},
                                                'record_repealed': {'alt_confirm': 'Confirm!',
                                                                    'confirm_text': 'But it <i>is</i> this person\'s paper.',
                                                                    'alt_forget': 'Forget decision!',
                                                                    'forget_text': 'Forget decision.',
                                                                    'alt_repeal': 'Repealed',
                                                                    'repeal_text': 'Marked as not this person\'s paper',
                                                                    'to_other_text': 'Assign to another person',
                                                                    'alt_to_other': 'To other person!'}}},
                         'admin': {'mass_buttons': {'no_doc_string': 'Sorry, there are currently no documents to be found in this category.',
                                                    'b_confirm': 'Yes, those papers are by this person.',
                                                    'b_repeal': 'No, those papers are not by this person',
                                                    'b_to_others': 'Assign to other person',
                                                    'b_forget': 'Forget decision'},
                                   'record_undecided': {'alt_confirm': 'Confirm!',
                                                        'confirm_text': 'Yes, this paper is by this person.',
                                                        'alt_repeal': 'Rejected!',
                                                        'repeal_text': 'No, this paper is <i>not</i> by this person',
                                                        'to_other_text': 'Assign to another person',
                                                        'alt_to_other': 'To other person!'},
                                   'record_confirmed': {'alt_confirm': 'Confirmed.',
                                                        'confirm_text': 'Marked as this person\'s paper',
                                                        'alt_forget': 'Forget decision!',
                                                        'forget_text': 'Forget decision.',
                                                        'alt_repeal': 'Repeal!',
                                                        'repeal_text': 'But it\'s <i>not</i> this person\'s paper.',
                                                        'to_other_text': 'Assign to another person',
                                                        'alt_to_other': 'To other person!'},
                                   'record_repealed': {'alt_confirm': 'Confirm!',
                                                       'confirm_text': 'But it <i>is</i> this person\'s paper.',
                                                       'alt_forget': 'Forget decision!',
                                                       'forget_text': 'Forget decision.',
                                                       'alt_repeal': 'Repealed',
                                                       'repeal_text': 'Marked as not this person\'s paper',
                                                       'to_other_text': 'Assign to another person',
                                                       'alt_to_other': 'To other person!'}}}
