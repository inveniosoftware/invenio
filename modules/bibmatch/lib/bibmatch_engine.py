## This file is part of Invenio.
## Copyright (C) 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""BibMatch - tool to match records with database content of an Invenio instance,
either locally or remotely through invenio_connector."""

__revision__ = "$Id$"

import sys
if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set #for "&" intersection
    # pylint: enable=W0622

import os
import getopt
import re
from tempfile import mkstemp
from time import sleep

from invenio.config import CFG_SITE_URL, CFG_BIBMATCH_FUZZY_WORDLIMITS, \
                           CFG_BIBMATCH_QUERY_TEMPLATES, \
                           CFG_BIBMATCH_FUZZY_EMPTY_RESULT_LIMIT, \
                           CFG_BIBMATCH_LOCAL_SLEEPTIME, \
                           CFG_BIBMATCH_REMOTE_SLEEPTIME
from invenio.invenio_connector import InvenioConnector
from invenio.bibrecord import create_records, \
    record_get_field_values, record_xml_output, record_modify_controlfield, \
    record_has_field, record_add_field
from invenio import bibconvert
from invenio.search_engine import get_fieldcodes
from invenio.search_engine_query_parser import SearchQueryParenthesisedParser
from invenio.dbquery import run_sql
from invenio.textmarc2xmlmarc import transform_file
from invenio.xmlmarc2textmarc import get_sysno_from_record, create_marc_record

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

re_querystring = re.compile("\[(.+?)\]")
re_valid_tag = re.compile("^[0-9]{3}[a-zA-Z0-9_%]{0,3}$")

def usage():
    """Print help"""

    print >> sys.stderr, \
    """ BibMatch - match bibliographic data against database, either locally or remotely
 Usage: %s [options] [QUERY]

 Options:

 Output:

 -0 --print-new (default) print unmatched in stdout
 -1 --print-match print matched records in stdout
 -2 --print-ambiguous print records that match more than 1 existing records
 -3 --print-fuzzy print records that match the longest words in existing records

 -b --batch-output=(filename). filename.new will be new records, filename.matched will be matched,
      filename.ambiguous will be ambiguous, filename.fuzzy will be fuzzy match
 -t --text-marc-output transform the output to text-marc format instead of the default MARCXML

 Simple query:

 -q --query-string=(search-query/predefined-query) See "Querystring"-section below.
 -f --field=(field)

 General options:

 -n   --noprocess          Do not print records in stdout.
 -i,  --input              use a named file instead of stdin for input
 -v,  --verbose=LEVEL      verbose level (from 0 to 9, default 1)
 -r,  --remote=URL         match against a remote Invenio installation (Full URL, no trailing '/')
                           Beware: Only searches public records attached to home collection
 -a,  --alter-recid        The recid (controlfield 001) of matched or fuzzy matched records in
                           output will be replaced by the 001 value of the matched record.
                           Note: Useful if you want to replace matched records using BibUpload.
 -c,  --clean              clean queries before searching
 -h,  --help               print this help and exit
 -V,  --version            print version information and exit

 Advanced options:

 -c --config=(config-filename)
 -m --mode=(a|e|o|p|r) perform an advanced search using special search mode.
    Where mode is:
      "a" all of the words,
      "o" any of the words,
      "e" exact phrase,
      "p" partial phrase,
      "r" regular expression.

 -o --operator(a|o) used to concatenate identical fields in search query (i.e. several report-numbers)
    Where operator is:
      "a" boolean AND (default)
      "o" boolean OR

 QUERYSTRINGS
     Querystrings determine which type of query/strategy to use when searching for the
     matching records in the database.

   Predefined querystrings:

     There are some predefined querystrings available:

     title             - standard title search. (i.e. "this is a title") (default)
     title-author      - title and author search (i.e. "this is a title AND Lastname, F")
     reportnumber      - reportnumber search (i.e. reportnumber:REP-NO-123).

     You can also add your own predefined querystrings inside invenio.conf file.

     You can structure your query in different ways:

     * Old-style: fieldnames separated by '||' (conforms with earlier BibMatch versions):
       -q "773__p||100__a"

     * New-style: Invenio query syntax with "bracket syntax":
       -q "773__p:\"[773__p]\" 100__a:[100__a]"

     Depending on the structure of the query, it will fetch associated values from each record and put it into
     the final search query. i.e in the above example it will put journal-title from 773__p.

     When more then one value/datafield is found, i.e. when looking for 700__a (additional authors),
     several queries will be put together to make sure all combinations of values are accounted for.
     The queries are separated with given operator (-o, --operator) value.

     Note: You can add more then one query to a search, just give more (-q, --query-string) arguments.
     The results of all queries will be combined when matching.

   BibConvert formats:

     Another option to further improve your matching strategy is to use BibConvert formats. By using the formats
     available by BibConvert you can change the values from the retrieved record-fields.

     i.e. using WORDS(1,R) will only return the first (1) word from the right (R). This can be very useful when
     adjusting your matching parameters to better match the content. For example only getting authors last-name
     instead of full-name.

     You can use these formats directly in the querystrings (indicated by '::'):

     * Old-style: -q "100__a::WORDS(1,R)::DOWN()"
       This query will take first word from the right from 100__a and also convert it to lower-case.

     * New-style: -q "100__a:[100__a::WORDS(1,R)::DOWN()]"

     See BibConvert documentation for a more detailed explanation of formats.

   Predefined fields:

     In addition to specifying distinct MARC fields in the querystrings you can use predefined
     fields as configured in the LOCAL(!) Invenio system. These fields will then be mapped to one
     or more fieldtags to be retrieved from input records.

     Common predefined fields used in querystrings: (for Invenio demo site, your fields may vary!)

     'abstract', 'affiliation', 'anyfield', 'author', 'coden', 'collaboration',
     'collection', 'datecreated', 'datemodified', 'division', 'exactauthor',
     'experiment', 'fulltext', 'isbn', 'issn', 'journal', 'keyword', 'recid',
     'reference', 'reportnumber', 'subject', 'title', 'year'

 Examples:

 $ bibmatch [options] < input.xml > unmatched.xml
 $ bibmatch -b out -n < input.xml
 $ bibmatch -a -1 < input.xml > modified_match.xml

 $ bibmatch --field=title < input.xml
 $ bibmatch --field=245__a --mode=a < input.xml

 $ bibmatch --print-ambiguous -q title-author < input.xml > ambigmatched.xml
 $ bibmatch -q "980:Thesis 773__p:\"[773__p]\" 100__a:[100__a]" -r "http://inspirebeta.net" < input.xml
    """ % (sys.argv[0],)
    sys.exit(1)

    return

class Querystring:
    """
    Holds the information about a querystring.
    The object contains lists of fields, formats and queries which generates search queries.

    self.fields    is a dict of found field-values {"tag": [list of found field-values]}
    self.formats   is a dict of found BibConvert formats {"tag": [list of found format-values]}
    self.pattern   contains the original search string
    self.query     contains the generated query

    To populate the Querystring instance with values and search string structure,
    call create_query(..) with BibRecord structure and a query-string to populate with retrieved values.

    Example: The template "title:[245__a]" will retrieve the value from subfield 245__a in
             given record. If any BibConvert formats are specified for this field, these will
             be applied.
    """
    def __init__(self, operator="and", clean=False):
        """
        Creates Querystring instance.

        @param operator: operator used to concatenate several queries
        @type operator: str

        @param clean: indicates if queries should be sanitized
        @type clean: bool
        """
        self.fields = {}
        self.operator = " %s " % (operator,)
        self.pattern = ""
        self.query = ""
        self.clean = clean
        self.formats = {}

    def create_query(self, record, qrystr="[title]"):
        """
        Main method that parses and generates a search query from
        given query-string structure and record data. Returns the
        resulting query-string and completeness determination as a tuple.

        @param record: bibrecord to retrive field-values from
        @type record: dict

        @param qrystr: proper query string template. (i.e. title:[245__a])
                       defaults to: [title]
        @type qrystr: str

        @return: (query-string, complete flag)
        @rtype: tuple
        """
        if qrystr == "":
            qrystr = "[title]"
        if "||" in qrystr or not "[" in qrystr:
            # Assume old style query-strings
            qrystr = self._convert_qrystr(qrystr)

        # FIXME: Convert to lower case, we do this to account for fuzzy_parser
        # which treats everything lower-case, and may cause KeyError when
        # retrieving data from the self.fields dict.
        # Also BibConvert formats are currently case sensitive.
        self.pattern = qrystr.lower()
        self.fields = {}
        complete = True
        fieldtags_found = []
        # Find all potential references to record tag values and
        # add to fields-dict as a list of values using fieldname as key
        for field_reference in re_querystring.findall(qrystr):
            # First we see if there is any special formats for this field_reference
            # This is done before transforming to lower case, as BibConvert formats
            # are case-sensitive
            fieldname = self._extract_formats(field_reference)
            self.pattern = self.pattern.replace("[%s]" % (field_reference.lower(),), "[%s]" % (fieldname,))

            # Find proper MARC tag(s) for the fieldname
            tag_list = get_field_tags_from_fieldname(fieldname)
            if len(tag_list) == 0:
                tag_list = [fieldname]
            for field in tag_list:
                # Check if it is really a reference to a tag to not confuse with e.g. regex syntax
                if re_valid_tag.match(field) != None:
                    tag = field[0:3]
                    ind1 = field[3:4]
                    ind2 = field[4:5]
                    code = field[5:6]
                    if ind1 == "_" or ind1 == "%":
                        ind1 = ""
                    if ind2 == "_" or ind2 == "%":
                        ind2 = ""
                    value_list = record_get_field_values(record, tag, ind1, ind2, code)
                    for value in value_list:
                        if value.strip() != "":
                            # Apply formats if applicable
                            for aformat in self.formats.get(fieldname, []):
                                value = bibconvert.FormatField(value, aformat)
                            self.fields.setdefault(fieldname, []).append((fieldname, value))
                    # Add fieldname to found tags, so we can check completeness later
                    fieldtags_found.append(fieldname)

        # Is the query deemed complete? i.e. did we find data for all field-name references
        complete = not bool([n for n in fieldtags_found if n not in self.fields])

        # Now determine the Cartesian product over all found values,
        # then iterate over each combination to generate proper query
        all_queries = []
        query_tuples = cproduct(self.fields.values())
        for query in query_tuples:
            new_query = self.pattern
            for fieldname, value in query:
                new_query = new_query.replace("[%s]" % (fieldname,), value)
            all_queries.append(new_query)

        # Finally we concatenate all queries into one, delimited by chosen operator
        self.query = self.operator.join(set(all_queries))
        if not complete:
            # Clean away field-name references not found
            for fieldtag in fieldtags_found:
                self.query = self.query.replace("[%s]" % (fieldtag,), "")

        # Clean query?
        if self.clean:
            self._clean_query()
        return self.query, complete

    def fuzzy_queries(self):
        """
        Returns a list of queries that are built more 'fuzzily' using the main query as base.
        The list returned also contains the current operator in context, so each query is a tuple
        of (operator, query).

        @return: tuple of (operator, query)
        @rtype: (str, str)
        """
        fuzzy_query_list = []
        parser = SearchQueryParenthesisedParser()
        query_parts = parser.parse_query(self.pattern)
        # Go through every expression in the query and generate fuzzy searches
        for i in xrange(0, len(query_parts) - 1, 2):
            current_operator = query_parts[i]
            current_pattern = query_parts[i + 1]
            fieldname_list = re_querystring.findall(current_pattern)
            if fieldname_list == []:
                # No reference to record value, add query 'as is'
                fuzzy_query_list.append((current_operator, current_pattern))
            else:
                for fieldname in re_querystring.findall(current_pattern):
                    for dummy, value in self.fields.get(fieldname, []):
                        new_query = []
                        # Grab the x longest words in the string and perform boolean AND for each word
                        # x is determined by the configuration dict and is tag-based. Defaults to 3 words
                        word_list = get_longest_words(value, limit=CFG_BIBMATCH_FUZZY_WORDLIMITS.get(fieldname, 3))
                        for word in word_list:
                            # Create fuzzy query with key + word, including any surrounding elements like quotes, regexp etc.
                            new_query.append(current_pattern.replace("[%s]" % (fieldname,), word))
                        fuzzy_query_list.append((current_operator, " ".join(new_query)))
        # Return a list of unique queries
        return list(set(fuzzy_query_list))

    def _clean_query(self):
        """
        This function will remove erroneous characters and combinations from
        a the generated search query that might cause problems when searching.

        @return: cleaned query
        @rtype: str
        """
        #FIXME: Extend cleaning to account for encodings and LaTeX symbols
        query = self.query.replace("''", "")
        query = query.replace('""', "")
        return query

    def _convert_qrystr(self, qrystr):
        """
        Converts old-style query-strings into new-style.
        """
        fields = qrystr.split("||")
        converted_query = []
        for field in fields:
            converted_query.append("[%s]" % (field,))
        return self.operator.join(converted_query)

    def _extract_formats(self, field_reference):
        """
        Looks for BibConvert formats within query-strings and adds to
        the instance. Formats are defined by one or more '::' followed
        by a format keyword which is defined in BibConvert FormatField()
        method.

        Returns the field_reference reference, with formats stripped.
        """
        field_parts = field_reference.split("::")
        for aformat in field_parts[1:]:
            self.formats.setdefault(field_parts[0], []).append(aformat)
        return field_parts[0]

def get_field_tags_from_fieldname(field):
    """
    Gets list of field 'field' for the record with 'sysno' system number from the database.
    """
    query = "select tag.value from tag left join field_tag on tag.id=field_tag.id_tag " \
            + "left join field on field_tag.id_field=field.id where field.code='%s'" % (field,)
    out = []
    res = run_sql(query)
    for row in res:
        out.append(row[0])
    return out

def cproduct(args):
    """
    Returns the Cartesian product of passed arguments as a list of tuples.
    '12','34' -> ('1', '3'), ('1', '4'), ('2', '3'), ('2', '4')

    @param args: iterable with elements to compute
    @type args: iterable

    @return list containing tuples for each computed combination
    @rtype list of tuples

    Based on http://docs.python.org/library/itertools.html#itertools.product
    """
    values = map(tuple, args)
    result = [[]]
    for value in values:
        result = [x + [y] for x in result for y in value]
    return [tuple(res) for res in result]

def bylen(word1, word2):
    """ Sort comparison method that compares by length """
    return len(word1) - len(word2)

def get_longest_words(wstr, limit=5):
    """
    Select the longest words for matching. It selects the longest words from
    the string, according to a given limit of words. By default the 5 longest word are selected

    @param wstr: string to extract the longest words from
    @type wstr: str

    @param limit: maximum number of words extracted
    @type limit: int

    @return: list of long words
    @rtype: list
    """
    words = []
    if wstr:
        words = wstr.split()
        words.sort(cmp=bylen)
        words.reverse()
        words = words[:limit]
    return words

def add_recid(record, recid):
    """
    Add a given record-id to the record as $$001 controlfield. If an 001 field already
    exists it will be replaced.

    @param record: the record to retrive field-values from
    @type record: a bibrecord instance

    @param recid: record-id to be added
    @type recid: int
    """
    if record_has_field(record, '001'):
        record_modify_controlfield(record, '001', \
                                   controlfield_value=str(recid), \
                                   field_position_global=1)
    else:
        record_add_field(record, '001', controlfield_value=str(recid))

def match_result_output(recID_list, server_url, query, matchmode="no match"):
    """
    Generates result as XML comments from passed record and matching parameters.

    @param record: record tuple containing results
    @type record: list

    @param server_url: url to the server the matching has been performed
    @type server_url: str

    @param qrystrs: Querystrings
    @type qrystrs: list of object

    @param matchmode: matching type
    @type matchmode: str

    @rtype str
    @return XML result string
    """
    result = []
    for recID in recID_list:
        result.append("<!-- BibMatch-Matching-Found: %s/record/%s -->" \
                             % (server_url, recID))
    result.append("<!-- BibMatch-Matching-Mode: %s -->" \
                              % (matchmode,))
    result.append("<!-- BibMatch-Matching-Criteria: %s -->\n" \
                              % (query,))
    return "\n".join(result)

def match_records(records, qrystrs=None, search_mode=None, operator="and", verbose=1, \
                  server_url=CFG_SITE_URL, modify=0, sleeptime=CFG_BIBMATCH_LOCAL_SLEEPTIME, clean=False):
    """
    Match passed records with existing records on a local or remote Invenio
    installation. Returns which records are new (no match), which are matched,
    which are ambiguous and which are fuzzy-matched. A formatted result of each
    records matching are appended to each record tuple:
    (record, status_code, list_of_errors, result)

    @param records: records to analyze
    @type records: list of records

    @param qrystrs: list of tuples (field, querystring)
    @type qrystrs: list

    @param search_mode: if mode is given, the search will perform an advanced query using
                        the desired mode. Otherwise 'simple search' is used.
    @type search_mode: str

    @param operator: operator used to concatenate values of fields occurring more then once.
                     Valid types are: AND, OR. Defaults to AND.
    @type operator: str

    @param verbose: be loud
    @type verbose: int

    @param server_url: which server to search on. Local installation by default
    @type server_url: str

    @param modify: output modified records of matches
    @type modify: int

    @param sleeptime: amount of time to wait between each query
    @type sleeptime: float

    @rtype: list of lists
    @return an array of arrays of records, like this [newrecs,matchedrecs,
                                                      ambiguousrecs,fuzzyrecs]
    """
    server = InvenioConnector(server_url)

    newrecs = []
    matchedrecs = []
    ambiguousrecs = []
    fuzzyrecs = []

    ## Go through each record and try to find matches using defined querystrings
    record_counter = 0
    querystring = Querystring(operator, clean=clean)
    for rec in records:
        record_counter += 1
        if (verbose > 1):
            sys.stderr.write("\n Processing record: #%d .." % (record_counter,))

        # At least one (field, querystring) tuple is needed for default search query
        if not qrystrs:
            qrystrs = [("", "")]

        # Temporary store result(s) for each record
        matched_results = []
        ambiguous_results = []
        fuzzy_results = []
        # Go through each querystring, trying to find a matching record
        # Stops on first valid match, if no exact-match we continue with fuzzy match
        for field, qrystr in qrystrs:
            query, complete = querystring.create_query(rec[0], qrystr)
            if query == "":
                if (verbose > 1):
                    sys.stderr.write("\nEmpty query. Skipping...\n")
                # Empty query, no point searching database
                continue

            if not complete:
                if (verbose > 1):
                    sys.stderr.write("\nQuery not complete. Flagged as uncertain/ambiguous...\n")

            # Determine proper search parameters
            if search_mode != None:
                search_params = dict(p1=query, f1=field, m1=search_mode, of='id')
            else:
                search_params = dict(p=query, f=field, of='id')

            ## Perform the search with retries
            result_recids = server.search_with_retry(**search_params)
            if (verbose > 8):
                if len(result_recids) > 10:
                    sys.stderr.write("\nSearching with values %s result=%s\n" %
                                 (search_params, "More then 10 results..."))
                else:
                    sys.stderr.write("\nSearching with values %s result=%s\n" %
                                 (search_params, result_recids))
            sleep(sleeptime)
            ## Check results:
            # Ambiguous match
            if len(result_recids) > 1 and len(result_recids) < 11:
                ambiguous_results.append((result_recids, query))
                if (verbose > 8):
                    sys.stderr.write("Ambiguous\n")
            # Match
            elif len(result_recids) == 1:
                if modify:
                    add_recid(rec[0], result_recids[0])
                if complete:
                    matched_results.append((result_recids, query))
                    if (verbose > 8):
                        sys.stderr.write("Match\n")
                    # This was a complete match, so let's break out to avoid fuzzy search
                    break
                else:
                    # We treat the result as ambiguous (uncertain) when query is not complete
                    ambiguous_results.append((result_recids, query))
                    if (verbose > 8):
                        sys.stderr.write("Ambiguous\n")
            # No match
            else:
                if (verbose > 8):
                    sys.stderr.write("New (no matches)\n")
        # No complete matches, lets try fuzzy matching of all the queries
        else:
            ## Fuzzy matching: Analyze all queries and perform individual searches, then intersect results.
            for field, qrystr in qrystrs:
                query, complete = querystring.create_query(rec[0], qrystr)
                if query == "":
                    if (verbose > 1):
                        sys.stderr.write("\nEmpty query. Skipping...\n")
                    # Empty query, no point searching database
                    continue
                result_hitset = None
                fuzzy_query_list = querystring.fuzzy_queries()
                empty_results = 0
                # Go through every expression in the query and generate fuzzy searches
                for current_operator, qry in fuzzy_query_list:
                    current_resultset = None
                    search_params = dict(p=qry, f=field, of='id')
                    current_resultset = server.search_with_retry(**search_params)
                    if (verbose > 8):
                        if len(current_resultset) > 10:
                            sys.stderr.write("\nSearching with values %s result=%s\n" %
                                         (search_params, "More then 10 results..."))
                        else:
                            sys.stderr.write("\nSearching with values %s result=%s\n" %
                                         (search_params, current_resultset))
                    sleep(sleeptime)
                    if current_resultset == None:
                        continue
                    if current_resultset == [] and empty_results < CFG_BIBMATCH_FUZZY_EMPTY_RESULT_LIMIT:
                        # Allows some empty results
                        empty_results += 1
                    else:
                        # Intersect results with previous results depending on current operator
                        if result_hitset == None:
                            result_hitset = current_resultset
                        if current_operator == '+':
                            result_hitset = list(set(result_hitset) & set(current_resultset))
                        elif current_operator == '-':
                            result_hitset = list(set(result_hitset) - set(current_resultset))
                        elif current_operator == '|':
                            result_hitset = list(set(result_hitset) | set(current_resultset))

                if result_hitset and len(result_hitset) < 10:
                    # This was a fuzzy match
                    query_out = " #Fuzzy# ".join([q for dummy, q in fuzzy_query_list])
                    if len(result_hitset) == 1 and complete:
                        if modify:
                            add_recid(rec[0], result_hitset[0])
                        fuzzy_results.append((result_hitset, query_out))
                        if (verbose > 8):
                            sys.stderr.write("Fuzzy: %s\n" % (result_hitset,))
                    else:
                        # We treat the result as ambiguous (uncertain) when:
                        # - query is not complete
                        # - more then one result
                        ambiguous_results.append((result_hitset, query_out))
                        if (verbose > 8):
                            sys.stderr.write("Ambiguous\n")

        ## Evaluate final results for record
        # Add matched record iff number found is equal to one, otherwise return fuzzy, ambiguous or no match
        if len(matched_results) == 1:
            results, query = matched_results[0]
            matchedrecs.append((rec[0], "<!-- BibMatch-Matching-Results: -->\n%s" % (match_result_output(results, server_url, \
                                                                                                         query, "exact-matched"))))
            if (verbose > 1):
                sys.stderr.write("Final result: match\n")
        else:
            if len(fuzzy_results) > 0:
                # Find common record-id for all fuzzy results and grab first query as "representative" query
                query = fuzzy_results[0][1]
                result_lists = []
                for res, dummy in fuzzy_results:
                    result_lists.extend(res)
                results = set([res for res in result_lists])
                fuzzyrecs.append((rec[0], "<!-- BibMatch-Matching-Results: -->\n%s" % (match_result_output(results, server_url, \
                                                                                            query, "fuzzy-matched"),)))
                if (verbose > 1):
                    sys.stderr.write("Final result: fuzzy\n")
            elif len(ambiguous_results) > 0:
                # Find common record-id for all ambiguous results and grab first query as "representative" query
                query = ambiguous_results[0][1]
                result_lists = []
                for res, dummy in ambiguous_results:
                    result_lists.extend(res)
                results = set([res for res in result_lists])
                ambiguousrecs.append((rec[0], "<!-- BibMatch-Matching-Results: -->\n%s" % (match_result_output(results, server_url, \
                                                                                            query, "ambiguous-matched"),)))
                if (verbose > 1):
                    sys.stderr.write("Final result: ambiguous\n")
            else:
                newrecs.append((rec[0], "<!-- BibMatch-Matching-Results: -->\n%s" % (match_result_output([], server_url, str(qrystrs)),)))
                if (verbose > 1):
                    sys.stderr.write("Final result: new\n")
    return [newrecs, matchedrecs, ambiguousrecs, fuzzyrecs]

def transform_input_to_marcxml(filename=None, file_input=""):
    """
    Takes the filename or input of text-marc and transforms it
    to MARCXML.
    """
    if not filename:
        # Create temporary file to read from
        tmp_fd, filename = mkstemp()
        os.write(tmp_fd, file_input)
        os.close(tmp_fd)
    try:
        # Redirect output, transform, restore old references
        old_stdout = sys.stdout
        new_stdout = StringIO()
        sys.stdout = new_stdout

        transform_file(filename)
    finally:
        sys.stdout = old_stdout
    return new_stdout.getvalue()

def main():
    """
    Record matches database content when defined search gives
    exactly one record in the result set. By default the match is
    done on the title field.
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "0123hVm:fq:c:nv:o:b:i:r:taz",
                 [
                   "print-new",
                   "print-match",
                   "print-ambiguous",
                   "print-fuzzy",
                   "help",
                   "version",
                   "mode=",
                   "field=",
                   "query-string=",
                   "config=",
                   "no-process",
                   "verbose=",
                   "operator=",
                   "batch-output=",
                   "input=",
                   "remote=",
                   "text-marc-output",
                   "alter-recid",
                   "clean"
                 ])

    except getopt.GetoptError, e:
        usage()

    match_results = []
    qrystrs = []                              # list of query strings
    print_mode = 0                            # default match mode to print new records
    noprocess = 0                             # dump result in stdout?
    operator = "and"
    verbose = 1                               # 0..be quiet
    records = []
    batch_output = ""                         # print stuff in files
    f_input = ""                              # read from where, if param "i"
    server_url = CFG_SITE_URL                 # url to server performing search, local by default
    modify = 0                                # alter output with matched record identifiers
    textmarc_output = 0                       # output in MARC instead of MARCXML
    field = ""
    search_mode = None                        # activates a mode, uses advanced search instead of simple
    sleeptime = CFG_BIBMATCH_LOCAL_SLEEPTIME  # the amount of time to sleep between queries, changes on remote queries
    clean = False                             # should queries be sanitized?

    for opt, opt_value in opts:
        if opt in ["-0", "--print-new"]:
            print_mode = 0
        if opt in ["-1", "--print-match"]:
            print_mode = 1
        if opt in ["-2", "--print-ambiguous"]:
            print_mode = 2
        if opt in ["-3", "--print-fuzzy"]:
            print_mode = 3
        if opt in ["-n", "--no-process"]:
            noprocess = 1
        if opt in ["-h", "--help"]:
            usage()
            sys.exit(0)
        if opt in ["-V", "--version"]:
            print __revision__
            sys.exit(0)
        if opt in ["-t", "--text-marc-output"]:
            textmarc_output = 1
        if opt in ["-v", "--verbose"]:
            verbose = int(opt_value)
        if opt in ["-f", "--field"]:
            if opt_value in get_fieldcodes():
                field = opt_value
        if opt in ["-q", "--query-string"]:
            try:
                template = CFG_BIBMATCH_QUERY_TEMPLATES[opt_value]
                qrystrs.append((field, template))
            except KeyError:
                qrystrs.append((field, opt_value))
        if opt in ["-m", "--mode"]:
            search_mode = opt_value
        if opt in ["-o", "--operator"]:
            if opt_value.lower() in ["o", "or", "|"]:
                operator = "or"
            elif opt_value.lower() in ["a", "and", "&"]:
                operator = "and"
        if opt in ["-b", "--batch-output"]:
            batch_output = opt_value
        if opt in ["-i", "--input"]:
            f_input = opt_value
        if opt in ["-r", "--remote"]:
            server_url = opt_value
            sleeptime = CFG_BIBMATCH_REMOTE_SLEEPTIME
        if opt in ["-a", "--alter-recid"]:
            modify = 1
        if opt in ["-z", "--clean"]:
            clean = True
        if opt in ["-c", "--config"]:
            config_file = opt_value
            config_file_read = bibconvert.read_file(config_file, 0)
            for line in config_file_read:
                tmp = line.split("---")
                if(tmp[0] == "QRYSTR"):
                    qrystrs.append((field, tmp[1]))

    if verbose:
        sys.stderr.write("\nBibMatch: Parsing input file %s..." % (f_input,))

    read_list = []
    if not f_input:
        for line_in in sys.stdin:
            read_list.append(line_in)
    else:
        f = open(f_input)
        for line_in in f:
            read_list.append(line_in)
        f.close()
    file_read = "".join(read_list)

    # Detect input type
    if not file_read.startswith('<'):
        # Not xml, assume type textmarc
        file_read = transform_input_to_marcxml(f_input, file_read)

    records = create_records(file_read)

    if len(records) == 0:
        if verbose:
            sys.stderr.write("\nBibMatch: Input file contains no records.\n")
        sys.exit(0)

    if verbose:
        sys.stderr.write("read %d records" % (len(records),))
        sys.stderr.write("\nBibMatch: Matching ...")

    match_results = match_records(records,
                                  qrystrs,
                                  search_mode,
                                  operator,
                                  verbose,
                                  server_url,
                                  modify,
                                  sleeptime,
                                  clean)

    # set the output according to print..
    # 0-newrecs 1-matchedrecs 2-ambiguousrecs 3-fuzzyrecs
    recs_out = match_results[print_mode]

    if verbose:
        sys.stderr.write("\n\n Bibmatch report\n")
        sys.stderr.write("=" * 35)
        sys.stderr.write("\n New records         : %d" % (len(match_results[0]),))
        sys.stderr.write("\n Matched records     : %d" % (len(match_results[1]),))
        sys.stderr.write("\n Ambiguous records   : %d" % (len(match_results[2]),))
        sys.stderr.write("\n Fuzzy records       : %d\n" % (len(match_results[3]),))
        sys.stderr.write("=" * 35)
        sys.stderr.write("\n Total records       : %d\n" % (len(records),))

    if not noprocess:
        options = {'text-marc':1, 'aleph-marc':0}
        for record, results in recs_out:
            if textmarc_output:
                # FIXME: textmarc output does not print matching results
                sysno = get_sysno_from_record(record, options)
                print create_marc_record(record, sysno, options)
            else:
                print results
                print record_xml_output(record)

    if batch_output:
        i = 0
        options = {'text-marc':1, 'aleph-marc':0}
        outputs = ['new', 'matched', 'ambiguous', 'fuzzy']
        for result in match_results:
            filename = "%s.%s" % (batch_output, outputs[i])
            file_fd = open(filename, "w")
            for record, results in result:
                out = []
                if textmarc_output:
                    # FIXME: textmarc output does not print matching results
                    sysno = get_sysno_from_record(record, options)
                    out.append(create_marc_record(record, sysno, options))
                else:
                    out.append(results)
                    out.append(record_xml_output(record))
                file_fd.write("".join(out) + '\n')
            file_fd.close()
            i += 1
