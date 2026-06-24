import cv2

img = cv2.imread("./image.jpg")

print("Shape:", img.shape)        # (height, width, channels)
print("Dtype:", img.dtype)        # uint8
print("Size:", img.size)          # total pixels * channels

cv2.imshow("Image", img)
cv2.waitKey(0)                    # wait forever until any key
cv2.destroyAllWindows()