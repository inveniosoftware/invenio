## -*- mode: python; coding: utf-8; -*-
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
    import getpass
    import time
    import base64
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)

try:
    from invenio.config import CFG_SITE_ADMIN_EMAIL, CFG_VERSION
except ImportError, e:
    print "Error: %s" % e
    import sys
    sys.exit(1)


http_response_status_code = {

    "000" : "Unknown",
    "100" : "Continue",
    "200" : "OK",
    "302" : "Redirect",
    "401" : "Authentication Required",
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

    return urllib.urlencode(http_param_dict)

def OAI_Session(server, script, http_param_dict , method="POST", output="",
                resume_request_nbr=0, secure=False, user=None, password=None,
                cert_file=None, key_file=None):
    """Handle one OAI session (1 request, which might lead
    to multiple answers because of resumption tokens)

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
                    http_request_parameters(http_param_dict, method), method,
                    secure, user, password, cert_file, key_file)

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
                        http_request_parameters(http_param_dict, method), method,
                        secure, user, password, cert_file, key_file)

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
            sets=None, secure=False, user=None, password=None,
            cert_file=None, key_file=None):
    """
    Handle multiple OAI sessions (multiple requests, which might lead to
    multiple answers).

    Needed for harvesting multiple sets in one row.

    Returns the number of files created by the harvesting

        Parameters:

         server - *str* the server URL to harvest
                  eg: cdsweb.cern.ch

         script - *str* path to the OAI script on the server to harvest
                  eg: /oai2d

http_param_dict - *dict* the URL parameters to send to the OAI script
                  eg: {'verb':'ListRecords', 'from'='2004-04-01'}
                  EXCLUDING the setSpec parameters. See 'sets'
                  parameter below.

         method - *str* if we harvest using POST or GET
                  eg: POST

         output - *str* the path (and base name) where results are
                  saved. To handle multiple answers (for eg. triggered
                  by multiple sets harvesting or OAI resumption
                  tokens), this base name is suffixed with a sequence
                  number. Eg output='/tmp/z.xml' ->
                  '/tmp/z.xml.0000000', '/tmp/z.xml.0000001', etc.
                  If file at given path already exists, it is
                  overwritten.
                  When this parameter is left empty, the results are
                  returned on the standard output.

           sets - *list* the sets to harvest. Since this function
                  offers multiple sets harvesting in one row, the OAI
                  'setSpec' cannot be defined in the 'http_param_dict'
                  dict where other OAI parameters are.

         secure - *bool* of we should use HTTPS (True) or HTTP (false)

           user - *str* username to use to login to the server to
                  harvest in case it requires Basic authentication.

       password - *str* a password (in clear) of the server to harvest
                  in case it requires Basic authentication.

       key_file - *str* a path to a PEM file that contain your private
                  key to connect to the server in case it requires
                  certificate-based authentication
                  (If provided, 'cert_file' must also be provided)

       cert_file - *str* a path to a PEM file that contain your public
                  key in case the server to harvest requires
                  certificate-based authentication
                  (If provided, 'key_file' must also be provided)
    """
    if sets:
        i = 0
        for set in sets:
            http_param_dict['set'] = set
            i = OAI_Session(server, script, http_param_dict, method,
                            output, i, secure, user, password,
                            cert_file, key_file)
            i += 1
        return i
    else:
        OAI_Session(server, script, http_param_dict, method,
                    output, secure=secure, user=user,
                    password=password, cert_file=cert_file,
                    key_file=key_file)
        return 1

def write_file(filename="harvest", a=""):
    "Writes a to filename"

    f = open(filename, "w")
    f.write(a)
    f.close()

def OAI_Request(server, script, params, method="POST", secure=False,
                user=None, password=None,
                key_file=None, cert_file=None):
    """Handle OAI request

    Parameters:

        server - *str* the server URL to harvest
                 eg: cdsweb.cern.ch

        script - *str* path to the OAI script on the server to harvest
                 eg: /oai2d

        params - *str* the URL parameters to send to the OAI script
                 eg: verb=ListRecords&from=2004-04-01

        method - *str* if we harvest using POST or GET
                 eg: POST

        secure - *bool* of we should use HTTPS (True) or HTTP (false)

          user - *str* username to use to login to the server to
                 harvest in case it requires Basic authentication.

      password - *str* a password (in clear) of the server to harvest
                 in case it requires Basic authentication.

      key_file - *str* a path to a PEM file that contain your private
                 key to connect to the server in case it requires
                 certificate-based authentication
                 (If provided, 'cert_file' must also be provided)

      cert_file - *str* a path to a PEM file that contain your public
                 key in case the server to harvest requires
                 certificate-based authentication
                 (If provided, 'key_file' must also be provided)
    """

    headers = {"Content-type":"application/x-www-form-urlencoded",
               "Accept":"text/xml",
               "From": CFG_SITE_ADMIN_EMAIL,
               "User-Agent":"CDS Invenio %s" % CFG_VERSION}

    if password:
        # We use basic authentication
        headers["Authorization"] = "Basic " + base64.encodestring(user + ":" + password).strip()

    i = 0
    while i < 10:
        i = i + 1
        if secure and not (key_file and cert_file):
            # Basic authentication over HTTPS
            try:
                conn = httplib.HTTPSConnection(server)
            except httplib.HTTPException, e:
                sys.stderr.write("An error occured when trying to connect to %s: %s" % (server, e))
                sys.exit(0)
        elif secure and key_file and cert_file:
            # Certificate-based authentication
            try:
                conn = httplib.HTTPSConnection(server,
                                               key_file=key_file,
                                               cert_file=cert_file)
            except httplib.HTTPException, e:
                sys.stderr.write("An error occured when trying to connect to %s: %s" % (server, e))
                sys.exit(0)
        else:
            # Unsecured connection
            try:
                conn = httplib.HTTPConnection(server)
            except httplib.HTTPException, e:
                sys.stderr.write("An error occured when trying to connect to %s: %s" % (server, e))
                sys.exit(0)

        if method == "GET":
            conn.request("GET", script + "?" + params, headers=headers)
        elif method == "POST":
            conn.request("POST", script, params, headers)

        try:
            response = conn.getresponse()
        except httplib.HTTPException, e:
            sys.stderr.write("An error occured when trying to read response from %s: %s" % (server, e))
            sys.exit(0)

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

        elif response.status == 401:
            if user is not None:
                sys.stderr.write("Try again\n")
            if not secure:
                sys.stderr.write("*WARNING* Your password will be sent in clear!\n")
            # getting input from user
            sys.stderr.write('User:')
            try:
                user = raw_input()
                password = getpass.getpass()
            except EOFError, e:
                sys.stderr.write("\n")
                sys.exit(1)
            except KeyboardInterrupt, e:
                sys.stderr.write("\n")
                sys.exit(1)
            headers["Authorization"] = "Basic " + base64.encodestring(user + ":" + password).strip()
        else:
            sys.stderr.write("Retry in 10 seconds...\n")
            time.sleep(10)


    sys.stderr.write("Harvesting interrupted (after 10 attempts) at %s: %s\n"
        % (time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()), params))

    sys.exit(1)


def usage(exitcode=0, msg=""):
    "Print out info"

    if msg:
        sys.stderr.write(msg + "\n")

    sys.stderr.write("""
Usage: bibharvest [options] baseURL
Example:
       bibharvest -vListRecords -f2004-04-01 -u2004-04-02 -pmarcxml -o/tmp/z.xml http://cdsweb.cern.ch/oai2d

Options:
 -h, --help           print this help
 -V, --version        print version number
 -o, --output         specify output file
 -v, --verb           OAI verb to be executed
 -m, --method         http method (default POST)
 -p, --metadataPrefix metadata format
 -i, --identifier     OAI identifier
 -s, --set            OAI set(s). Whitespace-separated list
 -r, --resuptionToken Resume previous harvest
 -f, --from           from date (datestamp)
 -u, --until          until date (datestamp)
 -c, --certificate    path to public certificate (in case of certificate-based harvesting)
 -k, --key            path to private key (in case of certificate-based harvesting)
 -l, --user           username (in case of password-protected harvesting)
 -w, --password       password (in case of password-protected harvesting)
""")

    sys.exit(exitcode)

def main():
    "Main"

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hVo:v:m:p:i:s:f:u:r:x:c:k:w:l:",
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
                   "resumptionToken",
                   "certificate",
                   "key",
                   "user",
                   "password"
                 ]
        )
    except getopt.error, e:
        usage(1, e)

    http_param_dict        = {}
    method                 = "POST"
    output                 = ""
    user                   = None
    password               = None
    cert_file              = None
    key_file               = None
    sets = []

    # get options and arguments
    for opt, opt_value in opts:
        if   opt in ["-v", "--version"]:
            http_param_dict['verb']             = opt_value
        elif opt in ["-m", '--method']:
            if opt_value == "GET" or opt_value == "POST":
                method                          = opt_value
        elif opt in ["-p", "--metadataPrefix"]:
            http_param_dict['metadataPrefix']   = opt_value
        elif opt in ["-i", "--identifier"]:
            http_param_dict['identifier']       = opt_value
        elif opt in ["-s", "--set"]:
            sets                                = opt_value.split()
        elif opt in ["-f", "--from"]:
            http_param_dict['from']             = opt_value
        elif opt in ["-u", "--until"]:
            http_param_dict['until']            = opt_value
        elif opt in ["-r", "--resumptionToken"]:
            http_param_dict['resumptionToken']  = opt_value
        elif opt in ["-o", "--output"]:
            output                              = opt_value
        elif opt in ["-c", "--certificate"]:
            cert_file                           = opt_value
        elif opt in ["-k", "--key"]:
            key_file                            = opt_value
        elif opt in ["-l", "--user"]:
            user                                = opt_value
        elif opt in ["-w", "--password"]:
            password                            = opt_value
        elif opt in ["-V", "--version"]:
            print __revision__
            sys.exit(0)
        else:
            usage(1, "Option %s is not allowed" % opt)

    if len(args) > 0:
        server    = args[-1].split("/")[2]
        secure    = args[-1].lower().strip().startswith('https')

        if (cert_file and not key_file) or \
           (key_file and not cert_file):
            # Both are needed if one specified
            usage(1, "You must specify both certificate and key files")

        if password and not user:
            # User must be specified when password is given
            usage(1, "You must specify a username")
        elif user and not password:
            if not secure:
                sys.stderr.write("*WARNING* Your password will be sent in clear!\n")
            try:
                password = getpass.getpass()
            except KeyboardInterrupt, e:
                sys.stderr.write("\n")
                sys.exit(0)

        script    = "/" + "/".join(args[0].split("/")[3:])
        harvest(server, script, http_param_dict, method, output,
                sets, secure, user, password, cert_file, key_file)
        sys.stderr.write("Harvesting successfully completed at: %s\n\n" %
            time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))

    else:
        usage(1, "You must specify the URL to harvest")

if __name__ == '__main__':
    main()

