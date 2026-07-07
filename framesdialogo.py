#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import os, sys, urllib.parse
import tkinter as tk
from tkinter import ttk, filedialog as fd, simpledialog
from tkinter.messagebox import showerror, showinfo
from tkinter.constants import LEFT, RIGHT, TRUE
import logging

__author__ = 'Hernani Aleman Ferraz'
__email__ = 'afhernani@gmail.com'
__apply__ = 'framesdialogo - diálogo modal'
__version__ = '0.1'

__all__ = ('FramesDialog')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ============================================================
# NUEVO: Diálogo personalizado con slider para elegir frames
# ============================================================
class FramesDialog(tk.Toplevel):
    """Diálogo modal con slider para elegir el número de frames del GIF."""
    
    def __init__(self, parent, total_frames, fps_video, duration_video):
        super().__init__(parent)
        self.title("Configurar GIF")
        self.resizable(False, False)
        self.transient(parent)  # Siempre encima de la ventana padre
        self.grab_set()         # Modal
        
        self.result = None
        self.total_frames = int(total_frames)
        self.fps_video = fps_video
        self.duration_video = duration_video
        
        # Valor por defecto: 20 o el total si es menor
        default_value = min(20, max(1, self.total_frames))
        max_value = max(1, self.total_frames)
        
        # --- Contenido del diálogo ---
        main_frame = tk.Frame(self, padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        tk.Label(main_frame, text="Número de frames a extraer:",
                 font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        
        # Slider
        self.slider_var = tk.IntVar(value=default_value)
        self.slider = tk.Scale(
            main_frame,
            from_=1,
            to=max_value,
            orient=tk.HORIZONTAL,
            variable=self.slider_var,
            command=self._on_slider_change,
            length=350,
            resolution=1,
            tickinterval=max(1, max_value // 5),
            showvalue=False
        )
        self.slider.pack(fill=tk.X, pady=(5, 10))
        
        # Valor actual (grande y visible)
        self.value_label = tk.Label(
            main_frame,
            text=f"{default_value} frames",
            font=("Segoe UI", 14, "bold"),
            fg="#1976d2"
        )
        self.value_label.pack(pady=(0, 10))
        
        # Separador
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Info contextual
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(info_frame, text=f"Video: {self.total_frames} frames · {duration_video:.1f}s",
                 fg="gray").pack(anchor=tk.W)
        
        self.duration_gif_label = tk.Label(
            info_frame,
            text=self._calc_duration_gif_text(default_value),
            fg="gray"
        )
        self.duration_gif_label.pack(anchor=tk.W)
        
        # Botones
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.btn_cancel = tk.Button(btn_frame, text="Cancelar", width=12,
                                    command=self._on_cancel)
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        
        self.btn_ok = tk.Button(btn_frame, text="✓ Crear GIF", width=12,
                                bg="#1976d2", fg="white",
                                command=self._on_ok)
        self.btn_ok.pack(side=tk.RIGHT, padx=5)
        
        # Atajos de teclado
        self.bind('<Escape>', lambda e: self._on_cancel())
        self.bind('<Return>', lambda e: self._on_ok())
        
        # Centrar sobre la ventana padre
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Esperar a que se cierre
        self.wait_window(self)
    
    def _on_slider_change(self, value):
        """Actualiza las etiquetas cuando cambia el slider."""
        n = int(float(value))
        self.value_label.config(text=f"{n} frame{'s' if n != 1 else ''}")
        self.duration_gif_label.config(text=self._calc_duration_gif_text(n))
    
    def _calc_duration_gif_text(self, n_frames):
        """Calcula la duración estimada del GIF (asumiendo 0.8s por frame de intervalo)."""
        # La duración total del GIF = n_frames * (duración_video / (n_frames+1))
        # Simplificado: duration_per_frame ≈ duration_video / (n_frames + 1)
        if n_frames <= 0:
            return "Duración estimada del GIF: 0.0s"
        duration_per_frame = self.duration_video / (n_frames + 1)
        total_gif_duration = n_frames * duration_per_frame
        return f"Duración estimada del GIF: {total_gif_duration:.1f}s"
    
    def _on_ok(self):
        self.result = self.slider_var.get()
        self.grab_release()
        self.destroy()
    
    def _on_cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()
