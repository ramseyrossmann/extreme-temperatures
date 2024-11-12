#!/usr/bin/env python3
from cfg import sizes
from runTrial import runTrial
from makeFiles import makeFiles

name = 'independent'
kind = '1percent'
param_type = 'constraint'
dir1 = name+'_'+param_type
# CHECK CFG NPYNAMES
size = 'large' # test size
train_size = 'mid'
mem = 18
n_trains = 15
risk_measure = 'cvar'

Ulist = [0,10,50,100,250,500,1000,1500,3000,20000]

if True:# kind == '1percent':
    cvar = 0.1
    alpha = 0.99
# else:
    # cvar = 0.003
    # alpha = 0.999

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
