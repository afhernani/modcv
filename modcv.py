#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os, sys
import tkinter as tk
from tkinter import Variable, ttk
from tkinter.constants import LEFT, RIGHT, TRUE
from tkinter.messagebox import showerror, showinfo
from tkinter import filedialog as fd
import cv2, threading
from PIL import Image, ImageTk
import time
import datetime
import logging, configparser

from lark import logger


__author__ = 'Hernani Aleman Ferraz'
__email__ = 'afhernani@gmail.com'
__apply__ = 'modcv - opencv'
__version__ = '0'

__all__ = ('MyVideoCapture')

logging.basicConfig(level=logging.DEBUG)

def get_base_path():
    """Obtiene la ruta base correcta según si es ejecutable o script."""
    if getattr(sys, 'frozen', False):
        # Estamos en un ejecutable de PyInstaller
        return sys._MEIPASS
    else:
        # Estamos en modo desarrollo (python modcv.py)
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

CONFIG_FILE = os.path.join(BASE_PATH, "config.ini")

def cargar_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config.get("Setings", "dirpathmovies", fallback=".")

def guardar_config(carpeta):
    config = configparser.ConfigParser()
    config["Setings"] = {"dirpathmovies": carpeta}
    with open(CONFIG_FILE, "w") as f:
        config.write(f)

class MyVideoCapture:
    """Captura de video con OpenCV, para usar en Tkinter. """
    
    def __init__(self, video_source=None, thumb=None):
        ''' thumb = (100, 100 )'''
        size = (100, 100 ) if thumb is None else thumb
        self.poss = 0.0 # posicion en milisegundos
        self.frames = []
        try:
            self.set_video(video_source)
            sec = round(self.seconds / 3 , 2)
            self.vid.set(cv2.CAP_PROP_POS_MSEC, sec*1000)
            ret, frame = self.vid.read()

            if ret:
                imagen = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                imagen_f = Image.fromarray(imagen)
                imagen_f.thumbnail(size)
            
            self.photo = ImageTk.PhotoImage(image=imagen_f)
            # TODO: Reinicamos al inicio para la reproduccion del video.
            self.vid.set(cv2.CAP_PROP_POS_MSEC, 0)

        except Exception as e:
            logging.warning(f"init: Exception: {str(e.args)}")
            raise ValueError(f"Unable to open video source: {video_source}")
        
    def set_info(self):
        """Obtiene información de la fuente de video."""
        if self.vid.isOpened():
            self.n_frames = self.vid.get(cv2.CAP_PROP_FRAME_COUNT)
            self.fps = int(self.vid.get(cv2.CAP_PROP_FPS))
            self.seconds = round((self.n_frames / self.fps), 3)
            self.time = str(datetime.timedelta(seconds=self.seconds))
        logger.info(f"Video info: {self.n_frames} frames, {self.fps} fps, {self.seconds} seconds, duration: {self.time}")
    
    def set_dimension(self):
        """Obtiene las dimensiones de la fuente de video."""
        if self.vid.isOpened():
            # Get video source width and height
            self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
            self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
        logger.info(f"Video dimensions: {self.width}x{self.height}")

    def set_only_video(self, url=None):
        '''reset VideoCapture url=None, --> self.url'''
        new_url=self.video_source if url is None else url
        self.vid =cv2.VideoCapture(new_url)

    def set_video(self, video_source):
        """Abre la fuente de video y obtiene información de la misma."""
        self.video_source=video_source if video_source is not None else None
        # if self.video_source: guardar_config(os.path.dirname(self.video_source))
        # Open the video source
        self.vid = cv2.VideoCapture(video_source)
        
        if not self.vid.isOpened():
            raise ValueError(f"Unable to open video source: {video_source}")
        # obtener informacion de la fuente de video
        self.set_dimension()
        self.set_info()

    def set_poss(self, sec):
        '''Posiciona el video en la secuencia de tiempo sec, en segundos, especificados.'''
        if self.vid.isOpened():
            self.vid.set(cv2.CAP_PROP_POS_MSEC,sec*1000)

    def get_frame(self):
        """Devuelve el siguiente frame de la fuente de video.
        Returns:"""
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            self.poss = self.vid.get(cv2.CAP_PROP_POS_MSEC)

            if ret:
                # Return a boolean success flag and the current frame converted to BGR
                return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                logging.info(f'valor ret: {ret}')
                self.set_poss(0) # posicionamos al principio
                return (ret, None)
        else:
            return (False, None)
            # raise ValueError(f"not open video source: {self.video_source}")

    def __get_frame_sec(self, sec):
        '''devuelve true/false, true, guarda imagen de la secuencia sec,
         en segundos.'''
        self.vid.set(cv2.CAP_PROP_POS_MSEC,sec*1000)
        ret, frame = self.vid.read()
        if ret:
            self.frames.append(frame)
            # cv2.imwrite("image"+str(count)+".jpg", image)     # save frame as JPG file
            return ret
        else:
            return False

    def save_gif_file(self, namefile="smiling", duration=0.8):
        """Crea un archivo GIF a partir de la fuente de video sin bloquear la interfaz de usuario. 
        Se extraen n frames del video y se guardan en un archivo GIF.
        Args:"""
        logging.info("[save_gif_file] Extracting frames from video...")
        self.frames.clear()
        # Usamos una instancia Temporal para evitar conflictos con la reproducción del video en la interfaz de usuario.
        temp_vid = cv2.VideoCapture(self.video_source)
        if not temp_vid.isOpened():
            logging.error(f"[save_gif_file] Unable to open video source: {self.video_source}")
            return ValueError(f"Unable to open video source: {self.video_source}")
        
        n_frames = int(temp_vid.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(temp_vid.get(cv2.CAP_PROP_FPS))
        total_sec = n_frames / fps if fps > 0 else 10


        logging.info("Extrayendo frames para el GIF ...")
        ntf = 20  # Número de frames a extraer
        rate_sec = round((total_sec / (ntf + 1)), 3)
        sec = rate_sec

        while sec <= total_sec:
            temp_vid.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
            ret, frame = temp_vid.read()
            if ret:
                self.frames.append(frame)
                logging.info(f"Frame extraído a {sec:.2f} segundos.")
            else:
                logging.warning(f"No se pudo extraer el frame a {sec:.2f} segundos.")
            sec += rate_sec
            sec = round(sec, 2)

        temp_vid.release()
        logging.info(f"Total de frames extraídos: {len(self.frames)}")

        # Guardar Gif
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if not namefile.lower().endswith('.gif'):
            namefile += f"_{timestamp}.gif"
        logging.info(f"Guardando archivo GIF: {namefile}")
        
        #  Convertimos todos los frames a PIL Image
        pil_frames = []
        for frame in self.frames:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            pil_frames.append(pil_img)
        
        # PIL usa MILISEGUNDOS para la duración
        duration_ms = int(duration * 1000)
        
        # Guardamos el GIF con Pillow directamente
        pil_frames[0].save(
            namefile,
            save_all=True,
            append_images=pil_frames[1:],
            duration=duration_ms,  # MILISEGUNDOS por frame
            loop=0                 # Bucle infinito
        )
        
        logging.info(f"GIF guardado: {namefile} con {len(pil_frames)} frames, "
                    f"duración por frame: {duration_ms}ms por frame")


    def __get_frames_from_video(self, nft=20):
        """Extrae n frames del video y los guarda en la lista self.frames."""
        rate_sec = round((self.seconds / (nft + 1)), 3)
        sec = rate_sec
        success = self.__get_frame_sec(sec)
        while success:
            sec += rate_sec
            sec = round(sec, 2)
            success = self.__get_frame_sec(sec)

    def release(self):
        """Libera los recursos del video."""
        if self.vid is not None and self.vid.isOpened():
            self.vid.release()


class App:
    def __init__(self, window, window_title, video_source=0, run_mainloop=True):
        self.window = window
        self.window_title = window_title
        self.window.title(window_title)
        self._set_window_icon()
        self.video_source = video_source
        self.stop = False
        self.v_time = tk.DoubleVar()
        self.all_time = tk.DoubleVar()

        # open video source (by default this will try to open the computer webcam)
        self.vid = MyVideoCapture(self.video_source)

        # self.vid.set_only_video()
        if not self.vid.vid.isOpened():
            showerror(title="Aviso", message=f"No se pudo abrir la fuente {self.video_source}")
            exit(0)
        
        # Create a canvas that can fit the above video source size
        self.all_time.set(self.vid.seconds)
        self.canvas = tk.Canvas(window, width = self.vid.width, height = self.vid.height)
        self.canvas.pack()

        # Frame contenedor
        self.frame = tk.Frame(self.window)

        # Button that lets the user take a snapshot
        self.btn_snapshot=tk.Button(self.frame, text="Snapshot", command=self.snapshot)
        self.btn_snapshot.pack(side=tk.LEFT) #anchor=tkinter.CENTER, expand=True)

        # Button that lets us to create a gif file.
        self.btn_gif=tk.Button(self.frame, text="Gif", command=self.gifshow)
        self.btn_gif.pack(side=tk.LEFT)
        # stop button
        self.btn_stop = tk.Button(self.frame, text='II', command=self.stopshow)
        self.btn_stop.pack(side=tk.LEFT)

        # slider.
        options={'tickinterval': 0 , 'showvalue': True, 'resolution':0.1}
        self.slider = tk.Scale(self.frame, from_=0,
                                to=self.all_time.get(), 
                                orient='horizontal',
                                command=self.slider_changed,
                                variable=self.v_time,
                                **options
                                 )
        self.slider.pack(side=LEFT, expand=True, fill=tk.BOTH)

        # Button that let us to open another video file.
        self.btn_open=tk.Button(self.frame, text="Open", command=self.openshow)
        self.btn_open.pack(side=tk.RIGHT)
        # Etiqueta time
        self.lb_time =tk.Label(self.frame, text="...", width=8)
        self.lb_time.pack(side=tk.RIGHT)

        # pack frame
        self.frame.pack(anchor=tk.CENTER, expand=TRUE, fill=tk.BOTH)

        # After it is called once, the update method will be automatically called every delay milliseconds
        logging.info(f"fps: {self.vid.fps}")
        self.window.bind('<Configure>', self.handle_resize)
        # Calculamos el delay basado en los FPS reales del video
        # Fórmula: delay_ms = 1000 / fps
        self.delay = max(1, int(1000 / self.vid.fps))
        logging.info(f"Video FPS: {self.vid.fps}, Calculated delay: {self.delay}ms")

        # Añade esto al final del __init__:
        self.gif_thread = None
        self.is_generating_gif = False
        self.status_var = tk.StringVar(value="Listo")
        self.status_label = tk.Label(self.frame, textvariable=self.status_var, fg="gray")
        self.status_label.pack(side=tk.RIGHT, padx=10)

        self.update()
        if run_mainloop:
            self.window.mainloop()


    def _set_window_icon(self):
        """Configura el icono de la ventana usando un archivo PNG."""
        try:
            # Ruta relativa al directorio del script
            icon_path = os.path.join(BASE_PATH, 'assets', 'modcv.png')
            
            if os.path.exists(icon_path):
                icon_image = Image.open(icon_path)
                # Crear PhotoImage desde PIL
                self.window_icon = ImageTk.PhotoImage(icon_image)
                self.window.iconphoto(True, self.window_icon)
                logging.info(f"Icono cargado: {icon_path}")
            else:
                logging.warning(f"Icono no encontrado: {icon_path}")
                self._set_default_icon()
        except Exception as e:
            logging.error(f"Error al cargar el icono: {e}")
            self._set_default_icon()
    
    def _set_default_icon(self):
        """Icono por defecto generado programáticamente (fallback)."""
        try:
            # Creamos un icono simple de 64x64 con un círculo azul
            icon = Image.new('RGB', (64, 64), color=(30, 144, 255))
            # Dibujar un triángulo de "play" blanco
            from PIL import ImageDraw
            draw = ImageDraw.Draw(icon)
            draw.polygon([(20, 15), (20, 49), (50, 32)], fill='white')
            self.window_icon = ImageTk.PhotoImage(icon)
            self.window.iconphoto(True, self.window_icon)
            logging.info("Usando icono por defecto")
        except Exception as e:
            logging.error(f"No se pudo crear el icono por defecto: {e}")

    def handle_resize(self, ev):
        logging.info(f"resize: {self.window.geometry()}")
        logging.info(f"canvas: {self.canvas.winfo_height()}, {self.canvas.winfo_width()}")
        logging.info(f"frame: {self.frame.winfo_height()}, {self.frame.winfo_width()}")

    def slider_changed(self, value):
        logging.info(f'time: {str(self.v_time.get())}, value: {value}')
        logging.info(f"valor scale: {self.slider.get()}")
        valor = self.slider.get()
        self.vid.set_poss(valor)

    def snapshot(self):
        # Get a frame from the video source
        ret, frame = self.vid.get_frame()

        if ret:
            #TODO: Guardamos el snapshot en Home si no es un archivo de video.
            timestamp = time.strftime("%d-%m-%Y-%H-%M-%S")
            if self.video_source != 0 :
                # Extraer directorio y nombre base del video
                video_dir = os.path.dirname(self.video_source)  # Carpeta del video
                video_name = os.path.splitext(os.path.basename(self.video_source))[0]  # Nombre sin extensión
                # Construir nombre del archivo: video_original_snapshot_YYYY-MM-DD_HH-MM-SS.jpg
                snapshot_name = f"{video_name}_snapshot_{timestamp}.jpg"           
                # Ruta completa
                snapshot_path = os.path.join(video_dir, snapshot_name)
            else:
                # Si es la webcam, guardamos en el directorio actual
                # timestamp = time.strftime("%d-%m-%Y-%H-%M-%S")
                snapshot_name = f"webcam_snapshot_{timestamp}.jpg"
                snapshot_dir  = cargar_config()  # Cargar la carpeta de snapshots desde el archivo de configuración
                snapshot_path = os.path.join(snapshot_dir, snapshot_name)
                snapshot_path = fd.asksaveasfilename(defaultextension=".jpg", 
                                                    initialfile=snapshot_name, 
                                                    filetypes=[("JPEG files", "*.jpg"),
                                                             ("PNG files", "*.png"), 
                                                             ("All files", "*.*")],
                                                    title="Guardar Snapshot",
                                                    initialdir = snapshot_dir
                                                    )
                guardar_config(os.path.dirname(snapshot_path))
            
            cv2.imwrite(snapshot_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

        logging.info(f"Snapshot guardado: {snapshot_path}")

    def stopshow(self):
        if self.btn_stop['text'] == 'II':
            self.btn_stop['text'] = '>'
            self.stop=True
        elif self.btn_stop['text'] == '>':
            self.btn_stop['text'] = 'II'
            self.stop=False
            self.window.after(self.delay, self.update)

    def gifshow(self):
        if  self.is_generating_gif:
            return # Evita clicks multiples
        
        self.is_generating_gif = True
        self.status_var.set("Generando GIF...")
        # Pausamos la reproduccion para liberar cv2.VideoCapture
        self.btn_stop['text'] = '>'
        self.stop=True
        self.btn_gif.config(state=tk.DISABLED)

        # Creamos y arrancamos el hilo en segundo plano.
        self.gif_thread = threading.Thread(target=self._generate_gif_worker, daemon=True)
        self.gif_thread.start()
        '''
        self.status_var.set("Generando GIF...")
        self.gif_thread = threading.Thread(target=self._generate_gif)
        self.gif_thread.start()
        '''

    def _generate_gif_worker(self):
        """Se ejecuta en el hilo secundario."""
        try:
            self.vid.save_gif_file(namefile=self.video_source)
            # Programamos la actualización en el hilo principal
            self.window.after(0, lambda: self._on_gif_finished(success=True))
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error creando GIF: {error_msg}")
            self.window.after(0, lambda: self._on_gif_finished(success=False, error=error_msg))

    def _on_gif_finished(self, success, error=None):
        """Se ejecuta en el hilo principal (GUI)."""
        self.is_generating_gif = False
        self.btn_gif.config(state=tk.NORMAL)
        
        if success:
            self.status_var.set("GIF creado")
            # showinfo("Éxito", "El archivo GIF se ha guardado correctamente.")
        else:
            self.status_var.set("Error al crear GIF")
            showerror("Error", f"No se pudo crear el GIF:\n{error}")
            
        # Reanudamos la reproducción automáticamente
        # Cambiamos el estado de pausa/reproducción
        self.btn_stop['text'] = 'II'
        self.stop=False
        self.window.after(self.delay, self.update)


    def _generate_gif(self):
        self.vid.save_gif_file(namefile=self.video_source)

    def openshow(self):
        filetypes = (
            ('text files', '*.mp4 *.avi *.mkv'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
                        title = 'Open a file',
                        initialdir = cargar_config(),
                        filetypes = filetypes
                        )
        if filename:
            logging.info(f"open file: {filename}")
            # liberamos los recursos del video actual
            self.vid.release()

            guardar_config(os.path.dirname(filename))

            self.video_source = filename
            self.vid = MyVideoCapture(self.video_source)

            # self.vid.set_only_video()
            self.canvas.configure(width=self.vid.width, height=self.vid.height)
            self.all_time.set(self.vid.seconds)
            self.slider.configure(to=self.all_time.get())
            # Actualizar el dalay basando en los nuevos fps del video abierto.
            self.delay = max(1, int(1000 / self.vid.fps))
            logging.info(f"new fps: {self.vid.fps}, delay: {self.delay}")
            

    def update(self):
        """Método de actualizacion con sincronizacion precisa de fps del video."""
        start_time = time.time()  # tiempo de inicio de la actualización

        try:
            ret, frame = self.vid.get_frame()
            
            self.v_time.set(round((self.vid.poss / 1000), 3)) 
            # Formato de tiempo mejorado (MM:SS)
            current_sec = int(self.v_time.get())
            minutes = current_sec // 60
            seconds = current_sec % 60
            self.lb_time['text'] = f"{minutes:02d}:{seconds:02d}"

        except Exception as e:
            logging.debug(f"App update error: {e}")
            # salimos del loop ...
            return

        if ret:
            self.photo = ImageTk.PhotoImage(image = Image.fromarray(frame))
            self.canvas.create_image(0, 0, image = self.photo, anchor = tk.NW)

        if self.stop:
            # salimos del loop
            return
        # Calculamos cuánto tiempo tomó procesar este frame
        processing_time = time.time() - start_time
        processing_time_ms = processing_time * 1000
        
        # Ajustamos el delay restando el tiempo de procesamiento
        adjusted_delay = max(1, self.delay - processing_time_ms)
        
        # Programamos el siguiente frame
        self.window.after(int(adjusted_delay), self.update)


if __name__ == '__main__':
    # Create a window and pass it to the Application object
    App(tk.Tk(), "Tkinter and OpenCV", 0)  # 0 para usar la webcam por defecto
    logging.info("End of program")