import numpy
import logging
logger=logging.getLogger()

def calc_energy_env(a, sr, win_size=0.01):
    wsize=win_size*sr
    a=numpy.array(a, dtype=numpy.int32)
    win= numpy.ones(wsize, dtype=numpy.float) / float(wsize) / 10737418.24 
    e= numpy.convolve(a * a, win, 'same')
    return e

def dbg_segments(segments, sr):    
    if logger.level and logger.level>logging.DEBUG:
        return
    sr=float(sr)
    diff=(segments[:, 1] - segments[:,0]) / sr
    logger.debug('Found %d segments: %s (lenghts %s)' % (len(segments), str(segments/sr), str(diff) ))
    
def cut_segments(a, sr, segments, size_sec=None, sound_canvas=None):
    
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

def segment_audio(data_array, sr, step_sec=0.35, limit =500, 
                  silence_sec=0.03, size_sec=None, seg_details=None, sound_canvas=0.5):
    step=int(round(step_sec*sr))
    silence=silence_sec*sr
    if sound_canvas:
        sound_canvas=int(round(silence*sound_canvas))
    env=calc_energy_env(data_array,sr)  
    i=0 
    in_segment=False
    seg_start=0
    segments=[]
    silence_detected=0
    while i<len(env) :
        if env[i]>limit:
            silence_detected=0
        if env[i]<=limit and in_segment:
            silence_detected+=1
            if silence_detected>=silence:
                in_segment=False
                segments.append([seg_start, i-silence])
                
        elif env[i]>limit and not in_segment:
            in_segment=True
            seg_start=i
            i+=step
        i+=1
    if in_segment:
        segments.append([seg_start, len(env)-1])
    segments=numpy.array(segments, dtype=numpy.int)
    if seg_details is not None and hasattr(seg_details, 'extend'):
        seg_details.extend(segments)
    dbg_segments(segments, sr)
    return cut_segments(data_array, sr, segments, None, sound_canvas)
    
    
def segment_audio_oldest(data_array, sr, step_sec=0.01, limit=0.05, size_sec=None):
    
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
    
    
    dbg_segments(segments, sr)
    return cut_segments(a, sr, segments, size_sec)