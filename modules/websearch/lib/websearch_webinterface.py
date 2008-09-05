## $Id$
##
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

"""WebSearch URL handler."""

__revision__ = "$Id$"

import cgi
import os
import datetime
from urllib import quote
try:
    from mod_python import apache
except ImportError:
    pass

#maximum number of collaborating authors etc shown in GUI
MAX_COLLAB_LIST = 10
MAX_KEYWORD_LIST = 10
MAX_VENUE_LIST = 10
#tag constants
AUTHOR_TAG = "100__a"
COAUTHOR_TAG = "700__a"
AUTHOR_INST_TAG = "100__u"
VENUE_TAG = "909C4p"
KEYWORD_TAG = "6531_a"

try:
    Set = set
except NameError:
    from sets import Set

from invenio.config import \
     CFG_SITE_URL, \
     CFG_SITE_NAME, \
     CFG_CACHEDIR, \
     CFG_SITE_LANG, \
     CFG_SITE_ADMIN_EMAIL, \
     CFG_SITE_SECURE_URL, \
     CFG_WEBSEARCH_INSTANT_BROWSE_RSS, \
     CFG_WEBSEARCH_RSS_TTL, \
     CFG_WEBSEARCH_RSS_MAX_CACHED_REQUESTS, \
     CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, \
     CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES, \
     CFG_WEBDIR, \
     CFG_WEBSEARCH_USE_JSMATH_FOR_FORMATS
from invenio.dbquery import Error
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import redirect_to_url, make_canonical_urlargd, drop_default_urlargd, create_html_link
from invenio.webuser import getUid, page_not_authorized, get_user_preferences, \
    collect_user_info, http_check_credentials, logoutUser
from invenio import search_engine
from invenio.websubmit_webinterface import WebInterfaceFilesPages
from invenio.webcomment_webinterface import WebInterfaceCommentsPages
from invenio.bibcirculation_webinterface import WebInterfaceHoldingsPages
from invenio.webpage import page, create_error_box
from invenio.messages import gettext_set_language
from invenio.search_engine import get_colID, get_coll_i18nname, \
    check_user_can_view_record, collection_restricted_p, restricted_collection_cache, \
    get_fieldvalues
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_config import VIEWRESTRCOLL
from invenio.access_control_mailcookie import mail_cookie_create_authorize_action
from invenio.bibformat import format_records
from invenio.bibformat_engine import get_output_formats
from invenio.websearch_webcoll import mymkdir, get_collection
from invenio.intbitset import intbitset
from invenio.bibupload import find_record_from_sysno
from invenio.bibrank_citation_searcher import get_author_cited_by, get_cited_by_list
from invenio.bibrank_downloads_indexer import get_download_weight_total
from invenio.search_engine_summarizer import summarize_records

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


class WebInterfaceAuthorPages(WebInterfaceDirectory):
    """ Handle /author/Doe%2C+John etc set of pages."""

    _exports = ['author']

    def __init__(self, authorname=''):
        """Constructor."""
        self.authorname = authorname

    def _lookup(self, component, path):
        """This handler parses dynamic URLs (/author/John+Doe)."""
        return WebInterfaceAuthorPages(component), path


    def __call__(self, req, form):
        """Serve the page in the given language."""
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG)})
        ln = argd['ln']
        req.argd = argd #needed since perform_req_search

        # start page
        req.content_type = "text/html"
        req.send_http_header()
        uid = getUid(req)

        search_engine.page_start(req, "hb", "", "", ln, uid)

        #wants to check it in case of no results
        self.authorname = self.authorname.replace("+"," ")

        if not self.authorname:
            return websearch_templates.tmpl_author_information(req, {}, self.authorname,
                                                               0, {},
                                                               {}, {}, {}, {}, ln)

        citelist = get_author_cited_by(self.authorname)
        #search the publications by this author
        pubs = search_engine.perform_request_search(req=req, p=self.authorname, f="author")
        #get most frequent first authors of these pubs
        authors = [authorfreq[0] for authorfreq in search_engine.get_most_popular_field_values(pubs, (AUTHOR_TAG, COAUTHOR_TAG))]
        #and publication venues
        venuedict =  search_engine.get_values_for_code_dict(pubs, VENUE_TAG)
        #and keywords
        kwdict = search_engine.get_values_for_code_dict(pubs, KEYWORD_TAG)

        #construct a simple list of tuples that contains keywords that appear more than once
        #moreover, limit the length of the list to MAX_KEYWORD_LIST
        kwtuples = []
        for k in kwdict.keys():
            if kwdict[k] > 1:
                mytuple = (kwdict[k], k)
                kwtuples.append(mytuple)
        #sort ..
        kwtuples.sort()
        kwtuples.reverse()
        kwtuples = kwtuples[0:MAX_KEYWORD_LIST]

        #same for venues
        vtuples = []

        for k in venuedict.keys():
            if venuedict[k] > 1:
                mytuple = (venuedict[k], k)
                vtuples.append(mytuple)
        #sort ..
        vtuples.sort()
        vtuples.reverse()
        vtuples = vtuples[0:MAX_VENUE_LIST]

        #remove the author in question from authors: they are associates
        if (authors.count(self.authorname) > 0):
            authors.remove(self.authorname)

        authors = authors[0:MAX_COLLAB_LIST] #cut extra

        #a dict. keys: affiliations, values: lists of publications
        author_aff_pubs = self.get_institute_pub_dict(pubs)
        authoraffs = author_aff_pubs.keys()

        #find out how many times these records have been downloaded
        recsloads = {}
        recsloads = get_download_weight_total(recsloads, pubs)
        #sum up
        totaldownloads = 0
        for k in recsloads.keys():
            totaldownloads = totaldownloads + recsloads[k]

        #get cited by..
        citedbylist = get_cited_by_list(pubs)
        #finally all stuff there, call the template
        websearch_templates.tmpl_author_information(req, pubs, self.authorname,
                                                    totaldownloads, author_aff_pubs,
                                                    citedbylist, kwtuples, authors, vtuples, ln)

        #cited-by summary
        out = summarize_records(intbitset(pubs), 'hcs', ln, self.authorname, 'author', req)
        req.write(out)

        simauthbox = search_engine.create_similarly_named_authors_link_box(self.authorname)
        req.write(simauthbox)

        return search_engine.page_end(req, 'hb', ln)

    def get_institute_pub_dict(self, recids):
        #return a dictionary consisting of institute -> list of publications
        affus = [] #list of insts from the record
        author_aff_pubs = {} #the disct to be build
        for recid in recids:
            #iterate all so that we get first author's intitute
            #if this the first author OR
            #"his" institute if he is an affliate author
            mainauthors = get_fieldvalues(recid, AUTHOR_TAG)
            mainauthor = " "
            if mainauthors:
                mainauthor = mainauthors[0]
            if (mainauthor == self.authorname):
                affus = get_fieldvalues(recid, AUTHOR_INST_TAG)
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
    """ Handling of a /record/<recid> URL fragment """

    _exports = ['', 'files', 'reviews', 'comments', 'usage',
                'references', 'export', 'citations', 'holdings']

    #_exports.extend(output_formats)

    def __init__(self, recid, tab, format=None):
        self.recid = recid
        self.tab = tab
        self.format = format

        self.export = self
        self.files = WebInterfaceFilesPages(self.recid)
        self.reviews = WebInterfaceCommentsPages(self.recid, reviews=1)
        self.comments = WebInterfaceCommentsPages(self.recid)
        self.usage = self
        self.references = self
        self.holdings = WebInterfaceHoldingsPages(self.recid)
        self.citations = self
        self.export = WebInterfaceRecordExport(self.recid, self.format)

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

        if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : search_engine.guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                    make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_URL + req.unparsed_uri}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg,\
                navmenuid='search')

        # mod_python does not like to return [] in case when of=id:
        out = search_engine.perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    # Return the same page wether we ask for /record/123 or /record/123/
    index = __call__

class WebInterfaceRecordRestrictedPages(WebInterfaceDirectory):
    """ Handling of a /record-restricted/<recid> URL fragment """

    _exports = ['', 'files', 'reviews', 'comments', 'usage',
                'references', 'export', 'citations', 'holdings']

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
        self.holdings = WebInterfaceHoldingsPages(self.recid)
        self.citations = self
        self.export = WebInterfaceRecordExport(self.recid, self.format)

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

        record_primary_collection = search_engine.guess_primary_collection_of_a_record(self.recid)

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
        out = search_engine.perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    # Return the same page wether we ask for /record/123 or /record/123/
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
                text = _("You are not authorized to view this area."),
                                       navmenuid='search')
        elif uid > 0:
            pref = get_user_preferences(uid)
            try:
                if not form.has_key('rg'):
                    # fetch user rg preference only if not overridden via URL
                    argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass

        involved_collections = Set()
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
                restricted_colls = restricted_collection_cache.get_cache()
                for collname in restricted_colls:
                    (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=collname)
                    if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
                        coll_recids = get_collection(collname).reclist
                        if coll_recids & recids:
                            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : collname})
                            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                                    make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_URL + req.unparsed_uri}, {})
                            return redirect_to_url(req, target)
                    elif auth_code:
                        return page_not_authorized(req, "../", \
                            text = auth_msg,\
                            navmenuid='search')
            else:
                involved_collections.add(search_engine.guess_primary_collection_of_a_record(argd['recid']))

        # If any of the collection requires authentication, redirect
        # to the authentication form.
        for coll in involved_collections:
            if collection_restricted_p(coll):
                (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=coll)
                if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
                    cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : coll})
                    target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                            make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_URL + req.unparsed_uri}, {})
                    return redirect_to_url(req, target)
                elif auth_code:
                    return page_not_authorized(req, "../", \
                        text = auth_msg,\
                        navmenuid='search')

        # Keep all the arguments, they might be reused in the
        # search_engine itself to derivate other queries
        req.argd = argd

        # mod_python does not like to return [] in case when of=id:
        out = search_engine.perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    def cache(self, req, form):
        """Search cache page."""
        argd = wash_urlargd(form, {'action': (str, 'show')})
        return search_engine.perform_request_cache(req, action=argd['action'])

    def log(self, req, form):
        """Search log page."""
        argd = wash_urlargd(form, {'date': (str, '')})
        return search_engine.perform_request_log(req, date=argd['date'])

    def authenticate(self, req, form):
        """Restricted search results pages."""

        argd = wash_search_urlargd(form)

        user_info = collect_user_info(req)
        for coll in argd['c'] + [argd['cc']]:
            if collection_restricted_p(coll):
                (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=coll)
                if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
                    cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : coll})
                    target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                            make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_URL + req.unparsed_uri}, {})
                    return redirect_to_url(req, target)
                elif auth_code:
                    return page_not_authorized(req, "../", \
                        text = auth_msg,\
                        navmenuid='search')

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
        out = search_engine.perform_request_search(req, **argd)
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
        # /record/... display if a recid is requested
        if argd['recid'] != -1:
            target = '/record/%d' % argd['recid']
            del argd['recid']

        else:
            target = '/search'

        target += make_canonical_urlargd(argd, search_results_default_urlargd)
        return redirect_to_url(req, target, apache.HTTP_MOVED_PERMANENTLY)

    index = __call__


# Parameters for the legacy URLs, of the form /?c=ALEPH
legacy_collection_default_urlargd = {
    'as': (int, CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE),
    'verbose': (int, 0),
    'c': (str, CFG_SITE_NAME)}

class WebInterfaceSearchInterfacePages(WebInterfaceDirectory):

    """ Handling of collection navigation."""

    _exports = [('index.py', 'legacy_collection'),
                ('', 'legacy_collection'),
                ('search.py', 'legacy_search'),
                'search', 'openurl', 'testsso',
                'logout_SSO_hook']

    search = WebInterfaceSearchResultsPages()
    legacy_search = WebInterfaceLegacySearchPages()

    def testsso(self, req, form):
        """ For testing single sign-on """
        req.add_common_vars()
        sso_env = {}
        for var, value in req.subprocess_env.iteritems():
            if var.startswith('HTTP_ADFS_'):
                sso_env[var] = value
        out = "<HTML><HEAD><TITLE>SSO test</TITLE</HEAD>"
        out += "<BODY><TABLE>"
        for var, value in sso_env.iteritems():
            out += "<TR><TD><STRONG>%s</STRONG></TD><TD>%s</TD></TR>" % (var, value)
        out += "</TABLE></BODY></HTML>"
        return out

    def logout_SSO_hook(self, req, form):
        """Script triggered by the display of the centralized SSO logout
        dialog. It logouts the user from CDS Invenio and stream back the
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
                return display_collection(req, **argd)

            return answer, []


        elif component == 'record' or component == 'record-restricted':
            try:
                recid = int(path[0])
            except IndexError:
                # display record #1 for URL /record without a number
                recid = 1
            except ValueError:
                if path[0] == '':
                    # display record #1 for URL /record/ without a number
                    recid = 1
                else:
                    # display page not found for URLs like /record/foo
                    return None, []

            if recid <= 0:
                # display page not found for URLs like /record/-5 or /record/0
                return None, []

            format = None
            tab = ''
            try:
                if path[1] in ['', 'files', 'reviews', 'comments',
                               'usage', 'references', 'citations', 'holdings']:
                    tab = path[1]
                elif path[1] == 'export':
                    tab = ''
                    format = path[2]
#                    format = None
#                elif path[1] in output_formats:
#                    tab = ''
#                    format = path[1]
                else:
                    # display page not found for URLs like /record/references
                    # for a collection where 'references' tabs is not visible
                    return None, []

            except IndexError:
                # Keep normal url if tabs is not specified
                pass

            #if component == 'record-restricted':
                #return WebInterfaceRecordRestrictedPages(recid, tab, format), path[1:]
            #else:
            return WebInterfaceRecordPages(recid, tab, format), path[1:]

        return None, []

    def openurl(self, req, form):
        """ OpenURL Handler."""
        argd = wash_urlargd(form, websearch_templates.tmpl_openurl_accepted_args)
        ret_url = websearch_templates.tmpl_openurl2invenio(argd)
        if ret_url:
            return redirect_to_url(req, ret_url)
        else:
            return redirect_to_url(req, CFG_SITE_URL)

    def legacy_collection(self, req, form):
        """Collection URL backward compatibility handling."""
        accepted_args = dict(legacy_collection_default_urlargd)
        accepted_args.update({'referer' : (str, ''),
             'realm' : (str, '')})
        argd = wash_urlargd(form, accepted_args)

        # Apache authentication stuff
        if argd['realm']:
            http_check_credentials(req, argd['realm'])
            return redirect_to_url(req, argd['referer'] or '%s/youraccount/youradminactivities' % CFG_SITE_SECURE_URL)

        del argd['referer']
        del argd['realm']

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

        target += make_canonical_urlargd(argd, legacy_collection_default_urlargd)
        return redirect_to_url(req, target)

def display_collection(req, c, as, verbose, ln):
    """Display search interface page for collection c by looking
    in the collection cache."""
    _ = gettext_set_language(ln)

    req.argd = drop_default_urlargd({'as': as, 'verbose': verbose, 'ln': ln},
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
        return page(title=_("Internal Error"),
                    body = create_error_box(req, verbose=verbose, ln=ln),
                    description="%s - Internal Error" % CFG_SITE_NAME,
                    keywords="%s, Internal Error" % CFG_SITE_NAME,
                    language=ln,
                    req=req,
                    navmenuid='search')
    # start display:
    req.content_type = "text/html"
    req.send_http_header()
    # deduce collection id:
    colID = get_colID(c)
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
    # display collection interface page:
    try:
        filedesc = open("%s/collections/%d/navtrail-as=%d-ln=%s.html" % (CFG_CACHEDIR, colID, as, ln), "r")
        c_navtrail = filedesc.read()
        filedesc.close()
        filedesc = open("%s/collections/%d/body-as=%d-ln=%s.html" % (CFG_CACHEDIR, colID, as, ln), "r")
        c_body = filedesc.read()
        filedesc.close()
        filedesc = open("%s/collections/%d/portalbox-tp-ln=%s.html" % (CFG_CACHEDIR, colID, ln), "r")
        c_portalbox_tp = filedesc.read()
        filedesc.close()
        filedesc = open("%s/collections/%d/portalbox-te-ln=%s.html" % (CFG_CACHEDIR, colID, ln), "r")
        c_portalbox_te = filedesc.read()
        filedesc.close()
        filedesc = open("%s/collections/%d/portalbox-lt-ln=%s.html" % (CFG_CACHEDIR, colID, ln), "r")
        c_portalbox_lt = filedesc.read()
        filedesc.close()
        # show help boxes (usually located in "tr", "top right")
        # if users have not banned them in their preferences:
        c_portalbox_rt = ""
        if user_preferences.get('websearch_helpbox', 1) > 0:
            filedesc = open("%s/collections/%d/portalbox-rt-ln=%s.html" % (CFG_CACHEDIR, colID, ln), "r")
            c_portalbox_rt = filedesc.read()
            filedesc.close()
        filedesc = open("%s/collections/%d/last-updated-ln=%s.html" % (CFG_CACHEDIR, colID, ln), "r")
        c_last_updated = filedesc.read()
        filedesc.close()

        title = get_coll_i18nname(c, ln)
        # if there is only one collection defined, do not print its
        # title on the page as it would be displayed repetitively.
        if len(search_engine.collection_reclist_cache.keys()) == 1:
            title = ""

        rssurl = CFG_SITE_URL + '/rss'
        if c != CFG_SITE_NAME:
            rssurl += '?cc=' + quote(c)

        if 'hb' in CFG_WEBSEARCH_USE_JSMATH_FOR_FORMATS:
            metaheaderadd = """
  <script type='text/javascript'>
    jsMath = {
        Controls: {cookie: {printwarn: 0}}
    };
  </script>
  <script src='/jsMath/easy/invenio-jsmath.js' type='text/javascript'></script>
"""
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
                    show_title_p=-1 not in CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES)
    except:
        if verbose >= 9:
            req.write("<br />c=%s" % c)
            req.write("<br />as=%s" % as)
            req.write("<br />ln=%s" % ln)
            req.write("<br />colID=%s" % colID)
            req.write("<br />uid=%s" % uid)
        return page(title=_("Internal Error"),
                    body = create_error_box(req, ln=ln),
                    description="%s - Internal Error" % CFG_SITE_NAME,
                    keywords="%s, Internal Error" % CFG_SITE_NAME,
                    uid=uid,
                    language=ln,
                    req=req,
                    navmenuid='search')

    return "\n"

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

        for coll in argd['c'] + [argd['cc']]:
            if collection_restricted_p(coll):
                user_info = collect_user_info(req)
                (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=coll)
                if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
                    cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : coll})
                    target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                            make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_URL + req.unparsed_uri}, {})
                    return redirect_to_url(req, target)
                elif auth_code:
                    return page_not_authorized(req, "../", \
                        text = auth_msg,\
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

            recIDs = search_engine.perform_request_search(req, of="id",
                                                          c=argd['c'], cc=argd['cc'],
                                                          p=argd['p'], f=argd['f'],
                                                          p1=argd['p1'], f1=argd['f1'],
                                                          m1=argd['m1'], op1=argd['op1'],
                                                          p2=argd['p2'], f2=argd['f2'],
                                                          m2=argd['m2'], op2=argd['op2'],
                                                          p3=argd['p3'], f3=argd['f3'],
                                                          m3=argd['m3'])
            next_url = None
            if len(recIDs) >= argd['jrec'] + argd['rg']:
                next_url = websearch_templates.build_rss_url(argd,
                                                             jrec=(argd['jrec'] + argd['rg']))

            recIDs = recIDs[-argd['jrec']:(-argd['rg']-argd['jrec']):-1]

            rss_prologue = '<?xml version="1.0" encoding="UTF-8"?>\n' + \
            websearch_templates.tmpl_xml_rss_prologue(current_url=current_url,
                                                      previous_url=previous_url,
                                                      next_url=next_url) + '\n'
            req.write(rss_prologue)
            rss_body = format_records(recIDs,
                                      of='xr',
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
    """ Handling of a /record/<recid>/export/<format> URL fragment """

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
        if auth_code and user_info['email'] == 'guest' and not user_info['apache_user']:
            cookie = mail_cookie_create_authorize_action(VIEWRESTRCOLL, {'collection' : search_engine.guess_primary_collection_of_a_record(self.recid)})
            target = CFG_SITE_SECURE_URL + '/youraccount/login' + \
                    make_canonical_urlargd({'action': cookie, 'ln' : argd['ln'], 'referer' : CFG_SITE_URL + req.unparsed_uri}, {})
            return redirect_to_url(req, target)
        elif auth_code:
            return page_not_authorized(req, "../", \
                text = auth_msg,\
                navmenuid='search')

        # mod_python does not like to return [] in case when of=id:
        out = search_engine.perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    # Return the same page wether we ask for /record/123/export/xm or /record/123/export/xm/
    index = __call__
