## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

"""CDS Invenio Access Control Config. """

__revision__ = \
    "$Id$"

# pylint: disable-msg=C0301

from invenio.config import cdsname, weburl, sweburl, supportemail, CFG_CERN_SITE
import cPickle
from zlib import compress
from invenio.messages import gettext_set_language


class InvenioWebAccessFireroleError(Exception):
    """Just an Exception to discover if it's a FireRole problem"""
    pass

# VALUES TO BE EXPORTED
# CURRENTLY USED BY THE FILES access_control_engine.py access_control_admin.py webaccessadmin_lib.py

# name of the role giving superadmin rights
SUPERADMINROLE      = 'superadmin'

# name of the webaccess webadmin role
WEBACCESSADMINROLE  = 'webaccessadmin'

# name of the action allowing roles to access the web administrator interface
WEBACCESSACTION     = 'cfgwebaccess'

# name of the action allowing roles to access the web administrator interface
VIEWRESTRCOLL     = 'accrestrcoll'


# name of the action allowing roles to delegate the rights to other roles
# ex: libraryadmin to delegate libraryworker
DELEGATEADDUSERROLE = 'accdelegaterole'

# max number of users to display in the drop down selects
MAXSELECTUSERS = 25

# max number of users to display in a page (mainly for user area)
MAXPAGEUSERS = 25

""" Serialized compiled default role definition"""
CFG_ACC_EMPTY_ROLE_DEFINITION_SER=compress(cPickle.dumps((False, False, ()), -1))

""" Source of the default role definition"""
CFG_ACC_EMPTY_ROLE_DEFINITION_SRC='deny any'



# Use external source for access control?
# Atleast one must be added
# Adviced not to change the name, since it is used to identify the account
# Format is:   System name: (System class, Default True/Flase), atleast one
# must be default
CFG_EXTERNAL_AUTHENTICATION = {"Local": (None, True)}

# Variables to set to the SSO Authentication name if using SSO
CFG_EXTERNAL_AUTH_USING_SSO = False
CFG_EXTERNAL_AUTH_LOGOUT_SSO = None

if CFG_CERN_SITE:
    if False: #FIXME set this to True when we deploy SSO at CERN
        import external_authentication_sso as ea_sso
        CFG_EXTERNAL_AUTH_USING_SSO = "CERN"
        # Link to reach in order to logout from SSO
        CFG_EXTERNAL_AUTH_LOGOUT_SSO = 'https://login.cern.ch/adfs/ls/?wa=wsignout1.0'
        CFG_EXTERNAL_AUTHENTICATION = {CFG_EXTERNAL_AUTH_USING_SSO : (ea_sso.ExternalAuthSSO(), True)}
    else:
        import external_authentication_cern as ea_cern
        CFG_EXTERNAL_AUTHENTICATION = {"Local": (None, False), \
        "CERN": (ea_cern.ExternalAuthCern(), True)}





# default data for the add_default_settings function
# Note: by default the definition is set to deny any. This won't be a problem
# because userid directly connected with roles will still be allowed.
# roles
#           name          description          definition
DEF_ROLES = ((SUPERADMINROLE, 'superuser with all rights', 'deny any'),
             ('photoadmin',   'Photo collection administrator', 'deny any'),
             (WEBACCESSADMINROLE,     'WebAccess administrator', 'deny any'))

# users
# list of e-mail addresses
DEF_USERS = []

# actions
#            name                  desc     allowedkeywords   optional
DEF_ACTIONS = (
               ('cfgwebsearch',         'configure WebSearch',       '',              'no'),
               ('cfgbibformat',         'configure BibFormat',       '',              'no'),
               ('cfgwebsubmit',         'configure WebSubmit',       '',              'no'),
               ('runbibindex',          'run BibIndex',       '',              'no'),
               ('runbibupload',         'run BibUpload',       '',              'no'),
               ('runwebcoll',           'run webcoll',       'collection',    'yes'),
               ('runbibformat',         'run BibFormat',       'format',        'yes'),
               (WEBACCESSACTION,        'configure WebAccess',       '',              'no'),
               (DELEGATEADDUSERROLE,    'delegate subroles inside WebAccess',       'role',          'no'),
               (VIEWRESTRCOLL, 'view restricted collection', 'collection', 'no'),
               ('runbibtaskex',         'run BibTaskEx example',       '',              'no'),
               ('referee',                  'referee document type doctype/category categ', 'doctype,categ',    'yes'),
               ('submit',                   'use webSubmit',    'doctype,act',  'yes'),
               ('runbibrank',         'run BibRank',       '',              'no'),
               ('cfgbibrank',         'configure BibRank',       '',              'no'),
               ('cfgbibharvest',         'configure BibHarvest',       '',              'no'),
               ('runoaiharvest',         'run oaiharvest task',       '',              'no'),
               ('cfgwebcomment',         'configure WebComment',       '',              'no'),
               ('runoaiarchive',         'run oaiarchive task',       '',              'no'),
               ('runbibedit',         'run BibEdit',       '',              'no'),
               ('runwebstatadmin', 'run WebStadAdmin', '', 'no'),
               ('viewrestrdoc', 'view restricted document', 'status', 'no'),
              )

# authorizations
#          role              action          arglistid  optional   arguments
DEF_AUTHS = (
             (SUPERADMINROLE,    'cfgwebsearch',         -1,      0,       {}),
             (SUPERADMINROLE,    'cfgbibformat',         -1,      0,       {}),
             (SUPERADMINROLE,    'cfgwebsubmit',         -1,      0,       {}),
             (SUPERADMINROLE,    'runbibindex',          -1,      0,       {}),
             (SUPERADMINROLE,    'runbibupload',         -1,      0,       {}),
             (SUPERADMINROLE,    'runbibformat',         -1,      1,       {}),
             (SUPERADMINROLE,    WEBACCESSACTION,        -1,      0,       {}),
             ('photoadmin',      'runwebcoll',           -1,      0,       {'collection': 'Pictures'}),
             (WEBACCESSADMINROLE,WEBACCESSACTION,        -1,      0,       {}),
             (SUPERADMINROLE,    'runtaskex',            -1,      0,       {}),
             (SUPERADMINROLE,    'referee',         -1,      1,       {}),
             (SUPERADMINROLE,    'submit',         -1,      1,       {}),
             (SUPERADMINROLE,    'runbibrank',           -1,      0,       {}),
             (SUPERADMINROLE,    'cfgbibrank',           -1,      0,       {}),
             (SUPERADMINROLE,    'cfgbibharvest',           -1,      0,       {}),
             (SUPERADMINROLE,    'runoaiharvest',            -1,      0,       {}),
             (SUPERADMINROLE,    'cfgwebcomment',            -1,      0,       {}),
             (SUPERADMINROLE,    'runoaiarchive',            -1,      0,       {}),
             (SUPERADMINROLE,    'runbibedit',            -1,      0,       {}),
            )


_ = gettext_set_language('en')
CFG_ACC_ACTIVITIES_URLS = {
    'runbibedit' : (_("Run BibEdit"), "%s/admin/bibedit/bibeditadmin.py?ln=%%s" % weburl),
    'cfgbibformat' : (_("Configure BibFormat"), "%s/admin/bibformat/bibformatadmin.py?ln=%%s" % weburl),
    'cfgbibharvest' : (_("Configure BibHarvest"), "%s/admin/bibharvest/?ln=%%s" % weburl),
    'cfgbibindex' : (_("Configure BibIndex"), "%s/admin/bibindex/bibindexadmin.py?ln=%%s" % weburl),
    'cfgbibrank' : (_("Configure BibRank"), "%s/admin/bibrank/bibrankadmin.py?ln=%%s" % weburl),
    'cfgwebaccess' : (_("Configure WebAccess"), "%s/admin/webaccess/webaccessadmin.py?ln=%%s" % weburl),
    'cfgwebcomment' : (_("Configure WebComment"), "%s/admin/webcomment/webcommentadmin.py?ln=%%s" % weburl),
    'cfgwebsearch' : (_("Configure WebSearch"), "%s/admin/websearch/websearchadmin.py?ln=%%s" % weburl),
    'cfgwebsubmit' : (_("Configure WebSubmit"), "%s/admin/websubmit/websubmitadmin.py?ln=%%s" % weburl),
}

CFG_WEBACCESS_MSGS = {
                                0: 'Try to <a href="%s/youraccount/login?referer=%%s">login</a> with another account.' % (sweburl),
                                1: '<br>If you think this is not correct, please contact: <a href="mailto:%s">%s</a>' % (supportemail, supportemail),
                                2: '<br>If you have any questions, please write to <a href="mailto:%s">%s</a>' % (supportemail, supportemail),
                                3: 'Guest users are not allowed, please <a href="%s/youraccount/login">login</a>.' % sweburl,
                                4: 'The site is temporarily closed for maintenance.  Please come back soon.',
                                5: 'Authorization failure',
                                6: '%s temporarily closed' % cdsname,
                                7: 'This functionality is temporarily closed due to server maintenance. Please use only the search engine in the meantime.',
                                8: 'Functionality temporarily closed'
        }

CFG_WEBACCESS_WARNING_MSGS = {
                                0: 'Authorization granted',
                                1: 'Error(1): You are not authorized to perform this action.',
                                2: 'Error(2): You are not authorized to perform any action.',
                                3: 'Error(3): The action %s does not exist.',
                                4: 'Error(4): Unexpected error occurred.',
                                5: 'Error(5): Missing mandatory keyword argument(s) for this action.',
                                6: 'Error(6): Guest accounts are not authorized to perform this action.',
                                7: 'Error(7): Not enough arguments, user ID and action name required.',
                                8: 'Error(8): Incorrect keyword argument(s) for this action.',
                                9: """Error(9): Account '%s' is not yet activated.""",
                               10: """Error(10): You were not authorized by the authentication method '%s'.""",
                               11: """Error(11): The selected login method '%s' is not the default method for this account, please try another one.""",
                               12: """Error(12): Selected login method '%s' does not exist.""",
                               13: """Error(13): Could not register '%s' account.""",
                               14: """Error(14): Could not login using '%s', because this user is unknown.""",
                               15: """Error(15): Could not login using your '%s' account, because you have introduced a wrong password.""",
                               16: """Error(16): External authentication troubles using '%s' (maybe temporary network problems).""",
                               17: """Error(17): You have not yet confirmed the email address for the '%s' authentication method.""",
                               18: """Error(18): The administrator has not yet activated your account for the '%s' authentication method.""",
                               19: """Error(19): The site is having troubles in sending you an email for confirming your email address. The error has been logged and will be taken care of as soon as possible."""
        }

