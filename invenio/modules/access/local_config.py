# This file is part of Invenio.
# Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2014 CERN.
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

"""Invenio Access Control Config. """

__revision__ = \
    "$Id$"

# pylint: disable=C0301

from invenio.config import CFG_SITE_NAME, CFG_SITE_URL, CFG_SITE_SECURE_URL, CFG_SITE_SUPPORT_EMAIL, CFG_SITE_RECORD, CFG_SITE_ADMIN_EMAIL
from invenio.base.i18n import _
from invenio.base.globals import cfg as config

# VALUES TO BE EXPORTED
# CURRENTLY USED BY THE FILES access_control_engine.py modules.access.control.py webaccessadmin_lib.py

# name of the role giving superadmin rights
SUPERADMINROLE = 'superadmin'

# name of the webaccess webadmin role
WEBACCESSADMINROLE = 'webaccessadmin'

# name of the action allowing roles to access the web administrator interface
WEBACCESSACTION = 'cfgwebaccess'

# name of the action allowing roles to access the web administrator interface
VIEWRESTRCOLL = 'viewrestrcoll'


# name of the action allowing roles to delegate the rights to other roles
# ex: libraryadmin to delegate libraryworker
DELEGATEADDUSERROLE = 'accdelegaterole'

# max number of users to display in the drop down selects
MAXSELECTUSERS = 25

# max number of users to display in a page (mainly for user area)
MAXPAGEUSERS = 25

# default role definition, source:
CFG_ACC_EMPTY_ROLE_DEFINITION_SRC = 'deny all'

# default role definition, compiled:
CFG_ACC_EMPTY_ROLE_DEFINITION_OBJ = (False, ())

# default role definition, compiled and serialized:
CFG_ACC_EMPTY_ROLE_DEFINITION_SER = None

# List of tags containing (multiple) emails of users who should authorize
# to access the corresponding record regardless of collection restrictions.
#if CFG_CERN_SITE:
#    CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS = ['859__f', '270__m']
#else:

CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS = ['8560_f']

#if CFG_CERN_SITE:
#    CFG_ACC_GRANT_VIEWER_RIGHTS_TO_EMAILS_IN_TAGS = ['506__m']
#else:

CFG_ACC_GRANT_VIEWER_RIGHTS_TO_EMAILS_IN_TAGS = []

# Use external source for access control?

# CFG_EXTERNAL_AUTHENTICATION -- this is a dictionary with the enabled login method.
# The key is the name of the login method and the value is an instance of
# of the login method (see /help/admin/webaccess-admin-guide#5). Set the value
# to None if you wish to use the local Invenio authentication method.
# CFG_EXTERNAL_AUTH_DEFAULT -- set this to the key in CFG_EXTERNAL_AUTHENTICATION
# that should be considered as default login method
# CFG_EXTERNAL_AUTH_USING_SSO -- set this to the login method name of an SSO
# login method, if any, otherwise set this to None.
# CFG_EXTERNAL_AUTH_LOGOUT_SSO -- if CFG_EXTERNAL_AUTH_USING_SSO was not None
# set this to the URL that should be contacted to perform an SSO logout

CFG_EXTERNAL_AUTH_DEFAULT = 'Local'
CFG_EXTERNAL_AUTH_USING_SSO = False
CFG_EXTERNAL_AUTH_LOGOUT_SSO = None
CFG_EXTERNAL_AUTHENTICATION = {
    "Local": None,
    # "Robot": ExternalAuthRobot(enforce_external_nicknames=True, use_zlib=False),
    # "ZRobot": ExternalAuthRobot(enforce_external_nicknames=True, use_zlib=True)
    # CFG_EXTERNAL_AUTH_USING_SSO : ea_sso.ExternalAuthSSO(enforce_external_nicknames=True),
}

# from invenio.legacy.external_authentication.robot import ExternalAuthRobot
# if CFG_CERN_SITE:
#     from invenio.legacy.external_authentication import sso as ea_sso
#     CFG_EXTERNAL_AUTH_USING_SSO = "CERN"
#     CFG_EXTERNAL_AUTH_DEFAULT = CFG_EXTERNAL_AUTH_USING_SSO
#     CFG_EXTERNAL_AUTH_LOGOUT_SSO = 'https://login.cern.ch/adfs/ls/?wa=wsignout1.0'
#     CFG_EXTERNAL_AUTHENTICATION = {
#         CFG_EXTERNAL_AUTH_USING_SSO : ea_sso.ExternalAuthSSO(),
#     }
# elif CFG_INSPIRE_SITE:
#     # INSPIRE specific robot configuration
#     CFG_EXTERNAL_AUTH_DEFAULT = 'Local'
#     CFG_EXTERNAL_AUTH_USING_SSO = False
#     CFG_EXTERNAL_AUTH_LOGOUT_SSO = None
#     CFG_EXTERNAL_AUTHENTICATION = {
#     "Local": None,
#     "Robot": ExternalAuthRobot(enforce_external_nicknames=True, use_zlib=False, check_user_ip=2, external_id_attribute_name='personid'),
#     "ZRobot": ExternalAuthRobot(enforce_external_nicknames=True, use_zlib=True, check_user_ip=2, external_id_attribute_name='personid')
#     }
# else:
#     CFG_EXTERNAL_AUTH_DEFAULT = 'Local'
#     CFG_EXTERNAL_AUTH_USING_SSO = False
#     CFG_EXTERNAL_AUTH_LOGOUT_SSO = None
#     CFG_EXTERNAL_AUTHENTICATION = {
#     "Local": None,
#     "Robot": ExternalAuthRobot(enforce_external_nicknames=True, use_zlib=False),
#     "ZRobot": ExternalAuthRobot(enforce_external_nicknames=True, use_zlib=True)
#     }

# CFG_TEMP_EMAIL_ADDRESS
# Temporary email address for logging in with an OpenID/OAuth provider which
# doesn't supply email address
CFG_TEMP_EMAIL_ADDRESS = "%s@NOEMAIL"

# CFG_OPENID_PROVIDERS
# CFG_OAUTH1_PROVIDERS
# CFG_OAUTH2_PROVIDERS
# Choose which providers you want to use. Some providers don't supply e mail
# address, if you choose them, the users will be registered with an temporary
# email address like CFG_TEMP_EMAIL_ADDRESS % randomstring
#
# Order of the login buttons can be changed by CFG_EXTERNAL_LOGIN_BUTTON_ORDER
# in invenio.websession_config
CFG_OPENID_PROVIDERS = [
    'google',
    'yahoo',
    'aol',
    'wordpress',
    'myvidoop',
    'openid',
    'verisign',
    'myopenid',
    'myspace',
    'livejournal',
    'blogger'
]

CFG_OAUTH1_PROVIDERS = [
    'twitter',
    'linkedin',
    'flickr'
]

CFG_OAUTH2_PROVIDERS = [
    'facebook',
    'yammer',
    'foursquare',
    'googleoauth2',
    'instagram',
    'orcid'
]

# CFG_OPENID_CONFIGURATIONS
# identifier: (required) identifier url. {0} will be replaced by username (an
#       input).
# trust_email: (optional, default: False) Some providers let their users
#       change their emails on login page. If the provider doesn't let the user,
#       set it True.
CFG_OPENID_CONFIGURATIONS = {
    'openid': {
        'identifier': '{0}'
    },
    'myvidoop': {
        'identifier': '{0}.myvidoop.com'
    },
    'google': {
        'identifier': 'https://www.google.com/accounts/o8/id',
        'trust_email': True
    },
    'wordpress': {
        'identifier': '{0}.wordpress.com'
    },
    'aol': {
        'identifier': 'openid.aol.com/{0}',
        'trust_email': True
    },
    'myopenid': {
        'identifier': '{0}.myopenid.com'
    },
    'yahoo': {
        'identifier': 'yahoo.com',
        'trust_email': True
    },
    'verisign': {
        'identifier': '{0}.pip.verisignlabs.com'
    },
    'myspace': {
        'identifier': 'www.myspace.com/{0}'
    },
    'livejournal': {
        'identifier': '{0}.livejournal.com'
    },
    'blogger': {
        'identifier': '{0}'
    }
}

# CFG_OAUTH1_CONFIGURATIONS
#
# !!IMPORTANT!!
# While creating an app in the provider site, the callback uri (redirect uri)
# must be in the form of :
# CFG_SITE_SECURE_URL/youraccount/login?login_method=oauth1&provider=PROVIDERNAME
#
# consumer_key: required
#   Consumer key taken from provider.
#
# consumer_secret: required
#   Consumer secret taken from provider.
#
# authorize_url: required
#   The url to redirect the user for authorization
#
# authorize_parameters: optional
#   Additional parameters for authorize_url (ie. scope)
#
# request_token_url: required
#   The url to get request token
#
# access_token_url: required
#   The url to exchange the request token with the access token
#
# request_url: optional
#   The url to gather the user information
#
# request_parameters: optional
#   Additional parameters for request_url
#
# email, nickname: optional
# id: required
#   The location where these properties in the response returned from the
#   provider.
#   example:
#       if the response is:
#                        {
#                            'user': {
#                                'user_name': 'ABC',
#                                'contact': [
#                                    {
#                                        'email': 'abc@def.com'
#                                    }
#                                ]
#                            },
#                           'user_id': 'XXX',
#                        }
#       then:
#       email must be : ['user', 'contact', 0, 'email']
#       id must be: ['user_id']
#       nickname must be: ['user', 'user_name']
#
# debug: optional
#	When debug key is set to 1, after login process, the json object
#	returned from provider is displayed on the screen. It may be used
#	for finding where the id, email or nickname is.
CFG_OAUTH1_CONFIGURATIONS = {
    'twitter': {
        'consumer_key' : '',
        'consumer_secret' : '',
        'request_token_url' : 'https://api.twitter.com/oauth/request_token',
        'access_token_url' : 'https://api.twitter.com/oauth/access_token',
        'authorize_url' : 'https://api.twitter.com/oauth/authorize',
        'id': ['user_id'],
        'nickname': ['screen_name']
    },
    'flickr': {
        'consumer_key' : '',
        'consumer_secret' : '',
        'request_token_url' : 'http://www.flickr.com/services/oauth/request_token',
        'access_token_url' : 'http://www.flickr.com/services/oauth/access_token',
        'authorize_url' : 'http://www.flickr.com/services/oauth/authorize',
        'authorize_parameters': {
            'perms': 'read'
        },
        'nickname': ['username'],
        'id': ['user_nsid']
    },
    'linkedin': {
        'consumer_key' : '',
        'consumer_secret' : '',
        'request_token_url' : 'https://api.linkedin.com/uas/oauth/requestToken',
        'access_token_url' : 'https://api.linkedin.com/uas/oauth/accessToken',
        'authorize_url' : 'https://www.linkedin.com/uas/oauth/authorize',
        'request_url': 'http://api.linkedin.com/v1/people/~:(id)',
        'request_parameters': {
            'format': 'json'
        },
        'id': ['id']
    }
}

# CFG_OAUTH2_CONFIGURATIONS
#
# !!IMPORTANT!!
# While creating an app in the provider site, the callback uri (redirect uri)
# must be in the form of :
# CFG_SITE_SECURE_URL/youraccount/login?login_method=oauth2&provider=PROVIDERNAME
#
# consumer_key: required
#   Consumer key taken from provider.
#
# consumer_secret: required
#   Consumer secret taken from provider.
#
# authorize_url: required
#   The url to redirect the user for authorization
#
# authorize_parameters:
#   Additional parameters for authorize_url (like scope)
#
# access_token_url: required
#   The url to get the access token.
#
# request_url: required
#   The url to gather the user information.
#       {access_token} will be replaced by access token
#
# email, nickname: optional
# id: required
#   The location where these properties in the response returned from the
#   provider.
#       !! See the example in CFG_OAUTH1_CONFIGURATIONS !!
#
# debug: optional
#	When debug key is set to 1, after login process, the json object
#	returned from provider is displayed on the screen. It may be used
#	for finding where the id, email or nickname is.
CFG_OAUTH2_CONFIGURATIONS =  {
    'facebook': {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token_url': 'https://graph.facebook.com/oauth/access_token',
        'authorize_url': 'https://www.facebook.com/dialog/oauth',
        'authorize_parameters': {
            'scope': 'email'
        },
        'request_url' : 'https://graph.facebook.com/me?access_token={access_token}',
        'email': ['email'],
        'id': ['id'],
        'nickname': ['username']
    },
    'foursquare': {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token_url': 'https://foursquare.com/oauth2/access_token',
        'authorize_url': 'https://foursquare.com/oauth2/authorize',
        'request_url': 'https://api.foursquare.com/v2/users/self?oauth_token={access_token}',
        'id': ['response', 'user', 'id'],
        'email': ['response', 'user', 'contact' ,'email']
    },
    'yammer': {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token_url': 'https://www.yammer.com/oauth2/access_token.json',
        'authorize_url': 'https://www.yammer.com/dialog/oauth',
        'request_url': 'https://www.yammer.com/oauth2/access_token.json?access_token={access_token}',
        'email':['user', 'contact', 'email_addresses', 0, 'address'],
        'id': ['user', 'id'],
        'nickname': ['user', 'name']
    },
    'googleoauth2': {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token_url': 'https://accounts.google.com/o/oauth2/token',
        'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        'authorize_parameters': {
            'scope': 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'
        },
        'request_url': 'https://www.googleapis.com/oauth2/v1/userinfo?access_token={access_token}',
        'email':['email'],
        'id': ['id']
    },
    'instagram': {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token_url': 'https://api.instagram.com/oauth/access_token',
        'authorize_url': 'https://api.instagram.com/oauth/authorize/',
        'authorize_parameters': {
            'scope': 'basic'
        },
        'id': ['user', 'id'],
        'nickname': ['user', 'username']
    },
    'orcid': {
        'consumer_key': '',
        'consumer_secret': '',
        'authorize_url': 'http://sandbox-1.orcid.org/oauth/authorize',
        'access_token_url': 'http://api.sandbox-1.orcid.org/oauth/token',
        'request_url': 'http://api.sandbox-1.orcid.org/{id}/orcid-profile',
        'authorize_parameters': {
            'scope': '/orcid-profile/read-limited',
            'response_type': 'code',
            'access_type': 'offline',
        },
        'id': ['orcid'],
    }
}

# Let's override OpenID/OAuth1/OAuth2 configuration from invenio(-local).conf
CFG_OPENID_PROVIDERS = config['CFG_OPENID_PROVIDERS']
CFG_OAUTH1_PROVIDERS = config['CFG_OAUTH1_PROVIDERS']
CFG_OAUTH2_PROVIDERS = config['CFG_OAUTH2_PROVIDERS']
if config['CFG_OPENID_CONFIGURATIONS']:
    for provider, configuration in config['CFG_OPENID_CONFIGURATIONS'].items():
        if provider in CFG_OPENID_CONFIGURATIONS:
            CFG_OPENID_CONFIGURATIONS[provider].update(configuration)
        else:
            CFG_OPENID_CONFIGURATIONS[provider] = configuration
if config['CFG_OAUTH1_CONFIGURATIONS']:
    for provider, configuration in config['CFG_OAUTH1_CONFIGURATIONS'].items():
        if provider in CFG_OAUTH1_CONFIGURATIONS:
            CFG_OAUTH1_CONFIGURATIONS[provider].update(configuration)
        else:
            CFG_OAUTH1_CONFIGURATIONS[provider] = configuration
if config['CFG_OAUTH2_CONFIGURATIONS']:
    for provider, configuration in config['CFG_OAUTH2_CONFIGURATIONS'].items():
        if provider in CFG_OAUTH2_CONFIGURATIONS:
            CFG_OAUTH2_CONFIGURATIONS[provider].update(configuration)
        else:
            CFG_OAUTH2_CONFIGURATIONS[provider] = configuration

# If OpenID authentication is enabled, add 'openid' to login methods
CFG_OPENID_AUTHENTICATION = bool(CFG_OPENID_PROVIDERS)
if CFG_OPENID_AUTHENTICATION:
    from invenio.legacy.external_authentication.openid import ExternalOpenID
    CFG_EXTERNAL_AUTHENTICATION['openid'] = ExternalOpenID(enforce_external_nicknames=True)

# If OAuth1 authentication is enabled, add 'oauth1' to login methods.
CFG_OAUTH1_AUTHENTICATION = bool(CFG_OAUTH1_PROVIDERS)
if CFG_OAUTH1_AUTHENTICATION:
    from invenio.legacy.external_authentication.oauth1 import ExternalOAuth1
    CFG_EXTERNAL_AUTHENTICATION['oauth1'] = ExternalOAuth1(enforce_external_nicknames=True)

# If OAuth2 authentication is enabled, add 'oauth2' to login methods.
CFG_OAUTH2_AUTHENTICATION = bool(CFG_OAUTH2_PROVIDERS)
if CFG_OAUTH2_AUTHENTICATION:
    from invenio.legacy.external_authentication.oauth2 import ExternalOAuth2
    CFG_EXTERNAL_AUTHENTICATION['oauth2'] = ExternalOAuth2(enforce_external_nicknames=True)


# If using SSO, this is the number of seconds after which the keep-alive
# SSO handler is pinged again to provide fresh SSO information.
CFG_EXTERNAL_AUTH_SSO_REFRESH = 600

# default data for the add_default_settings function
# Note: by default the definition is set to deny any. This won't be a problem
# because userid directly connected with roles will still be allowed.
# roles
#           name          description          definition
DEF_ROLES = ((SUPERADMINROLE, 'superuser with all rights', 'deny any'),
             (WEBACCESSADMINROLE, 'WebAccess administrator', 'deny any'),
             ('anyuser', 'Any user', 'allow any'),
             ('basketusers', 'Users who can use baskets', 'allow any'),
             ('loanusers', 'Users who can use loans', 'allow any'),
             ('groupusers', 'Users who can use groups', 'allow any'),
             ('alertusers', 'Users who can use alerts', 'allow any'),
             ('messageusers', 'Users who can use messages', 'allow any'),
             ('holdingsusers', 'Users who can view holdings', 'allow any'),
             ('statisticsusers', 'Users who can view statistics', 'allow any'),
             ('claimpaperusers', 'Users who can perform changes to their own paper attributions without the need for an operator\'s approval', 'allow any'),
             ('claimpaperoperators', 'Users who can perform changes to _all_ paper attributions without the need for an operator\'s approval', 'deny any'),
             ('paperclaimviewers', 'Users who can view "claim my paper" facilities.', 'allow all'),
             ('paperattributionviewers', 'Users who can view "attribute this paper" facilities', 'allow all'),
             ('paperattributionlinkviewers', 'Users who can see attribution links in the search', 'allow all'),
             ('authorlistusers', 'Users who can user Authorlist tools', 'deny all'),
             ('holdingpenusers', 'Users who can view Holding Pen', 'deny all'),
             )


# users
# list of e-mail addresses
DEF_USERS = []

# actions
#            name                  desc     allowedkeywords   optional
DEF_ACTIONS = (
               ('cfgwebsearch', 'configure WebSearch', '', 'no'),
               ('cfgbibformat', 'configure BibFormat', '', 'no'),
               ('cfgbibknowledge', 'configure BibKnowledge', '', 'no'),
               ('cfgwebsubmit', 'configure WebSubmit', '', 'no'),
               ('cfgbibrank', 'configure BibRank', '', 'no'),
               ('cfgwebcomment', 'configure WebComment', '', 'no'),
               ('cfgweblinkback', 'configure WebLinkback' , '', 'no'),
               ('cfgoaiharvest', 'configure OAI Harvest', '', 'no'),
               ('cfgoairepository', 'configure OAI Repository', '', 'no'),
               ('cfgbibindex', 'configure BibIndex', '', 'no'),
               ('cfgbibexport', 'configure BibExport', '', 'no'),
               ('cfgrobotkeys', 'configure Robot keys', 'login_method,robot', 'yes'),
               ('cfgbibsort', 'configure BibSort', '', 'no'),
               ('runbibindex', 'run BibIndex', '', 'no'),
               ('runbibupload', 'run BibUpload', '', 'no'),
               ('runwebcoll', 'run webcoll', 'collection', 'yes'),
               ('runbibformat', 'run BibFormat', 'format', 'yes'),
               ('runbibclassify', 'run BibClassify', 'taxonomy', 'yes'),
               ('runbibtaskex', 'run BibTaskEx example', '', 'no'),
               ('runbibrank', 'run BibRank', '', 'no'),
               ('runoaiharvest', 'run oaiharvest task', '', 'no'),
               ('runoairepository', 'run oairepositoryupdater task', '', 'no'),
               ('runbibedit', 'run Record Editor', 'collection', 'yes'),
               ('runbibeditmulti', 'run Multi-Record Editor', '', 'no'),
               ('runbibdocfile', 'run Document File Manager', '', 'no'),
               ('runbibmerge', 'run Record Merger', '', 'no'),
               ('runbibswordclient', 'run BibSword client', '', 'no'),
               ('runwebstatadmin', 'run WebStadAdmin', '', 'no'),
               ('runinveniogc', 'run InvenioGC', '', 'no'),
               ('runbibexport', 'run BibExport', '', 'no'),
               ('runauthorlist', 'run Authorlist tools', '', 'no'),
               ('referee', 'referee document type doctype/category categ', 'doctype,categ', 'yes'),
               ('submit', 'use webSubmit', 'doctype,act,categ', 'yes'),
               ('viewrestrdoc', 'view restricted document', 'status', 'no'),
               ('viewrestrcomment', 'view restricted comment', 'status', 'no'),
               (WEBACCESSACTION, 'configure WebAccess', '', 'no'),
               (DELEGATEADDUSERROLE, 'delegate subroles inside WebAccess', 'role', 'no'),
               (VIEWRESTRCOLL, 'view restricted collection', 'collection', 'no'),
               ('cfgwebjournal', 'configure WebJournal', 'name,with_editor_rights', 'no'),
               ('viewcomment', 'view comments', 'collection', 'no'),
               ('viewlinkbacks', 'view linkbacks', 'collection', 'no'),
               ('sendcomment', 'send comments', 'collection', 'no'),
               ('attachcommentfile', 'attach files to comments', 'collection', 'no'),
               ('attachsubmissionfile', 'upload files to drop box during submission', '', 'no'),
               ('cfgbibexport', 'configure BibExport', '', 'no'),
               ('runbibexport', 'run BibExport', '', 'no'),
               ('usebaskets', 'use baskets', '', 'no'),
               ('useloans', 'use loans', '', 'no'),
               ('usegroups', 'use groups', '', 'no'),
               ('usealerts', 'use alerts', '', 'no'),
               ('usemessages', 'use messages', '', 'no'),
               ('viewholdings', 'view holdings', 'collection', 'yes'),
               ('viewstatistics', 'view statistics', 'collection', 'yes'),
               ('runbibcirculation', 'run BibCirculation', '', 'no'),
               ('moderatecomments', 'moderate comments', 'collection', 'no'),
               ('moderatelinkbacks', 'moderate linkbacks', 'collection', 'no'),
               ('runbatchuploader', 'run batchuploader', 'collection', 'yes'),
               ('runbibtasklet', 'run BibTaskLet', '', 'no'),
               ('claimpaper_view_pid_universe', 'View the Claim Paper interface', '', 'no'),
               ('claimpaper_claim_own_papers', 'Clam papers to his own personID', '', 'no'),
               ('claimpaper_claim_others_papers', 'Claim papers for others', '', 'no'),
               ('claimpaper_change_own_data', 'Change data associated to his own person ID', '', 'no'),
               ('claimpaper_change_others_data', 'Change data of any person ID', '', 'no'),
               ('runbibtasklet', 'run BibTaskLet', '', 'no'),
               ('cfgbibsched', 'configure BibSched', '', 'no'),
               ('runinfomanager', 'run Info Space Manager', '', 'no')
              )


from invenio.ext.principal.wrappers import Action

for action in DEF_ACTIONS:
    type(action[0], (Action, ), {
        '__doc__': action[1],
        'allowedkeywords': action[2].split(','),
        'optional': action[3] == "yes"
    })

# Default authorizations
#              role          action        arguments
DEF_AUTHS = (('basketusers', 'usebaskets', {}),
             ('loanusers', 'useloans', {}),
             ('groupusers', 'usegroups', {}),
             ('alertusers', 'usealerts', {}),
             ('messageusers', 'usemessages', {}),
             ('holdingsusers', 'viewholdings', {}),
             ('statisticsusers', 'viewstatistics', {}),
             ('authorlistusers', 'runauthorlist', {}),
             ('claimpaperusers', 'claimpaper_view_pid_universe', {}),
             ('claimpaperoperators', 'claimpaper_view_pid_universe', {}),
             ('claimpaperusers', 'claimpaper_claim_own_papers', {}),
             ('claimpaperoperators', 'claimpaper_claim_own_papers', {}),
             ('claimpaperoperators', 'claimpaper_claim_others_papers', {}),
             ('claimpaperusers', 'claimpaper_change_own_data', {}),
             ('claimpaperoperators', 'claimpaper_change_own_data', {}),
             ('claimpaperoperators', 'claimpaper_change_others_data', {}),
             ('holdingpenusers', 'viewholdingpen', {}),
             )


# Activities (i.e. actions) for which exists an administrative web interface.
CFG_ACC_ACTIVITIES_URLS = {
    'runbibedit' : (_("Run Record Editor"), "%s/%s/edit/?ln=%%s" % (CFG_SITE_URL, CFG_SITE_RECORD)),
    'runbibeditmulti' : (_("Run Multi-Record Editor"), "%s/%s/multiedit/?ln=%%s" % (CFG_SITE_URL, CFG_SITE_RECORD)),
    'runbibdocfile' : (_("Run Document File Manager"), "%s/%s/managedocfiles?ln=%%s" % (CFG_SITE_URL, CFG_SITE_RECORD)),
    'runbibmerge' : (_("Run Record Merger"), "%s/%s/merge/?ln=%%s" % (CFG_SITE_URL, CFG_SITE_RECORD)),
    'runbibswordclient' : (_("Run BibSword client"), "%s/bibsword/?ln=%%s" % CFG_SITE_URL),
    'cfgbibknowledge' : (_("Configure BibKnowledge"), "%s/kb?ln=%%s" % CFG_SITE_URL),
    'cfgbibformat' : (_("Configure BibFormat"), "%s/admin/bibformat/bibformatadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgoaiharvest' : (_("Configure OAI Harvest"), "%s/admin/oaiharvest/oaiharvestadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgoairepository' : (_("Configure OAI Repository"), "%s/admin/oairepository/oairepositoryadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgbibindex' : (_("Configure BibIndex"), "%s/admin/bibindex/bibindexadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgbibrank' : (_("Configure BibRank"), "%s/admin/bibrank/bibrankadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgwebaccess' : (_("Configure WebAccess"), "%s/admin/webaccess/webaccessadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgwebcomment' : (_("Configure WebComment"), "%s/admin/webcomment/webcommentadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgweblinkback' : (_("Configure WebLinkback"), "%s/admin/weblinkback/weblinkbackadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgwebsearch' : (_("Configure WebSearch"), "%s/admin/websearch/websearchadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgwebsubmit' : (_("Configure WebSubmit"), "%s/admin/websubmit/websubmitadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgwebjournal' : (_("Configure WebJournal"), "%s/admin/webjournal/webjournaladmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgbibsort' : (_("Configure BibSort"), "%s/admin/bibsort/bibsortadmin.py?ln=%%s" % CFG_SITE_URL),
    'runbibcirculation' : (_("Run BibCirculation"), "%s/admin/bibcirculation/bibcirculationadmin.py?ln=%%s" % CFG_SITE_URL),
    'runbatchuploader' : (_("Run Batch Uploader"), "%s/batchuploader/metadata?ln=%%s" % CFG_SITE_URL),
    'runinfomanager' : (_("Run Info Space Manager"), "%s/info/manage?ln=%%s" % CFG_SITE_URL),
    'claimpaper_claim_others_papers' : (_("Run Person/Author Manager"), "%s/author/search?ln=%%s" % CFG_SITE_URL)
}

CFG_WEBACCESS_MSGS = {
    0: 'Try to <a href="%s/youraccount/login?referer=%%s">login</a> with another account.' % (CFG_SITE_SECURE_URL),
    1: '<br />If you think this is not correct, please contact: <a href="mailto:%s">%s</a>' % (CFG_SITE_SUPPORT_EMAIL, CFG_SITE_SUPPORT_EMAIL),
    2: '<br />If you have any questions, please write to <a href="mailto:%s">%s</a>' % (CFG_SITE_SUPPORT_EMAIL, CFG_SITE_SUPPORT_EMAIL),
    3: 'Guest users are not allowed, please <a href="%s/youraccount/login">login</a>.' % CFG_SITE_SECURE_URL,
    4: 'The site is temporarily closed for maintenance.  Please come back soon.',
    5: 'Authorization failure',
    6: '%s temporarily closed' % CFG_SITE_NAME,
    7: 'This functionality is temporarily closed due to server maintenance. Please use only the search engine in the meantime.',
    8: 'Functionality temporarily closed',
    9: '<br />If you think this is not correct, please contact: <a href="mailto:%s">%s</a>',
   10: '<br />You might also want to check <a href="%s">%s</a>',
}

CFG_WEBACCESS_WARNING_MSGS = {
    0: 'Authorization granted',
    1: 'You are not authorized to perform this action.',
    2: 'You are not authorized to perform any action.',
    3: 'The action %s does not exist.',
    4: 'Unexpected error occurred.',
    5: 'Missing mandatory keyword argument(s) for this action.',
    6: 'Guest accounts are not authorized to perform this action.',
    7: 'Not enough arguments, user ID and action name required.',
    8: 'Incorrect keyword argument(s) for this action.',
    9: """Account '%s' is not yet activated.""",
    10: """You were not authorized by the authentication method '%s'.""",
    11: """The selected login method '%s' is not the default method for this account, please try another one.""",
    12: """Selected login method '%s' does not exist.""",
    13: """Could not register '%s' account.""",
    14: """Could not login using '%s', because this user is unknown.""",
    15: """Could not login using your '%s' account, because you have introduced a wrong password.""",
    16: """External authentication troubles using '%s' (maybe temporary network problems).""",
    17: """You have not yet confirmed the email address for the '%s' authentication method.""",
    18: """The administrator has not yet activated your account for the '%s' authentication method.""",
    19: """The site is having troubles in sending you an email for confirming your email address. The error has been logged and will be taken care of as soon as possible.""",
    20: """No roles are authorized to perform action %s with the given parameters.""",
    21: """Verification cancelled""",
    22: """Verification failed. Please try again or use another provider to login""",
    23: """Verification failed. It is probably because the configuration isn't set properly. Please contact with the <a href="mailto:%s">administator</a>""" % CFG_SITE_ADMIN_EMAIL
}

