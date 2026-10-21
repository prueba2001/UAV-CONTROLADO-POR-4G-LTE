// =====================================================================
//  Joystick.ino - Arduino UNO
//  Lee los 2 joysticks y envia "X1,Y1,X2,Y2" (0-1023) por serial a la laptop
//
//  Asignacion de mandos (modo 2, como una radio RC):
//   Joystick 1 (izquierdo): X1 = guinada (timones), Y1 = gas
//   Joystick 2 (derecho):   X2 = alabeo (alerones), Y2 = cabeceo (profundidad)
//  La conversion a grados y a % de gas se hace en el Orange Pi (tesis.py).
// =====================================================================

// Definir los pines para el Joystick 1
const int pinX1 = A0;
const int pinY1 = A1;

// Definir los pines para el Joystick 2
const int pinX2 = A2;
const int pinY2 = A3;

void setup() {
  // Iniciar la comunicación serial
  Serial.begin(9600);
}

void loop() {
  // Leer valores del Joystick 1
  int valorX1 = analogRead(pinX1);
  int valorY1 = analogRead(pinY1);

  // Leer valores del Joystick 2
  int valorX2 = analogRead(pinX2);
  int valorY2 = analogRead(pinY2);

  // Enviar los datos estructurados y separados por comas
  Serial.print(valorX1);
  Serial.print(",");
  Serial.print(valorY1);
  Serial.print(",");
  Serial.print(valorX2);
  Serial.print(",");
  Serial.println(valorY2); // El println final da el salto de línea para Python

  // Pausa de 50 milisegundos (20 envios por segundo).
  // Antes eran 100 ms: con 50 ms el avion responde mas rapido y la Pico
  // recibe datos con margen de sobra frente a su failsafe de 500 ms.
  delay(50);
}
