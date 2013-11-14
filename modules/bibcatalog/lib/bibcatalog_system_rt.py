# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2009, 2010, 2011, 2012 CERN.
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
import invenio.legacy.webuser
from invenio.utils.shell import run_shell_command, escape_shell_arg
from invenio.bibcatalog_system import BibCatalogSystem, get_bibcat_from_prefs

from invenio.config import CFG_BIBCATALOG_SYSTEM, \
                           CFG_BIBCATALOG_SYSTEM_RT_CLI, \
                           CFG_BIBCATALOG_SYSTEM_RT_URL, \
                           CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_USER, \
                           CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_PWD

class BibCatalogSystemRT(BibCatalogSystem):

    BIBCATALOG_RT_SERVER = "" #construct this by http://user:password@RT_URL

    def check_system(self, uid=None):
        """return an error string if there are problems"""
        if uid:
            rtuid, rtpw = get_bibcat_from_prefs(uid)
        else:
            # Assume default RT user
            rtuid = CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_USER
            rtpw = CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_PWD

        if not rtuid and not rtpw:
            return "No valid RT user login specified"

        if not CFG_BIBCATALOG_SYSTEM == 'RT':
            return "CFG_BIBCATALOG_SYSTEM is not RT though this is an RT module"
        if not CFG_BIBCATALOG_SYSTEM_RT_CLI:
            return "CFG_BIBCATALOG_SYSTEM_RT_CLI not defined or empty"
        if not os.path.exists(CFG_BIBCATALOG_SYSTEM_RT_CLI):
            return "CFG_BIBCATALOG_SYSTEM_RT_CLI " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " file does not exists"

        # Check that you can execute the binary.. this is a safe call unless someone can fake CFG_BIBCATALOG_SYSTEM_RT_CLI (unlikely)
        dummy, myout, myerr = run_shell_command(CFG_BIBCATALOG_SYSTEM_RT_CLI + " help")
        helpfound = False
        if myerr.count("help") > 0:
            helpfound = True
        if not helpfound:
            return "Execution of CFG_BIBCATALOG_SYSTEM_RT_CLI " + CFG_BIBCATALOG_SYSTEM_RT_CLI + " help did not produce output 'help'"

        if not CFG_BIBCATALOG_SYSTEM_RT_URL:
            return "CFG_BIBCATALOG_SYSTEM_RT_URL not defined or empty"
        # Construct URL, split RT_URL at //
        if not CFG_BIBCATALOG_SYSTEM_RT_URL.startswith('http://') and \
           not CFG_BIBCATALOG_SYSTEM_RT_URL.startswith('https://'):
            return "CFG_BIBCATALOG__SYSTEM_RT_URL does not start with 'http://' or 'https://'"
        httppart, siteandpath = CFG_BIBCATALOG_SYSTEM_RT_URL.split("//")
        # Assemble by http://user:password@RT_URL
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
        return ""

    def ticket_search(self, uid, recordid=-1, subject="", text="", creator="", owner="", \
                      date_from="", date_until="", status="", priority="", queue=""):
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
            creatorprefs = invenio.legacy.webuser.get_user_preferences(creator)
            creator = "Nobody can Have This Kind of Name"
            if creatorprefs.has_key("bibcatalog_username"):
                creator = creatorprefs["bibcatalog_username"]
            search_atoms.append("Creator = " + escape_shell_arg(str(creator)))
        if (len(str(owner)) > 0):
            ownerprefs = invenio.legacy.webuser.get_user_preferences(owner)
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
        if queue:
            search_atoms.append("Queue = " + escape_shell_arg(queue))
        searchexp = " and ".join(search_atoms)
        tickets = []

        if len(searchexp) == 0:
            #just make an expression that is true for all tickets
            searchexp = "Created > '1900-01-01'"

        command = CFG_BIBCATALOG_SYSTEM_RT_CLI + " ls -l \"" + searchexp + "\""
        command_out = self._run_rt_command(command, uid)
        if command_out == None:
            return tickets

        statuses = []
        for line in command_out.split("\n"):
            #if there are matching lines they will look like NUM:subj.. so pick num
            if (line.count('id: ticket/') > 0):
                dummy, tnum = line.split('/') #get the ticket id
                try:
                    dummy = int(tnum)
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

    def ticket_submit(self, uid=None, subject="", recordid=-1, text="", queue="",
        priority="", owner="", requestor=""):
        """creates a ticket. return ticket num on success, otherwise None"""
        queueset = ""
        textset = ""
        priorityset = ""
        ownerset = ""
        subjectset = ""
        requestorset = ""
        if subject:
            subjectset = " subject=" + escape_shell_arg(subject)
        recidset = " CF-RecordID=" + escape_shell_arg(str(recordid))
        if priority:
            priorityset = " priority=" + escape_shell_arg(str(priority))
        if queue:
            queueset = " queue=" + escape_shell_arg(queue)
        if requestor:
            requestorset = " requestor=" + escape_shell_arg(requestor)
        if owner:
            #get the owner name from prefs
            ownerprefs = invenio.legacy.webuser.get_user_preferences(owner)
            if ownerprefs.has_key("bibcatalog_username"):
                owner = ownerprefs["bibcatalog_username"]
                ownerset = " owner=" + escape_shell_arg(owner)
        if text:
            if '\n' in text:
                # contains newlines (\n) return with error
                return "Newlines are not allowed in text parameter. Use ticket_comment() instead."
            else:
                textset = " text=" + escape_shell_arg(text)
        # make a command.. note that all set 'set' parts have been escaped
        command = CFG_BIBCATALOG_SYSTEM_RT_CLI + " create -t ticket set " + subjectset + recidset + \
                  queueset + textset + priorityset + ownerset + requestorset
        command_out = self._run_rt_command(command, uid)
        if command_out == None:
            return None
        inum = -1
        for line in command_out.split("\n"):
            if line.count(' ') > 0:
                stuff = line.split(' ')
                try:
                    inum = int(stuff[2])
                except:
                    pass
        if inum > 0:
            return inum
        return None

    def ticket_comment(self, uid, ticketid, comment):
        """comment on a given ticket. Returns 1 on success, 0 on failure"""
        command = '%s comment -m %s %s' % (CFG_BIBCATALOG_SYSTEM_RT_CLI, \
                                           escape_shell_arg(comment), str(ticketid))
        command_out = self._run_rt_command(command, uid)
        if command_out == None:
            return None
        return 1

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
            ownerprefs = invenio.legacy.webuser.get_user_preferences(new_value)
            if not ownerprefs.has_key("bibcatalog_username"):
                return 0
            else:
                owner = escape_shell_arg(ownerprefs["bibcatalog_username"])
            setme = " set owner='" + owner +"'"

        if (attribute == 'status'):
            setme = " set status='" + escape_shell_arg(new_value) +"'"

        if (attribute == 'queue'):
            setme = " set queue='" + escape_shell_arg(new_value) +"'"

        #make sure ticketid is numeric
        try:
            dummy = int(ticketid)
        except:
            return 0

        command = CFG_BIBCATALOG_SYSTEM_RT_CLI + " edit ticket/" + str(ticketid) + setme
        command_out = self._run_rt_command(command, uid)
        if command_out == None:
            return 0
        mylines = command_out.split("\n")
        for line in mylines:
            if line.count('updated') > 0:
                return 1
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
        #make sure ticketid is numeric
        try:
            dummy = int(ticketid)
        except:
            return 0
        if attributes is None:
            attributes = []

        command = CFG_BIBCATALOG_SYSTEM_RT_CLI + " show ticket/" + str(ticketid)
        command_out = self._run_rt_command(command, uid)

        if command_out == None:
            return 0

        tdict = {}
        for line in command_out.split("\n"):
            if line.count(": ") > 0:
                tattr, tvaluen = line.split(": ")
                tvalue = tvaluen.rstrip()
                tdict[tattr] = tvalue

        #query again to get attachments -> Contents
        command = CFG_BIBCATALOG_SYSTEM_RT_CLI + " show ticket/" + str(ticketid) + "/attachments/"
        command_out = self._run_rt_command(command, uid)
        if command_out == None:
            return 0

        attachments = []
        for line in command_out.split("\n"):
            if line.count(": ") > 1: #there is a line Attachments: 40: xxx
                aline = line.split(": ")
                attachments.append(aline[1])

        #query again for each attachment
        for att in attachments:
            command = CFG_BIBCATALOG_SYSTEM_RT_CLI + " show ticket/" + str(ticketid) + "/attachments/" + att
            command_out = self._run_rt_command(command, uid)
            if command_out == None:
                return 0
            #get the contents line
            for line in command_out.split("\n"):
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
                uid = invenio.legacy.webuser.get_uid_based_on_pref("bibcatalog_username", rt_owner)
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

    def _run_rt_command(self, command, uid=None):
        """
        This function will run a RT CLI command as given user. If no user is specified
        the default RT user will be used, if configured.

        Should any of the configuration parameters be missing this function will return
        None. Otherwise it will return the standard output from the CLI command.

        @param command: RT CLI command to execute
        @type command: string

        @param uid: the Invenio user id to submit on behalf of. Optional.
        @type uid: int

        @return: standard output from the command given. None, if any errors.
        @rtype: string
        """
        if not CFG_BIBCATALOG_SYSTEM_RT_URL:
            return None
        if uid:
            username, passwd = get_bibcat_from_prefs(uid)
        else:
            username = CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_USER
            passwd = CFG_BIBCATALOG_SYSTEM_RT_DEFAULT_PWD
        httppart, siteandpath = CFG_BIBCATALOG_SYSTEM_RT_URL.split("//")
        BIBCATALOG_RT_SERVER = httppart + "//" + username + ":" + passwd + "@" + siteandpath
        #set as env var
        os.environ["RTUSER"] = username
        os.environ["RTSERVER"] = BIBCATALOG_RT_SERVER
        passwd = escape_shell_arg(passwd)
        error_code, myout, dummyerr = run_shell_command("echo "+passwd+" | " + command)
        if error_code > 0:
            raise ValueError, 'Problem running "%s": %d' % (command, error_code)
        return myout
