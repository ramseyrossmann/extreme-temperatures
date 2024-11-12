#!/usr/bin/env python3
import os, pickle
def savePickle(folder,name,file):
    if folder != '':
        if not os.path.isdir(folder):
            os.makedirs(folder)
    with open(folder+name+'.pkl','wb') as f:
        pickle.dump(file,f)
        
def loadPickle(filename):
    with open(filename+'.pkl','rb') as f:
        return pickle.load(f)
