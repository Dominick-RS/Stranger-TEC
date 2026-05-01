"""
========================================================
 BRANCH: feature/comunicacion-serial
 Archivo: comunicacion_serial.py
 Descripción: Todas las funciones de comunicación USB
              entre Python y el Arduino (pyserial).
 Depende de: config_global.py (HAY_SERIAL, conexion_serial,
                                modo_simulacion)
========================================================
"""

import time
from config_global import HAY_SERIAL

# Si pyserial está disponible, importamos las herramientas necesarias
if HAY_SERIAL:
    import serial
    import serial.tools.list_ports

# Variables globales de conexión
conexion_serial = None
modo_simulacion = not HAY_SERIAL


def serial_listar_puertos():
    """
    Devuelve la lista de puertos COM disponibles en la computadora.
    Si no hay pyserial instalado, devuelve una opción de simulación.
    """
    if not HAY_SERIAL:
        return ["Simulación (sin Arduino)"]
    puertos = serial.tools.list_ports.comports()
    return [p.device for p in puertos] or ["Ninguno detectado"]


def serial_conectar(puerto):
    """
    Intenta abrir la conexión con el Arduino en el puerto indicado.
    Si falla o no hay Arduino, activa el modo simulación automáticamente.
    Retorna True si la conexión (real o simulada) fue exitosa.
    """
    global conexion_serial, modo_simulacion
    if not HAY_SERIAL or "Simulación" in puerto or "Ninguno" in puerto:
        modo_simulacion = True
        return True
    try:
        conexion_serial = serial.Serial(puerto, 9600, timeout=1)
        modo_simulacion = False
        time.sleep(2)  # Esperamos 2 segundos porque el Arduino se reinicia al conectar
        return True
    except:
        modo_simulacion = True
        return False


def serial_enviar(mensaje):
    """
    Envía un texto al Arduino terminado en salto de línea (\\n).
    En simulación solo imprime en consola para ver qué se enviaría.

    Mensajes válidos:
        FRASE:<texto>       → frase que debe reproducir la maqueta
        MODO:<LED|BUZZER>   → tipo de salida de la maqueta
        LISTO               → Arduino limpia matriz y reproduce la frase
        FIN                 → Arduino apaga todo
    """
    if modo_simulacion:
        print(f"[SIM] → {mensaje}")
        return
    if conexion_serial:
        try:
            conexion_serial.write(f"{mensaje}\n".encode())
        except:
            pass


def serial_leer():
    """
    Revisa si el Arduino envió algo y lo retorna como tupla (tipo, valor).
    Mensajes que entiende:
        MORSE:.-    → código morse de la letra presionada
        LETRA:A     → letra ya decodificada por el Arduino
        BORRAR      → limpiar la entrada de la maqueta
    Retorna None si no hay datos.
    """
    if modo_simulacion or not conexion_serial:
        return None
    if conexion_serial.in_waiting > 0:
        try:
            linea = conexion_serial.readline().decode().strip()
            if linea.startswith("MORSE:"):
                return ("MORSE", linea[6:])
            elif linea.startswith("LETRA:"):
                return ("LETRA", linea[6:])
            elif linea == "BORRAR":
                return ("BORRAR", "")
        except:
            pass
    return None


def serial_desconectar():
    """
    Cierra la conexión con el Arduino de forma limpia.
    """
    global conexion_serial
    if conexion_serial:
        conexion_serial.close()
        conexion_serial = None
