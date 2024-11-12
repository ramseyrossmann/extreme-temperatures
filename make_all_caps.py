#!/usr/bin/env python3
import random, time
from methods_pickle import loadPickle, savePickle
from cfg import L, fips6

random.seed(100)
fips = loadPickle('pickles/fips_midwest')
# gams = loadPickle('pickles/gams-data-midwest')
G = loadPickle('pickles/G')
#%%ç
for size in ['mid','small']:
    print(size)
    for kind in ['proposal0.99','unconditional0','base0','independent0.99']:
        print(kind)
        if (size,kind) != ('mid','proposal0.99'):
            for i in range(15):
                print(i)
                key = size + '/' + kind + '/S' +str(i)+'/'
                S = loadPickle('train-scenarios-temp/'+key+'S')[i]
                t = time.time()
                off = {}
                for s in S:
                    temp = {(u,r):
                                int(random.uniform(0,1) >=  S[s][L['Murphy'][G['map_uid_type'][u]]].get(r,0))
                                for u in G['zuid'] if G['map_uid_type'][u] in L['Murphy']
                                for r in fips6 if fips[r] == fips[G['map_uid_fips'][u]]
                                }
                    off[s] = {k:1 for k in temp if temp[k] == 0}
                    # break
                savePickle('train-scenarios/'+key,'off',off)
                print(time.time() - t)



#%%
def adjustCapacities(S):
    for Sdict in S:
        for s in S[Sdict]:
            g = {'cap':{}}
            for u in gams['uid']:
                r = gams['map_uid_fips'][u]
                gen_type = gams['map_uid_type'][u]
                if gen_type in L['Murphy']:
                    prob = random.uniform(0,1) # could do as array outside loop
                    g['cap'][u] = gams['cap'][u] * int(prob >= S[Sdict][s][L['Murphy'][gen_type]][r])
                # if gen_type in L['gen_gas']:
                #     S[Sdict][s]['cap'][u] = gams['cap'][u] * min(S[Sdict][s]['gas'], S[Sdict][s]['thermal'][r])
                elif gen_type in L['gen_cf']:
                    g['cap'][u] = gams['cap'][u] * S[Sdict][s]['factor'][gen_type, r]
                # elif gen_type in thermalNonGas:
                #     S[Sdict][s]['cap'][u] = gams['cap'][u]* S[Sdict][s]['thermal'][r]
                else:
                    g['cap'][u] = gams['cap'][u]
            S[Sdict][s].update(g)
    return S
