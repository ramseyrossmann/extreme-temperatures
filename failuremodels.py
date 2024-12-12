#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random, bisect

#%% notes
# all temperatures are Celsius except where stated otherwise (wind modeling)
# Solar:
# The solar model is deterministic and requires a base capacity factor (set to basecf=1 for demonstration purposes) as an input.
# The base capacity factor is a proxy for irradiance and can be sampled separately to model uncertainty.
# In the paper, this was selected by the scenario's hour of the year.

#%% data setup
# required data for conventional outages
rates = pd.read_csv('extra/temperture_dependent_rates_linear.csv').set_index('Temp')
t_index = list(rates.index)
r = rates.to_dict()
basecf = 1 # base capacity factor for solar (irradiance proxy)

# relevant technology names from rates table
conventional = ['CC','CT','NU','ST','DS','HD']
# all technologies modeled
technologies = ['wind','solar'] + conventional
# names for printing
map_tech_name = {
    'wind': 'Wind',
    'solar': 'Solar',
    'CC': 'Combined Cycle',
    'CT': 'Combustion Turbine',
    'NU': 'Nuclear',
    'ST': 'Coal steam',
    'DS': 'Diesel',
    'HD': 'Hydro'
}

#%% modeling functions
# solar is deterministic given a temperature and base capacity factor
# the base capacity factor is a proxy for irradiance
# the function returns an adjusted capacity factor (Z)
def solarfunction(temperature,basecapacityfactor):
    NOCT = 45
    eff = .18
    eta = 0.005
    Z = 1 - (temperature + (NOCT - 20) / 800 * basecapacityfactor / eff - 25) * eta
    return Z


# wind: only affects capacity between off and on temperatures
def windfunction(temperature):
    on = -20 # -20 Fahrenheit
    off = -30 # -30 Fahrenheit
    ratio = 0.1
    k = 0.1
    temperatureF = temperature * 9/5 + 32

    if temperatureF >= on:
        Z = 1
    elif temperatureF <= off:
        Z = 0
    else:
        q = getP_failure(temperatureF,on,off,ratio)
        Z = max(0, 1-np.random.normal(q, q*(1-q)*k))
    return Z

def getP_failure(t,on,off,ratio):
    dT = on-off
    b = -off+dT*ratio
    a = (off+b)*(on+b) / dT
    c = -a / (on+b)
    p_fail = a / (t + b) + c
    return p_fail


# conventional: interpolates data in table (if necessary) to find outage rate at temperature
def conventionalfunction(temperature, technology):
    outagerate = t_interp(temperature,technology)
    prob = random.uniform(0,1)
    Z = int(prob >= outagerate)
    return Z

def t_interp(t,tech):
    if t in t_index:
        return r[tech][t]
    else:
        b = bisect.bisect(t_index,t)
        low = t_index[b-1]
        high = t_index[b]
        return np.interp(t,(low,high),(r[tech][low],r[tech][high]))


# calls the appropriate function based on temperature and technology
def getcapacityfactor(temperature,technology):
    if technology == 'solar':
        Z = solarfunction(temperature,basecf)
    elif technology == 'wind':
        Z = windfunction(temperature)
    elif technology in conventional:
        Z = conventionalfunction(temperature,technology)
    return Z

#%% Sample data to produce approximate availability curves
def runsample():
    random.seed(1)
    temperatures = [random.randint(-40, 50) for i in range(10)]
    temperatures = np.linspace(-40,50,100001)
    outages = [[getcapacityfactor(temp,tech) for temp in temperatures] for tech in technologies]
    df = pd.DataFrame(columns=temperatures, index=technologies, data=outages).transpose().reset_index().rename({"index":"temp"},axis=1)
    df["T"] = df["temp"].round()
    gb = df.groupby('T').mean()
    for tech in technologies:
        plt.figure(figsize=(5,3), dpi=200)
        plt.scatter(x=gb.index, y=gb[tech])
        plt.xlabel("Temperature (C)")
        plt.ylabel("Capacity factor")
        plt.title(map_tech_name[tech]+' availability')
        plt.show()
# runsample()

#%% generator and capacity factor info
# from methods_pickle import loadPickle
# gams = loadPickle('pickles/gams-data-midwest')

# generator locations: gams['map_uid_fips'] = dictionary mapping unit id to unit's location
# generator technology: gams['map_uid_type'] = dictionary mapping unit id to unit's technology
# original source for generator info is EPA NEEDS, which has newer versions online

# capacity factor sample: gams['cf'][(t, f, h)] = capacity factor for hour h in fips location f for technology t
#   hours span 1 year ([1,8760]); those not included are 0.
#   fips locations are available for counties in MN, IA, WI, IL, IN, MI
#   technologies include 'Onshore_Wind' and 'SolarUtil' (among others)
