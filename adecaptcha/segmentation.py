import numpy
import logging
logger=logging.getLogger()
import inspect
from collections import OrderedDict


def _extract_params(f):
        params=inspect.getargspec(f)
        if len(params.args)-4>0:
            return OrderedDict(zip(params.args[4:], params.defaults[2:]))

def seg_alg(name):
    def _wrap(fn):
        def _inner(*args, **kwargs): 
            return fn(*args, **kwargs)
        _inner.alg_name=name
        _inner.alg_default_params=_extract_params(fn)
        _inner.alg_default_threshold = inspect.getargspec(fn).defaults[0]
        _inner.__name__ = fn.__name__
        return _inner
    return _wrap

def list_algs():
    res=[]
    for f in globals().values():
        if inspect.isfunction(f) and hasattr(f, 'alg_name'):
            res.append((f.alg_name, f))
    return res
        
    

def calc_energy_env(a, sr, win_size=0.01):
    wsize=win_size*sr
    a=numpy.array(a, dtype=numpy.int32)
    win= numpy.ones(int(wsize), dtype=numpy.float) / float(wsize) / 10737418.24 
    e= numpy.convolve(a * a, win, 'same')
    return e

def dbg_segments(segments, sr):    
    if logger.level and logger.level>logging.DEBUG:
        return
    sr=float(sr)
    diff=(segments[:, 1] - segments[:,0]) / sr
    logger.debug('Found %d segments: %s (lenghts %s)' % (len(segments), str(segments/sr), str(diff) ))
    
def cut_segments(a, sr, segments, size_sec=None, sound_canvas=None, seg_details=None):
    if seg_details is not None and hasattr(seg_details, 'extend'):
        seg_details.extend(segments)
    dbg_segments(segments, sr)
    
    ary_segments=[]
    if sound_canvas: 
        for i in xrange(len(segments)):
            s=segments[i][0]-sound_canvas
            if s < 0:
                s=0
            e=segments[i][1]+sound_canvas
            if e >= len(a):
                e=len(a)-1
                
            segments[i]=[s,e]
                  
    for s,e in segments:
        if size_sec:
            l=e-s
            nl=int(size_sec*sr)
            seg=numpy.resize(a.flat[s:e].copy(), int(size_sec*sr))
            # In contrary to documentation, if array is expanded, its not extended with zero, but with copy of itself
            if nl>l:
                seg[l:]=0
            ary_segments.append(seg)
        else:
            ary_segments.append(a.flat[s:e])
        
    return ary_segments

def segment_audio(seg_alg,data_array, sr,  limit =5,  seg_details=None,**kwargs):
    f=globals().get(seg_alg)
    if not f:
        raise ValueError('Invalid alg. name %s'%seg_alg)
    return f(data_array, sr,  limit,  seg_details, **kwargs)




#segmentation algorithms must have this signature:
#def alg(data_array, sr, limit=123, seg_details=None, ... (params specific to algorithm follows as keyword params with default)

@seg_alg('Simple Energy Envelope')
def segment_audio_ee(data_array, sr,  limit =5,  seg_details=None,
                  step_sec=0.2, win_size=0.1, silence_sec=0.1, 
                  sound_canvas=0.5, num_segments=4):
    step=int(round(step_sec*sr))
    silence=silence_sec*sr
    if sound_canvas:
        sound_canvas=int(round(silence*sound_canvas))
    env=calc_energy_env(data_array,sr, win_size)  
    env_len=len(env)
    limit_orig = limit
    # now try adatively decrease limit, if not found required number of segments
    while limit > limit_orig / 2.0:
        i=0 
        in_segment=False
        seg_start=0
        segments=[]
        silence_detected=0
        while i<env_len :
            if env[i]>limit:
                silence_detected=0
            if env[i]<=limit and in_segment:
                silence_detected+=1
                if silence_detected>=silence:
                    in_segment=False
                    segments.append([seg_start, int(i-silence)])
                    
            elif env[i]>limit and not in_segment:
                in_segment=True
                seg_start=i
                i+=step
            i+=1
        if in_segment:
            segments.append([seg_start, len(env)-1])
        if num_segments <= 0 or len(segments) == num_segments: 
            break    
        if num_segments>0 and len(segments) > num_segments:
            #lets select only n with greatest energy
            energies = []
            for seg in segments:
                e = env[seg[0]:seg[1]].sum()
                energies.append((e,seg))
            energies.sort(reverse=True)
            
            segments = [s for (e,s) in energies[:num_segments]]
            segments.sort()
            break
        limit = limit - limit_orig / 10.0
    
    segments=numpy.array(segments, dtype=numpy.int)
    
    return cut_segments(data_array, sr, segments, None, sound_canvas, seg_details)

@seg_alg('4 Fixed segments')
def segment_audio_fixed4(data_array, sr, limit=0.0,  seg_details=None, 
                        start_1=0.0,end_1=0.1,
                        start_2=0.2, end_2=0.3,
                        start_3=0.4, end_3=0.5,
                        start_4= 0.6, end_4=0.7):   
    
    segments=numpy.array([[start_1, end_1], [start_2, end_2], [start_3, end_3], [start_4,end_4]],dtype=numpy.double) * sr
    return cut_segments(data_array, sr, segments.astype(numpy.int), None, None, seg_details)
 
@seg_alg('Old Very Naive')    
def segment_audio_naive(data_array, sr, limit=0.05,  seg_details=None, 
                         step_sec=0.01,  size_sec=None):
    
    step=int(step_sec*sr)
    steps=numpy.ceil(float(len(data_array))/step)
    a=numpy.resize(data_array,(steps,step))
    p=numpy.square(a.astype(numpy.float)/32767).mean(1)
    started=False
    low_segments=0
    high_segments=0
    start_index=0
    stop_index=0
    segments=[]
    for i,val in enumerate(p):
        if val>limit:
            if started:
                low_segments=0
            else:
                if not high_segments:
                    start_index=i
                high_segments+=1
                if high_segments>=3:
                    started=True
                    high_segments=0
        else:
            if started:
                if not low_segments:
                    stop_index=i
                low_segments+=1
                if low_segments>=10:
                    started=False
                    low_segments=0
                    segments.append([start_index, stop_index])
                    
            else:
                high_segments=0
    if started:
        segments.append([start_index, i+1])
        
    segments=numpy.array(segments, dtype=numpy.int)*step
   
    return cut_segments(a, sr, segments, size_sec, seg_details=seg_details)