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
    });
  });

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
