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
import string
import os
import getopt
import re
import getpass
from tempfile import mkstemp
from time import sleep

from invenio.config import CFG_SITE_SECURE_URL, CFG_BIBMATCH_FUZZY_WORDLIMITS, \
                           CFG_BIBMATCH_QUERY_TEMPLATES, \
                           CFG_BIBMATCH_FUZZY_EMPTY_RESULT_LIMIT, \
                           CFG_BIBMATCH_LOCAL_SLEEPTIME, \
                           CFG_BIBMATCH_REMOTE_SLEEPTIME, \
                           CFG_SITE_RECORD, \
                           CFG_BIBMATCH_SEARCH_RESULT_MATCH_LIMIT
from invenio.bibmatch_config import CFG_BIBMATCH_LOGGER, \
                                    CFG_LOGFILE
from invenio.invenio_connector import InvenioConnector, \
                                      InvenioConnectorAuthError
from invenio.bibrecord import create_records, \
    record_get_field_values, record_xml_output, record_modify_controlfield, \
    record_has_field, record_add_field
from invenio import bibconvert
from invenio.search_engine import get_fieldcodes, \
    re_pattern_single_quotes, \
    re_pattern_double_quotes, \
    re_pattern_regexp_quotes, \
    re_pattern_spaces_after_colon
from invenio.search_engine_query_parser import SearchQueryParenthesisedParser
from invenio.dbquery import run_sql
from invenio.textmarc2xmlmarc import transform_file
from invenio.bibmatch_validator import validate_matches, transform_record_to_marc, \
                                       validate_tag, BibMatchValidationError
from invenio.textutils import translate_to_ascii, xml_entities_to_utf8

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

re_querystring = re.compile("\s?([^\s$]*)\[(.+?)\]([^\s$]*).*?", re.DOTALL)

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
 -z,  --clean              clean queries before searching
 --no-validation           do not perform post-match validation
 -h,  --help               print this help and exit
 -V,  --version            print version information and exit

 Advanced options:

 -m --mode=(a|e|o|p|r)     perform an advanced search using special search mode.
                             Where mode is:
                               "a" all of the words,
                               "o" any of the words,
                               "e" exact phrase,
                               "p" partial phrase,
                               "r" regular expression.

 -o --operator(a|o)        used to concatenate identical fields in search query (i.e. several report-numbers)
                             Where operator is:
                               "a" boolean AND (default)
                               "o" boolean OR

 -c --config=filename      load querystrings from a config file. Each line starting with QRYSTR will
                           be added as a query. i.e. QRYSTR --- [title] [author]

 -x --collection           only perform queries in certain collection(s).
                           Note: matching against restricted collections requires authentication.

 --user=USERNAME           username to use when connecting to Invenio instance. Useful when searching
                           restricted collections. You will be prompted for password.

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
     'collection', 'datecreated', 'datemodified', 'division', 'exactauthor', 'exactfirstauthor',
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

 $ bibmatch --collection 'Books,Articles' < input.xml
 $ bibmatch --collection 'Theses' --user admin < input.xml
    """ % (sys.argv[0],)
    sys.exit(1)

    return

class Querystring:
    """
    Holds the information about a querystring.
    The object contains lists of fields, formats and queries which generates search queries.

    self.fields    is a dict of found field-data {"tag": [list of found record data]}
    self.formats   is a dict of found BibConvert formats {"tag": [list of found format-values]}
    self.pattern   contains the original search string
    self.query     contains the generated query
    self.operator  holds the current active operator, upper-case (OR/AND)

    To populate the Querystring instance with values and search string structure,
    call create_query(..) with BibRecord structure and a query-string to populate with retrieved values.

    Example: The template "title:[245__a]" will retrieve the value from subfield 245__a in
             given record. If any BibConvert formats are specified for this field, these will
             be applied.
    """
    def __init__(self, operator="AND", clean=False, ascii_mode=False):
        """
        Creates Querystring instance.

        @param operator: operator used to concatenate several queries
        @type operator: str

        @param clean: indicates if queries should be sanitized
        @type clean: bool
        """
        self.fields = {}
        self.operator = operator.upper()
        self.pattern = ""
        self.query = ""
        self.clean = clean
        self.ascii_mode = ascii_mode
        self.formats = {}

    def create_query(self, record, qrystr="[title]"):
        """
        Main method that parses and generates a search query from
        given query-string structure and record data. Returns the
        resulting query-string and completeness determination as a tuple.

        A query is 'complete' when all found field references has a value
        in the passed record. Should a value be missing, the query is
        incomplete.

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

        # FIXME: Convert to lower case, since fuzzy_parser
        # which treats everything lower-case, and will cause problems when
        # retrieving data from the self.fields dict.
        # Also BibConvert formats are currently case sensitive, so we cannot
        # force lower-case yet.
        self.pattern = qrystr.lower()
        self.fields = {}
        # Extract referenced field-values from given record
        complete, fieldtags_found = self._extract_fieldvalues(record, qrystr)

        # If no field references are found, we exit as empty query.
        if len(self.fields) == 0:
            self.query = ""
            return self.query, False
        # Now we assemble the found values into a proper search query
        all_queries = []
        operator_delimiter = " %s " % (self.operator,)
        if self.operator == "AND":
            # We gather all the values from the self.fields and put them
            # in a list together with any prefix/suffix associated with the field.
            new_query = self.pattern
            for (field_prefix, field_reference, field_suffix), value_list in self.fields.iteritems():
                new_values = []
                for value in value_list:
                    new_values.append("%s%s%s" % (field_prefix, value, field_suffix))
                new_query = new_query.replace("%s[%s]%s" % (field_prefix, field_reference, field_suffix), \
                                              operator_delimiter.join(set(new_values)))
            all_queries = [new_query]
        else:
            # operator is OR, which means a more elaborate approach to multi-value fields
            field_tuples = []
            for key, values in self.fields.iteritems():
                field_list = []
                for value in values:
                    # We add key here to be able to associate the value later
                    field_list.append((key, value))
                field_tuples.append(field_list)
            # Grab all combinations of queries
            query_tuples = cproduct(field_tuples)
            for query in query_tuples:
                new_query = self.pattern
                for (field_prefix, field_reference, field_suffix), value in query:
                    new_query = new_query.replace("%s[%s]%s" % (field_prefix, field_reference, field_suffix), \
                                                  "%s%s%s" % (field_prefix, value, field_suffix))
                all_queries.append(new_query)
        # Finally we concatenate all unique queries into one, delimited by chosen operator
        self.query = operator_delimiter.join(set(all_queries))
        if not complete:
            # Clean away any leftover field-name references from query
            for fieldtag in fieldtags_found:
                self.query = self.query.replace("%s" % (fieldtag,), "")
        # Clean query?
        if self.clean:
            self._clean_query()
        return self.query, complete

    def fuzzy_queries(self):
        """
        Returns a list of queries that are built more 'fuzzily' using the main query as base.
        The list returned also contains the current operator in context, so each query is a tuple
        of (operator, query).

        @return: list of tuples [(operator, query), ..]
        @rtype: list [(str, str), ..]
        """
        fuzzy_query_list = []
        operator_delimiter = " %s " % (self.operator,)
        parser = SearchQueryParenthesisedParser()
        query_parts = parser.parse_query(self.pattern)
        author_query = []
        author_operator = None
        # Go through every expression in the query and generate fuzzy searches
        for i in xrange(0, len(query_parts) - 1, 2):
            current_operator = query_parts[i]
            current_pattern = query_parts[i + 1]
            fieldname_list = re_querystring.findall(current_pattern)
            if fieldname_list == []:
                # No reference to record value, add query 'as is'
                fuzzy_query_list.append((current_operator, current_pattern))
            else:
                # Each reference will be split into prefix, field-ref and suffix.
                # Example:
                # 773__p:"[773__p]" 100__a:/.*[100__a].*/ =>
                # [('773__p:"', '773__p', '"'), ('100__a:/.*', '100__a', '.*/')]
                for field_prefix, field_reference, field_suffix in fieldname_list:
                    if field_reference == '245__a':
                        new_query = []
                        for value in self.fields.get((field_prefix, field_reference, field_suffix), []):
                            # Grab the x+1 longest words in the string and perform boolean OR
                            # for all combinations of x words (boolean AND)
                            # x is determined by the configuration dict and is tag-based. Defaults to 3 words
                            word_list = get_longest_words(value, limit=CFG_BIBMATCH_FUZZY_WORDLIMITS.get(field_reference, 3)+1)
                            for i in range(len(word_list)):
                                words = list(word_list)
                                words.pop(i)
                                new_query.append("(" + current_pattern.replace("[%s]" % (field_reference,), " ".join(words)) + ")")
                            fuzzy_query_list.append((current_operator, " OR ".join(new_query)))
                    elif field_reference == '100__a':
                        for value in self.fields.get((field_prefix, field_reference, field_suffix), []):
                            author_query.append(current_pattern.replace("[%s]" % (field_reference,), value))
                            author_operator = current_operator
                    elif field_reference == '700__a':
                        for value in self.fields.get((field_prefix, field_reference, field_suffix), []):
                            # take only the first 2nd author
                            author_query.append(current_pattern.replace("[%s]" % (field_reference,), value))
                            if not author_operator:
                                author_operator = current_operator
                            break
                    # for unique idenifier (DOI, repno) fuzzy search makes no sense
                    elif field_reference == '037__a':
                        continue
                    elif field_reference == '0247_a':
                        continue
                    else:
                        new_query = []
                        for value in self.fields.get((field_prefix, field_reference, field_suffix), []):
                            # Grab the x longest words in the string and perform boolean AND for each word
                            # x is determined by the configuration dict and is tag-based. Defaults to 3 words
                            # AND can be overwritten by command line argument -o o
                            word_list = get_longest_words(value, limit=CFG_BIBMATCH_FUZZY_WORDLIMITS.get(field_reference, 3))
                            for word in word_list:
                                # Create fuzzy query with key + word, including any surrounding elements like quotes, regexp etc.
                                new_query.append(current_pattern.replace("[%s]" % (field_reference,), word))
                            fuzzy_query_list.append((current_operator, operator_delimiter.join(new_query)))
        if author_query:
            fuzzy_query_list.append((author_operator, " OR ".join(author_query)))
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

    def _extract_fieldvalues(self, record, qrystr):
        """
        Extract all the values in the given record referenced in the given query-string
        and attach them to self.fields as a list. Return boolean indicating if a query
        is complete, and a list of all field references found.

        Field references is checked to be valid MARC tag references and all values
        found are added to self.fields as a list, hashed by the full reference including
        prefix and suffix.

        If ascii_mode is enabled, the record values will be translated to its ascii
        representation.

        e.g. for the query-string: 700__a:"[700__a]"
        { ('700__a:"', '700__a', '"') : ["Ellis, J.", "Olive, K. A."]}

        Should no values be found for a field references, the query will be flagged
        as incomplete.

        @param record: bibrecord to retrive field-values from
        @type record: dict

        @param qrystr: proper query string template. (i.e. title:[245__a])
                       defaults to: [title]
        @type qrystr: str

        @return: complete flag, [field references found]
        @rtype: tuple
        """
        complete = True
        fieldtags_found = []
        # Find all potential references to record tag values and
        # add to fields-dict as a list of values using field-name tuple as key.
        #
        # Each reference will be split into prefix, field-ref and suffix.
        # Example:
        # 773__p:"[773__p]" 100__a:/.*[100__a].*/ =>
        # [('773__p:"', '773__p', '"'), ('100__a:/.*', '100__a', '.*/')]
        for field_prefix, field_reference, field_suffix in re_querystring.findall(qrystr):
            # First we see if there is any special formats for this field_reference
            # The returned value from _extract_formats is the field-name stripped from formats.
            # e.g. 245__a::SUP(NUM) => 245__a
            fieldname = self._extract_formats(field_reference)
            # We need everything in lower-case
            field_prefix = field_prefix.lower()
            field_suffix = field_suffix.lower()
            # Find proper MARC tag(s) for the stripped field-name, if fieldname is used.
            # e.g. author -> [100__a, 700__a]
            # FIXME: Local instance only!
            tag_list = get_field_tags_from_fieldname(fieldname)
            if len(tag_list) == 0:
                tag_list = [fieldname]
            for field in tag_list:
                # Check if it is really a reference to a tag to not confuse with e.g. regex syntax
                tag_structure = validate_tag(field)
                if tag_structure != None:
                    tag, ind1, ind2, code = tag_structure
                    value_list = record_get_field_values(record, tag, ind1, ind2, code)
                    if len(value_list) > 0:
                        # Apply any BibConvert formatting functions to each value
                        updated_value_list = self._apply_formats(fieldname, value_list)
                        # Also remove any errornous XML entities. I.e. &amp; -> &
                        updated_value_list = [xml_entities_to_utf8(v, skip=[]) \
                                              for v in updated_value_list]
                        if self.ascii_mode:
                            updated_value_list = translate_to_ascii(updated_value_list)
                        # Store found values linked to full field reference tuple including
                        # (prefix, field, suffix)
                        self.fields[(field_prefix,
                                     fieldname,
                                     field_suffix)] = updated_value_list
                    else:
                        # No values found. The query is deemed incomplete
                        complete = False
                    fieldtags_found.append("%s[%s]%s" % (field_prefix, fieldname, field_suffix))
        return complete, fieldtags_found

    def _extract_formats(self, field_reference):
        """
        Looks for BibConvert formats within query-strings and adds to
        the instance. Formats are defined by one or more '::' followed
        by a format keyword which is defined in BibConvert FormatField()
        method.

        The function also removes the references to formatting functions
        in the query (self.pattern)

        Returns the field_reference reference, with formats stripped.
        """
        field_parts = field_reference.split("::")
        if len(field_parts) > 1:
            # Remove any references to BibConvert functions in pattern. e.g. 245__a::SUP(PUNCT, ) -> 245__a
            # self.pattern is lower cased. Returned value is field-name stripped from formats.
            for aformat in field_parts[1:]:
                self.formats.setdefault(field_parts[0], []).append(aformat)
            self.pattern = self.pattern.replace("[%s]" % (field_reference.lower(),), "[%s]" % (field_parts[0],))
        return field_parts[0]

    def _apply_formats(self, fieldname, value_list):
        """
        Apply the current stored BibConvert formating operations for a
        field-name to the given list of strings. The list is then returned.

        @param fieldname: name of field - used as key in the formats dict
        @type fieldname: string

        @param value_list: list of strings to apply formats to
        @type value_list: list

        @return: list of values with formatting functions applied
        @rtype: list
        """
        if fieldname in self.formats:
            new_list = []
            for value in value_list:
                if value.strip() != "":
                    # Apply BibConvert formats if applicable
                    for aformat in self.formats[fieldname]:
                        value = bibconvert.FormatField(value, aformat)
                new_list.append(value)
            return new_list
        else:
            return value_list

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
        # Protect spaces within quotes
        wstr = re_pattern_single_quotes.sub(
            lambda x: "'" + string.replace(x.group(1), ' ', '__SPACE__') + "'",
            wstr)
        wstr = re_pattern_double_quotes.sub(
            lambda x: "\"" + string.replace(x.group(1), ' ', '__SPACE__') + "\"",
            wstr)
        wstr = re_pattern_regexp_quotes.sub(
            lambda x: "/" + string.replace(x.group(1), ' ', '__SPACE__') + "/",
            wstr)
        # and spaces after colon as well:
        wstr = re_pattern_spaces_after_colon.sub(
            lambda x: string.replace(x.group(1), ' ', '__SPACE__'),
            wstr)
        words = wstr.split()
        for i in range(len(words)):
            words[i] = words[i].replace('__SPACE__', ' ')
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

def match_result_output(bibmatch_recid, recID_list, server_url, query, matchmode="no match"):
    """
    Generates result as XML comments from passed record and matching parameters.

    @param bibmatch_recid: BibMatch record identifier
    @type bibmatch_recid: int

    @param recID_list: record matched with record
    @type recID_list: list

    @param server_url: url to the server the matching has been performed
    @type server_url: str

    @param query: matching query
    @type query: str

    @param matchmode: matching type
    @type matchmode: str

    @rtype str
    @return XML result string
    """
    result = ["<!-- BibMatch-Matching-Results: -->", \
              "<!-- BibMatch-Matching-Record-Identifier: %s -->" % (bibmatch_recid,)]
    for recID in recID_list:
        result.append("<!-- BibMatch-Matching-Found: %s/%s/%s -->" \
                             % (server_url, CFG_SITE_RECORD, recID))
    result.append("<!-- BibMatch-Matching-Mode: %s -->" \
                              % (matchmode,))
    result.append("<!-- BibMatch-Matching-Criteria: %s -->" \
                              % (query,))
    return "\n".join(result)

def match_records(records, qrystrs=None, search_mode=None, operator="and", \
                  verbose=1, server_url=CFG_SITE_SECURE_URL, modify=0, \
                  sleeptime=CFG_BIBMATCH_LOCAL_SLEEPTIME, \
                  clean=False, collections=[], user="", password="", \
                  fuzzy=True, validate=True, ascii_mode=False,
                  insecure_login=False):
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

    @param search_mode: if mode is given, the search will perform an advanced
                        query using the desired mode. Otherwise 'simple search'
                        is used.
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

    @param clean: should the search queries be cleaned before passed them along?
    @type clean: bool

    @param collections: list of collections to search, if specified
    @type collections: list

    @param user: username in case of authenticated search requests
    @type user: string

    @param password: password in case of authenticated search requests
    @type password: string

    @param fuzzy: True to activate fuzzy query matching step
    @type fuzzy: bool

    @param validate: True to activate match validation
    @type validate: bool

    @param ascii_mode: True to transform values to its ascii representation
    @type ascii_mode: bool

    @rtype: list of lists
    @return an array of arrays of records, like this [newrecs,matchedrecs,
                                                      ambiguousrecs,fuzzyrecs]
    """
    newrecs = []
    matchedrecs = []
    ambiguousrecs = []
    fuzzyrecs = []
    CFG_BIBMATCH_LOGGER.info("-- BibMatch starting match of %d records --" % (len(records),))
    try:
        server = InvenioConnector(server_url, user=user, password=password,
                                  insecure_login=insecure_login)
    except InvenioConnectorAuthError, error:
        if verbose > 0:
            sys.stderr.write("Authentication error when connecting to server: %s" \
                             % (str(error),))
        CFG_BIBMATCH_LOGGER.info("-- BibMatch ending match with errors (AuthError) --")
        return [newrecs, matchedrecs, ambiguousrecs, fuzzyrecs]

    ## Go through each record and try to find matches using defined querystrings
    record_counter = 0
    for record in records:
        record_counter += 1
        if (verbose > 1):
            sys.stderr.write("\n Processing record: #%d .." % (record_counter,))

        # At least one (field, querystring) tuple is needed for default search query
        if not qrystrs:
            qrystrs = [("", "")]
        CFG_BIBMATCH_LOGGER.info("Matching of record %d: Started" % (record_counter,))
        [matched_results, ambiguous_results, fuzzy_results] = match_record(bibmatch_recid=record_counter,
                                                                           record=record[0],
                                                                           server=server,
                                                                           qrystrs=qrystrs,
                                                                           search_mode=search_mode,
                                                                           operator=operator,
                                                                           verbose=verbose,
                                                                           sleeptime=sleeptime,
                                                                           clean=clean,
                                                                           collections=collections,
                                                                           fuzzy=fuzzy,
                                                                           validate=validate,
                                                                           ascii_mode=ascii_mode)

        ## Evaluate final results for record
        # Add matched record iff number found is equal to one, otherwise return fuzzy,
        # ambiguous or no match
        if len(matched_results) == 1:
            results, query = matched_results[0]
            # If one match, add it as exact match, otherwise ambiguous
            if len(results) == 1:
                if modify:
                    add_recid(record[0], results[0])
                matchedrecs.append((record[0], match_result_output(record_counter, results, server_url, \
                                                                query, "exact-matched")))
                if (verbose > 1):
                    sys.stderr.write("Final result: match - %s/record/%s\n" % (server_url, str(results[0])))
                CFG_BIBMATCH_LOGGER.info("Matching of record %d: Completed as 'match'" % (record_counter,))
            else:
                ambiguousrecs.append((record[0], match_result_output(record_counter, results, server_url, \
                                                                  query, "ambiguous-matched")))
                if (verbose > 1):
                    sys.stderr.write("Final result: ambiguous\n")
                CFG_BIBMATCH_LOGGER.info("Matching of record %d: Completed as 'ambiguous'" % (record_counter,))
        else:
            if len(fuzzy_results) > 0:
                # Find common record-id for all fuzzy results and grab first query
                # as "representative" query
                query = fuzzy_results[0][1]
                result_lists = []
                for res, dummy in fuzzy_results:
                    result_lists.extend(res)
                results = set([res for res in result_lists])
                if len(results) == 1:
                    fuzzyrecs.append((record[0], match_result_output(record_counter, results, server_url, \
                                                                     query, "fuzzy-matched")))
                    if (verbose > 1):
                        sys.stderr.write("Final result: fuzzy\n")
                    CFG_BIBMATCH_LOGGER.info("Matching of record %d: Completed as 'fuzzy'" % (record_counter,))
                else:
                    ambiguousrecs.append((record[0], match_result_output(record_counter, results, server_url, \
                                                                         query, "ambiguous-matched")))
                    if (verbose > 1):
                        sys.stderr.write("Final result: ambiguous\n")
                    CFG_BIBMATCH_LOGGER.info("Matching of record %d: Completed as 'ambiguous'" % (record_counter,))
            elif len(ambiguous_results) > 0:
                # Find common record-id for all ambiguous results and grab first query
                # as "representative" query
                query = ambiguous_results[0][1]
                result_lists = []
                for res, dummy in ambiguous_results:
                    result_lists.extend(res)
                results = set([res for res in result_lists])
                ambiguousrecs.append((record[0], match_result_output(record_counter, results, server_url, \
                                                                  query, "ambiguous-matched")))
                if (verbose > 1):
                    sys.stderr.write("Final result: ambiguous\n")
                CFG_BIBMATCH_LOGGER.info("Matching of record %d: Completed as 'ambiguous'" % (record_counter,))
            else:
                newrecs.append((record[0], match_result_output(record_counter, [], server_url, str(qrystrs))))
                if (verbose > 1):
                    sys.stderr.write("Final result: new\n")
                CFG_BIBMATCH_LOGGER.info("Matching of record %d: Completed as 'new'" % (record_counter,))
    CFG_BIBMATCH_LOGGER.info("-- BibMatch ending match: New(%d), Matched(%d), Ambiguous(%d), Fuzzy(%d) --" % \
                             (len(newrecs), len(matchedrecs), len(ambiguousrecs), len(fuzzyrecs)))
    return [newrecs, matchedrecs, ambiguousrecs, fuzzyrecs]

def match_record(bibmatch_recid, record, server, qrystrs=None, search_mode=None, operator="and", \
                 verbose=1, sleeptime=CFG_BIBMATCH_LOCAL_SLEEPTIME, \
                 clean=False, collections=[], fuzzy=True, validate=True, \
                 ascii_mode=False):
    """
    Matches a single record.

    @param bibmatch_recid: Current record number. Used for logging.
    @type bibmatch_recid: int

    @param record: record to match in BibRecord structure
    @type record: dict

    @param server: InvenioConnector server object
    @type server: object

    @param qrystrs: list of tuples (field, querystring)
    @type qrystrs: list

    @param search_mode: if mode is given, the search will perform an advanced
                        query using the desired mode. Otherwise 'simple search'
                        is used.
    @type search_mode: str

    @param operator: operator used to concatenate values of fields occurring more then once.
                     Valid types are: AND, OR. Defaults to AND.
    @type operator: str

    @param verbose: be loud
    @type verbose: int

    @param server_url: which server to search on. Local installation by default
    @type server_url: str

    @param sleeptime: amount of time to wait between each query
    @type sleeptime: float

    @param clean: should the search queries be cleaned before passed them along?
    @type clean: bool

    @param collections: list of collections to search, if specified
    @type collections: list

    @param fuzzy: True to activate fuzzy query matching step
    @type fuzzy: bool

    @param validate: True to activate match validation
    @type validate: bool

    @param ascii_mode: True to transform values to its ascii representation
    @type ascii_mode: bool
    """
    matched_results = []
    ambiguous_results = []
    fuzzy_results = []
    # Keep a list of generated querystring objects for later use in fuzzy match
    query_list = []
    # Go through each querystring, trying to find a matching record
    # Stops on first valid match, if no exact-match we continue with fuzzy match
    for field, qrystr in qrystrs:
        querystring = Querystring(operator, clean=clean, ascii_mode=ascii_mode)
        query, complete = querystring.create_query(record, qrystr)
        if query == "":
            if (verbose > 1):
                sys.stderr.write("\nEmpty query. Skipping...\n")
            # Empty query, no point searching database
            continue
        query_list.append((querystring, complete, field))
        if not complete:
            if (verbose > 1):
                sys.stderr.write("\nQuery not complete. Flagged as uncertain/ambiguous...\n")

        # Determine proper search parameters
        if search_mode != None:
            search_params = dict(p1=query, f1=field, m1=search_mode, of='id', c=collections)
        else:
            search_params = dict(p=query, f=field, of='id', c=collections)
        if (verbose > 8):
            sys.stderr.write("\nSearching with values %s\n" %
                             (search_params,))
        CFG_BIBMATCH_LOGGER.info("Searching with values %s" % (search_params,))
        ## Perform the search with retries
        try:
            result_recids = server.search_with_retry(sleeptime=62.0, retrycount=4,**search_params)
        except InvenioConnectorAuthError, error:
            if verbose > 0:
                sys.stderr.write("Authentication error when searching: %s" \
                                 % (str(error),))
            break

        sleep(sleeptime)

        ## Check results:
        if len(result_recids) > 0:
            # Matches detected
            CFG_BIBMATCH_LOGGER.info("Results: %s" % (result_recids[:15],))

            if len(result_recids) > CFG_BIBMATCH_SEARCH_RESULT_MATCH_LIMIT:
                # Too many matches, treat as non-match
                if (verbose > 8):
                    sys.stderr.write("result=More then %d results...\n" % \
                                    (CFG_BIBMATCH_SEARCH_RESULT_MATCH_LIMIT,))
                continue

            if (verbose > 8):
                sys.stderr.write("result=%s\n" % (result_recids,))

            if validate:
                # Validation can be run
                CFG_BIBMATCH_LOGGER.info("Matching of record %d: Query (%s) found %d records: %s" % \
                                         (bibmatch_recid,
                                          query,
                                          len(result_recids),
                                          str(result_recids)))
                exact_matches = []
                fuzzy_matches = []
                try:
                    exact_matches, fuzzy_matches = validate_matches(bibmatch_recid=bibmatch_recid, \
                                                                    record=record, \
                                                                    server=server, \
                                                                    result_recids=result_recids, \
                                                                    collections=collections, \
                                                                    verbose=verbose, \
                                                                    ascii_mode=ascii_mode)
                except BibMatchValidationError, e:
                    sys.stderr.write("ERROR: %s\n" % (str(e),))

                if len(exact_matches) > 0:
                    if (verbose > 8):
                        sys.stderr.write("Match validated\n")
                    matched_results.append((exact_matches, query))
                    break
                elif len(fuzzy_matches) > 0:
                    if (verbose > 8):
                        sys.stderr.write("Match validated fuzzily\n")
                    fuzzy_results.append((fuzzy_matches, query))
                    continue
                else:
                    if (verbose > 8):
                        sys.stderr.write("Match could not be validated\n")

            else:
                # No validation
                # Ambiguous match
                if len(result_recids) > 1:
                    ambiguous_results.append((result_recids, query))
                    if (verbose > 8):
                        sys.stderr.write("Ambiguous\n")
                    continue
                # Match
                elif len(result_recids) == 1:
                    if complete:
                        matched_results.append((result_recids, query))
                        if (verbose > 8):
                            sys.stderr.write("Match\n")
                        # This was a complete match, so let's break out to avoid more searching
                        break
                    else:
                        # We treat the result as ambiguous (uncertain) when query is not complete
                        # and we are not validating it.
                        ambiguous_results.append((result_recids, query))
                        if (verbose > 8):
                            sys.stderr.write("Ambiguous\n")
                        continue
        # No match
        if (verbose > 8):
            sys.stderr.write("result=No matches\n")
    # No complete matches, lets try fuzzy matching of all the queries
    else:
        if fuzzy:
            if (verbose > 8):
                sys.stderr.write("\nFuzzy query mode...\n")
            ## Fuzzy matching: Analyze all queries and perform individual searches, then intersect results.
            for querystring, complete, field in query_list:
                result_hitset = None
                if (verbose > 8):
                    sys.stderr.write("\n Start new search ------------ \n")
                fuzzy_query_list = querystring.fuzzy_queries()
                empty_results = 0
                # Go through every expression in the query and generate fuzzy searches
                for current_operator, qry in fuzzy_query_list:
                    current_resultset = None
                    if qry == "":
                        if (verbose > 1):
                            sys.stderr.write("\nEmpty query. Skipping...\n")
                            # Empty query, no point searching database
                            continue
                    search_params = dict(p=qry, f=field, of='id', c=collections)
                    CFG_BIBMATCH_LOGGER.info("Fuzzy searching with values %s" % (search_params,))
                    try:
                        current_resultset = server.search_with_retry(**search_params)
                    except InvenioConnectorAuthError, error:
                        if (verbose > 0):
                            sys.stderr.write("Authentication error when searching: %s" \
                                             % (str(error),))
                        break
                    CFG_BIBMATCH_LOGGER.info("Results: %s" % (current_resultset[:15],))
                    if (verbose > 8):
                        if len(current_resultset) > CFG_BIBMATCH_SEARCH_RESULT_MATCH_LIMIT:
                            sys.stderr.write("\nSearching with values %s result=%s\n" %
                                         (search_params, "More then %d results..." % \
                                          (CFG_BIBMATCH_SEARCH_RESULT_MATCH_LIMIT,)))
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
                else:
                    # We did not hit a break in the for-loop: we were allowed to search.
                    if result_hitset and len(result_hitset) > CFG_BIBMATCH_SEARCH_RESULT_MATCH_LIMIT:
                        if (verbose > 1):
                            sys.stderr.write("\nToo many results... %d  " % (len(result_hitset)))
                    elif result_hitset:
                        # This was a fuzzy match
                        query_out = " ".join(["%s %s" % (op, qu) for op, qu in fuzzy_query_list])
                        if validate:
                            # We can run validation
                            CFG_BIBMATCH_LOGGER.info("Matching of record %d: Fuzzy query (%s) found %d records: %s" % \
                                                     (bibmatch_recid,
                                                      query_out,
                                                      len(result_hitset),
                                                      str(result_hitset)))
                            exact_matches = []
                            fuzzy_matches = []
                            try:
                                exact_matches, fuzzy_matches = validate_matches(bibmatch_recid=bibmatch_recid, \
                                                                                record=record, \
                                                                                server=server, \
                                                                                result_recids=result_hitset, \
                                                                                collections=collections, \
                                                                                verbose=verbose, \
                                                                                ascii_mode=ascii_mode)
                            except BibMatchValidationError, e:
                                sys.stderr.write("ERROR: %s\n" % (str(e),))

                            if len(exact_matches) > 0:
                                if (verbose > 8):
                                    sys.stderr.write("Match validated\n")
                                matched_results.append((exact_matches, query_out))
                                break
                            elif len(fuzzy_matches) > 0:
                                if (verbose > 8):
                                    sys.stderr.write("Match validated fuzzily\n")
                                fuzzy_results.append((fuzzy_matches, query_out))
                            else:
                                if (verbose > 8):
                                    sys.stderr.write("Match could not be validated\n")
                        else:
                            # No validation
                            if len(result_hitset) == 1 and complete:
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
    return [matched_results, ambiguous_results, fuzzy_results]

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

def bibrecs_has_errors(bibrecs):
    """
    Utility function to check a list of parsed BibRec objects, directly
    from the output of bibrecord.create_records(), for any
    badly parsed records.

    If an error-code is present in the result the function will return True,
    otherwise False.
    """
    return 0 in [err_code for dummy, err_code, dummy2 in bibrecs]

def main():
    """
    Record matches database content when defined search gives
    exactly one record in the result set. By default the match is
    done on the title field.
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], "0123hVm:fq:c:nv:o:b:i:r:tazx:",
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
                   "clean",
                   "collection=",
                   "user=",
                   "no-fuzzy",
                   "no-validation",
                   "ascii"
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
    server_url = CFG_SITE_SECURE_URL          # url to server performing search, local by default
    modify = 0                                # alter output with matched record identifiers
    textmarc_output = 0                       # output in MARC instead of MARCXML
    field = ""
    search_mode = None                        # activates a mode, uses advanced search instead of simple
    sleeptime = CFG_BIBMATCH_LOCAL_SLEEPTIME  # the amount of time to sleep between queries, changes on remote queries
    clean = False                             # should queries be sanitized?
    collections = []                          # only search certain collections?
    user = ""
    password = ""
    validate = True                           # should matches be validate?
    fuzzy = True                              # Activate fuzzy-mode if no matches found for a record
    ascii_mode = False                        # Should values be turned into ascii mode

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
        if opt in ["-x", "--collection"]:
            colls = opt_value.split(',')
            for collection in colls:
                if collection not in collections:
                    collections.append(collection)
        if opt in ["--user"]:
            user = opt_value
            password = getpass.getpass()
        if opt == "--no-fuzzy":
            fuzzy = False
        if opt == "--no-validation":
            validate = False
        if opt == "--ascii":
            ascii_mode = True

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
    if not file_read.strip().startswith('<'):
        # Not xml, assume type textmarc
        file_read = transform_input_to_marcxml(f_input, file_read)

    records = create_records(file_read)

    if len(records) == 0:
        if verbose:
            sys.stderr.write("\nBibMatch: Input file contains no records.\n")
        sys.exit(1)

    # Check for any parsing errors in records
    if bibrecs_has_errors(records):
        # Errors found. Let's try to remove any XML entities
        if verbose > 8:
            sys.stderr.write("\nBibMatch: Parsing error. Trying removal of XML entities..\n")

        file_read = xml_entities_to_utf8(file_read)
        records = create_records(file_read)
        if bibrecs_has_errors(records):
            # Still problems.. alert the user and exit
            if verbose:
                errors = "\n".join([str(err_msg) for dummy, err_code, err_msg in records \
                                    if err_code == 0])
                sys.stderr.write("\nBibMatch: Errors during record parsing:\n%s\n" % \
                                 (errors,))
            sys.exit(1)

    if verbose:
        sys.stderr.write("read %d records" % (len(records),))
        sys.stderr.write("\nBibMatch: Matching ...")

    if not validate:
        if verbose:
            sys.stderr.write("\nWARNING: Skipping match validation.\n")

    match_results = match_records(records=records,
                                  qrystrs=qrystrs,
                                  search_mode=search_mode,
                                  operator=operator,
                                  verbose=verbose,
                                  server_url=server_url,
                                  modify=modify,
                                  sleeptime=sleeptime,
                                  clean=clean,
                                  collections=collections,
                                  user=user,
                                  password=password,
                                  fuzzy=fuzzy,
                                  validate=validate,
                                  ascii_mode=ascii_mode)

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
        sys.stderr.write("\n See detailed log at %s\n" % (CFG_LOGFILE,))

    if not noprocess and recs_out:
        print '<collection xmlns="http://www.loc.gov/MARC21/slim">'
        for record, results in recs_out:
            if textmarc_output:
                # FIXME: textmarc output does not print matching results
                print transform_record_to_marc(record)
            else:
                print results
                print record_xml_output(record)
        print "</collection>"

    if batch_output:
        i = 0
        outputs = ['new', 'matched', 'ambiguous', 'fuzzy']
        for result in match_results:
            out = []
            out.append('<collection xmlns="http://www.loc.gov/MARC21/slim">')
            for record, results in result:

                if textmarc_output:
                    # FIXME: textmarc output does not print matching results
                    out.append(transform_record_to_marc(record))
                else:
                    out.append(results)
                    out.append(record_xml_output(record))
            out.append("</collection>")
            filename = "%s.%s.xml" % (batch_output, outputs[i])
            file_fd = open(filename, "w")
            file_fd.write("\n".join(out))
            file_fd.close()
            i += 1
