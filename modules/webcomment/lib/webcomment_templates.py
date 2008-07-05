# -*- coding: utf-8 -*-
## $Id$
## Comments and reviews for records.

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

"""HTML Templates for commenting features """

__revision__ = "$Id$"

# CDS Invenio imports
from invenio.webuser import get_user_info
from invenio.dateutils import convert_datetext_to_dategui
from invenio.webmessage_mailutils import email_quoted_txt2html
from invenio.config import CFG_SITE_URL, \
                           CFG_SITE_SECURE_URL, \
                           CFG_SITE_LANG, \
                           CFG_SITE_NAME, \
                           CFG_SITE_NAME_INTL,\
                           CFG_WEBCOMMENT_ALLOW_REVIEWS, \
                           CFG_WEBCOMMENT_ALLOW_COMMENTS

from invenio.messages import gettext_set_language

class Template:
    """templating class, refer to webcomment.py for examples of call"""

    def tmpl_get_first_comments_without_ranking(self, recID, ln, comments, nb_comments_total, warnings):
        """
        @param recID: record id
        @param ln: language
        @param comments: tuple as returned from webcomment.py/query_retrieve_comments_or_remarks
        @param nb_comments_total: total number of comments for this record
        @param warnings: list of warning tuples (warning_msg, arg1, arg2, ...)
        @return html of comments
        """

        # load the right message language
        _ = gettext_set_language(ln)

        # naming data fields of comments
        c_nickname = 0
        c_user_id = 1
        c_date_creation = 2
        c_body = 3
        c_id = 4

        warnings = self.tmpl_warnings(warnings, ln)

        # comments
        comment_rows = ''
        for comment in comments:
            if comment[c_nickname]:
                nickname = comment[c_nickname]
                display = nickname
            else:
                (uid, nickname, display) = get_user_info(comment[c_user_id])
            messaging_link = self.create_messaging_link(nickname, display, ln)
            comment_rows += """
                    <tr>
                        <td>"""
            report_link = '%s/record/%s/comments/report?ln=%s&amp;comid=%s' % (CFG_SITE_URL, recID, ln, comment[c_id])
            reply_link = '%s/record/%s/comments/add?ln=%s&amp;comid=%s&amp;action=REPLY' % (CFG_SITE_URL, recID, ln, comment[c_id])
            comment_rows += self.tmpl_get_comment_without_ranking(ln=ln, nickname=messaging_link,
                                                                  date_creation=comment[c_date_creation],
                                                                  body=comment[c_body],
                                                                  report_link=report_link, reply_link=reply_link)
            comment_rows += """
                            <br />
                            <br />
                        </td>
                    </tr>"""

        # write button
        write_button_label = _("Write a comment")
        write_button_link = '%s/record/%s/comments/add' % (CFG_SITE_URL, recID)
        write_button_form = '<input type="hidden" name="ln" value="%s"/>' % ln
        write_button_form = self.createhiddenform(action=write_button_link, method="get", text=write_button_form, button=write_button_label)

        # output
        if nb_comments_total > 0:
            out = warnings
            comments_label = len(comments) > 1 and _("Showing the latest %i comments:") % len(comments) \
                             or ""
            out += """
<table>
  <tr>
    <td class="blocknote">%(comment_title)s</td>
  </tr>
</table>
%(comments_label)s<br />
<table border="0" cellspacing="5" cellpadding="5" width="100%%">
  %(comment_rows)s
</table>
%(view_all_comments_link)s
<br />
<br />
%(write_button_form)s<br />""" % \
            {'comment_title': _("Discuss this document"),
             'comments_label': comments_label,
             'nb_comments_total' : nb_comments_total,
             'recID': recID,
             'comment_rows': comment_rows,
             'tab': '&nbsp;'*4,
             'siteurl': CFG_SITE_URL,
             's': nb_comments_total>1 and 's' or "",
             'view_all_comments_link': nb_comments_total>0 and '''<a href="%s/record/%s/comments/display">View all %s comments</a>''' \
                                                                  % (CFG_SITE_URL, recID, nb_comments_total) or "",
             'write_button_form': write_button_form,
             'nb_comments': len(comments)
            }
        else:
            out = """
<!--  comments title table -->
<table>
  <tr>
    <td class="blocknote">%(discuss_label)s:</td>
  </tr>
</table>
%(detailed_info)s
<br />
%(form)s
<br />""" % {'form': write_button_form,
             'discuss_label': _("Discuss this document"),
             'detailed_info': _("Start a discussion about any aspect of this document.")
             }

        return out

    def tmpl_record_not_found(self, status='missing', recID="", ln=CFG_SITE_LANG):
        """
        Displays a page when bad or missing record ID was given.
        @param status:  'missing'   : no recID was given
                        'inexistant': recID doesn't have an entry in the database
                        'nan'       : recID is not a number
                        'invalid'   : recID is an error code, i.e. in the interval [-99,-1]
        @param return: body of the page
        """
        _ = gettext_set_language(ln)
        if status == 'inexistant':
            body = _("Sorry, the record %s does not seem to exist.") % (recID,)
        elif status in ('nan', 'invalid'):
            body = _("Sorry, %s is not a valid ID value.") % (recID,)
        else:
            body = _("Sorry, no record ID was provided.")

        body += "<br /><br />"
        link = "<a href=\"%s?ln=%s\">%s</a>." % (CFG_SITE_URL, ln, CFG_SITE_NAME_INTL.get(ln, CFG_SITE_NAME))
        body += _("You may want to start browsing from %s") % link
        return body

    def tmpl_get_first_comments_with_ranking(self, recID, ln, comments=None, nb_comments_total=None, avg_score=None, warnings=[]):
        """
        @param recID: record id
        @param ln: language
        @param comments: tuple as returned from webcomment.py/query_retrieve_comments_or_remarks
        @param nb_comments_total: total number of comments for this record
        @param avg_score: average score of all reviews
        @param warnings: list of warning tuples (warning_msg, arg1, arg2, ...)
        @return html of comments
        """
        # load the right message language
        _ = gettext_set_language(ln)

        # naming data fields of comments
        c_nickname = 0
        c_user_id = 1
        c_date_creation = 2
        c_body = 3
        c_nb_votes_yes = 4
        c_nb_votes_total = 5
        c_star_score = 6
        c_title = 7
        c_id = 8

        warnings = self.tmpl_warnings(warnings, ln)

        #stars
        if avg_score > 0:
            avg_score_img = 'stars-' + str(avg_score).split('.')[0] + '-' + str(avg_score).split('.')[1] + '.png'
        else:
            avg_score_img = "stars-0-0.png"

        # voting links
        useful_dict =   {   'siteurl'        : CFG_SITE_URL,
                            'recID'         : recID,
                            'ln'            : ln,
                            'yes_img'       : 'smchk_gr.gif', #'yes.gif',
                            'no_img'        : 'iconcross.gif' #'no.gif'
                        }
        link = '<a href="%(siteurl)s/record/%(recID)s/reviews/vote?ln=%(ln)s&amp;comid=%%(comid)s' % useful_dict
        useful_yes = link + '&amp;com_value=1">' + _("Yes") + '</a>'
        useful_no = link + '&amp;com_value=-1">' + _("No") + '</a>'

        #comment row
        comment_rows = ' '
        for comment in comments:
            if comment[c_nickname]:
                nickname = comment[c_nickname]
                display = nickname
            else:
                (uid, nickname, display) = get_user_info(comment[c_user_id])
            messaging_link = self.create_messaging_link(nickname, display, ln)

            comment_rows += '''
                    <tr>
                        <td>'''
            report_link = '%s/record/%s/reviews/report?ln=%s&amp;comid=%s' % (CFG_SITE_URL, recID, ln, comment[c_id])
            comment_rows += self.tmpl_get_comment_with_ranking(ln=ln, nickname=messaging_link,
                                                               date_creation=comment[c_date_creation],
                                                               body=comment[c_body],
                                                               nb_votes_total=comment[c_nb_votes_total],
                                                               nb_votes_yes=comment[c_nb_votes_yes],
                                                               star_score=comment[c_star_score],
                                                               title=comment[c_title], report_link=report_link)
            comment_rows += '''
                          %s %s / %s<br />''' % (_("Was this review helpful?"), useful_yes % {'comid':comment[c_id]}, useful_no % {'comid':comment[c_id]})
            comment_rows +=  '''
                          <br />
                        </td>
                      </tr>'''

        # write button
        write_button_link = '''%s/record/%s/reviews/add''' % (CFG_SITE_URL, recID)
        write_button_form = ' <input type="hidden" name="ln" value="%s"/>' % ln
        write_button_form = self.createhiddenform(action=write_button_link, method="get", text=write_button_form, button=_("Write a review"))

        if nb_comments_total > 0:
            avg_score_img = str(avg_score_img)
            avg_score = str(avg_score)
            nb_comments_total = str(nb_comments_total)
            score = '<b>'
            score += _("Average review score: %(x_nb_score)s based on %(x_nb_reviews)s reviews") % \
                {'x_nb_score': '</b><img src="' + CFG_SITE_URL + '/img/' + avg_score_img + '" alt="' + avg_score + '" />',
                 'x_nb_reviews': nb_comments_total}
            useful_label = _("Readers found the following %s reviews to be most helpful.")
            useful_label %= len(comments) > 1 and len(comments) or ""
            view_all_comments_link ='<a href="%s/record/%s/reviews/display?ln=%s&amp;do=hh">' % (CFG_SITE_URL, recID, ln)
            view_all_comments_link += _("View all %s reviews") % nb_comments_total
            view_all_comments_link += '</a><br />'

            out = warnings + """
                <!--  review title table -->
                <table>
                  <tr>
                    <td class="blocknote">%(comment_title)s:</td>
                  </tr>
                </table>
                %(score_label)s<br />
                %(useful_label)s
                <!-- review table -->
                <table style="border: 0px; border-collapse: separate; border-spacing: 5px; padding: 5px; width: 100%%">
                    %(comment_rows)s
                </table>
                %(view_all_comments_link)s
                %(write_button_form)s<br />
            """ % \
            {   'comment_title'         : _("Rate this document"),
                'score_label'           : score,
                'useful_label'          : useful_label,
                'recID'                 : recID,
                'view_all_comments'     : _("View all %s reviews") % (nb_comments_total,),
                'write_comment'         : _("Write a review"),
                'comment_rows'          : comment_rows,
                'tab'                   : '&nbsp;'*4,
                'siteurl'                : CFG_SITE_URL,
                'view_all_comments_link': nb_comments_total>0 and view_all_comments_link or "",
                'write_button_form'     : write_button_form
            }
        else:
            out = '''
                 <!--  review title table -->
                <table>
                  <tr>
                    <td class="blocknote">%s:</td>
                  </tr>
                </table>
                %s<br />
                %s
                <br />''' % (_("Rate this document"),
                           _("Be the first to review this document."),
                           write_button_form)
        return out

    def tmpl_get_comment_without_ranking(self, ln, nickname, date_creation, body, reply_link=None, report_link=None):
        """
        private function
        @param ln: language
        @param nickname: nickname
        @param date_creation: date comment was written
        @param body: comment body
        @param reply_link: if want reply and report, give the http links
        @param repot_link: if want reply and report, give the http links
        @return html table of comment
        """
        # load the right message language
        _ = gettext_set_language(ln)
        date_creation = convert_datetext_to_dategui(date_creation)
        out = ''
        final_body = email_quoted_txt2html(body)
        title = _('%(x_name)s wrote on %(x_date)s:') % {'x_name': nickname,
                                                        'x_date': '<i>' + date_creation + '</i>'}
        links = ''
        if reply_link:
            links += '<a href="' + reply_link +'">' + _("Reply") +'</a>'
            if report_link:
                links += ' | '
        if report_link:
            links += '<a href="' + report_link +'">' + _("Report abuse") + '</a>'
        out += """
<div style="margin-bottom:20px;background:#F9F9F9;border:1px solid #DDD">%(title)s<br />
    <blockquote>
%(body)s
    </blockquote>
<br />
<div style="float:right">%(links)s</div>
</div>""" % \
                {'title'         : '<div style="background-color:#EEE;padding:2px;"><img src="%s/img/user-icon-1-24x24.gif" alt="" />&nbsp;%s</div>' % (CFG_SITE_URL, title),
                 'body'          : final_body,
                 'links'         : links}
        return out

    def tmpl_get_comment_with_ranking(self, ln, nickname, date_creation, body, nb_votes_total, nb_votes_yes, star_score, title, report_link=None):
        """
        private function
        @param ln: language
        @param nickname: nickname
        @param date_creation: date comment was written
        @param body: comment body
        @param nb_votes_total: total number of votes for this review
        @param nb_votes_yes: number of positive votes for this record
        @param star_score: star score for this record
        @param title: title of review
        @return html table of review
        """
        # load the right message language
        _ = gettext_set_language(ln)

        if star_score > 0:
            star_score_img = 'stars-' + str(star_score) + '-0.png'
        else:
            star_score_img = 'stars-0-0.png'

        out = ""
        date_creation = convert_datetext_to_dategui(date_creation)
        reviewed_label = _("Reviewed by %(x_nickname)s on %(x_date)s") % {'x_nickname': nickname, 'x_date':date_creation}
        useful_label = _("%(x_nb_people)i out of %(x_nb_total)i people found this review useful") % {'x_nb_people': nb_votes_yes,
                                                                                                     'x_nb_total': nb_votes_total}
        links = ''
        if report_link:
            links += '<a href="' + report_link +'">' + _("Report abuse") + '</a>'
        _body = ''
        if body != '':
            _body = '''
      <blockquote>
%s
      </blockquote>''' % email_quoted_txt2html(body)

        out += '''
<div style="background:#F9F9F9;border:1px solid #DDD">
  <div style="background-color:#EEE;padding:2px;">
    <img src="%(siteurl)s/img/%(star_score_img)s" alt="%(star_score)s" style="margin-right:10px;"/><b>%(title)s</b><br />
      %(reviewed_label)s<br />
      %(useful_label)s
  </div>
  %(body)s
</div>
%(abuse)s''' % {'siteurl'        : CFG_SITE_URL,
               'star_score_img': star_score_img,
               'star_score'    : star_score,
               'title'         : title,
               'reviewed_label': reviewed_label,
               'useful_label'  : useful_label,
               'body'          : _body,
               'abuse'         : links
               }
        return out

    def tmpl_get_comments(self, recID, ln,
                          nb_per_page, page, nb_pages,
                          display_order, display_since,
                          CFG_WEBCOMMENT_ALLOW_REVIEWS,
                          comments, total_nb_comments,
                          avg_score,
                          warnings,
                          border=0, reviews=0,
                          total_nb_reviews=0,
                          nickname='', uid=-1, note='',score=5):
        """
        Get table of all comments
        @param recID: record id
        @param ln: language
        @param nb_per_page: number of results per page
        @param page: page number
        @param display_order:   hh = highest helpful score, review only
                                lh = lowest helpful score, review only
                                hs = highest star score, review only
                                ls = lowest star score, review only
                                od = oldest date
                                nd = newest date
        @param display_since:   all= no filtering by date
                                nd = n days ago
                                nw = n weeks ago
                                nm = n months ago
                                ny = n years ago
                                where n is a single digit integer between 0 and 9
        @param CFG_WEBCOMMENT_ALLOW_REVIEWS: is ranking enable, get from config.py/CFG_WEBCOMMENT_ALLOW_REVIEWS
        @param comments: tuple as returned from webcomment.py/query_retrieve_comments_or_remarks
        @param total_nb_comments: total number of comments for this record
        @param avg_score: average score of reviews for this record
        @param warnings: list of warning tuples (warning_msg, color)
        @param border: boolean, active if want to show border around each comment/review
        @param reviews: boolean, enabled for reviews, disabled for comments
        """
        # load the right message language
        _ = gettext_set_language(ln)
        # naming data fields of comments
        if reviews:
            c_nickname = 0
            c_user_id = 1
            c_date_creation = 2
            c_body = 3
            c_nb_votes_yes = 4
            c_nb_votes_total = 5
            c_star_score = 6
            c_title = 7
            c_id = 8
            discussion = 'reviews'
            comments_link = '<a href="%s/record/%s/comments/">%s</a> (%i)' % (CFG_SITE_URL, recID, _('Comments'), total_nb_comments)
            reviews_link = '<b>%s (%i)</b>' % (_('Reviews'), total_nb_reviews)
            add_comment_or_review = self.tmpl_add_comment_form_with_ranking(recID, uid, nickname, ln, '', score, note, warnings, show_title_p=True)
        else:
            c_nickname = 0
            c_user_id = 1
            c_date_creation = 2
            c_body = 3
            c_id = 4
            discussion = 'comments'
            comments_link = '<b>%s (%i)</b>' % (_('Comments'), total_nb_comments)
            reviews_link = '<a href="%s/record/%s/reviews/">%s</a> (%i)' % (CFG_SITE_URL, recID, _('Reviews'), total_nb_reviews)
            add_comment_or_review = self.tmpl_add_comment_form(recID, uid, nickname, ln, note, warnings)

        # voting links
        useful_dict =   {   'siteurl'        : CFG_SITE_URL,
                            'recID'         : recID,
                            'ln'            : ln,
                            'do'            : display_order,
                            'ds'            : display_since,
                            'nb'            : nb_per_page,
                            'p'             : page,
                            'reviews'       : reviews,
                            'discussion'    : discussion
                        }
        useful_yes = '<a href="%(siteurl)s/record/%(recID)s/%(discussion)s/vote?ln=%(ln)s&amp;comid=%%(comid)s&amp;com_value=1&amp;do=%(do)s&amp;ds=%(ds)s&amp;nb=%(nb)s&amp;p=%(p)s&amp;referer=%(siteurl)s/record/%(recID)s/%(discussion)s/display">' + _("Yes") + '</a>'
        useful_yes %= useful_dict
        useful_no = '<a href="%(siteurl)s/record/%(recID)s/%(discussion)s/vote?ln=%(ln)s&amp;comid=%%(comid)s&amp;com_value=-1&amp;do=%(do)s&amp;ds=%(ds)s&amp;nb=%(nb)s&amp;p=%(p)s&amp;referer=%(siteurl)s/record/%(recID)s/%(discussion)s/display">' + _("No") + '</a>'
        useful_no %= useful_dict
        warnings = self.tmpl_warnings(warnings, ln)

        link_dic =  {   'siteurl'    : CFG_SITE_URL,
                        'module'    : 'comments',
                        'function'  : 'index',
                        'discussion': discussion,
                        'arguments' : 'do=%s&amp;ds=%s&amp;nb=%s' % (display_order, display_since, nb_per_page),
                        'arg_page'  : '&amp;p=%s' % page,
                        'page'      : page,
                        'rec_id'    : recID}


        ## comments table
        comments_rows = ''
        for comment in comments:
            if comment[c_nickname]:
                _nickname = comment[c_nickname]
                display = _nickname
            else:
                (uid, _nickname, display) = get_user_info(comment[c_user_id])
            messaging_link = self.create_messaging_link(_nickname, display, ln)
            # do NOT delete the HTML comment below. It is used for parsing... (I plead unguilty!)
            comments_rows += """
<!-- start comment row -->
<tr>
  <td>"""
            if not reviews:
                report_link = '%(siteurl)s/record/%(recID)s/comments/report?ln=%(ln)s&amp;comid=%%(comid)s&amp;do=%(do)s&amp;ds=%(ds)s&amp;nb=%(nb)s&amp;p=%(p)s&amp;referer=%(siteurl)s/record/%(recID)s/comments/display' % useful_dict % {'comid':comment[c_id]}
                reply_link = '%(siteurl)s/record/%(recID)s/comments/add?ln=%(ln)s&amp;action=REPLY&amp;comid=%%(comid)s' % useful_dict % {'comid':comment[c_id]}
                comments_rows += self.tmpl_get_comment_without_ranking(ln, messaging_link, comment[c_date_creation], comment[c_body], reply_link, report_link)
            else:
                report_link = '%(siteurl)s/record/%(recID)s/reviews/report?ln=%(ln)s&amp;comid=%%(comid)s&amp;do=%(do)s&amp;ds=%(ds)s&amp;nb=%(nb)s&amp;p=%(p)s&amp;referer=%(siteurl)s/record/%(recID)s/reviews/display' % useful_dict % {'comid': comment[c_id]}
                comments_rows += self.tmpl_get_comment_with_ranking(ln, messaging_link, comment[c_date_creation], comment[c_body], comment[c_nb_votes_total], comment[c_nb_votes_yes], comment[c_star_score], comment[c_title])
                helpful_label = _("Was this review helpful?")
                report_abuse_label = "(" + _("Report abuse") + ")"
                comments_rows += """
    <table>
      <tr>
        <td>%(helpful_label)s %(tab)s</td>
        <td> %(yes)s </td>
        <td> / </td>
        <td> %(no)s </td>
        <td class="reportabuse">%(tab)s%(tab)s<a href="%(report)s">%(report_abuse_label)s</a></td>
      </tr>
    </table>""" \
                % {'helpful_label': helpful_label,
                   'yes'          : useful_yes % {'comid':comment[c_id]},
                   'no'           : useful_no % {'comid':comment[c_id]},
                   'report'       : report_link % {'comid':comment[c_id]},
                   'report_abuse_label': report_abuse_label,
                   'tab'       : '&nbsp;'*2}
            # do NOT remove HTML comment below. It is used for parsing...
            comments_rows += """
  </td>
</tr>
<!-- end comment row -->"""

        ## page links
        page_links = ''
        # Previous
        if page != 1:
            link_dic['arg_page'] = 'p=%s' % (page - 1)
            page_links += '<a href=\"%(siteurl)s/record/%(rec_id)s/%(discussion)s/%(function)s?%(arguments)s&amp;%(arg_page)s\">&lt;&lt;</a> ' % link_dic
        else:
            page_links += ' %s ' % ('&nbsp;'*(len(_('Previous'))+7))
        # Page Numbers
        for i in range(1, nb_pages+1):
            link_dic['arg_page'] = 'p=%s' % i
            link_dic['page'] = '%s' % i
            if i != page:
                page_links += '''
                <a href=\"%(siteurl)s/record/%(rec_id)s/%(discussion)s/%(function)s?%(arguments)s&amp;%(arg_page)s\">%(page)s</a> ''' % link_dic
            else:
                page_links += ''' <b>%s</b> ''' % i
        # Next
        if page != nb_pages:
            link_dic['arg_page'] = 'p=%s' % (page + 1)
            page_links += '''
                <a href=\"%(siteurl)s/record/%(rec_id)s/%(discussion)s/%(function)s?%(arguments)s&amp;%(arg_page)s\">&gt;&gt;</a> ''' % link_dic
        else:
            page_links += '%s' % ('&nbsp;'*(len(_('Next'))+7))

        ## stuff for ranking if enabled
        if reviews:
            if avg_score > 0:
                avg_score_img = 'stars-' + str(avg_score).split('.')[0] + '-' + str(avg_score).split('.')[1] + '.png'
            else:
                avg_score_img = "stars-0-0.png"
            ranking_average = '<br /><b>'
            ranking_average += _("Average review score: %(x_nb_score)s based on %(x_nb_reviews)s reviews") % \
                {'x_nb_score': '</b><img src="' + CFG_SITE_URL + '/img/' + avg_score_img + '" alt="' + str(avg_score) + '" />',
                 'x_nb_reviews': str(total_nb_reviews)}
            ranking_average += '<br />'
        else:
            ranking_average = ""

        write_button_link = '''%s/record/%s/%s/add''' % (CFG_SITE_URL, recID, discussion)
        write_button_form = '<input type="hidden" name="ln" value="%s"/>'
        write_button_form = self.createhiddenform(action=write_button_link,
                                                  method="get",
                                                  text=write_button_form,
                                                  button = reviews and _('Write a review') or _('Write a comment'))

        if reviews:
            total_label = _("There is a total of %s reviews")
        else:
            total_label = _("There is a total of %s comments")
        total_label %= total_nb_comments

        review_or_comment_first = ''
        if reviews == 0 and total_nb_comments == 0:
            review_or_comment_first = _("Start a discussion about any aspect of this document.")
        elif reviews == 1 and total_nb_reviews == 0:
            review_or_comment_first = _("Be the first to review this document.")

        # do NOT remove the HTML comments below. Used for parsing
        body = '''
%(comments_and_review_tabs)s
<!-- start comments table -->
<table style="border: %(border)spx solid black; width: 95%%; margin:10px;font-size:small">
  %(comments_rows)s
</table>
<!-- end comments table -->
%(review_or_comment_first)s
<br />''' % \
        {   'record_label': _("Record"),
            'back_label': _("Back to search results"),
            'total_label': total_label,
            'write_button_form' : write_button_form,
            'write_button_form_again' : total_nb_comments>3 and write_button_form or "",
            'comments_rows'             : comments_rows,
            'total_nb_comments'         : total_nb_comments,
            'comments_or_reviews'       : reviews and _('review') or _('comment'),
            'comments_or_reviews_title' : reviews and _('Review') or _('Comment'),
            'siteurl'                    : CFG_SITE_URL,
            'module'                    : "comments",
            'recid'                     : recID,
            'ln'                        : ln,
            'border'                    : border,
            'ranking_avg'               : ranking_average,
            'comments_and_review_tabs'  : CFG_WEBCOMMENT_ALLOW_REVIEWS and \
                                       CFG_WEBCOMMENT_ALLOW_COMMENTS and \
                                       '%s | %s <br />' % \
                                       (comments_link, reviews_link) or '',
            'review_or_comment_first'   : review_or_comment_first
        }

        # form is not currently used. reserved for an eventual purpose
        #form = """
        #        Display             <select name="nb" size="1"> per page
        #                                <option value="all">All</option>
        #                                <option value="10">10</option>
        #                                <option value="25">20</option>
        #                                <option value="50">50</option>
        #                                <option value="100" selected="selected">100</option>
        #                            </select>
        #        comments per page that are    <select name="ds" size="1">
        #                                <option value="all" selected="selected">Any age</option>
        #                                <option value="1d">1 day old</option>
        #                                <option value="3d">3 days old</option>
        #                                <option value="1w">1 week old</option>
        #                                <option value="2w">2 weeks old</option>
        #                                <option value="1m">1 month old</option>
        #                                <option value="3m">3 months old</option>
        #                                <option value="6m">6 months old</option>
        #                                <option value="1y">1 year old</option>
        #                            </select>
        #        and sorted by       <select name="do" size="1">
        #                                <option value="od" selected="selected">Oldest first</option>
        #                                <option value="nd">Newest first</option>
        #                                %s
        #                            </select>
        #    """ % \
        #        (reviews==1 and '''
        #                                <option value=\"hh\">most helpful</option>
        #                                <option value=\"lh\">least helpful</option>
        #                                <option value=\"hs\">highest star ranking</option>
        #                                <option value=\"ls\">lowest star ranking</option>
        #                            </select>''' or '''
        #                            </select>''')
        #
        #form_link = "%(siteurl)s/%(module)s/%(function)s" % link_dic
        #form = self.createhiddenform(action=form_link, method="get", text=form, button='Go', recid=recID, p=1)
        pages = """
<div>
%(v_label)s %(comments_or_reviews)s %(results_nb_lower)s-%(results_nb_higher)s <br />
%(page_links)s
</div>
""" % \
        {'v_label': _("Viewing"),
         'page_links': _("Page:") + page_links ,
         'comments_or_reviews': reviews and _('review') or _('comment'),
         'results_nb_lower': len(comments)>0 and ((page-1) * nb_per_page)+1 or 0,
         'results_nb_higher': page == nb_pages and (((page-1) * nb_per_page) + len(comments)) or (page * nb_per_page)}

        if nb_pages > 1:
            #body = warnings + body + form + pages
            body = warnings + body + pages + add_comment_or_review
        else:
            body = warnings + body + add_comment_or_review

        return '<div style="margin-left:10px;margin-right:10px;">' + body + '</div>'

    def create_messaging_link(self, to, display_name, ln=CFG_SITE_LANG):
        """prints a link to the messaging system"""
        link = "%s/yourmessages/write?msg_to=%s&amp;ln=%s" % (CFG_SITE_URL, to, ln)
        if to:
            return '<a href="%s" class="maillink">%s</a>' % (link, display_name)
        else:
            return display_name

    def createhiddenform(self, action="", method="get", text="", button="confirm", cnfrm='', **hidden):
        """
        create select with hidden values and submit button
        @param action: name of the action to perform on submit
        @param method: 'get' or 'post'
        @param text: additional text, can also be used to add non hidden input
        @param button: value/caption on the submit button
        @param cnfrm: if given, must check checkbox to confirm
        @param **hidden: dictionary with name=value pairs for hidden input
        @return html form
        """

        output  = """
<form action="%s" method="%s">""" % (action, method.lower().strip() in ['get','post'] and method or 'get')
        output += """
  <table style="width:90%">
    <tr>
      <td style="vertical-align: top">
"""
        output += text + '\n'
        if cnfrm:
            output += """
        <input type="checkbox" name="confirm" value="1" />"""
        for key in hidden.keys():
            if type(hidden[key]) is list:
                for value in hidden[key]:
                    output += """
        <input type="hidden" name="%s" value="%s" />""" % (key, value)
            else:
                output += """
        <input type="hidden" name="%s" value="%s" />""" % (key, hidden[key])
        output += """
      </td>
    </tr>
    <tr>
      <td>"""
        output += """
        <input class="adminbutton" type="submit" value="%s" />""" % (button, )
        output += """
      </td>
    </tr>
  </table>
</form>"""
        return output

    def tmpl_warnings(self, warnings, ln=CFG_SITE_LANG):
        """
        Prepare the warnings list
        @param warnings: list of warning tuples (warning_msg, arg1, arg2, etc)
        @return html string of warnings
        """
        red_text_warnings = ['WRN_WEBCOMMENT_FEEDBACK_NOT_RECORDED',
                            'WRN_WEBCOMMENT_ALREADY_VOTED']
        green_text_warnings = ['WRN_WEBCOMMENT_FEEDBACK_RECORDED']
        from invenio.errorlib import get_msgs_for_code_list
        span_class = 'important'
        out = ""
        if type(warnings) is not list:
            warnings = [warnings]
        if len(warnings) > 0:
            warnings_parsed = get_msgs_for_code_list(warnings, 'warning', ln)
            for (warning_code, warning_text) in warnings_parsed:
                if not warning_code.startswith('WRN'):
                    #display only warnings that begin with WRN to user
                    continue
                if warning_code in red_text_warnings:
                    span_class = 'important'
                elif warning_code in green_text_warnings:
                    span_class = 'exampleleader'
                else:
                    span_class = 'important'
                out += '''
                    <span class="%(span_class)s">%(warning)s</span><br />''' % \
                    {   'span_class'    :   span_class,
                        'warning'       :   warning_text         }
            return out
        else:
            return ""

    def tmpl_add_comment_form(self, recID, uid, nickname, ln, msg, warnings):
        """
        Add form for comments
        @param recID: record id
        @param uid: user id
        @param ln: language
        @param msg: comment body contents for when refreshing due to warning
        @param warnings: list of warning tuples (warning_msg, color)
        @return html add comment form
        """
        _ = gettext_set_language(ln)
        link_dic =  {   'siteurl'    : CFG_SITE_URL,
                        'module'    : 'comments',
                        'function'  : 'add',
                        'arguments' : 'ln=%s&amp;action=%s' % (ln, 'SUBMIT'),
                        'recID'     : recID}

        # FIXME a cleaner handling of nicknames is needed.
        if not nickname:
            (uid, nickname, display) = get_user_info(uid)
        if nickname:
            note = _("Note: Your nickname, %s, will be displayed as author of this comment") % ('<i>' + nickname + '</i>')
        else:
            (uid, nickname, display) = get_user_info(uid)
            link = '<a href="%s/youraccount/edit">' % CFG_SITE_SECURE_URL
            note = _("Note: you have not %(x_url_open)sdefined your nickname%(x_url_close)s. %(x_nickname)s will be displayed as the author of this comment.") % \
                {'x_url_open': link,
                 'x_url_close': '</a>',
                 'x_nickname': ' <br /><i>' + display + '</i>'}

        #from invenio.search_engine import print_record
        #record_details = print_record(recID=recID, format='hb', ln=ln)

        warnings = self.tmpl_warnings(warnings, ln)
        form = """<div><h2>%(add_comment)s</h2>

<textarea name="msg" cols="80" rows="20" style="width:90%%">%(msg)s</textarea>
<br />
                <span class="reportabuse">%(note)s</span>
                </div>
                """ % {'msg': msg,
                               'note': note,
                               #'record': record_details,
                               'record_label': _("Article") + ":",
                               'comment_label': _("Comment") + ":",
                               'add_comment': _('Add comment')}
        form_link = "%(siteurl)s/record/%(recID)s/comments/%(function)s?%(arguments)s" % link_dic
        form = self.createhiddenform(action=form_link, method="post", text=form, button='Add comment')
        return warnings + form

    def tmpl_add_comment_form_with_ranking(self, recID, uid, nickname, ln, msg, score, note,
                                           warnings, show_title_p=False):
        """
        Add form for reviews
        @param recID: record id
        @param uid: user id
        @param ln: language
        @param msg: comment body contents for when refreshing due to warning
        @param score: review score
        @param note: review title
        @param warnings: list of warning tuples (warning_msg, color)
        @param show_title_p: if True, prefix the form with "Add Review" as title
        @return html add review form
        """
        _ = gettext_set_language(ln)
        link_dic =  {   'siteurl'    : CFG_SITE_URL,
                        'module'    : 'comments',
                        'function'  : 'add',
                        'arguments' : 'ln=%s&amp;action=%s' % (ln, 'SUBMIT'),
                        'recID'     : recID}
        warnings = self.tmpl_warnings(warnings, ln)

        #from search_engine import print_record
        #record_details = print_record(recID=recID, format='hb', ln=ln)
        if nickname:
            note_label = _("Note: Your nickname, %s, will be displayed as the author of this review.")
            note_label %= ('<i>' + nickname + '</i>')
        else:
            (uid, nickname, display) = get_user_info(uid)
            link = '<a href="%s/youraccount/edit">' % CFG_SITE_SECURE_URL
            note_label = _("Note: you have not %(x_url_open)sdefined your nickname%(x_url_close)s. %(x_nickname)s will be displayed as the author of this comment.") % \
                {'x_url_open': link,
                 'x_url_close': '</a>',
                 'x_nickname': ' <br /><i>' + display + '</i>'}

        selected0 = ''
        selected1 = ''
        selected2 = ''
        selected3 = ''
        selected4 = ''
        selected5 = ''
        if score == 0:
            selected0 = ' selected="selected"'
        elif score == 1:
            selected1 = ' selected="selected"'
        elif score == 2:
            selected2 = ' selected="selected"'
        elif score == 3:
            selected3 = ' selected="selected"'
        elif score == 4:
            selected4 = ' selected="selected"'
        elif score == 5:
            selected5 = ' selected="selected"'
        form = """%(add_review)s
                <table style="width: 100%%">
                    <tr>
                      <td style="padding-bottom: 10px;">%(rate_label)s:
                        <select name=\"score\" size=\"1\">
                          <option value=\"0\"%(selected0)s>-%(select_label)s-</option>
                          <option value=\"5\"%(selected5)s>***** (best)</option>
                          <option value=\"4\"%(selected4)s>****</option>
                          <option value=\"3\"%(selected3)s>***</option>
                          <option value=\"2\"%(selected2)s>**</option>
                          <option value=\"1\"%(selected1)s>*     (worst)</option>
                        </select>
                      </td>
                    </tr>
                    <tr>
                      <td>%(title_label)s:</td>
                    </tr>
                    <tr>
                      <td style="padding-bottom: 10px;">
                        <input type="text" name="note" maxlength="250" style="width:90%%" value="%(note)s" />
                      </td>
                    </tr>
                    <tr>
                      <td>%(write_label)s:</td>
                    </tr>
                    <tr>
                      <td>
<textarea name="msg" cols="80" rows="20" style="width:90%%">%(msg)s</textarea>
                      </td>
                    </tr>
                    <tr>
                      <td class="reportabuse">%(note_label)s</td></tr>
                </table>
                """ % {'article_label': _('Article'),
                               'rate_label': _("Rate this article"),
                               'select_label': _("Select a score"),
                               'title_label': _("Give a title to your review"),
                               'write_label': _("Write your review"),
                               'note_label': note_label,
                               'note'      : note!='' and note or "",
                               'msg'       : msg!='' and msg or "",
                               #'record'    : record_details
                               'add_review': show_title_p and ('<h2>'+_('Add review')+'</h2>') or '',
                               'selected0': selected0,
                               'selected1': selected1,
                               'selected2': selected2,
                               'selected3': selected3,
                               'selected4': selected4,
                               'selected5': selected5
                               }
        form_link = "%(siteurl)s/record/%(recID)s/reviews/%(function)s?%(arguments)s" % link_dic
        form = self.createhiddenform(action=form_link, method="post", text=form, button=_('Add Review'))
        return warnings + form

    def tmpl_add_comment_successful(self, recID, ln, reviews, warnings):
        """
        @param recID: record id
        @param ln: language
        @return html page of successfully added comment/review
        """
        _ = gettext_set_language(ln)
        link_dic =  {   'siteurl'    : CFG_SITE_URL,
                        'module'    : 'comments',
                        'function'  : 'display',
                        'arguments' : 'ln=%s&amp;do=od' % ln,
                        'recID'     : recID,
                        'discussion': reviews==1 and 'reviews' or 'comments'}
        link = "%(siteurl)s/record/%(recID)s/%(discussion)s/%(function)s?%(arguments)s" % link_dic
        if warnings:
            out = self.tmpl_warnings(warnings, ln)  + '<br /><br />'
        else:
            if reviews:
                out = _("Your review was successfully added.") + '<br /><br />'
            else:
                out = _("Your comment was successfully added.") + '<br /><br />'
        out += '<a href="%s">' % link
        out += _('Back to record') + '</a>'
        return out

    def tmpl_create_multiple_actions_form(self,
                                          form_name="",
                                          form_action="",
                                          method="get",
                                          action_display={},
                                          action_field_name="",
                                          button_label="",
                                          button_name="",
                                          content="",
                                          **hidden):
        """ Creates an HTML form with a multiple choice of actions and a button to select it.
        @param form_action: link to the receiver of the formular
        @param form_name: name of the HTML formular
        @param method: either 'GET' or 'POST'
        @param action_display: dictionary of actions.
                                    action is HTML name (name of action)
                                    display is the string provided in the popup
        @param action_field_name: html name of action field
        @param button_label: what's written on the button
        @param button_name: html name of the button
        @param content: what's inside te formular
        @param **hidden: dictionary of name/value pairs of hidden fields.
        """
        output  = """
<form action="%s" method="%s">""" % (form_action, method)
        output += """
  <table>
    <tr>
      <td style="vertical-align: top" colspan="2">
"""
        output += content + '\n'
        for key in hidden.keys():
            if type(hidden[key]) is list:
                for value in hidden[key]:
                    output += """
        <input type="hidden" name="%s" value="%s" />""" % (key, value)
            else:
                output += """
        <input type="hidden" name="%s" value="%s" />""" % (key, hidden[key])
        output += """
      </td>
    </tr>
    <tr>
    <td style="text-align:right;">"""
        if type(action_display) is dict and len(action_display.keys()):
            output += """
        <select name="%s">""" % action_field_name
            for (key, value) in action_display.items():
                output += """
          <option value="%s">%s</option>""" % (key, value)
            output += """
        </select>"""
        output += """
      </td>
      <td style="text-align:left;">
        <input class="adminbutton" type="submit" value="%s" name="%s"/>""" % (button_label, button_name)
        output += """
      </td>
    </tr>
  </table>
</form>"""
        return output

    def tmpl_admin_index(self, ln):
        """
        Index page
        """
        # load the right message language
        _ = gettext_set_language(ln)

        out = '<ol>'
        if CFG_WEBCOMMENT_ALLOW_COMMENTS or CFG_WEBCOMMENT_ALLOW_REVIEWS:
            if CFG_WEBCOMMENT_ALLOW_COMMENTS:
                out += '<li><a href="%(siteurl)s/admin/webcomment/webcommentadmin.py/comments?ln=%(ln)s&amp;reviews=0">%(reported_cmt_label)s</a></li>' % \
                    {'siteurl': CFG_SITE_URL, 'ln': ln, 'reported_cmt_label': _("View all reported comments")}
            if CFG_WEBCOMMENT_ALLOW_REVIEWS:
                out += '<li><a href="%(siteurl)s/admin/webcomment/webcommentadmin.py/comments?ln=%(ln)s&amp;reviews=1">%(reported_rev_label)s</a></li>' % \
                    {'siteurl': CFG_SITE_URL, 'ln': ln, 'reported_rev_label': _("View all reported reviews")}
            out += """
                <li><a href="%(siteurl)s/admin/webcomment/webcommentadmin.py/delete?ln=%(ln)s&amp;comid=-1">%(delete_label)s</a></li>
                <li><a href="%(siteurl)s/admin/webcomment/webcommentadmin.py/users?ln=%(ln)s">%(view_users)s</a></li>
                <li><a href="%(siteurl)s/help/admin/webcomment-admin-guide">%(guide)s</a></li>
                """ % {'siteurl'    : CFG_SITE_URL,
                       'delete_label': _("Delete a specific comment/review (by ID)"),
                       'view_users': _("View all users who have been reported"),
                       'ln'        : ln,
                       'guide'     : _("Guide")}
        else:
            out += _("Comments and reviews are disabled") + '<br />'
        out += '</ol>'
        from invenio.bibrankadminlib import addadminbox
        return addadminbox('<b>%s</b>'%_("Menu"), [out])

    def tmpl_admin_delete_form(self, ln, warnings):
        """
        @param warnings: list of warning_tuples where warning_tuple is (warning_message, text_color)
                         see tmpl_warnings, color is optional
        """
        # load the right message language
        _ = gettext_set_language(ln)

        warnings = self.tmpl_warnings(warnings, ln)

        out = '''
        <br />
        %s<br />
        <br />'''%_("Please enter the ID of the comment/review so that you can view it before deciding whether to delete it or not")
        form = '''
            <table>
                <tr>
                    <td>%s</td>
                    <td><input type=text name="comid" size="10" maxlength="10" value="" /></td>
                </tr>
                <tr>
                    <td><br /></td>
                <tr>
            </table>
            <br />
        ''' %_("Comment ID:")
        form_link = "%s/admin/webcomment/webcommentadmin.py/delete?ln=%s" % (CFG_SITE_URL, ln)
        form = self.createhiddenform(action=form_link, method="get", text=form, button=_('View Comment'))
        return warnings + out + form

    def tmpl_admin_users(self, ln, users_data):
        """
        @param users_data:  tuple of ct, i.e. (ct, ct, ...)
                            where ct is a tuple (total_number_reported, total_comments_reported, total_reviews_reported, total_nb_votes_yes_of_reported,
                                                 total_nb_votes_total_of_reported, user_id, user_email, user_nickname)
                            sorted by order of ct having highest total_number_reported
        """
        _ = gettext_set_language(ln)
        u_reports = 0
        u_comment_reports = 1
        u_reviews_reports = 2
        u_nb_votes_yes = 3
        u_nb_votes_total = 4
        u_uid = 5
        u_email = 6
        u_nickname = 7

        if not users_data:
            return self.tmpl_warnings([(_("There have been no reports so far."), 'green')])

        user_rows = ""
        for utuple in users_data:
            com_label = _("View all %s reported comments") % utuple[u_comment_reports]
            com_link = '''<a href="%s/admin/webcomment/webcommentadmin.py/comments?ln=%s&amp;uid=%s&amp;reviews=0">%s</a><br />''' % \
                          (CFG_SITE_URL, ln, utuple[u_uid], com_label)
            rev_label = _("View all %s reported reviews") % utuple[u_reviews_reports]
            rev_link = '''<a href="%s/admin/webcomment/webcommentadmin.py/comments?ln=%s&amp;uid=%s&amp;reviews=1">%s</a>''' % \
                          (CFG_SITE_URL, ln, utuple[u_uid], rev_label)
            if not utuple[u_nickname]:
                user_info = get_user_info(utuple[u_uid])
                nickname = user_info[2]
            else:
                nickname = utuple[u_nickname]
            if CFG_WEBCOMMENT_ALLOW_REVIEWS:
                review_row = """
<td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
<td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
<td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>"""
                review_row %= (utuple[u_nb_votes_yes],
                               utuple[u_nb_votes_total] - utuple[u_nb_votes_yes],
                               utuple[u_nb_votes_total])
            else:
                review_row = ''
            user_rows += """
<tr>
  <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%(nickname)s</td>
  <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%(email)s</td>
  <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%(uid)s</td>%(review_row)s
  <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray; font-weight: bold;">%(reports)s</td>
  <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%(com_link)s%(rev_link)s</td>
</tr>""" % { 'nickname'  : nickname,
             'email'     : utuple[u_email],
             'uid'       : utuple[u_uid],
             'reports'   : utuple[u_reports],
             'review_row': review_row,
             'siteurl'    : CFG_SITE_URL,
             'ln'        : ln,
             'com_link'  : CFG_WEBCOMMENT_ALLOW_COMMENTS and com_link or "",
             'rev_link'  : CFG_WEBCOMMENT_ALLOW_REVIEWS and rev_link or ""
             }

        out = "<br />"
        out += _("Here is a list, sorted by total number of reports, of all users who have had a comment reported at least once.")
        out += """
<br />
<br />
<table class="admin_wvar" style="width: 100%%;">
  <thead>
    <tr class="adminheaderleft">
      <th>"""
        out += _("Nickname") + '</th>\n'
        out += '<th>' + _("Email") + '</th>\n'
        out += '<th>' + _("User ID") + '</th>\n'
        if CFG_WEBCOMMENT_ALLOW_REVIEWS > 0:
            out += '<th>' + _("Number positive votes") + '</th>\n'
            out += '<th>' + _("Number negative votes") + '</th>\n'
            out += '<th>' + _("Total number votes") + '</th>\n'
        out += '<th>' + _("Total number of reports") + '</th>\n'
        out += '<th>' + _("View all user's reported comments/reviews") + '</th>\n'
        out += """
    </tr>
  </thead>
  <tbody>%s
  </tbody>
</table>
        """ % user_rows
        return out

    def tmpl_admin_select_comment_checkbox(self, cmt_id):
        """ outputs a checkbox named "comidXX" where XX is cmt_id """
        return '<input type="checkbox" name="comid%i" />' % int(cmt_id)

    def tmpl_admin_user_info(self, ln, nickname, uid, email):
        """ prepares informations about a user"""
        _ = gettext_set_language(ln)
        out = """
%(nickname_label)s: %(messaging)s<br />
%(uid_label)s: %(uid)i<br />
%(email_label)s: <a href="mailto:%(email)s">%(email)s</a>"""
        out %= {'nickname_label': _("Nickname"),
                'messaging':  self.create_messaging_link(uid, nickname, ln),
                'uid_label': _("User ID"),
                'uid': int(uid),
                'email_label': _("Email"),
                'email': email}
        return out

    def tmpl_admin_review_info(self, ln, reviews, nb_reports, cmt_id, rec_id):
        """ outputs information about a review """
        _ = gettext_set_language(ln)
        if reviews:
            reported_label = _("This review has been reported %i times")
        else:
            reported_label = _("This comment has been reported %i times")
        reported_label %= int(nb_reports)
        out = """
%(reported_label)s<br />
<a href="%(siteurl)s/record/%(rec_id)i?ln=%(ln)s">%(rec_id_label)s</a><br />
%(cmt_id_label)s"""
        out %= {'reported_label': reported_label,
                'rec_id_label': _("Record") + ' #' + str(rec_id),
                'siteurl': CFG_SITE_URL,
                'rec_id': int(rec_id),
                'cmt_id_label': _("Comment") + ' #' + str(cmt_id),
                'ln': ln}
        return out

    def tmpl_admin_comments(self, ln, uid, comID, comment_data, reviews):
        """
        @param comment_data: same type of tuple as that
        which is returned by webcomment.py/query_retrieve_comments_or_remarks i.e.
                             tuple of comment where comment is
                             tuple (nickname,
                                    date_creation,
                                    body,
                                    id) if ranking disabled or
                             tuple (nickname,
                                    date_creation,
                                    body,
                                    nb_votes_yes,
                                    nb_votes_total,
                                    star_score,
                                    title,
                                    id)
        """
        _ = gettext_set_language(ln)
        comments = []
        comments_info = []
        checkboxes = []
        users = []
        for (cmt_tuple, meta_data) in comment_data:
            if reviews:
                comments.append(self.tmpl_get_comment_with_ranking(ln,
                                                                   cmt_tuple[0],#nickname
                                                                   cmt_tuple[2],#date_creation
                                                                   cmt_tuple[3],#body
                                                                   cmt_tuple[5],#nb_votes_total
                                                                   cmt_tuple[4],#nb_votes_yes
                                                                   cmt_tuple[6],#star_score
                                                                   cmt_tuple[7]))#title
            else:
                comments.append(self.tmpl_get_comment_without_ranking(ln,
                                                                      cmt_tuple[0],#nickname
                                                                      cmt_tuple[2],#date_creation
                                                                      cmt_tuple[3],#body
                                                                      None,        #reply_link
                                                                      None))       #report_link
            users.append(self.tmpl_admin_user_info(ln,
                                                   meta_data[0], #nickname
                                                   meta_data[1], #uid
                                                   meta_data[2]))#email
            comments_info.append(self.tmpl_admin_review_info(ln,
                                                             reviews,
                                                             meta_data[5], # nb abuse reports
                                                             meta_data[3], # cmt_id
                                                             meta_data[4]))# rec_id
            checkboxes.append(self.tmpl_admin_select_comment_checkbox(meta_data[3]))

        form_link = "%s/admin/webcomment/webcommentadmin.py/del_com?ln=%s" % (CFG_SITE_URL, ln)
        out = """
<table class="admin_wvar" style="width:100%%;">
  <thead>
    <tr class="adminheaderleft">
      <th>%(review_label)s</th>
      <th>%(written_by_label)s</th>
      <th>%(review_info_label)s</th>
      <th>%(select_label)s</th>
    </tr>
  </thead>
  <tbody>""" % {'review_label': reviews and _("Review") or _("Comment"),
              'written_by_label': _("Written by"),
              'review_info_label': _("General informations"),
              'select_label': _("Select")}
        for i in range (0, len(comments)):
            out += """
    <tr>
      <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
      <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
      <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
      <td class="admintd" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
    </tr>""" % (comments[i], users[i], comments_info[i], checkboxes[i])
        out += """
  </tbody>
</table>"""
        if reviews:
            action_display = {
            'delete': _('Delete selected reviews'),
            'unreport': _('Suppress selected abuse report')
            }
        else:
            action_display = {
            'delete': _('Delete selected comments'),
            'unreport': _('Suppress selected abuse report')
            }

        form = self.tmpl_create_multiple_actions_form(form_name="admin_comment",
                                                      form_action=form_link,
                                                      method="post",
                                                      action_display=action_display,
                                                      action_field_name='action',
                                                      button_label=_("OK"),
                                                      button_name="okbutton",
                                                      content=out)
        if uid > 0:
            header = '<br />'
            if reviews:
                header += _("Here are the reported reviews of user %s") %  uid
            else:
                header += _("Here are the reported comments of user %s") %  uid
            header += '<br /><br />'
        if comID > 0:
            header = '<br />' +_("Here is comment/review %s")% comID + '<br /><br />'
        if uid > 0 and comID > 0:
            header = '<br />' + _("Here is comment/review %(x_cmtID)s written by user %(x_user)s") % {'x_cmtID': comID, 'x_user': uid}
            header += '<br/ ><br />'
        if uid == 0 and comID == 0:
            header = '<br />'
            if reviews:
                header += _("Here are all reported reviews sorted by the most reported")
            else:
                header += _("Here are all reported comments sorted by the most reported")
            header += "<br /><br />"

        return header + form

    def tmpl_admin_del_com(self, del_res, ln=CFG_SITE_LANG):
        """
        @param del_res: list of the following tuple (comment_id, was_successfully_deleted),
                        was_successfully_deleted is boolean (0=false, >0=true
        """
        _ = gettext_set_language(ln)
        table_rows = ''
        for deltuple in del_res:
            table_rows += """
<tr>
  <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
  <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
</tr>""" % (deltuple[0], deltuple[1]>0 and _("Yes") or "<span class=\"important\">" +_("No") + "</span>")

        out = """
<table class="admin_wvar">
  <tr class="adminheaderleft">
  <td style="padding-right:10px;">%s</td>
    <td>%s</td>
  </tr>%s
<table>""" % (_("comment ID"), _("successfully deleted"), table_rows)

        return out


    def tmpl_admin_suppress_abuse_report(self, del_res, ln=CFG_SITE_LANG):
        """
        @param del_res: list of the following tuple (comment_id, was_successfully_deleted),
                        was_successfully_deleted is boolean (0=false, >0=true
        """
        _ = gettext_set_language(ln)
        table_rows = ''
        for deltuple in del_res:
            table_rows += """
<tr>
  <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
  <td class="admintdleft" style="padding: 5px; border-bottom: 1px solid lightgray;">%s</td>
</tr>""" % (deltuple[0], deltuple[1]>0 and _("Yes") or "<span class=\"important\">" +_("No") + "</span>")

        out = """
<table class="admin_wvar">
  <tr class="adminheaderleft">
  <td style ="padding-right: 10px;">%s</td>
    <td>%s</td>
  </tr>%s
<table>""" % (_("comment ID"), _("successfully suppressed abuse report"), table_rows)

        return out

    def tmpl_mini_review(self, recID, ln=CFG_SITE_LANG, action='SUBMIT',
                         avg_score=0, nb_comments_total=0):
        """Display the mini version of reviews (only the grading part)"""

        _ = gettext_set_language(ln)

        url = '%s/record/%s/reviews/add?ln=%s&amp;action=%s' % (CFG_SITE_URL, recID, ln, action)

        if avg_score > 0:
            score = _("Average review score: %(x_nb_score)s based on %(x_nb_reviews)s reviews") % \
                    {'x_nb_score':  '<b>%.1f</b>' % avg_score,
                     'x_nb_reviews': nb_comments_total}
        else:
            score = '(' +_("Not yet reviewed") + ')'

        if avg_score == 5:
            s1, s2, s3, s4, s5 = 'full', 'full', 'full', 'full', 'full'
        elif avg_score >= 4.5:
            s1, s2, s3, s4, s5 = 'full', 'full', 'full', 'full', 'half'
        elif avg_score >= 4:
            s1, s2, s3, s4, s5 = 'full', 'full', 'full', 'full', ''
        elif avg_score >= 3.5:
            s1, s2, s3, s4, s5 = 'full', 'full', 'full', 'half', ''
        elif avg_score >= 3:
            s1, s2, s3, s4, s5 = 'full', 'full', 'full', '', ''
        elif avg_score >= 2.5:
            s1, s2, s3, s4, s5 = 'full', 'full', 'half', '', ''
        elif avg_score >= 2:
            s1, s2, s3, s4, s5 = 'full', 'full', '', '', ''
        elif avg_score >= 1.5:
            s1, s2, s3, s4, s5 = 'full', 'half', '', '', ''
        elif avg_score == 1:
            s1, s2, s3, s4, s5 = 'full', '', '', '', ''
        else:
            s1, s2, s3, s4, s5 = '', '', '', '', ''

        out = '''
<small class="detailedRecordActions">%(rate)s:</small><br /><br />
<div style="margin:auto;width:160px;">
<span style="display:none;">Rate this document:</span>
<div class="star %(s1)s" ><a href="%(url)s&amp;score=1">1</a>
<div class="star %(s2)s" ><a href="%(url)s&amp;score=2">2</a>
<div class="star %(s3)s" ><a href="%(url)s&amp;score=3">3</a>
<div class="star %(s4)s" ><a href="%(url)s&amp;score=4">4</a>
<div class="star %(s5)s" ><a href="%(url)s&amp;score=5">5</a></div></div></div></div></div>
<div style="clear:both">&nbsp;</div>
</div>
<small>%(score)s</small>
''' % {'url': url,
        'score': score,
        'rate': _("Rate this document"),
        's1': s1,
        's2': s2,
        's3': s3,
        's4': s4,
        's5': s5
        }
        return out
