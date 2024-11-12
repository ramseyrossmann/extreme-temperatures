#!/usr/bin/env python3
from cfg import sizes
from runTrial import runTrial

name = 'proposal'
param_type = 'constraint'
dir1 = name+'_'+param_type
# CHECK CFG NPYNAMES
size = 'small' # test size
train_size = 'tiny'
n_trains = 3
risk_measure = 'cvar'
Ulist =  [100]#0,100,1000,5000,10000]
cvar = 0.1
alpha = 0.99

in_dict = {
    'runHere': True,
    'Ulist':Ulist,
    'train_size':train_size,
    'sizes':{
        'normal':sizes[train_size]['n'],
        'extreme':sizes[train_size]['e']
        },
    'n_trains':n_trains,
    'risk-measure':risk_measure,
    'cvar':cvar,
    'dpi':200,
    'alpha':alpha,
    'size':size,
    'name':name,
    'parameter-type':param_type,
    'dir':dir1+'/',
    'Sdir':'train-scenarios/'+train_size+'/'+name+str(alpha)+'/',
    'Rdir':dir1+'/results/',
    'cf_dict':{'Offshore_Wind':1,
               'Onshore_Wind':1,
               'SolarDistUtil':1,
               'SolarUtil':1}
    }

m = runTrial(in_dict)
