'''
Created on Apr 19, 2010

@author: ivan
'''
from collections import defaultdict
from StringIO import StringIO
import numpy, types
import audiolib
import svm.svmutil as svmutil
import logging, os.path, types
import threading

logger=logging.getLogger()
module_lock=threading.Lock()

model_cache={}

def release_models():
    model_cache.clear()

def classify_audio_file(audio_file,cfg, ext=None):
    if isinstance(cfg,types.StringTypes):
        cfg_path, _name=os.path.split(cfg)
        cfg=eval(open(cfg).read())
        if cfg_path:
            if not cfg['range_file'].startswith(os.sep):
                cfg['range_file']=os.path.join(cfg_path, cfg['range_file'])
            if not cfg['model_file'].startswith(os.sep):
                cfg['model_file']=os.path.join(cfg_path, cfg['model_file'])
            
        
    classes=cfg.get('classes')
    r=load_scaling_range(cfg['range_file'])
    a,sr=audiolib.load_audio_sample(audio_file, ext)
    logger.debug('Loaded audio sample of length %.2f' % (len(a)/float(sr)))
    segs=audiolib.segment_audio(a, sr, limit=cfg['threshold'], step_sec=cfg['seg_size_min'], 
                silence_sec=cfg['silence']) [cfg['start_index']:cfg['end_index']]
    
    scaled=[]
    for s in segs:
        features= audiolib.calc_mfcc(s, sr, nbins=cfg['nbins'])
        scaled.append(scale_sample(features, r))
    if model_cache.has_key(cfg['model_file']):
        m=model_cache[cfg['model_file']]
    else:
        with module_lock:    
            m=svmutil.svm_load_model(cfg['model_file'])
        model_cache[cfg['model_file']]=m
    p_labels, p_acc, p_vals=svmutil.svm_predict([0]*len(scaled), scaled, m, '-q')
    #logger.debug('prediction additional info ' +str(p_acc)+str(p_vals))
    res=''.join([cls2char(int(n), classes) for n in p_labels])
    return res


class ClsCollect(object):
    def __init__(self):
        self.all_classes=defaultdict(lambda: 0)
        
    def add(self, txt):
        for c in txt:
            self.all_classes[c]+=1
            
    def class_count(self, cls):
        return self.all_classes[cls]
    
    @property
    def classes(self):
        classes=self.all_classes.keys()
        classes.sort()
        return classes
def to_float(x):
    if numpy.isfinite(x):
        return x
    else:
        return 0.0
    
def to_list(a):
    return [float(x) for x in a.flat]
    
def to_svm_format(cls_char, char_range, arr):
    out=StringIO()
    cls=char2cls(cls_char, char_range)
    if isinstance(cls, (types.ListType, types.TupleType)): 
        out.write(','.join(map(str,cls)))
    else:
        out.write(str(cls))
    
    out.write(' ')
    if isinstance(arr, numpy.ndarray):
        arr=arr.flat
    for i,n in enumerate(arr):
        out.write('%d:%f ' % (i+1, n))
    out.write('\n')
    return out.getvalue()
        
    
def cls2char(cls, char_range):
    c=char_range[cls]  
    return c

def char2cls(char, char_range):
    index=char_range.index(char)
    return index  
    
    
#def cls2char(cls, char_range):
#    for i in range(len(cls)):
#        if cls[i]==1:
#            try:
#                return char_range[i]
#            except KeyError:
#                raise ValueError('Invalid Class Code - No Char Matched')
#    raise ValueError('Invalid Class Code - No 1 found')
#
#
#def char2cls(char, char_range):
#    try:
#        index=char_range.index(char)
#    except ValueError:
#        raise ValueError('Invalid char- not found in range')
#    
#    code=[]
#    for i in xrange(len(char_range)):
#        if i==index:
#            code.append(1)
#        else:
#            code.append(0)
#    return code

class Range(object):
    def __init__(self, min, max, ranges):
        self.min, self.max, self.ranges= min, max, ranges
        
    def __str__(self):
        return 'Min %f, Max %f, %d ranges\n %s'% (self.min, self.max, 
                            len(self.ranges), str(self.ranges))    
def scale_sample(a,range):
    size=len(range.ranges)
    minv=numpy.zeros(size)
    minv[:]=range.min
    scale=numpy.zeros(size)
    scale[:]=range.max
    scale=scale-minv
    range=numpy.array(range.ranges, dtype=numpy.float).T
    arr=a.flat[:size]
    scale=scale*(arr-range[0])/ (range[1] -range[0]) + minv
    l= list(scale)
    
    return l
    
                
def load_scaling_range(fname):
    
    f=open(fname,'r')
    fl=f.readline()
    if not fl.strip()=='x':
        raise ValueError('first line must be x')
    sl=f.readline().split()
    min,max=map(float, sl)
    range=[]
    for line in f:
        l=line.split()
        range.append((float(l[1]), float(l[2])))
                     
    return Range(min, max, range)
        
        

#def scale(int index, double value):
#{
#    /* skip single-valued attribute */
#    if(feature_max[index] == feature_min[index])
#        return;
#
#    if(value == feature_min[index])
#        value = lower;
#    else if(value == feature_max[index])
#        value = upper;
#    else
#        value = lower + (upper-lower) * 
#            (value-feature_min[index])/
#            (feature_max[index]-feature_min[index]);
#
#    if(value != 0)
#    {
#        printf("%d:%g ",index, value);
#        new_num_nonzeros++;
#    }
#}
        
