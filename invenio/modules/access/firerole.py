# This file is part of Invenio.
# Copyright (C) 2007, 2008, 2009, 2010, 2011, 2013, 2015 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Invenio Access Control FireRole.

These functions are for realizing a firewall like role definition for extending
webaccess to connect user to roles using every infos about users.
"""

import re

import sys

import time

from invenio.base.globals import cfg
from invenio.ext.logging import register_exception
from invenio.legacy.dbquery import blob_to_string, run_sql
from invenio.modules.access.local_config import \
    CFG_ACC_EMPTY_ROLE_DEFINITION_OBJ, \
    CFG_ACC_EMPTY_ROLE_DEFINITION_SER, \
    CFG_ACC_EMPTY_ROLE_DEFINITION_SRC

from six.moves import cPickle

from zlib import compress, decompress

from .errors import InvenioWebAccessFireroleError


__revision__ = "$Id$"

__lastupdated__ = """$Date$"""

if sys.hexversion < 0x2040000:
    # pylint: disable=W0622
    from sets import Set as set
    # pylint: enable=W0622


def compile_role_definition(firerole_def_src):
    """Compile role definition.

    Given a text in which every row contains a rule it returns the compiled
    object definition.
    Rules have the following syntax:
    allow|deny [not] field {list of one or more (double)quoted string or regexp}
    or allow|deny any
    Every row may contain a # sign followed by a comment which are discarded.
    Field could be any key contained in a user_info dictionary. If the key does
    not exist in the dictionary, the rule is skipped.
    The first rule which matches return.
    """
    line = 0
    ret = []
    default_allow_p = False
    if not firerole_def_src or not firerole_def_src.strip():
        firerole_def_src = CFG_ACC_EMPTY_ROLE_DEFINITION_SRC
    for row in firerole_def_src.split('\n'):
        line += 1
        row = row.strip()
        if not row:
            continue
        clean_row = _no_comment_re.sub('', row)
        if clean_row:
            g = _any_rule_re.match(clean_row)
            if g:
                default_allow_p = g.group('command').lower() == 'allow'
                break
            g = _rule_re.match(clean_row)
            if g:
                allow_p = g.group('command').lower() == 'allow'
                not_p = g.group('not') is not None
                field = g.group('field').lower()
                # Renaming groups to group
                for alias_item in _aliasTable:
                    if field in alias_item:
                        field = alias_item[0]
                        break
                if field.startswith('precached_'):
                    raise InvenioWebAccessFireroleError(
                        "Error while compiling rule %s (line %s): %s is a "
                        "reserved key and can not be used in FireRole rules!"
                        % (row, line, field))
                expressions = g.group(
                    'expression') + g.group('more_expressions')
                expressions_list = []
                for expr in _expressions_re.finditer(expressions):
                    expr = expr.group()
                    if field in ('from', 'until'):
                        try:
                            expressions_list.append(
                                (False,
                                 time.mktime(time.strptime(expr[1:-1],
                                                           '%Y-%m-%d'))))
                        except Exception as msg:
                            raise InvenioWebAccessFireroleError(
                                "Syntax error while compiling rule %s "
                                "(line %s): %s is not a valid date with format "
                                "YYYY-MM-DD because %s!"
                                % (row, line, expr, msg))
                    elif expr[0] == '/':
                        try:
                            expressions_list.append(
                                (True, re.compile(expr[1:-1], re.I)))
                        except Exception as msg:
                            raise InvenioWebAccessFireroleError(
                                "Syntax error while compiling rule %s "
                                "(line %s): %s is not a valid re because %s!"
                                % (row, line, expr, msg))
                    else:
                        if field == 'remote_ip' and '/' in expr[1:-1]:
                            try:
                                expressions_list.append(
                                    (False, _ip_matcher_builder(expr[1:-1])))
                            except Exception as msg:
                                raise InvenioWebAccessFireroleError(
                                    "Syntax error while compiling rule %s "
                                    "(line %s): %s is not a valid ip group "
                                    "because %s!" % (row, line, expr, msg))
                        else:
                            expressions_list.append((False, expr[1:-1]))
                expressions_list = tuple(expressions_list)
                if field in ('from', 'until'):
                    if len(expressions_list) != 1:
                        raise InvenioWebAccessFireroleError(
                            "Error when compiling rule %s (line %s): exactly "
                            "one date is expected when using 'from' or "
                            "'until', but %s were found"
                            % (row, line, len(expressions_list)))
                    if not_p:
                        raise InvenioWebAccessFireroleError(
                            "Error when compiling rule %s (line %s): 'not' is "
                            "not allowed when using 'from' or 'until'"
                            % (row, line))
                ret.append((allow_p, not_p, field, expressions_list))
            else:
                raise InvenioWebAccessFireroleError(
                    "Syntax error while compiling rule %s (line %s): not a "
                    "valid rule!" % (row, line))
    return (default_allow_p, tuple(ret))


def repair_role_definitions():
    """Try to rebuild compiled serialized definitions from source.

    Try to rebuild compiled serialized definitions from their respectives
    sources. This is needed in case Python break back compatibility.
    """
    definitions = run_sql("""SELECT id, firerole_def_src FROM "accROLE" """)
    for role_id, firerole_def_src in definitions:
        serialized = serialize(compile_role_definition(firerole_def_src))
        run_sql("""UPDATE "accROLE" SET firerole_def_ser=%s WHERE id=%s""",
                (bytearray(serialized) if serialized else None, role_id))


def store_role_definition(role_id, firerole_def_ser, firerole_def_src):
    """Store a compiled serialized definition and its source.

    Store in the database alongside the role to which it belong.
    :param role_id: the role_id
    :param firerole_def_ser: the serialized compiled definition
    :param firerole_def_src: the sources from which the definition was taken
    """
    run_sql("""UPDATE "accROLE" SET firerole_def_ser=%s, firerole_def_src=%s """
            """WHERE id=%s""", (firerole_def_ser, firerole_def_src, role_id))


def load_role_definition(role_id):
    """Load the definition corresponding to a role.

    If the compiled definition is corrupted it try to repairs definitions from
    their sources and try again to return the definition.

    :param role_id:
    :return: a deserialized compiled role definition
    """
    res = run_sql("""SELECT firerole_def_ser FROM "accROLE" WHERE id=%s""",
                  (role_id, ), 1, run_on_slave=True)
    if res:
        try:
            return deserialize(res[0][0])
        except Exception:
            # Something bad might have happened? (Update of Python?)
            repair_role_definitions()
            res = run_sql("""SELECT firerole_def_ser FROM "accROLE" WHERE """
                          """id=%s""", (role_id, ), 1, run_on_slave=True)
            if res:
                return deserialize(res[0][0])
    return CFG_ACC_EMPTY_ROLE_DEFINITION_OBJ


def acc_firerole_extract_emails(firerole_def_obj):
    """Extract all the possible email addresses.

    Best effort function to extract all the possible email addresses
    authorized by the given firerole.
    """
    authorized_emails = set()
    try:
        default_allow_p, rules = firerole_def_obj
        # for every rule
        for (allow_p, not_p, field, expressions_list) in rules:
            if not_p:
                continue
            if field == 'group':
                for reg_p, expr in expressions_list:
                    if reg_p:
                        continue
                    if cfg['CFG_CERN_SITE'] and expr.endswith(' [CERN]'):
                        authorized_emails.add(
                            expr[:-len(' [CERN]')].lower().strip() + ':cern.ch')
                        emails = run_sql(
                            "SELECT user.email FROM usergroup JOIN "
                            "user_usergroup ON "
                            "usergroup.id=user_usergroup.id_usergroup "
                            "JOIN user ON user.id=user_usergroup.id_user "
                            "WHERE usergroup.name=%s", (expr, ))
                    for email in emails:
                        authorized_emails.add(email[0].lower().strip())
            elif field == 'email':
                for reg_p, expr in expressions_list:
                    if reg_p:
                        continue
                    authorized_emails.add(expr.lower().strip())
            elif field == 'uid':
                for reg_p, expr in expressions_list:
                    if reg_p:
                        continue
                    email = run_sql("SELECT email FROM user WHERE id=%s",
                                    (expr, ))
                    if email:
                        authorized_emails.add(email[0][0].lower().strip())
        return authorized_emails
    except Exception as msg:
        raise InvenioWebAccessFireroleError(msg)


def acc_firerole_check_user(user_info, firerole_def_obj):
    """Matche the rules inside the deserialized compiled definition.

    Given a user_info dictionary, it matches the rules inside the deserialized
    compiled definition in order to discover if the current user match the roles
    corresponding to this definition.
    :param user_info: a dict produced by collect_user_info which contains every
    info about a user
    :param firerole_def_obj: a compiled deserialized definition produced by
    compile_role_defintion
    :return: True if the user match the definition, False otherwise.
    """
    try:
        default_allow_p, rules = firerole_def_obj
        # for every rule
        for (allow_p, not_p, field, expressions_list) in rules:
            group_p = field == 'group'  # Is it related to group?
            ip_p = field == 'remote_ip'  # Is it related to Ips?
            until_p = field == 'until'  # Is it related to dates?
            from_p = field == 'from'  # Idem.
            next_expr_p = False  # Silly flag to break 2 for cycles
            if field not in user_info and not from_p and not until_p:
                continue
            # For every element in the rule
            for reg_p, expr in expressions_list:
                if group_p:  # Special case: groups
                    if reg_p:  # When it is a regexp
                        # iterate over every group
                        for group in user_info[field]:
                            if expr.match(group):  # if it matches
                                if not_p:  # if must not match
                                    # let's skip to next expr
                                    next_expr_p = True
                                    break
                                else:  # Ok!
                                    return allow_p
                        if next_expr_p:
                            break  # I said: let's skip to next rule ;-)
                    # Simple expression then just check for expr in groups
                    elif expr.lower() in [group.lower()
                                          for group in user_info[field]]:
                        # If expr is in groups then if must not match
                        if not_p:
                            break  # let's skip to next expr
                        else:  # Ok!
                            return allow_p
                elif reg_p:  # Not a group, then easier. If it's a regexp
                    if expr.match(user_info[field]):  # if it matches
                        if not_p:  # If must not match
                            break  # Let's skip to next expr
                        else:
                            return allow_p  # Ok!
                # If it's just a simple expression but an IP!
                elif ip_p and isinstance(expr, tuple):
                    # Then if Ip matches
                    if _ipmatch(user_info['remote_ip'], expr):
                        if not_p:  # If must not match
                            break  # let's skip to next expr
                        else:
                            return allow_p  # ok!
                elif until_p:
                    if time.time() <= expr:
                        if allow_p:
                            break
                        else:
                            return False
                    elif allow_p:
                        return False
                    else:
                        break
                elif from_p:
                    if time.time() >= expr:
                        if allow_p:
                            break
                        else:
                            return False
                    elif allow_p:
                        return False
                    else:
                        break
                # Finally the easiest one!!
                elif expr.lower() == str(user_info[field]).lower():
                    if not_p:  # ...
                        break
                    else:  # ...
                        return allow_p  # ...
            if not_p and not next_expr_p:  # Nothing has matched and we got not
                return allow_p  # Then the whole rule matched!
    except Exception as msg:
        register_exception(alert_admin=True)
        raise InvenioWebAccessFireroleError(msg)
    return default_allow_p  # By default we allow ;-) it'an OpenAccess project


def serialize(firerole_def_obj):
    """Serialize and compress a definition."""
    if firerole_def_obj == CFG_ACC_EMPTY_ROLE_DEFINITION_OBJ:
        return CFG_ACC_EMPTY_ROLE_DEFINITION_SER
    elif firerole_def_obj:
        return compress(cPickle.dumps(firerole_def_obj, -1))
    else:
        return CFG_ACC_EMPTY_ROLE_DEFINITION_SER


def deserialize(firerole_def_ser):
    """Deserialize and decompress a definition."""
    if firerole_def_ser:
        return cPickle.loads(decompress(blob_to_string(firerole_def_ser)))
    else:
        return CFG_ACC_EMPTY_ROLE_DEFINITION_OBJ

# IMPLEMENTATION

# Comment finder
_no_comment_re = re.compile(r'[\s]*(?<!\\)#.*')

# Rule dissecter
_rule_re = re.compile(
    r'(?P<command>allow|deny)[\s]+(?:(?P<not>not)[\s]+)?(?P<field>[\w]+)[\s]+'
    r'(?P<expression>(?<!\\)\'.+?(?<!\\)\'|(?<!\\)\".+?(?<!\\)\"|(?<!\\)\/.+?'
    r'(?<!\\)\/)(?P<more_expressions>([\s]*,[\s]*((?<!\\)\'.+?(?<!\\)\'|'
    r'(?<!\\)\".+?(?<!\\)\"|(?<!\\)\/.+?(?<!\\)\/))*)(?:[\s]*(?<!\\).*)?', re.I)

_any_rule_re = re.compile(r'(?P<command>allow|deny)[\s]+(any|all)[\s]*', re.I)

# Sub expression finder
_expressions_re = re.compile(
    r'(?<!\\)\'.+?(?<!\\)\'|(?<!\\)\".+?(?<!\\)\"|(?<!\\)\/.+?(?<!\\)\/')


def _mkip(ip):
    """Compute a numerical value for a dotted IP."""
    num = 0L
    if '.' in ip:
        for i in map(int, ip.split('.')):
            num = (num << 8) + i
    return num

_full = 2L ** 32 - 1


_aliasTable = (('group', 'groups'), )


def _ip_matcher_builder(group):
    """Compile a string "ip/bitmask" (i.e. 127.0.0.0/24).

    :param group: a classical "ip/bitmask" string
    :return: a tuple containing the gip and mask in a binary version.
    """
    gip, gmk = group.split('/')
    gip = _mkip(gip)
    gmk = int(gmk)
    mask = (_full - (2L ** (32 - gmk) - 1))
    if not (gip & mask == gip):
        raise InvenioWebAccessFireroleError(
            "Netmask does not match IP (%Lx %Lx)" % (gip, mask))
    return (gip, mask)


def _ipmatch(ip, ip_matcher):
    """Check if an ip matches an ip_group.

    :param ip: the ip to check
    :param ip_matcher: a compiled ip_group produced by ip_matcher_builder
    :return: True if ip matches, False otherwise
    """
    return _mkip(ip) & ip_matcher[1] == ip_matcher[0]
