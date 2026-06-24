import cv2
import numpy as np

img = cv2.imread("./image.jpg")

# gray  = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
# rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
# hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# gray3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
# row = np.hstack([img,gray3,hsv, rgb])
# cv2.imshow("BGR | GRAY | HSV | RGB | GRAY ", row)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

gray  = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

rgb = cv2.cvtColor(gray, cv2.COLOR_BGR2RGB)

cv2.imshow("BRG",img)
cv2.imshow("GRAY",gray)
cv2.imshow("RGB",rgb)

# row = np.hstack([gray, rgb])
# cv2.imshow("BGR | GRAY | RGB", row)
cv2.waitKey(0)
cv2.destroyAllWindows()


