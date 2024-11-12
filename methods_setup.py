#!/usr/bin/env python3
import numpy as np
import pandas as pd
import random, copy, datetime, os, platform, time, shutil, bisect
from methods_pickle import loadPickle, savePickle
from cfg import L, npyNames, fips6, fipswi, params, validNames, FOR
from arrayReshape import reshape3dto4d

fips = fips6
gams = loadPickle('pickles/gams-data-midwest')
elist = ['unconditional','base','test']
rates = pd.read_csv('extra/temperture_dependent_rates_linear.csv').set_index('Temp')
t_index = list(rates.index)
r = rates.to_dict()

def makeFips6():
    df = pd.read_csv('sixstate_counties_lonlat_coordinates.txt',delimiter=' ',header=None)
    df.rename({0:'lon',1:'lat',2:'name',3:'fips'},inplace=True,axis=1)
    d = df[['fips','name']].set_index('fips').to_dict()['name']
    savePickle('','fips6_dict.pkl',d)
    d = df[['fips']].to_dict(orient='list')['fips']
    savePickle('','fips6.pkl',d)

def makeFipsWI():
    mapping = pd.read_csv(r'wi_counties_lonlat_coordinates.txt',sep = ' ',names=['lon','lat','name','fips'])
    mapping = mapping.drop({'lon','lat'},axis=1).set_index('name')
    fips_wi_dict = mapping.to_dict()['fips']
    savePickle('','fips_wi_dict.pkl',fips_wi_dict)
    fips_wi = list(fips_wi_dict.values())
    savePickle('','fips_wi.pkl',fips_wi)

def makeWindCF():
    W='Onshore_Wind'
    windcf = {(w,r,h):gams['cf'][(w,r,h)] for (w,r,h) in gams['cf'] if w == W}
    savePickle('pickles/','windcf',windcf)

def popUnnecessary(S):
    for s in S:
        # S[s].pop('temp')
        S[s].pop('CC')
        S[s].pop('CT')
        S[s].pop('HD')
        S[s].pop('NU')
        S[s].pop('ST')
        S[s].pop('wind')
    return S

def makeTestData(D):
    P = makeData(D)
    S = makeScenarioDict(P)
    if P['sizes']['extreme'] > 1:
        Se = {s:S[0][s] for s in S[0] if S[0][s]['extreme']}
        savePickle('test-scenarios/'+D['name']+'/'+D['size']+'/','Se_full',Se)
        Se = popUnnecessary(Se)
        for s in Se:
            Se[s].pop('temp')
        savePickle('test-scenarios/'+D['name']+'/'+D['size']+'/','Se',Se)

    if P['sizes']['normal'] > 1:
        Sn = {s:S[0][s] for s in S[0] if not S[0][s]['extreme']}
        savePickle('test-scenarios/'+D['name']+'/'+D['size']+'/','Sn_full',Sn)
        Sn = popUnnecessary(Sn)
        for s in Sn:
            Sn[s].pop('temp')
        savePickle('test-scenarios/'+D['name']+'/'+D['size']+'/','Sn',Sn)

def makeTrainDataOld(D):
    P = makeData(D)
    savePickle(D['Sdir']+'/','P',P)
    S = makeScenarioDict(P)
    t0 = time.time()
    for i in range(P['n_trains']):
        folder = D['Sdir']+'/S'+str(i)+'/'
        savePickle(folder,'S',{i:S[i]})
    print('savePickles',time.time() - t0)

def makeTrainData(D):
    P = makeData(D)
    savePickle(D['Sdir']+'/','P',P)
    S = makeScenarios(P)
    for i in range(P['n_trains']):
        t0 = time.time()
        Si = {i:S[i]}
        data = getTempLoad(Si,P)
        Si = tempScenario(Si,P,data)
        Si = makeFactor(Si)
        Si = adjustCapacities(Si)
        Si = {i:popUnnecessary(Si[i])}
        folder = D['Sdir']+'/S'+str(i)+'/'
        savePickle(folder,'S',Si)
        print('savePickles ' + str(i),time.time() - t0)

def copyPickles(dir1): # put pickles in dir1
    if not os.path.exists(dir1):
        os.mkdir(dir1)
    for name in ['L','G','fips6','current_fleet','tags','fips_midwest','new','good_CC','good_CT']:
        shutil.copyfile('pickles/'+name+'.pkl',dir1+'/'+name+'.pkl')

def populateDirs(in_dict,D):
    P = makeData(D)
    savePickle(in_dict['dir'],'P',P)
    # tags = loadPickle(in_dict['dir']+'tags')
    tags = [str(i) for i in range(P['n_trains'])]
    makeTextFiles(in_dict,P['Ulist'],tags)

    with open(in_dict['dir']+'train-data.txt','w') as f:
        Ulist = P['Ulist']
        rfolder = in_dict['Rdir']
        if not os.path.isdir(rfolder):
            os.mkdir(rfolder)

        for i in range(P['n_trains']):
            rfolder = in_dict['Rdir']+'S'+str(i)+'/'
            if not os.path.isdir(rfolder):
                os.mkdir(rfolder)

            for U in Ulist:
                folder = in_dict['Sdir']+'/S'+str(i)+'/U'+str(U)+'/'
                P['Ulist'] = [U]
                savePickle(folder,'P',P)
                f.write(str(i)+','+str(U)+'\n')
                rfolder = in_dict['Rdir']+'S'+str(i)+'/U'+str(U)+'/'
                if not os.path.isdir(rfolder):
                    os.mkdir(rfolder)

def makeTextFiles(in_dict,Ulist,tags):
    with open(in_dict['dir']+'results-data.txt','w') as f:
        if not os.path.isdir(in_dict['Rdir']):
            os.mkdir(in_dict['Rdir'])
        for extreme in ['normal','extreme']:#,'extreme_extreme']:
            if not os.path.isdir(in_dict['Rdir']+extreme+'/'):
                os.mkdir(in_dict['Rdir']+extreme+'/')
            for U in Ulist:
                for tag in tags:
                    f.write(extreme+','+str(U)+','+tag+'\n')
    with open(in_dict['dir']+'graph-data.txt','w') as f:
        # for source in ['wind','solar']:
        #     for tag in tags:
        #         f.write('map_'+source+'_'+tag+'.png\n') # heat maps
        f.write('plot.png\n')
        f.write('plot_ebars.png\n')
        f.write('capacity.png\n')
        f.write('results_table.csv\n')
        f.write('results_table.pkl\n')


def makeData(D):
    t0 = time.time()
    P = setP(D)
    print('setP:',time.time() - t0)
    t0 = time.time()
    P = setGenData(P)
    print('setGenData:',time.time() - t0)
    return P

def makeScenarioDict(P):
    t0 = time.time()
    S = makeScenarios(P)
    print('makeScenarios:',time.time() - t0)
    t0 = time.time()
    data = getTempLoad(S,P)
    print('getTempLoad:',time.time() - t0)
    t0 = time.time()
    S = tempScenario(S,P,data)
    print('tempScenario:',time.time() - t0)
    t0 = time.time()
    S = makeFactor(S)
    print('makeFactor:',time.time() - t0)
    t0 = time.time()
    S = adjustCapacities(S)
    print('adjustCapacities:',time.time() - t0)
    return S

def setP(newP):
    P = {'machine':platform.system(),
        'sizes':{'normal': 4,
                 'extreme': 8
                 },
        'n_trains': 1,
        'cvar': 0.01,
        'alpha':0.99, # for which proposal/independent data to use
        'test_cvar':0.0001,
        'cost_gas': 2.56, # Gas cost (dollars per MBtu); old gas price: 2.56
        'cost_coal': 2.02, # Coal cost (dollars per MBtu)
        'k': 0.42,
        'parameter-type':'constraint',
        'fixed-lambda':True,
        'exclude-extremes':False,
        'cost_shed':  65,
        'cost_shed_test': 65, # 64 is the max per unit operating cost (it's a CT)
        'npseed':  1,
        'randomseed': 1,
        'Ulist': [1,50,150,750],
        'time_horizon':  30,
        'scope':'midwest',
        'temperature-dependent':True,
        'demand_scale':1,#1.25,
        'incumbency-factor':1,#0.1,
        'TimeLimit':60*60*6,
        'new':False,
        }
    T = {
            'wind':    {'on':-20,'off':-30,'ratio':0.1},
            'gas':     {'on':-5,'off':-60,'ratio':0.2},
            'thermal': {'on':-5,'off':-60,'ratio':0.05, 'winter':25,'summer':85,'percent':0.1}
        }
    P['thresholds'] = T
    P['cf_dict'] = {'Offshore_Wind':1,
               'Onshore_Wind':1,
               'SolarDistUtil':1,
               'SolarUtil':1}
    P.update(newP)

    random.seed(P['randomseed'])
    np.random.seed(P['npseed'])

    # convert to Celsius?
    convert = True
    if convert:
        for i in ['wind','gas','thermal']:
            P['thresholds'][i]['on'] = (P['thresholds'][i]['on'] - 32 ) * 5/9
            P['thresholds'][i]['off'] = (P['thresholds'][i]['off'] - 32 ) * 5/9
        for i in ['thermal']:
            P['thresholds'][i]['winter'] = (P['thresholds'][i]['winter'] - 32 ) * 5/9
            P['thresholds'][i]['summer'] = (P['thresholds'][i]['summer'] - 32 ) * 5/9
    return P


def setGenData(P): # inputs are dollars per MBtu
    # also see this EIA link for comparison of total per kwh costs: https://www.eia.gov/electricity/annual/html/epa_08_04.html
    # Fixed scalars
    cost_biomass = 30  # Biomass cost (dollars per ton)
    heat_content = 8150 # Biomass heat content (Btu per pound)
    cost_landfill_gas = 2.56/2 # 2  # Landfill gas cost
    # renewable_scale = 1 # Renewables fixed cost factor

    # below, dividing by 1000 accomplishes MBtu to Btu conversion (for fuel costs) and kWh to MWh conversion
    # (for heat rate, happens later)
    fuel = {
        'Coal_Steam':P['cost_coal']/1000,
        'Combustion_Turbine': P['cost_gas']/1000,
        'Combined_Cycle': P['cost_gas']/1000,
        # 'Nuclear': 0.0015,
        'Nuclear': 0,
        'Biomass': cost_biomass*(1/2000)/heat_content*1000,
        # ^ this is a (very) rough average across different kinds of biomass
        'Landfill_Gas': cost_landfill_gas/1000, # guess
        'OG_Steam': P['cost_gas']/1000,
        # ^ almost all of the OG_Steam plants get modeled by gas according to EPA NEEDS database
    }
    fuel.update({'Non_Fossil_Waste': fuel['Biomass']}) # guess

    # fuel costs source:
    #   https://www.eia.gov/dnav/ng/hist/rngwhhdD.htm
    #   https://www.eia.gov/electricity/annual/html/epa_07_04.html - have to pick which kind of coal
    P['fuel'] = fuel

    capital_cost = {#   capital cost by generator type (dollars per MW)
        'Combined_Cycle': 989000,
        'Combustion_Turbine': 742000,
        'Nuclear': 6450000,
        'Coal_Steam': 3838000,
        'Biomass': 4208000,
        'Hydro': 1963000,
        'Non_Fossil_Waste': 1700000,
        'OG_Steam': 1700000,
        'Landfill_Gas': 1606000,
        'Onshore_Wind': 52000 # minimum-epsilon existing wind cost according to capcost_nrel - time horizon later
       }
    capital_cost['Onshore_Wind'] = capital_cost['Onshore_Wind']*P['time_horizon']
    P['capital_cost'] = capital_cost
    return P

def makeScenarios(P):
    S = {}
    if P['name'] in validNames:
        name = P['name']
    else:
        name = 'proposal'
    l1 = [list(range(params[name]['normal'])) for m in range(params['months'])]
    l2 = [list(range(params[name]['extreme'])) for m in range(params['months'])]
    for m in range(len(l1)):
        random.shuffle(l1[m])
    for m in range(len(l2)):
        random.shuffle(l2[m])
    # dictionary to keep track of unused samples (days) by month
    samples = {'normal':{m:l1[m] for m in range(params['months'])},
               'extreme':{m:l2[m] for m in range(params['months'])}}

    m = list(range(364))
    m = m[-31:] + m[:-31]
    d = [31,28,31,30,31,30,31,31,30,31,30,31]
    jul = {i:sum(d[:i]) for i in range(12)} # julian days
    l = [0,1,5,6]
    season_days = {'extreme':{i:list(range(jul[l[i]],jul[l[i]]+d[l[i]])) for i in range(len(l))},
                   'normal':{s:m[s*int(364/params['months']):(s+1)*int(364/params['months'])] for s in range(params['months'])}}
    data = {'extreme':{'h':params['hours'],'s':params[name]['extreme'],'m':list(range(params['months'])),
                       'size':P['sizes']['extreme']},
             'normal':{'h':params['hours'],'s':params[name]['normal'],'m':list(range(params['months'])),
                       'size':P['sizes']['normal'] } }
            # h: number of hours; s: number of scenarios; m: months to pick for; size: number of days per month
    if name == 'base':
        data.pop('extreme')
    for i in range(P['n_trains']):
        months = {'extreme':[],'normal':[] }
        hours = {'extreme':[],'normal':[] }
        scenarios = {'extreme':[],'normal':[] }
        for t in data: # t for type
            if name in elist:
                esource = 'normal'
            else:
                esource = t
            for m in data[t]['m']: # m for "month"
                # pick sims and remove from samples list
                # print(esource,m,len(samples[esource][m]))
                scen_new = [[samples[esource][m].pop(0)]*data[t]['h'] for i in range(data[t]['size'])]
                scen_new = [item for sublist in scen_new for item in sublist]
                # assign day of year to each sim
                days = random.choices(season_days[t][m],k=data[t]['size'])
                # assign hour of year to each sim
                h_new = [h for d in days for h in range(d*24+1,(d+1)*24+1,int(24/data[t]['h']))]
                scenarios[t] = scenarios[t] + scen_new
                months[t] = months[t] + [m]*data[t]['h']*data[t]['size']
                hours[t] = hours[t] + h_new
        Sdict = {}
        start = 0
        for t in data:
            data[t]['q'] = 1 / len(hours[t])
            extreme = t == 'extreme'
            Sdict.update({j+start: {
                'h': hours[t][j],
                'm': months[t][j],
                'q': data[t]['q'],
                'sim': scenarios[t][j],
                'extreme': extreme}
                for j in range(len(hours[t]))})
            start = len(Sdict)
        # means = {s: np.mean(Sdict[s]['sim']) for s in Sdict if not Sdict[s]['extreme'] }
        # 1 if not extreme, 0 if extreme
        # qvals = {s: {q: quants[q][(Sdict[s]['h']+5) % 24] < means[s]
        #              and means[s] < quants[1-q][(Sdict[s]['h']+5) % 24]
        #              for q in quants} for s in means}
        # extremes = {q: sum(qvals[s][q] for s in qvals) for q in quants}
        # for s in Sdict:
        #     if not Sdict[s]['extreme']:
        #         Sdict[s]['qval'] = {q: qvals[s][q]/extremes[q] for q in quants}
        #     else:
        #         Sdict[s]['qval'] = {q: S[s]['q'] for q in quants}
        #
        S[i] = Sdict
    return S

def getTempLoad(S,P):
    # updates each Sdict in S with corresponding temperature and load
    name = P.get('name','proposal')
    if name not in validNames:
        name = 'proposal'
    extreme = name not in elist # extremes are normal, for reshaping purposes

    data = {'temps':{
        False: reshape3dto4d({'extreme':False,
                              'temps':npyNames[P['scope']][name][P['alpha']]['normal']['temps']
                              }, False),
        True: reshape3dto4d({'extreme':extreme,
                             'temps':npyNames[P['scope']][name][P['alpha']]['extreme']['temps'],
                             }, False)
        },
        'loads':{
            False: np.load(npyNames[P['scope']][name][P['alpha']]['normal']['loads']),
            True: np.load(npyNames[P['scope']][name][P['alpha']]['extreme']['loads'])
            }
        }

    return data


def tempScenario(S,P,data):
    for Sdict in S:
        for s in S[Sdict].keys():
            extreme = S[Sdict][s]['extreme']
            h = S[Sdict][s]['h'] % 12
            m = S[Sdict][s]['m']
            temp = data['temps'][extreme][:,m,h,S[Sdict][s]['sim']] # temps for all counties for one hour
            load = data['loads'][extreme][m,h,S[Sdict][s]['sim']]
            S[Sdict][s].update({'temp':temp,'load': load})


            temps = S[Sdict][s]['temp']
            t = temps.mean()
            wind = dict()
            T = P['thresholds']
            # direct use of Murphy, et al, numbers
            outage_rates = {tech: {fips[r]: t_interp(temps[r],tech) for r in range(len(temps))}
                           for tech in L['Murphy-list']}


            # # gas
            # if t >= T['gas']['on']:
            #     gas = 1
            # elif t < T['gas']['off']:
            #     gas = 0
            # else:
            #     gas = max(0,1-coldEffect(t,T['gas'],P['k']))

            # wind
            if min(temps) >=  T['wind']['on']: # just to speed up computation for most days
                wind = {fips[r]:1 for r in range(len(temps))}
            else:
                for r in range(len(temps)):
                    t = temps[r]
                    if t >= T['wind']['on']:
                        cf = {fips[r]:1}
                    elif t > T['wind']['off']:
                        cf = {fips[r]:max(0,1-coldEffect(t,T['wind'],P['k']))}
                    else:
                        cf = {fips[r]:0}
                    wind.update(cf)

            # # thermal
            # for r in range(len(temps)):
            #     if t >= T['thermal']['on']:
            #         cf = {fips[r]:min(1,hotEffect(t,T['thermal']))}
            #     elif t > T['thermal']['off']:
            #         p_fail = getP_failure(t,T['thermal'])
            #         if random.uniform(0,1) < p_fail:
            #             cf = {fips[r]:0}
            #         else:
            #             cf = {fips[r]:1}
            #     else:
            #         cf = {fips[r]: 0}
            #     thermal.update(cf)

            # S[Sdict][s].update({'gas':gas,'wind':wind,'thermal':thermal})

            S[Sdict][s].update({'wind':wind})
            S[Sdict][s].update(outage_rates)
    return S


def coldEffect(t,data,k):
    p = getP_failure(t,data)
    s = np.random.normal(p, p*(1-p)*k)
    # returns randomized failure probability
    return s

# def hotEffect(t,data):
#     slope = data['percent'] / (data['winter'] - data['summer'])
#     thres = np.random.normal(t,1.5)
#     cf = 1 + (thres - data['winter'])*slope
#     s = max(0,cf)
#     return s

def t_interp(t,tech):
    if t in t_index:
        return r[tech][t]
    else:
        b = bisect.bisect(t_index,t)
        # print('b',b)
        # print('t',t)
        # print('t_index',t_index)
        # print('tech',tech)
        low = t_index[b-1]
        high = t_index[b]
        return np.interp(t,(low,high),(r[tech][low],r[tech][high]))

def getP_failure(t,data):
    on = data['on']
    off = data['off']
    ratio = data['ratio']
    dT = on-off
    b = -off+dT*ratio
    a = (off+b)*(on+b) / dT
    c = -a / (on+b)
    p_fail = a / (t + b) + c
    # returns failure probability on deterministic curve
    return p_fail

def makeFactor(S):
    # w='Onshore_Wind'
    NOCT = 45
    eff = .18
    eta = 0.005
    for Sdict in S:
        for s in S[Sdict].keys():
            # S[Sdict][s]['orig-factor'] = {(g,r): gams['cf'].get((g,r,S[Sdict][s]['h']),0) for (g,r) in gams['capcost_nrel']}
            # S[Sdict][s]['factor'] = {(g,r): gams['cf'].get((g,r,S[Sdict][s]['h']),0) * max(int(g!=w),S[Sdict][s]['wind'][r])
            #                          for (g,r) in gams['capcost_nrel']}

            # wind = {(g,r): gams['cf'].get((g,r,S[Sdict][s]['h']),0) * S[Sdict][s]['wind'][r] for (g,r) in gams['capcost_nrel'] if g==w}
            # solar = {(g,r): gams['cf'].get((g,r,S[Sdict][s]['h']),0) *
            #          (1 - (S[Sdict][s]['temp'][fips.index(r)] + (NOCT-20)/800*gams['cf'].get((g,r,S[Sdict][s]['h']),0)*CoverAe)*coefT)
            #          for (g,r) in gams['capcost_nrel'] if g in ['SolarUtil','SolarDistUtil']}
            S[Sdict][s]['factor'] = {(g,r): (gams['cf'].get((g,r,S[Sdict][s]['h']),0),
                                             gams['cf'].get((g,r,S[Sdict][s]['h']),0) *
                                     {'Offshore_Wind':1,
                                      'Onshore_Wind':S[Sdict][s]['wind'][r],
                                      'SolarUtil':1-(S[Sdict][s]['temp'][fips.index(r)]+(NOCT-20)/800*gams['cf'].get((g,r,S[Sdict][s]['h']),0)/eff - 25)*eta,
                                      'SolarDistUtil':1-(S[Sdict][s]['temp'][fips.index(r)]+(NOCT-20)/800*gams['cf'].get((g,r,S[Sdict][s]['h']),0)/eff - 25)*eta
                                      }[g])
                                     for (g,r) in gams['capcost_nrel']}

    return S

def adjustCapacities(S):
    # thermalNonGas = [i for i in L['gen_thermal'] if i not in L['gen_gas']]
    for Sdict in S:
        for s in S[Sdict]:
            g = {'cap':{},
                 'cap-for':{}}
            for u in gams['uid']:
                r = gams['map_uid_fips'][u]
                gen_type = gams['map_uid_type'][u]
                if gen_type in L['Murphy']:
                    prob = random.uniform(0,1) # could do as array outside loop
                    g['cap'][u] = gams['cap'][u] * int(prob >= S[Sdict][s][L['Murphy'][gen_type]][r])
                    g['cap-for'][u] = gams['cap'][u] * int(prob >= FOR[L['Murphy'][gen_type]])
                # if gen_type in L['gen_gas']:
                #     S[Sdict][s]['cap'][u] = gams['cap'][u] * min(S[Sdict][s]['gas'], S[Sdict][s]['thermal'][r])
                elif gen_type in L['gen_cf']:
                    g['cap'][u] = gams['cap'][u] * S[Sdict][s]['factor'][gen_type, r][1]
                    g['cap-for'][u] = gams['cap'][u] * S[Sdict][s]['factor'][gen_type, r][0]
                # elif gen_type in thermalNonGas:
                #     S[Sdict][s]['cap'][u] = gams['cap'][u]* S[Sdict][s]['thermal'][r]
                else:
                    g['cap'][u] = gams['cap'][u]
                    g['cap-for'][u] = gams['cap'][u]
            S[Sdict][s].update(g)
    return S

def makeNew():
    fips = loadPickle('pickles/fips6')
    # params = pd.read_excel('generator-parameters.xlsx',).set_index('params')
    params = pd.read_csv('generator-parameters.csv',).set_index('gens').transpose()
    gens = list(params.columns)
    new = {
        'map_model_type':params.loc['type'].to_dict(),
        'options':[(g,r) for g in gens for r in fips],
        'gens':gens,
        'cap': params.loc['cap'].to_dict(),
        'hr': params.loc['hr'].to_dict(),
        }
    savePickle('pickles/','new',new)
    return new

# Saves as pickles the generators that were chosen in all solutions in one sol = {i: {U: {z: {}, y: {}} if U <= U_high} }
def saveGoodGens(solution_dir, U_high):
    sol = loadPickle(solution_dir)
    sol_good = {i: {U: sol[i][U] for U in sol[i] if U <= U_high} for i in sol}
    G = loadPickle('pickles/G')
    map_name_abb = {'Combined_Cycle':'CC','Combustion_Turbine':'CT','Coal_Steam':'coal'}
    for gen in map_name_abb:
        gens_all = [ u for u in G['zuid'] if G['map_uid_type'][u] == gen]
        gens_on = {(U,i): [u for u in sol_good[i][U]['z'] if u in gens_all if sol_good[i][U]['z'][u] > 0.5 ]
                   for i in sol_good for U in sol_good[i] }
        gens_good = set.intersection(*map(set,list(gens_on.values())))
        if len(gens_good) > 0:
            savePickle('pickles/','good_'+map_name_abb[gen],gens_good)

sol_dir = 'may2-allgen/proposal_constraint/solutions'
U_high = 18000
# saveGoodGens(sol_dir, U_high)
