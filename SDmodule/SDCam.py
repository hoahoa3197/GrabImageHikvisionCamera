##################################################
# @author : HOA SD
# @version 08.11.0
##################################################
import cv2
import numpy as np
from .MvCameraControl_class import *
class SDCapture:
    def __init__(self,color = False):
        self.deviceList = MV_CC_DEVICE_INFO_LIST()
        self.buf_grab_image = None
        self.buf_grab_image_size = 0
        self.frame = None
        self.cam = MvCamera()
        self.openCamera()
        self.color = color
        self.stFrameInfo = MV_FRAME_OUT_INFO_EX()
        self.stPayloadSize = MVCC_INTVALUE_EX()
    def Mono_numpy(self,data, nWidth, nHeight):
        """ Convert Buffer Image to Mono_numpy
        Arguments:
            data: Buffer Data
            nWidth : Width of Buffer Image
            nHeight : Height of Buffer Image
        Returns:
            numArray[NDArray]: numpy Array.
        Example:
            >>> numArray = Mono_numpy(buffGrabImage , nWidth , nHeight)
        """
        data_ = np.frombuffer(data, count=int(nWidth * nHeight), dtype=np.uint8, offset=0)
        data_mono_arr = data_.reshape(nHeight, nWidth)
        numArray = np.zeros([nHeight, nWidth, 1], "uint8")
        numArray[:, :, 0] = data_mono_arr
        return numArray
    def Color_numpy(self,data, nWidth, nHeight):
        """ Convert Buffer Image to Numpy Color
        Arguments:
            data: Buffer Data
            nWidth : Width of Buffer Image
            nHeight : Height of Buffer Image
        Returns:
            numArray[NDArray]: numpy Array.
        Example:
            >>> numArray = Color_numpy(buffGrabImage , nWidth , nHeight)
        """
        data_ = np.frombuffer(data, count=int(nWidth * nHeight * 3), dtype=np.uint8, offset=0)
        data_r = data_[0:nWidth * nHeight * 3:3]
        data_g = data_[1:nWidth * nHeight * 3:3]
        data_b = data_[2:nWidth * nHeight * 3:3]

        data_r_arr = data_r.reshape(nHeight, nWidth)
        data_g_arr = data_g.reshape(nHeight, nWidth)
        data_b_arr = data_b.reshape(nHeight, nWidth)
        numArray = np.zeros([nHeight, nWidth, 3], "uint8")

        numArray[:, :, 0] = data_r_arr
        numArray[:, :, 1] = data_g_arr
        numArray[:, :, 2] = data_b_arr
        return numArray
        
    def findCamera(self):
        ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE,self.deviceList)
        if ret != 0:
            print ("[Error] Search Device False !")
            return ret

        if self.deviceList.nDeviceNum == 0:
            print ("[Error] Find no device!")
            return ret
        for i in range(0, self.deviceList.nDeviceNum):
            mvcc_dev_info = cast(self.deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                self.strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                    self.strModeName = self.strModeName + chr(per)
                    self.strModeName = self.strModeName.replace("\x00","")
                nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                self.currentIp = "%d.%d.%d.%d" % (nip1, nip2, nip3, nip4)
                print({"index":i,"name": self.strModeName,"ip":self.currentIp})
                return {"index":i,"name": self.strModeName,"ip":self.currentIp}
                
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print ("\nu3v device: [%d]" % i)
                self.strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if per == 0:
                        break
                    self.strModeName = self.strModeName + chr(per)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print({"index":i,"name": self.strModeName})
                return {"index":i,"name": self.strModeName}
                      
    def openCamera(self):
        try:
            self.indexCamera = self.findCamera()['index']
            stDeviceList = cast(self.deviceList.pDeviceInfo[int(self.indexCamera)],
                                POINTER(MV_CC_DEVICE_INFO)).contents
            ret = self.cam.MV_CC_CreateHandle(stDeviceList)
            if ret != 0:
                self.cam.MV_CC_DestroyHandle()
                return ret

            ret = self.cam.MV_CC_OpenDevice()
            if ret != 0:
                return {"status":"Error" , "message":"Open Camera Error ! "}

            # Detection network optimal package size(It only works for the GigE camera)
            if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
                nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
                if int(nPacketSize) > 0:
                    ret = self.cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
                    if ret != 0:
                        print("warning: set packet size fail! ret[0x%x]" % ret)
                else:
                    print("warning: set packet size fail! ret[0x%x]" % nPacketSize)
            return True
        except Exception as e:
            print("Open Camera Error !! ")
            self.closeCamera()
            return e
    def startGrabbing(self):
        self.cam.MV_CC_StartGrabbing()
        return True
    def closeCamera(self):
        self.Stop_grabbing()
        self.cam.MV_CC_CloseDevice()
        self.cam.MV_CC_DestroyHandle()
        return True
    def loadConfig(self,pathConfig):
        try:
            print("Importing Config File ...")
            ret = self.cam.MV_CC_FeatureLoad(pathConfig)
            if MV_OK != ret:
                    print ("Load Feature Config Failed ! ")
                    return False
            print("Load Feature Config Successfuly !")
            return True
        except:
            self.closeCamera()
            return False
    def saveConfig(self,pathConfig):
        try:
            print("Saving Config File ...")
            ret = self.cam.MV_CC_FeatureSave(pathConfig)
            if MV_OK != ret:
                print ("Save Feature Config Failed !")
                self.closeCamera()
                return False
            print ("Save Feature Config Successfuly !")
            self.closeCamera()
            return True
        except:
            self.closeCamera()
            return False
    def read(self):
        """Capture Image From Camera 
        Returns:
            numArray[NDArray]: numpy Array.
        """
        try:
            ret_temp = self.cam.MV_CC_GetIntValueEx("PayloadSize", self.stPayloadSize)
            if ret_temp != MV_OK:
                return
            NeedBufSize = int(self.stPayloadSize.nCurValue)
            if self.buf_grab_image_size < NeedBufSize:
                self.buf_grab_image = (c_ubyte * NeedBufSize)()
                self.buf_grab_image_size = NeedBufSize
            self.cam.MV_CC_GetOneFrameTimeout(self.buf_grab_image, self.buf_grab_image_size, self.stFrameInfo)
            if self.color == True:
                return cv2.cvtColor(self.Color_numpy(self.buf_grab_image,self.stFrameInfo.nWidth,self.stFrameInfo.nHeight),cv2.COLOR_BGR2RGB)
            return self.Mono_numpy(self.buf_grab_image,self.stFrameInfo.nWidth,self.stFrameInfo.nHeight)
        
        except Exception as e :
            return {'status' : 'error' , 'message':e}
        
    def Stop_grabbing(self):
        self.cam.MV_CC_StopGrabbing()
        return True
# cap = SDCapture(color= True)
# cap.startGrabbing()
# while True:
#     frame = cap.read()
#     frame_Resize = cv2.resize(frame,(1000,1000))
#     cv2.imshow("Frame" , frame_Resize)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         cap.closeCamera()
#         break
# cv2.destroyAllWindows()
    