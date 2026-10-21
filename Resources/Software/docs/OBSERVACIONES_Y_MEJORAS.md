# UAV 4G LTE · Observaciones técnicas y mejoras propuestas

> Resultado de la revisión de los códigos definitivos del repositorio. **Ningún código fue modificado**: aquí solo se documentan observaciones y caminos de mejora para la siguiente versión.

---

## 1. Lo que ya está bien resuelto

* **Separación de responsabilidades:** el Pico vuela el avión y la Orange Pi solo comunica. Si se cae la Orange Pi, el Pico decide solo.
* **Seguridad en dos capas:** retención de 1 s en `tesis1.py` y failsafe de 500 ms en `main1.py` (motor a 0, timones al centro, alas niveladas).
* **Mando por LTE cifrado:** Tailscale usa WireGuard, el mismo principio que el túnel VPN del SkyRiper Minotaur ucraniano (ver el [estado del arte](../Estado_del_arte_UAV_4G_LTE.pdf), sección 8).
* **Arranque seguro:** ESC al mínimo y superficies al centro antes de cualquier otra cosa; el Pico no obedece hasta la primera escritura I²C.
* **Gas seguro:** solo la mitad superior del joystick da gas; al soltarlo vuelve a 0.

---

## 2. Observaciones del código

| N° | Observación | Efecto | Propuesta |
| :---: | :--- | :--- | :--- |
| 1 | Con `ROLL_NEUTRO = True` el alabeo queda bloqueado en 0° y se gira solo con los timones | El estabilizador contrarresta la inclinación que el diedro intenta dar: giros planos, derrapados y de radio grande | Tras los primeros vuelos, usar `ROLL_NEUTRO = False`: el stick derecho pide hasta ±30° de inclinación y el MPU6050 la mantiene |
| 2 | El cabeceo no está estabilizado | En failsafe la profundidad queda a 90°; el planeo depende del trim y puede aparecer la oscilación fugoide | Añadir un amortiguador de cabeceo (término D con el giroscopio Y) o un nivel de cabeceo en failsafe |
| 3 | El motor está **siempre armado** | Gira en cuanto el gas es mayor que 0 y hay comunicación: riesgo para la mano en el lanzamiento | Secuencia de armado (por ejemplo, gas a 0 durante 2 s más un botón del joystick) o interruptor físico |
| 4 | No hay telemetría de vuelta (tierra ← avión) ni GPS | Solo se puede volar en línea de vista aunque el enlace sea 4G | Enviar por UDP la batería, la inclinación, la señal LTE y la posición GPS a la laptop |
| 5 | La latencia de Tailscale depende de la red móvil | Con NAT compartido (CGNAT), Tailscale puede pasar por sus servidores de retransmisión (DERP) y subir la latencia | Medir antes de volar con `tailscale ping <IP de la Orange Pi>` y revisar si dice *via DERP* |
| 6 | Los paquetes UDP no llevan número de secuencia | Un paquete viejo que llega tarde se aplica igual (efecto pequeño a 20 Hz) | Añadir un contador al texto (`seq,X1,Y1,X2,Y2`) y descartar los atrasados |
| 7 | Los sensores MQ de 5 V todavía no están en el código | Su salida analógica puede llegar a 5 V y el ADC del Pico admite **3,3 V máximo** | Divisor de tensión o conversor externo antes de GP26–GP28 |

> [!IMPORTANT]
> Para los primeros vuelos se mantiene la recomendación del informe: CG a 45 mm, sensores apagados y `ROLL_NEUTRO = True`. Las propuestas de esta tabla son para la versión 2 del código (actividad 10 del [cronograma](../../../Proyecto/Cronograma/README.md)).

---

## 3. Transmisión de vídeo (opcional, para una versión futura)

Si se agrega una cámara, el vídeo puede viajar por el **mismo túnel Tailscale** que ya usan los mandos. Opciones de menor a mayor integración:

| Opción | Qué es | Cuándo usarla |
| :--- | :--- | :--- |
| **VDO.Ninja** | Vídeo P2P por WebRTC desde el navegador, gratis y sin cuenta, hecho para baja latencia | Prueba rápida, por ejemplo con un celular a bordo |
| **Jitsi Meet** instalado por uno mismo | Alternativa abierta a Google Meet, sin pasar por servidores de terceros | Si varias personas deben ver el vídeo |
| **MediaMTX en la Orange Pi** ⭐ | Servidor de vídeo gratuito: toma la cámara (USB o CSI), la comprime en H.264 y la sirve por **WebRTC o SRT** | Opción recomendada: va directo por Tailscale, cifrada y sin depender de nadie |

Parámetros de partida para no saturar el enlace ni robar ancho de banda a los comandos: **640×480, 15–20 fps, 0,5–1 Mbit/s**, con compresión por hardware de la Orange Pi para dejar libre la CPU para `tesis1.py`.

**Referente en defensa:** Ucrania usa **Vezha**, un módulo de *streaming* integrado en el sistema Delta desde octubre de 2024, que reúne en tiempo real el vídeo de cientos de drones y se creó para dejar de depender de servicios de terceros ([Ministerio de Defensa de Ucrania](https://mod.gov.ua/en/news/kateryna-chernohorenko-the-battlefield-video-analysis-platform-known-as-vezha-is-now-accessible-within-the-delta-combat-system), [Militarnyi](https://militarnyi.com/en/news/vezha-streaming-module-is-now-available-in-delta-situational-awareness-system/)). Sus protocolos y enlaces no son públicos; MediaMTX sobre Tailscale es el equivalente civil y abierto.

---

## 4. Lecciones del estado del arte aplicadas al proyecto

1. **Software de vuelo maduro:** la industria construye sobre PX4 (Auterion OS) o ArduPilot. Hablar MAVLink permitiría usar QGroundControl o Mission Planner como estación terrena.
2. **El avión debe poder volar sin enlace:** el Corvo navega a estima sin datos y el Privet-82 hace tramos en silencio de radio. El siguiente paso natural del failsafe es un **retorno a casa** con GPS.
3. **Una SIM a bordo es visible para la red:** usar una línea registrada a nombre del proyecto y avisar al operador si se hacen vuelos frecuentes.
4. **Starlink no cabe en esta clase de avión** (≈1 kg de terminal frente a ≈1 kg de avión).
