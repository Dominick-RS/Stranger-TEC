"""
========================================================
 BRANCH: Ventana_Menu
 Archivo: ui_menu.py
 Descripción: Ventana 1 — Menú principal animado con GIF.
 Depende de: config_global.py, ui_base.py
========================================================
"""

import tkinter as tk
from PIL import Image, ImageTk
import os, random
from config_global import CARPETA, ROJO, ROJO_O, FUENTE
# from ui_config import abrir_config   # <-- descomentar al integrar todo


def abrir_menu():
    """
    Abre la ventana del menú principal.
    Muestra un GIF animado de fondo con texto parpadeante.
    Cualquier tecla o clic lleva a la pantalla de configuración.
    """
    ventana = tk.Tk()
    ventana.title("Stranger Tec")
    ventana.geometry("800x650")
    ventana.resizable(False, False)

    canvas = tk.Canvas(ventana, width=800, height=650,
                       bg="black", bd=0, highlightthickness=0)
    canvas.pack()

    # ── Cargar el GIF frame por frame con Pillow ──────────────────────────────
    # Tkinter por sí solo no puede animar GIFs, por eso necesitamos Pillow.
    gif = Image.open(os.path.join(CARPETA, "strangertec_menu.gif"))
    frames, tiempos = [], []
    try:
        while True:
            f = gif.copy().resize((800, 650), Image.LANCZOS)
            frames.append(ImageTk.PhotoImage(f))           # Convierte a formato tkinter
            tiempos.append(gif.info.get("duration", 80))  # Duración real del frame en ms
            gif.seek(gif.tell() + 1)                       # Pasar al siguiente frame
    except EOFError:
        pass  # EOFError significa que ya no hay más frames, es normal

    img_id = canvas.create_image(0, 0, anchor="nw", image=frames[0])

    # Guardamos los IDs de los after() para poder cancelarlos antes de cerrar.
    # Si no los cancelamos, tkinter intenta ejecutarlos sobre una ventana
    # que ya no existe y lanza un error.
    id_anim     = [None]
    id_parpadeo = [None]

    # ── Animación del GIF ─────────────────────────────────────────────────────
    def animar(i=0):
        """Cambia al frame i del GIF y programa el siguiente cambio."""
        canvas.itemconfig(img_id, image=frames[i])
        id_anim[0] = ventana.after(tiempos[i], animar, (i+1) % len(frames))

    # ── Texto "pulse cualquier botón" ─────────────────────────────────────────
    canvas.create_text(400, 570,
                       text="PULSE CUALQUIER BOTÓN PARA INICIAR ",
                       font=(FUENTE, 13, "bold"), fill=ROJO, tags="txt")

    vis = [True]  # Controla si el texto está visible o invisible

    def parpadear():
        """
        Alterna el color del texto entre rojo brillante y casi negro
        para simular el parpadeo de pantalla retro.
        El delay es aleatorio para que no sea mecánico.
        """
        canvas.itemconfig("txt",    fill=ROJO      if vis[0] else "#1a0000")
        canvas.itemconfig("sombra", fill="#5a0000" if vis[0] else "#1a0000")
        vis[0] = not vis[0]
        id_parpadeo[0] = ventana.after(random.choice([400,500,600,800]), parpadear)

    animar()
    parpadear()

    # ── Navegación a configuración ────────────────────────────────────────────
    def ir_a_config(e=None):
        """
        Cuando el usuario pulsa cualquier tecla o hace clic, va a configuración.
        Primero desactiva los eventos para que no se ejecute dos veces.
        Luego cancela las animaciones pendientes antes de destruir la ventana.
        """
        ventana.unbind("<Key>")
        ventana.unbind("<Button-1>")
        if id_anim[0]:     ventana.after_cancel(id_anim[0])
        if id_parpadeo[0]: ventana.after_cancel(id_parpadeo[0])
        ventana.destroy()
        abrir_config()     # <-- función de ui_config.py

    # bind escucha eventos: cualquier tecla o clic del ratón llama a ir_a_config
    ventana.bind("<Key>",      ir_a_config)
    ventana.bind("<Button-1>", ir_a_config)
    ventana.mainloop()
