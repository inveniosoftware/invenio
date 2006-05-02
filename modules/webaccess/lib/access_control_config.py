## $Id$
##
## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002, 2003, 2004, 2005, 2006 CERN.
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

"""CDSware Access Control Config. """

__version__ = "$Id$"

## global configuration parameters:
from cdsware.config import *

## local configuration parameters:

from cdsware.external_authentication import *

# VALUES TO BE EXPORTED
# CURRENTLY USED BY THE FILES access_control_engine.py access_control_admin.py webaccessadmin_lib.py

# name of the role giving superadmin rights
SUPERADMINROLE      = 'superadmin'
# name of the webaccess webadmin role
WEBACCESSADMINROLE  = 'webaccessadmin'
# name of the action allowing roles to access the web administrator interface
WEBACCESSACTION     = 'cfgwebaccess'
# name of the action allowing roles to delegate the rights to other roles
# ex: libraryadmin to delegate libraryworker
DELEGATEADDUSERROLE = 'accdelegaterole'
# max number of users to display in the drop down selects
MAXSELECTUSERS = 25
# max number of users to display in a page (mainly for user area)
MAXPAGEUSERS = 25
# Use external source for access control?
# Atleast one must be added
# Adviced not to change the name, since it is used to identify the account
# Format is:   System name: (System class, Default True/Flase), atleast one must be default
CFG_EXTERNAL_AUTHENTICATION = {"%s (internal)" % cdsname: (None, True)}
#CFG_EXTERNAL_AUTHENTICATION = {"%s (internal)" % cdsname: (None, True), "CERN NICE (external)": (external_auth_nice(), False)}

# default data for the add_default_settings function
# roles
#           name          description
def_roles = ((SUPERADMINROLE, 'superuser with all rights'),
             ('photoadmin',   'Photo collection administrator'),
             (WEBACCESSADMINROLE,     'WebAccess administrator'))
# users
# list of e-mail addresses
def_users = []
# actions
#            name                  desc     allowedkeywords   optional
def_actions = (
               ('cfgwebsearch',         'configure WebSearch',       '',              'no'),
               ('cfgbibformat',         'configure BibFormat',       '',              'no'),
               ('cfgwebsubmit',         'configure WebSubmit',       '',              'no'),
               ('runbibindex',          'run BibIndex',       '',              'no'),
               ('runbibupload',         'run BibUpload',       '',              'no'),
               ('runwebcoll',           'run webcoll',       'collection',    'yes'),
               ('runbibformat',         'run BibFormat',       'format',        'yes'),
               (WEBACCESSACTION,        'configure WebAccess',       '',              'no'),
               (DELEGATEADDUSERROLE,    'delegate subroles inside WebAccess',       'role',          'no'),
               ('runbibtaskex',         'run BibTaskEx example',       '',              'no'),
               ('referee',                  'referee document type doctype/category categ', 'doctype,categ',    'yes'),
               ('submit',                   'use webSubmit',    'doctype,act',  'yes'),
               ('runbibrank',         'run BibRank',       '',              'no'),
               ('cfgbibrank',         'configure BibRank',       '',              'no'),
               ('cfgbibharvest',         'configure BibHarvest',       '',              'no'),
               ('runoaiharvest',         'run oaiharvest task',       '',              'no'),
               ('cfgwebcomment',         'configure WebComment',       '',              'no'),
              )
# authorizations
#          role              action          arglistid  optional   arguments
def_auths = (
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
            )
cfg_webaccess_msgs = {
                                0: 'Try to <a href="%s/youraccount.py/login?referer=%s/admin/%s">login</a> with another account.' % (weburl, weburl, "%s"),
                                1: '<br>If you think this is not correct, please contact: <a href="mailto:%s">%s</a>' % (supportemail, supportemail),
                                2: '<br>If you have any questions, please write to <a href="mailto:%s">%s</a>' % (supportemail, supportemail),
				3: 'Guest users are not allowed, please <a href="%s/youraccount.py/login">login</a>.' % weburl,
				4: 'The site is temporarily closed for maintenance.  Please come back soon.',
 				5: 'Authorization failure',
                                6: '%s temporarily closed' % cdsname,
                                7: 'This functionality is temporarily closed due to server maintenance. Please use only the search engine in the meantime.',
                                8: 'Functionality temporarily closed'
		} 


cfg_webaccess_warning_msgs = {
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
                               15: """Error(15): Could not login using your '%s' account, because you have introduced a wrong password."""
		} 

