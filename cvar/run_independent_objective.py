#!/usr/bin/env python3
from cfg import sizes
from runTrial import runTrial
from makeFiles import makeFiles

name = 'independent'
kind = '1percent'
param_type = 'objective'
dir1 = name+'_'+param_type
# CHECK CFG NPYNAMES
size = 'large'
train_size = 'small'
n_trains = 11
risk_measure = 'cvar'
# Ulist = [20000,10000,2000,500,100,50]
Ulist = [10000,5000,2000,1000,500,200,150,100,50,45,35,20,15,5]

if kind == '1percent':
    cvar = 0.1
    alpha = 0.99
else:
    cvar = 0.003
    alpha = 0.999

in_dict = {
    'Ulist':Ulist,
    'train_size':train_size,
    'sizes':{
        'normal':sizes[train_size]['n'],
        'extreme':sizes[train_size]['e']
        },
    'n_trains':n_trains,
    'risk-measure':risk_measure,
    'cvar':cvar,
    'alpha':alpha,
    'kind':kind,
    'size':size,
    'name':name,
    'parameter-type':param_type,
    'dir':dir1+'/',
    'Sdir':dir1+'/scenarios/',
    'Rdir':dir1+'/results/'
    }

data = {
        'memory':{
            'train':'22', # max 65
            'nTest':'3',
            'eTest':'18',
            'extremeTest':'10',
            'processTrain':'1',
            'processTest':'1'
            }
    }

makeFiles(dir1,data,in_dict)

runTrial(in_dict)
