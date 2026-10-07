# Archivo: lector_serial.py  (corre en la laptop)
# Lee del Arduino las lineas "X1,Y1,X2,Y2" y las entrega al transmisor con yield.
import serial
import time

MOSTRAR_LOCAL = True   # False para no imprimir cada lectura (menos carga)


def leer_joysticks():
    # Configuración del puerto serial
    PUERTO = '/dev/ttyACM0'   # En Windows sera algo como 'COM3'
    BAUD_RATE = 9600

    try:
        print(f"Intentando conectar al puerto {PUERTO}...")
        arduino = serial.Serial(PUERTO, BAUD_RATE, timeout=1)
        time.sleep(2)                  # el Arduino se reinicia al abrir el puerto
        arduino.reset_input_buffer()   # descartamos datos viejos o cortados
        print("¡Conectado exitosamente! Escuchando a ambos joysticks...\n")
        print("-" * 50)

        while True:
            if arduino.in_waiting > 0:
                try:
                    linea_recibida = arduino.readline().decode('utf-8').strip()
                except UnicodeDecodeError:
                    continue   # linea corrupta (pasa al conectar); la ignoramos

                datos = linea_recibida.split(',')

                # Solo aceptamos lineas completas con 4 numeros validos
                if len(datos) == 4 and all(d.isdigit() for d in datos):
                    x1, y1, x2, y2 = datos

                    if MOSTRAR_LOCAL:
                        print(f"Local -> Joy 1 [X: {x1:<4} Y: {y1:<4}] | Joy 2 [X: {x2:<4} Y: {y2:<4}]")

                    # YIELD "escupe" los datos hacia el transmisor sin romper el bucle While
                    yield x1, y1, x2, y2
            else:
                time.sleep(0.005)   # evita usar el 100 % del CPU mientras espera datos

    except serial.SerialException as e:
        print(f"\nError de conexión: {e}")
    except ValueError:
        pass
    except KeyboardInterrupt:
        print("\nLectura detenida por el usuario.")
    finally:
        if 'arduino' in locals() and arduino.is_open:
            arduino.close()
            print("Puerto serial cerrado correctamente.")