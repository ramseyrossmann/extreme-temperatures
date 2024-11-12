#!/usr/bin/env python3
import sys
from methods_run import processTest

name = sys.argv[1]
processTest({'name':name,'dir':'','Rdir':'results/','dpi':300})
