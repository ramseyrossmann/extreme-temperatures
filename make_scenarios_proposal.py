#!/usr/bin/env python3
import sys
from runTrial import runTrial
from makeFiles import makeFiles

name = sys.argv[2]
kind = 'primary'
param_type = 'objective'
dir1 = 'train-scenarios/'+size+'/'name
# CHECK CFG NPYNAMES
n_trains = 15

n = 30
e = 130

in_dict = {
    'sizes':{
        'normal':n,
        'extreme':e
        },
    'n_trains':n_trains,
    'kind':kind,
    'name':name,
    'Sdir':dir1+'/scenarios/',
    }


runTrial(in_dict)
