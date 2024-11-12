#!/usr/bin/env python3
import sys
from methods_setup import makeTrainData

# size = sys.argv[1]
# name = sys.argv[2]

data = {
        'tiny':{
            'unconditional':{
                'n':5,
                'e':5
                },
            'proposal':{
                'n':5,
                'e':5
                }
            },
        'mid':{
            'proposal':{
                'n':11,
                'e':11
                },
            'unconditional':{
                'n':11,
                'e':11
                },
            'independent':{
                'n':11,
                'e':11
                },
            'base':{
                'n':21,
                'e':0
                }
            },
        'small':{
            'proposal':{
                'n':21,
                'e':21
                },
            'unconditional':{
                'n':21,
                'e':21
                },
            'independent':{
                'n':21,
                'e':21
                },
            'base':{
                'n':42,
                'e':0
                }
            },
        'medium':{
            'proposal':{
                'n':42,
                'e':42
                },
            'unconditional':{
                'n':42,
                'e':42
                },
            'independent':{
                'n':42,
                'e':42
                },
            'base':{
                'n':42,
                'e':0
                }
            },
        'large':{
            'proposal':{
                'n':30,
                'e':130
                },
            'unconditional':{
                'n':30,
                'e':130
                },
            'independent':{
                'n':30,
                'e':130
                },
            'base':{
                'n':84,
                'e':0
                }
            },
        'huge':{
            'unconditional':{
                'n':30,
                'e':200
                },
            'proposal':{
                'n':30,
                'e':130
                },
            'base':{
                'n':160,
                'e':0
                }
            }
        }


for size in ['tiny','mid','small']:#data:
    for name in data[size]:
        # if name == 'unconditional':# (size,name) in to_do:
            if name in ['base','unconditional']:
                alpha = 0
            else:
                alpha = 0.99
            D = {'n_trains':15,
                 'sizes':{'normal': data[size][name]['n'],
                          'extreme': data[size][name]['e']
                          },
                 'name':name,
                 'alpha':alpha,
                 'kind':'primary',
                 'npseed':1,
                 'randomseed':1,
                 'Sdir':'train-scenarios/'+size+'/'+name+str(alpha)
                }

            makeTrainData(D)
