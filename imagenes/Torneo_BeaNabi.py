"""
Torneo_BeaNabi.py  —  Versión final
=====================================
Bracket de eliminación directa para 16 jugadores.

Estructura:
  · Panel superior : bracket con 4 columnas por lado
                     (OCTAVOS -> CUARTOS -> SEMIFINAL -> FINAL -> CAMPEON)
  · Panel inferior : 3er Puesto (izquierda) + Podio (derecha)

Geometría del bracket (posiciones X por lado):
  0 = OCTAVOS    x = ±13.5   (N = 8)
  1 = CUARTOS    x = ± 9.5   (N = 4)
  2 = SEMIFINAL  x = ± 6.0   (N = 2)
  3 = FINAL      x = ± 2.5   (N = 1)
  Centro         x =   0.0   (Campeón, debajo de los finalistas)
"""

import re
import os
import copy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle

# =====================================================================
#  JUGADORES  —  reemplaza estos nombres con los reales del torneo
# =====================================================================
JUGADORES = [
    "Jugador 1",  "Jugador 2",  "Jugador 3",  "Jugador 4",
    "Jugador 5",  "Jugador 6",  "Jugador 7",  "Jugador 8",
    "Jugador 9",  "Jugador 10", "Jugador 11", "Jugador 12",
    "Jugador 13", "Jugador 14", "Jugador 15", "Jugador 16",
]

# =====================================================================
#  PALETA DE COLORES
# =====================================================================
C = {
    "bg":      "#0b0b1a",              # fondo general
    "azul":    ("#1a4a8a", "#4d9fff"), # lado izquierdo (octavos)
    "rojo":    ("#8a1a1a", "#ff4d4d"), # lado derecho  (octavos)
    "win":     ("#1a5c2e", "#50e87a"), # ganadores de ronda
    "final_w": ("#6b3a00", "#ffb347"), # finalistas
    "champ":   ("#5c4500", "#ffd700"), # campeón
    "silver":  ("#353535", "#c0c0c0"), # subcampeón
    "bronze":  ("#4a2800", "#cd7f32"), # 3er puesto
    "empty":   ("#0f0f20", "#252545"), # casilla vacía
    "line":    "#3a3a6a",              # conectores del bracket
    "sep":     "#2a2a50",              # separadores de sección
}

# =====================================================================
#  GEOMETRÍA — valores fijos para toda la figura
# =====================================================================

# Dimensiones de caja: iguales para todas las rondas del bracket.
BOX_W = 2.7   # ancho de cada caja
BOX_H = 0.84  # alto  de cada caja
FS    = 25    # tamaño de fuente para todas las cajas del bracket

# Separación vertical entre jugadores en octavos.
GAP_Y  = 1.5
N_SIDE = 8    # jugadores por lado (8 por cada mitad = 16 en total)

# Posiciones X de cada columna (izquierda y derecha).
# El paso se reduce hacia el centro para dar espacio al campeón.
XS_IZQ = [-13.5, -9.5, -6, -2.5]
XS_DER = [ 13.5,  9.5,  6,  2.5]

# Límites del panel superior (bracket)
XLIM_TOP = (-17.5, 17.5)
YLIM_TOP = (-2.2, 14.5)

# Límites del panel inferior (3er puesto + podio)
XLIM_BOT = (0.0, 36.0)
YLIM_BOT = (0.0, 12.0)

# Posiciones Y de referencia en el panel inferior
Y_HEAD = 9.9   # encabezados de sección
Y_CONT = 7.7   # cajas de contendientes
Y_WIN  = 5.5   # caja del ganador
Y_LBL  = 4.55  # etiqueta bajo el ganador


# =====================================================================
#  ESTADO DEL TORNEO
# =====================================================================

def estado_inicial(jugadores):
    """Devuelve el estado inicial para 16 jugadores en eliminación directa."""
    return {
        "wb": [
            list(jugadores),   # ronda 0: 16 jugadores (octavos)
            [None] * 8,        # ronda 1:  8 jugadores (cuartos)
            [None] * 4,        # ronda 2:  4 jugadores (semifinal)
            [None] * 2,        # ronda 3:  2 jugadores (final)
            [None] * 1,        # ronda 4:  1 jugador   (campeón)
        ],
        "semifinal_losers": [None, None],
        "tercero": None,
        "cuarto":  None,
    }


# =====================================================================
#  HELPERS DE GEOMETRÍA
# =====================================================================

def _oct_ys():
    """Posiciones Y de los 8 slots de octavos (de arriba a abajo, i=0 es el tope)."""
    return [(N_SIDE - 1 - i) * GAP_Y for i in range(N_SIDE)]


def _get_y(ronda, slot, oct_ys):
    """
    Calcula la Y del slot en la ronda indicada de forma recursiva.
    Y(r, j) = promedio de Y(r-1, 2j) e Y(r-1, 2j+1)
    Garantiza que los conectores queden centrados exactamente.
    """
    if ronda == 0:
        return oct_ys[slot]
    ya = _get_y(ronda - 1, 2 * slot,     oct_ys)
    yb = _get_y(ronda - 1, 2 * slot + 1, oct_ys)
    return (ya + yb) / 2


# =====================================================================
#  PRIMITIVAS DE DIBUJO
# =====================================================================

def draw_box(ax, cx, cy, nombre, estilo, w=BOX_W, h=BOX_H, fontsize=FS, z=3):
    """
    Dibuja una caja redondeada centrada en (cx, cy).
    - nombre=None  -> caja vacía punteada semitransparente.
    - nombre!=None -> caja rellena con el texto centrado.
    """
    if nombre is None:
        fc, ec = C["empty"]
        alpha = 0.55
        ls    = "--"
        txt   = ""
    else:
        fc, ec = C[estilo]
        alpha = 1.0
        ls    = "solid"
        txt   = nombre

    ax.add_patch(FancyBboxPatch(
        (cx - w/2, cy - h/2), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.10",
        fc=fc, ec=ec, lw=1.8, ls=ls, alpha=alpha, zorder=z
    ))
    if txt:
        ax.text(cx, cy, txt, ha="center", va="center",
                fontsize=fontsize, color="#ffffff", fontweight="bold",
                zorder=z + 1, clip_on=True)


def draw_box_champ(ax, cx, cy, nombre, w=BOX_W*1.35, h=BOX_H*1.35, fontsize=FS+2):
    """
    Caja especial del campeón con efecto de brillo dorado en capas concéntricas.
    Tamaño proporcional: BOX_W*1.35 de ancho, BOX_H*1.35 de alto, FS+2 de fuente.
    """
    if nombre is None:
        draw_box(ax, cx, cy, None, "empty", w=w, h=h, fontsize=fontsize, z=4)
        return
    fc, ec = C["champ"]
    for i in range(4, 0, -1):
        gw = w + i * 0.28
        gh = h + i * 0.18
        ax.add_patch(FancyBboxPatch(
            (cx - gw/2, cy - gh/2), gw, gh,
            boxstyle="round,pad=0.04,rounding_size=0.16",
            fc=fc, ec=ec, lw=0, alpha=0.055 * i, zorder=4
        ))
    ax.add_patch(FancyBboxPatch(
        (cx - w/2, cy - h/2), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.14",
        fc=fc, ec=ec, lw=2.6, ls="solid", alpha=1.0, zorder=5
    ))
    ax.text(cx, cy, nombre, ha="center", va="center",
            fontsize=fontsize, color="#ffd700", fontweight="bold",
            zorder=6, clip_on=True)


def draw_line(ax, x1, y1, x2, y2, lw=1.5, color=None, z=1):
    ax.plot([x1, x2], [y1, y2],
            color=color or C["line"], lw=lw, zorder=z,
            solid_capstyle="round", solid_joinstyle="round")


def draw_bracket_connector(ax, x_src, y_top, y_bot, x_dst, y_mid):
    """
    Conector tipo bracket (forma de gancho horizontal).
    xm = punto medio garantiza el gancho simétrico.
    """
    xm = (x_src + x_dst) / 2
    draw_line(ax, x_src, y_top, xm,    y_top)
    draw_line(ax, x_src, y_bot, xm,    y_bot)
    draw_line(ax, xm,    y_top, xm,    y_bot)
    draw_line(ax, xm,    y_mid, x_dst, y_mid)


def draw_match_connector_horiz(ax, xa, xb, y_cont, xc, yc_top):
    """
    Conector horizontal para dos contendientes al mismo Y.
    Une los bordes internos de (xa) y (xb) hacia el punto central (xc),
    luego baja verticalmente hasta (yc_top).
    Usado en la sección de 3er Puesto del panel inferior.
    """
    edge_a = xa + BOX_W / 2
    edge_b = xb - BOX_W / 2
    draw_line(ax, edge_a, y_cont, xc,     y_cont)
    draw_line(ax, edge_b, y_cont, xc,     y_cont)
    draw_line(ax, xc,     y_cont, xc, yc_top)


def draw_medal(ax, cx, cy, pos, r=0.42):
    """
    Dibuja una medalla circular con número y etiqueta de posición.
    pos=1 -> Oro, pos=2 -> Plata, pos=3 -> Bronce.
    """
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
    ax.text(cx, cy,           str(pos), ha="center", va="center",
            fontsize=10, fontweight="bold", color="#ffffff", zorder=7)
    ax.text(cx, cy - r - 0.16, label,  ha="center", va="top",
            fontsize=7.5, fontweight="bold", color=ec, zorder=7)


def draw_section_divider(ax, x, y0=0.5, y1=10.7):
    """Línea punteada vertical que delimita secciones en el panel inferior."""
    ax.plot([x, x], [y0, y1],
            color=C["sep"], lw=1.0, ls="--", zorder=1, alpha=0.55)


# =====================================================================
#  PANEL SUPERIOR — BRACKET PRINCIPAL
# =====================================================================

def dibujar_bracket(ax, st):
    """
    Dibuja el bracket completo de 16 jugadores.

    Columnas por lado:
      0 = OCTAVOS    x = ±13.5   (N=8)
      1 = CUARTOS    x = ± 9.5   (N=4)
      2 = SEMIFINAL  x = ± 6.0   (N=2)
      3 = FINAL      x = ± 2.5   (N=1)
      Centro         x =   0.0   (campeón, debajo de los finalistas)
    """
    ax.set_facecolor(C["bg"])
    ax.set_xlim(*XLIM_TOP)
    ax.set_ylim(*YLIM_TOP)
    ax.axis("off")

    oct_ys   = _oct_ys()
    y_lbl    = oct_ys[0] + 1.1   # Y de las etiquetas de columna
    y_titulo = oct_ys[0] + 2.6   # Y de los títulos "LADO AZUL / LADO ROJO"
    rondas   = st["wb"]

    for lado in ("izq", "der"):
        izq      = (lado == "izq")
        xs       = XS_IZQ  if izq else XS_DER
        idx0     = 0       if izq else 8
        col_base = "azul"  if izq else "rojo"
        titulo   = "LADO AZUL" if izq else "LADO ROJO"
        dir_s    = +1 if izq else -1

        # Etiquetas de columna sobre cada ronda
        etiquetas = ["OCTAVOS", "CUARTOS", "SEMIFINAL"]
        for r, (x, lbl) in enumerate(zip(xs, etiquetas)):
            ax.text(x, y_lbl, lbl, ha="center", va="bottom",
                    fontsize=20, fontweight="bold", color="#7070aa")

        # Título del lado
        ax.text(xs[1], y_titulo, titulo, ha="center", va="bottom",
                fontsize=25, fontweight="bold", color="#ccccff")

        estilos = {0: col_base, 1: "win", 2: "win", 3: "final_w"}

        # Cajas de las rondas 0-2 (la columna FINAL se dibuja en el bloque central)
        for r in range(3):
            n_slots = N_SIDE >> r
            for j in range(n_slots):
                g_idx  = (idx0 >> r) + j
                nombre = rondas[r][g_idx]
                cx     = xs[r]
                cy     = _get_y(r, j, oct_ys)
                draw_box(ax, cx, cy, nombre, estilos[r])

        # Conectores tipo bracket para rondas 1-3
        # (r=3 conecta las semis con los finalistas en la columna FINAL)
        for r in range(1, 4):
            n_match = N_SIDE >> r
            for j in range(n_match):
                y_top = _get_y(r - 1, 2 * j,     oct_ys)
                y_bot = _get_y(r - 1, 2 * j + 1, oct_ys)
                y_mid = _get_y(r,     j,          oct_ys)
                x_src = xs[r - 1] + dir_s * (BOX_W / 2)
                x_dst = xs[r]     - dir_s * (BOX_W / 2)
                draw_bracket_connector(ax, x_src, y_top, y_bot, x_dst, y_mid)

    # ── ZONA CENTRAL: columna FINAL (±2.5) + caja del campeón ──────────
    y_fin = _get_y(3, 0, oct_ys)   # Y de los finalistas
    cx    = 0.0

    # Finalistas en la columna FINAL (xs[3] = ±2.5)
    X_FIN_IZQ = XS_IZQ[3]   # -2.5
    X_FIN_DER = XS_DER[3]   # +2.5

    draw_box(ax, X_FIN_IZQ, y_fin, st["wb"][3][0],
             "azul" if st["wb"][3][0] else "final_w")
    draw_box(ax, X_FIN_DER, y_fin, st["wb"][3][1],
             "rojo" if st["wb"][3][1] else "final_w")

    # Etiqueta "★ GRAN FINAL ★" encima de los finalistas
    ax.text(cx, y_fin + BOX_H / 2 + 0.55,
            "★  GRAN FINAL  ★", ha="center", va="bottom",
            fontsize=FS - 2, fontweight="bold", color="#ffd700",
            bbox=dict(boxstyle="round,pad=0.30", fc="#1a1000",
                      ec="#b8860b", lw=1.5, alpha=0.95),
            zorder=6)

    # Caja del campeón, ubicada debajo de los dos finalistas
    champ_w = BOX_W * 1.1
    y_champ = y_fin - 2.0
    draw_box_champ(ax, cx, y_champ, st["wb"][4][0],
                   w=champ_w, h=BOX_H * 1.35, fontsize=FS + 2)

    # Conector descendente desde cada finalista hacia la caja del campeón
    y_bot_fin   = y_fin   - BOX_H / 2
    y_top_champ = y_champ + BOX_H * 1.35 / 2
    y_mid_conn  = (y_bot_fin + y_top_champ) / 2
    draw_line(ax, X_FIN_IZQ, y_bot_fin,  X_FIN_IZQ, y_mid_conn)
    draw_line(ax, X_FIN_DER, y_bot_fin,  X_FIN_DER, y_mid_conn)
    draw_line(ax, X_FIN_IZQ, y_mid_conn, X_FIN_DER, y_mid_conn)
    draw_line(ax, cx,        y_mid_conn, cx,         y_top_champ)

    # Texto "CAMPEON!" y estrellas debajo de la caja del campeón
    if st["wb"][4][0]:
        ax.text(cx, y_champ - BOX_H * 1.35 / 2 - 0.28,
                "CAMPEON!", ha="center", va="top",
                fontsize=FS - 2, fontweight="bold", color="#ffd700", zorder=6)
        ax.text(cx, y_champ - BOX_H * 1.35 / 2 - 0.90,
                "★  ★  ★", ha="center", va="top",
                fontsize=FS - 4, color="#b8860b", zorder=6)


# =====================================================================
#  PANEL INFERIOR — 3ER PUESTO + PODIO
# =====================================================================

def _subcampeon(st):
    """Devuelve al finalista que perdió la Gran Final (subcampeón)."""
    fin   = st["wb"][3]
    champ = st["wb"][4][0]
    if champ is None or fin[0] is None or fin[1] is None:
        return None
    return fin[1] if champ == fin[0] else fin[0]


def dibujar_panel_inferior(ax, st):
    """
    Panel inferior dividido en dos secciones simétricas (xlim = 0..36):

      Sección 1 [centro x =  9] -> 3er Puesto
        Partido entre los perdedores de semifinal y el ganador del bronce.

      Sección 2 [centro x = 27] -> Podio
        Clasificación final: Oro, Plata, Bronce y 4to puesto.

    BOT_W / BOT_H: dimensiones de caja reescaladas para igualar el tamaño
    físico del bracket superior, compensando diferencias de rango de
    coordenadas y proporciones de altura (height_ratios=[2.1, 1.0]).

        BOT_W = BOX_W * (36/35)            ~= 2.777
        BOT_H = BOX_H * (11.0/15.7) * 2.1 ~= 1.236
    """
    ax.set_facecolor(C["bg"])
    ax.set_xlim(*XLIM_BOT)
    ax.set_ylim(*YLIM_BOT)
    ax.axis("off")

    # Dimensiones de caja corregidas para igualar el tamaño físico del bracket
    _X_RANGE_TOP = (XLIM_TOP[1] - XLIM_TOP[0])   # 35
    _Y_RANGE_TOP = (YLIM_TOP[1] - YLIM_TOP[0])   # ~15.7
    _X_RANGE_BOT = (XLIM_BOT[1] - XLIM_BOT[0])   # 36
    _Y_RANGE_BOT = (YLIM_BOT[1] - YLIM_BOT[0])   # ~11.0
    _RATIO_TOP   = 2.1
    _RATIO_BOT   = 1.0
    BOT_W = BOX_W * (_X_RANGE_BOT / _X_RANGE_TOP)
    BOT_H = BOX_H * (_Y_RANGE_BOT / _Y_RANGE_TOP) * (_RATIO_TOP / _RATIO_BOT)

    sl = st["semifinal_losers"]

    # Línea divisoria central entre las dos secciones
    draw_section_divider(ax, 18)

    # =================================================================
    #  SECCIÓN 1 — 3ER PUESTO  (centro x = 9)
    # =================================================================
    X3 = 9.0

    draw_medal(ax, X3 - 2.5, Y_HEAD, 3, r=0.44)
    ax.text(X3 + 0.5, Y_HEAD, "3ER PUESTO", ha="center", va="center",
            fontsize=FS, fontweight="bold", color="#cd7f32")

    xa3 = X3 - 3.0
    xb3 = X3 + 3.0
    draw_box(ax, xa3, Y_CONT, sl[0], "azul" if sl[0] else "empty",
             w=BOT_W, h=BOT_H, fontsize=FS)
    draw_box(ax, xb3, Y_CONT, sl[1], "rojo" if sl[1] else "empty",
             w=BOT_W, h=BOT_H, fontsize=FS)

    draw_match_connector_horiz(ax, xa3, xb3, Y_CONT, X3, Y_WIN + BOT_H / 2)

    draw_box(ax, X3, Y_WIN, st["tercero"], "bronze", w=BOT_W, h=BOT_H, fontsize=FS)
    if st["tercero"]:
        ax.text(X3, Y_LBL-0.4, "3er Puesto", ha="center", va="center",
                fontsize=FS - 2, fontweight="bold", color="#cd7f32")

    # =================================================================
    #  SECCIÓN 2 — PODIO  (centro x = 27)
    # =================================================================
    XP  = 27.0
    ROW = 1.43

    ax.text(XP, Y_HEAD, "PODIO", ha="center", va="center",
            fontsize=FS, fontweight="bold", color="#ffffff")
    ax.plot([20.5, 33.5], [Y_HEAD - 0.52, Y_HEAD - 0.52],
            color=C["sep"], lw=1.2, zorder=1)

    podio = [
        (1, "Oro",    st["wb"][4][0],  "champ",  "#ffd700"),
        (2, "Plata",  _subcampeon(st), "silver", "#d0d0d0"),
        (3, "Bronce", st["tercero"],   "bronze", "#cd7f32"),
        (4, "4to",    st["cuarto"],    "empty",  "#5a5a7a"),
    ]

    for pos, lbl, nombre, estilo, color_lbl in podio:
        yp = 8.6 - (pos - 1) * ROW

        if pos <= 3:
            draw_medal(ax, XP - 3.5, yp, pos, r=0.39)
        else:
            ax.text(XP - 3.5, yp, "4to", ha="center", va="center",
                    fontsize=FS, fontweight="bold", color=color_lbl, zorder=5)

        ax.text(XP - 2.0, yp + 0.10, lbl, ha="left", va="center",
                fontsize=FS, fontweight="bold", color=color_lbl)

        draw_box(ax, XP + 3.5, yp, nombre, estilo if nombre else "empty",
                 w=BOT_W, h=BOT_H, fontsize=FS, z=3)


# =====================================================================
#  RENDER PRINCIPAL
# =====================================================================

def render(st, banner=None, ruta=None, dpi=130):
    """
    Genera y guarda la imagen completa del torneo.
    Figura: 34 x 20 pulgadas a 130 DPI = 4420 x 2600 px.
    """
    fig = plt.figure(figsize=(34, 20), facecolor=C["bg"])
    gs  = fig.add_gridspec(
        2, 1,
        height_ratios=[2.1, 1.0],
        hspace=0.03,
        top=0.93, bottom=0.02,
        left=0.01, right=0.99,
    )
    ax_top = fig.add_subplot(gs[0])
    ax_bot = fig.add_subplot(gs[1])

    dibujar_bracket(ax_top, st)
    dibujar_panel_inferior(ax_bot, st)

    # Título principal
    fig.suptitle(
        "TORNEO 16 JUGADORES  —  ELIMINACION DIRECTA",
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

def pedir_ganador(p1, p2, etiqueta):
    """Solicita por consola quién avanza en el partido indicado."""
    print(f"\n  --- {etiqueta} ---")
    print(f"  [1]  {p1}")
    print(f"  [2]  {p2}")
    print(f"  [0]  RETROCEDER")
    while True:
        raw = input("  Quien avanza? (1 / 2 / 0): ").strip()
        if raw == "0": return "RETROCEDER"
        if raw == "1": return p1, p2
        if raw == "2": return p2, p1
        print("  Ingresa 1, 2 o 0.")


def correr_torneo(jugadores, out_dir=None):
    """
    Ejecuta el torneo de forma interactiva por consola.
    Por cada partido solicita el ganador y actualiza la imagen.
    Permite retroceder partidos con la opción 0.
    """
    if out_dir is None:
        try:    out_dir = os.path.dirname(os.path.abspath(__file__))
        except: out_dir = os.getcwd()
    os.makedirs(out_dir, exist_ok=True)
    ruta_actual = os.path.join(out_dir, "actual.png")

    partidos     = _construir_partidos(jugadores)
    st           = estado_inicial(jugadores)
    historial    = []
    sets_jugados = 0

    # Banner inicial
    render(st, banner="Esperando el primer partido...", ruta=ruta_actual)
    print("\n" + "="*60)
    print("  TORNEO 16 JUGADORES - ELIMINACION DIRECTA")
    print("  [0] en cualquier momento para RETROCEDER")
    print("="*60)

    idx = 0
    while idx < len(partidos):
        p  = partidos[idx]
        n1 = _resolver(st, p["src1"])
        n2 = _resolver(st, p["src2"])
        if n1 is None or n2 is None:
            idx += 1
            continue

        print(f"\n{'='*60}\n  {p['etapa']}\n{'='*60}")
        resultado = pedir_ganador(n1, n2, p["label"])

        if resultado == "RETROCEDER":
            if not historial:
                print("  No hay partidos anteriores para deshacer.")
            else:
                st, prev_idx = historial.pop()
                idx          = prev_idx
                sets_jugados = max(0, sets_jugados - 1)
                print("Partido deshecho.")
                # Banner de retroceso
                render(st, banner=f"Partido deshecho  —  Retrocediendo al SET {sets_jugados}", ruta=ruta_actual)
            continue

        ganador, perdedor = resultado
        historial.append((copy.deepcopy(st), idx))
        _aplicar(st, p, ganador, perdedor)
        sets_jugados += 1
        # Banner de partido
        render(st,
               banner=f"Partido {sets_jugados}  ·  {p['label']}  ->  avanzó  {ganador}",
               ruta=ruta_actual)
        print(f"  Avanza: {ganador}")
        idx += 1

    print(f"\n{'='*60}")
    print("  TORNEO FINALIZADO")
    print(f"  1. Campeón:  {st['wb'][4][0]}")
    print(f"  2. 2do:      {_subcampeon(st)}")
    print(f"  3. 3er:      {st['tercero']}")
    print(f"  4. 4to:      {st['cuarto']}")
    print(f"  Imagen: {ruta_actual}")
    print("="*60)


# =====================================================================
#  CONSTRUCCIÓN DE PARTIDOS
# =====================================================================

def _construir_partidos(jugadores):
    """Construye la lista ordenada de partidos para eliminación directa."""
    partidos = []

    for r, (etapa, n) in enumerate([
        ("OCTAVOS DE FINAL", 8),
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
                "dst_lose": f"semi_loser[{i}]" if r == 2 else None,
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
        "src1":     "wb[3][0]",
        "src2":     "wb[3][1]",
        "dst_win":  "wb[4][0]",
        "dst_lose": None,
        "ronda":    3,
    })

    return partidos


def _resolver(st, src):
    """Devuelve el jugador en la posición indicada por src."""
    if src.startswith("wb["):
        r, i = map(int, re.findall(r"\d+", src))
        return st["wb"][r][i]
    if src.startswith("semi_loser["):
        i = int(re.findall(r"\d+", src)[0])
        return st["semifinal_losers"][i]
    return None


def _aplicar(st, p, ganador, perdedor):
    """Escribe el resultado del partido en el estado del torneo."""
    _escribir(st, p["dst_win"], ganador)
    if p.get("dst_lose"):
        _escribir(st, p["dst_lose"], perdedor)
    if p["ronda"] == "3p":
        st["tercero"] = ganador
        st["cuarto"]  = perdedor


def _escribir(st, dst, valor):
    """Actualiza una posición del estado a partir de su clave de destino."""
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
    correr_torneo(JUGADORES)