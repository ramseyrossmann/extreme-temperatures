#!/usr/bin/env python3
from cfg import sizes
from runTrial import runTrial
from makeFiles import makeFiles

name = 'unconditional'
kind = 'primary'
param_type = 'objective'
dir1 = name+'_'+param_type
# CHECK CFG NPYNAMES
size = 'small'
train_size = 'tiny'
n_trains = 3
risk_measure = 'cvar'
# Ulist = [10000,2000,1000,500,200,150,100,50,45,35,20,15,5]
Ulist = [2000,50,1]

cvar = 0.0001
alpha = 0





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
    'Rdir':dir1+'/results/',
    'temperature-dependent':False,
    }

data = {
        'memory':{
            'train':'4',# then 100
            'nTest':'3',
            'eTest':'18',
            'extremeTest':'10',
            'processTrain':'1',
            'processTest':'1'
            }
    }

makeFiles(dir1,data,in_dict)

runTrial(in_dict)