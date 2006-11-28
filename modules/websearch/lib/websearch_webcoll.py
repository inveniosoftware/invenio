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

"""Creates CDS Invenio collection specific pages, using WML and MySQL configuration tables."""

__revision__ = "$Id$"

import calendar
import copy
import getopt
import getpass
import marshal
import signal
import sys
import cgi
import sre
import os
import string
import zlib
import Numeric
import time
import traceback

from invenio.config import \
     CFG_CERN_SITE, \
     CFG_WEBSEARCH_INSTANT_BROWSE, \
     CFG_WEBSEARCH_NARROW_SEARCH_SHOW_GRANDSONS, \
     cachedir, \
     cdslang, \
     cdsname, \
     weburl
from invenio.messages import gettext_set_language, language_list_long
from invenio.search_engine import HitSet, search_pattern, get_creation_date, get_field_i18nname
from invenio.dbquery import run_sql, escape_string, Error, get_table_update_time
from invenio.access_control_engine import acc_authorize_action
from invenio.bibrank_record_sorter import get_bibrank_methods
from invenio.dateutils import convert_datestruct_to_dategui
from invenio.bibformat import format_record
from invenio.websearch_external_collections import \
     external_collection_load_states, \
     dico_collection_external_searches, \
     external_collection_sort_engine_by_name 
import invenio.template
websearch_templates = invenio.template.load('websearch')

## global vars
collection_house = {} # will hold collections we treat in this run of the program; a dict of {collname2, collobject1}, ...
options = {} # will hold task options

# cfg_cache_last_updated_timestamp_tolerance -- cache timestamp
# tolerance (in seconds), to account for the fact that an admin might
# accidentally happen to edit the collection definitions at exactly
# the same second when some webcoll process was about to be started.
# In order to be safe, let's put an exaggerated timestamp tolerance
# value such as 20 seconds:
cfg_cache_last_updated_timestamp_tolerance = 20

# cfg_cache_last_updated_timestamp_file -- location of the cache
# timestamp file:
cfg_cache_last_updated_timestamp_file = "%s/collections/last_updated" % cachedir

def get_collection(colname):
    """Return collection object from the collection house for given colname.
       If does not exist, then create it."""
    if not collection_house.has_key(colname):
        colobject = Collection(colname)
        collection_house[colname] = colobject
    return collection_house[colname]

## auxiliary functions:
def mymkdir(newdir, mode=0777):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mymkdir(head, mode)
        if tail:
            os.umask(022)
            os.mkdir(newdir, mode)

def is_selected(var, fld):
    "Checks if the two are equal, and if yes, returns ' selected'.  Useful for select boxes."
    if var == fld:
        return " selected"
    else:
        return ""

def write_message(msg, stream=sys.stdout):
    """Write message and flush output stream (may be sys.stdout or sys.stderr).  Useful for debugging stuff."""
    if stream == sys.stdout or stream == sys.stderr:
        stream.write(time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
        stream.write("%s\n" % msg)
        stream.flush()
    else:
        sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)
    return

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

class Collection:
    "Holds the information on collections (id,name,dbquery)."

    def __init__(self, name=""):
        "Creates collection instance by querying the DB configuration database about 'name'."
        self.calculate_reclist_run_already = 0 # to speed things up wihtout much refactoring
        self.update_reclist_run_already = 0 # to speed things up wihtout much refactoring
        self.reclist_with_nonpublic_subcolls = HitSet()
        if not name:
            self.name = cdsname # by default we are working on the home page
            self.id = 1
            self.dbquery = None
            self.nbrecs = None
            self.reclist = HitSet()
        else:
            self.name = name
            query = "SELECT id,name,dbquery,nbrecs,reclist FROM collection WHERE name='%s'" % escape_string(name)
            try:
                res = run_sql(query, None, 1)
                if res:
                    self.id = res[0][0]
                    self.name = res[0][1]
                    self.dbquery = res[0][2]
                    self.nbrecs = res[0][3]
                    try:
                        self.reclist = HitSet(Numeric.loads(zlib.decompress(res[0][5])))
                    except:
                        self.reclist = HitSet()
                else: # collection does not exist!
                    self.id = None
                    self.dbquery = None
                    self.nbrecs = None
                    self.reclist = HitSet()
            except Error, e:
                print "Error %d: %s" % (e.args[0], e.args[1])
                sys.exit(1)

    def get_name(self, ln=cdslang, name_type="ln", prolog="", epilog="", prolog_suffix=" ", epilog_suffix=""):
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

    def get_ancestors(self):
        "Returns list of ancestors of the current collection."
        ancestors = []
        id_son = self.id
        while 1:
            query = "SELECT cc.id_dad,c.name FROM collection_collection AS cc, collection AS c "\
                    "WHERE cc.id_son=%d AND c.id=cc.id_dad" % int(id_son)
            res = run_sql(query, None, 1)
            if res:
                col_ancestor = get_collection(res[0][1])
                ancestors.append(col_ancestor)
                id_son = res[0][0]
            else:
                break
        ancestors.reverse()
        return ancestors

    def restricted_p(self):
        """Predicate to test if the collection is restricted or not.  Return the contect of the
         `restrited' column of the collection table (typically Apache group).  Otherwise return
         None if the collection is public."""
        out = None
        query = "SELECT restricted FROM collection WHERE id=%d" % self.id
        res = run_sql(query, None, 1)
        try:
            out = res[0][0]
        except:
            pass
        return out

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
        id_dad = self.id
        query = "SELECT cc.id_son,c.name FROM collection_collection AS cc, collection AS c "\
                "WHERE cc.id_dad=%d AND cc.type='%s' AND c.id=cc.id_son ORDER BY score DESC" % (int(id_dad), type)
        res = run_sql(query)
        for row in res:
            col_desc = get_collection(row[1])
            descendants.append(col_desc)
            descendants += col_desc.get_descendants()
        return descendants

    def write_cache_file(self, filename='', filebody=''):
        "Write a file inside collection cache."
        # open file:
        dirname = "%s/collections/%d" % (cachedir, self.id)
        mymkdir(dirname)
        fullfilename = dirname + "/%s.html" % filename
        try:
            os.umask(022)
            f = open(fullfilename, "w")
        except IOError, v:
            try:
                (code, message) = v
            except:
                code = 0
                message = v
            print "I/O Error: " + str(message) + " (" + str(code) + ")"
            sys.exit(1)
        # print user info:
        if options["verbose"] >= 6:
            write_message("... creating %s" % fullfilename)
        sys.stdout.flush()
        # print page body:
        f.write(filebody)
        # close file:
        f.close()

    def update_webpage_cache(self):
        """Create collection page header, navtrail, body (including left and right stripes) and footer, and
           call write_cache_file() afterwards to update the collection webpage cache."""
        ## do this for each language:
        for lang, lang_fullname in language_list_long():

            # load the right message language
            _ = gettext_set_language(lang)

            ## first, update navtrail:
            for as in range(0, 2):
                self.write_cache_file("navtrail-as=%s-ln=%s" % (as, lang), self.create_navtrail_links(as, lang))
            ## second, update page body:
            for as in range(0, 2): # do both simple search and advanced search pages:
                body = websearch_templates.tmpl_webcoll_body(
                         ln=lang, collection=self.name,
                         te_portalbox = self.create_portalbox(lang, 'te'),
                         searchfor = self.create_searchfor(as, lang),
                         np_portalbox = self.create_portalbox(lang, 'np'),
                         narrowsearch = self.create_narrowsearch(as, lang, 'r'),
                         focuson = self.create_narrowsearch(as, lang, "v") + self.create_external_collections_box(),
                         instantbrowse = self.create_instant_browse(as=as, ln=lang),
                         ne_portalbox = self.create_portalbox(lang, 'ne')
                       )
                self.write_cache_file("body-as=%s-ln=%s" % (as, lang), body)
            ## third, write portalboxes:
            self.write_cache_file("portalbox-tp-ln=%s" % lang, self.create_portalbox(lang, "tp"))
            self.write_cache_file("portalbox-te-ln=%s" % lang, self.create_portalbox(lang, "te"))
            self.write_cache_file("portalbox-lt-ln=%s" % lang, self.create_portalbox(lang, "lt"))
            self.write_cache_file("portalbox-rt-ln=%s" % lang, self.create_portalbox(lang, "rt"))
            ## fourth, write 'last updated' information:
            self.write_cache_file("last-updated-ln=%s" % lang,
                                  convert_datestruct_to_dategui(time.localtime(),
                                                                ln=lang))
        return

    def create_navtrail_links(self, as=0, ln=cdslang):
        """Creates navigation trail links, i.e. links to collection
        ancestors (except Home collection).  If as==1, then links to
        Advanced Search interfaces; otherwise Simple Search.
        """
        
        dads = []
        for dad in self.get_ancestors():
            if dad.name != cdsname: # exclude Home collection
                dads.append((dad.name, dad.get_name(ln)))

        return websearch_templates.tmpl_navtrail_links(
            as=as, ln=ln, dads=dads)


    def create_portalbox(self, lang=cdslang, position="rt"):
        """Creates portalboxes of language CDSLANG of the position POSITION by consulting DB configuration database.
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

    def create_narrowsearch(self, as=0, ln=cdslang, type="r"):
        """Creates list of collection descendants of type 'type' under title 'title'.
        If as==1, then links to Advanced Search interfaces; otherwise Simple Search.
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
                 as = as,
                 ln = ln,
                 type = type,
                 father = self,
                 has_grandchildren = len(descendants)>len(sons),
                 sons = sons,
                 display_grandsons = CFG_WEBSEARCH_NARROW_SEARCH_SHOW_GRANDSONS,
                 grandsons = grandsons
               )

    def create_external_collections_box(self, ln=cdslang):
        external_collection_load_states()
        if not dico_collection_external_searches.has_key(self.id):
            return ""

        engines_list = external_collection_sort_engine_by_name(dico_collection_external_searches[self.id])

        return websearch_templates.tmpl_searchalso(ln, engines_list, self.id)

    def create_instant_browse(self, rg=CFG_WEBSEARCH_INSTANT_BROWSE, as=0, ln=cdslang):
        "Searches database and produces list of last 'rg' records."
        
        if self.restricted_p():
            return websearch_templates.tmpl_box_restricted_content(ln = ln)
        
        else:
            if self.nbrecs and self.reclist:
                # firstly, get last 'rg' records:
                recIDs = Numeric.nonzero(self.reclist._set)
                passIDs = []

                total = len(recIDs)
                to_display = min(rg, total)
                
                for idx in range(total-1, total-to_display-1, -1):
                    recid = recIDs[idx]

                    passIDs.append({'id': recid,
                                    'body': format_record(recid, "hb", ln=ln) + \
                                            websearch_templates.tmpl_record_links(weburl=weburl,
                                                                                  recid=recid,
                                                                                  ln=ln),
                                    'date': get_creation_date(recid, fmt="%Y-%m-%d<br>%H:%i")})
                    
                if self.nbrecs > rg:
                    url = websearch_templates.build_search_url(
                        cc=self.name, jrec=rg+1, ln=ln, as=as)
                else:
                    url = ""
                    
                return websearch_templates.tmpl_instant_browse(
                                 as=as, ln=ln, recids=passIDs, more_link=url)

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
                    values = [{'value' : '', 'text' : 'any' + field_name}] # FIXME: internationalisation of "any"
                    for row_bis in res_bis:
                        values.append({'value' : cgi.escape(row_bis[0], 1), 'text' : row_bis[1]})

                    box += websearch_templates.tmpl_select(
                                 fieldname = field_code,
                                 values = values
                                )
        return box

    def create_sortoptions(self, ln=cdslang):
        "Produces 'Sort options' portal box."

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
                values.append({'value' : row[0], 'text': row[1]})
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

    def create_rankoptions(self, ln=cdslang):
        "Produces 'Rank options' portal box."

        # load the right message language
        _ = gettext_set_language(ln)

        values = [{'value' : '', 'text': "- %s %s -" % (string.lower(_("OR")), _("rank by"))}]
        for (code, name) in get_bibrank_methods(self.id, ln):
            values.append({'value' : code, 'text': name})
        box = websearch_templates.tmpl_select(
                   fieldname = 'sf',
                   css_class = 'address',
                   values = values
                  )
        return box

    def create_displayoptions(self, ln=cdslang):
        "Produces 'Display options' portal box."

        # load the right message language
        _ = gettext_set_language(ln)

        values = []
        for i in ['10', '25', '50', '100', '250', '500']:
            values.append({'value' : i, 'text' : i + ' ' + _("results")})

        box = websearch_templates.tmpl_select(
                   fieldname = 'rg',
                   css_class = 'address',
                   values = values
                  )

        if self.get_sons():
            box += websearch_templates.tmpl_select(
                        fieldname = 'sc',
                        css_class = 'address',
                        values = [
                                  {'value' : '1' , 'text' : _("split by collection")},
                                  {'value' : '0' , 'text' : _("single list")}
                                 ]
                       )
        return box

    def create_formatoptions(self, ln=cdslang):
        "Produces 'Output format options' portal box."

        # load the right message language
        _ = gettext_set_language(ln)

        box = ""
        values = []
        query = """SELECT f.code,f.name FROM format AS f, collection_format AS cf
                   WHERE cf.id_collection=%d AND cf.id_format=f.id ORDER BY cf.score DESC, f.name ASC"""  % self.id
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
        "Produces 'search within' selection box for the current collection."

        # get values
        query = """SELECT f.code,f.name FROM field AS f, collection_field_fieldvalue AS cff
                   WHERE cff.type='sew' AND cff.id_collection=%d AND cff.id_field=f.id
                   ORDER BY cff.score DESC, f.name ASC"""  % self.id
        res = run_sql(query)
        values = [{'value' : '', 'text' : get_field_i18nname("any field", ln)}]
        if res:
            for row in res:
                values.append({'value' : row[0], 'text' : row[1]})
        else:
            if CFG_CERN_SITE:
                for tmp in ['title', 'author', 'abstract', 'report number', 'year']:
                    values.append({'value' : tmp.replace(' ', ''), 'text' : get_field_i18nname(tmp, ln)})
            else:
                for tmp in ['title', 'author', 'abstract', 'keyword', 'report number', 'year', 'fulltext', 'reference']:
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

    def create_searchfor(self, as=0, ln=cdslang):
        "Produces either Simple or Advanced 'Search for' box for the current collection."
        if as == 1:
            return self.create_searchfor_advanced(ln)
        else:
            return self.create_searchfor_simple(ln)

    def create_searchfor_simple(self, ln=cdslang):
        "Produces simple 'Search for' box for the current collection."

        return websearch_templates.tmpl_searchfor_simple(
          ln=ln,
          collection_id = self.name,
          collection_name=self.get_name(ln=ln),
          record_count=self.nbrecs,
          middle_option = self.create_searchwithin_selection_box(ln=ln),
        )

    def create_searchfor_advanced(self, ln=cdslang):
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
        """Calculate, set and return the (reclist, reclist_with_nonpublic_subcolls) tuple for given collection."""
        if self.calculate_reclist_run_already:
            # do we have to recalculate?
            return (self.reclist, self.reclist_with_nonpublic_subcolls)
        if options["verbose"] >= 6:
            write_message("... calculating reclist of %s" % self.name)
        reclist = HitSet() # will hold results for public sons only; good for storing into DB
        reclist_with_nonpublic_subcolls = HitSet() # will hold results for both public and nonpublic sons; good for deducing total
                                                   # number of documents
        if not self.dbquery:
            # A - collection does not have dbquery, so query recursively all its sons
            #     that are either non-restricted or that have the same restriction rules
            for coll in self.get_sons():
                coll_reclist, coll_reclist_with_nonpublic_subcolls = coll.calculate_reclist()
                if ((coll.restricted_p() is None) or
                    (coll.restricted_p() == self.restricted_p())):
                    # add this reclist ``for real'' only if it is public
                    reclist.union(coll_reclist)
                reclist_with_nonpublic_subcolls.union(coll_reclist_with_nonpublic_subcolls)
        else:
            # B - collection does have dbquery, so compute it:
            reclist = search_pattern(None, self.dbquery)
            reclist_with_nonpublic_subcolls = copy.deepcopy(reclist)
        # deduce the number of records:
        reclist.calculate_nbhits()
        reclist_with_nonpublic_subcolls.calculate_nbhits()
        # store the results:
        self.nbrecs = reclist_with_nonpublic_subcolls._nbhits
        self.reclist = reclist
        self.reclist_with_nonpublic_subcolls = reclist_with_nonpublic_subcolls
        # last but not least, update the speed-up flag:
        self.calculate_reclist_run_already = 1
        # return the two sets:
        return (self.reclist, self.reclist_with_nonpublic_subcolls)

    def update_reclist(self):
        "Update the record universe for given collection; nbrecs, reclist of the collection table."
        if self.update_reclist_run_already:
            # do we have to reupdate?
            return 0
        if options["verbose"] >= 6:
            write_message("... updating reclist of %s (%s recs)" % (self.name, self.nbrecs))
        sys.stdout.flush()
        try:
            query = "UPDATE collection SET nbrecs=%d, reclist='%s' WHERE id=%d" % \
                    (self.nbrecs, escape_string(zlib.compress(Numeric.dumps(self.reclist._set))), self.id)
            run_sql(query)
            self.reclist_updated_since_start = 1
        except Error, e:
            print "Database Query Error %d: %s." % (e.args[0], e.args[1])
            sys.exit(1)
        # last but not least, update the speed-up flag:
        self.update_reclist_run_already = 1
        return 0

def get_datetime(var, format_string="%Y-%m-%d %H:%M:%S"):
    """Returns a date string according to the format string.
       It can handle normal date strings and shifts with respect
       to now."""
    date = time.time()
    shift_re = sre.compile("([-\+]{0,1})([\d]+)([dhms])")
    factors = {"d":24*3600, "h":3600, "m":60, "s":1}
    m = shift_re.match(var)
    if m:
        sign = m.groups()[0] == "-" and -1 or 1
        factor = factors[m.groups()[2]]
        value = float(m.groups()[1])
        date = time.localtime(date + sign * factor * value)
        date = time.strftime(format_string, date)
    else:
        date = time.strptime(var, format_string)
        date = time.strftime(format_string, date)
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
    timestamp1 = sre.sub(r'\.[0-9]+$', '', timestamp1)
    timestamp2 = sre.sub(r'\.[0-9]+$', '', timestamp2)
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
    database_tables_timestamps.append(get_table_update_time('bibfmt'))
    database_tables_timestamps.append(get_table_update_time('idxWORD%'))
    database_tables_timestamps.append(get_table_update_time('collection%'))
    database_tables_timestamps.append(get_table_update_time('portalbox'))
    database_tables_timestamps.append(get_table_update_time('field%'))
    database_tables_timestamps.append(get_table_update_time('format%'))
    database_tables_timestamps.append(get_table_update_time('rnkMETHODNAME'))
    return max(database_tables_timestamps)

def get_cache_last_updated_timestamp():
    """Return last updated cache timestamp."""
    try:
        f = open(cfg_cache_last_updated_timestamp_file, "r")
    except:
        return "1970-01-01 00:00:00"
    timestamp = f.read()
    f.close()
    return timestamp

def set_cache_last_updated_timestamp(timestamp):
    """Set last updated cache timestamp to TIMESTAMP."""
    try:
        f = open(cfg_cache_last_updated_timestamp_file, "w")
    except:
        pass
    f.write(timestamp)
    f.close()
    return timestamp

def task_sig_sleep(sig, frame):
    """Signal handler for the 'sleep' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_sleep(), got signal %s frame %s" % (sig, frame))
    write_message("sleeping...")
    task_update_status("SLEEPING")
    signal.pause() # wait for wake-up signal

def task_sig_wakeup(sig, frame):
    """Signal handler for the 'wakeup' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_wakeup(), got signal %s frame %s" % (sig, frame))
    write_message("continuing...")
    task_update_status("CONTINUING")

def task_sig_stop(sig, frame):
    """Signal handler for the 'stop' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_stop(), got signal %s frame %s" % (sig, frame))
    write_message("stopping...")
    task_update_status("STOPPING")
    pass # FIXME: is there anything to be done?
    task_update_status("STOPPED")
    sys.exit(0)

def task_sig_suicide(sig, frame):
    """Signal handler for the 'suicide' signal sent by BibSched."""
    if options["verbose"] >= 9:
        write_message("task_sig_suicide(), got signal %s frame %s" % (sig, frame))
    write_message("suiciding myself now...")
    task_update_status("SUICIDING")
    write_message("suicided")
    task_update_status("SUICIDED")
    sys.exit(0)

def task_sig_unknown(sig, frame):
    """Signal handler for the other unknown signals sent by shell or user."""
    # do nothing for unknown signals:
    write_message("unknown signal %d (frame %s) ignored" % (sig, frame)) 

def authenticate(user, header="WebColl Task Submission", action="runwebcoll"):
    """Authenticate the user against the user database.
       Check for its password, if it exists.
       Check for action access rights.
       Return user name upon authorization success,
       do system exit upon authorization failure.
       """
    print header
    print "=" * len(header)
    if user == "":
        print >> sys.stdout, "\rUsername: ",
        user = string.strip(string.lower(sys.stdin.readline()))
    else:
        print >> sys.stdout, "\rUsername:", user
    ## first check user pw:
    res = run_sql("select id,password from user where email=%s", (user,), 1) + \
          run_sql("select id,password from user where nickname=%s", (user,), 1)
    if not res:
        print "Sorry, %s does not exist." % user
        sys.exit(1)
    else:
        (uid_db, password_db) = res[0]
        if password_db:
            password_entered = getpass.getpass()
            if password_db == password_entered:
                pass
            else:
                print "Sorry, wrong credentials for %s." % user
                sys.exit(1)
        ## secondly check authorization for the action:
        (auth_code, auth_message) = acc_authorize_action(uid_db, action)
        if auth_code != 0:
            print auth_message
            sys.exit(1)
    return user

def task_submit():
    """Submits task to the BibSched task queue.  This is what people will be invoking via command line."""
    global options
    ## sanity check: remove eventual "task" option:
    if options.has_key("task"):
        del options["task"]
    ## authenticate user:
    user = authenticate(options.get("user", ""))
    ## submit task:
    if options["verbose"] >= 9:
        print ""
        write_message("storing task options %s\n" % options)
    task_id = run_sql("""INSERT INTO schTASK (id,proc,user,runtime,sleeptime,status,arguments)
                         VALUES (NULL,'webcoll',%s,%s,%s,'WAITING',%s)""",
                      (user, options["runtime"], options["sleeptime"], marshal.dumps(options)))
    ## update task number:
    options["task"] = task_id
    run_sql("""UPDATE schTASK SET arguments=%s WHERE id=%s""", (marshal.dumps(options), task_id))
    write_message("Task #%d submitted." % task_id)
    return task_id

def task_update_progress(msg):
    """Updates progress information in the BibSched task table."""
    global options
    return run_sql("UPDATE schTASK SET progress=%s where id=%s", (msg, options["task"]))

def task_update_status(val):
    """Updates status information in the BibSched task table."""
    global options
    return run_sql("UPDATE schTASK SET status=%s where id=%s", (val, options["task"]))

def task_read_status(task_id):
    """Read status information in the BibSched task table."""
    res = run_sql("SELECT status FROM schTASK where id=%s", (task_id,), 1)
    try:
        out = res[0][0]
    except:
        out = 'UNKNOWN'
    return out

def task_get_options(id):
    """Returns options for the task 'id' read from the BibSched task queue table."""
    out = {}
    res = run_sql("SELECT arguments FROM schTASK WHERE id=%s AND proc='webcoll'", (id,))
    try:
        out = marshal.loads(res[0][0])
    except:
        write_message("Error: WebColl task %d does not seem to exist." % id)
        sys.exit(1)
    return out

def task_run(task_id):
    """Run the WebColl task by fetching arguments from the BibSched task queue.
       This is what BibSched will be invoking via daemon call.
       The task will update collection reclist cache and collection web pages for
       given collection. (default is all).
       Arguments described in usage() function.
       Return 1 in case of success and 0 in case of failure."""
    global options
    task_run_start_timestamp = get_current_time_timestamp()
    options = task_get_options(task_id) # get options from BibSched task table
    ## check task id:
    if not options.has_key("task"):
        write_message("Error: The task #%d does not seem to be a WebColl task." % task_id)
        return 0
    ## check task status:
    task_status = task_read_status(task_id)
    if task_status != "WAITING":
        write_message("Error: The task #%d is %s.  I expected WAITING." % (task_id, task_status))
        return 0
    ## we can run the task now:
    if options["verbose"]:
        write_message("Task #%d started." % task_id)
    task_update_status("RUNNING")
    ## initialize signal handler:
    signal.signal(signal.SIGUSR1, task_sig_sleep)
    signal.signal(signal.SIGTERM, task_sig_stop)
    signal.signal(signal.SIGABRT, task_sig_suicide)
    signal.signal(signal.SIGCONT, task_sig_wakeup)
    signal.signal(signal.SIGINT, task_sig_unknown)
    colls = []
    # decide whether we need to run or not, by comparing last updated timestamps:
    if options["verbose"] >= 3:
        write_message("Database timestamp is %s." % get_database_last_updated_timestamp())
        write_message("Collection cache timestamp is %s." % get_cache_last_updated_timestamp())
    if options.has_key("force") or \
       compare_timestamps_with_tolerance(get_database_last_updated_timestamp(),
                                         get_cache_last_updated_timestamp(),
                                         cfg_cache_last_updated_timestamp_tolerance) >= 0:
        ## either forced update was requested or cache is not up to date, so recreate it:
        # firstly, decide which collections to do:
        if options.has_key("collection"):
            coll = get_collection(options["collection"])
            if coll.id is None:
                usage(1, 'Collection %s does not exist' % coll.name)
            colls.append(coll)
        else:
            res = run_sql("SELECT name FROM collection ORDER BY id")
            for row in res:
                colls.append(get_collection(row[0]))
        # secondly, update collection reclist cache:
        i = 0
        for coll in colls:
            i += 1
            if options["verbose"]:
                write_message("%s / reclist cache update" % coll.name)
            coll.calculate_reclist()
            coll.update_reclist()
            task_update_progress("Part 1/2: done %d/%d" % (i, len(colls)))
        # thirdly, update collection webpage cache:
        i = 0
        for coll in colls:
            i += 1
            if options["verbose"]:
                write_message("%s / web cache update" % coll.name)
            coll.update_webpage_cache()
            task_update_progress("Part 2/2: done %d/%d" % (i, len(colls)))

        # finally update the cache last updated timestamp:
        # (but only when all collections were updated, not when only
        # some of them were forced-updated as per admin's demand)
        if not options.has_key("collection"):
            set_cache_last_updated_timestamp(task_run_start_timestamp)
            if options["verbose"] >= 3:
                write_message("Collection cache timestamp is set to %s." % get_cache_last_updated_timestamp())
    else:
        ## cache up to date, we don't have to run
        if options["verbose"]:
            write_message("Collection cache is up to date, no need to run.")        
        pass 
    ## we are done:
    task_update_progress("Done.")
    task_update_status("DONE")
    if options["verbose"]:
        write_message("Task #%d finished." % task_id)
    return 1

def usage(exitcode=1, msg=""):
    """Prints usage info."""
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    sys.stderr.write("Usage: %s [options]\n" % sys.argv[0])
    sys.stderr.write("Command options:\n")
    sys.stderr.write("  -c, --collection\t Update cache for the given collection only. [all]\n")
    sys.stderr.write("  -f, --force\t Force update even if cache is up to date. [no]\n")
    sys.stderr.write("Scheduling options:\n")
    sys.stderr.write("  -u, --user=USER \t User name to submit the task as, password needed.\n")
    sys.stderr.write("  -t, --runtime=TIME \t Time to execute the task (now), e.g.: +15s, 5m, 3h, 2002-10-27 13:57:26\n")
    sys.stderr.write("  -s, --sleeptime=SLEEP \t Sleeping frequency after which to repeat task (no), e.g.: 30m, 2h, 1d\n")
    sys.stderr.write("General options:\n")
    sys.stderr.write("  -h, --help      \t\t Print this help.\n")
    sys.stderr.write("  -V, --version   \t\t Print version information.\n")
    sys.stderr.write("  -v, --verbose=LEVEL   \t Verbose level (from 0 to 9, default 1).\n")
    sys.stderr.write("""Description: %s updates the collection cache
    (record universe for a given collection plus web page elements)
    based on WML and DB configuration parameters.
    If the collection name is passed as the second argument, it'll update
    this collection only.  If the collection name is immediately followed
    by a plus sign, it will also update all its desdendants.  The
    top-level collection name may be entered as the void string.\n""" % sys.argv[0])
    sys.exit(exitcode)

def main():
    """Main function that analyzes command line input and calls whatever is appropriate.
       Useful for learning on how to write BibSched tasks."""
    global options

    ## parse command line:
    if len(sys.argv) == 2 and sys.argv[1].isdigit():
        ## A - run the task
        task_id = int(sys.argv[1])
        try:
            if not task_run(task_id):
                write_message("Error occurred.  Exiting.", sys.stderr)
        except StandardError, e:
            write_message("Unexpected error occurred: %s." % e, sys.stderr)
            write_message("Traceback is:", sys.stderr)
            traceback.print_tb(sys.exc_info()[2])
            write_message("Exiting.", sys.stderr)
            task_update_status("ERROR")
    else:
        ## B - submit the task
        # set default values:
        options["runtime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        options["verbose"] = 1
        options["sleeptime"] = ""
        # set user-defined options:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hVv:u:s:t:c:f",
                                       ["help", "version", "verbose=","user=","sleep=","time=","collection=","force"])
        except getopt.GetoptError, err:
            usage(1, err)
        try:
            for opt in opts:
                if opt[0] in ["-h", "--help"]:
                    usage(0)
                elif opt[0] in ["-V", "--version"]:
                    print __revision__
                    sys.exit(0)
                elif opt[0] in [ "-u", "--user"]:
                    options["user"] = opt[1]
                elif opt[0] in ["-v", "--verbose"]:
                    options["verbose"] = int(opt[1])
                elif opt[0] in [ "-s", "--sleeptime" ]:
                    get_datetime(opt[1]) # see if it is a valid shift
                    options["sleeptime"] = opt[1]
                elif opt[0] in [ "-t", "--runtime" ]:
                    options["runtime"] = get_datetime(opt[1])
                elif opt[0] in [ "-c", "--collection"]:
                    options["collection"] = opt[1]
                elif opt[0] in [ "-f", "--force"]:
                    options["force"] = 1
                else:
                    usage(1)
        except StandardError, e:
            usage(e)
        task_submit()
    return

### okay, here we go:
if __name__ == '__main__':
    main()
