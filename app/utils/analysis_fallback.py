from __future__ import annotations

import unicodedata
from typing import Any

_FISICA_CATS: frozenset[str] = frozenset({"FISICA", "MULTIPLE", "SORDOCEGUERA"})


def _normalize_cat(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s.strip().upper())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def is_analysis_empty(payload: dict[str, Any]) -> bool:
    analisis = payload.get("analisis")
    if not isinstance(analisis, dict):
        return True

    tareas = analisis.get("tareas_recomendadas")
    admin = _safe_list((tareas or {}).get("administrativo_oficina"))
    operativo = _safe_list((tareas or {}).get("operativo_manual_liviano"))
    relacional = _safe_list((tareas or {}).get("relacional_apoyo"))
    tareas_no = _safe_list(analisis.get("tareas_no_recomendadas"))
    recomendaciones = _safe_list(analisis.get("recomendaciones_rrhh_sst"))
    perfil = str(analisis.get("perfil_funcionamiento") or "").strip()
    ajustes = analisis.get("ajustes_razonables")

    ajustes_validos = 0
    if isinstance(ajustes, list):
        for item in ajustes:
            if not isinstance(item, dict):
                continue
            titulo = str(item.get("titulo") or "").strip()
            descripcion = str(item.get("descripcion") or "").strip()
            fundamento = str(item.get("fundamento") or "").strip()
            if titulo and descripcion and fundamento:
                ajustes_validos += 1

    useful_recommended = len(admin) + len(operativo) + len(relacional)

    if useful_recommended == 0:
        return True
    if not perfil:
        return True
    if len(tareas_no) == 0:
        return True
    if len(recomendaciones) == 0:
        return True
    if ajustes_validos == 0:
        return True

    return False


def fallback_build_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    discapacidades_activas = _safe_list(payload.get("discapacidades_activas"))
    dominios = payload.get("dominios") if isinstance(payload.get("dominios"), dict) else {}

    cognicion = _safe_float(dominios.get("cognicion"))
    movilidad = _safe_float(dominios.get("movilidad"))
    cuidado_personal = _safe_float(dominios.get("cuidado_personal"))
    relaciones = _safe_float(dominios.get("relaciones"))
    vida_diaria = _safe_float(dominios.get("vida_diaria"))
    participacion = _safe_float(dominios.get("participacion"))

    active_normalized = {_normalize_cat(c) for c in discapacidades_activas}
    has_fisica_category = bool(_FISICA_CATS & active_normalized)
    has_auditiva_category = "AUDITIVA" in active_normalized
    auditiva_only = has_auditiva_category and active_normalized == {"AUDITIVA"}

    administrativo = [
        "Registro y actualizacion basica de informacion en sistemas o formatos estandarizados.",
        "Apoyo en organizacion documental, archivo y clasificacion de soportes fisicos o digitales.",
    ]
    operativo = [
        "Empaque liviano o alistamiento simple en puesto fijo con tiempos y secuencia definidos.",
        "Verificacion basica de materiales o productos con criterios de calidad definidos y secuencia estandarizada.",
    ]
    relacional = [
        "Orientacion inicial o apoyo al usuario con guiones, protocolos y funciones claramente definidas.",
        "Apoyo en actividades internas con comunicacion estructurada y seguimiento del proceso.",
    ]
    tareas_no = [
        "Funciones de alta multitarea, presion continua o exigencia de respuesta simultanea sin apoyos.",
    ]
    ajustes = [
        {
            "titulo": "Induccion y consignas claras",
            "descripcion": "Entregar instrucciones concretas, por pasos y con criterios de logro verificables para facilitar el desempeno inicial.",
            "fundamento": "Medida conservadora util cuando hay necesidad de estructuracion de tareas o adaptacion del proceso de aprendizaje.",
        },
        {
            "titulo": "Organizacion del puesto",
            "descripcion": "Mantener un puesto estable, ordenado y con elementos de trabajo faciles de consultar.",
            "fundamento": "Reduce sobrecarga operativa y mejora continuidad cuando se requiere mayor claridad del entorno.",
        },
    ]
    recomendaciones = [
        "Realizar induccion al cargo con funciones priorizadas, tiempos realistas y seguimiento durante el periodo inicial.",
        "Definir ajustes razonables documentados entre RRHH, SST y liderazgo directo, con revision periodica.",
        "Promover comunicacion clara, metas observables y retroalimentacion breve para favorecer inclusion y autonomia.",
        "Monitorear exigencias del puesto para ajustar carga y forma de trabajo cuando sea necesario.",
    ]

    if auditiva_only:
        administrativo = [
            "Gestion documental y registro de informacion por canales escritos y formatos estandarizados.",
            "Actualizacion de bases de apoyo o listados con instrucciones escritas y validaciones visibles.",
        ]
        operativo = [
            "Empaque, alistamiento o verificacion liviana con secuencia visible y bajo ruido de fondo.",
            "Revision de materiales en puesto fijo con instrucciones visibles y confirmacion escrita de cambios relevantes.",
        ]
        relacional = [
            "Orientacion inicial y apoyo interno por canales escritos, con funciones claramente definidas.",
            "Coordinacion con el equipo mediante comunicacion escrita, protocolos visibles y confirmacion de indicaciones relevantes.",
        ]
        tareas_no = [
            "Funciones de alta multitarea con instrucciones exclusivamente orales y cambios simultaneos sin apoyos escritos o visuales.",
            "Atencion al usuario exclusivamente por via telefonica sin alternativas escritas o visuales.",
            "Entornos con ruido elevado sin senalizacion visual complementaria como apoyo de seguridad.",
        ]
        ajustes = [
            {
                "titulo": "Induccion y comunicacion accesible",
                "descripcion": "Entregar instrucciones escritas, demostraciones visuales y criterios de logro verificables para facilitar el desempeno inicial.",
                "fundamento": "Medida conservadora coherente con una discapacidad auditiva activa cuando se requiere accesibilidad comunicativa desde el inicio.",
            },
            {
                "titulo": "Confirmacion escrita y apoyos visuales",
                "descripcion": "Mantener un canal escrito para novedades, prioridades y alertas visuales relacionadas con la operacion del puesto.",
                "fundamento": "La comunicacion accesible reduce errores cuando la informacion critica no debe depender solo de la via oral.",
            },
        ]
        recomendaciones = [
            "Realizar induccion al cargo con instrucciones escritas, apoyo visual y confirmacion de comprension.",
            "Definir ajustes razonables documentados entre RRHH, SST y liderazgo directo, con revision periodica.",
            "Promover comunicacion clara por canales escritos y retroalimentacion breve para favorecer inclusion y autonomia.",
            "Verificar que el puesto cuente con senalizacion visual para alertas de seguridad y operacion.",
        ]

    if has_fisica_category:
        tareas_no.extend(
            [
                "Cargue y manipulacion repetitiva de peso o tareas con esfuerzo fisico sostenido.",
                "Labores con desplazamientos frecuentes, cambios constantes de puesto o recorridos prolongados.",
            ]
        )
        recomendaciones.append(
            "Monitorear exigencias fisicas del puesto y reducir sobrecarga cuando existan restricciones de movilidad o esfuerzo."
        )

    if has_auditiva_category and not auditiva_only:
        tareas_no.extend(
            [
                "Atencion al usuario exclusivamente por via telefonica sin alternativas escritas o visuales.",
                "Entornos con ruido elevado sin senalizacion visual complementaria como apoyo de seguridad.",
            ]
        )
        recomendaciones.extend(
            [
                "Establecer canales de comunicacion escrita como alternativa formal a instrucciones verbales o telefonicas.",
                "Verificar que el puesto cuente con senalizacion visual para alertas de seguridad y operacion.",
            ]
        )

    if movilidad >= 50 and has_fisica_category:
        operativo = [
            "Alistamiento liviano en estacion fija con herramientas a la mano y minima necesidad de desplazamiento.",
            "Apoyo en control basico de inventario o revision simple de materiales desde un puesto estable.",
        ]
        tareas_no.extend(
            [
                "Desplazamientos continuos en planta, mensajeria interna o recorridos operativos extensos.",
                "Trabajo en alturas, superficies inestables o actividades que exijan cambios posturales frecuentes.",
            ]
        )
        ajustes.append(
            {
                "titulo": "Puesto fijo y apoyo ergonomico",
                "descripcion": "Ubicar a la persona en un puesto estable con ayudas ergonomicas, distancias cortas y acceso facil a insumos.",
                "fundamento": "La movilidad moderada o alta sugiere reducir traslados, sobreesfuerzo y exigencia postural.",
            }
        )
        recomendaciones.append(
            "Evitar asignaciones que dependan de desplazamientos frecuentes y priorizar puestos con estabilidad espacial."
        )

    if cognicion >= 50 and not auditiva_only:
        administrativo = [
            "Digitacion o registro de datos en formatos simples con validacion previa y pasos definidos.",
            "Actualizacion de bases de apoyo o listados cuando exista estructura, secuencia y supervision inicial.",
        ]
        relacional = [
            "Apoyo a usuarios en interacciones breves con guion o protocolo previamente establecido.",
            "Funciones de enlace interno con mensajes claros, tareas acotadas y seguimiento cercano al inicio.",
        ]
        tareas_no.extend(
            [
                "Toma de decisiones criticas en solitario o manejo simultaneo de multiples frentes complejos.",
                "Cargos con alta exigencia de priorizacion dinamica, respuesta inmediata y autonomia total desde el inicio.",
            ]
        )
        ajustes.append(
            {
                "titulo": "Estructuracion de tareas y supervision inicial",
                "descripcion": "Organizar actividades por pasos, con apoyos visuales, secuencia estable y apoyo inicial para consolidar rutina.",
                "fundamento": "La presencia de dificultad cognitiva moderada o alta aconseja tareas estructuradas y curva de adaptacion guiada.",
            }
        )
        recomendaciones.append(
            "Asignar funciones con instrucciones paso a paso y validar comprension antes de incrementar complejidad o autonomia."
        )

    if cuidado_personal <= 25:
        recomendaciones.append(
            "Reconocer la buena autonomia en autocuidado y favorecer roles que aprovechen esa capacidad preservada dentro de un entorno inclusivo."
        )

    if relaciones >= 40 and not auditiva_only:
        relacional = [
            "Apoyo relacional en contextos previsibles, con roles claros, tiempos definidos y bajo nivel de ambiguedad social.",
            "Apoyo al usuario o al equipo en funciones de soporte con interaccion guiada y canales claros de comunicacion.",
        ]
        tareas_no.append(
            "Mediacion de conflictos complejos o roles con exigencia constante de negociacion social ambigua."
        )
        ajustes.append(
            {
                "titulo": "Entorno relacional estructurado",
                "descripcion": "Definir funciones, interlocutores y protocolos de interaccion para reducir ambiguedad y facilitar adaptacion social.",
                "fundamento": "Las dificultades en relaciones sugieren mayor claridad de rol y contextos de interaccion previsibles.",
            }
        )

    if participacion >= 45 and not auditiva_only:
        tareas_no.extend(
            [
                "Roles totalmente autonomos sin apoyos, cambios frecuentes de prioridad o coordinacion simultanea de multiples demandas.",
                "Funciones de alta exposicion externa con requerimientos variables y poca estructura operativa.",
            ]
        )
        recomendaciones.append(
            "Evitar multitarea compleja y privilegiar funciones con prioridades visibles, secuencia estable y soporte de seguimiento."
        )

    if vida_diaria >= 50:
        ajustes.append(
            {
                "titulo": "Flexibilizacion operativa",
                "descripcion": "Organizar horarios, tiempos de ejecucion y distribucion de tareas de manera gradual para sostener desempeno funcional.",
                "fundamento": "Una afectacion relevante en vida diaria sugiere administrar cargas y tiempos de trabajo con mayor previsibilidad.",
            }
        )

    administrativo = _dedupe(administrativo)[:3]
    operativo = _dedupe(operativo)[:3]
    relacional = _dedupe(relacional)[:3]
    tareas_no = _dedupe(tareas_no)[:6]
    recomendaciones = _dedupe(recomendaciones)[:6]
    ajustes = _dedupe_adjustments(ajustes)[:4]

    discapacidades_texto = ", ".join(discapacidades_activas) if discapacidades_activas else "sin categorias activas claramente legibles"
    if auditiva_only:
        perfil = (
            f"La persona presenta un perfil funcional que requiere lectura conservadora del certificado, "
            f"con categorias activas reportadas como {discapacidades_texto}. "
            f"Los puntajes deben interpretarse dentro de la accesibilidad comunicativa propia de la discapacidad auditiva, "
            f"sin inferir otras discapacidades no certificadas. "
            f"Se recomiendan funciones con comunicacion escrita, apoyos visuales, senalizacion visual para alertas y confirmacion de instrucciones relevantes. "
            f"Tambien se reconoce la necesidad de evitar conclusiones absolutas y priorizar inclusion, claridad operativa y aprovechamiento de capacidades preservadas."
        )
    else:
        perfil = (
            f"La persona presenta un perfil funcional que requiere lectura conservadora del certificado, "
            f"con categorias activas reportadas como {discapacidades_texto}. "
            f"Los puntajes sugieren mayor atencion en cognicion={cognicion:.2f}, movilidad={movilidad:.2f}, "
            f"relaciones={relaciones:.2f} y participacion={participacion:.2f}. "
            f"Se recomiendan funciones estructuradas, con demandas previsibles, ajustes razonables y apoyo inicial. "
            f"Tambien se reconoce la necesidad de evitar conclusiones absolutas y priorizar inclusion, adaptacion del puesto y aprovechamiento de capacidades preservadas."
        )

    return {
        "tareas_recomendadas": {
            "administrativo_oficina": administrativo,
            "operativo_manual_liviano": operativo,
            "relacional_apoyo": relacional,
        },
        "ajustes_razonables": ajustes,
        "tareas_no_recomendadas": tareas_no,
        "perfil_funcionamiento": perfil,
        "recomendaciones_rrhh_sst": recomendaciones,
    }


def _safe_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _safe_float(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item.strip())
    return result


def _dedupe_adjustments(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for item in items:
        titulo = str(item.get("titulo") or "").strip()
        descripcion = str(item.get("descripcion") or "").strip()
        fundamento = str(item.get("fundamento") or "").strip()
        if not titulo or not descripcion or not fundamento:
            continue
        key = titulo.lower()
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
