import numpy as np
import pandas as pd
from cfg import fipswi, fips6, params

fips = fips6

def extendTemps(temps):
    IL = 102
    IN = 92
    IA = 99
    MI = 83
    MN = 87
    WI = 72
    ia = list(np.array([0]*(IA*4*12*2100)).reshape(IA,4,12,2100))
    mn = list(np.array([0]*(MN*4*12*2100)).reshape(MN,4,12,2100))
    T = np.array(list(temps[:IL+IN])+ia+list(temps[IL+IN:IL+IN+MI])+mn+list(temps[IL+IN+MI:]))
    return T

def splitNormal():
    temps = np.load('temp-and-load-sims/spatial_simulations_23years.npy')
    loads = np.load('temp-and-load-sims/spatial_load_23years.npy')
    testT = temps[:,:,:,:12]
    testL = loads[:,:,:1092]
    trainT = temps[:,:,:,12:]
    trainL = loads[:,:,1092:]
    np.save('temp-and-load-sims/spatial_simulations_23years_part1.npy',testT)
    np.save('temp-and-load-sims/spatial_load_23years_part1.npy',testL)
    np.save('temp-and-load-sims/spatial_simulations_23years_part2.npy',trainT)
    np.save('temp-and-load-sims/spatial_load_23years_part2.npy',trainL)

def make2d(D,save):
    temps = reshape3dto4d(D,False)
    hours,months,sims = temps.shape[2],temps.shape[1],temps.shape[3]
    temps = temps.transpose(3,2,1,0)
    h_factor = 2
    temps = np.insert(temps,0,[[h_factor*i] for i in range(hours)],axis=3) # hours
    temps = temps.transpose(0,2,1,3)
    temps = np.insert(temps,0,[[i] for i in range(months)],axis=3) # months
    temps = temps.transpose(1,0,2,3)
    temps = np.insert(temps,0,[[i] for i in range(sims)],axis=3) # simulations
    temps = temps.transpose(3,1,0,2)
    temps = temps.reshape(535+3,hours*months*sims)
    df = pd.DataFrame(temps,index=['sim','month','hour']+fips).transpose()
    df['sim'] = df['sim'].astype(int)
    df['month'] = df['month'].astype(int)
    df['hour'] = df['hour'].astype(int)
    if D['extreme']:
        df.loc[df.month == 1,'month'] = 0
        df.loc[df.month == 2,'month'] = 2
        df.loc[df.month == 3,'month'] = 2
    if save:
        df.to_pickle(D['filename2d'])
    return df

def reshape3dto4d(D,save):
    temps = np.load(D['temps'])
    if 'fivestate' in D['temps']:
        temps = extendTemps(temps)

    if not D['extreme']: # reshape and remove dec 31
        temps = temps[:,:364,:,:]
        temps = temps.transpose(0,3,2,1)
        d = 31
        for i in range(len(temps)):
            for j in range(len(temps[i])):
                for k in range(len(temps[i][j])):
                    temps[i][j][k] = np.concatenate((temps[i][j][k][364-d:],temps[i][j][k][:364-d]))
        s = temps.shape
        tot = s[0]*s[1]*s[2]*s[3]
        years = int(tot/535/12/91/4)
        temps = temps.reshape(535,12,years,91,4)
        temps = temps.transpose(0,1,3,4,2)
        scens = int(tot/535/12/4)
        temps = temps.reshape(535,12,4,scens)
        temps = temps.transpose(0,2,1,3)

    # shift to correct time
    temps = temps.transpose(0,1,3,2)
    shape = temps.shape
    for i in range(shape[0]):
        for j in range(shape[1]):
            for k in range(shape[2]):
                a = temps[i,j,k,:]
                b = np.append(a[3:], a[:3])
                temps[i,j,k,:] = b
    temps = temps.transpose(0,1,3,2)

    return temps



def make2d_old(D,save):
    temps = reshape3dto4d_old(D,False)
    hours,months,sims = params[D['extreme']]['hours'],params[D['extreme']]['months'],params[D['extreme']]['sims']
    temps = temps.transpose(3,2,1,0)
    if D['extreme']:
        h_factor = 2
    else:
        h_factor = 1
    temps = np.insert(temps,0,[[h_factor*i] for i in range(hours)],axis=3) # hours
    temps = temps.transpose(0,2,1,3)
    temps = np.insert(temps,0,[[i] for i in range(months)],axis=3) # months
    temps = temps.transpose(1,0,2,3)
    temps = np.insert(temps,0,[[i] for i in range(sims)],axis=3) # simulations
    temps = temps.transpose(3,1,0,2)
    temps = temps.reshape(535+3,hours*months*sims)
    df = pd.DataFrame(temps,index=['sim','month','hour']+fips).transpose()
    df['sim'] = df['sim'].astype(int)
    df['month'] = df['month'].astype(int)
    df['hour'] = df['hour'].astype(int)
    if D['extreme']:
        if params[False]['months'] == 13:
            df.loc[df.month == 2,'month'] = 6
            df.loc[df.month == 3,'month'] = 7
        elif  params[False]['months'] == 7:
            df.loc[df.month == 1,'month'] = 0
            df.loc[df.month == 2,'month'] = 3
        else: # == 4
            df.loc[df.month == 1,'month'] = 0
            df.loc[df.month == 2,'month'] = 2
            df.loc[df.month == 3,'month'] = 2
    if save:
        df.to_pickle(D['filename2d'])
    return df



def reshape3dto4d_old(D,save):
    # shift and reshape normal temp 3d to 4d to df pickle
    n = params[D['extreme']]['months']
    temps = np.load(D['temps'])
    if D['extreme']:
        temps = temps.transpose(0,1,3,2)
        for i in range(len(fips)):
            for j in range(params[True]['months']):
                for k in range(params[True]['sims']):
                    a = temps[i,j,k,:]
                    b = np.append(a[3:], a[:3])
                    temps[i,j,k,:] = b
        temps = temps.transpose(1,2,0,3)
        temps = temps.transpose(2,0,3,1)
    else:
        n_years = 29# temps.shape[3]
        temps = temps[:,6:8760-18,:]
        c = temps.shape[0] # number of counties
        # if D['wintershift']:
        temps = np.roll(temps,24*31,axis=1)
        temps = temps.transpose(0,2,1).reshape([c,n_years,n,int(8736/n)])
        temps = temps.transpose(0,2,1,3).reshape([c,n,n_years,int(8736/n/24),24])
        temps = temps.transpose(0,1,4,3,2).reshape([c,n,n_years,int(8736/24*n_years/n)])
    if save:
        np.save(D['filename4d'],temps)
    return temps


def reshape2dto4dload():
    d = np.load('load_counties_wi_2d_cutoff20.npy')
    print(d.shape)
    d = d.reshape(812,13,24)
    d = d.transpose(1,2,0)
    print(d.shape)


def reshape2dto4dtemp():
    df = pd.read_pickle('temp_counties_wi_2d')
    df = df[['sim','month','hour',55001]]
    d = df.to_numpy()
    print(d.shape)
    d = d.transpose(1,0)
    d = d.reshape(4,812,13,24)
    d = d.transpose(0,2,3,1)
    print(d.shape)
    pd.DataFrame(d[:,0,:,0]).transpose()


def makeIndSamples(tfile):
    if 'spatial' not in tfile:
        print('non-spatial simulations?')
    else:
        # making normal independent samples
        # shuffle years differently for each county (then go remake load predictions separately)
        seed = 10000
        temps = reshape3dto4d({'extreme':False,'temps':tfile},False)
        temps = temps.transpose(1,0,3,2)
        temps.shape
        np.random.seed(seed)
        for i in range(4):
            for r in range(535):
        #     make sure months are shuffling in different ways
                np.random.shuffle(temps[i][r])
        temps = temps.transpose(1,0,3,2)
        np.save(tfile.replace('spatial','independent'),temps)
        temps.shape
