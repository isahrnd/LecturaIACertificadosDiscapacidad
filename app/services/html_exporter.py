from __future__ import annotations

from html import escape
import re

from app.schemas.analysis import CertificateAnalysisSchema


class HTMLExportService:
    def render(self, analysis: CertificateAnalysisSchema) -> str:
        persona = analysis.persona
        dominios = analysis.dominios.model_dump()
        analisis = analysis.analisis
        cards = "".join(
            f"<div class='metric'><span>{escape(key.replace('_', ' ').title())}</span><strong>{escape(str(value if value is not None else 'No legible'))}</strong></div>"
            for key, value in dominios.items()
        )
        recommended = "".join(
            f"<li>{escape(item)}</li>"
            for bucket in analisis.tareas_recomendadas.model_dump().values()
            for item in bucket
        ) or "<li>Sin información</li>"
        not_recommended = "".join(
            f"<li>{escape(item)}</li>" for item in analisis.tareas_no_recomendadas
        ) or "<li>Sin información</li>"
        adjustments = "".join(
            (
                f"<li><strong>{escape(item.titulo)}</strong>: "
                f"{escape(item.descripcion)} "
                f"<em>({escape(item.fundamento)})</em></li>"
            )
            for item in analisis.ajustes_razonables
        ) or "<li>Sin información</li>"
        rrhh = "".join(
            f"<li>{escape(item)}</li>" for item in analisis.recomendaciones_rrhh_sst
        ) or "<li>Sin información</li>"

        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Informe laboral de discapacidad</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --surface: #fffaf3;
      --ink: #1f2933;
      --accent: #0f766e;
      --accent-soft: #d9f3ef;
      --warn: #b45309;
      --line: #d9cfc0;
    }}
    body {{ margin: 0; font-family: Georgia, 'Times New Roman', serif; background: linear-gradient(135deg, #f7f2ea, #e7f3f1); color: var(--ink); }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 60px; }}
    .hero {{ background: var(--surface); border: 1px solid var(--line); border-radius: 24px; padding: 28px; box-shadow: 0 18px 45px rgba(31,41,51,.08); }}
    .hero h1 {{ margin: 0 0 12px; font-size: 2rem; }}
    .sub {{ color: #52606d; margin-bottom: 18px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-top: 24px; }}
    .metric {{ background: var(--accent-soft); padding: 16px; border-radius: 18px; border: 1px solid rgba(15,118,110,.15); }}
    .metric span {{ display: block; font-size: .85rem; color: #365c58; }}
    .metric strong {{ font-size: 1.4rem; }}
    .section {{ margin-top: 22px; background: rgba(255,250,243,.92); border-radius: 20px; border: 1px solid var(--line); padding: 22px; }}
    .section h2 {{ margin: 0 0 10px; }}
    ul {{ padding-left: 20px; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
    .chip {{ background: #e8eef7; color: #1d4d8b; padding: 8px 12px; border-radius: 999px; font-size: .92rem; }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>{escape(persona.nombre_completo or "Persona no identificada")}</h1>
      <div class="sub">Documento: {escape(persona.documento or "No legible")} | Municipio: {escape(persona.municipio or "No legible")} | Departamento: {escape(persona.departamento or "No legible")}</div>
      <div class="sub">Fecha certificación: {escape(persona.fecha_certificacion or "No legible")} | IPS: {escape(persona.ips_certificadora or "No legible")}</div>
      <div class="chips">
        {''.join(f"<span class='chip'>{escape(item)}</span>" for item in analysis.discapacidades_activas) or "<span class='chip'>Sin categorías identificadas</span>"}
      </div>
      <div class="grid">{cards}</div>
    </section>
    <section class="section">
      <h2>Perfil de funcionamiento</h2>
      <p>{escape(analisis.perfil_funcionamiento or "Sin información estructurada.")}</p>
    </section>
    <section class="section">
      <h2>Tareas recomendadas</h2>
      <ul>{recommended}</ul>
    </section>
    <section class="section">
      <h2>Ajustes razonables</h2>
      <ul>{adjustments}</ul>
    </section>
    <section class="section">
      <h2>Tareas no recomendadas</h2>
      <ul>{not_recommended}</ul>
    </section>
    <section class="section">
      <h2>Recomendaciones para RRHH y SST</h2>
      <ul>{rrhh}</ul>
    </section>
  </div>
</body>
</html>
""".strip()

    def render_pdf_document(self, analysis: CertificateAnalysisSchema) -> str:
        sections = self.pdf_sections(analysis)

        return f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Informe laboral inclusivo</title>
  <style>
    @page {{
      size: A4;
      margin: 1.6cm;
    }}
    body {{
      margin: 0;
      background: #ffffff;
      color: #1f1f1f;
      font-family: Arial, Helvetica, sans-serif;
      font-size: 11px;
      line-height: 1.5;
    }}
    .document {{
      width: 100%;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 20px;
      font-weight: 700;
    }}
    h2 {{
      margin: 18px 0 8px;
      font-size: 14px;
      font-weight: 700;
      color: #000000;
    }}
    p {{
      margin: 0 0 10px;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    li {{
      margin-bottom: 5px;
    }}
    .section {{
      margin-bottom: 10px;
    }}
    .section strong {{
      font-weight: 700;
    }}
    .note {{
      margin-top: 18px;
      font-size: 10px;
      color: #4a4a4a;
    }}
  </style>
</head>
<body>
  <main class="document">
    <h1>Informe laboral inclusivo</h1>
    <p>Documento generado a partir del análisis del certificado de discapacidad.</p>
    {''.join(self._render_pdf_section(section) for section in sections)}
    <p class="note">Nota final: Este informe es una orientación laboral basada en la información disponible del certificado y debe complementarse con criterio humano y validación profesional.</p>
  </main>
</body>
</html>
""".strip()

    def pdf_sections(self, analysis: CertificateAnalysisSchema) -> list[dict[str, object]]:
        persona = analysis.persona
        analisis = analysis.analisis
        general_items = [
            f"Nombre completo: {persona.nombre_completo or 'No disponible'}",
            f"Documento: {persona.documento or 'No disponible'}",
            f"Municipio: {persona.municipio or 'No disponible'}",
            f"Departamento: {persona.departamento or 'No disponible'}",
            f"Fecha certificación: {persona.fecha_certificacion or 'No disponible'}",
            f"IPS certificadora: {persona.ips_certificadora or 'No disponible'}",
            "Discapacidades activas: "
            + (", ".join(analysis.discapacidades_activas) or "No disponible"),
        ]
        if analysis.metadata.fecha_procesamiento is not None:
            general_items.append(
                "Fecha de procesamiento: "
                + analysis.metadata.fecha_procesamiento.strftime("%Y-%m-%d %H:%M UTC")
            )

        return [
            {
                "title": "Datos generales",
                "kind": "list",
                "items": general_items,
            },
            {
                "title": "Resumen funcional",
                "kind": "paragraph",
                "text": analisis.perfil_funcionamiento
                or "Sin información estructurada.",
            },
            {
                "title": "Habilidades y capacidades",
                "kind": "list",
                "items": self._capabilities_items(analysis),
            },
            {
                "title": "Apoyos requeridos / elementos de apoyo",
                "kind": "list",
                "items": self._support_items(analysis),
            },
            {
                "title": "Tareas recomendadas",
                "kind": "list",
                "items": self._recommended_items(analysis),
            },
            {
                "title": "Tareas no recomendadas",
                "kind": "list",
                "items": analisis.tareas_no_recomendadas or ["Sin información."],
            },
            {
                "title": "Ajustes razonables",
                "kind": "list",
                "items": [
                    f"{item.titulo}: {item.descripcion}. Fundamento: {item.fundamento}"
                    for item in analisis.ajustes_razonables
                ]
                or ["Sin información."],
            },
            {
                "title": "Observaciones específicas",
                "kind": "list",
                "items": self._observation_items(analysis),
            },
            {
                "title": "Recomendaciones para RRHH y SST",
                "kind": "list",
                "items": analisis.recomendaciones_rrhh_sst or ["Sin información."],
            },
        ]

    def extract_body_content(self, html: str) -> str:
        match = re.search(r"<body[^>]*>(?P<body>.*)</body>", html, flags=re.IGNORECASE | re.DOTALL)
        return match.group("body") if match else html

    def _render_pdf_section(self, section: dict[str, object]) -> str:
        title = escape(str(section["title"]))
        kind = str(section["kind"])
        if kind == "paragraph":
            text = escape(str(section.get("text") or "Sin información."))
            return (
                f'<section class="section"><h2>{title}</h2><p>{text}</p></section>'
            )

        items = section.get("items") or ["Sin información."]
        rendered_items = "".join(
            f"<li>{escape(str(item))}</li>" for item in items if str(item).strip()
        ) or "<li>Sin información.</li>"
        return f'<section class="section"><h2>{title}</h2><ul>{rendered_items}</ul></section>'

    def _list_items(self, items: list[str]) -> str:
        cleaned = [item.strip() for item in items if item and item.strip()]
        if not cleaned:
            cleaned = ["Sin información."]
        return "".join(f"<li>{escape(item)}</li>" for item in cleaned)

    def _recommended_items(self, analysis: CertificateAnalysisSchema) -> list[str]:
        tasks = analysis.analisis.tareas_recomendadas
        items = [
            f"Administrativo / oficina: {item}"
            for item in tasks.administrativo_oficina
        ]
        items.extend(
            f"Operativo / manual liviano: {item}"
            for item in tasks.operativo_manual_liviano
        )
        items.extend(f"Relacional / apoyo: {item}" for item in tasks.relacional_apoyo)
        return items or ["Sin información."]

    def _capabilities_items(self, analysis: CertificateAnalysisSchema) -> list[str]:
        recommended = self._recommended_items(analysis)
        if recommended and recommended != ["Sin información."]:
            return [
                "Capacidad para desempeñarse en tareas consistentes con las recomendaciones del análisis.",
                *recommended,
            ]

        return [
            "No se identificaron capacidades funcionales adicionales distintas al resumen del análisis.",
        ]

    def _support_items(self, analysis: CertificateAnalysisSchema) -> list[str]:
        items = [
            f"{item.titulo}: {item.descripcion}"
            for item in analysis.analisis.ajustes_razonables
        ]
        return items or ["Sin información."]

    def _observation_items(self, analysis: CertificateAnalysisSchema) -> list[str]:
        observations: list[str] = []
        if analysis.discapacidades_activas:
            observations.append(
                "Las discapacidades activas identificadas en el certificado fueron: "
                + ", ".join(analysis.discapacidades_activas)
            )
        if analysis.codigos_cif.actividades_participacion:
            observations.append(
                "Se identificaron códigos CIF de actividades/participación: "
                + ", ".join(analysis.codigos_cif.actividades_participacion)
            )
        if analysis.metadata.estado:
            observations.append(
                "Estado del análisis registrado: " + analysis.metadata.estado
            )

        return observations or ["Sin observaciones específicas adicionales."]


def get_html_export_service() -> HTMLExportService:
    return HTMLExportService()
