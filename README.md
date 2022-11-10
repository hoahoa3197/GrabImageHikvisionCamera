# GrabImageHikvisionCamera
 Grab image from camera hikvision
 ## Usage
 ```python
from SDmodule.SDCam import *
import cv2
cap = SDCapture(color= True)
cap.startGrabbing()
while True:
    frame = cap.read()
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cap.closeCamera()
        break
cv2.destroyAllWindows()
    
