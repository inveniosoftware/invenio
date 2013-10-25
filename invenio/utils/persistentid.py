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

import re
from urlparse import urlparse


doi_regexp = re.compile(
    "(doi:|http://dx.doi.org/)?(10\.\d+(.\d+)*/.*)$",
    flags=re.I
)
"""
See http://en.wikipedia.org/wiki/Digital_object_identifier
"""

handle_regexp = re.compile(
    "(hdl:|http://hdl.handle.net/)?([^/\.]+(\.[^/\.]+)*/.*)$",
    flags=re.I
)
"""
See http://handle.net/rfc/rfc3651.html

<Handle>          = <NamingAuthority> "/" <LocalName>
<NamingAuthority> = *(<NamingAuthority>  ".") <NAsegment>
<NAsegment>       = Any UTF8 char except "/" and "."
<LocalName>       = Any UTF8 char
"""

arxiv_post_2007_regexp = re.compile(
    "arXiv:(\d{4})\.(\d{4})(v\d+)?$",
    flags=re.I
)
"""
See http://arxiv.org/help/arxiv_identifier
"""

arxiv_pre_2007_regexp = re.compile("[a-z\-]+(\.[A-Z]{2})?/\d{4}\d+$")
"""
See http://arxiv.org/help/arxiv_identifier
"""

ads_regexp = re.compile("(ads:|ADS:)?(\d{4}[A-Z]\S{13}[A-Z.:])$")
"""
See http://adsabs.harvard.edu/abs_doc/help_pages/data.html
"""

pmcid_regexp = re.compile("PMC\d+$", flags=re.I)
"""
PubMed Central ID regular expression
"""

pmid_regexp = re.compile("(pmid:)?(\d+)$", flags=re.I)
"""
PubMed ID regular expression
"""

ark_suffix_regexp = re.compile("ark:/\d+/.+$")
"""
See http://en.wikipedia.org/wiki/Archival_Resource_Key and
https://confluence.ucop.edu/display/Curation/ARK
"""

lsid_regexp = re.compile("urn:lsid:[^:]+(:[^:]+){2,3}$", flags=re.I)
"""
See http://en.wikipedia.org/wiki/LSID
"""


def _convert_x_to_10(x):
    """
    Convert char to int with X being converted to 10.
    """
    return int(x) if x != 'X' else 10


def is_isbn10(val):
    """
    Test if argument is an ISBN-10 number

    Courtesy Wikipedia:
    http://en.wikipedia.org/wiki/International_Standard_Book_Number
    """
    val = val.replace("-", "").replace(" ", "").upper()
    if len(val) != 10:
        return False
    try:
        r = sum([(10 - i) * (_convert_x_to_10(x)) for i, x in enumerate(val)])
        return not (r % 11)
    except ValueError:
        return False


def is_isbn13(val):
    """
    Test if argument is an ISBN-13 number

    Courtesy Wikipedia:
    http://en.wikipedia.org/wiki/International_Standard_Book_Number
    """
    val = val.replace("-", "").replace(" ", "").upper()
    if len(val) != 13:
        return False
    try:
        total = sum([
            int(num) * weight for num, weight in zip(val, (1, 3) * 6)
        ])
        ck = (10 - total) % 10
        return ck == int(val[-1])
    except ValueError:
        return False


def is_isbn(val):
    """ Test if argument is an ISBN-10 or ISBN-13 number """
    if is_isbn10(val) or is_isbn13(val):
        if val[0:3] in ["978", "979"] or not is_ean13(val):
            return True
    return False


def is_issn(val):
    """ Test if argument is an ISSN number """
    val = val.replace("-", "").replace(" ", "").upper()
    if len(val) != 8:
        return False
    r = sum([(8 - i) * (_convert_x_to_10(x)) for i, x in enumerate(val)])
    return not (r % 11)


def is_istc(val):
    """
    Test if argument is a International Standard Text Code

    See http://www.istc-international.org/html/about_structure_syntax.aspx
    """
    val = val.replace("-", "").replace(" ", "").upper()
    if len(val) != 16:
        return False
    sequence = [11, 9, 3, 1]
    try:
        r = sum([int(x, 16)*sequence[i % 4] for i, x in enumerate(val[:-1])])
        ck = hex(r % 16)[2:].upper()
        return ck == val[-1]
    except ValueError:
        return False


def is_doi(val):
    """ Test if argument is a DOI """
    return doi_regexp.match(val)


def is_handle(val):
    """
    Test if argument is a Handle

    Note, DOIs are also handles, and handle are very generic so they will also
    match e.g. any URL your parse
    """
    return handle_regexp.match(val)


def is_ean8(val):
    """
    Test if argument is a International Article Number (EAN-8)
    """
    if len(val) != 8:
        return False
    sequence = [3, 1]
    try:
        r = sum([int(x)*sequence[i % 2] for i, x in enumerate(val[:-1])])
        ck = (10 - r % 10) % 10
        return ck == int(val[-1])
    except ValueError:
        return False


def is_ean13(val):
    """
    Test if argument is a International Article Number (EAN-13)

    http://en.wikipedia.org/wiki/International_Article_Number_(EAN)
    """
    if len(val) != 13:
        return False
    sequence = [1, 3]
    try:
        r = sum([int(x)*sequence[i % 2] for i, x in enumerate(val[:-1])])
        ck = (10 - r % 10) % 10
        return ck == int(val[-1])
    except ValueError:
        return False


def is_ean(val):
    """
    Test if argument is a International Article Number (EAN-13 or EAN-8)
    """
    return is_ean13(val) or is_ean8(val)


def is_isni(val):
    """
    Test if argument is an International Standard Name Identifier
    """
    val = val.replace("-", "").replace(" ", "").upper()
    if len(val) != 16:
        return False
    try:
        r = 0
        for x in val[:-1]:
            r = (r + int(x))*2
        ck = (12 - r % 11) % 11
        return ck == _convert_x_to_10(val[-1])
    except ValueError:
        return False


def is_orcid(val):
    """
    Test if argument is an ORCID ID

    See http://support.orcid.org/knowledgebase/articles/116780-structure-of-the-orcid-identifier
    """
    val = val.replace("-", "").replace(" ", "")
    if is_isni(val):
        val = int(val[:-1], 10)  # Remove check digit and convert to int.
        return val >= 15000000 and val <= 35000000
    return False


def is_ark(val):
    """ Test if argument is an ARK """
    res = urlparse(val)
    return ark_suffix_regexp.match(val) or (
        res.scheme == 'http'
        and res.netloc != ''
        # Note res.path includes leading slash, hence [1:] to use same reexp
        and ark_suffix_regexp.match(res.path[1:])
        and res.params == ''
    )


def is_purl(val):
    """ Test if argument is a PURL """
    res = urlparse(val)
    return (res.scheme == 'http'
            and res.netloc in ['purl.org', 'purl.oclc.org', 'purl.net',
                               'purl.com']
            and res.path != '')


def is_url(val):
    """
    Test if argument is a URL
    """
    res = urlparse(val)
    return bool(res.scheme and res.netloc and res.params == '')


def is_lsid(val):
    """
    Test if argument is a LSID
    """
    return is_urn(val) and lsid_regexp.match(val)


def is_urn(val):
    """
    Test if argument is a URN
    """
    res = urlparse(val)
    return bool(res.scheme == 'urn' and res.netloc == '' and res.path != '')


def is_ads(val):
    """ Test if argument is an ADS id """
    return ads_regexp.match(val)


def is_arxiv_post_2007(val):
    return arxiv_post_2007_regexp.match(val)


def is_arxiv_pre_2007(val):
    return arxiv_post_2007_regexp.match(val)


def is_arxiv(val):
    """ Test if argument is an arXiv ID """
    return is_arxiv_post_2007(val) or is_arxiv_pre_2007(val)


def is_pmid(val):
    """ Test if argument is a PubMed ID

    Warning: PMID are just integers, with not structure, so this function might
    wrongly say any integer is a PubMed ID
    """
    return pmid_regexp.match(val)


def is_pmcid(val):
    """
    PubMed Central ID
    """
    return pmcid_regexp.match(val)


CFG_PID_SCHEMES = [
    ('doi', is_doi),
    ('ark', is_ark),
    ('handle', is_handle),
    ('purl', is_purl),
    ('lsid', is_lsid),
    ('urn', is_urn),
    ('url', is_url),
    ('ads', is_ads),
    ('arxiv', is_arxiv),
    ('pmcid', is_pmcid),
    ('isbn', is_isbn),
    ('issn', is_issn),
    ('orcid', is_orcid),
    ('isni', is_isni),
    ('ean13', is_ean13),
    ('ean8', is_ean8),
    ('istc', is_istc),
    ('pmid', is_pmid),
]


def detect_identifier_schemes(val):
    """
    Detect persistent identifier scheme for a given value.

    Note, some schemes like PMID are very generic.
    """
    schemes = []
    for scheme, test in CFG_PID_SCHEMES:
        if test(val):
            schemes.append(scheme)

    if 'pmid' in schemes and len(schemes) != 1:
        # Remove pmid as it's too generic (any int)
        schemes = filter(lambda x: x != 'pmid', schemes)
    elif 'handle' in schemes and 'url' in schemes \
         and not val.startswith("http://hdl.handle.net/"):
        schemes = filter(lambda x: x != 'handle', schemes)
    elif 'handle' in schemes and 'ark' in schemes:
        schemes = filter(lambda x: x != 'handle', schemes)
    return schemes


def normalize_doi(val):
    m = doi_regexp.match(val)
    return m.group(2)


def normalize_handle(val):
    m = handle_regexp.match(val)
    return m.group(2)


def normalize_ads(val):
    m = ads_regexp.match(val)
    return m.group(2)


def normalize_pmid(val):
    m = pmid_regexp.match(val)
    return m.group(2)


def normalize_pid(val, scheme):
    """
    Normalize a persistent identifier

    E.g. doi:10.1234/foo and http://dx.doi.org/10.1234/foo and 10.1234/foo
    will all be normalized to 10.1234/foo.
    """
    if not val:
        return val

    if scheme == 'doi':
        return normalize_doi(val)
    elif scheme == 'handle':
        return normalize_handle(val)
    elif scheme == 'ads':
        return normalize_ads(val)
    elif scheme == 'pmid':
        return normalize_pmid(val)
    return val


def to_url(val, scheme):
    val = normalize_pid(val, scheme)
    if scheme == 'doi':
        return "http://dx.doi.org/%s" % val
    elif scheme == 'handle':
        return "http://hdl.handle.net/%s" % val
    elif scheme == 'handle':
        return "http://hdl.handle.net/%s" % val
    elif scheme == 'arxiv':
        return "http://arxiv.org/abs/%s" % val
    elif scheme == 'orcid':
        return "http://orcid.org/%s" % val
    elif scheme == 'pmid':
        return "http://www.ncbi.nlm.nih.gov/pubmed/%s" % val
    elif scheme == 'ads':
        return "http://adsabs.harvard.edu/abs/%s" % val
    elif scheme == 'pmcid':
        return "http://www.ncbi.nlm.nih.gov/pmc/articles/%s/" % val
    elif scheme == 'urn':
        if val.lower().startswith("urn:nbn:"):
            return "http://nbn-resolving.org/%s" % val
    elif scheme in ['purl', 'url']:
        return val
    return ""
