
## Output some significant name variants to check performances of create_normalized_name

from invenio.dbquery import run_sql
from invenio.bibauthorid_name_utils import *
from itertools import *
from collections import *
import regex as re

all_names_100 = run_sql("select value from bib10x where tag='100__a'")
print 'Found ', len(all_names_100), ' 100__a'
all_names_700 = run_sql("select value from bib70x where tag='700__a'")
print 'Found ', len(all_names_700), ' 700__a'

all_names = set(x[0] for x in chain(all_names_100, all_names_700) if x[0])
print "Will process a set of ", len(all_names)

categories = defaultdict(dict)

for i, name in enumerate(all_names):
    try:
        surname, names = name.split(',', 1)
    except ValueError:
        surname = name
        names = None
    csur = re.sub( "[^\p{L}]" ," ",surname)

    if names:
        name_n = len(names.split(' '))
        name_d = len(names.split('.'))
        name_l = 0
        nameidx = (name_n, name_d)
    else:
        nameidx = (0,0)

    if surname.count(' ')>0:
        suridx = tuple(len(x) for x in surname.split(' '))
        if len(suridx) > 2:
            suridx = (suridx[0:2], 1)
    else:
        suridx = (1,)

    try:
        _ = categories[suridx][nameidx]
    except KeyError:
        categories[suridx][nameidx] = name

unrolled = list()

for k,v in categories.iteritems():
    for kk,vv in v.iteritems():
        unrolled.append(vv)

unrolled = filter(lambda x: len(x)<20, unrolled)

failed = list()
print '\n'
for n in sorted(unrolled):
    try:
        print '"'+n+'" --> "'+ create_normalized_name(split_name_parts(n))+ '"'
    except:
        failed.append(n)

print "Failed: ", failed
