
# Base Classes

class SRWDiagnostic (Exception):
    """ Base Diagnostic Class"""
    code = 0
    description = ""
    details = ""
    surrogate = 0
    fatal = 1

    def __str__(self):
        return "%d [%s]: %s" % (self.code, self.description, self.details)


class GeneralDiagnostic (SRWDiagnostic):
    pass

class CQLDiagnostic (SRWDiagnostic):
    pass

class RecordDiagnostic (SRWDiagnostic):
    pass

class ResultSetDiagnostic (SRWDiagnostic):
    pass

class SortDiagnostic (SRWDiagnostic):
    pass

class ExplainDiagnostic (SRWDiagnostic):
    pass

# Individual Diagnostics

class Diagnostic1 (GeneralDiagnostic):
    code = 1
    description = "Permanent system error"

class Diagnostic2 (GeneralDiagnostic):
    code = 2
    description = "System temporarily unavailable"

class Diagnostic3 (GeneralDiagnostic):
    code = 3
    description = "Authentication error"


class Diagnostic10 (CQLDiagnostic):
    code = 10
    description = "Malformed query"

class Diagnostic11 (CQLDiagnostic):
    code = 11
    description = "Unsupported query type"

class Diagnostic12 (CQLDiagnostic):
    code = 12
    description = "Too many characters in query"

class Diagnostic13 (CQLDiagnostic):
    code = 13
    description = "Unbalanced or illegal use of parentheses"

class Diagnostic14 (CQLDiagnostic):
    code = 14
    description = "Unbalanced or illegal use of quotes"

class Diagnostic15 (CQLDiagnostic):
    code = 15
    description = "Illegal or unsupported index set"

class Diagnostic16 (CQLDiagnostic):
    code = 16
    description = "Illegal or unsupported index"

class DiagnosticNew17 (CQLDiagnostic):
    code = 17
    description = "Illegal or unsupported combination of index and index set."

class Diagnostic18 (CQLDiagnostic):
    code = 18
    description = "Illegal or unsupported combination of indexes"

class Diagnostic19 (CQLDiagnostic):
    code = 19
    description = "Illegal or unsupported relation"

class Diagnostic20 (CQLDiagnostic):
    code = 20
    description = "Illegal or unsupported relation modifier"

class Diagnostic21 (CQLDiagnostic):
    code = 21
    description = "Illegal or unsupported combination of relation modifiers"

class Diagnostic22 (CQLDiagnostic):
    code = 22
    description = "Illegal or unsupported combination of relation and index"


class Diagnostic23 (CQLDiagnostic):
    code = 23
    description = "Too many characters in term"

class Diagnostic24 (CQLDiagnostic):
    code = 24
    description = "Illegal combination of relation and term"

class Diagnostic25 (CQLDiagnostic):
    code = 25
    description = "Special characters not quoted in term"

class Diagnostic26 (CQLDiagnostic):
    code = 26
    description = "Non special character escaped in term"

class Diagnostic27 (CQLDiagnostic):
    code = 27
    description = "Empty term unsupported"

class Diagnostic28 (CQLDiagnostic):
    code = 28
    description = "Masking character not supported"

class Diagnostic29 (CQLDiagnostic):
    code = 29
    description = "Masked words too short"

class Diagnostic30 (CQLDiagnostic):
    code = 30
    description = "Too many masking characters in term"

class Diagnostic31 (CQLDiagnostic):
    code = 31
    description = "Anchoring character not supported"

class Diagnostic32 (CQLDiagnostic):
    code = 32
    description = "Anchoring character in illegal or unsupported position."

class Diagnostic33 (CQLDiagnostic):
    code = 33
    description = "Combination of proximity/adjacency and masking characters not supported"

class Diagnostic34 (CQLDiagnostic):
    code = 34
    description = "Combination of proximity/adjacency and anchoring characters not supported"

class Diagnostic35 (CQLDiagnostic):
    code = 35
    description = "Term only exclusion (stop) words"

class Diagnostic36 (CQLDiagnostic):
    code = 36
    description = "Term in invalid format for index or relation"



class Diagnostic37 (CQLDiagnostic):
    code = 37
    description = "Illegal or unsupported boolean operator"

class Diagnostic38 (CQLDiagnostic):
    code = 38
    description = "Too many boolean operators"

class Diagnostic39 (CQLDiagnostic):
    code = 39
    description = "Proximity not supported"

class Diagnostic40 (CQLDiagnostic):
    code = 40
    description = "Illegal or unsupported proximity relation"

class Diagnostic41 (CQLDiagnostic):
    code = 41
    description = "Illegal or unsupported proximity distance"

class Diagnostic42 (CQLDiagnostic):
    code = 42
    description = "Illegal or unsupported proximity unit"

class Diagnostic43 (CQLDiagnostic):
    code = 43
    description = "Illegal or unsupported proximity ordering"

class Diagnostic44 (CQLDiagnostic):
    code = 44
    description = "Illegal or unsupported combination of proximity modifiers"

class Diagnostic45 (CQLDiagnostic):
    code = 45
    description = "Index set name (prefix) assigned to multiple identifiers"



class Diagnostic50 (ResultSetDiagnostic):
    code = 50
    description = "Result sets not supported"

class Diagnostic51 (ResultSetDiagnostic):
    code = 51
    description = "Result set does not exist"

class Diagnostic52 (ResultSetDiagnostic):
    code = 52
    description = "Result set temporarily unavailable"

class Diagnostic53 (ResultSetDiagnostic):
    code = 53
    description = "Result sets only supported for retrieval"

class Diagnostic54 (ResultSetDiagnostic):
    code = 54
    description = "Retrieval may only occur from an existing result set"

class Diagnostic55 (ResultSetDiagnostic):
    code = 55
    description = "Combination of result sets with search terms not supported"

class Diagnostic56 (ResultSetDiagnostic):
    code = 56
    description = "Only combination of single result set with search terms supported"

class Diagnostic57 (ResultSetDiagnostic):
    code = 57
    description = "Result set created but no records available"

class Diagnostic58 (ResultSetDiagnostic):
    code = 58
    description = "Result set created with unpredictable partial results available"

class Diagnostic59 (ResultSetDiagnostic):
    code = 59
    description = "Result set created with valid partial results available"




class Diagnostic60 (RecordDiagnostic):
    code = 60
    description = "Too many records retrieved"

class Diagnostic61 (RecordDiagnostic):
    code = 61
    description = "First record position out of range"

class Diagnostic62 (RecordDiagnostic):
    code = 62
    description = "Negative number of records requested"

class Diagnostic63 (RecordDiagnostic):
    code = 63
    description = "System error in retrieving records"

class Diagnostic64 (RecordDiagnostic):
    code = 64
    description = "Record temporarily unavailable"
    surrogate = 1

class Diagnostic65 (RecordDiagnostic):
    code = 65
    description = "Record does not exist"
    surrogate = 1

class Diagnostic66 (RecordDiagnostic):
    code = 66
    description = "Unknown schema for retrieval"

class Diagnostic67 (RecordDiagnostic):
    code = 67
    description = "Record not available in this schema"
    surrogate = 1

class Diagnostic68 (RecordDiagnostic):
    code = 68
    description = "Not authorised to send record"
    surrogate = 1

class Diagnostic69 (RecordDiagnostic):
    code = 69
    description = "Not authorised to send record in this schema"
    surrogate = 1

class Diagnostic70 (RecordDiagnostic):
    code = 70
    description = "Record too large to send"
    surrogate = 1


class Diagnostic80 (SortDiagnostic):
    code = 80
    description = "Sort not supported"

class Diagnostic81 (SortDiagnostic):
    code = 81
    description = "Unsupported sort type"

class Diagnostic82 (SortDiagnostic):
    code = 82
    description = "Illegal or unsupported sort sequence"

class Diagnostic83 (SortDiagnostic):
    code = 83
    description = "Too many records to sort"

class Diagnostic84 (SortDiagnostic):
    code = 84
    description = "Too many sort keys"

class Diagnostic85 (SortDiagnostic):
    code = 85
    description = "Duplicate sort keys"

class Diagnostic86 (SortDiagnostic):
    code = 86
    description = "Incompatible record formats"

class Diagnostic87 (SortDiagnostic):
    code = 87
    description = "Unsupported schema for sort"

class Diagnostic88 (SortDiagnostic):
    code = 88
    description = "Unsupported tag path for sort"

class Diagnostic89 (SortDiagnostic):
    code = 89
    description = "Tag path illegal or unsupported for schema"

class Diagnostic90 (SortDiagnostic):
    code = 90
    description = "Illegal or unsupported direction value"

class Diagnostic91 (SortDiagnostic):
    code = 91
    description = "Illegal or unsupported case value"

class Diagnostic92 (SortDiagnostic):
    code = 92
    description = "Illegal or unsupported missing value action"

class Diagnostic100 (ExplainDiagnostic):
    code = 100
    description = "Explain not supported"

class Diagnostic101 (ExplainDiagnostic):
    code = 101
    description = "Explain request type not supported"

class Diagnostic102 (ExplainDiagnostic):
    code = 102
    description = "Explain record temporarily unavailable"











    
