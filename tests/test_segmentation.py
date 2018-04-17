'''
Created on Aug 9, 2014

@author: ivan
'''
import unittest
from adecaptcha import audiolib
from adecaptcha import segmentation


class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass
    
    def test_list(self):
        l=segmentation.list_algs()
        self.assertTrue(len(l)>=2)
        ld=dict(l)
        x=ld['Simple Energy Envelope'].alg_default_params
        self.assertEqual(len(x), 5)
        self.assertTrue(x['step_sec']) 
        self.assertEqual(ld['Simple Energy Envelope'].__name__, 'segment_audio_ee')

    def test1(self):
        a,sr=audiolib.load_audio_sample('test1.wav')
        sd=[]
        segs=audiolib.segment_audio('segment_audio_ee',a, sr, limit =5,  seg_details=sd,
            silence_sec=0.1, step_sec=0.2)
        print sd
        self.assertEqual(len(sd),4)
        
    def test2(self):
        a,sr=audiolib.load_audio_sample('test2.mp3')
        sd=[]
        segs=audiolib.segment_audio('segment_audio_ee',a, sr, limit = 0.65,  seg_details=sd,
            step_sec=0.2, win_size=0.1, silence_sec=0.1, 
                  sound_canvas=0.5, num_segments=4)
        print sd
        self.assertEqual(len(sd),4)
        
    def test_fixed(self):
        a,sr=audiolib.load_audio_sample('test1.wav')
        sd=[]
        segs=audiolib.segment_audio('segment_audio_fixed4',a, sr, limit =5,  seg_details=sd,
            start_1=0.0,end_1=0.1,
            start_2=0.2, end_2=0.3,
            start_3=0.4, end_3=0.5,
            start_4= 0.6, end_4=0.7)
        print sd
        self.assertEqual(len(sd),4)
        self.assertEqual(len(segs),4)
        



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()