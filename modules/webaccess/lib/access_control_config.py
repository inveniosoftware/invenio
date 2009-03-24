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

from invenio.config import CFG_SITE_NAME, CFG_SITE_URL, CFG_SITE_LANG, \
     CFG_SITE_SECURE_URL, CFG_SITE_SUPPORT_EMAIL, CFG_CERN_SITE
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
VIEWRESTRCOLL     = 'viewrestrcoll'


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


# List of tags containing (multiple) emails of users who should authorize
# to access the corresponding record regardless of collection restrictions.
if CFG_CERN_SITE:
    CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS=['859__f', '270__m']
else:
    CFG_ACC_GRANT_AUTHOR_RIGHTS_TO_EMAILS_IN_TAGS=['8560_f']

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
             (WEBACCESSADMINROLE, 'WebAccess administrator', 'deny any'),
             ('anyuser', 'Any user', 'allow any'),
             ('basketusers', 'Users who can use baskets', 'allow any'),
             ('loanusers', 'Users who can use loans', 'allow any'),
             ('groupusers', 'Users who can use groups', 'allow any'),
             ('alertusers', 'Users who can use alerts', 'allow any'),
             ('messageusers', 'Users who can use messages', 'allow any'),
             ('holdingsusers', 'Users who can view holdings', 'allow any'),
             ('statisticsusers', 'Users who can view statistics', 'allow any'))

# Demo site roles
DEF_DEMO_ROLES = (('photocurator', 'Photo collection curator', 'deny any'),
                  ('thesesviewer', 'Theses viewer', 'allow group "Theses viewers"\nallow apache_group "theses"'),
                  ('thesescurator', 'Theses collection curator', 'deny any'),
                  ('referee_DEMOBOO_*', 'Book collection curator', 'deny any'),
                  ('restrictedpicturesviewer', 'Restricted pictures viewer', 'deny any'),
                  ('curator', 'Curator', 'deny any'),
                  ('basketusers', 'User who can use baskets', 'deny email "hyde@cds.cern.ch"\nallow any'))

DEF_DEMO_USER_ROLES = (('jekyll@cds.cern.ch', 'thesesviewer'),
                       ('dorian.gray@cds.cern.ch', 'referee_DEMOBOO_*'),
                       ('balthasar.montague@cds.cern.ch', 'curator'),
                       ('romeo.montague@cds.cern.ch', 'restrictedpicturesviewer'),
                       ('romeo.montague@cds.cern.ch', 'thesescurator'),
                       ('juliet.capulet@cds.cern.ch', 'restrictedpicturesviewer'),
                       ('juliet.capulet@cds.cern.ch', 'photocurator'))

# users
# list of e-mail addresses
DEF_USERS = []

# actions
#            name                  desc     allowedkeywords   optional
DEF_ACTIONS = (
               ('cfgwebsearch', 'configure WebSearch', '', 'no'),
               ('cfgbibformat', 'configure BibFormat', '', 'no'),
               ('cfgwebsubmit', 'configure WebSubmit', '', 'no'),
               ('cfgbibrank', 'configure BibRank', '', 'no'),
               ('cfgwebcomment', 'configure WebComment', '', 'no'),
               ('cfgbibharvest', 'configure BibHarvest', '', 'no'),
               ('cfgoairepository', 'configure OAI Repository', '', 'no'),
               ('cfgbibindex', 'configure BibIndex', '', 'no'),
               ('runbibindex', 'run BibIndex', '', 'no'),
               ('runbibupload', 'run BibUpload', '', 'no'),
               ('runwebcoll', 'run webcoll', 'collection', 'yes'),
               ('runbibformat', 'run BibFormat', 'format', 'yes'),
               ('runbibclassify', 'run BibClassify', 'taxonomy', 'yes'),
               ('runbibtaskex', 'run BibTaskEx example', '', 'no'),
               ('runbibrank', 'run BibRank', '', 'no'),
               ('runoaiharvest', 'run oaiharvest task', '', 'no'),
               ('runoaiarchive', 'run oaiarchive task', '', 'no'),
               ('runbibedit', 'run BibEdit', 'collection', 'yes'),
               ('runwebstatadmin', 'run WebStadAdmin', '', 'no'),
               ('runinveniogc', 'run InvenioGC', '', 'no'),
               ('referee', 'referee document type doctype/category categ', 'doctype,categ',    'yes'),
               ('submit', 'use webSubmit', 'doctype,act', 'yes'),
               ('viewrestrdoc', 'view restricted document', 'status', 'no'),
               (WEBACCESSACTION, 'configure WebAccess', '', 'no'),
               (DELEGATEADDUSERROLE, 'delegate subroles inside WebAccess', 'role',          'no'),
               (VIEWRESTRCOLL, 'view restricted collection', 'collection', 'no'),
               ('cfgwebjournal', 'configure WebJournal', 'name', 'yes'),
               ('viewcomment', 'view comments', 'collection', 'no'),
               ('sendcomment', 'send comments', 'collection', 'no'),
               ('attachcommentfile', 'attach files to comments', 'collection', 'no'),
               ('attachsubmissionfile', 'upload files to drop box during submission', '', 'no'),
               ('cfgbibexport', 'configure BibExport', '', 'no'),
               ('runbibexport', 'run BibExport', '', 'no'),
               ('fulltext', 'administrate Fulltext', '', 'no'),
               ('usebaskets', 'use baskets', '', 'no'),
               ('useloans', 'use loans', '', 'no'),
               ('usegroups', 'use groups', '', 'no'),
               ('usealerts', 'use alerts', '', 'no'),
               ('usemessages', 'use messages', '', 'no'),
               ('viewholdings', 'view holdings', 'collection', 'yes'),
               ('viewstatistics', 'view statistics', 'collection', 'yes')
              )

# Default authorizations
#              role          action       arglistid  optional  arguments
DEF_AUTHS = (('basketusers', 'usebaskets', -1, 0, {}),
             ('loanusers', 'useloans', -1, 0, {}),
             ('groupusers', 'usegroups', -1, 0, {}),
             ('alertusers', 'usealerts', -1, 0, {}),
             ('messageusers', 'usemessages', -1, 0, {}),
             ('holdingsusers', 'viewholdings', -1, 1, {}),
             ('statisticsusers', 'viewstatistics', -1, 1, {}))

# Demo site authorizations
#              role          action       arglistid  optional  arguments
DEF_DEMO_AUTHS = (
             ('photocurator', 'runwebcoll', -1, 0, {'collection': 'Pictures'}),
             ('restrictedpicturesviewer', 'viewrestrdoc', -1, 0, {'status': 'restricted_picture'}),
             ('thesesviewer', VIEWRESTRCOLL, -1, 0, {'collection': 'Theses'}),
             ('referee_DEMOBOO_*', 'referee', -1, 0, {'doctype': 'DEMOBOO', 'categ': '*'}),
             ('curator', 'runbibedit', -1, 1, {}),
             ('thesescurator', 'runbibedit', -1, 0, {'collection': 'Theses'}),
             ('thesescurator', VIEWRESTRCOLL, -1, 0, {'collection': 'Theses'}),
             ('photocurator', 'runbibedit', -1, 0, {'collection': 'Pictures'}),
             ('referee_DEMOBOO_*', 'runbibedit', -1, 0, {'collection': 'Books'})
            )

_ = gettext_set_language(CFG_SITE_LANG)
# Activities (i.e. actions) for which it exist an administrative web interface.
CFG_ACC_ACTIVITIES_URLS = {
    'runbibedit' : (_("Run BibEdit"), "%s/record/edit/?ln=%%s" % CFG_SITE_URL),
    'cfgbibformat' : (_("Configure BibFormat"), "%s/admin/bibformat/bibformatadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgbibharvest' : (_("Configure BibHarvest"), "%s/admin/bibharvest/bibharvestadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgoairepository' : (_("Configure OAI Repository"), "%s/admin/bibharvest/oaiarchiveadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgbibindex' : (_("Configure BibIndex"), "%s/admin/bibindex/bibindexadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgbibrank' : (_("Configure BibRank"), "%s/admin/bibrank/bibrankadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgwebaccess' : (_("Configure WebAccess"), "%s/admin/webaccess/webaccessadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgwebcomment' : (_("Configure WebComment"), "%s/admin/webcomment/webcommentadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgwebsearch' : (_("Configure WebSearch"), "%s/admin/websearch/websearchadmin.py?ln=%%s" % CFG_SITE_URL),
    'cfgwebsubmit' : (_("Configure WebSubmit"), "%s/admin/websubmit/websubmitadmin.py?ln=%%s" % CFG_SITE_URL),
    'runbibcirculation' : (_("Run BibCirculation"), "%s/admin/bibcirculation/bibcirculationadmin.py?ln=%%s" % CFG_SITE_URL)
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
                               19: """Error(19): The site is having troubles in sending you an email for confirming your email address. The error has been logged and will be taken care of as soon as possible.""",
                               20: """Error(20): No roles are authorized to perform action %s with the given parameters."""
        }

