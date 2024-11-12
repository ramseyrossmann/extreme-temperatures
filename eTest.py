#!/usr/bin/env python3
import sys
from methods_run import eTest
from methods_pickle import loadPickle
i = sys.argv[1]
U = sys.argv[2]
tag = sys.argv[3]

eTest({'i':i,
       'U':U,
       'tag':tag,
       'dir':'',
       'P':loadPickle('P'),
       'S':loadPickle('Se'),
       'G':loadPickle('G'),
       'new':loadPickle('new'),
       'off':loadPickle('Se_off'),
       'solutions':loadPickle('solutions')[int(i)][float(U)],
       'data':loadPickle('data')})
