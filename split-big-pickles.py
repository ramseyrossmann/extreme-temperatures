#!/usr/bin/env python3

import numpy as np
import pandas as pd
from methods_pickle import loadPickle, savePickle

#%%
# file = 'Sn_full'
# file = 'Se_full'
file = 'megaTest'
folder = {'Sn_full':'test-scenarios/test/large/',
          'Se_full':'test-scenarios/test/large/',
          'megaTest':'train-scenarios/small/'}
loadfile = folder[file]+file
S = loadPickle(loadfile)

#%%

new = {i:{(t,f):S[i]['factor'][(t,f)][0] for (t,f) in S[i]['factor']} for i in S}
# nt = {i:{(t,f):S[i]['factor'][(t,f)][1] for (t,f) in S[i]['factor']} for i in S}

#%%

# temps
# solardistutil
# onshore wind
# new cc big
# new ct big

#%%

small = {s:S[s] for s in range(100)}
