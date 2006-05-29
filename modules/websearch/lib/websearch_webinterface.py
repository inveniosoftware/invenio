## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

import sys
import sre
import MySQLdb

from urllib import quote

from invenio.config import weburl, cdsname, cdslang, cachedir, cdsnameintl
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory, http_check_credentials
from invenio.urlutils import redirect_to_url, make_canonical_urlargd, drop_default_urlargd
from invenio.webuser import getUid, page_not_authorized
from invenio import search_engine

import invenio.template
websearch_templates = invenio.template.load('websearch')

search_results_default_urlargd = websearch_templates.search_results_default_urlargd


def wash_search_urlargd(form):
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


class WebInterfaceSearchResultsPages(WebInterfaceDirectory):
    """ Handling of the /search URL and its sub-pages. """

    _exports = ['', 'authenticate', 'cache', 'log']

    def __call__(self, req, form):
        """ Perform a search. """
        argd = wash_search_urlargd(form)

        uid = getUid(req)
        if uid == -1: 
            return page_not_authorized(req, "../search")

        # If any of the collection requires authentication, redirect
        # to the authentication form.
        for coll in argd['c'] + [argd['cc']]:
            if search_engine.coll_restricted_p(coll):
                target = '/search/authenticate' + \
                         make_canonical_urlargd(argd, search_results_default_urlargd)
                return redirect_to_url(req, target)

        # Keep all the arguments, they might be reused in the
        # search_engine itself to derivate other queries
        req.argd = argd
        
        return search_engine.perform_request_search(req, **argd) 

        
    def cache(self, req, form):
        args = wash_urlargd(form, {'action': (str, 'show')})
        return search_engine.perform_request_cache(req, action=args['action'])
    
    def log(self, req, form):
        args = wash_urlargd(form, {'date': (str, '')})
        return search_engine.perform_request_log(req, date=args['date'])


    def authenticate(self, req, form):
        argd = wash_search_urlargd(form)

        def check_credentials(user, password):
            from invenio.webuser import auth_apache_user_collection_p
            
            for coll in argd['c'] + [argd['cc']]:
                if not auth_apache_user_collection_p(user, password, coll):
                    return False
            return True

        # this function only returns if the credentials are valid
        http_check_credentials(req, "restricted collection", check_credentials)

        # Keep all the arguments, they might be reused in the
        # search_engine itself to derivate other queries
        req.argd = argd

        return search_engine.perform_request_search(req, **argd) 
        
        

# Parameters for the legacy URLs, of the form /?c=ALEPH
legacy_collection_default_urlargd = {
    'as': (int, 0),
    'verbose': (int, 0),
    'c': (str, cdsname)}


search_interface_default_urlargd = {
    'as': (int, 0),
    'jrec': (int, 0),
    'verbose': (int, 0)}


class WebInterfaceSearchInterfacePages(WebInterfaceDirectory):

    """ Handling of collection navigation."""

    _exports = [('index.py', 'legacy_collection'),
                ('', 'legacy_collection'),
                ('search.py', 'legacy_search'),
                'search']

    search = WebInterfaceSearchResultsPages()

    def _lookup(self, component, path):
        """ This handler is invoked for the dynamic URLs (for
        collections and records)"""

        if component == 'collection':
            c = '/'.join(path)
        
            def answer(req, form):
                # Accessing collections: this is for accessing the
                # cached page on top of each collection, but also to
                # browse through all the records in a collection when
                # used in conjunction with the jrec=<start> argument.
                
                args = wash_urlargd(form, search_interface_default_urlargd)

                if args['jrec']:
                    # This is technically a search, but so far we did
                    # not try to restrict the results, so we are
                    # mostly navigating in the collection
                    args = wash_search_urlargd(form)
                    args['cc'] = c
                    
                    req.argd = args
                    return search_engine.perform_request_search(req, **args) 

                else:
                    # We simply return the cached page of the collection
                    del args['jrec']
                    args['c'] = c

                    if not args['c']:
                        # collection argument not present; display
                        # home collection by default
                        args['c'] = cdsname
                    
                    return display_collection(req, **args)
        
            return answer, []

        elif component == 'record':
            try:
                recid = int(path[0])
            except (ValueError, IndexError):
                return None, []

            def answer(req, form):
                args = wash_search_urlargd(form)
                args['recid'] = recid

                req.argd = args
                return search_engine.perform_request_search(req, **args) 
            
            return answer, []

        return None, []

    
    def legacy_collection(self, req, form):
        args = wash_urlargd(form, legacy_collection_default_urlargd)

        # If we specify no collection, then we don't need to redirect
        # the user, so that accessing <http://yoursite/> returns the
        # default collection.
        if not form.has_key('c'):
            return display_collection(req, ** args)
        
        # make the collection an element of the path, and keep the
        # other query elements as is. If the collection is cdsname,
        # however, redirect to the main URL.
        c = args['c']
        del args['c']

        if c == cdsname:
            target = '/'
        else:
            target = '/collection/' + quote(c)

        target += make_canonical_urlargd(args, legacy_collection_default_urlargd)
        return redirect_to_url(req, target)


    def legacy_search(self, req, form):
        args = wash_search_urlargd(form)

        # We either jump into the generic search form, or the specific
        # /record/... display if a recid is requested
        if args['recid'] != -1:
            target = '/record/%d' % args['recid']
            del args['recid']
            
        else:
            target = '/search'

        target += make_canonical_urlargd(args, search_results_default_urlargd)
        return redirect_to_url(req, target)
        

def display_collection(req, c, as, verbose, ln):
    "Display search interface page for collection c by looking in the collection cache."
    from invenio.webpage import page, create_error_box
    from invenio.webuser import getUid, page_not_authorized
    from invenio.messages import wash_language, gettext_set_language
    from invenio.search_engine import get_colID, get_coll_i18nname

    _ = gettext_set_language(ln)

    req.argd = drop_default_urlargd({'as': as, 'verbose': verbose, 'ln': ln},
                                    search_interface_default_urlargd)
    
    # get user ID:
    try:
        uid = getUid(req)
        if uid == -1:
            return page_not_authorized(req, "../")
    except MySQLdb.Error, e:
        return page(title=_("Internal Error"),
                    body = create_error_box(req, verbose=verbose, ln=ln),
                    description="%s - Internal Error" % cdsname, 
                    keywords="%s, CDS Invenio, Internal Error" % cdsname,
                    language=ln,
                    req=req)
    # start display:
    req.content_type = "text/html"
    req.send_http_header()
    # deduce collection id:
    colID = get_colID(c)
    if type(colID) is not int:
        return page(title=_("Collection %s Not Found") % c,
                    body=_("<p>Sorry, collection <strong>%s</strong> does not seem to exist. "
                           "<p>You may want to start browsing from <a href=\"%s\">%s</a>.") % (c, "%s?ln=%s" % (weburl, ln), cdsnameintl[ln]),
                    description="%s - Not found: %s " % (cdsname, c),
                    keywords="%s, CDS Invenio" % cdsname,
                    uid=uid,
                    language=ln,
                    req=req)
    # display collection interface page:
    try:
        fp = open("%s/collections/%d/navtrail-as=%d-ln=%s.html" % (cachedir, colID, as, ln), "r")
        c_navtrail = fp.read()
        fp.close()
        fp = open("%s/collections/%d/body-as=%d-ln=%s.html" % (cachedir, colID, as, ln), "r")
        c_body = fp.read()
        fp.close()
        fp = open("%s/collections/%d/portalbox-tp-ln=%s.html" % (cachedir, colID, ln), "r")
        c_portalbox_tp = fp.read()
        fp.close()
        fp = open("%s/collections/%d/portalbox-te-ln=%s.html" % (cachedir, colID, ln), "r")
        c_portalbox_te = fp.read()
        fp.close()
        fp = open("%s/collections/%d/portalbox-lt-ln=%s.html" % (cachedir, colID, ln), "r")
        c_portalbox_lt = fp.read()
        fp.close()
        fp = open("%s/collections/%d/portalbox-rt-ln=%s.html" % (cachedir, colID, ln), "r")
        c_portalbox_rt = fp.read()
        fp.close()
        fp = open("%s/collections/%d/last-updated-ln=%s.html" % (cachedir, colID, ln), "r")
        c_last_updated = fp.read()
        fp.close()
        if c == cdsname:
            title = cdsnameintl[ln]
        else:
            title = get_coll_i18nname(c, ln)
            
        return page(title=title,
                    body=c_body,
                    navtrail=c_navtrail,
                    description="%s - %s" % (cdsname, c),
                    keywords="%s, CDS Invenio, %s" % (cdsname, c),
                    uid=uid,
                    language=ln,
                    req=req,
                    cdspageboxlefttopadd=c_portalbox_lt,
                    cdspageboxrighttopadd=c_portalbox_rt,
                    titleprologue=c_portalbox_tp,
                    titleepilogue=c_portalbox_te,
                    lastupdated=c_last_updated)                    
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
                    keywords="%s, CDS Invenio, Internal Error" % cdsname,
                    uid=uid,
                    language=ln,
                    req=req)
         
    return "\n"    
