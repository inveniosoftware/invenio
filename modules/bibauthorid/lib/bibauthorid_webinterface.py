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
"""Bibauthorid URL handler."""
# pylint: disable=W0105
from operator import itemgetter
from cgi import escape
import simplejson as json

from invenio.bibauthorid_config import CLAIMPAPER_VIEW_PID_UNIVERSE
from invenio.bibauthorid_config import CLAIMPAPER_CHANGE_OWN_DATA
from invenio.bibauthorid_config import CLAIMPAPER_CHANGE_OTHERS_DATA
from invenio.bibauthorid_config import CLAIMPAPER_CLAIM_OWN_PAPERS
from invenio.bibauthorid_config import CLAIMPAPER_CLAIM_OTHERS_PAPERS
from invenio.bibauthorid_config import EXTERNAL_CLAIMED_RECORDS_KEY
from invenio.config import CFG_SITE_LANG
from invenio.config import CFG_SITE_URL
from invenio.config import CFG_SITE_NAME
from invenio.config import CFG_SITE_SECURE_URL
from invenio.webpage import page
from invenio.messages import gettext_set_language, wash_language
from invenio.template import load
from invenio.webinterface_handler import wash_urlargd, WebInterfaceDirectory
from invenio.session import get_session
from invenio.urlutils import redirect_to_url
from invenio.webuser import getUid, page_not_authorized, collect_user_info
from invenio.access_control_admin import acc_find_user_role_actions
from invenio.search_engine import perform_request_search
import invenio.bibauthorid_webapi as webapi

TEMPLATE = load('bibauthorid')


class WebInterfaceBibAuthorIDPages(WebInterfaceDirectory):
    """
    Handle /person pages and AJAX requests

    Supplies the methods
        /person/<string>
        /person/status
        /person/batchprocess
        /person/search
    """
    _exports = ['', 'batchprocess', 'comments', 'search', 'status', 'claim', 'me', 'you']


    def __init__(self, person_id=None):
        """
        Constructor of the web interface.

        @param person_id: The identifier of a user. Can be one of:
            - a bibref: e.g. "100:1442,155"
            - a person id: e.g. "14"
        @type person_id: string

        @return: will return an empty object if the identifier is of wrong type
        @rtype: None (if something is not right)
        """
        pid = -1
        is_bibref = False

        if (not isinstance(person_id, str)) or (not person_id):
            self.person_id = pid
            return None

        if person_id.count(":") and person_id.count(","):
            is_bibref = True

        if is_bibref and pid > -2:
            bibref = person_id
            table, ref, bibrec = None, None, None

            if not bibref.count(":"):
                pid = -2

            if not bibref.count(","):
                pid = -2

            try:
                table = bibref.split(":")[0]
                ref = bibref.split(":")[1].split(",")[0]
                bibrec = bibref.split(":")[1].split(",")[1]
            except IndexError:
                pid = -2

            try:
                table = int(table)
                ref = int(ref)
                bibrec = int(bibrec)
            except (ValueError, TypeError):
                pid = -2

            if pid == -1:
                try:
                    pid = int(webapi.get_person_id_from_paper(person_id))
                except ValueError:
                    pid = -1
            else:
                pid = -1
        else:
            try:
                pid = int(person_id)
            except ValueError:
                pid = -1

        self.person_id = pid


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
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'verbose': (int, 0)})
        ln = wash_language(argd['ln'])
        req.argd = argd #needed for perform_req_search
        pid_ok = -1
        session = get_session(req)

        if self.person_id and self.person_id >= 0:
            pid_ok = self.person_id

        if not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
            return page_not_authorized(
                        req=req,
                        referer="%s/person/%s" % (CFG_SITE_URL, pid_ok),
                        text=("We're sorry. You are not authorized to "
                             "perform this action. If you think that "
                             "this is incorrect, please contact your "
                             "administrator."),
                        ln=ln)

        if pid_ok < 0:
            return self._error_page(req, ln, "Invalid Person ID.")

        session["claimpaper_admin_last_viewed_pid"] = self.person_id
        title = "Author/Person Administration"
        metaheaderadd = self._scripts()
        session.save()

        # Acquire Data
        names = webapi.get_person_names_from_id(self.person_id)
        all_papers = webapi.get_papers_by_person_id(self.person_id)
        rejected_papers = [row for row in all_papers if row[2] < -1]
        rest_of_papers = [row for row in all_papers if row[2] >= -1]
        review_needed = webapi.get_review_needing_records(self.person_id)

        # Send data to template function
        body = TEMPLATE.tmpl_author_details(req, person_id=self.person_id,
                                            names=names,
                                            rejected_papers=rejected_papers,
                                            rest_of_papers=rest_of_papers,
                                            review_needed=review_needed)

        # Return readily constructed page
        return page(title=title,
            metaheaderadd=metaheaderadd,
            body=body,
            req=req,
            language=ln)


    index = __call__

    def _error_page(self, req, ln=CFG_SITE_LANG, message=None, intro=True):
        '''
        Create a page that contains a message explaining the error.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param ln: language
        @type ln: string
        @param message: message to be displayed
        @type message: string
        '''
        body = []

        if not message:
            message = "No further explanation available. Sorry."

        if intro:
            body.append("<p>We're sorry. An error occurred while "
                        "handling your request. Please find more information "
                        "below:</p>")
        body.append("<p><strong>%s</strong></p>" % message)

        return page(title="Notice",
                body="\n".join(body),
                description="%s - Internal Error" % CFG_SITE_NAME,
                keywords="%s, Internal Error" % CFG_SITE_NAME,
                language=ln,
                req=req)


    def _lookup(self, component, path):
        """
        This handler parses dynamic URLs:
        - /person/1332 shows the page of person 1332
        - /person/100:5522,1431 shows the page of the person
            identified by the table:bibref,bibrec pair
        - /person/status?person_id=1332&paper=1431 requests the JSON
            element that describes the status of a paper as
            identified by the bibrec
        """
        if not component in self._exports:
            return WebInterfaceBibAuthorIDPages(component), path


    def _scripts(self):
        '''
        Returns html code to be included in the meta header of the html page.
        The actual code is stored in the template.

        @return: html formatted Javascript and CSS inclusions for the <head>
        @rtype: string
        '''
        return TEMPLATE.tmpl_meta_includes()


    def batchprocess(self, req, form):
        '''
        Allows to mass/batch process assignments of records.

        Valid mass actions are:
        - massign: mass assign records to another person
        - mconfirm: mass confirm assignments to a person
        - mrepeal: mass repeal assignments from a person
        - mreset: mass reset assignments of a person
        - mreviewed: continue a started review process
        - mcancel: cancel whatever operation is currently running
        - mfind_bibref: ask confirmation for which bibref to assign and assign.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: string
        '''
        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'pid': (int, None),
             'selection': (list, []),
             'mconfirm': (str, None),
             'massign': (str, None),
             'mrepeal': (str, None),
             'mreset': (str, None),
             'mcancel': (str, None),
             'mreviewed': (str, None),
             'mfind_bibref': (str, None),
             'selected_bibrecs': (list, [])})

        ln = wash_language(argd['ln'])
        pid = None
        action = None
        bibrefs = None
        session = get_session(req)
        self.mass_fail_message = ("Sorry. The mass action for documents "
                             "failed for a currently unknown reason. The "
                             "administrators have been contacted.")

        if (not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS) and
            not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OWN_PAPERS)):
            return page_not_authorized(
                        req=req,
                        referer="%s/person/%s" % (CFG_SITE_URL, pid),
                        text=("We're sorry. You are not authorized to "
                             "perform this action. If you think that "
                             "this is incorrect, please contact your "
                             "administrator."),
                        ln=ln)
        if 'mcancel' in argd:
            if argd['mcancel']:
                redir_pid = pid

                if "pid_batch_assign_papers" in session:
                    redir_pid = session["pid_batch_assign_papers"]
                elif "aid_mass_review_pid" in session:
                    redir_pid = session["aid_mass_review_pid"]

                self.__session_cleanup(req)
                session['person_message_show'] = True
                session['person_message'] = ("Successfully canceled the "
                                     "process")
                session.save()
                if self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
                    return redirect_to_url(req, "%s/person/%s"
                                       % (CFG_SITE_URL, pid))
                else:
                    return redirect_to_url(req, "%s/person/claim" % CFG_SITE_URL)

        if 'mfind_bibref' in argd and argd['mfind_bibref']:
            if argd['mfind_bibref'] == 'claim' and argd['selected_bibrecs']:
                if self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
                    body = TEMPLATE.tmpl_bibref_confirm_dispatcher(req, argd['selected_bibrecs'])
                    return page(title="Review transaction",
                            metaheaderadd=self._scripts(),
                            body=body,
                            req=req,
                            language=ln)
                else:
                    return self.__bibref_select_page(req, ln, argd['selected_bibrecs'])
            elif argd['mfind_bibref'] == 'confirm':
                return self.__bibref_select_validate_confirm_page(req, ln, form)
            elif argd['mfind_bibref'] == 'admin_claim':
                if 'pid' in argd and argd['pid']:
                    return self.__bibref_select_page(req, ln, argd['selected_bibrecs'], force_pid=argd['pid'])
                else:
                    return self.__bibref_select_page(req, ln, argd['selected_bibrecs'])
            else:
                return self._error_page(req, ln, self.mass_fail_message)

        if 'pid' in argd:
            pid = argd['pid']
        else:
            return self._error_page(req, ln,
                                    "Please provide a valid person id")

        if 'selection' in argd and len(argd['selection']) > 0:
            bibrefs = argd['selection']

        elif (argd.has_key("massign") and argd["massign"] and
              session.has_key("mode_batch_assign_papers") and
              session.has_key("bibrecs_batch_assign_papers")):
            bibrefs = session["bibrecs_batch_assign_papers"]
        elif (argd.has_key("mreviewed") and
              session.has_key("aid_mass_review_action") and
              session.has_key("aid_mass_review_transactions")):
            bibrefs = []
        else:
            return self._error_page(req, ln,
                                    "Sorry. To use this function, please "
                                    "select at least one document from the "
                                    "list to be processed.")

        if 'mconfirm' in argd:
            if argd['mconfirm']:
                return self.__mass_confirm(req, pid, bibrefs, ln)

        if 'massign' in argd:
            if argd['massign']:
                return self.__mass_assign(req, argd['massign'], pid,
                                          bibrefs, ln)

        if 'mrepeal' in argd:
            if argd['mrepeal']:
                return self.__mass_repeal(req, pid, bibrefs, ln)

        if 'mreset' in argd:
            if argd['mreset']:
                return self.__mass_reset(req, pid, bibrefs, ln)

        if "mreviewed" in argd:
            if argd['mreviewed']:
                body = TEMPLATE.tmpl_author_transaction_review(req)

                return page(title="Review transaction",
                    metaheaderadd=self._scripts(),
                    body=body,
                    req=req,
                    language=ln)

        return "Action: p%s %s %s" % (pid, action, bibrefs)


    def comments(self, req, form):
        '''
        Handles comments attached to a person returning JSON objects
        Possible actions are:
        - get_comments: will return the comments of a certain person id
        - store_comment: will attach the comment to a certain person id

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: string
        '''
        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'pid': (int, None),
             'action': (str, "get_comments"),
             'message': (str, "")})

        ln = wash_language(argd['ln'])
        pid = None
        action = None
        message = None
        uid = getUid(req)
        userinfo = "%s||%s" % (uid, req.remote_ip)
        comments = {'comments': []}
        error_html = json.dumps({'comments': [
                                "We're sorry. An error occured while handling "
                                "your request"]})
        if 'pid' in argd:
            pid = argd['pid']
        else:
            return error_html

        if not self.__user_is_authorized(req, CLAIMPAPER_CHANGE_OTHERS_DATA):
            return json.dumps({'comments': [
                                "We're sorry. You are not authorized to "
                                "perform this action. If you think that "
                                "this is incorrect, please contact your "
                                "administrator."]})

        if 'action' in argd:
            action = argd['action']
        else:
            return error_html

        if 'message' in argd:
            message = argd['message']

        if action == "get_comments":
            comments_db = webapi.get_person_comments(pid)

            if comments_db:
                for comment in comments_db:
                    comments['comments'].append(comment)

            return json.dumps(comments)

        elif action == "store_comment":
            if message:
                washed_message = webapi.add_person_comment(pid, message)
                if washed_message:
                    webapi.log(userinfo, pid, "comment", "message",
                               washed_message)
                    comments['comments'].append(washed_message)
                    return json.dumps(comments)
                else:
                    return error_html
            else:
                return error_html
        else:
            return error_html


    def claim(self, req, form):
        '''
        Serve the main 'claim my paper' interface.
        Will use the user's internal account id to determine the person id to
        then get the relevant person information.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: string
        '''
        argd = wash_urlargd(form, {'ln': (str, CFG_SITE_LANG),
                                   'verbose': (int, 0)})
        ln = wash_language(argd['ln'])
        req.argd = argd #needed for perform_req_search
        uid = getUid(req)
        session = get_session(req)
        pid = -1
        _ = gettext_set_language(argd['ln'])

        if not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OWN_PAPERS):
            return page_not_authorized(
                        req=req,
                        referer="%s/person/claim" % (CFG_SITE_URL),
                        text=("We're sorry. You are not authorized to "
                              "perform this action. Please log in to start "
                              "claiming your papers"),
                        ln=ln)

        pid_info = webapi.get_pid_from_uid(uid)

        if pid_info and (not pid_info[0][0] or pid_info[0][0] < 0):
            return self._error_page(req, ln, "We could not reliably determine "
                                    "a bibliographic profile for you.  Please "
                                    "use the <a href=''>search function</a> "
                                    "and claim a paper to tell us who you are."
                                    "  Sorry for this inconvenience!", False)
        elif len(pid_info[0]) > 1:
            # take care of multiple Person assignments!
            pid = self.__handle_external_records(req, pid_info)
            pid = webapi.assign_uid_to_person(uid, pid)

            if pid < 0:
                pid = webapi.assign_uid_to_person(uid, pid, create_new_pid=True)

            session["claimpaper_first_time_user"] = True
            session.save()
        else:
            if not pid_info[1]:
                # take care of Person and paper assignment!
                pid = self.__handle_external_records(req, pid_info,
                                                     pid_info[0][0])
                pid = webapi.assign_uid_to_person(uid, pid)

                if pid < 0:
                    pid = webapi.assign_uid_to_person(uid, pid, create_new_pid=True)

                session["claimpaper_first_time_user"] = True
                session.save()
            elif pid_info[0][0]:
                try:
                    pid = int(pid_info[0][0])
                except (ValueError, TypeError, IndexError):
                    pid = -1
                self.__handle_external_records(req, pid_info, pid)

        if pid < 0:
            return self._error_page(req, ln, "Invalid Person ID.")

        title = "Claim Your Papers"
        metaheaderadd = self._scripts()

        # Acquire Data
        names = webapi.get_person_names_from_id(pid)
        all_papers = webapi.get_papers_by_person_id(pid)
        rejected_papers = [row for row in all_papers if row[2] < -1]
        rest_of_papers = [row for row in all_papers if row[2] >= -1]
        review_needed = webapi.get_review_needing_records(pid)

        # Send data to template function
        body = TEMPLATE.tmpl_author_claim(req, person_id=pid,
                                            names=names,
                                            rejected_papers=rejected_papers,
                                            rest_of_papers=rest_of_papers,
                                            review_needed=review_needed)

        # Return readily constructed page
        return page(title=title,
            metaheaderadd=metaheaderadd,
            body=body,
            req=req,
            navtrail='<a class="navtrail" href="%s/youraccount/display?ln=%s">%s</a>' % (CFG_SITE_SECURE_URL, ln, _("Your Account")),
            navmenuid='youraccount',
            language=ln)


    def __handle_external_records(self, req, pid_info, ppid= -1):
        pid = -1
        uid = getUid(req)
        userloginfo = "%s||%s" % (uid, req.remote_ip)
        user_info = collect_user_info(uid)
        recids_of_ext_ids = set()
        promising_pid = -1
        max_matches = 0
        processed_external_recs = []

        try:
            ppid = int(ppid)
        except (ValueError, TypeError):
            ppid = -1

        if ppid > -1:
            processed_external_recs = webapi.get_processed_external_recids(ppid)

            for rec_item in processed_external_recs:
                if not rec_item:
                    processed_external_recs.remove(rec_item)

        for rkey in EXTERNAL_CLAIMED_RECORDS_KEY:
            if rkey in user_info:
                if user_info[rkey]:
                    for ext_rec_str in user_info[rkey].split(";"):
                        if ext_rec_str in processed_external_recs:
                            continue

                        ids = perform_request_search(req, p=ext_rec_str)

                        if ids and len(ids) == 1:
                            recids_of_ext_ids.add(ids[0])
                            processed_external_recs.append(ext_rec_str)

        if recids_of_ext_ids:
            if ppid < 0:
                for cpid in pid_info[0]:
                    try:
                        cpid = int(cpid)
                    except (ValueError, TypeError):
                        continue

                    pid_papers = webapi.get_papers_by_person_id(cpid)
                    pid_recids = set([row[0] for row in pid_papers])
                    match = pid_recids.intersection(recids_of_ext_ids)

                    if len(match) == len(recids_of_ext_ids):
                        max_matches = len(match)
                        promising_pid = cpid
                        break
                    elif len(match) > max_matches:
                        max_matches = len(match)
                        promising_pid = cpid
            else:
                promising_pid = ppid

            if promising_pid > -1:
                pid = promising_pid
#                p_names = webapi.get_person_names_from_id(pid)

                for rec_id in recids_of_ext_ids:
                    ref = webapi.get_possible_bibrefs_from_pid_bibrec(pid,
                                                                      rec_id,
                                                                      False)

                    if ref and ref[0] and ref[0][1]:
                        if len(ref[0][1]) == 1:
                            refpair = "%s,%s" % (ref[0][1][0][0], rec_id)

                            status = webapi.get_paper_status(pid, refpair)

                            if status == 2 or status == -2:
                                continue

                            webapi.confirm_person_bibref_assignments(pid,
                                                                 [refpair],
                                                                 uid)
                            webapi.log(userloginfo, pid, "confirm",
                                            "bibref", refpair,
                                            comment=("auto confirm from "
                                                     "external record"))
                        else:
                            webapi.add_review_needing_record(pid, rec_id)
            else:
                pid = pid_info[0][0]

            webapi.set_processed_external_recids(pid, processed_external_recs)

            try:
                pid = int(pid)
            except (ValueError, TypeError):
                pid = -1

            return pid


    def __bibref_select_validate_confirm_page(self, req, ln, form):
        '''
        Sanity checks and deploys to _mass_confirm.
        @param form: UPDATEEEEEE list of bibrecbibref pairs which have been manually
        assigned. Will be crosscheckd with what have been saved in the session before
        generating the request of manual assignment for the user.
        '''
        session = get_session(req)

        try:
            pid = session['claimpaper_bibrecrefs_pid']
            bibrec_refs_needs_confirm = session['claimpaper_bibrecrefs_needs_confirm']
            bibrec_refs_to_confirm = session['claimpaper_bibrecrefs_to_confirm']
        except KeyError:
            return self._error_page(req, ln, "Sorry, looks like there has been a problem with"
                                    "the session. Cannot proceed.")
        if not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OWN_PAPERS):
            return page_not_authorized(
                        req=req,
                        referer="%s/person/%s" % (CFG_SITE_URL, pid),
                        text=("We're sorry. You are not authorized to "
                             "perform this action. If you think that "
                             "this is incorrect, please contact your "
                             "administrator."),
                        ln=ln)
        mass_bibcouples = []

        for b in bibrec_refs_to_confirm:
            mass_bibcouples.append(str(b[1][0][0]) + ',' + str(b[0]))

        bibreclist = []
        for bibrec in bibrec_refs_needs_confirm:
            rec_grp = "bibrecgroup%s" % bibrec[0]
            if rec_grp in form:
                bibreclist.append(form[rec_grp] + ',' + str(bibrec[0]))

        for p in bibreclist:
            rec = p.split(',')[1]
            ref = p.split(',')[0]
            for b in bibrec_refs_needs_confirm:
                if rec == str(b[0]):
                    for br in b[1]:
                        if ref == str(br[0]):
                            mass_bibcouples.append(p)

        return self.__mass_confirm(req, pid, mass_bibcouples, ln)


    def __bibref_select_page(self, req, ln, bibreclist, force_pid=''):
        '''
        Generates the page for bibrefs selection when claiming papers.
        @param bibreclist: a list of bibrecs which are being claimed.
        '''
        self.__session_cleanup(req)
        session = get_session(req)
        uid = getUid(req)

        if not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OWN_PAPERS):
            return page_not_authorized(
                        req=CFG_SITE_URL + req.unparsed_uri,
                        referer=req,
                        text=("We're sorry. You are not authorized to "
                             "perform this action. If you think that "
                             "this is incorrect, please contact your "
                             "administrator."),
                        ln=ln)
        if force_pid:
            try:
                pid = int(force_pid)
            except (ValueError, TypeError):
                pid = -1
        else:
            pid = webapi.get_pid_from_uid(((uid,),))[0][0]

        if pid < 0:
            return self._error_page(req, ln, "Sorry, looks like no personID is associated"
                                    " to this profile yet. Cannot proceed.")

        possible_bibrec_refs = webapi.get_possible_bibrefs_from_pid_bibrec(pid, bibreclist)
        bibrec_refs_needs_confirm = []
        bibrec_refs_to_confirm = []

        for br in possible_bibrec_refs:
            if len(br[1]) == 1:
                bibrec_refs_to_confirm.append(br)
            else:
                if len(br[1]) < 1:
                    br[1] = webapi.get_bibrefs_from_bibrecs([br[0]])[0][1]
                bibrec_refs_needs_confirm.append(br)

        session['claimpaper_bibrecrefs_to_confirm'] = bibrec_refs_to_confirm
        session['claimpaper_bibrecrefs_needs_confirm'] = bibrec_refs_needs_confirm
        session['claimpaper_bibrecrefs_pid'] = pid
        session.save()

        body = TEMPLATE.tmpl_bibref_confirm(req, pid, bibrec_refs_needs_confirm, bibrec_refs_to_confirm)

        return page(title="Review transaction",
                metaheaderadd=self._scripts(),
                body=body,
                req=req,
                language=ln)


    def __get_transaction_items(self, req, ln, pid, action, bibrefs):
        '''
        Constructs the items of a transaction in the following cases:
        1) No review process is in progress:
            Return all the items in bibrefs with attached values if the
            assignment may be touched and if the assignment has been touched
            before. Possibles states:
            - "not_authorized": User is not authorized to change the assignment
            - "touched": An assignment has been touched by another user
            - "OK": The assignment is ok for further processing
        2) if the transaction has been confirmed, delete all bibrefs that
            have been excluded from the transaction by the user and the ones
            that the user has no permission to touch

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param pid: person id of the person targeted by the mass action
        @type pid: int
        @param bibrefs: list of bibref-bibrec pairs to identify the records
        @type bibrefs: list of strings
        @param ln: the language the web page shall be served in
        @type ln: string

        @return: a fully formatted html page to be displayed to the user
        @rtype: string
        '''
        session = get_session(req)
        transactions = []
        err_msg = "Sorry. The action took a wrong turn. We're on to fix it."
        uid = getUid(req)

        if not session.has_key("aid_mass_review_action"):
            for bibref in bibrefs:
                if not webapi.user_can_modify_paper(uid, bibref):
                    transactions.append({"bibref": bibref,
                                         "status": "not_allowed"})
                elif webapi.person_bibref_is_touched(pid, bibref):
                    transactions.append({"bibref": bibref,
                                         "status": "touched"})
                else:
                    transactions.append({"bibref": bibref,
                                         "status": "OK"})
            return transactions

        elif not session["aid_mass_review_action"] == action:
            return self._error_page(req, ln, err_msg)

        elif not session.has_key("aid_mass_review_transactions"):
            return self._error_page(req, ln, err_msg)

        else:
            transactions = session["aid_mass_review_transactions"]

            for deletion in [row for row in transactions
                             if ((row['bibref'] in bibrefs) or
                                 (row["status"] == "not_allowed"))]:
                transactions.remove(deletion)

            for update_ok in [row for row in transactions
                             if (row["status"] == "touched")]:
                update_ok["status"] = "OK"

            if [row for row in transactions
                                 if ((row['status'] == "touched") or
                                     (row["status"] == "not_allowed"))]:
                return self._error_page(req, ln, err_msg)
            else:
                return transactions


    def __mass_assign(self, req, command, pid, bibrefs, ln):
        '''
        Will perform the actual mass action requested.
        Here: assign a bibref-bibrec pair to another person

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param command: the command is currently in process
        @type command: string
        @param pid: person id of the person targeted by the mass action
        @type pid: int
        @param bibrefs: list of bibref-bibrec pairs to identify the records
        @type bibrefs: list of strings
        @param ln: the language the web page shall be served in
        @type ln: string

        @return: a fully formatted html page to be displayed to the user
        @rtype: string
        '''
        session = get_session(req)
        uid = getUid(req)
        userinfo = "%s||%s" % (uid, req.remote_ip)

        if not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
            return page_not_authorized(
                        req=req,
                        referer="%s/person/%s" % (CFG_SITE_URL, pid),
                        text=("We're sorry. You are not authorized to "
                             "perform this action. If you think that "
                             "this is incorrect, please contact your "
                             "administrator."),
                        ln=ln)

        if command == "session":
            assign_from_pid = -1
            bibrefs_to_assign = []

            if "pid_batch_assign_papers" in session:
                assign_from_pid = session["pid_batch_assign_papers"]

            if "bibrecs_batch_assign_papers" in session:
                bibrefs_to_assign = session["bibrecs_batch_assign_papers"]

            transactions = self.__get_transaction_items(req, ln, assign_from_pid, "mconfirm", bibrefs_to_assign)

            if not isinstance(transactions, list):
                if isinstance(transactions, str):
                    return transactions
                else:
                    return self._error_page(req, ln, "transaction canceled: Broken Pipe")

            if [row for row in transactions if ((row['status'] == "touched") or
                                                (row["status"] == "not_allowed"))]:
                session.load()
                session["aid_mass_review_action"] = "mconfirm"
                session["aid_mass_review_transactions"] = transactions
                session["aid_mass_review_pid"] = pid
                session['person_message_show'] = True
                session['person_message'] = ("Remember that there is a "
                                             "transaction in progress! "
                                             "<a href='%s/person/batchprocess?"
                                             "mreviewed=True'>Click here to "
                                             "continue the process</a>" % CFG_SITE_URL)
                session.save()
                body = TEMPLATE.tmpl_author_transaction_review(req)

                return page(title="Review transaction",
                    metaheaderadd=self._scripts(),
                    body=body,
                    req=req,
                    language=ln)
            else:
                bibrefs = [row['bibref'] for row in transactions]

            if not bibrefs:
                self.__session_cleanup(req)
                session.load()
                session['person_message_show'] = True
                session['person_message'] = ("Mission to assign successful (no "
                                             "records have been updated)!")
                session.save()
                return redirect_to_url(req, "%s/person/%s"
                                       % (CFG_SITE_URL, pid))

            webapi.log(userinfo, pid, "assign", "from_pid", assign_from_pid)
            return self.__mass_confirm(req, pid, bibrefs, ln)

        else:
            session["mode_batch_assign_papers"] = True
            session["bibrecs_batch_assign_papers"] = bibrefs
            session["pid_batch_assign_papers"] = pid
            nameset = webapi.get_person_names_from_id(pid)
            namestr = "No name found."

            if nameset:
                namestr = ""
                for idx, name in enumerate(nameset):
                    if idx < 1:
                        namestr = "%s" % name[0]
                    else:
                        namestr = "%s, %s" % (namestr, name[0])

            session["name_batch_assign_papers"] = namestr
            session.save()
            body = TEMPLATE.tmpl_author_search(req, "", None)

            return page(title="Assign documents to a person",
                metaheaderadd=self._scripts(),
                body=body,
                req=req,
                language=ln)


    def __mass_confirm(self, req, pid, bibrefs, ln):
        '''
        Will perform the actual mass action requested.
        Here: confirm bibref-bibrec pairs to a person

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param pid: person id of the person targeted by the mass action
        @type pid: int
        @param bibrefs: list of bibref-bibrec pairs to identify the records
        @type bibrefs: list of strings
        @param ln: the language the web page shall be served in
        @type ln: string

        @return: a fully formatted html page to be displayed to the user
        @rtype: string
        '''
        transaction_id = 0
        session = get_session(req)
        uid = getUid(req)
        userinfo = "%s||%s" % (uid, req.remote_ip)

        if (not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OWN_PAPERS) and
            not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS)):
            return page_not_authorized(
                        req=req,
                        referer="%s/person/%s" % (CFG_SITE_URL, pid),
                        text=("We're sorry. You are not authorized to "
                             "perform this action. If you think that "
                             "this is incorrect, please contact your "
                             "administrator. [dbg: mass_confirmf]"),
                        ln=ln)

        transactions = self.__get_transaction_items(req, ln, pid, "mconfirm", bibrefs)

        if not isinstance(transactions, list):
            if isinstance(transactions, str):
                return transactions
            else:
                return self._error_page(req, ln, "transaction canceled: Broken Pipe")

        if [row for row in transactions if ((row['status'] == "touched") or
                                            (row["status"] == "not_allowed"))]:
            session.load()
            session["aid_mass_review_action"] = "mconfirm"
            session["aid_mass_review_transactions"] = transactions
            session["aid_mass_review_pid"] = pid
            session['person_message_show'] = True
            session['person_message'] = ("Remember that there is a "
                                         "transaction in progress! "
                                         "<a href='%s/person/batchprocess?"
                                         "mreviewed=True'>Click here to "
                                         "continue the process</a>" % CFG_SITE_URL)
            session.save()
            body = TEMPLATE.tmpl_author_transaction_review(req)

            return page(title="Review transaction",
                metaheaderadd=self._scripts(),
                body=body,
                req=req,
                language=ln)
        else:
            bibrefs = [row['bibref'] for row in transactions]

        if not bibrefs:
            self.__session_cleanup(req)
            session.load()
            session['person_message_show'] = True
            session['person_message'] = ("Mission to confirm successful (no "
                                         "records have been updated)!")
            session.save()
            if self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
                return redirect_to_url(req, "%s/person/%s"
                                   % (CFG_SITE_URL, pid))
            else:
                return redirect_to_url(req, "%s/person/claim" % CFG_SITE_URL)

        if not webapi.confirm_person_bibref_assignments(pid, bibrefs, uid):
            return self._error_page(req, ln, self.mass_fail_message)
        else:
            needing_review = webapi.get_review_needing_records(pid)
            for bibref in bibrefs:
                transaction_id = webapi.log(userinfo, pid, "confirm",
                                            "bibref", bibref,
                                            transactionid=transaction_id)
                try:
                    bibrec = int(bibref.split(',')[1])
                except (ValueError, IndexError, TypeError):
                    bibrec = -1
                if bibrec in needing_review:
                    webapi.del_review_needing_record(pid, bibrec)

            transaction_id = 0

            self.__session_cleanup(req)
            session.load()
            session['person_message_show'] = True
            session['person_message'] = ("Successfully confirmed %s "
                                         "assignments."
                                         % (len(bibrefs)))
            session.save()
            if self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
                return redirect_to_url(req, "%s/person/%s"
                                   % (CFG_SITE_URL, pid))
            else:
                return redirect_to_url(req, "%s/person/claim" % CFG_SITE_URL)


    def __mass_repeal(self, req, pid, bibrefs, ln):
        '''
        Will perform the actual mass action requested.
        Here: repeal bibref-bibrec pairs from a person

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param pid: person id of the person targeted by the mass action
        @type pid: int
        @param bibrefs: list of bibref-bibrec pairs to identify the records
        @type bibrefs: list of strings
        @param ln: the language the web page shall be served in
        @type ln: string

        @return: a fully formatted html page to be displayed to the user
        @rtype: string
        '''
        transaction_id = 0
        session = get_session(req)
        uid = getUid(req)
        userinfo = "%s||%s" % (uid, req.remote_ip)

        if (not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OWN_PAPERS) and
            not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS)):
            return page_not_authorized(
                        req=req,
                        referer="%s/person/%s" % (CFG_SITE_URL, pid),
                        text=("We're sorry. You are not authorized to "
                             "perform this action. If you think that "
                             "this is incorrect, please contact your "
                             "administrator."),
                        ln=ln)

        transactions = self.__get_transaction_items(req, ln, pid, "mrepeal", bibrefs)

        if not isinstance(transactions, list):
            if isinstance(transactions, str):
                return transactions
            else:
                return self._error_page(req, ln, "transaction canceled: Broken Pipe")

        if [row for row in transactions if ((row['status'] == "touched") or
                                            (row["status"] == "not_allowed"))]:
            session.load()
            session["aid_mass_review_action"] = "mrepeal"
            session["aid_mass_review_transactions"] = transactions
            session["aid_mass_review_pid"] = pid
            session['person_message_show'] = True
            session['person_message'] = ("Remember that there is a "
                                         "transaction in progress! "
                                         "<a href='%s/person/batchprocess?"
                                         "mreviewed=True'>Click here to "
                                         "continue the process</a>" % CFG_SITE_URL)
            session.save()
            body = TEMPLATE.tmpl_author_transaction_review(req)

            return page(title="Review transaction",
                metaheaderadd=self._scripts(),
                body=body,
                req=req,
                language=ln)
        else:
            bibrefs = [row['bibref'] for row in transactions]

        if not bibrefs:
            self.__session_cleanup(req)
            session.load()
            session['person_message_show'] = True
            session['person_message'] = ("Mission to repeal successful (no "
                                         "records have been updated)!")
            session.save()
            if self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
                return redirect_to_url(req, "%s/person/%s"
                                   % (CFG_SITE_URL, pid))
            else:
                return redirect_to_url(req, "%s/person/claim" % CFG_SITE_URL)

        if not webapi.repeal_person_bibref_assignments(pid, bibrefs, uid):
            return self._error_page(req, ln, self.mass_fail_message)
        else:
            for bibref in bibrefs:
                if transaction_id == 0:
                    transaction_id = webapi.log(userinfo, pid,
                                                "repeal",
                                                "bibref",
                                                bibref)
                else:
                    transaction_id = webapi.log(userinfo, pid,
                                                "repeal",
                                                "bibref",
                                                bibref,
                                         transactionid=transaction_id)
            transaction_id = 0
            self.__session_cleanup(req)
            session.load()
            session['person_message_show'] = True
            session['person_message'] = ("Successfully repealed %s "
                                         "assignments."
                                         % (len(bibrefs)))
            session.save()
            if self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
                return redirect_to_url(req, "%s/person/%s"
                                   % (CFG_SITE_URL, pid))
            else:
                return redirect_to_url(req, "%s/person/claim" % CFG_SITE_URL)


    def __mass_reset(self, req, pid, bibrefs, ln):
        '''
        Will perform the actual mass action requested.
        Here: reset bibref-bibrec pairs of a person

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param pid: person id of the person targeted by the mass action
        @type pid: int
        @param bibrefs: list of bibref-bibrec pairs to identify the records
        @type bibrefs: list of strings
        @param ln: the language the web page shall be served in
        @type ln: string

        @return: a fully formatted html page to be displayed to the user
        @rtype: string
        '''
        transaction_id = 0
        session = get_session(req)
        uid = getUid(req)
        userinfo = "%s||%s" % (uid, req.remote_ip)

        if (not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OWN_PAPERS) and
            not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS)):
            return page_not_authorized(
                        req=req,
                        referer="%s/person/%s" % (CFG_SITE_URL, pid),
                        text=("We're sorry. You are not authorized to "
                             "perform this action. If you think that "
                             "this is incorrect, please contact your "
                             "administrator."),
                        ln=ln)

        transactions = self.__get_transaction_items(req, ln, pid, "mreset", bibrefs)

        if not isinstance(transactions, list):
            if isinstance(transactions, str):
                return transactions
            else:
                return self._error_page(req, ln, "transaction canceled: Broken Pipe")

        if [row for row in transactions if ((row["status"] == "not_allowed"))]:
            session.load()
            session["aid_mass_review_action"] = "mreset"
            session["aid_mass_review_transactions"] = transactions
            session["aid_mass_review_pid"] = pid
            session['person_message_show'] = True
            session['person_message'] = ("Remember that there is a "
                                         "transaction in progress! "
                                         "<a href='%s/person/batchprocess?"
                                         "mreviewed=True'>Click here to "
                                         "continue the process</a>" % CFG_SITE_URL)
            session.save()
            body = TEMPLATE.tmpl_author_transaction_review(req)

            return page(title="Review transaction",
                metaheaderadd=self._scripts(),
                body=body,
                req=req,
                language=ln)
        else:
            bibrefs = [row['bibref'] for row in transactions]

        if not bibrefs:
            self.__session_cleanup(req)
            session.load()
            session['person_message_show'] = True
            session['person_message'] = ("Reset mission successful (no records"
                                         " have been updated)!")
            session.save()
            if self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
                return redirect_to_url(req, "%s/person/%s"
                                   % (CFG_SITE_URL, pid))
            else:
                return redirect_to_url(req, "%s/person/claim" % CFG_SITE_URL)

        if not webapi.reset_person_bibref_decisions(pid, bibrefs):
            return self._error_page(req, ln, self.mass_fail_message)
        else:
            for bibref in bibrefs:
                if transaction_id == 0:
                    transaction_id = webapi.log(userinfo, pid,
                                                "reset",
                                                "bibref",
                                                bibref)
                else:
                    transaction_id = webapi.log(userinfo, pid,
                                                "reset",
                                                "bibref",
                                                bibref,
                                         transactionid=transaction_id)
            transaction_id = 0
            self.__session_cleanup(req)
            session.load()
            session['person_message_show'] = True
            session['person_message'] = ("Successfully reset %s "
                                         "assignments."
                                         % (len(bibrefs)))
            session.save()
            if self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
                return redirect_to_url(req, "%s/person/%s"
                                   % (CFG_SITE_URL, pid))
            else:
                return redirect_to_url(req, "%s/person/claim" % CFG_SITE_URL)


    def __session_cleanup(self, req):
        '''
        Cleans the session from all bibauthorid specific settings and
        with that cancels any transaction currently in progress.

        @param req: Apache Request Object
        @type req: Apache Request Object
        '''
        session = get_session(req)

        if "mode_batch_assign_papers" in session:
            del(session["mode_batch_assign_papers"])
        if "bibrecs_batch_assign_papers" in session:
            del(session["bibrecs_batch_assign_papers"])
        if "pid_batch_assign_papers" in session:
            del(session["pid_batch_assign_papers"])
        if "aid_mass_review_action" in session:
            del(session["aid_mass_review_action"])
        if "aid_mass_review_transactions" in session:
            del(session["aid_mass_review_transactions"])
        if "aid_mass_review_pid" in session:
            del(session["aid_mass_review_pid"])
        if "person_message_show" in session:
            del(session["person_message_show"])
        if "person_message" in session:
            del(session["person_message"])
        if "name_batch_assign_papers" in session:
            del(session["name_batch_assign_papers"])
        if 'claimpaper_bibrecrefs_to_confirm' in session:
            del(session['claimpaper_bibrecrefs_to_confirm'])
        if 'claimpaper_bibrecrefs_needs_confirm' in session:
            del(session['claimpaper_bibrecrefs_needs_confirm'])
        if 'claimpaper_bibrecrefs_pid' in session:
            del(session['claimpaper_bibrecrefs_pid'])
        if "claimpaper_first_time_user" in session:
            del(session["claimpaper_first_time_user"])

        session.save()


    def search(self, req, form):
        '''
        Function used for searching a person based on a name with which the
        function is queried.

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a full page formatted in HTML
        @return: string
        '''
        max_num_show_papers = 5
        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'verbose': (int, 0),
             'q': (str, None)})

        ln = wash_language(argd['ln'])
        query = None
        recid = None
        nquery = None
        search_results = None
        title = "Author Search"

        if not self.__user_is_authorized(req, CLAIMPAPER_CLAIM_OTHERS_PAPERS):
            return page_not_authorized(
                        req=req,
                        referer="%s/person/search" % (CFG_SITE_URL),
                        text=("We're sorry. You are not authorized to "
                             "perform this action. If you think that "
                             "this is incorrect, please contact your "
                             "administrator."),
                        ln=ln)

        if 'q' in argd:
            if argd['q']:
                query = escape(argd['q'])

        if query:
            authors = []

            if query.count(":"):
                left, right = query.split(":")

                try:
                    recid = int(left)
                    nquery = str(right)
                except (ValueError, TypeError):
                    try:
                        recid = int(right)
                        nquery = str(left)
                    except (ValueError, TypeError):
                        recid = None
                        nquery = query

            else:
                nquery = query

            sorted_results = webapi.search_person_ids_by_name(nquery)

            for results in sorted_results:
                pid = results[0]
                authorpapers = webapi.get_papers_by_person_id(pid, -1)
                authorpapers = sorted(authorpapers, key=itemgetter(0),
                                      reverse=True)

                if (recid and
                    not (str(recid) in [row[0] for row in authorpapers])):
                    continue

                authors.append([results[0], results[1],
                                authorpapers[0:max_num_show_papers]])

            search_results = authors

        if recid and (len(search_results) == 1):
            return redirect_to_url(req, "/person/%s" % search_results[0][0])

        body = TEMPLATE.tmpl_author_search(req, query, search_results)

        return page(title=title,
                    metaheaderadd=self._scripts(),
                    body=body,
                    req=req,
                    language=ln)


    def status(self, req, form):
        '''
        Determines or sets the status of an assignment
        Possible actions are:
        - get_status: Will return a HTML scriptlet dexcibing the status
        - confirm_status: Will confirm an assignment and return a HTML
            scriptlet dexcibing the new status
        - repeal_status: Will repeal an assignment and return a HTML
            scriptlet dexcibing the new status
        - reset_status: Will reset an assignment and return a HTML
            scriptlet dexcibing the new status
        - json_editable: Will determine if a user may edit an assignment and
            if the assignment has been touched before. Will return a JSON
            object defining the status:
            - "not_authorized": User is not authorized to change the assignment
            - "touched": An assignment has been touched by another user
            - "OK": The assignment is ok for further processing

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param form: Parameters sent via GET or POST request
        @type form: dict

        @return: a json object or a html code scriptlet
        @return: string
        '''

        argd = wash_urlargd(
            form,
            {'ln': (str, CFG_SITE_LANG),
             'bibref': (str, None),
             'action': (str, "get_status"),
             'pid': (int, None)})

        ln = wash_language(argd['ln'])
        bibref = None
        action = None
        pid = None
        uid = getUid(req)
        userinfo = "%s||%s" % (uid, req.remote_ip)

        error_html = ("<p>We're sorry. An error occurred while handling "
                      "your request </p>")

        if 'bibref' in argd:
            bibref = argd['bibref']
        else:
            return error_html

        if 'action' in argd:
            action = argd['action']
        else:
            return error_html

        if 'pid' in argd:
            pid = argd['pid']
        else:
            return error_html

        attributed_html = {
            "True": TEMPLATE.tmpl_author_confirmed(req, bibref, pid),
            "False": TEMPLATE.tmpl_author_repealed(req, bibref, pid),
            "None": TEMPLATE.tmpl_author_undecided(req, bibref, pid)}

        if action == "get_status":
            status = webapi.get_paper_status(pid, bibref)

            if status == 2:
                return attributed_html["True"]
            elif status == -2:
                return attributed_html["False"]
            elif status > -2 and status < 2:
                return attributed_html["None"]
            else:
                return error_html

        elif action == "confirm_status":
            if not webapi.user_can_modify_paper(uid, bibref):
                return "You are not authorized to perform this action!"
            else:
                if webapi.confirm_person_bibref_assignments(pid, [bibref], uid):
                    webapi.log(userinfo, pid, "confirm", "bibref", bibref)
                    return attributed_html["True"]
                else:
                    return error_html

        elif action == "repeal_status":
            if not webapi.user_can_modify_paper(uid, bibref):
                return "You are not authorized to perform this action!"
            else:
                if webapi.repeal_person_bibref_assignments(pid, [bibref], uid):
                    webapi.log(userinfo, pid, "repeal", "bibref", bibref)
                    return attributed_html["False"]
                else:
                    return error_html

        elif action == "reset_status":
            if not webapi.user_can_modify_paper(uid, bibref):
                return "You are not authorized to perform this action!"
            else:
                if webapi.reset_person_bibref_decisions(pid, [bibref]):
                    webapi.log(userinfo, pid, "reset", "bibref", bibref)
                    return attributed_html["None"]
                else:
                    return error_html

        elif action == "json_editable":
            if not webapi.user_can_modify_paper(uid, bibref):
                return json.dumps({'editable': ["not_authorized"]})
            elif webapi.person_bibref_is_touched(pid, bibref):
                return json.dumps({'editable': ["touched"]})
            else:
                return json.dumps({'editable': ["OK"]})
        else:
            return "You have to specify an action for this method."


    def __user_is_authorized(self, req, action):
        '''
        Determines if a given user is authorized to perform a specified action

        @param req: Apache Request Object
        @type req: Apache Request Object
        @param action: the action the user wants to perform
        @type action: string

        @return: True if user is allowed to perform the action, False if not
        @rtype: boolean
        '''
        if not req:
            return False

        if not action:
            return False
        else:
            action = escape(action)

        uid = getUid(req)

        if not isinstance(uid, int):
            return False

        if uid == 0:
            return False

        allowance = [i[1] for i in acc_find_user_role_actions({'uid': uid})
                     if i[1] == action]

        if allowance:
            return True

        return False

    me = claim
    you = claim
