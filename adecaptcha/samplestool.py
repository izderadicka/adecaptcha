'''
Created on Apr 18, 2010

@author: ivan
'''


from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sampletool_dialog
import sys, os, os.path, audiolib, segmentation, time, clslib

import pylab
import numpy
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import traceback

TITLE = 'Prepare training samples'
AUDIO_EXTS=('.mp3', '.wav',)
PIC_EXTS=('.png', '.jpg', '.gif')
class WaveDialog(QDialog):
    def __init__(self, parent=None, threshold=500):
        super(WaveDialog, self).__init__(parent)
        self.dpi=100
        self.threshold=threshold
        self.fig = Figure((5.0, 4.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)
        self.setGeometry(0,0, 800,500)
        self.axes = self.fig.add_subplot(111)
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        self.setLayout(vbox)
        
    
    def plot_wave(self, arr, sr, seg_details=[]):
        x=numpy.arange(len(arr), dtype=numpy.double) / sr
        self.axes.plot(x, arr, color="blue")
        self.axes.axhline(self.threshold, color='green')
        for s,e in seg_details:
            self.axes.axvline(s/float(sr), color='red')
            self.axes.axvline(e/float(sr), color='yellow')
        self.canvas.draw()
        
class WorkerThread(QThread):
    updated=pyqtSignal(int)
    done=pyqtSignal(str)
    error=pyqtSignal(str)
    
    def __init__(self):
        QThread.__init__(self)
        self.mutex=QMutex()
        self.canceled=False
    
    
    def do_work(self):
        raise NotImplemented
    def run(self):  
        res=None
        try:
            res=self.do_work()
        except Exception, e:
            self.error.emit(str(e))
            print "Error in worker thread %s" %e
            traceback.print_exc()
        with QMutexLocker(self.mutex):
            if not self.canceled:
                self.done.emit(res)
        #self.terminate()
        
    def update_progress(self,n):
        with QMutexLocker(self.mutex):
            if self.canceled:
                raise audiolib.AbortedByUser
        print "Processing(%d) ..."%n
        self.updated.emit(n+1)
        
    def cancel(self):
        with QMutexLocker(self.mutex):
            self.canceled=True
        
class AnalyzeThread(WorkerThread):
    
    def __init__(self, items, dir, parent):
        WorkerThread.__init__(self)
        self.items=items
        self.dir=dir
        self.parent=parent
        
 
    def do_work(self):  
        res=audiolib.analyze_segments(self.items, self.dir, 
                    progress_callback=self.update_progress, 
                    seg_alg=self.parent.seg_alg.__name__, limit=self.parent.threshold, 
                    params=self.parent.get_params(), 
                    start_index=self.parent.start_index,
                    end_index=self.parent.end_index
                    ) 
        return res
        
        
def params_to_text(p):  
    res=[]
    for k in p:
        res.append('%s=%f'%(k, p[k] or 0))      
    return ', '.join(res)  

def text_to_params(t):
    res={}
    for x in str(t).split(','):
        e=x.strip().split('=')
        if len(e)!= 2:
            raise ValueError('Invalid expression %s'%x)
        res[e[0].strip()]= float(e[1])
    return res
        
    
class MainDialog(QDialog, sampletool_dialog.Ui_Dialog):
    def __init__(self, parent=None):
        super(MainDialog, self).__init__(parent)
        self.setupUi(self)
        self._dir=None
        self.lock=QReadWriteLock()
        self.player=Player(self.lock, self)
        self._clear_items()
        self.updateUi()
        self.connect(self, SIGNAL('directoryChanged'), self.directory_changed)
        self.connect(self.player, SIGNAL('finished()'), self. player_finished)
        self.setWindowTitle(TITLE)
        self.sizeEdit.setValidator(QIntValidator(self))
        self.tresholdEdit.setValidator(QDoubleValidator(self))
        self.startEdit.setValidator(QDoubleValidator(self))
        self.endEdit.setValidator(QDoubleValidator(self))
        self.startIndexEdit.setValidator(QIntValidator(self))
        self.endIndexEdit.setValidator(QIntValidator(self))
        #segmentation alg 
        self.seg_alg=None
        self._algs=segmentation.list_algs()
        self.algorithmCombo.addItems(zip(*self._algs)[0])
        self.algorithmCombo.activated.connect(self.alg_changed)
        
        self.restore_state()
        self.waveButton.setEnabled(False)
        self.playButton.setEnabled(False)
        self.analyze_thread=None
        self.analyze_dialog=None
        self._total_segments=0
        
    
        
        
        
    def alg_changed(self, idx):
        print 'Algorithm changed to %s' % self._algs[idx][0]
        self.seg_alg=self._algs[idx][1]
        self.segparamsEdit.setText(params_to_text(self.seg_alg.alg_default_params))
        self.tresholdEdit.setText(str(self.seg_alg.alg_default_threshold))
        
    def analyze_samples(self):
        self.analyze_dialog=QProgressDialog('Analyzing samples ...', 'Abort', 0, len(self._items), parent=self)
        #self.analyze_dialog.setWindowModality(Qt.WindowModal)
        self.analyze_dialog.show()
        
        self.analyze_thread=AnalyzeThread([i[0] for i in self._items], self._dir, self)
        self.analyze_thread.updated.connect(self.analyze_samples_update)
        self.analyze_thread.done.connect(self.analyze_samples_done)
        self.analyze_thread.error.connect(self.analyze_samples_done)
        self.connect(self.analyze_dialog, SIGNAL('canceled()'), self.analyze_samples_canceled)
        self.analyze_thread.start()
        
    def analyze_samples_update(self, n):   
        self.analyze_dialog.setValue(n) 
    def analyze_samples_done(self, res):
        print "Analyzis done"
        self.analyze_dialog.setValue(len(self._items)) 
        self.segstatEdit.setText(res)  
        
        self.analyze_dialog=None
        self.analyze_thread=None
        
    def analyze_samples_canceled(self):
        print "Canceled"
        self.analyze_thread.cancel()
        self.segstatEdit.setText('Canceled')  
        
        self.analyze_dialog=None
        self.analyze_thread=None
        
        
    @pyqtSignature('bool')    
    def on_analyzeCheckBox_toggled(self, state):
        if state and self._items:
            self.analyze_samples()
    def restore_state(self):
        settings=QSettings()
        self.sizeEdit.setText(settings.value('nbins').toString() or '40')
        self.tresholdEdit.setText(settings.value('threshold').toString() or '5')
        self.analyzeCheckBox.setChecked(settings.value('analyze').toBool() or False)
        self.autoplayCheckBox.setChecked(settings.value('autoplay').toBool()  or False)
        self.playWholeRadio.setChecked(settings.value('play_whole').toBool() or False)
        self.startIndexEdit.setText(settings.value('startIndex').toString() or '')
        self.endIndexEdit.setText(settings.value('endIndex').toString() or '')
        self.startEdit.setText(settings.value('start').toString() or '')
        self.endEdit.setText(settings.value('end').toString() or '')
        
        stored_dir= unicode(settings.value('dir').toString())
        if os.path.isdir(stored_dir):
            self.directoryEdit.setText(stored_dir)
            QTimer.singleShot(100,self.on_directoryEdit_editingFinished)
            
        segalg=settings.value('segalg').toString()
        segalg_index=None
        for i, (_, f) in enumerate(self._algs):
            if segalg==f.__name__:
                segalg_index=i
                
        if segalg_index is None:
            self.algorithmCombo.setCurrentIndex(0)
            self.alg_changed(0)
        else:
            self.algorithmCombo.setCurrentIndex(segalg_index)
            self.seg_alg=self._algs[segalg_index][1]
            self.segparamsEdit.setText(settings.value('segalg_params').toString())
                
        
            
            
    def save_state(self):
        settings=QSettings()  
        settings.setValue('nbins', QVariant(self.sizeEdit.text()))
        settings.setValue('threshold', QVariant(self.tresholdEdit.text()))
        settings.setValue('analyze', QVariant(self.analyzeCheckBox.isChecked()))
        settings.setValue('autoplay', QVariant(self.autoplayCheckBox.isChecked()))
        settings.setValue('play_whole', QVariant(self.playWholeRadio.isChecked()))
        settings.setValue('dir', QVariant(self._dir))
        settings.setValue('startIndex', QVariant(self.startIndexEdit.text()))
        settings.setValue('endIndex', QVariant(self.endIndexEdit.text()))
        settings.setValue('segalg',  QVariant(self.seg_alg.__name__ if self.seg_alg else ''))
        settings.setValue('segalg_params', QVariant(self.segparamsEdit.text()))
        settings.setValue('start', QVariant(self.startIndexEdit.text()))
        settings.setValue('end', QVariant(self.endIndexEdit.text()))
        
        
    def closeEvent(self, event):
        self.save_sample()
        self.save_state()  
    def updateUi(self, partial=False):
        def enable_controls(enabled):
            #self.playButton.setEnabled(enabled)
            self.nextButton.setEnabled(enabled)
            self.transcribeEdit.setEnabled(enabled)
            self.numberSpinBox.setEnabled(enabled)
            self.generateButton.setEnabled(enabled)
            
            
        if not self._dir or not os.path.isdir(self._dir):
            enable_controls(False)
        else:
            enable_controls(True)
        self.currentEdit.setText('')
        self.transcribeEdit.setText('')    
        self.imageLabel.setPixmap(QPixmap())
        if not partial:
            self.segstatEdit.clear()
    
    @pyqtSignature('')
    def on_browseDirButton_clicked(self):
        dir_name=QFileDialog.getExistingDirectory(self, 'Select Directory With Samples')
        if dir_name:
            self.directoryEdit.setText(dir_name)
            self.directoryEdit.emit(SIGNAL('editingFinished()'))
            
            
    def _clear_items(self):
        self._items=[]
        self._index=None
        self._audio_samples=[]
        self._dirty=False
    
    
    @pyqtSignature('')
    def on_transcribeEdit_returnPressed(self):
        if self.nextButton.isEnabled():
            self.nextButton.emit(SIGNAL('clicked()'))
    
    @pyqtSignature('QString')
    def on_transcribeEdit_textChanged(self, text):
        self._dirty=True
        
    @pyqtSignature('')
    def on_directoryEdit_editingFinished(self):
        new_dir=self.directoryEdit.text()
        
        if not new_dir or new_dir==self._dir:
            return
        print "Directory %s Entered" % new_dir
        if not os.path.isdir(new_dir):
            QMessageBox.warning(self, "Directory Doesn't Exist", "This directory doesn't exist, please choose other one")
            self.updateUi()
            return
        self._dir=unicode(new_dir)
        self.waveButton.setEnabled(False)
        self.playButton.setEnabled(False)
        self.emit(SIGNAL('directoryChanged'))
        
        
        
    def directory_changed(self):
        print "Directory changed to %s" % self._dir 
        self._clear_items()
        self.load_samples()
        
    def load_samples(self):
        files=os.listdir(self._dir)
        files.sort()
        for f in files:
            base_name,ext=os.path.splitext(f)
            if ext and ext.lower() in AUDIO_EXTS:
                af=f
                pic_file=None
                for e in PIC_EXTS:
                    name=base_name+e
                    try:
                        files.index(name)
                        pic_file=name
                        break
                    except ValueError:
                        pass
                txt_file=None
                try:
                    name=base_name+'.txt'
                    files.index(name)
                    txt_file=name
                except ValueError:
                    pass
                self._items.append([af,pic_file, txt_file])
                
                
                                   
        self.setWindowTitle(TITLE+ "- Loaded %d samples" % len(self._items))
        self.numberSpinBox.setMaximum(len(self._items))
        self.updateUi()
        if self.analyzeCheckBox.isChecked():
            self.analyze_samples()
        
    @pyqtSignature('')    
    def on_nextButton_clicked(self):
        print "Next Clicked"
        self.save_sample()
        if self._index==None:
            self._index=0
        else:
            self._index+=1
            
        self.load_sample()
        self.numberSpinBox.setValue(self._index+1)
        if self.autoplayCheckBox.isChecked():
            QTimer.singleShot(100,self.play_audio)
            
    def load_sample(self):
        
        if self._index>=len(self._items)-1:
            self.nextButton.setEnabled(False)
      
        af, pic_file, txt_file= self._items[self._index]
        self.transcribeEdit.clear()
        if pic_file:
            self.imageLabel.setPixmap(QPixmap(os.path.join(self._dir, pic_file)))
            
        if txt_file:
            f=open(os.path.join(self._dir, txt_file), 'r')
            self.transcribeEdit.setText(f.read().upper())
            f.close()
        self._load_audio(af)
        self.transcribeEdit.setInputMask('N'*len(self._audio_samples))
        self.transcribeEdit.setFocus()
        self._dirty=False
        self.currentEdit.setText(af+ " - %d audio segments"  % self._total_segments)
        
        
    def save_sample(self):
        if self._dirty:
            text=unicode(self.transcribeEdit.text())
            if text:
                txt_file=self._items[self._index][2]
                if not txt_file:
                    txt_file=os.path.splitext(self._items[self._index][0])[0]+'.txt'
                    
                f=open(os.path.join(self._dir, txt_file), 'w')
                f.write(text.upper())
                self._items[self._index][2]=txt_file
            self._dirty=False
        
    @pyqtSignature('')
    def on_numberSpinBox_editingFinished(self):
        i=int(self.numberSpinBox.value())
        if self._index is not None and  i-1==self._index:
            return
        if not i:
            self.updateUi(True)
            return
        self.save_sample()
        self._index=i-1
        self.nextButton.setEnabled(True)
        self.load_sample()
                 
    @property        
    def nbins(self):
        return int(self.sizeEdit.text() or 0)
    
    @property
    def threshold(self):
        return float(self.tresholdEdit.text() or 0) 
    
    @property
    def start_index(self):
        t=self.startIndexEdit.text()
        if not t:
            return None
        return int(t)
    
    @property
    def end_index(self):
        t=self.endIndexEdit.text()
        if not t:
            return None
        return int(t)
    
    @property
    def start_pos(self):
        t=self.startEdit.text()
        if not t:
            return None
        return float(t)
    
    @property
    def end_pos(self):
        t=self.endEdit.text()
        if not t:
            return None
        return float(t)
    
    @property
    def play_whole(self):
        return self.playWholeRadio.isChecked()
    
    
    def get_params(self):
        try:
            return text_to_params(self.segparamsEdit.text())
        except ValueError, e:
            QMessageBox.warning(self, 'Invalid parameters', 
                                    str(e),
                                    QMessageBox.Ok)
            
    def _load_audio(self, af):
        params=self.get_params()
        try:
            a, sr=audiolib.load_audio_sample(os.path.join(self._dir, af))
        except Exception,e:
            QMessageBox.warning(self, 'Invalid audio', 
                                    str(e),
                                    QMessageBox.Ok)
            return
        
        seg_details=[]
        try:
            samples=audiolib.segment_audio(self.seg_alg.__name__, a, sr, limit=self.threshold, seg_details=seg_details,
                                       **params)
        except Exception,e:
            QMessageBox.warning(self, 'Segmentation error', 
                                    str(e),
                                    QMessageBox.Ok)
            return
        with QWriteLocker(self.lock):
            self._full_audio=a
            self._seg_details=seg_details
            self._total_segments=len(samples)
            self._audio_samples=samples[self.start_index:self.end_index]
            self._sr=sr
        self.waveButton.setEnabled(True)
        self.playButton.setEnabled(True)
        
    @pyqtSignature('')            
    def on_playButton_clicked(self):
        print 'Play clicked'
        QTimer.singleShot(0,self.play_audio)
                
    def play_audio(self):
        self.playButton.setEnabled(False)
        if self.play_whole:
            self.player.initialize([self._full_audio], self._sr)
        else:
            self.player.initialize(self._audio_samples, self._sr)
        self.player.start()
        
    @pyqtSignature('')            
    def on_waveButton_clicked(self):
        print 'Showing wave'   
        wDialog=WaveDialog(self, self.threshold);
        wDialog.show() 
        wDialog.plot_wave(segmentation.calc_energy_env(self._full_audio, self._sr), self._sr, self._seg_details)
        
        
    @pyqtSignature('')
    def player_finished(self):
        print 'Player finished'
        if self._index!=None:
            self.playButton.setEnabled(True)
        
    @pyqtSignature('')    
    def on_generateButton_clicked(self):
        self.save_sample()
        no_ts_count=0
        cls_collector=clslib.ClsCollect()
        for a,p, txt_file in self._items:
            if not txt_file:
                no_ts_count+=1
            else:
                f=open(os.path.join(self._dir, txt_file))
                cls_collector.add(f.read())
                f.close()
                
        if no_ts_count>0:
            res=QMessageBox.warning(self, 'Not All Samples Transcribed', 
                                    "%d samples have not been transcribed.\n Do you want to continue?"%no_ts_count,
                                    QMessageBox.Yes|QMessageBox.No)
            if res!=QMessageBox.Yes:
                return
            
        #debug
        for c in cls_collector.classes: print '%s(%d),'%(c, cls_collector.class_count(c)), 
        print
        file_name=unicode(QFileDialog.getSaveFileName(self, 'File to save samples mfcc representation'), 'UTF-8')
        if not file_name:
            return
        base_name=os.path.splitext(file_name)[0]
        short_name=os.path.split(base_name)[-1]
        classes=cls_collector.classes
        params=self.get_params()
        def output_samples():
            pd=QProgressDialog('Saving samples ...', 'Abort', 0, len(self._items), self)
            #pd.setWindowModality(Qt.WindowModal)
            pd.show()
            f=open(file_name,'w')
            for count, (audio_file, _p, txt_file) in enumerate(self._items):
                if txt_file:
                    a,sr= audiolib.load_audio_sample(os.path.join(self._dir, audio_file))
                    samples=audiolib.segment_audio(self.seg_alg.__name__, a, sr, limit=self.threshold, **params )
                    segments=samples[self.start_index:self.end_index]
                    ts=open(os.path.join(self._dir, txt_file)).read()
                    for i,s in enumerate(segments):
                        rs= audiolib.calc_mfcc(s, sr, self.nbins)
                        try:
                            cls=ts[i]
                        except IndexError:
                            raise IndexError("Transcription %d has incorrect number of letter" % (count+1))
                        f.write(clslib.to_svm_format(cls, classes, rs))
                        
                pd.setValue(count)
            
                if pd.wasCanceled():
                    break
                
            f.close()
            cfg=open(base_name+'.cfg', 'w')
            cfg.write(repr({'classes':classes, 'nbins': self.nbins,
                            'threshold':self.threshold,
                            'start_index':self.start_index, 'end_index':self.end_index,
                            'start_pos':self.start_pos, 'end_pos':self.end_pos,
                            'segalg': self.seg_alg.__name__,
                            'params':params,
                            'range_file': short_name+'.range',
                            'model_file': short_name+'.model'
                            }))
            
            cfg.close()
            pd.setValue(len(self._items))
        QTimer.singleShot(100, output_samples)
        
        
            
                    
                
class Player(QThread):
    def __init__(self, lock, parent=None):
        super(Player, self).__init__(parent)
        self.lock = lock
        self.stopped = False
        self.mutex = QMutex()
        
    def initialize(self, audio_samples, sr):
        self.stopped = False
        self.audio_samples = audio_samples
        self.sr=sr
        
    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True


    def isStopped(self):
        with QMutexLocker(self.mutex):
            return self.stopped


    def run(self):
        with QReadLocker(self.lock):
            for a in self.audio_samples:   
                audiolib.play_array(a, self.sr)
                if self.isStopped():
                    break
                time.sleep(0.3)
                if self.isStopped():
                    break
        
        self.stop()
        #self.emit(SIGNAL("finished()"))          
        
            
    
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setOrganizationName("ivan")
    app.setOrganizationDomain("zderadicka.eu")
    app.setApplicationName(TITLE)
    dialog = MainDialog()
    dialog.show()
    # test 
#    g=WaveDialog(dialog)
#    g.show()
    sys.exit(app.exec_())



