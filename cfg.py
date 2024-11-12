#!/usr/bin/env python3
import pickle
import numpy as np
dpi = 300
testTime = dict()
trialTime = dict()
trainTime = dict()
retestTime = dict()

with open('pickles/fips_wi.pkl','rb') as f:
    fipswi = pickle.load(f)

with open('pickles/fips_wi_dict.pkl','rb') as f:
    fipswi_dict = pickle.load(f)

with open('pickles/fips6.pkl','rb') as f:
    fips6 = pickle.load(f)

with open('pickles/fips6_dict.pkl','rb') as f:
    fips6_dict = pickle.load(f)

with open('pickles/G.pkl','rb') as f:
    G = pickle.load(f)

# with open('pickles/L_old.pkl','rb') as f:
with open('pickles/L.pkl','rb') as f:
    L = pickle.load(f)

# with open('pickles/quantiles.pkl','rb') as f:
    # quants = pickle.load(f)


sizes = {
    'tiny':{
        'n':5,
        'e':5
        },
    'mid':{
        'n':11,
        'e':11,
        },
    'small':{
        'n':21,
        'e':21,
         },
    'medium':{
        'n':42,
        'e':42
        },
    'large':{
        'n':30,
        'e':130
        },
    'huge':{
        'n':30,
        'e':200
        }
    }

# unconditional forced outage rates from Resource Adequacy Implicatesion... Murphy, Lavin, Apt
FOR = {
       'CC': 0.033,
       'CT': 0.028,
       'DS': 0.109,
       'HD': 0.024,
       'NU': 0.026,
       'ST': 0.094
       }

validNames = ['test','base','proposal','unconditional','independent'] # ,'test_e']
alphas = [0,0.99]#,0.999]
params = {
    'hours':12,
    'months':4,
    'test':None,#{'normal':2093},
    'proposal':None,
    'unconditional':None,#{'normal':4277},
    'independent':None#{'normal':6370}
    }
# sim counts set below npyNames

tempDir = 'temp-and-load-sims/'
normalLoads = 'spatial_load_70years_205k.npy'
normalTemps = 'spatial_simulations_70years_205k.npy'
npyNames = {
    # 'wi':{
    #     'independent':{
    #         'extreme':{
    #             'loads':None,
    #             'temps':None
    #                 },
    #         'normal':{
    #             'loads':None,
    #             'temps':None
    #                 }
    #             },
    #     'spatial':{
    #         'extreme':{
    #             'loads':'load_wi_extreme_ridge0.1_c8_center_4month_nolow^2c.npy',
    #             'temps':'extreme_simulations_wi_spatial_shifted.npy'
    #             },
    #         'normal':{
    #             'loads':'load_wi_ridge0.1_c8_center_4month_nolow^2c.npy',
    #             'temps':'temp_counties_wi_4d_shifted.npy'
    #                 }
    #             }
    #         },
    'midwest':{
        # 'independent':{
        #     'extreme':{
        #         99:{
        #             'loads':tempDir+'extreme_load_sixstate_ind_p99.npy',
        #             'temps':tempDir+'extreme_simulations_sixstate_ind_p99.npy'
        #             },
        #         999:{
        #             'loads':tempDir+'extreme_load_sixstate_ind_p999.npy',
        #             'temps':tempDir+'extreme_simulations_sixstate_ind_p999.npy'
        #             }
        #         },
        #     'normal':{
        #         'loads':None,
        #         'temps':None
        #         }
        #     },
        # 'spatial':{
        #     'extreme':{
        #         99:{
        #             'loads':tempDir+'extreme_load_sixstate_spatial_p99.npy',
        #             'temps':tempDir+'extreme_simulations_sixstate_spatial_p99.npy'
        #             },
        #         999:{
        #             'loads':tempDir+'extreme_load_sixstate_spatial_p999.npy',
        #             'temps':tempDir+'extreme_simulations_sixstate_spatial_p999.npy'
        #             },
        #         },
        #     'normal':{
        #         'loads':tempDir+normalLoads,
        #         'temps':tempDir+normalTemps
        #             }
        #         },
        'test':{
            0:{
                'extreme':{
                    'loads':tempDir+'spatial_load_70years_100k.npy',
                    'temps':tempDir+'spatial_simulations_70years_100k.npy'
                    },
                'normal':{
                    'loads':tempDir+'spatial_load_70years_100k.npy',
                    'temps':tempDir+'spatial_simulations_70years_100k.npy'
                        }
                }
            },
        # 'test_e':{0.01:{
        #     'extreme':{
        #         'loads':tempDir+'extreme_load_fivestate_spatial_p99.npy',
        #         'temps':tempDir+'extreme_simulations_fivestate_spatial_p99.npy'
        #         },
        #     'normal':{
        #         'loads':tempDir+'spatial_load_70years_100k.npy',
        #         'temps':tempDir+'spatial_simulations_70years_100k.npy'
        #             }
        #         }},
        'proposal':{
            0.99:{
                'extreme':{
                    'loads':tempDir+'extreme_load_fullaverageextreme_spatial_p99.npy',
                    'temps':tempDir+'extreme_simulations_fullaverageextreme_spatial_p99.npy'
                    },
                'normal':{
                    'loads':tempDir+normalLoads,
                    'temps':tempDir+normalTemps
                    }
                },
            # 0.999:{
            #     'extreme':{
            #         'loads':tempDir+'extreme_load_fullaverageextreme_spatial_p999.npy',
            #         'temps':tempDir+'extreme_simulations_fullaverageextreme_spatial_p999.npy'
            #         },
            #     'normal':{
            #         'loads':tempDir+normalLoads,
            #         'temps':tempDir+normalTemps
            #         }
            #     }
            },
        'unconditional':{
            0:{
                'extreme':{
                    'loads':tempDir+normalLoads,
                    'temps':tempDir+normalTemps
                    },
                'normal':{
                    'loads':tempDir+normalLoads,
                    'temps':tempDir+normalTemps
                        }
                }
            },
        'base':{
            0:{
                'extreme':{
                    'loads':tempDir+normalLoads,
                    'temps':tempDir+normalTemps
                    },
                'normal':{
                    'loads':tempDir+normalLoads,
                    'temps':tempDir+normalTemps
                        }
                }
            },
        'independent':{
            0.99:{
                'extreme':{
                    'loads':tempDir+'extreme_load_fullaverageextreme_ind_p99.npy',
                    'temps':tempDir+'extreme_simulations_fullaverageextreme_ind_p99.npy'
                    },
                'normal':{
                    'loads':tempDir+'ind_load_70years.npy',
                    'temps':tempDir+'ind_simulations_70years.npy'
                        }
                },
            # 0.999:{
            #     'extreme':{
            #         'loads':tempDir+'extreme_load_fullaverageextreme_ind_p999.npy',
            #         'temps':tempDir+'extreme_simulations_fullaverageextreme_ind_p999.npy'
            #         },
            #     'normal':{
            #         'loads':tempDir+'ind_load_70years.npy',
            #         'temps':tempDir+'ind_simulations_70years.npy'
            #             }
            #     }
            }
        }
    }




for name in validNames:
    for alpha in npyNames['midwest'][name]:
        params[name] = {'extreme':np.load(npyNames['midwest'][name][alpha]['extreme']['loads']).shape[2],
                        'normal':np.load(npyNames['midwest'][name][alpha]['normal']['loads']).shape[2]}
