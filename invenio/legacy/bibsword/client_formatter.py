##This file is part of Invenio.
# Copyright (C) 2010, 2011 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

'''
BibSWORD Client Formatter
'''

import zipfile
import os
from tempfile import mkstemp
from xml.dom import minidom
from invenio.config import CFG_TMPDIR
from invenio.legacy.bibsched.bibtask import task_low_level_submission
from invenio.legacy.bibsword.config import CFG_MARC_REPORT_NUMBER, \
                                    CFG_MARC_TITLE, \
                                    CFG_MARC_AUTHOR_NAME, \
                                    CFG_MARC_AUTHOR_AFFILIATION, \
                                    CFG_MARC_CONTRIBUTOR_NAME, \
                                    CFG_MARC_CONTRIBUTOR_AFFILIATION, \
                                    CFG_MARC_ABSTRACT, \
                                    CFG_MARC_ADDITIONAL_REPORT_NUMBER, \
                                    CFG_MARC_DOI, \
                                    CFG_MARC_JOURNAL_REF_CODE, \
                                    CFG_MARC_JOURNAL_REF_TITLE, \
                                    CFG_MARC_JOURNAL_REF_PAGE, \
                                    CFG_MARC_JOURNAL_REF_YEAR, \
                                    CFG_MARC_COMMENT, \
                                    CFG_MARC_RECORD_SUBMIT_INFO, \
                                    CFG_SUBMIT_ARXIV_INFO_MESSAGE, \
                                    CFG_DOCTYPE_UPLOAD_COLLECTION, \
                                    CFG_SUBMISSION_STATUS_SUBMITTED, \
                                    CFG_SUBMISSION_STATUS_PUBLISHED, \
                                    CFG_SUBMISSION_STATUS_ONHOLD, \
                                    CFG_SUBMISSION_STATUS_REMOVED
from invenio.legacy.bibdocfile.api import BibRecDocs
from invenio.modules.formatter.engine import BibFormatObject

#-------------------------------------------------------------------------------
# Formating servicedocument file
#-------------------------------------------------------------------------------

def format_remote_server_infos(servicedocument):
    '''
        Get all informations about the server's options such as SWORD version,
        maxUploadSize, ... These informations are found in the servicedocument
        of the given server
        @param servicedocument: xml servicedocument in a string format
        @return: server_infomation. tuple containing the version, the
                                      maxUploadSize and the available modes
    '''

    #contains information tuple {'version', 'maxUploadSize', 'verbose', 'noOp'}
    server_informations = {'version' : '',
                           'maxUploadSize' : '',
                           'verbose' : '',
                           'noOp' : '',
                           'error' : '' }

    # now the xml node are accessible by programation
    try:
        parsed_xml_collections = minidom.parseString(servicedocument)
    except IOError:
        server_informations['error'] = \
            'No servicedocument found for the remote server'
        return server_informations

    # access to the root of the xml file
    xml_services = parsed_xml_collections.getElementsByTagName('service')
    xml_service = xml_services[0]

    # get value of the node <sword:version>
    version_node = xml_service.getElementsByTagName('sword:version')[0]
    server_informations['version'] = \
        version_node.firstChild.nodeValue.encode('utf-8')

    # get value of the node <sword:maxUploadSize>
    max_upload_node = xml_service.getElementsByTagName('sword:maxUploadSize')[0]
    server_informations['maxUploadSize'] = \
        max_upload_node.firstChild.nodeValue.encode('utf-8')


    # get value of the node <sword:verbose>
    verbose_node = xml_service.getElementsByTagName('sword:verbose')[0]
    server_informations['verbose'] = \
        verbose_node.firstChild.nodeValue.encode('utf-8')

    # get value of the node <sword:noOp>
    no_op_node = xml_service.getElementsByTagName('sword:noOp')[0]
    server_informations['noOp'] = \
        no_op_node.firstChild.nodeValue.encode('utf-8')

    return server_informations


def format_remote_collection(servicedocument):
    '''
        The function parse the servicedocument document and return a list with
        the collections of the given file ['id', 'name', 'url']
        @param servicedocument: xml file returned by the remote server.
        @return: the list of collection found in the service document
    '''

    collections = []  # contains list of collection tuple {'id', 'url', 'label'}

    # get the collections root node
    collection_nodes = parse_xml_servicedocument_file(servicedocument)

    # i will be the id of the collection
    i = 1

    #---------------------------------------------------------------------------
    # recuperation of the collections
    #---------------------------------------------------------------------------

    # loop that goes in each node's collection of the document
    for collection_node in collection_nodes:

        # dictionnary that contains the collections
        collection = {}

        collection['id'] = str(i)
        i = i + 1

        # collection uri (where to deposit the media)
        collection['url'] = \
            collection_node.attributes['href'].value.encode('utf-8')

        # collection name that is displayed to the user
        xml_title = collection_node.getElementsByTagName('atom:title')
        collection['label'] = xml_title[0].firstChild.nodeValue.encode('utf-8')

        # collection added to the collections list
        collections.append(collection)

    return collections


def format_collection_informations(servicedocument, id_collection):
    '''
        This methode parse the given servicedocument to find the given collection
        node. Then it retrieve all information about the collection that contains
        the collection node.
        @param servicedocument:  xml file returned by the remote server.
        @param id_collection: position of the collection in the sd (1 = first)
        @return: (collection_informations) tuple containing infos
    '''

    # contains information tuple {[accept], 'collectionPolicy', 'mediation',
    #                                      'treatment', 'accept_packaging'}
    collection_informations = {}

    # get the collections root node
    collection_nodes = parse_xml_servicedocument_file(servicedocument)

    # recuperation of the selected collection
    collection_node = collection_nodes[int(id_collection)-1]

    # get value of the nodes <accept>
    accept_nodes = collection_node.getElementsByTagName('accept')
    accept = []
    for accept_node in accept_nodes:
        accept.append(accept_node.firstChild.nodeValue.encode('utf-8'))

    collection_informations['accept'] = accept

    # get value of the nodes <sword:collectionPolicy>
    collection_policy = \
        collection_node.getElementsByTagName('sword:collectionPolicy')[0]
    collection_informations['collectionPolicy'] = \
        collection_policy.firstChild.nodeValue.encode('utf-8')

    # get value of the nodes <sword:mediation>
    mediation = collection_node.getElementsByTagName('sword:mediation')[0]
    collection_informations['mediation'] = \
        mediation.firstChild.nodeValue.encode('utf-8')

    # get value of the nodes <sword:treatment>
    treatment = collection_node.getElementsByTagName('sword:treatment')[0]
    collection_informations['treatment'] = \
        treatment.firstChild.nodeValue.encode('utf-8')

    # get value of the nodes <sword:acceptPackaging>
    accept_packaging = \
        collection_node.getElementsByTagName('sword:acceptPackaging')[0]
    collection_informations['accept_packaging'] = \
        accept_packaging.firstChild.nodeValue.encode('utf-8')

    return collection_informations


def format_primary_categories(servicedocument, collection_id=0):
    '''
        This method parse the servicedocument to retrieve the primary category
        of the given collection. If no collection is given, it takes the first
        one.
        @param servicedocument: xml file returned by the remote server.
        @param collection_id: id of the collection to search
        @return: list of primary categories tuple ('id', 'url', 'label')
    '''

    categories = []  # contains list of category tuple {'id', 'url', 'label'}

    # get the collections root node
    collection_nodes = parse_xml_servicedocument_file(servicedocument)

    # i will be the id of the collection
    i = 1

    # recuperation of the selected collection
    collection_node = collection_nodes[int(collection_id)-1]

    #---------------------------------------------------------------------------
    # recuperation of the categories
    #---------------------------------------------------------------------------

    # select all primary category nodes
    primary_categories_node = \
        collection_node.getElementsByTagName('arxiv:primary_categories')[0]
    primary_category_nodes = \
        primary_categories_node.getElementsByTagName('arxiv:primary_category')

    # loop that goes in each primary_category nodes
    for primary_category_node in primary_category_nodes:

        # dictionnary that contains the categories
        category = {}

        category['id'] = str(i)
        i = i + 1

        category['url'] = \
            primary_category_node.attributes['term'].value.encode('utf-8')
        category['label'] = \
            primary_category_node.attributes['label'].value.encode('utf-8')

        categories.append(category)

    return categories


def format_secondary_categories(servicedocument, collection_id=0):
    '''
        This method parse the servicedocument to retrieve the optional categories
        of the given collection. If no collection is given, it takes the first
        one.
        @param servicedocument: xml file returned by the remote server.
        @param collection_id: id of the collection to search
        @return: list of optional categories tuple ('id', 'url', 'label')
    '''

    categories = []  # contains list of category tuple {'id', 'url', 'label'}

    # get the collections root node
    collection_nodes = parse_xml_servicedocument_file(servicedocument)

    # i will be the id of the collection
    i = 1

    # recuperation of the selected collection
    collection_id = int(collection_id) - 1
    collection_node = collection_nodes[int(collection_id)]

    #---------------------------------------------------------------------------
    # recuperation of the categories
    #---------------------------------------------------------------------------

    # select all primary category nodes
    categories_node = collection_node.getElementsByTagName('categories')[0]
    category_nodes = categories_node.getElementsByTagName('category')

    # loop that goes in each primary_category nodes
    for category_node in category_nodes:

        # dictionnary that contains the categories
        category = {}

        category['id'] = str(i)
        i = i + 1

        category['url'] = category_node.attributes['term'].value.encode('utf-8')
        category['label'] = \
            category_node.attributes['label'].value.encode('utf-8')

        categories.append(category)

    return categories


def parse_xml_servicedocument_file(servicedocument):
    '''
        This method parse a string containing a servicedocument to retrieve the
        collection node. It is used by all function that needs to work with
        collections
        @param servicedocument: xml file in containing in a string
        @return: (collecion_node) root node of all collecions
    '''

    # now the xml node are accessible by programation
    parsed_xml_collections = minidom.parseString(servicedocument)

    # access to the root of the xml file
    xml_services = parsed_xml_collections.getElementsByTagName('service')
    xml_service = xml_services[0]

    # their is only the global workspace in this xml document
    xml_workspaces = xml_service.getElementsByTagName('workspace')
    xml_workspace = xml_workspaces[0]

    # contains all collections in the xml file
    collection_nodes = xml_workspace.getElementsByTagName('collection')

    return collection_nodes


#-------------------------------------------------------------------------------
# Formating marcxml file
#-------------------------------------------------------------------------------

def get_report_number_from_macrxml(marcxml):
    '''
        retrieve the record id stored in the marcxml file. The record is in the
        tag 'RECORD ID'
        @param marcxml: marcxml file where to look for the record id
        @return: the record id in a string
    '''

    #get the reportnumber tag list
    tag = CFG_MARC_REPORT_NUMBER
    if tag == '':
        return ''

    #variable that contains the result of the parsing of the marcxml file
    datafields = get_list_of_marcxml_datafields(marcxml)

    for datafield in datafields:

        report_number = get_subfield_value_from_datafield(datafield, tag)
        if report_number != '':
            return report_number

    return ''


def get_medias_to_submit(media_paths):
    '''
        This method get a list of recod of submission. It format a list of
        media containing name, size, type and file for each media id
        @param media_paths: list of path to the media to upload
        @return: list of media tuple
    '''

    # define the return value
    media = {}

    fp = open("/tmp/test.txt", "w")
    fp.write(media_paths[0])

    if len(media_paths) > 1:
        media_paths = format_file_to_zip_archiv(media_paths)
    else:
        media_paths = media_paths[0]

    if media_paths != '':
        media['file'] = open(media_paths, "r").read()
        media['size'] = len(media['file'])
        media['name'] = media_paths.split('/')[-1].split(';')[0]
        media['type'] = 'application/%s' % media['name'].split('.')[-1]

    return media


def get_media_from_recid(recid):
    '''
        This method get the file in the given url
        @param recid: id of the file to get
    '''

    medias = []

    bibarchiv = BibRecDocs(recid)
    bibdocs = bibarchiv.list_latest_files()

    for bibdocfile in bibdocs:

        bibfile = {'name': bibdocfile.get_full_name(),
                   'file': '',
                   'type': 'application/%s' % \
                       bibdocfile.get_superformat().split(".")[-1],
                   'path': bibdocfile.get_full_path(),
                   'collection': bibdocfile.get_type(),
                   'size': bibdocfile.get_size(),
                   'loaded': False,
                   'selected': ''}

        if bibfile['collection'] == "Main":
            bibfile['selected'] = 'checked=yes'

        medias.append(bibfile)

    return medias


def format_author_from_marcxml(marcxml):
    '''
        This method parse the marcxml file to retrieve the author of a document
        @param marcxml: the xml file to parse
        @return: tuple containing {'name', 'email' and 'affiliations'}
    '''

    #get the tag id for the given field
    main_author = CFG_MARC_AUTHOR_NAME
    main_author_affiliation = CFG_MARC_AUTHOR_AFFILIATION

    #variable that contains the result of the parsing of the marcxml file
    datafields = get_list_of_marcxml_datafields(marcxml)

    #init the author tuple
    author = {'name':'', 'email':'', 'affiliation':[]}

    for datafield in datafields:

        # retreive the main author
        if author['name'] == '':
            name = get_subfield_value_from_datafield(datafield, main_author)
            if name != '':
                author['name'] = name

        affiliation = get_subfield_value_from_datafield(datafield, main_author_affiliation)
        if affiliation != '':
            author['affiliation'].append(affiliation)

    return author


def format_marcxml_file(marcxml, is_file=False):
    '''
        Parse the given marcxml file to retreive the metadata needed by the
        forward of the document to ArXiv.org
        @param marcxml: marxml file that contains metadata from Invenio
        @return: (dictionnary) couple of key value needed for the push
    '''

    #init the return tuple
    marcxml_values = { 'id'            : '',
                       'title'         : '',
                       'summary'       : '',
                       'contributors'  : [],
                       'journal_refs'  : [],
                       'report_nos'    : [],
                       'comment'       : '',
                       'doi'           : '' }

    # check if the marcxml is not empty
    if marcxml == '':
        marcxml_values['error'] = "MARCXML string is empty !"
        return marcxml_values

    #get the tag id and code from tag table
    main_report_number = CFG_MARC_REPORT_NUMBER
    add_report_number = CFG_MARC_ADDITIONAL_REPORT_NUMBER
    main_title = CFG_MARC_TITLE
    main_summary = CFG_MARC_ABSTRACT
    main_author = CFG_MARC_AUTHOR_NAME
    main_author_affiliation = CFG_MARC_AUTHOR_AFFILIATION
    add_author = CFG_MARC_CONTRIBUTOR_NAME
    add_author_affiliation = CFG_MARC_CONTRIBUTOR_AFFILIATION
    main_comment = CFG_MARC_COMMENT
    doi = CFG_MARC_DOI
    journal_ref_code = CFG_MARC_JOURNAL_REF_CODE
    journal_ref_title = CFG_MARC_JOURNAL_REF_TITLE
    journal_ref_page = CFG_MARC_JOURNAL_REF_PAGE
    journal_ref_year = CFG_MARC_JOURNAL_REF_YEAR

    #init tmp values
    contributor = {'name' : '', 'email' : '', 'affiliation' : []}

    try:
        bfo = BibFormatObject(recID=None, xml_record=marcxml)
    except:
        marcxml_values['error'] = "Unable to open marcxml file !"
        return marcxml_values

    marcxml_values = { 'id'           : bfo.field(main_report_number),
                       'title'        : bfo.field(main_title),
                       'summary'      : bfo.field(main_summary),
                       'report_nos'   : bfo.fields(add_report_number),
                       'contributors' : [],
                       'journal_refs' : [],
                       'comment'      : bfo.field(main_comment),
                       'doi'          : bfo.field(doi)}

    authors = bfo.fields(main_author[:-1], repeatable_subfields_p=True)
    for author in authors:
        name = author.get(main_author[-1], [''])[0]
        affiliation = author.get(main_author_affiliation[-1], [])
        author = {'name': name, 'email': '', 'affiliation': affiliation}
        marcxml_values['contributors'].append(author)

    authors = bfo.fields(add_author[:-1], repeatable_subfields_p=True)
    for author in authors:
        name = author.get(add_author[-1], [''])[0]
        affiliation = author.get(add_author_affiliation[-1], [])
        author = {'name': name, 'email': '', 'affiliation': affiliation}
        marcxml_values['contributors'].append(author)

    journals = bfo.fields(journal_ref_title[:-1])
    for journal in journals:
        journal_title = journal.get(journal_ref_title[-1], '')
        journal_page = journal.get(journal_ref_page[-1], '')
        journal_code = journal.get(journal_ref_code[-1], '')
        journal_year = journal.get(journal_ref_year[-1], '')
        journal = "%s: %s (%s) pp. %s" % (journal_title, journal_code, journal_year, journal_page)
        marcxml_values['journal_refs'].append(journal)

    return marcxml_values


def get_subfield_value_from_datafield(datafield, field_tag):
    '''
        This function get the datafield note from a marcxml and get the tag
        value according to the tag id and code given
        @param datafield: xml node to be parsed
        @param field_tag: tuple containing id and code to find
        @return: value of the tag as a string
    '''

    # extract the tag number
    tag = datafield.attributes["tag"]

    tag_id = field_tag[0] + field_tag[1] + field_tag[2]
    tag_code = field_tag[5]

    # retreive the reference to the media
    if tag.value == tag_id:
        subfields = datafield.getElementsByTagName('subfield')
        for subfield in subfields:
            if subfield.attributes['code'].value == tag_code:
                return subfield.firstChild.nodeValue.encode('utf-8')

    return ''


def get_list_of_marcxml_datafields(marcxml, isfile=False):
    '''
        This method parse the marcxml file to retrieve the root of the datafields
        needed by all function that format marcxml nodes.
        @param marcxml: file or string that contains the marcxml file
        @param isfile: boolean that informs if a file or a string was given
        @return: root of all datafileds
    '''

    #variable that contains the result of the parsing of the marcxml file
    if isfile:
        try:
            parsed_marcxml = minidom.parse(marcxml)
        except IOError:
            return 0
    else:
        parsed_marcxml = minidom.parseString(marcxml)

    collections = parsed_marcxml.getElementsByTagName('collection')

    # some macxml file has no collection root but direct record entry
    if len(collections) > 0:
        collection = collections[0]
        records = collection.getElementsByTagName('record')
    else:
        records = parsed_marcxml.getElementsByTagName('record')

    record = records[0]

    return record.getElementsByTagName('datafield')


def format_file_to_zip_archiv(paths):
    '''
        This method takes a list of different type of file, zip its and group
        its into a zip archiv for sending
        @param paths: list of path to file of different types
        @return: (zip archiv) zipped file that contains all fulltext to submit
    '''

    (zip_fd, zip_path) = mkstemp(suffix='.zip', prefix='bibsword_media_',
                                 dir=CFG_TMPDIR)

    archiv = zipfile.ZipFile(zip_path, "w")

    for path in paths:
        if os.path.exists(path):
            archiv.write(path, os.path.basename(path), zipfile.ZIP_DEFLATED)

    archiv.close()

    return zip_path


#-------------------------------------------------------------------------------
# getting info from media deposit response file
#-------------------------------------------------------------------------------

def format_link_from_result(result):
    '''
        This method parses the xml file returned after the submission of a media
        and retreive the URL contained in it
        @param result: xml file returned by ArXiv
        @return: (links) table of url
    '''
    if isinstance(result, list):
        result = result[0]

    # parse the xml to access each node
    parsed_result = minidom.parseString(result)

    # finding the links in the xml file
    xml_entries = parsed_result.getElementsByTagName('entry')
    xml_entry = xml_entries[0]
    xml_contents = xml_entry.getElementsByTagName('content')

    # getting the unique content node
    content = xml_contents[0]

    # declare the dictionnary that contains type and url of a link
    link = {}
    link['link'] = content.attributes['src'].value.encode('utf-8')
    link['type'] = content.attributes['type'].value.encode('utf-8')

    return link


def format_update_time_from_result(result):
    '''
        parse any xml response to retreive and format the value of the 'updated'
        tag.
        @param result: xml result of a deposit or a submit call to a server
        @return: formated date content in the <updated> node
    '''

    # parse the xml to access each node
    parsed_result = minidom.parseString(result)

    # finding the links in the xml file
    xml_entries = parsed_result.getElementsByTagName('entry')
    xml_entry = xml_entries[0]
    xml_updated = xml_entry.getElementsByTagName('updated')

    # getting the unique content node
    updated = xml_updated[0]

    return updated.firstChild.nodeValue.encode('utf-8')


def format_links_from_submission(submission):
    '''
        parse the xml response of a metadata submission and retrieve all the
        informations proper to the link toward the media, the metadata and
        the status
        @param submission: xml response of a submission
        @return: tuple { 'medias', 'metadata', 'status' }
    '''

    # parse the xml to access each node
    parsed_result = minidom.parseString(submission)

    # finding the links in the xml file
    xml_entries = parsed_result.getElementsByTagName('entry')
    xml_entry = xml_entries[0]
    xml_links = xml_entry.getElementsByTagName('link')

    # getting all content nodes
    links = {'media':'', 'metadata':'', 'status':''}

    for link in xml_links:

        # declare the dictionnary that contains type and url of a link
        if link.attributes['rel'].value == 'edit-media':
            if links['media'] == '':
                links['media'] = link.attributes['href'].value.encode('utf-8')
            else:
                links['media'] = links['media'] + ', ' + \
                                   link.attributes['href'].value.encode('utf-8')

        if link.attributes['rel'].value == 'edit':
            links['metadata'] = link.attributes['href'].value.encode('utf-8')

        if link.attributes['rel'].value == 'alternate':
            links['status'] = link.attributes['href'].value.encode('utf-8')

    return links


def format_id_from_submission(submission):
    '''
        Parse the submission file to retrieve the arxiv id retourned
        @param submission: xml file returned after the submission
        @return: string containing the arxiv id
    '''

    # parse the xml to access each node
    parsed_result = minidom.parseString(submission)

    # finding the id in the xml file
    xml_entries = parsed_result.getElementsByTagName('entry')
    xml_entry = xml_entries[0]
    xml_id = xml_entry.getElementsByTagName('id')[0]

    remote_id = xml_id.firstChild.nodeValue.encode('utf-8')

    (begin, sep, end) = remote_id.rpartition("/")

    remote_id = 'arXiv:'
    i = 0
    for elt in end:
        remote_id += elt
        if i == 3:
            remote_id += '.'
        i = i + 1

    return remote_id


#-------------------------------------------------------------------------------
# write information in the marc file
#-------------------------------------------------------------------------------

def update_marcxml_with_remote_id(recid, remote_id, action="append"):
    '''
        Write a new entry in the given marc file. This entry is the remote record
        id given by the server where the submission has been done
        @param remote_id: the string containing the id to add to the marc file
        return: boolean true if update done, false if problems
    '''

    field_tag = CFG_MARC_ADDITIONAL_REPORT_NUMBER
    tag_id = "%s%s%s" % (field_tag[0], field_tag[1], field_tag[2])
    tag_code = field_tag[5]

    # concatenation of the string to append to the marc file
    node = '''<record>
    <controlfield tag="001">%(recid)s</controlfield>
    <datafield tag="%(tagid)s" ind1=" " ind2=" ">
        <subfield code="%(tagcode)s">%(remote_id)s</subfield>
    </datafield>
</record>''' % {
                 'recid': recid,
                 'tagid': tag_id,
                 'tagcode': tag_code,
                 'remote_id': remote_id
             }

    # creation of the tmp file containing the xml node to append
    (tmpfd, filename) = mkstemp(suffix='.xml', prefix='bibsword_append_remote_id_',
                                dir=CFG_TMPDIR)
    tmpfile = os.fdopen(tmpfd, 'w')
    tmpfile.write(node)
    tmpfile.close()

    # insert a task in bibsched to add the node in the marc file
    if action == 'append':
        result = \
            task_low_level_submission('bibupload', 'BibSword', '-a', filename)
    elif action == 'delete':
        result = \
            task_low_level_submission('bibupload', 'BibSword', '-d', filename)

    return result


def update_marcxml_with_info(recid, username, current_date, remote_id,
                             action='append'):
    '''
        This function add a field in the marc file to informat that the
        record has been submitted to a remote server
        @param recid: id of the record to update
    '''

    # concatenation of the string to append to the marc file
    node = '''<record>
    <controlfield tag="001">%(recid)s</controlfield>
    <datafield tag="%(tag)s" ind1=" " ind2=" ">
        <subfield code="a">%(submit_info)s</subfield>
    </datafield>
</record>''' % {
                 'recid': recid,
                 'tag': CFG_MARC_RECORD_SUBMIT_INFO,
                 'submit_info': CFG_SUBMIT_ARXIV_INFO_MESSAGE % (username, current_date, remote_id)
             }

    # creation of the tmp file containing the xml node to append
    (tmpfd, filename) = mkstemp(suffix='.xml', prefix='bibsword_append_submit_info_',
                                dir=CFG_TMPDIR)
    tmpfile = os.fdopen(tmpfd, 'w')
    tmpfile.write(node)
    tmpfile.close()

    # insert a task in bibschedul to add the node in the marc file
    if action == 'append':
        result = \
            task_low_level_submission('bibupload', 'BibSword', '-a', filename)
    elif action == 'delete':
        result = \
            task_low_level_submission('bibupload', 'BibSword', '-d', filename)

    return result



def upload_fulltext(recid, path):
    '''
        This method save the uploaded file to associated record
        @param recid: id of the record
        @param path: uploaded document to store
    '''

    # upload the file to the record

    bibarchiv = BibRecDocs(recid)
    docname = path.split('/')[-1].split('.')[0]
    doctype = path.split('.')[-1].split(';')[0]
    bibarchiv.add_new_file(path, CFG_DOCTYPE_UPLOAD_COLLECTION, docname,
                           format=doctype)

    return ''


#-------------------------------------------------------------------------------
# work with the remote submission status xml file
#-------------------------------------------------------------------------------

def format_submission_status(status_xml):
    '''
        This method parse the given atom xml status string and retrieve the
        the value of the tag <status>
        @param status_xml: xml atom entry
        @return: dictionnary containing status, id and/or possible error
    '''

    result = {'status':'', 'id_submission':'', 'error':''}

    parsed_status = minidom.parseString(status_xml)
    deposit = parsed_status.getElementsByTagName('deposit')[0]
    status_node = deposit.getElementsByTagName('status')[0]
    if status_node.firstChild != None:
        status = status_node.firstChild.nodeValue.encode('utf-8')
    else:
        result['status'] = ''
        return result

    #status = "submitted"
    if status == CFG_SUBMISSION_STATUS_SUBMITTED:
        result['status'] = status
        return result

    #status = "published"
    if status == CFG_SUBMISSION_STATUS_PUBLISHED:
        result['status'] = status
        arxiv_id_node = deposit.getElementsByTagName('arxiv_id')[0]
        result['id_submission'] = \
            arxiv_id_node.firstChild.nodeValue.encode('utf-8')
        return result

    #status = "onhold"
    if status == CFG_SUBMISSION_STATUS_ONHOLD:
        result['status'] = status
        return result

    #status = "removed"
    if status == 'unknown':
        result['status'] = CFG_SUBMISSION_STATUS_REMOVED
        error_node = deposit.getElementsByTagName('error')[0]
        result['error'] = error_node.firstChild.nodeValue.encode('utf-8')
        return result

    return result


#-------------------------------------------------------------------------------
# Classes for the generation of XML Atom entry containing submission metadata
#-------------------------------------------------------------------------------

class BibSwordFormat:
    '''
        This class gives the methodes needed to format all mandatories xml atom
        entry nodes. It is extended by subclasses that has optional nodes add
        to the standard SWORD format
    '''

    def __init__(self):
        ''' No init necessary for this class '''

    def frmt_id(self, recid):
        '''
            This methode check if there is an id for the resource. If it is the case,
            it format it returns a formated id node that may be inserted in the
            xml metadata file
            @param recid: the id of the resource
            @return: (xml) xml node correctly formated
        '''

        if recid != '':
            return '''<id>%s</id>\n''' % recid
        return ''


    def frmt_title(self, title):
        '''
            This methode check if there is a title for the resource. If yes,
            it returns a formated title node that may be inserted in the
            xml metadata file
            @param title: the title of the resource
            @return: (xml) xml node correctly formated
        '''

        if title != '':
            return '''<title>%s</title>\n''' % title
        return ''


    def frmt_author(self, author_name, author_email):
        '''
            This methode check if there is a submitter for the resource. If yes,
            it returns a formated author node that may containing the name and
            the email of the author to be inserted in the xml metadata file
            @param author_name: the name of the submitter of the resource
            @param author_email: the email where the remote server send answers
            @return: (xml) xml node correctly formated
        '''

        author = ''
        if author_name != '':
            author +=  '''<author>\n'''
            author += '''<name>%s</name>\n''' % author_name
            if author_email != '':
                author += '''<email>%s</email>\n''' % author_email
            author += '''</author>\n'''
        return author


    def frmt_summary(self, summary):
        '''
            This methode check if there is a summary for the resource. If yes,
            it returns a formated summary node that may be inserted in the
            xml metadata file
            @param summary: the summary of the resource
            @return: (xml) xml node correctly formated
        '''

        if summary != '':
            return '''<summary>%s</summary>\n''' % summary
        return ''


    def frmt_categories(self, categories, scheme):
        '''
            This method check if there is some categories for the resource. If it
            is the case, it returns the categorie nodes formated to be insered in
            the xml metadata file
            @param categories: list of categories for one resource
            @return: (xml) xml node(s) correctly formated
        '''

        output = ''

        for category in categories:

            output += '''<category term="%s" scheme="%s" label="%s"/>\n''' % (category['url'], scheme, category['label'])

        return output


    def frmt_link(self, links):
        '''
            This method check if there is some links for the resource. If it
            is the case, it returns the links nodes formated to be insered in
            the xml metadata file
            @param links: list of links for the resource
            @return: (xml) xml node(s) correctly formated
        '''

        output = ''

        if links != '':
            output += '''<link href="%s" ''' % links['link']
            output += '''type="%s" rel="related"/>\n''' % links['type']

        return output



class ArXivFormat(BibSwordFormat):
    '''
        This class inherit from the class BibSwordFormat. It add some specific
        mandatory nodes to the standard SWORD format.
    '''

    #---------------------------------------------------------------------------
    # Formating metadata file for submission
    #---------------------------------------------------------------------------

    def format_metadata(self, metadata):
        '''
            This method format an atom file that fits with the arxiv atom format
            used for the subission of the metadata during the push to arxiv process.
            @param metadata: tuple containing every needed information + some optional
            @return: (xml file) arxiv atom file
        '''

        #-----------------------------------------------------------------------
        # structure of the arxiv metadata submission atom entry
        #-----------------------------------------------------------------------

        output = '''<?xml version="1.0" encoding="utf-8"?>\n'''
        output += '''<entry xmlns="http://www.w3.org/2005/Atom" '''
        output += '''xmlns:arxiv="http://arxiv.org/schemas/atom">\n'''

        #id
        if 'id' in metadata:
            output += BibSwordFormat.frmt_id(self, metadata['id'])

        #title
        if 'title' in metadata:
            output += BibSwordFormat.frmt_title(self,
                                                             metadata['title'])

        #author
        if 'author_name' in metadata and 'author_email' in metadata:
            output += BibSwordFormat.frmt_author(self, metadata['author_name'],
                                                       metadata['author_email'])

        #contributors
        if 'contributors' in metadata:
            output += '' + self.frmt_contributors(metadata['contributors'])

        #summary
        if 'summary' in metadata:
            output += BibSwordFormat.frmt_summary(self, metadata['summary'])

        #categories
        if 'categories' in metadata:
            output += BibSwordFormat.frmt_categories(self, metadata['categories'],
                                                'http://arxiv.org/terms/arXiv/')

        #primary_category
        if 'primary_url' in metadata and 'primary_label' in metadata:
            output += self.frmt_primary_category(metadata['primary_url'],
                                                metadata['primary_label'],
                                                'http://arxiv.org/terms/arXiv/')

        #comment
        if 'comment' in metadata:
            output += self.frmt_comment(metadata['comment'])

        #journal references
        if 'journal_refs' in metadata:
            output += self.frmt_journal_ref(metadata['journal_refs'])

        #report numbers
        if 'report_nos' in metadata:
            output += self.frmt_report_no(metadata['report_nos'])

        #doi
        if 'doi' in metadata:
            output += self.frmt_doi(metadata['doi'])

        #link
        if 'links' in metadata:
            output += BibSwordFormat.frmt_link(self, metadata['links'])

        output += '''</entry>'''

        return output


    def frmt_contributors(self, contributors):
        '''
            This method display each contributors in the format of an editable input
            text. This allows the user to modifie it.
            @param contributors: The list of all contributors of the document
            @return: (html code) the html code that display each dropdown list
        '''

        output = ''

        for contributor in contributors:
            output += '''<contributor>\n'''
            output += '''<name>%s</name>\n''' % contributor['name']
            if contributor['email'] != '':
                output += '''<email>%s</email>\n''' % \
                    contributor['email']
            if len(contributor['affiliation']) != 0:
                for affiliation in contributor['affiliation']:
                    output += '''<arxiv:affiliation>%s'''\
                              '''</arxiv:affiliation>\n''' % affiliation
            output += '''</contributor>\n'''

        return output


    def frmt_primary_category(self, primary_url, primary_label, scheme):
        '''
            This method format the primary category as an element of a dropdown
            list.
            @param primary_url: url of the primary category deposit
            @param primary_label: name of the primary category to display
            @param scheme: url of the primary category schema
            @return: html code containing each element to display
        '''

        output = ''

        if primary_url != '':
            output += '''<arxiv:primary_category xmlns:arxiv="http://arxiv.org/schemas/atom/" scheme="%s" label="%s" term="%s"/>\n''' % (scheme, primary_label, primary_url)

        return output


    def frmt_comment(self, comment):
        '''
            This methode check if there is an comment given. If it is the case, it
            format it returns a formated comment node that may be inserted in the xml
            metadata file
            @param comment: the string comment
            @return: (xml) xml node correctly formated
        '''

        output = ''

        if comment != '':
            output = '''<arxiv:comment>%s</arxiv:comment>\n''' % comment

        return output


    def frmt_journal_ref(self, journal_refs):
        '''
            This method check if there is some journal refs for the resource. If it
            is the case, it returns the journal_ref nodes formated to be insered in
            the xml metadata file
            @param journal_refs: list of journal_refs for one resource
            @return: (xml) xml node(s) correctly formated
        '''

        output = ''

        for journal_ref in journal_refs:
            output += '''<arxiv:journal_ref>%s</arxiv:journal_ref>\n''' % \
                journal_ref

        return output


    def frmt_report_no(self, report_nos):
        '''
            This method check if there is some report numbres for the resource. If it
            is the case, it returns the report_nos nodes formated to be insered in
            the xml metadata file
            @param report_nos: list of report_nos for one resource
            @return: (xml) xml node(s) correctly formated
        '''

        output = ''

        for report_no in report_nos:
            output += '''<arxiv:report_no>%s</arxiv:report_no>\n''' % \
                report_no

        return output


    def frmt_doi(self, doi):
        '''This methode check if there is an doi given. If it is the case, it
            format it returns a formated doi node that may be inserted in the xml
            metadata file
            @param doi: the string doi
            @return: (xml) xml node correctly formated
        '''

        output = ''

        if doi != '':
            output = '''<arxiv:doi>%s</arxiv:doi>\n''' % doi

        return output
