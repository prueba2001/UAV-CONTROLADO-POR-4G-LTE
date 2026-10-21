# UAV Alapalap · Puesta en marcha

1. **Pico:** instala MicroPython ≥ 1.26, abre `firmware/pico_control/main1.py` en Thonny y guárdalo en la Pico como `main.py`. Cierra Thonny antes de usar otro programa con el mismo puerto (si no, aparece *Device is busy*).
2. **Orange Pi:**
   ```bash
   pip3 install smbus2
   sudo i2cdetect -y 2        # debe aparecer 08 (la Pico)
   tailscale ip -4            # anota esta IP para Transmisor1.py
   python3 tesis1.py
   ```
3. **Arduino UNO:** carga `firmware/Joystick1/Joystick1.ino` desde Arduino IDE. El monitor serial (9600) debe mostrar `X1,Y1,X2,Y2`. Ciérralo antes de abrir el transmisor.
4. **Laptop:**
   ```bash
   pip3 install pyserial
   ls -l /dev/serial/by-id/   # muestra en qué puerto está el Arduino (ttyACM0, ttyACM1…)
   python3 Transmisor1.py
   ```

## Comunicación
| Tramo | Medio | Formato |
| :--- | :--- | :--- |
| Arduino → laptop | USB serial 9600 | `X1,Y1,X2,Y2` (0–1023) cada 50 ms |
| Laptop → Orange Pi | UDP 5005 por Tailscale | mismo texto |
| Orange Pi → Pico | I2C bus 2, 0x08, registro 0 | `[alabeo, cabeceo, guiñada, gas]` |

## Límites de seguridad
* Quita la hélice para cualquier prueba en banco y para calibrar el ESC.
* Masa común entre Pico, Orange Pi, ESC y la fuente de los servos.
* Failsafe del Pico: 500 ms sin I2C → motor a 0, timones al centro, alas niveladas.
* Retención de la Orange Pi: 1 s repitiendo el último comando si no llega UDP.

## Antes de volar
* Mide la latencia del enlace desde la laptop: `tailscale ping <IP de Tailscale de la Orange Pi>`. Si responde *via DERP*, el tráfico pasa por un servidor de retransmisión y la latencia será mayor.
* Prueba el failsafe en tierra (sin hélice): corta la red y comprueba que a los ≈ 1,5 s el motor baja a 0 y las superficies vuelven al centro ([diagrama 10](../Imagenes/diagramas/10_linea_tiempo_failsafe.png)).
* Diagramas y mejoras propuestas: [`DIAGRAMAS.md`](DIAGRAMAS.md) · [`OBSERVACIONES_Y_MEJORAS.md`](OBSERVACIONES_Y_MEJORAS.md).

