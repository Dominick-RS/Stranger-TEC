"""
========================================================
 BRANCH: Ventana_configuración
 Archivo: ui_config.py
 Descripción: Ventana 2 — Configuración del juego.
              Permite elegir modo, salida, puerto COM. Valida y guarda
              todo antes de iniciar la partida.
 Depende de: config_global.py, ui_base.py,
             comunicacion_serial.py
========================================================
"""

import tkinter as tk
from config_global import (FONDO, NEGRO, ROJO, ROJO_M, ROJO_O,
                            AMARILLO, FUENTE, juego, FRASES)
from ui_base import dibujar_fondo, texto_glow, boton
from comunicacion_serial import serial_listar_puertos, serial_conectar
# from ui_juego import abrir_juego   # <-- descomentar al integrar todo


def abrir_config():
    """
    Abre la pantalla de configuración.

    Permite al usuario:
      - Elegir Modo A (Escucha y Transmisión) o Modo B (Transmisión Simple)
      - Elegir la salida de la maqueta: LED o BUZZER
      - Seleccionar el puerto COM donde está conectado el Arduino
      - Editar la lista de frases (mínimo 3, máximo 16 letras cada una)
    Al presionar INICIAR, valida, guarda y lanza la ventana de juego.
    """
    ventana = tk.Tk()
    ventana.title("Configuración")
    ventana.geometry("800x650")
    ventana.resizable(False, False)

    canvas = tk.Canvas(ventana, width=800, height=650,
                       bg=FONDO, bd=0, highlightthickness=0)
    canvas.pack()
    dibujar_fondo(canvas)
    texto_glow(canvas, 400, 40, "CONFIGURACIÓN", 22)

    # ── Selector de modo de juego ─────────────────────────────────────────────
    # Radiobutton = botón de opción; solo uno puede estar activo a la vez.
    canvas.create_text(400, 100, text="MODO DE JUEGO",
                       font=(FUENTE, 12, "bold"), fill=ROJO_M)
    var_modo = tk.StringVar(value=juego["modo"])
    for txt, val, px in [("MODO A — Escucha y Transmisión", "A", 60),
                          ("MODO B — Transmisión Simple",    "B", 440)]:
        tk.Radiobutton(canvas, text=txt, variable=var_modo, value=val,
                       font=(FUENTE, 10, "bold"), fg=ROJO, bg=FONDO,
                       selectcolor=NEGRO, relief="flat",
                       activeforeground="white", activebackground=ROJO_O
                       ).place(x=px, y=120)

    # ── Selector de salida en la maqueta ──────────────────────────────────────
    canvas.create_text(400, 185, text="SALIDA EN MAQUETA",
                       font=(FUENTE, 12, "bold"), fill=ROJO_M)
    var_salida = tk.StringVar(value=juego["salida"])
    for txt, val, px in [("💡 LEDs", "LED", 220), ("🔊 Buzzer", "BUZZER", 420)]:
        tk.Radiobutton(canvas, text=txt, variable=var_salida, value=val,
                       font=(FUENTE, 10, "bold"), fg=ROJO, bg=FONDO,
                       selectcolor=NEGRO, relief="flat",
                       activeforeground="white", activebackground=ROJO_O
                       ).place(x=px, y=205)

    # ── Menú desplegable: puerto serial del Arduino ───────────────────────────
    canvas.create_text(400, 265, text="PUERTO ARDUINO (cable USB)",
                       font=(FUENTE, 12, "bold"), fill=ROJO_M)
    puertos    = serial_listar_puertos()
    var_puerto = tk.StringVar(value=puertos[0])
    tk.OptionMenu(canvas, var_puerto, *puertos).place(x=290, y=283,
                                                       width=220, height=28)

    # ── Cuadro de texto: lista de frases ──────────────────────────────────────
    canvas.create_text(400, 345, text="FRASES (una por línea, máx. 16 letras)",
                       font=(FUENTE, 10, "bold"), fill=ROJO_M)
    txt_frases = tk.Text(canvas, width=30, height=10,
                         font=(FUENTE, 11), fg=ROJO, bg=NEGRO,
                         insertbackground=ROJO, relief="flat",
                         highlightbackground=ROJO_O, highlightthickness=1)
    txt_frases.insert("1.0", "\n".join(FRASES))
    canvas.create_window(400, 460, window=txt_frases)

    id_aviso = canvas.create_text(400, 555, text="",
                                   font=(FUENTE, 9), fill=AMARILLO)

    # ── Lógica del botón INICIAR ──────────────────────────────────────────────
    def iniciar():
        """
        Lee las frases del cuadro, valida y guarda toda la configuración.
        Filtra frases vacías y las que superen 16 caracteres.
        Necesita mínimo 3 frases válidas para continuar.
        """
        global FRASES
        lineas    = txt_frases.get("1.0", "end").strip().split("\n")
        frases_ok = [f.strip().upper() for f in lineas
                     if f.strip() and len(f.strip()) <= 16]
        if len(frases_ok) < 3:
            canvas.itemconfig(id_aviso,
                              text="⚠ Necesitas mínimo 3 frases (máx. 16 letras)")
            return
        # Guardamos todo en el diccionario global del juego
        FRASES             = frases_ok
        juego["modo"]      = var_modo.get()
        juego["salida"]    = var_salida.get()
        juego["pts_a"]     = 0  # Reiniciamos puntajes al empezar nueva partida
        juego["pts_b"]     = 0
        juego["ronda"]     = 1
        serial_conectar(var_puerto.get())
        ventana.destroy()
        abrir_juego()      # <-- función de ui_juego.py

    boton(canvas, 400, 610, "[ INICIAR JUEGO ]", iniciar)
    ventana.mainloop()
