"""Generación del CSV (RF-20) y del PDF (RF-44, RF-45) de un análisis."""
import csv
import io
import os

import matplotlib

matplotlib.use("Agg")  # sin ventana: el servidor no tiene pantalla
import matplotlib.pyplot as plt  # noqa: E402
from fpdf import FPDF  # noqa: E402

ROJO = (168, 32, 26)


def generar_csv(resultados):
    salida = io.StringIO()
    escritor = csv.writer(salida)
    # area_um2 y longitud_um usan una escala provisional sin calibrar (60 px = 1 micra)
    escritor.writerow(["imagen", "espermatozoide", "area_px", "longitud_px", "area_um2", "longitud_um"])
    for img in resultados["imagenes"]:
        for c in img["cabezas"]:
            escritor.writerow([img["nombre"], c["numero"], c["area_px"], c["longitud_px"],
                               c.get("area_um2", ""), c.get("longitud_um", "")])
    # BOM para que Excel abra bien los acentos
    return "﻿" + salida.getvalue()


def _texto(valor):
    """Las fuentes base del PDF solo aceptan latin-1."""
    return str(valor).encode("latin-1", "replace").decode("latin-1")


def _grafica_barras(bordes, valores, titulo, eje_y):
    fig, ax = plt.subplots(figsize=(6, 2.8), dpi=150)
    anchos = [bordes[i + 1] - bordes[i] for i in range(len(valores))]
    ax.bar(bordes[:-1], valores, width=anchos, align="edge", color="#a8201a",
           edgecolor="white")
    ax.set_title(titulo, fontsize=10)
    ax.set_xlabel("Área del espermatozoide (px)", fontsize=9)
    ax.set_ylabel(eje_y, fontsize=9)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return buffer


class ReportePDF(FPDF):
    def __init__(self, usuario, fecha):
        super().__init__(format="Letter")
        self.usuario = usuario
        self.fecha = fecha
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        # Logotipo provisional hasta contar con el definitivo (RF-45)
        self.set_fill_color(*ROJO)
        self.ellipse(12, 9, 10, 10, style="F")
        self.set_xy(25, 9)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*ROJO)
        self.cell(0, 6, "IMAGE BIO PRO")
        self.set_xy(25, 15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(90, 90, 90)
        self.cell(0, 4, _texto("Análisis de imágenes de microscopio"))
        self.set_draw_color(*ROJO)
        self.line(12, 22, self.w - 12, 22)
        self.set_y(26)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(110, 110, 110)
        self.cell(0, 5, _texto(f"{self.usuario} · {self.fecha} · página {self.page_no()}/{{nb}}"),
                  align="C")


def generar_pdf(resultados, usuario, fecha, carpeta_marcadas, ruta_salida):
    pdf = ReportePDF(usuario, fecha.strftime("%d/%m/%Y %H:%M"))
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 8, _texto("Resultados del análisis"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _texto(f"Usuario: {usuario}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, _texto(f"Fecha y hora: {fecha.strftime('%d/%m/%Y %H:%M:%S')}"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, _texto(f"Imágenes: {len(resultados['imagenes'])}"),
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 60, 0)
    pdf.multi_cell(0, 5, _texto(
        "Escala provisional, sin calibrar: se usa 60 px = 1 micra para todas las imágenes "
        "(la regla de la imagen marcada mide 300 px = 5 micras). "
        "Las medidas en micras son aproximadas."))
    pdf.set_text_color(0, 0, 0)
    if resultados.get("provisional"):
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(150, 60, 0)
        pdf.multi_cell(0, 5, _texto(
            "Detección provisional por umbral de color, sin el modelo entrenado. "
            "Los resultados sirven para probar el sistema y no tienen validez científica."))
        pdf.set_text_color(0, 0, 0)
    elif resultados.get("modelo_preliminar"):
        pdf.ln(2)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(150, 60, 0)
        pdf.multi_cell(0, 5, _texto(
            "Modelo preliminar, entrenado con pocas imágenes: los resultados son aproximados. "
            "Donde hay muchos espermatozoides juntos el conteo puede ser menos exacto."))
        pdf.set_text_color(0, 0, 0)

    for img in resultados["imagenes"]:
        _pagina_imagen(pdf, img, carpeta_marcadas)

    promedios = resultados.get("promedios")
    if promedios:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, _texto(f"Promedio entre las {promedios['imagenes']} imágenes"),
                 new_x="LMARGIN", new_y="NEXT")
        grafica = _grafica_barras(promedios["bordes"], promedios["promedios"],
                                  "Distribución promedio de tamaños", "Células (promedio)")
        pdf.image(grafica, w=pdf.epw)

    pdf.output(ruta_salida)


def _pagina_imagen(pdf, img, carpeta_marcadas):
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, _texto(f"Imagen: {img['nombre']}"), new_x="LMARGIN", new_y="NEXT")

    meta = img.get("metadatos") or {}
    if meta:
        pdf.set_font("Helvetica", "", 9)
        partes = [f"Formato {meta['formato']}", f"{meta['ancho']} x {meta['alto']} px",
                  f"modo {meta['modo']}", f"{meta['peso_kb']} KB"]
        if meta.get("dpi"):
            partes.append(f"{meta['dpi']} dpi")
        pdf.cell(0, 5, _texto("Metadatos: " + ", ".join(partes)), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 9)
    for _, mensaje in img["mensajes"]:
        pdf.multi_cell(0, 5, _texto("- " + mensaje), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    if not img["cabezas"]:
        return

    marcada = os.path.join(carpeta_marcadas, img["marcada"])
    if os.path.exists(marcada):
        pdf.image(marcada, w=pdf.epw * 0.8, x=pdf.l_margin + pdf.epw * 0.1)
        pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _texto(f"Conteo de células: {img['conteo']}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for etiqueta, clave in (("Área del espermatozoide (px)", "area"), ("Largo del espermatozoide (px)", "longitud")):
        r = img[clave]
        pdf.cell(0, 5, _texto(f"{etiqueta}: media {r['media']}, desviación estándar {r['desviacion']}, "
                              f"mínimo {r['minimo']}, máximo {r['maximo']}"),
                 new_x="LMARGIN", new_y="NEXT")
    if img.get("area_um"):
        for etiqueta, clave in (("Área del espermatozoide (µm²)", "area_um"), ("Largo del espermatozoide (µm)", "longitud_um")):
            r = img[clave]
            pdf.cell(0, 5, _texto(f"{etiqueta}: media {r['media']}, desviación estándar {r['desviacion']}, "
                                  f"mínimo {r['minimo']}, máximo {r['maximo']}"),
                     new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    h = img["histograma"]
    grafica = _grafica_barras(h["bordes"], h["frecuencias"], "Distribución de tamaños", "Células")
    pdf.image(grafica, w=pdf.epw * 0.85)
    pdf.ln(2)
