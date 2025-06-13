import cv2
from ultralytics import YOLO
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import pandas as pd
from datetime import datetime
import os

# Colores y fuentes globales
neon_verde = "#39ff14"
neon_rojo = "#ff3131"
blanco = "#ffffff"
fondo_ventana = "#2e4863"
fondo_panel = "#1f3247"
titulo_fuente = ("Segoe UI", 16, "bold")
texto_fuente = ("Segoe UI", 13)

# Cargar modelo YOLO
model = YOLO("Modelos/best.pt")
model.to('cuda')

# Variables globales
running = True
cap = None
selected_camera_index = 0  # cámara por defecto

# Tamaños mínimos del video
min_video_width = 640
min_video_height = 480

# Variables para guardar conteo y estado actuales
current_full_count = 0
current_empty_count = 0
current_status = "Sin detección"

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

def crear_ventana_principal():
    global root, label_video, detected_labels_text, counter_text, status_text, running, cap, selected_camera_index, combo_camaras
    global current_full_count, current_empty_count, current_status

    running = True

    root = tk.Tk()
    root.title("Blister Detection")
    root.geometry("1024x650")
    root.configure(bg=fondo_ventana)
    root.minsize(1024, 650)

    # Configurar grid adaptativo
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    frame_main = tk.Frame(root, bg=fondo_ventana)
    frame_main.grid(row=0, column=0, sticky="nsew")
    frame_main.columnconfigure(0, weight=1)
    frame_main.columnconfigure(1, weight=0)
    frame_main.rowconfigure(0, weight=1)

    recuadro_estilo = {"bd": 4, "relief": "ridge", "bg": fondo_panel}

    # Panel video
    frame_video = tk.Frame(frame_main, **recuadro_estilo)
    frame_video.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    label_video = tk.Label(frame_video, width=min_video_width, height=min_video_height, bg="#000000")
    label_video.pack(fill="both", expand=True)

    # Panel derecho
    frame_labels = tk.Frame(frame_main, **recuadro_estilo, width=500)
    frame_labels.grid(row=0, column=1, sticky="ns", padx=15, pady=15)
    frame_labels.grid_propagate(False)

    inner_frame = tk.Frame(frame_labels, bg=fondo_panel)
    inner_frame.pack(expand=True)

    # ComboBox para seleccionar cámara
    label_cam = tk.Label(inner_frame, text="Seleccionar Cámara", font=titulo_fuente, fg=blanco, bg=fondo_panel)
    label_cam.pack(pady=(0,5))

    camaras = detectar_camaras_disponibles(5)
    if not camaras:
        camaras = [0]  # fallback por si no detecta ninguna

    camara_strs = [f"Cámara {i}" for i in camaras]
    combo_camaras = ttk.Combobox(inner_frame, values=camara_strs, state="readonly", font=texto_fuente)
    combo_camaras.current(0)
    selected_camera_index = camaras[0]
    combo_camaras.pack(pady=(0, 15))

    def cambiar_camara(event=None):
        global cap, selected_camera_index

        nuevo_indice = combo_camaras.current()
        if nuevo_indice < 0 or nuevo_indice >= len(camaras):
            return
        nuevo_index_cam = camaras[nuevo_indice]

        if nuevo_index_cam == selected_camera_index:
            return  # no cambiar si es la misma

        if cap is not None:
            cap.release()
        cap = cv2.VideoCapture(nuevo_index_cam)
        if not cap.isOpened():
            print(f"No se pudo abrir la cámara {nuevo_index_cam}, volviendo a cámara anterior {selected_camera_index}")
            cap = cv2.VideoCapture(selected_camera_index)
        else:
            selected_camera_index = nuevo_index_cam

    combo_camaras.bind("<<ComboboxSelected>>", cambiar_camara)

    # Etiquetas detectadas
    title_label = tk.Label(inner_frame, text="Etiquetas Detectadas", font=titulo_fuente, fg=blanco, bg=fondo_panel)
    title_label.pack()

    detected_labels_text = tk.StringVar(value="Sin detección")
    detected_labels_label = tk.Label(inner_frame, textvariable=detected_labels_text, font=texto_fuente, fg=blanco, bg=fondo_panel)
    detected_labels_label.pack(pady=(10, 10))

    # Conteo
    count_header = tk.Label(inner_frame, text="Conteo de Pastillas", font=titulo_fuente, fg=blanco, bg=fondo_panel)
    count_header.pack(pady=(10, 0))

    counter_text = tk.StringVar(value="Llenos: 0 | Vacíos: 0")
    counter_label = tk.Label(inner_frame, textvariable=counter_text, font=texto_fuente, fg=blanco, bg=fondo_panel)
    counter_label.pack(pady=(0, 20))

    # Diagnóstico
    diagnosis_header = tk.Label(inner_frame, text="Diagnóstico", font=titulo_fuente, fg=blanco, bg=fondo_panel)
    diagnosis_header.pack(pady=(10, 0))

    status_text = tk.StringVar(value="Sin detección")
    status_label = tk.Label(inner_frame, textvariable=status_text, font=("Segoe UI", 18, "bold"), bg=fondo_panel)
    status_label.pack()

    # Botón para guardar datos en Excel
    def guardar_en_excel():
        global current_full_count, current_empty_count, current_status

        # Preparar datos
        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        datos = {
            "FechaHora": [hora_actual],
            "Llenos": [current_full_count],
            "Vacíos": [current_empty_count],
            "Estado": [current_status]
        }

        df_nuevo = pd.DataFrame(datos)

        archivo_excel = "registro_pastillas.xlsx"

        if os.path.exists(archivo_excel):
            try:
                df_existente = pd.read_excel(archivo_excel)
                df_guardar = pd.concat([df_existente, df_nuevo], ignore_index=True)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo existente.\n{e}")
                return
        else:
            df_guardar = df_nuevo

        try:
            df_guardar.to_excel(archivo_excel, index=False)
            messagebox.showinfo("Éxito", "Datos guardados correctamente en Excel.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo Excel.\n{e}")

    boton_guardar = tk.Button(inner_frame, text="Guardar datos en Excel", font=texto_fuente, bg=neon_verde, fg="#000000",
                              activebackground=neon_verde, activeforeground="#000000", command=guardar_en_excel)
    boton_guardar.pack(pady=10, fill='x')

    # Abrir cámara inicial
    cap = cv2.VideoCapture(selected_camera_index)

    def update_frame():
        global current_full_count, current_empty_count, current_status

        if not running:
            return

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
                current_full_count = 0
                current_empty_count = 0
                current_status = "Sin detección"
            else:
                class_names = [results[0].names[int(cls)] for cls in class_ids]
                full_count = class_names.count("Full")
                empty_count = class_names.count("Empty")
                detected_labels_text.set(" | ".join(set(class_names)))
                counter_text.set(f"Llenos: {full_count} | Vacíos: {empty_count}")
                if empty_count > 0:
                    status_text.set("BLISTER NO APTO")
                    status_label.config(fg=neon_rojo)
                    current_status = "NO APTO"
                else:
                    status_text.set("APTO")
                    status_label.config(fg=neon_verde)
                    current_status = "APTO"
                current_full_count = full_count
                current_empty_count = empty_count

            annotated_frame = results[0].plot()
            annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)

            width = max(label_video.winfo_width(), min_video_width)
            height = max(label_video.winfo_height(), min_video_height)
            annotated_frame = cv2.resize(annotated_frame, (width, height))

            img = Image.fromarray(annotated_frame)
            imgtk = ImageTk.PhotoImage(image=img)

            label_video.imgtk = imgtk
            label_video.configure(image=imgtk)
        else:
            label_video.imgtk = None
            label_video.configure(image='')

        label_video.after(10, update_frame)

    def on_closing():
        global running, cap
        running = False
        if cap is not None:
            cap.release()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    update_frame()
    root.mainloop()

def ventana_carga():
    carga_root = tk.Tk()
    carga_root.title("Cargando sistema...")
    carga_root.geometry("400x120")
    carga_root.resizable(False, False)
    carga_root.configure(bg=fondo_ventana)

    label_cargando = tk.Label(carga_root, text="Cargando sistema...", font=titulo_fuente, fg=blanco, bg=fondo_ventana)
    label_cargando.pack(pady=10)

    barra_progreso = tk.Canvas(carga_root, width=300, height=20, bg=fondo_panel, bd=0, highlightthickness=0)
    barra_progreso.pack(pady=10)

    ancho_total = 300
    barra = barra_progreso.create_rectangle(0, 0, 0, 20, fill=neon_verde, width=0)

    tiempo_carga_ms = 3000  # 3 segundos de carga
    intervalo = 30          # intervalo de actualización en ms
    pasos = tiempo_carga_ms // intervalo
    incremento = ancho_total / pasos

    progreso = 0
    contador_pasos = 0

    def avanzar_barra():
        nonlocal progreso, contador_pasos
        if contador_pasos < pasos:
            progreso += incremento
            barra_progreso.coords(barra, 0, 0, progreso, 20)
            contador_pasos += 1
            carga_root.after(intervalo, avanzar_barra)
        else:
            barra_progreso.coords(barra, 0, 0, ancho_total, 20)
            carga_root.destroy()
            crear_ventana_principal()

    def parpadear_texto():
        current_color = label_cargando.cget("fg")
        nuevo_color = fondo_ventana if current_color == blanco else blanco
        label_cargando.config(fg=nuevo_color)
        carga_root.after(500, parpadear_texto)

    avanzar_barra()
    parpadear_texto()
    carga_root.mainloop()

if __name__ == "__main__":
    ventana_carga()
