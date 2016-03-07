import time
import argparse
import urllib2
import os.path
import cookielib
import sys

URL="https://ticket.urbtix.hk/internet/%d/en_US/wav/replay/captchaSound.wav"

def main():
    p=argparse.ArgumentParser()
    p.add_argument('directory', help='directory where to load data')
    p.add_argument('-n', '--number', type=int, default=200, help='number of samples')
    p.add_argument('--delay', type=float, default=1.0, help='delay between downloads')
    args=p.parse_args()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()))
    r=opener.open('http://www.urbtix.hk/')
    r.read()
    if not os.path.exists(args.directory):
        os.makedirs(args.directory)
    for n in range(args.number):
        url=URL% int (time.time()* 1000)
        #print url
        
        r=opener.open(url)
        with open(os.path.join(args.directory, 'sample%d.wav'%n), 'wb') as f:
            f.write(r.read())
        print '.',
        sys.stdout.flush()
        time.sleep(args.delay)
    print '\nDone'
        

if __name__=='__main__':
    main()