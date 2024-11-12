#!/usr/bin/env python3
from methods_pickle import loadPickle
import pandas as pd

S = loadPickle('test-scenarios/test/large/Se')

#%%
dane=55025
solar='SolarDistUtil'
cf = [S[i]['factor'][(t,f)] for i in S for (t,f) in S[i]['factor'] if t==solar if f==dane]
#%%
df = pd.DataFrame(cf)
df.to_csv('dane-solar-from-Se.csv')