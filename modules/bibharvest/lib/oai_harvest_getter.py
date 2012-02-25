## -*- mode: python; coding: utf-8; -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011 CERN.
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

"""OAI harvestor - 'wget' records from an OAI repository.

This 'getter' simply retrieve the records from an OAI repository.
"""

__revision__ = "$Id$"

try:
    import sys
    import httplib
    import urllib
    import getpass
    import socket
    import re
    import time
    import base64
    import tempfile
    import os
except ImportError, e:
    print "Error: %s" % e
    sys.exit(1)

try:
    from invenio.config import CFG_SITE_ADMIN_EMAIL, CFG_VERSION
except ImportError, e:
    print "Error: %s" % e
    sys.exit(1)

class InvenioOAIRequestError(Exception):
    pass

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

    Returns a tuple containing an int corresponding to the last created 'resume_request_nbr' and 
    a list of harvested files.
    """
    sys.stderr.write("Starting the harvesting session at %s" %
        time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()))
    sys.stderr.write("%s - %s\n" % (server,
        http_request_parameters(http_param_dict)))

    output_path, output_name = os.path.split(output)
    harvested_files = []
    i = resume_request_nbr
    while True:
        harvested_data = OAI_Request(server, script,
                                     http_request_parameters(http_param_dict, method), method,
                                     secure, user, password, cert_file, key_file)
        if output:
            # Write results to a file specified by 'output'
            if harvested_data.lower().find('<'+http_param_dict['verb'].lower()) > -1:
                output_fd, output_filename = tempfile.mkstemp(suffix="_%07d.harvested" % (i,), \
                                                              prefix=output_name, dir=output_path)
                os.write(output_fd, harvested_data)
                os.close(output_fd)
                harvested_files.append(output_filename)
            else:
                # No records in output? Do not create a file. Warn the user.
                sys.stderr.write("\n<!--\n*** WARNING: NO RECORDS IN THE HARVESTED DATA: "
                                 +  "\n" + repr(harvested_data) + "\n***\n-->\n")
        else:
            sys.stdout.write(harvested_data)

        rt_obj = re.search('<resumptionToken.*>(.+)</resumptionToken>',
            harvested_data, re.DOTALL)
        if rt_obj is not None and rt_obj != "":
            http_param_dict = http_param_resume(http_param_dict, rt_obj.group(1))
            i = i + 1
        else:
            break

    return i, harvested_files

def harvest(server, script, http_param_dict , method="POST", output="",
            sets=None, secure=False, user=None, password=None,
            cert_file=None, key_file=None):
    """
    Handle multiple OAI sessions (multiple requests, which might lead to
    multiple answers).

    Needed for harvesting multiple sets in one row.

    Returns a list of filepaths for harvested files.

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
        resume_request_nbr = 0
        all_harvested_files = []
        for set in sets:
            http_param_dict['set'] = set
            resume_request_nbr, harvested_files = OAI_Session(server, script, http_param_dict, method,
                            output, resume_request_nbr, secure, user, password,
                            cert_file, key_file)
            resume_request_nbr += 1
            all_harvested_files.extend(harvested_files)
        return all_harvested_files
    else:
        dummy, harvested_files = OAI_Session(server, script, http_param_dict, method,
                    output, secure=secure, user=user,
                    password=password, cert_file=cert_file,
                    key_file=key_file)
        return harvested_files

def OAI_Request(server, script, params, method="POST", secure=False,
                user=None, password=None,
                key_file=None, cert_file=None, attempts=10):
    """Handle OAI request. Returns harvested data.

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

      attempts - *int* maximum number of attempts
    Return:

    Returns harvested data if harvest is successful.
    """

    headers = {"Content-type":"application/x-www-form-urlencoded",
               "Accept":"text/xml",
               "From": CFG_SITE_ADMIN_EMAIL,
               "User-Agent":"Invenio %s" % CFG_VERSION}

    if password:
        # We use basic authentication
        headers["Authorization"] = "Basic " + base64.encodestring(user + ":" + password).strip()

    i = 0
    while i < attempts:
        i = i + 1
        # Try to establish a connection
        try:
            if secure and not (key_file and cert_file):
                # Basic authentication over HTTPS
                conn = httplib.HTTPSConnection(server)
            elif secure and key_file and cert_file:
                # Certificate-based authentication
                conn = httplib.HTTPSConnection(server,
                                               key_file=key_file,
                                               cert_file=cert_file)
            else:
                # Unsecured connection
                conn = httplib.HTTPConnection(server)
        except (httplib.HTTPException, socket.error), e:
            raise InvenioOAIRequestError("An error occured when trying to connect to %s: %s" % (server, e))

        # Connection established, perform a request
        try:
            if method == "GET":
                conn.request("GET", script + "?" + params, headers=headers)
            elif method == "POST":
                conn.request("POST", script, params, headers)
        except socket.gaierror, (err, str_e):
            # We'll retry in a few seconds
            nb_seconds_retry = 30
            sys.stderr.write("An error occured when trying to request %s: %s\nWill retry in %i seconds\n" % (server, e, nb_seconds_retry))
            time.sleep(nb_seconds_retry)
            continue

        # Request sent, get results
        try:
            response = conn.getresponse()
        except (httplib.HTTPException, socket.error), e:
            # We'll retry in a few seconds
            nb_seconds_retry = 30
            sys.stderr.write("An error occured when trying to read response from %s: %s\nWill retry in %i seconds\n" % (server, e, nb_seconds_retry))
            time.sleep(nb_seconds_retry)
            continue

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

    raise InvenioOAIRequestError("Harvesting interrupted (after 10 attempts) at %s: %s\n"
        % (time.strftime("%Y-%m-%d %H:%M:%S --> ", time.localtime()), params))
