# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 14:43:46 2014

@author: scarli
"""
import sys
from itertools import groupby
import pprint

f = open(sys.argv[1])
l = f.readlines()
l = [[y.strip() for y in x.split('\t')] for x in l]
l = [(x[0], int(x[1]), float(x[2]), x[3], int(x[4])) for x in l]
l.sort(key = lambda x: (x[0], x[1]))

g = groupby(l, lambda x:(x[0], x[1]))
cumul_time = list()
called_by = list()
for group in g:
    gr = list(group[1])
    calls = [x[2] for x in gr]
    cumul_time.append((group[0], sum(calls), len(calls)))
    gr.sort(key = lambda x: (x[3],x[4]))

    callers_list = list()
    callers = groupby(gr, lambda x: (x[3],x[4]))
    for caller in callers:
        callers_list.append((caller[0], len(list(caller[1]))))
    called_by.append((group[0],callers_list))

cumul_time.sort(key=lambda x: x[1], reverse=True)
print "\nCumulative times:"
pprint.pprint(cumul_time)

print "\nCallers:"
for c in called_by:
    print '\n', c[0], ' called  by: '
    for e in sorted(c[1], key=lambda x: x[1]):
        print '\t', e
