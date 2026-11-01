# UAV Alapalap 4S — Modelo en FreeCAD

Ensamble completo del UAV del repo [prueba2001/UAV-CONTROLADO-POR-4G-LTE](https://github.com/prueba2001/UAV-CONTROLADO-POR-4G-LTE), generado por script en FreeCAD 1.1. Cotas en mm.

## Archivos

| Archivo | Contenido |
| :--- | :--- |
| `Alapalap_4S.FCStd` | Ensamble con colores y piezas agrupadas (47 sólidos) |
| `Alapalap_4S.step` | Ensamble completo para otros CAD |
| `STL/` | Un STL por pieza |
| `alapalap_freecad.py` | Script que genera todo |

Regenerar después de cambiar una medida:

```bash
freecadcmd alapalap_freecad.py     # solo geometría
freecad alapalap_freecad.py        # con interfaz: también aplica colores
```

## Ejes del ensamble

* **X**: hacia atrás; 0 en el borde de ataque de la raíz.
* **Y**: envergadura; + es la semiala derecha.
* **Z**: arriba; 0 en la cara interior de W1 en la raíz.

## Fuentes de las medidas

| Pieza | Fuente |
| :--- | :--- |
| Perfil del ala, cuerdas, largueros W3/W4, alerones, huecos de servo | Plano `Ala_Alapalap_corte_y_caras.pdf`, `Ala_huecos_servos.pdf` y `visor3d/alapalap_3d.html` |
| W6 (unión central) | Contorno exacto de `DXF/F9x2_W6.dxf` |
| Botalones F9 | `DXF/F9_tail_boom.dxf` y `Proyecto/Mecanica/README.md` (306 entre centros, desde 53 tras el BA) |
| Costado F2 de la góndola | Vectores del plano `Gondola_brochetas_ligas.pdf` (silla, escalón a 341,1, ancho 124 / 113,6) |
| Brochetas | Mismo plano: 353,1 y 549,6 desde la nariz, a 65,4 del canto inferior, Ø3 × 155 |
| Cola S1/S3 | Plano A0 vía `Proyecto/Mecanica/README.md` |

## Decisión importante: diedro de 3,4° por semiala

El visor 3D del repo usa **1,7° por semiala** (3,4° en total), pero con ese ángulo la pieza W6 del DXF no cabe dentro del ala:

* El borde superior de W6 baja 9,93 mm en 167,5 mm → atan(9,93 / 167,5) = **3,4° por lado**.
* El centro de W6 (22,16 de alto) coincide con la altura interior de la raíz en el larguero W4, y sus puntas coinciden con el ala solo si el diedro es de 3,4° por lado.

Como W6 es la pieza física que fija el ángulo al pegar las semialas, el modelo usa **3,4° por semiala** (`TD` en el script).

**Pendiente:** corregir el visor 3D o el README para que digan lo mismo.

## Piezas deducidas (no salen de los planos)

En el árbol de FreeCAD llevan "(deducida)", "(supuesta)" u "(orientativo)" en el nombre.

* Nariz, tapa y fondo trasero de la góndola: siguen el contorno de F2 con Depron de 5 mm.
* Soporte del motor: contrachapado de 4 mm al final de la góndola.
* Forma de las derivas S2 y de los timones S4 (≈125 mm de alto).
* Espesor de W6: se supuso 3 mm.
* Hélice de 9" y posición del motor.
* Posición de toda la electrónica y de los servos de cola.

## Interferencias que quedan

Se revisaron todas las parejas de piezas. Solo quedan dos interferencias:

| Piezas | Volumen | Causa |
| :--- | ---: | :--- |
| W6 ↔ W5 (cada lado) | ≈ 460 mm³ | Las puntas de W6 sobresalen ≈1,4 mm. El modelo mantiene la piel con 5 mm de grosor en toda el ala, en vez de escalarla con la cuerda. En la realidad W5 se adapta al pegarla. |
| SG90 de alerón ↔ W5 (cada lado) | ≈ 42 mm³ | Una esquina del servo roza la piel superior. El plano ya dice que el hueco es muy justo (17–22 mm de alto por dentro). |

## Por hacer

* Ajustar las piezas deducidas con las medidas reales.
* Calcular el CG con las masas reales y fijar la posición de la batería (objetivo: 45 mm tras el BA, rango 42–50).
* Planos 2D con TechDraw.
* Subir esta carpeta al repo (por ejemplo, a `ArchivosCAD/FreeCAD/`).
