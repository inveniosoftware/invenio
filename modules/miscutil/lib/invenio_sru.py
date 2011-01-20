import re

class ContextSet:

    def __init__(self, short_name="", uri=""):
        "Initialize a ContextSet object"
        self.short_name = short_name
        self.uri = uri

    def translate_index_name(self, index_name):
        "Translate index"
        return index_name

    def translate_relation(self, relation):
        "Translate relation"
        return relation

    def translate_relation_qualifier(self, relation_qualifier):
        "Translate relation qualifier"
        return relation_qualifier

    def translate_relation(self, relation_modifier):
        "Translate relation modifier"
        return relation_modifier
    
    def translate_boolean_modified(self, boolean_modifier):
        "Translate boolean modifier"
        return boolean_modifier


class MarcContextSet(ContextSet):
    # FIXME: must apply around search terms ''
    # FIXME: better support for ANY indicators
    # FIXME: understand use of indicators...
    re_index_name = re.compile(r"marc\.(?P<tag>\d{3,5})(\$(?P<subfield>)|:(?P<indicator>))?")

    def __init__(self):
        "Initialize a MARC ContextSet object"
        self.short_name= "marc"
        self.uri = "info:srw/cql-context-set/1/marc-v1.0"

    def translate_index_name(self, index_name):
        "Translate index"
        try:
            match_obj = re_index_name.match(index_name)
        except:
            return index_name

        index_components = match_obj.groupdict()
        
        tag = index_components["tag"]
        subfield = index_components["subfield"]
        indicator = index_components["indicator"]
        if subfield is not None:
            return ("%-5s%s" % (tag, subfield)).replace(" ", "_")
        else:
            return ("%-5s%s" % (tag, subfield)).replace(" ", "_")


class DCContextSet(ContextSet):
    
    def __init__(self):
        "Initialize a Dublin Core ContextSet object"
        self.short_name= "dc"
        self.uri = "info:srw/cql-context-set/1/dc-v1.1"

    def translate_index_name(self, index_name):
        "Translate index"
        nindex_name = index_name
        if index_name == "creator":
            nindex_name = "author"
        elif index_name == "description":
            nindex_name = "abstract"

        return nindex_name
        
class CQLContextSet1_2(ContextSet):

    def __init__(self):
        "Initialize a CQL ContextSet object (1.2)"
        self.short_name= "cql"
        self.uri = "info:srw/cql-context-set/1/cql-v1.2"

    def translate_index_name(self, index_name):
        "Translate index"
        nindex_name = index_name
        if index_name == "allIndexes":
            return ""
        elif index_name == "serverchoice":
            return ""

    def translate_relation(self, relation):
        "Translate relation"
        return relation

class CQLContextSet1_1(CQLContextSet1_2):
    def __init__(self):
        "Initialize a CQL ContextSet object (1.1)"
        self.short_name= "cql"
        self.uri = "info:srw/cql-context-set/1/cql-v1.1"

    def translate_relation(self, relation):
        "Translate relation"
        nrelation = relation
        if nrelation == "exact":
            nrelation = "="
        elif nrelation == "exact":
            nrelation = "=="
        return nrelation

class CQLContextSet1_1old(CQLContextSet1_2):
    def __init__(self):
        "Initialize a CQL ContextSet object (1.1)"
        self.short_name= "cql"
        self.uri = "http://www.loc.gov/zing/cql/contextSets/cql/v1.1/"

def get_contextsets():
    context_sets = {}
    for contextset_class in (MarcContextSet, \
                             DCContextSet, \
                             CQLContextSet1_1, \
                             CQLContextSet1_1old, \
                             CQLContextSet1_2):
        contextset_obj = contextset_class()
        context_sets[contextset_obj.uri] = contextset_obj
    return context_sets