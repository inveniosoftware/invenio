# This file is part of Invenio.
# Copyright (C) 2010, 2011 CERN.
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

'''
BibSWORD Client Http Queries
'''

import urllib2
from tempfile import NamedTemporaryFile
from invenio.config import CFG_TMPDIR
from invenio.utils.url import make_user_agent_string

class RemoteSwordServer:
    '''This class gives every tools to communicate with the SWORD/APP deposit
        of ArXiv.
    '''

    # static variable used to properly perform http request
    agent = make_user_agent_string("BibSWORD")


    def __init__(self, authentication_infos):

        '''
            This method the constructor of the class, it initialise the
            connection using a passord. That allows users to connect with
            auto-authentication.
            @param self: reference to the current instance of the class
            @param authentication_infos: dictionary with authentication infos containing
                                         keys:
                                            - realm: realm of the server
                                            - hostname: hostname of the server
                                            - username: name of an arxiv known user
                                            - password: password of the known user
        '''

        #password manager with default realm to avoid looking for it
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()

        passman.add_password(authentication_infos['realm'],
                             authentication_infos['hostname'],
                             authentication_infos['username'],
                             authentication_infos['password'])

        #create an authentificaiton handler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)

        http_handler = urllib2.HTTPHandler(debuglevel=0)

        opener = urllib2.build_opener(authhandler, http_handler)
        # insalling : every call to opener will user the same user/pass
        urllib2.install_opener(opener)


    def get_remote_collection(self, url):
        '''
            This method sent a request to the servicedocument to know the
            collections offer by arxives.
            @param self: reference to the current instance of the class
            @param url: the url where the request is made
            @return: (xml file) collection of arxiv allowed for the user
        '''

        #format the request
        request = urllib2.Request(url)

        #launch request
        #try:
        response = urllib2.urlopen(request)
        #except urllib2.HTTPError:
        #    return ''
        #except urllib2.URLError:
        #    return ''

        return response.read()


    def deposit_media(self, media, collection, onbehalf):
        '''
            This method allow the deposit of any type of media on a given arxiv
            collection.
            @param self: reference to the current instanc off the class
            @param media: dict of file info {'type', 'size', 'file'}
            @param collection: abreviation of the collection where to deposit
            @param onbehalf: user that make the deposition
            @return: (xml file) contains error ot the url of the temp file
        '''

        #format the final deposit URL
        deposit_url = collection

        #prepare the header
        headers = {}
        headers['Content-Type'] = media['type']
        headers['Content-Length'] = media['size']
        #if on behalf, add to the header
        if onbehalf != '':
            headers['X-On-Behalf-Of'] = onbehalf

        headers['X-No-Op'] = 'True'
        headers['X-Verbose'] = 'True'
        headers['User-Agent'] = self.agent

        #format the request
        result = urllib2.Request(deposit_url, media['file'], headers)

        #launch request
        try:
            return urllib2.urlopen(result).read()
        except urllib2.HTTPError:
            return ''


    def metadata_submission(self, deposit_url, metadata, onbehalf):
        '''
            This method send the metadata to ArXiv, then return the answere
            @param metadata: xml file to submit to ArXiv
            @param onbehalf: specify the persone (and email) to informe of the
                                      publication
        '''

        #prepare the header of the request
        headers = {}
        headers['Host'] = 'arxiv.org'
        headers['User-Agent'] = self.agent
        headers['Content-Type'] = 'application/atom+xml;type=entry'
        #if on behalf, add to the header
        if onbehalf != '':
            headers['X-On-Behalf-Of'] = onbehalf

        headers['X-No-Op'] = 'True'
        headers['X-verbose'] = 'True'

        #format the request
        result = urllib2.Request(deposit_url, metadata, headers)

        #launch request
        try:
            response = urllib2.urlopen(result).read()
        except urllib2.HTTPError as e:
            tmpfd = NamedTemporaryFile(mode='w', suffix='.xml', prefix='bibsword_error_',
                                       dir=CFG_TMPDIR, delete=False)
            tmpfd.write(e.read())
            tmpfd.close()
            return ''
        except urllib2.URLError:
            return ''

        return response


    def get_submission_status(self, status_url) :
        '''
            This method get the xml file from the given URL and return it
            @param status_url: url where to get the status
            @return: xml atom entry containing the status
        '''

        #format the http request
        request = urllib2.Request(status_url)
        request.add_header('Host', 'arxiv.org')
        request.add_header('User-Agent', self.agent)

        #launch request
        try:
            response = urllib2.urlopen(request).read()
        except urllib2.HTTPError:
            return 'HTTPError (Might be an authentication issue)'
        except urllib2.URLError:
            return 'Wrong url'

        return response


