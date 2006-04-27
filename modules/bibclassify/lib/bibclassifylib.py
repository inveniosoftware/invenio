# -*- coding: utf-8 -*-
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005 CERN.
##
## The CDSware is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## The CDSware is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.  
##
## You should have received a copy of the GNU General Public License
## along with CDSware; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Bibclassify keyword extractor command line entry point.
"""

from marshal import loads,dumps
import getopt
import getpass
import string
import os
import sre
import sys
import time
import MySQLdb
import Numeric
import signal
import traceback

# rdflib-2.2.3
import rdflib

from cdsware.config import *
from cdsware.bibindex_engine_config import *
from cdsware.dbquery import run_sql
from cdsware.access_control_engine import acc_authorize_action

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
    usagetext =    """ Usage: bibclassify [options] 

 Examples:
      bibclassify -f file.pdf -k thesaurus.txt -o TEXT
      bibclassify -t file.txt -K ontology.rdf -m SLOW

 Specific options:
 -f, --pdffile=FILENAME      name of the pdf file to be classified
 -t, --textfile=FILENAME     name of the text file to be classified
 -k, --thesaurus=FILENAME    name of the text thesaurus (taxonomy)
 -K, --ontology=FILENAME     name of the RDF ontology 
 -o, --output=HTML|TEXT      output list of keywords in either HTML or text
 -n, --nkeywords=NUMBER      max number of keywords to be found
 -m, --mode=FAST|SLOW        processing mode: FAST (run on abstract and selected pages), SLOW (run on whole document - more accurate) 

 General options:
 -h,  --help               print this help and exit
 -V,  --version            print version and exit
"""
    sys.stderr.write(usagetext)
    sys.exit(code)


def generate_keywords(textfile, dictfile):
    """ A method that generates keywords (a list in text format) from a text file thesaurus. """
    counter = 0
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

def generate_keywords_rdf(textfile, dictfile, output, outwords, mode):
    """ A method that generates keywords from an rdf thesaurus. """
    keylist = []
    keyws = []

    counts = {}
    entries = []

    ns_skos = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
    ns_dc=rdflib.Namespace("http://purl.org/dc/elements/1.1/")
    ns_rdf=rdflib.Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    ns_concept=rdflib.Namespace("http://cain.nbii.org/thesauri/CERESTheme.rdf")
    
    store = rdflib.Graph()
    store.load(dictfile)              

    size = int(os.stat(textfile).st_size)
    rtmp = open(textfile, 'r')
    
    if mode == 1:
        # Fast mode: analysing only abstract + title + middle portion of document
        # Abstract and title is never more than 20% of whole document.
        text_string = str(rtmp.read(int(size*0.2)))
        throw_away = str(rtmp.read(int(size*0.25)))
        text_string += str(rtmp.read(int(size*0.2)))

    else:
        # Slow mode: get all document
        text_string = str(rtmp.read())
        
    text_string = text_string.lower()
    rtmp.close()

    try:
        if text_string.find("keywords:"):
            safe_keys = text_string.split("keywords:")[1].split("\n")[0]
        elif text_string.find("key words:"):
            safe_keys = text_string.split("key words:")[1].split("\n")[0]
    except:
        safe_keys = ""

    for s,pref in store.subject_objects(ns_skos["prefLabel"]):
        dictOUT = 0
        dictOUT_alt = 0
        safeOUT = 0
        alternatives = " "
        broaders = " "
        narrowers = " "
        relateds = " "
        safekey = 0

        pattern = '\\b' + pref.lower().strip() + '\\b'
        dictOUT = len(sre.findall(pattern,text_string))
        safeOUT = len(sre.findall(pattern,safe_keys))
        
        for alt in store.objects(s, ns_skos["altLabel"]):
            pattern_alt = '\\b' + alt.lower().strip() + '\\b' 
            dictOUT_alt += len(sre.findall(pattern_alt,text_string))
            safeOUT += len(sre.findall(pattern_alt,safe_keys))
            
            alternatives += alt.strip() + ", "


        alternatives = alternatives[:-2] 
        dictOUT_total = int(dictOUT) + int(dictOUT_alt)

        if dictOUT_total>1:
            if safeOUT>0:
                safekey = safeOUT
            for bro in store.objects(s, ns_skos["broader"]):
                bro_link = store.value(bro, ns_skos["prefLabel"], any=True)
                if bro_link:
                    broaders += bro_link.strip() + ", "
            for nar in store.objects(s, ns_skos["narrower"]):
                nar_link = store.value(nar, ns_skos["prefLabel"], any=True)
                if nar_link:
                    narrowers += nar_link.strip() + ", "
            for rel in store.objects(s, ns_skos["related"]):
                rel_link = store.value(rel, ns_skos["prefLabel"], any=True)
                if rel_link:
                    relateds += rel_link.strip() + ", "
            broaders = broaders[:-2]
            narrowers = narrowers[:-2]
            relateds = relateds[:-2]
                
            keylist.append([dictOUT_total, dictOUT, dictOUT_alt, pref.strip(), alternatives, relateds, broaders, narrowers, safekey])

    keylist.sort()
    keylist.reverse()

    if output == 0:
        details = "\n"
        for i in range(outwords):
                details += str(keylist[i][3]) + " ("+ str(keylist[i][0])
                if int(keylist[i][8])>0:
                    details += "*"
                details += ")\n"
                if len(str(keylist[i][4]))>1:
                    details += " UF (" + str(keylist[i][2]) + "):" + str(keylist[i][4]) + "\n"
                if len(str(keylist[i][5]))>1:
                    details += " RT:" + str(keylist[i][5]) + "\n"
                if len(str(keylist[i][6]))>1:
                    details += " BT:" + str(keylist[i][6]) + "\n"
                if len(str(keylist[i][7]))>1:
                    details += " NT:" + str(keylist[i][7]) + "\n"
                details += "\n"
        print details

    else:
        makeTagCloud(keylist, outwords)

    return keyws

def makeTagCloud(entries, outwords):
    """Using the counts for each of the tags, write a simple HTML page to 
    standard output containing a tag cloud representation. The CSS
    describes ten levels, each of which has differing font-size's,
    line-height's and font-weight's.
    """

    max = int(entries[0][0])
    print "<html>"
    print "<head>"
    print "<title>Keyword Cloud</title>"
    print "<style type=\"text/css\">"
    print "<!--"
    print '.pagebox {color: #000;   margin-left: 1em;   margin-bottom: 1em;    border: 1px solid #000;    padding: 1em;    background-color: #f1f1f1;    font-family: arial, sans-serif;   max-width: 700px;   margin: 10px;   padding-left: 10px;   float: left;}'
    print '.pagebox1 {color: #B5B5B5;   margin-left: 1em;   margin-bottom: 1em;    border: 1px dotted #B5B5B5;    padding: 1em;    background-color: #f2f2f2;    font-family: arial, sans-serif;   max-width: 300px;   margin: 10px;   padding-left: 10px;   float: left;}'
    print '.pagebox2 {color: #000;   margin-left: 1em;   margin-bottom: 1em;    border: 0px solid #000;    padding: 1em;    fond-size: x-small, font-family: arial, sans-serif;   margin: 10px;   padding-left: 10px;   float: left;}'

    for i in range(0, 10):
        print ".level%d" % i
        print "{"

        if i < 1:
            print "  color:#7094FF;"
        elif i < 5:
            print "  color:#3366FF;"
        else:
            print "  color:#003DF5;"
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

    cloud_size = 80
    detail_size = outwords
    details = ""
    cloud = ""
    cloud_list = []

    if cloud_size > len(entries):
        cloud_size = len(entries)
    if detail_size > len(entries):
        detail_size = len(entries)
        
    details += '<tr><div class="pagebox2" align="top"><small>'
    for i in range(0, detail_size):
        if detail_size > 0:
            detail_size -= 1
            details += "<b>" + str(entries[i][3]) + " </b>("+ str(entries[i][0])
            if int(entries[i][8])>0:
                    details += "*"
            details += ")<BR>"
            if len(str(entries[i][4]))>1:
                details += " &nbsp;&nbsp;UF (" + str(entries[i][2]) + "):" + str(entries[i][4]) + "<BR>"
            if len(str(entries[i][5]))>1:
                details += " &nbsp;&nbsp;RT:" + str(entries[i][5]) + "<BR>"
            if len(str(entries[i][6]))>1:
                details += " &nbsp;&nbsp;BT:" + str(entries[i][6]) + "<BR>"
            if len(str(entries[i][7]))>1:
                details += " &nbsp;&nbsp;NT:" + str(entries[i][7]) + "<BR>"
            details += "<BR>"
    details += '</small></div></tr>'

    cloud += '<tr><div class="pagebox" align="top">'    
    # Generate some ad-hoc count distribution
    for i in range(0, len(entries)):
        if cloud_size > 0:
            cloud_size -= 1 
            tag = str(entries[i][3])
            count = int(entries[i][0])
            color = int(entries[i][8])
            if count < (max/10):
                cloud_list.append([tag,0,color])
            elif count < (max/7.5):
                cloud_list.append([tag,1,color])
            elif count < (max/5):
                cloud_list.append([tag,2,color])
            elif count < (max/4):
                cloud_list.append([tag,3,color])
            elif count < (max/3):
                cloud_list.append([tag,4,color])
            elif count < (max/2):
                cloud_list.append([tag,5,color])
            elif count < (max/1.7):
                cloud_list.append([tag,6,color])
            elif count < (max/1.5):
                cloud_list.append([tag,7,color])
            elif count < (max/1.3):
                cloud_list.append([tag,8,color])
            else:
                cloud_list.append([tag,9,color])
        else:
            continue
    cloud_list.sort()
    for i in range(0, len(cloud_list)):
        cloud += '<span class=\"level%s\" ' % cloud_list[i][1] 
        if int(cloud_list[i][2]) > 0:
            cloud += 'style="color:red" '
        cloud += '>  %s  </span>' % cloud_list[i][0] 
    cloud += '</div></tr>'

    key = '<tr><div class="pagebox1" align="top"><em>Key:</em><br><b>UF</b> Used For (alternative term)<br> <b>RT</b> Related Term<br><b>BT</b> Broader Term<br><b>NT</b> Narrower Term<br><b>(n*)</b> Denotes author keyword</div></tr>'

    print cloud
    print key
    print details

    print "</table></body>"
    print "</html>"

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
    long_flags =["pdffile=", "textfile="
                 "thesaurus=","ontology=",
                 "output=","nkeywords=", "mode=",
                 "help", "version"]
    short_flags ="f:t:k:K:o:n:m:hV"
    format_string = "%Y-%m-%d %H:%M:%S"
    outwords = 15
    input_file = ""
    dict_file = ""
    output = 1
    mode = 1
    temp_text = tmpdir + '/bibclassify.pdftotext.' + str(os.getpid())
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], short_flags, long_flags)
    except getopt.GetoptError, err:
        write_message(err, sys.stderr)
        usage(1)
    if args:
        usage(1)

    try:
        for opt in opts:
            if opt == ("-h","")  or opt == ("--help",""):
                usage(1)
            elif opt == ("-V","")  or opt == ("--version",""):
                print "Version 0.1"
                sys.exit(1)
                
            elif opt[0] in [ "-f", "--pdffile" ]:
                if input_file=="":
                    cmd = "%s -nopgbrk -q " % pdftotext + opt[1] + " " + temp_text
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

            elif opt[0] in [ "-n", "--nkeywords" ]:
                try:
                    num = int(opt[1])
                    if num>1:
                        outwords = num
                    else:
                        write_message("Number of keywords (-nkeywords) must be an integer higher than 1. Using default value of 15...")

                except ValueError:
                    write_message("Number of keywords (-n) must be an integer. Using default value of 15...")

    except StandardError, e:
        write_message(e, sys.stderr)
        sys.exit(1)

    if input_file == "" or dict_file == "":
        write_message("Need to enter the name of an input file AND a thesaurus file \n")
        usage(1)

    # Weak method to detect dict_file. Need to improve this (e.g. by looking inside the metadata with rdflib?)
    if dict_file.find(".rdf")!=-1:
        outcome = generate_keywords_rdf(input_file, dict_file, output, outwords, mode)
        # profiling:
        # profile(input_file, dict_file)

    else: # Treat as text
        outcome = generate_keywords(input_file, dict_file)
        if outwords > len(outcome): outwords = len(outcome)
        if output == 0:
            for i in range(outwords):
                print outcome[i]
        else:
            print "<html>"
            print "<head>"
            print "<title>Keywords</title>"
            print "<body>"
            print "<table>"
            print '<tr><div class="pagebox2" align="top"><small>'
            for i in range(outwords):
                print "<b>" + str(outcome[i]) + "</b><br>"
            print '</small></div></tr>'
            print "</table></body>"
            print "</html>"
    return


if __name__ == '__main__':
    # profile("/home/apepe/temp/1bvcecuu6u0qrkgk.txt","/home/apepe/devel/semantic/rdfs/CERESTheme.rdf")
    main()                                                                                 


