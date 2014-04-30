# -*- coding: utf-8 -*-

## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

__revision__ = "$Id$"

import urllib2
from HTMLParser import HTMLParser
import re
import base64
import os
import sys
import Queue
import threading
import signal
import time


from invenio.config import (CFG_CACHEDIR,
                            CFG_HEPDATA_URL,
                            CFG_HEPDATA_PLOTSIZE,
                            CFG_LOGDIR,
                            CFG_TMPSHAREDDIR,
                            CFG_HEPDATA_THREADS_NUM,
                            CFG_HEPDATA_INDEX,
                            CFG_HEPDATA_FIELD,
                            CFG_SITE_RECORD,
                            CFG_SITE_SECURE_URL)
from invenio.jsonutils import json
from datetime import datetime
import time
from invenio import bibrecord

#raise Exception(str(dir(sys.modules['invenio'])))
import invenio.webpage as webpage

if "invenio.search_engine" in sys.modules:
    search_engine = sys.modules["invenio.search_engine"]
else:
    from invenio import search_engine

import cPickle

#imports realted to the harvesting daemon

from invenio.bibtask import task_init, write_message, \
    task_set_option, task_has_option, task_get_option, \
    task_low_level_submission, task_update_progress, \
    task_read_status, task_sleep_now_if_required, \
    task_get_task_param

# helper functions

def get_record_val(recid, field, ind1 = " ", ind2 = " ", sfcode = "a"):
    if not recid:
        return ""

    rec = search_engine.get_record(recid)
    if not rec:
        return ""

    fs = bibrecord.record_get_field_instances(rec, field, ind1 = ind1,
                                              ind2 = ind2)
    if fs:
        sfs = bibrecord.field_get_subfield_values(fs[0], sfcode)
        if sfs:
            return sfs[0]
    return ""

def get_record_collaboration(recid):
    """ Retrieve a collaboration of a given record"""
    return get_record_val(recid, "710", sfcode = "g")

def get_record_arxivid(recid):
    """Retrieve an arxiv identifier from a record of a given number"""
    return get_record_val(recid, "037", sfcode = "a")



# URL extensions that do not lead to additional formats
ACCEPTED_FORMATS = {
    "plain text" : "plain.txt",
    "AIDA" : "aida",
    "PYROOT": "pyroot.py",
    "YODA" : "yoda",
    "ROOT" : "root",
    "mpl" : "mpl",
    "jhepwork" : "jhepwork.py"
}

def download_with_retry(data_url):
    last_e = None
    sleeptime = 2
    for retry_num in xrange(5):
        try:
            f = urllib2.urlopen(data_url)
            content = f.read()
            return content
        except Exception, e:
            last_e = e
        time.sleep(sleeptime)
        sleeptime = sleeptime * 2
    raise Exception("Failed to download url. Last error code: %s " %( last_e.code, ))

class Paper(object):
    def __init__(self):
        self.datasets = []
        self.comment = ""
        self.additional_files = []
        self.systematics = ""
        self.additional_data_links = []

    def __repr__(self):
        return ("<Paper object comment=%s, additional_files=%s, " + \
                    "systematics=%s, additional_data_links=%s>") % \
            (repr(self.comment), repr(self.additional_files),
             repr(self.systematics), repr(self.additional_data_links))


    @staticmethod
    def create_from_record(rec):
        """Create a paper object from the record"""
        paper = Paper()

        # reading additional data links
        fs = bibrecord.record_get_field_instances(rec, "856", ind1="4",
                                                  ind2=" ")
        paper.additional_data_links = []
        if fs:
            for f in fs:
                fsf = bibrecord.field_get_subfield_values(f, "3")
                if fsf and fsf[0] == "ADDITIONAL HEPDATA":
                    fsf_href = bibrecord.field_get_subfield_values(f, "u")
                    fsf_desc = bibrecord.field_get_subfield_values(f, "y")
                    if fsf_href and fsf_desc:
                        paper.additional_data_links.append({
                                "href" : fsf_href[0],
                                "description" : fsf_desc[0]})

        # reading the comment
        fs = bibrecord.record_get_field_instances(rec, "520", ind1 = " ", ind2= " ")
        if fs:
            for f in fs:
                sfs = bibrecord.field_get_subfield_values(f, "9")
                if sfs and sfs[0].strip() == "HEPDATA":
                    sfs = bibrecord.field_get_subfield_values(f, "h")
                    if sfs:
                        paper.comment = sfs[0].strip()

        return paper

    def get_diff_marcxml(self, rec2):
        """Returns a code that will transform record passed as
        an argument into the current one.

        If there are no changes, the method returns None
        """
        outrec = {}

        # comparing links to external data
        correct_links = bibrecord.record_get_field_instances( \
            self.generate_additional_datalinks(), "856", ind1 = "4", ind2 = " ")

        existing_links = filter( \
            lambda field: bibrecord.field_get_subfield_values(field, "3") and \
                bibrecord.field_get_subfield_values(field, "3")[0].strip() == \
                "ADDITIONAL HEPDATA" ,
            bibrecord.record_get_field_instances(rec2, "856", ind1="4",
                                                 ind2 = " "))
        # now comparing correct with existing - first we have to sort !


        # sorting alphabetically !

        fgsv = bibrecord.field_get_subfield_values
        def links_comparer(link1, link2):
            # first try to compare on the description
            sfs1 = fgsv(link1, "y")
            sfs2 = fgsv(link2, "y")
            if sfs1 and sfs2:
                if sfs1[0] > sfs2[0]:
                    return True
                if sfs1[0] < sfs2[0]:
                    return False
            else:
                if sfs1 and not sfs2:
                    return True
                if (not sfs1) and sfs2:
                    return False

            # if failed, compare on the link. In correct situations
            # we should not get here
            sfs1 = fgsv(link1, "u")
            sfs2 = fgsv(link2, "u")
            if sfs1 and sfs2:
                return sfs1[0]>sfs2[0]
            else:
                if sfs1 and not sfs2:
                    return True
                if (not sfs1) and sfs2:
                    return False
            return False # finally they are equal. We shold never get here
            # in the case of well-formed MARC entries -
            # the world is not perfect and we will get here for errors in MARC

        correct_links.sort(cmp = links_comparer)
        existing_links.sort(cmp = links_comparer)

        cmp2 = lambda link1, link2: fgsv(link1, "y") == fgsv(link2, "y") and \
            fgsv(link1, "u") == fgsv(link2, "u")

        have_to_correct = not reduce( \
            lambda prev, links: prev and cmp2(links[0], links[1]),
            zip(correct_links, existing_links),
            len(correct_links) == len(correct_links))

        correct_links.sort()

        if have_to_correct:
            to_upload = filter( \
                lambda field: not (bibrecord.field_get_subfield_values(field, "3") and \
                                       bibrecord.field_get_subfield_values(field, "3") \
                                       [0].strip() == \
                                       "ADDITIONAL HEPDATA") ,
                bibrecord.record_get_field_instances(rec2, "856", ind1="4",
                                                     ind2 = " ")) + \
                                                     correct_links
            bibrecord.record_add_fields(outrec, "856", to_upload)

        # HEPDATA comment

        fs = bibrecord.record_get_field_instances(rec2, "520",
                                                  ind1 = " ", ind2 = " ")
        existing_comment = ""
        correct_comment = self.comment.strip()
        new_fields = []

        if fs:
            for f in fs:
                sfs = bibrecord.field_get_subfield_values(f, "9")
                if sfs and sfs[0].strip() == "HEPDATA":
                    # we have found THE CAPTION
                    sfs = bibrecord.field_get_subfield_values(f, "h")
                    if sfs:
                        existing_comment = sfs[0].strip()
                else:
                    new_fields.append(f)

        if existing_comment != correct_comment:
            bibrecord.record_add_fields(outrec, "520", new_fields)
            if correct_comment:
                bibrecord.record_add_field(outrec, "520", \
                                               subfields = [("9", "HEPDATA")] \
                                               + ((correct_comment or []) and \
                                                      [("h", correct_comment)]))

        if outrec:
            #If the output was different than empty so far, we are copying the
            # record identifier
            ids = bibrecord.record_get_field_values(rec2, "001")
            if ids:
                bibrecord.record_add_field(outrec, "001", \
                                               controlfield_value = str(ids[0]))
            return bibrecord.record_xml_output(outrec)
        else:
            return None

    def generate_additional_datalinks(self):
        """ Return a record containing only fields encoding
        aditional data links
        """
        rec = {}
        for adl in self.additional_data_links:
            bibrecord.record_add_field(rec, "856", ind1 = "4", ind2 = " ", \
                                           subfields = [ \
                    ("3", "ADDITIONAL HEPDATA"),
                    ("u", adl["href"]),
                    ("y", adl["description"]),])
        return rec


class Dataset(object):
    """Represents a single dataset saved in the document
    we represent only
    """
    def __init__(self):
        self.column_titles = []
        self.column_headers = []
        self.data_qualifiers = []
        self.data = [] # row by row
        self.comments = ""
        self.name = ""
        self.additional_files = []
        self.num_columns = 0
        self.location = ""
        self.position = 0 #position within the data record
        self.additional_data_links = []
        self.data_plain = ""
        self.recid = None
        self.x_columns = 0
        self.y_columns = 0
        self.title = ""

    def __repr__(self):
        return "Auxiliary information: " + repr(self.data_qualifiers) + \
            "  Headers: " + repr(self.column_headers) + " Data: " + repr(self.data)

    def get_type(self):
        """Determine type based on the location"""
        first_char = (len(self.location.strip()) > 0 or "") and \
            self.location.strip().lower()[0]
        if first_char == "F":
            return "FIGURE"
        elif first_char == "T":
            return "TABLE"
        else:
            return "DATASET"

    def get_marcxml(self, parent_recid = None):
        """Produces a ready to upload MARC XML
           If some files have to be attached to a record, they are
           written in the Invenio installation's temporary directory and
           referenced from the XML code"""
        return self.get_diff_marcxml({}, parent_recid)

    empty_data_str = cPickle.dumps({})

    def get_diff_marcxml(self, rec2, parent_recid, data_str=None, data_plain=None, force_reupload=False):
        """Produces a MARC XML allowing to modify passed dataset record
           into the current dataset. Necessary files are created in the
           temporary directory.
           If there are no changes to be made, None is returned.
           @param rec2: The dataset to compare with
           @type rec2: BibRecord
           @param recid: The identifier of the record prepresenting dataset
           @type recid: Integer
           @param parent_recid: The record identifier of the main MARC record
           @type parent_recid: Integer
           @rtype: String
           @returns: MARC XML which modifies the passed record into the one
                     described by current Dataset instance
           """
        outrec = {} # the output record
        def addf(*args, **args2):
            """Add field to the output record"""
            bibrecord.record_add_field(outrec, *args, **args2)

        def get_subfield_with_defval(tag, ind1 = " ", ind2 = " ",
                                     sfcode = "a", default = ""):
            """Retrieve the first vale of a subfield or default"""
            fs = bibrecord.record_get_field_instances(rec2, tag, ind1, ind2)
            if fs:
                sfs = bibrecord.field_get_subfield_values(fs[0], sfcode)
                if sfs:
                    return sfs[0].strip()
            return default

        # processing the title
        existing_title = get_subfield_with_defval(tag = "245", sfcode = "a", default="")

        if existing_title != self.title:
            addf("245", ind1 = " ", ind2 = " ", subfields = \
                 [("9", "HEPDATA"), ("a", self.title)])

        # processing number of x and y columns
        existing_x = int(get_subfield_with_defval(tag = "911", sfcode = "x", default=0))
        existing_y = int(get_subfield_with_defval(tag = "911", sfcode = "y", default=0))

        correct_x = self.x_columns
        correct_y = self.y_columns

        if correct_x != existing_x or correct_y != existing_y:
            addf("911", ind1 = " ", ind2=" ", subfields = \
                     [("x", str(self.x_columns)),
                       ("y", str(self.y_columns))])


        # processing caption

        fs = bibrecord.record_get_field_instances(rec2, "520",
                                                  ind1 = " ", ind2 = " ")
        existing_comment = ""
        correct_comment = self.comments.strip()
        new_fields = []

        if fs:
            for f in fs:
                sfs = bibrecord.field_get_subfield_values(f, "9")
                if sfs and sfs[0].strip() == "HEPDATA":
                    # we have found THE CAPTION
                    sfs = bibrecord.field_get_subfield_values(f, "h")
                    if sfs:
                        existing_comment = sfs[0].strip()
                else:
                    new_fields.append(f)


        if existing_comment != correct_comment:
            bibrecord.record_add_fields(outrec, "520", new_fields)
            if correct_comment:
                addf("520", \
                         subfields = [("9", "HEPDATA")] \
                         + ((correct_comment or []) and \
                                [("h", correct_comment)]))



        # collaboration
        existing_collaboration = get_subfield_with_defval(tag = "710",
                                                          sfcode = "g")
        correct_collaboration = get_record_collaboration(parent_recid).strip()

        if correct_collaboration and \
                existing_collaboration != correct_collaboration:
            addf("710", ind1= " ", ind2 = " ",
                 subfields = [("g", correct_collaboration)])


        # Link to the original record and the location
        if parent_recid:
            existing_id = get_subfield_with_defval(tag = "786", sfcode = "w")
            existing_arXivId = get_subfield_with_defval(tag = "786",
                                                        sfcode = "r")
            existing_location = get_subfield_with_defval(tag = "786",
                                                         sfcode = "h")
            correct_location = self.location.strip()
            correct_arXivId = get_record_arxivid(parent_recid).strip()

            correct_id = str(parent_recid).strip()

            existing_position =  get_subfield_with_defval(tag = "786",
                                                         sfcode = "q")
            correct_position = self.position


#            import rpdb2; rpdb2.start_embedded_debugger('password', fAllowRemote=True)
            if existing_location != correct_location or \
                    existing_arXivId != correct_arXivId or \
                    existing_id != correct_id or \
                    int(existing_position) != int(correct_position):
                subfields = [("w", correct_id), ("q", str(correct_position))]
                if correct_arXivId:
                    subfields.append(("r", correct_arXivId))
                if correct_location:
                    subfields.append(("h", correct_location))
                addf("786", ind1 = " ", ind2 = " ", subfields = subfields)
        else:
            write_message("No dataset parent recid!")

        # dataset type (determined based on the location)
        correct_type = self.get_type().strip()
        existing_type = get_subfield_with_defval(tag = "336", sfcode = "t")
#        print "Types: %s %s" % (correct_type, existing_type)
        if existing_type != correct_type:
            addf("336", ind1 = " ", ind2 = " ", subfields=[("t", correct_type)])

        #correcting the collection
        correct_collection = "DATA"
        existing_collection = get_subfield_with_defval(tag = "980",
                                                       sfcode = "a")
        if correct_collection != existing_collection:
            addf("980", ind1 = " ", ind2 = " ",
                 subfields=[("a", correct_collection)])


        # data qualifiers
        correct_qualifiers = bibrecord.record_get_field_instances(
            self.generate_qualifiers(parent_recid), "653",
            ind1 = "1", ind2 = " ")

        present_qualifiers = bibrecord.record_get_field_instances(rec2, "653",
                                                                  ind1 = "1",
                                                                  ind2 = " ")

        # order doe not matter ! we will sort them lexicographically
        # before comparing !
        def qualifier_comparer(q1, q2):
            """ compare two qualifier fields """
            sfs1 = bibrecord.field_get_subfield_values(q1, "r")
            sfs2 = bibrecord.field_get_subfield_values(q2, "r")
            if sfs1 and sfs2:
                if sfs1[0] > sfs2[0]:
                    return True
                if sfs2[0] > sfs1[0]:
                    return False
            else:
                # reaction is always bigger than non-reaction
                if sfs1 and not sfs2:
                    return True
                elif sfs2 and not sfs1:
                    return False
                else:
                    # compare on keys
                    sfs1 = bibrecord.field_get_subfield_values(q1, "k")
                    sfs2 = bibrecord.field_get_subfield_values(q2, "k")
                    if sfs1 and not sfs2:
                        return True
                    elif sfs2 and not sfs1:
                        return False
                    if sfs1 and sfs2 and sfs1[0] > sfs2[0]:
                        return True
                    elif sfs1 and sfs2 and sfs2[0] > sfs1[0]:
                        return False
                    else:
                        sfs1 = bibrecord.field_get_subfield_values(q1, "v")
                        sfs2 = bibrecord.field_get_subfield_values(q2, "v")
                        if sfs1 and not sfs2:
                            return True
                        elif sfs2 and not sfs1:
                            return False
                        elif sfs1 and sfs2:
                            return sfs1[0] > sfs2[0]
                        else:
                            return False


            # compare on columns
            sfs1 = " ".join(bibrecord.field_get_subfield_values(q1, "c"))
            sfs2 = " ".join(bibrecord.field_get_subfield_values(q2, "c"))
            return sfs1 > sfs2

        correct_qualifiers.sort(cmp = qualifier_comparer)
        present_qualifiers.sort(cmp = qualifier_comparer)
        fgsv = bibrecord.field_get_subfield_values
        qualifiers_eq = lambda x, y: \
            fgsv(x, "r") == fgsv(y, "r") and \
            fgsv(x, "k") == fgsv(y, "k") and \
            fgsv(x, "v") == fgsv(y, "v") and \
            set(fgsv(x, "c")) == set(fgsv(y, "c"))

        if not reduce(lambda x, y: x and qualifiers_eq(y[0], y[1]), \
                      zip(correct_qualifiers, present_qualifiers), \
                      (len(correct_qualifiers) == len(present_qualifiers))):
            bibrecord.record_add_fields(outrec, "653", correct_qualifiers)

        # columns ( the order does not matter)
        present_columns = bibrecord.record_get_field_instances(rec2, "910")
        correct_columns = bibrecord.record_get_field_instances(
            self.generate_columns(), "910")
        column_cmp = lambda x, y: \
            int(bibrecord.field_get_subfield_values(x, "n")[0]) > \
            int(bibrecord.field_get_subfield_values(y, "n")[0])

        fgsv = bibrecord.field_get_subfield_values
        columns_eq = lambda x, y: \
            fgsv(x, "n") == fgsv(y, "n") and \
            fgsv(x, "t") == fgsv(y, "t") and \
            fgsv(x, "d") == fgsv(y, "d")

        correct_columns.sort(cmp = column_cmp)
        present_columns.sort(cmp = column_cmp)

        (not reduce(lambda x, y: x and columns_eq(y[0], y[1]), \
                        zip(correct_columns, present_columns), \
                        len(correct_columns) == len(present_columns))) and \
                        bibrecord.record_add_fields(outrec, "910", \
                                                    correct_columns)
        # data of the table
        existing_data = {}
        try:
            existing_data = cPickle.loads(data_str)
        except:
            existing_data = []


        if (not data_str) or (not self.compare_data(existing_data)) or force_reupload:
            # we retreive plain data only if table data is different
            self.retrieve_plain_data()

            (fname_int, fname_plain) = self.write_data_to_tmpfile()
            if fname_int:
                bibrecord.record_add_field(outrec, "FFT", subfields = [ \
                        ("a", fname_int), \
                            ("t", "Data"), \
                            ("n", "Data"), \
                            ("f", ".data"), \
                            ("o", "HIDDEN"), \
                            ("d", "data extracted from the table") \
                            ])
            if fname_plain:
                bibrecord.record_add_field(outrec, "FFT", subfields = [ \
                        ("a", fname_plain), \
                            ("t", "Data"), \
                            ("n", "Data"), \
                            ("f", ".txt"), \
                            ("d", "data extracted from the table") \
                            ])

        if outrec:
            ids = bibrecord.record_get_field_values(rec2, "001")
            if ids:
                addf("001", controlfield_value = str(ids[0]))

            return bibrecord.record_xml_output(outrec)
        return None

    def retrieve_plain_data(self):
        data_url = urllib2.urlparse.urljoin(CFG_HEPDATA_URL,
                                            reduce( \
                lambda x, y: x or (y[1] == "plain text" and y[0]) ,
                self.additional_files, ""))
        try:
            self.data_plain = download_with_retry(data_url)

        except Exception, e:
            print "Impossible to retrieve the plain text format related to a dataset. URL: %s "% (data_url, )
            self.data_plain = ""

        return self.data_plain

    def generate_columns(self):
        """
        Generates an Invenio record containing only fields that describe
        columns present in the dataset
        """
        # Application of map/reduce to Invenio ;)
        import operator
        return reduce(lambda rec, sf: \
                          (bibrecord.record_add_field(rec, "910", subfields=sf)\
                               and rec),
                      map(lambda num, title, header: \
                              reduce(
                                  operator.add, [[("n", num)],
                                        (title or []) and [("t", title or "")],
                                        (header or []) and \
                                            [("d", header or "")]], []), \
                              map(str, range(self.num_columns)), \
                              reduce(operator.add,
                                     [[col_t["content"]] * col_t["colspan"] \
                                          for col_t in self.column_titles], []), \
                              reduce(operator.add,
                                     [[col_h["content"]] * col_h["colspan"] \
                                          for col_h in self.column_headers], [])),
                      {}) # start with {} as initial record

    def generate_qualifiers(self, master_recid):
        """Generate fields describing data qualifiers of a current dataset
           Returns a record containing only fields with necessary qualifiers
        """
        rec = {} # we will start adding to an empty record

        for dq_line in self.data_qualifiers:
            current_column = 0
            for dq in dq_line:
                col_pos = dq["content"].find(":")
                subfields = []
                if col_pos == -1:
                    log_msg = ("""Data qualifier "%(dq)s" does not contain""" +\
                                   """ colon. Record number: %(recid)s """) % {
                        "dq" : dq["content"],
                        "recid" : str(master_recid)
                        }
                    hepdata_log("harvesting", log_msg)
                    dq_key = ""
                    dq_value = dq["content"].strip()
                else:
                    dq_key = dq["content"][:col_pos].strip()
                    dq_value = dq["content"][col_pos + 1:].strip()

                if dq_key == "RE": # the reaction data
                    subfields.append(("r", dq_value))
                else:
                    subfields.append(("k", dq_key))
                    subfields.append(("v", dq_value))

                # now processing columns belonging
                subfields += [("c", str(col_num)) for col_num in \
                                  xrange(current_column,
                                         current_column + dq["colspan"])]
                current_column += dq["colspan"]

                bibrecord.record_add_field(rec, "653", ind1 = "1",
                                           ind2 = " ", subfields = subfields)
        return rec

    @staticmethod
    def create_from_record(rec, data_str, parent_recid, data_plain):
        """Creates an instance from a record"""
        ds = Dataset()
        ds.data_plain = data_plain
        ds.title = ""
        fs = bibrecord.record_get_field_instances(rec, "245", " ", " ")
        if fs:
            sfs = bibrecord.field_get_subfield_values(fs[0], "a")
            if sfs:
                ds.title = sfs[0].strip()
        # filling recid

        ds.recid = bibrecord.record_get_field_value(rec, "001")

        # comments:
        fs = filter(lambda field: bibrecord.field_get_subfield_values(field, "9") and \
                         bibrecord.field_get_subfield_values(field, "9")[0] == \
                        "HEPDATA", \
                        bibrecord.record_get_field_instances(rec, "520", \
                                                                 ind1 = " ", \
                                                                 ind2 = " "))

        if fs:
            sfs = bibrecord.field_get_subfield_values(fs[0], "h")
            if sfs:
                ds.comments = sfs[0]

        # reading the position

        fs = filter(lambda field: \
                        bibrecord.field_get_subfield_values(field, "w") and \
                        int(bibrecord.field_get_subfield_values(field, "w")[0]) \
                        ==  parent_recid,
                    bibrecord.record_get_field_instances(rec, "786"))
        if fs:
            sfs = bibrecord.field_get_subfield_values(fs[0], "q")
            if sfs:
                ds.position = int(sfs[0])

        # reading numbers of x and y columns

        fs = bibrecord.record_get_field_instances(rec, "911")
        ds.x_columns = 0
        ds.y_columns = 0

        if fs:
            ds.x_columns = int(bibrecord.field_get_subfield_values(fs[0], "x")[0])
            ds.y_columns = int(bibrecord.field_get_subfield_values(fs[0], "y")[0])

        ds.num_columns = ds.x_columns + ds.y_columns


        #reading columns - they are necessary for reading data qualifiers
        fs = bibrecord.record_get_field_instances(rec, "910")
        columns = []
        for f in fs:
            column = {"pos": -1, "header": "", "title":""}
            sfs = bibrecord.field_get_subfield_values(f, "n")
            if sfs:
                column["pos"] = sfs[0]

            sfs = bibrecord.field_get_subfield_values(f, "t")
            if sfs:
                column["title"] = sfs[0]

            sfs = bibrecord.field_get_subfield_values(f, "d")
            if sfs:
                column["header"] = sfs[0]
            columns.append(column)

        columns.sort(cmp = lambda x, y: x["pos"] > y["pos"])

        ds.column_headers = []
        ds.column_titles = []

        cur_header = None
        prev_header = None # previous header string

        cur_title = None
        prev_title = None # previous title string

        for col in columns:
            if col["title"] == prev_title:
                cur_title["colspan"] += 1
            else:
                if cur_title:
                    ds.column_titles.append(cur_title)
                cur_title = {"content" : col["title"], "colspan" : 1}
            prev_title = col["title"]

            if col["header"] == prev_header:
                cur_header["colspan"] += 1
            else:
                if cur_header:
                    ds.column_headers.append(cur_header)
                cur_header = {"content" : col["header"], "colspan" : 1}
            prev_header = col["header"]

        if cur_title:
            ds.column_titles.append(cur_title)
        if cur_header:
            ds.column_headers.append(cur_header)

        #reading data qualifiers -> we have to pack them into table !

        qualifiers = [("", [])] # an array with all possible qualifiers

        # first reading qualifiers
        # reading qualifiers requires assigning them places in the readable
        # table here we try to compactify qualifiers by leaving as few space
        # in the table as possible

        fs = bibrecord.record_get_field_instances(rec, "653", ind1="1")
        for f in fs:
            # first decoding the qualifier
            cur_qual = ""
            sfs = bibrecord.field_get_subfield_values(f, "r")
            if sfs: # this is a reaction
                cur_qual = "RE : %s" % (sfs[0],)
            sfs = bibrecord.field_get_subfield_values(f, "k")
            sfs2 = bibrecord.field_get_subfield_values(f, "v")
            if sfs and sfs2: # this is a regular key-value data qualifeir
                cur_qual = "%s : %s" % (sfs[0], sfs2[0])

            # read columns
            columns = []
            sfs = bibrecord.field_get_subfield_values(f, "c")
            for sf in sfs:
                if int(sf) >= ds.num_columns:
                    hepdata_log("reconstruction", "Data qualifiers occuly more columns that exist in a dataset. Qualifier %s in column %s ...  ignoring exceed. rec: %s" % (cur_qual, str(sf), str(rec), ))
                else:
                    columns.append(int(sf))
            columns.sort()
            qualifiers.append((cur_qual, columns))

        qualifiers.sort(cmp = lambda x, y: len(y[1]) - len(x[1]))
        qualifier_rows = [] # we start with an empty assignment

        for (q_pos, qualifier) in \
                zip(xrange(len(qualifiers) - 1), qualifiers[1:]):
            # searching for a row that can be used for this qualifier
            blocker = True # there was something "blocking" in the -1 line...a "reason" why data has not been put there
            elected_row = 0 # 0th row preelected

            while blocker and elected_row < len(qualifier_rows):
                blocker = False
                for col in qualifier[1]:
                    blocker = blocker or (qualifier_rows[elected_row][col] != 0)
                if blocker:
                    elected_row += 1

            if blocker:
                # adding new line to the list (if necessary):
                qualifier_rows.append([0] * ds.num_columns)

            # assigning the qualifier to the elected line
            for col in qualifier[1]:
                qualifier_rows[elected_row][col] = q_pos + 1
                # real position is shifted by 1

        # now translating into the regular qualifiers array
        ds.data_qualifiers = []

        for row in qualifier_rows:
            cur_row = []
            ds.data_qualifiers.append(cur_row)

            prev_data = None
            cur_width = 0

            for cell in row:
                if prev_data == cell:
                    cur_width += 1
                else:
                    if cur_width > 0:
                        cur_row.append({"content": qualifiers[prev_data][0],
                                        "colspan" : cur_width})
                    cur_width = 1
                    prev_data = cell

            # append the remaining one
            if cur_width > 0:
                cur_row.append({"content": qualifiers[prev_data][0],
                                "colspan" : cur_width})

        # Checking if the data content is up to date (or exists at all) and upload

        # reading the data -> from a stream provided as an argument
        # (stored as an attached record in the database)
        try:
            ds.data = cPickle.loads(data_str)
        except:
            ds.data = []

        return ds

    def compare_data(self, ds):
        """Compare current data with the dataset passed as an argument
        @parameter dataset to compare with (the same as the content of Dataset.data)
        @type ds List
        @return True if data in both datasets are equal, otherwise False
        @returntype boolean"""
        try:
            return reduce(lambda prev, datalines: prev and reduce( \
                    lambda prev, datas: prev and \
                        datas[0]["colspan"] == datas[1]["colspan"] and \
                        datas[0]["content"] == datas[1]["content"], \
                        zip(datalines[0], datalines[1]), \
                        len(datalines[0]) == len(datalines[1])), \
                              zip(ds, self.data), \
                              len(ds) == len(self.data))
        except Exception, e:
            import rpdb2; rpdb2.start_embedded_debugger('password')



    def write_data_to_tmpfile(self):
        """Writes data from the dataset into a temporary file and returns
           the file name. This file can be attached into the record
           @return Names of the files where data has been written (internal_data, plain_data)
           @returntype (string, string)"""

        import tempfile
        if cPickle.dumps(self.data):
            fdesc, fname = tempfile.mkstemp(suffix = ".data", prefix = "data_", \
                                                dir = CFG_TMPSHAREDDIR)

            os.write(fdesc, cPickle.dumps(self.data))
            os.close(fdesc)
        else:
            fname = None

        if self.data_plain:
            fdesc, fname2 = tempfile.mkstemp(suffix = ".txt", prefix = "data_", \
                                                 dir = CFG_TMPSHAREDDIR)
            os.write(fdesc, self.data_plain)
            os.close(fdesc)
        else:
            fname2 = None


        return (fname, fname2)

class DatasetParser(object):
    def __init__(self, owner, dataset):
        self.owner = owner
        self.dataset = dataset
        self.parsingComments = False
        self.parsingLocation = True # first comes location, than after <br> comes comment
        self.parsingOtherTag = 0

    def handle_starttag(self, tag, attrs):
        if self.parsingOtherTag > 0:
            self.parsingOtherTag += 1
        else:
            if tag == "br":
                self.parsingLocation = False
                self.parsingComments = True
            elif tag == "a":
                # search for those links which have href but it does not
                # end with one of marked suffixes
                for at in attrs:
                    if at[0] == "href":
                        link = strip_link_session_id(at[1])
                        for suf in ACCEPTED_FORMATS.keys():
                            if link.endswith(ACCEPTED_FORMATS[suf]):
                                self.dataset.additional_files.append([link, suf])
                self.parsingOtherTag = 1
            else:
                self.parsingOtherTag = 1


    def handle_endtag(self, tag):
        if self.parsingOtherTag > 0:
            self.parsingOtherTag -= 1
        if tag == "div":
            self.owner.exit_special_mode()
            self.parsingComments = False

    def handle_charref(self, name):
        if self.parsingOtherTag > 0:
            return

        refstring =  "&#" + name + ";"
        if self.parsingComments:
            self.dataset.comments += refstring
        elif self.parsingLocation:
            self.dataset.location += refstring


    def handle_entityref(self, name):
        if self.parsingOtherTag > 0:
            return
        if name == "nbsp":
            return
        refstring = "&" + name + ";"
        if self.parsingComments:
            self.dataset.comments += refstring
        elif self.parsingLocation:
            self.dataset.location += refstring


    def handle_data(self, data):
        if self.parsingOtherTag > 0:
            return

        if self.parsingComments:
            self.dataset.comments += data
        elif self.parsingLocation:
            self.dataset.location += data

    def exit_special_mode(self):
        pass



# Parsing : this is a very dangerous method of parsing the HTML page ... will fail and possibly corrupt data
#           whenever the maintainer of HEPData decides to modify the format of pages

class DataBoxParser(object):
    """ a special parser for data tables """
    def __init__(self, owner, dataset):
        """
        @param owner - The object owning the current one - a global parser
        """
        self.dataset = dataset
        self.state = "columntitles"
        self.owner = owner
        self.current_line = []
        self.current_cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.current_line = []

            if ("class", "xyheaders") in attrs:
                self.state = "headers"
            elif self.state == "headers":
                self.state = "predata" # things before headers and data ...
            elif self.state == "predata":
                self.state = "data"

            elif ("class", "altformats") in attrs:
                self.state = "footer"

        if tag in ("th", "td"):
            if self.state == "footer":
                self.dataset.x_columns += 1

            colspan = 1
            for attr in attrs:
                if attr[0] == "colspan":
                    colspan = int(attr[1])
            axis = ""
            if ("class", "xval") in attrs:
                axis = "x"
            if ("class", "yval") in attrs:
                axis = "y"
            self.current_cell = {"colspan": colspan, "content": "", "axis": axis}

        if tag in ("a"):
            if self.state == "footer":
                if ("title", "Display this table in graphical form") in attrs:
                    self.dataset.y_columns += 1
                    self.dataset.x_columns -= 1

    def handle_charref(self, name):
        if self.current_cell:
            self.current_cell["content"] += "&#" + name + ";"

    def handle_entityref(self, name):
        if name == "nbsp":
            return
        if self.current_cell:
            self.current_cell["content"] += "&" + name + ";"

    def handle_data(self, data):
        if self.current_cell:
            self.current_cell["content"] += data

    def handle_endtag(self, tag):
        if tag == "table":
            #exiting the data-reading mode
            self.owner.exit_special_mode()

        if tag == "tr":
            to_add = None
            if self.state == "auxiliary":
                to_add = self.dataset.data_qualifiers
            elif self.state == "headers":
                self.dataset.column_headers = self.current_line
            elif self.state == "data":
                to_add = self.dataset.data
            elif self.state == "columntitles":
                self.state = "auxiliary"
                self.dataset.column_titles = self.current_line

            if not to_add is None:
                to_add.append(self.current_line)
            self.current_line = []

        if tag in ("td", "th"):
            self.current_cell["content"] = self.current_cell["content"].strip()
            self.current_line.append(self.current_cell)

class AdditionalDataParser(object):
    def __init__(self, owner, paper):
        self.owner = owner
        self.paper = paper
        self.paper.additional_data_links = []
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        #we assume there art no subdivs inside this
        if tag == "a":
            self.current_link = {"description": ""}
            for attr in attrs:
                self.current_link[attr[0]] = attr[1]

            self.paper.additional_data_links.append(self.current_link)

    def handle_endtag(self, tag):
        if tag == "div":
            self.owner.exit_special_mode()
        elif tag == "a":
            self.current_link = None

    def handle_charref(self, name):
        if self.current_link:
            self.current_link["description"] += "&#" + name + ";"

    def handle_entityref(self, name):
        if name == "nbsp":
            return
        if self.current_link:
            self.current_link["description"] += "&" + name + ";"

    def handle_data(self, data):
        if self.current_link:
            self.current_link["description"] += data


class SystematicsParser(object):
    # Systematics we will remember as a table
    def __init__(self, owner, paper):
        self.owner = owner
        self.paper = paper

    def handle_starttag(self, tag, attrs):
        #we assume there art no subdivs inside this
        self.paper.systematics += "<" + tag + " " + \
            (" ".join([ s[0] + "=\"" + s[1] + "\"" for s in attrs])) + ">"

    def handle_endtag(self, tag):
        if tag == "div":
            self.owner.exit_special_mode()
        else:
            self.paper.systematics += "</" + tag + ">"

    def handle_charref(self, name):
        self.paper.systematics += "&#" + name + ";"

    def handle_entityref(self, name):
        if name == "nbsp":
            return
        self.paper.systematics += "&" + name + ";"

    def handle_data(self, data):
        self.paper.systematics += data

class HEPParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.special_mode = None
        self.paper = Paper()
        self.parsing_paper_comment = False

    def exit_special_mode(self):
        self.special_mode = None

    def parse_paperbox(self):
        """started parsing the paper box"""
        pass

    def parse_datasetbox(self):
        dataset = Dataset()
        self.paper.datasets += [dataset]
        self.special_mode = DatasetParser(self, dataset)


    def parse_dataset(self):
        """parse the data table"""
        dataset = self.paper.datasets[-1]
        self.special_mode = DataBoxParser(self, dataset)

    def parse_systematics(self):
        self.special_mode = SystematicsParser(self, self.paper)

    def parse_paper_comment(self):
        self.parsing_paper_comment = True

    def parse_additional_data(self):
        self.special_mode = AdditionalDataParser(self, self.paper)


    def handle_data(self, data):
        if self.special_mode != None:
            self.special_mode.handle_data(data)
        elif self.parsing_paper_comment:
            self.paper.comment += data

    def handle_charref(self, name):
        refstring = "&#" + name + ";"
        if self.special_mode != None:
            self.special_mode.handle_charref(name)
        elif self.parsing_paper_comment:
            self.paper.comment += refstring


    def handle_entityref(self, name):
        if name == "nbsp":
            return
        refstring = "&" + name + ";"

        if self.special_mode != None:
            self.special_mode.handle_entityref(name)
        elif self.parsing_paper_comment:
            self.paper.comment += refstring

    def handle_starttag(self, tag, attrs):
        if self.special_mode != None:
            self.special_mode.handle_starttag(tag, attrs)
        elif tag == "div":
            if ("class", "paperbox") in attrs:
                self.parse_paperbox()

            if ("class", "datasetbox") in attrs:
                self.parse_datasetbox()

            if ("class", "systematics") in attrs:
                self.parse_systematics()

            if ("class", "extradata") in attrs:
                self.parse_additional_data()
        elif tag == "table" and ("class", "dataset") in attrs:
            # we have to add real data to previous dataset
            self.parse_dataset()
        elif tag == "p" and ("class", "papercomment") in attrs:
            self.parse_paper_comment()
#        elif tag == "br" and self.parsing_paper_comment:
#            self.paper.comment += "<br>"
        elif tag == "a":
            # search for those links which have href but it does not
            # end with one of marked suffixes
            for at in attrs:
                if at[0] == "href":
                    link = strip_link_session_id(at[1])
                    for suf in ACCEPTED_FORMATS.keys():
                        if link.endswith(ACCEPTED_FORMATS[suf]):
                            self.paper.additional_files.append([link, suf])

    def handle_endtag(self, tag):
        if self.special_mode != None:
            self.special_mode.handle_endtag(tag)
        if tag == "p" and self.parsing_paper_comment:
            self.parsing_paper_comment = False

def strip_link_session_id(st):
    return st.split(";jsessionid")[0]

def wash_code(content):
    """Correcting the HEPData XHTML code so that it can be parsed\
    @return correct code - string
    """
    #filtering out cases of having incorrect closing tags containing attributes
    res = re.split("</([a-zA-Z0-9]+)\s[^>]*>", content)
    for pos in range(1, len(res), 2):
        res[pos] = "</" + res[pos] + ">"
    content = "".join(res)
    # in the systematics section there are errors with enclosing colspans in
    # quotes

    res = re.split("colspan=([0-9]+)\'", content)
    for pos in range(1, len(res), 2):
        res[pos] = "colspan='" + res[pos] + "'"
    content = "".join(res)
    return content

def download_paper(page_url, recid):
    try:
        content = wash_code(download_with_retry(page_url))
    except Exception, e:
        write_message("Error when retrieving dataset. URL: %s" %(page_url, ))
        raise e

    parser = HEPParser()
    parser.feed(content)
    paper = parser.paper


    # fixing column lengths and titles


    import operator
    get_line_len = lambda line: reduce(operator.add,
                                       map(lambda hd: hd["colspan"], line), 0)
    for ds in paper.datasets:
        ds.num_columns = reduce(max, map(get_line_len, ds.data) + \
                                [get_line_len(ds.column_headers),
                                 get_line_len(ds.column_titles), ds.x_columns + ds.y_columns])


        paper_title = get_record_val(recid, "245", sfcode = "a")
        if not paper_title:
            paper_title = "record %s" % (str(recid), )

        res = re.search("F\\s*([0-9]+)", ds.location)

        if res:
            ds.title = "Data from figure %s from: %s" % (res.groups()[0], paper_title)
        else:
            ds.title =         "Additional data from: %s" % (paper_title, )
            #        write_message("Setting the title")

    # download necessary datasets and fix other things

    cur_pos = 1
    for ds in paper.datasets:
        lo = ds.location.find("\n\n")
        ds.location = ds.location[:lo].strip()
        if ds.location and ds.location[0] == "(":
            ds.location = ds.location[1:]
        if ds.location and ds.location[-1] == ")":
            ds.location = ds.location[:-1]
        ds.location = ds.location.strip()
        ds.position = cur_pos
        cur_pos += 1
    return paper



def retrieve_hepdata(page_url, recid):
    """retrieves a dataset either from cache or downloads and fills the cache"""
    # we directly donwload... no cache this time
    data = download_paper(page_url, recid)
    return data


def get_hepdata_allids_url():
    """ Return the URL of a site giving all identifiers
    """
    return "%s/AllIds" % (CFG_HEPDATA_URL, )

def get_hepdata_url_from_recid(recid):
    """ Returns a HEPData URL for a given recid
    """
    return "%s/View/ins%s/all" % (CFG_HEPDATA_URL, str(recid))

def retrieve_data_for_record(recID):
    """Retrieves the Paper object representing data associated with a publication"""
    rec = search_engine.get_record(recID)
    paper = Paper.create_from_record(rec)

    try:
        paper.datasets = map(lambda x: x[1], get_attached_hepdata_datasets(recID))
    except:
        paper.datasets = None

    if not paper.datasets:
        return None
    else:
        return paper

def get_hepdata_by_recid_raw(recid):
    """Retrieves raw data corresponding to a HEPData record.
    @param recid: Identifier of the record representing a dataset
    @type recid: Integer
    @returns: a tuple consisting of a record (bibrecord representation) and string of data
    @rtype: (Record, String, String)
    """
    rec = search_engine.get_record(recid)
    # retrieving the data string (content of an attachment)
    data_str = cPickle.dumps([])
    data_plain = ""

    from invenio import bibdocfile
    brd = bibdocfile.BibRecDocs(recid)
    if brd.has_docname_p("Data"):
        bd = brd.get_bibdoc("Data")
        try:
            data_file = bd.get_file(".data")
            if data_file:
                data_str = data_file.get_content()
        except:
            #TODO: The document exists but does not have one of required formats ... we might want to record this in some type of log or even notify someone behind the scenes ?
            pass

        try:
            data_file = bd.get_file(".txt")
            if data_file:
                data_plain = data_file.get_content()
        except:
            #TODO: The document exists but does not have one of required formats ... we might want to record this in some type of log or even notify someone behind the scenes ?
            pass

    return (rec, data_str, data_plain)

def get_hepdata_by_recid(parent_recid, recid):
    """Retrieve a dataset encoded in a given record
    @param parent_recid: record identifier of the publication attaching the dataset
    @type parent_recid: Integer
    @param recid: Identifier of te record identifying the dataset
    @type recid: Integer
    @rtype: Dataset
    @returns: A dataset represented by a record of a given number
    """
    rec, data_str, data_plain = get_hepdata_by_recid_raw(recid)
    return Dataset.create_from_record(rec, data_str, parent_recid, data_plain)

def get_attached_hepdata_records(recid):
    """Retrieves raw data of a HEPData for a given recid

    We perform an additional in principle redundan (in the case of correct configuration)
    step to remove possibly removed records

    @param recid: The record id of a publication to which datasets refer
    @type recid: Integer

    @return: List of tuples (recid, record, data_string, data_plain)
    @rtype: List of tuples"""
    ids = get_attached_hepdata_dataset_ids(recid)
    def rec_not_deleted(tup):
        rec = tup[1]
        if not "980" in rec:
            return True
        f_980 = rec["980"]
        return reduce(lambda bool_res, subfield: bool_res and (not ('c', 'DELETED') in subfield[0]), f_980, True)
    return filter(rec_not_deleted , map(lambda element: (element[0], element[1][0], element[1][1], element[1][2]), \
                   zip(ids, map(get_hepdata_by_recid_raw, ids))))

def get_attached_hepdata_dataset_ids(recid):
    """Returns all identifeirs of datasets attached to a given publication

    @param recid: The identifeir of record to which datasets are attached
    @type recid: Integer
    @rtype: intbitset
    @returns: intbitset of all the record identifeirs
              """
    return search_engine.search_pattern(p="%s:%s" % (CFG_HEPDATA_FIELD, str(recid),))

def get_attached_hepdata_datasets(recid):
    """For a given recid, retrieves recids of datasets that are related
    to a publication

    @param recid: The identifeir of record to which datasets are attached
    @type recid: Integer
    @rtype:  Lsit of tuples
    @returns: List of tuples (recid, Dataset isntance) where recid is the
              identifer of a record representing given dataset
    """
    # Search for all the records refering to a given one
    recids = get_attached_hepdata_dataset_ids(recid)
    return zip(recids, map(
            lambda dsrecid: get_hepdata_by_recid(recid, dsrecid), recids))

# Universal log

def hepdata_log(category, msg):
    """Log an important event that should be processed by the administrator
       manually"""
    log_path = os.path.join(CFG_LOGDIR, "hepdata.log")
    f = open(log_path, "a")
    f.write("%s %s: %s\n" % (str(datetime.now()), category, msg))
    f.close()


# The harvesting daemon

def hepdata_get_latest_changes_identifiers(starting_date):
    url = CFG_HEPDATA_URL + "/AllIds/" + starting_date
    page_content = download_with_retry(url)
    matches = re.search("<pre>([^<]*)</pre>", page_content)
    json_string = matches.groups()[0].replace(",,", ",0,")
    return json.loads(json_string)[:-1] # We ommit the last 0,0,0 entry

def hepdata_get_all_identifiers():
    page_content = download_with_retry(get_hepdata_allids_url())
    matches = re.search("<pre>([^<]*)</pre>", page_content)
    json_string = matches.groups()[0].replace(",,", ",0,")
    return json.loads(json_string)[:-1] # We ommit the last 0,0,0 entry


def hepdata_harvest_get_identifiers(starting_date=None):
    """
    Retrieves identifiers of records that should be processed searching for
    corresponding HEPData entry
    """
    if task_has_option('record_to_harvest'):
        yield task_get_option('record_to_harvest')
    else:
        used_ids = set() # sometimes records are reported many times
        if starting_date:
            for res in hepdata_get_latest_changes_identifiers(starting_date):
                if res[0] and not res[0] in used_ids:
                    used_ids.add(res[0])
                    yield res[0]
        else:
            for res in hepdata_get_all_identifiers():
                if res[0] and not res[0] in used_ids:
                    used_ids.add(res[0])
                    yield res[0]


def prepare_hepdata_for_upload(recid, hepdata, insert_stream, correct_stream,
                               task_stats, force_reupload=False):

    """Retrieve a single entry from HEPData and create MARC XML files to
       upload to Inspire
       Uploaded files are:
          - patch to the original MARC record (assigning the link if it is
            inconsistent with the current one)
          - marc files for new records

       @param invenio_id: Number of the record inside current Invenio
                         installation
       @type invenio_id: Integer

       @param hepdata: Paper object representing current state of HEPData
                     (downloaded from the website)
       @type hepdata: Paper

       @param insert_stream: Queue.Queue of string reperesentations of records that will
                            be passed to bibupload in the insert mode
       @type insert_stream: Queue.Queue of strings

       @param correct_stream: Queue.Queue of string reperesentations of records that
                             will be passed to bibupload in the correct mode
       @type correct_stream: Queue.Queue of strings
       """


    # 1) check the inspire number that is related to the
    # How to detect if there is already an entry for HEPData try to upload
    # the description
    # Retrieve dataset records attached to the record.
    dataset_records = get_attached_hepdata_records(recid)

    get_record_pos = lambda entry: Dataset.create_from_record(entry[1], entry[2], None, None).position
    dataset_records.sort(cmp = lambda x, y: cmp(get_record_pos(x),get_record_pos(y)))

    #Applying changes to subsequent datasets !
    #   (The position is what matters in terms of uniqueness)
    hepdata_datasets = hepdata.datasets

    # 1) making lists have the same length
    len_diff = len(dataset_records) - len(hepdata_datasets)
    if len_diff > 0:
        hepdata_datasets += [None] * len_diff
    else:
        dataset_records += [None] * (-len_diff)

    import tempfile

#    fdesc, fname = tempfile.mkstemp()
#    os.write(fdesc, cPickle.dumps([dataset_records, hepdata_datasets]))
#    os.close(fdesc)
#    print "Retrieved datasets : %s" % (fname, )

    num_deleted = 0
    num_added = 0
    num_modified = 0
    for (inv_dataset, hep_dataset) in zip(dataset_records, hepdata_datasets):
        if inv_dataset is None:
            # create completely new record

            insert_stream.put_nowait(hep_dataset.get_marcxml(recid))
            if task_stats["semaphore"]:
                task_stats["semaphore"].acquire()

            task_stats["inserted_hepdata_datasets"] += 1
            if task_stats["semaphore"]:
                task_stats["semaphore"].release()
            num_added += 1
        elif hep_dataset is None:
            # delete invenio record corresponding to a data set
            if task_stats["semaphore"]:
                task_stats["semaphore"].acquire()
            task_stats["deleted_hepdata_datasets"] += 1
            if task_stats["semaphore"]:
                task_stats["semaphore"].release()

            rec = {}
            bibrecord.record_add_field(rec, "980", subfields = \
                                           [("c", "DELETED")])
            bibrecord.record_add_field(rec, "001", controlfield_value = \
                                           str(inv_dataset[0]))
            correct_stream.put_nowait(bibrecord.record_xml_output(rec))
            num_deleted += 1
        else:
            diff_xml = hep_dataset.get_diff_marcxml(inv_dataset[1], recid, inv_dataset[2], inv_dataset[3], force_reupload=force_reupload)
            if diff_xml:
                if task_stats["semaphore"]:
                    task_stats["semaphore"].acquire()
                task_stats["corrected_hepdata_datasets"] += 1
                if task_stats["semaphore"]:
                    task_stats["semaphore"].release()

                correct_stream.put_nowait(diff_xml)
                num_modified += 1

    # assure that the original MARC record is correct
    rec = search_engine.get_record(recid)
    if rec:
        diff_marcxml = hepdata.get_diff_marcxml(rec)
        if diff_marcxml:
            correct_stream.put_nowait(diff_marcxml)
            #        task_stats["new_hepdata_records"] += 1
    return num_added, num_deleted, num_modified


def get_data_line_length(data_line):
    """return a real width in columns of a data line"""
    d_len = 0
    for d in data_line:
        d_len += d["colspan"]
    return d_len

def calculate_columns_number(dataset):
    """Retrieve the real number of columns - maximum over data columns,
    header columns and titles"""
    max_len = 0

    for data_l in dataset.data:
        if get_data_line_length(data_l) > max_len:
            max_len = get_data_line_length(data_l)

    for data_l in dataset.data_qualifiers:
        if get_data_line_length(data_l) > max_len:
            max_len = get_data_line_length(data_l)


    if get_data_line_length(dataset.column_headers) > max_len:
        max_len = get_data_line_length(dataset.column_headers)

    if get_data_line_length(dataset.column_titles) > max_len:
        max_len = get_data_line_length(dataset.column_titles)

    return max_len

def hepdata_harvest_task_submit_elaborate_specific_parameter(key, value, opts, args):
    """ Given the string key it checks it's meaning, eventually using the
    value. Usually it fills some key in the options dict.
    It must return True if it has elaborated the key, False, if it doesn't
    know that key.
    eg:
    if key in ['-n', '--number']:
        task_get_option(\1) = value
        return True
    return False
    """
    if key in ("--recid", "-r"):
        task_set_option('record_to_harvest', value)
    elif key in ("--nthreads", "-n"):
        task_set_option('threads_number', value)
    elif key in ("--force-reupload", "-f"):
        task_set_option('force_reupload', True)
    elif key in ("--starting-date", "-d"):
        task_set_option('starting_date', value)
    else:
        return False
    return True

def hepdata_harvest_main():
    """The main function of the HEPData harvesting daemon executed via BibSched.
       This daemon harvests the complete HEPData set and uploads modifications
       to Inspire.
    """
    task_init(authorization_action = 'runhepdataharvest',
            authorization_msg = "HEPDataHarvest Task Submission",
            description = """Retrieve HEPData and attach them to correcponding
Invenio records.

Examples:
    $ hepdataharvest -r 12
""",
            help_specific_usage = \
"""  -r, --recid The identifier of the record  that should be reharvested
                 from HEPData
  -n, --nthreads Number of concurrent harvesting threads. This number is
                equal to the number of HTTP requests performed at the same
                time
  -f, --force-reupload Forces the harvester to reupload all data files
""",
            version=__revision__,
            specific_params=("r:n:f:d:",
                 [ "recid=", "nthreads=", "force-reupload", "starting-date=" ]),
            task_submit_elaborate_specific_parameter_fnc =
              hepdata_harvest_task_submit_elaborate_specific_parameter,
            task_run_fnc = hepdata_harvest_task_core)


def write_xml_stream_to_tmpfile(stream, prefix):
    """
    Stream: list of strings
    writes a list of strings into a temporary MARCXML file.
    The collection header and footer together with the XML
    structure are added

    @return Name of the temporary file
    """
    if not stream:
        # We do not want to write in the case of empty input
        return None


    import tempfile
    fdesc, fname = tempfile.mkstemp(suffix = ".xml", prefix = prefix, \
                                        dir = CFG_TMPSHAREDDIR)
    os.write(fdesc, """<?xml version="1.0" encoding="UTF-8"?>
<collection xmlns="http://www.loc.gov/MARC21/slim">""")
    for part in stream:
        os.write(fdesc, part)
    os.write(fdesc, "</collection>")

    os.close(fdesc)
    return fname

def update_single_status(recid, processed_recs, total_recs):
    """Update the BibSched task status"""
    from math import floor
    progress = floor(float(processed_recs * 1000) / total_recs)/10
    task_update_progress("Harvested %i records out of %i ( %s%% ) " % (processed_recs, total_recs, str(progress)))


def process_single_thread(input_recids, insert_queue, correct_queue, failed_ids, task_stats, suspend_wait_queue, suspend_resume_queue, main_syn_queue, num_tasks, finished_queue = None, total_recs=0, force_reupload = False):
    finished = False
    processed_recs = 0
    while not finished:
        try:
            recid = input_recids.get_nowait()
        except:
            finished = True

        if not finished:
            try:
                hepdata = retrieve_hepdata(get_hepdata_url_from_recid(recid), recid)
                try:
                    if not recid:
                        write_message("Problem! No recid present: %s" % (str(input_recids.queue)))
                    num_added, num_deleted, num_modified = prepare_hepdata_for_upload(
                        recid, hepdata, insert_queue, correct_queue,
                        task_stats, force_reupload = force_reupload)
                    write_message("Retrieved data for record %s: %i record added, %i records deleted, %i records modified" % (str(recid), num_added, num_deleted, num_modified ))

                except Exception, e:
                    write_message("Error: merging HepData for record %s failed: %s" \
                                      % (str(recid), str(e)))
                    failed_ids.put_nowait((str(recid), "Failed during the merging phase: %s" % (str(e), )))

            except Exception, e:
                write_message("Error: retrieving HEPData for record %s failed: %s" \
                                  % (str(recid), str(e)))
                failed_ids.put_nowait((str(recid), "Failed during the retrieval phase: %s" % (str(e), )))


            if finished_queue:
                finished_queue.put_nowait(str(recid))
            else:
                processed_recs +=1
                update_single_status(str(recid), processed_recs, total_recs)
            #Possibly trying to stop
            task_status = task_read_status()
            if task_status.startswith("ABOUT TO"):
                if num_tasks == 1:
                    task_sleep_now_if_required(True)
                else:
                    suspend_wait_queue.get()
                    write_message("Thread suspended")
                    if suspend_wait_queue.empty():
                        main_syn_queue.put("SLEEP")

                    suspend_resume_queue.get()
                    suspend_wait_queue.put(1)
                    write_message("Thread resumed")
            elif task_status == "KILLED":
                if num_tasks > 1:
                    main_syn_queue.put("KILLED")
                else:
                    exit(0)
                finished = True

    if num_tasks > 1: #signalise that this is the end of execution of some thread
        main_syn_queue.put("FINISH")

class RetrievalWorker(threading.Thread):
    def __init__(self, recids_queue, insert_queue, correct_queue, finished_queue, failed_ids, task_stats, suspend_wait_queue, suspend_resume_queue, main_syn_queue, num_tasks, force_reupload=False):
        threading.Thread.__init__(self)
        self.input_recids = recids_queue
        self.insert_queue = insert_queue
        self.correct_queue = correct_queue
        self.finished_queue = finished_queue
        self.failed_ids = failed_ids
        self.task_stats = task_stats
        self.suspend_wait_queue = suspend_wait_queue
        self.suspend_resume_queue = suspend_resume_queue
        self.num_tasks = num_tasks
        self.main_syn_queue = main_syn_queue
        self.daemon = True
        self.force_reupload = force_reupload

    def run(self):
        process_single_thread(self.input_recids, self.insert_queue, self.correct_queue,\
                                  self.failed_ids, self.task_stats, self.suspend_wait_queue, \
                                  self.suspend_resume_queue, self.main_syn_queue, self.num_tasks, self.finished_queue, force_reupload = self.force_reupload)

class StatusUpdater(threading.Thread):
    """This thread is used only to update the BibSched status"""
    def __init__(self, total_records, finished_queue):
        threading.Thread.__init__(self)
        self.total_records = total_records
        self.total_finished = 0
        self.finished_queue = finished_queue

    def run(self):
        while self.total_finished != self.total_records:
            finished_rec = self.finished_queue.get()
            self.total_finished += 1
            update_single_status(finished_rec, self.total_finished, self.total_records)

class SingleThreadQueue(object):
    """simple queue implementation for the case of a single processing thread.
     Standard queue implementation involves threads anyway"""

    def __init__(self):
        self.queue = []
        self.pointer = 0

    def put(self, el):
        self.queue.append(el)

    def put_nowait(self, el):
        self.queue.append(el)

    def get_nowait(self):
        self.pointer += 1
        return self.queue[self.pointer - 1]

    def get(self):
        self.pointer += 1
        return self.queue[self.pointer - 1]

    def empty(self):
        return self.pointer == len(self.queue)

def get_number_of_harvesting_threads():
    """Read the task parameters to retrieve the number of concurrent threads\
       The default threads number is encoded in the configuration file
    """
    if task_has_option("threads_number"):
        return int(task_get_option("threads_number"))
    return int(CFG_HEPDATA_THREADS_NUM)

def get_forceupload_param():
    """Read the task parameters to retrieve the information if data files should be reuploaded
    """
    if task_has_option("force_reupload"):
        return bool(task_get_option("force_reupload"))
    return False

def get_starting_date_param():
    """Read the task parameters or the config file to retrieve the starting date for harvest
        If is not provided, it will start from the beginning of times
    """
    # if forced
    if task_has_option("starting_date"):
        return str(task_get_option("starting_date"))
    # from file
    try:
        return open(CFG_TMPSHAREDDIR + "/hepdata-lastharvest.txt", "r+").read()
    except IOError:
        # not provided
        return "19700101"

def update_last_harvest():
    """ Updates the last harvest date
    """
    starting_time = task_get_task_param('task_starting_time')
    starting_date = time.strftime("%Y%m%d", time.strptime(starting_time, "%Y-%m-%d %H:%M:%S"))
    open(CFG_TMPSHAREDDIR + "/hepdata-lastharvest.txt", "w").write(starting_date)
    write_message("Updated last harvesest: %s" % starting_date)

def hepdata_harvest_task_core():
    def kill_handler(signum, frame):
        write_message('KILLED')
        exit(0)
    signal.signal(signal.SIGTERM, kill_handler)

    number_threads = get_number_of_harvesting_threads()
    force_reupload = get_forceupload_param()
    starting_date = get_starting_date_param()

    write_message("STARTING DATE: %s" % starting_date)

    task_stats = {
        "new_hepdata_records" : 0,
        "inserted_hepdata_datasets" : 0,
        "corrected_hepdata_datasets" : 0,
        "deleted_hepdata_datasets" : 0
        }

    if number_threads > 1:
        insert_queue = Queue.Queue()
        correct_queue = Queue.Queue()
        failed_ids = Queue.Queue()
        recs_queue = Queue.Queue()
        finished_queue = Queue.Queue()
        suspend_resume_queue = Queue.Queue()
        suspend_wait_queue = Queue.Queue()
        main_syn_queue = Queue.Queue()
        task_stats["semaphore"] = threading.Semaphore()

    else:
        insert_queue = SingleThreadQueue()
        correct_queue = SingleThreadQueue()
        failed_ids = SingleThreadQueue()
        recs_queue = SingleThreadQueue()
        task_stats["semaphore"] = None

    write_message("STAGE0: Harvesting data and building the input")

    # feed the input queue
    total_recs = 0
    for recid in hepdata_harvest_get_identifiers(starting_date):
        recs_queue.put_nowait(recid)
        total_recs += 1
    # spawn necessary number of workers (try not to spawn more than necessary)


    if number_threads > 1:
        for i in xrange(number_threads):
            suspend_wait_queue.put(1)
        ts = [RetrievalWorker(recs_queue, insert_queue, correct_queue, finished_queue, failed_ids, task_stats, suspend_wait_queue, suspend_resume_queue, main_syn_queue, number_threads, force_reupload = force_reupload) for i in xrange(number_threads)]
        update_t = StatusUpdater(total_recs, finished_queue)
        # start all the tasks

        for t in ts:
            t.start()
        update_t.start()
        write_message("Started all %i workers" % (number_threads, ))

        while True:
            token = main_syn_queue.get()
            if token == "SLEEP":
                task_sleep_now_if_required(True)

                for i in xrange(number_threads):
                    suspend_resume_queue.put(1)
            elif token == "KILLED":
                exit(0)
            else:
                break


        for t in ts:
            t.join()

        update_t.join()

    else:
        #just perform calculations
        write_message("started single processing thread")
        process_single_thread(recs_queue, insert_queue, correct_queue, failed_ids, task_stats, None, None, None, 1, total_recs = total_recs, force_reupload = force_reupload)

    # collect results and return
    f_i = list(failed_ids.queue)

    write_message("STAGE0 finished: %i records failed : %s" % \
                      (len(f_i), ", ".join(map(lambda x: "Record %s failed: %s" % (str(x[0]), str(x[1])), f_i))))

    i_q = list(insert_queue.queue)
    insert_fname = write_xml_stream_to_tmpfile(i_q,
                                               prefix = "hepdata_insert_")

    c_q = list(correct_queue.queue)
    correct_fname = write_xml_stream_to_tmpfile(c_q,
                                                prefix = "hepdata_correct_")

    write_message("STAGE0: input file: %s, correct file: %s" % \
                      (str(insert_fname), str(correct_fname)))

    write_message("STAGE1: spawning bibupload tasks")
    insert_tasknum = -1
    if insert_fname:
        insert_tasknum = task_low_level_submission("bibupload",
                                                   "admin", "-i",
                                                   insert_fname)

    correct_tasknum = -1
    if correct_fname:
        correct_tasknum = task_low_level_submission("bibupload",
                                                    "admin", "-c",
                                                    correct_fname)

    if correct_fname or insert_fname:
        index_tasknum = task_low_level_submission("bibindex",
                                                  "admin", "-w",
                                                  CFG_HEPDATA_INDEX)
        index_tasknum = task_low_level_submission("webcoll",
                                                  "admin", "-c",
                                                  "DATA")

    write_message(("Task summary: Inserted %(new_hepdata_records)i new" + \
                       "HepDATA records, %(inserted_hepdata_datasets)i " + \
                       "new datasets, corrected " + \
                       "%(corrected_hepdata_datasets)i" + \
                       " datasets, removed %(deleted_hepdata_datasets)i") \
                      % task_stats)
    write_message("   Spawned BibUpload tasks: insert: %i, correct: %i" % \
                      (insert_tasknum, correct_tasknum))
    update_last_harvest()
    return True


def create_hepdata_ticket(recid, msg, queue="Data_Exceptions"):
    """
    Creates a ticket when something goes wrong in rendering HepData
    records.
    """
    from invenio.bibcatalog_task import BibCatalogTicket
    subject = "Problem in data record %s: %s" % (str(recid),
                                                 msg[:30])
    body = """
    There is a problem in record: %(siteurl)s/%(record)s/%(recid)s

    %(msg)s
    """ % {
        'siteurl': CFG_SITE_SECURE_URL,
        'record': CFG_SITE_RECORD,
        'recid': recid,
        'msg': msg
    }
    ticket = BibCatalogTicket(subject=subject,
                              body=body,
                              queue=queue,
                              recid=recid)
    ticket.submit()

if __name__ == "__main__":
    # JUST DEBUG DO NOT USE ATM
    paper = download_paper("http://hepdata.cedar.ac.uk/view/ins1094568", None)
    #    for dataset in paper.datasets:
    print "MARCXML : " + paper.datasets[0].get_marcxml()
