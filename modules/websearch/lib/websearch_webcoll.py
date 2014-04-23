## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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

"""Create Invenio collection cache."""

__revision__ = "$Id$"

import calendar
import copy
import sys
import cgi
import re
import os
import string
import time
import cPickle

from invenio.config import \
     CFG_CERN_SITE, \
     CFG_WEBSEARCH_INSTANT_BROWSE, \
     CFG_WEBSEARCH_NARROW_SEARCH_SHOW_GRANDSONS, \
     CFG_WEBSEARCH_I18N_LATEST_ADDITIONS, \
     CFG_CACHEDIR, \
     CFG_SITE_LANG, \
     CFG_SITE_NAME, \
     CFG_SITE_LANGS, \
     CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES, \
     CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, \
     CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS, \
     CFG_SCOAP3_SITE
from invenio.messages import gettext_set_language, language_list_long
from invenio.search_engine import search_pattern_parenthesised, get_creation_date, get_field_i18nname, collection_restricted_p, sort_records, EM_REPOSITORY
from invenio.dbquery import run_sql, Error, get_table_update_time
from invenio.bibrank_record_sorter import get_bibrank_methods
from invenio.dateutils import convert_datestruct_to_dategui, strftime
from invenio.bibformat import format_record
from invenio.shellutils import mymkdir
from invenio.intbitset import intbitset
from invenio.websearch_external_collections import \
     external_collection_load_states, \
     dico_collection_external_searches, \
     external_collection_sort_engine_by_name
from invenio.bibtask import task_init, task_get_option, task_set_option, \
    write_message, task_has_option, task_update_progress, \
    task_sleep_now_if_required
import invenio.template
websearch_templates = invenio.template.load('websearch')

from invenio.websearch_external_collections_searcher import external_collections_dictionary
from invenio.websearch_external_collections_config import CFG_EXTERNAL_COLLECTION_TIMEOUT
from invenio.websearch_external_collections_config import CFG_HOSTED_COLLECTION_TIMEOUT_NBRECS

## global vars
COLLECTION_HOUSE = {} # will hold collections we treat in this run of the program; a dict of {collname2, collobject1}, ...

# CFG_CACHE_LAST_UPDATED_TIMESTAMP_TOLERANCE -- cache timestamp
# tolerance (in seconds), to account for the fact that an admin might
# accidentally happen to edit the collection definitions at exactly
# the same second when some webcoll process was about to be started.
# In order to be safe, let's put an exaggerated timestamp tolerance
# value such as 20 seconds:
CFG_CACHE_LAST_UPDATED_TIMESTAMP_TOLERANCE = 20

# CFG_CACHE_LAST_UPDATED_TIMESTAMP_FILE -- location of the cache
# timestamp file:
CFG_CACHE_LAST_UPDATED_TIMESTAMP_FILE = "%s/collections/last_updated" % CFG_CACHEDIR

# CFG_CACHE_LAST_FAST_UPDATED_TIMESTAMP_FILE -- location of the cache
# timestamp file usef when running webcoll in the fast-mode.
CFG_CACHE_LAST_FAST_UPDATED_TIMESTAMP_FILE = "%s/collections/last_fast_updated" % CFG_CACHEDIR


def get_collection(colname):
    """Return collection object from the collection house for given colname.
       If does not exist, then create it."""
    if not COLLECTION_HOUSE.has_key(colname):
        colobject = Collection(colname)
        COLLECTION_HOUSE[colname] = colobject
    return COLLECTION_HOUSE[colname]

## auxiliary functions:
def is_selected(var, fld):
    "Checks if the two are equal, and if yes, returns ' selected'.  Useful for select boxes."
    if var == fld:
        return ' selected="selected"'
    else:
        return ""

def get_field(recID, tag):
    "Gets list of field 'tag' for the record with 'recID' system number."

    out = []
    digit = tag[0:2]

    bx = "bib%sx" % digit
    bibx = "bibrec_bib%sx" % digit
    query = "SELECT bx.value FROM %s AS bx, %s AS bibx WHERE bibx.id_bibrec='%s' AND bx.id=bibx.id_bibxxx AND bx.tag='%s'" \
            % (bx, bibx, recID, tag)
    res = run_sql(query)
    for row in res:
        out.append(row[0])
    return out

def check_nbrecs_for_all_external_collections():
    """Check if any of the external collections have changed their total number of records, aka nbrecs.
    Return True if any of the total numbers of records have changed and False if they're all the same."""
    res = run_sql("SELECT name FROM collection WHERE dbquery LIKE 'hostedcollection:%';")
    for row in res:
        coll_name = row[0]
        if (get_collection(coll_name)).check_nbrecs_for_external_collection():
            return True
    return False

class Collection:
    "Holds the information on collections (id,name,dbquery)."

    def __init__(self, name=""):
        "Creates collection instance by querying the DB configuration database about 'name'."
        self.calculate_reclist_run_already = 0 # to speed things up without much refactoring
        self.update_reclist_run_already = 0 # to speed things up without much refactoring
        self.reclist_updated_since_start = 0 # to check if webpage cache need rebuilding
        self.reclist_with_nonpublic_subcolls = intbitset()
        # temporary counters for the number of records in hosted collections
        self.nbrecs_tmp = None # number of records in a hosted collection
        self.nbrecs_from_hosted_collections = 0 # total number of records from
                                                # descendant hosted collections
        if not name:
            self.name = CFG_SITE_NAME # by default we are working on the home page
            self.id = 1
            self.dbquery = None
            self.nbrecs = None
            self.reclist = intbitset()
            self.old_reclist = intbitset()
            self.reclist_updated_since_start = 1
        else:
            self.name = name
            try:
                res = run_sql("""SELECT id,name,dbquery,nbrecs,reclist FROM collection
                                  WHERE name=%s""", (name,))
                if res:
                    self.id = res[0][0]
                    self.name = res[0][1]
                    self.dbquery = res[0][2]
                    self.nbrecs = res[0][3]
                    try:
                        self.reclist = intbitset(res[0][4])
                    except:
                        self.reclist = intbitset()
                        self.reclist_updated_since_start = 1
                else: # collection does not exist!
                    self.id = None
                    self.dbquery = None
                    self.nbrecs = None
                    self.reclist = intbitset()
                    self.reclist_updated_since_start = 1
                self.old_reclist = intbitset(self.reclist)
            except Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                sys.exit(1)

    def get_example_search_queries(self):
        """Returns list of sample search queries for this collection.
        """
        res = run_sql("""SELECT example.body FROM example
        LEFT JOIN collection_example on example.id=collection_example.id_example
        WHERE collection_example.id_collection=%s ORDER BY collection_example.score""", (self.id,))
        return [query[0] for query in res]

    def get_name(self, ln=CFG_SITE_LANG, name_type="ln", prolog="", epilog="", prolog_suffix=" ", epilog_suffix=""):
        """Return nicely formatted collection name for language LN.
        The NAME_TYPE may be 'ln' (=long name), 'sn' (=short name), etc."""
        out = prolog
        i18name = ""
        res = run_sql("SELECT value FROM collectionname WHERE id_collection=%s AND ln=%s AND type=%s", (self.id, ln, name_type))
        try:
            i18name += res[0][0]
        except IndexError:
            pass
        if i18name:
            out += i18name
        else:
            out += self.name
        out += epilog
        return out

    def get_collectionbox_name(self, ln=CFG_SITE_LANG, box_type="r"):
        """
        Return collection-specific labelling of 'Focus on' (regular
        collection), 'Narrow by' (virtual collection) and 'Latest
        addition' boxes.

        If translation for given language does not exist, use label
        for CFG_SITE_LANG. If no custom label is defined for
        CFG_SITE_LANG, return default label for the box.

        @param ln: the language of the label
        @param box_type: can be 'r' (=Narrow by), 'v' (=Focus on), 'l' (=Latest additions)
        """
        i18name = ""
        res = run_sql("SELECT value FROM collectionboxname WHERE id_collection=%s AND ln=%s AND type=%s", (self.id, ln, box_type))
        try:
            i18name = res[0][0]
        except IndexError:
            res = run_sql("SELECT value FROM collectionboxname WHERE id_collection=%s AND ln=%s AND type=%s", (self.id, CFG_SITE_LANG, box_type))
            try:
                i18name = res[0][0]
            except IndexError:
                pass

        if not i18name:
            # load the right message language
            _ = gettext_set_language(ln)
            if box_type == "v":
                i18name = _('Focus on:')
            elif box_type == "r":
                if CFG_SCOAP3_SITE:
                    i18name = _('Narrow by publisher/journal:')
                else:
                    i18name = _('Narrow by collection:')
            elif box_type == "l":
                i18name = _('Latest additions:')

        return i18name

    def get_ancestors(self):
        "Returns list of ancestors of the current collection."
        ancestors = []
        ancestors_ids = intbitset()
        id_son = self.id
        while 1:
            query = "SELECT cc.id_dad,c.name FROM collection_collection AS cc, collection AS c "\
                    "WHERE cc.id_son=%d AND c.id=cc.id_dad" % int(id_son)
            res = run_sql(query, None, 1)
            if res:
                col_ancestor = get_collection(res[0][1])
                # looking for loops
                if self.id in ancestors_ids:
                    write_message("Loop found in collection %s" % self.name, stream=sys.stderr)
                    raise OverflowError("Loop found in collection %s" % self.name)
                else:
                    ancestors.append(col_ancestor)
                    ancestors_ids.add(col_ancestor.id)
                    id_son = res[0][0]
            else:
                break
        ancestors.reverse()
        return ancestors

    def restricted_p(self):
        """Predicate to test if the collection is restricted or not.  Return the contect of the
         `restrited' column of the collection table (typically Apache group).  Otherwise return
         None if the collection is public."""

        if collection_restricted_p(self.name):
            return 1
        return None

    def get_sons(self, type='r'):
        "Returns list of direct sons of type 'type' for the current collection."
        sons = []
        id_dad = self.id
        query = "SELECT cc.id_son,c.name FROM collection_collection AS cc, collection AS c "\
                "WHERE cc.id_dad=%d AND cc.type='%s' AND c.id=cc.id_son ORDER BY score DESC, c.name ASC" % (int(id_dad), type)
        res = run_sql(query)
        for row in res:
            sons.append(get_collection(row[1]))
        return sons

    def get_descendants(self, type='r'):
        "Returns list of all descendants of type 'type' for the current collection."
        descendants = []
        descendant_ids = intbitset()
        id_dad = self.id
        query = "SELECT cc.id_son,c.name FROM collection_collection AS cc, collection AS c "\
                "WHERE cc.id_dad=%d AND cc.type='%s' AND c.id=cc.id_son ORDER BY score DESC" % (int(id_dad), type)
        res = run_sql(query)
        for row in res:
            col_desc = get_collection(row[1])
            # looking for loops
            if self.id in descendant_ids:
                write_message("Loop found in collection %s" % self.name, stream=sys.stderr)
                raise OverflowError("Loop found in collection %s" % self.name)
            else:
                descendants.append(col_desc)
                descendant_ids.add(col_desc.id)
                tmp_descendants = col_desc.get_descendants()
                for descendant in tmp_descendants:
                    descendant_ids.add(descendant.id)
                descendants += tmp_descendants
        return descendants

    def write_cache_file(self, filename='', filebody={}):
        "Write a file inside collection cache."
        # open file:
        dirname = "%s/collections" % (CFG_CACHEDIR)
        mymkdir(dirname)
        fullfilename = dirname + "/%s.html" % filename
        try:
            os.umask(022)
            f = open(fullfilename, "wb")
        except IOError, v:
            try:
                (code, message) = v
            except:
                code = 0
                message = v
            print "I/O Error: " + str(message) + " (" + str(code) + ")"
            sys.exit(1)
        # print user info:
        write_message("... creating %s" % fullfilename, verbose=6)
        # print page body:
        cPickle.dump(filebody, f, cPickle.HIGHEST_PROTOCOL)
        # close file:
        f.close()

    def update_webpage_cache(self, lang):
        """Create collection page header, navtrail, body (including left and right stripes) and footer, and
           call write_cache_file() afterwards to update the collection webpage cache."""

        ## precalculate latest additions for non-aggregate
        ## collections (the info is ln and as independent)
        if self.dbquery:
            if CFG_WEBSEARCH_I18N_LATEST_ADDITIONS:
                self.create_latest_additions_info(ln=lang)
            else:
                self.create_latest_additions_info()

        # load the right message language
        _ = gettext_set_language(lang)

        # create dictionary with data
        cache = {"te_portalbox" : self.create_portalbox(lang, 'te'),
                 "np_portalbox" : self.create_portalbox(lang, 'np'),
                 "ne_portalbox" : self.create_portalbox(lang, 'ne'),
                 "tp_portalbox" : self.create_portalbox(lang, "tp"),
                 "lt_portalbox" : self.create_portalbox(lang, "lt"),
                 "rt_portalbox" : self.create_portalbox(lang, "rt"),
                 "last_updated" : convert_datestruct_to_dategui(time.localtime(),
                                                                    ln=lang)}
        for aas in CFG_WEBSEARCH_ENABLED_SEARCH_INTERFACES: # do light, simple and advanced search pages:
            cache["navtrail_%s" % aas] = self.create_navtrail_links(aas, lang)
            cache["searchfor_%s" % aas] = self.create_searchfor(aas, lang)
            cache["narrowsearch_%s" % aas] = self.create_narrowsearch(aas, lang, 'r')
            cache["focuson_%s" % aas] = self.create_narrowsearch(aas, lang, "v")+ \
                        self.create_external_collections_box(lang)
            cache["instantbrowse_%s" % aas] = self.create_instant_browse(aas=aas, ln=lang)
        # write cache file
        self.write_cache_file("%s-ln=%s"%(self.name, lang), cache)

        return cache

    def create_navtrail_links(self, aas=CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, ln=CFG_SITE_LANG):
        """Creates navigation trail links, i.e. links to collection
        ancestors (except Home collection).  If aas==1, then links to
        Advanced Search interfaces; otherwise Simple Search.
        """

        dads = []
        for dad in self.get_ancestors():
            if dad.name != CFG_SITE_NAME: # exclude Home collection
                dads.append((dad.name, dad.get_name(ln)))

        return websearch_templates.tmpl_navtrail_links(
            aas=aas, ln=ln, dads=dads)


    def create_portalbox(self, lang=CFG_SITE_LANG, position="rt"):
        """Creates portalboxes of language CFG_SITE_LANG of the position POSITION by consulting DB configuration database.
           The position may be: 'lt'='left top', 'rt'='right top', etc."""
        out = ""
        query = "SELECT p.title,p.body FROM portalbox AS p, collection_portalbox AS cp "\
                " WHERE cp.id_collection=%d AND p.id=cp.id_portalbox AND cp.ln='%s' AND cp.position='%s' "\
                " ORDER BY cp.score DESC" % (self.id, lang, position)
        res = run_sql(query)
        for row in res:
            title, body = row[0], row[1]
            if title:
                out += websearch_templates.tmpl_portalbox(title = title,
                                             body = body)
            else:
                # no title specified, so print body ``as is'' only:
                out += body
        return out

    def create_narrowsearch(self, aas=CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, ln=CFG_SITE_LANG, type="r"):
        """Creates list of collection descendants of type 'type' under title 'title'.
        If aas==1, then links to Advanced Search interfaces; otherwise Simple Search.
        Suitable for 'Narrow search' and 'Focus on' boxes."""

        # get list of sons and analyse it
        sons = self.get_sons(type)

        if not sons:
            return ''

        # get descendents
        descendants = self.get_descendants(type)

        grandsons = []
        if CFG_WEBSEARCH_NARROW_SEARCH_SHOW_GRANDSONS:
            # load grandsons for each son
            for son in sons:
                grandsons.append(son.get_sons())

        # return ""
        return websearch_templates.tmpl_narrowsearch(
                 aas = aas,
                 ln = ln,
                 type = type,
                 father = self,
                 has_grandchildren = len(descendants)>len(sons),
                 sons = sons,
                 display_grandsons = CFG_WEBSEARCH_NARROW_SEARCH_SHOW_GRANDSONS,
                 grandsons = grandsons
               )

    def create_external_collections_box(self, ln=CFG_SITE_LANG):
        external_collection_load_states()
        if not dico_collection_external_searches.has_key(self.id):
            return ""

        engines_list = external_collection_sort_engine_by_name(dico_collection_external_searches[self.id])

        return websearch_templates.tmpl_searchalso(ln, engines_list, self.id)

    def create_latest_additions_info(self, rg=CFG_WEBSEARCH_INSTANT_BROWSE, ln=CFG_SITE_LANG):
        """
        Create info about latest additions that will be used for
        create_instant_browse() later.
        """
        self.latest_additions_info = []
        if self.nbrecs and self.reclist:
            # firstly, get last 'rg' records:
            recIDs = list(self.reclist)
            of = 'hb'
            # CERN hack begins: tweak latest additions for selected collections:
            if CFG_CERN_SITE:
                # alter recIDs list for some CERN collections:
                this_year = time.strftime("%Y", time.localtime())
                if self.name in ['CERN Yellow Reports','Videos']:
                    last_year = str(int(this_year) - 1)
                    # detect recIDs only from this and past year:
                    recIDs = list(self.reclist & \
                                  search_pattern_parenthesised(p='year:%s or year:%s' % \
                                                 (this_year, last_year)))
                elif self.name in ['VideosXXX']:
                    # detect recIDs only from this year:
                    recIDs = list(self.reclist & \
                                  search_pattern_parenthesised(p='year:%s' % this_year))
                elif self.name == 'CMS Physics Analysis Summaries' and \
                         1281585 in self.reclist:
                    # REALLY, REALLY temporary hack
                    recIDs = list(self.reclist)
                    recIDs.remove(1281585)
                # apply special filters:
                if self.name in ['Videos']:
                    # select only videos with movies:
                    recIDs = list(intbitset(recIDs) & \
                                  search_pattern_parenthesised(p='collection:"PUBLVIDEOMOVIE"'))
                    of = 'hvp'
                # sort some CERN collections specially:
                if self.name in ['Videos',
                                 'Video Clips',
                                 'Video Movies',
                                 'Video News',
                                 'Video Rushes',
                                 'Webcast',
                                 'ATLAS Videos',
                                 'Restricted Video Movies',
                                 'Restricted Video Rushes',
                                 'LHC First Beam Videos',
                                 'CERN openlab Videos']:
                    recIDs = sort_records(None, recIDs, '269__c')
                elif self.name in ['LHCb Talks']:
                    recIDs = sort_records(None, recIDs, 'reportnumber')
                elif self.name in ['CERN Yellow Reports']:
                    recIDs = sort_records(None, recIDs, '084__a')
            # CERN hack ends.

            total = len(recIDs)
            to_display = min(rg, total)

            for idx in range(total-1, total-to_display-1, -1):
                recid = recIDs[idx]
                self.latest_additions_info.append({'id': recid,
                                                   'format': format_record(recid, of, ln=ln),
                                                   'date': get_creation_date(recid, fmt="%Y-%m-%d<br />%H:%i")})
        return

    def create_instant_browse(self, rg=CFG_WEBSEARCH_INSTANT_BROWSE, aas=CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, ln=CFG_SITE_LANG):
        "Searches database and produces list of last 'rg' records."

        if self.restricted_p():
            return websearch_templates.tmpl_box_restricted_content(ln = ln)

        if str(self.dbquery).startswith("hostedcollection:"):
            return websearch_templates.tmpl_box_hosted_collection(ln = ln)

        if rg == 0:
            # do not show latest additions box
            return ""

        # CERN hack: do not display latest additions for some CERN collections:
        if CFG_CERN_SITE and self.name in ['Periodicals', 'Electronic Journals',
                                           'Press Office Photo Selection',
                                           'Press Office Video Selection']:
            return ""

        try:
            self.latest_additions_info
            latest_additions_info_p = True
        except:
            latest_additions_info_p = False

        if latest_additions_info_p:
            passIDs = []
            for idx in range(0, min(len(self.latest_additions_info), rg)):
                # CERN hack: display the records in a grid layout, so do not show the related links
                if CFG_CERN_SITE and self.name in ['Videos']:
                    passIDs.append({'id': self.latest_additions_info[idx]['id'],
                                    'body': self.latest_additions_info[idx]['format'],
                                    'date': self.latest_additions_info[idx]['date']})
                else:
                    passIDs.append({'id': self.latest_additions_info[idx]['id'],
                                    'body': self.latest_additions_info[idx]['format'] + \
                                     websearch_templates.tmpl_record_links(recid=self.latest_additions_info[idx]['id'],
                                                                              rm='citation',
                                                                              ln=ln),
                                    'date': self.latest_additions_info[idx]['date']})

            if self.nbrecs > rg:
                url = websearch_templates.build_search_url(
                    cc=self.name, jrec=rg+1, ln=ln, aas=aas)
            else:
                url = ""
            # CERN hack: display the records in a grid layout
            if CFG_CERN_SITE and self.name in ['Videos']:
                return websearch_templates.tmpl_instant_browse(
                    aas=aas, ln=ln, recids=passIDs, more_link=url, grid_layout=True, father=self)

            return websearch_templates.tmpl_instant_browse(
                aas=aas, ln=ln, recids=passIDs, more_link=url, father=self)

        return websearch_templates.tmpl_box_no_records(ln=ln)

    def create_searchoptions(self):
        "Produces 'Search options' portal box."
        box = ""
        query = """SELECT DISTINCT(cff.id_field),f.code,f.name FROM collection_field_fieldvalue AS cff, field AS f
                   WHERE cff.id_collection=%d AND cff.id_fieldvalue IS NOT NULL AND cff.id_field=f.id
                   ORDER BY cff.score DESC""" % self.id
        res = run_sql(query)
        if res:
            for row in res:
                field_id = row[0]
                field_code = row[1]
                field_name = row[2]
                query_bis = """SELECT fv.value,fv.name FROM fieldvalue AS fv, collection_field_fieldvalue AS cff
                               WHERE cff.id_collection=%d AND cff.type='seo' AND cff.id_field=%d AND fv.id=cff.id_fieldvalue
                               ORDER BY cff.score_fieldvalue DESC, cff.score DESC, fv.name ASC""" % (self.id, field_id)
                res_bis = run_sql(query_bis)
                if res_bis:
                    values = [{'value' : '', 'text' : 'any' + ' ' + field_name}] # FIXME: internationalisation of "any"
                    for row_bis in res_bis:
                        values.append({'value' : cgi.escape(row_bis[0], 1), 'text' : row_bis[1]})

                    box += websearch_templates.tmpl_select(
                                 fieldname = field_code,
                                 values = values
                                )
        return box

    def create_sortoptions(self, ln=CFG_SITE_LANG):
        """Produces 'Sort options' portal box."""


        # load the right message language
        _ = gettext_set_language(ln)

        box = ""
        query = """SELECT f.code,f.name FROM field AS f, collection_field_fieldvalue AS cff
                   WHERE id_collection=%d AND cff.type='soo' AND cff.id_field=f.id
                   ORDER BY cff.score DESC, f.name ASC""" % self.id
        values = [{'value' : '', 'text': "- %s -" % _("latest first")}]
        res = run_sql(query)
        if res:
            for row in res:
                values.append({'value' : row[0], 'text': get_field_i18nname(row[1], ln)})
        else:
            for tmp in ('title', 'author', 'report number', 'year'):
                values.append({'value' : tmp.replace(' ', ''), 'text' : get_field_i18nname(tmp, ln)})

        box = websearch_templates.tmpl_select(
                   fieldname = 'sf',
                   css_class = 'address',
                   values = values
                  )
        box += websearch_templates.tmpl_select(
                    fieldname = 'so',
                    css_class = 'address',
                    values = [
                              {'value' : 'a' , 'text' : _("asc.")},
                              {'value' : 'd' , 'text' : _("desc.")}
                             ]
                   )
        return box

    def create_rankoptions(self, ln=CFG_SITE_LANG):
        "Produces 'Rank options' portal box."

        # load the right message language
        _ = gettext_set_language(ln)

        values = [{'value' : '', 'text': "- %s %s -" % (string.lower(_("OR")), _("rank by"))}]
        for (code, name) in get_bibrank_methods(self.id, ln):
            values.append({'value' : code, 'text': name})
        box = websearch_templates.tmpl_select(
                   fieldname = 'rm',
                   css_class = 'address',
                   values = values
                  )
        return box

    def create_displayoptions(self, ln=CFG_SITE_LANG):
        "Produces 'Display options' portal box."

        # load the right message language
        _ = gettext_set_language(ln)

        values = []
        for i in ['10', '25', '50', '100', '250', '500']:
            values.append({'value' : i, 'text' : i + ' ' + _("results")})

        box = websearch_templates.tmpl_select(
                   fieldname = 'rg',
                   selected = str(CFG_WEBSEARCH_DEF_RECORDS_IN_GROUPS),
                   css_class = 'address',
                   values = values
                  )

        if self.get_sons():
            box += websearch_templates.tmpl_select(
                        fieldname = 'sc',
                        css_class = 'address',
                        values = [
                                  {'value' : '1' , 'text' : CFG_SCOAP3_SITE and _("split by publisher/journal") or _("split by collection")},
                                  {'value' : '0' , 'text' : _("single list")}
                                 ]
                       )
        return box

    def create_formatoptions(self, ln=CFG_SITE_LANG):
        "Produces 'Output format options' portal box."

        # load the right message language
        _ = gettext_set_language(ln)

        box = ""
        values = []
        query = """SELECT f.code,f.name FROM format AS f, collection_format AS cf
                   WHERE cf.id_collection=%d AND cf.id_format=f.id AND f.visibility='1'
                   ORDER BY cf.score DESC, f.name ASC"""  % self.id
        res = run_sql(query)
        if res:
            for row in res:
                values.append({'value' : row[0], 'text': row[1]})
        else:
            values.append({'value' : 'hb', 'text' : "HTML %s" % _("brief")})
        box = websearch_templates.tmpl_select(
                   fieldname = 'of',
                   css_class = 'address',
                   values = values
                  )
        return box

    def create_searchwithin_selection_box(self, fieldname='f', value='', ln='en'):
        """Produces 'search within' selection box for the current collection."""


        # get values
        query = """SELECT f.code,f.name FROM field AS f, collection_field_fieldvalue AS cff
                   WHERE cff.type='sew' AND cff.id_collection=%d AND cff.id_field=f.id
                   ORDER BY cff.score DESC, f.name ASC"""  % self.id
        res = run_sql(query)
        values = [{'value' : '', 'text' : get_field_i18nname("any field", ln)}]
        if res:
            for row in res:
                values.append({'value' : row[0], 'text' : get_field_i18nname(row[1], ln)})
        else:
            if CFG_CERN_SITE:
                for tmp in ['title', 'author', 'abstract', 'report number', 'year']:
                    values.append({'value' : tmp.replace(' ', ''), 'text' : get_field_i18nname(tmp, ln)})
            else:
                for tmp in ['title', 'author', 'abstract', 'keyword', 'report number', 'journal', 'year', 'fulltext', 'reference']:
                    values.append({'value' : tmp.replace(' ', ''), 'text' : get_field_i18nname(tmp, ln)})

        return websearch_templates.tmpl_searchwithin_select(
                                                fieldname = fieldname,
                                                ln = ln,
                                                selected = value,
                                                values = values
                                              )
    def create_searchexample(self):
        "Produces search example(s) for the current collection."
        out = "$collSearchExamples = getSearchExample(%d, $se);" % self.id
        return out

    def create_searchfor(self, aas=CFG_WEBSEARCH_DEFAULT_SEARCH_INTERFACE, ln=CFG_SITE_LANG):
        "Produces either Simple or Advanced 'Search for' box for the current collection."
        if aas == 1:
            return self.create_searchfor_advanced(ln)
        elif aas == 0:
            return self.create_searchfor_simple(ln)
        else:
            return self.create_searchfor_light(ln)

    def create_searchfor_light(self, ln=CFG_SITE_LANG):
        "Produces light 'Search for' box for the current collection."

        return websearch_templates.tmpl_searchfor_light(
          ln=ln,
          collection_id = self.name,
          collection_name=self.get_name(ln=ln),
          record_count=self.nbrecs,
          example_search_queries=self.get_example_search_queries(),
        )

    def create_searchfor_simple(self, ln=CFG_SITE_LANG):
        "Produces simple 'Search for' box for the current collection."

        return websearch_templates.tmpl_searchfor_simple(
          ln=ln,
          collection_id = self.name,
          collection_name=self.get_name(ln=ln),
          record_count=self.nbrecs,
          middle_option = self.create_searchwithin_selection_box(ln=ln),
        )

    def create_searchfor_advanced(self, ln=CFG_SITE_LANG):
        "Produces advanced 'Search for' box for the current collection."

        return websearch_templates.tmpl_searchfor_advanced(
          ln = ln,
          collection_id = self.name,
          collection_name=self.get_name(ln=ln),
          record_count=self.nbrecs,

          middle_option_1 = self.create_searchwithin_selection_box('f1', ln=ln),
          middle_option_2 = self.create_searchwithin_selection_box('f2', ln=ln),
          middle_option_3 = self.create_searchwithin_selection_box('f3', ln=ln),

          searchoptions = self.create_searchoptions(),
          sortoptions = self.create_sortoptions(ln),
          rankoptions = self.create_rankoptions(ln),
          displayoptions = self.create_displayoptions(ln),
          formatoptions = self.create_formatoptions(ln)
        )

    def calculate_reclist(self):
        """
        Calculate, set and return the (reclist,
                                       reclist_with_nonpublic_subcolls,
                                       nbrecs_from_hosted_collections)
        tuple for the given collection."""

        if str(self.dbquery).startswith("hostedcollection:"):
            # we don't normally use this function to calculate the reclist
            # for hosted collections. In case we do, recursively for a regular
            # ancestor collection, then quickly return the object attributes.
            return (self.reclist,
                    self.reclist_with_nonpublic_subcolls,
                    self.nbrecs)

        if self.calculate_reclist_run_already:
            # do we really have to recalculate? If not,
            # then return the object attributes
            return (self.reclist,
                    self.reclist_with_nonpublic_subcolls,
                    self.nbrecs_from_hosted_collections)

        write_message("... calculating reclist of %s" % self.name, verbose=6)

        reclist = intbitset() # will hold results for public sons only; good for storing into DB
        reclist_with_nonpublic_subcolls = intbitset() # will hold results for both public and nonpublic sons; good for deducing total
                                                      # number of documents
        nbrecs_from_hosted_collections = 0 # will hold the total number of records from descendant hosted collections

        if not self.dbquery:
            # A - collection does not have dbquery, so query recursively all its sons
            #     that are either non-restricted or that have the same restriction rules
            for coll in self.get_sons():
                coll_reclist,\
                coll_reclist_with_nonpublic_subcolls,\
                coll_nbrecs_from_hosted_collection = coll.calculate_reclist()

                if ((coll.restricted_p() is None) or
                    (coll.restricted_p() == self.restricted_p())):
                    # add this reclist ``for real'' only if it is public
                    reclist.union_update(coll_reclist)
                reclist_with_nonpublic_subcolls.union_update(coll_reclist_with_nonpublic_subcolls)

                # increment the total number of records from descendant hosted collections
                nbrecs_from_hosted_collections += coll_nbrecs_from_hosted_collection

        else:
            # B - collection does have dbquery, so compute it:
            #     (note: explicitly remove DELETED records)
            if CFG_CERN_SITE:
                reclist = search_pattern_parenthesised(None, self.dbquery + \
                                         ' -980__:"DELETED" -980__:"DUMMY"', ap=-9) #ap=-9 for allow queries containing hidden tags
            else:
                reclist = search_pattern_parenthesised(None, self.dbquery + ' -980__:"DELETED"', ap=-9) #ap=-9 allow queries containing hidden tags
            reclist_with_nonpublic_subcolls = copy.deepcopy(reclist)

        # store the results:
        self.nbrecs_from_hosted_collections = nbrecs_from_hosted_collections
        self.nbrecs = len(reclist_with_nonpublic_subcolls) + \
                      nbrecs_from_hosted_collections
        self.reclist = reclist
        self.reclist_with_nonpublic_subcolls = reclist_with_nonpublic_subcolls
        # last but not least, update the speed-up flag:
        self.calculate_reclist_run_already = 1
        # return the two sets, as well as
        # the total number of records from descendant hosted collections:
        return (self.reclist,
                self.reclist_with_nonpublic_subcolls,
                self.nbrecs_from_hosted_collections)

    def calculate_nbrecs_for_external_collection(self, timeout=CFG_EXTERNAL_COLLECTION_TIMEOUT):
        """Calculate the total number of records, aka nbrecs, for given external collection."""
        #if self.calculate_reclist_run_already:
            # do we have to recalculate?
            #return self.nbrecs
        #write_message("... calculating nbrecs of external collection %s" % self.name, verbose=6)
        if external_collections_dictionary.has_key(self.name):
            engine = external_collections_dictionary[self.name]
            if engine.parser:
                self.nbrecs_tmp = engine.parser.parse_nbrecs(timeout)
                if self.nbrecs_tmp >= 0: return self.nbrecs_tmp
                # the parse_nbrecs() function returns negative values for some specific cases
                # maybe we can handle these specific cases, some warnings or something
                # for now the total number of records remains silently the same
                else: return self.nbrecs
            else: write_message("External collection %s does not have a parser!" % self.name, verbose=6)
        else: write_message("External collection %s not found!" % self.name, verbose=6)
        return 0
        # last but not least, update the speed-up flag:
        #self.calculate_reclist_run_already = 1

    def check_nbrecs_for_external_collection(self):
        """Check if the external collections has changed its total number of records, aka nbrecs.
        Rerurns True if the total number of records has changed and False if it's the same"""

        write_message("*** self.nbrecs = %s / self.cal...ion = %s ***" % (str(self.nbrecs), str(self.calculate_nbrecs_for_external_collection())), verbose=6)
        write_message("*** self.nbrecs != self.cal...ion = %s ***" % (str(self.nbrecs != self.calculate_nbrecs_for_external_collection()),), verbose=6)
        return self.nbrecs != self.calculate_nbrecs_for_external_collection(CFG_HOSTED_COLLECTION_TIMEOUT_NBRECS)

    def set_nbrecs_for_external_collection(self):
        """Set this external collection's total number of records, aka nbrecs"""

        if self.calculate_reclist_run_already:
            # do we have to recalculate?
            return
        write_message("... calculating nbrecs of external collection %s" % self.name, verbose=6)
        if self.nbrecs_tmp:
            self.nbrecs = self.nbrecs_tmp
        else:
            self.nbrecs = self.calculate_nbrecs_for_external_collection(CFG_HOSTED_COLLECTION_TIMEOUT_NBRECS)
        # last but not least, update the speed-up flag:
        self.calculate_reclist_run_already = 1

    def update_reclist(self):
        "Update the record universe for given collection; nbrecs, reclist of the collection table."
        if self.update_reclist_run_already:
            # do we have to reupdate?
            return 0
        write_message("... updating reclist of %s (%s recs)" % (self.name, self.nbrecs), verbose=6)
        sys.stdout.flush()
        try:
            ## In principle we could skip this update if old_reclist==reclist
            ## however we just update it here in case of race-conditions.
            run_sql("UPDATE collection SET nbrecs=%s, reclist=%s WHERE id=%s",
                    (self.nbrecs, self.reclist.fastdump(), self.id))
            if self.old_reclist != self.reclist:
                self.reclist_updated_since_start = 1
            else:
                write_message("... no changes in reclist detected", verbose=6)
        except Error, e:
            print "Database Query Error %d: %s." % (e.args[0], e.args[1])
            sys.exit(1)
        # last but not least, update the speed-up flag:
        self.update_reclist_run_already = 1
        return 0

def perform_display_collection(colID, colname, aas, ln, em, show_help_boxes):
    """Returns the data needed to display a collection page
    The arguments are as follows:
    colID - id of the collection to display
    colname - name of the collection to display
    aas - 0 if simple search, 1 if advanced search
    ln - language of the page
    em - code to display just part of the page
    show_help_boxes - whether to show the help boxes or not"""
    # check and update cache if necessary
    cachedfile = open("%s/collections/%s-ln=%s.html" %
                      (CFG_CACHEDIR, colname, ln), "rb")
    try:
        data = cPickle.load(cachedfile)
    except ValueError:
        data = get_collection(colname).update_webpage_cache(ln)
    cachedfile.close()
    # check em value to return just part of the page
    if em != "":
        if EM_REPOSITORY["search_box"] not in em:
            data["searchfor_%s" % aas] = ""
        if EM_REPOSITORY["see_also_box"] not in em:
            data["focuson_%s" % aas] = ""
        if EM_REPOSITORY["all_portalboxes"] not in em:
            if EM_REPOSITORY["te_portalbox"] not in em:
                data["te_portalbox"] = ""
            if EM_REPOSITORY["np_portalbox"] not in em:
                data["np_portalbox"] = ""
            if EM_REPOSITORY["ne_portalbox"] not in em:
                data["ne_portalbox"] = ""
            if EM_REPOSITORY["tp_portalbox"] not in em:
                data["tp_portalbox"] = ""
            if EM_REPOSITORY["lt_portalbox"] not in em:
                data["lt_portalbox"] = ""
            if EM_REPOSITORY["rt_portalbox"] not in em:
                data["rt_portalbox"] = ""
    c_body = websearch_templates.tmpl_webcoll_body(ln, colID, data["te_portalbox"],
                data["searchfor_%s"%aas], data["np_portalbox"], data["narrowsearch_%s"%aas],
                data["focuson_%s"%aas], data["instantbrowse_%s"%aas], data["ne_portalbox"],
                em=="" or EM_REPOSITORY["body"] in em)
    if show_help_boxes <= 0:
        data["rt_portalbox"] = ""
    return (c_body, data["navtrail_%s"%aas], data["lt_portalbox"], data["rt_portalbox"],
            data["tp_portalbox"], data["te_portalbox"], data["last_updated"])

def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    date = time.time()
    shift_re = re.compile("([-\+]{0,1})([\d]+)([dhms])")
    factors = {"d":24*3600, "h":3600, "m":60, "s":1}
    m = shift_re.match(var)
    if m:
        sign = m.groups()[0] == "-" and -1 or 1
        factor = factors[m.groups()[2]]
        value = float(m.groups()[1])
        date = time.localtime(date + sign * factor * value)
        date = strftime(format_string, date)
    else:
        date = time.strptime(var, format_string)
        date = strftime(format_string, date)
    return date

def get_current_time_timestamp():
    """Return timestamp corresponding to the current time."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def compare_timestamps_with_tolerance(timestamp1,
                                      timestamp2,
                                      tolerance=0):
    """Compare two timestamps TIMESTAMP1 and TIMESTAMP2, of the form
       '2005-03-31 17:37:26'. Optionally receives a TOLERANCE argument
       (in seconds).  Return -1 if TIMESTAMP1 is less than TIMESTAMP2
       minus TOLERANCE, 0 if they are equal within TOLERANCE limit,
       and 1 if TIMESTAMP1 is greater than TIMESTAMP2 plus TOLERANCE.
    """
    # remove any trailing .00 in timestamps:
    timestamp1 = re.sub(r'\.[0-9]+$', '', timestamp1)
    timestamp2 = re.sub(r'\.[0-9]+$', '', timestamp2)
    # first convert timestamps to Unix epoch seconds:
    timestamp1_seconds = calendar.timegm(time.strptime(timestamp1, "%Y-%m-%d %H:%M:%S"))
    timestamp2_seconds = calendar.timegm(time.strptime(timestamp2, "%Y-%m-%d %H:%M:%S"))
    # now compare them:
    if timestamp1_seconds < timestamp2_seconds - tolerance:
        return -1
    elif timestamp1_seconds > timestamp2_seconds + tolerance:
        return 1
    else:
        return 0

def get_database_last_updated_timestamp():
    """Return last updated timestamp for collection-related and
       record-related database tables.
    """
    database_tables_timestamps = []
    database_tables_timestamps.append(get_table_update_time('bibrec'))
    ## In INSPIRE bibfmt is on innodb and there is not such configuration
    bibfmt_last_update = run_sql("SELECT max(last_updated) FROM bibfmt")
    if bibfmt_last_update and bibfmt_last_update[0][0] is not None:
        database_tables_timestamps.append(str(bibfmt_last_update[0][0]))
    try:
        database_tables_timestamps.append(get_table_update_time('idxWORD%'))
    except ValueError:
        # There are no indexes in the database. That's OK.
        pass
    database_tables_timestamps.append(get_table_update_time('collection%'))
    database_tables_timestamps.append(get_table_update_time('portalbox'))
    database_tables_timestamps.append(get_table_update_time('field%'))
    database_tables_timestamps.append(get_table_update_time('format%'))
    database_tables_timestamps.append(get_table_update_time('rnkMETHODNAME'))
    database_tables_timestamps.append(get_table_update_time('accROLE_accACTION_accARGUMENT', run_on_slave=True))
    return max(database_tables_timestamps)

def get_cache_last_updated_timestamp():
    """Return last updated cache timestamp."""
    try:
        f = open(CFG_CACHE_LAST_UPDATED_TIMESTAMP_FILE, "r")
    except:
        return "1970-01-01 00:00:00"
    timestamp = f.read()
    f.close()
    return timestamp

def set_cache_last_updated_timestamp(timestamp):
    """Set last updated cache timestamp to TIMESTAMP."""
    try:
        f = open(CFG_CACHE_LAST_UPDATED_TIMESTAMP_FILE, "w")
    except:
        pass
    f.write(timestamp)
    f.close()
    return timestamp

def main():
    """Main that construct all the bibtask."""
    task_init(authorization_action="runwebcoll",
            authorization_msg="WebColl Task Submission",
            description="""Description:
    webcoll updates the collection cache (record universe for a
    given collection plus web page elements) based on invenio.conf and DB
    configuration parameters. If the collection name is passed as an argument,
    only this collection's cache will be updated. If the recursive option is
    set as well, the collection's descendants will also be updated.\n""",
            help_specific_usage="  -c, --collection\t Update cache for the given "
                     "collection only. [all]\n"
                    "  -r, --recursive\t Update cache for the given collection and all its\n"
                    "\t\t\t descendants (to be used in combination with -c). [no]\n"
                    "  -q, --quick\t\t Skip webpage cache update for those collections whose\n"
                    "\t\t\t reclist was not changed. Note: if you use this option, it is advised\n"
                    "\t\t\t to schedule, e.g. a nightly 'webcoll --force'. [no]\n"
                    "  -f, --force\t\t Force update even if cache is up to date. [no]\n"
                    "  -p, --part\t\t Update only certain cache parts (1=reclist,"
                    " 2=webpage). [both]\n"
                    "  -l, --language\t Update pages in only certain language"
                    " (e.g. fr,it,...). [all]\n",
            version=__revision__,
            specific_params=("c:rqfp:l:", [
                    "collection=",
                    "recursive",
                    "quick",
                    "force",
                    "part=",
                    "language="
                ]),
            task_submit_elaborate_specific_parameter_fnc=task_submit_elaborate_specific_parameter,
            task_submit_check_options_fnc=task_submit_check_options,
            task_run_fnc=task_run_core)

def task_submit_elaborate_specific_parameter(key, value, opts, args):
    """ Given the string key it checks it's meaning, eventually using the value.
    Usually it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    eg:
    if key in ['-n', '--number']:
        self.options['number'] = value
        return True
    return False
    """
    if key in ("-c", "--collection"):
        task_set_option("collection", value)
    elif key in ("-r", "--recursive"):
        task_set_option("recursive", 1)
    elif key in ("-f", "--force"):
        task_set_option("force", 1)
    elif key in ("-q", "--quick"):
        task_set_option("quick", 1)
    elif key in ("-p", "--part"):
        task_set_option("part", int(value))
    elif key in ("-l", "--language"):
        languages = task_get_option("language", [])
        languages += value.split(',')
        for ln in languages:
            if ln not in CFG_SITE_LANGS:
                print 'ERROR: "%s" is not a recognized language code' % ln
                return False
        task_set_option("language", languages)
    else:
        return False
    return True

def task_submit_check_options():
    if task_has_option('collection'):
        coll = get_collection(task_get_option("collection"))
        if coll.id is None:
            print 'ERROR: Collection "%s" does not exist' % coll.name
            return False
    return True

def task_run_core():
    """ Reimplement to add the body of the task."""
##
## ------->--->time--->------>
##  (-1)  |   ( 0)    |  ( 1)
##        |     |     |
## [T.db] |  [T.fc]   | [T.db]
##        |     |     |
##        |<-tol|tol->|
##
## the above is the compare_timestamps_with_tolerance result "diagram"
## [T.db] stands fore the database timestamp and [T.fc] for the file cache timestamp
## ( -1, 0, 1) stand for the returned value
## tol stands for the tolerance in seconds
##
## When a record has been added or deleted from one of the collections the T.db becomes greater that the T.fc
## and when webcoll runs it is fully ran. It recalculates the reclists and nbrecs, and since it updates the
## collections db table it also updates the T.db. The T.fc is set as the moment the task started running thus
## slightly before the T.db (practically the time distance between the start of the task and the last call of
## update_reclist). Therefore when webcoll runs again, and even if no database changes have taken place in the
## meanwhile, it fully runs (because compare_timestamps_with_tolerance returns 0). This time though, and if
## no databases changes have taken place, the T.db remains the same while T.fc is updated and as a result if
## webcoll runs again it will not be fully ran
##
    task_run_start_timestamp = get_current_time_timestamp()
    colls = []
    # decide whether we need to run or not, by comparing last updated timestamps:
    write_message("Database timestamp is %s." % get_database_last_updated_timestamp(), verbose=3)
    write_message("Collection cache timestamp is %s." % get_cache_last_updated_timestamp(), verbose=3)
    if task_has_option("part"):
        write_message("Running cache update part %s only." % task_get_option("part"), verbose=3)
    if check_nbrecs_for_all_external_collections() or task_has_option("force") or \
    compare_timestamps_with_tolerance(get_database_last_updated_timestamp(),
                                        get_cache_last_updated_timestamp(),
                                        CFG_CACHE_LAST_UPDATED_TIMESTAMP_TOLERANCE) >= 0:
        ## either forced update was requested or cache is not up to date, so recreate it:
        # firstly, decide which collections to do:
        if task_has_option("collection"):
            coll = get_collection(task_get_option("collection"))
            colls.append(coll)
            if task_has_option("recursive"):
                r_type_descendants = coll.get_descendants(type='r')
                colls += r_type_descendants
                v_type_descendants = coll.get_descendants(type='v')
                colls += v_type_descendants
        else:
            res = run_sql("SELECT name FROM collection ORDER BY id")
            for row in res:
                colls.append(get_collection(row[0]))
        # secondly, update collection reclist cache:
        if task_get_option('part', 1) == 1:
            i = 0
            for coll in colls:
                i += 1
                write_message("%s / reclist cache update" % coll.name)
                if str(coll.dbquery).startswith("hostedcollection:"):
                    coll.set_nbrecs_for_external_collection()
                else:
                    coll.calculate_reclist()
                coll.update_reclist()
                task_update_progress("Part 1/2: done %d/%d" % (i, len(colls)))
                task_sleep_now_if_required(can_stop_too=True)
        # thirdly, update collection webpage cache:
        if task_get_option("part", 2) == 2:
            i = 0
            for coll in colls:
                i += 1
                if coll.reclist_updated_since_start or task_has_option("collection") or task_get_option("force") or not task_get_option("quick"):
                    write_message("%s / webpage cache update" % coll.name)
                    for lang in CFG_SITE_LANGS:
                        coll.update_webpage_cache(lang)
                else:
                    write_message("%s / webpage cache seems not to need an update and --quick was used" % coll.name, verbose=2)
                task_update_progress("Part 2/2: done %d/%d" % (i, len(colls)))
                task_sleep_now_if_required(can_stop_too=True)

        # finally update the cache last updated timestamp:
        # (but only when all collections were updated, not when only
        # some of them were forced-updated as per admin's demand)
        if not task_has_option("collection"):
            set_cache_last_updated_timestamp(task_run_start_timestamp)
            write_message("Collection cache timestamp is set to %s." % get_cache_last_updated_timestamp(), verbose=3)
    else:
        ## cache up to date, we don't have to run
        write_message("Collection cache is up to date, no need to run.")
    ## we are done:
    return True

### okay, here we go:
if __name__ == '__main__':
    main()
