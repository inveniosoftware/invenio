# -*- coding: utf-8 -*-

# This file is part of Invenio.
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
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

# Parsing the qualifier strings and displaying them in a nice LaTeX format

#symbols replacement dictionary

from invenio.config import (CFG_HEPDATA_URL,
                            CFG_HEPDATA_PLOTSIZE,
                            CFG_LOGDIR,
                            CFG_SITE_URL,
                            CFG_SITE_RECORD,
                            CFG_BASE_URL)

import re
import os
import datetime

symbols_dictionary = {
    ".LT." : "&gt;",
    ".GT." : "&lt;",
    ".GE." : "\\geq",
    ".LE." : "\\leq",
    "ELECTRON" : "e",
    "MU" : "\\mu",
    "NU" : "\\nu",
    "MU+" : "\\mu^{+}",
    "UPSILON" : "\Upsilon",
    "PT" : "{\\textit{p}_T}",
    "CHARGED" : "charged",
    "PB" : "Pb",
    "JET": "jet",
    "X" : "\\textit{X}",
    "NUCLEON" : "nucleon",
    "S" : "\\textit{s}",
    "PCT" : "\\%",
    "SIG" : "\\sigma",
    "sig" : "\\sigma",
    "DEG" : "^\\circ",
    "GEV" : "GeV",
    "PSI" : "\\psi",
    "LEPTON" : "l",
    "YRAP": "\\textit{y}",
    "NUMU" : "\\nu_{\\mu}",
    "NUE" : "\\nu_{e}",
    "LAMBDA" : "\\Lambda",
    "MULT" : "mult",
    "KS" : "K_s",
    "NEUTRALS": "neutrals",
    "P" : "p",
    "THETA" : "\\Theta",
    "OMEGA" : "\\Omega",
    "SIGMA" : "\\Sigma",
    "PLAB" : "P_{LAB}",
    "NUCLEUS": "nucleus",
    "CHI" : "\\chi",
    "GAMMA" : "\\Gamma"
 }

# ordered list of tokens to recognise

number_regexp = "\\-?(([0-9]+(\\.([0-9]+)?)?)|(\\.[0-9]+))"
tokens = [
    ("degreesexpr", "(([0-9]+(\\.[0-9]*)*)\\,((\\+|-)[0-9]+(\\.[0-9]*)*),((\\+|-)[0-9]+(\\.[0-9]*)*))"), # describes a range of degrees
    ("rangeexpr1", "((?P<mean>%(number)s)\s*\\(\s*BIN\s*=\s*(?P<from>%(number)s)\s*TO\s*(?P<to>%(number)s)\s*\\))" % {"number" : number_regexp}),
    ("rangeexpr2", "((?P<from>%(number)s)\s*TO\s*(?P<to>%(number)s)\s*\\(\s*MEAN=\s*(?P<mean>%(number)s)\\))" % {"number" : number_regexp}),
    ("rangeexpr3", "((?P<from>%(number)s)\s*TO\s*(?P<to>%(number)s))" % {"number" : number_regexp}),
    ("rangeexpr4", "((?P<from>%(number)s)<\s*(?P<to>%(number)s)\s*\\(\s*MEAN=\s*(?P<mean>%(number)s)\s*\\))" % {"number" : number_regexp}),
    ("number", "(\\-?(([0-9]+(\\.([0-9]+)?)?)|(\\.[0-9]+)))"),
#    ("number", "([0-9]+(\\.([0-9]+)?)?)"),
#    ("number", "(\\.[0-9]+)"), # different notation for numbers
    # fullnumber : (\\-?(([0-9]+(\\.([0-9]+)?)?)|(\\.[0-9]+)))
    ("rarrow", "(--&gt;)"),
    ("rarrow", "(-->)"),
    ("sthequals", "(\\(\s*[a-zA-Z]+\s*=)"),
    ("comasthequals", "(,\s*[a-zA-Z]+\s*=)"),
    ("defequals", "(\\((DEF|def)=)"),
    ("coma", "(,)"),
    ("rfequals", "(\\((RF|rf)=)"),
    ("equals", "(=)"),
    ("open_b", "(\\()"),
    ("close_b", "(\\))"),

    ("colon", "(:)"),
    ("separator", "(\s+)"),
    ("power", "(\\*\\*)"),
    ("arithmetic", "(\\+|-|\\*|\\/)"),
    ("underscore", "(_)"),


    ("greater", "(>)"),
    ("greater", "(\\.GT\\.)"),
    ("greater", "(&gt;)"),

    ("smaller", "(<)"),
    ("smaller", "(&lt;)"),
    ("smaller", "\\.LT\\."),

    ("smallereq", "(<=)"),
    ("smallereq", "(&lt;=)"),
    ("smallereq", "\\.LE\\."),

    ("greatereq", "(>=)"),
    ("greatereq", "(\\.GE\\.)"),
    ("greatereq", "(&gt;=)"),

    ("special", "(\\.[A-Za-z0-9]+\\.)"), #cases like .LG. .GT.
    ("symbol", "([A-Za-z]+[a-zA-Z0-9\\-]*(\\+|-)?)"),    #"[^\\)^\\(^=^:^\s^\\.^,^\\/^\\-^\\+^\\*]+)"),

    ("dot", "(\\.)"),
    ("percent", "(%)"),
    ("questionmark", "(\\?)"),
    ("quote", "(')"),
    ("dquote", "(\")"),
    ("dollar", "(\\$)"),
]

cmps = ("greater", "greatereq", "smaller", "smallereq")

def translate_symbol(s):
    """ Translates symbol using a dictionary.
    This method might work with the internal structure of a symbol"""
#    import rpdb2; rpdb2.start_embedded_debugger('password')
    changed = True

    result_suffix = ""
    result_prefix = ""

    while changed and len(s) > 0:
        changed = False
        if s.upper() in symbols_dictionary:
            # we replace the entire string +
            return result_prefix +  symbols_dictionary[s.upper()] + result_suffix
    # symbol not found in exact form ... we have to start parsing it

        if s[-1] in ("+", "-", "*"):
            result_suffix = "^{" + s[-1] + "}" + result_suffix
            s = s[:-1]
            changed = True

        num_pos = len(s)
        while num_pos > 0 and s[num_pos - 1].isdigit():
            num_pos -= 1

        if s[num_pos:].isdigit():
            result_suffix = "^{" +s[num_pos:] + "}" + result_suffix
            s = s[:num_pos]
            changed = True

        if s.upper().endswith("BAR"):
            result_prefix += "\\bar{"
            result_suffix = "}" + result_suffix
            s = s[:-3]
            changed = True

        # Trying to consider only a suffix of current identifier

        alpha_pos = len(s)
        while alpha_pos > 0 and s[alpha_pos - 1].isalpha():
            alpha_pos -= 1

        if s[alpha_pos:].upper() in symbols_dictionary:
            # only if the suffix is there
            result_suffix = symbols_dictionary[s[alpha_pos:].upper()] + result_suffix
            s = s[:alpha_pos]
            changed = True
        else:
            # treating teh D symbol at the beginning... only if current symbol has been already treated !
            match = re.match("(D([0-9]*))", s)
            if match:
                result_prefix += "d"
                if match.groups()[1]:
                    # we have a number
                    result_prefix += "^{" + match.groups()[1]

                s = s[len(match.groups()[0]):]
                changed = True

    return result_prefix + s + result_suffix

def parse_qualifier(s, is_real=False):
    """
    @param is_real Specifies if RE means real part ... in sope types of headers
    @type is_real boolean
    """
    res = ""
    while s.hasNext():
        # symbol[1] will contain the string representation. checking for symbol[1] means checking for keywords
        symbol = s.getNext()
        if symbol[1] == "ABS":
            symbol = s.getNext()
            while symbol[0] == "separator":
                symbol = s.getNext()
            if symbol[0] != "open_b":
                raise Exception("Missing opening bracket")
            res += "|"
            res += parse_qualifier(s, is_real)
            res += "|"
        elif symbol[1] == "SQRT":
            symbol = s.getNext()
            while symbol[0] == "separator":
                symbol = s.getNext()
            if symbol[0] != "open_b":
                raise Exception("Missing opening bracket")
            res += "\sqrt{"
            res += parse_qualifier(s, is_real)
            res += "}"
        elif symbol[0] == "rarrow":
            res += "\\rightarrow";
        elif symbol[0] == "power":
            # we expect a single number now!
            res += "^{"
            symbol = s.getNext();
            if symbol[1] == "-":
                res+="-"
                symbol = s.getNext();
            if symbol[0] != "number":
                raise Exception("Missing number after the power ** operator")
            res += symbol[1]
            res += "}"
        elif symbol[1] == "IN" or symbol[1] == "in":
            # the unit ... we eat everything until the colon
            unit_tokens = []

            while s.hasNext() and s.showNext()[0] != "colon":
                unit_tokens += [s.getNext()]
            start_pos = 0
            while start_pos < len(unit_tokens) and unit_tokens[start_pos][0] == "separator" :
                start_pos += 1

            res += "("
            res += parse_qualifier(TokensProvider(unit_tokens[start_pos:]), is_real)
            res += ")"

        elif symbol[1] == "TO" or symbol[1] == "to":
            res += "\mbox{--}"

        elif symbol[0] == "open_b":
            res += "("
            res += parse_qualifier(s, is_real)
            res += ")"
        elif symbol[0] == "dollar":
            #skip dollar sign
            pass
        elif symbol[0] == "close_b":
            return res

        elif symbol[0] == "sthequals":
            res += parse_specifier(s, symbol[1][1:-1], is_real)
        elif symbol[0] == "colon":
            while s.hasNext() and s.showNext()[0] == "separator":
                s.getNext()
            if s.hasNext() and s.showNext()[0] in cmps:
                pass
            elif s.hasNext() and s.showNext()[0] == "rangeexpr3":
                pass # there will be no = sign ... \in will come later
            elif s.hasNext():
                res += "="
        elif symbol[0] == "coma":
            # we just suppress comas... unless they are detected in for example degree strings THETA(P=4,P=1,RF=LAB) IN DEG : 140,+30,-40 AND 165,+15,-25
            pass
        elif symbol[0] == "dot":
            # dots will be repeated unless followed by colon
            while s.hasNext() and s.showNext()[0] == "separator":
                s.getNext()
            if s.hasNext() and s.showNext()[0] == "colon":
                s.getNext(); # just eat the following colon
            else:
                res += "."
        elif symbol[1].upper() == "RE":
            if is_real:
                # just a regular symbol ... render
                res += "\Re "
            else:
                while s.showNext()[0] == "separator":
                    s.getNext()

                # reaction should be treated differently depending if it is followed by ( or not
                if s.showNext()[0] == "sthequals":
                    n_tok = s.getNext()
                    res += "RE" + parse_specifier(s, n_tok[1][1:-1], is_real)
                elif s.showNext()[0] == "colon":
                    # eat the colon
                    s.getNext()
                # otherwise we ommit the reaction but render anything else (possibly brackets)

        elif symbol[0] == "degreesexpr":
            # in most of the cases we want to simply display the number. Sometimes the situation is more complex. We need to look if the number should be annotated with subsequent numbers
            # Examples:
            #    THETA(P=4,P=1,RF=LAB) IN DEG : 140,+30,-40 AND 165,+15,-25
            #
            sep = symbol[1].split(",")
            res += sep[0] + "^{" + sep[1] + "}_{" + sep[2] + "}"
        elif symbol[0] == "separator":
            res += "\\; "

        elif symbol[0] in ("rangeexpr1", "rangeexpr2", "rangeexpr4"):
            # expressions of type 370 (BIN=315 TO 420)
            #                     10 TO 20 (MEAN=12)
            #                     <1 (MEAN=0.2)
            regex = filter(lambda x: x[0]==symbol[0], tokens)[0][1]
            tmp = re.match(regex, symbol[1])
            res += tmp.group("mean") + " \\in (" + tmp.group("from") + ", " + tmp.group("to") + ")"
        elif symbol[0] == "rangeexpr3":
            # expressions of type 5 TO 14
            regex = filter(lambda x: x[0]=="rangeexpr3", tokens)[0][1]
            tmp = re.match(regex, symbol[1])
            res += "\\in (" + tmp.group("from") + ", " + tmp.group("to") + ")"
        elif symbol[0] == "greater":
            res += ">"
        elif symbol[0] == "greatereq":
            res += "\\geq "
        elif symbol[0] == "smaller":
            brackets_case = False
            tokens_between = []
            if symbol[1] in ("<", "&lt;"):
                while s.hasNext() and not (s.showNext()[0] in cmps):
                    tokens_between.append(s.getNext())
                if s.hasNext() and s.showNext()[0] == "greater" and s.showNext()[1] in (">", "&gt;"):
                    s.getNext(); #eating the next character which is a closing bracket
                    brackets_case = True
                else:
                    s.goBack(len(tokens_between))

            if brackets_case:
                # removign all the trailing separators
                s1 = 0
                s2 = len(tokens_between) - 1
                while s1 <= s2  and tokens_between[s1][0] == "separator":
                    s1 +=1
                while s1 <= s2 and tokens_between[s2][0] == "separator":
                    s2 -=1
                if s1 == s2 and tokens_between[s1][0] == "separator":
                    res += " \\langle \\rangle "
                else:
                    res += " \\langle " + parse_qualifier(TokensProvider(tokens_between[s1:(s2+1)]), is_real) + " \\rangle"
            else:
                res += " < "

        elif symbol[0] == "smallereq":
            res += "\\leq "
        elif symbol[0] == "number":
            res += symbol[1]
        elif symbol[0] == "arithmetic":
            if symbol[1] == "*":
                res += "\\cdot "
            else:
                res += symbol[1]
        elif symbol[0] == "symbol":
            if s.hasNext() and s.showNext()[1] == "*":
                s.getNext()
                res += translate_symbol(symbol[1] + "*")
            else:
                res += translate_symbol(symbol[1])
        else:
            res += translate_symbol(symbol[1])
    return res

def parse_specifier(tokens_provider, initial_specifier, is_real):
    """Parse expressions like:
       RE(Q=W-LEPTON)
       THETA(P=3,P=1,RF=LAB,Q=INCL,Q=L)
       When calling this method, the original symbol (RE and THETA in examples) has already
       been resolved. We have to parse everything in brackets

       also the first SOMETHING= has been resolved already
       @param is_real Specifies if RE sign should be treated as real part
       @type is_real boolean
       """
    res = []

    specifier_sections = {} # we maintain a list of all specifiers before rendering (we have to assign position to them and to. for a specifier we remember a list of parsed values
    cur_token = (None, None)

    next_specifier = initial_specifier
    while cur_token[0] != "close_b": # this one will be finished in only one case
        cur_specifier = next_specifier.upper()

        tokens_list = []
        # hunting for the coma or closing bracket
        cur_token = (None, None)
        brackets_count = 0 # we want to count brackets and escape in the case of too many closing
        while not ((cur_token[0] == "comasthequals" and  brackets_count == 0) or brackets_count < 0):
            # stop when cur_token[0] == "coma" and and brackets_count == 0
            # stop when brackets_count < 0
            cur_token = tokens_provider.getNext()
            if cur_token[0] == "open_b" or cur_token[0] == "sthequals":
                brackets_count += 1
            if cur_token[0] == "close_b":
                brackets_count -= 1
            tokens_list.append(cur_token)

        if cur_token[0] == "comasthequals":
            next_specifier = cur_token[1][1:-1].strip()

        if not (cur_specifier in specifier_sections):
            specifier_sections[cur_specifier] = []
        specifier_sections[cur_specifier].append(parse_qualifier(TokensProvider(tokens_list[:-1]), is_real))

    # first we treat the case of description separately

    def_section = []
    if "DEF" in specifier_sections:
        def_section = specifier_sections["DEF"][0]
        del specifier_sections["DEF"]

    # the time has come to determine what goes to the top and what to the bottom
    # we choose a very simplistic algorithm that assigns to currently minimal place
    upper_len = 0;
    upper = []
    lower_len = 0;
    lower = []

    for specifier in specifier_sections:
        cur_list = upper
        if upper_len < lower_len:
            upper_len += len(specifier_sections[specifier])
        else:
            cur_list = lower
            lower_len += len(specifier_sections[specifier])

        cur_list += specifier_sections[specifier]

    # and finally we include the comment after the whole specifier
    if len(upper) > 0:
        res.append("^{")
        res.append(",\;".join(upper))
        res.append("}")

    if len(lower) > 0:
        res.append("_{")
        res.append(",\;".join(lower))
        res.append("}")

    if def_section:
        res.append("(" + ",\\;".join(def_section) + ")")
    return "{" + "".join(res) + "}"


class TokensProvider(object):
    def __init__(self, tk):
        self.tokens = tk
        self.current_index = 0

    def hasNext(self):
        return self.current_index < len(self.tokens)

    def getNext(self):
        self.current_index = self.current_index + 1
        return self.tokens[self.current_index - 1]

    def goBack(self, positions=1):
        """return to the previous cahracter
        @parameter positions By how many positions we should go back
        @type positions integer"""
        self.current_index -= positions

    def showNext(self):
        return self.tokens[self.current_index]

def log_unparsable_qualifier(qualifier):
    """
    Extend the log by a qualifier that failed to be parsed.

    @param qualifier: The qualifier that cannot be successfully parsed
    @type qualifier: String
    """
    fname = os.path.join(CFG_LOGDIR, "hepdata_qualifiers.log")
    f = open(fname, "a")
    f.write("%s: %s\n" % (str(datetime.datetime.now()), qualifier))
    f.close()

def tokenize_string(input_s):
    """ Split string into seprate tokens """
    while input_s != "":
        cur_token = None
        for token in tokens:
            a = re.match(token[1], input_s)
            if a:
                cur_token = (token[0], a.groups()[0])
                input_s = input_s[len(a.groups()[0]):]
                break
        if cur_token is None:
            raise Exception("Can not recognise any token in " + input_s)
        yield cur_token

def data_qualifier_to_LateX(qualifier, is_real = False):
    """Transform a data qualifier from HepData representation to LaTeX
    @param is_real Specifies if RE should be treated as real part of a complex number. This depends on the field where we are rendering
    @type is_real boolean
    """
    try:
        tks = [tk for tk in tokenize_string(qualifier)]
        res = parse_qualifier(TokensProvider(tks), is_real)
    except Exception, e:
        log_unparsable_qualifier(qualifier)
#        raise Exception("Unrecognised token %s in a qualifier %s" % (e.message, qualifier))
    return res

def get_hepdata_column_class(dataset_num, datacolumn_num):
    """Generate a unique name that can be used for instance as a CSS class name
    for the data column"""
    return "dataset_%i_datacolumn_%i" % (dataset_num, datacolumn_num)


def get_hepdataplot_url(entry_id, table_num):
    """returns an URL of a general HEP-data page showing all plots
    created for a given publication"""

    return "%s/plot/%s/%s" % (CFG_HEPDATA_URL, entry_id, table_num)


def get_hepdataplot_image_urls(recid, dataset):
    """Returns links to all plots produced from given data
    @param recid Identifier of the parent publication record
    @type recid Integer
    """

    return [("%s/plotimage/hepdata-ins%s-d%s-x1-ylog%s_%s.png" % \
                                (CFG_HEPDATA_URL, str(recid),
                                 str(dataset.position),
                                 str(y+1), CFG_HEPDATA_PLOTSIZE),
                            "%s/plot/ins%s/d%s/x1/y%s" % \
                                (CFG_HEPDATA_URL, str(recid), str(dataset.position),
                                 str(y+1))
                            ) for y in xrange(dataset.y_columns)]

def get_hepdatamultiplot_image_url(recid, dataset):
    """ Create URL to the plot combining all data lines
    """
    # determining columns based on the first data line
    if len(dataset.data) == 0:
        return None
    separator = "$0020"
    insplen = len(filter(lambda x: x["axis"] == "y", dataset.data[0]))
    insp = [ "insp%sds%sya%i" % (str(recid), str(dataset.position), i) for i in xrange(1, insplen + 1)]

    parameters = {
        "yscale" : "lin",
        "xscale" : "lin",
        "xsize" : CFG_HEPDATA_PLOTSIZE,
        "ysize" : CFG_HEPDATA_PLOTSIZE,
        "plotType" : "png",
        "xkey" : 0.7,
        "ykey" : 0.9,
        "xtext" : 0.7,
        "ytext" : 0.9
        }

    str_arguments = separator.join( \
        insp + \
        map(lambda elem: str(elem[0]) + ":" + str(elem[1]), \
                parameters.items()))
    return "%s/plotcombinedimage/%s" % (CFG_HEPDATA_URL, str_arguments)


def get_hepdata_link(recID):
    """Get the hepdata link from for a given record id"""
    return "%s/view/ins%s" % (CFG_HEPDATA_URL, str(recID))


def html_strip(st):
    """Strip HTML string (taking into account nbsps"""
    changed = True
    while (changed):
        st1 = st
        st1 = st1.strip()
        if st1.lower().startswith("&nbsp;"):
            st1 = st1[6:]

        if st1.lower().endswith("&nbsp;"):
            st1 = st1[:-6]
        if st1.startswith("\\;"):
            st1 = st1[2:]

        if st1.endswith("\\;"):
            st1 = st1[:-2]

        changed = (st1 != st)
        st = st1
    return st


def render_hepdata_dataset_html(dataset, recid, seq, display_link=True):
    """ Rendering a single dataset
    @param display_link: Indicates if a link to the data record should be displayed
    @type display_link: boolean
    """
    from invenio.legacy.search_engine import get_fieldvalues

    should_expand_table = len(dataset.data) > 0

    # calculating the table width

    c = [] #collecting parts of the output
    # Fixing identifiers and classes typical for this particular dataset
    args = {
        "data_layer_class" : ("hepdata_data_%i" % (seq, )),
        "plots_layer_class" : ("hepdata_plots_%i" % (seq, )),
        "data_expander_id" : ("hepdata_expander_%i" % (seq, )),
        "masterplot_layer_class" : ("hepdata_masterplot_layer_%i" % (seq,)),
        "masterplot_expander_id" : ("hepdata_masterplot_expander_%i" % (seq,)),
        "plots_rowspan": len(dataset.data),
        "masterplot_rowspan": len(dataset.data_qualifiers) + 3
        }

    args["collapse_message_masterplot"] = "&#8595;&#8595;&#8595;Hide&#8595;&#8595;&#8595;"
    args["expand_message_masterplot"] = "&#8593;&#8593;&#8593;Plot&#8593;&#8593;&#8593;"

    args["onclick_code_masterplot_expand"] = "expandCollapseDataPlots(this.parentNode.parentNode.parentNode.parentNode, '%(masterplot_layer_class)s', '%(plots_layer_class)s', '%(data_layer_class)s', '%(masterplot_expander_id)s', '%(collapse_message_masterplot)s', '%(expand_message_masterplot)s');" % args

    args["collapse_message_moredata"] = "&#8593;&#8593;&#8593;Collapse&#8593;&#8593;&#8593;"
    args["expand_message_moredata"] = "&#8595;&#8595;&#8595;Expand&#8595;&#8595;&#8595;"

    args["onclick_code_moredata_expand"] = "return expandCollapseDataPlots(this.parentNode.parentNode.parentNode.parentNode, '%(data_layer_class)s','%(plots_layer_class)s', '%(masterplot_layer_class)s', '%(data_expander_id)s', '%(collapse_message_moredata)s', '%(expand_message_moredata)s');" % args


    args["expander_colspan"] = dataset.num_columns + 2 # table_width + 2
    args["plots_code"] = render_plots_page(dataset, recid, seq)
    multiplot_url = get_hepdatamultiplot_image_url(recid, dataset)
    if multiplot_url:
        args["multiplot_url"] = multiplot_url

    # rendering the HTML code

    c.append("<div style=\"background-color: #ececec; padding:10px;\">")
    # baseurl = get_hepdata_link(recid)
    # c.append("<h3><a href=\"%s/d%i\">%s</a></h3>" % (baseurl, seq, dataset.name, ))
    for fmt in dataset.additional_files:
        c.append("<a href=\"%s/%s\">%s</a>" % (CFG_HEPDATA_URL, fmt[0], fmt[1]))

    dataset.comments.strip()
    c.append("<br />")
    c.append("<b>Description: </b> " + dataset.comments + "<br />")
    c.append("<br />")

    publisher = get_fieldvalues(dataset.recid, '520__9')

    link_txt = "Go to the record"
    if display_link:
        c.append("<a href=\"%s/%s/%s\">%s</a>" % (CFG_BASE_URL, CFG_SITE_RECORD, str(dataset.recid), link_txt))

    temporary = get_fieldvalues(dataset.recid, '500__a')
    if temporary:
        temporary = temporary[0]

    if publisher[0] == 'HEPDATA' and temporary !="* Temporary entry *" :
        c.append("<div class=\"hepdataTablePlaceholder\">")
        c.append("<table cellpadding=\"0\" cellspacing=\"0\" class=\"hepdataTable\">")

        # rendering files links
        plain_file_url = get_fieldvalues(dataset.recid, '8564_u')
        if plain_file_url:
            c.append("<tr><td colspan=\"%(colspan)s\" style=\"text-align: left;\"> <a href=\"%(plain_file_url)s\"> <img src=\"%(site_url)s/img/file-icon-text-15x20.gif\"></img><br> Plain</td>" % {
                "site_url" : CFG_BASE_URL,
                "plain_file_url" : plain_file_url[0],
                "colspan" : str(dataset.num_columns)
                })

            c.append("""<td rowspan="%(rowspan)i" class="expanderTableCell masterPlotExpanderTableCell">""" \
                         % {"rowspan" :  len(dataset.data_qualifiers) + 3})
            if multiplot_url:
                c.append("""<p class="expander masterPlotExpander" onclick="%(onclick_code_masterplot_expand)s" id="%(masterplot_expander_id)s"><a>%(expand_message_masterplot)s</a></p>""" \
                             % args)
            c.append("</td>")
            c.append("<td class=\"masterplot_cell\" rowspan=\"%(masterplot_rowspan)s\"><div class=\"%(masterplot_layer_class)s\" style=\"display:none;\">" % args)
            if multiplot_url:
                c.append("<div><img src=\"%(multiplot_url)s\" alt=\"The plot is not available\" class=\"hepdataimg\"></img></div>" % args)

            c.append("</div></td>" % args)
            c.append("</tr>")
        else:
            from invenio.utils.hepdata.api import create_hepdata_ticket
            create_hepdata_ticket(dataset.recid, 'Data missing in 8564_u')

        # rendering column titles
        c.append("<tr>")
        for title in dataset.column_titles:
            title_str = ""

            strip_str = html_strip(title["content"])
            if strip_str == ":":
                strip_str = ""
            additional_class = "hepdataTableTitleLayer"
            try:
                title_str = "$" + data_qualifier_to_LateX(strip_str) + "$"
            except:
                title_str = strip_str
            if title_str in ("", "$$"):
                title_str = ""
                additional_class = "hepdataTableEmptyTitleLayer"
            c.append("<th colspan=\"%i\" class=\"hepdataColumnHeader\"><div class=\"%s\">%s</div></th>" % (title["colspan"], additional_class, title_str))
        c.append("</tr>")

        for data_line in dataset.data_qualifiers:
            c.append("<tr>")
            for data in data_line:
                qualifier_string = ""

                # stripping from spaces and single strings having only ":" sign
                strip_str = html_strip(data["content"])
                if strip_str == ":":
                    strip_str = ""
                additional_class = "hepdataQualifierLayer"
                try:
                    qualifier_string = "$" + data_qualifier_to_LateX(strip_str) + "$"

                except Exception, e:
                    qualifier_string = strip_str

                if qualifier_string in ("", "$$"):
                    qualifier_string = ""
                    additional_class = "hepdataEmptyQualifierLayer"
                c.append("<td colspan=\"%i\" class=\"hepdataTableQualifierCell\"><div class=\"%s\">%s</div></td>" % ( \
                        data["colspan"],
                        additional_class,
                        qualifier_string, ))
            c.append("</tr>")
        c.append("</td>")
        c.append("</tr>")


        c.append("<tr>")
        for header in dataset.column_headers:
            header_str = ""
            try:
                header_str = "$" + data_qualifier_to_LateX(header["content"]) + "$"
            except Exception, e:
                header_str = header["content"]

            c.append("<th colspan=\"%i\" class=\"hepdataColumnHeader\"><div class=\"hepdataTableHeaderLayer\">%s</div></th>" % (header["colspan"],
                                                     header_str))

        c.append("</tr>")
        if should_expand_table:
            c.append(("<tr class=\"expander_row\"><td colspan=\"%(expander_colspan)i\" class=" + \
                      "\"expanderTableCell detailedDataExpanderTableCell\">" + \
                      "<p onclick=\"%(onclick_code_moredata_expand)s\" " + \
                      "id=\"%(data_expander_id)s\" "  + \
                      "class=\"expander detailedDataExpander\">" +\
                      "<a>%(expand_message_moredata)s</a></p></td></tr>") % args)

        isFirst = True
        for line in dataset.data:
            c.append("<tr>")
            column_num = -1
            for datap in line:
                column_num += 1
                args["data_column_class"] = \
                    get_hepdata_column_class(seq, column_num)
                args["colspan"] = datap["colspan"]

                c.append(("<td class=\"hepdataDataCell " + \
                              "%(data_column_class)s\" colspan=\"%(colspan)s\"><div class=\"" + \
                              "%(data_layer_class)s hepdataDataLayer\" style=\"display:" + \
                              "none;\">") % args)

                if len(datap["content"].strip()) > 0 and datap["content"].strip()[0] != "-":
                    # we are trying to put all the minus characters before any number
                    c.append("&nbsp;")

                c.append(datap["content"])

                c.append("</div></td>")
            c.append("<td></td>") # an empty column
            if isFirst:
                c.append("<td rowspan=\"%(plots_rowspan)i\"><div class=\"%(plots_layer_class)s\" style=\"display:none;\">%(plots_code)s</div></td>" % args)
            isFirst = False
        c.append("</table>")
        c.append("</div>")

    # Dirty hack to show pre-HEPData harvested records
    # Remove when possible
    if temporary == "* Temporary entry *" and display_link== False:
        c.append("<div class=\"hepdataTablePlaceholder\">")
        c.append("<table cellpadding=\"0\" cellspacing=\"0\" class=\"hepdataTable\">")
        c.append("<tr><td style=\"text-align: center;\">Preview not available</td>")
        c.append("</tr>")
        c.append("</table>")
        c.append("</div>")

    c.append("</div>")
    return "\n".join(c)

def render_dataverse_dataset_html(recid, display_link = True):
    """ Rendering a single Dataverse dataset, both for the tab and the record
    @param display_link Indicates if a link to the data record should be displayed
    @type display_link boolean
    """
    from invenio.legacy.search_engine import get_fieldvalues

    # rendering the HTML code

    c = [] #collecting parts of the output
    c.append("<div style=\"background-color: #ececec; padding:10px;\">")

    comments = get_fieldvalues(recid, '520__h')[0]
    publisher = get_fieldvalues(recid, '520__9')

    c.append("<br />")
    c.append("<b>Description: </b> " + comments + "<br />")
    c.append("<br />")

    link_txt = "Go to the record"
    if display_link:
        c.append("<a href=\"%s/record/%s\">%s</a>" % (CFG_SITE_URL, str(recid), link_txt))

    c.append("<br /><br />")
    if publisher[0] == 'Dataverse' and display_link == False:
        c.append("<div class=\"hepdataTablePlaceholder\">")
        c.append("<table cellpadding=\"0\" cellspacing=\"0\" class=\"hepdataTable\">")
        c.append("<tr><td style=\"text-align: center;\">Preview not available</td>")
        c.append("</tr>")
        c.append("</table>")
        c.append("</div>")
        c.append("<br /><br />")

    c.append("</div>")
    return "\n".join(c)

def render_inspire_dataset_html(recid, display_link = True):
    """ Rendering a single Dataverse dataset, both for the tab and the record
    @param display_link Indicates if a link to the data record should be displayed
    @type display_link boolean
    """
    from invenio.legacy.search_engine import get_fieldvalues

    # rendering the HTML code

    c = [] #collecting parts of the output
    c.append("<div style=\"background-color: #ececec; padding:10px;\">")

    comments = get_fieldvalues(recid, '520__h')[0]

    c.append("<br />")
    c.append("<b>Description: </b> " + comments + "<br />")
    c.append("<br />")

    link_txt = "Go to the record"
    if display_link:
        c.append("<a href=\"%s/record/%s\">%s</a>" % (CFG_SITE_URL, str(recid), link_txt))

    c.append("<br /><br />")
    c.append("</div>")
    return "\n".join(c)

def render_other_dataset_html(recid, display_link = True):
    """ Try to render the basic content of an unknown dataset, both for the tab and the record
    @param display_link Indicates if a link to the data record should be displayed
    @type display_link boolean
    """
    from invenio.legacy.search_engine import get_fieldvalues

    c = [] #collecting parts of the output
    c.append("<div style=\"background-color: #ececec; padding:10px;\">")

    comments = get_fieldvalues(recid, '520__h')
    if comments:
        comments = comments[0]

    c.append("<br />")
    c.append("<b>Description: </b> " + comments + "<br />")
    c.append("<br />")

    link_txt = "Go to the record"
    if display_link:
        c.append("<a href=\"%s/record/%s\">%s</a>" % (CFG_SITE_URL, str(recid), link_txt))

    c.append("<br /><br />")
    c.append("</div>")
    return "\n".join(c)

def render_plots_page(dataset, recid, seq):
    """
    Generate a list of plots from HepData
    @param dataset Dataset object parsed from the HepData page
    @param recid The identifier of the record representing a paper
    @param seq The number of the dataset inside of the HepData page
    """

    def get_titles(dataset):
        remaining_occurences = 0
        cur_title = 0
        while True:
            if remaining_occurences == 0:
                cur_title += 1
                if cur_title in dataset.column_titles:
                    remaining_occurences = dataset.column_titles[cur_title]["colspan"]
                else:
                    while True:
                        yield ""

            if cur_title in dataset.column_titles and "content" in dataset.column_titles[cur_title]:
                yield dataset.column_titles[cur_title]["content"]
            else:
                yield ""
            remaining_occurences -= 1

    c = []
    entry_id = "ins%s" % (str(recid), )
    urls = get_hepdataplot_image_urls(recid, dataset)
    #matching plots with headlines (skip first and the rest should be matched by colspan)
    matched_urls = []

    column_num = dataset.x_columns
    ds_getter = get_titles(dataset)

    for url in urls:
        title = ds_getter.next()
        matched_urls.append((title,  url, get_hepdata_column_class(seq, column_num)))
        column_num += 1

    # rendering matches
    for matched_url in matched_urls:
        args = {
            "plot_page_url" : matched_url[1][1],
            "plot_image_url" : matched_url[1][0],
            "plot_title" : matched_url[0],
            "data_column_class": matched_url[2]
            }

        c.append("<div onmouseover=\"return selectDataColumn('%(data_column_class)s');\" onmouseout=\"return  unselectDataColumn('%(data_column_class)s');\">" % args)
        if args["plot_title"]:
            c.append("<p>%(plot_title)s</p>" % args)
        c.append("<br><a href=\"%(plot_page_url)s\" class=\"hepdataPlotLink\"><img src=\"%(plot_image_url)s\" alt=\"The plot is not available\" class=\"hepdataimg\"></a>" % args)
        c.append("</div>")

    return "\n".join(c)
