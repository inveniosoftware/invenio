# -*- coding: utf-8 -*-
# logicutils.py was originally distributed as part of the aima-python project, at
# http://code.google.com/p/aima-python/
# At the time it was integrated into Invenio (2010 May 20), aima-python
# had a notice on its website declaring the code to be under the "MIT license"
# and linking to http://www.opensource.org/licenses/mit-license.php by way of
# explanation.
#
# The contents of this file remain under that license (included below).  If
# you modify this file, just add your name and email address as it appears
# below.  See also:
# http://www.softwarefreedom.org/resources/2007/gpl-non-gpl-collaboration.html
#
# Portions Copyright 2010, Peter Norvig <peter.norvig@google.com>
# Portions Copyright 2010, Joseph Blaylock <jrbl@slac.stanford.edu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
"""Representations and Inference for Logic (Chapters 7-10)

from __future__ import print_function

Covers both Propositional and First-Order Logic. First we have important data
types:

    Expr          A logical expression
    substitution  Implemented as a dictionary of var:value pairs, {x:1, y:x}

Be careful: some code here may not expect to take Exprs as arguments.

    pl_true          Evaluate a propositional logical sentence in a model

And a few other functions:

    to_cnf           Convert to conjunctive normal form
    diff, simp       Symbolic differentiation and simplification
"""


import re


#
# Utility functions used by the code below
#______________________________________________________________________________

def isnumber(x):
    "Is x a number? We say it is if it has a __int__ method."
    return hasattr(x, '__int__')

def num_or_str(x):
    """The argument is a string; convert to a number if possible, or strip it.
    >>> num_or_str('42')
    42
    >>> num_or_str(' 42x ')
    '42x'
    """
    if isnumber(x): return x
    try:
        return int(x)
    except ValueError:
        try:
            return float(x)
        except ValueError:
            return str(x).strip()

def find_if(predicate, seq):
    """If there is an element of seq that satisfies predicate; return it.
    >>> find_if(callable, [3, min, max])
    <built-in function min>
    >>> find_if(callable, [1, 2, 3])
    """
    for x in seq:
        if predicate(x): return x
    return None

#
# Expr represents a symbolic mathematical expression
#______________________________________________________________________________

def expr(s):
    """Create an Expr representing a logic expression by parsing the input
    string. Symbols and numbers are automatically converted to Exprs.
    In addition you can use alternative spellings of these operators:
      'x ==> y'   parses as   (x >> y)    # Implication
      'x <== y'   parses as   (x << y)    # Reverse implication
      'x <=> y'   parses as   (x % y)     # Logical equivalence
      'x =/= y'   parses as   (x ^ y)     # Logical disequality (xor)
    But BE CAREFUL; precedence of implication is wrong. expr('P & Q ==> R & S')
    is ((P & (Q >> R)) & S); so you must use expr('(P & Q) ==> (R & S)').
    >>> expr('P <=> Q(1)')
    (P <=> Q(1))
    >>> expr('P & Q | ~R(x, F(x))')
    ((P & Q) | ~R(x, F(x)))

    WARNING: Uses eval()!  Do not use with unsanitized inputs!
    """
    if isinstance(s, Expr): return s
    if isnumber(s): return Expr(s)
    ## Replace the alternative spellings of operators with canonical spellings
    s = s.replace('==>', '>>').replace('<==', '<<')
    s = s.replace('<=>', '%').replace('=/=', '^')
    ## Replace a symbol or number, such as 'P' with 'Expr("P")'
    s = re.sub(r'([a-zA-Z0-9_.]+)', r'Expr("\1")', s)
    ## Now eval the string.  (A security hole; do not use with an adversary.)
    return eval(s, {'Expr':Expr})


class Expr:
    """A symbolic mathematical expression.  We use this class for logical
    expressions, and for terms within logical expressions. In general, an
    Expr has an op (operator) and a list of args.  The op can be:
      Null-ary (no args) op:
        A number, representing the number itself.  (e.g. Expr(42) => 42)
        A symbol, representing a variable or constant (e.g. Expr('F') => F)
      Unary (1 arg) op:
        '~', '-', representing NOT, negation (e.g. Expr('~', Expr('P')) => ~P)
      Binary (2 arg) op:
        '>>', '<<', representing forward and backward implication
        '+', '-', '*', '/', '**', representing arithmetic operators
        '<', '>', '>=', '<=', representing comparison operators
        '<=>', '^', representing logical equality and XOR
      N-ary (0 or more args) op:
        '&', '|', representing conjunction and disjunction
        A symbol, representing a function term or FOL proposition

    Exprs can be constructed with operator overloading: if x and y are Exprs,
    then so are x + y and x & y, etc.  Also, if F and x are Exprs, then so is
    F(x); it works by overloading the __call__ method of the Expr F.  Note
    that in the Expr that is created by F(x), the op is the str 'F', not the
    Expr F.   See http://www.python.org/doc/current/ref/specialnames.html
    to learn more about operator overloading in Python.

    WARNING: x == y and x != y are NOT Exprs.  The reason is that we want
    to write code that tests 'if x == y:' and if x == y were the same
    as Expr('==', x, y), then the result would always be true; not what a
    programmer would expect.  But we still need to form Exprs representing
    equalities and disequalities.  We concentrate on logical equality (or
    equivalence) and logical disequality (or XOR).  You have 3 choices:
        (1) Expr('<=>', x, y) and Expr('^', x, y)
            Note that ^ is bitwose XOR in Python (and Java and C++)
        (2) expr('x <=> y') and expr('x =/= y').
            See the doc string for the function expr.
        (3) (x % y) and (x ^ y).
            It is very ugly to have (x % y) mean (x <=> y), but we need
            SOME operator to make (2) work, and this seems the best choice.

    WARNING: if x is an Expr, then so is x + 1, because the int 1 gets
    coerced to an Expr by the constructor.  But 1 + x is an error, because
    1 doesn't know how to add an Expr.  (Adding an __radd__ method to Expr
    wouldn't help, because int.__add__ is still called first.) Therefore,
    you should use Expr(1) + x instead, or ONE + x, or expr('1 + x').
    """

    def __init__(self, op, *args):
        "Op is a string or number; args are Exprs (or are coerced to Exprs)."
        assert isinstance(op, str) or (isnumber(op) and not args)
        self.op = num_or_str(op)
        self.args = map(expr, args) ## Coerce args to Exprs

    def __call__(self, *args):
        """Self must be a symbol with no args, such as Expr('F').  Create a new
        Expr with 'F' as op and the args as arguments."""
        assert is_symbol(self.op) and not self.args
        return Expr(self.op, *args)

    def __repr__(self):
        "Show something like 'P' or 'P(x, y)', or '~P' or '(P | Q | R)'"
        if len(self.args) == 0: # Constant or proposition with arity 0
            return str(self.op)
        elif is_symbol(self.op): # Functional or Propositional operator
            return '%s(%s)' % (self.op, ', '.join(map(repr, self.args)))
        elif len(self.args) == 1: # Prefix operator
            return self.op + repr(self.args[0])
        else: # Infix operator
            return '(%s)' % (' '+self.op+' ').join(map(repr, self.args))

    def __eq__(self, other):
        """x and y are equal iff their ops and args are equal."""
        return (other is self) or (isinstance(other, Expr)
            and self.op == other.op and self.args == other.args)

    def __hash__(self):
        "Need a hash method so Exprs can live in dicts."
        return hash(self.op) ^ hash(tuple(self.args))

    def __str__(self):
        return repr(self)

    # See http://www.python.org/doc/current/lib/module-operator.html
    # Not implemented: not, abs, pos, concat, contains, *item, *slice
    def __lt__(self, other):
        return Expr('<',  self, other)
    def __le__(self, other):
        return Expr('<=', self, other)
    def __ge__(self, other):
        return Expr('>=', self, other)
    def __gt__(self, other):
        return Expr('>',  self, other)
    def __add__(self, other):
        return Expr('+',  self, other)
    def __sub__(self, other):
        return Expr('-',  self, other)
    def __and__(self, other):
        return Expr('&',  self, other)
    def __div__(self, other):
        return Expr('/',  self, other)
    def __truediv__(self, other):
        return Expr('/',  self, other)
    def __invert__(self):
        return Expr('~',  self)
    def __lshift__(self, other):
        return Expr('<<', self, other)
    def __rshift__(self, other):
        return Expr('>>', self, other)
    def __mul__(self, other):
        return Expr('*',  self, other)
    def __neg__(self):
        return Expr('-',  self)
    def __or__(self, other):
        return Expr('|',  self, other)
    def __pow__(self, other):
        return Expr('**', self, other)
    def __xor__(self, other):
        return Expr('^',  self, other)
    def __mod__(self, other):
        return Expr('<=>',  self, other) ## (x % y)


def is_symbol(s):
    "A string s is a symbol if it starts with an alphabetic char."
    return isinstance(s, str) and s[0].isalpha()

def is_var_symbol(s):
    "A logic variable symbol is an initial-lowercase string."
    return is_symbol(s) and s[0].islower()

def is_prop_symbol(s):
    """A proposition logic symbol is an initial-uppercase string other than
    TRUE or FALSE."""
    return is_symbol(s) and s[0].isupper() and s != 'TRUE' and s != 'FALSE'

def is_positive(s):
    """s is an unnegated logical expression
    >>> is_positive(expr('F(A, B)'))
    True
    >>> is_positive(expr('~F(A, B)'))
    False
    """
    return s.op != '~'

def is_negative(s):
    """s is a negated logical expression
    >>> is_negative(expr('F(A, B)'))
    False
    >>> is_negative(expr('~F(A, B)'))
    True
    """
    return s.op == '~'

def is_literal(s):
    """s is a FOL literal
    >>> is_literal(expr('~F(A, B)'))
    True
    >>> is_literal(expr('F(A, B)'))
    True
    >>> is_literal(expr('F(A, B) & G(B, C)'))
    False
    """
    return is_symbol(s.op) or (s.op == '~' and is_literal(s.args[0]))

def literals(s):
    """returns the list of literals of logical expression s.
    >>> literals(expr('F(A, B)'))
    [F(A, B)]
    >>> literals(expr('~F(A, B)'))
    [~F(A, B)]
    >>> literals(expr('(F(A, B) & G(B, C)) ==> R(A, C)'))
    [F(A, B), G(B, C), R(A, C)]
    """
    op = s.op
    if op in set(['&', '|', '<<', '>>', '%', '^']):
        result = []
        for arg in s.args:
            result.extend(literals(arg))
        return result
    elif is_literal(s):
        return [s]
    else:
        return []

def variables(s):
    """returns the set of variables in logical expression s.
    >>> ppset(variables(F(x, A, y)))
    set([x, y])
    >>> ppset(variables(expr('F(x, x) & G(x, y) & H(y, z) & R(A, z, z)')))
    set([x, y, z])
    """
    if is_literal(s):
        return set([v for v in s.args if is_variable(v)])
    else:
        lvars = set([])
        for lit in literals(s):
            lvars = lvars.union(variables(lit))
        return lvars

## Useful constant Exprs used in examples and code:
TRUE, FALSE, ZERO, ONE, TWO = map(Expr, ['TRUE', 'FALSE', 0, 1, 2])

#______________________________________________________________________________

def prop_symbols(x):
    "Return a list of all propositional symbols in x."
    if not isinstance(x, Expr):
        return []
    elif is_prop_symbol(x.op):
        return [x]
    else:
        s = set(())
        for arg in x.args:
            for symbol in prop_symbols(arg):
                s.add(symbol)
        return list(s)

def pl_true(exp, model={}):
    """Return True if the propositional logic expression is true in the model,
    and False if it is false. If the model does not specify the value for
    every proposition, this may return None to indicate 'not obvious';
    this may happen even when the expression is tautological."""
    op, args = exp.op, exp.args
    if exp == TRUE:
        return True
    elif exp == FALSE:
        return False
    elif is_prop_symbol(op):
        return model.get(exp)
    elif op == '~':
        p = pl_true(args[0], model)
        if p == None: return None
        else: return not p
    elif op == '|':
        result = False
        for arg in args:
            p = pl_true(arg, model)
            if p == True: return True
            if p == None: result = None
        return result
    elif op == '&':
        result = True
        for arg in args:
            p = pl_true(arg, model)
            if p == False: return False
            if p == None: result = None
        return result
    p, q = args
    if op == '>>':
        return pl_true(~p | q, model)
    elif op == '<<':
        return pl_true(p | ~q, model)
    pt = pl_true(p, model)
    if pt == None: return None
    qt = pl_true(q, model)
    if qt == None: return None
    if op == '<=>':
        return pt == qt
    elif op == '^':
        return pt != qt
    else:
        raise ValueError, "illegal operator in logic expression" + str(exp)

#______________________________________________________________________________

## Convert to Conjunctive Normal Form (CNF)

def to_cnf(s):
    """Convert a propositional logical sentence s to conjunctive normal form.
    That is, of the form ((A | ~B | ...) & (B | C | ...) & ...) [p. 215]
    >>> to_cnf("~(B|C)")
    (~B & ~C)
    >>> to_cnf("B <=> (P1|P2)")
    ((~P1 | B) & (~P2 | B) & (P1 | P2 | ~B))
    >>> to_cnf("a | (b & c) | d")
    ((b | a | d) & (c | a | d))
    >>> to_cnf("A & (B | (D & E))")
    (A & (D | B) & (E | B))

    WARNING: Passes through expr(), which uses eval() - Do not use with
             unsanitized inputs!
    """
    if isinstance(s, str): s = expr(s)
    s = eliminate_implications(s) # Steps 1, 2 from p. 215
    s = move_not_inwards(s) # Step 3
    return distribute_and_over_or(s) # Step 4

def eliminate_implications(s):
    """Change >>, <<, and <=> into &, |, and ~. That is, return an Expr
    that is equivalent to s, but has only &, |, and ~ as logical operators.
    >>> eliminate_implications(A >> (~B << C))
    ((~B | ~C) | ~A)
    """
    if not s.args or is_symbol(s.op): return s     ## (Atoms are unchanged.)
    args = map(eliminate_implications, s.args)
    a, b = args[0], args[-1]
    if s.op == '>>':
        return (b | ~a)
    elif s.op == '<<':
        return (a | ~b)
    elif s.op == '<=>':
        return (a | ~b) & (b | ~a)
    else:
        return Expr(s.op, *args)

def move_not_inwards(s):
    """Rewrite sentence s by moving negation sign inward.
    >>> move_not_inwards(~(A | B))
    (~A & ~B)
    >>> move_not_inwards(~(A & B))
    (~A | ~B)
    >>> move_not_inwards(~(~(A | ~B) | ~~C))
    ((A | ~B) & ~C)
    """
    if s.op == '~':
        NOT = lambda b: move_not_inwards(~b)
        a = s.args[0]
        if a.op == '~':
            return move_not_inwards(a.args[0]) # ~~A ==> A
        if a.op == '&':
            return NaryExpr('|', *map(NOT, a.args))
        if a.op == '|':
            return NaryExpr('&', *map(NOT, a.args))
        return s
    elif is_symbol(s.op) or not s.args:
        return s
    else:
        return Expr(s.op, *map(move_not_inwards, s.args))

def distribute_and_over_or(s):
    """Given a sentence s consisting of conjunctions and disjunctions
    of literals, return an equivalent sentence in CNF.
    >>> distribute_and_over_or((A & B) | C)
    ((A | C) & (B | C))
    """
    if s.op == '|':
        s = NaryExpr('|', *s.args)
        if len(s.args) == 0:
            return FALSE
        if len(s.args) == 1:
            return distribute_and_over_or(s.args[0])
        conj = find_if((lambda d: d.op == '&'), s.args)
        if not conj:
            return NaryExpr(s.op, *s.args)
        others = [a for a in s.args if a is not conj]
        if len(others) == 1:
            rest = others[0]
        else:
            rest = NaryExpr('|', *others)
        return NaryExpr('&', *map(distribute_and_over_or,
                                  [(c|rest) for c in conj.args]))
    elif s.op == '&':
        return NaryExpr('&', *map(distribute_and_over_or, s.args))
    else:
        return s

_NaryExprTable = {'&':TRUE, '|':FALSE, '+':ZERO, '*':ONE}

def NaryExpr(op, *args):
    """Create an Expr, but with an nary, associative op, so we can promote
    nested instances of the same op up to the top level.
    >>> NaryExpr('&', (A&B),(B|C),(B&C))
    (A & B & (B | C) & B & C)
    """
    arglist = []
    for arg in args:
        if arg.op == op: arglist.extend(arg.args)
        else: arglist.append(arg)
    if len(args) == 1:
        return args[0]
    elif len(args) == 0:
        return _NaryExprTable[op]
    else:
        return Expr(op, *arglist)

def conjuncts(s):
    """Return a list of the conjuncts in the sentence s.
    >>> conjuncts(A & B)
    [A, B]
    >>> conjuncts(A | B)
    [(A | B)]
    """
    if isinstance(s, Expr) and s.op == '&':
        return s.args
    else:
        return [s]

def disjuncts(s):
    """Return a list of the disjuncts in the sentence s.
    >>> disjuncts(A | B)
    [A, B]
    >>> disjuncts(A & B)
    [(A & B)]
    """
    if isinstance(s, Expr) and s.op == '|':
        return s.args
    else:
        return [s]

#______________________________________________________________________________

# DPLL-Satisfiable [Fig. 7.16]

def find_pure_symbol(symbols, unknown_clauses):
    """Find a symbol and its value if it appears only as a positive literal
    (or only as a negative) in clauses.
    >>> find_pure_symbol([A, B, C], [A|~B,~B|~C,C|A])
    (A, True)
    """
    for s in symbols:
        found_pos, found_neg = False, False
        for c in unknown_clauses:
            if not found_pos and s in disjuncts(c):
                found_pos = True
            if not found_neg and ~s in disjuncts(c):
                found_neg = True
        if found_pos != found_neg:
            return s, found_pos
    return None, None

def find_unit_clause(clauses, model):
    """A unit clause has only 1 variable that is not bound in the model.
    >>> find_unit_clause([A|B|C, B|~C, A|~B], {A:True})
    (B, False)
    """
    for clause in clauses:
        num_not_in_model = 0
        for literal in disjuncts(clause):
            sym = literal_symbol(literal)
            if sym not in model:
                num_not_in_model += 1
                P, value = sym, (literal.op != '~')
        if num_not_in_model == 1:
            return P, value
    return None, None


def literal_symbol(literal):
    """The symbol in this literal (without the negation).
    >>> literal_symbol(P)
    P
    >>> literal_symbol(~P)
    P
    """
    if literal.op == '~':
        return literal.args[0]
    else:
        return literal

#______________________________________________________________________________

def is_variable(x):
    "A variable is an Expr with no args and a lowercase symbol as the op."
    return isinstance(x, Expr) and not x.args and is_var_symbol(x.op)

def occur_check(var, x, s):
    """Return true if variable var occurs anywhere in x
    (or in subst(s, x), if s has a binding for x)."""

    if var == x:
        return True
    elif is_variable(x) and x in s:
        return occur_check(var, s[x], s) # fixed
    # What else might x be?  an Expr, a list, a string?
    elif isinstance(x, Expr):
        # Compare operator and arguments
        return (occur_check(var, x.op, s) or
                occur_check(var, x.args, s))
    elif isinstance(x, list) and x != []:
        # Compare first and rest
        return (occur_check(var, x[0], s) or
                occur_check(var, x[1:], s))
    else:
        # A variable cannot occur in a string
        return False

    #elif isinstance(x, Expr):
    #    return var.op == x.op or occur_check(var, x.args)
    #elif not isinstance(x, str) and issequence(x):
    #    for xi in x:
    #        if occur_check(var, xi): return True
    #return False

def extend(s, var, val):
    """Copy the substitution s and extend it by setting var to val;
    return copy.

    >>> ppsubst(extend({x: 1}, y, 2))
    {x: 1, y: 2}
    """
    s2 = s.copy()
    s2[var] = val
    return s2

def subst(s, x):
    """Substitute the substitution s into the expression x.
    >>> subst({x: 42, y:0}, F(x) + y)
    (F(42) + 0)
    """
    if isinstance(x, list):
        return [subst(s, xi) for xi in x]
    elif isinstance(x, tuple):
        return tuple([subst(s, xi) for xi in x])
    elif not isinstance(x, Expr):
        return x
    elif is_var_symbol(x.op):
        return s.get(x, x)
    else:
        return Expr(x.op, *[subst(s, arg) for arg in x.args])

#______________________________________________________________________________


# Example application (not in the book).
# You can use the Expr class to do symbolic differentiation.  This used to be
# a part of AI; now it is considered a separate field, Symbolic Algebra.

def diff(y, x):
    """Return the symbolic derivative, dy/dx, as an Expr.
    However, you probably want to simplify the results with simp.
    >>> diff(x * x, x)
    ((x * 1) + (x * 1))
    >>> simp(diff(x * x, x))
    (2 * x)
    """
    if y == x: return ONE
    elif not y.args: return ZERO
    else:
        u, op, v = y.args[0], y.op, y.args[-1]
        if op == '+':
            return diff(u, x) + diff(v, x)
        elif op == '-' and len(y.args) == 1:
            return -diff(u, x)
        elif op == '-':
            return diff(u, x) - diff(v, x)
        elif op == '*':
            return u * diff(v, x) + v * diff(u, x)
        elif op == '/':
            return (v*diff(u, x) - u*diff(v, x)) / (v * v)
        elif op == '**' and isnumber(x.op):
            return (v * u ** (v - 1) * diff(u, x))
        elif op == '**':
            return (v * u ** (v - 1) * diff(u, x)
                      + u ** v * Expr('log')(u) * diff(v, x))
        elif op == 'log':
            return diff(u, x) / u
        else: raise ValueError("Unknown op: %s in diff(%s, %s)" % (op, y, x))

def simp(x):
    if not x.args: return x
    args = map(simp, x.args)
    u, op, v = args[0], x.op, args[-1]
    if op == '+':
        if v == ZERO:
            return u
        if u == ZERO:
            return v
        if u == v:
            return TWO * u
        if u == -v or v == -u:
            return ZERO
    elif op == '-' and len(args) == 1:
        if u.op == '-' and len(u.args) == 1:
            return u.args[0] ## --y ==> y
    elif op == '-':
        if v == ZERO:
            return u
        if u == ZERO:
            return -v
        if u == v:
            return ZERO
        if u == -v or v == -u:
            return ZERO
    elif op == '*':
        if u == ZERO or v == ZERO:
            return ZERO
        if u == ONE:
            return v
        if v == ONE:
            return u
        if u == v:
            return u ** 2
    elif op == '/':
        if u == ZERO:
            return ZERO
        if v == ZERO:
            return Expr('Undefined')
        if u == v:
            return ONE
        if u == -v or v == -u:
            return ZERO
    elif op == '**':
        if u == ZERO:
            return ZERO
        if v == ZERO:
            return ONE
        if u == ONE:
            return ONE
        if v == ONE:
            return u
    elif op == 'log':
        if u == ONE:
            return ZERO
    else: raise ValueError("Unknown op: " + op)
    ## If we fall through to here, we can not simplify further
    return Expr(op, *args)

#_______________________________________________________________________________

# Utilities for doctest cases
# These functions print their arguments in a standard order
# to compensate for the random order in the standard representation

def pretty(x):
    t = type(x)
    if t == dict:
        return pretty_dict(x)
    elif t == set:
        return pretty_set(x)

def pretty_dict(ugly_dict):
    """Print the dictionary ugly_dict.

    Prints a string representation of the dictionary
    with keys in sorted order according to their string
    representation: {a: A, d: D, ...}.
    >>> pretty_dict({'m': 'M', 'a': 'A', 'r': 'R', 'k': 'K'})
    "{'a': 'A', 'k': 'K', 'm': 'M', 'r': 'R'}"
    >>> pretty_dict({z: C, y: B, x: A})
    '{x: A, y: B, z: C}'
    """

    def format(k, v):
        """Return formatted key, value pairs."""
        return "%s: %s" % (repr(k), repr(v))

    ugly_dictitems = ugly_dict.items()
    ugly_dictitems.sort(key=str)
    k, v = ugly_dictitems[0]
    ugly_dictpairs = format(k, v)
    for (k, v) in ugly_dictitems[1:]:
        ugly_dictpairs += (', ' + format(k, v))
    return '{%s}' % ugly_dictpairs

def pretty_set(s):
    """Print the set s.

    >>> pretty_set(set(['A', 'Q', 'F', 'K', 'Y', 'B']))
    "set(['A', 'B', 'F', 'K', 'Q', 'Y'])"
    >>> pretty_set(set([z, y, x]))
    'set([x, y, z])'
    """

    slist = list(s)
    slist.sort(key=str)
    return 'set(%s)' % slist

def pp(x):
    print(pretty(x))

def ppsubst(s):
    """Pretty-print substitution s"""
    ppdict(s)

def ppdict(d):
    print(pretty_dict(d))

def ppset(s):
    print(pretty_set(s))
