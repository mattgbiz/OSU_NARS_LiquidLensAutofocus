# OSU_NARS_LiquidLensAutofocus
Code is used to determine best voltage for focusing on an edge for in-situ neutron radiography focusing with a liquid lens.

ReadMe for Ohio State University Nuclear Analysis and Radiation Sensor (NARS) Codes for Liquid Lens Control and Autofocusing
*******************************************************************************************************
Original Author: Matthew Bisbee
Affiliations: Ohio State University Dept. of Mechanical and Aerospace Engineering, Nuclear Engineering
	      Nuclear Analysis and Radiation Sensor (NARS) Laboratory
	      DOE NEUP Fellowship FY19
	      Points of Contact: Advisor Dr. Raymond Cao - cao.152@osu.edu
			         Author Matthew Bisbee - bisbee.11@osu.edu
*******************************************************************************************************

Python script contents include: Autofocusing_KnifeEdge.py, LiquidControl.py, and NewCameraControl_Liquid.py

General Information: 

Each Python script is intended to run in Python3.X. I ran each code from VS code on a Windows 10 device. The liquid lens was an Edmund Optics lens where the applied voltage changes the index of refraction in the liquid portion of the lens setup. The scripts are used in finding the best focal point by adjusting working distance of the lens through voltage changes. The motivation of using  this lens and autofocusing code is to find the in focus working distance of a thick plastic scintillator in fast neutron imaging applications. 

Image acquisition requires an edge to calculate ESF then LSF (see later) for determining full width at half maximum (FWHM). The as FWHM is minimized, the edge is further in focus until deemed acceptable. Generally speaking, in the Ohio State imaging instrument, the best voltage was near 41.9 V and due to the working distance vs applied voltage curve of the liquid lens flattening here, very small changes in FWHM occur between 41 and 42.5 V.

Running the Autofocusing Script:

Autofocusing script uses the LiquidControl and NewCameraConrol_Liquid scripts so they must be in the same directory as Autofocusing script. At the bottom of the script I have a sample input for supplying initial voltage, exposure time, etc. The camera needs to be focusing on something with an edge to provide the LSF with a distinct peak for finding FWHM.

*******************************************************************************************

LiquidControl.py

This script is used to connect to the liquid lens through Python as opposed to the Corning Varioopitcs supplied GUI by manufacturer. The user would need .dll file on their local machine and supply the path to that file. The script has one function in which it connects to the lens controller, changes voltage, and disconnects.

*******************************************************************************************
NewCamaraControl_Liquid.py

This code is a modified script from the NARS tomography code that controls the Andor EMCCD camera through a Python wrapper pycromanager for the code Micro-Manager2.0. The script is used to take the images with specified exposure time and EM Gain and save the acquired image to specified location. 

********************************************************************************************
Autofocusing_KnifeEdge.py

This script has two main functions a FWHMFromImage(ImagePath,ROI_Input,ROI_Needed=Tru) and AutoFocus(InitialVoltage,ExposureTime, EMGain). The FWHMFromImage function takes the path to the already taken image and at the start of the code needs a user supplied ROI through a square ROI selected as the code is first run. That ROI is then supplied to subsequent images. The ROI is averaged by rows to provide an edge spread function (ESF). The derivative with respect to columns of the ESF produces the line spread function (LSF) which provides a peak at material boundary. The function calculates FWHM from the LSF peak and outputs the x array, LSF, region of interest and FWHM.

The second function AutoFocus is where each image is taken, voltage on liquid lens changed, and determination of best focal point is done. The code goes through an initial sweep of 10 voltages from the starting voltage (I usually did 35 V). Once the sweep from 35-44 V is done, the code determines what increment was best. If 35 or 44 V was best, then the code will continue from either of those direcitons to find where the FWHM is minimized with the coarse sweep. Then a refined sweep of 0.1 V is performed to further check what is the best FWHM. Again depending on working distance, the 1 V or 0.1 V changes may not have much of an impact on FWHM meaning that you have a range of voltages that are acceptably "In-focus."

********************************************************************************************************
Further Information:
     
How the code actually works can be seen if you take a look at Chapter 7 of the dissertation "Advancing Radiographic Acquisition and Post-Processing Capabilities for a University Research Reactor Fast and Thermal Neutron Radiography and Tomography Instrument" as that goes into more detail on logic and decisions. Otherwise, the code is fairly straightforward well commented, good luck!
