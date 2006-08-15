# -*- coding: utf-8 -*-
##
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

try:
    import sys, re, string
    import os, getopt, cgi
    from cStringIO import StringIO
    from time import mktime, localtime
    from invenio.refextract_config import *
except ImportError, e:
    raise ImportError(e)

class StringBuffer1:
    """This class is a String buffer, used for concatenation of strings.
       This version uses a memory file as a string buffer
    """
    def __init__(self):
        self._bufferFile = StringIO()
    def append(self, itm):
        """Add a string to the string buffer"""
        self._bufferFile.write("%s"%(itm,))
    def get(self):
        """Get buffered string and return it as string object"""
        return self._bufferFile.getvalue()

class StringBuffer2:
    """This class is a String buffer, used for concatenation of strings.
       This version uses a list as a string buffer
    """
    def __init__(self):
        self._buffer = []
    def append(self, itm):
        """Add a new string into the buffer"""
        self._buffer.append(itm)
    def get(self):
        """Join all strings in th buffer into a single string and return it"""
        return ''.join(self._buffer)

class SystemMessage:
    def __init__(self):
        self._helpMessage = """refextract recid:pdffile [recid:pdffile]"""
        self._versionMessage = cfg_refextract_version
    def getHelpMessage(self):
        return self._helpMessage
    def getVersionMessage(self):
        return self._versionMessage

class ReferenceSection:
    """Concrete class representing the Reference section of a document. Once References have been extracted, they are put into a
       ReferenceSection object, which contains a list of "ReferenceLine" objects
    """
    class ReferenceSectionIterator:
        def __init__(self, reflines):
            self._mylist = reflines
            self._listptr = 0
        def next(self):
            try:
                item = self._mylist[self._listptr]
                self._listptr += 1
                return item
            except IndexError:
                raise StopIteration
    def __init__(self, refLineStrings=None):
        """Initialise a ReferenceSection object with the lines composing the references of a document. If a string argument
           is supplied, it will be appended as the first reference line. If a list argument is supplied, each element of the list
           that contains a string will be appended to the list of reference lines in order. Arguments of neither String or
           list type will be ignored and an empty ReferenceSection object will be the result
        """
        self._referenceLines = []
        self._lnPtr = 0
        if refLineStrings is None:
            refLineStrings = []
        if type(refLineStrings) is list:
            for line in refLineStrings:
                self.addNewLine(line)
        else:
            if not self.addNewLine(refLineStrings):
                self._referenceLines = []
        self.resetLinePointer()
    def __iter__(self):
        """return self as iterator object"""
        return ReferenceSection.ReferenceSectionIterator(self._referenceLines)
    def resetLinePointer(self):
        """Reset the position of the ReferenceLine pointer of a ReferenceSection object to point at the first line"""
        self._lnPtr = 0
    def gotoNextLine(self):
        """Move the position of the ReferenceLine pointer of a ReferenceSection object to point at the next line"""
        if self.lineExists(self._lnPtr+1):
            self._lnPtr = self._lnPtr+1
            return True
        else:
            return False
    def gotoLine(self, lNum):
        """Move the position of the ReferenceLine pointer of a ReferenceSection object to point at the line number supplied"""
        if self.lineExists(lNum-1):
            self._lnPtr = lNum-1
            return True
        else:
            return False
    def getCurrentLineAsString(self):
        """Return a String containing the text contents of the ReferenceLine object currently pointed to by the internal
           pointer of a ReferenceSection object. Returns empty string if no ReferenceLine is currently pointed at
        """
        if self.lineExists(self._lnPtr):
            return self._referenceLines[self._lnPtr].getContent()
        else:
            self.resetLinePointer()
            return u''
    def getCurrentLine(self):
        """Return the ReferenceLine object that is currently pointed to by the internal pointer of a ReferenceSection object. If no
           object pointed at, return the 'None' object
        """
        if self.lineExists(self._lnPtr):
            return self._referenceLines[self._lnPtr]
        else:
            self.resetLinePointer()
            return None
    def getLineAsString(self, lNum):
        """Return a String containing the text contents of the ReferenceLine object at the line number supplied (1..n).
           Returns ain empty String if line number does not exist
        """
        if self.lineExists(lNum-1): return self._referenceLines[lNum-1].getContent()
        else: return u""
    def getLine(self, lNum):
        """Return the ReferenceLine at the line number supplied (1..n) Returns 'None' object if line number does not exist"""
        if self.lineExists(lNum-1): return self._referenceLines[lNum-1]
        else: return None
    def getSelfMARCXML(self):
        out = ""
        for x in self._referenceLines:
            out += x.getSelfMARCXML()
        return out
    def displayAllLines(self):
        """Display all ReferenceLine objects stored within a ReferenceSection object consecutively as Strings on the standard output stream"""
        for x in self._referenceLines: x.display()
    def displayCurrentLine(self):
        """Display the ReferenceLine that is currently pointed to by a ReferenceSection object"""
        if self.lineExists(self._lnPtr): self._referenceLines[self._lnPtr].display()
        else: self.resetLinePointer()
    def displayLine(self, lNum):
        """Display the reference line at the line number supplied (1..n).  Will display nothing if the line number does not exist"""
        if self.lineExists(lNum-1): self._referenceLines[lNum-1].display()
    def lineExists(self, lNum):
        """Returns True if line lNum exists in a ReferenceSection, False if not. (Reminder: Lines in the range 0..N)"""
        if (lNum < len(self._referenceLines)) and (lNum >= 0): return True
        else: return False
    def addNewLine(self, lineTxt):
        """Takes one String argument (lineTxt) and attempts to create a new ReferenceLine with this text, adding it to the last
           place in the referenceLines list of a ReferenceSection object. Returns True if successful, False if not
        """
        if type(lineTxt) is str or type(lineTxt) is unicode:
            ln = ReferenceLine(lineTxt)
            self._referenceLines.append(ln)
            return True
        else:
            return False
    def setContentLine(self, newContent):
        """Set the contents of the current line to that supplied in the 'newContent' argument. Return True on success, False on failure"""
        if self.lineExists(self._lnPtr): return self._referenceLines[self._lnPtr].setContent(newContent)
        else: return False
    def lAppendLineText(self, appendStr):
        """Append text to the beginning of the ReferenceLine object currently pointed at by a ReferenceSection object"""
        if self.lineExists(self._lnPtr): return self._referenceLines[self._lnPtr].lAppend(appendStr)
        else: return False
    def rAppendLineText(self, appendStr):
        """Append text to the end of the ReferenceLine object currently pointed at by a ReferenceSection object"""
        if self.lineExists(self._lnPtr): return self._referenceLines[self._lnPtr].rAppend(appendStr)
        else: return False
    def isEmpty(self):
        """Return True if the reference section contains no reference lines, False if it does contain lines"""
        return (len(self._referenceLines) < 1)

class ReferenceLine:
    """Concrete class representing an individual reference line as extracted from a document"""
    def __init__(self, data=''):
        """Initialise a ReferenceLine's contents with the supplied String. If argument supplied is not a String, the ReferenceLine
           object's contents will be initialised with a blank String
        """
        if type(data) is str or type(data) is unicode: self._content = data
        else: self._content = u''
    def getContent(self):
        """Return a String version of a ReferenceLine's contents"""
        return self._content
    def getSelfMARCXML(self):
        out = """   <datafield tag="999" ind1="C" ind2="7">
      <subfield code="f">%(rawline)s</subfield>
   </datafield>\n""" % { 'rawline' : self._content }
        return out
    def display(self):
        """Display a ReferenceLine as a String on the standard output stream"""
        print self._content.encode("utf-8")
    def setContent(self, newContent=u''):
        """Set the content of a ReferenceLine to a new text String. Returns True if successful, False if not"""
        if type(newContent) is str or type(newContent) is unicode:
            self._content = newContent
            return True
        else:
            return False
    def rAppend(self, appendStr):
        """Append a text String to the end of a ReferenceLine object's textual content. Returns True if append successful, False if not"""
        if type(appendStr) is str or type(appendStr) is unicode:
            self._content=self._content + appendStr
            return True
        else:
            return False
    def lAppend(self, appendStr):
        """Append a text String to the beginning of a ReferenceLine objects textual content. Returns True if append successful False if not"""
        if type(appendStr) is str or type(appendStr) is unicode:
            self._content = appendStr+self._content
            return True
        else:
            return False


class ReferenceSectionDisplayer:
    def display(self, extraction_status, cnt_misc, cnt_preprintref, cnt_journalref, cnt_urlref, processed_refsect,\
                raw_refsect, recid=None, myostream=sys.stdout):
        ## sanity checking:
        ## begin display:
        out =  u""" <record>\n"""
        if recid is not None and (type(recid) is unicode or type(recid) is str):
            out += u"""   <controlfield tag="001">""" + cgi.escape(recid) + u"""</controlfield>\n"""

        ## 999C5 (processed references):
        references = processed_refsect.getSelfMARCXML()
        if len(references.strip()) > 0:
            out += references

        ## add the 999C6 status subfields:
        out += u"""   <datafield tag="999" ind1="C" ind2="6">
      <subfield code="a">%(version)s-%(timestamp)s-%(status)s-%(preprintref)s-%(journalref)s-%(urlref)s-%(misc)s</subfield>
   </datafield>\n""" % { 'version'     : cfg_refextract_version,
                         'timestamp'   : str(int(mktime(localtime()))),
                         'status'      : extraction_status,
                         'preprintref' : cnt_preprintref,
                         'journalref'  : cnt_journalref,
                         'urlref'      : cnt_urlref,
                         'misc'        : cnt_misc,
                       }

        ## 999C& (raw references)
        references = raw_refsect.getSelfMARCXML()
        if len(references.strip()) > 0:
            out += references

        ## close record
        out += u""" </record>\n"""

        myostream.write("%s" % (out.encode("utf-8"),))
        myostream.flush()
        return


class RegexWordSpacer:
    """Concrete Class. Adds optional regex space matchers and quantifiers (\s*?) between the characters of a word. Useful because sometimes
       the document conversion process breaks up words with spaces
    """
    def space(self, word):
        """Add the space chars to a word & return the regex pattern (not compiled)"""
        newWord = None
        if type(word) is str or type(word) is unicode:
            newWord = u''
            p_spc = re.compile(unicode(r'\s'),re.UNICODE)
            for x in word:
                m_spc = p_spc.match(x)
                if m_spc is None:
                    newWord = newWord+x+unicode(r'\s*?')
                else:
                    newWord = newWord+x
        return newWord

class DocumentSearchPatternListCompiler:
    """Abstract class. Used to get a 'DocumentSearchCompiledPatternList' object, which is used for searching lines of a document for a
       given pattern
    """
    def getCompiledPatternList(self, prefix = u'', suffix = u''):
        """Return a list of compiled regex patterns"""
        pass
    def createPatterns(self, prefix = u'', suffix = u''):
        """Create the regex patterns (don't compile though)"""
        pass

class RefSecnTitleListCompiler(DocumentSearchPatternListCompiler):
    """Concrete class. Used to return a 'DocumentSearchCompiledPatternList' object containing regex patterns enabling the identification of
       possible reference section titles in a text line
    """
    def getCompiledPatternList(self, prefix = u'', suffix = u''):
        """Return a list of compiled regex patterns used to ID reference section title"""
        patterns = self.createPatterns()
        return CompiledPatternList(patterns)
    def createPatterns(self, prefix = u'', suffix = u''):
        """Create the regex patterns (don't compile though)"""
        patternList = []
        titles = self.getTitles()
        sectMarker = unicode(r'^\s*?([\[\-\{\(])?\s*?((\w|\d){1,5}([\.\-\,](\w|\d){1,5})?\s*?[\.\-\}\)\]]\s*?)?(?P<title>')
        lineEnd = unicode(r'(\s+?s\s*?e\s*?c\s*?t\s*?i\s*?o\s*?n\s*?)?)')
        lineEnd = lineEnd+unicode(r'($|\s*?[\[\{\(\<]\s*?[1a-z]\s*?[\}\)\>\]]|\:)')
        s = RegexWordSpacer()
        for x in titles:
            if (type(x) is str or type(x) is unicode) and len(x) > 1:
                s = RegexWordSpacer()
                namePtn = sectMarker+s.space(x)+lineEnd
                patternList.append(namePtn)
            elif (type(x) is str or type(x) is unicode) and len(x) > 0:
                namePtn = sectMarker+s.space(x)+lineEnd
                patternList.append(namePtn)
        return patternList
    def getTitles(self):
        """Get and return a list of the titles to be searched for"""
        titles = []
        titles.append(u'references')
        titles.append(u'r\u00C9f\u00E9rences')
        titles.append(u'r\u00C9f\u00C9rences')
        titles.append(u'reference')
        titles.append(u'refs')
        titles.append(u'r\u00E9f\u00E9rence')
        titles.append(u'r\u00C9f\u00C9rence')
        titles.append(u'r\xb4ef\xb4erences')
        titles.append(u'r\u00E9fs')
        titles.append(u'r\u00C9fs')
        titles.append(u'bibliography')
        titles.append(u'bibliographie')
        titles.append(u'citations')
        return titles

class PostRefSecnTitleListCompiler(DocumentSearchPatternListCompiler):
    """Concrete class. Used to return a 'DocumentSearchCompiledPatternList' object containing regex patterns enabling the identification of
       possible titles that usually follow the reference section in a doc
    """
    def getCompiledPatternList(self, prefix='', suffix=''):
        """Return a list of compiled regex patterns used to ID post reference section title"""
        patterns = self.createPatterns()
        return CompiledPatternList(patterns)
    def createPatterns(self, prefix='', suffix=''):
        """Create the regex patterns (don't compile though)"""
        patterns = []
        thead = unicode(r'^\s*?([\{\(\<\[]?\s*?(\w|\d)\s*?[\)\}\>\.\-\]]?\s*?)?')
        ttail = unicode(r'(\s*?\:\s*?)?')
        numatn = unicode(r'(\d+|\w\b|i{1,3}v?|vi{0,3})[\.\,]?\b')
        s = RegexWordSpacer()
        # Section titles:
        patterns.append(thead + s.space(u'appendix') + ttail)
        patterns.append(thead + s.space(u'appendices') + ttail)
        patterns.append(thead + s.space(u'acknowledgement') + unicode(r's?') + ttail)
        patterns.append(thead + s.space(u'table') + unicode(r'\w?s?\d?') + ttail)
        patterns.append(thead + s.space(u'figure') + unicode(r's?') + ttail)
        patterns.append(thead + s.space(u'annex') + unicode(r's?') + ttail)
        patterns.append(thead + s.space(u'discussion') + unicode(r's?') + ttail)
        patterns.append(thead + s.space(u'remercie') + unicode(r's?') + ttail)
        # Figure nums:
        patterns.append(r'^\s*?' + s.space(u'figure') + numatn)
        patterns.append(r'^\s*?' + s.space(u'fig') + unicode(r'\.\s*?') + numatn)
        patterns.append(r'^\s*?' + s.space(u'fig') + unicode(r'\.?\s*?\d\w?\b'))
        # Table nums:
        patterns.append(r'^\s*?' + s.space(u'table') + numatn)
        patterns.append(r'^\s*?' + s.space(u'tab') + unicode(r'\.\s*?') + numatn)
        patterns.append(r'^\s*?' + s.space(u'tab') + unicode(r'\.?\s*?\d\w?\b'))
        return patterns

class PostRefSecnKWListCompiler(DocumentSearchPatternListCompiler):
    """Concrete class. Used to return a 'DocumentSearchCompiledPatternList' object containing regex patterns enabling the identification of
       Key Words/phrases that are often found in lines following the reference section of a document
    """
    def getCompiledPatternList(self, prefix=u'', suffix=u''):
        """Return a list of compiled regex patterns used to ID keywords usually found in lines after a reference section"""
        patterns = self.createPatterns()
        return CompiledPatternList(patterns)
    def createPatterns(self, prefix=u'', suffix=u''):
        """Create the regex patterns (don't compile though)"""
        patterns = []
        s = RegexWordSpacer()
        patterns.append(unicode(r'(') + s.space(u'prepared') + unicode(r'|') + s.space(u'created') + unicode(r').*?(AAS\s*?)?\sLATEX'))
        patterns.append(unicode(r'AAS\s+?LATEX\s+?') + s.space(u'macros') + u'v')
        patterns.append(unicode(r'^\s*?') + s.space(u'This paper has been produced using'))
        patterns.append(unicode(r'^\s*?') + s.space(u'This article was processed by the author using Springer-Verlag') + u' LATEX')
        return patterns

class FirstRefLineNumerationListCompiler(DocumentSearchPatternListCompiler):
    """Concrete class. Used to return a 'DocumentSearchCompiledPatternList' object containing regex patterns enabling the identification of
       the first reference line by its numeration marker
    """
    def getCompiledPatternList(self, prefix=u'', suffix=u''):
        """Return a list of compiled regex patterns used to ID the first reference line by its numeration marker"""
        patterns = self.createPatterns()
        return CompiledPatternList(patterns)
    def createPatterns(self, prefix=u'', suffix=u''):
        """Create the regex patterns (don't compile though)"""
        patterns = []
        g_name = unicode(r'(?P<mark>')
        g_close = u')'
        patterns.append(g_name + unicode(r'(?P<left>\[)\s*?(?P<num>\d+)\s*?(?P<right>\])') + g_close)
        patterns.append(g_name + unicode(r'(?P<left>\{)\s*?(?P<num>\d+)\s*?(?P<right>\})') + g_close)
        return patterns

class RefLineNumerationListCompiler(DocumentSearchPatternListCompiler):
    """Concrete class. Used to return a 'DocumentSearchCompiledPatternList' object containing regex patterns enabling the ID of any reference
       line by its numeration marker
    """
    def getCompiledPatternList(self, prefix = u'', suffix = u''):
        """Return a list of compiled regex patterns used to ID the numeration marker for a reference line"""
        patterns = self.createPatterns()
        return CompiledPatternList(patterns)
    def createPatterns(self, prefix=u'', suffix=u''):
        """Create the regex patterns (don't compile though)"""
        patterns = []
        if type(prefix) is str or type(prefix) is unicode:
            title = prefix
        else:
            title = u''
        g_name = unicode(r'(?P<mark>')
        g_close = u')'
        space = unicode(r'\s*?')
        patterns.append(space + title + g_name + unicode(r'\[\s*?(?P<linenumber>\d+)\s*?\]') + g_close)
        patterns.append(space + title + g_name + unicode(r'\[\s*?[a-zA-Z]+\s?(\d{1,4}[A-Za-z]?)?\s*?\]') + g_close)
        patterns.append(space + title + g_name + unicode(r'\{\s*?\d+\s*?\}') + g_close)
        patterns.append(space + title + g_name + unicode(r'\<\s*?\d+\s*?\>') + g_close)
        patterns.append(space + title + g_name + unicode(r'\(\s*?\d+\s*?\)') + g_close)
        patterns.append(space + title + g_name + unicode(r'(?P<marknum>\d+)\s*?\.') + g_close)
        patterns.append(space + title + g_name + unicode(r'\d+\s*?') + g_close)
        patterns.append(space + title + g_name + unicode(r'\d+\s*?\]') + g_close)
        patterns.append(space + title + g_name + unicode(r'\d+\s*?\}') + g_close)
        patterns.append(space + title + g_name + unicode(r'\d+\s*?\)') + g_close)
        patterns.append(space + title + g_name + unicode(r'\d+\s*?\>') + g_close)
        patterns.append(space + title + g_name + unicode(r'\[\s*?\]') + g_close)
        patterns.append(space + title + g_name + unicode(r'\*') + g_close)
        return patterns

class CompiledPatternList:
    """Concrete Class. List of compiled regex patterns, ready to be used for searching through text lines"""
    class CompiledPatternListIterator:
        def __init__(self, ptnlines):
            self._mylist = ptnlines
            self._listptr = 0
        def next(self):
            try:
                item = self._mylist[self._listptr]
                self._listptr += 1
                return item
            except IndexError:
                raise StopIteration
    def __init__(self, patternList):
        """Accept a list of regex strings and compile them, adding them to the internal list of compiled regex patterns"""
        self._patterns = []
        if type(patternList) is list:
            for x in patternList:
                self._patterns.append(re.compile(x, re.I|re.UNICODE))
    def __iter__(self):
        """Return a CompiledPatternListIterator object so that the patterns held by a CompiledPatternList can be iterated through"""
        return CompiledPatternList.CompiledPatternListIterator(self._patterns)
    def getNumPatterns(self):
        """Return the length of the internal pattern list (patterns)"""
        return len(self._patterns)
    def getPattern(self, ptnIdx):
        """Return the regex pattern at [ptnIdx] in the internal pattern list (self._patterns). Returns 'None' if ptnIdx not valid"""
        if type(ptnIdx) is int and ptnIdx < len(self._patterns) and ptnIdx > -1:
            return self._patterns[ptnIdx]
        else:
            return None
    def display(self):
        """Display all patterns held in a CompiledPatternList object"""
        for x in self._patterns:
            print x.pattern.encode("utf-8")

class LineSearchAlgorithm:
    """Search algorithm for matching a pattern in a line"""
    def doSearch(self, searcher, line, patternList):
        """Search for a pattern in a line of text"""
        match = None
        unsafe = False
        try: getNumPatterns=patternList.getNumPatterns
        except AttributeError: unsafe=True
        if (type(line) is str or type(line) is unicode) and not unsafe:
            for x in patternList:
                match = searcher.goSearch(line, x)
                if match is not None:
                    break
        return match

class SearchExecuter:
    """Abstract class. Executes a regex search operation on a line of text which is passed to it"""
    def goSearch(self, line, pattern):
        """Execute the search and return a match object or None"""
        pass

class MatchSearchExecuter(SearchExecuter):
    """Concrete class. Executes a 're.match()' on a compiled re pattern"""
    def goSearch(self, line, pattern):
        """Execute the search and return a 'Match' object or None"""
        return pattern.match(line)

class SearchSearchExecuter(SearchExecuter):
    """Concrete class. Executes a 're.search()' on a compiled re pattern"""
    def goSearch(self, line, pattern):
        """Execute the search and return a 'Match' object or None"""
        return pattern.search(line)

class LineSearcher:
    """Concrete Class. This is the interface through which the user can carry out a line search"""
    def findAtStartLine(self, line, patternList):
        """Test a line of text against a list of patterns to see if any of the patterns match at the start of the line"""
        al = LineSearchAlgorithm()
        searcher = MatchSearchExecuter()
        return al.doSearch(searcher, line, patternList)
    def findWithinLine(self, line, patternList):
        """Test a line of text against a list of patterns to see if any of the patterns match anywhere within the line"""
        al = LineSearchAlgorithm()
        searcher = SearchSearchExecuter()
        return al.doSearch(searcher, line, patternList)

class TextLineTransformer:
    """Abstract Class Interface. Accepts line, performs some transformationon it and returns transformed line"""
    def processLine(self, line):
        """Carry out transformation on line. Return transformed line"""
        pass


class EscapeSequenceTransformer(TextLineTransformer):
    """Class to correct escape seq's which were not properly represented in the document conversion"""
    def __init__(self):
        """Compile & initialise pattern list"""
        self._patterns = self._getPatterns()
    def processLine(self, line):
        """Transform accents in a line into correct format"""
        try:
            for x in self._patterns.keys():
                try:
                    line = line.replace(x, self._patterns[x])
                except UnicodedecodeError:
                    sys.exit(0)
        except TypeError:
            pass
        return line
    def _getPatterns(self):
        """Return a list of regex patterns used to recognise escaped patterns"""
        plist = {}
        def _addLanguageTagCodePoints(ptnlist):
            """Add all language tag code points to remove from document"""
            # Language Tag Code Points:
            langTagCPs = [u"\U000E0000",u"\U000E0001",u"\U000E0002",u"\U000E0003",u"\U000E0004",u"\U000E0005",u"\U000E0006",u"\U000E0007",u"\U000E0008",u"\U000E0009",u"\U000E000A",u"\U000E000B",u"\U000E000C",u"\U000E000D",u"\U000E000E",u"\U000E000F",
                        u"\U000E0010",u"\U000E0011",u"\U000E0012",u"\U000E0013",u"\U000E0014",u"\U000E0015",u"\U000E0016",u"\U000E0017",u"\U000E0018",u"\U000E0019",u"\U000E001A",u"\U000E001B",u"\U000E001C",u"\U000E001D",u"\U000E001E",u"\U000E001F",
                        u"\U000E0020",u"\U000E0021",u"\U000E0022",u"\U000E0023",u"\U000E0024",u"\U000E0025",u"\U000E0026",u"\U000E0027",u"\U000E0028",u"\U000E0029",u"\U000E002A",u"\U000E002B",u"\U000E002C",u"\U000E002D",u"\U000E002E",u"\U000E002F",
                        u"\U000E0030",u"\U000E0031",u"\U000E0032",u"\U000E0033",u"\U000E0034",u"\U000E0035",u"\U000E0036",u"\U000E0037",u"\U000E0038",u"\U000E0039",u"\U000E003A",u"\U000E003B",u"\U000E003C",u"\U000E003D",u"\U000E003E",u"\U000E003F",
                        u"\U000E0040",u"\U000E0041",u"\U000E0042",u"\U000E0043",u"\U000E0044",u"\U000E0045",u"\U000E0046",u"\U000E0047",u"\U000E0048",u"\U000E0049",u"\U000E004A",u"\U000E004B",u"\U000E004C",u"\U000E004D",u"\U000E004E",u"\U000E004F",
                        u"\U000E0050",u"\U000E0051",u"\U000E0052",u"\U000E0053",u"\U000E0054",u"\U000E0055",u"\U000E0056",u"\U000E0057",u"\U000E0058",u"\U000E0059",u"\U000E005A",u"\U000E005B",u"\U000E005C",u"\U000E005D",u"\U000E005E",u"\U000E005F",
                        u"\U000E0060",u"\U000E0061",u"\U000E0062",u"\U000E0063",u"\U000E0064",u"\U000E0065",u"\U000E0066",u"\U000E0067",u"\U000E0068",u"\U000E0069",u"\U000E006A",u"\U000E006B",u"\U000E006C",u"\U000E006D",u"\U000E006E",u"\U000E006F",
                        u"\U000E0070",u"\U000E0071",u"\U000E0072",u"\U000E0073",u"\U000E0074",u"\U000E0075",u"\U000E0076",u"\U000E0077",u"\U000E0078",u"\U000E0079",u"\U000E007A",u"\U000E007B",u"\U000E007C",u"\U000E007D",u"\U000E007E",u"\U000E007F"]
            for itm in langTagCPs: ptnlist[itm] = u""
        def _addMusicNotation(ptnlist):
            """Add all musical notation items to remove from document"""
            # Musical Notation Scoping
            musicNotation = [u"\U0001D173",u"\U0001D174",u"\U0001D175",u"\U0001D176",u"\U0001D177",u"\U0001D178",u"\U0001D179",u"\U0001D17A"]
            for itm in musicNotation: ptnlist[itm] = u""
        # Control characters not suited to XML:
        plist[u'\u2028'] = u""
        plist[u'\u2029'] = u""
        plist[u'\u202A'] = u""
        plist[u'\u202B'] = u""
        plist[u'\u202C'] = u""
        plist[u'\u202D'] = u""
        plist[u'\u202E'] = u""
        plist[u'\u206A'] = u""
        plist[u'\u206B'] = u""
        plist[u'\u206C'] = u""
        plist[u'\u206D'] = u""
        plist[u'\u206E'] = u""
        plist[u'\u206F'] = u""
        plist[u'\uFFF9'] = u""
        plist[u'\uFFFA'] = u""
        plist[u'\uFFFB'] = u""
        plist[u'\uFFFC'] = u""
        plist[u'\uFEFF'] = u""
        _addLanguageTagCodePoints(plist)
        _addMusicNotation(plist)
        plist[u'\u0001'] = u"" # START OF HEADING
        # START OF TEXT & END OF TEXT:
        plist[u'\u0002'] = u""
        plist[u'\u0003'] = u""
        plist[u'\u0004'] = u"" # END OF TRANSMISSION
        # ENQ and ACK
        plist[u'\u0005'] = u""
        plist[u'\u0006'] = u""
        plist[u'\u0007'] = u""     # BELL
        plist[u'\u0008'] = u""     # BACKSPACE
        # SHIFT-IN & SHIFT-OUT
        plist[u'\u000E'] = u""
        plist[u'\u000F'] = u""
        # Other controls:
        plist[u'\u0010'] = u"" # DATA LINK ESCAPE
        plist[u'\u0011'] = u"" # DEVICE CONTROL ONE
        plist[u'\u0012'] = u"" # DEVICE CONTROL TWO
        plist[u'\u0013'] = u"" # DEVICE CONTROL THREE
        plist[u'\u0014'] = u"" # DEVICE CONTROL FOUR
        plist[u'\u0015'] = u"" # NEGATIVE ACK
        plist[u'\u0016'] = u"" # SYNCRONOUS IDLE
        plist[u'\u0017'] = u"" # END OF TRANSMISSION BLOCK
        plist[u'\u0018'] = u"" # CANCEL
        plist[u'\u0019'] = u"" # END OF MEDIUM
        plist[u'\u001A'] = u"" # SUBSTITUTE
        plist[u'\u001B'] = u"" # ESCAPE
        plist[u'\u001C'] = u"" # INFORMATION SEPARATOR FOUR (file separator)
        plist[u'\u001D'] = u"" # INFORMATION SEPARATOR THREE (group separator)
        plist[u'\u001E'] = u"" # INFORMATION SEPARATOR TWO (record separator)
        plist[u'\u001F'] = u"" # INFORMATION SEPARATOR ONE (unit separator)
        # \r -> remove it
        plist[u'\r'] = u""
        # Strange parantheses - change for normal:
        plist[u'\x1c']   = u'('
        plist[u'\x1d']   = u')'
        # Some ff from tex:
        plist[u'\u0013\u0010']   = u'\u00ED'
        plist[u'\x0b']   = u'ff'
        # fi from tex:
        plist[u'\x0c']   = u'fi'
        # ligatures from TeX:
        plist[u'\ufb00'] = u'ff'
        plist[u'\ufb01'] = u'fi'
        plist[u'\ufb02'] = u'fl'
        plist[u'\ufb03'] = u'ffi'
        plist[u'\ufb04'] = u'ffl'
        # Superscripts from TeX
        plist[u'\u2212'] = u'-'
        plist[u'\u2013'] = u'-'
        # Word style speech marks:
        plist[u'\u201d'] = u'"'
        plist[u'\u201c'] = u'"'
        # pdftotext has problems with umlaut and prints it as diaeresis followed by a letter:correct it
        # (Optional space between char and letter - fixes broken line examples)
        plist[u'\u00A8 a'] = u'\u00E4'
        plist[u'\u00A8 e'] = u'\u00EB'
        plist[u'\u00A8 i'] = u'\u00EF'
        plist[u'\u00A8 o'] = u'\u00F6'
        plist[u'\u00A8 u'] = u'\u00FC'
        plist[u'\u00A8 y'] = u'\u00FF'
        plist[u'\u00A8 A'] = u'\u00C4'
        plist[u'\u00A8 E'] = u'\u00CB'
        plist[u'\u00A8 I'] = u'\u00CF'
        plist[u'\u00A8 O'] = u'\u00D6'
        plist[u'\u00A8 U'] = u'\u00DC'
        plist[u'\u00A8 Y'] = u'\u0178'
        plist[u'\xA8a'] = u'\u00E4'
        plist[u'\xA8e'] = u'\u00EB'
        plist[u'\xA8i'] = u'\u00EF'
        plist[u'\xA8o'] = u'\u00F6'
        plist[u'\xA8u'] = u'\u00FC'
        plist[u'\xA8y'] = u'\u00FF'
        plist[u'\xA8A'] = u'\u00C4'
        plist[u'\xA8E'] = u'\u00CB'
        plist[u'\xA8I'] = u'\u00CF'
        plist[u'\xA8O'] = u'\u00D6'
        plist[u'\xA8U'] = u'\u00DC'
        plist[u'\xA8Y'] = u'\u0178'
        # More umlaut mess to correct:
        plist[u'\x7fa'] = u'\u00E4'
        plist[u'\x7fe'] = u'\u00EB'
        plist[u'\x7fi'] = u'\u00EF'
        plist[u'\x7fo'] = u'\u00F6'
        plist[u'\x7fu'] = u'\u00FC'
        plist[u'\x7fy'] = u'\u00FF'
        plist[u'\x7fA'] = u'\u00C4'
        plist[u'\x7fE'] = u'\u00CB'
        plist[u'\x7fI'] = u'\u00CF'
        plist[u'\x7fO'] = u'\u00D6'
        plist[u'\x7fU'] = u'\u00DC'
        plist[u'\x7fY'] = u'\u0178'
        plist[u'\x7f a'] = u'\u00E4'
        plist[u'\x7f e'] = u'\u00EB'
        plist[u'\x7f i'] = u'\u00EF'
        plist[u'\x7f o'] = u'\u00F6'
        plist[u'\x7f u'] = u'\u00FC'
        plist[u'\x7f y'] = u'\u00FF'
        plist[u'\x7f A'] = u'\u00C4'
        plist[u'\x7f E'] = u'\u00CB'
        plist[u'\x7f I'] = u'\u00CF'
        plist[u'\x7f O'] = u'\u00D6'
        plist[u'\x7f U'] = u'\u00DC'
        plist[u'\x7f Y'] = u'\u0178'
        # pdftotext: fix accute accent:
        plist[u'\x13a']     = u'\u00E1'
        plist[u'\x13e']     = u'\u00E9'
        plist[u'\x13i']     = u'\u00ED'
        plist[u'\x13o']     = u'\u00F3'
        plist[u'\x13u']     = u'\u00FA'
        plist[u'\x13y']     = u'\u00FD'
        plist[u'\x13A']     = u'\u00C1'
        plist[u'\x13E']     = u'\u00C9'
        plist[u'\x13I']     = u'\u00CD'
        plist[u'\x13O']     = u'\u00D3'
        plist[u'\x13U']     = u'\u00DA'
        plist[u'\x13Y']     = u'\u00DD'
        plist[u'\x13 a']     = u'\u00E1'
        plist[u'\x13 e']     = u'\u00E9'
        plist[u'\x13 i']     = u'\u00ED'
        plist[u'\x13 o']     = u'\u00F3'
        plist[u'\x13 u']     = u'\u00FA'
        plist[u'\x13 y']     = u'\u00FD'
        plist[u'\x13 A']     = u'\u00C1'
        plist[u'\x13 E']     = u'\u00C9'
        plist[u'\x13 I']     = u'\u00CD'
        plist[u'\x13 O']     = u'\u00D3'
        plist[u'\x13 U']     = u'\u00DA'
        plist[u'\x13 Y']     = u'\u00DD'
        plist[u'\u00B4 a'] = u'\u00E1'
        plist[u'\u00B4 e'] = u'\u00E9'
        plist[u'\u00B4 i'] = u'\u00ED'
        plist[u'\u00B4 o'] = u'\u00F3'
        plist[u'\u00B4 u'] = u'\u00FA'
        plist[u'\u00B4 y'] = u'\u00FD'
        plist[u'\u00B4 A'] = u'\u00C1'
        plist[u'\u00B4 E'] = u'\u00C9'
        plist[u'\u00B4 I'] = u'\u00CD'
        plist[u'\u00B4 O'] = u'\u00D3'
        plist[u'\u00B4 U'] = u'\u00DA'
        plist[u'\u00B4 Y'] = u'\u00DD'
        plist[u'\u00B4a'] = u'\u00E1'
        plist[u'\u00B4e'] = u'\u00E9'
        plist[u'\u00B4i'] = u'\u00ED'
        plist[u'\u00B4o'] = u'\u00F3'
        plist[u'\u00B4u'] = u'\u00FA'
        plist[u'\u00B4y'] = u'\u00FD'
        plist[u'\u00B4A'] = u'\u00C1'
        plist[u'\u00B4E'] = u'\u00C9'
        plist[u'\u00B4I'] = u'\u00CD'
        plist[u'\u00B4O'] = u'\u00D3'
        plist[u'\u00B4U'] = u'\u00DA'
        plist[u'\u00B4Y'] = u'\u00DD'
        # pdftotext: fix grave accent:
        plist[u'\u0060 a'] = u'\u00E0'
        plist[u'\u0060 e'] = u'\u00E8'
        plist[u'\u0060 i'] = u'\u00EC'
        plist[u'\u0060 o'] = u'\u00F2'
        plist[u'\u0060 u'] = u'\u00F9'
        plist[u'\u0060 A'] = u'\u00C0'
        plist[u'\u0060 E'] = u'\u00C8'
        plist[u'\u0060 I'] = u'\u00CC'
        plist[u'\u0060 O'] = u'\u00D2'
        plist[u'\u0060 U'] = u'\u00D9'
        plist[u'\u0060a'] = u'\u00E0'
        plist[u'\u0060e'] = u'\u00E8'
        plist[u'\u0060i'] = u'\u00EC'
        plist[u'\u0060o'] = u'\u00F2'
        plist[u'\u0060u'] = u'\u00F9'
        plist[u'\u0060A'] = u'\u00C0'
        plist[u'\u0060E'] = u'\u00C8'
        plist[u'\u0060I'] = u'\u00CC'
        plist[u'\u0060O'] = u'\u00D2'
        plist[u'\u0060U'] = u'\u00D9'
        # \02C7 : caron
        plist[u'\u02C7C'] = u'\u010C'
        plist[u'\u02C7c'] = u'\u010D'
        plist[u'\u02C7S'] = u'\u0160'
        plist[u'\u02C7s'] = u'\u0161'
        plist[u'\u02C7Z'] = u'\u017D'
        plist[u'\u02C7z'] = u'\u017E'
        # \027 : aa (a with ring above)
        plist[u'\u02DAa'] = u'\u00E5'
        plist[u'\u02DAA'] = u'\u00C5'
        # \030 : cedilla
        plist[u'\u0327c'] = u'\u00E7'
        plist[u'\u0327C'] = u'\u00C7'    
        return plist

class URLRepairer(TextLineTransformer):
    """Class to attempt to re-assemble URLs which have been broken during the document's conversion to text"""
    def __init__(self):
        """Initialise the URI correction pattern list"""
        self._patterns = self._compilePatterns(self._getPatterns())
    def processLine(self, line):
        """Repair any broken URLs in line and return newly repaired line"""
        def chop_spaces(m):
            chopper = SpaceNullifier()
            line = m.group(1)
            return chopper.processLine(line)
        if type(line) is str or type(line) is unicode:
            for x in self._patterns:
                line = x.sub(chop_spaces, line)
        return line
    def _getPatterns(self):
        """Return a list regex patterns and corrective measures to be used when broken URLs are encountered in a line"""
        fileTypesList = []
        fileTypesList.append(unicode(r'h\s*?t\s*?m'))           # htm
        fileTypesList.append(unicode(r'h\s*?t\s*?m\s*?l'))      # html
        fileTypesList.append(unicode(r't\s*?x\s*?t'))           # txt
        fileTypesList.append(unicode(r'p\s*?h\s*?p'))           # php
        fileTypesList.append(unicode(r'a\s*?s\s*?p\s*?'))       # asp
        fileTypesList.append(unicode(r'j\s*?s\s*?p'))           # jsp
        fileTypesList.append(unicode(r'p\s*?y'))                # py (python)
        fileTypesList.append(unicode(r'p\s*?l'))                # pl (perl)
        fileTypesList.append(unicode(r'x\s*?m\s*?l'))           # xml
        fileTypesList.append(unicode(r'j\s*?p\s*?g'))           # jpg
        fileTypesList.append(unicode(r'g\s*?i\s*?f'))           # gif
        fileTypesList.append(unicode(r'm\s*?o\s*?v'))           # mov
        fileTypesList.append(unicode(r's\s*?w\s*?f'))           # swf
        fileTypesList.append(unicode(r'p\s*?d\s*?f'))           # pdf
        fileTypesList.append(unicode(r'p\s*?s'))                # ps
        fileTypesList.append(unicode(r'd\s*?o\s*?c'))           # doc
        fileTypesList.append(unicode(r't\s*?e\s*?x'))           # tex
        fileTypesList.append(unicode(r's\s*?h\s*?t\s*?m\s*?l')) # shtml
        plist = []
        plist.append(unicode(r'(h\s*t\s*t\s*p\s*\:\s*\/\s*\/)'))
        plist.append(unicode(r'(f\s*t\s*p\s*\:\s*\/\s*\/\s*)'))
        plist.append(unicode(r'((http|ftp):\/\/\s*[\w\d])'))
        plist.append(unicode(r'((http|ftp):\/\/([\w\d\s\._\-])+?\s*\/)'))
        plist.append(unicode(r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\s\.\-])+?\/)+)'))
        plist.append(unicode(r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\s\.\-])+?\/)*([\w\d\_\s\-]+\.\s?[\w\d]+))'))
        # some possible endings for URLs:
        for x in fileTypesList:
            plist.append(unicode(r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\.\-])+?\/)*([\w\d\_\-]+\.') + x + u'))')
        # if url last thing in line, and only 10 letters max, concat them
        plist.append(unicode(r'((http|ftp):\/\/([\w\d\_\.\-])+\/(([\w\d\_\.\-])+?\/)*'\
                             r'\s*?([\w\d\_\.\-]\s?){1,10}\s*)$'))
        return plist
    def _compilePatterns(self, plist):
        """Compile regex patterns. Return mapping object containing patterns and replacement strings for each pattern"""
        ptns = []
        for x in plist:
            ptns.append(re.compile(x, re.I+re.UNICODE))
        return ptns

class SpaceNullifier(TextLineTransformer):
    """Class to remove all spaces from a text string"""
    def __init__(self):
        """Initialise space chopping pattern"""
        self.ptn = re.compile(unicode(r'\s+'), re.UNICODE)
        self.rep = u''
    def processLine(self, line):
        """Perform the act of chopping spaces from a line. Return line with no spaces in it"""
        newLine = line
        if type(newLine) is str or type(newLine) is unicode:
            newLine = self.ptn.sub(self.rep, line)
        return newLine

class MultispaceTruncator(TextLineTransformer):
    """Class to transform  multiple spaces into a single space"""
    def __init__(self):
        """Initialise space detection pattern"""
        self.ptn = re.compile(unicode(r'\s{2,}'), re.UNICODE)
        self.rep = u' '
    def processLine(self, line):
        """Perform the act of detecting and replacing multiple spaces"""
        newLine = line
        if type(newLine) is str or type(newLine) is unicode:
            newLine = self.ptn.sub(self.rep, line)
        return newLine

class Document:
    """Abstract class Representing a fulltext document in the system"""
    def __init__(self, newDocBody = [], filepath = None):
        """Initialise state of a document object"""
        self._content = []
        if filepath is not None:
            self._file_readlines(filepath)
        elif type(newDocBody) is list or type(newDocBody) is str or type(newDocBody) is unicode:
            self.appendData(newDocBody)
    def _file_readlines(self, fname):
        try:
            fh=open("%s" % (fname,), "r")
            for line in fh: self._content.append(line.decode("utf-8"))
            fh.close()
        except IOError:
            sys.stderr.write("""E: Failed to read in file "%s".\n""" % (fname,))
        except ValueError:
            sys.stderr.write("""E: Failed to read in file "%s".\n""" % (fname,))
    def displayDocument(self):
        """Abstract: Display the Document"""
        pass
    def appendData(self, newData):   
        """Add a text line to a TextDocument object"""
        if type(newData) is list:
            for line in newData:
                self._content.append(line)
        elif type(newData) is str or type(newData) is unicode:
            self._content.append(newData)
    def isEmpty(self):
        """Return 1 if self._content is empty; 0 if not"""
        return (len(self._content) < 1)

class TextDocument(Document):
    """Concrete class representing a TextDocument - effectively a list of Strings of plaintext"""
    def __init__(self,  newDocBody = [], filepath = None):
        """Initialise a TextDocument object"""
        Document.__init__(self, newDocBody, filepath)
    def displayDocument(self):
        for i in self._content: print i.encode("utf-8")
    def getReferences(self, start, end):
        """Get the reference section lines, put them into a ReferenceSectionRebuilder object, ask it to rebuild the
           lines, and return the resulting ReferenceSection object
        """
        startIdx = None
        if start.firstLineIsTitleAndMarker():
            # Title on same line as 1st ref- take title out!
            t = start.getTitleString()
            startIdx = start.getLineNum()
            newline = None
            sp = re.compile(unicode(r'^.*?') + t, re.UNICODE)
            newl = sp.split(self._content[startIdx], 1)
            self._content[startIdx] = newl[1]
        elif start.titlePresent():
            # Pass title
            startIdx = start.getLineNum() + 1
        else:
            startIdx = start.getLineNum()
        if type(end) is int:
            b = ReferenceSectionRebuilder(self._content[startIdx:end+1])
        else:
            b = ReferenceSectionRebuilder()
        return b.getRebuiltLines(start)
    def findEndReferenceSection(self, refStart):
        """Find the line number of the end of a TextDocument's reference section. Should be passed a ReferenceSectionStartPoint
           object containing at least the start line of the reference section. Returns the reference section end line number
           details if success, None if not
        """
        if refStart is None or refStart.getLineNum() is None:
            # No reference section start info!
            return None
        sectEnded = 0
        x = refStart.getLineNum()
        if (type(x) is not int) or (x<0) or (x>len(self._content)) or (len(self._content)<1):
            # Cant safely find end of refs with this info - quit!
            return None
        # Get line test patterns:
        t_patterns = PostRefSecnTitleListCompiler().getCompiledPatternList()
        kw_patterns = PostRefSecnKWListCompiler().getCompiledPatternList()
        if refStart.markerCharPresent():
            mk_patterns = CompiledPatternList([refStart.getMarkerPattern()])
        else:
            mk_patterns = RefLineNumerationListCompiler().getCompiledPatternList()
        garbageDigit_pattern = re.compile(unicode(r'^\s*?([\+\-]?\d+?(\.\d+)?\s*?)+?\s*?$'), re.UNICODE)
        searcher=LineSearcher()

        while (x<len(self._content)) and (not sectEnded):
            end_match = searcher.findWithinLine(self._content[x], t_patterns)
            if end_match is None:
                end_match = searcher.findWithinLine(self._content[x], kw_patterns)
            if end_match is not None:
                # End reference section? Check within next 5 lines for other reference numeration markers
                y = x + 1
                lineFnd = 0
                while (y < x + 6) and ( y < len(self._content)) and (not lineFnd):
                    num_match=searcher.findWithinLine(self._content[y], mk_patterns)
                    if num_match is not None and not num_match.group(0).isdigit():
                        lineFnd = 1
                    y = y + 1
                if not lineFnd:
                    # No ref line found-end section
                    sectEnded = 1
            if not sectEnded:
                # Does this & the next 5 lines simply contain numbers? If yes, it's probably the axis
                # scale of a graph in a fig. End refs section
                dm = garbageDigit_pattern.match(self._content[x])
                if dm is not None:
                    y = x + 1
                    digitLines = 4
                    numDigitLns = 1
                    while(y<x+digitLines) and (y<len(self._content)):
                        dm = garbageDigit_pattern.match(self._content[y])
                        if dm is not None:
                            numDigitLns = numDigitLns + 1
                        y = y + 1
                    if numDigitLns == digitLines:
                        sectEnded = 1
                x = x + 1
        return x - 1
    def extractReferences(self, no_rebuild=False):
        """Extract references from a TextDocument and return a ReferenceSection object"""
        # Try to remove pagebreaks, headers, footers
        self._removePageBoundaryInformation()
        # Find start of refs section:
        sectStart = self.findReferenceSection()
        if sectStart is None:
            # No references found
            sectStart = self.findReferenceSectionNoTitle()
        if sectStart is None:
            # No References
            refs = ReferenceSection()
        else:
            sectEnd = self.findEndReferenceSection(sectStart)
            if sectEnd is None:
                # No End to refs? Not safe to extract
                refs = ReferenceSection()
            else:
                # Extract
                refs = self.getReferences(sectStart, sectEnd)
        return refs
    def findReferenceSectionNoTitle(self):
        """Find the line number of the start of a TextDocument object's reference section by searching for the first reference
           line. Can only find reference sections with distinct line markers such as [1]. Returns a ReferenceSectionStartPoint
           object containing ref start line number & marker char, or the None type if nothing found
        """
        refStartLine = refLineMarker = refStart = None
        if len(self._content) > 0:
            mk_patterns = FirstRefLineNumerationListCompiler().getCompiledPatternList()
            searcher = LineSearcher()

            p_blank = re.compile(unicode(r'^\s*$'))
            x = len(self._content)-1
            foundSect = 0
            while x >= 0 and not foundSect:
                mk_match = searcher.findAtStartLine(self._content[x], mk_patterns)
                if mk_match is not None and string.atoi(mk_match.group('num')) == 1:
                    # Get mark recognition pattern:
                    mk_ptn = mk_match.re.pattern
               
                    # Look for [2] in next 10 lines:
                    nxtTestLines = 10
                    y = x + 1
                    tmpFnd = 0
                    while y < len(self._content) and y < x + nxtTestLines and not tmpFnd:
                        mk_match2 = searcher.findAtStartLine(self._content[y], mk_patterns)
                        if (mk_match2 is not None) and (string.atoi(mk_match2.group('num')) == 2) and (mk_match.group('left') == mk_match2.group('left')) and (mk_match.group('right') == mk_match2.group('right')):
                            # Found next line:
                            tmpFnd = 1
                        elif y == len(self._content) - 1:
                            tmpFnd = 1
                        y = y + 1

                    if tmpFnd:
                        foundSect = 1
                        refStartLine = x
                        refLineMarker = mk_match.group('mark')
                        refLineMarkerPattern = mk_ptn
                x = x - 1
        if refStartLine is not None:
            # Make ReferenceSectionStartPoint object with ref section start location details
            refStart = ReferenceSectionStartPoint()
            refStart.setLineNum(refStartLine)
            refStart.setMarkerChar(refLineMarker)
            refStart.setMarkerPattern(refLineMarkerPattern)
        return refStart
    def findReferenceSection(self):
        """Find the line number of the start of a TextDocument object's reference section.  Returns a 'ReferenceSectionStartPoint'
           object containing details of the reference section start line number, the reference section title & the marker char
           used for each reference line or returns None if not found
        """
        refStartLine = refTitle = refLineMarker = refLineMarkerPattern = None
        refStart = titleMarkerSameLine = foundPart = None
        if len(self._content) > 0:
            t_patterns = RefSecnTitleListCompiler().getCompiledPatternList()
            mk_patterns = RefLineNumerationListCompiler().getCompiledPatternList()
            searcher = LineSearcher()
            p_blank = re.compile(unicode(r'^\s*$'))
            # Try to find refs section title:
            x = len(self._content) - 1
            foundTitle = 0
            while x >= 0 and not foundTitle:
                title_match = searcher.findWithinLine(self._content[x], t_patterns)
                if title_match is not None:
                    temp_refStartLine = x
                    tempTitle = title_match.group('title')
                    mk_wtitle_ptrns = RefLineNumerationListCompiler().getCompiledPatternList(tempTitle)
                    mk_wtitle_match = searcher.findWithinLine(self._content[x], mk_wtitle_ptrns)
                    if mk_wtitle_match is not None:
                        mk = mk_wtitle_match.group('mark')
                        mk_ptn = mk_wtitle_match.re.pattern
                        p_num = re.compile(unicode(r'(\d+)'))
                        m_num = p_num.search(mk)
                        if m_num is not None and string.atoi(m_num.group(0)) == 1:
                            # Mark found.
                            foundTitle = 1
                            refTitle = tempTitle
                            refLineMarker = mk
                            refLineMarkerPattern = mk_ptn
                            refStartLine=temp_refStartLine
                            titleMarkerSameLine = 1
                        else:
                            foundPart = 1
                            refStartLine = temp_refStartLine
                            refLineMarker = mk
                            refLineMarkerPattern = mk_ptn
                            refTitle = tempTitle
                            titleMarkerSameLine = 1
                    else:
                        try:
                            y = x + 1
                            # Move past blank lines
                            m_blank = p_blank.match(self._content[y])
                            while m_blank is not None and y < len(self._content):
                                y = y + 1
                                m_blank = p_blank.match(self._content[y])
                            # Is this line numerated like a reference line?
                            mark_match = searcher.findAtStartLine(self._content[y], mk_patterns)
                            if mark_match is not None:
                                # Ref line found. What is it?
                                titleMarkerSameLine=None
                                mark = mark_match.group('mark')
                                mk_ptn = mark_match.re.pattern
                                p_num = re.compile(unicode(r'(\d+)'))
                                m_num = p_num.search(mark)
                                if m_num is not None and string.atoi(m_num.group(0)) == 1:
                                    # 1st ref truly found
                                    refStartLine = temp_refStartLine
                                    refLineMarker = mark
                                    refLineMarkerPattern = mk_ptn
                                    refTitle = tempTitle
                                    foundTitle = 1
                                elif m_num is not None and m_num.groups(0) != 1:
                                    foundPart = 1
                                    refStartLine = temp_refStartLine
                                    refLineMarker = mark
                                    refLineMarkerPattern = mk_ptn
                                    refTitle = tempTitle
                                else:
                                    if foundPart:
                                        foundTitle = 1
                                    else:
                                        foundPart = 1
                                        refStartLine = temp_refStartLine
                                        refTitle=tempTitle
                                        refLineMarker = mark
                                        refLineMarkerPattern = mk_ptn
                            else:
                                # No numeration
                                if foundPart:
                                    foundTitle = 1
                                else:
                                    foundPart = 1
                                    refStartLine = temp_refStartLine
                                    refTitle=tempTitle
                        except IndexError:
                            # References section title was on last line for some reason. Ignore
                            pass
                x = x - 1
        if refStartLine is not None:
            # Make ReferenceSectionStartPoint object with ref
            # section start location details
            refStart = ReferenceSectionStartPoint()
            refStart.setLineNum(refStartLine)
            refStart.setTitleString(refTitle)
            refStart.setMarkerChar(refLineMarker)
            refStart.setMarkerPattern(refLineMarkerPattern)
            if titleMarkerSameLine is not None:
                refStart.setTitleMarkerSameLine()
        return refStart
    def _removePageBoundaryInformation(self):
        """Locate page breaks, headers and footers within the doc body. remove them when found"""
        numHeadLn = numFootLn = 0
        pageBreaks = []
        # Make sure document not just full of whitespace:
        if not self.documentContainsText():
            return 0
        # Get list of index posns of pagebreaks in document:
        pageBreaks = self.getDocPageBreakPositions()
        # Get num lines making up each header if poss:
        numHeadLn = self.getHeadLines(pageBreaks)
        # Get num lines making up each footer if poss:
        numFootLn = self.getFootLines(pageBreaks)
        # Remove pagebreaks,headers,footers:
        self.chopHeadFootBreaks(pageBreaks, numHeadLn, numFootLn)
    def getheadFootWordPattern(self):
        """Regex pattern used to ID a word in a header/footer line"""
        return re.compile(unicode(r'([A-Za-z0-9-]+)'), re.UNICODE)
    def getHeadLines(self, breakIndices = []):
        """Using list of indices of pagebreaks in document, attempt to determine how many lines page headers consist of"""
        remainingBreaks = (len(breakIndices) - 1)
        numHeadLns = emptyLine = 0
        p_wordSearch = self.getheadFootWordPattern()
        if remainingBreaks > 2:
            if remainingBreaks > 3:
                # Only check odd page headers
                nxtHead = 2
            else:
                # Check headers on each page
                nxtHead = 1
            keepChecking = True
            while keepChecking:
                curBreak = 1
                #m_blankLineTest = p_wordSearch.search(self._content[(breakIndices[curBreak]+numHeadLns+1)])
                m_blankLineTest = re.compile(u'\S',re.UNICODE).search(self._content[(breakIndices[curBreak]+numHeadLns+1)])
                if m_blankLineTest == None:
                    # Empty line in header:
                    emptyLine = 1
                if (breakIndices[curBreak]+numHeadLns+1) == (breakIndices[(curBreak + 1)]):
                    # Have reached next pagebreak: document has no body - only head/footers!
                    keepChecking = False
                grps_headLineWords = p_wordSearch.findall(self._content[(breakIndices[curBreak]+numHeadLns+1)])
                curBreak = curBreak + nxtHead
                while (curBreak < remainingBreaks) and keepChecking:
                    grps_thisLineWords = p_wordSearch.findall(self._content[(breakIndices[curBreak]+numHeadLns+1)])
                    if emptyLine:
                        if len(grps_thisLineWords) != 0:
                            # This line should be empty, but isnt
                            keepChecking = False
                    else:
                        if (len(grps_thisLineWords) == 0) or (len(grps_headLineWords) != len(grps_thisLineWords)):
                            # Not same num 'words' as equivilent line in 1st header:
                            keepChecking = False
                        else:
                            keepChecking = self.checkBoundaryLinesSimilar(grps_headLineWords, grps_thisLineWords)
                    # Update curBreak for nxt line to check
                    curBreak = curBreak + nxtHead
                if keepChecking:
                    # Line is a header line: check next
                    numHeadLns = numHeadLns+1
                emptyLine = 0
        return numHeadLns
    def getFootLines(self, breakIndices = []):
        """Using list of indices of pagebreaks in document, attempt to determine how many lines page footers consist of"""
        numBreaks = (len(breakIndices))
        numFootLns = 0
        emptyLine = 0
        keepChecking = 1
        p_wordSearch = self.getheadFootWordPattern()
        if numBreaks > 2:
            while keepChecking:
                curBreak = 1
                #m_blankLineTest = p_wordSearch.match(self._content[(breakIndices[curBreak]-numFootLns-1)])
                m_blankLineTest = re.compile(u'\S',re.UNICODE).search(self._content[(breakIndices[curBreak] - numFootLns - 1)])
                if m_blankLineTest == None:
                    emptyLine = 1
                grps_headLineWords = p_wordSearch.findall(self._content[(breakIndices[curBreak]-numFootLns-1)])
                curBreak=curBreak + 1
                while (curBreak < numBreaks) and keepChecking:
                    grps_thisLineWords = p_wordSearch.findall(self._content[(breakIndices[curBreak] - numFootLns - 1)])
                    if emptyLine:
                        if len(grps_thisLineWords) != 0:
                            keepChecking = 0
                    else:
                        if (len(grps_thisLineWords) == 0) or (len(grps_headLineWords) != len(grps_thisLineWords)):
                            keepChecking = 0
                        else:
                            keepChecking = self.checkBoundaryLinesSimilar(grps_headLineWords, grps_thisLineWords)
                    curBreak = curBreak + 1
                if keepChecking:
                    numFootLns = numFootLns + 1
                emptyLine = 0
        return numFootLns
    def chopHeadFootBreaks(self, breakIndices=None, headLn=0, footLn=0):
        """Remove document lines containing breaks, headers, footers"""
        if type(breakIndices) not in (tuple, list):
            breakIndices = []
        numBreaks = len(breakIndices)
        pageLens = []
        for x in range(0,numBreaks):
            if x < numBreaks - 1:
                pageLens.append(breakIndices[x + 1] - breakIndices[x])
        pageLens.sort()
        if (len(pageLens) > 0) and (headLn + footLn + 1 < pageLens[0]):
            # Safe to chop hdrs & ftrs
            breakIndices.reverse()
            first = 1
            for i in range(0, len(breakIndices)):
                # Unless this is the last page break, chop headers
                if not first:
                    for j in range(1, headLn + 1):
                        self._content[breakIndices[i]+1:breakIndices[i]+2] = []
                else:
                    first = 0
                # Chop page break itself
                self._content[breakIndices[i]:breakIndices[i] + 1] = []
                # Chop footers (unless this is the first page break)
                if i != len(breakIndices) - 1:
                    for k in range(1, footLn + 1):
                        self._content[breakIndices[i] - footLn:breakIndices[i] - footLn + 1] = []
    def checkBoundaryLinesSimilar(self, l_1, l_2):
        """Compare two lists to see if their elements are roughly the same"""
        numMatches = 0
        if (type(l_1) != list) or (type(l_2) != list) or (len(l_1) != len(l_2)):
            return False
        p_int = re.compile(unicode(r'^(\d+)$'))
        for i in range(0,len(l_1)):
            m_int1 = p_int.match(l_1[i])
            m_int2 = p_int.match(l_2[i])
            if(m_int1 != None) and (m_int2 != None):
                numMatches=numMatches+1
            else:
                l1_str = l_1[i].lower()
                l2_str = l_2[i].lower()
                if (l1_str[0] == l2_str[0]) and (l1_str[len(l1_str) - 1] == l2_str[len(l2_str) - 1]):
                    numMatches=numMatches+1
        if (len(l_1) == 0) or (float(numMatches)/float(len(l_1)) < 0.9):
            return False
        else:
            return True
    def getDocPageBreakPositions(self):
        """Locate page breaks in the list of document lines and make a list of their indices to be returned"""
        pageBreaks = []
        p_break = re.compile(unicode(r'^\s*?\f\s*?$'), re.UNICODE)
        for i in range(len(self._content)):
            if p_break.match(self._content[i]) != None:
                pageBreaks.append(i)
        return pageBreaks
    def documentContainsText(self):
        """Test whether document contains text, or is just full of worthless whitespace. Return 1 if has text, 0 if not"""
        foundWord = False
        p_word = re.compile(unicode(r'\S+'))
        for i in self._content:
            if p_word.match(i) != None:
                foundWord = True
                break
        return foundWord

class Ps2asciiEncodedTextDocument(Document):
    """Text document that is encoded with PS coordinate information. This type of document is result of a ps2ascii conversion"""
    class Ps2asciiOutputLine:
        """Represents a line from a ps2ascii conversion"""
        def __init__(self, posx, posy, content, diffx):
            """Initialise a dataline's state"""
            self._posnX = self._posnY = 0
            self._dataContent = ''
            self._diff_posnX = 0
            self.setPosX(int(posx))
            self.setPosY(int(posy))
            self.setText(content)
            self.setDiffPosX(int(diffx))
        def setPosX(self, x):
            """Set posnX value for a Ps2asciiOutputLine object"""
            self._posnX = x
        def setPosY(self, y):
            """Set posnY value for a Ps2asciiOutputLine object"""
            self._posnY = y
        def setText(self, data):
            """Set dataContent value for Ps2asciiOutputLine object"""
            self._dataContent = data
        def setDiffPosX(self, dpx):
            """Set diff_posnX value for a Ps2asciiOutputLine object"""
            self._diff_posnX = dpx
        def getPosX(self):
            """Return the posnX value for a Ps2asciiOutputLine object"""
            return self._posnX
        def getPosY(self):
            """Return the posnY value for a Ps2asciiOutputLine object"""
            return self._posnY
        def getText(self):
            """Return a cleaned up version of the dataContent in this Ps2asciiOutputLine object"""
            return self._dataContent
        def getDiffPosX(self):
            """Return the diff_posnX value for a Ps2asciiOutputLine object"""
            return self._diff_posnX
        def isNewLine(self, previousLine):
            """Check the positional coordinates of this line with those of the supplied Ps2asciiOutputLine object to
               determine whether this is a new line. Return 1 if yes, or 0 if no
            """
            if (self.getPosX() <= previousLine.getPosX()) and (self.getPosY() != previousLine.getPosY()):
                return 1
            else:
                return 0
        def isSpaceSeparated(self, posnxEst):
            """Return 1 if the text in this Ps2asciiOutputLine object should be separated from that in a
               previous Ps2asciiOutputLine object, as determined by an X position estimate (posnxEst). Return 0 if not
            """
            if (self.getPosX() > (posnxEst + 7)):
                return 1
            else:
                return 0
    def __init__(self,  newDocBody = []):
        Document.__init__(self, newDocBody)
    def convertToPlainText(self):
        """Tell a Ps2asciiEncodedTextDocument to convert itself to convert itself to pure plaintext. Returns TextDocument object"""
        # Converted document:
        plaintextContent = []
        tempLine = ''
        # Fictitious old line to compare with 1st line:
        oldRawLine = self.Ps2asciiOutputLine(9999, 9999, "", 0)
        posnxEst = 9999
        for line in self._content:
            curRawLine = self.getDataLine(line)
            if curRawLine != None:
                # Find out if this a new line or a continuation of the last line
                if curRawLine.isNewLine(oldRawLine):
                    # Append previous full line:
                    plaintextContent.append(self.prepareLineForAppending(tempLine))
                    # Start a new line buffer:
                    tempLine = curRawLine.getText()
                else:
                    # Not new line: concat with last line
                    if curRawLine.isSpaceSeparated(posnxEst):
                        tempLine = tempLine + ' ' + curRawLine.getText()
                    else:
                        tempLine = tempLine + curRawLine.getText()
                posnxEst = (curRawLine.getPosX() + curRawLine.getDiffPosX())
                oldRawLine = curRawLine
        # Append very last line to list:
        plaintextContent.append(self.prepareLineForAppending(tempLine))
        # Remove first, empty cell from list:
        plaintextContent[0:1] = []
        # Make a TextDocument with the newly converted text content and return it:
        return TextDocument(plaintextContent)
    def getDataLine(self, rawLine):
        """Take a raw line from ps2ascii, and put its components into a Ps2asciiOutputLine object"""
        idPattern = re.compile(r'^S\s(?P<posnX>\d+)\s(?P<posnY>\d+)\s\((?P<content>.*)\)\s(?P<diff_posnX>\d+)$')
        match = idPattern.search(rawLine)
        if match != None:
            return self.Ps2asciiOutputLine(match.group('posnX'), match.group('posnY'), match.group('content'), match.group('diff_posnX'))
        else:
            return None
    def prepareLineForAppending(self, line):
        """Prepare the contents of a plaintext line which has been rebuilt from Ps2asciiOutputLine(s) to be appended to the
           list of plaintext lines which make up the plaintext document Test its contents: if all whitespace, but not formfeed,
           return an empty line; if contains non-whitespace or a formfeed, return the line as is
        """
        # Clean line to append of control codes:
        line = self.cleanLine(line)
        ep = re.compile('\S')
        em = ep.match(line)
        if em == None:
            fp = re.compile('^ *\f *$')
            fm = fp.match(line)
            if fm == None:
                line = ''
        return line
    def cleanLine(self, line):
        """Clean a line of text of the messy character codes that ps2ascii adds during conversion"""
        # Correct escaped parentheses
        p = re.compile(r'\\\(')
        line = p.sub('(', line)
        p = re.compile(r'\\\)')
        line = p.sub(r')', line)
        # Correct special symbols
        p = re.compile(r'\\\\')
        line = p.sub('', line)
        p = re.compile('\n')
        line = p.sub(r' ', line)
        # Change '\013' to 'ff' (ps2ascii messes this up)
        p = re.compile(r'\\013')
        line = p.sub('ff', line)
        # Change '\017' (bullet point) into '*'
        p = re.compile(r'\\017')
        line = p.sub('*', line)
        # Change '\003' into '*'
        p = re.compile(r'\\003')
        line = p.sub('', line)
        # Change '\\f' to 'fi' (ps2ascii messes this up)
        p = re.compile(r'\\f')
        line = p.sub('fi', line)
        # Remove page numbers:
        p = re.compile('\{\s\d+\s\{')
        line = p.sub(r'', line)
        # Correct Hyphens:
        p = re.compile('\{')
        line = p.sub('-', line)
        return line
    def displayDocument(self):
        """Let Ps2asciiEncodedTextDocument display itself on standard output stream"""
        for i in self._content:
            print i

class ReferenceSectionStartPoint:
    """Concrete class to hold information about the start line of a document's reference section (e.g. line number, title, etc)"""
    def __init__(self):
        self._lineNum = self._title = self._lineMarkerPresent = None
        self._haveMarkerRegex = self._markerChar = self._markerRegexPattern = self._markerTitleSameLine=None
    def setLineNum(self, num):
        """Set the line number of the references section start"""
        self._lineNum = num
    def setTitleString(self, t):
        """Set the title string for the references section start"""
        self._title = t
    def setMarkerChar(self, m):
        """Set the marker char for the references section start"""
        if m is not None and (type(m) is str or type(m) is unicode):
            self._markerChar = m
            self._lineMarkerPresent = 1
        else:
            self._markerChar = None
            self._lineMarkerPresent = 0
    def setMarkerPattern(self, p):
        """Set the regex pattern for the start of the first reference line"""
        if p is not None and (type(p) is str or type(p) is unicode):
            self._markerRegexPattern = p
            self._haveMarkerRegex = 1
        else:
            self._markerRegexPattern = None
            self._haveMarkerRegex = 0
    def setTitleMarkerSameLine(self):
        """Set a flag to say that the first reference line contains both a title and the first line"""
        self._markerTitleSameLine = 1
    def getLineNum(self):
        """Return the line number of the references section start"""
        return self._lineNum
    def getTitleString(self):
        """Return the title string for the references section start if there is one, else it will be None"""
        return self._title
    def firstLineIsTitleAndMarker(self):
        """Return 1 if the first reference line contains both reference section title & first line numeration marker"""
        if self._markerTitleSameLine is not None:
            return True
        else:
            return False
    def titlePresent(self):
        """Return 1 if there is a title present in the first reference line, 0 if not"""
        if self._title is not None:
            return True
        else:
            return False
    def markerCharPresent(self):
        """Return 1 if there is a marker char, 0 if not"""
        if self._lineMarkerPresent:
            return True
        else:
            return False
    def markerPatternPresent(self):
        """Return 1 if there is a marker regex pattern, 0 if not"""
        if self._haveMarkerRegex:
            return True
        else:
            return False
    def getMarkerChar(self):
        """Return the marker char for the reference section start if there is one, else it will be None"""
        return self._markerChar
    def getMarkerPattern(self):
        return self._markerRegexPattern

class ReferenceSectionRebuilder:
    """Concrete class whose job is to rebuild broken reference lines. Contains a list of Strings. Each String in this list
       represents the contents of either a complete reference line or part of a reference line. When a document is converted from
       its original format to plaintext, lines are often broken because the converter cant distinguish between wrapped lines and
       new lines. Objects of this class can be used to try to rebuild broken reference lines and create a 'ReferenceSection' object
    """
    def __init__(self, lines = []):
        """Initialise a ReferenceSectionRebuilder object with a list of 'broken' reference lines"""
        if type(lines) is list:
            self._dataLines = lines
        elif type(lines) is str or type(lines) is unicode:
            self._dataLines.append(lines)
        else:
            self._dataLines = []
    def getRebuiltLines(self, refStartInfo):
        """Trigger reference lines rebuilding process & return ReferenceSection object containing rebuilt ReferenceLine objects"""
        # Ensure we have a real 'ReferenceSectionStartPoint'
        try: getLineNum = refStartInfo.getLineNum
        except AttributeError: return ReferenceSection()
        self._removeLeadingGarbageLines()
        numatnInfo = self._getLineNumerationStyle(refStartInfo)
        return ReferenceSection(self._rebuild(numatnInfo))
    def _testBlankLineRefSeparators(self):
        """Test to see if reference lines are separated by blank lines so that these can be used to rebuild reference lines"""
        p_ws = re.compile(unicode(r'^\s*$'),re.UNICODE)
        numblank = 0            # No blank lines fnd between non-blanks
        numline = 0             # No ref lines separated by blanks
        blankLnSep = 0          # Flag to indicate if blanks lines separate ref lines
        multi_nonblanks_fd = 0  # Flag to indicate if multiple nonblank lines are found together (used because
                                # if line is dbl-spaced, it isnt a blank that separates refs & cant be relied upon)
        x = 0
        max = len(self._dataLines)
        while x < max:
            m_ws = p_ws.search(self._dataLines[x])
            if m_ws is None:
                # ! empty line
                numline = numline+1
                x = x + 1 # Move past line
                while x < len(self._dataLines) and p_ws.search(self._dataLines[x]) is None:
                    multi_nonblanks_fd=1
                    x = x + 1
                x = x - 1
            else:
                # empty line
                numblank = numblank + 1
                x = x + 1
                while x< len(self._dataLines) and p_ws.search(self._dataLines[x]) is not None:
                    x = x + 1
                if x == len(self._dataLines):
                    # Blanks at end doc: dont count
                    numblank = numblank-1
                x = x - 1
            x = x + 1
        # Now from data of num blank lines & num text lines, if numline>3, & numblank=numline or numblank=numline-1
        # then we hav blank line separators between ref lines
        if (numline > 3) and ((numblank == numline) or (numblank == numline - 1)) and (multi_nonblanks_fd):
            blankLnSep = 1
        return blankLnSep
    def _rebuild(self, refNum):
        """Based on whether a reference line numeration pattern was found, either have the reference lines rebuild by the
           identification of marker characters, or join all lines together if no numeration was found
        """
        # Private internal function
        def cleanAndAppendToRefsList(transformers, refList, line):
            """Before appending to list, process line with 'TextLineTransformers'"""
            for x in transformers:
                line = x.processLine(line)
            sp = re.compile(unicode(r'^\s*$'),re.UNICODE)
            if sp.match(line) is None:
                refList.append(line)
        rebuilt = []
        lineTrans = []
        tl = u''
        # List of line transformers to clean up line:
        lineTrans.append(URLRepairer())
        lineTrans.append(EscapeSequenceTransformer())
        lineTrans.append(MultispaceTruncator())
        if refNum is None or (type(refNum) is not str and type(refNum) is not unicode):
            if self._testBlankLineRefSeparators():
                # Use blank lines to separate ref lines
                refNum = unicode(r'^\s*$')
            else:
                # No ref line dividers: unmatchable pattern
                refNum = unicode(r'^A$^A$$')
        p_refNum = re.compile(refNum,re.I|re.UNICODE)
        p_leadingws = re.compile(unicode(r'^\s+'))
        p_trailingws = re.compile(unicode(r'\s+$'))
        for x in range(len(self._dataLines)-1,-1,-1):
            tstr = p_leadingws.sub(u'',self._dataLines[x])
            tstr = p_trailingws.sub(u'',tstr)
            m = p_refNum.match(tstr)
            if m is not None:
                # Ref line start marker
                if tstr == '':
                    # Blank line to separate refs
                    tl = p_trailingws.sub(u'',tl)
                    cleanAndAppendToRefsList(lineTrans, rebuilt, tl)
                    tl = u''
                else:
                    if tstr[len(tstr)-1] == u'-' or tstr[len(tstr)-1] == u' ':
                        tl = tstr + tl
                    else:
                        tl = tstr + u' ' + tl
                    tl = p_trailingws.sub(u'',tl)
                    cleanAndAppendToRefsList(lineTrans, rebuilt, tl)
                    tl = u''
            else:
                if tstr != u'':
                    # Continuation of line
                    if tstr[len(tstr) - 1] == u'-' or tstr[len(tstr) - 1] == u' ':
                        tl = tstr + tl
                    else:
                        tl = tstr + u' ' + tl
        if tl != u'':
            # Append last line
            tl = p_trailingws.sub(u'',tl)
            cleanAndAppendToRefsList(lineTrans, rebuilt, tl)
        rebuilt.reverse()
        d=self._testAndCorrectRebuiltLines(rebuilt, p_refNum)
        if d is not None: rebuilt = d
        return rebuilt
    def _testAndCorrectRebuiltLines(self, rebuiltlines, p_refmarker):
        """EXPERIMENTAL METHOD. Try to correct any rebuild reference lines that have been given a bad reference number at the start. Needs testing."""
        fixed = []
        unsafe = False
        try:
            m = p_refmarker.match(rebuiltlines[0])
            last_marknum = int(m.group("marknum"))
            if last_marknum != 1:
                return None                        # Even the first mark isnt 1 - probaby too dangerous to try to repair
        except IndexError:
            return None                            # Either no references or not a "numbered line marker" - cannot do anything
        except AttributeError:
            return None                            # No reference line marker (i.e. NoneType because couldn't match marker) - cannot do anything
        fixed.append(rebuiltlines[0])
        try:
            for x in range(1,len(rebuiltlines)):
                m = p_refmarker.match(rebuiltlines[x])
                try:
                    if int(m.group("marknum")) == last_marknum + 1:
                        # All is well
                        fixed.append(rebuiltlines[x])
                        last_marknum += 1
                        continue
                    elif len(string.strip(rebuiltlines[x][m.end():])) == 0:
                        # this line consists of a number only. And it is not a coorrect marker. Add it to the last line:
                        fixed[len(fixed) - 1] += rebuiltlines[x]
                        continue
                    else:
                        # Problem maybe. May have taken some of the last line into this line. Can we find the next marker in this line?
                        m_fix = p_refmarker.search(rebuiltlines[x])
                        if m_fix is not None and int(m_fix.group("marknum")) == last_marknum + 1:
                            m_fix_test = re.match(u"%s\s*[A-Z]"%(m_fix.group(),))
                            if m_fix_test is not None:
                                movesect = rebuiltlines[x][0:m_fix.start()]
                                rebuiltlines[x] = rebuiltlines[x][m_fix.start():]
                                fixed[len(fixed) - 1] += movesect
                                fixed.append(rebuiltlines[x])
                            else:
                                unsafe = True
                                break
                        else:
                            unsafe = True
                            break
                except AttributeError:
                    # This line does not have a line marker at the start! This line shall be added to the end of the previous line.
                    fixed[len(fixed) - 1] += rebuiltlines[x]
                    continue
        except IndexError:
            unsafe = True
        if unsafe: return None
        else: return fixed
    def _getLineNumerationStyle(self, refStartInfo):
        """Try to determine the numeration marker style for the reference lines"""
        mkregex = None
        if refStartInfo.markerPatternPresent():
            mkregex = refStartInfo.getMarkerPattern()
        return mkregex
    def _removeLeadingGarbageLines(self):
        """Sometimes, the first lines of the extracted references are completely blank or email addresses. These must be removed as they are not references"""
        p_emptyline = re.compile(unicode(r'^\s*$'),re.UNICODE)
        p_email = re.compile(unicode(r'^\s*e\-?mail'),re.UNICODE)
        while (len(self._dataLines)>0) and (p_emptyline.match(self._dataLines[0]) is not None or p_email.match(self._dataLines[0]) is not None):
            self._dataLines[0:1] = []

class DocumentConverter:
    """Abstract Class representing a document format conversion
       tool which converts a document from one format to another
    """
    def convertDocument(self, toConvert):
        """Document Conversion Method - returns a Document object"""
        pass
    def checkConvertFile(self, filePath):
        """Check that the file to convert is usable"""
        pass

class OSDependentDocumentConverter(DocumentConverter):
    """ABSTRACT CLASS: Represents a document conversion tool which is a
       separate program which needs to be executed via a call to the shell below
    """
    def __init__(self):
        self._converterSessionLink = self._convertCommand = ''
    def setConvertCommand(self, filePath):
        """ABSTRACT METHOD: Set the shell command used for calling the
           converter application. Declared abstract because it differs
           according to which specific application is used
        """
        pass
    def getConvertCommand(self):
        """Return the shell command by which the conversion application is called"""
        return self._convertCommand
    def openConverterSession(self):
        """Open a session with the shell 'converter' application"""
        if self._converterSessionLink is file:
            self._converterSessionLink.close()
            self._converterSessionLink = ""
        self._converterSessionLink =  os.popen(self.getConvertCommand(),'r')
    def closeConverterSession(self):
        """Close session with the shell 'converter' application"""
        if self._converterSessionLink is file:
            self._converterSessionLink.close()
        self._converterSessionLink = ""
    def getConversionResult(self):
        """Return list of lines from shell conversion session"""
        return self._converterSessionLink.readlines()

class PDFtoTextDocumentConverter(OSDependentDocumentConverter):
    """Converts PDF documents to ASCII plaintext documents"""
    def __init__(self):
        """Initialise PDFtoTextDocumentConverter object"""
        OSDependentDocumentConverter.__init__(self)
        self._applicationPath = ''
        self.setApplicationPath(cfg_refextract_pdftotext)
    def setApplicationPath(self, newPath):
        """Set path to conversion application"""
        self._applicationPath = newPath
    def getApplicationPath(self):
        """Return the path to the conversion application"""
        return self._applicationPath
    def setConvertCommand(self, filePath):
        """Set up the command by which to call pdftotext application"""
        self._convertCommand = self.getApplicationPath() + ' -raw -q -enc UTF-8 ' + filePath + ' -'
    def getConversionResult(self):
        mylines = []
        for line in self._converterSessionLink: mylines.append(line.decode("utf-8"))
        return mylines
    def convertDocument(self, toConvert):
        """Perform a conversion from PDF to text, returning the document contents as a TextDocument object"""
        if self._canAccessConvertFile(toConvert):
            self.setConvertCommand(toConvert)
            self.openConverterSession()
            convRes = self.getConversionResult()
            self.closeConverterSession()
            if self._conversionIsBad(convRes):
                # Bad conversion: empty document
                textDoc = TextDocument()
            else:
                # Good conversion
                textDoc = TextDocument(convRes)
        else:
            textDoc = TextDocument()
        return textDoc
    def _conversionIsBad(self, convertedLines):
        """Sometimes pdftotext performs a bad conversion which consists of many spaces and garbage characters.
           This method takes a list of strings obtained from a pdftotext conversion and examines them to see if
           they are likely to be the result of a bad conversion. Returns 1 if bad conversion, 0 if not
        """
        # Numbers of 'words' and 'whitespaces' found in document:
        numWords = numSpaces = 0
        # whitespace line pattern:
        ws_patt = re.compile(unicode(r'^\s+$'), re.UNICODE)
        # whitespace character pattern:
        p_space = re.compile(unicode(r'(\s)'), re.UNICODE)
        # non-whitespace 'word' pattern:
        p_noSpace = re.compile(unicode(r'(\S+)'), re.UNICODE)
        for line in convertedLines:
            numWords = numWords + len(p_noSpace.findall(line))
            numSpaces = numSpaces + len(p_space.findall(line))
        if numSpaces >= (numWords * 3):
            # Too many spaces - probably bad conversion
            return True
        else:
            return False
    def _canAccessConvertFile(self, filePath):
        """Check that the path to the file to convert really exists and is readable by the shell"""
        if os.access(filePath, os.R_OK): return True
        else: return False

class PS2AsciiDocumentConverter(OSDependentDocumentConverter):
    """Converts PS documents to ASCII plaintext documents"""
    def __init__(self):
        """Initialise PS2AsciiDocumentConverter object"""
        OSDependentDocumentConverter.__init__(self)
        self._catAppPath = self._gunzipAppPath = self._gsAppPath = ''
        self.setCATapplicationPath(cfg_refextract_cat)
        self.setGUNZIPapplicationPath(cfg_refextract_gunzip)
        self.setGSapplicationPath(cfg_refextract_gs)
    def setCATapplicationPath(self, catAppPath):
        """Set the path to the 'cat' application, used in conversion"""
        self._catAppPath = catAppPath
    def setGUNZIPapplicationPath(self, gunzipAppPath):
        """Set the path to the 'gunzip' application, used in conversion if the PS file has been zipped"""
        self._gunzipAppPath = gunzipAppPath
    def setGSapplicationPath(self, gsAppPath):
        """Set the path to the 'GhostScript' application, which is the means of calling 'ps2ascii'"""
        self._gsAppPath = gsAppPath
    def getCATapplicationPath(self):
        """Return the path to 'cat' as a string"""
        return self._catAppPath
    def getGUNZIPapplicationPath(self):
        """Return the path to 'gunzip' as a string"""
        return self._gunzipAppPath
    def getGSapplicationPath(self):
        """Return the path to 'gs' as a string"""
        return self._gsAppPath
    def setUnzippedPSConvertCommand(self, filePath):
        """Set converter command for unzipped PS file conversion"""
        self._convertCommand = self.getCATapplicationPath() + " " + filePath + " | " + self.getGSapplicationPath() + " -q -dNODISPLAY -dNOBIND -dWRITESYSTEMDICT -c save -f ps2ascii.ps - -c quit"
    def setZippedPSConvertCommand(self, filePath):
        """Set converter command for zipped PS file conversion"""
        self._convertCommand = self.getGUNZIPapplicationPath() + " -c " + filePath + " | " + self.getGSapplicationPath() + " -q -dNODISPLAY -dNOBIND -dWRITESYSTEMDICT -c save -f ps2ascii.ps - -c quit"
    def setConvertCommand(self, filePath):
        """Set up the shell command by which to call applications needed to perform the conversion"""
        if re.search(r'(\w{2})$', filePath).group(0) == "ps":
            self.setUnzippedPSConvertCommand(filePath)
        else:
            self.setZippedPSConvertCommand(filePath)
    def _canAccessConvertFile(self, filePath):
        """Check that the path to the file to convert really exists and is readable by the shell"""
        if os.access(filePath, os.R_OK): return True
        else: return False
    def _correctConvertFileName(self, filename):
        """Strip file extension from filename & replace with '.ps' or '.ps.gz' depending on which exists. If neither exist,
           replace with no extension
        """
        regexPattern = re.compile(r'(?P<fname>.*?)(\.\w+)?$')
        match = regexPattern.search(filename)
        name = match.group('fname')
        if self._canAccessConvertFile(name+'.ps'): name = name + '.ps'
        else: name = name + '.ps.gz'
        return name
    def convertDocument(self, toConvert):
        """This method performs a conversion from PS to text. If the file 'toConvert' exists and can be converted, a
           TextDocument object is returned.  If not, then an empty TextDocument is returned"""
        toConvert = self._correctConvertFileName(toConvert)
        if self._canAccessConvertFile(toConvert):
            self.setConvertCommand(toConvert)
            self.openConverterSession()
            ps2asciiDoc = Ps2asciiEncodedTextDocument(self.getConversionResult())
            # Convert the ps2asciiDoc to plaintext:
            textDoc = ps2asciiDoc.convertToPlainText()
            self.closeConverterSession()
        else:
            textDoc = TextDocument()
        return textDoc

class BadKBLineError(Exception):
    """Exception thrown if a line in the periodicals knowledge base does not comply with the expected format"""
    pass

class KnowledgeBase:
    """The knowledge base of periodical titles. Consists of search & replace terms. The search terms consist of non-standard periodical titles in upper case.
       These are often found in the text of documents. Replacement terms consist of standardised periodical titles in a standardised case. These will be used to
       replace identified non-standard titles
    """
    def __init__(self, fn = None):
        self._kb = {}
        self._compiledPatternsKB = {}
        self._unstandardisedTitle = {}
        if type(fn) is str: self._buildKB(fn)
    def _buildKB(self, fn):
        """From the filename provided (fn), read the periodicals knowledge base into memory, and build a dictionary of seek/replace values to be stored in self._kb"""
        def _mychop(line):
            if line[:-1] == u'\n':
                line = line[:-1]
            return line
        try:
            fh=open(fn, 'r')
            p_kbLine = re.compile(unicode('^\s*(?P<seek>\w.*?)\s*---\s*(?P<repl>\w.*?)\s*$'),re.UNICODE)
            for x in fh:
                y = x.decode("utf-8")
                y = _mychop(y)
                m_kbLine = p_kbLine.search(y)
                if m_kbLine is None:
                    raise BadKBLineError()
                if len(m_kbLine.group('seek')) > 1:
                    # Only add KB line if the search term is more than 1 char in length
                    self._kb[m_kbLine.group('seek')] = m_kbLine.group('repl')
                    tmp_ptn = re.compile(unicode(r'\b(') + re.escape(m_kbLine.group('seek')) + unicode(r')[^A-Z0-9]'), re.UNICODE)
                    self._compiledPatternsKB[tmp_ptn] = m_kbLine.group('repl')
                    self._unstandardisedTitle[tmp_ptn] = m_kbLine.group('seek')
            fh.close()
        except IOError:
            sys.exit('E: Cannot Open Knowledge Base File "%s".' % fn)
        except (BadKBLineError, AttributeError):
            sys.exit('E: Unexpected Line in Knowledge Base "%s".' % fn)
    def display(self):
        """Display the contents of the KB on the standard output stream"""
        print u"Knowledge Base Contents:"
        for x in self._kb.keys():
            sys.stdout.write("Search Term: '%s';\t\tReplace Term: '%s'\n" % (x.encode("utf-8"), (self._kb[x]).encode("utf-8")))
    def findPeriodicalTitles(self, ln):
        """Identify periodical titles in text line 'ln' and record information about where in the line they occur. Replace them for lower-case versions or
           lowercase letter 'a's if the match was numerical. Return a Tuple containing dictionaries containing information about the substitutions, along with the new line
        """
        def _bytitlelen(a, b):
            (aa,bb) = (self._unstandardisedTitle[a],self._unstandardisedTitle[b])
            if len(aa) < len(bb): return 1
            elif len(aa) == len(bb): return 0
            else: return -1
        def _byLen(a, b):
            (aa,bb) = (a.pattern,b.pattern)
            if len(aa) < len(bb): return 1
            elif len(aa) == len(bb): return 0
            else: return -1
        foundMatch = False
        title_match_len = {}
        title_match_txt = {}
        kb_keys = self._compiledPatternsKB.keys()
        kb_keys.sort(_bytitlelen)
        word_ptn = re.compile(unicode(r'^[ A-Z-a-z]+$'),re.UNICODE)
        for t_ptn in kb_keys:
            matches_iter = t_ptn.finditer(ln)
            # Record dets of each match:
            for m in matches_iter:
                # Record match info
                title_match_len[m.start()] = (len(m.group(0)) - 1)
                title_match_txt[m.start()] = self._unstandardisedTitle[t_ptn]
                # Replace matched txt in line with lowercase version (or n*'_' where n is len of match)
                rep_str = m.group(1)
                word_mtch = word_ptn.search(rep_str)
                if word_mtch is None:
                    # None alpha/whitespace chars
                    rep_str = u'_'*len(rep_str)
                else:
                    # Words
                    rep_str = rep_str.lower()
                ln = u''.join([ln[0:m.start(1)],rep_str,ln[m.end(1):]])
        if len(title_match_len) > 0: foundMatch = True
        return (title_match_len, title_match_txt, ln, foundMatch)
    def __getitem__(self, non_std_title):
        """Return the standardised title thought to be keyed by 'non_std_title'. Return None if not there"""
        try: return self._kb[non_std_title]
        except KeyError: return None

class PreprintClassificationItem:
    def __init__(self, srch='', repl=''):
        self._srchStr, self._rpStr = srch, repl
    def setSearchString(self, sstr): self._srchStr = sstr
    def setReplString(self, repstr): self._rpStr = repstr
    def getSearchString(self): return self._srchStr
    def getReplString(self): return self._rpStr
    def getLength(self): return len(self._srchStr)
    r_str = property(fget = getReplString, fset = setReplString)
    s_str = property(fget = getSearchString, fset = setSearchString)
    length = property(fget = getLength)
    del setSearchString, setReplString, getSearchString, getReplString
    del getLength

class Institute:
    def __init__(self, nm):
        self._name = nm
        self._preprintCatsList = []
        self._numerationList = []
        self._numerationRegex = ""
        self._preprintCatPatternsList = {}
    def setName(self, nm): self._name = nm
    def getName(self): return self._name
    def display(self):
        print u"----------------------"
        print u"Name: " + self._name.encode("utf-8")
        print u"Preprint Categories:"
        for x in self._preprintCatsList: print u"Search:", x.s_str.encode("utf-8"), u"Replace With:", x.r_str.encode("utf-8")
        print u"Numeration Styles List:"
        for x in self._numerationList: print x
        print u"Numeration Styles Regular expression List:"
        print self._numerationRegex
        print u"----------------------"
    def _getPatternLenList(self):
        """Make a copy of the list of numeration patterns for an Institute object. Return this new list"""
        nl = []
        ccp = re.compile(unicode(r'\[[^\]]+\]'),re.UNICODE)
        for x in self._numerationList:
            # Remove the character class & append to newList
            nx = ccp.sub(u'1', x)
            nl.append((len(nx),x))
        return nl
    def _createPattern(self, ptn):
        """Accept a user-defined search pattern, transform it, according to some simple rules, into a regex pattern, then compile and return it as a compiled RE object
           \     -> \\
           9     -> \d
           a     -> [A-Za-z]
           mm    -> (0[1-9]|1[0-2])
           yy    -> \d{2}
           yyyy  -> [12]\d{3}
           /     -> \/
           ## Added 14/08/2006:
           s     -> \s*?
        """
        # Make the search/replace patterns:
        s_r = []
        s_r.append((re.compile(unicode(r'([^\]A-Za-z0-9\/\[ "])'), re.UNICODE), unicode(r'\\\g<1>')))
        s_r.append((re.compile(u'9', re.UNICODE), unicode(r'\d')))
        s_r.append((re.compile(u'a', re.UNICODE), unicode(r'[A-Za-z]')))
        s_r.append((re.compile(u'mm', re.UNICODE), unicode(r'(0[1-9]|1[0-2])')))
        s_r.append((re.compile(u'yyyy', re.UNICODE), unicode(r'[12]\d\d\d')))
        s_r.append((re.compile(u'yy', re.UNICODE), unicode(r'\d\d')))
        s_r.append((re.compile(u's', re.UNICODE), unicode(r'\s*?')))
        s_r.append((re.compile(unicode(r'\/'), re.UNICODE), unicode(r'\/')))
        s_r.append((re.compile(unicode(r'\"([^"]+)\"'), re.UNICODE), unicode(r'\g<1>')))
        s_r.append((re.compile(unicode(r' \[([^\]]+) \]'), re.UNICODE), unicode(r'( [\g<1>])?')))
        for x in s_r:
            ptn = x[0].sub(x[1], ptn)
        return ptn
    def _makeOrderedPtns(self, ptns):
        """Using the list ordered by lengths, produce a list of ordered regex patterns"""
        p_list = u""
        if len(ptns) > 0:
            p_list = u"(?P<numn>"
            for i in ptns: p_list += self._createPattern(i[1]) + u"|"
            p_list = p_list[0:len(p_list)-1]
            p_list += u")"
        return p_list
    def assignNumerationRegex(self):
        """Build the regex patterns for this institute's numeration styles"""
        def _my_cmpfunc(a, b):
            if a[0] < b[0]: return 1
            elif a[0] == b[0]: return 0
            else: return -1
        # Remove user-defined character classes:
        lenPtns = self._getPatternLenList()
        lenPtns.sort(_my_cmpfunc)
        # Set own list of regex patterns:
        self._numerationRegex = self._makeOrderedPtns(lenPtns)

    def _makeOrderedPtnsList(self, ptns):
        p_list = []
        if len(ptns) > 0:
            for p in ptns:
                p_itm = u"(?P<numn>" + self._createPattern(p[1]) + u")"
                p_list.append(p_itm)
        return p_list
    def assignNumerationRegexList(self):
        """Build the regex patterns for this institute's numeration styles"""
        def _my_cmpfunc(a, b):
            if a[0] < b[0]: return 1
            elif a[0] == b[0]: return 0
            else: return -1
        # Remove user-defined character classes:
        lenPtns = self._getPatternLenList()
        lenPtns.sort(_my_cmpfunc)
        # Set own list of regex patterns:
        self._numerationRegexList = self._makeOrderedPtnsList(lenPtns)
    def createTestPatternsList(self):
        def _my_cmpfunc(a, b):
            if a.length < b.length: return 1
            elif a.length == b.length: return 0
            else: return -1
        self.assignNumerationRegexList()
        self._preprintCatsList.sort(_my_cmpfunc)
        preprintCatPatternsList = {}
        for categ in self._preprintCatsList:
            categptnslist = []
            for num_ptn in self._numerationRegexList:
                categptnslist.append(re.compile(unicode(r'\b((?P<categ>') + categ.s_str + u')' + num_ptn + r')', re.UNICODE))
            preprintCatPatternsList[categ] = categptnslist
        self._preprintCatPatternsList = preprintCatPatternsList
    def matchCategs2(self, ln):
        """Accept a line. Try to find matches for each of the preprint categories of this institute within that line"""
        def _my_cmpfunc(a, b):
            if a.length < b.length: return 1
            elif a.length == b.length: return 0
            else: return -1
        inst_full_len = {}
        inst_RN_rep_str = {}
        self._preprintCatsList.sort(_my_cmpfunc)
        for categ in self._preprintCatsList:
            for ptn in self._preprintCatPatternsList[categ]:
                # Search for this categ in line:
                matches_iter = ptn.finditer(ln)
                for x in matches_iter:
                    # Get hyphenated numeration segment of category:
                    numnMatch = x.group('numn')
                    numnMatch = re.sub(r'\s', '-', numnMatch)
                    ## replace funny cases:
                    numnMatch = re.sub(r'-{2,}', '-', numnMatch)
                    numnMatch = re.sub(r'/-', '/', numnMatch)
                    numnMatch = re.sub(r'-/', '/', numnMatch)
                    numnMatch = re.sub(r'-/-', '/', numnMatch)
                    # Replace found categ in string with lowercase version:
                    foundCateg = x.group('categ')
                    foundCateg = foundCateg.lower()
                    ln = ln[0:x.start()] + foundCateg + ln[x.end('categ'):]
                    inst_full_len[x.start()] = len(x.group(0))
                    inst_RN_rep_str[x.start()] = categ.r_str + numnMatch
        return (inst_full_len, inst_RN_rep_str, ln)

    def matchCategs(self, ln):
        """Accept a line. Try to find matches for each of the preprint categories of this institute within that line"""
        def _my_cmpfunc(a,b):
            if a.length < b.length: return 1
            elif a.length == b.length: return 0
            else: return -1
        inst_full_len = {}
        inst_RN_rep_str = {}
        self._preprintCatsList.sort(_my_cmpfunc)
        for categ in self._preprintCatsList:
            # Search for this categ in line:
            # Make the regex:
            my_ptn = re.compile(unicode(r'\b((?P<categ>') + categ.s_str + u')' + self._numerationRegex + r')',re.UNICODE)
            # Perform the search:
            matches_iter = my_ptn.finditer(ln)
            # For each match, record its position, etc and replace it with lower-case version
            for x in matches_iter:
                # Get hyphenated numeration segment of category:
                numnMatch = x.group('numn')
                numnMatch = re.sub(r'\s', '-', numnMatch)
                # Replace found categ in string with lowercase version:
                foundCateg = x.group('categ')
                foundCateg = foundCateg.lower()
                ln = ln[0:x.start()] + foundCateg + ln[x.end('categ'):]
                inst_full_len[x.start()] = len(x.group(0))
                inst_RN_rep_str[x.start()] = categ.r_str + numnMatch
        return (inst_full_len, inst_RN_rep_str, ln)
    def addCategory(self, k, v): self._preprintCatsList.append(PreprintClassificationItem(k,v))
    def addNumerationStyle(self, num): self._numerationList.append(num)
    name = property(fget = getName, fset = setName)
    del setName, getName

class InstituteList:
    def __init__(self, fn = ''):
        self._iList = self._getInstituteList(fn)
        self._buildInstNumtnRegexs()
    def _buildInstNumtnRegexs(self):
        for i in self._iList: i.createTestPatternsList()
    def display(self):
        for x in self._iList: x.display()
    def _getInstituteList(self, fn):
        """Read the list of institutes in from the file and return an institute list. Terminates execution if cant read the file"""
        try:
            fh = open(fn, 'r')
            iList = []
            p_instName = re.compile(unicode(r'^\#{5}\s*(.+)\s*\#{5}$'),re.UNICODE)
            p_prepClass = re.compile(unicode(r'^\s*(\w.*?)\s*---\s*(\w.*?)\s*$'),re.UNICODE)
            p_numtn = re.compile(unicode(r'^\<(.+)\>$'),re.UNICODE)
            for x in fh:
                y = x.decode("utf-8")
                m_instName = p_instName.search(y)
                m_prepClass = p_prepClass.search(y)
                m_numtn = p_numtn.search(y)
                if m_instName is not None:
                    curInst = Institute(m_instName.group(1))
                    iList.append(curInst)
                elif m_prepClass is not None:
                    try: curInst.addCategory(m_prepClass.group(1), m_prepClass.group(2))
                    except AttributeError, NameError: pass
                elif m_numtn is not None:
                    try: curInst.addNumerationStyle(m_numtn.group(1))
                    except AttributeError, NameError: pass
            fh.close()
            return iList
        except IOError:
            import sys
            sys.exit('E: Cannot Open Institutes File "%s".' % fn)
    def identifyPreprintReferences(self, ln):
        """Accept a line of text (String) and search it against the institutes records held in order to identify references to an institutes preprints"""
        foundMatch = False
        identified_pp_len = {}
        identified_pp_repStr = {}
        for inst in self._iList:
            #(tmp_id_lens, tmp_id_repStrs, ln) = inst.matchCategs(ln)
            (tmp_id_lens, tmp_id_repStrs, ln) = inst.matchCategs2(ln)
            identified_pp_len.update(tmp_id_lens)
            identified_pp_repStr.update(tmp_id_repStrs)
        if len(identified_pp_len) > 0: foundMatch = True
        return (identified_pp_len, identified_pp_repStr, ln, foundMatch)

class LineIBIDidentifier:
    """Class to identify and record information about IBID ocurrences in a text line"""
    def __init__(self):
        """Initialise regex pattern used to identify an IBID item"""
        self._p_ibid = re.compile(unicode(r'(-|\b)(IBID\.?( ([A-H]|(I{1,3}V?|VI{0,3})|[1-3]))?)\s?:'),re.UNICODE)
        self._pIbidPresent = re.compile(unicode(r'IBID\.?\s?([A-H]|(I{1,3}V?|VI{0,3})|[1-3])?'),re.UNICODE)
    def lineHasIbid(self, ln):
        m_ibidPresent = self._pIbidPresent.search(ln)
        if m_ibidPresent is not None: return True
        else: return False
    def getIbidSeriesLetter(self, ln):
        m_ibid = self._pIbidPresent.search(ln)
        try: series_letter = m_ibid.group(1)
        except IndexError: series_letter = u""
        if series_letter is None: series_letter = u""
        return series_letter
    def identify_record_ibids(self, ln):
        """Identify the IBIDs in "line". Record their information (index position in line, match length, and matched text. When identified, the word IBID
           is replaced with a lower-case version of itself Finally, the line is returned with all IBIDs identified, along with a lists of the identified
           IBID text and length. These 3 items are returned in a tuple.
        """
        ibid_match_len = {}
        ibid_match_txt = {}
        matches_iter = self._p_ibid.finditer(ln)
        # Record dets of each match:
        for m in matches_iter:
            # Record match info
            ibid_match_len[m.start()] = len(m.group(2))
            ibid_match_txt[m.start()] = m.group(2)
            # Replace matched txt in line with
            # Lowercase version
            rep_str = m.group(2)
            rep_str = rep_str.lower()
            ln = ln[0:m.start(2)] + rep_str + ln[m.end(2):]
        return (ibid_match_len, ibid_match_txt, ln)

class URLidentifier:
    """Identify, record information about, and remove URLs from a line"""
    def __init__(self):
        """Initialise url recognition patterns"""
        self._urlstr = unicode(r'((https?|s?ftp):\/\/([\w\d\_\.\-])+(\/([\w\d\_\.\-])+)*(\/([\w\d\_\-]+\.\w{1,6})?)?)')
        self._p_rawURL = re.compile(self._urlstr,re.UNICODE|re.I)
        self._p_taggedURL = re.compile(unicode(r'(\<a\s+href\s*=\s*([\'"])?(((https?|s?ftp):\/\/)?([\w\d\_\.\-])+(\/([\w\d\_\.\-])+)*(\/([\w\d\_\-]+\.\w{1,6})?)?)([\'"])?\>([^\<]+)\<\/a\>)'),re.UNICODE|re.I)
    def removeURLs(self, ln):
        # Find URLS in tags:
        urlfound = False
        found_urlmatch_fulllen = {}
        found_urlstr = {}
        found_urldescstr = {}
        # Record and remove tagged URLs found in line
        m_taggedURL_iter = self._p_taggedURL.finditer(ln)
        for m in m_taggedURL_iter:
            urlfound = True
            startpos = m.start()
            endpos = m.end()
            matchlen = len(m.group())
            found_urlmatch_fulllen[startpos] = matchlen
            found_urlstr[startpos] = m.group(3)
            found_urldescstr[startpos] = m.group(12)
            ln = ln[0:startpos] + u"_"*matchlen + ln[endpos:]
        # Record and remove raw URLs found in line:
        m_rawURL_iter = self._p_rawURL.finditer(ln)
        for m in m_rawURL_iter:
            urlfound = True
            startpos = m.start()
            endpos = m.end()
            matchlen = len(m.group())
            found_urlmatch_fulllen[startpos] = matchlen
            found_urlstr[startpos] = m.group(1)
            found_urldescstr[startpos] = m.group(1)
            ln = ln[0:startpos] + u"_"*matchlen + ln[endpos:]
        return (found_urlmatch_fulllen, found_urlstr, found_urldescstr, urlfound, ln)

class ProcessedReferenceLineBuilder:
    """Create a "ProcessedReferenceLine" from a reference line and information about where any matched items are"""
    def __init__(self, titles_list, ibid_identifier, numeration_processor, line_cleaner):
        self._titleslist = titles_list
        self._ibidIdentifier = ibid_identifier
        self._numerationprocessor = numeration_processor
        self._linecleaner = line_cleaner
        self._p_lineMarker = RefLineNumerationListCompiler().getCompiledPatternList()
        self._searcher = LineSearcher()
        self._p_tagFinder = re.compile(unicode(r'(\<cds\.(TITLE|VOL|YR|PG|RN|SER|URI value="[^\>]+")\>)'),re.UNICODE)
        self._p_leadRubbishRemover = re.compile(unicode(r'^([\.,;:-]+|\s+)+'),re.UNICODE)
        self._p_getNumatn = re.compile(unicode(r'^(\s*.?,?\s*:\s\<cds\.VOL\>(\d+)\<\/cds\.VOL> \<cds\.YR\>\(([1-2]\d\d\d)\)\<\/cds\.YR\> \<cds\.PG\>([RL]?\d+[c]?)\<\/cds\.PG\>)'),re.UNICODE)
    def _buildProcessedLine(self,ln,rawline):
        """Given a potentially marked up reference line, build and return a "ProcessedReferenceLine" object"""
        processedLine = ProcessedReferenceLine()
        linebckp = ln
        ln = string.lstrip(ln)
        # Trim line marker from start of line if possible & add it as a line segment
        m_lineMarker = self._searcher.findAtStartLine(ln, self._p_lineMarker)
        if m_lineMarker is not None:
            processedLine.addSection(LineMarker(m_lineMarker.group(u'mark')))
            ln = ln[m_lineMarker.end():]
        else:
            processedLine.addSection(LineMarker(u" "))
        m_tag = self._p_tagFinder.search(ln)
        thismisc = u""
        while m_tag is not None:
            # Found citation markup tag in line
            tagtype = m_tag.group(2)
            if tagtype == u"TITLE":
                # Title section
                thisyr = thispg = thisvol = None
                # Get text up to point of this match:
                if len(self._p_leadRubbishRemover.sub(u"",ln[0:m_tag.start()])) > 0: thismisc += ln[0:m_tag.start()]
                m_titletxt = re.match(unicode(r'^(%s(\<cds\.TITLE\>([^\<]+)\<\/cds\.TITLE\>))'%(re.escape(ln[0:m_tag.start()]),)),ln,re.UNICODE)
                thistitle = m_titletxt.group(3)
                ln = ln[m_titletxt.end():]
                # Remove and add volume, year and pagination tags which follow title if present
                m_numatn = self._p_getNumatn.match(ln)
                if m_numatn is not None:
                    thisvol = m_numatn.group(2)
                    thisyr  = m_numatn.group(3)
                    thispg  = m_numatn.group(4)
                    ln = ln[m_numatn.end():]
                    if len(thismisc) == 0: thismisc = None
                    processedLine.addSection(TitleCitationStandard(thistitle, thismisc, thispg, thisvol, thisyr))
                    thismisc = u""
                else:
                    thismisc += u" " + thistitle
            elif tagtype == u"RN":
                # Preprint reference number section
                # Get misc text up to point of match
                if len(self._p_leadRubbishRemover.sub(u"",ln[0:m_tag.start()])) > 0: thismisc += ln[0:m_tag.start()]
                m_rntxt = re.match(unicode(r'^(%s(\<cds\.RN\>([^\<]+)\<\/cds\.RN\>))'%(re.escape(ln[0:m_tag.start()]),)),ln,re.UNICODE)
                thisrn = m_rntxt.group(3)
                ln = ln[m_rntxt.end():]
                if len(thismisc) == 0: thismisc = None
                processedLine.addSection(InstitutePreprintReferenceCitation(thisrn, thismisc))
                thismisc = u""
            elif string.find(tagtype ,u"URI") == 0:
                # URL found
                # Get misc text up to point of match
                if len(self._p_leadRubbishRemover.sub(u"",ln[0:m_tag.start()])) > 0: thismisc += ln[0:m_tag.start()]
                m_urlinfo = re.match(unicode(r'^(%s(\<cds\.URI value\=\"([^\>]+)\"\>([^\<]+)\<\/cds\.URI\>))'%(re.escape(ln[0:m_tag.start()]),)),ln,re.UNICODE)
                thisurl = m_urlinfo.group(3)
                thisurldescr = m_urlinfo.group(4)
                if len(thisurldescr) == 0: thisurldescr = thisurl
                if len(thismisc) == 0: thismisc = None
                processedLine.addSection(URLCitation(thisurl, thisurldescr, thismisc))
                thismisc = u""
                ln = ln[m_urlinfo.end():]
            elif tagtype == u"VOL":
                # Volume info - it wasnt found after a title, so treat as misc
                thismisc += ln[0:m_tag.start()]
                m_voltxt = re.match(unicode(r'^(%s(\<cds\.VOL\>(\d+)\<\/cds\.VOL\>))'%(re.escape(ln[0:m_tag.start()]),)),ln,re.UNICODE)
                thismisc += m_voltxt.group(3)
                ln = ln[m_voltxt.end():]
            elif tagtype == u"YR":
                # Year info - discard as misc since not found after title info
                thismisc += ln[0:m_tag.start()]
                m_yrtxt = re.match(unicode(r'^(%s(\<cds\.YR\>(\([1-2]\d\d\d\))\<\/cds\.YR\>))'%(re.escape(ln[0:m_tag.start()]),)),ln,re.UNICODE)
                thismisc += m_yrtxt.group(3)
                ln = ln[m_yrtxt.end():]
            elif tagtype == u"PG":
                # Pagination info - discard since not found after title info
                thismisc += ln[0:m_tag.start()]
                m_pgtxt = re.match(unicode(r'^(%s(\<cds\.PG\>([RL]?\d+[c]?)\<\/cds\.PG\>))'%(re.escape(ln[0:m_tag.start()]),)),ln,re.UNICODE)
                thismisc += m_pgtxt.group(3)
                ln = ln[m_pgtxt.end():]
            elif tagtype == u"SER":
                # Series info - discard since not after title info (should have been caught earlier infact)
                thismisc += ln[0:m_tag.start()]
                m_sertxt = re.match(unicode(r'^(%s(\<cds\.SER\>([A-H]|(I{1,3}V?|VI{0,3}))\<\/cds\.SER\>))'%(re.escape(ln[0:m_tag.start()]),)),ln,re.UNICODE)
                thismisc += m_sertxt.group(3)
                ln = ln[m_sertxt.end():]
            else:
                # Unknown tag (never happen) - discard as misc
                thismisc += ln[0:m_tag.start()]
                m_uknowntag = re.match(unicode(r'^(%s(\<cds\.[^\>]+?\>([^\<]+?)\<\/cds\.[^\>]+?\>))'%(re.escape(ln[0:m_tag.start()]),)),ln,re.UNICODE)
                thismisc += m_uknowntag.group(3)
                ln = ln[m_uknowntag.end():]
            m_tag = self._p_tagFinder.search(ln)
        if processedLine.getNumberCitations() == 0 and cfg_refextract_no_citation_treatment == 0:
            # No Citations were found and strict mode in use demanding that when no citations are found the entire ORIGINAL, UNTOUCHED line be marked up into misc
            processedLine = ProcessedReferenceLine()
            untouchedline = string.lstrip(rawline)
            m_lineMarker = self._searcher.findAtStartLine(untouchedline, self._p_lineMarker)
            if m_lineMarker is not None:
                processedLine.addSection(LineMarker(m_lineMarker.group(u'mark')))
                untouchedline = untouchedline[m_lineMarker.end():]
            else:
                processedLine.addSection(LineMarker(u" "))
            if len(self._p_leadRubbishRemover.sub(u"",untouchedline)) > 0:
                processedLine.addSection(LineMiscellaneousText(untouchedline))
        else:
            thismisc += ln
            if len(self._p_leadRubbishRemover.sub(u"",thismisc)) > 0:
                processedLine.addSection(LineMiscellaneousText(thismisc))
        return processedLine
    def getProcessedReferenceLine(self, titlematch_len, titlematch_str, pprintmatch_str, pprintmatch_len, urlmatchfull_len, urlmatch_str, url_desc_str,\
                                                                                     removed_spaces, rawline, original_line, working_line, foundCitations):
        marked_line = u"" # line after titles etc have been recognised & marked up with "<cds.TITLE/>" etc tags
        if not foundCitations:
            marked_line = original_line
        else:
            # Rebuild line with citations marked up and standardised:
            start_pos = 0 # First cell of the reference line...
            last_match = u""
            extras = 0 # Variable to count the extra spaces to add
            series_letter = u""
            replacement_types = {}
            url_keys = urlmatch_str.keys()
            url_keys.sort()
            title_keys = titlematch_str.keys()
            title_keys.sort()
            pp_keys = pprintmatch_str.keys()
            pp_keys.sort()
            spaces_keys = removed_spaces.keys()
            spaces_keys.sort()
            # First, adjust the index replacement values of the URI replacements as they were made before the multispaces etc were
            # stripped & other replacements made after this could therefore have the same replacement indeces
            uri_virtual_locations = self._getVirtualUrlPositions(url_keys, spaces_keys, removed_spaces)
            # Make dictionary containing the types of replacements to be made at each position:
            rep_types = self._getReplacementTypes(uri_virtual_locations,title_keys,pp_keys)
            rep_types_keys = rep_types.keys()
            rep_types_keys.sort()
            # Begin the rebuild:
            for repidx in rep_types_keys:
                true_repidx = repidx
                spare_repidx = repidx
                extras = 0
                # Account for any spaces stripped before these values:
                (true_repidx,spare_repidx,extras) =\
                  self._addExtraStrippedSpaces(spaces_keys,removed_spaces,rep_types,pprintmatch_len,titlematch_len,true_repidx,spare_repidx,repidx,extras)
                if rep_types[repidx] == u"TITLE":
                    # Process addition of text into line for title:
                    (marked_line,start_pos,last_match) = self._addLineTitle(titlematch_str,titlematch_len,original_line,marked_line,start_pos,repidx,true_repidx,extras,last_match)
                elif rep_types[repidx] == u"RN":
                    # Process addition of text into line for preprint reference:
                    (marked_line,start_pos) = self._replaceLineItemPreprintRef(pprintmatch_str,pprintmatch_len,original_line,marked_line,start_pos,repidx,true_repidx,extras)
                elif rep_types[repidx] == u"URI":
                    # Process addition of text into line for URL:
                    (marked_line,start_pos) = self._addLineURI(urlmatch_str,url_desc_str,urlmatchfull_len,uri_virtual_locations,original_line,marked_line,start_pos,repidx,true_repidx)
            marked_line = marked_line + original_line[start_pos:]
        marked_line = self._numerationprocessor.restandardise(marked_line)
        marked_line = self._numerationprocessor.removeSeriesTags(marked_line) # Remove any "Series tags"
        marked_line = self._linecleaner.clean(marked_line)
        return self._buildProcessedLine(marked_line,rawline)
    def _replaceIbid(self,series_letter,last_match,rebuiltLine,ibid_str):
        """Replace an IBID occurrence in a line with the "last matched" title in the line. Also take into account a new series letter governed by the ibid"""
        if series_letter != u"":
            # IBID to replace has a series letter, so if the last matched title had a series letter, this must be changed to the new series letter
            if string.find(last_match,",") != -1:
                # Presence of comma signifies possible series information. Only replace if it is a single item (e.g. "A")
                m_lastMatch = re.search(unicode(r'\, +([A-H]|(I{1,3}V?|VI{0,3}))$'),last_match,re.UNICODE)
                if m_lastMatch is not None:
                    temp_series = m_lastMatch.group(1)
                    if temp_series == series_letter:
                        rebuiltLine = rebuiltLine + u" <cds.TITLE>" + last_match + u"</cds.TITLE>"
                    else:
                        last_match = re.sub(u"(\\.?)(,?) %s$"%(temp_series,),u"\\g<1>\\g<2> %s"%(series_letter,),last_match)
                        rebuiltLine = rebuiltLine + u" <cds.TITLE>" + last_match + u"</cds.TITLE>"
                else:
                    # Series info of last match not letter or roman numeral: cannot be sure about meaning of IBID - dont replace it
                    rebuiltLine = rebuiltLine + ibid_str
            else:
                # Match had no series letter but IBID did. Add comma followed by IBID series letter to last match, then add it
                last_match = string.rstrip(last_match)
                if last_match[-1] == u".":
                    last_match = last_match + u", " + series_letter
                else:
                    # Last match end with space - replace all spaces at end
                    last_match = last_match + u"., " + series_letter
                rebuiltLine = rebuiltLine + u" <cds.TITLE>" + last_match + u"</cds.TITLE>"
        else:
            # IBID has no series letter. Replace as-is:
            rebuiltLine = rebuiltLine + u" <cds.TITLE>" + last_match + u"</cds.TITLE>"
        return (rebuiltLine,last_match)
    def _addLineTitle(self,titlematch_str,titlematch_len,orig_line,rebuiltLine,start_pos,repidx,true_repidx,extras,last_match):
        rebuiltLine=rebuiltLine+orig_line[start_pos:true_repidx]
        series_letter = u""
        #if self._ibidIdentifier.lineHasIbid(titlematch_str[repidx]):
        if titlematch_str[repidx].upper().find(u"IBID") != -1:
            # Replace IBID item
            # Get series letter
            series_letter = self._ibidIdentifier.getIbidSeriesLetter(titlematch_str[repidx])
            if last_match != "":
                # Replacement has already been made in this line. IBID can therefore be replaced
                (rebuiltLine,last_match) = self._replaceIbid(series_letter, last_match, rebuiltLine, titlematch_str[repidx])
                start_pos=true_repidx+titlematch_len[repidx]+extras
                if orig_line[start_pos] == u"." or orig_line[start_pos] == u":" or\
                      orig_line[start_pos] == u";":
                    # Skip past ".:;" which may have followed an IBID:
                    start_pos=start_pos+1
            else:
                # No replacements made in this line before this IBID (its a line with an IBID and
                # we dont know what the IBID refers to..ignore it
                rebuiltLine = rebuiltLine + orig_line[true_repidx:true_repidx + titlematch_len[repidx] + extras]
                start_pos=true_repidx+titlematch_len[repidx]+extras
        else:
            # Normal title replacement - not an IBID
            # Skip past any "[" or "(" chars
            rebuiltLine = rebuiltLine + u"<cds.TITLE>" + self._titleslist[titlematch_str[repidx]] + u"</cds.TITLE>"
            last_match = self._titleslist[titlematch_str[repidx]]
            start_pos = true_repidx+titlematch_len[repidx]+extras
            if orig_line[start_pos] == u"." or orig_line[start_pos] == u":" or\
                   orig_line[start_pos] == u";":
                # Skip past punctuation at end of title
                start_pos = start_pos + 1
        return (rebuiltLine,start_pos,last_match)
    def _replaceLineItemPreprintRef(self,pprintmatch_str,pprintmatch_len,orig_line,rebuiltLine,start_pos,repidx,true_repidx,extras):
        """Replace a Preprint reference item in the line with a marked-up, standardised version of itself"""
        # Often pprint refs are enclosed in "[]" chars which we dont want. Stop 1 char before this if possible:
        if (true_repidx - start_pos - 1) >= 0:
            rebuiltLine = rebuiltLine + orig_line[start_pos:true_repidx - 1]
        else:
            rebuiltLine = rebuiltLine + orig_line[start_pos:true_repidx]
        # Is next char a "[" or "("? Skip past it if yes:
        if orig_line[true_repidx] == u"[" or \
                   orig_line[true_repidx] == u"(":
            rebuiltLine = rebuiltLine + u" - "
        else:
            rebuiltLine = rebuiltLine + orig_line[true_repidx-1]
            rebuiltLine = rebuiltLine + u"<cds.RN>" + pprintmatch_str[repidx] + u"</cds.RN>"
        start_pos = true_repidx + pprintmatch_len[repidx] + extras
        try:
            if orig_line[start_pos] == u"]" or orig_line[start_pos] == u")":
                # Skip past preprint ref no closing brace
                start_pos = start_pos + 1
        except IndexError:
            # Went past end of line. Ignore.
            pass
        return (rebuiltLine, start_pos)
    def _addLineURI(self,urlmatch_str,urldesc_str,urlmatchfull_len,uri_virtual_locations,orig_line,rebuiltLine,start_pos,repidx,true_repidx):
        rebuiltLine = rebuiltLine + orig_line[start_pos:start_pos + true_repidx - start_pos]
        rebuiltLine = rebuiltLine + u"<cds.URI value=\"" + urlmatch_str[uri_virtual_locations[repidx]] + u"\">" + urldesc_str[uri_virtual_locations[repidx]] + u"</cds.URI>"
        start_pos = true_repidx + urlmatchfull_len[uri_virtual_locations[repidx]]
        return (rebuiltLine, start_pos)
    def _addExtraStrippedSpaces(self, spacesKeys, removed_spaces, rep_types, pprintmatch_len, titlematch_len, true_repidx, spare_repidx, repidx, extras):
        """For a replacement index position, calculate a new (correct) replacement index, based on any spaces that have been removed before it, according to the type of the replacement"""
        for strip_space in spacesKeys:
            if strip_space < true_repidx:
                # Spaces were removed before this replacement item should be placed. Add number of spaces removed to current replacement idx:
                true_repidx = true_repidx + removed_spaces[strip_space]
                spare_repidx = spare_repidx + removed_spaces[strip_space]
            elif (strip_space >= spare_repidx) and (rep_types[repidx] == u"TITLE") and\
                                    (strip_space < (spare_repidx + titlematch_len[repidx])):
                # Replacing a periodical title. Account for double spaces that may have been removed
                # from the title before it was recognised.
                spare_repidx = spare_repidx + removed_spaces[strip_space]
                extras = extras + removed_spaces[strip_space]
            elif (strip_space >= spare_repidx) and (rep_types[repidx] == u"RN") and\
                                    (strip_space < (spare_repidx + pprintmatch_len[repidx])):
                # Replacing an institute  preprint reference. Spaces would have been removed from this
                # pprint reference itself, and must therefore be added
                spare_repidx = spare_repidx + removed_spaces[strip_space]
                extras = extras + removed_spaces[strip_space]
        return (true_repidx, spare_repidx, extras)
    def _getReplacementTypes(self,urls,titles,preprints):
        """Make dictionary detailing the type of replacement made at each position"""
        rep_types = {}
        for idx in urls:
            rep_types[idx] = u"URI"
        for idx in titles:
            rep_types[idx] = u"TITLE"
        for idx in preprints:
            rep_types[idx] = u"RN"
        return rep_types
    def _getVirtualUrlPositions(self, url_keys, spaces_keys, removed_spaces):
        """URLs were removed before punctuation and multiple spaces were recorded and stripped. This method makes a dictionary of
           URL positions as-if the URLs had been identified/removed after the punctuation/spaces
        """
        uri_virtual_locations = {}
        for idx in url_keys:
            virtual_pos = idx
            for spcidx in spaces_keys:
                if spcidx < idx:
                    # Spaces were removed before this URL. Account for this.
                    virtual_pos = virtual_pos - removed_spaces[spcidx]
            # All spaces removed before this URL accounted for - add it to the dictionary
            uri_virtual_locations[virtual_pos] = idx
        return uri_virtual_locations


## NICK
    ## making a class to process a line of text for citations, creating a "ProcessedReferenceLine" object.
    ## will then be possible to test processing a single reference line at a time.

class ProcessedReferenceLineFactory:
    def __init__(self, institutes, titles):
        self._instlist = institutes
        self._titleslist = titles
        self._ibidIdentifier = LineIBIDidentifier()
        self._numerationIdentifier = NumerationHandler()
        self._lineCleaner = LineCleaner()
        self._lineBuilder = ProcessedReferenceLineBuilder(self._titleslist, self._ibidIdentifier,\
                                                          self._numerationIdentifier, self._lineCleaner)
        self._accentTransformer = EscapeSequenceTransformer()
        self._punctuationStripper = PunctuationStripper()
        self._multispaceRemover = MultispaceRemover()
        self._urlRemover = URLidentifier()
        
    def createLine(self, refline, verbose=0):
        ## Sanity Checking:
        if type(refline) not in (str, unicode):
            raise TypeError("""Expected argument of type 'str' or 'unicode', got type %s""" % type(refline))

        ## initialise some variables:
        citationMatch=False
        foundItem = False
        found_ibids_len = {}
        found_ibids_matchtxt = {}
        found_title_len = {}
        found_title_txt = {}
        found_urlmatch_fulllen = {}
        found_urlstr = {}
        found_urldescstr = {}

        if verbose != 0:
            ## display original line, before all attempts to standardise/recognise citations:
            sys.stderr.write("""Raw Line: %s\n""" % refline.encode("utf-8"))

        tmpLine = refline

        # Preliminary line cleaning: transform bad accents, clean punctuation & remove dbl-spaces
        tmpLine = self._accentTransformer.processLine(tmpLine)
        tmpLine = self._lineCleaner.clean(tmpLine)
        if verbose != 0:
            ## display line after accent cleaning:
            sys.stderr.write("""Line Cleaned: %s\n""" % tmpLine.encode("utf-8"))

        # Remove and record details of URLs
        #(found_urlmatch_fulllen, found_urlstr, found_urldescstr, foundItem, tmpLine) = self._urlRemover.removeURLs(tmpLine)
        if foundItem:
            citationMatch = True

        if verbose != 0:
            ## display line after URLs removed:
            sys.stderr.write("""URLs Removed: %s\n""" % tmpLine.encode("utf-8"))

        ## Standardise numeration:
        tmpLine = self._numerationIdentifier.standardise(tmpLine)
        tmpLine = self._lineCleaner.clean(tmpLine)
        if verbose != 0:
            ## display line after numeration identified and re-arranged:
            sys.stderr.write("""Numeration Treated: %s\n""" % tmpLine.encode("utf-8"))

        ## Upper-case the line:
        tmpLine2 = string.upper(tmpLine)
        if verbose != 0:
            ## display upper-cased line:
            sys.stderr.write("""Uppercase: %s\n""" % tmpLine2.encode("utf-8"))

        ## strip punctuation:
        tmpLine2 = self._punctuationStripper.strip(tmpLine2)
        if verbose != 0:
            ## display line with punctuation stripped:
            sys.stderr.write("""Punctuation Stripped: %s\n""" % tmpLine2.encode("utf-8"))

        ## remove multiple spaces:
        (removedSpaces,tmpLine2) = self._multispaceRemover.recordRemove(tmpLine2) # remove multispace & record their positions
        if verbose != 0:
            ## display line with multiple spaces removed:
            sys.stderr.write("""Mutiple Spaces Stripped: %s\n""" % tmpLine2.encode("utf-8"))

        ## standardise/regognise preprint reference report numbers
        (found_pp_len, found_pp_rep_str, tmpLine2, foundItem) = self._instlist.identifyPreprintReferences(tmpLine2)
        if foundItem:
            citationMatch = True
        if verbose != 0:
            ## display line with report numbers recognised:
            sys.stderr.write("""Preprint References Processed: %s\n""" % tmpLine2.encode("utf-8"))

        ## find non-standard titles:
        (found_title_len,found_title_txt,tmpLine2,foundItem) = self._titleslist.findPeriodicalTitles(tmpLine2)
        if foundItem:
            citationMatch = True
        if verbose != 0:
            ## display line with non-standard titles recognised:
            sys.stderr.write("""Non-Standard Titles Processed: %s\n""" % tmpLine2.encode("utf-8"))

        ## If there is an IBID in the line, do a 2nd pass to try to catch it & identify its meaning
        if tmpLine2.upper().find(u"IBID") != -1:
            # Record/remove IBID(s) in line
            (found_ibids_len,found_ibids_matchtxt,tmpLine2) = self._ibidIdentifier.identify_record_ibids(tmpLine2)
            # Add found ibids to title matches:
            for itm in found_ibids_len.keys(): found_title_len[itm] = found_ibids_len[itm]
            for itm in found_ibids_matchtxt.keys(): found_title_txt[itm] = found_ibids_matchtxt[itm]

        if verbose != 0:
            ## display line with IBIDs recognised:
            sys.stderr.write("""IBIDs Processed: %s\n""" % tmpLine2.encode("utf-8"))

        # Create "ProcessedReferenceLine":
        processed_line = \
                self._lineBuilder.getProcessedReferenceLine(found_title_len, found_title_txt, found_pp_rep_str, \
                                                            found_pp_len, found_urlmatch_fulllen, found_urlstr, \
                                                            found_urldescstr, removedSpaces, refline, tmpLine, \
                                                            tmpLine2, citationMatch)
        return processed_line

## END factory for creating ProcessedReferenceLine
## NICK

class ReferenceSectionMarkupProcessor:
    """Process a reference section. Line will be cleaned, and cited items will be identified and their notation standardised. ProcessedReferenceLine will be returned"""
    def __init__(self, institutes, titles):
        """Initialise the object with its own instance of a "ProcessedReferenceLineFactory" class.
        """
        self._processed_line_factory = ProcessedReferenceLineFactory(institutes, titles)
        
    def getProcessedReferenceSection(self, refSect, verbose=0):
        """Take a ReferenceSection as argument. For each line, process it"""
        processedRefSection = ProcessedReferenceSection()
        for line in refSect:
            processed_line = self._processed_line_factory.createLine(line.getContent(), verbose)

            processedRefSection.appendLine(processed_line)
        return processedRefSection


## class ReferenceSectionMarkupProcessor:
##     """Process a reference section. Line will be cleaned, and cited items will be identified and their notation standardised. ProcessedReferenceLine will be returned"""
##     def __init__(self, institutes, titles):
##         self._instlist = institutes
##         self._titleslist = titles
##         self._ibidIdentifier = LineIBIDidentifier()
##         self._numerationIdentifier = NumerationHandler()
##         self._lineCleaner = LineCleaner()
##         self._lineBuilder = ProcessedReferenceLineBuilder(self._titleslist, self._ibidIdentifier, self._numerationIdentifier, self._lineCleaner)
##         self._accentTransformer = EscapeSequenceTransformer()
##         self._punctuationStripper = PunctuationStripper()
##         self._multispaceRemover = MultispaceRemover()
##         self._urlRemover = URLidentifier()
##     def getProcessedReferenceSection(self, refSect):
##         """Take a ReferenceSection as argument. For each line, process it"""
##         processedRefSection = ProcessedReferenceSection()
##         for line in refSect:
##             sys.stderr.write("""Raw Line: %s\n""" % line.getContent().encode("utf-8"))
##             citationMatch=False
##             found_ibids_len = {}
##             found_ibids_matchtxt = {}
##             found_title_len = {}
##             found_title_txt = {}
##             tmpLine = line.getContent() # Got line as unicode string
##             # Remove and record details of URLs
##             #(found_urlmatch_fulllen, found_urlstr, found_urldescstr, foundItem, tmpLine) = self._urlRemover.removeURLs(tmpLine)
##             found_urlmatch_fulllen = {}
##             found_urlstr = {}
##             found_urldescstr = {}
##             foundItem = False
##             if foundItem: citationMatch = True
##             # Preliminary line cleaning: transform bad accents, clean punctuation & remove dbl-spaces
##             tmpLine = self._accentTransformer.processLine(tmpLine)
##             tmpLine = self._lineCleaner.clean(tmpLine)
##             sys.stderr.write("""Cleaned Accents/Line: %s\n""" % tmpLine.encode("utf-8"))
##             # Standardise numeration:
##             tmpLine = self._numerationIdentifier.standardise(tmpLine)
##             tmpLine = self._lineCleaner.clean(tmpLine)
##             sys.stderr.write("""Processed Numeration: %s\n""" % tmpLine.encode("utf-8"))
##             # ---> Standardise the titles:
##             tmpLine2 = string.upper(tmpLine) # uppercase the line
##             sys.stderr.write("""Uppercase: %s\n""" % tmpLine2.encode("utf-8"))
##             tmpLine2 = self._punctuationStripper.strip(tmpLine2) # Strip punctuation
##             sys.stderr.write("""Punctuation Stripped: %s\n""" % tmpLine2.encode("utf-8"))
##             (removedSpaces,tmpLine2) = self._multispaceRemover.recordRemove(tmpLine2) # remove multispace & record their positions
##             (found_pp_len, found_pp_rep_str, tmpLine2, foundItem) = self._instlist.identifyPreprintReferences(tmpLine2)
##             if foundItem: citationMatch = True
##             # find_nonstandard_titles
##             (found_title_len,found_title_txt,tmpLine2,foundItem) = self._titleslist.findPeriodicalTitles(tmpLine2)
##             if foundItem: citationMatch = True
##             # If there is an IBID in the line, do a 2nd pass to try to catch it & identify its meaning
##             if tmpLine2.upper().find(u"IBID") != -1:
##                 # Record/remove IBID(s) in line
##                 (found_ibids_len,found_ibids_matchtxt,tmpLine2) = self._ibidIdentifier.identify_record_ibids(tmpLine2)
##                 # Add found ibids to title matches:
##                 for itm in found_ibids_len.keys(): found_title_len[itm] = found_ibids_len[itm]
##                 for itm in found_ibids_matchtxt.keys(): found_title_txt[itm] = found_ibids_matchtxt[itm]
##             # Create "ProcessedReferenceLine":
##             thisProcessedLine = self._lineBuilder.getProcessedReferenceLine(found_title_len,found_title_txt,found_pp_rep_str,found_pp_len,\
##                                    found_urlmatch_fulllen, found_urlstr, found_urldescstr,removedSpaces,line.getContent(),tmpLine,tmpLine2,citationMatch)
##             processedRefSection.appendLine(thisProcessedLine)
##         return processedRefSection

class LineItem:
    def getSelfMARCXML(self):
        """Return self, as marc xml string"""
        pass

class LineMarker(LineItem):
    def __init__(self, val):
        if type(val) is str or type(val) is unicode: self._value = val
        else: self._value = u""
    def getSelfMARCXML(self):
        return u"""   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="o">""" + cgi.escape(self._value)+u"""</subfield>
   </datafield>\n"""

class LineMiscellaneousText(LineItem):
    def __init__(self, val):
        if type(val) is str or type(val) is unicode: self._value = val.strip()
        else: self._value = u""
    def getSelfMARCXML(self):
        return u"""   <datafield tag="999" ind1="C" ind2="5">
      <subfield code="m">"""+cgi.escape(self._value)+u"""</subfield>
   </datafield>\n"""

class Citation(LineItem):
    """Abstract - represents a citation instance.  Could be used to count citations found in a line"""
    pass

class TitleCitation(Citation):
    def __init__(self, title, misc = None, pg = None, vol = None, yr = None):
        self._title = title
        if misc is not None: self._misc = misc.strip()
        else: self._misc = misc
        self._page = pg
        self._volume = vol
        self._yr = yr
    def is_complete_citation(self):
        if None not in (self._title, self._volume, self._yr, self._page):
            return 1
        else:
            return 0
    def getSelfMARCXML(self):
        out = u"""   <datafield tag="999" ind1="C" ind2="5">\n"""
        if self._misc is not None and (type(self._misc) is unicode or type(self._misc) is str):
            out += u"""      <subfield code="m">"""+cgi.escape(self._misc)+u"""</subfield>\n"""
        out += u"""      <subfield code="t">"""+cgi.escape(self._title)+u"""</subfield>\n"""
        if self._page is not None and (type(self._page) is unicode or type(self._page) is str):
            out += u"""      <subfield code="p">"""+cgi.escape(self._page)+u"""</subfield>\n"""
        if self._volume is not None and (type(self._volume) is unicode or type(self._volume) is str):
            out += u"""      <subfield code="v">"""+cgi.escape(self._volume)+u"""</subfield>\n"""
        if self._yr is not None and (type(self._yr) is unicode or type(self._yr) is str):
            out += u"""      <subfield code="y">"""+cgi.escape(self._yr)+u"""</subfield>\n"""
        out += u"""   </datafield>\n"""
        return out

class TitleCitationStandard(Citation):
    """[journal name] [volume] ([year]) [pagination]"""
    def __init__(self, title, misc = None, pg = None, vol = None, yr = None):
        self._title = title
        if misc is not None: self._misc = misc.strip()
        else: self._misc = misc
        self._page = pg
        self._volume = vol
        self._yr = yr
    def is_complete_citation(self):
        if None not in (self._title, self._volume, self._yr, self._page):
            return 1
        else:
            return 0
    def hasMisc(self):
        if self._misc is not None and (type(self._misc) is unicode or type(self._misc) is str) and len(self._misc.strip("()[], {}-")) > 0 or not\
               (self._title is not None and self._page is not None and self._volume is not None and self._yr is not None):
            return True
        else:
            return False
    def getS_subfield(self):
        if self._title is not None and self._page is not None and self._volume is not None and self._yr is not None:
            return u"""      <subfield code="s">%s %s (%s) %s</subfield>\n"""%(self._title,self._volume,self._yr,self._page)
        else:
            return None
    def getSelfMARCXML(self, xtra_subfield=None):
        subfieldOpen = False
        out = u"""   <datafield tag="999" ind1="C" ind2="5">\n"""
        if self._misc is not None and (type(self._misc) is unicode or type(self._misc) is str):
            out += u"""      <subfield code="m">"""+cgi.escape(self._misc)
            subfieldOpen=True
        if self._title is not None and self._page is not None and self._volume is not None and self._yr is not None:
            if subfieldOpen:
                out += u"""</subfield>\n"""
                subfieldOpen=False
            out += u"""      <subfield code="s">%s %s (%s) %s</subfield>\n"""%(self._title,self._volume,self._yr,self._page)
        else:
            if not subfieldOpen:
                out += u"""      <subfield code="m">"""
                subfieldOpen = True
            if self._title is not None: out += u" %s"%(self._title,)
            if self._title is not None: out += u" %s"%(self._volume,)
            if self._title is not None: out += u" (%s)"%(self._yr,)
            if self._title is not None: out += u" %s"%(self._page,)
        if subfieldOpen:
            out += u"""</subfield>\n"""
            subfieldOpen=False
        if xtra_subfield is not None:
            out += xtra_subfield
        out += u"""   </datafield>\n"""
        return out

class InstitutePreprintReferenceCitation(Citation):
    def __init__(self, rn, misc = None):
        self._rn = rn
        if misc is not None and len(misc.strip("()[], {}-")) > 0: self._misc = misc.strip()
        else: self._misc = None
    def is_complete_citation(self):
        return 1
    def hasMisc(self):
        if self._misc is not None and (type(self._misc) is unicode or type(self._misc) is str) and len(self._misc.strip()) > 0:
            return True
        else:
            return False
    def getRN_subfield(self):
        return u"""      <subfield code="r">"""+cgi.escape(self._rn)+u"""</subfield>\n"""
    def getSelfMARCXML(self, xtra_subfield=None):
        out = u"""   <datafield tag="999" ind1="C" ind2="5">\n"""
        if self._misc is not None and (type(self._misc) is unicode or type(self._misc) is str):
            out += u"""      <subfield code="m">"""+cgi.escape(self._misc)+u"""</subfield>\n"""
        out += u"""      <subfield code="r">"""+cgi.escape(self._rn)+u"""</subfield>\n"""
        if xtra_subfield is not None:
            out += xtra_subfield
        out += u"""   </datafield>\n"""
        return out

class URLCitation(Citation):
    def __init__(self, url, urldescr, misc=None):
        self._url = url
        self._urldescr = urldescr
        if misc is not None: self._misc = misc.strip()
        else: self._misc = misc
    def is_complete_citation(self):
        return 1
    def getSelfMARCXML(self):
        out = u"""   <datafield tag="999" ind1="C" ind2="5">\n"""
        if self._misc is not None and (type(self._misc) is unicode or type(self._misc) is str):
            out += u"""      <subfield code="m">"""+cgi.escape(self._misc)+u"""</subfield>\n"""
        out += u"""      <subfield code="u">"""+cgi.escape(self._url)+u"""</subfield>\n"""
        out += u"""      <subfield code="z">"""+cgi.escape(self._urldescr)+u"""</subfield>\n"""
        out += u"""   </datafield>\n"""
        return out

class ProcessedReferenceLine:
    """This is a reference line that has been processed for cited items"""
    def __init__(self):
        self._segments = {} # Segments of reference line, each keyed by start point index. Each is a 'LineItem'.
        self._nextposn = 0
    def getSelfMARCXML(self):
        """Return an XML string containing this lines contents, marked up in XML MARC, as used in CDS"""
        i = 0
        lenline = len(self._segments)
        out = u""
        while i < lenline:
            if isinstance(self._segments[i],TitleCitationStandard) and i < lenline-1 and isinstance(self._segments[i+1],InstitutePreprintReferenceCitation) and not self._segments[i+1].hasMisc():
                # This is a $s (periodical title) reference, followed immediately by its report number ($r). Concat them both under the $s.
                out += self._segments[i].getSelfMARCXML(self._segments[i+1].getRN_subfield())
                i = i + 1
            elif isinstance(self._segments[i],InstitutePreprintReferenceCitation) and i < lenline-1 and isinstance(self._segments[i+1],TitleCitationStandard) and not self._segments[i+1].hasMisc():
                # This is a report number ($r) reference followed immediately by its periodical title ($s) reference.  Concat them both under $s.
                out += self._segments[i].getSelfMARCXML(self._segments[i+1].getS_subfield())
                i = i + 1
            else:
                out += self._segments[i].getSelfMARCXML()
            i = i + 1
        return out
    def addSection(self, newSect):
        if isinstance(newSect,LineItem):
            self._segments[self._nextposn] = newSect
            self._nextposn += 1

    def getNumberCitations(self):
        numMisc = 0
        numURL = 0
        numPreprintRef = 0
        numTitle = 0
        numsegments = len(self._segments)
        for i in range(0, numsegments):
            if isinstance(self._segments[i], LineMiscellaneousText):
                numMisc += 1
            elif isinstance(self._segments[i], Citation) \
                   and not self._segments[i].is_complete_citation():
                numMisc += 1
            else:
                if isinstance(self._segments[i], URLCitation):
                    numURL += 1
                elif isinstance(self._segments[i], InstitutePreprintReferenceCitation):
                    numPreprintRef += 1
                elif (isinstance(self._segments[i], TitleCitationStandard) or isinstance(self._segments[i], TitleCitation)):
                    numTitle += 1
        return (numMisc, numTitle, numPreprintRef, numURL)


class ProcessedReferenceSection:
    """This is a reference section after it has been processed to identify cited items.  It contains a list of ProcessedReferenceLines."""
    def __init__(self):
        self._lines = {}
        self._nextline = 0
    def getSelfMARCXML(self):
        """Return a unicode string of all reference lines marked up in MARC XML"""
        out = u""
        numlines = len(self._lines)
        for i in range(0,numlines): out += self._lines[i].getSelfMARCXML()
        return out
    def appendLine(self, ln):
        """Add a new line to the list of processed reference lines"""
        if isinstance(ln, ProcessedReferenceLine):
            self._lines[self._nextline] = ln
            self._nextline += 1
    def getNumberCitations(self):
        num_misc     = 0
        num_titles   = 0
        num_preprefs = 0
        num_urls     = 0
        numlines = len(self._lines)
        for i in range(0, numlines):
            (num_misc_in_line, num_titles_inline, num_preprefs_inline, num_urls_inline) =\
                                                               self._lines[i].getNumberCitations()
            num_misc     += num_misc_in_line
            num_titles   += num_titles_inline
            num_preprefs += num_preprefs_inline
            num_urls     += num_urls_inline
        return (num_misc, num_titles, num_preprefs, num_urls)

class NumerationHandler:
    """Class whose instances identify reference numeration patterns in a text line and rearrange them into standardised numeration patterns
       Returns line with numeration patterns marked up in an XML style
    """
    def __init__(self):
        self._ptnList = []
        self._checkAgainPtnList = []
        self._ptn_seriesRemove = re.compile(unicode(r'((\<cds.TITLE\>)([^\<]+)(\<\/cds.TITLE\>)\s*.?\s*\<cds\.SER\>([A-H]|(I{1,3}V?|VI{0,3}))\<\/cds\.SER\>)'),re.UNICODE)
        self._setSearchPatterns()
        self._setRecheckPatterns()
    def _setRecheckPatterns(self):
        """After the line has been rebuilt with marked up titles, it can be rechecked for numeration patterns because perhaps now more can be found with the aid of the recognised titles"""
        self._checkAgainPtnList.append([re.compile(unicode(r'\(?([12]\d{3})([A-Za-z]?)\)?,? *(<cds\.TITLE>(\.|[^<])*<\/cds\.TITLE>),? *(\b[Vv]o?l?\.?)?\s?(\d+)(,\s*|\s+)[pP]?[p]?\.?\s?([RL]?\d+[c]?)\-?[RL]?\d{0,6}[c]?'), re.UNICODE),\
                                        unicode('\\g<1>\\g<2>, \\g<3> \\g<6> (\\g<1>) \\g<8>')])
        self._checkAgainPtnList.append([re.compile(unicode(r'\(?([12]\d{3})([A-Za-z]?)\)?,? *(<cds\.TITLE>(\.|[^<])*<\/cds\.TITLE>),? *(\b[Vv]o?l?\.?)?\s?(\d+)\s?([A-H])\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)\-?[RL]?\d{0,6}[c]?'), re.UNICODE),\
                                        unicode('\\g<1>\\g<2>, \\g<3> \\g<6> \\g<7> \\g<8> (\\g<1>)')])
    def _setSearchPatterns(self):
        """Populate self._ptnList with seek/replace numeration pattern pairs"""

        pattern_nucphysb_subtitle = unicode(r'(?:[\(\[]\s*?(?:[Ff][Ss]|[Pp][Mm])\s*?\d{0,4}\s*?[\)\]])?')
        
        # Delete the colon and expressions as Serie, vol, V. inside the pattern <serie : volume>
        self._ptnList.append([re.compile(unicode(r'(Serie\s|\bS\.?\s)?([A-H])\s?[:,]\s?(\b[Vv]o?l?\.?)?\s?(\d+)'), re.UNICODE),\
                              unicode('\\g<2> \\g<4>')])
        
        # Use 4 different patterns to standardise numeration as <serie(?) : volume (year) page>

        ## Pattern 0 (was pattern 3): <x, vol, page, year>
        self._ptnList.append([re.compile(unicode(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?[,:\s]\s?') +\
                                         pattern_nucphysb_subtitle +\
                                         unicode(r'[,;:\s]?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?,?\s?\(?([1-2]\d\d\d)\)?'), re.UNICODE),\
                              unicode(' : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<4>)</cds.YR> <cds.PG>\\g<3></cds.PG> ')])
        self._ptnList.append([re.compile(unicode(r'\b') +\
                                         pattern_nucphysb_subtitle +\
                                         unicode(r'[,;:\s]?([Vv]o?l?\.?)?\s?(\d+)\s?[,:\s]\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?,?\s?\(?([1-2]\d\d\d)\)?'), re.UNICODE),\
                              unicode(' : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<4>)</cds.YR> <cds.PG>\\g<3></cds.PG> ')])

        # Pattern 1: <x, vol, year, page>
##         self._ptnList.append([re.compile(unicode(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?'), re.UNICODE),\
##                               unicode(' : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<3>)</cds.YR> <cds.PG>\\g<4></cds.PG> ')])
        ## <v, [FS]?, y, p>
        self._ptnList.append([re.compile(unicode(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?') +\
                                         pattern_nucphysb_subtitle +\
                                         unicode(r'[,;:\s]?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?'), re.UNICODE),\
                              unicode(' : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<3>)</cds.YR> <cds.PG>\\g<4></cds.PG> ')])
        ## <[FS]?, v, y, p>
        self._ptnList.append([re.compile(unicode(r'\b') +\
                                         pattern_nucphysb_subtitle +\
                                         unicode(r'[,;:\s]?([Vv]o?l?\.?)?\s?(\d+)\s?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?'), re.UNICODE),\
                              unicode(' : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<3>)</cds.YR> <cds.PG>\\g<4></cds.PG> ')])


        # Pattern 2: <vol, serie, year, page>
##         self._ptnList.append([re.compile(unicode(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?([A-H])\s?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?'), re.UNICODE),\
##                               unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<4>)</cds.YR> <cds.PG>\\g<5></cds.PG> ')])

        ## <v, s, [FS]?, y, p>
        self._ptnList.append([re.compile(unicode(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?([A-H])\s?') +\
                                         pattern_nucphysb_subtitle +\
                                         unicode(r'[,;:\s]?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?'), re.UNICODE),\
                              unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<4>)</cds.YR> <cds.PG>\\g<5></cds.PG> ')])
        ## <v, [FS]?, s, y, p
        self._ptnList.append([re.compile(unicode(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?') +\
                                         pattern_nucphysb_subtitle +\
                                         unicode(r'[,;:\s]?([A-H])\s?\(([1-2]\d\d\d)\),?\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?'), re.UNICODE),\
                              unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<4>)</cds.YR> <cds.PG>\\g<5></cds.PG> ')])



        # Pattern 4: <vol, serie, page, year>
##         self._ptnList.append([re.compile(unicode(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?([A-H])[,:\s]\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?,?\s?\(([1-2]\d\d\d)\)'), re.UNICODE),\
##                               unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<5>)</cds.YR> <cds.PG>\\g<4></cds.PG> ')])

        ## <v, s, [FS]?, p, y>
        self._ptnList.append([re.compile(unicode(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?([A-H])[,:\s]\s?') +\
                                         pattern_nucphysb_subtitle +\
                                         unicode(r'[,;:\s]?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?,?\s?\(([1-2]\d\d\d)\)'), re.UNICODE),\
                              unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<5>)</cds.YR> <cds.PG>\\g<4></cds.PG> ')])

        ## <v, [FS]?, s, p, y>
        self._ptnList.append([re.compile(unicode(r'(\b[Vv]o?l?\.?)?\s?(\d+)\s?') +\
                                         pattern_nucphysb_subtitle +\
                                         unicode(r'[,;:\s]?([A-H])[,:\s]\s?[pP]?[p]?\.?\s?([RL]?\d+[c]?)(?:\-|\255)?[RL]?\d{0,6}[c]?,?\s?\(([1-2]\d\d\d)\)'), re.UNICODE),\
                              unicode(' <cds.SER>\\g<3></cds.SER> : <cds.VOL>\\g<2></cds.VOL> <cds.YR>(\\g<5>)</cds.YR> <cds.PG>\\g<4></cds.PG> ')])
        
    def removeSeriesTags(self, ln):
        """Remove any "<cds.SER />" tags from a line.  Series information should be part of a title, not separate"""
        m_seriesTagLine = self._ptn_seriesRemove.search(ln)
        while m_seriesTagLine is not None:
            whole_match = m_seriesTagLine.group(0)
            title_tag_opener = m_seriesTagLine.group(2)
            title_text = m_seriesTagLine.group(3)
            title_tag_closer = m_seriesTagLine.group(4)
            series_letter = m_seriesTagLine.group(5)
            real_title_text = title_text
            # If there is no comma in the matched title, add one to the end of it before series info added. If there is already a comma present, simply discard the series info
            if string.find(real_title_text,u",") != -1:
                real_title_text = string.rstrip(real_title_text)
                if real_title_text[-1] == u".":
                    real_title_text = real_title_text + u", " + series_letter
                else:
                    real_title_text = real_title_text + u"., " + series_letter
            ln = re.sub(u"%s"%(re.escape(whole_match),),u"%s%s%s"%(title_tag_opener,real_title_text,title_tag_closer),ln,1)
            m_seriesTagLine = self._ptn_seriesRemove.search(ln)
        return ln
    def restandardise(self, ln):
        """Given that some more titles have been recognised within a line, reprocess that line in the hopes of recognising more numeration patterns"""
        for x in self._checkAgainPtnList:
            ln = x[0].sub(x[1], ln)
        return self.standardise(ln)
    def standardise(self, ln):
        """Accept ln (text line) as argument. Perform transformations on this line to replace non-standard numeration styles with marked-up versions in a standard format.
           These recognised and marked-up numeration patterns can later be used to identify cited documents
        """
        for x in self._ptnList:
            ln = x[0].sub(x[1], ln)
        return ln

class LineCleaner:
    """Class to enable lines to be cleaned of punctuation errors"""
    def __init__(self):
        self._correctionList = {}
        self._setCorrectionList()
    def _setCorrectionList(self):
        """Set the list of punctuation (etc) errors in a line to be corrected"""
        self._correctionList[re.compile(unicode(r'\s,'),re.UNICODE)]   = u','
        self._correctionList[re.compile(unicode(r'\s;'),re.UNICODE)]   = u';'
        self._correctionList[re.compile(unicode(r'\s\.'),re.UNICODE)]  = u'.'
        self._correctionList[re.compile(unicode(r':\s:'),re.UNICODE)]  = u':'
        self._correctionList[re.compile(unicode(r',\s:'),re.UNICODE)]  = u':'
        self._correctionList[re.compile(unicode(r'\s\]'),re.UNICODE)]  = u']'
        self._correctionList[re.compile(unicode(r'\[\s'),re.UNICODE)]  = u'['
        self._correctionList[re.compile(unicode(r'\\255'),re.UNICODE)] = u'-'   # Hyphen symbols
        self._correctionList[re.compile(u'\u02D7',re.UNICODE)]         = u'-'
        self._correctionList[re.compile(u'\u0335',re.UNICODE)]         = u'-'
        self._correctionList[re.compile(u'\u0336',re.UNICODE)]         = u'-'
        self._correctionList[re.compile(u'\u2212',re.UNICODE)]         = u'-'
        self._correctionList[re.compile(u'\u002D',re.UNICODE)]         = u'-'
        self._correctionList[re.compile(u'\uFE63',re.UNICODE)]         = u'-'
        self._correctionList[re.compile(u'\uFF0D',re.UNICODE)]         = u'-'
        self._correctionList[re.compile(unicode(r':(?!\s*<cds)'),re.UNICODE|re.I)] = u'' ## ADDED 02/08/2006
    def clean(self, ln):
        # Remove double spaces:
        p_dblSpace = re.compile(unicode(r'\s{2,}'),re.UNICODE)
        ln = p_dblSpace.sub(u' ', ln)
        # Correct other bad punctuation:
        for x in self._correctionList.keys():
            ln = x.sub(self._correctionList[x], ln)
        return ln

class PunctuationStripper:
    """Class to strip punctuation characters from a line & replace them with a space character"""
    def __init__(self):
        self._punct = re.compile(unicode(r'[\.\,\;\'\(\)\-]'),re.UNICODE)
        self._rep = u' '
    def strip(self, ln):
        return self._punct.sub(self._rep, ln)

class MultispaceRemover:
    """Class to remove all ocurrences of multiple spaces from a line and replace them with a single space while recording information about their positioning"""
    def __init__(self):
        self._spcPtn = re.compile(unicode(r'(\s{2,})'),re.UNICODE)
    def recordRemove(self, ln):
        removedSpaces = {}    # Records posn of removed multispace & length of truncation
        fromPos = 0           # Posn in line from which to check for multispaces
        # Search for multispace:
        ms_matches = self._spcPtn.finditer(ln)
        for m in ms_matches:
            removedSpaces[m.start()] = m.end() - m.start() - 1
        ln = self._spcPtn.sub(u' ', ln)
        # Return a tuple of 2 items: a dictionary containing the removed multispace info,
        # and the line itself after the multispaces have been converted to single spaces
        return (removedSpaces, ln)

def getFileList(fname):
    """Return a list of files to be processed"""
    flist = []
    if os.access(fname, os.R_OK):
        try:
            f = open(fname, "r")
            for line in f:
                flist.append(line.strip())
            f.close()
        except IOError:
            return None
        return flist
    else:
        return None

def getRecidFilenames(args):
    files = []
    for x in args:
        items = string.split(x, ":")
        if len(items) != 2:
            sys.stderr.write(u"W: Recid:filepath argument invalid. Skipping.\n")
            continue
        files.append((items[0],items[1]))
    return files

def main():
    displayraw = 0
    myoptions, myargs = getopt.getopt(sys.argv[1:], "hrV", ["help", "display-raw", "version"])
    for o in myoptions:
        if o[0] in ("-V","--version"):
            sys.stderr.write("%s\n" % (SystemMessage().getVersionMessage(),)) # Version message and stop
            sys.exit(0)
        elif o[0] in ("-h","--help"):
            sys.stderr.write("%s\n" % (SystemMessage().getHelpMessage(),)) # Help message and stop
            sys.exit(0)
        elif o[0] in ("-r", "--display-raw"):
            displayraw = 1
    if len(myargs) == 0:
        sys.stderr.write("%s\n" % (SystemMessage().getHelpMessage(),)) # Help message and stop
        sys.exit(0)
    recidfiles = getRecidFilenames(myargs)
    if len(recidfiles) == 0:
        sys.stderr.write("%s\n" % (SystemMessage().getHelpMessage(),)) # Help message and stop
        sys.exit(0)
    converterList=[PDFtoTextDocumentConverter()] # List of document converters to use
    titles_kb = KnowledgeBase(fn=cfg_refextract_kb_journal_titles)
    institutes = InstituteList(fn=cfg_refextract_kb_report_numbers)
    refSect_processor  = ReferenceSectionMarkupProcessor(institutes, titles_kb)
    openxmltag         = u"""<?xml version="1.0" encoding="UTF-8"?>"""
    opencollectiontag  = u"""<collection xmlns="http://www.loc.gov/MARC21/slim">"""
    closecollectiontag = u"""</collection>\n"""
    done_coltags = False

    if len(converterList) < 1:
        sys.stderr.write("E: No document converter tools available - cannot process reference extraction.\n" % (curitem,))
        sys.exit(1)

    for curitem in recidfiles:
        if not done_coltags:
            # Output collection tags:
            sys.stdout.write("%s\n" % (openxmltag.encode("utf-8"),))
            sys.stdout.write("%s\n" % (opencollectiontag.encode("utf-8"),))
            done_coltags = True

        extract_error = 0  ## optimistic - extraction was OK unless determined otherwise
        num_misc = num_preprefs = num_titles = num_urls = 0

        if os.access(curitem[1], os.F_OK|os.R_OK):
            # filepath OK - attempt to extract references:
            doc = None

            # Convert file to text:
            for conv in converterList:
                doc = conv.convertDocument(curitem[1])
                try:
                    if not doc.isEmpty():
                        break
                except AttributeError:
                    pass
                
            # Do "Extract References" Stage
            try:
                if not doc.isEmpty():
                    refSection = doc.extractReferences()
                    processedReferenceSection = refSect_processor.getProcessedReferenceSection(refSection)
                    (num_misc, num_titles, num_preprefs, num_urls) = processedReferenceSection.getNumberCitations()
                    if displayraw == 0:
                        refSection = ReferenceSection()
                else:
                    extract_error = 4
                    refSection = ReferenceSection()
                    processedReferenceSection = ProcessedReferenceSection()
            except AttributeError:
                extract_error = 4
                refSection = ReferenceSection()
                processedReferenceSection = ProcessedReferenceSection()
        else:
            ## Invalid filepath (or maybe bad permissions)
            extract_error = 1
            refSection = ReferenceSection()
            processedReferenceSection = ProcessedReferenceSection()
            
        ## display extracted references:
        ReferenceSectionDisplayer().display(extraction_status=extract_error,
                                            cnt_misc=num_misc,
                                            cnt_preprintref=num_preprefs,
                                            cnt_journalref=num_titles,
                                            cnt_urlref=num_urls,
                                            processed_refsect=processedReferenceSection,
                                            raw_refsect=refSection,
                                            recid=curitem[0])

    ## If an XML collection was opened, display closing tag
    if done_coltags:
        sys.stdout.write("%s\n" % (closecollectiontag.encode("utf-8"),))













