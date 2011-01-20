#!/usr/bin/python

# Author:  Rob Sanderson (azaroth@liv.ac.uk)
# Distributed and Usable under the GPL 
# Version: 1.5
# Most Recent Changes: contexts, new modifier style for 1.1
#
# With thanks to Adam from IndexData and Mike Taylor for their valuable input

from shlex import shlex
from xml.sax.saxutils import escape
from xml.dom.minidom import Node, parseString
from SRWDiagnostics import *
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
import types
import collections

# Parsing strictness flags
errorOnEmptyTerm = 0          # index = ""      (often meaningless)
errorOnQuotedIdentifier = 0   # "/foo/bar" = "" (unnecessary BNF restriction)
errorOnDuplicatePrefix = 0    # >a=b >a=c ""    (impossible due to BNF) 
fullResultSetNameCheck = 1    # srw.rsn=foo and srw.rsn=foo (mutant!!)

# Base values for CQL
serverChoiceIndex = "cql.serverchoice"

order = ['=', '>', '>=', '<', '<=', '<>']
modifierSeparator = "/"
booleans = ['and', 'or', 'not', 'prox']

reservedPrefixes = {"srw" : "http://www.loc.gov/zing/cql/srw-indexes/v1.0/",
                    "cql" : "http://www.loc.gov/zing/cql/contextSets/cql/v1.1/"}

# End of 'configurable' stuff

serverChoiceRelation = "scr"

class PrefixableObject:
    "Root object for triple and searchClause"
    prefixes = {}
    parent = None
    config = None

    def __init__(self):
        self.prefixes = {}
        self.parent = None
        self.config = None

    def toXCQL(self, depth=0):
        # Just generate our prefixes
        space = "  " * depth
        xml = ['%s<prefixes>\n' % (space)]
        for p in self.prefixes.keys():
            xml.append("%s  <prefix>\n%s    <name>%s</name>\n%s    <identifier>%s</identifier>\n%s  </prefix>\n" % (space, space, escape(p), space, escape(self.prefixes[p]), space))
        xml.append("%s</prefixes>\n" % (space))
        return ''.join(xml)
        

    def addPrefix(self, name, identifier):
        if (errorOnDuplicatePrefix and (self.prefixes.has_key(name) or reservedPrefixes.has_key(name))):
            # Maybe error
            diag = Diagnostic45()
            diag.details = name
            raise diag;
        self.prefixes[name] = identifier

    def resolvePrefix(self, name):
        # Climb tree
        if (reservedPrefixes.has_key(name)):
            return reservedPrefixes[name]
        elif (self.prefixes.has_key(name)):
            return self.prefixes[name]
        elif (self.parent <> None):
            return self.parent.resolvePrefix(name)
        elif (self.config <> None):
            # Config is some sort of server config which specifies defaults
            return self.config.resolvePrefix(name)
        else:
            # Top of tree, no config, no resolution->Unknown indexset
            # For client we need to allow no prefix?

            #diag = Diagnostic15()
            #diag.details = name
            #raise diag
            return None


class PrefixedObject:
    "Root object for relation, relationModifier and index"
    prefix = ""
    prefixURI = ""
    value = ""
    parent = None

    def __init__(self, val):
        # All prefixed things are case insensitive
        val = val.lower()
        if val and val[0] == '"' and val[-1] == '"':
            if errorOnQuotedIdentifier:
                diag = Diagnostic14()
                diag.details = val
                raise diag
            else:
                val = val[1:-1]
        self.value = val
        self.splitValue()

    def __str__(self):
        if (self.prefix):
            return "%s.%s" % (self.prefix, self.value)
        else:
            return self.value

    def splitValue(self):
        f = self.value.find(".")
        if (self.value.count('.') > 1):
            diag = Diagnostic15()
            diag.details = "Multiple '.' characters: %s" % (self.value)
            raise(diag)
        elif (f == 0):
            diag = Diagnostic15()
            diag.details = "Null indexset: %s" % (irt.index)
            raise(diag)
        elif f >= 0:
            self.prefix = self.value[:f].lower()
            self.value = self.value[f+1:].lower()

    def resolvePrefix(self):
        if (self.prefixURI == ""):
            self.prefixURI = self.parent.resolvePrefix(self.prefix)
        return self.prefixURI

class ModifiableObject:
    # Treat modifiers as keys on boolean/relation?
    modifiers = []

    def __getitem__(self, k):
        if (type(k) == types.IntType):
            try:
                return self.modifiers[k]
            except:
                return None
        for m in self.modifiers:
            if (str(m.type) == k or m.type.value == k):
                return m
        return None
        
class Triple (PrefixableObject):
    "Object to represent a CQL triple"
    leftOperand = None
    boolean = None
    rightOperand = None

    def toXCQL(self, depth=0):
        "Create the XCQL representation of the object"
        space = "  " * depth
        xml = ['%s<triple>\n' % (space)]
        if self.prefixes:
            xml.append(PrefixableObject.toXCQL(self, depth+1))

        xml.append(self.boolean.toXCQL(depth+1))
        xml.append("%s  <leftOperand>\n" % (space))
        xml.append(self.leftOperand.toXCQL(depth+2))
        xml.append("%s  </leftOperand>\n" % (space))
        xml.append("%s  <rightOperand>\n" % (space))
        xml.append(self.rightOperand.toXCQL(depth+2))
        xml.append("%s  </rightOperand>\n" % (space))
        xml.append("%s</triple>\n" % (space))
        return ''.join(xml)

    def toCQL(self):
        txt = []
        if (self.prefixes):
            for p in self.prefixes.keys():
                if (p <> ''):
                    txt.append('>%s="%s"' % (p, self.prefixes[p]))
                else:
                    txt.append('>"%s"' % (self.prefixes[p]))
            prefs = ' '.join(txt)
            return "(%s %s %s %s)" % (prefs, self.leftOperand.toCQL(), self.boolean.toCQL(), self.rightOperand.toCQL())
        else:
            return "(%s %s %s)" % (self.leftOperand.toCQL(), self.boolean.toCQL(), self.rightOperand.toCQL())


    def getResultSetId(self, top=None):

        if fullResultSetNameCheck == 0 or self.boolean.value in ['not', 'prox']:
            return ""

        if top == None:
            topLevel = 1
            top = self;
        else:
            topLevel = 0

        # Iterate over operands and build a list
        rsList = []
        if isinstance(self.leftOperand, Triple):
            rsList.extend(self.leftOperand.getResultSetId(top))
        else:
            rsList.append(self.leftOperand.getResultSetId(top))
        if isinstance(self.rightOperand, Triple):
            rsList.extend(self.rightOperand.getResultSetId(top))
        else:
            rsList.append(self.rightOperand.getResultSetId(top))            

        if topLevel == 1:
            # Check all elements are the same, if so we're a fubar form of present
            if (len(rsList) == rsList.count(rsList[0])):
                return rsList[0]
            else:
                return ""
        else:
            return rsList

class SearchClause (PrefixableObject):
    "Object to represent a CQL searchClause"
    index = None
    relation = None
    term = None

    def __init__(self, ind, rel, t):
        PrefixableObject.__init__(self)
        self.index = ind
        self.relation = rel
        self.term = t
        ind.parent = self
        rel.parent = self
        t.parent = self

    def toXCQL(self, depth=0):
        "Produce XCQL version of the object"
        space = "  " * depth
        xml = [space + "<searchClause>\n"]
        if self.prefixes:
            xml.append(PrefixableObject.toXCQL(self, depth+1))

        xml.append(self.index.toXCQL(depth+1))
        xml.append(self.relation.toXCQL(depth+1))
        xml.append(self.term.toXCQL(depth+1))
        xml.append(space + "</searchClause>\n")
        return ''.join(xml)

    def toCQL(self):
        text = []
        for p in self.prefixes.keys():
            if (p <> ''):
                text.append('>%s="%s"' % (p, self.prefixes[p]))
            else:
                text.append('>"%s"' % (self.prefixes[p]))
        text.append('%s %s "%s"' % (self.index, self.relation.toCQL(), self.term))
        return ' '.join(text)

    def getResultSetId(self):
        idx = self.index
        idx.resolvePrefix()
        if (idx.prefixURI == reservedPrefixes['cql'] and idx.value.lower() == 'resultsetid'):
            return self.term.value
        else:
            return ""

class Index(PrefixedObject):
    "Object to represent a CQL index"

    def toXCQL(self, depth=0):
        return "%s<index>%s</index>\n" % ("  "*depth, escape(str(self)))

    def toCQL(self):
        return str(self)

class Relation(PrefixedObject, ModifiableObject):
    "Object to represent a CQL relation"
    def __init__(self, rel, mods=[]):
        PrefixedObject.__init__(self, rel)
        self.modifiers = mods
    def toXCQL(self, depth=0):
        "Create XCQL representation of object"
        space = ""
        for x in range(depth):
            space = space + "  "
        xml = space + "<relation>\n"
        xml = xml + space + "  <value>" + escape(self.value) + "</value>\n"
        if self.modifiers:
            xml = xml + space + "  <modifiers>\n"
            for m in self.modifiers:
                xml = xml + m.toXCQL(depth+2)
                xml = xml + space + "  </modifiers>\n"
        xml = xml + space + "</relation>\n"
        return xml

    def toCQL(self):
        txt = [self.value]
        txt.extend(map(str, self.modifiers))
        return '/'.join(txt)

class Term:
    value = ""
    def __init__(self, v):
        if (v <> ""):
            # Unquoted literal
            if v in ['>=', '<=', '>', '<', '<>', "/", '=']:
                diag = Diagnostic25()
                diag.details = self.value
                raise diag

            # Check existence of meaningful term
            nonanchor = 0
            for c in v:
                if c != "^":
                    nonanchor = 1
                    break
            if not nonanchor:
                diag = Diagnostic32()
                diag.details = "Only anchoring charater(s) in term: "  + v
                raise diag

            # Unescape quotes
            if (v[0] == '"' and v[-1] == '"'):
                v = v[1:-1]
                v = v.replace('\\"', '"') 

            if (not v and errorOnEmptyTerm):
                diag = Diagnostic27()
                raise diag

            # Check for badly placed \s
            startidx = 0
            idx = v.find("\\", startidx)
            while (idx > -1):
                startidx = idx+1
                if not irt.term[idx+1] in ['?', '\\', '*', '^']:
                    diag = Diagnostic26()
                    diag.details = irt.term
                    raise diag
                v = v.find("\\", startidx)

        elif (errorOnEmptyTerm):
            diag = Diagnostic27()
            raise diag

        self.value = v

    def __str__(self):
        return self.value

    def toXCQL(self, depth=0):
        return "%s<term>%s</term>\n" % ("  "*depth, escape(self.value))

class Boolean(ModifiableObject):
    "Object to represent a CQL boolean"
    value = ""
    parent = None
    def __init__(self, bool, mods=[]):
        self.value = bool
        self.modifiers = mods
        self.parent = None

    def toXCQL(self, depth=0):
        "Create XCQL representation of object"
        space = "  " * depth
        xml = ["%s<boolean>\n" % (space)]
        xml.append("%s  <value>%s</value>\n" % (space, escape(self.value)))
        if self.modifiers:
            xml.append("%s  <modifiers>\n" % (space))
            for m in self.modifiers:
                xml.append(m.toXCQL(depth+2))
            xml.append("%s  </modifiers>\n" % (space))
        xml.append("%s</boolean>\n" % (space))
        return ''.join(xml)

    def toCQL(self):
        txt = [self.value]
        for m in self.modifiers:
            txt.append(m.toCQL())
        return '/'.join(txt)

    def resolvePrefix(self, name):
        return self.parent.resolvePrefix(name)

class ModifierType(PrefixedObject):
    # Same as index, but we'll XCQLify in ModifierClause
    pass

class ModifierClause:
    "Object to represent a relation modifier"
    type = None
    comparison = ""
    value = ""

    def __init__(self, type, comp="", val=""):
        self.type = ModifierType(type)
        self.comparison = comp
        self.value = val

    def __str__(self):
        if (self.value):
            return "%s%s%s" % (str(self.type), self.comparison, self.value)
        else:
            return "%s" % (str(self.type))

    def toXCQL(self, depth=0):
        if (self.value):
            return "%s<modifier>\n%s<type>%s</type>\n%s<comparison>%s</comparison>\n%s<value>%s</value>\n%s</modifier>\n" % ("  " * depth, "  " * (depth+1), escape(str(self.type)), "  " * (depth+1), escape(self.comparison), "  " * (depth+1), escape(self.value), "  " * depth)
        else:
            return "%s<modifier><type>%s</type></modifier>\n" % ("  " * depth, escape(str(self.type)))

    def toCQL(self):
        return str(self)


# Requires changes for:  <= >= <>, and escaped \" in "
# From shlex.py (std library for 2.2+)
class CQLshlex(shlex):
    "shlex with additions for CQL parsing"
    quotes = '"'
    commenters = ""
    nextToken = ""


    def __init__(self, thing):
        shlex.__init__(self, thing)
        self.wordchars += "!@#$%^&*-+{}[];,.?|~`:\\"

    def read_token(self):
        "Read a token from the input stream (no pushback or inclusions)"

        while 1:
            if (self.nextToken != ""):
                self.token = self.nextToken
                self.nextToken = ""
                # Bah. SUPER ugly non portable
                if self.token == "/":
                    self.state = ' '
                    break
                
            nextchar = self.instream.read(1)
            if nextchar == '\n':
                self.lineno = self.lineno + 1
            if self.debug >= 3:
                print "shlex: in state ", repr(self.state),  " I see character:", repr(nextchar)

            if self.state is None:
                self.token = ''        # past end of file
                break
            elif self.state == ' ':
                if not nextchar:
                    self.state = None  # end of file
                    break
                elif nextchar in self.whitespace:
                    if self.debug >= 2:
                        print "shlex: I see whitespace in whitespace state"
                    if self.token:
                        break   # emit current token
                    else:
                        continue
                elif nextchar in self.commenters:
                    self.instream.readline()
                    self.lineno = self.lineno + 1
                elif nextchar in self.wordchars:
                    self.token = nextchar
                    self.state = 'a'
                elif nextchar in self.quotes:
                    self.token = nextchar
                    self.state = nextchar
                elif nextchar in ['<', '>']:
                    self.token = nextchar
                    self.state = '<'
                else:
                    self.token = nextchar
                    if self.token:
                        break   # emit current token
                    else:
                        continue
            elif self.state == '<':
                # Only accumulate <=, >= or <>

                if self.token == ">" and nextchar == "=":
                    self.token = self.token + nextchar
                    self.state = ' '
                    break
                elif self.token == "<" and nextchar in ['>', '=']:
                    self.token = self.token + nextchar
                    self.state = ' '
                    break
                elif not nextchar:
                    self.state = None
                    break
                elif nextchar == "/":
                    self.state = "/"
                    self.nextToken = "/"
                    break
                elif nextchar in self.wordchars:
                    self.state='a'
                    self.nextToken = nextchar
                    break
                elif nextchar in self.quotes:
                    self.state=nextchar
                    self.nextToken = nextchar
                    break
                else:
                    self.state = ' '
                    break
            
            elif self.state in self.quotes:
                self.token = self.token + nextchar
                # Allow escaped quotes
                if nextchar == self.state and self.token[-2] != '\\':
                    self.state = ' '
                    break
                elif not nextchar:      # end of file
                    if self.debug >= 2:
                        print "shlex: I see EOF in quotes state"
                    # Override SHLEX's ValueError to throw diagnostic
                    diag = Diagnostic14()
                    diag.details = self.token[:-1]
                    raise diag
            elif self.state == 'a':
                if not nextchar:
                    self.state = None   # end of file
                    break
                elif nextchar in self.whitespace:
                    if self.debug >= 2:
                        print "shlex: I see whitespace in word state"
                    self.state = ' '
                    if self.token:
                        break   # emit current token
                    else:
                        continue
                elif nextchar in self.commenters:
                    self.instream.readline()
                    self.lineno = self.lineno + 1
                elif nextchar in self.wordchars or nextchar in self.quotes:
                    self.token = self.token + nextchar
                elif nextchar in ['>', '<']:
                    self.nextToken = nextchar
                    self.state = '<'
                    break
                else:
                    self.pushback.appendleft(nextchar)
                    #if self.pushback is not None:
                    #    self.pushback = collections.deque([nextchar]).extend(self.pushback)
                    #else:
                    #    self.pushback = collections.deque([nextchar])
                    if self.debug >= 2:
                        print "shlex: I see punctuation in word state"
                    self.state = ' '
                    if self.token:
                        break   # emit current token
                    else:
                        continue
        result = self.token
        self.token = ''
        if self.debug > 1:
            if result:
                print "shlex: raw token=" + `result`
            else:
                print "shlex: raw token=EOF"
        return result

class CQLParser:
    "Token parser to create object structure for CQL"
    parser = ""
    currentToken = ""
    nextToken = ""

    def __init__(self, p, version="1.2"):
        """ Initialise with shlex parser """
        self.parser = p
        self.fetch_token() # Fetches to next
        self.fetch_token() # Fetches to curr
        serverChoiceRelation = "="
        if version == "1.1":
            serverChoiceRelation = "scr"

    def is_boolean(self, token):
        "Is the token a boolean"
        token = token.lower()
        return token in booleans

    def fetch_token(self):
        """ Read ahead one token """
        tok = self.parser.get_token()
        self.currentToken = self.nextToken
        self.nextToken = tok

    def prefixes(self):
        "Create prefixes dictionary"
        prefs = {}
        while (self.currentToken == ">"):
            # Strip off maps
            self.fetch_token()
            if self.nextToken == "=":
                # Named map
                name = self.currentToken
                self.fetch_token() # = is current
                self.fetch_token() # id is current
                identifier = self.currentToken
                self.fetch_token()
            else:
                name = ""
                identifier = self.currentToken
                self.fetch_token()
            if (errorOnDuplicatePrefix and prefs.has_key(name)):
                # Error condition
                diag = Diagnostic45()
                diag.details = name
                raise diag;
            if len(identifier) > 1 and identifier[0] == '"' and identifier[-1] == '"':
                identifier = identifier[1:-1]
            prefs[name.lower()] = identifier

        return prefs


    def query(self):
        """ Parse query """
        #print "entering query()" + repr((self.currentToken, self.nextToken))
        prefs = self.prefixes()
        left = self.subQuery()
        while 1:
            if not self.currentToken:
                break;
            bool = self.is_boolean(self.currentToken)
            if bool:
                boolobject = self.boolean()
                right = self.subQuery()
                # Setup Left Object
                trip = tripleType()
                trip.leftOperand = left
                trip.boolean = boolobject
                trip.rightOperand = right
                left.parent = trip
                right.parent = trip
                boolobject.parent = trip
                left = trip
            else:
                break;

        for p in prefs.keys():
            left.addPrefix(p, prefs[p])
        return left

    def subQuery(self):
        """ Find either query or clause """
        if self.currentToken == "(":
            #print "1" + repr((self.currentToken, self.nextToken))
            self.fetch_token() # Skip (
            #print "2" + repr((self.currentToken, self.nextToken))
            object = self.query()
            #print "3" +  repr(object)
            #print "4" +  repr((self.currentToken, self.nextToken))
            if self.currentToken == ")":
                self.fetch_token() # Skip )
                #print "5" +  repr((self.currentToken, self.nextToken))
            else:
                diag = Diagnostic13()
                diag.details = self.currentToken
                raise diag
        else:
            #print "going here now" + repr((self.currentToken, self.nextToken))
            prefs = self.prefixes()
            #print "prefs: " + repr(prefs)
            if (prefs):
                object = self.query()
                for p in prefs.keys():
                    object.addPrefix(p, prefs[p])
            else:
                object = self.clause()
            
        return object

    def clause(self):
        """ Find searchClause """
        #print "entering clause "
        bool = self.is_boolean(self.nextToken)
        if not bool and not (self.nextToken in [')', '(', '']):

            index = indexType(self.currentToken)
            self.fetch_token()   # Skip Index
            rel = self.relation()
            if (self.currentToken == ''):
                diag = Diagnostic10()
                diag.details = "Expected Term, got end of query."
                raise(diag)
            term = termType(self.currentToken)
            self.fetch_token()   # Skip Term 

            irt = searchClauseType(index, rel, term)

        elif self.currentToken and (bool or self.nextToken in [')', '']):
            #print "clause B1 " + repr((self.currentToken, self.nextToken))
            irt = searchClauseType(indexType(serverChoiceIndex), relationType(serverChoiceRelation), termType(self.currentToken))
            #print "clause B2 " + repr((self.currentToken, self.nextToken))
            self.fetch_token()
            #print "clause B3 " + repr((self.currentToken, self.nextToken))


        elif self.currentToken == ">":
            prefs = self.prefixes()
            # iterate to get object
            object = self.clause()
            for p in prefs.keys():
                object.addPrefix(p, prefs[p]);
            return object
            
        else:
            diag = Diagnostic10()
            diag.details = "Expected Boolean or Relation but got: " + self.currentToken
            raise diag

        return irt

    def modifiers(self):
        mods = []
        while (self.currentToken == modifierSeparator):
            self.fetch_token()
            mod = self.currentToken
            mod = mod.lower()
            if (mod == modifierSeparator):
                diag = Diagnostic20()
                diag.details = "Null modifier"
                raise diag
            self.fetch_token()
            comp = self.currentToken
            if (comp in order):
                self.fetch_token()
                value = self.currentToken
                self.fetch_token()
            else:
                comp = ""
                value = ""
            mods.append(ModifierClause(mod, comp, value))
        return mods
        

    def boolean(self):
        """ Find boolean """
        self.currentToken = self.currentToken.lower()
        if self.currentToken in booleans:
            bool = booleanType(self.currentToken)
            self.fetch_token()
            bool.modifiers = self.modifiers()
            
        else:
            diag = Diagnostic37()
            diag.details = self.currentToken
            raise diag
                
        return bool

    def relation(self):
        """ Find relation """
        self.currentToken = self.currentToken.lower()
        rel = relationType(self.currentToken)
        self.fetch_token()
        rel.modifiers = self.modifiers()

        return rel



class XCQLParser:
    """ Parser for XCQL using some very simple DOM """

    def firstChildElement(self, elem):
        """ Find first child which is an Element """
        for c in elem.childNodes:
            if c.nodeType == Node.ELEMENT_NODE:
                return c
        return None

    def firstChildData(self,elem):
        """ Find first child which is Data """
        for c in elem.childNodes:
            if c.nodeType == Node.TEXT_NODE:
                return c
        return None

    def searchClause(self, elem):
        """ Process a <searchClause> """
        sc = searchClauseType()
        for c in elem.childNodes:
            if c.nodeType == Node.ELEMENT_NODE:
                if c.localName == "index":
                    sc.index = indexType(self.firstChildData(c).data.lower())
                elif c.localName == "term":
                    sc.term = termType(self.firstChildData(c).data)
                elif c.localName == "relation":
                    sc.relation = self.relation(c)
                elif c.localName == "prefixes":
                    sc.prefixes = self.prefixes(c)
                else:
                    raise(ValueError, c.localName)
        return sc

    def triple(self, elem):
        """ Process a <triple> """
        trip = tripleType()
        for c in elem.childNodes:
            if c.nodeType == Node.ELEMENT_NODE:
                if c.localName == "boolean":
                    trip.boolean = self.boolean(c)
                elif c.localName == "prefixes":
                    trip.prefixes = self.prefixes(c)
                elif c.localName == "leftOperand":
                    c2 = self.firstChildElement(c)
                    if c2.localName == "searchClause":
                        trip.leftOperand = self.searchClause(c2)
                    else:
                        trip.leftOperand = self.triple(c2)
                else:
                    c2 = self.firstChildElement(c)
                    if c2.localName == "searchClause":
                        trip.rightOperand = self.searchClause(c2)
                    else:
                        trip.rightOperand = self.triple(c2)
        return trip

    def relation(self, elem):
        """ Process a <relation> """
        rel = relationType()
        for c in elem.childNodes:
            if c.nodeType == Node.ELEMENT_NODE:
                if c.localName == "value":
                    rel.value = c.firstChild.data.lower()
                elif c.localName == "modifiers":
                    mods = []
                    for c2 in c.childNodes:
                        if c2.nodeType == Node.ELEMENT_NODE:
                            if c2.localName == "modifier":
                                for c3 in c2.childNodes:
                                    if c3.localName == "value":
                                        val = self.firstChildData(c2).data.lower()
                                        mods.append(val)
                    rel.modifiers = mods
        return rel

    def boolean(self, elem):
        "Process a <boolean>"
        bool = booleanType()
        for c in elem.childNodes:
            if c.nodeType == Node.ELEMENT_NODE:
                if c.localName == "value":
                    bool.value = self.firstChildData(c).data.lower()
                else:
                    # Can be in any order, so we need to extract, then order
                    mods = {}
                    for c2 in c.childNodes:
                        if c2.nodeType == Node.ELEMENT_NODE:
                            if c2.localName == "modifier":
                                type = ""
                                value = ""
                                for c3 in c2.childNodes:
                                    if c3.nodeType == Node.ELEMENT_NODE:
                                        if c3.localName == "value":
                                            value = self.firstChildData(c3).data.lower()
                                        elif c3.localName == "type":
                                            type = self.firstChildData(c3).data
                                mods[type] = value

                    modlist = []
                    for t in booleanModifierTypes[1:]:
                        if mods.has_key(t):
                            modlist.append(mods[t])
                        else:
                            modlist.append('')
                    bool.modifiers = modlist
        return bool
        
    def prefixes(self, elem):
        "Process <prefixes>"
        prefs = {}
        for c in elem.childNodes:
            if c.nodeType == Node.ELEMENT_NODE:
                # prefix
                name = ""
                identifier = ""
                for c2 in c.childNodes:
                    if c2.nodeType == Node.ELEMENT_NODE:
                        if c2.localName == "name":
                            name = self.firstChildData(c2).data.lower()
                        elif c2.localName == "identifier":
                            identifier = self.firstChildData(c2).data
                prefs[name] = identifier
        return prefs


def xmlparse(s):
    """ API. Return a seachClause/triple object from XML string """
    doc = parseString(s)
    q = xcqlparse(doc.firstChild)
    return q

def xcqlparse(query):
    """ API.  Return a searchClause/triple object from XML DOM objects"""
    # Requires only properties of objects so we don't care how they're generated

    p = XCQLParser()
    if query.localName == "searchClause":
        return p.searchClause(query)
    else:
        return p.triple(query)


def parse(query):
    """ API. Return a searchClause/triple object from CQL string"""

    # XXX Find/Write full unicode capable shlex!
    try:
        query = query.encode("ascii")
    except:
        diag = Diagnostic10()
        diag.details = "Cannot parse non utf-8 characters"
        raise diag

    q = StringIO(query)
    lexer = CQLshlex(q)
    parser = CQLParser(lexer)
    object = parser.query()
    if parser.currentToken != '':
        diag = Diagnostic10()
        diag.details = "Unprocessed tokens remain: " + repr(parser.currentToken)
        raise diag
    else:
        del lexer
        del parser
        del q
        return object


# Assign our objects to generate
tripleType = Triple
booleanType = Boolean
relationType = Relation
searchClauseType = SearchClause
modifierClauseType = ModifierClause
modifierTypeType = ModifierType
indexType = Index
termType = Term

try:
    from CQLUtils import *
    tripleType = CTriple
    booleanType = CBoolean
    relationType = CRelation
    searchClauseType = CSearchClause
    modifierClauseType = CModifierClause
    modifierTypeType = CModifierType
    indexType = CIndex
    termType = CTerm
except:
    # Nested scopes. Utils needs our classes to parent
    # We need its classes to build (maybe)
    pass
    raise


if (__name__ == "__main__"):
    import sys;
    s = sys.stdin.readline()
    try:
        q = parse(s);
    except SRWDiagnostic, diag:
        # Print a full version, not just str()
        print "Diagnostic Generated."
        print "  Code:        " + str(diag.code)
        print "  Details:     " + str(diag.details)
        print "  Message:     " + str(diag.message)
    else:
        print q.toXCQL()[:-1];
    
