# UAV Alapalap 4S — Software y Firmware

> Código de los cuatro equipos del sistema: Arduino UNO (joysticks), laptop (transmisor), Orange Pi 4 Pro (receptor a bordo) y RPi Pico (controlador de vuelo).

---

## 1. Contenido

```text
Software/
├── firmware/
│   ├── pico_control/main1.py      ← RPi Pico · MicroPython ≥ 1.26
│   └── Joystick1/Joystick1.ino    ← Arduino UNO
├── orangepi/tesis1.py             ← Orange Pi 4 Pro · Python 3 + smbus2
├── laptop/
│   ├── Transmisor1.py             ← Python 3 (socket)
│   └── lector_serial1.py          ← Python 3 + pyserial
├── visor3d/alapalap_3d.html       ← Modelo 3D (three.js r128)
├── Imagenes/                      ← Diagramas y láminas
│   ├── diagramas/                 ← 10 diagramas + Gantt (PNG y SVG)
│   └── estado_del_arte/           ← Figuras del estado del arte
├── docs/SETUP.md                  ← Puesta en marcha rápida
├── docs/DIAGRAMAS.md              ← Explicación de los 10 diagramas + Gantt
├── docs/OBSERVACIONES_Y_MEJORAS.md ← Revisión del código y mejoras propuestas
└── Estado_del_arte_UAV_4G_LTE.pdf ← Estado del arte (también en .docx)
```

| Archivo | Corre en | Librerías | Función |
| :--- | :--- | :--- | :--- |
| `Joystick1.ino` | Arduino UNO | ninguna | Lee A0–A3 y envía `X1,Y1,X2,Y2` cada 50 ms |
| `lector_serial1.py` | Laptop | `serial`, `time` | Abre el puerto serial y entrega cada lectura válida con `yield` |
| `Transmisor1.py` | Laptop | `socket` | Envía cada lectura por UDP a la Orange Pi (Tailscale) |
| `tesis1.py` | Orange Pi | `socket`, `smbus2` | Recibe UDP, convierte a grados y gas, escribe 4 bytes al Pico por I2C |
| `main1.py` | RPi Pico | `sys`, `time`, `machine` | Esclavo I2C 0x08: 5 servos, ESC, MPU6050, PID de alabeo, failsafe |

<p align="center">
  <img src="Imagenes/grafico_flujo.png" alt="Cadena de control" width="820">
</p>

---

## 2. Firmware del RPi Pico (`main1.py`)

### 2.1. Opciones
| Variable | Valor | Efecto |
| :--- | :---: | :--- |
| `CALIBRAR_ESC` | `False` | `True` solo la primera vez, con la hélice quitada y la consola USB abierta |
| `DEBUG` | `True` | Imprime el estado 4 veces por segundo; `False` en vuelo |
| `ROLL_NEUTRO` | `True` | Ignora el alabeo del piloto (recomendado en los primeros vuelos) |
| `ESTABILIZAR_ROLL` | `True` | El MPU6050 mantiene las alas niveladas |

Si `ROLL_NEUTRO = True` y `ESTABILIZAR_ROLL = False`, los alerones quedan fijos al centro y el avión se gira solo con los timones.

### 2.2. Límites y ajustes
* Deflexión máxima: alabeo ±25°, cabeceo ±25°, guiñada ±30° alrededor de 90°.
* `SERVOS_CFG`: cada servo tiene `sentido` (1 o −1) y `trim`. El alerón derecho va con −1 para moverse opuesto al izquierdo. Si una superficie se mueve al revés, cambia su signo.
* ESC de 1000 a 2000 µs, con rampa de 10 µs por ciclo (0 → 100 % en 0,5 s). El motor está **siempre armado**: gira en cuanto el gas es mayor que 0.
* PID de alabeo: `KP_ROLL = 0.8`, `KD_ROLL = 0.05`, `KI_ROLL = 0.0`; filtro complementario con `FILTRO_ALFA = 0.995`.
* Failsafe: `FAILSAFE_MS = 500`. Para pruebas manuales con `i2cset` se puede subir a 5000.

### 2.3. Bucle principal (~200 Hz)
1. Lee el MPU6050 y estima la inclinación (giroscopio + acelerómetro).
2. Revisa si llegó una escritura I2C en los últimos 500 ms (failsafe).
3. Lee cabeceo, guiñada y gas de la memoria I2C.
4. Calcula el alabeo: PID hacia 0° (o hacia el ángulo pedido si `ROLL_NEUTRO = False`).
5. Aplica el gas con rampa y mueve los servos solo si cambió algo.

El Pico atiende el I2C por hardware con interrupciones, así que recibe órdenes y lee el MPU6050 al mismo tiempo con un solo núcleo.

---

## 3. Receptor a bordo (`tesis1.py`)

* Escucha UDP en `0.0.0.0:5005` con espera de 50 ms por paquete.
* Asignación modo 2: `X1` guiñada, `Y1` gas, `X2` alabeo, `Y2` cabeceo. Cada eje tiene su `INVERTIR_…`.
* Zona muerta de ±4°; el gas solo usa la mitad superior de `Y1` (al soltar el joystick el gas es 0).
* Retención de 1 s ante pérdida de paquetes; después deja de escribir y el Pico entra solo en failsafe.
* Al salir escribe `[90, 90, 90, 0]`.

---

## 4. Estación en tierra (`Transmisor1.py` + `lector_serial1.py`)

* `IP_RECEPTOR` debe ser la IP de Tailscale de la Orange Pi (`tailscale ip -4` en la Orange Pi).
* `PUERTO` en `lector_serial1.py`: `/dev/ttyACM0` en Linux, `COMx` en Windows. Si el Arduino aparece como otro puerto, usa la ruta fija de `/dev/serial/by-id/`.
* Los dos archivos deben estar en la misma carpeta (`Transmisor1.py` importa `leer_joysticks` de `lector_serial1`).

---

## 5. Visor 3D (`visor3d/alapalap_3d.html`)

Página única con three.js: girar, zoom, vistas (3/4, arriba, abajo, frente, lado), capas, modo transparente, mandos que mueven alerones, profundidad, timones y hélice, y los 4 bytes I2C equivalentes. La góndola, las derivas y la electrónica son aproximadas; el ala, los botalones y la cola salen del plano A0.

**[▶ Abrir el visor 3D interactivo en el navegador](https://claude.ai/artifact/1FfqrhXRi7ZsbawRA6YPTv)** — la misma página publicada en línea, sin descargar nada.

---

## 6. Puesta en marcha

Ver [`docs/SETUP.md`](docs/SETUP.md).

---

## 7. Diagramas del código

Los flujos de cada programa están dibujados a partir de estos mismos archivos. Detalle en [`docs/DIAGRAMAS.md`](docs/DIAGRAMAS.md).

| Programa | Diagrama |
| :--- | :--- |
| `Joystick1.ino`, `lector_serial1.py`, `Transmisor1.py` | [06 · Flujo del código en tierra](Imagenes/diagramas/06_flujo_codigo_tierra.png) |
| `tesis1.py` | [07 · Flujo de la Orange Pi](Imagenes/diagramas/07_flujo_tesis1_orangepi.png) |
| `main1.py` | [08 · Flujo del Pico](Imagenes/diagramas/08_flujo_main1_pico.png) · [09 · Lazo de alabeo](Imagenes/diagramas/09_lazo_control_alabeo.png) |
| Todos | [05 · Recorrido de un comando](Imagenes/diagramas/05_recorrido_comando.png) · [10 · Failsafe](Imagenes/diagramas/10_linea_tiempo_failsafe.png) |

<p align="center">
  <img src="Imagenes/diagramas/08_flujo_main1_pico.png" alt="Flujo de main1.py" width="820">
</p>

---

## 8. Observaciones y mejoras

Revisión de estos códigos (sin modificarlos) con propuestas para la versión 2: `ROLL_NEUTRO = False` para giros coordinados, amortiguador de cabeceo, armado seguro del motor, telemetría de retorno, medición de latencia de Tailscale y transmisión de vídeo con MediaMTX. Ver [`docs/OBSERVACIONES_Y_MEJORAS.md`](docs/OBSERVACIONES_Y_MEJORAS.md).

---

## 9. Estado del arte

[`Estado_del_arte_UAV_4G_LTE.pdf`](Estado_del_arte_UAV_4G_LTE.pdf) · versión editable [`.docx`](Estado_del_arte_UAV_4G_LTE.docx) · resumen en [`Proyecto/EstadoDelArte`](../../Proyecto/EstadoDelArte/README.md).

