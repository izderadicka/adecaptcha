import adecaptcha.clslib as clslib
import os.path



class UlozTo(object):
    __name__ = "UlozTo"
    def __init__(self, plugin=None):
        pass
        self._plugin=plugin
        

    def recognize(self, audio):
        #print "!!!CAPTCHA :", audio
        cfg_file=os.path.join(os.path.split(clslib.__file__)[0], 'ulozto.cfg')
        text= clslib.classify_audio_file(audio, cfg_file)
        return text
        

