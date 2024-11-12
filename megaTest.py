#!/usr/bin/env python3
import sys
from methods_pickle import loadPickle, savePickle

S = loadPickle('S')
G = loadPickle('G')
sol = sys.argv[1]

z = {}
y = {}
# parse .sol file into z and y
with open(sol) as f:
    for l in f:
        l = l.replace('[', ', ')
        l = l.replace('] ',', ')
        l = l.replace('\n','')
        if l[0] == 'z':
            a = l.split(', ')
            z[a[1]] = float(a[2])
        elif l[0] == 'y':
            l = l.replace(', ',',')
            a = l.split(',')
            y[(a[1],int(a[2]))] = float(a[3])

# evaluate shed
results = {key: None for key in S.keys()}
for key in S.keys():
    s = S[key]
    capacity = sum( s['cap'][u] * z[u] for u in G['zuid']
                   ) + sum( s['cap'][u] for u in G['uid'] if u not in G['zuid']
                   ) + sum( y[g, r]*s['factor'][g, r][1] for (g, r) in G['capcost_nrel'].keys())
    shed = max(0,s['load'] - capacity)
    results[key] = {'shed':shed}

savePickle('',sol+'_results',results)
