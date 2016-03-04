'''
Created on Jan 31, 2016

@author: ivan
'''
import unittest
from adecaptcha.pwrspec import twin



class Test(unittest.TestCase):
    def comp(self,x,y):
        self.assertEqual(len(x), len(y))
        for i in range(len(x)):
            self.assertAlmostEqual(x[i], y[i])

    def test(self):
        self.assertFalse( twin(0,0))
        self.assertEqual( twin(0,1), [1.])
        self.assertEqual(list(twin(0,2)), [ 0.5,  0.5])
        self.comp(twin(0,3), [ 0.33333333,  1.        ,  0.33333333])
        self.comp(twin(0,4), [ 0.25,  0.75,  0.75,  0.25])
        self.comp(twin(0,5), [ 0.2,  0.6,  1. ,  0.6,  0.2])
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()