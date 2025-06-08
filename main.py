import cv2
from ultralytics import YOLO

model = YOLO("Modelos/best.pt")
model.to('cuda')  # Fuerza GPU

cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (640, 480))

    results = model(frame)
    annotated_frame = results[0].plot()

    cv2.imshow("Blister Detection", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
