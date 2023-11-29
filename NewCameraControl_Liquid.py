###
#If you ever get that closed is not an attribute or something similar
#Update both pycromanager and download the nightly build of mm
###

from pycromanager import Bridge 
import numpy as np
from PIL import Image, ImageTk, ImageEnhance
#import matplotlib.pyplot as plt
import time, tifffile, os.path
from serial import Serial


class CameraControl:

    def __init__(self,port):
        #this creates a bridge from code to camera and connects it from the specific COM port specificied by the user
        self.bridge = Bridge()
        #get object representing micro-manager core
        self.core = self.bridge.get_core()
        self.core.load_device("Port","SerialManager",port)
        self.core.set_property("Port","StopBits","2")
        self.core.set_property("Port","Parity","None")
        self.core.initialize_device("Port")
        print('No Errors, MM ready')
        #JavaObjectShadow.__del__(core)

    def TakeImage(self,exposure,folder,filename,suffix,contrastVal,EMGain):
        #does stuff with autoshutter
        self.auto_shutter = self.core.get_property('Core','AutoShutter')
        self.core.set_property('Core','AutoShutter',0)
        
        #Set the EM Gain for the camera
        #if the EM gain is 3 or less than 3 do not adjust it probably using CMOS
        if EMGain > 3:
            self.core.set_property('Andor','Gain',EMGain)
        #use the input exposure time
        #take an image with a 1ms exposure time to reset the exposure the camera has seen as we have seen higher exposure due to stage movements
        #self.core.set_exposure(10)
        #self.core.snap_image()
        #time.sleep(0.01)
        
        self.core.set_exposure(exposure)
        ### Acquiring Images ###
        #The micromanager core exposes several mechanisms for acquiring images. 
        #In order to not interfere with ohter pycromanager functionality,
        #this is the one that should be used
        #StartTime = time.time()
        self.core.snap_image()
        #StopTime = time.time() - StartTime
        #print('In CamControl.py: Exposure: {}s Vs. Actual {}s'.format((exposure/1000),StopTime))
        
        self.tagged_image=self.core.get_tagged_image()
        #Pixels by default come out as a 1D array. We can reshape them into an image
        self.pixels = np.reshape(self.tagged_image.pix, newshape=[self.tagged_image.tags['Height'],self.tagged_image.tags['Width']])
        print(self.pixels.dtype)
        filepath = folder + '/' + filename + str(suffix) + '.tif'
        JPGPath = folder + '/ReSizedJPGs'
        if os.path.exists(JPGPath) == False:
            os.mkdir(JPGPath)
        self.returnedName = filename + str(suffix) + '.tif'
        tifffile.imwrite(filepath,self.pixels,photometric='minisblack')
        #Improve the contrast of the tiff itself
        #Create a contrast improved tif
        self.Tif = Image.open(filepath)
        self.RotatedTif = self.Tif.rotate(-90.0)
        self.RotatedTif.save((folder+'/'+filename+str(suffix)+'_rotated.tif'))
        #Change the Contrast of the tif itself
        self.Tif.mode = 'I'
        self.Enhancer = ImageEnhance.Contrast(self.Tif.point(lambda i:i*(1./256)).convert('L'))
        self.EnhancedTif = self.Enhancer.enhance(contrastVal)
        self.EnhancedFilepath = JPGPath+'/'+filename+str(suffix)+'_contrast.tif'
        self.EnhancedTif.save(self.EnhancedFilepath)

        #Turn this contrast enhanced tif into a jpeg
        #self.ContrastTif_r = Image.open(self.EnhancedFilepath)
        #self.ContrastTif = self.ContrastTif_r.rotate(90.0)   #i added the rotate here for the images
        #self.ContrastTif.save((JPGPath+'/'+filename+str(suffix)+'_contrast'+ '.jpeg'),"JPEG",quality=100)

        #Make JPG image of the original image
        self.JPGImage = Image.open(filepath)
        self.JPGImage.mode = 'I'
        self.JPGImage.point(lambda i:i*(1./256)).convert('L').save(JPGPath+'/'+filename+str(suffix)+'.jpeg')

        #Close all of these
        self.JPGImage.close()
        #self.ContrastTif_r.close()
        self.Tif.close()
        self.RotatedTif.close()
        #After the Image has been taken, set the EM Gain back to 3 if it was changed
        if EMGain > 3:
            self.core.set_property('Andor','Gain',3)

        return self.returnedName
        
        
        
    def CloseCamera(self):
        print('Deleting camera')
        self.core.delete()

"""
#The below code is for testing in this script
#It should remain commented out unless trying to debugg code
Attempt = CameraControl('COM1')
#take image with 15 ms exposure
print('taking image with 15 ms exposure')
#TakeImage(self,exposure,folder,filename,suffix,contrastVal,EMGain):
Attempt.TakeImage(15,'C:/Users/Public/NeutronImaging','DarkImage',1,50,30)
print('sleeping for 10 seconds')
time.sleep(10)
Attempt.TakeImage(15,'C:/Users/Public/NeutronImaging','Brightened',1,70,30)
#Attempt.CloseCamera()"""