# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

# pylint: disable-msg=W0105

#from cgi import escape
#from urllib import quote
#
from invenio.config import CFG_SITE_LANG
from invenio.config import CFG_SITE_URL
from invenio.config import CFG_SITE_SUPPORT_EMAIL
from invenio.bibformat import format_record
from invenio.session import get_session
#from invenio.messages import gettext_set_language, wash_language
#from invenio.textutils import encode_for_xml

class Template:
    """Templating functions used by aid"""

    def __init__(self, language=CFG_SITE_LANG):
        """Set defaults for all aid template output"""

        self.language = language
#        self._ = gettext_set_language(wash_language(language))

    def __records_table(self, req, form_id, person_id, bibrecids):
        no_papers_html = ['<div style="text-align:left;"><strong>']
        no_papers_html.append('Sorry, there are currently no documents to be found in this category.')
        no_papers_html.append('</strong></div>')

        if not bibrecids or not person_id:
            return "\n".join(no_papers_html)

        pp_html = []
        pp_h = pp_html.append
        pp_h('<form id="%s" action="/person/batchprocess" method="post">'
                   % (form_id))
        pp_h('<table  class="paperstable" cellpadding="3" width="100%">')
        pp_h("<thead>")
        pp_h("  <tr>")
        pp_h('    <th>&nbsp;</th>')
        pp_h('    <th>Paper Short Info</th>')
        pp_h("    <th>Author Name</th>")
        pp_h("    <th>Actions</th>")
        pp_h("  </tr>")
        pp_h("</thead>")
        pp_h("<tbody>")

        for paper in bibrecids:
            pp_h('  <tr>')

            pp_h('    <td><input type="checkbox" name="selection" '
                           'value="%s" /> </td>' % (paper[1]))
            pp_h("    <td>%s</td>"
                           % (format_record(paper[0], "aid", on_the_fly=True)))
            pp_h("    <td>%s</td>" % (paper[3]))
            paper_status = "No status information found."

            if paper[2] == 2:
                paper_status = self.tmpl_author_confirmed(req, paper[1], person_id)
            elif paper[2] == -2:
                paper_status = self.tmpl_author_repealed(req, paper[1], person_id)
            else:
                paper_status = self.tmpl_author_undecided(req, paper[1], person_id)

            pp_h('    <td><div id="bibref%s"><!--%s!-->%s &nbsp;</div></td>'
                           % (paper[1], paper[2], paper_status))
            pp_h("  </tr>")

        pp_h("  </tbody>")
        pp_h("</table>")

        pp_h('<div style="text-align:left;"> On all pages: ')
        pp_h('<a rel="group_1" href="#select_all">Select All</a> | ')
        pp_h('<a rel="group_1" href="#select_none">Select None</a> | ')
        pp_h('<a rel="group_1" href="#invert_selection">Invert Selection</a>')
        pp_h('</div>')

        pp_h('<div style="vertical-align:middle;">')
        pp_h('∟ With selected do: ')
        pp_h('<input type="hidden" name="pid" value="%s" />' % (person_id))
        pp_h('<input type="submit" name="mconfirm" value="Confirm" />')
        pp_h('<input type="submit" name="massign" value="Assign to other Person" />')
        pp_h('<input type="submit" name="mrepeal" value="Repeal" />')
        pp_h('<input type="submit" name="mreset" value="Forget Decision" />')
        pp_h("  </div>")
        pp_h('</form>')

        return "\n".join(pp_html)


    def tmpl_author_details(self, req, person_id=0, names=[],
                            rejected_papers=[], rest_of_papers=[]):
        html = []
        h = html.append

        h('<div id="aid_person">')
        session = get_session(req)
        session.load()

        h(self.tmpl_author_menu(req))

        if session.has_key("person_message_show") and session["person_message_show"]:
            message = "The requested action completed successfully!"

            if session.has_key("person_message"):
                message = session["person_message"]

            h(self.tmpl_notification_box(message, "Success:"))
            del(session["person_message_show"])
            del(session["person_message"])
            session.save()

        lid = int(person_id)
        next_lnk = ("<a href='%s/person/%s'>Next &gt;&gt;</a>"
                    % (CFG_SITE_URL, lid + 1))
        refresh_lnk = ("<a href='%s/person/%s'>Refresh</a>"
                    % (CFG_SITE_URL, lid))
        prev_lnk = ("<a href='%s/person/%s'>&lt;&lt; Prev</a>"
                    % (CFG_SITE_URL, lid - 1))
        aid_nav = ("<div style=\"text-align:right;\">%s | %s | %s</div>"
                   % (prev_lnk, refresh_lnk, next_lnk))

        h('<div id="aid_person_names" class="ui-tabs ui-widget ui-widget-content ui-corner-all">')
        h('<p style="margin-left: 20px;">Names of the person as collected from the records attached</p>')
        h("<ul>")
        h('  <li><span class="aid_lowlight_text">Person ID: <span id="pid%s">%s</span></span></li>'
                      % (person_id, person_id))

        for name in names:
            h("  <li>%s as appeared on %s records</li>"
                             % (name[0], name[1]))

        h("</ul>")

        h("</div>")

        h('<div id="aid_tabbing">')
        h('  <ul>')
        h('    <li><a href="#tabRecords"><span>Records (%s)</span></a></li>' % (len(rest_of_papers)))
        h('    <li><a href="#tabNotRecords"><span>Not this person\'s records (%s)</span></a></li>' % (len(rejected_papers)))
        h('    <li><a href="#tabComments"><span>Comments</span></a></li>')
        h('  </ul>')

        h('  <div id="tabRecords">')
        h(self.__records_table(req, "massfunctions",
                                         person_id, rest_of_papers))
        h("  </div>")

        h('  <div id="tabNotRecords">')
        h('These records have been marked as not being from this person.')
        h('<br />They will be regarded in the next run of the author '
          'disambiguation algorithm and will then disappear in this listing.')
        h(self.__records_table(req, "rmassfunctions",
                                         person_id, rejected_papers))
        h("  </div>")

        h('  <div id="tabComments">')
        h('<p>Please note that comments are visible to all operators who have '
          'access to this interface</p>')
        h('    <div id="comments">No comments yet.</div>')
        h('    <form id="jsonForm" action="/person/comments" method="post">\n'
                    '      <textarea rows="4" cols="60" name="message" id="message"></textarea>\n'
                    '      <input type="hidden" name="pid" value="%s" />\n'
                    '      <input type="hidden" name="action" value="store_comment" />\n'
                    '      <br />'
                    '      <input type="submit" value="Submit this comment" />\n'
                    '    </form>' % (person_id))
        h("  </div>")

        h("</div>")
        h(aid_nav)
        h("</div>")

#        h('<p>DEBUG Session Content: <pre>%s</pre> </p>' % session)

        return "\n".join(html)


    def tmpl_author_search(self, req, query, results):
        session = get_session(req)
        mode_batchprocess = False

        if not query:
            query = ""

        html = []
        h = html.append

        h('<div id="aid_person">')

        if session.has_key("person_message_show") and session["person_message_show"]:
            message = "The requested action completed successfully!"

            if session.has_key("person_message"):
                message = session["person_message"]

            h(self.tmpl_notification_box(message, "Note:"))
            del(session["person_message_show"])
            del(session["person_message"])
            session.save()

        if session.has_key("mode_batch_assign_papers") and session["mode_batch_assign_papers"]:
            mode_batchprocess = True
            mpid = -1
            mpname = ""
            num_bibrecs = 0

            if session.has_key("bibrecs_batch_assign_papers"):
                num_bibrecs = len(session['bibrecs_batch_assign_papers'])

            if session.has_key("pid_batch_assign_papers"):
                mpid = session["pid_batch_assign_papers"]

            if session.has_key("name_batch_assign_papers"):
                mpname = session["name_batch_assign_papers"]

            message_html = ['<div id="aid_message-ribbon">']
            message_h = message_html.append

            message_h("<p>Please keep in mind that were looking "
                                "for a person to assign the %s selected "
                                "papers to.</p>" % num_bibrecs)
            message_h("<p>The selected documents are currently attached to "
                                "the person with the nameset %s and the Person ID %s </p>" % (mpname, mpid))
            message_h('<em><a href="#" id="moreinfolink" '
                                'class="mpidMESSAGEHEAD">'
                                '<img src="../img/plus-9x9.png" '
                                'alt = "toggle additional information." /> '
                                'Show list of selected papers</a></em>')
            message_h('<div style="float:right;font-weight:bold;">')
            message_h('<a href="/person/batchprocess?mcancel=True">[Cancel]</a>&nbsp;&nbsp;')
            message_h('<a href="/person/%s">[Go back to Person page]</a>' % mpid)
            message_h('</div>')

            message_h('<div class="more-mpidMESSAGEHEAD" id="aid_moreinfo">')

            if session.has_key("bibrecs_batch_assign_papers"):
                message_h('Showing %d selected documents:' % num_bibrecs)
                message_h("<ul>")

                for bibref in session["bibrecs_batch_assign_papers"]:
                    bibrec = bibref.split(',')[1]
                    message_h("<li>%s</li>"
                           % (format_record(bibrec, "aid", on_the_fly=True)))

                message_h("</ul>")
            else:
                message_h("<p>No documents selected!?</p>")

            message_h("</div>")
            message_h("</div>")
            h("\n".join(message_html))

        h('<div id="header">Search for a person</div>')
        h('<form id="searchform" action="/person/search" method="post">')
        h('<input type="text" name="q" style="border:1px solid #333; width:500px;" '
                    'size="25" maxlength="25" value="%s" class="focus" />' % query)
        h('<input type="submit" value="Search" />')
        h('</form>')

        if not results and not query:
            h('</div>')
            return "\n".join(html)

        h("<hr />")

        if query and not results:
            h('<strong>Sorry, no results could be found for the query "%s"</strong>' % query)
            h('</div>')
            return "\n".join(html)

        h('<p><strong>Results for the query "%s"</strong></p>' % query)
        base_color = 220
        row_color = 0

        for index, result in enumerate(results):
            if len(results) > base_color:
                row_color += 1
            else:
                row_color = base_color - (base_color - index *
                                          (base_color / len(results)))

            pid = result[0]
            names = result[1]
            papers = result[2]

            h('<div id="aid_result%s">' % (index % 2))
            h('<div>')
            h('<span style="color:rgb(%d,%d,%d);">%s. </span>'
                         % (row_color, row_color, row_color, index + 1))

            for nindex, name in enumerate(names):
                color = row_color + nindex * 35
                color = min(color, base_color)
                h('<span style="color:rgb(%d,%d,%d);">%s</span>'
                            % (color, color, color, name[0]))
            h('</div>')
            h('<em><a href="#" id="moreinfolink" class="mpid%s">'
                        '<img src="../img/plus-9x9.png" '
                        'alt = "toggle additional information." /> '
                        'Show additional information</a></em>' % (pid))

            if mode_batchprocess:
                h('<span style="margin-left: 40px;">'
                            '<em><a href="%s/person/batchprocess?massign=session&pid=%s" id="confirmlink">'
                            '<strong>YES!</strong> Select this person to assign the documents to! (person ID: %d)</a></em></span>'
                            % (CFG_SITE_URL, pid, pid))
            else:
                h('<span style="margin-left: 40px;">'
                            '<em><a href="%s/person/%d" id="aid_moreinfolink">'
                            'Show author page (person ID: %d)</a></em></span>'
                            % (CFG_SITE_URL, pid, pid))
            h('<div class="more-mpid%s" id="aid_moreinfo">' % (pid))

            if papers:
                h('Showing the %d most recent documents:' % len(papers))
                h("<ul>")

                for paper in papers:
                    h("<li>%s</li>"
                           % (format_record(paper[0], "aid", on_the_fly=True)))

                h("</ul>")
            else:
                h("<p>Sorry, there are no documents known for this person</p>")

            h('<p><a href="%s/person/%d" target="_blank">'
                        'Show more information about this person'
                        ' in a new window or tab</a></p>' % (CFG_SITE_URL, pid))
            h('</div>')
            h('</div>')

        h('</div>')

#        h("<p>DEBUG Session: <br />%s</p>" % session)

        return "\n".join(html)


    def tmpl_author_confirmed(self, req, bibref, pid):
        return ('<!--2!--><span id="aid_status_details"> '
                '<img src="%(url)s/img/aid_check.png" alt="Confirmed." />'
                'This record assignment has been confirmed. <br>'
                '<a id="aid_reset" href="%(url)s/person/batchprocess?mreset=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reset_gray.png" alt="Forget Decision!" style="margin-left:22px;" />'
                'Forget assignment decision</a><br>'
                '<a id="aid_repeal" href="%(url)s/person/batchprocess?mrepeal=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reject_gray.png" alt="Repeal!" style="margin-left:22px;"/>'
                'Repeal record assignment</a> </span>'
                % ({'url': CFG_SITE_URL, 'ref': bibref, 'pid': pid}))


    def tmpl_author_repealed(self, req, bibref, pid):
        return ('<!---2!--><span id="aid_status_details"> '
                '<img src="%(url)s/img/aid_reject.png" alt="Rejected." />'
                'This record assignment has been repealed. <br>'
                '<a id="aid_reset" href="%(url)s/person/batchprocess?mreset=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reset_gray.png" alt="Forget Decision!" style="margin-left: 22px;" />'
                'Forget assignment decision</a><br>'
                '<a id="aid_confirm" href="%(url)s/person/batchprocess?mconfirm=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_check_gray.png" alt="Confirm!" style="margin-left: 22px;" />'
                'Confirm record assignment</a> </span>'
                % ({'url': CFG_SITE_URL, 'ref': bibref, 'pid': pid}))


    def tmpl_author_undecided(self, req, bibref, pid):
        #batchprocess?mconfirm=True&bibrefs=['100:17,16']&pid=1
        return ('<!--0!--><span id="aid_status_details"> '
                '<a id="aid_confirm" href="%(url)s/person/batchprocess?mconfirm=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_check.png" alt="Forget Decision!" />'
                'Confirm record assignment</a><br>'
                '<a id="aid_repeal" href="%(url)s/person/batchprocess?mrepeal=True&selection=%(ref)s&pid=%(pid)s">'
                '<img src="%(url)s/img/aid_reject.png" alt="Repeal!" />'
                'Repeal record assignment</a> </span>'
                % ({'url': CFG_SITE_URL, 'ref': bibref, 'pid': pid}))


    def tmpl_meta_includes(self):

        js_path = "%s/js" % CFG_SITE_URL
        imgcss_path = "%s/img" % CFG_SITE_URL

        scripts = ["jquery-1.4.4.js",
                   "ui.core.js",
                   "jquery.ui.widget.min.js",
                   "jquery.ui.tabs.min.js",
                   "jquery.form.js",
                   "jquery.dataTables.min.js",
                   "jquery.ui.mouse.min.js",
                   "jquery.ui.draggable.min.js",
                   "jquery.ui.position.min.js",
                   "jquery.ui.resizable.min.js",
                   "jquery.ui.button.min.js",
                   "jquery.ui.dialog.min.js",
                   "bibauthorid.js"]
        result = []

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


    def tmpl_notification_box(self, message, teaser="Notice:", show_close_btn=True):
        html = []
        h = html.append
        h('<div id="aid_notification" class="ui-widget">')
        h('  <div style="margin-top: 20px; padding: 0pt 0.7em;" class="ui-state-highlight ui-corner-all">')
        h('    <p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-info"></span>')
        h('    <strong>%s</strong> %s' % (teaser, message))

        if show_close_btn:
            h('    <span style="float:right; margin-right: 0.3em;"><a href="#" class="aid_close-notify">X</a></span></p>')

        h(' </div>')
        h('</div>')

        return "\n".join(html)


    def tmpl_error_box(self, message, teaser="Alert:", show_close_btn=True):
        html = []
        h = html.append
        h('<div id="aid_notification" class="ui-widget">')
        h('  <div style="margin-top: 20px; padding: 0pt 0.7em;" class="ui-state-error ui-corner-all">')
        h('    <p><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-alert"></span>')
        h('    <strong>%s</strong> %s' % (teaser, message))

        if show_close_btn:
            h('    <span style="float:right; margin-right: 0.3em;"><a href="#" class="aid_close-notify">X</a></span></p>')

        h(' </div>')
        h('</div>')

        return "\n".join(html)


    def tmpl_author_menu(self, req, role="admin"):
        html = []
        h = html.append
        h('<div id="aid_menu">')
        h('  <ul>')
        h('    <li><a href="%s/person/search">Person Search</a></li>' % CFG_SITE_URL)
        h('    <!--<li><a href="#">Person Interface FAQ</a></li>!-->')
        h('    <!--<li>You are currently logged in as %s of this interface</li>!-->' % role)
        h('  </ul>')
        h('</div>')

        return "\n".join(html)


    def tmpl_author_transaction_review(self, req):
        session = get_session(req)
        transactions = []

        if "aid_mass_review_transactions" in session:
            if session["aid_mass_review_transactions"]:
                transactions = session["aid_mass_review_transactions"]

        t_no_conflicts = [row['bibref'] for row in transactions if row["status"] == "OK"]
        t_touched = [row['bibref'] for row in transactions if row["status"] == "touched"]
        t_not_allowed = [row['bibref'] for row in transactions if row["status"] == "not_allowed"]

        html = ['<form id="review" action="/person/batchprocess" method="post">']
        h = html.append
        h("<div>")

        if t_no_conflicts:
            h(self.tmpl_notification_box("There are %s record wihout conflicts!" % len(t_no_conflicts)))

        if t_touched:
            h("<div>")
#            h('<div><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-info"></span>'
#                        'The following records need your attention. <br />')
#            h("The following records have been touched through a human before. "
#                        "Please make sure not to accidentaly touch the wrong records.<br />")
#            h("If you want these records <strong>NOT to be affected</strong> by the chosen action, "
#                        "please tick the box next to the records.</div>")
            h(self.tmpl_notification_box('The following records need your attention. <br />\n'
                                         'The following records have been touched through a human before. '
                                         'Please make sure not to accidentaly touch the wrong records.<br /> \n'
                                         'If you want to <strong>exclude</strong> any record from the chosen action, '
                                         'please <strong>tick the box</strong> next to the record.</div>"',
                                         "Note:", False))
            h("<table>")

            for bibref in t_touched:
                bibrec = bibref.split(',')[1]
                h('<tr>')
                h('<td><input type="checkbox" name="selection" value="%s" /> </td>' % bibref)
                h('<td>%s</td>' % (format_record(bibrec, "aid", on_the_fly=True)))
                h('</tr>')

            h("</table>")
            h("</div>")

        if t_not_allowed:
            h("<div>")
#            h('<div><span style="float: left; margin-right: 0.3em;" class="ui-icon ui-icon-alert"></span>'
#                        'The following records cannot be updated. <br />')
#            h("The following records have been touched through an operator before, which locked the decision for you. ")
#            h("Please feel free to contact the support team to correct or reset the attribution for you.<br />\n"
#                        "You may contact the support team by using the eMail "
#                        "&lt;<a href='mailto:%s?subject=Record attribution lock'>%s</a>&gt;.</div>" % CFG_SITE_SUPPORT_EMAIL)
            h(self.tmpl_error_box('The following records cannot be updated. <br />\n'
                                  'The following records have been touched through an operator before, which locked the decision for you.\n'
                                  'Please feel free to contact the support team to correct or reset the attribution for you.<br />\n'
                                  'You may contact the support team by using the eMail '
                                  '&lt;<a href="mailto:%s?subject=Record attribution lock">%s</a>&gt;.</div>' % CFG_SITE_SUPPORT_EMAIL,
                                  "Note:", False))
            h("<ul>")

            for bibref in t_not_allowed:
                bibrec = bibref.split(',')[1]
                h('<li>%s</li>' % (format_record(bibrec, "aid", on_the_fly=True)))

            h("</ul>")
            h("</div>")

        h("</div>")
        h('<div style="text-align:center;">')
        h('  <input type="hidden" name="pid" value="%s" />' % (session["aid_mass_review_pid"]))
        h('  <input type="submit" name="%s" value="Accept Changes" />' % session["aid_mass_review_action"])
        h('  <input type="submit" name="mcancel" value="Cancel operation" />')
        h("</div>")
        h('</form>')

#        h('<p>DEBUG Session Content: <pre>%s</pre> </p>' % session)
        return "\n".join(html)
