/* ============================================================
   MENÚ HAMBURGUESA UNIFICADO · Torneo BeaNabi / Team Crow Power
   Auto-inyectable: cada página solo necesita incluir
       <script src="menu.js"></script>
   antes de cerrar </body>. No requiere CSS extra.
   ============================================================ */
(function () {
  "use strict";

  /* --- Estructura del menú --------------------------------- */
  var INICIO = { etiqueta: "🏠 Inicio", href: "index.html" };

  var GRUPOS = [
    {
      titulo: "Torneo 1 VS 1",
      icono: "⚔️",
      items: [
        { etiqueta: "🏆 Bracket",     href: "pagina_2torneo.html" },
        { etiqueta: "⏱️ Reloj",        href: "paginareloj.html" },
        { etiqueta: "📝 Inscripción",  href: "index_inscripción.html" }
      ]
    },
    {
      titulo: "Torneo 2 VS 2",
      icono: "👥",
      items: [
        { etiqueta: "🏆 Bracket",      href: "bracket_2vs2.html" },
        { etiqueta: "⏱️ Reloj",         href: "pagina_reloj_2vs2.html" },
        { etiqueta: "📝 Inscripción",   href: "index_inscripción_2vs2.html" },
        { etiqueta: "🔮 Predicciones",  href: "Predicciones_2vs2.html" }
      ]
    }
  ];

  /* --- Página actual (para resaltar) ----------------------- */
  var actual = (window.location.pathname.split("/").pop() || "index.html");
  try { actual = decodeURIComponent(actual); } catch (e) {}
  if (actual === "") actual = "index.html";

  function esActivo(href) {
    var f = href.split("/").pop();
    try { f = decodeURIComponent(f); } catch (e) {}
    return f.toLowerCase() === actual.toLowerCase();
  }

  /* --- Estilos --------------------------------------------- */
  var css = `
  .tcp-nav{
    position:sticky; top:0; z-index:600;
    display:flex; align-items:center; justify-content:space-between;
    height:56px; padding:0 18px;
    background:rgba(13,11,43,.92);
    backdrop-filter:blur(14px);
    border-bottom:1px solid rgba(255,255,255,.15);
    font-family:'Nunito',system-ui,sans-serif;
  }
  .tcp-brand{
    font-family:'Lilita One','Nunito',cursive;
    font-size:1.1rem; color:#ffd23f; text-decoration:none;
    white-space:nowrap;
  }
  .tcp-burger{
    display:flex; flex-direction:column; gap:5px;
    width:42px; height:42px; align-items:center; justify-content:center;
    background:rgba(255,255,255,.06);
    border:1px solid rgba(255,255,255,.15);
    border-radius:12px; cursor:pointer;
  }
  .tcp-burger span{
    display:block; width:22px; height:3px; border-radius:2px;
    background:#fff; transition:transform .3s, opacity .3s;
  }
  .tcp-nav.tcp-open .tcp-burger span:nth-child(1){ transform:translateY(8px) rotate(45deg); }
  .tcp-nav.tcp-open .tcp-burger span:nth-child(2){ opacity:0; }
  .tcp-nav.tcp-open .tcp-burger span:nth-child(3){ transform:translateY(-8px) rotate(-45deg); }

  .tcp-overlay{
    position:fixed; inset:0; z-index:590;
    background:rgba(0,0,0,.55); backdrop-filter:blur(2px);
    opacity:0; visibility:hidden; transition:opacity .3s;
  }
  .tcp-overlay.tcp-show{ opacity:1; visibility:visible; }

  .tcp-drawer{
    position:fixed; top:0; right:0; z-index:610;
    width:280px; max-width:84vw; height:100%;
    background:linear-gradient(180deg,#15102f,#0d0b2b);
    border-left:1px solid rgba(255,255,255,.15);
    box-shadow:-12px 0 40px rgba(0,0,0,.5);
    transform:translateX(105%); transition:transform .32s cubic-bezier(.22,1,.36,1);
    display:flex; flex-direction:column; padding:18px 16px 28px;
    overflow-y:auto; font-family:'Nunito',system-ui,sans-serif;
  }
  .tcp-drawer.tcp-show{ transform:translateX(0); }

  .tcp-drawer-head{
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:8px;
  }
  .tcp-drawer-title{
    font-family:'Lilita One','Nunito',cursive; color:#ffd23f; font-size:1.05rem;
  }
  .tcp-close{
    width:34px; height:34px; border-radius:50%;
    background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.15);
    color:#fff; font-size:1.1rem; cursor:pointer; line-height:1;
  }
  .tcp-close:hover{ background:#ff3d81; }

  .tcp-home{
    display:block; text-decoration:none; color:#fff; font-weight:800;
    background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.15);
    border-radius:12px; padding:11px 14px; margin:10px 0 4px;
    transition:background .2s, color .2s;
  }
  .tcp-home:hover, .tcp-home.tcp-activo{ background:#2ec5ff; color:#fff; }

  .tcp-group{ margin-top:16px; }
  .tcp-group-title{
    font-family:'Lilita One','Nunito',cursive;
    font-size:.95rem; letter-spacing:.5px;
    color:#2ec5ff; text-transform:uppercase;
    padding:0 4px 8px; border-bottom:1px solid rgba(255,255,255,.12);
    margin-bottom:10px; display:flex; align-items:center; gap:8px;
  }
  .tcp-link{
    display:block; text-decoration:none; color:#cdd3ff; font-weight:700;
    padding:10px 14px; border-radius:11px; margin-bottom:7px;
    border:1px solid transparent; transition:background .2s, color .2s, transform .15s;
  }
  .tcp-link:hover{ background:rgba(46,197,255,.18); color:#fff; transform:translateX(4px); }
  .tcp-link.tcp-activo{
    background:#2ec5ff; color:#fff; border-color:rgba(255,255,255,.25);
  }

  .tcp-foot{
    margin-top:auto; padding-top:18px; font-size:.72rem; color:#7c82b8;
    text-align:center; line-height:1.5;
  }
  `;

  /* --- Construcción del DOM -------------------------------- */
  function build() {
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    /* Barra superior */
    var nav = document.createElement("nav");
    nav.className = "tcp-nav";
    nav.innerHTML =
      '<a class="tcp-brand" href="index.html">🐦 Team Crow Power</a>' +
      '<button class="tcp-burger" id="tcpBurger" aria-label="Abrir menú" aria-expanded="false">' +
        '<span></span><span></span><span></span>' +
      '</button>';

    /* Overlay */
    var overlay = document.createElement("div");
    overlay.className = "tcp-overlay";
    overlay.id = "tcpOverlay";

    /* Drawer */
    var drawer = document.createElement("aside");
    drawer.className = "tcp-drawer";
    drawer.id = "tcpDrawer";

    var html = "" +
      '<div class="tcp-drawer-head">' +
        '<span class="tcp-drawer-title">Menú</span>' +
        '<button class="tcp-close" id="tcpClose" aria-label="Cerrar menú">✕</button>' +
      '</div>' +
      '<a class="tcp-home' + (esActivo(INICIO.href) ? ' tcp-activo' : '') + '" href="' +
        INICIO.href + '">' + INICIO.etiqueta + '</a>';

    GRUPOS.forEach(function (g) {
      html += '<div class="tcp-group">';
      html += '<div class="tcp-group-title">' + g.icono + ' ' + g.titulo + '</div>';
      g.items.forEach(function (it) {
        html += '<a class="tcp-link' + (esActivo(it.href) ? ' tcp-activo' : '') +
                '" href="' + it.href + '">' + it.etiqueta + '</a>';
      });
      html += '</div>';
    });

    html += '<div class="tcp-foot">Team Crow Power · Torneo BeaNabi<br>Página de fans · sin fines de lucro</div>';
    drawer.innerHTML = html;

    document.body.insertBefore(nav, document.body.firstChild);
    document.body.appendChild(overlay);
    document.body.appendChild(drawer);

    /* --- Comportamiento --- */
    var burger = document.getElementById("tcpBurger");
    var close  = document.getElementById("tcpClose");

    function abrir() {
      nav.classList.add("tcp-open");
      overlay.classList.add("tcp-show");
      drawer.classList.add("tcp-show");
      burger.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";
    }
    function cerrar() {
      nav.classList.remove("tcp-open");
      overlay.classList.remove("tcp-show");
      drawer.classList.remove("tcp-show");
      burger.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    }
    function toggle() {
      if (drawer.classList.contains("tcp-show")) cerrar(); else abrir();
    }

    burger.addEventListener("click", toggle);
    close.addEventListener("click", cerrar);
    overlay.addEventListener("click", cerrar);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") cerrar();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
