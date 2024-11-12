#!/usr/bin/env python3
from cfg import sizes
from runTrial import runTrial
from makeFiles import makeFiles

name = 'base'
kind = 'primary'
param_type = 'objective'
dir1 = name+'_'+param_type
# CHECK CFG NPYNAMES
size = 'large'
train_size = 'mid'
mem = 25
n_trains = 15
risk_measure = 'cvar'

Ulist = [50000,5000,3000,1500,400,250,175,75,50,35]

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
    'cf_dict':{'Offshore_Wind':0,
               'Onshore_Wind':0,
               'SolarDistUtil':0,
               'SolarUtil':0}
    }

data = {
        'memory':{
            'train':str(mem),
            }
    }

makeFiles(dir1,data,in_dict)

runTrial(in_dict)
