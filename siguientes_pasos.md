# Siguientes pasos — Torneos Brawl Stars
_Última actualización: 17 jun 2026_

---

## Plantillas creadas en esta sesión

### Bracket viewers (12 archivos)
`bracket_A.html` · `bracket_B.html` · `bracket_C.html` · `bracket_D.html`
`bracket_E.html` · `bracket_F.html` · `bracket_G.html` · `bracket_H.html`
`bracket_I.html` · `bracket_J.html` · `bracket_K.html` · `bracket_L.html`

Basados en `pagina_2torneo.html`. Cada uno ya tiene:
- Título actualizado (`Bracket A`, `Bracket B`, etc.)
- Subtítulo con la fecha y hora correcta del evento
- Referencia a su propia imagen: `imagenes/bracket_A.png`, `imagenes/bracket_B.png`, etc.

**Lo que falta en cada bracket viewer:**
- Generar la imagen `imagenes/bracket_X.png` corriendo `Torneo_BeaNabi.py` con los jugadores reales de ese bracket y guardando el resultado con el nombre correcto.

### Relojes de cuenta regresiva (3 archivos)
| Archivo | Fecha programada | Brackets |
|---|---|---|
| `reloj_tanda1.html` | Sáb 21 jun 2026, 17:00 | A, B, C, D |
| `reloj_tanda2.html` | Sáb 28 jun 2026, 17:00 | E, F, G, H |
| `reloj_tanda3.html` | Lun 30 jun 2026, 17:00 | I, J, K, L |

Basados en `paginareloj.html`. Ya tienen la `FECHA_TORNEO` correcta por tanda.

**Lo que falta:** ajustar la hora exacta de inicio si no es a las 17:00 (actualmente puesta como placeholder).

### Inscripción
No se duplicó — se reutiliza `index_inscripción.html` para todos los brackets.
El formulario ya tiene los campos correctos y va a Google Sheets vía Apps Script.

---

## Tarea A pendiente — Archivar el 2 VS 2 en index.html

El torneo 2 VS 2 ya terminó y el premio ($15 USD) fue entregado.

**Qué hacer:**
- En `index.html`, convertir la sección `<section class="torneo dos">` a una apariencia de "historial":
  - Cambiar la etiqueta de `👥 Modalidad por equipos` a `📜 FINALIZADO`
  - Desaturar el color de acentos (de rosa `#ff3d81` a gris `#888`)
  - Reemplazar la cuadrícula de 4 accesos por un resumen compacto: equipo campeón + premio entregado + fecha
  - Dejar un solo enlace discreto "Ver bracket final" apuntando al `bracket_2vs2.html` existente (no borrar ese archivo)
- En `menu.js`, mover/renombrar el grupo 2 VS 2 a "📜 Archivo · 2 VS 2" al final de la navegación

---

## Contexto del calendario de premios

| Premio | Cantidad | Fecha límite de entrega | Expiración real |
|---|---|---|---|
| Siamese Kit | 12 | **6 jul 2026** | ~16 jul 2026 |
| Brawl Pass | 1 | **31 jul 2026** | ~10 ago 2026 |

Estructura de torneos:
- **Tanda 1** (21–22 jun): Brackets A, B, C, D — 1 Kit por bracket
- **Tanda 2** (28–29 jun): Brackets E, F, G, H — 1 Kit por bracket
- **Tanda 3** (30 jun – 1 jul): Brackets I, J, K, L — 1 Kit por bracket
- **Gran Final** (25–27 jul): Torneo #13, 1 Brawl Pass

La inscripción para Tandas 1 y 2 abre hoy (16 jun). Cierre Tanda 1: jue 19 jun.

---

## Flujo para activar un bracket nuevo

1. Recolectar 16 inscritos.
2. Editar `JUGADORES` en `imagenes/Torneo_BeaNabi.py` con los nombres reales.
3. Correr el script: genera `imagenes/actual.png`.
4. Renombrar/copiar esa imagen como `imagenes/bracket_X.png`.
5. Hacer push a GitHub → `bracket_X.html` ya apunta a esa imagen.

---

## Archivos existentes que NO se deben borrar

Estos archivos del torneo 2vs2 ya no están en el flujo principal pero siguen siendo accesibles por link directo:
`bracket_2vs2.html` · `pagina_reloj_2vs2.html` · `index_inscripción_2vs2.html` · `Predicciones_2vs2.html`
