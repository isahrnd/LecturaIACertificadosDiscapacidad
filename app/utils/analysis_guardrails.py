from __future__ import annotations

import re
from typing import Any

from app.core.config import get_settings
from app.core.logging import logger
from app.utils.disability_parser import normalize_disability_name, normalize_token

AUDITIVA = normalize_disability_name("Auditiva") or "Auditiva"
FISICA = normalize_disability_name("Fisica") or "Fisica"
VISUAL = normalize_disability_name("Visual") or "Visual"
INTELECTUAL = normalize_disability_name("Intelectual") or "Intelectual"
PSICOSOCIAL = normalize_disability_name("Psicosocial") or "Psicosocial"
SORDOCEGUERA = normalize_disability_name("Sordoceguera") or "Sordoceguera"
MULTIPLE = normalize_disability_name("Multiple") or "Multiple"

DOMAIN_ORDER: tuple[str, ...] = (
    "cognicion",
    "movilidad",
    "cuidado_personal",
    "relaciones",
    "vida_diaria",
    "participacion",
)

DOMAIN_LABELS: dict[str, str] = {
    "cognicion": "cognicion",
    "movilidad": "movilidad",
    "cuidado_personal": "cuidado personal",
    "relaciones": "relaciones",
    "vida_diaria": "actividades de la vida diaria",
    "participacion": "participacion",
}

_PHYSICAL_RESTRICTION_KEYWORDS: tuple[str, ...] = (
    # disability / limitation labels
    "DISCAPACIDAD FISICA",
    "LIMITACION FISICA",
    "LIMITACIONES FISICAS",
    "RESTRICCION FISICA",
    "RIESGO FISICO",
    # effort / load
    "ESFUERZO FISICO",
    "ESFUERZO MANUAL",
    "SOBREESFUERZO",
    "CARGA FISICA",
    "TRABAJO FISICO",
    "ACTIVIDAD FISICA",
    "EXIGENCIA FISICA",
    "DEMANDA FISICA",
    # mobility / displacement
    "MOVILIDAD INTENSA",
    "MOVILIDAD REDUCIDA",
    "MOVILIDAD LIMITADA",
    "DESPLAZAMIENTOS FRECUENTES",
    "DESPLAZAMIENTOS PROLONGADOS",
    "DESPLAZAMIENTOS CONTINUOS",
    "RECORRIDOS PROLONGADOS",
    "DEAMBULACION",
    "RUTAS DESPEJADAS",
    # postural / heights
    "CAMBIOS POSTURALES",
    "EXIGENCIA POSTURAL",
    "TRABAJO EN ALTURAS",
    "SUPERFICIES INESTABLES",
    "CAIDAS",
    # handling / weight
    "CARGUE DE PESO",
    "MANIPULACION DE CARGAS",
    "MANIPULACION REPETITIVA",
    "LEVANTAMIENTO DE CARGAS",
    "OPERACIONES MANUALES PESADAS",
    "ESFUERZO CORPORAL",
    # accessibility barriers
    "BARRERAS ARQUITECTONICAS",
    "OBSTACULOS FISICOS",
    "ACCESIBILIDAD FISICA",
    "ESPACIO FISICO",
    "ERGONOMIA",
    # mobility aids / assistive devices
    "SILLA DE RUEDAS",
    "BASTON",
    "CAMINADOR",
    "MULETAS",
    "PROTESIS",
    "ORTESIS",
    "AYUDAS TECNICAS DE MOVILIDAD",
)

_VISUAL_RESTRICTION_KEYWORDS: tuple[str, ...] = (
    "DISCAPACIDAD VISUAL",
    "BAJA VISION",
    "CEGUERA",
    "DEFICIT VISUAL",
    "LIMITACION VISUAL",
    "LIMITACIONES VISUALES",
    "RESTRICCION VISUAL",
    "ADAPTACIONES VISUALES",
    "EXCLUSIVAMENTE DE LA VISION",
)

_COGNITIVE_PSICOSOCIAL_RESTRICTION_KEYWORDS: tuple[str, ...] = (
    "GESTION COGNITIVA",
    "GESTION EMOCIONAL",
    "REGULACION EMOCIONAL",
    "SOBRECARGA COGNITIVA",
    "DEMANDA COGNITIVA",
    "PRESION SOCIAL",
    "ESTIMULOS ESTRESANTES",
    "MANEJO DE ESTRES",
    "MANEJO DE FATIGA",
    "FATIGA Y ESTRES",
    "SUPERVISION MINIMA",
    "INTERACCION SOCIAL",
    "ESTIMULACION SENSORIAL",
    "APOYO EMOCIONAL",
    "ALTA CONCENTRACION",
    "SUPERVISION PERMANENTE",
    "AMBIENTES PREDECIBLES",
)

_DISABILITY_LABELS: dict[str, tuple[str, ...]] = {
    FISICA: ("DISCAPACIDAD FISICA",),
    VISUAL: ("DISCAPACIDAD VISUAL",),
    AUDITIVA: ("DISCAPACIDAD AUDITIVA",),
    INTELECTUAL: ("DISCAPACIDAD INTELECTUAL",),
    PSICOSOCIAL: ("DISCAPACIDAD PSICOSOCIAL", "DISCAPACIDAD MENTAL"),
    SORDOCEGUERA: ("SORDOCEGUERA",),
    MULTIPLE: ("DISCAPACIDAD MULTIPLE",),
}

_PHONE_KEYWORDS: tuple[str, ...] = ("TELEFON", "LLAMAD")
_PHONE_SUPPORT_KEYWORDS: tuple[str, ...] = (
    "AUDIFON",
    "IMPLANTE",
    "SUBTITUL",
    "TRANSCRIP",
    "CHAT",
    "RELEVO",
    "MENSAJE",
)

_AUDITIVA_ADMIN_DEFAULTS: tuple[str, ...] = (
    "Gestion documental y archivo con instrucciones escritas claras.",
    "Digitacion y actualizacion de registros o formatos estandarizados.",
    "Apoyo administrativo y seguimiento de bases de datos por canales escritos.",
)

_AUDITIVA_OPERATIVE_DEFAULTS: tuple[str, ...] = (
    "Clasificacion, empaque o alistamiento liviano con secuencia visual definida.",
    "Inventario o apoyo logistico liviano con senalizacion visual y pasos claros.",
    "Verificacion de materiales en puestos con instrucciones visibles y bajo ruido de fondo.",
)

_AUDITIVA_RELATIONAL_DEFAULTS: tuple[str, ...] = (
    "Atencion y soporte por chat, correo o canales escritos.",
    "Apoyo interno en equipos con acuerdos de comunicacion accesible.",
    "Participacion en equipo con induccion inicial clara y confirmacion escrita de instrucciones.",
)

_AUDITIVA_NON_RECOMMENDED_DEFAULTS: tuple[str, ...] = (
    "Roles que dependan exclusivamente de llamadas telefonicas sin apoyo de comunicacion accesible.",
    "Ambientes con ruido extremo sin ajustes de comunicacion o control de ruido de fondo.",
    "Tareas de seguridad donde las alarmas sean solo sonoras y no existan alertas visuales.",
    "Procesos criticos con instrucciones verbales sin respaldo escrito o visual.",
)

_AUDITIVA_RRHH_DEFAULTS: tuple[str, ...] = (
    "Priorizar instrucciones escritas y visuales en induccion, entrenamiento y seguimiento.",
    "Confirmar la comprension de indicaciones relevantes por canales escritos.",
    "Reducir ruido de fondo o ubicar el puesto en zonas con mejor inteligibilidad comunicativa.",
    "Sensibilizar al equipo en comunicacion inclusiva y uso de apoyos visuales.",
    "Implementar alertas visuales cuando existan alarmas o instrucciones de seguridad.",
)

_AUDITIVA_ADJUSTMENTS_DEFAULTS: tuple[dict[str, str], ...] = (
    {
        "titulo": "Instrucciones escritas y visuales",
        "descripcion": "Entregar consignas, cambios de proceso y recordatorios por escrito o con apoyos visuales faciles de consultar.",
        "fundamento": "La discapacidad auditiva activa exige que la informacion critica no dependa solo de la via oral.",
    },
    {
        "titulo": "Canales de confirmacion accesibles",
        "descripcion": "Usar chat, correo, tableros o formatos breves para confirmar indicaciones, novedades y prioridades del turno.",
        "fundamento": "La confirmacion escrita reduce errores cuando la comunicacion verbal puede no ser suficiente.",
    },
    {
        "titulo": "Entorno con buena visibilidad y bajo ruido",
        "descripcion": "Ubicar el puesto en zonas con visibilidad del interlocutor, iluminacion adecuada y menor ruido de fondo.",
        "fundamento": "La accesibilidad comunicativa mejora cuando hay lectura visual del contexto y menos interferencia sonora.",
    },
    {
        "titulo": "Alertas visuales y apoyos de comunicacion",
        "descripcion": "Permitir audifonos, implante, subtitulos, mensajes escritos o alertas visuales segun la necesidad del puesto.",
        "fundamento": "Los apoyos tecnicos y visuales son coherentes con una discapacidad auditiva activa y mejoran la seguridad.",
    },
)

_TILDE_CORRECTIONS: tuple[tuple[str, str], ...] = (
    (r'\bgestion\b', 'gestión'),
    (r'\bdigitacion\b', 'digitación'),
    (r'\bactualizacion\b', 'actualización'),
    (r'\bclasificacion\b', 'clasificación'),
    (r'\bverificacion\b', 'verificación'),
    (r'\batencion\b', 'atención'),
    (r'\bparticipacion\b', 'participación'),
    (r'\bcomunicacion\b', 'comunicación'),
    (r'\binformacion\b', 'información'),
    (r'\binstruccion\b', 'instrucción'),
    (r'\binduccion\b', 'inducción'),
    (r'\bincorporacion\b', 'incorporación'),
    (r'\binteraccion\b', 'interacción'),
    (r'\borganizacion\b', 'organización'),
    (r'\bdocumentacion\b', 'documentación'),
    (r'\bconfirmacion\b', 'confirmación'),
    (r'\bdescripcion\b', 'descripción'),
    (r'\bdefinicion\b', 'definición'),
    (r'\bfuncion\b', 'función'),
    (r'\badministracion\b', 'administración'),
    (r'\bevaluacion\b', 'evaluación'),
    (r'\bsupervision\b', 'supervisión'),
    (r'\bseleccion\b', 'selección'),
    (r'\bcoordinacion\b', 'coordinación'),
    (r'\bhabilitacion\b', 'habilitación'),
    (r'\bintegracion\b', 'integración'),
    (r'\badaptacion\b', 'adaptación'),
    (r'\bplanificacion\b', 'planificación'),
    (r'\bsensibilizacion\b', 'sensibilización'),
    (r'\brecomendacion\b', 'recomendación'),
    (r'\bposicion\b', 'posición'),
    (r'\bprogramacion\b', 'programación'),
    (r'\bcontratacion\b', 'contratación'),
    (r'\bcondicion\b', 'condición'),
    (r'\bsesion\b', 'sesión'),
    (r'\bmediacion\b', 'mediación'),
    (r'\bnegociacion\b', 'negociación'),
    (r'\bestructuracion\b', 'estructuración'),
    (r'\biluminacion\b', 'iluminación'),
    (r'\bpresion\b', 'presión'),
    (r'\bsenalizacion\b', 'señalización'),
    (r'\bacompanamiento\b', 'acompañamiento'),
    (r'\bacompanante\b', 'acompañante'),
    (r'\bsenas\b', 'señas'),
    (r'\bcritica\b', 'crítica'),
    (r'\bcritico\b', 'crítico'),
    (r'\bcriticas\b', 'críticas'),
    (r'\bcriticos\b', 'críticos'),
    (r'\bfacil\b', 'fácil'),
    (r'\bfaciles\b', 'fáciles'),
    (r'\btelefono\b', 'teléfono'),
    (r'\btelefonos\b', 'teléfonos'),
    (r'\btelefonica\b', 'telefónica'),
    (r'\btelefonicas\b', 'telefónicas'),
    (r'\btelefonico\b', 'telefónico'),
    (r'\baudifono\b', 'audífono'),
    (r'\baudifonos\b', 'audífonos'),
    (r'\bsubtitulo\b', 'subtítulo'),
    (r'\bsubtitulos\b', 'subtítulos'),
    (r'\blogistico\b', 'logístico'),
    (r'\blogistica\b', 'logística'),
    (r'\bergonomia\b', 'ergonomía'),
    (r'\bfisico\b', 'físico'),
    (r'\bfisica\b', 'física'),
    (r'\bfisicos\b', 'físicos'),
    (r'\bfisicas\b', 'físicas'),
    (r'\bbaston\b', 'bastón'),
    (r'\bsegun\b', 'según'),
    (r'\bcomprension\b', 'comprensión'),
)

_STOPWORDS_DEDUP: frozenset[str] = frozenset({
    "DE", "LA", "EL", "LOS", "LAS", "Y", "O", "EN", "CON", "SIN",
    "PARA", "POR", "QUE", "UN", "UNA", "UNOS", "UNAS", "AL", "DEL",
    "SE", "SU", "SUS", "LO", "LE", "NI", "A", "E", "U",
    "CUANDO", "COMO", "DONDE", "SOBRE", "ENTRE", "DESDE", "HASTA",
    "ANTE", "BAJO", "TRAS", "MEDIANTE", "DURANTE", "SEGUN",
    "NO", "SI", "YA", "SOLO", "CADA", "TODO", "MAS",
    "ES", "SON", "SEA", "SEAN", "HAY", "PUEDE", "PUEDEN",
    "DEBE", "DEBEN", "TIENE", "TIENEN",
})

_GRAMMAR_CORRECTIONS: tuple[tuple[str, str], ...] = (
    (r'que normalmente sonoras?\b', 'que normalmente sean sonoros'),
)

_TILDE_CORRECTIONS_EXTRA: tuple[tuple[str, str], ...] = (
    (r"\brevision\b", "revisión"),
    (r"\borientacion\b", "orientación"),
    (r"\boperacion\b", "operación"),
    (r"\boperaciones\b", "operaciones"),
    (r"\bsimultaneos\b", "simultáneos"),
    (r"\bsimultaneo\b", "simultáneo"),
    (r"\bvia\b", "vía"),
    (r"\bperiodica\b", "periódica"),
    (r"\bperiodico\b", "periódico"),
    (r"\bretroalimentacion\b", "retroalimentación"),
    (r"\binclusion\b", "inclusión"),
    (r"\bautonomia\b", "autonomía"),
)


def normalize_analysis_for_certificate(
    payload: dict[str, Any],
    *,
    used_vision: bool,
    observations: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    active_categories = _normalize_active_categories(payload.get("discapacidades_activas"))
    domain_scores = _safe_domains(payload.get("dominios"))
    domain_levels = classify_domain_levels(domain_scores)
    observation_context = parse_observation_context(observations)
    physical_evidence = _has_physical_evidence(active_categories, domain_scores)
    visual_evidence = VISUAL in active_categories
    uncertainty_note = _build_uncertainty_note(payload, used_vision=used_vision)

    analysis = payload.get("analisis")
    if not isinstance(analysis, dict):
        analysis = {}

    if settings.analysis_debug:
        logger.info(
            "[ANALYSIS_DEBUG][analysis_guardrails] normalize_analysis_for_certificate active_categories=%s used_vision=%s",
            active_categories,
            used_vision,
        )

    if active_categories == [AUDITIVA]:
        return _normalize_auditiva_only_analysis(
            analysis,
            domain_scores=domain_scores,
            domain_levels=domain_levels,
            observation_context=observation_context,
            uncertainty_note=uncertainty_note,
        )

    return _normalize_generic_analysis(
        analysis,
        active_categories=active_categories,
        domain_scores=domain_scores,
        domain_levels=domain_levels,
        observation_context=observation_context,
        physical_evidence=physical_evidence,
        visual_evidence=visual_evidence,
        uncertainty_note=uncertainty_note,
    )


def classify_domain_levels(domain_scores: dict[str, float]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in domain_scores.items():
        if value <= 0:
            result[key] = "sin dificultad observada"
        elif value <= 24:
            result[key] = "dificultad leve"
        elif value <= 49:
            result[key] = "dificultad moderada"
        elif value <= 74:
            result[key] = "dificultad alta"
        else:
            result[key] = "dificultad muy alta"
    return result


def parse_observation_context(observations: str | None) -> dict[str, bool]:
    normalized = normalize_token(observations or "")
    return {
        "usa_audifono": "AUDIFON" in normalized,
        "usa_baston": "BASTON" in normalized,
        "usa_silla_ruedas": "SILLA DE RUEDAS" in normalized,
        "lee_labios": "LEE LABIOS" in normalized or "LECTURA LABIAL" in normalized,
        "no_sabe_lengua_senas": "NO SABE LENGUA DE SENAS" in normalized
        or "NO USA LENGUA DE SENAS" in normalized,
        "requiere_acompanante": "REQUIERE ACOMPANANTE" in normalized,
        "implante_coclear": "IMPLANTE COCLEAR" in normalized,
        "comunicacion_oral": "COMUNICARSE ORALMENTE" in normalized
        or "COMUNICACION ORAL" in normalized
        or "PERSONA ORALIZADA" in normalized,
    }


def _normalize_auditiva_only_analysis(
    analysis: dict[str, Any],
    *,
    domain_scores: dict[str, float],
    domain_levels: dict[str, str],
    observation_context: dict[str, bool],
    uncertainty_note: str | None,
) -> dict[str, Any]:
    tasks = (
        analysis.get("tareas_recomendadas")
        if isinstance(analysis.get("tareas_recomendadas"), dict)
        else {}
    )
    administrativo = _merge_items(
        _filter_strings(
            tasks.get("administrativo_oficina"),
            disallow_physical=True,
            disallow_visual=True,
            disallow_direct_phone=True,
        ),
        _AUDITIVA_ADMIN_DEFAULTS,
        minimum=2,
        maximum=3,
    )
    operativo = _merge_items(
        _filter_strings(
            tasks.get("operativo_manual_liviano"),
            disallow_physical=True,
            disallow_visual=True,
            disallow_direct_phone=True,
        ),
        _AUDITIVA_OPERATIVE_DEFAULTS,
        minimum=2,
        maximum=3,
    )
    relacional = _merge_items(
        _filter_strings(
            tasks.get("relacional_apoyo"),
            disallow_physical=True,
            disallow_visual=True,
            disallow_direct_phone=True,
        ),
        _AUDITIVA_RELATIONAL_DEFAULTS,
        minimum=2,
        maximum=3,
    )
    tareas_no = _merge_items(
        _filter_strings(
            analysis.get("tareas_no_recomendadas"),
            disallow_physical=True,
            disallow_visual=True,
        ),
        _AUDITIVA_NON_RECOMMENDED_DEFAULTS,
        minimum=3,
        maximum=6,
    )
    recomendaciones = _merge_items(
        _filter_strings(
            analysis.get("recomendaciones_rrhh_sst"),
            disallow_physical=True,
            disallow_visual=True,
            disallow_direct_phone=True,
        ),
        _AUDITIVA_RRHH_DEFAULTS,
        minimum=4,
        maximum=6,
    )
    ajustes = _merge_adjustments(
        _filter_adjustments(
            analysis.get("ajustes_razonables"),
            disallow_physical=True,
            disallow_visual=True,
            disallow_direct_phone=True,
        ),
        _AUDITIVA_ADJUSTMENTS_DEFAULTS,
        minimum=3,
        maximum=5,
    )

    if _is_domain_level(domain_levels["participacion"], "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        recomendaciones = _merge_items(
            recomendaciones,
            (
                "Planear una incorporacion gradual con induccion inicial, instrucciones escritas y canales de confirmacion accesibles.",
            ),
            minimum=5,
            maximum=6,
        )
        relacional = _merge_items(
            relacional,
            (
                "Participacion en equipo con acuerdos de comunicacion, induccion inicial clara y confirmacion escrita.",
            ),
            minimum=2,
            maximum=3,
        )
        tareas_no = _merge_items(
            tareas_no,
            (
                "Actividades grupales o coordinaciones que dependan de instrucciones orales cambiantes sin apoyos de comunicacion accesible.",
            ),
            minimum=4,
            maximum=6,
        )

    if _is_domain_level(domain_levels["relaciones"], "dificultad leve", "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        recomendaciones = _merge_items(
            recomendaciones,
            (
                "Definir acuerdos de comunicacion, mediacion y canales escritos para la interaccion cotidiana.",
            ),
            minimum=5,
            maximum=6,
        )
        tareas_no = _merge_items(
            tareas_no,
            (
                "Roles con negociacion, atencion a publico conflictivo o interaccion social intensa sin mediacion.",
            ),
            minimum=4,
            maximum=6,
        )

    if _is_domain_level(domain_levels["cognicion"], "dificultad leve", "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        recomendaciones = _merge_items(
            recomendaciones,
            (
                "Usar instrucciones paso a paso, checklists, recordatorios visuales y verificacion escrita cuando la tarea lo requiera.",
            ),
            minimum=5,
            maximum=6,
        )
        ajustes = _merge_adjustments(
            ajustes,
            (
                {
                    "titulo": "Checklists y pasos visibles",
                    "descripcion": "Disponer checklists, ayudas visuales y recordatorios simples para organizar la secuencia de trabajo.",
                    "fundamento": "Los puntajes de desempeno sugieren reforzar secuencia, organizacion y confirmacion escrita sin inferir una discapacidad cognitiva adicional.",
                },
            ),
            minimum=4,
            maximum=5,
        )
        tareas_no = _merge_items(
            tareas_no,
            (
                "Tareas con multiples instrucciones simultaneas solo verbales o cambios rapidos sin apoyos escritos de organizacion.",
            ),
            minimum=4,
            maximum=6,
        )

    recomendaciones, ajustes, profile_support_notes = _apply_observation_context(
        recomendaciones,
        ajustes,
        observation_context=observation_context,
    )

    active_text = "discapacidad auditiva como categoria activa"
    affected = _summarize_affected_domains(domain_scores, domain_levels)
    preserved = _summarize_preserved_domains(domain_levels)

    profile_parts = [
        f"El certificado identifica {active_text}.",
        "La movilidad no muestra dificultad relevante, por lo que no se sustentan restricciones fisicas generales."
        if domain_scores["movilidad"] == 0
        else f"La movilidad presenta {domain_levels['movilidad']}, por lo que cualquier ajuste corporal debe limitarse a lo expresamente sustentado por el certificado.",
    ]
    if affected:
        profile_parts.append(f"Los dominios mas comprometidos son {affected}.")
    if preserved:
        profile_parts.append(f"Se observan dominios sin afectacion relevante en {preserved}.")
    profile_parts.append(
        "El impacto laboral esperado se concentra en accesibilidad comunicativa, confirmacion escrita de instrucciones, alertas visuales y control del ruido de fondo."
    )
    if _is_domain_level(domain_levels["participacion"], "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        profile_parts.append(
            f"La participacion presenta {domain_levels['participacion']}, por lo que se recomienda incorporacion gradual, apoyos de comunicacion y confirmacion escrita de indicaciones relevantes."
        )
    if profile_support_notes:
        profile_parts.extend(profile_support_notes)
    if uncertainty_note:
        profile_parts.append(uncertainty_note)

    return _normalize_output_quality(
        {
            "tareas_recomendadas": {
                "administrativo_oficina": administrativo,
                "operativo_manual_liviano": operativo,
                "relacional_apoyo": relacional,
            },
            "ajustes_razonables": ajustes,
            "tareas_no_recomendadas": tareas_no,
            "perfil_funcionamiento": " ".join(profile_parts),
            "recomendaciones_rrhh_sst": recomendaciones,
        },
        [AUDITIVA],
    )


def _normalize_generic_analysis(
    analysis: dict[str, Any],
    *,
    active_categories: list[str],
    domain_scores: dict[str, float],
    domain_levels: dict[str, str],
    observation_context: dict[str, bool],
    physical_evidence: bool,
    visual_evidence: bool,
    uncertainty_note: str | None,
) -> dict[str, Any]:
    auditiva_activa = AUDITIVA in active_categories
    tasks = (
        analysis.get("tareas_recomendadas")
        if isinstance(analysis.get("tareas_recomendadas"), dict)
        else {}
    )
    administrativo = _filter_strings(
        tasks.get("administrativo_oficina"),
        active_categories=active_categories,
        disallow_physical=not physical_evidence,
        disallow_visual=not visual_evidence,
        disallow_direct_phone=auditiva_activa,
    )
    operativo = _filter_strings(
        tasks.get("operativo_manual_liviano"),
        active_categories=active_categories,
        disallow_physical=not physical_evidence,
        disallow_visual=not visual_evidence,
        disallow_direct_phone=auditiva_activa,
    )
    relacional = _filter_strings(
        tasks.get("relacional_apoyo"),
        active_categories=active_categories,
        disallow_physical=not physical_evidence,
        disallow_visual=not visual_evidence,
        disallow_direct_phone=auditiva_activa,
    )
    tareas_no = _filter_strings(
        analysis.get("tareas_no_recomendadas"),
        active_categories=active_categories,
        disallow_physical=not physical_evidence,
        disallow_visual=not visual_evidence,
    )
    recomendaciones = _filter_strings(
        analysis.get("recomendaciones_rrhh_sst"),
        active_categories=active_categories,
        disallow_physical=not physical_evidence,
        disallow_visual=not visual_evidence,
        disallow_direct_phone=auditiva_activa,
    )
    ajustes = _filter_adjustments(
        analysis.get("ajustes_razonables"),
        active_categories=active_categories,
        disallow_physical=not physical_evidence,
        disallow_visual=not visual_evidence,
        disallow_direct_phone=auditiva_activa,
    )
    perfil = str(analysis.get("perfil_funcionamiento") or "").strip()
    if _is_invalid_text(
        perfil,
        active_categories=active_categories,
        disallow_physical=not physical_evidence,
        disallow_visual=not visual_evidence,
        disallow_direct_phone=auditiva_activa,
    ):
        perfil = ""

    recomendaciones = _inject_domain_guidance(
        recomendaciones,
        domain_levels=domain_levels,
        active_categories=active_categories,
        auditiva_activa=auditiva_activa,
    )
    tareas_no = _inject_domain_cautions(
        tareas_no,
        domain_levels=domain_levels,
        active_categories=active_categories,
        auditiva_activa=auditiva_activa,
    )
    ajustes = _inject_domain_adjustments(
        ajustes,
        domain_levels=domain_levels,
        active_categories=active_categories,
        auditiva_activa=auditiva_activa,
        physical_evidence=physical_evidence,
    )
    recomendaciones, ajustes, support_notes = _apply_observation_context(
        recomendaciones,
        ajustes,
        observation_context=observation_context,
    )

    if uncertainty_note:
        recomendaciones = _merge_items(
            recomendaciones,
            (uncertainty_note,),
            minimum=min(len(recomendaciones) + 1, 6),
            maximum=6,
        )
        if perfil:
            perfil = f"{perfil} {uncertainty_note}"
        else:
            perfil = uncertainty_note

    if not perfil:
        category_text = ", ".join(active_categories) or "categorias sin confirmacion total"
        affected = _summarize_affected_domains(domain_scores, domain_levels)
        preserved = _summarize_preserved_domains(domain_levels)
        fragments = [f"El analisis debe priorizar {category_text} como referencia principal del certificado."]
        if affected:
            fragments.append(f"Los dominios mas relevantes son {affected}.")
        if preserved:
            fragments.append(f"Los dominios sin afectacion relevante incluyen {preserved}.")
        if support_notes:
            fragments.extend(support_notes)
        perfil = " ".join(fragments)

    return _normalize_output_quality(
        {
            "tareas_recomendadas": {
                "administrativo_oficina": administrativo[:3],
                "operativo_manual_liviano": operativo[:3],
                "relacional_apoyo": relacional[:3],
            },
            "ajustes_razonables": ajustes[:5],
            "tareas_no_recomendadas": tareas_no[:6],
            "perfil_funcionamiento": perfil,
            "recomendaciones_rrhh_sst": recomendaciones[:6],
        },
        active_categories,
    )


def _inject_domain_guidance(
    recomendaciones: list[str],
    *,
    domain_levels: dict[str, str],
    active_categories: list[str],
    auditiva_activa: bool,
) -> list[str]:
    injected = list(recomendaciones)
    auditiva_only = active_categories == [AUDITIVA]
    if _is_domain_level(domain_levels["participacion"], "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        injected = _merge_items(
            injected,
            (
                "Promover incorporacion gradual, instrucciones claras y apoyos proporcionados segun la participacion observada."
                if not auditiva_only
                else "Promover incorporacion gradual con induccion inicial, instrucciones escritas y confirmacion por canales accesibles.",
            ),
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    if _is_domain_level(domain_levels["relaciones"], "dificultad leve", "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        injected = _merge_items(
            injected,
            (
                "Definir acuerdos de comunicacion, mediacion y canales escritos para la interaccion laboral cotidiana."
                if not auditiva_only
                else "Definir acuerdos de comunicacion con instrucciones visuales, confirmacion escrita y canales escritos para la interaccion laboral cotidiana.",
            ),
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    if _is_domain_level(domain_levels["cognicion"], "dificultad leve", "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        injected = _merge_items(
            injected,
            (
                "Usar instrucciones paso a paso, checklists, recordatorios visuales y supervision inicial para tareas con demanda cognitiva."
                if not auditiva_only
                else "Usar instrucciones paso a paso, checklists, recordatorios visuales y confirmacion escrita para ordenar la ejecucion de tareas.",
            ),
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    if auditiva_activa:
        injected = _merge_items(
            injected,
            (
                "Evitar depender exclusivamente de llamadas o instrucciones solo verbales; priorizar confirmacion escrita y apoyos visuales.",
            ),
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    if _is_domain_level(domain_levels["movilidad"], "dificultad moderada", "dificultad alta", "dificultad muy alta") and FISICA in active_categories:
        injected = _merge_items(
            injected,
            (
                "Ajustar desplazamientos, pausas y ergonomia de acuerdo con la dificultad de movilidad observada.",
            ),
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    return injected


def _inject_domain_cautions(
    tareas_no: list[str],
    *,
    domain_levels: dict[str, str],
    active_categories: list[str],
    auditiva_activa: bool,
) -> list[str]:
    injected = list(tareas_no)
    auditiva_only = active_categories == [AUDITIVA]
    if auditiva_activa:
        injected = _merge_items(
            injected,
            _AUDITIVA_NON_RECOMMENDED_DEFAULTS,
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    if _is_domain_level(domain_levels["participacion"], "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        injected = _merge_items(
            injected,
            (
                "Actividades grupales complejas o de alta presion social sin apoyos ni acompanamiento."
                if not auditiva_only
                else "Actividades grupales o coordinaciones que dependan de instrucciones orales cambiantes sin apoyos de comunicacion accesible.",
            ),
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    if _is_domain_level(domain_levels["relaciones"], "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        injected = _merge_items(
            injected,
            (
                "Roles con negociacion compleja, atencion a publico conflictivo o interaccion intensa sin mediacion."
                if not auditiva_only
                else "Roles con intercambio oral continuo, negociacion verbal intensa o atencion a publico conflictivo sin respaldos escritos o visuales.",
            ),
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    if _is_domain_level(domain_levels["cognicion"], "dificultad leve", "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        injected = _merge_items(
            injected,
            (
                "Tareas con alta carga cognitiva, multitarea intensa o decisiones criticas sin apoyos de organizacion."
                if not auditiva_only
                else "Tareas con multiples instrucciones simultaneas solo verbales o cambios rapidos sin apoyos escritos para organizar prioridades.",
            ),
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    if _is_domain_level(domain_levels["movilidad"], "dificultad moderada", "dificultad alta", "dificultad muy alta") and FISICA in active_categories:
        injected = _merge_items(
            injected,
            (
                "Desplazamientos extensos o exigencia fisica continua sin ajustes de puesto.",
            ),
            minimum=min(len(injected) + 1, 6),
            maximum=6,
        )
    return injected


def _inject_domain_adjustments(
    ajustes: list[dict[str, str]],
    *,
    domain_levels: dict[str, str],
    active_categories: list[str],
    auditiva_activa: bool,
    physical_evidence: bool,
) -> list[dict[str, str]]:
    injected = list(ajustes)
    auditiva_only = active_categories == [AUDITIVA]
    if auditiva_activa:
        injected = _merge_adjustments(
            injected,
            (
                {
                    "titulo": "Confirmacion escrita de instrucciones",
                    "descripcion": "Asegurar que instrucciones relevantes, cambios y prioridades queden confirmados por escrito o en formato visual.",
                    "fundamento": "La discapacidad auditiva activa hace mas segura la comunicacion cuando existe respaldo escrito o visual.",
                },
            ),
            minimum=min(len(injected) + 1, 5),
            maximum=5,
        )
    if _is_domain_level(domain_levels["participacion"], "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        injected = _merge_adjustments(
            injected,
            (
                {
                    "titulo": "Acompanamiento inicial y estructuracion"
                    if not auditiva_only
                    else "Induccion inicial y comunicacion accesible",
                    "descripcion": "Planear una incorporacion gradual con acompanamiento inicial, secuencia estable y referentes claros del equipo."
                    if not auditiva_only
                    else "Planear una induccion inicial con instrucciones escritas, demostracion visual y canales claros para confirmar prioridades y cambios.",
                    "fundamento": "La participacion con dificultad moderada o mayor se beneficia de seguimiento inicial y menor ambiguedad operativa."
                    if not auditiva_only
                    else "La participacion observada sugiere reforzar la comunicacion accesible y la claridad de indicaciones sin inferir una discapacidad adicional.",
                },
            ),
            minimum=min(len(injected) + 1, 5),
            maximum=5,
        )
    if _is_domain_level(domain_levels["cognicion"], "dificultad leve", "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        injected = _merge_adjustments(
            injected,
            (
                {
                    "titulo": "Checklists y recordatorios visuales",
                    "descripcion": "Usar checklists, apoyos visuales y secuencias paso a paso para tareas con varias etapas o validaciones.",
                    "fundamento": "La dificultad cognitiva observada sugiere apoyar la organizacion y verificacion inicial del trabajo."
                    if not auditiva_only
                    else "Los puntajes de desempeno sugieren reforzar organizacion, secuencia y verificacion escrita dentro de una accesibilidad comunicativa auditiva.",
                },
            ),
            minimum=min(len(injected) + 1, 5),
            maximum=5,
        )
    if physical_evidence and _is_domain_level(domain_levels["movilidad"], "dificultad moderada", "dificultad alta", "dificultad muy alta"):
        injected = _merge_adjustments(
            injected,
            (
                {
                    "titulo": "Pausas, ergonomia y recorridos controlados",
                    "descripcion": "Organizar pausas, ergonomia y desplazamientos breves cuando la movilidad del certificado lo requiera.",
                    "fundamento": "La movilidad con dificultad moderada o mayor justifica ajustes del puesto y de los recorridos.",
                },
            ),
            minimum=min(len(injected) + 1, 5),
            maximum=5,
        )
    return injected


def _apply_observation_context(
    recomendaciones: list[str],
    ajustes: list[dict[str, str]],
    *,
    observation_context: dict[str, bool],
) -> tuple[list[str], list[dict[str, str]], list[str]]:
    updated_recommendations = list(recomendaciones)
    updated_adjustments = list(ajustes)
    profile_notes: list[str] = []

    if observation_context.get("usa_audifono"):
        updated_recommendations = _merge_items(
            updated_recommendations,
            (
                "Puede apoyarse en audifonos para comunicacion oral, pero se recomienda no depender exclusivamente de llamadas, porque el dispositivo puede fallar, la bateria puede agotarse o el ruido ambiente puede afectar la comprension.",
            ),
            minimum=min(len(updated_recommendations) + 1, 6),
            maximum=6,
        )
        updated_adjustments = _merge_adjustments(
            updated_adjustments,
            (
                {
                    "titulo": "Uso funcional de audifonos",
                    "descripcion": "Permitir el uso de audifonos como apoyo para comunicacion oral y complementar siempre con confirmacion escrita o visual.",
                    "fundamento": "La observacion del usuario describe audifonos como apoyo funcional, sin cambiar la categoria de discapacidad del certificado.",
                },
            ),
            minimum=min(len(updated_adjustments) + 1, 5),
            maximum=5,
        )
        profile_notes.append(
            "Puede apoyarse en audifonos para comunicacion oral, pero se recomienda no depender exclusivamente de llamadas, porque el dispositivo puede fallar, la bateria puede agotarse o el ruido ambiente puede afectar la comprension."
        )

    if observation_context.get("implante_coclear"):
        updated_adjustments = _merge_adjustments(
            updated_adjustments,
            (
                {
                    "titulo": "Apoyo con implante coclear",
                    "descripcion": "Considerar el implante coclear como apoyo funcional y reforzar la comunicacion con recursos escritos o visuales cuando la tarea sea critica.",
                    "fundamento": "La observacion del usuario aporta contexto funcional util para accesibilidad comunicativa sin modificar el diagnostico del certificado.",
                },
            ),
            minimum=min(len(updated_adjustments) + 1, 5),
            maximum=5,
        )
        profile_notes.append(
            "Las observaciones mencionan implante coclear como apoyo funcional y sugieren complementar la comunicacion oral con ayudas visuales o escritas."
        )

    if observation_context.get("lee_labios"):
        updated_recommendations = _merge_items(
            updated_recommendations,
            (
                "Favorecer comunicacion cara a cara con buena visibilidad del interlocutor cuando la persona use lectura labial.",
            ),
            minimum=min(len(updated_recommendations) + 1, 6),
            maximum=6,
        )
        profile_notes.append(
            "Las observaciones refieren lectura labial, por lo que la visibilidad del interlocutor y la iluminacion adecuada son apoyos relevantes."
        )

    if observation_context.get("no_sabe_lengua_senas"):
        updated_recommendations = _merge_items(
            updated_recommendations,
            (
                "No asumir lengua de senas como canal principal si las observaciones indican que no la utiliza; priorizar alternativas escritas y visuales.",
            ),
            minimum=min(len(updated_recommendations) + 1, 6),
            maximum=6,
        )

    if observation_context.get("comunicacion_oral"):
        profile_notes.append(
            "Las observaciones describen comunicacion oral funcional, pero se recomienda respaldarla con instrucciones escritas cuando la informacion sea critica."
        )

    if observation_context.get("requiere_acompanante"):
        updated_adjustments = _merge_adjustments(
            updated_adjustments,
            (
                {
                    "titulo": "Acompanamiento funcional",
                    "descripcion": "Coordinar acompanamiento inicial o apoyos de referencia cuando las observaciones indiquen necesidad de acompanante.",
                    "fundamento": "La observacion del usuario aporta contexto funcional para organizar apoyos sin crear nuevas categorias diagnosticas.",
                },
            ),
            minimum=min(len(updated_adjustments) + 1, 5),
            maximum=5,
        )

    if observation_context.get("usa_baston"):
        profile_notes.append(
            "Las observaciones mencionan baston como apoyo funcional; cualquier ajuste de movilidad debe depender del dominio de movilidad y no asumir una restriccion adicional por si mismo."
        )

    if observation_context.get("usa_silla_ruedas"):
        profile_notes.append(
            "Las observaciones mencionan silla de ruedas como apoyo funcional; su uso debe traducirse en accesibilidad del entorno solo cuando sea coherente con la movilidad observada."
        )

    return updated_recommendations, updated_adjustments, profile_notes


def _normalize_active_categories(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        category = normalize_disability_name(str(item))
        if not category:
            continue
        if category in seen:
            continue
        seen.add(category)
        normalized.append(category)
    return normalized


def _safe_domains(value: Any) -> dict[str, float]:
    domains = value if isinstance(value, dict) else {}
    return {
        "cognicion": _safe_float(domains.get("cognicion")),
        "movilidad": _safe_float(domains.get("movilidad")),
        "cuidado_personal": _safe_float(domains.get("cuidado_personal")),
        "relaciones": _safe_float(domains.get("relaciones")),
        "vida_diaria": _safe_float(domains.get("vida_diaria")),
        "participacion": _safe_float(domains.get("participacion")),
    }


def _has_physical_evidence(active_categories: list[str], domain_scores: dict[str, float]) -> bool:
    return FISICA in active_categories or domain_scores["movilidad"] >= 25


def _build_uncertainty_note(payload: dict[str, Any], *, used_vision: bool) -> str | None:
    raw_items = (
        payload.get("discapacidades_raw")
        if isinstance(payload.get("discapacidades_raw"), list)
        else []
    )
    active_categories = _normalize_active_categories(payload.get("discapacidades_activas"))
    has_ilegible = any(
        isinstance(item, dict)
        and normalize_token(str(item.get("marcado") or "")) == "ILEGIBLE"
        for item in raw_items
    )
    if active_categories:
        return None
    if not has_ilegible and not used_vision:
        return None
    return (
        "La categoria de discapacidad no pudo confirmarse con total confianza a partir del certificado legible; se recomienda validacion humana antes de tomar decisiones laborales definitivas."
    )


def _filter_strings(
    value: Any,
    *,
    active_categories: list[str] | None = None,
    disallow_physical: bool,
    disallow_visual: bool = False,
    disallow_direct_phone: bool = False,
) -> list[str]:
    active_categories = active_categories or []
    if not isinstance(value, list):
        return []

    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = str(item or "").strip()
        if not text:
            continue
        if _is_invalid_text(
            text,
            active_categories=active_categories,
            disallow_physical=disallow_physical,
            disallow_visual=disallow_visual,
            disallow_direct_phone=disallow_direct_phone,
        ):
            continue
        key = normalize_token(text)
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _filter_adjustments(
    value: Any,
    *,
    active_categories: list[str] | None = None,
    disallow_physical: bool,
    disallow_visual: bool = False,
    disallow_direct_phone: bool = False,
) -> list[dict[str, str]]:
    active_categories = active_categories or []
    if not isinstance(value, list):
        return []

    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        titulo = str(item.get("titulo") or "").strip()
        descripcion = str(item.get("descripcion") or "").strip()
        fundamento = str(item.get("fundamento") or "").strip()
        if not titulo or not descripcion or not fundamento:
            continue
        combined = " ".join((titulo, descripcion, fundamento))
        if _is_invalid_text(
            combined,
            active_categories=active_categories,
            disallow_physical=disallow_physical,
            disallow_visual=disallow_visual,
            disallow_direct_phone=disallow_direct_phone,
        ):
            continue
        key = normalize_token(titulo)
        if key in seen:
            continue
        seen.add(key)
        result.append(
            {
                "titulo": titulo,
                "descripcion": descripcion,
                "fundamento": fundamento,
            }
        )
    return result


def _is_invalid_text(
    text: str,
    *,
    active_categories: list[str],
    disallow_physical: bool,
    disallow_visual: bool = False,
    disallow_direct_phone: bool = False,
) -> bool:
    normalized = normalize_token(text)
    if not normalized:
        return True

    if disallow_physical and _contains_any(normalized, _PHYSICAL_RESTRICTION_KEYWORDS):
        return True
    if disallow_visual and _contains_any(normalized, _VISUAL_RESTRICTION_KEYWORDS):
        return True
    if disallow_direct_phone and _contains_any(normalized, _PHONE_KEYWORDS) and not _contains_any(
        normalized, _PHONE_SUPPORT_KEYWORDS
    ):
        return True

    for category, labels in _DISABILITY_LABELS.items():
        if category in active_categories:
            continue
        if _contains_any(normalized, labels):
            return True

    if INTELECTUAL not in active_categories and PSICOSOCIAL not in active_categories:
        if _contains_any(normalized, _COGNITIVE_PSICOSOCIAL_RESTRICTION_KEYWORDS):
            return True

    return False


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _merge_items(
    current: list[str],
    defaults: tuple[str, ...],
    *,
    minimum: int,
    maximum: int,
) -> list[str]:
    merged = list(current)
    seen = {normalize_token(item) for item in merged}
    for item in defaults:
        key = normalize_token(item)
        if key in seen:
            continue
        merged.append(item)
        seen.add(key)
        if len(merged) >= maximum:
            break
    return merged[: max(minimum, min(len(merged), maximum))]


def _merge_adjustments(
    current: list[dict[str, str]],
    defaults: tuple[dict[str, str], ...],
    *,
    minimum: int,
    maximum: int,
) -> list[dict[str, str]]:
    merged = list(current)
    seen = {normalize_token(item.get("titulo", "")) for item in merged}
    for item in defaults:
        key = normalize_token(item.get("titulo", ""))
        if key in seen:
            continue
        merged.append(dict(item))
        seen.add(key)
        if len(merged) >= maximum:
            break
    return merged[: max(minimum, min(len(merged), maximum))]


def _is_domain_level(current_level: str, *allowed_levels: str) -> bool:
    return current_level in allowed_levels


def _summarize_affected_domains(domain_scores: dict[str, float], domain_levels: dict[str, str]) -> str:
    parts: list[str] = []
    for key in DOMAIN_ORDER:
        level = domain_levels.get(key)
        score = domain_scores.get(key)
        if level is None or score is None:
            continue
        if level == "sin dificultad observada":
            continue
        label = DOMAIN_LABELS.get(key, key)
        parts.append(f"{label} ({level}, {score:.2f}%)")
    return ", ".join(parts)


def _summarize_preserved_domains(domain_levels: dict[str, str]) -> str:
    preserved = [
        DOMAIN_LABELS.get(key, key)
        for key in DOMAIN_ORDER
        if domain_levels.get(key) == "sin dificultad observada"
    ]
    return ", ".join(preserved[:3])


def _safe_float(value: Any) -> float:
    try:
        if value in (None, ""):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fix_tildes(text: str) -> str:
    for corrections in (_TILDE_CORRECTIONS, _TILDE_CORRECTIONS_EXTRA):
        for pattern, replacement in corrections:
            def _repl(m: re.Match, rep: str = replacement) -> str:
                word = m.group(0)
                if word.isupper():
                    return rep.upper()
                if word[0].isupper():
                    return rep[0].upper() + rep[1:]
                return rep
            text = re.sub(pattern, _repl, text, flags=re.IGNORECASE)
    return text


def _fix_grammar(text: str) -> str:
    for pattern, replacement in _GRAMMAR_CORRECTIONS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _stem_word(word: str) -> str:
    if len(word) > 5 and word.endswith('ES'):
        word = word[:-2]
    elif len(word) > 4 and word.endswith('S'):
        word = word[:-1]
    return word[:6]


def _content_words(text: str) -> frozenset[str]:
    tokens = normalize_token(text).split()
    cleaned = (re.sub(r'[^A-Z0-9]', '', t) for t in tokens)
    words = [t for t in cleaned if t not in _STOPWORDS_DEDUP and len(t) > 2]
    return frozenset(_stem_word(w) for w in words)


def _both_restrict_exclusive_phone(a: str, b: str) -> bool:
    _PHONE = ("TELEFO", "LLAMAD")
    _EXCL = ("EXCLUS",)

    def _is_phone_exclusive(text: str) -> bool:
        n = normalize_token(text)
        return any(k in n for k in _PHONE) and any(k in n for k in _EXCL)

    return _is_phone_exclusive(a) and _is_phone_exclusive(b)


def _both_light_sorting_tasks(a: str, b: str) -> bool:
    _SORT = ("CLASIF",)
    _LIGHT = ("MATERI", "LIVIAN")
    _VISUAL = ("VISUAL", "SECUEN")

    def _is_light_sorting(text: str) -> bool:
        n = normalize_token(text)
        return (
            any(k in n for k in _SORT)
            and any(k in n for k in _LIGHT)
            and any(k in n for k in _VISUAL)
        )

    return _is_light_sorting(a) and _is_light_sorting(b)


def _has_significant_overlap(a: str, b: str, threshold: float = 0.55) -> bool:
    words_a = _content_words(a)
    words_b = _content_words(b)
    if not words_a or not words_b:
        return False
    smaller = words_a if len(words_a) <= len(words_b) else words_b
    if len(words_a & words_b) / len(smaller) >= threshold:
        return True
    if _both_restrict_exclusive_phone(a, b):
        return True
    return _both_light_sorting_tasks(a, b)


def _semantic_dedup_list(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if not any(_has_significant_overlap(item, kept) for kept in result):
            result.append(item)
    return result


def _dedup_tasks_cross_category(tasks: dict[str, list[str]]) -> dict[str, list[str]]:
    seen: list[str] = []
    deduped: dict[str, list[str]] = {}
    for category, items in tasks.items():
        deduped_items: list[str] = []
        for item in items:
            if not any(_has_significant_overlap(item, s) for s in seen):
                deduped_items.append(item)
                seen.append(item)
        deduped[category] = deduped_items
    return deduped


def _get_adjustment_prefix(active_categories: list[str]) -> str:
    if len(active_categories) > 1:
        return "[Discapacidad múltiple]"
    if not active_categories:
        return "[Ajuste de accesibilidad]"
    cat = active_categories[0]
    if cat == AUDITIVA:
        return "[Discapacidad auditiva]"
    if cat == FISICA:
        return "[Discapacidad física]"
    if cat == VISUAL:
        return "[Discapacidad visual]"
    if cat == INTELECTUAL:
        return "[Discapacidad cognitiva/intelectual]"
    if cat == PSICOSOCIAL:
        return "[Discapacidad psicosocial]"
    if cat == SORDOCEGUERA:
        return "[Sordoceguera]"
    if cat == MULTIPLE:
        return "[Discapacidad múltiple]"
    return "[Ajuste de accesibilidad]"


def _ensure_subtype_prefix(
    items: list[dict[str, str]],
    active_categories: list[str],
) -> list[dict[str, str]]:
    prefix = _get_adjustment_prefix(active_categories)
    result: list[dict[str, str]] = []
    for item in items:
        titulo = item.get("titulo", "")
        if titulo and not re.match(r'^\[.+?\]', titulo):
            titulo = f"{prefix} {titulo}"
        result.append({**item, "titulo": titulo})
    return result


_AUDITIVA_PARADOX_KEYWORDS: tuple[str, ...] = (
    "APOYO AUDITIVO",
    "APOYOS AUDITIVOS",
    "COMUNICACION ADAPTADA",
    "ORGANIZACION DE AGENDAS",
    "APOYO SOCIAL",
    "APOYO COMUNITARIO",
)

_CATEGORY_TITLE_PREFIX_RULES: dict[str, tuple[str, ...]] = {
    MULTIPLE: ("[MULTIPLE", "[DISCAPACIDAD MULTIPLE"),
    FISICA: ("[FISICA", "[DISCAPACIDAD FISICA"),
    VISUAL: ("[VISUAL", "[DISCAPACIDAD VISUAL"),
    PSICOSOCIAL: ("[PSICOSOCIAL", "[DISCAPACIDAD PSICOSOCIAL", "[DISCAPACIDAD MENTAL"),
    INTELECTUAL: ("[INTELECTUAL", "[DISCAPACIDAD INTELECTUAL", "[DISCAPACIDAD COGNITIVA/INTELECTUAL"),
}

_CATEGORY_CONTENT_RULES: dict[str, tuple[str, ...]] = {
    MULTIPLE: ("[MULTIPLE", "DISCAPACIDAD MULTIPLE", "MULTIPLE CON AFECTACION"),
    FISICA: ("[FISICA", "DISCAPACIDAD FISICA"),
    VISUAL: ("[VISUAL", "DISCAPACIDAD VISUAL"),
    PSICOSOCIAL: ("[PSICOSOCIAL", "DISCAPACIDAD PSICOSOCIAL", "DISCAPACIDAD MENTAL"),
    INTELECTUAL: ("[INTELECTUAL", "DISCAPACIDAD INTELECTUAL", "DISCAPACIDAD COGNITIVA/INTELECTUAL"),
}

_AUDITIVA_ONLY_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "[MULTIPLE",
    "DISCAPACIDAD MULTIPLE",
    "MULTIPLE CON AFECTACION",
    "[FISICA",
    "DISCAPACIDAD FISICA",
    "MOVILIDAD REDUCIDA",
    "FACILITAR MOVILIDAD",
    "SILLA DE RUEDAS",
    "BASTON",
    "[VISUAL",
    "DISCAPACIDAD VISUAL",
    "ALTO CONTRASTE",
    "TAMANO DE LETRA",
    "BAJA VISION",
    "[PSICOSOCIAL",
    "APOYO EMOCIONAL",
    "ESTRES",
    "FATIGA",
    "[INTELECTUAL",
    "ALTA DEMANDA COGNITIVA",
    "SUPERVISION CONSTANTE",
    "SUPERVISION PERMANENTE",
    "ALTA PRESION SOCIAL",
    "PRESION SOCIAL",
    "ACOMPANAMIENTO",
    "ADAPTACION SOCIAL",
    "AMBIGUEDAD SOCIAL",
    "MEDIACION DE CONFLICTOS",
    "NEGOCIACION SOCIAL",
    "AMBIENTES PREDECIBLES",
    "MOBILIARIO ERGONOMICO",
    "RUTAS SIN BARRERAS",
    "BARRERAS ARQUITECTONICAS",
    "ESTIMULOS DISTRACTORES",
    "CONCENTRACION",
    "MEJORAR CONCENTRACION",
    "SUPERVISION PROGRESIVA",
    "ACCESO CERCANO A BANOS",
    "BANOS Y ESPACIOS DE DESCANSO",
    "ESPACIOS DE DESCANSO",
    "PUESTO DE TRABAJO CON ACCESO CERCANO",
    "SUPERVISION INICIAL Y SEGUIMIENTO PROGRESIVO",
)

_AUDITIVA_ONLY_REPLACEMENTS: dict[str, str] = {
    "FACILITAR SUPERVISION INICIAL Y SEGUIMIENTO PROGRESIVO PARA TAREAS ASIGNADAS.": "Realizar inducción inicial con instrucciones escritas, demostración visual y confirmación de comprensión.",
}


def _filter_extra_physical_in_auditiva(items: list[str]) -> list[str]:
    return [
        item for item in items
        if not _contains_any(normalize_token(item), _PHYSICAL_RESTRICTION_KEYWORDS)
    ]


def _filter_paradox_auditiva(items: list[str]) -> list[str]:
    return [
        item for item in items
        if not _contains_any(normalize_token(item), _AUDITIVA_PARADOX_KEYWORDS)
    ]


def _is_active_or_allowed_category(category: str, active_categories: list[str]) -> bool:
    return category in active_categories


def _matches_inactive_category_title_prefix(
    title: str,
    active_categories: list[str],
) -> bool:
    normalized = normalize_token(title)
    if not normalized.startswith("["):
        return False

    for category, prefixes in _CATEGORY_TITLE_PREFIX_RULES.items():
        if _is_active_or_allowed_category(category, active_categories):
            continue
        if _contains_any(normalized, prefixes):
            return True
    return False


def _contains_inactive_category_content(
    text: str,
    active_categories: list[str],
) -> bool:
    normalized = normalize_token(text)
    if not normalized:
        return False

    for category, phrases in _CATEGORY_CONTENT_RULES.items():
        if _is_active_or_allowed_category(category, active_categories):
            continue
        if _contains_any(normalized, phrases):
            return True

    if active_categories == [AUDITIVA] and _contains_any(normalized, _AUDITIVA_ONLY_FORBIDDEN_PHRASES):
        return True
    return False


def _sanitize_auditiva_only_text(text: str) -> str:
    normalized = normalize_token(text)
    for original_normalized, replacement in _AUDITIVA_ONLY_REPLACEMENTS.items():
        if normalized == original_normalized:
            return replacement
    if "SUPERVISION INICIAL" in normalized and "SEGUIMIENTO PROGRESIVO" in normalized:
        return "Realizar inducción inicial con instrucciones escritas, demostración visual y confirmación de comprensión."
    return text


def _clean_visible_output_by_active_categories(
    analysis: dict[str, Any],
    active_categories: list[str],
) -> dict[str, Any]:
    settings = get_settings()
    tasks = analysis.get("tareas_recomendadas", {})
    administrativo = list(tasks.get("administrativo_oficina") or [])
    operativo = list(tasks.get("operativo_manual_liviano") or [])
    relacional = list(tasks.get("relacional_apoyo") or [])
    ajustes = list(analysis.get("ajustes_razonables") or [])
    tareas_no = list(analysis.get("tareas_no_recomendadas") or [])
    perfil = str(analysis.get("perfil_funcionamiento") or "")
    recomendaciones = list(analysis.get("recomendaciones_rrhh_sst") or [])

    if settings.analysis_debug:
        logger.info(
            "[ANALYSIS_DEBUG][analysis_guardrails] pre_clean active_categories=%s tareas_no=%s recomendaciones=%s",
            active_categories,
            tareas_no,
            recomendaciones,
        )

    def keep_text(text: str) -> bool:
        return not _contains_inactive_category_content(text, active_categories)

    def clean_list(items: list[str]) -> list[str]:
        if active_categories == [AUDITIVA]:
            items = [_sanitize_auditiva_only_text(str(item or "")) for item in items]
        return [item for item in items if keep_text(str(item or ""))]

    cleaned_adjustments: list[dict[str, str]] = []
    for item in ajustes:
        if not isinstance(item, dict):
            continue
        titulo = str(item.get("titulo") or "")
        descripcion = str(item.get("descripcion") or "")
        fundamento = str(item.get("fundamento") or "")
        if _matches_inactive_category_title_prefix(titulo, active_categories):
            continue
        if not keep_text(" ".join((titulo, descripcion, fundamento))):
            continue
        cleaned_adjustments.append(
            {
                "titulo": titulo,
                "descripcion": descripcion,
                "fundamento": fundamento,
            }
        )

    cleaned = {
        "tareas_recomendadas": {
            "administrativo_oficina": clean_list(administrativo),
            "operativo_manual_liviano": clean_list(operativo),
            "relacional_apoyo": clean_list(relacional),
        },
        "ajustes_razonables": cleaned_adjustments,
        "tareas_no_recomendadas": clean_list(tareas_no),
        "perfil_funcionamiento": "" if not keep_text(perfil) else perfil,
        "recomendaciones_rrhh_sst": clean_list(recomendaciones),
    }
    if settings.analysis_debug:
        logger.info(
            "[ANALYSIS_DEBUG][analysis_guardrails] post_clean active_categories=%s tareas_no=%s recomendaciones=%s",
            active_categories,
            cleaned["tareas_no_recomendadas"],
            cleaned["recomendaciones_rrhh_sst"],
        )
    return cleaned


def _normalize_output_quality(
    analysis: dict[str, Any],
    active_categories: list[str],
    subtype: str | None = None,
) -> dict[str, Any]:
    is_auditiva_only = active_categories == [AUDITIVA]

    def fix_str(s: str) -> str:
        return _fix_grammar(_fix_tildes(s))

    def fix_list(items: list[str]) -> list[str]:
        return [fix_str(item) for item in items]

    def fix_adjustments(items: list[dict[str, str]]) -> list[dict[str, str]]:
        return [
            {
                "titulo": fix_str(item.get("titulo", "")),
                "descripcion": fix_str(item.get("descripcion", "")),
                "fundamento": fix_str(item.get("fundamento", "")),
            }
            for item in items
        ]

    tasks = analysis.get("tareas_recomendadas", {})
    administrativo = fix_list(list(tasks.get("administrativo_oficina") or []))
    operativo = fix_list(list(tasks.get("operativo_manual_liviano") or []))
    relacional = fix_list(list(tasks.get("relacional_apoyo") or []))
    ajustes = fix_adjustments(list(analysis.get("ajustes_razonables") or []))
    tareas_no = fix_list(list(analysis.get("tareas_no_recomendadas") or []))
    perfil = fix_str(str(analysis.get("perfil_funcionamiento") or ""))
    recomendaciones = fix_list(list(analysis.get("recomendaciones_rrhh_sst") or []))

    administrativo = _semantic_dedup_list(administrativo)
    operativo = _semantic_dedup_list(operativo)
    relacional = _semantic_dedup_list(relacional)
    tareas_no = _semantic_dedup_list(tareas_no)
    recomendaciones = _semantic_dedup_list(recomendaciones)

    deduped = _dedup_tasks_cross_category({
        "administrativo_oficina": administrativo,
        "operativo_manual_liviano": operativo,
        "relacional_apoyo": relacional,
    })
    administrativo = deduped["administrativo_oficina"]
    operativo = deduped["operativo_manual_liviano"]
    relacional = deduped["relacional_apoyo"]

    ajustes = _ensure_subtype_prefix(ajustes, active_categories)

    if is_auditiva_only:
        administrativo = _filter_extra_physical_in_auditiva(administrativo)
        operativo = _filter_extra_physical_in_auditiva(operativo)
        relacional = _filter_extra_physical_in_auditiva(relacional)
        tareas_no = _filter_extra_physical_in_auditiva(tareas_no)
        recomendaciones = _filter_extra_physical_in_auditiva(recomendaciones)
        ajustes = [
            a for a in ajustes
            if not _contains_any(
                normalize_token(" ".join(filter(None, (a.get("titulo"), a.get("descripcion"), a.get("fundamento"))))),
                _PHYSICAL_RESTRICTION_KEYWORDS,
            )
            and not _contains_any(
                normalize_token(a.get("titulo", "")),
                _AUDITIVA_PARADOX_KEYWORDS,
            )
        ]
        administrativo = _filter_paradox_auditiva(administrativo)
        operativo = _filter_paradox_auditiva(operativo)
        relacional = _filter_paradox_auditiva(relacional)
        tareas_no = _filter_paradox_auditiva(tareas_no)
        recomendaciones = _filter_paradox_auditiva(recomendaciones)

    return _clean_visible_output_by_active_categories({
        "tareas_recomendadas": {
            "administrativo_oficina": administrativo,
            "operativo_manual_liviano": operativo,
            "relacional_apoyo": relacional,
        },
        "ajustes_razonables": ajustes,
        "tareas_no_recomendadas": tareas_no,
        "perfil_funcionamiento": perfil,
        "recomendaciones_rrhh_sst": recomendaciones,
    }, active_categories)
