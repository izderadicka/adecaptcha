import sys

import ao
import mad

mf = mad.MadFile(sys.argv[1])
print "Sample rate", mf.samplerate(), "mode" , mf.mode(), "bitrate", mf.bitrate()
dev = ao.AudioDevice(0, bits=16, channels=2, rate=mf.samplerate())
while 1:
    buf = bytes(mf.read())
    if  len(buf) <=4: 
        break
    dev.play(buf, len(buf))