"""
========================================================
 BRANCH: Funciones_Dibujo
 Archivo: ui_base.py
 Descripción: Funciones de dibujo reutilizables en todas
              las ventanas: fondo degradado, texto con glow
              y botones estilo retro.
 Depende de: config_global.py (ROJO, ROJO_O, NEGRO, FUENTE)
========================================================
"""

import tkinter as tk
from config_global import ROJO, ROJO_M, ROJO_O, NEGRO, FUENTE


def dibujar_fondo(canvas, w=800, h=650):
    """
    Dibuja el fondo oscuro degradado y líneas verticales en los bordes.
    El degradado se consigue dibujando franjas horizontales de color
    que van de casi negro a gris muy oscuro de arriba a abajo.
    """
    for y in range(0, h, 4):
        v = int(y / h * 18)  # v va de 0 a 18 → color de casi negro a gris oscuro
        canvas.create_rectangle(0, y, w, y+4,
                                 fill=f"#{v:02x}{v:02x}{v+8:02x}", outline="")
    # Líneas verticales decorativas en los bordes laterales
    for x in [15, 18, w-18, w-15]:
        canvas.create_line(x, 0, x, h, fill=ROJO_O)


def texto_glow(canvas, x, y, texto, tamaño):
    """
    Escribe un texto con efecto de brillo rojo.
    El truco es escribir el mismo texto dos veces:
    - primero en rojo oscuro, un poco desplazado (la "sombra")
    - encima en rojo brillante en la posición real
    """
    canvas.create_text(x+2, y+2, text=texto,
                       font=(FUENTE, tamaño, "bold"), fill=ROJO_O)  # Sombra
    canvas.create_text(x,   y,   text=texto,
                       font=(FUENTE, tamaño, "bold"), fill=ROJO)    # Texto brillante


def boton(canvas, x, y, texto, accion):
    """
    Crea un botón con la estética retro del juego y lo coloca en el canvas.
    'accion' es la función que se ejecuta al hacer clic.
    Usa create_window para incrustar el widget Button dentro del Canvas.
    """
    b = tk.Button(canvas, text=texto, font=(FUENTE, 11, "bold"),
                  fg=ROJO, bg=NEGRO, activeforeground="white",
                  activebackground=ROJO_O, relief="flat",
                  cursor="hand2", command=accion)
    canvas.create_window(x, y, window=b)
    return b
