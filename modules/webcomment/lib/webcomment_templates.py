# -*- coding: utf-8 -*-
## $Id$
## Comments and reviews for records.
                                              
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
                                           
__lastupdated__ = """FIXME: last updated"""

import urllib
import time
import string

from config import *
from messages import gettext_set_language, language_list_long

class Template:
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
        c_date_creation = 1
        c_body = 2
        c_id = 3

        warnings = self.tmpl_warnings(warnings)

        report_link = '''%s/comments.py/report?recid=%s&amp;ln=%s&amp;comid=%%(comid)s&amp;reviews=0''' % (weburl, recID, ln)
        
        # comments                                                                                                                                       
        comment_rows = ''' '''
        for comment in comments:
            comment_rows += '''
                    <tr>
                        <td>'''
            comment_rows += self.tmpl_get_comment_without_ranking(recID, ln, comment[c_nickname], comment[c_date_creation], comment[c_body])
            comment_rows += '''
                            <br><br>
                        </td>
                    </tr>'''
        
        # write button                                             
        write_button_link = '''%s/comments.py/add''' % (weburl,)
        write_button_form = ''' <input type="hidden" name="recid" value="%s"/>
                                <input type="hidden" name="ln" value="%s"/>
                                <input type="hidden" name="reviews" value="0"/>''' % (recID, ln)
        write_button_form = self.createhiddenform(action=write_button_link, method="Get", text=write_button_form, button='Write a comment')
 
        # output
        if nb_comments_total > 0:
            out = warnings + '''
                <!--  comments title table -->
            <table><tr><td class="blocknote">%(comment_title)s</td></tr></table>
            Showing the latest %(nb_comments)s comment%(s)s: %(tab)s <br>
            <!-- comments table -->
            <table border="0" cellspacing="5" cellpadding="5" width="100%%">
                %(comment_rows)s
            </table>
            %(view_all_comments_link)s
            <br>
            <br>
            %(write_button_form)s<br>
            ''' % \
            {   'comment_title'                 : "Discuss this document:",
                'nb_comments_total'             : nb_comments_total,
                'recID'                         : recID,
                'comment_rows'                  : comment_rows,
                'tab'                           : '&nbsp;'*4,
                'weburl'                        : weburl,
                's'                             : cfg_webcomment_nb_comments_in_detailed_view>1 and 's' or "",
                'view_all_comments_link'        : nb_comments_total>0 and '''<a href="%s/comments.py/display?recid=%s&amp;reviews=0">View all %s comments</a>''' \
                                                                  % (weburl, recID, nb_comments_total) or "",
                'write_button_form'             : write_button_form,
                'nb_comments'                   : cfg_webcomment_nb_comments_in_detailed_view>1 and cfg_webcomment_nb_comments_in_detailed_view or ""
            }
        else:
            out = '''
            <!--  comments title table -->
            <table><tr><td class="blocknote">Discuss this document:</td></tr></table>
            Open a a discussion about any aspect of this document. 
            <br>
            %s
            <br>''' % (write_button_form,)

        return out

    def tmpl_record_not_found(self, status='missing', recID="", ln=cdslang):
        """
        Displays a page when bad or missing record ID was given.
        @param status:  'missing'   : no recID was given
                        'inexistant': recID doesn't have an entry in the database
                        'nan'       : recID is not a number
                        'invalid'   : recID is an error code, i.e. in the interval [-99,-1]
        @param return: body of the page
        """
        if status == 'inexistant':
            body = "Sorry, the record %s does not seem to exist." % (recID,)
        elif status == 'nan':
            body = "Sorry, the record %s does not seem to be a number." % (recID,)
        elif status == 'invalid':
            body = "Sorry, the record %s is not a valid ID value." % (recID,)
        else:
            body = "Sorry, no record ID was provided."

        body += "<br><br>You may want to start browsing from <a href=\"%s?ln=%s\">%s</a>." % (weburl, ln, cdsnameintl[ln])
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
        c_date_creation = 1
        c_body = 2
        c_nb_votes_yes = 3
        c_nb_votes_total = 4
        c_star_score = 5
        c_title = 6
        c_id = 7

        warnings = self.tmpl_warnings(warnings)

        #stars
        if avg_score > 0:
            avg_score_img = 'stars-' + str(avg_score).split('.')[0] + '-' + str(avg_score).split('.')[1] + '.gif'
        else:
            avg_score_img = "stars-except.gif"

        # voting links
        useful_dict =   {   'weburl'        : weburl,
                            'recID'         : recID, 
                            'ln'            : ln,
                            'yes_img'       : 'smchk_gr.gif', #'yes.gif',
                            'no_img'        : 'iconcross.gif' #'no.gif'       
                        }
        useful_yes = '''<a href="%(weburl)s/comments.py/vote?recid=%(recID)s&amp;ln=%(ln)s&amp;comid=%%(comid)s&amp;com_value=1&amp;reviews=1">Yes</a>''' % useful_dict
        useful_no = ''' <a href="%(weburl)s/comments.py/vote?recid=%(recID)s&amp;ln=%(ln)s&amp;comid=%%(comid)s&amp;com_value=-1&amp;reviews=1">No</a>''' % useful_dict 
        report_link = '''%(weburl)s/comments.py/report?recid=%(recID)s&amp;ln=%(ln)s&amp;comid=%%(comid)s&amp;reviews=1''' % useful_dict

        #comment row
        comment_rows = ''' '''
        for comment in comments:
            comment_rows += '''
                    <tr>
                        <td>'''
            comment_rows += self.tmpl_get_comment_with_ranking(recID, ln, comment[c_nickname], comment[c_date_creation], comment[c_body], 
                                                                    comment[c_nb_votes_total], comment[c_nb_votes_yes], comment[c_star_score], comment[c_title])
            comment_rows += '''
                        Was this review helpful? %s / %s<br>''' % (useful_yes % {'comid':comment[c_id]}, useful_no % {'comid':comment[c_id]})
            comment_rows +=  '''
                        <br>
                    </td></tr>'''

        # write button
        write_button_link = '''%s/comments.py/add''' % (weburl,)
        write_button_form = ''' <input type="hidden" name="recid" value="%s"/>
                                <input type="hidden" name="ln" value="%s"/>
                                <input type="hidden" name="reviews" value="1"/>''' % (recID, ln )
        write_button_form = self.createhiddenform(action=write_button_link, method="Get", text=write_button_form, button='Write a review')

        if nb_comments_total > 0:
            out = warnings + ''' 
                <!--  review title table -->
                <table><tr><td class="blocknote">%(comment_title)s</td></tr></table>
                <b>Average review score: </b><img src="%(weburl)s/img/%(avg_score_img)s" alt="%(avg_score)s" border="0"> based on %(nb_comments_total)s reviews<br>
                Readers found the following %(nb_helpful)s review%(s)s to be most helpful. 
                <!-- review table -->
                <table border="0" cellspacing="5" cellpadding="5" width="100%%">
                    %(comment_rows)s
                </table>
                %(view_all_comments_link)s
                %(write_button_form)s<br>
            ''' % \
            {   'comment_title'         : "Rate this document:",
                'avg_score_img'         : avg_score_img,
                'avg_score'             : avg_score,
                'nb_comments_total'     : nb_comments_total,
                'recID'                 : recID,
                'view_all_comments'     : "view all %s reviews" % (nb_comments_total,),
                'write_comment'         : "write a review",
                'comment_rows'          : comment_rows,
                's'                     : cfg_webcomment_nb_reviews_in_detailed_view>1 and 's' or "",
                'tab'                   : '&nbsp;'*4,
                'weburl'                : weburl,   
                'nb_helpful'            : cfg_webcomment_nb_reviews_in_detailed_view>1 and cfg_webcomment_nb_reviews_in_detailed_view or "",
                'view_all_comments_link': nb_comments_total>0 and """<a href="%s/comments.py/display?recid=%s&amp;ln=%s&amp;do=hh&amp;reviews=1">View all %s reviews</a><br>""" \
                                                                  % (weburl, recID, ln, nb_comments_total) or "",
                'write_button_form'     : write_button_form
            }
        else:
            out = '''
                 <!--  review title table -->
                <table><tr><td class="blocknote">Rate this document:</td></tr></table>
                Have the honor of being the first to review this document.<br>
                %s
                <br>''' % (write_button_form,)
        return out

    def tmpl_get_comment_without_ranking(self, recID, ln, nickname, date_creation, body, reply_link=None, report_link=None):
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

        date_creation = str(date_creation)
        date_creation_data = date_creation[:18]
        date_creation_data = time.strptime(str(date_creation_data), "%Y-%m-%d %H:%M:%S")
        date_creation_data = time.strftime("%d %b %Y %H:%M:%S %Z", date_creation_data)
        date_creation = str(date_creation_data) + date_creation[22:] # 22 to get rid of the .00 after time

        out = ''' '''

        # load the right message language
        #_ = gettext_set_language(ln)

        out += """
                <table width="100%%">
                    <tr>
                        <td><b>%(nickname)s</b> wrote on <i>%(date_creation)s</i></td>
                        <td align=right>%(links)s</td>
                    </tr>
                    <tr>
                        <td class="commentbox" colspan=2>%(body)s</td>
                    </tr>
                </table>""" % \
            {   #! FIXME  put send_a_private_message view_shared_baskets 
                'nickname'      : nickname,
                'date_creation' : date_creation,
                'body'          : body,
                'links'         : (report_link!=None and reply_link!=None) and " <a href=\"%s\">Reply</a> | <a href=\"%s\">Report abuse</a>" % (reply_link, report_link) or ""
            }
        return out

    def tmpl_get_comment_with_ranking(self, recID, ln, nickname, date_creation, body, nb_votes_total, nb_votes_yes, star_score, title):
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
            star_score_img = 'stars-' + str(star_score) + '-0.gif'
        else:
            star_score_img = 'stars-except.gif'

        out = """"""
        date_creation = str(date_creation)
        date_creation_data = date_creation[:18]
        date_creation_data = time.strptime(str(date_creation_data), "%Y-%m-%d %H:%M:%S")
        date_creation_data = time.strftime("%d %b %Y %H:%M:%S %Z", date_creation_data)
        date_creation = str(date_creation_data) + date_creation[22:]

        # load the right message language
        #_ = gettext_set_language(ln)

        out += """
                <table width="100%%">
                    <tr>
                        <td> 
                        <img src="%(weburl)s/img/%(star_score_img)s" alt="%(star_score)s" border="0"> <b>%(title)s</b><br>
                        Reviewed by <i>%(nickname)s</i> on %(date_creation)s<br>
                        %(nb_votes_yes)s out of %(nb_votes_total)s people found this review useful.<br>
                        </td>
                    </tr>
                    <tr>
                        <td><blockquote>%(body)s </blockquote></td>
                    </tr>
                </table>
        """ % \
            {   #! FIXME  put send_a_private_message view_shared_baskets 
                'nickname'      : nickname,
                'weburl'        : weburl,
                'star_score_img': star_score_img,
                'date_creation' : date_creation,
                'body'          : body, 
                'nb_votes_total'      : nb_votes_total,
                'star_score'    : star_score,
                'title'     : title, 
                'nb_votes_yes'    : nb_votes_yes<0 and "0" or nb_votes_yes
        }
        return out

    def tmpl_get_comments(self, recID, ln, nb_per_page, page, nb_pages, display_order, display_since, cfg_webcomment_allow_reviews, 
                          comments, total_nb_comments, avg_score, warnings, border=0, reviews=0):
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
        @param cfg_webcomment_allow_reviews: is ranking enable, get from config.py/cfg_webcomment_allow_reviews
        @param comments: tuple as returned from webcomment.py/query_retrieve_comments_or_remarks
        @param total_nb_comments: total number of comments for this record
        @param avg_score: average score of reviews for this record
        @param warnings: list of warning tuples (warning_msg, color)
        @param border: boolean, active if want to show border around each comment/review
        @param reviews: booelan, enabled for reviews, disabled for comments
        """
        # load the right message language
        _ = gettext_set_language(ln)

        # naming data fields of comments
        if reviews:
            c_nickname = 0
            c_date_creation = 1
            c_body = 2
            c_nb_votes_yes = 3
            c_nb_votes_total = 4
            c_star_score = 5
            c_title = 6
            c_id = 7
        else:
            c_nickname = 0
            c_date_creation = 1
            c_body = 2
            c_id = 3

        # voting links
        useful_dict =   {   'weburl'        : weburl,
                            'recID'         : recID, 
                            'ln'            : ln,
                            'do'            : display_order,
                            'ds'            : display_since,
                            'nb'            : nb_per_page,
                            'p'             : page,
                            'reviews'       : reviews   
                        }
        useful_yes = '''<a href="%(weburl)s/comments.py/vote?recid=%(recID)s&amp;ln=%(ln)s&amp;comid=%%(comid)s&amp;com_value=1&amp;do=%(do)s&amp;ds=%(ds)s&amp;nb=%(nb)s&amp;p=%(p)s&amp;reviews=%(reviews)s&amp;referer=%(weburl)s/comments.py/display">Yes</a>''' % useful_dict 
        useful_no = '''<a href="%(weburl)s/comments.py/vote?recid=%(recID)s&amp;ln=%(ln)s&amp;comid=%%(comid)s&amp;com_value=-1&amp;do=%(do)s&amp;ds=%(ds)s&amp;nb=%(nb)s&amp;p=%(p)s&amp;reviews=%(reviews)s&amp;referer=%(weburl)s/comments.py/display">No</a>''' % useful_dict
        warnings = self.tmpl_warnings(warnings)

        ## record details
        from search_engine import print_record
        record_details = print_record(recID=recID, format='hb')

        link_dic =  {   'weburl'    : weburl,
                        'module'    : 'comments.py',
                        'function'  : 'index',
                        'arguments' : 'recid=%s&amp;do=%s&amp;ds=%s&amp;nb=%s&amp;reviews=%s' % (recID, display_order, display_since, nb_per_page, reviews),
                        'arg_page'  : '&amp;p=%s' % page,
                        'page'      : page          }   

        ## comments table
        comments_rows = ''' '''
        for comment in comments:
            comments_rows += '''
                    <!-- start comment row -->
                    <tr>
                        <td>'''
            if not reviews:
                report_link = '''%(weburl)s/comments.py/report?recid=%(recID)s&amp;ln=%(ln)s&amp;comid=%%(comid)s&amp;do=%(do)s&amp;ds=%(ds)s&amp;nb=%(nb)s&amp;p=%(p)s&amp;reviews=%(reviews)s&amp;referer=%(weburl)s/comments.py/display''' % useful_dict % {'comid':comment[c_id]}
                reply_link = '''%(weburl)s/comments.py/add?recid=%(recID)s&amp;ln=%(ln)s&amp;action=REPLY&amp;comid=%%(comid)s''' % useful_dict % {'comid':comment[c_id]}
                comments_rows += self.tmpl_get_comment_without_ranking(recID, ln, comment[c_nickname], comment[c_date_creation], comment[c_body], reply_link, report_link)
            else:
                report_link = '''%(weburl)s/comments.py/report?recid=%(recID)s&amp;ln=%(ln)s&amp;comid=%%(comid)s&amp;do=%(do)s&amp;ds=%(ds)s&amp;nb=%(nb)s&amp;p=%(p)s&amp;reviews=%(reviews)s&amp;referer=%(weburl)s/comments.py/display''' % useful_dict % {'comid':comment[c_id]}
                comments_rows += self.tmpl_get_comment_with_ranking(recID, ln, comment[c_nickname], comment[c_date_creation], comment[c_body], 
                                                                        comment[c_nb_votes_total], comment[c_nb_votes_yes], comment[c_star_score], comment[c_title])
                comments_rows += '''<table>
                                        <tr>
                                            <td>Was this review helpful? %(tab)s</td>
                                            <td> %(yes)s </td>
                                            <td> / </td>
                                            <td> %(no)s </td>
                                            <td class="reportabuse">%(tab)s%(tab)s<a href="%(report)s">(Report abuse)</a></td>
                                        </tr>
                                    </table>''' \
                                 % {    'yes'       : useful_yes % {'comid':comment[c_id]}, 
                                        'no'        : useful_no % {'comid':comment[c_id]},
                                        'report'    : report_link % {'comid':comment[c_id]},
                                        'tab'       : '&nbsp;'*2
                                    }
            comments_rows += '''
                            <br>
                        </td>
                    </tr><!-- end comment row -->'''

        ## page links
        page_links = ''' '''
        # Previous
        if page != 1:
            link_dic['arg_page'] = 'p=%s' % (page - 1)
            page_links += '''
                <a href=\"%(weburl)s/%(module)s/%(function)s?%(arguments)s&amp;%(arg_page)s\">&lt;&lt;</a> ''' % link_dic
        else:
            page_links += ''' %s ''' % ('&nbsp;'*(len('< Previous')+7))
        # Page Numbers
        for i in range(1, nb_pages+1):
            link_dic['arg_page'] = 'p=%s' % i
            link_dic['page'] = '%s' % i
            if i != page:
                page_links += ''' 
                <a href=\"%(weburl)s/%(module)s/%(function)s?%(arguments)s&amp;%(arg_page)s\">%(page)s</a> ''' % link_dic
            else:
                page_links += ''' <b>%s</b> ''' % i 
        # Next
        if page != nb_pages:
            link_dic['arg_page'] = 'p=%s' % (page + 1)
            page_links += '''
                <a href=\"%(weburl)s/%(module)s/%(function)s?%(arguments)s&amp;%(arg_page)s\">&gt;&gt;</a> ''' % link_dic
        else:
            page_links += '''%s''' % ('&nbsp;'*(len('< Next')+7))

        ## stuff for ranking if enabled
        if reviews:
            comments_or_reviews = 'review'
            if avg_score > 0:  
                avg_score_img = 'stars-' + str(avg_score).split('.')[0] + '-' + str(avg_score).split('.')[1] + '.gif'
            else:
                avg_score_img = "stars-except.gif"
            ranking_average = '''<br><b>Average review score: </b><img src="%(weburl)s/img/%(avg_score_img)s" alt="%(avg_score)s" border="0"> based on %(nb_comments_total)s reviews<br>''' \
                                % { 'weburl'            : weburl,
                                    'avg_score'         : avg_score,
                                    'avg_score_img'     : avg_score_img,
                                    'nb_comments_total' : total_nb_comments }
        else:
            ranking_average = ""
            comments_or_reviews = 'comment'

        write_button_link = '''%s/comments.py/add''' % (weburl, )
        write_button_form = ''' <input type="hidden" name="recid" value="%s"/>
                                <input type="hidden" name="ln" value="%s"/>
                                <input type="hidden" name="reviews" value="%s"/>''' % (recID, ln, reviews)
        write_button_form = self.createhiddenform(action=write_button_link, method="Get", text=write_button_form, button='Write a %s' % comments_or_reviews)
        
        ## html
        body = '''
           
            <table width="100%%"><tr><td> <h1>Record %(recid)s</h1></td><td valign=top align=right><a href="%(weburl)s/search.py?recid=%(recid)s&amp;ln=%(ln)s">Back to search results</a></td></tr></table>
            <br>
            %(record_details)s
            <br>
            <br>
            <h2>%(comments_or_reviews_title)ss</h2>
            There is a total of %(total_nb_comments)s %(comments_or_reviews)ss. %(ranking_avg)s<br>
            %(write_button_form)s<br>
            <!-- start comments table -->
            <table border="%(border)s" width="100%%">
            %(comments_rows)s
            </table>
            <!-- end comments table -->
            <table width="100%%">
                <tr>
                    <td>%(write_button_form_again)s</td>
                    <td align=right><a href="%(weburl)s/search.py?recid=%(recid)s&amp;ln=%(ln)s">Back to search results</a></td>
                </tr>
            </table>
            <br>
            ''' % \
            {   'record_details'            : record_details,
                'write_button_form'         : write_button_form,
                'write_button_form_again'   : total_nb_comments>3 and write_button_form or "",
                'comments_rows'             : comments_rows,
                'total_nb_comments'         : total_nb_comments,
                'comments_or_reviews'       : comments_or_reviews,
                'comments_or_reviews_title' : comments_or_reviews[0].upper() + comments_or_reviews[1:],
                'weburl'                    : weburl,
                'module'                    : "comments.py",
                'recid'                     : recID,
                'ln'                        : ln,
                'border'                    : border,
                'ranking_avg'               : ranking_average   } 
        form = '''
                Display             <select name=\"nb\" size=\"1\"> per page 
                                        <option value=\"all\">All</option>
                                        <option value=\"10\">10</option>
                                        <option value=\"25\">20</option>
                                        <option value=\"50\">50</option>
                                        <option value=\"100\" selected>100</option>
                                    </select>
                comments per page that are    <select name=\"ds\" size=\"1\">                         
                                        <option value=\"all\" selected>Any age</option>                              
                                        <option value=\"1d\">1 day old</option>                                 
                                        <option value=\"3d\">3 days old</option>
                                        <option value=\"1w\">1 week old</option>
                                        <option value=\"2w\">2 weeks old</option>
                                        <option value=\"1m\">1 month old</option>
                                        <option value=\"3m\">3 months old</option>
                                        <option value=\"6m\">6 months old</option>
                                        <option value=\"1y\">1 year old</option>
                                    </select>
                and sorted by       <select name=\"do\" size=\"1\">
                                        <option value=\"od\" selected>Oldest first</option>
                                        <option value=\"nd\">Newest first</option>
                                        %s
                                    </select>
            ''' % \
                (reviews==1 and '''
                                        <option value=\"hh\">most helpful</option>
                                        <option value=\"lh\">least helpful</option>
                                        <option value=\"hs\">highest star ranking</option>
                                        <option value=\"ls\">lowest star ranking</option>
                                    </select>''' or '''
                                    </select>''')
        form_link = "%(weburl)s/%(module)s/%(function)s" % link_dic
        form = self.createhiddenform(action=form_link, method="Get", text=form, button='Go', recid=recID, p=1)
        pages = '''
            <br>
            Viewing %(comments_or_reviews)s %(results_nb_lower)s-%(results_nb_higher)s <br>
            %(page_links)s
            <br>
        ''' % \
        {   'page_links'            : "Page: " + page_links ,
            'comments_or_reviews'   : not reviews and 'comments' or 'reviews',
            'results_nb_lower'      : len(comments)>0 and ((page-1) * nb_per_page)+1 or 0,
            'results_nb_higher'     : page == nb_pages and (((page-1) * nb_per_page) + len(comments)) or (page * nb_per_page)   }

        if nb_pages > 1:
            #body = warnings + body + form + pages
            body = warnings + body + pages
        else:
            body = warnings + body

        return body


    def createhiddenform(self, action="", method="Get", text="", button="confirm", cnfrm='', **hidden):
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
        
        output  = '<form action="%s" method="%s">\n' % (action, string.lower(method).strip() in ['get','post'] and method or 'Get')
        output += '<table>\n<tr><td style="vertical-align: top">'
        output += text
        if cnfrm:
            output += ' <input type="checkbox" name="confirm" value="1"/>' 
        for key in hidden.keys():
            if type(hidden[key]) is list:
                for value in hidden[key]:
                    output += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, value)
            else:
                output += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, hidden[key])
        output += '</td><td style="vertical-align: bottom">'
        output += ' <input class="adminbutton" type="submit" value="%s"/>\n' % (button, )
        output += '</td></tr></table>'
        output += '</form>\n'

        return output

    def tmpl_warnings(self, warnings): 
        """
        Prepare the warnings list
        @param warnings: list of warning tuples (warning_msg, arg1, arg2, etc)
        @return html string of warnings
        """
        from errorlib import get_msgs_for_code_list
        span_class = 'important'
        out = ""
        if type(warnings) is not list:
            warnings = [warnings]
        if len(warnings) > 0:
            warnings_parsed = get_msgs_for_code_list(warnings, 'warning')
            for (warning_code, warning_text) in warnings_parsed:
                if not warning_code.startswith('WRN'): #display only warnings that begin with WRN to user
                    continue
                if warning_code.find('GREEN_TEXT') >= 0:
                    span_class = "exampleleader"
                elif warning_code.find('RED_TEXT') >= 0:
                    span_class = "important"
                out += '''
                    <span class="%(span_class)s">%(warning)s</span><br>''' % \
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
        link_dic =  {   'weburl'    : weburl,
                        'module'    : 'comments.py',
                        'function'  : 'add',
                        'arguments' : 'recid=%s&amp;ln=%s&amp;action=%s&amp;reviews=0' % (recID, ln, 'SUBMIT')  }

        from search_engine import print_record
        record_details = print_record(recID=recID, format='hb')

        warnings = self.tmpl_warnings(warnings)
        form = '''
                <table width="100%%">
                    <tr><td>Article:</td></tr>
                    <tr><td>%(record)s<br><br></td></tr>
                    <tr><td>Your nickname: %(nickname)s<br><br></td></tr>
                    <tr><td>Comment:</td></tr>
                    <tr><td><textarea name="msg" rows=20 cols=80>%(msg)s</textarea></td></tr>
                </table>
                <br><br> ''' % { 'msg'      : msg!='None' and urllib.unquote(msg) or "",
                                 'nickname' : nickname,
                                 'record'   : record_details                                } 
        form_link = "%(weburl)s/%(module)s/%(function)s?%(arguments)s" % link_dic
        form = self.createhiddenform(action=form_link, method="Post", text=form, button='Add comment')
        return warnings + form

    def tmpl_add_comment_form_with_ranking(self, recID, uid, nickname, ln, msg, score, note, warnings):
        """
        Add form for reviews
        @param recID: record id
        @param uid: user id
        @param ln: language
        @param msg: comment body contents for when refreshing due to warning
        @param score: review score
        @param note: review title
        @param warnings: list of warning tuples (warning_msg, color)
        @return html add review form
        """
        link_dic =  {   'weburl'    : weburl,
                        'module'    : 'comments.py',
                        'function'  : 'add',
                        'arguments' : 'recid=%s&amp;ln=%s&amp;action=%s&amp;reviews=1' % (recID, ln, 'SUBMIT')  }
        warnings = self.tmpl_warnings(warnings)

        from search_engine import print_record
        record_details = print_record(recID=recID, format='hb')

        form = '''
                <table width="100%%">
                    <tr><td>Article: </td></tr>
                    <tr><td>%(record)s<br><br></td></tr>
                    <tr><td>Select your score:  <select name=\"score\" size=\"1\"> 
                                                    <option value=\"0\" selected>None</option>
                                                    <option value=\"1\">1(worst)</option>
                                                    <option value=\"2\">2</option>
                                                    <option value=\"3\">3</option>
                                                    <option value=\"4\">4</option>
                                                    <option value=\"5\">5(best)</option>
                                                </select><br><br>
                    </td></tr>
                    <tr><td>Your nickname: %(nickname)s<br><br></td></tr>
                    <tr><td>Give a title to your review:</td></tr>
                    <tr><td><input type=text name="note" size=80 maxlength=250 value="%(note)s"><br><br></td></tr>
                    <tr><td>Write your review:</td></tr>
                    <tr><td><textarea name="msg" rows=20 cols=80>%(msg)s</textarea></td></tr>
                </table>
                <br><br>''' % { 'note'      : note!='None' and note or "", 
                                'msg'       : msg!='None' and msg or "",
                                'nickname'  : nickname,
                                'record'    : record_details    } 
        form_link = "%(weburl)s/%(module)s/%(function)s?%(arguments)s" % link_dic
        form = self.createhiddenform(action=form_link, method="Post", text=form, button='Add Review')
        return warnings + form

    def tmpl_add_comment_successful(self, recID, ln, reviews): 
        """
        @param recID: record id
        @param ln: language
        @return html page of successfully added comment/review
        """
        link_dic =  {   'weburl'    : weburl,
                        'module'    : 'comments.py',
                        'function'  : 'display',
                        'arguments' : 'recid=%s&amp;ln=%s&amp;do=od&amp;reviews=%s' % (recID, ln, reviews)  }
        link = "%(weburl)s/%(module)s/%(function)s?%(arguments)s" % link_dic
        return '''Your %s was successfully added<br><br><a href="%s">Back to record</a>''' % (reviews==1 and 'review' or 'comment', link)

    def tmpl_admin_index(self, ln):
        """
        """
        # load the right message language
        _ = gettext_set_language(ln)
   
        out = '''
        <table>'''
        if cfg_webcomment_allow_comments or cfg_webcomment_allow_reviews:
            if cfg_webcomment_allow_comments: 
                out += '''
                <tr><td>0.&nbsp;&nbsp;<small><a href="%(weburl)s/admin/webcomment/webcommentadmin.py/comments?ln=%(ln)s&amp;reviews=0">View all reported comments</a></small></td></tr>'''
            if cfg_webcomment_allow_reviews: 
                out += '''
                <tr><td>0.&nbsp;<small><a href="%(weburl)s/admin/webcomment/webcommentadmin.py/comments?ln=%(ln)s&amp;reviews=1">View all reported reviews</a></small></td></tr>'''
            out += '''
                <tr><td>1.&nbsp;<small><a href="%(weburl)s/admin/webcomment/webcommentadmin.py/delete?ln=%(ln)s&amp;comid=-1">Delete a specific comment/review (by ID)</a></small></td></tr>
                <tr><td>2.&nbsp;<small><a href="%(weburl)s/admin/webcomment/webcommentadmin.py/users?ln=%(ln)s">View all users who have been reported</a></small></td></tr>
                ''' 
            out = out % {   'weburl'    : weburl, 
                            'ln'        : ln        }
        else:
            out += '''
            <tr><td><br>Comments and reviews are disabled</td></tr>'''
        out += '''</table>'''
        from bibrankadminlib import addadminbox
        return addadminbox('<b>Menu</b>', [out])

    def tmpl_admin_delete_form(self, ln, warnings):
        """
        @param warnings: list of warning_tuples where warning_tuple is (warning_message, text_color)
                         see tmpl_warnings, color is optional
        """
        # load the right message language
        _ = gettext_set_language(ln)

        warnings = self.tmpl_warnings(warnings)

        out = '''
        <br>
        Please enter the ID of the comment/review so that you can view it before deciding to delete it or not<br>
        <br>'''
        form = '''
            <table> 
                <tr>
                    <td>Comment ID:</td>
                    <td><input type=text name="comid" size=10 maxlength=10 value=""></td>
                </tr>
                <tr>
                    <td><br></td>
                <tr>
            </table>
            <br>
        '''
        form_link = "%s/admin/webcomment/webcommentadmin.py/delete?ln=%s" % (weburl, ln)
        form = self.createhiddenform(action=form_link, method="Get", text=form, button='View Comment')
        return warnings + out + form

    def tmpl_admin_users(self, ln, users_data):
        """
        @param users_data:  tuple of ct, i.e. (ct, ct, ...)
                            where ct is a tuple (total_number_reported, total_comments_reported, total_reviews_reported, total_nb_votes_yes_of_reported, 
                                                 total_nb_votes_total_of_reported, user_id, user_email, user_nickname)
                            sorted by order of ct having highest total_number_reported
        """
        u_reports = 0
        u_comment_reports = 1
        u_reviews_reports = 2
        u_nb_votes_yes = 3
        u_nb_votes_total = 4
        u_uid = 5
        u_email = 6
        u_nickname = 7

        if not users_data:
            return self.tmpl_warnings([("There have been no reports so far.", 'green')])        

        user_rows = ""
        for utuple in users_data:
            com_link = '''<a href="%s/admin/webcomment/webcommentadmin.py/comments?ln=%s&amp;uid=%s&amp;reviews=0">View all %s reported comments</a><br>''' % \
                          (weburl, ln, utuple[u_uid], utuple[u_comment_reports])
            rev_link = '''<a href="%s/admin/webcomment/webcommentadmin.py/comments?ln=%s&amp;uid=%s&amp;reviews=1">View all %s reported reviews</a>''' % \
                          (weburl, ln, utuple[u_uid], utuple[u_reviews_reports])
            user_rows += ''' 
                <tr>
                    <td>%(nickname)s</td>
                    <td>%(email)s</td>
                    <td>%(uid)s</td>
                    %(review_row)s
                    <td><b>%(reports)s</b></td>
                    <td>%(com_link)s%(rev_link)s</td>
                </tr>
            ''' % { 'nickname'  : len(utuple[u_nickname])>0 and utuple[u_nickname] or utuple[u_email].split('@')[0],
                    'email'     : utuple[u_email],
                    'uid'       : utuple[u_uid],
                    'reports'   : utuple[u_reports],
                    'review_row': cfg_webcomment_allow_reviews>0 and "<td>%s</td><td>%s</td><td>%s</td>" % \
                                  (utuple[u_nb_votes_yes], utuple[u_nb_votes_total]-utuple[u_nb_votes_yes], utuple[u_nb_votes_total]) or "",
                    'weburl'    : weburl,
                    'ln'        : ln,
                    'com_link'  : cfg_webcomment_allow_comments>0 and com_link or "",
                    'rev_link'  : cfg_webcomment_allow_reviews>0 and rev_link or ""
                  }
 
        out = '''
            <br>
            Here is a list, sorted by total number of reports, of all users who have had at least one report to one of their comments.<br>
            <br>
            <table border="1">
                <tr>
                    <td>Nickname</td>
                    <td>Email</td>
                    <td>User ID</td>
                    %(reviews_columns)s
                    <td><b>Total number of reports</b></td>
                    <td>View all user's reported comments/reviews</td>
                </tr>
                %(user_rows)s
            </table>
        ''' % { 'reviews_columns'   : cfg_webcomment_allow_reviews>0 and 
                                      "<td>Number positive votes</td><td>Number negative votes</td><td>Total number votes</td>" or "",
                'user_rows'         : user_rows 
              }
        return out

    def tmpl_admin_comments(self, ln, uid, comID, comment_data, reviews):
        """
        @param comment_data: same type of tuple as that which is returned by webcomment.py/query_retrieve_comments_or_remarks i.e.
                             tuple of comment where comment is
                             tuple (nickname, date_creation, body, id) if ranking disabled or
                             tuple (nickname, date_creation, body, nb_votes_yes, nb_votes_total, star_score, title, id)
        """
        comments = self.tmpl_get_comments(recID=-1, ln=ln, nb_per_page=0, page=1, nb_pages=1, display_order='od', display_since='all', 
                                          cfg_webcomment_allow_reviews=cfg_webcomment_allow_reviews, comments=comment_data, total_nb_comments=len(comment_data), 
                                                          avg_score=-1, warnings=[], border=1, reviews=reviews)  
        comments = comments.split("<!-- start comments table -->")[1]
        comments = comments.split("<!-- end comments table -->")[0]
         
        form_link = "%s/admin/webcomment/webcommentadmin.py/del_com?ln=%s" % (weburl, ln)
        form = self.createhiddenform(action=form_link, method="Post", text=comments, button='Delete Selected Comments')
 
        if uid > 0:
            header = "<br>Here are the reported %s of user %s <br><br>" % (reviews>0 and "reviews" or "comments", uid)
        if comID > 0:
            header = "<br>Here is comment/review %s <br><br>" % comID
        if uid > 0 and comID > 0:
            header = "<br>Here is comment/review %s written by user %s <br><br>" % (comID, uid)
        if uid ==0 and comID == 0:
            header = "<br>Here are all reported %s sorted by most reported<br><br>" % (reviews>0 and "reviews" or "comments",)

        return header + form

    def tmpl_admin_del_com(self, del_res):
        """
        @param del_res: list of the following tuple (comment_id, was_successfully_deleted), 
                        was_successfully_deleted is boolean (0=false, >0=true
        """
        table_rows = ''' '''
        for deltuple in del_res:
            table_rows += '''
            <tr><td>%s</td><td>%s</td></tr>
            ''' % (deltuple[0], deltuple[1]>0 and "Yes" or "<span class=\"important\">No</span>")

        out = '''
        <table>
            <tr><td>comment ID</td><td>successfully deleted</td></tr>
            %s
        <table>''' % (table_rows)

        return out

    def createhiddenform(self, action="", method="Get", text="", button="confirm", cnfrm='', **hidden):
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
        
        output  = '<form action="%s" method="%s">\n' % (action, string.lower(method).strip() in ['get','post'] and method or 'Get')
        output += '<table>\n<tr><td style="vertical-align: top">'
        output += text
        if cnfrm:
            output += ' <input type="checkbox" name="confirm" value="1"/>'
        for key in hidden.keys():
            if type(hidden[key]) is list:
                for value in hidden[key]:
                    output += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, value)
            else:
                output += ' <input type="hidden" name="%s" value="%s"/>\n' % (key, hidden[key])
        output += '</td><td style="vertical-align: bottom">'
        output += ' <input class="adminbutton" type="submit" value="%s"/>\n' % (button, )
        output += '</td></tr></table>'
        output += '</form>\n'
        
        return output


