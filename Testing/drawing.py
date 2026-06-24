import cv2
import numpy as np

canvas = np.zeros((500,800,3), dtype="uint8")

# Rectangle: (image, top-left, bottom-right, BGR color, thickness)

cv2.rectangle(canvas,(50,50),(200,150),(45,255,53),2)

# Filled rectangle (thickness = -1)

cv2.rectangle(canvas ,(250,50),(400,150),(25,100,100),-1)


# Circle: (image, center, radius, color, thickness)
cv2.circle(canvas, (500, 100), 60, (255, 255, 0), 3)

# Filled circle
cv2.circle(canvas, (650, 100), 60, (255, 0, 255), -1)

# Line: (image, pt1, pt2, color, thickness)
cv2.line(canvas, (50, 200), (750, 200), (255, 255, 255), 2)

# Polyline (triangle)
pts = np.array([[400, 300], [300, 450], [500, 450]], dtype=np.int32)
cv2.polylines(canvas, [pts], isClosed=True, color=(0, 165, 255), thickness=2)

# Text: (image, text, origin, font, scale, color, thickness)
cv2.putText(canvas, "OpenCV Drawing", (50, 470),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 200, 200), 2)


cv2.imshow("Canvas",canvas)
cv2.waitKey(0)                    # wait forever until any key
cv2.destroyAllWindows()