#!/usr/bin/env python3
import sys
from methods_run import Train
from methods_pickle import loadPickle

i = sys.argv[1]
U = sys.argv[2]
name = sys.argv[3]
Train({'i':i,
       'U':U,
       'name':name,
       'dir':name,
       'S':loadPickle('S'),
       'P':loadPickle('P'),
       'G':loadPickle('G'),
       'L':loadPickle('L'),
       'new':loadPickle('new'),
       'off':loadPickle('off'),
       'good_CC':loadPickle('good_CC'),
       'good_CT':loadPickle('good_CT'),
       })
