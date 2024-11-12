#!/usr/bin/env python3
import sys
from methods_run import ExtremeTest
from methods_pickle import loadPickle
i = sys.argv[1]
U = sys.argv[2]
tag = sys.argv[3]

ExtremeTest({'i':i,
       'U':U,
       'tag':tag,
       'dir':'',
       'P':loadPickle('P'),
       'S':loadPickle('Se'),
       'G':loadPickle('G'),
       'solutions':loadPickle('solutions')[int(i)][int(U)],
       'data':loadPickle('data')})
