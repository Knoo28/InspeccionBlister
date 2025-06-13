import cv2
from ultralytics import YOLO

model = YOLO("Modelos/best.pt")
model.to('cuda')

cap = None
selected_camera_index = 0

def detectar_camaras_disponibles(max_camaras=5):
    disponibles = []
    for i in range(max_camaras):
        cap_test = cv2.VideoCapture(i)
        if cap_test.isOpened():
            ret, frame = cap_test.read()
            if ret:
                disponibles.append(i)
            cap_test.release()
    return disponibles

def iniciar_camara(index):
    global cap, selected_camera_index
    if cap is not None:
        cap.release()
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir la cámara {index}")
    selected_camera_index = index
    return cap

def detectar_en_frame():
    global cap
    if cap is None:
        return None, None
    ret, frame = cap.read()
    if not ret:
        return None, None
    results = model(frame)
    return frame, results

def liberar_camara():
    global cap
    if cap is not None:
        cap.release()
        cap = None
