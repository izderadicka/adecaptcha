'''
Created on Aug 23, 2014

@author: ivan
'''

import math
import numpy as np
from scipy.fftpack import dct
#import pyximport
#pyximport.install()
from pwrspec import pwrspec

    

def mfcc(sig, sr, nbins=40):
    #calculate power spectrum of the signal
    pw=pwrspec(sig, sr, nbins)
    #DCT of log of power spectrum
    return dct(np.log(pw))
    
    


    
    