'''
Created on Aug 9, 2014

@author: ivan
'''
import unittest
from adecaptcha import audiolib


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test1(self):
        a,sr=audiolib.load_audio_sample('test1.wav')
        sd=[]
        segs=audiolib.segment_audio(a, sr, step_sec=0.2, 
            limit =5,silence_sec=0.1, size_sec=0.5, seg_details=sd)
        print sd
        self.assertEqual(len(sd),4)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()