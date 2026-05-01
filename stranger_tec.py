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
# Cada letra/número tiene su código morse según la convención del proyecto.
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

# Frases disponibles para el juego (se pueden cambiar en la pantalla de config)
FRASES = ["PERRO","CASA","CAMINO","CONDE","MARIO","GATO","ANGEL","HIJO","GUERRA","JUAN"]

# Variable global que guarda la conexión con el Arduino
conexion_serial = None
modo_simulacion = not HAY_SERIAL  # Si no hay pyserial, arranca en simulación



#  FUNCIONES MORSE


def texto_a_morse(texto):
    # Convierte un texto normal en su representación morse.
    # Solo incluye letras/números que estén en la tabla MORSE.
    # Ejemplo: "SOS" → "... --- ..."
    return ' '.join(MORSE[l] for l in texto.upper() if l in MORSE)

def morse_a_texto(morse):
    # Convierte código morse a texto.
    # Cada código separado por espacio es una letra.
    # '/' representa un espacio entre palabras.
    # Si no reconoce un código, pone '?' en su lugar.
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
    # Compara la respuesta del jugador con la frase original.
    # Cuenta cuántas letras están en la posición correcta.
    # Devuelve un número entre 0 y 100.
    # Hay un pequeño bonus si la longitud de la respuesta es exacta.
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
    # Calcula un bonus de puntos según qué tan rápido transmitió el jugador.
    # Se compara contra un tiempo base proporcional al largo de la frase.
    # Devuelve los puntos de bonus y una etiqueta de velocidad.
    if segundos <= largo * 2.4:   return 30, "RÁPIDO"
    elif segundos <= largo * 3.4: return 15, "MEDIO"
    else:                          return 0,  "LENTO"

def frase_aleatoria():
    # Elige y devuelve una frase al azar de la lista FRASES.
    return random.choice(FRASES)

#  FUNCIONES SERIAL (comunicación con el Arduino)

def serial_listar_puertos():
    # Devuelve la lista de puertos COM disponibles en la computadora.
    # Si no hay pyserial instalado, devuelve una opción de simulación.
    if not HAY_SERIAL:
        return ["Simulación (sin Arduino)"]
    puertos = serial.tools.list_ports.comports()
    return [p.device for p in puertos] or ["Ninguno detectado"]

def serial_conectar(puerto):
    # Intenta abrir la conexión con el Arduino en el puerto indicado.
    # Si falla o no hay Arduino, activa el modo simulación automáticamente.
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
    # Envía un texto al Arduino terminado en salto de línea (\n).
    # En simulación solo imprime en consola para que podamos ver qué se enviaría.
    if modo_simulacion:
        print(f"[SIM] → {mensaje}")
        return
    if conexion_serial:
        try:
            conexion_serial.write(f"{mensaje}\n".encode())
        except:
            pass

def serial_leer():
    # Revisa si el Arduino envió algo y lo devuelve.
    # Ahora entiende mensajes:
    #   MORSE:.-      -> código morse de una letra
    #   LETRA:A       -> letra ya decodificada por Arduino
    #   BORRAR        -> limpiar entrada de maqueta
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
    # Cierra la conexión con el Arduino de forma limpia.
    global conexion_serial
    if conexion_serial:
        conexion_serial.close()
        conexion_serial = None



#  FUNCIONES DE DIBUJO (se reusan en todas las ventanas)


def dibujar_fondo(canvas, w=800, h=650):
    # Dibuja el fondo oscuro degradado y líneas verticales en los bordes.
    # Se quitaron las líneas horizontales y puntos porque tapaban el texto.
    for y in range(0, h, 4):
        v = int(y / h * 18)  # v va de 0 a 18 → color va de casi negro a gris muy oscuro
        canvas.create_rectangle(0, y, w, y+4,
                                 fill=f"#{v:02x}{v:02x}{v+8:02x}", outline="")
    # Solo mantenemos las líneas verticales en los bordes laterales
    for x in [15, 18, w-18, w-15]:
        canvas.create_line(x, 0, x, h, fill=ROJO_O)

def texto_glow(canvas, x, y, texto, tamaño):
    # Escribe un texto con efecto de brillo rojo.
    # El truco es escribir el mismo texto dos veces:
    # primero en rojo oscuro un poco desplazado (la "sombra")
    # y encima en rojo brillante en la posición real.
    canvas.create_text(x+2, y+2, text=texto,
                       font=(FUENTE, tamaño, "bold"), fill=ROJO_O)  # Sombra
    canvas.create_text(x,   y,   text=texto,
                       font=(FUENTE, tamaño, "bold"), fill=ROJO)    # Texto brillante

def boton(canvas, x, y, texto, accion):
    # Crea un botón con la estética retro del juego y lo coloca en el canvas.
    # 'accion' es la función que se ejecuta al hacer clic.
    b = tk.Button(canvas, text=texto, font=(FUENTE, 11, "bold"),
                  fg=ROJO, bg=NEGRO, activeforeground="white",
                  activebackground=ROJO_O, relief="flat",
                  cursor="hand2", command=accion)
    canvas.create_window(x, y, window=b)  # create_window incrusta el botón en el canvas
    return b


#  VENTANA 1: MENÚ PRINCIPAL

def abrir_menu():
    ventana = tk.Tk()
    ventana.title("Stranger Tec")
    ventana.geometry("800x650")
    ventana.resizable(False, False)

    canvas = tk.Canvas(ventana, width=800, height=650,
                       bg="black", bd=0, highlightthickness=0)
    canvas.pack()

    # Cargamos el GIF frame por frame con Pillow.
    # Tkinter por sí solo no puede animar GIFs, por eso necesitamos Pillow.
    gif = Image.open(os.path.join(CARPETA, "strangertec_menu.gif"))
    frames, tiempos = [], []
    try:
        while True:
            f = gif.copy().resize((800, 650), Image.LANCZOS)
            frames.append(ImageTk.PhotoImage(f))          # Convierte a formato tkinter
            tiempos.append(gif.info.get("duration", 80)) # Duración real de cada frame en ms
            gif.seek(gif.tell() + 1)                      # Pasar al siguiente frame
    except EOFError:
        pass  # EOFError significa que ya no hay más frames, es normal

    img_id = canvas.create_image(0, 0, anchor="nw", image=frames[0])

    # Guardamos los IDs de los after() para poder cancelarlos antes de cerrar.
    # Si no los cancelamos, tkinter intenta ejecutarlos sobre una ventana
    # que ya no existe y lanza un error.
    id_anim     = [None]
    id_parpadeo = [None]

    def animar(i=0):
        # Cambia al frame i del GIF y programa el siguiente cambio.
        canvas.itemconfig(img_id, image=frames[i])
        id_anim[0] = ventana.after(tiempos[i], animar, (i+1) % len(frames))

    # Texto "pulse cualquier botón"
    canvas.create_text(400, 570,
                       text="PULSE CUALQUIER BOTÓN PARA INICIAR ",
                       font=(FUENTE, 13, "bold"), fill=ROJO, tags="txt")

    vis = [True]  # Controla si el texto está visible o invisible
    def parpadear():
        # Alterna el color del texto entre rojo brillante y casi negro
        # para simular el efecto de parpadeo de pantalla retro.
        # El delay es aleatorio para que no sea tan mecánico.
        canvas.itemconfig("txt",    fill=ROJO      if vis[0] else "#1a0000")
        canvas.itemconfig("sombra", fill="#5a0000" if vis[0] else "#1a0000")
        vis[0] = not vis[0]
        id_parpadeo[0] = ventana.after(random.choice([400,500,600,800]), parpadear)

    animar()
    parpadear()

    def ir_a_config(e=None):
        # Cuando el usuario pulsa cualquier tecla o hace clic, vamos a configuración.
        # Primero desactivamos los eventos para que no se ejecute dos veces.
        ventana.unbind("<Key>")
        ventana.unbind("<Button-1>")
        # Cancelamos las animaciones pendientes antes de destruir la ventana
        if id_anim[0]:     ventana.after_cancel(id_anim[0])
        if id_parpadeo[0]: ventana.after_cancel(id_parpadeo[0])
        ventana.destroy()
        abrir_config()

    # Bind escucha eventos: cualquier tecla o clic del ratón llama a ir_a_config
    ventana.bind("<Key>",      ir_a_config)
    ventana.bind("<Button-1>", ir_a_config)
    ventana.mainloop()


#  VENTANA 2: CONFIGURACIÓN

def abrir_config():
    ventana = tk.Tk()
    ventana.title("Configuración")
    ventana.geometry("800x650")
    ventana.resizable(False, False)

    canvas = tk.Canvas(ventana, width=800, height=650,
                       bg=FONDO, bd=0, highlightthickness=0)
    canvas.pack()
    dibujar_fondo(canvas)
    texto_glow(canvas, 400, 40, "CONFIGURACIÓN", 22)

    # Selector de modo de juego (Radiobutton = botón de opción, solo uno activo)
    canvas.create_text(400, 100, text="MODO DE JUEGO",
                       font=(FUENTE, 12, "bold"), fill=ROJO_M)
    var_modo = tk.StringVar(value=juego["modo"])  # Variable ligada a los radiobuttons
    for txt, val, px in [("MODO A — Escucha y Transmisión", "A", 60),
                          ("MODO B — Transmisión Simple",    "B", 440)]:
        tk.Radiobutton(canvas, text=txt, variable=var_modo, value=val,
                       font=(FUENTE, 10, "bold"), fg=ROJO, bg=FONDO,
                       selectcolor=NEGRO, relief="flat",
                       activeforeground="white", activebackground=ROJO_O
                       ).place(x=px, y=120)

    # Selector de salida en la maqueta
    canvas.create_text(400, 185, text="SALIDA EN MAQUETA",
                       font=(FUENTE, 12, "bold"), fill=ROJO_M)
    var_salida = tk.StringVar(value=juego["salida"])
    for txt, val, px in [("💡 LEDs", "LED", 220), ("🔊 Buzzer", "BUZZER", 420)]:
        tk.Radiobutton(canvas, text=txt, variable=var_salida, value=val,
                       font=(FUENTE, 10, "bold"), fg=ROJO, bg=FONDO,
                       selectcolor=NEGRO, relief="flat",
                       activeforeground="white", activebackground=ROJO_O
                       ).place(x=px, y=205)

    # Menú desplegable para elegir el puerto serial del Arduino
    canvas.create_text(400, 265, text="PUERTO ARDUINO (cable USB)",
                       font=(FUENTE, 12, "bold"), fill=ROJO_M)
    puertos    = serial_listar_puertos()
    var_puerto = tk.StringVar(value=puertos[0])
    tk.OptionMenu(canvas, var_puerto, *puertos).place(x=290, y=283,
                                                       width=220, height=28)

    # Cuadro de texto para editar la lista de frases del juego
    canvas.create_text(400, 345, text="FRASES (una por línea, máx. 16 letras)",
                       font=(FUENTE, 10, "bold"), fill=ROJO_M)
    txt_frases = tk.Text(canvas, width=30, height=10,
                         font=(FUENTE, 11), fg=ROJO, bg=NEGRO,
                         insertbackground=ROJO, relief="flat",
                         highlightbackground=ROJO_O, highlightthickness=1)
    txt_frases.insert("1.0", "\n".join(FRASES))  # Ponemos las frases actuales de entrada
    canvas.create_window(400, 460, window=txt_frases)

    id_aviso = canvas.create_text(400, 555, text="",
                                   font=(FUENTE, 9), fill=AMARILLO)

    def iniciar():
        # Lee las frases del cuadro de texto, valida y guarda la configuración.
        global FRASES
        lineas    = txt_frases.get("1.0", "end").strip().split("\n")
        # Filtramos líneas vacías y las que superen 16 caracteres
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
        abrir_juego()

    boton(canvas, 400, 610, "[ INICIAR JUEGO ]", iniciar)
    ventana.mainloop()


#  VENTANA 3: JUEGO

def abrir_juego():
    # Preparamos la ronda: elegimos frase, reiniciamos turno y le avisamos al Arduino
    juego["frase"]       = frase_aleatoria()
    juego["turno"]       = 1
    juego["jugador_pc"]  = "A"
    juego["jugador_maq"] = "B"
    juego["t_inicio"]    = time.time()  # Guardamos la hora actual para medir velocidad

    serial_enviar(f"MODO:{juego['salida']}")   # Le decimos si usar LEDs o buzzer
    serial_enviar(f"FRASE:{juego['frase']}")   # Le decimos al Arduino qué frase reproducir

    ventana = tk.Tk()
    ventana.title("Stranger Tec — Juego")
    ventana.geometry("800x650")
    ventana.resizable(False, False)

    canvas = tk.Canvas(ventana, width=800, height=650,
                       bg=FONDO, bd=0, highlightthickness=0)
    canvas.pack()
    dibujar_fondo(canvas)
    texto_glow(canvas, 400, 38, "STRANGER TEC", 22)

    # Etiqueta que muestra en qué turno estamos y quién usa qué
    id_turno = canvas.create_text(400, 72, text="",
                                   font=(FUENTE, 11, "bold"), fill=ROJO_M)

    # Panel donde se muestra la frase y su equivalente en morse
    canvas.create_rectangle(60, 88, 740, 160, fill=NEGRO, outline=ROJO_O)
    id_frase       = canvas.create_text(400, 108, text="",
                                         font=(FUENTE, 15, "bold"), fill=ROJO)
    id_morse_frase = canvas.create_text(400, 140, text="",
                                         font=(FUENTE, 9), fill="#664444", width=660)

    # Panel de entrada para el jugador que usa la PC
    canvas.create_rectangle(60, 172, 740, 310, fill=NEGRO, outline=ROJO_O)
    id_label_pc = canvas.create_text(80, 190, text="", anchor="w",
                                      font=(FUENTE, 9, "bold"), fill=ROJO_M)
    # Campo de texto donde el jugador escribe el morse (. y -)
    entrada_pc  = tk.Text(canvas, width=58, height=2, font=(FUENTE, 13),
                          fg=ROJO, bg="#0a0a1a", insertbackground=ROJO,
                          relief="flat", highlightbackground=ROJO_O,
                          highlightthickness=1)
    canvas.create_window(400, 240, window=entrada_pc)
    # Muestra en tiempo real el texto decodificado de lo que escribe el jugador PC
    id_decode_pc = canvas.create_text(400, 292, text="",
                                       font=(FUENTE, 12, "bold"), fill=VERDE)

    # Panel que muestra lo que recibe del Arduino (jugador maqueta)
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

    # Barra inferior con los puntajes acumulados
    canvas.create_rectangle(30, 470, 770, 505, fill="#07070f", outline=ROJO_O)
    id_pts_a = canvas.create_text(120, 487, text="",
                                   font=(FUENTE, 11, "bold"), fill=ROJO_M)
    id_pts_b = canvas.create_text(680, 487, text="",
                                   font=(FUENTE, 11, "bold"), fill=ROJO_M)
    canvas.create_text(400, 487, text=f"RONDA {juego['ronda']}",
                       font=(FUENTE, 10, "bold"), fill="#330000")
    id_aviso = canvas.create_text(400, 530, text="",
                                   font=(FUENTE, 9), fill=AMARILLO)

    # Guardamos los IDs de los after() para cancelarlos antes de cambiar de ventana
    timer_on         = [False]
    id_after_timer   = [None]
    id_after_arduino = [None]

    def actualizar_pantalla():
        # Refresca todos los textos de la pantalla según el turno actual.
        # Se llama al inicio y después de cada cambio de turno.
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
            # En Modo A ambos jugadores ven la frase y la deben ingresar en morse
            canvas.itemconfig(id_frase,       text=juego["frase"])
            canvas.itemconfig(id_morse_frase, text=texto_a_morse(juego["frase"]))
            canvas.itemconfig(id_aviso,
                              text="Escucha/observa el morse emitido por la maqueta y responde")
        else:
            # En Modo B la frase está oculta porque el jugador de maqueta la transmite
            canvas.itemconfig(id_frase,       text="[ CLASIFICADO ]")
            canvas.itemconfig(id_morse_frase, text="")
            canvas.itemconfig(id_aviso,
                              text=f"La maqueta emite la palabra; JUG {jmaq}: responde con botones")

    def tick_timer():
        # Actualiza el cronómetro cada 100ms mientras esté activo.
        # time.time() devuelve los segundos actuales; la diferencia da el tiempo transcurrido.
        if timer_on[0]:
            seg = round(time.time() - juego["t_inicio"], 1)
            canvas.itemconfig(id_timer, text=f"⏱ {seg}s")
            id_after_timer[0] = ventana.after(100, tick_timer)

    # Acumulan lo que la maqueta va enviando letra por letra.
    # Ejemplo:
    #   Arduino manda MORSE:.- y LETRA:A
    #   Python guarda morse_maqueta = ".-" y texto_maqueta = "A"
    morse_maqueta = [""]
    texto_maqueta = [""]

    def revisar_arduino():
        # Revisa cada 200ms si el Arduino mandó datos.
        # Si llega una letra desde botones físicos, la agrega a la palabra de maqueta.
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
        # Se ejecuta cada vez que el jugador PC escribe algo.
        # Decodifica el morse en tiempo real y lo muestra en verde.
        m = entrada_pc.get("1.0", "end").strip()
        canvas.itemconfig(id_decode_pc, text=morse_a_texto(m) if m else "")

    # KeyRelease se dispara cada vez que el jugador suelta una tecla
    entrada_pc.bind("<KeyRelease>", al_escribir)

    def confirmar():
        # Se ejecuta al presionar "Confirmar Turno".
        # Recoge las respuestas, calcula puntajes y avanza el juego.
        morse_pc  = entrada_pc.get("1.0", "end").strip()
        morse_maq = morse_maqueta[0]

        # La PC se decodifica desde el campo de texto.
        # La maqueta ya viene decodificada desde Arduino y se acumula en texto_maqueta.
        texto_pc  = morse_a_texto(morse_pc)  if morse_pc  else ""
        texto_maq = texto_maqueta[0]

        pts_pc  = calcular_puntaje(juego["frase"], texto_pc)
        pts_maq = calcular_puntaje(juego["frase"], texto_maq)

        # En Modo B sumamos bonus de velocidad al jugador de la maqueta
        if juego["modo"] == "B":
            seg      = round(time.time() - juego["t_inicio"], 1)
            bonus, _ = velocidad_bonus(seg, len(juego["frase"]))
            pts_maq  = min(100, pts_maq + bonus)

        # Sumamos los puntos al jugador correcto según quién estaba en PC y quién en maqueta
        if juego["jugador_pc"] == "A":
            juego["pts_a"] += pts_pc
            juego["pts_b"] += pts_maq
        else:
            juego["pts_b"] += pts_pc
            juego["pts_a"] += pts_maq

        if juego["turno"] == 1:
            # Primer turno terminado: intercambiamos jugadores y esperamos el segundo
            juego["turno"]       = 2
            juego["jugador_pc"]  = "B"
            juego["jugador_maq"] = "A"
            juego["t_inicio"]    = time.time()
            entrada_pc.delete("1.0", "end")  # Limpiamos el campo de texto
            canvas.itemconfig(id_morse_maq,  text="[ esperando maqueta... ]")
            canvas.itemconfig(id_decode_maq, text="")
            canvas.itemconfig(id_decode_pc,  text="")
            morse_maqueta[0] = ""
            texto_maqueta[0] = ""
            timer_on[0] = juego["modo"] == "B"  # Timer solo activo en Modo B
            if timer_on[0]:
                tick_timer()
            serial_enviar("LISTO")  # Le avisamos al Arduino que puede recibir de nuevo
            actualizar_pantalla()
        else:
            # Segundo turno terminado: cancelamos los after() y vamos a resultados
            if id_after_timer[0]:   ventana.after_cancel(id_after_timer[0])
            if id_after_arduino[0]: ventana.after_cancel(id_after_arduino[0])
            serial_enviar("FIN")
            ventana.destroy()
            abrir_resultados(pts_pc, pts_maq)

    def volver_menu():
        # Cancelamos todo antes de salir para evitar errores
        if id_after_timer[0]:   ventana.after_cancel(id_after_timer[0])
        if id_after_arduino[0]: ventana.after_cancel(id_after_arduino[0])
        serial_desconectar()
        ventana.destroy()
        abrir_menu()

    boton(canvas, 280, 585, "[ CONFIRMAR TURNO ]", confirmar)
    boton(canvas, 560, 585, "[ MENÚ ]", volver_menu)

    # Arrancamos todo al abrir la ventana
    actualizar_pantalla()
    revisar_arduino()
    if juego["modo"] == "B":
        timer_on[0] = True
        tick_timer()
    serial_enviar("LISTO")
    ventana.mainloop()

#  VENTANA 4: RESULTADOS

def abrir_resultados(pts_ronda_pc, pts_ronda_maq):
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

    # Determinamos qué puntaje de ronda corresponde a cada jugador
    # según quién estaba en la PC durante el último turno
    pts_a_ronda = pts_ronda_pc  if juego["jugador_pc"] == "A" else pts_ronda_maq
    pts_b_ronda = pts_ronda_maq if juego["jugador_pc"] == "A" else pts_ronda_pc

    # Panel del Jugador A
    canvas.create_rectangle(60, 110, 370, 320, fill=NEGRO, outline=ROJO_O, width=2)
    texto_glow(canvas, 215, 138, "JUGADOR  A", 15)
    canvas.create_text(215, 190,
                       text=f"Puntos esta ronda: {pts_a_ronda}",
                       font=(FUENTE, 11, "bold"), fill=ROJO)
    canvas.create_text(215, 260,
                       text=f"TOTAL: {juego['pts_a']} pts",
                       font=(FUENTE, 13, "bold"), fill=AMARILLO)

    # Panel del Jugador B
    canvas.create_rectangle(430, 110, 740, 320, fill=NEGRO, outline=ROJO_O, width=2)
    texto_glow(canvas, 585, 138, "JUGADOR  B", 15)
    canvas.create_text(585, 190,
                       text=f"Puntos esta ronda: {pts_b_ronda}",
                       font=(FUENTE, 11, "bold"), fill=ROJO)
    canvas.create_text(585, 260,
                       text=f"TOTAL: {juego['pts_b']} pts",
                       font=(FUENTE, 13, "bold"), fill=AMARILLO)

    # Mensaje de quién va ganando según los puntajes acumulados
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

    # Botón para jugar otra ronda con una nueva frase aleatoria
    boton(canvas, 240, 470, "[ SIGUIENTE RONDA ]",
          lambda: [ventana.destroy(), abrir_juego()])
    # Botón para volver al inicio
    boton(canvas, 560, 470, "[ MENÚ PRINCIPAL ]",
          lambda: [ventana.destroy(), serial_desconectar(), abrir_menu()])

    ventana.mainloop()


# =============================================================================
#  INICIO DEL PROGRAMA
# =============================================================================
abrir_menu()
