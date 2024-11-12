#!/usr/bin/env python3
import sys
from cfg import sizes
from methods_setup import makeTrainData
# from makeFiles import makeFiles

name = sys.argv[1]
size = sys.argv[2]
n_trains = int(sys.argv[3])
kind = 'primary'
nametagmap = {
    'base': '0',
    'unconditional':'0',
    'proposal': '0.99',
    'independent':'0.99'
}
Sdir = 'train-scenarios/'+size+'/'+name+nametagmap[name]+'/'
# CHECK cfg.py npynames

in_dict = {
    'sizes':{
        'normal':sizes[size]['n'],
        'extreme':sizes[size]['e']
        },
    'n_trains':n_trains,
    'kind':kind,
    'name':name,
    'Sdir':Sdir,
    }

makeTrainData(in_dict)
