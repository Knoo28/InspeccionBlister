import cv2
from ultralytics import YOLO
import tkinter as tk
from PIL import Image, ImageTk

# Cargar modelo
model = YOLO("Modelos/best.pt")
model.to('cuda')

# Configurar cámara
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Crear interfaz
root = tk.Tk()
root.title("Blister Detection")

frame_main = tk.Frame(root)
frame_main.pack()

label_video = tk.Label(frame_main)
label_video.grid(row=0, column=0)

frame_labels = tk.Frame(frame_main, padx=10, pady=10)
frame_labels.grid(row=0, column=1, sticky="n")

# --- Encabezado para la muestra de etiquetas ---
title_label = tk.Label(frame_labels, text="Etiquetas", font=("Arial", 16, "bold"))
title_label.pack()

detected_labels_text = tk.StringVar()
detected_labels_label = tk.Label(frame_labels, textvariable=detected_labels_text, font=("Arial", 14))
detected_labels_label.pack(pady=(10, 10))

# --- Encabezado para el conteo ---
count_header = tk.Label(frame_labels, text="Conteo de Pastillas", font=("Arial", 16, "bold"))
count_header.pack(pady=(10, 0))

# Contadores
counter_text = tk.StringVar()
counter_label = tk.Label(frame_labels, textvariable=counter_text, font=("Arial", 14))
counter_label.pack(pady=(0, 20))

# --- Encabezado para el diagnóstico ---
diagnosis_header = tk.Label(frame_labels, text="Diagnóstico", font=("Arial", 16, "bold"))
diagnosis_header.pack(pady=(10, 0))

# Estado final
status_text = tk.StringVar()
status_label = tk.Label(frame_labels, textvariable=status_text, font=("Arial", 18, "bold"))
status_label.pack()


# Lógica de detección y actualización
def update_frame():
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (640, 480))
        results = model(frame)

        boxes = results[0].boxes
        class_ids = boxes.cls.cpu().numpy() if boxes.cls is not None else []

        if len(class_ids) == 0:
            # No se detectó ningún objeto
            detected_labels_text.set("Sin detección")
            counter_text.set("Llenos: 0 | Vacíos: 0")
            status_text.set("Sin detección")
            status_label.config(fg="black")
        else:
            class_names = [results[0].names[int(cls)] for cls in class_ids]

            full_count = class_names.count("Full")
            empty_count = class_names.count('Empty')

            detected_labels_text.set(" | ".join(set(class_names)))
            counter_text.set(f"Llenos: {full_count} | Vacíos: {empty_count}")

            if empty_count > 0:
                status_text.set("BLISTER NO APTO")
                status_label.config(fg="red")
            else:
                status_text.set("APTO")
                status_label.config(fg="green")

        # Mostrar imagen anotada
        annotated_frame = results[0].plot()
        annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(annotated_frame)
        imgtk = ImageTk.PhotoImage(image=img)

        label_video.imgtk = imgtk
        label_video.configure(image=imgtk)

    label_video.after(10, update_frame)

# Cierre seguro
def on_closing():
    cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Iniciar
update_frame()
root.mainloop()
