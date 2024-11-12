#!/usr/bin/env python3
import pickle

with open('pickles/gams-data-midwest.pkl', 'rb') as f:
    gams = pickle.load(f)

# with open('pickles/gams-data-wi.pkl', 'rb') as f:
#     gams_wi = pickle.load(f)


L = {
     # 'cost_types': ['operating','shedding','capital','retire'],
     'cost_types':['operating','shedding','capital','capital-old','capital-new-conventional','capital-new-renewable'],
     'solar': ['SolarDistUtil','SolarUtil'],
     'wind': ['Onshore_Wind','Offshore_Wind'],
     'gen_retire': ['Combined_Cycle', 'Combustion_Turbine','Coal_Steam','Nuclear','Onshore_Wind'],
     'gen_thermal': ['Combined_Cycle', 'Combustion_Turbine', 'Landfill_Gas', 'OG_Steam', 'Biomass','Coal_Steam','Nuclear', 'Non_Fossil_Waste'],
     'gen_fuel': ['Combined_Cycle', 'Combustion_Turbine', 'Landfill_Gas', 'OG_Steam', 'Biomass','Coal_Steam','Non_Fossil_Waste','Nuclear'],
     'gen_gas': ['Combined_Cycle', 'Combustion_Turbine', 'Landfill_Gas'],
     }
L['gen_cf'] = L['solar'] + L['wind']
L['gen'] = gams['gen'] + L['solar'] + ['Offshore_Wind']
L['Murphy'] = {
    'Combined_Cycle':'CC',
    'IGCC':'CC',
    'Combustion_Turbine':'CT',
    'Pumped_Storage':'HD',
    'Hydro':'HD',
    'Nuclear':'NU',
    'Coal_Steam':'ST',
    'OG_Steam':'ST'
    }

L['Murphy-list'] = ['CC','CT','HD','NU','ST'] # no 'DS' gens, so not included




gams['zuid'] = [u for u in gams['uid'] if gams['map_uid_type'][u] in L['gen_retire'] ]
keys = ['uid','zuid','capcost_nrel','map_uid_type','cap','hr','cap_nrel','map_uid_fips','map_fips_state']
G = {g:gams[g] for g in keys}

current_fleet = {g: gams['oldFleet'].get(g, 0) for g in set(gams['gen']+L['gen_cf'])}
with open('pickles/current_fleet.pkl','wb') as f:
    pickle.dump(current_fleet,f)

with open('pickles/L.pkl','wb') as f:
    pickle.dump(L,f)

with open('pickles/G.pkl','wb') as f:
    pickle.dump(G,f)

with open('pickles/tags.pkl','wb') as f:
    pickle.dump(['min','med','max'],f)
