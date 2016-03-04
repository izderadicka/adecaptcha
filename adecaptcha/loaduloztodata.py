#! /usr/bin/env python
'''
Created on Apr 16, 2010
@author: ivan
'''
import argparse
import urllib, urllib2, os, os.path, sys, shutil, urlparse
import json

parser=argparse.ArgumentParser()
parser.add_argument('directory', nargs="?", help="directory where to load ulozto samples", default="ulozto_data")
parser.add_argument('-n', '--number', type=int, help="number of samples to download" , default=500)
args=parser.parse_args()
dir=args.directory
count=args.number
url='http://www.ulozto.cz/reloadXapca.php'

while count:
    
    try:
        h=''
        res=urllib2.urlopen(url)
        obj=json.load(res)
        h=obj['hash']
        image_file=urlparse.urlsplit(obj['image'])[2]
        image_ext= os.path.splitext(image_file)[1]
        sound_file=urlparse.urlsplit(obj['sound'])[2]
        sound_ext=os.path.splitext(sound_file)[1]
        image_name=os.path.join(dir,h+image_ext)
        sound_name=os.path.join(dir, h+sound_ext)
        urllib.urlretrieve(obj['image'], image_name)
        urllib.urlretrieve(obj['sound'], sound_name)
    except Exception,e:
        print >>sys.stderr, "Error when downloading hash %s - %s" % (h, str(e))
        try:
            shutil.rmtree(image_name, True)
            shutil.rmtree(sound_name, True)
        except Exception:
            pass
        
    print '.',    
    if count%40==0 and count<args.number:
        print
    sys.stdout.flush()
    count-=1


