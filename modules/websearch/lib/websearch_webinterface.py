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

"""WebSearch URL handler."""

__revision__ = "$Id$"

import cgi
from urllib import quote
from mod_python import apache

from invenio.config import weburl, cdsname, cachedir, cdsnameintl, cdslang, adminemail, sweburl
from invenio.dbquery import Error
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory, \
    http_check_credentials, http_get_credentials
from invenio.urlutils import redirect_to_url, make_canonical_urlargd, drop_default_urlargd
from invenio.webuser import getUid, page_not_authorized, get_user_preferences, \
    collect_user_info, auth_apache_user_p, auth_apache_user_in_groups, setApacheUser
from invenio import search_engine
from invenio.websubmit_webinterface import WebInterfaceFilesPages
from invenio.webcomment_webinterface import WebInterfaceCommentsPages
from invenio.webpage import page, create_error_box
from invenio.messages import gettext_set_language
from invenio.search_engine import get_colID, get_coll_i18nname, collection_restricted_p
from invenio.access_control_engine import acc_authorize_action
from invenio.access_control_config import VIEWRESTRCOLL

import invenio.template
websearch_templates = invenio.template.load('websearch')

search_results_default_urlargd = websearch_templates.search_results_default_urlargd
search_interface_default_urlargd = websearch_templates.search_interface_default_urlargd
output_formats = ['xm', 'xd', 'hm', 'hx', 'hd', 'hb', 'xe', 'xn']

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

class WebInterfaceRecordPages(WebInterfaceDirectory):
    """ Handling of a /record/<recid> URL fragment """

    _exports = ['', 'files', 'reviews', 'comments', 'statistics', 'references', 'export']

    #_exports.extend(output_formats)

    def __init__(self, recid, tab, format=None):
        self.recid = recid
        self.tab = tab
        self.format = format

        self.export = self
        self.files = WebInterfaceFilesPages(self.recid)
        self.reviews = WebInterfaceCommentsPages(self.recid, reviews=1)
        self.comments = WebInterfaceCommentsPages(self.recid)
        self.statistics = self
        self.references = self
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
                argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass

        # Check if the record belongs to a restricted primary
        # collection.  If yes, redirect to the authenticated URL.
        record_primary_collection = search_engine.guess_primary_collection_of_a_record(self.recid)
        if collection_restricted_p(record_primary_collection):
            user_info = collect_user_info(req)
            (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=record_primary_collection)
            if auth_code and user_info['email'] == 'guest':
                target = '/youraccount/login' + \
                        make_canonical_urlargd({'action': VIEWRESTRCOLL, 'ln' : argd['ln'], 'referer' : \
                        weburl + '/record/' + str(self.recid) + make_canonical_urlargd(argd, \
                        search_results_default_urlargd)}, {'ln' : cdslang})
                return redirect_to_url(req, target)
            elif auth_code:
                return page_not_authorized(req, "../", \
                    text = auth_msg,\
                    navmenuid='search')

            #del argd['recid'] # not wanted argument for detailed record page
            #target = '/record-restricted/' + str(self.recid) + '/' + \
                     #make_canonical_urlargd(argd, search_results_default_urlargd)
            #return redirect_to_url(req, target)

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

    _exports = ['', 'files', 'reviews', 'comments', 'statistics', 'references', 'export']

    #_exports.extend(output_formats)

    def __init__(self, recid, tab, format=None):
        self.recid = recid
        self.tab = tab
        self.format = format

        self.files = WebInterfaceFilesPages(self.recid)
        self.reviews = WebInterfaceCommentsPages(self.recid, reviews=1)
        self.comments = WebInterfaceCommentsPages(self.recid)
        self.statistics = self
        self.references = self
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
                argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass

        # If any of the collection requires authentication, redirect
        # to the authentication form.
        for coll in argd['c'] + [argd['cc']]:
            if collection_restricted_p(coll):
                (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=coll)
                if auth_code and user_info['email'] == 'guest':
                    target = '/youraccount/login' + \
                    make_canonical_urlargd({'action' : VIEWRESTRCOLL, 'ln' : argd['ln'], 'referer' : \
                    weburl + '/search' + make_canonical_urlargd(argd, \
                    search_results_default_urlargd)}, {'ln' : cdslang})
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
                (auth_code, dummy) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=coll)
                if auth_code:
                    return page_not_authorized(req, "../",
                        text="You are not authorized to view this collection.",
                        navmenuid='search')

        # Keep all the arguments, they might be reused in the
        # search_engine itself to derivate other queries
        req.argd = argd

        uid = getUid(req)
        if uid > 0:
            pref = get_user_preferences(uid)
            try:
                argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass


        # mod_python does not like to return [] in case when of=id:
        out = search_engine.perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

# Parameters for the legacy URLs, of the form /?c=ALEPH
legacy_collection_default_urlargd = {
    'as': (int, 0),
    'verbose': (int, 0),
    'c': (str, cdsname)}

class WebInterfaceSearchInterfacePages(WebInterfaceDirectory):

    """ Handling of collection navigation."""

    _exports = [('index.py', 'legacy_collection'),
                ('', 'legacy_collection'),
                ('search.py', 'legacy_search'),
                'search', 'openurl']

    search = WebInterfaceSearchResultsPages()

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
                    argd['c'] = cdsname

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
                if path[1] in ['', 'files', 'reviews', 'comments', 'statistics', 'references']:
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

            if component == 'record-restricted':
                return WebInterfaceRecordRestrictedPages(recid, tab, format), path[1:]
            else:
                return WebInterfaceRecordPages(recid, tab, format), path[1:]

        return None, []

    def _apache_authentication(self, req, referer, realm):
        http_check_credentials(req, realm, auth_apache_user_p)
        (user, passwd) = http_get_credentials(req, realm)
        setApacheUser(req, user)
        return redirect_to_url(req, referer or '%s/youraccount/youradminactivities' % sweburl)

    def openurl(self, req, form):
        pass
        #openurl_journal_accepted_args = {
            #'url_ver' : (str, ''),
            #'ctx_ver' : (str, ''),
            #'rft_val_fmt' : (str, 'info:ofi/fmt:kev:mtx:journal'),
            #'rfr_id' : (str, ''),
            #'rft.atitle' : (str, ''),
            #'rft.title' : (str, ''),
            #'rft.jtitle' : (str, ''),
            #'rft.date' : (str, ''),
            #'rft.volume' : (str, ''),
            #'rft.issue' : (str, ''),
            #'rft.spage' : (str, ''),
            #'rft.epage' : (str, ''),
            #'rft.pages' : (str, ''),
            #'rft.artnumber' : (str, ''),
            #'rft.issn' : (str, ''),
            #'rft.eissn' : (str, ''),
            #'rft.aulast' : (str, ''),
            #'rft.aufirst' : (str, ''),
            #'rft.auinit' : (str, ''),
            #'rft.auinit1' : (str, ''),
            #'rft.auinitm' : (str, ''),
            #'rft.ausuffix' : (str, ''),
            #'rft.au' : (str, ''),
            #'rft.aucorp' : (str, ''),
            #'rft.isbn' : (str, ''),
            #'rft.coden' : (str, ''),
            #'rft.sici' : (str, ''),
            #'rft.genre' : (str, 'unknown'),
            #'rft.chron' : (str, ''),
            #'rft.ssn' : (str, ''),
            #'rft.quarter' : (int, ''),
            #'rft.part' : (str, ''),
        #argd_journal = wash_search_urlargd(form, openurl_accepted_args)
        #if argd_journal['url_ver'] == 'Z39.88-2004' and \
           #argd_journal['ctx_ver'] == 'Z39.88-2004' and \
           #argd_journal['rft_val_fmt'] == 'nfo:ofi/fmt:kev:mtx:journal':
            #pass


    def legacy_collection(self, req, form):
        """Collection URL backward compatibility handling."""
        accepted_args = dict(legacy_collection_default_urlargd)
        accepted_args.update({'referer' : (str, '%s/youraccount/your'),
             'realm' : (str, '')})
        argd = wash_urlargd(form, accepted_args)

        # Apache authentication stuff
        if argd['realm']:
            return self._apache_authentication(req, argd['referer'], argd['realm'])

        del argd['referer']
        del argd['realm']

        # If we specify no collection, then we don't need to redirect
        # the user, so that accessing <http://yoursite/> returns the
        # default collection.
        if not form.has_key('c'):
            return display_collection(req, **argd)

        # make the collection an element of the path, and keep the
        # other query elements as is. If the collection is cdsname,
        # however, redirect to the main URL.
        c = argd['c']
        del argd['c']

        if c == cdsname:
            target = '/'
        else:
            target = '/collection/' + quote(c)

        target += make_canonical_urlargd(argd, legacy_collection_default_urlargd)
        return redirect_to_url(req, target)


    def legacy_search(self, req, form):
        """Search URL backward compatibility handling."""
        argd = wash_search_urlargd(form)

        # We either jump into the generic search form, or the specific
        # /record/... display if a recid is requested
        if argd['recid'] != -1:
            target = '/record/%d' % argd['recid']
            del argd['recid']

        else:
            target = '/search'

        target += make_canonical_urlargd(argd, search_results_default_urlargd)
        return redirect_to_url(req, target)


def display_collection(req, c, as, verbose, ln):
    "Display search interface page for collection c by looking in the collection cache."

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
                    description="%s - Internal Error" % cdsname,
                    keywords="%s, Internal Error" % cdsname,
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
        page_body = '<p>' + (_("You may want to start browsing from %s.") % ('<a href="' + weburl + '?ln=' + ln + '">' + cdsnameintl.get(ln, cdsname) + '</a>')) + '</p>'
        return page(title=_("Collection %s Not Found") % cgi.escape(c),
                    body=page_body,
                    description=(cdsname + ' - ' + _("Not found") + ': ' + cgi.escape(str(c))),
                    keywords="%s" % cdsname,
                    uid=uid,
                    language=ln,
                    req=req,
                    navmenuid='search')
    # display collection interface page:
    try:
        filedesc = open("%s/collections/%d/navtrail-as=%d-ln=%s.html" % (cachedir, colID, as, ln), "r")
        c_navtrail = filedesc.read()
        filedesc.close()
        filedesc = open("%s/collections/%d/body-as=%d-ln=%s.html" % (cachedir, colID, as, ln), "r")
        c_body = filedesc.read()
        filedesc.close()
        filedesc = open("%s/collections/%d/portalbox-tp-ln=%s.html" % (cachedir, colID, ln), "r")
        c_portalbox_tp = filedesc.read()
        filedesc.close()
        filedesc = open("%s/collections/%d/portalbox-te-ln=%s.html" % (cachedir, colID, ln), "r")
        c_portalbox_te = filedesc.read()
        filedesc.close()
        filedesc = open("%s/collections/%d/portalbox-lt-ln=%s.html" % (cachedir, colID, ln), "r")
        c_portalbox_lt = filedesc.read()
        filedesc.close()
        # show help boxes (usually located in "tr", "top right")
        # if users have not banned them in their preferences:
        c_portalbox_rt = ""
        if user_preferences.get('websearch_helpbox', 1) > 0:
            filedesc = open("%s/collections/%d/portalbox-rt-ln=%s.html" % (cachedir, colID, ln), "r")
            c_portalbox_rt = filedesc.read()
            filedesc.close()
        filedesc = open("%s/collections/%d/last-updated-ln=%s.html" % (cachedir, colID, ln), "r")
        c_last_updated = filedesc.read()
        filedesc.close()
        if c == cdsname:
            title = cdsnameintl.get(ln, cdsname)
        else:
            title = get_coll_i18nname(c, ln)

        return page(title=title,
                    body=c_body,
                    navtrail=c_navtrail,
                    description="%s - %s" % (cdsname, c),
                    keywords="%s, %s" % (cdsname, c),
                    uid=uid,
                    language=ln,
                    req=req,
                    cdspageboxlefttopadd=c_portalbox_lt,
                    cdspageboxrighttopadd=c_portalbox_rt,
                    titleprologue=c_portalbox_tp,
                    titleepilogue=c_portalbox_te,
                    lastupdated=c_last_updated,
                    navmenuid='search')
    except:
        if verbose >= 9:
            req.write("<br>c=%s" % c)
            req.write("<br>as=%s" % as)
            req.write("<br>ln=%s" % ln)
            req.write("<br>colID=%s" % colID)
            req.write("<br>uid=%s" % uid)
        return page(title=_("Internal Error"),
                    body = create_error_box(req, ln=ln),
                    description="%s - Internal Error" % cdsname,
                    keywords="%s, Internal Error" % cdsname,
                    uid=uid,
                    language=ln,
                    req=req,
                    navmenuid='search')

    return "\n"

class WebInterfaceRSSFeedServicePages(WebInterfaceDirectory):
    """RSS 2.0 feed service pages."""

    def __call__(self, req, form):
        """RSS 2.0 feed service."""
        # FIXME: currently searching live, should put cache in place via webcoll
        return search_engine.perform_request_search(req, of="xr")

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
                argd['rg'] = int(pref['websearch_group_records'])
            except (KeyError, ValueError):
                pass

        # Check if the record belongs to a restricted primary
        # collection.  If yes, redirect to the authenticated URL.
        record_primary_collection = search_engine.guess_primary_collection_of_a_record(self.recid)
        if collection_restricted_p(record_primary_collection):
            user_info = collect_user_info(req)
            (auth_code, auth_msg) = acc_authorize_action(user_info, VIEWRESTRCOLL, collection=record_primary_collection)
            if auth_code and user_info['email'] == 'guest':
                target = '/youraccount/login' + \
                        make_canonical_urlargd({'action': VIEWRESTRCOLL, 'ln' : argd['ln'], 'referer' : \
                        weburl + '/record/' + str(self.recid) + make_canonical_urlargd(argd, \
                        search_results_default_urlargd)}, {'ln' : cdslang})
                return redirect_to_url(req, target)
            elif auth_code:
                return page_not_authorized(req, "../", \
                    text = auth_msg,\
                    navmenuid='search')

            #del argd['recid'] # not wanted argument for detailed record page
            #target = '/record-restricted/' + str(self.recid) + '/' + \
                     #make_canonical_urlargd(argd, search_results_default_urlargd)
            #return redirect_to_url(req, target)

        # mod_python does not like to return [] in case when of=id:
        out = search_engine.perform_request_search(req, **argd)
        if out == []:
            return str(out)
        else:
            return out

    # Return the same page wether we ask for /record/123/export/xm or /record/123/export/xm/
    index = __call__
