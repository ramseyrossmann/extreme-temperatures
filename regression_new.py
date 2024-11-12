#!/usr/bin/env python3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder
import joblib, time, copy, os
from arrayReshape import make2d, params, reshape3dto4d

pd.options.mode.chained_assignment = None  # default='warn'

from cfg import fipswi, fips6, npyNames

n_months = params['months']

h_list = ['h_'+str(i) for i in range(24)]
m_list = ['m_'+str(i) for i in range(n_months)]
d_list = ['weekend','weekday']

months = list(range(0,n_months)) + [0]*(24-n_months)
hours = list(range(24))

fips = fips6
temp_filename = 'temp-and-load-sims/sixstate_historical_data.npy'
load_filename = 'load_counties_midwest_2011.csv'

# make training temps
all_data = np.load(temp_filename)
year1 = all_data[:,6:8760-18,20] # 2011 for all counties, all hours
temp_train = pd.DataFrame(data=year1[0:,0:],index=fips,columns=range(0,8760-24)).transpose()
temp_train = temp_train[fips]

# Load data for 2011
load = pd.read_csv(load_filename).rename({'Unnamed: 0':'Hour'},axis=1)
load.drop(range(8736,8760),inplace=True)
# load.index = load.index+1
load.drop('Hour',axis=1,inplace=True)
load.columns = load.columns.astype(int)
load = load[fips]


def makeNames():
    colnames = []
    for m in m_list:
        # TMP * TMPID * MONTH:
        colnames.append('T '+m+'cold')
        colnames.append('T '+m+'hot')
        # TMP2 * TMPID * MONTH:
        colnames.append('T2 '+m+'cold')
        colnames.append('T2 '+m+'hot')

    for h in h_list:
        # TMP * TMPID * Hour
        colnames.append('T '+h+'cold')
        colnames.append('T '+h+'hot')
        # TMP2 * TMPID * Hour
        colnames.append('T2 '+h+'cold')
        colnames.append('T2 '+h+'hot')
        if h != h_list[0]:
            for d in d_list:
                # Hour * Day:
                colnames.append(d + ' ' + h)
    return colnames

def makeColumns(X):
    cols = []
    for m in m_list:
        # TMP * TMPID * MONTH:
        cols.append(X[m]*X['TMP']*X['Cold'])
        cols.append(X[m]*X['TMP']*X['Hot'])
        # TMP2 * TMPID * MONTH:
        cols.append(X[m]*X['TMP2']*X['Cold'])
        cols.append(X[m]*X['TMP2']*X['Hot'])

    for h in h_list:
        # TMP * TMPID * Hour
        cols.append(X[h]*X['TMP']*X['Cold'])
        cols.append(X[h]*X['TMP']*X['Hot'])
        # TMP2 * TMPID * Hour
        cols.append(X[h]*X['TMP2']*X['Cold'])
        cols.append(X[h]*X['TMP2']*X['Hot'])
        if h != h_list[0]:
            for d in d_list:
                # Hour * Day:
                cols.append(X[h]*X[d])
    return cols

def makeOneHot(df,model):
    df.rename({'month':'m','hour':'h'},axis=1,inplace=True)
    onehot = df[['m','h']]
    enc = OneHotEncoder(handle_unknown='ignore')
    enc.fit(onehot)
    codes = enc.transform(onehot).toarray()
    feature_names = enc.get_feature_names_out(['m', 'h'])
    columns_to_use = ['TMP','TMP2','Cold','Hot','weekday','weekend']
    if model:
        columns_to_use.append('Load')
    df1 = df[columns_to_use]
    X = pd.concat([df1.reset_index(drop=True),pd.DataFrame(codes,columns=feature_names).astype(int)],axis=1)
    return X


def oneCounty(county_code,D):  # returns model for one county for a set of hours
    cutoff = D['cutoff_C'] + 273 # converting to Kelvin
    df = pd.DataFrame()
    df['date'] = pd.date_range('1/1/2011 00:00:00', periods = 8736, freq ='H')
    df['day'] = df['date'].dt.weekday # Mon = 0, ..., Sunday = 6
    df['hour'] = df['date'].dt.hour
    df['Load'] = load[county_code]
    df['TMP'] = temp_train[int(county_code)] + 273
    if D['center']:
        offset = -D['cutoff_C']
    else:
        offset = 273
    df['TMP2'] = (temp_train[int(county_code)]+offset)**2
    if D['nolowsquare']:
        df.loc[df.TMP < D['cutoff_low']+273, 'TMP2'] = 0
    df['Cold'] = np.where(df['TMP']<cutoff, 1, 0)
    df['Hot'] = np.where(df['TMP']>=cutoff, 1, 0)

    df['weekday'] = np.where(df['day'].isin(range(0,5)), 1,0)
    df['weekend'] = np.where(df['day'] >= 5 ,1,0)
    df.drop(['date','day'],axis=1,inplace=True)
    if D['wintershift']:
        month_offset = 31*24 # for Dec, Jan, Feb to be winter, and so on
    else:
        month_offset = 0
    df['month'] = ((df.index - month_offset)/ (24*(364/n_months))).astype(int)
    if D['nowintersquare']:
        if params[False]['months'] == 7:
            w_list= [0,6]
        else:
            w_list = [0,1,2,11,12]
        df.loc[df.month.isin(w_list), 'TMP2'] = 0
    X = makeOneHot(df,True)
    cols = makeColumns(X)
    colnames = makeNames()

    model = pd.concat([X,pd.DataFrame(np.array(cols).transpose(), columns=colnames)],axis=1)
    model.drop(['TMP','TMP2','Cold','Hot','weekday','weekend','m_0','h_1'
               ],axis=1,inplace=True)
    model = model.reindex(sorted(model.columns), axis=1)
    return model

def modelLoad(D): # cutoff in Celsius
    os.mkdir(D['folder'])
    startTime= time.time()
    for region in fips:
        data = oneCounty(region,D)
        columns = data.columns
        X = data.drop('Load',axis=1)
        y = data.Load
        reg = D['model'].fit(X,y)
        joblib.dump(reg, D['folder']+'/'+str(region) + '_' + D['tag'] + '.joblib')
    joblib.dump(columns,D['folder']+'/'+'getLoadColumns_cutoff'+ D['tag'] + '.joblib')
    print(time.time() - startTime)

def calculateLoads(D):

    bigN = params['hours']*params['months']*params[D['name']][D['extreme_str']]
    t1 = time.time()
    temps = make2d(D,False)
    cutoff =  D['cutoff_C'] + 273
    temps['weekday'] = 1
    temps['weekend'] = 0

    loads = []
    if True:#D['extreme']:
        m = list(range(n_months)) + [0]*(24-n_months)
        h = list(range(24))
        fakedf = pd.DataFrame(data=[m,h],
                              index=['month','hour'],
                              columns=range(bigN,bigN+24)).transpose()
    else:
        h = list(range(24))
        fakedf = pd.DataFrame(data=[h],
                              index=['hour'],
                              columns=range(bigN,bigN+24)).transpose()

    for r in fips:
        print(r)
        df = temps[['month','hour','weekday','weekend',r]]
        df['TMP'] = df[r] + 273
        if D['center']:
            offset = -D['cutoff_C']
        else:
            offset = 273
        df['TMP2'] = (df[r]+offset)**2
        if D['nolowsquare']:
            df.loc[df.TMP < D['cutoff_low']+273, 'TMP2'] = 0
        df['Cold'] = np.where(df['TMP']<cutoff, 1, 0)
        df['Hot'] = np.where(df['TMP']>=cutoff, 1, 0)
        df.drop(r,axis=1,inplace=True)
        if True:#D['extreme']:
            df = pd.concat([df,fakedf])
        X = makeOneHot(df,False)
        cols = makeColumns(X)
        colnames = makeNames()
        model = pd.concat([X,pd.DataFrame(np.array(cols).transpose(), columns=colnames)],axis=1)
        # return model
        model.drop(['TMP','TMP2','Cold','Hot','weekday','weekend','m_0','h_1'
                   ],axis=1,inplace=True)
        if True:#D['extreme']:
            model.drop(range(bigN,bigN+24),inplace=True)
        model = model.reindex(sorted(model.columns), axis=1)
        reg = joblib.load(D['folder']+'/'+str(r) +'_'+ D['tag'] + '.joblib')
        loads.append(reg.predict(model.dropna()))

    load = np.sum(np.array(loads),0)
    print(load.shape)
    print('params',params)
    load = load.reshape(params[D['name']][D['extreme_str']],
                        params['months'],
                        params['hours']).transpose(1,2,0)
    print(time.time()-t1)
    np.save(D['load'],load)
    return load


def makeDF(D):
    loads = np.load(D['load'])
    print(loads.shape)
    temps = reshape3dto4d(D,False)
    means = copy.deepcopy(loads)
    mins = copy.deepcopy(loads)
    maxes = copy.deepcopy(loads)
    variances = copy.deepcopy(loads)
    mon = params['months']
    hou = params['hours']
    sim = params[D['name']][D['extreme_str']]
    print(temps.shape)
    for i in range(mon):
        for j in range(hou):
            for k in range(sim):
                means[i,j,k] = temps[:,i,j,k].mean()
                maxes[i,j,k] = temps[:,i,j,k].max()
                mins[i,j,k] =  temps[:,i,j,k].min()
                variances[i,j,k] = temps[:,i,j,k].var()

    df = pd.DataFrame(columns=['Load','Min','Mean','Max','Var','Month','Hour'])
    for i in range(mon):
        l = loads[i,:,:]
        mi = mins[i,:,:]
        m = means[i,:,:]
        M = maxes[i,:,:]
        v = variances[i,:,:]
        l = l.transpose(1,0).reshape(hou*sim)
        mi = mi.transpose(1,0).reshape(hou*sim)
        m = m.transpose(1,0).reshape(hou*sim)
        M = M.transpose(1,0).reshape(hou*sim)
        v = v.transpose(1,0).reshape(hou*sim)
        df1 = pd.DataFrame([l,mi,m,M,v],index=['Load','Min','Mean','Max','Var']).transpose()
        df1['Month'] = i
        df = pd.concat([df,df1])
    if True:# D['extreme']:
        df['Hour'] = df.index % 12
    else:
        df['Hour'] = df.index % 24
    return df


def make_scatter(data,D):
    # D = {data,var_scale,title,filename}
    if D['colorbyhour']:
        color = 'Hour'
    else:
        color = 'Month'
    for metric in ['Mean','Max','Min']:
        fig, ax = plt.subplots(figsize=(16,9),dpi=600)
        print(D['var_scale'])
        print(data['Var'].shape)
        print(data[metric].shape)
        print(data['Load'].shape)
        scatter = ax.scatter(data[metric],data['Load'],s=8*D['var_scale'],#s=data['Var']*D['var_scale'],
                             c=data[color])
        legend1 = ax.legend(*scatter.legend_elements(),
                           loc='lower right', title=color)
        ax.add_artist(legend1)

        # h, l = scatter.legend_elements(prop='sizes',alpha=1)
        # legend2 = ax.legend(h, l, loc='upper left',title='Var')
        # ax.add_artist(legend2)

        plt.title(D['title'] +'_'+ metric)
        plt.savefig(D['figname']+'_'+metric+'_'+color+'.png')
        # plt.show()

def makePlot(D):
    df = makeDF(D)
    make_scatter(df,D)


def runScript(D_input):
    # decisions
    center = True
    cutoff = 8
    nolowsquare = True
    month4 = True
    extreme = False
    colorbyhour = False
    wintershift = True
    alpha = 0.1

    model = Ridge(alpha=alpha)
    name = 'ridge'+str(alpha)
    tag = name +'_'+ 'c'+str(cutoff)
    if center:
        tag = tag + '_center'
    if month4:
        tag = tag+'_4month'
    if nolowsquare:
        tag = tag+'_nolow^2c'
    if wintershift:
        tag = tag+'_wintershift'
    D = {
        'cutoff_C':cutoff,
        'cutoff_low':cutoff,
        'model':model,
        'center':center,
        'nolowsquare':nolowsquare,
        'wintershift':wintershift,
        'tag':tag,
        'extreme':extreme,
        'colorbyhour':colorbyhour,
        'vline':cutoff,
        'hline':9500,
        'var_scale':1/16,
        'folder':'regression_'+tag
    }
    D.update(D_input)

    # modelLoad(D)
    calculateLoads(D)
    makePlot(D)


for extreme in ['extreme']:#,'normal']:
    for name in ['independent','proposal']:#,'test','unconditional','independent']:
        for alpha in npyNames['midwest'][name]:
            D_input = {'extreme':extreme == 'extreme',
                       'name':name,
                       'extreme_str':extreme,
                       'temps':npyNames['midwest'][name][alpha][extreme]['temps'],
                       'load':npyNames['midwest'][name][alpha][extreme]['loads'],
                       'figname':'graphs/full_'+extreme+'_'+name,
                       'title':'Predicted load, full '+npyNames['midwest'][name][alpha][extreme]['temps']
                       }
            runScript(D_input)


# D = {'extreme':False,
#      'load':'temp-and-load-sims/spatial_load_23years_part1.npy',
#      'temps':'temp-and-load-sims/spatial_simulations_23years_part1.npy',
#      'colorbyhour':False,
#      'var_scale':1/16,
#      'title':'Spatial normal part 1',
#      'figname':'spatial-normal-part-1.png'
#      }

# makePlot(D)
