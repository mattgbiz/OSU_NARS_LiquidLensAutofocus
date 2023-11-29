#This file will aim to emulate the file given by Corning Varioptic for MATLAB
#I need to connect to both a .dll and .h file and try to get the functions from them
from ctypes import *
from sys import platform


def ChangeVoltage(Voltage):
    #need to ensure the library path is in the path defined below
    #this path needs to be changed to wherever the ComCasp64.dll is stored from the liquid lens.
    shared_lib_path = 'C:\\Users\\Public\\NeutronImaging\\LiquidLensWork\\ComCasp64.dll'

    #now we try to load the library
    try:
        Lens_Lib = CDLL(shared_lib_path)
        print("Successfully loaded",Lens_Lib)
    except Exception as e:
        print(e)

    #Connect to the lens
    eCOMCaspErr = Lens_Lib.Casp_OpenCOM()
    #print(eCOMCaspErr)
    if eCOMCaspErr == 0:
        print('Connection to Board Successful')
        #Next try to change the voltage to of the lens
        voltage = c_double(Voltage)
        eCOMCaspErr = Lens_Lib.Casp_SetFocusVoltage(voltage)
        #eCOMCaspErr = Lens_Lib.Casp_GetFocusVoltage()
        #print('Focus voltage is {}'.format(eCOMCaspErr))
        if eCOMCaspErr == 0:
            print('Voltage was successfully changed')
            VoltChange = 1
        else:
            print('Voltage Not Changed Error: {}'.format(eCOMCaspErr))
            VoltChange = 0 

        #Finally close the communication port
        eCOMCaspErr = Lens_Lib.Casp_CloseCOM()
        if eCOMCaspErr == 0:
            print('Successfully closed communication with Liquid Lens')
        else:
            print('Communication Not ended')
    else:
        print('Connection Unsuccessful')
        VoltChange = 0 
    return VoltChange 

