#!/usr/bin/env python3
import os
from methods_setup import populateDirs, copyPickles
from methods_run import Train, eTest, nTest, processTrain, processTest
from methods_pickle import loadPickle

def runTrial(in_dict):

    D = {key:in_dict[key] for key in in_dict if key not in ['dir','Sdir','Rdir','size','runHere']}
    D.update({'dpi':300})
    copyPickles(in_dict['dir'])
    populateDirs(in_dict,D)

    if in_dict.get('runHere', False):
        P = loadPickle(in_dict['dir']+'P')
        Ulist = P['Ulist']
        for i in range(P['n_trains']):
            m = Train({'i':i,
                    'dir':in_dict['dir'],
                    'S':loadPickle(in_dict['Sdir']+'S'+str(i)+'/S'),
                    'P':loadPickle(in_dict['dir']+'P'),
                    'G':loadPickle(in_dict['dir']+'G'),
                    'L':loadPickle(in_dict['dir']+'L'),
                    'new':loadPickle(in_dict['dir']+'new'),
                    'off':loadPickle(in_dict['Sdir']+'S'+str(i)+'/off'),
                    'good_CC':loadPickle(in_dict['dir']+'good_CC'),
                    'good_CT':loadPickle(in_dict['dir']+'good_CT')
                    })
            # return m # comment for completion not on chtc
        os.system('bash mac-processTrain.sh ' + in_dict['dir'])
        in_dict['P'] = loadPickle(in_dict['dir']+'P')
        toTest = processTrain(in_dict)
        for i in range(P['n_trains']):
            for U in Ulist:
                testDict = {'i':i,
                            'U':U,
                            'tag':str(i),
                            'dir':in_dict['dir'],
                            'P':loadPickle(in_dict['dir']+'P'),
                            'S':loadPickle('test-scenarios/test/'+in_dict['size']+'/Se'),
                            'G':loadPickle(in_dict['dir']+'G'),
                            'L':loadPickle(in_dict['dir']+'L'),
                            'new':loadPickle(in_dict['dir']+'new'),
                            'off':loadPickle('test-scenarios/test/'+in_dict['size']+'/Se_off'),
                            'solutions':loadPickle(in_dict['Rdir']+'S'+str(i)+'/U'+str(U)+'/solutions')[U],
                            'data':loadPickle(in_dict['Rdir']+'S'+str(i)+'/U'+str(U)+'/data')}
                eTest(testDict)
                testDict.update({'S':loadPickle('test-scenarios/test/'+in_dict['size']+'/Sn'), 
                                  'off':loadPickle('test-scenarios/test/'+in_dict['size']+'/Sn_off')})
                nTest(testDict)
        os.system('bash mac-pre_processTest.sh '+in_dict['dir'])
        processTest(in_dict)
        os.system('mv plot_*_E*.png '+in_dict['dir']+'results/')
        os.system('mv capacity.png '+in_dict['dir'] + 'results/')
        print('completed')
