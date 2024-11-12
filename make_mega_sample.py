#!/usr/bin/env python3
from methods_pickle import loadPickle, savePickle

# make mega sample training samples
kind = 'proposal0.99'
n = 15

for size in ['small']:
    bigS = {}
    for i in range(n):
        S = loadPickle('train-scenarios/'+size+'/'+kind+'/S'+str(i)+'/S')[i]
        for s in S:
            S[s].pop('cap-for')
            S[s].pop('temp')
        bigS.update({s+len(S)*i:S[s] for s in S})
    savePickle('train-scenarios/'+size+'/',kind+'_all',bigS)
del bigS
