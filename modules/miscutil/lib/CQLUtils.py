
"""CQL utility functions and subclasses"""

from CQLParser import *
from types import ListType, IntType
from SRWDiagnostics import *
from invenio_sru import get_contextsets

try:
    from PyZ3950 import z3950, asn1, oids
    from PyZ3950.zdefs import make_attr
    asn1.register_oid (oids.Z3950_QUERY_CQL, asn1.GeneralString)
except:
    asn1 = None
    oids = None
    make_attr = None


class ZCQLConfig:

    DC = {'title' : 4,
          'subject' : 21,
          'creator' : 1003,
          'author' : 1003,
          'editor' : 1020,
          'publisher' : 1018,
          'description' : 62,
          'date' : 30,
          'resourceType' : 1031,
          'format' : 1034,
          'resourceIdentifier' : 12,
          'source' : 1019,
          'language' : 54
          }

    CQL = {'anywhere' : 1016,
           'serverChoice' : 1016}

    # The common bib1 points
    BIB1 = {"personal_name" : 1,
            "corporate_name" : 2,
            "conference_name" : 3,
            "title" : 4,
            "title_series" : 5,
            "title_uniform" : 6,
            "isbn" : 7,
            "issn" : 8,
            "lccn" : 9,
            "local_number" : 12,
            "dewey_number" : 13,
            "lccn" : 16,
            "local_classification" : 20,
            "subject" : 21,
            "subject_lc" : 27,
            "subject_local" : 29,
            "date" : 30,
            "date_publication" : 31,
            "date_acquisition" : 32,
            "local_call_number" : 53,
            "abstract" : 62,
            "note" : 63,
            "record_type" : 1001,
            "name" : 1002,
            "author" : 1003,
            "author_personal" : 1004,
            "identifier" : 1007,
            "text_body" : 1010,
            "date_modified" : 1012,
            "date_added" : 1011,
            "concept_text" : 1014,
            "any" : 1016,
            "default" : 1017,
            "publisher" : 1018,
            "record_source" : 1019,
            "editor" : 1020,
            "docid" : 1032,
            "anywhere" : 1035,
            "sici" : 1037
            }
    
  
    XD1 = {"title" : 1,
          "subject" : 2,
          "name" : 3,
          "description" : 4,
          "date" : 5,
          "type" : 6,
          "format" : 7,
          "identifier" : 8,
          "source" : 9,
          "langauge" : 10,
          "relation" : 11,
          "coverage" : 12,
          "rights" : 13}

    UTIL = {"record_date" : 1,
            "record_agent" : 2,
            "record_language" : 3,
            "control_number" : 4,
            "cost" : 5,
            "record_syntax" : 6,
            "database_schema" : 7,
            "score" : 8,
            "rank" : 9,
            "result_set_position" : 10,
            "all" : 11,
            "anywhere" : 12,
            "server_choice" : 13,
            "wildcard" : 14,
            "wildpath" : 15}

    def __init__(self):
        self.UTIL1 = self.UTIL
        self.XD = self.XD1


zConfig = ZCQLConfig()

invenio_contextsets = get_contextsets()

class CSearchClause(SearchClause):

    def convertMetachars(self, t):
        "Convert SRW meta characters in to Cheshire's meta characters"
        # Fail on ?, ^ or * not at the end.
        if (count(t, "?") != count(t, "\\?")):
            diag = Diagnostic28()
            diag.details = "? Unsupported"
            raise diag
        elif (count(t, "^") != count(t, "\\^")):
            diag = Diagnostic31()
            diag.details = "^ Unsupported"
            raise diag
        elif (count(t, "*") != count(t, "\\*")):
            if t[-1] != "*" or t[-2] == "\\":
                diag = Diagnostic28()
                diag.details = "Non trailing * unsupported"
                raise diag
            else:
                t[-1] = "#"
        t = replace(t, "\\^", "^")
        t = replace(t, "\\?", "?")
        t = replace(t, "\\*", "*")
        return t

    def toRPN(self, top=None):
        if not top:
            top = self

        if (self.relation.value in ['any', 'all']):
            # Need to split this into and/or tree
            if (self.relation.value == 'any'):
                bool = " or "
            else:
                bool = " and "
            words = self.term.value.split()
            self.relation.value = '='
            # Add 'word' relationModifier
            self.relation.modifiers.append(CModifierClause('cql.word'))
            
            # Create CQL, parse it, walk new tree
            idxrel = "%s %s" % (self.index.toCQL(), self.relation.toCQL())
            text = []
            for w in words:
                text.append('%s "%s"' % (idxrel, w))
            cql = bool.join(text)
            tree = parse(cql)
            return tree.toRPN(top)
        else:
            # attributes, term
            # AttributeElement: attributeType, attributeValue
            # attributeValue ('numeric', n) or ('complex', struct)
            if (self.index.value == 'resultsetid'):
                return ('op', ('resultSet', self.term.value))

            clause = z3950.AttributesPlusTerm()
            attrs = self.index.toRPN(top)
            if (self.term.value.isdigit()):
                self.relation.modifiers.append(CModifierClause('cql.number'))
            relattrs = self.relation.toRPN(top)
            attrs.update(relattrs)
            butes =[]
            for e in attrs.iteritems():
                butes.append((e[0][0], e[0][1], e[1]))

            clause.attributes = [make_attr(*e) for e in butes]
            clause.term = self.term.toRPN(top)

            return ('op', ('attrTerm', clause))

    def toInvenio(self, top=None):
        #if not top:
        #    top = self
        #text = []
        #for p in self.prefixes.keys():
        #    if (p <> ''):
        #        text.append('>%s="%s"' % (p, self.prefixes[p]))
        #    else:
        #        text.append('>"%s"' % (self.prefixes[p]))
        #text.append('%s %s "%s"' % (self.index, self.relation.toCQL(), self.term))
        #return ' '.join(text)
        text = ""
        nindex = self.index.toInvenio()
        if nindex:
            nindex = nindex.rstrip() + ":"

        terms_sep = " "
        relation = self.relation.value
        relation_prefix_uri = self.relation.prefixURI
        if invenio_contextsets.has_key(relation_prefix_uri):
            relation = invenio_contextsets[relation_prefix_uri].translate_relation(relation)
        if relation == "any":
            terms_sep = " or "
            terms = [nindex + item for item in self.term.value.split()]
            text = terms_sep.join(terms)

        elif relation == "all" or not relation:
            terms_sep = " and "
            terms = [nindex + item for item in self.term.value.split()]
            text = terms_sep.join(terms)
        
        elif relation in ("=", "==", "scr", "exact"):
            if nindex:
                text = nindex + '"%s"' % self.term.value
            else:
                text = self.term.value
        elif relation == "adj":
            text = nindex + "'%s'" % self.term.value
        elif relation == "<>":
            text = "not " + nindex + '"%s"' % self.term.value
        elif relation in ("<", "<="):
            # FIXME: < includes =
            text = nindex + '->"%s"' % self.term.value
        elif relation in (">", ">="):
            # FIXME: does not work
            text = nindex + '"%s"->' % self.term.value
        elif relation in ("within"):
            val1, val2 = self.term.value.split(" ", 1)
            text = nindex + '"%s"->"%s"' % (val1, val2)
        elif relation:
            #FIXME: unknown relation -> search in index
            text = nindex + "'" + self.term.value + "'"
        """
        for item in self.term.value.split():
            if item in ('and', 'or', 'not', 'prox', 'sortby'):
                text += " " + item + " "
            elif item  == 'prox':
                text += " and "
            elif item == 'sortby':
                pass
            else:
                if self.relation.value == "any":
                    text += " or "
                elif self.relation.value == "all":
                    text += " and "
                text += nindex + item + " "
        """
        return text


class CBoolean(Boolean):

    def toRPN(self, top):
        op = self.value
        if (self.value == 'not'):
            op = 'and-not'
        elif (self.value == 'prox'):
            # Create ProximityOperator
            prox = z3950.ProximityOperator()
            # distance, ordered, proximityUnitCode, relationType
            u = self['unit']
            try:
                units = ["", "character", "word", "sentence", "paragraph", "section", "chapter", "document", "element", "subelement", "elementType", "byte"]
                if (u.value in units):
                    prox.unit = ('known', units.index(u.value))
                else:
                    # Uhhhh.....
                    prox.unit = ('private', int(u.value))
            except:
                prox.unit = ('known', 2)

            d = self['distance']
            try:
                prox.distance = int(d.value)
            except:
                if (prox.unit == ('known', 2)):
                    prox.distance = 1
                else:
                    prox.distance = 0
            try:
                rels = ["", "<", "<=", "=", ">=", ">", "<>"]
                prox.relationType = rels.index(d.comparison)
            except:
                prox.relationType = 2

            prox.ordered = bool(self['ordered'])
            return ('op', ('prox', prox))
                    
        return (op, None)

    def toInvenio(self, top=None):
        return self.toCQL()

class CTriple(Triple):

    def toRPN(self, top=None):
        """rpnRpnOp"""
        if not top:
            top = self

        op = z3950.RpnRpnOp()
        op.rpn1 = self.leftOperand.toRPN(top)
        op.rpn2 = self.rightOperand.toRPN(top)
        op.op = self.boolean.toRPN(top)
        return ('rpnRpnOp', op)
        
    def toInvenio(self, top=None):
        """Invenio"""
        if not top:
            top = self

        txt = []
        #if (self.prefixes):
        #    for p in self.prefixes.keys():
        #        if (p <> ''):
        #            txt.append('>%s="%s"' % (p, self.prefixes[p]))
        #        else:
        #            txt.append('>"%s"' % (self.prefixes[p]))
        #    prefs = ' '.join(txt)
        #    return "(%s %s %s %s)" % (prefs, self.leftOperand.toCQL(), self.boolean.toCQL(), self.rightOperand.toCQL())
        #else:
        return "%s %s %s" % (self.leftOperand.toInvenio(), self.boolean.toInvenio(), self.rightOperand.toInvenio())

class CIndex(Index):
    def toRPN(self, top):
        self.resolvePrefix()
        pf = self.prefix
        if (not pf or pf in ['cql', 'dc']):
            pf = "bib1"
        pf = pf.upper()
        try:
            set = oids.oids['Z3950']['ATTRS'][pf]['oid']
        except:
            # Can't generate the set directly
            if (hasattr(top, 'config') and top.config):
                config = top.config
                # Check SRW Configuration
                cql = config.contextSetNamespaces['cql']
                index = self.value
                if self.prefixURI == cql and self.value == "serverchoice":
                    index = config.defaultIndex
                    pf = config.defaultContextSet

                pf = pf.lower()  # URGH! Standardise!
                if config.indexHash.has_key(pf) and config.indexHash[pf].has_key(index):
                    idx = config.indexHash[pf][index]
                    # Need to map from this list to RPN list
                    attrs = {}
                    for i in idx:
                        
                        set = oids.oids['Z3950']['ATTRS'][i[0].upper()]['oid']
                        type = int(i[1])
                        if (i[2].isdigit()):
                            val = int(i[2])
                        else:
                            val = i[2]
                        attrs[(set, type)] = val
                    return attrs

            else:
                print "Can't resolve %s" % pf
                raise(ValueError)
        
        if (self.value.isdigit()):
            # bib1.1018
            val = int(self.value)
        elif (hasattr(zConfig, pf)):
            map = getattr(zConfig, pf)
            if (map.has_key(self.value)):
                val = map[self.value]
            else:
                val = self.value
        else:
            # complex attribute for bib1
            val = self.value
            
        return {(set, 1) :  val}
            
    def toInvenio(self, top=None):
        self.resolvePrefix()
        prefix_uri = self.prefixURI
        if prefix_uri:
            prefix_uri = prefix_uri.strip()
        
        val = self.value
        if invenio_contextsets.has_key(prefix_uri):
            val = invenio_contextsets[prefix_uri].translate_index_name(val)
        elif prefix_uri is not None:
            #raise self.prefixURI
            pass
        return val.rstrip()

class CRelation(Relation):
    def toRPN(self, top):
        rels = ['', '<', '<=', '=', '>=', '>', '<>']
        set = z3950.Z3950_ATTRS_BIB1_ov


        vals = [None, None, None, None, None, None, None]



        if self.value in rels:
            vals[2] = rels.index(self.value)
        elif self.value in ['exact', 'scr']:
            vals[2] = 3
        elif (self.value == 'within'):
            vals[2] = 104

        if self['relevant']:
            vals[2] = 102
        elif self['stem']:
            vals[2] = 101
        elif self['phonetic']:
            vals[2] = 100

        if self['number']:
            vals[4] = 109
            vals[5] = 100
        elif self['date']:
            vals[4] = 5
        elif self['word']:
            vals[4] = 2

        if self.value == 'exact':
            vals[3] = 1
            vals[5] = 100 
            vals[6] = 3
        else:
            vals[3] = 3
            vals[6] = 1

        attrs = {}
        for x in range(1,7):
            if vals[x]:
                attrs[(z3950.Z3950_ATTRS_BIB1_ov, x)] = vals[x]

        return attrs
        
    #def toInvenio(self, top=None):
    #    return self.toCQL()

class CTerm(Term):
    def toRPN(self, top):
        return ('general', self.value)

    #def toInvenio(self, top=None):
    #    return self.toCQL()

class CModifierClause(ModifierClause):
    pass

class CModifierType(ModifierType):
    pass





