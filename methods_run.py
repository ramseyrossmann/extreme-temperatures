#!/usr/bin/env python3
import numpy as np
import pandas as pd
import scipy.stats, time, os
import matplotlib.pyplot as plt
from collections import Counter
from methods_pickle import loadPickle, savePickle
from model import train, extremeTest, normalTest, relocate

def Train(inputs):
    i = int(inputs['i'])
    tstart = time.time()
    P = inputs['P']
    if P.get('relocate',False):
        solutions,data,m = relocate(inputs)
        # return m
    else:
        solutions,data,m = train(inputs)
    S = inputs['S']
    if P['name'] == 'base':
        Se = {s:S[i][s] for s in S[i].keys() if not S[i][s]['extreme']} # all of S in this case
    else:
        Se = {s:S[i][s] for s in S[i].keys() if S[i][s]['extreme']}

    for U in P['Ulist']:
        print('Ulist:',P['Ulist'])
        if P['parameter-type'] == 'constraint':
            print('shed before extremeTest')
            print(data[U]['stats']['shed_E'])
            inputs.update({'S':Se,'solutions':solutions[U],'training':True})
            out = extremeTest(inputs)
            shed = [out[key]['shed'] for key in out]
            print('\n shed after extremeTest')
            print(shed)
        else:
            shed = data[U]['stats']['shed_E']
        n = len(Se)
        tol = 0.00001
        if P['name'] != 'base':
            lolp = len([i for i in shed if i > 0 + tol]) / n
        else:
            lolp = 0
        if P['name'] != 'base':
            data[U]['stats']['shed_E'] = np.mean([np.sort(shed)[i] for i in range(int((1-inputs['P']['cvar'])*n),n) ])
            data[U]['stats']['lolp_E'] = lolp
        data[U]['stats']['time_train'] = time.time() - tstart
        if P.get('relocate',False):
            savePickle('relocate-solutions_S'+str(i)+'_U'+str(U),solutions)
            savePickle('relocate-data_S'+str(i)+'_U'+str(U),data)
        else:
            savePickle('','solutions_S'+str(i)+'_U'+str(U),solutions)
            savePickle('','data_S'+str(i)+'_U'+str(U),data)
        print('feasible='+str(data[U]['stats']['SolCount'] > 0))
        return m

def nTest(inputs):
    normal = normalTest(inputs)
    savePickle('','results_normal_U'+str(inputs['U'])+'_'+inputs['tag'],normal)

def eTest(inputs):
    extreme = extremeTest(inputs)
    savePickle('','results_extreme_U'+str(inputs['U'])+'_'+inputs['tag'],extreme)

def ExtremeTest(inputs):
    extreme = extremeTest(inputs)
    savePickle('','results_extreme_extreme_U'+str(inputs['U'])+'_'+inputs['tag'],extreme)

def processTrain(in_dict):
    dir1 = in_dict['dir']
    Rdir = in_dict['Rdir']
    P = in_dict['P']
    data,solutions = loadData(Rdir,P)
    data = calculateFleet(solutions,data,dir1)
    savePickle(dir1,'data',data)
    savePickle(dir1,'solutions',solutions)


def loadData(Rdir,P):
    data = {i:{} for i in range(P['n_trains'])}
    solutions = {i:{} for i in range(P['n_trains'])}
    for i in range(P['n_trains']):
        for U in P['Ulist']:
            d = Rdir+'S'+str(i)+'/U'+str(U)+'/'
            data[i].update(loadPickle(d+'data'))
            solutions[i].update(loadPickle(d+'solutions'))
    return data, solutions


def calculateFleet(solutions, data, dir1):
    L = loadPickle(dir1+'L')
    G = loadPickle(dir1+'G')
    P = loadPickle(dir1+'P')
    NEW = loadPickle(dir1+'new')
    for i in data:
        for U in P['Ulist']:
            data[i][U].update({'fleet': dict(
                Counter({g: sum(G['cap'][u] for u in G['zuid'] if G['map_uid_type'][u] == g and solutions[i][U]['z'][u] >= 0.5)
                          for g in L['gen']})
                + Counter({g: sum(G['cap'][u] for u in G['uid'] if G['map_uid_type'][u] == g and u not in G['zuid'])
                            for g in L['gen']})
                + Counter({g: sum(solutions[i][U]['y'][g, r] for (gg, r) in G['capcost_nrel'].keys() if gg == g)
                           for g in L['gen_cf']})
                + Counter({g: sum(NEW['cap'][gg] for (gg, r) in NEW['options'] if gg == g and solutions[i][U]['znew'].get((gg,r),0) >= 0.5) 
                           for g in NEW['map_model_type'] }))
                })
            cap_reserve = round(sum(
                data[i][U]['fleet'][g] for g in data[i][U]['fleet'].keys() if g not in L['gen_cf']), 1)
            cap_variable = round(
                sum(data[i][U]['fleet'][g] for g in data[i][U]['fleet'].keys() if g in L['gen_cf']), 1)
            data[i][U]['stats'].update({'cap_reserve': cap_reserve,
                                        'cap_variable': cap_variable,
                                  })
    return data


def processTest(in_dict):
    print('start processTest')
    dir1 = in_dict['dir']
    data = loadPickle(dir1+'data')
    print('data loaded')
    P = loadPickle(dir1+'P')
    results, solved = makeResults(in_dict)
    print('results made')
    df = reshapeData(results,data,P,solved)
    print('data reshaped')
    df.to_csv(dir1+'results_table.csv')
    savePickle(dir1,'results_table',df)
    print('df saved')
    makeGraphs(df,data,P,in_dict)
    print('graphs made')


def makeResults(in_dict):
    dir1 = in_dict['dir']
    P = loadPickle(dir1+'P')
    results = {U:{i:{} for i in range(P['n_trains'])} for U in P['Ulist']}
    solved = {U:[] for U in P['Ulist']}
    sol_list = []
    for i in range(P['n_trains']):
        for U in P['Ulist']:
            alpha = 1-P['test_cvar']
            # confidence interval on cost and normal shed
            if os.path.isfile(dir1+'results/normal/U'+str(U)+'_'+str(i)+'.pkl'):
                print(U,i)
                sol_list.append((U,i))
                solved[U].append(i)
                
                # NORMAL
                normal = loadPickle(dir1+'results/normal/U'+str(U)+'_'+str(i))
                # cost
                cost_list = [normal[key]['cost'] for key in normal]
                bot = [np.sort(cost_list)[i] for i in range(0,int(len(cost_list)*alpha))]
                cost = mean_confidence_interval(cost_list,len(cost_list))
                costadj = mean_confidence_interval(bot,len(cost_list))
                # shed
                shedN_list = [normal[key]['shed'] for key in normal if normal[key]['cost'] <= bot[-1]]
                shedN = mean_confidence_interval([normal[key]['shed'] for key in normal],len(cost_list))
                shedNadj = mean_confidence_interval(shedN_list,len(cost_list))
                lolpN = len([i for i in shedN_list if i > 0.0001]) / len(normal)
                
                # EXTREME - shed only
                extreme = loadPickle(dir1+'results/extreme/U'+str(U)+'_'+str(i))
                shedE = [extreme[key]['shed'] for key in extreme]
                top = [np.sort(shedE)[i] for i in range(int(len(shedE)*alpha),len(shedE))]
                shedE_err = mean_confidence_interval(top,len(shedE))
                lolpE = len([i for i in shedE if i > 0.0001]) / len(extreme)

                # record
                results[U][i]={
                    'shed_N':shedN[0],
                    'shed_N_err':shedN[1],
                    'shed_N_99':shedNadj[0],
                    'shed_N_99_err':shedNadj[1],
                    'shed_E':shedE_err[0],
                    'shed_E_err':shedE_err[1],
                    'lolp_N':lolpN,
                    'lolp_E':lolpE,
                    'cost_operating':np.mean([normal[key]['cost'] for key in normal ]),
                    'cost_operating_99':np.mean([normal[key]['cost'] for key in normal if normal[key]['cost'] <= bot[-1]]),
                    'cost_shedding':np.mean([normal[key]['shed'] for key in normal ])* P['cost_shed_test'],
                    'cost_shedding_99':np.mean([normal[key]['shed'] for key in normal if normal[key]['cost'] <= bot[-1]])* P['cost_shed_test'],
                    'cost_test':cost[0],
                    'cost_test_err':cost[1],
                    'cost_test_99':costadj[0],
                    'cost_test_99_err':costadj[1],
                    'scenarios_N':len(normal),
                    'scenarios_E':len(extreme),
                    'alpha':alpha,
                    }
    print(solved)
    print(sol_list)
    return results, solved

def reshapeData(test,train,P,solved):
    dict1 = {(U,i):train[i][U]['stats'] for U in P['Ulist'] for i in range(P['n_trains'])}
    dict2 = {(U,tag):test[U][tag] for U in solved for tag in solved[U]}
    for (U,tag) in dict2:
        dict2[(U,tag)].update({stat:dict1[(U,tag)][stat] for stat in ['cost_capital','cost_capital-old','cost_capital-new-conventional',
                                                                      'cost_capital-new-renewable','cap_reserve','cap_variable']})
        dict2[(U,tag)].update({'objective':sum(dict2[(U,tag)][key] for key in ['cost_test','cost_capital']),
                               'objective_99':sum(dict2[(U,tag)][key] for key in ['cost_test_99','cost_capital'])})
    train = pd.concat({'train':pd.DataFrame(dict1).transpose()}).transpose()
    test = pd.concat({'test':pd.DataFrame(dict2).transpose()}).transpose()
    df = train.merge(test,how='outer',left_index=True,right_index=True)
    df.columns.names = ['T','U','i']
    return df

def mean_confidence_interval(data, n, confidence=0.95):
    a = 1.0 * np.array(data)
    m, se = np.mean(a), scipy.stats.sem(a)
    h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
    # confidence interval is (m-h, m+h)
    return m, h

def makeGraphs(df,data,P,in_dict):
    NEW = loadPickle(in_dict['dir'] + 'new')
    dpi = in_dict['dpi']
    Ulist = [float(i) for i in df.columns.get_level_values(1).unique()]
    if P.get('name','') != 'base':
        Ulist.sort(reverse=True)
    figsize=(16,9)
    fontsize = 14
    extremes = {'shed_E':{'xlabel':'CVAR_'+str(P['test_cvar'])+' load shed per extreme hour (MWh)',
                          'title':'Cost (normal temps) vs Resiliency (normal temps)',
                          'tag':'normal_temps'},
                'lolp_E':{'xlabel':'Probability of shedding load',
                        'title':'Cost (normal temps) vs Loss of Load Probability (normal temps)',
                        'tag':'normal_temps'}
                }
    col_adj_ebar_train = [('shed_E','',False,False),('shed_E','_99',False,False),('shed_E','',True,False),
                          ('shed_E','_99',True,False),('shed_E','',False,True),
                          ('lolp_E','',False,False),('lolp_E','_99',False,False),('lolp_E','',False,True)]
    for (col,adj,ebars,boolean) in col_adj_ebar_train:
        plt.figure(figsize=figsize, dpi=dpi)
        plt.rcParams.update({'font.size': fontsize})
        for U in Ulist:
            print(U,df)
            graph_data = df['test'].iloc[:,df['test'].columns.get_level_values(0) == U]
            x = graph_data.loc[col]
            y = graph_data.loc['objective'+adj]
            plt.scatter(y=y,x=x,label=U)
            if ebars:
                xerr = graph_data.loc[col+'_err']
                yerr = graph_data.loc['cost_test'+adj+'_err']
                plt.errorbar(x, y, yerr=yerr, xerr=xerr, fmt='none')
                figsavename = 'plot_'+col+adj+'_ebars.png'
            else:
                if boolean:
                    figsavename = 'plot_'+col+adj+'_train.png'
                else:
                    figsavename = 'plot_'+col+adj+'.png'
        if boolean:
            plt.scatter(y=df['train'].loc['cost_operating']+df['train'].loc['cost_capital'],x=df['train'].loc[col],label='Train')

        plt.xlabel(extremes[col]['xlabel'],fontsize=fontsize)
        plt.ylabel('Total cost'+adj,fontsize=fontsize)
        plt.title(extremes[col]['title'])
        plt.legend(loc="upper right")
        plt.savefig(figsavename)

    L = loadPickle(in_dict['dir']+'L')
    # Capacity bar graph
    main = list(set(L['gen_retire'] + L['solar'] + L['wind'] + list(NEW['map_model_type'].keys())))
    other = [g for g in L['gen'] if g not in main]
    f = {i:{} for i in range(P['n_trains'])}
    for i in range(P['n_trains']):
        fleets = {U:data[i][U]['fleet'] for U in P['Ulist']}
        f[i] = {U:{g:fleets[U].get(g,0) for g in main} for U in P['Ulist']}
        for U in f[i]:
            f[i][U].update({'Other':sum(fleets[U].get(g,0) for g in other)})
    df = pd.DataFrame.from_dict(f, orient="index").stack().to_frame()
    df = pd.DataFrame(df[0].values.tolist(), index=df.index)
    df = df[['Other','Nuclear','Combined_Cycle','Combustion_Turbine','Coal_Steam',
                  'Offshore_Wind','Onshore_Wind','SolarDistUtil','SolarUtil']]
    df = df.swaplevel(0).sort_index()

    current_fleet = loadPickle(in_dict['dir']+'current_fleet')
    old_fleet = {g:current_fleet.get(g,0) for g in main}
    old_fleet['SolarUtil'] = current_fleet['Solar_PV']
    old_fleet['Other'] = sum(current_fleet.get(g,0) for g in other if g != 'Solar_PV')
    df.loc['current'] = old_fleet
    df = df.div(1000)
    ax = df.plot(kind='bar',stacked=True, figsize=(16,9), legend='reverse', rot=45)
    ax.set_xlabel('Test Solution')
    ax.set_ylabel('Capacity (GW)')
    plt.savefig('capacity.png')


def txt_to_list(d): # turns list of .sol files into list of [S,U,sol number]
    out = []
    with open(d) as f:
        for l in f:
            a = l.split('_')
            if len(a) == 5:
                a = a[2:]
                a[0] = int(a[0][1:]) # S
                a[1] = float(a[1][1:]) # U
                a[2] = int(a[2][:1]) # solution number
                out.append(a)
    return out
