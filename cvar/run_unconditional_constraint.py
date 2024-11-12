#!/usr/bin/env python3
from cfg import sizes
from runTrial import runTrial
from makeFiles import makeFiles

name = 'unconditional'
kind = 'primary'
param_type = 'constraint'
dir1 = name+'_'+param_type
# CHECK CFG NPYNAMES
size = 'large'
train_size = 'mid'
mem = 18
n_trains = 5
risk_measure = 'cvar'

Ulist = [0,20,500,1000,1500,3000,4500,7000,12000,20000]

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
    'cf_dict':{'Offshore_Wind':1,
               'Onshore_Wind':1,
               'SolarDistUtil':1,
               'SolarUtil':1}
    }

data = {
        'memory':{
            'train':str(mem),
            }
    }

makeFiles(dir1,data,in_dict)

runTrial(in_dict)
