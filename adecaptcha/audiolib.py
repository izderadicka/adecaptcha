'''
Created on Apr 15, 2010

@author: ivan
'''
import sys
import mad  # @UnresolvedImport
import os.path
import wave
import struct
import mymfcc
try:
    import ao  # @UnresolvedImport
except:
    print >>sys.stderr, "WARNING: pyao module missing, will not be able to play audio"
from segmentation import segment_audio    
import numpy
import logging, types

logger=logging.getLogger()

class AbortedByUser(Exception):
    pass
def analyze_segments(mp3_files, dir='', progress_callback=None, 
                     seg_alg=None, limit=5, params=None,
                    start_index=None, end_index=None):
    seg_length=[]
    seg_no=[]
    for i,mp3_file in enumerate(mp3_files):  
        f=os.path.join(dir, mp3_file)
        a, sr= load_audio_sample(f)
        segments=segment_audio(seg_alg, a, sr, limit, **params )
        seg_no.append(len(segments))
        seg_length.extend([float(len(s))/float(sr) for s in segments[start_index: end_index]])
        if progress_callback:
            try:
                progress_callback(i)
            except AbortedByUser:
                return ''
    seg_length=numpy.array(seg_length, dtype=numpy.float)
    seg_no=numpy.array(seg_no, dtype=numpy.int)
    
    res= "Segments number per sample: min=%d, max=%d, mean=%.4f std=%.4f var=%.4f\n" % \
        (seg_no.min(), seg_no.max(), seg_no.mean(), seg_no.std(), seg_no.var())
    if len(seg_length):
        res+="Segments lengths(sec): min=%.4f, max=%.4f, mean=%.4f std=%.4f var=%.4f\n" % \
        (seg_length.min(), seg_length.max(), seg_length.mean(), seg_length.std(), seg_length.var())
    
    return res
    
def signal_envelope(data_array):
    return numpy.abs(data_array)  


def play_array(a, sr):
    data=a.tostring()
    dev = ao.AudioDevice(0, bits=16, channels=1, rate=sr )
    #print dev.driver_info()
    dev.play(data)
    
def load_audio_sample(fname, ext=None):
    if not ext and isinstance(fname, types.StringTypes):
        ext = os.path.splitext(fname)[1].lower()
    if not ext:
        raise ValueError('Cannot determine audio type')
    if ext=='.mp3':
        return load_mp3_sample(fname)
    elif ext=='.wav':
        return load_wav_sample(fname)
    else:
        raise ValueError('Unknown audio type')
    
def load_wav_sample(fname):
    f=wave.open(fname)
    try:
        if f.getcomptype() != 'NONE':
            raise ValueError('Compressed WAVE format is not supported!')
        sr=f.getframerate()
        slen=f.getsampwidth()
        flen=f.getnframes()
        nchan= f.getnchannels()
        name=fname if isinstance(fname, types.StringTypes) else '<stream>'  
        logger.debug('Loading wav file %s: rate: %d, channels: %s, sample size: %s', name, sr, nchan, slen)
        if nchan <1 or nchan>2:
            raise ValueError('Only 1 or 2 channels are supported')
        if slen==1:
            sample_to_int=lambda i: (ord(i) - 128) * 256 # 1 byte PCM is unsigned, scaling up to 2 byte int
        elif slen==2:
            sample_to_int = lambda i : struct.unpack('<h',i)[0]
        else:
            raise ValueError('Only 1 or2 bytes sample size is supported')
        count=flen/nchan
        sample=[]
        for pos in xrange(count):
            if nchan==1:
                s=f.readframes(1)
                if not s:
                    raise ValueError('File %s ends early, at pos. %d'%(fname,pos))
                sample.append(sample_to_int(s))
            elif nchan==2:
                l=f.readframes(1)
                r=f.readframes(1)
                if not l or not r:
                    raise ValueError('Files ends early, at pos. %d'%pos)
                val = (sample_to_int(l)+sample_to_int(r))/2
                sample.append(val)
        return numpy.array(sample, dtype=numpy.int16), sr
    finally:
        f.close()
        
def load_mp3_sample(fname):
    mf=mad.MadFile(fname)
    name=fname if isinstance(fname, types.StringTypes) else '<stream>'  
    logger.debug('loading mp3 file %s : rate %d, layer %d, mode %d, total time %d' %
                 (name, mf.samplerate(), mf.layer(), mf.mode(), mf.total_time()))
    
    a=numpy.array([], dtype=numpy.int16)
    #TODO: this is not very effective
    while 1:
        #read frame
        audio=mf.read()
        if audio is None:
            break
        a=numpy.append(a,numpy.frombuffer(audio, dtype=numpy.int16))
        
    
    #a=numpy.fromstring(str(sample)[3:], dtype=numpy.int16)
    logger.debug('Lodaded %d words' % len(a))
    if mf.mode() in (3,2):
        a.shape=-1,2
        a=numpy.mean(a,1)
        a=numpy.around(a, out=numpy.zeros(a.shape, numpy.int16 ))
        
    return a, mf.samplerate()

def calc_mfcc(sample, sr, nbins):
    nwin=int(0.025*sr)
    nstep=int(0.01*sr)
    rs= mymfcc.mfcc(sample, sr, nbins)
    numpy.ma.fix_invalid(rs, copy=False, fill_value=0)
    logger.debug("Calculated MFCC size: %s " % str(rs.shape))
    return rs
