cimport numpy as np
import numpy as np
def hz2mel(hz):
    return 2595.0 * np.log10(1.0+ hz/700.0)

def mel2hz(mel):
    return 700.0* ( np.power(10.0, mel/2595.0) - 1)

def fbins(sr, nbins=40):
    maxm= hz2mel(sr/2.0)
    step=maxm/(nbins+1)
    ms=np.arange(step,maxm,step)
    return mel2hz(ms)

def posbins(sr,slen, nbins=40):
    step=2.0*slen/sr
    p=np.around(fbins(sr,nbins)*step, out=np.zeros(nbins,dtype=np.double))
    return p.astype(np.int)

def winspos(sr,slen, nbins=40):
    p=posbins(sr,slen,nbins)
    s=np.roll(p,1)
    s[0]=0
    sz=p-s 
    return np.array([p-sz,p+sz+1]).T

cdef extern from "math.h":
    double fabs(double x)
    
ctypedef np.double_t DTYPE_t

def twin(start, stop):
    
    cdef: 
        np.ndarray[DTYPE_t] arr
        int n
        int len=stop-start
    arr=np.zeros(len)
    for n in range(len):
        arr[n]= 1.0 - fabs(((len-1)/2.0 -n)/ (len/2.0))
    return arr

def pwrspec(sig,sr,nbins=40):
    s=np.fft.rfft(sig)
    samples=len(s)
    wins=winspos(sr, samples, nbins)
    coefs=[]
    for i in xrange(nbins):
        start,stop = wins[i]
        if stop>samples:
            stop=samples
        pwr=np.square(s[start:stop].real)+np.square(s[start:stop].imag)
        coefs.append(np.dot(pwr, twin(start,stop)))
        
    return np.array(coefs)