# -*- coding: utf-8 -*-
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
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
Provide a "ticket" interface with a request tracker.
This is a subclass of BibCatalogSystem
"""

import os
import invenio.webuser
from invenio.shellutils import run_shell_command, escape_shell_arg
from invenio.bibcatalog_system import BibCatalogSystem, get_bibcat_from_prefs

from invenio.config import CFG_BIBCATALOG_SYSTEM, \
                           CFG_BIBCATALOG_SYSTEM_RT_CLI, \
                           CFG_BIBCATALOG_SYSTEM_RT_URL, \
                           CFG_BIBCATALOG_QUEUES

class BibCatalogSystemRT(BibCatalogSystem):

    BIBCATALOG_RT_SERVER = "" #construct this by http://user:password@RT_URL

    def check_system(self, uid):
        """return an error string if there are problems"""
        user_pref = invenio.webuser.get_user_preferences(uid)
        if not user_pref.has_key('bibcatalog_username'):
            return "user " + str(uid) + " has no bibcatalog_username"
        rtuid = user_pref['bibcatalog_username']
        if not user_pref.has_key('bibcatalog_password'):
            return "user " + str(uid) + " has no bibcatalog_password"
        rtpw = user_pref['bibcatalog_password']
        if not CFG_BIBCATALOG_SYSTEM == 'RT':
            return "CFG_BIBCATALOG_SYSTEM is not RT though this is an RT module"
        if not CFG_BIBCATALOG_SYSTEM_RT_CLI:
            return "CFG_BIBCATALOG_SYSTEM_RT_CLI not defined or empty"
        if not os.path.exists(CFG_BIBCATALOG_SYSTEM_RT_CLI):
            return "CFG_BIBCATALOG_SYSTEM_RT_CLI " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " file does not exists"
        #check that you can execute it.. this is a safe call unless someone can fake CFG_BIBCATALOG_SYSTEM_RT_CLI (unlikely)
        dummy, myout, myerr = run_shell_command(CFG_BIBCATALOG_SYSTEM_RT_CLI + " help")
        helpfound = False
        if myerr.count("help") > 0:
            helpfound = True
        if not helpfound:
            return "Execution of CFG_BIBCATALOG_SYSTEM_RT_CLI " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " help did not produce output 'help'"
        if not CFG_BIBCATALOG_SYSTEM_RT_URL:
            return "CFG_BIBCATALOG_SYSTEM_RT_URL not defined or empty"
        #construct.. split RT_URL at //
        if not CFG_BIBCATALOG_SYSTEM_RT_URL.startswith('http://') and \
           not CFG_BIBCATALOG_SYSTEM_RT_URL.startswith('https://'):
            return "CFG_BIBCATALOG__SYSTEM_RT_URL does not start with 'http://' or 'https://'"
        httppart, siteandpath = CFG_BIBCATALOG_SYSTEM_RT_URL.split("//")
        BIBCATALOG_RT_SERVER = httppart + "//" + rtuid + ":" + rtpw + "@" + siteandpath
        #set as env var
        os.environ["RTUSER"] = rtuid
        os.environ["RTSERVER"] = BIBCATALOG_RT_SERVER
        #try to talk to RT server
        #this is a safe call since rtpw is the only variable in it, and it is escaped
        rtpw = escape_shell_arg(rtpw)
        dummy, myout, myerr = run_shell_command("echo "+rtpw+" | " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " ls \"Subject like 'F00'\"")
        if len(myerr) > 0:
            return "could not connect to " + BIBCATALOG_RT_SERVER + " " + myerr
        #finally, check that there is some sane output like tickets or 'No matching result'
        saneoutput = (myout.count('matching') > 0) or (myout.count('1') > 0)
        if not saneoutput:
            return CFG_BIBCATALOG_SYSTEM_RT_CLI + " returned " + myout + " instead of 'matching' or '1'"
        if not CFG_BIBCATALOG_QUEUES:
            return "CFG_BIBCATALOG_QUEUES not defined or empty"
        (username, dummy) = get_bibcat_from_prefs(uid)
        if (username is None):
            return "Cannot find user preference bibcatalog_username for uid "+str(uid)
        return ""

    def ticket_search(self, uid, recordid=-1, subject="", text="", creator="", owner="", \
                      date_from="", date_until="", status="", priority=""):
        """returns a list of ticket ID's related to this record or by
           matching the subject, creator or owner of the ticket."""

        search_atoms = [] #the search expression will be made by and'ing these
        if (recordid > -1):
            #search by recid
            search_atoms.append("CF.{RecordID} = " + escape_shell_arg(str(recordid)))
        if (len(subject) > 0):
            #search by subject
            search_atoms.append("Subject like " + escape_shell_arg(str(subject)))
        if (len(text) > 0):
            search_atoms.append("Content like " + escape_shell_arg(str(text)))
        if (len(str(creator)) > 0):
            #search for this person's bibcatalog_username in preferences
            creatorprefs = invenio.webuser.get_user_preferences(creator)
            creator = "Nobody can Have This Kind of Name"
            if creatorprefs.has_key("bibcatalog_username"):
                creator = creatorprefs["bibcatalog_username"]
            search_atoms.append("Creator = " + escape_shell_arg(str(creator)))
        if (len(str(owner)) > 0):
            ownerprefs = invenio.webuser.get_user_preferences(owner)
            owner = "Nobody can Have This Kind of Name"
            if ownerprefs.has_key("bibcatalog_username"):
                owner = ownerprefs["bibcatalog_username"]
            search_atoms.append("Owner = " + escape_shell_arg(str(owner)))
        if (len(date_from) > 0):
            search_atoms.append("Created >= " + escape_shell_arg(str(date_from)))
        if (len(date_until) > 0):
            search_atoms.append("Created <= " + escape_shell_arg(str(date_until)))
        if (len(str(status)) > 0) and (type(status) == type("this is a string")):
            search_atoms.append("Status = " + escape_shell_arg(str(status)))
        if (len(str(priority)) > 0):
            #try to convert to int
            intpri = -1
            try:
                intpri = int(priority)
            except:
                pass
            if (intpri > -1):
                search_atoms.append("Priority = " + str(intpri))
        searchexp = " and ".join(search_atoms)
        tickets = []
        if not CFG_BIBCATALOG_SYSTEM_RT_URL:
            return tickets

        httppart, siteandpath = CFG_BIBCATALOG_SYSTEM_RT_URL.split("//")
        (username, passwd) = get_bibcat_from_prefs(uid)
        BIBCATALOG_RT_SERVER = httppart + "//" + username + ":" + passwd + "@" + siteandpath
        #set as env var
        os.environ["RTUSER"] = username
        os.environ["RTSERVER"] = BIBCATALOG_RT_SERVER
        #search..
        if len(searchexp) == 0:
            #just make an expression that is true for all tickets
            searchexp = "Created > '1900-01-01'"
        passwd = escape_shell_arg(passwd)
        #make a call. This is safe since passwd and all variables in searchexp have been escaped.
        dummy, myout, dummyerr = run_shell_command("echo "+passwd+" | " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " ls -l \"" + searchexp + "\"")
        statuses = []
        for line in myout.split("\n"):
            #if there are matching lines they will look like NUM:subj.. so pick num
            if (line.count('id: ticket/') > 0):
                dummy, tnum = line.split('/') #get the ticket id
                try:
                    inum = int(tnum)
                    tickets.append(tnum)
                except:
                    pass
            if (line.count('Status: ') > 0):
                dummy, tstatus = line.split('Status: ')
                statuses.append(tstatus)
        if (type(status) == type([])):
            #take only those tickets whose status matches with one of the status list
            alltickets = tickets
            tickets = []
            for i in range(len(alltickets)):
                tstatus = statuses[i]
                tnum = alltickets[i]
                if (status.count(tstatus) > 0): #match
                    tickets.append(tnum)
        return tickets

    def ticket_submit(self, uid, subject, recordid, text="", queue="", priority="", owner=""):
        """creates a ticket. return ticket num on success, otherwise None"""
        if not CFG_BIBCATALOG_SYSTEM_RT_URL:
            return None
        (username, passwd) = get_bibcat_from_prefs(uid)
        httppart, siteandpath = CFG_BIBCATALOG_SYSTEM_RT_URL.split("//")
        BIBCATALOG_RT_SERVER = httppart + "//" + username + ":" + passwd + "@" + siteandpath
        #set as env var
        os.environ["RTUSER"] = username
        os.environ["RTSERVER"] = BIBCATALOG_RT_SERVER
        queueset = ""
        textset = ""
        priorityset = ""
        ownerset = ""
        subjectset = ""
        if subject:
            subjectset = " subject=" + escape_shell_arg(subject)
        recidset = " CF-RecordID=" + escape_shell_arg(str(recordid))
        if text:
            textset = " text=" + escape_shell_arg(text)
        if priority:
            priorityset = " priority=" + escape_shell_arg(str(priority))
        if queue:
            queueset = " queue=" + escape_shell_arg(queue)
        if owner:
            #get the owner name from prefs
            ownerprefs = invenio.webuser.get_user_preferences(owner)
            if ownerprefs.has_key("bibcatalog_username"):
                owner = ownerprefs["bibcatalog_username"]
                ownerset = " owner=" + escape_shell_arg(owner)
        #make a command.. note that all set 'set' parts have been escaped

        command = CFG_BIBCATALOG_SYSTEM_RT_CLI + " create -t ticket set " + subjectset + recidset + \
                  queueset + textset + priorityset + ownerset

        passwd = escape_shell_arg(passwd)
        #make a call.. passwd and command have been escaped (see above)
        dummy, myout, dummyerr = run_shell_command("echo "+passwd+" | " + command)
        inum = -1
        for line in myout.split("\n"):
            if line.count(' ') > 0:
                stuff = line.split(' ')
                try:
                    inum = int(stuff[2])
                except:
                    pass
        if inum > 0:
            return inum
        return None

    def ticket_assign(self, uid, ticketid, to_user):
        """assign a ticket to an RT user. Returns 1 on success, 0 on failure"""
        return self.ticket_set_attribute(uid, ticketid, 'owner', to_user)

    def ticket_set_attribute(self, uid, ticketid, attribute, new_value):
        """change the ticket's attribute. Returns 1 on success, 0 on failure"""
        #check that the attribute is accepted..
        if attribute not in BibCatalogSystem.TICKET_ATTRIBUTES:
            return 0
        #we cannot change read-only values.. including text that is an attachment. pity
        if attribute in ['creator', 'date', 'ticketid', 'url_close', 'url_display', 'recordid', 'text']:
            return 0
        #check attribute
        setme = ""
        if (attribute == 'priority'):
            try:
                dummy = int(new_value)
            except:
                return 0
            setme = "set Priority=" + str(new_value)
        if (attribute == 'subject'):
            subject = escape_shell_arg(new_value)
            setme = "set Subject='" + subject +"'"

        if (attribute == 'owner'):
            #convert from invenio to RT
            ownerprefs = invenio.webuser.get_user_preferences(new_value)
            if not ownerprefs.has_key("bibcatalog_username"):
                return 0
            else:
                owner = escape_shell_arg(ownerprefs["bibcatalog_username"])
            setme = " set owner='" + owner +"'"

        if (attribute == 'status'):
            setme = " set status='" + escape_shell_arg(new_value) +"'"

        if (attribute == 'queue'):
            setme = " set queue='" + escape_shell_arg(new_value) +"'"

        if not CFG_BIBCATALOG_SYSTEM_RT_URL:
            return 0
        #make sure ticketid is numeric
        try:
            dummy = int(ticketid)
        except:
            return 0
        (username, passwd) = get_bibcat_from_prefs(uid)
        httppart, siteandpath = CFG_BIBCATALOG_SYSTEM_RT_URL.split("//")
        BIBCATALOG_RT_SERVER = httppart + "//" + username + ":" + passwd + "@" + siteandpath
        #set as env var
        os.environ["RTUSER"] = username
        os.environ["RTSERVER"] = BIBCATALOG_RT_SERVER
        passwd = escape_shell_arg(passwd)
        #make a call. safe since passwd and all variables in 'setme' have been escaped
        dummy, myout, dummyerr = run_shell_command("echo "+passwd+" | " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " edit ticket/" + str(ticketid) + setme)
        respOK = False
        mylines = myout.split("\n")
        for line in mylines:
            if line.count('updated') > 0:
                respOK = True
        if respOK:
            return 1
            #print str(mylines)
        return 0

    def ticket_get_attribute(self, uid, ticketid, attribute):
        """return an attribute of a ticket"""
        ticinfo = self.ticket_get_info(uid, ticketid, [attribute])
        if ticinfo.has_key(attribute):
            return ticinfo[attribute]
        return None

    def ticket_get_info(self, uid, ticketid, attributes = None):
        """return ticket info as a dictionary of pre-defined attribute names.
           Or just those listed in attrlist.
           Returns None on failure"""
        if not CFG_BIBCATALOG_SYSTEM_RT_URL:
            return 0
        #make sure ticketid is numeric
        try:
            dummy = int(ticketid)
        except:
            return 0
        if attributes is None:
            attributes = []
        (username, passwd) = get_bibcat_from_prefs(uid)
        httppart, siteandpath = CFG_BIBCATALOG_SYSTEM_RT_URL.split("//")
        BIBCATALOG_RT_SERVER = httppart + "//" + username + ":" + passwd + "@" + siteandpath
        #set as env var
        os.environ["RTUSER"] = username
        os.environ["RTSERVER"] = BIBCATALOG_RT_SERVER
        passwd = escape_shell_arg(passwd)
        #make a call. This is safe.. passwd escaped, ticketid numeric
        dummy, myout, dummyerr = run_shell_command("echo "+passwd+" | " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " show ticket/" + str(ticketid))
        tdict = {}
        for line in myout.split("\n"):
            if line.count(": ") > 0:
                tattr, tvaluen = line.split(": ")
                tvalue = tvaluen.rstrip()
                tdict[tattr] = tvalue
        #query again to get attachments -> Contents
        dummy, myout, dummyerr = run_shell_command("echo "+passwd+" | " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " show ticket/" + str(ticketid) + "/attachments/")
        attachments = []
        for line in myout.split("\n"):
            if line.count(": ") > 1: #there is a line Attachments: 40: xxx
                aline = line.split(": ")
                attachments.append(aline[1])
        #query again for each attachment
        for att in attachments:
            #passwd still escaped..
            dummy, myout, dummyerr = run_shell_command("echo "+passwd+" | " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " show ticket/" + str(ticketid) + "/attachments/" + att)
            #get the contents line
            for line in myout.split("\n"):
                if line.count("Content: ") > 0:
                    cstuff = line.split("Content: ")
                    tdict['Text'] = cstuff[1].rstrip()
        if (len(tdict) > 0):
            #iterate over TICKET_ATTRIBUTES to make a canonical ticket
            candict = {}
            for f in BibCatalogSystem.TICKET_ATTRIBUTES:
                tcased = f.title()
                if tdict.has_key(tcased):
                    candict[f] = tdict[tcased]
            if tdict.has_key('CF.{RecordID}'):
                candict['recordid'] = tdict['CF.{RecordID}']
            if tdict.has_key('id'):
                candict['ticketid'] = tdict['id']
            #make specific URL attributes:
            url_display = CFG_BIBCATALOG_SYSTEM_RT_URL + "/Ticket/Display.html?id="+str(ticketid)
            candict['url_display'] = url_display
            url_close = CFG_BIBCATALOG_SYSTEM_RT_URL + "/Ticket/Update.html?Action=Comment&DefaultStatus=resolved&id="+str(ticketid)
            candict['url_close'] = url_close
            url_modify = CFG_BIBCATALOG_SYSTEM_RT_URL + "/Ticket/ModifyAll.html?id="+str(ticketid)
            candict['url_modify'] = url_modify
            #change the ticket owner into invenio UID
            if tdict.has_key('owner'):
                rt_owner = tdict["owner"]
                uid = invenio.webuser.get_uid_based_on_pref("bibcatalog_username", rt_owner)
                candict['owner'] = uid
            if len(attributes) == 0: #return all fields
                return candict
            else: #return only the fields that were requested
                tdict = {}
                for myatt in attributes:
                    if candict.has_key(myatt):
                        tdict[myatt] = candict[myatt]
                return tdict
        else:
            return None


