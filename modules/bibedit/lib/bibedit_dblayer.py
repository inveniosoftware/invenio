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

from invenio.dbquery import run_sql

def get_name_tag(tag):
    
    """ This function return a textual name of tag """
    
    result = run_sql("SELECT name FROM tag WHERE value='%s'" % tag)
    
    if len(result) != 0:
        return result[0][0]
    
    else:
        return tag


def get_tag_name(name):
    
    """ This function return a tag from the name of this tag """
    
    result = run_sql("SELECT value FROM tag WHERE name LIKE '%s'" % name)
    
    if len(result) != 0:
        return result[0][0]
    
    else:
        return name 


def split_tag_to_marc(tag, ind1='', ind2='', subcode=''):
    
    """ This function make a marc tag with tag, ind1, ind2 and subcode. """
    
    tag = get_tag_name(tag)
    
    if len(tag) > 3:
        tag = tag[:3]
        
    if ind1 == ' ' or ind1 == '':
        ind1 = '_'
        
    if ind2 == ' ' or ind2 == '':
        ind2 = '_'
        
    if subcode == ' ' or subcode == '':
        subcode = '_'
        
    return "%s%s%s%s" % (tag, ind1, ind2, subcode)    


def marc_to_split_tag(tag):
    
    """ The inverse of split_tag_to_marc function. """
    
    tag = get_tag_name(tag)
    ind1 = ''
    ind2 = ''
    subcode = ''
    len_tag = len(tag)
    
    if len_tag > 3:
        
        ind1 = tag[3]
        if ind1 == '_':
            ind1 = ''
            
        if len_tag > 4:
            
            ind2 = tag[4]
            if ind2 =='_':
                ind2 = ''
                
            if len_tag > 5:
                subcode = tag[5]
                                   
    tag = tag[:3]
    
    return (tag, ind1, ind2, subcode)
