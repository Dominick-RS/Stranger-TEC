"""
========================================================
 BRANCH: Configuracion
 Archivo: config_global.py
 Descripción: Imports, constantes visuales, estado del
              juego y tabla Morse. Base de todo el sistema.
========================================================
"""

import tkinter as tk
from PIL import Image, ImageTk   # Pillow: necesario para cargar y animar el GIF
import random, os, time

# Importar pyserial para comunicarnos con el Arduino.
# Si no está instalado, el juego igual funciona en modo simulación.
try:
    import serial
    import serial.tools.list_ports
    HAY_SERIAL = True
except ImportError:
    HAY_SERIAL = False

# os.path.abspath(__file__) devuelve la ruta completa de este archivo.
# dirname() se queda solo con la carpeta. Así siempre encontramos el GIF
# sin importar desde qué carpeta se ejecute el programa.
CARPETA = os.path.dirname(os.path.abspath(__file__))

# ── Colores y fuente (cambiarlos aquí los cambia en toda la app) ──────────────
ROJO     = "#ff2222"
ROJO_M   = "#aa0000"
ROJO_O   = "#440000"
NEGRO    = "#03030f"
FONDO    = "#050510"
VERDE    = "#00ff88"
AMARILLO = "#ffcc00"
# "Fixedsys" es una tipografía clásica de DOS/Windows que da un look muy retro.
# Si no está disponible en tu sistema, cambia a "Courier" como respaldo.
FUENTE   = "Fixedsys"

# ── Estado del juego ──────────────────────────────────────────────────────────
# Guardamos todo en un solo diccionario para tener la información
# del juego accesible desde cualquier función fácilmente.
juego = {
    "frase": "",       # La frase elegida para la ronda actual
    "modo": "A",       # A = Escucha y Transmisión / B = Transmisión Simple
    "salida": "LED",   # Cómo muestra el morse la maqueta: LED o BUZZER
    "turno": 1,        # 1 = primer turno, 2 = segundo turno
    "jugador_pc": "A", # Quién usa la computadora en este turno
    "jugador_maq": "B",# Quién usa la maqueta en este turno
    "pts_a": 0,        # Puntaje acumulado del jugador A
    "pts_b": 0,        # Puntaje acumulado del jugador B
    "ronda": 1,        # Número de ronda actual
    "t_inicio": 0,     # Momento en que empezó el turno (para medir velocidad)
}

# ── Tabla Morse ───────────────────────────────────────────────────────────────
# Cada letra/número tiene su código morse
MORSE = {
    'A':'.-',   'B':'-...', 'C':'-.-.', 'D':'-..',  'E':'.',
    'F':'..-.', 'G':'--.',  'H':'....', 'I':'..',   'J':'.---',
    'K':'-.-',  'L':'.-..', 'M':'--',   'N':'-.',   'O':'---',
    'P':'.--.', 'Q':'--.-', 'R':'.-.',  'S':'...',  'T':'-',
    'U':'..-',  'V':'...-', 'W':'.--',  'X':'-..-', 'Y':'-.--',
    'Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-',
    '5':'.....','6':'-....','7':'--...','8':'---..','9':'----.',
    '+':'.-.-.','-':'-....-',' ':'/'
}

# Tabla invertida: de morse a letra.
# Creamos el diccionario al revés para poder decodificar fácilmente.
# Excluimos el espacio ' ' porque su código '/' se maneja por separado.
DECODE = {v: k for k, v in MORSE.items() if k != ' '}

# Frases disponibles para el juego
FRASES = ["PERRO","CASA","CAMINO","CONDE","MARIO","GATO","ANGEL","HIJO","GUERRA","JUAN"]

# Variable global que guarda la conexión con el Arduino
conexion_serial = None
modo_simulacion = not HAY_SERIAL  # Si no hay pyserial, arranca en simulación
