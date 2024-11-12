#!/usr/bin/env python3
import time
from model import extremeTest
from methods_pickle import loadPickle, savePickle


size = 'mid'
folder = 'dec16mid'
kind = 'proposal_constraint'
dir = folder + '/' + kind + '/'
P = loadPickle(dir+'P')
S = loadPickle('train-scenarios/'+size+'/proposal0.99_all')
G = loadPickle('pickles/G')

for U in P['Ulist']:
    print(U,type(U))
    if U != 500:
        t0 = time.time()
        i = 0
        results = extremeTest({'i':i,
               'U':int(U),
               'dir':'',
               'P':P,
               'S':S,
               'G':G,
               'solutions':loadPickle(dir+'solutions')[int(i)][float(U)],
               'data':loadPickle(dir+'data')})

        savePickle('mega-sample-tests/',folder+'_'+kind+'_'+size+'_results_S'+str(i)+'_U'+str(U),results)

        print(U,time.time() - t0)
