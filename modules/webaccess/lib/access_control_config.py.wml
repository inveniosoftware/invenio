## $Id$
## CDSware Access Control Config in mod_python.

## This file is part of the CERN Document Server Software (CDSware).
## Copyright (C) 2002 CERN.
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

<protect> ## okay, rest of the Python code goes below #######

__version__ = "$Id$"

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
# default data for the add_default_settings function
# roles
#           name          description
def_roles = ((SUPERADMINROLE, 'all rights'),
             ('photoadmin',   'administrator of the photo collections'),
             (WEBACCESSADMINROLE,     'access to web administrator interface'))
# users
# list of e-mail addresses
def_users = []
# actions
#            name                  desc     allowedkeywords   optional
def_actions = (('cfgwebsearch',         '',       '',              'no'),
               ('cfgbibformat',         '',       '',              'no'),
               ('runbibwords',          '',       '',              'no'),
               ('runbibupload',         '',       '',              'no'),
               ('runwebcoll',           '',       'collection',    'yes'),
               ('runbibformat',         '',       'format',        'yes'),
               (WEBACCESSACTION,        '',       '',              'no'),
               (DELEGATEADDUSERROLE,    '',       'role',          'no'))
# authorizations
#          role              action          arglistid  optional   arguments
def_auths = ((SUPERADMINROLE,    'cfgwebsearch',         -1,      0,       {}),
             (SUPERADMINROLE,    'cfgbibformat',         -1,      0,       {}),
             (SUPERADMINROLE,    'runbibwords',          -1,      0,       {}),
             (SUPERADMINROLE,    'runbibupload',         -1,      0,       {}),
             (SUPERADMINROLE,    'runbibformat',         -1,      1,       {}),
             (SUPERADMINROLE,    WEBACCESSACTION,        -1,      0,       {}), 
             ('photoadmin',      'runwebcoll',           -1,      0,       {'collection': 'Photos'}),
             (WEBACCESSADMINROLE,WEBACCESSACTION,        -1,      0,       {}))
</protect>


# # webaccess defaults, add to tabfill.sql.wml
# from access_control_config import * 
# # roles
# INSERT INTO accROLE VALUES (1,SUPERADMINROLE,'all rights');
# INSERT INTO accROLE VALUES (2,'photoadmin','administrator of the photo collections');
# INSERT INTO accROLE VALUES (3,WEBACCESSADMINROLE,'access to web administrator interface');
# # user_roles
# INSERT INTO user_accROLE VALUES (1,1)
# INSERT INTO user_accROLE VALUES (1,3)
# # actions
# INSERT INTO accACTION VALUES (1,'cfgwebsearch',     '','',          'no');
# INSERT INTO accACTION VALUES (2,'cfgbibformat',     '','',          'no');
# INSERT INTO accACTION VALUES (3,'runbibwords',      '','',          'no');
# INSERT INTO accACTION VALUES (4,'runbibupload',     '','',          'no');
# INSERT INTO accACTION VALUES (5,'runwebcoll',       '','collection','yes');
# INSERT INTO accACTION VALUES (6,'runbibformat',     '','format',    'yes');
# INSERT INTO accACTION VALUES (7,WEBACCESSACTION,    '','',          'no');
# INSERT INTO accACTION VALUES (8,DELEGATEADDUSERROLE,'','role',      'no');
# # arguments
# INSERT INTO accARGUMENT VALUES (1,'collection','Photos');
# # authorizations
# INSERT INTO accROLE_accACTION_accARGUMENT VALUES (1,1, 0, 0);
# INSERT INTO accROLE_accACTION_accARGUMENT VALUES (1,2, 0, 0);
# INSERT INTO accROLE_accACTION_accARGUMENT VALUES (1,3, 0, 0);
# INSERT INTO accROLE_accACTION_accARGUMENT VALUES (1,4, 0, 0);
# INSERT INTO accROLE_accACTION_accARGUMENT VALUES (1,6,-1,-1);
# INSERT INTO accROLE_accACTION_accARGUMENT VALUES (1,7, 0, 0);
# INSERT INTO accROLE_accACTION_accARGUMENT VALUES (2,5, 1, 1);
# INSERT INTO accROLE_accACTION_accARGUMENT VALUES (3,7, 0, 0);
