#! /usr/bin/env python2
'''
Created on Apr 20, 2010

@author: ivan
'''


import sys, urllib2, argparse, urlparse, os.path
try:
    from adecaptcha import clslib
except ImportError:
    import clslib

def def_options():
    p=argparse.ArgumentParser()
    p.add_argument('config_file', help='Configuration file')
    p.add_argument('sound_url', nargs='?', help='URL of sound file - wav or mp3, if not present reads file from stdin')
    p.add_argument('-t', '--sound-type', choices=['wav', 'mp3'], help='Type of sound file - if cannot be determined from URL')
    p.add_argument('-o', '--output-file', help='Writes result to file (instead of stdout)')
    return p.parse_args() 
    
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
    opts= def_options()
    
    if opts.output_file:
        f=open(opts.output_file, 'w')
    else:
        f=sys.stdout
    if opts.sound_url:
        url= urlparse.urlparse(opts.sound_url)
        if url[0]:
            resp=urllib2.urlopen(opts.sound_url)
        else:
            resp=open(opts.sound_url, 'rb')
    else:
        resp=sys.stdin
        
    ext='.' + opts.sound_type if opts.sound_type else None or \
        get_ext(resp.info()) if hasattr(resp, 'info') else None or \
        os.path.splitext(opts.sound_url)[1]
    if not ext or ext not in ['.wav', '.mp3']:
        print >>sys.stderr, 'Cannot determine sound file type, specify with -t argument'
        sys.exit(1)
    res=clslib.classify_audio_file(resp, opts.config_file, ext=ext)
    clslib.release_models()
    f.write(res+'\n')
    f.close()
    resp.close()
    
if __name__=='__main__':
    main()
       
