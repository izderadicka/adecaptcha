'''
Created on Mar 20, 2016

@author: ivan
'''

from __future__ import division
import argparse
import os.path
from adecaptcha import clslib
import numpy as np
import time


def main():
    p=argparse.ArgumentParser()
    p.add_argument('config_file', help='Config file')
    p.add_argument('directory', help='Directory with samples - *.wav and *.txt files')
    args=p.parse_args()
    correct=0
    incorrect=0
    incorrect_files=[]
    times=[]
    for f in os.listdir(args.directory):
        name, ext=os.path.splitext(f)
        if ext=='.wav':
            text_file=os.path.join(args.directory, name+'.txt')
            if not os.path.exists(text_file):
                continue
            with open(os.path.join(args.directory, text_file)) as tf:
                text=tf.read().strip()
            now= time.time()    
            res= clslib.classify_audio_file(os.path.join(args.directory, f), args.config_file).strip()
            times.append(time.time()-now)
            if res == text:
                correct += 1
            else:
                incorrect+=1
                incorrect_files.append((f, text, res))
                
    #
    print 'Samples %d' % (incorrect+correct)
    print 'Accuracy %f' % (correct / (incorrect+correct))
    print 'Average decode time %f' % np.array(times).mean()
    print 'Incorrect samples: '
    print '\n'.join(map(lambda x: '%s correct: %s found:%s' %x, incorrect_files))
    clslib.release_models()          


if __name__=='__main__':
    main()            