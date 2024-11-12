#!/usr/bin/env python3
import numpy as np
# import pandas as pd
import copy
from arrayReshape import reshape3dto4d
# from methods_pickle import loadPickle, savePickle

tempDir = 'temp-and-load-sims/'
temps = {'normal':reshape3dto4d({'extreme':False,
                       'temps':tempDir+'spatial_simulations_70years.npy'
                              }, False),
         .999:reshape3dto4d({'extreme':True,
                       'temps':tempDir+'extreme_simulations_fullaverageextreme_spatial_p999.npy'
                              }, False),
         .99:reshape3dto4d({'extreme':True,
                       'temps':tempDir+'extreme_simulations_fullaverageextreme_spatial_p99.npy'
                              }, False)
}

pct = [0.0001,0.001,0.01]

def etempsquant(T):
    emeans1d = {(i,j,k):T[i,j,k] for i in range(len(T))
              for j in range(len(T[0])) for k in range(len(T[0,0]))}
    cold = [i for i in emeans1d.values() if i < 0]
    hot = [i for i in emeans1d.values() if i > 0]
    return {'cvar':{'low':np.mean(cold),'high':np.mean(hot)},'quantile':{'low':max(cold),'high':min(hot)}}

stats = {k:{p:{'quantile':None,'cvar':None} for p in pct} for k in range(len(temps['normal']))}
for k in range(len(temps['normal'])):
    normal = copy.deepcopy(temps['normal'][k])
    normal1d = {(i,j,k):normal[i,j,k] for i in range(len(normal))
              for j in range(len(normal[0])) for k in range(len(normal[0,0]))}
    normal_sorted = np.sort(list(normal1d.values()))
    k = normal_sorted
    stats[k]['quantile'] = {p:{'low':k[int(len(k)*p)+1] ,
                 'high':k[int(len(k)*(1-p))-1]}
              for p in pct}
    stats[k]['cvar'] = {p:{'low':np.mean(k[:int(len(k)*p)+1]),
            'high':np.mean(k[int(len(k)*(1-p)):])}
        for p in pct}
    stats[k][.999] = etempsquant(temps[.999])
    stats[k][.99] = etempsquant(temps[.99])
