# Archivos CAD y Planos

## DXF para CNC (`DXF/`)
DXF R12 en milímetros, escala 1:1. Revisa la escala al importar en tu programa de CAM.

| Archivo | Contenido | Material |
| :--- | :--- | :--- |
| `F9_tail_boom.dxf` | Un botalón F9 (525,7 × 28,5 / 13,9) | Contrachapado |
| `F9x2_W6.dxf` | Dos F9 y la unión central W6 (334,9 × 32,1, diedro 3,4°) en una placa de 525,7 × 109,2 | Contrachapado |
| `W1_W5.dxf` | Caras del ala W1 (abajo) y W5 (arriba) de una semiala; área 750,2 × 469,8 | Depron 5 mm (cortar 2 en espejo) |

Capas de `W1_W5.dxf`:

| Capa | Uso |
| :--- | :--- |
| `CORTE` | Contornos y hueco del servo de 40 × 35 |
| `ALERON` | Corte del alerón (313,3) |
| `MARCAS` | Franjas de los largueros W3/W4 y posición del botalón F9 (no cortar, solo marcar) |
| `DOBLEZ` | 2 líneas de doblez en W1 y 7 en W5 (no cortar) |

## Planos en PDF (`Planos/`)
| Archivo | Contenido |
| :--- | :--- |
| `Ala_Alapalap_corte_y_caras.pdf` | Corte de la raíz 1:1, caras W1/W5 en planta, ubicación de los botalones y montaje de la cola |
| `Ala_huecos_servos.pdf` | Huecos de los servos de alerón referidos al centro y a los vértices, corte con el SG90 montado |
| `Gondola_brochetas_ligas.pdf` | Perforaciones de las brochetas en F2, vista de arriba con las ligas y corte de la góndola |

Imprime los planos al 100 % (tamaño real) y comprueba con la regla de 50 mm de cada lámina.

## Plano original
Las medidas salen del plano A0 del **Alapalap** de Julius Perdana. Ese plano no se incluye aquí: descárgalo gratis en [paper-replika.com](https://paper-replika.com).
