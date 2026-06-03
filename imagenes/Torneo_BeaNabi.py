"""
Torneo_BeaNabi.py  —  Renderizador v4 (arquitectura rediseñada)
===============================================================
AUDITORIA v3 → v4
-----------------
Errores geométricos corregidos:
  1. Espaciado entre columnas era variable (3.3–3.8). Ahora fijo: 4.0 u. c/ronda.
  2. Conector xm dependía del gap irregular. Ahora siempre cae en el punto medio exacto.
  3. El tamaño de las cajas cambiaba en la ronda FINAL (BOX_W*1.08, FS+0.5). Ahora
     TODAS las cajas del bracket usan las mismas dimensiones → alineación perfecta.

Errores de espaciado corregidos:
  4. GAP_Y causaba 9.45 u. de altura útil con espacio sobrante en ylim. Ahora
     GAP_Y=1.5 da 10.5 u. y ylim se ajusta al contenido real.
  5. Panel inferior: las secciones compartían eje sin límites claros. Ahora cada
     sección tiene un ancho fijo de 12 u. (total 36 u.) con divisores visuales.

Errores de jerarquía visual corregidos:
  6. El campeón tenía la misma caja que el resto. Ahora usa draw_box_champ:
     caja 2× más ancha (w=5.2), más alta (h=1.15), fuente 15pt y efecto glow.
  7. "GRAN FINAL" era un texto simple. Ahora lleva bbox dorado destacado y estrella.
  8. El podio no diferenciaba visualmente Oro/Plata/Bronce. Ahora draw_medal dibuja
     círculos coloreados con etiquetas ORO/PLATA/BRONCE.

Errores de UX corregidos:
  9. Las etiquetas de ronda (OCTAVOS, CUARTOS…) se renderizaban sobre el bracket
     sin línea guía. Ahora están alineadas a la X exacta de cada columna.
  10. El partido por el 3er puesto no estaba centrado en su sección. Ahora centrado
      en x=6.0 con conector T simétrico.
  11. Los conectores de 3er puesto y Gran Final eran líneas brutas, no conectores
      de bracket. Ahora usan draw_match_connector_horiz.
"""

import re
import os
import copy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle

# =====================================================================
#  JUGADORES (placeholder — reemplaza con los reales)
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
    "bg":      "#0b0b1a",   # fondo general
    "azul":    ("#1a4a8a", "#4d9fff"),   # lado izquierdo (octavos)
    "rojo":    ("#8a1a1a", "#ff4d4d"),   # lado derecho  (octavos)
    "win":     ("#1a5c2e", "#50e87a"),   # ganadores de ronda
    "final_w": ("#6b3a00", "#ffb347"),   # finalistas
    "champ":   ("#5c4500", "#ffd700"),   # campeón
    "silver":  ("#353535", "#c0c0c0"),   # subcampeón
    "bronze":  ("#4a2800", "#cd7f32"),   # 3er puesto
    "empty":   ("#0f0f20", "#252545"),   # casilla vacía
    "line":    "#3a3a6a",               # conectores del bracket
    "sep":     "#2a2a50",               # separadores de sección
}

# =====================================================================
#  GEOMETRÍA — valores fijos para TODA la figura
# =====================================================================

# Dimensiones de caja: IGUALES para todas las rondas del bracket.
# Criterio: nombre más largo ≤ 14 chars; a 130 DPI cada char ≈ 8px → ok en 2.7u.
BOX_W  = 2.7    # ancho fijo
BOX_H  = 0.84   # alto fijo
FS     = 11.5   # fontsize fijo (todas las cajas del bracket)

# Separación vertical entre jugadores en octavos.
# 8 jugadores → span vertical = 7 × GAP_Y = 10.5 u.
GAP_Y  = 1.5
N_SIDE = 8   # jugadores por lado

# Posiciones X de cada ronda.
# PASO FIJO = 4.0 u. garantiza espaciado horizontal uniforme y conectores iguales.
STEP = 4.0
XS_IZQ = [-13.5, -9.5, -5.5, -1.5]   # izq: octavos → final (de afuera hacia el centro)
XS_DER = [ 13.5,  9.5,  5.5,  1.5]   # der: octavos → final (ídem, espejo)

# Límites del panel superior (bracket)
XLIM_TOP = (-17.5, 17.5)
YLIM_TOP = (-1.2, 14.5)

# Límites del panel inferior (3er, final, podio)
XLIM_BOT = (0.0, 36.0)
YLIM_BOT = (0.0, 11.0)

# Y de referencia dentro del panel inferior
Y_HEAD  = 9.9    # encabezados de sección
Y_CONT  = 7.7    # cajas de contendientes (semifinal-losers / finalistas)
Y_WIN   = 5.5    # caja del ganador (3er / campeón)
Y_LBL   = 4.55   # etiqueta bajo el ganador


# =====================================================================
#  ESTADO DEL TORNEO
# =====================================================================

def estado_inicial(jugadores):
    """Devuelve el estado inicial para 16 jugadores en single elimination."""
    return {
        "wb": [
            list(jugadores),   # ronda 0: 16 (octavos)
            [None] * 8,        # ronda 1: 8  (cuartos)
            [None] * 4,        # ronda 2: 4  (semis)
            [None] * 2,        # ronda 3: 2  (finalistas)
            [None] * 1,        # ronda 4: 1  (campeón)
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
    Calcula la Y del slot 'slot' en 'ronda' de forma recursiva.
    Y(r, j) = promedio de Y(r-1, 2j) e Y(r-1, 2j+1) → conectores centrados exactos.
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
    Caja redondeada de tamaño fijo.
    - Si nombre is None → caja vacía punteada semitransparente.
    - Si nombre no es None → caja rellena con texto centrado.
    Todas las cajas del bracket usan w=BOX_W, h=BOX_H para que
    los conectores sean siempre precisos.
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


def draw_box_champ(ax, cx, cy, nombre, w=5.2, h=1.15, fontsize=15):
    """
    Caja especial del campeón:
      · 2× más ancha que una caja normal → protagonismo visual máximo.
      · Alto mayor (1.15 vs 0.84).
      · Efecto de glow dorado en capas concéntricas.
      · Texto en color oro brillante.
    """
    if nombre is None:
        draw_box(ax, cx, cy, None, "empty", w=w, h=h, fontsize=fontsize, z=4)
        return
    fc, ec = C["champ"]
    # Capas de glow (de mayor a menor opacidad, de fuera adentro)
    for i in range(4, 0, -1):
        gw = w + i * 0.28
        gh = h + i * 0.18
        ax.add_patch(FancyBboxPatch(
            (cx - gw/2, cy - gh/2), gw, gh,
            boxstyle="round,pad=0.04,rounding_size=0.16",
            fc=fc, ec=ec, lw=0, alpha=0.055 * i, zorder=4
        ))
    # Caja principal
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
    Conector estándar de bracket (forma de gancho).
    Arquitectura:
      1. Horizontal en y_top: desde x_src hasta xm (punto medio del gap).
      2. Horizontal en y_bot: desde x_src hasta xm.
      3. Vertical en xm: desde y_top hasta y_bot.
      4. Horizontal en y_mid: desde xm hasta x_dst (borde de la caja siguiente).

    Nota: x_src es el borde interior de las cajas fuente;
          x_dst es el borde exterior de la caja destino.
          xm = (x_src + x_dst) / 2 garantiza que el gancho sea simétrico
          respecto al gap entre columnas, que ahora es FIJO = STEP − BOX_W = 1.3 u.
    """
    xm = (x_src + x_dst) / 2
    draw_line(ax, x_src, y_top, xm,    y_top)
    draw_line(ax, x_src, y_bot, xm,    y_bot)
    draw_line(ax, xm,    y_top, xm,    y_bot)
    draw_line(ax, xm,    y_mid, x_dst, y_mid)


def draw_match_connector_horiz(ax, xa, xb, y_cont, xc, yc_top):
    """
    Conector para un partido donde ambos contendientes están al mismo Y.
    Usado en 3er Puesto y Gran Final del panel inferior.

    Arquitectura (vista lateral, izq→der):
      A ──────┐
              │  (vertical en xc)
      B ──────┘
              │
           [ganador]

    - Línea horizontal desde borde derecho de A hasta xc.
    - Línea horizontal desde borde izquierdo de B hasta xc.
    - Línea vertical desde y_cont hacia abajo hasta yc_top (borde sup del ganador).
    """
    edge_a = xa + BOX_W / 2   # borde derecho de A
    edge_b = xb - BOX_W / 2   # borde izquierdo de B
    draw_line(ax, edge_a, y_cont, xc,     y_cont)   # A → centro
    draw_line(ax, edge_b, y_cont, xc,     y_cont)   # B → centro
    draw_line(ax, xc,     y_cont, xc, yc_top)       # vertical al ganador


def draw_medal(ax, cx, cy, pos, r=0.42):
    """
    Medalla circular con número, color de posición y etiqueta textual.
    pos=1 → Oro, pos=2 → Plata, pos=3 → Bronce.
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
    ax.text(cx, cy,          str(pos), ha="center", va="center",
            fontsize=10, fontweight="bold", color="#ffffff", zorder=7)
    ax.text(cx, cy - r - 0.16, label, ha="center", va="top",
            fontsize=7.5, fontweight="bold", color=ec, zorder=7)


def draw_section_divider(ax, x, y0=0.5, y1=10.7):
    """Línea punteada vertical que delimita las secciones del panel inferior."""
    ax.plot([x, x], [y0, y1],
            color=C["sep"], lw=1.0, ls="--", zorder=1, alpha=0.55)


# =====================================================================
#  PANEL SUPERIOR — BRACKET PRINCIPAL
# =====================================================================

def dibujar_bracket(ax, st):
    """
    Dibuja el bracket completo de 16 jugadores en el eje ax.

    Arquitectura de columnas (por lado):
      Columna  0 = OCTAVOS  x = ±13.5   (N=8 cajas)
      Columna  1 = CUARTOS  x = ± 9.5   (N=4 cajas)
      Columna  2 = SEMIS    x = ± 5.5   (N=2 cajas)
      Columna  3 = FINAL    x = ± 1.5   (N=1 caja — el finalista)

    Paso fijo entre columnas = 4.0 u. → gap entre bordes de caja = 4.0 − BOX_W = 1.3 u.
    Todos los conectores tienen exactamente el mismo ancho de gancho.
    """
    ax.set_facecolor(C["bg"])
    ax.set_xlim(*XLIM_TOP)
    ax.set_ylim(*YLIM_TOP)
    ax.axis("off")

    oct_ys   = _oct_ys()
    y_lbl    = oct_ys[0] + 1.1    # Y de etiquetas de ronda
    y_titulo = oct_ys[0] + 2.6    # Y de "LADO AZUL / LADO ROJO"
    rondas   = st["wb"]

    for lado in ("izq", "der"):
        izq      = (lado == "izq")
        xs       = XS_IZQ  if izq else XS_DER
        idx0     = 0       if izq else 8
        col_base = "azul"  if izq else "rojo"
        titulo   = "LADO AZUL" if izq else "LADO ROJO"
        dir_s    = +1 if izq else -1   # +1 conectores van a la derecha; -1 a la izquierda

        # ── Etiquetas de ronda (alineadas exactamente sobre cada columna) ──
        etiquetas = ["OCTAVOS", "CUARTOS", "SEMIFINAL", "FINAL"]
        for r, (x, lbl) in enumerate(zip(xs, etiquetas)):
            ax.text(x, y_lbl, lbl, ha="center", va="bottom",
                    fontsize=9.5, fontweight="bold", color="#7070aa")

        # ── Título del lado ──
        ax.text(xs[1], y_titulo, titulo, ha="center", va="bottom",
                fontsize=14, fontweight="bold", color="#ccccff")

        # Estilos por ronda
        estilos = {0: col_base, 1: "win", 2: "win", 3: "final_w"}

        # ── Cajas ──────────────────────────────────────────────────
        # Todas con BOX_W y FS constantes — sin variaciones por ronda.
        # Esto garantiza que los conectores siempre apunten al borde exacto.
        for r in range(4):
            n_slots = N_SIDE >> r   # 8, 4, 2, 1
            for j in range(n_slots):
                # Índice global en st["wb"][r]
                g_idx  = (idx0 >> r) + j
                nombre = rondas[r][g_idx]
                cx     = xs[r]
                cy     = _get_y(r, j, oct_ys)
                draw_box(ax, cx, cy, nombre, estilos[r])

        # ── Conectores ─────────────────────────────────────────────
        # Para cada ronda r>0, conectamos el par de cajas fuente con la caja destino.
        # x_src = borde "interior" (hacia el centro) de la caja fuente.
        # x_dst = borde "exterior" (opuesto al centro) de la caja destino.
        # El signo dir_s hace que x_src esté siempre en el lado correcto.
        for r in range(1, 4):
            n_match = N_SIDE >> r   # partidos en esta ronda
            for j in range(n_match):
                y_top = _get_y(r - 1, 2 * j,     oct_ys)
                y_bot = _get_y(r - 1, 2 * j + 1, oct_ys)
                y_mid = _get_y(r,     j,          oct_ys)
                x_src = xs[r - 1] + dir_s * (BOX_W / 2)
                x_dst = xs[r]     - dir_s * (BOX_W / 2)
                draw_bracket_connector(ax, x_src, y_top, y_bot, x_dst, y_mid)


# =====================================================================
#  PANEL INFERIOR — 3er PUESTO / GRAN FINAL / PODIO
# =====================================================================

def _subcampeon(st):
    """Finalista que perdió la Gran Final (subcampeón)."""
    fin   = st["wb"][3]
    champ = st["wb"][4][0]
    if champ is None or fin[0] is None or fin[1] is None:
        return None
    return fin[1] if champ == fin[0] else fin[0]


def dibujar_panel_inferior(ax, st):
    """
    Dibuja las tres secciones del panel inferior en el eje ax.

    Arquitectura del panel (xlim=0..36, 3 secciones de 12 u. cada una):
      Sección 1 [x: 0–12 , centro=6 ] → 3er Puesto
      Sección 2 [x: 12–24, centro=18] → Gran Final + Campeón
      Sección 3 [x: 24–36, centro=30] → Podio (Oro/Plata/Bronce/4to)

    El ancho igual (12 u.) por sección garantiza equilibrio visual.
    """
    ax.set_facecolor(C["bg"])
    ax.set_xlim(*XLIM_BOT)
    ax.set_ylim(*YLIM_BOT)
    ax.axis("off")

    sl  = st["semifinal_losers"]
    fin = st["wb"][3]

    # Líneas divisorias entre secciones
    draw_section_divider(ax, 12)
    draw_section_divider(ax, 24)

    # =================================================================
    #  SECCIÓN 1 — 3ER PUESTO  (centro x = 6)
    # =================================================================
    X3   = 6.0
    BW3  = 3.0   # ancho de cajas de contendientes en panel inferior

    # Encabezado: medalla a la izquierda del texto
    draw_medal(ax, X3 - 2.5, Y_HEAD, 3, r=0.44)
    ax.text(X3 + 0.5, Y_HEAD, "3ER PUESTO", ha="center", va="center",
            fontsize=12.5, fontweight="bold", color="#cd7f32")

    # Contendientes: semis-loser[0] (izq) y semis-loser[1] (der)
    xa3 = X3 - 2.8
    xb3 = X3 + 2.8
    draw_box(ax, xa3, Y_CONT, sl[0], "azul" if sl[0] else "empty",
             w=BW3, fontsize=10)
    draw_box(ax, xb3, Y_CONT, sl[1], "rojo" if sl[1] else "empty",
             w=BW3, fontsize=10)

    # Conector → ganador 3er puesto
    draw_match_connector_horiz(ax, xa3, xb3, Y_CONT, X3, Y_WIN + BOX_H / 2)

    # Caja del 3er puesto
    draw_box(ax, X3, Y_WIN, st["tercero"], "bronze", w=3.4, fontsize=11)
    if st["tercero"]:
        ax.text(X3, Y_LBL, "3er Puesto", ha="center", va="center",
                fontsize=9.5, fontweight="bold", color="#cd7f32")

    # =================================================================
    #  SECCIÓN 2 — GRAN FINAL  (centro x = 18)
    # =================================================================
    XF   = 18.0
    BW_F = 3.0

    # Encabezado: estrella + texto con bbox dorado
    ax.text(XF, Y_HEAD, "★  GRAN FINAL  ★", ha="center", va="center",
            fontsize=13, fontweight="bold", color="#ffd700",
            bbox=dict(boxstyle="round,pad=0.35", fc="#1a1000",
                      ec="#b8860b", lw=1.6, alpha=0.95))

    # Finalistas
    xaf = XF - 3.5
    xbf = XF + 3.5
    draw_box(ax, xaf, Y_CONT, fin[0], "azul" if fin[0] else "empty",
             w=BW_F, fontsize=10)
    draw_box(ax, xbf, Y_CONT, fin[1], "rojo" if fin[1] else "empty",
             w=BW_F, fontsize=10)

    # Conector → campeón (el borde superior del champ box usa h=1.15)
    champ_top = Y_WIN + 1.15 / 2
    draw_match_connector_horiz(ax, xaf, xbf, Y_CONT, XF, champ_top)

    # Caja del campeón (grande, con glow, texto dorado)
    draw_box_champ(ax, XF, Y_WIN, st["wb"][4][0])

    # Etiqueta y estrella decorativa
    if st["wb"][4][0]:
        ax.text(XF, Y_LBL + 0.15, "CAMPEON!", ha="center", va="center",
                fontsize=11, fontweight="bold", color="#ffd700")
        ax.text(XF, Y_LBL - 0.55, "★  ★  ★", ha="center", va="center",
                fontsize=11, color="#b8860b", zorder=3)

    # =================================================================
    #  SECCIÓN 3 — PODIO  (centro x = 30)
    # =================================================================
    XP  = 30.0
    ROW = 1.43   # separación vertical entre filas

    ax.text(XP, Y_HEAD, "PODIO", ha="center", va="center",
            fontsize=13, fontweight="bold", color="#ffffff")
    ax.plot([25.5, 34.5], [Y_HEAD - 0.52, Y_HEAD - 0.52],
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
            draw_medal(ax, 25.8, yp, pos, r=0.39)
        else:
            ax.text(25.8, yp, "4to", ha="center", va="center",
                    fontsize=9, fontweight="bold", color=color_lbl, zorder=5)

        ax.text(26.9, yp + 0.10, lbl, ha="left", va="center",
                fontsize=10.5, fontweight="bold", color=color_lbl)

        draw_box(ax, 32.0, yp, nombre, estilo if nombre else "empty",
                 w=4.6, fontsize=10, z=3)


# =====================================================================
#  RENDER PRINCIPAL
# =====================================================================

def render(st, banner=None, ruta=None, dpi=130):
    """
    Genera la imagen completa del torneo.

    Figura: 34 × 20 pulgadas a 130 DPI = 4420 × 2600 px.
    Layout (gridspec):
      - ax_top (65%): bracket principal
      - ax_bot (35%): 3er puesto / gran final / podio

    dpi=130 mejora la nitidez respecto al anterior dpi=90–120.
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
        fontsize=22, fontweight="bold", color="#dde0ff",
        y=0.97, fontfamily="DejaVu Sans",
    )

    # Banner de estado (SET actual, retroceso, etc.)
    if banner:
        fig.text(
            0.5, 0.935, banner,
            ha="center", va="top",
            fontsize=12, fontweight="bold", color="#ffe08a",
            bbox=dict(boxstyle="round,pad=0.4",
                      fc="#140f00", ec="#b8860b", lw=1.6),
        )

    if ruta:
        fig.savefig(ruta, bbox_inches="tight", dpi=dpi,
                    facecolor=C["bg"], pad_inches=0.12)
    plt.close(fig)


# =====================================================================
#  LÓGICA DEL TORNEO (sin cambios respecto a v3)
# =====================================================================

def pedir_ganador(p1, p2, etiqueta):
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
    if out_dir is None:
        try:    out_dir = os.path.dirname(os.path.abspath(__file__))
        except: out_dir = os.getcwd()
    os.makedirs(out_dir, exist_ok=True)
    ruta_actual = os.path.join(out_dir, "actual.png")

    partidos     = _construir_partidos(jugadores)
    st           = estado_inicial(jugadores)
    historial    = []
    sets_jugados = 0

    render(st, banner="Esperando el primer set...", ruta=ruta_actual)
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
                print("  Partido deshecho.")
                render(st, banner=f"Retrocedido - SET {sets_jugados}", ruta=ruta_actual)
            continue

        ganador, perdedor = resultado
        historial.append((copy.deepcopy(st), idx))
        _aplicar(st, p, ganador, perdedor)
        sets_jugados += 1
        render(st,
               banner=f"SET {sets_jugados} - {p['label']}: avanzo {ganador}",
               ruta=ruta_actual)
        print(f"  Avanza: {ganador}")
        idx += 1

    print(f"\n{'='*60}")
    print("  TORNEO FINALIZADO")
    print(f"  1. Campeon:  {st['wb'][4][0]}")
    print(f"  2. 2do:      {_subcampeon(st)}")
    print(f"  3. 3er:      {st['tercero']}")
    print(f"  4. 4to:      {st['cuarto']}")
    print(f"  Imagen: {ruta_actual}")
    print("="*60)


# =====================================================================
#  PARTIDOS DECLARATIVOS
# =====================================================================

def _construir_partidos(jugadores):
    """Construye la lista ordenada de partidos para single elimination."""
    partidos = []

    # Octavos, cuartos, semis
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

    # Partido por el 3er puesto
    partidos.append({
        "etapa":    "3ER PUESTO",
        "label":    "Partido 3er Puesto",
        "src1":     "semi_loser[0]",
        "src2":     "semi_loser[1]",
        "dst_win":  "tercero",
        "dst_lose": "cuarto",
        "ronda":    "3p",
    })

    # Gran Final
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
    correr_torneo(JUGADORES)
