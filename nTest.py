#!/usr/bin/env python3
import sys
from methods_run import nTest
from methods_pickle import loadPickle
i = sys.argv[1]
U = sys.argv[2]
tag = sys.argv[3]

nTest({'i':i,
       'U':U,
       'tag':tag,
       'dir':'',
       'P':loadPickle('P'),
       'S':loadPickle('Sn'),
       'G':loadPickle('G'),
       'L':loadPickle('L'),
       'new':loadPickle('new'),
       'off':loadPickle('Sn_off'),
       'solutions':loadPickle('solutions')[int(i)][float(U)],
       'data':loadPickle('data')})
