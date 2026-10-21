# Archivo: tesis.py  (corre en el Orange Pi 4 Pro)
# Recibe "X1,Y1,X2,Y2" por UDP (Tailscale) y envia a la Pico por I2C los
# 4 bytes que espera su main.py: [alabeo, cabeceo, guinada, gas]
import socket
import smbus2

# --- CONFIGURACIÓN DE RED (Tailscale) ---
IP_ESCUCHA = '0.0.0.0'
PUERTO_UDP = 5005

# --- CONFIGURACIÓN DE HARDWARE (Pico) ---
NUMERO_BUS = 2
DIRECCION_PICO = 0x08

# --- ASIGNACIÓN DE JOYSTICKS (modo 2) ---
#   Joystick 1 (izquierdo): X1 = guiñada (timones), Y1 = gas
#   Joystick 2 (derecho):   X2 = alabeo (alerones), Y2 = cabeceo (profundidad)
# Si un eje responde al revés, pon su INVERTIR en True.
INVERTIR_ALABEO = False
INVERTIR_CABECEO = False
INVERTIR_GUINADA = False
INVERTIR_GAS = False

CENTRO_JOY = 512      # valor del joystick en reposo (0-1023)
ZONA_MUERTA = 4       # grados alrededor de 90 que se toman como centro exacto
ZONA_MUERTA_GAS = 20  # cuentas sobre el centro antes de empezar a dar gas

# --- RETENCIÓN ANTE PÉRDIDA DE PAQUETES UDP ---
# Si no llegan paquetes, se reenvía el último comando durante 1 s para
# aguantar cortes breves de la red. Después se deja de escribir por I2C
# y la Pico entra sola en failsafe (motor a 0, superficies al centro).
TIMEOUT_UDP = 0.05        # segundos de espera por paquete
CICLOS_RETENCION = 20     # 20 x 0,05 s = 1 s de retención


# 1. Abrimos el Hardware primero
try:
    bus = smbus2.SMBus(NUMERO_BUS)
    print(f" ✅ Bus I2C {NUMERO_BUS} abierto correctamente.")
except Exception as e:
    print(f" ❌ Error al abrir el bus I2C: {e}")
    exit()

# 2. Abrimos la Red después
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    sock.bind((IP_ESCUCHA, PUERTO_UDP))
    sock.settimeout(TIMEOUT_UDP)
    print(f" 📡 Servidor UDP iniciado. Escuchando en el puerto {PUERTO_UDP}...\n")
    print("-" * 60)
except Exception as e:
    print(f" ❌ Error al abrir el puerto UDP: {e}")
    bus.close()
    exit()


# --- FUNCIONES MATEMÁTICAS DE MAPEO ---
def mapear_a_angulo(valor_joystick_str, invertir=False):
    """Convierte el rango 0-1023 del joystick al rango 0-180 (90 = neutro)"""
    try:
        # 1. Convertimos el texto a número entero
        valor = int(valor_joystick_str)

        # 2. Por seguridad, limitamos el valor por si hay ruido en la señal
        valor = max(0, min(1023, valor))
        if invertir:
            valor = 1023 - valor

        # 3. Regla de 3 simple: (valor / Max_Joy) * Max_Servo
        angulo = round((valor / 1023) * 180)

        # 4. Zona muerta: el joystick en reposo nunca da 90 exacto
        if abs(angulo - 90) <= ZONA_MUERTA:
            angulo = 90

        return angulo

    except ValueError:
        return None  # Si llega basura por red, lo ignoramos


def mapear_a_gas(valor_joystick_str, invertir=False):
    """
    Convierte el eje Y1 en gas de 0 a 100 %.
    Solo la mitad superior da gas: al soltar el joystick (vuelve al centro)
    o bajarlo, el gas es 0. Así el motor nunca queda encendido por accidente.
    """
    try:
        valor = int(valor_joystick_str)
        valor = max(0, min(1023, valor))
        if invertir:
            valor = 1023 - valor

        inicio = CENTRO_JOY + ZONA_MUERTA_GAS
        if valor <= inicio:
            return 0

        gas = round((valor - inicio) / (1023 - inicio) * 100)
        return min(100, gas)

    except ValueError:
        return None


def enviar_a_pico(comando):
    """Escribe los 4 bytes desde el registro 0 de la Pico. Devuelve True si salió bien."""
    try:
        bus.write_i2c_block_data(DIRECCION_PICO, 0x00, comando)
        return True
    except OSError:
        print(" ⚠️ Error (NACK) - La Pico no respondió al envío del comando.")
        return False


# --- BUCLE PRINCIPAL DE TELEOPERACIÓN ---
ultimo_comando = None
ciclos_sin_datos = 0

try:
    while True:
        # Espera un paquete UDP como máximo TIMEOUT_UDP segundos
        try:
            datos_bytes, direccion_origen = sock.recvfrom(1024)
        except socket.timeout:
            ciclos_sin_datos += 1
            if ultimo_comando is not None and ciclos_sin_datos <= CICLOS_RETENCION:
                enviar_a_pico(ultimo_comando)   # mantenemos viva a la Pico
            elif ciclos_sin_datos == CICLOS_RETENCION + 1:
                print(" ⚠️ Sin datos UDP por más de 1 s: la Pico entra en failsafe.")
            continue

        if ciclos_sin_datos > CICLOS_RETENCION:
            print(" 🔗 Enlace UDP recuperado.")
        ciclos_sin_datos = 0

        try:
            mensaje = datos_bytes.decode('utf-8')
        except UnicodeDecodeError:
            continue   # paquete corrupto, lo ignoramos

        datos = mensaje.split(',')

        # Si el paquete viene completo con los 4 datos (x1, y1, x2, y2)
        if len(datos) == 4:
            x1, y1, x2, y2 = datos
            ip_remota = direccion_origen[0]

            alabeo = mapear_a_angulo(x2, INVERTIR_ALABEO)
            cabeceo = mapear_a_angulo(y2, INVERTIR_CABECEO)
            guinada = mapear_a_angulo(x1, INVERTIR_GUINADA)
            gas = mapear_a_gas(y1, INVERTIR_GAS)

            if None not in (alabeo, cabeceo, guinada, gas):
                comando = [alabeo, cabeceo, guinada, gas]

                # ¡Disparo directo por hardware a la Pico!
                if enviar_a_pico(comando):
                    ultimo_comando = comando
                    # Imprimimos en consola para monitorear
                    print(f"Tailscale ({ip_remota}) -> Roll {alabeo:>3}° | Pitch {cabeceo:>3}° | "
                          f"Yaw {guinada:>3}° | Gas {gas:>3}% ➔ I2C OK")

except KeyboardInterrupt:
    print("\n 🛑 Teleoperación detenida por el usuario.")
finally:
    # Dejamos todo en neutro con el motor a 0 antes de salir
    try:
        bus.write_i2c_block_data(DIRECCION_PICO, 0x00, [90, 90, 90, 0])
    except OSError:
        pass
    # Siempre cerramos los puertos al salir para no bloquear el sistema operativo
    sock.close()
    bus.close()
    print("Puertos cerrados limpios. ¡Todo apagado!")