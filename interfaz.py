import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import cv2
from tkcalendar import DateEntry
import time
import pandas as pd
from datetime import datetime
import os
from deteccion import detectar_camaras_disponibles, iniciar_camara, detectar_en_frame, liberar_camara

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

neon_verde = "#39ff14"
neon_rojo = "#ff3131"
blanco = "#ffffff"

# Variables globales de estado
current_full_count = 0
current_empty_count = 0
current_status = "Sin detección"
archivo_excel = "registro_pastillas.xlsx"

running = True
cap = None
selected_camera_index = 0
min_video_width = 640
min_video_height = 480

def salir(ventana):
    global running, cap
    running = False
    if cap is not None:
        cap.release()
    ventana.destroy()

def crear_dashboard_lateral():
    global root, label_video, detected_labels_text, counter_text, status_text, running, cap, selected_camera_index, combo_camaras
    global current_full_count, current_empty_count, current_status, archivo_excel, tabla_historial_text

    running = True
    root = ctk.CTk()
    root.title("Blister Detection - Dashboard Lateral")
    root.geometry("1100x700")

    camaras = detectar_camaras_disponibles(5)
    if not camaras:
        camaras = [0]
    camara_strs = [f"Cámara {i}" for i in camaras]

    # Layout: frame izquierdo (dashboard), frame derecho (contenido)
    frame_dashboard = ctk.CTkFrame(root, width=200)
    frame_dashboard.pack(side="left", fill="y")

    label_reloj = ctk.CTkLabel(frame_dashboard, text="", font=("Segoe UI", 16, "bold"))
    label_reloj.pack(pady=20)

    def actualizar_reloj():
        hora_actual = time.strftime("%H:%M:%S")
        label_reloj.configure(text=hora_actual)
        label_reloj.after(1000, actualizar_reloj)

    actualizar_reloj()

    frame_contenido = ctk.CTkFrame(root)
    frame_contenido.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    # Variables para gestionar frames de contenido
    frames = {}

    # Función para cambiar vista
    def mostrar_frame(nombre):
        for f in frames.values():
            f.pack_forget()
        frames[nombre].pack(fill="both", expand=True)

    # ---------------------- FRAME Detección ------------------------
    frame_detec = ctk.CTkFrame(frame_contenido)
    frames["Detección"] = frame_detec

    frame_main = ctk.CTkFrame(frame_detec)
    frame_main.pack(fill="both", expand=True, padx=15, pady=15)

    frame_main.grid_columnconfigure(0, weight=1)
    frame_main.grid_columnconfigure(1, weight=0)
    frame_main.grid_rowconfigure(0, weight=1)

    frame_video = ctk.CTkFrame(frame_main)
    frame_video.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    label_video = ctk.CTkLabel(frame_video, text="", width=min_video_width, height=min_video_height)
    label_video.pack(fill="both", expand=True)

    frame_labels = ctk.CTkFrame(frame_main, width=300)
    frame_labels.grid(row=0, column=1, sticky="ns", padx=15, pady=15)

    ctk.CTkLabel(frame_labels, text="Seleccionar Cámara", font=("Segoe UI", 16, "bold")).pack(pady=(10, 5))
    combo_camaras = ctk.CTkComboBox(frame_labels, values=camara_strs, font=("Segoe UI", 13))
    combo_camaras.pack(pady=(0, 15))
    combo_camaras.set(camara_strs[0])
    global selected_camera_index
    selected_camera_index = camaras[0]

    def cambiar_camara(event=None):
        global cap, selected_camera_index
        nuevo_indice = combo_camaras.get()
        nuevo_index_cam = int(nuevo_indice.split()[1])

        if nuevo_index_cam == selected_camera_index:
            return

        try:
            iniciar_camara(nuevo_index_cam)
            selected_camera_index = nuevo_index_cam
        except RuntimeError as e:
            messagebox.showerror("Error", str(e))
            iniciar_camara(selected_camera_index)
            combo_camaras.set(f"Cámara {selected_camera_index}")

    combo_camaras.bind("<FocusOut>", cambiar_camara)

    ctk.CTkLabel(frame_labels, text="Etiquetas Detectadas", font=("Segoe UI", 16, "bold")).pack()
    detected_labels_text = ctk.StringVar(value="Sin detección")
    ctk.CTkLabel(frame_labels, textvariable=detected_labels_text, font=("Segoe UI", 13)).pack(pady=(10, 10))

    ctk.CTkLabel(frame_labels, text="Conteo de Pastillas", font=("Segoe UI", 16, "bold")).pack(pady=(10, 0))
    counter_text = ctk.StringVar(value="Llenos: 0 | Vacíos: 0")
    ctk.CTkLabel(frame_labels, textvariable=counter_text, font=("Segoe UI", 13)).pack(pady=(0, 20))

    ctk.CTkLabel(frame_labels, text="Diagnóstico", font=("Segoe UI", 16, "bold")).pack(pady=(10, 0))
    status_text = ctk.StringVar(value="Sin detección")
    status_label = ctk.CTkLabel(frame_labels, textvariable=status_text, font=("Segoe UI", 18, "bold"))
    status_label.pack()

    def guardar_en_excel():
        global current_full_count, current_empty_count, current_status, archivo_excel

        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        datos = {
            "FechaHora": [hora_actual],
            "Llenos": [current_full_count],
            "Vacíos": [current_empty_count],
            "Estado": [current_status]
        }

        df_nuevo = pd.DataFrame(datos)

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
            messagebox.showinfo("Éxito", f"Datos guardados correctamente en Excel:\n{archivo_excel}")
            filtrar_historial()  # Actualizar tabla historial
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo Excel.\n{e}")

    ctk.CTkButton(frame_labels, text="Guardar datos en Excel", command=guardar_en_excel).pack(pady=10, fill='x')

    try:
        iniciar_camara(selected_camera_index)
    except RuntimeError as e:
        messagebox.showerror("Error", str(e))

    def update_frame():
        global current_full_count, current_empty_count, current_status

        if not running:
            return

        frame, results = detectar_en_frame()
        if frame is not None and results is not None:
            boxes = results[0].boxes
            class_ids = boxes.cls.cpu().numpy() if boxes.cls is not None else []

            if len(class_ids) == 0:
                detected_labels_text.set("Sin detección")
                counter_text.set("Llenos: 0 | Vacíos: 0")
                status_text.set("Sin detección")
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
                    status_label.configure(text_color=neon_rojo)
                    current_status = "NO APTO"
                else:
                    status_text.set("APTO")
                    status_label.configure(text_color=neon_verde)
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

    # --------------------- FRAME Historial ------------------------
    frame_historial = ctk.CTkFrame(frame_contenido)
    frames["Historial"] = frame_historial
    ctk.CTkLabel(frame_historial, text="Historial de Detecciones", font=("Segoe UI", 20, "bold")).pack(pady=10)

    # Entrada para filtro por fecha
    filtro_fecha_entry = DateEntry(frame_historial, date_pattern='yyyy-MM-dd', width=15)
    filtro_fecha_entry.pack(pady=(0, 10), padx=10, anchor="w")

    def filtrar_historial():
        filtro = filtro_fecha_entry.get().strip()
        tabla_historial_text.configure(state="normal")
        tabla_historial_text.delete("1.0", "end")

        if os.path.exists(archivo_excel):
            try:
                df = pd.read_excel(archivo_excel)
                # Convertir columna a datetime para mejor comparación
                df["FechaHora"] = pd.to_datetime(df["FechaHora"], errors='coerce')

                if filtro:
                    try:
                        filtro_dt = pd.to_datetime(filtro)
                        df_filtrado = df[df["FechaHora"].dt.date == filtro_dt.date()]
                        if df_filtrado.empty:
                            tabla_historial_text.insert("end", f"No se encontraron registros para la fecha {filtro}.")
                        else:
                            tabla_historial_text.insert("end", df_filtrado.to_string(index=False))
                    except Exception as e:
                        tabla_historial_text.insert("end", f"Formato de fecha inválido. Use YYYY-MM-DD.\n{e}")
                else:
                    tabla_historial_text.insert("end", df.to_string(index=False))
            except Exception as e:
                tabla_historial_text.insert("end", f"Error al cargar historial:\n{e}")
        else:
            tabla_historial_text.insert("end", "No se encontró el archivo de historial.")

        tabla_historial_text.configure(state="disabled")

    ctk.CTkButton(frame_historial, text="Filtrar por Fecha", command=filtrar_historial).pack(pady=(0, 10))

    tabla_historial_text = ctk.CTkTextbox(frame_historial, width=880, height=540, font=("Consolas", 12))
    tabla_historial_text.pack(padx=15, pady=10, fill="both", expand=True)

    # Cargar todo el historial inicialmente
    filtrar_historial()

    # --------------------- FRAME Configuración ------------------------
    frame_config = ctk.CTkFrame(frame_contenido)
    frames["Configuración"] = frame_config
    ctk.CTkLabel(frame_config, text="Configuración", font=("Segoe UI", 20, "bold")).pack(pady=15)

    ctk.CTkLabel(frame_config, text="Seleccionar Cámara", font=("Segoe UI", 16)).pack(pady=(10,5))
    combo_camaras_config = ctk.CTkComboBox(frame_config, values=camara_strs, font=("Segoe UI", 14))
    combo_camaras_config.pack(pady=(0, 20))
    combo_camaras_config.set(camara_strs[0])

    def aplicar_camara_config():
        nuevo_indice = combo_camaras_config.get()
        nuevo_index_cam = int(nuevo_indice.split()[1])

        global selected_camera_index
        if nuevo_index_cam != selected_camera_index:
            try:
                iniciar_camara(nuevo_index_cam)
                selected_camera_index = nuevo_index_cam
                combo_camaras.set(nuevo_indice)
            except RuntimeError as e:
                messagebox.showerror("Error", str(e))
                iniciar_camara(selected_camera_index)
                combo_camaras_config.set(f"Cámara {selected_camera_index}")

    ctk.CTkButton(frame_config, text="Aplicar Cámara", command=aplicar_camara_config).pack()

    ctk.CTkLabel(frame_config, text="Archivo Excel para Registro", font=("Segoe UI", 16)).pack(pady=(20, 5))
    archivo_path_var = ctk.StringVar(value=archivo_excel)
    entry_archivo = ctk.CTkEntry(frame_config, textvariable=archivo_path_var, width=300)
    entry_archivo.pack(pady=(0,10))

    def seleccionar_archivo():
        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                           filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if ruta:
            archivo_path_var.set(ruta)

    ctk.CTkButton(frame_config, text="Seleccionar Archivo...", command=seleccionar_archivo).pack(pady=(0, 20))

    def guardar_configuracion():
        global archivo_excel
        archivo_excel = archivo_path_var.get()
        messagebox.showinfo("Configuración", "Configuración guardada correctamente.")
        filtrar_historial()  # Actualiza historial con posible nuevo archivo

    ctk.CTkButton(frame_config, text="Guardar Configuración", command=guardar_configuracion).pack()

    # --------------------- Botones Dashboard -------------------------
    btn_detec = ctk.CTkButton(frame_dashboard, text="Detección", command=lambda: mostrar_frame("Detección"))
    btn_detec.pack(fill="x", pady=15, padx=10)

    btn_hist = ctk.CTkButton(frame_dashboard, text="Historial", command=lambda: mostrar_frame("Historial"))
    btn_hist.pack(fill="x", pady=15, padx=10)

    btn_config = ctk.CTkButton(frame_dashboard, text="Configuración", command=lambda: mostrar_frame("Configuración"))
    btn_config.pack(fill="x", pady=15, padx=10)

    # Mostrar por defecto la detección
    mostrar_frame("Detección")
    update_frame()

    root.protocol("WM_DELETE_WINDOW", lambda: salir(root))
    root.mainloop()

# Inicia la aplicación
if __name__ == "__main__":
    crear_dashboard_lateral()