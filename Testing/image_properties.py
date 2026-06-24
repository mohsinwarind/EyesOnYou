import cv2
import numpy as np
img = cv2.imread("./image.jpg")

h,w,c = img.shape

print(f"Height : {h} , Width : {w}, Channels: {c}")


b,g,r = cv2.split(img)

print(f"Blue channel shape: {b}, Green channel shape: {g}, Red channel shape: {r}")

print(f"Blue channel shape: {b.shape}, Green channel shape: {g.shape}, Red channel shape: {r.shape}")


myimage = cv2.imread("./me.jpeg")
b,g,r = cv2.split(myimage)

combined = np.hstack([b,g,r])

cv2.imshow("B | G | R", combined)

cv2.waitKey(0)                    # wait forever until any key
cv2.destroyAllWindows()