import NewCameraControl_Liquid, LiquidControl
import cv2
import numpy as np
import matplotlib.pyplot as plt
import scipy as scipy
from scipy import ndimage, misc
from scipy.interpolate import UnivariateSpline 
import sys,os
from PIL import Image
from datetime import date

def FWHMFromImage(ImagePath,ROI_Input,ROI_Needed=True):
    #Open the image in question
    original1 = cv2.imread(ImagePath,-1)
    img_med1 = ndimage.median_filter(original1, size=20)
    if ROI_Needed == True:
        #croi = cv2.selectROI(img_med)
        maximg = np.max(original1)
        #maximg = np.max(img_med1)
        imgmult = int(65530/maximg) #multiply this to stretch the image to fill 16bit depth for cv2
        cal = img_med1*imgmult
        roi = cv2.selectROI(cal)
    else:
        roi = ROI_Input
    #print rectangle point of selected ROI
    #print(roi)
    #crop selected roi from raw image
    roi_cropped = original1[int(roi[1]):int(roi[1]+roi[3]),int(roi[0]):int(roi[0]+roi[2])]
    #show cropped image
    #cv2.imshow("ROI",roi_cropped)

    #after we have our region turn it into an array
    cropped_array = np.array(roi_cropped)
    #Now that we have the array, I need to average from left to right in this array to get ESF
    ESF = np.mean(cropped_array, axis=0)
    #can uncomment the next line to save the ESF
    #np.savetxt(ImagePath+'/ESF_ROI.csv',ESF,fmt='%.2f',delimiter=',')

    #Make a dummy x variable for pixel number across the ESF
    X = np.arange(1,len(ESF)+1,1)

    #Next Get the derivative for the LSF
    MaxY = np.max(ESF)
    i = 0
    Y=[]
    while i < len(ESF):
        Y.append(ESF[i]/MaxY)
        i = i+1 

    #If the image was light to dark need to multiply by -1 to have a positive derivative
    der = np.diff(Y)/np.diff(X)*-1
    #But we lose an element so need another array that has X values between each original point
    i = 0
    x2 = []
    while i < len(X):
        if i > 0:
            X2val = (X[i] + X[i-1])/2
            x2.append(X2val)
            i = i+1
        else:
            i = i+1
    #get the difference between baseline and peak value
    difference = np.max(der) - np.min(der)
    #half of that peak height is the half maximum
    HalfMax = difference/2.0
    #this is the peak height without subtracting off baseline
    peakVal = der.argmax()
    nearest_above = (np.abs(der[peakVal:-1]-HalfMax)).argmin()
    nearest_below = (np.abs(der[0:peakVal]-HalfMax)).argmin()
    FWHM = (np.mean(x2[nearest_above+peakVal])-np.mean(x2[nearest_below]))
    #using the univariate spline method to find the two crossing points for fwhm provides more variation but is subject to problems.
    #spline = UnivariateSpline(X2, der-np.max(der)/2,s=0)
    #r1,r2=spline.roots()
    #FWHM= r2-r1
    print('X at above={}, X at below={},FWHM={}'.format(np.mean(x2[nearest_above+peakVal]),np.mean(x2[nearest_below]),FWHM))
    return x2, der, roi, FWHM#, r1, r2

def AutoFocus(InitialVoltage, ExposureTime, EMGain):
    Camera = NewCameraControl_Liquid.CameraControl('COM1')
    inc = 0 #increment for any arrays that we have
    xArray = []
    DerArray = []
    roi = []
    FWHMarray = []
    vApplied = []
    while inc < 10:
        #change the voltage on the liquid lens
        if inc == 0:       
            VChange = LiquidControl.ChangeVoltage(InitialVoltage)
            CurrentVoltage = InitialVoltage
        else:
            VChange = LiquidControl.ChangeVoltage(CurrentVoltage)
        #take the first image to get the baseline and ROI
        if VChange == 1:
            Image = Camera.TakeImage(ExposureTime,currentPath,'Focus_'+str(CurrentVoltage)+'V_',inc,0,EMGain)    #have EM set to 3 aka no em gain
            ImageName = currentPath+'Focus_'+str(CurrentVoltage)+'V_1_rotated.tif'
            #on the first one, we will need to select the ROI, all other images will use this ROI going forward.
            if inc == 0:
                Outputs = FWHMFromImage(ImageName,[0,0,0,0],ROI_Needed=True)
                LSFPath = currentPath+'LSF_Array/'
                if not os.path.exists(LSFPath):
                    #path didn't exist so we just made it
                    os.makedirs(LSFPath)
            else:
                Outputs = FWHMFromImage(ImageName,roi[0],ROI_Needed=False)
            #add the outputs from the FWHMFromImage function to the array for comparisons
            xArray.append(Outputs[0])
            DerArray.append(Outputs[1])
            roi.append(Outputs[2])
            FWHMarray.append(Outputs[3])
            vApplied.append(CurrentVoltage)
            #this is optional to save the LSF, it is nice to visually make sure the optimal voltage was selected
            np.savetxt(LSFPath+'LSF_'+str(CurrentVoltage)+'V.csv',np.transpose(np.array((xArray[inc],DerArray[inc]),dtype=object)),delimiter=',')
            plt.plot(xArray[inc],DerArray[inc],label=str(CurrentVoltage)+'V on Lens')
            inc += 1
            CurrentVoltage = CurrentVoltage + 1.0   #the voltages are floats. I plan to sweep 10 voltages and then find the best interval there
        else:
            raise Exception('Voltage was not changed properly, breaking the loop')

    #now that I have done a sweep of the first 10 images, I am going to see which is best FWHM
    minFWHM = np.min(FWHMarray)
    if minFWHM == FWHMarray[0]:
        minFound = False
        firstMin = True
        #this means that the best FWHM was at the first voltage and I need to go lower in voltage
        CurrentVoltage = InitialVoltage - 1.0
        while minFound == False:
            VChange = LiquidControl.ChangeVoltage(CurrentVoltage)
            if VChange == 1:
                Image = Camera.TakeImage(ExposureTime,currentPath,'Focus_'+str(CurrentVoltage)+'V_',inc,0,3)        #have EM set to 3 aka no em gain
                ImageName = currentPath+'Focus_'+str(CurrentVoltage)+'V_1_rotated.tif'
                Outputs = FWHMFromImage(ImageName,roi[0],ROI_Needed=False)
                xArray.append(Outputs[0])
                DerArray.append(Outputs[1])
                roi.append(Outputs[2])
                FWHMarray.append(Outputs[3])
                vApplied.append(CurrentVoltage)
                np.savetxt(LSFPath+'LSF_'+str(CurrentVoltage)+'V.csv',np.transpose(np.array((xArray[inc],DerArray[inc]),dtype=object)),delimiter=',')
                plt.plot(xArray[inc],DerArray[inc],label=str(CurrentVoltage)+'V on Lens')
                if firstMin == True:
                    if FWHMarray[0] < FWHMarray[-1]:    #if the first one we tested (initial voltage) is smaller than last one we tested then the min actually was initial
                        minFound = True
                        minVoltage = vApplied[0]
                    else:
                        firstMin = False
                        inc += 1
                        CurrentVoltage = CurrentVoltage - 1.0
                else:
                    if FWHMarray[-2] < FWHMarray[-1]:   #if the second to last tested is smaller than current, the second to last was min
                        minFound = True
                        minVoltage = vApplied[-2]
                        minFWHM = FWHMarray[-2]
                    else:
                        inc += 1
                        CurrentVoltage = CurrentVoltage - 1.0
    elif minFWHM == FWHMarray[-1]:
        minFound = False
        #this means that the best FWHM was at the last voltage and I need to go higher in voltage
        while minFound == False:
            VChange = LiquidControl.ChangeVoltage(CurrentVoltage)
            if VChange == 1:
                Image = Camera.TakeImage(ExposureTime,currentPath,'Focus_'+str(CurrentVoltage)+'V_',inc,0,3)        #have EM set to 3 aka no em gain
                ImageName = currentPath+'Focus_'+str(CurrentVoltage)+'V_1_rotated.tif'
                Outputs = FWHMFromImage(ImageName,roi[0],ROI_Needed=False)
                xArray.append(Outputs[0])
                DerArray.append(Outputs[1])
                roi.append(Outputs[2])
                FWHMarray.append(Outputs[3])
                vApplied.append(CurrentVoltage)
                np.savetxt(LSFPath+'LSF_'+str(CurrentVoltage)+'V.csv',np.transpose(np.array((xArray[inc],DerArray[inc]),dtype=object)),delimiter=',')
                plt.plot(xArray[inc],DerArray[inc],label=str(CurrentVoltage)+'V on Lens')
                if FWHMarray[-2] < FWHMarray[-1]:   #if the second to last tested is smaller than current, the second to last was min
                    minFound = True
                    minVoltage = vApplied[-2]
                    minFWHM = FWHMarray[-2]
                else:
                    inc += 1
                    CurrentVoltage = CurrentVoltage + 1.0
    else:
        minVoltage = vApplied[np.argmin(FWHMarray)] #if we didn't have to look for other voltages, the minimum voltage is at the argmin location for min FWHM
    
    print('We have found the minimum FWHM of {} at voltage = {}'.format(minFWHM,minVoltage))
    print('After you close the plot you will be asked if you agree that the minimum point is what was calculated')
    np.savetxt(LSFPath+'FWHMforVoltages.csv',np.transpose(np.array((vApplied,FWHMarray),dtype=object)),delimiter=',')
    plt.xlabel('Pixel Distance')
    plt.ylabel('Derivative of Intensity')
    plt.title('LSF for each image at 340 mm')
    plt.legend()
    plt.show()
    #this input question prompts the user to do a refined scane of 0.1 V instead of 1 V increments from before.
    ProceedQuestion = input("Should the code proceed to do a refined scan based on calculated minimum point [yes or no]\n")
    if ProceedQuestion == 'Y' or ProceedQuestion == 'y' or ProceedQuestion == 'Yes' or ProceedQuestion == 'yes':
        #now that we have minVoltage, I want to do a refined scan around minVoltage to find the true minimum point, I will do a scan of 0.1 V between -1 and +1 v of the min voltage
        inc = 0
        refinedX = []
        refinedDer = []
        refinedROI = []
        refinedFWHM = []
        refinedV = []
        CurrentVoltage = minVoltage - 0.9
        while CurrentVoltage < minVoltage+1.00:
            VChange = LiquidControl.ChangeVoltage(CurrentVoltage)
            if VChange == 1:
                Image = Camera.TakeImage(ExposureTime,currentPath,'Focus_'+str(CurrentVoltage)+'V_',inc,0,3)        #have EM set to 3 aka no em gain
                ImageName = currentPath+'Focus_'+str(CurrentVoltage)+'V_1_rotated.tif'
                Outputs = FWHMFromImage(ImageName,roi[0],ROI_Needed=False)
                refinedX.append(Outputs[0])
                refinedDer.append(Outputs[1])
                refinedROI.append(Outputs[2])
                refinedFWHM.append(Outputs[3])
                refinedV.append(CurrentVoltage)
                np.savetxt(LSFPath+'LSF_'+str(CurrentVoltage)+'V.csv',np.transpose(np.array((refinedX[inc],refinedDer[inc]),dtype=object)),delimiter=',')
                plt.plot(refinedX[inc],refinedDer[inc],label=str(CurrentVoltage)+'V on Lens')
                inc += 1
                CurrentVoltage = round(CurrentVoltage+0.1,1)   #the voltages are floats. I plan to sweep 10 images and then find the best interval there
            else:
                raise Exception('Voltage was not changed properly, breaking the loop')
        #now that I haved done the refined loop, lets look for the smallest FWHM now
        minRefinedFWHM = np.min(refinedFWHM)
        minRefinedV = refinedV[np.argmin(refinedFWHM)]
        print('The smallest FWHM was {} at voltage of {}'.format(minRefinedFWHM,minRefinedV))
        np.savetxt(LSFPath+'FWHMforVoltages.csv',np.transpose(np.array((vApplied,FWHMarray),dtype=object)),delimiter=',')
        plt.xlabel('Pixel Distance')
        plt.ylabel('Derivative of Intensity')
        plt.title('LSF for each image | Refined Voltage Sweep')
        plt.legend()
        plt.show()
    else:
        print('You did not answer yes or variant of yes so we are completing the code without doing a refined sweep')



#this was used for when I tested the code for the voltage versus working distance curve             
#DistToWall = 300    #measured in mm
#currentPath = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))+'/Images_'+str(DistToWall)+'mm_FromWall/'
InitialVoltage = 35.0
currentPath = (os.path.dirname(os.path.realpath(__file__)))+'/Autofocusing_'+str(date.today())+'_StartingVoltage_'+str(InitialVoltage)+'/'
if not os.path.exists(currentPath):
    #path didn't exist so we just made it
    os.makedirs(currentPath)
else:
    #path did exist so we should either increment or overwrite
    OverWrite = input("Folder Exists: Overwrite? [Y] or [N]\n")
    if OverWrite == 'Y' or OverWrite == "y":
        pass    #Filtered Path stays the same
    elif OverWrite == 'N' or OverWrite == 'n':
        NewFilteredPath = input("Enter a new identifier for unique folder name:\n")
        currentPath = currentPath+NewFilteredPath
        #NoisePath = ImagePath+'Noise/'+NewFilteredPath
        os.makedirs(currentPath)
        #os.makedirs(NoisePath)
    else:
        print('You didnt put Y or N')
ExposureTime = 10   #10 ms
EMGain = 3  # a value of 3 on the EM gain is equivalent to no gain. Not recommended to use EM Gain above 100
AutoFocus(InitialVoltage,ExposureTime,EMGain)   

