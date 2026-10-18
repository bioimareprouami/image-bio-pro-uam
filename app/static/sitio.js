// Selector de idioma ES/EN con el traductor de Google (RF-03).
// El traductor lee la cookie "googtrans" (idioma origen / idioma destino) al cargar la página.
function idiomaActual() {
  const cookie = document.cookie.split("; ").find((c) => c.startsWith("googtrans="));
  return cookie && cookie.endsWith("/en") ? "en" : "es";
}

function cambiarIdioma(idioma) {
  const vencida = "expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
  // Google también la guarda con el dominio; se borran ambas
  document.cookie = `googtrans=; ${vencida}`;
  document.cookie = `googtrans=; ${vencida}; domain=${location.hostname}`;
  document.cookie = `googtrans=; ${vencida}; domain=.${location.hostname}`;
  if (idioma === "en") {
    document.cookie = "googtrans=/es/en; path=/";
  }
  location.reload();
}

function iniciarTraductor() {
  new google.translate.TranslateElement(
    { pageLanguage: "es", includedLanguages: "en,es", autoDisplay: false },
    "google_translate_element"
  );
}

document.addEventListener("DOMContentLoaded", () => {
  const actual = idiomaActual();
  document.querySelectorAll("[data-idioma]").forEach((enlace) => {
    if (enlace.dataset.idioma === actual) enlace.classList.add("fw-bold");
    enlace.addEventListener("click", (evento) => {
      evento.preventDefault();
      cambiarIdioma(enlace.dataset.idioma);
    });
  });

  // Cubierta con barra de progreso mientras se analiza (RF-36)
  document.querySelectorAll("form[data-analisis]").forEach((formulario) => {
    formulario.addEventListener("submit", () => {
      document.getElementById("cubierta-analisis").classList.add("visible");
      iniciarTemporizador();
    });
  });

  iniciarVisorZoom();
  iniciarDetalleEsperma();

  // Ventana de infografías: pone la imagen, el título y el texto de la elegida (RF-07)
  const ventana = document.getElementById("ventana");
  if (ventana) {
    ventana.addEventListener("show.bs.modal", (evento) => {
      const origen = evento.relatedTarget;
      if (!origen) return;
      document.getElementById("ventana-titulo").textContent = origen.dataset.titulo;
      document.getElementById("ventana-texto").textContent = origen.dataset.texto;
      const imagen = document.getElementById("ventana-imagen");
      imagen.innerHTML = origen.dataset.imagen
        ? `<img class="img-fluid" src="${origen.dataset.imagen}" alt="">`
        : `<div class="ph" style="height: 340px">[${origen.dataset.titulo} en grande]</div>`;
    });
  }
});

// Temporizador de la pantalla de espera. Solo existe en desarrollo (MOSTRAR_TEMPORIZADOR=1): si el elemento
// no está en la página, no hace nada.
function iniciarTemporizador() {
  const etiqueta = document.getElementById("temporizador-analisis");
  if (!etiqueta) return;
  const inicio = Date.now();
  const poner = () => {
    const s = Math.floor((Date.now() - inicio) / 1000);
    etiqueta.firstChild.textContent = `Tiempo: ${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")} `;
  };
  poner();
  setInterval(poner, 250);
}

// Visor con zoom de la imagen marcada (pantalla de resultados). Rueda del ratón o botones para acercar, arrastrar para
// moverse, doble clic para acercar o volver, y dos dedos en pantallas táctiles.
function iniciarVisorZoom() {
  const ventana = document.getElementById("visor-zoom");
  if (!ventana) return;
  const vista = ventana.querySelector(".visor-vista");
  const lienzo = ventana.querySelector(".visor-lienzo");
  const imagen = lienzo.querySelector("img");
  const MAXIMO = 12;
  let ajuste = 1;                 // píxeles de pantalla por píxel de la imagen cuando la imagen cabe entera
  let escala = 1;                 // 1 = la imagen cabe entera; más es acercar
  let x = 0, y = 0;               // esquina de la imagen dentro de la vista, en píxeles de pantalla
  const punteros = new Map();
  let distanciaPrevia = null;

  const tam = () => ({ ancho: imagen.naturalWidth * ajuste, alto: imagen.naturalHeight * ajuste });
  function limitar() {
    const t = tam(), vw = vista.clientWidth, vh = vista.clientHeight;
    const w = t.ancho * escala, h = t.alto * escala;
    x = w <= vw ? (vw - w) / 2 : Math.min(0, Math.max(vw - w, x));      // si cabe, centrada; si no, sin dejar huecos
    y = h <= vh ? (vh - h) / 2 : Math.min(0, Math.max(vh - h, y));
  }
  function aplicar() {
    limitar();
    lienzo.style.transform = `translate(${x}px, ${y}px) scale(${escala})`;
  }
  function ajustar() {
    const vw = vista.clientWidth, vh = vista.clientHeight;
    ajuste = Math.min(vw / imagen.naturalWidth, vh / imagen.naturalHeight);
    imagen.style.width = `${imagen.naturalWidth * ajuste}px`;
    imagen.style.height = `${imagen.naturalHeight * ajuste}px`;
    escala = 1; x = 0; y = 0;
    aplicar();
  }
  // Acerca o aleja manteniendo fijo el punto (px, py) de la vista
  function zoomEn(px, py, nueva) {
    nueva = Math.min(MAXIMO, Math.max(1, nueva));
    x = px - (px - x) * (nueva / escala);
    y = py - (py - y) * (nueva / escala);
    escala = nueva;
    aplicar();
  }
  const centro = () => [vista.clientWidth / 2, vista.clientHeight / 2];

  // Los botones "ampliar" de la página ponen la imagen grande y abren la ventana
  document.querySelectorAll("[data-ampliar]").forEach((enlace) => {
    enlace.addEventListener("click", (evento) => {
      evento.preventDefault();
      document.getElementById("visor-zoom-titulo").textContent = enlace.dataset.titulo || "";
      imagen.style.width = imagen.style.height = "";
      imagen.src = enlace.dataset.ampliar;
      // Las zonas de cada espermatozoide viajan con la imagen: así el detalle también sale dentro del visor
      lienzo.querySelectorAll(".capa-esperma").forEach((capa) => capa.remove());
      const capa = enlace.querySelector(".capa-esperma");
      if (capa) lienzo.appendChild(capa.cloneNode(true));
      bootstrap.Modal.getOrCreateInstance(ventana).show();
    });
  });
  ventana.addEventListener("shown.bs.modal", () => { if (imagen.complete && imagen.naturalWidth) ajustar(); });
  imagen.addEventListener("load", () => { if (ventana.classList.contains("show")) ajustar(); });
  window.addEventListener("resize", () => { if (ventana.classList.contains("show")) ajustar(); });

  ventana.querySelector("[data-zoom='mas']").addEventListener("click", () => zoomEn(...centro(), escala * 1.5));
  ventana.querySelector("[data-zoom='menos']").addEventListener("click", () => zoomEn(...centro(), escala / 1.5));
  ventana.querySelector("[data-zoom='ajustar']").addEventListener("click", ajustar);
  ventana.querySelector("[data-zoom='real']").addEventListener("click", () => zoomEn(...centro(), 1 / ajuste));  // 100%: un píxel de la imagen por píxel de pantalla

  vista.addEventListener("wheel", (evento) => {
    evento.preventDefault();
    const r = vista.getBoundingClientRect();
    zoomEn(evento.clientX - r.left, evento.clientY - r.top, escala * (evento.deltaY < 0 ? 1.2 : 1 / 1.2));
  }, { passive: false });
  vista.addEventListener("dblclick", (evento) => {
    const r = vista.getBoundingClientRect();
    zoomEn(evento.clientX - r.left, evento.clientY - r.top, escala > 1.01 ? 1 : 3);
  });

  vista.addEventListener("pointerdown", (evento) => {
    vista.setPointerCapture(evento.pointerId);
    punteros.set(evento.pointerId, { x: evento.clientX, y: evento.clientY });
    vista.classList.add("moviendo");
  });
  vista.addEventListener("pointermove", (evento) => {
    const previo = punteros.get(evento.pointerId);
    if (!previo) return;
    punteros.set(evento.pointerId, { x: evento.clientX, y: evento.clientY });
    if (punteros.size === 1) {                                   // un dedo o el ratón: mover
      x += evento.clientX - previo.x;
      y += evento.clientY - previo.y;
      aplicar();
    } else if (punteros.size === 2) {                            // dos dedos: acercar o alejar
      const [a, b] = [...punteros.values()];
      const distancia = Math.hypot(a.x - b.x, a.y - b.y);
      if (distanciaPrevia) {
        const r = vista.getBoundingClientRect();
        zoomEn((a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top, escala * distancia / distanciaPrevia);
      }
      distanciaPrevia = distancia;
    }
  });
  const soltar = (evento) => {
    punteros.delete(evento.pointerId);
    if (punteros.size < 2) distanciaPrevia = null;
    if (punteros.size === 0) vista.classList.remove("moviendo");
  };
  vista.addEventListener("pointerup", soltar);
  vista.addEventListener("pointercancel", soltar);
}

// Detalle de cada espermatozoide al pasar el mouse sobre él (imagen marcada de los resultados y visor con zoom).
// Cada zona es un <polygon class="zona-esperma"> con sus medidas en atributos data-*.
function iniciarDetalleEsperma() {
  const cuadro = document.createElement("div");
  cuadro.id = "detalle-esperma";
  cuadro.setAttribute("role", "tooltip");
  document.body.appendChild(cuadro);

  const numero = (texto, decimales) => Number(texto).toLocaleString("es-MX", { maximumFractionDigits: decimales });
  function llenar(zona) {
    const d = zona.dataset;
    cuadro.innerHTML =
      `<b>Espermatozoide n.º ${d.numero}</b>` +
      `<div>Área: ${numero(d.areaPx, 0)} px · ${numero(d.areaUm, 3)} µm²</div>` +
      `<div>Largo: ${numero(d.largoPx, 1)} px · ${numero(d.largoUm, 2)} µm</div>` +
      `<div class="nota">Micras con escala provisional</div>`;
  }
  function colocar(evento) {
    const margen = 14;
    const ancho = cuadro.offsetWidth, alto = cuadro.offsetHeight;
    let x = evento.clientX + margen, y = evento.clientY + margen;
    if (x + ancho > window.innerWidth - 6) x = evento.clientX - ancho - margen;      // si no cabe a la derecha, a la izquierda
    if (y + alto > window.innerHeight - 6) y = evento.clientY - alto - margen;       // si no cabe abajo, arriba
    cuadro.style.left = `${Math.max(6, x)}px`;
    cuadro.style.top = `${Math.max(6, y)}px`;
  }

  document.addEventListener("pointerover", (evento) => {
    const zona = evento.target.closest && evento.target.closest(".zona-esperma");
    if (!zona) return;
    llenar(zona);
    cuadro.classList.add("visible");
    colocar(evento);
  });
  document.addEventListener("pointermove", (evento) => {
    if (cuadro.classList.contains("visible")) colocar(evento);
  });
  document.addEventListener("pointerout", (evento) => {
    const zona = evento.target.closest && evento.target.closest(".zona-esperma");
    if (zona && !(evento.relatedTarget && evento.relatedTarget.closest && evento.relatedTarget.closest(".zona-esperma"))) {
      cuadro.classList.remove("visible");
    }
  });
  // Al abrir o cerrar el visor, el cuadro se esconde para que no se quede pegado
  document.addEventListener("hidden.bs.modal", () => cuadro.classList.remove("visible"));
}
