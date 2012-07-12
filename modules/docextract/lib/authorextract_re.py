# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2010, 2011 CERN.
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
import sys
from invenio.docextract_utils import write_message
from invenio.refextract_cli import halt
from invenio.refextract_config import CFG_REFEXTRACT_KBS


def get_author_affiliation_numeration_str(punct=None):
    """The numeration which can be applied to author names. Numeration
    is sometimes found next to authors of papers.
    @return: (string), which can be compiled into a regex; identifies
    numeration next to an author name.
    """

    ##FIXME cater for start or end numeration (ie two puncs)

    ## Number to look for, either general or specific
    re_number = '(?:\d\d?)'
    re_chained_numbers = "(?:(?:[,;]\s*%s\.?\s*))*" % re_number
    ## Punctuation surrounding the number, either general or specific again
    if punct is None:
        re_punct = "(?:[\{\(\[]?)"
    else:
        re_punct = re.escape(punct)

    ## Generic number finder (MUST NOT INCLUDE NAMED GROUPS!!!)
    numeration_str = """
    (?:\s*(%(punct)s)\s*            ## Left numeration punctuation
        (%(num)s\s*                 ## Core numeration item, either specific or generic
            %(num_chain)s           ## Extra numeration, either generic or empty
        )
        (?:(%(punct)s))       ## Right numeration punctuation
    )""" % {'num'       : re_number,
            'num_chain' : re_chained_numbers,
            'punct'     : re_punct}
    return numeration_str


def get_initial_surname_author_pattern(incl_numeration=False):
    """Match an author name of the form: 'initial(s) surname'

    Return a standard author, with a maximum of 6 initials, and a surname.
    The author pattern returned will match 'Initials Surname' formats only.
    The Initials MUST be uppercase, and MUST have at least a dot, hypen or apostrophe between them.
    @param incl_numeration: (boolean) Return an author pattern with optional numeration after authors.
    @return (string): The 'Initials Surname' author pattern."""
    # Possible inclusion of superscript numeration at the end of author names
    # Will match the empty string
    if incl_numeration:
        append_num_re = get_author_affiliation_numeration_str() + '?'
    else:
        append_num_re = ""

    return ur"""
    (?:
        (?:[A-Z]\w{2,20}\s+)?                                ## Optionally a first name before the initials

        (?<!Volume\s)                                        ## Initials (1-5) (cannot follow 'Volume\s')
        [A-Z](?:\s*[.'’\s-]{1,3}\s*[A-Z]){0,4}[.\s-]{1,2}\s* ## separated by .,-,',etc.

        (?:[A-Z]\w{2,20}\s+)?                                ## Optionally a first name after the initials

        (?:
            (?!%(invalid_prefixes)s)                         ## Invalid prefixes to avoid
            [A-Za-z]{1,3}(?<!and)(?:(?:[’'`´-]\s?)|\s)       ## The surname prefix: 1, 2 or 3
        )?                                                   ## character prefixes before the surname (e.g. 'van','de')

        (?!%(invalid_surnames)s)                             ## Invalid surnames to avoid
        [A-Z]                                                ## The surname, which must start with an upper case character
        (?:[rR]\.|\w{1,20})                                  ## handle Jr.
        (?:[\-’'`´][\w’']{1,20})?                            ## single hyphen allowed jan-el or Figueroa-O'Farrill
        [’']?                                                ## Eventually an ending '

        %(numeration)s                                       ## A possible number to appear after an author name, used for author extraction

        (?:               # Look for editor notation after the author group...
            \s*,?\s*      # Eventually a coma/space
            %(ed)s
        )?
    )""" % {
        'invalid_prefixes': '|'.join(invalid_prefixes),
        'invalid_surnames': '|'.join(invalid_surnames),
        'ed'              : re_ed_notation,
        'numeration'      : append_num_re,
    }


def get_surname_initial_author_pattern(incl_numeration=False):
    """Match an author name of the form: 'surname initial(s)'

    This is sometimes the represention of the first author found inside an author group.
    This author pattern is only used to find a maximum of ONE author inside an author group.
    Authors of this form MUST have either a comma after the initials, or an 'and',
    which denotes the presence of other authors in the author group.
    @param incl_numeration: (boolean) Return an author pattern with optional numeration after authors.
    @return (string): The 'Surname Initials' author pattern."""
    # Possible inclusion of superscript numeration at the end of author names
    # Will match the empty string
    if incl_numeration:
        append_num_re = get_author_affiliation_numeration_str() + '?'
    else:
        append_num_re = ""

    return ur"""
    (?:
        (?:
            (?!%(invalid_prefixes)s)                             ## Invalid prefixes to avoid
            [A-Za-z]{1,3}(?<!and)(?<!in)(?:(?:[’'`´-]\s?)|\s)
        )?   ## The optional surname prefix:
                                                                 ## 1 or 2, 2-3 character prefixes before the surname (e.g. 'van','de')

        (?!%(invalid_surnames)s)                                 ## Invalid surnames to avoid
        [A-Z]\w{2,20}(?:[\-’'`´]\w{2,20})?                       ## The surname, which must start with an upper case character (single hyphen allowed)

        \s*[,.\s]\s*                                             ## The space between the surname and its initials

        (?<!Volume\s)                                            ## Initials
        [A-Z](?:\s*[.'’\s-]{1,2}\s*[A-Z]){0,4}\.{0,2}            ##

                                                                 ## Either a comma or an 'and' MUST be present ... OR an end of line marker
                                                                 ## (maybe some space's between authors)
                                                                 ## Uses positive lookahead assertion
        (?:               # Look for editor notation after the author group...
            \s*,?\s*      # Eventually a coma/space
            %(ed)s
        )?
    )""" % {
        'invalid_prefixes': '|'.join(invalid_prefixes),
        'invalid_surnames': '|'.join(invalid_surnames),
        'ed'              : re_ed_notation,
        'numeration'      : append_num_re,
    }


invalid_surnames = (
    'Supergravity', 'Collaboration', 'Theoretical', 'Appendix'
)
invalid_prefixes = (
    'at',
)


def make_auth_regex_str(etal, initial_surname_author=None, surname_initial_author=None):
    """
        Returns a regular expression to be used to identify groups of author names in a citation.
        This method contains patterns for default authors, so no arguments are needed for the
        most reliable form of matching.

        The returned author pattern is capable of:
        1. Identifying single authors, with at least one initial, of the form:
        'Initial. [surname prefix...] Surname'

        2. Identifying multiple authors, each with at least one initial, of the form:
        'Initial. [surname prefix...] Surname, [and] [Initial. [surname prefix...] Surname ... ]'
        ***(Note that a full stop, hyphen or apostrophe after each initial is
        absolutely vital in identifying authors for both of these above methods.
        Initials must also be uppercase.)***

        3. Capture 'et al' statements at the end of author groups (allows for authors with et al
        to be processed differently from 'standard' authors)

        4. Identifying a single author surname name positioned before the phrase 'et al',
        with no initials: 'Surname et al'

        5. Identifying two author surname name positioned before the phrase 'et al',
        with no initials, but separated by 'and' or '&': 'Surname [and|&] Surname et al'

        6. Identifying authors of the form:
        'Surname Initials, Initials Surname [Initials Surname]...'. Some authors choose
        to represent the most important cited author (in a list of authors) by listing first
        their surname, and then their initials. Since this form has little distinguishing
        characteristics which could be used to create a reliable a pattern, at least one
        standard author must be present after it in order to improve the accuracy.

        7. Capture editor notation, of which can take many forms e.g.
        'eds. editors. edited by. etc.'. Authors captured in this way can be treated as
        'editor groups', and hence processed differently if needed from standard authors

        @param etal: (string) The regular expression used to identify 'etal' notation
        @param author: (string) An optional argument, which replaces the default author
        regex used to identify author groups (initials, surnames... etc)

        @return: (string) The full author group identification regex, which will:
        - detect groups of authors in a range of formats, e.g.:
            C. Hayward, V van Edwards, M. J. Woodbridge, and L. Kelloggs et al.,
        - detect whether the author group has been marked up as editors of the doc.
            (therefore they will NOT be marked up as authors) e.g.:
            ed. C Hayward | (ed) V van Edwards  | ed by, M. J. Woodbridge and V van Edwards
            | L. Kelloggs (editors) | M. Jackson (eds.) | ...
        -detect a maximum of two surnames only if the surname(s) is followed by 'et al'
         (must be separated by 'and' if there are two), e.g.:
            Amaldi et al., | Hayward and Yellow et al.,
    """
    if not initial_surname_author:
        ## Standard author, with a maximum of 6 initials, and a surname.
        ## The Initials MUST be uppercase, and MUST have at least a dot, hypen or apostrophe between them.
        initial_surname_author = get_initial_surname_author_pattern()

    if not surname_initial_author:
        ## The author name of the form: 'surname initial(s)'
        ## This is sometimes the represention of the first author found inside an author group.
        ## This author pattern is only used to find a maximum of ONE author inside an author group.
        ## Authors of this form MUST have either a comma after the initials, or an 'and',
        ## which denotes the presence of other authors in the author group.
        surname_initial_author = get_surname_initial_author_pattern()

    ## Pattern used to locate a GROUP of author names in a reference
    ## The format of an author can take many forms:
    ## J. Bloggs, W.-H. Smith, D. De Samuel, G.L. Bayetian, C. Hayward et al.,
    ## (the use of 'et. al' is a giveaway that the preceeding
    ## text was indeed an author name)
    ## This will also match authors which seem to be labeled as editors (with the phrase 'ed.')
    ## In which case, the author will be thrown away later on.
    ## The regex returned has around 100 named groups already (max), so any new groups must be
    ## started using '?:'

    return ur"""
     (?:^|\s+|\()                                                     ## Must be the start of the line, or a space (or an opening bracket in very few cases)
     (?P<es>                                                        ## Look for editor notation before the author
      (?:(?:(?:[Ee][Dd]s?|[Ee]dited|[Ee]ditors?)((?:\.\s?)|(?:\.?\s)))                    ## 'eds?. '     | 'ed '      | 'ed.'
      |(?:(?:[Ee][Dd]s?|[Ee]dited|[Ee]ditions?)(?:(?:\.\s?)|(?:\.?\s))by(?:\s|([:,]\s)))    ## 'eds?. by, ' | 'ed. by: ' | 'ed by '  | 'ed. by '| 'ed by: '
      |(?:\(\s?([Ee][Dd]s?|[Ee]dited|[Ee]ditors?)(?:(?:\.\s?)|(?:\.?\s))?\)))           ## '( eds?. )'  | '(ed.)'    | '(ed )'   | '( ed )' | '(ed)'
     )?

                                                                    ## **** (1) , one or two surnames which MUST end with 'et al' (e.g. Amaldi et al.,)
   (?P<author_names>
       (?:
         (?:[A-Z](?:\s*[.'’-]{1,2}\s*[A-Z]){0,4}[.\s]\s*)?          ## Initials
         [A-Z][^0-9_\.\s]{2,20}(?:(?:[,\.]\s*)|(?:[,\.]?\s+))       ## Surname
         (?:[A-Z](?:\s*[.'’-]{1,2}\s*[A-Z]){0,4}[.\s]\s*)?          ## Initials
         (?P<multi_surs>
          (?:(?:[Aa][Nn][Dd]|\&)\s+)                                ## Maybe 'and' or '&' tied with another name
          [A-Z][^0-9_\.\s]{3,20}(?:(?:[,\.]\s*)|(?:[,\.]?\s+))      ## More surnames
          (?:[A-Z](?:[ -][A-Z])?\s+)?                               ## with initials
         )?
         (?:                     # Look for editor notation after the author group...
             \s*[,\s]?\s*        # Eventually a coma/space
             %(ed)s
         )?
         (?P<et2>
            %(etal)s                                                ## et al, MUST BE PRESENT however, for this author form
         )
         (?:                     # Look for editor notation after the author group...
             \s*[,\s]?\s*        # Eventually a coma/space
             %(ed)s
         )?
       ) |

        (?:
                                                                    ## **** (2) , The standard author form.. (e.g. J. Bloggs)
                                                                    ## This author form can either start with a normal 'initial surname' author,
                                                                    ## or it can begin with a single 'surname initial' author

            (?:                                                     ## The first author in the 'author group'
               %(i_s_author)s |
               (?P<sur_initial_auth>%(s_i_author)s)
            )

            (?P<multi_auth>
                (?:                                                 ## Then 0 or more author names
                    \s*[,\s]\s*
                    (?:
                        %(i_s_author)s | %(s_i_author)s
                    )
                )*

                (?:                                                 ## Maybe 'and' or '&' tied with another name
                    (?:
                        \s*[,\s]\s*                                 ## handle "J. Dan, and H. Pon"
                        (?:[Aa][Nn][DdsS]|\&)
                        \s+
                    )
                    (?P<mult_auth_sub>
                        %(i_s_author)s | %(s_i_author)s
                    )
                )?
             )
             (?P<et>            # 'et al' need not be present for either of
                \s*[,\s]\s*
                %(etal)s        # 'initial surname' or 'surname initial' authors
             )?
        )
    )
    (?P<ee>
        \s*[,\s]\s*
        \(?
        (?:[Ee][Dd]s|[Ee]ditors)\.?
        \)?
        [\.\,]{0,2}
    )?
    # End of all author name patterns

    \)?                # A possible closing bracket to finish the author group
    (?=[\s,.;])        # Consolidate by checking we are not partially matching
                       # something else

    """ % { 'etal'       : etal,
            'i_s_author' : initial_surname_author,
            's_i_author' : surname_initial_author,
            'ed'         : re_ed_notation }

## Finding an et. al, before author names indicates a bad match!!!
## I.e. could be a title match... ignore it
etal_matches = (
    u' et al.,',
    u' et. al.,',
    u' et. al.',
    u' et.al.,',
    u' et al.',
    u' et al',
)

# Editor notation: 'eds?.' | 'ed.' | 'ed'
re_ed_text = ur"(?:[Ee][Dd]|[Ee]dited|[Ee]ditor)\.?"
re_ed_notation = ur"""
    (?:
        \(?
        %(text)s
        \s?
        \)?
        [\.\,]{0,2}
    )""" % {'text': re_ed_text}

## Standard et al ('and others') pattern for author recognition
re_etal = ur"""[Ee][Tt](?:(?:(?:,|\.)\s*)|(?:(?:,|\.)?\s+))[Aa][Ll][,\.]?[,\.]?"""

## The pattern used to identify authors inside references
re_auth = (re.compile(make_auth_regex_str(re_etal), re.VERBOSE|re.UNICODE))

## Given an Auth hit, some misc text, and then another Auth hit straight after,
## (OR a bad_and was found)
## check the entire misc text to see if is 'looks' like an author group, which didn't match
## as a normal author. In which case, append it to the single author group.
## PLEASE use this pattern only against space stripped text.
## IF a bad_and was found (from above).. do re.search using this pattern
## ELIF an auth-misc-auth combo was hit, do re.match using this pattern
re_weaker_author = ur"""
      ## look closely for initials, and less closely at the last name.
      (?:([A-Z]((\.\s?)|(\.?\s+)|(\-))){1,5}
      (?:[^\s_<>0-9]+(?:(?:[,\.]\s*)|(?:[,\.]?\s+)))+)"""

## End of line MUST match, since the next string is definitely a portion of an author group (append '$')
re_auth_near_miss = re.compile(make_auth_regex_str(
    re_etal, "(" + re_weaker_author + ")+$"), re.VERBOSE|re.UNICODE)

## Used as a weak mechanism to classify possible authors above identified affiliations
## (start) Firstname SurnamePrefix Surname (end)
re_ambig_auth = re.compile(u"^\s*[A-Z][^\s_<>0-9]+\s+([^\s_<>0-9]{1,3}\.?\s+)?[A-Z][^\s_<>0-9]+\s*$", \
                           re.UNICODE)

## Obtain the compiled expression which includes the proper author numeration
## (The pattern used to identify authors of papers)
## This pattern will match groups of authors, from the start of the line
re_auth_with_number = re.compile(make_auth_regex_str(
        re_etal,
        get_initial_surname_author_pattern(incl_numeration=True),
        get_surname_initial_author_pattern(incl_numeration=True)
    ), re.VERBOSE | re.UNICODE)

## Used to obtain authors chained by connectives across multiple lines
re_comma_or_and_at_start = re.compile("^(,|((,\s*)?[Aa][Nn][Dd]|&))\s", re.UNICODE)


def make_extra_author_regex_str():
    """ From the authors knowledge-base, construct a single regex holding the or'd possibilities of patterns
    which should be included in $h subfields. The word 'Collaboration' is also converted to 'Coll', and
    used in finding matches. Letter case is not considered during the search.
    @return: (string) The single pattern built from each line in the author knowledge base.
    """
    def add_to_auth_list(s):
        """ Strip the line, replace spaces with '\s' and append 'the' to the start
        and 's' to the end. Add the prepared line to the list of extra kb authors."""
        s = u"(?:the\s)?" + s.strip().replace(u' ', u'\s') + u"s?"
        auths.append(s)

    ## Build the 'or'd regular expression of the author lines in the author knowledge base
    auths = []
    fpath = CFG_REFEXTRACT_KBS['collaborations']

    try:
        fh = open(fpath, "r")
    except IOError:
        ## problem opening KB for reading, or problem while reading from it:
        emsg = """Error: Could not build knowledge base containing """ \
               """author patterns - failed """ \
               """to read from KB %(kb)s.\n""" \
               % { 'kb' : fpath }
        write_message(emsg, sys.stderr, verbose=0)
        halt(err=IOError, msg="Error: Unable to open author kb '%s'" % fpath, exit_code=1)

    for line_num, rawline in enumerate(fh):
        try:
            rawline = rawline.decode("utf-8")
        except UnicodeError:
            write_message("*** Unicode problems in %s for line %d" \
                             % (fpath, line_num), sys.stderr, verbose=0)
            halt(err=UnicodeError, \
                 msg="Error: Unable to parse author kb (line: %s)" % str(line_num), exit_code=1)
        if rawline.strip() and rawline[0].strip() != '#':
            add_to_auth_list(rawline)
            ## Shorten collaboration to 'coll'
            if rawline.lower().endswith('collaboration\n'):
                coll_version = rawline[:rawline.lower().find(u'collaboration\n')] + u"coll[\.\,]"
                add_to_auth_list(coll_version.strip().replace(' ', '\s') + u"s?")

    author_match_re = ""
    if len(auths) > 0:
        author_match_re = u'|'.join([u"(?:" + a + u")" for a in auths])
        author_match_re = ur"(?:(?:[\(\"]?(?P<extra_auth>" + \
            author_match_re + ur")[\)\"]?[\,\.]?\s?(?:and\s)?)+)"

    return author_match_re

## Create the regular expression used to find user-specified 'extra' authors
## (letter case is not concidered when matching)
re_extra_auth = re.compile(make_extra_author_regex_str(), re.IGNORECASE)


def get_single_and_extra_author_pattern():
    """Generates a simple, one-hit-only, author name pattern, matching just one author
    name, but ALSO INCLUDING author names generated from the knowledge base. The author
    patterns are the same ones used inside the main 'author group' pattern generator.
    This function is used not for reference extraction, but for author extraction.
    @return: (string) the union of the built-in author pattern, with the kb defined
    patterns."""
    return get_single_author_pattern() + "|" + make_extra_author_regex_str()


def get_single_author_pattern():
    """Generates a simple, one-hit-only, author name pattern, matching just one author
    name in either of the 'S I' or 'I S' formats. The author patterns are the same
    ones used inside the main 'author group' pattern generator. This function is used
    not for reference extraction, but for author extraction. Numeration is appended
    to author patterns by default.
    @return (string): Just the author name pattern designed to identify single author names
    in both SI and IS formats. (NO 'et al', editors, 'and'... matching)
    @return: (string) the union of 'initial surname' and 'surname initial'
    authors"""
    return "(?:"+ get_initial_surname_author_pattern(incl_numeration=True) + \
           "|" + get_surname_initial_author_pattern(incl_numeration=True) + ")"


## Targets single author names
re_single_author_pattern = re.compile(get_single_and_extra_author_pattern(), re.VERBOSE)
