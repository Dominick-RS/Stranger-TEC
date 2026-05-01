"""
========================================================
 BRANCH: feature/logica-morse
 Archivo: logica_morse.py
 Descripción: Funciones de conversión Morse, cálculo de
              puntaje, bonus de velocidad y selección de frases.
 Depende de: config_global.py (MORSE, DECODE, FRASES)
========================================================
"""

from config_global import MORSE, DECODE, FRASES
import random


def texto_a_morse(texto):
    """
    Convierte un texto normal en su representación morse.
    Solo incluye letras/números que estén en la tabla MORSE.
    Ejemplo: "SOS" → "... --- ..."
    """
    return ' '.join(MORSE[l] for l in texto.upper() if l in MORSE)


def morse_a_texto(morse):
    """
    Convierte código morse a texto.
    Cada código separado por espacio es una letra.
    '/' representa un espacio entre palabras.
    Si no reconoce un código, pone '?' en su lugar.
    """
    texto = ''
    for codigo in morse.strip().split(' '):
        if codigo == '/':
            texto += ' '
        elif codigo in DECODE:
            texto += DECODE[codigo]
        elif codigo:
            texto += '?'
    return texto


def calcular_puntaje(original, respuesta):
    """
    Compara la respuesta del jugador con la frase original.
    Cuenta cuántas letras están en la posición correcta.
    Devuelve un número entre 0 y 100.
    Hay un pequeño bonus si la longitud de la respuesta es exacta.
    """
    original  = original.upper().strip()
    respuesta = respuesta.upper().strip()
    if not original:
        return 0
    # Compara letra por letra hasta donde llegue la respuesta más corta
    correctos = sum(1 for i in range(min(len(original), len(respuesta)))
                    if original[i] == respuesta[i])
    pts = round((correctos / len(original)) * 100)
    if len(original) == len(respuesta):
        pts = min(100, pts + 10)  # Bonus por longitud exacta
    return pts


def velocidad_bonus(segundos, largo):
    """
    Calcula un bonus de puntos según qué tan rápido transmitió el jugador.
    Se compara contra un tiempo base proporcional al largo de la frase.
    Devuelve los puntos de bonus y una etiqueta de velocidad.
    """
    if segundos <= largo * 2.4:   return 30, "RÁPIDO"
    elif segundos <= largo * 3.4: return 15, "MEDIO"
    else:                          return 0,  "LENTO"


def frase_aleatoria():
    """
    Elige y devuelve una frase al azar de la lista FRASES.
    """
    return random.choice(FRASES)
