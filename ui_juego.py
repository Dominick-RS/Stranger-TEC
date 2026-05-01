"""
========================================================
 BRANCH: Ventana_juego
 Archivo: ui_juego.py
 Descripción: Ventana 3 — Pantalla principal de juego.
              Maneja dos turnos, entrada de morse por PC,
              recepción desde Arduino, timer y puntajes.
 Depende de: config_global.py, ui_base.py, logica_morse.py,
             comunicacion_serial.py
========================================================
"""

import tkinter as tk
import time
from config_global import (FONDO, NEGRO, ROJO, ROJO_M, ROJO_O,
                            VERDE, AMARILLO, FUENTE, juego)
from ui_base import dibujar_fondo, texto_glow, boton
from logica_morse import (texto_a_morse, morse_a_texto,
                          calcular_puntaje, velocidad_bonus, frase_aleatoria)
from comunicacion_serial import (serial_enviar, serial_leer, serial_desconectar)



def abrir_juego():
    """
    Abre la ventana principal del juego.

    Flujo:
      Turno 1 → Jugador A en PC / Jugador B en maqueta
      Turno 2 → roles invertidos (B en PC / A en maqueta)
    Al confirmar el turno 2, va a la pantalla de resultados.
    """
    # ── Preparar la ronda ─────────────────────────────────────────────────────
    juego["frase"]       = frase_aleatoria()
    juego["turno"]       = 1
    juego["jugador_pc"]  = "A"
    juego["jugador_maq"] = "B"
    juego["t_inicio"]    = time.time()

    serial_enviar(f"MODO:{juego['salida']}")   # LED o BUZZER
    serial_enviar(f"FRASE:{juego['frase']}")   # Frase que reproducirá el Arduino

    # ── Ventana y canvas ──────────────────────────────────────────────────────
    ventana = tk.Tk()
    ventana.title("Stranger Tec — Juego")
    ventana.geometry("800x650")
    ventana.resizable(False, False)

    canvas = tk.Canvas(ventana, width=800, height=650,
                       bg=FONDO, bd=0, highlightthickness=0)
    canvas.pack()
    dibujar_fondo(canvas)
    texto_glow(canvas, 400, 38, "STRANGER TEC", 22)

    # ── Widgets de información de turno ───────────────────────────────────────
    id_turno = canvas.create_text(400, 72, text="",
                                   font=(FUENTE, 11, "bold"), fill=ROJO_M)

    # Panel de frase y su morse
    canvas.create_rectangle(60, 88, 740, 160, fill=NEGRO, outline=ROJO_O)
    id_frase       = canvas.create_text(400, 108, text="",
                                         font=(FUENTE, 15, "bold"), fill=ROJO)
    id_morse_frase = canvas.create_text(400, 140, text="",
                                         font=(FUENTE, 9), fill="#664444", width=660)

    # ── Panel: jugador PC ─────────────────────────────────────────────────────
    canvas.create_rectangle(60, 172, 740, 310, fill=NEGRO, outline=ROJO_O)
    id_label_pc = canvas.create_text(80, 190, text="", anchor="w",
                                      font=(FUENTE, 9, "bold"), fill=ROJO_M)
    # Campo de texto donde el jugador escribe el morse (. y -)
    entrada_pc  = tk.Text(canvas, width=58, height=2, font=(FUENTE, 13),
                          fg=ROJO, bg="#0a0a1a", insertbackground=ROJO,
                          relief="flat", highlightbackground=ROJO_O,
                          highlightthickness=1)
    canvas.create_window(400, 240, window=entrada_pc)
    # Decodificación en tiempo real de lo que escribe el jugador PC
    id_decode_pc = canvas.create_text(400, 292, text="",
                                       font=(FUENTE, 12, "bold"), fill=VERDE)

    # ── Panel: jugador maqueta ────────────────────────────────────────────────
    canvas.create_rectangle(60, 322, 740, 430, fill=NEGRO, outline=ROJO_O)
    id_label_maq  = canvas.create_text(80, 340, text="", anchor="w",
                                        font=(FUENTE, 9, "bold"), fill=ROJO_M)
    id_morse_maq  = canvas.create_text(400, 370, text="[ esperando maqueta... ]",
                                        font=(FUENTE, 12), fill="#664444")
    id_decode_maq = canvas.create_text(400, 410, text="",
                                        font=(FUENTE, 12, "bold"), fill=VERDE)

    # Timer de velocidad (solo visible en Modo B)
    id_timer = canvas.create_text(680, 450, text="",
                                   font=(FUENTE, 11, "bold"), fill=AMARILLO)

    # ── Barra de puntajes ─────────────────────────────────────────────────────
    canvas.create_rectangle(30, 470, 770, 505, fill="#07070f", outline=ROJO_O)
    id_pts_a = canvas.create_text(120, 487, text="",
                                   font=(FUENTE, 11, "bold"), fill=ROJO_M)
    id_pts_b = canvas.create_text(680, 487, text="",
                                   font=(FUENTE, 11, "bold"), fill=ROJO_M)
    canvas.create_text(400, 487, text=f"RONDA {juego['ronda']}",
                       font=(FUENTE, 10, "bold"), fill="#330000")
    id_aviso = canvas.create_text(400, 530, text="",
                                   font=(FUENTE, 9), fill=AMARILLO)

    # IDs de after() para cancelarlos antes de destruir la ventana
    timer_on         = [False]
    id_after_timer   = [None]
    id_after_arduino = [None]

    # Acumuladores de lo que envía la maqueta letra por letra
    morse_maqueta = [""]
    texto_maqueta = [""]

    # ── Funciones internas ────────────────────────────────────────────────────

    def actualizar_pantalla():
        """
        Refresca todos los textos según el turno actual.
        Se llama al inicio y después de cada cambio de turno.
        """
        jpc  = juego["jugador_pc"]
        jmaq = juego["jugador_maq"]
        canvas.itemconfig(id_turno,
                          text=f"TURNO {juego['turno']}/2  —  "
                               f"JUG {jpc}: PC  |  JUG {jmaq}: MAQUETA")
        canvas.itemconfig(id_label_pc,
                          text=f"JUGADOR {jpc} — escribe el morse (punto=.  raya=-):")
        canvas.itemconfig(id_label_maq,
                          text=f"JUGADOR {jmaq} — usando los botones de la maqueta:")
        canvas.itemconfig(id_pts_a, text=f"JUG A: {juego['pts_a']} pts")
        canvas.itemconfig(id_pts_b, text=f"JUG B: {juego['pts_b']} pts")
        if juego["modo"] == "A":
            # Modo A: ambos jugadores ven la frase y la ingresan en morse
            canvas.itemconfig(id_frase,       text=juego["frase"])
            canvas.itemconfig(id_morse_frase, text=texto_a_morse(juego["frase"]))
            canvas.itemconfig(id_aviso,
                              text="Escucha/observa el morse emitido por la maqueta y responde")
        else:
            # Modo B: la frase está oculta, la transmite el jugador de maqueta
            canvas.itemconfig(id_frase,       text="[ CLASIFICADO ]")
            canvas.itemconfig(id_morse_frase, text="")
            canvas.itemconfig(id_aviso,
                              text=f"La maqueta emite la palabra; JUG {jmaq}: responde con botones")

    def tick_timer():
        """
        Actualiza el cronómetro cada 100ms.
        time.time() - juego['t_inicio'] da los segundos transcurridos.
        """
        if timer_on[0]:
            seg = round(time.time() - juego["t_inicio"], 1)
            canvas.itemconfig(id_timer, text=f"⏱ {seg}s")
            id_after_timer[0] = ventana.after(100, tick_timer)

    def revisar_arduino():
        """
        Revisa cada 200ms si el Arduino mandó datos.
        Actualiza los paneles de morse y texto de la maqueta.
        """
        recibido = serial_leer()
        if recibido:
            tipo, valor = recibido

            if tipo == "MORSE":
                if morse_maqueta[0]:
                    morse_maqueta[0] += " " + valor
                else:
                    morse_maqueta[0] = valor
                canvas.itemconfig(id_morse_maq, text=morse_maqueta[0])

            elif tipo == "LETRA":
                texto_maqueta[0] += valor
                canvas.itemconfig(id_decode_maq, text=texto_maqueta[0])
                timer_on[0] = False
                canvas.itemconfig(id_timer, text="")

            elif tipo == "BORRAR":
                morse_maqueta[0] = ""
                texto_maqueta[0] = ""
                canvas.itemconfig(id_morse_maq, text="[ esperando maqueta... ]")
                canvas.itemconfig(id_decode_maq, text="")

        id_after_arduino[0] = ventana.after(200, revisar_arduino)

    def al_escribir(e=None):
        """
        Se ejecuta cada vez que el jugador PC suelta una tecla.
        Decodifica el morse escrito y lo muestra en verde en tiempo real.
        """
        m = entrada_pc.get("1.0", "end").strip()
        canvas.itemconfig(id_decode_pc, text=morse_a_texto(m) if m else "")

    entrada_pc.bind("<KeyRelease>", al_escribir)

    def confirmar():
        """
        Al presionar "Confirmar Turno":
        - Recoge las respuestas de PC y maqueta
        - Calcula puntajes (con bonus de velocidad en Modo B)
        - Si es turno 1: intercambia jugadores y reinicia el turno
        - Si es turno 2: va a la pantalla de resultados
        """
        morse_pc  = entrada_pc.get("1.0", "end").strip()
        texto_pc  = morse_a_texto(morse_pc) if morse_pc else ""
        texto_maq = texto_maqueta[0]

        pts_pc  = calcular_puntaje(juego["frase"], texto_pc)
        pts_maq = calcular_puntaje(juego["frase"], texto_maq)

        if juego["modo"] == "B":
            seg      = round(time.time() - juego["t_inicio"], 1)
            bonus, _ = velocidad_bonus(seg, len(juego["frase"]))
            pts_maq  = min(100, pts_maq + bonus)

        if juego["jugador_pc"] == "A":
            juego["pts_a"] += pts_pc
            juego["pts_b"] += pts_maq
        else:
            juego["pts_b"] += pts_pc
            juego["pts_a"] += pts_maq

        if juego["turno"] == 1:
            # Intercambio de roles para el segundo turno
            juego["turno"]       = 2
            juego["jugador_pc"]  = "B"
            juego["jugador_maq"] = "A"
            juego["t_inicio"]    = time.time()
            entrada_pc.delete("1.0", "end")
            canvas.itemconfig(id_morse_maq,  text="[ esperando maqueta... ]")
            canvas.itemconfig(id_decode_maq, text="")
            canvas.itemconfig(id_decode_pc,  text="")
            morse_maqueta[0] = ""
            texto_maqueta[0] = ""
            timer_on[0] = juego["modo"] == "B"
            if timer_on[0]:
                tick_timer()
            serial_enviar("LISTO")
            actualizar_pantalla()
        else:
            # Fin de la ronda
            if id_after_timer[0]:   ventana.after_cancel(id_after_timer[0])
            if id_after_arduino[0]: ventana.after_cancel(id_after_arduino[0])
            serial_enviar("FIN")
            ventana.destroy()
            abrir_resultados(pts_pc, pts_maq)   # <-- función de ui_resultados.py

    def volver_menu():
        """Cancela todo y regresa al menú principal."""
        if id_after_timer[0]:   ventana.after_cancel(id_after_timer[0])
        if id_after_arduino[0]: ventana.after_cancel(id_after_arduino[0])
        serial_desconectar()
        ventana.destroy()
        abrir_menu()    # <-- función de ui_menu.py

    # ── Botones ───────────────────────────────────────────────────────────────
    boton(canvas, 280, 585, "[ CONFIRMAR TURNO ]", confirmar)
    boton(canvas, 560, 585, "[ MENÚ ]", volver_menu)

    # ── Arranque ──────────────────────────────────────────────────────────────
    actualizar_pantalla()
    revisar_arduino()
    if juego["modo"] == "B":
        timer_on[0] = True
        tick_timer()
    serial_enviar("LISTO")
    ventana.mainloop()
