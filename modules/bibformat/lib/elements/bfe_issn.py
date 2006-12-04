# -*- coding: utf-8 -*-
##
## $Id$
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
"""BibFormat element - Print ISSN corresponding to given journal name 
"""

__revision__ = "$Id$"

import pprint
import urllib
import sys
import re
import getopt
from invenio.search_engine import \
     get_fieldvalues, \
     perform_request_search

def format(bfo):
    """
    Returns the ISSN of the record, if known.<br/>
    Note that you HAVE to pre-generate the correspondances
    journal->ISSN if you want this element
    to return something (Run <code>python bfe_issn.py -h</code> to get help).
    """   
    issns = {   'acta phys. pol. a': '0587-4246',
                'adv. colloid interface sci.': '0001-8686',
                'appl. phys.': '0340-3793',
                'asimmetrie': '1827-1383',
                'atom': '0004-7015',
                'biophys. chem.': '0301-4622',
                'bulg. j. phys.': '1310-0157',
                'curr. appl. phys.': '1567-1739',
                'curr. opin. colloid. interface sci.': '1359-0294',
                'electron. j. theor. phys.': '1729-5254',
                'eur. j. solid state inorg. chem.': '0992-4361',
                'eur. trans. electr. power': '1546-3109',
                'eur. union': '1472-3395',
                'high energy density phys.': '1574-1818',
                'hit j. sci. eng.': '1565-5008',
                'int. j. appl. electromagn. mech.': '1383-5416',
                'int. j. hum.-comput. stud.': '1071-5819',
                'int. j. mass spectrom.': '1387-3806',
                'int. j. mass spectrom. ion process.': '0168-1176',
                'int. j. prod. econ.': '0925-5273',
                'int. j. radiat. appl. instrum. a': '0883-2889',
                'int. j. rock mech. min. sci.': '1365-1609',
                'int. j. therm. sci.': '1290-0729',
                'ipn sci.': '1622-5120',
                'itbm-rbm': '1297-9562',
                'itbm-rbm news': '1297-9570',
                'j. colloid interface sci.': '0021-9797',
                'j. fluids struct.': '0889-9746',
                'j. interlibr. loan doc. deliv. electron. reserve': '1072-303X',
                'j. magn. reson.': '1090-7807',
                'j. magn. reson. a': '1064-1858',
                'j. magn. reson. b': '1064-1866',
                'j. microcomput. appl.': '0745-7138',
                'j. netw. comput. appl.': '1084-8045',
                'j. non-newton. fluid mech.': '0377-0257',
                'j. oper. manage.': '0272-6963',
                'j. sound vib.': '0022-460X',
                'j. vis. commun. image represent.': '1047-3203',
                'jpn. j. appl. phys.': '1347-4065',
                'kek news': '1343-3547',
                'magn. reson. imaging': '0730-725X',
                'mech. syst. signal process.': '0888-3270',
                'netw. comput.': '1046-4468',
                'nucl. eng. technol.': '1738-5733',
                'nucl. phys. news': '1050-6896',
                'nucl. tracks': '0191-278X',
                'nucl. tracks radiat. meas.': '0191-278X',
                'opt. fiber technol.': '1068-5200',
                'opt. switch. netw.': '1573-4277',
                'optik': '0030-4026',
                'philips j. res.': '0165-5817',
                'photonics nanostruct., fundam. appl.': '1569-4410',
                'phys. life rev.': '1571-0645',
                'phys. rev.': '0031-899X',
                'phys. rev. (ser. i)': '0031-899X',
                'plasmas ions': '1288-3255',
                'polym. gels netw.': '0966-7822',
                'prog. nucl. magn. reson. spectrosc.': '0079-6565',
                'rbm-news': '0222-0776',
                'real time imaging': '1077-2014',
                'res. inf.': '1744-8026',
                'rev. g\xc3\xa9n. therm.': '0035-3159',
                'rom. rep. phys.': '1841-8759',
                'sens. actuators b': '0925-4005',
                'simul. model. pract. theory': '1569-190X',
                'solid state sci.': '1293-2558',
                'stat. sci.': '0883-4237',
                'superlattices microstruct.': '0749-6036',
                'tsinghua sci. technol.': '1007-0214',
                'world pat. inf.': '0172-2190',
                'z. phys.': '0044-3328'}


    journal_name = bfo.field('210__%')
    # Here you might want to process journal name
    # by doing the same operation that has been
    # done when saving the mappings
    journal_name = journal_name.lower().strip()
    if journal_name.endswith("[online]"):
        journal_name = journal_name[:-8].rstrip()

    return issns.get(journal_name, 'def')

def build_distant_issns(url, limit=1000):
    """
    Retrieves the ISSNs from a distant Invenio system.
    Store the "journal name -> issn" relation.

    Normalize journal names a little bit:
        - strip whithespace chars (left and right)
        - all lower case
        - remove "[Online]" suffix

    Print the result as Python dict structure.
    """
    ## Parse the results of the http request:
    ## http://cdsweb.cern.ch/search?cc=Periodicals&ot=022,210&of=tm&rg=9000
    
    pattern_field = re.compile(r'''
    \D*(?P<docid>\d*)              #document id
    \s(?P<tag>\d*)__\s\$\$a   #tag
     (?P<value>.*?)$                #value
      ''', re.IGNORECASE | re.DOTALL | re.VERBOSE)
    request = '/search?cc=Periodicals&ot=022,210&of=tm&rg=' + str(limit)
    try:
        fields = urllib.urlopen(url.rstrip('/') + request).readlines()
    except IOError:
        sys.stderr.write("Error: Could not connect to %s.\n" % url)
        sys.exit(0)
        
    issns = {}
    last_doc_id = None
    last_issn = None
    
    for field in fields:
        result = pattern_field.search(field)
        if result:
            doc_id = result.group('docid')
            if doc_id != last_doc_id:
                # Reset saved ISSN if we parse new document
                last_issn = None
                
            tag = result.group('tag')
            if tag == '022':
                # Remember this ISSN
                last_issn = result.group('value')
            
            elif tag == '210' and last_issn is not None:
                # Found a journal name and issn exists.
                # Depending on how journal names are entered into the
                # database, you might want to do some processing
                # before saving:
                journal = result.group('value')
                journal = journal.lower().strip()
                if journal.endswith("[online]"):
                    journal = journal[:-8].rstrip()
                
                issns[journal] = last_issn

            last_doc_id = doc_id
   
    prtyp = pprint.PrettyPrinter(indent=4)
    prtyp.pprint(issns)      

def build_local_issns(limit=1000):
    """
    Retrieves the ISSNs from the local database.
    Store the "journal name -> issn" relation.

    Normalize journal names a little bit:
        - strip whithespace chars (left and right)
        - all lower case
        - remove "[Online]" suffix

    Print the result as Python dict structure.

    """
    
    rec_id_list = perform_request_search(cc='Periodicals',
                                         of='id',
                                         rg=limit)
    issns = {}
    for rec_id in rec_id_list:
        journal_name_list = get_fieldvalues(rec_id, '210__%')
        issn_list = get_fieldvalues(rec_id, '022__a')
        if issn_list:
            issn = issn_list[0] # There should be only one ISSN
            for journal_name in journal_name_list:
                # Depending on how journal names are entered into the database,
                # you might want to do some processing before saving:
                journal_name = journal_name.lower().strip()
                if journal_name.endswith("[online]"):
                    journal_name = journal_name[:-8].rstrip()

                issns[journal_name] = issn
    
    prtyp = pprint.PrettyPrinter(indent=4)
    prtyp.pprint(issns)

def print_info():
    """
    Info on element arguments
    """
    print """ Collects ISSN and corresponding journal names from local repository
 and prints archive as dict structure.
   
 Usage: python bfe_issn.py [Options] [url]
 Example: python bew_issn.py http://cdsweb.cern.ch/
 
 Options:
   -h, --help      print this help
   -u, --url       the URL to collect ISSN from
   -l, --limit     the max number of records to parse for collecting
   -v, --version   print version number
   
 If 'url' is not given, collect from local database, using a faster method.

 Returned structure can then be copied into bfe_issn.py
 'format' function.    
    """
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hl:u:v",
                                   ["help",
                                    "url",
                                    "limit",
                                    "version"
                                    ])
    except getopt.error:
        print_info()
        sys.exit(0)
            
    url = None
    limit = 1000
    for opt, opt_value in opts:

        if opt in ["-u", "--url"]:
            url = opt_value
        elif opt in ["-l", "--limit"]:
            try:
                limit = int(opt_value)
            except ValueError:
                print "'limit' must be an integer"
                print_info()
                sys.exit(1)
                
        elif opt in ["-v", "--version"]:
            print __revision__
            sys.exit(0)
        else:
            print_info()
            sys.exit(0)
            
    if url is not None:
        build_distant_issns(url, limit)
    else:
        build_local_issns(limit) 
