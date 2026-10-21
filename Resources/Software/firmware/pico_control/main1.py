import sys
import time
from machine import Pin, PWM, I2C

# =====================================================================
#  UAV ALAPALAP - CONTROL DE 5 SERVOS SG90 + ESC BRUSHLESS POR I2C
#  RPi Pico (esclavo I2C 0x08) <- Orange Pi 4 Pro (maestro)
#
#  Superficies segun el informe:
#   - Alabeo (roll):  2 servos, aleron izquierdo y derecho (opuestos)
#                     Con ROLL_NEUTRO = True no se obedece la casilla 0:
#                     si ESTABILIZAR_ROLL = True el MPU6050 mantiene las
#                     alas niveladas; si no, alerones fijos al centro
#   - Cabeceo (pitch): 1 servo, timon de profundidad S3
#   - Guinada (yaw):  2 servos, timones S4 de las dos derivas (juntos)
#   - Motor: ESC 40 A + brushless 4S 920 kV (siempre armado:
#     gira en cuanto el gas es mayor que 0 y hay comunicacion)
# =====================================================================

# --- 0. OPCIONES ---
CALIBRAR_ESC = False   # True solo la primera vez (necesita consola USB)
DEBUG = True           # False en vuelo: los print() hacen mas lento el bucle
ROLL_NEUTRO = True     # True: se ignora la casilla 0 (el piloto no manda alabeo)
ESTABILIZAR_ROLL = True  # True: el MPU6050 mantiene las alas niveladas

# --- 1. CHEQUEO DE FIRMWARE I2C ---
try:
    from machine import I2CTarget
except ImportError:
    print("Error: Actualiza MicroPython a v1.26 o superior.")
    sys.exit()

# --- 2. CONFIGURACION DE PINES ---
PIN_SDA = 0
PIN_SCL = 1
PIN_ALERON_IZQ = 2
PIN_ALERON_DER = 3
PIN_PROFUNDIDAD = 4
PIN_TIMON_IZQ = 5
PIN_TIMON_DER = 6
PIN_ESC = 15
PIN_IMU_SDA = 10   # MPU6050 en el bus I2C1 (el I2C0 lo usa el Orange Pi)
PIN_IMU_SCL = 11

CENTRO = 90  # grados del servo en posicion neutra

# Limite de deflexion por eje (grados a cada lado del centro).
# Las superficies no necesitan 180 grados; esto evita que el SG90
# choque con su tope interno y consuma corriente de mas.
LIMITE_ALABEO = 25
LIMITE_CABECEO = 25
LIMITE_GUINADA = 30

# Configuracion de cada servo: pin, eje, sentido y trim (grados).
# sentido = 1 o -1. Si una superficie se mueve al reves, cambia su signo.
# trim = correccion fina del centro de cada servo tras el montaje.
SERVOS_CFG = {
    "aleron_izq":  {"pin": PIN_ALERON_IZQ,  "eje": "alabeo",  "sentido": 1,  "trim": 0},
    "aleron_der":  {"pin": PIN_ALERON_DER,  "eje": "alabeo",  "sentido": -1, "trim": 0},
    "profundidad": {"pin": PIN_PROFUNDIDAD, "eje": "cabeceo", "sentido": 1,  "trim": 0},
    "timon_izq":   {"pin": PIN_TIMON_IZQ,   "eje": "guinada", "sentido": 1,  "trim": 0},
    "timon_der":   {"pin": PIN_TIMON_DER,   "eje": "guinada", "sentido": 1,  "trim": 0},
}
LIMITES = {"alabeo": LIMITE_ALABEO, "cabeceo": LIMITE_CABECEO, "guinada": LIMITE_GUINADA}

# ESC
ESC_MIN_US = 1000
ESC_MAX_US = 2000
RAMPA_GAS_US = 10       # cambio maximo de pulso por ciclo (0 -> 100 % en 0,5 s)

# Failsafe: si el maestro deja de escribir por I2C durante este tiempo,
# motor apagado, profundidad y timones al centro y, si el MPU6050 funciona,
# alas niveladas (el avion planea recto con L/D ~ 11).
# Para pruebas manuales con i2cset puedes subirlo a 5000.
FAILSAFE_MS = 500

# --- ESTABILIZACION DE ROLL (MPU6050) ---
DIR_MPU = 0x68       # direccion I2C del MPU6050 (0x69 si AD0 va a 3V3)
SENTIDO_IMU = 1      # si al bajar el ala DERECHA el roll sale negativo, pon -1
KP_ROLL = 0.8        # grados de aleron por cada grado de inclinacion
KD_ROLL = 0.05       # grados de aleron por cada grado/s de velocidad de alabeo
KI_ROLL = 0.0        # corrige inclinaciones pequenas persistentes (empieza en 0)
LIMITE_INTEGRAL = 10  # limite del termino integral (grados de aleron)
ANGULO_MAX_ROLL = 30  # con ROLL_NEUTRO = False: inclinacion maxima que pide la casilla 0
FILTRO_ALFA = 0.995   # filtro complementario: cuanto se confia en el giroscopio

# --- 3. CONFIGURACION DE LOS SERVOS 180 ---
servos = {}
for nombre, cfg in SERVOS_CFG.items():
    pwm = PWM(Pin(cfg["pin"]))
    pwm.freq(50)  # El SG90 funciona a 50 Hz
    servos[nombre] = pwm


def controlar_servo_180(servo, angulo):
    """
    Traduce un angulo de 0 a 180 grados a ciclo de trabajo:
    - 0   : 0 grados (extremo)   -> ~0.5 ms
    - 90  : 90 grados (centro)   -> ~1.5 ms
    - 180 : 180 grados (extremo) -> ~2.5 ms
    """
    if angulo > 180:
        angulo = 180
    elif angulo < 0:
        angulo = 0
    duty = int(1638 + (angulo / 180) * (8192 - 1638))
    servo.duty_u16(duty)


def aplicar_superficies(cmd_alabeo, cmd_cabeceo, cmd_guinada):
    """
    Recibe los tres comandos (0-180, 90 = neutro) y mueve los 5 servos.
    Los alerones se mueven en sentidos opuestos; los dos timones juntos.
    """
    comandos = {"alabeo": cmd_alabeo, "cabeceo": cmd_cabeceo, "guinada": cmd_guinada}
    for nombre, cfg in SERVOS_CFG.items():
        eje = cfg["eje"]
        limite = LIMITES[eje]
        deflexion = comandos[eje] - CENTRO
        if deflexion > limite:
            deflexion = limite
        elif deflexion < -limite:
            deflexion = -limite
        angulo = CENTRO + cfg["trim"] + cfg["sentido"] * deflexion
        controlar_servo_180(servos[nombre], angulo)


# --- 4. CONFIGURACION DEL ESC ---
esc = PWM(Pin(PIN_ESC))
esc.freq(50)


def set_pulse_us(us):
    duty = int((us / 20000) * 65535)
    esc.duty_u16(duty)


def calibrar_esc():
    print("--- PROCEDIMIENTO DE CALIBRACIÓN ---")
    print("¡QUITA LA HÉLICE ANTES DE CONTINUAR!")
    print("1. DESCONECTA la batería 4S del ESC.")
    print("2. Enviando señal MÁXIMA (2000us)...")
    set_pulse_us(ESC_MAX_US)
    input("Presiona ENTER en la consola cuando hayas CONECTADO la batería 4S...")
    print("Esperando tonos de calibración del ESC (2 segundos)...")
    time.sleep(2)
    print("Enviando señal MÍNIMA (1000us)...")
    set_pulse_us(ESC_MIN_US)
    time.sleep(3)
    print("¡Calibración completada! El ESC ya reconoce el rango correcto.")


def gas_a_pulso(porcentaje):
    if porcentaje > 100:
        porcentaje = 100
    return ESC_MIN_US + int(porcentaje * (ESC_MAX_US - ESC_MIN_US) / 100)


def detener_todo():
    set_pulse_us(ESC_MIN_US)
    aplicar_superficies(CENTRO, CENTRO, CENTRO)


# --- 4.1 FUNCIONES DEL MPU6050 ---
PI = 3.14159265


def atan2_grados(y, x):
    """atan2 aproximado en grados (error < 0,3 grados), sin librerias extra."""
    if x == 0 and y == 0:
        return 0.0
    if abs(x) >= abs(y):
        z = y / x
        a = (PI / 4) * z + 0.273 * z * (1 - abs(z))
        if x < 0:
            a = a + PI if y >= 0 else a - PI
    else:
        z = x / y
        a = (PI / 4) * z + 0.273 * z * (1 - abs(z))
        a = (PI / 2 - a) if y > 0 else (-PI / 2 - a)
    return a * 57.29578


def a_entero_con_signo(alto, bajo):
    valor = (alto << 8) | bajo
    return valor - 65536 if valor > 32767 else valor


imu = None


def iniciar_mpu():
    global imu
    imu = I2C(1, sda=Pin(PIN_IMU_SDA), scl=Pin(PIN_IMU_SCL), freq=400000)
    if DIR_MPU not in imu.scan():
        raise OSError("MPU6050 no encontrado en el bus I2C1")
    imu.writeto_mem(DIR_MPU, 0x6B, b'\x00')  # despertar el sensor
    time.sleep_ms(100)
    imu.writeto_mem(DIR_MPU, 0x1A, b'\x03')  # filtro paso bajo ~44 Hz (vibracion)
    imu.writeto_mem(DIR_MPU, 0x1B, b'\x08')  # giroscopio +-500 grados/s
    imu.writeto_mem(DIR_MPU, 0x1C, b'\x00')  # acelerometro +-2 g


def leer_mpu():
    """Devuelve aceleracion Y, aceleracion Z y giro en X (grados/s)."""
    d = imu.readfrom_mem(DIR_MPU, 0x3B, 14)
    ay = a_entero_con_signo(d[2], d[3])
    az = a_entero_con_signo(d[4], d[5])
    gx = a_entero_con_signo(d[8], d[9]) / 65.5
    return ay, az, gx


def calibrar_giroscopio(muestras=200):
    """Promedia el giroscopio quieto para eliminar su desvio (1 s)."""
    suma = 0.0
    for _ in range(muestras):
        suma += leer_mpu()[2]
        time.sleep_ms(5)
    return suma / muestras


# Arranque seguro: motor al minimo y superficies al centro ANTES de todo
set_pulse_us(ESC_MIN_US)
aplicar_superficies(CENTRO, CENTRO, CENTRO)

if CALIBRAR_ESC:
    calibrar_esc()
else:
    print("Inicializando ESC con señal mínima (3 s)...")
    time.sleep(3)

# --- 4.2 ARRANQUE DEL MPU6050 ---
imu_ok = False
sesgo_giro = 0.0
roll = 0.0          # inclinacion lateral estimada (grados, + = ala derecha abajo)
tasa_roll = 0.0     # velocidad de alabeo (grados/s)
integral_roll = 0.0
errores_imu = 0

if ESTABILIZAR_ROLL:
    try:
        iniciar_mpu()
        print("🧭 MPU6050 listo. NO MUEVAS EL AVIÓN: calibrando giroscopio (1 s)...")
        sesgo_giro = calibrar_giroscopio()
        ay, az, gx = leer_mpu()
        roll = SENTIDO_IMU * atan2_grados(ay, az)
        imu_ok = True
        print(f"✅ Estabilizacion de roll activa. Inclinacion inicial: {roll:+.1f}°")
    except Exception as e:
        print(f"⚠️ MPU6050 no disponible ({e}): alerones al centro sin estabilizar")


def estabilizar_roll(objetivo, dt):
    """Controlador PID: devuelve el comando de alabeo (0-180, 90 = neutro)."""
    global integral_roll
    error = objetivo - roll
    integral_roll += error * dt
    if KI_ROLL > 0:
        maximo = LIMITE_INTEGRAL / KI_ROLL
        integral_roll = max(-maximo, min(maximo, integral_roll))
    else:
        integral_roll = 0.0
    correccion = KP_ROLL * error + KI_ROLL * integral_roll - KD_ROLL * tasa_roll
    correccion = max(-LIMITE_ALABEO, min(LIMITE_ALABEO, correccion))
    return CENTRO + correccion

# --- 5. CONFIGURACION I2C (TARGET) ---
# Mapa de memoria (el maestro escribe desde el registro 0):
#   [0] alabeo   0-180 (90 = neutro) -> ignorado si ROLL_NEUTRO = True
#   [1] cabeceo  0-180 (90 = neutro)
#   [2] guinada  0-180 (90 = neutro)
#   [3] gas      0-100 %
REG_ALABEO, REG_CABECEO, REG_GUINADA, REG_GAS = range(4)
memoria = bytearray([CENTRO, CENTRO, CENTRO, 0])  # arranque en neutro

# Hora de la ultima escritura recibida (la anota la interrupcion I2C)
t_ultima_escritura = time.ticks_ms()
hubo_escritura = False


def al_recibir_escritura(i2c):
    """Se ejecuta cada vez que el maestro termina de escribir."""
    global t_ultima_escritura, hubo_escritura
    t_ultima_escritura = time.ticks_ms()
    hubo_escritura = True


try:
    pico_esclavo = I2CTarget(0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), addr=0x08, mem=memoria)
    pico_esclavo.irq(al_recibir_escritura, trigger=I2CTarget.IRQ_END_WRITE)
    print("✅ Pico lista (I2C en 0x08): 5 servos + ESC. ¡Esperando comandos!")
except Exception as e:
    print(f"Error iniciando I2C: {e}")
    detener_todo()
    sys.exit()

ultimo_estado = None
pulso_actual = ESC_MIN_US
en_failsafe = True  # hasta recibir la primera escritura
t_anterior_us = time.ticks_us()
t_ultimo_print = time.ticks_ms()

# --- 6. BUCLE PRINCIPAL ---
try:
    while True:
        ahora = time.ticks_ms()
        ahora_us = time.ticks_us()
        dt = time.ticks_diff(ahora_us, t_anterior_us) / 1000000
        t_anterior_us = ahora_us

        # 6.0 Sensor: estima la inclinacion con filtro complementario
        #     (giroscopio rapido + acelerometro que corrige la deriva)
        if imu_ok:
            try:
                ay, az, gx = leer_mpu()
                tasa_roll = SENTIDO_IMU * (gx - sesgo_giro)
                roll_acel = SENTIDO_IMU * atan2_grados(ay, az)
                roll = FILTRO_ALFA * (roll + tasa_roll * dt) + (1 - FILTRO_ALFA) * roll_acel
                errores_imu = 0
            except OSError:
                errores_imu += 1
                if errores_imu > 20:
                    imu_ok = False
                    print("⚠️ MPU6050 dejó de responder: alerones al centro sin estabilizar")

        # 6.1 Comunicacion: detecta si el maestro sigue escribiendo
        sin_datos = time.ticks_diff(ahora, t_ultima_escritura) > FAILSAFE_MS
        if en_failsafe and hubo_escritura and not sin_datos:
            en_failsafe = False
            if DEBUG:
                print("🔗 Enlace con el maestro establecido")
        elif not en_failsafe and sin_datos:
            en_failsafe = True
            if DEBUG:
                print("⚠️ FAILSAFE: sin datos I2C, motor apagado, timones al centro y alas niveladas")

        # 6.2 Leer comandos
        if en_failsafe:
            cabeceo, guinada, gas = CENTRO, CENTRO, 0
        else:
            cabeceo = memoria[REG_CABECEO]
            guinada = memoria[REG_GUINADA]
            gas = memoria[REG_GAS]

        # 6.2b Alabeo: estabilizado por el MPU6050 o directo
        #      (en failsafe se siguen nivelando las alas para planear recto)
        if imu_ok:
            if ROLL_NEUTRO or en_failsafe:
                objetivo_roll = 0
            else:
                objetivo_roll = (memoria[REG_ALABEO] - CENTRO) * ANGULO_MAX_ROLL / 90
            alabeo = estabilizar_roll(objetivo_roll, dt)
        else:
            alabeo = CENTRO if (ROLL_NEUTRO or en_failsafe) else memoria[REG_ALABEO]

        # 6.3 Motor siempre armado, con rampa suave
        objetivo = gas_a_pulso(gas)
        if objetivo > pulso_actual + RAMPA_GAS_US:
            pulso_actual += RAMPA_GAS_US
        elif objetivo < pulso_actual - RAMPA_GAS_US:
            pulso_actual -= RAMPA_GAS_US
        else:
            pulso_actual = objetivo
        set_pulse_us(pulso_actual)

        # 6.4 Superficies (solo si cambiaron, como en el codigo original)
        estado = (round(alabeo), cabeceo, guinada, gas)
        if estado != ultimo_estado:
            aplicar_superficies(alabeo, cabeceo, guinada)
            ultimo_estado = estado

        # 6.5 Monitoreo en consola (como maximo 4 veces por segundo)
        if DEBUG and time.ticks_diff(ahora, t_ultimo_print) > 250:
            t_ultimo_print = ahora
            print(f"--> Incl. {roll:+5.1f}° | Aleron {round(alabeo) - CENTRO:+d}° | "
                  f"Pitch {cabeceo - CENTRO:+d}° | Yaw {guinada - CENTRO:+d}° | "
                  f"Gas {min(gas, 100)}%{' | FAILSAFE' if en_failsafe else ''}")

        # Pequeña pausa para no saturar el procesador (bucle de ~200 Hz)
        time.sleep(0.005)

except KeyboardInterrupt:
    print("\nDeteniendo...")

finally:
    # Limpieza de pines al salir (tambien si ocurre cualquier error)
    set_pulse_us(ESC_MIN_US)
    try:
        pico_esclavo.deinit()
    except Exception:
        pass
    aplicar_superficies(CENTRO, CENTRO, CENTRO)
    time.sleep(0.5)  # tiempo fisico para que los servos lleguen al centro
    for pwm in servos.values():
        pwm.deinit()
    esc.deinit()
    print("Programa detenido de forma segura. Motor apagado y servos en el centro.")