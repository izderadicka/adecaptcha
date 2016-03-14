import urllib2
import sys
import cookielib
import time
from StringIO import StringIO
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from adecaptcha import clslib, audiolib

if len(sys.argv) <2 :
    print >>sys.stderr, 'Config file must be provided as script parameter'
    sys.exit(1)

opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
r=opener.open('http://www.urbtix.hk/')
r.read()
r=opener.open("https://ticket.urbtix.hk/internet/%d/en_US/wav/captchaSound.wav" % int (time.time()* 1000) )

buf=StringIO()
buf.write(r.read())
buf.seek(0)

res= clslib.classify_audio_file(buf, sys.argv[1], ext='.wav')
print 'Captcha is:',res
buf.seek(0)
print 'Playing captcha ...'
a,sr=audiolib.load_wav_sample(buf)
audiolib.play_array(a, sr)
clslib.release_models()
