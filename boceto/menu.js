// Encabezado y pie de página compartidos por todas las pantallas del boceto.
// En el sitio real esto vivirá en la plantilla base de Flask.

const fuentes = document.createElement("link");
fuentes.rel = "stylesheet";
fuentes.href = "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600&family=Roboto:wght@400;700&family=Roboto+Slab:wght@400;600&display=swap";
document.head.appendChild(fuentes);

const paginas = [
  ["index.html", "Inicio"],
  ["nosotros.html", "Nosotros"],
  ["aliados.html", "Aliados"],
  ["ia.html", "Inteligencia Artificial"],
  ["contacto.html", "Contacto"],
];

const actual = location.pathname.split("/").pop() || "index.html";

const enlaces = paginas
  .map(([archivo, nombre]) => {
    const activo = archivo === actual ? " active" : "";
    return `<li class="nav-item"><a class="nav-link${activo}" href="${archivo}">${nombre}</a></li>`;
  })
  .join("");

// Con ?menu en la dirección, el menú aparece abierto (sirve para las capturas)
const abierto = location.search.includes("menu") ? " show" : "";

document.getElementById("menu").innerHTML = `
  <header>
    <div class="logo">
      <a href="index.html">
        <div class="circulo"></div>
        <div>
          <div class="nombre">IMAGE BIO PRO</div>
          <div class="lema">Análisis de imágenes de microscopio</div>
        </div>
      </a>
    </div>

    <nav class="navbar menu-principal p-0">
      <div class="contenedor d-flex justify-content-between align-items-center">
        <button class="boton-menu" type="button" data-bs-toggle="collapse" data-bs-target="#navegacion">
          <span class="navbar-toggler-icon"></span> Menú
        </button>
        <div class="extras">
          <a href="#"><b>ES</b></a> | <a href="#">EN</a>
          <a class="ms-3" href="login.html">Iniciar sesión</a>
        </div>
      </div>
      <div class="collapse w-100${abierto}" id="navegacion">
        <ul class="navbar-nav contenedor">${enlaces}</ul>
      </div>
    </nav>
  </header>`;

document.getElementById("pie").innerHTML = `
  <footer class="pie">
    <div class="contenedor d-flex flex-wrap justify-content-between gap-3">
      <div>
        <div class="nombre">Image Bio Pro</div>
        <div>UAM Unidad Xochimilco</div>
      </div>
      <div class="text-md-end">
        <div>Contacto: contacto@ejemplo.com</div>
        <div>© 2026 Image Bio Pro</div>
      </div>
    </div>
  </footer>`;
