"""
========================================================
 BRANCH:Ventana_resultados
 Archivo: ui_resultados.py
 Descripción: Ventana 4 — Pantalla de resultados al final
              de cada ronda. Muestra puntajes, ganador y
              botones para jugar de nuevo o volver al menú.
 Depende de: config_global.py, ui_base.py,
             comunicacion_serial.py
========================================================
"""

import tkinter as tk
from config_global import (FONDO, NEGRO, ROJO, ROJO_M, ROJO_O,
                            AMARILLO, FUENTE, juego)
from ui_base import dibujar_fondo, texto_glow, boton
from comunicacion_serial import serial_desconectar



def abrir_resultados(pts_ronda_pc, pts_ronda_maq):
    """
    Abre la pantalla de resultados al terminar una ronda.

    Parámetros:
        pts_ronda_pc  (int): Puntos obtenidos por el jugador que usó la PC
                             en el último turno (turno 2).
        pts_ronda_maq (int): Puntos del jugador que usó la maqueta en el
                             último turno (turno 2).

    Muestra:
      - Frase de la ronda
      - Panel individual por jugador con puntos de ronda y total acumulado
      - Mensaje de quién va ganando (o empate)
      - Botones: siguiente ronda / menú principal
    """
    ventana = tk.Tk()
    ventana.title("Resultados")
    ventana.geometry("800x650")
    ventana.resizable(False, False)

    canvas = tk.Canvas(ventana, width=800, height=650,
                       bg=FONDO, bd=0, highlightthickness=0)
    canvas.pack()
    dibujar_fondo(canvas)
    texto_glow(canvas, 400, 40, "RESULTADOS", 26)

    canvas.create_text(400, 88, text=f"Frase: \"{juego['frase']}\"",
                       font=(FUENTE, 12, "bold"), fill=ROJO_M)

    # ── Determinar puntajes por jugador ───────────────────────────────────────
    # Según quién estaba en la PC durante el último turno (turno 2),
    # asignamos los puntajes correctamente a jugador A y B.
    pts_a_ronda = pts_ronda_pc  if juego["jugador_pc"] == "A" else pts_ronda_maq
    pts_b_ronda = pts_ronda_maq if juego["jugador_pc"] == "A" else pts_ronda_pc

    # ── Panel Jugador A ───────────────────────────────────────────────────────
    canvas.create_rectangle(60, 110, 370, 320, fill=NEGRO, outline=ROJO_O, width=2)
    texto_glow(canvas, 215, 138, "JUGADOR  A", 15)
    canvas.create_text(215, 190,
                       text=f"Puntos esta ronda: {pts_a_ronda}",
                       font=(FUENTE, 11, "bold"), fill=ROJO)
    canvas.create_text(215, 260,
                       text=f"TOTAL: {juego['pts_a']} pts",
                       font=(FUENTE, 13, "bold"), fill=AMARILLO)

    # ── Panel Jugador B ───────────────────────────────────────────────────────
    canvas.create_rectangle(430, 110, 740, 320, fill=NEGRO, outline=ROJO_O, width=2)
    texto_glow(canvas, 585, 138, "JUGADOR  B", 15)
    canvas.create_text(585, 190,
                       text=f"Puntos esta ronda: {pts_b_ronda}",
                       font=(FUENTE, 11, "bold"), fill=ROJO)
    canvas.create_text(585, 260,
                       text=f"TOTAL: {juego['pts_b']} pts",
                       font=(FUENTE, 13, "bold"), fill=AMARILLO)

    # ── Banner de quién va ganando ────────────────────────────────────────────
    if juego["pts_a"] > juego["pts_b"]:
        msg, col = "★  JUGADOR A VA GANANDO  ★", ROJO
    elif juego["pts_b"] > juego["pts_a"]:
        msg, col = "★  JUGADOR B VA GANANDO  ★", ROJO
    else:
        msg, col = "— EMPATE —", AMARILLO

    canvas.create_rectangle(60, 340, 740, 400, fill="#0d000d",
                             outline="#660044", width=2)
    canvas.create_text(400, 370, text=msg,
                       font=(FUENTE, 17, "bold"), fill=col)

    # ── Botones de navegación ─────────────────────────────────────────────────
    boton(canvas, 240, 470, "[ SIGUIENTE RONDA ]",
          lambda: [ventana.destroy(), abrir_juego()])         # <-- ui_juego.py
    boton(canvas, 560, 470, "[ MENÚ PRINCIPAL ]",
          lambda: [ventana.destroy(), serial_desconectar(), abrir_menu()])  # <-- ui_menu.py

    ventana.mainloop()
