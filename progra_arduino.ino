
const int LED_PIN = 13;
const int BUZZER_PIN = 8;

const int BOTON_PUNTO = 12;
const int BOTON_RAYA  = 7;
const int BOTON_ENTER = 4;

const int DATA1_A = 2;
const int DATA1_B = 3;

// Registro 2: 5 LEDs
const int DATA2_A = 9;
const int DATA2_B = 10;

const int CLK_PIN = 5;


const int LED_VERTICAL_1 = A1;
const int LED_VERTICAL_2 = A5;

String frase = "";
String modo = "LED";
String morseActual = "";


// =====================
// SETUP
// =====================
void setup() {
  Serial.begin(9600);

  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  pinMode(BOTON_PUNTO, INPUT_PULLUP);
  pinMode(BOTON_RAYA, INPUT_PULLUP);
  pinMode(BOTON_ENTER, INPUT_PULLUP);

  pinMode(DATA1_A, OUTPUT);
  pinMode(DATA1_B, OUTPUT);
  pinMode(DATA2_A, OUTPUT);
  pinMode(DATA2_B, OUTPUT);
  pinMode(CLK_PIN, OUTPUT);

  pinMode(LED_VERTICAL_1, OUTPUT);
  pinMode(LED_VERTICAL_2, OUTPUT);

  limpiarMatriz();
}


// =====================
// LOOP PRINCIPAL
// =====================
void loop() {
  leerPython();
  leerBotones();
}


// =====================
// LEER PYTHON
// =====================
void leerPython() {
  if (Serial.available()) {
    String mensaje = Serial.readStringUntil('\n');
    mensaje.trim();

    if (mensaje.startsWith("FRASE:")) {
      frase = mensaje.substring(6);
      frase.toUpperCase();
    }

    else if (mensaje.startsWith("MODO:")) {
      modo = mensaje.substring(5);
      modo.toUpperCase();
    }

    else if (mensaje == "LISTO") {
      morseActual = "";
      limpiarMatriz();
      reproducirFrase(frase);  // LED/buzzer emite la palabra elegida por Python
    }

    else if (mensaje == "FIN") {
      morseActual = "";
      limpiarMatriz();
      apagarTodo();
    }
  }
}


// =====================
// LEER BOTONES
// =====================
void leerBotones() {
  if (botonPresionado(BOTON_PUNTO)) {
    morseActual += ".";   // el botón solo escribe; no emite sonido/luz
  }

  if (botonPresionado(BOTON_RAYA)) {
    morseActual += "-";   // el botón solo escribe; no emite sonido/luz
  }

  if (botonPresionado(BOTON_ENTER)) {
    char letra = morseALetra(morseActual);

    if (letra != '?') {
      mostrarLetra(letra);

      Serial.print("MORSE:");
      Serial.println(morseActual);

      Serial.print("LETRA:");
      Serial.println(letra);
    }

    morseActual = "";
  }
}


// =====================
// BOTÓN CON ANTIRREBOTE
// =====================
bool botonPresionado(int pin) {
  if (digitalRead(pin) == LOW) {
    delay(50);

    if (digitalRead(pin) == LOW) {
      while (digitalRead(pin) == LOW) {
        delay(10);
      }
      return true;
    }
  }

  return false;
}


// =====================
// MORSE A LETRA
// =====================
char morseALetra(String m) {
  if (m == ".-") return 'A';
  if (m == "-...") return 'B';
  if (m == "-.-.") return 'C';
  if (m == "-..") return 'D';
  if (m == ".") return 'E';
  if (m == "..-.") return 'F';
  if (m == "--.") return 'G';
  if (m == "....") return 'H';
  if (m == "..") return 'I';
  if (m == ".---") return 'J';
  if (m == "-.-") return 'K';
  if (m == ".-..") return 'L';
  if (m == "--") return 'M';
  if (m == "-.") return 'N';
  if (m == "---") return 'O';
  if (m == ".--.") return 'P';
  if (m == "--.-") return 'Q';
  if (m == ".-.") return 'R';
  if (m == "...") return 'S';
  if (m == "-") return 'T';
  if (m == "..-") return 'U';
  if (m == "...-") return 'V';
  if (m == ".--") return 'W';
  if (m == "-..-") return 'X';
  if (m == "-.--") return 'Y';
  if (m == "--..") return 'Z';

  return '?';
}


// =====================
// MOSTRAR LETRA EN MATRIZ
// =====================
void mostrarLetra(char letra) {
  limpiarMatriz();

  int indice = letra - 'A';

  if (indice < 0 || indice > 25) return;

  int fila;
  int columna;

  if (indice < 13) {
    fila = 1;
    columna = indice;
  } else {
    fila = 2;
    columna = indice - 13;
  }

  if (fila == 1) {
    digitalWrite(LED_VERTICAL_1, HIGH);
    digitalWrite(LED_VERTICAL_2, LOW);
  } else {
    digitalWrite(LED_VERTICAL_1, LOW);
    digitalWrite(LED_VERTICAL_2, HIGH);
  }

  encenderColumna(columna);
}


// =====================
// ENCENDER COLUMNA
// =====================
void encenderColumna(int columna) {
  byte registro1 = 0;
  byte registro2 = 0;

  if (columna >= 0 && columna <= 7) {
    registro1 = 1 << columna;
  }

  else if (columna >= 8 && columna <= 12) {
    registro2 = 1 << (columna - 8);
  }

  enviarRegistros(registro1, registro2);
}


// =====================
// ENVIAR DATOS A LOS 2 74LS164
// =====================
void enviarRegistros(byte valor1, byte valor2) {
  for (int i = 7; i >= 0; i--) {
    int bit1 = (valor1 >> i) & 1;
    int bit2 = (valor2 >> i) & 1;

    digitalWrite(DATA1_A, bit1);
    digitalWrite(DATA1_B, bit1);

    digitalWrite(DATA2_A, bit2);
    digitalWrite(DATA2_B, bit2);

    digitalWrite(CLK_PIN, HIGH);
    delayMicroseconds(20);
    digitalWrite(CLK_PIN, LOW);
    delayMicroseconds(20);
  }
}


// =====================
// LIMPIAR MATRIZ
// =====================
void limpiarMatriz() {
  digitalWrite(LED_VERTICAL_1, LOW);
  digitalWrite(LED_VERTICAL_2, LOW);
  enviarRegistros(0, 0);
}


// =====================
// LETRA A MORSE
// =====================
String letraAMorse(char c) {
  switch (toupper(c)) {
    case 'A': return ".-";
    case 'B': return "-...";
    case 'C': return "-.-.";
    case 'D': return "-..";
    case 'E': return ".";
    case 'F': return "..-.";
    case 'G': return "--.";
    case 'H': return "....";
    case 'I': return "..";
    case 'J': return ".---";
    case 'K': return "-.-";
    case 'L': return ".-..";
    case 'M': return "--";
    case 'N': return "-.";
    case 'O': return "---";
    case 'P': return ".--.";
    case 'Q': return "--.-";
    case 'R': return ".-.";
    case 'S': return "...";
    case 'T': return "-";
    case 'U': return "..-";
    case 'V': return "...-";
    case 'W': return ".--";
    case 'X': return "-..-";
    case 'Y': return "-.--";
    case 'Z': return "--..";
    default: return "";
  }
}


// =====================
// REPRODUCIR PALABRA SECRETA
// =====================
void reproducirFrase(String texto) {
  if (texto.length() == 0) return;

  delay(500); // pequeña pausa antes de empezar

  for (int i = 0; i < texto.length(); i++) {
    String codigo = letraAMorse(texto[i]);
    if (codigo.length() == 0) continue;

    reproducirMorse(codigo);
    delay(600); // espacio entre letras
  }
}

void reproducirMorse(String codigo) {
  for (int i = 0; i < codigo.length(); i++) {
    if (codigo[i] == '.') {
      punto();
    }
    else if (codigo[i] == '-') {
      raya();
    }
  }
}


// =====================
// PUNTO Y RAYA
// =====================
void punto() {
  activarSalida(200);
  delay(150);
}

void raya() {
  activarSalida(600);
  delay(150);
}

void activarSalida(int duracion) {
  if (modo == "LED") {
    digitalWrite(LED_PIN, HIGH);
    delay(duracion);
    digitalWrite(LED_PIN, LOW);
  }

  else if (modo == "BUZZER") {
    tone(BUZZER_PIN, 700);
    delay(duracion);
    noTone(BUZZER_PIN);
  }

  else {
    digitalWrite(LED_PIN, HIGH);
    tone(BUZZER_PIN, 700);
    delay(duracion);
    digitalWrite(LED_PIN, LOW);
    noTone(BUZZER_PIN);
  }
}

void apagarTodo() {
  digitalWrite(LED_PIN, LOW);
  noTone(BUZZER_PIN);
}