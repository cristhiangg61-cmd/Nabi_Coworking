import re
import os
import sys
import copy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# =====================================================================
#  TORNEO ELIMINACIÓN DIRECTA — 16 JUGADORES
#  · Control manual de quién avanza en cada partido
#  · Opción de RETROCEDER al partido anterior
#  · Imagen "actual.png" que se SOBRESCRIBE en cada set
#  · 3er puesto primero, luego Gran Final
# =====================================================================

JUGADORES = [
    "Jugador 1",  "Jugador 2",  "Jugador 3",  "Jugador 4",
    "Jugador 5",  "Jugador 6",  "Jugador 7",  "Jugador 8",
    "Jugador 9",  "Jugador 10", "Jugador 11", "Jugador 12",
    "Jugador 13", "Jugador 14", "Jugador 15", "Jugador 16",
]

# ─────────────────────── Paleta de colores ───────────────────────
C = {
    "bg":      "#0d0d1a",
    "panel":   "#1a1a2e",
    "border":  "#16213e",
    "azul":    ("#1a4a8a", "#4d9fff"),
    "rojo":    ("#8a1a1a", "#ff4d4d"),
    "win":     ("#1a5c2e", "#50e87a"),
    "final_w": ("#6b3a00", "#ffb347"),
    "champ":   ("#5c4500", "#ffd700"),
    "bronze":  ("#4a2800", "#cd7f32"),
    "empty":   ("#111122", "#2a2a4a"),
    "line":    "#3a3a6a",
}

BOX_W = 2.2
BOX_H = 0.60


# =====================================================================
#  ESTADO DEL TORNEO
# =====================================================================

def estado_inicial(jugadores):
    return {
        "wb": [
            list(jugadores),  # ronda 0: 16 jugadores (octavos)
            [None] * 8,       # ronda 1: cuartos
            [None] * 4,       # ronda 2: semis
            [None] * 2,       # ronda 3: finalistas
            [None] * 1,       # ronda 4: campeón
        ],
        "semifinal_losers": [None, None],
        "tercero": None,
        "cuarto":  None,
    }


# =====================================================================
#  PRIMITIVAS DE DIBUJO
# =====================================================================

def draw_box(ax, cx, cy, nombre, estilo, w=BOX_W, h=BOX_H, fontsize=8.5):
    if nombre is None:
        fc, ec = C["empty"]
        alpha = 0.5
        txt_color = "#3a3a6a"
        ls = "--"
        display = ""
    else:
        fc, ec = C[estilo]
        alpha = 1.0
        txt_color = "#ffffff"
        ls = "solid"
        display = nombre

    patch = FancyBboxPatch(
        (cx - w/2, cy - h/2), w, h,
        boxstyle="round,pad=0.05,rounding_size=0.08",
        fc=fc, ec=ec, lw=1.5, ls=ls, alpha=alpha, zorder=3
    )
    ax.add_patch(patch)
    if display:
        ax.text(cx, cy, display, ha="center", va="center", zorder=4,
                fontsize=fontsize, color=txt_color, fontweight="bold",
                clip_on=True)


def draw_line(ax, x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], color=C["line"], lw=1.3, zorder=1,
            solid_capstyle="round")


def bracket_connector(ax, x_src, y_top, y_bot, x_dst, y_mid, flip=False):
    """
    Dibuja el conector en forma de ⌐ entre dos cajas y la siguiente.
    flip=True para el lado derecho (conectores van de derecha a izquierda).
    """
    xm = (x_src + x_dst) / 2
    draw_line(ax, x_src, y_top, xm,    y_top)
    draw_line(ax, x_src, y_bot, xm,    y_bot)
    draw_line(ax, xm,    y_top, xm,    y_bot)
    draw_line(ax, xm,    y_mid, x_dst, y_mid)


# =====================================================================
#  DIBUJO DE UN LADO DEL BRACKET (izquierdo o derecho)
# =====================================================================

def dibujar_lado(ax, st, lado):
    """
    lado = "izq" | "der"
    izq : jugadores 0-7, columnas crecen hacia la derecha
    der : jugadores 8-15, columnas crecen hacia la izquierda
    """
    rondas = st["wb"]
    N = 8          # jugadores por lado
    idx0 = 0 if lado == "izq" else 8

    # ── Posiciones X de cada ronda ──
    # Ronda 0 (octavos) más al exterior; ronda 3 (final) en el centro
    if lado == "izq":
        xs = [-12.5, -9.0, -5.5, -2.2]  # octavos → semifinal → final
        color_base = "azul"
        titulo = "LADO AZUL"
        dir_sign = +1   # conectores van hacia la derecha
    else:
        xs = [12.5,  9.0,  5.5,  2.2]
        color_base = "rojo"
        titulo = "LADO ROJO"
        dir_sign = -1

    GAP_Y = 1.10   # separación vertical entre jugadores en octavos

    # Posiciones Y de octavos (de arriba a abajo: 0..7)
    oct_ys = [(N - 1 - i) * GAP_Y for i in range(N)]

    # Calcular Y de cada partido (promedio de sus dos participantes)
    def get_y(ronda, j_local):
        if ronda == 0:
            return oct_ys[j_local]
        ya = get_y(ronda - 1, 2 * j_local)
        yb = get_y(ronda - 1, 2 * j_local + 1)
        return (ya + yb) / 2

    # ── Etiquetas de ronda ──
    etiquetas_ronda = ["OCTAVOS", "CUARTOS", "SEMIFINAL", "FINAL"]
    y_header = oct_ys[0] + 1.3
    for r, (x, et) in enumerate(zip(xs, etiquetas_ronda)):
        ax.text(x, y_header, et, ha="center", va="bottom",
                fontsize=8.5, fontweight="bold", color="#8888cc")

    # Título del lado
    ax.text(xs[1], y_header + 1.0, titulo, ha="center", va="bottom",
            fontsize=13, fontweight="bold", color="#ccccff")

    # ── Cajas ──
    estilos = {0: color_base, 1: "win", 2: "win", 3: "final_w"}

    for r in range(4):
        n_partidos = N >> r
        for j in range(n_partidos):
            cx = xs[r]
            cy = get_y(r, j)
            g_idx = idx0 // (2 ** r) + j if r > 0 else idx0 + j
            nombre = rondas[r][g_idx]
            estilo = estilos[r]
            fs = 9.0 if r == 3 else 8.5
            bw = BOX_W * 1.1 if r == 3 else BOX_W
            draw_box(ax, cx, cy, nombre, estilo, w=bw, fontsize=fs)

    # ── Conectores ──
    for r in range(1, 4):
        n = N >> r
        for j in range(n):
            ya = get_y(r - 1, 2 * j)
            yb = get_y(r - 1, 2 * j + 1)
            ym = get_y(r, j)
            x_src = xs[r - 1] + dir_sign * BOX_W / 2
            x_dst = xs[r]     - dir_sign * BOX_W / 2
            bracket_connector(ax, x_src, ya, yb, x_dst, ym)


# =====================================================================
#  PANEL INFERIOR: 3er puesto + Gran Final + Podio
# =====================================================================

def _subcampeon(st):
    fin   = st["wb"][3]
    champ = st["wb"][4][0]
    if champ is None or fin[0] is None or fin[1] is None:
        return None
    return fin[1] if champ == fin[0] else fin[0]


def dibujar_panel_inferior(ax, st):
    ax.set_facecolor(C["bg"])
    ax.set_xlim(0, 30)        # Canvas centrado y bien espaciado
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    # ─── 3ER PUESTO ───────────────────────────────────────────────
    ax.text(5.0, 8.0, "[  3  ]  3ER PUESTO", ha="center", fontsize=12,
            fontweight="bold", color="#cd7f32")

    sl = st["semifinal_losers"]
    draw_box(ax, 2.0, 6.5, sl[0], "azul" if sl[0] else "empty", w=2.8, fontsize=9)
    draw_box(ax, 8.0, 6.5, sl[1], "rojo" if sl[1] else "empty", w=2.8, fontsize=9)

    # Conector
    draw_line(ax, 3.4, 6.5, 5.0, 6.5)
    draw_line(ax, 6.6, 6.5, 5.0, 6.5)
    draw_line(ax, 5.0, 6.5, 5.0, 5.5)
    draw_box(ax, 5.0, 4.9, st["tercero"], "bronze", w=3.5, fontsize=9.5)

    if st["tercero"]:
        ax.text(5.0, 4.0, "3° Puesto", ha="center", fontsize=9,
                fontweight="bold", color="#cd7f32")

    # ─── GRAN FINAL ───────────────────────────────────────────────
    ax.text(15.0, 8.0, "* GRAN FINAL *", ha="center", fontsize=12,
            fontweight="bold", color="#ffd700")

    fin = st["wb"][3]
    draw_box(ax, 11.5,  6.5, fin[0], "azul" if fin[0] else "empty", w=2.8, fontsize=9)
    draw_box(ax, 18.5, 6.5, fin[1], "rojo" if fin[1] else "empty", w=2.8, fontsize=9)

    draw_line(ax, 12.9, 6.5, 15.0, 6.5)
    draw_line(ax, 17.1, 6.5, 15.0, 6.5)
    draw_line(ax, 15.0, 6.5, 15.0, 5.5)
    draw_box(ax, 15.0, 4.9, st["wb"][4][0], "champ", w=4.0, fontsize=11)

    if st["wb"][4][0]:
        ax.text(15.0, 4.0, "¡CAMPEÓN!", ha="center", fontsize=10,
                fontweight="bold", color="#ffd700")

    # ─── PODIO ────────────────────────────────────────────────────
    ax.text(25.0, 8.0, "[  PODIO  ]", ha="center", fontsize=12,
            fontweight="bold", color="#ffffff")

    podio = [
        (" 1  1er", st["wb"][4][0],  "champ"),
        (" 2  2do", _subcampeon(st), "final_w"),
        (" 3  3er", st["tercero"],    "bronze"),
        ("     4to", st["cuarto"],    "empty"),
    ]
    for k, (label, nombre, estilo) in enumerate(podio):
        yp = 6.5 - k * 1.35
        ax.text(22.0, yp, label, ha="left", va="center",
                fontsize=9, fontweight="bold", color="#aaaacc")
        draw_box(ax, 25.5, yp, nombre, estilo if nombre else "empty",
                 w=3.8, fontsize=9)


# =====================================================================
#  RENDER PRINCIPAL
# =====================================================================

def render(st, banner=None, ruta=None, dpi=100):
    fig = plt.figure(figsize=(32, 18), facecolor=C["bg"])
    gs = fig.add_gridspec(2, 1, height_ratios=[2.3, 1.0], hspace=0.08)

    ax_top = fig.add_subplot(gs[0])
    ax_bot = fig.add_subplot(gs[1])

    # ── Panel superior: bracket ──
    ax_top.set_facecolor(C["bg"])
    ax_top.set_xlim(-15, 15)
    ax_top.set_ylim(-3.0, 10.5)
    ax_top.axis("off")

    dibujar_lado(ax_top, st, "izq")
    dibujar_lado(ax_top, st, "der")

    # ── Panel inferior ──
    ax_bot.set_ylim(-1.5, 8.5)
    dibujar_panel_inferior(ax_bot, st)

    # ── Título principal ──
    fig.suptitle("TORNEO 16 JUGADORES — ELIMINACION DIRECTA",
                 fontsize=20, fontweight="bold", color="#e0e0ff",
                 y=0.94, fontfamily="DejaVu Sans")

    if banner:
        fig.text(0.5, 0.90, banner, ha="center", fontsize=12,
                 fontweight="bold", color="#ffe08a",
                 bbox=dict(boxstyle="round,pad=0.4", fc="#1a1400",
                           ec="#b8860b", lw=1.5))

    if ruta:
        fig.savefig(ruta, bbox_inches="tight", dpi=dpi, facecolor=C["bg"])
    plt.close(fig)


# =====================================================================
#  LÓGICA DEL TORNEO
# =====================================================================

def pedir_ganador(p1, p2, etiqueta):
    print(f"\n  ─── {etiqueta} ───")
    print(f"  [1]  {p1}")
    print(f"  [2]  {p2}")
    print(f"  [0]  ↩  RETROCEDER")
    while True:
        raw = input("  ¿Quién avanza? (1 / 2 / 0): ").strip()
        if raw == "0":
            return "RETROCEDER"
        if raw == "1":
            return p1, p2
        if raw == "2":
            return p2, p1
        print("  ⚠  Ingresa 1, 2 ó 0.")


def correr_torneo(jugadores, out_dir=None):
    if out_dir is None:
        try:
            out_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            out_dir = os.getcwd()
    os.makedirs(out_dir, exist_ok=True)
    ruta_actual = os.path.join(out_dir, "actual.png")

    partidos = _construir_partidos(jugadores)
    st = estado_inicial(jugadores)
    historial = []
    sets_jugados = 0

    render(st, banner="Esperando el primer set...", ruta=ruta_actual, dpi=90)
    print("\n" + "═"*60)
    print("  TORNEO 16 JUGADORES — ELIMINACIÓN DIRECTA")
    print("  Ingresa [0] en cualquier momento para RETROCEDER")
    print("═"*60)

    idx = 0
    while idx < len(partidos):
        p = partidos[idx]
        n1 = _resolver(st, p["src1"])
        n2 = _resolver(st, p["src2"])

        if n1 is None or n2 is None:
            idx += 1
            continue

        _header(p["etapa"])
        resultado = pedir_ganador(n1, n2, p["label"])

        if resultado == "RETROCEDER":
            if not historial:
                print("  ⚠  No hay partidos anteriores para deshacer.")
            else:
                st, prev_idx = historial.pop()
                idx = prev_idx
                sets_jugados = max(0, sets_jugados - 1)
                print("  ✅ Partido deshecho.")
                render(st, banner=f"↩ Retrocedido — SET {sets_jugados}",
                       ruta=ruta_actual, dpi=90)
            continue

        ganador, perdedor = resultado
        historial.append((copy.deepcopy(st), idx))
        _aplicar(st, p, ganador, perdedor)
        sets_jugados += 1
        banner = f"SET {sets_jugados} — {p['label']}:  avanzó → {ganador}"
        render(st, banner=banner, ruta=ruta_actual, dpi=90)
        print(f"  ✅ Avanza: {ganador}")
        idx += 1

    print("\n" + "═"*60)
    print("  🏆  TORNEO FINALIZADO")
    print(f"  🥇 Campeón:   {st['wb'][4][0]}")
    print(f"  🥈 2°:        {_subcampeon(st)}")
    print(f"  🥉 3°:        {st['tercero']}")
    print(f"     4°:        {st['cuarto']}")
    print(f"\n  Imagen final → {ruta_actual}")
    print("═"*60)


# =====================================================================
#  PARTIDOS DECLARATIVOS
# =====================================================================

def _construir_partidos(jugadores):
    partidos = []

    for r, (etapa, n_pares) in enumerate([
        ("OCTAVOS DE FINAL", 8),
        ("CUARTOS DE FINAL", 4),
        ("SEMIFINALES",      2),
    ]):
        for i in range(n_pares):
            partidos.append({
                "etapa":    etapa,
                "label":    f"{etapa.title()} — Partido {i+1}",
                "src1":     f"wb[{r}][{2*i}]",
                "src2":     f"wb[{r}][{2*i+1}]",
                "dst_win":  f"wb[{r+1}][{i}]",
                "dst_lose": f"semi_loser[{i}]" if r == 2 else None,
                "ronda":    r,
            })

    # 3er puesto
    partidos.append({
        "etapa":    "3ER PUESTO (antes de la Gran Final)",
        "label":    "Partido por el 3er Puesto",
        "src1":     "semi_loser[0]",
        "src2":     "semi_loser[1]",
        "dst_win":  "tercero",
        "dst_lose": "cuarto",
        "ronda":    "3p",
    })

    # Gran Final
    partidos.append({
        "etapa":    "🏆 GRAN FINAL",
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
        r, i = map(int, re.findall(r'\d+', src))
        return st["wb"][r][i]
    if src.startswith("semi_loser["):
        i = int(re.findall(r'\d+', src)[0])
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
        r, i = map(int, re.findall(r'\d+', dst))
        st["wb"][r][i] = valor
    elif dst.startswith("semi_loser["):
        i = int(re.findall(r'\d+', dst)[0])
        st["semifinal_losers"][i] = valor
    elif dst == "tercero":
        st["tercero"] = valor
    elif dst == "cuarto":
        st["cuarto"] = valor


def _header(texto):
    print(f"\n{'═'*60}")
    print(f"  {texto}")
    print(f"{'═'*60}")


# =====================================================================
if __name__ == "__main__":
    correr_torneo(JUGADORES)