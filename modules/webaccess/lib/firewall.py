"""These functions are for realizing a firewall for records. Given a file of the
form:
query1 # a query
    rule1 # a 1st rule
    rule2 # a 2nd rule

query2
    rule3
    ...
in which every rows can have comments precedeed by '#', every query is in the
form of what is accepted by a websearch, every rules must be indented by at
least a space or a tab and consist of this syntax:
allow|forbid [reg] expression field
where allow means that every user who respects this rule for those recid may
see their documents, while forbid means the contrary;
reg means that the following expression is a regular expression;
expression could be an exact match or a regular expression (when reg is there);
field is a field to which apply this rule among:
    uid, nickname, email, groups, remote_addr, remote_ip, remote_host, external
where groups apply if there's at least a group to which the user belong that
correspond to this expression, and external means external account.
All the rules are applied in the arriving order. The first rules that match
return.
"""

from invenio.webgroup_dblayer import get_groups
from invenio.search_engine import perform_request_search
from invenio.webinterface_handler import http_get_credentials
from invenio.dbquery import run_sql
from invenio.access_control_config import CFG_FIREWALL_DEFAULT_ALLOW
from socket import gethostbyname
from sets import Set
import re
from cPickle import dumps, loads
from zlib import compress, decompress
from stat import S_ISREG, S_ISDIR, ST_MODE
import os

EMPTY_ROLE_DEFINITION=compress(dumps((CFG_FIREWALL_DEFAULT_ALLOW, ()), -1))

EMPTY_ROLE_DEFINITION_SRC=CFG_FIREWALL_DEFAULT_ALLOW and 'allow any' or 'deny any'

class FirewallException(Exception):
    """Just an Exception to discover if it's a Firewall problem"""
    pass


# Comment finder
no_comment_re = re.compile(r'[\s]*(?<!\\)#.*')

# Rule dissecter
rule_re = re.compile(r'(?P<command>allow|deny)[\s]+(?:(?P<not>not)[\s]+)?(?P<field>[\w]+)[\s]+(?P<expression>(?<!\\)\'.+?(?<!\\)\'|(?<!\\)\".+?(?<!\\)\"|(?<!\\)\/.+?(?<!\\)\/)(?P<more_expressions>([\s]*,[\s]*((?<!\\)\'.+?(?<!\\)\'|(?<!\\)\".+?(?<!\\)\"|(?<!\\)\/.+?(?<!\\)\/))*)(?:[\s]*(?<!\\).*)?', re.I)

any_rule_re = re.compile(r'(?P<command>allow|deny)[\s]+any[\s]*', re.I)

# Sub expression finder
expressions_re = re.compile(r'(?<!\\)\'.+?(?<!\\)\'|(?<!\\)\".+?(?<!\\)\"|(?<!\\)\/.+?(?<!\\)\/')

def _mkip (ip):

    """ Compute a numerical value for a dotted IP """

    num = 0L
    for i in map (int, ip.split ('.')): num = (num << 8) + i
    return num

_full = 2L ** 32 - 1


def ip_matcher_builder(group):
    gip, gmk = group.split('/')
    gip = _mkip(gip)
    gmk = int(gmk)
    mask = (_full - (2L ** (32 - gmk) - 1))
    if not (gip & mask == gip):
        raise FirewallException, "Netmask does not match IP (%Lx %Lx)" % (gip, mask)
    return (gip, mask)

def ipmatch(ip, ip_matcher):
    return _mkip(ip) & ip_matcher[1] == ip_matcher[0]

def definition_compiler(definition):
    """Given a text in which every row contains a rule it returns the compiled
    object rules"""
    line = 0
    ret = []
    default_allow_p = CFG_FIREWALL_DEFAULT_ALLOW
    for row in definition.split('\n'):
        line += 1
        g = no_comment_re.match(row)
        if g:
            clean_row = g.group('row').strip()
            if row:
                g = any_rule_re.match(clean_row)
                if g:
                    default_allow_p = g.group('command').lower() == 'allow'
                    break
                g = rule_re.match(clean_row)
                if g:
                    allow_p = g.group('command').lower() == 'allow'
                    not_p = g.group('not').lower() == 'not'
                    field = g.group('field').lower()
                    expressions = g.group('expression')+g.group('more_expressions')
                    expressions_list = []
                    for expr in expressions_re.finditer(expressions):
                        if expr[0] == '/':
                            try:
                                expressions_list.append((True, re.compile(expr[1:-1])))
                            except Exception, msg:
                                raise FirewallException, "Syntax error while compiling rule %s (line %s): %s is not a valid re because %s!" % (row, line, expr, msg)
                        else:
                            if field == 'remote_ip' and '/' in expr[1:-1]:
                                try:
                                    expressions_list(False, ip_matcher_builder(expr[1:-1]))
                                except Exception, msg:
                                    raise FirewallException, "Syntax error while compiling rule %s (line %s): %s is not a valid ip group because %s!" % (row, line, expr, msg)
                            else:
                                expressions_list.append(False, expr[1:-1])
                    expressions_list = tuple(expressions_list)
                    ret.append((allow_p, not_p, field, expressions_list))
                else:
                    raise FirewallException, "Syntax error while compiling rule %s (line %s): not a valid rule!" % (row, line)
    return (compress(dumps((default_allow_p, tuple(ret)), -1)))

#def find_parenthesis(text):
    #pos = 0
    #prev = ''
    #ret = []
    #in_quotes = False
    #in_2quotes = False
    #in_backslash = False
    #for s in text:
        #if prev == '\\':
            #in_backslash = not in_backslash
        #else:
            #in_backslash = False
        #if s == '"' and not in_backslash and not in_quotes:
            #in_2quotes = not in_2quotes
        #elif s == "'" and not in_backslash and not in_2quotes:
            #in_quotes = not in_quotes
        #elif not in_quotes and not in_2quotes and s in ['(', ')']:
            #ret.append((s, pos))
        #pos += 1
        #prev = s
    #return ret

#def parenthesis_matcher(text):
    #parenthesis= find_parenthesis(text)
    #queue = []
    #ret = []
    #for s, pos in parenthesis:
        #if s == '(':
            #queue.append(pos)
        #elif s == ')':
            #try:
                #pos2 = queue.pop()
            #except IndexError:
                #raise FirewallException, 'Parenthesis don\'t match!'
            #ret.append((pos2, pos))
        #else:
            #raise FirewallException, 'Currupted list of parenthesis!'
    #if queue:
        #raise FirewallException, 'Parenthesis don\'t match!'
    #ret.reverse()
    #return ret
    #for pos, pos2 in ret[1:]:
        #ret_text.append(text[pos+1:pos2-1])
    #return ret_text

def repair_role_definitions():
    definitions = run_sql("SELECT id, definition_src FROM accROLE""")
    for role_id, definition_src in definitions:
        run_sql("UPDATE accROLE SET definition=%s WHERE id=%s", (definition_compiler(definitions), role_id))

def store_role_definition(role_id, definition, definition_src):
    run_sql("UPDATE accROLE SET definition=%s, definition_src=%s WHERE id=%s", (definition, definition_src, role_id))

def load_role_definition(role_id):
    res = run_sql("SELECT definition FROM accROLE WHERE id=%s", (role_id, ), 1)
    if res:
        try:
            return load(decompress(res[0][0]))
        except Exception:
            repair_role_definitions()
            res = run_sql("SELECT definition FROM accROLE WHERE id=%s", (role_id, ), 1)
            if res:
                return loads(decompress(res[0][0]))
            else:
                return (CFG_FIREWALL_DEFAULT_ALLOW, ())
    else:
        return (CFG_FIREWALL_DEFAULT_ALLOW, ())

def firewall(user_info, definition):
    """Given a user_info dictionary, it matches the rules inside the definition
    in order to discover if the current user can access the content.
    """
    try:
        default_allow_p, definition = definition
        for (allow_p, not_p, field, expressions_list) in definition: # for every rule
            group_p = field in ['groups', 'apache_groups'] # Is it related to group?
            ip_p = field == 'remote_ip' # Is it related to Ips?
            next_rule_p = False # Silly flag to break 2 for cycle
            for reg_p, expr in expressions_list: # For every element in the rule
                if group_p: # Special case: groups
                    if reg_p: # When it is a regexp
                        for group in user_info[field]: # iterate over every group
                            if expr.match(group): # if it matches
                                if not_p: # if must not match
                                    next_rule_p = True # let's skip to next rule
                                    break
                                else: # Ok!
                                    return allow_p
                        if next_rule_p:
                            break # I said: let's skip to next rule ;-)
                    elif expr in user_info[field]: # Simple expression then just check for expr in groups
                        if not_p: # If expr is in groups then if must not match
                            break # let's skip to next rule
                        else: # Ok!
                            return allow_p
                elif reg_p: # Not a group, then easier. If it's a regexp
                    if expr.match(user_info[field]): # if it matches
                        if not_p: # If must not match
                            break # Let's skip to next rule
                        else:
                            return allow_p # Ok!
                elif ip_p: # If it's just a simple expression but an IP!
                    if type(expr) == type(()): # If it's an IP group request (similar to regexp)
                        if ip_matcher(user_info['remote_ip'], expr): # Then if Ip matches
                            if not_p: # If must not match
                                break # let's skip to next rule
                            else:
                                return allow_p # ok!
                    elif expr == user_info[field]: # Finally the easiest one!!
                        if not_p: # ...
                            break
                        else: # ...
                            return allow_p # ...
    except Exception, msg:
        raise FirewallException, msg
    return default_allow_p # By default we allow ;-) it'an OpenSource project

def deserialize(definition):
    return loads(uncompress(definition))
