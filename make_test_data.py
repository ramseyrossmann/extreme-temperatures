#!/usr/bin/env python3
import sys
from methods_setup import makeTestData

size = sys.argv[1]

if size == 'small':
    n = 8
    e = 8
    name = 'test'
elif size == 'large_e':
    n = 105
    e = 521
    name = 'test_e'
elif size == 'large':
    n = 105
    e = 521
    name = 'test'

D = {'n_trains':1, # to make one Se and one Sn
     'size':size,
     'alpha':0,
     'sizes':{'normal': n,
              'extreme': 1
              },
     'name':name,
     'kind':'primary',
     'npseed':100000,
     'randomseed':100000,
        }

# makes normal test data
makeTestData(D)

# makes extreme test data
D['sizes']['normal'] = 1
D['sizes']['extreme'] = e
makeTestData(D)
