#!/usr/bin/env python3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from methods_pickle import  loadPickle
from paper_figures import data, colors, sizeTO, sizeHalf
from combine_graphs_new import makeRes, params
# from cfg import L, npyNames, fips6, fipswi, params, validNames, FOR

#%%
def makedf(dir1):
    df = pd.read_csv(dir1[0]+'/results/results_table.csv',header=[0,1,2],index_col=0)
    # df = df.loc[keep_cols]
    return df['test'].transpose()

#%%
dlabels = {
    'new':{'name':'BiObj-Cond', 'df':None, 'tag':''},
    'new_nt':{'name':'BiObj-Cond (NT)','df':None, 'tag':' NT'}
    }

decisions = {
    # 'Combined_Cycle':'CC',
     'Onshore_Wind':'Wind',
     'Nuclear':'Nuclear',
     # 'Combustion_Turbine':'CT',
     'SolarDistUtil':'Solar',
     'SolarUtil':'Solar',
     'CT_small':'CT',
     'CT_big':'CT',
     'CC_big':'CC'
     }

def fleetdf(d):
    DATA = loadPickle(data[d]['dir'][0]+'/data')
    fleets = {i: {U: DATA[i][U]['fleet'] for U in DATA[i] if U != 'i' } for i in DATA}

    tuples = [(i,j) for i in fleets.keys() for j in fleets[0].keys()]
    cols = pd.MultiIndex.from_tuples(tuples, names=["i", "U"])
    df = pd.DataFrame( columns=cols )
    for i in fleets.keys():
        df[i] = pd.DataFrame.from_dict(fleets[i])
    df = df.fillna(0)
    df = df.div(1000) # MW to GW
    return df

def fleeteff(d):
    params['nondominated'] = True
    res = makeRes(data[d],params)
    dlabels[d]['eff'] = {(int(res.loc[r]['i']),float(res.loc[r]['parameter']) ): res.loc[r]['shed_E'] for r in res.index }
    df = fleetdf(d)    
    df = df[dlabels[d]['eff']]
    df = df.transpose()
    df['shed_E'] = pd.Series(dlabels[d]['eff'])
    # df = df.reset_index()
    df.index = df['shed_E']
    df = df.transpose()
    # df = df.swaplevel(axis=1)
    df['type'] = pd.Series(decisions)
    toplot = df.groupby('type').sum()
    return toplot


def fleetave(d):
    df = fleetdf(d)
    df = df.swaplevel(axis=1)
    Uvals = [U/1000 for U in set(df.columns.get_level_values(0)) if U != 30000]
    aves = pd.DataFrame(columns=Uvals)
    for U in Uvals:
        aves[U] = df[U*1000].mean(axis=1)
    aves['type'] = pd.Series(decisions)
    aves = aves.drop([i for i in aves.index if i not in decisions])
    toplot = aves.groupby('type').sum()    
    
    makeplot(toplot)
    return toplot

def makeplot(df):
    plt.figure(dpi=200)
    for energy_type in df.index:
        plt.scatter(df.columns, df.loc[energy_type], label=energy_type)
    # plt.legend()
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left') 
    plt.xlabel('Training U value (GW)')
    plt.ylabel('Capacity installed (GW)')
    # plt.title(dlabels[d])
    plt.show()
    

    
#%%
ave = True
save = False

if ave:
    new = fleetave('new')
    newnt = fleetave('new_nt')
else:
    new = fleeteff('new')
    newnt = fleeteff('new_nt')

dlabels['new']['df'] = new
dlabels['new_nt']['df'] = newnt

fig, axs = plt.subplots(2,2, dpi=200)
tech = {'CC':{'title':'Combined Cycle','ax':axs[0,0]},
        'CT':{'title':'Combustion Turbine','ax':axs[1,0]},
        'Wind':{'title':'Wind','ax':axs[0,1]},
        'Solar':{'title':'Solar','ax':axs[1,1]}
        }

for t in tech:
    # tech[t]['ax'].figure(dpi=200, figsize=sizeHalf)
    
    tech[t]['ax'].scatter(new.columns, new.loc[t], label=dlabels['new']['name'], 
                color = colors[data['new']['color']]['color'],
                marker = data['new']['marker'])
    tech[t]['ax'].scatter(newnt.columns, newnt.loc[t], label=dlabels['new_nt']['name'], 
                color = colors[data['new_nt']['color']]['color'],
                marker = data['new_nt']['marker']
                )
    if ave:
        xlabel = 'Training U value (GW)'
        if t in ['CC','Wind']:
            ylim = (29,49)
        else:
            ylim = (-1,11)
    else:
        xlabel = 'Testing U value (GW)'
        if t in ['CC','Wind']:
            ylim = (27,49)
        else:
            ylim = (-1,15)

    tech[t]['ax'].set_ylim(ylim)

    tech[t]['ax'].set_title(tech[t]['title'])
    for ax in axs.flat:
        ax.set(xlabel=xlabel, ylabel='Capacity installed (GW)')    
        ax.label_outer()

    plt.legend()
fig.show()
if save:
    if ave:
        plt.savefig('paper-figs/new-vs-newnt-fleet_ave.pdf')
    else:
        plt.savefig('paper-figs/new-vs-newnt-fleet_eff.pdf')
