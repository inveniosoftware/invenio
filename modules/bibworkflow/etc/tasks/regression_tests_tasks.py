## This file is part of Invenio.
## Copyright (C) 2012 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import time
from invenio.bibconvert_xslt_engine import convert

###### Basic test functions - NOT FOR XML ########
def higher_than_20():
     def _higher_than_20(obj, eng):
        """Function checks if variable is lower than 20"""
        if obj.data['a'] < 20:
            print "a < 20"
            eng.haltProcessing("Value of filed: a in object is lower than 20.")
        return
     return _higher_than_20
 

def lower_than_20():
     def _lower_than_20(obj, eng):
        """Function checks if variable is higher than 20"""
        if obj.data['a'] > 20:
            print "a > 20"
            eng.haltProcessing("Value of filed: a in object is higher than 20.")
        return
     return _lower_than_20


def add(value):
     def _add(obj, eng):
        """Function adds value to variable"""
        obj.data['a'] += value
     return _add
     
def subtract(value):
     def _subtract(obj, eng):
        """Function subtract value from variable"""
        obj.data['a'] -= value
     return _subtract

###### XML functions #######
def xml_convert_record(xslt_stylesheet):
    def _xml_convert_record(obj, eng):
        """Test"""
        eng.log.info("Engine: test engine logging")
        eng.log.info(obj.data)
        eng.log.info(type(obj.data))
        eng.log.info(xslt_stylesheet)
        newtext = convert(obj.data, xslt_stylesheet)
        obj.log.info("Object: test object logging")
        obj.data = newtext
    return _xml_convert_record

def xml_print_record(obj, eng):
    print obj.data

###### other functions #######
def sleep_task(t):
    def _sleep_task(obj, eng):
        """Function simulates long running task"""
        print "Going to sleep..."
        time.sleep(t)
        print "I've woken up:)"
    return _sleep_task    
    
def save_workflow():
    def _save_workflow(obj, eng):
        """Function saves workflow"""
        eng.save()
        print "Workflow saved from task"
    return _save_workflow
    
def save_object():
    def _save_object(obj, eng):
        """Function saves object in ERROR state"""
        #We should consider creating other state for saving in execution purpose
        obj.save(2)
        print "Object saved from task"
    return _save_object