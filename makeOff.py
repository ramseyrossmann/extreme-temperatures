#!/usr/bin/env python3
import numpy as np
import pandas as pd
from methods_pickle import loadPickle, savePickle
from cfg import FOR
import copy, time, bisect

# G = loadPickle('pickles/G')
L = loadPickle('pickles/L')
fips = loadPickle('pickles/fips')
# fips_midwest = loadPickle('pickles/fips_midwest')
fips6 = loadPickle('pickles/fips6')
new = loadPickle('pickles/new')

rates = pd.read_csv('extra/temperture_dependent_rates_linear.csv').set_index('Temp')
t_index = list(rates.index)
r = rates.to_dict()

index = new['options']
map_r_i = {r: fips6.index(r) for r in fips6}
map_uid_murphy = {g: L['Murphy'][new['map_model_type'][g]] for (g,i) in index}

#%%
def t_interp(t,tech):
    # if t in t_index: # might need to uncomment if T occurs on boundary
        # return r[tech][t]
    # else:
        b = bisect.bisect(t_index,t)
        low = t_index[b-1]
        high = t_index[b]
        return np.interp(t,(low,high),(r[tech][low],r[tech][high]))

def offFromS(S,tempDependent):
    OFF = {}
    T0 = time.time()
    for j in S:
        if tempDependent:
            s = S[j]
            Rates = {(g,i):t_interp(s['temp'][i],g) for i in range(len(fips6)) for g in L['Murphy-list'] }
        else:
            Rates = {(g,i):FOR[g] for i in range(len(fips6)) for g in L['Murphy-list'] }
        rates = [ (g,map_r_i[r], Rates[(map_uid_murphy[g],map_r_i[r])]) for (g,r) in index ]
        randoms = np.random.rand(len(index))
        outages = [item1[0:2] for item1, item2 in zip(rates, randoms) if item1[2] > item2]
        OFF[j] = {(u,fips6[i]):1 for (u,i) in outages}
    print('total  ',time.time() - T0)
    return OFF

#%% Train off
sizes = ['tiny','mid','small']
np.random.seed(0)
for size in sizes:
    for kind in ['base0','unconditional0','proposal0.99','independent0.99']:
        for I in range(15):
            try:
                S = loadPickle('train-scenarios/'+size+'/'+kind+'/S'+str(I)+'/S')[I]
                off = offFromS(S,True)
                savePickle('train-scenarios/'+size+'/'+kind+'/S'+str(I)+'/','off',off)
                off_nt = offFromS(S,False)
                savePickle('train-scenarios/'+size+'/'+kind+'/S'+str(I)+'/','off_nt',off_nt)
            except:
                print('Failed to create off for '+size+'/'+kind+'/S'+str(I))
    
#%% Test off
size = 'small'

np.random.seed(100000)
t0 = time.time()
S = loadPickle('test-scenarios/test/'+size+'/Se_full')
print('S loaded:', time.time() - t0)
t0 = time.time()
off = offFromS(S,True)
print('off:', time.time() - t0)
t0 = time.time()
savePickle('test-scenarios/test/'+size+'/','Se_off',off)
print('saved:', time.time()-t0)

np.random.seed(200000)
t0 = time.time()
S = loadPickle('test-scenarios/test/'+size+'/Sn_full')
print('S loaded:', time.time() - t0)
t0 = time.time()
off = offFromS(S,True)
print('off:', time.time() - t0)
t0 = time.time()
savePickle('test-scenarios/test/'+size+'/','Sn_off',off)
print('saved:', time.time()-t0)
















