#!/usr/bin/env python
import os
import sys
from PyQt4.QtGui import *
from picamera import PiCamera
from picamera.array import PiRGBArray
from time import time, sleep
import time
from datetime import datetime
from PyQt4.QtCore import QDir, Qt, QObject
import cv2
import threading
from PyQt4 import QtGui
from SimpleCV import Camera, VideoStream, Color, Display, Image, VirtualCamera
from SimpleCV import *
import numpy as np
click = True

#dewarp
# build the mapping
def buildMap(Ws,Hs,Wd,Hd,R1,R2,Cx,Cy):
    map_x = np.zeros((Hd,Wd),np.float32)
    map_y = np.zeros((Hd,Wd),np.float32)
    rMap = np.linspace(R1, R1 + (R2 - R1), Hd)
    thetaMap = np.linspace(0, 0 + float(Wd) * 2.0 * np.pi, Wd)
    sinMap = np.sin(thetaMap)
    cosMap = np.cos(thetaMap)
    for y in xrange(0, int(Hd-1)):
	map_x[y] = Cx + rMap[y] * sinMap
	map_y[y] = Cy + rMap[y] * cosMap
	#(map1, map2) = cv2.convertMaps(map_x, map_y, cv2.CV_16SC2)

    return map_x, map_y
	#return map1, map2

# do the unwarping 
def unwarp(img,xmap,ymap):
    output = cv2.remap(img.getNumpyCv2(),xmap,ymap,cv2.INTER_LINEAR)
    result = Image(output, cv2image=True)
    # return result
    return result

class test(threading.Thread):
    def run(self):
        global click
        click = True
        print('Record button click')
        camera = PiCamera()
        camera.framerate = 16
        camera.resolution = (480,480)
        sleep(0.1)
        btime = time.time()
        fname = filename()
        print("Filename is "+fname)
        camera.start_preview()
        #camera.annotate_background = picamera.Color('black')
        camera.annotate_text = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        camera.start_recording("/home/pi/box1/storage/donutVideoFiles/"+fname +".mjpeg")
        while True:
            if (time.time()-btime)>60:
                fname = filename()
                print("Filename is "+fname)
                camera.split_recording("/home/pi/box1/storage/donutVideoFiles/"+fname +".mjpeg")
                btime = time.time()
            if click == False:
                break
            camera.annotate_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sleep(0.5)
        click = True
        camera.stop_recording()
        print("STOP")
        camera.stop_preview()
        camera.close()
 
#filenmae = yyyymmdd_hhss
def filename():
    dt = datetime.now()
    month = ""
    day = ""
    hour = ""
    minute = ""
    if dt.month<10:
        month = "0" + str(dt.month)
    else:
        month = str(dt.month)
    if dt.day<10:
        day = "0" + str(dt.day)
    else:
        day = str(dt.day)
    if dt.hour<10:
        hour = "0" + str(dt.hour)
    else:
        hour = str(dt.hour)
    if dt.minute<10:
        minute = "0" + str(dt.minute)
    else:
        minute = str(dt.minute)
    s = str(dt.year)+month+day+"_"+hour+minute
    return s
 
#MainWindow
class Example(QMainWindow):
 
    def __init__(self):
        super(Example, self).__init__()
        self.title = 'PyQt5 menu - pythonspot.com'
        self.left = 20
        self.top = 40
        self.width = 640
        self.height = 400
        # set to raspberry pi screen size
 
        self.initUI()
 
 
    def initUI(self):
 
        #StatusBar
        self.statusBar().showMessage('Ready')
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&devClose')
        
        self.setWindowState(Qt.WindowMaximized)
        self.setStyleSheet("background:rgb(255,255,255)");
        #self.setGeometry(0, 20, 250, 300)
        self.setWindowTitle('PanoBox')
 
        #home
        self.stopbtn=QPushButton("STOP", self)
        self.stopbtn.move(20, 160)
        self.stopbtn.clicked.connect(self.on_click_STOP)
        self.stopbtn.setStyleSheet("QPushButton {background-color:pink; color:purple}");
 
        # Button_Record
        self.recbtn=QPushButton("RECORD", self)
        self.recbtn.move(20, 40)
        self.recbtn.clicked.connect(self.on_click_rec)
        self.recbtn.setToolTip('Starting <b>Record</b> Panobox')
 
        # Button_Folder
        self.filebtn=QPushButton("FOLDER", self)
        self.filebtn.move(20,100)
        self.filebtn.clicked.connect(self.on_click_file)
 
	# Button_Close
	self.closebtn = QPushButton("CLOSE", self)
	self.closebtn.move(20, 220)
	self.closebtn.clicked.connect(self.on_click_close)

	# Button_devClose
        self.closebtn = QPushButton("devClose", self)
        self.closebtn.move(20, 280)
        self.closebtn.clicked.connect(self.on_click_devclose)

        #image show
        pic  = QtGui.QLabel(self)
        pic.setGeometry(200,100,600,200)
        pic.setPixmap(QtGui.QPixmap("/home/pi/box1/pano.png"))
                      
        self.show()
  
    def on_click_STOP(self):
        global click
        click = False
 
    def on_click_rec(self):
        th = test()
        th.start()
 
    def on_click_file(self):
        win = UI()
        win.exec_()
        #print('PyQt5 File button click')
        #self.dialogTextBrowser.exec_()
        # dialog = FolderDialog()
        # dialog.exec_()
    def on_click_close(self):
	os.system('sudo shutdown -r now')
    def on_click_devclose(self):
	sys.exit()

#######################################################################
#Folder
class UI(QtGui.QDialog):
    def __init__(self, parent=None):
    # def __init__(self):
        global selectfile
        QtGui.QDialog.__init__(self, parent)
        # QtGui.QWidget.__init__(self, parent)
 
        #tree dir view
        self.tree = MyTreeView()
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)
        #convButton
        self.convButton = QtGui.QPushButton()
        self.convButton.setText("Convert selected file")
        #playButton
        self.playButton = QtGui.QPushButton()
        self.playButton.setText("Play selected file")
        #closeButton
        self.closeButton = QtGui.QPushButton()
        self.closeButton.setText("close folder manager")

        #grid setting
        grid = QtGui.QGridLayout()
        grid.addWidget(self.tree)
        grid.addWidget(self.convButton)
        grid.addWidget(self.playButton)
        grid.addWidget(self.closeButton)
        self.setLayout(grid)
 
        #window size -->
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitle('File Manager')
 
        #button connect with click function
#         self.connect(self.convButton, QtCore.SIGNAL("clicked()"), self._Convert)
#         self.connect(self.playButton, QtCore.SIGNAL("clicked()"), self._Play)
        self.convButton.clicked.connect(self._Convert)
        self.playButton.clicked.connect(self._Play)
        self.closeButton.clicked.connect(self._Close)

    def _Convert(self):
        # selectfile = self.listView.DirModel.fileName(self.listView.currentIndex())
        selectfile = self.tree.DirModel.filePath(self.tree.currentIndex())
        sfilename = self.tree.DirModel.fileName(self.tree.currentIndex())
        strfn = sfilename[0:13]
        print selectfile + " convert"
        #os.system('sh /home/pi/panoBox/dewarp.sh')
        disp = Display((800,480)) #
        vals = []
        last = (0,0)
        # Load the video from the rpi
        vc = VirtualCamera(str(selectfile),"video")
        #vc = picamera.PiCamera()
        # Sometimes there is crud at the begining, buffer it out
        for i in range(0,10):
            img = vc.getImage()
        #    img = vc.capture()
            img.save(disp)
        
        """
        cnt = 0
        while not disp.isDone():
            test = disp.leftButtonDownPosition()
            if( test != last and test is not None):
                last= test
                vals.append(test)
                cnt += 1
                if cnt == 3:
                    break
        """
        ###############################################
        #480
        Cx = 260
        Cy = 195
        R1x = 320
        R1y = 195
        R2x = 380
        R2y = 195
        """
        #1200
        Cx = 645
        Cy = 490
        R1x = 787
        R1y = 490
        R2x = 937
        R2y = 490
        """
        ##############################################
        """
        Cx = vals[0][0]
        Cy = vals[0][1]
        R1x = vals[1][0]
        R1y = vals[1][1]
        R2x = vals[2][0]
        R2y = vals[2][1]
        print Cx
        print Cy 
        print R1x 
        print R1y 
        print R2x 
        print R2y
        """
        ##############################################
        R1 = R1x-Cx
        R2 = R2x-Cx
        Wd = round(float(max(R1, R2)) * 2.0 * np.pi)
        Hd = (R2-R1)
        Ws = img.width
        Hs = img.height
        # build the pixel map, this could be sped up
        print "BUILDING MAP!"
        xmap,ymap = buildMap(Ws,Hs,Wd,Hd,R1,R2,Cx,Cy)
        print "MAP DONE!"
        # do an unwarping and show it to us
        result = unwarp(img,xmap,ymap)
        result.save(disp)
        # I used these params for converting the raw frames to video
        # avconv -f image2 -r 30 -v:b 1024K -i samples/lapinsnipermin/%03d.jpeg output.mpeg
        i = 0
        while img is not None:
            print img.width, img.height
            result = unwarp(img,xmap,ymap)

            result.save(disp)
            # Save to file
            fname = "/home/pi/box1/panoImageFiles/FRAME{num:05d}.png".format(num=i)
            result.save(fname)
            #vs.writeFrame(derp)
            # get the next frame
            img = vc.getImage()
            i = i + 1
        disp.quit()
        ff = "sudo avconv -r 12 -i /home/pi/box1/panoImageFiles/FRAME%05d.png -vf 'scale=trunc(iw/2)*2:trunc(ih/2)*2 , transpose=1, transpose=1' -c:v libx264 /home/pi/box1/storage/panoVideoFiles/"+str(strfn)+".mp4&&sudo rm /home/pi/box1/panoImageFiles/*.png"
        os.system(ff)
        
 
    def _Play(self):
        selectfile = self.tree.DirModel.filePath(self.tree.currentIndex())
        print selectfile + " play"
        sfile = "sudo omxplayer -o hdmi --win '12 20 790 360' " + selectfile
        os.system(str(sfile))

    def _Close(self):
	self.close()	
 
    @staticmethod
    def Display():
        # app = QtGui.QApplication(sys.argv)
        win = UI()
        win.show()
        sys.exit(app.exec_())
 
# class MyDirModel(QObject):
class MyDirModel(QtGui.QDirModel):
    '''
    SubClass of QtGui.QDirmodel
    '''
    def __init__(self, parent=None):
        super(MyDirModel, self).__init__()
 
    def getData(self, ModelIndex):
        '''
        Using QModelIndex I can get data via the data() method or
        via any other method that suport a QModelIndex
        '''
        paths = []
        if isinstance(ModelIndex, list):
            for items in ModelIndex:
                #print self.data(items).toString()
                paths.append(self.filePath(items))
            return paths
        else:
            raise ValueError("getData() requires a list(QtGui.QModelIndexs)")
 
class MyTreeView(QtGui.QTreeView):
# class MyTreeView(QObject):
    '''
    SubClass of QtGui.QListView
    '''
    global selectfile
    def __init__(self, parent=None):
    # def __init__(self):
        # super(MyTreeView, self).__init__(parent)
        super(MyTreeView, self).__init__()
        # QtGui.QTreeView.__init__(self)
        self.DirModel = MyDirModel()
        self.setModel(self.DirModel) # we have to set the listView to use this DirModel
        self.setRootIndex(self.DirModel.index("/home/pi/box1/storage")) # set the deafault to load to c:\
 
        # self.connect(self, QtCore.SIGNAL("doubleClicked(QModelIndex)"), self._DoubleClicked)
        self.doubleClicked.connect(self._DoubleClicked)
 
    def getModelItemCollection(self):
        '''
        From this list get the QModelIndex that we set with .setRootIndex
        Using QModelIndex and DirModel we can get all the elements at that Index
        '''
        ModelIndex = self.rootIndex()
        ModelIndexCollection = []
        for i in range(0, self.DirModel.rowCount(ModelIndex)):
            ModelIndexCollection.append(ModelIndex.child(i,0))
        return ModelIndexCollection
 
    def _DoubleClicked(self):
        if self.DirModel.isDir(self.currentIndex()):
            path = self.DirModel.filePath(self.currentIndex())
            # self.setRootIndex(self.DirModel.index(path))
            items = self.getModelItemCollection()
 
def main():
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
 
if __name__ == '__main__':
    main()
