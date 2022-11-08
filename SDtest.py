from SDmodule.SDCam import *
import cv2
cap = SDCapture(color= True)
cap.startGrabbing()
while True:
    frame = cap.read()
    frame_Resize = cv2.resize(frame,(1000,1000))
    cv2.imshow("Frame" , frame_Resize)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cap.closeCamera()
        break
cv2.destroyAllWindows()
    