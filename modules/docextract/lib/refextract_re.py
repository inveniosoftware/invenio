# -*- coding: utf-8 -*-
##
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

import re
from datetime import datetime

# Pattern for PoS journal

# e.g. 2006
re_pos_year_num = ur'(?:19|20)\d{2}'
re_pos_year = ur'(?P<year>(' \
                  + ur'\s' + re_pos_year_num + ur'\s' \
                  + ur'|' \
                  + ur'\(' + re_pos_year_num + '\)' \
                  + ur'))'
# e.g. LAT2007
re_pos_volume = ur'(?P<volume>\w{1,10}(?:19|20)\d{2})'
# e.g. (LAT2007)
re_pos_volume_par = ur'\(' + re_pos_volume + ur'\)'
# e.g. 20
re_pos_page = ur'(?P<page>\d{1,4})'
re_pos_title = ur'POS'

re_pos_patterns = [
    re_pos_title + ur'\s*' + re_pos_year + ur'\s+' + re_pos_volume + ur'\s+' + re_pos_page,
    re_pos_title + ur'\s+' + re_pos_volume + ur'\s*' + re_pos_year + ur'\s*' + re_pos_page,
    re_pos_title + ur'\s+' + re_pos_volume + ur'\s+' + re_pos_page + ur'\s*' + re_pos_year,
    re_pos_title + ur'\s*' + re_pos_volume_par + ur'\s*' + re_pos_page,
]
re_opts = re.VERBOSE | re.UNICODE | re.IGNORECASE


def compute_pos_patterns(patterns):
    return [re.compile(p, re_opts) for p in patterns]
re_pos = compute_pos_patterns(re_pos_patterns)

# Pattern for arxiv numbers
re_arxiv = re.compile(ur""" # arxiv 9910-1234v9 [physics.ins-det]
    ARXIV[\s:-]*(?P<year>\d{2})-?(?P<month>\d{2})
    [\s.-]*(?P<num>\d{4})(?:[\s-]*V(?P<version>\d))?
    \s*(?P<suffix>\[[A-Z.-]+\])? """, re.VERBOSE | re.UNICODE | re.IGNORECASE)

# Pattern for old arxiv numbers
old_arxiv_numbers = ur"(?P<num>/\d{7})"
old_arxiv = {
    ur"acc-ph": None,
    ur"astro-ph": None,
    ur"astro-phy": "astro-ph",
    ur"astro-ph\.[a-z]{2}": None,
    ur"atom-ph": None,
    ur"chao-dyn": None,
    ur"chem-ph": None,
    ur"cond-mat": None,
    ur"cs": None,
    ur"cs\.[a-z]{2}": None,
    ur"gr-qc": None,
    ur"hep-ex": None,
    ur"hep-lat": None,
    ur"hep-ph": None,
    ur"hepph": "hep-ph",
    ur"hep-th": None,
    ur"hepth": "hep-th",
    ur"math": None,
    ur"math\.[a-z]{2}": None,
    ur"math-ph": None,
    ur"nlin": None,
    ur"nlin\.[a-z]{2}": None,
    ur"nucl-ex": None,
    ur"nucl-th": None,
    ur"physics": None,
    ur"physics\.acc-ph": None,
    ur"physics\.ao-ph": None,
    ur"physics\.atm-clus": None,
    ur"physics\.atom-ph": None,
    ur"physics\.bio-ph": None,
    ur"physics\.chem-ph": None,
    ur"physics\.class-ph": None,
    ur"physics\.comp-ph": None,
    ur"physics\.data-an": None,
    ur"physics\.ed-ph": None,
    ur"physics\.flu-dyn": None,
    ur"physics\.gen-ph": None,
    ur"physics\.geo-ph": None,
    ur"physics\.hist-ph": None,
    ur"physics\.ins-det": None,
    ur"physics\.med-ph": None,
    ur"physics\.optics": None,
    ur"physics\.plasm-ph": None,
    ur"physics\.pop-ph": None,
    ur"physics\.soc-ph": None,
    ur"physics\.space-ph": None,
    ur"plasm-ph": "physics\.plasm-ph",
    ur"q-bio\.[a-z]{2}": None,
    ur"q-fin\.[a-z]{2}": None,
    ur"q-alg": None,
    ur"quant-ph": None,
    ur"quant-phys": "quant-ph",
    ur"solv-int": None,
    ur"stat\.[a-z]{2}": None,
    ur"stat-mech": None,
}


def compute_arxiv_re(report_pattern, report_number):
    if report_number is None:
        report_number = ur"\g<name>"
    report_re = re.compile("(?P<name>" + report_pattern + ")" \
                                        + old_arxiv_numbers, re.U|re.I)
    return report_re, report_number

RE_OLD_ARXIV = [compute_arxiv_re(*i) for i in old_arxiv.iteritems()]


def compute_years():
    current_year = datetime.now().year
    return '|'.join(str(y)[2:] for y in xrange(1991, current_year + 1))
arxiv_years = compute_years()


def compute_months():
    return '|'.join(str(y).zfill(2) for y in xrange(1, 13))
arxiv_months = compute_months()

re_new_arxiv = re.compile(ur""" # 9910.1234v9 [physics.ins-det]
    (?<!ARXIV:)
    (?P<year>%(arxiv_years)s)
    (?P<month>%(arxiv_months)s)
    \.(?P<num>\d{4})(?:[\s-]*V(?P<version>\d))?
    \s*(?P<suffix>\[[A-Z.-]+\])? """ % {'arxiv_years': arxiv_years,
        'arxiv_months': arxiv_months}, re.VERBOSE | re.UNICODE | re.IGNORECASE)

# Pattern to recognize quoted text:
re_quoted = re.compile(ur'"(?P<title>[^"]+)"', re.UNICODE)

# Pattern to recognise an ISBN for a book:
re_isbn = re.compile(ur"""
    (?:ISBN[-– ]*(?:|10|13)|International Standard Book Number)
    [:\s]*
    (?P<code>[-\-–0-9Xx]{10,25})""", re.VERBOSE | re.UNICODE)

# Pattern to recognise a correct knowledge base line:
re_kb_line = re.compile(ur'^\s*(?P<seek>[^\s].*)\s*---\s*(?P<repl>[^\s].*)\s*$',
                        re.UNICODE)

# precompile some often-used regexp for speed reasons:
re_regexp_character_class = re.compile(ur'\[[^\]]+\]', re.UNICODE)
re_multiple_hyphens = re.compile(ur'-{2,}', re.UNICODE)


# In certain papers, " bf " appears just before the volume of a
# cited item. It is believed that this is a mistyped TeX command for
# making the volume "bold" in the paper.
# The line may look something like this after numeration has been recognised:
# M. Bauer, B. Stech, M. Wirbel, Z. Phys. bf C : <cds.VOL>34</cds.VOL>
# <cds.YR>(1987)</cds.YR> <cds.PG>103</cds.PG>
# The " bf " stops the title from being correctly linked with its series
# and/or numeration and thus breaks the citation.
# The pattern below is used to identify this situation and remove the
# " bf" component:
re_identify_bf_before_vol = \
                re.compile(ur' bf ((\w )?: \<cds\.VOL\>)', \
                            re.UNICODE)

# Patterns used for creating institutional preprint report-number
# recognition patterns (used by function "institute_num_pattern_to_regex"):
# Recognise any character that isn't a->z, A->Z, 0->9, /, [, ], ' ', '"':
re_report_num_chars_to_escape = \
                re.compile(ur'([^\]A-Za-z0-9\/\[ "])', re.UNICODE)
# Replace "hello" with hello:
re_extract_quoted_text = (re.compile(ur'\"([^"]+)\"', re.UNICODE), ur'\g<1>',)
# Replace / [abcd ]/ with /( [abcd])?/ :
re_extract_char_class = (re.compile(ur' \[([^\]]+) \]', re.UNICODE), \
                          ur'( [\g<1>])?')


# URL recognition:
# Stand-alone URL (e.g. http://invenio-software.org/ )
re_raw_url = \
 re.compile(ur"""\"?
    (
        (https?|s?ftp):\/\/([\w\d\_\.\-])+(:\d{1,5})?
        (\/\~([\w\d\_\.\-])+)?
        (\/([\w\d\_\.\-\?\=\&])+)*
        (\/([\w\d\_\-]+\.\w{1,6})?)?
    )
    \"?""", re.UNICODE|re.I|re.VERBOSE)

# HTML marked-up URL (e.g. <a href="http://invenio-software.org/">
# CERN Document Server Software Consortium</a> )
re_html_tagged_url = \
 re.compile(ur"""(\<a\s+href\s*=\s*([\'"])?
    (((https?|s?ftp):\/\/)?([\w\d\_\.\-])+(:\d{1,5})?
    (\/\~([\w\d\_\.\-])+)?(\/([\w\d\_\.\-\?\=])+)*
    (\/([\w\d\_\-]+\.\w{1,6})?)?)([\'"])?\>
    ([^\<]+)
    \<\/a\>)""", re.UNICODE|re.I|re.VERBOSE)


# Numeration recognition pattern - used to identify numeration
# associated with a title when marking the title up into MARC XML:
vol_tag = ur'<cds\.VOL\>(?P<vol>[^<]+)<\/cds\.VOL>'
year_tag = ur'\<cds\.YR\>\((?P<yr>[^<]+)\)\<\/cds\.YR\>'
series_tag = ur'(?P<series>(?:[A-H]|I{1,3}V?|VI{0,3}))?'
page_tag = ur'\<cds\.PG\>(?P<pg>[^<]+)\<\/cds\.PG\>'
re_recognised_numeration_for_title_plus_series = re.compile(
    ur'^\s*[\.,]?\s*(?:Ser\.\s*)?' + series_tag + ur'\s*:?\s*' + vol_tag +
    u'\s*(?: ' + year_tag + u')?\s*(?: ' + page_tag + u')', re.UNICODE)

# Another numeration pattern. This one is designed to match marked-up
# numeration that is essentially an IBID, but without the word "IBID". E.g.:
# <cds.JOURNAL>J. Phys. A</cds.JOURNAL> : <cds.VOL>31</cds.VOL>
# <cds.YR>(1998)</cds.YR> <cds.PG>2391</cds.PG>; : <cds.VOL>32</cds.VOL>
# <cds.YR>(1999)</cds.YR> <cds.PG>6119</cds.PG>.
re_numeration_no_ibid_txt = \
          re.compile(ur"""
          ^((\s*;\s*|\s+and\s+)(?P<series>(?:[A-H]|I{1,3}V?|VI{0,3}))?\s*:?\s   ## Leading ; : or " and :", and a possible series letter
          \<cds\.VOL\>(?P<vol>\d+|(?:\d+\-\d+))\<\/cds\.VOL>\s                  ## Volume
          \<cds\.YR\>\((?P<yr>[12]\d{3})\)\<\/cds\.YR\>\s                       ## year
          \<cds\.PG\>(?P<pg>[RL]?\d+[c]?)\<\/cds\.PG\>)                         ## page
          """, re.UNICODE|re.VERBOSE)

re_title_followed_by_series_markup_tags = \
     re.compile(ur'(\<cds.JOURNAL(?P<ibid>ibid)?\>([^\<]+)\<\/cds.JOURNAL(?:ibid)?\>\s*.?\s*\<cds\.SER\>([A-H]|(I{1,3}V?|VI{0,3}))\<\/cds\.SER\>)', re.UNICODE)

re_title_followed_by_implied_series = \
     re.compile(ur'(\<cds.JOURNAL(?P<ibid>ibid)?\>([^\<]+)\<\/cds.JOURNAL(?:ibid)?\>\s*.?\s*([A-H]|(I{1,3}V?|VI{0,3}))\s+:)', re.UNICODE)


re_punctuation = re.compile(ur'[\.\,\;\'\(\)\-]', re.UNICODE)

# The following pattern is used to recognise "citation items" that have been
# identified in the line, when building a MARC XML representation of the line:
re_tagged_citation = re.compile(ur"""
          \<cds\.                ## open tag: <cds.
          ((?:JOURNAL(?P<ibid>ibid)?)  ## a JOURNAL tag
          |VOL                   ## or a VOL tag
          |YR                    ## or a YR tag
          |PG                    ## or a PG tag
          |REPORTNUMBER          ## or a REPORTNUMBER tag
          |SER                   ## or a SER tag
          |URL                   ## or a URL tag
          |DOI                   ## or a DOI tag
          |QUOTED                ## or a QUOTED tag
          |ISBN                  ## or a ISBN tag
          |PUBLISHER             ## or a PUBLISHER tag
          |AUTH(stnd|etal|incl)) ## or an AUTH tag
          (\s\/)?                ## optional /
          \>                     ## closing of tag (>)
          """, re.UNICODE|re.VERBOSE)


# is there pre-recognised numeration-tagging within a
# few characters of the start if this part of the line?
re_tagged_numeration_near_line_start = \
                         re.compile(ur'^.{0,4}?<CDS (VOL|SER)>', re.UNICODE)

re_ibid = \
   re.compile(ur'(-|\b)?((?:(?:IBID(?!EM))|(?:IBIDEM))\.?(\s([A-H]|(I{1,3}V?|VI{0,3})|[1-3]))?)\s?', \
               re.UNICODE)

re_matched_ibid = re.compile(ur'(?:(?:IBID(?!EM))|(?:IBIDEM))(?:[\.,]{0,2}\s*|\s+)([A-H]|(I{1,3}V?|VI{0,3})|[1-3])?', \
                               re.UNICODE)

re_series_from_numeration = re.compile(ur'^\.?,?\s+([A-H]|(I{1,3}V?|VI{0,3}))\s+:\s+', \
                               re.UNICODE)

# Obtain the series character from the standardised title text
# Only used when no series letter is obtained from numeration matching
re_series_from_title = re.compile(ur"""
    ([^\s].*)
    (?:[\s\.]+(?:(?P<open_bracket>\()\s*[Ss][Ee][Rr]\.)?
            ([A-H]|(I{1,3}V?|VI{0,3}))
    )?
    (?(open_bracket)\s*\))$   ## Only match the ending bracket if the opening bracket was found""", \
                               re.UNICODE|re.VERBOSE)


re_wash_volume_tag = (
    re.compile(ur'<cds\.VOL>(\w) (\d+)</cds\.VOL>'),
        ur'<cds.VOL>\g<1>\g<2></cds.VOL>',
)

# Roman Numbers
re_roman_numbers = ur"[XxVvIi]+"

# Sep
re_sep = ur"\s*[,\s:-]\s*"

# Title tag
re_title_tag = ur"(?P<title_tag><cds\.JOURNAL>[^<]*<\/cds\.JOURNAL>)"

# Number (within a volume)
re_volume_sub_number = ur'[Nn][oO°]\.?\s*\d{1,6}'
re_volume_sub_number_opt = u'(?:' + re_sep + u'(?P<vol_sub>' + \
    re_volume_sub_number + u'))?'

# Volume
re_volume_prefix = ur"(?:[Vv]o?l?\.?|[Nn][oO°]\.?)"  # Optional Vol./No.
re_volume_suffix = ur"(?:\s*\(\d{1,2}(?:-\d)?\))?"
re_volume_num = ur"\d+|" + "(?:(?<!\w)" + re_roman_numbers + "(?!\w))"
re_volume_id = ur"(?P<vol>(?:(?:[A-Za-z]\s?)?(?P<vol_num>%(volume_num)s))|(?:(?:%(volume_num)s)(?:[A-Za-z]))|(?:(?:[A-Za-z]\s?)?\d+\s*\-\s*(?:[A-Za-z]\s?)?\d+))" % {'volume_num': re_volume_num}
re_volume_check = ur"(?<![\/\d])"
re_volume = ur"\b" + u"(?:" + re_volume_prefix + u")?\s*" + re_volume_check + \
    re_volume_id + re_volume_suffix

# Month
re_short_month = ur"""(?:(?:
[Jj]an|[Ff]eb|[Mm]ar|[Aa]pr|[Mm]ay|[Jj]un|
[Jj]ul|[Aa]ug|[Ss]ep|[Oo]ct|[Nn]ov|[Dd]ec
)\.?)"""

re_month = ur"""(?:(?:
[Jj]anuary|[Ff]ebruary|[Mm]arch|[Aa]pril|[Mm]ay|[Jj]une|
[Jj]uly|[Aa]ugust|[Ss]eptember|[Oo]ctober|[Nn]ovember|[Dd]ecember
)\.?)"""

# Year
re_year_num = ur"(?:19|20)\d{2}"
re_year_text = u"(?P<year>[A-Za-z]?" + re_year_num + u")(?:[A-Za-z]?)"
re_year = ur"""
    \(?
    (?:%(short_month)s[,\s]\s*)?  # Jul, 1980
    (?:%(month)s[,\s]\s*)?        # July, 1980
    (?<!\d)
    %(year)s
    (?!\d)
    \)?
""" % {
    'year': re_year_text,
    'short_month': re_short_month,
    'month': re_month,
}

# Page
re_page_prefix = ur"[pP]?[p]?\.?\s?"  # Starting page num: optional Pp.
re_page_num = ur"[RL]?\w?\d+[cC]?"    # pagenum with optional R/L
re_page_sep = ur"\s*[\s-]\s*"         # optional separatr between pagenums
re_page = re_page_prefix + \
    u"(?P<page>" + re_page_num + u")(?:" + re_page_sep + \
    u"(?P<page_end>" + re_page_num + u"))?"

# Series
re_series = ur"(?P<series>[A-H])"

# Used for allowing 3(1991) without space
re_look_ahead_parentesis = ur"(?=\()"
re_sep_or_parentesis = u'(?:' + re_sep + u'|' + re_look_ahead_parentesis + ')'

re_look_behind_parentesis = ur"(?<=\))"
re_sep_or_after_parentesis = u'(?:' + \
    re_sep + u'|' + re_look_behind_parentesis + ')'


# After having processed a line for titles, it may be possible to find more
# numeration with the aid of the recognised titles. The following 2 patterns
# are used for this:

re_correct_numeration_2nd_try_ptn1 = (re.compile(
  re_year + re_sep +         # Year
  re_title_tag + re_sep +    # Recognised, tagged title
  re_volume + re_sep +       # The volume
  re_page,                   # The page
  re.UNICODE|re.VERBOSE), ur'\g<title_tag> : <cds.VOL>\g<vol></cds.VOL> ' \
    ur'<cds.YR>(\g<year>)</cds.YR> <cds.PG>\g<page></cds.PG>')

re_correct_numeration_2nd_try_ptn2 = (re.compile(
  re_year + re_sep +
  re_title_tag + re_sep +
  re_volume + re_sep +
  re_series + re_sep +
  re_page, re.UNICODE|re.VERBOSE),
    ur'\g<title_tag> <cds.SER>\g<series></cds.SER> : ' \
                                      ur'<cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG>')

re_correct_numeration_2nd_try_ptn3 = (re.compile(
  re_title_tag + re_sep +    # Recognised, tagged title
  re_volume + re_sep +       # The volume
  re_page,                   # The page
  re.UNICODE|re.VERBOSE), ur'\g<title_tag>  <cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.PG>\g<page></cds.PG>')


re_correct_numeration_2nd_try_ptn4 = (re.compile(
  re_title_tag + re_sep +        # Recognised, tagged title
  re_year + ur"\s*[.,\s:]\s*" +  # Year
  re_volume + re_sep +           # The volume
  re_page,                       # The page
  re.UNICODE|re.VERBOSE), ur'\g<title_tag> : <cds.VOL>\g<vol></cds.VOL> ' \
    ur'<cds.YR>(\g<year>)</cds.YR> <cds.PG>\g<page></cds.PG>')


re_correct_numeration_2nd_try_ptn5 = (re.compile(
  re_title_tag + re_sep + re_volume, re.UNICODE|re.VERBOSE),
    ur'\g<title_tag> <cds.VOL>\g<vol></cds.VOL>')

## precompile some regexps used to search for and standardize
## numeration patterns in a line for the first time:

## Delete the colon and expressions such as Serie, vol, V. inside the pattern
## <serie : volume> E.g. Replace the string """Series A, Vol 4""" with """A 4"""
re_strip_series_and_volume_labels = (re.compile(
    ur'(Serie\s|\bS\.?\s)?([A-H])\s?[:,]\s?(\b[Vv]o?l?\.?|\b[Nn]o\.?)?\s?(\d+)', re.UNICODE),
                      ur'\g<2> \g<4>')


## This pattern is not compiled, but rather included in
## the other numeration paterns:
re_nucphysb_subtitle = \
    ur'(?:[\(\[]\s*(?:[Ff][Ss]|[Pp][Mm])\s*\d{0,4}\s*[\)\]])'
re_nucphysb_subtitle_opt = \
    u'(?:' + re_sep + re_nucphysb_subtitle + u')?'


## the 4 main numeration patterns:

## Pattern 1: <vol, page, year>

## <v, p, y>
re_numeration_vol_page_yr = (re.compile(
  re_volume + re_volume_sub_number_opt + re_sep +
  re_page + re_sep_or_parentesis +
  re_year, re.UNICODE|re.VERBOSE), ur' : <cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')

## <v, [FS], p, y>
re_numeration_vol_nucphys_page_yr = (re.compile(
  re_volume + re_volume_sub_number_opt + re_sep +
  re_nucphysb_subtitle + re_sep +
  re_page + re_sep_or_parentesis +
  re_year, re.UNICODE|re.VERBOSE), ur' : <cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')

## <[FS], v, p, y>
re_numeration_nucphys_vol_page_yr = (re.compile(
  re_nucphysb_subtitle + re_sep +
  re_volume + re_sep +
  re_page + re_sep_or_parentesis +
  re_year, re.UNICODE|re.VERBOSE), ur' : <cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')

## Pattern 2: <vol, year, page>

## <v, y, p>
re_numeration_vol_yr_page = (re.compile(
  re_volume + re_sep_or_parentesis +
  re_year + re_sep_or_after_parentesis +
  re_page, re.UNICODE|re.VERBOSE), ur' : <cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')

## <v, sv, [FS]?, y, p>
re_numeration_vol_subvol_nucphys_yr_page = (re.compile(
  re_volume + re_volume_sub_number_opt +
  re_nucphysb_subtitle_opt + re_sep_or_parentesis +
  re_year + re_sep_or_after_parentesis +
  re_page, re.UNICODE|re.VERBOSE), ur' : <cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')

## <v, [FS]?, y, sv, p>
re_numeration_vol_nucphys_yr_subvol_page = (re.compile(
  re_volume + re_nucphysb_subtitle_opt +
  re_sep_or_parentesis +
  re_year + re_volume_sub_number_opt + re_sep +
  re_page, re.UNICODE|re.VERBOSE), ur' : <cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')

## <[FS]?, v, y, p>
re_numeration_nucphys_vol_yr_page = (re.compile(
  re_nucphysb_subtitle + re_sep +
  re_volume + re_sep_or_parentesis +        # The volume (optional "vol"/"no")
  re_year + re_sep_or_after_parentesis +    # Year
  re_page, re.UNICODE|re.VERBOSE), ur' : <cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')

## Pattern 3: <vol, serie, year, page>

## <v, s, [FS]?, y, p>
# re_numeration_vol_series_nucphys_yr_page = (re.compile(
#   re_volume + re_sep +
#   re_series + re_sep +
#   _sre_non_compiled_pattern_nucphysb_subtitle + re_sep_or_parentesis +
#   re_year + re_sep +
#   re_page, re.UNICODE|re.VERBOSE), ur' \g<series> : ' \
#                                       ur'<cds.VOL>\g<vol></cds.VOL> ' \
#                                       ur'<cds.YR>(\g<year>)</cds.YR> ' \
#                                       ur'<cds.PG>\g<page></cds.PG> ')

## <v, [FS]?, s, y, p
re_numeration_vol_nucphys_series_yr_page = (re.compile(
  re_volume + re_nucphysb_subtitle_opt + re_sep +
  re_series + re_sep_or_parentesis +
  re_year + re_sep_or_after_parentesis +
  re_page, re.UNICODE|re.VERBOSE), ur' \g<series> : ' \
                                  ur'<cds.VOL>\g<vol></cds.VOL> ' \
                                  ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                  ur'<cds.PG>\g<page></cds.PG> ')

## Pattern 4: <vol, serie, page, year>
## <v, s, [FS]?, p, y>
re_numeration_vol_series_nucphys_page_yr = (re.compile(
  re_volume + re_sep +
  re_series + re_nucphysb_subtitle_opt + re_sep +
  re_page + re_sep +
  re_year, re.UNICODE|re.VERBOSE), ur' \g<series> : ' \
                                      ur'<cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')

## <v, [FS]?, s, p, y>
re_numeration_vol_nucphys_series_page_yr = (re.compile(
    re_volume + re_nucphysb_subtitle_opt + re_sep +
    re_series + re_sep +
    re_page + re_sep +
    re_year, re.UNICODE|re.VERBOSE), ur' \g<series> : ' \
                                      ur'<cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')

## Pattern 5: <year, vol, page>
re_numeration_yr_vol_page = (re.compile(
    re_year + re_sep_or_after_parentesis +
    re_volume + re_sep +
    re_page, re.UNICODE|re.VERBOSE), ur' : <cds.VOL>\g<vol></cds.VOL> ' \
                                      ur'<cds.YR>(\g<year>)</cds.YR> ' \
                                      ur'<cds.PG>\g<page></cds.PG> ')


## Pattern used to locate references of a doi inside a citation
## This pattern matches both url (http) and 'doi:' or 'DOI' formats
re_doi = (re.compile(ur"""
    ((\(?[Dd][Oo][Ii](\s)*\)?:?(\s)*)       #'doi:' or 'doi' or '(doi)' (upper or lower case)
    |(https?:\/\/dx\.doi\.org\/))?          #or 'http://dx.doi.org/'    (neither has to be present)
    (10\.                                   #10.                        (mandatory for DOI's)
    \d{4}                                   #[0-9] x4
    \/                                      #/
    [\w\-_;\(\)\/\.]+                       #any character
    [\w\-_;\(\)\/])                         #any character excluding a full stop
    """, re.VERBOSE))


def _create_regex_pattern_add_optional_spaces_to_word_characters(word):
    """Add the regex special characters (\s*) to allow optional spaces between
       the characters in a word.
       @param word: (string) the word to be inserted into a regex pattern.
       @return: string: the regex pattern for that word with optional spaces
        between all of its characters.
    """
    new_word = u""
    for ch in word:
        if ch.isspace():
            new_word += ch
        else:
            new_word += ch + ur'\s*'
    return new_word


def get_reference_section_title_patterns():
    """Return a list of compiled regex patterns used to search for the title of
       a reference section in a full-text document.
       @return: (list) of compiled regex patterns.
    """
    patterns = []
    titles = [u'references',
              u'references.',
              u'r\u00C9f\u00E9rences',
              u'r\u00C9f\u00C9rences',
              u'reference',
              u'refs',
              u'r\u00E9f\u00E9rence',
              u'r\u00C9f\u00C9rence',
              u'r\xb4ef\xb4erences',
              u'r\u00E9fs',
              u'r\u00C9fs',
              u'bibliography',
              u'bibliographie',
              u'citations',
              u'literaturverzeichnis']
    sect_marker = u'^\s*([\[\-\{\(])?\s*' \
                  u'((\w|\d){1,5}([\.\-\,](\w|\d){1,5})?\s*' \
                  u'[\.\-\}\)\]]\s*)?' \
                  u'(?P<title>'
    sect_marker1 = u'^(\d){1,3}\s*(?P<title>'
    line_end = ur'(\s*s\s*e\s*c\s*t\s*i\s*o\s*n\s*)?)([\)\}\]])?' \
        ur'($|\s*[\[\{\(\<]\s*[1a-z]\s*[\}\)\>\]]|\:$)'

    for t in titles:
        t_ptn = re.compile(sect_marker + \
                            _create_regex_pattern_add_optional_spaces_to_word_characters(t) + \
                            line_end, re.I|re.UNICODE)
        patterns.append(t_ptn)
        ## allow e.g.  'N References' to be found where N is an integer
        t_ptn = re.compile(sect_marker1 + \
                       _create_regex_pattern_add_optional_spaces_to_word_characters(t) + \
                       line_end, re.I|re.UNICODE)
        patterns.append(t_ptn)

    return patterns


def get_reference_line_numeration_marker_patterns(prefix=u''):
    """Return a list of compiled regex patterns used to search for the marker
       of a reference line in a full-text document.
       @param prefix: (string) the possible prefix to a reference line
       @return: (list) of compiled regex patterns.
    """
    title = u""
    if type(prefix) in (str, unicode):
        title = prefix
    g_name = u'(?P<mark>'
    g_close = u')'
    space = ur'^\s*'
    patterns = [
        space + title + g_name + ur'\[\s*(?P<marknum>\d+)\s*\]' + g_close,
        space + title + g_name + ur'\[\s*[a-zA-Z]+\+?\s?(\d{1,4}[A-Za-z]?)?\s*\]' + g_close,
        space + title + g_name + ur'\{\s*(?P<marknum>\d+)\s*\}' + g_close,
        space + title + g_name + ur'\<\s*(?P<marknum>\d+)\s*\>' + g_close,
        space + title + g_name + ur'\(\s*(?P<marknum>\d+)\s*\)' + g_close,
        space + title + g_name + ur'(?P<marknum>\d+)\s*\.(?!\d)' + g_close,
        space + title + g_name + ur'(?P<marknum>\d+)\s+' + g_close,
        space + title + g_name + ur'(?P<marknum>\d+)\s*\]' + g_close,
        space + title + g_name + ur'(?P<marknum>\d+)\s*\}' + g_close,
        space + title + g_name + ur'(?P<marknum>\d+)\s*\)' + g_close,
        space + title + g_name + ur'(?P<marknum>\d+)\s*\>' + g_close,
        space + title + g_name + ur'\[\s*\]' + g_close,
        space + title + g_name + ur'\*' + g_close,
    ]
    return [re.compile(p, re.I|re.UNICODE) for p in patterns]


def get_reference_line_marker_pattern(pattern):
    """Return a list of compiled regex patterns used to search for the first
       reference line in a full-text document.
       The line is considered to start with either: [1] or {1}
       The line is considered to start with : 1. or 2. or 3. etc
       The line is considered to start with : 1 or 2 etc (just a number)
       @return: (list) of compiled regex patterns.
    """
    return re.compile(u'(?P<mark>' + pattern + u')', re.I|re.UNICODE)

re_reference_line_bracket_markers = get_reference_line_marker_pattern(
        ur'(?P<left>\[)\s*(?P<marknum>\d+)\s*(?P<right>\])'
)
re_reference_line_curly_bracket_markers = get_reference_line_marker_pattern(
        ur'(?P<left>\{)\s*(?P<marknum>\d+)\s*(?P<right>\})'
)
re_reference_line_dot_markers = get_reference_line_marker_pattern(
        ur'(?P<left>)\s*(?P<marknum>\d+)\s*(?P<right>\.)'
)
re_reference_line_number_markers = get_reference_line_marker_pattern(
        ur'(?P<left>)\s*(?P<marknum>\d+)\s*(?P<right>)'
)


def get_post_reference_section_title_patterns():
    """Return a list of compiled regex patterns used to search for the title
       of the section after the reference section in a full-text document.
       @return: (list) of compiled regex patterns.
    """
    compiled_patterns = []
    thead = ur'^\s*([\{\(\<\[]?\s*(\w|\d)\s*[\)\}\>\.\-\]]?\s*)?'
    ttail = ur'(\s*\:\s*)?'
    numatn = ur'(\d+|\w\b|i{1,3}v?|vi{0,3})[\.\,]{0,2}\b'
    roman_numbers = ur'[LVIX]'
    patterns = [
        # Section titles
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'appendix') + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'appendices') + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'acknowledgement') + ur's?' + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'acknowledgment') + ur's?' + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'table') + ur'\w?s?\d?' + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'figure') + ur's?' + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'list of figure') + ur's?' + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'annex') + ur's?' + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'discussion') + ur's?' + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'remercie') + ur's?' + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'index') + ur's?' + ttail,
        thead + _create_regex_pattern_add_optional_spaces_to_word_characters(u'summary') + ur's?' + ttail,
        # Figure nums
        ur'^\s*' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'figure') + numatn,
        ur'^\s*' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'fig') + ur'\.\s*' + numatn,
        ur'^\s*' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'fig') + ur'\.?\s*\d\w?\b',
        # Tables
        ur'^\s*' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'table') + numatn,
        ur'^\s*' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'tab') + ur'\.\s*' + numatn,
        ur'^\s*' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'tab') + ur'\.?\s*\d\w?\b',
        # Other titles formats
        ur'^\s*' + roman_numbers + ur'\.?\s*[Cc]onclusion[\w\s]*$',
    ]

    for p in patterns:
        compiled_patterns.append(re.compile(p, re.I|re.UNICODE))

    return compiled_patterns


def get_post_reference_section_keyword_patterns():
    """Return a list of compiled regex patterns used to search for various
       keywords that can often be found after, and therefore suggest the end of,
       a reference section in a full-text document.
       @return: (list) of compiled regex patterns.
    """
    compiled_patterns = []
    patterns = [u'(' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'prepared') + \
                ur'|' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'created') + \
                ur').*(AAS\s*)?\sLATEX',
                ur'AAS\s+?LATEX\s+?' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'macros') + u'v',
                ur'^\s*' + _create_regex_pattern_add_optional_spaces_to_word_characters(u'This paper has been produced using'),
                ur'^\s*' + \
                _create_regex_pattern_add_optional_spaces_to_word_characters(u'This article was processed by the author using Springer-Verlag') + \
                u' LATEX']
    for p in patterns:
        compiled_patterns.append(re.compile(p, re.I|re.UNICODE))
    return compiled_patterns


def regex_match_list(line, patterns):
    """Given a list of COMPILED regex patters, perform the "re.match" operation
       on the line for every pattern.
       Break from searching at the first match, returning the match object.
       In the case that no patterns match, the None type will be returned.
       @param line: (unicode string) to be searched in.
       @param patterns: (list) of compiled regex patterns to search  "line"
        with.
       @return: (None or an re.match object), depending upon whether one of
        the patterns matched within line or not.
    """
    m = None
    for ptn in patterns:
        m = ptn.match(line)
        if m is not None:
            break
    return m

# The different forms of arXiv notation
re_arxiv_notation = re.compile(ur"""
    (arxiv)|(e[\-\s]?print:?\s*arxiv)
    """, re.VERBOSE)

# et. al. before J. /// means J is a journal

re_num = re.compile(ur'(\d+)')
