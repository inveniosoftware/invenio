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
"""WebAuthorProfile Web Interface Logic and URL handler."""
# pylint: disable=W0105
# pylint: disable=C0301
# pylint: disable=W0613

import sys
from operator import  itemgetter

from invenio.bibauthorid_webauthorprofileinterface import is_valid_canonical_id, \
    get_person_id_from_paper, get_person_id_from_canonical_id, \
    search_person_ids_by_name, get_papers_by_person_id, get_person_redirect_link

from invenio.webauthorprofile_corefunctions import get_pubs, get_person_names_dicts, \
    get_institute_pub_dict, get_coauthors, get_summarize_records, \
    get_total_downloads, get_cited_by_list, get_kwtuples, get_venuetuples, \
    get_veryfy_my_pubs_list_link, get_hepnames_data, get_self_pubs, \
    get_collabtuples


#from invenio.bibauthorid_config import EXTERNAL_CLAIMED_RECORDS_KEY
from invenio.config import CFG_SITE_LANG
from invenio.config import CFG_SITE_URL
from invenio.config import CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID
from invenio.webpage import pageheaderonly
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.urlutils import redirect_to_url
from invenio.jsonutils import json_unicode_to_utf8



import invenio.template
websearch_templates = invenio.template.load('websearch')
webauthorprofile_templates = invenio.template.load('webauthorprofile')
bibauthorid_template = invenio.template.load('bibauthorid')

from invenio.search_engine import page_end
JSON_OK = False

if sys.hexversion < 0x2060000:
    try:
        import simplejson as json
        JSON_OK = True
    except ImportError:
        # Okay, no Ajax app will be possible, but continue anyway,
        # since this package is only recommended, not mandatory.
        JSON_OK = False
else:
    try:
        import json
        JSON_OK = True
    except ImportError:
        JSON_OK = False

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

class WebAuthorPages(WebInterfaceDirectory):
    """
    Handle webauthorpages. /author/
    """
    _exports = ['']

    def _lookup(self, component, path):
        """
        This handler parses dynamic URLs:
        - /person/1332 shows the page of person 1332
        - /person/100:5522,1431 shows the page of the person
            identified by the table:bibref,bibrec pair
        """
        if not component in self._exports:
            return WebAuthorPages(component), path

    def __init__(self, person_id=None):
        """
        Constructor of the web interface.

        @param person_id: The identifier of a user. Can be one of:
            - a bibref: e.g. "100:1442,155"
            - a person id: e.g. "14"
            - a canonical id: e.g. "Ellis_J_1"
        @type person_id: string

        @return: will return an empty object if the identifier is of wrong type
        @rtype: None (if something is not right)
        """
        self.person_id = None
        self.cid = None
        self.original_search_parameter = person_id

        if not CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID:
            return

        if (not person_id) or (not isinstance(person_id, str)):
            return

        try:
            self.person_id = int(person_id)
            self.cid = get_person_redirect_link(self.person_id)
            return
        except (TypeError, ValueError):
            pass

        try:
            self.person_id = int(get_person_id_from_canonical_id(person_id))
            if self.person_id < 0:
                if is_valid_canonical_id(person_id):
                    self.cid = None
                    return
                else:
                    raise ValueError
            self.cid = get_person_redirect_link(self.person_id)
            return
        except (ValueError, TypeError):
            pass

        fail_bibrecref = False
        if person_id.count(":") and person_id.count(","):
            bibref = person_id
            table, ref, bibrec = None, None, None

            if not bibref.count(":"):
                fail_bibrecref = True

            if not bibref.count(","):
                fail_bibrecref = True

            try:
                table = bibref.split(":")[0]
                ref = bibref.split(":")[1].split(",")[0]
                bibrec = bibref.split(":")[1].split(",")[1]
            except IndexError:
                fail_bibrecref = True
            try:
                table = int(table)
                ref = int(ref)
                bibrec = int(bibrec)
            except (ValueError, TypeError):
                fail_bibrecref = True

            try:
                pid = int(get_person_id_from_paper(person_id))
            except (ValueError, TypeError):
                fail_bibrecref = True

            if not fail_bibrecref:
                self.person_id = pid
                self.cid = self.cid = get_person_redirect_link(self.person_id)
                return

        self.person_id = -1

        #self.person_id can be:
        # -1 if not valid personid

    def index(self, req, form):
        '''
        Serve the main person page.
        Will use the object's person id to get a person's information.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: string
        '''
        argd = wash_urlargd(form,
                            {'ln': (str, CFG_SITE_LANG),
                             'verbose': (int, 0),
                             'recid': (int, -1)
                             })

        ln = argd['ln']

        if CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID:
            try:
                self.person_id = int(self.person_id)
            except (TypeError, ValueError):
                #In any case, if the parameter is invalid, go to a person search page
                self.person_id = -1
                return redirect_to_url(req, "%s/person/search?q=%s" %
                        (CFG_SITE_URL, self.original_search_parameter))

            if self.person_id < 0:
                return redirect_to_url(req, "%s/person/search?q=%s" %
                        (CFG_SITE_URL, self.original_search_parameter))
        else:
            self.person_id = self.original_search_parameter

        if form.has_key('jsondata'):
            req.content_type = "application/json"
            self.create_authorpage_websearch(req, form, self.person_id, ln)
            return
        else:
            req.content_type = "text/html"
        req.send_http_header()
        metaheaderadd = '<script type="text/javascript" src="%s/js/webauthorprofile.js"> </script>' % (CFG_SITE_URL)
        metaheaderadd += """
        <style> 
        .hidden {
            display: none;
        }
        </style>
        """
        title_message = "Author Publication Profile Page"

        req.write(pageheaderonly(req=req, title=title_message,
                                 metaheaderadd=metaheaderadd, language=ln))
        req.write(websearch_templates.tmpl_search_pagestart(ln=ln))
        self.create_authorpage_websearch(req, form, self.person_id, ln)
        return page_end(req, 'hb', ln)


    def __call__(self, req, form):
        '''
        Serve the main person page.
        Will use the object's person id to get a person's information.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: string
        '''
        argd = wash_urlargd(form,
                    {'ln': (str, CFG_SITE_LANG),
                     'verbose': (int, 0),
                     'recid': (int, -1)
                     })
        recid = argd['recid']

        if not CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID:
            return self.index(req, form)

        if self.cid:
            return redirect_to_url(req, '%s/author/%s/' % (CFG_SITE_URL, self.cid))
        elif self.person_id and self.person_id >= 0:
            return redirect_to_url(req, '%s/author/%s/' % (CFG_SITE_URL, self.person_id))

        elif self.person_id and recid > -1:
            #we got something different from person_id, canonical name or bibrefrec pair.
            #try to figure out a personid
            argd = wash_urlargd(form,
                                {'ln': (str, CFG_SITE_LANG),
                                 'verbose': (int, 0),
                                 'recid': (int, -1)
                                 })
            recid = argd['recid']
            if not recid:
                return redirect_to_url(req, "%s/person/search?q=%s" %
                    (CFG_SITE_URL, self.original_search_parameter))
                # req.write("Not enough search parameters %s"%
                #    str(self.original_search_parameter))

            nquery = self.original_search_parameter
            sorted_results = search_person_ids_by_name(nquery)
            test_results = None
            authors = []

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
            if len(test_results) == 1:
                self.person_id = test_results[0][0]
                self.cid = get_person_redirect_link(self.person_id)
                if self.cid and self.person_id > -1:
                    redirect_to_url(req, '%s/author/%s/' % (CFG_SITE_URL, self.cid))
                elif self.person_id > -1:
                    redirect_to_url(req, '%s/author/%s/' % (CFG_SITE_URL, self.person_id))
                else:
                    return redirect_to_url(req, "%s/person/search?q=%s" %
                    (CFG_SITE_URL, self.original_search_parameter))
                    #req.write("Could not determine personID from bibrec. What to do here? %s"%
                    #str(self.original_search_parameter))
            else:
                return redirect_to_url(req, "%s/person/search?q=%s" %
                    (CFG_SITE_URL, self.original_search_parameter))
                #req.write("Could not determine personID from bibrec. What to do here 2? %s"%
                #   (str(self.original_search_parameter),str(recid)))

        else:
            return redirect_to_url(req, "%s/person/search?q=%s" %
                    (CFG_SITE_URL, self.original_search_parameter))
            # req.write("Search param %s does not represent a valid person, please correct your query"%
            #(str(self.original_search_parameter),))

    def create_authorpage_websearch(self, req, form, person_id, ln='en'):

        if CFG_WEBAUTHORPROFILE_USE_BIBAUTHORID:
            if person_id < 0:
                return ("Critical Error. PersonID should never be less than 0!")

        pubs, pubsStatus = get_pubs(person_id)
        if not pubs:
            pubs = []

        selfpubs, selfpubsStatus = get_self_pubs(person_id)
        if not selfpubs:
            selfpubs = []

        namesdict, namesdictStatus = get_person_names_dicts(person_id)
        if not namesdict:
            namesdict = {}

        try:
            authorname = namesdict['longest']
            db_names_dict = namesdict['db_names_dict']
        except (IndexError, KeyError):
            authorname = 'None'
            db_names_dict = {}

        #author_aff_pubs, author_aff_pubsStatus = (None, None)
        author_aff_pubs, author_aff_pubsStatus = get_institute_pub_dict(person_id)
        if not author_aff_pubs:
            author_aff_pubs = {}


        coauthors, coauthorsStatus = get_coauthors(person_id)
        if not coauthors:
            coauthors = {}

        summarize_records, summarize_recordsStatus = get_summarize_records(person_id, 'hcs', ln)
        if not summarize_records:
            summarize_records = 'None'

        totaldownloads, totaldownloadsStatus = get_total_downloads(person_id)
        if not totaldownloads:
            totaldownloads = 0

        citedbylist, citedbylistStatus = get_cited_by_list(person_id)
        if not citedbylist:
            citedbylist = 'None'

        kwtuples, kwtuplesStatus = get_kwtuples(person_id)
        if kwtuples:
            pass
            #kwtuples = kwtuples[0:MAX_KEYWORD_LIST]
        else:
            kwtuples = []

        collab, collabStatus = get_collabtuples(person_id)

        vtuples, venuetuplesStatus = get_venuetuples(person_id)
        if vtuples:
            pass
            #vtuples = venuetuples[0:MAX_VENUE_LIST]
        else:
            vtuples = str(vtuples)

        person_link, person_linkStatus = get_veryfy_my_pubs_list_link(person_id)
        if not person_link:
            bibauthorid_data = {"is_baid": True, "pid":person_id, "cid": None}
            person_link = 'None'
        else:
            bibauthorid_data = {"is_baid": True, "pid":person_id, "cid": person_link}

        hepdict, hepdictStatus = get_hepnames_data(person_id)

        #req.write("\nPAGE CONTENT START\n")
        #req.write(str(time.time()))
        #eval = [not_empty(x) or y for x, y in
        beval = [y for _, y in
                                               [(authorname, namesdictStatus) ,
                                               (totaldownloads, totaldownloadsStatus),
                                               (author_aff_pubs, author_aff_pubsStatus),
                                               (citedbylist, citedbylistStatus),
                                               (kwtuples, kwtuplesStatus),
                                               (coauthors, coauthorsStatus),
                                               (vtuples, venuetuplesStatus),
                                               (db_names_dict, namesdictStatus),
                                               (person_link, person_linkStatus),
                                               (summarize_records, summarize_recordsStatus),
                                               (pubs, pubsStatus),
                                               (hepdict, hepdictStatus),
                                               (selfpubs, selfpubsStatus),
                                               (collab, collabStatus)]]
        #not_complete = False in eval
        #req.write(str(eval))

        if form.has_key('jsondata'):
            json_response = {'boxes_info': {}}
            json_data = json.loads(str(form['jsondata']))
            json_data = json_unicode_to_utf8(json_data)
            # loop to check which boxes need content
            json_response['boxes_info'].update({'name_variants': {'status':beval[0], 'html_content': webauthorprofile_templates.tmpl_author_name_variants_box(req, db_names_dict, bibauthorid_data, ln, add_box=False, loading=not beval[7])}})
            json_response['boxes_info'].update({'combined_papers': {'status':(beval[3] and beval[12]), 'html_content': webauthorprofile_templates.tmpl_papers_with_self_papers_box(req, pubs, selfpubs, bibauthorid_data, totaldownloads, ln, add_box=False, loading=not beval[3])}})
            #json_response['boxes_info'].update({'papers': {'status':beval[3], 'html_content': webauthorprofile_templates.tmpl_papers_box(req, pubs, bibauthorid_data, totaldownloads, ln, add_box=False, loading=not beval[3])}})
            json_response['boxes_info'].update({'selfpapers': {'status':beval[12], 'html_content': webauthorprofile_templates.tmpl_self_papers_box(req, selfpubs, bibauthorid_data, totaldownloads, ln, add_box=False, loading=not beval[12])}})
            json_response['boxes_info'].update({'keywords': {'status':beval[4], 'html_content': webauthorprofile_templates.tmpl_keyword_box(kwtuples, bibauthorid_data, ln, add_box=False, loading=not beval[4])}})
            json_response['boxes_info'].update({'affiliations': {'status':beval[2], 'html_content': webauthorprofile_templates.tmpl_affiliations_box(author_aff_pubs, ln, add_box=False, loading=not beval[2])}})
            json_response['boxes_info'].update({'coauthors': {'status':beval[5], 'html_content': webauthorprofile_templates.tmpl_coauthor_box(bibauthorid_data, coauthors, ln, add_box=False, loading=not beval[5])}})
            json_response['boxes_info'].update({'numpaperstitle': {'status':beval[10], 'html_content': webauthorprofile_templates.tmpl_numpaperstitle(bibauthorid_data, pubs)}})
            json_response['boxes_info'].update({'authornametitle': {'status':beval[7], 'html_content': webauthorprofile_templates.tmpl_authornametitle(db_names_dict)}})
            json_response['boxes_info'].update({'citations': {'status':beval[9], 'html_content': summarize_records}})
            json_response['boxes_info'].update({'hepdata': {'status':beval[11], 'html_content':webauthorprofile_templates.tmpl_hepnames(hepdict, ln, add_box=False, loading=not beval[11])}})
            json_response['boxes_info'].update({'collaborations': {'status':beval[13], 'html_content': webauthorprofile_templates.tmpl_collab_box(collab, bibauthorid_data, ln, add_box=False, loading=not beval[13])}})

            req.content_type = 'application/json'
            req.write(json.dumps(json_response))
        else:
            gboxstatus = ''
            if False not in [beval[2], beval[3], beval[4], beval[5], beval[7], beval[9], beval[11]]:
                gboxstatus = 'noAjax'
            req.write('<script type="text/javascript">var gBOX_STATUS = "%s" </script>' % (gboxstatus))
            req.write(webauthorprofile_templates.tmpl_author_page(req,
                                            pubs, \
                                            selfpubs, \
                                            authorname, \
                                            totaldownloads, \
                                            author_aff_pubs, \
                                            citedbylist, kwtuples, \
                                            coauthors, vtuples, \
                                            db_names_dict, person_link, \
                                            bibauthorid_data, \
                                            summarize_records, \
                                            hepdict, \
                                            collab, \
                                            ln, \
                                            beval))



