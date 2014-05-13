# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013 CERN.
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

from datetime import datetime

from invenio.docextract_record import BibRecord, \
                                      BibRecordField
from invenio.refextract_config import \
    CFG_REFEXTRACT_FIELDS, \
    CFG_REFEXTRACT_IND1_REFERENCE, \
    CFG_REFEXTRACT_IND2_REFERENCE, \
    CFG_REFEXTRACT_TAG_ID_EXTRACTION_STATS, \
    CFG_REFEXTRACT_SUBFIELD_EXTRACTION_STATS, \
    CFG_REFEXTRACT_SUBFIELD_EXTRACTION_TIME, \
    CFG_REFEXTRACT_SUBFIELD_EXTRACTION_VERSION, \
    CFG_REFEXTRACT_VERSION

from invenio import config
CFG_INSPIRE_SITE = getattr(config, 'CFG_INSPIRE_SITE', False)


def format_marker(line_marker):
    return line_marker.strip("[](){}. ")


def build_record(counts, fields, recid=None, status_code=0):
    """Given a series of MARC XML-ized reference lines and a record-id, write a
       MARC XML record to the stdout stream. Include in the record some stats
       for the extraction job.
       The printed MARC XML record will essentially take the following
       structure:
        <record>
           <controlfield tag="001">1</controlfield>
           <datafield tag="999" ind1="C" ind2="5">
              [...]
           </datafield>
           [...]
           <datafield tag="999" ind1="C" ind2="6">
              <subfield code="a">
        Invenio/X.XX.X refextract/X.XX.X-timestamp-err-repnum-title-URL-misc
              </subfield>
           </datafield>
        </record>
       Timestamp, error(code), reportnum, title, URL, and misc will are of
       course take the relevant values.

       @param status_code: (integer)the status of reference-extraction for the
        given record: was there an error or not? 0 = no error; 1 = error.
       @param count_reportnum: (integer) - the number of institutional
        report-number citations found in the document's reference lines.
       @param count_title: (integer) - the number of journal title citations
        found in the document's reference lines.
       @param count_url: (integer) - the number of URL citations found in the
        document's reference lines.
       @param count_misc: (integer) - the number of sections of miscellaneous
        text (i.e. 999C5$m) from the document's reference lines.
       @param count_auth_group: (integer) - the total number of author groups
        identified ($h)
       @param recid: (string) - the record-id of the given document. (put into
        001 field.)
       @param xml_lines: (list) of strings. Each string in the list contains a
        group of MARC XML 999C5 datafields, making up a single reference line.
        These reference lines will make up the document body.
       @return: The entire MARC XML textual output, plus recognition statistics.
    """
    record = BibRecord(recid=recid)
    record['999'] = fields
    field = record.add_field(CFG_REFEXTRACT_TAG_ID_EXTRACTION_STATS)
    stats_str = "%(status)s-%(reportnum)s-%(title)s-%(author)s-%(url)s-%(doi)s-%(misc)s" % {
           'status'             : status_code,
           'reportnum'          : counts['reportnum'],
           'title'              : counts['title'],
           'author'             : counts['auth_group'],
           'url'                : counts['url'],
           'doi'                : counts['doi'],
           'misc'               : counts['misc'],
    }
    field.add_subfield(CFG_REFEXTRACT_SUBFIELD_EXTRACTION_STATS,
                       stats_str)
    field.add_subfield(CFG_REFEXTRACT_SUBFIELD_EXTRACTION_TIME,
                       datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    field.add_subfield(CFG_REFEXTRACT_SUBFIELD_EXTRACTION_VERSION,
                       CFG_REFEXTRACT_VERSION)

    return record


def build_references(citations):
    """Build marc xml from a references list

    Transform the reference elements into marc xml
    """
    # Now, run the method which will take as input:
    # 1. A list of lists of dictionaries, where each dictionary is a piece
    # of citation information corresponding to a tag in the citation.
    # 2. The line marker for this entire citation line (mulitple citation
    # 'finds' inside a single citation will use the same marker value)
    # The resulting xml line will be a properly marked up form of the
    # citation. It will take into account authors to try and split up
    # references which should be read as two SEPARATE ones.
    return [c for citation_elements in citations
              for elements in citation_elements['elements']
              for c in build_reference_fields(elements,
                                             citation_elements['line_marker'])]


def add_subfield(field, code, value):
    return field.add_subfield(CFG_REFEXTRACT_FIELDS[code], value)


def add_journal_subfield(field, element, inspire_format):
    if inspire_format:
        value = '%(title)s,%(volume)s,%(page)s' % element
    else:
        value = '%(title)s %(volume)s (%(year)s) %(page)s' % element

    return add_subfield(field, 'journal', value)


def create_reference_field(line_marker):
    field = BibRecordField(ind1=CFG_REFEXTRACT_IND1_REFERENCE,
                           ind2=CFG_REFEXTRACT_IND2_REFERENCE)
    if line_marker.strip("., [](){}"):
        add_subfield(field, 'linemarker', format_marker(line_marker))
    return field


def build_reference_fields(citation_elements, line_marker, inspire_format=None):
    """ Create the MARC-XML string of the found reference information which
        was taken from a tagged reference line.
        @param citation_elements: (list) an ordered list of dictionary elements,
                                  with each element corresponding to a found
                                  piece of information from a reference line.
        @param line_marker: (string) The line marker for this single reference
                            line (e.g. [19])
        @return xml_line: (string) The MARC-XML representation of the list of
                          reference elements
    """
    if inspire_format is None:
        inspire_format = CFG_INSPIRE_SITE

    # Begin the datafield element
    current_field = create_reference_field(line_marker)

    reference_fields = [current_field]

    for element in citation_elements:
        # Before going onto checking 'what' the next element is, handle misc text and semi-colons
        # Multiple misc text subfields will be compressed later
        # This will also be the only part of the code that deals with MISC tag_typed elements
        misc_txt = element['misc_txt']
        if misc_txt.strip("., [](){}"):
            misc_txt = misc_txt.lstrip('])} ,.').rstrip('[({ ,.')
            add_subfield(current_field, 'misc', misc_txt)

        # Now handle the type dependent actions
        # JOURNAL
        if element['type'] == "JOURNAL":
            add_journal_subfield(current_field, element, inspire_format)

        # REPORT NUMBER
        elif element['type'] == "REPORTNUMBER":
            add_subfield(current_field, 'reportnumber', element['report_num'])

        # URL
        elif element['type'] == "URL":
            if element['url_string'] == element['url_desc']:
                # Build the datafield for the URL segment of the reference line:
                add_subfield(current_field, 'url', element['url_string'])
            # Else, in the case that the url string and the description differ in some way, include them both
            else:
                add_subfield(current_field, 'url', element['url_string'])
                add_subfield(current_field, 'urldesc', element['url_desc'])

        # DOI
        elif element['type'] == "DOI":
            add_subfield(current_field, 'doi', 'doi:' + element['doi_string'])
        # HDL
        elif element['type'] == "HDL":
            add_subfield(current_field, 'hdl', 'hdl:' + element['hdl_id'])

        # AUTHOR
        elif element['type'] == "AUTH":
            value = element['auth_txt']
            if element['auth_type'] == 'incl':
                value = "(%s)" % value

            add_subfield(current_field, 'author', value)

        elif element['type'] == "QUOTED":
            add_subfield(current_field, 'title', element['title'])

        elif element['type'] == "ISBN":
            add_subfield(current_field, 'isbn', element['ISBN'])

        elif element['type'] == "BOOK":
            add_subfield(current_field, 'title', element['title'])

        elif element['type'] == "PUBLISHER":
            add_subfield(current_field, 'publisher', element['publisher'])

        elif element['type'] == "YEAR":
            add_subfield(current_field, 'year', element['year'])

        elif element['type'] == "COLLABORATION":
            add_subfield(current_field,
                         'collaboration',
                         element['collaboration'])

        elif element['type'] == "RECID":
            add_subfield(current_field, 'recid', str(element['recid']))

    for field in reference_fields:
        merge_misc(field)

    return reference_fields


def merge_misc(field):
    current_misc = None
    for subfield in field.subfields[:]:
        if subfield.code == 'm':
            if current_misc is None:
                current_misc = subfield
            else:
                current_misc.value += " " + subfield.value
                field.subfields.remove(subfield)
