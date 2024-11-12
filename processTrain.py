#!/usr/bin/env python3
import sys
from methods_run import processTrain
from methods_pickle import loadPickle

name = sys.argv[1]
processTrain({'name':name,'dir':'','Rdir':'results/','P':loadPickle('P')})
