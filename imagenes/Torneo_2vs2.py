"""
Torneo_2vs2.py  —  Torneo 2 VS 2 desde Cuartos
================================================
Bracket de eliminación directa para 8 EQUIPOS (parejas).
Cada equipo tiene dos jugadores mostrados en el mismo bloque.

Estructura:
  · Panel superior : bracket con 3 columnas por lado
                     (CUARTOS -> SEMIFINAL -> FINAL -> CAMPEON)
  · Panel inferior : 3er Puesto (izquierda) + Podio (derecha)

Geometría del bracket (posiciones X por lado):
  0 = CUARTOS     x = ±12.0   (N = 4 parejas por lado)
  1 = SEMIFINAL   x = ± 7.5   (N = 2)
  2 = FINAL       x = ± 3.0   (N = 1)
  Centro          x =   0.0   (Campeón, debajo de los finalistas)
"""

import re
import os
import copy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

# =====================================================================
#  EQUIPOS  —  lista de 8 pares  [jugador1, jugador2]
# =====================================================================
EQUIPOS = [
    ["J1-A",  "J1-B"],
    ["J2-A",  "J2-B"],
    ["J3-A",  "J3-B"],
    ["J4-A",  "J4-B"],
    ["J5-A",  "J5-B"],
    ["J6-A",  "J6-B"],
    ["J7-A",  "J7-B"],
    ["J8-A",  "J8-B"],
]

# =====================================================================
#  PALETA DE COLORES
# =====================================================================
C = {
    "bg":      "#0b0b1a",
    "azul":    ("#1a3d7a", "#4d9fff"),
    "rojo":    ("#7a1a1a", "#ff5555"),
    "win":     ("#1a5c2e", "#50e87a"),
    "final_w": ("#6b3a00", "#ffb347"),
    "champ":   ("#5c4500", "#ffd700"),
    "silver":  ("#353535", "#c0c0c0"),
    "bronze":  ("#4a2800", "#cd7f32"),
    "empty":   ("#0f0f20", "#252545"),
    "line":    "#3a3a6a",
    "sep":     "#2a2a50",
    "div1":    "#223366",   # divisor entre jugador 1 y 2 dentro del bloque
}

# =====================================================================
#  GEOMETRÍA
# =====================================================================

# Bloque doble: ancho y alto total que contiene AMBOS jugadores
BOX_W  = 3.2    # ancho
BOX_H1 = 0.72   # alto de cada sub-fila (jugador 1 / jugador 2)
BOX_H  = BOX_H1 * 2 + 0.08   # alto total del bloque (~1.52)
FS     = 22     # fuente para nombres

# Separación vertical entre parejas en cuartos
GAP_Y  = 2.6
N_SIDE = 4      # parejas por lado (4+4 = 8 equipos en total)

# Columnas X (cuartos, semi, final) por lado
XS_IZQ = [-12.0, -7.5, -3.0]
XS_DER = [ 12.0,  7.5,  3.0]

# Límites paneles
XLIM_TOP = (-16.5, 16.5)
YLIM_TOP = (-2.5, 13.5)
XLIM_BOT = (0.0, 36.0)
YLIM_BOT = (0.0, 12.0)

# Posiciones Y panel inferior
Y_HEAD = 9.9
Y_CONT = 7.2
Y_WIN  = 5.0
Y_LBL  = 4.0


# =====================================================================
#  ESTADO DEL TORNEO
# =====================================================================

def estado_inicial(equipos):
    """Devuelve el estado inicial para 8 equipos en cuartos."""
    # Cada elemento es una pareja [j1, j2] o None
    return {
        "wb": [
            list(equipos),      # ronda 0: 8 equipos (cuartos)
            [None] * 4,         # ronda 1: 4 equipos (semifinal)
            [None] * 2,         # ronda 2: 2 equipos (final)
            [None] * 1,         # ronda 3: 1 equipo  (campeón)
        ],
        "semifinal_losers": [None, None],
        "tercero": None,
        "cuarto":  None,
    }


# =====================================================================
#  HELPERS
# =====================================================================

def _oct_ys():
    """Y de los 4 slots de cuartos por lado (arriba → abajo)."""
    return [(N_SIDE - 1 - i) * GAP_Y for i in range(N_SIDE)]


def _get_y(ronda, slot, oct_ys):
    if ronda == 0:
        return oct_ys[slot]
    ya = _get_y(ronda - 1, 2 * slot,     oct_ys)
    yb = _get_y(ronda - 1, 2 * slot + 1, oct_ys)
    return (ya + yb) / 2


def _nombre_equipo(equipo):
    """Devuelve el nombre del equipo para mostrar en listas de texto."""
    if equipo is None:
        return "???"
    if isinstance(equipo, list):
        return f"{equipo[0]} & {equipo[1]}"
    return str(equipo)


# =====================================================================
#  PRIMITIVAS DE DIBUJO
# =====================================================================

def draw_box_duo(ax, cx, cy, equipo, estilo, w=BOX_W, h=BOX_H, h1=BOX_H1, fontsize=FS, z=3):
    """
    Dibuja un bloque doble (dos sub-filas) centrado en (cx, cy).
    La fila superior tiene al Jugador 1 y la inferior al Jugador 2.
    Una línea delgada separa los dos jugadores dentro del bloque.
    """
    es_vacio = (equipo is None)

    if es_vacio:
        fc, ec = C["empty"]
        alpha, ls = 0.55, "--"
        j1_txt = j2_txt = ""
    else:
        fc, ec = C[estilo]
        alpha, ls = 1.0, "solid"
        if isinstance(equipo, list):
            j1_txt, j2_txt = equipo[0], equipo[1]
        else:
            j1_txt, j2_txt = str(equipo), ""

    # Caja exterior redondeada
    ax.add_patch(FancyBboxPatch(
        (cx - w/2, cy - h/2), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.12",
        fc=fc, ec=ec, lw=2.0, ls=ls, alpha=alpha, zorder=z
    ))

    if not es_vacio:
        # Línea divisoria entre los dos jugadores
        yline = cy                   # centro del bloque = frontera
        ax.plot([cx - w/2 + 0.10, cx + w/2 - 0.10], [yline, yline],
                color=C["div1"], lw=0.9, ls="-", alpha=0.7, zorder=z + 1)

        # Sub-fila superior: Jugador 1
        y1 = cy + h1 / 2 + 0.04     # centro de la fila superior
        # Etiqueta "J1" pequeña a la izquierda
        ax.text(cx - w/2 + 0.14, y1, "①",
                ha="left", va="center",
                fontsize=fontsize - 9, color="#a0c8ff", fontweight="bold", zorder=z + 2)
        ax.text(cx + 0.1, y1, j1_txt,
                ha="center", va="center",
                fontsize=fontsize - 2, color="#ffffff", fontweight="bold",
                zorder=z + 2, clip_on=True)

        # Sub-fila inferior: Jugador 2
        y2 = cy - h1 / 2 - 0.04
        ax.text(cx - w/2 + 0.14, y2, "②",
                ha="left", va="center",
                fontsize=fontsize - 9, color="#ffb0b0", fontweight="bold", zorder=z + 2)
        ax.text(cx + 0.1, y2, j2_txt,
                ha="center", va="center",
                fontsize=fontsize - 2, color="#ffffff", fontweight="bold",
                zorder=z + 2, clip_on=True)


def draw_box_champ_duo(ax, cx, cy, equipo, w=BOX_W * 1.4, h=None, fontsize=FS + 2):
    """Caja especial del campeón con brillo dorado y diseño 2vs2."""
    h = h or BOX_H * 1.5
    h1_champ = (h - 0.10) / 2

    if equipo is None:
        draw_box_duo(ax, cx, cy, None, "empty", w=w, h=h, fontsize=fontsize, z=4)
        return

    fc, ec = C["champ"]
    # Capas de brillo
    for i in range(4, 0, -1):
        gw = w + i * 0.30
        gh = h + i * 0.20
        ax.add_patch(FancyBboxPatch(
            (cx - gw/2, cy - gh/2), gw, gh,
            boxstyle="round,pad=0.04,rounding_size=0.18",
            fc=fc, ec=ec, lw=0, alpha=0.055 * i, zorder=4
        ))
    ax.add_patch(FancyBboxPatch(
        (cx - w/2, cy - h/2), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.16",
        fc=fc, ec=ec, lw=2.8, ls="solid", alpha=1.0, zorder=5
    ))

    if isinstance(equipo, list):
        j1_txt, j2_txt = equipo[0], equipo[1]
    else:
        j1_txt, j2_txt = str(equipo), ""

    # Línea divisoria
    ax.plot([cx - w/2 + 0.12, cx + w/2 - 0.12], [cy, cy],
            color="#b8860b", lw=1.1, alpha=0.8, zorder=6)

    y1 = cy + h1_champ / 2 + 0.04
    y2 = cy - h1_champ / 2 - 0.04

    ax.text(cx - w/2 + 0.16, y1, "①",
            ha="left", va="center",
            fontsize=fontsize - 7, color="#ffd700", fontweight="bold", zorder=7)
    ax.text(cx + 0.1, y1, j1_txt,
            ha="center", va="center",
            fontsize=fontsize, color="#ffd700", fontweight="bold",
            zorder=7, clip_on=True)

    ax.text(cx - w/2 + 0.16, y2, "②",
            ha="left", va="center",
            fontsize=fontsize - 7, color="#ffd700", fontweight="bold", zorder=7)
    ax.text(cx + 0.1, y2, j2_txt,
            ha="center", va="center",
            fontsize=fontsize, color="#ffd700", fontweight="bold",
            zorder=7, clip_on=True)


def draw_line(ax, x1, y1, x2, y2, lw=1.5, color=None, z=1):
    ax.plot([x1, x2], [y1, y2],
            color=color or C["line"], lw=lw, zorder=z,
            solid_capstyle="round", solid_joinstyle="round")


def draw_bracket_connector(ax, x_src, y_top, y_bot, x_dst, y_mid):
    xm = (x_src + x_dst) / 2
    draw_line(ax, x_src, y_top, xm,    y_top)
    draw_line(ax, x_src, y_bot, xm,    y_bot)
    draw_line(ax, xm,    y_top, xm,    y_bot)
    draw_line(ax, xm,    y_mid, x_dst, y_mid)


def draw_medal(ax, cx, cy, pos, r=0.42):
    paleta = {
        1: ("#a07800", "#ffd700", "ORO"),
        2: ("#606060", "#d8d8d8", "PLATA"),
        3: ("#7a4500", "#cd7f32", "BRONCE"),
    }
    if pos not in paleta:
        return
    fc, ec, label = paleta[pos]
    ax.add_patch(Circle((cx, cy), r + 0.07, fc=C["bg"], ec=ec, lw=2.2, zorder=5))
    ax.add_patch(Circle((cx, cy), r,         fc=fc,      ec=ec, lw=1.2, zorder=6))
    ax.text(cx, cy,             str(pos), ha="center", va="center",
            fontsize=10, fontweight="bold", color="#ffffff", zorder=7)
    ax.text(cx, cy - r - 0.16, label,   ha="center", va="top",
            fontsize=7.5, fontweight="bold", color=ec, zorder=7)


def draw_section_divider(ax, x, y0=0.5, y1=10.7):
    ax.plot([x, x], [y0, y1],
            color=C["sep"], lw=1.0, ls="--", zorder=1, alpha=0.55)


# =====================================================================
#  PANEL SUPERIOR — BRACKET 2 VS 2
# =====================================================================

def dibujar_bracket(ax, st):
    ax.set_facecolor(C["bg"])
    ax.set_xlim(*XLIM_TOP)
    ax.set_ylim(*YLIM_TOP)
    ax.axis("off")

    oct_ys = _oct_ys()
    y_lbl    = oct_ys[0] + 1.4
    y_titulo = oct_ys[0] + 2.8
    rondas   = st["wb"]

    for lado in ("izq", "der"):
        izq      = (lado == "izq")
        xs       = XS_IZQ  if izq else XS_DER
        idx0     = 0       if izq else 4
        col_base = "azul"  if izq else "rojo"
        titulo   = "LADO AZUL" if izq else "LADO ROJO"
        dir_s    = +1 if izq else -1

        etiquetas = ["CUARTOS", "SEMIFINAL"]
        for r, (x, lbl) in enumerate(zip(xs, etiquetas)):
            ax.text(x, y_lbl, lbl, ha="center", va="bottom",
                    fontsize=19, fontweight="bold", color="#7070aa")

        ax.text(xs[0] if izq else xs[0], y_titulo, titulo,
                ha="center", va="bottom",
                fontsize=24, fontweight="bold", color="#ccccff")

        estilos = {0: col_base, 1: "win", 2: "final_w"}

        # Cajas rondas 0-1 (cuartos y semi); la final se dibuja en bloque central
        for r in range(2):
            n_slots = N_SIDE >> r
            for j in range(n_slots):
                g_idx  = (idx0 >> r) + j
                equipo = rondas[r][g_idx]
                cx     = xs[r]
                cy     = _get_y(r, j, oct_ys)
                draw_box_duo(ax, cx, cy, equipo, estilos[r])

        # Conectores para rondas 1-2
        for r in range(1, 3):
            n_match = N_SIDE >> r
            for j in range(n_match):
                y_top = _get_y(r - 1, 2 * j,     oct_ys)
                y_bot = _get_y(r - 1, 2 * j + 1, oct_ys)
                y_mid = _get_y(r,     j,          oct_ys)
                x_src = xs[r - 1] + dir_s * (BOX_W / 2)
                x_dst = xs[r]     - dir_s * (BOX_W / 2)
                draw_bracket_connector(ax, x_src, y_top, y_bot, x_dst, y_mid)

    # ── ZONA CENTRAL: FINAL (±3.0) + CAMPEÓN ────────────────────────────
    y_fin      = _get_y(2, 0, oct_ys)
    cx         = 0.0
    X_FIN_IZQ  = XS_IZQ[2]   # -3.0
    X_FIN_DER  = XS_DER[2]   # +3.0

    draw_box_duo(ax, X_FIN_IZQ, y_fin, rondas[2][0],
                 "azul" if rondas[2][0] else "final_w")
    draw_box_duo(ax, X_FIN_DER, y_fin, rondas[2][1],
                 "rojo" if rondas[2][1] else "final_w")

    # Banner "★ GRAN FINAL ★"
    ax.text(cx, y_fin + BOX_H / 2 + 0.60,
            "★  GRAN FINAL  ★", ha="center", va="bottom",
            fontsize=FS - 2, fontweight="bold", color="#ffd700",
            bbox=dict(boxstyle="round,pad=0.30", fc="#1a1000",
                      ec="#b8860b", lw=1.5, alpha=0.95),
            zorder=6)

    # Caja campeón
    champ_h = BOX_H * 1.5
    y_champ = y_fin - 2.4
    draw_box_champ_duo(ax, cx, y_champ, rondas[3][0],
                       w=BOX_W * 1.4, h=champ_h, fontsize=FS + 2)

    # Conectores hacia el campeón
    y_bot_fin   = y_fin   - BOX_H / 2
    y_top_champ = y_champ + champ_h / 2
    y_mid_conn  = (y_bot_fin + y_top_champ) / 2
    draw_line(ax, X_FIN_IZQ, y_bot_fin,  X_FIN_IZQ, y_mid_conn)
    draw_line(ax, X_FIN_DER, y_bot_fin,  X_FIN_DER, y_mid_conn)
    draw_line(ax, X_FIN_IZQ, y_mid_conn, X_FIN_DER, y_mid_conn)
    draw_line(ax, cx,        y_mid_conn, cx,         y_top_champ)

    # "CAMPEONES!" bajo la caja del campeón
    if rondas[3][0]:
        ax.text(cx, y_champ - champ_h / 2 - 0.28,
                "¡CAMPEONES!", ha="center", va="top",
                fontsize=FS - 2, fontweight="bold", color="#ffd700", zorder=6)
        ax.text(cx, y_champ - champ_h / 2 - 0.95,
                "★  ★  ★", ha="center", va="top",
                fontsize=FS - 4, color="#b8860b", zorder=6)


# =====================================================================
#  PANEL INFERIOR — 3ER PUESTO + PODIO  (versión 2vs2)
# =====================================================================

def _subcampeon(st):
    fin   = st["wb"][2]
    champ = st["wb"][3][0]
    if champ is None or fin[0] is None or fin[1] is None:
        return None
    return fin[1] if (isinstance(champ, list) and champ == fin[0]) or champ == fin[0] else fin[0]


def dibujar_panel_inferior(ax, st):
    """
    Panel inferior dividido en dos secciones (xlim = 0..36):

      Sección 1 [centro x =  9] -> 3er Puesto
      Sección 2 [centro x = 27] -> Podio

    Los bloques de equipo también muestran dos jugadores (duo).
    """
    ax.set_facecolor(C["bg"])
    ax.set_xlim(*XLIM_BOT)
    ax.set_ylim(*YLIM_BOT)
    ax.axis("off")

    # Escalado de cajas para que coincidan en tamaño físico con el bracket
    _X_RANGE_TOP = (XLIM_TOP[1] - XLIM_TOP[0])   # 33
    _Y_RANGE_TOP = (YLIM_TOP[1] - YLIM_TOP[0])   # 16
    _X_RANGE_BOT = (XLIM_BOT[1] - XLIM_BOT[0])   # 36
    _Y_RANGE_BOT = (YLIM_BOT[1] - YLIM_BOT[0])   # 12
    _RATIO_TOP   = 2.1
    _RATIO_BOT   = 1.3
    BOT_W = BOX_W * (_X_RANGE_BOT / _X_RANGE_TOP)
    BOT_H = BOX_H * (_Y_RANGE_BOT / _Y_RANGE_TOP) * (_RATIO_TOP / _RATIO_BOT)
    BOT_H1 = BOT_H / 2 - 0.04   # alto de cada sub-fila escalada

    sl = st["semifinal_losers"]

    draw_section_divider(ax, 18)

    # =================================================================
    #  SECCIÓN 1 — 3ER PUESTO  (centro x = 9)
    # =================================================================
    X3 = 9.0

    draw_medal(ax, X3 - 2.6, Y_HEAD, 3, r=0.44)
    ax.text(X3 + 0.5, Y_HEAD, "3ER PUESTO", ha="center", va="center",
            fontsize=FS, fontweight="bold", color="#cd7f32")

    xa3 = X3 - 3.2
    xb3 = X3 + 3.2
    draw_box_duo(ax, xa3, Y_CONT, sl[0], "azul" if sl[0] else "empty",
                 w=BOT_W, h=BOT_H, h1=BOT_H1, fontsize=FS)
    draw_box_duo(ax, xb3, Y_CONT, sl[1], "rojo" if sl[1] else "empty",
                 w=BOT_W, h=BOT_H, h1=BOT_H1, fontsize=FS)

    # Conector hacia el ganador del bronce
    edge_a = xa3 + BOT_W / 2
    edge_b = xb3 - BOT_W / 2
    draw_line(ax, edge_a, Y_CONT, X3,   Y_CONT)
    draw_line(ax, edge_b, Y_CONT, X3,   Y_CONT)
    draw_line(ax, X3,     Y_CONT, X3,   Y_WIN + BOT_H / 2)

    draw_box_duo(ax, X3, Y_WIN, st["tercero"], "bronze",
                 w=BOT_W, h=BOT_H, h1=BOT_H1, fontsize=FS)
    if st["tercero"]:
        ax.text(X3, Y_LBL - 0.2, "3er Puesto", ha="center", va="center",
                fontsize=FS - 2, fontweight="bold", color="#cd7f32")

    # =================================================================
    #  SECCIÓN 2 — PODIO  (lado derecho, xlim 18..36)
    #  Disposición real de podio:
    #    PLATA(izq)  ORO(centro-alto)  BRONCE(der)
    #                   4TO (abajo)
    # =================================================================

    # Centro de la sección podio y parámetros de layout
    SEC_CX   = 27.0          # centro horizontal de la sección (18..36)
    SEC_TOP  = Y_HEAD        # Y del título

    # Título PODIO
    ax.text(SEC_CX, SEC_TOP, "PODIO", ha="center", va="center",
            fontsize=FS, fontweight="bold", color="#ffffff")
    ax.plot([19.0, 35.0], [SEC_TOP - 0.52, SEC_TOP - 0.52],
            color=C["sep"], lw=1.2, zorder=1)

    # Datos de cada posición
    podio_data = {
        1: (st["wb"][3][0],  "champ",  "#ffd700"),
        2: (_subcampeon(st), "silver", "#d0d0d0"),
        3: (st["tercero"],   "bronze", "#cd7f32"),
        4: (st["cuarto"],    "empty",  "#5a5a7a"),
    }

    # Escalado de caja para el podio — ligeramente más pequeño que BOT
    PW   = BOT_W * 0.88
    PH   = BOT_H * 0.88
    PH1  = PH / 2 - 0.04
    PFS  = FS - 2

    # ── Posiciones X ─────────────────────────────────────────────────────
    H_SEP    = PW + 1.1
    X_GOLD   = SEC_CX
    X_SILVER = SEC_CX - H_SEP
    X_BRONZE = SEC_CX + H_SEP

    # ── Posiciones Y — ancla en Y_GOLD, todo derivado ────────────────────
    MR       = 0.38
    Y_GOLD   = SEC_TOP - 2.8
    Y_SILVER = Y_GOLD - 1.20
    Y_BRONZE = Y_GOLD - 1.35
    Y_4TH    = Y_GOLD - 3.50

    plat_w = PW + 0.5

    # ── Plataformas (escalones decorativos) ───────────────────────────────
    # Plata
    ax.add_patch(FancyBboxPatch(
        (X_SILVER - plat_w/2, Y_SILVER - PH/2 - 0.48),
        plat_w, 0.38,
        boxstyle="round,pad=0.04,rounding_size=0.08",
        fc="#2a2a2a", ec="#606060", lw=1.2, alpha=0.85, zorder=2
    ))
    # Bronce
    ax.add_patch(FancyBboxPatch(
        (X_BRONZE - plat_w/2, Y_BRONZE - PH/2 - 0.62),
        plat_w, 0.52,
        boxstyle="round,pad=0.04,rounding_size=0.08",
        fc="#2a1a0a", ec="#7a4500", lw=1.2, alpha=0.85, zorder=2
    ))
    # Oro
    ax.add_patch(FancyBboxPatch(
        (X_GOLD - plat_w/2, Y_GOLD - PH*1.10/2 - 0.82),
        plat_w, 0.70,
        boxstyle="round,pad=0.04,rounding_size=0.08",
        fc="#2b2000", ec="#b8860b", lw=1.4, alpha=0.90, zorder=2
    ))

    # ── ORO ───────────────────────────────────────────────────────────────
    eq1, st1, col1 = podio_data[1]
    draw_medal(ax, X_GOLD, Y_GOLD + PH*1.10/2 + MR + 0.18, 1, r=MR + 0.06)
    draw_box_duo(ax, X_GOLD, Y_GOLD, eq1,
                 st1 if eq1 else "empty",
                 w=PW * 1.10, h=PH * 1.10, h1=PH1 * 1.10, fontsize=PFS + 1, z=4)
    ax.text(X_GOLD, Y_GOLD - PH*1.10/2 - 0.26, "★  ★  ★",
            ha="center", va="top",
            fontsize=PFS - 5, color="#b8860b", zorder=5)

    # ── PLATA ─────────────────────────────────────────────────────────────
    eq2, st2, col2 = podio_data[2]
    draw_medal(ax, X_SILVER, Y_SILVER + PH/2 + MR + 0.12, 2, r=MR)
    draw_box_duo(ax, X_SILVER, Y_SILVER, eq2,
                 st2 if eq2 else "empty",
                 w=PW, h=PH, h1=PH1, fontsize=PFS, z=3)

    # ── BRONCE ────────────────────────────────────────────────────────────
    eq3, st3, col3 = podio_data[3]
    draw_medal(ax, X_BRONZE, Y_BRONZE + PH/2 + MR + 0.12, 3, r=MR)
    draw_box_duo(ax, X_BRONZE, Y_BRONZE, eq3,
                 st3 if eq3 else "empty",
                 w=PW, h=PH, h1=PH1, fontsize=PFS, z=3)

    # ── 4TO LUGAR ─────────────────────────────────────────────────────────
    eq4, st4, col4 = podio_data[4]
    draw_box_duo(ax, SEC_CX, Y_4TH, eq4,
                 st4 if eq4 else "empty",
                 w=PW * 0.90, h=PH * 0.90, h1=PH1 * 0.90, fontsize=PFS - 1, z=3)
    ax.text(SEC_CX, Y_4TH - PH*0.90/2 - 0.18, "4° LUGAR",
            ha="center", va="top",
            fontsize=PFS - 2, fontweight="bold", color=col4, zorder=5)


# =====================================================================
#  RENDER PRINCIPAL
# =====================================================================

def render(st, banner=None, ruta=None, dpi=130):
    fig = plt.figure(figsize=(34, 20), facecolor=C["bg"])
    gs  = fig.add_gridspec(
        2, 1,
        height_ratios=[2.1, 1.3],
        hspace=0.03,
        top=0.93, bottom=0.02,
        left=0.01, right=0.99,
    )
    ax_top = fig.add_subplot(gs[0])
    ax_bot = fig.add_subplot(gs[1])

    dibujar_bracket(ax_top, st)
    dibujar_panel_inferior(ax_bot, st)

    fig.suptitle(
        "TORNEO 2 VS 2  —  ELIMINACION DIRECTA  (8 EQUIPOS)",
        fontsize=25, fontweight="bold", color="#dde0ff",
        y=0.97, fontfamily="DejaVu Sans",
    )

    if banner:
        fig.text(
            0.5, 0.935, banner,
            ha="center", va="top",
            fontsize=20, fontweight="bold", color="#ffe08a",
            bbox=dict(boxstyle="round,pad=0.4",
                      fc="#140f00", ec="#b8860b", lw=1.6),
        )

    if ruta:
        fig.savefig(ruta, bbox_inches="tight", dpi=dpi,
                    facecolor=C["bg"], pad_inches=0.12)
    plt.close(fig)


# =====================================================================
#  LÓGICA DEL TORNEO
# =====================================================================

def _nombre_eq(eq):
    if eq is None: return "???"
    if isinstance(eq, list): return f"{eq[0]} & {eq[1]}"
    return str(eq)


def pedir_ganador(eq1, eq2, etiqueta):
    print(f"\n  --- {etiqueta} ---")
    print(f"  [1]  {_nombre_eq(eq1)}")
    print(f"  [2]  {_nombre_eq(eq2)}")
    print(f"  [0]  RETROCEDER")
    while True:
        raw = input("  Quien avanza? (1 / 2 / 0): ").strip()
        if raw == "0": return "RETROCEDER"
        if raw == "1": return eq1, eq2
        if raw == "2": return eq2, eq1
        print("  Ingresa 1, 2 o 0.")


def correr_torneo(equipos, out_dir=None):
    if out_dir is None:
        try:    out_dir = os.path.dirname(os.path.abspath(__file__))
        except: out_dir = os.getcwd()
    os.makedirs(out_dir, exist_ok=True)
    ruta_actual = os.path.join(out_dir, "actual_2vs2.png")

    partidos     = _construir_partidos(equipos)
    st           = estado_inicial(equipos)
    historial    = []
    sets_jugados = 0

    render(st, banner="Esperando el primer partido...", ruta=ruta_actual)
    print("\n" + "="*60)
    print("  TORNEO 2 VS 2 - ELIMINACION DIRECTA - 8 EQUIPOS")
    print("  [0] en cualquier momento para RETROCEDER")
    print("="*60)

    idx = 0
    while idx < len(partidos):
        p  = partidos[idx]
        e1 = _resolver(st, p["src1"])
        e2 = _resolver(st, p["src2"])
        if e1 is None or e2 is None:
            idx += 1
            continue

        print(f"\n{'='*60}\n  {p['etapa']}\n{'='*60}")
        resultado = pedir_ganador(e1, e2, p["label"])

        if resultado == "RETROCEDER":
            if not historial:
                print("  No hay partidos anteriores para deshacer.")
            else:
                st, prev_idx = historial.pop()
                idx          = prev_idx
                sets_jugados = max(0, sets_jugados - 1)
                print("Partido deshecho.")
                render(st, banner=f"Partido deshecho  —  Retrocediendo al SET {sets_jugados}", ruta=ruta_actual)
            continue

        ganador, perdedor = resultado
        historial.append((copy.deepcopy(st), idx))
        _aplicar(st, p, ganador, perdedor)
        sets_jugados += 1
        render(st,
               banner=f"Partido {sets_jugados}  ·  {p['label']}  ->  avanzó  {_nombre_eq(ganador)}",
               ruta=ruta_actual)
        print(f"  Avanza: {_nombre_eq(ganador)}")
        idx += 1

    print(f"\n{'='*60}")
    print("  TORNEO FINALIZADO")
    print(f"  1. Campeones: {_nombre_eq(st['wb'][3][0])}")
    print(f"  2. 2do:       {_nombre_eq(_subcampeon(st))}")
    print(f"  3. 3er:       {_nombre_eq(st['tercero'])}")
    print(f"  4. 4to:       {_nombre_eq(st['cuarto'])}")
    print(f"  Imagen: {ruta_actual}")
    print("="*60)


# =====================================================================
#  CONSTRUCCIÓN DE PARTIDOS
# =====================================================================

def _construir_partidos(equipos):
    partidos = []

    for r, (etapa, n) in enumerate([
        ("CUARTOS DE FINAL", 4),
        ("SEMIFINALES",      2),
    ]):
        for i in range(n):
            partidos.append({
                "etapa":    etapa,
                "label":    f"{etapa.title()} - Partido {i+1}",
                "src1":     f"wb[{r}][{2*i}]",
                "src2":     f"wb[{r}][{2*i+1}]",
                "dst_win":  f"wb[{r+1}][{i}]",
                "dst_lose": f"semi_loser[{i}]" if r == 1 else None,
                "ronda":    r,
            })

    partidos.append({
        "etapa":    "3ER PUESTO",
        "label":    "Partido 3er Puesto",
        "src1":     "semi_loser[0]",
        "src2":     "semi_loser[1]",
        "dst_win":  "tercero",
        "dst_lose": "cuarto",
        "ronda":    "3p",
    })

    partidos.append({
        "etapa":    "GRAN FINAL",
        "label":    "Gran Final",
        "src1":     "wb[2][0]",
        "src2":     "wb[2][1]",
        "dst_win":  "wb[3][0]",
        "dst_lose": None,
        "ronda":    2,
    })

    return partidos


def _resolver(st, src):
    if src.startswith("wb["):
        r, i = map(int, re.findall(r"\d+", src))
        return st["wb"][r][i]
    if src.startswith("semi_loser["):
        i = int(re.findall(r"\d+", src)[0])
        return st["semifinal_losers"][i]
    return None


def _aplicar(st, p, ganador, perdedor):
    _escribir(st, p["dst_win"], ganador)
    if p.get("dst_lose"):
        _escribir(st, p["dst_lose"], perdedor)
    if p["ronda"] == "3p":
        st["tercero"] = ganador
        st["cuarto"]  = perdedor


def _escribir(st, dst, valor):
    if dst is None:
        return
    if dst.startswith("wb["):
        r, i = map(int, re.findall(r"\d+", dst))
        st["wb"][r][i] = valor
    elif dst.startswith("semi_loser["):
        i = int(re.findall(r"\d+", dst)[0])
        st["semifinal_losers"][i] = valor
    elif dst == "tercero":
        st["tercero"] = valor
    elif dst == "cuarto":
        st["cuarto"]  = valor


# =====================================================================
if __name__ == "__main__":
    correr_torneo(EQUIPOS)