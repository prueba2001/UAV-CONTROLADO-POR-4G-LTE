# -*- coding: utf-8 -*-
# UAV Alapalap 4S - genera todas las piezas y el ensamble en FreeCAD.
# Medidas: ArchivosCAD (DXF, planos PDF), Proyecto/Mecanica y visor3d del repo
# prueba2001/UAV-CONTROLADO-POR-4G-LTE. Cotas en mm.
#
# Ejes del ensamble:  X = hacia atras (0 = borde de ataque en la raiz)
#                     Y = envergadura (+ = semiala derecha)
#                     Z = arriba
#
# Uso:  freecad alapalap_freecad.py        (con interfaz: colores y vistas)
#       freecadcmd alapalap_freecad.py     (sin interfaz: solo geometria)

import math
import os
import FreeCAD as App
import Part
from FreeCAD import Vector as V

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_NAME = "Alapalap_4S"

# ---------------------------------------------------------------- parametros
D2R = math.pi / 180
TD = math.tan(3.4 * D2R)          # diedro por semiala: lo fija el borde superior de W6 (DXF)
SEMI = 750.0                      # semienvergadura
T_DEPRON = 5.0
T_F9 = 4.0                        # contrachapado de los botalones
T_W6 = 3.0                        # contrachapado de la union central (supuesto)


def chord(s):
    return 226.0 - 64.5 * s / SEMI


def le(s):
    return 2.24 * s / SEMI


# Corte de la raiz (plano 1:1), cuerda 226: [x desde el BA, z]
PROF = [(226, -5), (21.1, -5), (8.4, -3), (3, 0), (0, 3.5), (1.5, 8.5), (6, 13),
        (14, 18.5), (31, 24.5), (55, 27.2), (83, 27.1), (109, 24.4), (160, 15.2),
        (206, 4.5), (226, 0)]
PROF_N = [(x / 226.0, z / 226.0) for x, z in PROF]


def wpt(side, s, xz):
    """Punto del perfil normalizado (x/c, z/c) en la estacion s de la semiala."""
    c = chord(s)
    return V(le(s) + xz[0] * c, side * s, xz[1] * c + s * TD)


def wire_at(side, s, pts2d):
    return Part.makePolygon([wpt(side, s, p) for p in pts2d] + [wpt(side, s, pts2d[0])])


def loft(w1, w2):
    return Part.makeLoft([w1, w2], True, True)


def inner_profile(s):
    """Perfil interior (hueco) a 5 mm de la piel, en coordenadas normalizadas."""
    c = chord(s)
    pts = [V(x * c, 0, z * c) for x, z in PROF_N]
    f = Part.Face(Part.makePolygon(pts + [pts[0]]))
    off = f.makeOffset2D(-T_DEPRON, 2)          # 2 = esquinas en interseccion
    vs = [v.Point for v in off.Wires[0].OrderedVertexes]
    return [(p.x / c, p.z / c) for p in vs]


def prism_xy(pts_xy, z0=-200, z1=200):
    w = Part.makePolygon([V(x, y, z0) for x, y in pts_xy] + [V(pts_xy[0][0], pts_xy[0][1], z0)])
    return Part.Face(w).extrude(V(0, 0, z1 - z0))


def plate_xz(pts_xz, y_center, thick):
    """Placa con contorno en el plano X-Z, espesor en Y centrado en y_center."""
    y0 = y_center - thick / 2
    w = Part.makePolygon([V(x, y0, z) for x, z in pts_xz] + [V(pts_xz[0][0], y0, pts_xz[0][1])])
    return Part.Face(w).extrude(V(0, thick, 0))


def plate_yz(pts_yz, x0, thick):
    w = Part.makePolygon([V(x0, y, z) for y, z in pts_yz] + [V(x0, pts_yz[0][0], pts_yz[0][1])])
    return Part.Face(w).extrude(V(thick, 0, 0))


def box(lx, ly, lz, cx, cy, cz):
    return Part.makeBox(lx, ly, lz, V(cx - lx / 2, cy - ly / 2, cz - lz / 2))


def cyl_y(r, length, cx, cy, cz):
    return Part.makeCylinder(r, length, V(cx, cy - length / 2, cz), V(0, 1, 0))


# ---------------------------------------------------------------- documento
if DOC_NAME in App.listDocuments():
    App.closeDocument(DOC_NAME)
doc = App.newDocument(DOC_NAME)

COLORS = {}       # nombre de objeto -> (r, g, b, transparencia)


def part_container(name, label):
    p = doc.addObject("App::Part", name)
    p.Label = label
    return p


def add(container, name, label, shape, color, transp=0):
    o = doc.addObject("Part::Feature", name)
    o.Label = label
    o.Shape = shape.removeSplitter() if shape.ShapeType != "Compound" else shape
    container.addObject(o)
    COLORS[o.Name] = (color, transp)
    return o


C_FOAM = (0.91, 0.90, 0.86)
C_SURF = (0.37, 0.61, 0.84)
C_SPAR = (0.88, 0.54, 0.42)
C_PLY = (0.77, 0.56, 0.31)
C_POD = (0.83, 0.82, 0.78)
C_SERVO = (0.20, 0.45, 0.77)
C_DARK = (0.20, 0.22, 0.23)
C_METAL = (0.60, 0.63, 0.64)
C_PCB = (0.18, 0.48, 0.28)
C_PICO = (0.25, 0.64, 0.37)
C_BAT = (0.17, 0.42, 0.56)
C_CG = (0.79, 0.34, 0.12)
C_BAMBOO = (0.85, 0.72, 0.45)

ens = part_container("Ensamble", "UAV Alapalap 4S")
g_ala = part_container("Ala", "Ala (W1-W6, alerones)")
g_bot = part_container("Botalones", "Botalones F9")
g_cola = part_container("Cola", "Cola (S1-S4)")
g_gon = part_container("Gondola", "Gondola (F1, F2, tapas)")
g_ele = part_container("Electronica", "Electronica")
g_srv = part_container("Servos", "Servos SG90")
g_pro = part_container("Propulsion", "Motor y helice")
g_ref = part_container("Referencias", "Referencias (CG)")
for g in (g_ala, g_bot, g_cola, g_gon, g_ele, g_srv, g_pro, g_ref):
    ens.addObject(g)

# ---------------------------------------------------------------- ala
INNER_ROOT = inner_profile(0)
INNER_TIP = inner_profile(SEMI)
# linea que separa W1 (abajo, con el frente doblado) de W5 (arriba, envuelve el BA)
# (pasa por encima de la cara interior de W1 y baja al centro del borde de fuga romo)
LOWER_N = [(x / 226.0, z / 226.0) for x, z in
           ((-50, 1.0), (180, 1.0), (226, -2.5), (300, -2.5), (300, -100), (-50, -100))]


def ail_chord(s):
    return 50.1 + (40.0 - 50.1) * (s - 437.0) / 313.0


def hinge_x(s):
    return le(s) + chord(s) - ail_chord(s)


W2_BY_SIDE = {}
for side, sfx, txt in ((1, "D", "derecha"), (-1, "I", "izquierda")):
    outer = loft(wire_at(side, 0, PROF_N), wire_at(side, SEMI, PROF_N))
    # el hueco interior va de la raiz hasta 5 mm antes de la punta (punta cerrada)
    inner_tip = [(x, z) for x, z in inner_profile(SEMI - T_DEPRON)]
    inner = loft(wire_at(side, -1, INNER_ROOT), wire_at(side, SEMI - T_DEPRON, inner_tip))
    skin = outer.cut(inner)

    lower_tool = loft(wire_at(side, -2, LOWER_N), wire_at(side, SEMI + 2, LOWER_N))

    # alerones: todo lo que queda detras de la bisagra entre s = 437 y la punta
    ys = [437.0, SEMI + 10]
    ail_tool = prism_xy([(hinge_x(ys[0]), side * ys[0]), (hinge_x(ys[1]), side * ys[1]),
                         (400, side * ys[1]), (400, side * ys[0])])

    # hueco del servo 40 x 35 en W1, girado 4,9 deg paralelo a W3
    s_srv = 472.6
    x_srv = le(s_srv) + 92.7
    z_bot = -5 * chord(s_srv) / 226 + s_srv * TD
    hole = box(35, 40, 20, x_srv, side * s_srv, z_bot)
    hole.rotate(V(x_srv, side * s_srv, z_bot), V(0, 0, 1), side * 4.9)

    w1 = skin.common(lower_tool).cut(ail_tool).cut(hole)
    w5 = skin.cut(lower_tool).cut(ail_tool)
    ail = skin.common(ail_tool)

    add(g_ala, "W1_" + sfx, "W1 cara inferior " + txt, w1, C_FOAM, 55)
    add(g_ala, "W5_" + sfx, "W5 cara superior " + txt, w5, C_FOAM, 55)
    add(g_ala, "Aleron_" + sfx, "Aleron " + txt + " (313,3 x 50,1-40)", ail, C_SURF)

    # largueros W4 (5 x 22,3) y W3 (5 x 12,4): recortados al hueco interior
    for nm, f_root, f_tip in (("W4", 67.5, 43.5), ("W3", 150.4, 89.0)):
        pts = [(le(0) + f_root, 0), (le(0) + f_root + 5, 0),
               (le(SEMI) + f_tip + 5, side * SEMI), (le(SEMI) + f_tip, side * SEMI)]
        spar = prism_xy(pts).common(inner)
        add(g_ala, nm + "_" + sfx, "Larguero " + nm + " " + txt, spar, C_SPAR)

    # W2: formador del perfil en la raiz (base plana desde el doblez 2 hasta 19,8 del BF)
    y0 = 0 if side > 0 else -T_DEPRON
    slab = Part.makeBox(206.2 - 21.1, T_DEPRON, 200, V(21.1, y0, -100))
    w2 = inner.common(slab)
    W2_BY_SIDE[side] = (w2, sfx, txt)

# W6: union central de contrachapado (contorno del DXF F9x2_W6), detras de W4
W6_PTS = [(1.2, 32.09), (167.48, 22.16), (333.75, 32.09), (334.95, 12.34), (167.48, 0.0), (0.0, 12.34)]
w6 = plate_yz([(y - 167.48, z) for y, z in W6_PTS], le(0) + 67.5 + 5, T_W6)
add(g_ala, "W6", "W6 union central (contrachapado)", w6, C_PLY)

# W2 ranurado para los largueros y W6
for side, (w2, sfx, txt) in W2_BY_SIDE.items():
    for nm in ("W4_", "W3_"):
        w2 = w2.cut(doc.getObject(nm + sfx).Shape)
    w2 = w2.cut(w6)
    add(g_ala, "W2_" + sfx, "W2 formador raiz " + txt, w2, C_SPAR)

# ---------------------------------------------------------------- botalones F9
BT = 151 * TD - 5 * chord(151) / 226          # cara inferior del ala en el canto interior del botalon
F9_X0, F9_X1 = 53.0, 578.7
for side, sfx, txt in ((1, "D", "derecho"), (-1, "I", "izquierdo")):
    f9 = plate_xz([(F9_X0, BT), (F9_X1, BT), (F9_X1, BT - 13.9), (F9_X0, BT - 28.5)], side * 153, T_F9)
    add(g_bot, "F9_" + sfx, "F9 botalon " + txt + " (525,7 x 28,5/13,9)", f9, C_PLY)

# ---------------------------------------------------------------- cola
S1Z = BT
add(g_cola, "S1", "S1 estabilizador (320 x 100)",
    Part.makeBox(100, 320, T_DEPRON, V(F9_X1 - 100, -160, S1Z)), C_FOAM)
add(g_cola, "S3", "S3 profundidad (316 x 24)",
    Part.makeBox(24, 316, T_DEPRON, V(F9_X1, -158, S1Z)), C_SURF)
for side, sfx, txt in ((1, "D", "derecha"), (-1, "I", "izquierda")):
    yc = side * 162.5
    fin = plate_xz([(478.7, S1Z), (578.7, S1Z), (578.7, S1Z + 125), (538.7, S1Z + 125)], yc, T_DEPRON)
    add(g_cola, "S2_" + sfx, "S2 deriva " + txt + " (forma deducida)", fin, C_FOAM)
    rud = Part.makeBox(25, T_DEPRON, 125, V(F9_X1, yc - T_DEPRON / 2, S1Z))
    add(g_cola, "S4_" + sfx, "S4 timon " + txt + " (deducido)", rud, C_SURF)

# ---------------------------------------------------------------- gondola
# Costado F2 (plano Gondola_brochetas_ligas.pdf): [desde la nariz, desde el canto inferior]
F2_PTS = [(0.0, 16.6), (38.8, 60.3), (80.8, 84.0), (143.2, 95.6), (341.1, 95.6),
          (341.1, 73.4), (579.6, 73.0), (579.3, 34.2), (458.3, 0.0), (37.4, 0.0)]
NOSE_X = -341.1                         # el escalon de la silla toca el BA
POD_Z0 = -5.0 - 73.4                    # la silla (73,4) recibe la cara inferior del ala
W_OUT, W_IN = 124.0, 113.6
T_F2 = (W_OUT - W_IN) / 2


def pod(xz):
    return (NOSE_X + xz[0], POD_Z0 + xz[1])


SKEWERS = [cyl_y(1.5, 155, *(lambda p: (p[0], 0, p[1]))(pod((xn, 65.4)))) for xn in (353.1, 549.6)]
for side, sfx, txt in ((1, "D", "derecho"), (-1, "I", "izquierdo")):
    f2 = plate_xz([pod(p) for p in F2_PTS], side * (W_IN / 2 + T_F2 / 2), T_F2)
    for sk in SKEWERS:
        f2 = f2.cut(sk)
    add(g_gon, "F2_" + sfx, "F2 costado " + txt + " (579,6)", f2, C_POD)


# Envolvente de Depron: contorno F2 menos su offset de 5 mm, sin la silla (la cubre el ala)
# ni el final (lo cierra el soporte del motor); se parte en piezas sin solapes.
_f2 = Part.Face(Part.makePolygon([V(x, 0, z) for x, z in F2_PTS] + [V(*((F2_PTS[0][0], 0, F2_PTS[0][1])))]))
_ring = _f2.cut(_f2.makeOffset2D(-T_DEPRON, 2))
_ring.translate(V(NOSE_X, -W_IN / 2, POD_Z0))
shell = _ring.extrude(V(0, W_IN, 0))
shell = shell.cut(Part.makeBox(300, W_OUT, 60, V(NOSE_X + 341.1 - T_DEPRON, -W_OUT / 2, POD_Z0 + 73.4 - T_DEPRON - 1)))
shell = shell.cut(Part.makeBox(20, W_OUT, 200, V(NOSE_X + 579.6 - T_DEPRON, -W_OUT / 2, POD_Z0 - 10)))


def region(x0, x1, z0, z1):
    return shell.common(Part.makeBox(x1 - x0, W_OUT, z1 - z0, V(NOSE_X + x0, -W_OUT / 2, POD_Z0 + z0)))


add(g_gon, "Nariz", "Nariz (deducida)", region(-10, 80, -10, 120), C_POD)
add(g_gon, "Tapa", "Tapa de la gondola (deducida)", region(80, 400, 50, 120), C_POD)
add(g_gon, "F1", "F1 fondo", region(80, 458.3, -10, 50), C_POD)
add(g_gon, "Fondo_trasero", "Fondo trasero (deducido)", region(458.3, 600, -10, 50), C_POD)

# Brochetas de las ligas: 12 tras el escalon y 30 antes del final, 65,4 sobre el canto inferior
for nm, xn in (("Brocheta_del", 353.1), ("Brocheta_tras", 549.6)):
    x, z = pod((xn, 65.4))
    add(g_gon, nm, nm.replace("_", " ") + " (bambu 3 x 155)", cyl_y(1.5, 155, x, 0, z), C_BAMBOO)

# Soporte del motor (deducido): contrachapado al final de la gondola
X_END = NOSE_X + 579.6
add(g_gon, "Soporte_motor", "Soporte del motor (deducido)",
    Part.makeBox(4, W_OUT, 70, V(X_END, -W_OUT / 2, POD_Z0 + 30)), C_PLY)

# ---------------------------------------------------------------- propulsion
MOT_X0, MOT_Z = X_END + 4, 4.0
motor = Part.makeCylinder(14, 30, V(MOT_X0, 0, MOT_Z), V(1, 0, 0))
add(g_pro, "Motor", "Motor brushless 4S 920 kV", motor, C_METAL)
PROP_X = MOT_X0 + 34
blades = []
for sgn in (1, -1):
    b = box(2.5, 112, 17, PROP_X, sgn * 58, MOT_Z)
    b.rotate(V(PROP_X, 0, MOT_Z), V(0, 1, 0), sgn * 16)
    blades.append(b)
hub = Part.makeCylinder(8, 8, V(PROP_X - 4, 0, MOT_Z), V(1, 0, 0))
spinner = Part.makeCone(12, 0, 26, V(PROP_X + 4, 0, MOT_Z), V(1, 0, 0))
add(g_pro, "Helice", "Helice propulsora 9 pulg. (supuesta)", hub.fuse(blades + [spinner]), C_DARK)

# ---------------------------------------------------------------- servos SG90
def sg90(name, label, cx, cy, cz, lx, ly, lz, rot=0):
    s = box(lx, ly, lz, cx, cy, cz)
    if rot:
        s.rotate(V(cx, cy, cz), V(0, 0, 1), rot)
    add(g_srv, name, label, s, C_SERVO)


for side, sfx, txt in ((1, "D", "derecho"), (-1, "I", "izquierdo")):
    s = 472.6
    zb = -5 * chord(s) / 226 + s * TD
    # acostado de lado: 12,2 de alto, base a ras de la cara inferior
    sg90("Servo_aleron_" + sfx, "SG90 aleron " + txt, le(s) + 92.7, side * s, zb + 6.1, 23, 22.7, 12.2, side * 4.9)
    sg90("Servo_timon_" + sfx, "SG90 timon " + txt + " (orientativo)", 545, side * 140, S1Z + 5 + 11.35, 23, 12.2, 22.7)
sg90("Servo_prof", "SG90 profundidad (orientativo)", 555, 0, S1Z + 5 + 11.35, 12.2, 23, 22.7)

# ---------------------------------------------------------------- electronica (orientativa)
ZF = POD_Z0 + T_DEPRON                  # piso interior


def ebox(name, label, lx, ly, lz, x0, y, z0, color):
    add(g_ele, name, label, Part.makeBox(lx, ly, lz, V(x0, y - ly / 2, z0)), color)


ebox("Bateria", "LiPo 4S 3300 mAh (mover hasta CG = 45)", 135, 43, 33, -240, 0, ZF, C_BAT)
ebox("OrangePi", "Orange Pi 4 Pro", 89, 56, 4, -95, 0, ZF + 38, C_PCB)
ebox("Disipador", "Disipador Orange Pi", 40, 40, 10, -70, 0, ZF + 42, C_DARK)
ebox("MPU6050", "MPU6050 (cerca del CG)", 21, 16, 2, 35, 0, ZF, (0.42, 0.25, 0.63))
ebox("Pico_control", "RPi Pico control (I2C 0x08)", 51, 21, 3, 60, -18, ZF, C_PICO)
ebox("Pico_MQ", "RPi Pico sensores MQ", 51, 21, 3, 60, 18, ZF, C_PICO)
ebox("Modem_LTE", "Modem LTE", 62, 28, 10, 70, 0, ZF + 25, (0.93, 0.93, 0.93))
ebox("ESC", "ESC", 60, 25, 10, -90, -28, ZF, C_DARK)
ebox("UBEC", "UBEC 5 V", 35, 18, 8, -90, 28, ZF, C_DARK)

# ---------------------------------------------------------------- referencias
add(g_ref, "CG", "Centro de gravedad (45 tras el BA)", Part.makeSphere(7, V(45, 0, 45)), C_CG)

doc.recompute()

# ---------------------------------------------------------------- comprobaciones
bad = [o.Label for o in doc.Objects if o.TypeId == "Part::Feature" and (o.Shape.isNull() or not o.Shape.isValid() or o.Shape.Volume <= 0)]
print("Piezas:", sum(1 for o in doc.Objects if o.TypeId == "Part::Feature"))
print("Piezas con problemas:", bad or "ninguna")

# ---------------------------------------------------------------- colores y vistas (solo con interfaz)
if App.GuiUp:
    import FreeCADGui as Gui
    for name, (col, tr) in COLORS.items():
        vo = doc.getObject(name).ViewObject
        vo.ShapeColor = col
        vo.Transparency = tr
    Gui.SendMsgToActiveView("ViewFit")
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")

doc.saveAs(os.path.join(OUT_DIR, DOC_NAME + ".FCStd"))

# STEP del ensamble completo y STL de cada pieza (para imprimir o pasar a otro CAD)
import Import
feats = [o for o in doc.Objects if o.TypeId == "Part::Feature"]
Import.export([ens], os.path.join(OUT_DIR, DOC_NAME + ".step"))
stl_dir = os.path.join(OUT_DIR, "STL")
os.makedirs(stl_dir, exist_ok=True)
import Mesh
for o in feats:
    Mesh.export([o], os.path.join(stl_dir, o.Name + ".stl"))
print("Guardado en", OUT_DIR)
