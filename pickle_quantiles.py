#!/usr/bin/env python3
from methods_pickle import savePickle

# Q={
#     0.01:{'jan','feb'},
#     0.001:{'jan','feb'},
#     0.99:{'jul','aug'},
#     0.999:{'jul','aug'},
# }
Q={'jan':{0.01,0.001},
   'feb':{0.01,0.001},
   'jul':{0.99,0.999},
   'aug':{0.99,0.999}}
M={
#    'jan':0,
   'feb':0,
   'jul':2,
#    'aug':0
}
H=list(range(0,24,2))
beg='simulated_quantiles/fullstate_empirical_'
end='quantiles.txt'
quantiles={q:{h:float(open(beg+str(q)+m+'hour'+str(h)+end,'r').readlines()[0].strip()) 
             for h in H}
      for m in M    for q in Q[m] }
      
       
savePickle('pickles/','quantiles',quantiles)
quantiles