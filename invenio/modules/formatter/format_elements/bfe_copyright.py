# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2012, 2013, 2014 CERN.
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

from __future__ import print_function

"""BibFormat element - Prints copyright information"""

__revision__ = "$Id$"

import sys

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622

from six import iteritems

from invenio.utils.url import create_html_link

CFG_CERN_LICENSE_URL = 'http://copyright.cern.ch/'

def format_element(bfo, copyrights_separator=", ", licenses_separator=", ", instances_separator=", ",
                   link_to_licenses='yes', auto_link_to_CERN_license='no', remove_link_to_CERN_license='yes',
                   show_licenses='yes', show_material="yes",
                   show_sponsor="yes", license_to_url_kb='LICENSE2URL'):
    """
    Print copyright information

    Run this element to start the unit tests embedded within this element

    @param copyrights_separator: a separator between the copyrights of a bibdoc
    @param licenses_separator: a separator between the licenses of a bibdoc
    @param instances_separator: a separator between the licenses/copyrights of each BibDoc
    @param link_to_licenses: if 'yes', print the links to the licenses (otherwise just the name)
    @param auto_link_to_CERN_license: if 'yes', automatically add a link to CERN license when applicable (even if not in metadata)
    @param remove_link_to_CERN_license: if 'yes', remove link to CERN license when existing in the metadata. This option is ignored when auto_link_to_CERN_license is set to 'yes'
    @param show_licenses: if 'no', completely ignore license information
    @param show_material: if 'yes', material to which license/copyright applies ($3 subfield) is displayed
    @param license_to_url_kb: knowledge base used to map a license (as found in 540__a) to a URL
    """
    if auto_link_to_CERN_license.lower() == 'yes':
        # These option are mutually exclusive
        remove_link_to_CERN_license = 'no'
    add_CERN_license_link_to_bibdocs = []

    copyrights_info = bfo.fields('542__', escape=1)
    licenses_info = bfo.fields('540__', escape=1)

    copyrights_and_licenses_list = {}
    if copyrights_info or licenses_info:
        out = set()

        for copyright_info in copyrights_info:

            # Check to which bibdoc ID this copyright applies
            bibdoc_id = 0
            material = None
            if '8' in copyright_info:
                try:
                    bibdoc_id = int(copyright_info['8'])
                except:
                    pass
            elif '3' in copyright_info:
                # in that case, map using subfield $3
                material = copyright_info['3']

            # Retrieve what to display to user
            label = ''
            if 'f' in copyright_info:
                # Copyright message. Use this as label
                label = copyright_info['f']
            elif 'd' in copyright_info:
                # Copyright holder
                year = ''
                if 'g' in copyright_info:
                    # Year was given. Use it too
                    year = "%s " % copyright_info['g']
                label = "&copy; " + year + copyright_info['d']
                if copyright_info['d'] == 'CERN' and \
                   len(licenses_info) == 0 and \
                   auto_link_to_CERN_license.lower() == 'yes':
                    # There is not license, it is a CERN copyright and
                    # we would like to add a link to the "license
                    # page"
                    add_CERN_license_link_to_bibdocs.append(bibdoc_id)

            elif 'e' in copyright_info:
                # There is no copyright information available here?
                # Display contact person
                label = "Copyright info: " +  copyright_info['e']
            else:
                continue

            # Append our copyright to the list, for given BibDoc
            if bibdoc_id not in copyrights_and_licenses_list and not (material and bibdoc_id == 0):
                copyrights_and_licenses_list[bibdoc_id] = {'copyright':[], 'license': []}
            elif material and material not in copyrights_and_licenses_list:
                copyrights_and_licenses_list[material] = {'copyright':[], 'license': []}
            if not (material and bibdoc_id == 0):
                copyrights_and_licenses_list[bibdoc_id]['copyright'].append((label, copyright_info.get('d', '')))
            elif material in copyrights_and_licenses_list:
                copyrights_and_licenses_list[material]['copyright'].append((label, copyright_info.get('d', '')))

        # Now get the licenses. Try to map to a copyright
        for license_info in licenses_info:

            # Check to which bibdoc ID this license applies
            bibdoc_id = 0
            material = None
            sponsor_info = license_info.get('f', '')
            if license_info.has_key('8'):
                try:
                    bibdoc_id = int(license_info['8'])
                except:
                    pass
            elif '3' in license_info:
                # in that case, map using subfield $3
                material = license_info['3']
            label = ''
            url = ''
            license_body = ''
            if 'a' in license_info:
                # Terms governing use
                label = license_info['a']
            if 'b' in license_info:
                # Body imposing the license
                license_body = license_info['b']
            if not url and \
                   ((label in ('&copy; CERN', 'CERN')) or ('CERN' in license_body)) and \
                   auto_link_to_CERN_license.lower() == 'yes':
                url = CFG_CERN_LICENSE_URL
            if not url and license_to_url_kb:
                # Look for URL in knowledge base
                url = bfo.kb(license_to_url_kb, label)
            if 'u' in license_info:
                # License URL
                url = license_info['u']

            # Append our license to the list, for given BibDoc
            if bibdoc_id not in copyrights_and_licenses_list and not (material and bibdoc_id == 0):
                copyrights_and_licenses_list[bibdoc_id] = {'copyright':[], 'license': []}
            elif material and material not in copyrights_and_licenses_list:
                copyrights_and_licenses_list[material] = {'copyright':[], 'license': []}
            if not (material and bibdoc_id == 0):
                copyrights_and_licenses_list[bibdoc_id]['license'].append([label, license_body, url, sponsor_info])
            elif copyrights_and_licenses_list.has_key(material):
                copyrights_and_licenses_list[material]['license'].append([label, license_body, url, sponsor_info])

        # We also need to add the auto CERN licenses to specified BibDocs
        for bibdoc_id in add_CERN_license_link_to_bibdocs:
            copyrights_and_licenses_list[bibdoc_id]['license'].append(['', '', CFG_CERN_LICENSE_URL, ''])

        for linkage, copyright_and_license in iteritems(copyrights_and_licenses_list):
            copyrights = copyright_and_license['copyright']
            licenses = copyright_and_license['license']
            if len(copyrights) == 1 and len(licenses) == 1:
                # Great that is one particular case we can maybe handle
                copyright_label, copyright_holder = copyrights[0]
                license_label, license_body, license_url, dummy = licenses[0]
                if not license_label or copyright_holder in ("&copy; " + license_label, license_label):
                    # Cool, we can squash things
                    if remove_link_to_CERN_license.lower() == 'yes' and \
                           license_url == CFG_CERN_LICENSE_URL:
                        # Thou must not display the license
                        license_url = ''
                    if show_material == 'yes' and not isinstance(linkage, int):
                        linkage_prefix = linkage + ': '
                    else:
                        linkage_prefix = ''
                    if license_url and link_to_licenses.lower() == 'yes':
                        out.add(linkage_prefix + create_html_link(license_url, {}, copyright_label))
                    else:
                        out.add(linkage_prefix + copyright_label)
                    continue

            # that is an 'else' for all other cases...
            # First print simply the copyrights
            copyright_tmp = copyrights_separator.join([copyright_label for (copyright_label, copyright_holder) in copyrights])
            if show_material == 'yes' and not isinstance(linkage, int):
                copyright_tmp =  linkage + ': ' + copyright_tmp

            license_tmp = []
            # Then do the licenses.

            # Check if we should prefix with "License(s):", i.e. when
            # keyword license is missing from license labels

            prefix_license = ''
            prefix_license_p = len([license_info for license_info in licenses if not 'license' in license_info[0].lower()])
            if prefix_license_p:
                if len(licenses) == 1:
                    prefix_license = 'License: '
                else:
                    prefix_license = 'Licenses: '

            sponsor_tmp = []
            for license_label, license_body, license_url, sponsor_info in licenses:
                if sponsor_info:
                    sponsor_tmp.append(sponsor_info)
                if not license_label and license_url and link_to_licenses.lower() == 'yes':
                    license_tmp.append(create_html_link(license_url, {}, 'License'))
                    prefix_license = '' # no longer needed
                elif license_label and license_url and link_to_licenses.lower() == 'yes':
                    license_tmp.append(create_html_link(license_url, {}, license_label))
                elif license_label:
                    license_tmp.append(license_label)

            if sponsor_tmp and show_sponsor == "yes" and 'SCOAP3' in sponsor_tmp:
                sponsored_by = 'sponsored by <a href="http://scoap3.org">SCOAP&#179;</a>'
            else:
                sponsored_by = ''

            if show_licenses.lower() != 'yes':
                # All that work for nothing!
                license_tmp = []
            if copyright_tmp and license_tmp:
                out.add('%s (%s%s)%s' % \
                         (copyright_tmp, \
                          prefix_license, \
                          licenses_separator.join(license_tmp), \
                          sponsored_by and ', %s' % sponsored_by or '' \
                         )\
                       )
            else:
                out.add(copyright_tmp+licenses_separator.join(license_tmp))

        return instances_separator.join(out).replace('©', '&copy;')

def escape_values(bfo):
    """
    Called by BibFormat in order to check if output of this element
    should be escaped.
    """
    return 0


def test():
    """
    Test the function
    """
    from invenio.modules.formatter.engine import BibFormatObject

    xml1 = '''
<record>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo1 = BibFormatObject(0, xml_record=xml1)
    assert(format_element(bfo1)  == '&copy; CERN')


    xml2 = '''
<record>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="f">ATLAS Experiment © CERN</subfield>
    </datafield>
</record>'''

    bfo2 = BibFormatObject(0, xml_record=xml2)
    assert(format_element(bfo2)  == 'ATLAS Experiment &copy; CERN')


    xml3 = '''
<record>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">BBC</subfield>
    </datafield>
</record>'''

    bfo3 = BibFormatObject(0, xml_record=xml3)
    assert(format_element(bfo3)  == '&copy; BBC')


    xml4 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="u">http://cern.ch</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo4 = BibFormatObject(0, xml_record=xml4)
    assert(format_element(bfo4)  == '<a href="http://cern.ch">&copy; CERN</a>')


    xml5 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">BBC</subfield>
    </datafield>
</record>'''

    bfo5 = BibFormatObject(0, xml_record=xml5)
    assert(format_element(bfo5)  == '<a href="http://bbc.co.uk">&copy; BBC</a>')


    xml6 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo6 = BibFormatObject(0, xml_record=xml6)
    assert(format_element(bfo6)  == '&copy; CERN (License: <a href="http://bbc.co.uk">BBC</a>)')


    xml7 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">1</subfield>
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo7 = BibFormatObject(0, xml_record=xml7)
    assert(format_element(bfo7)  == '&copy; CERN, <a href="http://bbc.co.uk">BBC</a>')


    xml8 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">1</subfield>
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo8 = BibFormatObject(0, xml_record=xml8)
    assert(format_element(bfo8)  == '&copy; CERN (License: <a href="http://bbc.co.uk">BBC</a>)')


    xml9 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="8">2</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">2</subfield>
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo9 = BibFormatObject(0, xml_record=xml9)
    assert(format_element(bfo9)  == '&copy; CERN, <a href="http://bbc.co.uk">BBC</a>')


    xml10 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="8">2</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">1</subfield>
        <subfield code="d">BBC</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">2</subfield>
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo10 = BibFormatObject(0, xml_record=xml10)
    assert(format_element(bfo10)  == '<a href="http://bbc.co.uk">&copy; BBC</a>, &copy; CERN')


    xml11 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC License 1</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="8">2</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">1</subfield>
        <subfield code="d">BBC</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">2</subfield>
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo11 = BibFormatObject(0, xml_record=xml11)
    assert(format_element(bfo11)  == '&copy; CERN, &copy; BBC (<a href="http://bbc.co.uk">BBC License 1</a>)')


    xml12 = '''
<record>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo12 = BibFormatObject(0, xml_record=xml12)
    assert(format_element(bfo12, auto_link_to_CERN_license='yes')  == '<a href="%s">&copy; CERN</a>' % CFG_CERN_LICENSE_URL)


    xml13 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
    </datafield>
    <datafield tag="269" ind1=" " ind2=" ">
        <subfield code="b">CERN</subfield>
        <subfield code="c">2010</subfield>
    </datafield>
</record>'''

    bfo13 = BibFormatObject(0, xml_record=xml13)
    assert(format_element(bfo13, auto_link_to_CERN_license='yes')  == '<a href="%s">&copy; CERN</a>' % CFG_CERN_LICENSE_URL)


##     xml14 = '''
## <record>
##     <datafield tag="269" ind1=" " ind2=" ">
##         <subfield code="b">CERN</subfield>
##         <subfield code="c">2010</subfield>
##     </datafield>
## </record>'''

##     bfo14 = BibFormatObject(0, xml_record=xml14)
##     assert(format_element(bfo14, auto_link_to_CERN_license='yes')  == 'CERN')


    xml15 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC License 1</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="8">2</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">1</subfield>
        <subfield code="d">BBC</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">2</subfield>
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo15 = BibFormatObject(0, xml_record=xml15)
    assert(format_element(bfo15, show_licenses='no', instances_separator=" &amp; ")  == '&copy; BBC &amp; &copy; CERN')

    xml16 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC License 1</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="8">2</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">1</subfield>
        <subfield code="d">BBC</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">2</subfield>
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo16 = BibFormatObject(0, xml_record=xml16)
    assert(format_element(bfo16, link_to_licenses='no')  == '&copy; BBC (BBC License 1), &copy; CERN')

    xml17 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC License 1</subfield>
        <subfield code="u">http://bbc.co.uk/license1</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC License 2</subfield>
        <subfield code="u">http://bbc.co.uk/license2</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="8">2</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">1</subfield>
        <subfield code="d">BBC</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="8">2</subfield>
        <subfield code="d">CERN</subfield>
    </datafield>
</record>'''

    bfo17 = BibFormatObject(0, xml_record=xml17)
    assert(format_element(bfo17)  == '&copy; CERN, &copy; BBC (<a href="http://bbc.co.uk/license1">BBC License 1</a>, <a href="http://bbc.co.uk/license2">BBC License 2</a>)')

    xml18 = '''
<record>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="g">1984</subfield>
    </datafield>
</record>'''

    bfo18 = BibFormatObject(0, xml_record=xml18)
    assert(format_element(bfo18)  == '&copy; 1984 CERN')

    xml19 = '''
<record>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="g">1984</subfield>
        <subfield code="f">ATLAS Experiment © CERN</subfield>
    </datafield>
</record>'''

    bfo19 = BibFormatObject(0, xml_record=xml19)
    assert(format_element(bfo19)  == 'ATLAS Experiment &copy; CERN')


    xml20 = '''
<record>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">BBC</subfield>
        <subfield code="g">1984</subfield>
    </datafield>
</record>'''

    bfo20 = BibFormatObject(0, xml_record=xml20)
    assert(format_element(bfo20)  == '&copy; 1984 BBC')


    xml21 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="u">http://cern.ch</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="g">1984</subfield>
    </datafield>
</record>'''

    bfo21 = BibFormatObject(0, xml_record=xml21)
    assert(format_element(bfo21)  == '<a href="http://cern.ch">&copy; 1984 CERN</a>')


    xml22 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">BBC</subfield>
        <subfield code="u">http://bbc.co.uk</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">BBC</subfield>
        <subfield code="g">1984</subfield>
    </datafield>
</record>'''

    bfo22 = BibFormatObject(0, xml_record=xml22)
    assert(format_element(bfo22)  == '<a href="http://bbc.co.uk">&copy; 1984 BBC</a>')


    xml23 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CC-BY-3.0</subfield>
        <subfield code="u">http://creativecommons.org/licenses/by/3.0/</subfield>
        <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CC-BY-3.0</subfield>
        <subfield code="u">http://creativecommons.org/licenses/by/3.0/</subfield>
        <subfield code="3">Publication</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="g">2011</subfield>
        <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="g">2012</subfield>
       <subfield code="3">Publication</subfield>
    </datafield>
</record>'''

    bfo23 = BibFormatObject(0, xml_record=xml23)
    assert(format_element(bfo23)  == 'Publication: &copy; 2012 CERN (License: <a href="http://creativecommons.org/licenses/by/3.0/">CC-BY-3.0</a>), Preprint: &copy; 2011 CERN (License: <a href="http://creativecommons.org/licenses/by/3.0/">CC-BY-3.0</a>)')


    xml24 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CC-BY-3.0</subfield>
        <subfield code="u">http://creativecommons.org/licenses/by/3.0/</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CC-BY-3.0</subfield>
        <subfield code="u">http://creativecommons.org/licenses/by/3.0/</subfield>
        <subfield code="3">Publication</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="g">2011</subfield>
        <subfield code="8">1</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="g">2012</subfield>
       <subfield code="3">Publication</subfield>
    </datafield>
</record>'''

    bfo24 = BibFormatObject(0, xml_record=xml24)
    assert(format_element(bfo24)  == 'Publication: &copy; 2012 CERN (License: <a href="http://creativecommons.org/licenses/by/3.0/">CC-BY-3.0</a>), &copy; 2011 CERN (License: <a href="http://creativecommons.org/licenses/by/3.0/">CC-BY-3.0</a>)')


    xml25 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CC-BY-3.0</subfield>
        <subfield code="u">http://creativecommons.org/licenses/by/3.0/</subfield>
        <subfield code="3">Publication</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="g">2011</subfield>
        <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">FOO</subfield>
        <subfield code="g">2012</subfield>
       <subfield code="3">Publication</subfield>
    </datafield>
</record>'''

    bfo25 = BibFormatObject(0, xml_record=xml25)
    assert(format_element(bfo25, auto_link_to_CERN_license='yes')  == 'Publication: &copy; 2012 FOO (License: <a href="http://creativecommons.org/licenses/by/3.0/">CC-BY-3.0</a>), Preprint: <a href="http://copyright.cern.ch/">&copy; 2011 CERN</a>')


    xml26 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CC-BY-3.0</subfield>
        <subfield code="3">Publication</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
        <subfield code="a">CERN</subfield>
        <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">CERN</subfield>
        <subfield code="g">2011</subfield>
        <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
        <subfield code="d">FOO</subfield>
        <subfield code="g">2012</subfield>
       <subfield code="3">Publication</subfield>
    </datafield>
</record>'''

    bfo26 = BibFormatObject(0, xml_record=xml26)
    assert(format_element(bfo26, remove_link_to_CERN_license="no")  == 'Publication: &copy; 2012 FOO (License: <a href="http://creativecommons.org/licenses/by/3.0/">CC-BY-3.0</a>), Preprint: <a href="http://copyright.cern.ch/">&copy; 2011 CERN</a>')

    xml27 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
       <subfield code="f">SCOAP3</subfield>
       <subfield code="a">CC-BY-3.0</subfield>
       <subfield code="3">Publication</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
       <subfield code="a">CERN</subfield>
       <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
       <subfield code="d">CERN</subfield>
       <subfield code="g">2011</subfield>
       <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
       <subfield code="d">ESA</subfield>
       <subfield code="g">2014</subfield>
      <subfield code="3">Publication</subfield>
    </datafield>
</record>'''

    bfo27 = BibFormatObject(0, xml_record=xml27)
    assert(format_element(bfo27, remove_link_to_CERN_license="yes")  == 'Preprint: &copy; 2011 CERN, Publication: &copy; 2014 ESA (License: <a href="http://creativecommons.org/licenses/by/3.0/">CC-BY-3.0</a>), sponsored by <a href="http://scoap3.org">SCOAP&#179;</a>')

    xml28 = '''
<record>
    <datafield tag="540" ind1=" " ind2=" ">
       <subfield code="f">SCOAP3</subfield>
       <subfield code="a">CC-BY-3.0</subfield>
       <subfield code="3">Publication</subfield>
    </datafield>
    <datafield tag="540" ind1=" " ind2=" ">
       <subfield code="a">CERN</subfield>
       <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
       <subfield code="d">CERN</subfield>
       <subfield code="g">2011</subfield>
       <subfield code="3">Preprint</subfield>
    </datafield>
    <datafield tag="542" ind1=" " ind2=" ">
       <subfield code="d">ESA</subfield>
       <subfield code="g">2014</subfield>
      <subfield code="3">Publication</subfield>
    </datafield>
</record>'''

    bfo28 = BibFormatObject(0, xml_record=xml28)
    assert(format_element(bfo28, remove_link_to_CERN_license="yes", show_sponsor="no")  == 'Preprint: &copy; 2011 CERN, Publication: &copy; 2014 ESA (License: <a href="http://creativecommons.org/licenses/by/3.0/">CC-BY-3.0</a>)')

    print("All tests run ok")

if __name__ == "__main__":
    test()
