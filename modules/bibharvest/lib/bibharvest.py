## -*- mode: python; coding: utf-8; -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CDS Invenio OAI harvestor."""

__revision__ = "$Id$"

try:
    import httplib
    import urllib
    import sys
    import re
    import getopt
    import time
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)

try:
    from invenio.config import CFG_SITE_ADMIN_EMAIL, CFG_VERSION, CFG_SITE_NAME
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)


http_response_status_code = {

    "000" : "Unknown",
    "100" : "Continue",
    "200" : "OK",
    "302" : "Redirect",
    "403" : "Forbidden",
    "404" : "Not Found",
    "500" : "Error",
    "503" : "Service Unavailable"
}

def http_param_resume(http_param_dict, resumptionToken):
    "Change parameter dictionary for harvest resumption"

    http_param = {
        'verb'            : http_param_dict['verb'],
        'resumptionToken' : resumptionToken
    }

    return http_param

def http_request_parameters(http_param_dict, method="POST"):
    "Assembly http request parameters for http method used"

    params = ""

    if method == "GET":
        for key in http_param_dict.keys():
            if params:
                params = "%s&" % (params)
            if key:
                params = "%s%s=%s" % (params, key, http_param_dict[key])

    elif method == "POST":
        http_param = {}
        for key in http_param_dict.keys():
            if http_param_dict[key]:
                http_param[key] = http_param_dict[key]
        params = urllib.urlencode(http_param)

    return params

def OAI_Session(server, script, http_param_dict , method="POST", output="",
        stylesheet="", resume_request_nbr=0):
    """Handle one OAI session (1 request, which might lead
    to multiple answers)

    If output filepath is given, each answer of the oai repository is saved
    in corresponding filepath, with a unique number appended at the end.
    This number starts at 'resume_request_nbr'.

    Returns an int corresponding to the last created 'resume_request_nbr'.
    """

    sys.stderr.write("Starting the harvesting session at %s" %
        time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
    sys.stderr.write("%s - %s\n" % (server,
        http_request_parameters(http_param_dict)))

    a = OAI_Request(server, script,
        http_request_parameters(http_param_dict, method), method)

    rt_obj = re.search('<resumptionToken.*>(.+)</resumptionToken>',
        a, re.DOTALL)

    i = resume_request_nbr

    while rt_obj is not None and rt_obj != "":

        if output:
            # Write results to a file named 'output'
            if a.lower().find('<'+http_param_dict['verb'].lower()) > -1:
                write_file( "%s.%07d" % (output, i), a)
            else:
                # hmm, were there no records in output? Do not create
                # a file and warn user
                sys.stderr.write("\n<!--\n*** WARNING: NO RECORDS IN THE HARVESTED DATA: "
                                 +  "\n" + repr(a) + "\n***\n-->\n")
        else:
            sys.stdout.write(a)

        i = i + 1

        time.sleep(1)

        http_param_dict = http_param_resume(http_param_dict, rt_obj.group(1))

        a = OAI_Request(server, script,
            http_request_parameters(http_param_dict, method), method)

        rt_obj = re.search('<resumptionToken.*>(.+)</resumptionToken>',
            a, re.DOTALL)

    if output:
        # Write results to a file named 'output'
        if a.lower().find('<'+http_param_dict['verb'].lower()) > -1:
            write_file("%s.%07d" % (output, i), a)
        else:
            # hmm, were there no records in output? Do not create
            # a file and warn user
            sys.stderr.write("\n<!--\n*** WARNING: NO RECORDS IN THE HARVESTED DATA: "
                                 +  "\n" + repr(a) + "\n***\n-->\n")
    else:
        sys.stdout.write(a)

    return i

def harvest(server, script, http_param_dict , method="POST", output="",
        stylesheet="", sets=[]):
    """
    Handle multiple OAI sessions (multiple requests, which might lead to
    multiple answers).

    Needed for harvesting multiple sets in one row.

    Returns the number of files created by the harvesting
    """
    if sets:
        i = 0
        for set in sets:
            http_param_dict['set'] = set
            i = OAI_Session(server, script, http_param_dict, method,
                output, stylesheet, i)
            i += 1
        return i
    else:
        OAI_Session(server, script, http_param_dict, method,
            output, stylesheet)
        return 1

def write_file(filename="harvest", a=""):
    "Writes a to filename"

    f = open(filename, "w")
    f.write(a)
    f.close()

def help():
    "Print out info"

    print "\n  bibharvest -fhimoprsuv baseURL\n"
    print "  -h                 print this help"
    print "  -V                 print version number"
    print "  -o<outputfilename> specify output file"
    print "  -v<verb>           OAI verb to be executed"
    print "  -m<method>         http method (default POST)"
    print "  -p<metadataPrefix> metadata format"
    print "  -i<identifier>     OAI identifier"
    print "  -s<set(s)>         OAI set(s). Whitespace-separated list"
    print "  -r<resuptionToken> Resume previous harvest"
    print "  -f<from>           from date (datestamp)"
    print "  -u<until>          until date (datestamp)\n"


def OAI_Request(server, script, params, method="POST"):
    "Handle OAI request"

    headers = {"Content-type":"application/x-www-form-urlencoded",
        "Accept":"text/xml",
        "From": CFG_SITE_ADMIN_EMAIL,
        "User-Agent":"CDS Invenio %s" % CFG_VERSION}

    i = 0
    while i < 10:
        i = i + 1
        conn = httplib.HTTPConnection(server)
        if method == "GET":
            conn.putrequest(method, script + "?" + params)
            conn.putheader("Content-type", "application/x-www-form-urlencoded")
            conn.putheader("Accept", "text/xml")
            conn.putheader("From", CFG_SITE_ADMIN_EMAIL)
            conn.putheader("User-Agent", CFG_SITE_NAME)
            conn.endheaders()
        elif method == "POST":
            conn.request("POST", script, params, headers)

        response = conn.getresponse()

        status = "%d" % response.status

        if http_response_status_code.has_key(status):
            sys.stderr.write("%s(%s) : %s : %s\n" % (status,
                http_response_status_code[status],
                response.reason,
                params))
        else:
            sys.stderr.write("%s(%s) : %s : %s\n" % (status,
                http_response_status_code['000'],
                response.reason, params))

        if response.status == 200:
            i = 10
            data = response.read()
            conn.close()
            return data

        elif response.status == 503:
            try:
                nb_seconds_to_wait = \
                    int(response.getheader("Retry-After", "%d" % (i*i)))
            except ValueError:
                nb_seconds_to_wait = 10
            sys.stderr.write("Retry in %d seconds...\n" % nb_seconds_to_wait)
            time.sleep(nb_seconds_to_wait)

        elif response.status == 302:
            sys.stderr.write("Redirecting...\n")
            server    = response.getheader("Location").split("/")[2]
            script    = "/" + \
                "/".join(response.getheader("Location").split("/")[3:])

        else:
            sys.stderr.write("Retry in 10 seconds...\n")
            time.sleep(10)


    sys.stderr.write("Harvesting interrupted (after 10 attempts) at %s: %s\n"
        % (time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()), params))

    sys.exit(1)

def main():
    "Main"


    try:
        opts, args = getopt.getopt(sys.argv[1:], "hVo:v:m:p:i:s:f:u:r:x:",
                 [
                   "help",
                   "version",
                   "output",
                   "verb",
                   "method",
                   "metadataPrefix",
                   "identifier",
                   "set",
                   "from",
                   "until",
                   "resumptionToken"
                 ]
        )
    except getopt.error:
        help()
        sys.exit(1)

    http_param_dict        = {}
    method                 = "POST"
    output                 = ""
    stylesheet             = ""
    sets = []

    # get options and arguments
    for opt, opt_value in opts:
        if   opt == "-v":
            http_param_dict['verb']             = opt_value
        elif opt == "-m":
            if opt_value == "GET" or opt_value == "POST":
                method                          = opt_value
        elif opt == "-p":
            http_param_dict['metadataPrefix']   = opt_value
        elif opt == "-i":
            http_param_dict['identifier']       = opt_value
        elif opt == "-s":
            sets                                = opt_value.split()
        elif opt == "-f":
            http_param_dict['from']             = opt_value
        elif opt == "-u":
            http_param_dict['until']            = opt_value
        elif opt == "-r":
            http_param_dict['resumptionToken']  = opt_value
        elif opt == "-o":
            output                              = opt_value
        elif opt == "-x":
            stylesheet                          = opt_value
        elif opt in ["-V", "--version"]:
            print __revision__
            sys.exit(0)
        else:
            help()
            sys.exit()

    if len(args) > 0:
        server    = args[-1].split("/")[2]
        script    = "/" + "/".join(args[0].split("/")[3:])
        harvest(server, script, http_param_dict, method, output,
            stylesheet, sets)
        sys.stderr.write("Harvesting successfully completed at: %s\n\n" %
            time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))

    else:
        help()
        sys.exit()

if __name__ == '__main__':
    main()

