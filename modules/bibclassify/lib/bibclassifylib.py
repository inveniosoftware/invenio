# -*- coding: utf-8 -*-
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Bibclassify keyword extractor command line entry point.
"""

import getopt
import string
import os
import sre
import sys

# Please fill in the following variables if using standalone (Invenio-independent) version
TMPDIR_STANDALONE = "/usr/local/invenio/var/tmp"
PDFTOTEXT_STANDALONE = "/usr/bin/pdftotext"

fontSize = [12, 14, 16, 18, 20, 22, 24, 26, 28, 30]

def write_message(msg, stream=sys.stdout):
    """Write message and flush output stream (may be sys.stdout or sys.stderr)."""
    if stream == sys.stdout or stream == sys.stderr:
        stream.write("BibClassify Message:  ")
        stream.write("%s\n" % msg)
        stream.flush()
    else:
        sys.stderr.write("Unknown stream %s.  [must be sys.stdout or sys.stderr]\n" % stream)
    return


def usage(code, msg=''):
    "Prints usage for this module."
    if msg:
        sys.stderr.write("Error: %s.\n" % msg)
    usagetext =    """
Usage: bibclassify [options] 

 Examples:
      bibclassify -f file.pdf -k thesaurus.txt -o TEXT
      bibclassify -s -t file.txt -K ontology.rdf -m SLOW

 Specific options:
 -s, --standalone            run as a standalone program rather than as Invenio module (need to set some variables manually)
 -f, --pdffile=FILENAME      name of the pdf file to be classified
 -t, --textfile=FILENAME     name of the text file to be classified
 -k, --thesaurus=FILENAME    name of the text thesaurus (taxonomy)
 -K, --ontology=FILENAME     name of the RDF ontology (a local file or URL)
 -o, --output=HTML|TEXT      output list of keywords in either HTML or text
 -n, --nkeywords=NUMBER      number of keywords that will be processed to generate results (the higher the n, the higher the number of generated composite keywords)
 -N, --Nkeywords=NUMBER      number of output keywords that will be generated (the higher the N, the higher the number of generated main keywords)
 -m, --mode=FAST|SLOW        processing mode: FAST (run on abstract and selected pages), SLOW (run on whole document - more accurate) 
 -q, --spires                outputs composite keywords in the SPIRES standard format (ckw1, ckw2)
 
 General options:
 -h,  --help               print this help and exit
 -V,  --version            print version and exit
"""
    sys.stderr.write(usagetext)
    sys.exit(code)


def generate_keywords(textfile, dictfile):
    """ A method that generates a sorted list of keywords of a document (textfile) based on a simple thesaurus (dictfile). """
    keylist = []
    keyws = []
    wordlista = os.popen("more " + dictfile)
    thesaurus = [x[:-1] for x in wordlista.readlines()]
    for keyword in thesaurus:
        try:
            string.atoi(keyword)
        except ValueError:
            dummy = 1
        else:
            continue                                                    
        if len(keyword)<=1: #whitespace or one char - get rid of
            continue
        else:
           dictOUT = os.popen('grep -iwc "' +keyword.strip()+'" '+textfile).read()
           try:
                occur = int(dictOUT)
                if occur != 0:
                    keylist.append([occur, keyword])
           except ValueError:
                continue
    keylist.sort()
    keylist.reverse()

    for item in keylist:
        keyws.append(item[1])

    return keyws

def generate_keywords_rdf(textfile, dictfile, output, nkeywords, Nkeywords, mode, spires):
    """ A method that generates a sorted list of keywords (text or html output) based on a RDF thesaurus. """

    import rdflib
    keylist = []
    ckwlist = {}
    outlist = []
    compositesOUT = []
    compositesTOADD = []

    keys2drop = []

    composites = {}
    compositesIDX = {}

    text_out = ""
    html_out = []

    delimiter = ""
    if spires==True: delimiter = ","
    else: delimiter = ":"
    
    ns_skos = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
    
    store = rdflib.Graph()
    store.parse(dictfile)              

    size = int(os.stat(textfile).st_size)
    rtmp = open(textfile, 'r')
    atmp = open(textfile, 'r')

    # ASSUMPTION: Guessing that the first 10% of file contains title and abstract
    abstract = " " + str(atmp.read(int(size*0.1))) + " "
    
    if mode == 1:
        # Fast mode: analysing only abstract + title + middle portion of document
        # Abstract and title is generally never more than 20% of whole document.
        text_string = " " + str(rtmp.read(int(size*0.2)))
        throw_away = str(rtmp.read(int(size*0.25)))
        text_string += str(rtmp.read(int(size*0.2)))

    else:
        # Slow mode: get all document
        text_string = " " + str(rtmp.read()) + " "
        
    atmp.close()
    rtmp.close()

    try:
        # Here we are trying to match the human-assigned keywords
        # These are generally found in a document after the key phrase "keywords" or similar
        if text_string.find("Keywords:"):
            safe_keys = text_string.split("Keywords:")[1].split("\n")[0]
        elif text_string.find("Key words:"):
            safe_keys = text_string.split("Key words:")[1].split("\n")[0]
        elif text_string.find("Key Words:"):
            safe_keys = text_string.split("Key Words:")[1].split("\n")[0]
    except:
        safe_keys = ""

    if safe_keys != "":
        print "Author keyword string detected: " + safe_keys

    # Here we start the big for loop around all concepts in the RDF ontology

    for s,pref in store.subject_objects(ns_skos["prefLabel"]):

        dictOUT = 0
        safeOUT = 0
        hideOUT = 0
        candidates = []

        wildcard = ""
        regex = False
        nostandalone = False
        
        # For each concept, we gather the candidates (i.e. prefLabel, hiddenLabel and altLabel)
        # ADDITION: we also consider spiresLabel: this is HEP ontology specific
        candidates.append(pref.strip())

        if store.value(s,ns_skos["note"],any=True) == "nostandalone":
            nostandalone = True
        
        for alt in store.objects(s, ns_skos["altLabel"]):
            candidates.append(alt.strip())

        for hid in store.objects(s, ns_skos["hiddenLabel"]):
            candidates.append(hid.strip())

        # We then create a regex pattern for each candidate and we match it in the document
        # First we match any possible candidate containing regex. These have to be handled a priori
        # (because they might cause double matching, e.g. "gauge theor*" will match "gauge theory"
        for candidate in candidates:
            if candidate.find("/", 0, 1) > -1:
                # We have a wildcard or other regex, do not escape chars
                # Wildcards matched with '\w*'. These truncations should go into hidden labels in the ontology
                regex = True
                pattern = makePattern(candidate, 3)                
                wildcard = pattern
                hideOUT += len(sre.findall(pattern,text_string))
                # print "HIDEOUT: " + str(candidate) + " " + str(hideOUT)

        for candidate in candidates:
            # Different patterns are created according to the type of candidate keyword encountered

            if candidate.find("/", 0, 1) > -1:
                # We have already taken care of this
                continue
            
            elif regex and candidate.find("/", 0, 1) == -1 and len(sre.findall(wildcard," " + candidate + " ")) > 0:
                # The wildcard in hiddenLabel matches this candidate: skip it
                # print "\ncase 2 touched\n"
                continue
            
            elif candidate.find("-") > -1:
                # We have an hyphen -> e.g. "word-word". Look for: "word-word", "wordword", "word word" (case insensitive)
                pattern = makePattern(candidate, 2)

            elif candidate[:2].isupper() or len(candidate) < 3:
                # First two letters are uppercase or very short keyword. This could be an acronym. Better leave case untouched
                pattern = makePattern(candidate, 1)

            else:
                # Let's do some plain case insensitive search
                pattern = makePattern(candidate, 0)

            if len(candidate) < 3:
                # We have a short keyword
                if len(sre.findall(pattern,abstract))> 0:
                    # The short keyword appears in the abstract/title, retain it
                    dictOUT += len(sre.findall(pattern,text_string))
                    safeOUT += len(sre.findall(pattern,safe_keys))

            else:
                dictOUT += len(sre.findall(pattern,text_string))
                safeOUT += len(sre.findall(pattern,safe_keys))

        dictOUT += hideOUT

        if dictOUT > 0 and store.value(s,ns_skos["compositeOf"],default=False,any=True):
            # This is a ckw whose altLabel occurs in the text
            ckwlist[s.strip()] = dictOUT
                                       
        elif dictOUT > 0:
            keylist.append([dictOUT, s.strip(), pref.strip(), safeOUT, candidates, nostandalone])

        regex = False
        
    keylist.sort()
    keylist.reverse()

    if nkeywords > len(keylist):
        nkeywords = len(keylist)

    if Nkeywords > nkeywords:
        Nkeywords = nkeywords

    # Sort out composite keywords based on nkeywords (default=70)
    # Work out whether among nkeywords MKWS, there are possible composite combinations 
    # Generate compositesIDX dictionary of the form:   s (URI) : keylist 
    for i in range(nkeywords):
        try:
            if store.value(rdflib.Namespace(keylist[i][1]),ns_skos["composite"],default=False,any=True):
                compositesIDX[keylist[i][1]] = keylist[i]
                for composite in store.objects(rdflib.Namespace(keylist[i][1]),ns_skos["composite"]):
                    if composites.has_key(composite):
                        composites[composite].append(keylist[i][1])
                    else:
                        composites[composite]=[keylist[i][1]]

            elif store.value(rdflib.Namespace(keylist[i][1]),ns_skos["compositeOf"],default=False,any=True):
                compositesIDX[keylist[i][1]] = keylist[i]

            else:
                outlist.append(keylist[i])

        except:
            print "Problem with composites.. : " + keylist[i][1]

    for s_CompositeOf in composites:
        
        if len(composites.get(s_CompositeOf)) > 2:
            print s_CompositeOf + " - Sorry! Only composite combinations of max 2 keywords are supported at the moment." 
        elif len(composites.get(s_CompositeOf)) > 1:
            # We have a composite match. Need to look for composite1 near composite2
            comp_one = compositesIDX[composites.get(s_CompositeOf)[0]][2]
            comp_two = compositesIDX[composites.get(s_CompositeOf)[1]][2]

            # Now check that comp_one and comp_two really correspond to ckw1 : ckw2
            if store.value(rdflib.Namespace(s_CompositeOf),ns_skos["prefLabel"],default=False,any=True).split(":")[0].strip() == comp_one:
                # order is correct
                searchables_one = compositesIDX[composites.get(s_CompositeOf)[0]][4]
                searchables_two = compositesIDX[composites.get(s_CompositeOf)[1]][4]
                comp_oneOUT = compositesIDX[composites.get(s_CompositeOf)[0]][0]
                comp_twoOUT = compositesIDX[composites.get(s_CompositeOf)[1]][0]
            else:
                # reverse order
                comp_one = compositesIDX[composites.get(s_CompositeOf)[1]][2]
                comp_two = compositesIDX[composites.get(s_CompositeOf)[0]][2]
                searchables_one = compositesIDX[composites.get(s_CompositeOf)[1]][4]
                searchables_two = compositesIDX[composites.get(s_CompositeOf)[0]][4]
                comp_oneOUT = compositesIDX[composites.get(s_CompositeOf)[1]][0]
                comp_twoOUT = compositesIDX[composites.get(s_CompositeOf)[0]][0]
                
            compOUT = 0
            wildcards = []
            phrases = []

            for searchable_one in searchables_one:
                # Work out all possible combination of comp1 near comp2
                c1 = searchable_one
                if searchable_one.find("/", 0, 1) > -1: m1 = 3
                elif searchable_one.find("-") > -1: m1 = 2
                elif searchable_one[:2].isupper() or len(searchable_one) < 3: m1 = 1 
                else: m1 = 0
                for searchable_two in searchables_two:
                    c2 = searchable_two
                    if searchable_two.find("/", 0, 1) > -1: m2 = 3
                    elif searchable_two.find("-") > -1: m2 = 2
                    elif searchable_two[:2].isupper() or len(searchable_two) < 3: m2 = 1 
                    else: m2 = 0

                    c = [c1,c2]
                    m = [m1,m2]

                    patterns = makeCompPattern(c, m)
                    if m1 == 3 or m2 == 3:
                        # One of the composites had a wildcard inside
                        wildcards.append(patterns[0])
                        wildcards.append(patterns[1])
                    else:
                        # No wildcards
                        phrase1 = c1 + " " + c2
                        phrase2 = c2 + " " + c1
                        phrases.append([phrase1, patterns[0]])
                        phrases.append([phrase2, patterns[1]])

                    THIScomp = len(sre.findall(patterns[0],text_string)) + len(sre.findall(patterns[1],text_string))
                    compOUT += THIScomp

            if len(wildcards)>0:
                for wild in wildcards:
                    for phrase in phrases:
                        if len(sre.findall(wild," " + phrase[0] + " ")) > 0:
                            compOUT = compOUT - len(sre.findall(phrase[1],text_string))

            # Add extra results due to altLabels, calculated in the first part
            if ckwlist.get(s_CompositeOf, 0) > 0:
                # Add count and pop the item out of the dictionary
                compOUT += ckwlist.pop(s_CompositeOf)

            if compOUT > 0 and spires==True:
                # Output ckws in spires standard output mode (,)
                if store.value(rdflib.Namespace(s_CompositeOf),ns_skos["spiresLabel"],default=False,any=True):
                    compositesOUT.append([compOUT, store.value(rdflib.Namespace(s_CompositeOf),ns_skos["spiresLabel"],default=False,any=True), comp_one, comp_two, comp_oneOUT, comp_twoOUT])
                else:
                    compositesOUT.append([compOUT, store.value(rdflib.Namespace(s_CompositeOf),ns_skos["prefLabel"],default=False,any=True).replace(":",","), comp_one, comp_two, comp_oneOUT, comp_twoOUT])
                keys2drop.append(comp_one.strip())
                keys2drop.append(comp_two.strip())

            elif compOUT > 0:
                # Output ckws in bibclassify mode (:)
                compositesOUT.append([compOUT, store.value(rdflib.Namespace(s_CompositeOf),ns_skos["prefLabel"],default=False,any=True), comp_one, comp_two, comp_oneOUT, comp_twoOUT])
                keys2drop.append(comp_one.strip())
                keys2drop.append(comp_two.strip())

    # Deal with ckws that only occur as altLabels
    ckwleft = len(ckwlist)
    while ckwleft > 0:
        compositesTOADD.append(ckwlist.popitem())
        ckwleft = ckwleft - 1

    for s_CompositeTOADD, compTOADD_OUT in compositesTOADD:
        if spires == True:
            compositesOUT.append([compTOADD_OUT, store.value(rdflib.Namespace(s_CompositeTOADD),ns_skos["prefLabel"],default=False,any=True).replace(":",","), "null", "null", 0, 0])
        else:
            compositesOUT.append([compTOADD_OUT, store.value(rdflib.Namespace(s_CompositeTOADD),ns_skos["prefLabel"],default=False,any=True), "null", "null", 0, 0])
    
    compositesOUT.sort()
    compositesOUT.reverse()

    # Some more keylist filtering: inclusion, e.g remove "magnetic" if have "magnetic field"
    for i in keylist:
        pattern_to_match = " " + i[2].strip() + " "
        for j in keylist:
            test_key = " " + j[2].strip() + " "
            if test_key.strip() != pattern_to_match.strip() and test_key.find(pattern_to_match) > -1:
                keys2drop.append(pattern_to_match.strip())


    text_out += "\nComposites:\n"
    for ncomp, pref_cOf_label, comp_one, comp_two, comp_oneOUT, comp_twoOUT in compositesOUT:
        safe_comp_mark = " "
        safe_one_mark = ""
        safe_two_mark = ""
        if safe_keys.find(pref_cOf_label)>-1:
            safe_comp_mark = "*"
        if safe_keys.find(comp_one)>-1:
            safe_one_mark = "*"
        if safe_keys.find(comp_two)>-1:
            safe_two_mark = "*"
        text_out += str(ncomp) + safe_comp_mark + " " + str(pref_cOf_label) + " [" + str(comp_oneOUT)  + safe_one_mark + ", " + str(comp_twoOUT) + safe_two_mark + "]\n"
        if safe_comp_mark == "*": html_out.append([ncomp, str(pref_cOf_label), 1])
        else: html_out.append([ncomp, str(pref_cOf_label), 0])

    text_out += "\n\nMain Keywords:\n"
    for i in range(nkeywords):
        safe_mark = " "
        try:
            idx = keys2drop.index(keylist[i][2].strip())
        except:
            idx = -1

        if safe_keys.find(keylist[i][2])>-1:
            safe_mark = "*"

        if idx == -1 and Nkeywords > 0 and keylist[i][5] == False:
            text_out += str(keylist[i][0]) + safe_mark + " " + keylist[i][2] + "\n" 
            if safe_mark == "*": html_out.append([keylist[i][0], keylist[i][2], 1])
            else: html_out.append([keylist[i][0], keylist[i][2], 0])
            Nkeywords = Nkeywords - 1

    if output == 0:
        # Output some text
        print text_out
        
    else:
        # Output some HTML
        html_out.sort()
        html_out.reverse()
        makeTagCloud(html_out)

    return 0

def makeTagCloud(entries):
    """Using the counts for each of the tags, write a simple HTML page to 
    standard output containing a tag cloud representation. The CSS
    describes ten levels, each of which has differing font-size's,
    line-height's and font-weight's.
    """

    max_occurrence = int(entries[0][0])
    print "<html>"
    print "<head>"
    print "<title>Keyword Cloud</title>"
    print "<style type=\"text/css\">"
    print "<!--"
    print 'a{color:#003DF5; text-decoration:none;}'
    print 'a:hover{color:#f1f1f1; text-decoration:none; background-color:#003DF5;}'
    print '.pagebox {color: #000;   margin-left: 1em;   margin-bottom: 1em;    border: 1px solid #000;    padding: 1em;    background-color: #f1f1f1;    font-family: arial, sans-serif;   max-width: 700px;   margin: 10px;   padding-left: 10px;   float: left;}'
    print '.pagebox1 {color: #B5B5B5;   margin-left: 1em;   margin-bottom: 1em;    border: 1px dotted #B5B5B5;    padding: 1em;    background-color: #f2f2f2;    font-family: arial, sans-serif;   max-width: 300px;   margin: 10px;   padding-left: 10px;   float: left;}'
    print '.pagebox2 {color: #000;   margin-left: 1em;   margin-bottom: 1em;    border: 0px solid #000;    padding: 1em;    fond-size: x-small, font-family: arial, sans-serif;   margin: 10px;   padding-left: 10px;   float: left;}'

    for i in range(0, 10):
        print ".level%d" % i
        print "{  color:#003DF5;"
        print "  font-size:%dpx;" % fontSize[i]
        print "  line-height:%dpx;" % (fontSize[i] + 5)

        if i > 5:
            print "  font-weight:bold;"

        print "}"

    print "-->"
    print "</style>"
    print "</head>"
    print "<body>"
    print "<table>"

    cloud = ""
    cloud_list = []

    cloud += '<tr><div class="pagebox" align="top">'    
    # Generate some ad-hoc count distribution
    for i in range(0, len(entries)):
            count = int(entries[i][0])
            tag = str(entries[i][1])
            color = int(entries[i][2])
            if count < (max_occurrence/10):
                cloud_list.append([tag,0,color])
            elif count < (max_occurrence/7.5):
                cloud_list.append([tag,1,color])
            elif count < (max_occurrence/5):
                cloud_list.append([tag,2,color])
            elif count < (max_occurrence/4):
                cloud_list.append([tag,3,color])
            elif count < (max_occurrence/3):
                cloud_list.append([tag,4,color])
            elif count < (max_occurrence/2):
                cloud_list.append([tag,5,color])
            elif count < (max_occurrence/1.7):
                cloud_list.append([tag,6,color])
            elif count < (max_occurrence/1.5):
                cloud_list.append([tag,7,color])
            elif count < (max_occurrence/1.3):
                cloud_list.append([tag,8,color])
            else:
                cloud_list.append([tag,9,color])

    cloud_list.sort()
    for i in range(0, len(cloud_list)):
        cloud += '<span class=\"level%s\" ' % cloud_list[i][1] 
        if int(cloud_list[i][2]) > 0:
            cloud += 'style="color:red" '
        cloud += '><a href=""> %s </a></span>' % cloud_list[i][0] 
    cloud += '</div></tr>'

    print cloud
    print "</table></body>"
    print "</html>"


def makeCompPattern(candidates, modes):
    """Takes a set of two composite keywords (candidates) and compiles a REGEX expression around it, according to the chosen modes for each one:
        - 0 : plain case-insensitive search
        - 1 : plain case-sensitive search
        - 2 : hyphen
        - 3 : wildcard"""

    # NB. For the moment, some patterns are compiled having an optional trailing "s"
    #     This is a very basic method to find plurals in English.
    #     If this program is to be used in other languages, please remove the "s?" from the REGEX
    #     Also, inclusion of plurals at the ontology level would be preferred. 


    begREGEX = '(?:[^A-Za-z0-9\+-])('
    endREGEX = ')(?=[^A-Za-z0-9\+-])'

    pattern_text = []
    patterns = []
    
    for i in range(2):

        if modes[i] == 0:
            pattern_text.append(str(sre.escape(candidates[i]) + 's?'))

        if modes[i] == 1:
            pattern_text.append(str(sre.escape(candidates[i])))

        if modes[i] == 2:
            hyphen = True
            parts = candidates[i].split("-")
            pattern_string = ""
            for part in parts:
                if len(part)<1 or part.find(" ", 0, 1)> -1:
                    # This is not really a hyphen, maybe a minus sign: treat as isupper().
                    hyphen = False
                pattern_string = pattern_string + sre.escape(part) + "[- \t]?"
            if hyphen:
                pattern_text.append(pattern_string)
            else:
                pattern_text.append(sre.escape(candidates[i]))

        if modes[i] == 3:
            pattern_text.append(candidates[i].replace("/","")) 

    pattern_one = sre.compile(begREGEX + pattern_text[0] + "s?[ \s,-]*" + pattern_text[1] + endREGEX, sre.I)
    pattern_two = sre.compile(begREGEX + pattern_text[1] + "s?[ \s,-]*" + pattern_text[0] + endREGEX, sre.I)

    patterns.append(pattern_one)
    patterns.append(pattern_two)
        
    return patterns


def makePattern(candidate, mode):
    """Takes a keyword (candidate) and compiles a REGEX expression around it, according to the chosen mode:
        - 0 : plain case-insensitive search
        - 1 : plain case-sensitive search
        - 2 : hyphen
        - 3 : wildcard"""

    # NB. For the moment, some patterns are compiled having an optional trailing "s"
    #     This is a very basic method to find plurals in English.
    #     If this program is to be used in other languages, please remove the "s?" from the REGEX
    #     Also, inclusion of plurals at the ontology level would be preferred. 

    begREGEX = '(?:[^A-Za-z0-9\+-])('
    endREGEX = ')(?=[^A-Za-z0-9\+-])'
    try:
        if mode == 0:
            pattern = sre.compile(begREGEX + sre.escape(candidate) + 's?' + endREGEX, sre.I)

        if mode == 1:
            pattern = sre.compile(begREGEX + sre.escape(candidate) + endREGEX)

        if mode == 2:
            hyphen = True
            parts = candidate.split("-")
            pattern_string = begREGEX
            for part in parts:
                if len(part)<1 or part.find(" ", 0, 1)> -1:
                    # This is not really a hyphen, maybe a minus sign: treat as isupper().
                    hyphen = False
                pattern_string = pattern_string + sre.escape(part) + "[- \t]?"
            pattern_string += endREGEX
            if hyphen:
                pattern = sre.compile(pattern_string, sre.I)
            else:
                pattern = sre.compile(begREGEX + sre.escape(candidate) + endREGEX, sre.I)

        if mode == 3:
            pattern = sre.compile(begREGEX + candidate.replace("/","") + endREGEX, sre.I) 

    except:
        print "Invalid thesaurus term: " + sre.escape(candidate) + "<br>"

    return pattern



def profile(t="", d=""):
    import profile
    import pstats
    profile.run("generate_keywords_rdf(textfile='%s',dictfile='%s')" % (t, d), "bibclassify_profile")
    p = pstats.Stats("bibclassify_profile")
    p.strip_dirs().sort_stats("cumulative").print_stats()
    return 0

def main():
    """Main function """

    global options
    long_flags =["standalone", "pdffile=", "textfile="
                 "thesaurus=","ontology=",
                 "output=","nkeywords=", "Nkeywords=", "mode=",
                 "spires", "help", "version"]
    short_flags ="sf:t:k:K:o:n:N:m:qhV"
    standalone = False
    spires = False
    nkeywords = 70
    Nkeywords = 25
    input_file = ""
    dict_file = ""
    output = 1
    mode = 1
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], short_flags, long_flags)
    except getopt.GetoptError, err:
        write_message(err, sys.stderr)
        usage(1)
    if args:
        usage(1)

    try:
        for opt in opts:
            if opt[0] in [ "-s", "--standalone" ]:
                tmpdir = TMPDIR_STANDALONE
                pdftotext = PDFTOTEXT_STANDALONE
                standalone = True
        if not standalone:
            # Invenio-specific dependencies
            from invenio.config import tmpdir, pdftotext, version
            version_bibclassify = 0.1
            bibclassify_engine_version = "CDS Invenio/%s bibclassify/%s" % (version, version_bibclassify)

    except StandardError, e:
        write_message(e, sys.stderr)
        sys.exit(1)

    temp_text = tmpdir + '/bibclassify.pdftotext.' + str(os.getpid())

    try:
        for opt in opts:

            if opt == ("-h","")  or opt == ("--help",""):
                usage(1)
            elif opt == ("-V","")  or opt == ("--version",""):
                print bibclassify_engine_version
                sys.exit(1)

            elif opt[0] in [ "-f", "--pdffile" ]:
                if input_file=="":
                    cmd = "%s " % pdftotext + opt[1] + " " + temp_text
                    errcode = os.system(cmd)
                    if errcode == 0 and os.path.exists("%s" % temp_text):
                        input_file = temp_text
                    else:
                        print "Error while running %s.\n" % cmd 
                        sys.exit(1)
                else:
                    print "Either text of pdf file in input"
                    sys.exit(1)
                    
            elif opt[0] in [ "-t", "--textfile" ]:
                if input_file=="":
                    input_file = opt[1]
                else:
                    print "Either text of pdf file in input"
                    sys.exit(1)
                    
            elif opt[0] in [ "-k", "--thesaurus" ]:
                if dict_file=="":
                    dict_file = opt[1]
                else:
                    print "Either a text thesaurus or an ontology (in .rdf format)"
                    sys.exit(1)
                    
            elif opt[0] in [ "-K", "--ontology" ]:
                if dict_file=="" and opt[1].find(".rdf")!=-1:
                    dict_file = opt[1]
                else:
                    print "Either a text thesaurus or an ontology (in .rdf format)"
                    sys.exit(1)

            elif opt[0] in [ "-o", "--output" ]:
                try:
                    if str(opt[1]).lower().strip() == "html":
                        output = 1
                    elif str(opt[1]).lower().strip() == "text":
                        output = 0
                    else:
                        write_message('Output mode (-o) can only be "HTML" or "TEXT". Using default output mode (HTML)')
                except:
                    write_message('Output mode (-o) can only be "HTML" or "TEXT". Using default output mode (HTML)')

            elif opt[0] in [ "-m", "--mode" ]:
                try:
                    if str(opt[1]).lower().strip() == "fast":
                        mode = 1
                    elif str(opt[1]).lower().strip() == "slow":
                        mode = 0
                    else:
                        write_message('Processing mode (-m) can only be "FAST" or "SLOW". Using default output mode (fast)')
                except:
                    write_message('Processing mode (-m) can only be "FAST" or "SLOW". Using default output mode (fast)')

            elif opt[0] in [ "-q", "--spires" ]:
                spires = True
                
            elif opt[0] in [ "-n", "--nkeywords" ]:
                try:
                    num = int(opt[1])
                    if num>1:
                        nkeywords = num
                    else:
                        write_message("Number of keywords for processing (-nkeywords) must be an integer higher than 1. Using default value of 70...")

                except ValueError:
                    write_message("Number of keywords for processing (-n) must be an integer. Using default value of 70...")

            elif opt[0] in [ "-N", "--Nkeywords" ]:
                try:
                    num = int(opt[1])
                    if num>1:
                        Nkeywords = num
                    else:
                        write_message("Number of keywords (-Nkeywords) must be an integer higher than 1. Using default value of 25...")

                except ValueError:
                    write_message("Number of keywords (-N) must be an integer. Using default value of 25...")

    except StandardError, e:
        write_message(e, sys.stderr)
        sys.exit(1)

    if input_file == "" or dict_file == "":
        write_message("Need to enter the name of an input file AND a thesaurus file \n")
        usage(1)

    # Weak method to detect dict_file. Need to improve this (e.g. by looking inside the metadata with rdflib?)
    if dict_file.find(".rdf")!=-1:
        outcome = generate_keywords_rdf(input_file, dict_file, output, nkeywords, Nkeywords, mode, spires)

    else: # Treat as text
        outcome = generate_keywords(input_file, dict_file)
        if nkeywords > len(outcome): nkeywords = len(outcome)
        if output == 0:
            for i in range(nkeywords):
                print outcome[i]
        else:
            print "<html>"
            print "<head>"
            print "<title>Keywords</title>"
            print "<body>"
            print "<table>"
            print '<tr><div class="pagebox2" align="top"><small>'
            for i in range(nkeywords):
                print "<b>" + str(outcome[i]) + "</b><br>"
            print '</small></div></tr>'
            print "</table></body>"
            print "</html>"
    return


if __name__ == '__main__':
    main()                                                                                 


