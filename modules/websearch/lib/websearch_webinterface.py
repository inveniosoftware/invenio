## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012 CERN.
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

"""WebSearch URL handler."""

__revision__ = "$Id$"

import cgi
import os
import datetime
import time
import sys
from urllib import quote
from invenio import webinterface_handler_config as apache
import threading

#maximum number of collaborating authors etc shown in GUI
MAX_COLLAB_LIST = 10
MAX_KEYWORD_LIST = 10
MAX_VENUE_LIST = 10
#tag constants
AUTHOR_TAG = "100__a"
AUTHOR_INST_TAG = "100__u"
COAUTHOR_TAG = "700__a"
COAUTHOR_INST_TAG = "700__u"
VENUE_TAG = "909C4p"
KEYWORD_TAG = "695__a"
FKEYWORD_TAG = "6531_a"
CFG_INSPIRE_UNWANTED_KEYWORDS_START = ['talk',
                                      'conference',
                                      'conference proceedings',
                                      'numerical calculations',
                                      'experimental results',
                                      'review',
                                      'bibliography',
                                      'upper limit',
                                      'lower limit',
                                      'tables',
                                      'search for',
                                      'on-shell',
                                      'off-shell',
                                      'formula',
                                      'lectures',
                                      'book',
                                      'thesis']
CFG_INSPIRE_UNWANTED_KEYWORDS_MIDDLE = ['GeV',
                                        '((']

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from invenio.config import \
     CFG_SITE_URL, \
     CFG_SITE_NAME, \
     CFG_CACHEDIR, \
     CFG_SITE_LANG, \
     CFG_SITE_SECURE_URL, \
     CFG_BIBRANK_SHOW_DOWNLOAD_STATS, \
     CFG_WEBSEARCH_INSTANT_BROWSE_RSS, \
     CFG_WEBSEARCH_RSS_TTL, \
     CFG_WEBSEARCH_RSS_MAX_CACHED_REQUESTS, \
     CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, \
     CFG_WEBDIR, \
     CFG_WEBSEARCH_USE_MATHJAX_FOR_FORMATS, \
     CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS, \
     CFG_WEBSEARCH_PERMITTED_RESTRICTED_COLLECTIONS_LEVEL, \
     CFG_WEBSEARCH_USE_ALEPH_SYSNOS, \
     CFG_WEBSEARCH_RSS_I18N_COLLECTIONS, \
     CFG_INSPIRE_SITE, \
     CFG_WEBSEARCH_WILDCARD_LIMIT, \
     CFG_SITE_RECORD
from invenio.dbquery import Error
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import redirect_to_url, make_canonical_urlargd, drop_default_urlargd
from invenio.htmlutils import get_mathjax_header
from invenio.htmlutils import nmtoken_from_string
from invenio.webuser import getUid, page_not_authorized, get_user_preferences, \
    collect_user_info, logoutUser, isUserSuperAdmin
from invenio.websubmit_webinterface import WebInterfaceFilesPages
from invenio.webcomment_webinterface import WebInterfaceCommentsPages
from invenio.bibcirculation_webinterface import WebInterfaceHoldingsPages
from invenio.webpage import page, pageheaderonly, create_error_box
from invenio.messages import gettext_set_language
from invenio.search_engine import check_user_can_view_record, \
     collection_reclist_cache, \
     collection_restricted_p, \
     create_similarly_named_authors_link_box, \
     get_colID, \
     get_coll_i18nname, \
     get_fieldvalues_alephseq_like, \
     get_most_popular_field_values, \
     get_mysql_recid_from_aleph_sysno, \
     guess_primary_collection_of_a_record, \
     page_end, \
     page_start, \
     perform_request_cache, \
     perform_request_log, \
     perform_request_search, \
     restricted_collection_cache, \
     get_coll_normalised_name
from invenio.search_engine_utils import get_fieldvalues
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.access_control_mailcookie import mail_cookie_create_authorize_action
from invenio.bibformat import format_records
from invenio.bibformat_engine import get_output_formats
from invenio.websearch_webcoll import get_collection
from invenio.intbitset import intbitset
from invenio.bibupload import find_record_from_sysno
from invenio.bibrank_citation_searcher import get_cited_by_list
from invenio.bibrank_downloads_indexer import get_download_weight_total
from invenio.search_engine_summarizer import summarize_records
from invenio.errorlib import register_exception
from invenio.bibedit_webinterface import WebInterfaceEditPages
from invenio.bibeditmulti_webinterface import WebInterfaceMultiEditPages
from invenio.bibmerge_webinterface import WebInterfaceMergePages
from invenio.search_engine import get_record
from invenio.shellutils import mymkdir

import invenio.template
websearch_templates = invenio.template.load('websearch')

search_results_default_urlargd = websearch_templates.search_results_default_urlargd
search_interface_default_urlargd = websearch_templates.search_interface_default_urlargd
try:
    output_formats = [output_format['attrs']['code'].lower() for output_format in \
                      get_output_formats(with_attributes=True).values()]
except KeyError:
    output_formats = ['xd', 'xm', 'hd', 'hb', 'hs', 'hx']
output_formats.extend(['hm', 't', 'h'])

def wash_search_urlargd(form):
    """
    Create canonical search arguments from those passed via web form.
    """

    argd = wash_urlargd(form, search_results_default_urlargd)
    if argd.has_key('as'):
        argd['aas'] = argd['as']
        del argd['as']

    # Sometimes, users pass ot=245,700 instead of
    # ot=245&ot=700. Normalize that.
    ots = []
    for ot in argd['ot']:
        ots += ot.split(',')
    argd['ot'] = ots

    # We can either get the mode of function as
    # action=<browse|search>, or by setting action_browse or
    # action_search.
    if argd['action_browse']:
        argd['action'] = 'browse'
    elif argd['action_search']:
        argd['action'] = 'search'
    else:
        if argd['action'] not in ('browse', 'search'):
            argd['action'] = 'search'

    del argd['action_browse']
    del argd['action_search']

    return argd

class WebInterfaceUnAPIPages(WebInterfaceDirectory):
    """ Handle /unapi set of pages."""
    _exports = ['']

    def __call__(self, req, form):
        argd = wash_urlargd(form, {
            'id' : (int, 0),
            'format' : (str, '')})

        formats_dict = get_output_formats(True)
        formats = {}
        for format in formats_dict.values():
            if format['attrs']['visibility']:
                formats[format['attrs']['code'].lower()] = format['attrs']['content_type']
        del formats_dict


        if argd['id'] and argd['format']:
            ## Translate back common format names
            format = {
                'nlm' : 'xn',
                'marcxml' : 'xm',
                'dc' : 'xd',
                'endnote' : 'xe',
                'mods' : 'xo'
            }.get(argd['format'], argd['format'])
            if format in formats:
                redirect_to_url(req, '%s/%s/%s/export/%s' % (CFG_SITE_URL, CFG_SITE_RECORD, argd['id'], format))
            else:
                raise apache.SERVER_RETURN, apache.HTTP_NOT_ACCEPTABLE
        elif argd['id']:
            return websearch_templates.tmpl_unapi(formats, identifier=argd['id'])
        else:
            return websearch_templates.tmpl_unapi(formats)

    index = __call__


class WebInterfaceAuthorPagesCacheUpdater(threading.Thread):
    '''
    Handle asynchronous cache updates in the background as a loose Thread.
    '''
    def __init__(self, req, form, identifier, current_cache):
        threading.Thread.__init__(self)
        self.req = req
        self.form = form
        self.identifier = identifier
        self.current_cache = current_cache

    def run(self):
        webint = WebInterfaceAuthorPages()
        webint.pageparam = self.identifier
        c = datetime.datetime.now() - self.current_cache[4]
        delay = (c.microseconds + (c.seconds + c.days * 24 * 3600) * 10 ** 6) / 10 ** 6
        if delay < 3600 * 1:
            pass
        else:
            webint.update_cache_timestamp(self.identifier)
            page = webint.create_authorpage(self.req, self.form, return_html=True)
            webint.update_cache(self.identifier, page)

class WebInterfaceAuthorPages(WebInterfaceDirectory):
    """
    Handle /author/Doe%2C+John page requests as well as
    /author/<bibrec_id>:<authorname_string> (e.g. /author/15:Doe%2C+John)
    requests. The latter will try to find a person from the personid
    universe and will display the joint information from that particular
    author cluster.

    This interface will handle the following URLs:
    - /author/Doe%2C+John which will show information on the exactauthor search
    - /author/<bibrec_id>:<authorname_string> (e.g. /author/15:Doe%2C+John)
        will try to find a person from the personid
        universe and will display the joint information from that particular
        author cluster.
    - /author/<personid> (e.g. /author/152) will display the joint information
        from that particular  author cluster (an entity called person).
    """

    _exports = ['author']

    def __init__(self, pageparam=''):
        """Constructor."""
        self.pageparam = cgi.escape(pageparam.replace("+", " "))
        self.personid = -1
        self.authorname = " "
        self.must_fallback_on_person_search = False
        self.person_search_results = None
        self.search_query = None
        try:
            import invenio.bibauthorid_searchinterface as pt
            self.cache_supported = True
            self.pt = pt
        except ImportError:
            self.cache_supported = False
            self.pt = None
            raise AssertionError

    def _lookup(self, component, path):
        """This handler parses dynamic URLs (/author/John+Doe)."""
        return WebInterfaceAuthorPages(component), path


    def update_cache_timestamp(self, pageparam):
        '''
        update cache timestamp to prevent multiple threads computing the same page
        at the same time
        '''
        if not pageparam:
            return

        if not self.cache_supported:
            return

        self.pt.update_cached_author_page_timestamp(pageparam)

    def update_cache(self, pageparam, pagecontent):
        '''
        Triggers the update to the DB
        @param pageparam: identifier for the cache
        @type pageparam: string
        @param pagecontent: content to write to cache
        @type pagecontent: string
        '''
        #TABLE: id, tag, identifier, data, date
        if not pageparam:
            return

        if not pagecontent:
            return

        if not self.cache_supported:
            return

        self.pt.update_cached_author_page(pageparam, pagecontent)


    def __call__(self, req, form):
        '''
        Cache manager for the author pages.
        #look up self.pageparam in cache table
        #if up to date return it
        #if not up to date:
        #    if exists:
        #        return it and update
        #    else:
        #        create, update, return
        @param req: Apache request object
        @type req: Apache request object
        @param form: Parameters
        @type form: dict

        @return: HTML code for the author or author search page
        @rtype: string
        '''
        argd = wash_urlargd(form,
                            {'ln': (str, CFG_SITE_LANG),
                             'verbose': (int, 0),
                             'recid': (int, -1)
                             })
        param_recid = argd['recid']
        ln = argd['ln']
        req.argd = argd #needed since perform_req_search
        _ = gettext_set_language(ln)
        title_message = "Author Details"
        page_content = ""

        is_bibauthorid = False
        try:
            from invenio.bibauthorid_webapi import search_person_ids_by_name
            from invenio.bibauthorid_webapi import get_papers_by_person_id
            from invenio.bibauthorid_webapi import get_person_names_from_id
            from invenio.bibauthorid_webapi import get_person_db_names_from_id
            from invenio.bibauthorid_webapi import get_person_redirect_link
            from invenio.bibauthorid_webapi import is_valid_canonical_id
            from invenio.bibauthorid_name_utils import create_normalized_name
            from invenio.bibauthorid_name_utils import split_name_parts
#            from invenio.bibauthorid_config import CLAIMPAPER_CLAIM_OTHERS_PAPERS
            from invenio.bibauthorid_config import AID_ENABLED
            from invenio.bibauthorid_config import AID_ON_AUTHORPAGES
            bibauthorid_template = invenio.template.load('bibauthorid')
            import bibauthorid_searchinterface as pt
            is_bibauthorid = True
        except ImportError:
            return self.create_authorpage(req, form)

        if not AID_ENABLED or not AID_ON_AUTHORPAGES:
                is_bibauthorid = False

        self.resolve_personid(param_recid)

        if self.personid > -1:
            identifier = self.personid
        else:
            identifier = self.pageparam

        cached_page = pt.get_cached_author_page(identifier)

        if cached_page:
            page_content = cached_page[3]
            background = WebInterfaceAuthorPagesCacheUpdater(req, form,
                                                             identifier,
                                                             cached_page)
            background.start()

        else:
            pagecontent = self.create_authorpage(req, form, return_html=True)
            self.update_cache(identifier, pagecontent)
            page_content = pagecontent

        metaheaderadd = ""

        ### next two lines are commented out in order to avoid
        ### including all JS files in /author pages:
        #if is_bibauthorid:
        #    metaheaderadd = bibauthorid_template.tmpl_meta_includes()

        # Start the page in clean manner:
        req.content_type = "text/html"
        req.send_http_header()
        req.write(pageheaderonly(req=req, title=title_message, uid=getUid(req),
                                 metaheaderadd=metaheaderadd, language=ln))
        req.write(websearch_templates.tmpl_search_pagestart(ln=ln))
        req.write(page_content)

        return page_end(req, 'hb', ln)


    def resolve_personid(self, param_recid):
        '''
        Resolves the Person ID from a given string.

        @param param_recid: record ID parameter
        @type param_recid: int
        '''
        try:
            from invenio.bibauthorid_webapi import search_person_ids_by_name
            from invenio.bibauthorid_webapi import get_papers_by_person_id
            from invenio.bibauthorid_webapi import get_person_id_from_canonical_id
            from invenio.bibauthorid_webapi import is_valid_canonical_id
            from invenio.bibauthorid_config import AID_ENABLED
            from invenio.bibauthorid_config import AID_ON_AUTHORPAGES
#            from invenio.access_control_admin import acc_find_user_role_actions

            if not AID_ENABLED or not AID_ON_AUTHORPAGES:
                is_bibauthorid = False
            else:
                is_bibauthorid = True
        except (ImportError):
            is_bibauthorid = False

        from operator import itemgetter

        authors = []
        recid = None
        nquery = ""

        #check if it is a person id (e.g. 144):
        try:
            self.personid = int(self.pageparam)
        except (ValueError, TypeError):
            self.personid = -1

        if self.personid > -1:
            return
        #check if it is a canonical ID (e.g. Ellis_J_1):
        if is_bibauthorid and is_valid_canonical_id(self.pageparam):
            try:
                self.personid = int(get_person_id_from_canonical_id(self.pageparam))
            except (ValueError, TypeError):
                self.personid = -1

        if self.personid < 0 and is_bibauthorid:
            if param_recid > -1:
                # Well, it's not a person id, did we get a record ID?
                recid = param_recid
                nquery = self.pageparam
            elif self.pageparam.count(":"):
                # No recid passed, maybe name is recid:name or name:recid pair?
                left, right = self.pageparam.split(":")

                try:
                    recid = int(left)
                    nquery = str(right)
                except (ValueError, TypeError):
                    try:
                        recid = int(right)
                        nquery = str(left)
                    except (ValueError, TypeError):
                        recid = None
                        nquery = self.pageparam
            else:
                # No recid could be determined. Work with name only
                nquery = self.pageparam

            sorted_results = search_person_ids_by_name(nquery)
            test_results = None

            if recid:
                for results in sorted_results:
                    pid = results[0]
                    authorpapers = get_papers_by_person_id(pid, -1)
                    authorpapers = sorted(authorpapers, key=itemgetter(0),
                                          reverse=True)

                    if (recid and
                        not (str(recid) in [row[0] for row in authorpapers])):
                        continue

                    authors.append([results[0], results[1],
                                    authorpapers[0:4]])

                test_results = authors
            else:
                test_results = [i for i in sorted_results if i[1][0][2] > .8]

            if len(test_results) == 1:
                self.personid = test_results[0][0]
            else:
                self.person_search_results = sorted_results
                self.search_query = nquery
                self.must_fallback_on_person_search = True

    def create_authorpage(self, req, form, return_html=False):
        '''
        Creates an author page in a given language
        If no author is found, return person search or an empty author page
        @param req: Apache request object
        @type req: Apache request object
        @param form: URL parameters
        @type form: dict
        @param return_html: if False: write to req object consecutively else
        construct and return html code for the caches
        @type return_html: boolean
        '''
        is_bibauthorid = False
        bibauthorid_template = None
        userinfo = collect_user_info(req)
        metaheaderadd = ""
        html = []

        try:
            from invenio.bibauthorid_webapi import search_person_ids_by_name
            from invenio.bibauthorid_webapi import get_papers_by_person_id
            from invenio.bibauthorid_webapi import get_person_names_from_id
            from invenio.bibauthorid_webapi import get_person_db_names_from_id
            from invenio.bibauthorid_webapi import get_person_redirect_link
            from invenio.bibauthorid_webapi import is_valid_canonical_id
            from invenio.bibauthorid_name_utils import create_normalized_name
            from invenio.bibauthorid_name_utils import split_name_parts
#            from invenio.bibauthorid_config import CLAIMPAPER_CLAIM_OTHERS_PAPERS
            from invenio.bibauthorid_config import AID_ENABLED
            from invenio.bibauthorid_config import AID_ON_AUTHORPAGES
            bibauthorid_template = invenio.template.load('bibauthorid')
#            from invenio.access_control_admin import acc_find_user_role_actions

            if not AID_ENABLED or not AID_ON_AUTHORPAGES:
                is_bibauthorid = False
            else:
                is_bibauthorid = True
        except (ImportError):
            is_bibauthorid = False

        from operator import itemgetter
        import time

        argd = wash_urlargd(form,
                            {'ln': (str, CFG_SITE_LANG),
                             'verbose': (int, 0),
                             'recid': (int, -1)
                             })
        ln = argd['ln']
        verbose = argd['verbose']
        req.argd = argd #needed since perform_req_search
        param_recid = argd['recid']
        bibauthorid_data = {"is_baid": is_bibauthorid, "pid":-1, "cid": ""}

        pubs = []
        authors = []
        recid = None
        nquery = ""
        names_dict = {}
        db_names_dict = {}
        _ = gettext_set_language(ln)
        title_message = "Author Details"

        #let's see what takes time..
        time1 = time.time()
        genstart = time1
        time2 = time.time()

        if is_bibauthorid:
            metaheaderadd = bibauthorid_template.tmpl_meta_includes()
        if not return_html:
            # Start the page in clean manner:
            req.content_type = "text/html"
            req.send_http_header()
            req.write(pageheaderonly(req=req, title=title_message,
                                     metaheaderadd=metaheaderadd,
                                     language=ln))
            req.write(websearch_templates.tmpl_search_pagestart(ln=ln))

        if is_bibauthorid:
            self.resolve_personid(param_recid)

            if self.must_fallback_on_person_search:
                if bibauthorid_template and self.search_query:
                    authors = []

                    for results in self.person_search_results:
                        pid = results[0]
                        authorpapers = get_papers_by_person_id(pid, -1)
                        authorpapers = sorted(authorpapers, key=itemgetter(0),
                                              reverse=True)
                        authors.append([results[0], results[1],
                                        authorpapers[0:4]])

                    srch = bibauthorid_template.tmpl_author_search
                    body = srch(self.search_query, authors, author_pages_mode=True)

                    if return_html:
                        html.append(body)
                        return "\n".join(html)
                    else:
                        req.write(body)
                        return
        import time
        # start page
#        req.content_type = "text/html"
#        req.send_http_header()
#        uid = getUid(req)
#        page_start(req, "hb", "", "", ln, uid)

        if self.personid < 0 and is_bibauthorid:
            # Well, no person. Fall back to the exact author name search then.
            ptitle = None
            if recid:
                try:
                    ptitle = get_record(recid)['245'][0][0][0][1]
                except (IndexError, TypeError, KeyError):
                    ptitle = '"Title not available"'
            else:
                return redirect_to_url(req, "%s/person/search" % (CFG_SITE_URL))

            self.authorname = self.pageparam
            title = ''
            pmsg = ''

            if ptitle:
                pmsg = " on paper '%s'" % ptitle

            # We're sorry we're introducing html tags where they weren't before. XXX
            message = ""

            if CFG_INSPIRE_SITE:
                message += ("<p>We are in the process of attributing papers to people so that we can "
                            "improve publication lists.</p>\n")

            message += ("<p>We have not generated the publication list for author '%s'%s.  Please be patient as we "
                        "continue to match people to author names and publications. '%s' may be attributed in the next "
                        "few weeks.</p>" % (self.pageparam, pmsg, self.pageparam))

            if return_html:
                html.append('<div id="header">%s</div><br>' % title)
                html.append('%s <br>' % message)

            else:
                req.write('<div id="header">%s</div><br>' % title)
                req.write('%s <br>' % message)

            if not nquery:
                nquery = self.pageparam

            if not authors:
                authors = []
                sorted_results = search_person_ids_by_name(nquery)

                for results in sorted_results:
                    pid = results[0]
                    authorpapers = get_papers_by_person_id(pid, -1)
                    authorpapers = sorted(authorpapers, key=itemgetter(0),
                                          reverse=True)
                    authors.append([results[0], results[1],
                                    authorpapers[0:4]])

            srch = bibauthorid_template.tmpl_author_search
            body = srch(nquery, authors, author_pages_mode=True)

            if return_html:
                html.append(body)
                return "\n".join(html)
            else:
                req.write(body)

            return
#            return self._psearch(req, form, is_fallback=True, fallback_query=self.pageparam,  fallback_title=title, fallback_message=message)

        elif self.personid < 0 and not is_bibauthorid:
            if not self.pageparam:
                return websearch_templates.tmpl_author_information(req, {},
                                                            self.authorname,
                                                            0, {}, {}, {},
                                                            {}, {}, {},
                                                            None,
                                                            bibauthorid_data,
                                                            ln, return_html)

            self.authorname = self.pageparam
            #search the publications by this author
            pubs = perform_request_search(req=None, p=self.authorname, f="exactauthor")
            names_dict[self.authorname] = len(pubs)
            db_names_dict[self.authorname] = len(pubs)

        elif is_bibauthorid and self.personid > -1:
            #yay! Person found! find only papers not disapproved by humans
            if return_html:
                html.append("<!-- Authorpages are Bibauthorid-powered !-->")
            else:
                req.write("<!-- Authorpages are Bibauthorid-powered !-->")

            full_pubs = get_papers_by_person_id(self.personid, -1)
            pubs = [int(row[0]) for row in full_pubs]
            longest_name = ""

            try:
                self.personid = int(self.personid)
            except (TypeError, ValueError):
                raise ValueError("Personid must be a number!")

            for aname, acount in get_person_names_from_id(self.personid):
                names_dict[aname] = acount
                norm_name = create_normalized_name(split_name_parts(aname))

                if len(norm_name) > len(longest_name):
                    longest_name = norm_name

            for aname, acount in get_person_db_names_from_id(self.personid):
                aname = aname.replace('"', '').strip()
                db_names_dict[aname] = acount

            self.authorname = longest_name

        if not pubs and param_recid > -1:
            if return_html:
                html.append("<p>")
                html.append(_("We're sorry. The requested author \"%s\" seems not to be listed on the specified paper."
                            % (self.pageparam,)))
                html.append("<br />")
                html.append(_("Please try the following link to start a broader search on the author: "))
                html.append('<a href="%s/author/%s">%s</a>'
                          % (CFG_SITE_URL, self.pageparam, self.pageparam))
                html.append("</p>")

                return "\n".join(html)
            else:

                req.write("<p>")
                req.write(_("We're sorry. The requested author \"%s\" seems not to be listed on the specified paper."
                            % (self.pageparam,)))
                req.write("<br />")
                req.write(_("Please try the following link to start a broader search on the author: "))
                req.write('<a href="%s/author/%s">%s</a>'
                          % (CFG_SITE_URL, self.pageparam, self.pageparam))
                req.write("</p>")

                return page_end(req, 'hb', ln)

        #get most frequent authors of these pubs
        popular_author_tuples = get_most_popular_field_values(pubs, (AUTHOR_TAG, COAUTHOR_TAG))
        coauthors = {}

        for (coauthor, frequency) in popular_author_tuples:
            if coauthor not in db_names_dict:
                coauthors[coauthor] = frequency

            if len(coauthors) > MAX_COLLAB_LIST:
                break

        time1 = time.time()
        if verbose == 9 and not return_html:
            req.write("<br/>popularized authors: " + str(time1 - time2) + "<br/>")

        #and publication venues
        venuetuples = get_most_popular_field_values(pubs, (VENUE_TAG))
        time2 = time.time()
        if verbose == 9 and not return_html:
            req.write("<br/>venues: " + str(time2 - time1) + "<br/>")


        #and keywords
        kwtuples = get_most_popular_field_values(pubs, (KEYWORD_TAG, FKEYWORD_TAG), count_repetitive_values=False)
        if CFG_INSPIRE_SITE:
            # filter kw tuples against unwanted keywords:
            kwtuples_filtered = ()
            for (kw, num) in kwtuples:
                kwlower = kw.lower()
                kwlower_unwanted = False
                for unwanted_keyword in CFG_INSPIRE_UNWANTED_KEYWORDS_START:
                    if kwlower.startswith(unwanted_keyword):
                        kwlower_unwanted = True  # unwanted keyword found
                        break
                for unwanted_keyword in CFG_INSPIRE_UNWANTED_KEYWORDS_MIDDLE:
                    if unwanted_keyword in kwlower:
                        kwlower_unwanted = True  # unwanted keyword found
                        break
                if not kwlower_unwanted:
                    kwtuples_filtered += ((kw, num),)
            kwtuples = kwtuples_filtered
        time1 = time.time()

        if verbose == 9 and not return_html:
            req.write("<br/>keywords: " + str(time1 - time2) + "<br/>")

        #construct a simple list of tuples that contains keywords that appear
        #more than once moreover, limit the length of the list
        #to MAX_KEYWORD_LIST
        kwtuples = kwtuples[0:MAX_KEYWORD_LIST]
        vtuples = venuetuples[0:MAX_VENUE_LIST]

        time2 = time.time()
        if verbose == 9 and not return_html:
            req.write("<br/>misc: " + str(time2 - time1) + "<br/>")

        #a dict. keys: affiliations, values: lists of publications
        author_aff_pubs = self.get_institute_pub_dict(pubs, db_names_dict.keys())

        time1 = time.time()
        if verbose == 9 and not return_html:
            req.write("<br/>affiliations: " + str(time1 - time2) + "<br/>")

        totaldownloads = 0
        if CFG_BIBRANK_SHOW_DOWNLOAD_STATS:
            #find out how many times these records have been downloaded
            recsloads = {}
            recsloads = get_download_weight_total(recsloads, pubs)
            #sum up
            for k in recsloads.keys():
                totaldownloads = totaldownloads + recsloads[k]

        #get cited by..
        citedbylist = get_cited_by_list(pubs)
        person_link = None


        if (is_bibauthorid
            and self.personid >= 0
            and "precached_viewclaimlink" in userinfo
            and "precached_usepaperattribution" in userinfo
            and "precached_usepaperclaim" in userinfo
            and (userinfo["precached_usepaperclaim"]
                 or userinfo["precached_usepaperattribution"])
            ):
            person_link = self.personid
            bibauthorid_data["pid"] = self.personid
            cid = get_person_redirect_link(self.personid)

            if is_valid_canonical_id(cid):
                person_link = cid
                bibauthorid_data["cid"] = cid

        time1 = time.time()
        if verbose == 9 and not return_html:
            req.write("<br/>citedby: " + str(time1 - time2) + "<br/>")

        #finally all stuff there, call the template
        if return_html:
            html.append(websearch_templates.tmpl_author_information(req, pubs,
                                                    self.authorname,
                                                    totaldownloads,
                                                    author_aff_pubs,
                                                    citedbylist, kwtuples,
                                                    coauthors, vtuples,
                                                    db_names_dict, person_link,
                                                    bibauthorid_data, ln,
                                                    return_html))
        else:
            websearch_templates.tmpl_author_information(req, pubs,
                                                    self.authorname,
                                                    totaldownloads,
                                                    author_aff_pubs,
                                                    citedbylist, kwtuples,
                                                    coauthors, vtuples,
                                                    db_names_dict, person_link,
                                                    bibauthorid_data, ln,
                                                    return_html)

        time1 = time.time()
        #cited-by summary
        rec_query = ""
        extended_author_search_str = ""

        if bibauthorid_data['is_baid']:
            if bibauthorid_data["cid"]:
                rec_query = 'author:"%s"' % bibauthorid_data["cid"]
            elif bibauthorid_data["pid"] > -1:
                rec_query = 'author:"%s"' % bibauthorid_data["pid"]

        if not rec_query:
            rec_query = 'exactauthor:"' + self.authorname + '"'

            if is_bibauthorid:
                if len(db_names_dict.keys()) > 1:
                    extended_author_search_str = '('

                for name_index, name_query in enumerate(db_names_dict.keys()):
                    if name_index > 0:
                        extended_author_search_str += " OR "

                    extended_author_search_str += 'exactauthor:"' + name_query + '"'

                if len(db_names_dict.keys()) > 1:
                    extended_author_search_str += ')'

            if is_bibauthorid and extended_author_search_str:
                rec_query = extended_author_search_str

        if pubs:
            if return_html:
                html.append(summarize_records(intbitset(pubs), 'hcs', ln, rec_query))
            else:
                req.write(summarize_records(intbitset(pubs), 'hcs', ln, rec_query, req=req))

        time2 = time.time()
        if verbose == 9 and not return_html:
            req.write("<br/>summarizer: " + str(time2 - time1) + "<br/>")

#        simauthbox = create_similarly_named_authors_link_box(self.authorname)
#        req.write(simauthbox)
        if verbose == 9 and not return_html:
            req.write("<br/>all: " + str(time.time() - genstart) + "<br/>")

        if return_html:
            return "\n".join(html)
        else:
            return page_end(req, 'hb', ln)

    def _psearch(self, req, form, is_fallback=True, fallback_query='', fallback_title='', fallback_message=''):
        html = []
        h = html.append
        if fallback_title:
                h('<div id="header">%s</div><br>' % fallback_title)
        if fallback_message:
                h('%s <br>' % fallback_message)
        h(' We may have \'%s\' partially matched; <a href=/person/search?q=%s>click here</a> ' % (fallback_query, fallback_query))
        h('to see what we have so far.  (Note: this is likely to update frequently.')
        return "\n".join(html)


    def get_institute_pub_dict(self, recids, names_list):
        """return a dictionary consisting of institute -> list of publications"""
        author_aff_pubs = {} #the dictionary to be built
        for recid in recids:
            #iterate all so that we get first author's intitute
            #if this the first author OR
            #"his" institute if he is an affliate author
            affus = [] #list of insts from the given record
            mainauthors = get_fieldvalues(recid, AUTHOR_TAG)
            mainauthor = " "
            if mainauthors:
                mainauthor = mainauthors[0]
            if (mainauthor in names_list):
                affus = get_fieldvalues(recid, AUTHOR_INST_TAG)
            else:
                #search for coauthors..
                coauthor_field_lines = []
                coauthorfield_content = get_fieldvalues_alephseq_like(recid, \
                                        COAUTHOR_TAG[:3])
                if coauthorfield_content:
                    coauthor_field_lines = coauthorfield_content.split("\n")
                for line in coauthor_field_lines:
                    for name_item in names_list:
                        breakit = False
                        if line.count(name_item) > 0:
                            #get affilitions .. the correct ones are $$+code
                            code = COAUTHOR_INST_TAG[-1]
                            myparts = line.split("$$")
                            for part in myparts:
                                if part and part[0] == code:
                                    myaff = part[1:]
                                    affus.append(myaff)
                            breakit = True
                        if breakit:
                            break

            #if this is empty, add a dummy " " value
            if (affus == []):
                affus = [" "]
            for a in affus:
                #add in author_aff_pubs
                if (author_aff_pubs.has_key(a)):
                    tmp = author_aff_pubs[a]
                    tmp.append(recid)
                    author_aff_pubs[a] = tmp
                else:
                    author_aff_pubs[a] = [recid]
        return author_aff_pubs

    index = __call__


class WebInterfaceRecordPages(WebInterfaceDirectory):
    """ Handling of a /CFG_SITE_RECORD/<recid> URL fragment """

    _exports = ['', 'files', 'reviews', 'comments', 'usage',
                'references', 'export', 'citations', 'holdings', 'edit',
                'keywords', 'multiedit', 'merge', 'plots']

    #_exports.extend(output_formats)

    def __init__(self, recid, tab, format=None):
        self.recid = recid
        self.tab = tab
        self.format = format

        self.files = WebInterfaceFilesPages(self.recid)
        self.reviews = WebInterfaceCommentsPages(self.recid, reviews=1)
        self.comments = WebInterfaceCommentsPages(self.recid)
        self.usage = self
        self.references = self
        self.keywords = self
        self.holdings = WebInterfaceHoldingsPages(self.recid)
        self.citations = self
        self.plots = self
        self.export = WebInterfaceRecordExport(self.recid, self.format)
        self.edit = WebInterfaceEditPages(self.recid)
        self.merge = WebInterfaceMergePages(self.recid)

        return

    def __call__(self, req, form):
        argd = wash_search_urlargd(form)

        argd['recid'] = self.recid

        argd['tab'] = self.tab

        if self.format is not None:
            argd['of'] = self.format
        req.argd = argd
        uid = getUid(req)
        if uid == -1:
            return page_not_authorized(req, "../",
                text="You are not authorized to view this record.",
                                       navmenuid='search')
        elif uid > 0:
            pref = get_user_preferences(uid)
            try:
                if not form.has_key('rg'):
                    # fetch user rg preference only if not overridden via URL
                    argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass

        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)

        if argd['rg'] > CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS and acc_authorize_action(req, 'runbibedit')[0] != 0:
            argd['rg'] = CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS

        #check if the user has rights to set a high wildcard limit
        #if not, reduce the limit set by user, with the default one
        if CFG_WEBSEARCH_WILDCARD_LIMIT > 0 and (argd['wl'] > CFG_WEBSEARCH_WILDCARD_LIMIT or argd['wl'] == 0):
            if acc_authorize_action(req, 'runbibedit')[0] != 0:
                argd['wl'] = CFG_WEBSEARCH_WILDCARD_LIMIT

        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                    make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text=auth_msg, \
                navmenuid='search')

        from invenio.search_engine import record_exists, get_merged_recid
        # check if the current record has been deleted
        # and has been merged, case in which the deleted record
        # will be redirect to the new one
        record_status = record_exists(argd['recid'])
        merged_recid = get_merged_recid(argd['recid'])
        if record_status == -1 and merged_recid:
            url = CFG_SITE_URL + '/' + CFG_SITE_RECORD + '/%s?ln=%s'
            url %= (str(merged_recid), argd['ln'])
            redirect_to_url(req, url)

        # mod_python does not like to return [] in case when of=id:
        out = perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    # Return the same page wether we ask for /CFG_SITE_RECORD/123 or /CFG_SITE_RECORD/123/
    index = __call__

class WebInterfaceRecordRestrictedPages(WebInterfaceDirectory):
    """ Handling of a /record-restricted/<recid> URL fragment """

    _exports = ['', 'files', 'reviews', 'comments', 'usage',
                'references', 'export', 'citations', 'holdings', 'edit',
                'keywords', 'multiedit', 'merge', 'plots']

    #_exports.extend(output_formats)

    def __init__(self, recid, tab, format=None):
        self.recid = recid
        self.tab = tab
        self.format = format

        self.files = WebInterfaceFilesPages(self.recid)
        self.reviews = WebInterfaceCommentsPages(self.recid, reviews=1)
        self.comments = WebInterfaceCommentsPages(self.recid)
        self.usage = self
        self.references = self
        self.keywords = self
        self.holdings = WebInterfaceHoldingsPages(self.recid)
        self.citations = self
        self.plots = self
        self.export = WebInterfaceRecordExport(self.recid, self.format)
        self.edit = WebInterfaceEditPages(self.recid)
        self.merge = WebInterfaceMergePages(self.recid)

        return

    def __call__(self, req, form):
        argd = wash_search_urlargd(form)
        argd['recid'] = self.recid
        if self.format is not None:
            argd['of'] = self.format

        req.argd = argd

        uid = getUid(req)
        user_info = collect_user_info(req)
        if uid == -1:
            return page_not_authorized(req, "../",
                text="You are not authorized to view this record.",
                                       navmenuid='search')
        elif uid > 0:
            pref = get_user_preferences(uid)
            try:
                if not form.has_key('rg'):
                    # fetch user rg preference only if not overridden via URL
                    argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass

        if argd['rg'] > CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS and acc_authorize_action(req, 'runbibedit')[0] != 0:
            argd['rg'] = CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS

        #check if the user has rights to set a high wildcard limit
        #if not, reduce the limit set by user, with the default one
        if CFG_WEBSEARCH_WILDCARD_LIMIT > 0 and (argd['wl'] > CFG_WEBSEARCH_WILDCARD_LIMIT or argd['wl'] == 0):
            if acc_authorize_action(req, 'runbibedit')[0] != 0:
                argd['wl'] = CFG_WEBSEARCH_WILDCARD_LIMIT

        record_primary_collection = guess_primary_collection_of_a_record(self.recid)

        if collection_restricted_p(record_primary_collection):
            (auth_code, dummy) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=record_primary_collection)
            if auth_code:
                return page_not_authorized(req, "../",
                    text="You are not authorized to view this record.",
                    navmenuid='search')

        # Keep all the arguments, they might be reused in the
        # record page itself to derivate other queries
        req.argd = argd

        # mod_python does not like to return [] in case when of=id:
        out = perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    # Return the same page wether we ask for /CFG_SITE_RECORD/123 or /CFG_SITE_RECORD/123/
    index = __call__

class WebInterfaceSearchResultsPages(WebInterfaceDirectory):
    """ Handling of the /search URL and its sub-pages. """

    _exports = ['', 'authenticate', 'cache', 'log']

    def __call__(self, req, form):
        """ Perform a search. """
        argd = wash_search_urlargd(form)

        _ = gettext_set_language(argd['ln'])

        if req.method == 'POST':
            raise apache.SERVER_RETURN, apache.HTTP_METHOD_NOT_ALLOWED

        uid = getUid(req)
        user_info = collect_user_info(req)
        if uid == -1:
            return page_not_authorized(req, "../",
                text=_("You are not authorized to view this area."),
                                       navmenuid='search')
        elif uid > 0:
            pref = get_user_preferences(uid)
            try:
                if not form.has_key('rg'):
                    # fetch user rg preference only if not overridden via URL
                    argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass

            if CFG_WEBSEARCH_PERMITTED_RESTRICTED_COLLECTIONS_LEVEL == 2:
                ## Let's update the current collections list with all
                ## the restricted collections the user has rights to view.
                try:
                    restricted_collections = user_info['precached_permitted_restricted_collections']
                    argd_collections = set(argd['c'])
                    argd_collections.update(restricted_collections)
                    argd['c'] = list(argd_collections)
                except KeyError:
                    pass

        if argd['rg'] > CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS and acc_authorize_action(req, 'runbibedit')[0] != 0:
            argd['rg'] = CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS

        involved_collections = set()
        involved_collections.update(argd['c'])
        involved_collections.add(argd['cc'])

        if argd['id'] > 0:
            argd['recid'] = argd['id']
        if argd['idb'] > 0:
            argd['recidb'] = argd['idb']
        if argd['sysno']:
            tmp_recid = find_record_from_sysno(argd['sysno'])
            if tmp_recid:
                argd['recid'] = tmp_recid
        if argd['sysnb']:
            tmp_recid = find_record_from_sysno(argd['sysnb'])
            if tmp_recid:
                argd['recidb'] = tmp_recid

        if argd['recid'] > 0:
            if argd['recidb'] > argd['recid']:
                # Hack to check if among the restricted collections
                # at least a record of the range is there and
                # then if the user is not authorized for that
                # collection.
                recids = intbitset(xrange(argd['recid'], argd['recidb']))
                restricted_collection_cache.recreate_cache_if_needed()
                for collname in restricted_collection_cache.cache:
                    (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=collname)
                    if auth_code and user_info['email'] == 'guest':
                        coll_recids = get_collection(collname).reclist
                        if coll_recids & recids:
                            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : collname})
                            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                                    make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri}, {})
                            return redirect_to_url(req, target, norobot=True)
                    elif auth_code:
                        return page_not_authorized(req, "../", \
                            text=auth_msg, \
                            navmenuid='search')
            else:
                involved_collections.add(guess_primary_collection_of_a_record(argd['recid']))

        # If any of the collection requires authentication, redirect
        # to the authentication form.
        for coll in involved_collections:
            if collection_restricted_p(coll):
                (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=coll)
                if auth_code and user_info['email'] == 'guest':
                    cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : coll})
                    target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                            make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri}, {})
                    return redirect_to_url(req, target, norobot=True)
                elif auth_code:
                    return page_not_authorized(req, "../", \
                        text=auth_msg, \
                        navmenuid='search')

        #check if the user has rights to set a high wildcard limit
        #if not, reduce the limit set by user, with the default one
        if CFG_WEBSEARCH_WILDCARD_LIMIT > 0 and (argd['wl'] > CFG_WEBSEARCH_WILDCARD_LIMIT or argd['wl'] == 0):
            auth_code, auth_message = acc_authorize_action(req, 'runbibedit')
            if auth_code != 0:
                argd['wl'] = CFG_WEBSEARCH_WILDCARD_LIMIT

        # Keep all the arguments, they might be reused in the
        # search_engine itself to derivate other queries
        req.argd = argd

        # mod_python does not like to return [] in case when of=id:
        out = perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    def cache(self, req, form):
        """Search cache page."""
        argd = wash_urlargd(form, {'action': (str, 'show')})
        return perform_request_cache(req, action=argd['action'])

    def log(self, req, form):
        """Search log page."""
        argd = wash_urlargd(form, {'date': (str, '')})
        return perform_request_log(req, date=argd['date'])

    def authenticate(self, req, form):
        """Restricted search results pages."""

        argd = wash_search_urlargd(form)

        user_info = collect_user_info(req)
        for coll in argd['c'] + [argd['cc']]:
            if collection_restricted_p(coll):
                (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=coll)
                if auth_code and user_info['email'] == 'guest':
                    cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : coll})
                    target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                            make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri}, {})
                    return redirect_to_url(req, target, norobot=True)
                elif auth_code:
                    return page_not_authorized(req, "../", \
                        text=auth_msg, \
                        navmenuid='search')

        #check if the user has rights to set a high wildcard limit
        #if not, reduce the limit set by user, with the default one
        if CFG_WEBSEARCH_WILDCARD_LIMIT > 0 and (argd['wl'] > CFG_WEBSEARCH_WILDCARD_LIMIT or argd['wl'] == 0):
            auth_code, auth_message = acc_authorize_action(req, 'runbibedit')
            if auth_code != 0:
                argd['wl'] = CFG_WEBSEARCH_WILDCARD_LIMIT

        # Keep all the arguments, they might be reused in the
        # search_engine itself to derivate other queries
        req.argd = argd

        uid = getUid(req)
        if uid > 0:
            pref = get_user_preferences(uid)
            try:
                if not form.has_key('rg'):
                    # fetch user rg preference only if not overridden via URL
                    argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass


        # mod_python does not like to return [] in case when of=id:
        out = perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    index = __call__

class WebInterfaceLegacySearchPages(WebInterfaceDirectory):
    """ Handling of the /search.py URL and its sub-pages. """

    _exports = ['', ('authenticate', 'index')]

    def __call__(self, req, form):
        """ Perform a search. """

        argd = wash_search_urlargd(form)

        # We either jump into the generic search form, or the specific
        # /CFG_SITE_RECORD/... display if a recid is requested
        if argd['recid'] != -1:
            target = '/%s/%d' % (CFG_SITE_RECORD, argd['recid'])
            del argd['recid']

        else:
            target = '/search'

        target += make_canonical_urlargd(argd, search_results_default_urlargd)
        return redirect_to_url(req, target, apache.HTTP_MOVED_PERMANENTLY)

    index = __call__


# Parameters for the legacy URLs, of the form /?c=ALEPH
legacy_collection_default_urlargd = {
    'as': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
    'aas': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
    'verbose': (int, 0),
    'c': (str, CFG_SITE_NAME)}

class WebInterfaceSearchInterfacePages(WebInterfaceDirectory):

    """ Handling of collection navigation."""

    _exports = [('index.py', 'legacy_collection'),
                ('', 'legacy_collection'),
                ('search.py', 'legacy_search'),
                'search', 'openurl',
                'opensearchdescription', 'logout_SSO_hook']

    search = WebInterfaceSearchResultsPages()
    legacy_search = WebInterfaceLegacySearchPages()

    def logout_SSO_hook(self, req, form):
        """Script triggered by the display of the centralized SSO logout
        dialog. It logouts the user from Invenio and stream back the
        expected picture."""
        logoutUser(req)
        req.content_type = 'image/gif'
        req.encoding = None
        req.filename = 'wsignout.gif'
        req.headers_out["Content-Disposition"] = "inline; filename=wsignout.gif"
        req.set_content_length(os.path.getsize('%s/img/wsignout.gif' % CFG_WEBDIR))
        req.send_http_header()
        req.sendfile('%s/img/wsignout.gif' % CFG_WEBDIR)

    def _lookup(self, component, path):
        """ This handler is invoked for the dynamic URLs (for
        collections and records)"""

        if component == 'collection':
            c = '/'.join(path)

            def answer(req, form):
                """Accessing collections cached pages."""
                # Accessing collections: this is for accessing the
                # cached page on top of each collection.

                argd = wash_urlargd(form, search_interface_default_urlargd)

                # We simply return the cached page of the collection
                argd['c'] = c

                if not argd['c']:
                    # collection argument not present; display
                    # home collection by default
                    argd['c'] = CFG_SITE_NAME

                # Treat `as' argument specially:
                if argd.has_key('as'):
                    argd['aas'] = argd['as']
                    del argd['as']

                return display_collection(req, **argd)

            return answer, []


        elif component == CFG_SITE_RECORD and path and path[0] == 'merge':
            return WebInterfaceMergePages(), path[1:]

        elif component == CFG_SITE_RECORD and path and path[0] == 'edit':
            return WebInterfaceEditPages(), path[1:]

        elif component == CFG_SITE_RECORD and path and path[0] == 'multiedit':
            return WebInterfaceMultiEditPages(), path[1:]

        elif component == CFG_SITE_RECORD or component == 'record-restricted':
            try:
                if CFG_WEBSEARCH_USE_ALEPH_SYSNOS:
                    # let us try to recognize /<CFG_SITE_RECORD>/<SYSNO> style of URLs:
                    # check for SYSNOs with an embedded slash; needed for [ARXIVINV-15]
                    if len(path) > 1 and get_mysql_recid_from_aleph_sysno(path[0] + "/" + path[1]):
                        path[0] = path[0] + "/" + path[1]
                        del path[1]
                    x = get_mysql_recid_from_aleph_sysno(path[0])
                    if x:
                        recid = x
                    else:
                        recid = int(path[0])
                else:
                    recid = int(path[0])
            except IndexError:
                # display record #1 for URL /CFG_SITE_RECORD without a number
                recid = 1
            except ValueError:
                if path[0] == '':
                    # display record #1 for URL /CFG_SITE_RECORD/ without a number
                    recid = 1
                else:
                    # display page not found for URLs like /CFG_SITE_RECORD/foo
                    return None, []

            from invenio.intbitset import __maxelem__
            if recid <= 0 or recid > __maxelem__:
                # __maxelem__ = 2147483647
                # display page not found for URLs like /CFG_SITE_RECORD/-5 or /CFG_SITE_RECORD/0 or /CFG_SITE_RECORD/2147483649
                return None, []

            format = None
            tab = ''
            try:
                if path[1] in ['', 'files', 'reviews', 'comments', 'usage',
                               'references', 'citations', 'holdings', 'edit',
                               'keywords', 'multiedit', 'merge', 'plots']:
                    tab = path[1]
                elif path[1] == 'export':
                    tab = ''
                    format = path[2]
#                    format = None
#                elif path[1] in output_formats:
#                    tab = ''
#                    format = path[1]
                else:
                    # display page not found for URLs like /CFG_SITE_RECORD/references
                    # for a collection where 'references' tabs is not visible
                    return None, []

            except IndexError:
                # Keep normal url if tabs is not specified
                pass

            #if component == 'record-restricted':
                #return WebInterfaceRecordRestrictedPages(recid, tab, format), path[1:]
            #else:
            return WebInterfaceRecordPages(recid, tab, format), path[1:]
        elif component == 'sslredirect':
            ## Fallback solution for sslredirect special path that should
            ## be rather implemented as an Apache level redirection
            def redirecter(req, form):
                real_url = "http://" + '/'.join(path)
                redirect_to_url(req, real_url)
            return redirecter, []

        return None, []

    def openurl(self, req, form):
        """ OpenURL Handler."""
        argd = wash_urlargd(form, websearch_templates.tmpl_openurl_accepted_args)
        ret_url = websearch_templates.tmpl_openurl2invenio(argd)
        if ret_url:
            return redirect_to_url(req, ret_url)
        else:
            return redirect_to_url(req, CFG_SITE_URL)

    def opensearchdescription(self, req, form):
        """OpenSearch description file"""
        req.content_type = "application/opensearchdescription+xml"
        req.send_http_header()
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'verbose': (int, 0) })
        return websearch_templates.tmpl_opensearch_description(ln=argd['ln'])

    def legacy_collection(self, req, form):
        """Collection URL backward compatibility handling."""
        accepted_args = dict(legacy_collection_default_urlargd)
        argd = wash_urlargd(form, accepted_args)

        # Treat `as' argument specially:
        if argd.has_key('as'):
            argd['aas'] = argd['as']
            del argd['as']

        # If we specify no collection, then we don't need to redirect
        # the user, so that accessing <http://yoursite/> returns the
        # default collection.
        if not form.has_key('c'):
            return display_collection(req, **argd)

        # make the collection an element of the path, and keep the
        # other query elements as is. If the collection is CFG_SITE_NAME,
        # however, redirect to the main URL.
        c = argd['c']
        del argd['c']

        if c == CFG_SITE_NAME:
            target = '/'
        else:
            target = '/collection/' + quote(c)

        # Treat `as' argument specially:
        # We are going to redirect, so replace `aas' by `as' visible argument:
        if argd.has_key('aas'):
            argd['as'] = argd['aas']
            del argd['aas']

        target += make_canonical_urlargd(argd, legacy_collection_default_urlargd)
        return redirect_to_url(req, target)

def display_collection(req, c, aas, verbose, ln):
    """Display search interface page for collection c by looking
    in the collection cache."""
    _ = gettext_set_language(ln)

    req.argd = drop_default_urlargd({'aas': aas, 'verbose': verbose, 'ln': ln},
                                    search_interface_default_urlargd)

    # get user ID:
    try:
        uid = getUid(req)
        user_preferences = {}
        if uid == -1:
            return page_not_authorized(req, "../",
                text="You are not authorized to view this collection",
                                       navmenuid='search')
        elif uid > 0:
            user_preferences = get_user_preferences(uid)
    except Error:
        register_exception(req=req, alert_admin=True)
        return page(title=_("Internal Error"),
                    body=create_error_box(req, verbose=verbose, ln=ln),
                    description="%s - Internal Error" % CFG_SITE_NAME,
                    keywords="%s, Internal Error" % CFG_SITE_NAME,
                    language=ln,
                    req=req,
                    navmenuid='search')
    # start display:
    req.content_type = "text/html"
    req.send_http_header()
    # deduce collection id:
    colID = get_colID(get_coll_normalised_name(c))
    if type(colID) is not int:
        page_body = '<p>' + (_("Sorry, collection %s does not seem to exist.") % ('<strong>' + str(c) + '</strong>')) + '</p>'
        page_body = '<p>' + (_("You may want to start browsing from %s.") % ('<a href="' + CFG_SITE_URL + '?ln=' + ln + '">' + get_coll_i18nname(CFG_SITE_NAME, ln) + '</a>')) + '</p>'
        if req.header_only:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
        return page(title=_("Collection %s Not Found") % cgi.escape(c),
                    body=page_body,
                    description=(CFG_SITE_NAME + ' - ' + _("Not found") + ': ' + cgi.escape(str(c))),
                    keywords="%s" % CFG_SITE_NAME,
                    uid=uid,
                    language=ln,
                    req=req,
                    navmenuid='search')
    # wash `aas' argument:
    if not os.path.exists("%s/collections/%d/body-as=%d-ln=%s.html" % \
                          (CFG_CACHEDIR, colID, aas, ln)):
        # nonexistent `aas' asked for, fall back to Simple Search:
        aas = 0
    # display collection interface page:
    try:
        filedesc = open("%s/collections/%d/navtrail-as=%d-ln=%s.html" % \
                        (CFG_CACHEDIR, colID, aas, ln), "r")
        c_navtrail = filedesc.read()
        filedesc.close()
    except:
        c_navtrail = ""
    try:
        filedesc = open("%s/collections/%d/body-as=%d-ln=%s.html" % \
                        (CFG_CACHEDIR, colID, aas, ln), "r")
        c_body = filedesc.read()
        filedesc.close()
    except:
        c_body = ""
    try:
        filedesc = open("%s/collections/%d/portalbox-tp-ln=%s.html" % \
                        (CFG_CACHEDIR, colID, ln), "r")
        c_portalbox_tp = filedesc.read()
        filedesc.close()
    except:
        c_portalbox_tp = ""
    try:
        filedesc = open("%s/collections/%d/portalbox-te-ln=%s.html" % \
                        (CFG_CACHEDIR, colID, ln), "r")
        c_portalbox_te = filedesc.read()
        filedesc.close()
    except:
        c_portalbox_te = ""
    try:
        filedesc = open("%s/collections/%d/portalbox-lt-ln=%s.html" % \
                        (CFG_CACHEDIR, colID, ln), "r")
        c_portalbox_lt = filedesc.read()
        filedesc.close()
    except:
        c_portalbox_lt = ""
    try:
        # show help boxes (usually located in "tr", "top right")
        # if users have not banned them in their preferences:
        c_portalbox_rt = ""
        if user_preferences.get('websearch_helpbox', 1) > 0:
            filedesc = open("%s/collections/%d/portalbox-rt-ln=%s.html" % \
                            (CFG_CACHEDIR, colID, ln), "r")
            c_portalbox_rt = filedesc.read()
            filedesc.close()
    except:
        c_portalbox_rt = ""
    try:
        filedesc = open("%s/collections/%d/last-updated-ln=%s.html" % \
                        (CFG_CACHEDIR, colID, ln), "r")
        c_last_updated = filedesc.read()
        filedesc.close()
    except:
        c_last_updated = ""
    try:
        title = get_coll_i18nname(c, ln)
    except:
        title = ""

    show_title_p = True
    body_css_classes = []
    if c == CFG_SITE_NAME:
        # Do not display title on home collection
        show_title_p = False
        body_css_classes.append('home')

    if len(collection_reclist_cache.cache.keys()) == 1:
        # if there is only one collection defined, do not print its
        # title on the page as it would be displayed repetitively.
        show_title_p = False

    if aas == -1:
        show_title_p = False

    if CFG_INSPIRE_SITE == 1:
        # INSPIRE should never show title, but instead use css to
        # style collections
        show_title_p = False
        body_css_classes.append(nmtoken_from_string(c))

    # RSS:
    rssurl = CFG_SITE_URL + '/rss'
    rssurl_params = []
    if c != CFG_SITE_NAME:
        rssurl_params.append('cc=' + quote(c))
    if ln != CFG_SITE_LANG and \
           c in CFG_WEBSEARCH_RSS_I18N_COLLECTIONS:
        rssurl_params.append('ln=' + ln)

    if rssurl_params:
        rssurl += '?' + '&amp;'.join(rssurl_params)

    if 'hb' in CFG_WEBSEARCH_USE_MATHJAX_FOR_FORMATS:
        metaheaderadd = get_mathjax_header(req.is_https())
    else:
        metaheaderadd = ''

    return page(title=title,
                body=c_body,
                navtrail=c_navtrail,
                description="%s - %s" % (CFG_SITE_NAME, c),
                keywords="%s, %s" % (CFG_SITE_NAME, c),
                metaheaderadd=metaheaderadd,
                uid=uid,
                language=ln,
                req=req,
                cdspageboxlefttopadd=c_portalbox_lt,
                cdspageboxrighttopadd=c_portalbox_rt,
                titleprologue=c_portalbox_tp,
                titleepilogue=c_portalbox_te,
                lastupdated=c_last_updated,
                navmenuid='search',
                rssurl=rssurl,
                body_css_classes=body_css_classes,
                show_title_p=show_title_p)

class WebInterfaceRSSFeedServicePages(WebInterfaceDirectory):
    """RSS 2.0 feed service pages."""

    def __call__(self, req, form):
        """RSS 2.0 feed service."""

        # Keep only interesting parameters for the search
        default_params = websearch_templates.rss_default_urlargd
        # We need to keep 'jrec' and 'rg' here in order to have
        # 'multi-page' RSS. These parameters are not kept be default
        # as we don't want to consider them when building RSS links
        # from search and browse pages.
        default_params.update({'jrec':(int, 1),
                               'rg': (int, CFG_WEBSEARCH_INSTANT_BROWSE_RSS)})
        argd = wash_urlargd(form, default_params)
        user_info = collect_user_info(req)

        for coll in argd['c'] + [argd['cc']]:
            if collection_restricted_p(coll):
                (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=coll)
                if auth_code and user_info['email'] == 'guest':
                    cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : coll})
                    target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                            make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri}, {})
                    return redirect_to_url(req, target, norobot=True)
                elif auth_code:
                    return page_not_authorized(req, "../", \
                        text=auth_msg, \
                        navmenuid='search')

        # Create a standard filename with these parameters
        current_url = websearch_templates.build_rss_url(argd)
        cache_filename = current_url.split('/')[-1]

        # In the same way as previously, add 'jrec' & 'rg'

        req.content_type = "application/rss+xml"
        req.send_http_header()
        try:
            # Try to read from cache
            path = "%s/rss/%s.xml" % (CFG_CACHEDIR, cache_filename)
            # Check if cache needs refresh
            filedesc = open(path, "r")
            last_update_time = datetime.datetime.fromtimestamp(os.stat(os.path.abspath(path)).st_mtime)
            assert(datetime.datetime.now() < last_update_time + datetime.timedelta(minutes=CFG_WEBSEARCH_RSS_TTL))
            c_rss = filedesc.read()
            filedesc.close()
            req.write(c_rss)
            return
        except Exception, e:
            # do it live and cache

            previous_url = None
            if argd['jrec'] > 1:
                prev_jrec = argd['jrec'] - argd['rg']
                if prev_jrec < 1:
                    prev_jrec = 1
                previous_url = websearch_templates.build_rss_url(argd,
                                                                 jrec=prev_jrec)

            #check if the user has rights to set a high wildcard limit
            #if not, reduce the limit set by user, with the default one
            if CFG_WEBSEARCH_WILDCARD_LIMIT > 0 and (argd['wl'] > CFG_WEBSEARCH_WILDCARD_LIMIT or argd['wl'] == 0):
                if acc_authorize_action(req, 'runbibedit')[0] != 0:
                    argd['wl'] = CFG_WEBSEARCH_WILDCARD_LIMIT

            recIDs = perform_request_search(req, of="id",
                                                          c=argd['c'], cc=argd['cc'],
                                                          p=argd['p'], f=argd['f'],
                                                          p1=argd['p1'], f1=argd['f1'],
                                                          m1=argd['m1'], op1=argd['op1'],
                                                          p2=argd['p2'], f2=argd['f2'],
                                                          m2=argd['m2'], op2=argd['op2'],
                                                          p3=argd['p3'], f3=argd['f3'],
                                                          m3=argd['m3'], wl=argd['wl'])
            nb_found = len(recIDs)
            next_url = None
            if len(recIDs) >= argd['jrec'] + argd['rg']:
                next_url = websearch_templates.build_rss_url(argd,
                                                             jrec=(argd['jrec'] + argd['rg']))

            first_url = websearch_templates.build_rss_url(argd, jrec=1)
            last_url = websearch_templates.build_rss_url(argd, jrec=nb_found - argd['rg'] + 1)

            recIDs = recIDs[-argd['jrec']:(-argd['rg'] - argd['jrec']):-1]

            rss_prologue = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
            websearch_templates.tmpl_xml_rss_prologue(current_url=current_url,
                                                      previous_url=previous_url,
                                                      next_url=next_url,
                                                      first_url=first_url, last_url=last_url,
                                                      nb_found=nb_found,
                                                      jrec=argd['jrec'], rg=argd['rg'],
                                                      cc=argd['cc']) + '\n'
            req.write(rss_prologue)
            rss_body = format_records(recIDs,
                                      of='xr',
                                      ln=argd['ln'],
                                      user_info=user_info,
                                      record_separator="\n",
                                      req=req, epilogue="\n")
            rss_epilogue = websearch_templates.tmpl_xml_rss_epilogue() + '\n'
            req.write(rss_epilogue)

            # update cache
            dirname = "%s/rss" % (CFG_CACHEDIR)
            mymkdir(dirname)
            fullfilename = "%s/rss/%s.xml" % (CFG_CACHEDIR, cache_filename)
            try:
                # Remove the file just in case it already existed
                # so that a bit of space is created
                os.remove(fullfilename)
            except OSError:
                pass

            # Check if there's enough space to cache the request.
            if len(os.listdir(dirname)) < CFG_WEBSEARCH_RSS_MAX_CACHED_REQUESTS:
                try:
                    os.umask(022)
                    f = open(fullfilename, "w")
                    f.write(rss_prologue + rss_body + rss_epilogue)
                    f.close()
                except IOError, v:
                    if v[0] == 36:
                        # URL was too long. Never mind, don't cache
                        pass
                    else:
                        raise repr(v)

    index = __call__


class WebInterfaceRecordExport(WebInterfaceDirectory):
    """ Handling of a /<CFG_SITE_RECORD>/<recid>/export/<format> URL fragment """

    _exports = output_formats

    def __init__(self, recid, format=None):
        self.recid = recid
        self.format = format

        for output_format in output_formats:
            self.__dict__[output_format] = self

        return

    def __call__(self, req, form):
        argd = wash_search_urlargd(form)
        argd['recid'] = self.recid

        if self.format is not None:
            argd['of'] = self.format
        req.argd = argd
        uid = getUid(req)
        if uid == -1:
            return page_not_authorized(req, "../",
                text="You are not authorized to view this record.",
                                       navmenuid='search')
        elif uid > 0:
            pref = get_user_preferences(uid)
            try:
                if not form.has_key('rg'):
                    # fetch user rg preference only if not overridden via URL
                    argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass

        # Check if the record belongs to a restricted primary
        # collection.  If yes, redirect to the authenticated URL.
        user_info = collect_user_info(req)
        (auth_code, auth_msg) = check_user_can_view_record(user_info, self.recid)

        if argd['rg'] > CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS and acc_authorize_action(req, 'runbibedit')[0] != 0:
            argd['rg'] = CFG_WEBSEARCH_MAX_RECORDS_IN_GROUPS

        #check if the user has rights to set a high wildcard limit
        #if not, reduce the limit set by user, with the default one
        if CFG_WEBSEARCH_WILDCARD_LIMIT > 0 and (argd['wl'] > CFG_WEBSEARCH_WILDCARD_LIMIT or argd['wl'] == 0):
            if acc_authorize_action(req, 'runbibedit')[0] != 0:
                argd['wl'] = CFG_WEBSEARCH_WILDCARD_LIMIT

        if auth_code and user_info['email'] == 'guest':
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                    make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_SECURE_URL + req.unparsed_uri}, {})
            return redirect_to_url(req, target, norobot=True)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text=auth_msg, \
                navmenuid='search')

        # mod_python does not like to return [] in case when of=id:
        out = perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    # Return the same page wether we ask for /CFG_SITE_RECORD/123/export/xm or /CFG_SITE_RECORD/123/export/xm/
    index = __call__
