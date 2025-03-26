#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy

file = 'needs-rev-06-06-2024.xlsx'
DF = pd.read_excel(file,sheet_name='NEEDS_Active')

#%%
df = copy.deepcopy(DF)
totalcapacity = df['Capacity (MW)'].sum()
print("num states =",len(df['State Name'].unique())) # + DC - AK - HI
print('PlantType:  ',df['PlantType'].unique())
print('Combustion Turbine/IC Engine:  ',df['Combustion Turbine/IC Engine'].unique())
print('Boiler/Generator/Committed Unit:  ',df['Boiler/Generator/Committed Unit'].unique())
print('Modeled Fuels:  ',df['Modeled Fuels'].unique())
df = df[['Plant Name','UniqueID_Final','Boiler/Generator/Committed Unit','Unit ID','CAMD Database UnitID','PlantType','Combustion Turbine/IC Engine','FIPS5','Capacity (MW)','Heat Rate (Btu/kWh)','Cogen?','Modeled Fuels']]

summary = df[['Capacity (MW)','PlantType']].groupby('PlantType').sum()
summary['pct'] = np.round(summary['Capacity (MW)'] / totalcapacity,4) * 100
summary.sort_values('pct',ascending=False)

#%%
categories = ['CombinedCycle','CombustionTurbine','Diesel','Hydroelectric','Nuclear','SteamTurbine','Wind','PV']

# map1 below is a natural matching of the NEEDS data to the appropriate model categories from the papers (Murphy 2019 and Rossmann 2025)
# All the mappings match either the models described in Rossmann 2025 (for wind and solar PV) or the data sources described by Murphy 2019 (everything else)
# One slight mismatch: steam turbines
# The vast majority of steam turbine plants are powered by coal, oil or natural gas (and it seems those powered by another source are always categorized separately by that fuel source, like biomass, waste, etc.).
# NEEDS distinguishes between coal-fired ("Coal Steam") and oil- or gas-fired ("O/G Steam"), but PJM/Murphy 2019 does not.
# According to Murphy 2019, 95% of the steam plants in their PJM data for 2017 were coal-fired, so they use "Steam" and "coal" interchangeably.
# I assume almost all the remaining 5% are oil and gas.
# Nationally, according to NEEDS, the split is 70% coal/30% oil and gas (code for this below).
# That means this map essentially applies coal steam outage patterns to oil and gas plants, which is probably not entirely fair plenty good enough.
# My only intuition on what kinds of inaccuracies this could lead to is the oil and gas plants tend to be smaller and probably older, both of which I think make them less reliable.
# For the purposes of this project, I think it is reasonable to apply PJM SteamTurbine rates to both coal steam and o/g steam.
coal = DF[DF['PlantType'] == 'Coal Steam']['Capacity (MW)'].sum()
og = DF[DF['PlantType'] == 'O/G Steam']['Capacity (MW)'].sum()
steam = coal + og
print('coal pct =', coal / steam)
print('o/g pct  =', og / steam)

map1 = {
    'Coal Steam': 'SteamTurbine',
    'O/G Steam': 'SteamTurbine',
    'Combustion Turbine': 'CombustionTurbine',
    'Hydro': 'Hydroelectric',
    'Onshore Wind': 'Wind',
    'Combined Cycle': 'CombinedCycle',
    'Solar PV': 'PV',
    'Nuclear': 'Nuclear',
    'Offshore Wind': 'Wind',
    'Pumped Storage': 'Hydroelectric',
}

# map2 is a next order approximation given the outage models already available.
# This is applying the models beyond their source data in ways that seem reasonable to me but come with inaccuracies.
# I describe my reasoning for each briefly below.
# I reference Table 3-7 of Chapter 3 of the NEEDS documentation, which is here: 
# https://www.epa.gov/power-sector-modeling/documentation-epas-power-sector-modeling-platform-v6-summer-2021-reference
# Note that the availability numbers in the table do not match the numbers reported in the PJM data in the Murphy paper that well.
# I am using Table 3-7 as a relative, not absolute, indicator of reliability and treating the PJM/Murphy data as absolute.
# My first guess as to the discrepancy is that Murphy et al exclude reserve shutdowns in the paper results and the NEEDS documentation probably includes them.
# The results in the Appendix to the Murphy paper (some of which include reserve shutdowns) match the NEEDS table better (see Figure B.14), though still not perfect.

# Biomass:
# Most (maybe all) biomass to electricity is done by burning the fuel in a steam turbine.
# see: https://www.eia.gov/energyexplained/biomass/
# The NEEDS documentation table suggests biomass reliability is pretty similar to coal steam, so I think this is a pretty good model.

# Municipal Solid Waste:
# This usually gets burned in a steam turbine.
# The NEEDS documentation here also suggests these are more reliable than a generic steam turbine, so it might make sense to scale down the outage rates while keeping the same temperature pattern.
# See: https://www.eia.gov/energyexplained/biomass/waste-to-energy-in-depth.php#:~:text=Waste%2Dto%2Denergy%20plants%20burn,and%20products%20made%20from%20wood.

# Landfill gas:
# This is tricky. I think there is a mix of generation technologies used (combustion turbine and internal combustion engine).
# The NEEDS data doesn't seem to distringuish between them.
# The NEEDS documentation suggests that landfill gas is fairly reliable, so I chose CombustionTurbine instead of Diesel (diesel generators are a type of internal combustion engine).

# IGCC:
# IGCC is a combined cycle plant (which are usually gas-fired) running on gassified coal, so the power generation technology is the same as CombinedCycle
# However, they wouldn't be affected by shortages in the gas network (which are implicitly modeled by the PJM/Murphy data),
# and gassified coal is probably affected by temperature in at least slightly different ways than natural gas is.
# The NEEDS documenation says IGCC availability is similar to regular coal, so the best choice might be to use CombinedCycle and SteamTurbine 50% each for IGCC
# Regardless there are only 2 of these facilities in existence with a total capacity of 815 MW,
# and it's unlikely that anyone will ever build one again, so it just doesn't matter that much.
map2 = {
    'Biomass': 'SteamTurbine',
    'Municipal Solid Waste': 'SteamTurbine',
    'Landfill Gas': 'CombustionTurbine',
    'IGCC': 'CombinedCycle',
}


# map3: The remaining technologies are challenging to match to our existing models.
# I'll give my ideas and reasoning, but they are pretty much only guesses.

# Energy Storage: This is the biggest remaining category (2.5% of total), and I don't have much intuition about their reliability.
# I guess that PV and Nuclear are the best matches for these. 
# Overall they are reliable, but heat is the main problem: it takes power to keep them cool, and there's not so much that can break in the cold.
# Unfortunately from the modeling perspective, it is probably somewhat important to be close on this given the rapid growth of batteries.

# Solar Thermal: This seems like it would be a reliable combination of PV and steam turbine
# They typically involve boiling water to make steam to turn a turbine (i.e., they contain a steam turbine)
# but they don't burn anything and are generally newer so I would guess more reliable than regular steam turbines.
# Also, they are probably helped in the cold (like PV) because of a larger temperature gradient.
# (This is true for steam turbines in general, but the data suggest that the bigger effect of cold is to break things.)

# Geothermal: The NEEDS documentation says these are about as reliable as combined cycle plants,
# and my intuition says they're affected by the heat (by lower temperature gradient) and the cold (by things breaking),
# which is about what happens to combined cycle plants.
# These typically have a steam turbine as the main generator, but are more reliable than typical steam turbines.

# Fossil Waste and Non-Fossil Waste:
# I know very little about this but I think both tend to involve burning waste for a steam turbine.

# Tires:
# there are so few it's probably not worth it to model this, but I'd guess this involves burning tires for a steam turbine.

# Fuel cell:
# These run on gas and are reliable according to NEEDS documentation, though have little resemblance to a combined cycle plant

map3 = {
    'Fossil Waste': 'SteamTurbine',
    'Non-Fossil Waste': 'SteamTurbine',
    'Geothermal': 'CombinedCycle',
    'Solar Thermal': 'PV', 
    'Energy Storage': 'Nuclear', 
    'Tires': 'SteamTurbine',
    'Fuel Cell': 'CombinedCycle',
}

fullmap = {**map1, **map2, **map3}

data = copy.deepcopy(df[['PlantType','Combustion Turbine/IC Engine','Modeled Fuels','Capacity (MW)']])
data['type'] = list(zip(df['PlantType'],df['Combustion Turbine/IC Engine'],df['Modeled Fuels']))
data['category'] = data['PlantType'].map(fullmap)
remaining = data[pd.isna(data['category'])]
summary = remaining[['Capacity (MW)','type']].groupby('type').sum()
summary['pct'] = np.round(summary['Capacity (MW)'] / totalcapacity,4) * 100
summary.sort_values('pct',ascending=False)

data['mapping'] = list(zip(data['PlantType'], data['category']))
mapsum = data[['Capacity (MW)','mapping']].groupby('mapping').sum()
mapsum['pct'] = np.round(mapsum['Capacity (MW)'] / totalcapacity,4) * 100
mapsum.sort_values('pct',ascending=False)

# %%
NonFossilSteamTurbines = ['Biomass', 'Geothermal', 'Non-Fossil Waste', 'Municipal Solid Waste', 'Solar Thermal', 'Fossil Waste', 'Tires']
nfst = df[df['PlantType'].isin(NonFossilSteamTurbines)]
nfstcap = nfst['Capacity (MW)'].sum()
print("nfst pct =",nfstcap / totalcapacity)
