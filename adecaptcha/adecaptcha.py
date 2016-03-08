#! /usr/bin/env python
'''
Created on Apr 20, 2010

@author: ivan
'''


import sys,os, os.path, urllib, urllib2, optparse, traceback
try:
    from adecaptcha import clslib
except ImportError:
    import clslib

p=optparse.OptionParser(usage="%s [options] config_file mp3_url" % sys.argv[0])
def def_options():
    pass
    
def get_ext(res):
    mime=res['Content-Type']
    if mime:
        mime.lower()
    if mime=='audio/x-wav' or mime=='audio/wav':
        return '.wav'
    elif mime=='audio/mpeg3' or mime=='audio/x-mpeg-3':
        return '.mp3'
    
def main():
    def_options()
    options, args=p.parse_args() 
    if len(args)<2:
        p.print_usage()
        sys.exit(1)
    must_close=False
    if len(args)>2:
        f=open(args[2], 'w')
        must_close=True
    else:
        f=sys.stdout
        
    try:    
        resp=urllib2.urlopen(args[1])
        
        res=clslib.classify_audio_file(resp, args[0], ext=get_ext(resp.info()))
        
    except:
        traceback.print_exc()
        sys.exit(2)
    clslib.release_models()
    f.write(res+'\n')
    if must_close:
        f.close()
    
    
if __name__=='__main__':
    main()
       
