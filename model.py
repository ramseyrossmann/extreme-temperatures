#!/usr/bin/env python3
import gurobipy as gp
from gurobipy import GRB
import numpy as np

def calculateM(S,S_e,P,G):
    satisfied = []
    cf_dict = P['cf_dict']
    Ymax = {(g, r): max([S[s]['factor'][g, r][cf_dict[g]] for s in S_e]) for (g,r) in G['capcost_nrel'].keys()}
    if True:
        gp.setParam('OutputFlag', 0)
        bigM = {}
        demands = np.sort([S[s]['load']* P.get('demand_scale',1) for s in S_e])
        index = np.ceil((1-P['Ulist'][0])*(len(demands) - 1))
        print(index)
        D = demands[int(np.ceil((1-P['Ulist'][0])*(len(demands) - 1)))]
        print('D',D)
        print('demands')
        for i in range(len(demands)):
            print(i,demands[i])
        model = gp.Model('bigM')
        Z = model.addVars(G['zuid'], name='Z', vtype=GRB.BINARY)
        # for u in G['zuid']:
        #     Z[u].ub = 1
        Y = model.addVars(G['capcost_nrel'].keys(), name='Y', vtype=GRB.CONTINUOUS)

        for (g, r) in G['cap_nrel'].keys():
            Y[g, r].ub = G['cap_nrel'][g, r]
        model.addConstr(sum( Z[u]*G['cap'][u]  for u in G['zuid'])
                    + sum( Y[g,r]*Ymax[g, r] for (g, r) in G['capcost_nrel'] )
                    + sum( G['cap'][u] for u in G['uid'] if u not in G['zuid'])
                    >= D )
        for s in S_e:
            model.setObjective(sum(Z[u]*S[s]['cap'][u] for u in G['zuid'])
                           + sum(Y[g, r]*S[s]['factor'][g, r][cf_dict[g]] for (g, r) in G['capcost_nrel'])
                                 + sum( G['cap'][u] for u in G['uid'] if u not in G['zuid']),
                           GRB.MINIMIZE)
            model.optimize()
            Mk = S[s]['load']* P.get('demand_scale',1) - model.getAttr('ObjVal')
            if Mk < 0:
                satisfied.append(s)
            else:
                bigM[s] = max(Mk,0)
        print('len(satisfied) =', len(satisfied))
    else:
        bigM = {s:S[s]['load']* P.get('demand_scale',1) for s in S_e}
        D = max(bigM.values())
    return bigM, satisfied, D, Ymax

def train(inputs):
    Ss = inputs['S']
    P = inputs['P']
    G = inputs['G']
    L = inputs['L']
    NEW = inputs['new']
    if P.get('new',False):
        OFF = inputs['off'] # needs to be selected a priori for temperature dependence or not
        good_cc = inputs['good_CC']
        good_ct = inputs['good_CT']
    else:
        good_cc = []
        good_ct = []
    cf_dict = P['cf_dict']
    i = list(Ss.keys())[0]
    S = Ss[i]
    if P['temperature-dependent']:
        capkey = 'cap'
    else:
        capkey = 'cap-for'
    if P['exclude-extremes']:
        for s in S:
            S[s]['q'] = S[s]['qval'][P['cvar']]
    S_n = [s for s in S.keys() if not S[s]['extreme']]
    # gp.setParam('OutputFlag', 0)
    m = gp.Model('main')
    m.Params.SolFiles = "S"+str(i)+"_U"+str(P['Ulist'][0])
    m.setParam('TimeLimit',P['TimeLimit']) # 6 hours
    z = m.addVars(G['zuid'], name='z', vtype=GRB.BINARY)
    y = m.addVars(G['capcost_nrel'].keys(), name='y', vtype=GRB.CONTINUOUS)
    x = m.addVars(S_n, G['uid'], name='x', vtype=GRB.CONTINUOUS)
    shed = m.addVars(S.keys(), name='shed', vtype=GRB.CONTINUOUS)
    costs = m.addVars(L['cost_types'], name='costs', vtype=GRB.CONTINUOUS)

    if P.get('new',False):
        znew = m.addVars( NEW['options'], name='znew', vtype=GRB.BINARY)
        xnew = m.addVars( [(s,g,r) for s in S_n for (g,r) in NEW['options']], name='xnew', vtype=GRB.CONTINUOUS)
    else:
        znew = []
        xnew = []

    if P['name'] == 'base':
        extreme_eq = m.addConstr((1/P['cost_shed']) * costs['shedding'] == sum(shed[s] * S[s]['q'] for s in S_n ) )
        S_e = []
        w = None # to be able to pass w to solve
    else:
        S_e = [s for s in S.keys() if S[s]['extreme']]
        if P['parameter-type'] == 'objective': # varying lambda
            if P['fixed-lambda']:
                S_obj = S_e
                m.addConstr((1/P['cost_shed']) * costs['shedding'] == sum(shed[s] * S[s]['q'] for s in S_n ) )
            else:
                S_obj = S
            if P['cvar'] > 0:
                w = m.addVars(S_obj, name='w', vtype=GRB.CONTINUOUS)
                gamma = m.addVar(name='gamma')
                m.addConstrs((w[s] >= shed[s] - gamma for s in S_obj), name='cvar')
                extreme_eq = m.addConstr((1/P['cost_shed']) * costs['shedding'] == gamma + (1/P['cvar']) * sum(w[s]*S[s]['q'] for s in S_obj))
            else:
                extreme_eq = m.addConstr((1/P['cost_shed']) * costs['shedding'] == sum(shed[s] * S[s]['q'] for s in S_obj ) )
                w = None # to be able to pass w to solve
        elif P['parameter-type'] == 'constraint': # varying U
            if P['risk-measure'] == 'cvar':
                if P['cvar'] > 0:
                    w = m.addVars(S_e, name='w', vtype=GRB.CONTINUOUS)
                    gamma = m.addVar(name='gamma')
                    m.addConstrs((w[s] >= shed[s] - gamma for s in S_e), name='cvar')
                    extreme_eq = m.addConstr(gamma + (1 / P['cvar']) * sum(w[s] * S[s]['q'] for s in S_e) <= 0 )
                    # 1 / P['cvar'] should be ~ 1 / epsilon
                else:
                    extreme_eq = m.addConstr(sum(shed[s] * S[s]['q'] for s in S_e ) <= 0 )
            elif P['risk-measure'] == 'lolp':
                M, satisfied, D, Ymax = calculateM(S,S_e,P,G)

                m.addConstr(sum( z[u]*G['cap'][u]  for u in G['zuid'])
                            + sum( y[g, r]*Ymax[g, r] for (g, r) in G['capcost_nrel'] )
                            + sum( G['cap'][u] for u in G['uid'] if u not in G['zuid'])
                            >= D )

                newS_e = list(M.keys())
                # newS_e = S_e
                w = m.addVars(S_e, name='w', vtype=GRB.BINARY)
                m.addConstrs((shed[s] <= M[s]*(1-w[s]) for s in newS_e), name='failure')
                alpha = P['Ulist'][0]
                # extreme_eq = m.addConstr( sum( w[s] for s in newS_e) >= np.ceil( len(S_e)*(1-alpha) ) - (len(S_e) - len(newS_e)), name='lolp')
                extreme_eq = m.addConstr( sum( w[s] for s in S_e) >= np.ceil( len(S_e)*(1-alpha) ), name='lolp')
                print('alpha =', alpha)
                print('satisfied:',satisfied)
                print('newS_e:', newS_e)
                print('bigM')
                for s in M:
                    print(s,M[s])
            m.addConstr(costs['shedding'] == P['cost_shed']*sum(shed[s] * S[s]['q'] for s in S_n ) )
        for s in S_e: # extreme capacity and binary constraints
            m.addConstr(shed[s] >= S[s]['load'] * P.get('demand_scale',1)
                         - sum( z[u] * S[s][capkey][u] for u in G['zuid'] )
                         - sum( S[s][capkey][u] for u in G['uid'] if u not in G['zuid'])
                         - sum( y[g, r]*S[s]['factor'][g, r][cf_dict[g]] for (g, r) in G['capcost_nrel'].keys())
                         - sum( znew[g,r] * NEW['cap'][g]*(1-OFF[s].get((g,r),0)) for (g,r) in znew)
                         )

    m.addConstr(costs['capital-new-renewable'] ==
                (1/8760) * sum(y[g, r]*G['capcost_nrel'][g, r] for (g, r) in G['capcost_nrel'].keys()),
                'capital-costs')

    m.addConstr(costs['capital-old'] ==
                (1/8760) * P.get('incumbency-factor',1) / P['time_horizon'] * sum(
                    z[u]*G['cap'][u]*P['capital_cost'][G['map_uid_type'][u]] for u in G['zuid']
                    if u not in good_cc if u not in good_ct),
                'incumbent-capital-costs')

    m.addConstr(costs['capital-new-conventional'] ==
                (1/8760) / P['time_horizon'] * sum(
                    znew[g,r] * NEW['cap'][g] * P['capital_cost'][NEW['map_model_type'][g]] for (g,r) in znew),
                'capital-new-steam')

    m.addConstr(costs['capital'] ==
                costs['capital-new-renewable'] + costs['capital-old'] + costs['capital-new-conventional'],
                'capital-all')

    m.addConstr(costs['operating'] == sum(S[s]['q'] * P['fuel'][G['map_uid_type'][u]] * G['hr'][u] * x[s, u]
                for u in G['uid'] for s in S_n if G['map_uid_type'][u] in L['gen_fuel'])
                + sum( S[s]['q'] * P['fuel'][NEW['map_model_type'][g]] * NEW['hr'][g] * xnew[s,g,r]
                      for (s,g,r) in xnew),# if g != 'Nuclear'),
                'operating-costs') # takes LONG time

    for (t, r) in G['cap_nrel'].keys():
        y[t, r].ub = G['cap_nrel'][t, r]

    for s in S_n:
        m.addConstr(S[s]['load'] * P.get('demand_scale',1) - shed[s]
                    <= sum(x[s, u] for u in G['uid'])
                    + sum(y[g, r]*S[s]['factor'][g, r][cf_dict[g]] for (g, r) in G['capcost_nrel'].keys())
                    + sum(xnew[s,g,r] for (g,r) in znew ),
                    'demand')

    for s in S_n: # normal capacity and binary constraints
        for u in G['uid']:
            if u in G['zuid']:
                m.addConstr( x[s, u] <= z[u] * S[s][capkey][u], 'capacity-z')
            else:
                x[s, u].ub = S[s][capkey][u]
        for (g,r) in znew:
            m.addConstr( xnew[s,g,r] <= znew[g,r] * NEW['cap'][g]*(1-OFF[s].get((g,r),0) ), 'capacity-znew')

    m.setObjective(costs['operating'] + costs['shedding'] + costs['capital'], GRB.MINIMIZE)

    # SCALING DOWN MODEL
    # i = 0
    # for (t, r) in G['cap_nrel'].keys():
        # removing one kind of solar
        # if t == 'SolarDistUtil':
        #     y[t,r].ub = 0
        #     y[t,r].lb = 0
        # turning off every other county's remaining solar
        # if t == 'SolarUtil':
        #     i = i+1
        #     if i % 2 == 0:
        #         y[t,r].ub = 0
        #         y[t,r].lb = 0
        # # removing IA and MN
        # if G['map_fips_state'][r] in ['IA','MN']:
        #     y[t,r].ub = 0
        #     y[t,r].lb = 0

    ct = 0
    cc = 0
    coal = 0
    numDecisions = 0
    if P.get('new',False):
        factor = 20000 # 2
    else:
        factor = 1
    for u in G['zuid']:
        # turning on half/all of CTs
        if G['map_uid_type'][u] == 'Combustion_Turbine':
            ct = ct+1
            if ct % factor == 0:
                z[u].ub = 1
                z[u].lb = 1
                numDecisions = numDecisions + 1
        # turning on half/all of CCs
        if G['map_uid_type'][u] == 'Combined_Cycle':
            cc = cc+1
            if cc % factor == 0:
                z[u].ub = 1
                z[u].lb = 1
                numDecisions = numDecisions + 1
        # turning off half/all of coal
        if G['map_uid_type'][u] == 'Coal_Steam':
            coal = coal+1
            if coal % factor == 0:
                z[u].ub = 0
                z[u].lb = 0
                numDecisions = numDecisions + 1
    print("Number of decisions made a priori =",numDecisions)

        # removing IA and MN
        # if G['map_uid_fips'][u] in ['IA','MN']:
            # z[u].ub = 0
            # z[u].lb = 0

    # # New down-scaling approach: turn on good generators ahead of time
    # for u in good_cc: # good combined cycles
    #     z[u].ub = 1
    #     z[u].lb = 1
    # for u in good_ct: # good combustion turbines
    #     z[u].ub = 1
    #     z[u].lb = 1
    if P.get('new',False):
        # Remove 3/4 of znew options
        fips = np.sort(list(set(r for (g,r) in NEW['options'])))
        for j in range(len(fips)):
            if j % 4 != 0:
                for g in NEW['gens']:
                    znew[g,r].ub = 0
                    znew[g,r].lb = 0

    m.update()
    solutions = {U:{s:dict() for s in ['y','z','znew']} for U in P['Ulist']}
    data = {U:{s:dict() for s in ['stats','shed','cost']} for U in P['Ulist']}
    data.update({'i':i})
    for U in P['Ulist']:
        solve(S,P,G,L,m,i,extreme_eq,w,x,y,z,znew,xnew,shed,gamma,S_e,S_n,costs,solutions,data,U)
    return solutions,data,m

def solve(S,P,G,L,m,i,extreme_eq,w,x,y,z,znew,xnew,shed,gamma,S_e,S_n,costs,solutions,data,U):
    if not P.get('relocate',False):
        if P['parameter-type'] == 'objective':
            m.chgCoeff(extreme_eq,costs['shedding'],1/U)
        elif P['risk-measure'] == 'cvar':
            m.setAttr('RHS', extreme_eq, U)
            m.update()
        elif P['risk-measure'] == 'lolp':
            RHS = np.ceil( len(S_e)*(1-U) )
            print('U =', U)
            m.setAttr('RHS', extreme_eq, RHS )
            m.update()

    m.optimize()

    status = m.getAttr('Status')
    if status == GRB.TIME_LIMIT:
        print('Time limit reached')
        data[U]['stats']['solved'] = False
    elif status == GRB.INFEASIBLE:
        print('Infeasible')
        data[U]['stats']['solved'] = False
    else:
        data[U]['stats']['solved'] = True

    if m.getAttr('SolCount') > 0:
        # w_vals = [var for var in m.getVars() if "w" in var.VarName]

        if P.get('relocate',False):
            var_names = []
            var_values = []
            for var in m.getVars():
                if var.X > 0 and 'x' not in str(var.varName):
                    var_names.append(str(var.varName))
                    var_values.append(var.X)
                elif 'cost' in var.varName:
                    var_names.append(str(var.varName))
                    var_values.append(var.X)
            for i in range(len(var_names)):
                print(var_names[i],var_values[i])

        # saving training solution and cost
        else:
            cost_vals = [var for var in m.getVars() if "cost" in var.VarName]
            print('COST VALUES')
            for i in range(len(cost_vals)):
                print(cost_vals[i])
            solutions[U]['y'].update({(g, r): y[g, r].X for g, r in G['capcost_nrel'].keys()})

            # print('W VALUES')
            # shed_vals = [var for var in m.getVars() if "shed" in var.VarName]
            # for i in range(len(w_vals)):
                # print(w_vals[i],shed_vals[i])

            solutions[U]['z'].update({u: z[u].X for u in G['zuid']})
            solutions[U]['znew'].update({g: znew[g].X for g in znew})
            data[U]['shed'].update({'extreme':{s:shed[s].X for s in S_e},
                                    'normal':{s:shed[s].X for s in S_n}})
            data[U]['stats'].update({'cost_'+g: round(costs[g].X, 1) for g in L['cost_types']})
            data[U]['stats'].update({'objective':round(m.getAttr('ObjVal'),2),
                                     'shed_N': np.mean([data[U]['shed']['normal'][s] for s in S_n]),
                                     'shed_E': [data[U]['shed']['extreme'][s]  for s in S_e],
                                     # might not be tight in constraint model^
                                     'scenarios_N': len(S_n),
                                     'scenarios_E': len(S_e)*int(P['name'] != 'base'),
                                     'NodeCount':m.getAttr('NodeCount'),
                                     'NumConstrs':m.getAttr('NumConstrs'),
                                     'NumVars':m.getAttr('NumVars'),
                                     'NumNZs':m.getAttr('NumNZs'),
                                     'Runtime':m.getAttr('Runtime'),
                                     'TimeLimit':P['TimeLimit'],
                                     'Gap':m.MIPGap,
                                     'Bound':m.ObjBound,
                                     'SolCount':m.getAttr('SolCount'),
                                     })
            print('U =',U)
            print('gamma =',gamma)
            # print('znew',znew)
            print('extreme shed')
            for k in data[U]['shed']['extreme']:
                print(k,data[U]['shed']['extreme'][k])
        if P['name'] == 'base':
            data[U]['stats']['shed_E'] = data[U]['stats']['shed_N'] # for plotting purposes


def normalTest(inputs):
    P = inputs['P']
    S = inputs['S']
    G = inputs['G']
    L = inputs['L']
    NEW = inputs['new']
    if P.get('new',False):
        OFF = inputs['off']
    cf_dict = P['cf_dict']
    solutions = inputs['solutions']
    gp.setParam('OutputFlag', 0)
    y = solutions['y']
    z = solutions['z']
    znew = solutions['znew']
    non_z_gen = [u for u in G['uid'] if u not in G['zuid']]
    results = {key: None for key in S.keys()}

    for key in S.keys():
        s = S[key]
        n = gp.Model('normal')
        x = n.addVars(G['uid'], name='x', vtype=GRB.CONTINUOUS)
        xnew = n.addVars( znew, name='xnew', vtype=GRB.CONTINUOUS)
        shed = n.addVar(name='shed', vtype=GRB.CONTINUOUS)
        cost = n.addVar(name='operating cost', vtype=GRB.CONTINUOUS)

        n.addConstr(cost == sum(P['fuel'][G['map_uid_type'][u]] * G['hr'][u] * x[u]
                    for u in G['uid'] if G['map_uid_type'][u] in L['gen_fuel'])
                     + sum( P['fuel'][NEW['map_model_type'][g]] * NEW['hr'][g] * xnew[g,r]
                           for (g,r) in xnew ),# if g != 'Nuclear'),
                    'operating-costs')

        n.addConstr(s['load'] * P.get('demand_scale',1) - shed
                    <= sum(x[u] for u in G['uid'])
                    + sum(y[g, r]*s['factor'][g, r][cf_dict[g]] for (g, r) in G['capcost_nrel'].keys())
                    + sum( xnew[g,r] for (g,r) in xnew ),
                    'demand')

        for u in G['zuid']:
            x[u].ub = z[u] * s['cap'][u]
        for u in non_z_gen:
            x[u].ub = G['cap'][u]
        for (g,r) in xnew:
            xnew[g,r].ub = znew[g,r] * NEW['cap'][g]*(1-OFF[key].get((g,r),0) )

        n.setObjective(cost + shed*P['cost_shed_test'], GRB.MINIMIZE)
        n.optimize()
        results[key] = {'cost':cost.X,'shed':shed.X}
    return results


def extremeTest(inputs):
    S = inputs['S']
    G = inputs['G']
    P = inputs['P']
    NEW = inputs['new']
    if P.get('new',False):
        OFF = inputs['off']
    cf_dict = P['cf_dict']
    solutions = inputs['solutions']
    capkey = 'cap'
    if inputs.get('training',False) and not P['temperature-dependent']:
        capkey = 'cap-for'
    print(capkey)
    y = solutions['y']
    z = solutions['z']
    znew = solutions['znew']
    results = {key: None for key in S.keys()}
    for key in S.keys():
        s = S[key]
        capacity = sum( s[capkey][u] * z[u] for u in G['zuid']
                       ) + sum( G['cap'][u] for u in G['uid'] if u not in G['zuid']
                       ) + sum( y[g, r]*s['factor'][g, r][cf_dict[g]] for (g, r) in G['capcost_nrel'].keys()
                       ) + sum( znew[g,r] * NEW['cap'][g] * (1-OFF[key].get((g,r),0)) for (g,r) in znew)
        shed = max(0,s['load'] * P.get('demand_scale',1) - capacity)
        results[key] = {'shed':shed}
    return results


def relocate(inputs):
    Ss = inputs['S']
    off = inputs['off']
    P = inputs['P']
    G = inputs['G']
    L = inputs['L']
    i = list(Ss.keys())[0]
    U = P['Ulist'][0] # tradeoff value between obj1 and obj2
    sol = inputs['sol'][U]
    fips = inputs['fips']
    S = Ss[i]
    cf_ix = 1
    if not P.get('temperature-dependent',True):
        print('MUST BE TEMPERATURE DEPENDENT')
        return False
    S_n = [s for s in S.keys() if not S[s]['extreme']]
    S_e = [s for s in S.keys() if S[s]['extreme']]
    # gp.setParam('OutputFlag', 0)
    m = gp.Model('relocate')
    z_built = [u for u in G['zuid'] if sol['z'][u] > 0.5]
    z_list = [(u,r) for u in z_built for r in fips if fips[r] == fips[G['map_uid_fips'][u]] ]
    z = m.addVars(z_list, name='z', vtype=GRB.BINARY)
    for u in z_built: # must build z in state exactly once
        m.addConstr(sum(z[u,r] for r in fips if (u ,r) in z_list ) == 1)
    y = sol['y']
    x_list = [u for u in G['uid'] if u not in G['zuid']] + z_built
    x = m.addVars(S_n, x_list, name='x', vtype=GRB.CONTINUOUS)
    shed = m.addVars(S.keys(), name='shed', vtype=GRB.CONTINUOUS)
    costs = m.addVars(L['cost_types'], name='costs', vtype=GRB.CONTINUOUS)
    obj1_var = m.addVar(vtype=GRB.CONTINUOUS)
    obj2_var = m.addVar(vtype=GRB.CONTINUOUS)



    # obj1
    # obj = inputs['data'][U]['stats']['objective'] # original optimal cost
    # m.addConstr(costs['operating'] + costs['shedding'] + costs['capital'] <= obj, name='original-obj')
    m.addConstr(obj1_var = costs['operating'] + costs['shedding'] + costs['capital'], name='obj1')
    m.addConstr((1/P['cost_shed']) * costs['shedding'] == sum(shed[s] + S[s]['q'] for s in S_n ) )

    # obj2
    w = m.addVars(S_e, name='w', vtype=GRB.CONTINUOUS)
    gamma = m.addVar(name='gamma')
    m.addConstrs((w[s] >= shed[s] - gamma for s in S_e), name='cvar')
    m.addConstr(obj2_var == gamma + (1 / P['cvar']) * sum(w[s] * S[s]['q'] for s in S_e) )

    m.setObjective(U*obj1_var + (1-U)*obj2_var, GRB.MINIMIZE)

    for s in S_e: # extreme capacity and binary constraints
        m.addConstr(shed[s] >= S[s]['load']
                      - sum( z[u,r] * G['cap'][u] * (1-off[s].get((u,r),0)) for (u,r) in z_list )
                      - sum( S[s]['cap'][u] for u in G['uid'] if u not in G['zuid'])
                      - sum( y[g, r]*S[s]['factor'][g, r][cf_ix] for (g, r) in G['capcost_nrel'].keys()) )

    m.addConstr(costs['capital'] == costs['retire'] + (1/8760) * sum(y[g, r]*G['capcost_nrel'][g, r]
                                  for (g, r) in G['capcost_nrel'].keys()),
                'capital-costs')
    m.addConstr(costs['retire'] == (1/8760)*sum(sol['z'][u]*G['cap'][u]*P['capital_cost'][G['map_uid_type'][u]]/P['time_horizon']
                                                for u in G['zuid'] if u in z_built),
                'retirement-costs')
    m.addConstr(costs['operating'] == sum(S[s]['q'] * P['fuel'][G['map_uid_type'][u]] * G['hr'][u] * x[s, u]
                for u in x_list for s in S_n if G['map_uid_type'][u] in L['gen_fuel']),
                'operating-costs') # takes LONG time

    for s in S_n:
        m.addConstr(S[s]['load'] - shed[s]
                    <= sum(x[s, u] for u in x_list)
                    + sum(y[g, r]*S[s]['factor'][g, r][cf_ix] for (g, r) in G['capcost_nrel'].keys()),
                    'demand')

    for s in S_n: # normal capacity and binary constraints
        for u in x_list:
            if u in z_built:
                m.addConstr( x[s, u] <= sum(z[u, r] * G['cap'][u] * (1-off[s].get((u,r),0) )
                                            for r in fips if fips[r] == fips[G['map_uid_fips'][u]]), 'capacity-z')
            elif u not in G['zuid']:
                x[s, u].ub = S[s]['cap'][u]
            else: # shouldn't be anything here
                print('x out of scope:',s,u)
                x[s, u].ub = 0


    ct = 0
    cc = 0
    # coal = 0
    for u in z_built: # don't move generators that weren't chosen by the model in the first place
        # turning on half of CTs
        if G['map_uid_type'][u] == 'Combustion_Turbine':
            ct = ct+1
            if ct % 2 == 0:
                z[u,G['map_uid_fips'][u]].ub = 1
                z[u,G['map_uid_fips'][u]].lb = 1
        # turning on half of CCs
        if G['map_uid_type'][u] == 'Combined_Cycle':
            cc = cc+1
            if cc % 2 == 0:
                z[u,G['map_uid_fips'][u]].ub = 1
                z[u,G['map_uid_fips'][u]].lb = 1
        # turning off half of coal
        # if G['map_uid_type'][u] == 'Coal_Steam':
        #     coal = coal+1
        #     if coal % 2 == 0:
        #         z[u].ub = 0
        #         z[u].lb = 0
        # removing IA and MN
        # if G['map_uid_fips'][u] in ['IA','MN']:
        #     z[u].ub = 0
        #     z[u].lb = 0


    m.update()
    solutions = {U:{s:dict() for s in ['y','z']} for U in P['Ulist']}
    data = {U:{s:dict() for s in ['stats','shed','cost']} for U in P['Ulist']}
    data.update({'i':i})

    m.optimize()

    var_names = []
    var_values = []
    for var in m.getVars():
        if var.X > 0 and 'x' not in str(var.varName):
            var_names.append(str(var.varName))
            var_values.append(var.X)
        elif 'cost' in var.varName:
            var_names.append(str(var.varName))
            var_values.append(var.X)
    for i in range(len(var_names)):
        print(var_names[i],var_values[i])

    return solutions,data,m
