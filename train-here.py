#!/usr/bin/env python3
import sys
from methods_run import Train
from methods_pickle import loadPickle

i = sys.argv[1]
U = sys.argv[2]
name = sys.argv[3]
dir = sys.argv[4]
P = loadPickle(dir+name+'scenarios/S'+str(i)+'/U'+str(U)+'/P')
# P['relocate'] = True
Train({
    'i':i,
    'U':U,
    'name':name,
    # 'sol':,
    # 'caps':
    'S':loadPickle('train-scenarios/mid/proposal0.99/S'+str(i)+'/S'),
    'P':P,
    'G':loadPickle('pickles/G'),
    'L':loadPickle('pickles/L'),
    'fips':loadPickle('pickles/fips_midwest')
    })
