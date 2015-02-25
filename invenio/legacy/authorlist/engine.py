# This file is part of Invenio.
# Copyright (C) 2011, 2012, 2013, 2014 CERN.
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

""" Invenio Authorlist Data Conversion Engine. """
import time
try:
    import json
except ImportError:
    import simplejson as json
from xml.dom import minidom

try:
    from xml.etree import ElementTree as ET
except ImportError:
    import elementtree.ElementTree as ET

from invenio.legacy.webuser import page_not_authorized
from invenio.modules.access.engine import acc_authorize_action
from invenio.legacy.authorlist import config as cfg
from invenio.legacy.search_engine import perform_request_search, record_exists
from invenio.legacy.bibrecord import get_fieldvalues
from invenio.legacy.bibedit.utils import get_record
# from lxml import etree
from invenio.legacy.authorlist.dblayer import get_owner
from invenio.utils.text import escape_latex

# default name that will be used, when affiliation name is missing
UNKNOWN_AFFILIATION = 'Unknown Affiliation'
# Namespaces used in the xml file
NAMESPACES = {'cal': 'http://www.slac.stanford.edu/spires/hepnames/authors_xml/',
              'foaf': 'http://xmlns.com/foaf/0.1/',
              }


def retrieve_data_from_record(recid):
    """
    Extract data from a record id in order to import it to the Author list
    interface
    """
    if not record_exists(recid):
        return

    output = {}

    DEFAULT_AFFILIATION_TYPE = cfg.OPTIONS.AUTHOR_AFFILIATION_TYPE[0]
    DEFAULT_IDENTIFIER = cfg.OPTIONS.IDENTIFIERS_LIST[0]
    IDENTIFIERS_MAPPING = cfg.OPTIONS.IDENTIFIERS_MAPPING

    bibrecord = get_record(recid)

    try:
        paper_title = get_fieldvalues(recid, '245__a')[0]
    except IndexError:
        paper_title = ""
    try:
        collaboration_name = get_fieldvalues(recid, '710__g')
    except IndexError:
        collaboration_name = ""
    try:
        experiment_number = get_fieldvalues(recid, '693__e')
    except IndexError:
        experiment_number = ""

    record_authors = bibrecord.get('100', [])
    record_authors.extend(bibrecord.get('700', []))

    author_list = []
    unique_affiliations = []

    for i, field_instance in enumerate(record_authors, 1):
        family_name = ""
        given_name = ""
        name_on_paper = ""
        status = ""
        affiliations = []
        identifiers = []
        field = field_instance[0]
        for subfield_code, subfield_value in field:
            if subfield_code == "a":
                try:
                    family_name = subfield_value.split(',')[0]
                    given_name = subfield_value.split(',')[1].lstrip()
                except:
                    pass
                name_on_paper = subfield_value
            elif subfield_code == "u":
                affiliations.append([subfield_value, DEFAULT_AFFILIATION_TYPE])
                unique_affiliations.append(subfield_value)
            elif subfield_code == "i":
                # FIXME This will currently work only with INSPIRE IDs
                id_prefix = subfield_value.split("-")[0]
                if id_prefix in IDENTIFIERS_MAPPING:
                    identifiers.append([subfield_value, IDENTIFIERS_MAPPING[id_prefix]])
        if not identifiers:
            identifiers.append(['', DEFAULT_IDENTIFIER])
        if not affiliations:
            affiliations.append([UNKNOWN_AFFILIATION, DEFAULT_AFFILIATION_TYPE])
            unique_affiliations.append(UNKNOWN_AFFILIATION)
        author_list.append([
            i,              # Row number
            '',             # Place holder for the web interface
            family_name,
            given_name,
            name_on_paper,
            status,
            affiliations,
            identifiers
        ])

    unique_affiliations = list(set(unique_affiliations))

    output.update({'authors': author_list})

    # Generate all the affiliation related information
    affiliation_list = []
    for i, affiliation in enumerate(unique_affiliations, 1):
        institution = perform_request_search(c="Institutions", p='110__u:"' + affiliation + '"')
        full_name = affiliation
        if len(institution) == 1:
            full_name_110_a = get_fieldvalues(institution[0], '110__a')
            if full_name_110_a:
                full_name = str(full_name_110_a[0])
            full_name_110_b = get_fieldvalues(institution[0], '110__b')
            if full_name_110_b:
                full_name += ', ' + str(full_name_110_b[0])
        affiliation = [i,
                       '',
                       affiliation,
                       '',
                       full_name,
                       '',
                       True,
                       '']
        affiliation_list.append(affiliation)

    output.update({'affiliations': affiliation_list})
    output.update({'paper_title': paper_title,
                   'collaboration': collaboration_name,
                   'experiment_number': experiment_number,
                   'last_modified': int(time.time()),
                   'reference_ids': [],
                   'paper_id': '1'})

    return output


def retrieve_data_from_xml(xml):
    """
    Extract data from an XML file to import it to the Author list
    interface
    """

    def get_element_value_helper(element, tag):
        """
        Helper that takes an element and returns text from the first node
        of that element
        """
        text = ''
        elements_list = element.getElementsByTagName(tag)
        if elements_list:
            child = elements_list[0].firstChild
            if child:
                text = child.nodeValue

        return text

    output = {}
    # Save the affiliatons variable, the default value for "Affiliation" column
    # will be always first value from type_of_affiliation table
    type_of_affiliation = cfg.OPTIONS.AUTHOR_AFFILIATION_TYPE
    # Save the default identifier - first element from the list of identifiers
    default_identifier = cfg.OPTIONS.IDENTIFIERS_LIST[0]
    # Save identifiers mapping
    identifiers_mapping = cfg.OPTIONS.IDENTIFIERS_MAPPING

    parsed_xml = minidom.parseString(xml)

    # Extract collaboration name and experiment number
    collaboration_name = ''
    experiment_number = ''
    collaborations = parsed_xml.getElementsByTagName('cal:collaborations')
    if len(collaborations) == 1:
        collaboration_name = get_element_value_helper(collaborations[0], 'foaf:name')
        experiment_number = get_element_value_helper(collaborations[0], 'cal:experimentNumber')

    # Extract affiliations
    affiliation_list = []
    affiliation_id_name = {}

    affiliations = parsed_xml.getElementsByTagName('foaf:Organization')
    for i, affiliation in enumerate(affiliations):
        affiliation_id = affiliation.getAttribute('id') or ''
        affiliation_name = get_element_value_helper(affiliation, 'foaf:name')
        affiliation_acronym = get_element_value_helper(affiliation, 'cal:orgName')
        if not affiliation_acronym:
            # No acronym ? Use the name instead
            affiliation_acronym = affiliation_name
        affiliation_address = get_element_value_helper(affiliation, 'cal:orgAddress')
        if not affiliation_address:
            affiliation_address = affiliation_name
        affiliation_domain = get_element_value_helper(affiliation, 'cal:orgDomain')
        # saving {id:name}, it will be needed for authors affiliations
        if affiliation_id:
            # According to
            # http://stackoverflow.com/questions/8214932/how-to-check-if-a-value-exists-in-a-dictionary-python
            # itervalues is faster than values() and viewvalues()
            if affiliation_acronym in affiliation_id_name.itervalues():
                # in case we have a duplicate of acronym, make it unique by
                # appending the iteration number
                affiliation_acronym += str(i+1)
            affiliation_id_name[affiliation_id] = affiliation_acronym

        affiliation_info = [long(i+1),
                            '',
                            affiliation_acronym,
                            '',
                            affiliation_address,
                            affiliation_domain,
                            True,
                            '']
        affiliation_list.append(affiliation_info)

    # Extract authors
    author_list = []
    authors = parsed_xml.getElementsByTagName('foaf:Person')
    for i, author in enumerate(authors):
        first_name = get_element_value_helper(author, 'foaf:givenName')
        # In case there was no given name under previous field, we search for initials in cal:authorNamePaperGiven
        if not first_name:
            first_name = get_element_value_helper(author, 'cal:authorNamePaperGiven')
        last_name = get_element_value_helper(author, 'foaf:familyName')
        full_name = get_element_value_helper(author, 'cal:authorNamePaper')
        status = get_element_value_helper(author, 'cal:authorStatus')

        # Extract author affiliations
        author_affiliations = []
        if author.getElementsByTagName('cal:authorAffiliations'):
            for afil in author.getElementsByTagName('cal:authorAffiliations')[0].getElementsByTagName('cal:authorAffiliation'):
                a_id = afil.getAttribute('organizationid')
                if afil.getAttribute('connection') in type_of_affiliation:
                    affiliation_type = afil.getAttribute('connection')
                else:
                    affiliation_type = type_of_affiliation[0]
                author_affiliations.append([affiliation_id_name.get(a_id, UNKNOWN_AFFILIATION), affiliation_type])
        else:
            author_affiliations = [UNKNOWN_AFFILIATION, type_of_affiliation[0]]

        identifiers = []
        if author.getElementsByTagName('cal:authorids'):
            for author_id in author.getElementsByTagName('cal:authorids')[0].getElementsByTagName('cal:authorid'):
                if author_id.getAttribute('source') in identifiers_mapping and author_id.firstChild:
                    identifiers.append([
                        author_id.firstChild.nodeValue,
                        identifiers_mapping[author_id.getAttribute('source')]])
        if not identifiers:
            identifiers.append(['', default_identifier])
        author_info = [long(i+1),
                       '',
                       last_name,
                       first_name,
                       full_name,
                       status,
                       author_affiliations,
                       identifiers]
        author_list.append(author_info)

    output.update({'authors': author_list})
    output.update({'affiliations': affiliation_list})
    # Add generic information about the paper
    output.update({'collaboration': collaboration_name,
                   'experiment_number': experiment_number,
                   'last_modified': int(time.time()),
                   'reference_ids': [],
                   'paper_id': '1',
                   'paper_title': ''})

    return output


def user_authorization(req, ln):
    """ Check user authorization to visit page """
    auth_code, auth_message = acc_authorize_action(req, 'runauthorlist')
    if auth_code != 0:
        referer = '/authorlist/'
        return page_not_authorized(req=req, referer=referer,
                                   text=auth_message, navmenuid="authorlist")
    else:
        return None


def check_user_rights(user_id, paper_id):
    """Check if user can modify this paper"""
    # if the paper_id is empty - user is trying to create new record
    # we allow him, because everyone can do that
    if not paper_id or (user_id == get_owner(paper_id)):
        return True
    return False


class Converter(object):
    CONTENT_TYPE = 'text/plain'
    FILE_NAME = 'converted.txt'

    def __init__(self):
        raise NotImplementedError

    def dump(self, data):
        raise NotImplementedError

    def dumps(self, data):
        raise NotImplementedError


class NA62Latex(Converter):
    FILE_NAME = 'la.tex'

    def __init__(self):
        pass

    def dump(self, data):
        pass

    def dumps(self, data):
        pass


class ElsevierArticle(Converter):
    CONTENT_TYPE = 'text/plain'
    FILE_NAME = 'elsarticle.tex'
    cal = '{http://www.slac.stanford.edu/spires/hepnames/authors_xml/}'
    foaf = '{http://xmlns.com/foaf/0.1/}'

    def __init__(self):
        pass

    def dictionary_to_list(self, node):
        res = {}
        res[node.tag] = []
        self.xmltodict(node, res[node.tag])
        reply = {}
        reply[node.tag] = {'value': res[node.tag], 'attribs': node.attrib, 'tail': node.tail}
        return reply

    def xmltodict(self, node, res):
        rep = {}
        if len(node):
            for n in list(node):
                rep[node.tag] = []
                value = self.xmltodict(n, rep[node.tag])
                if len(n):
                    value = {'value': rep[node.tag], 'attributes': n.attrib, 'tail': n.tail}
                    res.append({n.tag: value})
                else:
                    res.append(rep[node.tag][0])
        else:
            value = {}
            value = {'value': node.text, 'attributes': node.attrib, 'tail': node.tail}
            res.append({node.tag: value})
        return

    def get_organizations(self, organizations):
        organization_dict = dict()
        for orgs_element in organizations:
            key = orgs_element.keys()[0]
            if key == self.foaf + 'Organization':
                for name_element in orgs_element[key]['value']:
                    value_key = name_element.keys()[0]
                    if value_key == self.cal + 'orgAddress':
                        if name_element[value_key]['value']:
                            organization_dict[orgs_element[key]['attributes']['id']] = name_element[value_key]['value'].encode('utf-8')
                        else:
                            organization_dict[orgs_element[key]['attributes']['id']] = ''
                        break
        return organization_dict

    def get_authors(self, authors):
        author_list = []
        for auth_element in authors:
            key = auth_element.keys()[0]
            if key == self.foaf + 'Person':
                affiliation_list = []
            given_name = ''
            family_name = ''
            for name_element in auth_element[key]['value']:
                value_key = name_element.keys()[0]
                if value_key == self.foaf + 'familyName' and name_element[value_key]['value']:
                    family_name = name_element[value_key]['value'].encode('utf-8')
                elif value_key == self.foaf + 'givenName' and name_element[value_key]['value']:
                    given_name = name_element[value_key]['value'].encode('utf-8')
                elif value_key == self.cal + 'authorAffiliations':
                    for aff_element in name_element[value_key]['value']:
                        aff_key = aff_element.keys()[0]
                        if aff_key == self.cal + 'authorAffiliation':
                            if aff_element[aff_key]['attributes']['connection'] == 'Affiliated with':
                                affiliation_list.append(aff_element[aff_key]['attributes']['organizationid'])
            author_list.append([(given_name, family_name), tuple(affiliation_list)])
        return author_list

    def dump(self, data):

        AuthorsXMLConverter = Converters.get('authorsxml')
        AuthorsXML = dumps(data, AuthorsXMLConverter)

        root = ET.fromstring(AuthorsXML)
        tree = ET.ElementTree(root)

        res = self.dictionary_to_list(tree.getroot())

        collaboration_author_list_values = res['collaborationauthorlist']['value']
        organization_dict = dict()
        author_list = []

        for element in collaboration_author_list_values:
            key = element.keys()[0]
            # if the value of the key is empty, start next loop cycle
            if element[key]['value'] is None:
                continue
            if key == self.cal + 'organizations':
                organization_dict = self.get_organizations(element[key]['value'])
            elif key == self.cal + 'authors':
                author_list = self.get_authors(element[key]['value'])

        clusters = []
        organization_codes = []

        for element in author_list:
            if len(element[1]) >= 1:
                organization_code = element[1][0]
                other_affiliations = element[1][1:]
                author = [element[0]]
                if other_affiliations:
                    author.extend(other_affiliations)
                # if this organization already exists in the cluster
                if organization_code in organization_codes:
                    for cluster in clusters:
                        if cluster[0] == organization_code:
                            cluster.append(author)
                            break
                else:
                    organization_codes.append(organization_code)
                    clusters.append([organization_code, author])

        myout = ""

        myout += "\\documentclass[a4paper,12pt]{article}\r\n"
        myout += "\\usepackage[utf8]{inputenc}\r\n"
        myout += "\\begin{document}\r\n"
        myout += "\\begin{center}\r\n"
        myout += "{\\Large Collaboration}\\\\\r\n"
        myout += "\\vspace{2mm}\r\n%\r\n"
        primary_output_string = ""
        secondary_affiliation_count = 1
        secondary_affiliations = ""
        secondary_affiliations_pos = {}
        for data in clusters:
            primary_output = []
            organization_code = data[0]
            for author in data[1:]:
                name = " " + str(escape_latex(author[0][0])) + '~' + str(escape_latex(author[0][1]))
                if len(author) > 1:
                    for sec_affiliation in author[1:]:
                        if sec_affiliation in organization_dict.keys():
                            if organization_dict[sec_affiliation] in secondary_affiliations_pos.keys():
                                name += "$\\,$\\footnotemark[" + str(secondary_affiliations_pos[organization_dict[sec_affiliation]]) + "]"
                            else:
                                name += "$\\,$\\footnotemark[" + str(secondary_affiliation_count) + "]"
                                secondary_affiliations += "%\r\n\\footnotetext[" + str(secondary_affiliation_count) + "]{" + str(escape_latex(organization_dict[sec_affiliation])) + "}\r\n"
                                secondary_affiliations_pos[organization_dict[sec_affiliation]] = secondary_affiliation_count
                                secondary_affiliation_count += 1
                primary_output.append(name)
            if organization_dict.get(data[0]):
                organization = organization_dict.get(data[0])
            else:
                organization = UNKNOWN_AFFILIATION
            primary_output_string += ',\r\n'.join(primary_output) + " \\\\\r\n{\\em \\small " + str(escape_latex(organization)) + "} \\\\[0.2cm]\r\n%\r\n"

        myout += primary_output_string
        myout += "\\end{center}\r\n"
        myout += "\\setcounter{footnote}{0}\r\n"
        myout += secondary_affiliations
        myout += "\\end{document}\r\n"

        return myout

    def dumps(self, data):
        return self.dump(data)


class APSpaper(Converter):
    CONTENT_TYPE = 'text/plain'
    FILE_NAME = 'APSpaper.tex'

    def __init__(self):
        pass

    def dump(self, data):
        AuthorsXMLConverter = Converters.get('authorsxml')
        AuthorsXML = dumps(data, AuthorsXMLConverter)

        organizations_list = []
        authors_list = []

        root = ET.fromstring(AuthorsXML)
        # save affiliations
        for organization in root.findall('{%s}organizations/{%s}Organization' % (NAMESPACES['cal'], NAMESPACES['foaf'])):
            org_id = organization.attrib['id']
            org_name = ''
            if organization.find('{%s}name' % NAMESPACES['foaf']) is not None:
                org_name = organization.find('{%s}name' % NAMESPACES['foaf']).text or ''

            organizations_list.append([org_id, org_name.encode('utf-8')])

        # save authors
        for author in root.findall('{%s}authors/{%s}Person' % (NAMESPACES['cal'], NAMESPACES['foaf'])):
            author_name = ''
            author_affiliations = []
            if author.find('{%s}authorNamePaper' % NAMESPACES['cal']) is not None:
                author_name = author.find('{%s}authorNamePaper' % NAMESPACES['cal']).text or ''
            for affil in author.findall('{%(cal)s}authorAffiliations/{%(cal)s}authorAffiliation' % {'cal': NAMESPACES['cal']}):
                author_affiliations.append(affil.attrib['organizationid'])

            authors_list.append([author_name.encode('utf-8'), author_affiliations])

        myout = ''
        for author in authors_list:
            myout += '\\author{' + str(escape_latex(author[0])) + '$^{' + ','.join(author[1]) + '}$}\r\n'
        for org in organizations_list:
            myout += '\\affiliation{$^{' + str(org[0]) + '}$ ' + str(escape_latex(org[1])) + '}\r\n'

        return myout

    def dumps(self, data):
        return self.dump(data)


class AuthorsXML(Converter):
    CONTENT_TYPE = 'text/xml'
    FILE_NAME = 'authors.xml'

    def __init__(self):
        pass

    def create_affiliation(self, document, parsed, organization_ids):
        affiliation = document.createElement('cal:authorAffiliation')

        affiliation_acronym = parsed[cfg.JSON.AFFILIATION_ACRONYM]
        affiliation_status = parsed[cfg.JSON.AFFILIATION_STATUS]

        if affiliation_acronym not in organization_ids:
            affiliation.setAttribute('organizationid',
                                     'Error - there is no organization called ' +
                                     affiliation_acronym)
        else:
            affiliation.setAttribute('organizationid',
                                     organization_ids[affiliation_acronym])
        affiliation.setAttribute('connection', affiliation_status)

        return affiliation

    def create_identifier(self, document, parsed):
        identifier = document.createElement('cal:authorid')

        identifier_number = parsed[cfg.JSON.IDENTIFIER_NUMBER]
        identifier_name = parsed[cfg.JSON.IDENTIFIER_NAME]

        identifier.setAttribute('source', identifier_name)
        identifier_text = document.createTextNode(identifier_number)
        identifier.appendChild(identifier_text)

        return identifier

    def create_authors(self, document, root, parsed, organization_ids):
        parsed_authors = parsed[cfg.JSON.AUTHORS_KEY]

        authors = document.createElement('cal:authors')
        root.appendChild(authors)

        for parsed_author in parsed_authors:
            author = self.create_author(document, parsed_author, organization_ids)
            authors.appendChild(author)

    def create_author(self, document, parsed, organization_ids):
        author = document.createElement('foaf:Person')

        # paper name
        paper_name = document.createElement('cal:authorNamePaper')
        paper_name_info = parsed[cfg.JSON.PAPER_NAME]
        paper_name_text = document.createTextNode(paper_name_info)
        paper_name.appendChild(paper_name_text)
        author.appendChild(paper_name)

        # given name
        given_name_info = parsed[cfg.JSON.GIVEN_NAME]
        if (cfg.EMPTY.match(given_name_info) is None):
            given_name = document.createElement('foaf:givenName')
            given_name_text = document.createTextNode(given_name_info)
            given_name.appendChild(given_name_text)
            author.appendChild(given_name)

        # family name
        family_name_info = parsed[cfg.JSON.FAMILY_NAME]
        if (cfg.EMPTY.match(family_name_info) is None):
            family_name = document.createElement('foaf:familyName')
            family_name_text = document.createTextNode(family_name_info)
            family_name.appendChild(family_name_text)
            author.appendChild(family_name)

        # status
        author_status_info = parsed[cfg.JSON.STATUS]
        if (author_status_info):
            author_status = document.createElement('cal:authorStatus')
            author_status_text = document.createTextNode(author_status_info)
            author_status.appendChild(author_status_text)
            author.appendChild(author_status)

        # collaboration
        collaboration = document.createElement('cal:authorCollaboration')
        collaboration.setAttribute('collaborationid', cfg.AuthorsXML.COLLABORATION_ID)
        author.appendChild(collaboration)

        # affiliations
        affiliations = document.createElement('cal:authorAffiliations')
        author.appendChild(affiliations)
        for parsed_affiliation in parsed[cfg.JSON.AFFILIATIONS]:
            affiliation = self.create_affiliation(document, parsed_affiliation, organization_ids)
            affiliations.appendChild(affiliation)

        # identifiers
        identifiers = document.createElement('cal:authorids')
        author.appendChild(identifiers)
        for parsed_identifier in parsed[cfg.JSON.IDENTIFIERS]:
            identifier = self.create_identifier(document, parsed_identifier)
            identifiers.appendChild(identifier)

        return author

    def create_collaboration(self, document, root, parsed):
        # collaborations
        collaborations = document.createElement('cal:collaborations')
        collaboration = document.createElement('cal:collaboration')
        collaboration.setAttribute('id', cfg.AuthorsXML.COLLABORATION_ID)
        collaborations.appendChild(collaboration)

        # name
        name = document.createElement('foaf:name')
        name_info = parsed[cfg.JSON.COLLABORATION]
        name_text = document.createTextNode(name_info)
        name.appendChild(name_text)
        collaboration.appendChild(name)

        # experiment number
        experiment_number_info = parsed[cfg.JSON.EXPERIMENT_NUMBER]
        if (cfg.EMPTY.match(experiment_number_info) is None):
            experiment_number = document.createElement('cal:experimentNumber')
            experiment_number_text = document.createTextNode(experiment_number_info)
            experiment_number.appendChild(experiment_number_text)
            collaboration.appendChild(experiment_number)
        root.appendChild(collaborations)

    def create_document(self):
        dom = minidom.getDOMImplementation()
        document = dom.createDocument(None, 'collaborationauthorlist', None)
        root = document.documentElement

        root.setAttribute('xmlns:foaf', 'http://xmlns.com/foaf/0.1/')
        root.setAttribute('xmlns:cal', 'http://www.slac.stanford.edu/spires/hepnames/authors_xml/')

        return document, root

    def create_header(self, document, root, parsed):
        # creation date
        creation_date = document.createElement('cal:creationDate')
        creation_date_info = time.strftime(cfg.AuthorsXML.TIME_FORMAT)
        creation_date_text = document.createTextNode(creation_date_info)
        creation_date.appendChild(creation_date_text)
        root.appendChild(creation_date)

        # publication reference
        for reference_info in parsed[cfg.JSON.REFERENCE_IDS]:
            reference = document.createElement('cal:publicationReference')
            reference_text = document.createTextNode(reference_info)
            reference.appendChild(reference_text)
            root.appendChild(reference)

    def create_organizations(self, document, root, parsed, ids):
        parsed_organizations = parsed[cfg.JSON.AFFILIATIONS_KEY]

        # organizations container
        organizations = document.createElement('cal:organizations')
        root.appendChild(organizations)

        # create individual organizations and append them
        for parsed_organization in parsed_organizations:
            organization = self.create_organization(document, parsed_organization, ids)
            organizations.appendChild(organization)

    def create_organization(self, document, parsed, ids):
        acronym = parsed[cfg.JSON.ACRONYM]
        organization = document.createElement('foaf:Organization')
        organization.setAttribute('id', ids[acronym])

        # create the domain node if field is set
        domain_info = parsed[cfg.JSON.DOMAIN]
        if (cfg.EMPTY.match(domain_info) is None):
            domain = document.createElement('cal:orgDomain')
            domain_text = document.createTextNode(domain_info)
            domain.appendChild(domain_text)
            organization.appendChild(domain)

        # organization name, no presence check, already done on the client side
        name = document.createElement('foaf:name')
        name_info = parsed[cfg.JSON.NAME]
        name_text = document.createTextNode(name_info)
        name.appendChild(name_text)
        organization.appendChild(name)

        # organization acronym
        org_acronym = document.createElement('cal:orgName')
        org_acronym_text = document.createTextNode(acronym)
        org_acronym.appendChild(org_acronym_text)
        organization.appendChild(org_acronym)

        # organization identifier
        org_name_info = parsed[cfg.JSON.SPIRES_ID]
        if (cfg.EMPTY.match(org_name_info) is None):
            org_name = document.createElement('cal:orgName')
            org_name.setAttribute('source', cfg.AuthorsXML.SPIRES)
            org_name_text = document.createTextNode(org_name_info)
            org_name.appendChild(org_name_text)
            organization.appendChild(org_name)
        else:
            org_name_info = parsed[cfg.JSON.NAME]
            org_address = document.createElement('cal:orgAddress')
            org_address_text = document.createTextNode(org_name_info)
            org_address.appendChild(org_address_text)
            organization.appendChild(org_address)

        # membership
        org_status_info = parsed[cfg.JSON.MEMBER]
        if (not org_status_info):
            org_status_info = cfg.AuthorsXML.NONMEMBER
        else:
            org_status_info = cfg.AuthorsXML.MEMBER
        org_status = document.createElement('cal:orgStatus')
        org_status_text = document.createTextNode(org_status_info)
        org_status.appendChild(org_status_text)
        organization.appendChild(org_status)

        # umbrella organization/group
        group_info = parsed[cfg.JSON.UMBRELLA]
        if (cfg.EMPTY.match(group_info) is None):
            if group_info in ids.keys():
                group = document.createElement('cal:group')
                group.setAttribute('with', ids[group_info])
                organization.appendChild(group)

        return organization

    def dump(self, data):
        parsed = json.loads(data)
        document, root = self.create_document()
        affiliations = parsed[cfg.JSON.AFFILIATIONS_KEY]

        organization_ids = self.generate_organization_ids(affiliations)

        self.create_header(document, root, parsed)
        self.create_collaboration(document, root, parsed)
        self.create_organizations(document, root, parsed, organization_ids)
        self.create_authors(document, root, parsed, organization_ids)

        return document

    def dumps(self, data):
        # FIX for toprettyxml function from website:
        # http://ronrothman.com/public/leftbraned/xml-dom-minidom-toprettyxml-and-silly-whitespace/
        def fixed_writexml(self, writer, indent="", addindent="", newl=""):
            # indent = current indentation
            # addindent = indentation to add to higher levels
            # newl = newline string
            writer.write(indent+"<" + self.tagName)

            attrs = self._get_attributes()
            a_names = attrs.keys()
            a_names.sort()

            for a_name in a_names:
                writer.write(" %s=\"" % a_name)
                minidom._write_data(writer, attrs[a_name].value)
                writer.write("\"")
            if self.childNodes:
                if len(self.childNodes) == 1 and self.childNodes[0].nodeType == minidom.Node.TEXT_NODE:
                    writer.write(">")
                    self.childNodes[0].writexml(writer, "", "", "")
                    writer.write("</%s>%s" % (self.tagName, newl))
                    return
                writer.write(">%s" % (newl))
                for node in self.childNodes:
                    node.writexml(writer, indent + addindent, addindent, newl)
                writer.write("%s</%s>%s" % (indent, self.tagName, newl))
            else:
                writer.write("/>%s" % (newl))
        # replace minidom's function with ours
        minidom.Element.writexml = fixed_writexml
        # End of FIX
        return self.dump(data).toprettyxml(indent='    ', newl='\r\n', encoding='utf-8')

    def generate_organization_ids(self, organizations):
        ids = {}
        # Map each organization acronym to an id of the kind 'o[index]'
        for index, organization in enumerate(organizations):
            acronym = organization[cfg.JSON.ACRONYM]
            ids[acronym] = cfg.AuthorsXML.ORGANIZATION_ID + str(index)

        return ids


class Converters:
    __converters__ = {'authorsxml': AuthorsXML, 'elsevier': ElsevierArticle, 'aps': APSpaper}

    @classmethod
    def get(cls, format):
        return cls.__converters__.get(format)


def dump(data, converter):
    return converter().dump(data)


def dumps(data, converter):
    return converter().dumps(data)
