import cv2

img = cv2.imread("image.jpg")
h, w = img.shape[:2]

# Resize to fixed size
fixed = cv2.resize(img, (300, 300), interpolation=cv2.INTER_AREA)

# Resize by percentage
scale = 0.5
percent = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

# Crop: img[y1:y2, x1:x2]
crop = img[50:200, 100:300]

cv2.imshow("Original", img)
cv2.imshow("Fixed 300x300", fixed)
cv2.imshow("50% scale", percent)
cv2.imshow("Cropped ROI", crop)

cv2.waitKey(0)
cv2.destroyAllWindows()