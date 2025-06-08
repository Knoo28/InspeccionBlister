import cv2
from ultralytics import YOLO
import tkinter as tk
from PIL import Image, ImageTk

# Cargar modelo
model = YOLO("Modelos/best.pt")
model.to('cuda')

# Configurar cámara
cap = cv2.VideoCapture(1)

# Crear interfaz
root = tk.Tk()
root.title("Blister Detection")
root.geometry("1024x600")
root.configure(bg="#2e4863")  # Fondo general
root.minsize(1024, 600)

# Configurar grid adaptativo
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

# Marco principal
frame_main = tk.Frame(root, bg="#2e4863")
frame_main.grid(row=0, column=0, sticky="nsew")
frame_main.columnconfigure(0, weight=1)
frame_main.columnconfigure(1, weight=0)
frame_main.rowconfigure(0, weight=1)

# Tamaño mínimo del video
min_video_width = 640
min_video_height = 480

# Estilo de recuadros 3D
recuadro_estilo = {
    "bd": 4,
    "relief": "ridge",
    "bg": "#1f3247"
}

# Video (panel izquierdo con borde)
frame_video = tk.Frame(frame_main, **recuadro_estilo)
frame_video.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
label_video = tk.Label(frame_video, width=min_video_width, height=min_video_height, bg="#000000")
label_video.pack(fill="both", expand=True)

# Panel derecho (información)
frame_labels = tk.Frame(frame_main, **recuadro_estilo, width=500)
frame_labels.grid(row=0, column=1, sticky="ns", padx=15, pady=15)
frame_labels.grid_propagate(False)

# Contenido interior centrado
inner_frame = tk.Frame(frame_labels, bg="#1f3247")
inner_frame.pack(expand=True)

# Estilo de texto
titulo_fuente = ("Segoe UI", 16, "bold")
texto_fuente = ("Segoe UI", 13)
neon_verde = "#39ff14"
neon_rojo = "#ff3131"
blanco = "#ffffff"

# Etiquetas detectadas
title_label = tk.Label(inner_frame, text="Etiquetas Detectadas", font=titulo_fuente, fg=blanco, bg="#1f3247")
title_label.pack()

detected_labels_text = tk.StringVar()
detected_labels_label = tk.Label(inner_frame, textvariable=detected_labels_text, font=texto_fuente, fg=blanco, bg="#1f3247")
detected_labels_label.pack(pady=(10, 10))

# Conteo
count_header = tk.Label(inner_frame, text="Conteo de Pastillas", font=titulo_fuente, fg=blanco, bg="#1f3247")
count_header.pack(pady=(10, 0))

counter_text = tk.StringVar()
counter_label = tk.Label(inner_frame, textvariable=counter_text, font=texto_fuente, fg=blanco, bg="#1f3247")
counter_label.pack(pady=(0, 20))

# Diagnóstico
diagnosis_header = tk.Label(inner_frame, text="Diagnóstico", font=titulo_fuente, fg=blanco, bg="#1f3247")
diagnosis_header.pack(pady=(10, 0))

status_text = tk.StringVar()
status_label = tk.Label(inner_frame, textvariable=status_text, font=("Segoe UI", 18, "bold"), bg="#1f3247")
status_label.pack()

# Actualizar frame
def update_frame():
    ret, frame = cap.read()
    if ret:
        results = model(frame)
        boxes = results[0].boxes
        class_ids = boxes.cls.cpu().numpy() if boxes.cls is not None else []

        if len(class_ids) == 0:
            detected_labels_text.set("Sin detección")
            counter_text.set("Llenos: 0 | Vacíos: 0")
            status_text.set("Sin detección")
            status_label.config(fg=blanco)
        else:
            class_names = [results[0].names[int(cls)] for cls in class_ids]
            full_count = class_names.count("Full")
            empty_count = class_names.count("Empty")
            detected_labels_text.set(" | ".join(set(class_names)))
            counter_text.set(f"Llenos: {full_count} | Vacíos: {empty_count}")
            if empty_count > 0:
                status_text.set("BLISTER NO APTO")
                status_label.config(fg=neon_rojo)
            else:
                status_text.set("APTO")
                status_label.config(fg=neon_verde)

        annotated_frame = results[0].plot()
        annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)

        width = max(label_video.winfo_width(), min_video_width)
        height = max(label_video.winfo_height(), min_video_height)
        annotated_frame = cv2.resize(annotated_frame, (width, height))

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

# Iniciar loop
update_frame()
root.mainloop()
