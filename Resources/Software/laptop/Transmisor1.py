# Archivo: Transmisor.py  (corre en la laptop)
# Envia por UDP (VPN Tailscale) los valores de los joysticks al Orange Pi 4 Pro.
import socket

# Importamos tu función desde el otro archivo
from lector_serial1 import leer_joysticks

# IP de Tailscale del Orange Pi 4 Pro (en la Orange Pi: tailscale ip -4)
IP_RECEPTOR = '100.94.73.36'
PUERTO_UDP = 5005

# Paquete de seguridad al detener: todo al centro.
# Con Y1 en el centro el gas es 0 (tesis.py solo da gas en la mitad superior).
MENSAJE_NEUTRO = "512,512,512,512"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("Iniciando módulo transmisor UDP...")
print(f"Destino: {IP_RECEPTOR}:{PUERTO_UDP}\n")

try:
    # Este 'for' llama a tu código. Cada vez que tu código hace un 'yield',
    # recibimos los 4 valores aquí en tiempo real.
    for x1, y1, x2, y2 in leer_joysticks():
        # Empaquetamos para envío
        mensaje = f"{x1},{y1},{x2},{y2}"

        # Disparamos por Tailscale
        sock.sendto(mensaje.encode('utf-8'), (IP_RECEPTOR, PUERTO_UDP))

except KeyboardInterrupt:
    print("\nTransmisión detenida principal.")
finally:
    # Antes de cerrar mandamos varias veces el paquete neutro (motor a 0,
    # superficies al centro) por si alguno se pierde en la red
    try:
        for _ in range(5):
            sock.sendto(MENSAJE_NEUTRO.encode('utf-8'), (IP_RECEPTOR, PUERTO_UDP))
        print("Paquete neutro enviado: motor a 0 y superficies al centro.")
    except OSError:
        pass
    sock.close()