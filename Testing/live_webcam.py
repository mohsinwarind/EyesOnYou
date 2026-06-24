import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: We can't open the Camera , there is some kind of error")
    exit()

i=0
while True:
    ret,frame = cap.read()
    if not ret:
        print("Frame grab failed")
        break
   
    cv2.imshow("WebCam - press Q to quit ",frame)
    
    i= i+1
    print(i," Frame : ",frame.shape)
    print(i," Retrive : ",ret)
   
    if cv2.waitKey(1) & 0xFF== ord('q'):
        break

cap.release()
cv2.destroyAllWindows()